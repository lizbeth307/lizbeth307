# KiCad runtime and original-library verification

Date: 2026-10-19. Source repository commit: `465318835e71eae326059f5f66e2b47232169556`.

## Runtime

- KiCad CLI: **10.0.7**; Ubuntu 24.04 amd64 package `10.0.7~ubuntu24.04.1`.
- Primary package source: [official KiCad 10.0 releases PPA](https://ppa.launchpadcontent.net/kicad/kicad-10.0-releases/ubuntu/dists/noble/main/binary-amd64/Packages.xz).
- KiCad package SHA256: `ce96f7c3bd935a021c65b301427f74c1c16b211210b49ce9b40309ce5ecfbb33`.
- Symbols package SHA256: `3fbd4a8528760697456bfbd8da677d255e4cea2dcd3e938ad9ebe6006f861da3`.
- Both hashes verified against the package index. Dependencies came from the configured Ubuntu noble snapshot; packages were extracted into a temporary runtime. No project source was changed by verification.
- This session launcher: `/tmp/kicad-runtime/kicad-cli`. Standard symbols: `/usr/share/kicad/symbols` (10.0.7). These temporary runtime locations are not project dependencies.

## Original libraries

Commands were run against `git-source/sat-receiver-audit/build/kicad`, not regenerated libraries.

| Library | Top-level symbols | Exported unit SVGs | Pin declarations | Repeated numbers within a symbol |
|---|---:|---:|---:|---:|
| `sr_rx_v2_pwr.kicad_sym` | 16 | 16 | 101 | 0 |
| `sr_rx_v2_sig.kicad_sym` | 20 | 20 | 198 | 0 |

Both `sym export svg` processes returned exit status 0. This verifies that KiCad can parse and render every original custom symbol. It does **not** verify the electrical design, datasheet pin assignments, module connector orientation, footprints, or a complete project ERC.

Original file hashes:

- `sr_rx_v2_pwr.kicad_sym`: `046433ebdb6ef986795dd02d0ad77b675f13c4eda3941bc9ac7585b49d8bcb67`.
- `sr_rx_v2_sig.kicad_sym`: `7effe947a1a8ce9f25931c6af40dbe56c0f8f99a9688209947438c91321eee78`.

```bash
kicad-cli version
kicad-cli sym export svg --output review/pwr-svg build/kicad/sr_rx_v2_pwr.kicad_sym
kicad-cli sym export svg --output review/sig-svg build/kicad/sr_rx_v2_sig.kicad_sym
```

## Serializer fixture

A separate two-sheet fixture was generated in temporary storage. It used an embedded `Probe:Pass` symbol, its standalone `Probe.kicad_sym` library, two physical pin numbers, actual wires, global labels on both sheets, and per-project symbol/sheet instances. All four schematic operations below returned exit status 0. ERC reported 0 violations. The XML netlist contained `NET_A` with `U1.1` and `U2.1`, and `NET_B` with `U1.2` and `U2.2`; the PDF contained two pages.

```bash
kicad-cli sch export svg --output review/svg probe.kicad_sch
kicad-cli sch export pdf --output review/probe.pdf probe.kicad_sch
kicad-cli sch export netlist --format kicadxml --output review/probe.xml probe.kicad_sch
kicad-cli sch erc --format json --severity-all --exit-code-violations --output review/erc.json probe.kicad_sch
```

Verified serializer details:

- Schematic format `20250114`; standalone symbol-library format `20241209`.
- Root-symbol instance path: `/<root_uuid>`.
- Child-symbol instance path: `/<root_uuid>/<sheet_instance_uuid>`; do not substitute the child document UUID.
- Child sheet instances path in the parent: `/<root_uuid>` with its page number.
- Root `sheet_instances`: `(path "/" (page "1"))`.
- Embedded symbol name `Library:Name`, standalone name `Name`, internal groups `Name_0_1` and `Name_1_1`.
- Every wire connects to the symbol pin physical anchor. Global labels are placed at the intended wire endpoint.

Reference: [KiCad schematic S-expression documentation](https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/).

The fixture result establishes tool and serialization capability. The reconstructed E1–E5 must still undergo their own ERC and connectivity comparison.
