#!/usr/bin/env python3
"""Run local regressions with native Internet sockets denied in this process.

This only reduces test-process network access; it is not a general sandbox.
Linux seccomp documentation: kernel.org/doc/html/latest/userspace-api/seccomp_filter.html
"""
import ctypes as C
import errno
import os
from pathlib import Path
import platform
import runpy
import socket
import sys


def deny_internet_sockets():
    if sys.platform != "linux" or sys.byteorder != "little":
        raise RuntimeError("Offline native test filter requires supported Linux")
    targets = {"x86_64": (0xC000003E, 41), "aarch64": (0xC00000B7, 198)}
    if platform.machine() not in targets:
        raise RuntimeError("Unknown syscall ABI; refusing a network-enabled fallback")
    for fd in Path("/proc/self/fd").iterdir():
        try:
            target = os.readlink(fd)
        except OSError:
            continue
        if target.startswith("socket:["):
            raise RuntimeError("Inherited socket descriptor; refusing to run offline tests")
    arch, syscall_socket = targets[platform.machine()]

    class Filter(C.Structure):
        _fields_ = [("code", C.c_ushort), ("jt", C.c_ubyte),
                    ("jf", C.c_ubyte), ("k", C.c_uint32)]
    class Program(C.Structure):
        _fields_ = [("length", C.c_ushort), ("filters", C.POINTER(Filter))]

    rules = (Filter * 11)(
        Filter(0x20, 0, 0, 4),                  # seccomp_data.arch
        Filter(0x15, 1, 0, arch),
        Filter(0x06, 0, 0, 0x80000000),         # Unsupported ABI: kill process
        Filter(0x20, 0, 0, 0),                  # syscall number
        Filter(0x54, 0, 0, 0xBFFFFFFF),         # Also filter the x86 x32 ABI bit
        Filter(0x15, 0, 4, syscall_socket),
        Filter(0x20, 0, 0, 16),                 # first argument: socket family
        Filter(0x15, 1, 0, socket.AF_INET),
        Filter(0x15, 0, 1, socket.AF_INET6),
        Filter(0x06, 0, 0, 0x00050000 | errno.EPERM),
        Filter(0x06, 0, 0, 0x7FFF0000))
    program = Program(len(rules), rules)
    libc = C.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0 or libc.prctl(22, 2, C.byref(program), 0, 0) != 0:
        raise OSError(C.get_errno(), "Cannot enforce offline test filter")
    # No connection or payload is attempted. Prove both Internet families fail.
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            candidate = socket.socket(family, socket.SOCK_STREAM)
        except OSError as error:
            if error.errno != errno.EPERM:
                raise RuntimeError("Unexpected offline-filter self-test result") from error
        else:
            candidate.close()
            raise RuntimeError("Internet socket filter was not enforced")
    os.environ["SRRX_TEST_INET_DENIED"] = "1"


def main():
    if "onnxruntime" in sys.modules:
        raise RuntimeError("Runtime imported before privacy guard; start a fresh process")
    # The installed runtime Privacy.md documents this pre-initialization opt-out.
    os.environ["ORT_DISABLE_TELEMETRY"] = "1"
    deny_internet_sockets()
    print("Offline test guard PASS: IPv4/IPv6 socket creation denied; ORT telemetry disabled before import", flush=True)
    if sys.argv[1:] == ["--self-test-only"]:
        return 0
    if sys.argv[1:]:
        raise ValueError("Only --self-test-only is supported")
    runpy.run_path(str(Path(__file__).with_name("check_software.py")), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
