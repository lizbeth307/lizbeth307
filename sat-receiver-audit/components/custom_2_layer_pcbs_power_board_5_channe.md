# Custom 2 layer pcbs power board 5 channe: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** Custom 2-layer PCB set: power board + 5-channel injector board (ch1 VHF-137, ch2 UHF 435-438, ch3 L-band 1525-1710, ch4 2 m/WIDE optional, ch5 LNB IF 739.5 MHz; it also carries the HMC7992 sections). Band chokes >=0.5 A, LNB choke >=1 A, C0G DC blocks. Tier core, group Power, 1 set.
- **Current pick:** Custom 2-layer power board and 5-channel injector board. STACK v1 names no fab, finish, laminate, choke MPN, SRF, DCR or capacitor voltage. The ch1-ch4 chokes and the C0G blocks are inside the $10-30 estimate; the >=1 A LNB choke was bought separately with the QO-100 kit. Bench qualification is conducted, on the LiteVNA.
- **Current price usd:** 10-30 (STACK v1 estimate, a model, not verified)
- **Decision:** keep
- **Chosen:** KEEP the custom PCB set. No candidate that is not the same part is cheaper and also not worse: every ready-made bias tee, module, clone, used unit or DIY route failed. What changes is the specification: the v1 row was unspecified, and these are its first concrete values.
  (a) Fab: JLCPCB, ordered through the JLCONE Desktop app. Two separate designs, each <=100x100 mm. FR-4 TG130, 1.6 mm +/-10%, Dk 4.5. Injector board 1 oz; power board 1 oz with widened power paths, or 2 oz. ENIG finish. Panel thru-line coupon. Fallbacks: PCBWay, then AISLER (made in the EU, no duty).
  (b) Chokes, Murata, bought at DigiKey DE as extra lines in the existing DigiKey order:
  - ch1: LQW2UASR27J00L
  - ch2: LQW2UASR12J00L
  - ch3: LQW18AN33NJ80D
  - ch5 LNB: LQW2UAS68NG00L (or LQW2UAS68NJ00L)
  - ch4: LQW2UASR27J00L for 2 m only. For true WIDE use, TCBT-2R5G+ with RILIM 162 kOhm, the trade already declared in STACK.
  (c) DC blocks, Murata C0G 50 V 0402: GRM1555C1H102JA01D (1 nF) on every path that carries VHF/UHF, including the RTL-A RFC. GRM1555C1H101JA01D (100 pF) only on ch3, ch5 and the RTL-B side.
- **Chosen price usd:** Verified and known, net of VAT: about $10.42.
  - JLCPCB fab fee: $4.00 (2 x 'From $2.00 / 5 pcs', jlcpcb.com, 18 Oct 2026; only through JLCONE Desktop).
  - Temporary EU duty: EUR 3 per tariff line, about $3.37 for bare PCBs (HS 8534), or $6.74 if the two designs count as two items.
  - Chokes and C0G blocks at DigiKey DE: about EUR 2.71, about $3.05 (5x R27, 3x R12, 3x 33N, 3x 68NG at EUR 0.16/0.16/0.12/0.19 at qty 1; 10x each capacitor at EUR 0.02-0.03).
  UNVERIFIED: the ENIG and 2 oz surcharges, JLCPCB shipping to the EU (the calculator is dynamic and did not load), the EU handling fee of EUR 2 per line (from about 1 Nov 2026) and import VAT.
  Modelled landed total: about $15-35. Keep the row as '10-30 (estimate)' until a JLCONE checkout quote exists.
- **Saving usd:** 0 proven. The part does not change. Named fab and parts probably land inside the $10-30 estimate, but shipping, ENIG and VAT are not quoted, so no saving can be claimed. The real gain is traceability and a pinned specification. One small real saving: the LNB choke moves out of the QO-100 kit into the DigiKey order (EUR 0.19, no separate parcel).
- **Equivalence proof:** The analog is the same Gerbers. RF and DC performance comes from the layout, chokes and capacitors, so the only fab-dependent specs are the substrate and the build quality.
  
  FAB (JLCPCB), from the capabilities and base-material pages, read 18 Oct 2026:
  - Dk 4.5 for 2-layer, 1.6 mm +/-10% (at >=1.0 mm).
  - Copper 1/2/2.5/3.5/4.5 oz. Minimum trace/space 0.10 mm at 1 oz, 0.16 mm at 2 oz. Drill 0.15 mm, via 0.25 mm.
  - HASL/ENIG/OSP finishes. Standard FR-4 is TG130, which meets the Tg >=130 C requirement exactly.
  - Every substrate and feature spec in either search is met.
  - No impedance control on 2-layer. My rerun of the GCPW conformal-mapping model (w 1.0-1.2 mm, gap 0.15-0.25 mm, h 1.44-1.76 mm, er 4.3-4.7) gives Z0 46.1-58.4 Ohm, so RL >=22 dB. Use w 1.1-1.2 mm with a 0.2 mm gap: about 49-50 Ohm nominal.
  - NOT verified on any page read: JLCPCB's e-test policy and its UL number. PCBWay does state 'We electrically test every PCB... fly probe free'.
  
  CHOKES (Murata catalog O05E LQW2UAS table; Murata spec JELF243A_0102J-01; DigiKey DE parametrics, 18 Oct 2026; all Active):
  - R27: 270 nH, 500 mA, 0.91 Ohm max, SRF >=600 MHz.
  - R12: 120 nH, 650 mA, 0.63 Ohm, SRF >=950 MHz.
  - LQW18AN33NJ80D: 33 nH, 1.1 A (rated at a 40 C rise; full rating up to 85 C ambient), 0.11 Ohm, SRF >=3.15 GHz.
  - 68NG: 68 nH, 1 A, 0.20 Ohm, SRF >=1.3 GHz.
  So every band choke is >=0.5 A and the LNB choke >=1 A, with SRF above each band.
  
  My model, shunt choke with Q and SRF, worst case at L -5% with no SRF boost:
  - ch1, 137.5 MHz: |Z| 222-246 Ohm, IL 0.065-0.076 dB, RL 19-20 dB.
  - ch2, 435-438 MHz: 312-419 Ohm, 0.03-0.04 dB.
  - ch3, 1525-1710 MHz: 301-503 Ohm, 0.03-0.05 dB.
  - ch5, 739.5 MHz in 75 Ohm: 299-480 Ohm, 0.04-0.08 dB.
  - 2 m on R27: 234-261 Ohm.
  All are far inside the 0.3 dB pass mark. Every choke sits after an LNA or LNB (SAWbird+ 41/38 dB, Uputronics >=19 dB, LNB about 60 dB), so its effect on system NF is negligible.
  
  DC drop: ch1 164 mV at 180 mA, so the SAWbird+ still gets about 4.27 V against its 3.3-5.5 V range. ch2 32 mV, ch3 18 mV, ch4 82 mV, ch5 60-100 mV.
  
  Self-heating (I^2 scaling from the 40 C rise rating):
  - ch1: 5 C at 180 mA; 19 C at the 342 mA worst-case trip, which lasts only about 7.5 ms before the TPS2553-1 latches off.
  - ch5: 10 C at the 0.499 A eFuse limit.
  
  C0G blocks: DigiKey DE confirms both GRM1555C1H102JA01D and GRM1555C1H101JA01D are C0G/NP0, 50 V, 0402 and Active. 50 V is above the 13.2 V LNB rail plus transients.
  - 1 nF (0.45 nH ESL model): RL >=26 dB from 137 to 1710 MHz.
  - 100 pF: 19 dB at 137 MHz, so it is not used on VHF. It series-resonates near 740 MHz, which suits the LNB IF.
  
  Hard rules: the hardware is passive, receive-only, qualified conducted only, and has no loop or H-field footprints.
- **Rejected:**
  1.
    - **Name:** Same Murata LQW chokes and GRM C0G blocks bought from LCSC (C703705, C2044072, C3221306, C703709, C76947, C77177; 'about $3.50')
    - **Why:** The MPNs pass on specs, but LCSC fails as a source. (1) Traceability: the LCSC page says only '100% authentic'; it does not claim franchised Murata status. (2) The price is not real landed. A separate non-EU parcel adds EUR 3 x 2 tariff lines of duty, EUR 2 x 2 lines of handling fee (from about 1 Nov 2026), shipping and VAT, several times the parts cost. DigiKey DE sells the same MPNs: EUR 0.12-0.19 per choke and EUR 0.02-0.10 per capacitor, in stock, added to an order that already exists.
  2.
    - **Name:** Coilcraft 0805HP-221/121/33N + 1008HQ-68N (premium chokes)
    - **Why:** Not worse. The Coilcraft PDFs confirm: 0.50/0.62/1.1/1.1 A at a 15 C rise; DCR 426/293/87/130 mOhm; SRF typ 930/1265/2410 MHz and min 1.15 GHz. But they are not the cheapest: about $6.25 a set at LCSC, with stock of only 10-38 on some lines. DigiKey DE has no result for 0805HP-221XGRC. The ch1 220 nH part has less reactance (RL about 18 dB). Keep only as an upgrade if bench self-heating or DCR on ch1 fails.
  3.
    - **Name:** Mini-Circuits TCBT-2R5G+ ($9.05 at qty 10 to $12.44)
    - **Why:** Worse: 200 mA DC and 25 V maximum (datasheet), against >=0.5 A and the 50 V needed on the LNB channel. IL is 0.7 dB typ at 1250-2500 MHz. It costs about 60-80x a chip choke. It stays only on ch4 WIDE, as the trade STACK already declares (RILIM 162 kOhm, <=150 mA).
  4.
    - **Name:** Mini-Circuits TCBT-14+ ($10.42-12.12, LCSC)
    - **Why:** Worse: 200 mA, and VSWR 1.2/1.5 max against TCBT-2R5G+'s 1.05/1.2. Not cheaper.
  5.
    - **Name:** Mini-Circuits ADCH-80A+
    - **Why:** Worse: 100 mA DC (250 mA absolute maximum), and the band starts at 50 MHz. It would overheat on the SAWbird+ channels.
  6.
    - **Name:** Generic '10 MHz-6 GHz' SMA bias-tee modules (AliExpress/Amazon, about EUR 7 each)
    - **Why:** Worse and unproven. No rated current, unknown capacitor dielectric, unshielded. The only measurement found is secondary: an Amazon review in earlier research shows several dB of loss at VHF. Five of them cost more than the board, and the power/switch PCB is still needed.
  7.
    - **Name:** Used connectorized bias tees (ZFBT-4R2GW+ class)
    - **Why:** No listing was verified. Each unit would have to cost under about $6 to compete; five bodies do not fit the RF bay; there is no per-unit measurement; and the PCB is still needed.
  8.
    - **Name:** Marketplace modules wired together in place of the power board (LT3045, INA3221 boards etc.)
    - **Why:** Worse. Counterfeit-chip risk, and no module exists for the TPS259630 eFuse, the latch-off TPS2553 channels or the GCPW sections. More DC wiring loops in the RF bay, and the bonded-plate thermal path is broken. More expensive.
  9.
    - **Name:** Home-made board (toner transfer or CNC)
    - **Why:** Worse: no plated vias, so no via fence, no EPAD thermal or ground vias and no solder mask for 0.5 mm QFN.
  10.
    - **Name:** PCBWay 2-layer (2 x $5 for 10 pcs, 100x100 mm, 1.6 mm)
    - **Why:** Not worse; it is verified to e-test every board, fly probe free. But the fab fee is $10 against $4, and Dk and Tg are not stated on its capabilities page. It is the fallback if JLCPCB's e-test cannot be confirmed in the quote form, or if its landed quote is higher.
  11.
    - **Name:** AISLER (Germany) 2-layer HASL/ENIG Budget, sets of 3
    - **Why:** The formula is verified: EUR 12 job fee + EUR 0.067 (HASL) or 0.097 (ENIG) per cm2 x 3, net of VAT. For two assumed 60 cm2 designs that is about EUR 48-59 net, or $64-79 with 19% VAT, so it is not cheaper. E-test and free shipping are not stated on the pricing page; the page's own worked example uses a different rate (EUR 0.051). It remains the EU no-duty fallback if JLCPCB's landed quote is above AISLER's.
  12.
    - **Name:** OSH Park 2-layer ENIG
    - **Why:** About $93 for two assumed 9.3 sq in boards, plus EU duty and VAT; 1 oz only. Not cheaper.
- **Confidence:** medium
- **Conditions or tests:** Order gates:
  1. Quote both designs in JLCONE Desktop: 1.6 mm, 1 oz (power board 2 oz only if the battery/SYS12 paths cannot be widened), ENIG, green, one parcel. Confirm that the e-test field reads a full flying-probe test. Record the landed total: fab + ENIG + shipping + IOSS VAT + EUR 3 per tariff line + the EUR 2 handling fee per line if the parcel lands after about 1 Nov 2026.
     - Accept if it is <=$30 and below AISLER's landed figure.
     - Otherwise go to PCBWay, or to AISLER ENIG Budget.
     - A board over 100x100 mm leaves the $2 price class; re-quote it.
  
  Arrival checks:
  2. Calipers: 1.44-1.76 mm. ENIG pads flat. Continuity spot checks.
  
  LiteVNA, conducted only, into loads:
  3. Panel thru-line coupon: S11 <= -20 dB to 1.8 GHz.
  4. Per channel, in band:
     - IL <= 0.3 dB
     - S11 <= -15 dB (target -20 dB; ch1 R27 models at 19-20 dB, and that is accepted because it sits after a 41 dB LNA)
     - DC-port-to-RF isolation and channel-to-channel isolation >= 40 dB
     - every RF output reads 0 V DC.
  
  DC and thermal:
  5. Drop and heat:
     - ch1 at 180 mA: total drop <= 0.25 V from the LNA4V5 bus to the SAWbird+.
     - 30 min at 180 mA on ch1 and 0.45 A on ch5 (electronic load): choke rise <= 15 C.
  6. After the TPS2553 and eFuse hard-short tests (re-audit B), re-measure each choke's DCR. It must be within 10% of the first reading, which shows no wire damage.
  
  Spec rule:
  7. Never fit the LQW18AN_00 (non-80) parts or LQW2UASR33 and above: they are 120-470 mA, which breaks the >=0.5 A rule.
- **Stack changes:** STACK line 257 (PCB row) becomes:
  - 'Custom 2-layer PCBs, JLCPCB via JLCONE Desktop (fallback PCBWay; EU no-duty fallback AISLER).'
  - FR-4 TG130, 1.6 mm +/-10%, Dk 4.5. Injector board 1 oz; power board 1 oz with widened paths, or 2 oz. ENIG. Flying-probe e-test confirmed in the quote. Thru-line coupon on the panel.
  - GCPW w 1.1-1.2 mm, gap 0.2 mm, solid bottom ground, via fence.
  - Price stays '10-30 (estimate)' until the quote. Show the landed EU cost: duty EUR 3 per tariff line, handling fee EUR 2 per line from about 1 Nov 2026, VAT.
  
  C9 / BOM, new DigiKey DE lines in the existing DigiKey order:
  - LQW2UASR27J00L x5 (ch1, ch4 2 m, spares)
  - LQW2UASR12J00L x3 (ch2)
  - LQW18AN33NJ80D x3 (ch3)
  - LQW2UAS68NG00L x3 (ch5)
  - GRM1555C1H102JA01D x10
  - GRM1555C1H101JA01D x10
  - About EUR 2.71 net in total.
  
  C8/C23 and the QO-100 kit row (line 295):
  - The region is now Europe, so the >=1 A LNB choke (LQW2UAS68NG00L) moves out of the kit into this DigiKey order now.
  - The 68 nH part covers only the 735-750 MHz QO-100 IF. A 950-2150 MHz TV-LNB IF would need a re-verified choke.
  
  DC block rule:
  - 1 nF on every VHF/UHF-carrying pin, including ch1, ch2, ch4 and the RTL-A RFC.
  - 100 pF only on ch3, ch5 and the RTL-B pins.
  
  ch4: R27 for 2 m only. For WIDE, TCBT-2R5G+ with RILIM 162 kOhm, the trade already declared.
  
  No change to rails (LNA4V5 4.5 V, LNB13V2), connectors, drivers (passive hardware) or case. A board larger than 100x100 mm changes only the price, not the case.
  
  Sourcing rule: no separate LCSC parcel for these parts (traceability, and duty per tariff line).
- **Sources:**
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md lines 44-45, 257, 295, 680-692
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_B_receivers_rf.json (RF front end v1.1: loads 170-180/120-160/50/90/20 mA, RILIM 88.7k/162k, eFuse 0.405-0.499 A)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md items 34-35 (EUR 3 per tariff line duty, EUR 2 UHF)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/g_pcb_dl/C703705.pdf (Murata catalog O05E, LQW2UAS table p254-255)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/g_pcb_dl/C3221306.pdf (Murata spec JELF243A_0102J-01, LQW18AN_80, 40 C rise rating, derating above 85 C)
  - https://www.digikey.de/en/products/result?keywords=LQW2UASR27J00L
  - https://www.digikey.de/en/products/result?keywords=LQW2UASR12J00L
  - https://www.digikey.de/en/products/result?keywords=LQW18AN33NJ80D
  - https://www.digikey.de/en/products/result?keywords=LQW2UAS68N
  - https://www.digikey.de/en/products/result?keywords=GRM1555C1H102JA01D
  - https://www.digikey.de/en/products/result?keywords=GRM1555C1H101JA01D
  - https://www.digikey.de/en/supplier-centers/murata-electronics
  - https://www.lcsc.com/product-detail/power-inductors_murata-electronics-lqw2uas68ng00l_C703709.html
  - https://www.coilcraft.com/pdfs/0805hp.pdf
  - https://www.coilcraft.com/pdfs/1008hq.pdf
  - https://www.minicircuits.com/pdfs/TCBT-2R5G+.pdf
  - https://jlcpcb.com/
  - https://jlcpcb.com/capabilities/pcb-capabilities
  - https://jlcpcb.com/help/article/jlcpcb-base-material
  - https://jlcpcb.com/help/article/Shipping-Methods-and-Delivery-Time
  - https://jlcpcb.com/shipping
  - https://www.pcbway.com/
  - https://www.pcbway.com/capabilities.html
  - https://community.aisler.net/t/our-simple-pricing
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/pcbB_calc/gcpw.py (rerun by me, plus extended tolerance grid and choke and DC-block models)
  - Note: the shared WebSearch budget was exhausted (1 call refused), so verification used WebFetch on primary and distributor pages and local datasheets only. JLCPCB ENIG and 2 oz surcharges, EU shipping and the e-test policy remain unverified.

