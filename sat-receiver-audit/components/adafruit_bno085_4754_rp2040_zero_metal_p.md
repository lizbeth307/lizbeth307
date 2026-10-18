# Adafruit bno085 4754 rp2040 zero metal p: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** IMU pack: BNO085 breakout + RP2040-Zero bridge, metal enclosure, 4-pin connector pair, 1.5-2 m shielded 4-core lead, TVS. Framed UART at 115200 with CRC to Pico UART1, never USB.
- **Current pick:** Adafruit BNO085 4754 + Waveshare RP2040-Zero 20187 + metal puck, GX12 4-pin pair, 1.5-2 m shielded 4-core lead, TVS. Only the two boards are named parts. The puck, connector, lead and TVS are an unpriced estimate.
- **Current price usd:** 64.49-89.49 (29.50 Adafruit US + 4.99 + 30-55 estimate; US prices without tax)
- **Decision:** replace_conditionally
- **Chosen:** Keep the same two boards and buy them from an EU seller. Replace the estimated hardware with named, rated parts.
  (1) Adafruit 4754 BNO085 from BerryBase DE (ADA4754): EUR 27.45 incl. VAT, 35 in stock, 1-3 days. BerryBase is on Adafruit's own distributor list.
  (2) Waveshare RP2040-Zero 20187 from BerryBase (WS-20187): EUR 4.90 incl. VAT, 94 in stock, same parcel.
  (3) Enclosure: Hammond 1550Z101 die-cast aluminium, natural finish. 50.2x45.2x30.4 mm outside, 44.3x39.3x25.4 mm inside. Silicone gasket, UL NEMA 4/4X, IP66 (TME). DigiKey DE EUR 8.80.
  (4) Connector: Olimex CONNECTOR-GX16-4 set instead of the GX12. Clamp opening about 5.0 mm, M16 panel thread, 20 A. Olimex EUR 1.55 (in stock) or DigiKey DE EUR 1.74. Fitted with a tethered cap.
  (5) Lead: HELU SUPERTRONIC-C-PURO 4x0.14 (49655), 2 m. PUR sheath rated for outdoor use and UV. Flexing range -30 to +70 C. Tinned-copper braid with about 85% coverage. OD 4.5 mm (TME).
  (6) Gland at the pack end: LAPP SKINTOP MS-SC-M12 (53112610) EMC gland. Nickel-plated brass, IP68, cable range 3.5-7 mm, -30 to +100 C (TME).
  (7) TVS: 2x TI TPD4E1U06DBVR, one at each end, on TX, RX and 5 V. SOT-23-6, VRWM 5.5 V, 0.8 pF, IEC 61000-4-2 +/-15 kV contact. DigiKey DE EUR 0.83 each, 19,526 in stock.
  (8) Unpriced extras: 2 brass M4x20 lid screws (these replace Hammond's stainless screws), conductive foil tape over the lid seam, adhesive heat-shrink.
- **Chosen price usd:** 51.73 ex VAT, or 61.56 incl. 19% VAT, for the priced items at 1 EUR = 1.1241 USD. Breakdown ex VAT: BNO085 25.93 (30.86 incl.); RP2040-Zero 4.63 (5.51 incl.); 1550Z101 9.89; GX16-4 1.96; HELU 49655 2 m 3.56 (TME, $1.78/m at qty 1; the unit is unverified); SKINTOP M12 3.89 (TME, qty 1); TPD4E1U06DBVR x2 1.87. Add about 2-4 for the unpriced extras. Shipping is not included.
- **Saving usd:** About 9-36 ex VAT against 64.49-89.49. Of that, 3.93 is firm (BNO085 29.50 to 25.93; RP2040-Zero 4.99 to 4.63). The rest comes from replacing the 30-55 hardware estimate with about 23-25 of priced parts. The saving only holds if the DigiKey and TME items go into the stack's existing DigiKey and TME orders. Separate shipping, or a US order with the EU flat duty plus VAT, would cancel most of it.
- **Equivalence proof:** BNO085 and RP2040-Zero: same SKUs, so every spec is the same.
  - BerryBase lists ADA4754 itself, and Adafruit's 4754 page names BerryBase as an EU distributor, so the board is genuine Adafruit.
  - Adafruit 4754 has the external 32.768 kHz crystal (Adafruit product page), so the CEVA datasheet accuracy figures apply: RV 2.0/3.5 deg, Game RV 1.5/2.5 deg with 0.5 deg/min drift, gravity 1.5 deg. Board 25.6x22.7x4.6 mm.
  - The SPI0 wiring, Adafruit_BNO08x 1.2.7, arduino-pico 6.3.0 at an explicit 125 MHz, and the ME6217 LDO on the RP2040-Zero are all unchanged.
  
  No cheaper board is not-worse:
  - SparkFun BNO086 is dearer.
  - The DIY bare chip, SlimeVR, clone, host-fusion and used options each lose a spec or have unproven quality (see the rejected list).
  
  Pack hardware, spec by spec against the stack:
  - Enclosure: aluminium (non-magnetic), IP66 and NEMA 4X against the IPX4/IP54 target. The boards fit side by side: 22.7+18 = 40.7 mm along the 44.3 mm length and 25.6 mm along the 39.3 mm width, leaving about 13 mm for the gland (my model). The 2 M4 lid screws are a common brass size; the 1550WA's four M3.5 screws are not.
  - Lead: braid screen (not foil), 4 cores, flexes to -30 C, outdoor and UV rated. 0.14 mm2 Cu is about 0.13 ohm/m, so 2 m out and back at 50 mA drops about 26 mV, which does not matter for 5 V or for 115200 baud.
  - Pack end: the IP68 EMC gland gives the 360 deg braid bond the stack requires.
  - Connector: GX16 is the same family and price as the GX12. Metal shell, threaded lock, 20 A against the 0.5 A needed, and its about 5.0 mm clamp takes the 4.5 mm lead.
  - TVS: meets VRWM of at least 5 V, a few pF or less (0.8 pF), and at least 8 kV contact (15 kV). Hand-solderable.
  
  Faults found in the candidates:
  - The GX12 cable entry is 4 mm (Olimex/DigiKey drawing), so the current GX12 cannot clamp any braided 4-core lead that meets the spec. Both 5 mm LAPP cables and the 5.3 mm HELU 4x0.25 are too thick.
  - LAPP LiYCY and LAPP UNITRONIC PUR CP are both rated for occasional flexing only from -5 C (LAPP datasheets). LiYCY is also for 'dry or damp rooms' only. The searches' LiYCY pick therefore fails the winter-flex spec.
  - Neither Hammond gasket is conductive, so RF-tightness depends on the foil-taped seam and the A/B test below. Without the tape it is not proven.
  
  Rules: every part is passive or a connector. No transmitter, loop or H-field probe is added, the pack stays off USB, and heading stays live-only. The Q6A and Ubuntu 24.04 arm64 see nothing new, because the frames still arrive through the Pico on UART7.
- **Rejected:**
  1.
    - **Name:** SparkFun VR IMU Breakout BNO086 (SEN-22857)
    - **Why:** Dearer, not a budget part: $34.95 against $29.50. In the EU, BerryBase lists it at EUR 41.90 and not available, against EUR 27.45 for the 4754. STACK's 'Budget: SparkFun BNO086 $34.95' is wrong; relabel it 'second source'. The $34.95 price comes from the search results and re-audit D; I did not re-fetch it because the search budget ran out.
  2.
    - **Name:** Adafruit 4754 at DigiKey DE
    - **Why:** Same part, 6,879 in stock, but EUR 25.90 ex VAT (30.82 incl.) is EUR 2.83 more than BerryBase. Fallback seller only.
  3.
    - **Name:** Adafruit 4754 direct from Adafruit US ($29.50)
    - **Why:** An EU buyer pays the post-1-July-2026 flat customs duty (amount unverified), import VAT and express shipping on top, so the landed cost is higher than BerryBase.
  4.
    - **Name:** Adafruit 4754 at Kiwi, BOTLAND and Opencircuit
    - **Why:** Kiwi and BOTLAND are out of stock or dearer. Opencircuit is EUR 42.50 incl. VAT.
  5.
    - **Name:** DIY board with a bare CEVA BNO085 (DigiKey $12.29) and Adafruit's CC BY-SA PCB
    - **Why:** Build quality and reliability are unproven: LGA-28 reflow, crystal and the layout around the magnetometer. DigiKey stock was 0 (restock due 26 Oct 2026). It needs PCBA or a stencil, saves only about $10-15, and LCSC is not a franchised source. Not proven not-worse.
  6.
    - **Name:** SlimeVR IMU Module BNO085 (EUR 12)
    - **Why:** I2C only, with no SPI, which breaks the stack's SPI0 design. Crystal unverified, sold out, and the page returned 429, so nothing was verified live.
  7.
    - **Name:** Unbranded BNO085/BNO080 boards (AliExpress, Fruugo, Amazon) and 7Semi BNO086 (India)
    - **Why:** The chip variant and genuineness cannot be checked (SlimeVR calls these listings misleading). They break the stack rule of BNO08x only from Adafruit or SparkFun, and the India listing adds import costs.
  8.
    - **Name:** LSM6DSV or ICM-45686 + QMC6309 with host fusion; Adafruit 4517 LSM6DSOX+LIS3MDL; SparkFun LSM6DSV16X; BNO055, ICM-20948, MPU9250
    - **Why:** No published Rotation Vector, gravity or magnetometer-heading accuracy, and no on-chip magnetometer calibration (the LSM6DSV16X has no magnetometer at all). They need new fusion firmware. BNO055, ICM-20948 and MPU9250 drift worse (SlimeVR), and the BNO055 is end-of-life. All worse.
  9.
    - **Name:** Used Adafruit 4754 (eBay)
    - **Why:** No verified used listing. The one listing found is new at $49.50 + $66.41 shipping.
  10.
    - **Name:** Generic RP2040-Zero clones
    - **Why:** Regulator, flash and crystal are unknown, so the LDO-only and no-switcher spurs rule cannot be shown. They break the branded-board rule, and the saving is at most $1-2.
  11.
    - **Name:** Dropping the RP2040-Zero: BNO085 UART-RVC, or UART-SHTP at 3 Mbaud straight to the Pico
    - **Why:** RVC loses magnetometer calibration, Gravity, RV and the magnetic-field report. UART-SHTP runs at a fixed 3 Mbaud over a 2 m unbalanced lead with no CRC framing, and puts MHz edges along the boom. Both are worse.
  12.
    - **Name:** LAPP UNITRONIC LiYCY 4x0.25 (0034404)
    - **Why:** LAPP datasheet: PVC sheath, occasional flexing only from -5 C (fixed installation -40 C), 'dry or damp rooms'. It fails winter flex and outdoor use. Its 5.0 mm OD also does not fit the 4 mm GX12 entry.
  13.
    - **Name:** LAPP UNITRONIC PUR CP 4x0.25 (0032802)
    - **Why:** PUR and UV-resistant, but the LAPP datasheet still limits occasional flexing to -5 C. Fails winter flex.
  14.
    - **Name:** HELU SUPERTRONIC-C-PURO 4x0.25 (49666, 5.3 mm)
    - **Why:** Specs are good (flex to -30 C), but at 5.3 mm OD it does not fit the 4 mm GX12 entry and is marginal in the 5.0 mm GX16 clamp. The 4x0.14 version (4.5 mm) was chosen; it is also cheaper.
  15.
    - **Name:** Olimex CONNECTOR-GX12-4 (current connector family)
    - **Why:** Cheap ($1.96 at DigiKey DE, 2,388 in stock; the search's 'out of stock' applied only to the Olimex shop). But the Olimex drawing shows a 4 mm cable entry, so no compliant braided 4-core cold-flex lead can be clamped. Stripping the jacket at the clamp would weaken the seal and strain relief. Same price as the GX16, so the GX16 replaces it. The '4-6 mm' figure from retailers contradicts the drawing.
  16.
    - **Name:** WEIPU SF12 4-pin (IP67)
    - **Why:** Not cheaper: the plug alone is $8.64-12.91 and the panel half is unpriced. Shell material unverified (the datasheet PDF has no text layer). Kept as an upgrade path only.
  17.
    - **Name:** WEIPU SP13 4-pin
    - **Why:** The shell is probably plastic (unverified), so there is no 360 deg braid bond. Worse shielding.
  18.
    - **Name:** Amphenol LTW M12A-04PFFS/PMMS-SF8001 pair (DigiKey DE EUR 5.43 + 5.51)
    - **Why:** An IP-rated upgrade, but about 6x the GX16 price, and the shell and shield path are unverified. Not the cheapest not-worse option.
  19.
    - **Name:** Hammond 1550WA (89x35x30.1 mm, EVA gasket, IP66)
    - **Why:** Not worse in itself, and the same EUR 8.80 at DigiKey DE ($10.02 at DigiKey US, 4 in stock, 4-week lead). It uses four M3.5 lid screws, a size that is hard to find in brass. Fallback if the 1550Z101 fit check fails; it also gives more distance from the gland to the magnetometer.
  20.
    - **Name:** Nylon gland with an internal braid pigtail
    - **Why:** Loses the 360 deg braid bond the stack requires. Worse.
  21.
    - **Name:** TI TPD4E05U06 (USON-10) and the GOODWORK 'TPD4E05U06DQAR' marketplace part
    - **Why:** The TI part meets the spec but is hard to hand-solder on a pack without a PCB, and its contact rating is +/-12 kV against +/-15 kV for the TPD4E1U06. The GOODWORK part has a lower VWM (5 V), a higher clamping voltage and no IEC test data.
- **Confidence:** medium
- **Conditions or tests:** Gates before the pack hardware swap is final. The BNO085 and RP2040-Zero seller change needs only the price and stock re-check at order.
  1. Fit check on Hammond's 1550Z101 STEP model. The two boards must sit side by side (40.7x25.6 mm footprint), and the M12 gland's 16 mm locknut must clear the floor and lid on the wall farthest from the BNO085. If not, use the 1550WA (same EUR 8.80).
  2. GX16 lead termination. The clamp must grip the 4.5 mm HELU jacket with the braid folded back onto the shell. Measure shell-to-pack-box continuity through the braid at or below 0.1 ohm.
  3. RF A/B with the pack on and off, lid seam bridged with conductive foil tape (both gaskets are non-conductive). Pass: GNSS C/N0 change of 1 dB-Hz or less; L-band floor at 1692/1704 MHz; A/B at 145.9 and 437 MHz (existing STACK section 9 and re-audit tests). If it fails, use a conductive gasket or more bonding.
  4. IPX4 spray test, 10 min, caps fitted: GX16 receptacle (tethered cap), gland and lid. No water inside.
  5. Cold flex. 50 bends of the lead at -20 C at radius 34 mm or more (7.5x OD), then the 1e6-frame CRC test with zero errors.
  6. Magnetics. Brass M4 lid screws, no Hammond copper-plated steel ground screw. Magnet-check the gland and screws. Reach calibration status 3 with everything fitted, and compare magnetometer heading against a sun sighting.
  7. Existing pack tests. 100 cold boots with SPI init passing every time; clk_sys reported as 125 MHz; Game RV static drift at or below 0.5 deg/min over 20 min; quaternion-to-az/el unit tests.
  8. Goods-in. Check the board is a genuine Adafruit 4754 PCB and read the SH-2 product ID.
  9. Order checks. Confirm the TME qty-1 prices and per-metre unit (only structured-data ranges were seen, and stock showed both 0 and in stock), DigiKey DE stock for the 1550Z101 and GX16-4, and BerryBase shipping (not verified).
  My WebSearch budget ran out after one call, so all checks after that used direct WebFetch of primary pages.
- **Stack changes:** 1. BOM 2.8, 'IMU pack' row:
  - Split into named lines: BerryBase ADA4754 + WS-20187; Hammond 1550Z101; Olimex GX16-4 + cap; HELU 49655 2 m; LAPP SKINTOP MS-SC-M12; 2x TPD4E1U06DBVR; 2x brass M4x20; foil tape.
  - Price: $51.73 ex VAT ($61.56 incl.) plus about $2-4.
  - Change 'Budget: SparkFun BNO086 $34.95' to 'second source (dearer)'.
  2. Connector GX12 to GX16, everywhere it appears: D12, D15 rear wall, section 9 panels, the LAB-bus text at STACK line 672, and the case drawing.
  - Panel hole 16 mm instead of 12 mm; hex nut 18.8 mm; mated length about 46 mm.
  - Tethered cap. IPX4 spray test unchanged.
  - The case top-band reprint already planned for the Lime build covers the hole change.
  - Pinout unchanged: 5 V, TX, RX, GND.
  3. Lead: HELU SUPERTRONIC-C-PURO 4x0.14 (OD 4.5 mm, PUR, flexes to -30 C) instead of a generic shielded 4-core. Fixes the cold-flex gap and the GX12 cable-entry conflict.
  4. Pack enclosure:
  - Hammond 1550Z101 with brass M4 lid screws; Hammond's stainless lid screws and copper-plated ground screw are not used.
  - Lid seam bridged with conductive foil tape.
  - SKINTOP MS-SC-M12 in a 12 mm hole on the wall farthest from the BNO085, braid bonded 360 deg.
  - Mount with nylon or brass hardware, at least 30 cm from active elements and the GNSS magnet, and 15-20 cm from steel (unchanged).
  - Enclosure mass about 70 g on the boom.
  5. TVS: one TPD4E1U06DBVR at the GX16 receptacle on the Pico side and one in the pack, on TX, RX and 5 V.
  - The pack's 5 V Schottky (re-audit back-feed fix) stays.
  - The 31/43 ferrite near the pack stays, from the existing DigiKey ferrite line.
  6. No change to rails (LAB5 5 V, tens of mA), firmware (arduino-pico 6.3.0 at 125 MHz, Adafruit_BNO08x 1.2.7, SPI 1 MHz MODE3), Q6A drivers or Ubuntu 24.04 arm64 packages (the Q6A reads Pico frames on UART7). Receive-only and the other rules are unaffected.
  7. Shopping order: BerryBase parcel (BNO085 + RP2040-Zero); DigiKey DE (1550Z101, GX16-4, 2x TPD4E1U06DBVR) added to the existing DigiKey order; TME (HELU 49655 2 m, SKINTOP M12) added to a TME order. Ordered on their own, shipping would eat the saving.
- **Sources:**
  - https://www.berrybase.de/en/search?search=BNO085
  - https://www.berrybase.de/en/search?search=RP2040-Zero
  - https://www.adafruit.com/product/4754
  - https://www.digikey.de/en/products/detail/adafruit-industries-llc/4754/13426653
  - https://www.hammfg.com/files/parts/pdf/1550Z101.pdf
  - https://www.hammfg.com/files/parts/pdf/1550WA.pdf
  - https://www.tme.eu/en/details/hm-1550z101/multipurpose-enclosures/hammond/1550z101/
  - https://www.digikey.de/en/products/result?keywords=1550Z101
  - https://www.digikey.de/en/products/result?keywords=1550WA
  - https://www.digikey.com/en/products/detail/hammond-manufacturing/1550WA/2211556
  - https://olimex.com/Products/Components/Connectors/CONNECTOR-GX12-4
  - https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5560/Olimex%20-%20CONNECTOR-GX12-4.pdf
  - https://www.digikey.de/en/products/result?keywords=CONNECTOR-GX12-4
  - https://www.olimex.com/Products/Components/Connectors/CONNECTOR-GX16-4/
  - https://www.olimex.com/Products/Components/Connectors/CONNECTOR-GX16-4/resources/gx-connector-dimension.jpg
  - https://www.tme.eu/en/details/liycy-4x0.25/multicore-cables-shielded/lapp/0034404/
  - https://www.tme.eu/Document/81757d262281e1d1d26979f5e2f3610b/0034410.pdf
  - https://www.tme.eu/en/details/utr-cp-4x0.25/multicore-cables-shielded/lapp/0032802/
  - https://www.tme.eu/Document/59c7c8e3b0d5ec6a476ab8d93fd7c494/LAPP_PRO220ENGB.pdf
  - https://www.tme.eu/en/details/str-c-pur4x0.14/cables-for-power-chains-shielded/helu/49655/
  - https://www.tme.eu/en/details/str-c-pur4x0.25/cables-for-power-chains-shielded/helu/49666/
  - https://www.tme.eu/Document/b254c58c4bdf03558b00613acbf53bf0/STR-C-PUREN.pdf
  - https://www.tme.eu/en/details/ms-sc-m12/glands/lapp/53112610/
  - https://www.ti.com/product/TPD4E1U06
  - https://www.digikey.de/en/products/result?keywords=TPD4E1U06DBVR
  - https://www.ti.com/product/TPD4E05U06
  - https://www.tme.eu/en/details/sf1210_s4/weipu-connectors/weipu/sf1210-s4i/
  - https://www.reichelt.com/de/en/shop/search/liycy%204x0.25
  - https://www.sparkfun.com/sparkfun-vr-imu-breakout-bno086-qwiic.html
  - https://www.digikey.com/en/products/detail/ceva-technologies-inc/BNO085/9445940
  - https://docs.slimevr.dev/diy/imu-comparison.html
  - https://www.ceva-ip.com/wp-content/uploads/BNO080_085-Datasheet.pdf

