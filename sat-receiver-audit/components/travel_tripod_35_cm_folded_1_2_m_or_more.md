# Travel tripod 35 cm folded 1 2 m or more: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_37583a7b-1a8`_

- **Part:** Travel tripod for the folding antenna kit (Supports, qty 1): 35 cm or less folded, 1.2 m or more, ball head with pan lock or pan-tilt, 1/4-20. It carries the horn plus LNB, the helicone, the V-dipole at 1.087 m and the L-band patch.
- **Current pick:** Rollei Compact Traveler No. 1 Aluminium, black, SKU 22585, EAN 4048805225859, from rollei.de (the maker's own store, Rollei GmbH & Co. KG, Norderstedt DE). The 2026 version comes with a 2026 ball head and plate.
- **Current price usd:** 57.33 = EUR 50.95 incl. 19% DE VAT (rollei.de Shopify data fetched 18 Oct 2026; compare-at price EUR 99.00; black variant available=true). Without VAT: EUR 42.82 = USD 48.18. Landed DE/AT: EUR 56.93 = USD 64.06 (EUR 5.98 shipping, free from EUR 100). Landed in the rest of the EU: EUR 63.94 = USD 71.95 (EUR 12.99 shipping, free from EUR 150). Rate 1.1253 USD/EUR. Caveat: the EUR 50.95 is a sale price, and for non-DE destinations the gross price may change with the local VAT rate (OSS). This was not verified.
- **Decision:** keep
- **Chosen:** Keep the Rollei Compact Traveler No. 1 Aluminium, black (SKU 22585), bought from rollei.de at EUR 50.95. No candidate survived adversarial verification as both cheaper and not worse.
- **Chosen price usd:** 57.33 incl. VAT (EUR 50.95); landed 64.06 (DE/AT) or 71.95 (other EU)
- **Saving usd:** 0 (kept). For reference, it is USD 77.65 cheaper than the earlier named alternative, the Manfrotto BeFree One Aluminium at EUR 119.95 (USD 134.98).
- **Equivalence proof:** Baseline, re-verified today from the rollei.de product page, its .json/.js data and the 2026 head and plate pages:
  - Legs: folded 34.5 cm; minimum height 34.5 cm; maximum 145 cm; 'Maximale Arbeitshöhe' 113 cm, which is the column-down height (145 minus 113 matches the column travel).
  - Construction: 5 aluminium sections, 22/19/16/13/10 mm tubes, twist locks, spikes, reverse fold, no split column.
  - Weight and load: 942 g without head, 1.14 kg with head; 8 kg rated load.
  - Monopod mode: 49-151 cm.
  - Head: aluminium, 8.8 cm tall, 40 mm base, 197 g, 8 kg, 3/8 in connection.
  - Plate: Arca-Swiss, 4x4x1 cm, 20 g, 1/4 in camera screw.
  - Box: tripod, hex key, bag, phone holder, manual. No ballast hook and no spirit levels are listed.
  - Support: 24-month exchange warranty, GPSR person named, EU stock. Spares are sold separately: head EUR 35.95, plate EUR 26.95 (SKU 20022), rubber feet.
  - The 2016 datasheet (justmore.dk PDF) describes the older version: 31.5 cm, 134 cm, 1170 g, 5 kg, a 275 g 'pan, lock and tilt' head with 3 levels, and a hook.
  - It meets every stack rule: 34.5 cm is within the 35 cm cap, 145 cm is above 1.2 m, and 34.5 cm is below the 50 cm minimum-height need.
  
  Candidates I tried to break:
  - Every candidate cheaper than USD 57.33 fails a hard spec:
    - Rollei Star S1, EUR 17.95: folds to 38 cm in the table, 40 cm in the text; 2 kg; 125 cm; 20 mm top tube.
    - Rollei Compact Creator Star, EUR 34.99: folds to 50 cm; 2.5 kg; plastic parts.
    - Rollei Mini M-1, EUR 40.95: maximum height 49 cm.
    - Neewer TP53, USD 29.99: folds to 43 cm; 1.5 kg.
    - Neewer TP12, USD 49.99: 51 cm; 5 kg; 1.33 kg; plastic.
  - Every candidate that fits 35 cm or less is more expensive or unverified:
    - Sirui Traveler 5A, USD 89.90 from a US store: 4 kg; 138 cm.
    - Manfrotto Element Traveller Small: no price, 'OutOfStock' at price 0 on manfrotto.com (global and global-uk), and the EU retailers I tried could not be read. Its stated payload is also lower (6 kg against 8 kg) and it has 2 levels against Rollei's 3 (older version).
    - Rollei Carbon No. 1: EUR 117.99.
    - BeFree One: EUR 119.95.
  - So no candidate is both cheaper and not worse. Where the current part is weaker than a pricier rival, I say so (no silent trade-off):
    - Manfrotto: 127.5 cm column-down height against 113 cm, a published -30 to +60 C rating, and a confirmed independent pan lock.
    - Sirui: 33 cm folded against 34.5 cm.
    - Neither is cheaper, so the keep stands. The rule is passive mechanics, so receive-only, no-loop and conducted-only rules are unaffected.
- **Rejected:**
  1.
    - **Name:** Rollei Compact Traveler Star S1 (SKU 20837), EUR 17.95 = USD 20.20
    - **Why:** Fails the folded-length rule: 38 cm in the spec table, 40 cm in the description, against 35 cm. Max load is 2 kg against 8 kg. Max height is 125 cm against 145 cm. It has 4 sections of 11-20 mm, so the top tube is thinner (20 mm against 22 mm). Its video pan-tilt head would be better for az/el, but that does not offset the hard-rule failure. Verified on rollei.de.
  2.
    - **Name:** Rollei Compact Traveler Mini M-1 (SKU 20846), EUR 40.95 = USD 46.08
    - **Why:** Maximum height is 49 cm (17-49 cm), so it cannot reach the 1.087 m V-dipole height or the 1.1-1.3 m horn and helicone heights. Verified on rollei.de.
  3.
    - **Name:** Rollei Compact Creator Star (SKU 26930), EUR 34.99 = USD 39.37
    - **Why:** Folds to 50 cm, rated 2.5 kg, aluminium with plastic parts. Breaks the 35 cm rule and the build is weaker. Verified on rollei.de.
  4.
    - **Name:** Rollei Compact Traveler No. 2 (SKU 23150), EUR 53.95
    - **Why:** Folds to 43.5 cm and weighs 1.48 kg. It is not cheaper, and it is sold out (available=false). Verified on rollei.de.
  5.
    - **Name:** Manfrotto Element Traveller Small with ball head, MKELES5BK-BH
    - **Why:** No real price: the manfrotto.com global and global-uk pages show price 0 and 'OutOfStock', the de/it/fr/es/eu pages redirect to 404, and the EU retailers tried (fotokoch, MediaMarkt, foto-erhardt, Calumet) returned 403, 404 or timed out. Better than the Rollei on paper: 32 cm folded, 127.5 cm column down, -30 to +60 C, confirmed independent pan lock. Worse in stated payload: 6 kg in the overview text only (the spec table gives no max load) against 8 kg. It has 2 spirit levels, and the top attachment is listed only as a 1/4 in screw (no 3/8 in head-swap thread listed). Cannot replace the Rollei without a verified lower EU price, and even then the stated load is lower.
  6.
    - **Name:** SIRUI Traveler 5A, USD 89.90 (store.sirui.com, US)
    - **Why:** More expensive, plus EU duty/UHF/VAT under operator note 35. Max load 4 kg against 8 kg; max height 138 cm against 145 cm. Better only in folded length (33 cm) and weight (1.05 kg). Verified in the store JSON spec table.
  7.
    - **Name:** K&F Concept A305A1+BH-40 (KF09.170), USD 59.99 (US store)
    - **Why:** Folds to 40 cm without the head and 48 cm with it, which breaks the 35 cm rule. Not cheaper once EU duty is added. Its 10 kg load is a maker claim. Verified on kfconcept.com.
  8.
    - **Name:** K&F Concept S204A1 / S205A1 / S174A1 / O234A1, USD 22.99-59.99 (US store)
    - **Why:** Per the search agent's fetch of kfconcept.com (I did not re-fetch each one): they fold to 39-43 cm, which breaks the 35 cm rule. The cheaper three are rated 2-3 kg with 11-17 mm legs.
  9.
    - **Name:** NEEWER TP53, USD 29.99 / NEEWER Basics TP12, USD 49.99 / NEEWER LT07, USD 99.99
    - **Why:** TP53: folds to 43 cm, 1.5 kg load. TP12: 51 cm, 5 kg, 1.33 kg, aluminium plus plastic. LT07: folds to 52 cm and is more expensive. All break the 35 cm rule and all come from a US store (EU duty applies). Verified in neewer.com product JSON.
  10.
    - **Name:** Cullmann NANDO 530TM RB8.5
    - **Why:** Packs to 39 cm, rated 3 kg, weighs 1540 g. The whole NANDO series packs to 39-49 cm. No price on cullmann.de. Verified on cullmann.de.
  11.
    - **Name:** Ulanzi TT53 Traveler-Uka, USD 69.99 / Ulanzi Ombra YING, USD 69.95
    - **Why:** TT53: folds to 43 cm (10x43 cm), ball head rated 3 kg, ABS parts, and more expensive. Ombra YING: more expensive; folded length and load are not published on the store page. Verified on ulanzi.com.
  12.
    - **Name:** ZOMEi Q555, USD 79.99 (zomei.com)
    - **Why:** Folds to 17.5 in = 44.5 cm, weighs 2.9 lb = 1.32 kg, minimum height 22.7 in = 58 cm (the requirement is 50 cm or less). More expensive. Verified on zomei.com.
  13.
    - **Name:** Rollei Compact Traveler No. 1 Carbon (SKU 22578), EUR 117.99
    - **Why:** Not worse (same functions, 8 kg, 961 g), but 2.3 times the price. Verified on rollei.de.
  14.
    - **Name:** Manfrotto BeFree One Aluminium (MKBFR1A4B-BH), EUR 119.95 at bigbearsound.com (Irish EUR store)
    - **Why:** 2.35 times the price; the re-audit gives it 2.5 kg load and 1.35 kg weight. Price verified in the store's .js.
  15.
    - **Name:** Vanguard VEO 3 GO 204AB Gen 2, from USD 139.99
    - **Why:** More expensive (per the search agent; specs not re-verified).
  16.
    - **Name:** Used Rollei Compact Traveler No. 1 (eBay.de / Kleinanzeigen)
    - **Why:** No listing could be read (eBay.de returned 403), so the price is unverified. No 24-month warranty or statutory return from a private seller. A pre-2026 unit is worse in max height (134 cm) and rated load (5 kg) and has the old 1/4 in head mount. Not worse can only be shown after an on-receipt creep test.
  17.
    - **Name:** Flexible mini tripod in the RTL-SDR Blog dipole kit (USD 0 extra)
    - **Why:** Tabletop only: cannot reach 1.087 m, and offers no load or wind stability. It stays as the documented fallback (hand-held horn and helicone).
  18.
    - **Name:** DIY or 3D-printed tripod or pan-tilt head
    - **Why:** No design with measured stiffness, creep or wind data was found. Printed PETG/ASA under a cantilevered load would need its own creep data. Unproven.
- **Conditions or tests:** Acceptance checks inside the 14-day return window. Returns are free from DE/AT; from other EU countries the return costs EUR 15 and outbound shipping is not refunded.
  (1) Measure the folded length with the head and plate fitted. It must be 35.0 cm or less; the listing says 34.5 cm, so the margin is 0.5 cm.
  (2) Confirm that the 2026 head has a panorama lock independent of the ball lock, and a drop notch for 90 deg tilt. The 2026 table does not state this; the 2016 head was 'pan, lock and tilt'.
  (3) Check whether a centre-column ballast hook or hook thread is present. It is not in the 2026 box list. If missing, hang the ballast from a cord loop with a carabiner around the column foot.
  (4) Re-audit creep test: helicone (about 0.4-0.5 kg) and horn plus Bullseye LNB at 30 deg elevation, 1.1-1.3 m, about 20 km/h wind. Allowed creep is 2 deg or less in 10 min.
  (5) V-dipole at 1.087 m with the centre column down (113 cm working height), checked for stability.
  (6) The Arca plate's 1/4-20 screw seats in the enclosure insert and the printed V clamp; the head thread is 3/8-16.
  Reject and return the unit if any leg section slips or (1) or (4) fails.
- **Stack changes:** No changes to rails, connectors, drivers or the electronics case.
  - reaudit_C and the BOM: replace the 2016 datasheet figures with the 2026 listing. Old: 31.5 cm, 134 cm, 1170 g, 5 kg. New:
    - folded 34.5 cm, minimum 34.5 cm, maximum 145 cm, 113 cm column down
    - 1.14 kg with head, 8 kg claimed
    - head 197 g with 3/8 in connection; Arca plate 4x4x1 cm with 1/4 in screw
    - spikes and monopod mode; no hook and no levels in the box list
  - Price: replace 'TBD' with USD 57.33 (EUR 50.95 incl. VAT, sale against an RRP of EUR 99; buy before it moves).
    - DE/AT landed: USD 64.06; free shipping from EUR 100, not EUR 150.
    - Other EU landed: USD 71.95; free from EUR 150.
  - Packing table: tripod 31.5-32 cm becomes 34.5 cm. The backpack's inner length must be 36 cm or more.
  - Kit weight line: 1.14 kg is within 1.2-1.4 kg.
  - Optional: a second Arca plate, EUR 26.95 (rollei.de SKU 20022), so the V clamp and the horn collar each keep a plate fitted. With the tripod that still totals under EUR 100, so DE/AT shipping still applies.
  - Optional later: the 3/8-16 head thread allows a true pan-tilt head.
  - Pointing: the IMU gives level, so the missing spirit levels do not matter; the az/el step is unchanged.
  - Method limits:
    - The shared WebSearch budget was exhausted, so no web searches were run in this step. All checks are direct fetches of maker and store pages.
    - Amazon.de, idealo, eBay.de, fotokoch, MediaMarkt, foto-erhardt and Calumet could not be read, so cheaper EU offers for the same Rollei SKU are unverified.
- **Confidence:** medium
- **Sources:**
  - https://www.rollei.de/products/stativ-compact-traveler-no-1
  - https://www.rollei.de/products/stativ-compact-traveler-no-1.js
  - https://www.rollei.de/products/stativ-compact-traveler-no-1.json
  - https://www.rollei.de/products/kugelkopf-compact-traveler-no1-v2026
  - https://www.rollei.de/products/schnellwechselplatte-fur-compact-traveler-no-1-version-2026-arca-swiss
  - https://www.rollei.de/policies/shipping-policy
  - https://justmore.dk/images/media/ProductsDocs/Rollei-Compact-Traveler-No-I-kamerastativ-sort.pdf
  - https://www.rollei.de/products/compact-traveler-star-s1-20837
  - https://www.rollei.de/products/stativ-compact-traveler-mini-m-1-schwarz-20846
  - https://www.rollei.de/products/stativ-aluminium-stativ-compact-creator-26930.js
  - https://www.rollei.de/products/compact-traveler-no-2-stativ-23150.js
  - https://www.rollei.de/products/carbon-stativ-compact-traveler-no-1.js
  - https://www.manfrotto.com/global-en/element-traveller-tripod-small-with-ball-head-black-mkeles5bk-bh/
  - https://www.manfrotto.com/global-uk/element-traveller-tripod-small-with-ball-head-black-mkeles5bk-bh/
  - https://bigbearsound.com/products/manfrotto-befree-one-aluminium-travel-tripod-with-head-black
  - https://store.sirui.com/products/sirui-traveler-5c-5a-54-3-inches-lightweight-carbon-fiber-aluminum-travel-tripod.json
  - https://www.kfconcept.com/KF09.170_63-aluminum-travel-camera-tripod-arca-ball-head
  - https://www.neewer.com/products/neewer-entry-level-version-tp53-metal-travel-tripod-66607525.json
  - https://www.neewer.com/products/neewer-basics-tp12-aluminum-alloy-travel-tripod-66607053.json
  - https://www.neewer.com/products/neewer-lt07-61-aluminum-travel-tripod-with-ball-head-66604165.json
  - https://www.cullmann.de/products/nando/nando-530tm-rb8-5/
  - https://www.ulanzi.com/products/tt53-traveler-uka-tripod-t093gbb1
  - https://www.ulanzi.com/products/ombra-ying-travel-tripod-3029.json
  - https://www.zomei.com/products/travel-tripod-q555black

