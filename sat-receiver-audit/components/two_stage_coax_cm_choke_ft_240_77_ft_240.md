# Two stage coax cm choke ft 240 77 ft 240: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e32114dd-52d`_

- **Part:** Two-stage coax common-mode choke on the HF+ / Boni-Whip coax near P5 (STACK C17): LF/MF stage FT-240-77 (Fair-Rite 5977003801) + HF stage FT-240-31 (Fair-Rite 2631803802), wound with RG316, bracket bonded to the mid-plate. Qty 1, tier core, group HF.
- **Current pick:** Fair-Rite 5977003801 (#77, 61 x 35.55 x 12.7 mm, AL 2950 nH +/-25%, 106 g) + Fair-Rite 2631803802 (#31, 61 x 35.55 x 12.7 mm, 118 g), RG316, SMA at both ends. STACK gives no turn counts. The searchers' model is about 30 turns on #77 (1 kOhm at 60 kHz at nominal AL, 35 turns at -25% AL) and about 13 turns on #31 (about 1.9 kOhm at 1 MHz, N-squared from the Fair-Rite single-turn data).
- **Current price usd:** Cores $20.12 at DigiKey US qty 1, verified today: 5977003801 $10.77 (417 in stock) + 2631803802 $9.35 (15,676 in stock). DigiKey DE: 2631803802 is EUR 8.21 ex VAT / EUR 9.77 incl. VAT (verified); 5977003801 is EUR 9.46 ex VAT (searcher's figure, not re-checked). TME prices are not real at qty 1: no price breaks are shown, stock fields contradict each other, and 5977003801 has 0 stock with MOQ 200. RG316, 2 SMA and the bracket are about $5-10 (estimate). Total about $25-30.
- **Decision:** replace_conditionally
- **Chosen:** Keep the FT-240-77 LF stage (Fair-Rite 5977003801) unchanged. Replace only the FT-240-31 HF stage with one Fair-Rite 2631102002 #31 round cable core (sleeve 25.9 +/-0.75 OD x 12.8 +/-0.25 ID x 28.6 +/-0.8 mm, 55 g, burnished edges). Wind it with 9 turns of RG316, not the searcher's 8; trim to 9-11 turns on the LiteVNA. Wind loosely: the outside return loops keep a bend radius of about 10 mm or more, matching the toroid, and are not pulled tight against the end faces. Pass the turns through in sequence so the input and output leave at opposite ends.
- **Chosen price usd:** Cores $13.71 at DigiKey US qty 1 ($10.77 + $2.94 for 2631102002, 76,935 in stock, Active, verified). DigiKey DE: 2631102002 is EUR 2.58 ex VAT / EUR 3.07 incl. VAT (verified), so the cores are about EUR 12.04 ex VAT.
- **Saving usd:** $6.41 at DigiKey US qty 1 ($9.35 - $2.94). In the EU (DigiKey DE): EUR 5.63 ex VAT, EUR 6.70 incl. 19% VAT. If the bench gate fails, the cost is +$2.94 for the sleeve and the 2631803802 is ordered as before.
- **Equivalence proof:** 1) Same maker, same #31 MnZn material and same burnished, uncoated finish. Fair-Rite's tolerance statement is the same for both parts: controlled for impedance only, minimum is typically the listed value less 20%. So mu vs T, Curie temperature, dimensional-resonance class and aging are those of #31 in both. TME lists both at -55 to +90 C.
  2) Fair-Rite single-turn typical Z, sleeve 2631102002 vs toroid 2631803802 (both page tables): 31-38 vs 10.2-12 ohm at 1 MHz, 79-90 vs 28-32.5 at 5 MHz, 103-110 vs 40-41 at 10 MHz, 156-163 vs 61-63 at 25 MHz. Even pairing the sleeve's low table with the toroid's high table, the sleeve gives 2.43-2.58x per turn squared. The geometric ratio h*ln(OD/ID) is 2.94, which is consistent.
  3) With N-squared scaling, 9 sleeve turns against 13 toroid turns: +49/+34/+26/+23% at 1/5/10/25 MHz (mean tables), and +24/+17/+20/+19% in the worst cross-pairing. The searcher's 8 turns is refuted: it comes out 0% at 10 MHz and -3% at 25 MHz (mean), and -5 to -6% in the worst pairing. So 9 turns is the minimum. Rule: sleeve turns of at least 0.64 x the toroid turns covers any toroid winding up to about 18 turns.
  4) The inductance at the 0.3-3 MHz handover is the same (same material, N-squared-equivalent winding), so the series-resonance hand-off to the unchanged #77 stage is unchanged to first order.
  5) Window: one ring in the 12.55 mm minimum bore holds about 12 RG316 turns (2.5 mm OD, Belden 83284), so 9-11 turns fit.
  6) Differential path: about 0.7-1.0 m of RG316 for 9 turns, against about 0.8 m for 13 turns on the toroid. DC loop resistance (0.30 ohm/m, Belden) and insertion loss at 30 MHz are equal within about 0.1 ohm and 0.03 dB (model). The searcher's 'lower DCR' claim does not hold once the turns are wound loosely, and it was never the reason to switch. Boni-Whip DC passes on the centre conductor and the core carries no bias.
  7) The HF stage gets smaller and lighter: 55 g instead of 118 g, envelope about 30 x 50 x 50 mm with loops instead of a 61 mm OD toroid. The ferrite is genuine Fair-Rite from an authorized distributor.
  NOT PROVEN, so the replacement is conditional: winding capacitance. All 9 turns are bunched in one bore, against 13 turns spread around a 104 mm toroid circumference. Per K9YC, the parasitic C both through the core and between turns sets the upper-HF |Z|, and N-squared figures at 10-30 MHz (6-13 kOhm) are not physical for either part. No independent measurement of RG316 on this sleeve exists. The current pick is also unmeasured.
- **Rejected:**
  1.
    - **Name:** TDK B64290L0659X830 (R40x24x16, N30, epoxy) LF stage + 2631102002 HF stage ($12.44, saves $7.68)
    - **Why:** Verified: AL 7000 nH +/-25%, mu_i 4300, epoxy coated (41.8 max OD, 22.5 min ID, 17.2 max height), 61 g, DigiKey $9.50 with 262 in stock. Not proven not-worse at datasheet level. The N30 material sheet (mu', mu'' vs f at 0.3-1 MHz; mu_i at -20 C; Curie point) could not be retrieved (TDK URLs returned 404/403), so the 518 kHz NAVTEX and cold behaviour is unverified. By Snoek's law a mu_i 4300 ferrite rolls off at roughly half the frequency of mu_i 2000 #77, inside the handover region. Less headroom: at -25% AL it needs about 22.5 turns, and the coated window holds about 25 touching turns; the FT-240-77 needs about 35 against about 40. It also inherits every condition of the sleeve HF stage. Only worth a later bench experiment (sweep 40 kHz-1 MHz at room temperature and cold).
  2.
    - **Name:** 2x Fair-Rite 5978002701 (#78, FT-140 size) stacked LF stage + sleeve ($9.02)
    - **Why:** Not orderable: DigiKey shows 0 in stock, 371 expected 30 Oct 2026, 20-week lead time (verified). Worse in headroom: stacked AL 5090 nH means 1 kOhm at 60 kHz needs about 23 turns nominal and about 26.4 at -25% AL, but the 22.45 mm minimum ID holds only about 25 single-layer turns. A worst-tolerance core therefore misses the C17 target, or needs a second layer (more capacitance, lower SRF across 0.3-3 MHz). The FT-240-77 can reach the target at -25% AL in one layer.
  3.
    - **Name:** 2x Fair-Rite 5977002701 (#77, FT-140 size) stacked LF stage + sleeve ($9.30)
    - **Why:** Not orderable: DigiKey shows 0 in stock, 371 past due (est. 16 Oct 2026), 20-week lead time; TME has 0 stock with MOQ 742 (verified on DigiKey). Same headroom failure: stacked AL 4800 nH needs about 27 turns at -25% AL against about 25 that fit in one layer.
  4.
    - **Name:** 2x Fair-Rite 2631803802 (#31 for both stages, $18.70)
    - **Why:** Saves only $1.42. Fair-Rite does not control AL for #31 ('controlled for impedances only', no AL listed), so the 60 kHz inductance is not guaranteed. At the estimated AL of 2050 nH it needs about 36 turns nominal and about 41.5 at -25%, beyond the about 40-turn single-layer window. More turns also mean more capacitance in the 0.3-1 MHz gap. Worse.
  5.
    - **Name:** Current part from cheaper sellers (TME, RS AT, Arrow, eBay PL1, Alltronics, Amidon/RS PT)
    - **Why:** The prices are not real at qty 1. TME 2631803802 shows only a USD 4.75-8.65 range with no breaks and conflicting stock (0 vs 127). TME 5977003801 has 0 stock, MOQ 200, multiple 200. RS, Arrow and eBay figures are snippets or out of stock. Amidon and Alltronics cost more. DigiKey stays the verified source.
  6.
    - **Name:** Würth WE-TOF 74270191 (4 W 620) as HF or LF stage
    - **Why:** mu_i about 620 against 2000 (#77), so it is far weaker at LF. Würth gives no impedance data at 1-25 MHz. At $7.16 (searcher) it is dearer than the 2631102002 ($2.94) with less data.
  7.
    - **Name:** Palomar F240-31 'FT240-3I' 3-pack ($29.95, about $9.98 each)
    - **Why:** Not cheaper than the genuine 2631803802 ($9.35). The core maker is not named (country of origin China), and there is no AL or Z data, so the material cannot be traced.
  8.
    - **Name:** Unbranded 'FT240-31/77' marketplace cores
    - **Why:** No listing was found with a datasheet. The mix cannot be checked by eye, so counterfeit or wrong-mix risk violates the traceability requirement.
  9.
    - **Name:** Palomar SLO31-1/2-5 slip-on bead isolator, clip-on/snap-on ferrites, ready-made 1.8-65 MHz line isolators
    - **Why:** No useful CM impedance at 40-500 kHz (all rated from 1.8-3 MHz up), sized for 1/2-in or RG-8X coax with no SMA, and bulkier. This is the same failure as the clip-on budget option STACK already rejects.
- **Confidence:** medium
- **Conditions or tests:** Acceptance gate, conducted bench only, LiteVNA (no on-air sweep):
  1) Wind the sleeve with 9 RG316 turns, loose external loops with a bend radius of about 10 mm or more, sequential passes, input and output at opposite ends. Fit SMA and measure the sleeve stage alone, then the full two-stage choke on the bracket in its final position next to the bonded plate (stray C to the plate is part of the result).
  2) Measure CM |Z|, Rs and Xs at 40, 60, 77.5, 162, 490, 518 kHz and at 1, 1.8, 3, 5, 7, 10, 14, 21, 25 and 30 MHz.
  3) Pass if all of these hold:
     - Combined |Z| is at least 1 kOhm at 60 kHz (LF stage unchanged).
     - Combined |Z| is at least 2 kOhm at every point from 1 to 30 MHz, with no handover dip at 0.3-3 MHz (the 490/518 kHz points must not fall below the 162 kHz value by more than the inductive trend).
     - The sleeve stage alone gives at least 2.3 kOhm at 1 MHz (the 13-turn FT-240-31 datasheet figure, 1.88 kOhm, plus a 20% tolerance margin is the reference).
     - Rs is at least |Xs| over 1-30 MHz where achievable.
  4) If 14-30 MHz is low because of capacitance, trim between 9 and 11 turns. More turns raise 1-5 MHz but lower the SRF, so never go below 9 (that keeps 10-25 MHz not worse by datasheet).
  5) If no turn count from 9 to 11 passes every point, keep the current design: order 2631803802 ($9.35 / EUR 8.21 ex VAT) and wind it as before. The sleeve costs $2.94.
  6) Optional, if a direct A/B against the current pick is wanted, buy both #31 cores. That removes the saving on this unit, so the absolute gate above is the default.
  7) Mechanical check after 10 thermal cycles (or -20 / +60 C if available): no jacket cuts at the bore edges, centre-shield isolation and DC loop resistance unchanged (the labd DC-sense and Boni current window will also catch a short).
- **Stack changes:** - BOM line 'Синфазний дросель КХ': Fair-Rite 5977003801 (FT-240-77) + Fair-Rite 2631102002 (#31 sleeve, 9-11 turns RG316); 2631803802 becomes the fallback if the gate fails. Cores $13.71 (DigiKey US) / EUR 12.04 ex VAT (DigiKey DE). Price status: cores verified 18 Oct 2026; RG316, SMA and bracket still estimated.
  - Mechanics: the HF stage drops from a 61 mm OD, 118 g toroid to a 25.9 x 28.6 mm, 55 g sleeve (about 30 x 50 x 50 mm envelope with loops), saving 63 g. The bracket needs a sleeve cradle with a silicone or foam pad and cable ties, never metal clamps on the ferrite. The bracket stays bonded to the mid-plate and the case envelope is unchanged.
  - Electrical: no change to rails, connectors, drivers or software. Same SMA RG316 path; Boni DC (13.8 V rail per re-audit B, eFuse window 30-150 mA) passes unchanged, and the extra loop resistance is about 0.1 ohm or less.
  - Build note: wind loosely and do not pull RG316 tight around the 6.55 mm sleeve wall. A tight wrap is about a 4.5 mm bend radius against Belden's 25 mm installation minimum; the toroid wrap is about 10 mm.
  - Test plan: add the sleeve gate above to the existing C17 LiteVNA CM measurement.
  - Rule check: receive-only, conducted-only measurement, not an antenna and not an H-field loop probe; no hard rule affected.
- **Sources:**
  - https://fair-rite.com/product/round-cable-emi-suppression-cores-2631102002/
  - https://fair-rite.com/product/round-cable-emi-suppression-cores-2631803802/
  - https://fair-rite.com/product/toroids-5977003801/
  - https://fair-rite.com/product/toroids-5978002701/
  - https://www.digikey.com/en/products/result?keywords=2631102002
  - https://www.digikey.de/en/products/result?keywords=2631102002
  - https://www.digikey.com/en/products/result?keywords=2631803802
  - https://www.digikey.de/en/products/result?keywords=2631803802
  - https://www.digikey.com/en/products/result?keywords=5977003801
  - https://www.digikey.com/en/products/result?keywords=B64290L0659X830
  - https://www.digikey.com/en/products/result?keywords=5978002701
  - https://www.digikey.com/en/products/result?keywords=5977002701
  - https://www.tdk-electronics.tdk.com/inf/80/db/fer/r_40_0_24_0_16_0.pdf
  - https://www.tme.eu/en/details/2631102002/ferrite-sleeves/fair-rite/
  - https://www.tme.eu/en/details/2631803802/ferrite-sleeves/fair-rite/
  - https://www.tme.eu/en/details/5977003801/ring-ferrites/fair-rite/
  - https://catalog.belden.com/index.cfm?event=pd&p=PF_83284
  - https://www.hellschreiber.com/radio/pdf-ant/2018Cookbook.pdf (K9YC Choke Cookbook 2018: parasitic C grows about linearly with N, MnZn #31/#77/#78 have dimensional resonance, +/-10% spread in new #31 cores, RG179 2.4-in #31 data)
  - NOTE: the WebSearch budget for this turn was exhausted, so no further independent measurements of RG316-on-sleeve chokes could be searched for; the TDK N30 material sheet URLs returned 404/403.

