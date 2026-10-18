# Aneng an8008 9 dmm: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** Pocket DMM, bench and field case, qty 1 (STACK.md line 348 lists it as "ANENG AN8008/9")
- **Current pick:** ANENG AN8008 (the variant reaudit_D names). STACK.md lists "AN8008/9", and the procedures already depend on the AN8009's K-type input (radio_lab.json lines 3359, 3506 and 4250; reaudit_D line 1248, thermocouple on a cell).
- **Current price usd:** AN8008, AliExpress search pages read 18 Oct 2026 from a US IP; the .com and de. pages both show USD, without VAT or the EUR 3 duty:
  - $28.52 (item 3256808914707497, 249 sold) and $29.12 (item 3256808889489096, 74 sold) are NEW-SHOPPER prices ($71.47 - $42.95 and $71.25 - $42.13). Neither is the regular price.
  - Regular price: $33.43 (item 3256808311369414, 6 sold), $36.48 or $42.59.
  - STACK range: $26-53.
- **Decision:** replace_conditionally
- **Chosen:** ANENG AN8009, the same vendor, case and PCB family. Buy from a high-volume listing:
  - item 3256806808156150: $26.19, 1,000+ sold, 4.9 rating
  - or item 3256810125666852: $24.35 new-shopper price, 900+ sold, 4.7 rating
  Avoid any "AN8008/AN8009 ... Rm 409b" listing.
  
  Fallback if the condition fails: AN8008 (item 3256808311369414 or 3256808914707497) plus a separate K-type thermometer, price not checked.
- **Chosen price usd:** Prices are from the AliExpress search pages on 18 Oct 2026, in USD, excluding VAT and duty:
  - $24.35 (new-shopper price, $23.13 each for 2 or more)
  - $24.79 (item 3256812466121218, 11 sold, regular price)
  - $26.19 (1,000+ sold, "Lowest price in 90 days")
  - $34.39-34.69 for other regular listings
  
  EU landed cost, from operator_notes item 35: price + import VAT 19-27% + EUR 3 duty per tariff line + EUR 2 handling fee from about 1 Nov 2026. The duty and fee are identical for the AN8008, so they do not change the comparison.
- **Saving usd:** The saving is $4-9 before VAT. It is about $5-11 including 19-27% VAT; that range is my calculation.
  - New shopper vs new shopper: $28.52 - $24.35 = $4.17.
  - Regular vs regular: $33.43 - $26.19 = $7.24, or $8.64 against the $24.79 listing.
  - HKJ's AN8009 package (2017) included a K-type probe. If current listings still include it, the stack does not need a separate thermometer; package contents are not checked.
- **Equivalence proof:** Sources: HKJ measured both meters (lygte-info). I compared the two reviews line by line.
  
  **Equal**
  - Case: 130.4x65x32.3 mm against 130.2x65x32.3 mm. Both weigh 136 g with batteries, run on 2x AAA and have auto power-off at 15 min.
  - 9999 counts.
  - uA shunt: R23+R24 = 99+1 Ohm, so about 10 mV burden at 99.99 uA. It is protected by D5 plus F2 0.2 A/250 V 3.6x10 mm. I saw R24 "1 Ohm", F1 "10A/250V" and F2 "200mA/250V" myself in HKJ photo DSC_3997.
  - A/mA: 0.01 Ohm shunt (very low burden) and F1 10 A/250 V.
  - Current ranges limited to 36 VDC.
  - DCV input 10-11 MOhm (AN8008: 10 MOhm).
  - Capacitance to 70 mF.
  - Diode test 3.2 V open, display up to 3.000 V.
  - Continuity threshold under 50 Ohm.
  - HKJ found both "within specified tolerances except 10 A". The 10 A flaw (a few % heating drift at 5-10 A) is the same on both, so pack-current accuracy stays with the FNB58 and INA228.
  - Both CAT ratings are fake. Low-energy use only, as before.
  
  **Better on the AN8009**
  - Resistance to 99.99 MOhm (AN8008: 9.999 MOhm).
  - Frequency counter to 6.6 MHz at 1 Vrms, and 250 mV sensitivity at 1 kHz (AN8008: 3 MHz and about 600 mV).
  - Continuity responds in 4 ms (AN8008: 20 ms).
  - K-type temperature on the mV position, probe included in 2017. The stack's procedures use it.
  - Backlight stays on 120 s (AN8008: 15 s).
  
  **Worse or different, stated openly**
  - No square-wave output. A grep of STACK.md and every re-audit file finds no procedure that uses the DMM square wave; the only square waves are the tinySA and the GPSDO. Dropping it also removes one signal source from the kit.
  - Supply current 1.6-2.0 mA (AN8008: 1.6 mA), and 8.7 mA with the backlight (AN8008: 7.5 mA). That is still more than 500 h on 2x AAA (my calculation).
  - Diode-test current 0.14 mA (AN8008: 0.2 mA). Vf reads about 9 mV lower; pass/fail is unaffected.
  - The mV input stays high-impedance only up to about 1.5 V (AN8008: about 2 V). The stack uses that range below 100 mV.
  - NCV is added; it is unused and passive.
  
  **Not proven: the reason this is conditional**
  HKJ's AN8009 review does not list the 99.99 uA / 0.01 uA range or the 9.999 mV / 1 uV range. For the AN8008 these come from the official Zotek ZT109 manual (99.99 uA at 0.01 uA, +/-(0.8%+3); 9.999 mV at 0.001 mV; DCV +/-(0.5%+3)) and from Hennessy. On the AN8009 I infer them from the identical 100 Ohm shunt and the same architecture, with ranges defined in the 24C02A EEPROM. That is an inference, not a measurement, and HKJ notes "small variations in functions" between rebadges. The 10 nA range is essential for the #2813 off-state check (<0.2 uA) and the TPS70933 check (1.3 uA). The 999.9 uA range gives +/-0.3 uA, which is not enough.
- **Rejected:**
  1.
    - **Name:** ZOYI/Zotek ZT109 '9999 Counts Square Wave Output' (items 3256811633310820 at $24.36, 3256812492441881 at $35.49; 3256812201274210 at $22.28 as claimed by the search agent)
    - **Why:** The specs are genuine for the real ZT109: the official Zotek manual (szzotek.com) matches the AN8008 exactly. The price is not real, though. $24.36 is a new-shopper price ($69.25 - $44.89), 3 sold. The same title at the regular price is $35.49, which is more than the AN8008's regular $33.43. The $22.28 listing did not appear when I fetched the page, so it is unverified. The titles mix 'ZT109 / ZT111', and Zotek's official model list has no ZT111, so you cannot be sure which variant ships. It also has no K-type input, which the stack's procedures use, so for this stack it is worse than the AN8009 at the same new-shopper price.
  2.
    - **Name:** ZOYI 'ZT109 ZT111 9999 Counts NCV' (items 3256811726494118, 3256811842651199, $15.33)
    - **Why:** 1-3 sold, no spec table, a model that is not on Zotek's official list, and a mixed-model title. Neither the 10 nA range nor temperature can be proven. Rejected as unverifiable and a possible grey-market or counterfeit risk.
  3.
    - **Name:** ZOYI 'ZT109/111 6000 Counts' (Dollar Express $20.19 / $21.99, item 3256808186461731 $16.05)
    - **Why:** A different 6000-count meter under the ZT109 name. It loses the 9999 counts and almost certainly the 99.99 uA / 10 nA range.
  4.
    - **Name:** ZOYI ZT-109 'Anti-burn' ($21.55 new-shopper, regular $28.35)
    - **Why:** The title states neither counts nor ranges, so the variant is unknown. Nothing shows it is not worse.
  5.
    - **Name:** ANENG AN8008/AN8009 'Rm 409b Double Fuse' listings ($35.59-36.19)
    - **Why:** The title mixes in a different 6000-count Richmeters meter, a sign of mislabelled or grey stock. It is not cheaper either.
  6.
    - **Name:** ANENG AN8008 (kept as fallback only)
    - **Why:** $28.52 and $29.12 are new-shopper prices. Its regular price of $33.43 or more is above the AN8009's. It has no K-type input, which the stack's procedures need, so keeping it requires a separate thermometer.
  7.
    - **Name:** ANENG AN8002 / ZOYI ZT-102A
    - **Why:** 6000 counts and no 10 nA uA range (Hennessy and HKJ).
  8.
    - **Name:** ANENG AN870
    - **Why:** $34.88-35.39, so not cheaper. Its 1 Ohm mA shunt gives about 100x the mA burden. It weighs 374 g and measures 180x89x44 mm.
  9.
    - **Name:** UNI-T UT61E+ / UT61E (used)
    - **Why:** $52-55, about 350 g. The UT61E's uA/mA shunt chain gives about 10x the uA burden (HKJ). Not cheaper.
  10.
    - **Name:** ANENG AN860B+ / VC17B+, ANENG Q1, BSIDE ADM20
    - **Why:** Best uA resolution only 0.1 uA, or a uA offset and no mA range (Q1), or 6000 counts and bulk (ADM20).
  11.
    - **Name:** INA228 used as a uA meter (DIY)
    - **Why:** About 20.8 uA per LSB on the 15 mOhm shunt, so about 2000x coarser than 10 nA. It is not a DMM.
  12.
    - **Name:** Used AN8008/AN8009
    - **Why:** Price unverified (eBay 403). Unknown fuse and shunt history, for a saving of only a few dollars.
- **Conditions or tests:** BEFORE ORDERING (any one is enough):
  - The listing's spec image shows DC uA '99.99uA 0.01uA' and DC mV '9.999mV 0.001mV'.
  - Or the seller confirms both in writing.
  - The listing includes the K-type probe.
  If none of these can be had, buy the AN8008 instead.
  
  ON ARRIVAL (return within AliExpress buyer protection if any step fails):
  1. In the uA position, press RANGE: the display must step to xx.xx uA. In the mV position, DC: it must show x.xxx mV.
  2. Reaudit_D test: at 10 uA and 90 uA from the DPS-150 through a known 0.1% resistor (for example, 1.000 V into 100.0 kOhm gives 10.00 uA; spec +/-0.11 uA), check the reading and the burden.
  3. Open the case. Check F1 10 A/250 V and F2 200 mA/250 V, both 3.6x10 mm, and that R23/R24 are 99+1 Ohm.
  4. K-type in ice water reads about 0 C. The AN8009's temperature accuracy is not published (unverified), so use it only for pass/fail spot checks (45 C cell, 70 C KSD9700).
  5. Buy spare 3.6x10 mm fuses (0.2 A and 10 A).
- **Stack changes:** - **STACK.md line 348:** change "ANENG AN8008/9" to "ANENG AN8009 (K-type probe included; fallback AN8008 + K-type thermometer)".
  - **STACK.md line 407:** change AN8008 to AN8009. This makes the procedures that already cite the AN8009 thermocouple consistent with the BOM.
  - **Reaudit_D acceptance test:** drop "PCB marked ZT109 / DM1106EN". The AN8009's main IC is chip-on-board under epoxy (HKJ photo DSC_3997), and its PCB marking is unverified. Use the functional checks above instead.
  - **INA228 SHUNT_CAL check:** keep it on the external-shunt mV method (9.999/99.99 mV ranges), not the 10 A range.
  - **The 1.0 mA standby target** still sits at the top of the 999.9 uA range, the same as with the AN8008.
  - **No change** to rails, connectors, drivers, Ubuntu or the case: same size, 2x AAA, no host interface.
  - **Thermal camera:** the TC001 stays optional.
  - **Hard rules:** all still hold. The meter is passive, NCV is a passive E-field sensor, there is no loop or H-field probe, and losing the square-wave output removes one signal source from the kit.
  
  Limits of this check:
  - WebSearch was already used up (shared turn budget), so everything here comes from WebFetch and curl on primary pages.
  - AliExpress item pages, Amazon (503) and eBay (403) could not be read, so sellers and checkout prices are unverified.
  - No EU-stock seller of the AN8008/9 or ZT109 was found.
- **Confidence:** medium
- **Sources:**
  - https://lygte-info.dk/review/DMMAnengAN8009%20UK.html
  - https://lygte-info.dk/review/DMMAnengAN8008%20UK.html
  - https://lygte-info.dk/pic/Aneng/AN8009/DSC_3997.jpg
  - https://www.markhennessy.co.uk/budget_multimeters/aneng_an8008.htm
  - http://www.szzotek.com/en/col.jsp?id=144
  - https://download.s21i.co99.net/8164272/0/0/ABUIABA9GAAgnrCGzAUohvWTvgU.pdf?f=ZT109-Eng.pdf&v=1501665310
  - https://www.manualslib.com/manual/4049557/Aneng-An8008.html
  - https://www.aliexpress.com/w/wholesale-aneng-an8009.html
  - https://de.aliexpress.com/w/wholesale-aneng-an8009.html
  - https://www.aliexpress.com/w/wholesale-aneng-an8008.html
  - https://www.aliexpress.com/w/wholesale-zoyi-zt109-9999-counts.html
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dmm_dl/zt109.txt

