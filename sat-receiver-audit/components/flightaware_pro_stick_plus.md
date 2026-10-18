# Flightaware pro stick plus: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_c3ba734e-52b`_

- **Part:** FlightAware Pro Stick Plus (continuous 1090 MHz ADS-B receiver on LAB USB-A, CH334F H3, TPS2553 0.75 A). Tier extended, group Lab extended, qty 1.
- **Current pick:** FlightAware Pro Stick Plus from The Pi Hut (SKU 103075).
- **Current price usd:** 69.92 (GBP 52.50 incl. UK VAT; Shopify .js re-read 18 Oct 2026: price 5250, available=true). Ex-VAT that is GBP 43.75 = $58.27.
  
  With the localization=DE cookie, Pi Hut charges GBP 52.06 incl. 19% DE VAT = $69.33 (verified; IOSS). EU delivery is DHL Express only at GBP 30 = $39.95 per order, plus a mandatory flat-rate customs duty whose amount Pi Hut does not state (reported as EUR 3 per item = $3.37; unverified).
  
  Landed in DE (model):
  - Bought on its own: about $112.65.
  - Added to the Pi Hut order the stack already places (2x Pico, MTT hub): about $72.70.
- **Decision:** keep
- **Chosen:** Keep the FlightAware Pro Stick Plus from The Pi Hut. It is the only channel I could verify that is in stock and ships to the EU. Buy it in the SAME Pi Hut order as the 2x Raspberry Pi Pico and the Waveshare MTT bench hub, not as a separate last-step order.
- **Chosen price usd:** 69.92 is the USD base (GBP 52.50 incl. UK VAT). Real EU checkout is GBP 52.06 = $69.33 in DE (19% VAT via IOSS, verified). Other states scale with their VAT rate on GBP 43.75 (model).
- **Saving usd:** 0.00 on the part.
  
  The stack does save $39.95 in landed cost by merging the stick into the existing Pi Hut order, because one DHL Express charge (GBP 30) is avoided.
- **Equivalence proof:** The part is kept, so nothing is traded. I re-verified its specs from primary pages (flightaware.com/adsb/prostick, and the Pi Hut and Pimoroni copies of the FA spec):
  - R820T2 + RTL2832U.
  - Amplifier 19 dB, NF 0.4 dB, OIP3 +39.
  - 0.5 ppm TCXO.
  - SAW passband 1075-1105 MHz, 2.3 dB insertion loss, 30 dB attenuation elsewhere.
  - 300 mA.
  - 95 x 32 x 13 mm, SMA female.
  
  rtl-sdr.com review, verified:
  - The Skyworks LNA comes first and the SAW after it.
  - Measured 300 mA (330 mA for the Pro Stick plus external filter).
  - The LNA draws about 60 mA instead of 100 mA (probably runs at 3.3 V), so the real OIP3 is likely below the datasheet figure.
  - It did not overload on a resonant 1090 antenna at max gain, but gave 'dismal' results on a discone.
  
  System NF (my cascade model: 0.4 dB / 19 dB, then 2.3 dB SAW, then R820T2 at about 5 dB) is about 0.6 dB.
  
  The adversarial pass found every cheaper candidate to be one of these:
  - (a) The same SKU through a channel that does not ship to the EU or is out of stock. The FA store FAQ says 'Currently, we only ship our products within the US', and Shopify cart/shipping_rates returns an empty list for DE and FR. Pimoroni is available=false. rtl-sdr.com is 'Out of stock'. BerryBase says 'aktuell nicht lieferbar'.
  - (b) Worse on a published spec (FlightStick, Pro Stick + filter, jetvision, the V4L DIY chains).
  - (c) Unpublished specs and also US-only (ADSBx Blue).
  
  Break-even against adding the stick to the existing Pi Hut order ($72.70 incl. 19% VAT and duty): a $45.99 FA-store unit wins only if forwarding plus international shipping costs under about $12.3. An ADSBx Blue would have to stay under about $8.3. Neither forwarder cost was verified.
- **Rejected:**
  1.
    - **Name:** Same SKU, flightaware.store, $45.99
    - **Why:** Verified US-only: the FAQ says 'we only ship our products within the US', and Shopify shipping_rates for Germany and France come back empty. It is cheaper than the Pi Hut route ($72.70 incl. 19% VAT and duty) only if a US forwarder's fee plus shipping stays under about $12.3. The forwarder cost is unverified. It is not a real EU price.
  2.
    - **Name:** Same SKU, Pimoroni, GBP 19.75
    - **Why:** Shopify .js shows available=false (sold out). The price is a stale legacy figure, and UK-to-EU DHL, VAT and duty would apply anyway.
  3.
    - **Name:** Same SKU, Moonraker EU, EUR 68.96 (search A) / GBP 59.95 (search B)
    - **Why:** curl and WebFetch both got HTTP 403, so price and stock are unverified. A search snippet marks it discontinued. EUR 68.96 = $77.52, which is above the $69.92 base and the $72.70 Pi Hut route.
  4.
    - **Name:** Same SKU, BerryBase DE, EUR 79.90
    - **Why:** Verified 'Artikel aktuell nicht lieferbar' (not deliverable). At $89.82 it is also more expensive.
  5.
    - **Name:** Same SKU, rtl-sdr.com store, $29.95
    - **Why:** Verified 'Out of stock' on the product page.
  6.
    - **Name:** Used Pro Stick Plus (eBay, Kleinanzeigen)
    - **Why:** No verified price (eBay blocked). The LNA is the part most exposed to ESD and lightning, there is no warranty, and it could be a mis-described orange Pro Stick. Not provably cheaper or equal.
  7.
    - **Name:** ADSBexchange Blue R820T2 + amp + 1090 filter, $49.99
    - **Why:** The product JSON description is empty. The only text, on the bundle page, says 'Onboard 1090 Mhz filter and amplifier' and 'Drop-in Replacement'. LNA part, gain, NF, filter passband and rejection, filter position and current are all unpublished, and I found no independent measurement. Shopify shipping_rates for DE and FR are empty, so it does not ship to the EU, and the forwarder break-even is about $8.3. It fails the never-trade-silently rule.
  8.
    - **Name:** AirNav RadarBox FlightStick, $49.95 + $4.99 standard shipping to DE (verified)
    - **Why:** It does ship to the EU. Landed DE cost is about $68.75 (model, VAT collection method unverified), only about $4 under the Pi Hut route. It is worse on the vendor's own figures:
  - NF 0.75 dB vs 0.4 dB.
  - Gain 18.4 dB at 1 GHz vs 19 dB (the shop's 20.5 dB claim conflicts).
  - Filter passband and rejection unpublished.
  - No TCXO stated.
  - Current unpublished.
  In the only controlled strong-signal A/B (FA forum, nu3e, under 2 km from a cell site), the Pro Stick Plus received 'many more aircraft' with no external filter. The FlightStick matched it only with an external 1090 filter, which AirNav sells at $49.95. One user reports it runs hot.
  9.
    - **Name:** FlightAware Pro Stick + FA 1090 band-pass filter
    - **Why:** In the EU-reachable channel (Pi Hut, verified) it costs GBP 45.30 + 25.90 = GBP 71.20 = $94.82, more than the Plus. The $56.65 FA-store price is US-only. NF is worse by the filter's insertion loss, because the filter sits ahead of the LNA: 1.2 dB measured by rtl-sdr.com, 2.8 dB by a commenter. It draws 330 vs 300 mA and is two pieces on the LAB port. It is better only in overload immunity, a mixed trade and not not-worse.
  10.
    - **Name:** jetvision ADS-B USB Dongle 53199, EUR 29.50
    - **Why:** Verified listing: plain RTL2832/R820T2 with MCX female input. No LNA, SAW filter or TCXO is listed. That loses the 19 dB / 0.4 dB front end, the 30 dB preselection and the 0.5 ppm reference.
  11.
    - **Name:** DIY: spare V4L + Uputronics 1090 filtered preamp (GBP 44.40 at Pi Hut, EUR 44.95 = $50.53 at Uputronics EU)
    - **Why:** It consumes the spare V4L, which STACK C21 forbids for continuous duty. With a new V4L it costs $37.95 + $50.53 = $88.48, more than $69.92. Further drawbacks:
  - Modelled system NF about 0.95 vs 0.6 dB (0.75 dB including SAW, at least 16 dB gain, before the V4L).
  - Needs the labd-gated V4L bias tee.
  - The Uputronics passes no signal when unpowered.
  - Two pieces.
  It stays only as the documented fallback, with these trades stated.
  12.
    - **Name:** DIY: spare V4L + RTL-SDR Blog ADS-B Triple Filtered LNA, $39.95
    - **Why:** Verified 'Out of stock'. It would also consume the spare (C21) and need the bias tee. NF is higher than 0.4 dB on the vendor figures (about 1 dB, from the announcement, unverified by me). Rejection is better, but it cannot be bought.
  13.
    - **Name:** Generic AliExpress 'ADS-B LNA+SAW' sticks or SPF5189 boards
    - **Why:** No listing or price verified and no independent measurement. Counterfeit, relabel and oscillation risk. Akos' 19-dongle test ranked generics below the FA sticks.
- **Conditions or tests:** No replacement condition applies. Acceptance checks for the kept unit on arrival, all conducted or receive-only:
  1. Identity: lsusb shows 0bda:2832, rtl_test reports R820T2, and the FlightAware-branded case is present. Write a unique serial with rtl_eeprom -s for udev naming (C21).
  2. Power: the FNB58 on the LAB port should read about 300 mA steady (fail above 350 mA). No TPS2553 fault on hot-plug.
  3. Conducted selectivity, in Bench mode with no antenna:
     - tinySA tone at 1090 MHz through a 30 dB pad, at or below -70 dBm at the SMA; note the rtl_power level.
     - An out-of-band tone at the same level (within the tinySA's clean output range, e.g. around 800 MHz) should read at least about 25-30 dB lower (SAW spec 30 dB).
  4. Thermal: 2 h at 2.4 Msps; log case-surface temperature. Keep the stick outside the closed case on the bottom-edge port. The 'runs hot' reports are unverified for this model.
  5. Field, receive-only: with the 6.5 cm whiskers near a cell site, compare readsb messages/s and strong-signal % at max gain against one or two lower gain steps. If desense shows, either lower the gain or add an external 1090 SAW ahead of the stick, and record that trade (+1.2-2.8 dB NF).
  
  Search budget note: the shared WebSearch quota ran out early in this step. Everything above was checked by WebFetch or curl on primary store pages, Shopify JSON and cart/shipping_rates, the FA spec page, the rtl-sdr.com review and the FA forum thread. Moonraker and Amazon stayed unreadable (403/503).
- **Stack changes:** Nothing changes in rails, connectors, drivers or case:
  - LAB USB-A on CH334F H3, TPS2553 0.75 A, about 300 mA; within the labd 1.5 A LAB+LNA budget.
  - SMA female.
  - Stock R820T2 path in librtlsdr +lab .so.2; readsb --device-type rtlsdr.
  - No bias tee, so no labd token is involved.
  
  Text and BOM changes:
  (1) STACK line 364, BOM row: keep $69.92 (GBP 52.50 incl. UK VAT) as the USD base and add:
     - ex-VAT GBP 43.75 ($58.27);
     - EU checkout charges destination VAT under IOSS (DE GBP 52.06 = $69.33, verified);
     - EU delivery DHL Express only, GBP 30 ($39.95) per order;
     - mandatory flat-rate customs duty, amount not stated (EUR 3 per item reported, unverified).
  (2) Shopping order (STACK lines 1130 and 1151): move the Pro Stick Plus out of step 13 into the Pi Hut order that already carries the 2x Pico and the MTT hub. This shares one DHL charge (-$39.95 landed) and secures stock while Pi Hut is the only verified EU-reachable channel. That order is about GBP 65.5 ex VAT (about EUR 78), so it stays under EUR 150 and IOSS applies.
  (3) Budget fallback (STACK lines 364 and 373): change 'Uputronics 1090 GBP 44.39 ($59.12)' to 'EUR 44.95 ($50.53) at the Uputronics EU storefront / US $53.00, or GBP 44.40 at Pi Hut in the same order'. State the trades explicitly: NF about 0.95 vs 0.6 dB (model), it consumes the C21 spare, it needs the bias token, and it passes nothing unpowered.
  (4) Known limitation in C21/ADS-B rows: the LNA comes before the SAW, so the stick overloads with wideband antennas (rtl-sdr.com). Use only the resonant 6.5 cm whiskers or a 1090 antenna. The mitigation is an external 1090 SAW ahead of the stick (FA filter GBP 25.90 at Pi Hut), with its NF cost stated.
  (5) Supply note: FA store US-only, Pimoroni sold out, BerryBase not deliverable, rtl-sdr.com out of stock, Moonraker unverified. If Pi Hut sells out, fall back to (3).
  
  Unchanged reminders:
  - readsb --db-file pinned and fail-closed, with &1 and the proposed &4/&8 suppression.
  - GPSDO off and disconnected during ADS-B.
  - FNB58 current logged against the 0.75 A port.
- **Confidence:** high
- **Sources:**
  - https://thepihut.com/products/flightaware-pro-stick-plus-usb-sdr-ads-b-receiver.js (price 5250, available; with localization=DE: GBP 52.06)
  - https://thepihut.com/pages/delivery
  - https://thepihut.com/search/suggest.json?q=flightaware (Pro Stick GBP 45.30, FA 1090 filter GBP 25.90, ADS-B 1090 preamp GBP 44.40)
  - https://www.flightaware.com/adsb/prostick/
  - https://www.flightaware.store/products.json?limit=100
  - https://flightaware.store/pages/faqs
  - https://flightaware.store/cart/shipping_rates.json (DE/FR: empty)
  - https://shop.pimoroni.com/products/pro-stick-plus-high-performance-usb-sdr-ads-b-receiver.js
  - https://moonrakeronline.com/eu/adsb-receiver-prostick-plus (HTTP 403, unverified)
  - https://www.berrybase.de/search?search=pro+stick+plus
  - https://www.rtl-sdr.com/product/flightaware-prostick-plus-ads-b-specialty-rtl-sdr/
  - https://www.rtl-sdr.com/product/rtl-sdr-blog-ads-b-triple-filtered-lna-bias-tee-powered/
  - https://www.rtl-sdr.com/flightaware-prostick-vs-flightaware-prostick-plus-review/
  - https://store.adsbexchange.com/products/adsbexchange-com-blue-r820t2-rtl2832u-0-5-ppm-tcxo-ads-b-sdr-w-amp-and-1090-mhz-filter.js
  - https://store.adsbexchange.com/products/adsbexchange-com-r820t2-rtl2832u-0-5-ppm-tcxo-ads-b-sdr-w-amp-and-1090-mhz-filter-software-on-industrial-microsd.js
  - https://store.adsbexchange.com/cart/shipping_rates.json (DE/FR: empty)
  - https://shop.radarbox.com/products.json?limit=100
  - https://shop.radarbox.com/cart/shipping_rates.json (DE: Standard $4.99, Expedited $12.99, Priority $25.99)
  - https://en.airnavradar.com/flightstick1090
  - https://discussions.flightaware.com/t/radarbox-flightstick-vs-flightaware-pro-stick-plus/44824
  - https://webshop.jetvision.de/en/product/53199/
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_B_receivers_rf.json (Uputronics 1090 EUR 44.95 / US $53.00)
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md (lines 57, 233, 354, 364, 373, 616, 1130, 1151)

