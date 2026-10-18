# Nooelec flamingo fm v2 100813: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e32114dd-52d`_

- **Part:** FM broadcast band-stop filter. It is the first part after the antenna on P1 VHF-137 (Flamingo+ -> SAWbird+ NOAA), and an optional second unit (#2) sits on P8 WIDE/2 m before the LNA V2.
- **Current pick:** Nooelec Flamingo+ FM v2, SKU 100813, bought from Nooelec direct inside the existing >$100 Nooelec order (free shipping)
- **Current price usd:** 24.95 ex-VAT. Re-verified on nooelec.com on 18 Oct 2026, page shows Add to Cart and 1-day dispatch. EU landed price is about $29.7-30.2 with 19-21% import VAT. Because the Nooelec order is about $199.75, which is over EUR 150, IOSS does not apply: VAT, any duty (rate not verified) and a courier handling fee are collected on import.
- **Decision:** keep
- **Chosen:** Keep the Nooelec Flamingo+ FM v2 (100813), bought from Nooelec direct. The same applies to unit #2 on P8.
- **Chosen price usd:** 24.95
- **Saving usd:** 0 (no not-worse cheaper analog exists)
- **Equivalence proof:** Verdict: KEEP. Every cheaper candidate is worse in at least one spec that matters on P1. Both searches got one thing wrong, and I corrected it from the primary datasheet.
  
  REFERENCE DATA I verified myself
  - Flamingo+ FM datasheet Rev 1 (2019-12-02), fetched from the Passion Radio attachment for SKU 100813:
    - Stop band 80.5-114.8 MHz.
    - S21 min/typ/max is -77.5/-70/-10 dB. The 'max -10' is the band-edge figure.
    - Passband IL 0.01/0.5/1.2 dB.
    - S11 typ -20 dB.
    - Pin max +18 dBm.
  - Nooelec page: '>60dB typical average & >70dB typical maximum'; -3 dB at 75/120 MHz; -10 dB at 80/116 MHz; out-of-band IL <0.25 dB; ESD diode 'meant for RF applications'; anodised aluminium EMI case; 250 mA DC; 2-year warranty.
  - I digitised the datasheet's 50-150 MHz S21 plot, which shows one unit. Reading accuracy is about ±1 dB in the notch and ±0.5 dB in the passband:
    - 87.5 MHz about 46-47 dB; 88 MHz about 50 dB.
    - 90 MHz about 66 dB; 92 MHz about 77 dB; 95-100 MHz about 71-73 dB; 102 MHz about 68 dB.
    - 104 MHz about 54 dB; 106 MHz about 42 dB; 107 MHz about 37 dB; 108 MHz about 32 dB.
    - Mean over 88-108 MHz about 63.6 dB, so the stack's >=60 dB average test passes.
    - 120 MHz about 3.7 dB; 125 MHz about 2 dB; 137 MHz about 0.5-1.1 dB.
  
  CORRECTION TO BOTH SEARCHES AND THE STACK
  The European band edges are NOT 'deep inside the stopband'. At 108 MHz the Flamingo+ gives only about 32 dB, and at 87.5 MHz about 47 dB.
  
  WHY EACH CHEAPER CANDIDATE IS NOT NOT-WORSE
  - RTL-SDR Blog band-stop ($16.95):
    - Its spec is '>50 dB' against Flamingo+ '>60 dB typ avg'.
    - Its mid-band depth is about 50-55 dB (vendor: 'around 50 dB or more'; RadioReference snippet: about 55 dB at 95 MHz, unverified). Flamingo+ gives 70-77 dB at 90-102 MHz, so the RTL filter is about 15-20 dB worse.
    - It has no published ESD diode. The re-audit relies on that diode as P1 protection.
    - It has no maximum-input rating (Flamingo+: +18 dBm).
    - Its 137 MHz loss is not published. The admin says '<4 dB' above about 120 MHz, and the upper -3 dB point is 122 MHz against 120 MHz.
    - It IS better at the 108 MHz edge: vendor 45-50 dB against about 32 dB. That makes it a trade, not a not-worse analog.
  - Flamingo FM v1 ($22.95) and Distill:FM Barebones ($17.95): both >40 dB typical, about 20 dB shallower, with no numeric IL. The Distill also has only a board-level EMI frame, no aluminium case, and no stated warranty (30-day return only).
  - Maker go Tindie ($11.90): copies the RTL-SDR Blog spec text and states no ESD or input rating. Its origin is unverifiable.
  - Generic AliExpress/eBay modules: no S21 sweeps. The only report is 25-30 dB.
  - TV traps: 75 ohm F-type with higher loss.
  - DIY designs: 30-52 dB of rejection, or 137 MHz falls on the filter skirt; no ESD protection.
  - Two cheaper filters in cascade: 2x Distill is $35.90 and 2x RTL is $33.90, so neither is cheaper, and the cascade adds 137 MHz loss.
  
  COMPATIBILITY
  The Flamingo+ is passive, has SMA female connectors, and needs no rail or driver. No change is needed.
- **Rejected:**
  1.
    - **Name:** RTL-SDR Blog Broadcast FM Band-Stop Filter (88-108 MHz), $16.95 at rtl-sdr.com (131 in stock, verified)
    - **Why:** WORSE IN:
  - Average and mid-band rejection. Spec is '>50 dB' against >60 dB typ avg. Vendor post: 'around 50 dB or more', almost 60 dB at 88 MHz, 45-50 dB at 108 MHz. Flamingo+ gives 70-77 dB at 90-102 MHz.
  - No ESD diode, which P1 needs. Fixing that adds a part.
  - No maximum-input rating.
  - 137 MHz insertion loss unpublished (admin: '<4 dB' above about 120 MHz).
  - No stated warranty term.
  
  BETTER IN:
  - 108 MHz edge: 45-50 dB against about 32 dB for the Flamingo+ (datasheet plot). That makes it a spec trade, not not-worse.
  
  AVAILABILITY:
  - The store does not ship to the EU (buy page, verified).
  - The Elektor product URL cited by both searches now 404s and does not appear in Elektor's product search, so that EU route is not real today.
  - Prices at the official AliExpress and eBay stores were not verified. Clones are sold on both marketplaces.
  2.
    - **Name:** Nooelec Flamingo FM v1 (100780), $22.95
    - **Why:** About 20 dB less rejection ('>40dB typical' against >60 dB average), which fails the >=60 dB intake test. No numeric insertion loss. It saves only $2.
  3.
    - **Name:** Nooelec Distill:FM Barebones (100758), $17.95
    - **Why:** About 20 dB less rejection ('>40dB typical'), which fails >=60 dB. Board-level EMI frame only, no anodised aluminium enclosure. No warranty stated (30-day return policy only). No numeric insertion loss. It does keep the ESD diode and the +18 dBm rating.
  4.
    - **Name:** Maker go (adz1122) Tindie 'Broadcast FM Band-Stop Filter', $11.90 + shipping from Shenzhen
    - **Why:** Its spec text copies the RTL-SDR Blog listing (>50 dB, 76/122 MHz, <0.5 dB), so it inherits every RTL-SDR Blog shortfall. No ESD protection, maximum input or enclosure stated. No measurements. The seller has 5 reviews. Unknown origin, so it fails the not-counterfeit rule.
  5.
    - **Name:** Generic AliExpress/eBay 88-108 MHz SMA modules (e.g. NWDZ BS), about EUR 11 (unverified)
    - **Why:** No independent S21 sweep. The only user report is 25-30 dB. 137 MHz loss, ESD protection and build are unknown. Some listings are actually band-pass filters. Counterfeit and consistency risk.
  6.
    - **Name:** Cheap TV FM trap (about $5)
    - **Why:** 75 ohm F-connectors in a 50 ohm SMA chain. rtl-sdr.com's comparison shows much less stopband rejection and much higher passband loss.
  7.
    - **Name:** GPIO Labs FM Notch 88-108 MHz (Tindie), $30.00, 9 in stock (verified)
    - **Why:** Not cheaper. Only 25 dB at 108 MHz. Loss of 0.8 dB at 150 MHz; 137 MHz not given. No ESD protection stated. The 'airband' and enclosed versions are worse or dearer.
  8.
    - **Name:** Mini-Circuits NSBP-108+
    - **Why:** Not cheaper (about $184, from the second search, not re-verified). N-type connectors at 73 g. Rejection >20 dB at 88-108 MHz and about 26 dB at 108 MHz. About 1 dB loss at 140 MHz.
  9.
    - **Name:** Same Flamingo+ FM v2 from Passion Radio (FR), EUR 33.90 incl. VAT, in stock (verified 18 Oct 2026; SKU NOO-100813)
    - **Why:** Not cheaper: about $38.1 incl. VAT, or about EUR 28.25 / $31.8 ex 20% VAT, against $24.95 direct. The only benefit is EU dispatch with VAT already handled.
  10.
    - **Name:** DIY designs (9A4QV SMD trap, adaeuper Legendre, experimental-engineering stripline)
    - **Why:** 30-52 dB rejection, or upper -3 dB at 140-141 MHz, which puts 137 MHz on the skirt. No ESD protection or shielding. Every unit varies and would need a VNA sweep.
  11.
    - **Name:** Used Flamingo+ FM v2
    - **Why:** No listing found, so there is no verifiable price. The warranty probably does not transfer, and the ESD diode history is unknown.
  12.
    - **Name:** Cascade of two cheaper filters (2x Distill $35.90; 2x RTL-SDR Blog $33.90)
    - **Why:** Not cheaper than one Flamingo+, and it doubles the passband loss ahead of the LNA.
- **Confidence:** high
- **Conditions or tests:** No swap, so no swap test. Tighten the existing LiteVNA intake test (conducted only) using datasheet-derived limits:
  1. Mean S21 over 88-108 MHz <= -60 dB. The datasheet plot gives about -63.6 dB.
  2. Point limits: <= -45 dB at 87.5-88 MHz; <= -65 dB at 92-100 MHz; <= -28 dB at 107.9 MHz. The plot gives about 47/50, 71-77 and 32 dB.
  3. |S21| <= 1.2 dB at 137.1 and 137.9 MHz, and <= 1.2 dB at 144-146 MHz for unit #2.
  4. S11 <= -15 dB at 137 MHz. The plot shows about -25 dB.
  
  Site check: with the HF+ on the AIS/FM port, list the strongest FM stations at the operating site. Size the SAWbird+ NOAA and V4L intermod margin using the measured per-station S21, not a flat 60 dB, because a strong station at 104-108 MHz gets only about 32-54 dB. If a band-edge station breaks the margin, the fix is an ADDED filter, which is a new design decision, not a swap.
- **Stack changes:** No changes to rails, connectors, drivers or the case. The part is passive and has SMA connectors. P8 #2 is unchanged.
  
  STACK.md text fixes:
  1. C10 and BOM row 'FM-режектор': drop 'DC-прохід 250 mA' as the selection reason, and drop 'без рейтингу DC' as the reason to reject the RTL-SDR Blog filter. P1 has no DC, and bias enters at the SAWbird+ output. The real reasons are:
     - deeper average and mid-band rejection (about 63.6 dB average, 70-77 dB at 90-102 MHz);
     - an RF ESD diode on the input;
     - a +18 dBm rating;
     - published 0.5/1.2 dB passband insertion loss;
     - a 2-year warranty.
  2. Correct the band-edge claim. The datasheet plot gives about 47 dB at 87.5 MHz, about 50 dB at 88 MHz, about 37 dB at 107 MHz and about 32 dB at 108 MHz. The re-audit's 'band-edge stations deep inside the stopband' and any flat '>60 dB across 87.5-108 MHz' assumption in the intermod budget must be replaced by per-frequency values.
  3. Add the point limits and S11 check above to the bring-up intake test.
  4. The budget-alternative note should read: 'RTL-SDR Blog $16.95 is a spec trade. It is better at 108 MHz but about 15-20 dB shallower mid-band, has no ESD diode and no input rating, and is not sold direct to the EU (Elektor listing gone).'
  5. Sourcing: Nooelec direct stays cheapest. Passion Radio (EUR 33.90 incl. VAT, in stock) is the EU fallback if import handling on the Nooelec order is a problem.
  
  Limits of this check: the web-search budget was exhausted, so I did not run new marketplace searches (Amazon, the official AliExpress and eBay stores). The eBay and RadioReference measurements quoted by the searches remain unverified (HTTP 403 and 503).
- **Sources:**
  - https://www.nooelec.com/store/flamingo-plus-fm.html
  - https://www.passion-radio.com/sdr-accessory/flamingo-v2-2539.html
  - https://www.passion-radio.com/index.php?controller=attachment&id_attachment=1206
  - https://www.nooelec.com/store/flamingo-fm.html
  - https://www.nooelec.com/store/distill-fm-broadcast-fm-filter.html
  - https://www.nooelec.com/store/catalogsearch/result/?q=flamingo
  - https://www.nooelec.com/store/catalogsearch/result/?q=distill
  - https://www.rtl-sdr.com/product/rtl-sdr-blog-broadcast-fm-band-stop-filter/
  - https://www.rtl-sdr.com/rtl-sdr-com-broadcast-fm-band-stop-filter-88-108-mhz-reject-now-for-sale/
  - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
  - https://elektor.com/products/rtl-sdr-broadcast-fm-band-stop-filter-88-108-mhz-reject (now 404, redirects to search)
  - https://www.tindie.com/products/gpio/fm-notch-filter-88-108mhz-sma-m-sma-f/
  - https://www.tindie.com/products/adz1122/broadcast-fm-band-stop-filter-88-108-mhz-fm-trap/
  - https://forums.radioreference.com/threads/fm-bandstop-filter-comparison.394943/ (HTTP 503, unverified)
  - https://www.ebay.de/itm/146949589034 (HTTP 403, unverified)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/flam_ds/ds_en.pdf
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/flam_ds/s21_zoom.png

