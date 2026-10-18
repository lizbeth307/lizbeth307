# Ip2368 4s 100 w pd board charge only bz: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** IP2368 4S 100 W USB-C PD charger board on node N (charge-only BZ wanted; RVSET 5.1k = 4.10 V/cell, RISET 15k = 3 A, ISET_MODE to GND, 10k B3380 NTC, KSD9700 70 C). Qty 2, tier core, group Power.
- **Current pick:** IP2368 4S 100 W PD board, charge-only BZ (RVSET 5.1k, RISET 15k). Every retail board is really the bidirectional COUT version: 48x34 mm, 4x NVMFS5C450N, HYG082N03 VBUS FET, 35 V caps, and either an HT7550-1 or an ME6201 5 V LDO. It sits behind the TPS259470A reverse-blocking eFuse.
- **Current price usd:** 25-49 for 2 (STACK, unverified), so about 12.5-24.5 per board. The only cited price is a Newegg snippet of $15.79 per board. Newegg returned 403 on 18 Oct 2026, so it is still unverified.
- **Decision:** keep
- **Chosen:** Keep the IP2368 4S board (retail COUT, the reviewed 48x34 mm BOM). No different part survived. The only cheaper-looking options are this same board from other listings. That is a choice of seller, not an analog. Suggested route for Europe: buy the 4S variant from a high-volume AliExpress listing that ships to the EU and charges VAT at checkout (IOSS). Buy 3 if the multi-buy price makes 3 cost about the same as 2. Record the real landed price at checkout. Every goods-in gate stays in force.
- **Chosen price usd:** Unchanged: 25-49 for 2 (unverified). Possible EU landed cost on the AliExpress route, from search snippets only: 2 x $9.28-13.13 = $18.6-26.3, plus EU VAT of 17-27 % (about $22-33), plus the flat EU customs duty that has applied since 1 Jul 2026 (operator note 34; the amount is not verified), plus shipping. That lands inside the STACK range. It is not below it.
- **Saving usd:** 0 proven. Choosing the cheapest 4S listing might save $0-15 for the pair, but I could not verify any price today, and VAT plus the new EU duty take most of the gap. Do not count a saving.
- **Equivalence proof:** I tried to prove each candidate worse.
  
  1) Same IP2368 board from other listings (AliExpress high-volume seller, the AliExpress item mysku measured, Walmart, OnBuy):
  - The specs come from the chip, so they are equal by construction. I checked IP2368 DS V1.41 myself:
    - 2-5S; CV range 4.1-4.4 V/cell; VTRGT = 4000 + 0.02*RVSET, so 5.1k gives 4.102 V/cell, at the very bottom of the range. The DS table characterises only 7.5k and up (4.11/4.15/4.19 V), so the +/-40 mV/cell at 5.1k is extrapolated. The goods-in V_CV test covers this.
    - ICHRG = 0.2*RISET with ISET_MODE to GND: 15k = 3 A.
    - IL_PK 10 A; ISTOP 100 mA; recharge at VTRGT - N*0.1 V; TEND 45/48/51 h.
    - Input 4.5-25 V, OVP 25 V, pins rated 30 V; auto-derating to the adapter's PD power (DS 12.3).
    - Charge and discharge switching 250 kHz, typical only, with no min/max given.
    - NTC 80/20 uA, 0.39/0.55 V, 0-45 C; ISTB 180 uA at 14.8 V; OTP 110-140 C.
  - Measured (mysku, 3 May 2024, same board family, 4S by default with R7 13k):
    - 0.1 mA sleep; NTC trips at 0.39/0.55 V; 5.1 A charge at RISET 27k.
    - 89-94.3 % in boost; 80-85 W maximum.
    - One FET just above 100 C at 5.1 A.
  - Where it fails: build quality is not guaranteed even within one listing. The two boards mysku received from the same listing carried different LDOs (HT7550-1 vs ME6201), so a cheaper seller is not-worse only after goods-in.
  - Price could not be verified anywhere today:
    - aliexpress.com/item/1005004270757563 redirects to aliexpress.us/item/3256804084442811, which served a captcha or an empty JS shell.
    - aliexpress.us/item/3256805610415460 sent me into a login redirect loop.
    - Walmart 5614775489 and 5799421375 hit a bot wall.
    - Newegg and OnBuy returned 403.
    - EU maker shops (Botland, BerryBase, Roboter-Bausatz) have no IP2368 board.
  - So no saving is proven. Walmart US is not a real route for a buyer in Europe (I did not check whether it ships to the EU).
  
  2) IP2366 140 W board. I checked DS V1.10 and it is worse here:
  - No charge-current set point. PSET only picks 30/45/60/65/100/140 W. At 45 W that is about 3.2 A at 13.2 V and 2.6 A at 16.4 V (slower end of charge). At 60 W it is up to about 4.3 A at 13.2 V, which breaks the 3 A heat cap inside the case.
  - PD3.1 EPR can negotiate 28 V, which trips the TPS259470A OVLO of about 22 V.
  - The DS lists no charge-only variant. CC_BDO only sets the CC default in the low-power state.
  - No independent measurement exists.
  - Price is the same class, and it needs a new footprint.
  - It is better only in standby (5/10 uA vs 180 uA), power and input range.
  - Correction to the angle-B claim: its 50 mA trickle below 2.5 V is not a disadvantage. IP2368 DS V1.41 gives the same 30/50/70 mA.
  
  3) TI BQ25798 EVM, DIY BZ board, PD trigger plus buck, and ISDT-only charging are each worse or not buyable (see rejected).
  
  Result: nothing cheaper is not-worse, so the current part stays.
- **Rejected:**
  1.
    - **Name:** Same IP2368 4S board from a high-volume AliExpress seller (JETTING-type listing, aliexpress.us 3256805610415460; snippets $9.28-13.13)
    - **Why:** Same part, so it is not an analog. The price is unverifiable: the listing sends me into a login redirect loop, and BOM photos and the 4S variant could not be checked. EU VAT (17-27 %) and the flat EU duty since 1 Jul 2026 take most of the gap. BOM varies even within one listing (HT7550-1 vs ME6201 in the mysku pair). Kept only as the suggested buy route. No saving counted.
  2.
    - **Name:** Walmart US 2-pack $19.94 / single 4S $12.50 (walmart.com/ip/5614775489, 5799421375)
    - **Why:** Both pages hit a bot wall on 18 Oct 2026, so the price is unverified. It is not confirmed that the 2-pack is 4S. It is a US marketplace listing, and I did not confirm delivery to Europe. US-to-EU import would add VAT, duty and shipping. Not a real price for this Europe-based user.
  3.
    - **Name:** The AliExpress listing mysku measured (item 1005004270757563)
    - **Why:** It redirects to aliexpress.us/item/3256804084442811, which served a captcha. The only price is 1089 RUB from May 2024, so today's price is unknown. The two boards from it had different LDOs, so even this listing does not guarantee the reviewed BOM. Same part, not provably cheaper.
  4.
    - **Name:** OnBuy Romania IP2368 4S board (83.27 RON + 16.53 RON delivery)
    - **Why:** The page returned 403, so the price is unverified. About 99.8 RON is roughly $22 per board, or about $44 for 2 (rough conversion), which is not cheaper than the current range. Seller and LDO variant unknown.
  5.
    - **Name:** Injoinic IP2366 140 W 2-6S board (eBay $10.15 + $5.79, eBay.de EUR 11.66, Walmart $24.72; all unverified)
    - **Why:** DS V1.10: no charge-current set point; PSET steps only (45 W is about 2.6-3.2 A depending on pack voltage, 60 W up to about 4.3 A, over the 3 A thermal cap). PD3.1 can request 28 V EPR, which trips the TPS259470A OVLO of about 22 V. The DS lists no charge-only variant. No independent measurement. New footprint and case CAD. Price is not lower. Better only in standby (5/10 uA).
  6.
    - **Name:** TI USB-PD-CHG-EVM-01 (BQ25798 + TPS25751)
    - **Why:** Not cheaper: DigiKey HK HKD 1,458.74 (snippet; ti.com shows no price). BQ25798 is I2C-configured, so it needs a host. It switches at 750 kHz or 1.5 MHz (ti.com), with fundamentals in the MW band, so it needs a new spur gate. The EVM form factor does not fit the case.
  7.
    - **Name:** DIY board with the genuine IP2368_BZ chip
    - **Why:** Cannot be bought: LCSC C5203723 shows 'Not available now' (18 Oct 2026), C7545631 is no longer manufactured, and the JLC $0.04 rows are placeholders. The home layout's thermals, efficiency and spurs are unmeasured. Not shown cheaper at qty 2.
  8.
    - **Name:** USB-C PD trigger at 20 V + generic CC/CV buck set to 16.4 V / 3 A
    - **Why:** It loses the NTC 0-45 C charge window, ISTOP termination, the 45-51 h timer, PD power derating and the known 250 kHz spur plan, and it can back-feed. That breaks the battery-safety rules.
  9.
    - **Name:** Drop the internal charger; charge only with the ISDT 608PD
    - **Why:** isdt.co/608pd: LiFe/LiPo/LiHv(4.35-4.50 V) 1-6S. No Li-ion 4.10 V setting is stated, there is no temperature-probe input, and its USB-C is bidirectional (140 W in / 100 W out). It would also lose the single sealed inlet, charging while the receiver runs and the NTC window.
- **Confidence:** medium
- **Conditions or tests:** Goods-in, unchanged and mandatory for every retail board, whichever seller:
  - Chip marked IP2368 / Injoinic.
  - 4S strap: R7 13k (DS example: 9.1k = 3S).
  - Swap RVSET (R4 10k) to 5.1k 1 % and RISET (R3 27k) to 15k. Keep ISET_MODE to GND through 1k (R1).
  - Fit the real 10k B3380 NTC on the R6 footprint, with 100 nF at the pin. The pin must never float.
  - Read the LDO marking: HT7550-1 (30 V) is OK. Replace an ME6201 with an LDO rated 30 V or more, because node N reaches 16.8 V.
  - After one activation charge from a one-way PD adapter: FNB58 sink test through the TPS259470A, with no VBUS out.
  - V_CV 16.25-16.57 V. The 4.10 V point is the bottom of the DS range and is extrapolated.
  - ISTOP about 100 mA. NTC trips at 0.39/0.55 V.
  - 2 h burn-in at 3 A, logging FET temperature.
  - New: measure fsw per board. The DS gives 250 kHz typical only, and 2*fsw sits 10 kHz from NAVTEX 490 kHz, so a 2 % low fsw lands on it. Then do the HF+ spur check at fsw and 2*fsw. Keep 'no charging in HF/LF Quiet'.
  - Qualify the 45 W and 60 W PD sources with the FNB58.
  - Buy 3 if 3 costs about the same as 2, to cover a reject.
  - Record the landed EU price (VAT plus EU flat duty) at checkout.
- **Stack changes:** No change to rails, connectors, drivers or case.
  
  Text corrections:
  - (1) STACK and re-audit D say 'trickle 100 mA below 2.5 V'. IP2368 DS V1.41 gives 30/50/70 mA at VBAT < 2.5 V and 100/200/300 mA from 2.5 V to N*3.0 V. Fix the Daly UVP-wake test to expect 30-70 mA when the charger sees a pack below 2.5 V.
  - (2) The BOM line 'BZ charge-only' should read 'retail COUT board; BZ is not sold as a board and the BZ chip is unavailable at LCSC (18 Oct 2026)'. Keep the TPS259470A (OVLO about 22 V) on VBUS.
  - (3) Add the per-board fsw measurement to the goods-in and spur gate.
  - (4) Price line stays 'unverified'. Add a landed-EU note (IOSS VAT plus the flat customs duty since 1 Jul 2026, amount to be confirmed).
  
  Limits: the shared WebSearch budget was already used up, so I made no searches this turn. Prices could only be checked by direct fetches, and every marketplace blocked them.
- **Sources:**
  - https://datasheet.lcsc.com/datasheet/pdf/752f0c4a0b5b0a79a7f68752c4eac200.pdf?productCode=C5203723
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/ip2368ds/ip2368.txt
  - https://atta.szlcsc.com/upload/public/pdf/source/20240105/FCCF6C49D09DDCCD74C581E56E6D79FA.pdf
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/ip2366ds/ip2366.txt
  - https://mysku.club/blog/aliexpress/100034.html
  - https://www.lcsc.com/product-detail/C5203723.html
  - https://www.aliexpress.com/item/1005004270757563.html (redirects to https://www.aliexpress.us/item/3256804084442811.html, captcha)
  - https://www.aliexpress.us/item/3256805610415460.html (login redirect loop)
  - https://www.walmart.com/ip/5614775489 (bot wall)
  - https://www.newegg.com/p/27U-00HC-00022 (403)
  - https://www.onbuy.com/ro/p/ip2368-bidirectional-100w-fast-charging-module-buck-boost-type-c-interface-4s-lithium-battery-high-power-charging-board~p252223345/ (403)
  - https://botland.store/search/ip2368
  - https://www.berrybase.de/search?search=IP2368
  - https://www.isdt.co/608pd.html
  - https://www.ti.com/tool/USB-PD-CHG-EVM-01
  - https://www.ti.com/product/BQ25798
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (item 34, EU duty)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json

