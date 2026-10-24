# Ti tps2553 lab port 0 75 a lna ch1 4 300: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** TI TPS2553 adjustable current-limited power-distribution switch, qty 10 (LNA bias ch1-4 at 300 mA / 166 mA TCBT, LAB USB-A at 0.75 A, HF+ VBUS, RTL-A/RTL-B VBUS, 2 spares). EN from MCP23017 #1, FAULT to MCP #3.
- **Current pick:** TI TPS2553 (STACK v1 line: 'LCSC, not verified, check the -1 latch variant'). Re-audit B requires TPS2553DBVR-1 (latch-off) on LNA ch1-4.
- **Current price usd:** 5.50 for 10 (STACK). Checked 18 Oct 2026: this is the LCSC qty-1 price of the constant-current TPS2553DBVR (C55266, 0.5455 each; 0.4515 at 10+, i.e. 4.52 for 10). The latch-off -1 actually costs less.
- **Decision:** keep
- **Chosen:** TI TPS2553DBVR-1 (latch-off). This is the same part and datasheet (SLVS841F); no analog replaces it. Fit it on all 10 positions. Buy from LCSC C111738 (brand TI, SOT-23-6, active-high EN, 'latch protection'; LCSC's own stock, not a third-party listing). Authorised fallback: DigiKey TPS2553DBVR-1.
- **Chosen price usd:** 2.96 for 10 (0.2959 each at the 5+ tier; 0.2353 at 50+). LCSC product API checked 18 Oct 2026: 2,665 in stock, MOQ 5. Price is ex-VAT and excludes shipping. With 21% VAT it is about 3.58 (model). Authorised fallback: DigiKey 0.766 at qty 10 = 7.66 for 10, 4,259 in stock, Active (checked 18 Oct 2026); about 9.27 with 21% VAT (model). EU stock: TME showed none in the search results (I did not re-check). Farnell and Mouser returned HTTP 503.
- **Saving usd:** 2.54 against the STACK's 5.50. This comes from the source and SKU, not from an analog; analogs save 0. Buying from DigiKey instead costs 2.16 more than the STACK figure. Landed-cost caveat (model, from operator note 35): LCSC ships from outside the EU and gives this part TARIC 8536500300. If the LCSC parcel is EUR 150 or less and goes via IOSS, this tariff line can add EUR 3 duty plus EUR 2 handling fee (from about 1 Nov 2026), unless another part in the same order already uses that line. DigiKey also ships from the US, so the same rule applies to its orders of EUR 150 or less. The AP22653A and TPS2553DBVR carry the same TARIC code, so the duty does not change which candidate is cheapest.
- **Equivalence proof:** The chosen part is the same TI part on the same datasheet (SLVS841F, ti.com/lit/ds/symlink/tps2553.pdf), which I re-read for this check. Every spec is equal because nothing changes:
  - VIN 2.5-6.5 V; abs max 7 V on IN, OUT, EN, ILIM and FAULT; IN-to-OUT ±7 V.
  - RDS(on) 85 typ / 95 max mΩ at 25 C, 135 max over TJ -40..125 C (DBV package).
  - Current limit guaranteed over TJ -40..125 C: 475/520/565 mA at 49.9k, 1200-1375 mA at 20k, 110-150 mA at 210k. TI's equations give these windows at the stack's resistors: 144/166/192 mA at 162k, 265/299/339 mA at 88.7k, 685/747/817 mA at 34.8k.
  - Short-circuit response 2 µs. Reverse comparator trips at 95/135/190 mV and turns the FET off in 3-7 ms. Reverse leakage 1 µA max; off current 1 µA max; on current 140/120 µA max.
  - FAULT deglitch 5/7.5/10 ms (overcurrent) and 2/4/6 ms (reverse). EN thresholds 0.66-1.1 V. UVLO 2.35/2.45 V. Thermal shutdown 135 C in current limit, 155 C otherwise. Rise time 0.7-1.5 ms.
  - UL E169910 and NEMKO IEC 60950-1.
  - Pinout unchanged. RILIM values unchanged (88.7k, 162k, 34.8k).
  - The -1 latch-off is what re-audit B requires. The datasheet confirms it: the -1 'asserts FAULT after the deglitch period and immediately turns off' and stays off until EN is toggled or power is cycled.
  
  LCSC C111738 matches the datasheet: TI brand, TPS2553DBVR-1, SOT-23-6, active high, 2.5-6.5 V, 85 mΩ, 1.5 A, latch protection.
  
  Adversarial results on the cheaper candidates:
  - **Diodes AP22653A (2.61 for 10 at LCSC):**
    - Worse:
      - Voltage: 3.0-5.5 V operating and 6.0 V abs max on all pins, against 6.5 / 7 V.
      - Speed: short-circuit response 5 µs vs 2 µs.
      - Fault blanking: 2/6/20 ms (min 2 ms vs 5 ms).
      - Start-up foldback: about 0.28 x ILIMIT (140 mA at 49.9k vs 490 mA ILIMIT). Starting into a short or a heavy load it can clamp below the load and latch.
      - Limit specification: rated over TA -40..85 C only, not TJ to 125 C, and the 210k row is guaranteed at 25 C only.
      - The 0.75 A window is wider: 665-832 vs 685-817 mA.
    - Partly refuted: by the AP's own best-fit equations, its 166 mA and 300 mA windows (144-191 and 262-341 mA) roughly match the TPS2553. The search claim that it is wider there is not confirmed. The voltage, speed, blanking and foldback failures remain.
  - **TPS2553D (1.88 for 10):** no latch-off version exists in datasheet SLVSDL7, and on-current is higher (150/130 vs 140/120 µA max).
  - **HTC 'TPS2553D':** costs more (3.93 for 10) and LCSC has only 9 in stock.
- **Rejected:**
  1.
    - **Name:** Diodes AP22653AW6-7 (LCSC C1511768, 0.2607 at 5+ = 2.61 for 10, 6,955 in stock; DigiKey 3.00 for 10 per search)
    - **Why:** Worse on several specs (datasheet DS41186 Rev 5-2, re-read): 3.0-5.5 V operating and 6.0 V abs max (TPS2553: 6.5 / 7 V); 5 µs short-circuit response (vs 2 µs); fault blanking minimum 2 ms (vs 5 ms), so false latch-off on the HF+ 100 µF LC inrush is more likely; start-up foldback to about 0.28 x ILIMIT, so into a 180 mA SAWbird+ at a 300 mA setting it would clamp near 84 mA and could latch; limit specified only over TA -40..85 C (210k row at 25 C only); 0.75 A window 665-832 mA vs 685-817 mA; every RILIM must be recalculated. Better: RDS(on) 65/90 mΩ, 2.1 A, output discharge, reverse-current limiting. It saves only 0.35 for 10 against the genuine -1 at LCSC.
  2.
    - **Name:** TI TPS2553DDBVR (TPS2553D, LCSC C521201, 0.1878 = 1.88 for 10, 11,035 in stock)
    - **Why:** No latch-off version (SLVSDL7 lists only the constant-current TPS2552D and TPS2553D), so it cannot serve LNA ch1-4. On-current is higher: 150/130 µA max vs 140/120 µA. VIN minimum 2.7 V. A mixed BOM using it on the LAB and VBUS channels saves at most about 0.43, still carries the on-current penalty, and adds a look-alike part (top mark 15JL vs CHZ).
  3.
    - **Name:** TI TPS2553DBVR, constant current (LCSC C55266, 0.4515 at 10 = 4.52 for 10; the STACK's 5.50 is its qty-1 price)
    - **Why:** Costs more than the -1 at LCSC and has no latch-off. Keep it only as a drop-in for a non-LNA channel that fails the inrush test (top mark 2553).
  4.
    - **Name:** TI TPS2553DBVT-1, small reel (LCSC C2680358, 0.6130 at 10, 50 in stock)
    - **Why:** Same part on a different reel, at about twice the price.
  5.
    - **Name:** HTC Korea / Taejin TPS2553DSF6 (LCSC C2904147, 0.3925 at 10 = 3.93 for 10)
    - **Why:** Costs more than the genuine -1, and LCSC has only 9 in stock, so 10 cannot be bought there. VIN 2.8-5.5 V, TA -40..85 C, no latch-off, typical-only current limit with a 200 mA floor (cannot set 166 mA), foldback. The TI-like name creates a mix-up risk.
  6.
    - **Name:** SG Micro SGM2593XN6G/TR
    - **Why:** Price not verified (the LCSC search API returned 404). The datasheet shows a wider limit: 125-245 mA at 38k and 345-467 mA at 17k over TJ (about ±15-33%). EN and other pins are rated 5.5 V recommended and 6 V abs max; COUT must be at least 10 µF; shutdown current is 5 µA max; flag delay is 14 ms typical with no limits; no latch-off version was found.
  7.
    - **Name:** Silergy SY6280AAC (LCSC C55136, 0.0933 = 0.93 for 10)
    - **Why:** No FAULT pin, so nothing can go to MCP #3. ILIM minimum is 0.4 A, so it cannot set 166 or 300 mA. Accuracy is ±25% at 25 C only. SOT-23-5 with a different pinout, 6 V abs max, preliminary datasheet, no latch-off.
  8.
    - **Name:** TI TPS2552DBVR-1 (DigiKey 6.50 for 10, per search)
    - **Why:** Costs more. Its active-low EN needs a pull-up; with the MCP23017 unpowered, the MCP's ESD diode holds EN near 0.5-0.7 V, at or under the 0.66 V threshold, so the switch can turn on. That breaks fail-safe-off and the no-back-feed rule.
  9.
    - **Name:** TI TPS25221DBVR (DigiKey 5.83 for 10)
    - **Why:** Costs more. Its 275 mA minimum makes 166 mA impossible, and its 300 mA-class setting spreads 210-370 mA. No latch-off, no reverse comparator while enabled, VIN 5.5 V maximum.
  10.
    - **Name:** TI TPS25200DRVR (DigiKey 7.13 for 10, 0 in stock)
    - **Why:** Costs more and is out of stock. WSON package, not SOT-23. Reverse leakage 3/5 µA, no latch-off, poor accuracy at the low end of its range.
  11.
    - **Name:** Microchip MIC2009A-1YM6
    - **Why:** P-FET with 170 mΩ typical, 0.9 A maximum, VIN 5.5 V maximum, rated -40..85 C.
  12.
    - **Name:** onsemi NCP380 (adjustable)
    - **Why:** Adjustable only from 0.5 to 2.1 A, so it cannot set 166 or 300 mA; ±15% at the 0.75 A class; different pinout.
  13.
    - **Name:** DIY discrete limiter, or INA3221 software cut-off
    - **Why:** Response in milliseconds instead of 2 µs; no guaranteed accuracy, reverse protection or certification; more parts and board area. No measured evidence that it is equal.
  14.
    - **Name:** Used or loose-lot 'TPS2553' parts
    - **Why:** No traceability, so they fail the counterfeit rule. Genuine new parts already cost 0.30.
- **Conditions or tests:** 1. **Goods-in check.** LCSC's TI authorisation is not verified: TI's distributor pages returned 404 and WebSearch was out of budget. Every part must carry the top mark 'CHZ', which is TI's marking for TPS2553DBVR-1 (TPS2553DBVR is marked '2553', TPS2553D '15JL'). Reject the lot if the mark differs.
  2. **Trip test, every channel, at 4.5 V (LNA) or 5.0 V (LAB):**
     - Electronic-load ramp: 265-339 mA at 88.7k, 144-192 mA at 162k, 685-817 mA at 34.8k.
     - Latch-off within 5-10 ms of overload, FAULT seen at MCP #3, reset by an EN toggle.
     - Channel stays off with EN pulled down and the MCP unpowered.
  3. **Inrush test on the channels that move to latch-off (HF+ VBUS, RTL-A/B VBUS, LAB port).** Enable into the HF+ 100 µH/100 µF LC with the HF+ connected, and into the 120 µF USB bulk, at -10 C and in the warm case. The current-limit period must end before the 5 ms minimum deglitch.
     - Model: 100 µF x 5 V / (0.5 A - 0.3 A) ≈ 2.5 ms in the worst case.
     - If a channel latches, fit the constant-current TPS2553DBVR (LCSC C55266) on that channel only.
  4. **Spur check (unchanged).** Look for charge-pump spurs with the tinySA at each LNA bias port.
  5. **Landed-cost check.** Before ordering, confirm whether the LCSC parcel is EUR 150 or less (EUR 3 duty plus EUR 2 handling per tariff line) and whether VAT is collected via IOSS. If the counterfeit risk is not acceptable, buy from DigiKey at 7.66 for 10.
- **Stack changes:** - **BOM line:** 'TI TPS2553DBVR-1 (latch-off), qty 10, LCSC C111738, 2.96 for 10 (0.2959 at 5+), verified 18 Oct 2026; authorised fallback DigiKey 7.66 for 10'. The Power group total drops by 2.54. This closes the STACK open item 'check the -1 latch variant'.
  - **One SKU on all 10 positions:** LNA ch1-4, LAB USB-A, HF+ VBUS, RTL-A and RTL-B VBUS, plus 2 spares. The -1 is cheaper than the constant-current DBVR, and a shorted LAB port then latches off instead of thermal-cycling at about 3.7 W in the closed case.
  - **labd:** treat FAULT on every channel as a latch (EN low, wait, EN high, with a retry limit and backoff), not only on the LNA channels. The existing RTL watchdog VBUS toggle (GPA2/GPA3/GPA0) already does this.
  - **No other hardware changes:** RILIM values (88.7k, 162k, 34.8k; HF+ and RTL at 1.5-2x the measured current), the EN pull-down, the FAULT pull-ups, footprint, rails (LNA4V5 4.5 V, 4.30 V since v2.1; LAB5 5.0 V), connectors and case all stay. There is no driver or Ubuntu dependency.
  - **Hard rules:** receive-only and the other hard rules are unaffected; this is a linear DC switch with no RF path.
  - **Possible extra unit:** if the operator-note-30 Lime M.2 3.3 V power-cycle switch is ever given to a TPS2553, qty becomes 11. That is not decided here; at 1.5 A maximum continuous the TPS2553 may be marginal for the Lime.
  - **Limits of this check:** the WebSearch budget was used up, so I found no forum or bench measurements, and Farnell and Mouser returned HTTP 503. All prices above were checked through the LCSC product API and the DigiKey page on 18 Oct 2026. Downloaded data: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/v_tps2553/lcsc_C111738.json and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/v_tps2553/ds/tps2553d.txt.
- **Sources:**
  - https://www.lcsc.com/product-detail/C111738.html (data via https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=C111738)
  - https://www.lcsc.com/product-detail/C55266.html
  - https://www.lcsc.com/product-detail/C521201.html
  - https://www.lcsc.com/product-detail/C1511768.html
  - https://www.lcsc.com/product-detail/C2904147.html
  - https://www.lcsc.com/product-detail/C55136.html
  - https://www.lcsc.com/product-detail/C2680358.html
  - https://www.digikey.com/en/products/result?keywords=TPS2553DBVR-1
  - https://www.ti.com/lit/ds/symlink/tps2553.pdf
  - https://www.ti.com/lit/ds/symlink/tps2553d.pdf
  - https://www.diodes.com/assets/Datasheets/AP22652_53.pdf
  - https://www.sg-micro.com/product/SGM2593
  - https://www.ti.com/lit/ds/symlink/tps25221.pdf
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (items 34-35, EU duty rules)
- **Confidence:** high

