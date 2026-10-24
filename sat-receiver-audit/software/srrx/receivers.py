"""Small RX-only bindings. No TX, EEPROM, RF-bias-on or raw-IQ file API."""
from __future__ import annotations

import ctypes as C
import hashlib
import os
from pathlib import Path
import queue
import re
import stat

import numpy as np

from .commissioning import GATE_IDS, _read_json

# Review finding RX-10: a driver record binds only through the RX gate whose
# current/inrush measurement used that driver build (E5-04: R501 RTL-A and R509
# HF+; E2-03: U210 RTL-B). RTLA and HFP share E5-04; the record's branch separates them.
DRIVER_GATES = {"RTLA": "E5-04", "RTLB": "E2-03", "HFP": "E5-04"}
if not set(DRIVER_GATES.values()) <= set(GATE_IDS):
    raise RuntimeError("Driver gate is not an acceptance gate")
# Only these UIDs may own a driver library and its directories. Deliberately no
# CLI flag or environment variable; only component tests pass another set in code.
TRUSTED_LIBRARY_UIDS = frozenset({0})
MAX_LIBRARY_BYTES = 64 * 1024 * 1024


def _check(result, operation):
    if result != 0:
        raise OSError(f"{operation} failed ({result})")


def _bind(lib, name, args, result=C.c_int):
    function = getattr(lib, name)
    function.argtypes, function.restype = args, result
    return function


def check_library(path, trusted_uids, opened=None):
    """Refuse a driver library that an untrusted principal could change.

    The path must be absolute and canonical: no component is a symlink (on merged
    /usr, /lib/... is one). The file must be a regular, trusted-owned file without
    group/world write or setuid/setgid. Every parent must be a trusted-owned
    directory without group/world write (sticky allowed), as decoder_policy and
    scope_policy require. Metadata comes from lstat, so a FIFO or device is never
    opened. opened is os.fstat of the descriptor to hash and load: it must be the
    same checked inode, so its bytes cannot be rewritten in place by another user.
    """
    if (type(trusted_uids) is not frozenset or not trusted_uids
            or not all(type(uid) is int and uid >= 0 for uid in trusted_uids)):
        raise ValueError("Trusted library UIDs must be a non-empty frozenset")
    text = os.fspath(path)
    if type(text) is not str or not os.path.isabs(text) or os.path.realpath(text) != text:
        raise ValueError("Driver library path must be absolute and canonical, without symlinks")
    try:
        info = os.lstat(text)
        folders = [os.lstat(parent) for parent in Path(text).parents]
    except OSError as exc:
        raise ValueError("Driver library is unavailable") from exc
    def trusted_file(item):
        return (stat.S_ISREG(item.st_mode) and item.st_uid in trusted_uids and not item.st_mode & 0o022
                and not item.st_mode & (stat.S_ISUID | stat.S_ISGID) and 0 < item.st_size <= MAX_LIBRARY_BYTES)
    if not trusted_file(info):
        raise ValueError("Driver library must be a regular file of a trusted UID, without group/world write or setuid/setgid")
    for folder in folders:
        if (not stat.S_ISDIR(folder.st_mode) or folder.st_uid not in trusted_uids
                or folder.st_mode & 0o022 and not folder.st_mode & stat.S_ISVTX):
            raise ValueError("Driver library directories must be owned by a trusted UID, without group/world write")
    if opened is not None and (not trusted_file(opened)
                               or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino)):
        raise ValueError("Opened driver library is not the checked file")
    return info


def load_driver_record(path, project, accepted, *, trusted_uids=TRUSTED_LIBRARY_UIDS):
    """Internal: accepted is the already validated commissioning record.

    The driver record must itself be a hashed artifact of its branch's RX gate
    (DRIVER_GATES). A digest binds reviewed bytes; it does not prove an ELF or
    its dependencies are safe.
    """
    project, path = Path(project).resolve(strict=True), Path(path).resolve(strict=True)
    if not path.is_relative_to(project) or not path.is_file():
        raise ValueError("Driver record must be a small project-local artifact")
    with path.open("rb") as stream:
        raw = stream.read(16385)  # read once: the bytes parsed are the bytes hashed
    if not 0 < len(raw) <= 16384:
        raise ValueError("Driver record must be a small project-local artifact")
    entry = {"path": path.relative_to(project).as_posix(), "sha256": hashlib.sha256(raw).hexdigest()}
    artifacts = [a for gate in accepted["gates"].values()
                 for a in gate["evidence"]["artifacts"]]
    if entry not in artifacts:
        raise ValueError("Driver record is not bound to hardware acceptance")
    record = _read_json(path, raw)
    fields = {"v", "backend", "branch", "serial", "library_path", "library_sha256",
              "rx_only_reviewed", "bias_disabled_verified", "dependencies_reviewed"}
    if (type(record) is not dict or set(record) != fields or type(record["v"]) is not int or record["v"] != 1
            or record["backend"] not in ("rtl", "airspyhf")
            or any(record[k] is not True for k in
                   ("rx_only_reviewed", "bias_disabled_verified", "dependencies_reviewed"))):
        raise ValueError("Reviewed receive-only driver record required")
    if record["branch"] not in (("RTLA", "RTLB") if record["backend"] == "rtl" else ("HFP",)):
        raise ValueError("Backend/physical branch mismatch")
    if type(record["serial"]) is not str or not re.fullmatch(r"[A-Za-z0-9_.:-]{4,64}", record["serial"]):
        raise ValueError("Explicit hardware serial required")
    if record["backend"] == "airspyhf" and not re.fullmatch(r"[0-9a-fA-F]{16}", record["serial"]):
        raise ValueError("AirspyHF serial must contain exactly 16 hex digits")
    gate = DRIVER_GATES[record["branch"]]
    if entry not in accepted["gates"].get(gate, {}).get("evidence", {}).get("artifacts", []):
        raise ValueError(f"Driver record is not bound to acceptance gate {gate} of branch {record['branch']}")
    verify_library(record["library_path"], record["library_sha256"], trusted_uids)
    return record


def verify_library(path, sha256, trusted_uids=TRUSTED_LIBRARY_UIDS):
    """check_library, then the streamed SHA256 of that same open inode."""
    if type(path) is not str or type(sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("Driver library path/digest mismatch")
    check_library(path, trusted_uids)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError as exc:
        raise ValueError("Driver library is unavailable") from exc
    try:
        check_library(path, trusted_uids, opened=os.fstat(fd))
        digest, size = hashlib.sha256(), 0
        for block in iter(lambda: os.read(fd, 1024 * 1024), b""):  # 1 MiB blocks, bounded
            size += len(block)
            if size > MAX_LIBRARY_BYTES:
                raise ValueError("Driver library path/digest mismatch")
            digest.update(block)
    finally:
        os.close(fd)
    if digest.hexdigest() != sha256:
        raise ValueError("Driver library path/digest mismatch")


def validate_tuning(backend, center_hz, sample_rate):
    if type(center_hz) is not int or type(sample_rate) is not int:
        raise ValueError("Integer tuning/rate required")
    if backend == "rtl":
        if not 500000 <= center_hz <= 1766000000:
            raise ValueError("RTL tuning outside configured V4/R820T envelope")
        if not (225001 <= sample_rate <= 300000 or 900001 <= sample_rate <= 2400000):
            raise ValueError("Unsupported RTL sample rate; >2.4MS/s not qualified")
    elif backend == "airspyhf":
        if not (9000 <= center_hz <= 31000000 or 60000000 <= center_hz <= 260000000):
            raise ValueError("Airspy HF+ tuning outside supported bands")
        if not 48000 <= sample_rate <= 912000:
            raise ValueError("HF+ rate must also occur in the live device's rate list")
    else:
        raise ValueError("Unsupported physical RX backend; Lime remains blocked")


class RTLReceiver:
    """Osmocom rtl-sdr.h C ABI. Use only inside a supervised worker process."""
    # Successive rtlsdr_read_sync blocks are not proven contiguous: never splice them.
    discontinuity = True

    def __init__(self, record, center_hz, sample_rate, *, loader=C.CDLL):
        validate_tuning("rtl", center_hz, sample_rate)
        self.dev, self.lib = C.c_void_p(), loader(record["library_path"])
        self.closed = False
        v, i, u = C.c_void_p, C.c_int, C.c_uint32
        definitions = {
            "rtlsdr_get_device_count": ([], u),
            "rtlsdr_get_device_usb_strings": ([u, C.c_char_p, C.c_char_p, C.c_char_p], i),
            "rtlsdr_open": ([C.POINTER(v), u], i), "rtlsdr_close": ([v], i),
            "rtlsdr_get_usb_strings": ([v, C.c_char_p, C.c_char_p, C.c_char_p], i),
            "rtlsdr_set_bias_tee": ([v, i], i),
            "rtlsdr_set_direct_sampling": ([v, i], i),
            "rtlsdr_set_center_freq": ([v, u], i), "rtlsdr_get_center_freq": ([v], u),
            "rtlsdr_set_sample_rate": ([v, u], i), "rtlsdr_get_sample_rate": ([v], u),
            "rtlsdr_set_tuner_gain_mode": ([v, i], i),
            "rtlsdr_set_agc_mode": ([v, i], i), "rtlsdr_reset_buffer": ([v], i),
            "rtlsdr_read_sync": ([v, v, i, C.POINTER(i)], i)}
        for name, (args, result) in definitions.items():
            _bind(self.lib, name, args, result)
        try:
            count = self.lib.rtlsdr_get_device_count()
            if not 1 <= count <= 64:
                raise OSError("Missing/excessive RTL device count")
            matching = []
            for index in range(count):
                serial = C.create_string_buffer(256)
                _check(self.lib.rtlsdr_get_device_usb_strings(index, None, None, serial), "enumerate RTL")
                if serial.value.decode("ascii", errors="strict") == record["serial"]:
                    matching.append(index)
            if len(matching) != 1:
                raise OSError("RTL serial missing or ambiguous; index fallback forbidden")
            _check(self.lib.rtlsdr_open(C.byref(self.dev), matching[0]), "open RTL")
            # Never requests bias ON. Hardware branch bias is controlled by labd.
            _check(self.lib.rtlsdr_set_bias_tee(self.dev, 0), "disable RTL bias")
            serial = C.create_string_buffer(256)
            _check(self.lib.rtlsdr_get_usb_strings(self.dev, None, None, serial), "verify open serial")
            if serial.value.decode("ascii") != record["serial"]:
                raise OSError("Opened RTL serial changed")
            _check(self.lib.rtlsdr_set_direct_sampling(self.dev, 0), "disable direct sampling")
            _check(self.lib.rtlsdr_set_sample_rate(self.dev, sample_rate), "RTL rate")
            _check(self.lib.rtlsdr_set_center_freq(self.dev, center_hz), "RTL center")
            _check(self.lib.rtlsdr_set_tuner_gain_mode(self.dev, 0), "RTL tuner auto gain")
            _check(self.lib.rtlsdr_set_agc_mode(self.dev, 0), "RTL digital AGC off")
            if (self.lib.rtlsdr_get_center_freq(self.dev) != center_hz
                    or self.lib.rtlsdr_get_sample_rate(self.dev) != sample_rate):
                raise OSError("RTL tuning/rate readback mismatch")
            _check(self.lib.rtlsdr_reset_buffer(self.dev), "RTL reset buffer")
        except BaseException:
            self.close()
            raise

    def read(self):
        raw = (C.c_ubyte * 16384)()
        count = C.c_int()
        _check(self.lib.rtlsdr_read_sync(self.dev, raw, len(raw), C.byref(count)), "RTL read")
        if not 0 < count.value <= len(raw) or count.value % 2:
            raise OSError("Invalid/empty RTL IQ block")
        iq = (np.frombuffer(raw, dtype=np.uint8, count=count.value).astype(np.float32) - 127.5) / 127.5
        return (iq[0::2] + 1j * iq[1::2]).astype(np.complex64)

    def close(self):
        if not self.closed:
            self.closed = True
            if self.dev.value:
                try:
                    self.lib.rtlsdr_set_bias_tee(self.dev, 0)
                finally:
                    self.lib.rtlsdr_close(self.dev)


class _HFTransfer(C.Structure):
    _fields_ = [("device", C.c_void_p), ("ctx", C.c_void_p),
                ("samples", C.POINTER(C.c_float)), ("sample_count", C.c_int),
                ("dropped_samples", C.c_uint64)]


class AirspyHFReceiver:
    """Official airspyhf.h callback ABI, serial-selected, bounded RAM queue."""
    def __init__(self, record, center_hz, sample_rate, *, loader=C.CDLL):
        validate_tuning("airspyhf", center_hz, sample_rate)
        self.dev, self.lib = C.c_void_p(), loader(record["library_path"])
        self.closed, self.started, self.error, self.discontinuity, self._gap = False, False, None, False, False
        self.blocks = queue.Queue(maxsize=64)  # (gap_before, block); 1 MiB at 2048-sample transfers
        self.callback_type = C.CFUNCTYPE(C.c_int, C.POINTER(_HFTransfer))
        v, u = C.c_void_p, C.c_uint32
        for name, args in {
            "airspyhf_open_sn": [C.POINTER(v), C.c_uint64],
            "airspyhf_close": [v], "airspyhf_set_freq": [v, u],
            "airspyhf_get_samplerates": [v, C.POINTER(u), u],
            "airspyhf_set_samplerate": [v, u],
            "airspyhf_start": [v, self.callback_type, v], "airspyhf_stop": [v]}.items():
            _bind(self.lib, name, args)
        try:
            _check(self.lib.airspyhf_open_sn(C.byref(self.dev), int(record["serial"], 16)), "HF+ open serial")
            # HF+1.6.8 has no bias API. A later library must explicitly disable it.
            if hasattr(self.lib, "airspyhf_set_bias_tee"):
                _check(_bind(self.lib, "airspyhf_set_bias_tee", [v, C.c_int8])(self.dev, 0), "HF+ bias off")
            count = u()
            _check(self.lib.airspyhf_get_samplerates(self.dev, C.byref(count), 0), "HF+ rate count")
            if not 1 <= count.value <= 64:
                raise OSError("HF+ invalid rate list")
            rates = (u * count.value)()
            _check(self.lib.airspyhf_get_samplerates(self.dev, rates, count.value), "HF+ rates")
            if sample_rate not in rates:
                raise ValueError("Rate absent from device-reported HF+ list")
            _check(self.lib.airspyhf_set_samplerate(self.dev, sample_rate), "HF+ rate")
            _check(self.lib.airspyhf_set_freq(self.dev, center_hz), "HF+ center")
            self.callback = self.callback_type(self._receive)
            _check(self.lib.airspyhf_start(self.dev, self.callback, None), "HF+ start")
            self.started = True
        except BaseException:
            self.close()
            raise

    def _receive(self, pointer):
        try:
            transfer = pointer.contents
            if not 0 < transfer.sample_count <= 262144 or transfer.dropped_samples:
                raise OSError("HF+ invalid block or dropped samples")
            if not transfer.samples:
                raise OSError("HF+ null samples")
            a = np.ctypeslib.as_array(transfer.samples, shape=(2 * transfer.sample_count,)).copy()
            block = (a[::2] + 1j * a[1::2]).astype(np.complex64)
            # Consumer lag is not a USB drop: drop this transfer and mark the next
            # queued one. Only read() dequeues and only this thread touches _gap,
            # so a block marked contiguous never follows a dropped one.
            try:
                self.blocks.put_nowait((self._gap, block))
                self._gap = False
            except queue.Full:
                self._gap = True
            return 0
        except BaseException as exc:
            self.error = str(exc) or "HF+ callback failed"
            return -1

    def read(self):
        if self.error:
            raise OSError(self.error)
        try:
            self.discontinuity, block = self.blocks.get(timeout=.25)
        except queue.Empty as exc:
            raise TimeoutError("HF+ sample timeout") from exc
        return block

    def close(self):
        if not self.closed:
            self.closed = True
            if self.dev.value:
                try:
                    if self.started:
                        self.lib.airspyhf_stop(self.dev)
                finally:
                    self.lib.airspyhf_close(self.dev)


class ControlGuard:
    """Read-only labd observer. Never creates/renews an operator lease."""
    def __init__(self, transport, branch):
        if branch not in ("RTLA", "RTLB", "HFP"):
            raise ValueError("Unsupported physical RX branch")
        self.transport, self.branch, self.session = transport, branch, None

    def check(self):
        reply = self.transport({"op": "status"})
        data = reply.get("data", {}) if type(reply) is dict and reply.get("ok") is True else {}
        if type(data) is not dict:
            raise RuntimeError("RX blocked: malformed control status")
        policy, pico = data.get("policy", {}), data.get("pico", {})
        if type(policy) is not dict or type(pico) is not dict or type(policy.get("outputs", {})) is not dict:
            raise RuntimeError("RX blocked: malformed control readiness")
        valid = (data.get("mode") == "HARDWARE" and data.get("hardware_qualified") is True
                 and data.get("live_identity_verified") is True
                 and data.get("configured") is True and not data.get("last_error")
                 and pico.get("state") == "ACTIVE" and pico.get("mcp_reset") is False
                 and policy.get("armed") is True and policy.get("commissioned") is True
                 and policy.get("pico_active") is True and not policy.get("fault")
                 and policy.get("outputs", {}).get("EN_" + self.branch) is True)
        session = data.get("session")
        if not valid or type(session) not in (str, int) or not session:
            raise RuntimeError("RX blocked: labd is not fresh/qualified/armed or branch is OFF")
        if self.session is not None and session != self.session:
            raise RuntimeError("RX stopped: Pico session changed; explicit restart required")
        self.session = session
        return data
