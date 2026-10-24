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
# LC76G on the board's fixed UART6 (alias serial1 = .../serial@998000, build/04 pinout): its rule
# needs no devices.json entry. devices.json schema_version 1 is still an exact key set, and that set
# includes wifi_bt (the FE1.1s port-4 radio-off binding). Read-only group.
GNSS_GROUP, GNSS_KERNEL_PARENT = "srrx-gnss", "998000.serial"
# Single source of the forbidden packages (names, globs, version rules such as "+lab builds only")
# and of the extra forbidden basenames, for doctor and for selftest.py RX-01a/RX-01b.
POLICY = HERE / "receive-only-policy.json"
VERSION_RULE_KEYS = ("allow_only", "allow_only_globs", "forbid_globs", "forbid_at_least", "require_substring", "require_lab_build")
# require_lab_build: the version ends in the local repository's +labN marker, or in the -0labN Debian
# revision of a locked lab rebuild (gr-satellites 5.10.0~git20260922-0lab1, sources.lock.json).
LAB_BUILD = re.compile(r"(?:\+lab|-0lab)[1-9][0-9]*\Z")
VERSION_NOTE = " (version not allowed by the receive-only policy)"

# Floor of the policy (STACK.md v2 §5.4 "Заборонено" and "Закріплено на -1", 1.2 #10, 4.3
# excluded services, 5.2 FE1.1s P4): tests require receive-only-policy.json to keep covering
# every name and glob here. Doctor never applies these two on their own, so it cannot reach
# another verdict than RX-01a. Only TX-capable tools, decoders of private content and their
# codec/driver packages are listed; kernel and Qualcomm firmware pins are version locks.
# Region is Europe, so the US-only profile packages (multimon-ng EAS, nrsc5, dump978-fa,
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
# Distro/upstream builds carry TX plugins, pager modes or the rtl-sdr-blog fork: only the patched
# RX-only local repository builds are allowed. That rule lives in the policy (version_rule
# require_lab_build); deploy.LAB_BUILD_ONLY_PACKAGES is derived from it on access (__getattr__).
# Doctor checks these basenames together with BAD_NAMES and the policy forbidden_basenames.
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
# srrx.service waits (Wants=+After=) for the udev-tagged /dev/lab nodes its release guard stats, at
# most LAB_DEVICE_TIMEOUT_S per device unit instead of DefaultDeviceTimeoutSec (90 s). Config-only:
# the static unit stays device-free, so the QEMU simulation unit never waits for absent devices.
LAB_DEVICE_DROPIN = "30-lab-devices.conf"
DEVICE_TIMEOUT_DROPIN = "50-srrx-device-timeout.conf"
LAB_DEVICE_TIMEOUT_S = 30
# GNSS time chain (software/GNSS-UART.md): SRRX_GNSS in devices.env selects the one UART6 reader,
# gpsd (STACK default) or srrx-locationd raw; off runs neither orchestration nor locationd.
GNSS_MODES = ("gpsd", "raw", "off")
GNSS_DEVICE = "/dev/lab/gnss"
GNSS_MODE_DROPIN = "40-gnss-mode.conf"
GNSS_CONFIG_UNIT = "srrx-gnss-config.service"
GNSS_POLKIT_RULE = "etc/polkit-1/rules.d/60-srrx-gnss-config.rules"
# No release guard for these: they energize nothing, run as srrx-loc/_chrony (no access to the
# acceptance and cache records), and the oneshot must not hash the cache each time labd starts it.
# srrx-passes@ is started only by labd, after labd's own guard, and opens no device (DEPLOYMENT.md).
RELEASE_GUARD_EXEMPT = frozenset({"srrx-locationd.service", "srrx-timegate.service", GNSS_CONFIG_UNIT, "srrx-passes@.service"})


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
    if type(config) is dict and "wifi_bt" not in config:
        raise DeploymentError("devices.json predates the radio-off binding: add wifi_bt.fe11s_port4_usb_path")
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
        if pico["kernel_parent"] == GNSS_KERNEL_PARENT:
            # 71-srrx-gnss.rules would re-own that tty (srrx-gnss 0640) and alias it as lab/gnss.
            raise DeploymentError("Pico UART parent is the fixed LC76G UART6 " + GNSS_KERNEL_PARENT)
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
    if pico["kind"] == "usb" and (pico["vid"], pico["pid"], pico["serial"]) in identities:
        # Its usb_device would also get the receiver rule (GROUP lab, raw usbfs writes past srrx-pico).
        raise DeploymentError("USB Pico identity equals a receiver: one device would get two bindings")
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


def gnss_udev_rules():
    """/dev/lab/gnss by UART6 platform parent, never by ttyHS number (probe order).

    0640: the group reads, nobody else; srrx.gnss_uart opens O_RDONLY and gpsd runs
    with -b (no receiver writes, STACK.md gpsd row). No ModemManager AT probe. Create
    the group before installing the rule: udev logs an unresolved GROUP and keeps the
    node's previous group, so the rule alone is not a fail-closed guarantee. The live
    mode is a Q6A check (RUNTIME_ONLY).
    """
    return ("# Candidate only: LC76G UART6; " + GNSS_GROUP + " is a system group without login members;"
            " the raw reader and gpsd -b are exclusive by configuration.\n"
            f'SUBSYSTEM=="tty", KERNELS=="{GNSS_KERNEL_PARENT}", GROUP="{GNSS_GROUP}", MODE="0640", ENV{{ID_MM_DEVICE_IGNORE}}="1", SYMLINK+="lab/gnss", TAG+="systemd"\n')


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
    # DefaultDependencies=no: RequiresMountsFor= keeps it after the mount holding /opt/srrx.
    return ("[Unit]\nDescription=SR-RX receive-only: rfkill block wlan and bluetooth (second layer)\n"
            "DefaultDependencies=no\nRequiresMountsFor=/opt/srrx\nAfter=systemd-rfkill.service\nBefore=srrx.service network-pre.target\n"
            "Wants=network-pre.target\n\n[Service]\nType=oneshot\nRemainAfterExit=yes\n"
            "Environment=PYTHONPATH=/opt/srrx/software PYTHONDONTWRITEBYTECODE=1\n"
            # -B and a read-only system: never a __pycache__ in the hash-verified /opt/srrx tree.
            "ProtectSystem=strict\nExecStart=/usr/bin/python3 -B -m srrx.rfkill block\n\n"
            "[Install]\nWantedBy=sysinit.target\n")


def radio_off_dropin():
    """srrx.service only: the receiver never starts unless the rfkill second layer ran first. The
    shutdown bridge gets no such drop-in: a failed oneshot must not fail it with a dependency error."""
    return "[Unit]\nRequires=" + RADIO_OFF_UNIT + "\nAfter=" + RADIO_OFF_UNIT + "\n"


def guarded_devices(config):
    """The /dev/lab nodes doctor stats at every release-guard run: the three receivers and the Pico UART.
    lab/gnss is not one (labd never opens it; the gpsd chain owns it), nor are the /dev/i2c-N buses."""
    return dict(config["usb"], pico=config["pico"])


def guarded_device_paths(config):
    return {name: device["path"] for name, device in guarded_devices(config).items()}


def device_unit(path):
    """`systemd-escape --path --suffix=device` of a plain /dev/lab node. A name that would need
    \\x escaping (any '-' or other byte) is refused rather than escaped by hand."""
    if type(path) is not str or not re.fullmatch(r"/dev/lab/[a-z0-9]+", path):
        raise DeploymentError("device unit only for a plain /dev/lab/[a-z0-9]+ node: " + repr(path))
    return "dev-lab-" + path[len("/dev/lab/"):] + ".device"


def lab_device_dropin(paths):
    """srrx.service.d ordering after the device units of `paths`. Wants= only: a device that never
    appears times out its own job and the guard then fails closed in doctor (exit 2); never
    Requires=/BindsTo=, which would turn a missing receiver into a dependency failure or a stop."""
    units = " ".join(device_unit(path) for path in paths)
    return ("[Unit]\n# release guard (doctor) stats these udev-tagged /dev/lab nodes\n"
            "Wants=" + units + "\nAfter=" + units + "\n")


def device_timeout_dropin(seconds):
    """<device>.d drop-in bounding the wait for an absent node, the systemd-fstab-generator
    x-systemd.device-timeout mechanism (a device job otherwise waits DefaultDeviceTimeoutSec)."""
    if type(seconds) is not int or not 1 <= seconds <= 300:
        raise DeploymentError("device timeout must be 1..300 s")
    return "[Unit]\nJobRunningTimeoutSec=" + str(seconds) + "s\n"


def gnss_polkit_rule():
    """labd may start exactly srrx-gnss-config.service: no stop/restart, no other unit, no other user."""
    return ("// SR-RX (software/GNSS-UART.md): labd starts only the LC76G read-back/config oneshot.\n"
            "polkit.addRule(function(action, subject) {\n"
            '    if (action.id == "org.freedesktop.systemd1.manage-units" &&\n'
            '        action.lookup("unit") == "' + GNSS_CONFIG_UNIT + '" &&\n'
            '        action.lookup("verb") == "start" &&\n'
            '        subject.user == "labd") {\n'
            "        return polkit.Result.YES;\n"
            "    }\n"
            "});\n")


def gnss_mode_dropin(mode):
    """srrx-locationd.service.d: gpsd mode may reach loopback gpsd only; raw mode reads the UART
    (srrx-gnss group, after dev-lab-gnss.device). The static unit has neither."""
    if mode == "gpsd":
        return ("[Unit]\nWants=gpsd.socket\nAfter=gpsd.socket gpsd.service\n\n[Service]\n"
                "RestrictAddressFamilies=AF_INET AF_INET6\nIPAddressAllow=localhost\n")
    if mode == "raw":
        unit = device_unit(GNSS_DEVICE)
        return ("[Unit]\nWants=" + unit + "\nAfter=" + unit + "\nConflicts=gpsd.service gpsd.socket\n\n"
                "[Service]\nSupplementaryGroups=" + GNSS_GROUP + "\n")
    raise DeploymentError("SRRX_GNSS must be gpsd or raw for a locationd drop-in: " + repr(mode))


def _assignments(path):
    """KEY=value lines of an environment/defaults file (quotes stripped); None if absent."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[key.strip()] = value
    return values


def gnss_mode_issues(root=Path("/")):
    """Exactly one UART6 reader (build/07 §18): gpsd -n -b on /dev/lab/gnss, or srrx-locationd raw.

    Files only (doctor runs no systemctl): devices.env SRRX_GNSS, /etc/default/gpsd, gpsd enable
    links and the staged locationd drop-in. srrx-locationd itself also refuses raw mode while
    gpsd is active; the live check of both is a Q6A item (RUNTIME_ONLY)."""
    root = Path(root)
    try:
        # The release guard runs as labd: devices.env must be readable by it (systemd itself reads it as root).
        env = _assignments(root / "etc/srrx/devices.env")
        defaults = _assignments(root / "etc/default/gpsd")
    except OSError as exc:
        return ["GNSS reader configuration unreadable: " + (exc.filename or "") + " " + type(exc).__name__]
    if env is None:
        return []  # no deployment record: doctor reports the missing bindings elsewhere
    mode = env.get("SRRX_GNSS")
    if mode not in GNSS_MODES:
        return ["SRRX_GNSS missing or invalid in /etc/srrx/devices.env (gpsd, raw or off)"]
    devices = (defaults or {}).get("DEVICES", "").split()
    units = root / "etc/systemd/system"
    enabled = sorted({link.name for pattern in ("*.wants/gpsd.service", "*.wants/gpsd.socket")
                      for link in units.glob(pattern)})
    dropin = units / "srrx-locationd.service.d" / GNSS_MODE_DROPIN
    raw_group = dropin.is_file() and ("SupplementaryGroups=" + GNSS_GROUP) in dropin.read_text()
    issues = []
    if mode == "gpsd":
        options = (defaults or {}).get("GPSD_OPTIONS", "").split()
        if devices != [GNSS_DEVICE]:
            issues.append("gpsd mode: /etc/default/gpsd DEVICES must be exactly " + GNSS_DEVICE)
        if "-b" not in options or "-n" not in options:
            issues.append("gpsd mode: GPSD_OPTIONS must keep -n -b (gpsd never writes the receiver)")
        if (defaults or {}).get("USBAUTO") != "false":
            issues.append('gpsd mode: USBAUTO must be "false" (no hotplug devices)')
    if mode != "raw" and raw_group:
        issues.append("srrx-locationd holds " + GNSS_GROUP + " outside raw mode")
    if mode == "raw":
        if GNSS_DEVICE in devices:
            issues.append("raw mode: gpsd DEVICES still lists " + GNSS_DEVICE)
        if enabled:
            issues.append("raw mode: gpsd enabled (" + ",".join(enabled) + ")")
        if not raw_group:
            issues.append("raw mode: srrx-locationd lacks its " + GNSS_MODE_DROPIN + " drop-in")
    return issues


def _read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return None


def _bound_interface(port):
    """An interface directory (<port>:<config>.<n>) with a driver link; unreadable counts as bound.
    No glob: "*:*" is a drive pattern on a Windows host."""
    try:
        return any(":" in p.name and os.path.lexists(p / "driver") for p in port.iterdir())
    except OSError:
        return True


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
            if port.exists() and (_read(port / "authorized") != "0" or _bound_interface(port)):
                issues.append("USB device on FE1.1s port 4 is authorized or has a bound driver")
    return issues


def _order(c):
    if c == "~":
        return -1
    if c in "0123456789":
        return 0
    return ord(c) if c.isascii() and c.isalpha() else ord(c) + 256


def _verrevcmp(a, b):
    i = j = 0
    while i < len(a) or j < len(b):
        while (i < len(a) and a[i] not in "0123456789") or (j < len(b) and b[j] not in "0123456789"):
            ac, bc = _order(a[i]) if i < len(a) else 0, _order(b[j]) if j < len(b) else 0
            if ac != bc:
                return ac - bc
            i, j = i + 1, j + 1
        while i < len(a) and a[i] == "0":
            i += 1
        while j < len(b) and b[j] == "0":
            j += 1
        first = 0
        while i < len(a) and j < len(b) and a[i] in "0123456789" and b[j] in "0123456789":
            first = first or ord(a[i]) - ord(b[j])
            i, j = i + 1, j + 1
        if i < len(a) and a[i] in "0123456789":
            return 1
        if j < len(b) and b[j] in "0123456789":
            return -1
        if first:
            return first
    return 0


def deb_compare(a, b):
    """dpkg version ordering (epoch:upstream-revision, '~' sorts first)."""
    def split(version):
        if len(version) > 256:
            raise ValueError("version string too long")
        epoch, colon, rest = version.partition(":")
        if not colon:
            epoch, rest = "0", version
        if not epoch.isdigit():
            raise ValueError("invalid epoch")
        upstream, dash, revision = rest.rpartition("-")
        return (int(epoch), upstream, revision) if dash else (int(epoch), rest, "")
    (ea, ua, ra), (eb, ub, rb) = split(a), split(b)
    return (ea > eb) - (ea < eb) or _verrevcmp(ua, ub) or _verrevcmp(ra, rb)


def check_version_rule(rule, label):
    """The one version_rule vocabulary of the policy (doctor and selftest.load_policy)."""
    if type(rule) is not dict or not rule or set(rule) - set(VERSION_RULE_KEYS):
        raise DeploymentError(label + " version_rule has missing or unknown fields")
    for key, item in rule.items():
        if key == "require_lab_build":
            valid = item is True
        elif key in ("forbid_at_least", "require_substring"):
            valid = type(item) is str and bool(item)
        else:
            valid = type(item) is list and bool(item) and all(type(x) is str and x for x in item)
        if not valid:
            raise DeploymentError(label + " version_rule." + key + " has the wrong type or is empty")


def version_forbidden(rule, version):
    """True when a present version breaks its policy version_rule; None means presence alone."""
    if rule is None:
        return True
    if type(rule) is not dict or set(rule) - set(VERSION_RULE_KEYS) or type(version) is not str:
        return True  # unknown vocabulary or no version text: conservative
    try:
        return (("allow_only" in rule and version not in rule["allow_only"])
                or ("allow_only_globs" in rule and not any(fnmatch.fnmatchcase(version, p) for p in rule["allow_only_globs"]))
                or ("forbid_globs" in rule and any(fnmatch.fnmatchcase(version, p) for p in rule["forbid_globs"]))
                or ("forbid_at_least" in rule and deb_compare(version, rule["forbid_at_least"]) >= 0)
                or ("require_substring" in rule and rule["require_substring"] not in version)
                or ("require_lab_build" in rule and not LAB_BUILD.search(version)))
    except (ValueError, TypeError):
        return True  # unparsable target version: conservative


def receive_only_policy(path=None):
    """The policy's package and basename rules, read with the strict bounded load (duplicate keys,
    NaN/Infinity and files of 4 MiB or more are refused); any malformed entry fails closed."""
    policy = load(POLICY if path is None else path)
    entries = policy.get("forbidden_packages") if type(policy) is dict else None
    if type(entries) is not list or not entries:
        raise DeploymentError("receive-only policy lists no forbidden packages")
    for entry in entries:
        kind = [k for k in ("name", "glob") if type(entry) is dict and k in entry]
        if len(kind) != 1 or entry.get("check") not in ("presence", "pin_only") or type(entry[kind[0]]) is not str or not entry[kind[0]]:
            raise DeploymentError("receive-only policy has a malformed forbidden package entry")
        if "version_rule" in entry:
            check_version_rule(entry["version_rule"], "receive-only policy " + entry[kind[0]])
    basenames = policy.get("forbidden_basenames")
    if type(basenames) is not list or not all(type(e) is dict and type(e.get("name")) is str and e["name"] for e in basenames):
        raise DeploymentError("receive-only policy has malformed forbidden basenames")
    return policy


def prohibited_packages(path=None):
    """(names, globs) whose mere presence the receive-only policy forbids. Entries with a
    version_rule are decided per version (prohibited_installed, the same rule as selftest.py
    RX-01a); pin_only entries are RX-01a BLOCKED findings, not doctor issues."""
    names, globs = set(), set()
    for entry in receive_only_policy(path)["forbidden_packages"]:
        if entry["check"] == "presence" and "version_rule" not in entry:
            (names.add(entry["name"].lower()) if "name" in entry else globs.add(entry["glob"].lower()))
    return names, globs


def lab_build_only_packages(path=None):
    """Names the policy allows only as patched RX-only local builds (version_rule require_lab_build)."""
    return frozenset(e["name"].lower() for e in receive_only_policy(path)["forbidden_packages"]
                     if "name" in e and e["check"] == "presence" and (e.get("version_rule") or {}).get("require_lab_build") is True)


def __getattr__(name):
    if name == "LAB_BUILD_ONLY_PACKAGES":  # derived from the policy on every access, never a second list
        return lab_build_only_packages()
    raise AttributeError("module 'deploy' has no attribute " + repr(name))


def prohibited_installed(installed, identifiers=False, policy=None):
    """Present packages ({name: version}) that the receive-only policy forbids by presence or version.

    identifiers=True reports the matching rule (exact name or glob, plus VERSION_NOTE for a
    version rule) instead of the dpkg name, so doctor never echoes text that no rule names.
    """
    entries = [e for e in (policy or receive_only_policy())["forbidden_packages"] if e["check"] == "presence"]
    found = set()
    for raw, version in installed.items():
        name = raw.split(":", 1)[0].lower()
        for entry in entries:
            rule = entry.get("name") or entry["glob"]
            if not (name == rule.lower() if "name" in entry else fnmatch.fnmatchcase(name, rule.lower())):
                continue
            if "version_rule" not in entry:
                found.add(rule.lower() if identifiers else raw)
            elif version_forbidden(entry["version_rule"], version or ""):
                found.add(rule.lower() + VERSION_NOTE if identifiers else raw)
    return sorted(found)


def forbidden_basenames(policy=None):
    """Lower-case basenames doctor forbids: PROHIBITED_EXECUTABLES, BAD_NAMES (verify_build) and the
    policy forbidden_basenames, the same set selftest.py RX-01b uses."""
    extra = (policy or receive_only_policy())["forbidden_basenames"]
    return {n.lower() for n in PROHIBITED_EXECUTABLES | BAD_NAMES} | {e["name"].lower() for e in extra}


def prohibited_executables(root=Path("/"), names=None):
    names = forbidden_basenames() if names is None else names
    found = set()
    for directory in EXECUTABLE_DIRS:
        try:
            entries = [p.name for p in (Path(root) / directory).iterdir()]
        except OSError:
            continue
        found.update("/" + directory + "/" + n for n in entries if n.lower() in names)
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
    try:
        policy = receive_only_policy()
    except (OSError, ValueError) as exc:  # fail closed: no policy, no forbidden-package or basename verdict
        report["issues"].append("receive-only policy unavailable: " + str(exc))
        policy = None
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
        # Rule identifiers only (name, glob, or either + VERSION_NOTE): dpkg text is never echoed.
        found = set(prohibited_installed(present, identifiers=True, policy=policy) if policy else [])
        # Legacy floor (a test keeps it a subset of the policy): still reported if the policy is edited.
        found |= {p.lower() for p in present if p.lower() in PROHIBITED_PACKAGES}
        found |= {g for g in PROHIBITED_PACKAGE_GLOBS if any(fnmatch.fnmatchcase(p.lower(), g) for p in present)}
        found = sorted(found)
        if found:
            report["issues"].append("prohibited packages installed: " + ",".join(found))
    executables = prohibited_executables(names=forbidden_basenames(policy) if policy else
                                         {n.lower() for n in PROHIBITED_EXECUTABLES | BAD_NAMES})
    if executables:
        report["issues"].append("prohibited TX/private-content executables present: " + ",".join(executables))
    radio = radio_off_issues(config)
    report["radio_off"] = {"status": "BLOCKED" if radio else "RADIO_OFF_OBSERVED", "issues": radio,
                           "wifi_pwr_en_hog": "OPEN (bench gate W1-2)"}
    report["issues"].extend(radio)
    gnss = gnss_mode_issues()
    report["gnss_readers"] = {"status": "BLOCKED" if gnss else "ONE_READER_CONFIGURED_OR_NO_RECORD", "issues": gnss}
    report["issues"].extend(gnss)
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
            for name, device in guarded_devices(config).items():  # = the srrx.service device ordering
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
    files, modules = build_inventory(root)
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


def build_inventory(root):
    """(files, modules) of a prefix exactly as verify_build compares them; the build-manifest
    generator (deployment/system/build_manifest.py) emits the same walk, so the two never diverge."""
    root = Path(root).resolve(strict=True)
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
    return files, modules


def stage_gnss(rootfs, mode):
    """GNSS reader chain files of an explicit-config stage (software/GNSS-UART.md): the polkit
    rule for labd -> srrx-gnss-config, the locationd mode drop-in and the one reader's ordering
    after dev-lab-gnss.device (gpsd.service in gpsd mode, srrx-locationd in raw mode; DEP-11)."""
    units = rootfs / "etc/systemd/system"
    rule = rootfs / GNSS_POLKIT_RULE
    rule.parent.mkdir(parents=True, exist_ok=True)  # srrx.pass_jobs already wrote its rule there
    rule.write_text(gnss_polkit_rule(), newline="\n")
    locationd = units / "srrx-locationd.service.d"
    locationd.mkdir(exist_ok=True)
    (locationd / GNSS_MODE_DROPIN).write_text(gnss_mode_dropin(mode), newline="\n")
    if mode == "gpsd":
        gpsd = units / "gpsd.service.d"
        gpsd.mkdir()
        unit = device_unit(GNSS_DEVICE)  # gpsd -n opens the UART at start, not on the first client
        (gpsd / LAB_DEVICE_DROPIN).write_text("[Unit]\n# gpsd -n opens " + GNSS_DEVICE + " at start (DEP-11)\n"
                                              "Wants=" + unit + "\nAfter=" + unit + "\n", newline="\n")
    timeout = units / (device_unit(GNSS_DEVICE) + ".d")
    timeout.mkdir()
    (timeout / DEVICE_TIMEOUT_DROPIN).write_text(device_timeout_dropin(LAB_DEVICE_TIMEOUT_S), newline="\n")


def system_files():
    """deployment/system/system_files.py: sysusers, tmpfiles, udev, presets, polkit, masks, hooks."""
    path = str(HERE / "system")
    if path not in sys.path:
        sys.path.insert(0, path)
    import system_files as module
    return module


def stage_system(rootfs, config, gnss):
    """System files of the installed root (software/DEPLOYMENT.md, «Системні файли»). Writes only
    below rootfs; refuses to overwrite another staged file and any account nothing creates."""
    system = system_files()
    for relative, content in sorted(system.staged_files(config, gnss).items()):
        path = rootfs / relative
        if path.exists():
            raise DeploymentError("system file collides with a staged file: " + relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
        if relative in system.EXECUTABLES:
            path.chmod(0o755)
    unknown = system.unknown_accounts(rootfs)
    if unknown:
        raise DeploymentError("staged units/rules name accounts sysusers.d does not create: " + ", ".join(unknown))


def stage(destination, config=None, gnss="gpsd"):
    if gnss not in GNSS_MODES:
        raise DeploymentError("--gnss must be one of " + ", ".join(GNSS_MODES))
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
        if unit.name in RELEASE_GUARD_EXEMPT:
            continue
        dropin = units / (unit.name + ".d")
        dropin.mkdir()
        if unit.name == "srrx.service":  # only the receiver; the shutdown bridge never Requires= it (DEPLOYMENT.md)
            (dropin / "10-radio-off.conf").write_text(radio_off_dropin(), newline="\n")
        (dropin / "20-release-guard.conf").write_text("[Service]\nExecStartPre=/usr/bin/python3 -B /opt/srrx/deployment/deploy.py release-guard --devices /etc/srrx/devices.json --acceptance /etc/srrx/acceptance.json --release /etc/srrx/release.json --build-manifest /etc/srrx/build-manifest.json --cache /srv/srrx-cache\n", newline="\n")
    (units / RADIO_OFF_UNIT).write_text(radio_off_unit(), newline="\n")
    modprobe = rootfs / RADIO_OFF_MODPROBE
    modprobe.parent.mkdir(parents=True)
    modprobe.write_text(radio_off_modprobe(), newline="\n")
    sys.path.insert(0, str(PROJECT / "software"))
    from srrx import pass_jobs  # polkit rule and plan directory of srrx-passes@.service, from one source
    for relative, text in pass_jobs.staged_files().items():
        (rootfs / relative).parent.mkdir(parents=True, exist_ok=True)
        (rootfs / relative).write_text(text, newline="\n")
    for name in ("release.template.json", "build-manifest.template.json", "devices.template.json"):
        shutil.copyfile(HERE / name, etc / name)
    shutil.copyfile(PROJECT / "software/config/acceptance.template.json", etc / "acceptance.template.json")
    if config:
        (etc / "devices.json").write_text(json.dumps(config, indent=2) + "\n", newline="\n")
        (etc / "devices.env").write_text("SRRX_I2C0=" + config["i2c"]["ina228"]["path"] + "\nSRRX_I2C2=" + config["i2c"]["control"]["path"] + "\nSRRX_PICO=/dev/lab/pico\nSRRX_GNSS=" + gnss + "\n", newline="\n")
        rules = rootfs / "etc/udev/rules.d"
        rules.mkdir(parents=True)
        (rules / "70-srrx-serial-bound.rules").write_text(udev_rules(config), newline="\n")
        (rules / "71-srrx-gnss.rules").write_text(gnss_udev_rules(), newline="\n")
        (rootfs / RADIO_OFF_UDEV).write_text(radio_off_udev(config), newline="\n")
        # Only with the udev candidate that tags these nodes TAG+="systemd" (DEPLOYMENT.md, DEP-11).
        paths = list(guarded_device_paths(config).values())
        (units / "srrx.service.d" / LAB_DEVICE_DROPIN).write_text(lab_device_dropin(paths), newline="\n")
        for path in paths:
            timeout = units / (device_unit(path) + ".d")
            timeout.mkdir()
            (timeout / DEVICE_TIMEOUT_DROPIN).write_text(device_timeout_dropin(LAB_DEVICE_TIMEOUT_S), newline="\n")
        if gnss != "off":
            stage_gnss(rootfs, gnss)
    stage_system(rootfs, config, gnss)
    files = {p.relative_to(rootfs).as_posix(): sha(p) for p in sorted(rootfs.rglob("*")) if p.is_file()}
    (destination / "stage-files.json").write_text(json.dumps({"schema_version": 1, "status": "STAGED_ONLY", "files": files}, indent=2) + "\n", newline="\n")
    (destination / "INSTALL_PLAN.txt").write_text("STAGED ONLY. No services enabled and no hardware acceptance supplied.\nReview software/DEPLOYMENT.md, run doctor and all release guards, then package rootfs via signed local repository.\nField/QUIET root: Wi-Fi/BT modprobe blacklist (install /bin/false), FE1.1s port-4 authorized=0 rule and rfkill unit are staged; the WIFI_PWR_EN gpio-hog (W1-2) is OPEN and not generated.\nDo not copy over /etc acceptance files, repartition UFS, flash BIOS, run rsetup or auto-enable units.\nA/B installation is a separate bench/recovery procedure; no activation command is generated here.\n", newline="\n")
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
    executables = system_files().EXECUTABLES  # initramfs-tools runs only executable hooks
    with output.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(mode="w", fileobj=compressed, format=tarfile.PAX_FORMAT) as archive:
                for path in sorted(rootfs.rglob("*")):
                    info = archive.gettarinfo(str(path), arcname=path.relative_to(rootfs).as_posix())
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = ""
                    info.mode = 0o755 if path.is_dir() or info.name in executables else 0o644
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
    receive_only_policy()  # doctor would otherwise only report the broken policy on the target
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
    staging.add_argument("--gnss", choices=GNSS_MODES, default="gpsd",
                         help="UART6 reader chain written to devices.env and the GNSS drop-ins (with --devices)")
    rules = commands.add_parser("udev")
    rules.add_argument("--devices", type=Path, required=True)
    commands.add_parser("udev-gnss", help="print the fixed UART6 /dev/lab/gnss candidate rule")
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
        elif args.operation == "stage": result = stage(args.dest, load(args.devices) if args.devices else None, args.gnss)
        elif args.operation == "udev": print(udev_rules(load(args.devices)), end=""); return
        elif args.operation == "udev-gnss": print(gnss_udev_rules(), end=""); return
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
