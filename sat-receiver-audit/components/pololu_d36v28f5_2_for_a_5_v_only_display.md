# Pololu d36v28f5 2 for a 5 v only display: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_00ce4a12-e10`_

- **Part:** Pololu D36V28F5 #2 (#3782): optional 5 V buck from SW to the display board, needed only if the Wisecoco board turns out to be 5 V-only. Tier optional, qty 1.
- **Current pick:** Pololu D36V28F5 #3782 bought from Pololu direct (US)
- **Current price usd:** 23.95 at qty 1, 22.03 at 5+ ('Rationed (Active and Preferred)'; live pololu.com/product/3782 fetch on 18 Oct 2026). A WebSearch snippet showed 21.95, but that is a stale cache; the live page wins. For the EU buyer this is before US shipping, import VAT, the EUR 3 duty per tariff line and the EUR 2 UHF from about 1 Nov 2026 (operator notes 34-35).
- **Decision:** replace_conditionally
- **Chosen:** Buy no converter. Feed the Wisecoco 'DC(5-24V)' barrel, or the 4D fallback's 12 V barrel, straight from the existing DISP12 rail: SYS12 (D36V50F12, 12 V +/-4%) -> LC -> TPS259470A eFuse (ILIM 1.5 A, OVLO about 13.5 V, EN on Pico GP16). This is already the stack default after re-audit D.
  
  Contingency, only if Wisecoco's written answer shows a 5 V-only board revision: the same Pololu D36V28F5 #3782 from Botland, an official Pololu EU distributor (botland.de / botland.store / botland.com.pl, index PLL-17169, EAN 5903351242837) at EUR 15.22 net / EUR 18.11 gross, with TME POLOLU-3782 as the fallback seller. It must carry an ideal-diode or Schottky at its output, and panel VBUS stays open.
- **Chosen price usd:** 0.00, since every DISP12 part is already in the BOM and its load is already counted in SYS12. Contingency only: 17.13 net / 20.38 gross (EUR 15.22 / 18.11 at ECB 1.1253 USD/EUR of 16 Oct 2026, which I re-checked). Botland PL is PLN 79.90 gross, about 16.73 net / 20.57 gross at ECB 4.37 PLN/EUR. Shipping is from EUR 4.69 (DE) or EUR 8.07 (GLS EU, botland.store).
- **Saving usd:** 23.95 against the list price, and more against the Pololu-US landed EU cost (shipping + VAT + EUR 3 duty + EUR 2 UHF), which is roughly 34+ USD (estimate). In the contingency case: 6.82 net (17.13 vs 23.95) and no US landed extras.
- **Equivalence proof:** The no-converter path is equal or better on every spec that matters for a board with a 5-24 V input.
  
  **What I checked:**
  - **Input claim:** I read the Wisecoco listing image myself (7-inch-2000-nits-lcd-7.webp, local copy disp5v_img/w7.png). The barrel is labelled 'DC(5-24V)', and an input electrolytic near DC IN reads '100 35V' (my reading of the image). The two Type-C ports are labelled only '5V 2A' (10 W), below the 14 W D4 ceiling. The product page text still gives no input spec (live fetch 18 Oct 2026: $132, 'I2C', -20~70).
  - **4D fallback:** 12 V 540 mA on a barrel, per STACK line 136 and re-audit D citing the 4D datasheet R1.5. I did not re-read the PDF; it exceeded the fetch size.
  
  **Spec by spec:**
  1. **Supply voltage at the board.** 11.52-12.48 V (SYS12 +/-4%) sits in the middle of the 5-24 V window. The D36V28F5 path gives 4.80-5.20 V, minus the cable I*R drop at 2.8 A. That puts it at or below the 5 V floor of the barrel, so the current pick is actually worse for this board.
  2. **Current and power.** 14 W is 1.17 A at 12 V and 1.27 A at 11.0 V. The eFuse is set to 1.5 A (+/-10%, so 1.35 A worst case) and passes 2 x ILIM transients via ITIMER. That is 14.85-18 W available, against 16 W typical for the D36V28F5 (3.2 A at 36 V in), which falls further in a 50 C closed case. The eFuse loss is about 45 mW (28.3 mOhm). The D36V28F5 loses about 1.9 W at 14 W and 88%.
  3. **Efficiency.** No extra stage: D36V50F12 at 92% (already in the runtime model) vs the D36V28F5 at 88%. The board's LED boost and logic bucks also run at a lower step ratio from 12 V than from 5 V. That is a physics argument, not measured.
  4. **Spurs and ripple.** One fewer roughly 500 kHz switcher. Its fundamental sits about 10 kHz from 490 kHz and 18 kHz from 518 kHz, and its tolerance is unknown. The LC filter on DISP12 is kept.
  5. **Control.** EN on GP16 works the same way.
     - Off-state draw: the eFuse is at microamp level, vs 10-20 uA/V (140-280 uA) for the D36V28F5 asleep.
     - On-state Iq: 0.43 mA vs 2-3 mA.
     - Signals: PG (adjustable) and FLT vs PG only.
  6. **Protection.** The eFuse adds:
     - active ILIM (+/-10%) with a 500 ns short-circuit response;
     - adjustable OVLO with a 1.2 us response;
     - dV/dt soft start;
     - true reverse-current blocking (TPS25947 page, Rev C).
  
     Reverse polarity: the eFuse is rated only -15 V, but it sits behind the D36V50F12 and its 40 V reverse protection. The 27.6 V SMBJ17A transient is absorbed by that 50 V-rated regulator and never reaches the board.
  7. **Back-feed.** I confirmed the D36V28Fx back-feed fault myself on Pololu forum t/29129: Pololu staff measured VIN above 60 V with slightly over 5 V on VOUT, and the original poster saw 67 V. The eFuse path blocks reverse current, so it is strictly better here.
  8. **Size, heat and mechanics.** Zero modules, about 1.9 W less heat in the case, only a barrel lead.
  9. **Rest.** Driver-neutral (no software), nothing to counterfeit, no effect on any hard rule (DC only, no RF path, no loops).
  
  **SYS12 load.** The DISP12 load (0.25/1.1 A, up to 1.27 A) is already counted in the SYS12 1.0/2.9 A and about 4 A Lime-peak figures (STACK power table), and in the 4.2 A heat-soak gate. So the power budget does not change.
  
  **Contingency part.** The Botland unit is the identical SKU and EAN from a distributor Pololu lists ('offizieller Distributor' on the page), so it is not an analog and no spec changes.
- **Rejected:**
  1.
    - **Name:** Pololu D36V28F5 from Pololu direct (current pick)
    - **Why:** Same part, but 23.95 pre-tax plus US shipping, EU import VAT, EUR 3 per tariff line and EUR 2 UHF. For a board with a 5-24 V input it is also technically worse than DISP12: a 4.80 V minimum output (-4%) minus drop at 2.8 A sits at or below the 5 V barrel floor, 88% efficiency, about 1.9 W of heat, a VIN pump above 60 V on back-feed (forum t/29129), and one more 500 kHz spur source.
  2.
    - **Name:** Pololu D36V28F5 from TME (POLOLU-3782)
    - **Why:** Same part, but the price is not displayed ('no-prices'). Structured data gives a range of 21.51-24.41 USD with net/gross unclear, which is not below Botland. Visible stock is 0 while structured data says 29. Kept only as the fallback seller.
  3.
    - **Name:** Pololu D36V28F5 from Opencircuit (NL) / Optimus Digital (RO) / eBay.de
    - **Why:** Dearer: Opencircuit EUR 30.45 gross (EUR 25.20 net; WebSearch summary, not fetched), Optimus Digital 159.00 lei and out of stock (fetched), eBay.de EUR 33.99 (WebSearch summary, not fetched; third-party seller, not a Pololu-listed channel).
  4.
    - **Name:** Pololu D30V30F5 #4892
    - **Why:** Better on back-feed and current, but dearer (29.95, not re-fetched), with a 45 V input max and about 700 kHz, which would need a new C4 check. Not cheaper, so not an analog.
  5.
    - **Name:** Pololu D24V50F5 / D36V50F5
    - **Why:** Dearer (32.95 and out of stock; 39.95) and larger. The D24V50F5 input max is 38 V.
  6.
    - **Name:** Pololu D24V22F5 / D24V25F5
    - **Why:** Rated about 2.2-2.6 A, below the 2.8 A (14 W) need, and not cheaper (25.95-27.95).
  7.
    - **Name:** RECOM R-78K5.0-2.0
    - **Why:** 2.0 A, below the 2.8 A need. No EN (GP16 gating would need an extra load switch), no PG, no reverse/OTP/OVP listed, 4% load regulation, up to 120 mVp-p ripple.
  8.
    - **Name:** Traco TSR 3-2450
    - **Why:** Dearer (35.96). 3 A vs 3.2 A typ, 30 V input max vs 50 V, no PG, no reverse protection listed.
  9.
    - **Name:** MORNSUN K78xx-3AR3 (K7805-3AR3)
    - **Why:** 3.0 A rating vs 3.2 A typ, input 8-36 V (Mornsun series announcement), no reverse-polarity protection, no PG. EN/CTRL not verified for the 3 A model. G3 run found it 'not for new designs' with 0 DigiKey stock (not re-checked).
  10.
    - **Name:** Adafruit UBEC 5 V 3 A (#1385)
    - **Why:** Input cap 'might be rated 16V max', which the 27.6 V clamp transient exceeds. +/-5% accuracy, no EN/PG/reverse protection, 'a little noisy'.
  11.
    - **Name:** RECOM RPM5.0-3.0
    - **Why:** 20 V abs max (below the 27.6 V clamp), 3.0 A, LGA package needs reflow.
  12.
    - **Name:** DIY TPSM63604 module board
    - **Why:** Needs reflow (B3QFN), no input reverse protection (-0.3 V abs min), uncharacterised back-feed and 2-layer thermals, no measured reference board.
  13.
    - **Name:** Generic panel-mount 3 A USB socket buck (HKJ)
    - **Why:** Measured 134-280 mVpp noise, 12 mA idle, no EN, unknown frequency (C4 mask cannot be checked), QC can raise VBUS to 9/12 V, 36 x 51 mm.
  14.
    - **Name:** Generic 6-24 V to 5 V 3 A car USB module (HKJ)
    - **Why:** Stays in USB tolerance only to about 2 A. No overload, reverse or UV protection seen. 6-23 V input, below the 27.6 V clamp. 42-53 mV rms noise.
  15.
    - **Name:** Generic LM2596 module
    - **Why:** 2 A (3 A only with a heatsink), 65 kHz so the 8th harmonic at 520 kHz lands 2 kHz from 518 kHz (fails C4), about 200 mVpp, no EN, 43 x 21 mm, fake ICs common.
  16.
    - **Name:** Generic LT3800 10 A module
    - **Why:** 75 x 21 mm, no OTP seen, output drift, died at 60 V / 2.5 A in HKJ's test, no EN.
  17.
    - **Name:** Generic MP2307 (Mini-360 class)
    - **Why:** 23 V input max, 144.5 C hotspot at 2.5 A, high noise, no EN.
  18.
    - **Name:** Generic XL4015/XL4016 modules
    - **Why:** 144-216 kHz oscillator covers 162 kHz, 3rd harmonic covers 490/518 kHz, 48 kHz short-circuit foldback sits between the 40 and 60 kHz carriers (fails C4). No EN, large.
  19.
    - **Name:** Used Pololu D36V28F5
    - **Why:** No verified listing. Unknown back-feed history (VIN above 60 V stress) and clone risk, for a saving of a few USD at most.
- **Confidence:** high
- **Conditions or tests:** **Condition 1: Wisecoco's written D5 answer, before payment, must confirm:**
  - the 5-24 V barrel input (or at least 11.0-12.5 V) on the revision that actually ships;
  - the barrel size;
  - the current at 12 V at 25/50/100%;
  - NEW question: whether the Type-C VBUS pins are diode-isolated from the barrel input.
  
  If the answer shows a 5 V-only board, apply the contingency:
  - buy D36V28F5 #3782 from Botland at EUR 15.22 net and confirm stock at checkout, because the page text is contradictory ('Auf Lager' vs 'currently unavailable / next delivery'); fallback seller is TME;
  - add an output ideal diode or Schottky;
  - panel VBUS stays open;
  - 60 min at 2.8 A in the closed case at 14.0 and 16.4 V in, output within 4%, no thermal trip;
  - C4 spur gate.
  
  **Condition 2: goods-in bench on DISP12.** Feed the barrel at 11.0, 12.0 and 12.5 V with no USB cable attached:
  - Measure VBUS on both Type-C ports and the 5 V pin of the USB TP header. If any reads above 5.25 V (12 V passed through), those pins stay permanently unconnected, and re-audit D's fallback 'VBUS from the board's own 5 V side' is struck.
  - 20 cold starts through the eFuse dV/dt with no ILIM trip.
  - Full-white 100% must draw no more than 1.17 A at 12 V and 1.27 A at 11.0 V.
  - Because the 1.5 A ILIM has a 1.35 A worst-case floor, consider setting ILIM to about 1.7 A nominal (1.53 A minimum).
  
  **Condition 3: C4 HF+ A/B with the panel on DISP12, display on vs off.**
  - No line 3 dB or more above the floor within +/-5 kHz of 40, 60, 77.5, 162, 490, 518 or 4209.5 kHz.
  - Record the board's own converter frequency at 12 V in.
  
  **Condition 4: the SYS12 4.2 A heat-soak gate runs with the display at 100% on DISP12.** The load is already counted, but confirm it in the test log.
- **Stack changes:** **BOM**
  - Delete the optional line '5 V для дисплея: Pololu D36V28F5 #2, 1, 23.95, Pololu' (STACK.md line 300). The optional subtotal drops by 23.95.
  - Add a contingency note: 'only for a 5 V-only panel: D36V28F5 from Botland EUR 15.22 net + output ideal diode'.
  
  **Rows to edit in STACK.md**
  - DISP12 row and D4: replace '(якщо лише 5 V — окремий D36V28F5 #2 від SW)' with: DISP12 -> DC barrel (Wisecoco 'DC(5-24V)' / 4D 12 V 5.5 mm), 5 V-only contingency as above.
  - D5: drop the input-voltage question. Keep current at 12 V at 25/50/100% and barrel size. Add the Type-C VBUS isolation question.
  
  **Rails, budget and parts**
  - Rails and power budget: unchanged, since DISP12 is already inside SYS12's 2.9 A, about 4 A Lime peak and the 4.2 A gate.
  - Optional: raise the DISP12 eFuse ILIM to about 1.7 A nominal for tolerance margin.
  - Connectors: one DISP12-to-barrel lead (size from Wisecoco). No USB VBUS to the panel, as before. HDMI pin 18 Schottky unchanged.
  
  **Case, software and shopping**
  - Case: no second Pololu module by the lower vent, about 1.9 W less internal heat at 14 W.
  - Drivers and software: none (driver-neutral on Ubuntu 24.04 arm64).
  - Shopping: no Pololu-direct line for #2. If LAB5's D36V28F5 is also sourced at Botland (G3), the US Pololu order shrinks to the D36V50F12 and #2813 lines.
  
  **Already in the stack, not caused by this decision**
  - The TPS259470A (TPS25947 family) is a 2 x 2 mm VQFN-HR, while the search file lists no reflow as a build rule. Its J21, USB-C VBUS and DISP12 instances need PCBA assembly or a breakout.
  
  **Hard rules:** none affected (DC rail only).
- **Sources:**
  - https://www.wisecocodisplay.com/wp-content/uploads/2025/05/7-inch-2000-nits-lcd-7.webp (local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/disp5v_img/w7.png, read by me)
  - https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
  - https://www.pololu.com/product/3782
  - https://forum.pololu.com/t/strange-behavior-of-d36v28f5-pololu-3782/29129
  - https://www.ti.com/product/TPS25947
  - https://www.pololu.com/distributors
  - https://botland.de/abwartswandler/17169-d36v28f5-abwartswandler-5v-32a-pololu-3782-5903351242837.html
  - https://botland.store/converters-step-down/17169-step-down-voltage-converter-d36v28f5-5v-32a-pololu-3782-5903351242837.html
  - https://botland.com.pl/przetwornice-step-down/17169-d36v28f5-przetwornica-step-down-5v-32a-pololu-3782-5903351242837.html
  - https://www.tme.eu/en/details/pololu-3782/converter-modules/pololu/5v-3-2a-step-down-voltage-reg-d36v28f5/
  - https://www.optimusdigital.ro/en/5-v-step-down-power-supplies/8266-5v-32a-step-down-voltage-regulator-d36v28f5.html
  - https://opencircuit.shop/Product/5V.-3.2A-Step-Down-Voltage-Regulator-D36V28F5 (WebSearch summary only)
  - https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html (1.1253, 16 Oct 2026)
  - https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-pln.en.html (4.3700, 16 Oct 2026)
  - https://www.mornsun-power.com/html/news-detail/product-news/243.html (K78_3AR3 series, via WebSearch summary)
  - https://recom-power.com/pdf/Innoline/R-78K-2.0.pdf
  - https://www.digikey.com/en/products/detail/traco-power/TSR-3-2450/9382354
  - https://www.adafruit.com/product/1385
  - https://lygte-info.dk/review/Power%20Adjustable%20buck%20converter%20LM2596%20UK.html
  - https://lygte-info.dk/review/USBpower%203A%20USB%20socket%20for%2012V%20and%2024V%20UK.html
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md (DISP12/SYS12 power table, BOM line 300, D4/D5)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (items 34-35)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/g6_parts/pololu_d36v28f5_2_for_a_5_v_only_display.json

