# Allnet 64 gb microsd adafruit 5212 reade: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_071e1025-145`_

- **Part:** Recovery set: rescue microSD (64 GB) + microSD reader + Adafruit 6324 C-to-A 2 m cable + USB3 A-A EDL cable (core, group Recovery, 1 set; re-audit D specifies 2 rescue cards)
- **Current pick:** ALLNET 64 GB microSDXC UHS-1 ALN-TFUHS1-64 (x1 in STACK, x2 per reaudit_D) + Adafruit 5212 USB-C microSD reader + Adafruit 6324 woven USB-C to USB-A 2 m cable + unnamed USB3 A-A cable ($5.00 placeholder, no seller)
- **Current price usd:** 31.89 ex VAT for 1 card (16.99 + 6.95 + 2.95 + 5.00 placeholder). 48.88 with re-audit D's 2 cards, which governs. All three named prices re-checked live on 18 Oct 2026 (ALLNET JSON: SKU ALN-TFUHS1-64, 1699 cents, available). For an EU buyer the ALLNET (CN) and Adafruit (US) items also carry import VAT and the flat-rate EU duty in force since 1 Jul 2026 (operator note 34; amount unverified), plus shipping.
- **Decision:** replace_conditionally
- **Chosen:** Cards: 2x Verbatim Pro U3 microSDXC 64 GB, part 47042 (EAN 0023942470427), from Reichelt. If it fails the random-I/O gate, use 2x PNY Pro Elite microSDXC 64 GB P-SDU64GV31100PRO-GE (Reichelt) instead. EDL cable: Goobay 95717 USB 3.0 A-plug to A-plug, 1.0 m, 28 AWG, 3x shielded (Reichelt, same order). KEEP the Adafruit 5212 and the Adafruit 6324: no cheaper reader or cable was proven not-worse. Optional, conditional swap: Transcend TS-RDF5K in place of the 5212 + 6324 (see conditions).
- **Chosen price usd:** 35.60 ex VAT for the 2-card set: 2x11.29 Verbatim + 3.12 Goobay + 6.95 (5212) + 2.95 (6324). 24.31 for the 1-card set. Reichelt prices incl. 19% DE VAT: Verbatim EUR 11.95 ($13.43), Goobay 95717 EUR 3.30 ($3.71); the Reichelt part of the order (2 cards + cable) is EUR 27.20 = $30.58 incl. VAT. Reichelt shipping is extra, "from EUR 5.95" ($6.69 incl., $5.62 ex), for DE; other EU destinations unverified. PNY fallback: EUR 13.50 incl. = $15.18 incl. = $12.75 ex per card, so the 2-card set costs 38.52. FX: EUR x 1.1241, the stack's rate.
- **Saving usd:** 2-card set (governing): 13.28 ex VAT before shipping (48.88 -> 35.60), or about 7.66 after a separate Reichelt shipment ($5.62 ex VAT). 1-card set: 7.58 before shipping (31.89 -> 24.31), about 1.96 after. PNY fallback: 10.36 (2 cards) or 6.12 (1 card) before shipping. The EU landed saving is larger than these ex-VAT figures, because the ALLNET cards would also pay import VAT, the flat duty and CN shipping. The optional RDF5 swap saves another 2.39 (9.90 -> 7.51) and comes off the Adafruit order.
- **Equivalence proof:** CARD, Verbatim 47042 vs ALLNET ALN-TFUHS1-64. Every published ALLNET spec is matched or beaten:
  - Capacity: both 64 GB nominal microSDXC.
  - Bus: both UHS-I. Verbatim adds U3, i.e. a guaranteed minimum sustained write of 30 MB/s (V30 per Reichelt; the Verbatim page states U3 only). ALLNET has no class at all.
  - Max read: 90 vs 80.6 MB/s. Max write: 45 vs 42.0 MB/s. These are vendor max figures for both. The Q6A slot caps reads at about 73.7 MB/s (Geerling #85 via reaudit_D), so in the slot both cards are capped by the slot on read.
  - Build: water- and shock-resistant claim vs none.
  - Traceability: genuine brand with a traceable EAN, sold by Reichelt (a large German distributor), with a Verbatim 2-year limited warranty (Verbatim Europe general terms). The ALLNET card has an unknown OEM, no published warranty and no temperature rating.
  - Unknown on both sides: random 4K IOPS (neither card is A-rated), temperature range, and real capacity (ALLNET states 59.5 GB; Verbatim states none). These are closed by the bench gate below.
  PNY fallback: 100/90 MB/s, U3/V30/A1. A1 is a rated minimum of 1500 read / 500 write IOPS, so it beats ALLNET even on random I/O; EU responsible person is PNY Europe. Its warranty and temperature range are verified only for PNY's current 128 GB+ line (lifetime limited, -25 to 85 C), not for this 64 GB EU SKU.
  A-A CABLE, Goobay 95717 vs the placeholder (which had no spec):
  - USB 3.0 5 Gbit/s, A-plug to A-plug, 1.0 m as the requirement asks, 28 AWG, 3x shielding, CE/RoHS, Wentronic (DE) brand.
  - It beats the ALLNET 158949 alternative ($3.95, shielding unstated, ships from CN) on price and on documentation.
  READER and 6324: no candidate was both cheaper than the $6.95 5212 and proven not-worse, so both are kept.
  HARD RULES: all items are passive service-kit parts with no RF or TX role. Receive-only, no-loop and conducted-only rules are unaffected.
- **Rejected:**
  1.
    - **Name:** Transcend RDF5 TS-RDF5K as an unconditional 1:1 replacement (Reichelt EUR 7.95 incl. = $7.51 ex)
    - **Why:** It costs MORE than the 5212 alone ($7.51 vs $6.95). It is 'cheaper' only if the 6324 is deleted, which removes a part rather than finding an analog. It also loses the USB-C plug, the 5212's only working role (a USB-C-only laptop). The datasheet does confirm USB 2.0/3.0, microSDXC UHS-I, 56x24x8.9 mm, 18 g and a 2-year warranty, so it is accepted only as the conditional swap.
  2.
    - **Name:** PNY Pro Elite 64 GB as first choice
    - **Why:** It is not worse; it is $1.46 per card dearer than the Verbatim, which already matches or beats every published ALLNET spec. Kept as the fallback if the Verbatim fails the A1-floor gate. The pibenchmarks 'PNY SD Pro Elite (SD64G)' page (30 tests, average 2,252) is a CID bucket mixing PNY, Arcanite and Cytron cards, so it is not SKU-specific evidence.
  3.
    - **Name:** Kingston Canvas Select Plus Gen3 64 GB (TinyTronics EUR 18.50 = $17.19 ex)
    - **Why:** Dearer than ALLNET ex VAT ($17.19 vs $16.99). Only U1/V10, and write speed not stated. It would ride the TinyTronics board order for free, but 2 cards there ($41.59 incl.) still cost more than 2 Verbatim + Reichelt shipping ($33.55 incl.).
  4.
    - **Name:** Other TinyTronics 64 GB cards (Samsung EVO Plus 64 GB V10 EUR 22.50; SanDisk Ultra 64 GB EUR 27.00; SanDisk Extreme 64 GB EUR 33.99)
    - **Why:** All dearer than ALLNET; EVO Plus 64 GB and Ultra are U1-class only.
  5.
    - **Name:** Raspberry Pi A2 64 GB (Adafruit 6011 $12.79)
    - **Why:** Out of stock. EU sells only the preloaded SKU (Pi Hut GBP 30.60, UK, now with EU flat duty and DHL Express), and sequential speeds are unpublished.
  6.
    - **Name:** SanDisk Nintendo Switch 64 GB EUR 11.79; Patriot EP; Kioxia Exceria; Philips FM64MP65B; Samsung 64 GB
    - **Why:** Not purchasable, dearer ex VAT, write speed unpublished, or price unverified (pages returned 403), per search notes. None is a verified candidate.
  7.
    - **Name:** Generic, no-name or used 64 GB cards (AliExpress, marketplace lots)
    - **Why:** Fake-capacity and counterfeit risk; fails the not-counterfeit rule.
  8.
    - **Name:** Kingston MobileLite Plus MLPM (Alternate EUR 9.29 incl. = $8.78 ex)
    - **Why:** Not shippable ('available soon'), dearer than the 5212, USB-A only.
  9.
    - **Name:** LogiLink CR0049 USB 3.2 Gen1, USB-A + USB-C (Reichelt EUR 9.95 = $9.40 ex)
    - **Why:** Dearer than the 5212 ($9.40 vs $6.95). UHS mode, chipset and warranty not stated. Storage-box form (listing 85x62x95 mm, 31-46 g). It saves money only if the 6324 is deleted, and only $0.50.
  10.
    - **Name:** LogiLink CR0034A USB 3.0 USB-A ($6.56 ex)
    - **Why:** Loses the USB-C plug. UHS-I mode, chipset and warranty unverified; budget brand.
  11.
    - **Name:** Goobay 38656 USB 2.0 USB-A reader ($4.68 ex)
    - **Why:** Loses USB-C; SDXC/64 GB support not verified.
  12.
    - **Name:** Berrybase 2-in-1 microSD reader USB-A + USB-C, USB 2.0, art. 125454 (EUR 3.90 incl. = $3.68 ex)
    - **Why:** The page names no microSDHC/SDXC support, maximum capacity, speed or chipset, and it has 0 reviews, so 64 GB SDXC operation is unproven. It also needs a separate Berrybase order (free shipping only from EUR 200).
  13.
    - **Name:** ALLNET USB-C microSD reader ACC-USBC2SDXC-READER ($3.49)
    - **Why:** Out of stock (JSON available=false).
  14.
    - **Name:** The Pi Hut Mini USB 2.0 / Mini USB-C microSD readers
    - **Why:** UK seller: EU flat duty + VAT + DHL Express since 1 Jul 2026 erase the saving. No speed or SDXC data. The USB-A one loses USB-C.
  15.
    - **Name:** DIY: write the rescue card in the Q6A's own slot, no reader
    - **Why:** Cannot write a card when the Q6A will not boot, which is the rescue case. The slot also has no case opening (STACK panel list).
  16.
    - **Name:** ALLNET USB 3.0 A-A 1 m SKU 158949 ($3.95 ex)
    - **Why:** Dearer than the Goobay 95717 ($3.12 ex), shielding/AWG not stated, and ships from CN (EU import VAT + flat duty unless it rides an ALLNET order, which the EU build no longer needs).
  17.
    - **Name:** Goobay 95716 0.5 m at Berrybase (EUR 2.86)
    - **Why:** 0.5 m is shorter than the ~1 m requirement (hatch to bench PC) and needs a separate Berrybase order.
  18.
    - **Name:** Nedis CCGB61000BK10 USB 3.0 A-A 1 m (Reichelt EUR 5.19)
    - **Why:** Dearer; AWG and shielding not stated.
  19.
    - **Name:** The Pi Hut USB 3.0 A-A 1 m (GBP 3.00)
    - **Why:** UK: EU flat duty, VAT and express shipping.
  20.
    - **Name:** Goobay 93593 / Digitus USB 2.0 A-A cables
    - **Why:** No SuperSpeed pairs, a spec loss against the USB 3 requirement while the Firehose USB 3 behaviour on QCS6490 is unverified.
  21.
    - **Name:** Alternatives to the Adafruit 6324 (Pi Hut 2 m GBP 4.50)
    - **Why:** No cheaper 2 m data cable found; the 6324 at $2.95 stays.
- **Confidence:** medium
- **Conditions or tests:** ON ARRIVAL, each card:
  1. f3write/f3read over the full card must pass. Record the real byte count against ALLNET's 59.5 GB. The rescue set (_512 image, _4096 UFS image, BIOS 260120 zip, edl-ng, 2x 32 MiB SPI dumps, SHA-256 lists) must fit with at least 2x margin.
  2. In the Q6A slot, the sdhci-msm debugfs 'ios' must show SDR104 at 1.8 V.
  3. fio 1M sequential: read must reach the slot cap (about 70+ MB/s) and write must be at least 42 MB/s.
  4. fio 4K random, QD1: at least 1500 read IOPS and 500 write IOPS (the A1 floor). If the Verbatim misses this, switch to the A1-rated PNY.
  5. 20 cold boots from the slot, plus a dd-and-SHA-256 refresh of the image through the 5212 on the PC.
  
  A-A CABLE:
  1. Meter it: D+ 2-2, D- 3-3, GND; note whether VBUS is connected. Tape the VBUS pin at the PC end.
  2. EDL with J21 power only: the board must enumerate as 05c6:9008.
  3. Two whole-chip edl-ng reads (33,554,432 B) must give the same SHA-256.
  
  OPTIONAL SWAP (5212 + 6324 -> TS-RDF5K) is allowed only if all three hold:
  (a) the service PC has USB-A. The stack already assumes this, because the A-A EDL cable needs it.
  (b) the 6324 has no other user in the stack.
  (c) the user accepts losing the USB-C plug.
  Then bench it: at least 20 USB boots from the rescue card through the RDF5 on the blue USB-A, and lsusb -t shows uas/usb-storage. Use it only outside L-band/GNSS sessions (SuperSpeed RFI, operator note 7).
  
  Availability: Reichelt shows 'limited stock' for both cards; check at checkout.
- **Stack changes:** 1. BOM row 'Відновлення' (STACK line 176):
     - Cards become 2x Verbatim 47042 (fallback PNY P-SDU64GV31100PRO-GE), from Reichelt.
     - The A-A cable becomes Goobay 95717 1 m (Reichelt), with a real price ($3.12 ex) instead of the $5.00 placeholder.
     - The 5212 and 6324 stay on the Adafruit order.
     - Add one Reichelt order: 2 cards + cable, shipping from EUR 5.95.
     - Remove the 'microSD 64 GB $16.99' line from the ALLNET order (shopping plan line 1118).
  2. Do not double-buy the A-A cable: it is also listed in the cable-kit composition (line 286).
  3. DEFECT in the current set (independent of the swap), to record in v2:
     - The 5212 has a USB-C plug and the 6324 is C-male to A-male, so they cannot be joined.
     - The 5212 cannot plug into any handheld port (LAB USB-A, blue USB-A).
     - The Q6A microSD slot has no case opening (panel list, lines 76 and 896).
     - So a field rescue needs the case opened, or a USB-A reader for USB boot (USB is first in boot order).
     - My engineering reading of the Type-C spec: the 6324's C plug carries an Rp pull-up, so a USB-C-only laptop will not act as EDL host through it. EDL from such a laptop needs a C-to-A OTG adapter (Rd) plus the A-A cable.
     - Either document the 6324's real user, or take the RDF5 swap under the stated conditions.
  4. Do the USB rescue boot on the blue USB-A in the hatch, with the T7 unplugged in the Lime build. Do not use the LAB USB-A for it: that port sits behind FE1.1s -> CH334F with TPS2553 EN driven by MCP23017 GPA0 (line 616), and its EN state at UEFI time, before Linux runs, is unverified.
  5. No changes to rails, drivers (usb-storage/uas, standard UMS) or case. The RDF5 (if used) protrudes 56 mm only while it is plugged in.
  6. Method limit: the shared WebSearch budget was exhausted at this step (my one search was refused). There are no independent reviews or measurements of the Verbatim 47042, PNY 64 GB, 5212 or RDF5; all evidence is from manufacturer pages, distributor listings and the datasheet, fetched 18 Oct 2026. A follow-up can resume the search.
- **Sources:**
  - https://shop.allnetchina.cn/products/allnet-micro-sd.js
  - https://www.adafruit.com/product/5212
  - https://www.adafruit.com/product/6324
  - https://www.reichelt.com/de/en/shop/product/microsdxc-card_64gb_-_verbatim_-_class_10_-_u3-182524
  - https://www.verbatim-europe.com/en/prod/pro-u3-microsdxc-card-64gb-47042/
  - https://www.verbatim-europe.com/en/warranty/
  - https://www.reichelt.com/de/en/shop/product/microsdxc_memory_card_64gb_pro_elite-426301
  - https://www.pny.com/pro-elite-microsd
  - https://pibenchmarks.com/brand/PNY_SD_Pro_Elite_%28SD64G%29/
  - https://www.reichelt.com/de/en/shop/product/usb_3_0_cable_a_plug_to_a_plug_1_0_m-249385
  - https://www.reichelt.com/de/en/shop/product/usb_3_0_cable_a_plug_1_m-382785
  - https://www.reichelt.com/de/en/shop/product/card_reader_external_usb_3_0_sd_microsd-221091
  - https://cdn-reichelt.de/documents/datenblatt/E200/TRANSCEND_TS-RDF5R_DB-EN.pdf
  - https://www.reichelt.com/de/en/shop/product/card_reader_external_usb_3_2_gen1_microsd_sd-423355
  - https://www.berrybase.de/en/2in1-microsd-cardreader-mit-usb-a-und-usb-c-stecker-usb-2.0-schwarz
  - https://www.berrybase.de/en/detail/019234a38bc47171813a89a25b5960ab
  - https://shop.allnetchina.cn/products/usb-3-0-male-type-a-to-a-1-5m-for-rock-pi-4.js
  - https://shop.allnetchina.cn/products/usb-c-sd-card-reader.js
  - https://www.tinytronics.nl/en/data-storage/sd-cards
  - https://docs.radxa.com/en/dragon/q6a/low-level-dev/edl-mode
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md (lines 76, 176, 286, 616, 896, 1118)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (notes 7, 34)

