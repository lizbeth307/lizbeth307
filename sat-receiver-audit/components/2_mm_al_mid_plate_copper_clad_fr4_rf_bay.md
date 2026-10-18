# 2 mm al mid plate copper clad fr4 rf bay: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_37583a7b-1a8`_

- **Part:** Chassis set: 2 mm Al mid-plate + copper-clad FR4 RF bay + steel 1/4-20 mount + KSD9700 70 C (Mechanical, core, qty 1 set)
- **Current pick:** Generic set from STACK v1 line 275: a locally machined 2 mm Al mid-plate (alloy never named), a soldered copper-clad FR4 RF bay, a steel 1/4-20 press-in insert or captured nut (final_integration allows either, in a boss of 6 mm or more, never tapped into the plate), and a KSD9700 70 C NO wired at signal level in parallel with the CHG_INHIBIT MOSFET (power.json). No SKU, alloy or seller is named for any item.
- **Current price usd:** 35-70 for the set (STACK v1 model, 'local'; no line is verified). Earlier model breakdown: plate, pedestal and pads 15-25; FR4 and tape about 5; bulkheads and captured nut 10-15; KSD9700 unpriced.
- **Decision:** replace_conditionally
- **Chosen:** Item by item:
  (1) KSD9700: REPLACE with Piekarz (PL) item 31610, "Thermostat; bimetallic; KSD9700; NO; 70°C; 5A; 250V AC; 4,2x8x20mm; leads". Buy 5 and bench-bin them: one fitted, one for the spares kit, the rest spare.
  (2) 1/4-20 mount: use the stack's already-allowed captured nut, a zinc-plated steel 1/4-20 UNC hex nut (ASME B18.2.2, 7/16 in AF, 7/32 in thick), loaded from the inside into a hex pocket in the ASA boss, plus the tests below.
  (3) Mid-plate: CONDITIONAL. A 2.0 mm EN AW-5754 (AlMg3) cut-to-size blank from Alu-Verkauf (Hildesheim, DE), drilled at home with the Q6A board or a 1:1 template from STEP V1.21. Pedestal stock from the same parcel: 10 mm AlMg3 50x50, or 25x25x75. Use this only if a local machining quote exceeds the landed DIY cost AND the thermal soak passes; otherwise keep local machining. Note the conductivity issue under equivalence_proof.
  (4) RF-bay FR4: KEEP the spec. No source is cheaper than the $5 model. Named sources: Bungard 120306Z33 1.5 mm 35/35 um 160x100 (TME) x2, or Scankemi 1.6 mm 35/35 um (Electrokit 41003697) x1.
- **Chosen price usd:** About 27-49 for the covered items, delivered in Germany. FX is approximate (EUR 1.16, PLN 0.27, SEK 0.105 USD).
  - Plate 2 mm AlMg3 150x250: EUR 5.95 incl. 19% VAT = 6.90. Configurator variants dated 13-17 Oct 2026; one 110x216 cut was EUR 3.81 on 15 Oct.
  - Pedestal stock: 25x25x75 EUR 3.81 = 4.42, or 10 mm 50x50 EUR 8.33 = 9.66.
  - Alu-Verkauf shipping up to 5 kg: DE EUR 6.95 = 8.06; AT/BE/NL/LU/DK EUR 12.95 = 15.02; FR EUR 19.50 = 22.6; SE EUR 27.50 = 31.9. Other EU countries are not listed.
  - FR4: Bungard 2x 2.97-3.70 = 5.94-7.40 (TME JSON-LD; net/gross not stated; TME shipping not verified). Or Electrokit 76 SEK incl. 25% VAT = about 7.98.
  - KSD9700 Piekarz 31610: 2.75 PLN net at 1+ (about 0.74 net, 0.91 with 23% VAT); 1.89 PLN at 5+ (5 pcs about 2.55 net, 3.14 gross). 33 in stock. Piekarz shipping not verified.
  - 1/4-20 nut: RS PRO 245-0741 100-pack EUR 11.63 ex VAT = about 13.5 (search snippet only; the RS page returned 403), so UNVERIFIED. A single nut from a local shop is unpriced.
  Bulkheads and thermal pads are unchanged and not included.
- **Saving usd:** 0 proven. With verified prices, the covered items cost about 27-49 delivered in DE. That matches the model's equivalent lines (about 20-35 plus the unpriced KSD9700), so on paper nothing is saved, and outside DE/AT/Benelux the plate shipping alone (15-32) makes it worse. The only real saving is the plate machining labour, and only if a local quote for plate plus pedestal comes in above about 25 in DE (35-45 for FR/SE). No such quote exists. The KSD9700 and nut changes save under 1-2 each.
- **Equivalence proof:** KSD9700, Piekarz 31610 (equal):
  - The listing says NO, 70 C, 5 A/250 VAC, 4.2x8x20 mm, leads; 33 in stock.
  - That matches power.json exactly: NO, glued to the hottest IP2368 MOSFET, in parallel with CHG_INHIBIT, signal-level current, so the AC rating has a huge margin. The body is the size the stack specifies.
  - Like the current generic KSD9700, the listing gives no tolerance, reset, shell material or approval. So it is equal to the current pick, not better.
  - Class datasheet (Xucheng KSD9700, LCSC PDF, read): trip 70+/-5 C, reset 50+/-10 C (hysteresis >=15 K), <=50 mOhm, 10,000 cycles at AC250V 5A, 1450 VAC hipot, CQC, iron shell, part code "B = normally closed, K = normally open".
  - The missing data is covered by the bench test (conditions).
  
  1/4-20 captured nut (equal or better, but proven only by test):
  - Same steel 1/4-20 UNC thread. The hex pocket gives a positive anti-rotation lock. The stack already allows it ("a captured 1/4-20 nut, or a press-in steel insert in a boss of 6 mm or more", final_integration).
  - CNC Kitchen, read (M3, PETG, 4 perimeters, 100% infill, 3 pull samples): bottom-pocket nut about 166 kg pull-out vs heat-set insert 119 kg. Torque-out was about 2 Nm vs 3 Nm, so the nut was WORSE at M3. My scaling: a 1/4-20 nut has about 4x the M3 bearing area and about half the clamp force per Nm, so bearing stress per Nm is about 1/9. Hand-tight tripod torque should therefore be far below the crush limit, but no 1/4-20 measurement exists, so a test is required.
  - Disadvantage the searches missed: a nut loaded from the inside sits behind an outer skin, so a short tripod or quick-release screw engages fewer threads than with a flush insert. Hence the skin and engagement condition.
  
  Mid-plate, 2.0 mm 5754 (equal in every spec except conductivity, which is unproven):
  - Thickness is equal. E is 68 GPa (MakeItFrom) against about 70 for any Al alloy, so stiffness is equal. Density is equal, so mass is about 140 g at 210x125 mm. The bare, deburred surface suits bond points.
  - Thermal conductivity is 130 W/mK (MakeItFrom and Wikipedia, both read), NOT the 140-160 both searches claimed. Their Wieland PDF returns 404, so that figure is unverified.
  - For comparison: a 6xxx-T6 plate is 180 W/mK (the Aalco sheet served at the cited URL) and 1050A is 222 W/mK (RS PRO datasheet, read). STACK never fixed an alloy, so whether 5754 is not-worse depends on the baseline. A local shop may well use 5754 too.
  - My model: in-plane spreading resistance goes with 1/k, so 130 vs 167 W/mK is about +28% plate temperature rise, roughly +1-2 K at the Lime pedestal at 4 W typical.
  - Shielding: 33% IACS. A 2 mm plate is still more than a skin depth thick from about 10 kHz up (delta about 1.15 mm at 10 kHz, my calculation). The 35 um FR4 bay is the weaker shield, so there is no material change.
  - Holes: the board holes are 3.5 mm for M2.5, giving about 0.5 mm of float. A drill-press template at +/-0.2 mm is enough.
  - Conclusion: not-worse holds only if the stack's own thermal acceptance test passes.
  
  FR4 (equal):
  - Bungard 120306Z33: FR4 glass-epoxy, 1.5 mm, 35 um copper, double-sided. It is photoresist-coated; strip it before soldering.
  - Electrokit 41003697: FR4 1.6 mm, 35/35 um, 27 in stock.
  - Neither states UL94. The bay is at the top edge, not at the charger or battery barrier.
  - Both cost the same as or more than the $5 model, so this is a keep with named sources.
  
  Hard rules: all passive mechanics. Nothing transmits, there are no loop structures, and the thermostat check is thermal or conducted only.
- **Rejected:**
  1.
    - **Name:** Xucheng KSD9700-70/5JSB/080C (LCSC C156512)
    - **Why:** Normally closed: the datasheet says 'B = normal closed, K = normal open' and the page says '1 pole opener'. That is the wrong contact form for the NO-in-parallel-with-CHG_INHIBIT wiring, so it is a design change, not a drop-in. LCSC's attributes (75/60 C) contradict its own datasheet (70+/-5 / 50+/-10 C). Stock 36. It ships from CN, and since 1 Jul 2026 low-value EU imports carry a flat duty (operator note 34; amount unverified), which outweighs the $0.30 difference. Usable only if v2 deliberately chooses an NC fail-safe loop.
  2.
    - **Name:** Xucheng KSD301-70/103PAK (LCSC C156501)
    - **Why:** NO, with better ratings, but the body is 16 mm in diameter, 33.6 mm long with the bracket and 11.8 mm tall, with 6.3 mm tabs. It cannot be glued to the IP2368 MOSFET, so the sensing point changes. The vendor's own test table shows 72-78 C for all 5 samples, outside its stated 70+/-3 C.
  3.
    - **Name:** JLCCNC laser-cut 5052 plate
    - **Why:** No published price (CAD quote only), shipping from CN plus the EU low-value duty, and 5052 conductivity (about 138 W/mK, not verified here) is no better than 5754. Not proven cheaper.
  4.
    - **Name:** metallshopper.de 2 mm EN AW-5754 cut to size
    - **Why:** Not rejected on spec: same alloy as the chosen blank, raw, deburred, EUR 128.21/m2 ex VAT (about EUR 3.4-4.1 ex VAT for 210x125 to 230x140 mm). Shipping is shown only in the cart (unverified), so the landed cost is unproven. A fallback to Alu-Verkauf.
  5.
    - **Name:** Alu-Verkauf 2 mm AlMg1_elox (anodized)
    - **Why:** The anodized surface insulates the GND standoff, bulkhead and FR4-seam bond points, and at EUR 10.12 for 180x250 it costs more than AlMg3.
  6.
    - **Name:** Alu-Verkauf 2 mm AlCuMg1 (2017A)
    - **Why:** EUR 17.00 for 300x300 vs EUR 13.82 for AlMg3. Dearer, and no conductivity advantage was shown.
  7.
    - **Name:** Solder Peak LAM210X297ED1.5 FR4
    - **Why:** 18 um copper vs the required 35 um: worse absorption at HF/LF and weaker at hand-soldered seams.
  8.
    - **Name:** eBay.de Trinity Fastener 1/4-20 nuts, 10 pcs, $5.35
    - **Why:** Page returned 403, so the price is unverified. Ships from the US, so EU duty, VAT and possible express fees apply.
  9.
    - **Name:** Brass heat-set 1/4-20 inserts, side-loaded nut pocket, anonymous eBay KSD9700 lots, generic AliExpress 'FR4', firmware-only NTC limit
    - **Why:** Brass threads wear faster than steel. A side pocket measured 86 kg vs 119 kg for the insert (CNC Kitchen, read). The anonymous parts have no evidence of their spec or material. A firmware limit removes the independent hardware backstop.
- **Confidence:** medium
- **Conditions or tests:** 1. KSD9700 (each unit):
  - Hot plate or stirred bath with a K-type thermocouple, ramp 1 K/min or slower.
  - Must close at 65-75 C and reopen at least 15 K lower. Closed resistance 50 mOhm or less (4-wire). 10 cycles.
  - Magnet test: the iron shell must be magnetic. Reject plastic-shell units, which couple worse.
  - Fit the best-binned unit with polyimide between the shell and the MOSFET tab.
  - In the 2 h IP2368 burn-in it must not trip. A hot-air test on the MOSFET must assert CHG_INHIBIT at 75 C or below.
  
  2. Mid-plate (only if a local quote for plate plus pedestal is above about $25 in DE, or $35-45 in FR/SE):
  - Holes within +/-0.2 mm of V1.21; the Q6A drops on without force.
  - Flatness 0.2 mm or better under the Q6A, the pedestal and both TPS7A4701/D36V50F12 pads (feeler gauge on float glass).
  - Deburred, bare bond points, never tapped.
  - Riser window about 26x20 mm; UFS boss or slot at least 30 mm from the pedestal.
  - Then the stack's 45-min noon soak with the Lime in modes B, D, G and H: frame 60 C or less, LMS7002M (lms7_temp) 75 C or less, ufs-thermal no worse, cells 45 C or less.
  - If any margin is under 3 K or a limit fails, use 1050A-H14 (222 W/mK) or 6082-T6 (about 180) instead. No verified cut-to-size price was found for those.
  
  3. Captured nut:
  - Hex pocket 11.3 mm AF, about 5.8 mm deep, loaded from the inside, nut glued or capped.
  - Outer skin 1.0 mm or less, with a 6.6 mm clearance hole. At least 3 full threads (3.8 mm) engaged with the shortest tripod or quick-release screw the user owns (measure protrusion minus skin). At least 3 mm screw-tip clearance behind the nut.
  - ASA boss at 100% infill with 4 or more perimeters.
  - Pull test at 3x device weight (about 4.5-5.3 kg) for 60 s. Torque test to 3 Nm or more without spin or crush (my threshold). 20 mount/unmount cycles.
  
  4. FR4 on arrival:
  - Glass weave visible at the cut edge; no blistering after 10 s at 350 C.
  - Measure the Electrokit sheet: the title says 233x160, the description says 200x160.
  - If two 160x100 sheets are used, solder the splice continuously on both faces.
- **Stack changes:** - Chassis line (STACK.md 275):
    - Name the sources and the alloy: "2.0 mm EN AW-5754 mill finish, 130 W/mK, accepted only if the Lime soak passes; else 1050A or 6082-T6".
    - Correct the searches' "5754 = 140-160 W/mK".
    - Keep "never tap the plate".
    - Add a 1:1 drill template from STEP V1.21 to build/.
  - KSD9700:
    - Remove the double count. It appears in the charger line (STACK.md 247) and the chassis line (275), plus one in the spares kit. Keep one line: Piekarz 31610, qty 5 for binning, about 9.45 PLN net.
    - Fix the wiring text in STACK.md lines 841 and 950 and in final_integration ("in its input") to match power.json: NO, signal level, in parallel with the CHG_INHIBIT MOSFET. Never in series with the 20 V PD VBUS (no DC rating; 50 mOhm self-heating).
    - Add polyimide insulation under the shell.
  - Rear boss (case STL): replace the insert bore with the back-loaded 7/16 in hex pocket and clearance hole described in conditions.
  - FR4: add "strip the Bungard photoresist before soldering"; seams stay at 7 mm or less.
  - Sourcing: prefer EU sellers (Alu-Verkauf DE, Piekarz PL, TME PL, Electrokit SE) because of the July 2026 EU low-value import duty (operator note 34; amount unverified). Consolidate the TME and Piekarz lines with other stack orders, because their shipping is not verified.
  - Keep the chassis cost at 35-70 (model) until a local machining quote exists; the verified covered-item cost is about 27-49 delivered in DE.
  - No change to rails, connectors, drivers (Ubuntu 24.04 arm64) or case outline. Hard rules unaffected.
  - Not verified (web-search budget exhausted, fetch only): the ISO 1222 tripod screw length, the exact EU duty amount, the RS nut price, and the TME, Piekarz and metallshopper shipping costs.
- **Sources:**
  - https://www.piekarz.pl/en/thermostats/6
  - https://www.lcsc.com/product-detail/C156512.html
  - https://datasheet.lcsc.com/datasheet/pdf/d10b39980d4644c3b735c1f0516a765d.pdf?productCode=C156512
  - https://datasheet.lcsc.com/datasheet/pdf/90267733683f47b994e67d865bfdf8de.pdf?productCode=C156501
  - https://alu-verkauf.de/products/aluminium-platten (Shopify product JSON, variants dated 13-18 Oct 2026)
  - https://alu-verkauf.de/policies/shipping-policy
  - https://metallshopper.de/Aluminiumblech-2mm
  - https://metallshopper.de/kundendienst/lieferung/
  - https://www.makeitfrom.com/material-properties/5754-AlMg3-3.3535-A95754-Aluminum
  - https://en.wikipedia.org/wiki/5754_aluminium_alloy
  - https://www.aalco.co.uk/datasheets/Aluminium-Alloy-5754-H111-Sheet-and-Plate_148.ashx (served a T6/T651 plate sheet, 180 W/mK)
  - https://docs.rs-online.com/3200/A700000015669212.pdf (RS PRO 1050A, 222 W/mK)
  - https://www.tme.eu/en/details/fr4100x160_3535/two-layer-laminates/bungard/120306z33/
  - https://www.bungard.de/de/produkte-verbrauch/verbrauchsmaterial/fotobeschichtetes-basismaterial
  - https://www.electrokit.com/en/kopparlaminat-dubbelsidigt-fr4-1.6mm-35/35u-233x160
  - https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment
  - https://de.rs-online.com/web/p/sechskantmuttern/2450741 (403, unverified)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/power.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/final_integration.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (item 34)
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md lines 134, 247, 275, 841, 896, 950

