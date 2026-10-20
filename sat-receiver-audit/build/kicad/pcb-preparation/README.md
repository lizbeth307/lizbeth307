# Unrouted DC detector core placement

**NOT FOR FABRICATION. No Gerbers.** The `.kicad_pcb` is a concrete 71-component KiCad 10 placement starter using real portable footprint candidates, with every source physical pin assigned to its original net. It has no tracks, vias or zones. The 125 × 115 mm outline and two-layer configuration are engineering candidates; enclosure fit, mounting and stackup remain unapproved.

Open `detector-core-placement.kicad_pcb` in KiCad; the adjacent project and relative `fp-lib-table` resolve the bundled resources. `detector-core-placement.svg` and `.png` provide native board previews. The board silkscreen marks the unreleased status.

The native read-back audit and independent parser confirm 71 parts, 187 pads, 180 connected pads, seven NC pads and 40 nets. The eight external boundary nets have no invented connector pads. Eighteen RF-port tap/bleed components are excluded, so no RF transmission-line routing is present. Fifty passive footprints remain unqualified placement proposals.

`drc-raw.json` is the full unfiltered KiCad result: **140 unconnected errors, zero other/geometric violations, zero ignored checks; DRC exit 5**. The five normally ignored check categories are explicitly enabled as warning in the project. There is no production DRC pass. Full-project schematic parity was not requested for this subset board; exact source-node → subset-pad correspondence is audited separately.

- `placement-audit.json`: every source pin, board pad, net, position and resource hash.
- `footprint-provenance.json`: official KiCad 10.0.7 R0402 package/resource hash and license reference.
- `drc-command.log`, `svg-command.log`: native command output.
- `../../../verification/pcb-review.md` and `.json`: review details and release gates (paths relative to this folder).

From the repository root, with KiCad Python and CLI installed:

```sh
python3 pcb/generate_layout.py
python3 pcb/generate_layout.py --check
```

In the current container, the official Ubuntu KiCad 10.0.7 package and its runtime dependencies were extracted locally. Use:

```sh
python3 pcb/generate_layout.py --runtime-root /tmp/kicad-runtime/root --kicad-cli /tmp/kicad-runtime/kicad-cli
python3 pcb/generate_layout.py --runtime-root /tmp/kicad-runtime/root --check
```

The runtime-root option sets `LD_LIBRARY_PATH` and `PYTHONPATH` before importing native `pcbnew`; this is optional on an installed KiCad system. The script validates real footprint pin sets, generates and native-parses the board, performs an exact source-to-pad audit, invokes raw DRC with all severities, and exports the native SVG. PyMuPDF optionally renders the PNG. Generated output is atomically published. The read-only `--check` verifies source/board/resource snapshot consistency; it does not assert production readiness.

Regenerating changes native UUIDs; repeat the consistency audit after changes and update snapshot review hashes before any release claim. Run `python3 pcb/prepare.py` and its `--check` before generation when source metadata changes.

The independent checker uses only the Python standard library and reads the source input, board and raw DRC directly, without importing generator code or requiring native KiCad:

```sh
python3 verification/independent_pcb_check.py
```

It exits nonzero on mismatched components/pads/nets, invalid NCs/footprint IDs, duplicate UUIDs, unexpected routing, invalid outline, excluded RF-port components or incomplete raw DRC coverage.
