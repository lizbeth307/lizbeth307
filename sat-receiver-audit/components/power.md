# Power: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_d9388111-e66`_

- **Subsystem:** power
- **Findings:**
  1.
    - **Claim in stack:** Cells: Molicel INR21700-P50B, 5.0 Ah, 18 Wh, 60 A continuous; 4S1P = 72 Wh nominal
    - **Finding:** The Molicel product data sheet V1.1 gives 5000 mAh typical (4850 min), 18.0 Wh (17.5 min), 3.6 V nominal, 4.2 V charge, 2.5 V cutoff, 5 A standard / 25 A max charge, 60 A continuous (80 C cutoff), DC impedance 12.8 mOhm at 50% SOC, AC 6.5 mOhm at 30% SOC, and charge ambient -20 to 60 C. The molicel.com page lists 1,400 cycles. The STACK 0-45 C charge window is more conservative than the cell allows and matches the IP2368 NTC thresholds.
    - **Verdict:** confirmed
    - **Action:** Keep. Use 4.85 Ah (minimum) and about 7-13 mOhm (1 kHz AC / DC) as the goods-in limits.
    - **Impact:** Battery choice holds.
    - **Sources:**
      - https://www.fsaeonline.com/content/Molicel-TDS--INR-21700-P50B-80122.pdf
      - https://www.molicel.com/inr-21700-p50b/
  2.
    - **Claim in stack:** P50B weight about 68 g; goods-in check 68-70 g
    - **Finding:** The official data sheet gives 71 g maximum. A 68-70 g window could reject genuine cells in the 70-71 g range. The pack is up to 284 g of cells, not 272 g.
    - **Verdict:** corrected
    - **Action:** Change the goods-in window to 68-71 g and the pack mass model to 4 x 71 g max.
    - **Impact:** Small: weight budget plus about 12 g, fewer false rejects.
    - **Sources:**
      - https://www.fsaeonline.com/content/Molicel-TDS--INR-21700-P50B-80122.pdf
  3.
    - **Claim in stack:** P50B $9.99 each at 18650 Battery Store (verified); NKON $7.59 (unverified)
    - **Finding:** On 18 Oct 2026 the 18650 Battery Store Shopify catalogue shows 'Molicel 21700 P50B 5000mAh 60A Battery' at $9.99, available. IMR Batteries also lists it at $9.99, available. NKON returned HTTP 403, so the NKON price is still unverified.
    - **Verdict:** confirmed
    - **Action:** Keep $49.95 for 5 cells. Leave NKON marked unverified.
    - **Impact:** No cost change.
    - **Sources:**
      - https://www.18650batterystore.com/products/molicel-21700-p50b-5000mah-50a-battery
      - https://imrbatteries.com/products/molicel-21700-p50b-5000mah-60a-battery
  4.
    - **Claim in stack:** 4S1P P50B is the right cell for the 72 Wh pack (power cell, 60 A)
    - **Finding:** The worst-case pack current is about 4.6 A, which is 0.9C. The 60 A power rating is unused. Molicel now also lists INR-21700-M65A: 6.5 Ah, 23.4 Wh, 26 A continuous, 322 Wh/kg, implied mass about 73 g. A 4S1P M65A pack would be 93.6 Wh nominal, still under 100 Wh, and runs about 26% longer on the same model (mode B 4.2 h warm instead of 3.3 h). M65A is $11.99 and SOLD OUT at IMR Batteries and 18650battery.com. NKON's €9.75 comes from a search snippet; its stock is unverified. The cold (0 C) performance of the high-energy cell is not published on the page.
    - **Verdict:** new_option
    - **Action:** Keep P50B as the baseline. List M65A as an upgrade only after the full Molicel data sheet (charge temperature range, cold discharge curve) and in-stock retail are confirmed. Re-run the cold-runtime model with M65A cold data before switching.
    - **Impact:** About +21 Wh and about +20-30% runtime for about +$10 and about +8-12 g, if the cells are available.
    - **Sources:**
      - https://www.molicel.com/inr-21700-m65a/
      - https://imrbatteries.com/products/molicel-m65a-21700-6500mah-26a-battery
      - https://www.nkon.nl/en/molicel-inr21700-m65a-6500mah-26a.html
  5.
    - **Claim in stack:** Budget cell alternative: other 5 Ah cells (stage-5 analog search)
    - **Finding:** 18650 Battery Store lists Samsung INR21700-58E at $4.99, in stock. The listing gives 5330 mAh min (0.2C), 5170 mAh min (1C), 3.64 V nominal, 10.7 A continuous (2C), 0.5C (2.67 A) standard charge, 1C max charge, and 74 g max. All of these come from the retailer page; the Samsung SDI spec CC5493F101 was not fetched. The 3 A charge setting is slightly above the 0.5C standard. Cold performance is not given.
    - **Verdict:** new_option
    - **Action:** Pass to the stage-5 cheaper-analog run as a candidate (half price, about +7% Wh). Requires the Samsung spec sheet and a cold-discharge bench test. If adopted, set RISET to 2.5 A (12.5k).
    - **Impact:** Could save about $25 for 5 cells. Unverified at the manufacturer level.
    - **Sources:**
      - https://www.18650batterystore.com/products/samsung-58e-21700-battery
  6.
    - **Claim in stack:** BMS: Daly 4S 15 A common-port with balancing, $9.00 at TinyTronics (unverified); BMS cutoff 2.5-2.8 V/cell
    - **Finding:** TinyTronics lists €8.00 incl. VAT (€6.61 ex), 'only 9 pieces in stock'. Specs: Li-ion/LiPo, common port, 15 A continuous, discharge OCP 40±10 A, charge OCP 10±2 A, OVP 4.25±0.05 V (release 4.15), UVP 2.70±0.05 V (release 3.0 V). Balancing is passive, 30±10 mA, and starts only at 4.18 V. Self-consumption and the wake-up requirement are NOT published.
    - **Verdict:** corrected
    - **Action:** Price confirmed (about $9 at an assumed 1.16 USD/EUR). Correct the cutoff row to UVP 2.65-2.75 V, release 3.0 V. The 4.10 V daily charge never reaches the 4.18 V balance start, so the monthly ISDT balance is mandatory (already in STACK). Some units can hit OVP at 4.20 V, which only ends a monthly 4.20 V charge early and is harmless. Measure BMS quiescent current on the bench and keep the wake test 3/3.
    - **Impact:** Confirms the monthly-balance design. Stock is thin (9 pcs).
    - **Sources:**
      - https://www.tinytronics.nl/en/power/bms-and-chargers/bms/daly-bms-li-ion-li-po-protection-circuit-4s-15a-with-balancing
  7.
    - **Claim in stack:** IP2368 datasheet V1.41: 2-5 cells, up to 100 W, 250 kHz, timer 45-51 h, standby 180 uA; RVSET 5.1k = 4.10 V/cell; RISET 15k = 3 A; NTC 10k B3380
    - **Finding:** Read directly from the IP2368 V1.41 data sheet (Nov 2023; the revision note says 6S is no longer supported):
  - VTRGT = 4000 + 0.02*RVSET mV, so 5.1k gives 4.102 V/cell. The settable Li-ion range is 4.1-4.4 V/cell, 10 mV step, 1% resistor; about ±40 mV/cell tolerance at 7.5k.
  - With ISET_MODE to GND, ICHRG = 0.2*RISET mA, so 15k gives 3 A (5 A max).
  - 250 kHz charge and discharge switching. TEND 45/48/51 h. ISTB 180 uA at VBAT 14.8 V.
  - NTC: 80 uA / 0.39 V means above 45 C; 20 uA / 0.55 V means below 0 C. The BOM NTC is 10k@25 C, B=3380 (my calculation: 4.90 k at 45 C, 28.2 k at 0 C).
  - Abs max VBAT/VBUS 30 V; VBUS operating 4.5-25 V; θJA 30 C/W.
    - **Verdict:** confirmed
    - **Action:** Keep the settings. Note that the 500 kHz second harmonic of the 250 kHz switcher sits between NAVTEX 490 and 518 kHz, which justifies 'no charging in HF/LF Quiet'.
    - **Impact:** Charger parameters hold.
    - **Sources:**
      - https://datasheet.lcsc.com/datasheet/pdf/752f0c4a0b5b0a79a7f68752c4eac200.pdf?productCode=C5203723
      - https://www.lcsc.com/product-detail/C5203723.html
  8.
    - **Claim in stack:** IP2368 'BZ' charge-only board version, 2 boards $25-49 from a marketplace
    - **Finding:** The data sheet defines IP2368_BZ as the standard part (2-5S charging). IP2368_COUT adds USB-C discharge output (DRP Try.SRC); _NACT and _I2C variants also exist. Retail boards found (Walmart about $12.50-12.98, Newegg Business $15.79, Newegg $18.99, Newegg.ca $23.98) are all sold as BIDIRECTIONAL 100 W boards. Sellers warn that the bidirectional C port may only be connected to one-way chargers or devices, and that connecting another bidirectional port causes role flapping. No listing sold as charge-only was found. The IP2368_BZ_VGLIP chip (LCSC C5203723) shows 'Not available now'. The Anker 737 named in STACK as the bench source is itself a bidirectional USB-C power bank.
    - **Verdict:** new_risk
    - **Action:** Assume the bought board is a COUT variant until proven otherwise. Goods-in test: with the board on battery, attach a USB-C sink (FNB58 plus load); any VBUS means COUT. Mitigations, choose one:
  - A reverse-blocking eFuse (e.g. TI TPS25947: 2.7-23 V, 28 V abs max, true reverse blocking) between the enclosure USB-C VBUS and the board. This is a model; bench-verify that PD still negotiates.
  - Source an IP2368_BZ chip from an Injoinic distributor for the custom power PCB.
  - Charge only from one-way PD adapters, never from bidirectional power banks.
    - **Impact:** Without mitigation, a power bank or phone on the port could drain the pack, or charging could flap. Price is roughly confirmed ($25-48 for 2).
    - **Sources:**
      - https://datasheet.lcsc.com/datasheet/pdf/752f0c4a0b5b0a79a7f68752c4eac200.pdf?productCode=C5203723
      - https://www.lcsc.com/product-detail/C5203723.html
      - https://www.neweggbusiness.com/p/9B-27U-00HC-00022
      - https://www.newegg.com/p/3C6-00RD-001C4
      - https://www.walmart.com/ip/5614775489
      - https://www.onbuy.com/ro/p/ip2368-bidirectional-100w-fast-charging-module-buck-boost-type-c-interface-4s-lithium-battery-high-power-charging-board~p252223345/
      - https://www.ti.com/product/TPS25947
  9.
    - **Claim in stack:** For 45 W PD sources use input-power-limit mode (RISET value to verify on bench)
    - **Finding:** The data sheet says the standard IP2368 automatically lowers charge current so that input power stays at or below the PD power the adapter advertises. Its worked example is a 30 W adapter with RISET 15k. Only the IP2368_NA custom variant ignores adapter capability. With non-PD 5 V input, input current is capped at 3 A.
    - **Verdict:** corrected
    - **Action:** Drop the separate 45 W RISET mode. Keep ISET_MODE to GND, RISET 15k. A 45 W source simply charges slower above about 14-15 V pack voltage. Still qualify each source with the FNB58.
    - **Impact:** Simpler configuration; one resistor value.
    - **Sources:**
      - https://datasheet.lcsc.com/datasheet/pdf/752f0c4a0b5b0a79a7f68752c4eac200.pdf?productCode=C5203723
  10.
    - **Claim in stack:** SYS12: Pololu D36V50F12, 12 V ±4%, about 500 kHz under load, power-save at light load, $39.95, 'Rationed'; drop-out below about 13.3 V battery
    - **Finding:** Pololu #4095: 12 V ±4%; 4.5 A typical at 36 V in (2.3-6.5 A typical continuous range); input 13.3-50 V; about 500 kHz under heavy load; power-save mode at light load stays above 20 kHz; EN sleep below 1.2 V, wake above 1.35 V; PG open-drain (+20% / -10%); Iq 2-4 mA; sleep current 10-20 uA per volt, 'mostly from the EN pull-up'; $39.95 (1), $36.75 (5+); 'Rationed (Active and Preferred)'. No numeric dropout is given; it rises with load (curves only).
    - **Verdict:** confirmed
    - **Action:** Keep with the existing A/B gates. Because EN has an internal pull-up, a divider of about 0.10 will not give exactly 12.0/13.5 V. Calibrate the backup-EN divider on the bench.
    - **Impact:** Price, stock and specs unchanged. The about 500 kHz fundamental sits 10-18 kHz from NAVTEX 490/518 kHz and moves with load, so the C4 gate is essential.
    - **Sources:**
      - https://www.pololu.com/product/4095
  11.
    - **Claim in stack:** C4 fallback: synchronous buck with forced PWM at a fixed frequency via RT/SYNC, part to be chosen in P5
    - **Finding:** Verified candidate: TI LM61460 (ACTIVE, Rev D 2022). Specs:
  - 3.0-36 V input (42 V transient), 6 A, RT-set 200 kHz-2.2 MHz.
  - An external clock on EN/SYNC forces FPWM and disables PFM ('all parts operate in FPWM mode when synchronizing'); the only orderable part, LM61460AANRJRR, is auto-mode without spread spectrum, so the sync input is how FPWM is reached.
  - 0.4 V typical dropout at 4 A; adjustable SW rise time; HotRod package.
  - LM61460EVM exists (5 V / 400 kHz, needs rework for 12 V).
  Price and stock not checked.
    - **Verdict:** new_option
    - **Action:** Name LM61460 (synced from a clean clock chosen by the harmonic scan, e.g. 1.8-2.1 MHz) as the P5 fallback for SYS12 on the custom power PCB. Verify price and stock in P5.
    - **Impact:** Gives a concrete fixed-frequency path if the Pololu fails the NAVTEX/LF A/B test. Lower dropout than the Pololu module.
    - **Sources:**
      - https://www.ti.com/product/LM61460
      - https://www.ti.com/lit/ds/symlink/lm61460.pdf
  12.
    - **Claim in stack:** LAB5: Pololu D36V28F5, 3.2 A, $23.95
    - **Finding:** Pololu #3782: 5 V ±4%; 3.2 A typical at 36 V in (2.5-4 A typical continuous); input 5.3-50 V; about 500 kHz; power-save mode above 20 kHz; same EN thresholds; Iq 2-3 mA; $23.95 (1), $22.03 (5+); Rationed (Active and Preferred). D36V50F5 (#4091, 5.5 A, $39.95) exists for the Lime case.
    - **Verdict:** confirmed
    - **Action:** Keep. Set the D14 'D36V50F5 price unverified' note to $39.95 (verified).
    - **Impact:** None.
    - **Sources:**
      - https://www.pololu.com/product/3782
      - https://www.pololu.com/product/4091
  13.
    - **Claim in stack:** Main switch: Pololu #2813 HP, 4.5-40 V, 6 A at 55 C, <0.2 uA off, A-to-GND on-only, OFF pulse from Pico, $8.95
    - **Finding:** Pololu #2813 'Big Pushbutton Power Switch with Reverse Voltage Protection, HP':
  - 4.5-40 V in the intro, but the spec table gives 4.5-32 V recommended and 40 V absolute maximum.
  - About 6 A at 55 C; off current <0.2 uA; A-to-GND gives on-only; OFF pin high pulse (>1 V) turns it off; CTRL pin.
  - $8.95 (1), $8.23 (5+); Rationed.
  - Pololu warns against using it as an emergency cutoff or safety disconnect, and says it 'does not isolate the load when off'.
    - **Verdict:** confirmed
    - **Action:** Keep. Use 32 V as the design limit; the SMBJ17A clamp of 27.6 V stays below it. The BMS and the 7.5 A fuse remain the safety disconnects; the supervisor-held OFF is only an energy cutoff. Keep the bench test of a held OFF against a button press on A.
    - **Impact:** No change. The safety wording in STACK should not call the #2813 a protective cutoff.
    - **Sources:**
      - https://www.pololu.com/product/2813
  14.
    - **Claim in stack:** Gauge: Adafruit INA228 #5832, 15 mOhm shunt, ADCRANGE 0 = ±10.9 A, $14.95; AON budget about 0.7 mA
    - **Finding:** Adafruit #5832: $14.95, in stock; 15 mOhm 0.1% shunt; up to 10 A in high-current mode, 2.75 A in low-current mode; 85 V common mode; 10k I2C pull-ups; default address 0x40; ALRT active-low; VBUS jumper open by default. TI INA228 (ACTIVE, data sheet Rev A May 2022): 2.7-5.5 V supply; 640 uA typical, 1.1 mA max; 5 uA max shutdown; ±163.84 / ±40.96 mV ranges (15 mOhm gives 10.92 / 2.73 A); energy and charge accumulators.
    - **Verdict:** confirmed
    - **Action:** Keep. For high-side use, close the VBUS jumper. Budget AON at 0.7 mA typical but 1.2 mA worst case.
    - **Impact:** None.
    - **Sources:**
      - https://www.adafruit.com/product/5832
      - https://learn.adafruit.com/adafruit-ina228-i2c-power-monitor/pinouts
      - https://www.ti.com/product/INA228
  15.
    - **Claim in stack:** INA228 board prep: remove pull-ups; OFF draw about 13-14 mW, about 170-185 days
    - **Finding:** The Adafruit board also has a green 'on' power LED, and the guide shows no jumper to disable it. On a linear AON LDO fed from about 15.5 V, every 1 mA of LED current costs about 15 mW. That alone could halve standby time; the LED current is unverified. The 170-185 days figure assumes 58 Wh from full. The STACK storage rule (about 50% SoC) leaves about 36 Wh, so about 110 days at 13.5 mW (model). After that the AON load keeps draining toward BMS UVP (2.70 V/cell).
    - **Verdict:** new_risk
    - **Action:** Remove the board's power LED (or its resistor) as well as the pull-ups. On poweroff when SoC is below about 30%, have labpowerd put the INA228 into shutdown mode (5 uA max), accepting that charge while off is not counted, or let the supervisor cut the AON load below about 13.0 V. Restate standby as 'about 110 days from 50% storage' (model).
    - **Impact:** Prevents a silently over-discharged pack after months in storage.
    - **Sources:**
      - https://learn.adafruit.com/adafruit-ina228-i2c-power-monitor/pinouts
      - https://www.ti.com/product/INA228
  16.
    - **Claim in stack:** INA228 read via i2c-dev in user space, no DT binding; 'bound ina238 driver blocks CHARGE register access'
    - **Finding:** Mainline Linux has supported INA228 in the ina238 hwmon driver since v6.17 (merged 2025). The current kernel docs list INA228, INA237, INA238, INA700, INA780 and SQ52206. The driver exposes energy1_input but no charge attribute. The user-space decision is still correct, and on any kernel 6.17 or newer a DT node would now bind the driver.
    - **Verdict:** confirmed
    - **Action:** Keep i2c-dev. Add 'blacklist ina238' (or make sure no ti,ina228 DT node exists) to the image, and check i2cdetect shows 0x40 not as UU.
    - **Impact:** Prevents a silent driver grab on newer Radxa kernels.
    - **Sources:**
      - https://docs.kernel.org/hwmon/ina238.html
      - https://code.amethyst.name/public-mirrors/linux/src/branch/master/drivers/hwmon/ina238.c
  17.
    - **Claim in stack:** LNB and Boni LDO: TI TPS7A4701, 3-36 V, 1 A, 307 mV dropout, θJA 30.5 C/W; 0.96 W at 0.3 A / 1.44 W at 0.45 A
    - **Finding:** TI page and data sheet Rev G (May 2026): ACTIVE; IN 3-35 V operating, 36 V abs max; ANY-OUT 1.4-20.5 V (adjustable to 34 V); 1 A; dropout 216 mV at 0.5 A and 307 typ / 450 max mV at 1 A; current limit 1.0 min / 1.26 typ A; 4 uVrms; θJA 30.5 C/W (RGW VQFN-20). 13.2 V and 12.5 V can both be set with ANY-OUT pins (0.1 V steps). Dissipation recomputed: 0.96 W / +29 K and 1.44 W / +44 K (model).
    - **Verdict:** confirmed
    - **Action:** Keep the electrical choice.
    - **Impact:** None.
    - **Sources:**
      - https://www.ti.com/product/TPS7A47
      - https://www.ti.com/lit/ds/symlink/tps7a47.pdf
  18.
    - **Claim in stack:** TPS7A4701 'PG on MCP #3' for LNB13V2 and BONI12V5
    - **Finding:** The TPS7A47 pin table (Rev G) has OUT, NC, SENSE, the ANY-OUT pins (0P1V-6P4V2), GND, EN, NR, IN and NC. There is NO power-good pin. The schematic cannot wire PG to the MCP23017.
    - **Verdict:** corrected
    - **Action:** Replace the 'PG' line with an external monitor. Options: a TPS3762 or TLV6700-class comparator on each output, or read the rail through a divider into a spare ADC (Pico) or a comparator into MCP #3.
    - **Impact:** A schematic error that would otherwise be found only at layout.
    - **Sources:**
      - https://www.ti.com/lit/ds/symlink/tps7a47.pdf
  19.
    - **Claim in stack:** Acceptance: LNB 13.2 V ±0.2 V at the F connector; Boni 12.5 V ±0.25 V
    - **Finding:** Overall TPS7A47 accuracy is ±2.5% over line, load and temperature (±1% at 25 C only), valid when VIN ≥ VO + 1 V. That is ±0.33 V at 13.2 V and ±0.31 V at 12.5 V, before the drop across the PTC, LC and choke. Near the 13.2-13.8 V battery region the LDO is close to dropout.
    - **Verdict:** corrected
    - **Action:** Widen acceptance to 13.2 V ±0.35 V (still inside the Bullseye 11.5-14 V V-pol window) and 12.5 V ±0.35 V, or trim in adjustable mode with 0.1% resistors. Test at a battery voltage of at least 14.2 V.
    - **Impact:** Avoids false acceptance failures; no functional change.
    - **Sources:**
      - https://www.ti.com/lit/ds/symlink/tps7a47.pdf
  20.
    - **Claim in stack:** TPS7A4701 x2 at LCSC, $10-20 total (price unverified)
    - **Finding:** On 18 Oct 2026 LCSC C90084 (TPS7A4701RGWR) is 'Out of Stock' at $13.29 (1+), so two cost about $26.6. The TI store shows RGWR and RGWT out of stock. DigiKey regional pages show backorder with a 12-week lead time (aggregator snapshot; Mouser stock in snapshots is unverified). LCSC lists TPS7A4701MRGWREP (TI enhanced product, same function) at $11.01 with 110 in stock.
    - **Verdict:** new_risk
    - **Action:** Order early, the same as other long-lead items: try Mouser/DigiKey live, else buy 2x TPS7A4701MRGWREP from LCSC. Budget $22-27 for two. Keep a 36-40 V adjustable LDO as plan C (e.g. ADI LT3081/LT3080 class; not verified here).
    - **Impact:** Plus about $7-17 and a possible schedule risk on both the LNB and Boni rails.
    - **Sources:**
      - https://www.lcsc.com/product-detail/C90084.html
      - https://www.ti.com/product/TPS7A47/part-details/TPS7A4701RGWR
      - https://punchouttest.digikey.ca/en/products/detail/texas-instruments/TPS7A4701RGWR/4579595
  21.
    - **Claim in stack:** LNA rail: 2x ADI LT3045 in parallel at 4.5 V from LAB5, $8.33 each, LCSC (not ADI-franchised)
    - **Finding:** LCSC C666574 LT3045EDD#PBF: $8.63 (1+), 446 in stock, 20 V operating, 500 mA, 260 mV typical dropout, 10 uF minimum output capacitor. Headroom is tight: D36V28F5 5.0 V ±4% (4.8 V minimum) minus the LC drop leaves about 0.25-0.45 V above 4.5 V. That puts the LT3045 near dropout, where its PSRR against the about 500 kHz LAB5 ripple is reduced (PSRR at this headroom not verified; the ADI site returned 503).
    - **Verdict:** confirmed
    - **Action:** Price $17.26 for 2. On the bench, measure the 4.5 V ripple at 500 kHz with LAB5 at its low tolerance. If PSRR is poor, lower the rail to about 4.3-4.4 V if the LNAs allow it (check with the rf_frontend owner).
    - **Impact:** Small cost change; possible LNA-rail ripple issue.
    - **Sources:**
      - https://www.lcsc.com/product-detail/C666574.html
  22.
    - **Claim in stack:** TPS2553 x10: LNA channels 300 mA nominal (240 mA minimum), LAB port 0.75 A; TI store out of stock; check -1 latch variant
    - **Finding:** TI: ACTIVE; 2.5-6.5 V; adjustable limit about 75 mA-1.7 A; TPS2553-1 is the latch-off version; FAULT deglitch 5/7.5/10 ms; data sheet Rev F. The TI store shows TPS2553DBVR out of stock. LCSC C55266 has tens of thousands at about $0.30 (search snapshot), and TPS2553DBVR-1 is C111738.
  Data-sheet equations, with RILIM in kOhm (my calculation):
  - RILIM = 88.7k gives IOS min/nom/max about 265/300/341 mA.
  - RILIM = 34.8k gives 685/747/817 mA.
  TI also suggests the pin-compatible TPS25221 (0.275-2.7 A).
    - **Verdict:** confirmed
    - **Action:** Keep. Use 88.7k (1%) for the LNA channels; the minimum is about 265 mA, not 240. Use 34.8k for the LAB port (0.75 A nominal). Buy from LCSC.
    - **Impact:** About $3-5 for 10; no change.
    - **Sources:**
      - https://www.ti.com/product/TPS2553
      - https://www.ti.com/lit/ds/symlink/tps2553.pdf
      - https://www.ti.com/product/TPS2553/part-details/TPS2553DBVR
      - https://www.lcsc.com/product-image/C55266.html
      - https://fat.lcsc.com/product-image/C111738.html
  23.
    - **Claim in stack:** AON 3.3 V: TPS709-class LDO (30 V input, uA Iq; to verify)
    - **Finding:** TI TPS709: ACTIVE (Rev H 2021); 2.7-30 V; 150 mA; 1 uA typical Iq; 3.3 V fixed option available; WSON-6 or SOT-23-5. The page names TPS7E71 as a pin-compatible newer part (higher Iq, no reverse-current protection) and TPS7A19 (40 V). The SMBJ17A clamp of 27.6 V at Ipp stays below 30 V.
    - **Verdict:** confirmed
    - **Action:** Fix the part as TPS70933 (DBV). Keep TPS7A19 as the higher-margin option if the node-N transient margin worries the reviewer.
    - **Impact:** None.
    - **Sources:**
      - https://www.ti.com/product/TPS709
  24.
    - **Claim in stack:** Micropower UV supervisor 12.8 V trip / 13.6 V release (part to be chosen in P5)
    - **Finding:** TI TPS3762: ACTIVE (Rev A Dec 2023); 2.7-65 V supply; 4 uA Iq; 0.8 V SENSE threshold set by an external divider; 2/5/10% hysteresis options; latching option; open-drain active-low output; SOT-23-THN. It can sit directly on node N. The fixed percent hysteresis gives 13.44 V (5%) or 14.08 V (10%) release from 12.8 V, not exactly 13.6 V.
    - **Verdict:** new_option
    - **Action:** Use TPS3762 (5% version, release about 13.45 V) or add a resistor for extra hysteresis to land on 13.6 V. Power it from N, not from AON 3.3 V, so it works even if the AON LDO fails. Confirm the hysteresis definition in the data sheet.
    - **Impact:** Turns a 'model' line into a sourced part costing about 0.06 mW.
    - **Sources:**
      - https://www.ti.com/product/TPS3762
  25.
    - **Claim in stack:** TVS: SMBJ13A on J21 (VRWM 13 V, breakdown 14.4-15.9 V, below the Q6A's 16 V capacitors); SMBJ17A on node N
    - **Finding:** The Vishay SMBJ table confirms both: SMBJ13A VBR 14.4-15.9 V at 1 mA, VC 21.5 V at 27.9 A; SMBJ17A VBR 18.9-20.9 V, VC 27.6 V at 21.7 A. However, Diodes Inc's SMBJ13A listing gives VBR max 16.5 V (search snippet; primary page returned 403), so the 15.9 V bound depends on the vendor. Under any real surge the clamp (21.5 V) is above the SY81012's 16 V. If the D36V50F12 fails with its high side shorted, SMBJ13A crowbars at 16.4 V (model: about 5 A, about 80 W) until it fails or the 4 A fuse opens.
    - **Verdict:** corrected
    - **Action:** Specify the manufacturer: Vishay or Littelfuse SMBJ13A, not a generic part. For real J21 over-voltage protection, add an eFuse with adjustable OVLO set to about 13.5 V. TI TPS25947 (2.7-23 V, 5.5 A, adjustable ILIM 0.5-6 A, 1.2 us OVLO, true reverse blocking) also blocks back-feed from the Q6A side. Keep the TVS only for fast edges.
    - **Impact:** Closes a real fault mode (buck short putting 16.4 V on the Q6A). About +$1-3.
    - **Sources:**
      - https://www.vishay.com/docs/88392/smbj.pdf
      - https://www.diodes.com/part/view/SMBJ13A
      - https://www.ti.com/product/TPS25947
  26.
    - **Claim in stack:** DISP12: eFuse 1.5 A (part unnamed)
    - **Finding:** No part is named in STACK. TPS25947 (above) fits: 2.7-23 V, adjustable ILIM from 0.5 A (±10% above 1 A), latch or auto-retry, EN for Pico control, reverse blocking (prevents back-feed from a display board with its own supply). Iq 426 uA typ when on.
    - **Verdict:** new_option
    - **Action:** Name TPS25947 for DISP12 (ILIM about 1.5 A) and J21. Verify price and stock in P5.
    - **Impact:** Turns a 'model' item into a sourced part.
    - **Sources:**
      - https://www.ti.com/product/TPS25947
  27.
    - **Claim in stack:** J21 accepts 4.5-16 V (forum); SY81012 2.7-16 V; Radxa asks for at least 24 W (12 V/2 A)
    - **Finding:** Radxa Dragon Q6A product brief Revision 1.7 (2026-10-10): power input is 12 V (USB-C PD 12 V or 12 V DC, or the external 12 V connector). Minimum 18 W (12 V/1.5 A) without heavy USB/PCIe, at least 24 W (12 V/2 A) fully loaded. No voltage range is published, and the docs page gives pin 1 = 12 V, 2 = GND, 3 = PWR. SY81012 2.7-16 V is confirmed only from a third-party copy of the Rev 0.9A data sheet.
    - **Verdict:** unverified
    - **Action:** Keep 12 V regulated on J21. Treat the 4.5-16 V tolerance as forum-only. The 11.0 V display test and an 11.5 V Q6A brown-out bench test remain required.
    - **Impact:** The dropout-zone assumption (SYS12 about 11.5-12 V) is not vendor-guaranteed.
    - **Sources:**
      - https://dl.radxa.com/q6a/docs/radxa_dragon_q6a_product_brief.pdf
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/power-header
      - https://atta.szlcsc.com/upload/public/pdf/source/20240509/0FD7B458A1C7C9AED0BF280C094B69EB.pdf
  28.
    - **Claim in stack:** Q6A 2.9 / 9.3 / 10.1 W (measured, Geerling) as runtime-model inputs
    - **Finding:** geerlingguy/sbc-reviews #85: idle 2.9 W 'at wall', stress-ng 9.3 W, Geekbench 9.5 W, HPL 10.1 W, LLM about 7.8-7.9 W. These are wall figures that include adapter loss, so they slightly overstate draw at J21.
    - **Verdict:** confirmed
    - **Action:** Keep as conservative inputs.
    - **Impact:** None.
    - **Sources:**
      - https://github.com/geerlingguy/sbc-reviews/issues/85
  29.
    - **Claim in stack:** LNB rail 13.2 V vertical only; Bullseye 11.5-14 V V-pol; current unpublished (0.2-0.3 A assumed); PTC 0.45 A
    - **Finding:** The RTL-SDR Blog store says the Bullseye needs 11.5-14 V for vertical and 16-19 V for horizontal polarisation. It is $29.95 with 70 in stock; stability ±10 kHz at 23 C and ±30 kHz over -20 to 60 C; each unit factory-calibrated to about 1 kHz. Current draw is still not published.
    - **Verdict:** confirmed
    - **Action:** Keep. Measure the LNB current before sizing the PTC and the heat-sink attachment (already in STACK).
    - **Impact:** None.
    - **Sources:**
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
      - https://www.rtl-sdr.com/?p=44655
  30.
    - **Claim in stack:** BONI12V5: 12.5 V inside published 9-15 V and 12-15 V ranges; 0.05-0.1 A (unpublished); PTC 0.2 A
    - **Finding:** Only secondary sources were reachable; Bonito and WIMO pages returned 404 and Moonraker returned 403. One SWLing 2017 review measured 45 mA. The 9-15 V and 12-15 V ranges remain from search snippets and reviews.
    - **Verdict:** unverified
    - **Action:** Keep 12.5 V (inside both ranges) and confirm the range from the manual shipped with the antenna. The 0.2 A PTC is about 4x the measured 45 mA, which is adequate.
    - **Impact:** Low.
    - **Sources:**
      - https://swling.com/blog/2017/07/portable-powerhouses-comparing-the-bonito-boni-whip-and-wellbrook-ala1530lnp-antennas
  31.
    - **Claim in stack:** Runtime table (58 Wh warm / 50 Wh cold): A 6.9/5.9 h ... I 0.9/0.8 h; peak battery current 4.63 A at 13.2 V
    - **Finding:** Recomputed in Python (model): A 6.90/5.95, B 3.30/2.84, C 3.02/2.60, D 2.53/2.18, E 7.07/6.10, E2 4.83/4.17, F 3.07/2.65, G 1.29/1.11, H 1.88/1.62, I 0.95/0.82 h. 61.1 W / 13.2 V = 4.63 A; 45 W / 13.2 V = 3.41 A. The arithmetic matches STACK; the inputs are still models until the INA228 logs are taken. The charge time model (0.85 x 5 Ah / 3 A, about 1.4 h CC) is also consistent.
    - **Verdict:** confirmed
    - **Action:** Keep the 'model' labels. Replace them with INA228 measurements in W1-2, as planned.
    - **Impact:** None.
    - **Sources:**
      - https://www.fsaeonline.com/content/Molicel-TDS--INR-21700-P50B-80122.pdf
  32.
    - **Claim in stack:** Monthly balance to 4.20 V with ISDT 608PD via the node-N service port
    - **Finding:** isdt.co lists the 608PD as a current product: DC 5-30 V (XT60) or USB-C PD 3.1 5-28 V input, 240 W, 0.5-10 A charge, LiPo/LiFe/LiHV 1-6S, up to 0.8 A balance per cell. The page does not say whether a custom 4.10 V Li-ion target is settable; standard LiPo at 4.20 V is enough for the monthly balance.
    - **Verdict:** confirmed
    - **Action:** Keep. Set the charge current to 1-2 A for the monthly top balance.
    - **Impact:** None.
    - **Sources:**
      - https://www.isdt.co/608pd.html
  33.
    - **Claim in stack:** Fuses: mini blade 7.5 A battery, 4 A J21, 3 A LAB5; '5 A at 60 C only about 3.3 A continuous'; PTC 0.75 A AUX
    - **Finding:** The Littelfuse MINI (297) series page returned 403, so the time-current and temperature re-rating figures were not checked against the primary source. By ratio, 4.6 A peak on 7.5 A is 61% and 1.3-2.5 A on 4 A is 33-63%, which pass usual 75%-at-25-C rules of thumb, but this is not verified.
    - **Verdict:** unverified
    - **Action:** In P5, pull the Littelfuse MINI 297 data sheet (or the Bel/Eaton equivalent) and the PTC parts' hold/trip-versus-temperature curves before freezing the values.
    - **Impact:** Low risk; values look plausible.
    - **Sources:**
      - https://www.littelfuse.com/products/fuses-overcurrent-protection/fuses/automotive-passenger-car/blade-fuses/mini-297
  34.
    - **Claim in stack:** Budget injector Mini-Circuits TCBT-2R5G+ $11.31 (200 mA max)
    - **Finding:** The Mini-Circuits web store shows 71 in stock, with the lowest listed tier at 10+ for $9.05 (no qty-1 price shown). It also mentions DigiKey with 1,589 available. The 200 mA DC rating was not re-read here (data sheet link only).
    - **Verdict:** unverified
    - **Action:** Leave it to the rf_frontend owner. Re-quote the price at qty 1 from DigiKey.
    - **Impact:** Minor.
    - **Sources:**
      - https://www.minicircuits.com/WebStore/dashboard.html?model=TCBT-2R5G%2B
- **Current status oct 2026:** Status on 18 Oct 2026, checked on primary or distributor pages.
  
  **Cells and BMS**
  - Molicel P50B: active, $9.99 and in stock at 18650 Battery Store and IMR Batteries. Molicel's lineup now also lists P60C, M65A (6.5 Ah, 23.4 Wh) and P50S. M65A is sold out at the US shops checked.
  - Daly 4S 15 A Li-ion BMS: €8.00 at TinyTronics, 9 in stock.
  
  **Charger**
  - IP2368: the newest data sheet found is still V1.41 (Nov 2023; 6S support dropped).
  - The IP2368_BZ chip shows 'Not available now' at LCSC.
  - Retail boards ($12.50-23.98) are all sold as bidirectional.
  
  **Regulators and switch**
  - Pololu D36V50F12 ($39.95), D36V28F5 ($23.95), D36V50F5 ($39.95) and #2813 ($8.95): all 'Rationed (Active and Preferred)', with backorders allowed and prices unchanged.
  
  **Gauge**
  - Adafruit INA228 #5832: $14.95, in stock.
  - TI INA228: active, data sheet Rev A (2022).
  - Linux has supported INA228 in the ina238 hwmon driver since v6.17. It exposes energy only, no charge attribute.
  
  **LDOs and switches**
  - TPS7A47 data sheet is Rev G (May 2026). TPS7A4701RGWR/RGWT are out of stock at the TI store and at LCSC ($13.29). The EP variant is in stock at LCSC (110 pcs, $11.01).
  - LT3045EDD#PBF: $8.63 at LCSC, 446 in stock.
  - TPS2553: active. Out of stock at the TI store; in stock at LCSC (snapshot).
  - TPS709: active. TI lists the pin-compatible TPS7E71 as a newer part.
  - TPS3762 and LM61460: active.
  
  **Q6A and other parts**
  - Radxa Q6A product brief is now Rev 1.7 (2026-10-10). Power requirement unchanged: 12 V, 18 W minimum, 24 W when fully loaded. No header voltage range is published.
  - ISDT 608PD: current product.
  - Bullseye LNB: $29.95, 70 in stock.
  
  No EOL notices were found for any power part.
- **Notes:** **Corrections STACK needs**
  1. TPS7A4701 has no power-good pin. The 'PG on MCP #3' lines in C8, C17 and the rail table must become an external comparator or ADC sense.
  2. TPS7A47 accuracy is ±2.5% overall, so widen the LNB and Boni acceptance to about ±0.35 V.
  3. Daly cutoffs are UVP 2.70±0.05 V, release 3.0 V. Balancing starts only at 4.18 V, which confirms the monthly ISDT balance is required.
  4. The standard IP2368 already derates to the adapter's PD power, so no separate 45 W RISET mode is needed.
  5. P50B goods-in weight window becomes 68-71 g.
  6. TPS7A4701 cost is about $22-27 for two, and it is out of stock at TI and LCSC.
  
  **Biggest new risks**
  - Every IP2368 board on the market is bidirectional (COUT, Try.SRC). The Anker 737 bench source is also bidirectional. Goods-in test the board, and add reverse blocking (TPS25947) or charge only from one-way adapters.
  - TPS7A4701 is out of stock at the TI store and LCSC; DigiKey regional pages show a 12-week backorder.
  - The Adafruit INA228 power LED is not mentioned in STACK. Remove it along with the pull-ups, or standby time could roughly halve.
  - Standby is about 110 days from 50% storage SoC, not 170-185 days.
  - SMBJ13A on J21 crowbars rather than protects if the buck's high side fails short. Add an OVLO eFuse.
  
  **New options worth carrying into P5 or stage 5**
  - LM61460 synced in forced-PWM mode as the concrete C4 fallback.
  - TPS3762 as the 65 V micropower supervisor.
  - TPS25947 for J21 and DISP12.
  - Molicel M65A (+21 Wh, availability poor).
  - Samsung 58E at $4.99 (retailer specs only).
  
  **What could not be checked**
  - ADI pages (503), NKON (403), Littelfuse (403), Diodes (403), Bonito, WIMO and Moonraker.
  - Fuse derating, the Boni-Whip supply range, Daly quiescent current and wake behaviour, Bullseye current and LT3045 PSRR near dropout all remain unverified.
  
  All runtime and standby numbers are models (Python recompute). Rule check: no on-air transmitters, loops or dishes are involved in this subsystem, and prices are world USD.
  
  Downloaded data sheets are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/pw_dl/ (p50b/, ip2368/, ti/, radxa/).

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

_Run `wf_d9388111-e66`_

- **Subsystem:** power
- **Verdict:** The power architecture holds after adversarial checking: 4S1P Molicel P50B, Daly 4S 15 A BMS, IP2368 charger, Pololu #2813, D36V50F12 (SYS12), D36V28F5 (LAB5), two TPS7A4701, INA228 on I2C0, and the 7.5/4/3 A fuses. Most stage-1/2 findings were confirmed against primary sources: Molicel DS V1.1, IP2368 DS V1.41, TPS7A47 Rev G (May 2026), INA228 Rev A, TPS2553 Rev F, TPS709 Rev H, TPS25947 Rev C (May 2026), LM61460 Rev D, the Daly spec, Pololu product pages and forum, the Radxa forum, the Q6A schematic v1.21 and the Adafruit Eagle files.
  
  Four findings did not survive:
  - **TPS3762 as the UV supervisor.** Its data sheet lists only an over-voltage variant, so the stage-2 inverter built on it also falls. Replaced by TLV3012.
  - **Stage-2 EN divider (9.1k/1.0k).** The Pololu 100 k pull-up sits in parallel with the top resistor, giving 11.2/12.6 V instead of 12.0/13.5 V. Corrected to 10.0k/1.00k.
  - **Stage-2 HMI MCU board.** It said the HMI MCU is an RP2040-Zero. It is a Raspberry Pi Pico, which has a VBUS-to-VSYS Schottky (D1). The direct VBUS link is in the IMU-pack RP2040-Zero. The diode fix stands for both boards.
  - **Stage-2 'one IP2368 board DOA'.** The review's first board was one that charged but would not discharge, which is acceptable for this use. It is not a DOA rate.
  
  New items:
  - SoC resync must be calibrated per charger unit (IP2368 VTRGT tolerance).
  - The Lime-default build raises the SYS12 heat-soak gate to 4.2 A.
  - The Pico battery divider must tap SW, not N.
  - The INA228 ALERT pull-up must go to the Q6A 3.3 V rail.
  - Field charging from the DRP Anker 737 is not guaranteed. The ISDT 608PD USB-C port is also bidirectional.
  - The #2813 '6 A at 55 C' is a MOSFET temperature at 22 C ambient, not an ambient rating.
  - Q6A schematic v1.21: the header 3.3 V rail exists only while the PMIC L18B rail is on, so it should fall after poweroff. Bench-confirm.
  
  Still unverified:
  - Fuse derating (Littelfuse returned 403).
  - LT3045 PSRR near dropout (ADI unreachable).
  - Bullseye and Boni-Whip currents.
  - Daly real quiescent current.
  - The IP2368 board LDO rating.
  - TPS25947 price and stock (TI store out of stock).
  
  WebSearch was already exhausted for this turn (shared limit), so this pass used WebFetch, curl, gh and local files only.
- **Confirmed:**
  - Molicel INR-21700-P50B DS V1.1: 5000 mAh typ / 4850 min, 18.0 / 17.5 Wh, 3.6 V nominal, 4.2 V charge, 2.5 V cutoff, 5.0 A standard / 25 A max charge, 60 A continuous, charge ambient -20 to 60 C, AC 6.5 mOhm (30% SOC), DC 12.8 mOhm, 71 g max. molicel.com lists 1400 cycles, but under a 100 W BBU profile.
  - P50B is $9.99 and available at both 18650 Battery Store and IMR Batteries (Shopify JSON, 18 Oct 2026). M65A is $11.99 and NOT available at IMR.
  - Molicel INR-21700-M65A exists: 6.5 Ah, 23.4 Wh, 26 A, 322 Wh/kg, >1000 cycles. No weight, charge or temperature specs on the page; the data sheet is gated behind a contact form.
  - Daly DL-J05G-L4S15ATJ (TinyTronics EUR 8.00 incl. VAT, 9 in stock): OVP 4.25+/-0.05 V (release 4.15), UVP 2.70+/-0.05 V (release 3.0), discharge OCP 40+/-10 A, charge OCP 10+/-2 A, short circuit 10-500 us, Ron <20 mOhm, passive balance 30+/-10 mA only while charging and at 4.18 V or more, self-consumption <500 uA in operation. Sleep is 0 uA only with no current. The linked PDF file name says DL-J04G3; the page says DL-J05G.
  - IP2368 DS V1.41 (Nov 2023; V1.40 dropped 6S):
  - VTRGT = 4000 + 0.02*RVSET mV, settable 4.1-4.4 V, 10 mV step, 1% resistor.
  - ICHRG = 0.2*RISET mA (15k = 3 A, 25k or more = 5 A).
  - 250 kHz charge and discharge switching. TEND 45/48/51 h. ISTOP 100 mA. Recharge at VTRGT - N*0.1 V.
  - Trickle 100 mA below 2.5 V and 200 mA up to N*3 V. ISTB 180 uA at 14.8 V.
  - NTC: 80 uA / 0.39 V means above 45 C, 20 uA / 0.55 V means below 0 C. 100 nF at the pin. Never float the pin (10 k if unused).
  - Input 4.5-25 V, input pins withstand 30 V. 5 V non-PD input is capped at 3 A.
  - IP2368 standard part derates charge current automatically to the adapter's advertised PD power (DS section 12.3, example with RISET 15k and a 30 W adapter). Only the _NA custom variant ignores adapter capability. No separate 45 W RISET mode is needed.
  - IP2368_COUT: Try.SRC (charges a DRP partner preferentially) and needs a charge to activate after the battery is first connected. _NACT removes the activation. _BZ is the standard 2-5S charge-only part.
  - Hands-on IP2368 review (mysku, 3 May 2024):
  - One MOSFET just above 100 C when charging at 5.1 A (default RISET 27k); inductor at 60-70 C.
  - 0.1 mA in sleep.
  - A fixed 10 k sits on the NTC footprint.
  - 5 V LDO is an HT7550-1 or an ME6201. The author says the ME6201 is a 16 V part (unverified).
  - Sellers forbid connecting the board's bidirectional C port to another bidirectional C port.
  - Pololu D36V50F12 #4095: 12 V +/-4%, input 13.3-50 V, 2.3-6.5 A typical (4.5 A at 36 V in), about 500 kHz with power-save above 20 kHz, Iq 2-4 mA, EN sleep below 1.2 V / wake above 1.35 V, 100 k pull-up from EN to VIN (product page), PG +20%/-10%, reverse protection to 40 V, $39.95 / $36.75 (5+), Rationed.
  - Pololu D36V28F5 #3782: 5 V +/-4%, input 5.3-50 V, 3.2 A at 36 V (2.5-4 A), about 500 kHz, Iq 2-3 mA, same EN thresholds and 100 k pull-up, $23.95 / $22.03, Rationed.
  - D30V30F5 #4892: 5 V, 3.4 A at 30 V in, input 5-45 V, about 700 kHz, EN sleep 0.65-1.05 V, $29.95, Rationed.
  - Pololu forum t/29129 (live, 2 Jul 2026): staff reproduced >60 V on the D36V28Fx VIN when slightly over 5 V is applied to VOUT. The D30V30F5 passed about 5 V, but 5.5 V on VOUT gave about 11 V on VIN.
  - Pololu #2813:
  - $8.95 / $8.23, Rationed.
  - 4.5-40 V in the intro, but 4.5-32 V recommended and 40 V absolute maximum in the table.
  - Off current <0.2 uA.
  - A through a button to GND gives on-only. OFF and CTRL are pulsed (>1 V). Holding pins high may interfere with other controls.
  - 'Power applied to VOUT cannot be switched to VIN.'
  - 'Do not use as an emergency cutoff or safety disconnect.'
  - TPS7A4700/01 data sheet SBVS204G (May 2026):
  - Pins: OUT, NC, SENSE/FB, the ANY-OUT pins, GND, EN, NR, IN. There is NO power-good pin.
  - VIN 3-35 V operating, 36 V abs max. OUT abs min -0.4 V.
  - Accuracy +/-1% at 25 C, +/-2.5% overall (only for VIN >= VO + 1 V).
  - Dropout 216 mV at 0.5 A; 307 typ / 450 max mV at 1 A. Current limit 1.0 min / 1.26 typ A.
  - EN high 2.0 V or more. Shutdown current 3.04 uA typ / 60 uA max at 35 V.
  - TPS7A4701-EP is ACTIVE and listed by TI as pin-for-pin with the same function. LCSC on 18 Oct 2026: TPS7A4701RGWR C90084 out of stock ($13.29 at 1+); TPS7A4701MRGWREP 110 pcs ($11.01).
  - INA228 SLYS021A (May 2022):
  - VS 2.7-5.5 V. IQ 640 uA typ, 750 uA max at 25 C, 1.1 mA max over -40 to 125 C. Shutdown 2.8 / 5 uA.
  - Common mode -0.3 to 85 V. VIH 1.2 V.
  - A0/A1 are sampled on every bus transaction. A1 = A0 = VS gives 0x45.
  - ENERGY and CHARGE are invalid in triggered mode.
  - Adafruit INA228 Eagle files:
  - R6 is ONE 10k 4-pack with SCL and SDA pulled to VCC and ADDR0 and ADDR1 pulled to GND. The A0/A1 jumpers tie ADDR to VCC.
  - D1 is a green LED with R7 = 10 k from VCC.
  - ALERT has no pull-up.
  - Learn guide: the VBUS jumper is open by default (low side); close it for high side.
  - Linux: INA228 is in the ina238 hwmon driver. The Radxa linux-6.18.2 ina238.c has 'ti,ina228' with no detect routine and no charge attribute. Radxa 7.0.11 defconfig: SENSORS_INA238=m, I2C_CHARDEV=y, POWER_RESET_SYSCON_POWEROFF=y. docs.kernel.org (7.3-rc7) lists INA228.
  - TPS2553 SLVS841F: reverse-voltage protection, IREV 0.01 uA at VOUT 6.5 V and VIN 0 V. IOS equations: 88.7k gives 265/299/339 mA (min/nom/max); 34.8k gives 685/747/817 mA. TPS2553-1 is the latch-off version.
  - TPS709 SBVS186H: 2.7-30 V, 32 V abs max, 150 mA, IGND 1.3 uA typ / 2.05 max, +/-1% for VOUT 3.3 V or more, reverse-current protection. TPS70933 is the 3.3 V option.
  - TPS25947 SLVSFC9C (May 2026): 2.7-23 V, 28 V abs max, -15 V reverse polarity, back-to-back FETs, true reverse-current blocking, ILIM 0.5-6 A. TPS259470A/L: adjustable OVLO (1.2 us), active current limit, auto-retry or latch. TPS259474: circuit breaker. TPS259472: fixed OVC 3.8/5.7/13.8 V.
  - LM61460 SNVSBD5D (Jul 2022): 3-36 V (42 V transient), 6 A. The only orderable part is LM61460AANRJRR (auto mode, no spread spectrum). An external clock on EN/SYNC forces FPWM, 200 kHz-2.2 MHz. Dropout 0.4 V at 4 A.
  - Vishay SMBJ (doc 88392, rev 09-Jan-2024): SMBJ13A VBR 14.4-15.9 V, VC 21.5 V at 27.9 A. SMBJ17A VBR 18.9-20.9 V, VC 27.6 V at 21.7 A. 27.6 V is below the 30-36 V limits of TPS709, TPS7A47, IP2368 input and TPS25947.
  - Radxa staff (strongtz) say the 12 V header takes 4.5-16 V: 26 Jan, 30 Jan and 15 Oct 2026 (live thread t/31611, in reply to a 4S1P question). BigfootACA (Radxa Team): 3.6-16 V; do not use USB-C while the header is powered. Product brief Rev 1.7 (2026-10-10): 18 W minimum, 24 W fully loaded.
  - Q6A schematic v1.21 (DC-IN sheet):
  - ADP12V feeds the SY81012 with input caps of 22 uF 16 V x2 and 100 nF 16 V. That confirms the 16 V limit.
  - SY81012 EN is tied high ('ALWAYS ON').
  - The only TVS is SMBJ15CA (D19) on USB-C VBUS before the Q5 FET switch. The J21 path has no on-board TVS.
  - J21 pin 3 is PWR_ON_KEY.
  - Geerling sbc-reviews #85: idle 2.9 W (at wall), stress-ng 9.3 W, Geekbench 9.5 W, HPL 10.1 W, LLM 7.8-7.9 W.
  - RTL-SDR Blog Bullseye article: 11.5-14 V for vertical, 16-19 V for horizontal; LO 9750/10600 MHz. The store page shows $29.95 with 70 in stock and does not state current or voltage.
  - Raspberry Pi Pico data sheet: VBUS reaches VSYS through Schottky D1; for a second supply, OR it into VSYS through another Schottky (or a P-FET). ADC pins GPIO26-29 have a diode to IOVDD.
  - Waveshare RP2040-Zero FAQ: 'VSYS ... connected to the VUSB pin directly'.
  - TLV3012: 1.8-5.5 V, 2.8 uA typ / 5 uA max, 1.242 V reference (1%), push-pull output (TLV3011 is open-drain), ACTIVE.
  - Radxa forum: some header-powered boards need the power button to boot; after rupdate one board stopped at the UEFI menu (unresolved); 10 s reset loops were treated as hardware.
  - Runtime arithmetic recomputed (model): A 6.90/5.95, B 3.30/2.84, C 3.02/2.60, D 2.53/2.18, E 7.07/6.10, E2 4.83/4.17, F 3.07/2.65, G 1.29/1.11, H 1.88/1.62, I 0.95/0.82 h (warm/cold). 61.1 W / 13.2 V = 4.63 A.
  - IP2368 500 kHz second harmonic falls between NAVTEX 490 and 518 kHz, so 'no charging in HF/LF Quiet' stands.
- **Corrections:**
  1.
    - **Claim in stack:** P50B weight about 68 g; goods-in 68-70 g
    - **Finding:** The Molicel DS V1.1 gives 71 g max. molicel.com gives 265 Wh/kg (DS 260).
    - **Verdict:** corrected
    - **Action:** Set goods-in to 68-71 g. Model pack cell mass at 4 x 71 g = 284 g.
    - **Impact:** Up to +12 g in the mass model; fewer false rejects.
    - **Sources:**
      - https://www.fsaeonline.com/content/Molicel-TDS--INR-21700-P50B-80122.pdf
      - https://www.molicel.com/inr-21700-p50b/
  2.
    - **Claim in stack:** BMS cutoff 2.5-2.8 V/cell; self-consumption unknown; wake test 3/3
    - **Finding:** Daly spec: UVP 2.70+/-0.05 V, release 3.0 V; OVP 4.25+/-0.05 V, release 4.15 V; balance only while charging and at 4.18 V or more; operating self-consumption <500 uA. 'Sleep 0 uA' needs no current, which never happens with the AON load on node N.
    - **Verdict:** corrected
    - **Action:** Cutoff row: UVP 2.65-2.75 V, release 3.0 V. Budget the BMS at 0-0.5 mA. Keep the monthly ISDT 4.20 V balance, because the daily 4.10 V charge never reaches 4.18 V. Add the Daly wiring order and the heat-sink isolation rules to the assembly notes.
    - **Impact:** Standby restated (see below). Assembly safety improves.
    - **Sources:**
      - https://www.tinytronics.nl/en/power/bms-and-chargers/bms/daly-bms-li-ion-li-po-protection-circuit-4s-15a-with-balancing
      - https://www.tinytronics.nl/product_files/005102_Data-Sheet-of-DL-J04G3-L04S15ATJ-BMS-circuits.pdf
  3.
    - **Claim in stack:** IP2368 RVSET 5.1k = 4.10 V/cell; SoC resync at 16.35 V and <0.1 A, or at 16.3 V or more at rest on boot
    - **Finding:** VTRGT = 4000 + 0.02*RVSET mV, so 5.1k gives 4.102 V typical. The DS tolerance at 7.5k is +/-40 mV/cell. At 5.1k the pack CV can therefore be about 16.25-16.57 V (model). A low-tolerance unit at 16.25 V never meets either resync condition. ISTOP is 100 mA typical.
    - **Verdict:** corrected
    - **Action:** At goods-in, measure each board's CV voltage (V_CV) at the battery terminals. Set the resync thresholds to V_CV - 0.05 V, and current below 0.15 A.
    - **Impact:** Without this, the fuel gauge may never resync to 100% on some boards.
    - **Sources:**
      - https://datasheet.lcsc.com/datasheet/pdf/752f0c4a0b5b0a79a7f68752c4eac200.pdf?productCode=C5203723
  4.
    - **Claim in stack:** ISET_MODE to GND, RISET 15k = 3 A; for 45 W PD sources use an input-power-limit RISET mode
    - **Finding:** The pin table says ISET_MODE 'to GND'. Section 12 says 'through a 1 k resistor to GND', and the reviewed board fits R1 = 1 k. The standard part auto-derates to the advertised PD power. Boards ship with RISET 27k (5 A).
    - **Verdict:** corrected
    - **Action:** Keep ISET_MODE to GND through 1 k (as fitted) and change RISET to 15k (1%). Drop the separate 45 W mode.
    - **Impact:** One configuration; the board runs cooler than at the 5 A default.
    - **Sources:**
      - https://datasheet.lcsc.com/datasheet/pdf/752f0c4a0b5b0a79a7f68752c4eac200.pdf?productCode=C5203723
      - https://mysku.club/blog/aliexpress/100034.html
  5.
    - **Claim in stack:** IP2368 'BZ charge-only' board; Anker 737 as a PD source
    - **Finding:** All retail boards are sold as bidirectional COUT boards (Try.SRC, activation charge needed). Anker 737 in STACK is the 24,000 mAh power bank, which is DRP.
  
  A reverse-blocking eFuse (TPS259470x) on VBUS stops the pack being drained. But with Try.SRC the board takes the source role, so charging from a DRP bank will most likely flap or fail rather than charge.
  
  The ISDT 608PD USB-C port is also input-or-output (140 W in / 100 W out), so the Anker to ISDT fallback is not guaranteed either.
    - **Verdict:** new_risk
    - **Action:** Fit enclosure USB-C, then TPS259470A (OVLO about 22 V, ILIM about 3.5 A), then the board VBUS; route CC1/CC2 direct.
  
  Goods-in test after one activation charge: a sink on the port must see no VBUS. Keep a board that refuses to discharge.
  
  Bench-test Anker 737 to receiver and Anker 737 to ISDT 608PD. Until a test passes, field charging is a one-way PD wall adapter only.
    - **Impact:** Prevents the pack draining; field charging from the power bank is unproven.
    - **Sources:**
      - https://datasheet.lcsc.com/datasheet/pdf/752f0c4a0b5b0a79a7f68752c4eac200.pdf?productCode=C5203723
      - https://mysku.club/blog/aliexpress/100034.html
      - https://www.isdt.co/608pd.html
      - https://www.ti.com/lit/ds/symlink/tps25947.pdf
  6.
    - **Claim in stack:** IP2368 board on node N during the 16.8 V monthly ISDT balance
    - **Finding:** The reviewed boards carry an HT7550-1 or ME6201 5 V LDO. The reviewer calls the ME6201 a 16 V part; a commenter disputes this. Not verified.
    - **Verdict:** unverified
    - **Action:** At goods-in, read the LDO marking. If it is not documented to 20 V or more, replace it with a part rated 30 V or more, or remove the board from node N during the 4.20 V balance.
    - **Impact:** Possible LDO over-voltage on the board at 16.8 V.
    - **Sources:**
      - https://mysku.club/blog/aliexpress/100034.html
  7.
    - **Claim in stack:** Backup EN of D36V50F12: divider about 0.10, sleep about 12.0 V, wake about 13.5 V (stage 2: 9.1 k over 1.0 k)
    - **Finding:** The Pololu product page confirms a 100 k pull-up from EN to VIN. It sits in parallel with the top resistor. 9.1k/1.0k gives sleep 11.2 V and wake 12.6 V (model). 10.0k/1.00k gives sleep 12.1 V and wake 13.6 V. With the pull-up at +/-20% (80-120 k), sleep moves to 11.9-12.3 V. The divider draws 1.6 mA, only while ON.
    - **Verdict:** corrected
    - **Action:** Fit a 10.0 k top (SW to EN) and a 1.00 k bottom, both 1%. Calibrate on the bench.
    - **Impact:** The cutoff lands where intended instead of 0.8 V too low.
    - **Sources:**
      - https://www.pololu.com/product/4095
  8.
    - **Claim in stack:** C4 gate (2): 60 min at 3.5 A in the closed enclosure at 14.0 and 16.4 V
    - **Finding:** The user made the with-Lime build the default. STACK gives SYS12 about 4 A at the Lime peak. Pololu's 4.5 A typical is at 36 V in and room temperature.
    - **Verdict:** corrected
    - **Action:** Run gate (2) at 4.2 A. Log the D36V50F12, #2813 and fuse temperatures. D36V50F5 stays the LAB5 escape route if LAB5 exceeds 2.5 A.
    - **Impact:** Qualifies SYS12 for the build that will actually be shipped.
    - **Sources:**
      - https://www.pololu.com/product/4095
  9.
    - **Claim in stack:** Main switch #2813: '6 A at 55 C', OFF held by the supervisor
    - **Finding:** Pololu's rows are the currents that heat the MOSFETs to 55 C and 150 C in 22 C still air. They are not ambient ratings. Model: at 4.6 A in a 45-50 C enclosure the MOSFETs run about 65-70 C. Recommended operating limit is 32 V; 40 V is abs max. Pololu says it is not a safety disconnect.
    - **Verdict:** corrected
    - **Action:** Reword STACK: about 6 A gives a 55 C MOSFET in 22 C air. Design limit 32 V. BMS plus the 7.5 A fuse are the safety disconnects. Keep the 'held OFF vs button on A' bench test.
    - **Impact:** No BOM change; correct thermal margin statement.
    - **Sources:**
      - https://www.pololu.com/product/2813
  10.
    - **Claim in stack:** Micropower UV supervisor 12.8/13.6 V; stage 1 picked TPS3762 (5% hysteresis on N); stage 2 added an inverter
    - **Finding:** TPS3762 is a window (OV and UV) functional-safety supervisor with BIST and latch. Its DS Rev A Table 9-1 lists only TPS3762D02OVDDFR: over-voltage only, 2% hysteresis, latch and BIST enabled. The TI page lists no other orderable part.
  
  STACK wiring is a diode-OR of the supervisor output with GP13 into OFF, so it needs an active-high push-pull output.
    - **Verdict:** corrected
    - **Action:** Use TI TLV3012 (push-pull, 1.242 V reference, 2.8 uA) on AON 3.3 V. Model values:
  - Divider from N: 3.3 MOhm into IN-, 346 kOhm to GND (0.1%).
  - REF through 100 kOhm into IN+; OUT through 4.22 MOhm into IN+.
  - Trip about 12.8 V falling, release about 13.6 V. OUT is high on undervoltage.
  - OUT goes through BAT54 to #2813 OFF. No inverter needed.
  Calibrate on the bench.
    - **Impact:** The supervisor becomes buildable; total current about 8 uA.
    - **Sources:**
      - https://www.ti.com/product/TPS3762
      - https://www.ti.com/lit/ds/symlink/tps3762.pdf
      - https://www.ti.com/product/TLV3012
  11.
    - **Claim in stack:** LAB5 feeds the Pico ('via VSYS') and the IMU pack; back-feed rules cover only Q6A VBUS and HDMI
    - **Finding:** Back-feeding the D36V28F5 output above about 5 V pumps its VIN above 60 V (Pololu staff, live thread).
  
  The HMI MCU is a Raspberry Pi Pico (STACK BOM), whose USB feeds VSYS through D1. Plugging it into a PC back-feeds LAB5 at about 4.7 V and powers the whole LAB5 load from the PC.
  
  The IMU-pack RP2040-Zero has VSYS tied directly to VBUS, so its USB puts 5.0-5.25 V straight into LAB5. That is the pump condition.
    - **Verdict:** corrected
    - **Action:** Fit four fixes:
  - A Schottky from LAB5 into Pico VSYS (the data sheet's ORing scheme).
  - A Schottky in the IMU pack on its 5 V input.
  - SMBJ17A (Vishay/Littelfuse) on the SW node.
  - Assembly rule: flash either MCU only with the main switch ON or with it unplugged from LAB5.
    - **Impact:** Protects both TPS7A4701 (36 V abs max) and the PC USB port. About $1.
    - **Sources:**
      - https://forum.pololu.com/t/strange-behavior-of-d36v28f5-pololu-3782/29129
      - https://pip-assets.raspberrypi.com/categories/610-raspberry-pi-pico/documents/RP-008307-DS-2-pico-datasheet.pdf
      - https://www.waveshare.com/wiki/RP2040-Zero
  12.
    - **Claim in stack:** INA228 board prep: remove the pull-ups; AON about 0.7 mA
    - **Finding:** R6 is one 4 x 10 k pack: SCL and SDA pull-ups plus the ADDR0/ADDR1 pull-downs. Removing it floats A0/A1, and the INA228 samples A0/A1 on every transaction.
  
  The LED is D1 with R7 = 10 k, about 0.12 mA (about 1.8 mW at 14.8 V).
  
  The VBUS jumper SJ1 is open by default.
  
  Shunt R1 is 'HoLLR2512-2W-15mR-1%' in the Eagle BOM, but the product text says 0.1%.
  
  IQ is 640 typ / 750 max uA at 25 C and 1.1 mA over temperature. CHARGE is only valid in continuous mode.
  
  ALERT has no on-board pull-up.
    - **Verdict:** corrected
    - **Action:** Remove R6 and R7. Close both A0 and A1 jumpers (0x45), or wire both ADDR pads to GND (0x40), and set labpowerd to match. Close SJ1. Use continuous mode. Calibrate SHUNT_CAL against a reference at 0.5/2/4 A. Pull ALERT up to the Q6A header 3.3 V, never to AON.
    - **Impact:** No address drift, no back-feed into the Q6A I/O, about 1% gauge accuracy.
    - **Sources:**
      - https://github.com/adafruit/Adafruit-INA228-PCB
      - https://learn.adafruit.com/adafruit-ina228-i2c-power-monitor/pinouts
      - https://www.ti.com/lit/ds/symlink/ina228.pdf
  13.
    - **Claim in stack:** OFF draw about 13-14 mW, about 170-185 days
    - **Finding:** Model at 14.8 V (linear AON, so mA in equals mA out):
  - INA228 typ + LED + IP2368 0.18 mA + TPS709 + comparator, Daly 0 mA: 14.2 mW, 106 days from 36 Wh (50%).
  - LED removed, Daly 0.5 mA: 19.8 mW, 76 days.
  - Worst case: 28.9 mW, 52 days.
  - INA228 in shutdown: 2.9-10.3 mW, 145-509 days.
  - Fuse pulled (Daly only, worst case): 7.4 mW, 203 days or more.
    - **Verdict:** corrected
    - **Action:** Restate standby as about 50-105 days from 50% storage (model).
  
  Rule: labpowerd puts the INA228 into shutdown at poweroff when no charger is present. For storage longer than 2-4 weeks, pull the 7.5 A pack fuse.
  
  Bench target: total OFF current at 14.8 V of 1.0 mA or less with the INA228 running, and 0.25 mA or less (excluding the BMS) with the INA228 in shutdown.
    - **Impact:** Prevents a pack over-discharged in storage.
    - **Sources:**
      - https://www.ti.com/lit/ds/symlink/ina228.pdf
      - https://www.tinytronics.nl/product_files/005102_Data-Sheet-of-DL-J04G3-L04S15ATJ-BMS-circuits.pdf
      - https://datasheet.lcsc.com/datasheet/pdf/752f0c4a0b5b0a79a7f68752c4eac200.pdf?productCode=C5203723
  14.
    - **Claim in stack:** TPS7A4701 'PG on MCP #3'; acceptance 13.2 V +/-0.2 V and 12.5 V +/-0.25 V
    - **Finding:** There is no PG pin (Rev G pin table). Overall accuracy is +/-2.5% and holds only for VIN >= VO + 1 V. OUT abs min is -0.4 V.
  
  ANY-OUT settings:
  - 13.2 V: ground 6P4V1, 3P2V, 1P6V, 0P4V and 0P2V.
  - 12.5 V: ground 6P4V1, 3P2V, 0P8V, 0P4V, 0P2V and 0P1V.
    - **Verdict:** corrected
    - **Action:** Replace PG with a TLV3011 (open-drain) per rail. It senses about 90% of nominal through a divider, is powered from the Q6A 3.3 V, and drives MCP #3.
  
  Widen acceptance to +/-0.35 V, tested at a battery voltage of 14.2 V or more.
  
  Add a Schottky from OUT to GND (cathode on OUT) on both outputs.
    - **Impact:** Fixes a schematic error and avoids false acceptance failures.
    - **Sources:**
      - https://www.ti.com/lit/ds/symlink/tps7a47.pdf
  15.
    - **Claim in stack:** TPS7A4701 x2 at LCSC, $10-20, price unverified
    - **Finding:** On 18 Oct 2026 TPS7A4701RGWR (LCSC C90084) is out of stock at $13.29. TPS7A4701MRGWREP (TI Enhanced Product, pin-for-pin with the same function per TI) has 110 in stock at $11.01.
    - **Verdict:** corrected
    - **Action:** Order 2x TPS7A4701MRGWREP now, or RGWR if a franchised distributor has stock. Budget $22-27.
    - **Impact:** About +$7, and the schedule risk is removed.
    - **Sources:**
      - https://www.lcsc.com/product-detail/C90084.html
      - https://www.ti.com/product/TPS7A4701-EP
  16.
    - **Claim in stack:** J21: SMBJ13A + 220 uF/25 V; 'Q6A accepts 4.5-16 V (forum)'
    - **Finding:** The 4.5-16 V range is confirmed by Radxa staff four times; latest 15 Oct 2026, live. Q6A schematic v1.21: ADP12V has 16 V input caps and no on-board TVS on the J21 path.
  
  If the SYS12 high side fails short, the SMBJ13A (VBR 14.4-15.9 V) conducts about 2-8 A at 16.4 V (model) until the 4 A fuse opens, with the Q6A sitting near its 16 V limit.
    - **Verdict:** corrected
    - **Action:** J21 chain: SYS12, 4 A fuse, TPS259470A (OVLO about 13.5 V, ILIM about 4 A), pi filter, Vishay/Littelfuse SMBJ13A plus 220 uF/25 V, then J21 or the pads. Treat 16 V as absolute. Keep the Q6A USB-C sealed.
    - **Impact:** Closes the regulator-short over-voltage path for about $2-3.
    - **Sources:**
      - https://forum.radxa.com/t/radxa-q6a-4s1p-powering/31611
      - https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://www.vishay.com/docs/88392/smbj.pdf
      - https://www.ti.com/lit/ds/symlink/tps25947.pdf
  17.
    - **Claim in stack:** DISP12 eFuse 1.5 A (unnamed)
    - **Finding:** TPS25947 meets the needs: ILIM 0.5-6 A (+/-10% above 1 A), reverse blocking, EN, OVLO. The TI store shows TPS259470ARPWR out of stock; price not shown.
    - **Verdict:** new_option
    - **Action:** Name TPS259470A for DISP12 (ILIM 1.5 A, EN from GP16, OVLO about 13.5 V), and the same part for J21 and USB-C VBUS. Check LCSC/DigiKey stock and price in P5.
    - **Impact:** One eFuse part number for three places.
    - **Sources:**
      - https://www.ti.com/lit/ds/symlink/tps25947.pdf
      - https://www.ti.com/product/TPS25947/part-details/TPS259470ARPWR
  18.
    - **Claim in stack:** Pico opens #2813 3 s after the Q6A 3.3 V disappears (stage 2: the 3.3 V rail may stay up after poweroff)
    - **Finding:** Schematic v1.21 DC-IN sheet:
  - VCC_3V3 (ETA3521 U50) is enabled from VCC_5V_PERI.
  - VCC_5V_PERI (SY7120 EN plus the SGM40666AS nEN through Q22) is gated by the PMIC rail VREG_L18B_1P8.
  - The SY81012 is 'ALWAYS ON'.
  So the header 3.3 V should fall whenever the PMIC turns L18B off. 'halt' (1.9-2.5 W) likely leaves the PMIC on. Whether 'poweroff' turns L18B off is firmware-dependent and unpublished.
    - **Verdict:** confirmed
    - **Action:** Keep stage 2's second trigger:
  - ARM-OFF frame on UART7, then a systemd-shutdown hook sends OFF-NOW.
  - The Pico pulses OFF on 3.3 V loss, or 20-30 s after OFF-NOW, or 60 s after heartbeat loss following ARM-OFF.
  - Bring-up: log J21 current for 2 min after 'systemctl poweroff'.
    - **Impact:** Prevents a silent drain; risk is lower than stage 2 stated.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://forum.radxa.com/t/upcoming-radxa-dragon-q6a/26723
  19.
    - **Claim in stack:** Pico reads the battery through its own 1:6 divider (tap point unspecified)
    - **Finding:** Pico GPIO26-29 ADC pins have a diode to IOVDD. If the divider taps node N, it back-powers the unpowered Pico (LAB5 off) whenever the main switch is OFF.
    - **Verdict:** new_risk
    - **Action:** Tap the 1:6 divider from SW, not N. 16.8 V / 6 = 2.8 V, below 3.3 V. Use 100 k / 20 k or similar.
    - **Impact:** Avoids a parasitic supply into the Pico and a standby leak.
    - **Sources:**
      - https://pip-assets.raspberrypi.com/categories/610-raspberry-pi-pico/documents/RP-008307-DS-2-pico-datasheet.pdf
  20.
    - **Claim in stack:** AON 3.3 V: TPS709-class LDO (to verify)
    - **Finding:** TPS709 (SBVS186H): 2.7-30 V, 32 V abs max, IGND 1.3 uA typ, 150 mA, reverse-current protection. TPS70933 is the 3.3 V option.
    - **Verdict:** confirmed
    - **Action:** Fix the part as TPS70933DBVR.
    - **Impact:** Turns a model item into a sourced part.
    - **Sources:**
      - https://www.ti.com/lit/ds/symlink/tps709.pdf
  21.
    - **Claim in stack:** C4 fallback: forced-PWM synchronous buck via RT/SYNC (P5)
    - **Finding:** LM61460AANRJRR: 3-36 V, 6 A. A clock on EN/SYNC forces FPWM, 200 kHz-2.2 MHz. Dropout 0.4 V at 4 A. ACTIVE.
    - **Verdict:** new_option
    - **Action:** Name LM61460AANRJRR, synced from a clean clock chosen by the harmonic scan (1.8-2.1 MHz preferred). Price and stock in P5.
    - **Impact:** A concrete escape route if the Pololu module fails the NAVTEX/LF A/B test.
    - **Sources:**
      - https://www.ti.com/lit/ds/symlink/lm61460.pdf
  22.
    - **Claim in stack:** TPS2553: LNA channels 300 mA (240 mA minimum), LAB port 0.75 A
    - **Finding:** Recomputed from the DS equations: 88.7k gives 265/299/339 mA; 34.8k gives 685/747/817 mA (resistor tolerance excluded).
    - **Verdict:** corrected
    - **Action:** RILIM 88.7k (1%) for LNA ch1-4; the minimum is 265 mA, not 240 mA. RILIM 34.8k for the LAB port.
    - **Impact:** None functionally.
    - **Sources:**
      - https://www.ti.com/lit/ds/symlink/tps2553.pdf
  23.
    - **Claim in stack:** Cells: P50B baseline; M65A option
    - **Finding:** M65A: 6.5 Ah, 23.4 Wh, 26 A, about 73 g implied. Out of stock at IMR ($11.99). No charge temperature or cold data published.
    - **Verdict:** new_option
    - **Action:** Keep P50B. Consider M65A (93.6 Wh pack, under 100 Wh) only after the full data sheet, stock, and a 0 C discharge test.
    - **Impact:** About +30% energy if the cells qualify.
    - **Sources:**
      - https://www.molicel.com/inr-21700-m65a/
      - https://imrbatteries.com/products/molicel-m65a-21700-6500mah-26a-battery
  24.
    - **Claim in stack:** Fuses 7.5/4/3 A mini blade; '5 A at 60 C only about 3.3 A'
    - **Finding:** Littelfuse MINI 297 pages and PDF return 403 (Akamai); the Eaton ATM PDF failed. Ratios: 4.63 A on 7.5 A is 62%; 2.3 A on the LAB5 3 A fuse is 77% (Lime build).
    - **Verdict:** unverified
    - **Action:** In P5, get the fuse time-current and temperature re-rating curves. Bench-test 4.6 A on the 7.5 A fuse and 2.3 A on the LAB5 3 A fuse, 30 min each in a 50 C enclosure. If the LAB5 fuse runs hot, move to 4 A with the D36V50F5.
    - **Impact:** Low; the values are plausible.
    - **Sources:**
      - https://www.littelfuse.com/products/fuses-overcurrent-protection/fuses/automotive-passenger-car/blade-fuses/mini-297
  25.
    - **Claim in stack:** LNA rail 2x LT3045 at 4.5 V from LAB5
    - **Finding:** ADI was unreachable again (HTTP/2 reset, empty reply). LAB5 can be as low as 4.8 V, leaving 0.25-0.45 V of headroom.
    - **Verdict:** unverified
    - **Action:** Bench-measure 500 kHz ripple on the 4.5 V rail with LAB5 at 4.8 V. If PSRR is poor, lower the rail to 4.3-4.4 V (ask the rf_frontend owner).
    - **Impact:** Possible spur leak into the LNAs.
    - **Sources:**
      - https://www.lcsc.com/product-detail/C666574.html
  26.
    - **Claim in stack:** Runtime table and the 13.2 V software cutoff
    - **Finding:** The arithmetic is correct (model). At the Lime peak of 4.63 A, the path resistance (4 x 12.8 mOhm DC + BMS <20 + shunt 15 + fuse and wiring about 20, partly assumed) gives about 0.5 V of sag. So 13.2 V under load is about 13.7 V OCV, and mode I will stop early. Typical use with the Lime default is mode H: 1.9 h warm / 1.6 h cold (user-accepted).
    - **Verdict:** confirmed
    - **Action:** Keep the 'model' labels. Replace them with INA228 logs in W1-2. State mode H as the typical session.
    - **Impact:** Mode I runtime is optimistic.
    - **Sources:**
      - https://www.fsaeonline.com/content/Molicel-TDS--INR-21700-P50B-80122.pdf
- **New risks:**
  - Field charging from the DRP Anker 737 is unproven. A COUT IP2368 board (Try.SRC), even with a reverse-blocking eFuse, will probably not sink from a DRP bank. The ISDT 608PD USB-C port is also bidirectional (140 W in / 100 W out). Until a bench test passes, a one-way PD wall adapter is the only certain source.
  - IP2368 VTRGT tolerance (about +/-40 mV/cell) puts the pack CV at about 16.25-16.57 V (model) with RVSET 5.1k. The fixed 16.35 V / 16.3 V SoC resync thresholds can then fail on some boards. Calibrate them per board.
  - The with-Lime default puts about 4 A on SYS12 and 2.3 A on LAB5 (77% of its 3 A fuse). The SYS12 heat-soak gate must be run at 4.2 A, and the LAB5 fuse heating checked.
  - The Pico battery divider must tap SW, not N: RP2040 ADC pins have a diode to IOVDD, so a divider on N would back-power the unpowered Pico.
  - The Adafruit INA228 ALERT line has no on-board pull-up. A pull-up to AON 3.3 V would back-feed the Q6A header pin; use the Q6A 3.3 V rail.
  - The IMU-pack RP2040-Zero ties VBUS directly to its 5 V input (Waveshare FAQ). USB flashing of the pack back-feeds LAB5 above 5 V, which is the D36V28F5 pump condition (>60 V on SW). It needs its own Schottky.
  - The Q6A J21 path has no on-board TVS; the SMBJ15CA is only on USB-C VBUS (schematic v1.21). The SY81012 input caps are rated 16 V, so the external OVLO eFuse plus SMBJ13A are the only over-voltage protection.
  - The 5 V LDO on the IP2368 board (HT7550-1 or ME6201) may be rated only 16 V (unverified). It sits on node N, which reaches 16.8 V during the monthly ISDT balance.
  - The TPS25947 (proposed for USB-C VBUS, J21 and DISP12) is out of stock at the TI store; price not verified.
  - The Adafruit INA228 shunt is listed as 1% in the Eagle BOM but as 0.1% in the product text. Calibrate SHUNT_CAL against a reference.
- **Refuted findings:**
  1.
    - **Finding:** Stage 1: TPS3762 (5% hysteresis version, release about 13.45 V) placed on node N as the 12.8 V UV supervisor.
    - **Why:** TPS3762 is a 65 V window (OV and UV) functional-safety supervisor with BIST and latch. Its data sheet Rev A Table 9-1 lists only TPS3762D02OVDDFR (over-voltage only, 2% hysteresis, latch and BIST enabled), and the TI product page lists no other orderable part. A UV 5% variant cannot be bought. Replaced by TLV3012 (push-pull, internal 1.242 V reference) on AON 3.3 V.
  2.
    - **Finding:** Stage 2: an inverter (N-FET plus 1 M pull-ups) after the TPS3762 open-drain output to hold #2813 OFF high.
    - **Why:** It is built on a part that cannot be ordered. STACK already diode-ORs the supervisor with GP13 into OFF, so an active-high push-pull comparator (TLV3012) drives OFF directly with no inverter.
  3.
    - **Finding:** Stage 2: a stiff backup-EN divider of about 9.1 k over 1.0 k makes the internal 100 k pull-up irrelevant (sleep about 12.0 V, wake about 13.5 V).
    - **Why:** The 100 k pull-up from EN to VIN (Pololu product page) is in parallel with the 9.1 k top resistor. The thresholds become 11.2 V sleep and 12.6 V wake (model). 10.0 k / 1.00 k gives 12.1 / 13.6 V.
  4.
    - **Finding:** Stage 2: the HMI Pico is an RP2040-Zero whose VSYS is tied directly to VBUS.
    - **Why:** STACK's BOM and pin map use a Raspberry Pi Pico for the HMI, and the Pico data sheet shows VBUS feeding VSYS through Schottky D1. The direct link is in the IMU-pack RP2040-Zero. The mitigation still stands, but it must cover both boards (Pico: Schottky from LAB5 into VSYS; pack: Schottky on its 5 V input).
  5.
    - **Finding:** Stage 2: 'one of two IP2368 boards was DOA, buy 2-3'.
    - **Why:** In the mysku review the first board charged its battery but would not discharge; the author treated it as defective and was refunded. For this charge-only use that behaviour is acceptable or even preferred, so it is not a dead-on-arrival rate. Two boards (STACK) plus goods-in testing are enough.
  6.
    - **Finding:** Stage 1: the Adafruit INA228 power LED 'alone could halve standby time'.
    - **Why:** From the Eagle files the LED is D1 with R7 = 10 k from 3.3 V, about 0.12 mA, or about 1.8 mW at 14.8 V. That is about 13% of the 14 mW OFF budget, not half (stage 2 had already corrected this).
  7.
    - **Finding:** STACK and Stage 1: #2813 is rated '6 A at 55 C'.
    - **Why:** Pololu's rows are 'continuous current at 55 C / 150 C' with the footnote '12 V, 22 C ambient, still air'. They are the currents that heat the MOSFETs to those temperatures, not ratings at 55 C ambient.
  8.
    - **Finding:** Stage 1: the RTL-SDR Blog store page states the Bullseye supply as 11.5-14 V (vertical).
    - **Why:** The store page (18 Oct 2026) gives no supply voltage or current. The 11.5-14 V / 16-19 V figures are in the RTL-SDR Blog article (?p=44655). The value stands; only the attribution changes.
  9.
    - **Finding:** Stage 1: Daly BMS self-consumption and wake behaviour 'not published'.
    - **Why:** The Daly spec linked from TinyTronics gives operating self-consumption <500 uA and sleep 0 uA (entry requires no current). Corrected in stage 2 and confirmed here.
- **Corrected spec:** POWER SUBSYSTEM v1.1 (stage-3 verified, 18 Oct 2026; 'model' = calculated, not measured)
  
  **Pack**
  - 4S1P Molicel INR-21700-P50B (DS V1.1). Buy 5 at $9.99 (18650 Battery Store / IMR, in stock).
  - Goods-in: at least 4.85 Ah; 68-71 g; AC IR about 6.5 mOhm (30% SOC) and DC about 12.8 mOhm as typical references; no terminal or wrap wear.
  - Daily charge to 4.10 V/cell; monthly ISDT 608PD LiPo 4.20 V balance through the node-N service port (5 A fuse, after the shunt), main switch OFF.
  - Usable energy (model): 58 Wh warm / 50 Wh at 0 C. Never flown.
  - Option: M65A only after data sheet, stock and a 0 C test.
  
  **BMS**
  - Daly DL-J05G-L4S15ATJ 4S 15 A common port (TinyTronics EUR 8.00): OVP 4.25+/-0.05 V (release 4.15), UVP 2.70+/-0.05 V (release 3.0), DOCP 40+/-10 A, COCP 10+/-2 A, Ron <20 mOhm, balance 30 mA at 4.18 V or more while charging, Iq <500 uA.
  - Wire B- first, then the sense leads from B0 up. The heat-sink must not touch cells or nickel.
  
  **Path**
  Cells, BMS, mini-blade 7.5 A, INA228 shunt, node N, Pololu #2813 HP, node SW.
  - Wiring 18-20 AWG.
  - SMBJ17A (Vishay/Littelfuse) on N and a second SMBJ17A on SW.
  
  **Gauge**
  - Adafruit INA228 #5832 ($14.95). Remove R6 (4 x 10k pack) and R7 (LED).
  - Address: close A0 and A1 (0x45) or wire ADDR to GND (0x40). Close SJ1 for high side.
  - VS from AON. ADCRANGE 0 (+/-10.92 A). Continuous mode.
  - SHUNT_CAL calibrated against a reference. ALERT pulled up to the Q6A header 3.3 V only.
  - i2c-dev, labpowerd sole owner, 'blacklist ina238', no ti,ina228 DT node, i2cdetect must not show UU.
  - At poweroff with no charger present: INA228 into shutdown.
  
  **AON**
  - TPS70933DBVR from N (2.7-30 V, 32 V abs max, 1.3 uA).
  - UV supervisor TLV3012 (push-pull) on AON:
    - N through 3.3 MOhm into IN-, 346 kOhm to GND (0.1%).
    - REF through 100 kOhm into IN+; OUT through 4.22 MOhm into IN+.
    - Trip about 12.8 V, release about 13.6 V (model; calibrate).
    - OUT through BAT54 to #2813 OFF, diode-ORed with Pico GP13.
  
  **Main switch**
  - Pololu #2813 HP ($8.95).
  - Button on A to GND (on-only); OFF pulses from the Pico; OFF held by TLV3012 under UV.
  - Design limit 32 V. Not a safety disconnect.
  
  **SYS12**
  - Pololu D36V50F12 ($39.95, buy 2), from SW.
  - Backup EN: 10.0 k (SW to EN) / 1.00 k (EN to GND), 1%. Sleep about 12.1 V, wake about 13.6 V (model; calibrate). v2.1 owner decision: 4.99 k / 562 Ohm 0.1% 25 ppm/K, sleep about 11.35 V (10.9-11.8 V), wake about 12.77 V (at most 13.27 V, below the UV release); E1-04, Zh-03.
  - C4 gates: (1) NAVTEX/LF A/B; (2) 60 min at 4.2 A in the closed enclosure at 14.0 and 16.4 V.
  - Fallback: LM61460AANRJRR synced on EN/SYNC (FPWM, clock 1.8-2.1 MHz from the harmonic scan).
  
  **J21**
  - SYS12, 4 A fuse, TPS259470A (OVLO about 13.5 V, ILIM about 4 A), pi filter, SMBJ13A (Vishay/Littelfuse) plus 220 uF/25 V, then J21 (20 AWG twisted pair from pads in the Lime build).
  - Q6A limit 4.5-16 V (Radxa staff). Q6A USB-C stays sealed.
  - PWR pin (J21 pin 3) pulse 0.8-1.0 s from the Pico.
  
  **DISP12**
  - SYS12, LC, TPS259470A (ILIM 1.5 A, OVLO about 13.5 V, EN on GP16).
  
  **AUX12**
  - Unchanged: P-FET +/-20 V VGS, PTC 0.75 A hold.
  
  **LAB5**
  - Pololu D36V28F5 ($23.95), 3 A fuse.
  - Pico VSYS fed through a Schottky (data sheet ORing). IMU-pack RP2040-Zero 5 V input through a Schottky.
  - Flash either MCU only with the main switch ON or with it unplugged.
  - D36V50F5 ($39.95) if LAB5 exceeds 2.5 A.
  
  **LNA4V5**
  - LAB5, LC, 2x LT3045EDD#PBF in parallel (LCSC, about $8.63 each, not re-checked). v2.1: 2x LT3045EMSE#PBF at 4.30 V (RSET 21.5k), see E2-04.
  - TPS2553 per channel, RILIM 88.7k (265/299/339 mA). LAB USB-A TPS2553 RILIM 34.8k (685/747/817 mA). TPS2553-1 if latch-off is preferred.
  
  **LNB13V2 / BONI12V5**
  - 2x TPS7A4701 (RGWR, or TPS7A4701MRGWREP: LCSC 110 pcs, $11.01), from SW through LC.
  - ANY-OUT 13.2 V: ground 6P4V1, 3P2V, 1P6V, 0P4V, 0P2V.
  - ANY-OUT 12.5 V: ground 6P4V1, 3P2V, 0P8V, 0P4V, 0P2V, 0P1V.
  - EN from MCP #1 (2.0 V or more is high).
  - No PG pin: per rail, a divider to about 90% into a TLV3011 (open-drain, powered from the Q6A 3.3 V), into MCP #3.
  - Schottky OUT to GND on each.
  - PTCs: LNB sized after the current measurement (provisional 0.45 A); Boni 0.2 A.
  - Acceptance +/-0.35 V at the connector, with the battery at 14.2 V or more.
  
  **Charger**
  - IP2368 board (assume COUT; buy 2): RVSET 5.1k (1%, 4.102 V/cell, pack CV about 16.25-16.57 V model), RISET 15k, ISET_MODE through 1 k to GND, NTC 10k B3380 on a cell plus 100 nF (charge 0-45 C), KSD9700 70 C on the board.
  - Enclosure USB-C, TPS259470A (OVLO about 22 V, ILIM about 3.5 A), board VBUS; CC1/CC2 direct.
  - Sources: one-way PD adapter, 60 W or more, qualified with the FNB58.
  - Auto-derating handles 45 W sources.
  - No charging in HF/LF Quiet (250/500 kHz).
  - The on-board 5 V LDO must be rated 20 V or more.
  - SoC resync = measured V_CV - 0.05 V at <0.15 A.
  
  **Cutoffs**
  - Economy: 14.0 V / 20%. Linux poweroff: 13.2 V under load for 10 s, or 3%.
  - Pico emergency: 13.05 V for 5 s (v2.1, the same 13050 mV as the labd graceful cutoff; was 12.9 V). TLV3012: 12.8 V hold OFF, 13.6 V release.
  - D36V50F12 EN: about 12.1 V. BMS UVP: 2.70 V/cell.
  - Pico second OFF trigger: OFF-NOW frame plus 20-30 s, or 60 s heartbeat loss after ARM-OFF.
  - Pico battery divider (1:6) taps SW, not N.
  
  **Standby (model)**
  - About 50-105 days from 50% SoC, or about 145-500 days with the INA228 in shutdown.
  - Storage longer than 2-4 weeks: pull the 7.5 A fuse.
  
  **Runtime (model)**
  - With Lime as default: mode H 1.9 / 1.6 h, mode I 0.95 / 0.82 h (optimistic: about 0.5 V sag at 4.6 A).
  - Without Lime: mode B 3.3 / 2.8 h.
  
  **Prices (USD, 18 Oct 2026)**
  - Verified: P50B $9.99; Daly about $9; D36V50F12 $39.95; D36V28F5 $23.95; #2813 $8.95; INA228 $14.95; TPS7A4701 EP $11.01.
  - Not verified: TPS25947, TLV3012/3011.
- **Bench tests:**
  - IP2368 goods-in (each board), after one activation charge from a one-way PD adapter:
  - With the board on battery, attach FNB58 plus a load as a sink. Any VBUS means COUT; keep a board that never sources.
  - Record V_CV at the battery terminals with RVSET 5.1k (target 16.25-16.57 V), the termination current, and the NTC trips (0.39 V hot / 0.55 V cold with 10k B3380).
  - Read the 5 V LDO marking.
  - DRP charging matrix, logging which side sources (FNB58 direction) and whether the pack charges, 10 plug cycles each:
  - Anker 737 to receiver USB-C (through the TPS259470A).
  - Anker 737 to ISDT 608PD USB-C.
  - Phone to receiver: must never drain the pack.
  - Back-feed, main switch OFF:
  - Apply 5.1 V, current-limited to 50 mA, to LAB5. The SW node must stay below 17 V.
  - Plug the Pico USB into a PC, then the IMU-pack USB. LAB5 must stay below 0.5 V and the SW node near 0 V.
  - Q6A poweroff: after 'systemctl poweroff', log J21 current with the INA228 for 2 min, record whether the header 3.3 V falls, and confirm the Pico opens #2813. Repeat after every rsetup/SPI update. A cold power-on must reach the login with no keyboard.
  - D36V50F12 backup EN (10.0k/1.00k): sweep SW from 14 V down to 11 V and back with a bench supply. Record sleep and wake (targets about 12.1 / 13.6 V). v2.1: with 4.99k/562 Ohm sweep down to 10.5 V; accept wake at most 13.30 V, sleep 10.9-12.0 V.
  - TLV3012 supervisor:
  - Sweep N from 14.0 V to 12.0 V and back; record trip and release (targets 12.8 / 13.6 V).
  - With OFF held high, press the button on A: the switch must stay off.
  - 20 PD plug/unplug cycles with the device OFF and ON: the #2813 state never changes spontaneously.
  - C4 gate (2) for the Lime default: 60 min at 4.2 A in the closed enclosure at 14.0 and 16.4 V input. Log D36V50F12, #2813 MOSFET and 7.5 A fuse temperatures. Also run 4.6 A at the pack for 30 min at 50 C ambient.
  - C4 gate (1): HF+ narrowband A/B with SYS12 and LAB5 load steps 0.3-3 A and charger on/off. No line 3 dB or more above the floor within +/-5 kHz of 40, 60, 77.5, 162, 490, 518 or 4209.5 kHz. Repeat with the LM61460 if it fails.
  - Standby at 14.8 V with the main switch off:
  - Total current with the INA228 continuous: target 1.0 mA or less.
  - With the INA228 shutdown: target 0.25 mA or less, excluding the BMS.
  - Daly quiescent current separately (spec <500 uA).
  - Daly behaviour:
  - UVP wake with the IP2368 trickle (100-200 mA), 3/3.
  - Short-circuit trip release with the AON load (about 1 mA) present.
  - OVP point during the 4.20 V ISDT balance.
  - INA228 calibration:
  - Compare against an FNB58 or bench DMM plus shunt at 0.5, 2 and 4 A, and set SHUNT_CAL.
  - Confirm the address (0x45 or 0x40) stays stable over 10^5 reads.
  - i2cdetect shows the address, not UU.
  - TPS7A4701 rails:
  - 13.2 V and 12.5 V at the F/bias-tee connector, at battery 14.2 and 16.4 V: within +/-0.35 V.
  - Output at battery 13.2 V (dropout).
  - Bullseye current: size the PTC at 1.5-2x at 60 C and fix the heat-sink attachment.
  - Boni-Whip current.
  - Rail-good comparators trip at about 90%.
  - LT3045 rail: 500 kHz ripple and spurs on the 4.5 V LNA rail with LAB5 trimmed to 4.8 V, at 0.17 and 0.6 A load. v2.1: the rail is 4.30 V (RSET 21.5k); also measure V(E2_LNA_IN)-V(OUTS) of at least 0.40 V at 3.2 A LAB5 / 1 A pair / 50 C.
  - Fuse heat: 7.5 A fuse at 4.6 A and LAB5 3 A fuse at 2.3 A, 30 min each in a 50 C enclosure. Measure the fuse-holder temperature rise.
  - Cells: capacity at 1 A to 2.5 V (at least 4.85 Ah), mass 68-71 g, 1 kHz AC IR. Cold-soaked pack at 0 C: log a mode-H run with the INA228 to replace the 50 Wh cold model.
  - Display and Q6A brown-out: SYS12 at 11.0 V (display stable) and at 11.5 V (Q6A stable), with J21 fed through the TPS259470A.
- **Confidence:** medium

_Run `wf_f924b2ab-5ad`_

- **Component:** Power system (battery, charging, 12 V rail, power switch, fuel gauge) for the Radxa Dragon Q6A handheld satellite receiver
- **Recommendation holds:** так
- **Issues:**
  1.
    - **Claim:** Researcher: never feed raw 4S into J21 because 16.8 V exceeds the SMBJ15CA 15 V TVS standoff.
    - **Problem:** Wrong reason. I read schematic v1.21, sheet DC-IN. The SMBJ15CA (D19) sits on the USB-C VBUS side, before the back-to-back DMP2160 switch (Q5). The J21 header path has no TVS and no reverse-polarity protection. Only C602 (10 uF/25 V) and C611/C612 (22 uF/16 V) sit in front of the SY81012.
    - **Correction:** The conclusion still holds: no raw 4S. The real limits are the 16 V input capacitors and the SY81012, and Radxa staff state 4.5-16 V (Oct 15, 2026). The builder must add their own fuse, reverse protection, TVS and bulk capacitor in front of J21.
    - **Source:** https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf (sheet DC-IN); https://forum.radxa.com/t/radxa-q6a-4s1p-powering/31611
  2.
    - **Claim:** Fixes agent: the Q6A's SY7120 5 V boost can deliver about 7 A (~35 W), so there is plenty of headroom for the LimeSDR.
    - **Problem:** This ignores the stage before the boost. VPH_PWR reaches VPH_PERI through an SGM40666 OVP switch (U28), which SG Micro rates at 4.5 A continuous.
    - **Correction:** VCC_5V_PERI is good for roughly 4.2 V x 4.5 A x 0.92 = ~17 W (~3.5 A at 5 V); this is my calculation. That budget is shared by the M.2 3.3 V buck (LimeSDR up to 8.25 W), VCC_3V3, VCC_1V8, all USB ports, the 40-pin 5 V and the fan. It is still enough for Lime + RTL + fan + GNSS/IMU, but no display backlight or other big load may hang off Q6A USB or 40-pin 5 V.
    - **Source:** https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf (U28 SGM40666AS, U24 SY7120); https://sg-micro.com/product/SGM40666A
  3.
    - **Claim:** Researcher: peak load ~35-37 W at the battery, sunlight display 5-10 W.
    - **Problem:** A 1000-2200 nit 7-inch panel draws more. The FeelWorld LUT7 (2200 nit, 7-24 V input) is rated 20 W.
    - **Correction:** Re-budget at the pack:
  - Typical (Lime + SatDump + display ~60%): ~25-28 W.
  - Peak (Lime, NPU, display 100%, LNB): ~45-52 W, about 4 A at 13 V.
  - Size the fuse at 7.5 A and the master switch for at least 6 A.
    - **Source:** https://www.adorama.com/felut7.html ; https://www.bhphotovideo.com/c/product/1531472-REG/feelworld_lut7_7_touch_screen.html
  4.
    - **Claim:** Researcher: IP2368 supports 2-6S.
    - **Problem:** IP2368 datasheet V1.41 says 2-5 cells. Its changelog states that 6S support was dropped (Nov 2023). Prom.ua listings still advertise 2-6S.
    - **Correction:** 4S is supported, so the stock strap R7 = 13 kOhm is fine. Do not rely on 6S.
    - **Source:** IP2368 datasheet V1.41: https://datasheet.lcsc.com/datasheet/pdf/752f0c4a0b5b0a79a7f68752c4eac200.pdf?productCode=C5203723
  5.
    - **Claim:** Researcher: the IP23xx USB-C port doubles as a reverse power bank for phones and radios, and charges from any power bank.
    - **Problem:** Per the datasheet, the standard IP2368_BZ is charge-only. Only the COUT/NACT variants discharge, and they implement DRP Try.SRC: when connected to another DRP device they preferentially SOURCE power to it. Most modern power banks have bidirectional C ports, so the handheld may charge the bank instead of itself, or flip direction. A seller listing warns never to join two bidirectional C ports, and a mikrocontroller.net report describes wrong-direction behaviour.
    - **Correction:** Prefer a charge-only (BZ) IP2368 board.
  - If you buy a bidirectional COUT/NACT board, charge from output-only C ports (power stations, PD wall/car chargers, PD solar) or from a power bank's USB-A port with an A-to-C cable (15-18 W).
  - Test every power bank you plan to use.
  - Drop 'reverse power bank' as a design goal.
    - **Source:** IP2368 datasheet V1.41 sections 6 and 12.2; https://www.walmart.com/ip/5799421375 ; https://www.mikrocontroller.net/topic/569785
  6.
    - **Claim:** Researcher wiring: BMS -> fuse -> master switch -> INA228 shunt -> loads, with the IP23xx BAT on the battery side of the shunt.
    - **Problem:** With this wiring the shunt never sees charge current. And if the master switch sits before the IP23xx tap, the pack cannot charge while the device is off.
    - **Correction:** Pack+ -> 7.5 A fuse -> INA228 shunt -> node N.
  - Node N feeds IP2368 BAT+ permanently.
  - Node N also feeds the master switch, then the loads.
  - Power the INA228 from an always-on 3.3 V LDO so its 40-bit CHARGE accumulator keeps counting while the Q6A is off. Remove the breakout's pull-ups to avoid back-feeding the unpowered Q6A I2C pins.
  - Otherwise, re-initialise state of charge from rested OCV at boot.
    - **Source:** https://www.ti.com/product/INA228 ; https://www.adafruit.com/product/5832
  7.
    - **Claim:** Fixes agent: Pololu #2812 Big Pushbutton Power Switch MP handles about 8 A.
    - **Problem:** Pololu gives 8 A only at a 150 C MOSFET temperature. At 55 C it is about 4 A, which is marginal for the ~4 A peak pack current.
    - **Correction:** Use the Pololu #2813 HP instead: $8.95, 4.5-40 V, 6 A at 55 C, <0.2 uA off, reverse protection.
    - **Source:** https://www.pololu.com/product/2812 ; https://www.pololu.com/product/2813
  8.
    - **Claim:** Stack/researcher: LimeSDR Micro M.2 costs $199 and deliveries start ~Sept 30, 2026.
    - **Problem:** Crowd Supply now lists the M.2 2280 Basic at $249 ($18 worldwide shipping) and the GNSS version at $299. New orders ship Dec 15, 2026.
    - **Correction:** Budget $267 delivered. Real Q6A + Lime power measurements cannot happen before ~late Dec 2026.
    - **Source:** https://www.crowdsupply.com/lime-micro/limesdr-micro
  9.
    - **Claim:** Researcher budget option: a single LTC3780 module supplies both the Q6A and the LNB.
    - **Problem:** Community reports describe AliExpress LTC3780 boards as 'staggeringly noisy' and their output as collapsing under ~48 W loads. That is the worst choice next to an SDR front-end.
    - **Correction:** Use a quality 12 V buck: Pololu D36V50F12 (verified $39.95; 13.3-50 V in; 12 V +/-4%; ~4.5 A typ; ~500 kHz; precise EN thresholds; stock marked 'Rationed'). On a budget, drop the converter entirely and run 3S straight into J21 (see the budget option).
    - **Source:** https://www.pololu.com/product/4095 ; https://community.element14.com/challenges-projects/project14/portable-electronics-kit/f/forum/39004/ltc3780-buck-boost-converter
  10.
    - **Claim:** Researcher: IP2368 board ~$5-10, P50B cells ~$28-40 for four, Ukrainian availability unverified.
    - **Problem:** Prices are now checked on Prom.ua (Oct 2026):
  - IP2368 bidirectional boards: 600-700 UAH (~$14-17); the bare chip is 231 UAH.
  - Molicel P50B single cells: 219-380 UAH (~$5-9). One 155 UAH listing is suspiciously cheap, and a BudgetLightForum report describes a used or fake P50B.
  - P60B (6 Ah, announced June 2025): no retail listings in Ukraine.
    - **Correction:** Four P50B cost ~$25-36 locally; buy from established sellers and test capacity and IR. The IP2368 board costs ~$14-17 in Ukraine, or less on AliExpress (unverified).
    - **Source:** https://prom.ua/ua/search?search_term=IP2368 ; https://prom.ua/ua/search?search_term=Molicel%20P50B ; https://budgetlightforum.com/t/fake-or-damaged-molicell-p50b/230574
  11.
    - **Claim:** Fixes agent: glue a blank plug into the Q6A USB-C port.
    - **Problem:** Back-feed is real: VBUS from any source turns on Q5 and parallels it with the header rail. But per Radxa docs EDL flashing uses the USB-A port, so USB-C is power-only and is handy for bench power when the pack is disconnected.
    - **Correction:** Use a removable silicone dust plug and a warning label instead of glue. Never plug anything into it while J21 is powered.
    - **Source:** https://docs.radxa.com/en/dragon/q6a/low-level-dev/edl-mode ; https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
- **Forum and fix assessment:** VERDICT: The community findings are accurate. I re-checked them against primary sources:
  - Radxa staff, via the Discourse JSON: strongtz gives 4.5-16 V (Jan and Oct 2026); BigfootACA gives 3.6-16 V and says not to use USB-C while the header is powered.
  - willy measured 1.9-2.5 W after 'halt'.
  - The UEFI 'PwrKey press 75 ms ... expected 400 ms' log line exists in that thread.
  - Geerling measured 2.9 W idle, 9.3 W stress-ng and 10.1 W HPL.
  - Lime staff say the Micro M.2 draws ~4 W.
  
  The fixes are mostly sound. I verified their datasheet numbers directly:
  - IP2368 V1.41:
    - VTRGT = 4000 + 0.02 x RVSET (5.1k = 4.10 V; minimum 4.1 V/cell).
    - ISET_MODE to GND with RISET 15k gives 3 A; input-power mode is 4 W per kOhm.
    - ISTOP 100 mA, charge timer TEND 45-51 h, standby 180 uA at 14.8 V, 250 kHz.
    - NTC trips at 0.39 V with 80 uA (hot) and 0.55 V with 20 uA (cold), designed for a 10k B3380.
  - Software support:
    - The radxa-overlays i2c6 overlay exists.
    - Radxa kernel 7.0.11-7 ships ina238.ko, which supports the INA228.
  - Pololu D36V50F12 and #2812 specs and prices match.
  
  Corrections to the fixes:
  1. The Q6A 5 V_PERI headroom is ~17 W, not 35 W, because of the SGM40666 4.5 A switch upstream of the boost.
  2. The #2812 is only ~4 A at 55 C; use the #2813 HP.
  3. Power the INA228 from an always-on rail, or charge done while the device is off goes uncounted.
  4. The IP2368 COUT/NACT Try.SRC behaviour conflicts with 'charge from power banks'. This is the biggest practical gap. Choose a charge-only board, or charge from one-way ports.
  5. 3S-direct needs real hot-plug protection: ringing can approach 2 x 12.6 V, above the SY81012's 18 V absolute maximum, so a soft switch, a bulk electrolytic and a TVS are mandatory.
  
  The researcher's architecture (4S, regulated feed into the J21 header, IP23xx USB-C charger, separate balancing BMS, INA228) holds. Its weak parts were:
  - the LTC3780 regulator;
  - the shunt placement;
  - the TVS reasoning;
  - the display power estimate;
  - the 'reverse power bank' double-duty.
- **Final recommendation:**
  - **Name:** 4S1P Molicel P50B (72 Wh) + IP2368 USB-C PD charger (charge-only BZ preferred, set to 4.10 V/cell and 3 A, real NTC) + Pololu D36V50F12 12 V buck into Q6A J21 + Pololu #2813 HP switch + Adafruit INA228 gauge on an always-on supply
  - **Price:** About $125-160 before shipping:
  - 4x P50B: ~$25-36 (219-380 UAH each on Prom.ua).
  - 4S common-port balancing BMS, 15-20 A: $5-12 (unverified).
  - IP2368 board: $14-17 on Prom.ua (cheaper on AliExpress, unverified).
  - Pololu D36V50F12: $39.95.
  - Pololu #2813: $8.95.
  - Adafruit INA228: $14.95.
  - LT3045 LNA LDO module: $5-10 (unverified).
  - 10k B3380 NTC, 7.5 A fuse, XT30, nickel strip, ferrites, pi-filter parts, SMBJ14A, 220 uF: ~$10-15.
  - Optional ISDT 608PD backup balance charger: ~1,979-2,250 UAH (~$47-54).
  - **Why:** WIRING:
  - Pack+ -> 7.5 A fuse -> INA228 shunt -> node N.
  - Node N -> IP2368 BAT+ (always connected, so the pack charges while the device is off).
  - Node N -> #2813 switch -> D36V50F12 (EN divider as a ~12.8 V hardware cutoff) -> pi-filter -> J21 pins 1/2. A GPIO-switched, polyfused branch feeds an LNB if one is used.
  - A 7-24 V sunlight display is fed straight from the switched pack node; a 5 V panel gets its own filtered 5 V buck.
  - J21 pin 3 goes to a case button or an MCU press pulse.
  
  WHY:
  - The 4S range never violates the 16 V header limit once regulated. At 4S the battery current stays at about 4 A or less even at a ~50 W peak, and the 12 V rail also suits an LNB (11.5-14 V).
  - There is no USB-PD dependency for the Q6A, so a charger plug or unplug never glitches it.
  - Runtime with a 72 Wh pack: ~2.3-2.6 h typical (Lime 56 MHz, bright display), ~5 h light (RTL-SDR, dim display), ~1.3 h worst case. Carry a second XT30 pack for long sessions.
  - **Sources:**
    - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
    - https://forum.radxa.com/t/radxa-q6a-4s1p-powering/31611
    - https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
    - https://github.com/geerlingguy/sbc-reviews/issues/85
    - https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
    - https://datasheet.lcsc.com/datasheet/pdf/752f0c4a0b5b0a79a7f68752c4eac200.pdf?productCode=C5203723
    - https://www.pololu.com/product/4095
    - https://www.pololu.com/product/2813
    - https://www.adafruit.com/product/5832
    - https://docs.kernel.org/hwmon/ina238.html
    - https://www.molicel.com/inr-21700-p50b/
    - https://prom.ua/ua/search?search_term=Molicel%20P50B
    - https://prom.ua/ua/search?search_term=IP2368
    - https://www.adorama.com/felut7.html
- **Final budget option:**
  - **Name:** 3S1P Molicel P50B pack (54 Wh) wired straight into Q6A J21, with no external 12 V converter
  - **Price:** About $55-75:
  - 3x P50B: ~$18-27.
  - Daly 3S 20 A common-port BMS: 407 UAH (~$10) on Prom.ua.
  - IP2368 board: ~$14-17 on Prom.ua (cheaper on AliExpress, unverified).
  - Pololu #2813: $8.95.
  - INA226 module: $2-4 (unverified).
  - TVS, capacitor, fuse, XT30, nickel strip: ~$5-8.
  - Optional 13 V boost for an LNB: ~$3-10 (unverified).
  - **Why:** PARTS AND WIRING:
  - Pack: 3S1P P50B (9.0-12.3 V).
  - BMS: Daly 3S 20 A common-port BMS, with balancing.
  - Charging: IP2368 strapped for 3S (RBAT_NUM 9.1k) at 4.10 V/cell, with a real NTC.
  - Main path: fuse -> INA226 module (R010 shunt fitted) -> Pololu #2813 switch -> 220 uF/25 V electrolytic + SMBJ14A TVS -> J21 directly.
  - Display (7-24 V type) and LNAs (via LDO) run from the same node.
  
  WHY:
  - The whole pack range sits inside the staff-stated 4.5-16 V window and the SY81012's 2.7-16 V rating, so there is no external switching converter. That makes it the quietest and cheapest option, with the fewest failure points.
  - Trade-offs:
    - 25% less energy (~1.8-2 h typical, ~4 h light).
    - J21 carries up to ~2.5 A.
    - An LNB (11.5-14 V) needs its own small switched boost converter.
    - Radxa docs still say '12 V' and no public long-term 3S bench test exists, so do the 6-14 V sweep first.
  - It beats the researcher's LTC3780 budget path, which has poor noise and stability reports.
- **Known problems and fixes to apply:**
  - Never put raw 4S on J21. The header path has no TVS and no reverse protection, only 16 V capacitors and the SY81012. Feed it a regulated 12 V, or 3S, behind a fuse, reverse protection (#2813), an SMBJ14A TVS and a 100-220 uF/25 V electrolytic. Use a keyed, latched 3-pin housing.
  - Q6A USB-C back-feed: VBUS from any source switches Q5 on and parallels it with J21. Cover the port with a removable plug and a label. Make the IP2368 port the only charging input.
  - The Q6A draws 1.9-2.5 W after 'halt'. Use poweroff (HandlePowerKey=poweroff), and put the #2813 hard switch after the IP2368 tap so the pack still charges while the device is off.
  - Auto-boot from J21 is inconsistent (the UEFI log wants a press of at least 400 ms). Update the SPI firmware. Add an open-drain 0.5-1.5 s pulse on J21 pin 3, sent by an MCU or a second case button, and only when 40-pin 3.3 V is absent.
  - Low-battery handling:
  - Linux powers off at ~3.4 V/cell (13.6 V), read from the INA228.
  - Hardware cut via the D36V50F12 EN divider at ~12.8 V.
  - The BMS cutoff (2.5-2.8 V/cell) is the last resort only. This avoids BMS lock-out and regulator oscillation (Pololu forum case).
  - IP2368 board heat (MOSFET over 100 C at 5 A): set RISET to 15k (3 A), thermal-pad the board to the case, keep it 10 mm or more from the cells, and fit a 70 C KSD9700 or similar. Buy 2-3 boards and burn each in for 2 h at 3 A.
  - The IP2368 ships with a fixed 10k resistor in place of the NTC. Fit a 10k B3380 NTC on the middle cell (charging stops below 0 C and above 45 C). Never charge a pack below 0 C; let the receiver warm it for 15-20 min first.
  - Use-while-charging: with any load over 100 mA the IP2368 never terminates and floats in CV until the 45-51 h timer. Set 4.10 V/cell (RVSET 5.1k). Optionally add the NTC-pull charge inhibit, then bench-verify it and its effect on the timer. Do a 4.20 V balance charge monthly (ISDT 608PD via the balance lead), because cheap BMS boards barely balance at 4.10 V.
  - IP2368 COUT/NACT boards use Try.SRC and may push power INTO bidirectional power banks. Prefer a charge-only (BZ) board. Otherwise charge from output-only PD ports or a USB-A port with an A-to-C cable, and test each power bank. For use while charging, a source of 45-65 W or more is needed: a 20 W bank cannot keep up with a 25 W load.
  - Some IP2368 boards need a USB-C 'kick' after the battery is connected or after a protection trip; NACT variants do not. Some BMS boards ship locked. Recover both by plugging in the PD charger; confirm this works 3 out of 3 times.
  - Q6A internal 5 V_PERI is limited to about 17 W by the SGM40666 (4.5 A). Keep only the LimeSDR, RTL-SDR, fan, GNSS and IMU on it. Power the display from the pack or the 12 V rail, never from a Q6A USB port.
  - LimeSDR through the 2230-to-2280 extender: measure at least 3.20 V at the card under a 61.44 Msps + CPU + NPU load. Heatsink the card and design for 10 W.
  - Fuel gauge:
  - Use INA228 coulomb counting, not voltage-based percentage, which forum reports show is off by 20-90%.
  - Put the shunt in the pack lead.
  - Set shunt-resistor = <15000> in the overlay.
  - Power the INA228 from an always-on LDO so off-state charging is counted, or re-sync from rested OCV at boot.
  - Reset to 100% at 16.35 V with current under 0.1 A.
  - EMI: the IP2368 switches at 250 kHz, the D36V50F12 at ~500 kHz (power-save mode at light load), and the Q6A SY81012/SY7120 at ~1 MHz (the SY7120 runs PFM at light load because MODE is pulled low). Use pi-filters, a shielded corner, Mix-31 ferrites and an LT3045 for the LNAs. Run A/B noise-floor sweeps at 137, 145.8, 435-438, 1698-1707 and 2200-2290 MHz with each source on and off.
  - Before blaming the power system for reboots, rule out the Kioxia UFS bug (needs a kernel with the PA_TACTIVATE quirk, Armbian 26.05+) and disable auto-suspend.
  - Counterfeit cells: avoid outlier-cheap listings (e.g. 155 UAH 'P50B'). Check the wrap and terminals, and test capacity and IR before spot-welding.
- **Missed better options:**
  - Feed a 7-24 V-input sunlight display (field-monitor style; LUT7 is 7-24 V, 20 W) directly from the switched 4S pack node. This removes the 5 V display buck and keeps 8-20 W off both the 12 V converter and the Q6A's internal 5 V.
  - Use the D36V50F12 EN pin (precise 1.2/1.35 V thresholds) with a resistor divider as a hardware low-voltage cutoff. This removes the need for an MCU for the last-resort cut.
  - Pololu #2813 HP ($8.95, 6 A at 55 C) instead of the #2812 MP as the master switch: it gives reverse protection, near-zero off current and an OFF input in one part.
  - 3S1P direct into J21 with no external converter (Radxa staff: 4.5-16 V). This is the quietest and cheapest path if 54 Wh is enough.
  - ISDT 608PD (USB-C PD 5-28 V/140 W input, 0.8 A/cell balancing, ~1,979-2,250 UAH on Prom.ua) as a backup charger and monthly balancer through the XT30 and balance lead. It also charges from power stations and power banks.
  - Molicel P60B (6 Ah, announced June 2025) would give a 86 Wh 4S1P pack, but there are no retail listings in Ukraine, so it is not a practical option yet.
- **Remaining uncertainties:**
  - Measured Q6A + LimeSDR + NPU + sunlight-display draw: all runtime figures are estimates until the INA228 logs exist, and the Lime only ships from Dec 15, 2026.
  - Whether charge-only IP2368_BZ boards are easy to find (most listings are bidirectional), and real AliExpress prices and quality of IP2368 and BMS boards.
  - Whether the NTC-pull charge inhibit stops the IP2368 cleanly, and how it interacts with the 45-51 h charge timer.
  - The D36V50F12's continuous current at 13-17 V input in a closed case, and the spur behaviour of its light-load power-save mode near the SDR bands.
  - 3S-direct: there is no public long-term bench test at 9-12.6 V. Hot-plug overshoot and J21 pin heating at ~2.5 A must be measured.
  - Bullseye LNB current (budget 200-300 mA), and whether an LNB is used at all now that dishes are abandoned.
  - J21 connector current rating (not published; the header was designed for Radxa's PoE HAT).
  - Whether the ina238 hwmon driver resets the INA228 accumulators on probe (affects off-state charge counting).
  - The UAH/USD rate in October 2026 (~42 assumed).
- **Confidence:** medium

_Агент цього етапу ще працює (run `wf_f924b2ab-5ad`)._

