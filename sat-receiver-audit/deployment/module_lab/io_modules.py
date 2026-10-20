"""Bounded synthetic USB inventory for module-lab scenarios.

This is a fixture reader, not a production USB driver, udev monitor or binding
service. It never reads /sys, changes USB authorization, loads firmware, mounts
storage, or opens a device. Fixture VID/PID values identify invented test
descriptors; they do not identify a particular commercial board revision.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil


MAX_DEVICES = 64
MAX_DESCRIPTOR_BYTES = 256
_NAME = re.compile(r"[1-9][0-9]?-[1-9][0-9]?(?:\.[1-9][0-9]?){0,4}\Z")
_HEX4 = re.compile(r"[0-9a-fA-F]{4}\Z")
_HEX2 = re.compile(r"[0-9a-fA-F]{2}\Z")
_MARKER = "SRRX_SYNTHETIC_USB_ONLY_V1\n"


def _name(value):
    if type(value) is not str or not _NAME.fullmatch(value):
        raise ValueError("Bounded synthetic USB topology name required")
    return value


def _text(path):
    if path.is_symlink():
        raise ValueError("Descriptor symlinks are not read")
    with path.open("rb") as stream:
        raw = stream.read(MAX_DESCRIPTOR_BYTES + 1)
    if len(raw) > MAX_DESCRIPTOR_BYTES:
        raise ValueError("Oversized USB descriptor fixture")
    value = raw.decode("utf-8", "strict").strip()
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("Control characters in USB descriptor fixture")
    return value


class USBFixture:
    """Own an explicitly marked directory containing sysfs-shaped test files."""
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink() or self.root.resolve() == Path("/sys"):
            raise ValueError("A private synthetic directory is required")
        marker = self.root / "SYNTHETIC_USB_ONLY"
        if marker.exists() and _text(marker) != _MARKER.strip():
            raise ValueError("Not a module-lab synthetic root")
        if not marker.exists() and any(self.root.iterdir()):
            raise ValueError("Fixture root must initially be empty")
        marker.write_text(_MARKER, encoding="ascii")
        self.devices = self.root / "bus" / "usb" / "devices"
        self.devices.mkdir(parents=True, exist_ok=True)

    def connect(self, name, *, vid, pid, serial="fixture-only", product="Synthetic peripheral",
                device_class="00", speed="480", driver=None):
        name = _name(name)
        if not _HEX4.fullmatch(vid) or not _HEX4.fullmatch(pid) or not _HEX2.fullmatch(device_class):
            raise ValueError("Hex USB fixture descriptors required")
        if speed not in ("1.5", "12", "480", "5000", "10000", "20000"):
            raise ValueError("Unsupported synthetic USB speed")
        for value in (serial, product):
            if type(value) is not str or len(value.encode("utf-8")) > MAX_DESCRIPTOR_BYTES - 1 or any(ord(c) < 32 for c in value):
                raise ValueError("Bounded descriptor text required")
        if "." in name and not (self.devices / name.rsplit(".", 1)[0]).is_dir():
            raise ValueError("Connect the parent fixture hub first")
        path = self.devices / name
        if path.exists() or path.is_symlink():
            raise ValueError("Fixture device already exists")
        path.mkdir()
        for filename, value in {"idVendor": vid, "idProduct": pid, "serial": serial,
                                "product": product, "bDeviceClass": device_class,
                                "speed": speed, "authorized": "1"}.items():
            (path / filename).write_text(value + "\n", encoding="utf-8")
        if driver is not None:
            if type(driver) is not str or not re.fullmatch(r"[a-zA-Z0-9_-]{1,40}", driver):
                shutil.rmtree(path)
                raise ValueError("Bounded synthetic driver name required")
            # A link name is observed only. No real driver path is resolved.
            (path / "driver").symlink_to("../../drivers/" + driver)
        return path

    def remove(self, name):
        name = _name(name)
        # A physical hub departure also removes every descendant in the fixture.
        targets = [p for p in self.devices.iterdir() if p.name == name or p.name.startswith(name + ".")]
        for path in targets:
            if path.is_symlink():
                path.unlink()
            else:
                shutil.rmtree(path)
        return sorted(path.name for path in targets)


class USBInventory:
    """Read private fixture descriptors, reporting errors without auto-binding."""
    def __init__(self, root):
        self.root = Path(root).absolute()
        if self.root.is_symlink() or _text(self.root / "SYNTHETIC_USB_ONLY") != _MARKER.strip():
            raise ValueError("An explicitly marked synthetic USB root is required")
        self.devices = self.root / "bus" / "usb" / "devices"

    def scan(self):
        records, errors, entries = [], [], []
        truncated = False
        try:
            with os.scandir(self.devices) as iterator:
                for entry in iterator:
                    if len(entries) == MAX_DEVICES:
                        truncated = True
                        break
                    entries.append(entry.name)
        except OSError as error:
            return {"devices": [], "errors": [{"device": None, "error": type(error).__name__}],
                    "truncated": False, "synthetic": True, "auto_bind": False}
        for name in sorted(entries):
            try:
                _name(name)
                path = self.devices / name
                if path.is_symlink() or not path.is_dir():
                    raise ValueError("Not a fixture device directory")
                vid, pid, cls = (_text(path / field) for field in ("idVendor", "idProduct", "bDeviceClass"))
                if not _HEX4.fullmatch(vid) or not _HEX4.fullmatch(pid) or not _HEX2.fullmatch(cls):
                    raise ValueError("Malformed fixture descriptor")
                speed, authorized = _text(path / "speed"), _text(path / "authorized")
                if speed not in ("1.5", "12", "480", "5000", "10000", "20000") or authorized not in ("0", "1"):
                    raise ValueError("Malformed fixture USB state")
                driver = path / "driver"
                observed_driver = None
                if driver.is_symlink():
                    observed_driver = Path(os.readlink(driver)).name
                    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,40}", observed_driver):
                        raise ValueError("Malformed fixture driver link")
                elif driver.exists():
                    raise ValueError("Fixture driver must be a name-only symlink")
                records.append({"device": name, "vid": vid.lower(), "pid": pid.lower(),
                                "device_class": cls.lower(), "serial": _text(path / "serial"),
                                "product": _text(path / "product"), "speed_mbps": float(speed),
                                "authorized": authorized == "1", "observed_driver": observed_driver,
                                "binding": "UNSUPPORTED", "driver_selected": False,
                                "synthetic": True})
            except (OSError, ValueError, UnicodeError) as error:
                errors.append({"device": name[:48], "error": type(error).__name__})
        return {"devices": records, "errors": errors, "truncated": truncated,
                "synthetic": True, "auto_bind": False}


def changes(previous, current):
    """Inventory deltas describe fixture files, never a kernel uevent claim."""
    before = {item["device"]: item for item in previous["devices"]}
    after = {item["device"]: item for item in current["devices"]}
    return {"added": sorted(after.keys() - before.keys()), "removed": sorted(before.keys() - after.keys()),
            "changed": sorted(name for name in before.keys() & after.keys() if before[name] != after[name])}
