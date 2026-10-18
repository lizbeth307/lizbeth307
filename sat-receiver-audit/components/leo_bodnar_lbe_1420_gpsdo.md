# Leo bodnar lbe 1420 gpsdo: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_c3ba734e-52b`_

- **Part:** Leo Bodnar LBE-1420 GPSDO (extended lab tier, qty 1). Two jobs: the GNSS-locked 10 MHz or 30.72 MHz CMOS reference into LimeSDR Micro J4, and the conducted calibration tone behind 80 dB of pads plus a BLK-89-S+ DC block.
- **Current pick:** Leo Bodnar LBE-1420 GPSDO locked clock source (EAN 5060992290020): 1 Hz-1.1 GHz, +11 dBm 3.3 V CMOS into 50 Ohm, -164 dBc/Hz at 1 MHz offset, USB-C 5 V 250 mA, HID 1dd2:2443, 69x40x12 mm, 2-year warranty, CE/FCC/UKCA, active antenna included.
- **Current price usd:** 175.80 = GBP 132.00. I checked the Bodnar cart (session only, no order placed): it shows "£132.00 (Incl. VAT)", so this is a UK price including 20% VAT. The stack's "VAT basis not stated" is now resolved. For this Europe-based user, the same seller with Region "European Union" charges EUR 137.94 net ($155.06) plus destination VAT. The cart shows "Inclusive of VAT/tariffs" and "duties and taxes paid by LBE"; orders ship from SkunkRF in France. Checkout amounts: DE EUR 164.15 (19%), FR 165.53 (20%), NL and ES 166.91 (21%), IT 168.29 (22%), PL 169.67 (23%), HU 175.18 (27%). EU Mail shipping is EUR 6.90-10.33. Landed: EUR 171.76 for DE (= $193.08 at the stack's 1.1241 USD/EUR) up to EUR 185.51 for HU ($208.53).
- **Decision:** keep
- **Chosen:** Keep the Leo Bodnar LBE-1420, bought direct from leobodnar.com with Region set to "European Union". It ships from SkunkRF in France with VAT and duties paid, so there are no import charges. Do not buy it from Batronix or Uputronics.
- **Chosen price usd:** EUR 164.15 incl. 19% VAT + EUR 7.61 shipping = EUR 171.76 = $193.08 for a German address. The general rule is EUR 137.94 net ($155.06) x (1 + destination VAT) + EUR 6.90-10.33 EU Mail, which gives $193.08-208.53 landed across the 7 EU countries checked. Stack basis: $175.80 = GBP 132 incl. UK VAT.
- **Saving usd:** 0.00. No cheaper analog survived, so the part stays. Seller check: Bodnar-EU beats the Batronix price the search had marked "cheapest" by EUR 20.30 (= $22.82) on goods for a DE address (164.15 vs 184.45 incl. 19% VAT), plus Batronix shipping, which is charged below a EUR 200 order. Net, Bodnar-EU is EUR 137.94 vs Batronix EUR 155.00. Correction for v2: $175.80 understates the EU landed cost by about $17-33.
- **Equivalence proof:** This is a keep, so no analog has to prove equivalence. For the sourcing claim: Bodnar is the manufacturer, and the EAN 5060992290020 and the spec list are the same on Bodnar and Batronix (both fetched today). The not-worse specs for this stack, rechecked on the primary pages:
  (1) Range 1 Hz-1.1 GHz with 'infinite resolution'. This covers 10 MHz and exact 30.72 MHz for J4 (10-52 MHz) and the conducted tones up to 1.1 GHz.
  (2) 3.3 V CMOS square wave, 50 Ohm source, +11 dBm at 10 MHz, rise/fall 300/260 ps. Matches J4's 1.8-3.3 V CMOS input.
  (3) Phase noise at 10 MHz: -72/-101/-128/-147/-156/-159/-164 dBc/Hz from 1 Hz to 1 MHz; sub-ps jitter.
  (4) Stability approaches 1e-12. febo's maser test of an older Bodnar unit measured -1.55e-11.
  (5) Holdover: a digital PLL keeps the best estimated frequency; about 30 s to acquire.
  (6) USB-C 5 V, 250 mA max.
  (7) 69x40x12 mm.
  (8) The Bodnar page itself links simontheu/lbe-1420 as its Linux CLI. bvernoux/lbe-142x lists 0x2443 (f1 up to 1.6 GHz) but is tested only on Ubuntu 24.04 x64, so the arm64 build stays a bench test.
  (9) CE/FCC/UKCA, 2-year warranty.
  
  Every cheaper candidate gave up at least one of these, or its price or availability was not real (see rejected).
  
  Two claims from the searches are refuted:
  - "GBP 132 / EUR 165.53 are ex-VAT, landed about EUR 197-205". Wrong: both carts say "Incl. VAT" and "Inclusive of VAT/tariffs".
  - "Batronix is the cheapest verified EU listing, $1.56 cheaper". Wrong: it compared Batronix's net price with Bodnar's VAT-inclusive price.
  
  Limit: the shared web-search budget ran out on my first query, so I could not search for new candidates. This verification covers only the candidates from the two searches, checked by direct fetches of primary pages.
- **Rejected:**
  1.
    - **Name:** Batronix (DE), same SKU LBE-1420
    - **Why:** Same device, but dearer. EUR 155.00 net vs Bodnar-EU EUR 137.94 net; EUR 184.45 incl. 19% VAT vs Bodnar EUR 164.15 incl. 19% for a DE address. Batronix ships free to the EU only from EUR 200 of goods, so its shipping comes on top. Its page does not say it is an authorized Bodnar distributor. Not cheaper, so rejected as the seller.
  2.
    - **Name:** Uputronics (UK), same SKU
    - **Why:** GBP 158.40 tax included; the Shopify product JSON says available=true. It ships from the UK, so an EU buyer also pays import VAT, normal customs duty above EUR 150 and the handling fee (operator notes 34/35). Clearly dearer than Bodnar-EU, which ships duty-paid.
  3.
    - **Name:** Leo Bodnar Mini Precision GPS Reference Clock
    - **Why:** Same price (EUR 165.53 FR / GBP 132). Range 400 Hz-810 MHz, so no tones above 810 MHz. Phase noise -150/-153/-155 dBc/Hz at 10k/100k/1M vs -156/-159/-164. Output +10.3 dBm max. Mini-USB. Bodnar itself recommends the LBE-1420 instead. Worse and not cheaper.
  4.
    - **Name:** Leo Bodnar LBE-1421 (new)
    - **Why:** Better spec (1.4 GHz, two outputs, PPS, same size and power, lbe-142x PID 0x2444) but dearer: GBP 198 / EUR 248.29 (FR) at Bodnar, EUR 267.75 at Batronix. Not a cheaper analog.
  5.
    - **Name:** Leo Bodnar LBE-1423 / LBE-1425 / original 2-output Precision GPS Reference Clock
    - **Why:** All dearer: EUR 303.47 / 455.20 / 250.36 at the 21% VAT basis in the Bodnar EU catalogue. The original BNC unit is also worse: 450 Hz-800 MHz and worse phase noise.
  6.
    - **Name:** Used LBE-1420 or LBE-1421 (eBay, including the USD 120 sale)
    - **Why:** Not buyable today. eBay returned 403 to both fetch methods, so nothing could be verified. The USD 120 sale has already closed and its model is ambiguous (it may be the older BNC 2-port unit, which is worse). The 2-year warranty probably does not transfer, which makes it worse on warranty. Its price and availability are not real.
  7.
    - **Name:** Elektronik-Idee GPSDXO 40/10 MHz (Tindie, USD 94.90)
    - **Why:** Fixed 10 MHz sine at only 1-2 dBm (about 0.8 Vpp), below J4's 1.8-3.3 V CMOS input, plus 40 MHz at 1.2 Vpp and 1PPS. No 30.72 MHz and no 1.1 GHz tones. Phase noise -112/-130/-150 at 1k/10k/>=100k (vs -147/-156/-159). Accuracy only 1 ppb. The page contradicts itself on the oscillator ('temperature controlled' vs 'no temperature or oven controlled oscillator') and on the connector (USB-C vs a micro-USB cable). Clone-class ATGM336H GNSS module. 88x38x103 mm, 200 g. Stock is not shown.
  8.
    - **Name:** BG7TBL 10 MHz OCXO GPSDO
    - **Why:** Not cheaper ($205 + $15.88 per the search listing, not re-fetched). Fixed 10 MHz sine, so no 30.72 MHz, no tones, and J4 would need a squarer. 12 V at up to about 15 W with OCXO warm-up; bench-box size. In febo's maser test the 2019 unit showed a -9.62e-11 average offset (vs -1.55e-11 for the Bodnar) and an ADEV hump more than 10x worse; quality varies widely between versions.
  9.
    - **Name:** QRP Labs ProgRock2 + QLG GPS kit
    - **Why:** 3.5 kHz-200 MHz, so no tones up to 1.1 GHz. No phase-noise or jitter figure is published. The page says only 'GPS frequency discipline using 1pps', with no documented lock or holdover behaviour. Si5351A/MS5351M is a clone-capable part. Bare board, ships from outside the EU (duty), and labd has no driver for it. Worse in range, purity evidence and build.
  10.
    - **Name:** gpsfreak open hardware (LMK05318B + MAX-M10S)
    - **Why:** DIY only. Range, phase noise, ADEV and accuracy are all unmeasured, with no certification or warranty, and arm64 tool support is not stated. It fails the requirement for verified specs and build quality.
  11.
    - **Name:** DIY OCXO GPSDO / used telecom GPSDO (Z3805A, Thunderbolt class)
    - **Why:** Fixed 10 MHz only, so they fail the 30.72 MHz and 1.1 GHz tone roles. They draw several watts from 12 V or more with warm-up, are bench-sized, and have no USB HID control. Better close-in stability does not offset failing those roles and the size and power limits.
  12.
    - **Name:** PPS count + GNSS-SDR ppm (already in core)
    - **Why:** Not an RF source: it cannot drive J4 or give a conducted tone. It is a fallback, not an analog.
- **Confidence:** high
- **Conditions or tests:** Ordering:
  - On leobodnar.com, set Region = European Union. Confirm at checkout the line "EU Mail Service ... duties and taxes paid by LBE" and an amount equal to EUR 137.94 x (1 + your VAT); expect DE EUR 164.15 + EUR 7.61.
  - Opportunistic only, not a replacement: a used LBE-1420 (PID 0x2443) or LBE-1421 (PID 0x2444) may be bought if all of these hold:
    - the landed price is clearly below the Bodnar-EU landed price for the user's country (for example EUR 171.76 for DE);
    - SMA and USB-C connectors, antenna included, firmware 1.08 or later;
    - `lbe-142x --status` shows lock before payment;
    - the user accepts losing the warranty.
  Bench tests on arrival (unchanged):
  - Build bvernoux/lbe-142x on arm64 (or simontheu/lbe-1420) and run --status.
  - Set 10 MHz. Through 80 dB + BLK-89-S+ into the tinySA, expect -69 dBm +/-3 dB, and record the 30/50 MHz harmonic levels.
  - Scope the J4 swing at 30.72 MHz and 10 MHz; run the 1 ppm shift test.
  - Keep it in a still-air pouch during Lime trims: EEVblog notes a stability wobble from airflow.
  Rules kept: conducted-only, off and disconnected during H1, ADS-B and Inmarsat-C sessions, never into an antenna.
- **Stack changes:** No changes to rails, connectors, drivers or the case: same part, LAB 5 V rail at 250 mA, SMA, hidraw 1dd2:2443.
  Text corrections for v2 in /home/user/lizbeth307/sat-receiver-audit/STACK.md:
  (1) GPSDO BOM row (line 363) and the extended order step (line 1130): replace "GBP 132; VAT basis not stated" with "GBP 132 incl. UK VAT. EU: leobodnar.com Region 'European Union', EUR 137.94 net + destination VAT (DE EUR 164.15), EU Mail EUR 6.90-10.33, ships from SkunkRF France with duties and taxes paid; landed DE EUR 171.76 = $193.08".
  (2) Customs paragraph (line 1132): take Leo Bodnar off the list of UK sellers with import VAT and a broker fee for EU buyers, since EU orders ship from inside the EU duty-paid. Uputronics UK stays on it.
  (3) Extended-tier totals: at a DE address, use $193.08 for the GPSDO line instead of $175.80 (+$17.28).
  (4) Software note: the Bodnar product page names simontheu/lbe-1420 as its Linux CLI; bvernoux/lbe-142x is the primary tool but is tested only on Ubuntu 24.04 x64. Keep the arm64 build as a bench test and limit --f1 to 1.1 GHz.
- **Sources:**
  - https://www.leobodnar.com/shop/index.php?main_page=product_info&products_id=393
  - https://www.leobodnar.com/shop/index.php?main_page=shopping_cart (cart/shipping-estimator session, 18 Oct 2026: GBP 132.00 'Incl. VAT'; EU EUR 164.15 DE / 165.53 FR / 166.91 NL,ES / 168.29 IT / 169.67 PL / 175.18 HU 'Inclusive of VAT/tariffs'; EU Mail EUR 6.90-10.33 'duties and taxes paid by LBE')
  - https://www.leobodnar.com/shop/index.php?main_page=shippinginfo
  - https://www.leobodnar.com/shop/index.php?main_page=index&cPath=107
  - https://www.leobodnar.com/shop/index.php?main_page=product_info&products_id=301
  - https://www.leobodnar.com/shop/index.php?main_page=product_info&products_id=399
  - https://www.batronix.com/shop/frequency-references/GPSDO/LBE-1420.html
  - https://www.batronix.com/versand/index.html
  - https://www.batronix.com/shop/shopping/vat-information.html
  - https://store.uputronics.com/products/lbe-1420-gps-locked-clock-source
  - https://raw.githubusercontent.com/bvernoux/lbe-142x/main/README.md
  - https://www.tindie.com/products/elidee/gps-disciplined-4010mhz-frequency-source-0001ppm/
  - https://qrp-labs.com/progrock2.html
  - https://blog.febo.com/?p=636
  - https://www.ebay.com/itm/277703990794 (403, unverifiable)
  - https://www.ebay.com/itm/116984943460 (403, unverifiable)

_Run `wf_c3ba734e-52b`_

- **Part:** GPSDO / GNSS-locked reference and conducted calibration-tone source (extended lab tier, qty 1)
- **Current pick:** Leo Bodnar LBE-1420 GPSDO locked clock source (EAN 5060992290020): 1 Hz-1.1 GHz, 3.3 V CMOS square wave, 50 ohm source, +11 dBm at 10 MHz, USB-C 5 V 250 mA, 69x40x12 mm, HID 1dd2:2443, active antenna with 5 m cable included
- **Current price usd:** 175.80 (GBP 132.00). Correction: the cart on 18 Oct 2026 shows GBP 132.00 '(Incl. VAT)' for a UK address, so this figure includes UK VAT. The VAT basis is no longer unknown.
- **Decision:** keep
- **Chosen:** Keep the Leo Bodnar LBE-1420, but change where it is bought. Order direct from leobodnar.com in the 'European Union' region. These orders ship from the EU partner SkunkRF in France on 'EU Mail Service (2-3 working days, duties and taxes paid by LBE)'. Cart and shipping estimates on 18 Oct 2026, item plus shipping incl. destination VAT: Germany EUR 164.15 + 7.61 = EUR 171.76; France EUR 165.53 + 6.90 = EUR 172.43; Poland EUR 169.67 + 10.01 = EUR 179.68. All three are EUR 137.94 net plus the destination VAT rate.
- **Chosen price usd:** 193.08 landed for DE (EUR 171.76 at 1.1241 USD/EUR, the rate the upstream search used, not re-checked). FR 193.83, PL 201.98. Net of VAT: EUR 137.94 = 155.06.
- **Saving usd:** 0.00 at part level: no cheaper part is not-worse, so the part stays. Seller level: Bodnar-EU DDP is cheaper than the best other EU listing, Batronix (EUR 184.45 incl. 19% VAT + shipping not shown). The landed saving is at least EUR 12.69 (= $14.26) plus Batronix's shipping. On the item price alone it is EUR 20.30 (= $22.82). Note: the stack's $175.80 is a UK price incl. UK VAT. The true EU landed cost is about $193 (DE), so the v2 BOM line goes up by about $17.28. It does not go down.
- **Equivalence proof:** The chosen item is the same SKU (EAN 5060992290020) from the manufacturer, so every spec is the same by definition. Specs that matter here, checked on leobodnar.com and Batronix on 18 Oct 2026:
  (1) Range 1 Hz-1.1 GHz with 'infinite resolution'. It hits 10 MHz and exactly 30.72 MHz for Lime J4 (firmware accepts 10-52 MHz), and gives GNSS-locked tones up to 1.1 GHz for RTL-SDR V4L, Airspy HF+, tinySA and Lime VCTCXO ppm checks.
  (2) Output: 3.3 V CMOS square wave, 50 ohm source, +11 dBm at 10 MHz, rise/fall 300/260 ps. It drives J4 directly with no squarer.
  (3) Phase noise at 10 MHz, typical: -72/-101/-128/-147/-156/-159/-164 dBc/Hz at 1 Hz-1 MHz; sub-ps RMS jitter.
  (4) Accuracy about 1e-12 when locked. EEVblog (Wim13, against Rb) measured 1 s ADEV of about 5e-11 and some 5e-11 to 1e-10 wander that depends on airflow and temperature (Leo Bodnar: 10-1000 s depends on ambient). This is adequate for ppb-level SDR calibration.
  (5) Glitchless holdover entry and exit; usable after about 30 s.
  (6) USB-C 5 V, 250 mA max.
  (7) 69x40x12 mm.
  (8) SMA antenna port with 3.3 V / 30 mA bias; inside is a u-blox M10050KB (GPS, Galileo, BeiDou; EEVblog).
  (9) Linux arm64: bvernoux/lbe-142x v1.2 (20 Apr 2026) lists LBE-1420 = 0x2443, up to 1600 MHz, with --f1/--f1t/--status/--monitor. It builds with cmake and libudev-dev. Settings are kept in flash.
  (10) CE/FCC/UKCA, 2-year warranty, bought from the manufacturer, so it cannot be a counterfeit.
  (11) Rules: conducted-only source with no transmit function. The rules are unchanged.
  Adversarial result: every other candidate is worse in at least one spec that matters (see rejected), or its price or availability is not real. Two corrections to the searches: (a) their claim that GBP 132 / EUR 165.53 are ex-VAT is wrong; the cart says 'Incl. VAT' and '(Inclusive of VAT/tariffs)'. (b) Batronix is therefore not the cheapest EU route; Bodnar-EU DDP is.
- **Rejected:**
  1.
    - **Name:** Same SKU from Batronix (DE)
    - **Why:** Not cheaper. EUR 155 net / EUR 184.45 incl. 19% VAT, with 'Plus Shipping Costs' (amount not shown, unverified). Bodnar-EU's net is EUR 137.94, which is EUR 17.06 lower before VAT. Both charge VAT at the destination rate, and Bodnar-EU shipping (EUR 6.90-10.01) is less than that net gap times (1+VAT). So Bodnar-EU is cheaper landed whatever Batronix charges for shipping. The specs are identical. Fallback only: if Bodnar-EU stock runs out, ask Batronix to apply its 'best price guarantee' (it excludes offers from outside the EU; whether SkunkRF/Bodnar-EU qualifies is unverified).
  2.
    - **Name:** Same SKU from Uputronics (UK)
    - **Why:** Not cheaper and not EU stock. The product JSON on 18 Oct 2026 shows GBP 158.40 'Tax included' with available=true; the page also carries a 'Sold Out' template string. That is 20% above Bodnar's own UK price incl. VAT. To the EU it ships from the UK on a consignment above EUR 150, so import VAT, normal duty, the EUR 2 Union handling fee from about 1 Nov 2026 and courier fees all apply (operator notes 34-35). The landed cost is above EUR 172 (model).
  3.
    - **Name:** Leo Bodnar LBE-1420 or LBE-1421, used (eBay)
    - **Why:** Price and availability are not real. No current used listing was found (WebSearch, 18 Oct 2026; eBay pages return 403). The USD 120 'used' sale has already sold and its model is ambiguous: it may be the older BNC 2-port unit, which is worse. A US eBay purchase adds EU import VAT, duty and the handling fee. It also loses the 2-year manufacturer warranty, which is a reliability downgrade. Also, early units had a GPS fault after firmware 1.05 (EEVblog, EvgenyG). Opportunistic only, and only if landed price <= EUR 171.76, PID 0x2443/0x2444, SMA + USB-C, antenna included, firmware >= 1.08, and a lock shown with lbe-142x --status.
  4.
    - **Name:** Leo Bodnar LBE-1421 (new)
    - **Why:** A superset in specs (Out1 1 Hz-800 MHz or 1PPS, Out2 1 Hz-1.4 GHz, 1 uHz resolution, +11 dBm below 400 MHz, same 250 mA, 69x40x12 mm, supported by lbe-142x as 0x2444; datasheet V1.0, 15 Jul 2025), but more expensive: GBP 198 at Bodnar, EUR 225 net at Batronix (search result). Not a cheaper analog.
  5.
    - **Name:** Leo Bodnar Mini Precision GPS Reference Clock
    - **Why:** Same GBP 132, so not cheaper, and worse. Range is 400 Hz-810 MHz (vs 1 Hz-1.1 GHz). Phase noise at 10 MHz is -70/-100/-125/-145/-150/-153/-155 dBc/Hz (vs -72/-101/-128/-147/-156/-159/-164), so 6-9 dB worse at 10 kHz-1 MHz. Output is at most +10.3 dBm at 32 mA drive, and it uses a mini-USB connector. Bodnar's own page says 'We recommend a newer version of this product' and links to the LBE-1420.
  6.
    - **Name:** Leo Bodnar original 2-output Precision GPS Reference Clock (BNC)
    - **Why:** Worse: range 450 Hz-800 MHz, worse phase noise (-143 at 1 kHz, -155 at 1 MHz), BNC connectors, larger, and not listed in lbe-142x (no arm64 control path). New price GBP 198, so not cheaper.
  7.
    - **Name:** Elektronik-Idee GPSDXO 10/40 MHz (Tindie, DE)
    - **Why:** USD 94.90, but worse in almost every spec that matters. Outputs are fixed: 10 MHz sine at 1-2 dBm, 40 MHz at about 1.2 Vpp, 1PPS. It cannot give 30.72 MHz or tones. Phase noise is -112/-130 dBc/Hz at 1 kHz/10 kHz (vs -147/-156), 26-35 dB worse. Accuracy is 1 ppb typical (0.5 ppb best), versus about 1e-11. A sine at 1-2 dBm into J4 (CMOS input) is unverified. It measures 88x38x103 mm and 200 g. The GNSS is an ATGM336H. The page contradicts itself (USB-C vs micro-USB; 50 mA vs 90-110 mA; CR2032 vs CR3032), and stock is not shown.
  8.
    - **Name:** BG7TBL 10 MHz OCXO GPSDO
    - **Why:** Fails the role. Output is a fixed 10 MHz sine (about +13 dBm) with 1PPS: no 30.72 MHz and no tones up to 1.1 GHz. It needs about 12 V at up to about 15 W with OCXO warm-up (older listing), is bench-box sized, and has no USB HID control or lock reporting to labd. Versions vary a lot from unit to unit (febo maser test: -9.62e-11 offset on the 2019 unit). It is better only in short-term stability: EEVblog Wim13 measured about 1e-11 at 1 s and about 8e-12 offset on one unit. Not cheaper either: the eBay.de listing is USD 205 + 15.88 shipping from CN, and the USD 98 forum figure is unverified and undated.
  9.
    - **Name:** QRP Labs ProgRock2 (Si5351A/MS5351M) + GNSS 1PPS
    - **Why:** USD 18 + GNSS + case, but worse. Range is 3.5 kHz-200 MHz (vs 1.1 GHz), with two outputs in GPS mode. The chip may be the MS5351M clone (the page says 'Si5351A or MS5351M'). The page states no phase-noise data and no GPS-discipline accuracy; Si5351A measured by QRP Labs in the QCX is about -135.6 dBc/Hz at 10 kHz (vs -156). Discipline is by 1PPS counting, with no documented glitchless holdover. It is a bare board with no labd/HID lock reporting, and it ships from outside the EU.
  10.
    - **Name:** gpsfreak open hardware (LMK05318B + MAX-M10S), DIY
    - **Why:** About USD 50 (author's estimate), but phase noise, ADEV and accuracy are all unmeasured, the maximum frequency is disputed, it is DIY with no certification or warranty, and Linux arm64 support is not stated. It cannot be proven not-worse.
  11.
    - **Name:** DIY OCXO GPSDO / used telecom GPSDO (Z3805A, Thunderbolt class)
    - **Why:** Output is a fixed 10 MHz; multi-watt OCXO heating with warm-up; bench size; no USB HID control. They cannot provide the 30.72 MHz or 1.1 GHz tone roles. Prices are not verified.
  12.
    - **Name:** PPS count + GNSS-SDR ppm (software, already in core)
    - **Why:** Not an analog: it has no RF output, so it cannot drive Lime J4 or supply a conducted calibration tone.
- **Confidence:** high
- **Conditions or tests:** Sourcing: before ordering, run the Bodnar-EU cart with the user's real country and postcode. The price varies with VAT (verified DE 19% / FR 20% / PL 23%), and payment goes through PayPal, where the final shipping is shown. Choose 'EU Mail Service (duties and taxes paid by LBE)' so no import charges arrive later.
  Acceptance tests on arrival, inside the 14-day EU withdrawal window:
  (1) lbe-142x v1.2 on the Q6A (Ubuntu 24.04 arm64) enumerates 1dd2:2443 through the hidraw udev rule, and --status shows GPS lock and PLL lock within about 30 s outdoors.
  (2) --f1 10000000 and then 30720000. tinySA behind the 80 dB pad plus BLK-89-S+ reads the expected level (about +11 dBm - 80 dB = about -69 dBm at 10 MHz, model) and the frequency within the tinySA's own calibration.
  (3) A short --f1t tone at 1090/1420/1540 MHz is visible on RTL-B behind the pads, then the output is returned to 10 MHz.
  (4) The Lime J4 lock test P7, first at 30.72 MHz and then at 10 MHz.
  (5) Keep the antenna coax free of shorts: EEVblog reports that the u-blox antenna-port protection cuts bias on a shorted coax and reception degrades.
  (6) For Lime VCTCXO trims, operate the unit in still air or wrapped, because 10-1000 s stability depends on airflow and temperature.
- **Sources:**
  - https://www.leobodnar.com/shop/index.php?main_page=product_info&products_id=393
  - https://www.leobodnar.com/shop/index.php?main_page=shopping_cart (cart + Estimate Shipping, 18 Oct 2026: UK GBP 132.00 Incl. VAT; DE EUR 164.15 + 7.61; FR EUR 165.53 + 6.90; PL EUR 169.67 + 10.01; '(Inclusive of VAT/tariffs)', 'EU Mail Service ... duties and taxes paid by LBE')
  - https://www.leobodnar.com/shop/index.php?main_page=shippinginfo
  - https://www.leobodnar.com/shop/index.php?main_page=product_info&products_id=301
  - https://leobodnar.com/files/datasheets/LBE-1421-Datasheet-V1.0_Initial_Release-15-07-2025.pdf
  - https://www.batronix.com/shop/frequency-references/GPSDO/LBE-1420.html
  - https://store.uputronics.com/products/lbe-1420-gps-locked-clock-source (and .js product JSON: GBP 158.40, available=true)
  - https://raw.githubusercontent.com/bvernoux/lbe-142x/main/README.md
  - https://www.eevblog.com/forum/metrology/a-closer-look-at-the-leo-bodnar-lbe1-420-and-the-precision-gpsdo
  - https://www.tindie.com/products/elidee/gps-disciplined-4010mhz-frequency-source-0001ppm/
  - https://qrp-labs.com/progrock2.html
  - https://blog.febo.com/?p=636
  - https://www.ebay.de/itm/124281373714 (from search results; not re-fetched, eBay returns 403)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (items 34-35, EU duty and handling fee)
- **Stack changes:** No changes to rails, connectors, case or the attenuation rule. Still LAB 5 V USB-C at 250 mA max, SMA out into 80 dB + BLK-89-S+, a pouch module 69x40x12 mm, and the rule 'off and disconnected during H1, ADS-B and Inmarsat-C'.
  BOM and text edits for v2 in /home/user/lizbeth307/sat-receiver-audit/STACK.md:
  (1) GPSDO BOM line (about line 363) and shopping step 13 (about line 1130). Replace 'GBP 132; VAT basis not stated / Leo Bodnar (UK)' with: 'GBP 132 incl. UK VAT (cart, 18 Oct 2026). EU buyer: leobodnar.com EU region, ships DDP from SkunkRF (FR), EUR 164.15 incl. 19% DE VAT + EUR 7.61 EU Mail = EUR 171.76 landed (about $193.08); FR EUR 172.43; PL EUR 179.68; fallback Batronix EUR 184.45 incl. VAT + shipping.' This raises the extended-tier figure by about $17.28 in USD at the upstream rate (1.1241 USD/EUR, not re-checked).
  (2) Customs/VAT paragraph (about line 1132): Leo Bodnar is currently listed among the UK sellers that add import VAT and courier fees. For EU destinations it ships DDP from France, so there are no import charges.
  (3) Instrument software row #34 (about line 113) names 'lbgpsdo with python hid'. Align it with the re-audit: bvernoux/lbe-142x v1.2 (cmake, libudev-dev, hidraw udev rule for 1dd2:2443) as the primary tool, and keep lbgpsdo only if its LBE-1420 support is confirmed.
  (4) Add notes to the GPSDO bring-up procedure (P6/P7): the antenna-port short-protection behaviour, and still-air or wrapped operation during Lime trims.

