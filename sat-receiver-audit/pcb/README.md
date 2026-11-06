# PCB preparation package

This directory contains audited PCB partition and placement inputs. It is **not a fabrication package**. The E1–E5 schematic graphs include whole purchased products, existing board circuitry, cables and physical interfaces as well as custom-board parts. Placing all 777 graph references on one PCB would duplicate hardware and invent module pads.

Run from the repository root:

```sh
python pcb/prepare.py
python pcb/prepare.py --check
```

Only Python standard-library modules are used. The script reads E1–E5 and the mount decision of each reference from `design/parts/parts.json` (only the fields listed under `parts_database` in `generated/provenance.json`), verifies actual portable-footprint hashes and pad numbers, and compares every connected graph pin against the real KiCad XML export. `--check` fails for stale generated output, a missing/hash-changed footprint, pin/pad mismatch or graph/XML mismatch.

| Output | Use |
|---|---|
| `generated/partition.json` | Every reference, category, candidate board, unresolved item and constraints |
| `generated/components.csv` | Filterable BOM/placement classification of all 777 references |
| `generated/unresolved.csv` | Missing physical footprint, pin/pad or module/interface/rework blocker records; a connector or feed that is not a board part stays blocking (`interface_mounting_unresolved`) until its parts-database entry fixes both the mating part and the mounting (`interface_resolved`), and a virtual contact whose nets reach no host pin is `host_pads_unconnected` |
| `generated/detector-core-input.json` | Exact 71-part DC core placement input, original pin/net/NC data and eight-net boundary |
| `generated/detector-core-nodes.csv` | All 187 core pin assignments; 180 connected and seven NC |
| `generated/constraints.json` | Current, thermal, RF, DC, grounding and mechanical requirements with sources |
| `generated/provenance.json` | Exact input SHA256s and primary-document URLs |
| `generated/summary.json` | Reproducible counts and audit outcomes |

Existing assemblies are separated from custom-PCB parts. In particular U102/R101/C101/C102 are already on the Adafruit INA228 breakout; U500 represents existing Q6A rail circuitry. R117–R120/C118 are IP2368 module rework, not parts automatically placed on a new motherboard. A407 YAT and A424 TCBT are the opposite exception: these are physical SMT RF parts despite their graph `kind=module`.

Eight domains are candidates for partitioning and may be combined or split after electrical/mechanical review. They do not require buying eight new boards. The DC core excludes three first RF tap resistors, their three 100 pF capacitors and twelve hot bleed resistors, keeping these 18 parts at the antenna/RF substrate. Its eight external nets have **no invented connector footprint or pin order**.

All 71 DC core parts now carry graph-assigned portable footprints with MPNs selected in `design/parts/parts.json` (three 0402 series resistors, 29 resistors and 18 capacitors in 0603, 13 SOT-23 and 8 SOT-23-6; exact counts in `generated/summary.json`). A selected MPN is a procurement record, not a qualification: voltage/power/TCR/leakage ratings and land patterns still need review, and the circuit has not passed threshold/RF tests.

The CAD-stage generator and actual starter boards, if present, are maintained separately from `prepare.py`. See `../build/13-pcb-preparation.md` for boundaries and release gates. No Gerber/drill output should be treated as approved from these inputs.
