# Pack sundries nickel fish paper kapton j: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** Battery pack sundries set: pure nickel 0.15x8 mm, 21700 fish-paper rings, Kapton, JST-XH 5-pin balance lead, Amass XT30 service lead to DC5525, spot-weld service, 1 mm FR-4/mica barrier, 3 mm closed-cell foam plus reflective layer, fire bag. Used for the 4S1P Molicel P50B pack (2x2, 4.63 A peak, 7.5 A fuse, compartment about 54x33x158 mm). Tier core, qty 1 set.
- **Current pick:** The sundries set as specified in STACK.md line 258 and the final_integration Battery row. It is a spec with a model price, not specific products, and it was never itemised.
- **Current price usd:** 50-110 (model estimate, never verified)
- **Decision:** keep
- **Chosen:** KEEP the set as specified. No candidate is both cheaper than the spec and proven not worse. Fill the set with these verified EU line items, each with an acceptance test.
  
  (1) Nickel: LaskaKit LA123130 "Čistý Nikl" (pure nickel), 8x0.15 mm, 10 m, 378 CZK, 9 in stock.
  (2) Rings: LaskaKit LA123144C, 21700 self-adhesive insulating paper, 0.2 mm, 72 pcs, 28 CZK.
  (3) Polyimide tape: CELLCON PA-R376 (reichelt PMB 8-33), EUR 16.95.
  (4) Balance lead: genuine JST XHP-5 housing plus SXH-001T-P0.6 phosphor-bronze contacts (TME), self-crimped, 22 AWG silicone wire. Not reichelt's BXH (brass).
  (5) XT30 service lead: genuine Amass XT30U-M on the lead, added to the Amass XT30 order the stack already has in the protection line. BerryBase A-XT30 female (EUR 0.48) is the verified EU source for a female or spare.
  (6) Barrier: Solder Peak LAM100X160E1, 1.0 mm FR-4, 100x160 mm (TME, MOQ 5). Etch the copper face off, or face it away from the cells and cover it with the same polyimide.
  (7) Reflective layer: tesa 56223 aluminium tape, 50 mm x 10 m (reichelt), EUR 8.95.
  (8) Fire bag: flat 23x30 cm bag, either Jamara LiPo Guard XL 141430 (reichelt, EUR 10.50, same cart) or Robbe 90340069 (Lindinger, EUR 6.49 plus its own shipping).
  (9) Spot welding and 3 mm closed-cell foam: keep the current path (battery-shop weld). No verified analog was found for either.
- **Chosen price usd:** Verified goods, delivered to DE: about $82-86.
  - LaskaKit (nickel + rings): 406 CZK = $18.78, plus GLS to DE EUR 5.67 = $6.38, so $25.16.
  - reichelt (CELLCON + tesa + Jamara): EUR 36.40, plus shipping from EUR 5.95, so $47.66.
  - TME (5 FR-4 sheets, 2 XHP-5, 10 SXH): about $7.6-10.6 from the page's structured data (net or gross not stated), about $9-13 with VAT.
  Not verified: weld service $20-40 (estimate), foam $5-15 (estimate), TME shipping, XT30U-M about $1, DC5525 plug and 18 AWG wire.
  Realistic total: about $110-150 (model). Add $30.37 (Robbe JST-XH crimp pliers, Lindinger, EUR 26.99) if no XH crimper is at hand.
  FX: ECB 16 Oct 2026, 1 EUR = 1.1253 USD = 24.323 CZK.
- **Saving usd:** 0. No saving is proven. The verified goods alone (about $82-86) already exceed the estimate's low end. With the unverified weld service, foam and shipping, the realistic set cost is about $110-150 (model), so the $50-110 BOM figure is too low and should be raised. Possible stack-level saving: the polyimide roll ($19.07) and the tesa roll ($10.07) also serve other stack lines (Q6A mid-plate and NTC taping; aluminium tape for the QO-100 horn seams, STACK line 937), so charge each roll once.
- **Equivalence proof:** Each item was checked against the spec that matters for this pack; pages fetched 18 Oct 2026.
  
  - **Nickel (LaskaKit LA123130):** same 0.15x8 mm (1.2 mm2), listed as pure nickel.
    - Density check against the same seller's plated-steel strip (spec "Poniklovaná ocel"): pure listing 0.105 kg / 10 m, plated listing 0.094 kg.
    - Expected for 12 cm3: 106.8 g for Ni (8.90 g/cm3) and 94.2 g for steel (7.85 g/cm3). The weights fit, but this is an inference, not proof.
    - Equal only after the goods-in test: 1.00 A through 100 mm, measured at 20-25 C. Pass is 7-8 mV (Ni201/Ni200 textbook resistivity 8.5/9.5 uOhm.cm). Reject at 11.5 mV or more (steel). A magnet cannot tell them apart.
  - **Rings (LaskaKit LA123144C):** 21700 size, 0.2 mm insulating paper, adhesive. That matches the spec thickness. Paper type, inner/outer diameter and temperature rating are not published, so fit is checked on a P50B: the ring must cover the shoulder and leave the + cap weld area clear.
  - **Polyimide (CELLCON PA-R376):** 0.050 mm polyimide film, silicone adhesive, -73 to +260 C (315 C short), UL E175868. Meets the polyimide spec of 25-50 um film, 260 C and silicone adhesive. Breakdown voltage is not stated; any polyimide film has far more than the 16.8 V needed.
  - **JST lead:** XHP-5 is genuine JST, 250 V / 3 A, 10 mOhm, -25 to +85 C (reichelt).
    - The JST XH datasheet hosted by reichelt (JST_XH_DB_EN.pdf) lists the standard contacts SXH-001T-P0.6 as "phosphor bronze, tin-plated" and says "contact JST if you require ... contacts made of brass".
    - So reichelt's BXH-001T-P0.6 is the brass variant (B prefix; the JST XH series page lists only SXH). It is not shown equal; use SXH. The JST series page gives 3 A at AWG 22.
  - **XT30:** BerryBase A-XT30 is listed as Changzhou Amass: 15 A, 500 V, -20 to 120 C, gold-flash brass, PA UL94 V-0, 1000 cycles. Identical to the STACK "original Amass" rule. On arrival, check for the AMASS moulding.
  - **Barrier (LAM100X160E1):** FR-4 glass-epoxy, 1.0 mm, 160 mm long, so it covers the 158 mm compartment in one piece. Matches STACK's "FR-4 or mica".
    - Two faults: one 35 um Cu face (conductive), and UL94 is not stated on the TME page or the Solder Peak family page.
    - Fixes: etch the copper (or cover it with the polyimide and face it away from the cells), and flame-test an offcut (it must self-extinguish within about 10 s of removing the flame).
  - **Reflective layer (tesa 56223):** aluminium foil, -40 to +140 C, which beats the 100 C minimum. Bare Al foil reflects at least as well as aluminised film (general property; no emissivity is published). It is conductive, so it goes on the outer face of the foam only, never against the nickel or BMS.
  - **Fire bag (Robbe 23x30 / Jamara XL 30x23):** same class as any LiPo bag. No bag has a published containment test. Robbe states it does not stop smoke and resists heat only briefly.
    - Fit (model): the case is about 210x135x52 mm, so its girth is 2x(135+52) = 374 mm against about 460 mm of bag girth, and its length is about 236 mm against 300 mm. The device plausibly fits; check before relying on it.
  - **Weld and foam:** unchanged.
  
  No item touches the rails, drivers, interfaces or the RF hard rules.
- **Rejected:**
  1.
    - **Name:** LaskaKit 'Propojovací pásek 8x0,15mm 10m' (118 CZK)
    - **Why:** Seller spec says 'Poniklovaná ocel' (nickel-plated steel), listed weight 0.094 kg (steel density), and a reviewer disputes the 'nickel' label. About 1.5-1.7x the resistance of pure Ni (textbook) and cut edges rust. Worse.
  2.
    - **Name:** Botland NSZ-09462 welding tape 0.12x8 mm, 10 m (EUR 7.99)
    - **Why:** 20% less cross-section than 0.15x8 mm, and the material is not stated. Worse.
  3.
    - **Name:** Generic marketplace 'pure nickel' 0.15x8 / Hilumin-type plated steel
    - **Why:** Marketplace rolls: no listing could be fetched and none is measured, so at best conditional on the 4-wire test, and not cheaper than the verified LaskaKit roll. Plated steel (Hilumin type) has higher resistance and corrodes. Rejected.
  4.
    - **Name:** LaskaKit house 'Kaptonová páska' 5/10/50 mm (48-248 CZK)
    - **Why:** 180 C continuous vs 260 C for CELLCON, and the film material is not stated. Lower temperature rating, so worse under the rule.
  5.
    - **Name:** Thermal Grizzly TG-KIS-10-60-50 Kapton sheet (reichelt, EUR 4.90)
    - **Why:** 40 um total thickness vs a 50 um film plus adhesive (thinner, so less abrasion and puncture margin where the nickel crosses the can shoulder). reichelt calls it 'polyamide film'. Only 50 strips of 10x60 mm, so it cannot do a cell wrap or the Q6A mid-plate. Worse.
  6.
    - **Name:** iFixit polyimide tape 12.7 mm x 33 m (reichelt, EUR 11.99)
    - **Why:** No film thickness, adhesive or temperature rating published. Not proven equal.
  7.
    - **Name:** Generic marketplace Kapton
    - **Why:** No material or thickness data; PET is often sold as polyimide. Not proven.
  8.
    - **Name:** reichelt JST XH crimp contact BXH-001T-P0.6 (EUR 0.08)
    - **Why:** Brass variant. Per the JST XH datasheet, the standard contacts are SXH phosphor bronze and brass is special-order. Brass has a lower spring and contact-force retention, so it is not shown equal. Use SXH-001T-P0.6. Housing XHP-5 from reichelt is fine.
  9.
    - **Name:** LaskaKit JST-XH-5 20 cm lead (10 CZK)
    - **Why:** 26 AWG vs 22 AWG target, PVC per user comment, housing and contact origin unknown. Worse.
  10.
    - **Name:** Robbe #46175 XH 4S 22 AWG lead (Lindinger, EUR 2.99)
    - **Why:** Out of stock on 18 Oct 2026; JST provenance of the housing and contacts not stated.
  11.
    - **Name:** Clone 'XH2.54' housings/leads
    - **Why:** No contact-resistance or retention data; genuine JST costs cents, so nothing to save.
  12.
    - **Name:** MULDENTAL XT-30 81217/81218 (EUR 0.80) and KLS XT30U clones at TME
    - **Why:** Not Amass (fails the STACK authenticity rule), no ratings published.
  13.
    - **Name:** Amass XT30U-M at TME
    - **Why:** Genuine, but inventory 0 / OutOfStock on 18 Oct 2026.
  14.
    - **Name:** Pimoroni Amass XT30 (UK, GBP 0.58)
    - **Why:** Genuine, but a UK seller: EUR 3 duty per tariff line + EUR 2 UHF + import VAT + shipping (operator notes 34-35), so landed cost is far above an EU or bundled unit.
  15.
    - **Name:** 18650 Battery Store 21700 black insulator rings ($1.49/20)
    - **Why:** US seller (duty, VAT and shipping). Stated OD is about 18 mm, which may not cover the shoulder of a 21 mm can, and no dielectric or heat data.
  16.
    - **Name:** 18650 Battery Store epoxy insulator sheet 208x175x0.5 mm ($2)
    - **Why:** No FR-4 or UL94 grade. Its stated 55 g implies about 3.0 g/cm3, not FR-4's about 1.85, so the material is unclear. US seller. Not proven flame-retardant.
  17.
    - **Name:** LaskaKit FR4 70x100 double-sided
    - **Why:** Too short for one 158 mm piece, and copper on both faces.
  18.
    - **Name:** 2 mm aluminium mid-plate as the barrier
    - **Why:** Conductive next to nickel, spreads heat to the board side, and melts at about 660 C. Worse than FR-4 or mica.
  19.
    - **Name:** kWeld DIY welder (keenlab, EUR 169-177 ex VAT)
    - **Why:** $226-237 incl. VAT plus a 1500 A source, against $20-40 (estimate) for one shop weld. Not cheaper for one pack.
  20.
    - **Name:** Malectrics prebuilt kit V4 (EUR 96.60)
    - **Why:** Out of stock; needs a car battery or LiPo; no published weld-quality data; dearer than one shop weld.
  21.
    - **Name:** Cheap marketplace capacitor/LiPo spot welders
    - **Why:** No measured weld-energy or consistency data on 0.15 mm Ni.
  22.
    - **Name:** Absima 9000008 bag (170x70x70 mm inside) and Robbe Lipoguard M (155x90x115 mm)
    - **Why:** Cannot hold the whole device for in-device charging. Lipoguard M is also shorter than the 158 mm compartment. Storage-only, so they fail the role.
  23.
    - **Name:** Non-combustible surface only, no bag
    - **Why:** An existing STACK rule alternative with no flame or ejecta containment. Worse, so not an analog.
- **Confidence:** medium
- **Conditions or tests:** 1. Nickel goods-in test.
     - Cut 1 m, pass 1.00 A and read the mV across 100 mm at 20-25 C.
     - Pass is 7-8 mV (pure Ni). Return the roll at 11.5 mV or more (plated steel).
     - Micrometer check: 0.15 +/- 0.01 mm.
     - Optional: a salt-water overnight rust test on a cut edge.
  2. Ring fit: on one P50B, the ring must cover the can shoulder fully and leave the + cap weld area clear. Weld through or next to it only as the shop advises.
  3. JST contacts.
     - Order XHP-5 with SXH-001T-P0.6 only (TME stock display is contradictory: confirm at checkout).
     - Crimp with a proper XH tool and pull-test each crimp.
     - Order: B-, B1, B2, B3, B+. Check each tap voltage with a DMM before plugging into the ISDT 608PD.
  4. XT30: look for the AMASS moulding; reject unmarked parts.
  5. Barrier.
     - Etch the Cu face off (or face it outward and cover it with polyimide).
     - Flame-test an offcut: it must self-extinguish within about 10 s.
     - Mica stays preferred if an EU mica sheet of 1 mm or less is found at the same or lower cost.
  6. Reflective layer: tesa 56223 on the outer face of the foam only; check that nothing conductive can reach the nickel or BMS.
  7. Fire bag.
     - Check that the closed device fits the 23x30 cm bag with the Velcro closed except for a cable exit.
     - If it does not fit, use the bag for storage or transport only and charge on a non-combustible surface (the STACK rule already allows this).
     - The KSD9700 70 C and NTC 45 C limits stay active while in the bag, since the bag traps charger heat.
  8. Shop weld.
     - Cells IR- and capacity-tested before welding.
     - At least 2 spots per joint; peel-test coupons (on scrap nickel or practice cans) first.
     - No soldering to cells.
  9. Foam: choose a 3 mm closed-cell EPDM/PE/neoprene sheet with a stated self-extinguishing rating and a service temperature of 80 C or higher. No listing was verified here.
  
  Evidence limits:
  - WebSearch budget was already exhausted (0 searches made).
  - NKON (403), the JST catalog PDF (403), TinyTronics and Conrad could not be read.
  - Lindinger shipping, TME shipping, weld-service and foam prices are unverified.
  - The LaskaKit price includes CZ 21% VAT; the destination VAT at checkout may differ slightly.
- **Stack changes:** - BOM row (STACK line 258 / final_integration Battery): replace the "50-110 (model)" figure with the itemised list above and re-base it to about $110-150 (model; $82-86 verified goods). Charge the CELLCON polyimide roll and the tesa aluminium roll once across the stack: the same rolls cover the Q6A mid-plate insulation, the NTC/Lime sensor taping and the line 937 horn-seam aluminium tape.
  - Name the nickel as pure Ni with the goods-in mV test (assembly instructions).
  - Name the balance-lead contacts as SXH-001T-P0.6 (not BXH). Add a JST-XH crimp tool to the tools line (line 356) if none is owned (+$30.37, Robbe crimp pliers at Lindinger).
  - Add one XT30U-M (plus a spare) to the existing Amass XT30 order in the protection line, so the service lead needs no separate XT30 order. Also list a DC5525 plug and 18 AWG silicone wire for that lead.
  - Barrier note: 1.0 mm FR-4 with the copper face removed or covered.
  - Fire-bag note: in-device charging needs a bag the closed device fits in (about 210x135x52 mm); otherwise charge on a non-combustible surface.
  - STACK line 258 also lists glass-fibre tape (склострічка) and the 4S wrap. Neither was priced or sourced in this pass: an open gap.
  - No change to rails, connectors at the BMS or pack, drivers, Ubuntu packages, case outline (compartment stays about 54x33x158 mm) or any RF hard rule.
- **Sources:**
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/final_integration.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/final_completeness.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md
  - https://www.laskakit.cz/niklovy-propojovaci-pasek-pro-propojovani-baterii--8x0-15mm-10m/
  - https://www.laskakit.cz/niklovy-propojovaci-pasek-pro-propojovani-baterii--8x0-15mm/
  - https://www.laskakit.cz/samolepici-izolacni-krouzek-21700--arch-72ks/
  - https://www.laskakit.cz/doprava-a-platba/
  - https://www.reichelt.com/de/en/shop/product/polyimide_film_tape_one-sided_8_mm_33_m-152966
  - https://www.reichelt.com/de/en/shop/product/kapton_insulation_sheet-414962
  - https://www.reichelt.com/de/en/shop/product/polyimide_tape_0_5_inch-259148
  - https://www.reichelt.com/de/en/shop/product/jst_socket_housing_1x5-pin_xh-185088
  - https://www.reichelt.com/de/en/shop/product/jst_crimp_contact_socket_xh-185091
  - https://cdn-reichelt.de/documents/datenblatt/C100/JST_XH_DB_EN.pdf
  - https://www.jst-mfg.com/product/detail_e.php?series=277
  - https://www.berrybase.de/amass-xt30-weiblicher-stecker-fuer-dc-stromversorgung-loetanschluss-15a-nennstrom
  - https://www.tme.eu/en/details/xt30u-m/dc-power-connectors/amass/
  - https://www.tme.eu/en/details/lam100x160e1/one-layer-laminates/solder-peak/
  - https://www.tme.eu/html/EN/laminate-fr4-solder-peak/ramka_1892_EN_pelny.html
  - https://www.tme.eu/en/details/polyht-20mm/high-temperature-resistant-tapes/blt/31803-20-tasma-kapton-20/
  - https://www.reichelt.com/de/en/shop/product/tesa_aluminium_tape-65551
  - https://www.reichelt.com/de/en/shop/product/lipo_fire_protection_bag-207644
  - https://www.lindinger.at/en/RC-Electronics/Drive-Set/Batteries/Robbe-Modellsport-Lipo-Bag-protective-case-ROBBE-23x30cm/9787514
  - https://www.reichelt.com/de/en/shop/search/xt30
  - https://www.lindinger.at/en/search?search=xt30&order=price-asc&limit=48
  - https://www.18650batterystore.com/products/21700-insulator-black
  - https://www.18650batterystore.com/products/epoxy-insulator-sheet-208-175-0-5mm-lifepo4-cell-separator
  - https://www.keenlab.de/index.php/shop/
  - https://malectrics.eu/product/diy-arduino-battery-spot-welder-prebuilt-kit-v3/
  - https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml

