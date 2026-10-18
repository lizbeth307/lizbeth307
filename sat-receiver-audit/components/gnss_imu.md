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

_Агент цього етапу ще працює (run `wf_45d278c2-004`)._

