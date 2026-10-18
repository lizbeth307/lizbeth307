# Asa 1 kg cnc kitchen m3 inserts and scre: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_37583a7b-1a8`_

- **Part:** Mechanical set (core, qty 1 set): ASA 1 kg + CNC Kitchen inserts and screws + Gelid pads + hand and neck strap
- **Current pick:** This is what final-checks.md (items 30-38) actually sourced, not the loose STACK.md wording:
  - Polymaker ASA Grey 1 kg (PF01003).
  - CNC Kitchen hardware, which is what the $46 line covers: M3x5.7 inserts (EUR 9.40), M2.5x4 inserts (EUR 9.90), 1/4-20x12.7 inserts (EUR 9.90, for the IMU puck only), M2.5x6 TX8 A2 screws (EUR 6.00) and copper M2.5x12 screws (EUR 5.70). Together EUR 40.90 = $45.97.
  - 2x Gelid GP-Extreme 80x40x2.0 mm (TP-GP01-D) from QuietPC NL at EUR 4.98 each.
  - Peak Design Leash ($49.95). It is the only strap priced; no hand strap was priced.
- **Current price usd:** STACK.md says 98-133. Re-priced at EUR 1 = $1.124: 26.99 (ASA Grey, US store) + 45.97 (CNC Kitchen) + 11.20 (2x GP-Extreme 2.0 mm) + 49.95 (Leash) = about $134.1, before shipping. For an EU buyer: Grey is EUR 24.99 incl. 19% DE VAT at 3DJake ($28.09) but is unavailable there (0 in stock, no date). The US store is a regional store, so its $26.99 is not a real EU price.
- **Decision:** replace_conditionally
- **Chosen:** Line by line:
  (1) ASA: REPLACE with Polymaker ASA White 1 kg, same material (PF01002). $25.99 at us.polymaker.com; in the EU, 3DJake.de EUR 24.99 incl. 19% VAT, 16 in stock, delivery 22 Oct.
  (2) Inserts and screws: KEEP CNC Kitchen direct.
  (3) Pads: REPLACE the 2x GP-Extreme 2.0 mm with Gelid GP-Ultimate 1.0 mm, same maker and higher grade:
  - 1x 90x50 (TP-GP04-B), EUR 4.14 at QuietPC NL, 378 in stock;
  - or 120x20 strips (TP-GP04-R-B) at EUR 2.61 each, 25 in stock, if two pad sets are enough.
  Condition: the fit check must give gaps of 0.7-1.0 mm.
  (4) Neck strap: KEEP the Peak Design Leash.
  (5) Hand strap, a line the stack was missing: add SmallRig Hand Strap PAC2456, EUR 12 incl. VAT. It is a new line, not a replacement.
- **Chosen price usd:** Lines that match the current pick: 25.99 (ASA White, US) + 45.97 (CNC Kitchen) + 4.65 (1x GP-Ultimate 1.0 mm 90x50) + 49.95 (Leash) = about $126.6. Using the EU ASA price ($28.09 incl. VAT) it is about $128.7. With 2x 120x20 strips instead of the 90x50 sheet, add $1.22. The set also needs items the stack never priced: CNC Kitchen M3 ISO 14580 A2 TX10 screws ($20.91 for M3x8/10/12, or $28.21 for 4 lengths) and the PAC2456 ($13.49). The full set is therefore about $161-168 before shipping.
- **Saving usd:** About $7.55 on the US basis:
  - ASA: $1.00 (White $25.99 vs Grey $26.99).
  - Pads: $6.55 ($11.20 down to $4.65). With 2x 120x20 strips: $5.33.
  VAT-for-VAT in the EU, the ASA saving is $0 (Grey and White are both EUR 24.99 at 3DJake), but White is in stock and Grey is not; the pad saving is EUR 5.82 ($6.54). Inserts, screws and the neck strap: $0, because no cheaper part survived. The added items (M3 screws, hand strap, steel tripod nut) raise the set total above STACK.md's $98-133. That is a costing gap that existed before this step, not something the analogs caused.
- **Equivalence proof:** ASA White vs Grey:
  - Polymaker publishes one TDS for all colours (wiki, re-read 18 Oct): Tg 98 C, Vicat 105 C, HDT 100 C at 1.8 MPa and 103 C at 0.45 MPa, tensile 43.8 (X-Y) and 32 (Z) MPa, notched Charpy 10.3 (X-Y) and 6.7 (Z) kJ/m2. It gives no colour-specific values and does not say which colour the specimens were.
  - Same 1.75 mm diameter, print profile and UV-stable claim.
  - White reflects more sunlight than light grey, which helps the 14.6-18.4 W solar-load model. It has no carbon-black pigment, so RF transparency for Wi-Fi and GNSS is equal or better.
  - White is already allowed: mechanical_thermal.json says 'Light-grey or white ASA'.
  - The only possible downside is reflection next to the display, and the stack already specifies a 'light bezel'. Not worse on any published spec.
  
  Pads, GP-Ultimate 1.0 mm vs GP-Extreme 2.0 mm, all Gelid official pages:
  - Hardness 60-70 vs 65 Shore OO: the same class. QuietPC's '35 OO' for GP-Extreme contradicts Gelid's own page.
  - Density 3.2 vs 2.8 g/cm3; claimed conductivity 15 vs 12 W/mK. Gelid's FAQ now says it does not use W/mK ratings, so these are claims, not measurements.
  - -60 to 220 C, non-conductive, non-curing, compresses by up to 30%.
  - At 1.0 mm instead of 2.0 mm, thermal resistance is about half.
  - Most important: the current 2.0 mm SKU does not meet the corrected spec. A 2.0 mm pad at 30% compression fills only 1.4-2.0 mm gaps, but the spec asks for Lime 0.5-1.5, LPDDR5 0.5-1 and UFS 1-1.5 mm. A 1.0 mm pad fills 0.7-1.0 mm, which is inside all three ranges.
  - A 20 mm wide strip covers the 26x20 mm Lime window.
  
  Rejected parts: each one fails on a measured value, landed price or missing evidence (see 'rejected'). None of these parts touch the receive-only, conducted-only or no-loop rules.
- **Rejected:**
  1.
    - **Name:** Polymaker ASA Natural (3DJake EUR 24.99)
    - **Why:** Same price as White, so no saving. It is unpigmented and translucent, so it lets sunlight and UV into the case; nothing published shows it handles the sun load. Cannot be shown not-worse.
  2.
    - **Name:** 3DO ASA, plain (not CF/GF)
    - **Why:** In the My Tech Fun spreadsheet (asa-10x.xlsx, re-read) it equals or beats Polymaker on all 7 metrics, e.g. 92 vs 86 C heat and 6.28% vs 6.31% creep. But the price could not be verified: the shop was unreachable and this pass had no WebSearch budget left. It is one spool with no UV test, so it is not a proven saving. Re-check only if a real EU price under EUR 24.99 turns up.
  3.
    - **Name:** ELEGOO ASA Grey (eu.elegoo.com EUR 16.99, Grey in stock, White out)
    - **Why:** The official page (Shopify JSON, re-read) gives no TDS figures; it only claims a diameter of +/-0.02 mm and UV resistance. Retailer figures are worse: HDT 99 vs 103 C at 0.45 MPa, Vicat 102 vs 105 C, tensile 35 vs 43.8 MPa. No independent measurement exists.
  4.
    - **Name:** SUNLU ASA (EUR 18.99, out of stock)
    - **Why:** My Tech Fun measured creep at 10.6% vs 6.3% for Polymaker and warp score 1 (failed) vs 3. Higher creep matters for screw bosses and strap lugs in a hot case. Also no TDS and no stock.
  5.
    - **Name:** Bambu Lab ASA
    - **Why:** TDS HDT 92 vs 100 C at 1.8 MPa. My Tech Fun: layer adhesion 33.55 vs 38.95, warp 1 vs 3. Not cheaper either (EUR 26.99 ex VAT per search B).
  6.
    - **Name:** AzureFilm, Prusament, eSun, Qidi, Flashforge, FormFutura ASA
    - **Why:** Each is measured worse than Polymaker on at least one metric in the My Tech Fun spreadsheet:
  - AzureFilm: impact 18.75 vs 72.5 kJ/m2, layer adhesion 31.05 vs 38.95.
  - Prusament: impact 24.4, creep 6.7%, and an 800 g spool ($32.4/kg).
  - eSun: tensile 59.1 vs 62.2, creep 9.1%.
  - Qidi: tensile 60.8, creep 7.2%.
  - Flashforge: impact 32.3, warp 2.
  - FormFutura: worse on almost every metric.
  7.
    - **Name:** 3DJAKE own-brand ASA light grey
    - **Why:** EUR 24.99, not cheaper, and no measurements.
  8.
    - **Name:** ruthex RX-M3x5.7 inserts, 100 pcs (EUR 8.99, in stock)
    - **Why:** Not worse on spec. CNC Kitchen's own test measured 181 kg pull-out in PLA; it has opposed spiral knurls, takes a 4.0 mm hole per the ruthex manual, and is lead- and cadmium-free brass. But the landed price is higher. ruthex sells no screws, and the CNC Kitchen order is needed anyway for the M2.5 inserts, screws, copper screws and 1/4-20 inserts. A separate ruthex order pays EUR 3.90 shipping in DE (under EUR 22) or EUR 9.90 elsewhere in the EU (under EUR 80), so the net change is -EUR 3.49 to -9.49 against the EUR 0.41 unit saving.
  9.
    - **Name:** CNC Kitchen M3x5.7 resold by Prusa ($10.99) or 3DJake (EUR 11.89)
    - **Why:** Same part, dearer than EUR 9.40 direct.
  10.
    - **Name:** Cheap injection-moulded vertical-knurl inserts and shallow-knurl eBay inserts
    - **Why:** CNC Kitchen test: 39 kg pull-out vs 181 kg, and the eBay insert started to spin in ASA. Also needs a 4.5 mm hole instead of 4.0 mm.
  11.
    - **Name:** Captive M3 hex nuts in printed pockets
    - **Why:** Torque-out 2 vs 3 Nm (from a search summary, unverified), needs access pockets that break the IP54 walls, needs a boss redesign, and saves nothing.
  12.
    - **Name:** Bossard ISO 14580 M3 TX via RS (288-4394)
    - **Why:** Price comes only from a 403 snippet. The A2-70 grade is not confirmed. Free shipping only from EUR 100, and it only gets cheaper above about 47 screws of one length.
  13.
    - **Name:** Generic wholesale or AliExpress '304' M3 screws
    - **Why:** No listing gave a price. ISO 7380 is a different head and does not fit the counterbores. Uncertified '304' could be magnetic 200-series steel near the IMU.
  14.
    - **Name:** Arctic TP-3, Jaden EC360 Silver, generic '12-15 W/mK' pads
    - **Why:** Arctic publishes no W/mK value and its prices are only from secondary sources; the EC360 is estimated at 8 W/mK or less (snippet); the generics have no measurement. None has a verified lower landed price than GP-Ultimate 1.0 mm at EUR 2.61-4.14.
  15.
    - **Name:** SmallRig Camera Neck Strap Lite 2794 (EUR 19 incl. VAT, 1 pc in stock)
    - **Why:** Worse than the Leash, which is the pick: safe load 7 kg (only 4.4-5.2x a 1.35-1.6 kg device) vs 90 kg per Leash anchor (this rating was not re-read this pass); 3/8 in webbing ends; no anchor wear indicator; needs split rings that are not included (and steel ones are ferrous). That is a trade, not a not-worse analog.
  16.
    - **Name:** SmallRig braided shoulder strap 4882 (EUR 24)
    - **Why:** 10 kg static rating, below the Leash, and no quick release.
  17.
    - **Name:** Used Peak Design Leash; AliExpress clone anchor straps
    - **Why:** Used price unverified (eBay 403), anchor wear unknown, fake risk. Clones have no load rating.
- **Confidence:** medium
- **Conditions or tests:** Pads:
  1. Run the fit check in the V1.21 STEP and the cooler/pedestal CAD before ordering. If all three gaps (Lime pedestal, LPDDR5 step, UFS boss) are 0.7-1.0 mm, buy GP-Ultimate 1.0 mm only. If they are not, buy the matching GP-Ultimate 90x50 thicknesses (0.5 mm EUR 3.46, 1.5 mm EUR 6.52); then the pad saving shrinks to about $0.
  2. After assembly, check that the UFS module is still fully seated on its B2B connectors (link up at HS-G4, no lift visible). A thinner pad at the same gap tolerance pushes harder, and the UFS is held only by the B2B clicks.
  3. Keep the existing acceptance gates: the UFS pad A/B test (bench_tests[6]) and the Lime pedestal temperature in modes H/I. No Gelid pad has an independent W/mK measurement, so the stack's '>= 6 W/mK' gate is still met only by the maker's claim.
  
  ASA:
  - Buy the White spool from 3DJake (in stock) or the US store. Do not buy Natural.
  - In the P18 midday sun test, also check that the display is readable in sun with the white bezel and hood. If glare is visible, add matte black paint or flock to the inside of the hood. A grey shell would need the same fix.
  
  Hand strap:
  - PAC2456 is backordered at Syntex until 23 Oct 2026.
  - The CAD needs two strap slots of 12 mm or less.
  - Pull-test it at 3x the device weight together with the strap-lug test (bench_tests[14]).
  - SmallRig's care note says to keep it out of direct sun (PU/EVA facing), so treat it as a wear item and inspect it each season.
  
  Not verified in this pass (the shared WebSearch budget was used up after one attempt):
  - 3DO ASA price;
  - Peak Design EU or used price and the 90 kg anchor rating;
  - Igor's Lab pad data (403);
  - shipping and VAT outside DE for 3DJake and QuietPC (QuietPC NL prices do not state VAT).
- **Stack changes:** 1. CASE line: change 'Light-grey Polymaker ASA (1 kg Grey $26.99)' to 'Light-grey or white Polymaker ASA'. Default buy: White PF01002, EUR 24.99 incl. VAT at 3DJake or $25.99 at the US store. Print profile and heat limits stay the same.
  2. Pads: the sourced SKU (GP-Extreme 2.0 mm, TP-GP01-D) does not fit the corrected 0.5-1.5 mm ranges. Replace it with GP-Ultimate 1.0 mm, ordered in the same QuietPC order as the Noctua NF-A4x10 so there is no extra shipping. If the IP2368-to-case pad from final-checks is kept, keep one 2.0 mm pad for it (EUR 4.98); it is not in the corrected spec.
  3. Missing BOM lines:
  - CNC Kitchen M3 ISO 14580 A2 TX10 screws: EUR 5.80-6.60 per 25, lengths from the CAD; the $46 line covers M2.5 hardware and inserts but no M3 screws. Note that the search-A 'M2.5 missing' flag is wrong: M2.5x4 inserts and M2.5x6 screws are inside the $46.
  - A stainless captured 1/4-20 nut or press-in steel insert for the tripod boss, as the re-audit requires. Unpriced. The brass 1/4-20 insert stays for the IMU puck only.
  - A hand strap: SmallRig PAC2456, EUR 12, which needs two strap slots of 12 mm or less in the rear shell.
  4. Neck strap: no change (Peak Design Leash, anchors through the printed lugs).
  5. No impact on power rails, connectors, drivers or software. All parts are mechanical and neutral to the receive-only, conducted-only and no-loop rules. No carbon-fibre or metallic ASA near the antennas.
- **Sources:**
  - https://us.polymaker.com/products/asa.json (variant prices, fetched 18 Oct 2026)
  - https://www.3djake.de/polymaker/polymaker-asa-weiss (EUR 24.99 incl. 19% VAT, 16 in stock)
  - https://www.3djake.de/polymaker/polymaker-asa-grau (Grey: currently unavailable)
  - https://www.3djake.com/polymaker/polylite-asa-white?sai=5247
  - https://www.3djake.de/versandkosten
  - https://wiki.polymaker.com/polymaker-wiki-pt/produtos-polymaker/mais-sobre-nossos-produtos/documentos/fichas-tecnicas/abs-asa/polymaker-tm-asa (TDS)
  - https://mytechfun.com/download/398/asa-10x.xlsx (local copy re-read: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/angleB_mech/dl_mtf/asa-10x.xlsx)
  - https://eu.elegoo.com/products/asa-filament-1-75mm-colored-1kg (Shopify JSON saved at /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/mech_dl/s_eu.elegoo.com.json)
  - https://ruthex.de/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen (JSON saved at /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/mech_dl/ruthex.json)
  - https://ruthex.de/policies/shipping-policy
  - https://cnckitchen.store/products.json (saved at /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/mech_dl/cnck_all.json)
  - https://cnckitchen.store/policies/shipping-policy (DE free from EUR 15, otherwise EUR 3.90; worldwide EUR 8.90)
  - https://www.cnckitchen.com/blog/threaded-inserts-for-3d-prints-cheap-vs-expensive
  - https://quietpc.co.nl/gel-gp-ult-1-120-20?product=6515
  - https://quietpc.co.nl/gelid-gp-ultimate-pads?product=6120
  - https://www.quietpc.com/gelid-gp-pads?product=5037
  - https://gelidsolutions.com/product/accessories-gp-extreme/
  - https://gelidsolutions.com/product/gp-ultimate-xl-thermal-pad/
  - https://gelidsolutions.com/product/gp-ultimate-thermal-pad/
  - https://www.syntex.tv/smallrig-hand-strap-pac2456
  - https://syntex.tv/smallrig-camera-neck-strap-lite-2794
  - https://www.peakdesign.com/products/leash
  - /home/user/lizbeth307/sat-receiver-audit/final-checks.md (items 30-38: current-pick breakdown)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json (mech_thermal corrected_spec)

