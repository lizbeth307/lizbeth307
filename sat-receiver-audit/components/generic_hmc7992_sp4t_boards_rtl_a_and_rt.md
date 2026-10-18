# Generic hmc7992 sp4t boards rtl a and rt: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e32114dd-52d`_

- **Part:** RTL-A and RTL-B input selectors: absorptive SP4T RF switch x2 (behind the bias injectors; RF1 = 50 Ohm park; C0G DC blocks on all 5 RF pins; 2-line control from MCP23017 #1 at 3.3 V)
- **Current pick:** Generic marketplace HMC7992 SP4T boards x2 (reference listing Walmart.ca / Joystore 'HMC7992 Non-Reflective SP4T RF Switch Module'). The design in the photos I viewed is a hand-assembled board with 5 edge SMA jacks, a VDD/A/B/GND header and an 'ANALOG DEVICES' logo plus ADI part text on the silkscreen. ADI does not make this board; its only board is EV1HMC7992LP3D. Visible flux residue. The values of the 5 port capacitors are unknown. No measured S-parameters exist for any generic board.
- **Current price usd:** 30-40 for 2 (STACK, unverified). Walmart.ca CA$20.49 each (about $14.7) could not be re-checked because of a bot wall. EU shipping is unlikely, and EU VAT and shipping are not included.
- **Decision:** replace_conditionally
- **Chosen:** Genuine ADI HMC7992LP3DE x2 from DigiKey (505-HMC7992LP3DE-ND), placed on the existing custom 5-channel injector PCB as two 50 Ohm GCPW switch sections. This follows the re-audit B advice 'prefer chips on the custom injector PCB'. Each section has: C0G DC blocks on RFC and RF1-RF4; an on-board 49.9 Ohm 0402 park load on RF1 behind its own C0G block; 100k pull-downs and 100 pF on A/B; VDD from the same 3.3 V rail as the MCP23017, with 100 nF + 100 pF bypass; and a via-fenced EPAD ground.
- **Chosen price usd:** Chips: 2 x EUR 11.50 ex VAT = EUR 23.00 = $25.85 ex VAT at 1.1241 USD/EUR, or 2 x EUR 13.685 = EUR 27.37 = $30.77 incl. 19% DE VAT. DigiKey DE verified 18 Oct 2026: Active, 4,655 in stock, next price break EUR 9.05 at qty 10. Add about $1-2 of 0402 C0G and 49.9 Ohm passives (model) and 2-3 edge SMA or U.FL jacks for the two RFC outputs and the RTL-B BENCH input (model, not priced). PCB cost is unchanged: it stays inside the existing $10-30 custom-PCB line. Shipping is assumed to ride on the existing DigiKey order.
- **Saving usd:** On the line itself, chips only: about $4-14 ex VAT ($25.85 vs $30-40). After passives and 2-3 jacks: about $0-12 (model). Not priced: the change also removes 10 board SMA jacks, about 4-6 internal SMA jumpers from the injector outputs to the switch inputs, and the 2 SMA 50 Ohm terminators used as park loads. Including VAT it is roughly break-even if the current pick really costs $30. The main gain is a provable genuine part and a defined board, not the money.
- **Equivalence proof:** The die is the same, and DigiKey is an ADI-franchised channel with traceability, so every chip-level spec is identical to what the current pick claims. All values below come from the HMC7992 Rev 0 datasheet, which I downloaded and read:
  - Frequency range: 0.1-6 GHz specified. The text adds 'can operate well down to 10 kHz', with P1dB 21 dBm and IIP3 37 dBm at 1 MHz.
  - Insertion loss: 0.6 dB typ / 0.9 dB max at 0.1-2 GHz.
  - Isolation, RFC to RF1-RF4 worst case: 40 dB min / 45 dB typ at 0.1-2 GHz.
  - Return loss: on-state 25 dB; off-state 7 dB (0.1-2 GHz), 15 dB (0.4-1 GHz), 20 dB (1-6 GHz). Absorptive 50 Ohm.
  - Linearity at 3.3 V: P0.1dB 31 dBm, P1dB 33 dBm, IIP3 56 dBm.
  - Supply: VDD 3.0-5.4 V, IDD 0.16 typ / 0.20 max mA.
  - Control: VIH 1.15 V at VDD 3.3 V, input current under 1 uA. Truth table: A=B=Low selects RF1.
  - Power handling: 32 dBm through, 27 dBm terminated and 27 dBm hot-switch at 25 C.
  - Robustness: ESD 2 kV HBM / 1.25 kV CDM; case -40 to +105 C.
  - No negative-voltage generator, so no switch-generated spurs.
  
  At board level the chosen design is equal or better on every point we control:
  - DC blocks: our BOM sets the values. I propose 1 nF C0G, Xc 1.16 Ohm at 137 MHz. ADI's eval BOM uses 100 pF, which is 11.6 Ohm per cap at 137 MHz. With two such caps in the path that is about 0.2 dB extra IL and on-state RL near 13 dB at 137 MHz (my model). A generic board that copies that BOM would be worse at VHF-137.
  - The park load sits on-board on RF1.
  - VDD shares the MCP rail, which meets the datasheet sequence (GND, then VDD, then control). Driving A/B before VDD can forward-bias the internal ESD diodes, and a separately powered generic board does not guarantee that order.
  - Layout: 50 Ohm GCPW with via fence and EPAD vias, per ADI's applications section.
  
  Compatibility:
  - Same 2-line control on MCP23017 #1 GPB4-7, same 3.3 V rail, same truth table.
  - No new driver: MCP23017 over I2C is already in labd. Nothing changes on Ubuntu 24.04 arm64.
  - Smaller total footprint in the RF bay.
  
  Rules: the switch is a passive receive-path part, and qualification is conducted-only on the LiteVNA into loads. No loops are involved.
  
  What is not yet proven: board-level IL and isolation on 2-layer FR4. This is the reason for the condition below. The current pick is also unmeasured.
- **Rejected:**
  1.
    - **Name:** AliExpress HMC7992 SP4T board, item 3256809527409961, about $6.22-6.55 each (search snapshot only; the item page came back empty)
    - **Why:** Fails the 'not a counterfeit' requirement on price evidence. A whole board with 5 SMA jacks costs less than the authorized chip alone even at reel volume: DigiKey DE gives EUR 7.09 ex VAT, about $7.97, at qty 1,000 and EUR 11.50 at qty 1. It is the same ADI-logo design (photos viewed). An incoming LiteVNA test cannot clear it: a remarked HMC241 is pin- and truth-table-compatible, with similar IL and isolation, so it would pass the LiteVNA check while being 11 dB worse in IIP3 and 7 dB worse in P1dB, and our lab cannot measure 56 dBm IIP3. DC-block values are unknown, and with 100 pF the IL and RL at 137 MHz would be worse.
  2.
    - **Name:** AliExpress 'SPDT/SP4T RF Switch Module 100MHz-6GHz HMC7992/HMC349/ARW3235/HMC849', item 1005009856440413, about $6.69 each (snippet, unverified)
    - **Why:** In the product photos I viewed, the 'ANALOG DEVICES' logo and ADI part text are silkscreened on a board ADI does not make. That is trademark misuse, and the board is not provably genuine. Its price is also below the authorized chip cost. Flux residue is visible, and the cap values and grounding are unknown. Same untestable-linearity problem as above.
  3.
    - **Name:** AliExpress HMC7992 board, item 3256808774768321, $15.58 each for 2+ (about $31.2 for 2; about $37-39 incl. EU VAT; unverified)
    - **Why:** Not cheaper than the chosen route ($25.85 ex VAT). Provenance is unproven: a price above the qty-1 chip price only makes a genuine die more plausible, it does not prove it. Same generic board-level unknowns.
  4.
    - **Name:** AliExpress HMC7992 board, item 3256808728006825, $13.78-20.89 each (price moved between fetches; 23 sold)
    - **Why:** The price is unstable and at best only marginally below the chosen route. Same provenance and board unknowns. The low sales history gives no evidence.
  5.
    - **Name:** DIY genuine HMC7992LP3DE on a separate own 2-layer board with 5 SMA (about $41-60 for 2, estimate)
    - **Why:** Same performance as the chosen route but not cheaper, because of 10 extra SMA jacks and its own PCB. The on-injector variant supersedes it. It stays as the fallback layout.
  6.
    - **Name:** Mini-Circuits HSWA4-63DR+ (DigiKey DE EUR 6.15)
    - **Why:** Worse in insertion loss and on-state return loss (Mini-Circuits datasheet, which I read). IL is 0.9 typ / 1.1 max dB at 30-900 MHz and 1.1 / 1.35 dB at 0.9-2.1 GHz, against 0.6 / 0.9. On-state RL is 17 dB against 25 dB. It also has an internal driver whose spurs are not published, and all-low selects RF4. Better isolation (55-61 dB) does not offset this, and the user's rule forbids trading these specs.
  7.
    - **Name:** HMC241 / HMC241ALP3E boards
    - **Why:** Worse linearity: IIP3 about 45-47 dBm against 56 dBm and P1dB 26-29 dBm against 33 dBm. Also worse IL at 2 GHz, minimum isolation and on-state RL (18 against 25 dB). The old GaAs part needs 5 V. EOL or old-stock provenance.
  8.
    - **Name:** ARW3433 board (AliExpress 3256812139800248, $12.83)
    - **Why:** IL 1.00-1.10 dB at 0.1-2 GHz against 0.6 dB. Internal negative-voltage generator, so spur risk. Preliminary datasheet from an unidentified maker. Power-up state unverified.
  9.
    - **Name:** pSemi PE42540 board (AliExpress, about $22.49 each)
    - **Why:** Not cheaper. IL 0.8 typ / 1.1 max dB, worse. Charge-pump spurs. VDD max 3.55 V.
  10.
    - **Name:** pSemi PE42441 chip (own PCB)
    - **Why:** IL 0.8 typ / 1.1 max dB, worse. Terminated power +20 dBm against +27 dBm. Price not verified, 5x5 LGA, DIY only.
  11.
    - **Name:** ADI EV1HMC7992LP3D / Mini-Circuits ZSWA4-63DR+
    - **Why:** About $250-320 each, roughly 10x the price, and too large for the handheld RF bay.
  12.
    - **Name:** Manual 'connect X' SMA swapping
    - **Why:** Not an analog: it loses software selection, the 50 Ohm park at boot and labd automation, and adds connector wear. Kept only as an emergency fallback.
  13.
    - **Name:** Keep current generic boards
    - **Why:** Not chosen: likely the same ADI-logo marketplace design, so it fails the 'not counterfeit' check as photographed. Its price is unverified and probably not EU-shippable, and its DC blocks are unknown. It is the last-resort fallback only, after the LiteVNA qualification plus a marking check.
- **Confidence:** medium
- **Conditions or tests:** Accept the on-board switches only after these checks (all conducted, LiteVNA into loads/DUT only, no on-air sweeps):
  
  (1) Thru-line coupon. Put a thru-line coupon of the same trace length on the same panel and de-embed with it.
  
  (2) Insertion loss. For each used throw: IL ≤0.9 dB at 0.1-2.2 GHz after de-embedding.
  
  (3) Isolation. RFC to every off throw: ≥40 dB from 0.1 to 1.7 GHz (datasheet min). Between RTL-A throws: ≥40 dB at 137-437 MHz.
  - 37-40 dB is still no worse than the current pick's expected 30-37 dB. Accept it, but log a layout fix for v2.
  - Below 37 dB, add fence vias or a shield can and re-measure.
  
  (4) Return loss. On-state RL ≥20 dB at 137, 437, 739.5 and 1530-1710 MHz. Off throws must present a load, not an open.
  
  (5) Power-up park. With the MCP23017 in reset (outputs high-Z, 100k pull-downs), RFC must see the RF1 49.9 Ohm park, RL ≥20 dB.
  
  (6) Spurs. With the switch powered and unpowered, check RTL + tinySA at 137/437/739.5/1540-1710 MHz: no new spurs.
  
  (7) BENCH throw. If the RTL-B BENCH/sled throw must reach HF, use 10 nF C0G there and on RFC-B, and spot-check IL and isolation at 1-30 MHz. Below 100 MHz the datasheet tabulates no IL or isolation.
  
  (8) Incoming parts.
  - Chip marking must read '7992' over a 4-character lot code (ADI ordering guide branding). The earlier note 'H7992' is wrong.
  - Keep the DigiKey packing slip and CoC.
  - MSL3: bake if the bag has been open for more than 168 h before reflow.
  
  (9) Assembly. Reflow, or hotplate plus hot-air, with stencil or paste on the EPAD. This is the same process the custom boards already need for the INA3221 VQFN and TPS7A4701 VQFN-20.
  
  If a section fails after rework: build the separate-board fallback from a spare PCB of the same order (the fab minimum is 5 pcs). Only as the very last resort, buy generic boards, and then only with checks (1)-(8) plus the marking check.
- **Stack changes:** 1. BOM row 'Перемикачі входів RTL'. Old: 'Загальні плати HMC7992 SP4T x2, 30-40, маркетплейс, не перевірено'. New: 'ADI HMC7992LP3DE x2 (DigiKey 505-HMC7992LP3DE-ND), EUR 11.50 ex VAT / EUR 13.685 incl. 19% VAT each, $25.85 ex VAT for 2; verified 18 Oct 2026; on the injector PCB'. Budget fallback stays manual 'connect X'. Remove 'загальні HMC7992 з маркетплейсів' from the purchase plan and add the chips to the existing DigiKey order (shopping step 7).
  
  2. Custom PCB row. The 5-channel injector PCB gains two SP4T sections:
  - 50 Ohm GCPW on 2-layer FR4 with a solid bottom ground. Example geometry for 1.6 mm FR4: about 1.0-1.2 mm trace, 0.2 mm gap. This is a model; compute it with the fab's calculator.
  - Via fence, and at least 5 vias in the EPAD.
  - Shield-can footprint over the switch sections.
  - A thru-line coupon on the panel.
  The PCB cost class is unchanged ($10-30).
  
  3. Park correction everywhere. STACK lines 69, 194, 644, 690 and the sled row still say T4. Change them so the park load is on RF1, because A=B=Low selects RF1. The park is a 49.9 Ohm 0402 1% resistor to GND behind its own C0G block, so the SMA 50 Ohm terminators are no longer needed. Mapping: RTL-A RF1 park, RF2 VHF-137, RF3 UHF, RF4 WIDE/2 m; RTL-B RF1 park, RF2 L-band, RF3 LNB IF (after the LNB DC block and the 15/20 dB pad), RF4 BENCH/sled. labd truth tables get the same remap; no other software change.
  
  4. DC blocks.
  - 1 nF C0G 0402, rated 50 V or more, on all RTL-A pins and RFC-B.
  - 100 pF or 1 nF C0G on the L-band and IF throws.
  - 10 nF C0G 0603 on RTL-B RF4/RFC only if BENCH must reach HF.
  Do not copy ADI's 100 pF eval BOM onto the VHF path.
  
  5. Control and rails. A/B come from MCP23017 #1 GPB4/5 (RTL-A) and GPB6/7 (RTL-B), with 100k pull-downs and 100 pF to GND. VDD comes from the same 3.3 V rail as the MCP23017s, so VDD is up before the logic. Load is 0.32-0.40 mA total.
  
  6. Connectors and cabling.
  - Removed: 10 board SMA jacks and about 4-6 internal SMA jumpers.
  - Added: 2 edge SMA or U.FL for RFC-A and RFC-B out to the V4L extensions, plus 1 for the RTL-B BENCH/sled input.
  - The LNB 15/20 dB pad can become an on-board 0402 pi-pad with a selectable value, or stay an inline SMA pad with 2 jacks.
  
  7. Case and RF bay. The area of two separate boards is freed. The injector PCB grows by about 2 x 15x20 mm (model). Add a shield wall or can option over the switch sections.
  
  8. Lime (kept). Put the third HMC7992, which routes L-band ch3 to RTL-B or Lime RX1, on the same injector PCB: one more chip at EUR 11.50 inside the Lime-parts line. The extended-tier sled switch can use a spare PCB from the same order. 3-4 chips stay below DigiKey's 10-piece break (EUR 9.05).
  
  9. Authenticity list. Replace 'загальні HMC7992 з маркетплейсів — ризик сірих копій' with 'HMC7992 only from franchised distribution (DigiKey/Mouser/Farnell); marketplace boards carry ADI-logo silkscreen and below-cost pricing'.
  
  10. Datasheet notes to carry: chip marking is '7992' plus lot code; power-up order is GND, then VDD, then control; RF pins are DC-coupled; operation down to 10 kHz is stated, but IL and isolation below 100 MHz are not tabulated.
- **Sources:**
  - https://www.digikey.de/en/products/detail/analog-devices-inc/HMC7992LP3DE/5873027 (fetched 18 Oct 2026: EUR 11.50 ex VAT / 13.685 incl. VAT, breaks 10 = 9.05, 1000 = 7.08835, 4,655 in stock, Active)
  - https://www.farnell.com/datasheets/2283884.pdf (HMC7992 Rev 0 datasheet, downloaded and read: Table 1-3, truth table, power-up sequence, eval BOM 100 pF blocks, branding '7992')
  - https://www.minicircuits.com/pdfs/HSWA4-63DR+.pdf (downloaded and read: IL 0.9/1.1 dB at 30-900 MHz, 1.1/1.35 dB at 0.9-2.1 GHz, on-state RL 17 dB)
  - https://ae-pic-a1.aliexpress-media.com/kf/S8cc609f3513a4fe980d25eb31a205d56A.jpg_960x960.jpg (generic HMC7992 board photo, viewed: ADI logo silkscreen, flux residue)
  - https://ae-pic-a1.aliexpress-media.com/kf/S199d5161f8c94c998a9b92f3d80812496.jpg_960x960.jpg (multi-chip generic board photo, viewed: ADI logo on HMC7992/HMC349/HMC849 boards)
  - https://www.aliexpress.com/item/1005009856440413.html (listing, page blocked, unverified)
  - https://www.aliexpress.us/item/3256809527409961.html (page returned empty, price unverified)
  - https://www.walmart.ca/en/ip/HMC7992-Non-Reflective-SP4T-RF-Switch-Module-PCB-Material-0-1-6GHz-Frequency-Range-3V-5V-Power-Supply-45dB-Isolation-0-6dB-Insertion-Loss-58dBm-IIP3/4LT6JIAL4ULJ (current pick reference, bot wall, unverified)
  - https://lt.farnell.com/analog-devices/hmc7992lp3de/rf-switch-sp4t-silicon-6ghz-lfcsp/dp/4030607 (HTTP 503; EUR 9.78 not verified)
  - https://www.psemi.com/pdf/datasheets/pe42540ds.pdf and https://www.psemi.com/pdf/datasheets/pe42441ds.pdf (from the search candidates; not re-fetched)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_B_receivers_rf.json (park on RF1, 'prefer chips on the custom injector PCB')
  - Note: the session's WebSearch budget was exhausted, so no new search for published bench measurements of generic HMC7992 boards was possible; both earlier search angles found none.

