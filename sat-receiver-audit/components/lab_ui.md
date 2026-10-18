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

