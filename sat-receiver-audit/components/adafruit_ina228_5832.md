# Adafruit ina228 5832: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** Pack-lead charge counter / power monitor (C14): Adafruit INA228 #5832 (TI INA228, 20-bit, 85 V, 15 mOhm shunt), high-side between the 7.5 A blade fuse and node N, VS from AON 3.3 V, I2C0 via user-space i2c-dev (labpowerd), ALERT on header pin 3
- **Current pick:** Adafruit INA228 #5832
- **Current price usd:** 14.95 (adafruit.com, qty 1, in stock, re-verified 18 Oct 2026; $13.46 at 10-99). EU: DigiKey DE 1528-5832-ND EUR 13.13 excl. VAT / EUR 15.62 incl. 19% VAT, 1,177 in stock. Free shipping only from EUR 75; below that DigiKey DE charges EUR 25.
- **Decision:** keep
- **Chosen:** Adafruit INA228 #5832 (unchanged). Buy it in the planned Adafruit order, or for an EU landed price add it to a DigiKey EU order that is already above EUR 75.
- **Chosen price usd:** 14.95
- **Saving usd:** 0 now. A rev-2 DIY of the same silicon could save about $8.9 per unit (see conditions_or_tests), but it cannot be bought today.
- **Equivalence proof:** No candidate cheaper than $14.95 survived as not-worse, so the current part stays.
  
  What the stack needs from this part, checked against TI's INA228 page on 18 Oct 2026:
  - Hardware 40-bit CHARGE and ENERGY accumulators. They count while the Q6A is off and the IP2368 is charging, and software integration cannot do that.
  - 20-bit ADC: 312.5 nV/LSB, about 20.8 uA/LSB at 15 mOhm. The 0.7 mA AON standby current is about 34 LSB.
  - Offset max +/-1 uV (about +/-67 uA), offset drift 0.01 uV/C, gain error +/-0.05%, gain drift 20 ppm/C, CMRR 154 dB.
  - Accuracy: power 0.5% FS, energy and charge 1.0% FS.
  - Common mode -0.3 to 85 V (the pack is 13.2-16.8 V; SMBJ17A transients reach about 27 V).
  - Iq 640 uA typ / 1.1 mA max; shutdown 5 uA max.
  - I2C with ALERT, and the labpowerd register map (SHUNT_CAL, SHUNT_TEMPCO, CHARGE, ENERGY, DIAG_ALRT).
  - Full scale +/-10.92 A, covering the 4.6 A peak and the 7.5 A fuse.
  
  Every cheaper alternative fails at least one of these:
  - Adafruit INA238 ($10.95), per TI: 16-bit, offset +/-5 uV, gain error +/-0.1%, no energy or charge registers.
  - Adafruit INA237 ($9.95), per TI: offset +/-50 uV, gain error +/-0.3%, no energy or charge registers.
  - INA260 ($9.95): 36 V, 1.25 mA LSB, no accumulators.
  - INA219: 3.2 A maximum, below the 4.6 A peak.
  - INA226 modules: 16-bit, no accumulators.
  - TI INA700 (has charge and energy): offset +/-1.5 mA max, more than twice the 0.7 mA standby current. Also 40 V and a WCSP package, with no board found.
  
  The only cheaper part with identical silicon is a DIY build: INA228AIDGSR ($5.31) plus a Bourns CRA2512-FZ-R015ELF shunt (15 mOhm, 1%, 3 W, +/-50 ppm/C, $0.59, 56k in stock), about $6.0 in parts.
  - It is equal on every converter spec.
  - It is not available. DigiKey shows 0 in stock, with restock 04 and 07 Jan 2027 and a 20-week lead time. The TI store shows out of stock. TME shows 0 and marks it "hardly available". Mouser and Farnell returned 503 and LCSC blocked access, so no authorised stock could be confirmed.
  - Its build quality is unproven: a 0.5 mm VSSOP-10 with a Kelvin layout on the 2-layer power PCB, not yet built or tested.
  - It cannot make the W1-2 energy gate (19 Oct - 1 Nov 2026), which needs INA228 logs.
  - It therefore fails 'legally obtainable now, same or better build quality' and is not a replacement for v1.
  
  The other routes cost more or have no traceable provenance:
  - Same SKU from other sellers: Kiwi EUR 14.29 excl. VAT, Botland EUR 20.14 (B2B only), The Pi Hut GBP 14.40.
  - MikroE Power Monitor Click: $24.69, 0 in stock.
  - SparkFun INA228 Qwiic: $14.95, the same price.
  - AliExpress '5832' clones: no provenance, and priced below the single-IC distributor price while authorised stock is zero.
  
  Nothing is traded away. The current part, its rails, interfaces and software stay as they are.
- **Rejected:**
  1.
    - **Name:** DIY: TI INA228AIDGSR + Bourns CRA2512-FZ-R015ELF on the custom 2-layer power PCB (about $6.0 in parts)
    - **Why:** Same silicon, so it is equal on paper, but it cannot be bought now. DigiKey: 0 in stock (cut tape $5.31), 1,178 due 04 Jan 2027 and 1,322 due 07 Jan 2027, 20-week lead time. TI store: out of stock. TME: 0, 'hardly available'. Mouser and Farnell returned 503 and LCSC refused access, so no authorised stock was found. It misses the W1-2 INA228 energy gate that starts 19 Oct 2026. Build quality is unproven until a calibrated bench test (0.5 mm VSSOP-10 and Kelvin layout on a 2-layer board, versus a factory-assembled board). The shunt is 1% / +/-50 ppm/C (DigiKey verified). Adafruit's product text claims 0.1% but its Eagle schematic gives R1 = HoLLR2512-2W-15mR-1% (checked in the .sch file this run), so the tolerance is only equal if the fitted part really is 1%. A 0.5% Vishay WSL2512R0150DEA is $1.06 but rated only 1 W (TCR not listed). Shipping: DigiKey DE charges EUR 25 under EUR 75, so the saving is real only when bundled. Not a v1 replacement; a candidate for rev 2.
  2.
    - **Name:** DIY variant: INA228AQDGSRQ1 (AEC-Q100) + CRA2512-FZ-R015ELF (about $7.4)
    - **Why:** Same availability problem: 0 at DigiKey, 2,500 due 21 Jan 2027. Electrical parity of the -Q1 datasheet tables was not verified. Rejected for v1.
  3.
    - **Name:** Adafruit INA238 #6349 ($10.95)
    - **Why:** TI page verified: 16-bit (about 333 uA/LSB at 15 mOhm, so the 0.7 mA standby current is about 2 LSB), offset +/-5 uV max (5x worse), gain error +/-0.1% max (2x worse), and no ENERGY/CHARGE accumulation. It cannot count charge while the Q6A is off or charging. Its 2.73 A low range is below the 4.6 A peak. Fails the not-worse rule.
  4.
    - **Name:** Adafruit INA237 #6340 ($9.95)
    - **Why:** TI page verified: 16-bit, offset +/-50 uV max (50x worse), gain error +/-0.3% max (6x worse), power accuracy +/-1.6% FS in the features list (the table says 0.6%; the page conflicts), and no energy or charge accumulation. Fails.
  5.
    - **Name:** Adafruit INA260 #4226 ($9.95; Berrybase EUR 10.95, unavailable)
    - **Why:** 36 V bus maximum (85 V on the current part), 16-bit, about 1.25 mA LSB (the 0.7 mA standby current is below 1 LSB), no accumulators, a different register map, so labpowerd would need a rewrite. Fails.
  6.
    - **Name:** Adafruit INA219 #904 / Soldered INA219 Qwiic (EUR 10.70 / EUR 7.20 incl. VAT)
    - **Why:** 3.2 A maximum with its 0.1 Ohm shunt, below the 4.6 A peak; 26 V; 12-bit; no accumulators. Fails.
  7.
    - **Name:** Generic INA226 modules (CJMCU-226, about $1.1) / M5Stack INA226-10A (GBP 8.20 incl. VAT)
    - **Why:** 16-bit, no CHARGE/ENERGY, 36 V; offset and gain worse per the search (figures from memory, not re-fetched). Different register map. Clone shunts are unknown. Fails.
  8.
    - **Name:** TI INA700 (EZShunt, has energy/charge)
    - **Why:** TI page verified: 40 V, 16-bit, offset current +/-1.5 mA max in the features (+/-2 mA in the table) versus about +/-67 uA, so it cannot resolve the 0.7 mA standby current; gain error +/-0.5% max at 5 A. PowerWCSP-8 package; no breakout found. Fails.
  9.
    - **Name:** MikroE Power Monitor Click MIKROE-4810 (INA228)
    - **Why:** $24.69 at TME (net or gross not stated), 0 in stock. Shunt and current rating unverified (the MikroE page returned 403). The mikroBUS board is larger. More expensive.
  10.
    - **Name:** SparkFun SEN-31438 INA228 Qwiic
    - **Why:** $14.95 per the search, the same price, so it is not cheaper. Its page reportedly contradicts itself on the shunt (15 vs 10 mOhm). My fetch of sparkfun.com/products/31438 returned 404, so the listing is unverified.
  11.
    - **Name:** Same SKU from Kiwi Electronics (NL), Botland (PL), The Pi Hut (UK)
    - **Why:** Kiwi EUR 14.29 excl. VAT with 1 in stock; Botland EUR 20.14 incl. VAT, businesses only; Pi Hut GBP 14.40 incl. VAT. All are dearer than $14.95 in USD base (from the searches, not re-fetched).
  12.
    - **Name:** Same SKU from DigiKey EU (1528-5832-ND)
    - **Why:** Not a different part, only a sourcing route. EUR 13.13 excl. / EUR 15.62 incl. VAT (verified), about parity with $14.95. A EUR 25 shipping charge applies below EUR 75, so it pays only when bundled into a larger DigiKey EU order.
  13.
    - **Name:** AliExpress '5832 INA228' clones (items 3256809060132764, 3256809762166296, etc.) and multi-variant INA228/237/238 modules
    - **Why:** Item pages could not be read; $1-3.4 search-page prices are unverified. The price is below DigiKey's $5.31 single-IC price while authorised stock is zero, which is a strong counterfeit or remark indicator (inference). Chip marking and the shunt part, tolerance and TCR are unknown, and there are no measurements. Fails the legal / not-counterfeit / proven rule.
  14.
    - **Name:** Used Adafruit #5832 (eBay etc.)
    - **Why:** No listing found in this run; per-unit history is unknown, and any saving on a $15 board disappears after shipping.
- **Confidence:** high
- **Conditions or tests:** Board preparation and bench gates (from reaudit_D), unchanged by this decision:
  - Remove R7 (LED, 10k, about 0.12 mA).
  - Remove R6. It is one 4 x 10k pack holding the SDA/SCL pull-ups and the ADDR0/ADDR1 pull-downs, so removing it floats A0/A1.
  - Strap the address: close A0 and A1 for 0x45, or wire ADDR to GND for 0x40. Set labpowerd to match.
  - Close SJ1 for high-side sensing.
  - Pull ALERT up to the Q6A 3.3 V rail, never to AON.
  - Run in continuous mode (ENERGY and CHARGE are invalid in triggered mode).
  - Calibrate SHUNT_CAL against a reference at 0.5, 2 and 4 A. Treat the shunt as 1%, as the Eagle BOM says.
  - Do 10^5 reads to confirm a stable address.
  - Standby at 14.8 V: 1.0 mA or less with the INA228 running, 0.25 mA or less with it in shutdown (excluding the BMS).
  
  Possible future replacement (power PCB rev 2 only; not part of this decision): an on-board INA228AIDGSR plus a 15 mOhm 2512 shunt, about $6.0 in parts, saving about $8.9. All of these must hold:
  - Stock bought from an authorised TI channel with traceability (TI store, DigiKey, Mouser, Farnell, Arrow), never AliExpress or the grey market.
  - The PCB follows TI layout guidance with Kelvin sense traces, ADDR hard-tied to GND (0x40) and ALERT pulled up to Q6A 3.3 V; no series input resistors above about 10 Ohm.
  - The shunt is rated at least 2 W with a published TCR, for example the CRA2512-FZ-R015ELF (3 W, +/-50 ppm/C). Prefer a 0.1%-0.5% part if one with at least 2 W is found; otherwise 1% plus SHUNT_CAL, which is the same treatment the current part needs.
  - Professional or stencil assembly.
  - It passes the same SHUNT_CAL gate: charge error within 1% FS against the reference at 0.5, 2 and 4 A, plus the 10^5-read address test and the standby tests above.
  - The parts are bundled into a DigiKey EU order of EUR 75 or more, so the EUR 25 shipping does not cancel the saving.
  - The Adafruit #5832 stays as the v1 part and as the fallback.
- **Stack changes:** No changes to rails, connectors, drivers or the case. The part stays: AON 3.3 V VS, I2C0, ALERT on pin 3, labpowerd over i2c-dev, ina238 hwmon blacklisted. Three text corrections should go into STACK.md:
  - C14 and the BOM row say 'pull-ups removed, 0x40'. Removing R6 also removes the ADDR pull-downs, so the address must be strapped (0x45 with A0+A1 closed, or ADDR to GND for 0x40), and the pin-13/15 table must match.
  - The shunt is listed as 15 mOhm 0.1% in Adafruit's text, but the Eagle schematic gives R1 = HoLLR2512-2W-15mR-1% (verified in the .sch this run). Write '1% (BOM), calibrate SHUNT_CAL'.
  - EU sourcing note: DigiKey DE 1528-5832-ND is EUR 13.13 excl. / EUR 15.62 incl. VAT, 1,177 in stock, with EUR 25 shipping below EUR 75. Buy it only inside a larger DigiKey EU order; otherwise keep it in the planned Adafruit order.
  
  Limits of this verification:
  - The WebSearch budget was already used up when I started (0 searches ran); only WebFetch and curl on primary pages were used.
  - Mouser and Farnell returned 503 and LCSC refused access, so INA228AIDGSR stock there is unconfirmed.
  - INA780 was not checked (TI page 404).
  - The SparkFun listing was not re-verified (404).
  - Kiwi, Botland and Pi Hut prices come from the searches, not re-fetched.
- **Sources:**
  - https://www.adafruit.com/product/5832
  - https://github.com/adafruit/Adafruit-INA228-PCB (Eagle .sch: R1 value HoLLR2512-2W-15mR-1%, R6 10K Pack, R7 10K, D1 GREEN)
  - https://raw.githubusercontent.com/adafruit/Adafruit-INA228-PCB/main/Adafruit%20INA228%20I2C%20Power%20Monitor.sch
  - https://www.ti.com/product/INA228
  - https://www.ti.com/product/INA228/part-details/INA228AIDGSR
  - https://www.digikey.com/en/products/result?keywords=INA228AIDGSR
  - https://www.tme.eu/en/details/ina228aidgsr/
  - https://www.digikey.com/en/products/result?keywords=CRA2512-FZ-R015ELF
  - https://www.digikey.com/en/products/result?keywords=WSL2512R0150DEA
  - https://www.digikey.de/de/products/result?keywords=adafruit%205832
  - https://www.ti.com/product/INA238
  - https://www.ti.com/product/INA237
  - https://www.ti.com/product/INA700
  - https://www.adafruit.com/product/6349
  - https://www.adafruit.com/product/6340
  - https://www.adafruit.com/product/4226
  - https://www.kiwi-electronics.com/en/adafruit-ina228-i2c-85v-20-bit-high-or-low-side-power-monitor-stemma-qt-qwiic-19941
  - https://botland.store/current-sensors/24135-ina228-current-and-power-sensor-i2c-stemma-qt-qwiic-adafruit-5832-5904422387198.html
  - https://www.tme.eu/en/details/mikroe-4810/add-on-boards/mikroe/
  - https://www.aliexpress.com/w/wholesale-INA228-module.html
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md

