# Adafruit mcp23017 5346 0x20 outputs 0x22: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_071e1025-145`_

- **Part:** GPIO expanders x2 (D13): #1 at 0x20 drives the enables; #3 at 0x22 reads FAULT/PG/sense inputs, with GPA7/GPB7 as outputs. They sit on Q6A I2C2 (pins 27/28, 100 kHz, behind the UM3204H), with INT mirrored open-drain to pin 5. Both run from the Q6A 3.3 V rail, have 100k pull-downs on every line, and are driven by labd through smbus2.
- **Current pick:** Adafruit MCP23017 breakout PID 5346 x2. From the Eagle schematic, the chip is an MCP23017 in the ML (QFN) package. The board has 10k pull-up arrays on SDA/SCL/RESET and on INTA/INTB, 10k pull-downs on A0-A2 with jumpers to VCC, decoupling of 0.1 uF + 2x10 uF, and a power LED with a 10k resistor that can be cut at SJ1. It measures 43x18 mm and has 2x STEMMA QT connectors (cables not included).
- **Current price usd:** 11.90 for 2 ($5.95 each; $5.36 at 10-99). Adafruit page re-fetched 18 Oct 2026: in stock. US price with no EU import VAT; it rides the Adafruit bring-up order.
- **Decision:** replace_conditionally
- **Chosen:** 2x genuine Microchip MCP23017-E/SO (SOIC-28 wide), bought from DigiKey (authorized) in the DigiKey order the stack already places, and fitted on the stack's own 2-layer power PCB (the 'Власні PCB' line, still at model status). Per chip: 100 nF at VDD plus 10 uF bulk; RESET through 10k to the Q6A 3V3 net; A2..A0 hard-tied (000 = 0x20, 010 = 0x22, no resistors); INTA/INTB mirrored open-drain to header pin 5. Add one DNP pair of footprints for 10k SDA/SCL pull-ups. Keep the existing 100k pull-downs on the same board. VDD comes only from the Q6A header 3.3 V net, never from a board-local 3.3 V. FALLBACK: if the power PCB is already frozen or ordered, or the bench conditions below fail, KEEP the Adafruit 5346 x2. No cheaper ready-made module was shown to be not-worse.
- **Chosen price usd:** About 3.6-3.9 for 2. Chips are $3.24 (DigiKey MCP23017-E/SO-ND: $1.62 at qty 1, $1.35 at 25, $1.247 at 100; 13,353 in stock; Active; tube; verified 18 Oct 2026). Passives are about $0.4-0.6 (estimate, unverified). EU VAT is added at DigiKey checkout (DDP). There is no extra shipping because it rides the existing DigiKey order (PEC11R, KSC641J, ferrites). It adds no PCB fab cost if it is laid out before the power-PCB order and the board stays within the fab's price-step size.
- **Saving usd:** About 8.0-8.3 ex VAT ($11.90 - $3.24 - $0.4-0.6 passives). About 9.6-10 EU-landed at 19-21% VAT, since the Adafruit lines would also have drawn import VAT. If you also buy 1 spare chip (+$1.62) and/or 1 MCP23017-E/SP DIP for breadboard labd bring-up before the power PCB exists (+$1.69, DigiKey, 8,127 in stock, verified), the saving falls to about $4.7-6.6. Possible extra saving: 2 STEMMA QT cables at $0.95 each, if they were budgeted (not confirmed in the BOM).
- **Equivalence proof:** Same die and the same datasheet (Microchip DS20001952D, which applies to the SO, SS, SP and ML packages alike). The Adafruit 5346 is this chip in QFN. Spec by spec, the bare chip is equal or better:
  (1) 16 I/O; GPA7/GPB7 output-only on both, and D13 already allows for it.
  (2) Addresses 0x20-0x27: 0x20 and 0x22 reachable with no clash with 0x21, 0x48 or 0x30.
  (3) VDD 1.8-5.5 V; -40..+85 C at 3.3 V for both (E grade, +125 C only at 4.5-5.5 V).
  (4) POR state (safety-critical) identical: IODIR = 1111 1111, GPPU = 0000 0000, so every enable is held off by the 100k pull-downs at boot and while the Q6A is off.
  (5) INT latch identical: 'interrupt will only be cleared if the associated GPIO or INTCAP is read'; mirror and open-drain are set via IOCON.
  (6) Drive identical: 25 mA per pin abs max; VDD 125 mA; VSS 150 mA; VOL 0.6 V at 8 mA; VOH VDD-0.7 at -3 mA.
  (7) ESD identical (4 kV HBM / 400 V MM). Adafruit adds no TVS, so board-level ESD is also equal.
  (8) Schmitt inputs 0.2/0.8 VDD; 1 uA max standby.
  (9) Identical register map, so labd/smbus2 needs no change and Ubuntu 24.04 arm64 is unaffected (userspace; PINCTRL_MCP23S08 still not needed).
  (10) Authorized channel (DigiKey) gives the same counterfeit protection as Adafruit.
  Better in three ways:
  (a) No hard-wired 10k I2C pull-ups. Two 5346 boards add 5k in parallel behind the UM3204H's own 10k, against the stack's 'no pull-ups below 10k on the header side' rule. The PCB fits at most one 10k pair, and only if the rise-time test needs it.
  (b) Lower quiescent current. The A-pins are direct-tied, so the 0.33 mA through the Adafruit #3 A1 jumper/10k pull-down goes away, and there is no LED.
  (c) Two friction-fit JST-SH (STEMMA QT) joints and about 18 flying enable wires are replaced by on-board traces next to the load switches, plus one 5-wire harness (3V3_Q6A, GND, SDA, SCL, INT).
  Not worse in build quality: SOIC-28 at 1.27 mm pitch on a fabricated PCB is the same construction class as the Adafruit board.
  Trade I am naming, not hiding: field swap becomes hot-air rework rather than a module swap. Mitigations are a $1.62 spare chip and, optionally, 0.1 in header pads on the power PCB that accept an Adafruit 5346 as a fallback.
  CONDITIONS / BENCH TESTS (all must pass; otherwise keep the 5346):
  (i) Layout is done before the power PCB is ordered (it is at model status today).
  (ii) The expanders sit at least 15-20 mm from the TPS7A4701s, PTCs and buck inductors. In the sealed-case thermal test, board temperature near the chips stays at or below 75 C (85 C rating at 3.3 V). I2C traces are kept away from the switch nodes.
  (iii) Boot test: Q6A off with LAB5/SYS12/pack live, then 20 warm + 20 cold Q6A boots. Every enable (LNB, Boni, AUX12, VBUS x4, LNA ch1-4, relays, HMC7992 A/B) stays below 0.4 V on a scope, with no glitch.
  (iv) I2C2 at 100 kHz, measured at the chips: rise time at or below 1000 ns and VOL at or below 0.4 V. Then 1e6 read/compare cycles with zero errors while LNB 13.2 V, AUX12 and LAB5 are loaded. Fit the 10k pull-up pair only if the rise time fails.
  (v) A 10 us FAULT pulse on a 0x22 input asserts pin 5 and stays latched until INTCAP is read.
  (vi) The labd expander unit tests pass unchanged.
  (vii) No back-power: with the Q6A off, there is no voltage on 3V3_Q6A from FAULT/PG pull-ups. Those pull-ups go to 3V3_Q6A only.
- **Rejected:**
  1.
    - **Name:** Microchip MCP23017T-E/SS (SSOP-28, cut tape) on the power PCB
    - **Why:** Same silicon, so not worse in specs, but dominated: search A lists it at $1.69 each (not re-verified by me), more than the $1.62 -E/SO. Its 0.65 mm pitch is also harder to hand-solder and inspect than SOIC's 1.27 mm.
  2.
    - **Name:** MCP23017-E/SP (DIP-28) on hand-wired perfboard
    - **Why:** Electrically identical ($1.69, DigiKey, 8,127 in stock, verified), but build quality is worse: perfboard wiring and sockets in a handheld that sees vibration and cold. Acceptable only as a bench chip for labd bring-up, not in the build.
  3.
    - **Name:** Waveshare MCP23017 IO Expansion Board 15391 x2
    - **Why:** Waveshare schematic checked myself. RESET is not broken out (10k/100 nF RC only). Decoupling is 100 nF only, versus 0.1 uF + 2x10 uF. The 10k I2C pull-ups are hard-wired. The A0-A2 pull-ups are 10k to VCC with jumpers to GND, so 0x20/0x22 draws about 1.65 mA, versus about 0.33 mA on the Adafruit pair (+1.3 mA). The product page claims an 'onboard voltage translator' that the schematic does not show, a documentation-quality red flag. Stock is not stated on the page. The saving is only $1.12 for 2 ($5.39 at the qty-2 tier, layout ambiguous) before shipping. Worse in several specs.
  4.
    - **Name:** Soldered 333007 IO expander MCP23017 breakout (Reichelt DEBO IO EXPANDER)
    - **Why:** EUR 4.40 incl. VAT (about $4.95), but Reichelt shows 'Available on 10/26/2026', so not in stock. Defaults to 5 V through an on-board regulator, so running at the Q6A 3.3 V needs the JP4 bypass bridged and JP3 cut. It has two pull-up sets (JP1 5 V, JP2 3.3 V, normally closed) of undocumented value, and its RESET and decoupling networks are undocumented. Default 0x27 needs jumper work. Reichelt shipping is EUR 5.95 with no other Reichelt order in the stack, and the soldered.com direct price could not be fetched (HTTP 429). Not provably not-worse, and dominated by the bare chip.
  5.
    - **Name:** DFRobot Gravity DFR0626
    - **Why:** $5.90, only $0.05 less per board, so shipping erases it. 44x32 mm, much larger than 43x18. The address is set by a DIP switch, mechanical contacts in a vibrating handheld. Stock is unclear (the page FAQ asks whether it is discontinued). RESET breakout is not mentioned, and the schematic was not checked.
  6.
    - **Name:** TI TCA9535PWR (STACK D13 'budget alternative')
    - **Why:** Worse. INT is not latched: the TI datasheet says 'Resetting the interrupt circuit is achieved when data on the port is changed to the original setting', so short FAULT/PG pulses are lost. No RESET pin. ESD is ±2000 V HBM / ±1000 V CDM versus 4 kV HBM. IOH is 10 mA. labd must be rewritten. At $2.00 (DigiKey, per search A/B) it also costs more than the $1.62 MCP23017-E/SO. STACK.md should relabel it 'spec trade', not 'budget'.
  7.
    - **Name:** NXP PCAL9535A (TSSOP/HWQFN)
    - **Why:** ESD is 2 kV HBM versus 4 kV. Different register map, so labd must be rewritten and the power-on all-off behavior re-tested. At $2.51-2.66 (DigiKey per search A; not re-verified) it is dearer than the $1.62 bare MCP23017.
  8.
    - **Name:** NXP PCAL6416A / 16-bit single-ADDR-pin expanders
    - **Why:** PCAL6416A datasheet checked: one ADDR pin gives 'one of the two possible slave addresses' (0x20/0x21). It cannot sit at 0x22, and 0x21 collides with sled MCP23017 #2. TCAL6416 is assumed similar but was not checked.
  9.
    - **Name:** TCA9555 / PCA9555 / CAT9555 (bare or modules)
    - **Why:** Fails the safety rule. Internal 100k pull-ups are always active on inputs, so against the 100k pull-downs every enable sits near VCC/2 from POR until labd runs. No RESET.
  10.
    - **Name:** PCF8575 / PCF8574 (incl. Adafruit 5611)
    - **Why:** Fails the safety rule. TI SCPS121I says 'At power on, the I/Os are high', so every enable would turn on at boot. Quasi-bidirectional, with no RESET.
  11.
    - **Name:** Adafruit AW9523 4886
    - **Why:** Adafruit states that the default is all pins as outputs, set LOW, so pins are not high-Z at POR and contend with the push-pull PG/FAULT inputs on the input chip. No INTCAP-style latch, a different register map, and no per-pin current spec.
  12.
    - **Name:** MCP23018
    - **Why:** Open-drain outputs only (no push-pull high), so enables would need pull-ups, which breaks the pull-down boot-off scheme. Rejected on spec from part-family knowledge; the datasheet was not re-read in this step and the part was not priced.
  13.
    - **Name:** Generic AliExpress/marketplace MCP23017 modules (CJMCU-2317 type)
    - **Why:** Not priced. Chip provenance cannot be shown to be genuine or authorized, and pull-up and decoupling values are unknown (possibly 4.7k, which breaks the 10k rule). The WebSearch budget was used up, so no listing or counterfeit report was checked. Rejected for lack of evidence and authenticity.
  14.
    - **Name:** Same Adafruit 5346 from EU sellers (Berrybase EUR 5.90, Botland EUR 7.99, The Pi Hut GBP 5.70)
    - **Why:** Identical part, but per searches A/B it is out of stock (Berrybase, Botland) or not cheaper in USD (Pi Hut $7.59). I did not re-verify these. It remains only the module fallback source.
  15.
    - **Name:** Reichelt MCP23017-E/SO bare chip, EUR 1.49 incl. VAT (in stock, verified)
    - **Why:** Cheapest per chip ($1.41 net), but EUR 5.95 shipping with no other Reichelt order in the stack cancels it, and Reichelt's status as a Microchip-franchised distributor is unverified. Use DigiKey (authorized, existing order). TME lists it at $1.35 but 'not available for sale in your country' / 0 stock.
- **Confidence:** high
- **Conditions or tests:** Replace ONLY if both hold: (1) the power PCB is still unordered, so the two SOIC-28W footprints, passives and DNP pull-up pads can be added; (2) bench tests (iii)-(vii) from the equivalence proof pass on the first power-PCB build: boot-glitch test over 20 warm + 20 cold boots, I2C rise time/VOL plus 1e6 zero-error reads under load, a 10 us FAULT latch test, unchanged labd unit tests, and a no-back-power check. Also, (ii): at or below 75 C near the chips in the sealed-case thermal test. If the power PCB is frozen or ordered, or any test fails, keep the Adafruit 5346 x2 ($11.90). Optional but recommended: 1 spare MCP23017-E/SO ($1.62), and 1 MCP23017-E/SP DIP ($1.69) so labd can be developed on a breadboard before the power PCB exists. Buy from DigiKey only.
- **Stack changes:** BOM (D13 'Розширювачі GPIO'): Adafruit 5346 x2 $11.90 becomes MCP23017-E/SO x2 on the power PCB, about $3.6-3.9 incl. passives, sourced from DigiKey (verified). The Adafruit bring-up order (order-plan step 2) drops 2x MCP23017 (about $104.95 to about $93.05 before VAT). The DigiKey order (step 7) adds 2x MCP23017-E/SO (+1 spare, +1 DIP dev chip optional). The 'Budget: TCA9535' note should read 'TCA9535 = spec trade (no INT latch, no RESET, 2 kV ESD); not a not-worse alternative'.
  Power PCB: add 2x SOIC-28W (about 18x12 mm each incl. pads) plus 2x 100 nF, 2x 10 uF, 2x 10k RESET pull-ups and a DNP 10k SDA/SCL pair; area estimate +6-8 cm2. RESET may optionally go to a Pico GPIO through an open-drain stage, so the supervisor can force every enable off if labd hangs (pull-ups to 3V3_Q6A only). Fit the HMC7992 A/B 1 kOhm series resistors and 100 pF on the power PCB, or route 3V3_Q6A to the switch boards, per reaudit B. Give the board a 5-pin input connector: 3V3_Q6A, GND, SDA, SCL, INT.
  Harness/case: remove 2 STEMMA QT cables, 2 module mounts (4x M2.5 holes each, 43x18 mm) and about 18 flying enable wires; add one short 5-wire harness from header pins 1/17, 27/28, 5 and GND.
  Rails: unchanged. Power still comes from the Q6A 3.3 V, so 'Q6A off means all enables off' still holds. Idle draw falls by about 0.33-0.46 mA.
  Pinout and addresses: unchanged (I2C2 27/28, 0x20/0x22, INT on pin 5).
  Drivers and software: none. Same register map; smbus2 userspace on Ubuntu 24.04 arm64; GPIO_PCA953X still unused for these.
  Side finding for both options: with the 5346 boards the header-side I2C pull-ups total 5k, plus the UM3204H's own 10k, which breaks the stack's own 'no pull-ups below 10k on the header side' rule. The bare-chip build fixes this by construction.
  Consistency (optional, outside this part): sled MCP23017 #2 (0x21) can use the same bare chip on the sled PCB.
  Hard rules: receive-only, conducted-only, no loops and no private-content decoding are unaffected (digital control part).
- **Sources:**
  - https://www.digikey.com/en/products/detail/microchip-technology/MCP23017-E-SO/894271 (fetched 18 Oct 2026: $1.62 qty 1, $1.35 qty 25, $1.247 qty 100, 13,353 in stock, Active)
  - https://www.digikey.com/en/products/detail/microchip-technology/MCP23017-E-SP/894272 (fetched: $1.69, 8,127 in stock, Active)
  - https://www.adafruit.com/product/5346 (fetched: $5.95, in stock, tiers $5.36/$4.76, 43x18x5 mm, STEMMA QT cable not included)
  - https://github.com/adafruit/Adafruit-MCP23017-PCB (local Eagle copy, parsed nets: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_ada5346/sch.xml)
  - Microchip MCP23017 datasheet DS20001952D, local text: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/ds_mcp23017/mcp.txt (ESD 4 kV:400 V; IODIR POR 1111 1111; GPPU 0000 0000; INT cleared only on GPIO/INTCAP read; A0-A2 and RESET must be externally biased; 25 mA/pin; temperature ranges by VDD)
  - https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf
  - https://www.waveshare.com/mcp23017-io-expansion-board.htm (fetched: $5.99, tier $5.39 at 2, claims an onboard voltage translator)
  - https://www.waveshare.com/w/upload/5/54/MCP23017-IO-Expansion-Board-Schematic.pdf (downloaded and rendered: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p5_mcpv_dl/ws-1.png; no translator, RESET RC only, 100 nF only, 10k address pull-ups)
  - https://www.reichelt.com/de/en/shop/product/developer_boards_-_i_o_expansion_board_mcp23017-376528 (fetched: Soldered 333007, EUR 4.40 incl. VAT, available 26 Oct 2026)
  - https://cdn-reichelt.de/documents/datenblatt/A300/IO-EXPANDER-MCP23017-BREAKOUT.pdf (rendered: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p5_mcpv_dl/sold-1.png; VCC 5 V default, JP1-JP4 regulator/pull-up jumpers)
  - https://www.reichelt.com/de/en/shop/product/i_o_extension_16bit_1_8_-_5v_serial_i2c_so-28-282743 (fetched: MCP23017-E/SO EUR 1.49 incl. VAT, in stock, shipping from EUR 5.95)
  - https://www.tme.eu/en/details/mcp23017-e_so/i-o-expanders-integrated-circuits/microchip-technology/ (fetched: $1.35, 0 stock / not for sale in this country)
  - https://www.dfrobot.com/product-2002.html (fetched: DFR0626 $5.90, 44x32 mm, DIP-switch address, stock unclear)
  - TI TCA9535 datasheet SCPS201F, local text: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/ds_tca9535/tca9535.txt (INT resets when the port returns to its original setting; ±2000 V HBM)
  - https://www.nxp.com/docs/en/data-sheet/PCAL6416A.pdf (local: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p5_mcpv_dl/pcal6416a.txt; one ADDR pin, two addresses)
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md lines 237, 257, 625-672, 1118-1135 (D13 row, power PCB at model status, pinout, order plan with DigiKey/Adafruit/LCSC orders)
  - Not verified: Mouser and Microchip Direct (HTTP 503), soldered.com (HTTP 429), and the PCAL9535A/TCA9535/MCP23017T-E/SS DigiKey prices (taken from searches A/B). The WebSearch budget was exhausted, so no counterfeit-report search was run.

