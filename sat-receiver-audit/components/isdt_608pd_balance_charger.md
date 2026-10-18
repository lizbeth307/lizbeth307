# Isdt 608pd balance charger: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** ISDT 608PD balance charger (bench tier, qty 1). It does the monthly 4S LiPo-mode 4.20 V/cell balance of the Molicel P50B 4S1P pack through the node-N XT30 service port (5 A fuse, after the INA228 shunt) and the JST-XH 5-pin lead, with the main switch OFF. It is also the goods-in tool for per-cell voltage and IR.
- **Current pick:** ISDT 608PD. Specs per isdt.co/608pd.html: DC 5-30 V 240 W/10 A and USB-C PD3.1 5-28 V 140 W/5 A inputs; charge 0.5-10 A; balance 0.8 A/cell max; LiFe/LiPo/LiHV 1-6S; USB-C output 100 W; IPS screen with per-cell V and IR; abnormal-voltage and cell-count alarms; 0-40 C; 72.5x60x26.6 mm; 85 g. It has a BLE ISD Link app.
- **Current price usd:** STACK.md lists $32.99-42.99, which was never verified. Prices checked 18 Oct 2026:
  - DarwinFPV: $49.99 (US, before tax, in stock).
  - Pyrodrone: $42.99 (US).
  - FPV24 DE: EUR 43.90 incl. 19% VAT = $49.35. Landed in DE with EUR 6.90 shipping: EUR 50.80 = $57.10.
- **Decision:** keep
- **Chosen:** Keep the ISDT 608PD; only the seller changes.
  - Primary EU source: Modellbau Lindinger, Austria, product no. 9798048, manufacturer no. 608PD. ISDT's own dealer list (isdt.co/buy) names Lindinger as its Austrian dealer. The page says 'Auf Lager, Lieferzeit 1-3 Werktage'.
  - World/USD fallback: ISDT's official web shop (isdtshop.com, SKU FBM-608PD-CN), $33.00 (list $39.99). Adding it to the cart was accepted. It ships from China in 7-20 working days, and its policy says EU VAT is added at checkout on standard shipping.
  - Also genuine per isdt.co/buy, but price not verified: the ISDT AliExpress store 1101243810, MTTEC, rc-dome, Conrad, Droneshop.nl.
- **Chosen price usd:** Lindinger:
  - EUR 34.99 incl. 20% AT VAT = $39.33 (EUR 29.16 = $32.78 ex VAT).
  - Shipping: EUR 5.99 to AT/DE, so landed EUR 40.98 = $46.07. Other EU zone (FR/IT/NL/PL...): EUR 12.99, so EUR 47.98 = $53.93. Free shipping from EUR 89 (AT) / EUR 99 (DE).
  - VAT for non-AT buyers (OSS) not confirmed; EUR 34.99 is used as the conservative figure.
  
  ISDT official shop:
  - $33.00 + $4.99 standard shipping to DE/NL/PL/FR = $37.99, then EU VAT at checkout. That is about $45.21 landed in DE (19%) and $45.97-46.73 in NL/PL. Any customs duty is not included (unverified).
- **Saving usd:** Against the re-audit price of $49.99 (DarwinFPV):
  - Lindinger item price incl. VAT: $10.66 cheaper ($39.33).
  - Ex VAT: $17.21 cheaper ($32.78).
  
  Against the cheapest earlier EU landed price (FPV24 in DE, $57.10):
  - Lindinger landed in DE/AT: $11.03 cheaper ($46.07).
  - ISDT official shop, DE, VAT included: about $11.89 cheaper ($45.21).
  
  In other EU countries:
  - Against FPV24 zone 1 (EUR 57.80 = $64.97), Lindinger saves $11.04.
  - The ISDT official shop saves about $18 more, but ships from China and has the slower warranty path.
  
  The new verified price falls inside the old unverified STACK.md range of $32.99-42.99.
- **Equivalence proof:** It is the same part:
  - Same manufacturer SKU ('608PD'), sold new by a dealer ISDT itself lists (Lindinger, AT) or by ISDT's own store. That rules out counterfeit or grey units.
  - Lindinger's spec block matches isdt.co exactly: 5-30 V DC / 5-28 V USB-C, 240 W/10 A DC and 140 W/5 A USB-C, 0.5-10 A charge, USB-C discharge 100 W/5 A, 0.8 A/cell balance, XT60 output, 0-40 C, 72.5x60x26.6 mm, 85 g.
  - So every spec that matters is identical: 4S LiPo 4.20 V CV, 0.8 A/cell balance, 0.5-3 A usable charge, PD3.1 input from the stack's PD adapter, per-cell V/IR display, alarms, ISD Go USB firmware updates.
  
  The EU purchase adds:
  - statutory 2-year EU warranty
  - CE/GPSR responsibility on an EU dealer
  - no customs step.
  
  The hard rules are unchanged: the charger is bench-only, conducted, and never connects to the Q6A or any antenna. Its BLE radio is the same as before and was already accepted with mitigations.
  
  No other brand cheaper than about EUR 35 matches the 608PD; each one is worse on at least one spec, mainly balance current (details under 'rejected').
- **Rejected:**
  1.
    - **Name:** ToolkitRC M4 Pocket (1-4S, 80 W)
    - **Why:** Its balance current is 400 mA at 4.20 V against 0.8 A (toolkitrc.com/m4-pocket). It covers only 1-4S, 80 W, USB-C 5-20 V, and no IR measurement is published. It is better on three points: a LiPo Storage mode, a published balance accuracy below 0.005 V, and no radio listed. It is EUR 32.90 at FPV24 + EUR 6.90 = EUR 39.80 ($44.74) landed in DE, only $1.33 below the 608PD from Lindinger. It fails the not-worse rule and saves almost nothing.
  2.
    - **Name:** SkyRC B6neo 2 (SK-100225)
    - **Why:** Balance 550 mA. 1.77in TN 128x160 display against IPS. PD input 12-20 V/80 W against 5-28 V/140 W. Accuracy and IR are not published (skyrc.com/b6neo-series). At EUR 40.90 (FPV24) it now costs more than the 608PD at Lindinger.
  3.
    - **Name:** SkyRC B6neo (SK-100198) / B6neo+ (SK-100211)
    - **Why:** Balance 500 mA / 600 mA and TN display. B6neo PD input is 12-20 V/80 W. B6neo was out of stock at Unmanned Tech (GBP 29.95). The B6neo+ price was not checked. Both are worse on balance current.
  4.
    - **Name:** ISDT PD60
    - **Why:** Per isdt.co/pd60: balance 0.5 A/cell, input 5-20 V/60 W, LiPo 1-4S, charge current only in fixed 1/2/3/6 A steps, and no screen (no per-cell V/IR readout). The $26.39 AliExpress seller was not verified.
  5.
    - **Name:** ISDT Q6 Nano
    - **Why:** Per the ISDT manual: balance 0.5 A/cell and DC 10-30 V input only, so it needs an extra PD-trigger lead or a DC supply. 120 g. It is better on calibration, storage mode and having no radio, but worse on balance current and input. It was out of stock at GBP 30.41.
  6.
    - **Name:** ToolkitRC M7
    - **Why:** Balance 400 mA (toolkitrc.com/m7) and DC-only input. Worse.
  7.
    - **Name:** ToolkitRC M8P
    - **Why:** Balance 1000 mA is better, but input is DC 7-35 V only (no USB-C PD, and the core bench has no DC supply). It is 180 g and 99x72x35 mm in a 600 W class; price not verified and certainly not below EUR 35. It fails on compatibility and cost.
  8.
    - **Name:** ISDT 608PD at Unmanned Tech UK (GBP 28.89 incl. UK VAT)
    - **Why:** For EU buyers: GBP 24.08 ex UK VAT + GBP 14.95 'Standard International' shipping to DE/NL/FR (rates from the Shopify cart) = GBP 39.03 ($51.98) before destination VAT, about $61.85 in DE. The page shows both 'In stock' and a backorder notice, and the shop is not on ISDT's dealer list. It costs more landed than Lindinger.
  9.
    - **Name:** ISDT 608PD at Pyrodrone US ($42.99)
    - **Why:** Cheapest shipping to DE/NL is UPS Worldwide Expedited at $40.34, so $83.33 before import VAT (about $99 landed). Not viable for an EU buyer.
  10.
    - **Name:** ISDT 608PD at FPV24 DE (EUR 43.90)
    - **Why:** Genuine EU stock, but EUR 50.80 ($57.10) landed in DE and EUR 57.80 in EU zone 1. That is EUR 9.82 more than Lindinger for the identical part. FPV24 is not on ISDT's dealer list.
  11.
    - **Name:** ISDT 608PD from unidentified AliExpress sellers ($38.64-60.09)
    - **Why:** Store identity cannot be tied to ISDT, so counterfeit or grey-unit risk, and none is cheaper than Lindinger or ISDT's own shop. The genuine ISDT AliExpress store (1101243810, per isdt.co/buy) could not be priced because the page is JS-only.
  12.
    - **Name:** Used ISDT 608PD (Unmanned Tech 'Good' GBP 19.99; EU second-hand)
    - **Why:** The Unmanned Tech unit shows available=false in its Shopify JSON (verified). eBay and Kleinanzeigen returned 403. Used units have unknown history and no warranty, and the price gap to a new EU unit at EUR 34.99 is now small.
  13.
    - **Name:** iMAX B6 clones / cheali-charger DIY
    - **Why:** Balance 0.3 A/cell, DC 11-18 V only, 50 W. They copy a SkyRC trademarked product, which breaks the no-counterfeit rule.
  14.
    - **Name:** DPS-150 at 16.8 V + Daly passive balancing
    - **Why:** No per-cell end-of-charge control. The only per-cell guard is the Daly OVP (4.25 +/-0.05 V), there are no alarms, and the DPS-150 itself costs $73-75.
- **Conditions or tests:** Goods-in, for any seller:
  1. Genuine-unit check:
     - Buy only from an ISDT-listed seller (isdt.co/buy).
     - Read the firmware version with ISD Go for Windows over USB.
     - Do not update firmware from the phone app.
  2. Accuracy gate. Oscar Liang's table shows the screen resolves only 0.01 V, and the Daly OVP can trip at 4.20 V. So:
     - Compare each cell against the AN8008 at the JST-XH.
     - If any cell is off by more than 5 mV, run the ISD Link 'Voltage Calibration'. This needs BLE pairing: do it at home with the receiver off.
     - After a LiPo 4.20 V balance charge, every cell measured on the DMM must read 4.190-4.200 V, none above 4.200 V.
  3. Settings:
     - Charge current 2.5 A, never above 3 A (Daly COCP 10 +/-2 A, 5 A service-port fuse).
     - LiPo mode, 4S, balance mode.
  4. Radio check: tinySA 2400-2485 MHz receive-only max-hold scan with the charger idle, charging, and on the pairing screen.
  5. Power check:
     - FNB58 check of PD negotiation from the one-way PD wall adapter.
     - The Anker 737 (DRP) to 608PD test stays open, because the 608PD USB-C port is bidirectional.
  6. Storage: the 608PD has no storage mode (Oscar Liang). As of July 2024 the lowest settable USB-C-discharge end voltage was 4.15 V; a reader comment reports 3.7 V after a firmware update (unverified). Until a bench test on the delivered firmware shows a 3.8 V end voltage, reach the 50% storage state by running the receiver down.
- **Stack changes:** Bench BOM line 355 (ISDT 608PD): change the price from '32.99-42.99 / не перевірено' to EUR 34.99 incl. VAT = $39.33 at Modellbau Lindinger (AT, ISDT-listed dealer, in stock, 18 Oct 2026).
  - Shipping: EUR 5.99 to AT/DE, EUR 12.99 to the rest of the EU.
  - World ex-VAT reference: $33.00 + $4.99 shipping at the ISDT official shop.
  - Bench total: about -$10.66 against the re-audit's $49.99.
  - Optional: order other bench items from Lindinger to reach its free-shipping threshold (EUR 89 AT / EUR 99 DE).
  
  Add one lead to the battery-assembly kit (line 258 lists only the XT30 service lead and JST-XH 5-pin): an XT60-to-XT30 charge lead, 16 AWG, short.
  - Match its genders to the 608PD output and the node-N service port.
  - Check its polarity before first use.
  
  No changes to:
  - rails: the 16.8 V CV on node N stays below the SMBJ17A standoff
  - fuses: 5 A service-port fuse
  - Q6A drivers: the charger never connects to the Q6A
  - case: same 85 g / 72.5x60x26.6 mm in the Pelican bench case.
  
  Stack text corrections to carry:
  - The 608PD has BLE (FPV24 listing; Oscar Liang).
  - Voltage calibration exists, in the ISD Link app.
  - The display resolves 0.01 V/cell, so the ±10 mV gate is read on the AN8008.
  - The 608PD has no storage mode.
  - There is no Li-ion 4.10 V preset; use LiPo 4.20 V.
  
  Method limits:
  - The shared WebSearch budget was exhausted (one call refused), so all data come from direct fetches of primary pages and store Shopify JSON/shipping-rate endpoints.
  - Amazon.de returned 503, and the AliExpress store pages are JS-only, so neither could be priced.
- **Confidence:** high
- **Sources:**
  - https://www.isdt.co/608pd.html
  - https://www.isdt.co/buy
  - https://isdtshop.com/products/isdt-608pd
  - https://isdtshop.com/policies/shipping-policy
  - https://www.lindinger.at/de/RC-Elektronik/Ladegeraete-Netzgeraete/Ladegeraete/Ladegeraete-DC-12-50V/ISDT-608PD-Smart-Charger-DC-240W-10A-USB-C-140W-5A-1-6S-Lipo/9798048
  - https://www.lindinger.at/de/Modellbau-Lindinger/Versandkosten/
  - https://www.fpv24.com/de/isdt/isdt-608pd-lipo-ladegeraet-1-6s-240w-10a-usb-c-pd-xt60-smart-charger
  - https://www.fpv24.com/de/page/versandkosten
  - https://www.unmannedtechshop.co.uk/products/isdt-608pd-240w-dc-battery-charger
  - https://www.unmannedtechshop.co.uk/policies/shipping-policy
  - https://www.unmannedtechshop.co.uk/products/isdt-608pd-smart-charger-character-building-scratches-included-good
  - https://pyrodrone.com/products/isdt-608pd-dc-240w-10a-lipo-1-6s-usb-c-universal-pocket-charger
  - https://darwinfpv.com/products/isdt-608pd-lipo-charger-dc-240w-10a-usb-c-140w-5a-smart-digital-charger
  - https://oscarliang.com/isdt-608pd-charger/
  - https://www.toolkitrc.com/m4-pocket/
  - https://www.toolkitrc.com/m7/
  - https://www.toolkitrc.com/m8p/
  - https://www.skyrc.com/b6neo-series
  - https://www.isdt.co/pd60.html
  - https://www.isdt.co/down/pdf/Q6nano_EN.pdf
  - https://www.skyrc.com/iMAX_B6_Charger

