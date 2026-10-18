# Nooelec sawbird h1: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_c3ba734e-52b`_

- **Part:** Nooelec SAWbird+ H1 (SKU 100811): 1420 MHz LNA-SAW-LNA for 21 cm HI and solar noise. Used on P3/ch3 with 4.5 V coax bias through a TPS2553 channel, then HMC7992 to RTL-B, or to the Lime through a pad. Tier extended, group Lab extended, qty 1.
- **Current pick:** Nooelec SAWbird+ H1, cased, SKU 100811 (UPC 0616469146557)
- **Current price usd:** 49.95 ex VAT at Nooelec direct (verified 18 Oct 2026; page shows Add to Cart and 'usually shipped in 1 business day'). Landed in the EU from the US: $59.44-60.44 with 19-21% VAT, plus EUR 3 duty and EUR 2 UHF (about $5.62) once UHF applies, so at least $65.1-66.1, plus shipping (free only on orders over $100) and any postal clearance fee. Nooelec names no IOSS or DDP.
- **Decision:** keep
- **Chosen:** Keep the Nooelec SAWbird+ H1 (100811). Only the buying channel changes. For an EU buyer, buy the same ASIN B07XPV9RX2 from an Amazon EU store where the seller is Nooelec Inc (merchant A1TIGMJ4AZ1K1A) and Amazon fulfils it. Verified on Amazon.nl, 18 Oct 2026. No other brand, generic, DIY or used option is both cheaper and not worse.
- **Chosen price usd:** EUR 55.10 incl. 21% NL VAT at Amazon.nl (page says 'All prices include VAT'), free delivery, about $61.93 at 1.124. Ex VAT EUR 45.54, about $51.18. At 19% DE VAT the same net price would be about $60.91; that figure is my calculation, because Amazon.de served a bot page. Goods are already in the EU, so there is no EUR 3 duty and no EUR 2 UHF. Seller is Nooelec Inc, shipped by Amazon, returnable within 30 days. Rated 4.7/5 from 92 ratings.
- **Saving usd:** $0 on the part itself, because no cheaper not-worse analog exists. The channel saves money landed in the EU. Amazon EU costs about $61.9 delivered. Nooelec direct costs at least $65.1-66.1 plus shipping and any postal clearance fee. The saving is therefore about $3-4 on a combined Nooelec order over $100 (free shipping), and about $3-4 plus the full shipping cost and clearance fee when the H1 is ordered alone. Ex VAT the Amazon price is $1.23 higher than the $49.95 list price, so the gain comes only from avoiding duty, UHF and US shipping.
- **Equivalence proof:** Same part. The Amazon EU listing is the identical SKU and ASIN B07XPV9RX2, titled 'NooElec SAWbird+ H1 ... 1420 MHz'. The seller is genuine: the merchant ID on the Amazon.nl buy box, A1TIGMJ4AZ1K1A, is the merchant ID Nooelec itself links for Amazon DE/FR/IT/ES on its 'Where to buy' section (nooelec.com/store/shipping-delivery-info). Amazon fulfils the order, so it is not a third-party marketplace seller, and counterfeit and grey-market risk are minimal.
  
  Specs I checked myself in datasheet rev 1 (nooelec.com/datasheets/100811, local copy sha256 38a07946...):
  - Range 1376-1441 MHz, centre 1408 MHz, BW 65 MHz (3 dB) and 75 MHz (10 dB).
  - Gain max 42 dB; the plot shows 40-42 dB flat over 1378-1440 MHz with about 2 dB ripple. 1420.4 MHz is well inside.
  - NF 0.70/0.8/0.9 dB (Tn 51/59/67 K); OP1dB +18 dBm; Pin max 0 dBm.
  - 3.3-5.5 V; 108/122/150 mA.
  - Reverse isolation better than 60 dB.
  - 80x30x20 mm, 52 g.
  
  Product page: fully EMI-shielded, a separate shield per LNA, overvoltage protection up to 12 V, three power paths (use one only).
  
  Every other candidate is proven worse or more expensive (see rejected). The best NF option, TQP3M9037 (0.4 dB measured), costs $128.91 per board. Cheap wideband stages measure 0.6-0.7 dB NF but only 15-16 dB of gain, with no SAW. No cheaper candidate matches the H1's combination of 40 dB or more of gain, at most 0.9 dB NF, SAW selectivity of 65 MHz, shielding, and 4.5 V coax bias at 150 mA or less.
- **Rejected:**
  1.
    - **Name:** Nooelec SAWbird+ H1 Barebones (B07XJLKQDN)
    - **Why:** Worse NF: about 1.05 dB vs about 0.8 dB on Nooelec's own H1 page, roughly +20 K Tsys, because the 50 Ohm reference switch adds loss. No enclosure or shields. Not in the Nooelec SAWbird catalog (17 products, ?limit=all, 18 Oct 2026: the only H1 is the cased one). No price or stock verified.
  2.
    - **Name:** Reuse the SAWbird+ GOES 100792 / iO 100788 already in the stack
    - **Why:** Wrong band. The GOES datasheet gives centre 1688 MHz with 70 MHz 3 dB BW (about 1653-1723 MHz); the iO is centred at 1542 MHz. 1420 MHz falls in the SAW stopband of both, so neither can serve HI at all.
  3.
    - **Name:** GPIO Labs Hydrogen Line Pre-filtered LNA w/ Bias Tee (Tindie)
    - **Why:** Verified 18 Oct 2026: $97.20 (about 1.9x), plus import from Canada. Gain 34 dB vs 40-42; NF '1 dB' (an external memo puts it at about 1.16 dB) vs 0.8. Max input -10 dBm vs 0 dBm. Filter type and passband unspecified. The seller states that 'less than +5V DC will result in unreliable or no amplification', so it is incompatible with the 4.5 V ch3 bias rail. Enclosure and current not stated. The 32 dB version ($87.00) fails the same way.
  4.
    - **Name:** Single LNA4ALL (9A4QV, PSA4-5043+), bias-T mod
    - **Why:** EUR 23 + 3 + 7 shipping = EUR 33, about $37 (maker list, undated; stock note May 2025). About 15.4-16.0 dB gain at 1420 MHz (Astropeiler Y-factor) vs 40-42 dB. No filter, so it gives up the H1's about 36-80 dB SAW rejection of GSM/LTE/GNSS/Inmarsat. Bare PCB, no shield. Better IP3 (about +34 dBm) does not offset the missing gain and selectivity.
  5.
    - **Name:** 2x LNA4ALL + Mini-Circuits VBFZ-1400-S+ (or 9A4QV filter)
    - **Why:** About $120 (EUR 59 for the LNAs plus $54.13 for the filter; the filter price was not re-verified). About 29-30 dB after 2.3 dB filter loss vs 40-42 dB. Filter 3 dB points 1139-1784 MHz (Astropeiler), so it passes B32 SDL 1452-1492, Inmarsat and GNSS. Three bare boxes, with no single shielded module for the feed mount. NF gain of 0.7 vs 0.8 dB is within measurement error.
  6.
    - **Name:** RTL-SDR Blog Wideband LNA (SPF5189Z), $19.95
    - **Why:** No filter. Single stage of about 15 dB class (Astropeiler measured 14.6-15.1 dB on SPF5189Z boards) vs 40 dB. NF only stated as '<1 dB'. 150 mA vs a 122 mA typical. Already struck by STACK D8/#99.
  7.
    - **Name:** Generic eBay/AliExpress SPF5189Z boards, cascaded, plus hairpin filter or VBFZ
    - **Why:** Measured 2-stage cascade: 28.6 dB at NF 1.0 dB (Astropeiler) vs 40-42 dB at 0.8 dB. The hairpin filter adds 5 dB loss and has a 2.4 GHz spurious passband. SPF5189Z is EOL, so re-marked chips are a risk. No CE DoC, 5 V header only. Board prices not verified.
  8.
    - **Name:** Mini-Circuits ZX60-P162LN+
    - **Why:** $128.77 (search A, not re-verified), about 2.6x. Single stage with no SAW, DC on a separate pin rather than coax bias. NF 0.5 dB is better, but price, rejection and gain all fail.
  9.
    - **Name:** Qorvo TQP3M9037-PCB eval boards (2x) + filter
    - **Why:** $128.91 each at DigiKey, so more than $258 before a filter. NF 0.4 dB at 22.8 dB per stage is better electrically, but it fails the 'cheaper' condition. Bare boards, 5 V supply, needs a DIY bias-T and housing.
  10.
    - **Name:** Kuhne electronic (DE, EU) MKU LNA 131 AH SMA
    - **Why:** Checked directly 18 Oct 2026: EUR 309.00 incl. 19% VAT. Range 1246-1346 MHz (does not cover 1420), 20 dB gain, needs +9 to +15 V. No 1420 MHz Kuhne LNA is in its current LNA catalog (3 pages checked). Rejected on price, band and supply.
  11.
    - **Name:** Used Down East Microwave 1420LNAH / 1420LNA
    - **Why:** 27.9 or 11.1 dB vs 40-42 dB; NF 0.8-0.9 dB (Astropeiler); no band filter; N connectors; no listing or price found; no warranty.
  12.
    - **Name:** Used Nooelec SAWbird+ H1
    - **Why:** No listing verified (eBay returned 403). A degraded first stage cannot be excluded with the stack's tools: the DIY noise source and tinySA only give relative Y-factor. Warranty does not transfer. Equality is unprovable.
  13.
    - **Name:** AliExpress '1420 MHz hydrogen line SAW LNA' clones
    - **Why:** None found by search B. My WebSearch budget for this turn was used up, so this was not re-searched. With no listing and no measurement there is nothing to verify, so rejected.
  14.
    - **Name:** Same SKU via Amazon.co.uk
    - **Why:** UK to EU means import VAT plus duty, UHF and handling on top of GBP list. The buy-box price was hidden (unverified). Landed cost is above Amazon EU.
  15.
    - **Name:** Same SKU via Passion Radio (FR) or Neven (CZ), the EU affiliates Nooelec names
    - **Why:** Passion Radio's Nooelec supplier catalog shows only the SAWbird NOAA, with no H1 found. Neven's search link from Nooelec returned HTTP 404. No offer is verifiable.
- **Confidence:** high
- **Conditions or tests:** On arrival:
  1. Check the label shows SKU 100811, the cased version with SMA in/out, and that the seller on the invoice is Nooelec Inc via Amazon EU.
  2. Measure supply current on ch3 at 4.5 V (INA3221). It must be 108-150 mA.
  3. Run a conducted LiteVNA S21 sweep on the bench only, with a load or DUT and never an antenna. Pad the input so the H1 sees -40 dBm or less (Pin max 0 dBm, gain about 42 dB). Pad the output, and feed bias through a bias-T with a DC block toward the VNA. Expect 40 dB or more at 1420.4 MHz, the 3 dB passband near 1376-1441 MHz, and record the rejection at 1452, 1455, 1460, 1490, 1542, 1575 and 1800 MHz.
  4. Run a relative Y-factor check with the DIY ZFL-500 noise source (BENCH, conducted). Then do the receive-only sun-rise test: expect about 0.7-1.2 dB over Tsys 125 K (model).
  5. Include a D10 noise-floor A/B at 1420 MHz.
  
  Order condition: buy only when the Amazon buy box shows 'Nooelec Inc' (A1TIGMJ4AZ1K1A) and 'Amazon' as the shipper. Accept Amazon.de/fr/it/es only if the price is EUR 55.10 or less incl. VAT; their prices were not readable today because of bot pages. Otherwise order Nooelec direct together with other Nooelec items to pass $100 for free shipping, and budget VAT + EUR 3 duty + EUR 2 UHF per tariff line.
- **Stack changes:** Corrections for STACK row #366 and related rows:
  - Price and status: VERIFIED $49.95 at https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-h1.html. The old '45-50, URL 404' is out of date.
  - EU channel: Amazon.nl EUR 55.10 incl. VAT, free delivery, about $61.93; sold by Nooelec Inc (A1TIGMJ4AZ1K1A), shipped by Amazon. This is cheaper landed than US import.
  - Specs, replacing the approximations, from datasheet rev 1:
    - 1376-1441 MHz, centre 1408 MHz, BW 65/75 MHz
    - gain 40-42 dB (max 42)
    - NF 0.70/0.8/0.9 dB
    - OP1dB +18 dBm (not the GOES +20)
    - Pin max 0 dBm
    - 3.3-5.5 V; 108/122/150 mA
    - 80x30x20 mm, 52 g
    - The datasheet header says 'SAWbird+ H1m ... Barebones' as a template slip. Its NF and dimensions match the cased 100811.
  - labd/INA3221 baseline window for H1 on ch3: 108-150 mA, not a flat 120 mA. Well inside the TPS2553 300 mA channel.
  - Selectivity caveat, from my reading of the datasheet S21 plot: the upper skirt is soft. Gain is about 25 dB at 1450 MHz and about 0 dB near 1455 MHz, with a notch near 1457 MHz, then about +5 dB over 1465-1500 MHz. Relative rejection is therefore only about 15-25 dB at 1452 MHz, the band-32/n75 SDL lower edge, and about 36 dB at 1465-1495 MHz. Add this to the D10 A/B and the bring-up S21 test. No cheaper candidate is better there.
  - Lime path: OP1dB +18 dBm against a Lime absolute maximum input of +10 dBm. Use the 12 dB pad, not 10 dB, after the H1 on the Lime path. Psat is unpublished.
  - Warranty note: the page says '2 year warranty' and also 'standard 1 year warranty'. Overvoltage damage is excluded. Bias only from ch3 over coax; never micro-USB or the header at the antenna, because the three power paths must not be combined.
  - No change to rails, connectors (SMA), drivers (passive, so Ubuntu 24.04 arm64 is unaffected), case or mounting.
  - Shopping order step 13/14: H1 bought via Amazon EU (Nooelec merchant). Consider checking Amazon EU for the other Nooelec parts (NOAA, GOES, iO, Flamingo+) too, to avoid the per-line EUR 3 duty and EUR 2 UHF; this was not checked here.
  - Hard rules unaffected: receive-only LNA, bench sweeps conducted-only, no loops.
- **Sources:**
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-h1.html (price $49.95, warranty texts, H1 vs Barebones NF, power options; fetched 18 Oct 2026)
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird.html?limit=all (17 products, only one H1, no sales)
  - https://www.nooelec.com/datasheets/100811 (datasheet rev 1; local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p5h1b/dl/h1_ds.pdf, plots pg-3.png/pg-4.png read by me)
  - https://www.nooelec.com/store/shipping-delivery-info/ (USPS/UPS, free shipping over $100, no EU warehouse, affiliate list incl. Amazon EU merchant A1TIGMJ4AZ1K1A, Passion Radio, Neven)
  - https://www.amazon.nl/dp/B07XPV9RX2 (EUR 55.10 incl. VAT, sold by Nooelec Inc A1TIGMJ4AZ1K1A, ships from Amazon, free delivery, 4.7/5 from 92; fetched 18 Oct 2026; local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/h1verify/amz/nl.html)
  - https://www.amazon.de/dp/B07XPV9RX2 (bot page; price unverified)
  - https://www.tindie.com/products/gpio/hydrogen-line-pre-filtered-lna-1420mhz-w-bias-tee/ ($97.20, 34 dB, 1 dB NF, -10 dBm max, >=5 V)
  - https://lna4all.blogspot.com/ (EUR 23 / +3 bias-T / 7 shipping; 2-stage 31.35-32.2 dB, NF 0.698-0.757 dB; 47 mA at 4.5 V)
  - https://astropeiler.de/wp-content/uploads/2020/01/Hydrogen_2.pdf (LNA4ALL 15.4-16.0 dB/0.7 dB; SPF5189Z 14.6-15.1 dB/0.6-0.7 dB; 2-stage 28.6 dB/1.0 dB; TQP3M9037 22.8 dB/0.4 dB; DEM 1420LNAH 27.9 dB/0.8 dB; VBFZ-1400-S+ 2.3 dB, 1139-1784 MHz)
  - https://shop.kuhne-electronic.com/kuhne/en/shop/low-noise-amplifiers/ and MKU LNA 131 AH SMA page (EUR 309 incl. VAT, 1246-1346 MHz, 9-15 V)
  - https://www.passion-radio.com/suppliers/nooelec-17 (only SAWbird NOAA found)
  - https://www.digikey.com/en/products/result?keywords=TQP3M9037-PCB ($128.91, per search B)
  - https://www.minicircuits.com/WebStore/dashboard.html?model=ZX60-P162LN%2B ($128.77, per search A, not re-verified)
  - Nooelec SAWbird+ GOES datasheet (local /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p5h1b/dl/100792.bin): 1688 MHz centre, 70 MHz BW, OP1dB +20 dBm

