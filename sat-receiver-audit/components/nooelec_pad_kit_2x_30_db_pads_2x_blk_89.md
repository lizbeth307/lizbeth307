# Nooelec pad kit 2x 30 db pads 2x blk 89: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** RF accessory set (bench): Nooelec 100815 SMA attenuator kit + 2x 30 dB pads + 2x Mini-Circuits BLK-89-S+ DC block + 3x ANNE-50+ 50 Ohm load + 3x 086-6SM+ Hand-Flex 6 in (one cut into open-ended E-field stubs)
- **Current pick:** Nooelec 100815 kit (1/2/3/6/10/20 dB) + 2x Mini-Circuits VAT-30W2+ (the 30 dB pad that reaudit_D prefers; it overrides STACK v1's Passion Radio pad) + 2x BLK-89-S+ + 3x ANNE-50+ + 3x 086-6SM+
- **Current price usd:** 245.86 (corrected; STACK v1's 212.68 is wrong). 47.95 + 2x31.43 + 2x20.26 + 3x14.84 + 3x16.67, at Nooelec and Mini-Circuits direct, checked live 18 Oct 2026, before shipping, EU import VAT, duty and the EUR 2 per tariff line UHF. The v1 figure priced the -3 dB variant of the Passion Radio listing (EUR 13.20). The -30 dB variant is EUR 18.20 incl. VAT ($20.46) and is on backorder (qty -6), which gives a 223.92 line with no accuracy spec.
- **Decision:** keep
- **Chosen:** Keep the full current set: Nooelec 100815 + 2x VAT-30W2+ + 2x BLK-89-S+ + 3x ANNE-50+ + 3x 086-6SM+. Buy from Mini-Circuits direct or an authorised EU distributor (DigiKey DE / Mouser EU), and the kit from Nooelec direct. No candidate survived adversarial verification as not-worse.
- **Chosen price usd:** 245.86 (same as current, pre-shipping and pre-EU VAT)
- **Saving usd:** 0.00 against the corrected line. Against STACK v1 the line rises by +33.18; that is a price correction, not an analog effect.
- **Equivalence proof:** The current set meets every spec that matters. I checked each value against the datasheets myself (local PDFs Rev D/H/E/G/B) and confirmed the store pages live.
  - VAT-30W2+: DC-6 GHz, 30 +/-0.3 dB nominal, flatness 0.70 dB DC-3 GHz and 1.30 dB DC-6 GHz (flatness = p-p/2), 0.3 dB max drift over temperature, VSWR 1.35 max DC-3 GHz and 1.70 max 3-5 GHz, 2 W, -45 to +100 C, unibody, $31.43, more than 1,000 in stock.
  - Nooelec 100815: DC-6 GHz, 2 W, +/-0.1 dB DC-3 GHz, +/-0.4 dB DC-6 GHz, VSWR below 1.2 max, $47.95, 2-year warranty.
  - BLK-89-S+: 0.1-8000 MHz, IL 0.09/0.3/0.8/0.9 dB max, RL at least 20/25/18/13 dB, 50 V DC, 4 W.
  - ANNE-50+: DC-18 GHz, RL at least 30 dB DC-4 GHz and 27 dB 4-8 GHz, 1 W.
  - 086-6SM+: silver-plated CCS centre (holds its shape for the stubs), tin-soaked braid, PTFE, passivated SS nut, IL 0.30 dB max DC-2 GHz, RL at least 23 dB DC-6 GHz.
  The cheaper candidates are each either measurably worse in a guaranteed spec or cannot be shown not-worse.
  - ANNE-50L+: RL 26/21 dB min (datasheet Rev E), against 30/27.
  - Second Nooelec kit as 20+10 composites: loses the simultaneous 10/20 dB steps, adds interfaces, and makes the 80 dB GPSDO chain 9 bodies long.
  - Generic 30 dB pads (AliExpress, Passion Radio): no guaranteed tolerance, VSWR, power, temperature or connector spec. The only independent data is one user's S11 trace (SWR at most about 1.12 to 4 GHz, about 1.25 at 6 GHz). I inspected the EEVblog image: it shows no independent S21, and the flat S21 plot is the seller's. The listing could not be verified live: the global ID 1005005879252327 now redirects to a different US item, 3256805692937575, then hits a login wall, and the $3 price dates from Dec 2023.
  - Generic loads (RL claim at most 20.8 dB) and Amphenol 132360 (VSWR 1.30 per an aggregator): worse match.
  - Generic DC blocks: 1 dB IL claimed, low corner and DC rating unspecified; a failure would put 13-18 V LNB DC into the tinySA (+/-5 V max).
  - Crystek CBLK-300-3: 3 GHz top end and 16 V rating.
  - Surplus SAT-30: DC-1 GHz only.
  - Used Weinschel and used BLK-89: dearer.
  So nothing cheaper is not-worse, and the current part stays.
- **Rejected:**
  1.
    - **Name:** Mini-Circuits ANNE-50L+ ($9.41, >1,000 stock) for 2 or 3 of the ANNE-50+
    - **Why:** WORSE in the defining spec of a termination: guaranteed RL is 26 dB DC-4 GHz and 21 dB 4-8 GHz, against 30 and 27 dB (ANNE-50L+ datasheet Rev E). Typical RL is 30.8 dB at 4 GHz and 27.2 dB at 6 GHz, so many units would not even reach ANNE-50+ minimums. Derating is 325 vs 350 mW. A LiteVNA using its bundled cal-kit load cannot certify 30 dB RL reliably, so no bench test can rescue it. Offer only as an explicit user trade: 2x ANNE-50L+ as labelled parking/A-B loads plus 1x ANNE-50+ as the VNA load, saving $10.86.
  2.
    - **Name:** Second Nooelec 100815 kit as 2x (20+10 dB) composite 30 dB pads ($47.95 vs $62.86, saves $14.91)
    - **Why:** Functionally worse. On paper the RF is fine: about +/-0.27 dB to 3 GHz including mismatch ripple, and input VSWR at most 1.2. But each kit holds only one 10 and one 20 dB, so both kits' 10/20 dB pads are used up, and no 1-20 dB steps remain alongside two 30 dB pads, which breaks the 'two 30 dB pads plus the kit at the same time' requirement. The 80 dB GPSDO chain becomes 9 bodies (more interfaces, mechanical strain, wear). Nooelec publishes neither a temperature range nor the body material, whereas VAT-30W2+ is rated -45 to +100 C with drift at most 0.3 dB.
  3.
    - **Name:** Generic unbranded 30 dB SMA pad, AliExpress 3256805879252327 / 1005005879252327 (EEVblog Randy222, Dec 2023), about $3 then
    - **Why:** Not proven not-worse, and price and availability are not real-verified. Independent evidence is one unit's S11 only (I inspected the image: SWR about 1.0-1.12 to 4 GHz, about 1.25 at 6 GHz). There is no independent S21, so the -30.03 dB flat plot is seller marketing. Power rating, temperature rating and drift, body material and SMA pin depth are all unpublished; a bad pin depth can damage the LiteVNA and tinySA ports, and the stack has no pin-depth gauge. EEVblog posters (nctnico, fourfathom) report cheap pads missing their power ratings. Live check 18 Oct 2026: the global ID 302-redirects to a DIFFERENT US item (3256805692937575), then a login wall, so the measured listing's identity and current price cannot be confirmed. Up to about $50 saving, but only as an explicit trade, not an analog.
  4.
    - **Name:** Passion Radio 'RF KONNECT' -30 dB pad (ADAPT-SMA-ATTENUA30-8263), EUR 18.20 incl. VAT = $20.46
    - **Why:** No attenuation tolerance, flatness or VSWR published; only 0-6 GHz, 2 W, gold-plated brass and -55 to +125 C (from the saved page, 18 Oct 2026). Backorder qty -6. Cannot be shown not-worse than VAT-30W2+'s guaranteed figures, and brass is less wear-resistant than unibody. This is also why STACK v1's pick must not be reinstated.
  5.
    - **Name:** Generic AliExpress 2 W DC-6 GHz pad set as Nooelec kit replacement (items 4000412303682, 3256801757708013)
    - **Why:** Independent data covers only one 10 dB pad, within about 0.4 dB to 6 GHz; +/-0.1 dB DC-3 GHz is not shown and the other values are unmeasured. Power is unverified, and EEVblog reports are mixed ('acceptable up to 1 GHz'). Prices and listings are unverified (AliExpress blocked).
  6.
    - **Name:** DIY 10+20 dB cascade from the existing kit
    - **Why:** Removes an independent 30 dB pad and ties up the kit's 10/20 dB pieces, so simultaneous attenuation steps are lost; adds one interface.
  7.
    - **Name:** Amphenol RF 132360 SMA-M termination ($4.79)
    - **Why:** The only VSWR figure found is 1.30 (about 17.7 dB RL, everythingrf), against ANNE-50+'s guaranteed RL of at least 30 dB DC-4 GHz. Amphenol and RS pages returned 403, so this is unverified at source, but it would need VSWR at most 1.065 to match. Brass body. Worse or unproven.
  8.
    - **Name:** Tyclon SMA50-SP-1W ($8.81, DigiKey Marketplace)
    - **Why:** No VSWR or RL published; marketplace shipping and VAT. Cannot be shown not-worse.
  9.
    - **Name:** Generic 2 W DC-6 GHz loads (sdrstore.eu, Hilitand, Passion Radio 81T414 / 1 W 6 GHz)
    - **Why:** Claimed SWR at most 1.20 (RL about 20.8 dB) or no RL spec at all; about 9 dB worse match than ANNE-50+ by claim, with no independent measurements.
  10.
    - **Name:** Generic AliExpress/Amazon SMA DC block ('DC-6 GHz, SWR 1.2, IL 1 dB')
    - **Why:** Claimed IL 1 dB against 0.10-0.15 dB typical; low cutoff and DC voltage rating unspecified. This is a safety-critical part, because a failure puts 13-18 V LNB or 28 V boost-rail DC into the tinySA (+/-5 V max) or an SDR. No independent data.
  11.
    - **Name:** DIY DC block (series C0G cap between SMA edge connectors)
    - **Why:** Reaching 0.1 MHz needs large capacitance, whose SRF falls into the GHz range; no measured design; voltage and enclosure unknown.
  12.
    - **Name:** Crystek CBLK-300-3
    - **Why:** 300 kHz-3 GHz and 16 V DC, against 0.1 MHz-8 GHz and 50 V. Fails the 6 GHz bench band, the 18 V LNB and the 28 V rail. Not reliably cheaper (about $20-27, unverified).
  13.
    - **Name:** Crystek CATTEN series
    - **Why:** DC-3 GHz, at most 1 W, VSWR 1.30; a 30 dB value is not confirmed to exist. Worse.
  14.
    - **Name:** Mini-Circuits VAT-30+ (cheaper 1 W sibling)
    - **Why:** Verified live: 'This is a non-catalog model' (no price or stock); 1 W is also worse than 2 W.
  15.
    - **Name:** Surplus Mini-Circuits SAT-30 ($13)
    - **Why:** DC-1000 MHz only; does not cover the LNB IF top end, L-band or S-band.
  16.
    - **Name:** Used Weinschel 41-30-12 (EUR 125) / used BLK-89 eBay ($24.99, untested)
    - **Why:** Not cheaper than new; the BLK-89 is untested and its variant unconfirmed.
  17.
    - **Name:** Generic RG405 SMA M-M jumpers (AliExpress/eBay)
    - **Why:** No assembly-level IL/RL data and no confirmation of tin-soaked braid or CCS centre conductor. Shield leakage at a poor crimp would spoil the E-field stub's localization. Prices not verified.
  18.
    - **Name:** Unnamed AliExpress cal-kit male load (M. Hellmich measurement)
    - **Why:** Measured excellent, but the seller and model are unidentified so it cannot be re-bought with certainty; about EUR 40 for one male load, so not cheaper for 3 loads.
- **Confidence:** high
- **Conditions or tests:** No replacement, so no acceptance gate is attached to a swap. These checks apply to the kept parts, from the existing stack plus items found here.
  (1) Characterise every pad on the LiteVNA, up to 6.0 GHz only, since VAT-30W2+ and the Nooelec kit are rated only to 6 GHz, not 6.3. Store S21 per pad per frequency. VAT-30W2+ typical attenuation is 29.72 dB at 1 GHz, 28.80 dB at 3 GHz and 27.69 dB at 6 GHz, so labd's '30 dB pad keeps tinySA sources at or below -40 dBm into paths' check must use the measured S21, not the nominal 30 dB: above about 1 GHz, add the 3 dB kit pad or lower the source by the measured shortfall. Above 3 GHz the HW 3.1 LiteVNA has only about 50 dB dynamic range, so average when measuring the 30 dB pads there.
  (2) BLK-89-S+ is specified only down to 0.1 MHz, and the HF+ LF time-signal use is 40-77.5 kHz. Measure S21 from 50 kHz on the LiteVNA, and A/B the DCF77/MSF SNR on the HF+ with and without the block. If it is lossy, run the HF+ LF path without a block once 0 V DC on that port is confirmed.
  (3) Label the 3 ANNE-50+ and never put one on a biased line: DC block first (13.2 V would dissipate about 3.5 W into a 1 W load).
  (4) Buy only from Mini-Circuits direct, DigiKey or Mouser (authorised), and Nooelec direct; no 'Mini-Circuits' parts from marketplace sellers.
  (5) EU landed cost (rules from operator note 35), not verified here. Mini-Circuits ships from the US: 4 tariff lines, about $198, which is above EUR 150, so normal duty plus import VAT plus courier fee plus the EUR 2/line UHF from about 1 Nov 2026. DigiKey DE (angle A data, not re-checked) quotes VAT-inclusive EUR prices but had BLK/ANNE/086 at 0 stock until 27 Oct / 27 Nov. Compare both landed totals at order time.
  (6) Optional explicit user trades, not adopted because each gives up a spec:
  - 2x ANNE-50L+ as parking loads: -$10.86, RL 26/21 vs 30/27 dB.
  - Generic 30 dB pads: up to about -$50, with unknown build, power and temperature ratings. Only with per-unit LiteVNA acceptance (S21 within VAT-30W2+ limits, VSWR at most 1.35 to 3 GHz), a 9-10 V DC soak at about 1.6-2 W for 30 min followed by a re-measure, and first mating on a sacrificial adapter, never directly on instrument ports.
- **Stack changes:** - STACK v2 line 'RF accessories': price 245.86 (not 212.68), with VAT-30W2+ named as the 30 dB pad. It is not the 'budget alternative': it is the specified, in-stock baseline. Passion Radio -30 dB pads are dropped (no spec, backorder).
  - Core total: +$33.18 against v1, as in reaudit_D.
  - No changes to power rails, connectors, drivers (all passive), case or Pelican layout.
  - Calibration and labd: the pad S21 table is stored per pad per frequency up to 6.0 GHz. The source-level guard uses measured attenuation (VAT-30W2+ is about 28.8 dB at 3 GHz typical), not 30 dB.
  - Bring-up: add a BLK-89-S+ check below 100 kHz for the HF+ LF/time-signal path.
  - Data correction for v2 text: BLK-89-S+ minimum RL is 20 dB at 0.1-100 MHz and 25 dB at 100-1000 MHz (angle A's '25 dB from 0.1 MHz' is wrong); ANNE-50L+ minimum RL is 26/21/18 dB.
  - Sourcing: prefer authorised EU stock when the landed total is close, under operator notes 34-35.
- **Sources:**
  - https://www.minicircuits.com/WebStore/dashboard.html?model=VAT-30W2%2B (fetched 18 Oct 2026: $31.43 qty 1, >1,000 stock, no EOL)
  - https://www.minicircuits.com/WebStore/dashboard.html?model=ANNE-50L%2B (fetched: $9.41, >1,000 stock)
  - https://www.minicircuits.com/WebStore/dashboard.html?model=VAT-30%2B (fetched: 'This is a non-catalog model')
  - https://www.minicircuits.com/pdfs/VAT-30W2+.pdf (Rev D, local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/padsB_dl/c_VAT-30W2+.pdf)
  - https://www.minicircuits.com/pdfs/ANNE-50+.pdf (Rev H, local /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/padsB_dl/anne50.pdf)
  - https://www.minicircuits.com/pdfs/ANNE-50L+.pdf (Rev E, local /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/padkit_dl/ANNE-50L.pdf)
  - https://www.minicircuits.com/pdfs/BLK-89-S+.pdf (Rev G, local /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/padsB_dl/c_BLK-89-S+.pdf)
  - https://www.minicircuits.com/pdfs/086-6SM+.pdf (Rev B, local /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/padsB_dl/c_086-6SM+.pdf)
  - https://www.nooelec.com/store/sdr/sdr-addons/attenuators/attenuator-bundle.html (fetched: SKU 100815 $47.95, +/-0.1 dB DC-3 GHz, +/-0.4 dB DC-6 GHz, VSWR <1.2 max, 2 W, 2-yr warranty)
  - https://www.passion-radio.com/sma/sma-attenuator-826.html (live fetch failed with a redirect loop; saved page of 18 Oct 2026 shows -30 dB variant +4.166667 ex VAT, qty -6, no VSWR/tolerance)
  - https://www.eevblog.com/forum/rf-microwave/sma-attenuators-(value-find)/ (local copy and both images inspected: independent S11 only; S21 plot is seller-supplied)
  - https://www.eevblog.com/forum/beginners/beginner-attenuators-set-3db-6db-10db-20db/
  - https://www.aliexpress.com/item/1005005879252327.html (live: 302 to a different item, aliexpress.us/item/3256805692937575, then login wall; unverified)
  - https://www.digikey.com/en/products/detail/amphenol-rf/132360/1011928 (from angle A; Amphenol and RS pages returned 403 to me)
  - https://everythingrf.com/products/rf-terminations/amphenol-rf/694-267-132360
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json (price correction for the 30 dB pads)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (items 34-35, EU landed-cost rules)
  - Note: the shared WebSearch budget was exhausted on the first search call, so verification used WebFetch on primary pages plus the datasheets and forum copies already saved in the scratchpad.

