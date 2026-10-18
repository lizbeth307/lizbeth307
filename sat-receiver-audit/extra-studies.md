# Додаткові дослідження: повні відповіді субагентів

## fold:vhf_uhf (run `wf_4a343103-e9e`)

- **Band group:** VHF/UHF: 137 MHz Meteor-M LRPT, 145.8 MHz ISS SSTV, 435-438 MHz CubeSats (RTL-SDR V4L for 137/145.8 MHz, LimeSDR Micro for 435 MHz). Targets unchanged. Packing targets unchanged: recommended tier has no piece longer than about 35 cm; ultra-compact tier no piece longer than about 20 cm.
- **Options:**
  1.
    - **Band:** 137 MHz (also 145.8 MHz retuned, 435 MHz as a test dipole)
    - **Name:** RTL-SDR Blog multipurpose dipole kit as a 137 MHz V-dipole (current pick, already telescopic)
    - **Type:** buy
    - **Fold method:** Telescopic elements screw into the base on M5 threads. The large pair runs 23 cm to 1 m and the small pair 5-13 cm. The base, flexible tripod and RG174 lead are loose parts.
    - **Packed size cm:** Longest piece 23 cm (collapsed element, verified). Whole kit about 23 x 8 x 5 cm (my estimate; the vendor gives no packed size).
    - **Deployed size cm:** Arms 53.4 cm at 120 deg, about 92 cm tip to tip x 27 cm deep. Hold about 1-1.1 m above ground, axis north-south.
    - **Weight g:** Not published (estimate 150-250 g with tripod)
    - **Setup time:** About 1-2 min: extend the elements to marked lengths and set the angle (estimate)
    - **Gain:** About 1.5-3 dBi toward zenith (NEC2 free-space model, sensitive to feed geometry). Linear polarisation, about 3 dB loss on the RHCP Meteor signal.
    - **Gain vs current pick db:** 0 (this is the current pick)
    - **Price:** $17.95 (RTL-SDR Blog store, in stock Oct 2026, from antennas.json)
    - **Availability:** In stock, ships worldwide from China
    - **Durability notes:** Telescopic sections work loose or pull out, and the tripod legs and terminal block are weak. Carry a spare pair of telescopics. The verify stage's advice to fit fixed 53 cm rods breaks the new folding rule; use 2-3 piece rods joined with M5 couplers instead.
    - **Evidence:** Proven on Meteor LRPT (RTL-SDR.com, SatNOGS). Element lengths and M5 thread are verified on the product page.
    - **Sources:**
      - https://www.rtl-sdr.com/DIPOLE
      - https://www.rtl-sdr.com/simple-noaameteor-weather-satellite-antenna-137-mhz-v-dipole/
      - https://community.libre.space/t/mathematical-modeling-and-physical-optimization-of-v-dipole-antennas-for-vhf-imaging-satellite-reception/14844
      - https://www.ebay.de/urw/RTL-SDR-Blog-Multipurpose-Dipole-Antenna-Kit-DE-SPJS-1110-1874-/product-reviews/9013164391?pgn=1
  2.
    - **Band:** 145.8 MHz, re-markable to 137 MHz
    - **Name:** Roll-up tape-measure 3-el Yagi: WB2HOL dimensions on Axotron-style spools with a split boom
    - **Type:** modify
    - **Fold method:** Each tape half-element rolls onto its own 3D-printed spool at the clamp (Axotron v3: six spools/clamps, one hex pin to wind them). The 16 mm PVC boom splits at the driven-element clamp, and the handle swings aside. Ultra variant: cut the boom into 3 sections of 17-18 cm or less.
    - **Packed size cm:** Axotron boom pieces are 34.7 cm and 27.9 cm (verified), so about 35 x 8 x 6 cm with the spools (estimate). With a 3-piece boom, 18 cm or less.
    - **Deployed size cm:** 105 cm wide (reflector) x 51 cm boom. Axotron boom is 62.6 cm.
    - **Weight g:** About 200-300 g (estimate: 25 mm steel tape about 25 g/m, PVC boom, six spools)
    - **Setup time:** About 2-3 min to unroll six tapes to their marks and join the boom (estimate)
    - **Gain:** 7.9 dBi, F/B 17.7 dB at 145.8 (NEC2; same geometry as the rigid WB2HOL). Steel-tape loss about 0.1 dB. Remarked to 137.5 MHz (all lengths x1.060: R 111.4, DE 2x47.8, D 94.6 cm) on the same boom: 7.7 dBi, F/B 20 dB. The same hairpin gives SWR 1.33 (model).
    - **Gain vs current pick db:** 0 at 145.8 (model). Setting errors of up to 1 cm per half cost at most 0.4 dB gain, but F/B can fall to 12 dB. As a 137 MHz antenna it is about +6 dB over the V-dipole when pointed.
    - **Price:** About $15-30 (tape measure, PVC conduit, PETG prints, hose clamps; estimate)
    - **Availability:** DIY. The Axotron 3MF files are a free zip; tape and PVC are sold in any Ukrainian hardware store.
    - **Durability notes:** The spools stop the tape from kinking, which is the main failure of folded tape elements. Lacquer the tape, use adhesive heat-shrink on the hairpin, and mark lengths for both 145.8 and 137.5 MHz. Check that the clamp bridges the reflector and director halves electrically, because a split parasitic element is detuned.
    - **Evidence:** Axotron v3 is a published, built 2 m fox-hunting tape Yagi with roll-up spools; no gain figure is published. The WB2HOL is proven on ISS. My NEC2 numbers are a model.
    - **Sources:**
      - https://axotron.se/blog/?p=1619
      - https://axotron.se/blog/improved-2-m-fox-hunting-antenna/
      - https://axotron.se/blog/wp-content/uploads/2025/02/2m-antenna-v3.zip
      - https://www.w9rh.org/wp-content/uploads/2024/01/2m-tape-measure-yagi-instructions.pdf
      - https://hamradioprep.com/how-to-build-a-tape-measure-yagi-antenna/
  3.
    - **Band:** 145.8 + 435 MHz (crossed, two feeds)
    - **Name:** Packable crossed 2 m/70 cm Yagi: the current crossed pick rebuilt with roll-up 2 m tapes, pivoting 70 cm elements and a 2 x 35 cm keyed boom
    - **Type:** modify
    - **Fold method:** The 0.70 m boom (20x20 mm square PVC/GRP or wood) splits at 0.35 m with a printed square spigot. The square section keeps the two element planes orthogonal (the ±5 deg rule from the NEC study). The 2 m WB2HOL tapes roll onto spools. Each 70 cm N2SPI #8 Al element turns on one centre screw with a 90 deg detent and lies flat along the boom. Both feeds (2 m DE at 0.20 m, 70 cm DE at 0.094 m) sit on the rear half, so no coax crosses the joint.
    - **Packed size cm:** Two boom halves of 35 cm. The longest 70 cm element is 34 cm and folds along the boom. Bundle about 35 x 10 x 6 cm (estimate).
    - **Deployed size cm:** 105 cm (2 m reflector) x 70 cm boom, with 34 cm vertical 70 cm elements
    - **Weight g:** About 350-500 g (estimate)
    - **Setup time:** About 3-4 min (estimate). A similar folding crossband (alpha_adhito 3x6) takes 1-2 min by its builder's report.
    - **Gain:** 7.9 dBi (2 m) and 11.0 dBi (70 cm), from the existing NEC2 crossed-boom study in antennas.json, if orthogonality stays within ±5 deg
    - **Gain vs current pick db:** 0 / 0 (model). The joint gap of 3.4 cm or more from the 70 cm D2 at 0.316 m keeps the element positions unchanged.
    - **Price:** About $25-40 materials (estimate)
    - **Availability:** DIY
    - **Durability notes:** Use a wing-nut pivot with a detent so elements cannot creep off 90 deg. Use PETG/ASA for the prints. Re-check S11 on both ports after the first assembly, and after any re-marking of the tapes.
    - **Evidence:** Mechanism proven separately: Axotron spools; K6ARK-style and alpha_adhito rotating or folding elements. The combination is my design and untested.
    - **Sources:**
      - https://axotron.se/blog/?p=1619
      - https://community.libre.space/t/collapsible-yagi-antennas/14441
      - https://wiki.oarc.uk/2m0iig-satellite-yagi
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
      - https://www.w9rh.org/wp-content/uploads/2024/01/2m-tape-measure-yagi-instructions.pdf
  4.
    - **Band:** 435-438 MHz
    - **Name:** N2SPI/WA5VJB 6-el 70 cm Yagi on a 2-piece boom with pivoting elements (current pick, made packable)
    - **Type:** modify
    - **Fold method:** Split the 64 cm boom at about 32 cm with a keyed ferrule. Elements pivot on centre screws to lie along the boom, or are pushed through grommets and removed. They stay one-piece, so there is no contact at the current maximum.
    - **Packed size cm:** 34 x 4 x 3 cm per half, about 34 x 5 x 4 cm for the pair (estimate). Longest element 34.0 cm (13-3/8 in reflector).
    - **Deployed size cm:** 64 x 34 cm
    - **Weight g:** About 150-250 g (estimate: #8 Al elements about 42 g plus boom)
    - **Setup time:** About 1-2 min (estimate)
    - **Gain:** 11.0 dBi, F/B 24.9 dB, flat 435-438 MHz (NEC2, reproduced: 11.05/11.03/10.99 dBi at 435/436.5/438)
    - **Gain vs current pick db:** 0
    - **Price:** About $10-15 materials (estimate)
    - **Availability:** DIY
    - **Durability notes:** The half-folded driven element can stay on its pivot with the coax attached. Replace the foam board with a varnished batten or GRP tube.
    - **Evidence:** The N2SPI design was used hand-held for FM LEOs. The split boom and pivots are my modification (untested).
    - **Sources:**
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
      - https://wa5vjb.com/yagi-pdf/cheapyagi.pdf
  5.
    - **Band:** 435-438 MHz (ultra-compact)
    - **Name:** 4-el 70 cm Yagi (N2SPI first four elements on a 28.6 cm boom) with screw-in or banana-plug half-elements
    - **Type:** diy
    - **Fold method:** Boom in two 15 cm pieces. Each element is two 17 cm or shorter half-rods (3-4 mm brass/Al) with M3/M4 threads or 4 mm banana plugs. Parasitic sockets are bridged inside the boom by a brass strip. The driven element becomes a straight split dipole with a hairpin, because the half-folded DE cannot be split. A 5-el variant on a 44.5 cm boom (2 x 22 cm) gives 10.6 dBi.
    - **Packed size cm:** About 17 x 4 x 3 cm (estimate)
    - **Deployed size cm:** 29 x 34 cm
    - **Weight g:** About 80-120 g (estimate)
    - **Setup time:** About 2-3 min for 8 half-elements (estimate)
    - **Gain:** 9.5 dBi, F/B 13 dB (NEC2). DE shortened to 0.97x plus a hairpin gives SWR 1.03-1.47 across 435-438 MHz (model).
    - **Gain vs current pick db:** -1.5 (model)
    - **Price:** About $10-20 materials (estimate)
    - **Availability:** DIY
    - **Durability notes:** 12 loose parts is the risk; colour-code them. A threaded centre joint adds about 0.1 dB at most (estimate). Tune with a VNA.
    - **Evidence:** Model only. No build of this exact cut-down was found.
    - **Sources:**
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
      - https://www.makerworld.com/en/models/2781656
  6.
    - **Band:** 145.8 MHz (also 137 and 435 MHz)
    - **Name:** Telescopic-element 3-el 2 m Yagi (M5 telescopics like the dipole-kit ones on a split boom; ZL1SWW/K6ARK concept)
    - **Type:** diy
    - **Fold method:** Telescopic elements pivot or unscrew at the boom, and the boom splits in 2-3 pieces. Lengths are continuously adjustable, so one antenna covers 137.5 and 145.8 MHz.
    - **Packed size cm:** 23-35 cm (23 cm collapsed telescopics, verified for the RTL-SDR kit; boom pieces 25-35 cm)
    - **Deployed size cm:** About 105 x 51 cm
    - **Weight g:** About 200-300 g (estimate)
    - **Setup time:** About 2-3 min (estimate)
    - **Gain:** About 7.5-7.9 dBi if lengths are set to the WB2HOL values (my NEC model of that geometry). ZL1SWW's 7-el telescopic contest Yagi reached 11 dBi (author's figure).
    - **Gain vs current pick db:** 0 to -0.4 (model)
    - **Price:** About $36 if built from two extra dipole kits (2 x $17.95), or generic telescopics (price unverified)
    - **Availability:** DIY
    - **Durability notes:** Telescopics loosen and wobble (dipole-kit reviews). Mark lengths, and expect element sag in wind. The DE impedance of about 15-25 ohm needs a hairpin, or accept about 1-2 dB mismatch on receive.
    - **Evidence:** Concept proven by ZL1SWW (pivoting telescopics) and the OARC K6ARK-based dual-band. The OARC build is low gain: it starts hearing satellites only at about 40-45 deg elevation.
    - **Sources:**
      - https://www.qsl.net/zl1sww/2mPortable%20Yagi.htm
      - https://wiki.oarc.uk/2m0iig-satellite-yagi
      - https://www.rtl-sdr.com/DIPOLE
  7.
    - **Band:** 145.8 + 435 MHz
    - **Name:** alpha_adhito folding crossband Yagi 3x6 V/U (YD1BDE-based), Thingiverse thing:7090427
    - **Type:** diy
    - **Fold method:** The VHF elements fold, with solder wick bridging the hinge of the parasitic element. The UHF elements are removable. The builder says it folds 'into a small bag'.
    - **Packed size cm:** Not quantified (unverified; the Thingiverse page returned 403)
    - **Deployed size cm:** Not published (3-el 2 m / 6-el 70 cm class, about 1 m x 0.5-0.7 m, estimate)
    - **Weight g:** Not published
    - **Setup time:** 1-2 min (builder's report)
    - **Gain:** Not published. A 3-el / 6-el class is about 7.5-8 / 10-11 dBi (class estimate, not measured).
    - **Gain vs current pick db:** About 0 / 0 (unverified)
    - **Price:** DIY, printed parts plus rods (estimate under $30)
    - **Availability:** Free STL on Thingiverse
    - **Durability notes:** The builder calls it 'not the most sturdy but it works'. 400-500 QSOs in about a year.
    - **Evidence:** First-hand SatNOGS forum report, 24 Feb 2026
    - **Sources:**
      - https://community.libre.space/t/collapsible-yagi-antennas/14441
      - https://www.thingiverse.com/thing:7090427
  8.
    - **Band:** 137 MHz (one per band; 145.8 version also possible)
    - **Name:** Wire Moxon on fiberglass spreaders (homebrew; QRP Lifestyle sells a 144/432 version)
    - **Type:** diy
    - **Fold method:** Wire elements coil up. The X-frame of thin fiberglass rods (not carbon) unplugs from a printed hub.
    - **Packed size cm:** About 30-35 cm, set by the spreader segment length (unverified for any specific rod)
    - **Deployed size cm:** 137 MHz: 80 x 29 cm. 145.8 MHz: 76 x 28 cm (scaled Cebik/Moxgen-class dimensions, model).
    - **Weight g:** About 100-200 g (estimate). The QRP Lifestyle 144 MHz Moxon is 133 g (listing).
    - **Setup time:** About 2-3 min (estimate)
    - **Gain:** About 5.5 dBi, F/B about 16 dB, SWR 1.2-1.4 directly on 50 ohm (NEC2). QRP Lifestyle claims 6.1 dBi and F/B over 15 dB on 2 m. Wide beam, so pointing is easy.
    - **Gain vs current pick db:** 137 MHz: about +4 over the V-dipole. 145.8 MHz: -1.8 to -2.4 vs WB2HOL.
    - **Price:** DIY about $15-25 (estimate). QRP Lifestyle price not found.
    - **Availability:** DIY; QRP Lifestyle via pileupdx (product page 404 at check time)
    - **Durability notes:** Wire geometry must be held taut; fiberglass rods only.
    - **Evidence:** Model plus the vendor benchmark
    - **Sources:**
      - https://pileupdx.com/product/qrp-lifestyle-moxon-144-432
      - https://www.jpole-antenna.com/?p=16440
  9.
    - **Band:** 435-438 MHz
    - **Name:** 70 cm wire Moxon (QRP Lifestyle 432 part or DIY)
    - **Type:** buy
    - **Fold method:** No fold needed: it is already only 25 x 10 cm, and the wire version can be flattened.
    - **Packed size cm:** 25 x 10 x 1-2 cm
    - **Deployed size cm:** 25 x 10 cm (vendor) / about 25 x 9 cm (model)
    - **Weight g:** 31 g (vendor listing)
    - **Setup time:** Under 1 min
    - **Gain:** About 5.4 dBi (NEC2, scaled) / 6.1 dBi (vendor)
    - **Gain vs current pick db:** -4.9 to -5.6
    - **Price:** Not found (DIY under $5)
    - **Availability:** Vendor page 404 at check time
    - **Durability notes:** Robust; small enough to hand-hold with the IMU
    - **Evidence:** Vendor listing via search snippet, plus model
    - **Sources:**
      - https://pileupdx.com/product/qrp-lifestyle-moxon-144-432
  10.
    - **Band:** 137 MHz
    - **Name:** Collapsible QFH (DIY concept: 2-piece mast, screw-in half cross-arms, coiled coax or wire loops)
    - **Type:** diy
    - **Fold method:** Mast in two sections of 30 cm or less. Eight screw-in half-arms of about 18 cm. Flexible loops coiled.
    - **Packed size cm:** About 30-35 cm (estimate; full 137 MHz cross-arms are about 34-37 cm, so they must be split)
    - **Deployed size cm:** About 55-60 cm tall x 35-37 cm (approximate standard 137 MHz QFH dimensions, not re-verified). The rigid Diamond KE-137 is 100 cm tall and 1100 g.
    - **Weight g:** About 300-500 g (estimate)
    - **Setup time:** About 5-10 min, and the geometry must be exact
    - **Gain:** Circular and omni. Expect roughly equal to the V-dipole: no 3 dB polarisation loss, but home builds lose about 1 dB, and one user saw it work only above about 35 deg elevation.
    - **Gain vs current pick db:** About 0 to +2 (unverified)
    - **Price:** About $15-30 (estimate)
    - **Availability:** No tested portable build found. The jcoppens site listing an 'Ekkehard portable construction' was unreachable.
    - **Durability notes:** Fussy, and the loops change shape each time. Not recommended.
    - **Evidence:** Weak: no collapsible 137 MHz QFH product or documented build found
    - **Sources:**
      - https://www.wimo.com/en/ke-137
      - https://www.rtl-sdr.com/simple-noaameteor-weather-satellite-antenna-137-mhz-v-dipole/
  11.
    - **Band:** 435-438 MHz
    - **Name:** Cheap collapsible UHF Yagis (eBay/AliExpress 'Collapsible YAGI Gamma 3/5 element 430-450 MHz', MagicalANT Yagi-U)
    - **Type:** buy
    - **Fold method:** Elements fold along the boom on hinges; gamma match
    - **Packed size cm:** 3-el: '17.7 in' (45 cm) in a search snippet (unverified). 5-el: unknown, likely more than 35 cm.
    - **Deployed size cm:** Unknown
    - **Weight g:** 5-el YID05Q: 530 g (listing snippet)
    - **Setup time:** About 1 min (fold-out)
    - **Gain:** 3-el: 7 dBi claimed, beamwidth 53/45 deg. The 5-el '13 dBi' claim is implausible: NEC of a 5-el on a 44.5 cm boom gives 10.6 dBi.
    - **Gain vs current pick db:** About -4 (3-el, claim-based)
    - **Price:** About $54-75 (eBay listings via search snippets; the 5-el listing has ended)
    - **Availability:** eBay/AliExpress; pages returned 403, so unverified
    - **Durability notes:** Rigidity unknown (unanswered question on SatNOGS). SO-239 connector needs an adapter.
    - **Evidence:** Seller claims only
    - **Sources:**
      - https://community.libre.space/t/collapsible-yagi-antennas/14441
      - https://www.ebay.de/itm/256998624992
      - https://www.ebay.com/itm/175847102985
  12.
    - **Band:** 145.8 + 435 MHz
    - **Name:** Arrow II 146/437-10BP (split boom, two BNC feeds)
    - **Type:** buy
    - **Fold method:** Two-piece boom. Aluminium arrow-shaft elements come off the boom. Fits Arrow's optional roll-up bag.
    - **Packed size cm:** Longest part under 22 in (56 cm), per the vendor. Fails the 35 cm target.
    - **Deployed size cm:** Boom 37.5 in (95 cm) x about 1 m (2 m elements; width unverified)
    - **Weight g:** About 19 oz + 1 oz for the split boom, about 570 g (vendor)
    - **Setup time:** A few minutes. Elements are unlabelled, so colour-code them (NT1K).
    - **Gain:** Not published by Arrow. 3-el / 7-el class.
    - **Gain vs current pick db:** About 0 (class estimate, unverified)
    - **Price:** $156.95 (Moonraker US, from antennas.json)
    - **Availability:** Moonraker UK/EU/US; stock not confirmed
    - **Durability notes:** Arrow shafts and inserts can break or go missing; carry spares
    - **Evidence:** The classic proven satellite handheld
    - **Sources:**
      - https://www.arrowantennas.com/arrowii/146-437.html
      - https://moonrakeronline.com/us/arrow-ii-146-437-10bp-without-duplexer-handheld-portable-satellite-antenna
      - https://nt1k.com/antenna-reviews-arrow-satellite-ii-vs-elk-log-periodic/
  13.
    - **Band:** 145.8 + 435 MHz
    - **Name:** Elk Antennas 2M/440L5 log-periodic
    - **Type:** buy
    - **Fold method:** Elements come off; one-piece boom
    - **Packed size cm:** 24 x 3 x 3 in (61 cm), per the vendor. Fails the target.
    - **Deployed size cm:** 61 cm boom x about 1 m
    - **Weight g:** 822 g (1.8125 lb, vendor)
    - **Setup time:** About 2-3 min (estimate)
    - **Gain:** 8.7 dBi (2 m) / 9 dBi (70 cm), manufacturer figures via Gigaparts
    - **Gain vs current pick db:** +0.8 (2 m) / -2.0 (70 cm)
    - **Price:** $137.95-170.95 (elkantennas.com)
    - **Availability:** US only; shipping to Ukraine not verified
    - **Durability notes:** Rugged, but pointing tolerance is tight. Single feed, so it needs a diplexer to feed both SDRs at once.
    - **Evidence:** Owner reports (NT1K, AMSAT-BB)
    - **Sources:**
      - https://elkantennas.com/product/dual-band-2m440l5-log-periodic-antenna/
      - https://www.gigaparts.com/2m-440l5-dual-band-directional-yagi-antenna.html
  14.
    - **Band:** 145.8 + 435 MHz
    - **Name:** WiMo SOTA-Antenne Dualband 2m/70cm (art. 18503, 5-el log-periodic)
    - **Type:** buy
    - **Fold method:** Breaks down to a 64 cm pack
    - **Packed size cm:** 64 cm (vendor). Fails the target.
    - **Deployed size cm:** 61 x 96 cm
    - **Weight g:** About 600 g
    - **Setup time:** Not stated
    - **Gain:** 5 dBi (2 m) / 7 dBi (70 cm), free space (vendor)
    - **Gain vs current pick db:** -2.9 / -4.0
    - **Price:** EUR 139 incl. VAT (WiMo)
    - **Availability:** In stock, ships in 1-2 days
    - **Durability notes:** Single BNC, so both bands share one feed
    - **Evidence:** Vendor data
    - **Sources:**
      - https://www.wimo.com/de/sota-antenne
  15.
    - **Band:** 145.8 MHz (and 435 MHz)
    - **Name:** Dipole kit only (straight dipole, arms about 49 cm for 145.8; small elements for 435)
    - **Type:** buy
    - **Fold method:** Telescopic
    - **Packed size cm:** 23 cm
    - **Deployed size cm:** About 98 cm span (145.8) / about 33 cm (435)
    - **Weight g:** Same kit as the 137 MHz V-dipole
    - **Setup time:** Under 1 min
    - **Gain:** 2.1 dBi (NEC2)
    - **Gain vs current pick db:** -5.8 at 145.8 / -8.9 at 435
    - **Price:** $0 extra (same kit)
    - **Availability:** In stock
    - **Durability notes:** See the dipole kit entry
    - **Evidence:** AMSAT-UK: 'a 2m handheld with a 1/4 wave antenna will be enough' for ISS SSTV (about 25 W output)
    - **Sources:**
      - https://amsat-uk.org/beginners/iss-sstv/
      - https://community.libre.space/t/iss-sstv-ariss-sstv-experiment-october-8-14/12325
- **Recommended:** Recommended foldable kit (no piece longer than 35 cm, all three bands at the same modelled gain as the rigid picks):
  
  (1) **137 MHz:** keep the RTL-SDR Blog dipole kit as the V-dipole ($17.95). It already packs to 23 cm. Carry a spare telescopic pair. Do not follow the verify stage's advice to fit fixed 53 cm rods.
  
  (2) **145.8 + 435 MHz:** the current crossed Yagi rebuilt to pack:
  - The 0.70 m boom becomes two keyed 35 cm halves of square section, which keeps the planes within ±5 deg.
  - The WB2HOL 2 m tape elements roll onto Axotron-style printed spools.
  - The N2SPI 6-el 70 cm #8 Al elements pivot flat on centre screws.
  - The two feeds stay on the rear half.
  - Packed size is about 35 x 10 x 6 cm and weight about 350-500 g (estimate).
  - Setup takes about 3-4 min and materials cost about $25-40.
  - Gain stays 7.9 / 11.0 dBi (NEC model), so 0 dB change.
  
  Bonus: mark the 2 m tapes for 137.5 MHz too (R 111.4, DE 2x47.8, D 94.6 cm). The 2 m half then becomes a 7.7 dBi Meteor Yagi, about +6 dB over the V-dipole (model), for Meteor-M N2-3 and low passes. The same hairpin gives SWR 1.33.
  
  If you don't want the crossed build, use two separate packable antennas instead, at the same gains: the Axotron-style tape Yagi (boom pieces 34.7 and 27.9 cm) and the split-boom N2SPI (34 cm).
  
  No commercial antenna meets 35 cm. The Arrow II 10BP packs to 56 cm, the Elk to 61 cm and the WiMo SOTA to 64 cm.
- **Ultra compact:** Ultra-compact kit (aim: no piece longer than 20 cm):
  
  - **137 and 145.8 MHz:** the dipole kit: V-dipole at 53.4 cm arms, straight dipole at about 49 cm arms for ISS. Its collapsed elements are 23 cm, 3 cm over the target; no shorter M5 telescopic was found. To reach 20 cm, use 3-piece M5-coupled rods or tape arms on spools (concept, untested).
  - **435 MHz:** a 4-element 70 cm Yagi using the first four N2SPI elements on a 28.6 cm boom split into two 15 cm pieces. Half-elements of 17 cm or less screw in or use banana plugs, with a split DE plus hairpin. It models at 9.5 dBi (-1.5 dB vs the 6-el), F/B 13 dB, SWR 1.03-1.47 across 435-438 MHz.
  
  Total about 23 x 8 x 6 cm and under about 400 g (estimate), about $30-40.
  
  Optional: the 2 m roll-up tape Yagi with a 3-piece boom (18 cm or shorter sections) restores 7.9 dBi at 145.8 and 7.7 dBi at 137.5. It costs about 4 min of setup.
- **Losses:**
  1.
    - **Target:** Meteor-M LRPT 137 MHz, recommended kit
    - **With foldable kit:** kept
    - **Margin change db:** 0 (same V-dipole). Optional +6 dB (model) using the re-marked 2 m tape Yagi, hand-pointed.
    - **What we lose:** Nothing in RF terms. The only loss is the verify stage's 'fixed 53 cm rods' durability fix, so telescopic wear remains.
    - **Workaround:** Carry a spare telescopic pair or 3-piece M5 rods. Mount at about 1-1.1 m. Fit the FM band-stop. Use the tape Yagi on N2-3 and low passes.
  2.
    - **Target:** ISS SSTV 145.8 MHz, recommended kit
    - **With foldable kit:** kept
    - **Margin change db:** 0 (model). Worst-case length-setting error costs 0.4 dB gain, and F/B may fall from 17.7 to about 12 dB.
    - **What we lose:** About 2-3 min more setup than the rigid boom (unrolling six tapes). Steel tape needs care against kinks and rust.
    - **Workaround:** Print length marks on the tapes, use a VNA check once, and lacquer the tape
  3.
    - **Target:** CubeSats 435-438 MHz, recommended kit
    - **With foldable kit:** kept
    - **Margin change db:** 0 (11.0 dBi model). Margin model for a 1 W 9k6 FSK satellite: about +5.7 dB at 10 deg and +11 dB at 30 deg elevation.
    - **What we lose:** Nothing in gain. A pivot that creeps more than 10-20 deg off 90 deg costs 0.2-0.8 dB and some F/B (crossed-boom NEC data).
    - **Workaround:** Detented pivots and a square keyed boom joint
  4.
    - **Target:** Meteor-M LRPT 137 MHz, ultra-compact kit
    - **With foldable kit:** kept
    - **Margin change db:** 0
    - **What we lose:** No Yagi option unless the 3-piece tape Yagi is added. The longest piece is 23 cm, not 20 cm.
    - **Workaround:** Add the 3-section tape Yagi (+6 dB, model) for weak passes
  5.
    - **Target:** ISS SSTV 145.8 MHz, ultra-compact kit (dipole only)
    - **With foldable kit:** degraded
    - **Margin change db:** -5.8 vs the WB2HOL (2.1 vs 7.9 dBi). Model CNR in 15 kHz is still about +28 dB at 10 deg (25 W; about +21 dB if only 5 W), far above the FM threshold of about 12 dB.
    - **What we lose:** Directivity: no 17.7 dB F/B against terrestrial QRM such as APRS 144.800 and local noise. Less robustness on low and terrain-blocked passes and in dipole pattern nulls. Image quality is unaffected on normal passes (AMSAT-UK: a 1/4-wave handheld is enough).
    - **Workaround:** Higher ground, the FM band-stop, passes above about 20 deg, IQ recording. Add the 3-section tape Yagi to restore 0 dB.
  6.
    - **Target:** CubeSats 435-438 MHz, ultra-compact kit (4-el 70 cm)
    - **With foldable kit:** degraded
    - **Margin change db:** -1.5 (9.5 vs 11.0 dBi). Model margin for 1 W 9k6 is about +4.2 dB at 10 deg vs +5.7 dB.
    - **What we lose:** F/B drops from 25 to about 13 dB. The weakest 0.5 W satellites lose about 1.5 dB at the horizon. Setup involves 8 loose half-elements.
    - **Workaround:** Filtered 70 cm LNA at the feed (e.g. Uputronics 435 preamp from rf_frontend). Pick passes above 20 deg, or use the 5-el 44.5 cm variant (-0.4 dB) if 22 cm pieces are acceptable.
  7.
    - **Target:** CubeSats 435-438 MHz, dipole-only fallback (no 70 cm Yagi at all)
    - **With foldable kit:** degraded
    - **Margin change db:** -8.9 (2.15 vs 11.0 dBi). Model margin for 1 W 9k6 is -3.2 dB at 10 deg, about 0 at 20 deg, +2.2 at 30 deg, +6 to +7 above 60 deg.
    - **What we lose:** Effectively lost: low-elevation passes, 0.5 W and weaker satellites, and higher-rate (19k2+) links. Only high passes of 1 W 9k6 satellites remain, with polarisation fades.
    - **Workaround:** Fly only passes above about 45-60 deg; FSPL is 8-9 dB lower than at 10 deg, which offsets the gain loss. Add an LNA and use SatNOGS network data for missed satellites.
- **Other ways out:**
  - Choose high passes: at 500 km altitude, path loss at 436.5 MHz is 149.8 dB at 10 deg elevation, 144.4 dB at 30 deg and 140.4 dB at 60 deg. Flying only passes above 45-60 deg recovers 8-9 dB, about what a dipole loses to the 6-el Yagi, at the cost of fewer usable passes per day.
  - Polarisation diversity on 435 MHz: two crossed 70 cm element sets on the same split boom feed both LimeSDR RX channels, which share one LO and so can both sit on 435. Software maximum-ratio or RHCP combining then removes most of the 3 dB polarisation loss and the deep fades from tumbling CubeSats. The cost is a second set of six pivot elements (about 40 g).
  - LNA at the feed: at 435 MHz the Lime's noise figure matters, so a filtered 70 cm preamp recovers about 1-3 dB of system noise (estimate). At 137/145.8 MHz external noise dominates, so an LNA buys little; use the FM band-stop instead.
  - Record IQ and decode offline (SatDump, gr-satellites with the satellite's .yml). Several demodulator settings can be retried on marginal passes.
  - Use the SatNOGS network as a fallback for CubeSat frames the handheld cannot close: you lose your own reception but keep the data.
  - A rigid Yagi kept at a home or car base is unaffected by the backpack rule. Only the travel kit has to fold.
  - Mount on the dipole kit's tripod or the Arrow-style 1/4-20 tripod thread to remove arm fatigue on 10-15 min Meteor passes. The re-marked 137 MHz tape Yagi's wide beam (3-el) tolerates rough pointing.
- **Notes:** **Basis.** I reused antennas.json:
  - picks: V-dipole kit, crossed WB2HOL 7.9 dBi + N2SPI 11.0 dBi on a 0.7 m boom
  - the NEC crossed-boom study
  - the ISS and dipole evidence
  
  The digest and dish_replacement.json have no VHF/UHF link budgets. The absolute margins above therefore come from my own simple model (scripts/nec_vhf/lb.py), and are good to about ±5 dB:
  - CubeSat: 1 W EIRP minus 3 dB pattern loss, 3 dB polarisation and 1.5 dB miscellaneous loss, Tsys 300 K with an LNA, Eb/N0 of 12 dB required at 9600 bps
  - ISS: 25 W per AMSAT-UK, Tsys 1500 K
  
  Treat the relative dB changes as the reliable output.
  
  **Models.** All gains marked 'NEC2' are my free-space, perfect-conductor PyNEC models: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/nec_vhf/m.py, m2.py and m3.py. Steel tape adds about 0.1 dB of loss. My tape-arm V-dipole runs gave unreliable junction results, so I do not quote them; tune tape arms with a VNA. The WB2HOL and N2SPI reproductions match the earlier study (7.89 and 11.03 dBi).
  
  **Key physical constraint.**
  - 70 cm elements, 34 cm at most, fit the 35 cm tier unsplit.
  - 2 m and 137 MHz elements (89-111 cm) must roll, telescope or split into 3+ pieces in any tier.
  - The ultra 20 cm tier also forces split 70 cm elements.
  
  **Errors and conflicts in the input.** The verify stage's fix 'fit fixed 53 cm rods' to the V-dipole now breaks the fold rule. The 0.7 m crossed boom and the 76 cm N2SPI batten are both non-compliant as specified, and must be split as described.
  
  **Commercial check.**
  - No commercial dual-band satellite antenna packs to 35 cm or less: Arrow II 10BP under 56 cm, Elk 2M/440L5 61 cm, WiMo SOTA LPDA 64 cm (EUR 139, 5/7 dBi).
  - Cheap eBay/AliExpress collapsible UHF Yagis exist ($54-75; 7 dBi claimed for the 3-el). Their 13 dBi claim for a 5-el is implausible. I could not inspect them: eBay returned 403.
  
  **Not verified.**
  - Thingiverse 7090427 (403)
  - homingin.com KC6MEH folding tape Yagis (503)
  - jcoppens QFH 'portable construction' (DNS failure)
  - the QRP Lifestyle Moxon page (404; figures from a search snippet)
  
  **Rejected as non-compliant.**
  - KB6NU-listed Thingiverse 3042505: tape elements stored inside the tube, so it packs to about the boom length
  - OARC K6ARK-based telescopic: 1 m boom, low gain
  
  **What is documented and what is new.** Axotron v3's roll-up spools and split boom are a documented build; the crossed packable variant and the split or pivot N2SPI are my untested modifications. Budget: 17 WebSearch calls.

