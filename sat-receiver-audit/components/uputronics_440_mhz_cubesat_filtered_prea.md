# Uputronics 440 mhz cubesat filtered prea: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e32114dd-52d`_

- **Part:** 70 cm (435-438 MHz) filtered preamp, the first part after the UHF antenna on P2, RTL-A T2, bias on ch2 of the 4.5 V LNA rail
- **Current pick:** Uputronics FPA "440MHz CubeSAT" filtered preamp (HAB-FPA440). Signal path: limiter, then HPF below 100 MHz, then PSA4-5043+ LNA, then 440 MHz / 30 MHz SAW. V3 aluminium enclosure 69x40x12 mm, SMA-F in and out. Datasheet Rev 3.0 (18/10/2024).
- **Current price usd:** STACK.md lists 68.71 (GBP 51.59 incl. UK VAT). I re-checked all five Shopify storefronts on 18 Oct 2026 and all show the 440MHz CubeSAT variant as available=true:
  - DE, FR and NL: EUR 52.95, "Shipping, taxes, & promos calculated at checkout". That is 59.52 at 1.1241, before VAT.
  - UK: GBP 51.59 "Tax included" (68.71). Ex-VAT that is GBP 42.99, or 57.25.
  - US: 62.00.
  EU landed cost (model): EUR 63.0-64.1 = 70.8-72.0 at 19-21% VAT, or 69.6-75.6 across the EU's full 17-27% VAT range. Shipping was not checked.
- **Decision:** keep
- **Chosen:** Keep the Uputronics 440MHz CubeSAT FPA. Buy it direct from store.uputronics.com, EU storefront, EUR 52.95 plus VAT at checkout. Make sure it is the V3/Rev 3.0 board. Do not buy from Kubii: it is pre-order only, costs more, and its listing describes an older board.
- **Chosen price usd:** 59.52 ex-VAT (EUR 52.95, the stack's USD-without-import-VAT basis). EU landed is about 70.8-72.0 at 19-21% VAT, plus shipping (not verified).
- **Saving usd:** 0.00 real saving; no analog survives. The BOM line drops from 68.71 to 59.52 (-9.19) only because the price basis changes from UK incl. VAT to EU ex-VAT. An EU buyer actually pays about 70.8-72.0 plus shipping, which is the same as or slightly more than the old 68.71. This must not be reported as a saving.
- **Equivalence proof:** The chosen part is the same SKU as the current pick. I checked its specs on primary sources myself:
  
  - **Datasheet Rev 3.0 text** (pdftotext of HAB-FPA_Series.pdf):
    - NF "Average 0.75dB"
    - supply 3.5-5.5 V; "Exceeding 5.5V will cause permanent damage"
    - about 50 mA
    - 440 MHz gain "at least 19dB", V3 enclosure 69x40x12 mm
    - -40 to +85 C
    - antenna port DC-blocked, Skyworks limiter, HPF below 100 MHz on all models
    - unpowered: "no passthrough of signal and the unit attenuates heavily"
    - not IP rated
    - CE and UKCA declarations on p.15-16
  - **440 MHz plot, which I rendered from p.10:** 19.63 dB at 440 MHz, 16.27 dB at 427.33 MHz, 16.17 dB at 452.0 MHz. So 435-438 MHz sits on the flat top. The far stopband is about -36 to -38 dB (about 55 dB below the passband), and it is about -20 dB near 470 MHz. The trace is the vendor's own Rigol plot marked UNCAL, not an independent measurement.
  - **434 MHz variant plot (p.9):** 20.25 dB at 434 MHz, 16.08 dB at 437.67 MHz (-4.2 dB), so it is too narrow.
  - **Datasheet on the wideband unit:** "The wideband unit is not fitted with any filter."
  
  Compatibility is unchanged:
  - About 4.4 V at the preamp after the TPS2553, the INA3221 0.2 ohm shunt and the choke (model). That is inside 3.5-5.5 V.
  - 50 mA is well under the ch2 limit of 144-192 mA.
  - SMA, no driver needed, same mechanics.
  - Receive-only, with no TX path and no loop.
- **Rejected:**
  1.
    - **Name:** Uputronics 434MHz HABAmp/CubeSAT/ISM FPA (EUR 42.95 = $48.28 ex-VAT; GBP 41.99; US $50)
    - **Why:** Worse in the critical passband spec. The vendor plot (datasheet p.9, rendered and read by me) shows 16.08 dB at 437.67 MHz against 20.25 dB at its peak, a 4.2 dB loss. ISS SSTV 437.550 and APRS 437.825 fall on the SAW skirt, where NF and group delay are unspecified.
  2.
    - **Name:** Uputronics Wideband 100 MHz-4 GHz FPA (EUR 42.95 = $48.28 ex-VAT)
    - **Why:** The datasheet says it has no filter, which loses about 40-55 dB of rejection against DVB-T 470+, LTE800, GSM900, TETRA and 2 m. It also uses the larger V2 case (63.5x63.5x30 mm).
  3.
    - **Name:** Same SKU from Kubii FR, ref HAB-FPA440
    - **Why:** I verified it through the PrestaShop variant refresh (group[71]=327, attribute 1310): 'Pre-order EUR 65.95 incl. VAT' = $74.13 ($61.78 ex-VAT, which is more than $59.52). Stock shows -1, 'Supplier stock. Available within 15 days', with back in stock estimated 23/10/2026. The description still shows the old '5V to 26V' regulator, so the revision is uncertain. The static page's EUR 47.64 headline is not the 440 price. For a French buyer, Kubii's intra-EU landed price could come close to Uputronics direct plus UK shipping, but that cannot be verified without both checkouts, and Kubii's pre-order status and revision doubt still rule it out.
  4.
    - **Name:** Same SKU, Uputronics US storefront ($62.00) or Wegmatt US ($68, out of stock per search)
    - **Why:** More expensive than the EU storefront for an EU address. Wegmatt also adds US-to-EU import VAT.
  5.
    - **Name:** LNA4ALL 9A4QV, assembled with 2x SMA plus bias-T mod (EUR 23 + 3 + 7 shipping = EUR 33 = $37.10, prices verified on lna4all.blogspot.com, undated price list, stock note May 2025)
    - **Why:** It has the same PSA4-5043+ MMIC, and its NF and linearity are equal or better. But it covers 28 MHz-2.5 GHz with no filter, no limiter, no HPF below 100 MHz and no enclosure (bare PCB). It loses about 40-55 dB of rejection. Closing the gap needs an external 70 cm filter. The Nooelec Ham Filter Bank costs $66.95 (verified on the Nooelec store), so LNA4ALL plus that filter is about $104, more than $59.52. A cheaper filter would be DIY and unmeasured. The bias-T is a mod, and I found no CE DoC.
  6.
    - **Name:** RTL-SDR Blog Wideband LNA (V2 already in the stack as the bench spare, $19.95) + Nooelec Ham Filter Bank Barebones
    - **Why:** The filter bank alone is US$66.95 (verified), which is more than $59.52. Its first stage is unfiltered, with no limiter or HPF, it draws 90 mA, and it needs two boxes. Using it would also take away the bench spare. D8 already rejected this combination.
  7.
    - **Name:** GPIO Labs 433 MHz Filtered LNA 20 dB (Tindie, $57.00, 'Only 8 left', ships from Canada)
    - **Why:** I verified the page. The passband is '430 - 436 MHz', so 437.55-437.825 is outside the spec. NF is only bounded at '<1 dB', against 0.75 dB average. Out-of-band is '<-20 dB' at 50-400 MHz and '<-15 dB' at 480-1000 MHz, weaker than the current part. Max input is given as both -10 and -15 dBm. Connectors and enclosure are not stated. The bias tee needs a user-soldered 10 uH inductor. Landed in the EU with shipping and import VAT it costs more than the current part.
  8.
    - **Name:** GPIO Labs 433 MHz 40 dB version
    - **Why:** Same 430-436 MHz passband gap. Its 40 dB of gain would overload the RTL-SDR V4L. B reports $96.
  9.
    - **Name:** Janilab/Janielectronics (HU) 70 cm LNA with SAW, about $30-38 (eBay, not verified; eBay returned 403)
    - **Why:** The cq.sk review (8 Aug 2026), which I fetched, gives NF 1.8 dB and gain +18 dB for 430-446 MHz. Those are vendor figures, not measured by the reviewer. Against 0.75 dB and at least 19 dB, it is worse in both NF and gain. Rejection, linearity, connectors and enclosure are unpublished.
  10.
    - **Name:** Decent Labs Spacewalker LNA 434 MHz (CrowdSupply)
    - **Why:** I fetched the page on 18 Oct 2026: 'This project is launching soon', with no price or ship date. Its passband, P1dB/IP3 and supply range are not stated. It cannot be bought.
  11.
    - **Name:** vhfdesign LNA-70cm-ATF531-SAW
    - **Why:** Its RF specs are better (NF <0.4 dB, >22 dB gain, OIP3 37 dBm, verified on the page). But it needs '12 V & 140 mA' (8-12 V), which does not fit the 4.5 V ch2 bias bus. It uses N-female connectors, weighs 150 g, has no listed price, and its -3 dB bandwidth is under 20 MHz (edges not given). It is incompatible.
  12.
    - **Name:** Generic SPF5189Z boards and AliExpress 'full band' LNAs
    - **Why:** Both are unfiltered, with no measured NF at 70 cm. They take 5 V header power rather than a bias tee. The SPF5189Z is EOL at Qorvo, so these boards carry counterfeit risk, and there is no CE DoC.
  13.
    - **Name:** RTL-SDR Blog Wideband LNA bought new
    - **Why:** Unfiltered. The stack already holds one as a bench spare.
  14.
    - **Name:** DIY PSA4-5043+ + Akoustis SF2446E SAW (BOM about $20-35, estimate)
    - **Why:** There is no measured evidence for it: SAW stopband not read, layout and stability unproven. The stack has no calibrated ENR source, so an NF of 0.75 dB or better cannot be proven. There is no CE DoC, and it costs build labour.
  15.
    - **Name:** Nooelec SAWbird family
    - **Why:** I checked the full Nooelec SAWbird category (?limit=all) on 18 Oct 2026. It has NOAA, GOES, IR, iO, H1 and ADS-B models only. There is no 70 cm model.
  16.
    - **Name:** Used Uputronics 440
    - **Why:** None found in search B. The only hit was an 868 MHz unit.
- **Confidence:** high
- **Conditions or tests:** No replacement, so these are acceptance tests for the kept part. Measure everything conducted only.
  1. On arrival, confirm it is the V3 enclosure and the Rev 3.0 board (3.5-5.5 V input).
  2. On ch2 at the actual feed voltage (about 4.4 V at the preamp), the INA3221 should read about 50 mA. Store that as the labd alarm baseline.
  3. Bench mode, 50 ohm terminations, tinySA as the source at -40 dBm or lower into ANT:
     - gain at least 19 dB at 435.0, 437.55 and 437.825 MHz;
     - -3 dB edges near 427 and 452 MHz;
     - rejection at 470 MHz and 800-960 MHz recorded in parts.yaml.
  4. Unpowered: the path must be heavily attenuated. The UI must show "ch2 off = no UHF".
  5. Never put more than 5.5 V on P2. A 12.5 V or 13.2 V source must never be able to mate with it.
  6. At checkout, confirm that VAT is collected at sale (IOSS, so the courier adds no fee) and check the shipping cost. If the delivery address is in the UK, the price is GBP 51.59 incl. VAT ($68.71).
  
  The WebSearch budget was exhausted on my first query (turn-wide limit). Instead I verified with direct fetches of primary pages: the Uputronics .js and HTML for DE, FR, NL, GB and US; the datasheet PDF; Kubii's variant endpoint; Tindie; the LNA4ALL blog; cq.sk; CrowdSupply; vhfdesign; and the Nooelec catalogue. Products that only a search could turn up (AliExpress 435 MHz SAW-LNA boards, the SV1AFN store, which is JavaScript-rendered and showed nothing) were not checked further.
- **Stack changes:** The part, rails, connectors, drivers and case all stay the same. Documentation changes only:
  - **BOM row 2.3:** price 68.71 → 59.52 (EUR 52.95, Uputronics EU storefront, ex-VAT). Note: "EU landed about 70.8-72.0 at 19-21% VAT plus shipping; UK GBP 51.59 incl. VAT; US $62.00". The group subtotal falls 9.19 on the ex-VAT basis, but this is not a real saving.
  - **Bias text:** replace "current boards '5V max' (register #98)" with "Rev 3.0: 3.5-5.5 V, >5.5 V permanent damage, about 50 mA". That closes #98 on paper and keeps the ch2 measurement.
  - **D8/5.3 wording:** "SAW 30 MHz" → "passband about 427-452 MHz at -3.4 dB (vendor UNCAL plot)".
  - **Shopping order:** buy from Uputronics direct, not Kubii.
  - **Unchanged:**
    - rain cover (not IP rated);
    - mount on an SMA M-F jumper or bracket, not cantilevered on P2;
    - "never substitute the 434 MHz variant";
    - the HMC7992 route.
- **Sources:**
  - https://store.uputronics.com/products/uputronics-filtered-preamps.js?country=DE
  - https://store.uputronics.com/products/uputronics-filtered-preamps.js?country=GB
  - https://store.uputronics.com/products/uputronics-filtered-preamps.js?country=US
  - https://store.uputronics.com/products/uputronics-filtered-preamps?country=DE
  - https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf?v=1729257808
  - https://www.kubii.com/en/network-modules/3349-lna-amplifier-modules-with-saw-filter-and-single-frequency-3272496306646.html
  - https://www.kubii.com/en/index.php?controller=product&id_product=3349&group[71]=327 (ajax refresh, attribute 1310)
  - https://www.tindie.com/products/gpio/433-mhz-filtered-low-noise-amplifier-lna-20-db/
  - https://lna4all.blogspot.com/
  - https://cq.sk/en/lna-diplexer-filter-janielectronics/
  - https://www.crowdsupply.com/decent-labs/spacewalker-lna-434-mhz
  - https://vhfdesign.com/lnas/lna-eme-atf531-for-2m-and-70cm-bands.html
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird.html?limit=all
  - https://www.nooelec.com/store/catalogsearch/result/?q=ham+filter+bank
  - https://www.minicircuits.com/pdfs/PSA4-5043+.pdf

