# Gnss imu location: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_d9388111-e66`_

- **Subsystem:** gnss_imu_location (GNSS LC76G with MS621FE backup cell, PPS on the held 6.18.2 kernel, BNO085 IMU pack and its single UART link, Q6A RTC with CR2032, location service with plausibility/spoofing gate and city-table-free fallbacks, WMM2025 declination, pointing aid)
- **Findings:**
  1.
    - **Claim in stack:** #79 / 2.8 BOM: Waveshare 24370 LC76G on UART6, $14.99, PPS available, 115200 default; GPS+GLONASS+Galileo+BDS+QZSS; TTFF target <=60 s
    - **Finding:** Quectel spec V1.1 confirms LC76G(AB): GPS L1 C/A, GLONASS L1, Galileo E1, BDS B1I/B1C, QZSS. 47 channels, 4+QZSS concurrent. 1PPS 30 ns RMS. UART 9600-921600 (default 115200, up to 10 Hz), I2C up to 400 kbps. 2.55-3.6 V, I/O = VCC, 36 mA tracking. Cold TTFF 28 s autonomous / 15 s EASY / hot 1 s. SBAS: WAAS, EGNOS, MSAS, GAGAN only. Dynamic limits 10,000 m and 490 m/s. Waveshare page: $14.99 (tier prices $14.19-13.63). Header: VCC, GND, TX, RX, PPS, RST, SDA, SCL. Onboard rechargeable MS621FE. Ships with an active ceramic antenna and an MX1.25 8-pin cable. The page shows no stock text. Little Bird AU listed it in stock (cached); RobotShop lists it on demand. Waveshare states that Quectel forbids shipping to Iran and Russia.
    - **Verdict:** confirmed
    - **Action:** Keep. The <=60 s TTFF target is consistent with the 28 s cold-start spec. Confirm stock at checkout. If the user turns out to be in Russia or Iran, Waveshare cannot ship there: switch to the u-blox option.
    - **Impact:** Part choice holds; price is correct.
    - **Sources:**
      - https://quectel.com/content/uploads/2024/03/Quectel_LC76G_Series_GNSS_Specification_V1.1-1-1.pdf
      - https://www.waveshare.com/lc76g-gnss-module.htm
      - https://www.waveshare.com/wiki/LC76G_GNSS_Module
      - https://littlebirdelectronics.com.au/products/lc76g-multi-gnss-module-supports-gps-bds-glonass-galileo-qzss
      - https://www.robotshop.com/es/products/waveshare-lc76g-multi-gnss-module-supports-gps-bds-glonass-galileo-qzss
  2.
    - **Claim in stack:** #79 / gpsd row: configure LC76G with $PAIR752,2,100 (PPS only on 3D fix) and $PAIR391,1 (jamming detection)
    - **Finding:** Protocol spec v1.4 (2024-03-05) confirms both commands. PAIR752 PPSType: 2 = 3D fix only; pulse width 1-999 ms, default 100. Checksums verified: PAIR752,2,100*39, PAIR391,1*2C. PAIR391 enables PAIRSPF status 1 (good), 2 (warning), 3 (critical). The gap: settings sit in RTC RAM until $PAIR513 ('Saves the current configurations from RTC RAM into flash', *3D) or $PQTMSAVEPAR (*5A) is sent. STACK never saves them. MS621FE hold time (model): 5.5 mAh / 13 uA backup current = ~17.6 days, ~9 days at 50 % usable depth. After a few weeks unpowered, unsaved PPS and jamming settings revert to defaults and the next start is cold.
    - **Verdict:** corrected
    - **Action:** Provisioning sequence, run once with gpsd stopped: $PAIR752,2,100*39, $PAIR391,1*2C, $PAIR513*3D. Then read back after a full power-off. Log $PQTMVERNO*58 at bring-up.
    - **Impact:** Without the save, PPS gating and jam flags silently disappear after storage.
    - **Sources:**
      - https://forums.quectel.com/uploads/short-url/rUEismNTHFHWMMyJR1WxrcTaRB7.pdf
      - https://www.sii.co.jp/en/me/datasheets/ms-rechargeable/ms621fe
  3.
    - **Claim in stack:** LC76G firmware and timing behaviour (implicit; TTFF not verified)
    - **Finding:** Current AB firmware cited by Quectel staff is LC76GABNR12A04S, dated 2025-05-08. No newer AB build was found. Quectel sends firmware by email only, and the QGNSS flashing tool is Windows-only. Flashing the wrong variant bricked one user's module. In an April-May 2026 thread, Quectel said this firmware moved from EASY to EPOC and that $PAIR490/491 are no longer supported. Turning EPOC off ($PAIR496,0 + $PAIR513) cut that user's chrony RMS by about 35 %. Quectel also suggested $PAIR753,1, which spec v1.4 documents only for LC26G-T; it gave a 5-8 % gain. The 'periodic PPS noise' in that thread turned out to come from the host OS, not the module.
    - **Verdict:** new_risk
    - **Action:** Keep EPOC ON. On a handheld TTFF matters more, and sub-100 ns PPS is far more than SDR ppm calibration needs. Do not use the undocumented $PAIR753,1. Do not plan field firmware updates (Windows-only tool). Record PQTMVERNO in the build log.
    - **Impact:** Low. Mainly a documentation and procedure fix; avoids chasing EASY commands that no longer work.
    - **Sources:**
      - https://forums.quectel.com/t/significant-periodic-1pps-noise-with-lc76g-module/57109
      - https://forums.quectel.com/t/latest-firmware-for-gnss-modules-lc79h-al-lc79h-el-and-lc76g-series/57735
      - https://forums.quectel.com/t/unable-to-flash-new-firmware-in-lc76g-ab-gnss-module-via-qgnss/58652
  4.
    - **Claim in stack:** #80: LC76G reports only jamming; Uputronics MAX-M10S (spoofDetState, jammingState) from GBP 28.80 / $38.36 if spoofing flags matter
    - **Finding:** Confirmed: spec v1.4 has no spoofing feature, only PAIRSPF, PQTMJAMMINGSTATUS and the JAM_IND pin. MAX-M10S datasheet R08 (30 Jan 2026): MAX-M10S-00B in mass production on ROM SPG 5.10, with 'Spoofing detection and reporting', jamming detection and 30 ns RMS timepulse. A regional variant MAX-M10S-00B1 is in initial production; this is a production-site code, not a functional lock. Uputronics store, 18 Oct 2026: 3V variant GBP 28.79, 5V level-converted variant GBP 34.79. SMA female, TP (PPS) on the header, supercap backup, default 9600 baud. A '3V out of stock until w/b 5 Oct 2026' note is still on the page. Integration catch: gpsd 3.25 does not publish spoofDetState. gpsd 3.26 added only ant_stat and jam to JSON. The gate would have to read UBX-NAV-STATUS itself, through gpsd raw watch or ubxtool.
    - **Verdict:** confirmed
    - **Action:** Keep the MAX-M10S as the region-dependent alternative. If it is chosen: use the 3V board, set 115200 baud, and add a UBX NAV-STATUS reader to the location service. The supercap only holds settings for a short time, so store the config in BBR/flash or re-apply it at boot. USD conversion not re-derived.
    - **Impact:** Spoofing flags are only available with the u-blox part, and only with extra code.
    - **Sources:**
      - https://forums.quectel.com/uploads/short-url/rUEismNTHFHWMMyJR1WxrcTaRB7.pdf
      - https://content.u-blox.com/sites/default/files/MAX-M10S_DataSheet_UBX-20035208.pdf
      - https://store.uputronics.com/products/ublox-max-m8q-breakout-for-active-antennas
      - https://gitlab.com/gpsd/gpsd/-/raw/master/NEWS
  5.
    - **Claim in stack:** 2.4 BOM / band table: Waveshare GNSS L1+L5 active antenna 25346 ($16.99) on P7; 'GNSS L1 + regional SBAS 1559-1610 MHz - reliable'
    - **Finding:** Waveshare and Pi Hut (WAV-25346, GBP 16.60) list these bands: BDS B1I/B1C/B2a, GPS L1/L1C/L5, Galileo E1/E5a, QZSS L5, IRNSS L5. GLONASS is not listed in either listing; no MHz passband is published. Specs: LNA 28+/-2 dB, NF <=2 dB, 3.0-18 V, <=20 mA, fixed 3 m RG174, SMA-J (male), 50x50x19.1 mm, 102 g, magnetic base. The LC76G is L1-only, so the L5 half is unused, and GLONASS G1 (1598-1606 MHz) may fall outside the antenna's L1 passband. Option: Waveshare GNSS helical Q25, $15.99-17.99. It lists GLONASS G1/G2, SMA male, IP67, 58.7 x 27.7 mm, but needs a separate SMA cable or magnetic base ($3.15-3.49). It is a small rigid helix, not a patch, so it needs a rules decision.
    - **Verdict:** corrected
    - **Action:** Change the band row to 'GPS/Galileo/BDS/QZSS L1 reliable; GLONASS unverified with 25346'. Either accept losing GLONASS (more than 20 satellites remain from three constellations), or buy an L1 antenna whose spec lists GLONASS G1 (Q25 helix if the antenna rule allows it). Keep the antenna's magnet away from the IMU pack (see the separate finding).
    - **Impact:** Small loss of availability and spoofing cross-check; the STACK overstates coverage.
    - **Sources:**
      - https://www.waveshare.com/gps-external-antenna-d.htm
      - https://thepihut.com/products/gnss-l1-l5-dual-frequency-active-antenna
      - https://www.waveshare.com/gnss-helical-antenna.htm
  6.
    - **Claim in stack:** P7 SMA, '3.3 V from LC76G' feeds the active antenna; IPX-SMA pigtail in the cable kit
    - **Finding:** Quectel spec says antenna power is 'External or Internal (through VDD_RF)'. The Waveshare page names neither the connector nor the bias voltage; the accessory text ('GPS external antenna (with IPX to SMA Adapter)') implies an IPX socket. The 25346 needs at least 3.0 V, so a 3.3 V VDD_RF leaves only about 0.3 V margin for any series drop. The cable kit already lists an IPX-SMA pigtail.
    - **Verdict:** unverified
    - **Action:** At bring-up, measure DC on the IPX centre pin under a 20 mA load before connecting the antenna. If it is below about 3.1 V, add an external bias-tee from 5 V.
    - **Impact:** A possible weak or absent LNA bias would look like poor C/N0.
    - **Sources:**
      - https://quectel.com/content/uploads/2024/03/Quectel_LC76G_Series_GNSS_Specification_V1.1-1-1.pdf
      - https://www.waveshare.com/lc76g-gnss-module.htm
  7.
    - **Claim in stack:** C13/#26: held 6.18.2-4 kernel lacks PPS_CLIENT_GPIO, so pps-gpio is built as DKMS; GPIO96 (pin 7) is free; Route B (7.0.11) rejected
    - **Finding:** Radxa kernel branch linux-6.18.2 (head 559f4f9, last commit 11 May 2026): qcom_module.config has no PPS_CLIENT_GPIO or PPS_CLIENT_LDISC, and RTC_DRV_DS1307=m. drivers/pps/clients/pps-gpio.c (compatible 'pps-gpio') is in the tree, so an out-of-tree DKMS build is feasible. Branch linux-7.0.11 (head 4ff8ac9, 14 Oct 2026) has PPS_CLIENT_GPIO=m and PPS_CLIENT_LDISC=m. In the Radxa DTS, GPIO96 is named 'PIN_7' and nothing references gpio96 or the mi2s0_mclk pinctrl, so it is free on the DT side. The Radxa pin page confirms pin 7 = GPIO_96 (PRI_MI2S_MCLK), 16/18 = UART6 TX/RX and 32/29 = UART7 TX/RX. CONFIG_PPS=y does not appear in the fragment itself (probably selected via PTP); it rests on the earlier installed-config check.
    - **Verdict:** confirmed
    - **Action:** Keep DKMS pps-gpio. In W1-2, check 'grep CONFIG_PPS= /boot/config-*', the pinmux-pins owner of gpio96, and ppstest /dev/pps0. Note: the 6.18.2 branch has had no commits since May 2026; if the image ever moves to 7.0.x, drop the DKMS package and use the in-tree module.
    - **Impact:** Holds; the PPS path is buildable.
    - **Sources:**
      - https://github.com/radxa/kernel/tree/linux-6.18.2
      - https://github.com/radxa/kernel/tree/linux-7.0.11
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/pin-gpio
      - https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
  8.
    - **Claim in stack:** chrony 4.5: 'refclock PPS /dev/pps0 lock NMEA', 'maxchange 5 1 -1', 'rtcsync'
    - **Finding:** chrony 4.5 docs: 'lock' pairs the PPS with another refclock 'specified by its reference ID', and PPS 'do not supply full time'. STACK defines no refclock with refid NMEA, so the PPS line cannot lock to anything. 'maxchange 5 1 -1' is correct: a negative ignore count means large offsets are ignored forever and chronyd never exits. rtcsync uses the kernel 11-minute mode and cannot be combined with rtcfile; RTC_SYSTOHC defaults to y and is not overridden in the Radxa fragment. libgpiod in noble is 1.6.3, so Route A must use the raw uAPI flag GPIO_V2_LINE_FLAG_EVENT_CLOCK_REALTIME (bit 11, present in the 6.18 uapi gpio.h).
    - **Verdict:** corrected
    - **Action:** Add 'refclock SHM 0 refid NMEA offset <measured, ~0.1-0.3> delay 0.2 noselect' (gpsd writes NMEA time to SHM 0). Keep 'refclock PPS /dev/pps0 lock NMEA'. Measure the NMEA offset against PPS in W1-2.
    - **Impact:** As written, chrony would never use the PPS.
    - **Sources:**
      - https://chrony-project.org/doc/4.5/chrony.conf.html
      - https://github.com/radxa/kernel/tree/linux-6.18.2
  9.
    - **Claim in stack:** gpsd 3.25 with GPSD_OPTIONS='-n -p -s 115200', DEVICES=/dev/gnss0, USBAUTO=false
    - **Finding:** Noble ships gpsd 3.25-3ubuntu3.2, a security update dated 6 Jan 2026 that fixes CVE-2025-67268 and CVE-2025-67269. Upstream is at 3.27.5 (14 Jan 2026); Ubuntu resolute has 3.27.5-0.1. The 3.25 man page confirms '-p, --passive: do not autoconfigure the receiver, but allow manual configuration changes' and '-s' as a fixed speed up to 921600. '-b, --readonly' stops gpsd from ever writing to the receiver. Whether -p alone still sends identification probes was not verified.
    - **Verdict:** confirmed
    - **Action:** Keep 3.25 from noble-security. Consider '-n -b -s 115200' for field use, and apply PAIR provisioning with gpsd stopped.
    - **Impact:** Low.
    - **Sources:**
      - https://changelogs.ubuntu.com/changelogs/pool/main/g/gpsd/gpsd_3.25-3ubuntu3.2/changelog
      - https://gitlab.com/gpsd/gpsd/-/raw/release-3.25/man/gpsd.adoc
      - https://gitlab.com/gpsd/gpsd/-/raw/master/NEWS
  10.
    - **Claim in stack:** UART6 = /dev/ttyHS1 with udev /dev/gnss0 (no AppArmor caveat)
    - **Finding:** The noble gpsd .deb installs /etc/apparmor.d/usr.sbin.gpsd in enforce mode (no complain flag). It allows only /dev/tty{,S,USB,AMA,ACM}[0-9]* and chrony.tty{,S,USB,AMA}*.sock, not /dev/ttyHS*; AppArmor checks the symlink target, so /dev/gnss0 -> ttyHS1 would be denied. The risk is latent: the Radxa 6.18.2 config has SECURITY_APPARMOR=y, but CONFIG_LSM='landlock,lockdown,yama,integrity,bpf' and DEFAULT_SECURITY_DAC, so AppArmor is inactive unless the kernel command line enables it.
    - **Verdict:** new_risk
    - **Action:** In W1-2, check 'cat /sys/kernel/security/lsm'. If apparmor is listed, ship /etc/apparmor.d/local/usr.sbin.gpsd containing '/dev/ttyHS[0-9]* rw,' in the lab deb. The same applies to any chrony SOCK path.
    - **Impact:** gpsd would fail to open the GNSS port if AppArmor is ever enabled.
    - **Sources:**
      - https://packages.ubuntu.com/noble/arm64/gpsd/filelist
      - https://ports.ubuntu.com/ubuntu-ports/pool/main/g/gpsd/gpsd_3.25-3ubuntu3.2_arm64.deb
      - https://github.com/radxa/kernel/tree/linux-6.18.2
  11.
    - **Claim in stack:** lab-q6a.dtso merges Radxa uart6/uart7 overlays; port appears as /dev/ttyHS1; udev symlink to /dev/gnss0
    - **Finding:** radxa-overlays (head e713889, 14 Oct 2026) has qcs6490-radxa-dragon-q6a-uart6.dtso (pins 16 TX / 18 RX; it disables i2c6 and spi6 and is exclusive with gpio26/27) and a uart7 overlay. There is no PPS overlay upstream, so the pps-gpio node must be custom, as planned. The qcom_geni_serial driver numbers non-aliased ports from the highest serial alias + 1 (serial0 = uart5) in probe order. uart6 (0x998000) and uart7 (0x99c000) can therefore come up as ttyHS1 or ttyHS2. Wi-Fi/BT (FCU760K) is on USB, so no BT UART competes.
    - **Verdict:** confirmed
    - **Action:** Keep the udev rule KERNELS=='998000.serial' -> /dev/gnss0. Never hard-code ttyHS1.
    - **Impact:** Holds.
    - **Sources:**
      - https://github.com/radxa-pkg/radxa-overlays
      - https://github.com/radxa/kernel/tree/linux-6.18.2
  12.
    - **Claim in stack:** #7: RTC 'RS4C411 with CR2032' anchors the time gate; '$0.95 RTC battery'; check the connector against schematic sheet 18
    - **Finding:** Mainline and Radxa DTS: rtc@68, compatible 'st,m41t11', on i2c10. The PMIC RTC (pmk8350) is disabled, so this RTC is rtc0. Radxa docs: CR2032, '2-Pin 1.25mm', 3.3 V, /dev/rtc0, with a polarity warning. rtc-ds1307 is a module, but the 6.18 rtc class code calls rtc_hctosys() when the device registers (RTC_HCTOSYS defaults to y), so system time is still set from the RTC at boot. The part name 'RS4C411' could not be found in any datasheet; only the M41T11-compatible binding is confirmed. The $0.95 price was not verified: the plug needs a leaded cell, not a bare coin. Radxa X4 docs say the RTC connector does not charge; the Q6A docs are silent.
    - **Verdict:** confirmed
    - **Action:** Buy a pre-wired CR2032 with a 1.25 mm 2-pin plug (Radxa 2-pin RTC battery or similar; price unverified) and check polarity with a meter. In W1-2, after 10+ minutes unpowered, check 'dmesg | grep -i hctosys' and 'hwclock -r -f /dev/rtc0'. Change the wording 'RS4C411' to 'M41T11-compatible (part name unverified)'.
    - **Impact:** Holds; BOM wording and price need a fix.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/rtc
      - https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://docs.radxa.com/en/x/x4/accessories/rtc-battery
      - https://www.electrokit.com/en/cr2032-med-kabel-3.0v-180mah
  13.
    - **Claim in stack:** #7 gate: accept a fix only if GNSS time is within 120 s of the RTC
    - **Finding:** Model; the M41T11-type RTC has no published accuracy here and no temperature compensation. 120 s is exceeded after 69 days at 20 ppm, 28 days at 50 ppm, and 14 days at 100 ppm. A watch crystal stored at -10 C adds about -42 ppm (-0.034 ppm/C^2 parabola, model). A device left in a drawer or a cold car for a month or more will see genuine GNSS time rejected, or wrongly flagged as spoofed.
    - **Verdict:** new_risk
    - **Action:** Make the window grow with RTC age: 120 s + 100 ppm x (RTC now - last trusted sync), with the last-sync stamp stored in /data. Beyond the window, mark the time 'unverified' rather than rejecting it, unless another spoofing indicator is present.
    - **Impact:** Medium. Prevents false rejections after storage.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/rtc
  14.
    - **Claim in stack:** #7: fallbacks = last good fix with age, or manual lat/lon or Maidenhead; no city table; admin-0 polygons for jurisdiction only; export rounded to 0.1 deg or a 4-character locator; a 100 km error moves GEO pointing by only 1-2 deg
    - **Finding:** Complies with the hard rules: no city lists, and admin-0 polygons are country boundaries used only for jurisdiction. Model check for a GEO at 25.9E: a 100 km error changes azimuth by 0.2-1.7 deg and elevation by 0.3-1.0 deg at latitudes 10-50 N, which matches '1-2 deg'. IMU heading is shown live only, so the no-bearing-log rule is kept.
    - **Verdict:** confirmed
    - **Action:** Keep.
    - **Impact:** Holds.
    - **Sources:**
      - https://www.ncei.noaa.gov/products/world-magnetic-model
  15.
    - **Claim in stack:** WMM2025 computed at the fix point for declination
    - **Finding:** NCEI: WMM2025 released 17 Dec 2024, valid until 31 Dec 2029. No out-of-cycle update is listed as of Oct 2026. The 27 Jan 2026 NOAA news item is the separate HDGM 2026 model. A WMM2025 technical report (Aug 2025) and annual report (Jan 2026) exist. NCEI publishes blackout-zone maps for the magnetic-pole regions. Implementation option: pygeomag 1.1.0 (21 Dec 2024) defaults to WMM-2025, supports WMMHR-2025 and tests NOAA's published test values.
    - **Verdict:** confirmed
    - **Action:** Use pygeomag 1.1.0 with the WMM2025 COF, pinned in the lab venv. Show a 'compass unreliable' warning inside the WMM blackout or caution zones. Re-check for WMM2030 in late 2029.
    - **Impact:** Holds.
    - **Sources:**
      - https://www.ncei.noaa.gov/products/world-magnetic-model
      - https://www.ncei.noaa.gov/node/8611
      - https://pypi.org/project/pygeomag/
  16.
    - **Claim in stack:** D12 / 2.8: IMU pack = Adafruit BNO085 4754 ($29.50) + RP2040-Zero ($4.99); budget alternative SparkFun BNO086 $34.95
    - **Finding:** BNO08X datasheet rev 1.17: rotation error 2.0 deg static / 3.5 deg dynamic, heading drift 0.5 deg/min, magnetometer 1.4 uT. 'The master device MUST support clock stretching'; repeated start is not supported; magnetometer calibration is off in UART-RVC mode. Adafruit 4754: $29.50, in stock (PCB refresh Dec 2023). SparkFun SEN-22857 BNO086: $34.95, in stock. Mouser shows BNO085/BNO086 stock with incoming 2026 lots; no EOL or NRND notice was found. RP2040-Zero (SKU 20187): $3.99-4.99, 20 edge GPIO, 2 MB flash, USB-C. Library tags: Adafruit_BNO08x 1.2.7, SparkFun_BNO08x v1.0.6, CEVA sh2 v1.4.0; arduino-pico 6.3.0; pico-sdk 2.3.1.
    - **Verdict:** confirmed
    - **Action:** Keep. Note that the 'budget' BNO086 costs more than the BNO085.
    - **Impact:** Holds.
    - **Sources:**
      - https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf
      - https://www.adafruit.com/product/4754
      - https://www.sparkfun.com/sparkfun-vr-imu-breakout-bno086-qwiic.html
      - https://www.mouser.co.uk/c/?m=CEVA
      - https://www.waveshare.com/rp2040-zero.htm
      - https://github.com/adafruit/Adafruit_BNO08x
      - https://github.com/sparkfun/SparkFun_BNO08x_Arduino_Library
      - https://github.com/ceva-dsp/sh2
  17.
    - **Claim in stack:** IMU 'single interface': framed UART at 115200 with CRC from the pack to Pico UART1 (GP8/9); the BNO085-to-RP2040-Zero link inside the pack is not specified
    - **Finding:** The external single interface is sound: Pico GP8/GP9 are UART1 TX/RX in the RP2040 function table (not re-fetched this pass), separate from the UART7 link. Inside the pack, BNO08x I2C is the weak point. SparkFun forum: a BNO086 on an RP2040 would not run above 100 kHz because of clock stretching. Adafruit lists the BNO085 among troublesome clock-stretching I2C chips. SPI (with INT and RST wired) avoids this, and the Adafruit 4754 supports SPI.
    - **Verdict:** new_option
    - **Action:** Specify SPI between RP2040-Zero and BNO085 inside the pack (SCK, MOSI, MISO, CS, INT, RST; about 8 of the 20 edge GPIO). Fall back to I2C at 100 kHz only if needed.
    - **Impact:** Removes the main known failure mode of the BNO08x.
    - **Sources:**
      - https://community.sparkfun.com/t/bno086-and-rp2040-dont-work-faster-than-100-khz/67222
      - https://learn.adafruit.com/raspberry-pi-i2c-clock-stretching-fixes/example-issue
      - https://github.com/bradcar/bno08x_i2c_spi_MicroPython
      - https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf
  18.
    - **Claim in stack:** #9 IMU pack RFI: metal pack, ferrite, >=30 cm behind active elements; A/B tests at 145.9 and 437 MHz
    - **Finding:** Model: harmonics of the RP2040's 12 MHz crystal (144 and 432 MHz) fall outside the 145.8-146.0 and 435-438 MHz satellite sub-bands, so the earlier '144/432 MHz' worry is overstated. They do fall inside GNSS L1 (1560, 1572, 1584, 1596, 1608 MHz) and L-band HRPT/GOES (1692, 1704 MHz). The default 125 MHz system clock has no harmonics in any listed band; 100 or 133 MHz would put harmonics in GNSS L1. Not measured.
    - **Verdict:** new_risk
    - **Action:** Keep clk_sys at 125 MHz. Add GNSS C/N0 and L-band noise-floor checks with the pack on and off to the A/B matrix.
    - **Impact:** Low-medium; matters when the pack sits near the GNSS antenna.
    - **Sources:**
      - https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf
  19.
    - **Claim in stack:** #82: external active GNSS antenna on a 1-3 m lead; IMU pack 15-20 cm from steel and LNA
    - **Finding:** The 25346 has a magnetic mounting base (Waveshare spec). If it is placed on the mast, tripod or boom near the BNO085 pack, it will bias heading and fail the |B| and dip checks against WMM.
    - **Verdict:** new_risk
    - **Action:** Keep the magnetic-base antenna at least 30 cm from the pack (same rule as steel), or mount it with tape or a non-magnetic clip. Add this to the assembly instructions.
    - **Impact:** Low-medium heading error if ignored.
    - **Sources:**
      - https://www.waveshare.com/gps-external-antenna-d.htm
  20.
    - **Claim in stack:** Pointing aid: elevation from gravity, azimuth from sun-sighting (~1 min); magnetometer off on the steel tape Yagi; Skyfield 1.55 / sgp4 2.27
    - **Finding:** Datasheet heading drift of 0.5 deg/min (Game RV) gives, as a model, 2.5 / 5 / 7.5 deg after 5 / 10 / 15 min from the sun alignment. That is inside 30-60 deg beamwidths, but adds up over long sessions. Skyfield 1.55 (7 Aug 2026) and sgp4 2.27 (3 Jul 2026) are the current PyPI releases; noble apt has only Skyfield 1.48.
    - **Verdict:** confirmed
    - **Action:** Keep. Prompt a re-sight every 15-20 min of Game-RV-only pointing. Keep Skyfield and sgp4 in the venv, not apt.
    - **Impact:** Holds.
    - **Sources:**
      - https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf
      - https://pypi.org/project/skyfield/
      - https://pypi.org/project/sgp4/
  21.
    - **Claim in stack:** #1093: 'Quectel regional lock behaviour (unknown)'
    - **Finding:** Protocol spec v1.4 documents no region lock. It has only user geofences (PQTMCFGGEOFENCE / PQTMGEOFENCESTATUS) and the dynamic limits of 10,000 m and 490 m/s. The real regional restriction is commercial: Waveshare may not ship the LC76G to, or support it in, Iran or Russia.
    - **Verdict:** corrected
    - **Action:** Replace 'regional lock unknown' with 'no functional region lock documented; shipping embargo Iran/Russia; altitude limit 10 km'.
    - **Impact:** Closes an open question.
    - **Sources:**
      - https://forums.quectel.com/uploads/short-url/rUEismNTHFHWMMyJR1WxrcTaRB7.pdf
      - https://www.waveshare.com/LC76G-GNSS-Module.htm
  22.
    - **Claim in stack:** Spoofing gate inputs: RTC, saved position, TLE window, jamming flag
    - **Finding:** Not tested; method proposals. (a) The stack already receives civilian LF time stations (DCF77, MSF, WWVB, JJY). Their time codes are a time reference that does not depend on GNSS, and they are public broadcasts, so decoding them is allowed. (b) Per-satellite C/N0 from gpsd SKY: if many satellites show uniformly high, nearly identical C/N0, that is a known spoofing signature. (c) Comparing |B| and dip from the BNO085 with WMM at the claimed position can flag gross position spoofs of hundreds of km or more, but only in a clean magnetic environment.
    - **Verdict:** new_option
    - **Action:** Add (a) as an optional cross-check where an LF station is in range, and (b) and (c) as soft warnings, never hard rejects. Validate them in the field before trusting them.
    - **Impact:** Adds spoofing indicators to the LC76G without extra cost.
    - **Sources:**
      - https://forums.quectel.com/uploads/short-url/rUEismNTHFHWMMyJR1WxrcTaRB7.pdf
      - https://www.ncei.noaa.gov/products/world-magnetic-model
  23.
    - **Claim in stack:** #83: LimeSDR Micro GNSS variant not taken (+$50); firmware passes no NMEA or PPS
    - **Finding:** Not re-checked in this pass. It applies only if the Lime is kept.
    - **Verdict:** unverified
    - **Action:** Re-check only if the Lime is reinstated.
    - **Impact:** None for the core build.
    - **Sources:**
      - https://github.com/myriadrf/LimeSDR-Micro_FW
- **Current status oct 2026:** As of 18 Oct 2026:
  
  **GNSS**
  - **LC76G:** Waveshare 24370 is listed at $14.99, with no stock text on its page. Firmware LC76GABNR12A04S (2025-05-08) is the newest AB build I found; Quectel sends firmware by email and flashes it only with the Windows QGNSS tool. That firmware moved from EASY to EPOC, and PAIR490/491 are dropped. Protocol spec v1.4 (2024-03-05) is the newest public one. No EOL notice found.
  - **u-blox MAX-M10S:** datasheet R08 (30 Jan 2026), mass production on ROM SPG 5.10, with spoofing and jamming detection. A regional variant (-00B1) is in initial production. Uputronics breakout: GBP 28.79 (3V) / 34.79 (5V).
  - **Waveshare 25346 antenna:** $16.99 (Pi Hut GBP 16.60). The spec does not list GLONASS.
  
  **IMU**
  - BNO08X datasheet rev 1.17. Adafruit 4754 is $29.50 and in stock; SparkFun BNO086 is $34.95 and in stock. Mouser has stock plus incoming 2026 lots; no EOL notice found.
  - RP2040-Zero is $3.99-4.99.
  - Library tags: Adafruit_BNO08x 1.2.7, SparkFun BNO08x v1.0.6, CEVA sh2 v1.4.0.
  
  **Kernel and device tree**
  - Radxa linux-6.18.2 branch: last commit 11 May 2026; no PPS_CLIENT_GPIO.
  - Radxa linux-7.0.11 branch: updated 14 Oct 2026; has PPS_CLIENT_GPIO=m.
  - radxa-overlays (14 Oct 2026): has the Q6A uart6 and uart7 overlays, no PPS overlay.
  
  **Ubuntu noble packages**
  - gpsd 3.25-3ubuntu3.2 (security fixes CVE-2025-67268/67269, Jan 2026). It ships an enforce-mode AppArmor profile that omits ttyHS ports; this only matters if AppArmor is enabled.
  - chrony 4.5-1ubuntu4.2 and libgpiod 1.6.3.
  - Upstream: gpsd 3.27.5, chrony 4.8 (in resolute).
  
  **Magnetic model and pointing software**
  - WMM2025 is current and valid to 31 Dec 2029, with no out-of-cycle update.
  - pygeomag 1.1.0 defaults to WMM2025.
  - Skyfield 1.55 and sgp4 2.27 are the current releases.
- **Notes:** **Method.** I used 13 WebSearch calls. Everything else came from primary pages and files:
  - Quectel spec and protocol PDFs, read with pdftotext.
  - The CEVA datasheet.
  - The u-blox datasheet R08.
  - The Waveshare, Adafruit, SparkFun and Uputronics shop JSON and pages.
  - Launchpad and the Ubuntu changelog, plus the noble gpsd .deb itself (its AppArmor profile).
  - Sparse git clones of radxa/kernel (linux-6.18.2 and linux-7.0.11 configs, DTS, rtc class code, qcom_geni_serial), radxa-pkg/radxa-overlays, gpsd release-3.25, and Debian util-linux.
  
  **Numbers that are models, not measurements:**
  - MS621FE hold time of about 17.6 days (5.5 mAh / 13 uA).
  - RTC drift against the 120 s gate.
  - Cold-storage crystal drift.
  - Game Rotation Vector drift over a satellite pass.
  - RP2040 clock-harmonic map.
  - GEO look-angle error for a 100 km position error.
  
  **Unverified:**
  - The part name RS4C411.
  - The $0.95 RTC cell (it needs a pre-wired 1.25 mm plug).
  - The LC76G board's antenna connector type (IPX is likely) and its bias voltage.
  - The 25346 antenna's real passband for GLONASS.
  - Whether gpsd -p still sends identification probes.
  - That the board's installed kernel config has CONFIG_PPS=y; the source tree only implies it.
  - Whether AppArmor is active on the shipped image.
  - USD conversions for GBP prices.
  
  **Highest-value edits to STACK.md:**
  1. Add a chrony refclock with refid NMEA (SHM 0); without it the 'lock NMEA' PPS line has nothing to lock to.
  2. Add $PAIR513 so the LC76G settings are saved to flash.
  3. Make the RTC time window grow with time since the last trusted sync.
  4. Fix the GNSS antenna's GLONASS claim, or choose an antenna whose spec lists GLONASS G1.
  5. Use SPI between the BNO085 and the RP2040-Zero inside the pack.
  6. Keep EPOC on.
  7. Add an AppArmor local rule if the LSM list includes apparmor.
  
  **Hard-rule check.** The subsystem keeps every hard rule: receive-only, no loops, no city tables, no emitter geolocation, and IMU heading is live only. The Q25 helix option needs the user's antenna-rule decision.
  
  Working files from this research are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/gnss_dl/.

## Адверсаріальна перевірка (`verify`)

_Run `wf_d9388111-e66`_

- **Subsystem:** gnss_imu_location: Waveshare 24370 LC76G(AB) with MS621FE backup cell; PPS on GPIO96 through DKMS pps-gpio on the held 6.18.2-4 kernel; Q6A RTC (RS4C411ZAE, M41T11 binding, CR2032); BNO085 IMU pack (RP2040-Zero, framed UART to Pico UART1); location gate with city-table-free fallbacks; WMM2025; pointing aid. Region: Europe.
- **Verdict:** Mostly holds, with five material fixes. (1) The PPS provisioning from stages 1 and 2 does not persist. Spec v1.4, PAIR513 note 3, says "This command does not support saving configurations set by PPS-related PAIR messages". So $PAIR752 plus $PAIR513 survives only while the MS621FE backup cell holds, and the stage-2 "TX-free" fallback fails for PPS. The fix is $PQTMCFGPPS,W,1,1,100,3,0,0*70 plus $PQTMSAVEPAR*5A, which the spec documents for LC76G but which still needs a bench test. (2) The RTC part name "RS4C411" is correct: Radxa schematic v1.21, page 16, shows RS4C411ZAE with a 20 ppm 32.768 kHz crystal. Stage 1's rename is refuted. (3) The 125 MHz clock for the IMU pack is not the default in the toolchain the pack uses. arduino-pico 6.3.0 defaults to 200 MHz, whose 8th harmonic (1600 MHz) falls inside GLONASS G1, so 125 MHz must be set explicitly. (4) The Waveshare LC76G board must be fed 5 V. Its RT9193-33 LDO feeds both the antenna bias (VCC_RF through 10 ohm) and the MS621FE charging path (1N4148 + 470 ohm). (5) The held 6.18.2-4 kernel image and headers are now only on the GitHub releases page (radxa-pkg/linux-qcom 6.18.2-4); the radxa-repo qcs6490-noble index lists only 7.0.11-7. The 6.18.2-4 image config itself confirms CONFIG_PPS=y, PPS_CLIENT_GPIO unset, no module signing, RTC_HCTOSYS/SYSTOHC on rtc0 and AppArmor outside CONFIG_LSM. The chrony fix (SHM 0 refid NMEA plus PPS lock) holds: the chrony 4.5 source has PPS_LOCK_LIMIT 0.4 s, and selectopts has existed since 4.4. LC76G stays the Europe default. MAX-M10S stays optional, because its datasheet lists no flash, so its config lives in supercap-backed BBR and needs the still-unproven UART6 TX at every power-up. Method: the WebSearch budget was already used up, so every claim was re-checked by direct fetches of primary PDFs, source trees, .debs, forum JSON and shop pages.
- **Confirmed:**
  - LC76G(AB) spec V1.1: GPS L1 C/A, GLONASS L1, Galileo E1, BDS B1I+B1C, QZSS; 47 channels; 4 GNSS + QZSS concurrent; SBAS WAAS/EGNOS/MSAS/GAGAN; 1PPS 30 ns RMS; UART 9600-921600, default 115200, up to 10 Hz; I2C up to 400 kbps; supply 2.55-3.6 V, I/O = VCC; 36 mA tracking; 13 uA backup mode; TTFF 28/25/1 s without AGNSS (cold/warm/hot); limits 10,000 m, 490 m/s, 4 g. https://quectel.com/content/uploads/2024/03/Quectel_LC76G_Series_GNSS_Specification_V1.1-1-1.pdf
  - Waveshare 24370: $14.99 (tiers $14.19/$13.79/$13.63); VCC 3.3-5 V; MS621FE rechargeable backup; MX1.25 8-pin cable; Waveshare's own TTFF figure is 26 s cold autonomous; Quectel bars shipping to Iran and Russia. https://www.waveshare.com/lc76g-gnss-module.htm
  - Waveshare schematic: header P1 is 1 VCC, 2 GND, 3 TXD, 4 RXD, 5 1PPS (direct from LC76G pin 4; it also drives the PPS LED FET through 1 kOhm), 6 RESET, 7 SDA, 8 SCL. Antenna socket is IPEX; active bias comes from VCC_RF through 10 ohm + 68 nH. Backup charging runs from 3V3 through a 1N4148 and 470 ohm. https://files.waveshare.com/wiki/LC76G/manual/LC76G%20GNSS%20Module.pdf
  - Protocol spec v1.4 (2024-03-05) commands and checksums, re-computed: $PAIR752,2,100*39 (PPS on 3D fix only; types 5-8 are LC26G-T only); $PAIR391,1*2C turns on $PAIRSPF (0 unknown, 1 good, 2 warning, 3 critical); $PAIR513*3D; $PQTMSAVEPAR*5A; $PAIR006*3C (cold start, keeps settings); $PAIR007*3D (also restores factory settings); $PQTMVERNO*58; $PAIR496,0*2D, $PAIR508*37 and $PAIR509*36 match what Quectel staff posted.
  - No spoofing feature exists on LC76G: the spec has only PAIRSPF, PQTMJAMMINGSTATUS and the JAM_IND pin. The only region-related features are user geofences and the dynamic limits.
  - Quectel forum 57735: the user's current firmware is LC76GABNR12A04S (2025-05-08), and Quectel emailed 'the latest FW version'. Thread 58652: the QGNSS V2.4 upgrade needs a RESET_N pulse within 20 s of the handshake; it worked, so there was no brick. Thread 57109: A04S moved from EASY to EPOC and PAIR490/491 are gone; turning EPOC off cut RMS offset by about 35 %; $PAIR753,1 gave 5-8 %; the periodic noise came from the host OS. Thread 45880: with PPSType 1 the pulse free-ran for 45 min with no fix. Thread 47717: on the LC29H, NMEA arrives about 80 ms after PPS, and 300-400 ms once every 30 min during the ephemeris flash save.
  - Quectel forum 57394 (May 2026): for the sibling LC86G (LC86GABNR12A02S), Quectel staff wrote 'Unfortunately the module will not be working in Russia'. This is a functional restriction whose mechanism is undocumented.
  - Quectel LC76G product page lists Protocol Spec V1.5, Hardware Design V1.3, the EASY&EPOC Difference Introduction V1.0, Firmware Upgrade Guide V1.2 and QGNSS V2.5 (login-gated), and shows no EOL status. https://www.quectel.com/product/gnss-lc76g/
  - MAX-M10S datasheet R08 (30 Jan 2026): -00B-01 in mass production on ROM SPG 5.10; -00B1 is a regional production-site variant in initial production; it has anti-jamming and anti-spoofing; timepulse 30 ns RMS; default GPS+Galileo+BDS B1I with SBAS (incl. EGNOS) and QZSS; GLONASS cannot run together with B1I.
  - Uputronics 'uBLOX MAX Breakout for Active Antennas' (the URL slug still says m8q, but the board carries a MAX-M10S): 3V GBP 28.79, 5V GBP 34.79; a stale 'out of stock until w/b 5 Oct 2026' note; supercap; TP (PPS) on the header; default 9600 baud. At the ECB rates of 16 Oct 2026 that is about $38.39 and $46.39, VAT treatment not checked.
  - Waveshare 25346 antenna: $16.99; bands BDS B1I/B1C/B2a, GPS L1/L1C/L5, Galileo E1/E5a, QZSS L5, IRNSS L5, with GLONASS not listed; 28+/-2 dB, NF <=2 dB, 3.0-18 V, <=20 mA, RG174 3 m, SMA-J, magnetic base or tape. https://www.waveshare.com/gps-external-antenna-d.htm
  - Radxa kernel branch heads: linux-6.18.2 = 559f4f9 (2026-05-11) and linux-7.0.11 = 4ff8ac9 (2026-10-14). The 6.18.2 qcom_module_defconfig has no PPS_CLIENT_GPIO; the 7.0 defconfig has PPS_CLIENT_GPIO=m and PPS_CLIENT_LDISC=m. pps-gpio.c (compatible 'pps-gpio') is in the 6.18.2 tree. The 6.18 uapi defines GPIO_V2_LINE_FLAG_EVENT_CLOCK_REALTIME as bit 11.
  - linux-image-6.18.2-4-qcom /boot/config: CONFIG_PPS=y, PPS_CLIENT_GPIO/LDISC not set, PTP_1588_CLOCK=y, RTC_HCTOSYS=y and RTC_SYSTOHC=y on rtc0, RTC_DRV_DS1307=m, MODULE_SIG not set, SECURITY_APPARMOR=y but CONFIG_LSM='landlock,lockdown,yama,integrity,bpf', built with Debian gcc 12.2.0.
  - Q6A DTS (6.18.2): rtc@68 'st,m41t11' on i2c10; pmk8350_rtc is status=disabled, so the M41T11-type RTC is rtc0; GPIO96 is named 'PIN_7' and nothing else references it. The 6.18 rtc class code calls rtc_hctosys() on registration. rtc-ds1307 handles m41t11 by checking only the CH bit (no oscillator-fail flag).
  - Radxa pin page: pin 7 = GPIO_96 (PRI_MI2S_MCLK), 16/18 = UART6 TX/RX, 32/29 = UART7 TX/RX. radxa-overlays e713889 (2026-10-14) has the Q6A uart6 overlay (disables spi6/i2c6, tx/rx pinctrl, exclusive with gpio26/27) and no pps-gpio overlay anywhere. Issue #534 (MI2S0 audio on Q6A) names GPIO97/98/100, not GPIO96.
  - qcom_geni_serial (6.18.2): non-aliased ports take numbers from the highest serial alias + 1 (serial0 = uart5), and the driver logs 'Invalid FW loaded' or 'UART firmware load failed'. Forum 30455: UART6 and UART12 came up as ttyHS1/ttyHS2. Forum 30063: UART6 worked in both directions after an overlay fix that was never published (a Sep 2026 question is unanswered). Forum 31422: TX does not arrive while RX works, unresolved. Forum 29642: Radxa staff point to the UEFI 'QUPV3_xxx Mode' setting.
  - gpsd in noble = 3.25-3ubuntu3.2 (security fixes CVE-2025-67268 and CVE-2025-67269, 6 Jan 2026). Man page: -b read-only, -p passive, -s fixed speed. SHM NTP0/NTP1 go to the first device, gpsd must start as root, and it writes time only after NTP_MIN_FIXES. gpsd 3.25 sends PMTK/PQ commands only in reply to PMTK705/424, which the LC76G does not emit. gpsd 3.25 has no spoofing field (3.26 added ant_stat and jam only).
  - Noble AppArmor profiles: gpsd allows /dev/tty{,S,USB,AMA,ACM}N and /run/chrony.tty*N.sock only, so ttyHS is denied; chronyd allows /dev/pps*, /dev/rtc* and /run/chrony.*.sock, and SHM needs 'capability ipc_owner' (LP #722815). Both are latent because AppArmor is not in CONFIG_LSM.
  - chrony 4.5-1ubuntu4.2 (noble-updates). The chrony.conf(5) example is 'refclock PPS /dev/pps0 lock NMEA refid GPS1' plus a NMEA source marked noselect. maxchange with a negative ignore count ignores large offsets forever. 'selectopts' was added in 4.4 and accepts a refclock refid. The noble default chrony.conf has pools, rtcsync and 'makestep 1 3'.
  - Radxa RTC doc: CR2032, '2-Pin 1.25mm', 3.3 V, polarity warning, /dev/rtc0, rtc-ds1307, hwclock via util-linux-extra; nothing about charging. Forum 31194 (ML2020 recharge question) has no answer.
  - BNO08X datasheet rev 1.17 (24 Jul 2023): RV 2.0 deg static / 3.5 deg dynamic; Game RV heading drift 0.5 deg/min; GeoRV 3.0/4.5 deg; magnetometer 1.4 uT; 'in practice' RV is about 5 deg and GeoRV about 10 deg. The I2C master 'MUST support clock stretching'; repeated start is not supported; SPI max 3 MHz; PS0/WAKE must be high from before reset; the host must answer H_INTN within about 10 ms. UART-RVC turns magnetometer calibration off.
  - Adafruit 4754: $29.50, in stock (PCB silkscreen refresh Dec 2023). SPI wiring: P0 and P1 to 3V; SCL to SCK, SDA to MISO, DI to MOSI; CS, INT and RST to GPIO; INT and RST are 'Required for stable SPI operation'. SparkFun BNO086 SEN-22857: $34.95, in stock. RP2040-Zero (SKU 20187): $3.99-4.99, 20 edge GPIO + 9 pads.
  - Adafruit_BNO08x 1.2.7 source: SPI at 1 MHz in SPI_MODE3; INT wait of 500 ms followed by a hardware reset; UART-SHTP at 3 Mbaud. Library tags: SparkFun v1.0.6, sh2 v1.4.0, arduino-pico 6.3.0, pico-sdk 2.3.1.
  - Library defects confirmed in source: SparkFun v1.0.6 getGravity(x,y,z,acc) returns gravityX for all three axes (lines 512-514); sh2 v1.4.0 euler.h declares q_to_ypr(..., pRoll, pPitch, pYaw) while euler.c defines (pYaw, pPitch, pRoll); sh2 #3 (setReorientation x/y) and #18 (40 Hz vibration glitch) are open; Adafruit #27, #29 and #37 are open.
  - SparkFun forum 67222 (Oct 2025): a BNO086 on an RP2040 works at 100 kHz and fails at 350-400 kHz, attributed to clock stretching. The SlimeVR IMU page rates the BNO085 'Poor', notes the stomp bug and says it was 'discontinued from the SlimeVR store'.
  - WMM2025: released 17 Dec 2024, valid until 31 Dec 2029, no out-of-cycle update listed. pygeomag 1.1.0 (2024-12-21) is the newest. Skyfield 1.55 (2026-08-07) and sgp4 2.27 (2026-07-03, needs Python >=3.10) are current on PyPI.
  - SII MS621FE: 3 V, 5.5 mAh, charge voltage 2.8-3.3 V (standard 3.1 V). Hold-time model: 5.5 mAh / 13 uA = 17.6 days at full capacity.
  - EASA SIB 2022-02R4 exists (it revises R3 of 5 Jul 2024). The PDF names the south and eastern Mediterranean, Black Sea, Middle East, Baltic Sea and Arctic; lists 'loss or misleading time and/or date'; and advises 'Monitor the GNSS time versus non-GNSS time sources'.
  - Hard rules hold: receive-only; no loops; no city table (fallbacks are last fix, manual lat/lon or Maidenhead); admin-0 polygons are used for jurisdiction only; IMU heading is shown live and never logged as bearings; the Russia note concerns the device's own position.
- **Corrections:**
  1.
    - **Claim in stack:** Stage 1/2 provisioning: $PAIR752,2,100*39 + $PAIR391,1*2C + $PAIR513*3D saves the PPS and jamming settings to flash, so at runtime RX plus PPS is enough (the TX-free fallback)
    - **Finding:** Spec v1.4 PAIR513 note 3: 'This command does not support saving configurations set by PPS-related PAIR messages.' Note 1: settings sit in RTC RAM, held only by the backup supply. So PPSType 2 is lost once the MS621FE runs flat, and the default PPS behaviour is not documented. PQTMCFGPPS (Set/Get, Mode 3 = 3D fix; only <Interval> is limited to LC26G-T) is a PQTM command, and PQTMSAVEPAR 'Saves the configurations set via $PQTM commands to NVM'.
    - **Verdict:** corrected
    - **Action:** Provision PPS with $PQTMCFGPPS,W,1,1,100,3,0,0*70 then $PQTMSAVEPAR*5A, and read back with $PQTMCFGPPS,R,1*6A. Keep $PAIR391,1*2C, $PAIR410,1*22 and $PAIR400,2*20, followed by $PAIR513*3D, for the PAIR settings. Use one PPS method only. If UART6 TX works, re-assert the PQTMCFGPPS read-back from a gpsd ExecStartPre script at every boot. The TX-free fallback is valid only after the persistence bench test passes.
    - **Impact:** Without this, after storage chrony could lock to a pulse that keeps running without a fix (thread 45880: up to 45 min), or PPS gating silently changes.
    - **Sources:**
      - https://forums.quectel.com/uploads/short-url/rUEismNTHFHWMMyJR1WxrcTaRB7.pdf
      - https://forums.quectel.com/t/gnss-lc76g-1-pss-configuration/45880
  2.
    - **Claim in stack:** #7 / 2.8 BOM: RTC 'RS4C411 with CR2032'; stage 1: rename it to 'M41T11-compatible (part name unverified)'; 'check the connector against schematic sheet 18'
    - **Finding:** Radxa schematic v1.21, PDF page 16, shows U 'RS4C411ZAE' (pinout X1, X2, VBAT, GND, SDA, SCL, SQW/OUT, VCC, like the DS1307/M41T11), a 32.768 kHz 12.5 pF 20 ppm crystal, a BAT54CW diode-OR into VRTC, connector J11 (CON_1X2) through 1 kOhm, and a VCOIN net to sheet 18. The DT binding is st,m41t11 and the driver rtc-ds1307.
    - **Verdict:** corrected
    - **Action:** Keep 'RS4C411ZAE (Radxa schematic v1.21 p.16), driver binding st,m41t11, rtc0'. Fix the reference from 'sheet 18' to 'PDF page 16, J11'. Use only a primary CR2032 with a pre-wired 1.25 mm 2-pin plug (price unverified). Use 20 ppm as the base drift in the gate model.
    - **Impact:** Stage 1's rename was wrong; the part name is documented.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/rtc
  3.
    - **Claim in stack:** Stage 1 #9 RFI: 'Keep clk_sys at 125 MHz; the default 125 MHz system clock has no harmonics in any listed band'
    - **Finding:** pico-sdk 2.3.1 does default to 125 MHz (200 MHz only with PICO_USE_FASTEST_SUPPORTED_CLOCK=1). The pack firmware, however, is Adafruit_BNO08x on arduino-pico 6.3.0, and boards.txt lists 'waveshare_rp2040_zero.menu.freq.200' as the first, and therefore default, menu entry. Model: 8 x 200 MHz = 1600 MHz, inside GLONASS G1 (about 1597.5-1605.9 MHz). The 12 MHz crystal harmonics (1560, 1572, 1584, 1596, 1608, 1692 and 1704 MHz) are present at any clk_sys.
    - **Verdict:** corrected
    - **Action:** Build with FQBN rp2040:rp2040:waveshare_rp2040_zero:freq=125 (or call set_sys_clock_khz(125000) at start). Report clock_get_hz(clk_sys) in the frame header and have labd reject packs that do not report 125 MHz. Keep the pack at least 30 cm from the GNSS antenna and add pack on/off GNSS C/N0 and 1692/1704 MHz checks to the A/B matrix.
    - **Impact:** Default builds would put a CW spur inside GLONASS G1, about 3.4 MHz from L1-band signals.
    - **Sources:**
      - https://raw.githubusercontent.com/earlephilhower/arduino-pico/6.3.0/boards.txt
      - https://github.com/raspberrypi/pico-sdk/blob/2.3.1/src/rp2040/hardware_regs/include/hardware/platform_defs.h
  4.
    - **Claim in stack:** P7 'SMA, 3.3 V from LC76G'; 2.8 BOM GNSS; VCC_5V_PERI lists GNSS as a load
    - **Finding:** Schematic: the board's RT9193-33 LDO makes the 3V3 that feeds the LC76G VCC, VCC_RF (the antenna bias through R5 10 ohm + L1 68 nH) and the backup charging path (1N4148 + 470 ohm to V_BAT). Model: with VCC = 5 V the antenna sees about 3.1 V at 20 mA, against a 3.0 V minimum for the 25346, and the MS621FE charges at about 2.7-2.9 V, below SII's standard 3.1 V. With VCC = 3.3 V the LDO drops out and both values fall further.
    - **Verdict:** corrected
    - **Action:** Feed the Waveshare board VCC from 5 V (VCC_5V_PERI or header pin 2/4), never from 3.3 V. Its logic stays 3.3 V, matching the Q6A header. At bring-up, measure DC at the IPEX centre under about a 150 ohm (about 20 mA) load and require at least 3.05 V; otherwise add a 5 V bias-tee with a DC block. Lower the expected backup hold time to about 1-2 weeks (model).
    - **Impact:** A marginal LNA bias reads as poor C/N0; an under-charged backup cell means cold starts sooner.
    - **Sources:**
      - https://files.waveshare.com/wiki/LC76G/manual/LC76G%20GNSS%20Module.pdf
      - https://www.waveshare.com/gps-external-antenna-d.htm
      - https://www.sii.co.jp/en/me/datasheets/ms-rechargeable/ms621fe
  5.
    - **Claim in stack:** C13/#26: pps-gpio built with DKMS for 6.18.2-4 (linux-headers 6.18.2-4 mirrored)
    - **Finding:** The live radxa-repo qcs6490-noble index (InRelease 24 Sep 2026) lists only linux-image/headers 7.0.11-7. The 6.18.2-4 image (68 MB) and headers (9 MB) are still downloadable from GitHub releases radxa-pkg/linux-qcom/6.18.2-4. The kernel was built with Debian gcc 12.2.0, with MODVERSIONS and MODULE_SIG off and zstd module compression.
    - **Verdict:** corrected
    - **Action:** Mirror linux-image and linux-headers 6.18.2-4-qcom from the GitHub release into the aptly repo now and pin them. Build the DKMS pps-gpio with gcc-12 (noble universe) via MAKE[0] CC=gcc-12, check modinfo vermagic, and record the source as radxa/kernel 559f4f9 drivers/pps/clients/pps-gpio.c.
    - **Impact:** If the release assets vanish, the held kernel and the PPS module cannot be rebuilt.
    - **Sources:**
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/main/binary-arm64/Packages
      - https://github.com/radxa-pkg/linux-qcom/releases/tag/6.18.2-4
      - https://github.com/radxa/kernel/tree/linux-6.18.2
  6.
    - **Claim in stack:** chrony: 'refclock PPS /dev/pps0 lock NMEA' with no NMEA refclock (stage 1/2 fix: add SHM 0 refid NMEA; stage 2: 'pairs only within 40 % of the pulse interval')
    - **Finding:** In chrony 4.5 refclock.c, PPS_LOCK_LIMIT = 0.4. A pulse is rejected when |ref_offset - pulse_offset| + NMEA root dispersion + average sample dispersion + pulse dispersion > 0.4 s; root delay is not part of the test. Model: the measured NMEA latency must be within about 0.3 s of the configured offset. An 80-150 ms latency passes with offset 0-0.15; the man-page value 0.5 and the gpsd howto placeholder 0.9999 fail.
    - **Verdict:** confirmed
    - **Action:** Use 'refclock SHM 0 refid NMEA offset <measured median, expect 0.05-0.15> delay 0.2 noselect' and 'refclock PPS /dev/pps-gnss lock NMEA refid PPS noselect'. The gate runs 'chronyc selectopts PPS -noselect' plus 'chronyc reselect' on accept and '+noselect' on any jam or spoof flag. Keep 'maxchange 5 1 -1', 'makestep 1 3' and 'rtcsync'.
    - **Impact:** PPS lock works, and system time is held back until the gate accepts it.
    - **Sources:**
      - https://gitlab.com/chrony/chrony/-/raw/4.5/refclock.c
      - https://chrony-project.org/doc/4.5/chrony.conf.html
      - https://chrony-project.org/doc/4.5/chronyc.html
  7.
    - **Claim in stack:** #80 / C23: choice between LC76G and MAX-M10S after the region is known (now: Europe); stage 1: 'store the MAX-M10S config in BBR/flash'
    - **Finding:** The MAX-M10S datasheet R08 lists no flash, only V_BCKP (28 uA in hardware backup mode). The Uputronics board keeps settings on a supercap. So baud rate and UBX NAV-STATUS output (spoofDetState) must be re-sent at every cold power-up, which needs UART6 TX, and the Q6A community has not yet shown TX working. The LC76G keeps its config in flash, EGNOS is supported, and Waveshare ships to the EU.
    - **Verdict:** corrected
    - **Action:** Region Europe: keep the LC76G as the default build. Add the MAX-M10S (3V, GBP 28.79, about $38.39) only for trips toward the Baltic, Finland, eastern Poland, the Black Sea or the eastern Mediterranean, and only after W1-2 proves UART6 TX. It then needs per-boot UBX-CFG-VALSET and a UBX NAV-STATUS reader in the location service.
    - **Impact:** Resolves C23 for this subsystem.
    - **Sources:**
      - https://content.u-blox.com/sites/default/files/MAX-M10S_DataSheet_UBX-20035208.pdf
      - https://store.uputronics.com/products/ublox-max-m8q-breakout-for-active-antennas
      - https://forum.radxa.com/t/uart-transmission/31422
  8.
    - **Claim in stack:** Band table: 'GNSS L1 + regional SBAS 1559-1610 MHz, reliable' with Waveshare 25346
    - **Finding:** Neither the Waveshare 25346 spec nor the Pi Hut listing names GLONASS, and no passband is published.
    - **Verdict:** corrected
    - **Action:** Reword the row to 'GPS/Galileo/BDS/QZSS L1 + EGNOS reliable; GLONASS G1 unverified with 25346'. Settle it on the bench with gpsd SKY (GLONASS PRNs 65-96, C/N0 within about 3 dB of GPS at similar elevation). Keep the magnetic base at least 30 cm from the IMU pack.
    - **Impact:** Small loss of availability if GLONASS is not tracked.
    - **Sources:**
      - https://www.waveshare.com/gps-external-antenna-d.htm
  9.
    - **Claim in stack:** #1093: 'Quectel regional lock behaviour (unknown)'
    - **Finding:** Quectel staff confirmed that the sibling LC86G 'will not be working in Russia'; the mechanism is undocumented and no LC76G report exists. There is also a Waveshare shipping embargo (Iran, Russia). The altitude limit is 10 km.
    - **Verdict:** corrected
    - **Action:** Reword to: functional region restriction confirmed for LC86G (Russia), assumed for LC76G; shipping embargo Iran/Russia; altitude limit 10 km. The gate labels 'fix lost with normal C/N0 and no jam flag' as a possible lockout or spoof, not an antenna fault.
    - **Impact:** Low in the EU.
    - **Sources:**
      - https://forums.quectel.com/t/lc86g-not-working-in-russia/57394
      - https://www.waveshare.com/lc76g-gnss-module.htm
  10.
    - **Claim in stack:** #7 gate: time within 120 s of the RTC
    - **Finding:** Model with a 20 ppm crystal and the -0.034 ppm/C^2 parabola: 120 s is exceeded after 69 days at 25 C, 41 days at 5 C and 22 days at -10 C storage. rtc-ds1307 reads m41t11 time checking only the CH bit, so a brown-out can leave a plausible but wrong time. rtcsync writes system time to rtc0 every 11 min while chrony is synchronised (RTC_SYSTOHC=y).
    - **Verdict:** corrected
    - **Action:** Use window = 120 s + 100 ppm x (RTC now - last gate-approved sync), with the stamp stored in /data. Outside the window mark time 'unverified'; reject only with a second indicator. Treat an RTC year earlier than the image build date as 'unset'. Write the last-trusted stamp only on gate-approved time. Keep PPS +noselect on any flag so chrony stops being synchronised and the kernel stops writing to rtc0 (model).
    - **Impact:** Prevents false spoof flags after storage and keeps a mid-session spoof from contaminating the RTC.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://github.com/radxa/kernel/blob/linux-6.18.2/drivers/rtc/rtc-ds1307.c
  11.
    - **Claim in stack:** D12: framed UART 115200 + CRC from the pack to Pico UART1; the BNO085-to-RP2040-Zero link is not specified
    - **Finding:** I2C to a BNO08x on an RP2040 fails above 100 kHz because of clock stretching. SPI is supported (1 MHz, mode 3, INT and RST required) and the Adafruit library implements it.
    - **Verdict:** confirmed
    - **Action:** Inside the pack use SPI0: SCK, MOSI, MISO, CS, INT, RST; tie P1 to 3V3; tie P0/WAKE to 3V3 (Adafruit wiring) or drive it from a GPIO held high through reset. Run Adafruit_BNO08x 1.2.7 at 1 MHz. Send quaternions (Game RV, plus Rotation Vector and raw magnetic field for soft checks) over the framed UART. Do the quaternion-to-az/el conversion on the Q6A with unit tests. Do not use the sh2 euler helpers, sh2_setReorientation or SparkFun getGravity(), and never enable RAW reports alone.
    - **Impact:** Removes the known BNO08x failure modes and the axis-swap defects.
    - **Sources:**
      - https://learn.adafruit.com/adafruit-9-dof-orientation-imu-fusion-breakout-bno085/arduino
      - https://community.sparkfun.com/t/bno086-and-rp2040-dont-work-faster-than-100-khz/67222
      - https://github.com/ceva-dsp/sh2/issues
  12.
    - **Claim in stack:** udev: UART6 -> /dev/gnss0; chrony uses /dev/pps0
    - **Finding:** Port numbering follows probe order (ttyHS1 or ttyHS2). PPS numbering also depends on registration order. No PTP-PPS source was found on this board (Ethernet is r8169 on PCIe), so this is insurance only.
    - **Verdict:** confirmed
    - **Action:** Keep KERNELS=='998000.serial' -> /dev/gnss0. Add SUBSYSTEM=='pps', ATTR{name}=='<pps-gpio node name>' -> /dev/pps-gnss and point chrony at it. Never hard-code ttyHS1 or pps0.
    - **Impact:** Low.
    - **Sources:**
      - https://forum.radxa.com/t/using-serial-ports-on-dragon-q6/30455
      - https://github.com/radxa/kernel/blob/linux-6.18.2/drivers/tty/serial/qcom_geni_serial.c
  13.
    - **Claim in stack:** gpsd: GPSD_OPTIONS='-n -p -s 115200'
    - **Finding:** -p still lets gpsd write; -b forbids all writes. gpsd sends commands only in reply to PMTK705/424, which the LC76G does not emit. Provisioning happens with gpsd stopped.
    - **Verdict:** confirmed
    - **Action:** Set GPSD_OPTIONS='-n -b -s 115200', DEVICES='/dev/gnss0', USBAUTO='false'. Provision from an ExecStartPre script or with gpsd stopped. AppArmor local rules (gpsd '/dev/ttyHS[0-9]* rw,', chronyd 'capability ipc_owner,') are needed only if /sys/kernel/security/lsm lists apparmor.
    - **Impact:** Low.
    - **Sources:**
      - https://gitlab.com/gpsd/gpsd/-/raw/release-3.25/man/gpsd.adoc
      - https://ports.ubuntu.com/ubuntu-ports/pool/main/g/gpsd/gpsd_3.25-3ubuntu3.2_arm64.deb
- **New risks:**
  - PPS mode persistence: PAIR513 does not save PAIR752. Unless the PQTMCFGPPS+PQTMSAVEPAR path is bench-proven, PPS behaviour after backup-cell depletion is the undocumented factory default.
  - The arduino-pico 6.3.0 default of 200 MHz for RP2040 boards puts the 8th harmonic at 1600 MHz, inside GLONASS G1 (model). The 12 MHz crystal harmonics land in L1/E1/B1 and at 1692/1704 MHz whatever clk_sys is.
  - LC76G board fed from 3.3 V instead of 5 V: the LDO drops out, antenna bias goes below the 25346's 3.0 V minimum, and the MS621FE is under-charged (model). Even at 5 V the bias is about 3.1 V at 20 mA (model).
  - MS621FE charge voltage is about 2.7-2.9 V (1N4148 + 470 ohm from 3V3), below SII's standard 3.1 V, so hold time is likely under the 17.6-day model. Expect about 1-2 weeks (model).
  - The held 6.18.2-4 kernel and headers are gone from the radxa-repo index and exist only as GitHub release assets. The DKMS build also has a compiler mismatch (kernel built with gcc 12.2.0; noble default is gcc 13).
  - MAX-M10S on the Uputronics breakout has no flash; its config lives in supercap-backed BBR, so the spoofing flags need working UART6 TX at every cold start. UART6 TX is unproven on the Q6A (forum 31422).
  - rtcsync plus a spoof accepted mid-session could write wrong time into rtc0, which the gate uses as its reference (model). Keep PPS +noselect on any flag and store last-trusted stamps only from gate-approved time.
  - The RS4C411ZAE path in rtc-ds1307 (m41t11) has no oscillator-fail check; after a weak cell or brown-out a plausible but wrong time is accepted by hctosys.
  - PPS_LOCK_LIMIT 0.4 s includes dispersion terms. The LC76G's periodic flash saves could delay NMEA by 300-400 ms (seen on the LC29H, thread 47717) and cause intermittent 'pulse ignored'. This is harmless only if the NMEA offset is set from a measured median.
  - Firmware updates need Windows QGNSS (V2.4/2.5, login-gated) and a RESET_N pulse within 20 s of the handshake. Any newer firmware than A04S is only available by email request, and its version string is unknown.
- **Refuted findings:**
  1.
    - **Finding:** Stage 1: '$PAIR513 saves PAIR752/PAIR391; read back after full power-off' (as the PPS persistence mechanism)
    - **Why:** Spec v1.4 PAIR513 note 3: PPS-related PAIR settings are not saved. The persistent route documented for PPS is PQTMCFGPPS + PQTMSAVEPAR.
  2.
    - **Finding:** Stage 2: 'TX-free fallback: provision once by USB-UART; saved settings survive in flash, so RX plus PPS is enough at runtime'
    - **Why:** For PPS gating this fails if PAIR752 is used (same note 3). It holds only if PQTMCFGPPS + PQTMSAVEPAR persistence passes the bench test.
  3.
    - **Finding:** Stage 1: 'The part name RS4C411 could not be found; change it to M41T11-compatible (part name unverified)'
    - **Why:** Radxa schematic v1.21, PDF page 16, names RS4C411ZAE with a 32.768 kHz 12.5 pF 20 ppm crystal.
  4.
    - **Finding:** Stage 1: 'The default 125 MHz system clock has no harmonics in any listed band' (as the pack's default)
    - **Why:** 125 MHz is the pico-sdk default only. The pack uses arduino-pico 6.3.0, whose default menu entry for waveshare_rp2040_zero is 200 MHz (harmonic at 1600 MHz).
  5.
    - **Finding:** Stage 2: 'a newer AB build probably exists'
    - **Why:** Thread 57735 shows only that Quectel emailed 'the latest FW version' for LC79H and LC76G together; nothing shows it is newer than A04S. Status: unknown.
  6.
    - **Finding:** Stage 1: MAX-M10S option 'store the config in BBR/flash'
    - **Why:** Datasheet R08 lists no flash on the MAX-M10S, only the V_BCKP backup domain; on the Uputronics board that is a supercap.
  7.
    - **Finding:** Stage 2: 'radxa-overlays issue #425 requested a pps-gpio overlay' (cited as Q6A evidence)
    - **Why:** #425 asks for Rock 3A/3C/5B (Rockchip). The conclusion that no pps-gpio overlay exists still holds, checked against the repo at e713889.
  8.
    - **Finding:** Stage 2 wording: the Waveshare wiki 'shows PPS as NC', implying the header PPS may be unusable
    - **Why:** The board schematic routes LC76G pin 4 (1PPS) straight to header pin 5. 'NC' appears only in the demo wiring tables.
  9.
    - **Finding:** Stage 2: EASA SIB 2022-02R4 dated 22 Jul 2026
    - **Why:** The PDF reads 'Issued: 03 July 2026'; 22 Jul 2026 is the republication of the editorial correction (C1). The content claims stand.
- **Corrected spec:** GNSS RECEIVER: Waveshare 24370 LC76G Multi-GNSS module (Quectel LC76G(AB)), $14.99.
  - Feed board VCC from 5 V; the onboard RT9193-33 makes 3V3, so logic is 3.3 V.
  - Header MX1.25 8-pin: 1 VCC, 2 GND, 3 TXD to Q6A pin 18 (UART6 RX), 4 RXD from pin 16 (UART6 TX), 5 1PPS to pin 7 (GPIO96, wire <=20 cm), 6 RESET (active low) to a spare MCP23017 #1 output via a 2N7002 open-drain, 7/8 SDA/SCL unused.
  - Backup: onboard MS621FE.
  - Antenna: Waveshare 25346 L1+L5 active, $16.99, via an IPEX to SMA-K bulkhead pigtail to P7. Bias comes from LC76G VCC_RF through 10 ohm, about 3.1 V at 20 mA (model). GLONASS support is unverified. Keep the magnetic base at least 30 cm from the IMU pack.
  
  ONE-TIME PROVISIONING (gpsd stopped; UART6 or a USB-UART):
  1. $PQTMVERNO*58 (log it).
  2. $PQTMCFGPPS,W,1,1,100,3,0,0*70, then $PQTMSAVEPAR*5A; check with $PQTMCFGPPS,R,1*6A.
  3. $PAIR391,1*2C, $PAIR410,1*22, $PAIR400,2*20, then $PAIR513*3D (1 Hz, so no PAIR382/003 needed). Read back with $PAIR401*3F and $PAIR411*3E.
  4. Optional: $PQTMCFGMSGRATE,W,PQTMJAMMINGSTATUS,1,1*11, then $PQTMSAVEPAR*5A.
  Rules: keep EPOC on. Never send $PAIR007. No $PAIR753 timing modes and no stationary mode. For spoof recovery use $PAIR006*3C or a RESET pulse. No field firmware updates. Archive spec V1.5 and the EASY/EPOC note from quectel.com.
  
  KERNEL AND DEVICE TREE:
  - Held linux-image/headers 6.18.2-4-qcom (CONFIG_PPS=y, PPS_CLIENT_GPIO unset, MODULE_SIG off), mirrored from github.com/radxa-pkg/linux-qcom/releases/tag/6.18.2-4.
  - DKMS pps-gpio built from radxa/kernel 559f4f9 drivers/pps/clients/pps-gpio.c with CC=gcc-12.
  - lab-q6a.dtso: the Radxa uart6 overlay content (spi6/i2c6 disabled, qup_uart6_tx/rx, okay) plus a node compatible 'pps-gpio' with gpios = <&tlmm 96 GPIO_ACTIVE_HIGH>.
  - UEFI: QUPV3 SE6 mode set to UART if listed.
  - udev: KERNELS=='998000.serial' -> /dev/gnss0; SUBSYSTEM=='pps', ATTR{name}=='<node>' -> /dev/pps-gnss.
  - Route A (GPIO v2 ioctl with GPIO_V2_LINE_FLAG_EVENT_CLOCK_REALTIME, bit 11) is fallback only; never run it together with pps-gpio.
  
  GPSD 3.25-3ubuntu3.2: DEVICES='/dev/gnss0', GPSD_OPTIONS='-n -b -s 115200', USBAUTO='false'.
  
  CHRONY 4.5-1ubuntu4.2 (noble defaults kept: pools, makestep 1 3, rtcsync), plus:
  - refclock SHM 0 refid NMEA offset <measured median, about 0.05-0.15> delay 0.2 noselect
  - refclock PPS /dev/pps-gnss lock NMEA refid PPS noselect
  - maxchange 5 1 -1
  Gate control: on accept, 'chronyc selectopts PPS -noselect' then 'chronyc reselect'; on a jam or spoof flag, '+noselect'. Restart chronyd only after a gate re-accept that follows a spoof.
  AppArmor local rules only if /sys/kernel/security/lsm lists apparmor.
  
  RTC: on-board RS4C411ZAE (st,m41t11 binding, i2c10 0x68, rtc0, 20 ppm crystal), primary CR2032 with a pre-wired 2-pin 1.25 mm plug in J11 (check polarity), util-linux-extra for hwclock.
  
  LOCATION GATE:
  - Accept: 3D fix with at least 6 SV. First run: at least 8 SV and within 50 m for 5 min.
  - Time window: 120 s + 100 ppm x days since the last gate-approved sync. Outside it, mark 'unverified'; reject only with a second indicator. An RTC year earlier than the image build date means 'unset'.
  - TLE-epoch date window; a jump over 100 km needs confirmation.
  - Jam: PAIRSPF or PQTMJAMMINGSTATUS of 2 or more sets PPS +noselect.
  - Soft indicators, never hard rejects: C/N0 uniformity (excluding QZSS); |B|/dip against WMM (clean magnetic site only, catches errors of several hundred km or more); an optional DCF77/MSF time cross-check; 'fix lost with C/N0 normal' is labelled possible lockout or spoof.
  - Fallbacks: last good fix with its age, manual lat/lon or Maidenhead. No city table. Admin-0 polygons for jurisdiction only. Exports rounded to 0.1 deg or a 4-character locator.
  
  WMM: pygeomag 1.1.0 with the WMM2025 COF (valid to 31 Dec 2029) in the venv. Show a compass warning in the blackout and caution zones (H thresholds per the WMM technical report; not re-fetched).
  
  IMU PACK:
  - Adafruit 4754 BNO085 ($29.50) on SPI0 of a Waveshare RP2040-Zero 20187 ($3.99-4.99): SCK, MOSI(DI), MISO(SDA), CS, INT, RST; P1 to 3V3; P0/WAKE to 3V3 or a GPIO held high through reset.
  - Firmware: arduino-pico 6.3.0, FQBN freq=125 (explicit), Adafruit_BNO08x 1.2.7 at SPI 1 MHz.
  - Reports: Game RV quaternion, Gravity, Rotation Vector and magnetic field.
  - Link: framed UART 115200 with CRC and a clk_sys field, to Pico UART1 GP8/GP9. Metal pack, 31/43 ferrite, at least 30 cm behind active elements and the GNSS antenna.
  
  POINTING: Skyfield 1.55 and sgp4 2.27 in a venv.
  - Elevation from gravity; azimuth from a sun sighting plus Game RV.
  - Re-sight prompt every 15-20 min (0.5 deg/min drift model).
  - Own quaternion-to-az/el code with unit tests.
  - Drop frames whose |g| is not about 1 g, or that show a stuck X=Y=0 pattern.
  - Magnetometer heading only away from steel (datasheet: RV about 5 deg, GeoRV about 10 deg in practice).
  - Heading is shown live only and never logged.
  
  OPTION: Uputronics MAX-M10S 3V (GBP 28.79, about $38.39) for the Baltic or eastern borders, only after UART6 TX is proven. It needs per-boot UBX config and a NAV-STATUS reader.
- **Bench tests:**
  - UART6 bring-up (W1-2): dmesg has no 'Invalid FW loaded' or 'UART firmware load failed'; record the UEFI QUPV3 SE6 mode; pins 16-18 TX-to-RX loopback at 115200 with 1e5 bytes and zero errors; then the LC76G answers $PQTMVERNO*58.
  - PPS path: debugfs pinmux-pins shows gpio96 owned only by pps-gpio; 'ppstest /dev/pps-gnss' shows 1 Hz asserts only with a 3D fix. Disconnect the antenna: pulses must stop within the 3D-loss time, with none free-running.
  - PPS persistence (decides the TX-free fallback): provision with PQTMCFGPPS + PQTMSAVEPAR + PAIR513; remove VCC and drain or remove the MS621FE (or short V_BAT through 1 kOhm for 1 min); power up; $PQTMCFGPPS,R,1*6A must return mode 3; PAIRSPF output must be present; $PAIR401*3F must return 2.
  - NMEA latency and chrony lock: log the PPS-to-first-sentence delay for 24 h with a logic analyser or chrony refclock logs. Set the NMEA offset to the median. 'chronyc sources' shows PPS '*' after the gate's selectopts; count 'pulse ignored' events (target under 1 %).
  - Antenna bias: with VCC = 5 V, the IPEX centre pin under a 150 ohm load reads at least 3.05 V. Repeat with VCC = 3.3 V to document the drop.
  - GLONASS with the 25346: 30 min of open sky; gpsd SKY shows GLONASS PRNs 65-96 used, with mean C/N0 within 3 dB of GPS satellites at similar elevation. Otherwise mark GLONASS unsupported in the band table.
  - TTFF: 10 cold starts ($PAIR006*3C) outdoors, median 60 s or less; hot starts 5 s or less. Then leave the board unpowered for 3, 7 and 14 days and record hot vs cold start to measure the real MS621FE hold time (model 9-18 days).
  - RTC: after 10+ min unpowered, 'dmesg | grep -i hctosys' and 'hwclock -r -f /dev/rtc0'. Measure drift over 7 days at room temperature and after a 24 h fridge soak; confirm it stays within the 100 ppm window growth.
  - Gate drill (conducted-only rule: no GNSS simulator on air, so replay recorded NMEA with gpsfake): an RTC 200 s off after 30 days of storage gives 'unverified' and no reject; a jam flag sets PPS +noselect; a 150 km jump asks for confirmation.
  - IMU pack: 100 cold boots with SPI init passing every time; clk_sys reported as 125 MHz; Game RV drift static for 20 min and on a turntable; quaternion-to-az/el unit tests flat-north and at 90 deg about each axis; 1e6-frame UART CRC test.
  - RF A/B (pack and display on/off): GNSS C/N0 change of 1 dB-Hz or less; L-band noise floor at 1692/1704 MHz; repeat with the pack deliberately at 200 MHz to confirm or refute the 1600 MHz spur.
  - Platform: 'cat /sys/kernel/security/lsm' has no apparmor (otherwise ship the two local rules); DKMS pps-gpio built with gcc-12 has a vermagic matching 6.18.2-4-qcom; the aptly mirror holds the image and headers debs.
- **Confidence:** medium

