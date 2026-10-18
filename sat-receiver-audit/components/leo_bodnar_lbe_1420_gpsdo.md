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

