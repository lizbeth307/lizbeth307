# Routed DC_CORE internal prototype review

**Internal routing is complete and verified; this is NOT FOR FABRICATION.** A separate compacted prototype preserves the frozen 71-part DC_CORE source exactly. The frozen placement starter, source graphs and schematics remain unchanged. No Gerbers or drill files were generated.

> **Update 2026-10-23.** After the merge of branch `ccr-1537979d-cj7q9t` (duplicate pull-ups R102/R503/R507/R511 removed) with this revision's design-graph corrections, the CI re-freeze step (job `cad`, official `kicad/kicad:10.0.7` image, option `refreeze_pcb`) re-placed the starter, re-routed this prototype from the regenerated input with the deterministic pin order and re-pinned `pcb-prototype-review-check.py`. The core (71 parts, 187 pads, 180 connected, 7 NC, 40 nets, 8 boundary nets) is unchanged; `verification/pcb-prototype-review.json` is authoritative for the values below.

## Verified result

| Property | Result |
|---|---:|
| Components / physical pads | 71 / 187 |
| Connected pads / empty NC pads | 180 / 7 |
| Source nets / external boundary nets | 40 / 8 |
| Track segments / through vias | 753 / 93 |
| Filled ground zones | 1, B.Cu GND |
| Unique UUIDs | 2,231 / 2,231 |
| Candidate outline | closed 125 × 115 mm rectangle |
| Raw native DRC violations / unconnected / ignored checks | 0 / 0 / 0 |

The native pad audit and a separately implemented standard-library parser both pass. The independent checker reads the actual CAD, source input, real footprint candidates and raw DRC without importing router/generator code. It verifies reference/pad/net equality, actual footprint IDs and geometry including rotations, the seven NC pads' geometric isolation, the eight boundary names, 18 excluded RF-port references, unique UUIDs, outline and routing/zone net identities. Negative checks rejected a wrong net, an ignored DRC category and copper across an NC pad.

The generation DRC of the re-frozen board (KiCad 10.0.7, native zone filling) returned exit 0. `pcb/generate_routed.py` now repeats native DRC on the published copy, which resolves footprints through the portable relative `fp-lib-table`; for the 23.10.2026 re-freeze that repeat also returned exit 0 and is stored as `drc-portable-raw.json` (the generator refuses to publish if it does not). Both reports include error, warning and exclusion severities, and neither has ignored check categories. All five normally ignored categories were explicitly enabled as warning. Raw reports are retained unchanged as `build/kicad/pcb-prototype/drc-raw.json` and `drc-portable-raw.json`; no findings were suppressed or filtered. Full-project schematic parity was not requested for this subset board. Instead, preparation checks connected subset source nodes against the full XML netlist, then native and independent checks compare the exact subset to PCB pads.

## Layout choices and limits

The spaced starter was not routed in place: its SENSE capacitor-to-second-comparator distances were about 32.7 mm. In the prototype, each SENSE island is confined to **5.125 × 7.05 mm** of F.Cu routing with **zero SENSE vias**. Total trace-tree lengths are 17.640877 mm for each of UHF, L-band and HF (computed from the `routing` records of the JSON). Total tree length includes all branches. These dimensions describe the CAD; they are not electrical acceptance limits.

Comparator bypasses and the LM4040 bypass were moved beside their relevant pins; local ground escapes feed the bottom ground plane. The threshold/reference network is separated from the output/gate circuitry. B.Cu has a broad ground pour with approximately 120.1 mm total signal crossover routing. Front and bottom previews were inspected separately so the ground fill does not conceal the front copper. Reference labels, pads, bypasses and candidate warnings are legible; native courtyard, silkscreen, copper clearance and hole-spacing checks pass.

`E4_DCS_RETURN` and `E4_DCS_REF_RETURN_MID` remain switched signal nets. Neither was renamed, poured or shorted to GND. No DCS pullups were added; the pullups remain in E3. The board routes filtered DC TAP nets only. The first RF taps/capacitors and twelve hot bleed resistors, 18 source references in total, remain excluded and must be implemented at the RF ports.

The prototype rules are 0.20 mm track width and clearance, 0.60 mm via diameter / 0.30 mm drill, 0.25 mm hole-edge spacing and 0.50 mm copper-to-edge minimum. The two-layer configuration, copper weight, material, outline, mounting and case fit are unapproved candidates. The router's grid collision model is not the acceptance test: actual native DRC and a separate CAD audit establish the reported copper result.

TI's TLV301x datasheet Rev C §10.5 recommends local decoupling, ground planes and careful treatment of high-impedance nodes. TI's LM4040 datasheet Rev Q §8.4 recommends close external parts, cathode bypassing and separating analog/digital routing. Those primary references informed the placement; no simulation or fabrication performance is inferred from those recommendations:

- https://www.ti.com/lit/ds/symlink/tlv3011.pdf
- https://www.ti.com/lit/ds/symlink/lm4040.pdf

## Physical implementation and test gates

The eight physical interfaces are **not implemented**. No connector, cable pad or invented module pin was added:

| Boundary | Actual core endpoint(s) | Remaining decision |
|---|---|---|
| 3V3_Q6A, GND | Existing supply/return component pads | Supply/return connector or wire-pad implementation, mating target and location |
| DCS_UHF, DCS_LBAND, DCS_HF | Q450.3, Q452.3, Q454.3 | Physical output interconnect to E3, retaining its external pullups |
| E4_DCS_UHF_TAP, E4_DCS_LBAND_TAP, E4_DCS_HF_TAP | R4421.1, R4431.1, R4441.1 | Physical filtered-DC interconnect from the RF-port tap assemblies |

Six of these nets have one core pad. KiCad can report zero unconnected items on such nets even though no usable external connection exists. The bare 0402 and transistor pads are source circuit terminals, not approved harness terminations.

Before fabrication/release, select the interconnect implementation and its pinout/strain relief; approve manufacturer MPNs and land patterns for all **50 passive proposals**; approve enclosure/mounting/stackup and assembly/cleaning process; and implement the separate RF-port tap/bleed assemblies. The three R0402 KiCad resources are now bundled with official 10.0.7 provenance; fetching that resource is resolved, while selecting and qualifying the actual precision resistors is still open.

Hardware must verify the source's threshold, leakage, temperature, supply, ground-offset and RF behavior, startup/reference failures and rail-off/backfeed behavior. The analytical corner has only **1.370 mV** remaining margin to the 100 mV port threshold. A DRC pass does not validate contamination leakage, guard effectiveness, assembly effects, thermal offsets, or that margin. No functional or production qualification is claimed.

## Reproduction and reviewed hashes

```sh
python3 pcb/generate_routed.py --runtime-root /tmp/kicad-runtime/root --kicad-cli /tmp/kicad-runtime/kicad-cli
python3 verification/pcb-prototype-review-check.py
```

The first command uses the current official KiCad 10.0.7 extracted runtime plus NumPy/SciPy. On an installed KiCad Python system, omit both runtime arguments. The second command requires only Python's standard library and reads repository-relative defaults. Optional PyMuPDF renders the native SVG previews. Runtime and official footprint provenance remain in `design/runtime-review.md`, the original footprint manifests/license, and `build/kicad/pcb-preparation/footprint-provenance.json`.

The portable repeat is the same native command against the published project:

```sh
kicad-cli pcb drc --format json --severity-all --all-track-errors --exit-code-violations --output build/kicad/pcb-prototype/drc-portable-raw.json build/kicad/pcb-prototype/detector-core-routed-prototype.kicad_pcb
```

The router sorts each net's pins before routing, so its geometry no longer depends on KiCad's UUID-ordered board files: two independent CI re-freezes on 23.10.2026 produced identical track endpoints (2800 start/end records), differing only in native UUIDs. In the CI workflow the re-freeze runs on manual dispatch with `refreeze_pcb=true`. Reviewed SHA-256 after the 23.10.2026 re-freeze (the 20.10 values are in Git history):

- Source input: `e1f11f659704c558b1f98bef9aadcfb795d2d2443ef2a84e4ea529eb447f2746`
- Frozen starter: `baf16f51f6b56cb41e33f486c94d556fbab217542a32202d8e8b7c76b0769d48`
- Routed prototype: `5a517890b3661f4e291fefd61053610ab2699c20fde2cc0b501a30411c189c1f`
- Generation raw DRC: `45a44d7cc66ea094d7d9cc381c1dfc231db135f6a3595a0b71c3f5d02435824b`
- Portable repeat DRC: `797614bbb38f27a2bd40744fa422afebd985c12a40b3927d40395e0b1498eb5c`

`pcb-prototype-review.json` retains the full native routing inventory and independent audit. Re-run the checks after any geometry, resource or input change; regeneration changes native UUIDs.
