# Portable footprint dependency verification

Date: 2026-10-19. Runtime: KiCad 10.0.7.

The current graphs contain **176 footprint assignments**, resolved by **16 official footprint files** in **6 project-local libraries**. No footprint assignments were removed to silence ERC. The exact selected files, SHA256 values, component references and pad numbers are in `build/kicad/footprints/manifest.json`.

| Project-local library | Selected footprint files |
|---|---:|
| `Capacitor_SMD` | 3 |
| `Diode_SMD` | 2 |
| `Package_SO` | 4 |
| `Package_SON` | 1 |
| `Package_TO_SOT_SMD` | 4 |
| `Resistor_SMD` | 2 |

## Provenance and portability

- Source: [official KiCad 10.0 release PPA package](https://ppa.launchpadcontent.net/kicad/kicad-10.0-releases/ubuntu/pool/main/k/kicad-library-footprints/kicad-footprints_10.0.7~ubuntu24.04.1_all.deb), version `10.0.7~ubuntu24.04.1`.
- Package SHA256 verified against the PPA index: `a1c25a690348180d572b73496668cffafdaecf284d6555279fa89d5e4fefa46c`.
- Only the selected `.kicad_mod` files were copied; footprint contents are unmodified. `build/kicad/fp-lib-table` uses `${KIPRJMOD}/footprints/<library>.pretty` paths.
- The original KiCad library license is included at `build/kicad/footprints/LICENSE.md` (CC-BY-SA 4.0 with KiCad design-output exception).
- All declared pin numbers of footprint-assigned components are present as pad numbers in the selected file. This checks numbering coverage; it does not certify placement, orientation, current rating, soldering or PCB layout.

## Corrected identifiers

- `U102`: nonexistent `Package_SO:VSSOP-10_3x3mm_P0.5mm` was corrected by E1 to the existing `Package_SO:MSOP-10_3x3mm_P0.5mm`. Both the KiCad footprint and TI DGS0010A drawing reference JEDEC MO-187 BA. The bundled KiCad IPC land pattern differs from the TI example, so layout and assembly verification remain required.
- `D202/D203`: nonexistent `Diode_SMD:D_SOD-123W` was corrected by E2 to the actual standard name `Diode_SMD:Nexperia_CFP3_SOD-123W` after matching the Nexperia PMEG4030ER package.

## ERC disposition

Footprint-resource resolution does not alter electrical nets, power flags or ERC exclusions. The earlier unpowered DNP A422 boundary was a real initial circuit gap; the finalized E4 graph now selects an active LaNA WB module and an E2 protected supply branch. The final raw ERC and independent graph-to-netlist comparison must evaluate that new circuit, rather than reuse the earlier DNP conclusion. Physical supply/module qualification remains governed by the E2/E4 hardware acceptance notes.

Rerun the full project after regenerating the schematics from the latest graphs:

```bash
kicad-cli sch erc --format json --severity-all --exit-code-violations --output verification/erc.json build/kicad/sr-rx-v2.kicad_sch
```

This report records resource preparation. The final raw ERC and separate independent XML-netlist comparison establish the final generated-project status.
