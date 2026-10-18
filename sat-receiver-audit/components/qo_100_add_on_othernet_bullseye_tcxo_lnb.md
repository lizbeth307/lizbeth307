# Qo 100 add on othernet bullseye tcxo lnb: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a8fdb4aa-74b`_

- **Part:** QO-100 add-on (in scope: Othernet Bullseye BE01 TCXO LNB + F/75-ohm parts; the cone/horn is an antenna and out of scope; the LNB injector choke >=1 A is still unnamed in STACK)
- **Current pick:** Othernet Bullseye 10 kHz BE01 TCXO LNB from the RTL-SDR Blog webstore ($29.95), plus unnamed generic F/75-ohm parts: a 75 ohm F terminator for the red 25 MHz port and adapters. The LNB injector choke (>=1 A) has no part number yet.
- **Current price usd:** LNB $29.95 list at rtl-sdr.com ('70 in stock', 18 Oct 2026). That webstore does not ship to the EU (verified on the buy page: 'we can no longer ship directly to you from our webstore... order from our official Aliexpress or eBay stores'), so a Europe-based user cannot order at that price. The STACK line total of $47.95-75.00 includes the out-of-scope horn/cone materials. The F parts and the choke are not itemised.
- **Decision:** keep
- **Chosen:** Keep the Othernet Bullseye BE01 (identical part, no analog survived) and change only the seller: buy 2 units (one spare) from Passion Radio, France, EU stock, ref QO100-LNB-BULLSEYE-978. For the red 25 MHz port, name the terminator as AXING CFA 11-00 (75 ohm F male, DC-decoupled) and add 2 pcs to the existing G1 Reichelt order. TechniSat 0002/3077 (screening >100 dB) is the fallback if the spur A/B test favours it. The other F/75-ohm parts stay the SAT-rated G1 parts. The injector choke stays unnamed: it cannot be compared until v2 names a part.
- **Chosen price usd:** LNB at Passion Radio: EUR 24.95 ex VAT = $28.05. EUR 29.94 incl. 20% VAT (FR/AT) = $33.66. CORRECTION: both searches and reaudit_C read EUR 29.94 as 'ex VAT'. It is VAT-inclusive. Proof: the page JS shows priceDisplayMethod=0 and taxRate=20, and the cart JSON shows productTotal 29,94 EUR, 'Including VAT 6,79 EUR' (= 4.99 on the product + 1.80 on shipping), total 40,76 EUR. Destination VAT applies (the shipping quotes carry 19% DE, 21% NL, 23% PL), so the DE product price is EUR 29.69 = $33.37 (modelled from the ex-VAT price). Cheapest verified shipping (Colissimo Point Retrait, 1 unit): FR EUR 5.58, DE 7.90, NL 8.03, IT 9.49, AT 10.82, PL 11.09. Landed for 1 unit: FR EUR 35.52 = $39.93; DE EUR 37.59 = $42.25; NL $42.96; IT $44.89; AT $45.82; PL $46.96. For 2 units to DE (shipping EUR 8.06, verified with qty 2 in the cart): EUR 67.44 = $75.81, about $37.90 per unit. AXING CFA 11-00 terminator: EUR 1.60 incl. 19% VAT = $1.80 each, $3.60 for 2. It rides the G1 Reichelt order, so no extra shipping. Rate 1 EUR = 1.1241 USD.
- **Saving usd:** None from an analog: no cheaper LNB is not-worse. On a like-for-like ex-VAT basis, Passion Radio is $1.90 below the $29.95 list, but that list price cannot be reached from the EU. v2 should RAISE the LNB line to the real EU landed cost: about $40-47 for one unit, about $38 per unit for two to DE. Terminator: AXING at $1.80 against TechniSat at $3.37 plus separate shipping (TechniSat ships free only from EUR 29), a saving of about $1.57 per piece plus the shipping. The v1 generic terminator was unpriced.
- **Equivalence proof:** LNB: same SKU, so there is no spec delta. The Passion Radio page (fetched 18 Oct 2026) lists 'Bullseye 10 kHz BE01': PLL with 2 ppm 25 MHz TCXO; input 10489-12750 MHz; LO 9750/10600 MHz; +/-10 kHz at 23 C and +/-30 kHz over -20..+60 C; factory calibration within 1 kHz; gain 50-66 dB; NF 0.5 dB; return loss 8 dB (739-1950 MHz); V-pol 11.5-14 V, H-pol 16-19 V; 40 mm neck; 64 mm red cap; 25 MHz reference out on the red F port; CE/RoHS/FCC; 2-year warranty. This matches the rtl-sdr.com product page item for item. Genuineness: Passion Radio is an established EU ham retailer with 49 product reviews, the latest dated 18/10/2026 and 19/09/2026 ('works perfect with qo-100'). Interfaces, the 13.2 V V-pol rail, the 739.5 MHz IF to RTL-B, the 40 mm neck for the horn/cone, and the absence of any driver are all unchanged. Receive-only: the LNB is a passive downconverter.
  
  Terminator: AXING CFA 11-00 against the stack's requirements (search A: 75 ohm F male, DC-decoupled, RL >=20 dB at 25 MHz; search B: screening Class A 85 dB minimum). AXING product information sheet (07.01.2013): 5-2200 MHz; 75 ohm; F male; DC-insulated; return loss EN 60728-4 Class 1, >=22.0 dB at 10-47 MHz; screening Class A (85 dB at 5-30 MHz). It meets every minimum, and AXING is an established Swiss SAT/CATV brand sold by Reichelt. Not hidden: TechniSat 0002/3077 has better screening (>100 dB, against AXING's 85 dB) and a wider range (to 2400 MHz), with the same RL (>=22 dB at 5-30 MHz). That trade is acceptable here only because the leak path at 25 MHz is dominated by the Bullseye's own plastic housing (F4DAV), and the A/B spur test below confirms it.
  
  New verified fact that makes DC decoupling mandatory: F4DAV's teardown says 'Pin 4 of the microcontroller is DC-coupled to the red coaxial connector', which is presumably the calibration interface. The port is also 'unbuffered' and 'heavily attenuated'. A DC-coupled 75 ohm load would therefore sit across an MCU pin. Both AXING and TechniSat are DC-decoupled.
- **Rejected:**
  1.
    - **Name:** Inverto Premium Single 40 mm PLL LNB IDLP-SNL413-PREMU-OPN
    - **Why:** Datasheet re-read: low-band input 10.7-11.7 GHz, so 10489.5 MHz is out of spec. Output 950-1950 MHz, so the 739.5 MHz IF is also out of spec. LO initial accuracy +/-500 kHz and drift +/-2.0 MHz at 60 C, against the Bullseye's +/-10/30 kHz (50-67x worse). No TCXO, no calibration, no reference port. Gain up to 67 dB is above the pad plan. Better only in its 100 mA max current and documented phase noise. Retail price unverified.
  2.
    - **Name:** Generic mainstream PLL LNB (Goobay 67269, Opticum, McLean, SR-320 class)
    - **Why:** Goobay +/-300 kHz, 42 dB gain, rated only from 10.7 GHz, 25 MHz crystal, no reference port; Passion Radio lists it as discontinued. F4DAV measured a mainstream PLL LNB as about 30x less accurate and less stable than the BE01. Worse on the deciding spec, LO stability.
  3.
    - **Name:** Octagon OTLSO 1609 twin PLL LNB (same RT320M IC)
    - **Why:** Plain crystal instead of TCXO, uncalibrated, twin body (larger and heavier), no drift or NF measurement, no price found. Sharing the RT320M chip does not make the reference stable.
  4.
    - **Name:** DIY: generic PLL LNB with its 25 MHz crystal swapped for a TCXO (DL9SEC, Goobay mods)
    - **Why:** No independent drift, offset or phase-noise measurement (the DL9SEC PDFs returned 503). The housing is opened and resealed, which is worse build quality than a factory-sealed unit. Gain and NF of the donor are unspecified at 10.49 GHz (Goobay gain 42 dB). Any saving is unproven and at most about $10-25.
  5.
    - **Name:** DIY: PLL LNB locked to the LBE-1420 GPSDO over the coax (G8GKQ/OQSLG mod)
    - **Why:** One measured case lost 3 dB of DVB-S MER (phase noise). The modified LNB stops working without the reference, and the GPSDO is an extended-tier item, so the core kit fails standalone. It puts a +6 dBm 25 MHz carrier on the IF coax, a new spur source for the HF+ and V4L. The housing is opened.
  6.
    - **Name:** Used genuine Bullseye BE01 (eBay/Kleinanzeigen/flea market)
    - **Why:** No listing could be read (eBay 403). Calibration ages about 1 ppm/yr (about 9.75 kHz/yr at the LO), there is no warranty and the moisture/UV history is unknown. Equality would need the buyer's own 24 h beacon test, and no saving is proven.
  7.
    - **Name:** Bullseye via the RTL-SDR Blog webstore ($29.95)
    - **Why:** Not orderable: the buy page (fetched 18 Oct 2026) says the webstore no longer ships to EU customers.
  8.
    - **Name:** Bullseye via the official AliExpress 'RTLSDRBlog Store' (item 4001089711265)
    - **Why:** The listing exists (og:title read on de.aliexpress.com), but the page is client-rendered and no price could be read: UNVERIFIED. Model landed cost to DE at $29.95 with free shipping: $35.64 incl. VAT + EUR 3 duty ($3.37) + EUR 2 UHF from about 1 Nov 2026 ($2.25) = $41.26, against Passion Radio's verified $42.25 (1 unit) or $37.90 per unit (2 units). Not proven cheaper, and slower from China. Keep it only as a fallback, for example if Passion Radio sells out or does not deliver to the user's country.
  9.
    - **Name:** Bullseye via the official eBay 'rtl-sdr-blog' account (item 283900721154)
    - **Why:** eBay returned 403. The only figure is a stale 2025 snippet of $29.97 + $10 shipping from Shanghai, about $40 before the 2026 EUR 3 duty and EUR 2 UHF. Unverified and not cheaper.
  10.
    - **Name:** Bullseye via an Amazon EU reseller (ASIN B08GJ6B1HB)
    - **Why:** Amazon FR, IT, ES and NL all show 'Currently unavailable' (fetched 18 Oct 2026).
  11.
    - **Name:** Bullseye at Elektor (EUR 24.95 incl. VAT, old snippet)
    - **Why:** Delisted: the product URL returns 301 to a search page on both elektor.com and elektor.de (18 Oct 2026).
  12.
    - **Name:** RemoteQTH 'LNB PLL TCXO + BIAS-T' pack (Passion Radio)
    - **Why:** EUR 69.00 incl. VAT, more than twice the Bullseye's price, and a modified generic LNB. Not cheaper.
  13.
    - **Name:** QRO.cz SDR LO 9750 LNB
    - **Why:** EUR 52.03 (hamparts.shop) to EUR 65.00 (WiMo), not cheaper. It stays the upgrade path only.
  14.
    - **Name:** Reichelt FAW 75DC no-name DC-decoupled F terminator (EUR 1.79)
    - **Why:** Manufacturer 'FREI' (unbranded), with no published return loss, frequency range or screening. It also costs more than the AXING CFA 11-00 at EUR 1.60.
  15.
    - **Name:** TechniSat 0002/3077 DC-decoupled F terminator (EUR 3.00)
    - **Why:** Not rejected on quality: it has better screening (>100 dB) and the same RL (>=22 dB at 5-30 MHz). It is just not the cheapest that meets the stack spec: EUR 3.00 plus separate shipping below EUR 29. Kept as the fallback if the spur A/B test shows any leakage difference.
  16.
    - **Name:** Generic AliExpress-class F/75-ohm parts (F-F, F-SMA, terminators)
    - **Why:** No measured evidence: screening class, DC rating and plating are unstated, and AliExpress listings could not be read. Saving of a few dollars at most. The SAT-rated G1 parts stay.
- **Confidence:** high
- **Conditions or tests:** 1) Order now: Passion Radio shows 'Warning: Last items in stock', the AliExpress price is unverified and Elektor/Technofix/Amazon EU are gone. Buy 2 units in one parcel. At checkout, confirm the destination-VAT product price (the DE EUR 29.69 is modelled) and the carrier. Passion Radio's delivery page says it does not ship to the UK or Ireland, but its cart estimator offered IE carriers (EUR 9.91 for 2 units). That is contradictory, so an Irish buyer must confirm or use the official AliExpress store (only via the store link on rtl-sdr.com).
  2) On arrival: confirm the unit is genuine (Othernet BE01 label, green IF / red reference F ports). Measure the current at 13.2 V cold and warm before setting RILM (F4DAV's 'about 1 W', about 75 mA, is a statement, not a measurement).
  3) Red port: measure DC first. Expect an MCU logic level, because the port is DC-coupled to MCU pin 4. Never connect a DC-coupled load or instrument without a DC block. Fit the AXING CFA 11-00.
  4) A/B with the beacon: the 10489.500 MHz CW beacon offset with the terminator on and off must not shift by more than about 100 Hz (the port is attenuated against load pulling).
  5) Spur A/B: HF+ at 25.000/50.000/75.000 MHz and the V4L near 739.5 MHz, comparing port open, AXING and TechniSat. If AXING is worse than TechniSat by more than 1 dB anywhere, use TechniSat 0002/3077.
  6) Optional, conducted bench mode only: LiteVNA S11 of the terminator at 25 MHz better than -20 dB through a de-embedded F-SMA adapter.
- **Stack changes:** 1) STACK line 295 (QO-100 set): change the source from 'RTL-SDR Blog (Bullseye $29.95, 70 pcs)' to 'Passion Radio QO100-LNB-BULLSEYE-978, EUR 24.95 ex VAT / EUR 29.94 incl. 20% VAT (destination VAT applies), qty 2'. LNB cost becomes about $40-47 landed for 1 unit, about $76 for 2 to DE. Correct the 'EUR 29.94 ex VAT' error in reaudit_C and the G6 search JSON. The line total rises by about $8-12 per LNB against v1; the horn/cone stay out of scope. The fallback is the official AliExpress RTLSDRBlog Store, with the cost-rule-35 EUR 3 + EUR 2 per tariff line (2 identical LNBs count as 1 item).
  2) F/75-ohm parts: add AXING CFA 11-00 x2 (EUR 3.20) to the G1 Reichelt order; no new seller or shipping. Replace the reaudit rule 'terminator only if 0 V DC, otherwise a dust cap' with 'always a DC-decoupled 75 ohm terminator (the red port is DC-coupled to an MCU pin, per F4DAV); measure DC anyway'. Do not double-count the F-F bulkhead, internal 75 ohm lead or Goobay 58814, which are already in G1.
  3) No change to rails (TPS7A4701 13.2 V V-pol, TPS259630 eFuse; RILM stays pending the current measurement), connectors (F female), drivers (none) or case/horn throat (same 40 mm neck). Keep the open point that F4DAV gives a 60 mm cap and Passion Radio 64 mm: measure before printing the throat ring.
  4) LNB injector choke >=1 A: still no part number. v2 must name it (rated current >=1 A, DCR, impedance/SRF at 739.5 MHz) before any analog check is possible. It is not an expensive item.
  5) Shopping order item 11: no longer wait for the region (Europe decided); buy the 2 LNBs now.
- **Sources:**
  - https://www.passion-radio.com/lnb-pll/lnb-othernet-978.html (price, stock, specs, reviews; page JS priceDisplayMethod=0, taxRate=20; cart JSON via /cart?add=1&ajax=true: productTotal 29,94 EUR incl. VAT 6,79 EUR, total 40,76 EUR)
  - https://www.passion-radio.com/modules/carriercompare/ajax.php (method=getCarriers: DE/FR/NL/IT/PL/AT/IE shipping quotes, 18 Oct 2026)
  - https://www.passion-radio.com/store/shipping-6 (delivery zones; says no UK/IE delivery)
  - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/ (EU customers cannot order from the webstore)
  - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/ ($29.95, 70 in stock, specs)
  - http://www.pabr.org/radio/otherlnb/otherlnb.en.html (F4DAV: +/-600 Hz over 24 h, 30x better than a PLL LNB, about 1 W, red port DC-coupled to MCU pin 4, unbuffered and attenuated, 60 mm cap / 40 mm neck)
  - https://inverto.tv/download/file/66da86eecfc1d-1725597422.pdf (Inverto IDLP-SNL413-PREMU-OPN datasheet)
  - https://www.technisat.de/en/f-connectors-and-adapters/technisat-f-termination-resistor-dc-decoupled-75-ohm-all_verpackungsinhalt-1-stueck-piece-colour-silver (EUR 3.00, RL and screening specs)
  - https://www.reichelt.de/de/de/shop/produkt/f-abschlusswiderstand_75_ohm_dc_entkoppelt-310551 (AXING CFA 11-00, EUR 1.60 incl. 19% VAT, in stock)
  - https://www.reichelt.de/de/de/shop/produkt/f-abschlusswiderstand_75_ohm_dc_entkoppelt-28509 (FAW 75DC no-name, EUR 1.79)
  - https://asset.conrad.com/media10/add/160267/c1/-/gl/001318378DS01/tehnicni-podatki-1318378-axing-cfa-11-00-zakljucni-upor-za-f-vtic-1-kos.pdf (AXING CFA 11-00 product information: 5-2200 MHz, RL Class 1 >=22 dB at 10-47 MHz, screening Class A)
  - https://de.aliexpress.com/item/4001089711265.html (listing exists; price not readable, client-rendered)
  - https://www.amazon.fr/dp/B08GJ6B1HB, amazon.it, amazon.es, amazon.nl (Currently unavailable)
  - https://www.elektor.com/products/bullseye-10-khz-tcxo-lnb-for-qo-100 (301 to a search page: delisted)
  - https://www.ebay.de/itm/283900721154 (HTTP 403, unverified)

