# Lab ui: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_9603e249-d87`_

- **Subsystem:** lab_ui (Lab Shell Qt QML on labwc/cage, labbar, greetd, labd/labrx/labinput daemons, RP2040 HMI, glove/sun usability, function profiles, rule enforcement)
- **Findings:**
  1.
    - **Claim in stack:** Lab Shell is built on Qt 6.4.2 QML from noble apt: qt6-base, qt6-declarative, qt6-wayland, qml6-module-qtwebengine, qtcharts, qtpositioning and qt6-virtualkeyboard-plugin, all 6.4.2 (#51, 5.4 UI).
    - **Finding:** Versions confirmed on packages.ubuntu.com: qt6-base-dev 6.4.2+dfsg-21.1build5 (universe; arm64 present), qt6-wayland 6.4.2-5build3, qml6-module-qtwebengine 6.4.2-final+dfsg-12ubuntu9 (arm64 present), qml6-module-qtcharts 6.4.2-5build2, qt6-virtualkeyboard-plugin 6.4.2+dfsg-4build2. Noble has no noble-updates or backports for Qt6. Upstream Qt 6.4 support ended on 31 Mar 2023 (open source) and 28 Sep 2023 (commercial), and these packages sit in universe.
    - **Verdict:** confirmed
    - **Action:** Keep 6.4.2 as the v1 baseline and record it as an upstream-EOL dependency. See the next finding for the upgrade path.
    - **Impact:** The shell can be built from apt today. It inherits three years of unfixed QtQuick and QtWayland bugs.
    - **Sources:**
      - https://packages.ubuntu.com/noble/qt6-base-dev
      - https://packages.ubuntu.com/noble/qml6-module-qtwebengine
      - https://endoflife.date/qt
  2.
    - **Claim in stack:** Qt 6 Location is not in noble, so the map is our own QML tile layer over MBTiles. layer-shell-qt in noble is Qt5-only, so the bar cannot live inside the Qt6 shell (#51, lab_ui_hf tech_stack).
    - **Finding:** Both confirmed. qml6-module-qtlocation exists only in questing (6.9.2), resolute (6.10.2) and stonking (6.11.2), not in noble. layer-shell-qt in noble is 5.27.11 with liblayershellqtinterface5; Qt6 builds with qml6-module-org-kde-layershell start in questing (6.4.5) and resolute (6.6.4).
    - **Verdict:** confirmed
    - **Action:** No change for the noble build.
    - **Impact:** The custom MBTiles layer and the GTK labbar stay justified on noble.
    - **Sources:**
      - https://packages.ubuntu.com/search?keywords=qml6-module-qtlocation&searchon=names&suite=all&section=all
      - https://packages.ubuntu.com/search?keywords=layer-shell-qt&searchon=sourcenames&suite=all&section=all
  3.
    - **Claim in stack:** (implicit) The only Qt available for the shell is noble's 6.4.2.
    - **Finding:** Qt publishes prebuilt linux_gcc_arm64 desktop binaries for 6.8.0-6.8.3, 6.9.x, 6.10.x, 6.11.x and 6.12.0. They include qtlocation, qtcharts, qtvirtualkeyboard, qtpositioning, qtwaylandcompositor and qtserialport, and QtWebEngine for arm64 is in the extensions repository for 6.8.0-6.12.0. The Qt 6.12 supported-platforms page lists Ubuntu 24.04 x86_64 and arm64 and says the installer binaries are built on Ubuntu 24.04, so they match noble's glibc 2.39. Qt 6.12 LTS was released on 30 Sep 2026 (open-source support until 1 Apr 2027). The last open-source 6.8 LTS patch is 6.8.3. PySide6-Essentials 6.12.0 (8 Oct 2026) ships manylinux_2_39 aarch64 wheels.
    - **Verdict:** new_option
    - **Action:** In P5, evaluate Qt 6.8.3 or 6.12.0 arm64 (fetched with aqtinstall, repackaged as a +labN deb under /opt, held). The gain is native QtLocation (offline OSM tiles) in place of the hand-written MBTiles layer, plus newer QtQuick, QtWayland and WebEngine fixes. Licences: LGPLv3, with GPLv3 for Charts and VirtualKeyboard, which is fine for a personal device. Keep 6.4.2 as the fallback.
    - **Impact:** Removes an EOL toolkit and a custom map component. About 1-1.5 GB more on rootfs (estimate, not measured).
    - **Sources:**
      - https://download.qt.io/online/qtsdkrepository/linux_arm64/desktop/qt6_6120/qt6_6120/
      - https://download.qt.io/online/qtsdkrepository/linux_arm64/extensions/qtwebengine/
      - https://doc.qt.io/qt-6/supported-platforms.html
      - https://www.qt.io/blog/tag/releases
      - https://endoflife.date/qt
      - https://pypi.org/pypi/PySide6-Essentials/json
  4.
    - **Claim in stack:** labwc 0.7.1 (noble) with XWayland. Touch mouseEmulation exists only from 0.8.2. If the W1-2 gate fails, use a local labwc 0.8.4 build, which needs wlroots 0.18 via a meson wrap and libwayland 1.23 or newer as a fallback because noble has 1.22 (#51, lab_ui_hf).
    - **Finding:** Confirmed: noble labwc is 0.7.1-1build1 (universe, arm64). The NEWS file puts 'Add mouse emulation for touch devices' in 0.8.2 (13 Dec 2024). The text-input-v3 and input-method-v2 (IME) protocols arrived in 0.7.2. Upstream is now 0.20.2 (21 Aug 2026, wlroots 0.20.2) and 0.9.8 (11 Jun 2026, wlroots 0.19.3). The 0.8.4 fallback analysis holds: labwc 0.8.4 needs wlroots >=0.18.1,<0.19. wlroots 0.18.2 needs wayland-server >=1.23 (noble has 1.22.0), libdrm >=2.4.122 (noble-updates has 2.4.125) and wayland-protocols >=1.35 (noble-updates has 1.45). New: labwc 0.7.4 (19 Jun 2024) declares wlroots >=0.17.0,<0.18.0 and wayland-server >=1.19, so it builds directly against noble's libwlroots 0.17.1 with no subprojects. It brings the 0.7.2-0.7.4 fixes, including input-method support, but not touch mouse emulation.
    - **Verdict:** new_option
    - **Action:** Order of fallbacks: 0.7.1 (apt), then 0.7.4 (+lab deb, same wlroots), then 0.8.4 (wlroots 0.18 and libwayland-server 1.23 as static meson subprojects). Go to 0.8.4 only if XWayland GLFW apps need compositor touch mouse emulation.
    - **Impact:** A cheaper first fallback than 0.8.4, with no second libwayland on the system.
    - **Sources:**
      - https://packages.ubuntu.com/noble/labwc
      - https://raw.githubusercontent.com/labwc/labwc/master/NEWS.md
      - https://raw.githubusercontent.com/labwc/labwc/0.7.4/meson.build
      - https://raw.githubusercontent.com/labwc/labwc/0.8.4/meson.build
      - https://gitlab.freedesktop.org/wlroots/wlroots/-/raw/0.18.2/meson.build
      - https://packages.ubuntu.com/noble/libwayland-server0
      - https://packages.ubuntu.com/noble/wayland-protocols
  5.
    - **Claim in stack:** labwc 0.7.1 works on the Q6A HDMI output (RA620 bridge, HDMI-A-1) with Mesa Turnip/freedreno. Listed as a W1-2 gate.
    - **Finding:** Still not verified anywhere public. Radxa's download page lists only Radxa OS r2 noble GNOME images (plus Android 15 RC 20261008); there is no Ubuntu 26.04 image. Mesa 25.2.8-0ubuntu0.24.04.4 and libdrm 2.4.125 are confirmed in noble-updates. A mainline DTS for the Q6A (qcs6490-radxa-dragon-q6a.dts) is now in torvalds/master.
    - **Verdict:** unverified
    - **Action:** Keep the W1-2 gate: labwc, Lab Shell and labbar on HDMI-A-1 with the field EDID, touch mapped to the output, and 20 cold boots.
    - **Impact:** The whole UI depends on this gate.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/download
      - https://packages.ubuntu.com/noble-updates/mesa-vulkan-drivers
      - https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
  6.
    - **Claim in stack:** cage 0.1.5 is the safe mode: after 3 session crashes in 10 min, or HOME held at power-on, run lab-shell --safe (#51).
    - **Finding:** Confirmed: noble has cage 0.1.5+20240127-2build1 (a git snapshot on wlroots 0.17; universe, arm64). Upstream has moved on (0.2.0 for wlroots 0.18, 0.2.1 for 0.19, 0.3.0 for wlroots 0.20, latest 0.3.1), but the apt build is enough for a single-window recovery shell.
    - **Verdict:** confirmed
    - **Action:** No change. Keep safe mode free of SDR engines.
    - **Impact:** Low.
    - **Sources:**
      - https://packages.ubuntu.com/noble/cage
      - https://github.com/cage-kiosk/cage/releases
  7.
    - **Claim in stack:** greetd 0.9.0 has both initial_session and default_session pointing at a crash-counting lab-session wrapper running as user 'lab' (#51).
    - **Finding:** Confirmed: noble has 0.9.0-4ubuntu1. Upstream is 0.10.3 (greetd_ipc crate, 7 Jun 2024). Per greetd(5), initial_session is 'started exactly once when greetd is initially launched'. Every restart after a crash therefore runs default_session, a greeter-class logind session. Not verified: whether a greeter-class session gets the seat's uaccess device ACLs and the PipeWire/D-Bus user services the shell expects.
    - **Verdict:** new_risk
    - **Action:** W1-2 test: kill Lab Shell 3 times and check that the restarted session (default_session) has /dev/dri, input, audio and the user D-Bus. If not, make default_session an autologin helper that starts a proper user-class session.
    - **Impact:** Crash recovery could come back without GPU, input or audio access.
    - **Sources:**
      - https://packages.ubuntu.com/noble/greetd
      - https://man.archlinux.org/man/greetd.5.en
      - https://crates.io/api/v1/crates/greetd_ipc
  8.
    - **Claim in stack:** labbar is GTK3 + gtk-layer-shell 0.8.2 with a 13 mm 6-chip status row (#51, #52).
    - **Finding:** gtk-layer-shell 0.8.2-1build2 is in noble (resolute has 0.10.0). lab_ui_hf contradicts itself: the status_bar section says a 7 mm exclusive zone, while ui_system and STACK say 13 mm.
    - **Verdict:** confirmed
    - **Action:** Fix the exclusive zone at 13 mm (about 162 px at 1080p, 110 px at 1280x800) in the CI menu test and correct lab_ui_hf.
    - **Impact:** Low.
    - **Sources:**
      - https://packages.ubuntu.com/search?keywords=gtk-layer-shell&searchon=sourcenames&suite=all&section=all
  9.
    - **Claim in stack:** The labd, labpowerd and labinput daemons use Python 3.12 with python3-sdbus 0.11.1 or dbus-next 0.2.3, python3-libgpiod 1.6.3 (v1 API), python3-evdev 1.7.0, smbus2, pyudev 0.24, pyserial 3.5 and python3-systemd 235. wvkbd 0.14.3 is the OSK for third-party apps; squeekboard is not in noble.
    - **Finding:** All confirmed in noble: python3-sdbus 0.11.1-2build1, python3-dbus-next 0.2.3-3, python3-libgpiod 1.6.3-1.1build1, python3-evdev 1.7.0+dfsg-1build1, python3-smbus2 0.4.3-1, python3-pyudev 0.24.0-1, python3-serial 3.5-2, python3-systemd 235-1build4, wvkbd 0.14.3-1. squeekboard is not found in noble. xwayland is 2:23.2.6-1ubuntu0.7.
    - **Verdict:** confirmed
    - **Action:** Pin these versions in the lab repo.
    - **Impact:** None.
    - **Sources:**
      - https://packages.ubuntu.com/noble/python3-sdbus
      - https://packages.ubuntu.com/noble/python3-libgpiod
      - https://packages.ubuntu.com/noble/python3-evdev
      - https://packages.ubuntu.com/noble/wvkbd
      - https://packages.ubuntu.com/noble/xwayland
  10.
    - **Claim in stack:** labd is the single hardware owner and enforces leases with transient DevicePolicy=closed + DeviceAllow drop-ins on the leased USB node. Every exclusive lease and Expert-GUI runs with ReadOnlyPaths=/data. Hand-off is stop, release, re-enumeration check, start (C7, 5.4).
    - **Finding:** The systemd man page confirms DeviceAllow is eBPF filtering. 'closed' allows only the listed devices plus /dev/null, zero, full, random and urandom. Paths must resolve when the unit starts, and matching by major/minor is not recommended. The device filter acts when a node is opened, so it cannot revoke a file descriptor that is already open; the stop-first hand-off is therefore required, not optional. /dev/bus/usb/BBB/DDD changes on re-enumeration, so drop-ins must be regenerated for each lease (the design already does this). Not documented: whether DeviceAllow/DevicePolicy work in per-user managers (the page notes user-manager limits only for IPAccounting and NFTSet). ReadOnlyPaths in a user unit needs user namespaces, which Ubuntu 24.04 userland may restrict (the Radxa kernel's behaviour is unknown). The Expert GUIs run inside the labwc user session.
    - **Verdict:** new_risk
    - **Action:** Run Expert-GUI and engine leases as system units (User=lab, with the Wayland socket and XDG_RUNTIME_DIR passed in), or prove in W1-2 that 'systemd-run --user -p DevicePolicy=closed -p ReadOnlyPaths=/data' blocks both a non-leased RTL and writes to /data. The self-test must check enforcement (open() of a non-leased node fails), not just the unit properties.
    - **Impact:** Without this, an Expert GUI could open any SDR or write raw IQ around the labrx voice and band masks.
    - **Sources:**
      - https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html
  11.
    - **Claim in stack:** The HMI and supervisor MCU is a Raspberry Pi Pico (RP2040, 26 GPIO), 2 pcs (one spare), $10.12 (2 x GBP 3.80, The Pi Hut, unverified) (D12, 2.6).
    - **Finding:** Spec confirmed: 26 GPIO, 2 UART, 2 I2C, 3 analogue inputs, and the Pico 1 series 'will remain in production until at least January 2036'. Price corrected: DigiKey SC0915 costs $4.59 at qty 1 with 40,279 in stock (Active), so 2 pcs = $9.18. Adafruit 4864 lists $4.00 but is out of stock. The Pi Hut page returned HTTP 429 three times, so the GBP 3.80 figure stays unverified. The Pico W ($6) and Pico 2 W carry a Wi-Fi/BT radio.
    - **Verdict:** corrected
    - **Action:** Use DigiKey SC0915, 2 x $4.59 = $9.18. Specify the non-wireless Pico only; a Pico W would put a second Wi-Fi/BT transmitter inside a receive-only device and outside rfkill control.
    - **Impact:** -$0.94, a verified source, and a compliance note.
    - **Sources:**
      - https://www.raspberrypi.com/products/raspberry-pi-pico/
      - https://www.digikey.com/en/products/result?keywords=SC0915
      - https://www.adafruit.com/product/4864
  12.
    - **Claim in stack:** Encoders, keys and knobs: Bourns PEC11R-4215F-S0024 x3, C&K KSC641J IP67 x10, Adafruit 2055 x2 = $17.75, marked unverified (2.6).
    - **Finding:** All lines are now verified, and the total stands. PEC11R-4215F-S0024: $2.95, 13,117 in stock, Active, 24 PPR, 24 detents, push switch, 15 mm flatted shaft, rear-facing PC pins (datasheet REV D04/26). KSC641J LFS: $0.82 (1) / $0.70 (10), 30,086 in stock, Active, IP67, 340 gf, SMD 6.2 x 6.2 mm, 7.7 mm actuator, -40...85 C. Adafruit 2055 scrubber knob: 34.7 mm diameter, $0.95, in stock. Sum: 3 x 2.95 + 10 x 0.70 + 2 x 0.95 = $17.75.
    - **Verdict:** confirmed
    - **Action:** Change the row status to verified (18 Oct 2026).
    - **Impact:** None.
    - **Sources:**
      - https://www.digikey.com/en/products/result?keywords=PEC11R-4215F-S0024
      - https://www.digikey.com/en/products/detail/c-k/KSC641J-LFS/1003852
      - https://www.adafruit.com/product/2055
  13.
    - **Claim in stack:** Two PEC11R encoders (tune, volume) are glove- and rain-capable controls in an IPX4/IP54 enclosure. In rain, use LOCK and encoders only (#52, 5.8).
    - **Finding:** PEC11R datasheet: operating -30...+70 C, rotational life 30,000 cycles minimum, detent torque 30-90 gf-cm, no sealing class. A Farnell listing gives IP40 (seen in a search result only, page not fetched). A light detent and an unsealed shaft are weak points for gloved, wet field use, and a heavily used tuning encoder could reach 30k revolutions in months (model). Grayhill's 62S-series datasheet offers an optional shaft and panel seal and pushbutton (from a search result; model, IP class and price not verified).
    - **Verdict:** new_risk
    - **Action:** Put a shaft O-ring or silicone boot behind the panel on both encoders and keep a spare. In P5, price a sealed panel encoder (for example Grayhill 62S with panel seal) for the main tuning encoder only. Keep PEC11R for volume.
    - **Impact:** Water ingress at the most-used control. Cold limit -30 C.
    - **Sources:**
      - https://www.bourns.com/docs/Product-Datasheets/PEC11R.pdf
      - https://no.farnell.com/en-NO/bourns/pec11r-4215f-s0024/incremental-encoder-2ch-24pulse/dp/2474844
      - https://www.mouser.lt/datasheet/3/1072/1/62sg_datasheet.pdf
  14.
    - **Claim in stack:** Glove ergonomics: keys of 12 mm or more at 13 mm pitch in a 2x3 grid inside a 38-42 mm HMI column. Touch targets of 15 mm or more (primary 20 mm), 3 mm gaps, 29x20 mm tiles, digits of 6 mm or more (#52, 5.8).
    - **Finding:** The arithmetic is confirmed (model): on the 6.97 in FHD panel (80.4 um/px) 15 mm = 187 px, 20 mm = 249 px, 29 mm = 361 px; on a 1280x800 7 in panel 15 mm = 127 px. A 4x3 grid of 29x20 mm tiles with 3 mm gaps plus the 13 mm bar needs 125 x 79 mm, which fits the 154 x 87 mm active area. However, 12 mm caps at 13 mm pitch leave about 1 mm between edges. A DTIC 1992 study (abstract only; full PDF returned 403) found 13 mm spacing adequate for gloved operation speed across five glove types. Its spacing definition, and the MIL-STD-1472 figures, could not be read, so no standard number is verified here. Two key columns at 19 mm pitch fit the 38 mm column (2 x 19 = 38).
    - **Verdict:** new_risk
    - **Action:** Raise the 2x3 key pitch to 18-19 mm (6-7 mm edge gap, model), give the keys distinct shapes or tactile ridges, and keep the rule that every critical action works from keys and encoders. Grow the home tiles to about 36 x 22 mm, which the screen allows.
    - **Impact:** Fewer wrong presses with gloves. No cost change.
    - **Sources:**
      - https://apps.dtic.mil/sti/pdfs/ADA256894.pdf
  15.
    - **Claim in stack:** The VEML7700 (0x10, on the Pico's I2C0 with the PCA9555 at 0x20) drives the Day/Night/Red themes, mounted outside the visor (#52, 5.2).
    - **Finding:** Vishay datasheet Rev 1.8 (28 Nov 2024): range 0 to about 140 klx, resolution down to 0.0042 lx/ct, fixed 7-bit address 0x10, so there is no collision with a PCA9555 at 0x20. Adafruit 4162 breakout costs $4.95, in stock (Adafruit states about 120 klx).
    - **Verdict:** confirmed
    - **Action:** No change. Use the Adafruit 4162 board or the bare part. Set theme switching with hysteresis below about 100 klx so midday sun cannot saturate it.
    - **Impact:** None.
    - **Sources:**
      - https://www.vishay.com/docs/84286/veml7700.pdf
      - https://www.adafruit.com/product/4162
  16.
    - **Claim in stack:** A PCA9555 key expander with INT on the Pico's I2C (6 keys + 2 encoder pushes), $5-10 model (D12, 2.6).
    - **Finding:** TI PCA9555: Active, 2.3-5.5 V, open-drain active-low INT, 5 V-tolerant I/O. TI lists the TCA9555 as a newer drop-in replacement with improved power-on reset and interrupt behaviour, 1.65-5.5 V.
    - **Verdict:** new_option
    - **Action:** Specify the TCA9555 (pin-compatible), or keep the PCA9555. The price stays a model.
    - **Impact:** More robust power-on reset on the switched LAB5 rail.
    - **Sources:**
      - https://www.ti.com/product/PCA9555
  17.
    - **Claim in stack:** labinput uses UART7 on pins 32/29. The UART7 overlay exists upstream but its presence on the held image is unverified (C6, 5.2).
    - **Finding:** Confirmed upstream: radxa-overlays main has qcs6490-radxa-dragon-q6a-uart7.dtso, 'pin 32(tx), 29(rx)', copyright 2026. It is exclusive with spi7, i2c7, gpio30 and gpio31 and enables GSI DMA. The uart6 (16/18), i2c0 and i2c2 overlays also exist. Because the uart7 file is dated 2026, an older radxa-overlays package on the held image may lack it.
    - **Verdict:** confirmed
    - **Action:** In W1-2, check the installed radxa-overlays version. If uart7 is missing, compile this .dtso into lab-q6a.dtso.
    - **Impact:** Removes most of the risk of the USB fallback for the Pico.
    - **Sources:**
      - https://raw.githubusercontent.com/radxa-pkg/radxa-overlays/main/arch/arm64/boot/dts/qcom/overlays/qcs6490-radxa-dragon-q6a-uart7.dtso
      - https://github.com/radxa-pkg/radxa-overlays/tree/main/arch/arm64/boot/dts/qcom/overlays
  18.
    - **Claim in stack:** Field and QUIET modes: rfkill blocks wlan and bluetooth, plus USB authorized=0 for the FCU760K on FE1.1s port P4. Bluetooth is off permanently (service masked, driver blacklisted, rfkill state saved). Wi-Fi only at home (#8, C5).
    - **Finding:** The mainline Q6A DTS models the module as 'wifi@4', compatible usba69c,8d80 (AIC8800D80) on hub port 4, with no power-control or regulator property. The schematic's WIFI_PWR_EN is therefore not exposed as a standard Linux control. The Wi-Fi driver is out-of-tree (radxa-pkg/aic8800 DKMS). Community reports say firmware is loaded by the host (aic_load_fw before aic8800_fdrv) and that the Bluetooth path is Android-oriented. Once the driver is blacklisted, no rfkill entry exists, so a self-test that expects 'soft blocked' would report a false fail or a false pass.
    - **Verdict:** new_risk
    - **Action:** Make the structural block primary. Field roots do not load aic8800_fdrv, aic_load_fw or any aic BT module (blacklist plus install /bin/false), and a udev rule sets authorized=0 for a69c:8d80. Without host firmware the chip cannot transmit (an inference from the host-loaded firmware, to be confirmed on the board). rfkill stays as a second layer. Self-test pass condition: no wlan netdev and no hci device present, or both present and soft-blocked. Test the home unblock path in W1-2.
    - **Impact:** Turns the receive-only Wi-Fi/BT rule from a driver-dependent soft block into one that holds even if the out-of-tree driver mishandles rfkill.
    - **Sources:**
      - https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://github.com/radxa-pkg/aic8800
      - https://forum.armbian.com/topic/60133-wifi-gone-on-current-version/
  19.
    - **Claim in stack:** Artemis 4.2.0 is used for identification only. A match to a military or government entry is logged as 'out of scope' and not recorded, annotated, analysed or decoded (#8, C16, user rule line 33).
    - **Finding:** Artemis 4.2.0 is the current release (Flathub release timestamp 18 Jul 2026), and DB v74 is dated 18 Jul 2026, with a stated target of a release every 1-2 months. The DB crawler keeps only these sigidwiki 'Additional categories': Aviation, Marine, Navigation, Amateur Radio, Trunked Radio, Military, Commercial, Utility, Analogue, Digital, Satellite, Radar, Interfering, Numbers Stations, Time. There is no 'Government' label, and entries without a tag carry no category. Artemis is also not identification-only: it lets users 'collect RF signals' and 'store spectrum waterfalls, audio samples, and all types of documents'. Linux arm64 builds come only through Flathub (runtime org.kde.Platform 6.10, about 333 MB installed) or from source (Python >=3.12, pyside6==6.11.1, peewee >=4.2.6). STACK puts the stop in labd; the completeness check puts it in labclassify.
    - **Verdict:** corrected
    - **Action:** Implement the stop in one owner, labd, with Lab Shell and labclassify calling it, over the Artemis SQLite DB opened read-only. Stop when the category is in {Military, Radar, Numbers Stations}, OR the name or description matches a deny regex (military, navy, air force, NATO, STANAG, MIL-STD, Link-11/16, jammer, OTH, intelligence), OR the frequency falls in the masked bands. Treat Trunked Radio as unnamed occupancy. Fail closed for untagged entries in masked bands. Do not ship the Artemis GUI's user-database or collect feature on the device: either skip the GUI or run it with its data directory read-only. Mirror DB v74 offline with its SHA-256.
    - **Impact:** Without this, a military signal with no tag, or the missing 'Government' label, would pass the stop.
    - **Sources:**
      - https://github.com/AresValley/Artemis/releases
      - https://flathub.org/api/v2/appstream/com.aresvalley.artemis
      - https://raw.githubusercontent.com/AresValley/Artemis/master/pyproject.toml
      - https://raw.githubusercontent.com/AresValley/artemis-db/main/utils/constants.py
      - https://raw.githubusercontent.com/AresValley/artemis-db/main/2.get_data.py
      - https://raw.githubusercontent.com/AresValley/artemis-db/main/CHANGELOG.md
  20.
    - **Claim in stack:** Receive-only guard: SDRangel 7.27.2 RX-only, with a build audit that fails on any TX, DSD, Inmarsat, Heat Map, doa2, simpleptt, limerfe or FileSink/SigMF-sink plugin (#11, 5.4).
    - **Finding:** 7.27.2 (19 Aug 2026) is confirmed as the latest release. 7.27.0 added channeltx/modmeshcore (caught by the TX audit) and channelrx/demodmeshcore, whose readme says it 'demodulates and decodes incoming MeshCore wire packets' including TXT_MSG, with auto PSK for public channels and an AES keys dialog, plus an optional UDP JSON sink. Also present on master: channelrx/demodmeshtastic (and channeltx/modmeshtastic), channelrx/demodpager (POCSAG and FLEX messages and capcodes), channelrx/demodchirpchat (LoRa/ASCII text), and channelrx/remotesink, which sends baseband IQ over UDP and so bypasses the labrx voice and band masks. None of these RX plugins is on STACK's deny list. STACK forbids pager decoders only in general terms.
    - **Verdict:** new_risk
    - **Action:** Add demodpager, demodmeshcore, demodmeshtastic, demodchirpchat and remotesink (also remoteinput/remoteoutput) to the build-time exclusion and the runtime plugin audit. Re-run the audit on every SDRangel tag.
    - **Impact:** Closes a private-messaging decode path and a mask bypass in the main Expert engine.
    - **Sources:**
      - https://github.com/f4exb/sdrangel/releases/tag/v7.27.0
      - https://github.com/f4exb/sdrangel/releases/tag/v7.27.2
      - https://raw.githubusercontent.com/f4exb/sdrangel/master/plugins/channelrx/demodmeshcore/readme.md
      - https://raw.githubusercontent.com/f4exb/sdrangel/master/plugins/channelrx/demodpager/readme.md
      - https://raw.githubusercontent.com/f4exb/sdrangel/master/plugins/channelrx/remotesink/readme.md
  21.
    - **Claim in stack:** OpenWebRX+ 1.2.126 is installed with --no-install-recommends, with pager, selcall and digital-voice modes disabled in config and a -1 pin list (js8call, rtl-433, digiham, codecserver, acarsdec, dumphfdl, dumpvdl2) (#10, C22).
    - **Finding:** 1.2.126 is confirmed in the luarvique noble repo (Architecture all; amd64, arm64 and armhf sub-repos). Its Recommends field includes direwolf, wsjtx, js8call, libhamlib-utils, multimon-ng, python3-meshtastic, dump978-fa-minimal, dumphfdl, dumpvdl2, acarsdec, rtl-433, m17-demod, codec2, nrsc5 and python3-digiham. python3-meshtastic, a client library for TX-capable Meshtastic nodes, and m17-demod (digital voice) are not on the -1 list.
    - **Verdict:** confirmed
    - **Action:** Add python3-meshtastic, m17-demod and dump978-fa-minimal to the -1 pins, and add nrsc5 except in the US profile. Keep --no-install-recommends and the CI check that the mode list is empty.
    - **Impact:** Small. Closes a dependency-drift hole.
    - **Sources:**
      - https://luarvique.github.io/ppa/noble/Packages
  22.
    - **Claim in stack:** AIS 'type 35' tracks are neither shown nor logged; ADS-B tracks with dbFlags&1 are suppressed (C16, 5.4).
    - **Finding:** AIS: in the AIVDM reference, 35 is the ship type 'Military ops'. Message types run only from 1 to 27, so STACK's wording 'message type 35' is wrong. Ship type is carried in static messages (type 5 confirmed here; 19 and 24B per ITU-R M.1371, not re-read). Position reports carry no ship type, so a type-35 vessel would appear on the live map until its static message arrives. ADS-B: readsb documents 'military = dbFlags & 1', but --db-file defaults to 'none'. Without the tar1090-db aircraft.csv.gz the flag is never set, so suppression would fail open.
    - **Verdict:** corrected
    - **Action:** AIS: show or log a vessel only after a static message with ship type other than 35, and purge on a late 35. ADS-B: ship a pinned offline aircraft.csv.gz, and have labd refuse the ADS-B profile (fail closed) if the db file is missing or older than a set age.
    - **Impact:** Brings the military-emitter suppression in line with the rule instead of depending on the data.
    - **Sources:**
      - https://gpsd.gitlab.io/gpsd/AIVDM.html
      - https://raw.githubusercontent.com/wiedehopf/readsb/dev/README-json.md
      - https://raw.githubusercontent.com/wiedehopf/readsb/dev/README.md
  23.
    - **Claim in stack:** URH is rejected (archived); Pinecil IronOS Bluetooth = Off in QUIET (user rules lines 32-33).
    - **Finding:** Both confirmed. The jopohl/urh repository was archived by its owner on 29 Mar 2026. IronOS V2.23 (31 Aug 2025, the latest): 'Bluetooth BLE is off by default (security)'; the BLE settings toggle has existed since V2.21.
    - **Verdict:** confirmed
    - **Action:** Pinecil: flash V2.23 or later and check that BLE shows Off. URH stays on the forbidden list.
    - **Impact:** None.
    - **Sources:**
      - https://github.com/jopohl/urh
      - https://github.com/Ralim/IronOS/releases
  24.
    - **Claim in stack:** QtTinySA runs in a venv with PySide6 6.12 aarch64 wheels (manylinux_2_39, matching noble glibc 2.39) (C22, #34).
    - **Finding:** Confirmed: PySide6-Essentials 6.12.0 was released on 8 Oct 2026 with manylinux_2_39_aarch64 wheels, as were 6.10.x and 6.11.x. Artemis pins pyside6==6.11.1, so it needs its own venv.
    - **Verdict:** confirmed
    - **Action:** Keep one venv per tool. If Artemis is used at all, give it a separate venv.
    - **Impact:** None.
    - **Sources:**
      - https://pypi.org/pypi/PySide6-Essentials/json
      - https://raw.githubusercontent.com/AresValley/Artemis/master/pyproject.toml
  25.
    - **Claim in stack:** Every lab function has a one-tap function profile. A CI menu test checks every leaf with and without Lime and T7, and every critical leaf works from keys and encoders alone (5.4, #52).
    - **Finding:** This is a design and test claim; nothing exists to verify. The completeness check counted 105 leaves, about 25 stale or bound to Lime or T7. The new SDRangel plugins and the Artemis category facts above add leaves that the menu policy test must cover (Artemis stop, no pager or mesh modes).
    - **Verdict:** unverified
    - **Action:** Make the CI menu test data-driven from the same deny lists (SDRangel plugins, OpenWebRX+ modes, Artemis categories), so a new upstream plugin cannot appear as a menu leaf without failing CI.
    - **Impact:** Keeps the menu and the policy from drifting apart.
    - **Sources:** []
  26.
    - **Claim in stack:** (not in v1) The OS stays Radxa OS r2 noble.
    - **Finding:** Ubuntu 26.04 LTS (resolute) ships Qt 6.10.2 (with qml6-module-qtlocation), labwc 0.9.3, gtk-layer-shell 0.10.0 and layer-shell-qt 6.6.4 with a Qt6 QML module, which would let the status bar live inside the Qt shell. Radxa publishes no resolute image for the Q6A, and the held 6.18.2-4 kernel and NPU set are tied to r2. SDRangel 7.27.2 adds an Ubuntu 26.04 Qt6 .deb build.
    - **Verdict:** new_option
    - **Action:** Defer to a v2 review once Radxa publishes a 26.04 image. Do not change v1.
    - **Impact:** None for v1.
    - **Sources:**
      - https://packages.ubuntu.com/search?keywords=qt6-base-dev&searchon=names&suite=all&section=all
      - https://packages.ubuntu.com/search?keywords=labwc&searchon=names&suite=all&section=all
      - https://docs.radxa.com/en/dragon/q6a/download
- **Current status oct 2026:** As of 18 Oct 2026:
  - Noble packages are unchanged from what STACK assumes: Qt 6.4.2 (universe, upstream EOL since 2023), labwc 0.7.1, cage 0.1.5+20240127, greetd 0.9.0, gtk-layer-shell 0.8.2, Mesa 25.2.8 and libdrm 2.4.125 in noble-updates.
  - Radxa still offers only Radxa OS r2 noble (plus Android 15 RC 20261008) for the Q6A; BIOS 260120 is listed. The radxa-overlays repository now has uart7 (pins 32/29, 2026), uart6, i2c0 and i2c2 overlays for the Q6A, and a mainline Q6A DTS exists in torvalds/master.
  - Upstream releases: labwc 0.20.2 (21 Aug 2026, wlroots 0.20) and 0.9.8 (11 Jun 2026); cage 0.3.1; greetd 0.10.3; Qt 6.12 LTS (30 Sep 2026) with prebuilt linux_arm64 desktop binaries for 6.8-6.12 including QtLocation and QtWebEngine; PySide6 6.12.0 (8 Oct 2026); SDRangel 7.27.2 (19 Aug 2026; 7.27.0 added MeshCore RX/TX plugins); OpenWebRX+ 1.2.126; Artemis 4.2.0 (18 Jul 2026) with DB v74 (18 Jul 2026; Linux arm64 via Flathub only); IronOS V2.23 (BLE off by default).
  - URH was archived on 29 Mar 2026.
  - HMI parts are active and in stock: Pico SC0915 $4.59 at DigiKey (40,279 pcs; production until at least Jan 2036); PEC11R-4215F-S0024 $2.95 (13,117 pcs; datasheet REV D04/26); KSC641J LFS $0.82/$0.70 (30,086 pcs); Adafruit 2055 $0.95; VEML7700 datasheet Rev 1.8 and Adafruit 4162 $4.95. TI lists the PCA9555 as Active and recommends the TCA9555.
  - No EOL notices for any HMI part.
- **Notes:** Method: primary pages fetched directly (packages.ubuntu.com, labwc NEWS and meson.build at tags, wlroots meson.build, download.qt.io listings, doc.qt.io, endoflife.date, systemd man page, Radxa docs and overlay sources, mainline DTS, Vishay, Bourns and TI datasheets or product pages, DigiKey, Adafruit, Artemis and artemis-db raw sources, Flathub API, SDRangel plugin readmes, the luarvique Packages index, readsb docs, AIVDM). I used about 6 WebSearch calls before the shared search budget ran out; after that I only fetched pages and did no more searching.
  
  Unverified items:
  - MIL-STD-1472 glove pushbutton and touch figures: the DTIC PDF returned 403, so only the study abstract was seen.
  - The IP40 rating for PEC11R and the Grayhill 62S seal details: from search result snippets only.
  - The Pi Hut Pico price: HTTP 429 three times.
  - Behaviour of the AIC8800 out-of-tree driver: from community sources only.
  - Whether DeviceAllow and ReadOnlyPaths are enforced in a systemd --user manager on the Radxa kernel: not documented, must be tested on the board.
  
  Figures marked 'model' are my arithmetic: px per mm from panel diagonal and resolution, the tile grid fit, and the 19 mm key pitch.
  
  Consistency issues found in the background files:
  - lab_ui_hf gives the labbar zone as 7 mm in one place and 13 mm in another.
  - The Artemis stop is placed in labd in STACK and in labclassify in final_completeness.
  - STACK calls 'AIS type 35' a message type; it is ship type 35 (Military ops).
  
  Disclosure: one early crates.io API request (to check the greetd version) put the user's e-mail address in the HTTP User-Agent header by mistake. Nothing else was sent, and no later request included it.
  
  No files were written except downloaded reference copies in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/labui_dl/ (labwc_NEWS.md, veml7700.pdf, pec11r.pdf, q6a.dts, artemis-db sources).

## Адверсаріальна перевірка (`verify`)

_Run `wf_9603e249-d87`_

- **Subsystem:** lab_ui: Lab Shell (Qt QML) on labwc/cage, greetd session, labbar, labd/labrx/labinput daemons, RP2040 HMI, glove/sun usability, function profiles, rule enforcement (rfkill and Wi-Fi/BT block, Artemis stop, receive-only guard). Stage 3 adversarial verification, 18 Oct 2026.
- **Verdict:** Most facts from stages 1 and 2 hold against primary sources. I re-fetched the noble package pages, labwc sources at the 0.7.1, 0.7.4 and master tags, Qt Jira and Gerrit, the greetd 0.9.0 source and Ubuntu packaging, systemd v255, radxa-pkg/aic8800, the mainline DTS, SDRangel v7.27.2, the shipped OpenWebRX+ 1.2.126 .deb, readsb, tar1090, AIVDM, the Pico and RP2040 datasheets, and DigiKey, Adafruit, TI, Vishay and Bourns pages.
  
  Four stage findings are refuted or need major correction:
  1. Stage 2's QTBUG-114671 crash risk does not apply. labwc and wlroots always create the wl_seat global, and the Qt fix is only a null check on a missing seat.
  2. Stage 2's "greeter-class restart is low risk" is half wrong. The ACLs do work, but greetd exits as soon as a default_session that never creates a session exits. Its unit has StartLimitBurst=5 in 30 s, so a crash loop ends in a black screen.
  3. STACK's mechanism of OpenWebRX+ modes "disabled in the pinned config" does not exist in 1.2.126. A mode exists whenever its requirement is met. DSC, SITOR-B, NAVTEX, RTTY, FAX and SSTV are built in and always present. TETRA, P25, wM-Bus, Meshtastic/MeshCore/MeshCom and a speech-to-text transcriber appear as soon as their helpers or a URL are present.
  4. The SDRangel deny list is incomplete even after stage 1:
     - feature/sid is explicitly aimed at naval VLF transmitters.
     - demoddsc shows routine calls and MMSIs.
     - demodadsb and demodais bypass the military suppression.
     - samplemimo/audiocatsiso keys PTT on a transceiver.
     - remotetcpsink, udpsink and localsink bypass the masks.
     - rigctlserver, ambe, demodm17, demodfreedv and demodendoftrain are also missing.
     SDRangel exposes ENABLE_* CMake options for each plugin, so the guard must become a build allowlist.
  
  STACK's WEFAX backend is wrong: SDRangel 7.27.2 has no WEFAX plugin. OpenWebRX+'s built-in 'fax' mode is the only one on the device.
  
  New hardware and OS findings:
  - DevicePolicy=closed must also allow the GPU render node for Expert GUIs.
  - WIFI_PWR_EN is an SoC GPIO, so the Wi-Fi/BT module can be cut off in hardware.
  - LOCK can use labwc 0.7.1 sendEventsMode, which survives touch re-enumeration.
  - The Pico has no spare ADC channel for an offset reference.
  
  The UI as a whole still depends on the W1-2 board gate: HDMI through the RA620 bridge on the held 6.18.2-4 kernel.
- **Confirmed:**
  - Noble versions checked on packages.ubuntu.com on 18 Oct 2026, all universe: labwc 0.7.1-1build1, cage 0.1.5+20240127-2build1, greetd 0.9.0-4ubuntu1, libgtk-layer-shell0 0.8.2-1build2, qt6-base-dev 6.4.2+dfsg-21.1build5, qml6-module-qtwebengine 6.4.2-final+dfsg-12ubuntu9, qt6-wayland 6.4.2-5build3, qml6-module-qtcharts 6.4.2-5build2, qt6-virtualkeyboard-plugin and qml6-module-qtquick-virtualkeyboard 6.4.2+dfsg-4build2, qml6-module-qtpositioning 6.4.2-3build3, wvkbd 0.14.3-1, libwlroots-dev 0.17.1-2.1build1, python3-sdbus 0.11.1-2build1, python3-libgpiod 1.6.3-1.1build1. Not in noble: squeekboard and qml6-module-qtlocation. liblayershellqtinterface5 is 5.27.11 (Qt5 only).
  - Ubuntu 26.04 (resolute) has labwc 0.9.3-1, qt6-base 6.10.2, qml6-module-qtlocation 6.10.2-1, qml6-module-org-kde-layershell 6.6.4 and gtk-layer-shell 0.10.0. Radxa's download page still offers only Radxa OS r2 noble GNOME images, Android 15 RC 20261008 and BIOS flat_build 260120. Keep this as a v2 option only.
  - Qt support status (endoflife.date): Qt 6.4 open-source support ended 31 Mar 2023. Qt 6.8 LTS stopped at 6.8.3 for open source (26 Mar 2025). Qt 6.12 LTS was released 30 Sep 2026 with open-source support to 1 Apr 2027. download.qt.io has linux_arm64 desktop qt6_6120 with qtlocation, qtcharts, qtgraphs, qtpositioning, qtvirtualkeyboard, qtwaylandcompositor and qtserialport, and WebEngine 6120 under extensions. The Qt 6.12 supported-platforms page lists Ubuntu 24.04 arm64 and says the installer binaries are built on Ubuntu 24.04 (glibc 2.39). PySide6-Essentials 6.12.0 (8 Oct 2026) ships cp310-abi3-manylinux_2_39_aarch64. The latest aqtinstall is 3.3.0 (2 Jun 2025).
  - labwc NEWS: <touch deviceName mapToOutput> and libinput sendEventsMode arrived in 0.7.1. text-input-v3/input-method-v2, LABWC_FALLBACK_OUTPUT, touch on headerbars and the Chromium virtual-keyboard crash fix arrived in 0.7.2. 'Add mouse emulation for touch devices' arrived in 0.8.2 (13 Dec 2024). Current upstream releases are 0.20.2 (21 Aug 2026) and 0.9.8 (11 Jun 2026).
  - labwc 0.7.4 meson.build requires wlroots >=0.17.0,<0.18.0, wayland-server >=1.19.0 and libinput >=1.14, all of which noble satisfies. It builds against noble libwlroots 0.17.1 with no subprojects (dependency check only; not built).
  - labwc 0.7.1 desktop_update_top_layer_visiblity() disables the whole TOP layer on any output that has a fullscreen view. layers_arrange() subtracts exclusive zones from overlay down to background. output.c raises layer_tree[3] (OVERLAY) above the view trees, so an OVERLAY labbar stays visible over fullscreen windows.
  - labwc 0.7.1 and 0.7.4 src/input/touch.c store x_offset/y_offset as uint32_t; master has double. Issue #3764 ('Touch motion coordinates overflow due to unsigned offsets') was opened and closed on 15 Oct 2026, fixed by PR #3765, commit 6ab9d3fe464b31eed25fe2126d6b0dfb6cd0bff4. No release contains the fix yet.
  - greetd 0.9.0 source and Ubuntu packaging:
  - initial_session runs only when /run/greetd.run does not exist (is_first_run).
  - Every later session runs default_session through start_greeter() with XDG_SESSION_CLASS=greeter and the PAM service greetd-greeter. Ubuntu ships /etc/pam.d/greetd-greeter, which includes 'login'.
  - In systemd v255 logind, session_start() calls user_start() unconditionally, and seat_apply_acls() does not check the session class.
  - systemd issue #23198 'DevicePolicy=closed silently ignored' is open (RFE, pid1, analyze). The original report is about a kernel without CONFIG_CGROUP_BPF. A comment of 11 Aug 2026 says DevicePolicy is ignored in systemd --user units and that the documentation does not say so.
  - radxa-pkg/aic8800:
  - The DKMS file installs aic_load_fw_usb, aic8800_fdrv_usb and aic_btusb_usb (DEST_MODULE_NAME = name + '_usb').
  - The fdrv Makefile has CONFIG_RFTEST=y and CONFIG_COUNTRY_CODE "00".
  - The aicrf-test binary package installs /usr/bin/wifi_test and /usr/bin/bt_test.
  - The driver headers list product ID 0x8d81 and a second vendor ID 0x368B.
  - The mainline Q6A DTS has the FCU760K as 'wifi@4', compatible usba69c,8d80, on the FE1.1s hub (usb1a40,0101). There is no power-control property and no display nodes.
  - SDRangel 7.27.2 (CHANGELOG 19 Aug 2026):
  - These plugins exist: channelrx/demodpager, demodmeshcore (TXT_MSG decode, auto PSK for public channels, vendored tiny-AES-c), demodmeshtastic, demodchirpchat and remotesink; channeltx/modmeshcore and modmeshtastic; samplesource/remoteinput; samplesink/remoteoutput.
  - On Linux, pluginmanager.cpp loads plugins only from <bindir>/../lib/sdrangel/<subdir> and <bindir>/lib/<subdir>, with filter '*'.
  - OpenWebRX+ 1.2.126 (Architecture all, SHA-256 2f959307a4ac71ab93649a3951b6bd56b40220fa2d12d60c352d540716bdd61a in the luarvique noble repo) Recommends direwolf, wsjtx, js8call, m17-demod, codecserver, dump978-fa-minimal, dumphfdl, dumpvdl2, acarsdec, rtl-433, python3-meshtastic, python3-pycryptodome, python3-paho-mqtt, multimon-ng, nrsc5, libhamlib-utils, hpsdrconnector, csdr-skimmer, sonde-decoders, dxlaprs-lora and others.
  - readsb: --db-file defaults to "none", and military = dbFlags & 1. tar1090 planeObject.js also has a milRange() ICAO-block check. In the AIVDM reference, ship type 35 is 'Military ops', ship type is carried in static messages, and message types run 1-27.
  - Artemis 4.2.0 on Flathub (release timestamp 18 Jul 2026; aarch64 and x86_64; 332,548,608 bytes installed; runtime org.kde.Platform 6.10). The appstream text says it lets users 'collect RF signals' and 'store spectrum waterfalls, audio samples'. artemis-db CATEGORIES are exactly: Aviation, Marine, Navigation, Amateur Radio, Trunked Radio, Military, Commercial, Utility, Analogue, Digital, Satellite, Radar, Interfering, Numbers Stations, Time. There is no 'Government' category. DB v74 is dated 2026-07-18 and targets a release every 1-2 months.
  - URH: 'This repository was archived by the owner on Mar 29, 2026.' IronOS V2.23 (31 Aug 2025) is the latest release: 'Bluetooth BLE is off by default (security)'. The BLE toggle has existed since v2.21.
  - HMI parts:
  - Raspberry Pi Pico: 26 GPIO, 2 UART, 2 I2C, 3 analogue inputs, 'Pico 1 series will remain in production until at least January 2036', Wi-Fi/BT only on W/WH. DigiKey 2648-SC0915CT-ND costs $4.59 at qty 1, 40,279 in stock, Active.
  - PEC11R-4215F-S0024: $2.95 (qty 1), $2.375 (qty 10), 13,117 in stock, Active, 24 PPR, detent, switch. Datasheet REV.D04/26: operating -30 to +70 C, 30,000 rotations minimum, switch life 20,000 cycles, 60 RPM maximum, contact bounce 2 ms. Ordering code 4 = PC pin horizontal / rear facing, 2 = 24 detents, 15 = 15 mm, F = flatted, S = switch.
  - KSC641J LFS: $0.82 / $0.70 (qty 10), 30,086 in stock, IP67, 340 gf, SMD 6.2 x 6.2 mm, 7.7 mm actuator, -40 to 85 C.
  - Adafruit 2055: 34.7 mm x 10.5 mm, $0.95, in stock.
  - Group sum: 3 x 2.95 + 10 x 0.70 + 2 x 0.95 = $17.75. Pico: 2 x 4.59 = $9.18.
  - VEML7700 datasheet Rev. 1.8 (28 Nov 2024): 0 to about 140 klx, 0.0042 lx/ct, I2C address 0x10 (0x20 in 8-bit form). It does not collide with a PCA9555/TCA9555 at 7-bit 0x20. TI: PCA9555 is Active, 2.3-5.5 V, open-drain active-low INT, 5 V-tolerant I/O. The TCA9555 is the 'Drop-in replacement with upgraded functionality' ('power-on reset, interrupt, and lower voltage operation').
  - radxa-overlays qcs6490-radxa-dragon-q6a-uart7.dtso (copyright 2026) gives 'pin 32(tx), 29(rx)', is exclusive with spi7, uart7, i2c7, gpio30 and gpio31, sets qcom,enable-gsi-dma, and uses TX/RX pinctrl only. Radxa staff on the forum: header GPIOs are on gpiochip4 (pin 3 = line 24), and GPI DMA needs UEFI 'Radxa Platform Configuration -> GPIO -> QUPV3_xxx Mode' (stated for SPI).
  - Radxa forum:
  - Thread 31304: 7.0.11-4-qcom (via apt full-upgrade) blanks HDMI when msm_dpu binds; several users reproduced it; one reported 'HDMI works now after the latest kernel updates' on 9 Sep 2026.
  - Thread 31574 (community Ubuntu 26.04.1 v1.3.0, 7 Oct 2026, kernel 7.2.9).
  - Thread 30884: mainline Gentoo 7.0.9 with Vulkan, community calls the bridge 'RK620'.
  - Thread 30264: Radxa staff say 'The Q6A does not support Vulkan (GPU) as a backend' for llama.cpp but support OpenCL.
  - Pico datasheet RP-008307-DS-2:
  - ADC_AVDD comes from the SMPS 3.3 V through 201 ohm into 2.2 uF; offset 'about 150 uA x 200 = ~30 mV'.
  - GPIO23 high forces PWM and 'can greatly reduce the inherent ripple'.
  - Suggested offset fix: 'tying a second channel of the ADC to ground'.
  - An LM4040 3.0 V shunt on ADC_VREF limits the range to 0-3.0 V at about 1.5 mA.
  - VSYS input range is about 1.8-5.5 V.
  RP2040 datasheet: erratum RP2040-E11, DNL peaks at 512, 1536, 2560 and 3584, ENOB 8.7, affects B0/B1/B2, 'Not fixed'.
  - pico-examples quadrature_encoder.pio (2023) is a full-quadrature computed-jump state machine. It 'must be loaded at address 0' and reads up to sysclk/10. With 24 PPR and 24 detents that is 4 counts per detent.
  - Display arithmetic (model):
  - 6.97 in FHD: 154.3 x 86.8 mm, 12.44 px/mm; 13 mm = 162 px, 15 mm = 187 px, 20 mm = 249 px.
  - 7.0 in 1280x800: 150.8 x 94.2 mm, 8.49 px/mm; 13 mm = 110 px, 15 mm = 127 px.
  lab_ui_hf's later, revised section fixes labbar at 13 mm with a stated reason; the 7 mm figure is the superseded draft.
  - Mainline v6.18 msm DP reads EDID with drm_edid_read_ddc() -> drm_edid_read_custom() -> _drm_do_get_edid(), which applies drm_edid_override_get() first. drm.edid_firmware therefore works on the msm DP path, but only after HPD and a successful DPCD/sink-count read. simple-bridge.c has compatible 'radxa,ra620' with connector type HDMIA (the source of 'HDMI-A-1'). This is inferred for the Radxa 6.18.2-4 kernel and needs a board test.
- **Corrections:**
  1.
    - **Claim in stack:** (Stage 2 new_risk) Qt 6.4.2 QTBUG-114671 crash: Lab Shell crashes at start when no input device exists, so lab-shell must be ordered after labinput.
    - **Finding:** The Qt fix (qtwayland change 488069, 'client: check nullptr before usage' in QWaylandInputContext::textInput()) guards against a missing defaultInputDevice(), i.e. no wl_seat global at all. That happens on Weston with no input devices. labwc 0.7.1 calls wlr_seat_create("seat0") at startup, so the seat global always exists. Capabilities are computed per device, but that does not affect whether the global exists. With QT_IM_MODULE=qtvirtualkeyboard the Wayland input context path is not used. The Q6A DTS also has pon_pwrkey, a keyboard-class device that is always present.
    - **Verdict:** corrected
    - **Action:** Drop the crash rationale. Keeping lab-shell After=labinput-ready is still fine for usability (keys work from the first frame), but the shell must not depend on it. W1-2: boot with touch unplugged and the Pico in reset; the shell must come up.
    - **Impact:** Removes a false boot-crash risk. No patch to qt6-wayland is needed.
    - **Sources:**
      - https://qt-project.atlassian.net/browse/QTBUG-114671
      - https://codereview.qt-project.org/c/qt/qtwayland/+/488069
      - https://raw.githubusercontent.com/qt/qtwayland/v6.4.2/src/client/qwaylandinputcontext.cpp
      - https://raw.githubusercontent.com/labwc/labwc/0.7.1/src/seat.c
  2.
    - **Claim in stack:** #51: greetd 0.9.0 with initial_session and default_session both pointing at a crash-counting lab-session wrapper. Stage 2 rated the greeter-class restart as low risk.
    - **Finding:** greetd 0.9.0 context.rs check_children(): when the greeter (default_session) exits without having created a session, greetd returns Err('greeter exited without creating a session') and exits. Ubuntu's greetd.service has Restart=always, RestartSec=1, StartLimitBurst=5, StartLimitInterval=30. If the wrapper exits on every shell crash, the sequence is: the first crash starts default_session; each further crash restarts the whole greetd; more than 5 exits in 30 s leaves greetd failed with no UI. The cage safe mode runs the same Qt 6.4.2 lab-shell binary and can fail the same way. The ACL and user@ part of stage 2 still holds.
    - **Verdict:** corrected
    - **Action:** The lab-session wrapper must never exit on a child crash. It supervises labwc and Lab Shell itself, counts 3 crashes in 10 min, then execs cage with lab-shell --safe. If safe mode also crashes 3 times, it execs a last-resort text status (cage running a terminal with labctl status, or a plain VT) and keeps labd and labinput running so the keys still work. Add a greetd.service drop-in with StartLimitBurst=0 or OnFailure=lab-rescue.target. Keep the counter in /run.
    - **Impact:** Prevents a crash loop from ending in a black screen in the field.
    - **Sources:**
      - http://archive.ubuntu.com/ubuntu/pool/universe/g/greetd/greetd_0.9.0.orig.tar.gz
      - http://archive.ubuntu.com/ubuntu/pool/universe/g/greetd/greetd_0.9.0-4ubuntu1.debian.tar.xz
      - https://raw.githubusercontent.com/systemd/systemd/v255/src/login/logind-session.c
      - https://raw.githubusercontent.com/systemd/systemd/v255/src/login/logind-seat.c
  3.
    - **Claim in stack:** 5.4/#10: OpenWebRX+ 1.2.126 has pager (POCSAG/FLEX), selcall and digital-voice modes disabled in the pinned config, with a test that they are absent from the mode list.
    - **Finding:** The shipped 1.2.126 code (owrx/modes.py and feature.py from the .deb) has no per-mode disable setting. A mode is offered whenever its requirement is met:
  - 'page', 'selcall' and 'eas' need multimon.
  - 'tetra' needs tetrarx (luarvique package dxlaprs-tetra).
  - 'dmr', 'dstar', 'nxdn', 'ysf' and 'p25' need digiham + codecserver_ambe.
  - 'm17' needs m17_demod; 'freedv' needs freedv_rx; 'radel'/'radeu' need webrx_rade_decode.
  - 'ism' and 'wmbus' need rtl_433.
  - 'lora-wan', 'meshtastic', 'meshcore' and 'meshcom' need lorarx (dxlaprs-lora), and meshtastic also needs python3-meshtastic.
  - 'speech' (Speech Transcriber) is enabled by setting speech_url.
  'dsc', 'sitorb', 'navtex', 'rtty*', 'bpsk*', 'cwdecoder', 'fax' and 'sstv' have no requirement, so they are always present. DSC decodes every category including MMSIs, which conflicts with user rule line 42. Defaults also include allow_audio_recording=True and allow_chat=True. allow_center_freq_changes=False is the default.
    - **Verdict:** corrected
    - **Action:** Repackage as openwebrx 1.2.126+lab1 with a patched modes.py that keeps only: nfm, wfm, am, sam, lsb, usb, cw, usbd, drm, dab, bpsk31/63, rtty170/450/85, sitorb, navtex, ft8, ft4, jt9, wspr, sstv, fax, sonde-*, meteor-lrpt, elektro-lrit. Remove dsc, page, selcall, zvei, eas, tetra, p25, dmr, dstar, nxdn, ysf, m17, freedv, radel/radeu, ism, wmbus, lora-*, meshtastic, meshcore, meshcom, speech, hfdl, vdl2, acars, adsb, uat and ais. Pin settings: allow_center_freq_changes=false, allow_audio_recording=false, allow_chat=false, speech_url="" (CI asserts all four). Make each profile a frequency window that already satisfies the allowlists (amateur bands, NAVTEX 490/518 kHz, published MSI and civil WEFAX channels, broadcast). CI queries the running feature/mode list and fails on any mode outside the list.
    - **Impact:** Closes TETRA/P25, pager, mesh, wM-Bus, speech-to-text and routine-DSC paths that the config approach did not close.
    - **Sources:**
      - https://luarvique.github.io/ppa/noble/Packages
      - https://luarvique.github.io/ppa/noble/arm64/openwebrx_1.2.126_all.deb
      - https://raw.githubusercontent.com/luarvique/openwebrx/1.2.126/owrx/modes.py
      - https://raw.githubusercontent.com/luarvique/openwebrx/master/owrx/feature.py
  4.
    - **Claim in stack:** 5.4/C22: -1 pins js8call, rtl-433, digiham, codecserver, acarsdec, dumphfdl, dumpvdl2. Stage 1 added python3-meshtastic, m17-demod, dump978-fa-minimal and nrsc5.
    - **Finding:** The luarvique noble repo also ships dxlaprs-tetra (tetrarx), dxlaprs-lora (lorarx), codecserver-driver-ambe3k, codecserver-driver-all, hpsdrconnector, skyaware978, dump978-fa, dump1090-fa(-minimal), libacars-tools, multimon-ng (its own build, which would land in OpenWebRX+'s PATH), python3-bleak (BLE library) and python3-protobuf. libhamlib-utils is in Recommends, and STACK already forbids it.
    - **Verdict:** corrected
    - **Action:** Pin at -1 everywhere (aptly mirror, device and build host): dxlaprs-tetra, dxlaprs-lora, python3-meshtastic, python3-bleak, m17-demod, codecserver*, digiham*, python3-digiham, hpsdrconnector, dump978-fa*, skyaware978, nrsc5 (outside the US profile), multimon-ng (allowed only as the EAS wrapper in the US profile, which is off in Europe), libacars-tools, acarsdec, dumphfdl, dumpvdl2, rtl-433, js8call, libhamlib-utils. Keep the global APT::Install-Recommends "false" (#24).
    - **Impact:** Missing pins would quietly re-enable TETRA and mesh decoding through feature detection.
    - **Sources:**
      - https://luarvique.github.io/ppa/noble/Packages
      - https://raw.githubusercontent.com/luarvique/openwebrx/master/owrx/feature.py
  5.
    - **Claim in stack:** 5.4/#11: the SDRangel 7.27.2 audit fails on TX/DSD .so, Inmarsat C, Heat Map, doa2, interferometer, beamsteeringcwmod, simpleptt, limerfe, FileSink/SigMF sink. Stage 1 added demodpager, demodmeshcore, demodmeshtastic, demodchirpchat, remotesink, remoteinput and remoteoutput.
    - **Finding:** The full 7.27.2 plugin tree also contains plugins that break rules and are on no list:
  - feature/sid: its readme says the source 'should typically be a VLF signal ... used by navies to communicate with submarines (GQD/HWU/NAA)'. Conflicts with user rule line 36.
  - channelrx/demoddsc: shows Category Routine and 'From/To' MMSIs, and looks names up on aprs.fi. Conflicts with line 42.
  - channelrx/demodadsb and demodais: own databases, no dbFlags&1 or ship-type-35 suppression, links to vesselfinder.
  - samplemimo/audiocatsiso: 'sends its samples to an audio device on the Tx side ... CAT control ... frequency and PTT for transceivers', i.e. a TX path that is not under channeltx.
  - channelrx/remotetcpsink (IQ over TCP / rtl_tcp), udpsink and localsink: bypass the masks.
  - feature/rigctlserver (network control), feature/ambe (DV vocoder), demodm17 and demodfreedv (digital voice), demodendoftrain (railway telemetry), kiwisdr/remotetcpinput/aaroniartsainput (network sources).
  - All samplesink and samplemimo device plugins (bladerf, hackrf, pluto, usrp, xtrx, lime, metis).
  The pager readme mentions POCSAG only; FLEX is OpenWebRX+'s 'page' mode. Every plugin is gated by an ENABLE_<GROUP>_<NAME> CMake option (83 ENABLE_CHANNELRX references).
    - **Verdict:** corrected
    - **Action:** Replace the deny list with a build allowlist. Configure with every ENABLE_* option OFF, then enable only:
  - channelrx: chanalyzer, channelpower, demodam, demodbfm, demodwfm, demodnfm, demodssb, demodnavtex, demodrtty, demodft8, demodpacket (APRS only), radioclock, radioastronomy, freqtracker, demodvor, demodils, noisefigure (Bench only).
  - samplesource: rtlsdr, airspyhf, soapysdrinput (LimeSuiteNG patched module only), fileinput, sigmffileinput, testsource.
  - feature: satellitetracker, startracker, skymap, freqdisplay, antennatools, demodanalyzer, denoiser, morsedecoder.
  - None from channeltx, channelmimo, samplesink or samplemimo.
  The runtime audit hashes every file in <prefix>/lib/sdrangel/* and <prefix>/bin/lib/* against the signed manifest. Gate text decoders (RTTY, NAVTEX, packet) to sdrangelsrv only, with labd-set frequencies from the allowlists; leave them out of the Expert-GUI build. Re-run the audit on every tag.
    - **Impact:** Closes naval-VLF SID logging, routine-DSC/MMSI display, unsuppressed military ADS-B/AIS, a soundcard TX/PTT path and three IQ export paths.
    - **Sources:**
      - https://raw.githubusercontent.com/f4exb/sdrangel/v7.27.2/plugins/channelrx/CMakeLists.txt
      - https://raw.githubusercontent.com/f4exb/sdrangel/v7.27.2/plugins/feature/sid/readme.md
      - https://raw.githubusercontent.com/f4exb/sdrangel/v7.27.2/plugins/channelrx/demoddsc/readme.md
      - https://raw.githubusercontent.com/f4exb/sdrangel/v7.27.2/plugins/samplemimo/audiocatsiso/readme.md
      - https://raw.githubusercontent.com/f4exb/sdrangel/v7.27.2/plugins/channelrx/remotetcpsink/readme.md
      - https://raw.githubusercontent.com/f4exb/sdrangel/v7.27.2/plugins/channelrx/demodadsb/readme.md
      - https://raw.githubusercontent.com/f4exb/sdrangel/v7.27.2/plugins/channelrx/demodpager/readme.md
  6.
    - **Claim in stack:** 5.4/C7: mode 2 exclusive engine leases include 'sdrangelsrv (NAVTEX, RTTY, WEFAX, Radio Clock)'; the HF hub has a WEFAX leaf.
    - **Finding:** SDRangel 7.27.2 has no WEFAX/FAX plugin: none in channelrx/CMakeLists.txt or feature/, and demodfax, wefax and related paths return 404. OpenWebRX+ 1.2.126 has a built-in 'fax' mode with no requirement.
    - **Verdict:** corrected
    - **Action:** Bind the WEFAX function profile to OpenWebRX+ 'fax', using one profile per allowlisted civil meteorological WEFAX channel (Northwood and USCG-operated stations excluded), with allow_center_freq_changes=false. Remove WEFAX from the sdrangelsrv list. The menu CI test must resolve every leaf to an existing backend.
    - **Impact:** Without this the WEFAX leaf has no working backend.
    - **Sources:**
      - https://raw.githubusercontent.com/f4exb/sdrangel/v7.27.2/plugins/channelrx/CMakeLists.txt
      - https://raw.githubusercontent.com/luarvique/openwebrx/1.2.126/owrx/modes.py
  7.
    - **Claim in stack:** C7/5.4: each lease is confined with transient DevicePolicy=closed + DeviceAllow on the leased USB node. Stage 1/2: run Expert GUIs and engines as system units (User=lab).
    - **Finding:** System units are needed: DevicePolicy is ignored in --user managers (#23198, Aug 2026) and silently ignored without CONFIG_CGROUP_BPF. A gap neither stage noticed: 'closed' allows only the listed nodes plus /dev/null, zero, full, random and urandom. Expert GUIs (SDR++, SDRangel) and OpenWebRX+ rendering need /dev/dri/renderD128 (GLES/EGL on the Wayland socket). Without it they fall back to llvmpipe or fail to start.
    - **Verdict:** corrected
    - **Action:** Lease units: User=lab, DevicePolicy=closed, DeviceAllow=<leased /dev/bus/usb/BBB/DDD> rw, DeviceAllow=/dev/dri/renderD128 rw. Add audio only through the PipeWire socket, not /dev/snd. Pass WAYLAND_DISPLAY, XDG_RUNTIME_DIR=/run/user/<uid> and DBUS_SESSION_BUS_ADDRESS. Set ReadOnlyPaths=/data with ReadWritePaths=/data/products/<lease>, and ProtectSystem=strict. W1-2: confirm CONFIG_CGROUP_BPF=y in /boot/config-6.18.2-4-qcom. In the self-test, opening a non-leased /dev/bus/usb node must return EPERM, writing under /data must return EROFS, and an EGL_RENDERER query must not report llvmpipe.
    - **Impact:** Keeps enforcement working without breaking GPU rendering of the Expert GUIs.
    - **Sources:**
      - https://github.com/systemd/systemd/issues/23198
      - https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html
  8.
    - **Claim in stack:** (Stage 2) Pico ADC fixes: drive GPIO23 high, fit an LM4040, and 'tie a spare ADC input to GND for offset subtraction'.
    - **Finding:** The datasheet supports GPIO23 high, the LM4040 3.0 V shunt (about 1.5 mA, range 0-3.0 V) and the grounded-channel method. STACK's Pico map uses all three external ADC inputs (GP26 panel NTC, GP27 battery divider 1:6, GP28 case NTC); ADC3/GP29 is VSYS/3 on the board. There is no spare channel. Model: with the 30 mV reference drop, a 1:6 divider reads high by 0.118 V at 12.9 V. With an LM4040 the full scale is 18.0 V; 12.9, 13.2 and 16.8 V map to codes 2935, 3004 and 3823, clear of the E11 DNL peaks (2560 = 11.25 V, 3584 = 15.75 V). (v2.1: the cutoff is now 13.05 V, code about 2970; the same model reads about 0.12 V high there.)
    - **Verdict:** corrected
    - **Action:** Fit the LM4040 3.0 V on ADC_VREF (or remove R7 and feed a reference). As an alternative or in addition, labd cross-calibrates against the INA228 at boot and stores gain and offset in Pico flash. Do not use a grounded channel unless one NTC moves to an I2C sensor. Drive GPIO23 high, and add the RT6150 switching frequency to the harmonic scan (frequency not in the Pico datasheet; measure it).
    - **Impact:** An accurate undervoltage backstop with the existing pin map.
    - **Sources:**
      - https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf
      - https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
  9.
    - **Claim in stack:** #52/5.8: 2x3 sealed keys of 12 mm or more at 13 mm pitch in a 38-42 mm HMI column. Stage 1: raise the pitch to 18-19 mm because '2 x 19 = 38'.
    - **Finding:** At 13 mm pitch, 12 mm caps leave a 1 mm edge gap. Stage 1's conclusion holds, but its width arithmetic is wrong. Model: a 2-column block is pitch + cap wide (19 mm pitch gives 31 mm), and 3 rows are 2 x pitch + cap tall (19 mm gives 50 mm; 25 mm pitch gives 37 x 62 mm, still within the column width). KSC641J is a 6.2 mm SMD switch with a 7.7 mm actuator, so a '12 mm key' is a printed cap or plunger. IP67 applies to the switch only, so the panel needs a silicone keypad or boot. The MIL-STD-1472 figures are still unread (DTIC 403; the WebSearch budget was used up).
    - **Verdict:** corrected
    - **Action:** Key pitch 19-21 mm (7-9 mm edge gap). Use 22-25 mm only if the 135-140 mm face height still fits the 35 mm main knob, the volume encoder and 62 mm of keys. Use a silicone keypad or individual boots over the KSC641J, with distinct cap shapes (LOCK and REC with a ridge). Keep 'every critical action from keys and encoders' as an acceptance test.
    - **Impact:** Fewer gloved mispresses. Sealing is actually achieved. No BOM change apart from the keypad (about $5-15, model).
    - **Sources:**
      - https://www.digikey.com/en/products/detail/c-k/KSC641J-LFS/1003852
      - https://apps.dtic.mil/sti/pdfs/ADA256894.pdf
  10.
    - **Claim in stack:** #8/C5: Bluetooth off permanently (driver blacklisted); Wi-Fi/BT blocked by rfkill + USB authorized=0 on FE1.1s P4. Stage 2: blacklist the suffixed and plain module names, plus a udev rule for a69c:8d80 and 8d81.
    - **Finding:** The module names and the 8d81 ID are confirmed. The driver also lists vendor ID 0x368B, so a VID:PID rule is brittle; matching by port path is better. The schematic text shows WIFI_PWR_EN as an SoC GPIO, level-shifted by a CJ3134K to WIFI_PWR_EN_3V3, which feeds the FCU760K. The mainline DTS does not model it, so a field DTBO could hog it low and cut power to the module, a hardware-level block. The exact TLMM line number was not resolved from the text extraction.
    - **Verdict:** new_option
    - **Action:** Field/QUIET roots:
  - blacklist plus install /bin/false for aic_load_fw(_usb), aic8800_fdrv(_usb), aic_btusb(_usb) and btusb;
  - udev authorized=0 by the FE1.1s port-4 devpath (any VID);
  - aicrf-test forbidden.
  W1-2: find the WIFI_PWR_EN TLMM GPIO on schematic page 4 and test a field-DTBO gpio-hog output-low. If the module then does not enumerate on P4 and the home root still unblocks it, make the hog the primary field block. Self-test pass: no device on P4, no wlan netdev and no hci.
    - **Impact:** Turns receive-only Wi-Fi/BT from a software block into an unpowered radio.
    - **Sources:**
      - https://raw.githubusercontent.com/radxa-pkg/aic8800/main/debian/aic8800-usb-dkms.dkms
      - https://raw.githubusercontent.com/radxa-pkg/aic8800/main/src/USB/driver_fw/drivers/aic8800/aic8800_fdrv/aicwf_usb.h
      - https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
  11.
    - **Claim in stack:** #52: LOCK in rain disables touch. Stage 2: EVIOCGRAB re-grab after touch re-enumeration.
    - **Finding:** labwc 0.7.1 already supports <libinput><device category="touch"><sendEventsMode>no</sendEventsMode></device></libinput>, applied by reconfigure. The setting matches by category, so it survives USB re-enumeration with no grab race.
    - **Verdict:** new_option
    - **Action:** Implement LOCK as labd writing a labwc rc.xml fragment with touch sendEventsMode=no and running labwc --reconfigure. Keep EVIOCGRAB by labinput only as a fallback if reconfigure latency exceeds 300 ms (to be measured). The LOCK chip state comes from labd.
    - **Impact:** A simpler, more robust LOCK.
    - **Sources:**
      - https://raw.githubusercontent.com/labwc/labwc/master/NEWS.md
  12.
    - **Claim in stack:** (Stage 2) labwc 0.7.2 softened top-layer hiding; labbar should go on the OVERLAY layer.
    - **Finding:** The NEWS entry 'Show/hide top layer more smartly' is under 0.7.3 (12 Jun 2024), not 0.7.2. The OVERLAY fix stands (verified in 0.7.1 output.c and layers.c). labwc has no window rule that denies fullscreen. The practical route is a wlr-foreign-toplevel-management client calling unset_fullscreen (labwc implements the protocol; behaviour on 0.7.x not tested here).
    - **Verdict:** corrected
    - **Action:** labbar: gtk_layer_set_layer(OVERLAY), exclusive zone 13 mm (162 px on FHD, 110 px on 1280x800). Lab Shell runs maximized. Fullscreen Expert GUIs are tolerated: the OVERLAY bar covers their top 13 mm. Optional: labbar uses foreign-toplevel to unset fullscreen. CI: fullscreen every Expert GUI and assert labbar is visible.
    - **Impact:** REC, LOCK and QUIET chips stay visible.
    - **Sources:**
      - https://raw.githubusercontent.com/labwc/labwc/0.7.1/src/desktop.c
      - https://raw.githubusercontent.com/labwc/labwc/0.7.1/src/output.c
      - https://raw.githubusercontent.com/labwc/labwc/master/NEWS.md
  13.
    - **Claim in stack:** (Stage 2) QTBUG-138747 is a QVK + WebEngine regression reproduced on Ubuntu 24.04, so pick Qt 6.12, not 6.8.3.
    - **Finding:** The reporter's Ubuntu 24.04 was on WSL2, which uses Weston. A Qt developer reports that GNOME and the Qt Compositor do not reproduce it and calls it 'a problem specific to Weston'. Affected 6.5.9, 6.8.3, 6.9.1; fixed 6.5.10, 6.8.6, 6.9.3, 6.10.0, with further integrations into 6.8, 6.9 and 6.10 in Dec 2025. Whether it affects labwc is unknown. The choice of 6.12 over 6.8.3 still holds for a different reason: 6.8.3 open-source support ended 2 Apr 2025, while 6.12 is supported to 1 Apr 2027.
    - **Verdict:** corrected
    - **Action:** If Qt is upgraded in P5, use 6.12.0 (+labN under /opt, held). Base the choice on support status, and keep the WebEngine <select> then QVK regression test on labwc. If aqtinstall 3.3.0 cannot read the 6.12 layout, fetch the 7z archives from download.qt.io with SHA checks. 6.4.2 stays the v1 baseline.
    - **Impact:** Same decision, correct rationale.
    - **Sources:**
      - https://qt-project.atlassian.net/browse/QTBUG-138747
      - https://endoflife.date/api/qt.json
      - https://pypi.org/pypi/aqtinstall/json
  14.
    - **Claim in stack:** (Stage 2 new_risk) noble libsoapysdr0.8 Recommends soapysdr0.8-module-all, and '--no-install-recommends is specified only for OpenWebRX+'.
    - **Finding:** The Recommends field is confirmed: 'soapysdr0.8-module-all | soapysdr0.8-module', and module-all depends on -remote, -lms7, -hackrf, -bladerf, -uhd, -redpitaya and others. STACK #24 already says 'Install-Recommends false', so the 'only for OpenWebRX+' part is wrong. With the Lime now KEPT, the apt soapysdr0.8-module-lms7 (legacy LimeSuite, unpatched) would sit next to the patched LimeSuiteNG Soapy module.
    - **Verdict:** corrected
    - **Action:** Keep the global Install-Recommends false. Pin at -1: soapysdr0.8-module-all, -remote, -lms7, -hackrf, -bladerf, -uhd, -redpitaya. CI: SoapySDRUtil --info must list only rtlsdr, airspyhf and the patched LimeSuiteNG module (not just rtlsdr and airspyhf), and SOAPY_SDR_PLUGIN_PATH must be unset in all units.
    - **Impact:** Blocks an unpatched TX-capable Lime driver and SoapyRemote.
    - **Sources:**
      - https://packages.ubuntu.com/noble/libsoapysdr0.8
      - https://packages.ubuntu.com/noble/soapysdr0.8-module-all
  15.
    - **Claim in stack:** C16/5.4: ADS-B tracks with dbFlags&1 are suppressed; AIS 'type 35' is suppressed.
    - **Finding:** readsb sets dbFlags only when --db-file is given (default "none"), so suppression fails open without a database. tar1090 also flags military aircraft by ICAO block (milRange()). AIS ship type 35 arrives only in static messages (5, 19, 24B).
    - **Verdict:** corrected
    - **Action:** labd ADS-B filter: suppress if (dbFlags & 1) OR the ICAO address is in tar1090's military ranges (pinned copy). Refuse the profile if the pinned aircraft.csv.gz is missing or older than 90 days (fail closed). AIS: hold a vessel off map and log until a static message with ship type other than 35 arrives, and purge on a late 35. Both filters apply only to readsb and AIS-catcher. SDRangel demodadsb/demodais and OpenWebRX+ adsb/ais are not built.
    - **Impact:** Military suppression no longer depends on data that may be missing.
    - **Sources:**
      - https://raw.githubusercontent.com/wiedehopf/readsb/dev/README.md
      - https://raw.githubusercontent.com/wiedehopf/readsb/dev/README-json.md
      - https://raw.githubusercontent.com/wiedehopf/tar1090/master/html/planeObject.js
      - https://gpsd.gitlab.io/gpsd/AIVDM.html
  16.
    - **Claim in stack:** #8/C16: Artemis 4.2.0 is used for identification only; a military or government match is logged as 'out of scope'.
    - **Finding:** The category list has no 'Government'. The GUI has collect and store features and online space-weather fetches, and on aarch64 it ships only as a 333 MB Flatpak. The DB release format and checksum are not shown on the releases page.
    - **Verdict:** corrected
    - **Action:** Ship the DB only, not the GUI. Mirror artemis-db v74 with a locally computed SHA-256 and verify its format (SQLite expected via peewee; unverified). Do the matching in labd, with the Lab Shell 'Identify' sheet as a client. Stop rule: category in {Military, Radar, Numbers Stations}, OR the name or description matches the deny regex (military, navy, air force, NATO, STANAG, MIL-STD, Link-11/16, ALE 4G/WALE, jammer, OTH, intelligence), OR the frequency lies in a masked band. Untagged entries in masked bands fail closed. Trunked Radio counts as unnamed occupancy only.
    - **Impact:** Closes the missing-'Government' gap and removes a collect/store tool and 333 MB.
    - **Sources:**
      - https://raw.githubusercontent.com/AresValley/artemis-db/main/utils/constants.py
      - https://raw.githubusercontent.com/AresValley/artemis-db/main/CHANGELOG.md
      - https://flathub.org/api/v2/summary/com.aresvalley.artemis
  17.
    - **Claim in stack:** 5.4: labrx FFT tiles use VkFFT on Turnip, with FFTW as fallback.
    - **Finding:** There is no public VkFFT or Turnip compute result for the QCS6490. Radxa staff say Vulkan is unsupported for llama.cpp on the Q6A; a mainline Gentoo user reports Vulkan working. With the Lime kept, LIME-W at 56 MS/s and N=65536 needs 854 FFT/s, or 1709/s with 50 % overlap. Model: at an assumed 3-5 GFLOPS per A78 core with FFTW NEON, one core does 572-954 FFT/s, so 0.9-1.5 cores without overlap. Not measured.
    - **Verdict:** corrected
    - **Action:** FFTW is the default labrx backend. Enable VkFFT only after a W1-2/P0 bench pass: max |diff| against FFTW below 1e-4 relative, at least 1709 FFT/s at N=65536, and an 8 h soak with zero VK_ERROR_DEVICE_LOST. Qt Quick stays on the OpenGL ES RHI (QSG_RHI_BACKEND=opengl).
    - **Impact:** The spectrum pipeline does not rest on an unproven GPU path. CPU budget for LIME-W: 1-2 A78 cores (model).
    - **Sources:**
      - https://forum.radxa.com/t/vulkan-crashes-and-npu-setup-for-llm-inference-on-dragon-q6a-need-guidance/30264
      - https://forum.radxa.com/t/mainline-gentoo-7-0-9-all-working/30884
  18.
    - **Claim in stack:** 2.6: Raspberry Pi Pico 2 pcs, $10.12 (2 x GBP 3.80, The Pi Hut, unverified); encoders, keys and knobs $17.75 unverified; PCA9555 key expander.
    - **Finding:** DigiKey 2648-SC0915CT-ND costs $4.59, 40,279 in stock. The PEC11R, KSC641J and Adafruit 2055 lines are verified and the sum of $17.75 is exact. The PCA9555 is Active and TI recommends the drop-in TCA9555. Base Pico has no radio; Pico W/WH has Wi-Fi/BT 5.2.
    - **Verdict:** corrected
    - **Action:** Pico line: DigiKey SC0915, 2 x $4.59 = $9.18 (-$0.94), verified 18 Oct 2026. Mark the encoder/key/knob row as verified. Use the TCA9555 in place of the PCA9555. Specify the non-wireless Pico only (no W/WH, no Pico 2 W) in the BOM and the CI part check.
    - **Impact:** -$0.94; verified sources; no extra transmitter inside the device.
    - **Sources:**
      - https://www.digikey.com/en/products/result?keywords=SC0915
      - https://www.digikey.com/en/products/result?keywords=PEC11R-4215F-S0024
      - https://www.digikey.com/en/products/detail/c-k/KSC641J-LFS/1003852
      - https://www.adafruit.com/product/2055
      - https://www.ti.com/product/PCA9555
      - https://www.raspberrypi.com/products/raspberry-pi-pico/
  19.
    - **Claim in stack:** #51 and stage 1/2: labwc 0.7.1 from apt; 0.7.4+lab as default or first fallback; 0.8.4 only for XWayland touch mouse emulation.
    - **Finding:** 0.7.4 brings IME, LABWC_FALLBACK_OUTPUT, the smarter top layer (0.7.3) and touch-headerbar handling on the same wlroots 0.17.1. The uint32_t touch-offset bug exists in 0.7.1 and 0.7.4 and is fixed only on master. Inference, untested: Xwayland as an X server applies XI 2.2 pointer emulation to touch for X clients that do not select touch events, which may make compositor mouse emulation (0.8.2+) unnecessary for GLFW/X11 apps.
    - **Verdict:** confirmed
    - **Action:** Build labwc 0.7.4+lab1 against noble wlroots 0.17.1, carrying the 6ab9d3f backport (uint32_t to double). Set LABWC_FALLBACK_OUTPUT=NOOP-fallback in the session. Keep apt 0.7.1 as the rollback. Before considering 0.8.4, test SDR++ (XWayland GLFW) taps and drags with 0.7.4.
    - **Impact:** Fewer touch glitches, the shell survives HDMI loss, and no second libwayland.
    - **Sources:**
      - https://raw.githubusercontent.com/labwc/labwc/0.7.4/meson.build
      - https://raw.githubusercontent.com/labwc/labwc/master/NEWS.md
      - https://github.com/labwc/labwc/issues/3764
- **New risks:**
  - greetd crash-loop lockout: greetd 0.9.0 exits when a default_session that never creates a session exits, and greetd.service has StartLimitBurst=5 in 30 s. A wrapper that exits on each Lab Shell crash, followed by a crash-looping cage safe mode running the same Qt binary, ends in a black screen. Fix: the wrapper supervises internally and never exits; add a text-mode last resort and a StartLimit drop-in.
  - OpenWebRX+ 1.2.126 has no per-mode disable knob:
  - Built-in DSC (all categories, MMSIs), SITOR-B, RTTY, FAX and SSTV are always present.
  - TETRA (dxlaprs-tetra/tetrarx), P25/DMR/NXDN/YSF/D-Star, wM-Bus, ISM, LoRa/Meshtastic/MeshCore/MeshCom and a Whisper speech transcriber turn on through feature detection or one setting.
  - Defaults allow_audio_recording=True and allow_chat=True.
  TETRA matters most in the Europe region.
  - SDRangel 7.27.2 policy gaps beyond stage 1: feature/sid (naval VLF by design), demoddsc (routine calls and MMSIs), demodadsb and demodais (no military suppression), samplemimo/audiocatsiso (soundcard TX plus CAT PTT), remotetcpsink, udpsink and localsink (IQ export), rigctlserver, ambe, demodm17, demodfreedv, demodendoftrain, network sample sources, and every samplesink/samplemimo device plugin.
  - DevicePolicy=closed blocks /dev/dri/renderD128 unless allowed, which silently drops Expert GUIs and OpenWebRX+ rendering to llvmpipe or a startup failure.
  - Expert-GUI mode cannot enforce the frequency allowlists for text and FAX decoders (SITOR, RTTY, NAVTEX, WEFAX, DSC). Those decoders must exist only in headless sdrangelsrv, or in OpenWebRX+ profiles locked with allow_center_freq_changes=false.
  - PEC11R life: 30,000 rotations minimum, 60 RPM maximum, -30 C lower limit, no sealing class in the datasheet. A heavily used 35 mm tuning knob may need replacement within months (model). Mount the encoder on a small daughterboard with a connector and carry a spare.
  - KSC641J IP67 covers the switch only. The panel opening around a 12 mm cap needs a silicone keypad or boot to reach the enclosure's IPX4/IP54 target.
  - The edid_firmware override is applied only after the msm DP path detects HPD and reads DPCD and sink count (mainline v6.18 dp_panel.c). It cannot rescue a dead HPD/AUX path such as the 7.0.11 regression, so the kernel hold remains the only protection.
  - Radxa repo drift: forum reports show 7.0.11-4 broke HDMI and audio and a later kernel fixed HDMI (9 Sep 2026). Any change to a held kernel, embloader or SPI firmware package must stay refused by the offline updater.
- **Refuted findings:**
  1.
    - **Finding:** Stage 2: QTBUG-114671 (crash with no input device) threatens Lab Shell at boot on noble Qt 6.4.2 and could crash-loop it into safe mode.
    - **Why:** The bug is a null defaultInputDevice() when no wl_seat global exists (a Weston case). labwc 0.7.1 and cage create seat0 at startup, so the global always exists. Lab Shell's QVK in-process input context does not use QWaylandInputContext. pon_pwrkey also provides a keyboard device on this board. Sources: QTBUG-114671, Gerrit 488069, qtwayland v6.4.2 qwaylandinputcontext.cpp, labwc 0.7.1 seat.c.
  2.
    - **Finding:** Stage 2: greeter-class restarts are low risk, so the autologin-helper workaround is likely unnecessary.
    - **Why:** Only the ACL and user@ part holds. greetd 0.9.0 exits when the greeter (default_session) exits without creating a session, and Ubuntu's unit limits restarts to 5 in 30 s, so a wrapper that exits on a crash can lock out the UI (see new_risks).
  3.
    - **Finding:** STACK/#10 as carried by stage 1: OpenWebRX+ pager, selcall and digital-voice modes are disabled in the pinned config.
    - **Why:** The shipped 1.2.126 code has no mode-disable setting. Modes depend only on whether their requirements are present, and some decoders (DSC and others) have no requirement at all.
  4.
    - **Finding:** STACK 5.4: sdrangelsrv provides WEFAX.
    - **Why:** SDRangel v7.27.2 contains no WEFAX/FAX plugin (plugin list from plugins/channelrx/CMakeLists.txt; probed paths return 404).
  5.
    - **Finding:** Stage 2: --no-install-recommends is specified only for OpenWebRX+.
    - **Why:** STACK #24 already says 'Install-Recommends false'. The pins are still useful; the stated gap is not real.
  6.
    - **Finding:** Stage 2: labwc 0.7.2 softened top-layer hiding.
    - **Why:** In NEWS.md the entry 'Show/hide top layer more smartly' is in the 0.7.3 section (12 Jun 2024).
  7.
    - **Finding:** Stage 2: QTBUG-138747 was reproduced on Ubuntu 24.04, so it is a general Wayland risk.
    - **Why:** The reporter's Ubuntu 24.04 was WSL2 (WSLg, which is Weston). Qt developers found it 'specific to Weston' and not reproducible on GNOME or the Qt Compositor. It is unproven on labwc.
  8.
    - **Finding:** Stage 2: tie a spare Pico ADC input to GND for offset subtraction.
    - **Why:** STACK's map uses GP26, GP27 and GP28; ADC3/GP29 is VSYS/3 internally. There is no spare channel.
  9.
    - **Finding:** Stage 1: SDRangel demodpager decodes POCSAG and FLEX.
    - **Why:** The v7.27.2 readme mentions only POCSAG. FLEX belongs to OpenWebRX+'s 'page' mode, which needs multimon.
  10.
    - **Finding:** Stage 1: two key columns at 19 mm pitch fill the 38 mm column (2 x 19 = 38).
    - **Why:** A 2-column block is pitch + cap wide: 19 + 12 = 31 mm. The conclusion (it fits) stands; the arithmetic does not.
  11.
    - **Finding:** Stage 1: lab_ui_hf contradicts itself (7 mm versus 13 mm bar).
    - **Why:** The 7 mm figure is the first draft. The later critique-revised section sets 13 mm and gives a reason, so this is a stale passage, not a live contradiction. The fix is to delete the old line.
- **Corrected spec:** LAB_UI v1.1 (noble, held 6.18.2-4-qcom; build default WITH Lime per the user decision of 18 Oct; every leaf also declares a no-Lime/no-T7 backend)
  
  1. Compositor and session
  - labwc 0.7.4+lab1, built against noble libwlroots 0.17.1-2.1build1. Carries the 6ab9d3f touch-offset backport. Apt 0.7.1-1build1 is the rollback. XWayland 2:23.2.6 held.
  - Environment: LABWC_FALLBACK_OUTPUT=NOOP-fallback, WLR_DRM_DEVICES=/dev/dri/by-path/<display controller>, QSG_RHI_BACKEND=opengl, QT_IM_MODULE=qtvirtualkeyboard.
  - rc.xml:
    - output HDMI-A-1 mode pinned;
    - <touch deviceName=... mapToOutput="HDMI-A-1"/>;
    - libinput touch sendEventsMode toggled by LOCK;
    - window rules for app_id lab.shell (maximized, no SSD).
  - greetd 0.9.0-4ubuntu1: initial_session and default_session = lab-session (user lab). /etc/pam.d/greetd-greeter identical to greetd.
  - lab-session supervises labwc and the shell and never exits. 3 crashes in 10 min: exec cage 0.1.5 with lab-shell --safe (no SDR engines). 3 more crashes: text status console. Counter in /run.
  - greetd.service drop-in: StartLimitBurst=0 or OnFailure=lab-rescue.target.
  
  2. Shell and bar
  - Lab Shell: Qt 6.4.2 QML (qt6-base 6.4.2+dfsg-21.1build5, qt6-wayland 6.4.2-5build3, qml6-module-qtwebengine 6.4.2-final+dfsg-12ubuntu9, qtcharts 6.4.2-5build2, qtpositioning 6.4.2-3build3, qtvirtualkeyboard 6.4.2+dfsg-4build2).
    - Own MBTiles QML map layer.
    - One waterfall QQuickItem from labrx shm.
    - Maximized, never fullscreen.
  - P5 option: Qt 6.12.0 LTS arm64 under /opt as +labN (native QtLocation; open-source support to 1 Apr 2027). Gate: WebEngine <select> then QVK test on labwc.
  - labbar: GTK3 + gtk-layer-shell 0.8.2 on the OVERLAY layer, exclusive zone 13 mm (162 px FHD / 110 px 1280x800). Six chips of at least 18 mm with 3 mm gaps. CI: labbar visible with every Expert GUI fullscreen.
  - OSK: QVK in the shell; wvkbd 0.14.3 for third-party apps.
  
  3. Daemons
  - labd: Python 3.12, python3-sdbus 0.11.1, libgpiod v1 1.6.3; gpiochip4 lines looked up by label.
    - Single owner of I2C2, enables, leases, profiles and policy.
    - Leases run as system units: User=lab, DevicePolicy=closed, DeviceAllow=<leased /dev/bus/usb node> rw plus /dev/dri/renderD128 rw, WAYLAND_DISPLAY / XDG_RUNTIME_DIR / DBUS_SESSION_BUS_ADDRESS passed in, ProtectSystem=strict, ReadOnlyPaths=/data, ReadWritePaths=/data/products/<lease>.
    - Hand-off: stop, release, re-enumeration check, regenerate the drop-in, start.
    - Requires CONFIG_CGROUP_BPF=y.
  - labrx: C++. FFTW default (VkFFT only after the bench gate). Ring 4 GiB + 3 GiB burst with Lime (1.5 GiB without). CPU7 isolated with Lime. Masks are applied before any write.
  - labinput: UART7 on pins 32/29 (radxa-overlays uart7 with GSI DMA; UEFI QUPV3 mode for that serial engine set), framed protocol with CRC. Emits uinput keys and encoder detents (count/4, ±2-count hysteresis).
  
  4. RP2040 HMI
  - MCU: Raspberry Pi Pico SC0915 (non-wireless), 2 pcs, DigiKey $4.59 each = $9.18.
  - Firmware:
    - PIO quadrature_encoder.pio at origin 0, two state machines (GP2/3, GP6/7);
    - GPIO23 high (PWM);
    - ADC with an LM4040 3.0 V on ADC_VREF (full scale 18 V at 1:6; 13.05 V = code about 2970, 13.2 V = 3004), plus labd INA228 cross-calibration stored in flash;
    - undervoltage backstop at 13.05 V for 5 s without heartbeat (v2.1, the same 13050 mV as the labd graceful cutoff and above the 12.8 +/-0.1 V hardware UV trip; was 12.9 V).
  - I2C0 (GP4/5): TCA9555 at 0x20 (replaces PCA9555) and VEML7700 at 0x10, with theme hysteresis below 100 klx. Pin map otherwise as in STACK 5.2.
  - Encoders: Bourns PEC11R-4215F-S0024 x3 at $2.95 (one spare; $2.375 each at qty 10). O-ring or boot behind the panel. Main encoder on a connectorized daughterboard. P5: price a sealed panel encoder for tuning (unverified).
  - Knobs: Adafruit 2055 x2 at $0.95 (fit on the 6 mm flatted shaft to be checked).
  - Keys: C&K KSC641J LFS x10 at $0.70, under a silicone keypad or boots, 2x3 at 19-21 mm pitch (block 31-33 x 50-54 mm), distinct cap shapes.
  - Group total: $17.75 plus keypad.
  
  5. Usability
  - Touch targets of at least 15 mm (187 px), primary at least 20 mm (249 px), gaps at least 3 mm, home tiles about 36 x 22 mm, digits at least 6 mm, day contrast at least 7:1.
  - Menu depth Home > Hub > Mode. Risky actions need a 1.5 s hold. No drag-and-drop; use long-press and encoders.
  - LOCK = touch sendEventsMode=no plus labwc --reconfigure; EVIOCGRAB as fallback.
  
  6. Rule enforcement
  6a. Wi-Fi/BT
  - Field/QUIET roots blacklist and install /bin/false for aic_load_fw(_usb), aic8800_fdrv(_usb), aic_btusb(_usb) and btusb.
  - udev authorized=0 by the FE1.1s port-4 devpath.
  - Pending W1-2: WIFI_PWR_EN gpio-hog low in the field DTBO.
  - rfkill as a second layer.
  - aicrf-test and /usr/bin/wifi_test and bt_test forbidden.
  - Home Wi-Fi unblock by a 1.5 s hold with automatic re-block.
  
  6b. SDRangel 7.27.2
  - Allowlist build with all ENABLE_* OFF except:
    - channelrx: chanalyzer, channelpower, demodam, demodbfm, demodwfm, demodnfm, demodssb, demodnavtex, demodrtty, demodft8, demodpacket, radioclock, radioastronomy, freqtracker, demodvor, demodils, noisefigure (Bench);
    - samplesource: rtlsdr, airspyhf, soapysdrinput, fileinput, sigmffileinput, testsource;
    - feature: satellitetracker, startracker, skymap, freqdisplay, antennatools, demodanalyzer, denoiser, morsedecoder.
  - No channeltx, channelmimo, samplesink or samplemimo.
  - Text decoders only in sdrangelsrv at labd-set frequencies.
  - Runtime hash audit of <prefix>/lib/sdrangel/* and <prefix>/bin/lib/*.
  
  6c. OpenWebRX+
  - 1.2.126+lab1 with patched modes.py keeping only: nfm, wfm, am, sam, lsb, usb, cw, usbd, drm, dab, bpsk31/63, rtty170/450/85, sitorb, navtex, ft8, ft4, jt9, wspr, sstv, fax, sonde-*, meteor-lrpt, elektro-lrit.
  - Settings: allow_center_freq_changes=false, allow_audio_recording=false, allow_chat=false, speech_url="". Profiles are allowlisted frequency windows. WEFAX is served here.
  - -1 pins: dxlaprs-tetra, dxlaprs-lora, python3-meshtastic, python3-bleak, m17-demod, codecserver*, digiham*, hpsdrconnector, dump978-fa*, skyaware978, nrsc5 (non-US), multimon-ng (non-US), libacars-tools, acarsdec, dumphfdl, dumpvdl2, rtl-433, js8call, libhamlib-utils, plus soapysdr0.8-module-all, -remote, -lms7, -hackrf, -bladerf, -uhd, -redpitaya.
  - APT::Install-Recommends "false" globally.
  
  6d. ADS-B and AIS
  - ADS-B: readsb with a pinned aircraft.csv.gz (refuse the profile if missing or older than 90 days). Suppress on dbFlags&1 or a tar1090 military ICAO range.
  - AIS: AIS-catcher; show only after a static message with ship type other than 35; purge on a late 35.
  
  6e. Artemis
  - DB v74 only, SHA-256 pinned; matching runs in labd.
  - Stop on category in {Military, Radar, Numbers Stations}, the deny regex, or a masked band. Untagged entries in masked bands fail closed.
  - No Artemis GUI.
  
  6f. Other tools
  - Pinecil IronOS V2.23 or later with BLE Off. URH forbidden.
  
  6g. Menu CI
  - Data-driven from the same allowlists. Every leaf must resolve to an existing backend, with and without Lime and T7. Every critical leaf must work from keys and encoders.
- **Bench tests:**
  - W1-2 display gate on the held 6.18.2-4 kernel:
  - labwc 0.7.4+lab, Lab Shell and labbar on card1-HDMI-A-1;
  - /sys/class/drm/card1-HDMI-A-1/edid byte-identical to field.bin;
  - modetest/debugfs pixel clock 151.50 MHz;
  - 20 cold boots;
  - 20 HDMI unplug/replug cycles with the shell surviving (LABWC_FALLBACK_OUTPUT set).
  - greetd recovery: kill Lab Shell 3 times in 2 min. Expect the wrapper to stay alive, a switch to cage --safe on the third crash, and greetd never restarted (journalctl shows no greetd exit). Then make --safe crash 3 times: expect the text console, labd still running, keys still working. Check the loginctl class and the /dev/dri ACL in each state.
  - Lease enforcement inside an Expert-GUI system unit:
  - open() of a non-leased RTL /dev/bus/usb node returns EPERM;
  - a write under /data returns EROFS, while /data/products/<lease> is writable;
  - the EGL renderer is not llvmpipe.
  Also confirm CONFIG_CGROUP_BPF=y in /boot/config-6.18.2-4-qcom.
  - Wi-Fi/BT block:
  - home root with Wi-Fi up, warm reboot into the field root: no device on FE1.1s port 4 (lsusb -t), no wlan netdev, no hci0;
  - repeat from a cold boot;
  - find the WIFI_PWR_EN TLMM line, apply a gpio-hog low in the field DTBO, measure the module supply as 0 V, and confirm the home unblock still works;
  - dpkg -l aicrf-test is absent.
  - SDRangel audit: configure 7.27.2 with the allowlist and diff the installed plugin set against the manifest. Fail if any of sid, demoddsc, demodadsb, demodais, audiocatsiso, remotetcpsink, udpsink, localsink, rigctlserver, ambe, demodm17, demodfreedv, demodpager, demodmesh*, demodchirpchat, heatmap, any samplesink, samplemimo or channelmimo is present.
  - OpenWebRX+ audit: install 1.2.126+lab1 with the -1 pins and query the running feature and mode report. Expect no dsc, tetra, p25, dmr, page, selcall, eas, ism, wmbus, lora-*, mesh*, speech, adsb or ais. Settings must read allow_center_freq_changes=false, allow_audio_recording=false, allow_chat=false, speech_url=''. Selecting the WEFAX profile must decode a civil WEFAX recording in 'fax' mode.
  - Policy recordings: replay a mixed SigMF set (ADS-B with and without a DB, an AIS vessel with ship type 35 and with a late static message, DSC routine and distress, an Artemis Military entry and an untagged entry at 300 MHz). Expect only allowed objects to be shown or logged, and nothing stored inside the masked bands.
  - Glove/sun/rain acceptance: 3 glove types; at least 95 % first-hit accuracy on 15/20 mm targets and on keys at 19-21 mm pitch; LOCK under water spray (no touch events, LOCK still set after a touch USB re-enumeration); readable values at 100 klx with VEML7700 lux logged; theme hysteresis with no flapping.
  - Pico ADC: compare the Pico battery reading with the INA228 from 11.0 to 16.8 V in 0.1 V steps, before and after fitting the LM4040, with GPIO23 high. Require error at most 0.05 V at 13.05 V (v2.1 cutoff; was 12.9 V) and 13.2 V, -20 to +50 C. Scan HF and VHF for RT6150 PWM harmonics.
  - UART7 link: verify the UEFI QUPV3 mode for SE7, then a 1e6-frame CRC loop at the chosen baud with zero errors. Check that pinmux-pins shows a single owner for pins 29/32.
  - FFT backend: FFTW against VkFFT at N=65536, 1709 FFT/s (LIME-W, 50 % overlap). Measure A78 core load for FFTW and run an 8 h VkFFT soak with zero VK_ERROR_DEVICE_LOST before enabling VkFFT.
  - XWayland touch: on labwc 0.7.4, test SDR++ (GLFW/X11) taps, slider drags and waterfall pans with touch. If pointer emulation is missing or broken, try the 0.8.4 fallback.
- **Confidence:** medium

