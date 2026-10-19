# Independent graph-to-netlist verification

Result: **PASS**. Checked on 2026-10-19 using an independent standard-library JSON/XML parser, without importing the project generator or validator.

- Hardware components: **754** in both the reviewed graphs and KiCad XML.
- Physical / functional pin declarations: **2326**, comprising **2189** connected pins and **137** declared NC pins.
- Intended connected nets: **466**. The XML has **603** total net entries because it also emits named entries for the 137 unconnected pins.
- Explicit power-source annotations: **25**; recorded separately from physical components.
- Missing pins, wrong net names, extra connected pins, duplicate node assignments, unexpectedly connected NC pins, missing/extra hardware components, semantic value changes, and raw Daly B0/B− tied to system GND: **0**.
- Final staged graphs were byte-identical to the reviewed working E1–E5 graphs at the time of this check.

KiCad trims outer whitespace from text values in its XML export. The checker records 19 such normalizations explicitly; it compares the remaining value text exactly, without changing graphs or CAD.

The report contains SHA256 values for each source graph and the XML netlist so that a later change can be detected. It establishes agreement between the reviewed connection data and the generated schematic netlist; it does not certify a PCB, firmware, hardware ratings or physical assembly.

Reproduce from the repository root:

```bash
python3 verification/independent_netlist_check.py
```

The script can also be invoked by its full path from any directory. Use `--project-root PATH` when the script is relocated independently. Optional `--working-design PATH` also checks a separate reviewed graph directory. All default paths are relative to the script's project root; no workstation path is required.

Exact machine-readable results: `verification/independent-netlist-review.json`.
