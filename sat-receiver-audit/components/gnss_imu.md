# Gnss imu: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_45d278c2-004`_

- **Component:** GNSS receiver + IMU/compass for location, timing and on-screen antenna pointing
- **Current pick assessment:** The picks are in the right class, but the prices and assumptions need fixing.
  (1) u-blox M10 is a good GNSS choice: 30 ns RMS timepulse, 25 mW tracking, a native UBX driver in gpsd, and jamming/spoofing reporting. The $15-20 figure only buys a bare module or a drone puck, and those usually have no PPS pin. M10 breakouts that do expose PPS cost $46-52 in the US (SparkFun MAX-M10S/SAM-M10Q) and 4,550-6,170 UAH (~$100-137) on Prom.ua.
  (2) ATGM336H works as a budget part: it has a PPS pin and outputs NMEA at 283-520 UAH. But the 5N-31 tracks GPS+BDS only, it is configured with proprietary CASIC commands, and I found no published PPS accuracy.
  (3) BNO085 is still a sensible IMU. The datasheet gives Rotation Vector 2.0 deg static / 3.5 deg dynamic and Game RV drift of 0.5 deg/min. It is in stock at Adafruit for $29.50, and BNO086 is a pin- and software-compatible drop-in. Caveats:
  - Its I2C master must support clock stretching. This is unverified on the Q6A's Qualcomm GENI I2C behind the header level translators.
  - Linux has no kernel driver, so you need a user-space SH-2 driver.
  - UART-RVC mode disables magnetometer calibration.
  - Inside a handheld, the biggest heading error comes from the battery, fan and DC currents, not from the sensor.
  (4) The LimeSDR Micro GNSS variant (+$50) does NOT replace a separate GNSS module today. Its Antenova M10578-A3 (MediaTek MT3333) talks only to the on-board LA9310 MCU. In the firmware as of 9 Oct 2026 there is no NMEA pass-through and no GPSDO loop: the VCTCXO DAC loads from an EEPROM value, and the host can set it. Crowd Supply says GPSDO 'may' come but 'is not guaranteed'.
  Also note: the LimeSDR Micro is now $249 basic / $299 GNSS (the $199 early-bird price has ended), and new orders ship Dec 15, 2026.
- **Alternatives:**
  1.
    - **Name:** Quectel LC76G (Waveshare 24370 module board)
    - **Key specs:** Module 10.1x9.7x2.4 mm; GPS/GLONASS/Galileo/BDS/QZSS L1, 47 ch, -166 dBm tracking; 1PPS 30 ns RMS; LC76G(AB) 36 mA @3.3 V (PA low-power variant 10 mA); UART 9600-921600 bps (default 115200, up to 10 Hz) + I2C 400 kbps; NMEA 0183 v4.10 + PAIR/PQTM. Waveshare board runs on 3.3/5 V and has a PPS pin, an MS621FE backup cell, an active ceramic antenna and an MX1.25 8-pin cable.
    - **Price:** $14.99 (Waveshare); Prom.ua 1,044-1,421 UAH (~$23-32 at 44.89 UAH/USD)
    - **Pros:** Cheapest well-documented board that combines PPS, an active antenna and a backup cell. PPS spec (30 ns RMS) equals the M10. UART or I2C. Several Ukrainian sellers stock it. On a Pi, chrony showed <100 ns RMS once a host-OS problem was fixed.
    - **Cons:** About 4x the power of the M10 (119 mW vs 25 mW; still negligible here). gpsd handles it only as generic NMEA, configured with PAIR commands. PPS stops about 45 min after losing fix unless 'PPS always output' is enabled. Waveshare labels the PPS pin as a 'status indicator'. Spoofing reporting is not documented.
    - **Availability:** In stock at Waveshare and at Prom.ua sellers (RoboTrade, kabelok, bazarok), Oct 2026.
    - **Q6a compatibility:** 3.3 V logic matches the header. Use UART6 (pins 16/18) and wire PPS to a free GPIO through a pps-gpio overlay. Works with gpsd NMEA + chrony.
    - **Sources:**
      - https://quectel.com/content/uploads/2024/03/Quectel_LC76G_Series_GNSS_Specification_V1.1-1-1.pdf
      - https://www.waveshare.com/LC76G-GNSS-Module.htm
      - https://forums.quectel.com/t/gnss-lc76g-1-pss-configuration/45880
      - https://forums.quectel.com/t/significant-periodic-1pps-noise-with-lc76g-module/57109
      - https://prom.ua/ua/search?search_term=LC76G
  2.
    - **Name:** u-blox MAX-M10S (SparkFun GNSS Receiver Breakout MAX-M10S, Qwiic)
    - **Key specs:** M10, module 9.7x10.1x2.5 mm; 25 mW continuous tracking; timepulse 30 ns RMS / 60 ns 99%, configurable 0.25 Hz-10 MHz; 4 GNSS supported (3 concurrent in current firmware). SparkFun board: SMA, PPS pin + LED, MS621FE backup cell (keeps config/orbits ~2 weeks), UART 38400 default + I2C 0x42, 3.3 V, ~44x30 mm.
    - **Price:** $45.95 SparkFun (backorder); GBP 46.20 Pi Hut; Prom.ua 4,550 UAH (~$101); bare module $10.39-12.72 (Mouser), ~$10.7 (LCSC)
    - **Pros:** First-class gpsd UBX driver plus ubxtool. Lowest power. Jamming and spoofing detection with reporting, which is useful under Ukrainian EW conditions. Mature ecosystem.
    - **Cons:** MAX-M10S has no flash, so configuration lives in battery-backed RAM and the backup cell is required. Breakouts are expensive in Ukraine. The cheap M10 drone pucks sold locally usually lack a PPS pin. The newer MAX-M10N (flash-upgradable, SPG 5.30, better spoofing detection) has no hobby breakout found yet.
    - **Availability:** SparkFun backordered. One Prom.ua listing. EU retailers have intermittent stock.
    - **Q6a compatibility:** 3.3 V. UART6 + PPS GPIO, or I2C on I2C0/I2C2. Best gpsd support of all the options.
    - **Sources:**
      - https://content.u-blox.com/sites/default/files/MAX-M10S_DataSheet_UBX-20035208.pdf
      - https://www.sparkfun.com/sparkfun-gnss-receiver-breakout-max-m10s-qwiic.html
      - https://docs.sparkfun.com/SparkFun_u-blox_MAX-M10S/hardware_overview/
      - https://content.u-blox.com/sites/default/files/MAX-M10_ProductSummary_UBX-20017987.pdf
      - https://www.cnx-software.com/2025/10/24/u-blox-max-m10n-gnss-module-supports-low-energy-accurate-positioning-leap-mode-firmware-upgrades/
      - https://prom.ua/ua/search?search_term=u-blox%20M10
  3.
    - **Name:** u-blox SAM-M10Q (SparkFun GPS-21834 / Matek SAM-M10Q drone board)
    - **Key specs:** M10 with integrated antenna; timepulse 30 ns RMS. SparkFun board has a PPS through-hole, a 3 V/1 mAh backup cell, Qwiic, UART/I2C, 3.3 V.
    - **Price:** $51.50 SparkFun; Prom.ua SparkFun 5,145-6,169 UAH (~$115-137); Matek SAM-M10Q 1,782-2,684 UAH (~$40-60)
    - **Pros:** No external antenna or coax to fit. Can be mounted flush on the top of the case.
    - **Cons:** The integrated antenna sits close to the Q6A, LimeSDR and DC-DC noise. Expensive. Matek boards are drone-oriented, and I could not verify whether they expose a PPS pin (they have only a PPS LED).
    - **Availability:** In stock on Prom.ua (Matek and SparkFun).
    - **Q6a compatibility:** Same as MAX-M10S.
    - **Sources:**
      - https://www.sparkfun.com/sparkfun-gps-breakout-chip-antenna-sam-m10q-qwiic.html
      - https://rcdrone.top/ja/products/20x20mm-matek-m10q-5883-gnss-gps-module
      - https://prom.ua/ua/search?search_term=SAM-M10Q
  4.
    - **Name:** Quectel LC29H(AA) dual-band L1+L5
    - **Key specs:** 16.0x12.2x2.4 mm; GPS/Galileo/QZSS L1+L5, BDS B1/B2a, GLONASS L1; 1 m CEP; 1PPS <100 ns; 43 mA tracking @3.3 V; I/O 2.8 V; UART up to 10 Hz; NMEA/PAIR/PQTM (the BS variant outputs proprietary messages only).
    - **Price:** Prom.ua module 1,900-2,151 UAH (~$42-48); Waveshare HAT $39.99 (Prom.ua 3,691 UAH); L1+L5 active antenna ~2,000 UAH
    - **Pros:** Dual-band gives better multipath and jamming resilience. RTK variants (DA/EA) are available.
    - **Cons:** Overkill for satellite pass prediction. Needs a larger, pricier L1+L5 antenna. About 6x the M10's power. PPS spec is worse than M10/LC76G. 2.8 V I/O needs care.
    - **Availability:** Several Prom.ua sellers; Waveshare.
    - **Q6a compatibility:** Use a translator (or the Waveshare HAT) for the 2.8 V I/O. Works with gpsd as NMEA.
    - **Sources:**
      - https://img.dfrobot.com.cn/wiki/5ea64bf6cf1d8c7738ad2881/53d6e4d5dd5f02611860cbafb2f69405.pdf
      - https://www.waveshare.com/lc29h-gps-hat.htm?sku=25278
      - https://forums.quectel.com/t/use-lc29h-bs-as-da/32359
      - https://prom.ua/ua/search?search_term=LC29H
  5.
    - **Name:** ATGM336H-5N31 (Zhongke Weike AT6558)
    - **Key specs:** GPS+BDS (the 5N-7x variants add other constellations); PPS pin with rising edge aligned to UTC (no jitter figure published); ~30 mA @3.3 V (distributor figure); UART NMEA; boards are commonly 5V/GND/TX/RX/PPS with a patch antenna.
    - **Price:** Prom.ua 491-520 UAH with antenna (~$11-12), 283 UAH without (~$6.3); ElectroDragon $8.50; LCSC ~$1.95 @1k
    - **Pros:** Cheapest option with PPS. Available in Ukraine today. gpsd reads its NMEA without trouble.
    - **Cons:** Only 2 constellations on the 5N-31. No published timing accuracy. Proprietary CASIC configuration. Weaker sensitivity than M10. No spoofing/jamming reporting.
    - **Availability:** Widely stocked on Prom.ua and AliExpress.
    - **Q6a compatibility:** Check the board's I/O level (most are 3.3 V even when fed 5 V). UART6 + PPS GPIO.
    - **Sources:**
      - https://www.electrodragon.com/product/gnss-module-atgm336h/
      - https://www.tinytronics.nl/en/communication-and-signals/wireless/gps/modules/atgm336h-gps-module
      - https://wiki.millerjs.org/_media/atgm336h-5n_datasheet.pdf
      - https://prom.ua/ua/search?search_term=ATGM336H
  6.
    - **Name:** SpeedyBee BZGNSS BZ-181 (u-blox M10 drone puck)
    - **Key specs:** u-blox M10, 18x18x8 mm ceramic patch, 5 V supply, UBX/NMEA, 115200 baud, 1-10 Hz. No PPS pin documented.
    - **Price:** Prom.ua 560 UAH (~$12.5, in stock); GBP 19.99 UK
    - **Pros:** Cheapest genuine u-blox M10 sold in Ukraine. Native UBX in gpsd. Antenna included.
    - **Cons:** No documented PPS, so time is NMEA-only (~10-100 ms). 5 V supply. Drone form factor.
    - **Availability:** In stock on Prom.ua (TopWin Technology).
    - **Q6a compatibility:** UART only; check the TX level. Good fit if PPS is not wanted.
    - **Sources:**
      - https://www.flyingtech.co.uk/product/speedybee-bzgnss-bz-181-gps
      - https://prom.ua/ua/search?search_term=u-blox%20M10
  7.
    - **Name:** LimeSDR Micro M.2 GNSS variant (Antenova M10578-A3 on board)
    - **Key specs:** M10578-A3: MediaTek MT3333, 9x9x1.8 mm, 0.5 ppm TCXO, 3 GNSS concurrently, MHF4 X5 active antenna connector. GNSS_1PPS goes to the LA9310 MCU and the UART goes to the LA9310. Rakon VCTCXO 30.72 MHz: +/-1 ppm calibration, +/-50 ppb over temperature, +/-5 ppm tuning range via 16-bit DAC. External 10-52 MHz reference in (J4) and PPS in/out (J5, M.2 pins 46/48).
    - **Price:** $299 vs $249 basic (+$50); new orders ship Dec 15, 2026
    - **Pros:** No extra board or UART needed. The hardware path to discipline the VCTCXO and timestamp samples exists.
    - **Cons:** Firmware (LimeSDR-Micro_FW, commit of 9 Oct 2026) has no NMEA forwarding and no GPSDO loop; the XO DAC comes from EEPROM. Crowd Supply says GPSDO support is not guaranteed. The host gets neither position nor PPS. Older MT3333 receiver.
    - **Availability:** Pre-order on Crowd Supply, fulfilled by Mouser.
    - **Q6a compatibility:** Nothing reaches the Q6A except through future firmware/LimeSuiteNG. Does not replace a host-side GNSS module.
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/clock.html
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/clock.html
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/overview.html
      - https://github.com/myriadrf/LimeSDR-Micro_FW
      - https://www.digikey.it/en/products/detail/antenova/M10578-A3/5959794
  8.
    - **Name:** CEVA BNO085 (Adafruit 4754 / GY-BNO085 clones)
    - **Key specs:** 9-axis SiP with Cortex-M0+ SH-2 fusion. Rotation Vector 2.0 deg static / 3.5 deg dynamic; Geomagnetic RV 3.0/4.5 deg; Game RV drift 0.5 deg/min; gravity 1.5 deg. Interfaces: I2C (master must support clock stretching), SPI, UART-SHTP, and UART-RVC (115200 baud, 100 Hz).
    - **Price:** Adafruit $29.50 (in stock); Prom.ua GY-BNO085 2,121 UAH (~$47), other BNO085 boards 2,295-3,401 UAH (~$51-76); AliExpress price not verified
    - **Pros:** Turn-key fusion with dynamic calibration, accuracy flags and save-DCD. Accuracy is ample for Yagi/helix beamwidths. Mature Arduino libraries.
    - **Cons:** No Linux kernel driver (the staging driver was not merged). Clock-stretching risk on non-Broadcom I2C is unverified on Qualcomm. UART-RVC disables magnetometer calibration. Magnetometer calibration is opaque. Clone authenticity unverified.
    - **Availability:** Adafruit in stock. Prom.ua has several sellers. Mouser lists incoming stock.
    - **Q6a compatibility:** 3.3 V. Prefer SPI or UART-SHTP, or an RP2040 USB bridge. Direct I2C on I2C0/I2C2 only after testing.
    - **Sources:**
      - https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf
      - https://www.adafruit.com/product/4754
      - https://lore.kernel.org/all/YqsMmmqhN3WEx1Lq@kroah.com/T/
      - https://prom.ua/ua/search?search_term=BNO085
  9.
    - **Name:** CEVA BNO086 (SparkFun VR IMU Breakout SEN-22857)
    - **Key specs:** Drop-in for BNO085 (same pinout and software) with 14-bit accelerometer fusion, lower idle power and Interactive Calibration. Qwiic.
    - **Price:** SparkFun $34.95; Prom.ua 3,595-4,060 UAH (~$80-90)
    - **Pros:** Newer part in the same family with easier calibration. DigiKey has shown stock.
    - **Cons:** Costs more in Ukraine. Same Linux and magnetic caveats as BNO085.
    - **Availability:** SparkFun (stock varies); Prom.ua in stock.
    - **Q6a compatibility:** Same as BNO085.
    - **Sources:**
      - https://www.sparkfun.com/sparkfun-vr-imu-breakout-bno086-qwiic.html
      - https://www.digikey.com/en/product-highlight/h/hillcrest-labs/bno080-imu
      - https://prom.ua/ua/search?search_term=BNO086
  10.
    - **Name:** TDK ICM-20948 (+AK09916 magnetometer)
    - **Key specs:** 9-axis with DMP. Fusion done on the host (e.g. x-io Fusion/imufusion). I2C/SPI.
    - **Price:** Adafruit 4554 $19.95; SparkFun $21.95; Prom.ua generic 598-617 UAH (~$13-14), Adafruit 1,585-1,926 UAH
    - **Pros:** Cheap and plentiful. Plain I2C with no clock stretching.
    - **Cons:** TDK's product page now lists it as EOL. Mediocre magnetometer. You write and calibrate the fusion yourself.
    - **Availability:** Modules still plentiful in Ukraine. The chip is EOL.
    - **Q6a compatibility:** Direct on I2C0/I2C2 at 3.3 V; Python with smbus2.
    - **Sources:**
      - https://invensense.tdk.com/products/motion-tracking/9-axis/icm-20948/
      - https://www.adafruit.com/product/4554
      - https://www.sparkfun.com/sparkfun-9dof-imu-breakout-icm-20948-qwiic.html
      - https://prom.ua/ua/search?search_term=ICM-20948
  11.
    - **Name:** ST LSM6DSV16X (or ISM330DHCX) + Memsic MMC5983MA, host fusion with x-io Fusion
    - **Key specs:** LSM6DSV16X: 6-axis with on-chip SFLP game rotation vector. MMC5983MA: 18-bit, +/-8 G, 0.4 mG RMS noise, SET/RESET degauss, SparkFun claims +/-0.5 deg heading at sensor level. One-board option: SparkFun 9DoF ISM330DHCX+MMC5983MA (SEN-19895). LIS3MDL is an alternative magnetometer (price not verified).
    - **Price:** SparkFun LSM6DSV16X $24.54 + MMC5983MA ~$18.50 (Mouser); SEN-19895 $45.74. Prom.ua: LSM6DSV16X 2,330-2,701 UAH, MMC5983MA 1,610-2,520 UAH, SEN-19895 4,295-5,338 UAH
    - **Pros:** Best magnetometer of the group. Transparent ellipsoid calibration and magnetic-rejection settings in imufusion. Plain I2C.
    - **Cons:** Costs the most. You maintain the fusion and calibration code. Real heading accuracy is still limited by magnetic interference.
    - **Availability:** SparkFun and Prom.ua in stock.
    - **Q6a compatibility:** Direct on I2C0/I2C2; user-space Python with smbus2 + imufusion.
    - **Sources:**
      - https://learn.sparkfun.com/tutorials/qwiic-micro-magnetometer---mmc5983ma-hookup-guide/all
      - https://www.sparkfun.com/sparkfun-9dof-imu-breakout-ism330dhcx-mmc5983ma-qwiic.html
      - https://www.sparkfun.com/sparkfun-6dof-imu-breakout-lsm6dsv16x-qwiic.html
      - https://community.st.com/mems-and-sensors-62/how-lsm6dsv16x-enables-sensor-fusion-low-power-sflp-algorithm-120280
      - https://github.com/xioTechnologies/Fusion
      - https://prom.ua/ua/search?search_term=MMC5983MA
  12.
    - **Name:** Bosch BMI270 + BMM350 (DFRobot Fermion SEN0622)
    - **Key specs:** BMM350 TMR magnetometer, +/-2000 uT, I2C. BMI270 is a 6-axis IMU. Fusion runs on the host (Bosch BSX is closed).
    - **Price:** BMM350 Fermion: DigiKey EUR 5.91 / GBP 5.16; Prom.ua 615 UAH (~$13.7), Gravity version 845 UAH. BMI270 breakout price in UA not verified (bare chip 386 UAH).
    - **Pros:** Cheap modern magnetometer that is easy to find in Ukraine.
    - **Cons:** Two boards plus custom fusion. Less hobby documentation. BMI270 breakout availability not verified.
    - **Availability:** BMM350 boards in stock on Prom.ua.
    - **Q6a compatibility:** I2C0/I2C2, user-space Python.
    - **Sources:**
      - https://www.digikey.co.uk/en/products/detail/dfrobot/SEN0622/26460569
      - https://prom.ua/ua/search?search_term=BMM350
- **Recommended:**
  - **Name:** Quectel LC76G (Waveshare 24370) with PPS on the Q6A, plus a BNO086 (or BNO085) in an antenna-mounted 'pointing puck' read through an RP2040-Zero USB bridge
  - **Why:** GNSS:
  - The LC76G gives the same 30 ns RMS PPS as the u-blox M10.
  - The board includes an active patch antenna, a backup cell and both UART and I2C, for $14.99 direct or ~1,050-1,400 UAH locally. An M10 breakout with PPS costs ~4,550 UAH in Ukraine.
  - Location and time only need 1-2 m and well under 1 s; PPS just improves IQ timestamps. Dual-band LC29H and the LimeSDR GNSS variant add cost without adding host functions.
  - If you can get a MAX-M10S breakout with PPS for ≤$30 (e.g. from the EU), take it instead: native UBX in gpsd and spoofing flags.
  
  IMU:
  - The BNO08x does fusion and calibration on-chip. Its 2.0-3.5 deg spec is well inside Yagi/helix beamwidths (30-60 deg), and the dish is fine-peaked on the beacon anyway.
  - Put it in a small puck on the antenna boom, not in the case. The magnetometer must point with the antenna and stay away from the 21700 steel cans, fan magnet and multi-amp DC leads. Current-dependent fields cannot be calibrated out.
  - An RP2040-Zero (125-220 UAH) running SparkFun's SH-2 Arduino library sends quaternion and accuracy over USB-CDC. This avoids the unverified clock stretching on Qualcomm GENI I2C, the lack of a Linux BNO08x driver, and long-cable I2C problems.
  - Choose the BNO086 if the price is close; the BNO085 is fine.
  - **Price:** ~$50-55 buying direct (LC76G $14.99 + Adafruit BNO085 $29.50 or SparkFun BNO086 $34.95 + RP2040-Zero ~$3-5); ~3,300-4,000 UAH (~$75-90) on Prom.ua at 44.89 UAH/USD
  - **Sources:**
    - https://quectel.com/content/uploads/2024/03/Quectel_LC76G_Series_GNSS_Specification_V1.1-1-1.pdf
    - https://www.waveshare.com/LC76G-GNSS-Module.htm
    - https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf
    - https://www.adafruit.com/product/4754
    - https://www.sparkfun.com/sparkfun-vr-imu-breakout-bno086-qwiic.html
    - https://github.com/myriadrf/LimeSDR-Micro_FW
    - https://ardupilot.org/copter/docs/common-magnetic-interference.html
    - https://prom.ua/ua/search?search_term=RP2040-Zero
    - https://minfin.com.ua/ua/currency/nbu/
- **Budget option:**
  - **Name:** ATGM336H-5N31 (with PPS and patch antenna) + generic ICM-20948 module, with fusion done on the Q6A by x-io Fusion (imufusion)
  - **Why:** This is the cheapest combination that still has a PPS pin and a 9-axis sensor, and both parts are in stock in Ukraine. gpsd reads NMEA from the ATGM336H and chrony uses its PPS. The ICM-20948 is plain I2C (no clock stretching), and imufusion provides magnetic rejection and a transparent calibration. Trade-offs: the ATGM336H tracks only GPS+BDS and has no published timing spec, and the ICM-20948 is EOL at TDK (modules are still plentiful). If you don't need PPS, swap the GNSS for a SpeedyBee BZ-181 (genuine u-blox M10, 560 UAH).
  - **Price:** ~1,090-1,140 UAH (~$24-25) on Prom.ua (ATGM336H 491-520 UAH + ICM-20948 598-617 UAH)
- **Risks:**
  - GNSS spoofing and jamming by EW in Ukraine: Ukraine's General Staff has said its counter-drone EW spoofs GPS, and phones in Kyiv have shown wrong time zones. Sanity-check the fix against a saved home QTH and the system clock, allow manual QTH, keep NTP as a chrony fallback, and prefer u-blox if you want spoofing flags.
  - Q6A bus enablement: the patches that enable all QUP serial engines for the 40-pin header went to LKML in Nov 2025. Not verified: whether the current Radxa Ubuntu image exposes UART6/I2C0/I2C2, and whether its kernel has CONFIG_PPS_CLIENT_GPIO for a pps-gpio overlay. You may need a custom device-tree overlay.
  - UART6 (pins 16/18) and I2C6 (pins 3/5) share QUP SE6, and only one protocol can run per serial engine. Pins 8/10 are the debug console UART.
  - BNO08x over direct I2C needs clock stretching. This is unverified on Qualcomm GENI I2C behind the header's UM3204H/UM3304 level translators, so use SPI, UART-SHTP or the RP2040 bridge. Do not use UART-RVC for absolute azimuth: the datasheet says magnetometer calibration is off in RVC mode.
  - Magnetic interference: Kyiv's horizontal field is about 19.4 uT, so 1 uT of stray field is about 3 deg of heading error. A 4 A lead at 5 cm adds ~16 uT (calculated). Steel tape-measure Yagi elements, steel camping dishes, 21700 cans and the fan magnet all distort the field. Current-dependent errors cannot be calibrated out.
  - AliExpress or no-name GY-BNO085 boards may be clones or relabelled parts. I could not verify authenticity or AliExpress prices.
  - LC76G PPS stops about 45 min after fix loss unless 'PPS always output' is enabled. MAX-M10S has no flash, so its config is lost without the backup cell.
  - LimeSDR Micro: GPSDO and NMEA support is not in the firmware and is 'not guaranteed'. New orders ship Dec 15, 2026, at $249/$299 rather than the $199 early-bird price.
  - ICM-20948 is EOL at TDK, so long-term supply of that budget path is uncertain.
  - Prom.ua prices were scraped on 17 Oct 2026 and converted at the NBU rate of 44.89 UAH/USD. Stock and prices change daily.
- **Integration notes:**
  - Header voltage: the Q6A 40-pin header signals are level-translated to 3.3 V (UM3204H/UM3304, VCC_1V8 to VCC_3V3, schematic v1.21), so 3.3 V GNSS and IMU boards connect directly. Leave pins 8/10 alone: they are the DBG_UART console.
  - GNSS wiring: pin 16 = UART6_TX goes to GNSS RX; pin 18 = UART6_RX comes from GNSS TX; 3V3 on pin 1/17; GND. UART7 (TX pin 32, RX pin 29) is the fallback. PPS goes to a free GPIO (e.g. pin 37, GPIO_58) with a pps-gpio overlay.
  - Put any I2C sensors on I2C0 (pins 13/15) or I2C2 (pins 27/28), not I2C6, because I2C6 shares its serial engine with UART6.
  - Time stack: gpsd plus chrony. Ubuntu 24.04 ships gpsd 3.25; 3.26/3.27 improve UBX. chrony config: 'refclock SHM 0 refid NMEA offset 0.1 noselect' and 'refclock PPS /dev/pps0 lock NMEA refid PPS'. Expect about 1 us with PPS and 10-100 ms with NMEA only. Either is enough for TLE/Doppler; PPS mainly helps IQ timestamps.
  - LC76G setup: keep 115200 baud and 1 Hz. Enable 'PPS always output'. For timing, Quectel's forum advice is to disable EPOC ($PAIR496,0, then save with $PAIR513) and enable high-precision timing mode ($PAIR753,1).
  - GNSS antenna placement: mount the 25x25 mm active patch on the top face of the case over a ground plane of 50x50 mm or more, at least 5 cm from the Q6A SoC, the LimeSDR and the DC-DC converters. Alternatively fit an SMA bulkhead and use an external puck antenna. Route the u.FL coax away from HDMI/DSI/USB3 cables.
  - IMU puck: BNO086 + RP2040-Zero in a 3D-printed puck on the antenna boom, behind the reflector or at the edge of the helix ground plane. Keep it at least 15-20 cm from the steel elements, LNB, battery and power leads, and use brass or nylon screws. Run USB to a spare Q6A USB 2.0 port (the RTL-SDR uses one). The RP2040 streams quaternion + accuracy at 20-50 Hz; Python on the Q6A draws the az/el arrows.
  - Calibration: calibrate with the antenna attached, because rigidly mounted steel then becomes a fixed hard/soft-iron term the sensor can compensate. Rotate through all axes until the magnetometer accuracy flag reads 3, then save the DCD. Verify against the sun's azimuth or a known landmark. Do one calibration per antenna.
  - Declination: apply WMM2025 computed from the GNSS fix (pygeomag). Values for Oct 2026 that I computed: Kyiv +8.5 deg E, Lviv +7.2 deg, Kharkiv +9.3 deg, Odesa +7.4 deg.
  - QO-100 dish: beamwidth is about 5.7 deg at 35 cm and 10.5 GHz. Use accelerometer elevation and a coarse compass azimuth, then peak on the beacon in SDR++. If the dish is steel, move the puck away from it after coarse alignment.
  - Power draw is negligible: LC76G(AB) 36 mA @3.3 V (~0.12 W), MAX-M10S 25 mW, LC29H 43 mA, RP2040 + BNO08x a few tens of mA.
- **Double duty opportunities:**
  - One GNSS fix feeds the QTH for Gpredict/SatDump, the WMM2025 declination for the compass, and chrony time for TLE propagation and IQ-file timestamps.
  - Sun alignment: GNSS time and position give the sun's az/el. Point the boom at the sun once (shadow trick) to set a heading offset, then track with the BNO08x Game Rotation Vector (gyro-only, 0.5 deg/min drift spec). This avoids magnetic errors for the length of a pass.
  - Shared PPS: the external GNSS PPS can also feed the LimeSDR Micro's J5 PPS input on the basic board (v1.1/v1.2: remove R176 and fit a 0 ohm at R179). If Lime adds PPS timestamping or GPSDO, one receiver serves both host and SDR, so skip the $50 GNSS variant.
  - The IMU's gravity vector (1.5 deg static spec) gives antenna elevation on its own, even where the compass is unusable (steel dish, near the vehicle).
  - The RP2040 bridge in the puck can also drive an 'on target' buzzer or LED whose pitch tracks pointing error, so you don't have to watch the screen.
  - If you choose a u-blox M10, its jamming/spoofing flags double as an EW-interference indicator to log alongside recordings.
  - The GNSS backup cell keeps ephemeris and time for hot starts, and GNSS time can stand in for an RTC when booting offline. I did not verify whether the Q6A has an RTC battery fitted.
- **Confidence:** medium

## Форуми та досвід спільноти (`forums`)

_Run `wf_45d278c2-004`_

- **Component:** GNSS receiver + IMU/compass (location, timing/PPS, on-screen antenna pointing) attached to the Radxa Dragon Q6A (QCS6490)
- **Experiences:**
  1.
    - **Product:** Radxa Dragon Q6A UART6 (pins 16/18), the planned GNSS port
    - **Source url:** https://forum.radxa.com/t/using-uart-in-native-mode-solved/30063
    - **Community:** forum.radxa.com
    - **What they built:** Application UART on the Q6A header (Ubuntu 24.04, kernel 6.17.1-2-qcom, SPI-NOR fw 251013)
    - **Problems:**
      - UART12 showed status=disabled in the live DTB, which comes from the UEFI/SPI firmware; the poster says kernel DTS edits had no effect
      - The radxa uart6 .dtbo applied at boot (embloader log) but the port did not work
    - **Fixes:**
      - Poster found an error in qcs6490-radxa-dragon-q6a-uart6.dtbo, modified it, and got bidirectional /dev/ttyHS1
      - The fix was never published; a later user asked for it in Sept 2026 with no answer
    - **Outcome:** Solved for that user only. Today's upstream uart6.dtso sets pinctrl-0 = qup_uart6_tx/rx explicitly; commits are dated Nov 2025, Apr 2026 and May 2026.
  2.
    - **Product:** Radxa Dragon Q6A UART (header) TX path
    - **Source url:** https://forum.radxa.com/t/uart-transmission/31422
    - **Community:** forum.radxa.com
    - **What they built:** Q6A talking JSON over UART to an ESP32 (Waveshare UGV02); the same script works on Pi 4/5 and Rock 5T
    - **Problems:**
      - RX (telemetry) works but nothing the Q6A transmits arrives
      - In thread 30455 the same user (Aug 2026) says rsetup shows 'error' for the UART pin states
    - **Fixes:**
      - None. Replies only point to closed firmware and overlays.
    - **Outcome:** Unresolved as of Sept 2026.
  3.
    - **Product:** Radxa Dragon Q6A UART6/UART12 via rsetup
    - **Source url:** https://forum.radxa.com/t/using-serial-ports-on-dragon-q6/30455
    - **Community:** forum.radxa.com
    - **What they built:** Two header UARTs enabled on the RadxaOS noble r2 image
    - **Problems:**
      - Expected /dev/ttyS6 and /dev/ttyS12, which never appeared
    - **Fixes:**
      - The enabled GENI UARTs show up as /dev/ttyHS1 and /dev/ttyHS2
    - **Outcome:** Solved. gpsd and chrony must point at /dev/ttyHSx.
  4.
    - **Product:** Radxa Dragon Q6A SPI6 / GPIO on the 40-pin header
    - **Source url:** https://forum.radxa.com/t/how-to-enable-spi-and-use-gpio/29642
    - **Community:** forum.radxa.com
    - **What they built:** e-paper and ST7789 displays over SPI; an SX1262 LoRa (Meshtastic) on SPI6
    - **Problems:**
      - Header GPIOs sit on /dev/gpiochip4, not gpiochip0
      - SPI degraded above about 30 MHz; Radxa suspects the UM3304 level translator
      - DMA mode is gated by firmware
    - **Fixes:**
      - Use gpiod on gpiochip4, line = GPIO number (pin 3 = line 24)
      - Enable SPI overlays with rsetup
      - Update the kernel and UEFI firmware, and set 'Radxa Platform Configuration -> GPIO -> QUPV3_xxx Mode' to SPI in the UEFI menu for GPI DMA
    - **Outcome:** Working: SX1262 Meshtastic ran on SPI6. A BNO08x SPI link (3 MHz max) is far below the 30 MHz limit.
  5.
    - **Product:** Radxa Dragon Q6A I2C2 (pins 27/28)
    - **Source url:** https://github.com/radxa-pkg/radxa-overlays/issues/552
    - **Community:** GitHub radxa-pkg/radxa-overlays
    - **What they built:** Argon fan HAT (I2C device) on the Q6A
    - **Problems:**
      - The device did not respond after setting pins 27/28 to I2C in the BIOS and enabling the kernel option
    - **Fixes:**
      - None. Assigned to a Radxa developer on 2 Jul 2026.
    - **Outcome:** Open. No public report shows a working I2C sensor on the Q6A header under Linux.
  6.
    - **Product:** Quectel LC76G (Waveshare module) as a GPS-PPS time source
    - **Source url:** https://forums.quectel.com/t/significant-periodic-1pps-noise-with-lc76g-module/57109
    - **Community:** forums.quectel.com
    - **What they built:** Stratum-1 NTP server: Waveshare LC76G, PPS into a Raspberry Pi 4 (aarch64), chrony
    - **Problems:**
      - Normally <100 ns RMS, but every ~3 h for ~30 min the offset jumped to tens of µs
      - EASY commands $PAIR490/491 were removed in firmware LC76GABNR12A04S
      - Stationary mode picked a fixed position metres off the surveyed point
    - **Fixes:**
      - Root cause was the host OS; moving to in-memory Alpine Linux removed the periodic noise
      - Disabling EPOC ($PAIR496,0, save with $PAIR513, reset with $PAIR002) cut mean RMS offset by ~35%
      - High-precision timing mode ($PAIR753,1, then $PQTMSAVEPAR) gained another 5-8%
    - **Outcome:** Working, sub-100 ns RMS. Confirms the LC76G PPS is timing-grade and that host-side jitter dominates.
  7.
    - **Product:** Quectel LC76G PPS behaviour without a fix
    - **Source url:** https://forums.quectel.com/t/gnss-lc76g-1-pss-configuration/45880
    - **Community:** forums.quectel.com
    - **What they built:** Locomotive timing with the LC76G set to 'PPS after first fix' ($PAIR752 PPSType=1)
    - **Problems:**
      - With the antenna disconnected, PPS stopped after 45 minutes
    - **Fixes:**
      - Quectel: set 'PPS always output'; the module then free-runs PPS from its RTC and resyncs when signal returns
    - **Outcome:** Workaround given. Free-run PPS accuracy during the outage is not specified.
  8.
    - **Product:** Quectel LC76G(AB) over I2C
    - **Source url:** https://forums.quectel.com/t/lc76g-ab-over-i2c-0x54-permanently-nacks-while-0x50-still-acks-reset-n-does-not-recover-only-long-power-off/59469
    - **Community:** forums.quectel.com
    - **What they built:** LC76G on a Waveshare ESP32-S3 AMOLED board, shared I2C bus at 100 kHz
    - **Problems:**
      - I2C is a proprietary 0x50/0x54 mailbox protocol, not plain NMEA
      - The module clock-stretches up to ~200 ms
      - 400 kHz gave corrupt reads and repeated-START gave NACKs
      - Writing raw NMEA to 0x50 corrupted module state
      - 0x54 eventually NACKs permanently; RESET_N does not recover it, only long power-off does
    - **Fixes:**
      - Separate frames per step, ≥10 ms delays, 500 ms receive timeout, 512-byte chunks
      - Quectel recommends UART as the workaround
    - **Outcome:** Unresolved on I2C. gpsd cannot use this mode, so the LC76G must go on UART.
  9.
    - **Product:** Quectel LC29H(BA) PPS-to-NMEA latency
    - **Source url:** https://forums.quectel.com/t/weird-behavior-on-lc29hba-with-a-30-minutes-period/47717
    - **Community:** forums.quectel.com
    - **What they built:** PPS-triggered GNSS data logger
    - **Problems:**
      - NMEA normally arrives ~80 ms after PPS but jumps to 300-400 ms for one cycle every 30 minutes
    - **Fixes:**
      - Quectel: the module writes ephemeris to flash every half hour. No disable command was offered.
    - **Outcome:** Explained, not removable. NMEA-only timing has periodic outliers; PPS is unaffected.
  10.
    - **Product:** Quectel LC29H(AA) Waveshare HAT on Raspberry Pi 5
    - **Source url:** https://forums.quectel.com/t/lc29h-aa-in-ntpsec/46578
    - **Community:** forums.quectel.com
    - **What they built:** Planned gpsd + ntpsec/chrony time source
    - **Problems:**
      - gpsd could not read NMEA from /dev/ttyAMA0
    - **Fixes:**
      - Quectel gave only a generic PPS explanation (20 ns RMS)
    - **Outcome:** Unresolved in the thread.
  11.
    - **Product:** Quectel LC86G (same Airoha-based family as LC76G)
    - **Source url:** https://forums.quectel.com/t/lc86g-not-working-in-russia/57394
    - **Community:** forums.quectel.com
    - **What they built:** Truck trackers
    - **Problems:**
      - All modules worked except in the Russia region
    - **Fixes:**
      - Quectel staff: 'the module will not be working in Russia'. No mechanism was explained.
    - **Outcome:** Confirms Quectel GNSS firmware has a regional restriction. How it decides location is undocumented.
  12.
    - **Product:** u-blox MAX-M10S + gpsd 3.27.6 on Raspberry Pi 5
    - **Source url:** https://gitlab.com/gpsd/gpsd/-/work_items/415
    - **Community:** gpsd GitLab
    - **What they built:** MAX-M10S on /dev/ttyAMA0 feeding gpsd
    - **Problems:**
      - QZSS $GQGSV sentences reach the serial port but gpsd drops them from gpspipe and port 2947
    - **Fixes:**
      - None yet
    - **Outcome:** Open (Sept 2026). Cosmetic for sky view; position and time are unaffected.
  13.
    - **Product:** SparkFun MAX-M10S + gpsd ubxtool
    - **Source url:** https://gitlab.com/gpsd/gpsd/-/work_items/281
    - **Community:** gpsd GitLab
    - **What they built:** Configuring signals with ubxtool
    - **Problems:**
      - CFG-SIGNAL-BDS_B1C_ENA (0x1031000f) was missing from ubx.py
    - **Fixes:**
      - User patch added the key
    - **Outcome:** Closed 2024, fixed upstream. Older distro gpsd may still lack it.
  14.
    - **Product:** SparkFun MAX-M10S breakout
    - **Source url:** https://community.sparkfun.com/t/adding-configuration-flash-memory-to-sparkfun-gnss-receiver-breakout-max-m10s/65405
    - **Community:** community.sparkfun.com
    - **What they built:** PPS set to 1 MHz to drive a PLL
    - **Problems:**
      - Configuration survives only while the backup battery is alive; no external flash is possible
      - Slow 3-5 Hz FM on the timepulse
    - **Fixes:**
      - Use OTP for permanent settings, or pick a flash-equipped part (NEO-F10N, Beitian BE-126)
      - Timepulse is an NCO-quantised clock (M10 uses 64 MHz); clean it with a PLL/VCXO
    - **Outcome:** Design guidance only. 1 Hz PPS for chrony is unaffected.
  15.
    - **Product:** SparkFun SAM-M10Q (integrated chip antenna)
    - **Source url:** https://community.sparkfun.com/t/sam-m10q-breakout-cannot-acquire-fix/67651
    - **Community:** community.sparkfun.com
    - **What they built:** Bench test with u-center
    - **Problems:**
      - 10-20 min to first fix, fix lost after 1-5 s, no satellites in the default configuration
    - **Fixes:**
      - clive1: isolate it from MCU and GPIO clock noise; use a ~12 cm ground plane with the SAM on top and circuitry underneath; avoid body blockage
      - SparkFun: feed it clean 3.3 V; offered a replacement
    - **Outcome:** No confirmed resolution. The antenna-integrated M10 is very sensitive to nearby digital noise.
  16.
    - **Product:** u-blox GPS on HackerGadgets uConsole AIO V1 (handheld: CM4 + RTL-SDR + GPS)
    - **Source url:** https://forum.clockworkpi.com/t/hackergadgets-aio-v1-gps-antenna-open-frozen-lat-lon-on-debian-bookworm-two-separate-bugs-both-fixed/23298
    - **Community:** forum.clockworkpi.com
    - **What they built:** Handheld SDR/GPS console
    - **Problems:**
      - Persistent 'ANTENNA OPEN': a leftover SOT-23 part (marked 3K10) back-fed 4.7-4.9 V onto the antenna line
      - gpsd 3.22 (Debian bookworm) froze TPV lat/lon at a placeholder in UBX mode while ECEF kept updating
      - UBX-MON-HW NAKs on this module
    - **Fixes:**
      - Desolder the part; vendor says it only affects the warning
      - Run gpsd with -p (no receiver reconfiguration) or use gpsd ≥3.24
    - **Outcome:** Both fixed. Ubuntu 24.04's gpsd 3.25 is past the lat/lon bug.
  17.
    - **Product:** GPS on uConsole AIO V2 (CM5)
    - **Source url:** https://forum.clockworkpi.com/t/uconsole-aio-v2-rtl-sdr-lora-gps-rtc-usb-hub-usb-3-0-rj45-ethernet/20800/83
    - **Community:** forum.clockworkpi.com
    - **What they built:** Handheld with GPS on a serial line
    - **Problems:**
      - U-Boot drove the GPS power-enable high, and the GPS serial output disrupted the bootloader
    - **Fixes:**
      - Use an image that leaves GPS power off at boot
    - **Outcome:** Fixed by image choice. On the Q6A, NMEA must never reach the debug UART (pins 8/10), where the embloader menu accepts input.
  18.
    - **Product:** SatNOGS station clock disciplined by GNSS + PPS (NEO-7M with a hand-soldered PPS wire)
    - **Source url:** https://community.libre.space/t/tutorial-setup-gpsd-and-pulse-per-second-pps-for-satnogs-station-discipline-clock-getting-the-time-directly-from-the-satellites/15272
    - **Community:** community.libre.space (SatNOGS)
    - **What they built:** Raspberry Pi 4 ground station with gpsd, pps-gpio and chrony (Sept 2026)
    - **Problems:**
      - Cheap module had no PPS pin
      - gpsd.socket and gpsd.service conflicted on port 2947 and froze xgps (another user)
      - USB NMEA-only source showed +53 ms offset
    - **Fixes:**
      - Solder a wire to the PPS pin of the GPS chip
      - Resolve the systemd unit conflict
      - Use PPS. frovelli warns a disciplined Linux clock does not make the SDR sample clock or timestamps accurate.
    - **Outcome:** Working.
  19.
    - **Product:** SatNOGS PPS-disciplined station vs satellite clocks
    - **Source url:** https://community.libre.space/t/my-groundstation-clock-vs-satellite-clock/15370
    - **Community:** community.libre.space (SatNOGS)
    - **What they built:** Comparing station decode times with satellite telemetry clocks
    - **Problems:**
      - chrony showed the NMEA (GPS) refclock at +135 ms ±101 ms and PPS at -1354 ns ±242 ns
      - A FrontierSat developer found the SatNOGS/GNU Radio recording-to-timestamp path off by 4-7 s even with a good station clock
    - **Fixes:**
      - Use PPS as the selected source and NMEA only for the second number
      - Hardware timestamping is still needed for sub-second IQ timing
    - **Outcome:** Station clock accurate to ~1 µs, but the software pipeline adds seconds-level error.
  20.
    - **Product:** chrony + PPS stratum-1 references
    - **Source url:** https://community.libre.space/t/setup-operational-report-gps-qzss-backed-stratum-1-ntp-server/15456
    - **Community:** community.libre.space (SatNOGS)
    - **What they built:** GPS/QZSS NTP servers
    - **Problems:**
      - USB NMEA-only setup reached only ~0.1 ms
    - **Fixes:**
      - PPS: PE0SAT reports 661 ns RMS offset; bali reports 948 ns
    - **Outcome:** Baseline for what the Q6A should reach with pps-gpio.
  21.
    - **Product:** ATGM336H (x2) vs NEO-7M PPS
    - **Source url:** https://febo.com/pipermail/time-nuts_lists.febo.com/2022-May/105808.html
    - **Community:** time-nuts mailing list
    - **What they built:** Three GPS PPS outputs time-stamped against a 10 MHz rubidium-derived 200 MHz timer
    - **Problems:**
      - Module-to-module mean offsets of 10-39 ns
      - Periodic variation up to 20 ns; NEO-7M was the worst
    - **Fixes:**
      - None needed. Author suggests GPSDO phase specs should allow ~10-20 ns PPS uncertainty.
    - **Outcome:** Gives the ATGM336H the PPS figure missing from its datasheet: tens of ns, more than adequate here.
  22.
    - **Product:** BNO085/BNO086 with the Adafruit CircuitPython BNO08x library
    - **Source url:** https://github.com/adafruit/Adafruit_CircuitPython_BNO08x/issues/49
    - **Community:** GitHub issues
    - **What they built:** BNO08x on Pi Pico (RP2040), Raspberry Pi 3B+ and Pi Zero 2 W
    - **Problems:**
      - RuntimeError ('Unprocessable Batch bytes', 2) on enable_feature; intermittent or no data, reported by 7+ users 2024-2025
    - **Fixes:**
      - Comment out the raise in _handle_packet (bad data for ~1 s, then valid) and run 400 kHz
      - Clock-stretching guide (slow bus)
      - One user switched to an LSM9DS1
    - **Outcome:** Still open, no maintainer fix. Avoid this library on Linux and RP2040; use CEVA SH-2 based C libraries.
  23.
    - **Product:** BNO08x on NVIDIA Jetson Orin Nano (non-Broadcom ARM Linux I2C)
    - **Source url:** https://github.com/adafruit/Adafruit_CircuitPython_BNO08x/issues/56
    - **Community:** GitHub issues
    - **What they built:** Stereo camera IMU over I2C
    - **Problems:**
      - First SHTP packet read, then OSError [Errno 121] Remote I/O error on enable_feature
    - **Fixes:**
      - None
    - **Outcome:** Open. This is the closest analogue to Qualcomm GENI I2C.
  24.
    - **Product:** BNO085 on Raspberry Pi Zero W
    - **Source url:** https://forum.core-electronics.com.au/t/problems-using-bno085-imu-with-pi-zer0-w/9218?page=2
    - **Community:** Core Electronics forum
    - **What they built:** Absolute-orientation project
    - **Problems:**
      - Hardware I2C failed (clock stretching)
      - Lowering the clock was judged an unreliable hack
    - **Fixes:**
      - Software I2C (i2c-gpio overlay on other pins) worked
      - Others use the UART instead of I2C on Pi/ESP32 'with no problems'
    - **Outcome:** Working with bit-banged I2C.
  25.
    - **Product:** BNO080 on ESP32-C3 (Rust driver)
    - **Source url:** https://github.com/tstellanova/bno080/issues/5
    - **Community:** GitHub issues
    - **What they built:** Embedded IMU driver
    - **Problems:**
      - NACKs or I2C timeouts in soft_reset/init because the host reads before the sensor is ready (long clock stretch)
    - **Fixes:**
      - Wait for the INT pin before every read; otherwise retry with a timeout
    - **Outcome:** Proposal, no maintainer reply. Wiring INT (and RST) is important on any host.
  26.
    - **Product:** BNO085 on Arduino UNO R4 WiFi (Renesas I2C)
    - **Source url:** https://forum.arduino.cc/t/bno085-responds-at-i-c-address-0x4a-but-initialization-fails-on-arduino-uno-r4-wifi/1452433
    - **Community:** forum.arduino.cc
    - **What they built:** Qwiic-connected BNO085
    - **Problems:**
      - Scanner sees 0x4A but begin_I2C() fails; the sensor stops responding rather than recovering
    - **Fixes:**
      - Not resolved
      - A poster quotes Adafruit: BNO08x I2C 'violates the protocol in some cases' and works best on SAMD51, RP2040, STM32F4 and nRF52840
    - **Outcome:** Unresolved (July 2026). Supports bridging through an RP2040.
  27.
    - **Product:** BNO085 9-DOF rotation vector heading
    - **Source url:** https://forum.arduino.cc/t/bno085-calibration-process/904696
    - **Community:** forum.arduino.cc
    - **What they built:** Heading measurement
    - **Problems:**
      - Accuracy flag reached 3 almost immediately, yet heading jumped 45-90° after high-motion periods
      - The calibration routine is opaque
    - **Fixes:**
      - Game Rotation Vector (6-DOF) was more stable
      - jremington: ~15 min manual calibration per sensor, or use an ICM-20948/LSM9DS1 with host fusion; reject outlier samples
    - **Outcome:** No fix for 9-DOF heading. Do not trust the accuracy flag alone.
  28.
    - **Product:** SparkFun BNO086 (VR IMU)
    - **Source url:** https://community.sparkfun.com/t/bno086/62015
    - **Community:** community.sparkfun.com
    - **What they built:** Robot compass
    - **Problems:**
      - The magnetometer X axis pointed the wrong way even after calibration, while an ICM-20948 at the same spot was fine
      - Euler example axes wrong for the datasheet frame: pitch and roll swapped, heading = 360 - yaw
    - **Fixes:**
      - Unit replaced, which immediately fixed it
      - Remap axes in code
    - **Outcome:** Faulty units do occur. Run a field-magnitude sanity check on arrival.
  29.
    - **Product:** SparkFun BNO086 on a mobile robot
    - **Source url:** https://community.sparkfun.com/t/imu-bno086/64830
    - **Community:** community.sparkfun.com
    - **What they built:** Robot using geomagnetic Euler yaw
    - **Problems:**
      - Yaw swung ±150° within a minute
      - Occasional single wrong yaw samples after calibration
    - **Fixes:**
      - Calibrate per the CEVA procedure
      - jremington: the docs warn that dynamic calibration can cause a sudden orientation reset, so turn it off during use
    - **Outcome:** Partially addressed.
  30.
    - **Product:** SparkFun BNO086 as a tilt-compensated compass
    - **Source url:** https://community.sparkfun.com/t/bno086-how-to-access-geomagnetic-vector-i-just-want-a-compass/46474
    - **Community:** community.sparkfun.com
    - **What they built:** Compass on an Arduino Mega
    - **Problems:**
      - Library examples gave startup-relative yaw; the Geomagnetic Rotation Vector was not exposed
    - **Fixes:**
      - User patched the library (~8 lines)
      - SparkFun created a geomagnetic_rotation_vector branch (Nov 2023)
    - **Outcome:** Branch provided. Calibration still unresolved.
  31.
    - **Product:** BNO08x on RP2040 (Waveshare RP2040-Touch-LCD) with the SparkFun library
    - **Source url:** https://github.com/sparkfun/SparkFun_BNO08x_Arduino_Library/issues/18
    - **Community:** GitHub issues
    - **What they built:** RP2040-hosted BNO08x orientation display, the same architecture as the proposed puck
    - **Problems:**
      - Roll/pitch drifted 1-5° during yaw rotation and sometimes settled 1-4° off until power cycle
      - Possible damage from 5 V supply; buck-converter noise suspected
    - **Fixes:**
      - Power the BNO from clean 3.3 V, which 'solved most of the issue'
      - Tare; repeated 180° rotations; power cycle
    - **Outcome:** Open, partially mitigated by clean 3.3 V.
  32.
    - **Product:** BNO08x SparkFun library, I2C chunking
    - **Source url:** https://github.com/sparkfun/SparkFun_BNO08x_Arduino_Library/issues/32
    - **Community:** GitHub issues
    - **What they built:** ESP32-S3 with linear acceleration + game RV at 5 ms
    - **Problems:**
      - Reports corrupted by the next report's header when ~100-byte packets are read in 32-byte chunks; status stays 3, so accuracy filtering misses them
    - **Fixes:**
      - Set _maxBufferSize to 128 (the platform Wire buffer)
    - **Outcome:** Workaround works, upstream open (Sept 2026). On RP2040, set the buffer ≥ packet size.
  33.
    - **Product:** BNO085 ROS 2 driver on Raspberry Pi
    - **Source url:** https://groups.google.com/g/hbrobotics/c/EfLPPDUdEZE
    - **Community:** HomeBrew Robotics Club (Google Groups)
    - **What they built:** ROS 2 Jazzy robot
    - **Problems:**
      - Magnetometer calibration fails in some setups
      - Another member reports the heading 'hunts'
    - **Fixes:**
      - Added an enable_6dof_mode parameter (PR #4)
    - **Outcome:** I2C works on that Pi. UART/SPI untested in the driver.
  34.
    - **Product:** SparkFun, no-name and Adafruit BNO08x boards compared
    - **Source url:** https://wolles-elektronikkiste.de/en/bno08x-9-dof-imus
    - **Community:** Wolles Elektronikkiste (German maker blog)
    - **What they built:** Side-by-side tests over I2C/SPI/UART/UART-RVC
    - **Problems:**
      - Default I2C address differs: SparkFun and no-name 0x4B, Adafruit 0x4A
      - Only the Adafruit board is 5 V tolerant
      - Author notes I2C can cause problems and suggests switching protocol
    - **Fixes:**
      - Use SPI/UART if I2C misbehaves; connect INT and RST with the SparkFun library
    - **Outcome:** All three boards, including the no-name one, worked. Awake current ~12.3 mA at 3.3 V.
  35.
    - **Product:** BNO085 / LSM6DSV / ICM-20948 / BMI270 in SlimeVR trackers
    - **Source url:** https://docs.slimevr.dev/diy/imu-comparison.html
    - **Community:** SlimeVR docs (large DIY user base)
    - **What they built:** Thousands of body-tracking IMUs
    - **Problems:**
      - BNO085: 'stomp bug', 'very misleading AliExpress listings', dropped from the SlimeVR store
      - ICM-20948 'sensitive to bad magnetic environments'
      - BMI270 'very poor tracking'
    - **Fixes:**
      - LSM6DSV 'seems to perform just as well as the BNO085, but at a lower cost'
      - Magnetometer environment should fluctuate ≤5 µT
    - **Outcome:** Community-scale evidence: LSM6DSV is a real alternative; BMI270 is weak; BNO085 supply is getting harder.
  36.
    - **Product:** SARCNET Mini Satellite-Antenna Rotator Mk1 (LSM303 accel/mag on the antenna boom)
    - **Source url:** https://www.sarcnet.org/mini-satellite-antenna-rotator-mk1.html
    - **Community:** SARCNET (amateur satellite builders)
    - **What they built:** Portable solar-powered az/el satellite rotator with a boom-mounted 3D sensor
    - **Problems:**
      - Small steel screws on the sensor shifted the reported pointing
      - Electronics RFI audible in the receiver
      - I2C interference near the driven elements
    - **Fixes:**
      - Brass screws or silicone adhesive
      - Mount on the lift arm away from driven elements
      - Shielded I2C cable, ferrites, 0.1 µF caps on motors
      - 12-point calibration plus declination entry
    - **Outcome:** '+/- 5 degree accuracy is possible with optimal calibration, but is not guaranteed.' The most comparable real-world figure for boom-mounted compass pointing.
  37.
    - **Product:** SARCTRAC Mk2 (Raspberry Pi 3B+, boom-mounted 3D sensor, built-in GPS)
    - **Source url:** https://www.sarcnet.org/sarctrac-mk2.html
    - **Community:** SARCNET
    - **What they built:** Satellite antenna tracker with GPS for location and time
    - **Problems:**
      - Pi and 5 V supply caused significant RFI
      - I2C 'does not work much over 1 metre of unshielded cable'
      - Oscillation unless the sensor is rigidly mounted
    - **Fixes:**
      - Linear-regulated 5 V and RF chokes on 5 V/DIO lines brought noise down to ~S6
      - I2C slowed to 10 kbps
      - Rigid boom mount; factory calibration
    - **Outcome:** Working product. Supports a short local link or a USB bridge for a boom puck.
  38.
    - **Product:** SatNOGS rotator with magnetometer homing
    - **Source url:** https://community.libre.space/t/satnogs-rotator-and-arduino-magnetic-compass/2723
    - **Community:** community.libre.space (SatNOGS)
    - **What they built:** Rotator auto-homing with accel + magnetometer
    - **Problems:**
      - Motor interference corrupts compass readings
    - **Fixes:**
      - Measure only at power-up with motors off; needs station position for true north
    - **Outcome:** Design guidance. The handheld equivalent: read heading with no TX/fan transients nearby.
  39.
    - **Product:** BNO085 'Directional Gyro' (Teensy 4.0)
    - **Source url:** https://www.pjrc.com/directional-gyro/
    - **Community:** PJRC
    - **What they built:** Heading indicator immune to magnetic disturbance
    - **Problems:**
      - Magnetometer heading disturbed by ferrous metal and motors
    - **Fixes:**
      - Use gyro-based heading and calibrate to north once with a magnetic compass
    - **Outcome:** Working. Validates the 'set north once, then Game Rotation Vector' approach.
  40.
    - **Product:** SparkFun MMC5983MA magnetometer
    - **Source url:** https://community.sparkfun.com/t/mmc5983ma-doesnt-seem-to-work-properly/46529
    - **Community:** community.sparkfun.com
    - **What they built:** Compass accuracy test against WMM
    - **Problems:**
      - Field magnitude varied 76-131% with orientation; SET/RESET did not remove the offsets
    - **Fixes:**
      - A MEMSIC evaluation board worked correctly; the poster suspects the SparkFun board was soldered above the part's low maximum reflow temperature
      - jremington: ellipsoid calibration (3x3 matrix + offsets)
    - **Outcome:** Unit/board quality variance.
  41.
    - **Product:** SparkFun MMC5983MA digital compass example
    - **Source url:** https://community.sparkfun.com/t/mmc5983ma-example2-i2c_digital_compass/45244
    - **Community:** community.sparkfun.com
    - **What they built:** Turntable test at cardinal points
    - **Problems:**
      - 0/90/180/270° read as 0/119/158/184°
      - Another thread (45043) reports a bad sample every 15 readings
    - **Fixes:**
      - Calibrate in the final mounting (Cave Pearl / Pololu ellipsoid method)
    - **Outcome:** Raw magnetometers are useless as compasses until calibrated in place.
  42.
    - **Product:** ICM-20948 IMU HAT with pypilot (OpenPlotter, Raspberry Pi)
    - **Source url:** https://forum.openmarine.net/printthread.php?tid=4686
    - **Community:** forum.openmarine.net
    - **What they built:** Boat autopilot compass
    - **Problems:**
      - 'compass out of range', 'failed to read IMU', 'imu process failed to keep time'; a second pypilot instance was also reading the IMU
    - **Fixes:**
      - Run a single pypilot instance and the OpenPlotter calibration
    - **Outcome:** Final cause was a faulty Pi; the IMU worked on another Pi.
  43.
    - **Product:** LimeSDR XTRX GNSS/GPSDO and PPS (closest Lime analogue to the Micro GNSS variant)
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-xtrx-v1-3-reference-clock-and-pps/13045
    - **Community:** discourse.myriadrf.org
    - **What they built:** XTRX boards with external 10 MHz / onboard GNSS
    - **Problems:**
      - External clock and PPS sync are undocumented in LimeSuiteNG and need raw register writes
      - PPS-triggered TX proven not to work
      - Fairwave XTRX GPSDO never reached ~0.1 ppb
      - An unfitted R156 on v1.3 blocked the external clock
    - **Fixes:**
      - limeSPI writes / WriteRegister(0x0018) to select the external clock
      - Square-wave reference (not sine)
      - Fit R156
    - **Outcome:** Partly working on XTRX (LiteX gateware with LimePPSDO). No equivalent exists for the Micro.
  44.
    - **Product:** LimeSDR XTRX hardware timestamping with 1PPS
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-xtrx-hardware-timestamping-with-1-pps/12949
    - **Community:** discourse.myriadrf.org
    - **What they built:** Interferometry plan with GPSDOs
    - **Problems:**
      - Only XTRX gateware supports PPS-synchronised sampling start; other LimeSDRs likely do not
    - **Fixes:**
      - Feature request opened in LimeSDR_GW, 'no guarantee'
    - **Outcome:** For the Micro, PPS-accurate IQ timestamps are not available today.
  45.
    - **Product:** LimeSDR Micro firmware: external reference clock select
    - **Source url:** https://github.com/myriadrf/LimeSDR-Micro_FW/issues/6
    - **Community:** GitHub myriadrf/LimeSDR-Micro_FW
    - **What they built:** Evaluating the Micro with a GPS-disciplined 10 MHz reference
    - **Problems:**
      - The code writes MCP23017 register 0x09 (INTCONB) instead of OLATA (0x14), so the board silently stays on its internal TCXO while reporting success
    - **Fixes:**
      - Commit 1f70189 'Fix #6 external reference clock select' linked on 16 Oct 2026
    - **Outcome:** Issue still open; fix not yet on master. Any external-reference/GPSDO plan for the basic Micro needs a firmware build that includes it.
  46.
    - **Product:** GNSS receivers near Raspberry Pi 4 / USB 3 devices
    - **Source url:** https://forum.openmarine.net/showthread.php?pid=19200
    - **Community:** forum.openmarine.net (also NVIDIA developer forum thread 195632)
    - **What they built:** Boat computers with USB GPS and SSDs
    - **Problems:**
      - USB 3 circuitry jammed GPS within ~2 m of a Pi 4
    - **Fixes:**
      - Move the SSD to USB 2, which cured it immediately
      - Put the GPS on a 5 m active USB 2 extension
      - Foil-shield the USB 3 enclosure and cable: 'no fix' became 'instantaneous fix'
      - External antenna
    - **Outcome:** Working after the fixes. Read from search snippets, not full thread fetch.
- **Common problems:**
  1.
    - **Problem:** BNO08x I2C fails or corrupts on general-purpose hosts. Clock stretching and protocol violations cause NACKs, Errno 121 errors, 'Unprocessable Batch bytes' and lock-ups that need a reset.
    - **Affected products:** BNO085/BNO086 on Raspberry Pi (all models), Jetson Orin Nano, ESP32/ESP32-C3/S3, Renesas UNO R4. Likely relevant to Qualcomm GENI I2C (untested).
    - **Frequency:** common
    - **Known fix:** Avoid hardware I2C on Linux hosts:
  - use SPI (Q6A SPI6 is proven working), UART-SHTP, or an MCU bridge (Adafruit lists RP2040/SAMD51/STM32F4/nRF52840 as good hosts);
  - on a Pi: software I2C (i2c-gpio) or 400 kHz;
  - always wire INT and RST and gate reads on INT;
  - set the library I2C buffer ≥ packet size;
  - don't use the CircuitPython library: issue #49 is unresolved even on RP2040.
    - **Fix sources:**
      - https://github.com/adafruit/Adafruit_CircuitPython_BNO08x/issues/49
      - https://github.com/adafruit/Adafruit_CircuitPython_BNO08x/issues/56
      - https://forum.core-electronics.com.au/t/problems-using-bno085-imu-with-pi-zer0-w/9218?page=2
      - https://github.com/tstellanova/bno080/issues/5
      - https://forum.arduino.cc/t/bno085-responds-at-i-c-address-0x4a-but-initialization-fails-on-arduino-uno-r4-wifi/1452433
      - https://github.com/sparkfun/SparkFun_BNO08x_Arduino_Library/issues/32
      - https://learn.adafruit.com/adafruit-9-dof-orientation-imu-fusion-breakout-bno085/python-circuitpython
      - https://forum.radxa.com/t/how-to-enable-spi-and-use-gpio/29642
  2.
    - **Problem:** Magnetometer heading wrong or jumping. Causes: poor or opaque calibration, nearby ferrous parts (steel screws, elements) and current-carrying wiring. The BNO08x accuracy flag can read 3 while heading is off by 45-150°, and dynamic calibration can cause sudden resets.
    - **Affected products:** BNO085/BNO086, MMC5983MA, ICM-20948, LSM303 (SARCNET), SEN-19895
    - **Frequency:** common
    - **Known fix:** Calibrate in the final mounting with everything powered (ellipsoid fit for raw sensors; CEVA procedure plus save DCD for BNO08x), then disable dynamic calibration during use.
  - Mount the sensor on the boom or lift arm, away from driven elements.
  - Use brass or nylon screws.
  - Read heading with motors/fan transients absent.
  - Check field magnitude against WMM.
  - Prefer Game Rotation Vector plus a one-time north reference (sun or landmark) for passes.
  - Expect ±5° at best, per SARCNET.
    - **Fix sources:**
      - https://forum.arduino.cc/t/bno085-calibration-process/904696
      - https://community.sparkfun.com/t/imu-bno086/64830
      - https://www.sarcnet.org/mini-satellite-antenna-rotator-mk1.html
      - https://community.sparkfun.com/t/mmc5983ma-example2-i2c_digital_compass/45244
      - https://www.pjrc.com/directional-gyro/
      - https://community.libre.space/t/satnogs-rotator-and-arduino-magnetic-compass/2723
  3.
    - **Problem:** Q6A 40-pin header UARTs are hard to bring up. Peripherals are firmware/UEFI-gated (QUP mode), the uart6 overlay had a bug, ports appear as /dev/ttyHSx, and some users see RX working while TX does not.
    - **Affected products:** Radxa Dragon Q6A (RadxaOS/Ubuntu 24.04 images, kernels 6.17-7.0)
    - **Frequency:** occasional
    - **Known fix:** Enable uart6/uart7 via rsetup (radxa-overlays). Use /dev/ttyHS1/ttyHS2.
  - Update SPI-NOR/UEFI firmware.
  - Set 'Radxa Platform Configuration -> GPIO -> QUPV3_xxx Mode' in UEFI.
  - Verify TX with a loopback before relying on PAIR/UBX configuration.
  - The user who fixed the uart6 dtbo never published the change.
    - **Fix sources:**
      - https://forum.radxa.com/t/using-uart-in-native-mode-solved/30063
      - https://forum.radxa.com/t/using-serial-ports-on-dragon-q6/30455
      - https://forum.radxa.com/t/uart-transmission/31422
      - https://forum.radxa.com/t/how-to-enable-spi-and-use-gpio/29642
      - https://github.com/radxa-pkg/radxa-overlays/tree/main/arch/arm64/boot/dts/qcom/overlays
  4.
    - **Problem:** No pps-gpio support or overlay on the Q6A out of the box. radxa-overlays has no PPS overlay. CONFIG_PPS_CLIENT_GPIO is absent from Radxa's linux-6.17.1 and linux-6.18.2 qcom_module_defconfig and present (=m) in linux-7.0.11 radxa_qcom_7_0_defconfig. This is my own inspection of the kernel sources, not a community report.
    - **Affected products:** Radxa Dragon Q6A with RadxaOS kernels 6.17.x/6.18.x (default on Feb 2026 images); 7.0.11-x-qcom from radxa-repo
    - **Frequency:** occasional
    - **Known fix:** Upgrade to the 7.0.11 qcom kernel, or build pps-gpio.ko for 6.18.
  - Write a pps-gpio overlay on a free tlmm line (e.g. pin 37 = GPIO_58, gpiochip4) with UART14 disabled.
  - Test with ppstest /dev/pps0.
  - Then use chrony 'refclock PPS /dev/pps0 lock NMEA'.
    - **Fix sources:**
      - https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/configs/radxa_qcom_7_0_defconfig
      - https://github.com/radxa/kernel/blob/linux-6.18.2/arch/arm64/configs/qcom_module_defconfig
      - https://github.com/radxa-pkg/linux-qcom
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/pin-gpio
  5.
    - **Problem:** LC76G I2C mode is unusable for gpsd. It is a proprietary mailbox protocol with clock stretching up to ~200 ms, corrupts at 400 kHz, and has lock-ups that only a power cycle clears.
    - **Affected products:** Quectel LC76G(AB) (Waveshare boards)
    - **Frequency:** occasional
    - **Known fix:** Use UART (115200 default; $PAIR864 changes baud). Quectel itself recommends UART.
    - **Fix sources:**
      - https://forums.quectel.com/t/lc76g-ab-over-i2c-0x54-permanently-nacks-while-0x50-still-acks-reset-n-does-not-recover-only-long-power-off/59469
      - https://forums.quectel.com/t/lc76g-change-baud-rate/33867
  6.
    - **Problem:** PPS and NMEA timing artefacts from module housekeeping or the host OS: periodic µs-level PPS noise, NMEA latency spikes every 30 min, and PPS stopping after 45 min without a fix.
    - **Affected products:** Quectel LC76G, LC29H(BA)
    - **Frequency:** occasional
    - **Known fix:** Disable EPOC ($PAIR496,0 then $PAIR513), enable high-precision timing ($PAIR753,1 + $PQTMSAVEPAR) and 'PPS always output'.
  - Lock chrony to PPS, not NMEA.
  - Calibrate the NMEA offset (SatNOGS users saw +53 to +135 ms).
  - Suspect the host OS when periodic noise appears.
    - **Fix sources:**
      - https://forums.quectel.com/t/significant-periodic-1pps-noise-with-lc76g-module/57109
      - https://forums.quectel.com/t/gnss-lc76g-1-pss-configuration/45880
      - https://forums.quectel.com/t/weird-behavior-on-lc29hba-with-a-30-minutes-period/47717
      - https://community.libre.space/t/my-groundstation-clock-vs-satellite-clock/15370
  7.
    - **Problem:** gpsd quirks:
  - gpsd.socket and gpsd.service conflict;
  - gpsd reconfigures receivers and other apps can't share the port;
  - gpsd 3.22 froze lat/lon in u-blox binary mode;
  - QZSS GSV is dropped in 3.27.6;
  - gpsd auto-switched a Quectel MT3333 to the MTK driver and lost VTG.
    - **Affected products:** u-blox M10/M8 and Quectel L76/LC-series with gpsd on Debian/Ubuntu/RPi OS
    - **Frequency:** occasional
    - **Known fix:** Use gpsd ≥3.24 (Ubuntu 24.04 ships 3.25).
  - Set GPSD_OPTIONS="-n" and add -p if gpsd must not reconfigure the receiver.
  - Set USBAUTO=false.
  - Run one consumer of the serial port, or let everything else read from gpsd.
    - **Fix sources:**
      - https://forum.clockworkpi.com/t/hackergadgets-aio-v1-gps-antenna-open-frozen-lat-lon-on-debian-bookworm-two-separate-bugs-both-fixed/23298
      - https://community.libre.space/t/tutorial-setup-gpsd-and-pulse-per-second-pps-for-satnogs-station-discipline-clock-getting-the-time-directly-from-the-satellites/15272
      - https://gitlab.com/gpsd/gpsd/-/work_items/415
      - https://gitlab.com/gpsd/gpsd/-/work_items/245
  8.
    - **Problem:** GNSS desense from nearby digital noise (USB 3, SBC clocks, DC-DC, MCU GPIO). Integrated-antenna modules are worst.
    - **Affected products:** SAM-M10Q chip-antenna boards, any GNSS patch inside an SBC enclosure (RPi 4 USB 3 cases)
    - **Frequency:** common
    - **Known fix:** Use an external active patch on a ≥12 cm ground plane, with circuitry on the other side, and keep distance.
  - Use USB 2 instead of USB 3 nearby.
  - Shield USB 3 cables and enclosures.
  - Feed the module clean 3.3 V.
    - **Fix sources:**
      - https://community.sparkfun.com/t/sam-m10q-breakout-cannot-acquire-fix/67651
      - https://forum.openmarine.net/showthread.php?pid=19200
      - https://forums.developer.nvidia.com/t/usb3-0-gps-interference-how-to-mitigate/195632
  9.
    - **Problem:** Boom-mounted sensor wiring injects RFI into the receiver, and I2C fails over cable runs above ~1 m.
    - **Affected products:** SARCNET rotators (LSM303, Raspberry Pi), any boom-mounted IMU on I2C
    - **Frequency:** occasional
    - **Known fix:** Use a linear or filtered 5 V supply, RF chokes and ferrites, and shielded cable.
  - Run I2C at 10 kbps, or put an MCU at the sensor and send data over USB or serial.
  - Mount the sensor away from the driven elements.
    - **Fix sources:**
      - https://www.sarcnet.org/sarctrac-mk2.html
      - https://www.sarcnet.org/mini-satellite-antenna-rotator-mk1.html
  10.
    - **Problem:** GNSS NMEA on a boot console UART disrupts the bootloader.
    - **Affected products:** uConsole AIO V2 (U-Boot). Same risk on the Q6A debug UART5 (pins 8/10), where the embloader menu reads input.
    - **Frequency:** rare
    - **Known fix:** Never wire GNSS to the console UART. Keep GNSS power off during boot, or use UART6/UART7.
    - **Fix sources:**
      - https://forum.clockworkpi.com/t/uconsole-aio-v2-rtl-sdr-lora-gps-rtc-usb-hub-usb-3-0-rj45-ethernet/20800/83
      - https://forum.radxa.com/t/using-uart-in-native-mode-solved/30063
  11.
    - **Problem:** Configuration lost on power loss.
    - **Affected products:** u-blox MAX-M10S (battery-backed RAM only)
    - **Frequency:** occasional
    - **Known fix:** Fit a backup cell (the SparkFun board has an MS621FE), use OTP, re-send config at every gpsd start, or choose a flash-equipped part (NEO-F10N, BE-126). The LC76G does save to NVM with $PAIR513.
    - **Fix sources:**
      - https://community.sparkfun.com/t/adding-configuration-flash-memory-to-sparkfun-gnss-receiver-breakout-max-m10s/65405
      - https://forums.quectel.com/t/significant-periodic-1pps-noise-with-lc76g-module/57109
  12.
    - **Problem:** Unit-to-unit quality variance and misleading listings: a faulty magnetometer axis, a heat-damaged MMC5983MA board, and AliExpress BNO085 listings described as 'very misleading'.
    - **Affected products:** BNO086 (SparkFun), MMC5983MA (SparkFun), AliExpress 'BNO085' boards
    - **Frequency:** occasional
    - **Known fix:** Buy from Adafruit/SparkFun or established sellers with returns.
  - On arrival, check that field magnitude stays constant while rotating and that Rotation Vector heading matches a known reference.
  - No-name BNO08x boards default to address 0x4B.
    - **Fix sources:**
      - https://community.sparkfun.com/t/bno086/62015
      - https://community.sparkfun.com/t/mmc5983ma-doesnt-seem-to-work-properly/46529
      - https://docs.slimevr.dev/diy/imu-comparison.html
      - https://wolles-elektronikkiste.de/en/bno08x-9-dof-imus
  13.
    - **Problem:** A GNSS-disciplined system clock does not give accurate IQ or decode timestamps. SDR software pipelines add seconds-level error, and only the XTRX among Lime boards has PPS-synchronised sampling.
    - **Affected products:** SatNOGS/GNU Radio flowgraphs; LimeSDR Micro (no PPS timestamping); XTRX (partial)
    - **Frequency:** common
    - **Known fix:** Record the host time of the first sample at stream start (SoapySDR/LimeSuiteNG timestamps) and log the chrony state.
  - Accept ms-level accuracy.
  - True sub-µs IQ time needs SDR-side PPS latching, which the Micro does not have.
    - **Fix sources:**
      - https://community.libre.space/t/my-groundstation-clock-vs-satellite-clock/15370
      - https://discourse.myriadrf.org/t/limesdr-xtrx-hardware-timestamping-with-1-pps/12949
      - https://community.libre.space/t/tutorial-setup-gpsd-and-pulse-per-second-pps-for-satnogs-station-discipline-clock-getting-the-time-directly-from-the-satellites/15272
  14.
    - **Problem:** Lime GPSDO and external-reference features are undocumented or buggy. XTRX needs raw register writes. The Micro firmware's external-reference select writes the wrong expander register and silently stays on the TCXO.
    - **Affected products:** LimeSDR XTRX, LimeSDR Micro (basic and GNSS variants)
    - **Frequency:** occasional
    - **Known fix:** For XTRX: WriteRegister(0x0018, 0x0004) for the external clock, a square-wave reference, and R156 fitted on v1.3. For the Micro: wait for commit 1f70189 on master or build firmware with it.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/limesdr-xtrx-v1-3-reference-clock-and-pps/13045
      - https://github.com/myriadrf/LimeSDR-Micro_FW/issues/6
- **Unresolved problems:**
  1.
    - **Problem:** No public report of any GNSS module or IMU actually working on the Dragon Q6A 40-pin header under Linux. One user's UART TX does not work (Sept 2026), rsetup shows pin-state errors, and an I2C HAT on pins 27/28 is not responding (open issue).
    - **Evidence:** forum.radxa.com 31422 and 30455 #3 (unanswered); radxa-overlays issue #552 (open); the uart6 dtbo fix in 30063 was never published.
    - **Why it matters for us:** GNSS configuration needs TX: EPOC off, PPS always output, UBX/PAIR saves. The direct-I2C IMU path is unproven. Budget a USB fallback: USB-UART bridge for the GNSS, RP2040 USB bridge for the IMU.
  2.
    - **Problem:** Qualcomm GENI I2C behaviour with the BNO08x (clock stretching behind UM3204H/UM3304 translators) is untested by anyone.
    - **Evidence:** No Q6A/QCS6490 reports found. The closest analogue, Jetson Orin Nano, fails with Errno 121 (Adafruit #49/#56). Radxa notes the UM3304 limits SPI to ~30 MHz.
    - **Why it matters for us:** Wiring a BNO085 straight to I2C0/I2C2 may fail intermittently. Use the RP2040 bridge or SPI6 instead, both of which have positive evidence.
  3.
    - **Problem:** pps-gpio on the Q6A is unverified end to end. There is no overlay, the module exists only in the 7.0.11 kernel config, and edge latency through the header level translator is unknown.
    - **Evidence:** radxa-overlays has no PPS overlay. CONFIG_PPS_CLIENT_GPIO=m is in radxa_qcom_7_0_defconfig and absent in the 6.17.1/6.18.2 configs. The forum shows separate FastRPC/NPU problems on both 6.18.2-3 and 7.0.11-5 kernels.
    - **Why it matters for us:** Getting PPS may force a kernel choice that interacts with the NPU stack, and needs a self-written DT overlay. NMEA-only time (10-135 ms) is enough for passes and Doppler but not for µs logging.
  4.
    - **Problem:** The LimeSDR Micro GNSS variant gives the host neither position nor PPS, and no user has tested the basic board's J5 PPS input or external-reference input.
    - **Evidence:** LimeSDR-Micro_FW has only 2 issues. #6 shows external-reference select was silently broken until a fix linked on 16 Oct 2026 (not merged). XTRX threads show PPS sync and GPSDO are XTRX-gateware features.
    - **Why it matters for us:** Don't pay +$50 for the GNSS variant. Frequency accuracy for Doppler and QO-100 still relies on the Rakon VCTCXO, or on a disciplined 10 MHz into J4 once the firmware fix lands.
  5.
    - **Problem:** GNSS behaviour under Ukrainian EW spoofing is undocumented for hobby modules. That covers u-blox M10 spoofing flags in the field, and whether Quectel's regional lock ('will not work in Russia') could trigger on a spoofed position.
    - **Evidence:** Quectel forum 57394 (lock confirmed, mechanism unexplained). Kyiv Independent: Ukrainian EW changes phone time zones. NovAtel bulletin (seen via search, page 403): receivers in Ukraine reported future GPS week numbers and stopped tracking.
    - **Why it matters for us:** A spoofed or locked receiver could give a wrong QTH or time to chrony, Gpredict and SatDump. Add sanity checks: saved home QTH, maxchange limits in chrony, refuse jumps, NTP fallback. A u-blox with spoofing flags is a hedge, but its field performance here is unproven.
  6.
    - **Problem:** No quantified community data on compass error from a battery pack, fan and DC leads inside a handheld enclosure.
    - **Evidence:** SARCNET gives ±5° for a boom-mounted LSM303 and documents steel-screw errors. SlimeVR suggests ≤5 µT field fluctuation. No handheld SDR build with an in-case magnetometer was found.
    - **Why it matters for us:** Confirms the decision to put the IMU in a boom puck. Fine pointing at 2.2 GHz and 10 GHz (narrow beams) cannot rely on the compass; use sun or landmark alignment plus Game RV, then peak on signal.
  7.
    - **Problem:** BNO08x 9-DOF heading can jump tens of degrees while reporting accuracy 3, and nobody published a fix.
    - **Evidence:** Arduino forum 904696 (45-90° jumps), SparkFun 64830 (±150° spikes), SparkFun lib #18 (1-5° tilt error after yaw on RP2040).
    - **Why it matters for us:** The on-screen arrow needs outlier rejection, a Game RV mode, and an operator-set north offset. Do not trust the BNO's accuracy flag alone.
  8.
    - **Problem:** LC76G with gpsd on Linux is untested in this research: whether gpsd identifies it as generic NMEA or an MTK variant, and whether the Waveshare 'PPS (status indicator)' pin is a clean timing edge.
    - **Evidence:** Waveshare wiki marks PPS as 'GPS status indicator' and NC in demos, and its demos use 9600 baud though the LC76G defaults to 115200. gpsd #245 shows auto-switching to the MTK driver on a Quectel L76. The only LC76G timing report used a Raspberry Pi.
    - **Why it matters for us:** Verify with ppstest and gpsd -D before building. If needed, use gpsd -p or a fixed driver, and keep a scope check of the PPS edge after the Q6A level translator.
  9.
    - **Problem:** Alternative IMUs have little or no Linux-SBC community data: BMM350 boards (no reports found), LSM6DSV16X SFLP on Linux (one unanswered Pi 4 thread), and MMC5983MA, which has no kernel driver in the Radxa config.
    - **Evidence:** SparkFun 64170 (LSM6DSV16X SFLP on Pi, no solution). SlimeVR rates LSM6DSV ≈ BNO085 and BMI270 poor. Radxa 7.0.11 config has st_lsm6dsx, BMI270, BNO055 and MMC35240 drivers, but no BNO08x, ICM-20948, MMC5983 or BMM350.
    - **Why it matters for us:** For a host-fusion fallback, LSM6DSV16X (kernel IIO driver) + MMC5983MA (user space) is the best-supported pair. BMI270 + BMM350 carries the most integration risk.
- **Communities checked:**
  - forum.radxa.com (Discourse JSON search + topic reads)
  - GitHub radxa-pkg/radxa-overlays (issues, overlay sources) and radxa/kernel + radxa-pkg/linux-qcom (kernel config inspection)
  - docs.radxa.com (Q6A 40-pin GPIO page)
  - forums.quectel.com (LC76G, LC29H, LC86G topics)
  - community.sparkfun.com (MAX-M10S, SAM-M10Q, BNO086, MMC5983MA, LSM6DSV16X topics)
  - gpsd GitLab issue tracker (REST API; comments not accessible)
  - GitHub issues: adafruit/Adafruit_CircuitPython_BNO08x, sparkfun/SparkFun_BNO08x_Arduino_Library, tstellanova/bno080, bnbhat/bno08x_ros2_driver, xioTechnologies/Fusion (titles only), SatDump/SatDump, AlexandreRouma/SDRPlusPlus (no GPS issues), myriadrf/LimeSDR-Micro_FW
  - discourse.myriadrf.org (LimeSDR Micro/XTRX GNSS, PPS, GPSDO)
  - Crowd Supply LimeSDR Micro updates page
  - community.libre.space (SatNOGS GNSS/PPS and rotator compass threads)
  - forum.clockworkpi.com (uConsole AIO GPS + SDR handheld)
  - forum.arduino.cc
  - forum.core-electronics.com.au
  - forum.openmarine.net (pypilot ICM-20948; USB3/GPS interference via search)
  - time-nuts mailing list (febo.com archive)
  - Google Groups hbrobotics
  - SARCNET project pages (sarcnet.org)
  - PJRC project page
  - SlimeVR documentation
  - wolles-elektronikkiste.de (German maker blog, WP API)
  - Waveshare wiki (LC76G)
  - Kyiv Independent / NovAtel / Defense News via WebSearch (EW/spoofing context)
  - Reddit: unreachable (WebFetch refused for www.reddit.com and old.reddit.com, curl gets a bot-block page; site:reddit.com searches returned no Reddit results)
  - Not reachable: forum.allaboutcircuits.com (403), mikrocontroller.net (403), novatel.com bulletin (403), hackaday.io search (login wall), GitHub REST API (blocked in this session; used github.com pages instead)
  - Searched with no relevant results: EEVblog (site search), Armbian forum (via search)
  - Not checked (budget): BATC forum, AMSAT-UK/AMSAT-DL, Ubuntu Discourse, Qualcomm developer forum, CNX Software comments, Ukrainian-language forums
- **Recommendation impact:** Community evidence supports the researcher's overall direction: a UART GNSS with PPS, plus a BNO08x in an antenna-boom puck behind an MCU bridge. Several details change.
  
  GNSS:
  - The LC76G is confirmed as a timing-grade receiver (<100 ns RMS in a real stratum-1 build), but only on UART. Its I2C mode is a clock-stretching mailbox protocol that gpsd cannot use.
  - Configure it once: EPOC off ($PAIR496,0 + $PAIR513), $PAIR753,1, 'PPS always output'. This needs a working TX line.
  - Q6A TX is not guaranteed (open forum report), so check UART6 (/dev/ttyHS1) with a loopback first. Keep a CP2102/CH340 USB-UART on a USB 2.0 port as a fallback; PPS can then use the DCD line or the GPIO.
  - pps-gpio exists as a module only in Radxa's 7.0.11 kernel config (not in 6.17/6.18), and there is no PPS overlay. Plan a custom overlay and a kernel decision.
  - The budget ATGM336H is better than assumed: time-nuts measured 10-20 ns PPS variation, so it is fine for chrony.
  - Integrated-antenna boards (SAM-M10Q, Matek) are a poor fit next to the Q6A, LimeSDR, HDMI and DC-DC. Use an external active patch on a ≥12 cm ground plane, away from USB 3, HDMI and the converters.
  - Never put GNSS on the debug UART (pins 8/10).
  - Use gpsd ≥3.24 with -n (and -p if needed).
  
  LimeSDR Micro GNSS variant: confirmed redundant. There is no host path, and the basic board's external-reference select was itself silently broken until an unmerged October 2026 fix. Skip the +$50.
  
  Timestamps: PPS will give ~1 µs system time, but SatNOGS users show SDR and decoder timestamps stay at ms to s level unless the SDR latches PPS, and the Micro does not. Treat the 'PPS improves IQ timestamps' benefit as minor.
  
  IMU:
  - Strong, repeated evidence that BNO08x I2C fails on Linux hosts (Pi, Jetson, ESP32, Renesas). This reinforces the RP2040 bridge; Adafruit lists RP2040 as a good host.
  - Use the CEVA SH-2 based Arduino library, not CircuitPython. Wire INT/RST, set the I2C buffer ≥128 B, and power from clean 3.3 V (RP2040 tilt errors were tied to supply noise).
  - SPI6 on the Q6A is a proven fallback.
  - Expect about ±5° compass pointing at best (SARCNET, boom-mounted, brass screws). BNO08x 9-DOF heading can jump while reporting accuracy 3.
  - The UI should offer a sun/landmark 'set north' mode with Game Rotation Vector tracking, plus outlier rejection.
  - For host fusion or a cheaper second source, LSM6DSV16X (kernel st_lsm6dsx driver present) + MMC5983MA is the best-supported fallback; SlimeVR rates LSM6DSV ≈ BNO085. De-prioritise BMI270 + BMM350 (poor or no community data).
  - Buy BNO08x from Adafruit/SparkFun or other established sellers with returns; SlimeVR calls AliExpress BNO085 listings misleading.
  
  EW risk: add spoofing and geofence sanity checks before GNSS data feeds Gpredict, SatDump or chrony (home-QTH fallback, chrony maxchange, NTP fallback).
  
  Confidence: medium. The Q6A-specific GNSS/IMU path is undocumented by any user.

## Власні виправлення (`fixes`)

_Run `wf_45d278c2-004`_

- **Component:** GNSS receiver + IMU/compass (location, time, on-screen antenna pointing) on Radxa Dragon Q6A
- **Fixes:**
  1.
    - **Problem:** Nobody has publicly reported a GNSS module or IMU working on the Dragon Q6A 40-pin header. Reported symptoms: UART TX not working (forum 31422), rsetup pin-state errors (30455 #3), an I2C HAT on pins 27/28 not answering (radxa-overlays #552), and a uart6 dtbo fix that was never published (30063).
    - **Proposed fix:** Treat the header as a known-electrical, unknown-software interface and bring it up in stages, each with a pass/fail gate. Choose pins by which level translator sits behind them. Schematic v1.21, sheet 26 (my reading):
  - U48 UM3204H: pins 3/5/16/18. Open-drain/TXS-type with internal 10 kOhm pull-ups and a one-shot edge accelerator. I2C is OK. Outputs are weak when high.
  - U47 UM3204H: pins 8/10/27/28.
  - Q12/Q13 CJ3134K MOSFET shifters with 10 kOhm pull-ups (the classic I2C shifter): pins 13/15 (I2C0).
  - UM3304 (TXB-type, 4 kOhm output buffers, max 50 pF load, needs pull resistors >50 kOhm, not usable for I2C): pin 7 and SPI7/UART7 pins 11/29/31/32, plus SPI12, SPI14 and MI2S pins.
  
  Recommended pin plan:
  - GNSS on UART6: pin 16 TX, pin 18 RX, with the official uart6 overlay.
  - PPS on pin 7 (GPIO96). It is free in the mainline DT. Pin 37/GPIO58 is NOT free: spi14 is enabled by default on GPIO56-59.
  - Any direct I2C sensor on I2C0, pins 13/15.
  - Keep header wires under about 20 cm.
  
  Keep a USB fallback ready: an FT232RL module with DCD for the GNSS, and the RP2040 bridge for the IMU. For time-stamping in this project, USB PPS (±1 ms) is still good enough.
    - **Steps:**
      - Find which translator each signal uses before wiring. TX through U48 is high only via a 10 kOhm pull-up, so any load below about 100 kOhm, or a second driver on the line (for example an ESP32 RX that is shared with an on-board USB-UART TX, my hypothesis for forum 31422), will break TX. GNSS RX inputs such as the Waveshare LC76G (direct module pin, no pull-ups) are fine.
      - Enable the UART6 overlay with sudo rsetup → Overlays. It disables i2c6/spi6 and muxes only gpio26/27. Reboot. Confirm with: ls -l /dev/ttyHS*; dmesg | grep -i 998000; cat /proc/device-tree/soc@0/geniqup@9c0000/serial@998000/status (use ls /proc/device-tree/soc@0 to find the node name). Ports appear as ttyHS1/ttyHS2, not ttyS6 (forum 30455).
      - Create a stable name with /etc/udev/rules.d/60-gnss.rules: SUBSYSTEM=="tty", KERNELS=="998000.serial", SYMLINK+="gnss0". For UART7 use 99c000.serial.
      - Check the pin mux in debugfs rather than rsetup's pin-state view: sudo cat /sys/kernel/debug/pinctrl/*f100000*/pinmux-pins | grep -E 'gpio(2[4-7]|96) '. gpio26/27 should show function qup06 owned by 998000.serial. Note that mainline gpio-line-names mislabels GPIO27 as "PIN_27"; it is physically pin 18.
      - Loopback test with nothing else connected: jumper pin 16 to pin 18, run stty -F /dev/gnss0 115200 raw -echo -crtscts; cat /dev/gnss0 & printf 'hello\r\n' > /dev/gnss0. If loopback works but a target does not receive, it is a load problem. Measure the idle-high voltage at pin 16 with the target connected (it should be >2.4 V). The fix is a 74LVC1G125 or 74LVC1G17 buffer powered from header 3V3, between pin 16 and the target (cents in cost).
      - If loopback fails, copy qcs6490-radxa-dragon-q6a-uart6.dtso from radxa-overlays. Add a pin config: &qup_uart6_tx { drive-strength = <8>; bias-disable; }; &qup_uart6_rx { bias-pull-up; };. Base kodiak.dtsi sets neither for uart6. The qcom,enable-gsi-dma line is a no-op in the 6.18 GENI drivers (grep finds no user), so it is not the cause. Compile with dtc -@ -I dts -O dtb and install with rsetup → Overlays → install 3rd-party overlay. Verify the menu name on your image.
      - I2C: GENI I2C advertises no SMBus Quick (i2c-qcom-geni.c: I2C_FUNC_SMBUS_EMUL & ~I2C_FUNC_SMBUS_QUICK). So plain 'i2cdetect -y N' silently skips 0x03-0x2F, 0x38-0x4F and 0x60-0x77, which hides the BNO08x (0x4A/0x4B), ICM-20948 (0x68), LSM6DS (0x6A/0x6B) and the Argon fan HAT (0x1A). Always use 'i2cdetect -y -r N'. This probably explains issue #552.
      - USB fallback for GNSS: FT232RL module (Prom.ua/AliExpress, price not verified, roughly $3-8). Wire GNSS TX→RXD, RX→TXD and PPS→DCD. Run gpsd on /dev/ttyUSB0. gpsd timestamps DCD edges itself, and pps-ldisc (CONFIG_PPS_CLIENT_LDISC=m) is only in the Radxa 7.0 config. Expect about ±1 ms (full-speed USB).
      - Fallback for the IMU: RP2040 USB-CDC puck (see the IMU fixes). It needs only a USB 2.0 port and no header at all.
    - **How to verify:** Gate 1: pin16↔18 loopback echoes at 115200 and at 921600.
  Gate 2: with the GNSS connected, gpspipe -w shows TPV mode 3, and a configuration command ($PQTMVERNO*58) gets a $PQTMVERNO reply. That proves TX works.
  Gate 3: 'i2cdetect -y -r 0' shows the sensor address.
  Gate 4: a 24 h soak with no 'geni' errors in dmesg.
  Scope or logic-analyzer check: pin 16 idle high ≥3.0 V unloaded, and ≥2.4 V with the target connected.
    - **Confidence:** medium
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://www.union-ic.com/upload/Datasheet/Datasheet_UM3204_Rev16.pdf
      - https://www.union-ic.com/upload/Datasheet/Datasheet_UM3304_Rev16.pdf
      - https://github.com/radxa-pkg/radxa-overlays/tree/main/arch/arm64/boot/dts/qcom/overlays
      - https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/kodiak.dtsi
      - https://raw.githubusercontent.com/torvalds/linux/master/drivers/i2c/busses/i2c-qcom-geni.c
      - https://git.kernel.org/pub/scm/utils/i2c-tools/i2c-tools.git/plain/tools/i2cdetect.c
      - https://forum.radxa.com/t/31422
      - https://forum.radxa.com/t/30455
      - https://forum.radxa.com/t/30063
      - https://github.com/radxa-pkg/radxa-overlays/issues/552
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/pin-gpio
      - https://gpsd.gitlab.io/gpsd/gpsd-time-service-howto.html
  2.
    - **Problem:** Nobody has tested the BNO08x on Qualcomm GENI I2C behind the Q6A header translators. The BNO08x needs clock stretching, and the closest analogue (Jetson) fails with Errno 121.
    - **Proposed fix:** Make the GENI question irrelevant for the main build by running the BNO08x on an RP2040 that talks to the Q6A over USB-CDC. The RP2040 runs the CEVA sh2 driver from the Adafruit or SparkFun library, and its DesignWare I2C supports stretching.
  
  If you want a direct Q6A link (bench work, or a case-mounted sensor), the root cause and its fix are in the datasheet:
  - A polled BNO085 with no data 'will stretch the clock until it has data to send'. GENI aborts a transfer after XFER_TIMEOUT = 1 s.
  - A polled BNO086 instead returns zero-length packets.
  - The BNO08x does not support repeated start.
  
  So for a direct link: use a BNO086, read only when H_INTN is low, use separate write and read transactions, and put it on I2C0 (pins 13/15), which has the MOSFET shifter. If I2C still fails, use UART-SHTP at 3 Mbaud on UART7. The UM3304 behind it is rated at 24 Mbps push-pull.
    - **Steps:**
      - Main path, puck: RP2040-Zero plus BNO086/085. Run the BNO in SPI mode (no stretching at all) or in I2C mode with INT→GP and RST→GP. Use the arduino-pico core and Adafruit_BNO08x.
      - Puck firmware: enable SH2_ARVR_STABILIZED_RV (0x28), SH2_GAME_ROTATION_VECTOR (0x08) and SH2_MAGNETIC_FIELD_CALIBRATED (0x03) at 20 ms. On bno.wasReset(), re-enable all reports. Print one CSV line per report: sensorId, status, i, j, k, real, accuracy_rad, mag x/y/z. Accept host commands that map to sh2_setCalConfig(), sh2_saveDcdNow(), sh2_setDcdAutoSave() and sh2_setTareNow().
      - On the Q6A the puck appears as /dev/ttyACM0 (CONFIG_USB_ACM=m is in the 6.18 and 7.0 configs). Add a udev SYMLINK on the RP2040 serial number.
      - Direct path, pin plan with UART6 used for GNSS: BNO SDA→pin 13, SCL→pin 15 (I2C0, CJ3134K MOSFET shifter, 10 kOhm pull-ups on both sides), H_INTN→pin 3 (GPIO24), NRST→pin 5 (GPIO25). Pins 3/5 go through UM3204H, which tolerates the breakout's pull-ups; UM3304 pins need pulls >50 kOhm. Enable the i2c0 overlay (100 kHz). The BNO allows up to 400 kHz.
      - Direct-path software: wait for the INT falling edge (libgpiod), then os.read() the 4-byte SHTP header and then the full packet length with plain read()/write() on /dev/i2c-0. Never use I2C_RDWR combined messages, because those use repeated start.
      - Check timing with a $10 FX2 logic analyser (sigrok/PulseView, 24 MS/s) on the 3.3 V side: record SCL-low stretch durations during a 1 h capture. They must stay well under 1 s.
      - If I2C still errors: set PS1=1/PS0=0 for UART-SHTP, wire to UART7 (pin 32 TX, pin 29 RX; enable the uart7 overlay), and run at 3,000,000 baud. The datasheet requires the external crystal for UART. Feasibility: 48 MHz = 16×3 Mbaud is a standard GENI SE clock, but this is untested on the Q6A.
    - **How to verify:** Puck: 24 h stream at 50 Hz with zero sequence gaps (check SHTP sequence numbers) and no unexpected resets.
  Direct I2C: 24 h soak at 100 kHz and then at 400 kHz with zero -EREMOTEIO/-ETIMEDOUT/'geni' errors in dmesg, and a logic-analyser capture showing stretch at most a few ms.
  UART-SHTP: product-ID response and a 1 h stream with no checksum errors.
    - **Confidence:** high
    - **Sources:**
      - https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf
      - https://raw.githubusercontent.com/torvalds/linux/master/drivers/i2c/busses/i2c-qcom-geni.c
      - https://raw.githubusercontent.com/adafruit/Adafruit_BNO08x/master/src/sh2.h
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://www.union-ic.com/upload/Datasheet/Datasheet_UM3304_Rev16.pdf
      - https://raw.githubusercontent.com/radxa/kernel/linux-7.0.11/arch/arm64/configs/radxa_qcom_7_0_defconfig
  3.
    - **Problem:** pps-gpio on the Q6A is unverified end to end. There is no overlay, CONFIG_PPS_CLIENT_GPIO=m exists only in the 7.0.11 config, switching kernels may break the NPU (FastRPC), and the latency through the translator is unknown.
    - **Proposed fix:** Avoid changing kernels.
  
  Route A (recommended): a 30-line user-space PPS daemon. It requests GPIO96 (pin 7) with the GPIO character device v2 API, rising edge and CLOCK_REALTIME event timestamps. The kernel stamps the edge in the hard IRQ, the same place pps-gpio does. The daemon sends chrony a SOCK 'pulse' sample. This works on 6.18 and 7.0 and needs no DT change. It also makes gating against spoofing easy.
  
  Route B: a DT overlay plus pps-gpio. On 7.0 the module already exists. On 6.18, build drivers/pps/clients/pps-gpio.c out-of-tree; CONFIG_PPS is built in because PTP_1588_CLOCK selects PPS.
  
  Translator delay: UM3304/UM3204 push-pull tPLH is about 5-7 ns, which is negligible against 5-20 µs of IRQ latency.
  
  Overall requirement: LimeSDR buffers are host-stamped with ms-level jitter anyway, so even NMEA-only time is adequate. PPS matters mainly for the VCTCXO calibration in the LimeSDR fix.
    - **Steps:**
      - Wiring: LC76G board pin 5 '1PPS' → Q6A pin 7. The Waveshare schematic shows it is the module's 1PPS pin directly; the LED is driven separately through a 1 kOhm/SI2306. Connect GND to pin 9. Keep the wire under 20 cm because UM3304 is limited to 50 pF.
      - Find the chip with gpiodetect: it is the TLMM f100000.pinctrl, which Radxa docs show as /dev/gpiochip4. Then run gpiomon or gpioinfo to confirm line 96 is unused.
      - Route A: python3 -m venv /opt/pps && /opt/pps/bin/pip install gpiod. Use the PyPI 2.x bindings; Ubuntu 24.04's python3-libgpiod is 1.6.3 (v1 API, monotonic stamps only).
      - Route A daemon core: req = gpiod.request_lines('/dev/gpiochip4', consumer='pps', config={96: gpiod.LineSettings(edge_detection=Edge.RISING, bias=Bias.DISABLED, event_clock=Clock.REALTIME)}). For each event: sec, ns = divmod(ev.timestamp_ns, 10**9); usec = ns // 1000; f = usec / 1e6; off = -f if f < 0.5 else 1 - f. Then sock.sendto(struct.pack('qqdiiii', sec, usec, off, 1, 0, 0, 0x534F434B), '/run/chrony.pps0.sock'). That is a 40-byte struct sock_sample with pulse=1. Send only while the gnss-gate flag is OK (see the spoofing fix). Run it as a root systemd service.
      - chrony (/etc/chrony/conf.d/gnss.conf): refclock SHM 0 refid NMEA offset 0.1 delay 0.2 noselect, and refclock SOCK /run/chrony.pps0.sock refid PPS lock NMEA precision 1e-6 maxlockage 2.
      - Route B overlay (pps-pin7.dts): /dts-v1/; /plugin/; &{/} { pps-gnss { compatible = "pps-gpio"; gpios = <&tlmm 96 0>; pinctrl-names = "default"; pinctrl-0 = <&pps_gnss_pin>; }; }; &tlmm { pps_gnss_pin: pps-gnss-pin-state { pins = "gpio96"; function = "gpio"; bias-disable; }; };. Use bias-disable because UM3304 needs pulls >50 kOhm.
      - Route B on 6.18: apt install linux-headers-$(uname -r) (Radxa repo; package availability not verified). Download pps-gpio.c from the v6.18 tag, add a Makefile containing 'obj-m += pps-gpio.o', run make -C /lib/modules/$(uname -r)/build M=$PWD, install the module and run depmod -a. Then use refclock PPS /dev/ppsN lock NMEA. Check /sys/class/pps/*/name to pick the right N.
    - **How to verify:** Route A: chronyc sources -v shows PPS as '*' after about 10 min, and chronyc sourcestats shows a PPS std-dev of a few µs to about 20 µs.
  Route B: ppstest /dev/ppsN prints one assert per second with sequence numbers.
  All routes: scope pin 7 and confirm a clean 3.3 V edge with rise under 50 ns and no double-triggering. Unplug the antenna and confirm PPS stops (in PAIR752 mode 2) and chrony stops selecting PPS.
  Run the NPU demo before and after to prove the timing stack does not touch FastRPC.
    - **Confidence:** medium
    - **Sources:**
      - https://gitlab.com/chrony/chrony/-/raw/master/refclock_sock.c
      - https://chrony-project.org/doc/4.5/chrony.conf.html
      - https://packages.ubuntu.com/noble/python3-libgpiod
      - https://raw.githubusercontent.com/radxa/kernel/linux-7.0.11/arch/arm64/configs/radxa_qcom_7_0_defconfig
      - https://github.com/radxa/kernel/tree/linux-6.18.2
      - https://files.waveshare.com/wiki/LC76G/manual/LC76G%20GNSS%20Module.pdf
      - https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://www.union-ic.com/upload/Datasheet/Datasheet_UM3304_Rev16.pdf
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/pin-gpio
  4.
    - **Problem:** The LimeSDR Micro GNSS variant gives the host neither position nor PPS. Nobody has tested the J5 PPS input or the J4 external reference input. External-reference select was broken until a fix that is linked but not yet merged.
    - **Proposed fix:** Buy the basic board ($249); the +$50 GNSS variant adds nothing today. Firmware (commit 13628a9, 9 Oct 2026) confirms this:
  - vPhyTimerPPSINEnable() is never called, and the PPS_IN handler is an empty stub.
  - The GNSS pin is read only as GNSS_FIX on the MCP23017.
  - The VCTCXO DAC (I2C 0x4C) loads from EEPROM 0xFFFE at boot; the default 0xA1B8 is written when unset.
  
  For frequency accuracy, calibrate the VCTCXO DAC once against the GNSS-disciplined host clock and store it in EEPROM. LimeSuiteNG exposes custom parameter 0 'VCTCXO DAC (volatile)' and the EEPROM region 'XO_DAC' (0xFFFE, 2 bytes). Use J4 only after commit 1f70189 is merged. The MCP23017 write went to INTCONB (0x09) instead of OLATA (0x14).
    - **Steps:**
      - Measure: with chrony locked to GNSS PPS for more than 1 h, run a SoapySDR Python RX stream (driver=limesuiteng, 30.72 Msps) for 30-60 min. For each readStream, log the host clock_gettime(CLOCK_REALTIME) and the buffer timeNs. Hardware time is sample-tick based (getHardwareTime = ticks at the nominal rate), so a linear fit of hw_ns against host_ns gives the fractional frequency error = slope − 1.
      - Expected precision: about 1 ms host jitter, ~1e5 buffers and 3600 s give a slope σ of about 3e-9. The PPS-disciplined host frequency error should be ≤1e-8. Drop any run with overflow ('O') events.
      - Find the DAC sensitivity: set DAC = current ±2000 LSB with CustomParameterWrite({{0, value}}) (C++ API or limeGUI board controls; GUI location not verified) and re-measure. The finding implies about ±5 ppm over 16 bits, i.e. about 0.15 ppb/LSB. Measure it instead of assuming.
      - Pick the DAC value for zero error and persist it: MemoryWrite to EEPROM region 'XO_DAC' (0xFFFE), uint16 little-endian. Power-cycle and confirm the firmware log 'XO_DAC set to (N)'.
      - Cross-check over the air, optional: run srsRAN 4G cell_search with the Soapy RF (LTE band 3, 1800 MHz). 3GPP wide-area eNB accuracy is ±0.05 ppm. The reported CFO should be within ±100 Hz.
      - J4: after a firmware build containing 1f70189, run limeConfig --refclk 10e6 --refclk_source external (flags verified in cli/limeConfig.cpp) with a GPSDO's 10 MHz input. Re-run the regression and expect under 0.01 ppm; switching to internal should restore the old offset.
      - J5/GPSDO: no host-visible use until firmware enables PPS_IN. A DIY loop is possible but unproven: PPS_IN capture → count phytimer ticks per second → PI loop on SetXODAC. Mark it a firmware project. For QO-100, correct the LNB+SDR together on the beacon as usual.
    - **How to verify:** The residual error after the DAC write is below 0.05 ppm (110 Hz at 2.2 GHz, 37 Hz at a 740 MHz IF), repeatable across cold and warm boots within the Rakon ±50 ppb temperature spec. LTE CFO or a known GSM/LTE carrier agrees within ±0.1 ppm.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/myriadrf/LimeSDR-Micro_FW
      - https://github.com/myriadrf/LimeSDR-Micro_FW/issues/6
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/clock.html
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
  5.
    - **Problem:** Nobody has documented how hobby GNSS modules behave under Ukrainian EW spoofing. Quectel firmware reportedly will not work in Russia, which could trigger on a spoofed position. A spoofed or locked receiver could feed a wrong QTH or time to chrony, Gpredict and SatDump.
    - **Proposed fix:** Gate GNSS before it reaches chrony or the apps, and anchor time to an independent source. The Q6A has a discrete RTC: RS4C411 (DT 'st,m41t11' on i2c10 @0x68) with a VBAT input. Fit its backup cell; check the connector on schematic sheet 18.
  
  A 'gnss-gate' daemon reads gpsd JSON and opens the PPS path to chrony only when every rule passes. Rules:
  - time within ±120 s of the RTC;
  - date inside the window set by the newest TLE epoch (−2 d to +60 d);
  - position within 100 km of the saved QTH unless the operator confirms a move;
  - fix mode 3 with ≥6 satellites;
  - no EW flags.
  
  EW flags available:
  - LC76G: $PAIR391,1*2C enables $PAIRSPF jamming status (1 good, 2 warning, 3 critical); $PQTMJAMMINGSTATUS is also available.
  - u-blox M10 (SPG 5.10): UBX-NAV-STATUS flags2.spoofDetState (2/3 = spoofing) and UBX-MON-RF jammingState with CFG-ITFM-ENABLE=1.
  
  Pass prediction tolerates kilometres of QTH error and about 1 s of time error, so the gate only needs to catch gross spoofing (hours or days, week jumps, positions in another country).
  
  A Quectel regional lockout fails safe: no fix means the gate keeps the saved QTH and chrony free-runs on the RTC-seeded clock.
    - **Steps:**
      - Fit the RTC backup cell. Enable rtcsync in chrony. Confirm hwclock -r is correct after 24 h unpowered.
      - chrony: maxchange 5 1 -1 (after the first update, never accept a >5 s correction; -1 means never exit). Keep NMEA as noselect, with PPS fed only by the gated SOCK daemon. Add pool servers for when Wi-Fi is up: with 3 or more NTP sources, chrony rejects a spoofed refclock as a falseticker.
      - gnss-gate.py: connect to gpsd at localhost:2947 and send ?WATCH={"enable":true,"json":true,"raw":1} (raw mode passes $PAIRSPF through). Apply the rules and write /run/gnss-gate/state (OK/HOLD/EW). Only in the OK state does the PPS daemon forward pulses, and SatDump/Gpredict get a fresh QTH file. Otherwise they keep the last good QTH.
      - LC76G startup script (ExecStartPre of gpsd, because it is not known whether PAIR391 survives a save): send $PAIR391,1*2C and $PQTMCFGMSGRATE,W,PQTMJAMMINGSTATUS,1,1*11.
      - u-blox option: ubxtool -z CFG-ITFM-ENABLE,1 -z CFG-MSGOUT-UBX_NAV_STATUS_UART1,1. Parse NAV-STATUS with pyubx2, or forward it through the gpsd raw stream.
      - Write the last good time and position to /var/lib/gnss-gate on every OK epoch. On boot, refuse GNSS time earlier than the last saved time.
      - Show the state on screen (green OK, amber HOLD, red EW) and log it with every IQ recording. This doubles as an EW monitor.
    - **How to verify:** Bench replay without RF transmission (receive-only project): feed gpsd recorded or hand-edited NMEA through a pty (gpsfake) with (a) the date shifted +1024 weeks, (b) the position moved 500 km, (c) $PAIRSPF,3. Each must switch the gate to HOLD/EW, and chronyc tracking must show no step.
  Field: cover the antenna and confirm the PAIRSPF/NAV-STATUS fields change. Compare GNSS time with RTC and NTP when online.
    - **Confidence:** medium
    - **Sources:**
      - https://forums.quectel.com/uploads/short-url/rUEismNTHFHWMMyJR1WxrcTaRB7.pdf
      - https://cdn.sparkfun.com/assets/f/1/2/9/e/u-blox-M10-SPG-5.10_InterfaceDescription_UBX-21035062.pdf
      - https://chrony-project.org/doc/4.5/chrony.conf.html
      - https://forums.quectel.com/t/57394
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://gpsd.gitlab.io/gpsd/gpsd.html
  6.
    - **Problem:** There is no quantified community data on compass error from a battery pack, fan and DC leads inside a handheld enclosure.
    - **Proposed fix:** Quantify it yourself with the BNO08x's own magnetometer stream and a load-switching protocol, then set placement rules from the numbers.
  
  Reference field from WMM (Oct 2026):
  - Kyiv: H = 19.45 µT, F = 51.05 µT, I = 67.6°, D = +8.5°.
  - Odesa: H = 21.6 µT.
  
  A perpendicular disturbance ΔB gives a heading error of atan(ΔB/H), about 2.95° per µT in Kyiv.
  
  Biot-Savart for wires:
  - A single 4 A wire at 5 cm gives 16 µT (about 40° worst case).
  - The same current in a 2 mm-spaced pair falls off as 1/r²: 0.64 µT at 5 cm (≈1.9°) and 0.04 µT at 20 cm (≈0.1°).
  - USB 5 V at 50 mA in a cable 2 mm apart: about 0.2 µT at 1 cm.
  
  Rules that follow: keep the magnetometer in the boom puck at least 15-20 cm from cells, fan and LNA. Run all DC as twisted pairs, with no single-wire returns through the chassis. Use coax-only returns for bias-tee current. Use brass or nylon hardware.
    - **Steps:**
      - Fix the puck on a non-magnetic jig (wood or plastic). Stream SH2_MAGNETIC_FIELD_UNCALIBRATED (or the RM3100/MMC5983 equivalent) at 50 Hz to a CSV.
      - Record 60 s per state: (0) puck alone on a power bank; (1) Q6A idle at distance d; (2) LimeSDR at 56 Msps plus NPU stress (maximum battery current); (3) fan on/off; (4) LNA bias-tee on/off; (5) LNB 13 V injector on/off (if used).
      - Repeat at d = 5, 10, 20 and 40 cm and fit |ΔB|(d) to find the 1/r² or 1/r³ falloff. Compute Δheading = atan2 of the horizontal ΔB component against H = 19.4 µT.
      - Acceptance: every switching step must give |ΔB_h| < 0.3 µT (<1°), plus any static offset that the calibration can absorb. If a step fails, increase the distance or twist and reroute the leads, then re-test.
      - Static ferrous parts that move with the antenna (WB2HOL steel tape elements, brackets) are soft or hard iron. Calibrate with the antenna attached, once per antenna, and keep one DCD per antenna.
    - **How to verify:** After the fixes, heading against a sun-sight reference (skyfield sun azimuth from GNSS time and position) stays within ±3° through the full load cycle. Logged |B| stays within ±2% of 51.0 µT and dip within ±2° of 67.6° (Kyiv).
    - **Confidence:** high
    - **Sources:**
      - https://www.ncei.noaa.gov/products/world-magnetic-model
      - https://pypi.org/project/pygeomag/
      - https://ardupilot.org/copter/docs/common-magnetic-interference.html
      - https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf
  7.
    - **Problem:** BNO08x 9-DOF heading can jump tens of degrees while still reporting accuracy 3 (Arduino forum 904696, SparkFun 64830, SparkFun lib #18), and nobody has published a fix.
    - **Proposed fix:** Do not trust the 2-bit status alone; build a disturbance-aware display from data the BNO already provides.
  (1) Use the AR/VR-Stabilized Rotation Vector (0x28). CEVA designed it to suppress sudden heading corrections.
  (2) Gate on the Rotation Vector's own heading accuracy estimate in radians (sh2_RotationVectorWAcc_t.accuracy, SparkFun getQuatRadianAccuracy).
  (3) Detect magnetic disturbance independently: compare |B| from Magnetic Field Calibrated with WMM F, and the dip angle (between gravity and B) with WMM I.
  (4) Display Game RV yaw plus a slowly updated offset, learned only during clean epochs. Game RV is gyro-only with 0.5°/min drift spec and cannot jump magnetically.
  (5) After a good calibration, freeze magnetometer dynamic calibration with sh2_setCalConfig(SH2_CAL_ACCEL|SH2_CAL_GYRO) and sh2_setDcdAutoSave(false) after sh2_saveDcdNow(). CEVA notes that dynamic magnetometer calibration can cause jumps.
  (6) Offer a sun-sight button that sets the offset from the sun's azimuth, bypassing magnetics completely. Elevation always comes from gravity.
    - **Steps:**
      - Puck firmware: report ARVR-RV (0x28), Game RV (0x08) and Magnetic Field Calibrated (0x03) at 50 Hz, including the status and accuracy fields. Report every reset.
      - Calibration: rotate through all axes until magnetometer status = 3 and the RV accuracy is below 0.06 rad (3.5°). Check |B| = F ±3% and dip = I ±2°. Then call sh2_saveDcdNow(), sh2_setCalConfig(SH2_CAL_ACCEL|SH2_CAL_GYRO) and sh2_setDcdAutoSave(false). Store one DCD per antenna.
      - Host filter, clean epoch = all of: RV accuracy < 0.087 rad; mag status ≥ 2; ||B| − F| < 2.5 µT; |dip − I| < 3°; gyro rate < 30°/s. Only in clean epochs: offset ← circular low-pass of (yaw_ARVR − yaw_game) with τ = 10-20 s. Otherwise freeze the offset.
      - Displayed true azimuth = yaw_game + offset + WMM declination (pygeomag at the GNSS fix; +8.5° in Kyiv). Show an amber 'magnetic disturbed' badge when the epoch is not clean.
      - Outlier guard: if |yaw_ARVR − (yaw_game + offset)| > 15°, never step the display. Require more than 5 s of clean epochs before the offset may move more than 1°/s.
      - Sun-sight: put a gnomon pin on the puck aligned with the boom. When its shadow vanishes, press 'SUN'. Then offset = az_sun(skyfield, GNSS time and position) − yaw_game. Re-sight every 20-30 min (0.5°/min drift spec).
      - On a reset event (wasReset or a new product-ID packet): re-enable the reports, re-apply the calibration config, and hold the display until 3 s of clean epochs have passed.
    - **How to verify:** Tripod with a printed compass rose aligned by sun azimuth. Do 50 slews between 12 azimuths and 3 elevations, then 20 min of handheld motion near the battery pack.
  Count displayed heading steps >10° (target: 0) and compute RMS error (target ≤3°).
  Also log raw RV yaw to show the jumps the filter removed.
    - **Confidence:** medium
    - **Sources:**
      - https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf
      - https://raw.githubusercontent.com/adafruit/Adafruit_BNO08x/master/src/sh2.h
      - https://raw.githubusercontent.com/adafruit/Adafruit_BNO08x/master/src/sh2_SensorValue.h
      - https://raw.githubusercontent.com/sparkfun/SparkFun_BNO080_Arduino_Library/main/src/SparkFun_BNO080_Arduino_Library.h
      - https://forum.arduino.cc/t/904696
      - https://github.com/sparkfun/SparkFun_BNO08x_Arduino_Library/issues/18
      - https://pypi.org/project/pygeomag/
  8.
    - **Problem:** LC76G with gpsd on Linux is untested: gpsd may misidentify it or treat it as MTK, and Waveshare labels the PPS pin a 'status indicator'. Separately, some earlier advice (PPS 'always output', timing mode $PAIR753,1) is questionable.
    - **Proposed fix:** The Waveshare 24370 schematic shows header P1 pin 5 '1PPS' wired directly to module pin 4 (1PPS). The LED is driven separately through 1 kOhm into an SI2306 gate. TXD/RXD are direct 3.3 V module pins with no pull-ups. So the PPS is a real timing edge.
  
  Configure the module with documented PAIR/PQTM commands before starting gpsd. Then run gpsd in passive mode (-p, 'do not autoconfigure') at a fixed 115200 baud so it never sends MTK probes. The LC76G is Airoha-based and answers PMTK with PAIR001.
  
  Corrections to the earlier plan:
  - Use $PAIR752,2,100*39 (PPS only with a 3D fix), not 'Always'. 'Always' free-runs PPS from the RTC with no fix, which chrony would happily lock onto.
  - Do NOT enable $PAIR753 timing modes. Spec v1.4 defines 0, 2 (survey-in), 3 (position-hold) and 4 (delay); survey-in and position-hold assume a static antenna. The '1' from the forum is not in the spec.
  - Leave EPOC on for fast TTFF. Disabling it ($PAIR496,0*2D, forum-sourced) only reduces µs-level PPS noise.
    - **Steps:**
      - stty -F /dev/gnss0 115200 raw -echo -crtscts. Watch the replies with cat /dev/gnss0 & in a second shell.
      - Send: $PQTMVERNO*58 (log the firmware); $PAIR752,2,100*39 (PPS 3D-fix only, 100 ms); $PAIR066,1,1,1,1,0,0*3A (GPS+GLONASS+Galileo+BDS); $PAIR391,1*2C (jamming detect). Each PAIR command should be answered with $PAIR001,<cmd>,0.
      - Save: $PAIR513*3D at 1 Hz. If you raise the rate, follow the PAIR382/PAIR003/PAIR513/PAIR002 sequence from spec §2.4.49. Also send $PQTMSAVEPAR*5A for PQTM settings. Re-send PAIR391 at every boot from the gpsd ExecStartPre.
      - Debug run: gpsd -N -D 3 -n -p -s 115200 /dev/gnss0. Check gpsd --help on Ubuntu 24.04's gpsd 3.25 to confirm -p is present. Then: gpspipe -w | grep DEVICE should show the NMEA0183 driver and no MTK. cgps shows a 3D fix. ntpshmmon shows NTP0 samples.
      - Production: /etc/default/gpsd: DEVICES="/dev/gnss0", GPSD_OPTIONS="-n -p -s 115200", USBAUTO="false". Feed PPS by Route A or Route B from the PPS fix.
      - Calibrate the NMEA offset: after 1 h with PPS selected, read the NMEA refclock offset in chronyc sourcestats/sources (typically 50-150 ms at 115200) and put it into 'refclock SHM 0 ... offset X'.
    - **How to verify:** PPS present only with a 3D fix (cover the antenna and it stops). Scope at Q6A pin 7 shows a 100 ms-wide 3.3 V pulse whose rising edge coincides with the second. chrony selects PPS with std-dev in the µs range. gpsd stays on the NMEA0183 driver for 24 h, and settings survive a power cycle (backup cell fitted).
    - **Confidence:** medium
    - **Sources:**
      - https://files.waveshare.com/wiki/LC76G/manual/LC76G%20GNSS%20Module.pdf
      - https://forums.quectel.com/uploads/short-url/rUEismNTHFHWMMyJR1WxrcTaRB7.pdf
      - https://forums.quectel.com/t/gnss-lc76g-1-pss-configuration/45880
      - https://forums.quectel.com/t/significant-periodic-1pps-noise-with-lc76g-module/57109
      - https://forums.quectel.com/t/module-lc76g-does-not-respond-to-pmtk314-command/27199
      - https://gpsd.gitlab.io/gpsd/gpsd.html
      - https://gpsd.gitlab.io/gpsd/gpsd-time-service-howto.html
  9.
    - **Problem:** Alternative IMUs have little or no Linux-SBC community data. Radxa configs have no driver for the BNO08x, ICM-20948, MMC5983MA or BMM350, and nobody has answered the LSM6DSV16X SFLP-on-Linux question.
    - **Proposed fix:** Move sensor fusion into the RP2040 puck so the Linux driver question disappears. Any IMU then appears as one USB-CDC stream of quaternion + accuracy + |B|. Use x-io Fusion (C, magnetic rejection, runs on a Cortex-M0+) for non-BNO sensors.
  
  If you want host-side drivers anyway, use what both Radxa kernels actually ship:
  - CONFIG_IIO_ST_LSM6DSX=m in both 6.18 and 7.0. It supports LSM6DSO/LSM6DSOX/LSM6DS3TR-C/ISM330DHCX/LSM6DSV16X accel+gyro, but not SFLP.
  - A user-space LIS3MDL. CONFIG_IIO_ST_MAGN_3AXIS is not enabled, though st_lsm6dsx's sensor-hub code supports LIS2MDL/LIS3MDL if wired to the IMU's aux bus.
  
  Concrete boards: Pololu MinIMU-9 v6 (LSM6DSO + LIS3MDL), ~1,967 UAH, or Adafruit 5543 (LSM6DS3TR-C + LIS3MDL), ~2,404 UAH. Both are made-to-order on Prom.ua.
  
  Keep the BNO086 as first choice. BMI270+BMM350 remains the highest-risk combination.
    - **Steps:**
      - Puck firmware for non-BNO sensors: read the IMU at 200 Hz over I2C or SPI and the magnetometer at 50-100 Hz. Run FusionAhrsUpdate with magneticRejection ≈10° and recoveryTriggerPeriod of about 5 s. Calibrate the magnetometer with an ellipsoid fit (hard and soft iron) done on the host from a logged rotation, and flash the coefficients.
      - Host-side option: overlay node on &i2c0: imu@6b { compatible = "st,lsm6dso"; reg = <0x6b>; }. Then modprobe st_lsm6dsx_i2c and read /sys/bus/iio/devices/iio:deviceN. Read the LIS3MDL at 0x1e with smbus2 in Python and run imufusion (pip) on the host.
      - Use 'i2cdetect -y -r 0' when probing. 0x1e and 0x6b are in the ranges plain i2cdetect skips on GENI.
      - Run the same validation as the BNO fixes (|B| and dip checks, sun-sight comparison) so the two sensors can be compared.
    - **How to verify:** Same tripod and sun-sight test as the BNO fixes, run back to back with the BNO086 puck. Accept the alternative if RMS heading error is ≤3° and there are zero displayed jumps >10°.
  For the host path: iio_info or cat in_accel_x_raw works after a reboot with the overlay, and a 24 h read loop shows no I2C errors.
    - **Confidence:** medium
    - **Sources:**
      - https://raw.githubusercontent.com/radxa/kernel/linux-7.0.11/arch/arm64/configs/radxa_qcom_7_0_defconfig
      - https://github.com/radxa/kernel/tree/linux-6.18.2/drivers/iio/imu/st_lsm6dsx
      - https://github.com/xioTechnologies/Fusion
      - https://prom.ua/ua/search?search_term=LIS3MDL
      - https://git.kernel.org/pub/scm/utils/i2c-tools/i2c-tools.git/plain/tools/i2cdetect.c
- **Residual risks:**
  - Translator assignments come from my reading of schematic v1.21, sheet 26. Board revisions may differ, so confirm with a continuity meter before wiring.
  - Nothing here has been run on real Q6A hardware: the user-space PPS daemon, 3 Mbaud UART-SHTP, the out-of-tree pps-gpio build, and the availability of linux-headers for Radxa kernels are all unverified.
  - The 'rsetup pin-state error' (forum 30455 #3) and the exact content of the unpublished uart6 dtbo fix (30063) are still unknown. The TX-failure explanation (a weak 10 kOhm high from the UM3204H plus contention on the target) is a hypothesis that needs a voltmeter or scope to confirm.
  - Ubuntu 24.04 apt ships libgpiod 1.6.3. The PyPI gpiod 2.x wheel must build on aarch64, which I have not tested on the Q6A.
  - LimeSDR Micro: the custom-parameter and EEPROM APIs exist in LimeSuiteNG, but the GUI path, the DAC linearity and slope, and the claim that buffer timeNs is a hardware sample-count stamp all need checking on a real board. External reference works only after commit 1f70189 is merged and flashed. PPS-IN/GPSDO needs firmware development.
  - The LC76G PAIR391 setting may not persist after PAIR513, so it has to be re-sent at every boot. The jamming flags are vendor heuristics and are not validated against Ukrainian spoofers.
  - Detection of subtle spoofing (slow time or position drift within the gate limits) is not achievable with these receivers. The gate only catches gross attacks; OSNMA-capable receivers are out of budget.
  - Even with AR/VR stabilisation and gating, the BNO08x can still drift or jump during long passes. Sun-sight re-referencing every 20-30 min is assumed to be possible, which fails when it is overcast or dark (fall back to a landmark azimuth).
  - Prom.ua prices and stock (MinIMU-9 v6, Adafruit 5543, made-to-order) were taken from a single search page on 18 Oct 2026. The FT232RL module price was not verified.
  - The RTC backup-cell connector and its current behaviour on the Q6A have not been physically confirmed. Without a cell, the RTC cross-check against GNSS time is unavailable after power loss.

## Адверсаріальна перевірка (`verify`)

_Агент цього етапу ще працює (run `wf_45d278c2-004`)._

