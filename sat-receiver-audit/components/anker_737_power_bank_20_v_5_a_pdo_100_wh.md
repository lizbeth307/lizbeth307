# Anker 737 power bank 20 v 5 a pdo 100 wh: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** Anker 737 Power Bank (PowerCore 24K, A1289): bench and carry-on USB-PD source. It feeds the IP2368 4S receiver charger (about 49-52 W), the ISDT 608PD, the Pinecil V2 (20 V/3 A, 60 W limit) and the Waveshare bench hub (USB-A 5 V/3 A). Tier bench, qty 1.
- **Current pick:** Anker 737 PowerCore 24K A1289 (EAN/GTIN 194644098728) from Anker US.
- **Current price usd:** 109.99 (anker.com US, in stock, 18 Oct 2026). anker.com/de lists EUR 109.99 incl. VAT (about USD 123.64 at the stack's 1 EUR = 1.1241 USD). anker.com/eu-en shows it sold out.
- **Decision:** keep
- **Chosen:** Keep the Anker 737 A1289, because no cheaper analog survived verification. Buy the identical SKU from a cheaper authorised EU retailer: MediaMarkt.de or Saturn.de, EUR 82.99 incl. 19 % VAT, free shipping, listed as in stock with 1-2 working-day delivery. Fallbacks: other offers in the billiger.de list (playox EUR 83.69 + 5.99 shipping), then anker.com/de at EUR 109.99, then Anker US at USD 109.99.
- **Chosen price usd:** 93.29 (EUR 82.99 x 1.1241, VAT included). Source: billiger.de offer list for EAN 0194644098728, Oct 2026. The 6-month low there is EUR 73.17; billiger marks today's price as "high".
- **Saving usd:** 16.70 against the USD 109.99 baseline. Against the EU official store (anker.com/de, EUR 109.99) the saving is EUR 27.00, about USD 30.35. The part does not change.
- **Equivalence proof:** 1. It is the same SKU, so it is not worse on any spec. The billiger.de listing carries EAN 0194644098728 (listed since July 2022, 24,000 mAh). That matches the gtin and barcode 194644098728 in the anker.com US and EU-en product data for the A1289. One offer in the same list names A1289011.
  
  2. Specs carried over unchanged (Anker spec table):
  - USB-C1 input: 5V3A, 9V3A, 15V3A, 20V5A, 28V5A.
  - USB-C1 and USB-C2 output: 5V3A, 9V3A, 15V3A, 20V5A, 28V5A.
  - USB-A: 5V3A, 9V2A, 12V1.5A.
  - 140 W total. 630 g. 155.7 x 54.6 x 49.5 mm.
  - 24-month Anker warranty (US page). An EU seller adds the 2-year statutory guarantee.
  
  3. Measured data (techtest.org, 2022, updated Apr 2023):
  - Delivered energy: 77.21 Wh at 20 V/3 A and 74.89 Wh at 20 V/5 A.
  - Recharge: 48 min at about 126 W peak on a 140 W charger; 55 min on 100 W.
  - Limit: while USB-A is in use, both C ports are capped at 65 W.
  
  4. The display shows Battery Cycle, Battery Health, Total Input and Total Output. Anker's FAQ says a new unit reads 0 cycles and 100 % health, which makes a genuine-and-new check possible on receipt.
  
  5. Seller and legality: MediaMarkt and Saturn are large authorised German retailers, so this is a legal sale with a VAT invoice and low counterfeit risk.
  
  6. Hard rules: unaffected. A power bank has no RF function, so receive-only, conducted-only and no-loop rules still hold. 86.4 Wh nominal is under 100 Wh, so it can still go in cabin baggage.
  
  7. Correction to reaudit D: the 737 is not DRP on both ports. Anker lists only USB-C1 as an input, and techtest says input goes through the primary C port. USB-C2 is therefore output-only by spec and carries the full 20V5A/28V5A set. This is the property no cheaper candidate matched.
- **Rejected:**
  1.
    - **Name:** UGREEN Nexode 25000mAh 200W (SKU 35525): EUR 76.99 at de.ugreen.com (about USD 86.55, verified in the store JSON), USD 89.99 with a code at us.ugreen.com
    - **Why:** Only EUR 6 cheaper than the same 737 at MediaMarkt/Saturn, and worse on verified specs (official spec table):
  - Input is 65 W max on each port (20V/3.25A, PD3.0/PD2.0 input only) vs 140 W. The 737 measured 48 min to full; at 65 W this bank would take about twice as long.
  - USB-C1 and USB-C2 are both listed as inputs, so there is no source-only port, and the reaudit-D DRP risk with the IP2368 COUT (Try.SRC) board and the ISDT 608PD returns.
  - 28 V only on C1, which is a DRP port.
  - The display shows battery, V, A, input and output only: no cycle count or health.
  - No independent capacity or ripple measurements found.
  Equal or better: 90 Wh, 20V5A on both C ports, USB-A 5V3A, 609 g.
  2.
    - **Name:** Anker Laptop Power Bank 25K 165W A1695 (EUR 69.59 via billiger.de, about USD 78.23; USD 119.99 at Anker US)
    - **Why:** Anker's spec page:
  - Every USB-C port and built-in cable is input and output (DRP), so there is no source-only port.
  - No 28 V/EPR (20V5A is the top PDO).
  - Input 100 W, about 2 h to recharge vs 48-55 min.
  - Retractable built-in cables are a wear item.
  - The display has no cycle or health readout.
  3.
    - **Name:** UGREEN Nexode 25000mAh 145W 3-port (SKU 90597A): EUR 69.99 at eu.ugreen.com (about USD 78.68), USD 79.99 with a code in the US
    - **Why:** EU spec table:
  - Input is USB-C1 only, 65 W.
  - C2 output 65 W max, with no PDO table, so 20V5A on a source-only port is not available.
  - Output protocols are listed as PD3.0/PD2.0 even though 140 W on C1 needs PD 3.1 EPR, so the PDOs are inconsistent and unverified.
  - LED percentage display only. USB-A 22.5 W, with 5V3A not stated.
  4.
    - **Name:** INIU B64 27,000 mAh 140W (EUR 79.99 at eu.iniushop.com per search A; out of stock at the INIU US store per search B)
    - **Why:** Delivered energy is better (techtest 2 Oct 2024: 87.0 Wh at 20V/3A, 86.0 Wh at 20V/5A; rated 99.9 Wh), but:
  - C2 is only 45 W (20V/3A).
  - With USB-A in use the split is 100 W + 12 W + 12 W, so USB-A cannot carry the hub's 5V/3A (15 W) and C2 falls to 12 W.
  - Recharge takes 1:25-1:30 h.
  - The display has no cycles, health or temperature.
  - About EUR 3 cheaper at best.
  The reader report of a soldering-iron shutoff was not found on re-fetch, so it is not used as a reason.
  5.
    - **Name:** INIU Cougar P63-E1 25,000 mAh 100W (USD 66.99-69.99, EUR 66.99)
    - **Why:** No 28 V. C2 has no 20 V (15V3A max). The three-port total falls to 80 W. Input 65 W. Techtest measured only 66.9 Wh at 20V/5A and throttling from 100 W to 65 W. The display shows charge level only.
  6.
    - **Name:** UGREEN 25000mAh 165W with built-in cables (SKU 55995, EUR 63.99 DE)
    - **Why:** No per-port PDO table, input figure or port roles published. The main outputs are captive cables (a wear item that cannot be swapped for a certified 5 A e-marked cable). Not provably not-worse.
  7.
    - **Name:** Baseus EnerFill FC41 25000mAh 145W (USD 67.99 with a code / EUR 89.99)
    - **Why:** Input 65 W. Built-in cables. No PDO table, and neither 20V5A nor a source-only port is verified. The spec source (store FAQ) is low-confidence. The EU price is above the 737's EUR 82.99.
  8.
    - **Name:** CUKTECH 20 / P23 25,000 mAh
    - **Why:** No verified official-seller price (cuktech.com shows a 999.00 placeholder). C2 is 45-60 W, so 20V5A and 28 V are only on the DRP C1. Input 100 W max (techtest: 1:50 h). Throttles to about 60 W after about 22 min at 130 W. Output interruptions were seen with one laptop.
  9.
    - **Name:** VOLTCRAFT VC-C909 27,000 mAh 140W (Conrad)
    - **Why:** Current price unverified (conrad.de returned 403). C2 is only 20 W. Recharge takes 1:52 h. 655 g. No health or cycle readout (techtest, Mar 2025).
  10.
    - **Name:** KOOSEED 983SP-145W 27,000 mAh
    - **Why:** Generic OEM with no verified price. No 28 V. 100 W is not sustained below about 25 % charge. Recharge takes 1:38 h. The display has no W, health or cycle readout.
  11.
    - **Name:** AsperX AX2410 24,000 mAh
    - **Why:** Price unverified. Lower energy at 20 V (76.4 Wh). No 28 V. C2 45 W. Recharge takes 1:39 h. A reader reports no USB-A overcurrent protection (unverified safety red flag).
  12.
    - **Name:** SHARGE HyperTower 170
    - **Why:** Price unverified. No 28 V. 75.7 Wh at 20V/3A (less than the 737). Output drops to 60 W at about 20 % charge. Recharge takes 1:17 h. 688 g. Integrated cables.
  13.
    - **Name:** UGREEN PB205 145W 25,000 mAh
    - **Why:** Not cheaper (about EUR 120 at the 2023 test). No PPS. C2 45 W. Output resets under load. Recharge takes about 2 h. Level-only display.
  14.
    - **Name:** Sandberg All-in1 27000 PD 240W
    - **Why:** No verified price. The 140 W output is a captive cable and is not sustained (falls to 100 W at about 50 %). Recharge takes 1:47 h.
  15.
    - **Name:** Used, open-box or refurbished A1289
    - **Why:** No price could be obtained (eBay, Back Market and Geizhals returned 403). Cell wear and the warranty are unknown. It is not equal until an acceptance test passes, and the new unit is already only EUR 82.99.
  16.
    - **Name:** DIY SW6306/IP5389 bank with 6x 21700
    - **Why:** No UN 38.3 type test, so it cannot go in cabin baggage. The stack's own power.json records output resets, about 100 C MOSFETs and balancer faults. Rejected on the rules.
  17.
    - **Name:** An existing 60 W-or-more bank already owned
    - **Why:** Unknown PDOs, energy and port roles. It is worse until the FNB58 proves 20V5A, 60 W sustained at 20 V and 77 Wh or more at 20V/3A. At most a budget fallback, not an analog.
- **Confidence:** high
- **Conditions or tests:** Price confidence is medium, so re-check at checkout:
  - The EUR 82.99 comes from the billiger.de aggregator (Oct 2026). The MediaMarkt and Saturn pages returned 403 and could not be read directly.
  - Both shops deliver within Germany only. Outside Germany, use the local MediaMarkt or Amazon.de (ASIN B09VPHVT2Z, Model A1289, now titled "Anker Prime Power Bank 24000 mAh 140 W"). Its price is unverified: a techtest widget showed EUR 74.96 with no timestamp. The 6-month low is EUR 73.17.
  - Check the listing says A1289 / EAN 194644098728, not the A1695 or the 26K model.
  - No WebSearch was available: the shared budget was used up and my one call was refused. Everything here comes from WebFetch and curl on primary pages.
  
  Goods-in tests:
  - Label shows A1289, EAN 194644098728, and a Wh figure no higher than 100 (86.4 Wh nominal; Anker's page does not print Wh, so the label must). Mass about 630 g.
  - Display reads Battery Cycle 0 and Health 100 % (Anker FAQ).
  - FNB58 PDO list on C1 and on C2: 5/9/15/20 V at 3-5 A, plus 28V5A with a 240 W e-marked cable.
  - FNB58 discharge at 20 V/3 A delivers about 75 Wh or more (techtest: 77.2).
  - Measure ripple at 20 V/3 A and 5 V/3 A. No published data exists for any bank.
  
  DRP charging matrix, 10 plug cycles each, logging FNB58 direction:
  - 737 USB-C2 to the receiver USB-C (through the TPS259470A) with the IP2368 COUT board: the board must sink, with no reverse VBUS.
  - 737 USB-C2 to the ISDT 608PD.
  - The same two tests on C1, for the record.
  Field charging from the bank counts as proven only after the C2 tests pass. Until then, a one-way PD wall adapter remains the certain source.
  
  Load split:
  - While USB-A feeds the hub, both C ports are capped at 65 W (techtest). The Pinecil stays at its 60 W limit (IronOS PD Mode = No Dynamic, non-EPR cable), and the IP2368 at about 52 W fits.
  - Do not run Pinecil, receiver charging and the hub together above 140 W total.
- **Stack changes:** 1. BOM row "Банк живлення":
  - Part unchanged: Anker 737 A1289.
  - Price 109.99 becomes 93.29 (EUR 82.99 incl. 19 % DE VAT, MediaMarkt.de/Saturn.de via billiger.de, 18 Oct 2026; EAN 0194644098728). Status: verified via aggregator.
  - Fallbacks: anker.com/de EUR 109.99, Anker US USD 109.99.
  - Core total falls by USD 16.70.
  - Shopping order row 8 (weeks 2-3) switches the 737 to this seller.
  
  2. Port routing (power section, D7, packing notes):
  - 737 USB-C2 (output-only by Anker spec) feeds the receiver's IP2368 USB-C input and the ISDT 608PD input.
  - 737 USB-C1 (the DRP port) is for recharging the bank (140 W PD 3.1 charger) and for the Pinecil (a sink-only device, so DRP is harmless there).
  - USB-A 5V/3A feeds the Waveshare hub.
  
  3. Correct reaudit D's statement "Anker 737 is DRP": C1 is DRP; C2 is output-only per Anker's spec, but bench-confirm this with the FNB58 before relying on it. Rewrite the DRP charging-matrix test to use C2.
  
  4. The note "Budget alternative: existing ≥60 W bank" stays only as an FNB58-qualified fallback, not an equivalent.
  
  5. No changes to rails, connectors, drivers (no software; Ubuntu 24.04 arm64 unaffected), case or Pelican layout. The existing 5 A e-marked C-to-C cable is still required; add one 240 W EPR cable for the 28 V/ISDT check.
- **Sources:**
  - https://www.anker.com/products/a1289
  - https://www.anker.com/de/products/a1289
  - https://www.anker.com/eu-en/products/a1289
  - https://www.billiger.de/pricelist/3996283292-anker-737-power-bank-24000-mah-schwarz
  - https://techtest.org/die-anker-737-powercore-24k-powerbank-im-test-mit-140w-usb-c-port-zur-besten-powerbank/
  - https://www.amazon.de/dp/B09VPHVT2Z
  - https://de.ugreen.com/products/ugreen-nexode-powerbank-200w-25000mah
  - https://us.ugreen.com/products/ugreen-nexode-power-bank-25000mah-200w-with-smart-digital-display
  - https://eu.ugreen.com/products/ugreen-nexode-power-bank-200w-25000mah
  - https://eu.ugreen.com/products/ugreen-145w-power-bank-for-laptop
  - https://www.anker.com/products/a1695-anker-power-bank-25000mah-165w
  - https://techtest.org/iniu-power-bank-27000mah-140w-im-test-inius-erste-echte-flaggschiff-powerbank/
  - https://techtest.org/voltcraft-vc-c909-test-140w-27-000-mah-powerbank-zum-kampfpreis-lohnt-sich-der-kauf/ (from search B, not re-fetched)
  - https://techtest.org/eine-der-besten-powerbanks-cuktech-20-im-test-25-000-mah-und-140w-usb-c/ (from search B, not re-fetched)
  - https://techtest.org/iniu-p63-e1-powerbank-mit-tinycells-im-test-25-000-mah-100-w/ (from search B, not re-fetched)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/pb_dl/anker_us.html (GTIN 194644098728, FAQ cycle/health, 24-month warranty)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/pb_verify/bil_pl.html (billiger.de offer list)

