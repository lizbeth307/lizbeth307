# Rf sled hmc7992 sp4t pe4302 mcp23017 2 a: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_c3ba734e-52b`_

- **Part:** RF sled (extended tier, Lab extended, qty 1): HMC7992 SP4T + PE4302 0-31.5 dB DSA + MCP23017 #2 (0x21) + ADS1115 (0x48) + buck->LC->LDO LNA bias (2x TPS2553) + aluminium box with shield wall, SMA bulkheads and 1/4-20 mount, on the LAB BUS (I2C-B via TCA9517, AUX12, GND). Corrected mapping (re-audit B): RF1 = 49.9 Ohm park (A=B=Low), RF2 chain A, RF3 chain B, RF4 BENCH.
- **Current pick:** A module build: a generic marketplace HMC7992 SP4T board, a generic PE4302 module (the chip has been EOL since 2016), Adafruit 5346 (MCP23017), Adafruit 1085 (ADS1115), an unnamed buck->LC->LDO bias chain and an unnamed aluminium box of about 110x70x30 mm.
- **Current price usd:** 104-168 (STACK, unverified and not itemized). Line items:
  - Adafruit 5346: $5.95 and Adafruit 1085: $14.95 (verified by other agents).
  - Generic HMC7992 board: $13.78-20.89 (AliExpress, unverified).
  - PE4302 module: about $17.72 delivered on eBay (2025 listing) or $27.14 on Newegg. Both pages returned 403 today, so the price is unverified.
  - Bias, box, SMA, internal jumpers and LAB BUS connector: about $40-90 (estimate).
  Sum of the lines: about $92-159 ex VAT. The US/CN sellers (Adafruit, AliExpress, eBay) add EU import VAT, EUR 3 duty per tariff line, EUR 2 UHF per line from about 1 Nov 2026, and shipping (operator note 35).
- **Decision:** replace_conditionally
- **Chosen:** Sled v2: one own 2-layer 50 Ohm GCPW sled PCB carrying franchised bare chips, bought on the existing DigiKey DE order:
  - ADI HMC7992LP3DE (505-HMC7992LP3DE-ND)
  - pSemi PE4312C-Z (1046-1178-1-ND), the pin-compatible in-production successor of the PE4302
  - Microchip MCP23017-E/SO (MCP23017-E/SO-ND)
  - TI ADS1115IDGSR (296-38849-1-ND)
  
  Bias chain:
  - Pololu D36V6F6 6 V buck, placed on the far side of the box shield wall, feeding through a feedthrough capacitor / pi filter.
  - Then LC, then ADI LT3045EMSE#PBF (505-LT3045EMSE#PBF-ND) set to 4.5 V.
  - Then 2x TI TPS2553DBVR, with FAULT lines to MCP #2.
  - A small 3.3 V LDO for all logic and VDD.
  
  Box: Hammond 1590B die-cast (112.4x60.5x31 mm outside, about 107x55x27 mm inside), with a shield wall and a bonded 1/4-20 nut plate. The Hammond 1590BB (119.5x94x34 mm) is the fallback only if the layout does not fit.
  
  Merged from candidates:
  - A1's 1590BB is replaced by the 1590B.
  - A1's LT3045EDD is replaced by the LT3045EMSE, because the EDD is out of stock at DigiKey DE until 18 Jan 2027.
  - B2's claim that the PE4312 is 'not available in the EU' is wrong: DigiKey DE has 11,705 in stock.
- **Chosen price usd:** About $72-104 ex VAT (USD/EUR 1.1241).
  
  Checked today at DigiKey DE, ex VAT, qty 1, Active:
  - HMC7992LP3DE: EUR 11.50 (4,655 in stock).
  - PE4312C-Z: EUR 3.86 cut tape (11,705 in stock).
  - MCP23017-E/SO: EUR 1.42 (13,353 in stock).
  - ADS1115IDGSR: EUR 4.64 (36,903 in stock).
  - Chip subtotal: EUR 21.42 = $24.08 (EUR 25.49 / $28.65 with 19% VAT).
  - LT3045EMSE#PBF: EUR 8.78 (16,667 in stock).
  - 2x TPS2553DBVR: EUR 2.04 (stock not shown).
  - Hammond 1590B: EUR 10.22 (VAT basis not shown, assumed ex VAT).
  - Subtotal for the lines checked today: EUR 42.46 = $47.73.
  
  Other priced lines:
  - Pololu D36V6F6: $5.95 at Pololu US (verified). The EU-distributor price is not verified.
  
  Estimated, not verified:
  - PCB: $2-9 (JLCPCB $2 for 5 pcs per G3, plus a share of shipping and a possible EUR 3 duty line).
  - 5-6 SMA jacks: $10-25.
  - Passives, 49.9 Ohm park, C0G blocks, 10k resistors, 3.3 V LDO and shield fence: $3-8.
  - Locking 6-pin LAB BUS connector: $3-8 (needed by both builds).
  
  DigiKey DE is DDP, with VAT added at checkout.
- **Saving usd:** On the like-for-like electronics lines (ex VAT), about $17-41: modules at $52.40-68.93 against chips $24.08 + PCB $2-9 + about $2 of extra passives. The real saving is larger, because the DIY board also removes 4-6 internal SMA jumpers and the RF1 50 Ohm SMA terminator of the module build; those are not priced. For the whole sled it is about $20-60 (model): $72-104 against $104-168 (STACK, unverified). It is more once EU landed costs are counted on the Adafruit, AliExpress and eBay lines (VAT, EUR 3 per line duty, UHF, shipping), which DigiKey DE DDP avoids. Not guaranteed: SMA, PCB and connector costs are estimates on both sides.
- **Equivalence proof:** I tried to prove each part worse.
  
  SWITCH
  - Same HMC7992 die as the current board, from a franchised channel. Chip specs are identical (datasheet Rev 0, read by G1):
    - Range 0.1-6 GHz.
    - IL 0.6 typ / 0.9 max dB.
    - Isolation 40 min / 45 typ dB at 0.1-2 GHz.
    - On-state RL 25 dB; off-state RL 7 dB at the low end, the same die-level weakness for both builds.
    - P0.1dB 31 dBm, P1dB 33 dBm, IIP3 56 dBm.
    - No negative-voltage generator. A=B=Low selects RF1. VIH 1.15 V.
  - The board is equal or better: 1 nF C0G blocks on all five RF pins (generic boards likely copy ADI's 100 pF eval BOM, which costs about 0.2 dB and gives RL about 13 dB at 137 MHz), an on-board RF1 park, and VDD on the logic rail so VDD comes up first.
  - Below 100 MHz the switch is unspecified on both builds (same die).
  
  ATTENUATOR: PE4312, datasheet DOC-81482-4.01 (06/2026), read by me
  - Range 1 MHz-4 GHz, 0.5 dB steps to 31.5 dB, monotonic to 4 GHz.
  - IL: 1.3 typ / 1.5 max dB below 1 GHz; 1.5 / 1.8 dB at 1-2.2 GHz.
  - Error: ±(0.10+1%) at 1 MHz-1 GHz and ±(0.15+2%) at 1-2.2 GHz.
  - RL 14 min / 18 typ dB at 1-2.2 GHz.
  - IIP3 59 dBm, P0.1dB 30 dBm.
  - RF input +24 dBm CW above 50 MHz (derated at 1-50 MHz); absolute max +30 dBm.
  - Switching 500 ns, with safe state transitions (no output power spikes).
  - VDD 2.3-5.5 V at 130 uA. Logic VIH 1.17 V, max 3.6 V.
  - Power-up state is selectable (latched parallel with LE=0 and PUP1=PUP2=1 gives 31.5 dB).
  - Charge-pump spur -140 dBm typ; a bypass mode with -3.3 V on pin 12 makes it spur-free.
  - ESD 1500 V HBM / 250 V CDM. MSL1. Pin-compatible with the PE4302.
  
  PE4302 reference figures: IL 1.5 / 1.75 dB at DC-2.2 GHz, ±(0.10+3%) and ±(0.15+5%) accuracy, IIP3 52 dBm, P1dB 30 dBm. These come from the candidate's search snippet; pSemi's pe4302ds.pdf now returns 404, so I could not re-read them.
  - Silicon Chip measured the module at 1-1.5 dB IL below 2.5 GHz, with accuracy good only to about 1.5 GHz.
  - The module is wired direct-parallel with LE high and PUP grounded, so it powers up at 0 dB, which is unsafe.
  
  Result for the attenuator:
  - Better in accuracy, IIP3, switching, safe transitions, power-up state, supply range and production status.
  - Equal in range, steps and typical IL.
  - The only paper deficit is max IL at 1-2.2 GHz: 1.8 against 1.75 dB (+0.05 dB). It is offset at system level, because the integrated board deletes the module build's switch-to-DSA SMA jumper and two jacks. It is also closed by acceptance test (3) below, so it is not traded silently.
  - Power handling is irrelevant here: sources are ≤-40 dBm, and both parts are rated ≥+24 dBm.
  
  MCP23017 and ADS1115
  - Same dies as the Adafruit boards. Franchised provenance, same addresses and register maps, smbus2 with no kernel driver on Ubuntu 24.04 arm64.
  
  BIAS
  - The current chain is unnamed, so I prove it by spec, not by part. D36V6F6 (Pololu page read): 6 V ±4%, 600 mA, 6.2-50 V input, fixed 2.1 MHz, <0.1 mA quiescent, OCP and OTP, no reverse protection. Light-load behaviour and efficiency are not published as numbers.
  - LT3045: 500 mA. Set to 4.5 V it has 1.26 V or more of headroom, enough for its PSRR at 2.1 MHz. Dissipation is about 0.54 W at 0.36 A.
  - Sled draw from AUX12 is about 0.21 A, inside the 0.42 A budget.
  
  BOX
  - Die-cast aluminium. It is smaller than the planned box (55 mm against about 64 mm inside width), so fit is a condition.
  
  RULES
  - Passive receive path; conducted-only BENCH at ≤-40 dBm; no TX parts; no loops; every chip franchised.
- **Rejected:**
  1.
    - **Name:** Candidate A1 as written (1590BB box, LT3045EDD)
    - **Why:** The substance survives and is merged into the chosen build. Two parts change. The LT3045EDD#PBF is out of stock at DigiKey DE (121 due 18 Jan 2027) and its price is EUR 8.78, not the claimed $7.84. The 1590BB (119.5x94x34 mm) exceeds the planned 110x70x30 mm envelope, while the 1590B at EUR 10.22 is cheaper and closer to it.
  2.
    - **Name:** Candidate B2 hybrid: DIY board plus the generic PE4302 module on an SMA jumper
    - **Why:** Its premise is false: the PE4312 is not unobtainable in the EU (DigiKey DE: EUR 3.86, 11,705 in stock, Active). Against the full DIY build it is worse in five ways: an EOL chip of unprovable provenance, a 0 dB (unsafe) power-up, lower accuracy and IIP3, an extra jumper with its IL, and about $13-23 more cost.
  3.
    - **Name:** PE4312C-Z from LCSC ($2.24)
    - **Why:** LCSC's franchise status with pSemi is not verified, so it breaks the counterfeit rule, and the saving over DigiKey DE is only about $2. Buy from DigiKey, Mouser or RFMW only.
  4.
    - **Name:** pSemi PE42441 SP4T ($3.68, RFMW US)
    - **Why:** Worse IL: 0.8/1.1 dB against 0.6/0.9. VDD max is 3.55 V and terminated power is +20 against +27 dBm (G1). It is a US-only seller (EU duty and VAT apply). A spec trade, so it is not an analog.
  5.
    - **Name:** pSemi PE42442 SP4T ($2.63, RFMW US)
    - **Why:** Worse IL by 0.25-0.5 dB and a -120 dBm charge-pump spur. Its truth table selects RF4 on 000, so it needs 3 lines and a park remap. Better isolation does not offset a loss the rule forbids.
  6.
    - **Name:** pSemi PE43711B-Z DSA ($7.31)
    - **Why:** IL 1.6/1.85 dB at 1-2.2 GHz exceeds the 1.75 dB reference, the fixed error below 1 GHz is worse (0.15 against 0.10 dB), it is not pin-compatible, and it costs more than the PE4312.
  7.
    - **Name:** Seeed Grove ADS1115 module (about $12, UK sellers)
    - **Why:** Saves only $1-3 against the Adafruit 1085 in a module build. Address and pull-ups are unverified (they must suit the '4.7k on the sled side only' rule) and it needs a Grove adapter. UK sellers add EUR 3 per line duty and VAT. It is beaten by the EUR 4.64 bare chip.
  8.
    - **Name:** Generic marketplace HMC7992 boards (AliExpress $6.22-20.89, Walmart.ca)
    - **Why:** They carry ADI-logo silkscreen on a board ADI does not make, some are priced below the authorized chip cost, and no measurement exists. Their DC blocks are unknown (likely 100 pF, worse at 137 MHz). A remarked HMC241 would pass a LiteVNA check with 11 dB lower IIP3. Fails the counterfeit rule (G1).
  9.
    - **Name:** Generic PE4302 modules (eBay, Banggood, Newegg)
    - **Why:** The chip has been discontinued since 2016, so any module carries old-stock or remarked silicon. It powers up at 0 dB. Prices could not be re-verified (403).
  10.
    - **Name:** Generic HMC472 6-bit DSA module
    - **Why:** Measured worse by Silicon Chip: IL up to 2.5 dB at 2.64 GHz, accuracy ±(0.35+5%), top frequency 3.8 GHz, 5 V logic. Not cheaper.
  11.
    - **Name:** Generic 'LF-6 GHz 0.25 dB' DSA module (suspected HMC1119)
    - **Why:** No measurement, the chip identity is unconfirmed, the interface is unknown, and it is dearer than the PE4312.
  12.
    - **Name:** Used Mini-Circuits ZX76-31R5-PP-S+
    - **Why:** Datasheet: IL 1.5-2.0 dB typ, upper limit 2.4 GHz, IIP3 +52 dBm, ESD 500 V HBM. Used condition is unknown and there are US/CN import costs. Worse in IL and range.
  13.
    - **Name:** RUDAT-6000-30, USB-SP4T-63, EV1HMC7992LP3D, ZSWA4-63DR+
    - **Why:** $175 to over $300 each, far dearer than the whole sled. They use USB control instead of the LAB BUS.
  14.
    - **Name:** Generic ADS1115 breakouts
    - **Why:** 12-bit ADS1015 relabels are documented (16-count steps, four LSBs stuck at zero; TI E2E and Arduino forum). Provenance cannot be proven.
  15.
    - **Name:** Generic LT3045 / MP1584 / LM2596 regulator modules, CJMCU MCP23017 boards
    - **Why:** No measured noise or ripple data. A documented precedent: a fake LM2596 switched at about 28 kHz instead of 150 kHz (EEVblog). Spur risk into the 137-1710 MHz chains.
  16.
    - **Name:** Manual SMA swaps
    - **Why:** Not an analog. It loses software path selection, the boot-time 50 Ohm park, scripted 0.5 dB sweeps and labd logging, and adds connector wear.
  17.
    - **Name:** Keep the current module build
    - **Why:** Its two RF modules fail the counterfeit/EOL rule as specified (G1, re-audit B). It costs more, and it is no better in any spec than the qualified DIY build. It is kept only as the last-resort fallback after the marking check and VNA qualification.
- **Confidence:** medium
- **Conditions or tests:** Accept Sled v2 only after these tests. All are conducted, with the LiteVNA into loads or a DUT only, never on air.
  
  (1) Calibration: de-embed with a thru-line coupon on the same panel.
  
  (2) Switch:
  - IL ≤0.9 dB per throw at 0.1-2.2 GHz.
  - Isolation from RFC to each off throw ≥40 dB target, ≥37 dB accept, at 0.1-1.7 GHz. 37 dB still beats the module's expected 30-37 dB; below 37 dB, add fence vias or a can and re-measure.
  - On-state RL ≥20 dB at 137, 437, 739.5 and 1530-1710 MHz.
  - With the MCP in reset, the RF1 park reads RL ≥20 dB.
  
  (3) PE4312, de-embedded:
  - 0 dB-state IL ≤1.5 dB below 1 GHz and ≤1.75 dB at 1-2.2 GHz. This closes the +0.05 dB paper gap to the PE4302.
  - All 64 states swept from 1 MHz to 2.2 GHz: monotonic, error within ±(0.15+2%), correction table stored.
  
  (4) Whole BENCH path (BENCH -> DSA at 0 dB -> switch -> RFC): IL ≤2.65 dB at 2.2 GHz.
  
  (5) Power-up: with the MCP in reset, the DSA reads 31.5 dB and the switch sits on RF1.
  
  (6) Bias:
  - 4.5 V ±2% from 0 to 0.4 A.
  - Efficiency ≥85% at 0.36 A from AUX12 (INA readings).
  - TPS2553 trip and FAULT verified.
  - Spur check with the tinySA and RTL-B at the bias-tee outputs: at 137, 437, 739.5 and 1540-1710 MHz and at multiples of 2.1 MHz, with bias on/off and LNAs loaded or unloaded (light load included). No new spurs above the RTL floor. If the PE4312 charge-pump spur shows, use bypass mode with -3.3 V on pin 12.
  
  (7) Leak rule: BENCH source ≤-40 dBm with RF2/RF3 loaded; record the leak.
  
  (8) Incoming parts:
  - HMC7992 marking '7992' plus lot code; PE4312 marking per the pSemi marking spec.
  - Keep the DigiKey packing slips.
  - HMC7992 is MSL3: bake if the bag has been open more than 168 h. PE4312 is MSL1.
  - ESD handling (PE4312 CDM rating is 250 V).
  
  (9) Fit: the PCB must be ≤100x48 mm, with the shield wall, 5-6 SMA and the LAB BUS connector fitting the 1590B. If not, use the 1590BB.
  
  (10) Failure path: if the board fails after one rework, rebuild on a spare PCB. If that fails too, revert to the current module build with a marking check and full VNA qualification.
  
  Not verified:
  - PE4302 datasheet values (pSemi 404) and PE4302 module price (eBay/Newegg 403).
  - D36V6F6 efficiency and light-load mode.
  - 1590B VAT basis, SMA/PCB/connector costs, TPS2553 stock.
  
  The shared WebSearch budget was exhausted after one query, so only direct fetches were used.
- **Stack changes:** 1. BOM sled row: replace the module build with Sled v2 (parts and DigiKey DE numbers as chosen), about $72-104 ex VAT. Remove the marketplace HMC7992 board, the PE4302 module, the second Adafruit 5346 and the Adafruit 1085 from the extended purchase. Add the chips, LT3045EMSE, TPS2553 and 1590B to the DigiKey DE order (shopping step 7). Buy the D36V6F6 from an EU Pololu distributor (e.g. Botland or TME) to avoid duty.
  
  2. Fix the sled text in STACK:
  - RF1 is the 49.9 Ohm park (A=B=Low), RF2 chain A, RF3 chain B, RF4 BENCH. It was 'RF4 50 Ohm'.
  - The HMC7992 has 2 control lines (A/B), not V1-V3.
  - PE4302 is replaced by PE4312.
  
  3. PE4312 wiring:
  - Latched parallel: P/S low, LE on an MCP #2 output with a 100k pull-down (it overrides the internal 2 MOhm pull-up).
  - PUP1 and PUP2 to 3.3 V via 10k, for a 31.5 dB start.
  - 10k series on pin 1 (C16); pin 3 (Data) to GND via 10k; pin 12 to GND.
  - RF pins at 0 VDC behind C0G blocks.
  - labd: write the C bits, then pulse LE. No driver change.
  
  4. MCP #2 line budget is 14 of 16:
  - Outputs: A, B, 6 C bits, LE, NOISE EN, LNA EN1, LNA EN2.
  - Inputs: FAULT1, FAULT2, not on GPA7/GPB7.
  
  5. Sled rails:
  - AUX12 -> D36V6F6 6 V (behind the shield wall) -> feedthrough/pi filter -> LC -> LT3045 at 4.5 V -> 2x TPS2553 (RILIM 88.7k).
  - A small 3.3 V LDO feeds HMC7992, PE4312, MCP23017, ADS1115 and the 4.7k I2C pull-ups, so VDD comes up before logic.
  - Add an input reverse-polarity guard (the Pololu board has none).
  
  6. DC blocks: 1 nF C0G on RFC, RF2 and RF3; 10 nF C0G on RF4/BENCH if HF bench work is needed. HF below 100 MHz stays unspecified until swept.
  
  7. Box: Hammond 1590B with a milled shield wall or a PCB tinplate fence, SMA bulkheads or edge jacks through the walls, and a bonded or bolted 1/4-20 nut plate (the die-cast floor is too thin to tap). The 1590BB is the fallback.
  
  8. PCB: a third design (≤100x100 mm) on the JLCPCB order with the power and injector boards. Spares from the 5-piece lot serve as the rework fallback. Budget a possible extra EUR 3 duty line.
  
  9. Authenticity list: PE4302 modules are EOL and not provable. The PE4312 comes only from franchised distribution. Marketplace HMC7992 boards are rejected.
  
  10. No change to I2C addresses (0x21, 0x48), the TCA9517 LAB BUS, Ubuntu 24.04 arm64 drivers (smbus2), the AUX12 budget (sled about 0.21 A of 0.42 A) or the receive-only, conducted-only rules.
- **Sources:**
  - https://www.psemi.com/pdf/datasheets/pe4312ds.pdf (read 18 Oct 2026, DOC-81482-4.01, 06/2026: Tables 1-5 and 9, MSL1, ordering PE4312C-Z)
  - https://www.psemi.com/pdf/datasheets/pe4302ds.pdf (HTTP 404 on 18 Oct 2026; PE4302 figures unverified)
  - https://www.digikey.de/en/products/result?keywords=PE4312C-Z (1046-1178-1-ND, EUR 3.86 CT, 11,705 in stock, Active)
  - https://www.digikey.com/en/products/result?keywords=PE4312C-Z ($4.40, 11,705, Active, 16-week lead time)
  - https://www.digikey.de/en/products/detail/analog-devices-inc/HMC7992LP3DE/5873027 (EUR 11.50 / 13.685 incl. VAT, 4,655, Active)
  - https://www.digikey.de/en/products/detail/texas-instruments/ADS1115IDGSR/2231567 (EUR 4.64 / 5.5216 incl. VAT, 36,903)
  - https://www.digikey.de/en/products/result?keywords=MCP23017-E%2FSO (EUR 1.42, 13,353 in stock)
  - https://www.digikey.de/en/products/result?keywords=LT3045EMSE%23PBF (EUR 8.78, 16,667 in stock)
  - https://www.digikey.de/en/products/result?keywords=LT3045EDD%23PBF (EUR 8.78, out of stock, 121 due 18 Jan 2027)
  - https://www.digikey.de/en/products/result?keywords=TPS2553DBVR (EUR 1.02, stock not shown)
  - https://www.digikey.de/en/products/result?keywords=1590B (Hammond 1590B EUR 10.22)
  - https://www.hammfg.com/files/parts/pdf/1590B.pdf (112.4x60.5x31 mm, inside 107.05x55.45x27 mm, die-cast aluminium)
  - https://www.pololu.com/product/3793 (D36V6F6: $5.95, 6.2-50 V input, 6 V ±4%, 600 mA, fixed 2.1 MHz, no reverse protection)
  - https://siliconchip.com.au/Issue/2018/June/El+Cheapo+Modules+17%3A+4GHz+digital+attenuator (PE4302 module: 1-1.5 dB IL below 2.5 GHz, accuracy good to about 1.5 GHz, direct parallel with PUP grounded)
  - https://www.farnell.com/datasheets/2283884.pdf (HMC7992 Rev 0, read by G1)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/analogs_G1_receivers_rf.json (HMC7992 decision, generic-board rejection)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/analogs_G3_power_gnss_imu.json (LT3045EMSE choice, JLCPCB $2 per 5 pcs)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_B_receivers_rf.json (PE4302 EOL, RF1 park)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (items 34-35, EU landed cost)
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md (sled row line 365, MCP #2 line 647)

