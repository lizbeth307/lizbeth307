# Independent PDF visual verification

Result: **PASS**, 2026-10-23 (after the schematic was redrawn with wires).

The PDF opens cleanly in Poppler and PyMuPDF: **14 A2 pages** (contents page plus 13 electrical pages), **764,564 bytes**, no repair needed. No text span lies outside a page, no page title leaves the drawing frame and there are no replacement glyphs on any page.

What was inspected: all 14 pages in a Poppler contact sheet; the first page of E1, E2, E3, E4 and E5 at 75 dpi; and the dense areas in 110–160 dpi crops while the layout was tuned (E1 AON/UV and IP2368, E2 eFuse and LNA groups, E3 MCP23017 pull-up bank and Q6A header, E4 RF chains and DC detectors, E5 PCIe riser and HDMI pass-through). No missing pages, cut-off components or overlapping group blocks were found. An automated check of the generator geometry found no overlap between symbol bodies, reference/value texts and labels.

Drawing, from `build/kicad/generation-manifest.json`: 2596 wires, 429 junctions, 916 global labels (one per wire tree), 471 GND symbols. The previous drawing had 2206 wire stubs and 2206 global labels, one per pin.

Known minor issues (none affects the netlist, because a KiCad label connects only at its anchor):

- E5_02, HDMI pass-through J520–U520: E5_HDMI_SCL, E5_HDMI_SDA and E5_HDMI_HPD lie along their own wire. The vertical label E5_HDMI_D2_N crosses neighbouring bus wires.
- Long buses (E3 MCP23017 pull-up bank, E5 PCIe riser) keep some wire crossings without junctions; a crossing is not a connection.
- On E2–E4, larger group blocks are placed first to avoid a nearly empty last page. Groups are never split across columns, but their order differs from `design/E#.json`.

Update 2026-10-23: open item E5-10 (bench gate W1-2, WIFI_PWR_EN hold) was added as a framed note above U500 on page 13 (E5 1/2). Nothing else on the drawing changed and `verification/netlist.xml` is byte-identical. Page 13 was re-inspected in full at 60 dpi and the note at 150 dpi (inside its frame, no overlap); the automated checks were repeated on all 14 pages (0 text spans outside a page, 0 replacement glyphs, title blocks inside the frame).

Final SHA256: `15f550c4e905230e7fb192c30502f8b94d4212334e89cd9c255af6901323557b` (previous: `d02ec6fc75f6d8162e6fe8a06a4d1b4f737deda79ed396ac0c4968880421f18b`).

Exact page checks: `verification/pdf-visual-review.json`. Electrical agreement is recorded separately in `verification/validation.json` and `verification/independent-netlist-review.json`. Hardware acceptance gates remain open in the project documentation.
