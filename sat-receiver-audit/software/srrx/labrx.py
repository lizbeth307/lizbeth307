"""Supervised RX-to-spectrum pipeline. Default input is synthetic, never RF TX."""
from __future__ import annotations

import argparse
import ctypes as C
import errno
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import resource
import signal
import sys
import tempfile
import time

import numpy as np

from .receivers import AirspyHFReceiver, RTLReceiver, ControlGuard, load_driver_record, validate_tuning


def atomic_json(path, value, *, storage_guard=None):
    if storage_guard is not None:
        storage_guard.atomic_json(path, value)
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n").encode()
    fd, name = tempfile.mkstemp(prefix=".srrx-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def synthetic_blocks(fft_size, sample_rate, count, *, seed=307):
    """Deterministic complex tone+noise. These bytes never leave RAM as IQ."""
    rng = np.random.default_rng(seed)
    phase, index = 0, 0
    while count == 0 or index < count:
        t = np.arange(fft_size, dtype=np.float64) + phase
        samples = .3 * np.exp(2j * np.pi * .125 * t)
        samples += .01 * (rng.normal(size=fft_size) + 1j * rng.normal(size=fft_size))
        yield samples.astype(np.complex64)
        phase += fft_size
        index += 1


def _disable_worker_core_dumps(*, libc=None):
    """Fail closed before loading a driver or receiving samples on Linux.

    RLIMIT_CORE alone does not stop a piped crash collector. PR_SET_DUMPABLE
    disables kernel core generation independently of that system-wide handler.
    https://man7.org/linux/man-pages/man5/core.5.html
    https://man7.org/linux/man-pages/man2/pr_set_dumpable.2const.html
    """
    if sys.platform != "linux":
        raise OSError(errno.ENOSYS, "RX worker core-dump protection requires Linux")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    runtime = libc if libc is not None else C.CDLL(None, use_errno=True)
    try:
        prctl = runtime.prctl
    except AttributeError as exc:
        raise OSError(errno.ENOSYS, "RX worker requires prctl core-dump protection") from exc
    prctl.argtypes = [C.c_int, C.c_ulong, C.c_ulong, C.c_ulong, C.c_ulong]
    prctl.restype = C.c_int
    if prctl(4, 0, 0, 0, 0) != 0:  # PR_SET_DUMPABLE, 0L
        raise OSError(C.get_errno() or errno.EPERM, "Cannot disable RX worker core dumps")
    dumpable = prctl(3, 0, 0, 0, 0)  # PR_GET_DUMPABLE
    if dumpable != 0:
        code = (C.get_errno() or errno.EPERM) if dumpable < 0 else errno.EPERM
        raise OSError(code, "RX worker core-dump protection was not confirmed")


def _worker(connection, record, center_hz, sample_rate):
    """C driver calls cannot stall the control observer in the parent."""
    receiver = None
    try:
        _disable_worker_core_dumps()
        # Recheck exact library bytes immediately before dlopen in this process.
        p = Path(record["library_path"])
        if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest() != record["library_sha256"]:
            raise ValueError("Driver bytes changed before open")
        cls = RTLReceiver if record["backend"] == "rtl" else AirspyHFReceiver
        receiver = cls(record, center_hz, sample_rate)
        # Reassert/verify after driver initialization, before the first read.
        _disable_worker_core_dumps()
        while True:
            samples = receiver.read()
            if samples.ndim != 1 or not 1 <= samples.size <= 262144 or not np.isfinite(samples).all():
                raise OSError("Invalid hardware samples")
            connection.send_bytes(b"I" + samples.astype("<c8", copy=False).tobytes())
    except (Exception, KeyboardInterrupt) as exc:
        try:
            # Constant class/message only; no samples or decoder payload logged.
            connection.send_bytes(b"E" + str(exc).encode("utf-8", errors="replace")[:512])
        except (OSError, BrokenPipeError):
            pass
    finally:
        if receiver is not None:
            receiver.close()
        connection.close()


class WorkerSource:
    def __init__(self, record, center_hz, sample_rate):
        ctx = mp.get_context("spawn")
        self.reader, sender = ctx.Pipe(duplex=False)
        self.process = ctx.Process(target=_worker, args=(sender, record, center_hz, sample_rate), daemon=True)
        try:
            self.process.start()
        except BaseException:
            self.reader.close()
            raise
        finally:
            sender.close()

    def read(self, guard, *, timeout_s=1.0):
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            guard.check()
            if self.reader.poll(.05):
                try:
                    data = self.reader.recv_bytes(2 * 1024 * 1024 + 1)
                except EOFError as exc:
                    raise OSError("RX worker pipe closed before a complete block") from exc
                if not data or data[0:1] != b"I":
                    raise OSError(data[1:].decode("utf-8", errors="replace")[:512] or "RX worker failed")
                if not data[1:] or (len(data) - 1) % 8:
                    raise OSError("Invalid worker complex64 block")
                return np.frombuffer(data, dtype="<c8", offset=1).copy()
            if not self.process.is_alive():
                raise OSError("RX worker exited")
        raise TimeoutError("No fresh RX block within one second")

    def close(self):
        self.reader.close()
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(.5)
        if self.process.is_alive():
            self.process.kill()
            self.process.join(.5)


def run_capture(*, center_hz=100000000, sample_rate=1024000, fft_size=1024,
                frames=10, output=None, survey=None, record=None, transport=None,
                source_factory=WorkerSource, storage_guard=None):
    from .spectrum import SpectrumProcessor, append_survey
    if type(frames) is not int or not 0 <= frames <= 1000000:
        raise ValueError("frames must be 0 (until stopped) or 1..1000000")
    if type(fft_size) is not int or not 64 <= fft_size <= 16384 or fft_size & (fft_size - 1):
        raise ValueError("FFT size must be a power of two in 64..16384")
    if type(center_hz) is not int or not 0 <= center_hz <= 6000000000:
        raise ValueError("Integer center in 0..6GHz required")
    if type(sample_rate) is not int or not 48000 <= sample_rate <= 56000000:
        raise ValueError("Integer sample rate in 48k..56M required")
    processor = SpectrumProcessor(fft_size=fft_size)
    source, guard, completed, last = None, None, 0, None
    observed = False
    try:
        if storage_guard is not None:
            storage_guard.check()
        if record is not None:
            if transport is None:
                raise ValueError("Hardware requires a live control observer")
            validate_tuning(record["backend"], center_hz, sample_rate)
            # This process also holds raw sample blocks and FFT/ring buffers.
            # Protect it before any control observation or source construction;
            # keep it nondumpable after capture because freed heap may retain IQ.
            _disable_worker_core_dumps()
            guard = ControlGuard(transport, record["branch"])
            guard.check()
            observed = True
            source = source_factory(record, center_hz, sample_rate)
        blocks = synthetic_blocks(fft_size, sample_rate, frames) if record is None else None
        while frames == 0 or completed < frames:
            if storage_guard is not None:
                storage_guard.check()
            samples = next(blocks) if source is None else source.read(guard)
            if guard is not None:
                guard.check()
            # This implementation computes FFTs, does not demodulate/private-decode,
            # and has no IQ/audio recorder or socket sample-export endpoint.
            last = processor.process(samples[-fft_size:], center_hz, sample_rate,
                                     source="SIMULATION" if record is None else "HARDWARE")
            if output is not None:
                atomic_json(output, last, storage_guard=storage_guard)
            if survey is not None:
                append_survey(survey, last, storage_guard=storage_guard)
            completed += 1
            if source is None and frames == 0:
                time.sleep(.1)
    finally:
        try:
            if source is not None:
                source.close()
        finally:
            if observed:
                try:
                    transport({"op": "control", "name": "EN_" + record["branch"], "value": False})
                except (OSError, RuntimeError, ValueError):
                    pass
    return {"frames": completed, "source": "SIMULATION" if record is None else "HARDWARE",
            "raw_iq_persisted": False, "physical_tests_performed": False, "last_frame": last}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--simulate", action="store_true")
    mode.add_argument("--hardware", action="store_true")
    p.add_argument("--center-hz", type=int, default=100000000)
    p.add_argument("--sample-rate", type=int, default=1024000)
    p.add_argument("--fft-size", type=int, default=1024)
    p.add_argument("--frames", type=int, default=10)
    p.add_argument("--output", type=Path)
    p.add_argument("--survey", type=Path)
    p.add_argument("--storage-root", type=Path,
                   help="Opt-in exact mounted output root; existing directories only; no removable-mount fallback")
    p.add_argument("--storage-device", type=Path,
                   help="Explicit block device, preferably operator-verified /dev/disk/by-uuid/...; pair with --storage-root")
    p.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--acceptance", type=Path)
    p.add_argument("--driver-record", type=Path)
    p.add_argument("--socket", default="/tmp/srrx/control.sock")
    args = p.parse_args(argv)
    storage_guard = None
    try:
        if (args.storage_root is None) != (args.storage_device is None):
            raise ValueError("--storage-root and --storage-device must be supplied together")
        if args.storage_root is not None:
            from .storage import StorageGuard
            storage_guard = StorageGuard(args.storage_root, args.storage_device)
        record, transport = None, None
        if args.hardware:
            from .commissioning import load_acceptance
            from .daemon import request_once
            accepted = load_acceptance(args.acceptance, args.project)
            if args.driver_record is None:
                raise ValueError("Hardware driver record required")
            record = load_driver_record(args.driver_record, args.project, accepted)
            transport = lambda request: request_once(args.socket, request, timeout=.2)
        elif args.acceptance is not None or args.driver_record is not None:
            raise ValueError("Physical options require explicit --hardware")
        result = run_capture(center_hz=args.center_hz, sample_rate=args.sample_rate,
                             fft_size=args.fft_size, frames=args.frames, output=args.output,
                             survey=args.survey, record=record, transport=transport,
                             storage_guard=storage_guard)
        result.pop("last_frame")
        print(json.dumps(result, allow_nan=False))
        return 0
    except KeyboardInterrupt:
        return 130
    except (ValueError, OSError, RuntimeError) as exc:
        import sys
        print("labrx: " + str(exc), file=sys.stderr)
        return 2
    finally:
        if storage_guard is not None:
            storage_guard.close()


if __name__ == "__main__":
    raise SystemExit(main())
