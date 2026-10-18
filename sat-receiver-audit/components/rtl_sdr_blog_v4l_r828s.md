# Rtl sdr blog v4l r828s: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e32114dd-52d`_

- **Part:** RTL-SDR Blog V4L (Lite), R828S + RTL2832U, 1 ppm TCXO, dongle only. Qty 3: RTL-A (VHF/UHF), RTL-B (L-band / LNB IF), spare. Tier core, group SDR.
- **Current pick:** RTL-SDR Blog V4L (R828S), official rtl-sdr.com store. EU buyers order from the official eBay 'rtl-sdr-blog' or the AliExpress 'RTLSDRBlog Store' 4523039 / 1101427871.
- **Current price usd:** 113.85 for 3 (37.95 each), excluding shipping, VAT and duty. Re-fetched 2026-10-18: 'USD $37.95', '455 in stock', no quantity discount. The webstore does not ship to the EU. EU landed price through the official AliExpress/eBay stores is a model, not a checked price: 45.16-46.68 per unit at 19-23 % VAT, about 135.5-140.0 for 3. The marketplace pages could not be read (AliExpress returned an empty JS page or reset the connection; eBay showed a security check). Verified EU fallback: Passion Radio, EUR 41.60 ex VAT / EUR 49.92 incl. 20 % VAT, which is 56.11 USD each or 168.33 for 3 at 1.1241.
- **Decision:** keep
- **Chosen:** RTL-SDR Blog V4L (R828S), unchanged. No candidate survived. The V3 R860 remains only as the documented after-stockpile fallback, and it is explicitly a downgrade.
- **Chosen price usd:** 113.85 for 3 (37.95 each, ex VAT and shipping; official store, 2026-10-18)
- **Saving usd:** 0.00
- **Equivalence proof:** The part is kept, so nothing is replaced. Why no candidate is not-worse:
  
  (1) Every candidate cheaper than 37.95 is worse on a spec that matters. The only ones are the V3 R860 at 34.95 and the FlightAware Pro Stick Plus at 29.95. I checked all 22 receivers on nooelec.com (both listing pages, fetched 2026-10-18): none costs less than 37.95, and the lowest, the NESDR XTR Tiny, costs exactly 37.95.
  
  (2) V3 against the V4L, from the vendor's combined MDS chart (V4L datasheet V1.0, 3 dB MDS in 500 Hz; I re-read the embedded image myself):
  - 137 MHz: V3 about -138.7, V4L -140.7 dBm.
  - 400-550 MHz: V3 about -137.7, V4L -140.7.
  - 739.5 MHz: V3 about -134.7, V4L about -137.7.
  - 1090 MHz: V3 about -132.7, V4L about -133.7.
  - 1544 MHz: V3 about -130.7, V4L about -132.7.
  - 1700 MHz: V3 about -127.7, V4L about -130.7.
  - The V3 is equal to the V4L only around 210 MHz and is never better anywhere from 90 to 1766 MHz.
  - Two-tone desense: the V4L datasheet says the results are 'identical to the V3', so this is a tie, not a gain.
  - HF: the V3 uses direct sampling, 500 kHz-24 MHz, at about -115 to -122 dBm with Nyquist folding at 14.4 MHz. The V4L uses an upconverter and reaches about -134 to -135 dBm. The stack also forbids direct_sampling, so in this stack a V3 has no HF at all.
  - Datasheets: V3 'Up to 2.4 MHz stable' and 270-280 mA, against V4L '2.56 MHz stable' and 250-270 mA. Both use the same RTL2832U, so the bandwidth gap is probably wording rather than hardware, but on paper it is still worse.
  
  (3) The FlightAware Pro Stick Plus has a SAW filter with a 1075-1105 MHz passband and 30 dB of attenuation everywhere else (flightaware.com), so it cannot fill the RTL-A, RTL-B or spare roles.
  
  (4) Everything else is equal in price or more expensive, worse, or both:
  - Nooelec, all at or above 37.95: XTR Tiny (E4000, no TCXO going by the XTR+/XTR naming); SMArt v5 44.95; SMArTee v2 44.95; Mini 2+ 47.95; Nano 3 52.95; SMArt/SMArTee XTR 54.95.
  - V4 R828D: end of line, and worse in MDS by about 3 dB at 137 MHz, 1 dB at 400, 3-4 dB at 740, 4 dB at 1090 and 4-5 dB at 1700 MHz (same chart).
  - Clones: counterfeit, and rtl-sdr.com testing found them defective.
  - MSI.SDR: no input above 1 GHz.
  - DIY build: not cheaper and has no measurements.
  
  Caveat: every V4L RF number comes from the vendor; no independent V4L measurement exists. The D10 conducted bench baseline (MDS and two-tone at 137.5, 437 and 1700 MHz) and the per-unit genuineness check therefore stay mandatory. Any future 'not worse' claim for a substitute must be proven on that same bench.
- **Rejected:**
  1.
    - **Name:** RTL-SDR Blog V3 R860 (R820T2), dongle only, USB-A or USB-C, $34.95 (official store, add-to-cart, 2026-10-18; buy page range $34.95-39.95)
    - **Why:** It would save only $9.00 for 3, and it is worse:
  - MDS is worse on the vendor chart: about 2 dB at 137 MHz, 3 dB at 400-550 MHz, about 3 dB at 739.5 MHz, about 1 dB at 1090 MHz, about 2 dB at 1544 MHz and about 3 dB at 1700 MHz. That hurts most on the spare, which runs bare whiskers.
  - HF is direct sampling only (500 kHz-24 MHz, 12-18 dB worse MDS, folding at 14.4 MHz), and direct sampling is banned in this stack.
  - Datasheet stable rate is 2.4 vs 2.56 Msps.
  - Current is 270-280 vs 250-270 mA.
  - Two-tone is identical, not better.
  It fails the not-worse rule. It stays only as the documented after-stockpile downgrade.
  2.
    - **Name:** FlightAware Pro Stick Plus, $29.95 on the rtl-sdr.com listing (shown with 'Read more' rather than add-to-cart, so probably not orderable there; unverified)
    - **Why:** The built-in SAW filter passes only 1075-1105 MHz and attenuates everything else by 30 dB, which rules out 137, 174-240, 400-438, 739.5 and 1537-1707 MHz. It draws 300 mA against 250-270 mA, has no HF, and FlightAware does not mention a bias tee. It cannot fill any of the three roles.
  3.
    - **Name:** Nooelec NESDR XTR Tiny (RTL2832U + E4000), $37.95 (nooelec.com, 2026-10-18)
    - **Why:** It is not cheaper (same price) and comes bundled with an antenna and remote control. The TCXO version is the separate XTR+ at $39.95, so the plain XTR has no 1 ppm TCXO (inferred from the product names). It has no HF upconverter and no published bias tee or thermal-pad aluminium case. The E4000 coverage gap is not re-verified. It fails on price and on clock.
  4.
    - **Name:** Nooelec NESDR SMArt v5 / SMArTee v2 / Mini 2+ / Nano 2 / Nano 3 / SMArt and SMArTee XTR ($44.95-54.95, nooelec.com, both listing pages checked)
    - **Why:** All cost more than $37.95; none of Nooelec's 22 receivers is cheaper. The SMArt v5 also tops out at 1.75 GHz (vs 1.766), has no bias tee and uses direct-sampling HF. The R820T2 models have no published MDS that matches the V4L.
  5.
    - **Name:** RTL-SDR Blog V4 (R828D), new or used genuine
    - **Why:** It is end of line and no genuine new units are available. Third-party listings at about $61.75-63.75 are unverified (eBay blocked), cost more than the V4L, and the vendor says most of them are clones. On the vendor's MDS chart it is worse than the V4L by about 3 dB at 137 MHz, 1 dB at 400 MHz, 3-4 dB at 740 MHz, 4 dB at 1090 MHz and 4-5 dB at 1700 MHz. Its better two-tone does not offset the sensitivity loss under the not-worse rule.
  6.
    - **Name:** Used genuine RTL-SDR Blog V3
    - **Why:** It has the same spec deficits as the new V3 (MDS, HF, stable rate, current). Its price is unverified because eBay was blocked, and it carries no warranty in a clone-heavy market.
  7.
    - **Name:** Generic 'RTL.SDR' V3-style clones (R820T2/R860)
    - **Why:** rtl-sdr.com tests found 'very strange distorted spectrums', 'a mysterious high pitched whine', and 'most of them are missing key features like the bias tee and the TCXO'. They copy the RTL-SDR Blog trade dress (counterfeit), and no measurement shows them equal. Price unverified.
  8.
    - **Name:** Marketplace 'RTL-SDR Blog V4' / 'V4 Pro' listings from unofficial sellers
    - **Why:** They are counterfeit: the vendor says they use a copied V4 enclosure with a V3-clone circuit inside, so the HF path is dead and the TCXO and bias tee are unknown. They also cost more than the V4L (about $61.75-63.75, unverified).
  9.
    - **Name:** MSI.SDR (MSi2500 + MSi001, unauthorised RSP1 clone)
    - **Why:** The revspace owner reports 'there is no input for signals > 1 GHz on my receiver', so it loses 1090 MHz and all of 1537-1707 MHz. It has no bias tee. Drivers are 'not very mature', the kernel driver is unusable, and rtl_433 gave no decodes. It is not a librtlsdr drop-in, and it is an unauthorised clone. Price unverified.
  10.
    - **Name:** DIY RTL2832U + R828S/R820T2 board
    - **Why:** It would not be cheaper at qty 3 (estimate), there is no verified R828S distributor source, and it has no measurements. Copying the 'RTLSDRBlog'/'Blog V4L' strings to reach the V4L code path would be misrepresentation.
  11.
    - **Name:** Same V4L from Passion Radio (France, official reseller list), EUR 49.92 incl. VAT ($56.11)
    - **Why:** This is the same part, not an analog, and it is dearer than the official route. Price verified on 2026-10-18 from the page JSON: TaxExcl 41.6, TaxIncl 49.92, displayed price '49,92 €', 19 in stock. The page H1 still reads 'RTL-SDR.com V4 TCXO USB key + SMA + Bias-T + R828D tuner', so it could ship the worse V4 (R828D). Use it only as a fallback, after the seller confirms the R828S V4L SKU in writing.
- **Confidence:** high
- **Conditions or tests:** No replacement condition applies. Carried-over gates:
  (a) Incoming genuineness check on every unit, whatever the channel:
  - diagonal case screws;
  - rtl_eeprom read-only shows 'RTLSDRBlog'/'Blog V4L' and IR bit = 1;
  - the log shows 'RTL-SDR Blog V4 Lite Detected';
  - conducted CW tones via tinySA through a 30 dB pad at 10.000, 137.500, 437.000 and 1700.000 MHz, at about -90 dBm, all visible.
  (b) D10 bench baseline for MDS and two-tone at 137.5/437/1700 MHz. The V4L numbers are the vendor's only.
  (c) EU checkout: confirm that the official AliExpress (4523039 / 1101427871) or eBay 'rtl-sdr-blog' listing ships to the buyer's country, and record the real price incl. VAT. The 45.16-46.68 USD per unit figure is a model.
  (d) If Passion Radio is used, get written confirmation that the SKU is the R828S V4L, because the page H1 says V4 / R828D.
  Evidence limits: the WebSearch budget was exhausted before this step, so verification used WebFetch on primary pages plus the local datasheets. The V4L MDS chart is /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p5rtl/v4lds/img/i-000.png; the V3 datasheet is /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p5rtl_verify/v3ds/v3.pdf.
- **Stack changes:** None to rails, connectors, drivers or case. The part is unchanged, so these stay as they are: USB map, 250-270 mA per unit, TPS2553 0.75 A LAB port, lab librtlsdr 2.0.3 build with the gpio==0-only bias gate, EEPROM bias default off, aluminium case bonded to the plate, and the spur mask (144.0, 403.2, 432.0, 1699.2 MHz).
  
  BOM and sourcing text updates:
  1. Keep $113.85 as the USD base (ex VAT). Add the EU landed note: about $135.5-140.0 for 3 incl. 19-23 % VAT via the official AliExpress/eBay stores (model, unverified). Verified fallback: Passion Radio, EUR 149.76 incl. 20 % FR VAT for 3 ($168.33), only after written SKU confirmation. For other EU countries the destination-country VAT applies at checkout.
  2. Note that the V4L is in the China warehouse only ('Amazon USA warehouse not stocked yet'), and order all 3 now: limited edition, R828S stockpile about one year.
  3. The V3 fallback text must say explicitly that it is a downgrade:
  - MDS 1-3 dB worse at 137-1766 MHz;
  - no HF in this stack, because direct sampling is banned;
  - 2.4 Msps stable on its datasheet;
  - 270-280 mA.
  4. A side observation for a different row, not this part, and unverified: rtl-sdr.com lists the FlightAware Pro Stick Plus at $29.95 but shows only 'Read more', not add-to-cart, while STACK carries it at $69.92 from The Pi Hut. The verifier for the extended ADS-B row should check availability before relying on either price.
- **Sources:**
  - https://www.rtl-sdr.com/product/rtl-sdr-blog-v4l-lite-r828s-rtl2832u-1ppm-tcxo-sma-software-defined-radio-dongle-only/
  - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
  - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
  - https://www.rtl-sdr.com/wp-content/uploads/2018/02/RTL-SDR-Blog-V3-Datasheet.pdf
  - https://www.rtl-sdr.com/product-category/uncategorized/?product-page=1
  - https://www.flightaware.com/adsb/prostick/
  - https://www.nooelec.com/store/sdr/sdr-receivers.html?p=1
  - https://www.nooelec.com/store/sdr/sdr-receivers.html?p=2
  - https://www.passion-radio.com/rtl-sdr-stick/r828s-v4l-3214.html
  - https://www.revspace.nl/Msi2500SDR
  - https://www.rtl-sdr.com/avoiding-fake-rtl-sdr-blog-v3-clones-2021-supply-chain-updates/
  - https://www.rtl-sdr.com/rtl-sdr-blog-v4-end-of-line/
  - https://www.aliexpress.com/store/1101427871 (fetched: JS-only page, no price readable)
  - https://www.ebay.com/str/rtlsdrblog (fetched: eBay security check, blocked)

