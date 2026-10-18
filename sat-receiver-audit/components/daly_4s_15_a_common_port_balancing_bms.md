# Daly 4s 15 a common port balancing bms: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** BMS, Power group, core tier, qty 1: 4S Li-ion (NMC) common-port balancing BMS between the 4S1P Molicel P50B pack and the 7.5 A blade fuse, INA228 shunt and node N
- **Current pick:** Daly DL-J05G-L4S15ATJ, Li-ion 4S 12V 15A common port with balance (TinyTronics SKU 005102 / DALYBMS4S15A)
- **Current price usd:** 8.99. This is EUR 8.00 incl. 21% NL VAT, or EUR 6.61 = $7.43 ex VAT, at 1 EUR = 1.1241 USD. TinyTronics page re-read 18 Oct 2026: "Only 9 pieces in stock". STACK.md rounds this to 9.00.
- **Decision:** keep
- **Chosen:** Daly DL-J05G-L4S15ATJ (unchanged), TinyTronics SKU 005102
- **Chosen price usd:** 8.99 (EUR 8.00 incl. VAT)
- **Saving usd:** 0.00
- **Equivalence proof:** No replacement, so nothing has to be proven equal. Every cheaper candidate is shown worse below.
  
  CURRENT PART, RE-VERIFIED FROM PRIMARY SOURCES (18 Oct 2026)
  Source: Daly "Product Specification Approval" A0 for DL-J05G-L4S15ATJ (10-page PDF linked from TinyTronics; text extracted with pdftotext). The file name says DL-J04G3, but every page says DL-J05G-L4S15ATJ.
  - Common port: B- and P-.
  - Rated discharge 15 A. Rated charge 8 A. Charge voltage 16.8 V.
  - OVP 4.25 +/-0.05 V, delay 1 +/-0.5 s; release 4.15 +/-0.05 V.
  - UVP 2.7 +/-0.05 V, delay 1 +/-0.5 s; release 3.0 +/-0.05 V.
  - Discharge OCP 40 +/-10 A, 1 s; released by removing the load.
  - Charge OCP 10 +/-2 A, 1 s; released by removing the charger.
  - Short circuit: delay 10-500 us; released by removing the load.
  - Passive balance 30 +/-10 mA, at 4.18 V or more and only while charging.
  - Main-path Ron under 20 mOhm.
  - Self-consumption under 500 uA in operation ("not including module self-consumption"); 0 uA in sleep, which needs no communication, no current and no key signal.
  - Voltage accuracy +/-15 mV.
  - No soft switch. Temperature protection fields are blank ("/").
  - -40 to 85 C.
  - 59 x 34 x 9 mm on the datasheet; TinyTronics lists 61 x 35 x 9 mm and 35 g.
  - Leads: B- and P- in 16 AWG, 100 mm. Sense leads in 24 AWG, 300 mm, PHB2.0 5-pin with buckle.
  - Injection-moulded sealed housing, anodised heat sink, 1-year warranty.
  The TinyTronics page matches: EUR 8.00 incl. VAT, EUR 6.61 ex VAT, 9 in stock.
  
  WHY NO CHEAPER PART SURVIVES
  Each candidate is worse on at least one stack-relevant spec, by its own primary page or the maker's datasheet:
  - LFP thresholds (Daly J13G3 F04S).
  - UVP tolerance below the P50B minimum, plus no balance, Iq or Ron data (BMS4S30A).
  - No balancing at all (QSKJ).
  - Unverifiable, wide-tolerance generics.
  - DIY that is neither cheaper nor equal in build quality.
  
  THE ONLY ON-PAPER NOT-WORSE CANDIDATE HAS NO LISTING
  The Daly J13G3 datasheet A3 (DL-J13G3-TJ family, from TinyTronics) shows that a Li-ion 3-4S, 15 A variant exists in Daly's selection table. Its specs:
  - OVP 4.25 +/-0.05 V, release 4.15 V.
  - UVP 2.7 +/-0.05 V, release 3.0 V.
  - Balance 100 +/-25 mA from 4.125 V.
  - Iq under 400 uA. Ron under 20 mOhm.
  - Rated 15 A discharge and 15 A charge. DOCP 50 +/-10 A, COCP 20 +/-3 A.
  - Short circuit released by removing the load OR inserting the charger.
  - Onboard temperature cut: charge 55 / -20 C, discharge 75 / -40 C.
  - Size 61 x 35 x 9 mm.
  No 4S Li-ion J13G3 is listed at TinyTronics (the full 18-item BMS category was read; only 7S/10S Li-ion and 4S/8S LFP J13G3 are listed) or in Daly's official store (bmsdaly.com products.json; its cheapest Li-ion 4S hardware board is G11-JG-107266 at $14.80). With no verifiable price or availability, it cannot replace the J05G.
- **Rejected:**
  1.
    - **Name:** Daly J13G3 LiFePO4 4S 15/20 A with balance (DL-J13G3-F04S15ATJ / F04S20ATJ), TinyTronics, EUR 7.00 incl. VAT = $7.87
    - **Why:** Wrong chemistry, per Daly's own J13G3 datasheet A3, LFP 4-7S column:
  - OVP 3.65 +/-0.05 V, release 3.55 V. It would cut the NMC pack at about 14.6 V, versus the 16.25-16.57 V IP2368 CV, losing roughly half or more of the usable capacity (model).
  - UVP 2.3 +/-0.05 V. The 2.25 V worst case is below the P50B 2.5 V minimum.
  - Balancing starts at 3.525 V, so it would bleed cells for most of the NMC range.
  Daly's precautions section itself says NMC and LFP boards must not be mixed. Saving of $1.12 is irrelevant.
  2.
    - **Name:** TinyTronics no-brand 'Li-ion/Li-Po Protection circuit (BMS) 4S with Balancing' BMS4S30A, SKU 002133, EUR 5.00 incl. VAT = $5.62 (50+ in stock)
    - **Why:** Re-read 18 Oct 2026.
  Worse:
  - UVP 2.55 +/-0.08 V. The 2.47 V worst case is below the P50B 2.5 V minimum and outside the D1 2.5-2.8 V window.
  Unpublished (the Daly specifies all of them):
  - Balance current and start voltage, release voltages, Iq (drives the 50-105 day standby budget), Ron (sag budget at 4.6 A), discharge and charge OCP (only a 75 +/-5 A short-circuit figure), delays and recovery behaviour.
  Also worse:
  - No brand, datasheet or warranty.
  - Open PCB, versus the moulded, sealed Daly with an insulated heat sink.
  - 56 x 45 x 8 mm: 45 mm is wider than the 33-35 mm bay, so it would need an external mount.
  Fails 'not worse'.
  3.
    - **Name:** QSKJ QS-B405ANL-25A 'Li-ion/Li-Po Protection Circuit (BMS) 4S', TinyTronics SKU 002932, EUR 3.50 incl. VAT = $3.93
    - **Why:** Re-read 18 Oct 2026. The page states balancing 'No' (the chip only protects).
  - That loses the Daly's 30 mA passive balance outright.
  - UVP 2.80 +/-0.08 V can trip at 2.88 V, above the D1 2.8 V upper bound, which costs low-end energy.
  - Iq, Ron, release voltages, port type and size are unpublished.
  Its tighter OVP (+/-0.025 V) and 10k NTC input do not offset the lost balancing. The rule forbids trading a spec away.
  4.
    - **Name:** Daly G/H-series hardware 'Li-ion 4S 12V / 15A NTC' (official store SKU G11-JG-107266)
    - **Why:** $14.80 plus shipping and EU VAT on bmsdaly.com/products.json (read 18 Oct 2026). It adds an NTC cut but costs about 1.6 times as much. Not cheaper.
  5.
    - **Name:** Daly J13G3 Li-ion 4S 15 A (DL-J13G3-L04S15ATJ, implied by the J13G3 datasheet A3 selection table)
    - **Why:** Not rejected on specs: on paper it is equal or better on every stack-relevant spec except looser OCP trips (DOCP 50 vs 40 A, COCP 20 vs 10 A). Those are covered by the 7.5 A blade fuse and the 3 A IP2368.
  Behaviour differences:
  - Balancing starts at 4.125 V without the 'only while charging' condition, so it can bleed 100 mA at rest after a CV at the IP2368 upper tolerance (16.57 V = 4.14 V/cell).
  - It adds a 75 C discharge temperature cut.
  No seller listing, price or stock was found (TinyTronics category and Daly official store both checked), so the price and availability are not real yet. Watch item only.
  6.
    - **Name:** Generic AliExpress/eBay 4S 15-20 A balance boards (HX-4S-A01/A20, HXYP-4S-BM20, CF-4S30A class), about $1-3 (unverified)
    - **Why:** Vendor claims only, inconsistent between listings:
  - OVP 4.25-4.35 V. The upper end exceeds the 4.30 V ceiling.
  - UVP 2.3-3.0 V. The lower end is below the P50B 2.5 V minimum.
  - HX-4S-A01 'working current' 6-8 A, below 15 A.
  No balance-current tolerance, Ron or release-voltage datasheet for an identifiable board. The same title ships different PCBs. Prices were not verified (eBay.de returned 403 to me). Fails 'not worse'.
  7.
    - **Name:** BM3451-based 'universal' 3S/4S/5S 100 A board (Li-ion TNDC variant), about $1.90 (2023 mysku price, not re-checked)
    - **Why:** - Price is stale and unverified.
  - No published Li-ion balance current, Iq or Ron.
  - Large 100 A board.
  - Jumper-selected cell count, and a chemistry variant identified only by IC marking (high risk of receiving the wrong board).
  - Forum reports of no auto-reset after a trip.
  - The compiled Li-ion OVP range of 4.14-4.24 V (unverified) would sit at or below the 4.20 V monthly ISDT balance.
  Fails 'not worse' on documentation alone.
  8.
    - **Name:** DIY TI BQ77915 protector (integrated 50 mA balance) + back-to-back N-FETs on a custom PCB
    - **Why:** TI part page for BQ7791500PWR (18 Oct 2026): out of stock, no price shown. The page lists only threshold ranges (OV 3-4.575 V +/-10 mV, UV 1.2-3 V +/-18 mV), so this variant's factory thresholds are unconfirmed.
  IC + FETs + sense resistor + PCB fab + shipping is not shown to be under $8.99. A hand-built, unencapsulated main safety disconnect is worse in build quality and reliability than the moulded Daly, and it needs a cell-simulator validation campaign.
  9.
    - **Name:** Used or pulled Daly / other 4S BMS (eBay, marketplaces)
    - **Why:** No listing with measured thresholds or trip history was found. Angle B saw new Daly listings on eBay.de from about EUR 10.90 (not re-checked; eBay returned 403 to me), which is above TinyTronics anyway. Unknown FET stress and counterfeit or wrong-chemistry risk on the pack's only cell-level disconnect. Rejected.
- **Conditions or tests:** BENCH TESTS ON THE DALY, ALL STILL REQUIRED (unchanged)
  1. UVP wake by the IP2368 trickle (100-200 mA): 3 of 3 tries.
  2. Short-circuit / DOCP trip release with the AON load (about 1 mA) present. Datasheet: released only by removing the load. If it does not release with the AON present, the documented reset is to pull and re-insert the 7.5 A blade fuse, which removes every load from P-.
  3. OVP point of the actual unit during the monthly 4.20 V ISDT balance. The datasheet's lower OVP edge is 4.20 V, exactly the balance end voltage. If the unit trips below about 4.21 V, use the spare or exchange it.
  4. Quiescent current at 14.8 V, measured against the spec of under 500 uA. The stack budgets 0-0.5 mA.
  5. Charge OCP margin: COCP is 10 +/-2 A and released only by removing the charger, so keep the ISDT 608PD charge current at 3 A or less (rated 8 A).
  
  WATCH CONDITION, NOT A REPLACEMENT
  If TinyTronics or Daly lists a Li-ion 4S J13G3 (DL-J13G3-L04S15ATJ) at no more than EUR 8.00 incl. VAT, re-open this decision. It would need the same bench tests 1-4, plus:
  - confirming that at-rest balancing from 4.125 V does not drain a stored pack, given storage at about 50% SoC;
  - confirming the onboard temperature cut does not trip in the closed, sun-loaded case.
  Deadline: none. It is only a cost and feature upgrade.
- **Stack changes:** No BOM, price, rail, connector, driver or case change.
  
  DOCUMENTATION ADDITIONS FROM THE DATASHEET A0
  - Size: 59 x 34 x 9 mm on the datasheet, 61 x 35 x 9 mm at TinyTronics. Reserve 61 x 35 x 10 mm in the bay or external mount.
  - Leads: B- and P- in 16 AWG, 100 mm. Sense leads in 24 AWG, 300 mm, PHB2.0 5-pin.
  - Delays: OVP, UVP and OCP 1 +/-0.5 s. Short circuit 10-500 us.
  - Release conditions: DOCP and short circuit by removing the load (procedure: pull the 7.5 A fuse). COCP by removing the charger.
  - Iq under 500 uA "excluding module self-consumption". The 0 uA sleep is unreachable while the AON load sits on node N.
  - No temperature protection (the IP2368 NTC covers the 0-45 C charge window). No soft switch.
  - Voltage accuracy +/-15 mV. 1-year warranty.
  - Wiring order: B- first, then sense from B0 up. On removal, sense plug first.
  - The anodised heat sink must not touch cells or nickel.
  
  PROCUREMENT
  Optionally buy 2 (one spare) in the same TinyTronics order, because stock is only 9. That adds $8.99 outside the per-part figure.
  
  Note: WebSearch was exhausted for this turn (shared budget; my single search call was refused). Verification used WebFetch and curl on primary pages only: TinyTronics pages and PDFs, bmsdaly.com products.json and the TI part page. eBay.de and NKON returned 403; Botland had no Daly BMS.
- **Sources:**
  - https://www.tinytronics.nl/en/power/bms-and-chargers/bms/daly-bms-li-ion-li-po-protection-circuit-4s-15a-with-balancing
  - https://www.tinytronics.nl/product_files/005102_Data-Sheet-of-DL-J04G3-L04S15ATJ-BMS-circuits.pdf
  - https://www.tinytronics.nl/en/power/bms-and-chargers/bms
  - https://www.tinytronics.nl/product_files/006582_Data_Sheet_of_DL-J13G3-TJ_BMS.pdf
  - https://www.tinytronics.nl/en/power/bms-and-chargers/bms/daly-bms-li-ion-li-po-protection-circuit-7s-15a-with-balancing
  - https://www.tinytronics.nl/en/power/bms-and-chargers/bms/daly-j13g3-bms-lifepo4-protection-circuit-4s-15a-with-balancing
  - https://www.tinytronics.nl/en/power/bms-and-chargers/bms/li-ionli-po-protection-circuit-(bms)-4s
  - https://www.tinytronics.nl/en/power/bms-and-chargers/bms/qskj-li-ionli-po-protection-circuit-(bms)-4s
  - https://bmsdaly.com/products.json
  - https://www.ti.com/product/BQ77915/part-details/BQ7791500PWR
  - https://www.ebay.de/itm/388444903713
  - https://mysku.club/blog/aliexpress/98195.html
  - https://done.land/components/power/powersupplies/battery/bms/4s/15a/
- **Confidence:** high

