# Radxa armor 7056a heatsink or stepped cu: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_071e1025-145`_

- **Part:** Q6A cooling set: Radxa Armor 7056A (AE036) heatsink (top cover only), or the stepped Cu block; path-1 40 mm 5 V fan; 5 V display-channel blower (path 2)
- **Current pick:** STACK v1: ALLNET Armor 7056A $9.90 + Adafruit 6101 $4.95 + blower estimate. The re-audit (reaudit_D, which governs) changed the path-1 fan to the Noctua NF-A4x10 5V non-PWM (3-pin with tach) and kept the 6101 as a spare only. The blower still has no model.
- **Current price usd:** STACK v1: 19.85-24.85. Governing re-audit set: 33.47-38.47 (ALLNET Armor 9.90 + NF-A4x10 5V 18.57 = QuietPC GBP 13.96 + blower estimate 5-10), plus 4.95 for the 6101 spare. These are not landed prices for a buyer in Europe; see equivalence_proof.
- **Decision:** keep
- **Chosen:** KEEP all three parts. (1) Heatsink: the same Radxa Armor 7056A. For the Europe build, buy it at TinyTronics (SKU 007949) inside the step-1 TinyTronics board order. Non-EU build: ALLNET inside the ALLNET order. The stepped Cu block stays option (A) on performance, not as a cheaper analog. (2) Path-1 fan: Noctua NF-A4x10 5V non-PWM. No cheaper fan is not-worse. (3) Blower: still unspecified, so it stays an estimate. (4) Adafruit 6101: spare only, rides the Adafruit order.
- **Chosen price usd:** Same parts, so the BOM basis is unchanged at 33.47-38.47. Real Europe landed price (my calculation, EUR 1 = USD 1.1241):
  - Armor: 13.49 (TinyTronics EUR 12.00 incl. 21% NL VAT; zero extra shipping because TinyTronics charges per parcel up to 23 kg).
  - NF-A4x10 5V: 17.87 (Alternate.de EUR 15.90 incl. VAT), plus 8.98 shipping (EUR 7.99) if it ships alone.
  - Blower: 5-10 estimate. A branded 5 V 5015 blower with a datasheet costs 8.38-12.28 at DigiKey.
  - Set: 36.36-41.36, or 45.34-50.34 if the fan ships alone; 6101 spare +4.95.
- **Saving usd:** 0.00. No analog survived. The '-4.91 Arace saving' in both searches is refuted for Europe. Arace landed is about 30.93 (DE) / 32.66 (NL) against 13.49 at TinyTronics, so Arace would cost about 17-19 more. Separately, the 18.57 Noctua figure is not a verified EU landed price; the verified EU option is 17.87 + 8.98 shipping.
- **Equivalence proof:** HEATSINK: same part, every spec equal.
  - Radxa's 7056A page lists the Dragon Q6A, Cubie A7A, ROCK 5A and ROCK 5C. Material: Mg-Si aluminium with 3D fins. Contents: top and bottom covers, 2 thermal pads, 4x CM2.5x8x4 screws.
  - ALLNET's listing (AE036, $9.90, available) gives a 70x56x15 mm top cover and a 85x56x15 mm bottom cover.
  - TinyTronics 007949 (EUR 12.00 incl. VAT, 6 in stock) has the same contents (top, bottom, 4 bolts, 2 pads), 85x56 mm and 106 g. It names the 'Cubie Q6A', which is a naming error for the Dragon Q6A.
  - The Radxa Q6A docs accessories page lists no cooler at all, so no other heatsink is proven Q6A-compatible.
  
  LANDED COST, from Shopify cart quotes on 18 Oct 2026:
  - Arace ships DDU (its shipping policy says duties and VAT are paid on arrival). Armor alone: DE $21.00 (7-20 days) or UPS $36; NL $22. That gives 4.99 + 21 = 25.99, plus 19% VAT = $30.93 before the carrier fee. Arace has nothing else in this order (the Q6A is sold out there), so the shipping cannot be shared.
  - ALLNET alone: $16.97 to DE/NL, so $31.98-32.51 landed. Inside an ALLNET order, adding the Armor to 2x microSD raised shipping from $15.40 to $18.53 (+$3.13), so $15.51-15.77 landed.
  - TinyTronics inside the board order is therefore the cheapest real EU source.
  
  FAN: no cheaper candidate meets every governing spec. The specs are ≥8.2 m3/h, ≥1.78 mmH2O, ≤17.9 dB(A), ≤0.25 W/0.05 A, tach, 40x40x10 mm. QuietPC and Alternate confirm the Noctua figures, plus SSO2, MTBF >150k h and a 6-year warranty. Every cheaper datasheet-backed fan draws more power, and most also lose noise, the tach or the 10 mm thickness (see rejected).
  
  BLOWER: no baseline model exists, so 'not worse' cannot be tested; it stays an estimate.
  
  RULES: all parts are passive cooling with no RF function and no loops. The receive-only and conducted-only rules are untouched.
- **Rejected:**
  1.
    - **Name:** Radxa Armor 7056A AE036 from Arace, $4.99
    - **Why:** Same part, but the price is not real for Europe. Shopify quote on 18 Oct 2026: shipping $21 (DE) / $22 (NL), sold DDU. Landed about $30.93-32.66 plus the carrier fee, against $13.49 at TinyTronics. It ships alone because Arace has nothing else for this order in stock.
  2.
    - **Name:** Radxa Armor 7056A from ALLNET, $9.90 (STACK v1 seller)
    - **Why:** Not rejected as a part. For Europe it is dearer landed: $31.98-32.51 alone, or $15.51-15.77 inside an ALLNET order (shipping +$3.13 measured with 2x microSD in the cart). Keep it as the non-EU source and as the fallback if TinyTronics' 6 units sell out.
  3.
    - **Name:** Sunon MF40100V2-1000U-A99, $4.87 (DigiKey, 10,325 in stock)
    - **Why:** Datasheet D04114210G-02: 0.47 W rated / 0.55 W max vs 0.25 W; 20.6 vs 17.9 dB(A); no tach. The tach variant -G99 has 0 stock and a 30-piece minimum. Rated life is L10 70k h at 40 C, which cannot be compared with MTBF >150k h. Worse in power, noise and tach.
  4.
    - **Name:** Sunon MF40200V3-1000U-G99, $10.88 (40x40x20, tach)
    - **Why:** Datasheet D04115080G-01: 0.38 W rated / 0.44 W max vs 0.25 W (worse). It is 20 mm thick, and the fit in the 55-60 mm case is unproven. DigiKey shows no stock for this exact part (the 344 belongs to a substitute) and a 26-week lead time. Better in flow (6.3 CFM), pressure (27.4 Pa) and noise (16.5 dB(A)), with a tach. A near-miss that needs an explicit user decision; not adopted.
  5.
    - **Name:** Same Sky CFM-4020V-050-165-20, $9.43 (40x40x20, tach)
    - **Why:** 87 mA max (about 0.44 W) vs 0.25 W, 20 mm thick, no published bearing life. 6.3 CFM and 16.5 dBA. Same near-miss as the Sunon 20 mm fan; not adopted silently.
  6.
    - **Name:** Same Sky CFM-4010V-058-206-20, $8.00
    - **Why:** 550 mW and 20.6 dB(A): worse in power and noise. Bearing life is unpublished.
  7.
    - **Name:** Same Sky CFM-4010V-150-157-20, $8.58 (12 V, tach)
    - **Why:** 460 mW vs 0.25 W, and it needs the 12 V rail. Better in noise and pressure, but not not-worse.
  8.
    - **Name:** Sunon MF40100V1-1000U-G99, $6.74
    - **Why:** 0.68 W and 27.3 dB(A): much louder and higher power.
  9.
    - **Name:** Sunon HA40101V4-1000U-A99, $4.40 (12 V)
    - **Why:** No tach (the stall alarm is lost), about 0.37 W, needs the 12 V rail, 26-week lead time. The search data was not re-fetched by me; it fails on the tach alone.
  10.
    - **Name:** TinyTronics 'Sunon Fan 40x40x10mm 12V' = EE40101S2-999-A, EUR 3.00
    - **Why:** Sleeve bearing, 23 dBA, about 0.96 W (80 mA at 12 V), 35,000 h life, no tach, 12 V. Worse in every key spec, although it would ride the board order.
  11.
    - **Name:** Adafruit 6101 as the path-1 fan, $4.95
    - **Why:** About 1 W (0.2 A), no tach (the page says 'no PWM/feedback pin'), no rpm, airflow, noise or life data. Stays a spare only. The Sunon MF40100V2 is better specified than the 6101 but saves only $0.08 and lacks the 6101's included screws and grills, so the spare is not changed.
  12.
    - **Name:** Noctua NF-A4x10 5V PWM / NF-A4x10 FLX (12 V)
    - **Why:** Not cheaper (EUR 13.80-15.90). The PWM version is louder and draws more power at full DC speed; the FLX needs 12 V.
  13.
    - **Name:** AliExpress stepped Cu Q6A cooler (item 1005010333340740)
    - **Why:** Price could not be verified (the page returned empty; earlier agents saw $17-30), above the Armor's $13.49. The only measurement is one anecdotal '55 C stressed' report (btop, no ambient). Not a cheaper analog; it stays the re-audit's option (A) on performance merit.
  14.
    - **Name:** Pi-style 40x40 sink on a shared pad, twin small sinks, Pi 5 Active Cooler, CM5 cooler, DIY Cu shim, used parts
    - **Why:** These break the separate SoC/LPDDR5 contact rule, or lack any Q6A fit or measurement. The Pi 5 cooler is mechanically incompatible with the Q6A's 4 corner holes, and the bearing wear of a used fan cannot be proven.
  15.
    - **Name:** Blower candidates: Same Sky CBM-5015BF/CF, TinyTronics 5015 (EUR 3.50)
    - **Why:** With no baseline model, no not-worse test is possible. The TinyTronics 5015 is 12/24 V only with no datasheet, so it fails the 5 V requirement. The angle-B price of $6.28 for the CBM-5015CF-055-391 was not confirmed: DigiKey shows the -055-391-20 at $8.92, and the cheapest 5 V CF is the -035-293 at $8.38.
- **Confidence:** high
- **Conditions or tests:** Heatsink:
  - Order it at TinyTronics in the step-1 board order and check stock at checkout (6 left). VAT for a non-NL EU destination may differ (unverified).
  - On arrival, confirm the Radxa 7056A/AE036 identity and contents (2 pads, 4 screws).
  
  Bench gates (unchanged by this step):
  - STEP v1.21 fit-check of the top cover on M2.5 standoffs.
  - Separate SoC (paste/PTM7950) and LPDDR5 (0.5-1 mm pad) contacts.
  - SoC-to-inlet ≤3.5 K/W at about 10 W stress-ng for 10 min, with no passive trip.
  - At least 2.7 m3/h per air path through the mesh plus foam.
  - HF+/RTL noise-floor A/B with the fan and blower on/off. Motor EMI is unpublished for every fan.
  - Tach read test.
  
  Near-miss: the Sunon MF40200V3-1000U-G99 or Same Sky CFM-4020V-050-165-20 could replace the Noctua only if the user explicitly accepts +0.13-0.19 W and +10 mm depth. That would save about $5-16 against the Alternate Noctua, riding the DigiKey order (EU price and VAT are a model). It would then need the case-depth fit check and the same airflow and EMI gates.
  
  Limits of this check: the WebSearch budget was exhausted, noctua.at returned 429, and geizhals/idealo/TinyTronics search returned 403. Further EU sellers of the NF-A4x10 5V, QuietPC's EU VAT and shipping, and carrier customs fees are unverified.
- **Stack changes:** 1) BOM cooling line, heatsink:
  - EU source: TinyTronics 007949, EUR 12.00 incl. VAT ($13.49), added to the step-1 TinyTronics order.
  - Non-EU source: ALLNET $9.90 within the ALLNET order.
  - Delete the 'Budget: Arace $4.99' note; its landed cost is about $31-33.
  
  2) Fan line, per the re-audit: NF-A4x10 5V non-PWM.
  - EU: Alternate.de EUR 15.90 incl. VAT plus EUR 7.99 shipping (verified), or QuietPC (EUR 13.80 on .co.nl; UK seller, VAT and shipping unverified).
  - Do not fit the included L.N.A. (it lowers airflow).
  - The 6101 stays a spare.
  
  3) Wiring knock-on from adding a tach (my engineering note, not a datasheet claim):
  - STACK C6 switches 2-wire fans with a low-side FET. With a 3-wire tach fan, low-side switching floats the fan ground when off. The tach is then invalid and can back-feed into a 3.3 V Pico pin.
  - Fix: switch path-1 high-side (P-MOSFET plus a small driver, or a 5 V load switch) and keep the flyback diode.
  - Tach input: open-collector, pull-up of about 10 kOhm to 3.3 V (never 5 V), series resistor of about 1-4.7 kOhm into a spare Pico GPIO.
  - Firmware: ignore the tach while the fan is off and for about 2 s after switch-on. Stall alarm = no pulses for more than 2 s while on (Noctua gives 2 pulses per revolution).
  
  4) Blower stays an estimate. If a branded part with a 70 C rating is required, the realistic price is $8.38-12.28 (Same Sky CBM-5015CF/BF via the DigiKey order), not $5-10. Choose it after the channel-flow bench test.
  
  5) No changes to rails (LAB5 5 V unchanged), drivers or the Q6A. The case is unchanged unless the user accepts a 20 mm near-miss fan, which would add 10 mm of depth on path 1.
- **Sources:**
  - https://arace.tech/products/radxa-armor-case-7056a.js
  - https://arace.tech/policies/shipping-policy
  - https://arace.tech/cart/shipping_rates.json (Shopify quote, DE/NL, 18 Oct 2026)
  - https://shop.allnetchina.cn/products/radxa-heatsink-7056a.js
  - https://shop.allnetchina.cn/cart/shipping_rates.json (Shopify quote, Armor alone and with 2x microSD, 18 Oct 2026)
  - https://www.tinytronics.nl/en/tools-and-mounting/enclosures/others/radxa-metal-case-7056a-for-rock-5a-5c-and-cubie-q6a-a7a
  - https://www.tinytronics.nl/en/delivery-information
  - https://www.tinytronics.nl/en/mechanics-and-actuators/fans
  - https://www.tinytronics.nl/en/mechanics-and-actuators/fans/sunon-fan-40x40x10mm-12v
  - https://radxa.com/products/accessories/armor-case-7056a/
  - https://docs.radxa.com/en/dragon/q6a/accessories
  - https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
  - https://quietpc.co.nl/nf-a4x10-flx-5v
  - https://www.alternate.de/Noctua/NF-A4x10-5V-Geh%C3%A4usel%C3%BCfter/html/product/1232067
  - https://www.sunonusa.com/wp-content/uploads/2026/05/MF40100V2-1000U-A99-D04114210G-02-0_Ref.pdf
  - https://www.sunonusa.com/wp-content/uploads/2026/02/MF40200V3-1000U-G99-D04115080G-01-1.pdf
  - https://www.digikey.com/en/products/result?keywords=MF40100V
  - https://www.digikey.com/en/products/result?keywords=MF40200V3-1000U-G99
  - https://www.digikey.com/en/products/result?keywords=CFM-4010V
  - https://www.sameskydevices.com/product/thermal-management/dc-fans/axial-fans/cfm-4020v-050-165-20
  - https://www.digikey.com/en/products/result?keywords=CBM-5015
  - https://www.sameskydevices.com/product/thermal-management/dc-fans/centrifugal-blowers/cbm-5015cf-055-391
  - https://www.adafruit.com/product/6101

