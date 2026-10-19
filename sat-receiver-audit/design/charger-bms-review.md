# External balance charger versus common-port BMS: blocking gate

Date: 2026-10-19. Gate: **G-CHG-BMS — OPEN; external 608PD balance-charge harness is not released for assembly or use.**

## Existing topology

The source project uses a Daly DL-J05G-L4S15ATJ common-port BMS. Its external service XT30 is at node N, with the return at protected P−. The separate 5-pin balance harness exposes raw cell taps B0–B4; B0 is raw pack negative. The proposed 608PD workflow connects both harnesses at once with the receiver main switch OFF.

## Primary evidence and limitation

- [Daly official 4S wiring tutorial](https://www.dalybms.com/4s-bms-wiring-tutorial/), sections II and VI: B0 identifies the total battery negative; B− goes to raw battery negative, while P− is the negative terminal for charge/discharge. This establishes that the two project nets have different roles. The tutorial is family-level guidance, not a model-specific internal schematic.
- [ISDT official 608PD manual](https://www.isdt.co/down/pdf/608PD.pdf), English pages 12–15: separate balance and DC battery ports are shown, and the manual describes using charging and balancing cables. The manual does not disclose their internal electrical interconnection or approve this protected-pack/raw-tap topology. No internal short, galvanic isolation, or BMS compatibility is established by this review.

## Conditional fault analysis

**Engineering inference, not an observed charger fault:** if the charger's balance-negative and battery-output-negative have a sufficiently low-impedance connection in any connected operating state, this harness creates a path from raw B0 to protected P− around the BMS switching path. Charge, discharge, or fault current can then use the balance wiring instead of being interrupted by the BMS. A main switch on the positive supply downstream does not break that negative bypass. The service fuse alone does not prove protection of individual cell-tap wires.

## Required project disposition

1. Disable the external 608PD plus raw-balance-harness workflow in the assembly and operating instructions. Mark the external balance connector DNP / service-only, insulated and unavailable for ordinary charging until the gate closes. **Do not remove the BMS's own internal sampling harness.**
2. Keep raw B0 and protected P− as distinct nets in KiCad; no net tie, PWR_FLAG, global ground label, or other ERC workaround may merge them.
3. Do not treat moving charger XT30− to raw B− as a fix: that deliberately charges outside the BMS path. Do not move balance B0 to P− without a manufacturer-approved design; it ceases to be the actual cell-stack reference when protection operates.
4. Ordinary protected-port charging remains a separate path and needs its normal validation. It does not establish that the planned monthly external balance routine is safe or fulfilled. Existing BMS balancing capability alone is not proof of adequate balancing at the project's lower daily-charge voltage.
5. Close the gate only with a documented approved interface, or a redesigned battery/charger protection arrangement that preserves interruption of all relevant charge/discharge paths. Any chosen redesign requires an explicit netlist, conductor/fuse ratings, and validation that BMS charge and discharge trips do not leave a bypass through balance, USB, earth, or other attached grounds. A single unpowered continuity measurement cannot prove absence of a connection in all charger operating states.

No physical charger or pack was tested. Do not describe this gate as closed by KiCad ERC, syntax validation, or a clean schematic plot.
