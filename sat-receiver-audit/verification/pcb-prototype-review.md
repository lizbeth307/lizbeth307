# Routed DC_CORE internal prototype review

**Internal routing is complete and verified; this is NOT FOR FABRICATION.** A separate compacted prototype preserves the frozen 71-part DC_CORE source exactly. The frozen placement starter, source graphs and schematics remain unchanged. No Gerbers or drill files were generated.

## Verified result

| Property | Result |
|---|---:|
| Components / physical pads | 71 / 187 |
| Connected pads / empty NC pads | 180 / 7 |
| Source nets / external boundary nets | 40 / 8 |
| Track segments / through vias | 729 / 93 |
| Filled ground zones | 1, B.Cu GND |
| Unique UUIDs | 2,207 / 2,207 |
| Candidate outline | closed 125 × 115 mm rectangle |
| Raw native DRC violations / unconnected / ignored checks | 0 / 0 / 0 |

The native pad audit and a separately implemented standard-library parser both pass. The independent checker reads the actual CAD, source input, real footprint candidates and raw DRC without importing router/generator code. It verifies reference/pad/net equality, actual footprint IDs and geometry including rotations, the seven NC pads' geometric isolation, the eight boundary names, 18 excluded RF-port references, unique UUIDs, outline and routing/zone net identities. Negative checks rejected a wrong net, an ignored DRC category and copper across an NC pad.

Two real KiCad 10.0.7 runs returned exit 0: generation with native zone filling, and a repeat using the published relative-library project. Both include error, warning and exclusion severities, and neither report has ignored check categories. All five normally ignored categories were explicitly enabled as warning. Raw reports are retained unchanged as `build/kicad/pcb-prototype/drc-raw.json` and `drc-portable-raw.json`; no findings were suppressed or filtered. Full-project schematic parity was not requested for this subset board. Instead, preparation checks connected subset source nodes against the full XML netlist, then native and independent checks compare the exact subset to PCB pads.

## Layout choices and limits

The spaced starter was not routed in place: its SENSE capacitor-to-second-comparator distances were about 32.7 mm. In the prototype, each SENSE island is confined to **5.125 × 7.05 mm** of F.Cu routing with **zero SENSE vias**. Total trace-tree lengths are UHF 17.499455 mm, L-band 17.640877 mm and HF 17.499455 mm. Total tree length includes all branches. These dimensions describe the CAD; they are not electrical acceptance limits.

Comparator bypasses and the LM4040 bypass were moved beside their relevant pins; local ground escapes feed the bottom ground plane. The threshold/reference network is separated from the output/gate circuitry. B.Cu has a broad ground pour with approximately 119.1 mm total signal crossover routing. Front and bottom previews were inspected separately so the ground fill does not conceal the front copper. Reference labels, pads, bypasses and candidate warnings are legible; native courtyard, silkscreen, copper clearance and hole-spacing checks pass.

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

The second portable native check used:

```sh
kicad-cli pcb drc --format json --severity-all --all-track-errors --exit-code-violations --output /tmp/sr-rx-proto-portable-drc.json build/kicad/pcb-prototype/detector-core-routed-prototype.kicad_pcb
```

Its JSON was retained byte-for-byte as `drc-portable-raw.json`. Reviewed SHA-256:

- Source input: `e0fb2d49421ffe4ac388af1e239a5342cb782f46ec4ab00048a3459b0ee428d9`
- Frozen starter: `2fe4de9b11293c0af930ee4e919f6f832fb0fc8994c51a132b2c9053df9fc862`
- Routed prototype: `c6992a48231194bb25a983757c3f5e1e381b9a746d215ca7f0f31a8325652158`
- Generation raw DRC: `52dcd3e72a52249098fed1306a48460d81aeb86fd5d4e5906c3b2848958c3d5c`
- Portable repeat DRC: `43f4e0042b8a3af92698c605a02b2dcb9840b4f8244c7b2ab1bd88bbbc4c4674`

`pcb-prototype-review.json` retains the full native routing inventory and independent audit. Re-run the checks after any geometry, resource or input change; regeneration changes native UUIDs.
