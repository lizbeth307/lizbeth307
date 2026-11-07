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
# group only. One "m" line only (SESSION_MEMBERS): the touch-session account srrx-ui joins labd for
# the 0660 control socket. srrx-pico and srrx-gnss must stay without members (deploy.py doctor
# refuses a member), and units get their extra groups only via SupplementaryGroups=.
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
    ("u", "srrx-ui", "SR-RX touch session", "/var/lib/srrx-ui",
     "greetd default_session user (session_files(), STACK.md:884); runs the user unit srrx-menu.service"),
)
# The one documented member line: HMI users join labd for the socket (deploy.py PICO_GROUP comment),
# srrx.daemon binds /run/srrx/control.sock 0660 labd:labd below RuntimeDirectoryMode=0750 (srrx.service).
SESSION_MEMBERS = (("srrx-ui", "labd", "software/srrx/daemon.py control socket 0660 in /run/srrx 0750 labd"),)
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
# Touch session (session_files(), STACK.md:160/:884): greetd 0.9.0-4ubuntu1 default_session -> lab-session
# -> labwc 0.7.1-1build1 (+ kanshi 1.5.1-1), cage 0.1.5 in safe mode. Sources in deployment/system/session.
SESSION_SOURCES = HERE / "session"
LAB_SESSION = "usr/lib/srrx/lab-session"
# bundle() gives exactly these staged paths mode 0755: initramfs-tools runs only executable hooks, and
# greetd execs lab-session through `/bin/sh -c "exec <command>"`.
EXECUTABLES = frozenset({EDID_HOOK, DSP_HOOK, LAB_SESSION})

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
    lines = [GENERATED.rstrip("\n"), "# System accounts only: no login shell, created disabled (no password); no members in srrx-pico/srrx-gnss."]
    for kind, name, gecos, home, source in SERVICE_ACCOUNTS:
        lines.append("# " + source)
        lines.append(f'u {name} - "{gecos}" {home} /usr/sbin/nologin' if kind == "u" else f"g {name} -")
    for user, group, source in SESSION_MEMBERS:
        lines.append("# " + source)
        lines.append(f"m {user} {group}")
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


# The image's /etc/chrony/chrony.conf (W2 IMG-2): build_image.py writes it over chrony's own ucf copy
# after the package closure. Not a staged file: chrony is a package of the image, not of the bundle.
CHRONY_CONF = "etc/chrony/chrony.conf"
# chrony.conf(5) directives that add a time source, open an NTP or command service to others, or read
# source lists; none may appear in chrony_conf(). refclock belongs to the bench-measured candidate only.
CHRONY_NETWORK_DIRECTIVES = ("pool", "server", "peer", "sourcedir", "refclock", "allow", "broadcast", "bindaddress",
                             "bindcmdaddress", "cmdallow", "ntsserverkey", "ntsservercert")


def chrony_conf():
    """build/07 §18 without its two refclock lines: they stay in the inert CHRONY_CANDIDATE until the NMEA
    offset is measured (W-04/W-05), because chrony 4.5 stops when the PPS device cannot be opened
    (refclock_pps.c LOG_FATAL) and the SHM offset is TBD. No pool, server, peer, sourcedir or allow line:
    the receiver is offline and sends no NTP packet on bench Ethernet. confdir, driftfile, logdir,
    maxupdateskew and leapsectz right/UTC (from tzdata-legacy, the reason chrony depends on it) are the
    package's own defaults (/usr/share/chrony/chrony.conf of chrony 4.5-1ubuntu4.2, read 2026-11-07);
    confdir reads only *.conf files (conf.c parse_confdir), so the .candidate name stays inert."""
    return (GENERATED + "# Offline receiver (build/07 §18): no pool, server, peer, sourcedir or allow line, so chronyd sends no NTP packet.\n"
            "# The GNSS refclocks are conf.d/60-srrx-gnss.conf.candidate, inert under that name until the NMEA offset is measured.\n"
            "confdir /etc/chrony/conf.d\n"
            "driftfile /var/lib/chrony/chrony.drift\n"
            "logdir /var/log/chrony\n"
            "maxupdateskew 100.0\n"
            "leapsectz right/UTC\n"
            "maxchange 5 1 -1\n"
            "makestep 1 3\n"
            "rtcsync\n")


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
    files.update(session_files())
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


# ---------------------------------------------------------------- touch session (D-12 host part)
# STACK.md:160 and :884; the image (IMG lineage) installs the packages and makes greetd the display
# manager. Upstream behaviour cited below was read on 2026-11-07 from the noble sources
# (archive.ubuntu.com pool, SHA-256 equal to the .dsc): greetd_0.9.0.orig.tar.gz +
# greetd_0.9.0-4ubuntu1.debian.tar.xz, labwc_0.7.1.orig.tar.gz, kanshi_1.5.1.orig.tar.gz +
# kanshi_1.5.1-1.debian.tar.xz, cage_0.1.5+20240127.orig.tar.gz; systemd v255 from its git tag.
SESSION_USER = "srrx-ui"
SESSION_HOME = "/var/lib/srrx-ui"
SESSION_STATE = "/run/srrx-session"
SESSION_VT = 1
FIELD_OUTPUT = "HDMI-A-1"
# greetd 0.9.0 reads /etc/greetd/greetd.conf first, then config.toml (greetd/src/config/mod.rs read_config);
# config.toml is the noble package's conffile (debian/greetd.install), which this file replaces.
GREETD_CONFIG = "etc/greetd/config.toml"
GREETD_DROPIN = "etc/systemd/system/greetd.service.d/60-srrx-session.conf"
SESSION_TMPFILES = "usr/lib/tmpfiles.d/srrx-session.conf"
LABWC_DIR = "usr/lib/srrx/labwc"
KANSHI_DIR = "usr/lib/srrx/kanshi"
# STACK.md:81/:884 profile names in the field EDID's DTD order (edid_field.TIMINGS): field60 is the default.
KANSHI_PROFILES = (("field60", edid_field.TIMINGS[0]), ("field52", edid_field.TIMINGS[1]))
# Written by the administrator at commissioning (one word, field60 or field52); read by the labwc autostart.
DISPLAY_PROFILE = "/etc/srrx/display-profile"


def session_tmpfiles():
    """sysusers.d sets only the home record of a "u" line (sysusers.d(5), v255): the home is made here.
    The lab-session state directory is in /run, so a greetd restart keeps it and a reboot clears it."""
    return (GENERATED + "# Touch session (system_files.session_files()): srrx-ui home and the lab-session crash counter.\n"
            f"d {SESSION_HOME} 0700 {SESSION_USER} {SESSION_USER} -\n"
            f"d {SESSION_STATE} 0700 {SESSION_USER} {SESSION_USER} -\n")


def greetd_config():
    """/etc/greetd/config.toml for greetd 0.9.0 (config/mod.rs parse_new_config; inish: '#' comment
    lines, [section], key = value). Only a default_session: every start, the first or after a restart,
    runs lab-session with the same class (greeter), PAM service (greetd-greeter, which includes login;
    server.rs main) and no authentication (context.rs start_greeter). greetd runs the command through
    /bin/sh -c "exec ..." whatever the account's shell is (session/worker.rs), so srrx-ui keeps
    /usr/sbin/nologin. source_profile = false: /etc/profile and ~/.profile are not sourced, so the
    session environment comes only from PAM, lab-session and the labwc environment file."""
    return (GENERATED + "# SR-RX touch session; replaces the greetd 0.9.0-4ubuntu1 conffile (agreety on VT 7).\n"
            "# greetd.service.d/60-srrx-session.conf keeps getty off this VT and lifts the start limit.\n"
            "[terminal]\n"
            f"vt = {SESSION_VT}\n"
            "\n"
            "[general]\n"
            "source_profile = false\n"
            "\n"
            "[default_session]\n"
            f'command = "/{LAB_SESSION}"\n'
            f'user = "{SESSION_USER}"\n')


def greetd_dropin():
    """greetd.service of greetd 0.9.0-4ubuntu1 has Restart=always, RestartSec=1, StartLimitBurst=5 and
    StartLimitInterval=30 in [Service], and After=/Conflicts=getty@tty7.service (Debian patch
    systemd_service_tweaks.patch). systemd v255 rate-limits only with interval > 0 and burst > 0
    (src/basic/ratelimit.h ratelimit_configured), and [Unit] and [Service] StartLimitBurst= set the same
    field (load-fragment-gperf.gperf.in): StartLimitBurst=0 lets greetd restart every second for as
    long as it fails, instead of ending in a black screen (STACK.md:160). VT 1 needs the getty
    conflict that the Debian patch moved to tty7 (greetd(5): "Conflicts=getty@ttyN.service")."""
    return (GENERATED + "[Unit]\n"
            "# No start limit: a failing greetd is restarted after RestartSec=1 for as long as it fails.\n"
            "StartLimitBurst=0\n"
            f"# greetd runs the session on VT {SESSION_VT} (/etc/greetd/config.toml): no getty may use it.\n"
            f"Conflicts=getty@tty{SESSION_VT}.service\n"
            f"After=getty@tty{SESSION_VT}.service\n")


def labwc_rc():
    """rc.xml of labwc 0.7.1 (docs/labwc-config.5.scd). Every touch device maps to HDMI-A-1: a <touch>
    without deviceName is the default entry (src/config/touch.c find_default_config). labwc loads its
    default key and mouse bindings (terminal, launcher, root menu with Exit) only when rc.xml defines
    none, and then drops every binding whose only action is None (src/config/rcxml.c post_processing,
    deduplicate_key_bindings/deduplicate_mouse_bindings): one None binding of each kind leaves the
    kiosk without any binding. The lab.shell rule (STACK.md:884) waits for the Lab Shell (no code yet)."""
    return ('<?xml version="1.0"?>\n'
            "<!-- " + GENERATED[2:].rstrip("\n") + " -->\n"
            "<labwc_config>\n"
            f'  <touch mapToOutput="{FIELD_OUTPUT}"/>\n'
            "  <keyboard>\n"
            '    <keybind key="W-Return"><action name="None"/></keybind>\n'
            "  </keyboard>\n"
            "  <mouse>\n"
            '    <context name="Root">\n'
            '      <mousebind button="Left" action="Press"><action name="None"/></mousebind>\n'
            "    </context>\n"
            "  </mouse>\n"
            "  <windowRules>\n"
            '    <windowRule identifier="lab.shell" serverDecoration="no">\n'
            '      <action name="Maximize"/>\n'
            "    </windowRule>\n"
            "  </windowRules>\n"
            "</labwc_config>\n")


def labwc_environment():
    """labwc reads <config dir>/environment before it starts (src/config/session.c
    session_environment_init; '#' lines are comments). LABWC_FALLBACK_OUTPUT is STACK.md:884's value,
    but the headless fallback output arrived in labwc 0.7.2 (NEWS.md at tag 0.7.4): 0.7.1 ignores it."""
    return (GENERATED + "# Inherited by the autostart and kanshi, not by user units (srrx-menu.service).\n"
            "# Effective from labwc 0.7.2 on (0.7.4+lab1); labwc 0.7.1 has no fallback output.\n"
            "LABWC_FALLBACK_OUTPUT=NOOP-fallback\n"
            "# WLR_DRM_DEVICES=/dev/dri/by-path/<display controller>: TBD, the by-path name on the Q6A is a\n"
            "# bench read (W1-2); until then it stays unset and wlroots picks the device itself.\n")


def kanshi_profile(name):
    """One kanshi 1.5.1 profile per file: kanshi applies the first matching profile only (main.c
    match/match_and_apply) and noble's 1.5.1-1 is built without IPC (no libvarlink in Build-Depends,
    meson option ipc=auto), so kanshictl cannot switch; the autostart picks the file. The refresh comes
    from the field EDID timing (matched within 50 mHz, main.c match_refresh); never @60Hz, @52Hz or
    --custom (STACK.md:81)."""
    timing = dict(KANSHI_PROFILES)[name]
    refresh = edid_field.check_timing(timing)["refresh_hz"]
    return (GENERATED + f"# STACK.md:884 profile {name}: field EDID {timing[0]}, {timing[1] / 1000:.2f} MHz.\n"
            f"profile {name} {{\n"
            f"\toutput {FIELD_OUTPUT} mode {timing[2]}x{timing[6]}@{refresh:.3f}Hz\n"
            "}\n")


def session_files():
    """{rootfs-relative path: text} of the touch session, staged for every GNSS mode. lab-session and the
    labwc autostart are shell scripts kept as files in deployment/system/session (tests run them)."""
    files = {SESSION_TMPFILES: session_tmpfiles(), GREETD_CONFIG: greetd_config(), GREETD_DROPIN: greetd_dropin(),
             LAB_SESSION: (SESSION_SOURCES / "lab-session").read_text(encoding="utf-8"),
             LABWC_DIR + "/rc.xml": labwc_rc(), LABWC_DIR + "/environment": labwc_environment(),
             LABWC_DIR + "/autostart": (SESSION_SOURCES / "labwc-autostart").read_text(encoding="utf-8")}
    for name, _ in KANSHI_PROFILES:
        files[KANSHI_DIR + "/" + name] = kanshi_profile(name)
    return files
