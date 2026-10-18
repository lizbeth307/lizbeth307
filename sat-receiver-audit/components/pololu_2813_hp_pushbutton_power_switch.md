# Pololu 2813 hp pushbutton power switch: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** Main power switch: Pololu #2813 Big Pushbutton Power Switch with Reverse Voltage Protection, HP (node N to SW, 4S pack; qty 2, 1 spare)
- **Current pick:** Pololu #2813 HP from pololu.com, qty 2. Button on A to GND (on-only). Pico GP13 OFF pulse and TLV3012 UV hold are diode-ORed through BAT54 into OFF.
- **Current price usd:** 17.90 for 2 (8.95 each; 8.23 at 5+), pololu.com, 18 Oct 2026, status Rationed. This excludes VAT and shipping. For an EU buyer the landed cost adds import VAT (19-27%, so at least $21.30 at 19%), the EUR 3 per tariff line customs duty (postal/IOSS consignments up to EUR 150), the EUR 2 Union handling fee (expected from about 1 Nov 2026) and US shipping (not fetched).
- **Decision:** keep
- **Chosen:** KEEP the same part, the genuine Pololu #2813 HP, but BUY IT FROM BOTLAND (botland.de, index PLL-05117, EAN 5903351244862). Botland is an authorised Pololu distributor for DE, PL and CZ on pololu.com/product/2813/distributors. No different design survived verification, so this changes only the seller, not the part.
- **Chosen price usd:** EUR 7.99 each gross with 19% DE VAT, EUR 6.72 net. For 2: EUR 15.98 gross / EUR 13.44 net, which is $17.98 gross / $15.12 net at the ECB rate of 1.1253 (16 Oct 2026). Checked on Botland's own price and stock API on 18 Oct 2026: the regular price is the same as the shown price, so it is not a promotion; 20 in stock; no purchase limit set; backorder not allowed. Shipping to DE: GLS EU from EUR 4.69, free from EUR 100. Inference, not checked at checkout: for other EU countries the gross price follows destination VAT (OSS) while the EUR 6.72 net stays the same.
- **Saving usd:** VAT-exclusive like for like: $2.78 for 2 ($1.39 each; $15.12 vs $17.90). Landed in the EU: at least $3.32 for 2 before Pololu's shipping, duty and handling fee ($17.98 gross vs at least $21.30). The real figure is higher, because Pololu-direct also pays the EUR 3 per line duty, the EUR 2 handling fee from about 1 Nov 2026, and US shipping. A Botland order under EUR 100 pays shipping from EUR 4.69 (DE). Pololu-direct also has to pay shipping, so the saving is not wiped out if both orders carry the same items.
- **Equivalence proof:** Same SKU from an authorised channel, so every spec is identical. Proof:
  (1) pololu.com/product/2813/distributors lists 'Botland B.Derkacz sp.k.' for Germany, Poland and the Czech Republic, shipping from Poland.
  (2) The Botland listing title and JSON-LD say 'Pololu 2813', 'HP', SKU PLL-05117, GTIN 5903351244862. Its spec block matches the Pololu table: 40 V abs max, 4.5-32 V recommended, 6 A at 55 C, 16 A at 150 C, 90 A max, green LED, 20 x 25 x 4 mm, 2.7 g. Those are the Big-HP column values, not the MP #2812 ones (4.0 A / 8 A / 40 A).
  (3) Pololu's own spec table, columns LV / SV / MP / HP, parsed from the raw HTML: HP has 13 mOhm at 4.5 V and 8.6 mOhm at 10 V combined max, 6.0 A to a 55 C MOSFET and 16 A to 150 C (footnote: 12 V, 22 C ambient, still air), 90 A max, about 120 uA/V on-state, <0.2 uA off, 0.8 x 1.0 x 0.16 in, 2.7 g, reverse-voltage protection, A/B/ON/OFF/CTRL inputs.
  Every critical spec for this stack is therefore unchanged: 4S pack at 13.2-16.8 V; about 40 mV and 0.18 W at the 4.6 A peak; off-state <0.2 uA for the about 170-185-day standby budget; on-only on A; OFF above 1 V from the 3.3 V GP13 and the push-pull TLV3012; built-in reverse protection relied on by J21; starts off at power-up (16.8 V is mid-range, not 'near the upper end'); static latch with no oscillator.
  Remaining risk: old Botland stock or mis-picking (the MP #2812 looks identical). This is covered by the goods-in check under conditions_or_tests.
- **Rejected:**
  1.
    - **Name:** Pololu #2812 Big Pushbutton Power Switch MP ($5.95)
    - **Why:** WORSE on current and on-resistance (Pololu table, MP column): 40 mOhm at 4.5 V and 30 mOhm at 10 V vs 13 / 8.6; 4.0 A vs 6.0 A to a 55 C MOSFET; 8 A vs 16 A to 150 C; 40 A vs 90 A max. The 4.6 A with-Lime peak is above its 4.0 A figure. Drop is about 138 mV vs 40 mV, and dissipation about 0.63 W vs 0.18 W. Only its off-state current is better (<0.01 uA).
  2.
    - **Name:** Pololu #2815 Big MOSFET Slide Switch HP ($8.49; Eckstein EUR 8.03)
    - **Why:** FUNCTION INCOMPATIBLE. It has the same MOSFETs but no latch and no OFF input. It cannot do on-only pushbutton start, the Pico OFF pulse after poweroff, or the TLV3012 holding OFF under UV, and the Pico runs from the switched rail. Off-state current is not published. It saves only $0.46 each.
  3.
    - **Name:** Pololu #2809 Mini Pushbutton SV ($4.95)
    - **Why:** WORSE: 2.0 A to 55 C, 4.3 A to 150 C, 7.2 A max, 90 / 50 mOhm. This is below even the 3.4 A load without the Lime.
  4.
    - **Name:** Pololu #2808 Mini Pushbutton LV ($4.95)
    - **Why:** WORSE on voltage: 2.2-16 V recommended and 20 V abs max, against a 4S pack at 16.4-16.8 V with SMBJ17A clamping. Also 3.0 A to 55 C and about 210 uA/V on-state.
  5.
    - **Name:** Adafruit #1400 Push-button Power Switch Breakout ($5.95)
    - **Why:** WORSE (verified on adafruit.com): 3-14 V DC, 3 A with a DMG3415U ('gets a little toasty at continuous 3A'), 0.5 uA quiescent vs <0.2 uA. No reverse-polarity protection; the body diode back-feeds. Toggle only, with no documented on-only mode. It would be over-voltaged on 4S.
  6.
    - **Name:** SparkFun Soft Power Switch PRT-26993 ($7.32) / SPX-17870 (retired)
    - **Why:** WORSE (verified on sparkfun.com): 1.8-5.5 V max, 2 A continuous / 4 A peak, <1 uA quiescent, no reverse protection stated. The Mk1 was rated to 12 V and is retired and out of stock.
  7.
    - **Name:** DIY latch with 2x Infineon IPD90P04P4L-04 back-to-back P-FETs
    - **Why:** WORSE or UNPROVEN (datasheet Rev 1.2 checked locally): IDSS max 1 uA vs the board's <0.2 uA. Pair RDS(on) max is 13.2 vs 13 mOhm at 4.5 V. VGS limit +5/-16 V needs a gate clamp for a 16.8 V pack. Power-up state, debounce, OFF-vs-A priority and noise immunity are all unmeasured. BOM price not verified (distributors blocked). Fallback only if #2813 stock fails, after the bench proof.
  8.
    - **Name:** DIY TI LM74502 + N-FETs + separate latch
    - **Why:** WORSE: shutdown current 0.9 uA typ / 1.5 uA max vs <0.2 uA. Its hysteretic charge pump (turn-on 10.3-13 V above VS) is an unmeasured spur risk for the HF+ LF/NAVTEX gate. Needs an extra latch circuit. No price, no measured build.
  9.
    - **Name:** Generic AliExpress bistable or self-locking MOSFET pushbutton modules, and Pololu clones
    - **Why:** UNVERIFIED: no listing, datasheet or measurement was found (WebSearch budget used up), so off current, RDS(on), voltage, reverse protection and power-up state are unproven. Clones copy a design Pololu calls patented, and counterfeit FETs are a risk.
  10.
    - **Name:** Used Pololu #2813
    - **Why:** Not found (eBay 403). Earlier surge or over-current damage to the MOSFETs cannot be seen without measurement, it carries a mix-up risk with the look-alike #2812, and has no warranty. Saves at most a few dollars.
  11.
    - **Name:** Pololu #2813 from Eckstein GmbH (authorised, DE)
    - **Why:** Same part but MORE EXPENSIVE: EUR 8.63 gross / EUR 7.25 net (about $9.71 / $8.16) vs Botland's EUR 7.99 / 6.72. In stock, 1-3 days.
  12.
    - **Name:** Pololu #2813 direct from pololu.com to the EU
    - **Why:** Same part but higher landed cost: $8.95 net plus import VAT, the EUR 3 duty per tariff line (postal/IOSS consignments up to EUR 150), the EUR 2 handling fee from about 1 Nov 2026, and US shipping. Stock is 'Rationed'.
  13.
    - **Name:** Not evaluated (marked, not claimed)
    - **Why:** LTC2955-based DIY: analog.com returned 503. TME, Kamami and RobotShop EU: Cloudflare 403. Electrokit, Vanallesenmeer, 3Sigma and Robot Italy: search URLs returned 404 or redirected. Robot Italy's EUR 13.10 from the search agent is not cheaper anyway.
- **Conditions or tests:** Goods-in check, for each Botland unit:
  - Confirm the board is the Big HP: green LED, 0.8 x 1.0 in, 5 mm terminal pads. The MP #2812 looks identical.
  - At room temperature, VIN to VOUT drop must be 40 mV or less at 4.6 A (about 8.6 mOhm).
  - Off-state current at 16.8 V must be 0.2 uA or less.
  - If the drop is near 138 mV, the unit is an MP: reject it.
  
  Bench tests that STACK already requires, unchanged:
  - With the TLV3012 holding OFF high, pressing the button on A must leave the switch off. If it turns on, route the button line through the supervisor (D1).
  - 100 pack connections at 16.8 V must all come up OFF.
  - 20 USB-PD plug/unplug cycles, device OFF and ON: no spontaneous state change. Pololu: 'does not maintain state through power disruptions or excessive noise'.
  - C4 gate (2): log the #2813 MOSFET temperature at 4.2 A for 60 min in the closed enclosure, and at 4.6 A for 30 min at 50 C ambient.
  - C4 gate (1): HF+ narrowband A/B with no new lines.
  
  Shipping condition: the saving is largest when the #2813 order is combined with other Botland items. Over EUR 100 it ships free to DE; otherwise GLS from EUR 4.69.
- **Stack changes:** 1. BOM row 'Головний вимикач': seller Pololu → Botland (botland.de PLL-05117). Price: 2 x EUR 7.99 gross (EUR 6.72 net), about $15.12 net / $17.98 gross, verified 18 Oct 2026. Status changes from Rationed to 20 in stock. No electrical, connector, rail, driver, firmware or case change; it is the same board and footprint.
  
  2. Week-1 shopping order (step 6). Optional, and a decision for those parts' verifiers, not this one: Botland also stocks the rest of the Pololu order at lower net prices (verified 18 Oct 2026 via the Botland API):
  - D36V50F12 #4095: EUR 31.27 gross / 26.28 net (about $29.57 net vs $39.95), 10 in stock.
  - D36V28F5 #3782: EUR 18.11 / 15.22 (about $17.13 net vs $23.95), 27 in stock, 50 more due 30 Oct.
  - 2x D36V50F12 + D36V28F5 + 2x #2813 = EUR 96.63 gross, just under the EUR 100 DE free-shipping line.
  - Moving the whole Pololu order to Botland also removes the non-EU duty and handling fees, and the 'Rationed' supply risk.
  
  3. Carry the re-audit D wording fixes into v2:
  - '6 A at 55 C' means about 6 A heats the MOSFETs to 55 C in 22 C still air; it is not an ambient rating.
  - Recommended limit is 32 V; 40 V is abs max.
  - Not a safety disconnect; the BMS and the 7.5 A fuse do that job.
  
  4. Add the goods-in HP/MP check above to the bring-up list.
- **Confidence:** high
- **Sources:**
  - https://www.pololu.com/product/2813
  - https://www.pololu.com/product/2813/distributors
  - https://www.pololu.com/product/2812
  - https://www.pololu.com/category/121/pololu-power-switches
  - https://botland.de/elektronische-und-digitale-schalter/5117-grosser-push-mosfet-schalter-hp-45-40v-16a-mit-ruckstromschutz-pololu-2813-5903351244862.html
  - https://botland.de/edge_api/v1/products?ajax=1&ids=5117
  - https://botland.de/edge_api/v1/orderability?ajax=1&id_product=5117
  - https://botland.store/digital-switches/5117-large-hp-mosfet-switch-45-40v16a-with-back-current-protection-pololu-2813-5903351244862.html
  - https://botland.de/abwartswandler/16387-d36v50f12-abwartswandler-12v-45a-pololu-4095-5904422344436.html
  - https://botland.de/abwartswandler/17169-d36v28f5-abwartswandler-5v-32a-pololu-3782-5903351242837.html
  - https://eckstein-shop.de/Pololu-Big-Pushbutton-Power-Switch-with-Reverse-Voltage-Protection-HP
  - https://www.adafruit.com/product/1400
  - https://www.sparkfun.com/products/26993
  - https://www.infineon.com/assets/row/public/documents/10/49/infineon-ipd90p04p4l-04-datasheet-en.pdf
  - https://www.ti.com/lit/ds/symlink/lm74502.pdf
  - https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (items 34-35, EU duty and handling fee)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p2813v/dl/pol2813.html (raw Pololu spec table, LV/SV/MP/HP columns)
  - NOTE: WebSearch budget was exhausted for this turn (0 successful searches by this verifier); all checks used direct WebFetch/curl of primary pages.

