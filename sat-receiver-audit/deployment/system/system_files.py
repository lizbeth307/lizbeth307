"""System files an installed SR-RX root needs, as pure generators (deploy.py stage writes them).

Nothing here creates users, reloads udev, enables or masks a unit on the running host,
or runs a command: every function returns file content. deploy.stage writes it below
its new rootfs directory; systemd-sysusers, systemd-tmpfiles, udev, systemctl preset,
polkitd and update-initramfs act on it only on the target, as reviewed install steps
(software/DEPLOYMENT.md, "Системні файли").

Sources: users and groups from the staged units and deploy.py; masks, logind,
gpsd, chrony and the GNSS blacklist from build/07 §1.2 and §18; zram and the ina238
blacklist from build/07 §21 / STACK.md:877; FastRPC udev and group from build/07 §6 /
STACK.md:863; the EDID hook from STACK.md:851; the DSP firmware hook from build/07 §6 /
STACK.md:864.
"""
import hashlib
import json
from pathlib import Path
import re
import uuid

import edid_field

HERE = Path(__file__).resolve().parent
DSP_LOCK = HERE / "npu/dsp-firmware.lock.json"

# kind, name, GECOS, home, source. "u" creates the user and its same-named group; "g" a
# group only. No "m" lines: srrx-pico and srrx-gnss must stay without members (deploy.py
# doctor refuses a member), and units get their extra groups only via SupplementaryGroups=.
SERVICE_ACCOUNTS = (
    ("u", "labd", "SR-RX labd hardware control", "/var/lib/srrx", "software/systemd/srrx.service User=labd"),
    ("u", "lab", "SR-RX engine lease", "/nonexistent", "STACK.md:873 lease User=lab; deploy.udev_rules GROUP=lab"),
    ("u", "labnpu", "SR-RX NPU inference", "/nonexistent", "STACK.md:875 inferd-htp User=labnpu"),
    ("u", "srrx-loc", "SR-RX location service", "/nonexistent", "software/systemd/srrx-locationd.service"),
    ("u", "srrx-passes", "SR-RX pass planner", "/nonexistent", "software/systemd/srrx-passes@.service"),
    ("u", "srrx-satdump", "SR-RX SatDump decode", "/nonexistent",
     "software/systemd/srrx-satdump-decode@.service User= (satdump_pass.UNIT_USER), products 2770 labd:srrx-satdump"),
    ("g", "srrx-bb", None, None, "satdump_pass.BASEBAND_GROUP: LRPT baseband class directory, sweep unit Group=, decode unit"),
    ("g", "srrx-pico", None, None, "deploy.PICO_GROUP: Pico UART, no members"),
    ("g", "srrx-gnss", None, None, "deploy.GNSS_GROUP: LC76G UART, no members"),
    ("g", "i2c", None, None, "srrx.service SupplementaryGroups=i2c; bound /dev/i2c-N"),
    ("g", "fastrpc", None, None, "STACK.md:863/875 FastRPC devices, inferd-htp SupplementaryGroups"),
)
# Created by packages of the base image, never by this file: root (base-passwd), dialout
# (base-passwd, gid 20), _chrony (chrony), gpsd (gpsd).
PACKAGE_ACCOUNTS = frozenset({"root", "dialout", "_chrony", "gpsd"})

SYSUSERS = "usr/lib/sysusers.d/srrx.conf"
TMPFILES = "usr/lib/tmpfiles.d/srrx.conf"
SYSTEM_PRESET = "usr/lib/systemd/system-preset/40-srrx.preset"
USER_PRESET = "usr/lib/systemd/user-preset/40-srrx.preset"
UDEV_FASTRPC = "etc/udev/rules.d/60-srrx-fastrpc.rules"
UDEV_PPS = "etc/udev/rules.d/72-srrx-pps.rules"
UDEV_I2C = "etc/udev/rules.d/73-srrx-i2c.rules"
# Same name as the rule of Ubuntu noble i2c-tools 4.3-4build2 (debian/i2c-tools.udev, installed by
# dh_installudev with its default priority 60): a file in /etc/udev/rules.d replaces it.
UDEV_I2C_TOOLS_OVERRIDE = "etc/udev/rules.d/60-i2c-tools.rules"
GNSS_BLACKLIST = "etc/modprobe.d/lab-gnss-blacklist.conf"
INA238_BLACKLIST = "etc/modprobe.d/lab-ina238-blacklist.conf"
GPSD_DEFAULTS = "etc/default/gpsd"
CHRONY_CANDIDATE = "etc/chrony/conf.d/60-srrx-gnss.conf.candidate"
LOGIND_DROPIN = "etc/systemd/logind.conf.d/60-srrx.conf"
# zram-tools 0.3.3.1-1.1 (installed in r2 with its zramswap.service enabled, image-facts.json) reads this
# conffile; systemd-zram-generator is not in r2 (build/15 «Збирання образу»).
ZRAMSWAP_DEFAULTS = "etc/default/zramswap"
POLKIT_RADIO_OFF = "etc/polkit-1/rules.d/60-srrx-radio-off.rules"
EDID_FIRMWARE = "usr/lib/firmware/edid/field.bin"
EDID_HOOK = "etc/initramfs-tools/hooks/srrx-edid"
DSP_HOOK = "etc/initramfs-tools/hooks/lab-dsp-fw"
NPU_PHASE0 = "/etc/srrx/npu-phase0.env"
# bundle() gives exactly these staged paths mode 0755: initramfs-tools runs only executable hooks.
EXECUTABLES = frozenset({EDID_HOOK, DSP_HOOK})

# build/07 §1.2 (STACK.md:845): unattended apt/fwupd, ModemManager and every sleep state; and the
# receive-only userspace layer over the AIC8800 blacklist (IMG-06, build/15 «Збирання образу»):
# bluetoothd and wpa_supplicant, which would start BT/Wi-Fi transmissions if an interface appeared.
# An empty unit file in /etc/systemd/system is masked like a /dev/null link (systemd.unit(5));
# bundle() refuses symlinks, so the masks are empty files.
MASKED_UNITS = ("apt-daily.timer", "apt-daily-upgrade.timer", "fwupd-refresh.timer", "ModemManager.service",
                "sleep.target", "suspend.target", "hibernate.target", "hybrid-sleep.target",
                "bluetooth.service", "wpa_supplicant.service")
# Raw mode: srrx-locationd is the one UART6 reader; gpsd may not be started at all.
RAW_MODE_MASKS = ("gpsd.service", "gpsd.socket")
GNSS_MODULES = ("gnss-usb", "gnss-ubx", "gnss-mtk", "gnss-sirf", "gnss-serial")
# The pps-gpio platform device of the /pps-gnss node in lab-q6a.dtso: of_device_add() names
# it "pps-gnss" (root child without reg) with id -1, and pps-gpio registers "<name>.<id>".
PPS_SOURCE_NAME = "pps-gnss.-1"
# NetworkManager 1.46 polkit actions that switch a transmitter on, scan actively or share a
# hotspot (data/org.freedesktop.NetworkManager.policy.in.in at tag 1.46.0).
NM_TX_ACTIONS = ("org.freedesktop.NetworkManager.enable-disable-wifi",
                 "org.freedesktop.NetworkManager.enable-disable-wwan",
                 "org.freedesktop.NetworkManager.enable-disable-wimax",
                 "org.freedesktop.NetworkManager.wifi.scan",
                 "org.freedesktop.NetworkManager.wifi.share.protected",
                 "org.freedesktop.NetworkManager.wifi.share.open")
# No host name over DHCP (build/15 «Ім'я хоста (W2 SYS-HOST)»). r2 runs NetworkManager 1.46.0-1ubuntu2.5
# (image-facts.json of CI run 42366505251), which reads dhcp-send-hostname from the profile only
# (src/core/devices/nm-device.c at tag 1.46.0; NetworkManager.conf(5) of 1.46.0 lists no global default
# for it). So: no in-memory "Wired connection" (no-auto-default=*), one wired profile with both
# dhcp-send-hostname=false, and 0600 root:root for it, which the keyfile plugin requires
# (nms-keyfile-utils.c at 1.46.0) and bundle() cannot give: a tmpfiles z line sets it in the builder's
# chroot run and at every boot (systemd-tmpfiles-setup.service, Before=sysinit.target, NM after it).
NM_NO_AUTO_DEFAULT = "etc/NetworkManager/conf.d/60-srrx-no-auto-default.conf"
NM_WIRED_PROFILE = "etc/NetworkManager/system-connections/srrx-wired.nmconnection"
NM_PROFILE_TMPFILES = "usr/lib/tmpfiles.d/srrx-network.conf"
# A fixed UUID: the same profile on every unit; Ubuntu's netplan migration (network-manager postinst) needs one.
NM_WIRED_UUID = str(uuid.uuid5(uuid.NAMESPACE_URL, "urn:sr-rx-v2.1:networkmanager:srrx-wired"))
GENERATED = "# SR-RX v2.1: generated by deployment/system/system_files.py (deploy.py stage); do not edit by hand.\n"
# software/systemd templates started only by labd (srrx.satdump_pass DECODE_TEMPLATE, RECORD_TEMPLATE).
TEMPLATE_UNITS = ("srrx-satdump-decode@.service", "srrx-baseband-record@.service")


class SystemFilesError(ValueError):
    pass


def accounts():
    users = {name for kind, name, *_ in SERVICE_ACCOUNTS if kind == "u"}
    groups = {name for kind, name, *_ in SERVICE_ACCOUNTS} | PACKAGE_ACCOUNTS
    return users | PACKAGE_ACCOUNTS, groups


def sysusers():
    lines = [GENERATED.rstrip("\n"), "# Service accounts only: no login shell, no members in srrx-pico/srrx-gnss."]
    for kind, name, gecos, home, source in SERVICE_ACCOUNTS:
        lines.append("# " + source)
        lines.append(f'u {name} - "{gecos}" {home} /usr/sbin/nologin' if kind == "u" else f"g {name} -")
    return "\n".join(lines) + "\n"


def tmpfiles():
    # /var/lib/srrx and its orbits/plans directories belong to srrx.pass_jobs (etc/tmpfiles.d/srrx-passes.conf);
    # repeating them here would make systemd-tmpfiles warn about duplicate lines.
    # Every lease unit's ReadWritePaths=/data/products/<engine>-<alias> must exist before systemd sets up its
    # namespace, and neither lab nor labd can create it below this root-owned parent: lease_products().
    # 0751: group lab lists it; every other account may only pass through to a subdirectory that grants
    # it access by its own mode (labd to products/satdump, 2770 labd:srrx-satdump, srrx.satdump_pass).
    # Group lab for labd would also open the receiver nodes to it (udev GROUP="lab"; build/15 Baseband/IQ).
    return (GENERATED + "# Lease outputs (STACK.md:873, build/07 §21): read-only /data, one writable /data/products/<lease>.\n"
            "# Each lease directory grants others nothing (0751 lets any account pass through, never list).\n"
            "d /data/products 0751 root lab -\n" + lease_products())


# srrx.engine_leases ENGINES x RECEIVERS (the template instance is the udev alias, deploy.validate_devices);
# test_engine_leases checks that both lists equal the module's.
LEASE_ENGINES = ("readsb", "aiscatcher", "sdrangelsrv")
LEASE_RECEIVERS = ("rtla", "rtlb", "hfplus")


def lease_products():
    """The writable directory of each engine lease unit (srrx-lease-<engine>@<alias>.service,
    ReadWritePaths=/data/products/<engine>-%i): 2750 lab:labd, so the engine (User=lab, UMask=0027)
    writes its products and labd reads them through the setgid group; nobody else enters."""
    lines = ["# Engine lease products: srrx-lease-<engine>@<alias>.service (software/systemd, srrx.engine_leases)."]
    lines += ["d /data/products/%s-%s 2750 lab labd -" % (engine, receiver)
              for engine in LEASE_ENGINES for receiver in LEASE_RECEIVERS]
    return "\n".join(lines) + "\n"


def udev_fastrpc():
    return (GENERATED + "# FastRPC 1.0.4-1 ships no rule or group (STACK.md:863, build/07 §6): CDSP/ADSP sessions and the\n"
            "# DMA heaps the HTP runtime maps, for the fastrpc group (inferd-htp SupplementaryGroups=fastrpc) only.\n"
            'KERNEL=="fastrpc-*", GROUP="fastrpc", MODE="0660"\n'
            'SUBSYSTEM=="dma_heap", GROUP="fastrpc", MODE="0660"\n')


def udev_pps():
    return (GENERATED + "# LC76G PPS on GPIO96 (lab-q6a.dtso node /pps-gnss): chrony refclock PPS /dev/pps-gnss (build/07 §18).\n"
            "# The class device has no parent (pps-gpio sets no info.dev), so it is matched by its source name.\n"
            f'SUBSYSTEM=="pps", ATTR{{name}}=="{PPS_SOURCE_NAME}", SYMLINK+="pps-gnss"\n')


def udev_i2c(config):
    """Group i2c on exactly the two observed buses of devices.json, never on every adapter (HDMI DDC,
    camera buses). The number is the observed one; doctor checks its OF node at every guard run."""
    lines = [GENERATED.rstrip("\n"), "# INA228 bus (I2C0) and control bus (I2C2) from devices.json; doctor binds number to OF node."]
    for label in ("ina228", "control"):
        path = config["i2c"][label]["path"]
        if type(path) is not str or not re.fullmatch(r"/dev/i2c-[0-9]+", path):
            raise SystemFilesError("unverified I2C path for " + label)
        lines.append(f'SUBSYSTEM=="i2c-dev", KERNEL=="{path[5:]}", GROUP="i2c", MODE="0660"')
    return "\n".join(lines) + "\n"


def udev_i2c_tools_override():
    """Replaces i2c-tools' own rule, which gives group i2c (and so labd) every /dev/i2c-N once the
    package is installed for bench i2cdetect (build/07 §5.3). Comments only: no rule applies."""
    return (GENERATED + "# Replaces /usr/lib/udev/rules.d/60-i2c-tools.rules of the i2c-tools package, which would put every\n"
            "# i2c-dev node (HDMI DDC, camera buses) in group i2c. Only 73-srrx-i2c.rules grants that group, on the two\n"
            "# buses bound in devices.json; doctor reports any other node open to the group.\n")


def gnss_blacklist():
    return (GENERATED + "# build/07 §18: no kernel GNSS driver may bind the LC76G UART next to gpsd or srrx-locationd.\n"
            + "".join("blacklist " + module + "\n" for module in GNSS_MODULES))


def ina238_blacklist():
    # STACK.md:877, build/07 §21: labpowerd owns the INA228 over i2c-dev; the ina238 hwmon driver
    # (INA228 support since Linux 6.17) must not bind it, so no ti,ina228 node and no autoload.
    return (GENERATED + "# labpowerd reads the INA228 on I2C0 over i2c-dev (STACK.md:877); the hwmon driver stays unbound.\n"
            "blacklist ina238\n")


def gpsd_defaults(mode):
    """build/07 §18 for gpsd mode; in raw and off mode gpsd names no device (deploy.gnss_mode_issues)."""
    if mode == "gpsd":
        return GENERATED + 'DEVICES="/dev/lab/gnss"\nGPSD_OPTIONS="-n -b -s 115200"\nUSBAUTO="false"\n'
    if mode in ("raw", "off"):
        return GENERATED + "# SRRX_GNSS=" + mode + ": gpsd does not read UART6.\n" + 'DEVICES=""\nGPSD_OPTIONS="-n -b"\nUSBAUTO="false"\n'
    raise SystemFilesError("unknown GNSS mode " + repr(mode))


def chrony_candidate():
    """Inert until the bench: chrony reads only *.conf in conf.d, and the NMEA offset is a
    measured median (STACK.md C13, about 0.05-0.15 s) that no generator may invent. Rename to
    60-srrx-gnss.conf after replacing TBD_MEASURED_MEDIAN_S with the W-04/W-05 median."""
    return (GENERATED + "# CANDIDATE (build/07 §18): inert under this name; the offset is TBD until measured.\n"
            "refclock SHM 0 refid NMEA offset TBD_MEASURED_MEDIAN_S delay 0.2 noselect\n"
            "refclock PPS /dev/pps-gnss lock NMEA refid PPS noselect\n"
            "maxchange 5 1 -1\nmakestep 1 3\nrtcsync\n")


def logind_dropin():
    # labpowerd owns KEY_POWER (STACK.md:877); no idle action may suspend a receiver (STACK.md:845).
    return GENERATED + "[Login]\nHandlePowerKey=ignore\nIdleAction=ignore\n"


def zramswap_defaults():
    """build/07 §21 / STACK.md:910: zram 1 GiB, no disk swap. Keys of zram-tools 0.3.3.1-1.1 (its
    conf/zramswap and the zramswap script on sources.debian.org, read 2026-11-07): SIZE in MiB, and
    PERCENT (of MemTotal) overrides SIZE. r2's own copy (image-facts.json root.zramswap_default, CI
    run 42318869479) sets ALGO=zstd and PERCENT=50: ALGO is kept, PERCENT is dropped for SIZE.
    PRIORITY keeps the script default (100; the only swap device, so it orders nothing)."""
    return (GENERATED + "# zram-tools conffile (/usr/sbin/zramswap sources it): one 1 GiB zram swap device, no disk swap.\n"
            "# Replaces r2's copy (ALGO=zstd, PERCENT=50): the algorithm stays, PERCENT would override SIZE.\n"
            "ALGO=zstd\nSIZE=1024\n")


def system_preset(mode):
    """Only the receive-only layer is enabled by `systemctl preset`; every other SR-RX unit is
    enabled deliberately after acceptance (software/DEPLOYMENT.md install order)."""
    lines = [GENERATED.rstrip("\n"), "enable srrx-radio-off.service"]
    # The baseband sweep timer too: it is enabled at commissioning, after the administrator has written
    # /etc/srrx/baseband.env (srrx.satdump_pass.sweep_units, ConditionPathExists= on that file).
    lines += ["disable " + unit for unit in ("srrx.service", "srrx-poweroff.service", "srrx-locationd.service",
                                              "srrx-timegate.service", "srrx-gnss-config.service", "inferd-htp.service",
                                              "srrx-baseband-sweep.timer")]
    # The LRPT record/decode templates have no [Install] and are never enabled: only labd starts their
    # instances (srrx.baseband_scheduler, polkit 60-srrx-satdump.rules). The lines keep a preset from doing so.
    lines += ["disable " + unit for unit in TEMPLATE_UNITS]
    if mode == "raw":
        lines += ["disable " + unit for unit in RAW_MODE_MASKS]
    return "\n".join(lines) + "\n"


def user_preset():
    return GENERATED + "# The touch console starts only after its venv has been built and audited.\ndisable srrx-menu.service\n"


def polkit_radio_off():
    condition = " ||\n        ".join('action.id == "' + action + '"' for action in NM_TX_ACTIONS)
    return ("// " + GENERATED[2:] +
            "// Field/QUIET root, receive-only: no session may switch Wi-Fi/WWAN on, scan actively or share a\n"
            "// hotspot through NetworkManager. polkit does not ask for root; the modprobe blacklist stays the layer.\n"
            "polkit.addRule(function(action, subject) {\n"
            "    if (" + condition + ") {\n"
            "        return polkit.Result.NO;\n"
            "    }\n"
            "});\n")


def network_manager_files():
    """Wired Ethernet without the host name in DHCP (option 12/81) on NetworkManager 1.46: the global
    drop-in, the one profile it leaves and the tmpfiles line that gives that profile 0600 root:root.
    No Wi-Fi profile: the receive-only root blacklists the radio and polkit refuses enabling it."""
    profile = (GENERATED +
               "# Any wired port (no interface-name); never sends the host name to a DHCP server (ipv4 and ipv6).\n"
               "[connection]\nid=srrx-wired\nuuid=" + NM_WIRED_UUID + "\ntype=ethernet\nautoconnect=true\n\n"
               "[ethernet]\n\n"
               "[ipv4]\nmethod=auto\ndhcp-send-hostname=false\n\n"
               "[ipv6]\nmethod=auto\ndhcp-send-hostname=false\n")
    no_auto = (GENERATED +
               "# NetworkManager.conf(5) [main] no-auto-default: no in-memory \"Wired connection\" for any device. That\n"
               "# profile would send the host name; srrx-wired.nmconnection is the only wired profile.\n"
               "[main]\nno-auto-default=*\n")
    tmpfiles = (GENERATED +
                "# The keyfile plugin ignores a profile readable by group or others; the controller bundle ships 0644.\n"
                "# z adjusts an existing file only (tmpfiles.d(5)): at boot before NetworkManager and in the builder chroot.\n"
                "z /" + NM_WIRED_PROFILE + " 0600 root root -\n")
    return {NM_NO_AUTO_DEFAULT: no_auto, NM_WIRED_PROFILE: profile, NM_PROFILE_TMPFILES: tmpfiles}


_HOOK_HEAD = """#!/bin/sh
{generated}{comment}PREREQ=""
prereqs()
{{
	echo "$PREREQ"
}}
case "$1" in
prereqs)
	prereqs
	exit 0
	;;
esac
. /usr/share/initramfs-tools/hook-functions
fail()
{{
	echo "{name}: $*" >&2
	exit 1
}}
# copy_file returns 1 when the file is already in the image; the digest check below decides.
copy_checked()
{{
	src="$1"
	want="$2"
	[ -f "$src" ] || fail "$src is missing"
	[ "$(sha256sum "$src" | cut -d' ' -f1)" = "$want" ] || fail "$src differs from the reviewed SHA-256"
	copy_file firmware "$src" "$src" || true
	for dest in "${{DESTDIR}}$src" "${{DESTDIR}}/usr$src" "${{DESTDIR}}${{src#/usr}}"; do
		if [ -f "$dest" ] && [ "$(sha256sum "$dest" | cut -d' ' -f1)" = "$want" ]; then
			return 0
		fi
	done
	fail "$src was not copied into the initramfs"
}}
"""


def edid_hook():
    digest = hashlib.sha256(edid_field.build()).hexdigest()
    head = _HOOK_HEAD.format(generated="# " + GENERATED[2:], name="srrx-edid",
                             comment="# drm.edid_firmware=HDMI-A-1:edid/field.bin (STACK.md:850-851) is loaded from the initramfs:\n"
                                     "# the field EDID must be there byte for byte, or the panel's own EDID could select 128.70 MHz.\n")
    return head + 'copy_checked /' + EDID_FIRMWARE + ' ' + digest + '\n'


def dsp_lock():
    lock = json.loads(DSP_LOCK.read_text(encoding="utf-8"))
    if lock.get("schema_version") != 1 or lock.get("kind") != "srrx_dsp_firmware_set":
        raise SystemFilesError("unexpected DSP firmware lock")
    for path, entry in lock["initramfs_files"].items():
        if not re.fullmatch(r"usr/lib/firmware/[A-Za-z0-9_./+-]+", path) or ".." in path.split("/") \
                or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise SystemFilesError("invalid DSP firmware lock entry " + path)
    return lock


def dsp_hook():
    """lab-dsp-fw (STACK.md:864): the one DSP load path for the selected 0.2.29 set; inert without
    a Phase 0 selection, and for 0.2.42 (that package ships its own hook)."""
    lock = dsp_lock()
    selection = lock["package"]["selection"]
    head = _HOOK_HEAD.format(generated="# " + GENERATED[2:], name="lab-dsp-fw",
                             comment="# One DSP load path (STACK.md:864, build/07 §6): copies the pinned " + selection + " set and\n"
                                     "# checks every SHA-256. Never mixes sets; files are never copied by hand (forum 31078).\n")
    body = [head,
            'selection=""',
            'if [ -f ' + NPU_PHASE0 + ' ]; then',
            "\tselection=$(sed -n 's/^SRRX_DSP_FIRMWARE=//p' " + NPU_PHASE0 + ")",
            'fi',
            'case "$selection" in',
            '"")',
            '\techo "lab-dsp-fw: no Phase 0 selection in ' + NPU_PHASE0 + '; nothing copied" >&2',
            '\texit 0',
            '\t;;',
            'radxa-firmware-qcs6490_0.2.42)',
            '\techo "lab-dsp-fw: 0.2.42 uses its own package hook; nothing copied" >&2',
            '\texit 0',
            '\t;;',
            selection + ')',
            '\t;;',
            '*)',
            '\tfail "unknown DSP firmware selection: $selection"',
            '\t;;',
            'esac']
    for path, entry in sorted(lock["initramfs_files"].items()):
        body.append("copy_checked /" + path + " " + entry["sha256"])
    return "\n".join(body) + "\n"


def staged_files(config=None, gnss="gpsd"):
    """{rootfs-relative path: str|bytes}; empty strings are masks. config is the validated devices.json."""
    files = {SYSUSERS: sysusers(), TMPFILES: tmpfiles(), SYSTEM_PRESET: system_preset(gnss), USER_PRESET: user_preset(),
             UDEV_FASTRPC: udev_fastrpc(), UDEV_PPS: udev_pps(), UDEV_I2C_TOOLS_OVERRIDE: udev_i2c_tools_override(),
             GNSS_BLACKLIST: gnss_blacklist(), INA238_BLACKLIST: ina238_blacklist(),
             GPSD_DEFAULTS: gpsd_defaults(gnss), LOGIND_DROPIN: logind_dropin(), ZRAMSWAP_DEFAULTS: zramswap_defaults(),
             POLKIT_RADIO_OFF: polkit_radio_off(), EDID_FIRMWARE: edid_field.build(),
             EDID_HOOK: edid_hook(), DSP_HOOK: dsp_hook()}
    files.update(network_manager_files())
    if gnss == "gpsd":
        files[CHRONY_CANDIDATE] = chrony_candidate()
    if config is not None:
        files[UDEV_I2C] = udev_i2c(config)
    for unit in masks(gnss):
        files["etc/systemd/system/" + unit] = ""
    return files


def masks(gnss="gpsd"):
    """The units staged_files() masks with an empty file in etc/systemd/system for this GNSS mode."""
    return MASKED_UNITS + (RAW_MODE_MASKS if gnss == "raw" else ())


_ACCOUNT_KEYS = {"User": "user", "Group": "group", "SupplementaryGroups": "group"}


def unit_accounts(text):
    """(kind, name) of every User=/Group=/SupplementaryGroups= assignment in a unit or drop-in."""
    found = set()
    for line in text.splitlines():
        key, sep, value = line.strip().partition("=")
        if sep and key in _ACCOUNT_KEYS:
            found.update((_ACCOUNT_KEYS[key], name) for name in value.split())
    return found


def rule_groups(text):
    return {("group", name) for name in re.findall(r'\bGROUP\s*:?=\s*"([^"]+)"', text)}


def tmpfiles_accounts(text):
    found = set()
    for line in text.splitlines():
        fields = line.split()
        if len(fields) >= 5 and not fields[0].startswith("#"):
            for kind, name in (("user", fields[3]), ("group", fields[4])):
                if name != "-":
                    found.add((kind, name))
    return found


def unknown_accounts(rootfs, transient_units=()):
    """Accounts that staged units, udev rules or tmpfiles name but nothing creates (empty = complete).

    transient_units: unit texts of systemd-run units that exist only at run time (the SatDump
    decode/live units, srrx.satdump_pass.transient_units); their User=/Group= are checked too."""
    rootfs = Path(rootfs)
    users, groups = accounts()
    needed = set()
    for text in transient_units:
        needed |= unit_accounts(text)
    for directory in ("etc/systemd/system", "usr/lib/systemd/system"):
        for path in sorted((rootfs / directory).rglob("*")):
            if path.is_file() and path.suffix in (".service", ".conf", ".socket", ".timer"):
                needed |= unit_accounts(path.read_text(encoding="utf-8"))
    for directory in ("etc/udev/rules.d", "usr/lib/udev/rules.d"):
        for path in sorted((rootfs / directory).glob("*.rules")):
            needed |= rule_groups(path.read_text(encoding="utf-8"))
    for directory in ("etc/tmpfiles.d", "usr/lib/tmpfiles.d"):
        for path in sorted((rootfs / directory).glob("*.conf")):
            needed |= tmpfiles_accounts(path.read_text(encoding="utf-8"))
    return sorted(kind + ":" + name for kind, name in needed
                  if name not in (users if kind == "user" else groups))
