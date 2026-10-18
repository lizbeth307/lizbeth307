# Fnirsi fnb58 std no radio: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** FNIRSI FNB58 Std (no Bluetooth). USB/USB-C PD tester and logger. Bench tier, Bench electronics group, qty 1.
- **Current pick:** FNIRSI FNB58 Std (SKU FNB58, no radio) from fnirsi.com.
- **Current price usd:** 53.99 on the fnirsi.com USD storefront, ex tax. I re-read the product JSON on 18 Oct 2026: Std $53.99 (compare-at $88.99), BT $58.99. For EU delivery the same JSON gives EUR 52.05 for Std (?country=DE/FR/NL/ES/IT/AT), which is about $58.57 at 1.1253. Whether that EUR price includes VAT is not verified; FNIRSI only says it provides a "duty payment service" for EU orders under $150.
- **Decision:** replace_conditionally
- **Chosen:** The same part, a genuine FNIRSI FNB58 Std, bought through a cheaper channel: AliExpress EU storefront, item 1005004665244812 (it is US item 3256804478930060; the redirect confirms the mapping). 1,000+ sold, 4.9 stars, ships from CN, free shipping. No different model survived. Order of preference: (a) this channel, if all the conditions hold; (b) BerryBase DE at EUR 49.90 incl. VAT if it comes back in stock (sold out on 18 Oct 2026); (c) otherwise keep fnirsi.com.
- **Chosen price usd:** 50.18 = EUR 44.59 incl. 19% DE VAT, free shipping (AliExpress DE search grid, taxRate 0.19, read 18 Oct 2026). That is about $42.17 ex VAT. Cheaper single-model listings exist at EUR 41.99 (1005008908357736, 69 sold, 4.7 stars), about $47.25, and EUR 42.59 (1005007468954965 / 1005007468735974 / 1005007469052955), about $47.93. Not verified: the store name, whether the lowest grid price is the Std variant, and whether checkout adds the EU EUR 3 per-item low-value-parcel duty.
- **Saving usd:** Landed in the EU: about $8.39 (EUR 7.46) against fnirsi.com's EU price of EUR 52.05, if that price includes VAT. About $5.0 if the EUR 3 EU parcel duty is charged only on the AliExpress order. Up to about $19.5 if fnirsi.com adds VAT on top of EUR 52.05. Against the $53.99 USD base line on an ex-VAT basis: $11.82. Zero if any condition fails, because then the part is kept. The claimed '$37.00' saving (about $17) is NOT real (see rejected).
- **Equivalence proof:** It is the identical product, so every spec that matters is equal by identity, provided the unit is a genuine Std:
  - VBUS 4-28 V, and down to 0 V when powered from the PC port (needed for the backfeed checks).
  - Current 0-7 A and 0-140 W, which covers the 5 A C-C cable and the INA228 points at 0.5, 2 and 4 A.
  - External 16-bit ADC with a 5-digit display. Bidirectional current indication for the DRP matrix.
  - PD2.0/3.0 PDO read and trigger, PD listener, e-marker, cable resistance, QC/FCP/SCP/AFC detection.
  - Ripple capture up to 4 Msps; curves at 2-100 sps.
  - USB-A male in and out, USB-C in and out, micro-USB PC port. Same metal/plastic housing and the same 2.0 in LCD.
  - Linux: the same USB HID ID 2E3C:5558. I read the current baryluk logger source: it matches VID 0x2E3C, PID 0x5558 and still sets refresh = 1.0 s for the FNB58 at line 305, so the stack's refresh = 0.003 patch, the udev rule and labd stall detection carry over unchanged.
  - No radio in the Std, so the QUIET rule holds.
  
  What is NOT equal, stated openly:
  - Manufacturer warranty. FNIRSI's warranty page: "2-year warranty (only available for orders purchased directly from fnirsi.com)". The 30-day price guarantee is also fnirsi.com only.
  - An AliExpress order relies on AliExpress buyer protection and EU consumer-law claims against a non-EU trader, which are harder to enforce.
  - Channel authenticity. A non-official store adds clone, refurb or BT-swap risk. That is why the conditions below are mandatory.
  
  The accuracy evidence is the same for either channel: FNIRSI publishes no accuracy figure for the FNB58, so the INA228 reference still needs a cross-check, as already planned.
- **Rejected:**
  1.
    - **Name:** AliExpress 'FNB58 at $37.00' (US item 3256804478930060), as quoted by both searches
    - **Why:** The price is not real for a normal buyer. The grid data for that item shows salePrice $37 with the tag 'New shoppers save $51', source 'welcomedeal' / 'card_new_user_welcomedeal_atm', and original price $88. It is a first-order welcome deal, in the US storefront, ex VAT (taxRate 0). The same item in the EU storefront (1005004665244812) is EUR 44.59 incl. VAT, which is the price used above.
  2.
    - **Name:** Other AliExpress US sale prices $35.53-38.72 (3256809533464638, 3256809533574431, 3256808428483720, 3256809536773368, 3256807874596765)
    - **Why:** These are also new-shopper welcome-deal prices: tags 'New shoppers save $6.5 / $7', source welcomedeal. The regular prices are $42.03-45.22, ex VAT. They are not landed EU prices.
  3.
    - **Name:** FNIRSI FNB-C2 ($38.99 at fnirsi.com)
    - **Why:** FNIRSI's own text: 'standard USB-C 24-PIN male and female ports' only, with no USB-A and no micro-USB, so it cannot sit inline at the Q6A/LAB USB-A ports without non-compliant A-C adapters. Ripple capture is 20 ksps-2 Msps against 4 Msps. Current is 0-6.5 A against 7 A. No Linux logger: baryluk supports only 0483:003A, 0483:003B, 2E3C:5558 and 2E3C:0049, and its PC software is Windows/Mac. It is better in V range (50 V), ADC (20-bit) and published accuracy (V ±(0.2‰+2), I ±(0.5‰+2)), but it fails ports, Linux logging and ripple rate.
  4.
    - **Name:** FNIRSI FNB48P Std ($35.99)
    - **Why:** The back label in FNIRSI's own product image reads '...24V 0-6.5A ... PC link mode'. It does not cover the 28 V the stack must survive and read on the Anker 737/Pinecil check. 6.5 A against 7 A, a 1.77 in display, PD3.0 only, an unpublished ripple rate, and Linux support for 2E3C:0049 untested on hardware.
  5.
    - **Name:** ChargerLAB POWER-Z KT002 ($49.99)
    - **Why:** V/I ranges, accuracy and ripple are unpublished; power-z.com sits behind a Cloudflare challenge and I could not read them. No Linux support: the in-kernel hwmon powerz.c (local Radxa 6.18.2 tree) matches only 5FC9:0061 (KM002C) and 5FC9:0063 (KM003C). It saves only $4 nominal. Not provably not-worse.
  6.
    - **Name:** ChargerLAB POWER-Z C240 ($29.99)
    - **Why:** No PD trigger or PDO read, no e-marker, no logging or PC link, no ripple, USB-C only. Functionally far below the FNB58.
  7.
    - **Name:** ChargerLAB POWER-Z KM003C ($109.99)
    - **Why:** Not cheaper (about 2x). USB-C only (no USB-A), 6 A. A reference upgrade only.
  8.
    - **Name:** AVHzY CT-3
    - **Why:** No verified price: none on the official page, and nothing found in the AliExpress DE grid for 'avhzy ct-3/ct3'. 0-6 A against 7 A, ripple 3.2 Msps against 4 Msps, Linux logging unverified, and a second 26 V variant exists. Not shown to be cheaper or not-worse.
  9.
    - **Name:** BerryBase DE FNB58 Std (EUR 49.90 incl. VAT, about $56.15)
    - **Why:** Same part, but re-checked on 18 Oct 2026 the page still carries schema.org SoldOut / 'nicht lieferbar', and shipping is extra (amount unverified). It stays as fallback (b) if it is restocked and its total stays below fnirsi.com's EU checkout total.
  10.
    - **Name:** FNB58 BT (Elektor EUR 49.95, BerryBase EUR 54.90, fnirsi.com $58.99)
    - **Why:** It has a Bluetooth radio, which breaks the QUIET/no-radio rule (user_requirements line 32).
  11.
    - **Name:** AliExpress 'FNB58 ... 240W ... Bluetooth APP' (3256812513972820, US $24.01 new-user / $30.81)
    - **Why:** The title contradicts the FNB58 (140 W, and the Std has no BT). It has 6 sold, no rating and is a welcome-deal price. A possible clone or misdescription.
  12.
    - **Name:** Multi-model AliExpress listings (EUR 17.99-21.19 DE; US $19.69-27.69: 1005013042710449, 1005012356414737, 1005012531958110, 1005002941028767 and others)
    - **Why:** The headline price belongs to the cheapest bundled model (FNAC-28/FNB38 class), not the FNB58. The real single-model FNB58 floor in the DE grid is EUR 41.99.
  13.
    - **Name:** WITRN K2 (EUR 34.99, 2 sold) / WITRN C5 (EUR 79.69)
    - **Why:** K2: specs and ports unverified and no Linux logger known, so it cannot be proven not-worse. C5: more expensive.
  14.
    - **Name:** RD Tech TC66C
    - **Why:** It has Bluetooth (rule fails), 5 A max, no PD detection or listener and no e-marker; price unverified.
  15.
    - **Name:** Used FNB58 (eBay, Kleinanzeigen)
    - **Why:** No verified live listing (HTTP 403). Unknown calibration and connector wear, and no warranty.
  16.
    - **Name:** DIY RP2040 + INA228 PD logger
    - **Why:** No measured evidence, no PD analysis, e-marker or 4 Msps ripple capture. Calibration would be circular, because the FNB58 is the reference for the INA228.
- **Confidence:** medium
- **Conditions or tests:** Buy from AliExpress EU only if ALL of these hold. Otherwise buy from BerryBase if it is restocked and cheaper in total, or else keep fnirsi.com.
  (1) The seller is FNIRSI's official AliExpress store. I could not verify this: the item pages are behind a JS/cookie wall and the grid carries no store names.
  (2) The 'FNB58 Std' / no-Bluetooth SKU is explicitly selected. The grid minPrice is the cheapest SKU, and that SKU is unverified.
  (3) The checkout total for an EU address, including VAT and any EUR 3 low-value-parcel duty, is at most EUR 47 and below fnirsi.com's EU checkout total for the same Std.
  (4) The user accepts losing FNIRSI's 2-year warranty, which applies to fnirsi.com orders only.
  
  Goods-in acceptance (return within the AliExpress window if any check fails):
  - lsusb shows 2e3c:5558; no BT logo on the label and no Bluetooth menu item; CE mark present.
  - Record the firmware version and do not update it.
  - Patched baryluk logger runs 100 sps for 8 h with no stall (or labd 'meter stalled' fires and recovers).
  - With the meter PC-powered, it reads 0.000 V on an unpowered port.
  - Cross-check against the AN8008 and the DPS-150 at 5, 12 and 20 V and at 0.5, 2 and 4 A. Accept if it agrees within the AN8008's tolerance band before using it as the INA228 SHUNT_CAL reference.
  - PD read on the Anker 737 shows 20 V PDOs.
- **Stack changes:** No hardware, rail, connector, case or driver changes: same device, same HID ID 2E3C:5558, same udev rule (90-usb-power-meter.rules), the same patched logger (refresh 0.003, no dev.reset, drain on exit) and the same labd stall detection. Only the BOM line changes:
  - Source becomes 'FNIRSI official AliExpress store, Std SKU, EU checkout'.
  - Price becomes EUR 44.59 incl. VAT (about $50.18), noted as a conditional price.
  - Warranty note: no FNIRSI 2-year warranty off fnirsi.com.
  - Fallbacks: BerryBase EUR 49.90 if restocked, otherwise fnirsi.com EUR 52.05 / $53.99.
  Add the goods-in acceptance list above to the bench bring-up section.
  Correct the analog notes everywhere they cite '$37.00 AliExpress': that is a new-shopper welcome price in the US storefront, not a usable EU price.
  Record that fnirsi.com's EU-market price is EUR 52.05 (not $53.99), so the EU landed baseline is about $58.57.
- **Sources:**
  - https://www.fnirsi.com/products/fnb58.json (USD: Std 53.99 / BT 58.99; ?country=DE,FR,NL,ES,IT,AT: Std EUR 52.05; read 18 Oct 2026)
  - https://www.fnirsi.com/products/fnb-c2.json (USB-C male/female only, 4-50 V, 0-6.5 A, 20 ksps-2 Msps ripple, published accuracy)
  - https://www.fnirsi.com/pages/warranty-policy (2-year warranty only for fnirsi.com orders)
  - https://www.fnirsi.com/policies/shipping-policy (duty payment service for EU orders under $150; customs otherwise customer's responsibility)
  - https://www.fnirsi.com/products/fnb48p and FNIRSI image FNIRSI_FNB48P_USB_Fast_Charge_Tester_02 (label '...24V 0-6.5A')
  - https://de.aliexpress.com/w/wholesale-fnirsi-fnb58.html (EUR grid, taxRate 0.19: 1005004665244812 EUR 44.59; 1005008908357736 EUR 41.99; 1005007468954965 EUR 42.59)
  - https://www.aliexpress.com/w/wholesale-fnirsi-fnb58.html (US grid: 3256804478930060 salePrice $37 tagged 'New shoppers save $51', source welcomedeal, original $88)
  - https://www.aliexpress.com/item/1005004665244812.html (302 redirect to aliexpress.us item 3256804478930060; item page itself not readable)
  - https://www.berrybase.de/fnirsi-fnb58-usb-tester-4-28-v-0-7a-140w-schwarz (EUR 49.90, schema.org SoldOut, 18 Oct 2026)
  - https://raw.githubusercontent.com/baryluk/fnirsi-usb-power-data-logger/master/fnirsi_logger.py (supported IDs 0483:003A/003B, 2E3C:5558, 2E3C:0049; refresh 1.0 s for FNB58 at line 305; sps=100)
  - Local Radxa 6.18.2 source drivers/hwmon/powerz.c (only 5FC9:0061 KM002C and 5FC9:0063 KM003C)
  - https://de.aliexpress.com/w/wholesale-witrn.html (WITRN K2 EUR 34.99, C5 EUR 79.69)
  - https://www.elektor.com/products/fnirsi-fnb58-usb-tester-with-bluetooth (BT only at Elektor)
  - Note: the session WebSearch budget was exhausted, so I did no web search; all checks were direct fetches. power-z.com (Cloudflare), AliExpress item pages (cookie/JS wall), Amazon and eBay could not be read. FX 1 EUR = 1.1253 USD (ECB 16 Oct 2026, as used in analogs_G2).

