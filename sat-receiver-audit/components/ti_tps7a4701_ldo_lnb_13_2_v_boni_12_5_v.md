# Ti tps7a4701 ldo lnb 13 2 v boni 12 5 v: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** TI TPS7A4701 ultra-low-noise LDO, qty 2: LNB13V2 rail (13.2 V, or 12.5 V per reaudit_C) and the Boni rail (BONI13V8 at 13.8 V per reaudit_B; 12.5 V in STACK v1). Chain on each rail: battery SW (12.8-16.4 V, 16.8 V during the service balance; SMBJ17A clamps at 27.6 V) -> LC -> TPS7A4701 with ANY-OUT straps -> TPS259630 eFuse -> INA3221 -> choke. EN comes from MCP23017 #1. There is no PG pin, so a TLV3011 comparator per rail reports to MCP #3.
- **Current pick:** TI TPS7A4701, commercial grade, VQFN-20 RGW 5x5 (SBVS204G, May 2026). reaudit_D's recommended in-stock buy, TPS7A4701MRGWREP (Enhanced Product), is a different orderable with a different accuracy spec; see the rejected list.
- **Current price usd:** STACK v1 says "10-20 for 2 (unverified, LCSC)". Verified 18 Oct 2026: the LCSC commercial RGWR (C90084) is $13.29 and out of stock. reaudit_D's buy, TPS7A4701MRGWREP at LCSC C2872670, is $11.0094 each with 110 in stock, so $22.02 for 2. The same part at TI.com is $11.54 each at 1-99 (search figure; I saw only the 1ku price of $6.952), with 49,362 in stock per the TI inventory API.
- **Decision:** keep
- **Chosen:** KEEP the TPS7A4701 in commercial grade, ordered as TPS7A4701RGWT. RGWT is the 250-piece reel of the same die and datasheet as RGWR. Buy it from DigiKey, a franchised TI distributor: DigiKey DE for the EU, part 296-37243-1-ND cut tape, 2,332 in stock on 18 Oct 2026. RGWR is equally acceptable once it is back in stock. Do NOT buy the EP part (TPS7A4701MRGWREP) as the default.
- **Chosen price usd:** $7.96 each at qty 1 (DigiKey US, verified), so $15.92 for 2, ex VAT. DigiKey DE (verified): EUR 6.99 each ex VAT (EUR 13.98 for 2), or EUR 8.3181 each with 19% German VAT. Shipping is EUR 25 on orders under EUR 75, so put these on the same DigiKey DE order as the other DigiKey lines (TPS259630DDAR, TLV3011, INA3221). Cheaper later: DigiKey RGWR is $6.75 cut tape on backorder (1,374 due 4 Nov 2026, 1,626 due 9 Nov 2026), which makes $13.50 for 2. TI.com RGWR is $5.089 at 1-99 (search figure; I saw the 1ku price of $2.766), with 0 in TI inventory today.
- **Saving usd:** Same part, so there is no saving against the STACK line itself: its "10-20 unverified" becomes a verified $15.92. Against reaudit_D's actual buy plan (EP at LCSC, $22.02 for 2) it saves $6.10, or $7.16 against the EP at TI.com ($23.08), and it also restores the ±2.5% accuracy spec. If the build can wait for the DigiKey RGWR backorder (4 Nov 2026), the pair costs $13.50, a further $2.42 off ($8.52 total against the EP plan).
- **Equivalence proof:** RGWT and RGWR are orderables of one part covered by one datasheet, SBVS204G (May 2026). I read the EC table myself. It specifies VI 3-35 V operating and 36 V abs max (above the 27.6 V SMBJ17A clamp), 1 A, and ILIM 1.0 A min / 1.26 A typ. Nominal accuracy is ±1% at 25 C and overall accuracy ±2.5% for VIN >= VO+1 V. Dropout is 216 mV at 0.5 A and 307 typ / 450 max mV at 1 A. Iq is 0.58 / 1.0 mA and IGND 6.1 mA at 1 A. EN high is >= 2.0 V and EN low <= 0.4 V. Shutdown current is 3.04 / 60 uA at 35 V. PSRR is 78 dB at 1 kHz (15 V out, 0.5 A). Noise is 4.17 uVrms at 1.4 V and 4.67 at 5 V, rising to 7.25 at 10 V and 12.28 at 15 V (Fig 5-1). Thermal shutdown is 170 C. RthetaJA is 32.5 C/W and RthetaJC(bot) 1.7 C/W. ESD is HBM ±2.5 kV and CDM ±500 V on the 4701. Footprint, ANY-OUT straps, EN logic, thermal path and BOM function are all identical, and the part has no Ubuntu or arm64 software dependency. DigiKey lists RGWT as Active, from TI, with a 20-week standard lead time. ANY-OUT arithmetic checked: 13.2 = 1.4+6.4+3.2+1.6+0.4+0.2; 12.5 = 1.4+6.4+3.2+0.8+0.4+0.2+0.1; 13.8 = 1.4+6.4+3.2+1.6+0.8+0.4. Every other candidate below is worse in at least one spec that matters here, costs more, or cannot be shown to be genuine.
- **Rejected:**
  1.
    - **Name:** GONGMOSEMI GM1415ACPZ-R7 (TPS7A47-pinout second source), LCSC C53430773, $3.49 each (verified, 1,275 in stock)
    - **Why:** Worse on its own Rev.0 datasheet (11/2025), which I read. (1) Noise is 13.5 uVrms at 15 V against TI's 12.28, and 7.4 against 4.67 at 5 V, so it is worse at our 12.5-13.8 V outputs. (2) Accuracy is -2/+3% against ±2.5%. (3) Max dropout is 500 mV against 450, measured at a copied VIN 3.3 V / VFB 0.5 V condition. (4) Iq is 1.0/1.7 mA against 0.58/1.0, and IGND at 1 A is 6.8/10 mA against 6.1. (5) Thermal shutdown is 155 C against 170. (6) PSRR in its Fig 14 (5 V out) is about 45 dB near 500 kHz and about 20-25 dB at 5-10 MHz, against roughly 58 dB at 10 MHz for TI (Fig 5-17/5-18). That matters for the 1.8-2.1 MHz LM61460 fallback and the buck harmonics. (7) No ESD rating is published, against HBM 2.5 kV for TI. (8) Footnote 3 says it was not tested at VIN > VOUT+1.7 V at 1 A; our worst case is 3.6-4.3 V of headroom. (9) Its own application text warns of 'two stable operating points' (a foldback start-up latch) when EN is pulled high with VIN already on under heavy load, needing input power cycling to recover. That is exactly how our rails switch: EN from MCP #1 with SW live, into an LNB load. (10) ILIM of 1.6 A min raises fault current into the TPS259630. (11) The datasheet is Rev.0, Chinese only, with copied test conditions; there is no reliability report, no PSRR-in-dropout data and no independent measurement. For EU delivery, LCSC landed cost also adds EUR 3 duty plus EUR 2 UHF per tariff line, plus shipping and VAT.
  2.
    - **Name:** TI TPS7A4701MRGWREP (Enhanced Product), $11.01 LCSC / $11.54 TI.com 1-99 (1ku $6.952 seen), 49,362 at TI
    - **Why:** Not cheaper, and worse in a spec that matters. SLVSDQ3 (Feb 2017), read by me, gives overall accuracy ±3.5% over -55..125 C, against ±2.5% for the commercial part. That is ±0.46 V at 13.2 V, ±0.48 V at 13.8 V and ±0.44 V at 12.5 V, all outside the ±0.35 V acceptance window. Every other EC value is the same: 36 V, 1 A, 307/450 mV, 4.17/4.67 uVrms, 78 dB, 2.5 kV HBM, 32.5 C/W, -55 C min TJ. Fallback only if franchised commercial stock disappears, and then only with a measured acceptance per unit and the user's sign-off.
  3.
    - **Name:** TI TPS7A4700RGWR / RGWT (ANY-OUT-only sibling)
    - **Why:** ESD is HBM ±1 kV against ±2.5 kV for the TPS7A4701 (SBVS204G Handling Ratings, verified), and both rails leave the box on F and BNC. It is not cheaper: DigiKey RGWR $6.75 and RGWT $7.96, the same as the 4701; TME's USD 3.47-5.26 range has no tiers. Stock is 0 at TI (inventory API verified), DigiKey and TME.
  4.
    - **Name:** TI TPS7A4701RGWRG4 (alternate orderable, same die)
    - **Why:** Same specs, but 0 at TI (inventory API verified). At $5.853 per 1-99 (search figure) it costs more than RGWR at TI.com, so it adds nothing over RGWT/RGWR.
  5.
    - **Name:** TI TPS7A4701QRGWTQ1 / QRGWRQ1 (automotive)
    - **Why:** QRGWTQ1 is $31.32 at LCSC with 0 stock. QRGWRQ1 is USD 5.71 at TME only with a 3000-piece MOQ, also 0 stock. The Q1 datasheet was not checked. Fails on price, MOQ and availability.
  6.
    - **Name:** AliExpress 'TPS7A4700 1A low-noise RF LDO' modules (the STACK 'budget alternative'), about $18.25-18.33 each (search listing, unverified)
    - **Why:** More expensive than a genuine franchised chip at $7.96. Built on the 4700 (1 kV HBM). Chip provenance and capacitors are unknown, and there is no measurement. A separate board adds wiring, pickup and mechanical changes. Remove it from STACK.
  7.
    - **Name:** AliExpress bare 'original' TPS7A4700/4701 chips, $2.65-6.15 (search listing, unverified)
    - **Why:** Non-franchised, with prices below franchised cut tape, which is a classic sign of remarked or recycled parts. Fails the rule that a part must be legally sold and not counterfeit.
  8.
    - **Name:** ADI LT3045 (chip about $8.63, or generic LT3045 modules about $5-10)
    - **Why:** VIN max is 20 V, below the 27.6 V SMBJ17A clamp and the >=30 V requirement. It is rated 500 mA, with no margin over the 0.405-0.499 A LNB eFuse limit. It needs a new DFN/MSOP footprint with ISET-set output. Its noise and MHz PSRR are better, but it fails on input voltage and current. Known ADI limits; analog.com returned 503, so not re-fetched.
  9.
    - **Name:** Other established-brand LDO classes (LT3042, LP38798, TPS7A4501: 20 V; ADP7142, LT3065, TPS7A49, TPS7A16, TPS7A4101: <=0.5 A, mostly 0.15-0.2 A; LT3080/81/86/88: 36-40 V and 0.8-2.1 A but tens of uVrms)
    - **Why:** Each fails at least one of: >=30 V input survival, current at least equal to the 1 A rating, or about 10-12 uVrms at 13 V. All need a new footprint. A 0.2 A part on the Boni rail alone would trade away current rating ('потужність') and add a second LDO type. These are known datasheet limits, not re-fetched in this pass.
  10.
    - **Name:** DIY LM317-class regulator plus RC/LC (about $1-2, estimate)
    - **Why:** Needs a 3 V input-output differential (SLVS044Z), so 13.2-13.8 V is impossible from a 12.8-16.4 V pack. Noise is about 0.003% of VOUT, roughly 400 uVrms against about 11. No logic EN with a true 0 V output.
  11.
    - **Name:** Used or pulled TPS7A47 chips, or TPS7A4701EVM-094 boards
    - **Why:** No traceable source, and the reflow and moisture history is unknown. An EVM is not a footprint part and is not cheaper than $7.96.
- **Confidence:** high
- **Stack changes:** 1) BOM row "LDO LNB and Boni-Whip": TI TPS7A4701RGWT (RGWR also OK), qty 2, from DigiKey DE (EUR 6.99 ex VAT each) or DigiKey US ($7.96 each); $15.92 for 2; status verified 18 Oct 2026. Put it on the same DigiKey DE order as the other DigiKey lines to get past the EUR 75 free-shipping threshold. Replaces "LCSC, 10-20, unverified".
  2) Supersede reaudit_D's "Order 2x TPS7A4701MRGWREP now": the EP is not equivalent (±3.5%).
  3) Delete the budget note "TPS7A4700 audio LDO modules".
  4) Correct the spec text in STACK C8, C17 and the BOM:
  - VIN is 3-35 V operating, 36 V abs max (not "3-36 V").
  - θJA is 32.5 C/W (not 30.5).
  - There is no PG pin; use the TLV3011 comparator into MCP #3, as in reaudit_D.
  - Noise at 12.5-13.8 V is about 10-12 uVrms (Fig 5-1), not 4.
  - PSRR at 10-15 V out dips to about 30-45 dB near 0.7-1 MHz (Fig 5-17).
  - In dropout, PSRR collapses to about 15-20 dB (Figs 5-15/5-16, VDO 200-300 mV). Size the LC pre-filter for the buck fundamentals and harmonics in that state, since the rails run in dropout below about a 14.0 V pack.
  5) No change to the VQFN-20 RGW footprint, ANY-OUT straps (13.2 / 12.5 / 13.8 V as listed), EN wiring, rails, connectors, drivers, firmware or case. Thermal is unchanged: worst case about (16.8-13.2) x 0.5 = 1.8 W, or about 2.15 W with the 12.5 V LNB option. Keep the exposed pad bonded to the mid-plate.
- **Conditions or tests:** Acceptance tests (no part change):
  (a) The ±2.5% overall accuracy holds only for VIN >= VO+1 V at the IN pin. Test LNB13V2 with IN at 14.2 V or more (13.5 V or more for the 12.5 V option). Test BONI13V8 with IN at 14.8 V or more, which means a battery of about 15.0 V or more after the LC and switch drop. reaudit_D's "battery >= 14.2 V" is not enough for the 13.8 V rail.
  (b) The guaranteed IC band is ±0.33 V at 13.2 V, ±0.345 V at 13.8 V and ±0.31 V at 12.5 V. The ±0.2 V windows (STACK, reaudit_B, reaudit_C) and the ±0.35 V connector window leave little or nothing for the drops across the 0.1 Ω INA3221 shunt, the eFuse RON, the PTC and the choke. Treat them as gates measured per unit, or set the windows from the load limits instead: Bullseye vertical 11.5-14 V, Boni 12-15 V at the barrel. The user decides; nothing is changed silently here.
  (c) First power-up: confirm each strapped voltage with EN toggled from MCP #1. Confirm the TLV3011 trip at about 90%.
  
  Purchasing:
  - Buy only from TI or a franchised distributor (DigiKey, Mouser, Farnell, TME). Check the TI marking and date code on arrival.
  - Optional cheaper route for the same part: DigiKey RGWR backorder at $6.75 (due 4 Nov 2026), or TI.com RGWR at about $5.09 when TI inventory goes above 0. Poll https://www.ti.com/storeservices/cart/opninventory?opn=TPS7A4701RGWR. Do not substitute the TPS7A4700 (1 kV HBM).
  
  EU landed cost:
  - DigiKey DE prices verified ex VAT.
  - Not verified this pass: whether DigiKey ships duties-paid (DDP), and whether the EUR 2 Union handling fee from about 1 Nov 2026 applies.
  - ICs (CN 8542) carry 0% conventional duty (known, not re-checked).
  
  Limits of this pass:
  - WebSearch budget was exhausted, so I made 0 searches. No new Chinese TPS7A47-pinout clones beyond GM1415 could be looked for; that is an open gap.
  - Mouser returned 503.
  - TI.com 1-99 prices come from the search agents. I saw only the 1ku prices: RGWR $2.766, RGWT $3.319, EP $6.952.
- **Sources:**
  - https://www.ti.com/lit/ds/symlink/tps7a47.pdf (SBVS204G May 2026; EC table, ESD table, Fig 5-1, Figs 5-13..5-18 read; local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_tps7a47/tps7a47.pdf)
  - https://www.ti.com/lit/ds/symlink/tps7a4701-ep.pdf (SLVSDQ3 Feb 2017; overall accuracy ±3.5% verified; local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/verif_tps7a47ep/tps7a4701-ep.pdf)
  - https://www.ti.com/product/TPS7A47
  - https://www.ti.com/product/TPS7A47/part-details/TPS7A4701RGWR (1ku $2.766)
  - https://www.ti.com/product/TPS7A4701-EP/part-details/TPS7A4701MRGWREP (1ku $6.952)
  - https://www.ti.com/storeservices/cart/opninventory?opn=TPS7A4701RGWR (0; also 4700RGWR 0, 4701RGWT 0, 4700RGWT 0, RGWRG4 0, MRGWREP 49362)
  - https://www.digikey.com/en/products/detail/texas-instruments/TPS7A4701RGWT/4625470 ($7.96, 2,332 in stock, Active)
  - https://www.digikey.de/en/products/detail/texas-instruments/TPS7A4701RGWT/4625470 (EUR 6.99 ex VAT / 8.3181 incl.; EUR 25 shipping under EUR 75)
  - https://www.digikey.com/en/products/result?keywords=TPS7A4701RGWR ($6.75, backorder 1,374 due 4 Nov 2026)
  - https://www.lcsc.com/product-detail/C2872670.html (EP $11.0094, 110 pcs)
  - https://www.lcsc.com/product-detail/C53430773.html (GM1415 $3.4943, 1,275 pcs)
  - https://datasheet.lcsc.com/datasheet/pdf/cd5e67c8e3650ce93fa86b135e448881.pdf?productCode=C53430773 (GM1415 Rev.0; local text /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_gm1415/gm1415_ds.txt)
  - https://www.tme.eu/en/details/tps7a4701rgwr/ (0 stock, no tiered prices)
  - https://www.lcsc.com/product-detail/C90084.html
  - https://www.aliexpress.com/w/wholesale-TPS7A4700-module.html (search-agent listing, unverified)
  - https://www.ti.com/lit/ds/symlink/lm317.pdf
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_B_receivers_rf.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md

