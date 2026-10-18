# Aon 3 3 v ldo tps709 class micropower uv: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** AON 3.3 V LDO (TPS709 class) + micropower UV supervisor 12.8/13.6 V (re-audit parts: TI TPS70933DBVR + TI TLV3012AIDBVR, 3.3 MOhm / 346 kOhm divider into IN-, REF through 100 kOhm into IN+, 4.22 MOhm OUT-to-IN+ feedback, OUT through BAT54 to #2813 OFF)
- **Current pick:** TI TPS70933DBVR (LCSC C89347) + TI TLV3012AIDBVR (DigiKey), plus BAT54 and 0.1 % divider resistors
- **Current price usd:** About $2.91 for the two ICs. TPS70933DBVR is $0.3409 each at LCSC (5+, MOQ 5, so a $1.70 line; 40,260 in stock, checked 18 Oct 2026). TLV3012AIDBVR is $2.57 at DigiKey (qty 1; 1,541 in stock; $1.909 at 10). With passives the set is about $3.2-4.5, inside STACK's $2-4 estimate. Buying both ICs at DigiKey would cost $4.08: TPS70933DBVR is $1.51 there but out of stock, with 11 due 03 Dec and 2,989 due 21 Dec 2026, 20-week lead time. TME's TLV3012AIDBVR price is not real: the page shows 'no-prices' and its stock reads both 0 and 1,062.
- **Decision:** replace_conditionally
- **Chosen:** LDO: KEEP TI TPS70933DBVR. No cheaper part is not-worse. Comparator: REPLACE TLV3012AIDBVR with Microchip MCP65R41T-1202E/CHY (push-pull, 1.21 V reference, SOT-23-6, same pin order), bought at DigiKey. Divider bottom resistor changes from 346 kOhm to 336 kOhm. The conditions are listed below. If the part fails the bench gate, go back to TLV3012AIDBVR.
- **Chosen price usd:** About $0.85 for the two ICs: TPS70933DBVR $0.34 at LCSC plus MCP65R41T-1202E/CHY $0.51 at DigiKey (qty 1; $0.4592 at 25; Active; 30,091 in stock; 4-week lead time). DigiKey DE: EUR 0.45 excl. VAT, EUR 0.5355 incl. 19 % DE VAT. LCSC C219181 has it at $0.8866 (250 in stock), but LCSC is not needed for it. All-franchised route (everything from DigiKey, B-pinout LDO): TPS709B33DBVR $1.51 (5,264 in stock) + $0.51 = $2.02. The set with passives is about $1.2-2.4.
- **Saving usd:** About $2.06 per set ($2.91 to $0.85, IC cost down about 71 %). In the EU at DigiKey DE: about EUR 1.81 excl. VAT (EUR 2.26 vs EUR 0.45; the EUR 2.26 TLV3012A figure is from search 1 and I did not re-fetch it). The LDO saves nothing.
- **Equivalence proof:** COMPARATOR: MCP65R41T-1202E/CHY (DS22269B) vs TLV3012A (SBOS300C section 6.7). All limits are at 25 C.
  - Supply: 1.8-5.5 V on both. Equal.
  - Iq: 2.5 typ / 4 max uA vs 2.8 / 5. Better.
  - VOS: +/-10 mV max vs 15 mV max, both at VCM = 0. Better.
    - Correcting to VCM of about 1.2 V with the CMRR minimums (55 dB vs 60 dB) gives at most 12.1 mV vs 16.2 mV. Still better.
  - Reference window: 1.185-1.234 V (+/-2.0 %) vs 1.208-1.276 V (+/-2.7 %). Better.
    - TI's '+/-1 % initial accuracy' line contradicts TI's own min/max limits. The binding numbers are the limits.
    - Untrimmed trip window (my model, VOS and CMRR included): MCP 12.40-13.18 V (+/-3.0 %) vs TLV3012A 12.33-13.38 V (+/-4.1 %). Better.
  - Reference drift: 27/22 typ, 100 ppm/C max vs 40 typ, 100 max. The max is equal, but Microchip's max is 'characterized but not production tested', while TI's carries no footnote. This is a weaker guarantee, NOT hidden; the bench gate covers it.
  - Reference drive: +/-500 uA within +/-2 % vs 0.5 mA. The circuit draws 0.28 uA source and 0.48 uA sink, so this is negligible on both.
  - Reference capacitive load: 200 pF typ (above 2 nF it may oscillate at power-up) vs stable to 10 nF. This is a layout constraint: no capacitor on VREF. The 100 k series resistor isolates IN+.
  - Input bias: 1 pA typ at 25 C, 50 pA at 85 C, 5 nA max at 125 C. TLV3012A gives +/-10 pA typ and no max at all. Worst case, 5 nA into the 313 kOhm Thevenin is 1.6 mV, about 17 mV at N (0.13 %). Negligible at the 45-50 C enclosure temperature.
  - Input absolute maximum: VSS-0.3 to VDD+0.3 V at +/-2 mA. The non-B TLV3012 is -0.5 to (V+)+0.5 V. The '7 V while unpowered' tolerance quoted in search 2 applies only to the B version, so that point is refuted. Through 3.3 MOhm, even with AON dead and N at 16.8 V, the input current is at most about 5 uA. Equal here.
  - Internal hysteresis: 1-5 mV (TLV3012A has none). It adds about +/-5-27 mV at N around each threshold; the external network is unchanged.
  - Output: push-pull, VOH at least VDD-0.2 V at 2 mA. Equal for the microamp load into BAT54 and #2813 OFF.
  - POR: neither has one (TLV3012A is non-B). Equal.
  - Temperature: -40 to 125 C on both. Equal.
  - ESD: 4 kV HBM vs 2 kV. Better.
  - Package and pinout: SOT-23-6 OUT/VSS/IN+/IN-/VREF/VDD, identical to the TLV3012 DBV OUT/V-/IN+/IN-/REF/V+. Drop-in.
  - Missing spec: Microchip has no tabulated VREF line regulation (TI: 100 uV/V max). This does not matter here: VDD is the regulated AON 3.3 V (+/-1 %, line regulation 10 mV max), and the VREF window holds over VDD 1.8-5.5 V.
  - Model thresholds with 336 kOhm: 12.79 V trip, 13.62 V release (TLV3012A with 346 k: 12.79 / 13.59).
  - Release sensitivity to AON +/-1 %: about 8 mV at N on both.
  - Standby current, max: about 1 uA lower.
  - Sourcing: DigiKey is a franchised Microchip distributor; the part is Active.
  
  LDO: TPS70933DBVR is kept (SBVS186H):
  - 2.7-30 V operating, 32 V absolute maximum (above the 27.6 V SMBJ17A clamp).
  - IGND 1.3 typ / 2.05 max uA.
  - Accuracy +/-1 % (VOUT 3.3 V or more, -40 to 85 C); line regulation 3/10 mV.
  - Current limit 200-500 mA; reverse current 10 nA out of IN / 100 nA into OUT.
  - Thermal shutdown 158 C; TJ to 125 C.
  Every cheaper candidate is worse on Iq, accuracy, temperature range or protections, and none is cheaper than LCSC's $0.34.
  
  No hard rule is affected: this is DC power and supervision with no RF or TX path and no loop.
- **Rejected:**
  1.
    - **Name:** TI TLV3012AIDCKR (SC70-6, LCSC C2860248, $1.39, 44 in stock)
    - **Why:** Electrically identical to the current part but costs more than the MCP65R41 ($0.51) and has the wider reference window of the A die. SC70 with 0.65 mm pitch is harder to hand-solder and inspect. LCSC is not a confirmed TI-franchised source. The stock is too small to rely on.
  2.
    - **Name:** TI TLV3012BIDBVR ($2.78 DigiKey, $2.83 LCSC)
    - **Why:** Better than the A version (POR, Iq 3.1 uA max, VOS 6 mV, REF 1.223-1.260 V), but $0.21 dearer than the current part at DigiKey, so it saves nothing. It is an optional paid upgrade, not the cheapest not-worse part.
  3.
    - **Name:** TI TLV4051R5DBVR + 2N7002 + about 6.2 MOhm (LCSC $1.30)
    - **Why:** Not a drop-in: single inverting input, fixed 20 mV hysteresis, different SOT-23-5 pinout. The 12.8/13.6 V hysteresis needs a FET-switched divider, which adds FET leakage error and is unproven on a safety-relevant OFF line. It costs more than the MCP65R41 and LCSC has only 135.
  4.
    - **Name:** RUNIC RS8912XH (LCSC $0.39)
    - **Why:** -40 to 85 C vs -40 to 125 C. Iq 3.5 uA vs 2.8. Reference value and accuracy not published in the listing; data sheet and pinout not verified.
  5.
    - **Name:** Holtek HT7533-1/-2 and Goodwork/UMW HT7533-1 clones (LCSC $0.15-0.17; DigiKey UMW $0.25, Goodwork 1k MOQ)
    - **Why:** Iq 2.5 uA (Holtek), 1.5/3.0 uA (Goodwork) or 3 uA (UMW) vs 1.3/2.05. Accuracy +/-2 % vs +/-1 %. 30 V absolute maximum vs 32 V. -40 to 85 C (UMW -25 to 70 C). No reverse-current protection or thermal shutdown specified. SOT-89 on some versions.
  6.
    - **Name:** Diodes AP7381-33SA-7 (LCSC $0.113)
    - **Why:** 0 in stock (SOT-89 version: 2 pcs). Iq 2.5 uA vs 1.3. SOT-23-3 footprint. Accuracy and reverse protection not verified.
  7.
    - **Name:** onsemi NCP730ASN330T1G (LCSC $1.07)
    - **Why:** Not cheaper than TPS70933DBVR ($0.34). Listed Iq of 1.8 uA is not better (data sheet not fetched).
  8.
    - **Name:** TPS70933 'clones': MSKSEMI TPS70933DBVR-MS, TECH PUBLIC TPS70933DBVR-TP, HEERMICR HE2210M533R (LCSC $0.14-0.26)
    - **Why:** Iq 2 uA vs 1.3. TECH PUBLIC is -40 to 85 C. MSKSEMI lists no specs. No data sheet or independent measurement checked. Copied TI part numbers raise authenticity concerns. Saves at most $0.20.
  9.
    - **Name:** TI TLV709
    - **Why:** Iq 3.2 uA, 2 % accuracy, no reverse-current protection listed; price not verified.
  10.
    - **Name:** TI TPS70933DRVR (WSON-6)
    - **Why:** Same die, but $1.34 at DigiKey is dearer than LCSC's $0.34 for the DBV. The exposed-pad WSON needs hot air or reflow. Stock not confirmed.
  11.
    - **Name:** TI TPS709B33DBVR (DigiKey $1.51, 5,264 in stock)
    - **Why:** Same spec, but not cheaper. Kept only as the franchised-route fallback; it needs the B-pinout footprint (GND 1, IN 2, OUT 3, NC 4, EN 5).
- **Conditions or tests:** Adopt MCP65R41T-1202E/CHY only with all of the following.
  
  (1) Layout:
  - VREF (pin 5) connects only to the 100 kOhm, by a short trace, with NO capacitor (200 pF or less total).
  - 100 nF VDD bypass within 2 mm.
  - Any deglitch capacitor goes on IN- (pin 4) only, e.g. 100 nF (tau about 31 ms), never on IN+ or VREF.
  - Clean flux off the 3.3 MOhm node.
  
  (2) Divider:
  - Bottom 336 kOhm built as 332 kOhm + 4.02 kOhm in series, both 0.1 % / 25 ppm thin film. The 4.02 k is the calibration trim, about 35 mV at N per kOhm. Use 330 k + 6.04 k as an alternative.
  - Reason: 336 k 0.1 % (Yageo RT0603BRD07336KL) is not stocked at DigiKey (5k reel, 23 weeks), and LCSC shows no stock.
  - Top: 3.3 MOhm 0.1 % (Vishay MCA1206, LCSC C4168316).
  - The 100 k and 4.22 M can be 1 %.
  
  (3) Bench gate, extending STACK's TLV3012 test:
  - Sweep N 14.0 -> 12.0 -> 14.0 V at 25 C and again with the board at about 50 C (enclosure temperature).
  - Pass at both temperatures: trip 12.8 +/-0.1 V, release 13.6 +/-0.1 V.
  - Pass: trip shift between 25 C and 50 C of 50 mV or less (budget: 100 ppm/C reference plus VOS drift plus resistor TCR). This checks the drift max that Microchip does not production-test.
  - Optional cold point at about 0 C for winter field use.
  - Fail: try a second unit; if that also fails, revert to TLV3012AIDBVR (same footprint; bottom resistor back to 340 k + 6.04 k).
  
  (4) Standby at 14.8 V, main switch OFF, INA228 in shutdown:
  - AON LDO + comparator + divider branch 11 uA or less (model: about 8 uA typ).
  
  (5) Keep the existing tests:
  - Held OFF vs button on pin A.
  - 20 PD plug/unplug cycles with no spontaneous #2813 change.
  
  (6) Goods-in:
  - Buy the MCP65R41 only from DigiKey (franchised); marking 'HV' + 2 traceability characters.
  - TPS70933DBVR from LCSC: marking 'SDG'. At no load and VIN 14.8 V, IGND 2.05 uA or less and VOUT 3.267-3.333 V.
  
  (7) Leave TPS709 EN floating (internal pull-up); never tie it to N (7 V absolute maximum).
- **Stack changes:** BOM line 'AON і супервізор' becomes:
  - TPS70933DBVR (LCSC C89347, $0.34, MOQ 5).
  - MCP65R41T-1202E/CHY (DigiKey, $0.51; DigiKey DE EUR 0.45 excl. VAT).
  - BAT54, 3.3 MOhm 0.1 %, 332 k + 4.02 k 0.1 %, 100 k, 4.22 M.
  - Set about $1.2-2.4 instead of $2-4. Status: verified prices, bench gate pending.
  
  Schematic: identical topology and SOT-23-6 footprint. Only the bottom divider changes (346 k becomes 332 k + 4.02 k). Model: 12.79 V trip, 13.62 V release. Add the 'no capacitor on VREF' rule and the optional IN- deglitch capacitor.
  
  Fallback footnote: the current TLV3012 design's 346 k is not an E192 value. It would also need a series pair (340 k + 6.04 k) or 344 k (12.85 / 13.66 V).
  
  LDO sourcing:
  - Default: LCSC (the order is already planned in STACK week 1).
  - If the build is restricted to franchised channels: lay out the B pinout and use TPS709B33DBVR from DigiKey ($1.51, in stock). TPS70933DBVR is backordered at DigiKey until Dec 2026.
  
  EU landed cost: the LCSC order counts as a non-EU shipment, so add EUR 3 per tariff item (consignments of EUR 150 or less via IOSS/postal) and EUR 2 UHF per item from about 1 Nov 2026 (operator notes 34-35). The LDO goes into the existing LCSC IC order, so it probably adds no new item; check at checkout. DigiKey DE prices exclude VAT (19-27 % by country).
  
  No change to rails, connectors, drivers, software or the case. Standby current is about 1 uA lower (max). No hard rule is affected.
  
  Method notes:
  - The WebSearch budget for this turn was used up, so I found no independent measurements of the MCP65R41. All values are from the manufacturer data sheets plus my own model.
  - microchip.com returned 403; Mouser and Microchip Direct returned 503.
- **Confidence:** high
- **Sources:**
  - https://ww1.microchip.com/downloads/en/DeviceDoc/22269B.pdf (local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/aon_ds/mcp.txt)
  - https://www.ti.com/lit/ds/symlink/tlv3012.pdf (SBOS300C, local /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/aon_ds/tlv3012.txt)
  - https://www.ti.com/lit/ds/symlink/tps709.pdf (SBVS186H, local /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/aon_ds/tps709.txt)
  - https://www.digikey.com/en/products/result?keywords=MCP65R41T-1202E%2FCHY
  - https://www.digikey.de/en/products/result?keywords=MCP65R41T-1202E%2FCHY
  - https://www.digikey.com/en/products/detail/texas-instruments/TLV3012AIDBVR/1678203
  - https://www.digikey.com/en/products/result?keywords=TPS70933DBVR
  - https://www.digikey.com/en/products/result?keywords=TPS709B33DBVR
  - https://www.lcsc.com/product-detail/C89347.html
  - https://www.lcsc.com/product-detail/comparators_microchip-tech-mcp65r41t-1202e-chy_C219181.html
  - https://www.tme.eu/en/details/tlv3012aidbvr/comparators-integrated-circuits/texas-instruments/
  - https://www.digikey.com/en/products/result?keywords=RT0603BRD07336KL
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (items 34-35)
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md

