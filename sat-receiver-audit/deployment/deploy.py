#!/usr/bin/env python3
"""Read-only inventory, deterministic staging and fail-closed release checks.

No command partitions, flashes, mounts, runs apt, writes /etc, reloads udev or
enables/starts a system service. stage writes only a new explicit directory.
Doctor reads metadata; it never opens I2C, SDR or UART data channels.
"""
import argparse
import ast
import fnmatch
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True  # imports must not add __pycache__ to the tree verify_build allowlists
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
BAD_PARTS = {"channeltx", "samplesink", "samplemimo", "channelmimo", "amarisoft-plugin"}
BAD_NAMES = {"rtl_biast", "rtl_eeprom", "rtl_tcp", "limegui", "limeflash", "limespi", "limei2c",
             "limecsr", "limeoem", "limevspa", "limeppsdo", "limetrx", "wsjtx", "fldigi", "qsstv",
             "direwolf", "urh", "rigctl", "rigctld", "soapysdrserver", "wifi_test", "bt_test"}
BAD_MODULE_WORDS = ("amarisoft", "soapysdrremote", "hackrf", "bladerf", "redpitaya", "uhd", "lms7",
                    "iq_exporter", "network_sink", "pager_decoder", "recorder", "heatmap", "demodinmarsat")
# Pico UART group: only labd via SupplementaryGroups; HMI users join labd for the socket, never this.
PICO_GROUP = "srrx-pico"

# Device self-check denylist (STACK.md v2 §5.4 "Заборонено" and "Закріплено на -1",
# 1.2 #10, 4.3 excluded services, 5.2 FE1.1s P4). Only TX-capable tools, decoders
# of private content and their codec/driver packages are listed here; kernel and
# Qualcomm firmware pins are version locks, checked elsewhere. Region is Europe,
# so the US-only profile packages (multimon-ng EAS, nrsc5, dump978-fa,
# skyaware978) are never installed on this root.
PROHIBITED_PACKAGES = frozenset({
    # Hamlib/WSJT/TX-capable applications
    "wsjtx", "js8call", "python3-js8py", "fldigi", "qsstv", "direwolf", "urh",
    # SoapyRemote, unaudited Soapy/Lime modules and Lime GUI/GNU Radio blocks
    "soapysdr-module-all", "soapysdr0.8-module-all", "soapysdr0.8-module-remote", "soapysdr-module-remote",
    "soapysdr0.8-module-lms7", "soapysdr-module-lms7", "soapysdr0.8-module-hackrf", "soapysdr-module-hackrf",
    "soapysdr0.8-module-bladerf", "soapysdr-module-bladerf", "soapysdr0.8-module-uhd", "soapysdr-module-uhd",
    "soapysdr0.8-module-redpitaya", "soapysdr-module-redpitaya", "limesuite", "limesuiteng-gui", "gr-limesuiteng",
    # GSM/Iridium/pager/trunking/TETRA/ACARS and other private-content decoders
    "gr-gsm", "gr-iridium", "kalibrate-rtl", "kalibrate-hackrf", "kalibrate-bladerf", "multimon-ng",
    "dsd", "dsdcc", "libdsdcc1", "rtl-433", "acarsdec", "dumphfdl", "dumpvdl2", "dxlaprs-lora",
    "python3-digiham", "python3-meshtastic", "python3-bleak", "m17-demod", "hpsdrconnector",
    "dump1090-fa", "dump1090-fa-minimal", "skyaware978", "piaware", "nrsc5", "lame", "python3-paho-mqtt",
    # Q6A AIC8800 RF test tool (/usr/bin/wifi_test, bt_test)
    "aicrf-test",
})
PROHIBITED_PACKAGE_GLOBS = ("libhamlib*", "libsoapysdr0.9*", "kalibrate*", "gr-gsm*", "gr-iridium*", "digiham*",
                            "codecserver*", "libacars*", "dxlaprs-tetra*", "dump978-fa*", "trunk-recorder*",
                            "sdrtrunk*", "op25*")
# Distro/upstream builds carry TX plugins, pager modes or the rtl-sdr-blog fork;
# only the patched RX-only local repository builds (+labN) are allowed.
LAB_BUILD_ONLY_PACKAGES = frozenset({"dream", "librtlsdr0", "librtlsdr2", "rtl-sdr", "sdrangel", "sdrangelsrv",
                                     "sdrpp", "openwebrx", "satdump", "gpredict", "gr-satellites",
                                     "limesuiteng-cli"})
PROHIBITED_EXECUTABLES = frozenset({"wifi_test", "bt_test", "rigctl", "rigctld", "rtl_tcp", "soapysdrserver",
                                    "limegui", "limespi", "limei2c", "limecsr", "limeoem", "limeflash",
                                    "limevspa", "limeppsdo", "multimon-ng", "kal", "grgsm_livemon",
                                    "grgsm_decode", "iridium-extractor", "wsjtx", "fldigi", "qsstv", "direwolf", "urh"})
EXECUTABLE_DIRS = ("usr/bin", "usr/sbin", "usr/local/bin", "usr/local/sbin", "bin", "sbin")

# Q6A FCU760K Wi-Fi/BT (AIC8800, FE1.1s hub port 4). This staged root is the
# field/QUIET root: Wi-Fi/BT stay off in every profile it runs; only a separate
# home root may unblock Wi-Fi. Layers: modprobe blacklist + install /bin/false,
# udev authorized=0 on the observed FE1.1s port-4 path (any VID), WIFI_PWR_EN
# gpio-hog (bench gate W1-2, OPEN, not generated here), rfkill as second layer.
AIC8800_MODULES = ("aic_load_fw", "aic_load_fw_usb", "aic8800_fdrv", "aic8800_fdrv_usb",
                   "aic_btusb", "aic_btusb_usb", "btusb")
WIFI_BT_USB_VENDORS = frozenset({"a69c", "368b"})
RADIO_OFF_MODPROBE = "etc/modprobe.d/60-srrx-radio-off.conf"
RADIO_OFF_UDEV = "etc/udev/rules.d/60-srrx-wifi-bt-deauthorize.rules"
RADIO_OFF_UNIT = "srrx-radio-off.service"


class DeploymentError(ValueError):
    pass


def sha(path):
    # Streamed: the guard runs inside MemoryMax=64M/128M units and hashes a 1.6 GB image.
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def load(path):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise DeploymentError("duplicate JSON key")
            out[key] = value
        return out
    path = Path(path)
    if not 0 < path.stat().st_size < 4 * 1024 * 1024:
        raise DeploymentError("JSON size is invalid")
    return json.loads(path.read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(DeploymentError("nonfinite JSON")))


def keys(data, expected, label):
    if type(data) is not dict or set(data) != set(expected):
        raise DeploymentError(label + " has missing or unknown fields")


def _string(value, pattern, label):
    if type(value) is not str or not re.fullmatch(pattern, value):
        raise DeploymentError("unverified or invalid " + label)


def validate_devices(config):
    keys(config, ("schema_version", "board_compatible", "i2c", "pico", "usb", "lime", "wifi_bt"), "device bindings")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1 or config["board_compatible"] != "radxa,dragon-q6a":
        raise DeploymentError("only the explicit Q6A revision is supported")
    keys(config["i2c"], ("ina228", "control"), "I2C buses")
    paths = []
    for label, bus in config["i2c"].items():
        keys(bus, ("path", "of_fullname"), label)
        _string(bus["path"], r"/dev/i2c-[0-9]+", label + " character-device path")
        _string(bus["of_fullname"], r"/[A-Za-z0-9_,/@.+:-]+", label + " observed DT node")
        paths.append(bus["path"])
    if paths[0] == paths[1] or config["i2c"]["ina228"]["of_fullname"] == config["i2c"]["control"]["of_fullname"]:
        raise DeploymentError("I2C0 and I2C2 must be distinct observed buses")
    pico = config["pico"]
    keys(pico, ("path", "kind", "kernel_parent", "vid", "pid", "serial"), "Pico")
    if pico["path"] != "/dev/lab/pico":
        raise DeploymentError("Pico must use its validated /dev/lab/pico binding")
    if pico["kind"] == "platform":
        _string(pico["kernel_parent"], r"[0-9a-f]+\.serial", "Pico UART platform parent")
        if any(pico[k] is not None for k in ("vid", "pid", "serial")):
            raise DeploymentError("platform Pico binding cannot contain USB selectors")
    elif pico["kind"] == "usb":
        if pico["kernel_parent"] is not None:
            raise DeploymentError("USB Pico cannot also match a platform parent")
        _usb(pico)
    else:
        raise DeploymentError("Pico kind must be platform or usb")
    keys(config["usb"], ("rtl_a", "rtl_b", "hfplus"), "required USB receivers")
    identities = []
    for name, device in config["usb"].items():
        keys(device, ("vid", "pid", "serial", "path"), name)
        _usb(device)
        if device["path"] != {"rtl_a": "/dev/lab/rtla", "rtl_b": "/dev/lab/rtlb", "hfplus": "/dev/lab/hfplus"}[name]:
            raise DeploymentError("unexpected receiver device alias")
        identities.append((device["vid"], device["pid"], device["serial"]))
        expected_usb = ("03eb", "800c") if name == "hfplus" else ("0bda", "2838")
        if (device["vid"], device["pid"]) != expected_usb:
            raise DeploymentError("receiver VID/PID differs from the specified hardware")
    if config["usb"]["rtl_a"]["serial"] != "LABRXA" or config["usb"]["rtl_b"]["serial"] != "LABRXB" or len(set(identities)) != 3:
        raise DeploymentError("receiver identities are duplicate or differ from assigned A/B serials")
    keys(config["lime"], ("enabled", "pci_address", "device_path"), "Lime")
    if config["lime"]["enabled"] is not False:
        raise DeploymentError("Lime runtime release is disabled pending full native TX audit and hardware gates")
    if config["lime"]["pci_address"] is not None or config["lime"]["device_path"] is not None:
        raise DeploymentError("disabled Lime binding must not grant a raw device path")
    keys(config["wifi_bt"], ("fe11s_port4_usb_path",), "Wi-Fi/BT radio-off binding")
    # Kernel USB device name of FE1.1s port 4 as observed on the unit (lsusb -t,
    # /sys/bus/usb/devices), e.g. 1-1.4. udev deauthorizes any VID on this port.
    _string(config["wifi_bt"]["fe11s_port4_usb_path"], r"[1-9][0-9]*-[0-9]+(?:\.[0-9]+)*\.4",
            "observed FE1.1s port-4 USB path")
    return config


def _usb(device):
    _string(device["vid"], "[0-9a-f]{4}", "USB vendor ID")
    _string(device["pid"], "[0-9a-f]{4}", "USB product ID")
    # HF+ USB strings are literally 'AIRSPYHF SN:' followed by16 hex digits.
    # Spaces/colon are safe here; quotes, escapes and udev glob syntax are not.
    _string(device["serial"], "[A-Za-z0-9_ :.-]{4,64}", "observed USB serial")
    if device["serial"].lower() in {"none", "null", "unknown", "unverified", "example", "0000"}:
        raise DeploymentError("placeholder USB serial")


def udev_rules(config):
    validate_devices(config)
    rules = ["# Candidate only: review udevadm properties on Q6A; no uaccess/world permissions; " + PICO_GROUP + " has no login members."]
    for name, device in config["usb"].items():
        alias = device["path"][5:]
        rules.append(f'SUBSYSTEM=="usb", ENV{{DEVTYPE}}=="usb_device", ATTR{{idVendor}}=="{device["vid"]}", ATTR{{idProduct}}=="{device["pid"]}", ATTR{{serial}}=="{device["serial"]}", GROUP="lab", MODE="0660", SYMLINK+="{alias}", TAG+="systemd"')
    pico = config["pico"]
    # labd holds the Pico tty exclusively (TIOCEXCL + flock); ModemManager must not probe it with AT commands.
    if pico["kind"] == "platform":
        rules.append(f'SUBSYSTEM=="tty", KERNELS=="{pico["kernel_parent"]}", GROUP="{PICO_GROUP}", MODE="0660", ENV{{ID_MM_DEVICE_IGNORE}}="1", SYMLINK+="lab/pico", TAG+="systemd"')
    else:
        rules.append(f'SUBSYSTEM=="tty", ATTRS{{idVendor}}=="{pico["vid"]}", ATTRS{{idProduct}}=="{pico["pid"]}", ATTRS{{serial}}=="{pico["serial"]}", GROUP="{PICO_GROUP}", MODE="0660", ENV{{ID_MM_DEVICE_IGNORE}}="1", SYMLINK+="lab/pico", TAG+="systemd"')
    return "\n".join(rules) + "\n"


def radio_off_modprobe():
    """Field/QUIET root: the AIC8800 Wi-Fi/BT drivers and btusb can never load."""
    lines = ["# SR-RX field/QUIET root (STACK.md v2 5.2 FE1.1s P4, 1.2 #8): receive-only.",
             "# Q6A FCU760K Wi-Fi/BT (AIC8800) and btusb never load; rfkill is only the second layer."]
    for module in AIC8800_MODULES:
        lines += ["blacklist " + module, "install " + module + " /bin/false"]
    return "\n".join(lines) + "\n"


def radio_off_udev(config):
    validate_devices(config)
    path = config["wifi_bt"]["fe11s_port4_usb_path"]
    return ("# SR-RX field/QUIET root: deauthorize any USB device on FE1.1s port 4 (Q6A Wi-Fi/BT), by port path, not VID:PID.\n"
            f'ACTION=="add", SUBSYSTEM=="usb", ENV{{DEVTYPE}}=="usb_device", KERNEL=="{path}", ATTR{{authorized}}="0"\n')


def radio_off_unit():
    # Same kernel call as `rfkill block wlan|bluetooth`; util-linux rfkill is not
    # in every Ubuntu image, so the project's own module writes /dev/rfkill.
    return ("[Unit]\nDescription=SR-RX receive-only: rfkill block wlan and bluetooth (second layer)\n"
            "DefaultDependencies=no\nAfter=systemd-rfkill.service\nBefore=srrx.service network-pre.target\n"
            "Wants=network-pre.target\n\n[Service]\nType=oneshot\nRemainAfterExit=yes\n"
            "Environment=PYTHONPATH=/opt/srrx/software\n"
            "ExecStart=/usr/bin/python3 -m srrx.rfkill block\n\n"
            "[Install]\nWantedBy=sysinit.target\n")


def _read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return None


def radio_off_issues(config=None, root=Path("/")):
    """Read-only receive-only self-check of the Q6A Wi-Fi/BT radio; fails closed."""
    root = Path(root)
    issues = []
    if _read(root / RADIO_OFF_MODPROBE) != radio_off_modprobe().strip():
        issues.append("Wi-Fi/BT modprobe blacklist with install /bin/false missing or modified: /" + RADIO_OFF_MODPROBE)
    modules = _read(root / "proc/modules")
    if modules is None:
        issues.append("loaded kernel module list unavailable; Wi-Fi/BT radio-off unverified")
    else:
        loaded = {line.split()[0].replace("-", "_") for line in modules.splitlines() if line.split()}
        found = sorted(loaded.intersection(AIC8800_MODULES))
        if found:
            issues.append("Wi-Fi/BT kernel modules loaded: " + ",".join(found))
    for device in sorted((root / "sys/class/rfkill").glob("rfkill*")):
        kind = _read(device / "type")
        if kind in ("wlan", "bluetooth") and "1" not in (_read(device / "soft"), _read(device / "hard")):
            issues.append("rfkill " + kind + " not blocked: " + device.name)
    for netdev in sorted((root / "sys/class/net").glob("*")):
        if (netdev / "wireless").exists() or (netdev / "phy80211").exists():
            issues.append("wireless network device present: " + netdev.name)
    if any((root / "sys/class/bluetooth").glob("hci*")):
        issues.append("Bluetooth hci device present")
    for device in sorted((root / "sys/bus/usb/devices").glob("*")):
        if (_read(device / "idVendor") or "").lower() in WIFI_BT_USB_VENDORS and _read(device / "authorized") != "0":
            issues.append("Wi-Fi/BT USB device authorized: " + device.name)
    if config is not None:
        try:
            expected_rule = radio_off_udev(config).strip()
        except (ValueError, KeyError, TypeError) as exc:
            issues.append("Wi-Fi/BT radio-off binding invalid: " + str(exc))
        else:
            if _read(root / RADIO_OFF_UDEV) != expected_rule:
                issues.append("FE1.1s port-4 authorized=0 udev rule missing or modified: /" + RADIO_OFF_UDEV)
            port = root / "sys/bus/usb/devices" / config["wifi_bt"]["fe11s_port4_usb_path"]
            if port.exists() and (_read(port / "authorized") != "0" or any(port.glob("*:*/driver"))):
                issues.append("USB device on FE1.1s port 4 is authorized or has a bound driver")
    return issues


def prohibited_installed(installed):
    """Names of installed packages that the receive-only/privacy rules forbid."""
    found = set()
    for name, version in installed.items():
        if name in PROHIBITED_PACKAGES or any(fnmatch.fnmatchcase(name, pattern) for pattern in PROHIBITED_PACKAGE_GLOBS):
            found.add(name)
        elif name in LAB_BUILD_ONLY_PACKAGES and not re.search(r"\+lab[0-9]*", version or ""):
            found.add(name + " (not a +lab RX-only build)")
    return sorted(found)


def prohibited_executables(root=Path("/")):
    found = set()
    for directory in EXECUTABLE_DIRS:
        try:
            names = [p.name for p in (Path(root) / directory).iterdir()]
        except OSError:
            continue
        found.update("/" + directory + "/" + n for n in names if n.lower() in PROHIBITED_EXECUTABLES)
    return sorted(found)


def command(args, limit=100_000):
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=10)
        if len(out.stdout) > limit:  # fail closed: a cut inventory would silently omit packages
            return {"returncode": -2, "error": "output exceeds bound", "stdout": "", "stderr": ""}
        return {"returncode": out.returncode, "stdout": out.stdout, "stderr": out.stderr[:1000]}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"returncode": -1, "error": str(exc)}


def device_node(name, path):
    """Live /dev/lab node: no access for others; the Pico UART only via a member-less group."""
    node = Path(path).stat()
    if not stat.S_ISCHR(node.st_mode):
        raise DeploymentError(name + " is not a character device")
    if node.st_mode & 0o007:
        raise DeploymentError(name + " grants access to other users")
    if name == "pico":
        import grp, pwd
        group = grp.getgrnam(PICO_GROUP)
        members = set(group.gr_mem) | {u.pw_name for u in pwd.getpwall() if u.pw_gid == group.gr_gid}
        if node.st_gid != group.gr_gid or members - {"labd"}:
            raise DeploymentError("Pico UART must belong to member-less group " + PICO_GROUP)
    return node


def doctor(config=None):
    """Read metadata only. No i2cdetect, EEPROM, serial writes or SDR opens."""
    report = {"read_only": True, "architecture": platform.machine(), "kernel": platform.release(),
              "issues": [], "hardware_ready": False}
    os_release = {}
    if Path("/etc/os-release").exists():
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                os_release[k] = v.strip('"')
    report["distribution"] = {k: os_release.get(k) for k in ("ID", "VERSION_ID", "VERSION_CODENAME")}
    try:
        report["dt_compatible"] = Path("/proc/device-tree/compatible").read_bytes().rstrip(b"\0").decode().split("\0")
    except OSError:
        report["dt_compatible"] = []
    expected = json.loads((HERE / "sources.lock.json").read_text())["target"]
    if report["architecture"] != expected["architecture"] or report["kernel"] != expected["kernel"]:
        report["issues"].append("architecture/kernel differs from pinned Q6A target")
    if os_release.get("ID") != "ubuntu" or os_release.get("VERSION_CODENAME") != "noble":
        report["issues"].append("distribution is not Ubuntu noble")
    if "radxa,dragon-q6a" not in report["dt_compatible"]:
        report["issues"].append("Q6A DT compatibility not observed")
    report["packages"] = command(["dpkg-query", "-W", "-f=${binary:Package}\t${Version}\t${db:Status-Status}\n"], limit=8 * 1024 * 1024)
    installed, present = {}, {}
    if report["packages"]["returncode"]:
        report["issues"].append("installed package inventory unavailable")
    else:
        for row in report["packages"]["stdout"].splitlines():
            fields = row.split("\t")
            if len(fields) == 3 and fields[2] == "installed":
                installed[fields[0].split(":", 1)[0]] = fields[1]
            # Unpacked/half-configured/triggers-pending packages already have files on disk.
            if len(fields) == 3 and fields[2] not in ("not-installed", "config-files"):
                present[fields[0].split(":", 1)[0]] = fields[1]
        requirements = load(HERE / "dependencies.json")["required_target_packages"]
        for name, versions in requirements.items():
            if installed.get(name) not in versions:
                report["issues"].append("missing/different pinned package: " + name)
        prohibited = prohibited_installed(present)
        if prohibited:
            report["issues"].append("prohibited packages installed: " + ",".join(prohibited))
    executables = prohibited_executables()
    if executables:
        report["issues"].append("prohibited TX/private-content executables present: " + ",".join(executables))
    radio = radio_off_issues(config)
    report["radio_off"] = {"status": "BLOCKED" if radio else "RADIO_OFF_OBSERVED", "issues": radio,
                           "wifi_pwr_en_hog": "OPEN (bench gate W1-2)"}
    report["issues"].extend(radio)
    try:
        report["bios_version"] = Path("/sys/class/dmi/id/bios_version").read_text().strip()
    except OSError:
        report["bios_version"] = None
    if not (report["bios_version"] or "").startswith("6.0.260120"):
        report["issues"].append("pinned BIOS260120 not observed; no flash action is performed")
    report["block_inventory"] = command(["lsblk", "-J", "-o", "NAME,TYPE,SIZE,ROTA,LOG-SEC,MOUNTPOINTS"])
    if config is None:
        report["issues"].append("explicit device bindings are missing")
    else:
        try:
            validate_devices(config)
            report["observed_devices"] = {}
            for label, bus in config["i2c"].items():
                path = Path(bus["path"])
                if not stat.S_ISCHR(path.stat().st_mode):
                    raise DeploymentError(label + " is not a character device")
                node = Path("/sys/class/i2c-dev") / path.name / "device/of_node"
                actual = "/" + node.resolve(strict=True).as_posix().split("/sys/firmware/devicetree/base/", 1)[-1]
                if actual != bus["of_fullname"]:
                    raise DeploymentError(label + " OF node differs from declared wiring")
            devices = dict(config["usb"], pico=config["pico"])
            for name, device in devices.items():
                path = Path(device["path"])
                device_node(name, path)
                result = command(["udevadm", "info", "--query=property", "--name", str(path)])
                if result["returncode"]:
                    raise DeploymentError("udevadm could not identify " + name)
                properties = dict(l.split("=", 1) for l in result["stdout"].splitlines() if "=" in l)
                if name == "pico" and device["kind"] == "platform":
                    if device["kernel_parent"] not in properties.get("DEVPATH", "").split("/"):
                        raise DeploymentError("Pico platform UART parent differs")
                else:
                    # ID_SERIAL_SHORT can normalize spaces. Match the raw USB
                    # ancestor attributes used by ATTR/ATTRS rules instead.
                    ancestor = Path("/sys") / properties.get("DEVPATH", "").lstrip("/")
                    actual_usb = None
                    while ancestor != Path("/sys") and ancestor.is_relative_to("/sys"):
                        if all((ancestor / k).is_file() for k in ("idVendor", "idProduct", "serial")):
                            actual_usb = tuple((ancestor / k).read_text().rstrip("\n") for k in ("idVendor", "idProduct", "serial"))
                            break
                        ancestor = ancestor.parent
                    if actual_usb != (device["vid"], device["pid"], device["serial"]):
                        raise DeploymentError(name + " live raw VID/PID/serial differs")
                report["observed_devices"][name] = str(path.resolve())
        except (OSError, ValueError, RuntimeError, KeyError) as exc:
            report["issues"].append(str(exc))
    report["status"] = "TARGET_METADATA_OK" if not report["issues"] else "BLOCKED"
    return report


def verify_cache(cache, components=None, include_core=True):
    lock = load(HERE / "sources.lock.json")
    selected = set([c["id"] for c in lock["components"]] if components is None else components)
    if selected - {c["id"] for c in lock["components"]}:
        raise DeploymentError("unknown source component")
    entries = [{"path": a["cache_path"], "sha256": a["sha256"], "size": a["size"]} for a in lock["artifacts"]] if include_core else []
    for component in lock["components"]:
        if component["id"] in selected:
            if component["commit"] is None or not component["ref_verified"]:
                raise DeploymentError("primary source pin unresolved: " + component["id"])
            entries.append({"path": component["source_cache_path"], "sha256": component["source_archive_sha256"], "size": component.get("source_archive_size")})
    root = Path(cache).resolve(strict=True)
    for item in entries:
        if item["sha256"] is None:
            raise DeploymentError("source archive SHA256 unresolved: " + item["path"])
        relative = Path(item["path"])
        path = (root / relative).resolve(strict=True)
        if relative.is_absolute() or ".." in relative.parts or not path.is_relative_to(root) or not path.is_file():
            raise DeploymentError("unsafe/missing cache entry")
        if sha(path) != item["sha256"] or (item["size"] is not None and path.stat().st_size != item["size"]):
            raise DeploymentError("offline cache digest/size differs: " + item["path"])
    return {"status": "CACHE_BYTES_VERIFIED", "entries": len(entries), "includes_core": include_core, "hardware_ready": False}


def verify_build(prefix, manifest):
    """Exact file allowlist plus known TX exclusions; not a universal TX proof."""
    keys(manifest, ("schema_version", "status", "files", "allowed_modules", "source_audit", "tx_negative_tests"), "build manifest")
    if manifest["schema_version"] != 1 or manifest["status"] != "REVIEWED" or not manifest["files"]:
        raise DeploymentError("build manifest is OPEN/unreviewed")
    root = Path(prefix).resolve(strict=True)
    files = {}
    modules = []
    for path in sorted(root.rglob("*")):
        # is_dir() follows links and rglob does not descend into linked dirs: check targets first.
        link = path.resolve(strict=True) if path.is_symlink() else None
        if link is not None and not link.is_relative_to(root):
            raise DeploymentError("external staged symlink")
        if link is None and path.is_dir():
            continue
        relative = path.relative_to(root).as_posix()
        if not path.is_file() and not (link is not None and link.is_dir()):
            raise DeploymentError("non-regular staged file")
        lower = relative.lower()
        if any(part.lower() in BAD_PARTS for part in path.relative_to(root).parts) or path.name.lower() in BAD_NAMES:
            raise DeploymentError("prohibited TX/control executable or plugin: " + relative)
        if link is not None and link.is_dir():
            # Internal alias (e.g. venv lib64 -> lib) is itself allowlisted; its real target is walked.
            files[relative] = "symlink:" + link.relative_to(root).as_posix()
            continue
        if ".so" in path.name:
            modules.append(relative)
            if any(term in lower for term in BAD_MODULE_WORDS):
                raise DeploymentError("unsupported TX-capable/privacy plugin: " + relative)
            if "limesuite" in lower:
                raise DeploymentError("Lime runtime library is experimental; complete native TX audit is OPEN")
        files[relative] = sha(path)
    if files != manifest["files"] or sorted(modules) != sorted(manifest["allowed_modules"]):
        raise DeploymentError("staged file hashes/module allowlist differ; unknown files rejected")
    for name in ("source_audit", "tx_negative_tests"):
        record = manifest[name]
        keys(record, ("status", "report"), name)
        if record["status"] != "PASS":
            raise DeploymentError(name + " is OPEN")
        keys(record["report"], ("path", "sha256"), name + " report")
        report = (root / str(record["report"]["path"])).resolve(strict=True)
        if not report.is_relative_to(root) or not report.is_file() or sha(report) != record["report"]["sha256"] or report.stat().st_size < 32:
            raise DeploymentError(name + " evidence mismatch")
    return {"status": "REVIEWED_BUILD_FILES_MATCH", "files": len(files), "hardware_ready": False,
            "scope": "Exact reviewed files and known exclusions checked; hardware/native API behavior requires independent evidence."}


def stage(destination, config=None):
    destination = Path(destination).resolve()
    if destination.exists() or destination.is_relative_to(PROJECT) or PROJECT.is_relative_to(destination) or destination == Path("/"):
        raise DeploymentError("stage needs a NEW directory outside the checkout and host prefixes")
    if str(destination).startswith(("/etc/", "/usr/", "/opt/", "/boot/", "/dev/", "/sys/", "/proc/")):
        raise DeploymentError("host installation prefixes cannot be staging destinations")
    if config is not None:
        validate_devices(config)
    for directory in ("software", "firmware", "design", "deployment"):
        if any(p.is_symlink() and not p.resolve().is_relative_to(PROJECT) for p in (PROJECT / directory).rglob("*")):
            raise DeploymentError("external source symlink cannot be staged")
    rootfs = destination / "rootfs"
    project = rootfs / "opt/srrx"
    for name in ("software", "firmware", "design", "deployment"):
        shutil.copytree(PROJECT / name, project / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "tests", "upstream-fixtures"))
    etc = rootfs / "etc/srrx"
    units = rootfs / "etc/systemd/system"
    etc.mkdir(parents=True)
    units.mkdir(parents=True)
    for unit in (PROJECT / "software/systemd").glob("*.service"):
        if unit.name == "srrx-menu.service":
            user_units = rootfs / "usr/lib/systemd/user"
            user_units.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(unit, user_units / unit.name)
            continue
        shutil.copyfile(unit, units / unit.name)
        dropin = units / (unit.name + ".d")
        dropin.mkdir()
        (dropin / "10-radio-off.conf").write_text("[Unit]\nRequires=" + RADIO_OFF_UNIT + "\nAfter=" + RADIO_OFF_UNIT + "\n")
        (dropin / "20-release-guard.conf").write_text("[Service]\nExecStartPre=/usr/bin/python3 -B /opt/srrx/deployment/deploy.py release-guard --devices /etc/srrx/devices.json --acceptance /etc/srrx/acceptance.json --release /etc/srrx/release.json --build-manifest /etc/srrx/build-manifest.json --cache /srv/srrx-cache\n")
    (units / RADIO_OFF_UNIT).write_text(radio_off_unit())
    modprobe = rootfs / RADIO_OFF_MODPROBE
    modprobe.parent.mkdir(parents=True)
    modprobe.write_text(radio_off_modprobe())
    for name in ("release.template.json", "build-manifest.template.json", "devices.template.json"):
        shutil.copyfile(HERE / name, etc / name)
    shutil.copyfile(PROJECT / "software/config/acceptance.template.json", etc / "acceptance.template.json")
    if config:
        (etc / "devices.json").write_text(json.dumps(config, indent=2) + "\n")
        (etc / "devices.env").write_text("SRRX_I2C0=" + config["i2c"]["ina228"]["path"] + "\nSRRX_I2C2=" + config["i2c"]["control"]["path"] + "\nSRRX_PICO=/dev/lab/pico\n")
        rules = rootfs / "etc/udev/rules.d"
        rules.mkdir(parents=True)
        (rules / "70-srrx-serial-bound.rules").write_text(udev_rules(config))
        (rootfs / RADIO_OFF_UDEV).write_text(radio_off_udev(config))
    files = {p.relative_to(rootfs).as_posix(): sha(p) for p in sorted(rootfs.rglob("*")) if p.is_file()}
    (destination / "stage-files.json").write_text(json.dumps({"schema_version": 1, "status": "STAGED_ONLY", "files": files}, indent=2) + "\n")
    (destination / "INSTALL_PLAN.txt").write_text("STAGED ONLY. No services enabled and no hardware acceptance supplied.\nReview software/DEPLOYMENT.md, run doctor and all release guards, then package rootfs via signed local repository.\nField/QUIET root: Wi-Fi/BT modprobe blacklist (install /bin/false), FE1.1s port-4 authorized=0 rule and rfkill unit are staged; the WIFI_PWR_EN gpio-hog (W1-2) is OPEN and not generated.\nDo not copy over /etc acceptance files, repartition UFS, flash BIOS, run rsetup or auto-enable units.\nA/B installation is a separate bench/recovery procedure; no activation command is generated here.\n")
    return {"status": "STAGED_ONLY", "directory": str(destination), "files": len(files), "hardware_ready": False, "services_enabled": False}


def release_guard(devices, acceptance, release, build_manifest, cache):
    config = validate_devices(load(devices))
    report = doctor(config)
    if report["issues"]:
        raise DeploymentError("target doctor blocked: " + "; ".join(report["issues"]))
    sys.path.insert(0, str(PROJECT / "software"))
    from srrx.commissioning import load_acceptance
    # Runs at every start: an offline RTC behind accepted_at must not block; floor/ordering still apply.
    accepted = load_acceptance(acceptance, PROJECT, clock_check=False)
    record = load(release)
    keys(record, ("schema_version", "status", "hardware_unit_id", "device_bindings_sha256", "build_manifest_sha256", "source_lock_sha256", "profile", "base_image_sha256", "offline_snapshot"), "release")
    if (record["schema_version"] != 1 or record["status"] != "REVIEWED" or record["profile"] != "controller"
            or record["hardware_unit_id"] != accepted["hardware_unit_id"]):
        raise DeploymentError("release is OPEN/unreviewed, wrong unit or unsupported profile")
    for field, path in (("device_bindings_sha256", devices), ("build_manifest_sha256", build_manifest), ("source_lock_sha256", HERE / "sources.lock.json")):
        if record[field] != sha(path):
            raise DeploymentError("release binding differs: " + field)
    lock = load(HERE / "sources.lock.json")
    if lock["target"]["base_image_sha256"] is None or record["base_image_sha256"] != lock["target"]["base_image_sha256"]:
        raise DeploymentError("Radxa OS r2 base image SHA256 binding is missing or mismatched")
    snapshot = record["offline_snapshot"]
    keys(snapshot, ("status", "path", "sha256"), "offline package snapshot")
    if snapshot["status"] != "REVIEWED" or sha(snapshot["path"]) != snapshot["sha256"]:
        raise DeploymentError("offline signed repository snapshot metadata not bound")
    # Controller-only deployment needs the immutable base/kernel cache. The
    # full radio application suite has30 separate unresolved source archives.
    verify_cache(cache, components=[])
    verify_build(PROJECT, load(build_manifest))
    return {"status": "RELEASE_GUARDS_MATCH", "hardware_unit_id": accepted["hardware_unit_id"], "services_enabled": False}


def stage_ab(config, destination):
    """Generate BLS candidates only; no partitions, bootctl or activation."""
    keys(config, ("schema_version", "active_slot", "root_a_partuuid", "root_b_partuuid",
                  "base_cmdline_without_root", "kernel_efi_path", "initrd_efi_path", "lab_dtb_efi_path",
                  "rescue_kernel_efi_path", "rescue_initrd_efi_path", "rescue_dtb_efi_path"), "A/B staging")
    if config["schema_version"] != 1 or config["active_slot"] not in ("A", "B"):
        raise DeploymentError("invalid A/B schema or observed active slot")
    for key in ("root_a_partuuid", "root_b_partuuid"):
        _string(config[key], r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", key)
    if config["root_a_partuuid"].lower() == config["root_b_partuuid"].lower():
        raise DeploymentError("A/B PARTUUIDs must be distinct")
    for key in ("kernel_efi_path", "initrd_efi_path", "lab_dtb_efi_path", "rescue_kernel_efi_path", "rescue_initrd_efi_path", "rescue_dtb_efi_path"):
        _string(config[key], r"/[A-Za-z0-9_./+-]+", "verified ESP file " + key)
        if ".." in Path(config[key]).parts:
            raise DeploymentError("ESP path traversal")
    _string(config["base_cmdline_without_root"], r"[A-Za-z0-9_.,:/=+ -]+", "observed full base cmdline")
    tokens = config["base_cmdline_without_root"].split()
    if any(t.startswith("root=") for t in tokens) or "clk_ignore_unused" in tokens or len(tokens) < 3:
        raise DeploymentError("base cmdline must preserve observed options, without root= or clk_ignore_unused")
    destination = Path(destination).resolve()
    if (destination.exists() or str(destination).startswith(("/boot/", "/etc/", "/usr/", "/opt/", "/sys/", "/proc/", "/dev/"))
            or destination.is_relative_to(PROJECT) or PROJECT.is_relative_to(destination)):
        raise DeploymentError("A/B output must be a new independent staging directory")
    entries = destination / "loader/entries"
    entries.mkdir(parents=True)
    for slot in ("A", "B"):
        name = "lab" + slot + (".conf" if slot == config["active_slot"] else "+3.conf")
        options = " ".join(tokens) + " root=PARTUUID=" + config["root_" + slot.lower() + "_partuuid"]
        (entries / name).write_text(f'title SR-RX candidate {slot}\nlinux {config["kernel_efi_path"]}\ninitrd {config["initrd_efi_path"]}\ndevicetree {config["lab_dtb_efi_path"]}\noptions {options}\n')
    active_root = config["root_" + config["active_slot"].lower() + "_partuuid"]
    (entries / "rescue.conf").write_text(f'title SR-RX existing 6.18.2-3 rescue candidate\nlinux {config["rescue_kernel_efi_path"]}\ninitrd {config["rescue_initrd_efi_path"]}\ndevicetree {config["rescue_dtb_efi_path"]}\noptions {" ".join(tokens)} root=PARTUUID={active_root}\n')
    (destination / "loader/loader.conf").write_text("default lab" + config["active_slot"] + ".conf\ntimeout 3\neditor no\n")
    return {"status": "AB_CANDIDATES_ONLY", "directory": str(destination), "active_slot_changed": False,
            "warning": "Review actual ESP file formats, initramfs/root mounting, merged DTB and forced-failure rollback on bench; activation unsupported."}


def bundle(stage_directory, output):
    """Reproducible tar.gz of verified staged bytes, with zeroed owner/time."""
    directory = Path(stage_directory).resolve(strict=True)
    rootfs = directory / "rootfs"
    record = load(directory / "stage-files.json")
    keys(record, ("schema_version", "status", "files"), "stage manifest")
    if record["schema_version"] != 1 or record["status"] != "STAGED_ONLY":
        raise DeploymentError("not a staged-only tree")
    files = {}
    for path in rootfs.rglob("*"):
        if path.is_symlink() or (not path.is_dir() and not path.is_file()):
            raise DeploymentError("bundle refuses symlinks and special files")
        if path.is_file():
            files[path.relative_to(rootfs).as_posix()] = sha(path)
    if not files or files != record["files"]:
        raise DeploymentError("staged files changed; regenerate candidate deliberately")
    output = Path(output).resolve()
    if output.exists() or output.is_relative_to(directory) or str(output).startswith(("/etc/", "/usr/", "/opt/", "/boot/", "/sys/", "/proc/", "/dev/")):
        raise DeploymentError("bundle output must be a new independent artifact")
    with output.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(mode="w", fileobj=compressed, format=tarfile.PAX_FORMAT) as archive:
                for path in sorted(rootfs.rglob("*")):
                    info = archive.gettarinfo(str(path), arcname=path.relative_to(rootfs).as_posix())
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = ""
                    info.mode = 0o755 if path.is_dir() else 0o644
                    with path.open("rb") if path.is_file() else open(os.devnull, "rb") as content:
                        archive.addfile(info, content if path.is_file() else None)
    return {"status": "STAGED_ARCHIVE_ONLY", "path": str(output), "sha256": sha(output), "services_enabled": False}


def check():
    for root in (HERE, PROJECT / "software/srrx"):
        for path in root.rglob("*.py"):
            if "upstream-fixtures" not in path.parts:
                ast.parse(path.read_text(), filename=str(path))
    lock = load(HERE / "sources.lock.json")
    if lock["schema_version"] != 1 or lock["status"] != "BLOCKED" or len({c["id"] for c in lock["components"]}) != len(lock["components"]):
        raise DeploymentError("invalid source lock")
    for component in lock["components"]:
        if component["commit"] is not None:
            _string(component["commit"], "[0-9a-f]{40}", "full pinned commit")
        if component["source_archive_sha256"] is not None:
            _string(component["source_archive_sha256"], "[0-9a-f]{64}", "archive SHA256")
    from vendor_patch import check_fixtures
    check_fixtures()
    return {"status": "STAGING_TOOLS_CHECKED", "hardware_ready": False, "unresolved_source_archives": sum(c["source_archive_sha256"] is None for c in lock["components"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    commands.add_parser("check")
    inventory = commands.add_parser("doctor")
    inventory.add_argument("--devices", type=Path)
    staging = commands.add_parser("stage")
    staging.add_argument("--dest", type=Path, required=True)
    staging.add_argument("--devices", type=Path)
    rules = commands.add_parser("udev")
    rules.add_argument("--devices", type=Path, required=True)
    cache = commands.add_parser("verify-cache")
    cache.add_argument("--cache", type=Path, required=True)
    cache.add_argument("--component", action="append")
    cache.add_argument("--sources-only", action="store_true", help="verify selected source bytes without claiming core image/deb cache coverage")
    build = commands.add_parser("verify-build")
    build.add_argument("--prefix", type=Path, required=True)
    build.add_argument("--manifest", type=Path, required=True)
    ab = commands.add_parser("stage-ab")
    ab.add_argument("--config", type=Path, required=True)
    ab.add_argument("--dest", type=Path, required=True)
    package = commands.add_parser("bundle")
    package.add_argument("--stage-dir", type=Path, required=True)
    package.add_argument("--output", type=Path, required=True)
    guard = commands.add_parser("release-guard")
    for name in ("devices", "acceptance", "release", "build-manifest", "cache"):
        guard.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.operation == "check": result = check()
        elif args.operation == "doctor": result = doctor(load(args.devices) if args.devices else None)
        elif args.operation == "stage": result = stage(args.dest, load(args.devices) if args.devices else None)
        elif args.operation == "udev": print(udev_rules(load(args.devices)), end=""); return
        elif args.operation == "verify-cache": result = verify_cache(args.cache, args.component, not args.sources_only)
        elif args.operation == "verify-build": result = verify_build(args.prefix, load(args.manifest))
        elif args.operation == "stage-ab": result = stage_ab(load(args.config), args.dest)
        elif args.operation == "bundle": result = bundle(args.stage_dir, args.output)
        else: result = release_guard(args.devices, args.acceptance, args.release, args.build_manifest, args.cache)
        print(json.dumps(result, indent=2))
        if result.get("status") == "BLOCKED": sys.exit(2)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
