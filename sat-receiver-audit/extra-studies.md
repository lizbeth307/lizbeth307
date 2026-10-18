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

## fold:lband_sband (run `wf_4a343103-e9e`)

- **Band group:** L-band HRPT/AHRPT 1.69-1.71 GHz and S-band 2.2-2.3 GHz (foldable replacements for the rigid 11-turn helix (473 mm on a 20x20 cm plate) and the rigid helicone (440 mm cone))
- **Options:**
  1.
    - **Band:** L (1.69-1.71 GHz); S-band via a swap-in helix in the same cone
    - **Name:** Fold-flat PETAL helicone: 18 cm base disc + 8 clip-on aluminium petals (cone 18 to 44 cm, 12 cm deep) + 5-turn C=1.1λ RHCP spring helix
    - **Type:** diy
    - **Fold method:** The cone is 8 trapezoid petals of 0.3-0.5 mm aluminium, each about 6.9 cm wide at the bottom, 16.8 cm at the top and 17.7 cm along the slant, plus 1 cm overlap tabs. They clip onto the rim of a 1.5 mm aluminium base disc 18 cm across, with no tools, and lie flat in a stack for transport. The cone wall sits 47° from the axis. The helix is 2 mm phosphor-bronze or copper-clad-steel spring wire wound at 61.7 mm diameter with a 43 mm pitch. It compresses flat onto a 2-section fibreglass rod and is pulled up into printed pitch stops. The SAWbird+ GOES bolts under the disc.
    - **Packed size cm:** Petal stack plus disc about 19 x 19 x 3-4 cm. Helix compressed is about 7 cm across x 3 cm; the rod collapses to about 20 cm (or use a rigid 5-turn helix tube about 7 x 23 cm). All within the 30-35 cm tier.
    - **Deployed size cm:** Cone 44 cm across x 12 cm deep; helix 21.5 cm tall; about 44 x 44 x 23 cm overall
    - **Weight g:** About 350-450 g (estimate)
    - **Setup time:** 2-3 min: 8 clips, pull up the helix, screw on the SMA
    - **Gain:** 15.7 dBic at 1.70 GHz (my NEC2 model), flat at 15.6-15.7 from 1.65 to 1.75 GHz, beam 24-28° wide. A 4-turn helix models 15.7 and a 7-turn 16.0 dBic. A t0nito-like shallower cone (9 cm deep) models 14.8-15.3.
    - **Gain vs current pick db:** +2.2 dB vs the rigid 11-turn helix (13.5). Like-for-like in my model it is +1.7 dB (13.98 for an 11-turn on a 20 cm disc). +1.0 dB vs the rigid 40 cm/15 cm helicone (14.7; my model reproduces 14.74). Models are ±1-3 dB.
    - **Price:** About $20-35 in materials (aluminium sheet and disc, wire, PETG stops, clips; estimate), plus the SAWbird+ GOES ($44.95) already in the kit
    - **Availability:** DIY from hardware-store aluminium, wire and fibreglass rod (available in Ukraine; prices not verified)
    - **Durability notes:** Overlap the petals at least 1 cm so the radial seams don't break the surface currents (an assumption, not modelled). Store the petals flat in a stiff sleeve because dents only cost a little. Don't use soft copper for the spring helix: it work-hardens. Phosphor bronze, Cu-clad steel and even stainless model within 0.06 dB of copper. Per-turn pitch errors of ±6 mm cost 0.3 dB or less, and a ±15% overall stretch error costs 0.3 dB or less (model). The cone catches wind like a small umbrella.
    - **Evidence:** Field precedent for the shape: the t0nito/pe2bz helicone (134 mm base to 440 mm top, 88 mm high, mesh on 8 printed holders) gave clearly stronger signals than a flat reflector at 1545, 1700 and 2250 MHz. Saveitforparts hand-tracked NOAA HRPT with it. No folding version and no SNR figures were published. The gains here are my NEC2 models (PyNEC 2.3.4, wire-grid cone), scripts in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/nec_fold/.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://www.rtl-sdr.com/saveitforparts-testing-a-3d-printable-satellite-antenna-for-noaa-meteor-and-other-polar-orbiting-l-band-satellites/
      - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
  2.
    - **Band:** L (1.69-1.71 GHz)
    - **Name:** Pocket FABRIC helicone ('umbrella cone'): same 18 to 44 cm, 12 cm deep cone in copper-nickel ripstop on 8 hinged fibreglass ribs + 4-turn spring helix
    - **Type:** diy
    - **Fold method:** Eight 3 mm fibreglass ribs (kite spars) about 17.7 cm long are hinged at the edge of an 18 cm base disc and fold inward over it. The CuNi ripstop cone is cut as a 265° annular sector, inner radius 12.2 cm and outer 29.9 cm, and is taped or sewn to the ribs. An elastic cord holds the rim. The 4-turn spring helix (61.7 mm diameter, 172 mm tall) compresses to about 1 cm.
    - **Packed size cm:** A disc about 19 cm across x 3-4 cm thick, plus a rod 18 cm or shorter. Everything is 20 cm or less, so it meets the ultra-compact tier.
    - **Deployed size cm:** 44 cm across x 12 cm cone; helix 18 cm
    - **Weight g:** About 250-350 g (estimate)
    - **Setup time:** 1-2 min
    - **Gain:** 15.6 dBic modelled with octagonal flat facets between the ribs (an ideal cone gives 15.7)
    - **Gain vs current pick db:** +2.1 dB vs the rigid 11-turn (+1.6 like-for-like); +0.9 vs the rigid helicone (models)
    - **Price:** About $15-30 (estimate). A 1 m x 1.1 m piece of CuNi fabric costs about $10-15 (UK listing GBP 83 for an 8 x 1.1 m roll; not verified for Ukraine), plus kite spars, disc and wire.
    - **Availability:** CuNi 'Faraday/RFID' fabric is sold on AliExpress, Walmart and U-buy. No Prom.ua per-metre listing was found. Aluminium fly-screen mesh is a stiffer local alternative.
    - **Durability notes:** Fabric only works as a continuous conductive sheet. Laird and Schlegel CuNi ripstop measures 0.07 Ω/sq or less with more than 62-96 dB of shielding, and Holland's mesh 0.13 Ω/sq or less up to 10 GHz. My model shows sparse radial wires without fabric collapse the gain (8 radials: 10.9 dBic; 4 radials: 8.4), so the fabric must not tear. The ribs can splinter, so cap them with heat-shrink. The fabric is the part most likely to wear first.
    - **Evidence:** There is no field precedent for a fabric helicone. The cone shape follows the t0nito mesh-on-8-holders build. The fabric figures are vendor datasheets. The gains are my model.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://www.directindustry.com/prod/schlegel-electronic-materials/product-229436-2314787.html
      - https://hollandshielding.com/pdfs/Conductive-mesh-8900-TDS-rev-02-06-2026.pdf
      - https://marianinc.com/wp-content/uploads/2025/08/PS-1373.pdf
      - https://www.u-buy.co.uk/product/QV08DUB3A-military-grade-faraday-fabric-5g-emf-protection-signal-shielding-fabric-faraday-material-nickel-copper-faraday-cloth-conductive-for-shields-rfid
  3.
    - **Band:** L (1.69-1.71 GHz)
    - **Name:** Spring/telescopic 11-turn C=1.1λ helix + foldable ground plane (hinged 20x20 plate OR a 30 cm pop-up CuNi disc, optional 4 cm cup rim)
    - **Type:** modify
    - **Fold method:** The existing 11-turn design (61.7 mm diameter, 43 mm pitch, 473 mm) is wound from spring wire. It is stretched along a 3-section telescopic fibreglass rod into printed pitch stops and compresses to about 3 cm. For the ground plane there are three choices: (a) two 10x20 cm aluminium halves on a piano hinge; (b) a twist-fold spring-steel hoop covered in CuNi fabric (a 56 cm photo reflector folds to 23 cm and weighs 274 g, so a 30 cm hoop should fold to about 12 cm); (c) an 18 cm disc with a 4 cm fabric rim flaring to 24 cm.
    - **Packed size cm:** Ground plane 20 x 10 x 0.5 cm (hinged) or about 12-13 cm across x 2 cm (pop-up); rod about 18-20 cm; helix about 7 cm across x 3 cm
    - **Deployed size cm:** 20-30 cm ground plane; 48-50 cm tall
    - **Weight g:** About 200-300 g (estimate)
    - **Setup time:** 1-2 min
    - **Gain:** Modelled: 20 cm disc 13.98, 30 cm disc 13.88, 14 cm disc 13.71, cup rim 14.48 dBic. A 40 cm disc drops to 13.14. 8-turn 12.9, 6-turn 12.0, 5-turn 11.6.
    - **Gain vs current pick db:** -0.3 to +0.5 dB (cup rim) vs the rigid 11-turn helix, i.e. essentially the same if the ground is solid or fabric. -1.0 to -1.5 dB vs the rigid helicone.
    - **Price:** About $10-25 (estimate); the photo-reflector frame price was not verified
    - **Availability:** DIY. Photo pop-up reflectors are widely sold; the stock 'silver' cover's conductivity is unverified, so test it with an ohmmeter or recover it with CuNi fabric.
    - **Durability notes:** It is the simplest to get right because the geometry is the proven rigid pick. It is tolerant: ±6 mm per-turn pitch error costs 0.3 dB or less and ±4 mm radius error 0.4 dB or less (model). The hinge must be continuous metal.
    - **Evidence:** The rigid version is field-proven: Meti's 11-turn helix gave about 7 dB average SNR on Meteor-M2-3, and bending up the ground-plane edges gained about 1.5 dB. The collapsible version is untested; the gains are my model.
    - **Sources:**
      - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
      - https://www.skroutz.mt/s/65550879/smallrig-foldable-photography-reflector-60cm.html
      - https://patents.google.com/patent/US9142882
      - https://patents.google.com/patent/DE202010013085U1/en
  4.
    - **Band:** L and S (one antenna)
    - **Name:** Dual-band C=0.9λ 7-turn helix in the fold-flat 44 cm cone
    - **Type:** diy
    - **Fold method:** Same petal or fabric cone. The helix is 50.5 mm across with a 35.2 mm pitch and is 246 mm long as a spring. Swap the LNA at the feed (SAWbird+ GOES for L-band; wideband LNA plus Sysmocom cf2235-kt30 cavity for S-band) or use a diplexer.
    - **Packed size cm:** As for the petal or fabric helicone: about 19 x 19 x 4 cm plus a rod of about 20-25 cm
    - **Deployed size cm:** 44 cm across x about 25 cm
    - **Weight g:** About 300-450 g (estimate)
    - **Setup time:** 2-3 min plus an LNA swap
    - **Gain:** 14.4 dBic at 1.70 GHz and 15.4 dBic at 2.25 GHz (model)
    - **Gain vs current pick db:** L-band: +0.9 vs the rigid 11-turn, but -1.3 vs the C=1.1 fold helicone. S-band: +1.9 to +2.2 vs the rigid C=0.9 11-turn S helix (13.2-13.5 dBic).
    - **Price:** About $20-35 in materials (estimate). The S-band chain is extra: Sysmocom cf2235-kt30 EUR 65.45 plus an LNA.
    - **Availability:** DIY
    - **Durability notes:** Same as the cone options. The SAWbird+ GOES passes only 1648-1728 MHz, so S-band always needs its own LNA and filter.
    - **Evidence:** Model only. The 75%-scaled t0nito helicone did receive S-band on SatNOGS.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://shop.sysmocom.de/S-Band-cavity-filter-2170-2300-MHz/cf2235-kt30
  5.
    - **Band:** S (2.2-2.3 GHz)
    - **Name:** S-band helix in the L-band fold cone (7-turn C=1.1λ at 2.25 GHz) OR a dedicated 33 cm S-band fold cone with a 5-turn helix
    - **Type:** diy
    - **Fold method:** (a) A 7-turn helix, 46.7 mm across with a 32.5 mm pitch and 228 mm long, on its own SMA. It nests inside the 61.7 mm L-band helix for transport. (b) A separate cone scaled to 75% (13.6 cm base to 33 cm rim, 9 cm deep) in petals or fabric, with a 5-turn helix about 16 cm tall.
    - **Packed size cm:** (a) No extra bulk beyond the helix. (b) About 14 cm across x 3 cm, plus a 16-17 cm helix. Ultra-compact tier.
    - **Deployed size cm:** (a) 44 cm cone. (b) 33 cm cone.
    - **Weight g:** (a) About 30-50 g extra. (b) About 200-250 g (estimate).
    - **Setup time:** (a) 30 s to swap. (b) 1-2 min.
    - **Gain:** (a) 14.2 dBic (a 5-turn in the L cone gives only 13.0). (b) 15.5 dBic. Both at 2.25 GHz, modelled.
    - **Gain vs current pick db:** (a) +0.7 to +1.0 dB. (b) +2.0 to +2.3 dB vs the rigid C=0.9 11-turn S helix (13.2-13.5 dBic).
    - **Price:** (a) About $3-5. (b) About $10-20 (estimate). Plus the S-band LNA and cavity.
    - **Availability:** DIY
    - **Durability notes:** Same as the L-band cones. Wi-Fi 2.4 GHz and LTE sit near the band, so the cavity filter is mandatory.
    - **Evidence:** pe2bz: the 75%-scaled helicone 'There is reception' at 2250 MHz, and after 72 h it found three weak S-band satellites missed before. The gains here are my model.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://community.libre.space/t/station-4125-s-band/13718
  6.
    - **Band:** L (Metop-oriented)
    - **Name:** Fold-flat 2x2 array of spring helices on a 56-60 cm pop-up CuNi ground + 4-way Wilkinson combiner
    - **Type:** diy
    - **Fold method:** Four 7- or 11-turn spring helices on telescopic fibreglass rods stand at about 28-30 cm spacing on a twist-fold spring-hoop ground. A 56 cm photo reflector folds to 23 cm, 274 g; recover it in CuNi fabric. Four equal-length cables run to an RF ONE PDM-00503-S4 combiner (0.7 dB loss, 0.5-3 GHz).
    - **Packed size cm:** A disc about 23 cm across x 2-3 cm, plus 4 compressed helices (about 7 x 3 cm each), 4 rods 20 cm or shorter, a combiner and cables. The 30-35 cm tier.
    - **Deployed size cm:** About 56-60 x 56-60 cm; 30-50 cm tall
    - **Weight g:** About 0.9-1.3 kg with a tripod head (estimate)
    - **Setup time:** 5-10 min plus a pan-tilt tripod
    - **Gain:** Modelled before the combiner: 11-turn 18.75, 7-turn 17.8, 5-turn 16.8 dBic. After the 0.7 dB combiner: 18.0 / 17.1 / 16.1 dBic.
    - **Gain vs current pick db:** +4.5 dB (11-turn) / +3.6 dB (7-turn) vs the rigid 11-turn helix
    - **Price:** About $40-80 in materials (estimate). Combiner and pop-up frame prices are not verified. Optionally 4 SAWbirds at $44.95 each instead of combining before the LNA.
    - **Availability:** DIY. The combiner is from RF ONE through distributors.
    - **Durability notes:** The most complex option. Phase matching needs equal cables and a matching strip per helix, checked with a VNA covering 3 GHz or more. Do not use LimeSDR RX1/RX2 software combining until channel alignment is fixed: LimeSuiteNG issue #356 is open and the LMS7002M flips phase by 0/180° on retune.
    - **Evidence:** Model only. Nobody has documented a dish-free Metop decode.
    - **Sources:**
      - https://www.everythingrf.com/products/power-dividers/rf-one-electronics/612-1911-pdm-00503-s4
      - https://www.skroutz.mt/s/65550879/smallrig-foldable-photography-reflector-60cm.html
      - https://discourse.myriadrf.org/t/limesdr-xtrx-rx-data-out-of-sync/13290
      - https://www.amrita.edu/publication/design-of-axial-mode-helical-antenna-array-for-noaa-18-hrpt-reception-at-1700mhz/
  7.
    - **Band:** L and S
    - **Name:** Flat 2x2 CP patch-tile array (4 air-dielectric corner-truncated patches on 13x13 cm tiles + 4-way combiner)
    - **Type:** diy
    - **Fold method:** Four separate tiles stack like coasters and clip onto a folding X-frame at about 0.75λ spacing (about 13 cm), with 4 equal SMA cables to a Wilkinson combiner. Or one 26x26 cm board hinged once.
    - **Packed size cm:** About 13 x 13 x 4 cm (tiles), or 26 x 13 x 1 cm (hinged board). Ultra-compact.
    - **Deployed size cm:** About 26 x 26 x 1-2 cm
    - **Weight g:** About 300-500 g (estimate)
    - **Setup time:** 3-5 min (4 SMA connections)
    - **Gain:** About 11-13 dBic (estimate). The physical limit for 26x26 cm is 14.4 dBi at 100% efficiency; a measured A*STAR 2x2 L-band array gives more than 11.0 dBic over 1.51-1.68 GHz.
    - **Gain vs current pick db:** -0.5 to -2.5 dB vs the rigid 11-turn helix
    - **Price:** About $20-50 DIY (estimate). No commercial 1.7 GHz RHCP 2x2 board or Gerber was found.
    - **Availability:** DIY only (would need a design scaled and simulated for 1.70 GHz)
    - **Durability notes:** Robust once built, but the CP patch tuning and feed network are the hardest DIY step. No advantage over the helicone.
    - **Evidence:** Only the literature: A*STAR EuCAP 2024, an INMARSAT/GNSS band 2x2. No HRPT use found.
    - **Sources:**
      - https://oar.a-star.edu.sg/communities-collections/articles/19720
      - https://ntrs.nasa.gov/api/citations/19670009367/downloads/19670009367.pdf
  8.
    - **Band:** L and S
    - **Name:** 20 cm dual-polarised 4G/LTE MIMO panel, 1700-2700 MHz (R-Net 'Kvadrat' 2x17, 205x205x50 mm)
    - **Type:** buy
    - **Fold method:** Does not fold. It is a flat 'book', so it fits the size targets but not the spirit of 'must fold'. Bigger panels (Energy 2x24, 43x43 cm) fail the packing target.
    - **Packed size cm:** 20.5 x 20.5 x 5 cm
    - **Deployed size cm:** 20.5 x 20.5 x 5 cm
    - **Weight g:** About 600 g (listing)
    - **Setup time:** 0-1 min
    - **Gain:** The '17 dBi' label is impossible: its aperture caps it at 12.3 dBi at 1.70 GHz. Realistic is about 10-11 dBi linear, and 1.70 GHz is below its 1710 MHz band edge. On an RHCP satellite one port gives about 7-8 dBic-equivalent. Both ports through a 90° hybrid give about 10-10.5 dBic. At 2.25 GHz, about 11-13 dBi per port.
    - **Gain vs current pick db:** L-band: -5.5 to -6.5 dB on a single port; -3 to -4 dB with a hybrid. S-band: -3.5 to -5.5 dB single port; -0.5 to -2.5 dB with a hybrid.
    - **Price:** 1900 UAH for the R-Net (Energy 2x15 at 230 mm: 935 UAH). Connectorised 90° hybrids are expensive (E-meca 1.7-2.2 GHz N-type $504; Pasternack 1-18 GHz $1,100), so use a DIY branch-line coupler or software combining.
    - **Availability:** In stock on Prom.ua (Ukraine)
    - **Durability notes:** Rugged and weatherproof. Real gain and match at 1.70 GHz are unverified, so measure with a VNA. Software combining hits the LimeSDR phase-alignment issue.
    - **Evidence:** Only Prom.ua specs and my aperture calculation. No HRPT reports with these panels.
    - **Sources:**
      - https://prom.ua/Antenny-mimo-2x2.html
      - https://e-meca.com/collections/3-db-hybrids-couplers
      - https://www.pasternack.com/sma-coupler-18-ghz-pe2cp1144-p.aspx
  9.
    - **Band:** L
    - **Name:** Segmented 1.7 GHz loop Yagi (26 elements, 1.81 m boom in 6 push-fit 30 cm sections)
    - **Type:** diy
    - **Fold method:** Square aluminium boom in 6 plug-together sections of about 30 cm. The loops (about 6 cm across) stay riveted to their section.
    - **Packed size cm:** About 31 x 8 x 8 cm bundle
    - **Deployed size cm:** 181 cm long
    - **Weight g:** About 400-700 g (estimate)
    - **Setup time:** 2-3 min, plus a tripod or mount
    - **Gain:** About 20 dBi linear. This is a reader's estimate, not measured. On RHCP that is about 17 dBic-equivalent after the 3 dB polarisation loss.
    - **Gain vs current pick db:** About +3.5 dB vs the rigid 11-turn (unverified). A 1 m version would be about +1.5 (my rough scaling).
    - **Price:** About $20-40 DIY (estimate)
    - **Availability:** DIY
    - **Durability notes:** Narrowband, so it needs tuning. Hand-tracking a 1.8 m boom through a LEO pass is hard and it catches wind. One user found it much cleaner than a helix against terrestrial interference. A linear single port loses a constant 3 dB on CP signals.
    - **Evidence:** rtl-sdr.com RSP2 HRPT tutorial and its comments: decoded HRPT, no SNR figures.
    - **Sources:**
      - https://www.rtl-sdr.com/a-tutorial-on-receiving-hrpt-weather-satellite-images-with-an-sdrplay-rsp2/
  10.
    - **Band:** L and S
    - **Name:** Folding short-backfire (35 cm pop-up fabric main reflector + 4.4 cm fabric rim + 7 cm sub-reflector on a rod + crossed-dipole feed)
    - **Type:** diy
    - **Fold method:** The main reflector is a twist-fold spring hoop with CuNi fabric (35 cm should fold to about 14 cm). The rim is a fabric band. The sub-reflector disc sits on a fibreglass rod about 8.8 cm above. CP comes from a crossed-dipole feed through a 90° hybrid.
    - **Packed size cm:** About 14-15 cm across x 3 cm, plus a 10 cm rod. Ultra-compact.
    - **Deployed size cm:** 35 cm across x about 10 cm
    - **Weight g:** About 200-300 g (estimate)
    - **Setup time:** 2-4 min
    - **Gain:** 12-16 dBi (literature for a 2-2.5λ rim). After the hybrid that is about 11.5-14.5 dBic.
    - **Gain vs current pick db:** -2 to +1 dB vs the rigid 11-turn
    - **Price:** About $15-30 plus a DIY hybrid (estimate)
    - **Availability:** DIY
    - **Durability notes:** Needs a CP feed network that the helix gives for free. No HRPT precedent. It does no better than the helicone, so it is not preferred.
    - **Evidence:** Only the literature. Gain was not modelled here.
    - **Sources:**
      - https://en.wikipedia.org/wiki/Short_backfire_antenna
      - https://ntrs.nasa.gov/api/citations/19670009367/downloads/19670009367.pdf
  11.
    - **Band:** L
    - **Name:** Foil-lined umbrella reflector + linear PCB feed (Saveitforparts build)
    - **Type:** modify
    - **Fold method:** An ordinary umbrella lined with foil tape folds like an umbrella, with the feed on a short rod.
    - **Packed size cm:** About 25-35 cm (travel-umbrella class; estimate)
    - **Deployed size cm:** About 90-100 cm across (estimate; the article gives no size)
    - **Weight g:** About 400-700 g (estimate)
    - **Setup time:** 1-2 min
    - **Gain:** Not measured. The builder calls it 'not a great antenna, but it's something that can be used in a pinch'. A linear feed loses 3 dB on RHCP, and a helix feed in a reflector must be LHCP.
    - **Gain vs current pick db:** Unknown (unverified). It could match or beat the helix if the shape is close to a paraboloid, but there is no data.
    - **Price:** About $10-20 (estimate)
    - **Availability:** DIY
    - **Durability notes:** This brings back a dish-shaped reflector, which the user abandoned. It is not a paraboloid and is very wind-sensitive. The builder had trouble with the helical feed.
    - **Evidence:** Received GOES, NOAA and Meteor HRPT signals. The PCB linear feed 'worked much better' than the helix feed.
    - **Sources:**
      - https://www.rtl-sdr.com/saveitforparts-building-an-l-band-satellite-antenna-out-of-an-umbrella/
  12.
    - **Band:** L and S
    - **Name:** Commercial compact or deployable antennas checked: none qualifies
    - **Type:** buy
    - **Fold method:** None is a hobby-priced folding 1.7 GHz RHCP antenna
    - **Packed size cm:** Not applicable
    - **Gain:** RTL-SDR Blog L-band patch: 1525-1660 MHz, and the vendor says it is not for HRPT. Southwest Antennas 1005-007 conical helix: 1.7-2.7 GHz, 4 dBic. PRC-Com HC-1400-10: 1.1-1.7 GHz, 14.5 dBi, 4.7 kg (10.4 lb), rigid. Discovery Dish: 65 cm in 3 petals, still a dish. HCT Helios deployable helix: space-grade, 400-3000 MHz, memory-alloy deployment, no price.
    - **Gain vs current pick db:** Not applicable (the patch and the Southwest helix are 9-10 dB worse; the PRC-Com is not portable)
    - **Price:** Patch $59.95; the others are not hobby-priced or are unpriced
    - **Availability:** No commercial folding 1.7 GHz antenna for hobbyists was found
    - **Sources:**
      - https://www.rtl-sdr.com/preorder-sale-active-l-band-1525-1660-inmarsat-and-iridium-patch-back-in-stock-for-44-95/
      - https://everythingrf.com/products/all-antennas/southwest-antennas/741-685-1005-007
      - https://www.everythingrf.com/products/all-antennas/prc-com/741-2369-hc-1400-10
      - https://www.rtl-sdr.com/discovery-dish-pre-launch-a-lightweight-dish-and-feed-for-l-band-weather-satellites-and-hydrogen-line-reception/comment-page-4
      - https://satsearch.co/products/helical-communication-technologies-helios-deployable-antenna
- **Recommended:** Fold-flat PETAL helicone with swap-in helices.
  
  - **Build:** an 18 cm 1.5 mm aluminium base disc with the SAWbird+ GOES bolted underneath. Eight clip-on 0.3-0.5 mm aluminium petals form an 18 to 44 cm cone, 12 cm deep, overlapping at least 1 cm.
  - **L-band helix:** 5 turns, C=1.1λ, RHCP, 61.7 mm across, 43 mm pitch, 2 mm phosphor-bronze or Cu-clad-steel spring wire on a 2-section fibreglass rod with printed pitch stops.
  - **S-band helix:** 7 turns, C=1.1λ at 2.25 GHz, 46.7 mm across, 32.5 mm pitch, 228 mm. It nests inside the L-band helix and needs the wideband LNA plus a Sysmocom cf2235-kt30 cavity.
  - **Packed:** about 19 x 19 x 4 cm plus a rod of about 20-23 cm, roughly 0.4-0.5 kg. Setup is 2-3 min with no tools.
  - **Gain (my NEC2 model, ±1-3 dB):** L-band 15.7 dBic, which is +2.2 dB vs the rigid 11-turn (+1.7 like-for-like) and +1.0 vs the rigid helicone. S-band 14.2 dBic, +0.7 to +1.0 vs the rigid S helix. A dedicated 33 cm S cone would give 15.5 dBic.
  - **Why:** it is the only foldable option that improves gain rather than losing it, keeps native RHCP, needs no combiner and no 2-channel software, and copies a field-tested shape (the t0nito mesh-on-8-holders helicone).
  - **First test:** validate on Elektro-L5 LRIT at 1691 MHz against the rigid helix before trusting the numbers.
- **Ultra compact:** Pocket FABRIC helicone: the same 18 to 44 cm, 12 cm cone made of copper-nickel ripstop (0.07 Ω/sq or less) on 8 hinged 3 mm fibreglass ribs that fold in over the 18 cm base disc, with a 4-turn C=1.1λ spring helix (172 mm, compresses to about 1 cm).
  
  - **Packed:** a disc about 19 cm across x 3-4 cm plus a rod 18 cm or shorter. Every part is 20 cm or less, about 250-350 g, 1-2 min setup.
  - **Gain:** 15.6 dBic modelled with octagonal facets, about +2 dB vs the rigid 11-turn.
  - **If no fabric is wanted:** the 11-turn spring helix on a 30 cm twist-fold pop-up disc (about 12-13 cm across x 2 cm packed, plus a 20 cm rod) models 13.7-13.9 dBic, essentially the same as the rigid pick (-0.3 to +0.4 dB).
  - **Fallback with no folding at all:** a rigid 4-5 turn helix on an 18 cm plate (18 x 18 x 19-22 cm) models 11.6-12.0 dBic, -1.5 to -1.9 dB. Meteor is still kept; Metop is lost.
- **Losses:**
  1.
    - **Target:** Meteor-M N2-3/N2-4 HRPT, 1.70 GHz, 665 kbps (needs 0.5 dB SNR in SatDump)
    - **With foldable kit:** kept
    - **Margin change db:** +1.7 to +2.2 dB vs the rigid 11-turn helix (model). Estimated average SNR is about 8.5-9.5 dB, a margin of about +8.9 to +9.4 dB, against about +7.2 dB with the rigid pick. Spring 11-turn with pop-up ground: -0.3 to +0.4 dB. No-fold 5-turn helix on a plate: -1.9 dB, margin still about +5 dB.
    - **What we lose:** Nothing in link margin if the fold helicone is built correctly. What we do lose:
  - 2-3 min of setup.
  - Wind tolerance: the 44 cm cone catches wind like an umbrella.
  - Spare-part risk: petals, ribs and clips can get lost.
  - The beam is slightly narrower (24-28° vs 28-32°), so a ±7° hand-pointing error costs about 0.9 dB instead of 0.65 dB.
  - Certainty: the gain is a model, and no first-hand dish-free hand-tracked Meteor HRPT decode has been documented.
    - **Workaround:** Use a 20-25 cm folding mini tripod with a pan-tilt head and the BNO085 pointing aid. Hold the antenna at least 50 cm above ground. A/B test against the rigid helix on Elektro-L5 LRIT.
  2.
    - **Target:** Metop-B AHRPT, 1.70 GHz, about 3.5 Mbps / 2.333 Msym/s (needs 4 dB SNR). Metop-C AHRPT is 'No' per NOAA OSPO, Sept 2026.
    - **With foldable kit:** degraded
    - **Margin change db:** The rigid 11-turn is about -1.6 dB below threshold on a pass average, effectively lost. The fold helicone is about 0 to +0.5 dB average (+1.7 to +2.2 dB better), but minus 0.5-1 dB of pointing loss and about 0.5 dB of build tolerance. Slant range costs 6.8 dB at 20° elevation and 2.5 dB at 45°, relative to zenith.
    - **What we lose:** Low and medium passes (maximum elevation below about 45°) and the ends of every pass. At best, partial AVHRR swaths near the time of closest approach on high passes. Decode reliability will be poor. The Metop EIRP is not verified, so the estimate is ±2-3 dB. Nobody has documented a dish-free Metop decode.
    - **Workaround:** Fold-flat 2x2 spring-helix array on a 60 cm pop-up ground: 17.1-18.0 dBic after the combiner (model), about +2 to +3 dB average margin, 5-10 min setup on a tripod. Or a segmented 1.8 m loop Yagi (about 17 dBic-equivalent, unverified). Or the umbrella reflector (gain unknown). Or Metop data from online archives instead of reception.
  3.
    - **Target:** FengYun-3 AHRPT
    - **With foldable kit:** lost
    - **Margin change db:** Not applicable
    - **What we lose:** Lost with any antenna, rigid or foldable. FY-3C L-band ended in 2024, and FY-3D to FY-3H AHRPT is X-band at 7.8 GHz and 30-38 Msym/s, which needs a tracked dish of roughly 1 m.
    - **Workaround:** None within this kit
  4.
    - **Target:** Elektro-L5 LRIT, 1691 MHz, geostationary at 76°E (bonus target and gain-test source)
    - **With foldable kit:** kept
    - **Margin change db:** +1.7 to +2.2 dB vs the rigid helix (model). LRIT decodes at about +1 dB SNR.
    - **What we lose:** Nothing. It needs no tracking, so the fold helicone can sit on a mini tripod.
    - **Workaround:** Use it as the A/B reference to measure the real gain of each foldable build
  5.
    - **Target:** S-band 2.2-2.3 GHz downlinks (CubeSat/SatNOGS-class)
    - **With foldable kit:** kept
    - **Margin change db:** +0.7 to +1.0 dB (7-turn S helix in the L cone) or +2.0 to +2.3 dB (dedicated 33 cm S cone) vs the rigid C=0.9 11-turn S helix (13.2-13.5 dBic). The dual-band C=0.9 helix gives +1.9 to +2.2 on S-band but costs 1.3 dB on L-band vs the C=1.1 helix in the same fold cone. Our files hold no absolute S-band link budget.
    - **What we lose:** Simultaneous L/S reception from one feed. You must swap the helix and the LNA, because the SAWbird+ GOES passes only 1648-1728 MHz. The S chain needs its own LNA and cavity (Sysmocom cf2235-kt30, EUR 65.45). There is a 30 s swap per band change. Whether a given weak CubeSat decodes remains unknown, as it was with the rigid pick.
    - **Workaround:** Keep a dedicated 33 cm fold S cone (packs about 14 cm across x 3 cm) if S-band matters more than one-cone simplicity
  6.
    - **Target:** Kit-level: setup time, reliability, mechanics (all L/S options)
    - **With foldable kit:** degraded
    - **Margin change db:** 0 to -0.5 dB per assembly from build tolerance: modelled ±6 mm per-turn pitch error costs 0.3 dB or less, octagonal fabric facets 0.15 dB. Sparse radial wires without fabric cost 1.8-5.6 dB, so avoid them.
    - **What we lose:** - Setup goes from 0 to 1-3 min (5-10 min for the 2x2 array).
  - More parts to lose.
  - Repeat-folding wear on the fabric, ribs and spring wire. Soft copper fatigues; use phosphor bronze or Cu-clad steel.
  - Each fold or unfold can shift the geometry slightly.
  - Every gain figure is an unmeasured NEC2 model, ±1-3 dB.
    - **Workaround:** Print pitch stops into the rod, key the petals so they fit only one way, carry 2 spare ribs and clips, and keep the matching strip glued. Check S11 better than -10 dB over 1690-1710 MHz after each trip with a VNA covering 3 GHz or more.
- **Other ways out:**
  - Meteor LRPT at 137 MHz with the V-dipole already in the kit, as the fallback when HRPT fails. LRPT is 72 kbps and carries fewer MSU-MR channels than HRPT (3 vs 6, which is general knowledge and was not re-verified in this run). No 1.7 GHz antenna is needed.
  - Elektro-L5 LRIT at 1691 MHz from a fixed mini tripod. It is geostationary at 76°E and about 19° up from Kyiv, so it needs no tracking. It decodes at about +1 dB SNR, keeps an L-band target alive even on a 4-5 turn plate helix, and serves as the gain test source.
  - For Metop-B: a fold-flat 2x2 spring-helix array on a 60 cm twist-fold CuNi ground (packs to a disc about 23 cm across). It models 17.1-18.0 dBic after a 0.7 dB Wilkinson combiner. Use passive combining into a single RX, not LimeSDR RX1/RX2, until LimeSuiteNG channel alignment (issue #356) is fixed.
  - For Metop-B: a segmented 1.8 m loop Yagi in 6 sections of 30 cm (about 20 dBi linear per a reader estimate, unverified, so about 17 dBic-equivalent on RHCP). It is also cleaner against LTE than a helix, but hard to hand-track.
  - A foil-lined travel umbrella with a linear PCB feed (Saveitforparts received GOES, NOAA and Meteor HRPT with one). It folds to umbrella size, but its gain is unmeasured and it brings back a dish shape.
  - Mount any of the antennas on a 20-25 cm folding tripod with a pan-tilt head to remove 0.5-1.5 dB of hand-pointing loss with the 24-28° beams.
  - If the user also rejects fabric and petals: a rigid 4-5 turn helix on an 18 cm plate (11.6-12.0 dBic modelled, packs 18 x 18 x 19-22 cm). Meteor HRPT keeps about 5 dB of margin, Metop is lost, and S-band uses a 5-turn S helix (11.4 dBic modelled, about -2 dB).
  - Use online archives (for example the EUMETSAT Data Store, not checked in this run) for Metop and FengYun imagery that the kit can no longer receive.
- **Notes:** Working targets unchanged: packed 30-35 cm for the backpack tier and 20 cm or less for the ultra-compact tier, with a large deployed size allowed if setup takes a few minutes. The recommended fold helicone has no part over about 19-23 cm, so it also meets the ultra-compact tier with a 4-turn or spring helix.
  
  **Modelling (all gains are my models, unmeasured)**
  - NEC2 via PyNEC 2.3.4. Wire-grid discs and cones, 2 mm copper wire, gain as maximum RHCP.
  - Cross-check against earlier results: the same code reproduces the earlier helicone figure (40 cm rim, 15 cm deep: 14.74 dBic vs 14.7). It gives 13.98 dBic for the 11-turn on a 20 cm round disc, against the earlier 13.5 on a square plate, so deltas are quoted both ways (±0.5 dB).
  - Main new finding: a shallower, wider cone (18 cm base to 44 cm rim, 12 cm deep) with only 4-7 turns models 15.6-16.0 dBic, flat across 1.65-1.75 GHz, with a 24-28° beam. So the long helix is unnecessary. The cone is the part that folds, and the 17-23 cm helix fits the packing target even when rigid.
  - Tolerance results:
    - ±6 mm per-turn pitch error costs 0.3 dB or less; ±10 mm costs up to 0.6 dB.
    - ±4 mm radius error costs 0.4 dB or less.
    - ±10-15% overall stretch error costs 0.1-0.3 dB.
    - Phosphor bronze or stainless instead of copper costs 0.06 dB or less.
    - Octagonal fabric facets cost 0.15 dB.
    - A radial-wire-only ground plane is bad: 8.4-12.2 dBic.
    - A 40 cm flat disc is worse than a 20-30 cm one.
    - A 4 cm cup rim adds 0.5 dB.
  - 2x2 arrays (before the combiner): 11-turn 18.75, 7-turn 17.8, 5-turn 16.8 dBic on a 56 cm ground.
  - S-band: a scaled 33 cm helicone gives 15.5 dBic; a C=1.1λ 7-turn S helix in the L-band cone gives 14.2; a 5-turn on a 15 cm disc gives 11.4.
  - Scripts are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/nec_fold/ (fold.py, t2-t10.py).
  
  **Margin anchor (reused from dish_replacement.json, not redone)**
  - Meti's 11-turn helix (about 12.75 dBic) gave about 7 dB average SNR on Meteor-M2-3, against 0.5 dB needed.
  - Metop is estimated at about 1.6 dB average, against 4 dB needed (5.4 dB symbol-rate penalty, EIRP unverified).
  - I assumed SNR scales dB-for-dB with antenna gain.
  - Slant range at about 830 km orbit height costs 9.3 dB at 10° elevation, 6.8 dB at 20°, 4.8 dB at 30° and 2.5 dB at 45°, relative to zenith.
  
  **Evidence gaps**
  - I found no hobby or commercial folding 1.7 GHz antenna anywhere. The evidence for the concept is patents (US9142882 compressible spiral; DE202010013085U1 self-expanding helix; US8970447 nanosat deployable helix), the Georgia Tech origami helix and the HCT Helios space-grade deployable helix.
  - The closest real precedent is the t0nito/pe2bz helicone: mesh on 8 holders, stronger signals at 1545, 1700 and 2250 MHz, no SNR figures.
  - Unverified prices: CuNi fabric (about GBP 83 for 8 x 1.1 m), the pop-up reflector frame, the combiner, and all DIY materials.
  - Unverified gains: the 4G panel at 1.70 GHz (below its band edge), and the umbrella and loop-Yagi figures.
  
  **Polarisation**
  - Linear antennas (LTE panels, loop Yagi, umbrella with a PCB feed) lose a constant 3 dB on RHCP Meteor and Metop signals.
  - Fixing that takes a 90° hybrid. Connectorised hybrids cost $504 (E-meca 1.7-2.2 GHz) to $1,100 (Pasternack), so use a DIY branch-line coupler or software combining. Software combining is blocked on the LimeSDR Micro by the RX phase-alignment issue.
  
  **Search budget:** 16 web searches used.

