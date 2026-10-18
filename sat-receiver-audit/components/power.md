# Power: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_f924b2ab-5ad`_

- **Component:** Power system (battery, charging, converters, fuel gauge) for the Radxa Dragon Q6A handheld satellite receiver
- **Current pick assessment:** VERDICT: Keep 4S 21700 (~72 Wh). Drop the "USB-C PD source for the Q6A" and the separate 13 V LNB supply; one regulated 12 V rail can feed both.
  
  NOTE ON SOURCES: the shared web-search budget ran out partway through this research. Every Q6A, LimeSDR, RTL-SDR and LNB fact below comes from primary sources I could check. AliExpress and Ukrainian-shop prices for cells, IP2368/IP2366 boards, BMS boards and LTC3780 modules are ballpark figures from general market knowledge and are marked "unverified".
  
  Q6A POWER INPUT (verified):
  - Product brief: USB-C PD with 12 V, or 12 V DC into the USB-C port or the external 3-pin header (pin 1 = 12 V, pin 2 = GND, pin 3 = PWR button).
  - Radxa recommends at least 18 W (12 V/1.5 A) without power-hungry USB/PCIe devices, and at least 24 W (12 V/2 A) with USB 3.1 and PCIe fully loaded. It cannot be powered from the 5 V pins on the 40-pin header.
  
  Q6A SCHEMATIC v1.21, DC-IN page (read directly):
  - A CH224D PD sink requests 12 V; R267 is 24 kΩ, and the options table is 6.8k = 9 V, 24k = 12 V, 56k = 15 V, NC = 20 V.
  - USB-C VBUS has an SMBJ15CA TVS (15 V standoff) and a P-MOSFET switch.
  - The 12 V node feeds a Silergy SY81012 12 A buck, rated 2.7-16 V input, which makes the ~4 V phone-style VPH_PWR rail.
  - An SY7120 boosts VPH_PWR to VCC_5V_PERI. A dedicated ETA3521 buck (4 A max, 2.5-6 V input) makes VCC_3V3_MKEY for the M.2 slot.
  - Consequences:
    - NEVER feed a raw 4S pack: 16.8 V exceeds the TVS standoff and the buck's 16 V limit.
    - The board probably runs well below 12 V. This is my inference only, not supported by Radxa.
    - The M.2 3.3 V rail (4 A) is enough for the LimeSDR.
  - The USB-C port is hard-wired to the 12 V input pins. postmarketOS warns that anything plugged into USB-C while powering from the header is back-fed, and recommends taping the port over.
  - I found no published measured idle or load power for the Q6A, so this is UNVERIFIED. My estimate is ~3-5 W idle and ~8-12 W under heavy CPU+NPU load; design to Radxa's 24 W.
  
  OTHER LOADS:
  - LimeSDR Micro M.2: Lime staff say "about 4 W, depending on configuration". 2.5 A @ 3.3 V (8.25 W) in the schematic is a PCIe allowance, not a measured draw. The user guide says to design cooling for at least 10 W.
  - RTL-SDR V4: 250-270 mA @ 5 V (~1.3 W). Its bias tee gives 4.5 V, up to 180 mA.
  - Bullseye LNB: needs 11.5-14 V for vertical polarisation and 16-19 V for horizontal. The QO-100 NB downlink is vertical, so 12 V works. The LNB's current is not published; budget 100-250 mA (1.2-3 W).
  - 7-inch display: Waveshare 7" (H) draws 750-850 mA @ 5 V (~4 W). A sunlight-readable 1000+ nit panel is probably 5-10 W (estimate).
  - SPF5189Z and L-band LNAs: ~0.3-0.5 W each (estimate). GNSS + BNO085: ~0.15 W. 5 V fan: 0.3-1 W.
  
  POWER BUDGET (at the battery, ~90% converter efficiency):
  - Light (RTL-SDR LRPT, dimmed screen): ~11 W.
  - Typical (LimeSDR at 56 MHz + SatDump + bright screen): ~20-23 W.
  - Peak (NPU + UFS write + LimeSDR + LNB + bright screen): ~35-37 W. At 4S that is only ~2.2-3 A, so any 5 Ah energy cell is fine.
  
  RUNTIME (~90% of nominal usable):
  - 50 Wh: ~4 h light / ~2 h typical / ~1.2 h peak.
  - 72-75 Wh: ~5.5-6 h / ~2.8-3 h / ~1.8 h.
  - A satellite pass lasts 10-15 min, so 72 Wh covers 10+ passes with the LimeSDR running.
  
  CELL COUNT:
  - 4S1P (12.0-16.8 V) is best: lowest current, and it sits just above 12 V. A 12 V buck or buck-boost covers ~95% of capacity, and it fits the LNB's 11.5-14 V window. A flat row of four cells (~86x71x22 mm) is about the Q6A footprint (85x65 mm).
  - 3S1P: only 54 Wh, and it straddles 12 V.
  - 2S2P: needs a boost converter and ~6 A at peak.
  - 1S4P: needs 10-13 A boost currents (more heat and EMI).
  
  CHARGER CHIPS:
  - IP2368 (100 W) / IP2366 (140 W, PD3.1): 2-6S, bidirectional single USB-C, built-in coulomb gauge. These are the practical hobbyist choice, but they do NOT balance or protect individual cells, so a separate 4S balancing BMS is mandatory.
  - TI BQ25798 (verified): 1-4S buck-boost, 3.6-24 V input, 5 A, NVDC power path, MPPT, 16-bit ADC, I2C. Technically best, but ready modules are scarce; the EVM needs an EV2400/USB2ANY adapter.
  - TI BQ25713: an external-FET controller and its EVM is not available, so it is not worth it for a hobbyist.
- **Alternatives:**
  1.
    - **Name:** A. 4S1P 21700 + 4S balancing BMS + IP2368/IP2366 bidirectional USB-C PD board + 12 V regulator into the Q6A 3-pin header (recommended architecture)
    - **Key specs:** Pack: 14.4 V nominal, 64.8 Wh with Molicel P45B (4.5 Ah, 16.2 Wh, 45 A) or 72 Wh with 5 Ah cells (Molicel P50B: 18 Wh, 60 A, 265 Wh/kg, 1400 cycles; Samsung 50S; EVE 50E). IP2368: 2-6S, up to 100 W in and out, PD3.0/PPS, one USB-C port, coulomb gauge (from datasheet knowledge, not re-verified this session). IP2366: 140 W, PD3.1. 12 V rail goes to the Q6A J21 header, avoiding PD negotiation entirely.
    - **Price:** Cells: 4x EVE 50E ~$12-18; Samsung 50S ~$20-28; P50B ~$28-40 (all unverified). 4S BMS ~$3-8 (unverified). IP2368 board ~$5-10, IP2366 ~$8-15 (AliExpress, unverified). 12 V regulator $8-30. INA228 gauge $14.95. Total ~$45-120 depending on parts.
    - **Pros:** Lowest current (~3 A peak). One 12 V rail powers the Q6A and the QO-100 LNB. Charges from any USB-C source (5-20 V): power banks, EcoFlow/Bluetti USB-C ports, car PD adapters, PD solar panels. The IP23xx can also run in reverse as a power bank for a phone or radio during blackouts. The load always runs from the battery, so plugging or unplugging the charger never reboots the Q6A. Under the 100 Wh airline limit.
    - **Cons:** Needs spot-welded or holder-based series pack plus a separate BMS (IP23xx boards do not balance). In load-on-battery mode the charger may stay in CV (4.2 V/cell) while a load is connected, which ages cells if the device stays plugged in for long periods. AliExpress IP23xx board quality varies, and the chosen board must be set to 4S.
    - **Sources:**
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/power-header
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://www.molicel.com/inr-21700-p45b/
      - https://www.molicel.com/inr-21700-p50b/
      - https://www.adafruit.com/product/5832
    - **Availability:** 21700 cells (P45B especially, because of FPV-drone demand) and IP23xx boards are commonly sold on Prom.ua and AliExpress. Exact October 2026 listings and prices are unverified. P50B retail availability is uncertain.
    - **Q6a compatibility:** Fully compatible. Use the 12 V header (officially supported) and tape over the Q6A USB-C port, which is hard-wired to the 12 V input. Never connect the raw 4S pack (16.8 V exceeds the SMBJ15CA 15 V standoff and the SY81012 16 V max).
  2.
    - **Name:** B. TI BQ25798 charger (custom PCB or TI EVM) instead of the IP2368
    - **Key specs:** 1-4S, 3.6-24 V input (30 V abs max), 5 A charge, buck-boost with integrated FETs, 750 kHz/1.5 MHz, NVDC power path with dual-input mux, VOC-sampling MPPT for solar, 16-bit ADC (V/I/T), I2C, OTG 2.8-22 V at 3.32 A, -40 to 85 C. Pair with a TPS25751 for USB-C PD (TI USB-PD-CHG-EVM-01; reference design TIDA-050047, 20 V/5 A, 2-4 cells).
    - **Price:** Not shown on TI.com without login. EVM needs an EV2400/USB2ANY adapter. Ready third-party modules: unverified.
    - **Pros:** True power path (the system runs from the input and the battery sits idle and full). Real MPPT for direct solar-panel charging. 16-bit ADC fuel data over I2C straight into Linux. Choice of 1.5 MHz switching is easier to filter.
    - **Cons:** Needs a custom 4x4 mm QFN PCB or an expensive EVM, plus I2C configuration at every boot. Limited to 5 A charging. Not a plug-and-play AliExpress part.
    - **Sources:**
      - https://www.ti.com/product/BQ25798
      - https://www.ti.com/tool/BQ25798EVM
      - https://www.ti.com/tool/USB-PD-CHG-EVM-01
    - **Availability:** Chip is ACTIVE at TI and distributors. EVM stock status on TI.com is unclear. Hobby breakout boards are unverified.
    - **Q6a compatibility:** Compatible. SYS output goes to a 12 V regulator and then the header. The I2C ADC can be read from the 40-pin header.
  3.
    - **Name:** C. TI BQ25713 NVDC buck-boost charge controller
    - **Key specs:** 1-4S, 3.5-24 V input, 8.128 A charge, 800 kHz/1.2 MHz, NVDC, USB-C/PD compatible, OTG 3-20.8 V up to 6.4 A, I2C/SMBus, 32-pin WQFN. Controller only, needs external MOSFETs.
    - **Price:** BQ25713EVM-017 listed as not available for purchase. Chip price not listed.
    - **Pros:** Highest current and a laptop-grade power path.
    - **Cons:** Needs external FETs, a PD controller and an MCU, and the EVM is not obtainable. Overkill for a load under 40 W. Not recommended.
    - **Sources:**
      - https://www.ti.com/product/BQ25713
    - **Availability:** EVM unavailable. Effectively a custom-PCB-only option.
    - **Q6a compatibility:** Electrically compatible, but impractical.
  4.
    - **Name:** D. 1S4P 21700 + 100 W single-cell power-bank SoC board (e.g. SW6306 or IP5389 class) feeding the Q6A USB-C at 12 V PD
    - **Key specs:** 3.0-4.2 V, ~20 Ah (72 Wh with 5 Ah cells). The board boosts to PD 5/9/12/15/20 V (PDO list depends on the board, unverified).
    - **Price:** Board ~$5-12, cells $12-40 (unverified).
    - **Pros:** No series balancing. Cheapest and simplest to build. Charge and discharge over USB-C.
    - **Cons:** 10-13 A battery current at 25-37 W (heat, thick wiring, a noisier high-current boost near the SDR). Must offer a 12 V PDO for the Q6A's CH224D (behaviour when 12 V is missing is unverified). Many power-bank SoCs briefly drop the output when a charger is plugged in, which hard-reboots the Q6A. The LNB still needs its own 12-13 V boost.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
    - **Availability:** Widely sold on AliExpress (specific listings and prices unverified this session).
    - **Q6a compatibility:** Works only if the board offers a 12 V PDO and does not glitch during pass-through. Test before committing.
  5.
    - **Name:** E. Off-the-shelf USB-C PD power bank (external, 65-100 W, 12 V PDO)
    - **Key specs:** Typically 20,000-25,000 mAh (72-90 Wh), PD 5/9/12/15/20 V. Check that the label lists 12 V.
    - **Price:** ~$25-60 (unverified).
    - **Pros:** No pack building. Useful at home during blackouts too. Hot-swappable.
    - **Cons:** Not integrated into a palm-sized device. Many newer banks omit the 12 V PDO. Pass-through charging usually interrupts the output. Cannot feed the LNB without an extra boost converter.
    - **Sources:**
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
    - **Availability:** Rozetka, Prom.ua and EU shops carry many models; check the PDO table per model.
    - **Q6a compatibility:** Only via the Q6A USB-C (CH224D asks for 12 V). Do not combine with header power.
  6.
    - **Name:** F. Waveshare UPS Module 3S
    - **Key specs:** 3x 18650 in series, 5 V/5 A USB-C output plus raw 12.6 V on XH2.54, charges only from a 12.6 V/2 A DC barrel (not from 5 V or PD), I2C V/I/P monitor (INA219 per demo script), charge while discharging.
    - **Price:** Not listed on the wiki (unverified).
    - **Pros:** Ready-made UPS behaviour and I2C monitoring.
    - **Cons:** 18650 cells (less energy). No regulated 12 V output (raw 9-12.6 V). Cannot charge from USB-C or power banks. Not suitable for this build.
    - **Sources:**
      - https://www.waveshare.com/wiki/UPS_Module_3S
    - **Availability:** Waveshare and resellers.
    - **Q6a compatibility:** Poor. Its 5 V output cannot power the Q6A, and the raw 3S output is outside Radxa's 12 V spec.
  7.
    - **Name:** G. 12 V rail regulator options (4S to 12 V for the Q6A header and LNB)
    - **Key specs:** (1) Pololu S18V20F12 buck-boost: 3-30 V in, 12 V, ~2 A typical max, 80-90% efficiency, ~1 mA quiescent, 43x21x10 mm. (2) LTC3780-based buck-boost module: 4-switch controller, ~5-32 V in, 200-400 kHz, FCB pin for forced-continuous mode, several amps (module ratings unverified). (3) Any synchronous 12 V buck that can run at 100% duty: a 4S pack stays above ~12.4 V for about 95% of its capacity.
    - **Price:** Pololu $29.95 (verified). LTC3780 module ~$6-12 (unverified).
    - **Pros:** Pololu: small, quality, clean; ideal for the LNB or for a Q6A at moderate load. LTC3780: enough current for 24 W + LNB and cheap; forced-PWM mode avoids PFM spurs that wander across the spectrum.
    - **Cons:** Pololu's 2 A is not enough for Radxa's 24 W worst case plus the LNB. LTC3780 modules are bulky, run at a lower switching frequency, and need LC/ferrite filtering and shielding.
    - **Sources:**
      - https://www.pololu.com/product/2577
      - https://www.pololu.com/category/133/step-up-step-down-voltage-regulators
    - **Availability:** Pololu via EU distributors. LTC3780 modules on AliExpress and Prom.ua (unverified).
    - **Q6a compatibility:** Feed the J21 12 V header. Keep the output at 12.0 V ±5%.
  8.
    - **Name:** H. Fuel gauge: INA228 (Adafruit 5832) or generic INA226
    - **Key specs:** INA228: 0-85 V bus, 20-bit ADC, integrated energy and charge accumulators, I2C up to 2.94 MHz. Adafruit board: 15 mOhm shunt, up to 10 A, STEMMA QT.
    - **Price:** Adafruit INA228 $14.95 (verified). Generic INA226 modules ~$2-4 (unverified).
    - **Pros:** Coulomb counting plus live power per operating mode in Linux over I2C from the 40-pin header. Replaces a dedicated gauge IC. The IP23xx's own gauge only drives LEDs unless you use the I2C variant.
    - **Cons:** State of charge must be computed in software (combine coulomb count with a voltage-based reset at full charge).
    - **Sources:**
      - https://www.adafruit.com/product/5832
      - https://www.ti.com/product/INA228
    - **Availability:** Adafruit via EU resellers. INA226 boards everywhere.
    - **Q6a compatibility:** 3.3 V I2C on the 40-pin header.
- **Recommended:**
  - **Name:** 4S1P 21700 (Samsung 50S or Molicel P50B, 72 Wh) + 4S balancing BMS with NTC (10-15 A) + IP2366 (or IP2368) bidirectional USB-C PD charger board + one shielded, LC-filtered 12 V rail (≥4-5 A, forced-PWM) into the Q6A 3-pin 12 V header and, switched, into the QO-100 LNB bias tee + LT3045-class ultra-low-noise LDO for the LNAs + INA228 fuel gauge
  - **Why:** - No PD dependency: Radxa officially supports 12 V DC on the J21 header, which bypasses the CH224D and the need for a USB-C PD source.
  - 12 V regulation: a 4S pack stays above 12 V for almost all of its capacity, so a 12 V rail is easy to hold. The same rail powers the Bullseye LNB, which needs 11.5-14 V for vertical, the QO-100 NB downlink polarisation.
  - Light current: the peak load is only ~3 A.
  - Charging: the IP23xx board charges from anything with USB-C in Ukraine (power banks, EcoFlow, car, PD solar panel). It can also act as a power bank for a phone or radio.
  - No reboots: the load always runs from the battery, so connecting or disconnecting a charger cannot reboot the Q6A.
  - Q6A rails cover the small loads: the Q6A's internal 4 A M.2 3.3 V buck powers the LimeSDR, the USB 5 V powers the RTL-SDR, and the 40-pin 5 V/3.3 V pins power the fan, GNSS and IMU. So the only extra converters are the 12 V rail, a 5 V buck for the bright display, and an LDO for the LNAs.
  - Runtime: ~3 h with the LimeSDR at 56 MHz and a bright screen, ~5.5 h in RTL-SDR-only mode.
  - Upgrade path: for direct solar charging and a true power path, use a BQ25798 instead of the IP23xx on a custom PCB.
  - **Price:** ~$80-125 total (only Pololu and INA228 prices verified; the rest are unverified estimates).
  - 4x Samsung 50S or P50B: $20-40
  - 4S BMS: $5-8
  - IP2366 board: $8-15
  - 12 V buck-boost (LTC3780-class module, $6-12, or a quality brand module) plus Pololu S18V20F12 for the LNB if wanted: $30
  - 5 V/3 A buck for the display: $3-6
  - LT3045 LDO module: $5-10
  - INA228: $14.95
  - Fuse, switch, nickel or holders, XT30, ferrites: ~$10
  - **Sources:**
    - https://docs.radxa.com/en/dragon/q6a/hardware-use/power-header
    - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
    - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
    - https://docs.nura.eco/phone-harness/main/connecting-devices/radxa-dragon-q6a.html
    - https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
    - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
    - https://www.rtl-sdr.com/?p=44655
    - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines/
    - https://www.molicel.com/inr-21700-p50b/
    - https://www.adafruit.com/product/5832
- **Budget option:**
  - **Name:** 4S1P EVE 50E (or Molicel P45B for 64.8 Wh) + generic 4S balancing BMS + IP2368 100 W board + LTC3780 12 V module (forced-continuous, with an added LC output filter) + INA226 module
  - **Why:** Same safe 4S, 12 V-header architecture as the main pick, using the cheapest adequate parts.
  - EVE 50E energy cells (5 Ah, ~15 A max) are plenty for a ~3 A load.
  - The IP2368 is enough for 72 Wh (about 1-1.5 h charge on a 65-100 W PD source).
  - One LTC3780 supplies both the Q6A and the LNB.
  - An INA226 gives an I2C fuel gauge for about $3.
  - Runtime ~2.8 h typical / ~5.5 h light.
  - **Price:** ~$40-55 (unverified estimates).
  - Cells: $12-18
  - BMS: $3-5
  - IP2368: $5-10
  - LTC3780 module: $6-12
  - INA226: $2-4
  - Misc: ~$8
- **Risks:**
  - The Q6A's real power draw is unverified: I found no published idle or load measurements. Size everything for Radxa's 24 W (12 V/2 A) and measure the real draw with the INA228.
  - The Q6A input tolerance outside 12 V is inferred from schematic v1.21 (SY81012 rated 2.7-16 V), not stated by Radxa. Do not run 3S direct or anything under 11.5 V without a bench test. Never connect raw 4S: 16.8 V exceeds the SMBJ15CA 15 V standoff and the SY81012 16 V maximum.
  - USB-C back-feed: the Q6A USB-C port is hard-wired to the 12 V input. If someone plugs a charger into the Q6A port while the header is powered, it can damage the charger or the board. Make the IP23xx USB-C the only external port and seal or cover the Q6A's own port.
  - CH224D behaviour with chargers or power banks that lack a 12 V PDO is unverified. This is one more reason not to depend on PD for the Q6A.
  - IP2368/IP2366 specs, module quality and prices were not re-verified this session (web-search budget exhausted). These boards do not balance or protect individual cells, so a separate 4S BMS is mandatory. Make sure the board is set to 4S and that NTC charge inhibit below 0 °C works.
  - In load-on-battery mode the charger may sit in CV at 4.2 V/cell while the device stays plugged in for days. For long mains use, set 4.1 V/cell if the board allows it, or move to the BQ25798 NVDC power path.
  - Switching noise: external converters (especially low-frequency LTC3780 modules) can put spurs and broadband noise into the LNA, LNB and SDR inputs. Mitigate with forced-PWM mode (no PFM), shielded inductors, pi-filters (ferrite bead + 10-22 µH + 22-100 µF ceramics), a tin-plate or copper-tape shield box, common-mode chokes on DC leads, ultra-low-noise LDOs for the LNAs, and at least 5-10 cm between converters and RF parts.
  - The LimeSDR 3.3 V must pass through a 2230-to-2280 M.2 extension. Contact and trace resistance at 1.2-2.5 A can sag the rail, so measure at least 3.14 V at the card under load. Lime says to design cooling for at least 10 W.
  - Crowd Supply now lists the LimeSDR Micro M.2 Basic at $249 (+$18 worldwide shipping), with new orders shipping Dec 15, 2026. That affects the overall budget and schedule.
  - Counterfeit or relabelled 21700 cells are common. Buy from reputable EU (NKON-type) or established UA vendors, and check capacity and internal resistance.
  - Cold weather: expect roughly 20-30% less capacity around -10 °C, and never charge Li-ion below 0 °C. Molicel P45B/P50B handle cold better than budget energy cells.
  - Bullseye LNB current is not published (budget 250 mA). Horizontal polarisation (QO-100 WB/DATV) needs 16-19 V, which the 12 V rail cannot provide without a small switched boost converter.
- **Integration notes:**
  - WIRING: battery goes BMS → 5 A fuse → master switch → INA228 shunt → loads, with the IP23xx BAT pins on the battery side of the shunt so the gauge sees both charge and discharge current. The 12 V rail goes to Q6A J21 pin 1 (12 V) and pin 2 (GND); wire J21 pin 3 (PWR) to a case push-button as the power and shutdown button.
  - LOADS ON Q6A RAILS: LimeSDR runs from the Q6A's own M.2 3.3 V (ETA3521 buck, 4 A max, fed from the internal 5 V boost), which covers Lime's ~4 W typical and 8.25 W allowance. RTL-SDR V4 runs from a USB 2.0 port (250-270 mA). Fan runs from the 40-pin 5 V; GNSS and BNO085 from the 40-pin 3.3 V.
  - DISPLAY: power a sunlight-readable 7-inch panel (probably 5-10 W) from its own 5 V/3 A buck off the pack, not from a Q6A USB port. Dimming is the biggest single runtime lever.
  - LNAs: feed them from an LT3045-class LDO (5 V) behind an LC filter, or from the RTL-SDR V4's 4.5 V/180 mA bias tee when the RTL is the receiver; check that LNA current is under 180 mA.
  - LNB: feed it from the 12 V rail through a GPIO-switched P-MOSFET, a 100-250 mA polyfuse, and an RF choke or bias tee. 12 V selects vertical polarisation, which is correct for the QO-100 NB downlink. Turn it off when not doing QO-100 (saves 1-3 W).
  - PACK LAYOUT: a flat 4S1P 21700 row is about 86x71x22 mm, close to the Q6A footprint, so it can sit under the board as a sandwich. Total mass is about 280 g for the cells and ~350 g with BMS and holders. 72 Wh is under the 100 Wh airline limit.
  - CHARGING: about 1-1.5 h from a 65-100 W PD source; about 4 h from an 18-20 W power bank. In blackouts, charge from EcoFlow/Bluetti USB-C ports, a car USB-C PD adapter or a PD solar panel; the same port can charge a phone in reverse.
  - SOFTWARE: read the INA228 over I2C from Linux (accumulate charge, reset to 100% at charge termination) and show remaining Wh and minutes on the UI. Log power per mode (RTL vs Lime vs NPU) to calibrate runtime estimates.
  - EMI LAYOUT: put the 12 V and 5 V converters in a shielded corner far from the MHF4/SMA pigtails and LNAs; use twisted DC pairs and clip-on ferrites; avoid Bluetooth smart BMS boards (2.4 GHz radiation near the S-band chain).
- **Double duty opportunities:**
  - One regulated 12 V rail powers both the Q6A (via the J21 header) and the Bullseye LNB (11.5-14 V, vertical/NB). This removes both the USB-C PD source module and the separate 13 V LNB injector supply.
  - The IP2366/IP2368 USB-C port is both the device's universal charging input (power banks, power stations, car, PD solar) and a reverse PD power-bank output for a phone or radio during blackouts.
  - The Q6A's own regulators already supply M.2 3.3 V (4 A buck), USB 5 V and the 40-pin 5 V/3.3 V pins, so no external 3.3 V converter is needed for the LimeSDR, GNSS, IMU or fan.
  - The RTL-SDR V4's built-in 4.5 V/180 mA bias tee can power the masthead LNA, so no separate LNA power injector is needed in RTL mode.
  - The INA228 does fuel gauge, per-mode power logging and charger-present detection in one $15 I2C part, with no dedicated gauge IC.
  - J21 pin 3 (PWR) gives a case power button with clean shutdown, so no extra soft-power circuit is needed.
  - A pack in common FPV-drone format (4S 21700, XT30/XT60 + balance lead) can be balance-charged with the hobby chargers already widespread in Ukraine as a backup charging path (keep the BMS in place).
- **Confidence:** medium

## Форуми та досвід спільноти (`forums`)

_Run `wf_f924b2ab-5ad`_

- **Component:** Power system (battery, charging, converters, fuel gauge) for the Radxa Dragon Q6A handheld satellite receiver
- **Experiences:**
  1.
    - **Product:** Radxa Dragon Q6A 3-pin 12 V header fed from a 4S1P LiPo
    - **Source url:** https://forum.radxa.com/t/radxa-q6a-4s1p-powering/31611
    - **Community:** Radxa forum
    - **What they built:** A user wanted to feed a 4S1P pack (12.0-16.8 V) straight into the two pins beside the USB-C port (October 2026).
    - **Problems:**
      - Asked whether a raw 4S pack can go straight into the header.
    - **Fixes:**
      - Radxa staff (strongtz, 2026-10-15): the header pins 'can only handle 4.5V to 16V power input'.
    - **Outcome:** A raw 4S pack is ruled out: 16.8 V at full charge is above the 16 V limit. The schematic agrees: the input capacitors on ADP12V are rated 16 V and there is an SMBJ15CA TVS. A regulator is mandatory with 4S.
  2.
    - **Product:** Radxa Dragon Q6A powered from a battery through a DC-DC converter
    - **Source url:** https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
    - **Community:** Radxa forum
    - **What they built:** An outdoor battery-powered Q6A project.
    - **Problems:**
      - Unclear input tolerance.
      - Unclear how much current the 3.3 V pins can supply.
      - Unclear what the PWR pin does.
    - **Fixes:**
      - Radxa staff (BigfootACA, 2026-03-02): the 12V pin accepts 3.6-16 V, and 5, 9 or 12 V are the recommended values. The SY81012 then steps it down to 4.2 V.
      - PWR is a power key, the same as the on-board button.
      - Do not use USB-C when supplying the header.
      - The 40-pin 3.3 V comes from an ETA3521 (about 4 A in theory) shared with other loads, so use an external buck for significant 3.3 V loads.
      - Note: the same post also says direct 12 V power is 'technically possible, but not recommended', which is ambiguous wording.
    - **Outcome:** Staff statements give a wider input window (3.6 or 4.5 to 16 V) than the docs, which say 12 V only. That would allow 2S or 3S packs to feed the board directly, but it has not been bench-tested publicly.
  3.
    - **Product:** Radxa Dragon Q6A 12 V header
    - **Source url:** https://forum.radxa.com/t/dragon-q6a-12v-input-header-voltage-range/30233
    - **Community:** Radxa forum
    - **What they built:** Powering the Q6A from an external source.
    - **Problems:**
      - Voltage range not documented.
    - **Fixes:**
      - Staff (strongtz): 4.5 V to 16 V.
    - **Outcome:** Confirmed by staff twice (January and October 2026).
  4.
    - **Product:** Radxa Dragon Q6A on a 12 V supply into the 3-pin header
    - **Source url:** https://forum.radxa.com/t/how-to-setup-dragon-q6a-to-boot-without-pressing-the-power-button/30852
    - **Community:** Radxa forum
    - **What they built:** A headless setup that should boot when power is applied.
    - **Problems:**
      - One board powered from the header needs a button press to boot.
      - Other users' boards (USB-C or header) boot on power-up.
    - **Fixes:**
      - Staff (RadxaYuntian) suggested updating the BIOS/SPI firmware, since an old version may be running.
    - **Outcome:** Unresolved: the original poster never confirmed a fix. Auto-boot behaviour depends on the board or firmware.
  5.
    - **Product:** Q6A rear battery pads (+ / - / TS) and the PM7250B PMIC
    - **Source url:** https://forum.radxa.com/t/radxa-q6a-running-on-a-battery-and-charging/29650
    - **Community:** Radxa forum
    - **What they built:** An attempt to run the Q6A from a 1S Li-ion cell like a phone, using the rear pads.
    - **Problems:**
      - The PMIC is in 'fake battery' mode.
      - R24 is not populated.
      - VPH_PWR must not exceed 4.5 V.
      - BATT_ID has a 10 kΩ pull-down, so charging is impossible.
      - Software disables all charging features.
    - **Fixes:**
      - None: staff say it is not feasible without hardware modification, and warn against connecting Type-C and a battery at the same time.
      - The user planned their own external 12 V 2.5-3 A supply instead.
    - **Outcome:** Confirms an external battery, charger and regulator architecture is required. See also https://forum.radxa.com/t/question-about-the-three-pogo-pads-ts-on-the-back-of-dragon-q6a/30090 : there is no official battery module.
  6.
    - **Product:** Radxa Dragon Q6A (power state after software shutdown)
    - **Source url:** https://forum.radxa.com/t/upcoming-radxa-dragon-q6a/26723
    - **Community:** Radxa forum
    - **What they built:** Early testing with UFS and NVMe.
    - **Problems:**
      - After software power-off ('halt') the board still draws 1.9-2.5 W (user willy, 2025-09-21).
    - **Fixes:**
      - None given. The schematic shows the SY81012 input buck is 'ALWAYS ON' whenever input is present.
    - **Outcome:** On a battery this would drain 72 Wh in roughly 1.5 days, so a hard master switch or load switch is needed.
  7.
    - **Product:** Radxa Dragon Q6A power consumption benchmark
    - **Source url:** https://github.com/geerlingguy/sbc-reviews/issues/85
    - **Community:** GitHub (geerlingguy/sbc-reviews)
    - **What they built:** A standard SBC review with wall-power measurements.
    - **Problems:**
      - The PoE HAT fan is loud.
      - The PoE HAT fan device tree was hard to set up.
    - **Fixes:**
      - Fan controlled by a custom systemd script (on at 70 °C, off at 60 °C).
    - **Outcome:** Measured at the wall: 2.9 W idle, 9.3 W stress-ng, 9.5 W Geekbench multicore, 10.1 W HPL, 7.8-7.9 W for llama.cpp LLM inference. This confirms the researcher's estimate of ~3 W idle and ~10 W load for the board alone.
  8.
    - **Product:** Radxa Dragon Q6A on a USB-C PD 35 W adapter
    - **Source url:** https://forum.radxa.com/t/q6a-rebooting-constantly/30452
    - **Community:** Radxa forum
    - **What they built:** Armbian minimal setup with a copper heatsink and a 5 V fan.
    - **Problems:**
      - Instant resets after 3-30 minutes that looked like power drops.
      - Another user found that the default image suspends when idle, and suspected the PD supply stops delivering power during suspend.
    - **Fixes:**
      - Switching to the official radxa-dragon-q6a_noble_gnome_r2 image fixed it.
    - **Outcome:** Fixed by changing the image. Disable auto-suspend on a battery or SDR device.
  9.
    - **Product:** Radxa Dragon Q6A + Radxa 256 GB Kioxia UFS, powered by a DC12 36 W adapter on the 3-pin header
    - **Source url:** https://forum.radxa.com/t/ufs-random-reboots/30630
    - **Community:** Radxa forum
    - **What they built:** Booting from the UFS module (relevant because UFS is the planned raw-IQ storage).
    - **Problems:**
      - Stutters, freezes and random reboots that look like brown-outs.
      - ufshcd-qcom hibern8 exit errors.
      - Lowering the UFS gear to HS-G2 did not help.
    - **Fixes:**
      - Radxa added a PA_TACTIVATE quirk for the Kioxia THGJFGT1E45BAILB to radxa/kernel linux-6.18.2, and it is in Armbian 26.05.
      - Interim workaround: a keep-alive write loop.
      - Use 'apt-mark hold' so an upgrade does not revert to the unfixed kernel.
    - **Outcome:** Fixed (May 2026). Rule this out before blaming the power system for reboots.
  10.
    - **Product:** Radxa Dragon Q6A 40-pin 5 V input
    - **Source url:** https://forum.radxa.com/t/powering-the-q6a-via-the-5v-pin-on-the-40-pin-header/30833
    - **Community:** Radxa forum
    - **What they built:** An attempt to power the board from 5 V on the 40-pin header.
    - **Problems:**
      - Not documented whether this works.
    - **Fixes:**
      - Staff: the Q6A cannot be powered from the 40-pin 5 V pins.
    - **Outcome:** Only USB-C (12 V PD or 5 V/3 A) or the 3-pin header work.
  11.
    - **Product:** Radxa Dragon Q6A powered via the header from a 'phone harness'
    - **Source url:** https://docs.nura.eco/phone-harness/main/connecting-devices/radxa-dragon-q6a.html
    - **Community:** nura.eco project docs (postmarketOS-style phone harness)
    - **What they built:** A battery or harness supply into the auxiliary power connector.
    - **Problems:**
      - The USB-C port is hard-wired to the 12 V input pins and gets reverse-supplied (back-fed).
    - **Fixes:**
      - Never plug anything into the Q6A USB-C while header-powered, and seal the port with tape.
    - **Outcome:** Documented hazard. Make the charger's USB-C the device's only external port.
  12.
    - **Product:** Q6A eMMC/UFS module socket
    - **Source url:** https://forum.radxa.com/t/windows-on-radxa-dragon-q6a/29913
    - **Community:** Radxa forum
    - **What they built:** Testing third-party eMMC modules.
    - **Problems:**
      - An Orange Pi eMMC module shorts the UFS power lines and triggers an immediate protective shutdown.
    - **Fixes:**
      - Use only Radxa UFS or eMMC modules.
    - **Outcome:** A wrong module looks like a power fault.
  13.
    - **Product:** Q6A fan supply
    - **Source url:** https://forum.radxa.com/t/where-is-the-fan-interface-at-q6a/30737
    - **Community:** Radxa forum
    - **What they built:** Active cooling.
    - **Problems:**
      - There is no fan header.
    - **Fixes:**
      - Power the fan from the 40-pin 5 V and drive PWM from a GPIO (script https://github.com/Calin23/dragon-q6a-fan-control).
    - **Outcome:** Works. Budget the fan on the Q6A's internal 5 V rail.
  14.
    - **Product:** LimeSDR Micro M.2
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
    - **Community:** MyriadRF/Lime discourse
    - **What they built:** A carrier board design for the Micro M.2.
    - **Problems:**
      - The schematic shows 2.5 A at 3.3 V (8.25 W).
    - **Fixes:**
      - Lime (Zack, 2026-08-24): that figure is the PCIe specification allowance, and the board should consume about 4 W depending on configuration. Idle power was asked but not answered.
    - **Outcome:** Budget ~4 W typical and design cooling for 10 W, as the setup guide says.
  15.
    - **Product:** LimeSDR XTRX (LMS7002M PCIe sibling of the Micro) on a CM4 IO board
    - **Source url:** https://discourse.myriadrf.org/t/temperature-of-limesdr-xtrx/8366
    - **Community:** MyriadRF/Lime discourse
    - **What they built:** Open-air XTRX on CM4/CM5 hosts.
    - **Problems:**
      - About 60 °C within 5 minutes.
      - Over 85 °C at high sample rates.
      - 80 °C just running the GNU Radio FM receiver.
    - **Fixes:**
      - A small 40 mm fan brings it to ~50-55 °C.
      - A thermal pad to a copper pour (supplied with the full-size adapter).
    - **Outcome:** Fan and heatsink are needed. Fan power must go into the budget, and heat in a sealed handheld case is a real risk.
  16.
    - **Product:** LimeSDR Micro on a ClockworkPi uConsole (CM5, battery handheld)
    - **Source url:** https://www.crowdsupply.com/lime-micro/limesdr-micro/updates/thanks-and-uconsole-gqrx-demo
    - **Community:** Crowd Supply project updates
    - **What they built:** Lime's own demo of Gqrx at 40 Msps on a battery handheld ARM computer.
    - **Problems:**
      - No power, thermal or runtime data published.
    - **Fixes:** []
    - **Outcome:** Shows the Micro works on a battery-powered ARM handheld. No numbers to reuse.
  17.
    - **Product:** ClockworkPi uConsole with a custom 35,000 mAh 10P 18650 pack, AIO V2 board (RTL-SDR, LoRa, GPS) and extra radios
    - **Source url:** https://forum.clockworkpi.com/t/35-000mah-uconsole-the-everything-build-stl/23365
    - **Community:** ClockworkPi forum
    - **What they built:** A handheld RF lab with 15 antennas, an SDR and Wi-Fi cards (September 2026).
    - **Problems:**
      - Battery voltage sag repeatedly shut the whole console down; LiPo pouch cells could not handle the current.
      - The USB bus lacked current.
      - Shutdown left the board partly powered.
    - **Fixes:**
      - Spot-welded LG 18650 cells, a 20 A BMS, very short wires to the battery board, and an added aluminium capacitor.
      - AIO resistor changed to 6.8 kΩ so the USB bus gets 2 A.
      - Larger 220 µF capacitor at C513.
      - Hard-shutoff mod on the power button.
    - **Outcome:** Works: 17 h idle and 10 h of continuous SDR. Lesson: avoid high-current 1S boost designs, and use low-resistance cell interconnects.
  18.
    - **Product:** uConsole battery fuel gauge with SDR workloads
    - **Source url:** https://forum.clockworkpi.com/t/good-runtime-but-inaccurate-charge-level-indicator-despite-calibration/22410
    - **Community:** ClockworkPi forum
    - **What they built:** CM4/CM5 uConsoles on 18650, 21700 and 26650 cells.
    - **Problems:**
      - The gauge shows 100% for hours, then the device shuts off at 70-80%.
      - Under SDR load the system powered off at about 30% remaining.
    - **Fixes:**
      - Calibrate under a realistic load (video plus 50% brightness), not at idle.
      - Declare the pack's capacity and energy in config.txt (clockworkpi-custom-battery overlay).
    - **Outcome:** Partly fixed. Voltage-based gauging is unreliable under heavy, variable SDR load.
  19.
    - **Product:** HackerGadgets dual 21700 holder in a uConsole (Molicel P42A)
    - **Source url:** https://forum.clockworkpi.com/t/uconsole-only-uses-1-of-the-2-batteries-since-switching-to-hacker-gadgets-dual-21700-battery-holder/23476
    - **Community:** ClockworkPi forum
    - **What they built:** An upgrade to 2x 21700 in parallel.
    - **Problems:**
      - Only one cell was actually used; the other stayed full.
      - With one cell the device crashes when an app adds load.
      - At 3% the system crashes but does not fully power off.
    - **Fixes:**
      - Under investigation: swapping cells and slots, and recharging the empty cell.
    - **Outcome:** Unresolved (October 2026). Spring holders and contact resistance matter at high current, so spot-welded or soldered tabs are safer.
  20.
    - **Product:** uConsole CM5 + NVMe with a 10 Ah flat-pack
    - **Source url:** https://forum.clockworkpi.com/t/cm5-lite-trixie-nvme-boot/22359
    - **Community:** ClockworkPi forum
    - **What they built:** A CM5 handheld with NVMe and a larger battery.
    - **Problems:**
      - Voltage sag on the 10 Ah flat-pack was so bad the user gave up.
      - PCIe Gen3 was unstable over long traces.
      - The CM5 drains the battery even after shutdown.
    - **Fixes:**
      - Planned: 2x 10 Ah in 2S with a step-down converter.
      - Run PCIe at Gen2 for stability.
    - **Outcome:** Supports moving to a higher series cell count with a buck converter.
  21.
    - **Product:** Particle Tachyon (QCS6490, same SoC as the Q6A) with integrated PMIC fuel gauge, 1S LiPo
    - **Source url:** https://community.particle.io/t/battery-percentage-tracking-wildly-wrong/70194
    - **Community:** Particle community
    - **What they built:** A QCS6490 board running from an approximately 9 Ah 3P LiPo.
    - **Problems:**
      - The PMIC fuel gauge reported 94% at 3.41 V just before cutoff, and 75% then 12% across a reboot.
      - Measured idle draw: about 590 mA at 3.41 V (about 2 W).
    - **Fixes:**
      - Particle: the gauge relies on an open-circuit-voltage table that does not match the pack; correct battery profile and learning are needed.
    - **Outcome:** Not fully fixed. One user got 27.5 h of runtime. Strong argument for an external coulomb-counting gauge (INA228/INA226) on the Q6A.
  22.
    - **Product:** Particle Tachyon auto-boot after battery depletion
    - **Source url:** https://community.particle.io/t/sys-auto-boot-does-not-work-after-lipo-battery-dies/70372
    - **Community:** Particle community
    - **What they built:** Unattended QCS6490 devices on intermittent power.
    - **Problems:**
      - After the battery ran flat, the board stayed in a low-power state with a solid red LED.
      - Restoring USB-C power did not boot it; a button press was needed. Same report: https://community.particle.io/t/tachyon-autoboot-not-working-after-battery-depletion/70499
    - **Fixes:**
      - None published.
    - **Outcome:** Unresolved. A similar risk exists on the Q6A (header boot needing the button).
  23.
    - **Product:** Particle Tachyon USB-C PD charging
    - **Source url:** https://community.particle.io/t/my-tachyon-isnt-charging/70368
    - **Community:** Particle community
    - **What they built:** Charging from laptops and hubs.
    - **Problems:**
      - The battery drained from 60% to 1% while plugged into a laptop USB-C port, because charging needs USB PD.
    - **Fixes:**
      - Use a USB-C PD charger, such as a phone charger.
    - **Outcome:** Fixed. PD-dependent input is fragile with arbitrary sources.
  24.
    - **Product:** IP2368 100 W bidirectional USB-C PD charge/discharge board (AliExpress)
    - **Source url:** https://mysku.club/blog/aliexpress/100034.html
    - **Community:** mysku.club (Russian-language hands-on review site)
    - **What they built:** A bench test of the board configured for 3S, with readers' 4S and 6S experiences.
    - **Problems:**
      - The first board charged but would not discharge (refunded).
      - One MOSFET exceeded 100 °C while charging at 5.1 A.
      - The 5 V LDO runs hot.
      - Never reached 100 W; output fell back at about 80-85 W.
      - Does not balance cells.
      - The NTC position is a fixed 10 kΩ resistor, so there is no real temperature sensing.
      - After a battery is connected, or after a protection trip, the board gives no output until it is 'kicked' by charging through USB-C.
      - A 6S reader saw shutdown when forcing 3-5 A PD charging.
    - **Fixes:**
      - Resistor straps: R7 sets cell count (13k = 4S default); R3 sets charge current (0.2 × R ... 27k = 5.4 A); R4 sets charge voltage (V = 4000 + 0.02 × R mV); R5 sets capacity.
      - Fit a B3435 NTC thermistor: charging stops above about 45 °C.
      - Swap the LDO for an ME6203.
      - Kick-start with 5 V on USB-C, or buy the IP2368_NACT variant, which starts without activation.
      - Add a separate BMS.
    - **Outcome:** Works well after fixes: 92-94% efficient, about 0.1 mA standby. Usable to about 80 W. Quality varies (one dead-on-arrival board).
  25.
    - **Product:** IP2368 module charging from bidirectional devices
    - **Source url:** https://www.mikrocontroller.net/topic/569785
    - **Community:** mikrocontroller.net (German) — Cloudflare blocked, content from search-engine excerpt only
    - **What they built:** A 4S power bank.
    - **Problems:**
      - The module keeps sinking power from USB-C devices that are themselves bidirectional, and devices that request a voltage stay dead.
      - The charge cutoff voltage was respected.
    - **Fixes:**
      - Not reported in the excerpt. Sellers warn not to connect two bidirectional ports together.
    - **Outcome:** Unverified (page not fetchable). Reverse 'power bank' mode to phones or radios may not work automatically.
  26.
    - **Product:** IP2366 (140 W) charger chip and boards
    - **Source url:** https://done.land/components/power/powersupplies/battery/chargers/charge-discharge/ip2366/
    - **Community:** done.land (hobbyist component wiki)
    - **What they built:** Notes on configuring IP2366 boards.
    - **Problems:**
      - Identical-looking chips ship with different firmware (LED only, I2C only, or both), and markings do not tell them apart.
      - I2C settings are not retained.
      - Two parallel straps in one setting group give unpredictable values.
    - **Fixes:**
      - Set defaults with resistors or DIP switches, and use I2C only for fine-tuning after testing the actual chip.
      - Hold INT high to stop the chip sleeping (see https://github.com/InterfaceGUI/IP2368.h: the chip NACKs I2C while asleep).
    - **Outcome:** Usable, but I2C telemetry from IP23xx into Linux is unreliable. Use an INA228/INA226 for gauging.
  27.
    - **Product:** SW6306-based 45 W 4S2P power bank (8x DMEGC 18650)
    - **Source url:** https://mysku.club/blog/russia-stores/107502.html
    - **Community:** mysku.club
    - **What they built:** A teardown and measurement of a ready-made bank of the kind in alternatives D and E.
    - **Problems:**
      - The balancing circuit undercharges one group every cycle (PCB routing error).
      - One switching MOSFET reached 100-102 °C when charging at 63 W and 91 °C when discharging at 42 W.
      - Output ports reboot when external power is removed, and pass-through drops the output to 5 V.
      - The controller reset during charging.
      - Sleeps below about 80 mA load.
    - **Fixes:**
      - A wire and resistor from the second group to the HY2213 VDD pin, or remove the balancer.
    - **Outcome:** Efficiency was good (95.5% discharge), but output glitches make it unsuitable for powering an SBC directly.
  28.
    - **Product:** Power-bank pass-through (SW6208 bank vs. Xiaomi with separate stages)
    - **Source url:** https://goughlui.com/2021/09/03/note-potential-issues-of-using-a-usb-powerbank-as-a-ups/
    - **Community:** Gough Lui tech blog (oscilloscope measurements)
    - **What they built:** A test of power banks used as a UPS.
    - **Problems:**
      - On the SW6208 bank, plugging in a charger dropped the output to 0 V for 125 ms to about 1 s.
      - Cells sit at 4.2 V permanently.
    - **Fixes:**
      - A Xiaomi bank with separate charger and boost stages showed no interruption.
      - Use a Schottky diode and supercapacitor, or a proper UPS.
      - Samsung SDI recommends charging to 4.00-4.05 V for UPS use.
    - **Outcome:** Supports running loads from the battery side, and using a lower charge voltage for long plugged-in periods.
  29.
    - **Product:** Raspberry Pi 4 on a power bank
    - **Source url:** https://forum.storj.io/t/raspberry-pi-4-restarts-switching-from-main-power-to-power-bank/3902
    - **Community:** Storj forum
    - **What they built:** A Pi node with a power bank as backup supply.
    - **Problems:**
      - The Pi reboots when a charger is plugged in while the bank is low.
    - **Fixes:**
      - A better bank, or a dedicated UPS or battery board.
    - **Outcome:** Typical pass-through failure. The architecture should not route the SBC through a power-bank output.
  30.
    - **Product:** Pololu S18V20F12 12 V buck-boost + 4S Li-ion BMS
    - **Source url:** https://forum.pololu.com/t/s18v20f12-and-bms-undervoltage-cut-off-problem/20521
    - **Community:** Pololu forum
    - **What they built:** A sealed 4S device with a 12 V rail.
    - **Problems:**
      - After the BMS undervoltage cutoff (12 V), the regulator input sat at 1.4 V and the output at 0 V.
      - The pack could not be recharged until the regulator was disconnected.
    - **Fixes:**
      - Pololu: the BMS and regulator oscillate (the cell recovers, the regulator's few-mA quiescent load trips the BMS again). Suggested scoping VIN.
      - Implied fix: shut down above the BMS threshold and disable the regulator EN at low voltage.
    - **Outcome:** Not fully resolved in thread. Directly relevant: put a software low-voltage shutdown well above the BMS cutoff, and use regulator EN/UVLO.
  31.
    - **Product:** Pololu S18V20F12 thermal
    - **Source url:** https://forum.pololu.com/t/s18v20fx-heatsinking/21201
    - **Community:** Pololu forum
    - **What they built:** 20 V in, about 2 A out in a tight space.
    - **Problems:**
      - Runs hot near its rating.
    - **Fixes:**
      - Heatsink the inductor, which is the hottest part.
    - **Outcome:** Keep it to the LNB or light loads, as the researcher suggested.
  32.
    - **Product:** XL4015 buck converter from a LiPo to a Jetson Orin Nano
    - **Source url:** https://forums.developer.nvidia.com/t/powering-up-jetson-orin-nano-with-buck-converter-causing-strange-symptoms/343991
    - **Community:** NVIDIA Jetson forum
    - **What they built:** A drone companion computer on LiPo through a cheap buck converter.
    - **Problems:**
      - Audible noise from the board.
      - 12.4 kHz ripple on the buck output, versus under 20 Hz from the adapter.
    - **Fixes:**
      - None conclusive. Advised to check supply peak-current capability.
    - **Outcome:** Cheap converters drop into low-frequency pulse-skipping or PFM. Evidence for forced-PWM, quality converters near SDRs.
  33.
    - **Product:** Battery → switch → 5 V buck → Jetson Nano
    - **Source url:** https://forums.developer.nvidia.com/t/jetson-nano-does-not-autostart-without-unplugging-and-replugging-dc-jack/144315
    - **Community:** NVIDIA Jetson forum
    - **What they built:** A robot power chain with the switch placed before the buck.
    - **Problems:**
      - The board would not auto-boot after a power cycle unless the DC jack was re-plugged.
    - **Fixes:**
      - Put the on/off switch between the buck output and the board, so residual capacitance drains and the rail rises cleanly.
    - **Outcome:** Workaround reported. Relevant to the Q6A header auto-boot inconsistency.
  34.
    - **Product:** 4S LiPo + Pololu D36V50F12 (12 V, 4.5 A) for a Jetson Orin Nano
    - **Source url:** https://forums.developer.nvidia.com/t/powering-jetson-orin-nano-from-4s-lipo-using-pololu-12v-regulator-is-it-safe/337868
    - **Community:** NVIDIA Jetson forum
    - **What they built:** A drone companion computer on 4S with a 12 V buck.
    - **Problems:**
      - Whether a 4.5 A regulator is OK for a 25 W module.
    - **Fixes:**
      - NVIDIA: size for peak currents (TDP 25 W).
    - **Outcome:** Same 4S to 12 V pattern as our plan, and an accepted approach. The D36V50Fx has an ultrasonic power-save mode at light load (https://www.pololu.com/product/4092), so its frequency changes with load.
  35.
    - **Product:** LTC3780 buck-boost modules (AliExpress-type)
    - **Source url:** https://forum.allaboutcircuits.com/threads/ltc3780-voltage-falling-after-a-couple-of-seconds-under-load.181173/
    - **Community:** All About Circuits (403 to fetch — content from search-engine excerpt)
    - **What they built:** A 12 V supply for a 48 W LED load.
    - **Problems:**
      - Output collapses after a few seconds under load.
      - Responders suspect overheating or undetected oscillation, and note inconsistent quality control on imported modules.
    - **Fixes:**
      - Not confirmed.
    - **Outcome:** Unverified (excerpt). Plus element14 reports Chinese and demo LTC3780 boards were 'staggeringly noisy', and filters helped but not enough (https://community.element14.com/challenges-projects/project14/portable-electronics-kit/f/forum/39004/ltc3780-buck-boost-converter).
  36.
    - **Product:** Cheap Chinese BMS boards in a solar SatNOGS station
    - **Source url:** https://community.libre.space/t/green-satnogs-station-project/5324
    - **Community:** SatNOGS community (community.libre.space)
    - **What they built:** An off-grid Raspberry Pi SatNOGS station with an ESP32 power-gating the Pi.
    - **Problems:**
      - Cheap BMS boards (4 for the price of one) did not balance the cells.
      - The Pi drew about 1 A during observations and 200-400 mA idle.
    - **Fixes:**
      - Bought a proper balancing PCM.
      - An ESP32 switches the Pi off when no observation is scheduled.
    - **Outcome:** Worked after replacing the BMS. Verify balancing on any 4S BMS.
  37.
    - **Product:** 4S BMS boards (25 A/40 A class)
    - **Source url:** https://done.land/components/power/powersupplies/battery/bms/4s/25a/
    - **Community:** done.land
    - **What they built:** Notes on generic 4S BMS boards.
    - **Problems:**
      - Ships 'locked' with no output, and locks again after an over-current trip.
      - Over-discharge cutoff is only 2.8 V, over-charge 4.25 V.
      - Needs cells matched within 0.05 V.
      - Tiny 0 Ω solder-bridge configuration.
    - **Fixes:**
      - Unlock by applying 16.8-17.0 V or a charger to the output.
      - Match cells before assembly.
    - **Outcome:** Expected behaviour. Same activation issue reported at https://forum.allaboutcircuits.com/threads/how-to-active-lithium-bms.191294/
  38.
    - **Product:** Molicel P50B from a flashlight vendor (Wurkkos)
    - **Source url:** https://budgetlightforum.com/t/fake-or-damaged-molicell-p50b/230574
    - **Community:** BudgetLightForum
    - **What they built:** Buying a spare 21700.
    - **Problems:**
      - The cell arrived visibly used (oxidation, scratches) and nearly flat.
      - Suspected fake or used.
    - **Fixes:**
      - Return or replace it; compare with genuine P45B appearance.
    - **Outcome:** Quality and counterfeit risk is real even from known vendors.
  39.
    - **Product:** Samsung 50S 21700 bench test
    - **Source url:** https://forum.esk8.news/t/mooch-s-bench-test-results-samsung-50s-25a-5000mah-21700-a-great-performer-but-ran-a-little-hot/56544
    - **Community:** esk8.news (Battery Mooch)
    - **What they built:** An independent cell test.
    - **Problems:**
      - Runs close to 90 °C at 25 A, so it is re-rated to 20 A continuous.
    - **Fixes:**
      - Stay at or under 20 A.
    - **Outcome:** 5117 and 5122 mAh measured; best round cell under 10 A. Our ~3 A load is trivial for it.
  40.
    - **Product:** SunFounder TS7-Pro 7-inch LCD + Pi 4 + RTL-SDR V3 on a battery pack
    - **Source url:** https://www.rtl-sdr.com/sunfounder-ts7-pro-touch-screen-review-building-a-portable-rtl-sdr-pi-4-system/
    - **Community:** RTL-SDR.com
    - **What they built:** A portable touchscreen SDR.
    - **Problems:**
      - The LCD's driver board and ribbon cables created visible spectrum interference, mostly coupled through the antenna and coax.
      - A USB dongle at boot stopped the display being detected (possibly battery current at boot).
    - **Fixes:**
      - Put the antenna on a few metres of good coax away from the LCD (reduced but did not eliminate it).
      - Plug the dongle in after boot.
    - **Outcome:** Partly mitigated. A bright display and its supply are an RF noise source in our build too.
  41.
    - **Product:** Airspy HF+ + Raspberry Pi 3 + 7-inch LCD on a 13,000 mAh power bank
    - **Source url:** https://www.rtl-sdr.com/going-portable-with-the-airspy-hf-rapsberry-pi-and-7-inch-touch-lcd/
    - **Community:** RTL-SDR.com
    - **What they built:** A portable HF receiver.
    - **Problems:**
      - Finding a battery with enough current.
      - Voltage drop in the micro-USB cable.
      - Noise from the Pi's USB bus.
    - **Fixes:**
      - Not detailed in the article.
    - **Outcome:** About 3.5 h of runtime with Gqrx on the Pi. Host EMI goes into the receive path.
  42.
    - **Product:** TI BQ25798 hobby board
    - **Source url:** https://github.com/Marek128b/BQ25798-mppt-solar-charger
    - **Community:** GitHub
    - **What they built:** An open-source 1-4S, 5 A, I2C MPPT charger board with USB-C and solar inputs.
    - **Problems:**
      - V1.0: CE pin had no pull-down, no voltage markings, footprints too small.
      - V2.0: VAC1/VAC2 wired to VBUS instead of VIN1/VIN2.
    - **Fixes:**
      - Fixed in V2.0/V2.1: NTC divider, VAC wiring, R6 = 4.3 kΩ.
    - **Outcome:** A working community design exists, so option B is buildable without TI's EVM. No efficiency or thermal data published.
  43.
    - **Product:** TI BQ25798 charge control
    - **Source url:** https://e2e.ti.com/support/power-management-group/power-management/f/power-management-forum/1264245/bq25798-disable-charging
    - **Community:** TI E2E (403 to fetch — content from search-engine excerpt)
    - **What they built:** Host-controlled charging.
    - **Problems:**
      - Clearing EN_CHG over I2C did not always stop charging mid-cycle.
    - **Fixes:**
      - Using the hardware CE pin worked.
    - **Outcome:** Unverified (excerpt). Also note the watchdog resets registers to defaults per the datasheet, so the host must reconfigure the chip or disable the watchdog.
- **Common problems:**
  1.
    - **Problem:** Voltage sag and brown-out shutdowns on 1S packs with high-current boost, and with weak cell contacts or holders.
    - **Affected products:** uConsole CM4/CM5 handhelds (18650, 21700 holders, LiPo flat-packs); 1S power-bank SoC boards (option D)
    - **Frequency:** common
    - **Known fix:** Use a higher series count (2S-4S) and a buck converter. Use high-drain cells (Molicel, Samsung 50S, LG). Spot-weld or solder the cells. Keep battery leads short.
    - **Fix sources:**
      - https://forum.clockworkpi.com/t/35-000mah-uconsole-the-everything-build-stl/23365
      - https://forum.clockworkpi.com/t/cm5-lite-trixie-nvme-boot/22359
      - https://forum.clockworkpi.com/t/uconsole-only-uses-1-of-the-2-batteries-since-switching-to-hacker-gadgets-dual-21700-battery-holder/23476
  2.
    - **Problem:** Voltage or OCV-based fuel gauges are badly wrong under variable SDR load: they read 100% for hours, then the device dies at 30-80%.
    - **Affected products:** uConsole battery gauge; Particle Tachyon (QCS6490) PMIC gauge
    - **Frequency:** common
    - **Known fix:** Coulomb counting with an external shunt monitor (INA228/INA226). Calibrate and reset at full charge under realistic load. Declare the pack's capacity.
    - **Fix sources:**
      - https://community.particle.io/t/battery-percentage-tracking-wildly-wrong/70194
      - https://forum.clockworkpi.com/t/good-runtime-but-inaccurate-charge-level-indicator-despite-calibration/22410
  3.
    - **Problem:** Pass-through power banks and power-bank SoCs drop or reboot their output when a charger is connected or removed. PD renegotiation also cuts output.
    - **Affected products:** SW6208/SW6306 banks; generic USB-C PD power banks (options D and E); Raspberry Pi and SBC loads
    - **Frequency:** common
    - **Known fix:** Run the SBC from the battery side (or a separate boost stage) rather than the bank's output. Separate charger and boost paths. A diode and supercapacitor buffer as a last resort.
    - **Fix sources:**
      - https://goughlui.com/2021/09/03/note-potential-issues-of-using-a-usb-powerbank-as-a-ups/
      - https://mysku.club/blog/russia-stores/107502.html
      - https://forum.storj.io/t/raspberry-pi-4-restarts-switching-from-main-power-to-power-bank/3902
  4.
    - **Problem:** The board does not boot automatically when power is restored and needs a button press.
    - **Affected products:** Radxa Dragon Q6A on the 3-pin header (some boards); Jetson Nano behind a buck converter; Particle Tachyon after depletion
    - **Frequency:** occasional
    - **Known fix:** Update the Q6A SPI/BIOS firmware. Put the switch after the converter so the rail rises cleanly. As a fallback, have an MCU or RC circuit pulse J21 pin 3 (PWR) to GND after power-up.
    - **Fix sources:**
      - https://forum.radxa.com/t/how-to-setup-dragon-q6a-to-boot-without-pressing-the-power-button/30852
      - https://forums.developer.nvidia.com/t/jetson-nano-does-not-autostart-without-unplugging-and-replugging-dc-jack/144315
      - https://community.particle.io/t/sys-auto-boot-does-not-work-after-lipo-battery-dies/70372
  5.
    - **Problem:** Significant residual draw after software shutdown.
    - **Affected products:** Radxa Dragon Q6A (1.9-2.5 W after halt; SY81012 'ALWAYS ON'); Raspberry Pi CM5 in the uConsole
    - **Frequency:** common
    - **Known fix:** A hard master switch, or a MOSFET load switch cut by an MCU or GPIO after shutdown completes. A hard-off button mod.
    - **Fix sources:**
      - https://forum.radxa.com/t/upcoming-radxa-dragon-q6a/26723
      - https://forum.clockworkpi.com/t/35-000mah-uconsole-the-everything-build-stl/23365
  6.
    - **Problem:** USB-C back-feed: the Q6A Type-C port is wired to the 12 V input, so anything plugged in while the header is powered gets reverse-supplied.
    - **Affected products:** Radxa Dragon Q6A
    - **Frequency:** rare
    - **Known fix:** Seal or cover the Q6A USB-C port. Make the charger board's USB-C the only external port.
    - **Fix sources:**
      - https://docs.nura.eco/phone-harness/main/connecting-devices/radxa-dragon-q6a.html
      - https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
  7.
    - **Problem:** The BMS ships locked or locks after a fault. The BMS undervoltage cutoff interacts with the regulator's quiescent current and oscillates, leaving the pack uncharged.
    - **Affected products:** Generic 4S BMS boards; Pololu S18V20F12 behind a 4S BMS; IP2368 boards that need a USB-C 'kick' after the battery is connected
    - **Frequency:** occasional
    - **Known fix:** Unlock by applying the charger voltage. Shut down in software at about 3.3 V/cell (13.2 V), well above the BMS 2.5-2.8 V cutoff. Drive the regulator EN low at low voltage. Use the IP2368_NACT variant or kick it with 5 V on USB-C.
    - **Fix sources:**
      - https://forum.pololu.com/t/s18v20f12-and-bms-undervoltage-cut-off-problem/20521
      - https://done.land/components/power/powersupplies/battery/bms/4s/25a/
      - https://mysku.club/blog/aliexpress/100034.html
  8.
    - **Problem:** Cheap BMS or balancer boards that do not balance, or balance wrongly.
    - **Affected products:** Generic AliExpress BMS boards; SW6306 bank balancer
    - **Frequency:** occasional
    - **Known fix:** Use a known-good balancing BMS. Check cell voltages after several cycles. Start with cells matched within 0.05 V.
    - **Fix sources:**
      - https://community.libre.space/t/green-satnogs-station-project/5324
      - https://mysku.club/blog/russia-stores/107502.html
  9.
    - **Problem:** Power MOSFETs and LDOs on cheap bidirectional charger boards overheat at full power (over 100 °C), and some units are dead on arrival or fail.
    - **Affected products:** IP2368 boards; SW6306 banks
    - **Frequency:** common
    - **Known fix:** Program a lower charge current (IP2368 R3), for example 2.5-3 A, which is about 40-50 W into 4S. Heatsink or thermal pad to the case. Replace the 5 V LDO. Buy two boards.
    - **Fix sources:**
      - https://mysku.club/blog/aliexpress/100034.html
      - https://mysku.club/blog/russia-stores/107502.html
  10.
    - **Problem:** Switching-converter and display noise in SDR receive paths: low-frequency pulse-skipping ripple, noisy LTC3780 modules, LCD ribbon interference.
    - **Affected products:** XL4015 and LTC3780 modules; 7-inch LCDs next to an RTL-SDR; Pi USB bus with an Airspy HF+
    - **Frequency:** common
    - **Known fix:** Quality forced-PWM converters. LC/π filtering. Shielding. Distance and good coax between antenna and electronics. Antenna away from the display.
    - **Fix sources:**
      - https://forums.developer.nvidia.com/t/powering-up-jetson-orin-nano-with-buck-converter-causing-strange-symptoms/343991
      - https://www.rtl-sdr.com/sunfounder-ts7-pro-touch-screen-review-building-a-portable-rtl-sdr-pi-4-system/
      - https://community.element14.com/challenges-projects/project14/portable-electronics-kit/f/forum/39004/ltc3780-buck-boost-converter
  11.
    - **Problem:** LMS7002M-based PCIe SDRs run hot (60-85 °C), adding fan power and heat to a sealed case.
    - **Affected products:** LimeSDR XTRX; LimeSDR Micro (Lime says design cooling for 10 W)
    - **Frequency:** common
    - **Known fix:** A 40 mm fan (gives 50-55 °C), a thermal pad to a copper pour, and a heatsink.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/temperature-of-limesdr-xtrx/8366
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
  12.
    - **Problem:** Used, relabelled or counterfeit 21700 cells.
    - **Affected products:** Molicel P50B and P45B, Samsung 50S from non-authorised sellers
    - **Frequency:** occasional
    - **Known fix:** Buy from authorised distributors. Inspect the terminals and wrap. Run a capacity and internal-resistance test before welding.
    - **Fix sources:**
      - https://budgetlightforum.com/t/fake-or-damaged-molicell-p50b/230574
      - https://forum.esk8.news/t/mooch-s-bench-test-results-samsung-50s-25a-5000mah-21700-a-great-performer-but-ran-a-little-hot/56544
  13.
    - **Problem:** Random reboots or freezes that look like brown-outs but are a UFS driver issue.
    - **Affected products:** Q6A + Radxa 256 GB Kioxia UFS (powered by the official 12 V adapter)
    - **Frequency:** occasional
    - **Known fix:** Kernel with the Kioxia PA_TACTIVATE quirk (radxa/kernel linux-6.18.2 fix, Armbian 26.05+). Hold the package until the official kernel includes it.
    - **Fix sources:**
      - https://forum.radxa.com/t/ufs-random-reboots/30630
  14.
    - **Problem:** PD-sink inputs fail with sources that lack the right PDO or proper PD support (laptops, USB-A cables, 5 V-only chargers).
    - **Affected products:** Particle Tachyon; uConsole with a MacBook PD adapter; Q6A when fed by a CH224D sink
    - **Frequency:** occasional
    - **Known fix:** Avoid PD for the SBC input: feed the regulated 12 V header from the battery, and do PD only at the charger.
    - **Fix sources:**
      - https://community.particle.io/t/my-tachyon-isnt-charging/70368
      - https://forum.clockworkpi.com/t/uconsole-charging-issue-with-motherboard-noise/20836
      - https://forum.radxa.com/t/question-about-power-supply-for-dragon-q6a/30629
- **Unresolved problems:**
  1.
    - **Problem:** No published measurement of a Q6A and LimeSDR Micro M.2 running together, and the M.2 3.3 V source chain is unproven at that load.
    - **Why it matters for us:** In the schematic, VCC_3V3_MKEY is an ETA3521 buck fed from VCC_5V_PERI. That is an SY7120 boost from the ~4.2 V VPH_PWR rail, shared with USB (RTL-SDR) and the fan. If that boost limits at 4-8 W of SDR plus USB load, the Lime will brown out. Measure 3.3 V at the card through the 2230-to-2280 extension under load.
    - **Evidence:** Lime says ~4 W typical with a 10 W cooling design (https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304). Q6A schematic v1.21 shows the 5V_PERI to 3V3_MKEY chain. No community Q6A+Lime build found.
  2.
    - **Problem:** Q6A boot when powered from the header is inconsistent: some boards need the PWR button.
    - **Why it matters for us:** After a BMS cutoff, or after charging a flat pack, the receiver may not start without user action. If a GPIO or MCU-driven power switch is used, it must also pulse J21 pin 3.
    - **Evidence:** https://forum.radxa.com/t/how-to-setup-dragon-q6a-to-boot-without-pressing-the-power-button/30852 (BIOS update suggested, no confirmation).
  3.
    - **Problem:** Q6A draws 1.9-2.5 W after software shutdown, and Radxa has published no fix.
    - **Why it matters for us:** A 72 Wh pack goes flat in about 1.5 days if 'shut down' devices are stored without a hard cut. The power architecture needs a true master switch or load switch.
    - **Evidence:** https://forum.radxa.com/t/upcoming-radxa-dragon-q6a/26723 (willy, 2025-09-21).
  4.
    - **Problem:** Radxa staff and docs disagree on the header input range: 4.5-16 V vs 3.6-16 V, the docs say 12 V only, and one staff post calls direct 12 V 'not recommended'.
    - **Why it matters for us:** If 9-12.6 V is truly fine, a 3S pack (54 Wh) can feed the header directly with no external switching regulator. That is less noise, fewer failure modes and fewer parts. No one has published a bench test or long-term run at 3S direct.
    - **Evidence:** https://forum.radxa.com/t/dragon-q6a-12v-input-header-voltage-range/30233 ; https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400 ; https://docs.radxa.com/en/dragon/q6a/hardware-use/power-header
  5.
    - **Problem:** IP2368/IP2366 behaviour with a load on the battery side during charging is undocumented. Termination may never be reached, CV may be held at 4.2 V, and the safety timer may stop charging. Its interaction with a locked BMS is also undocumented.
    - **Why it matters for us:** The 'use while charging' plan (load on the battery) depends on it. A charger that never terminates ages the cells. One that times out stops charging during long blackout sessions.
    - **Evidence:** The mysku IP2368 review did not test pass-through (https://mysku.club/blog/aliexpress/100034.html). Gough Lui notes safety-timer risks in UPS use.
  6.
    - **Problem:** Quality variance of AliExpress IP2368 boards: dead-on-arrival units, a reported spontaneous burn-out, and heat over 100 °C at 5 A.
    - **Why it matters for us:** This is the only charge path in a sealed handheld, and a fire risk near Li-ion cells. Buy spares, derate the charge current, and add a thermal fuse or NTC.
    - **Evidence:** https://mysku.club/blog/aliexpress/100034.html ; retail review excerpt reporting one 'randomly fried itself' (from search; desertcart page not fetchable).
  7.
    - **Problem:** IP2368 boards ship with a fixed 10 kΩ resistor in place of the NTC, so there is no cold-charge inhibit.
    - **Why it matters for us:** In Ukrainian winter, charging below 0 °C plates lithium. A real thermistor on the cells must be fitted and its cold threshold verified.
    - **Evidence:** https://mysku.club/blog/aliexpress/100034.html ; https://done.land/components/power/powersupplies/battery/chargers/charge-discharge/ip2366/ (typical 0-45 °C charge window).
  8.
    - **Problem:** No RF-noise measurements of IP23xx chargers, LTC3780 or Pololu converters next to SDR inputs (137 MHz to 2.2 GHz).
    - **Why it matters for us:** The charger may run during passes when solar or power-bank charging happens in the field. Its unknown spurs could land on LRPT or HRPT. Plan an 'inhibit charging during recording' option (CE or EN control) and an A/B noise-floor test.
    - **Evidence:** Only generic reports: https://forums.developer.nvidia.com/t/powering-up-jetson-orin-nano-with-buck-converter-causing-strange-symptoms/343991 ; element14 LTC3780 noise thread (excerpt).
  9.
    - **Problem:** Bullseye LNB current draw is not published.
    - **Why it matters for us:** It sizes the switched 12-13 V LNB feed and polyfuse, if an LNB is kept with a non-dish antenna.
    - **Evidence:** Search found no figure. BATC forum unreachable (503).
  10.
    - **Problem:** Power draw of a 1000+ nit sunlight-readable HDMI panel has not been measured.
    - **Why it matters for us:** The display may be the second-largest load (estimated 5-10 W), which dominates runtime estimates.
    - **Evidence:** Only vendor specs for dimmer panels (6 W at 300 nit); no measured data found.
  11.
    - **Problem:** Linux support on the Q6A for the I2C fuel gauge: INA228 is in the mainline ina238 hwmon driver, but whether the Radxa kernel enables it and whether the 40-pin I2C overlays work is unverified.
    - **Why it matters for us:** The on-screen battery and runtime display depends on it. A Q6A UART overlay had a bug, fixed by a user but not merged (September 2026), so the same could happen with I2C.
    - **Evidence:** https://docs.kernel.org/hwmon/ina238.html ; https://forum.radxa.com/t/using-uart-in-native-mode-solved/30063
  12.
    - **Problem:** Charging from USB-C PD solar panels or fluctuating sources through the IP23xx (no MPPT): repeated renegotiation and dropouts under clouds are undocumented.
    - **Why it matters for us:** Solar charging is a stated blackout use case. Without MPPT, a panel may cycle or harvest poorly. The BQ25798 handles this but has few ready-made modules.
    - **Evidence:** No community report found. The BQ25798 hobby board exists: https://github.com/Marek128b/BQ25798-mppt-solar-charger
- **Communities checked:**
  - Radxa forum (forum.radxa.com): reachable through the Discourse JSON API; about 20 topics read
  - GitHub geerlingguy/sbc-reviews issue #85 (Q6A power measurements)
  - MyriadRF/Lime discourse (discourse.myriadrf.org): reachable
  - Crowd Supply LimeSDR Micro updates
  - Lime docs: LimeSDR Micro M.2 setup page
  - SatNOGS community (community.libre.space): reachable
  - ClockworkPi forum (uConsole/DevTerm handheld SDR builds): reachable
  - Particle community (Tachyon, QCS6490): reachable
  - Pololu forum: reachable
  - NVIDIA Jetson developer forum: reachable
  - BudgetLightForum: reachable
  - esk8.news (Battery Mooch tests): reachable
  - mysku.club (Russian-language hands-on reviews): reachable
  - Gough Lui blog
  - RTL-SDR.com: searched through the WordPress API
  - done.land hobbyist wiki
  - nura.eco docs (Q6A header powering)
  - Kernel docs: hwmon ina238
  - GitHub repository search (IP2368, BQ25798) and the LimeSuiteNG issue tracker
  - Radxa docs: Q6A power header and GPIO pages; Q6A schematic v1.21 (read directly)
  - Hackaday blog (WordPress API): no relevant hits
  - Reddit: BLOCKED (403 from www, old and api endpoints); not checked directly
  - EEVblog: search behind a CAPTCHA; no IP2368 or LTC3780 topic URLs found through web search
  - mikrocontroller.net: Cloudflare 403; only search-engine excerpt of topic 569785
  - BATC forum: unreachable (503)
  - element14, All About Circuits, TI E2E, MakerWorld: 403 to fetch; only search-engine excerpts used
  - hackaday.io: login wall
  - Ukrainian sources (ti.ua, dou.ua, itc.ua) through web search: only generic blackout and power-bank advice, no IP2368/4S build reports
- **Recommendation impact:** Keep the overall architecture: an external pack, a BMS, an IP23xx USB-C charger, a regulated feed into the Q6A J21 header, and an INA228 coulomb counter. Community evidence supports it: on-board PMIC battery use is impossible on the Q6A, PD inputs are fragile, and power banks reboot SBCs on pass-through. Add these changes:
  
  1. **Consider 3S direct.** Radxa staff twice said J21 accepts 4.5-16 V. A 3S1P 21700 pack (9.0-12.6 V, ~54 Wh) could feed J21 directly through a fuse and load switch, with no external 12 V converter. That removes the noisiest, most failure-prone stage (LTC3780 modules have poor community reports: noisy, output collapsing at ~48 W). A 4S pack still needs a regulator, because 16.8 V exceeds the 16 V limit, the 16 V input capacitors and the SMBJ15CA TVS. Bench-test 3S direct first, since the docs still say 12 V. If 4S (72 Wh) is kept, use a quality forced-PWM buck rather than an LTC3780 module.
  
  2. **Hard power cut.** Add a true master switch or MOSFET load switch. The Q6A draws 1.9-2.5 W after halt. Place it after the converter so the 12 V rail rises cleanly. Wire J21 pin 3 (PWR) so an MCU or RC pulse can start boards that do not auto-boot.
  
  3. **Software low-voltage shutdown at about 3.3 V/cell.** BMS cutoffs are only 2.5-2.8 V. Shutting down early avoids BMS lock-out, the regulator oscillation seen on the Pololu forum, and the IP2368 kick-start requirement.
  
  4. **Configure the IP2368/IP2366 board defensively.**
     - Lower the charge current to about 2.5-3 A (R3), because the MOSFET exceeded 100 °C at 5 A.
     - Fit a real NTC on the cells in place of the fixed 10 kΩ, for 0 °C and 45 °C inhibit.
     - Consider 4.1 V/cell (R4) for long plugged-in blackout use.
     - Prefer the IP2368_NACT variant.
     - Keep a spare board, since dead-on-arrival units occur.
     - Use a separate balancing BMS and verify it actually balances.
  
  5. **Fuel gauge.** Use the INA228/INA226 coulomb counter rather than voltage-based state of charge; uConsole and Tachyon voltage gauges were off by 20-90%. Plan a fallback (a small MCU over USB) if Q6A 40-pin I2C overlays misbehave.
  
  6. **Budget numbers.** Measured Q6A figures replace the estimates: 2.9 W idle, about 10 W maximum at the wall. Add the LimeSDR at ~4 W plus a fan, since XTRX experience shows LMS7002M boards need active cooling. Check that the Q6A's internal 5 V boost, which feeds the M.2 3.3 V rail, can actually carry the LimeSDR load.
  
  7. **Drop options D, E and F.** SW62xx and SW6306 power banks showed output resets, 100 °C MOSFETs and faulty balancers. 1S builds show sag shutdowns.
  
  8. **BQ25798 stays the upgrade path for solar MPPT.** An open hobby board exists on GitHub, so it is no longer EVM-only.
  
  9. **Rule out UFS first.** Rule out the Kioxia UFS bug (fixed kernel) before blaming the power system for reboots.

## Власні виправлення (`fixes`)

_Run `wf_f924b2ab-5ad`_

- **Component:** Power system (battery, charging, converters, fuel gauge) for the Radxa Dragon Q6A handheld satellite receiver (v3)
- **Fixes:**
  1.
    - **Problem:** No published measurement of a Q6A and LimeSDR Micro M.2 running together, and the M.2 3.3 V source chain is unproven at that load.
    - **Proposed fix:** The Q6A schematic v1.21 (sheets 'DC-IN' and 'M_KEY', read directly) shows plenty of headroom. The real weak points are the 2230-to-2280 extension and heat, so verify those and fix them if needed.
  
  The verified chain:
  - 12 V input to a SY81012VDC buck: 2.7-16 V in, 12 A. Its feedback divider (120k/20k, 0.6 V reference) sets VPH_PWR to 4.2 V. Its MODE resistor (62 kΩ) gives about 1 MHz.
  - VPH_PERI to a SY7120RAC boost (U24). The ILMT resistor (100 kΩ) sets a 10 A peak switch limit (ILMT = 1200/R in kΩ, minus 2). The FS resistor (100 kΩ) gives about 1.04 MHz. The feedback divider (80.6k/20k, 1 V reference) sets 5.03 V. The inductor (L47) is 1.5 µH/10 A.
  - VCC_5V_PERI to a dedicated M.2 buck, ETA3521 (U20): 2.5-6 V in, 4 A, 2 MHz COT, 1 µH/4 A inductor. Its 91k/20k divider sets 3.33 V. Its enable comes from PMIC LDO L18B.
  
  The load against that chain:
  - My calculation: the boost can supply about 7 A (~35 W) at 5 V before hitting its current limit.
  - LimeSDR worst case is 8.25 W (the PCIe 2.5 A allowance), and Lime staff say about 4 W typical. That is 1.2-2.5 A of the ETA3521's 4 A, or about 1-1.9 A from the 5 V rail.
  - The USB-A VBUS goes through WS4612 load switches. Their 3.24 kΩ ISET resistors give a limit of about 2.1 A (Ilim = 6800/Rset).
  
  Keep VCC_5V_PERI lightly loaded: put the display and fan on external rails, and leave only the RTL-SDR (~0.27 A) on USB.
    - **Steps:**
      - Use a short, rigid 2230-to-2280 extender (a PCB or metal-bracket type, not a flex riser).
  - Measure the resistance of its 3.3 V path end to end: pins 2, 4, 12, 14, 16, 18, 70, 72 and 74 against the GND pins. Use 4-wire measurement or a 1 A test current. Target <50 mΩ.
      - Put a heatsink or thermal pad on the LimeSDR shield (Lime's guide says to design cooling for at least 10 W). Make sure the Q6A fan airflow reaches the M.2 area.
      - Boot and check the PCIe link:
  - `lspci -vv | grep -E 'LnkCap|LnkSta'` should show 8GT/s x1.
  - `dmesg | grep -iE 'aer|pcie.*(error|link)'` should be clean.
      - Run a 60-minute worst-case load, all at once:
  - `stress-ng --cpu 8 --timeout 3600 &`
  - An NPU benchmark.
  - `rtl_test -s 2.4e6` on the RTL-SDR.
  - A Lime RX stream: run `SoapySDRUtil --find` to get the driver key, then `SoapySDRUtil --args="driver=<key>" --rate=61.44e6 --direction=RX`.
      - During the load test, measure at the card end of the extender.
  - DMM: 3.3 V should be at least 3.20 V (absolute minimum 3.135 V, which is −5%).
  - Scope (AC-coupled, 20 MHz bandwidth): ripple or droop under 100 mV p-p.
  - Also check the 40-pin 5 V (pin 2): at least 4.85 V.
      - Check temperatures with an IR thermometer or thermocouple: the Lime shield, the Q6A M.2-buck area and the SY7120 area should all stay under about 85-90 °C.
      - If 3.3 V sags, try these in order:
  - Replace the extender.
  - Add 2x 100 µF low-ESR polymer capacitors on the card-side 3.3 V pads, if the extender has pads.
  - Last resort: cut the extender's 3.3 V trace and feed the card from a separate 3.3 V/3 A synchronous buck. Never parallel it with the Q6A's ETA3521.
    - **How to verify:** Pass when all of these hold over 60 minutes at 61.44 Msps with CPU and NPU loaded:
  - No PCIe AER errors or link drops.
  - No SoapySDR overflows ('O').
  - 3.3 V at the card ≥3.20 V and 40-pin 5 V ≥4.85 V.
  - No thermal throttling.
  
  Record the J21 input power with the INA228 so the real Q6A+Lime figure replaces the estimates in the power budget.
    - **Confidence:** medium
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1912111437_Silergy-Corp-SY7120RAC_C207631.pdf
      - https://atta.szlcsc.com/upload/public/pdf/source/20240509/0FD7B458A1C7C9AED0BF280C094B69EB.pdf
      - https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2403151643_etasolution-ETA3521FSG_C22362743.pdf
      - https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
  2.
    - **Problem:** Q6A boot when powered from the header is inconsistent: some boards need the PWR button.
    - **Proposed fix:** Likely root cause, found in the schematic (JTAG sheet) and a UART log:
  - The board fakes a power-key press at every cold power-up. An SGM811 supervisor (U7) on the PMIC's always-on VREG_SYS_1P8 drives Q18/Q17 through an RC (R75 10 kΩ, C325 10 µF), and Q17 pulls PWR_ON_KEY (= J21 pin 3) low.
  - The pulse lasts the SGM811 reset timeout (240 ms typical, 150-560 ms rated) plus about 70 ms of RC delay (my estimate). That is roughly 0.2-0.6 s.
  - The UEFI log posted on the Radxa forum says: 'Boot up PwrKey press 75 ms detected is less than expected 400 ms duration.' So the firmware wants at least 400 ms and only sees part of the pulse.
  - The result therefore varies from unit to unit and with temperature and supply ramp.
  - Re-applying power within a few seconds of a shutdown does not re-trigger the circuit, because VREG_SYS_1P8 has not collapsed.
  
  The fix:
  - Update the boot firmware.
  - Generate a guaranteed long press externally on J21 pin 3, open-drain only, from the small power-controller MCU that also handles shutdown (see the next fix).
    - **Steps:**
      - Update the SPI boot firmware to the latest Radxa release, using the Radxa staff method from the folder flat_build/spinor/dragon-q6a: `sudo edl-ng --hostdev-as-target /dev/mtd0 rawprogram rawprogram0.xml patch0.xml`.
      - Connect a 3.3 V USB-UART to 40-pin pins 6, 8 and 10 (GND, TX, RX) at 115200 baud. Log cold boots and look for the 'PwrKey press N ms' line.
      - Add an open-drain 'press' on J21 pin 3.
  - Use a 2N7002 or AO3400 (gate through 1 kΩ, 100 kΩ pull-down) or a PC817 optocoupler, with the switch from pin 3 to pin 2 (GND).
  - Never drive pin 3 high: it is the PMIC's KPD_PWR_N net (1.8 V domain), wired-OR with the on-board button.
      - Add a power-controller MCU (ATtiny402/412 or CH32V003), fed from the pack by a TLV70433 LDO (2.5-24 V in, 3.2 µA quiescent).
  - Firmware: when the case button is pressed, close the load switch and at the same moment pull pin 3 low for 1.5 s, then release.
  - At t = 10 s, check 40-pin pin 1 (3.3 V, present only while the PMIC is running).
  - If it is absent, retry once with a 2 s press.
  - Only ever pulse when pin 1 is absent, because a press while the board is running asks it to shut down.
      - Fallback without an MCU: wire J21 pin 3 to a second case button. Optional board mod: add 47-100 µF (6.3 V, X5R) in parallel with C325 to lengthen the on-board pulse (my estimate: +0.2-0.5 s).
      - After a deliberate power-off, leave input power removed for at least 10 s before re-applying it.
    - **How to verify:** Run 50 cold power-ups (input off ≥10 s) at room temperature and 20 at about −10 °C (pack and board in a freezer).
  - Pass: 50/50 and 20/20 reach login.
  - The UART log shows a press of at least 400 ms.
  - With the board already running, the MCU must not issue a 1.5 s press (it checks pin 1 first).
    - **Confidence:** medium
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://forum.radxa.com/t/upcoming-radxa-dragon-q6a/26723
      - https://forum.radxa.com/t/how-to-setup-dragon-q6a-to-boot-without-pressing-the-power-button/30852
      - https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/SGMICRO_2D00_SGM811.pdf
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/power-header
      - https://www.ti.com/lit/ds/symlink/tlv704.pdf
  3.
    - **Problem:** Q6A draws 1.9-2.5 W after software shutdown, and Radxa has published no fix.
    - **Proposed fix:** Analysis:
  - The 1.9-2.5 W report says it was measured after typing 'halt'. On systemd, halt stops the CPUs but does not power the board off, which fits the reporter's own remark that the figure depended on CPU frequency.
  - In the schematic, the 5 V boost (SY7120 EN), the 3.3 V and 1.8 V bucks and the M.2 3.3 V buck are all enabled from PMIC LDO L18B. A real `poweroff` should therefore switch them all off.
  - That would leave only the always-on SY81012 (650-850 µA quiescent) and the PMIC. My estimate is well under 0.1 W, but this is unverified.
  
  Fix:
  - Always use `poweroff`.
  - Map the power key to poweroff.
  - Add a true hard cut anyway, because 72 Wh stored in 'shut down' devices must not drain.
    - **Steps:**
      - Measure first. Read input power with the INA228 or a DC meter after each of `sudo systemctl halt`, `sudo systemctl poweroff`, and a hard cut.
      - Make the power key power the board off.
  - In /etc/systemd/logind.conf, set HandlePowerKey=poweroff.
  - On GNOME images, also set the power-button action, or use a lightweight session.
  - Run `evtest` to confirm the PMIC power key produces KEY_POWER.
      - Add a hard cut: a Pololu #2812 Big Pushbutton Power Switch MP between the pack fuse and the 12 V regulator.
  - $5.95; 4.5-40 V (32 V recommended); about 8 A; reverse-voltage protection; <0.01 µA when off.
  - ON, OFF and CTRL inputs take pulses above 1 V.
      - MCU logic (same MCU as the previous fix):
  - Short press while running: send a 200 ms pulse on J21 pin 3 for a graceful poweroff.
  - When 40-pin pin 1 (3.3 V) has been gone for 5 s: pulse the Pololu OFF input.
  - Long press of 6 s: forced OFF.
      - Low-battery protection.
  - Linux powers off at 3.40 V/cell, read from the INA228.
  - MCU backup through a pack divider (1 MΩ/150 kΩ + 100 nF): graceful shutdown at 3.30 V/cell, hard cut at 3.20 V/cell.
      - Alternative without an MCU: a script /usr/lib/systemd/system-shutdown/cut-power that uses gpioset (libgpiod) to pulse a 40-pin GPIO, through 1 kΩ, into Pololu OFF. Or simply press the Pololu button after the screen goes dark.
      - For storage and transport, unplug the XT30 battery connector.
    - **How to verify:** With the hard cut open, measure pack current with a DMM in series after 1 minute of settling.
  - Expected: about 0.2-0.3 mA (~4 mW). That is the IP2368 at 180 µA (datasheet standby at 14.8 V) plus the BMS and MCU. Self-discharge then dominates over months.
  - Also confirm that nothing back-powers the Q6A through USB or HDMI while it is off.
    - **Confidence:** high
    - **Sources:**
      - https://forum.radxa.com/t/upcoming-radxa-dragon-q6a/26723
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://www.pololu.com/product/2812
      - https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308290920_INJOINIC-IP2368-BZ-VGLIP_C5203723.pdf
      - https://www.ti.com/lit/ds/symlink/tlv704.pdf
  4.
    - **Problem:** Radxa staff and docs disagree on the header input range (4.5-16 V vs 3.6-16 V vs '12 V only'), and nobody has bench-tested 3S direct.
    - **Proposed fix:** Resolved from the schematic.
  
  What is on the board:
  - J21 pin 1 (ADP12V_IN) connects straight to the ADP12V node. The only parts there are C602 (10 µF/25 V) and the SY81012 input capacitors C611/C612 (22 µF/16 V).
  - The SY81012 operates from 2.7 to 16 V (18 V absolute maximum). Its EN is always on through a 100 kΩ pull-up.
  - There is NO TVS and NO reverse-polarity protection on the header path. The SMBJ15CA sits on the USB-C VBUS side, behind the DMP2160 switch.
  
  What that means:
  - '12 V' is only the nominal value. Radxa staff (BigfootACA) state 3.6-16 V with 5, 9 or 12 V recommended, and say the input is stepped down to 4.2 V by the SY81012.
  - Practical window: about 6-14 V.
  - Upper limit: 16 V ceramics, DC-bias derating, and hot-plug ringing that can reach roughly 2x Vin (LT AN88).
  - Lower limit: 4.2 V output plus dropout, and header current at low voltage.
  
  Recommended topology: 4S plus a 12 V buck.
  - The same rail feeds the LNB.
  - J21 current stays around 2 A.
  
  3S direct also works and is the quietest option, with no external converter. But it gives only 54 Wh, and pin current reaches about 2.8 A at 9 V and 25 W.
    - **Steps:**
      - Bench sweep.
  - Lab supply with a 3.5 A limit, and a 100 µF electrolytic at J21.
  - Boot at 12.0 V and run the full load from the M.2 power test above.
  - Step 14 → 12 → 10 → 9 → 8 → 7 → 6 → 5.5 → 5.0 V, 5 minutes each.
  - Log dmesg, PCIe AER and USB disconnects, and note the brownout voltage.
  - Never go above 15 V.
      - Option A (recommended): 4S → Pololu D36V50F12.
  - $39.95; 13.3-50 V in; 12 V ±4%; up to 4.5 A; about 500 kHz; reverse-voltage protection; EN pin.
  - When the pack falls below about 13.3 V the output simply drops out. The Q6A tolerates this, and the LNB keeps working to about 11.5 V.
      - Option B: 3S (9.0-12.6 V) wired straight to J21.
  - Set the IP2368 cell-count resistor (RBAT_NUM) to 9.1 kΩ and its charge-voltage resistor (RVSET) to 10 kΩ or less.
  - Check J21 pin and wire heating: the header's current rating is not published.
  - The LNB then needs its own small 13 V boost.
      - Add the protection the board lacks at J21:
  - A 3-4 A fuse.
  - Reverse-polarity protection (the Pololu #2812 provides it).
  - An SMBJ14A TVS.
  - A 100-220 µF 25 V electrolytic to damp hot-plug ringing.
      - Use a keyed, latched 3-pin housing with strain relief on J21. A forum user notes the 12 V pin is about 1.5 mm from the USB-C shell ground.
      - Seal the Q6A's own USB-C port with a glued blank plug or a cover. VBUS from any source turns on the Q5 switch and parallels that source with the header rail; Radxa says not to use USB-C when supplying 12 V externally.
      - Never connect raw 4S to J21: 16.8 V, or 16.4 V at 4.10 V/cell, is above the 16 V caps and the SY81012 rating.
    - **How to verify:** - The sweep log shows stable operation from 8 V or lower up to 14 V at full load. The expected brownout is about 4.5-5 V, since VPH_PWR is 4.2 V.
  - J21 pin and wire temperature rise stays under 20 °C at maximum load.
  - A scope on J21 during switch-on shows overshoot below 15 V.
    - **Confidence:** medium
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
      - https://forum.radxa.com/t/dragon-q6a-12v-input-header-voltage-range/30233
      - https://atta.szlcsc.com/upload/public/pdf/source/20240509/0FD7B458A1C7C9AED0BF280C094B69EB.pdf
      - https://www.pololu.com/product/4095
      - https://www.analog.com/media/en/technical-documentation/application-notes/an88f.pdf
      - https://forum.radxa.com/t/upcoming-radxa-dragon-q6a/26723
  5.
    - **Problem:** IP2368/IP2366 behaviour with a load on the battery side during charging is undocumented: termination, CV hold, the safety timer and BMS interaction.
    - **Proposed fix:** Behaviour, from IP2368 datasheet V1.41:
  - Supports 2-5 cells (not 6).
  - CC/CV charging. It terminates when IBAT falls below ISTOP = 100 mA and restarts when VBAT drops below VTRGT − N x 0.1 V.
  - Charge cut-off timer TEND is 45-51 h.
  - VTRGT = 4000 mV + 0.02 x RVSET (Ω) per cell.
  - In current mode, ICHRG = 0.2 x RISET (mA).
  - It switches at 250 kHz.
  
  With the device's load on the battery node, the charger's output current is load plus battery current. Any load above 100 mA means it never terminates: it floats in CV at VTRGT until the 48 h timer.
  
  Fix:
  - Lower the float voltage.
  - Add software termination that uses the NTC-inhibit line from the RF-noise fix below.
  - Balance-charge monthly.
  - Size the charge current for load plus charge.
    - **Steps:**
      - Replace RVSET (R4 on the reviewed board; stock 10 kΩ = 4.20 V) with 5.1 kΩ 1% for 4.10 V/cell (16.4 V pack), or 7.5 kΩ for 4.15 V.
      - Set ISET_MODE to GND through 1 kΩ (R1), and RISET to 15 kΩ. That gives a 3.0 A battery-side limit, so a 65 W PD source covers a ~30 W load plus ~1 A of charging.
      - Put the INA228 shunt directly in the battery lead: pack+ → 10 A fuse → shunt → the node that feeds both IP2368 BAT+ and the load switch. It then sees net battery current. The earlier wiring note placed the IP2368 on the battery side of the shunt, which would hide charging current.
      - Software termination in the gauge daemon:
  - If V ≥ 16.35 V and net current stays within ±0.1 A for 10 minutes, assert CHG_INHIBIT.
  - Release it when V drops below 15.8 V (3.95 V/cell) or the charger is unplugged.
      - Balancing.
  - Cheap BMS boards usually bleed only near 4.18-4.20 V/cell, so at 4.10 V they rarely balance.
  - Once a month, do a full 4.20 V balance charge through the pack's balance lead with an FPV charger such as the ISDT 608PD (about $30-42; USB-C PD input 5-28 V/140 W; 1-6S; 0.8 A/cell balancing). Alternatively, fit a 4S active balancer.
      - 48 h timer: test whether an inhibit toggle restarts it. If it does not, unplug and replug the USB-C cable every 2 days during long blackout sessions, and have the daemon warn you.
      - BMS lockout test: discharge the pack until the BMS trips, then plug in the PD charger. The IP2368 trickle-charges at 50-200 mA below 3 V/cell, which should release the BMS; confirm that it does.
    - **How to verify:** Run 72 h plugged in at typical load.
  - Cells never exceed 4.11 V (DMM on the balance lead).
  - The INA228 log shows inhibit/release cycles.
  - Pack temperature stays under 40 °C.
  - Charging still works after 48 h, or the timer behaviour is documented.
  
  The BMS-lockout recovery succeeds 3 out of 3 times.
    - **Confidence:** medium
    - **Sources:**
      - https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308290920_INJOINIC-IP2368-BZ-VGLIP_C5203723.pdf
      - https://mysku.club/blog/aliexpress/100034.html
      - https://github.com/D-314/IP2368-Arduino-Library
      - https://darwinfpv.com/products/isdt-608pd-lipo-charger-dc-240w-10a-usb-c-140w-5a-smart-digital-charger
      - https://www.ti.com/product/BQ25798
  6.
    - **Problem:** AliExpress IP2368 boards vary in quality: dead-on-arrival units, a reported spontaneous burn-out, and heat over 100 °C at 5 A.
    - **Proposed fix:** Treat the board as untrusted: qualify each one on the bench, derate it, protect it thermally and with fuses, and keep a second, known-good charge path.
  
  Why the boards run hot: the mysku review found the stock RISET is 27 kΩ, which asks for 5.4 A (the chip clamps it to 5 A), and one MOSFET went above 100 °C at 5.1 A. Cutting the charge current to 2.5-3 A cuts the I²R losses by roughly 3-4x.
  
  Other notes from the review:
  - The stock cell-count resistor (R7) is 13 kΩ, which is 4S.
  - The NTC position (R6) has a fixed 10 kΩ resistor.
  - Readers report that the COUT variant needs a 'charge activation' (a USB-C charger plugged in once) before its reverse output works. The NACT variant does not.
    - **Steps:**
      - Buy 2-3 boards (about $5-10 each; prices unverified). Choose listings whose photos show the IP2368 marking, and note the variant (COUT or NACT).
      - Incoming check with a DMM:
  - R7 13 kΩ = 4S.
  - RVSET and RISET values as expected.
  - NTC position.
  - Inspect the solder joints of the 4 power MOSFETs and the inductor.
      - Derate: change RISET to 12.4-15 kΩ (2.5-3 A).
      - Burn-in: charge for 2 h at 3 A from a 65 W PD charger, with thermocouples on the MOSFETs and inductor. Pass when they stay under 75 °C at 25 °C ambient, inside the closed case.
      - Mounting:
  - Thermal pad to an aluminium plate or the case wall.
  - At least 10 mm from the cells, with a Kapton or FR4 barrier.
  - In the fan airflow.
      - Protection:
  - A 10 A fuse in the battery lead.
  - A 5 A fuse or polyfuse on the VBUS side.
  - A KSD9700 70 °C normally-open bimetal switch glued to the hottest MOSFET, wired in parallel with the CHG_INHIBIT MOSFET, so overheating stops charging.
      - Keep a spare board, plus a Plan B charger (ISDT 608PD) that works through the XT30 and balance lead.
    - **How to verify:** Each board must pass:
  - The 2 h burn-in.
  - 20 plug/unplug cycles at each of 5, 9, 15 and 20 V.
  - Reverse PD output into a phone.
  - The NTC hot and cold tests from the next fix.
  
  Log temperatures, and fit only boards that pass.
    - **Confidence:** medium
    - **Sources:**
      - https://mysku.club/blog/aliexpress/100034.html
      - https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308290920_INJOINIC-IP2368-BZ-VGLIP_C5203723.pdf
      - https://oscarliang.com/isdt-608pd-charger/
      - https://darwinfpv.com/products/isdt-608pd-lipo-charger-dc-240w-10a-usb-c-140w-5a-smart-digital-charger
  7.
    - **Problem:** IP2368 boards ship with a fixed 10 kΩ resistor in place of the NTC, so there is no cold-charge inhibit.
    - **Proposed fix:** Fit a real 10 kΩ, B = 3380 NTC on the cells. The datasheet's thresholds are built around exactly this part (it shows a 10 kΩ @ 25 °C, B = 3380 NTC in its BOM).
  
  How the NTC pin works:
  - The pin sources 80 µA or 20 µA.
  - Too hot: below 0.39 V at 80 µA, i.e. R < 4.88 kΩ, about 45 °C. Charging stops.
  - Too cold: above 0.55 V at 20 µA, i.e. R > 27.5 kΩ, about 0 °C (a B3380 NTC reads 28.2 kΩ at 0 °C). Charging stops.
  - The reviewer measured that discharge stops at about 0.23 V, roughly 60 °C.
  - The datasheet says to put a 10 kΩ resistor there only when no NTC is wanted.
  
  For winter use, warm the pack before charging.
    - **Steps:**
      - Remove R6 (10 kΩ). Keep the 100 nF capacitor at the chip pin, as the datasheet requires.
      - Fit a 10 kΩ B3380 NTC: an epoxy bead (MF52-type) or Murata NCP18XH103F03RB. A B3435 type shifts the thresholds by only about 1 °C.
  - Use a twisted pair of 10-20 cm.
  - Bond it to the middle cell with Kapton tape or thermal epoxy, under the pack's thermal wrap.
      - Prefer a BMS that has its own NTC cut-off as a second layer.
      - Cold practice:
  - Insulate the pack (foam liner in the case).
  - Run the receiver for 15-20 minutes before plugging in a charger, so its ~10-20 W of heat warms the pack.
  - Never charge a pack that has been sitting below 0 °C.
    - **How to verify:** - Cold: put the pack at −5 °C for 1 h, then plug in the charger. The INA228 shows no charge current. Charging resumes after the pack warms above about 2-3 °C.
  - Hot: heat the pack to about 47 °C (hair dryer). Charging stops.
  - Check the NTC pin voltage: about 0.8 V at 80 µA at 25 °C.
    - **Confidence:** high
    - **Sources:**
      - https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308290920_INJOINIC-IP2368-BZ-VGLIP_C5203723.pdf
      - https://mysku.club/blog/aliexpress/100034.html
      - https://done.land/components/power/powersupplies/battery/chargers/charge-discharge/ip2366/
  8.
    - **Problem:** There are no RF-noise measurements of the IP23xx charger, LTC3780 or Pololu converters next to the SDR inputs (137 MHz to 2.2 GHz).
    - **Proposed fix:** Measure it yourself with an A/B procedure, and build in a charge-inhibit line.
  
  Known noise sources:
  - IP2368: 250 kHz buck-boost. It switches only while charging or running its reverse output.
  - Q6A on-board: the SY81012 at about 1 MHz, and the SY7120 at about 1.04 MHz. The SY7120's MODE pin is pulled low through R167 (100 kΩ), so it runs PFM at light load.
  - The external 12 V buck.
  - The display's backlight driver.
  
  Inhibit trick (undocumented by Injoinic, so bench-verify it):
  - Pull the IP2368 NTC pin down through a GPIO-driven MOSFET and 2.2 kΩ. With the NTC in parallel, the total is under 2.9 kΩ, which the chip reads as above 60 °C.
  - Its converter should then stop: charging stops, and so does the reverse output.
  - The same line serves the software termination in the IP2368 load-on-battery fix above.
    - **Steps:**
      - Wire CHG_INHIBIT: a free 40-pin GPIO → 1 kΩ → 2N7002 gate (100 kΩ pull-down). The drain connects through 2.2 kΩ to the IP2368 NTC pin; the source goes to GND.
  - Wrap recordings: `gpioset` (libgpiod v2, with -z) to assert, then run SatDump or SDR++, then release.
      - Converter hygiene:
  - Shielded-inductor converters, using forced-PWM where the part allows it (for example the LTC3780 FCB pin).
  - An output pi-filter: high-current ferrite bead + 10-22 µF ceramic + 100 µF electrolytic, and the same on the input.
  - Mix-31 clip ferrites or common-mode chokes on the DC leads. A libre.space test saw nearly 20 dB less noise at 144 MHz with ferrites on cables.
  - Tin-plate or copper-tape shield box, with converters at least 5-10 cm from the LNAs and SMA pigtails.
      - Feed the LNAs from an LT3045-class LDO behind an LC filter. Never feed them from a switcher directly.
      - Baseline: SDR input terminated in 50 Ω, device on battery, charger unplugged.
  - `rtl_power -f 136M:138.5M:2k -g 40 -i 10 -e 2m base.csv`
  - Repeat for 144-147 MHz and 434-439 MHz.
  - For 1.69-1.71 GHz and 2.20-2.29 GHz, use soapy_power with the Lime.
      - Repeat the sweeps with each source switched on in turn:
  - Charger charging at 2-3 A.
  - Charger plugged in with inhibit asserted.
  - LNB feed on.
  - Display at 100% vs 20%.
  - 12 V buck at light vs heavy load.
  
  Then repeat with the real antennas connected.
      - Optional, only if PFM spurs from the Q6A's own 5 V boost are found: remove R167 so MODE floats, which the SY7120 datasheet says gives PWM. This costs some light-load efficiency.
    - **How to verify:** Pass criteria for each condition against the baseline:
  - Median noise floor rises by 0.5 dB or less.
  - No new spurs more than 3 dB above the floor within ±1 MHz of 137.1/137.9, 145.8, 435-438, 1698-1707 and 2200-2290 MHz.
  - With inhibit asserted, the charger condition must match the baseline.
    - **Confidence:** medium
    - **Sources:**
      - https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308290920_INJOINIC-IP2368-BZ-VGLIP_C5203723.pdf
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/1912111437_Silergy-Corp-SY7120RAC_C207631.pdf
      - https://community.libre.space/t/rf-shileding-and-interference-from-steppers/235
      - https://www.rtl-sdr.com/tip-effect-of-power-sources-on-the-ham-it-up-upconverter/
  9.
    - **Problem:** Bullseye LNB current draw is not published.
    - **Proposed fix:** Size the feed from comparable universal single LNBs, then measure the actual unit. This applies only if an LNB is kept for the non-dish QO-100 antenna.
  
  Comparable datasheet figures at 11.5-14 V (vertical):
  - ALPS BSTE8: 80 mA typical.
  - Inverto SNL410: 95 mA.
  - Kathrein KEL 411: 165 mA typical.
  - Norsat PLL LNBFs: 120-150 mA maximum.
  
  The Bullseye adds a TCXO. Budget 200 mA (2.4 W) and design for 300 mA.
    - **Steps:**
      - Feed from the 12 V rail (11.5-14 V selects vertical, which is correct for the QO-100 NB downlink).
  - Switch: AO3401 P-MOSFET driven by a 2N7002 from a GPIO (gate network 10 kΩ/100 kΩ).
  - Protection: a 0.3 A-hold polyfuse, or a TPS2595-class eFuse.
  - Then an RF choke (10-22 µH, self-resonance above 1 GHz, or a ready bias-tee) and a DC-block capacitor toward the SDR.
      - Measure with a DMM in series:
  - Inrush and steady current at 11.5, 12.0 and 13.0 V.
  - Steady current at 20 °C and at about 0 °C.
      - Turn the LNB off when not doing QO-100; it saves 1-3 W.
    - **How to verify:** - Steady current under 250 mA, and the polyfuse never trips at a cold start.
  - The voltage at the LNB F-connector stays between 11.5 and 14 V across the pack's discharge range.
  - The QO-100 beacon is visible at the expected IF (~739-740 MHz with a 9750 MHz LO).
    - **Confidence:** medium
    - **Sources:**
      - https://www.rtl-sdr.com/?p=44655
      - https://zajadacz.de/app/documents/Datenblaetter_KAWE_S20110027_TDatenblatt_M_C21542.pdf
      - https://www.alltrade.co.uk/public/product/5445-sp-idlp-snl410-premu-opnenv031018-pdf.pdf
      - https://www.norsat.com/products/custom-lnb-100098
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines/
  10.
    - **Problem:** The power draw of a 1000+ nit sunlight-readable HDMI panel has not been measured.
    - **Proposed fix:** Re-budget the display using vendor figures, then measure it.
  
  Vendor figures (ratings, not measurements):
  - Litemax 7" 1600-nit (12 V; HDMI on one variant): 5.5 or 8.9 W depending on model.
  - Litemax 10.1" 1920x1200, 1000-nit: 6.5-8.5 W.
  - FeelWorld LUT7 (7", 1920x1200, 2200 nits, 7-24 V DC input): rated about 16-20 W.
  
  Impact: at full brightness the display can be the single largest load, 8-20 W. A typical LimeSDR session may then be 25-35 W instead of 20-23 W, so 72 Wh lasts about 1.8-2.6 h.
  
  Double-duty: a field-monitor-style panel with 7-24 V input can run straight from the 4S pack or the 12 V rail, so no 5 V buck is needed.
    - **Steps:**
      - Measure the panel's current at 0, 25, 50 and 100% brightness, on white and black screens. On LCDs the draw is set by the backlight, not by the content.
      - Power:
  - Panels with 7-24 V input: feed from the 12 V rail through a 3 A fuse.
  - 5 V panels: a dedicated synchronous 5 V/4 A buck, with the same pi-filter and ferrites as the other converters.
      - Add automatic brightness with a VEML7700 or BH1750 ambient-light sensor on the I2C6 bus (alongside the INA228). Default to 40-60% in shade.
      - For long sessions, carry a second 4S1P pack with an XT30 connector. Each pack stays under the 100 Wh airline limit.
    - **How to verify:** - INA228 power logs per mode replace the estimates.
  - The runtime prediction on screen matches a real discharge test within 10%.
    - **Confidence:** medium
    - **Sources:**
      - https://litemax.com/product-detail/0708-T-durapixel-industrial-display
      - https://litemax.com/product-detail/1015-M-Ubipixel-industrial-display
      - https://www.parkcameras.com/shop/Feelworld-LUT7-7-Inch-Touch-Screen-Field-Monitor_B158653V
      - https://www.adorama.com/felut7.html
  11.
    - **Problem:** Linux support for the I2C fuel gauge on the Q6A (INA228 driver, 40-pin I2C overlays) is unverified.
    - **Proposed fix:** Verified from the Radxa apt repository (qcs6490-noble, Release dated 24 Sep 2026):
  - Kernel linux-image-7.0.11-7-qcom ships drivers/hwmon/ina238.ko, which supports the INA228 since Linux 6.17. It also ships ina2xx.ko and ina3221.ko.
  - radxa-overlays 0.2.31 includes qcs6490-radxa-dragon-q6a-i2c6.dtso (pin 3 SDA, pin 5 SCL, 100 kHz) and an i2c6-ssd1306 example. That example is the template for an INA228 overlay.
  
  A catch: the INA228's ENERGY register is unsigned, so it adds charge and discharge together. CHARGE (0x0A, 40-bit two's complement, in coulombs) is the right register for state of charge, but the hwmon driver exposes only energy1_input. So compute charge in userspace.
  
  The driver's default shunt is 2.5 mΩ, so the Adafruit board's 15 mΩ shunt must be set in device tree.
    - **Steps:**
      - Wire the INA228 to I2C6: pins 1 (3.3 V), 3 (SDA), 5 (SCL) and 9 (GND). Put the shunt in the battery lead, as in the IP2368 load-on-battery fix above.
      - Create the overlay `&i2c6 { qcom,enable-gsi-dma; status = "okay"; clock-frequency = <100000>; #address-cells = <1>; #size-cells = <0>; power-monitor@40 { compatible = "ti,ina228"; reg = <0x40>; shunt-resistor = <15000>; }; }; &spi6 { status = "disabled"; }; &uart6 { status = "disabled"; };`, compile it with `dtc -@`, install it through rsetup's overlay manager the same way radxa-overlays are, and reboot.
      - Check:
  - `i2cdetect -l` to find the bus, then `i2cdetect -y <bus>` shows 0x40.
  - `sudo modprobe ina238`.
  - `cat /sys/class/hwmon/hwmon*/name` shows ina228; read in1_input, curr1_input and power1_input.
      - Gauge daemon (Python, 1 Hz):
  - Integrate curr1_input to get state of charge.
  - Optionally read the coulomb counter directly: `i2ctransfer -f -y <bus> w1@0x40 0x0a r5@0x40`.
  - Reset to 100% at 16.35 V with |I| < 0.1 A, and to 0% at 13.2 V under load.
  - Log W per mode.
  - Drive CHG_INHIBIT and the low-battery poweroff.
      - Budget alternative: an INA226 module ($2-4; driver ina2xx).
  - Replace its R100 shunt (only ±0.82 A range) with an R010 2512 resistor (±8.2 A).
  - Then `echo ina226 0x40 | sudo tee /sys/bus/i2c/devices/i2c-<N>/new_device` and `echo 10000 | sudo tee .../shunt_resistor`.
      - Kernel note: 7.0.11 has reported HDMI and VPU regressions on the Q6A. If you stay on 6.18.2-x (also newer than 6.17), check with `modinfo ina238` that the module is present.
    - **How to verify:** - At 1.00 A from a lab load, the INA reading is within 1% of a reference DMM.
  - Over a full discharge, the counted capacity is within 3-5% of the cells' rating.
  - The value survives a reboot, and the overlay is listed as active.
    - **Confidence:** high
    - **Sources:**
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/main/Contents-arm64.gz
      - https://raw.githubusercontent.com/radxa-pkg/radxa-overlays/main/arch/arm64/boot/dts/qcom/overlays/qcs6490-radxa-dragon-q6a-i2c6.dtso
      - https://docs.kernel.org/hwmon/ina238.html
      - https://raw.githubusercontent.com/torvalds/linux/master/Documentation/devicetree/bindings/hwmon/ti,ina2xx.yaml
      - https://www.ti.com/lit/ds/symlink/ina228.pdf
      - https://www.adafruit.com/product/5832
      - https://forum.radxa.com/t/31304
  12.
    - **Problem:** Charging from USB-C PD solar panels or other fluctuating sources through the IP23xx (no MPPT) is undocumented: renegotiation and dropouts under clouds.
    - **Proposed fix:** What the IP2368 does have (datasheet):
  - An input-voltage control loop that cuts charge current to what the source can actually deliver.
  - It caps input power at the PD-advertised power.
  - It does not do MPPT.
  
  Options, in order of preference:
  1. Buffer the solar energy: panel → a power station or power bank with MPPT → USB-C PD → device. This is the most robust option and needs no hardware change.
  2. A direct PD panel, with a 'SOLAR' setting that limits the IP2368 to about 60-70% of the panel's rating, so the panel stays near its maximum-power point instead of collapsing and renegotiating.
  3. For real MPPT and a true power path, replace the IP2368 with a BQ25798 (1-4S buck-boost, 3.6-24 V input, VOC-sampling MPPT, NVDC path). The open-hardware Marek128b V2.1 board (BSD-2) is DIY assembly.
    - **Steps:**
      - Build the 'SOLAR' setting.
  - Use the IP2368's input-power mode (leave ISET_MODE floating). In this mode P = 4 W per kΩ of RISET, per the datasheet example: 15 kΩ = 60 W.
  - An SPDT switch selects RISET 5.1 kΩ (about 20 W) for SOLAR or 10 kΩ (40 W) for MAINS.
  - Only change it with USB-C unplugged, because ISET may be read only at start-up.
      - Mark the 'SOLAR' position on the case. Note that in input-power mode the battery current varies with pack voltage.
      - Field test, 2 h with passing clouds:
  - Log INA228 net battery current at 1 Hz.
  - Count on/off transitions (renegotiation cycles).
  - Compare the Wh harvested with the panel → power-bank → device path.
    - **How to verify:** In SOLAR mode, under partial cloud, there are fewer than 1 charge dropout per 10 minutes and the harvested energy is within 20% of the buffered path. If not, use the buffered path or the BQ25798.
    - **Confidence:** low
    - **Sources:**
      - https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2308290920_INJOINIC-IP2368-BZ-VGLIP_C5203723.pdf
      - https://mysku.club/blog/aliexpress/100034.html
      - https://www.ti.com/product/BQ25798
      - https://github.com/Marek128b/BQ25798-mppt-solar-charger
- **Residual risks:**
  - The real Q6A power draw (idle, NPU, Q6A plus Lime) is still unmeasured. All runtime numbers are estimates until the INA228 logs exist.
  - The schematic analysis applies to v1.21 boards. Other PCB revisions may differ, so check the revision silkscreen.
  - The UEFI power-key policy (the ≥400 ms requirement) may change with firmware updates. The external 1.5 s press covers both cases.
  - The NTC-pull charge-inhibit trick is not documented by Injoinic. Bench-verify that the converter really stops; the reverse PD output and the board LEDs also show a fault while it is asserted.
  - How the IP2368's 48 h charge timer interacts with inhibit toggles is unknown. Long blackout sessions may need a cable replug every 2 days.
  - Most cheap BMS boards rarely balance at 4.10-4.15 V/cell, so monthly 4.20 V balance charges or an active balancer are needed.
  - AliExpress IP2368, BMS and cell prices and listings were not verified. Counterfeit or relabelled 21700 cells are common, so test capacity and internal resistance.
  - The Pololu D36V50F12 has an ultrasonic power-save mode at light load. Its variable switching frequency could produce wandering spurs; check this in the A/B noise test.
  - A 2000-nit field-monitor display rated 16-20 W could halve runtime. Brightness control is the biggest runtime lever.
  - The J21 header's current rating is not published. The 3S-direct option pushes about 2.8 A at 25 W.
  - Radxa kernel 7.0.11 has reported HDMI and VPU regressions on the Q6A. The overlay must be re-checked after each kernel or radxa-overlays update.
  - The LimeSDR Micro M.2 price and schedule may still change (latest found: $249, new orders shipping Dec 15, 2026), which delays real power measurements.
  - Optional board mods (C325 capacitor, removing R167) are fine-pitch rework and may void the warranty.

## Адверсаріальна перевірка (`verify`)

_Агент цього етапу ще працює (run `wf_f924b2ab-5ad`)._

