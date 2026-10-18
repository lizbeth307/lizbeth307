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

