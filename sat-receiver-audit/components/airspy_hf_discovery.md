# Airspy hf discovery: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e32114dd-52d`_

- **Part:** Airspy HF+ Discovery (core, HF group, qty 1): 0.5 kHz-31 MHz HF/LF receiver plus second VHF receiver 64-260 MHz, on CH334F H4, in its own shield can, fed by the G6K-2F-RF K1/K2 selector
- **Current pick:** Airspy HF+ Discovery, new, ITEAD DE warehouse, SKU IM190522001EU
- **Current price usd:** 169.00 ex VAT. I checked this today through ITEAD's store API: 310 in stock. I also ran a guest cart, with nothing ordered, and VAT is added at checkout. To DE: +32.11 VAT (19 %) and DHL from the DE warehouse 4.55 + 0.86 VAT, so 206.52 landed. To FR: +33.80 VAT (20 %) and shipping 10.09 + 2.02, so 214.91 landed. To ES: +35.49 VAT (21 %).
- **Decision:** keep
- **Chosen:** Keep the Airspy HF+ Discovery and buy it new from ITEAD's DE warehouse (SKU IM190522001EU). The only real saving is timing, not a different part. If Airspy's Black Friday 2026 sale repeats at ITEAD (around 27 Nov to 1 Dec 2026), buy the same SKU then. If no sale is live by about 2 Dec 2026, buy at list.
- **Chosen price usd:** 169.00 ex VAT now (206.52 landed in DE). If the sale repeats (not announced yet, so unverified): 135.20 at 20 % off or 126.75 at 25 % off, ex VAT. That is about 166.30 or 156.24 landed in DE, assuming the same 19 % VAT and DHL rate.
- **Saving usd:** 0.00 confirmed. Conditional, only if the Black Friday 2026 sale repeats: 33.80-42.25 ex VAT, or about 40.22-50.28 landed in DE.
- **Equivalence proof:** Nothing replaces the part. Two not-worse options exist, and neither is a real saving today:
  (a) The identical SKU bought on sale. Specs are identical, but the price depends on a sale that is not announced yet.
  (b) A used genuine unit. Its availability is not real: the only lead is an eBay snippet that returns HTTP 403 and is probably expired.
  
  The bar every candidate had to meet comes from Airspy's own Discovery page, re-read today (airspy.com/airspy-hf-discovery):
  - Coverage: 0.5 kHz-31 MHz and 64-260 MHz.
  - MDS in 500 Hz: -140.0 dBm on HF at 15 MHz, -141.5 dBm at 64-118 MHz, -141.0 dBm at 118-260 MHz.
  - Noise figure: kTB in 500 Hz is -147 dBm, which gives NF about 7 dB if MDS equals the noise floor, or about 4 dB if MDS is set 3 dB above it.
  - Linearity: IIP3 +15 dBm (HF) and +13 dBm (VHF); BDR 110 dB (HF) and 95 dB (VHF); +10 dBm maximum input.
  - Preselectors: HF banks with corners at about DC, 5, 10, 17 and 31 MHz, plus VHF and FM preselectors.
  - Image rejection and IQ: 120 dB image rejection; 660 kHz alias- and image-free at 768 ksps; 18-bit DDC.
  - Clock: 0.5 ppm, adjustable in 1 ppb steps.
  - Environment and size: -45 to +85 C; 45x60x10 mm.
  
  Independent measurement (SM5BSZ via rtl-sdr.com, re-read today): at 7.2 MHz on a real antenna, with every receiver set to the same NF, results relative to the Perseus were HF+ Discovery -3 dB, HF+ Dual -10 dB, AFEDRI -15 dB, Airspy+SpyVerter -18 dB and RSP1 -23 dB.
  
  Every cheaper candidate from another brand, or another Airspy combination, failed a spec that matters here (see rejected). Other genuine EU dealers sell the identical part but are all dearer than ITEAD DE's 206.52 landed in DE: WiMo EUR 232 incl. VAT ($260.79), HamShop NL EUR 239 (VAT not stated), AstroRadio EUR 214.17 incl. 21 % IVA, Moonraker EUR 231.99.
  
  ITEAD's CN-warehouse SKU (IM190522001) is also not cheaper. Its cart today shows $169 + $5.98 shipping with no VAT collected. Because the goods are worth about EUR 150.3, just above the EUR 150 IOSS/duty-free threshold, import VAT, possible duty and a carrier fee would be due at delivery. That makes it at least $208.23, against $206.52 from DE.
- **Rejected:**
  1.
    - **Name:** SDRplay RSP1B (about $140.99 at SDRplay, out of stock; EU snippet EUR 123.13 ex VAT, unverified)
    - **Why:** Worse on its own datasheet (V1.0, downloaded today):
  - HF noise figure 22 dB at 300 kHz, 18 dB at 2-4 MHz and 15 dB at 12/25/40 MHz, against about 4-7 dB derived for the HF+. That puts the 500 Hz noise floor near -132 dBm at 12-25 MHz, against -140 dBm for the HF+, which is 8-15 dB worse. It is worse still at LF and at the NAVTEX and MW frequencies.
  - Maximum input 0 dBm continuous, against +10 dBm.
  - IIP3 and BDR not published (HF+ +15 dBm and 110 dB). The predecessor RSP1 measured 20 dB behind the Discovery (SM5BSZ).
  - 98x94x35 mm and 315 g, against 45x60x10 mm and 32 g, so it does not fit the slot or the can.
  - Specified only at 0-35 C.
  - Trim step 10 ppb, against 1 ppb.
  - A software-switchable 4.7 V bias-T on the antenna SMA adds a DC path on the antenna.
  - Closed SDRplay API and service daemon on arm64.
  It is better only in coverage above 260 MHz, bandwidth up to 10 MHz and VHF NF, none of which this role needs.
  2.
    - **Name:** Airspy Mini + SpyVerter R2 (ITEAD EU $99 + $49 = $148 ex VAT; both in stock per the store API today)
    - **Why:** About 15 dB worse in measured strong-signal dynamic range: SM5BSZ measured Airspy+SpyVerter at -18 dB, against -3 dB for the Discovery. The exact Airspy and SpyVerter revisions he used are not stated, and Airspy publishes no combined MDS, IIP3 or BDR for this pair, so parity is unproven in any case.
  Other problems:
  - Two boxes and an extra SMA joint, larger than 45x60x10 mm.
  - The SpyVerter is powered through the Mini's bias tee, which conflicts with the bias-off default and the token gate. The Mini's bias-tee capacity is unverified.
  - The VHF role needs the SpyVerter bypassed or an extra RF switch path; bypass behaviour is unverified.
  - More USB load.
  The saving would be only $21 ex VAT.
  3.
    - **Name:** Used genuine HF+ Discovery (eBay.de-indexed US listing, $110.25 + $5.02)
    - **Why:** Availability not real: eBay returns HTTP 403 again today, and the listing is probably expired; no other live used offer was found.
  The specs could be measured equal on arrival, but reliability and warranty are worse: no ITEAD 2-year quality warranty (ITEAD's page says 2 years, not 1 as stated earlier), and an unknown history of front-end ESD or overload on long wires.
  The earlier threshold of 'at most $140 landed' also mixed VAT bases: it compared a landed price including VAT with the $169 ex-VAT price. Against a new unit on sale at about $156 landed, a used unit would save only about $16-20.
  Keep it only as an opportunistic option, and only after the full conducted acceptance list: airspyhf_info, noise floor and MDS within 2 dB, a blocking check below +10 dBm, ppm against the GNSS reference, and a 60 min soak on H4. It is not the default.
  4.
    - **Name:** Used Airspy HF+ Dual Port (RigReference estimate of $133 only)
    - **Why:** About 7 dB worse in measured strong-signal dynamic range (SM5BSZ: -10 dB against -3 dB). It has no Discovery-style HF preselector bank; its spec page lists only a 'wide band RF filter bank' and tracking filters. HF starts at 9 kHz, against 0.5 kHz (harmless here, since 3-30 kHz is masked). It is 55x90x12 mm and has two RF ports, so it does not fit the can or the selector wiring. No live listing exists.
  One correction to the earlier search: 'reduced performance above 174 MHz' is NOT a difference. Airspy says the same of the Discovery's second Band-III tuner, and no stack VHF role lives above 174 MHz.
  5.
    - **Name:** AliExpress clones of the Airspy R2 and of the SDRplay RSP1 (sold as 'RSP1A'), about $139 in about 2018
    - **Why:** Copies of trademarked designs, often mislabelled, so not a clean legal or genuine purchase. There is no measurement of the clones themselves; the originals measured 15-20 dB behind the Discovery. The R2 clone would still need a SpyVerter for HF and LF. Not cheaper, and SDRplay API support for clones is not assured.
  6.
    - **Name:** RX-888 MkII (about $170 on AliExpress)
    - **Why:** Not cheaper. It needs USB 3 SuperSpeed for 16-bit direct sampling, which the CH334F H4 port map and the SuperSpeed RFI note (operator note 7) exclude. There is no calibrated MDS, IIP3 or BDR parity data, and an anecdotal QRSS test had it weaker than the Discovery on weak signals. The SDDC driver stack is unverified on noble arm64.
  7.
    - **Name:** Second RTL-SDR Blog V4L in HF/upconverter mode (about $37.95)
    - **Why:** No LF, so DCF77, MSF, TDF, JJY and NAVTEX 490/518 kHz are lost. It is an 8-bit ADC, with far lower IIP3 and BDR and worse sensitivity. It stays only as the noted budget fallback.
  8.
    - **Name:** Third-party eBay.de listing 'For Airspy HF + Discovery ... High Dynamic Range' (167535233505)
    - **Why:** Not on the airspy.com dealer list. It is unclear whether it is a genuine unit, an accessory or a copy, and there are no measurements. Price unknown (403). It could be a counterfeit.
  9.
    - **Name:** Same part from other EU dealers (WiMo EUR 232 incl. VAT; HamShop NL EUR 239, 7 in stock; AstroRadio EUR 214.17 incl. 21 % IVA; Moonraker EUR 231.99; Neven CZK 5,590; FB Radio SEK 2,495)
    - **Why:** Identical part but all dearer than ITEAD DE at $206.52 landed in DE. Fallback only if ITEAD runs out of stock.
  10.
    - **Name:** ITEAD CN-warehouse SKU IM190522001 ($169 + $5.98 standard shipping, no VAT at checkout)
    - **Why:** Not cheaper and slower. The goods are worth about EUR 150.3, above the EUR 150 IOSS/duty-free threshold, so import VAT (at least $33.25 in DE), possible customs duty and a carrier clearance fee are due on delivery. That is at least $208.23, against $206.52 delivered from the DE warehouse with VAT included.
  11.
    - **Name:** SDRplay RSPdx-R2, RSPduo, Perseus, ELAD FDM-S2/S3, ColibriNANO, AFEDRI, LimeFEA HF
    - **Why:** More expensive than $169 where a price is known (RSPdx-R2 GBP 188 ex VAT = $250.54; RSPduo GBP 214), measured worse (AFEDRI -15 dB), or lacking the 64-260 MHz role (Perseus). Their prices were not re-checked in this pass because the search budget was used up.
- **Confidence:** high
- **Conditions or tests:** Purchase rule:
  - Watch itead.cc (EU SKU IM190522001EU) and airspy.com and rtl-sdr.com for the Airspy Black Friday 2026 sale. Sales are verified for Black Friday 2025 (25 %, $126.75), summer 2026 (20 %, $135.20, 27 Jun-4 Jul) and Black Friday 2022-2024 (20 %, the last from the earlier search).
  - If a sale is live, buy then. If none is live by about 2 Dec 2026, buy at $169 + VAT. This does not delay the build (the Lime ships 15 Dec).
  - Buy only from ITEAD or an airspy.com/purchase dealer.
  
  On arrival, inside ITEAD's 30-day return window, run the existing bring-up tests from reaudit B:
  - airspyhf_info: record S/N, firmware and rate list, and confirm lsusb shows 03eb:800c.
  - Flash firmware to R5.0.1 if it is older than R4.0.7.
  - Calibrate with airspyhf_calibrate against the GNSS-locked 10 MHz, conducted through at least 40 dB.
  - Measure current with the FNB58 at 768 and 912 ksps.
  - Check ripple on the VBUS LC filter.
  - Run the 60 min H4 soak.
  All of these use conducted sources only.
  
  Used option: only with a verified live listing, landed clearly below the new sale price, and passing the full conducted acceptance list listed under the used candidate. Not recommended.
  
  Search budget: the shared WebSearch budget ran out during this pass, so no further used-market or AliExpress-official-store search was possible. Those two items stay unverified.
- **Stack changes:** No hardware, rail, connector, driver or case change. The same micro-USB B, 03eb:800c, libairspyhf 1.6.8-4build1, CH334F H4, tin shield and G6K selector all stay.
  
  BOM text corrections:
  (1) The $169.00 is ex VAT. ITEAD's DE warehouse charges destination VAT at checkout plus DHL. Landed price is $206.52 for DE and $214.91 for FR; VAT for ES is +$35.49. Use these for any EU incl-VAT total.
  (2) Keep the EU SKU IM190522001EU; the CN SKU is not cheaper after import VAT.
  (3) ITEAD's warranty is 2 years for quality defects plus a 30-day return (shipping not refunded), not 1 year.
  (4) Add a buying-window note: Airspy Black Friday 2026, about 27 Nov to 1 Dec. Possible saving $33.80-42.25 ex VAT; buy at list by about 2 Dec if there is no sale.
  (5) Clarification: Airspy states that the Discovery's own 174-260 MHz Band-III tuner has reduced performance. Every stack VHF role (AIS 162, airband, VOR, LRPT 137, ISS 145.8, FM-RDS) is below 174 MHz, so no change is needed.
  
  The HF+ current draw is still unmeasured; keep the 0.3 A placeholder until the FNB58 test.
- **Sources:**
  - https://itead.cc/wp-json/wc/store/v1/products?slug=airspy-hf-discovery-eu
  - https://itead.cc/wp-json/wc/store/v1/products?search=airspy&per_page=50
  - https://itead.cc/wp-json/wc/store/v1/cart (guest cart totals for DE/FR/ES, 18 Oct 2026; nothing ordered)
  - https://itead.cc/product/airspy-hf-discovery-eu/
  - https://airspy.com/airspy-hf-discovery/
  - https://airspy.com/airspy-hf-plus/
  - https://airspy.com/purchase/
  - https://sdrplay.com/wp-content/uploads/2026/06/RSP1B_Datasheet.pdf
  - https://www.rtl-sdr.com/leif-continues-his-comparisons-of-the-airspy-hf-discovery-rsp1-perseus-and-more-sdrs/
  - https://www.rtl-sdr.com/airspy-2026-summer-sale-20-off-all-airspy-products/
  - https://www.rtl-sdr.com/an-overview-of-2025-sdr-black-friday-deals/
  - https://www.wimo.com/es/airspy-discovery
  - https://hamshop.nl/product/airspy-discovery/
  - https://www.rtl-sdr.com/store/
  - https://www.ebay.de/itm/256976414445 (HTTP 403, unverified)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_B_receivers_rf.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md

