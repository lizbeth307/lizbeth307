# Routed internal DC detector prototype

**NOT FOR FABRICATION.** This is a routed prototype candidate for the 71-part DC_CORE subset. The eight external interfaces, 50 passive MPN/land-pattern approvals, enclosure fit and hardware performance tests remain unresolved. No Gerbers or drill files were created.

Open `detector-core-routed-prototype.kicad_pcb` with its adjacent `.kicad_pro` and relative `fp-lib-table`. The exact source mapping is retained: 71 components, 187 pads, 180 connected pads, seven NC pads and 40 nets. No connector pads, new components or substitute pin numbers were added. Eighteen RF-port tap/bleed references remain outside this board.

The prototype copy compacts the three SENSE islands, reference network and bypasses. The 23.10.2026 re-freeze (deterministic pin order, CI KiCad 10.0.7) has 753 track segments, 93 vias and one filled B.Cu GND zone; the 20.10.2026 copy had 729 segments. SENSE uses F.Cu only with zero vias; exact per-island track bounds are measured by `verification/pcb-prototype-review-check.py`. These are measured geometry, not precision qualification or TI acceptance limits. The 125 × 115 mm outline and two-layer configuration remain candidates.

Two real KiCad 10.0.7 checks passed with **0 violations, 0 unconnected items and 0 ignored checks**, including all warning/error/exclusion severities. The five normally ignored categories are enabled as warnings. `drc-raw.json` is the unfiltered generation report; `drc-portable-raw.json` is the unfiltered repeat against the published portable project. Full-project schematic parity was not requested for this subset: exact source-node/pad fidelity is checked separately.

Previews:

- `detector-core-routed-prototype.svg` / `.png`: F.Cu, silkscreen and outline.
- `detector-core-routed-prototype-bottom.svg` / `.png`: B.Cu plane and crossover routes, viewed from the top for layer alignment.

Review: `../../../verification/pcb-prototype-review.md` and `.json`.

From the repository root, using Python with KiCad 10 `pcbnew`, NumPy/SciPy and `kicad-cli`:

```sh
python3 pcb/generate_routed.py
python3 verification/pcb-prototype-review-check.py
```

In the current extracted official Ubuntu runtime:

```sh
python3 pcb/generate_routed.py --runtime-root /tmp/kicad-runtime/root --kicad-cli /tmp/kicad-runtime/kicad-cli
python3 verification/pcb-prototype-review-check.py
```

The checker uses only the Python standard library, reads the actual CAD and raw DRC, and does not import the router. It also runs from outside the checkout. Generation uses a unique temporary project, invokes native zone filling/DRC and publishes the board only after the exact pin audit and raw DRC gate pass. It does not alter the frozen starter or source graphs. Regeneration changes native UUIDs; repeat the independent check and review hashes after changes.

The router uses 0.20 mm tracks/clearance, 0.60/0.30 mm through vias and a 0.25 mm hole-edge spacing rule. These are explicit prototype rules, not an approved fabrication capability or stackup. KiCad's DRC and the independent geometric audit are the final copper checks; the coarse routing grid is not treated as proof of clearance.

A DRC pass connects only the selected internal circuit. Six boundary nets have a single source pad, so zero unconnected findings do not imply a physical harness exists. The remaining physical implementation and hardware test gates are detailed in the review.
