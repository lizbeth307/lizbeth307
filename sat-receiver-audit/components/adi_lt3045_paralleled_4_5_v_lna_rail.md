# Adi lt3045 paralleled 4 5 v lna rail: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** ADI LT3045, 2 in parallel, 4.5 V LNA bias rail (v2.1 owner decision 24.10.2026: set to 4.30 V with a shared RSET of 21.5k 0.1%; acceptance is a measured V(E2_LNA_IN)-V(OUTS) of at least 0.40 V at 3.2 A LAB5 / 1 A pair / 50 C, E2-04) (LNA4V5: LAB5 D36V28F5 -> LC -> 2x LT3045 -> 4x TPS2553 -> bias tees). Real load 0.17-0.6 A; labd LNA budget 1.0 A.
- **Current pick:** ADI LT3045EMSE#PBF (MSOP-12E), qty 2, LCSC C580012. Note: re-audit D wrote 'LT3045EDD#PBF (DFN)' only because that was the LCSC link it found, without giving a reason. This check shows the MSOP is the better choice (see stack_changes).
- **Current price usd:** 16.67 for 2 ($8.3329 each at qty 1, 1,603 in stock). Re-checked through the LCSC product API on 18 Oct 2026. Excludes EU import VAT, shipping, the EUR 3 duty per tariff line, and the EUR 2 Union handling fee (UHF) from about 1 Nov 2026. LCSC is not ADI-franchised. The authorised price at DigiKey is $10.00 each (16,667 in stock).
- **Decision:** keep
- **Chosen:** Keep ADI LT3045EMSE#PBF x2 (LCSC C580012). No cheaper candidate passes the 'not worse' test.
- **Chosen price usd:** 16.67 for 2 (LCSC, ex-VAT). Authorised fallback: 20.00 for 2 (DigiKey LT3045EMSE#PBF, $10.00 each, 16,667 in stock; or EMSE#TRPBF, $10.00 each, 12,159 in stock).
- **Saving usd:** 0 against the current pick. Against re-audit D's EDD#PBF wording ($8.6304 each, $17.26 for 2), keeping the MSOP saves $0.60 and also restores the guaranteed maximum dropout.
- **Equivalence proof:** I checked the strongest candidate, LT3045EDD#TRPBF (LCSC C514420), against the current pick. Price and stock are real (LCSC API and WebFetch, 18 Oct 2026): $7.4629 at qty 1, $6.4297 at qty 10, 4,236 in stock, minimum order 1, multiple 1. The page shows no reel or cut fee. The API has a field reelPrice=3.0, which looks like LCSC's optional customised-reel service (unverified; do not select it). The silicon is the same die as the MSOP, but on paper the part is WORSE in the spec that matters most on this rail. Datasheet Rev B (the LCSC mirror, the same PDF that LCSC links for all three SKUs), Note 5, says: "For DFN package: Linear Technology is unable to guarantee maximum dropout voltage specifications at high currents due to production test limitations with Kelvin-sensing the package pins." So the guaranteed maximum dropout at 300 mA (280 mV at 25 C, 350 mV over temperature) and at 500 mA (350/450 mV) applies only to the MSOP. For the DFN only typical values (220/260 mV) remain. Each device carries about 85-300 mA, and the headroom is only about 0.27-0.65 V (D36V28F5 at 5.0 V +/-4%, minus the LC drop). Datasheet curve G45 shows PSRR falling from about 56-67 dB at 0.5 V headroom to about 12-40 dB at 0.3 V. So the dropout guarantee is exactly what sets worst-case spur rejection. Swapping to the DFN would give up a guaranteed spec silently, which the rule forbids, for $1.73. Smaller points against the DFN: (a) it is leadless, which is harder to hot-air solder and inspect on a hand-built two-layer board than the MSOP's gull-wing leads plus exposed pad; (b) its top mark LGYP is shared by the E, I and H grades (the datasheet says the grade is only on the shipping label), so checking the mark on arrival cannot confirm the part; (c) the authorised DFN is not available: DigiKey EDD#TRPBF has 0 in stock and 2,500 are expected on 4 Jan 2027. The other part numbers each fail a hard spec (see rejected). Other LT3045 SKUs at LCSC all cost more than C580012: EMSE#TRPBF C666577 $8.4153; EDD#PBF C666574 $8.6304; IDD#TRPBF C666584 $8.8789; EDD-1#TRPBF $9.58 (JLC listing). So C580012 is already the cheapest LT3045 that keeps every guaranteed spec.
- **Rejected:**
  1.
    - **Name:** ADI LT3045EDD#TRPBF (DFN-10, LCSC C514420), $14.93 for 2
    - **Why:** The price is real ($7.4629, 4,236 in stock), and the part is identical to re-audit D's EDD#PBF. But the datasheet does not guarantee maximum dropout for the DFN at 300 or 500 mA (Note 5), while the MSOP is guaranteed at 280/350 mV (300 mA) and 350/450 mV (500 mA). That spec is critical at 0.27-0.65 V headroom. The package is leadless, so hand assembly and inspection are harder. The LGYP mark cannot confirm the grade. Same grey channel as the current pick. The authorised DFN is backordered until 4 Jan 2027. It would save only $1.73 by giving up a guaranteed spec.
  2.
    - **Name:** ADI LT3045EMSE#PBF from DigiKey (authorised)
    - **Why:** Same part at $10.00 each, $20.00 for 2 (16,667 in stock), which is $3.33 more. It is the authenticity fallback, not a saving.
  3.
    - **Name:** TI TPS7A9401DSCR (single 1 A LDO; DigiKey $8.73, LCSC C5220127 $2.63)
    - **Why:** Verified in datasheet section 6.1: absolute maximum on IN is 6.0 V and on OUT is VIN+0.3 V, so it has no reverse-current protection. If LAB5 fails high (up to 16.4 V), it is destroyed and the battery voltage can reach the LNAs. The LT3045 is rated +/-22 V. Fig 6-4 (VIN 5.5 V, VOUT 5.0 V, 500 mA, so 0.5 V headroom) gives about 50 dB at 1 MHz, about 45 dB at 1.6 MHz, about 52 dB at 2 MHz and about 34 dB at 10 MHz. The LT3045 (G45, at 0.5 V headroom) gives about 56 dB at 1 MHz and 65 dB at 2 MHz. GND current is 15 mA typical, against 2 x 2.2 mA. It is worse on robustness and on PSRR at the buck harmonics.
  4.
    - **Name:** ADI LT3041ADE#PBF (single 1 A)
    - **Why:** Datasheet table: dropout 290 mV typ, 380 mV max (25 C), 470 mV max over temperature at 500 mA, and 310/390/480 mV at 1 A. The LT3045 pair at 300 mA each gives 220/280/350 mV, so the LT3041 is about 70-130 mV worse inside a 0.27-0.65 V window. Noise is 1.0 uVrms, against about 0.57 for the pair. Reverse output current is up to 1 mA, against 25 uA. DigiKey has 0 in stock (due 30 Oct 2026). It would save only about $6.
  5.
    - **Name:** TI TPS7A4701RGWR
    - **Why:** Noise is 4.67 uVrms at 5 V (datasheet), about 6x the LT3045. Current limit is fixed. It has no PG pin (re-audit D adds a TLV3011 for this). Dropout is 307 mV at 1 A. It is not 'not worse'.
  6.
    - **Name:** TI TPS7A9601DSCR (2 A)
    - **Why:** TI parametrics: Vin max 5.7 V and PSRR at 100 kHz of 60 dB, against 77 dB for the LT3045. It has no reverse protection. It saves only about $5.
  7.
    - **Name:** ADI ADM7150ACPZ-4.5/-5.0
    - **Why:** 800 mA, below the 1.0 A labd budget. Dropout is too high for 0.27-0.65 V of headroom (DigiKey parametrics; the ADI datasheet could not be reached). The -4.5 version is $15.33 with 10 in stock.
  8.
    - **Name:** 3PEAK TPL910ADJA-DF6R (LCSC C5289801)
    - **Why:** Catalogue data: 500 mV dropout at 1 A, 4.5 uVrms noise, VIN max 6.5 V, 50 dB PSRR at 1 MHz. It fails on dropout, noise and robustness (datasheet not read; it fails on the catalogue values alone).
  9.
    - **Name:** Tokmas 'LT3045IDD-5' (LCSC C50346345)
    - **Why:** A name-squatted part, not an LT3045: SOT-23-3, fixed 5 V, 200 mA, 1 V dropout. Add it to the do-not-order list.
  10.
    - **Name:** A single LT3045, or LT3042 x5
    - **Why:** A single LT3045 gives 500 mA, against 1 A (rejected earlier in the stack, C9/D11). Five LT3042 cost $31.24, which is more.
  11.
    - **Name:** AliExpress LT3045 modules (single module $15.68-17.09; 1 A module $24.77; 2 A/3 A modules $52.89-71.29; the 'from $1.09' listing)
    - **Why:** They cost more per 0.5 A than the bare chip. No noise, PSRR or dropout measurements are published. Chip origin is unknown. They use trimmer SET resistors, have no ballast and probably no PG or ILIM, and do not fit the plate-bonded power board. The $1.09 variant's contents are unverified.
  12.
    - **Name:** Loose marketplace 'LGYP LT3045EDD' chips (about $5.72, maybe $1.31 each)
    - **Why:** High counterfeit and remark risk. $1.31 is below ADI-channel volume pricing. LGYP is shared by the E, I and H grades, so the mark proves nothing. These are DFN parts, so the dropout guarantee is also lost.
  13.
    - **Name:** DIY discrete or capacitance-multiplier regulator
    - **Why:** It needs about 0.6-0.7 V of headroom (Vbe plus saturation), which is more than the 0.27-0.65 V available. No current limit, thermal shutdown or PG. No measured evidence.
  14.
    - **Name:** Used or surplus LT3045 or demo board
    - **Why:** No offer found below the current price. Pulled chips cannot be traced.
  15.
    - **Name:** Other LT3045 SKUs at LCSC (EMSE#TRPBF C666577 $8.4153; EDD#PBF C666574 $8.6304; IDD#TRPBF C666584 $8.8789; EDD-1#TRPBF about $9.58)
    - **Why:** None is cheaper than C580012 at $8.3329. The DFN SKUs also lose the dropout guarantee.
- **Confidence:** high
- **Conditions or tests:** 1. Goods-in, per unit: MSOP top mark '3045', with the lot and date code consistent across the two parts. Set VOUT through RSET and check 4.5 V +/-2%. Measure dropout at 300 mA and 25 C: lower VIN until VOUT falls 1%; it must be 280 mV or less (datasheet maximum). Check current sharing in the pair with the ADI parallel layout (ballast, within about 20%). A unit that fails is treated as suspect, since the source is grey-channel. 2. STACK item 1079 bench test, run at the REAL headroom: log LAB5 under worst-case load, then measure 500 kHz, 1 MHz and 2 MHz ripple and the LNA-port spurs at 0.17 A and 0.6 A total. If LAB5 minus the LC drop leaves less than about 0.4 V (G45 PSRR collapses below about 0.35 V), take re-audit D's remedy: lower the rail to 4.3-4.4 V once the LNA owners confirm, or feed the LDOs from a higher point. 3. Explicit trade option, which I do not recommend: LT3045EDD#TRPBF (C514420) saves $1.73 only if the user explicitly accepts typical-only dropout at 300 mA and above for the DFN, plus DFN hand assembly. Bench-testing two units at room temperature does not replace the production guarantee over temperature. 4. EU landed cost: LCSC is a non-EU seller, so import VAT, EUR 3 per tariff line and the EUR 2 UHF apply (operator note 35). This adds the same amount for any LCSC SKU, so it does not change the ranking. TME (EU) lists neither LT3045EDD nor LT3045EMSE in its standard offer. DigiKey's EU landed cost (DDP or not) was not verified.
- **Stack changes:** 1. Correct re-audit D's LNA4V5 line from '2x LT3045EDD#PBF (LCSC about $8.63)' to '2x LT3045EMSE#PBF (LCSC C580012, $8.3329)'. That is $0.60 cheaper for the pair and keeps the guaranteed maximum dropout (datasheet Note 5). The power-board footprint becomes MSOP-12-EP: pin 13 exposed pad is GND and must be soldered, with thermal vias to the copper bonded to the plate. Thermal: theta-JA 33 C/W and theta-JC 8 C/W (DFN: 34 and 5.5 C/W), negligible at about 0.25 W per device. All functions used (EN/UV, PG, ILIM, PGFB, OUTS, SET) are on both packages, so the EN wiring from MCP #1, the PG wiring to MCP #3 and the TPS2553 stages do not change. 2. Authorised fallback in the BOM: DigiKey LT3045EMSE#PBF, $10.00, 16,667 in stock (or EMSE#TRPBF, $10.00, 12,159 in stock). Do not list DigiKey EDD parts: they are backordered until 4 Jan 2027. 3. Add Tokmas 'LT3045IDD-5' (LCSC C50346345) and marketplace 'LGYP' loose chips to the do-not-order list. 4. Keep the item 1079 bench test, run at the measured LAB5 headroom; the 4.3-4.4 V rail stays the remedy if headroom is under about 0.4 V. 5. No change to drivers, connectors, the case or the rails; the hard rules are untouched (DC bias regulator only, receive-only). Limits of this check: WebSearch was already used up for this turn (shared limit), so I worked only from the LCSC and JLC APIs and pages, DigiKey, TME and the cached datasheets. analog.com returned 503, so I could only verify Note 5 in Rev B. A later ADI revision was not checked.
- **Sources:**
  - https://www.lcsc.com/product-detail/C580012.html
  - https://www.lcsc.com/product-detail/C514420.html
  - https://www.lcsc.com/product-detail/C666574.html
  - https://www.lcsc.com/product-detail/C666577.html
  - https://www.lcsc.com/product-detail/C666584.html
  - https://datasheet.lcsc.com/datasheet/pdf/9d46bf6db3babcb8c3f12d5d51205ba7.pdf?productCode=C514420
  - https://www.digikey.com/en/products/result?keywords=LT3045EMSE%23PBF
  - https://www.digikey.com/en/products/result?keywords=LT3045EDD%23TRPBF
  - https://www.tme.eu/en/katalog/?search=LT3045EMSE
  - https://www.ti.com/lit/ds/symlink/tps7a94.pdf
  - https://www.ti.com/product/TPS7A96
  - https://www.ti.com/lit/ds/symlink/tps7a47.pdf
  - https://datasheet.lcsc.com/datasheet/pdf/edce8deb70883c53cbe3578b120f6cef.pdf?productCode=C7452881
  - https://www.lcsc.com/product-detail/C50346345.html
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/ldo_dl/lt3045.txt
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/ldo_dl/g45.png
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/ldo_dl/fig64.png
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/ver_lt3045/api_C514420.json

