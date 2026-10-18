# Airspy mini: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_31a822f9-b6d`_

- **Part:** Airspy Mini (optional, gated fast L-band SDR for Metop-B/C AHRPT at 1701.3 MHz and AWS at 1707 MHz, behind the helicone and SAWbird+ GOES; qty 1)
- **Current pick:** Airspy Mini from Moonraker UK, about GBP 110 per STACK.md (undated, unverified)
- **Current price usd:** About 140-160, stack midpoint 146.50 (GBP 110 x 1.3318). Not verifiable today: moonrakeronline.com returns HTTP 403 to WebFetch and curl. A search snippet (undated, unverified) shows the Moonraker EU duty-paid site at EUR 126.08 special (EUR 137.98 regular), about USD 141.7 before shipping. A UK seller with no duty paid adds import VAT, EUR 3 duty and the EUR 2 handling fee per tariff line, plus shipping (operator notes 34-35).
- **Decision:** replace_conditionally
- **Chosen:** The same genuine part from a cheaper official source: Airspy Mini EU, SKU IM150415001EU, sold by ITEAD (Airspy's official manufacturing partner) from its DE warehouse. https://itead.cc/product/airspy-mini-the-high-performance-miniature-sdr-dongle-eu/ . The purchase stays gated exactly as before.
- **Chosen price usd:** 99.00 ex VAT. Verified 18 Oct 2026 in the ITEAD WooCommerce store API: price 9900 USD minor units, regular = sale price, "242 in stock", "dispatched from our DE warehouse, 3-6 business days". Landed prices from a guest cart I re-ran (nothing ordered; shipping is "DHL (Ship From DE Warehouse)" and is flat per order):
  - DE: 123.22 (VAT 18.81, shipping 4.55 + 0.86 VAT)
  - FR: 130.91 (VAT 19.80, shipping 10.09 + 2.02)
  - PL: 130.23 (VAT 22.77, shipping 6.88 + 1.58)
  Derived from a multi-unit cart, assuming the same flat shipping per order:
  - AT about 127.27; CZ about 127.68; NL about 128.43; BE about 128.65; PT about 133.96; GR about 136.35; FI about 141.88; SE about 142.60
  - ES and IT: NO shipping rate was returned, so ITEAD DE delivery there is not proven.
  If an Airspy sale repeats (summer 2026 was 20% off, 79.20, verified on rtl-sdr.com, but ITEAD's participation was not named), the DE landed price would be about 99.66. That is conditional only.
- **Saving usd:** Against the stack midpoint of 146.50:
  - DE: about 23.28 (range 16.78-36.78 against 140-160)
  - FR: about 15.59
  - AT, CZ, NL, BE: about 18-19
  - PL: about 16.27
  Against the Moonraker EU snippet price of 141.7 plus shipping: at least about 18.5 for DE.
  Against WiMo (EUR 144.90 incl. VAT, USD 162.88, verified): 39.66 for DE.
  SE and FI: only about 4-5, which is marginal.
  ES and IT: 0 until ITEAD shipping there is confirmed.
  Nothing is spent unless the gate fails.
- **Equivalence proof:** It is the same hardware, the same SKU family and the same maker. airspy.com/purchase says "Itead Studio is our official manufacturing partner", so units from every distributor (Moonraker, WiMo and the others) are ITEAD-built. Every spec that matters for this stack is identical, because it is the same unit:
  - Range 24-1700 MHz. Metop and AWS are above this spec for BOTH options equally. libairspy airspy.h allows set_freq up to 1.75 GHz, and airspy_rx.c has FREQ_HZ_MAX 1900 MHz "(officially 1750MHz)", both read today. Community HRPT use of the Mini at about 1.7 GHz exists (Tysonpower dish + 2x SPF5189Z + Airspy Mini on rtl-sdr.com), but nobody has measured it at exactly 1701.3 or 1707 MHz.
  - NF 3.5 dB at 42-1002 MHz; tracking RF filters; +35 dBm IIP3 front end (vendor claim); maximum RF input +10 dBm.
  - 12-bit ADC at 20 MSPS, 10.4 ENOB. airspy.com gives 70 dB SNR and 95 dB SFDR; the ITEAD page gives 80 dB DR and 64 dB SNR. This is a difference in the published text for the same hardware, not a different unit.
  - 3, 6 and 10 Msps IQ (6 Msps covers Metop's 3.5 MHz); 0.5 ppm low-phase-noise clock; 4.5 V software-switched bias-T; -10 to +40 C.
  - USB 2.0 HS.
  - Drivers: libairspy0 1.0.10-3build1 and soapysdr0.8-module-airspy 0.2.0-4 are published in noble universe arm64 (I verified this on the Launchpad API today). SatDump has a native airspy plugin.
  - Receive-only hardware.
  
  Build quality and authenticity: the source is an official channel, so there is no counterfeit risk.
  
  The one non-hardware difference, stated rather than hidden, is seller terms. ITEAD lists a 30-day return and a 1-year quality replacement; the product badge says 24 months, which is inconsistent. ITEAD is a Shenzhen company with a DE warehouse. EU statutory 2-year conformity rights still apply to sales aimed at EU consumers, but they are harder to enforce than against WiMo (DE).
  
  Conditions for the replacement:
  (1) At checkout, confirm that ITEAD DE ships to the user's country. ES and IT returned no rate. If it does not ship, fall back to AstroRadio ES (EUR 127.05, VAT basis unverified) or WiMo.
  (2) Confirm that the order shows no customs or duty line and that DHL tracking starts in DE.
- **Rejected:**
  1.
    - **Name:** Airspy Mini via Moonraker UK (current source)
    - **Why:** Same part, but the price cannot be verified (HTTP 403 today). The EU duty-paid listing found in search is EUR 126.08, about USD 141.7 plus shipping (undated snippet), which is above ITEAD DE's landed 123.22. Shipped from the UK without duty paid, it also carries EUR 3 duty + EUR 2 handling fee + import VAT.
  2.
    - **Name:** Airspy Mini at WiMo DE
    - **Why:** Identical part, in stock, EUR 144.90 incl. VAT (verified today), USD 162.88. That is 39.66 more than ITEAD DE. Keep it as the fallback if ITEAD does not ship to the user's country or if an EU-established seller's warranty is preferred.
  3.
    - **Name:** Airspy Mini at AstroRadio ES / Neven CZ / FB Radio SE / Ham Shop NL
    - **Why:** Identical part, but not cheaper or not verifiable:
  - AstroRadio: EUR 127.05 (USD 142.82); VAT basis and stock not shown. It is the fallback for ES.
  - Neven: out of stock.
  - FB Radio: SEK price; VAT and stock unverified.
  - Ham Shop NL: no price found.
  4.
    - **Name:** Used Airspy Mini (Moonraker EU used listing, EUR 92.76 in a search snippet; eBay, Kleinanzeigen, Marktplaats)
    - **Why:** Price unverified: the Moonraker page returns 403, the snippet is undated, and eBay and Kleinanzeigen return 403. Worse in warranty and reliability: no 30-day return or 1-year replacement, and unknown ESD or overload history on the front end. Counterfeit risk on marketplaces. At most about USD 19 saved before UK shipping and import charges.
  5.
    - **Name:** Same ITEAD SKU bought in a sale (20% off = 79.20, about 99.66 landed DE)
    - **Why:** The price is not real today. The summer 2026 sale is over, ITEAD's participation was not named, and a Black Friday 2026 sale is unverified. Treat it only as an opportunistic option if the gate fails during a sale. Never buy early.
  6.
    - **Name:** LimeSDR Micro M.2 (already in the stack) used instead of buying a Mini (reaudit_C scope swap)
    - **Why:** Not a not-worse analog. It is better in coverage (1701-1707 MHz is inside its spec) but worse in:
  - Clock: +-1 ppm calibration and +-2 ppm first-year ageing, against 0.5 ppm. This is harmless next to AHRPT Doppler of about +-40 kHz, but it is still a lower spec.
  - Power: about 4 W, against a dongle.
  - One RX LO is shared, so a pass blocks other Lime use.
  - It is TX-capable hardware, blocked only by the LimeSuiteNG patch.
  - Not available before 15 Dec 2026.
  - IIP3 and maximum input are unverified against +35/+10 dBm.
  - Clock-derived spur model: a 1680 MHz line at 56 Msps; use the 7 Msps floor.
  Dropping the Mini is a scope decision for the orchestrator and user, not a like-for-like replacement under this rule.
  7.
    - **Name:** HydraSDR RFOne
    - **Why:** Not cheaper: USD 193.67 at DigiKey, 511 in stock (verified today), +94.67 ex VAT. It is better in coverage (24-1800 MHz, with Metop and AWS in spec), but it is larger (54x49x32 mm) and has no noble arm64 package, so it must be built from source. Keep it as the upgrade path only if a bought Mini fails PLL lock or the noise and spur check at 1707 MHz within the 30-day return window.
  8.
    - **Name:** Airspy R2 EU (ITEAD, IM141027001EU)
    - **Why:** Not cheaper: USD 169.00 ex VAT, 214 in stock (store API, verified). Same 1700 MHz spec limit, so no coverage gain, and a larger case.
  9.
    - **Name:** SDRplay RSP1B
    - **Why:** Not cheaper: GBP 105.80 ex VAT, about USD 141, and out of stock. Worse in maximum input (0 dBm against +10 dBm) and size and weight (98x94x35 mm, 315 g). Closed API and daemon on arm64. NF and IIP3 parity are unproven.
  10.
    - **Name:** RTL-SDR Blog V4L at 2.88 Msps (spare)
    - **Why:** Worse:
  - ADC: 8 bit against 12 bit at 10.4 ENOB.
  - Bandwidth: 2.88 Msps, about 82% of Metop's 3.5 MHz.
  - Linearity: much lower.
  It is the gate test that decides whether the Mini is bought, not an analog.
  11.
    - **Name:** RX888 MkII (open design, multiple makers)
    - **Why:** Not cheaper: eBay listings of about USD 150-192 (search snippet, unverified). VHF/UHF goes through the R828D tuner to the ADC, so the 16-bit ADC does not give 16-bit VHF performance. It needs USB 3 SuperSpeed at high rates (RFI). There is no official manufacturer and no measured parity at 1.7 GHz.
  12.
    - **Name:** MSI.SDR / MSi2500 'RSP1 clones'
    - **Why:** No input above 1 GHz on the RevSpace-measured unit, immature drivers (libmirisdr), no NF or dynamic-range data, clone hardware, and the price is unverified.
  13.
    - **Name:** AliExpress 'Airspy' Mini or R2 clones
    - **Why:** A copied trademarked design: fails the counterfeit and legality rule. No measurements and no warranty.
  14.
    - **Name:** HackRF One (and clones)
    - **Why:** Worse: 8-bit ADC with weaker dynamic range, and it overloads more than the Airspy (RTL-SDR.com review). It is also a TX-capable transceiver, which conflicts with the receive-only rule.
  15.
    - **Name:** Used SDRplay RSP1A
    - **Why:** Price unverified. Strong-signal parity is unproven: the RSP family was measured worse than the Mini. Closed API. Counterfeit MSi-based 'RSP1A' units circulate.
- **Confidence:** high
- **Conditions or tests:** The purchase gate is unchanged. Buy only if gate (a) fails, meaning 15 min of rtl_test at 2.88 Msps on the blue port with no drops, or gate (b) shows the Metop hump but the V4L cannot decode. Optionally, the orchestrator can add: do not buy if the Lime has already passed acceptance including a 15-minute zero-drop 7 Msps capture on the helicone + SAWbird+ GOES path. That is a scope choice, and it must be told to the user as a clock and power trade (see the rejected Lime entry).
  
  Source conditions:
  (1) ITEAD DE must offer shipping to the user's country. ES and IT returned no rate in the API. If not, use AstroRadio (ES) or WiMo.
  (2) Checkout must show no duty or customs line, and DHL tracking must start in DE.
  
  Acceptance inside the 30-day return window, conducted-only:
  (a) airspy_info shows the serial and firmware.
  (b) 6 Msps for 15 min on the Q6A with zero dropped samples; log Q6A CPU load.
  (c) Lab source at 1701.3 and 1707 MHz through at least 40 dB of attenuation into the Mini: confirm PLL lock, compare the noise floor and spurs with 1690 MHz, and check that the tone level is within about 3 dB of 1690 MHz. This covers the above-1700 MHz spec gap, which the current pick has too.
  (d) FNB58 USB current at 6 Msps, because it is unpublished (third-party estimates of 200-300 mA are unverified).
  If (c) fails, return the unit. The only in-spec analog is the HydraSDR RFOne (+94.67), which needs a new decision.
- **Stack changes:** BOM 2.11, line "Швидкий L-band SDR":
  - Change the seller from Moonraker to ITEAD (DE warehouse, SKU IM150415001EU).
  - Price: USD 99.00 ex VAT; landed DE 123.22 / FR 130.91 / PL 130.23 (verified 18 Oct 2026); other EU countries about 127-143.
  - Status: verified.
  - Note the ES/IT shipping caveat and the WiMo / AstroRadio fallback.
  - Group subtotal note: "Airspy Mini about $140-160" becomes "about $123-143 landed (gated)".
  
  Item #91:
  - Same price update.
  - Add the above-spec note: 24-1700 MHz official, libairspy 1.75 GHz, airspy_rx 1.9 GHz tool limit.
  - Add the 30-day conducted acceptance test (c).
  
  No change to rails: bus-powered from 5 V USB 2.0 on the blue port or the CH334F hub. Add the FNB58 measurement to the power budget once the unit is bought.
  
  Connectors: SMA female. Keep the stack's DC block between the TPS2553-injected LNA line and the SDR input. Keep the Mini's bias-T off; airspy_set_rf_bias stays behind the labd token.
  
  Drivers, unchanged: libairspy0 1.0.10-3build1 and soapysdr0.8-module-airspy 0.2.0-4 (noble arm64, verified), SatDump airspy plugin with PR #1172 stop-order fix. SoapyAirspy has no ppm correction, so rely on SatDump carrier tracking.
  
  Case: no change. The dongle is 77x26x10 mm (earlier research; not on the official page). It stays outside the case on a short USB lead to avoid the USB-shield noise seen on SBCs.
  
  Hard rules kept: RX-only hardware, conducted-only test source, no new software.
- **Sources:**
  - https://itead.cc/wp-json/wc/store/v1/products/751684
  - https://itead.cc/wp-json/wc/store/v1/products?search=airspy&per_page=50
  - https://itead.cc/wp-json/wc/store/v1/cart (guest cart, nothing ordered, 18 Oct 2026)
  - https://itead.cc/product/airspy-mini-the-high-performance-miniature-sdr-dongle-eu/
  - https://airspy.com/purchase/
  - https://airspy.com/airspy-mini/
  - https://raw.githubusercontent.com/airspy/airspyone_host/master/airspy-tools/src/airspy_rx.c
  - https://raw.githubusercontent.com/airspy/airspyone_host/master/libairspy/src/airspy.h
  - https://api.launchpad.net/1.0/ubuntu/+archive/primary (libairspy0, soapysdr0.8-module-airspy, noble arm64)
  - https://www.wimo.com/en/airspy-mini
  - https://www.astroradio.com/?post_type=product&s=airspy
  - https://moonrakeronline.com/eu/used-airspy-mini-sdr (403; search snippet only)
  - https://www.digikey.com/en/products/detail/benjamin-vernoux/HYDRASDR-RFONE/26256067
  - https://www.rtl-sdr.com/airspy-2026-summer-sale-20-off-all-airspy-products/
  - https://www.rtl-sdr.com/improving-hrpt-reception-free-hrpt-decoder/
  - https://www.rtl-sdr.com/tag/metop/
  - https://www.rtl-sdr.com/review-airspy-mini/
  - https://www.ab9il.net/software-defined-radio/airspy-mini-power.html (estimates only, not measurements)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/g6_parts/airspy_mini.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_B_receivers_rf.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_C_antennas_targets.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md

