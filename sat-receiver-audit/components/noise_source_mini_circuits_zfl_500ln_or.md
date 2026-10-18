# Noise source mini circuits zfl 500ln or: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** Noise source: Mini-Circuits ZFL-500LN+ (or ZFL-500+) in a DIY N8DMT-type source with a box (bench, Lab instruments, qty 1). It is BENCH-only, fed from AUX12 through NOISE EN, with a permanent 10 dB output pad.
- **Current pick:** Mini-Circuits ZFL-500LN+ (SMA, case Y460), new from Mini-Circuits direct, plus a box
- **Current price usd:** 116.81 for the amplifier (Mini-Circuits store, qty 1-4, more than 100 in stock, re-verified 18 Oct 2026). Line total with the $5-10 box: 121.81-126.81, ex VAT. Incl. 21% import VAT: about 141.34 for the amplifier (my calculation; VAT rate depends on the country). The stack line 104.55-126.81 spans both SKUs.
- **Decision:** replace_conditionally
- **Chosen:** Mini-Circuits ZFL-500+ (SMA, case Y460, rev F datasheet), new, bought only from Mini-Circuits direct, in the same order as the stack's other Mini-Circuits items (shopping order step 8). This applies only if the pre-purchase data condition below is met. Otherwise keep the ZFL-500LN+.
- **Chosen price usd:** 99.55 (Mini-Circuits store, qty 1-4, more than 100 in stock, EAR99, re-verified 18 Oct 2026). Line total with the $5-10 box: 104.55-109.55, ex VAT. Incl. 21% VAT: about 120.46 for the amplifier. DigiKey AT is dearer: EUR 107.80 ex / EUR 129.36 incl. VAT, out of stock (angle A figure, not re-checked).
- **Saving usd:** 17.26 ex VAT (about 20.88 incl. 21% VAT). Shipping is shared with the other Mini-Circuits items, so it adds nothing extra. The box cost is unchanged. Against the low end of the stack's range ($104.55) the saving is 0, because that low end already assumes the ZFL-500+.
- **Equivalence proof:** Data I checked myself: ZFL-500+ rev F datasheet; ZFL-500LN+ rev F datasheet; both S2P zips (parsed at the stack's frequencies); PCN16-075; the Mini-Circuits store pages; Mini-Circuits Standard Terms.
  
  Where the ZFL-500+ is equal or better (0.05-500 MHz, typical data):
  - Range: 0.05-500 MHz vs 0.1-500 MHz (better).
  - Gain at 12 V: 24.12-24.28 dB vs 24.30-24.88 dB (LN+ datasheet) or 26.2-26.8 dB (LN+ S2P).
  - NF at 15 V: 4.04-4.31 dB vs 2.89-3.04 dB. In a noise source, higher NF raises the output noise, so this is not a loss.
  - ENR model (G + NF - 10 dB pad): 18.2-18.5 dB vs 17.4-17.9 dB (LN+ datasheet) or 19.2-19.8 dB (LN+ S2P). It sits inside the LN+'s own roughly 2 dB unit spread and well above the stack target of at least 15 dB.
  - Supply sensitivity: 0.29 dB/V (24.17 to 25.05 dB from 12 to 15 V) vs 1.22 dB/V (datasheet) or 1.02 dB/V (S2P). About 4x better ENR stability.
  - Typical flatness at 12 V: +/-0.08 dB vs +/-0.29 dB.
  - VSWR: 1.3/1.3 typical vs 1.5/1.6.
  - Input match: S11 -28 to -40 dB vs -10 to -14 dB at 12 V.
  - P1dB +9 vs +5 dBm and IP3 +25 vs +14 dBm (better, though not critical here).
  - Same Y460 case, 38 g, SMA-F, +17 V max, -20 to +71 C.
  
  Where it is WORSE (stated, not hidden):
  1. Guaranteed minimum gain is 20 dB vs 24 dB, and guaranteed maximum flatness is +/-1.0 dB vs +/-0.5 dB. It is only better on typical data.
  2. Maximum current is 80 mA vs 60 mA at 15 V. The LN+ S2P shows 37 mA at 12 V; the ZFL-500+ figure at 12 V is unpublished. It is likely 20-40 mA more (+0.25-0.5 W, my estimate). That is inside the stack's 0.15 A budget and only drawn during bench Y-factor runs.
  3. Reverse isolation S12 is about -38 dB vs -45 dB. This does not matter with a terminated input.
  4. There is no data above 1 GHz. The only ZFL-500+ S2P is a 2008 unit labelled 'ZFL-500_BNC', supply voltage not stated, 0.05-1000 MHz, showing 22.9-23.0 dB at 1 GHz. The LN+ S2P (2 units, 12 V, to 12 GHz) gives:
  
  | Frequency | LN+ S21 at 12 V |
  |---|---|
  | 1090 MHz | 23.6-24.0 dB |
  | 1420 MHz | 20.3-20.7 dB |
  | 1540-1570 MHz | 18.2-18.8 dB |
  | 1700 MHz | 16.4-16.9 dB |
  | 2200-2400 MHz | 17.3-18.1 dB |
  
  So at the stack's L/S Y-factor points the ZFL-500+ is UNPROVEN.
  
  Why the arrival gate alone is not enough: Mini-Circuits' 30-day money-back covers only portable test equipment explicitly marked on the order, not components. The 12-month warranty covers only the datasheet spec (0.05-500 MHz, gain of at least 20 dB). A unit that is weak at L/S band, or at 21 dB in band, conforms to its spec and cannot be refunded. Break-even: if the unit fails, the user has also to buy the LN+ and loses $99.55, against a $17.26 gain if it passes. The swap therefore only pays if the failure risk is under about 15%. So the swap is gated on data BEFORE purchase.
  
  Net: it replaces the LN+ only if the conditions are met. Otherwise keep the LN+, which is the only option with measured S21 at every stack working point.
- **Rejected:**
  1.
    - **Name:** Used Mini-Circuits ZFL-500LN (non-plus), Surplus Sales, USA, $75
    - **Why:** Price verified: $75, InStock, ships worldwide. Electrically identical to the LN+ on paper (the 2009 rev D datasheet covers both). It fails on assurance and reliability:
  - condition not stated, no warranty on the page;
  - returns only by prior authorization, some electronics not returnable, at most 15 days, 20% restock fee (minimum $7);
  - non-RoHS pre-'+' revision, unknown history (ESD or overdrive would shift ENR over time, which an arrival test cannot rule out).
  Separate US shipment by USPS International, rate not published, plus its own import VAT and carrier handling fee. I estimate this eats most or all of the $41.81 ex-VAT saving. The earlier 'NOT an authorized distributor' quote could not be re-checked: old site HTTP 520, and the FAQ is silent on it.
  2.
    - **Name:** Used Mini-Circuits ZFL-500/ZFL-500+ from eBay or hamfests (~$20, N8DMT's purchase; stack budget line $20-40)
    - **Why:** Price unverified (eBay HTTP 403 for both earlier searches). Revision, history and connector are unknown; no warranty.
  PCN16-075 says the rev B typical table (21 dB at 12 V, NF 5.7) was only a stale datasheet, 'no change to fit, form, function'. So the claim that the old revision has about 1 dB less ENR is itself uncertain.
  It cannot be shown not-worse. Keep it in the stack only as an explicit, user-accepted budget trade.
  3.
    - **Name:** Mini-Circuits ZFL-500 NOS, RF Parts, $89.91
    - **Why:** Listing verified: 'New Old stock, No longer available for export'. Connector not listed; no warranty or return text. An EU buyer would need a US forwarder, which costs more than the $9.64 gap to a new ZFL-500+ (my estimate). Same out-of-band unknowns as the ZFL-500+.
  4.
    - **Name:** Mini-Circuits ZX60-V63+, $92.90 (11 in stock, more 4 Nov 2026)
    - **Why:** Datasheet verified: 0.05-6 GHz, gain 21.9 dB at 50 MHz, NF 3.6-3.8 dB, 5.0 V +/-0.2 V, 69 mA typical / 78 mA max, 5.7 V absolute max.
  - No coverage at 28 MHz or HF.
  - Padded ENR model about 15.5 dB at 50 MHz, 2-4 dB below the LN+ under 1 GHz.
  - Needs a 5 V regulator in the box; more current; thin stock.
  It is better only at L/S band, so this is a trade, not not-worse.
  5.
    - **Name:** RF Bay (Ironwave) LNA-2500
    - **Why:** Neither price nor specifications can be verified: everythingRF HTTP 403, rfbayinc.com timed out, ironwavetech.com HTTP 403. The snippet specs (0.1-2500 MHz, 25 dB, 12 V / 17 mA) are unconfirmed, and eBay '0.1-2500MHz 25dB' modules are clones.
  6.
    - **Name:** Nooelec LaNA (100812), $37.95
    - **Why:** Product page verified: no gain, NF or S-parameter numbers at all, so ENR cannot be modelled. Low end is 20 MHz (HF lost); 3.3-5.5 V supply, 50-80 mA.
  7.
    - **Name:** Generic Chinese 'noise source / tracking source' modules, about $16-26
    - **Why:** No ENR, flatness, match or spur data, only anecdotes; price unverified (listing pages 403). Some near-identical listings are sold as 'interference generators', which conflicts with the conducted-only rule.
  8.
    - **Name:** changpuak.ch DIY 2x GVA/GALI noise source
    - **Why:** Not cheaper (about 99 CHF BOM per the author). Draws about 200 mA (over the 0.15 A budget). No data below 500 MHz (137/435 MHz points unproven). Self-assembled build quality.
  9.
    - **Name:** Used Mini-Circuits ZJL-6G, Surplus Sales, $59
    - **Why:** 13 dB gain per the listing, so the padded ENR model is about 10 dB below the LN+ at VHF/UHF. No ENR measurement. Not re-verified by me.
  10.
    - **Name:** Other Mini-Circuits SKUs (prices re-verified 18 Oct 2026)
    - **Why:** None is cheaper than the LN+:
  - ZFL-500HLN+ $140.72
  - ZFL-500-BNC+ $156.35 (0 in stock)
  - ZFL-1000+ $116.81 (same price as the LN+)
  - ZFL-1000LN+ $131.43
  - ZKL-2R5+ $246.98
- **Conditions or tests:** A. PRE-PURCHASE (before shopping step 8; this is the real gate).
  Email Mini-Circuits sales or applications for S-parameters of current-production SMA ZFL-500+ units at 12 V up to at least 2.5 GHz, like those published for the LN+. Accept only if every unit supplied meets S21 of at least LN+ worst-unit S2P minus 1.0 dB. The 1 dB allowance offsets its roughly 1.2 dB higher in-band NF in ENR = G + NF.
  
  | Working point | Minimum S21 at 12 V |
  |---|---|
  | 1090 MHz | 22.6 dB |
  | 1300 MHz | 20.7 dB |
  | 1420 MHz | 19.3 dB |
  | 1541-1575 MHz | 17.2 dB |
  | 1691-1704 MHz | 15.4 dB |
  | 2200-2290 MHz | 16.4 dB |
  | 2400 MHz | 16.3 dB |
  
  Also require no resonance: no deviation of more than 1 dB from a smooth fit within +/-100 MHz of any working point.
  If the data are not supplied, or any point fails, buy the ZFL-500LN+ as planned.
  
  B. ON ARRIVAL. Same procedure as the stack's ENR table, plus pass/fail limits:
  1. LiteVNA S21 at 12.00 V with a total pad of at least gain + 3 dB: at least 23.7 dB, and flatness +/-0.5 dB or better, over 28-500 MHz. This holds the unit to the LN+'s guarantees, because the ZFL-500+ itself guarantees only 20 dB minimum and +/-1.0 dB.
  2. DC current at 12.00 V of 75 mA or less, so the PTC/TPS2553 rule of 1.5-2x measured stays within 0.15 A.
  3. tinySA ENR with the 10 dB pad (EXT GAIN 0, attenuation at least 10 dB): at least 17.2 dB at 28-440 MHz, at least 16 dB at 1090-1296 MHz, at least 10 dB at 1420-1704 MHz, at least 8.4 dB at 2200-2400 MHz.
  4. Slope between 11.5 and 12.5 V of 0.5 dB/V or less.
  5. Spur-free scan from 0.1 to 2400 MHz with the input terminated.
  6. ENR drift of 0.1 dB or less between 10 s and 120 s after NOISE EN.
  
  An in-band failure (gain below spec) goes to a warranty RMA. An out-of-band failure has no refund path, which is why condition A comes first.
- **Stack changes:** - Line becomes: 'Mini-Circuits ZFL-500+ (conditional on pre-purchase S2P data; else ZFL-500LN+) + box'. Price 104.55-109.55 if the condition passes, else 121.81-126.81.
  - Rails, NOISE EN P-FET switching, Y460 case, SMA-F connectors, box, pads and Pelican fit: no change.
  - Current: expect more than the LN+'s 37 mA at 12 V. Keep the 0.15 A preliminary budget, record the measured current in parts.yaml, and set the PTC/TPS2553 from it.
  - The 12.00 V +/-0.05 V regulation stays. With the ZFL-500+ the ENR error from supply ripple drops from about +/-0.06 dB to about +/-0.015 dB.
  - ENR sanity model in the stack: ZFL-500+ about 18.2-18.5 dB padded in band. For the LN+, correct '17-18 dB' to 17.4-19.8 dB, because the LN+ S2P at 12 V shows 26.2-26.8 dB gain against the datasheet's 24.3-24.9 dB.
  - N8DMT's numbers stay a sanity reference only.
  - Input termination for both SKUs: use a 50 Ohm load (ANNE-50+, SMA-M, fits directly), not an open-ended 5 dB pad. An open pad gives only a 10 dB-return-loss source and makes ENR depend on the amplifier's unknown noise parameters. Either dedicate one of the 3 ANNE-50+ or add a 4th ($14.84).
  - Relabel the 'Budget: used ZFL-500 $20-40' note as an unverified, explicit trade (no warranty, revision unknown), not an equivalent.
  - No Ubuntu or driver impact; it is only a GPIO-switched supply.
  - Rules unchanged: conducted-only, BENCH-only, no antenna connection. Total output is about -60 dBm over 2.4 GHz, far below the -40 dBm limit into receive chains.
- **Confidence:** medium
- **Sources:**
  - https://www.minicircuits.com/pdfs/ZFL-500+.pdf
  - https://www.minicircuits.com/pdfs/ZFL-500LN+.pdf
  - https://www.minicircuits.com/pages/s-params/ZFL-500+_S2P.zip
  - https://www.minicircuits.com/pages/s-params/ZFL-500LN+_S2P.zip
  - https://www.minicircuits.com/pcn/PCN16-075.pdf
  - https://www.minicircuits.com/WebStore/dashboard.html?model=ZFL-500%2B
  - https://www.minicircuits.com/WebStore/dashboard.html?model=ZFL-500LN%2B
  - https://www.minicircuits.com/WebStore/dashboard.html?model=ZX60-V63%2B
  - https://www.minicircuits.com/WebStore/dashboard.html?model=ZFL-500HLN%2B
  - https://www.minicircuits.com/WebStore/dashboard.html?model=ZFL-1000%2B
  - https://www.minicircuits.com/WebStore/dashboard.html?model=ZFL-1000LN%2B
  - https://www.minicircuits.com/WebStore/dashboard.html?model=ZKL-2R5%2B
  - https://www.minicircuits.com/WebStore/dashboard.html?model=ZFL-500-BNC%2B
  - https://www.minicircuits.com/terms/viewterm.html
  - https://www.minicircuits.com/pdfs/ZX60-V63+.pdf
  - https://hallaweb.jlab.org/tech/Detectors/public_html/manuals/data_sheets-manuals/M-N/M/mini-circuits/ZFL-500.pdf
  - https://web.ece.ucsb.edu/~long/ece145b/ZFL-500LN.pdf
  - https://qsl.net/n8dmt/test-page/diy-test-equipment/low-cost-diy-noise-source/index.html
  - https://www.surplussales.com/items/105916/low-noise-amplifier/
  - https://www.surplussales.com/faq/
  - https://www.rfparts.com/zfl-500.html
  - https://www.nooelec.com/store/lana.html
  - https://www.everythingrf.com/products/microwave-rf-amplifiers/rf-bay/567-791-lna-2500 (HTTP 403, unverified)
  - https://www.digikey.at/en/products/detail/mini-circuits/ZFL-500/21727830 (angle A figure, not re-checked)

