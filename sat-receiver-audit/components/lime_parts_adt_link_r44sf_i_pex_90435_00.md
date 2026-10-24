# Lime parts adt link r44sf i pex 90435 00: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_206ecd06-fb0`_

- **Part:** Lime-only parts set (with-Lime build is the default after the user's decision of 18 Oct 2026): ADT-Link R44SF 5 cm riser; MHF 4L tool; pedestal, gap pad and fins; DC blocks on Lime RX1/RX2; 10 dB pad after the SAWbird+ on the Lime RX1 L-band route; 50 Ohm load on Lime TX X1; 3rd HMC7992 SP4T on the injector PCB
- **Current pick:** ADT-Link R44SF 5 cm + I-PEX 90609-0001 tool (re-audit B fix; STACK v1 still says 90435-001) + Al pedestal / Gelid GP-Ultimate 1.0 mm strip / plate fins (pedestal stock and pad already counted in G4's chassis and mechanical sets) + 2x Mini-Circuits BLK-89-S+ (RX1, RX2) + 1x inline 10 dB SMA pad (STACK names no SKU; reference Mini-Circuits VAT-10A+) + Mini-Circuits ANNE-50+ on X1 + genuine ADI HMC7992LP3DE (DigiKey DE) as the 3rd section on the injector PCB, with C0G blocks on all 5 RF pins (G1 design)
- **Current price usd:** About 126.44 ex VAT and shipping, from today's verified prices (FX 1 EUR = 1.1241 USD). Breakdown: R44SF 19.00 (adt.link) + 90609-0001 EUR 16.08 = 18.08 (DigiKey DE, 358 in stock) + 2x BLK-89-S+ 40.52 (Mini-Circuits 20.26 each; DigiKey DE EUR 21.34 ex VAT, 0 in stock, 10 due 27 Oct) + VAT-10A+ 21.07 (Mini-Circuits 1-9, >1,000 in stock) + ANNE-50+ 14.84 (Mini-Circuits per re-audit D/G5, not re-fetched) + HMC7992LP3DE EUR 11.50 = 12.93 (DigiKey DE, G1). Add about 1-2 for section passives (model). Fins are unpriced. Pedestal and pad sit in the G4 lines. The STACK v1 figure of 87-127 was an unverified model and leaves out the X1 load.
- **Decision:** replace_conditionally
- **Chosen:** Two items change, both on the 3rd HMC7992 section of the injector PCB that already exists; everything else stays.
  (1) RX1 DC block: drop the inline BLK-89-S+. The HMC7992 datasheet makes the RFC and RF3 C0G caps mandatory (all 5 RF pins are DC-coupled, per re-audit B reading the Rev 0 datasheet). These caps (C0G, at least 50 V) become the RX1 block. Add one more series Murata GJM1555C1H220JB01D (22 pF C0G 50 V high-Q 0402; EUR 0.11 at DigiKey DE per angle B) at the Lime RX1 edge connector, so the path still has 3 series DC barriers, the same count as with the BLK-89.
  (2) 10 dB pad: replace the inline SMA pad with Mini-Circuits YAT-10A+ (MCLP 2x2 mm thin-film-on-GaAs attenuator, PL-586 footprint), placed after the RF3 cap. DigiKey DE 3157-YAT-10A+CT-ND, EUR 3.93 ex VAT / EUR 4.68 incl. VAT, 9,040 in stock, Active.
  KEEP unchanged:
  - ADT-Link R44SF 5 cm;
  - I-PEX 90609-0001;
  - 1x BLK-89-S+ on RX2 (the S-band LNA feed is not designed yet);
  - ANNE-50+ on X1;
  - HMC7992LP3DE from DigiKey DE;
  - pedestal and pad as in G4, and the plate fins.
- **Chosen price usd:** About 89.65 ex VAT and shipping. Breakdown: R44SF 19.00 + 90609-0001 18.08 + 1x BLK-89-S+ 20.26 + YAT-10A+ 4.42 + 22 pF edge cap 0.12 + ANNE-50+ 14.84 + HMC7992 12.93. Add the same 1-2 of section passives and the unpriced fins. Pedestal and pad stay in G4. EU incl. 19% DE VAT for the DigiKey DE parts: tool EUR 19.14, YAT EUR 4.68, HMC7992 EUR 13.685. R44SF (CN) and the Mini-Circuits parts (US) land with import VAT, plus EUR 3 duty per tariff line (consignments up to EUR 150, IOSS or postal), plus the EUR 2 handling fee per line from about 1 Nov 2026.
- **Saving usd:** About 36.79 ex VAT: BLK-89-S+ 20.26 + (VAT-10A+ 21.07 − YAT-10A+ 4.42 = 16.65) − 0.12 for the extra cap. The EU landed saving is larger, because two US-sourced tariff lines leave the Mini-Circuits order: VAT, EUR 3 duty and the EUR 2 handling fee on each.
- **Equivalence proof:** RX1 DC block (datasheets and design read):
  - The BLK-89-S+ Rev G spec is IL 0.15 typ / 0.8 max and RL 18 dB min at 1-4 GHz (0.12 dB / 26 dB typ at 2 GHz), 50 V, one coaxial capacitor.
  - RX1 only ever carries what the 3rd switch's RF3 throw delivers: the L-band ch3 route, about 1.42-1.71 GHz (SAWbird+ H1 / iO / GOES).
  - The RFC and RF3 C0G caps are already required by the HMC7992 datasheet. They already set the path's low-frequency response and already block DC. With the BLK added, the path still has those caps; the BLK only adds about 0.12 dB and two SMA interfaces.
  - After the change: DC rating is the same (50 V C0G against 50 V; the highest DC on ch3 is 4.5 V, and the LNB 13.2 V never reaches this switch). IL is lower and RL is no worse (model: a 22 pF high-Q 0402 is near series resonance at about 1.7 GHz, so |Z| is a few ohms). DC barriers are 3 in series, same as before.
  - The 0.1-8 GHz range of the BLK is not usable on this throw in either design, so no coverage is lost.
  - RX2 keeps its BLK-89-S+, so 2.2-3.8 GHz coverage is untouched.
  
  10 dB pad (both datasheets read):
  - YAT-10A+ Rev B guarantees 9.6-10.4 dB over DC-5 GHz. VAT-10A+ Rev C guarantees only 10±0.3 dB at 10 MHz; its flatness of 0.25 dB is typical, with no maximum. In band the YAT is equal or better (typical 9.98 dB at 1 GHz and 9.96 at 2 GHz, against 10.08-10.16).
  - VSWR: 1.09 typ / 1.25 max (DC-5 GHz) against 1.2 typ / 1.5 max. YAT is better.
  - Power: 1.7 W at 25 C derated to 1.0 W at 85 C, identical. Real level is below 0 dBm.
  - Range: DC-18 GHz against DC-6 GHz. YAT is better.
  - Genuine part from an authorised distributor; ESD HBM class 2; MSL1.
  
  Stated, not silent:
  - (a) Case temperature is rated -40 to +85 C against -45 to +100 C. The board already carries +85 C-class parts (TPS2553 ambient -40 to +85 C per TI, not re-read today). The stack's own limits are frame 60 C and LMS7002M 75 C, so the system envelope does not change.
  - (b) YAT drift over temperature is unpublished; VAT gives 0.3 dB max. A thin-film pad on a fixed protective role has more than 10 dB margin to the Lime's +10 dBm maximum.
  - (c) The pad value can no longer be swapped by hand. YAT-0A+ uses the same footprint as a 0 dB bypass, and an extra SMA pad can still go on the edge jack.
  - (d) Board-level S-parameters are unmeasured, so this is conditional.
  
  The edge connector toward the Lime RX1 cable is needed in both designs, so it is not an extra cost. Nothing changes on rails, drivers or software. All parts are passive and the receive-only rules are untouched.
- **Rejected:**
  1.
    - **Name:** ADT-Link M44SF (PCIe 4.0 x4)
    - **Why:** Not cheaper ($19 for 10 cm). Its shortest length is 10 cm against the 5 cm the layout needs, and its sideband wiring, female-board window and STEP model are unverified.
  2.
    - **Name:** Delock 64136 M.2 riser, 20 cm
    - **Why:** About $81 (EUR 69.95 at LDLC), about 4x the price; 20 cm; shielding and sideband wiring not stated.
  3.
    - **Name:** Generic AliExpress/eBay M.2 M-key extenders
    - **Why:** No AER/BER or link-margin measurement exists. Whether PERST#/CLKREQ#/REFCLK are carried is unknown (generic FPC risers failed on missing PERST), and shielding is unproven. A search found no cheaper genuine ADT-Link R44SF listing: Newegg $48.99-52.46, eBay.de $59.50.
  4.
    - **Name:** No riser (Lime straight into J13)
    - **Why:** Layout analysis shows it is worse: about 35-40 mm overhang over J8/J21/HDMI, no shielded RF bay, no pedestal cooling, and the SDR sits next to SoC/DSI noise.
  5.
    - **Name:** I-PEX 90435-001 (MHF 4 tool, the STACK v1 pick)
    - **Why:** I-PEX's MHF 4L page (read today) lists only 90609-0001 and the 90615-0013 tweezers for the 20565-001R-13 1.13 mm plug; 90435-001 is not listed. The fit on the Lime's receptacles is unproven, which risks the $249 board, for a saving of EUR 0.19 (EUR 15.89 against 16.08).
  6.
    - **Name:** I-PEX 90615-0013 / 90616-0008 tweezers, 90873-0001
    - **Why:** Dearer: $321.04 / $337.10 / $64.56.
  7.
    - **Name:** Generic MHF4/IPEX4 pullers
    - **Why:** No evidence that they fit the MHF 4L lock; price unverified.
  8.
    - **Name:** Removing the RX2 BLK-89-S+ as well (on-board cap)
    - **Why:** The S-band LNA is unnamed and its bias feed is not designed. Whether the cf2235 cavity passes DC is unknown, and no injector-PCB C0G cap faces RX2. Revisit only if the S-band LNA gets an injector channel on that PCB with a C0G cap of 50 V or more facing the Lime.
  9.
    - **Name:** Crystek CBLK-300-3
    - **Why:** Its top frequency is 3 GHz (cuts the 3.3-3.8 GHz wish on RX2) and it is rated 16 V (per G5). Its price comes only from search snippets; the saving would be at most $0.38.
  10.
    - **Name:** Nooelec SMA in-line DC block
    - **Why:** Dearer ($24.95); frequency range and DC rating unpublished.
  11.
    - **Name:** Generic AliExpress DC blocks
    - **Why:** The only independently measured unit had about 0.2-0.5 dB IL (worse than the BLK-89's 0.12 dB), no RL data, and an unknown DC rating.
  12.
    - **Name:** Used/marketplace BLK-89-S+
    - **Why:** Not cheaper ($24.97 + 3.99 eBay.de; $24.99 used AU); provenance unknown.
  13.
    - **Name:** DIY 0402 resistor pi-pad
    - **Why:** No S-parameter evidence for accuracy or VSWR at 1.4-1.7 GHz. The YAT-10A+ costs only $4.42 and has guaranteed specs.
  14.
    - **Name:** Second Nooelec attenuator kit, or generic SMA pads
    - **Why:** The kit is $47.95, dearer, with accuracy and VSWR unpublished; generic pads have no measurement. Taking the 10 dB from the lab-core kit would leave the lab kit short.
  15.
    - **Name:** Mini-Circuits ANNE-50L+ for the X1 load ($9.41)
    - **Why:** Its published specs are lower: RL 26 dB min at DC-4 GHz against 30 dB, and derating to 325 mW against 350 mW at 100 C (datasheet Rev E, as read by G5, which rejected it for the same reason). In the X1 dump-load role on a software-blocked TX port, neither number changes system behaviour, so it is offered only as an explicit user trade saving $5.43, not a silent swap.
  16.
    - **Name:** Joymax CT-SAA03T-006M terminator
    - **Why:** VSWR 1.3 (about 17.7 dB RL) against 30 dB min, no power rating, -40 to +85 C.
  17.
    - **Name:** MHF4 termination plug on X1 (no cable, no SMA load)
    - **Why:** Search found no genuine maker part with a datasheet (RL and power unknown).
  18.
    - **Name:** HMC7992LP3DE from Mouser
    - **Why:** The price ($10.25-10.98) comes only from aggregator snippets. Mouser.de returned 503 and findchips showed no results today, so it is unverified. It would also mean a separate shipment.
  19.
    - **Name:** HMC7992LP3DE from Richardson RFPD ($6.89)
    - **Why:** Stock 0 in the snippet, page returned 403; price, franchise status and minimums unverified.
  20.
    - **Name:** Generic marketplace HMC7992 boards
    - **Why:** Counterfeit indicators (ADI silkscreen on boards ADI does not make, below-cost price), unknown DC-block values, unverifiable linearity.
  21.
    - **Name:** Splitter instead of the 3rd switch
    - **Why:** 3.2-6 dB loss against 0.6 dB, about 20-25 dB isolation against 40 dB min, no 50 Ohm park, and Lime LO spurs would reach RTL-B.
- **Confidence:** medium
- **Conditions or tests:** All checks are conducted, in Bench mode, into loads or a DUT only, and never on air.
  
  1. Design rules:
  - The RFC and RF3 caps of the 3rd section are C0G rated 50 V or more.
  - The extra 22 pF C0G sits at the Lime RX1 edge jack.
  - The YAT-10A+ sits after the RF3 cap on 50 Ohm GCPW to PL-586, inside the shield-can footprint.
  - Keep all three caps at least 3 mm from board edges and screw holes (flex-crack).
  
  2. LiteVNA, after SOLT plus the G1 thru-coupon de-embedding, from RFC through RF3 to the RX1 edge jack, at 1.42-1.71 GHz:
  - pad contribution 10 ± 0.5 dB, and the whole section at most 0.9 dB (HMC7992 max) + 10.4 dB;
  - RL at the edge jack at least 20 dB, and never below 14 dB (the VAT-10A+ VSWR 1.5 limit).
  - On a fail, fit YAT-0A+ in the same footprint and go back to the inline VAT-10A+.
  
  3. DC check: with ch3 4.3 V bias on (v2.1), a DMM at the RX1 cable centre pin reads below 10 mV, with the cable unplugged from the Lime. Repeat at power-up with the MCP23017 in reset.
  
  4. The G1 isolation, park and spur tests also cover the 3rd section (RF1 park, isolation at least 30 dB conducted).
  
  5. The 45-min noon soak must keep the injector-board temperature at the YAT at or below 85 C (expected well below; frame limit 60 C).
  
  6. Unchanged gates:
  - riser: 8 GT/s x1, zero AER errors in 60 min, 50 warm + 20 cold boots, zero limeTRX drops;
  - R44SF 3.3 V current and temperature check (INA228);
  - ask ADT-Link which variant takes a 2230 host and a 2280 B+M card;
  - check that 90609-0001 fits the Taoglas MHF4L plugs on a spare cable first;
  - pedestal and pad per G4: gaps 0.7-1.0 mm, LMS7002M at most 75 C.
  
  7. Optional user trade: ANNE-50L+ on X1 saves $5.43, but only if the user explicitly accepts the lower published RL and derating.
- **Stack changes:** Corrections to STACK:
  - Rows 133, 293 and 1127: change 'I-PEX 90435-001' to 'I-PEX 90609-0001'.
  - Row 293 contents: R44SF 5 cm; 90609-0001; 1x BLK-89-S+ (RX2 only); RX1 DC block = the 3rd HMC7992 RFC/RF3 C0G caps plus a 22 pF C0G at the edge jack; YAT-10A+ 10 dB on board; ANNE-50+ on X1 (new: it was unpriced, but the receive-only rule requires it); HMC7992LP3DE from DigiKey DE.
  - Row 293 price: about $89.7 ex VAT/shipping, plus about $1-2 passives and the unpriced fins; pedestal and pad are counted in the G4 lines. This replaces the model 87-127.
  - Rows 69/688: Lime RX1 gets its 10 dB on the injector PCB, so no inline pad and no BLK on RX1.
  
  Order changes: drop 1x BLK-89-S+ and the inline 10 dB pad from the Mini-Circuits/US order; add YAT-10A+ (plus one YAT-0A+ as a fallback bypass, optional, price not checked) and the 22 pF cap to the existing DigiKey DE order.
  
  PCB and mechanics:
  - PCB: the 3rd section gains the PL-586 footprint and one 0402 cap. The edge jack was needed anyway.
  - RF bay: two inline bodies (about 66 mm, 17 g) leave the RX1 jumper run; the RX1 cabling (board SMA(f), M-M jumper, Taoglas MHF4L-SMA(f) bulkhead) is unchanged.
  
  labd: record the measured pad S21 in the Lime RX1 level-calibration table.
  
  No change to rails, drivers, Ubuntu 24.04 arm64 packages or the case outline. Receive-only, no-loop and conducted-only rules are unaffected.
- **Sources:**
  - https://www.adt.link/product/R44SF.html
  - https://www.i-pex.com/product/mhf-4l
  - https://www.digikey.de/en/products/result?keywords=90609-0001
  - https://www.digikey.de/en/products/result?keywords=BLK-89-S%2B
  - https://www.minicircuits.com/pdfs/BLK-89-S+.pdf
  - https://www.minicircuits.com/pdfs/YAT-10A+.pdf
  - https://www.digikey.de/en/products/result?keywords=YAT-10A%2B
  - https://www.minicircuits.com/pdfs/VAT-10A+.pdf
  - https://www.minicircuits.com/WebStore/dashboard.html?model=VAT-10A%2B
  - https://www.minicircuits.com/pdfs/ANNE-50+.pdf
  - https://www.minicircuits.com/pdfs/ANNE-50L+.pdf
  - https://www.digikey.de/en/products/detail/analog-devices-inc/HMC7992LP3DE/5873027
  - https://www.findchips.com/search/HMC7992LP3DE
  - https://shop.richardsonrfpd.com/Products/Product/HMC7992LP3DE
  - https://www.digikey.de/en/products/result?keywords=GJM1555C1H220JB01D
  - https://www.petertanner.dev/posts/Aliexpress-DC-block-characterization/
  - https://www.ebay.de/itm/253658960351
  - https://www.newegg.ca/p/2WG-068X-005E7
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_B_receivers_rf.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/analogs_G1_receivers_rf.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/analogs_G4_mechanical_field.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/analogs_G5_lab_bench.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/g6_parts/lime_parts_adt_link_r44sf_i_pex_90435_00.json

