# Pololu d36v50f12 sys12: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** SYS12 12 V buck: Pololu D36V50F12 (#4095). Core tier, Power group, qty 2 (1 spare), bonded to the mid-plate. Feeds J21/Q6A, DISP12 and AUX12. In the with-Lime default it must pass C4 gate (1), the NAVTEX/LF narrowband A/B, and gate (2), 60 min at 4.2 A at 14.0 and 16.4 V in, in the closed case.
- **Current pick:** Pololu D36V50F12 (#4095), bought from Pololu US
- **Current price usd:** 79.90 for 2 (39.95 each; 36.75 each at 5+). Re-checked on pololu.com on 18 Oct 2026: 'Rationed (Active and Preferred)', backorders allowed. Not included: US-to-EU shipping, import VAT, the EUR 3 per-tariff-line duty (Reg. (EU) 2026/382, for IOSS/postal consignments up to EUR 150), the EUR 2 Union handling fee (expected from about 1 Nov 2026) and carrier clearance fees. Estimated landed cost for a German consumer: at least about USD 101, before Pololu's shipping charge and carrier fees.
- **Decision:** keep
- **Chosen:** Keep the Pololu D36V50F12 (#4095) but buy the genuine part from Botland B.Derkacz sp.k. (Bralin, PL), an official Pololu distributor (listed on pololu.com/distributors for Poland, Germany and Czechia). Order on botland.de, botland.store or botland.com.pl; the three share one stock (product id 16387, EAN 5904422344436). It is the same part, so it is not an analog. No cheaper analog survived verification.
- **Chosen price usd:** 29.54 each net (EUR 26.28 ex VAT; live Botland API, 18 Oct 2026, regular price, no promo). 59.08 for 2 net. Gross EUR 31.27 at DE 19% VAT. Consumers pay their own country's VAT (OSS): EUR 30.75 (LU 17%) to EUR 33.38 (HU 27%) each. Shipping: botland.de from EUR 4.99, free above EUR 100. botland.store GLS from EUR 6.50 (zone 1), 7.50 (zone 2) or 10.00 (zone 3). Landed in DE, 2 units incl. VAT and shipping: EUR 67.53 = USD 75.91. FX 1 EUR = 1.124086 USD (open.er-api, 18 Oct 2026). Stock: quantity 10, availability 'high', can_buy true (Botland edge_api stock and products endpoints, 18 Oct 2026, 16:02 CEST).
- **Saving usd:** 20.82 for 2 (26%) like for like, ex VAT and ex shipping (79.90 to 59.08). Landed in DE about USD 25 or more (USD 75.91 vs at least about USD 101.34 for a Pololu US order), plus the Pololu shipping charge and carrier fees avoided. That US figure is a model: goods + 19% VAT + EUR 3 duty + EUR 2 UHF.
- **Equivalence proof:** Same part, same maker and same SKU: Pololu #4095 from an official Pololu distributor. Botland B.Derkacz sp.k. is on pololu.com/distributors for PL (botland.com.pl), DE (botland.de) and CZ (botland.cz). botland.store is the same legal entity at the same address (Gola 25A, 63-640 Bralin, per the schema.org data).
  
  Every spec is identical by definition:
  - 13.3-50 V in; 12 V ±4%.
  - 2.3-6.5 A typical max continuous (4.5 A at 36 V in).
  - About 500 kHz with power-save above 20 kHz.
  - EN sleep 1.2 V / wake 1.35 V, 100 k pull-up.
  - PG +20%/-10%; reverse protection to 40 V; OCP, OTP, output OV/UV, soft-start.
  - 25.4 x 25.4 x 9.5 mm, three 0.086 in holes.
  
  So the 10.0k/1.00k EN divider, PG wiring, plate bonding and both C4 gates stay exactly as specified. (v2.1 owner decision 24.10.2026, E1-04: the EN divider is now 4.99k / 562 Ohm 0.1% 25 ppm/K, wake about 12.77 V and at most 13.27 V, below the UV release; the part itself is unchanged.) Counterfeit risk is minimal (official channel, maker-direct supply).
  
  Adversarial check of the price: the 'not kept in stock / sourced from the manufacturer' text on the Botland page is a hidden template (the hidden attribute is set). The live stock API returns quantity 10, order_mode 'none' and promo_end_ts 0, so this is the regular price, not a sale. The earlier claim of '19% VAT on botland.store' was only partly right: the 26.28 net price is fixed and VAT follows the buyer's country.
  
  One correction to search B: Botland is not B2B-only. Its store regulations say a buyer without a TIN 'is assumed to be buying as a Consumer'.
- **Rejected:**
  1.
    - **Name:** Pololu D36V50F12 from EXP GmbH (exp-tech.de, SKU 80-4095)
    - **Why:** Same genuine part. Price and stock are real: EUR 28.94 ex VAT, labelled 'Sonderpreis', 'Verfügbar (12 Stück)', checked in the Shopify JSON and HTML on 18 Oct 2026. Not chosen for three reasons. (1) EXP's AGB 'schließt den Verkauf an Verbraucher i.S.v. § 13 BGB aus': it sells to businesses only, so a private buyer cannot use it. (2) It is EUR 2.66 per unit dearer than Botland net (USD 65.06 vs 59.08 for 2). (3) UPS shipping is EUR 6.50 (DE) to 20 (ES/GR), EUR 14-15 for AT/PL/IT/CZ. Keep it only as a backup source if the user buys as a business.
  2.
    - **Name:** TI TPSM63606RDLR power module on a custom 4-layer carrier
    - **Why:** Worse on specs that matter here. (1) No reverse-voltage protection: VIN abs min -0.3 V (SLVSGB4B 7.1) vs Pololu's 40 V, so an extra stage is needed. (2) Dropout: TI Table 8-1 recommends 1.7-2.2 MHz for 12 V out (integrated inductor), and tOFF(min) is 65 ns typ / 85 ns max. That gives about 13.5-14.8 V ideal minimum input before frequency foldback, worse than Pololu's 13.3 V. The foldback also moves the spurs at low battery, which defeats the purpose of fixed frequency. (3) Not a finished, tested module: build quality, EMI and thermals (RthJA 33.1 C/W on a 75x75 mm 2 oz board) depend on DIY B3QFN reflow. (4) Total cost is unverified: the TI page showed no price to me, and the USD 15.82 module price comes from the search. With PCB, passives and a reverse-polarity stage it is not shown to be below Botland's USD 29.54 per board. TI stock of 558 is confirmed by the TI inventory API. Better only in FPWM/sync, Iq and the ±1% FB tolerance.
  3.
    - **Name:** TI LMZM33606RLXR power module on a custom carrier
    - **Why:** No reverse protection (VIN abs min -0.3 V). The 16 x 10 x 4 mm QFN needs a custom PCB and reflow, so it is not a tested finished module. Recommended minimum VIN is 1.1 x VOUT, about 13.2 V: equal, not better. FPWM is selectable on SYNC/MODE and EN is 1.14-1.25 V, so the divider must be redone. Price (USD 14.46) not re-verified; total cost unverified. TI stock of 1000 is confirmed. Not shown not-worse or cheaper.
  4.
    - **Name:** TI LM61460AANRJRR discrete buck on a custom PCB (the stack's existing P5 fallback)
    - **Why:** No reverse protection (VIN abs min -0.3 V, SNVSBD5D 7.1). DIY layout and reflow of the VQFN-HR. No independent or 12 V / 4.2 A measurement. AANRJRR is auto mode, so it is FPWM only while a sync clock is present. TI stock of 60,000 is confirmed by the TI API, but DigiKey shows a backorder per the search. The '0.4 V dropout' holds only with clock foldback: with tOFF_MIN 65/85 ns at the 1.8-2.1 MHz sync the stack prefers, it folds back below about 13.6-14.6 V ideal input. Keep it only as the fallback if the D36V50F12 fails C4 (see stack_changes).
  5.
    - **Name:** TI LM61460EVM-FS-400K reworked to 12 V
    - **Why:** Not cheaper: USD 67.38 each vs USD 29.54. Larger than 25x25 mm (terminal blocks, EMI filter). No reverse protection. No 12 V measurement.
  6.
    - **Name:** Pololu D30V30F12 (#4896)
    - **Why:** USD 30.95 at Pololu. Typical max continuous output is 1.5-3.5 A (pololu.com, 18 Oct 2026), which fails the 4.2 A Lime-default gate. Its spread spectrum works against a fixed narrowband spur mask, and the search reports a less precise EN threshold.
  7.
    - **Name:** Pololu D42V55F12 (#5577)
    - **Why:** Not cheaper: USD 47.95 vs 39.95 at Pololu (both Rationed). Specs on pololu.com: 12-60 V in, ±3%, 3.5-6.5 A, about 400 kHz, Iq under 0.2 mA. The search reports a different and less precise EN scheme, so the backup UV divider would have to be redesigned.
  8.
    - **Name:** Generic XL4016 '8A/12A' buck module
    - **Why:** Free-running 180 kHz ±20% (144-216 kHz) with no sync. Its fundamental band covers TDF 162 kHz and its 2nd/3rd harmonics cover NAVTEX 490/518 kHz. Non-synchronous, so efficiency below 92% is likely at 14-16 V in. No PG, no defined EN UVLO, no reverse protection. Large, with a trimpot and heatsink. Counterfeit or remarked ICs are common, and there is no independent measurement. Datasheet figures are from the search, not re-read by me.
  9.
    - **Name:** Generic '7A 9-60V to 3-32V' LT3800 module (HKJ, lygte-info)
    - **Why:** Measured worse; I re-read the review. It needs about 3 V of headroom ('need about 27V to deliver 24V'), so it drops out across most of the 4S window at 12 V out. 200 kHz with 'fairly high' noise. Heatsink 98.7 C at 5.5 A, up to 157 C at 50 V in. No PG or EN UVLO. Much larger.
  10.
    - **Name:** Generic '10A 6.5-60V to 1.25-30V' LT3800 module (HKJ)
    - **Why:** Per the search's reading of HKJ's review: it died in test at 60 V / 2.5 A, had no apparent OTP, its output drifted, and it measured about 90% at 12 V to 5 V. No plate-bonding path, no PG/EN.
  11.
    - **Name:** Generic LM2596 '20W' module
    - **Why:** 3 A class (about 20 W) vs about 50 W needed. Non-synchronous, low efficiency.
  12.
    - **Name:** Generic Mini560 / Mini560 Pro 12 V
    - **Why:** No datasheet or independent measurement found, so it cannot be shown not-worse. The project already rejected Mini560 parts for J21.
  13.
    - **Name:** Used or second-hand D36V50F12
    - **Why:** No listing verified (eBay returned 403). Unknown stress history, no warranty, relabel risk. Any saving under Botland's new EUR 26.28 net would be small.
  14.
    - **Name:** Other EU listings of the same part (TME, The Pi Hut)
    - **Why:** Per search A: TME is USD 37.5-42.5 with conflicting stock (TME returned 403 to me). The Pi Hut is GBP 38.40 incl. VAT and UK-to-EU, so it also carries the EUR 3 duty, the UHF and DHL Express (operator notes 34/35). BerryBase does not list the D36V50F12 (search, 18 Oct 2026). All are dearer than Botland or not available.
- **Confidence:** high
- **Conditions or tests:** No new tests; the part is unchanged. The existing gates still apply to the units as delivered:
  - C4 gate (1): HF+ narrowband A/B with SYS12/LAB5 load steps 0.3-3 A and the charger on/off. No line 3 dB or more above the floor within ±5 kHz of 40, 60, 77.5, 162, 490, 518 or 4209.5 kHz, nor at the 1/7/14 MHz checks.
  - C4 gate (2): 60 min at 4.2 A in the closed case at 14.0 and 16.4 V in, logging D36V50F12, #2813 and fuse temperatures.
  - EN divider sweep: 10.0k/1.00k, targets sleep about 12.1 V and wake about 13.6 V. v2.1: 4.99k/562 Ohm, sweep 14 -> 10.5 -> 14 V at 25 and 50 C on every unit including the spare; accept wake at most 13.30 V and sleep 10.9-12.0 V; above 13.30 V fit R109 576 Ohm (both thresholds drop by about 2.2%) and repeat the sweep; accept only if the re-measured wake is at most 13.30 V and sleep at least 10.9 V, otherwise reject the module (Zh-03).
  
  Goods-in: check the Pololu silkscreen and #4095 marking, and that the output is 12 V ±4% unloaded.
  
  Purchase conditions:
  - Order soon. Botland holds 10 pieces and Pololu upstream is 'Rationed'.
  - Confirm that the cart applies your country's VAT on the EUR 26.28 net price.
  - If Botland stock runs out, the only other verified EU stock is EXP-tech, which sells to businesses only.
  
  Coverage limits:
  - WebSearch was exhausted (shared per-turn limit), so I worked from direct fetches only.
  - Kamami, TME and RobotShop EU returned 403. Electrokit and Gotronic search URLs returned 404.
  - Finished modules from RECOM, Murata, Würth and Mean Well were not searched.
- **Stack changes:** 1. BOM row SYS12 (STACK.md line 248): change the source from Pololu US to Botland (official Pololu distributor, PL warehouse). Price: EUR 26.28 net each (USD 29.54), USD 59.08 for 2 net; DE landed EUR 67.53 incl. 19% VAT and EUR 4.99 shipping. Status: 'verified, 10 in stock, 18 Oct 2026'. Power group total falls by about USD 20.82 net.
  
  2. Shopping order (STACK.md line 1123, week 1): move the 2x D36V50F12 out of the Pololu US order into a Botland order. Also check Botland for the D36V28F5 and 2x #2813 (not verified here). Consolidating would pass the EUR 100 free-shipping threshold on botland.de and avoid the US landed costs in operator note 35 (VAT, EUR 3 per tariff line, EUR 2 UHF, carrier fee).
  
  3. No change to rails, connectors, EN divider (10.0k/1.00k; changed later to 4.99k/562 Ohm by the v2.1 owner decision, E1-04), PG wiring, TPS259470A/J21 chain, plate bonding, case or drivers.
  
  4. Fallback correction, only if the D36V50F12 fails C4. My dropout model: an LM61460 synced at 1.8-2.1 MHz (as in the D re-audit) enters minimum-off-time frequency foldback below about 13.6-14.6 V ideal input (tOFF_MIN 65 ns typ / 85 ns max), plus IR drop. That shrinks the regulated window, and in foldback the frequency leaves the clock, which breaks the spur mask at low battery. So:
     - Cap the sync clock at about 1.0 MHz or less (about 12.8-13.1 V ideal), with the exact value from the harmonic scan, keeping n x f clear of the protected list (1/7/14 MHz included).
     - Size the external inductor for that frequency.
     - Add a reverse-polarity stage (VIN abs min is -0.3 V).
     - Redesign the EN divider for 1.263 V rising with no internal pull-up.
  
  5. Do not adopt the TPSM63606 as the fallback at 12 V out: TI recommends 1.7-2.2 MHz there, which forces the same early dropout.
- **Sources:**
  - https://www.pololu.com/product/4095
  - https://www.pololu.com/distributors
  - https://botland.store/converters-step-down/16387-step-down-voltage-regulator-d36v50f12-12v-45a-pololu-4095-5904422344436.html
  - https://botland.store/edge_api/v1/products?ajax=1&ids=16387
  - https://botland.store/edge_api/v1/stock?ajax=1&ids=16387
  - https://botland.de/edge_api/v1/products?ajax=1&ids=16387
  - https://botland.com.pl/edge_api/v1/products?ajax=1&ids=16387
  - https://botland.store/content/1-delivery
  - https://botland.de/content/1-versand
  - https://botland.store/content/98-statute
  - https://exp-tech.de/products/12v-45a-step-down-voltage-regulator-d36v50f12
  - https://exp-tech.de/products/12v-45a-step-down-voltage-regulator-d36v50f12.js
  - https://exp-tech.de/policies/shipping-policy
  - https://exp-tech.de/policies/terms-of-service
  - https://www.berrybase.de/search?search=D36V50F12
  - https://www.ti.com/lit/ds/symlink/tpsm63606.pdf
  - https://www.ti.com/lit/ds/symlink/lmzm33606.pdf
  - https://www.ti.com/lit/ds/symlink/lm61460.pdf
  - https://www.ti.com/storeservices/cart/opninventory?opn=TPSM63606RDLR
  - https://www.ti.com/storeservices/cart/opninventory?opn=LMZM33606RLXR
  - https://www.ti.com/storeservices/cart/opninventory?opn=LM61460AANRJRR
  - https://www.pololu.com/product/4896
  - https://www.pololu.com/product/5577
  - https://lygte-info.dk/review/Converter%20DC-DC%207A%209-60V%20to%203-32V%20UK.html
  - https://taxation-customs.ec.europa.eu/news_en
  - https://taxation-customs.ec.europa.eu/document/download/053e5b4e-f0be-4f20-9a23-3e3b659a6676_en?filename=Customs%20Guidance%20on%20EUR%203%20customs%20duty.pdf
  - https://open.er-api.com/v6/latest/EUR

