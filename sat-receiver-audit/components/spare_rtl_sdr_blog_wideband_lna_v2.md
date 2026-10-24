# Spare rtl sdr blog wideband lna v2: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** Spare RTL-SDR Blog Wideband LNA V2 (Qorvo QPL9547), qty 1. Bench tier. Also the optional LNA on the P8 WIDE/2 m path (Flamingo+ #2, then LNA V2, then ch4/TCBT, then RTL-A T3).
- **Current pick:** RTL-SDR Blog Wideband LNA V2 (QPL9547), from the rtl-sdr.com webstore
- **Current price usd:** 19.95 at the rtl-sdr.com webstore (re-verified 18 Oct 2026, 208 in stock). An EU buyer cannot pay this price. The buy page says: "EU customers ... we can no longer ship directly to you from our webstore. Please order directly from our eBay or Aliexpress stores".
- **Decision:** keep
- **Chosen:** Keep the same part: RTL-SDR Blog Wideband LNA V2 (QPL9547). Buy it through the official AliExpress listing 'Wideband LNA V2 by RTL-SDR Blog' (item 33011424874). The rtl-sdr.com buy page links this exact listing from the LNA V2 product block, next to add-to-cart=24866 and ebay.us/rq4IrC, so it is the manufacturer's own EU route. EU-stock fallback: Passion Radio, France.
- **Chosen price usd:** 28.99 = EUR 25.79 incl. 19% DE VAT, free shipping from CN (AliExpress search data, DE locale, 18 Oct 2026: salePrice 25.79, originPriceAmount 2579 so no promo, taxRate 0.19, 595 real trades). About EUR 21.67 ex VAT; other EU countries will differ slightly because VAT rates differ. Landed: about 32.36 (EUR 28.79) if the temporary EUR 3 per-item customs duty is added at checkout (I could not verify whether it is already included), and about 34.61 (EUR 30.79) once the EUR 2 Union handling fee applies, expected from about 1 Nov 2026. Fallback, Passion Radio cart verified: EUR 29.78 incl. 20% VAT + EUR 10.82 shipping (the cart's own local estimate) = EUR 40.60, about 45.64.
- **Saving usd:** 0 against the analog search: no cheaper not-worse analog exists, so the part stays. Two sourcing effects for v2. (1) The real EU landed cost is about $12.4-14.7 MORE than the $19.95 in STACK.md: about $32.36-34.61 instead of $19.95. (2) Buying through the official AliExpress listing instead of Passion Radio saves EUR 9.81-11.81, about $11.0-13.3, per unit.
- **Equivalence proof:** No replacement is made, so this proves the rejections; the part itself is unchanged.
  
  Specs that matter for this stack, with the reference values:
  (1) Coverage with no gaps at 144-146, 435-438 and about 740 MHz, 1.69-1.71 GHz and 2.20-2.30 GHz; bench spare up to 3.8 GHz (Lime) and usefully to 6 GHz (LiteVNA/tinySA). Reference: 100 MHz-6 GHz, per rtl-sdr.com, Passion Radio and the RFMW chip page '0.1 to 6 GHz'.
  (2) Board noise figure 1 dB or less. Reference: rtl-sdr.com '<1 dB'; Passion Radio '~1 dB'; chip 0.3 dB at 1.9 GHz.
  (3) Gain 15-20 dB, enough for the Friis case and not too much for the 8-bit RTL. Reference: Passion Radio 15-20 dB; chip 19.5 dB at 1.9 GHz (RFMW lists 19.3 dB).
  (4) Linearity. Reference chip: OIP3 +39 dBm at the 65 mA bias setting (39.3 dBm on RFMW), P1dB 22.7 dBm.
  (5) 3-5 V coax bias at the LNA bus (4.30 V since v2.1; was 4.5 V). Current must be 150 mA or less for the TCBT ch4 channel and 90 mA or less for the spare V4L tee. Reference: rtl-sdr.com buy page '3 - 5v, 90mA'; Passion Radio '150 mA max'; chip Id 65 mA.
  (6) Aluminium enclosure with SMA connectors, 46.5x32x15.6 mm (69.8 mm long with SMA).
  (7) Genuine chip in active production. QPL9547 is Qorvo's named replacement for the end-of-life SPF5189Z (stack rule #99).
  (8) No driver needed; receive-only.
  
  Every candidate cheaper than the official EU route (EUR 25.79-28.79) fails at least one of these:
  - Generic AliExpress QPL9547 board, EUR 18.99. Unproven on (2), (4) and (5); (6) unknown; (7) unprovable. I also found AliExpress selling single 'QPL9547' chips at EUR 2.19-5.29, below DigiKey's EUR 6.07, which is a remarking red flag.
  - TQP3M9037 modules. Unproven on (1), (2) and (4); fail (5) because they are DC-pin or USB powered; fail (7).
  - SPF5189Z boards. Fail (1) because they stop at 4 GHz; fail (5) because they have no coax bias; fail (7) because the chip is end-of-life and widely counterfeited.
  
  Every candidate that is not worse on paper costs more: Passion Radio's copy of the same part, Nooelec LaNA, LNA4ALL, F1OPA, GPIO Labs, and V1 stock (which is also end-of-life and stops at 4 GHz).
- **Rejected:**
  1.
    - **Name:** Generic 'QPL9547 6GHz RF LNA-Platine 20dB' board on AliExpress (item 1005013382308811)
    - **Why:** Verified in the DE search data: EUR 18.99 is an early-bird promo with 'nur noch 1 übrig' (only 1 left). The 30-day low is EUR 27.2, it was listed 10 Oct 2026, and it has no sales or reviews. With the EUR 3 duty: EUR 21.99 at the promo price, EUR 30.2 at the regular price, which is more than the official V2. There are no published S-parameters, NF, P1dB or current. Enclosure, shield, bias-tee input and ESD protection are all unknown (it is sold as a bare board, 'Platine'). Chip provenance is untraceable. The lab has no calibrated noise head, so 'not worse' on NF can never be shown. A saving of about EUR 6.8 on one promo unit does not justify an unprovable part.
  2.
    - **Name:** Generic TQP3M9037 modules (AliExpress, EUR 7.19-22.99)
    - **Why:** Only marketing claims ('100 kHz-6 GHz', 'NF 0.4 dB'), no measurements. I could not verify the chip's own frequency limits: Qorvo returned 429 and the distributors returned 403. Most are powered by DC pin, USB or jack, not by a 3-5 V coax bias tee. The 30-40 dB versions have too much gain for the 8-bit RTL. Unknown chip origin, shielding and stability.
  3.
    - **Name:** Generic SPF5189Z boards (AliExpress EUR 2-7; Passion Radio EUR 9.90)
    - **Why:** End-of-life chip (Qorvo PCN 21-0060) with documented fakes at 13-15 dB gain instead of 18.7 dB. Stops at 4 GHz instead of 6 GHz. Powered through PCB pins, not a bias tee. Mostly unenclosed. Banned by stack rule #99.
  4.
    - **Name:** RTL-SDR Blog Wideband LNA V1 (SPF5189Z): Van Dijken Elektronica NL EUR 27.50 incl. 21% VAT, in stock (new find); Astroradio ES EUR 24.45, out of stock
    - **Why:** Not cheaper than the official V2 route (EUR 25.79 + EUR 3). End-of-life chip (rule #99). Covers 50 MHz-4 GHz, which is worse above 4 GHz for the bench role. Current 75-105 mA typical can exceed the 90 mA limit on the V4L tee.
  5.
    - **Name:** Nooelec LaNA (SKU 100812)
    - **Why:** $37.95, verified on nooelec.com; EUR 30.41 sale price incl. VAT plus shipping at Passion Radio. More expensive on every route. Covers 20 MHz-4 GHz, short of 6 GHz. Nooelec publishes no NF, gain, OIP3 or P1dB.
  6.
    - **Name:** LNA4ALL (9A4QV, PSA4-5043+)
    - **Why:** The blog confirms 28-2500 MHz, so it does not cover the bench range up to 3.8-6 GHz and 2.3 GHz is near its edge. About 15-16 dB gain and OIP3 about 34 dBm, both lower than the reference. Bare board with no enclosure. Coax bias needs a solder modification, and the maker no longer supplies the inductor. About EUR 30-33 with shipping (figure from the search pass, not re-verified), so it is not cheaper.
  7.
    - **Name:** F1OPA wideband LNA (PGA-103+), Passion Radio
    - **Why:** EUR 42. Receive range 50-1500 MHz, so it misses 1.7 and 2.2 GHz. Needs 8-14 V, which does not fit the 4.3-4.5 V bias bus.
  8.
    - **Name:** GPIO Labs PSA4-5043+ inline LNA
    - **Why:** About $60 (from earlier research, not re-fetched). Covers 10 MHz-2 GHz, with only 12 dB at 1 GHz.
  9.
    - **Name:** PGA-103+ 'EMC field-probe preamp' kits (AliExpress)
    - **Why:** 9 V DC jack, stops at 4 GHz, no measurements, and sold bundled with H-field loop probes, which the stack bans.
  10.
    - **Name:** DIY QPL9547 board (genuine chip from DigiKey DE, EUR 6.07)
    - **Why:** A complete single build costs about $25-45 (estimate from the search pass). Board NF and stability depend on the layout and cannot be measured here without a calibrated noise head. The Qorvo eval board costs EUR 120.73 and is matched only for 0.6-4.2 GHz.
  11.
    - **Name:** Same part from Passion Radio (France, EU stock)
    - **Why:** Correction to search B: EUR 29.78 is the price INCLUDING 20% VAT, not ex VAT. The page variables say productPriceTaxIncluded=29.78 and productPriceTaxExcluded=24.82, and the anonymous cart shows product EUR 29.78, shipping EUR 10.82, tax EUR 6.76, total EUR 40.60 (the 'tax excl.' label on the page is wrong). It is EUR 9.8-11.8 dearer than the official AliExpress route. Keep it as the fallback: 23 in stock, EU warranty, 14-day returns, no customs.
  12.
    - **Name:** Same part from the rtl-sdr.com webstore at $19.95
    - **Why:** The webstore refuses EU delivery (VAT policy since 1 July 2021).
  13.
    - **Name:** Same part from the official eBay listing or Amazon US/DE (ASIN B07G14Q6XX)
    - **Why:** Prices could not be verified: eBay returned 403 and Amazon served a captcha. The Amazon ASIN is old and may still carry V1 stock.
  14.
    - **Name:** Used V2 or V1
    - **Why:** No listing was reachable. History unknown (ESD or overload damage); V1 also breaks rule #99.
  15.
    - **Name:** About $2 BFG425W 'TV antenna amplifier'
    - **Why:** rtl-sdr.com's own test shows overload and intermodulation. USB-powered, no coax bias, no lab data.
- **Confidence:** high
- **Conditions or tests:** This is a keep, so there is no condition for replacement. Acceptance checks when the unit arrives:
  (a) The AliExpress listing 33011424874 was launched on 2019-05-06, so it is the old V1 listing re-titled for V2, and most of its 500+ sales and 4.8-star rating are probably for V1. Confirm the case or label says V2, QPL9547, 100 MHz-6 GHz; V1 is SPF5189Z, 50 MHz-4 GHz. Confirm the seller is 'RTLSDRBlog Store' No. 4523039, and check the checkout for the EUR 3 duty line.
  (b) Measure the current at 4.5 V (FNB58/DPS-150). 90 mA or less is required before it may use the spare V4L tee; 150 mA or less for ch4/TCBT.
  (c) Conducted only: LiteVNA S21/S11 through a 30-40 dB pad at 145, 437, 740, 1700 and 2250 MHz, at least 15 dB gain everywhere.
  (d) Noise-source A/B against the SAWbird+ path (relative NF only).
  Method limits: WebSearch was unavailable (the shared budget was used up). Qorvo returned 429; DigiKey, TME, eBay and LCSC returned 403; Amazon served a captcha. The QPL9547 chip figures come from RFMW's Qorvo-sourced listing.
- **Stack changes:** No changes to power rails, connectors, drivers or the case.
  
  Price and sourcing changes for v2:
  - STACK.md line 346 ('Запасний LNA ... 19.95'): replace $19.95 with 'EUR 25.79 incl. VAT, free shipping, official AliExpress 33011424874 (+EUR 3 duty, and +EUR 2 handling fee from about 1 Nov 2026) = about $32.36-34.61 landed; non-EU list price $19.95; EU-stock fallback Passion Radio EUR 40.60 landed'. That is +$12.41 to +$14.66 against v1.
  - Correct rf_frontend.json and the search-B text: Passion Radio's EUR 29.78 is INCLUDING VAT.
  - Shopping-order line 1119 ('ЄС: офіційний eBay або AliExpress 4523039'): this route is right. Recompute the order total as EU-landed: EUR 3 duty per distinct tariff line while the consignment is EUR 150 or less and goes by IOSS or post, plus the EUR 2 handling fee per line from about 1 Nov 2026 (operator note 35).
  
  Electrical rules stay as they are: C9 preliminary budget 0.1 A, TPS2553 at 300 mA, TCBT only at 150 mA or less, V4L spare tee only at 90 mA or less with a labd token. Current sources disagree (rtl-sdr.com 90 mA, chip 65 mA at the 1.9 GHz bias point, Passion Radio '150 mA max'), so the measurement on arrival decides the tee.
  
  Hard rules unchanged: a receive-only passive gain block, never ahead of the FM filter on WIDE, no loops.
- **Sources:**
  - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
  - https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
  - https://www.aliexpress.com/item/33011424874.html
  - https://www.aliexpress.com/w/wholesale-rtl-sdr-blog-wideband-lna.html
  - https://www.aliexpress.com/w/wholesale-QPL9547.html
  - https://www.aliexpress.com/item/1005013382308811.html
  - https://www.passion-radio.com/sdr-accessory/lna-rtlsdr-764.html
  - https://www.vandijkenelektronica.nl/product/wideband-lna-bias-tee-powered/
  - https://www.rfmw.com/ProductDetail/QPL9547-Qorvo/675339
  - https://www.nooelec.com/store/sdr/sdr-addons/lana.html
  - https://lna4all.blogspot.com/
  - https://www.astroradio.com/p/lna_50mhz_a_4ghz_/
  - https://www.passion-radio.com/sdr-accessory/lna-opa-805.html
  - https://www.passion-radio.com/sdr-accessory/lna-spf-833.html
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/rf_frontend.json
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md

