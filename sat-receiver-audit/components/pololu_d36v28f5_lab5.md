# Pololu d36v28f5 lab5: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** Pololu D36V28F5 (#3782), LAB5 5 V buck rail (SW node 12.0-16.8 V, SMBJ17A clamp up to about 27.6 V, then a 3 A fuse). Loads: Pico, CH334F hub, IMU pack, fans, HF+, LAB USB-A, 2x LT3045 LNA rail. Current 0.6 A typical, 2.0 A peak, 2.3 A peak in the with-Lime default build. Tier core, Power, qty 1.
- **Current pick:** Pololu D36V28F5 (#3782) from Pololu direct or the DigiKey Marketplace (ships from Pololu, US)
- **Current price usd:** 23.95 at qty 1 (22.03 each at qty 5). Pololu status: Rationed (Active and Preferred). For an EU buyer, US shipping, EU import VAT and the flat customs duty since 1 Jul 2026 come on top (duty amount not verified).
- **Decision:** keep
- **Chosen:** Keep the Pololu D36V28F5 (#3782) and change the seller to Botland, which Pololu's own distributor list names for CZ (botland.cz), DE (botland.de) and PL (botland.com.pl). Botland index PLL-17169, EAN 5903351242837. botland.store is the B2B store and needs a VAT ID. If Botland has no stock or does not deliver to the user's country, buy from TME (POLOLU-3782, also a Pololu-listed distributor) or from Pololu direct.
- **Chosen price usd:** 17.13 net / 20.38 including 19% DE VAT (botland.de: EUR 15.22 net / EUR 18.11 gross). botland.com.pl: PLN 64.96 net / PLN 79.90 gross = USD 16.73 / 20.57. Rates: ECB reference rates of 16 Oct 2026 (1 EUR = 1.1253 USD = 4.37 PLN; verified). Shipping: botland.de from EUR 4.69 (GLS) in DE, free over EUR 100; botland.store GLS EU from EUR 8.07. Shipping is shared with the rest of an order.
- **Saving usd:** 6.82 net-to-net against the 23.95 list price (28%). 3.57 even after 19% German VAT. Against Pololu direct landed in the EU (US shipping + import VAT + flat duty), the saving is larger, but no exact number is given because the duty and shipping were not verified. An analog would save at most about 1-2 (the TI TPSM63604 path, rejected below).
- **Equivalence proof:** The chosen item is the same SKU, not an analog. Botland's pages give Pololu #3782, EAN 5903351242837, maker Pololu Corporation (Las Vegas, NV), country of origin USA. Botland states that it is an official Pololu distributor and that the parts are original. pololu.com/distributors confirms this: Botland is listed for the Czech Republic, Germany and Poland. So every spec is identical to the baseline (pololu.com/product/3782):
  - input 5.3-50 V
  - 5 V +/-4% output
  - 3.2 A typical at 36 V in (2.5-4 A range)
  - 80-90% efficiency
  - about 500 kHz under load, power-save above 20 kHz
  - Iq 2-3 mA
  - reverse-voltage protection to 40 V
  - over-current, short-circuit and over-temperature protection, output UV/OV protection, soft start
  - PG open drain (+20%/-10%) and EN (sleep below 1.2 V, wake above 1.35 V, 100 k pull-up)
  - 17.8 x 20.3 x 8.8 mm, two M2 holes, 0.1 in pins
  The back-feed behaviour is also the same. No spec is traded away.
  
  No other candidate survived the adversarial check (see the rejected list):
  - Every cheaper other-brand part is worse in at least one spec that matters: input voltage, current rating, protections, build method, or measured thermals and noise.
  - The only cheaper part that is better in some specs (TI TPSM63604) is worse in reverse protection, in build method (needs reflow and our own layout), and in back-feed and thermal behaviour that nobody has qualified.
- **Rejected:**
  1.
    - **Name:** TI TPSM63604RDLR 36 V / 4 A power module plus external RT, FB divider and Cin/Cout
    - **Why:** I checked the datasheet (SLVSGJ5) and DigiKey. Price: USD 12.48 at qty 1 (296-TPSM63604RDLRCT-ND, 4,266 in stock, Active). With about USD 3 of passives, the total is about 15.5, which is only about 1.6 below the Botland net price, before reflow or PCBA and before DigiKey shipping and VAT.
  
  Better: 4 A rating; FB accuracy +/-1%; fixed frequency in FPWM (200 kHz-2.2 MHz by RT, or EN/SYNC); Iq 7 uA non-switching; hiccup OCP; thermal shutdown at 168 C.
  
  Worse or unproven:
  - Abs max VIN 42 V and recommended 36 V, against 50 V. This still covers the 27.6 V clamp.
  - No input reverse-polarity protection (VIN abs min -0.3 V), against 40 V on the Pololu. The upstream #2813 is reverse-protected, but its rating is not stated.
  - No real output OVP: only a PG flag at 107% and a 0.5 mA SW pull-down.
  - The -3 A negative current limit in FPWM means a back-fed VOUT can be boosted into VIN, and this has not been characterized. VIN through the high-side body diode reaches about 4.5 V, above the 3.95 V start threshold.
  - No-load current in FPWM is not specified.
  - RθJA 33.1 C/W and the SOA curves are for a 4-layer 2 oz board; ours is a 2-layer board.
  - The B3QFN (MSL3) needs reflow, which breaks the 'no reflow' build requirement.
  - It is our own layout, not a tested assembly.
  It fails 'not worse'. Keep it as the C4 fallback only.
  2.
    - **Name:** RECOM RPM5.0-3.0 (DigiKey USD 6.90)
    - **Why:** I checked the RECOM RPM-3.0 datasheet: input 3-17 V, absolute maximum input 20 V, 3.0 A max. A full pack is 16.8 V and the SMBJ17A clamp reaches about 27.6 V, so the abs max is exceeded on a transient. 3 A is below 3.2 A and cannot pass the 3.5 A / 60 min gate. Ripple is 60 mVp-p. It is an LGA part that needs reflow.
  3.
    - **Name:** MORNSUN K7805-3AR3 (DigiKey USD 3.37)
    - **Why:** 3 A rating cannot pass the 3.5 A / 60 min gate. 'Not for new designs', 0 in stock, backorder unavailable. Its switching frequency, ripple and reverse/OV protection are unverified (DigiKey links the wrong datasheet). It is 32.2 x 9.1 x 14.9 mm, so a new footprint would be needed.
  4.
    - **Name:** Same part from Pololu direct / DigiKey Marketplace
    - **Why:** Identical part, but it ships from the US. Landed EU cost = 23.95 + shipping + import VAT + the flat duty since July 2026 (amount unverified), which is clearly above Botland's USD 20.38 gross.
  5.
    - **Name:** Same part from Pimoroni (UK)
    - **Why:** Out of stock on 18 Oct 2026. GBP 17.50 including UK VAT (about USD 23). Post-Brexit customs plus the EU flat duty and import VAT make it dearer once landed.
  6.
    - **Name:** Same part from TME (POLOLU-3782)
    - **Why:** Not rejected on quality: TME is a Pololu-listed distributor. But the page shows no price (its structured data gives USD 21.51-24.41) and stock is contradictory (0 shown, 29 in the data). It is not shown to be cheaper than Botland, so it is kept as the fallback seller.
  7.
    - **Name:** Same part from botland.store (B2B)
    - **Why:** Same EUR 15.22 net / 18.11 price, but it sells only to registered businesses with a VAT ID. Use the consumer storefronts (.de / .com.pl / .cz) instead.
  8.
    - **Name:** Generic MP2307 'Mini-360-class 3 A' buck module
    - **Why:** HKJ measurement (verified): 144.5 C hotspot at 2.5 A (12 V in, 5 V out), overheats at 3 A, up to 25 mA no-load, 340 kHz, 23 V max input, trimpot output, high noise. Fails on current, thermals, input margin, accuracy, noise and protections.
  9.
    - **Name:** Generic LM2596 module
    - **Why:** Per HKJ (via search B; not re-fetched by me): rated 2 A, about 200 mVpp ripple, 140 C heatsink at 2 A, about 65 kHz (puts harmonics into the 40-518 kHz watch list), 43 x 21 x 14 mm, and fake chips are common.
  10.
    - **Name:** Generic 7 A LT3800 + MCU module
    - **Why:** Per HKJ (via search B): 62 x 44 x 18 mm, about 200 kHz, 'fairly high' noise, extra MCU and pre-regulator noise sources. Does not fit and would fail C4.
  11.
    - **Name:** Generic MT3908 2 A module
    - **Why:** 2 A rating is below the 2.3 A load and the 3.5 A gate.
  12.
    - **Name:** DIY TI LMR33640 / TPS62933F buck
    - **Why:** Prices not verified. LMR33640 has light-load foldback (no forced PWM per search B, not re-verified). TPS62933F is 3 A / 30 V, below the 3.5 A gate. Neither has 40 V reverse protection; TPS62933F also has no PG. Layout-dependent EMI and thermals; no measured board exists. Same not-worse failures as TPSM63604.
  13.
    - **Name:** Used D36V28F5
    - **Why:** No listing verified (eBay 403). Unknown back-feed history (VIN pump above 60 V can stress the input cap and IC). The saving would be a few USD at most.
  14.
    - **Name:** Pololu D30V30F5 (#4892)
    - **Why:** Better back-feed behaviour and about 700 kHz, but dearer (USD 29.95; Botland EUR 24.58 net per search A) and 45 V max input. Not a cheaper analog.
- **Confidence:** high
- **Conditions or tests:** Sourcing conditions (the part does not change):
  1) Botland stock is ambiguous: both botland.de and botland.com.pl show 'in stock / Auf Lager' and also a 'notify when available' form. Confirm the quantity at checkout.
  2) Delivery country: botland.de structured data lists DE only, botland.com.pl lists PL and LT, botland.cz covers CZ, and botland.store (B2B, VAT ID) uses GLS EU. If no Botland store delivers to the user's country as a consumer, use TME POLOLU-3782 (check price and stock) or Pololu direct.
  3) Incoming check: Pololu silkscreen and item number on the board, and 5.0 V +/-4% at no load and at 2.3 A from 16.4 V.
  
  Existing gates stay unchanged (the current part has not yet passed them):
  - C4 spur gate: HF+ A/B with LAB5 load steps of 0.3-3 A. Note that about 500 kHz sits 10 kHz from 490 kHz and 18 kHz from 518 kHz, and Pololu gives no frequency tolerance.
  - 3.5 A for 60 min in the closed enclosure at 14.0 V and 16.4 V input.
  - 500 kHz ripple on the LT3045 rail with LAB5 at 4.8 V.
  - 2.3 A on the 3 A fuse for 30 min at 50 C.
  - Back-feed fixes stay in: Schottkys on Pico VSYS and on the IMU pack, SMBJ17A on SW, and the flashing rule.
  
  If C4 or the heat gate fails, the qualified escape path is TPSM63604:
  - FPWM at a fixed fsw (for example 1 MHz, or SYNC from a clock) chosen clear of the C4 lines.
  - An EN divider from VIN with UVLO of about 10 V, so that a back-fed VIN of about 4.5 V cannot start it. This is a design proposal, not bench-verified.
  - Rely on the #2813 reverse protection and confirm its reverse rating.
  - Keep the SMBJ17A.
  - Use a 4-layer power board, or measure thermals on the 2-layer board.
  - Reflow or PCBA.
  - Re-run all gates.
  The D36V50F5 stays the escape route if LAB5 load exceeds 2.5 A.
- **Stack changes:** BOM sourcing only:
  - Change the LAB5 seller line to Botland (botland.de / botland.com.pl / botland.cz), EUR 15.22 net / EUR 18.11 gross (DE VAT) = USD 17.13 / 20.38 at ECB 1.1253 (16 Oct 2026). Fallback sellers: TME POLOLU-3782, then Pololu direct.
  - Correct search A's FX assumption (1.17 to 1.1253): its USD 17.8 / 21.2 figures are too high.
  - Note that Botland's distributor status is now confirmed on pololu.com/distributors.
  - Bundle with other Botland items to share shipping.
  
  No changes to rails, connectors, pin plan, footprint, drivers (none involved; driver-neutral on Ubuntu 24.04 arm64), or case and vents.
  
  Optional note in the C4 fallback section: name TI TPSM63604RDLR (datasheet-verified, USD 12.48 at DigiKey) as the forced-PWM/SYNC fallback, with the conditions above.
  
  Search coverage was incomplete: the WebSearch budget was exhausted (shared cap). Other Pololu-listed EU resellers could not be checked: exp-tech 429, eu.robotshop 403, ptrobotics bot-block, kamami 403, eckstein/electrokit/gotronic search URLs 404, Optimus Digital 0 results. BerryBase lists only the D36V50F5 (EUR 34.95). A slightly cheaper EU reseller may exist.
- **Sources:**
  - https://www.pololu.com/product/3782
  - https://www.pololu.com/distributors
  - https://botland.de/abwartswandler/17169-d36v28f5-abwartswandler-5v-32a-pololu-3782-5903351242837.html
  - https://botland.de/suche?s=D36V28F5
  - https://botland.com.pl/przetwornice-step-down/17169-d36v28f5-przetwornica-step-down-5v-32a-pololu-3782-5903351242837.html
  - https://botland.store/converters-step-down/17169-step-down-voltage-converter-d36v28f5-5v-32a-pololu-3782-5903351242837.html
  - https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
  - https://www.tme.eu/en/details/pololu-3782/converter-modules/pololu/5v-3-2a-step-down-voltage-reg-d36v28f5/
  - https://www.ti.com/lit/ds/symlink/tpsm63604.pdf
  - https://www.digikey.com/en/products/result?keywords=TPSM63604RDLR
  - https://recom-power.com/pdf/Innoline/RPM-3.0.pdf
  - https://www.pololu.com/product/2813
  - https://lygte-info.dk/review/Converter%20DC-DC%203A%204.75-23V%20to%201.0-17V%20UK.html
  - https://forum.pololu.com/t/strange-behavior-of-d36v28f5-pololu-3782/29129
  - https://www.berrybase.de/search?search=D36V28F5
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lab5_verify/dl/tpsm63604.txt
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lab5_verify/dl/rpm3.txt

