# Pca9555 key expander piezo status led: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_071e1025-145`_

- **Part:** HMI key-expander set: 16-bit I2C expander for 6 keys and 2 encoder pushes (Pico I2C0 GP4/5, address 0x20, INT to GP10, VEML7700 at 0x10), piezo on GP20, status LED on GP21
- **Current pick:** STACK v1 lists "PCA9555, piezo, status LED" with no SKUs. Re-audit A changed the PCA9555 to the TI TCA9555PWR, so the real baseline is TCA9555PWR plus an unspecified externally driven piezo plus an unspecified single-colour LED.
- **Current price usd:** STACK gives 5-10 as a model estimate. The verified baseline set (DigiKey, qty 1, 18 Oct 2026) costs $3.08 in parts: TCA9555PWR $1.94 + CPT-1207-3TH $0.61 + WP7113LSECK/J3 $0.53, plus about $0.3 of passives, so about $3.4. On digikey.de the TCA9555PWR is EUR 1.70. The TI.com store has it out of stock and TME has 0 in stock.
- **Decision:** replace_conditionally
- **Chosen:** Diodes Inc. PI4IOE5V9555LEX (TSSOP-24, 0x20), Same Sky CPT-1207-3TH externally driven piezo, and Kingbright WP7113LSECK/J3 5 mm hyper-red LED (625 nm) behind a frosted sealed window or light pipe. The TCA9555PWR stays as a no-change fallback on the same footprint.
- **Chosen price usd:** $2.62 in parts (DigiKey qty 1: $1.48 + $0.61 + $0.53), about $2.9 with passives. At qty 10: $1.071 + $0.458 + $0.368. EU (digikey.de, ex VAT): EUR 1.30 + 0.54 + 0.47 = EUR 2.31, or EUR 2.75 with 19% DE VAT. The diffusing window or light pipe is not counted: it belongs to the case, and every LED needs one for IP54.
- **Saving usd:** $0.46 per set against the verified TCA9555 baseline ($3.08 to $2.62). In the EU that is EUR 0.40 ex VAT (EUR 1.70 to 1.30). The piezo and LED had no SKU before, so they are first verified picks, not savings. The BOM row also falls from the estimated 5-10 to about $2.9. That drop corrects the estimate; it is not an analog saving.
- **Equivalence proof:** EXPANDER: PI4IOE5V9555 (Diodes DS41303 Rev 1-2, Aug 2021) against TCA9555 (TI SCPS200E, Apr 2019). Both datasheets were read in full.
  - Equal:
    - 16 I/O.
    - Same command bytes 0-7 (input, output, polarity, config) with pair auto-toggle.
    - Address 0100 A2A1A0, so 0x20 works.
    - Same TSSOP-24 pinout: INT 1, A1 2, A2 3, P0 on 4-11, GND 12, P1 on 13-20, A0 21, SCL 22, SDA 23, VCC 24. The footprint is shared, so the two parts swap freely.
    - 400 kHz with a 50 ns spike filter.
    - Weak 100 kOhm pull-up on every I/O (IIL at most 100 uA). Inputs at reset.
    - Open-drain active-low INT, tv/trst 4 us.
    - 5 V-tolerant I/O, -40 to +85 C.
    - Port IOL at least 8 mA at 0.5 V and at least 10 mA at 0.7 V.
    - Limits of 25 mA per pin, 100 mA per octal and 200 mA total.
    - Latch-up above 100 mA.
    - Both lose an INT edge that falls on the ACK clock (TI section 9.3.3).
  - Better:
    - ESD 4 kV HBM against 2 kV (CDM 1 kV on both).
    - Standby with inputs high: 1 uA max against 3.5 uA at 5.5 V.
    - Tj max 125 C against 100 C.
    - VIH fixed at 1.8 V against 2.31 V at 3.3 V. That gives 0.5 V more margin on the weak-pull-up high state of the keys.
  - Worse, declared and judged irrelevant or covered:
    - (a) VCC min 2.3 V against 1.65 V. It runs at 3.3 V.
    - (b) Operating ICC 200 uA max (100 kHz, 5.5 V) against 40 uA. That is under 1% of the Pico load.
    - (c) VIL 0.81 V against 0.99 V. A closed key reads about 0 V.
    - (d) POR is characterised less well. VPOR is 1.16 typ / 1.41 max. A re-reset needs VCC below 0.2 V for at least 20 us, where the TCA needs below VPORF of 0.75-1.0 V. There is no ramp or glitch table, where TI gives VCC_GH/VCC_MV/VCC_GW. A short LAB5 drop-out can therefore leave the PI4IOE un-reset while the RP2040 reboots. It is covered by the firmware re-init and the bench test in the conditions.
    - (e) Factory lead time 52 weeks against 20. DigiKey has 3,021 Active units in stock.
  - Drivers: no driver difference. The part sits on the Pico bus. Mainline gpio-pca95xx.yaml has no ti,tca9555 or diodes,pi4ioe5v9555 compatible, so either part would use nxp,pca9555 if it ever moved to the Q6A.
  
  PIEZO: CPT-1207-3TH (Same Sky datasheet Rev 1.0, 22 Jul 2025).
  - No driving circuit and no coil, so no magnetic field near the HF+.
  - 4,000 Hz. SPL 75 dB MIN at 10 cm with a 3 Vp-p half-duty square wave (checked by column position in the PDF). The reference TDK PS1240P02BT gives 70 dB(A) min at 3 V0-P.
  - Current 3 mA max. Capacitance 8.4/12/15.6 nF.
  - -40 to +85 C, which meets the -30 C requirement. TDK is rated -10 C.
  - Size 12.5 x 7.0 mm (7.5 mm seated per DigiKey), inside the 13/8 mm limit. Declared: 0.3 mm wider and 0.5-1.0 mm taller than the TDK.
  - Not sealed (the TDK is not either), so it needs a vent.
  
  LED: WP7113LSECK/J3 (Kingbright DSAN8286 V.5A, Mar 2025).
  - 400 min / 1000 typ mcd at 2 mA (CIE127-2007). DigiKey lists 550 mcd. This beats 400 mcd at 10 mA or less by about 5x.
  - Vf 1.8 typ / 2.1 max at 2 mA.
  - -40 to +85 C, ESD 3 kV HBM.
  - Single colour, which fits GP21. PWM-dimmable.
  - Declared: the 20 deg clear lens fails the 60 deg spec on its own, so the frosted sealed window or light pipe is mandatory. The spec allows this, and IP54 requires a window anyway.
- **Rejected:**
  1.
    - **Name:** TI TCA9555PWR ($1.94, EUR 1.70)
    - **Why:** Not rejected on quality: it is the safe baseline and the fallback on the same footprint. It costs $0.46 more. Fit it if the PI4IOE fails the brown-out test.
  2.
    - **Name:** TI PCA9555PWR ($2.38)
    - **Why:** Costs more, and TI has superseded it with the TCA9555.
  3.
    - **Name:** onsemi CAT9555YI-T2 ($1.52)
    - **Why:** Costs more than the PI4IOE5V9555. DigiKey shows no stock quantity for it (the 22,740 shown belongs to a suggested TI PCA9535 substitute). 41-week lead time. ESD only 2 kV HBM.
  4.
    - **Name:** NXP PCAL9555APW,118 ($1.95)
    - **Why:** Not cheaper than the TCA9555. Datasheet not read. The power-up default of its Agile I/O pull-ups is unverified.
  5.
    - **Name:** Diodes PI4IOE5V9554LEX, TI TCA9554/TCA9554A, TI PCF8574PWR (8-bit)
    - **Why:** 8 I/O leaves no spare lines (an RGB option or more keys would be impossible), and the firmware or address would change. Spec trade.
  6.
    - **Name:** UMW TCA9555PWR ($2.21 / EUR 1.94) and UMW PCA9555PW ($1.97)
    - **Why:** Second-source clones that cost more than the genuine TI part. No independent data. The UMW IOL is specified differently.
  7.
    - **Name:** XINLUDA XL9555 and AliExpress PCA9555 modules
    - **Why:** No verified price, datasheet or provenance, and not from an authorised distributor. Counterfeit risk.
  8.
    - **Name:** Adafruit AW9523 #4886 ($4.95) and other breakouts
    - **Why:** Cost 2.5-4x more. The AW9523 has no pull-ups, powers up with outputs low and uses a different register model. A keypad PCB exists anyway.
  9.
    - **Name:** MaxLinear XRA1201
    - **Why:** Obsolete and not register-compatible (search result, not re-checked).
  10.
    - **Name:** TDK PS1240P02BT ($0.73; Adafruit #160 $1.50)
    - **Why:** Costs more than the CPT-1207-3TH and is quieter (70 dB(A) min against 75 dB min). Rated only to -10 C, which fails the -30 C requirement.
  11.
    - **Name:** Raltron RDT-4.000-1212-NS1 ($1.16)
    - **Why:** Costs more, low stock, datasheet not read. Worth it only if the keypad stack must be SMD or 3.3 mm tall.
  12.
    - **Name:** Same Sky CPT-2212-3TH ($1.19)
    - **Why:** At 22 mm it exceeds the 13 mm HMI-column limit, and it costs more.
  13.
    - **Name:** Murata PKM13EPYH4000-A0
    - **Why:** Last Time Buy.
  14.
    - **Name:** Differential piezo drive on GP20+GP22
    - **Why:** It would use the only spare GPIO, and 75 dB min single-ended already meets the spec.
  15.
    - **Name:** WS2812B/SK6812 on GP21
    - **Why:** Internal PWM at 430 Hz / 1.1 kHz falls in the audio band. It needs 5 V and a level shifter, and it draws quiescent current.
  16.
    - **Name:** Broadcom ASMB-LTD3-0C3F3 RGB ($0.61) and Kingbright WP154A4SUREQBFZGW RGB ($1.97)
    - **Why:** They need 3 expander lines, not GP21. G/B Vf of 2.9-3.3 V leaves almost no headroom at 3.3 V, and the temperature range is unverified. STACK v1 specifies one single-colour LED. Use them only if the RGB option is adopted.
- **Confidence:** medium
- **Conditions or tests:** 1. Pico firmware (needed for either chip):
     - At boot and after any I2C NACK or timeout: 9-clock bus recovery and STOP, write registers 2-7, then read ports 0/1 to clear INT.
     - Every 1 s: read back registers 2-7 and rewrite them on any mismatch.
     - Back up INT with a 20-50 ms port poll, because an edge on the ACK clock can be lost.
  2. Bench brown-out test before closing the case. Switch LAB5 off for 10, 30, 100, 300, 1000 and 3000 ms, 10 cycles each (60 in total). Then ramp VSYS slowly from 0 to 5 V at about 1 V/s. If a programmable supply is available, also dip the 3V3 rail to 2.0 V and to 1.0 V for 10 ms.
     - Pass: after every event all 8 switches read correctly, INT asserts and clears, SDA is never stuck, the readback matches and any spare outputs come up OFF.
     - On any failure, fit the TCA9555PWR (+$0.46, same footprint).
  3. Buy 2 PI4IOE5V9555LEX (factory lead time 52 weeks), or keep a TCA9555PWR as the spare.
  4. Piezo:
     - Check the 7.5 mm seated height in the keypad PCB and bezel stack.
     - Fit an ePTFE acoustic vent over the port.
     - Check the SPL at 10 cm with the 3.3 V GPIO drive and a 100-220 Ohm series resistor.
  5. LED:
     - Fit a frosted sealed window or light pipe.
     - Default resistor 680-750 Ohm (about 2 mA, at least 400 mcd min).
     - Check visibility in full sun (about 100 klx on the VEML7700). If it is not visible, use 330 Ohm (about 4.5 mA) with GP21 drive strength set to 8 mA.
  6. LF spur check. A 4.000 kHz tone puts its 15th harmonic exactly on 60 kHz (MSF) and its 10th on 40 kHz (JJY).
     - Bench A/B: try about 4.209 kHz (Pico TOP+1 = 29698 at 125 MHz). Its odd harmonics stay at least 2.1 kHz from 40, 60, 77.5 and 162 kHz. Adopt it if it loses no more than 2 dB SPL.
     - Either way, labd mutes non-Critical beeps and holds the LED at DC (no PWM) during LF time-signal sessions.
- **Stack changes:** - BOM row "Expander, piezo, status LED": replace "PCA9555 ... 5-10 (model)" with "Diodes PI4IOE5V9555LEX (TCA9555PWR as drop-in fallback) + Same Sky CPT-1207-3TH + Kingbright WP7113LSECK/J3 + passives. Verified DigiKey 18 Oct 2026, about $2.9 (EUR 2.31 ex VAT parts on digikey.de)." Bundle it into the existing DigiKey HMI order (Pico SC0915, PEC11R, KSC641J).
  - Pin map 5.2 and the I2C address map: the text changes from PCA9555 to PI4IOE5V9555 (or TCA9555). Address 0x20 is unchanged, with A0-A2 tied to GND. No clash with the VEML7700 at 0x10.
  - Keypad PCB:
    - TSSOP-24 PW footprint with 100 nF at VCC and a 10 kOhm pull-up on INT to 3V3.
    - Keys to GND need no external pull-ups.
    - Piezo: THT, 12.5 mm diameter, 7.5 mm seated, 100-220 Ohm series resistor from GP20.
    - LED: 5 mm THT on GP21 through 680-750 Ohm.
  - Case: a frosted sealed LED window or light pipe and an ePTFE vent over the piezo port.
  - Firmware: the re-init, readback and poll rules from the conditions, plus the LF-session rule (tone about 4.209 kHz or muted; LED DC only).
  - Unchanged:
    - Rails and power budget. On the Pico 3V3: expander 0.2 mA max, plus 8 x 33 uA with all keys pressed, LED 2-5 mA, piezo 3 mA or less.
    - No Ubuntu or arm64 driver is involved.
    - GP22 stays spare.
    - Hard rules are untouched: passive HMI, no emitter, no coil or loop.
  - RGB stays out of the default build: single colour on GP21, as in STACK v1. If the final_completeness RGB is wanted, it goes on 3 spare expander P1 pins, both chips being 5 V-tolerant and able to sink 10 mA or less. G/B then needs a 5 V anode, and the 16-bit part is the reason this remains possible.
  - Method limits:
    - The shared WebSearch budget was used up, so no independent forum measurements were found for the PI4IOE5V9555 or the CPT-1207-3TH.
    - Mouser returned 503 and the Diodes product page returned 403, so the PI4IOE lifecycle status comes from DigiKey ("Active").
    - TME has no listing for the PI4IOE5V9555.
  - Local copies: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/hmi_verif/pi4/ds.txt, /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/hmi_verif/cpt/ds.txt, /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/hmi_verif/kb/ds.txt, /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/hmi_verif/calc/harm.py
- **Sources:**
  - https://www.diodes.com/assets/Datasheets/PI4IOE5V9555.pdf
  - https://www.ti.com/lit/ds/symlink/tca9555.pdf
  - https://www.ti.com/product/TCA9555/part-details/TCA9555PWR
  - https://www.digikey.com/en/products/result?keywords=PI4IOE5V9555LEX
  - https://www.digikey.de/en/products/result?keywords=PI4IOE5V9555LEX
  - https://www.digikey.com/en/products/detail/texas-instruments/TCA9555PWR/2094642
  - https://www.digikey.de/en/products/result?keywords=TCA9555PWR
  - https://www.digikey.com/en/products/result?keywords=CAT9555YI-T2
  - https://www.tme.eu/en/katalog/?search=PI4IOE5V9555
  - https://www.sameskydevices.com/product/resource/cpt-1207-3th.pdf
  - https://www.digikey.com/en/products/result?keywords=CPT-1207-3TH
  - https://www.digikey.de/en/products/result?keywords=CPT-1207-3TH
  - https://www.kingbrightusa.com/images/catalog/SPEC/WP7113LSECK-J3.pdf
  - https://www.digikey.com/en/products/result?keywords=WP7113LSECK%2FJ3
  - https://www.digikey.de/en/products/result?keywords=WP7113LSECK%2FJ3
  - https://cdn-shop.adafruit.com/product-files/160/160_ds.pdf
  - https://raw.githubusercontent.com/torvalds/linux/master/Documentation/devicetree/bindings/gpio/gpio-pca95xx.yaml
  - https://raw.githubusercontent.com/torvalds/linux/master/drivers/gpio/gpio-pca953x.c

