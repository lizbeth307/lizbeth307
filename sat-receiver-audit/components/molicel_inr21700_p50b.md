# Molicel inr21700 p50b: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** Molicel INR21700-P50B Li-ion cell for the 4S1P pack (Power group, core tier, qty 5 = 4 + 1 spare)
- **Current pick:** Molicel INR21700-P50B from 18650 Battery Store (US). Checked 18 Oct 2026 through the store's Shopify JSON: $9.99 (list price $11.99), available. The store ships UN3480 cells by ground inside the US only, so a buyer in Europe cannot order from it.
- **Current price usd:** 49.95 for 5 ($9.99 each)
- **Decision:** replace_conditionally
- **Chosen:** The same cell, Molicel INR21700-P50B (Grade A listing, flat top, unprotected), bought from NKON in the Netherlands: https://www.nkon.nl/en/molicel-inr21700-p50b-5000mah-50a.html. Live page read 18 Oct 2026: 'In stock', EUR 6.75 incl. Dutch 21% VAT (EUR 5.58 ex VAT); 10+ cells EUR 5.92 each; EAN 6097326477405. Order with 'Optional solder tags: None', because the pack is spot-welded and tags are made to order with up to 2 weeks' extra delay. Fallback if NKON fails at checkout: akkuteile.de, EUR 8.90 incl. 19% German VAT, in stock (JSON-LD read 18 Oct 2026), shipping EUR 5.90 in Germany or EUR 13.90 international.
- **Chosen price usd:** 37.94 for 5 (EUR 33.75 incl. Dutch VAT at the stack's rate of 1.1241 USD/EUR; $7.59 each). Shipping is extra and only shown in the cart. NKON gives EUR 3-50 as the range, post parcels limited to 2 kg; not verified. If destination VAT is charged instead, the 5 cells cost $36.68-39.82 (17-27% VAT; not verified).
- **Saving usd:** 12.01 before shipping (49.95 - 37.94), about 24%. It is at least $10.13 even at the highest EU VAT rate (27%). The saving survives NKON shipping up to EUR 10.69. Against the cheapest seller that actually ships to an EU buyer (akkuteile.de: 5 x EUR 8.90 = $50.02 plus EUR 5.90-13.90 shipping), NKON saves about $12 plus the difference in shipping.
- **Equivalence proof:** It is the same manufacturer part number (Molicel INR21700-P50B), and NKON's Documents tab carries the Molicel datasheet. Every spec the stack depends on is therefore identical by construction. Values from Molicel PDS v1.1 (fsaeonline copy):
  - Capacity 5000 mAh / 18.0 Wh typical, 4850 mAh / 17.5 Wh minimum.
  - 3.6 V nominal, 4.2 V charge, 2.5 V discharge cut-off.
  - AC impedance 6.5 mOhm (30% SoC), DC 12.8 mOhm (50% SoC). So the 4.63 A sag, the 13.2 V cut-off timing and the cold runtime model are unchanged.
  - 60 A continuous (80 C cut-off).
  - Standard charge 5.0 A, maximum 25 A, so the IP2368's 3 A is 0.6x standard across the whole 0-45 C NTC window.
  - Ambient range: charge -20 to 60 C, discharge -40 to 60 C.
  - 21.55 x 70.15 mm max, so the 2x2 pack stays 43.1 x 21.55 x 140.3 mm inside 46x25x150. 71 g max, so the 284 g mass model holds.
  - Steel can, flat top, spot-weldable.
  - Cycle life per molicel.com: 700 to 1400 cycles at +1C / -100 W.
  
  NKON's own spec table is inconsistent (50 A in the title vs 60 A in the text, 68/70 g, 21.7/21.4 mm), so the Molicel datasheet governs. The NKON Grade B SKU is gone: its URL returns 404 today, so the remaining listing is the Grade A one.
  
  Legitimacy: NKON is a long-established Dutch cell retailer with an EU/VAT storefront and an MSDS on the page. That it is an authorised Molicel distributor is NOT confirmed; molicel.com has no where-to-buy page (404).
  
  Conditions for the replacement:
  (1) At checkout, the item must be the Grade A P50B (not 'grade B / lower cycle life') with no solder tags, and cells plus shipping plus destination VAT must total less than the akkuteile alternative.
  (2) Goods-in on all 5 cells, unchanged from the stack: at least 4.85 Ah at 1 A to 2.5 V, mass 68-71 g, 1 kHz AC IR near 6.5 mOhm. Also check the wrap and date code. A counterfeit or relabel shows up as low capacity, high IR or low mass, so it fails here.
  (3) Recommended addition (my suggestion, not a stack change): pick the best-matched 4 of the 5 for the 4S1P pack. The Daly balances only 30 mA, and only at 4.18 V or above. Suggested limits: capacity spread 2% or less, AC IR spread 1 mOhm or less.
- **Rejected:**
  1.
    - **Name:** Ampace INR21700-JP50 (JP50P1), NKON EUR 3.95 = $4.44 each, $22.20 for 5
    - **Why:** Worse in specs that matter, per Ampace datasheet PS-GC-JP50P1-01 Rev A, read myself.
  (1) Standard charge 2.5 A (0.5C) vs P50B 5.0 A, so the stack's 3 A charge is above JP50's rated standard.
  (2) The datasheet's temperature charge table allows only 2.5 A CC at 0-10 C, so the IP2368 at 3 A across the 0-45 C window breaks the cell spec. Fixing it means a lower RISET (slower charge) or a 10 C lower NTC limit (narrower window): a spec trade.
  (3) Discharge surface range -20 to 80 C vs P50B ambient -40 to 60 C: worse at the cold end for a handheld used outdoors.
  (4) Mass 72.0 g max vs 71 g.
  (5) The '*' specs (capacity, impedance, cycle life) apply only to unused cells within 30 days of manufacture.
  (6) Live NKON page: pre-order only, estimated ship date 30 Oct 2026.
  (7) No independent bench data found. Earlier searches found none; my WebSearch budget was exhausted before I could search again.
  Better only in minimum capacity (4900 mAh) and AC IR (4 mOhm max).
  2.
    - **Name:** BAK INR21700-50D2, NKON EUR 3.85 = $4.33 each, $21.64 for 5, in stock
    - **Why:** Worse, per BAK datasheet P/PR03/PB-D-INR2170-50D2-ZZ A/00 (first edition 20 Mar 2026), read myself.
  (1) Standard charge 2475 mA vs 5.0 A; the stack's 3 A is above it.
  (2) Charge window 0-45 C vs -20 to 60 C. It equals the stack's NTC window with zero margin, and the datasheet says current limits by temperature are 'defined by BAK' (not published), so 3 A at 0-10 C is unconfirmed.
  (3) Discharge down to -20 C vs -40 C.
  (4) Height 70.75 +/- 0.25 mm vs 70.15 max: the 2-cell row grows to 141.5 mm, shrinking the 9.7 mm end gap where the BMS may sit.
  (5) A brand-new model with no field record and no independent tests.
  Better only in minimum capacity (4950 mAh), AC IR (5 mOhm max) and mass (69 g max).
  3.
    - **Name:** Molicel INR21700-M65A (operator note #24), NKON EUR 9.75 = $10.96 each
    - **Why:** Not cheaper than NKON's P50B (EUR 6.75), and live NKON shows it out of stock. It is also worse in mass (74.5 g vs 71 g) and continuous current (26 A vs 60 A). Its full datasheet (charge window, cold data) is gated behind a contact form. Its extra capacity is a separate upgrade question, not a cheaper not-worse analog.
  4.
    - **Name:** Molicel P50B 'grade B / reduced cycle life', NKON EUR 4.95 (earlier snapshot)
    - **Why:** By NKON's own text, the manufacturer graded these as reduced quality with fast fade after about 500 cycles, so cycle life is worse. The listing URL returns 404 today, so it is not available.
  5.
    - **Name:** Molicel P50B at akkuteile.de, EUR 8.90 = $10.00 each, $50.02 for 5
    - **Why:** Same cell, so the specs are equal, and it is in stock (verified). But it costs more than NKON, shipping is EUR 5.90 in Germany or EUR 13.90 international, and the page has a '4500mAh' typo. Kept only as the fallback seller.
  6.
    - **Name:** Molicel/NPE P50B at Liion Wholesale (US), $8.99 each
    - **Why:** The price comes from a search snippet only (product page 403). It is a US ground-only seller, so it cannot ship to the European buyer.
  7.
    - **Name:** EVE INR21700-50PL
    - **Why:** EVE datasheet: 4800 mAh minimum, below the 4.85 Ah goods-in rule. Also 72 g max, standard charge 2.5 A (below the stack's 3 A), charge 0-45 C, discharge to -20 C, and no cycle life in the datasheet. NKON lists Grade B or a 'new version' only, after an earlier batch had a voltage-drop issue.
  8.
    - **Name:** EVE INR21700-50E
    - **Why:** AC IR up to 18 mOhm (about 2.5x the P50B), so more sag at 4.63 A and an earlier 13.2 V cut-off. It is rated 10-15 A, with a 1 A standard charge (the stack's 3 A is 3x that, so cycle life suffers) and charging only at 0-45 C. The only measurements come from a lab affiliated with the seller.
  9.
    - **Name:** Samsung INR21700-50S
    - **Why:** 4800 mAh minimum (fails goods-in), about 72 g, 25 A rated, and runs hot in Mooch's test (higher IR); the Samsung figures come from the search agent, not checked by me. Heavily counterfeited.
  10.
    - **Name:** Tenpower INR21700-60XG and 50XG
    - **Why:** 76 g and 75 g, worse in mass. The 60XG datasheet is a v0.1 draft that contradicts itself and lists no certifications. The 50XG specs are unverified. Both are pre-order.
  11.
    - **Name:** Used or second-life pulls, rewraps (Keeppower, Vapcell P50)
    - **Why:** For used cells, remaining cycle and calendar life cannot be proven equal. No rewrap was found cheaper than a genuine P50B, and the HKJ-tested Vapcell P50 is about 15 A with about 15 mOhm AC, so it is worse.
- **Confidence:** high
- **Conditions or tests:** Before payment:
  - The NKON cart shows the Grade A 'Molicel INR21700-P50B 5000mAh - 50A' listing (not grade B), 'solder tags: None', and the destination VAT and shipping.
  - Cells plus shipping must total less than akkuteile.de (5 x EUR 8.90 plus EUR 5.90 in Germany or EUR 13.90 international). Otherwise buy from akkuteile.
  - NKON's banner warns that shipping can take a few days because of a backlog, so order in week 1 as the plan says. Cells travel by ground within the EU.
  
  Goods-in, all 5 cells:
  - Capacity at least 4.85 Ah (1 A to 2.5 V) and mass 68-71 g.
  - 1 kHz AC IR near 6.5 mOhm (reject outliers).
  - Intact wrap and readable date code.
  - Pick the 4 best-matched cells for the 4S1P pack (suggested: capacity spread 2% or less, AC IR spread 1 mOhm or less); the 5th is the spare.
  
  Unverified:
  - NKON's shipping cost.
  - Destination VAT under OSS.
  - Whether NKON is an authorised Molicel distributor.
  - I read NKON through the r.jina.ai reader (direct requests return 403) before learning that the shared WebSearch budget was exhausted. No further searching was possible, so independent bench data for JP50 and 50D2 was not looked for again.
- **Stack changes:** Only the seller and price change. No change to the cell, BMS (Daly DL-J05G 4S 15 A thresholds), IP2368 settings (RVSET 5.1k, RISET 15k, 3 A, NTC 0-45 C), rails, fuses, connectors, drivers, CAD (46x25x150 mm pack, 54x33x158 mm compartment), the 284 g mass model, the runtime and cold models, or the safety rules (never flown, barrier and vent, about 50% SoC storage, spot-weld only).
  
  Edits needed:
  - STACK.md BOM row 245 ('Елементи'): seller becomes NKON (NL), EUR 6.75 incl. NL VAT = $7.59 each, $37.94 for 5 plus shipping (verified live 18 Oct 2026; shipping and destination VAT not verified). Fallback: akkuteile.de EUR 8.90 (verified). The 18650 Battery Store $9.99 price stays as a US reference only. Note 'solder tags: None' and 'Grade A, not grade B'.
  - Goods-in note: add the matching rule above.
  - Purchase timeline row 6 (line 1123): '5x P50B from a verified seller in your country' becomes '5x P50B NKON (fallback akkuteile.de)'.
  - Core total: minus $12.01 before shipping.
- **Sources:**
  - https://www.nkon.nl/en/molicel-inr21700-p50b-5000mah-50a.html
  - https://www.nkon.nl/en/ordering-and-shipping
  - https://www.fsaeonline.com/content/Molicel-TDS--INR-21700-P50B-80122.pdf
  - https://www.molicel.com/inr-21700-p50b/
  - https://www.18650batterystore.com/products/molicel-21700-p50b-5000mah-50a-battery
  - https://akkuteile.de/en/lithium-ionen-battery/size-21700/molicel/molicel-inr21700-p50b-5000mah-60a-3-6-3-7v-li-ion-battery_100638_3507
  - https://www.nkon.nl/en/ampace-inr21700-jp50-5000mah-60a.html
  - https://cdn.shopify.com/s/files/1/0481/9678/0183/files/01_PS-GC-JP50P1-Specification_202507_sent.pdf?v=1766497427
  - https://www.nkon.nl/en/bak-inr21700-50d2-5000mah-60a.html
  - https://www.nkon.nl/en/amfile/file/download/file/1946/product/6119/
  - https://www.nkon.nl/en/molicel-inr21700-m65a-6500mah-26a.html
  - https://www.nkon.nl/en/molicel-inr21700-p50b-5000mah-50a-grade-b.html
  - https://eurolamp.ua/shop/wp-content/uploads/eve-inr21700-50pl-datasheet.pdf
  - https://www.18650batterystore.com/products/eve-50e-21700-5000mah-15a-battery
  - https://forum.esk8.news/t/mooch-s-bench-test-results-samsung-50s-25a-5000mah-21700-a-great-performer-but-ran-a-little-hot/56544

