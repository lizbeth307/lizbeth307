# Mechanical thermal: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_e6b8e5e2-124`_

- **Component:** Mechanical, thermal and enclosure: M.2 riser, MHF4-to-SMA pigtails and SMA panel, Q6A and LimeSDR cooling, case, RF shielding, ergonomics, size and weight
- **Current pick assessment:** The current plan has the right parts but rests on four assumptions that need correcting.
  
  (1) A rigid 2230-to-2280 extension will not work. The Q6A's M.2 M-key socket (J13, PCIe Gen3 x2, M2x4 screw) is on the TOP side, top-left, just under the 40-pin header. The card points toward the bottom edge, where the USB-C PD input (J8), the 12 V/GND/PWR header (J21) and HDMI (J15) sit (Radxa placement map and 2D drawing v1.21). From the drawing I estimate a 2280 card sticks out about 35-40 mm past the 56 mm edge, right over J8/J21, which blocks the planned USB-C PD power input. The rigid "2230/2242-to-2280 adapters" on sale solve the opposite problem (a short SSD in a long slot). You need a flex M.2-to-M.2 riser.
  
  (2) The LimeSDR Micro M.2 has its heat sources on the side that faces the host board. The LMS7002M (IC1), LA9310 (IC6) and switchers IC26/IC30 are on the bottom (even-pin) side. The MHF4 RF ports (X1 TX_A, X2 RX_A, X4 RX_B) are at the far end of the top side, the MHF4 clock/PPS ports (J3-J6) are mid-edge, and top-side parts reach about 4 mm. Lime asks for cooling rated for at least 10 W; Lime staff quote about 4 W typical.
  
  (3) Radxa has no official Q6A heatsink or fan, and the board has no fan header. Measured load is about 9.3-10.1 W (2.9 W idle). A bare board shut down at about 105 C. Passive cooling throttled above 90 C. A small heatsink plus a 25 mm fan kept it under about 80 C on Armbian.
  
  (4) The PCB is 85x56 mm per Radxa's drawing, not 85x65. Mounting holes are 4x 3.5 mm at 58x49 mm (Raspberry Pi pattern), so M2.5 hardware fits.
  
  Also check the SDR price: Crowd Supply now lists the LimeSDR Micro M.2 2280 Basic at $249 ($299 with GNSS), and new orders ship Dec 15, 2026, not $199 / Sept 30.
  
  Pigtails: MHF4 to SMA is the right approach. Use 1.13 mm cable where you can and keep it about 10 cm. MHF4 is rated for only 30 mating cycles, so terminate every port on fixed bulkheads.
  
  Enclosure: plain PETG will soften in sun. Without an internal metal plate, a printed case gives no RF shielding.
- **Alternatives:**
  1.
    - **Name:** ADT-Link R44SF M.2(M) to M.2(M) flex riser, 5 or 10 cm
    - **Key specs:** PCIe 3.0 x4, ADT drawing note: 100% PCIe 3.0x4 32 Gb/s tested. Five shielded flat cables (conductive-polymer EMI shield), 1.4 mm thick, bendable but must not be pulled. Male end about 21.2 mm to the cable start, 3.8 mm stack (3 mm FR4 clamp pad). Female board is 80 mm long with M2 screws and nuts. Lengths 3-80 cm. STEP model available.
    - **Price:** $19 (5 or 10 cm), $21 (3 cm) list price on adt.link, plus shipping. AliExpress resellers ask about $40-50 for ADT Gen4/Gen5 versions.
    - **Pros:** Proven Gen3 margin at very short length, so the LimeSDR's Gen3 x1 is easy. Lets you put the SDR in its own shielded compartment with the MHF4 end next to the SMA panel. Cable is shielded. CAD models available.
    - **Cons:** The LimeSDR's hot underside faces the riser's female board, so cooling needs a gap pad plus a top-side heatsink and airflow. The male end may need a printed clamp for retention (I could not verify a 2230 screw notch). Shipping to Ukraine not verified.
    - **Sources:**
      - https://www.adt.link/product/R44SF.html
      - http://www.adt.link/Uploads/download/ADT_R44SS%20dimension%2020200326.pdf
      - https://www.adt.link/product/R44F.html
    - **Availability:** Listed on adt.link with an online shop (R44-Shop). ADT also sells through Newegg/AliExpress resellers. Stock in Oct 2026 not verified.
    - **Q6a compatibility:** Male end fits within the 2230 footprint of J13. 3.8 mm stack height above the socket. Check heatsink clearance with the Radxa v1.21 STEP model.
  2.
    - **Name:** ADT-Link M44SF M.2 to M.2 extender (PCIe 4.0-rated)
    - **Key specs:** PCIe 4.0 x4 (64 Gb/s), M-key both ends, 1.4 mm shielded flat cable, 10-100 cm (custom 5-100 cm), described as a '180-degree' vertical layout.
    - **Price:** $19 (10 cm), $20 (15 cm) on adt.link
    - **Pros:** Gen4-rated cable gives more headroom at Gen3. Same price as the R44SF.
    - **Cons:** No 3 or 5 cm stock size (custom only). Shape and orientation differ from the R44SF; check the drawing. Same underside-cooling issue.
    - **Sources:**
      - https://www.adt.link/product/M44V4.html
    - **Availability:** adt.link. Not verified on Ukrainian marketplaces.
    - **Q6a compatibility:** Electrically fine (link will train at Gen3 or below). Mechanical fit needs a check with the STEP model.
  3.
    - **Name:** Generic AliExpress M.2 M-key extension FPC (KYNBREL and similar, '2230-2280, PCIe 4.0')
    - **Key specs:** Claims PCIe 4.0 x4, supports 2230/2242/2260/2280, 10-80 cm. No signal-integrity data published.
    - **Price:** About $1.80 (new-buyer promo, $7.80 regular) to $9.21 (search snapshot, not a dated quote)
    - **Pros:** Very cheap. Fine for a first fit-check mock-up.
    - **Cons:** Unknown shielding and impedance control. Level1Techs and Amazon user reports of cheap extenders show mixed results. Must be checked with lspci LnkSta and AER logs.
    - **Sources:**
      - https://www.aliexpress.us/item/3256809154219544.html
      - https://www.aliexpress.us/item/3256807741690132.html
      - https://forum.level1techs.com/t/nvme-extension-riser-cables-do-they-work/179874
    - **Availability:** AliExpress, ships to Ukraine (typical).
    - **Q6a compatibility:** Probably works at Gen3 x1 for short lengths; not verified.
  4.
    - **Name:** No riser: LimeSDR plugged straight into J13 with a 3D-printed tail support
    - **Key specs:** Card sticks out about 35-40 mm past the board edge (my estimate from Radxa's drawing). The LMS7002M (about 49-61 mm from the card edge) would sit beyond the PCB with its underside exposed.
    - **Price:** $0
    - **Pros:** No extra PCIe connector pair. The exposed underside of the LMS7002M could be padded straight onto a plate.
    - **Cons:** Covers the USB-C PD input J8 and the 12 V header J21, and may hit the HDMI connector. LA9310 underside sits over the Q6A edge components. Unknown socket stand-off versus the LimeSDR's double-sided parts and the Wi-Fi module can. SDR sits right next to the SoC and DSI noise.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_components_placement_map_v1.21.pdf
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_2d_dimensions_v1.21.pdf
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/overview.html
    - **Availability:** n/a
    - **Q6a compatibility:** Only plausible if Q6A power comes in another way and calipers confirm clearance. Not recommended.
  5.
    - **Name:** MHF4 to SMA(f) bulkhead pigtails
    - **Key specs:** Lime accessory: I-PEX MHF-4L plug to SMA female bulkhead, 100 mm. Prom.ua: SMA female to IPEX MHF4 on RF1.13 or RF0.81, 5-20 cm. Loss: 0.81 mm cable about 2.65 dB/m at 1 GHz and 5.1 dB/m at 2.4 GHz; 1.13 mm about 2.8 dB/m at 2 GHz and 3.1 dB/m at 2.4 GHz. A 10 cm 1.13 mm pigtail costs about 0.3 dB at 2.2 GHz plus connector loss. MHF4 receptacles are rated for 30 mating cycles. MHF4L plugs mate with MHF4 receptacles (rated to 9 GHz on an MHF4 receptacle).
    - **Price:** Lime: $6 each (+$18 worldwide shipping unless bundled with the SDR order). Prom.ua: 63 UAH (10 cm RF0.81 or RF1.13), 95 UAH with gasket (RF1.13). rf-connectors.pl: 14.42 zl (0.81 mm, 10 cm).
    - **Pros:** Ukrainian stock is very cheap and fast. The Lime cable is a known match for the board. Use 1.13 mm to roughly halve the loss.
    - **Cons:** Bulkhead nut and gasket are not stated on most prom.ua listings. Many listings are RP-SMA; you need plain SMA. 0.81 mm cable is fragile (5 mm minimum bend radius).
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
      - https://prom.ua/Ipex-mhf4-gnezdo-sma.html
      - https://rf-connectors.pl/en/mhf4-on-sma/604-pigtail-mhf4-female-plug-sma-socket-rf081-10cm-5904734561361.html
      - https://www.taoglas.com/specifications/300115B000098A_Taoglas.pdf
      - https://portal.powertec.com.au/equipment/rf-communications/rf-cables/rf-cable-groups/081-mm-mini-coax
      - https://www.i-pex.com/product/mhf-4l-lk
      - https://www.digikey.es/en/products/detail/i-pex/20449-001E-03/22108824
    - **Availability:** Prom.ua in stock (many sellers). Crowd Supply accessory listed in stock.
    - **Q6a compatibility:** Not board-dependent. Fits the LimeSDR X2/X4 MHF4 ports.
  6.
    - **Name:** Q6A cooler: third-party copper heatsink or case with 3010 fan (NBcooler and others)
    - **Key specs:** Stepped copper block (the higher step takes paste on the SoC, the lower step takes a pad on the LPDDR5). Versions from 5.7 mm to 13 mm thick. 3010 5 V fan powered from GPIO 5 V/GND. A forum user reports 55 C under stress.
    - **Price:** About $17-30 in AliExpress listings (prices inconsistent). Amazon B0GZ9NW316 price not shown.
    - **Pros:** Made for the Q6A layout. Easiest proven drop-in.
    - **Cons:** A forum post says one AliExpress listing is no longer available. Small 30 mm fan. Clearance next to the riser's male end and the M.2 area is unverified. Fan runs at full speed with no PWM.
    - **Sources:**
      - https://www.aliexpress.com/item/1005010333340740.html
      - https://www.aliexpress.com/item/1005010333326718.html
      - https://us.amazon.com/Dragon-Copper-Cooling-Radiator-Heatsink/dp/B0GZ9NW316
      - https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
    - **Availability:** Intermittent on AliExpress; also on Amazon.
    - **Q6a compatibility:** Designed for the Q6A. M.2 or riser clearance not verified.
  7.
    - **Name:** Radxa Armor Case 7056A (official, passive)
    - **Key specs:** Mg-Si aluminium top and bottom covers with 3D fins, 2 thermal pads, 4x M2.5x8 screws. Fanless. Supports Q6A, ROCK 5A/5C and Cubie A7A.
    - **Price:** Not on Radxa's page (sold through partners). One AliExpress result showed $4.49, likely a variant price; unverified.
    - **Pros:** Only official thermal part for the Q6A. Silent. About 40 C idle at 23 C room reported.
    - **Cons:** One user saw over 90 C and throttling until a fan was glued on. It is a closed box, so it does not suit a handheld with an M.2 riser and DSI routing. Buyers report stock problems.
    - **Sources:**
      - https://radxa.com/products/accessories/armor-case-7056a
      - https://forum.radxa.com/t/recommended-heatsink-fan-for-q6a/30413
      - https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
    - **Availability:** Partners, Amazon, Arace. AliExpress has been unreliable.
    - **Q6a compatibility:** Fits the bare board. M.2 or riser use unverified (one comment says some coolers fit only if the M.2 slot is unused).
  8.
    - **Name:** Noctua NF-A4x10 5V PWM (or 5V FLX) 40x40x10 fan
    - **Key specs:** 0-5000 rpm, 8.9 m3/h, 19.6 dB(A), 1.95 mm H2O, 0.3 W, 4-pin, 10 g
    - **Price:** About 23-26 EUR in EU shops (LDLC shows the PWM version as no longer sold; Dateks lists 26.49 EUR, undated)
    - **Pros:** Quiet. Enough airflow for a ducted 15-20 W box. Light.
    - **Cons:** PWM version is being phased out at some retailers. Q6A PWM on GPIO is unconfirmed, so plan for on/off switching through a MOSFET.
    - **Sources:**
      - https://noctua.at/en/nf-a4x10-5v-pwm/specification
      - https://ldlc.com/en/product/PB00396294.html
      - https://www.dateks.lv/en/cenas/ventilatori/286035-noctua-nf-a4x10-5v-pwm
    - **Availability:** EU shops (Galaxus, Dateks). Generic 4010 5 V fans on AliExpress cost a few dollars (unverified) but are louder.
    - **Q6a compatibility:** 5 V from the 40-pin header or your own 5 V buck.
  9.
    - **Name:** Ready enclosures: Hammond 1599HSGY / 1599KSGY (ABS handheld), Hammond 1455Q2201 (extruded aluminium)
    - **Key specs:** 1599HSGY: 220x110x44.8 mm, IP54, recessed top (BAT version has a battery compartment). 1599KSGY: 220x140x40 mm. 1455Q2201: about 220x125x51.5 mm aluminium, 1.5 mm wall, IP54, 554 g. For reference, the Hammond 1553D (147x89x25) and OKW Soft-Case XL (150x92x28) are too thin for 21700 cells plus a 20 mm board.
    - **Price:** 1599HSGY GBP 7.54, 1599HSGYBAT GBP 12.17 (RS UK, ex VAT). 1455Q2201 GBP 29.20 (Rapid). 1599K price not verified.
    - **Pros:** The ABS boxes are cheap and RF-transparent. The aluminium box is a ready shield and heat sink.
    - **Cons:** Flat boxes give no grip. A 7-inch display cutout, vents and a fan duct are hard to machine. The 1599H inner width is probably under 100 mm, so the 120 mm-wide 7-inch module will not fit (inner dimensions unverified). The aluminium box is heavy and needs external Wi-Fi and GNSS antennas.
    - **Sources:**
      - https://uk.rs-online.com/web/p/hand-held-enclosures/2072158
      - https://cn.element14.com/hammond/1599ksgy/box-abs-grey-40x140x220mm/dp/1426565
      - https://www.rapidonline.com/catalogue/product/30-4432
      - https://nz.rs-online.com/web/p/general-purpose-enclosures/8180573
      - https://rapidonline.com/catalogue/product/30-3104
      - https://electronicspecifier.com/cabinets-and-enclosures/soft-case-handheld-enclosures-range-extended-okw
    - **Availability:** EU distributors (RS, Rapid, TME). Ukrainian stock not verified.
    - **Q6a compatibility:** Only the 1599K or 1455 sizes fit a 7-inch display plus 4x21700 plus the boards; both need heavy machining.
  10.
    - **Name:** RF shielding parts: Würth WE-SHC two-piece shield can, MG Chemicals 841AR nickel spray, copper tape, copper-clad FR4
    - **Key specs:** WE-SHC 36503505: 50x50x3 mm tinplate frame plus removable lid, up to 55 dB. 841AR: nickel-acrylic coating, about 29-48 dB at 100 MHz-1 GHz and 31-57 dB at 1-10 GHz (Vetco listing; the Farnell datasheet gives different bands). Copper tape works only if bonded to ground (RTL-SDR.com tests).
    - **Price:** WE-SHC 50x50: AU$10.05 / S$9.07 (element14). 841AR 340 g: $52.95 (TestEquity; cannot ship by air). Copper tape and FR4 sheet a few dollars (unverified).
    - **Pros:** Shield cans around the LNA, bias-tee and filter boards are easy. Spray turns a printed shell into a shield. Soldered copper-clad FR4 boxes are the cheapest custom can.
    - **Cons:** Spray is hard to ship to Ukraine (aerosol). A shell made conductive can detune internal Wi-Fi and GNSS antennas.
    - **Sources:**
      - https://au.element14.com/wurth-elektronik/36503505/shielding-cabinet-tht/dp/1909668
      - https://www.testequity.com/brand/MG-Chemicals/category/Static-Control/Facility-Static-Control/ESD-Safe-Paint-Primer-And-Coatings/10001527-841AR-340G
      - https://vetco.net/products/mg-super-shield-nickel-conductive-coating-spray-12oz
      - https://www.rtl-sdr.com/shielding-the-sdrplay-rsp-copper-tape/
      - https://www.rtl-sdr.com/?p=55992
    - **Availability:** element14/TME (Würth). Copper tape and FR4 are common in Ukrainian radio shops (unverified).
    - **Q6a compatibility:** n/a
- **Recommended:**
  - **Name:** Hybrid build: ASA 3D-printed shell + 2 mm aluminium mid-plate (chassis, heat spreader and shield) + ADT-Link R44SF 5-10 cm riser + ducted 40 mm fan + shielded RF bay + 1.13 mm MHF4-to-SMA bulkheads + 1/4"-20 inserts
  - **Why:** This layout solves all four problems found in the assessment.
  
  - **Riser:** The R44SF moves the LimeSDR away from the J8/J21/HDMI collision zone and from SoC and DSI noise. Its MHF4 end sits about 10 cm from the SMA panel.
  - **Mid-plate:** One 2 mm aluminium plate carries the Q6A (M2.5 standoffs on the 58x49 Pi-pattern holes), the riser board and the batteries. It is the ground and shield wall between the display/digital side and the RF bay. It spreads heat from the UFS module (bottom side) and the LimeSDR underside, and it holds the 1/4"-20 inserts.
  - **Fan:** A 40 mm fan (NF-A4x10 5V, 0.3 W) pulls air from a meshed intake on the shaded back. Air passes the Q6A fin stack (copper shim on the SoC, pad on the LPDDR5) and then the LimeSDR top-side heatsink before exhausting at the side. This is needed because internal heat is about 17-25 W and a passive box this size can shed only about 17 W at a 30 K rise before sun load.
  - **Shell:** Light-grey or white ASA (Tg about 100-105 C, UV-stable; PETG is about 75-80 C). No carbon fibre near antennas.
  - **Pigtails:** 1.13 mm, 10 cm (about 0.3 dB at 2.2 GHz) with all LNAs at the antenna, so pigtail loss sits after the LNA gain.
  - **Price:** About $120-170 total (excluding SDR, board, display and batteries):
  - ADT R44SF: $19 + shipping
  - 2-3 MHF4-SMA pigtails: about $3-5 at prom.ua (Lime's own cables are $6 each)
  - Q6A cooling: copper heatsink+fan $17-30 (AliExpress), or 40 mm Noctua (about 23-26 EUR) + generic fin stack, copper shim and pads ($10-15, unverified)
  - LimeSDR heatsink and pads: $3-6 (unverified)
  - Aluminium sheet: $5-10 (unverified)
  - ASA filament: about 0.3-0.4 kg, $8-12 (unverified)
  - 1-2 Würth WE-SHC 50x50 cans: about $7-10 each
  - Copper tape and FR4: $5
  - SMA/F bulkheads and an RTL-SDR jumper: $8-15 (unverified)
  - 1/4"-20 inserts: CNC Kitchen 20-pc set, price not verified
  - Straps, buttons, encoder, TPU bumpers: $10-20 (unverified)
  - **Sources:**
    - https://www.adt.link/product/R44SF.html
    - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_components_placement_map_v1.21.pdf
    - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_2d_dimensions_v1.21.pdf
    - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
    - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/overview.html
    - https://github.com/geerlingguy/sbc-reviews/issues/85
    - https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5
    - https://noctua.at/en/nf-a4x10-5v-pwm/specification
    - https://qidi3d.com/blogs/print-lab/asa-vs-petg-filament-direct-sunlight
    - https://www.taoglas.com/specifications/300115B000098A_Taoglas.pdf
    - https://prom.ua/Ipex-mhf4-gnezdo-sma.html
    - https://3djake.com/cnc-kitchen/threaded-inserts-1-4-20
- **Budget option:**
  - **Name:** PETG print + generic AliExpress M.2 extension FPC + Pi-style 40 mm aluminium heatsink/fan on GPIO 5 V + copper-tape and soldered copper-clad FR4 shields + prom.ua RF1.13 pigtails
  - **Why:** Keeps the same architecture (SDR on a riser, separate RF bay, fan-cooled SoC) at a fraction of the cost. Users report a 25-40 mm Pi-style heatsink+fan keeps the Q6A under about 80 C. PETG is fine if the device is not left in direct sun (it softens around 75-80 C). Validate the cheap riser with lspci and AER logs first, and upgrade to the $19 ADT-Link only if errors appear.
  - **Price:** About $40-65 total:
  - Generic riser: $2-9
  - Pi-style heatsink+fan: about $3-6 (unverified)
  - Pigtails: 2x 63 UAH at prom.ua
  - PETG, copper tape and FR4: about $10-15 (unverified)
  - SMA bulkheads, inserts, strap: about $15-25 (unverified)
- **Risks:**
  - Riser signal integrity: a cheap FPC can cause PCIe AER errors or link drops under sustained 61.44 Msps streaming. Fallback: Gen2 x1 (about 400 MB/s usable, computed) still carries one channel at 61.44 Msps x 4 B = 246 MB/s, but not two RX channels at 16-bit.
  - LimeSDR thermal: the main chips face the riser board. A gap pad to FR4 conducts heat poorly, so rely on airflow plus a top-side heatsink. Watch the onboard TMP1075 sensor. Lime's 10 W design guidance and 4 W typical figure are not verified by measurement.
  - Q6A heat: about 10 W SoC load (plus GPU and NPU) in a closed box in sun. A dark display face absorbs roughly 10+ W of sunlight (rough estimate: about 1000 W/m2 on 0.026 m2, half absorbed). Expect throttling without a fan and sun hood. Bare-board shutdown is about 105 C.
  - Clearance near J13: the riser male end (3.8 mm stack) sits next to the SoC heatsink area and over the Wi-Fi module. A third-party copper case may collide with it. Design around the Radxa STEP v1.21 model and ADT STEP files before buying the cooler.
  - MHF4 connectors last only about 30 mating cycles. Never use them as user-facing connectors. Strain-relieve the pigtails.
  - Prices and stock change: LimeSDR M.2 Basic is now $249 with new orders shipping Dec 15, 2026. The Armor Case and the Q6A copper coolers have had stock gaps. ADT-Link and Würth shipping to Ukraine not verified.
  - Weight: a 7-inch build comes out around 1.0-1.2 kg (estimate), not palm-sized. Hand fatigue during passes; a strap and a mount are mandatory.
  - Magnetometer errors: the fan motor, battery currents, steel screws and the speaker will bias the BNO085. It must be calibrated in the final assembly (CEVA guidance).
  - Wi-Fi and USB 3 noise: the Q6A Wi-Fi 6 transmitting at 2.4 GHz, and USB 3 noise (Intel measured a noise floor nearly 20 dB higher at 2.4-2.5 GHz in one test), will desensitise S-band (2.2 GHz) and possibly L-band reception.
  - LimeSDR RX matching per Lime docs: RX low is 0.3-2.2 GHz and wide is 0.7-2.6 GHz. 137/145 MHz is outside the matched range, so keep the RTL-SDR on its own bulkhead for VHF.
- **Integration notes:**
  - Layout (7-inch display): the display (Raspberry Pi Touch Display 2 class: 189.3x120.2x6.6 mm, about 245-250 g) sits in the front bezel. Behind it are a foam gap and the 2 mm aluminium mid-plate. The Q6A mounts top-side facing the back on 5-6 mm M2.5 standoffs, so the UFS module (J1, bottom side) gets a thermal pad to the plate. The 4x21700 cells (4x1 row, about 86x70x22 mm) go beside the Q6A. The riser and LimeSDR run along the top edge with the MHF4 end toward the SMA panel. RTL-SDR and LNA/bias boards go in a shield-can bay at the top corner.
  - Size and weight estimate: about 200-205 x 130-135 x 42-48 mm and 1.0-1.2 kg. Breakdown: 4x21700 = 280-290 g (P45B 70 g, 50S 72 g); display about 250 g; ASA shell about 180-250 g; Q6A about 40-50 g (not published; estimate); LimeSDR <20 g; riser about 15 g; RTL-SDR about 30 g; heatsinks, fan and plate 80-110 g; BMS, bucks, LNAs, GNSS, IMU, cables and bulkheads 120-160 g. A 5.5-6 inch two-layer build is about 160x100x55-60 mm and 0.85-0.95 kg (estimate). An aluminium Hammond 1455-type box adds roughly 0.3-0.4 kg.
  - Thermal budget (computed from sources): Q6A 2.9 W idle, 9.3-10.1 W load; LimeSDR about 4 W typical (design for 10 W); RTL-SDR about 1-1.5 W (unverified); display several W (panel-dependent); DC-DC losses about 1.5-2 W. Total about 17-25 W inside.
  - Fan control: the Q6A has no fan header and GPIO PWM is not documented. Feed the fan from 5 V through a logic MOSFET (AO3400/2N7002) switched by one GPIO with 60/70 C hysteresis (a forum user did this), or use a small thermostatic PWM module.
  - PCIe riser bring-up checks:
  - `lspci -vv` should show LnkSta 8GT/s x1.
  - `dmesg | grep -i aer` should stay clean during a 30-60 min stream at 61.44 Msps with LimeSuiteNG.
  - Route the riser cable away from the RF bay and the DSI flex. Fold it once with no tension (ADT: do not pull the cable).
  - SMA panel on the top edge (antenna side), 16-18 mm pitch, O-ring bulkheads bonded to a metal sub-plate tied to the mid-plate, from left to right:
  - LNB: F-female with internal bias-tee and a guarded 13 V toggle plus LED
  - RX-A: LimeSDR X2 (UHF/LNB IF)
  - RX-B: LimeSDR X4 (L/S)
  - RTL: RTL-SDR V4 through a short RG316 SMA(m) to SMA(f) bulkhead jumper
  - Optional GNSS external antenna
  Use plain SMA, not RP-SMA. Do not bring the LimeSDR TX_A (X1) to the panel (receive-only).
  - Keep high-speed and noisy ports (USB-C charge, HDMI, Ethernet, USB 3.1) on the bottom or opposite edge. Run the RTL-SDR on a USB 2.0 port and leave USB 3.1 empty during L/S-band work. Disable Wi-Fi/BT with rfkill while recording S-band. Wrap the DSI flex in grounded copper tape or route it over the mid-plate, away from the RF bay.
  - Inside the shell: ASA with 2.4-3 mm walls, a TPU corner bumper and grip overmould, and a slide-on printed sun hood for the display. Intake vent on the shaded back with a stainless mesh and a drip lip. No vents on the top face.
  - Ergonomics:
  - Brass 1/4"-20 heat-set inserts (CNC Kitchen 12.7 mm) on the bottom (tripod) and back (antenna-boom clamp or Arca plate).
  - Adjustable hand strap across the back, plus two side lugs for a neck strap.
  - Panel controls usable with gloves: 12-16 mm momentary power button wired to J21 PWR+GND, an EC11 encoder, and 2-3 GPIO buttons.
  - Pointing aid: mount the BNO085 rigidly in line with the antenna-boom mount, at least several cm from the fan, battery leads and speaker. Use brass inserts and A2/A4 or nylon screws nearby. Calibrate in the finished device (CEVA procedure).
  - Double-check before cutting: model everything in CAD from the Radxa Q6A STEP v1.21, the ADT R44 STEP and the Lime board drawings. The 2280 overhang and connector heights here are my estimates from 2D drawings.
- **Double duty opportunities:**
  - The aluminium mid-plate does four jobs: chassis, heat spreader (UFS module, LimeSDR underside, SoC fin base), RF ground and shield wall between display/digital and the RF bay, and anchor for the 1/4"-20 inserts. It replaces a separate SDR heatsink, a separate shield box and a separate tripod plate.
  - Power the Q6A through the 12 V/GND/PWR header J21 from one 4S-to-12 V buck instead of a USB-C PD source board. Radxa recommends at least 24 W (12 V/2 A) for full PCIe and USB load. The same rail can feed the QO-100 LNB: 12 V is inside the 11.5-14 V 'vertical' window, but cable drop can push it below 11.5 V, so measure it or keep a 13 V boost. Do not connect USB-C power at the same time (reverse-feed warning).
  - J21's PWR pin doubles as the input for a panel-mounted power button (short PWR to GND), so you need no separate power-switch board for the Q6A.
  - The 4x21700 pack can be a detachable grip/handle (2x2 cells, about 46x46x145 mm) with the tripod thread in its base. Battery, handle and mount become one part.
  - The 1/4"-20 insert plus a boom clamp mounts the receiver on the Yagi or helix boom. That fixes the IMU to the antenna, which is what makes the pointing aid accurate.
  - A printed sun hood also works as a screen protector when slid over the display for transport.
  - A bias-tee built into the LNB bulkhead (with PTC fuse and toggle) removes the external 13 V injector box.
- **Confidence:** medium

_Агент цього етапу ще працює (run `wf_e6b8e5e2-124`)._

## Форуми та досвід спільноти (`forums`)

_Run `wf_e6b8e5e2-124`_

- **Component:** Mechanical, thermal and enclosure: M.2 2230-to-2280 riser, MHF4-to-SMA pigtails and SMA panel, cooling for the Radxa Dragon Q6A and the LimeSDR Micro M.2, case material, RF shielding, ergonomics, size and weight
- **Experiences:**
  1.
    - **Product:** Radxa Dragon Q6A + official Armor Case 7056A (passive)
    - **Source url:** https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
    - **Community:** Radxa forum
    - **What they built:** Rahul007 (May 17 2026): headless edge-AI server running Docker containers 24/7. Summer ambient 35-40 C.
    - **Problems:**
      - With only the Armor Case, CPU/GPU went above 90 C, throttled, and sustained performance became inconsistent.
    - **Fixes:**
      - Glued a small recycled 5 V fan on top of the case with a little thermal glue (no drilling, reversible).
    - **Outcome:** Throttling stopped. Temperatures stayed stable under full CPU load. Monitor tool shared: github rahulbtc/radxa-q6a-monitor.
  2.
    - **Product:** Radxa Dragon Q6A + AliExpress stepped copper cooler (SoC plus LPDDR5) with 30/40 mm fan
    - **Source url:** https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
    - **Community:** Radxa forum
    - **What they built:** Several desktop builds in 3D-printed cases, mostly the Printables 'Radxa Dragon Q6A Case V4' by el_sattchmo.
    - **Problems:**
      - The included pad was big enough for only one chip, so the heatsink did not seat well on the DDR5 (Moonlight0551, Jan 2026).
      - If the standoffs are in the wrong order, the cooler sits above the parts instead of on them (Bob_Weurman).
      - The stock fan was 'way too loud and high-pitched' (GinKage).
      - The cooler went out of stock on AliExpress, and AliExpress is not available in some countries (osbope, ayushnix).
    - **Fixes:**
      - Paste on the taller SoC step and a pad on the lower memory step (CATNVol). Add a second pad on the DDR5.
      - Shorter standoffs on the PCB, longer ones below.
      - Swapped in a Noctua NF-A4x10 5 V with a 40 mm grill and a 3-pin speed-reduction cable (GinKage).
      - Journeymangeek used two single heatsink blocks with PTM2750 phase-change pads and 25 mm Pi-style 5 V fans on the header.
    - **Outcome:** About 55 C under stress (Bob_Weurman). 'Never heats up under load' (Journeymangeek). Quiet with the Noctua (GinKage). No one reported fitting it with an M.2 card installed.
  3.
    - **Product:** Radxa Dragon Q6A, homemade passive heatsink vs. copper fin + fan; Armor Case availability
    - **Source url:** https://forum.radxa.com/t/recommended-heatsink-fan-for-q6a/30413
    - **Community:** Radxa forum
    - **What they built:** Desktop boards.
    - **Problems:**
      - Homemade passive heatsink: CPU 'repeatedly hits 90 degrees and throttles' (drake, Feb 2026). No fan header in the docs.
      - Armor Case AliExpress listing unavailable; a second seller never shipped and the order was refunded (wilsonyan).
    - **Fixes:**
      - Copper fin heatsink + fan wired to the 5 V/GND header pins (Bob_Weurman, drake).
      - RPi CM5 '3007' 5 V fan (~5000 rpm, 1 W) on self-adhesive thermal tape, full speed (hacky).
      - Bought the Armor Case through Amazon or Arace instead.
    - **Outcome:** Fan solutions 'work very well' with constant full-speed noise accepted. Armor Case gives ~40 C idle at 23 C room (Dual-O) but has no load data.
  4.
    - **Product:** Q6A fan control (no fan header, no hardware PWM on the 40-pin header)
    - **Source url:** https://forum.radxa.com/t/pwm-on-radxa-dragon-q6a/30201
    - **Community:** Radxa forum + GitHub
    - **What they built:** PWM output for fans and buzzers.
    - **Problems:**
      - Radxa's strongtz: the QCS6490 'does not expose a general-purpose hardware PWM controller on the GPIO header'. The only PMIC PWM (PM_C_GPIO_09) goes to test point TP33.
      - Users report 25 mm header fans are loud; no MOSFET results were posted (wasted01, forum t/30737).
    - **Fixes:**
      - Write a device-tree overlay that assigns a GPIO to the kernel pwm-gpio driver (strongtz).
      - Calin23/dragon-q6a-fan-control (https://github.com/Calin23/dragon-q6a-fan-control): a 4-wire PWM fan with 5 V on pin 4, GND on pin 6, PWM on pin 16 (GPIO_26, gpiochip4 line 26) and optional tach on pin 18. Linear curve 40-70 C maps to 20-100 %. Ships a systemd unit. Tested on Armbian 25.11.2.
      - irusensei (geerlingguy/sbc-reviews#85): a script that switches the fan on at 70 C and off at 60 C.
    - **Outcome:** Software PWM works without a MOSFET for 4-wire PWM fans (such as the Noctua NF-A4x10 5V PWM). 2-wire fans still need on/off switching.
  5.
    - **Product:** Radxa Dragon Q6A bare board and 25 mm heatsink+fan (review)
    - **Source url:** https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5
    - **Community:** Independent review (Smart Home Circle)
    - **What they built:** Bench tests on Windows 11 and Armbian with NVMe + UFS + fan.
    - **Problems:**
      - The bare board shut down at about 105 C during vkmark.
      - With the 25 mm fan, Windows reached about 90-92 C after 10 minutes of stress.
    - **Fixes:**
      - A small Pi 4-style 25 mm heatsink+fan powered from GPIO.
    - **Outcome:** Under 80 C after 10 minutes of stress on Armbian, with no throttling. Power was 3.9-4 W idle and 9.5-10 W under stress. NVMe ran at ~1000 MB/s on Armbian. The review gives the board as 65x85 mm.
  6.
    - **Product:** Radxa Dragon Q6A power and thermal data, plus case fit
    - **Source url:** https://github.com/geerlingguy/sbc-reviews/issues/85
    - **Community:** GitHub (geerlingguy/sbc-reviews)
    - **What they built:** Benchmarking review board.
    - **Problems:**
      - The PoE HAT fan is noisy and has no speed control (irusensei).
      - Coolers may fit only if the M.2 slot is unused (MaybeNotABob, untested).
    - **Fixes:**
      - On/off fan script with 70/60 C hysteresis.
      - The Rock 5C metal case fits the Q6A, but the power button is hidden.
    - **Outcome:** Wall power was 2.9 W idle, 9.3 W stress-ng, and 10.1 W HPL. No temperature data. Clearance between the cooler and the M.2 slot is still unverified.
  7.
    - **Product:** Q6A M.2 slot with 2280 and NVMe devices
    - **Source url:** https://forum.radxa.com/t/nvme-2230-not-detected/30807
    - **Community:** Radxa forum
    - **What they built:** NVMe boot and storage.
    - **Problems:**
      - A 2230 NVMe was not detected after a sudden reboot; the board was returned under warranty (Corsair63).
      - Dust in the slot caused boot problems (rafaelwms).
    - **Fixes:**
      - Brush the slot clean.
      - Radxa staff (RadxaYuntian): 'Even 2280 devices can be just plugged in for testing' in J13. This shows a 2280 card physically seats in the socket and overhangs.
    - **Outcome:** willy (forum t/26723 #33) measured a Samsung 980 at Gen3 x2 and 1.3 GB/s. Boot priority is NVMe > UFS > SD/USB.
  8.
    - **Product:** Q6A power input (J21 12 V/GND/PWR header, USB-C) for battery projects
    - **Source url:** https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
    - **Community:** Radxa forum
    - **What they built:** Outdoor battery-powered Q6A (herbk).
    - **Problems:**
      - Official input voltage range not published.
      - A faulty '12 V' adapter caused DDR/boot problems (Catalin_Damian, forum t/29863).
    - **Fixes:**
      - BigfootACA: the 12 V pin accepts about 3.6-16 V, and 5/9/12 V is recommended. It is regulated down to 4.2 V. Do not use USB-C while feeding 12 V externally. PWR acts as a power key.
      - Analogous case (Rock 5B, https://forum.radxa.com/t/m-2-to-pcie-adapter-issues/13559): a PCIe card on an M.2 adapter would not boot until the user switched from USB-PD to a constant 12 V bench supply.
    - **Outcome:** Usable for a battery build through a buck regulator. A full 4S pack (16.8 V) is above the unofficial 16 V limit.
  9.
    - **Product:** Q6A with Radxa 256 GB UFS (Kioxia) module
    - **Source url:** https://forum.radxa.com/t/ufs-random-reboots/30630
    - **Community:** Radxa forum
    - **What they built:** UFS-booted systems.
    - **Problems:**
      - Random stutter, freezes and reboots, with ufshcd-qcom PM/hibernate errors and fio at ~60 MB/s. Temperatures were under 40-60 C with a fan-cooled 13 mm copper heatsink, so heat is not the cause.
    - **Fixes:**
      - Boot firmware 260120 and limit-hs-gear=<2> were tried; neither helped. Radxa saw no issues on Samsung UFS.
    - **Outcome:** Unresolved as of the last post (Apr 21 2026).
  10.
    - **Product:** LimeSDR XTRX (LMS7002M + FPGA, mPCIe), closest analogue for LimeSDR Micro thermals
    - **Source url:** https://discourse.myriadrf.org/t/temperature-of-limesdr-xtrx/8366
    - **Community:** MyriadRF Discourse
    - **What they built:** Open-air bench, a PCIe adapter, and a fanless small build.
    - **Problems:**
      - 60 C on the LMS7002M after 5 minutes of tests at 25 C ambient (sergey).
      - Above 85 C near maximum sample rate (0x12BFB9FA).
      - About 80 C running only an FM receiver, with no room for a fan (markpaz).
      - The Crowd Supply adapter arrived without the advertised pad or bracket (aardric).
    - **Fixes:**
      - A 40 mm fan brought the board to ~50-55 C.
      - Lime (andrewback): the full-size adapter uses a thermal pad to a large copper pour. Measure for your own sample rate, enclosure and ambient.
      - aardric bought a pad from Mouser (~$20).
    - **Outcome:** Fan cooling works. Staff gave no official maximum temperature (85 C cited for the old XTRX Pro).
  11.
    - **Product:** LimeSDR Micro M.2 2280 power draw
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
    - **Community:** MyriadRF Discourse
    - **What they built:** Carrier-board design (jonsnow, Aug 2026).
    - **Problems:**
      - The schematic shows a 2.5 A at 3.3 V (8.25 W) allowance.
    - **Fixes:**
      - Lime's Zack: the 2.5 A figure comes from the PCIe spec. The board 'should consume about 4 W, depending on configuration'.
    - **Outcome:** Idle power was asked about but not answered. Lime docs still say to design cooling for at least 10 W (https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html). No user deliveries or thermal reports on Discourse as of mid-Oct 2026.
  12.
    - **Product:** LimeSDR Mini (LMS7002M under a shield can)
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-mini-thermal-pad/3132
    - **Community:** MyriadRF Discourse
    - **What they built:** Pi 4 and PC hosts, an aluminium case, and fan mods.
    - **Problems:**
      - 65 C+ after 1 hour idle on a Pi 4 (TobyThomson, https://discourse.myriadrf.org/t/limesdr-mini-very-hot-on-idle/6384).
      - No factory pad under the shield.
      - Band 7 LTE TX would not calibrate when hot (herlesupreeth).
    - **Fixes:**
      - A small 5 V fan dropped it from 60 C to 38 C (HansKarel), wired to J10 5 V/GND.
      - A 13x13x3 mm copper plate under the shield dropped the LMS7002 from 50 C to 41.8 C (tony1tf, IR measurement).
      - Lime's Zack: active cooling is best. andrewback warned that adding material near RF parts can affect RF performance.
    - **Outcome:** Fans resolved it. Pads under shields worked but carry an RF caveat.
  13.
    - **Product:** LimeSDR XTRX on Raspberry Pi 5 / CM4 through various PCIe HATs and adapters
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-xtrx-not-found/8342?page=2
    - **Community:** MyriadRF Discourse
    - **What they built:** ARM SBC host with an SDR on an FPC/adapter chain.
    - **Problems:**
      - Intermittent enumeration. The M.2 HAT+ failed about 2 times in 30 reboots; GeeekPi HATs needed many reboots (sergey suspected signal integrity).
      - MSI failure ('device only supports 32 bits'), probe error -5.
      - mmap failure caused by the Pi 5's 16 KB PAGE_SIZE.
    - **Fixes:**
      - dtoverlay=pciex1-compat-pi5,no-mip as a temporary fix.
      - Gateware update for 64-bit DMA via limeFLASH plus power cycle.
      - Driver fix for 16 KB pages (ricardas).
      - Use the adapter that enumerates most reliably.
    - **Outcome:** basicRX/TX worked after the gateware and driver fixes (masefi, Jul 2024). Some Pi 5 adapters still never enumerated.
  14.
    - **Product:** LimeSDR XTRX on Jetson Orin via an NGFF-to-mPCIe adapter cable
    - **Source url:** https://discourse.myriadrf.org/t/lms-xtrx-not-detected-by-lspci/8446
    - **Community:** MyriadRF Discourse
    - **What they built:** ARM host with an SDR on a passive cable adapter.
    - **Problems:**
      - Not seen by lspci, while an EPIQ Sidekiq on the same cable was.
    - **Fixes:**
      - Lime (andrewback): without PERST connected, detection depends on the host. It works on some, fails on others, and is borderline on some. Fixed per the same post as in the 'XTRX not found' thread.
    - **Outcome:** Detected after the fix. Lesson: a riser must carry PERST#, CLKREQ# and REFCLK properly.
  15.
    - **Product:** ADT-Link M.2 risers/adapters (general)
    - **Source url:** https://forums.anandtech.com/threads/any-experience-issues-with-nvme-key-m-extender-cable.2601704/
    - **Community:** AnandTech forums; Level1Techs
    - **What they built:** ADT M.2-to-PCIe riser with a Mellanox ConnectX-3 on an Asus B450-I.
    - **Problems:**
      - Linux logged 'PCIE error correction messages' that did not appear when the NIC sat directly in a slot (thigobr, 2022).
      - A Level1Techs user reported that a 4-lane ADT variant sometimes negotiated only x1/x2 (https://forum.level1techs.com/t/m-2-to-pcie-adapter-myth-or-reality/207239).
    - **Fixes:**
      - Returned the adapter (AnandTech).
      - Level1Techs: 'ADT link is a solid brand to look for when shopping for weird adapters and risers'. Another user reports many ADT adapters working for over 2 years (https://forum.level1techs.com/t/low-profile-m-2-to-u-2-4-0x4-adapter/240695).
    - **Outcome:** Mixed results. I found no report on the R44SF M.2-to-M.2 extender itself.
  16.
    - **Product:** 25 cm M.2 2242-to-PCIe riser (generic) on Linux
    - **Source url:** https://forum.proxmox.com/threads/force-pcie-port-downgrade-at-boot-or-solve-aer-errors.173498/
    - **Community:** Proxmox forum
    - **What they built:** Mini PC with a 10GbE NIC or HBA on an M.2 riser (logan893, Oct 2025).
    - **Problems:**
      - AER floods (BadTLP, BadDLLP, RxErr). X540 Tx hangs and reset loop. ~400 correctable errors/s on an LSI 3008.
    - **Fixes:**
      - A setpci link-speed script removed the errors only until the link retrained.
      - Taping lanes to x1 worked but cut throughput.
      - Final fix: add pcie_aspm=off to the kernel cmdline (/etc/kernel/cmdline + proxmox-boot-tool refresh, then check /proc/cmdline).
    - **Outcome:** AER stopped. A 10-hour iperf3 averaged ~9 Gbps each way. The cost is higher idle power.
  17.
    - **Product:** Raspberry Pi 5 PCIe FPC at Gen 3
    - **Source url:** https://www.jeffgeerling.com/blog/2023/forcing-pci-express-gen-30-speeds-on-pi-5/
    - **Community:** Jeff Geerling blog
    - **What they built:** NVMe, a 10G NIC and a Coral TPU on the Pi 5 FFC.
    - **Problems:**
      - Occasional link errors from FPC insertion loss. The Coral TPU kept resetting at every generation.
    - **Fixes:**
      - Use Gen 2 when errors appear.
    - **Outcome:** NVMe went from 450 to 900 MB/s at Gen 3. Some devices never worked over the FPC.
  18.
    - **Product:** Radxa ROCK Pi 4 M.2 extension ribbon inside an aluminium ecoPI Pro case
    - **Source url:** https://forum.radxa.com/t/rockpi-4b-m-2-extension-board-v1-6-and-ecopi-pro-case/14164
    - **Community:** Radxa forum
    - **What they built:** SBC + NVMe on a flex ribbon in a closed metal case.
    - **Problems:**
      - The ribbon was folded and pressed by the case. The system crashed after 6 months and would not boot when the case was closed. The first cable died on first assembly, and the cable showed crease marks.
    - **Fixes:**
      - Radxa (NBA): do not add extra spacers; relieve stress on the ribbon and its connectors. Radxa sent replacement cables.
    - **Outcome:** Recurring until the cable was free of stress. Lesson: no case pressure on the flex and no tight folds.
  19.
    - **Product:** U.FL (IPEX1) to SMA pigtails on LimeSDR-USB in a Luftek enclosure (relevant to MHF4 handling)
    - **Source url:** https://discourse.myriadrf.org/t/plug-in-u-fl-pigtails/2620
    - **Community:** MyriadRF Discourse
    - **What they built:** LimeSDR-USB with 10 pigtails to a panel.
    - **Problems:**
      - Only 4 of 10 pigtails from the enclosure kit mated properly (DL8WOW).
      - A forced pigtail ripped the TX transformer T2 (TCM1-63AX+) off the board.
      - Pinched inner contacts let plugs slide off sideways (MountainLogic).
    - **Fixes:**
      - Align with tweezers and press with a pencil eraser until it clicks.
      - Open a pinched contact carefully with a pin.
      - Replace the cheap pigtails with DigiKey ones.
      - Resolder or replace the transformer (Mini-Circuits sent free samples).
    - **Outcome:** Board repaired. The branded pigtails mated without problems.
  20.
    - **Product:** MHF4/IPEX4 on M.2 cards (laptop and Mac Pro use)
    - **Source url:** https://forums.macrumors.com/threads/antenna-connector-size-problem-with-newer-wifi-cards.2386704/
    - **Community:** MacRumors forum; SFF forum
    - **What they built:** M.2 Wi-Fi cards with fine coax pigtails.
    - **Problems:**
      - Mismatched female connectors popped off as soon as the card moved (MacRumors).
      - A connector broke off a card after forced reseating and tight routing (https://smallformfactor.net/forum/threads/replacing-m-2-wifi-bluetooth-laptop-antenna-cables.6902/).
    - **Fixes:**
      - Non-conductive clip or hot glue proposed for retention.
      - Avoid forcing and strain when routing.
    - **Outcome:** No standard fix. Strain relief and few mating cycles are the lesson.
  21.
    - **Product:** Open-source CNC aluminium case for LimeSDR USB (RF firewall, thermal pads, full SMA breakout)
    - **Source url:** https://discourse.myriadrf.org/t/open-source-cnc-aluminum-case-for-limesdr-usb-rf-shielded-thermal-pads-full-sma-breakout/13130
    - **Community:** MyriadRF Discourse + GitHub PhilipLykov/LimeSDRCase
    - **What they built:** Machined aluminium case with RF/control separation, pads to the lid, optional 4010 fan, STEP/F3D files.
    - **Problems:**
      - 100 mm SMA-IPEX pigtails made assembly hard.
      - Threads are not modelled.
    - **Fixes:**
      - Use 75 mm RG113 (sic) pigtails.
      - Tap threads during assembly (M4x30 case, M3x4 PCB).
    - **Outcome:** About 34 C passive in RX use. The fan was not needed.
  22.
    - **Product:** Raspberry Pi 4 + PSU next to SatNOGS/RTL-SDR receivers
    - **Source url:** https://community.libre.space/t/hf-noise-from-raspberypi-4/8302
    - **Community:** SatNOGS community
    - **What they built:** Fixed ground stations.
    - **Problems:**
      - The Pi 4 and its PSU added about 10 dB of noise (ar3itrary).
      - S9 noise on 2 m (vk2byf).
      - A ferrite on the USB lead made it worse.
    - **Fixes:**
      - Grounding to protective earth gave about 3 dB.
      - Grounded metal cases plus a 5 V linear regulator instead of switch-mode PSUs (vk2byf).
      - Linear PSU made from LT1083s with 100 nF + 1 nF decoupling removed most birdies (i3vfj).
      - Physical separation with the LNA at the antenna (vk5qi).
      - Disabling HDMI gave no measurable change in ar3itrary's tests.
    - **Outcome:** Linear supplies, grounded metal boxes and distance helped most. Copper and ferrite tricks alone were unreliable. A related observation (https://community.libre.space/t/rfi-example-unplugging-a-nearby-rpi4-during-a-pass/7987) showed noise disappearing when a Pi 4 about 4 ft away was unplugged mid-pass.
  23.
    - **Product:** Pi Zero + RTL-SDR in a copper-taped plastic box
    - **Source url:** https://forum.krakenrf.com/t/noise-in-the-432-mhz-band/649
    - **Community:** KrakenRF forum
    - **What they built:** 433 MHz receiver.
    - **Problems:**
      - After copper tape bonded to the USB and HDMI shields, the noise floor rose from about -63 to -60 dB (3 dB worse).
    - **Fixes:**
      - Replacing a faulty USB data cable gave a few dB.
    - **Outcome:** Not fully diagnosed. Tape shielding that is not bonded well can make noise worse.
  24.
    - **Product:** Portable Pi 4 + 7" LCD + RTL-SDR (SunFounder TS7-Pro) and RasPad 3.0 tablet with an internal RTL-SDR
    - **Source url:** https://www.rtl-sdr.com/raspad-3-0-review-building-a-portable-raspberry-pi-4-tablet-with-built-in-rtl-sdr/
    - **Community:** RTL-SDR.com
    - **What they built:** Handheld SDR terminals.
    - **Problems:**
      - TS7-Pro: LCD electronics caused interference on some bands. It entered mostly through the antenna and coax; with the antenna removed there was almost none (https://www.rtl-sdr.com/?p=55992).
      - RasPad: interference appeared with a whip directly on the SMA or an antenna within 2-3 cm of the screen.
      - The RasPad fan was noisy and cooled poorly.
    - **Fixes:**
      - Shielded coax to an antenna kept away from the LCD.
      - Bulkhead SMA with a short shielded jumper.
      - Bigger or blower fan (reader).
    - **Outcome:** RasPad weighed just under 1 kg and ran 2 h 10 min at full brightness with SDR++. Remote antenna placement reduced the LCD noise but did not remove it.
  25.
    - **Product:** HDMI emissions (Pi 4 at 1440p; HDMI clock lines)
    - **Source url:** https://www.rtl-sdr.com/using-a-hackrf-to-investigate-why-wifi-on-the-raspberry-pi-4-doesnt-work-when-running-hdmi-at-1440p/
    - **Community:** RTL-SDR.com, CNX Software, sigidwiki
    - **What they built:** Near-field probe measurements with a HackRF.
    - **Problems:**
      - 2560x1440@60 (241.5 MHz pixel clock) produced a large TMDS spike at about 2.415 GHz that killed 2.4 GHz Wi-Fi channel 1.
      - sigidwiki lists HDMI lines at 148.35/148.5/296.7/297/445.05/445.5/742.5 MHz with about 700 kHz width (https://www.sigidwiki.com/wiki/HDMI_RFI_Clock).
    - **Fixes:**
      - Lower the resolution to 2048x1080 or below, or move Wi-Fi to 5 GHz.
      - A proposed vc4 kernel patch nudges the clock off Wi-Fi channel 1.
    - **Outcome:** The emission depends on the video mode and is avoidable by choosing the mode.
  26.
    - **Product:** ClockworkPi uConsole (CM4/CM5) handheld cooling, a sealed-case analogue
    - **Source url:** https://forum.clockworkpi.com/t/effective-cm5-cooling-solution/18180
    - **Community:** ClockworkPi forum
    - **What they built:** Handheld Linux SDR terminals with SoC pads to the aluminium back.
    - **Problems:**
      - About 60 C under load stock; spikes to ~80 C from badly fitted pads.
      - 67 C heat soak in a backpack (Lanthar).
    - **Fixes:**
      - Two layers of ARCTIC TP-3 to the back shell plus an external heatsink on 1" thermal tape (bgav).
      - Separate small pads per chip (L_Huddy).
      - Copper plate inside the case (Lanthar).
    - **Outcome:** Idle in the low 40s C and ~51 C under load, about 10 C lower (bgav). 50-60 C under medium-heavy load (Lanthar).
  27.
    - **Product:** uConsole printed backplates: PLA vs SLA vs PA12-HP nylon (MJF), with a fan
    - **Source url:** https://forum.clockworkpi.com/t/simple-extensible-backplate-replacement/20144
    - **Community:** ClockworkPi forum
    - **What they built:** Replacement backplate with an active fan for CM5 + HackerGadgets board, at 32-36 C ambient.
    - **Problems:**
      - PLA was 'not great' for heat. The SLA battery cover warped within weeks.
      - An aluminium plate was not available.
      - Fingers hit the fan.
    - **Fixes:**
      - Printed in PA12-HP nylon (JLC3DP, deflection temperature 175 C, ~$10-25).
      - Added a fan cover.
      - 5-step fan curve: off below 45 C, then steps at 45, 53, 58 and 63 C.
    - **Outcome:** 40-51 C under normal load, never above 55 C at 32-36 C ambient. Wi-Fi improved slightly because nylon is RF-transparent.
  28.
    - **Product:** uConsole HackerGadgets NVMe battery board (2230-2280 slot) and dual 21700 holder; Lime's LimeSDR Micro uConsole demo
    - **Source url:** https://forum.clockworkpi.com/t/hackergadgets-uconsole-upgrade-kit-adding-nvme-ssd-pcie-rj45-ethernet-and-usb-3-0-to-your-uconsole/20019
    - **Community:** ClockworkPi forum + Crowd Supply update
    - **What they built:** Handheld with an M.2 2280 PCIe slot next to the Li-ion cells. Lime showed a LimeSDR Micro in a CM5 uConsole running Gqrx at 40 Msps (https://www.crowdsupply.com/lime-micro/limesdr-micro/updates/thanks-and-uconsole-gqrx-demo); the connection method is not documented.
    - **Problems:**
      - Card plus heatsink must be under 5 mm thick (vileer).
      - Hot NVMe sits against the batteries (UJW).
      - Charging 21700 cells inside an already warm device stacks heat (Wander_Menezes, https://forum.clockworkpi.com/t/new-hacker-gadgets-dual-21700-battery-holder/23216).
    - **Fixes:**
      - Plastic insulation between the drive and the cells, thermal tape on the NVMe (MarkoeZ, suggested).
      - An M.2 heatsink on the back cover with adhesive held for 8 months; max 60 C (Rex).
    - **Outcome:** Works. No published LimeSDR Micro thermal data from the demo. The dual 21700 board gave 4 h 31 min of 1080p playback versus 2 h 27 min with 18650s.
  29.
    - **Product:** PLA/PETG/ASA printed parts in sun
    - **Source url:** https://forum.prusa3d.com/forum/english-forum-general-discussion-announcements-and-releases/my-print-melted-on-my-window-sill
    - **Community:** Prusa forum
    - **What they built:** Window-sill and car parts.
    - **Problems:**
      - A black thin-wall PLA print collapsed within hours on a sunny sill.
      - PETG went soft in a car in summer (FoxRun3D).
    - **Fixes:**
      - Use ASA or PC-CF outdoors (FoxRun3D, _KaszpiR_).
      - Light colours help.
    - **Outcome:** Experienced users move to ASA for sun exposure. One poster wrongly gave PETG Tg as ~100 C; it is about 80 C.
  30.
    - **Product:** Heat-set brass inserts under load (relevant to a 1/4"-20 tripod thread)
    - **Source url:** https://community.carbide3d.com/t/printed-t-nuts-for-hybrid-table-1500lb-clamping-force-possible/43704
    - **Community:** Carbide3D forum
    - **What they built:** Printed T-nuts with heat-set inserts.
    - **Problems:**
      - The insert pulled out at about 80 in-lb: the knurled brass pulled through the plastic.
    - **Fixes:**
      - Post-heat so the plastic flows into the knurls. Captive hex nuts are a common alternative in tripod mounts.
    - **Outcome:** Inserts are fine for light loads. Prefer a nut captured in or tapped into a metal plate for a 1 kg device on a boom.
  31.
    - **Product:** Compass and magnetometer near fans and electronics (BNO-class IMU)
    - **Source url:** https://discuss.bluerobotics.com/t/external-compass/15947
    - **Community:** Blue Robotics forum (via search)
    - **What they built:** ROV with an external compass and a Jetson Nano.
    - **Problems:**
      - A 20-30 degree heading offset.
    - **Fixes:**
      - Tested a fan on/off (<1 degree change) and Jetson CPU load (~1 degree). Neither explained the offset. CEVA requires calibration in the final assembled device (Mouser BNO080/085 calibration PDF).
    - **Outcome:** The fan is not the main error source. Ferrous parts and battery currents, plus calibration in the final assembly, matter more.
- **Common problems:**
  1.
    - **Problem:** The Q6A throttles at about 90 C with passive or official-case cooling, and the bare board shuts down at about 105 C
    - **Affected products:** Radxa Dragon Q6A bare, homemade passive heatsinks, Armor Case 7056A in hot ambient
    - **Frequency:** common
    - **Known fix:** Stepped copper heatsink (paste on the SoC, pad on the LPDDR5) plus a 25-40 mm 5 V fan on the 40-pin 5 V/GND pins. This keeps it at about 55-80 C under stress on Linux.
    - **Fix sources:**
      - https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
      - https://forum.radxa.com/t/recommended-heatsink-fan-for-q6a/30413
      - https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5
  2.
    - **Problem:** No fan header and no hardware PWM on the Q6A header, so fans run at full speed and are noisy
    - **Affected products:** Radxa Dragon Q6A
    - **Frequency:** common
    - **Known fix:** Use a 4-wire PWM fan with Calin23/dragon-q6a-fan-control (PWM on pin 16 / GPIO_26, tach on pin 18, systemd service), or a pwm-gpio DT overlay, or on/off switching at 70/60 C. A Noctua NF-A4x10 5V replaced a loud stock fan.
    - **Fix sources:**
      - https://github.com/Calin23/dragon-q6a-fan-control
      - https://forum.radxa.com/t/pwm-on-radxa-dragon-q6a/30201
      - https://github.com/geerlingguy/sbc-reviews/issues/85
  3.
    - **Problem:** Third-party Q6A coolers fit badly (pad too small for the DDR5, standoff order) and stock comes and goes
    - **Affected products:** AliExpress copper Q6A coolers, Armor Case
    - **Frequency:** occasional
    - **Known fix:** Add a second pad. Shorter standoffs on the PCB, longer below. Buy through Amazon or Arace.
    - **Fix sources:**
      - https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
      - https://forum.radxa.com/t/recommended-heatsink-fan-for-q6a/30413
  4.
    - **Problem:** Small LMS7002M SDR boards run hot (65-85 C) without airflow
    - **Affected products:** LimeSDR XTRX, LimeSDR Mini (and by extension the LimeSDR Micro)
    - **Frequency:** common
    - **Known fix:** A 30-40 mm fan gives 25-35 C lower readings (to about 38-55 C). A thermal pad to a copper pour or plate also helps; take care with pads inside RF shields.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/temperature-of-limesdr-xtrx/8366
      - https://discourse.myriadrf.org/t/limesdr-mini-thermal-pad/3132
      - https://discourse.myriadrf.org/t/limesdr-mini-very-hot-on-idle/6384
  5.
    - **Problem:** PCIe devices on risers, FPCs or adapters enumerate intermittently or log AER errors
    - **Affected products:** ADT-Link and generic M.2 risers, Pi 5 FPC HATs, NGFF adapter cables
    - **Frequency:** occasional
    - **Known fix:** Test over many cold boots. Check lspci LnkSta and dmesg AER. Add pcie_aspm=off. Drop the link speed (max-link-speed in DT, or Gen 2). Use an adapter that carries PERST#, CLKREQ# and REFCLK; swap to a better adapter if it still fails.
    - **Fix sources:**
      - https://forum.proxmox.com/threads/force-pcie-port-downgrade-at-boot-or-solve-aer-errors.173498/
      - https://discourse.myriadrf.org/t/limesdr-xtrx-not-found/8342?page=2
      - https://discourse.myriadrf.org/t/lms-xtrx-not-detected-by-lspci/8446
      - https://www.jeffgeerling.com/blog/2023/forcing-pci-express-gen-30-speeds-on-pi-5/
  6.
    - **Problem:** A flex PCIe cable is damaged by folds or case pressure and fails months later
    - **Affected products:** Radxa M.2 extension ribbons in metal cases (generalises to any flex riser)
    - **Frequency:** occasional
    - **Known fix:** Route with no pressure from the case. One gentle fold at most, and keep standoffs at the designed height.
    - **Fix sources:**
      - https://forum.radxa.com/t/rockpi-4b-m-2-extension-board-v1-6-and-ecopi-pro-case/14164
  7.
    - **Problem:** Cheap micro-coax pigtails vary in quality, do not mate, damage the SDR or pop off
    - **Affected products:** U.FL/MHF1 and MHF4 pigtails
    - **Frequency:** occasional
    - **Known fix:** Buy branded pigtails (DigiKey or Lime's $6 cable) or test each one. Seat with tweezers and an eraser. Never force. Strain-relieve at both ends. Keep them about 75-100 mm.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/plug-in-u-fl-pigtails/2620
      - https://discourse.myriadrf.org/t/open-source-cnc-aluminum-case-for-limesdr-usb-rf-shielded-thermal-pads-full-sma-breakout/13130
      - https://forums.macrumors.com/threads/antenna-connector-size-problem-with-newer-wifi-cards.2386704/
  8.
    - **Problem:** SBC, PSU, LCD and HDMI noise enters the SDR, mostly through the antenna and coax
    - **Affected products:** Pi 4/5-class SBC builds with an RTL-SDR, handheld SDR tablets
    - **Frequency:** common
    - **Known fix:** Separation, with the LNA at the antenna. Linear or well-filtered supplies for the SDR rail. Grounded metal enclosures. Keep antennas and coax several cm or more from the LCD. Pick an HDMI mode whose clocks miss your bands.
    - **Fix sources:**
      - https://community.libre.space/t/hf-noise-from-raspberypi-4/8302
      - https://www.rtl-sdr.com/raspad-3-0-review-building-a-portable-raspberry-pi-4-tablet-with-built-in-rtl-sdr/
      - https://www.rtl-sdr.com/?p=55992
      - https://www.sigidwiki.com/wiki/HDMI_RFI_Clock
  9.
    - **Problem:** Copper tape shielding does nothing, or makes noise worse, when bonding is poor
    - **Affected products:** Taped plastic boxes and dongles
    - **Frequency:** occasional
    - **Known fix:** Bond tape to the connector shields and the ground plane at several points, or use soldered copper-clad FR4 or shield cans. Ferrites need testing because one made things worse.
    - **Fix sources:**
      - https://forum.krakenrf.com/t/noise-in-the-432-mhz-band/649
      - https://www.rtl-sdr.com/shielding-the-sdrplay-rsp-copper-tape/
  10.
    - **Problem:** Printed enclosures soften or warp in sun or heat
    - **Affected products:** PLA, PETG, SLA resin parts
    - **Frequency:** common
    - **Known fix:** Use ASA, PC-CF or MJF PA12 nylon. Light colours.
    - **Fix sources:**
      - https://forum.prusa3d.com/forum/english-forum-general-discussion-announcements-and-releases/my-print-melted-on-my-window-sill
      - https://forum.clockworkpi.com/t/simple-extensible-backplate-replacement/20144
  11.
    - **Problem:** Heat stacks in sealed handhelds (SoC, NVMe, Li-ion cells during charging, heat soak in a bag)
    - **Affected products:** uConsole CM5 builds with an NVMe and 21700 board
    - **Frequency:** occasional
    - **Known fix:** Pads to a metal back plus an external heatsink or fan. Insulate the cells from hot M.2 cards. Avoid charging while under heavy load.
    - **Fix sources:**
      - https://forum.clockworkpi.com/t/effective-cm5-cooling-solution/18180
      - https://forum.clockworkpi.com/t/hackergadgets-uconsole-upgrade-kit-adding-nvme-ssd-pcie-rj45-ethernet-and-usb-3-0-to-your-uconsole/20019
      - https://forum.clockworkpi.com/t/new-hacker-gadgets-dual-21700-battery-holder/23216
  12.
    - **Problem:** Unstable boot or link with PCIe cards on USB-PD power
    - **Affected products:** Rock 5B with an M.2-to-PCIe adapter (analogous to the Q6A)
    - **Frequency:** rare
    - **Known fix:** Feed a constant 12 V into the DC header instead of USB-PD.
    - **Fix sources:**
      - https://forum.radxa.com/t/m-2-to-pcie-adapter-issues/13559
      - https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
- **Unresolved problems:**
  1.
    - **Problem:** No public report of a LimeSDR Micro M.2 (or any PCIe SDR) on a Dragon Q6A or another QCS6490 board, with or without a riser. No measured LimeSDR Micro temperatures or idle power.
    - **Why it matters for us:** The riser choice, heatsink size and fan curve all rest on Lime's '>=10 W' guidance and Zack's '~4 W'. LMS7002M boards (XTRX, Mini) reach 65-85 C without airflow. This must be measured on the first unit through the TMP1075.
    - **Evidence:** Discourse searches (Oct 2026) show only questions; Crowd Supply deliveries start now and new orders ship Dec 15 2026; https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
  2.
    - **Problem:** No user report on the ADT-Link R44SF M.2-to-M.2 extender itself, especially with a 2230-mounted male end on an ARM host. Retention of the male end in a 2230 screw position is also unverified.
    - **Why it matters for us:** It is the key mechanical part. Pi 5 and XTRX experience shows adapters that work on x86 can fail to enumerate on ARM about 1 boot in 15 or worse.
    - **Evidence:** ADT page lists specs only (https://www.adt.link/product/R44SF.html); Level1Techs and AnandTech have reports for other ADT products only
  3.
    - **Problem:** No one has reported fitting a Q6A copper cooler or the Armor Case together with anything in the M.2 slot.
    - **Why it matters for us:** The riser male end and its 3.8 mm stack sit beside the SoC heatsink area, so the cooler may need to be modified or replaced by a custom fin stack.
    - **Evidence:** MaybeNotABob in https://github.com/geerlingguy/sbc-reviews/issues/85 ('other coolers may fit if M.2 slot unused', untested); el_sattchmo planned a separate M.2 2230 cooler but posted no data
  4.
    - **Problem:** No measurements of RF emissions from the Q6A's HDMI path (DP-to-HDMI bridge) or from a >FHD panel, near 137/145/435/1700/2200 MHz.
    - **Why it matters for us:** HDMI lines are documented at 148.5, 297, 445.5 and 742.5 MHz. 148.5 MHz is 2.7 MHz from ISS 145.8 MHz. 445.5 MHz falls inside a 56 MHz window around 435-438 MHz. 742.5 MHz sits next to the old LNB IF (~739.5-749 MHz). TMDS for 2560x1440@60 is 2.415 GHz. (Offsets are computed.) The video mode should be chosen to avoid the bands.
    - **Evidence:** https://www.sigidwiki.com/wiki/HDMI_RFI_Clock; https://www.rtl-sdr.com/using-a-hackrf-to-investigate-why-wifi-on-the-raspberry-pi-4-doesnt-work-when-running-hdmi-at-1440p/; radrocks on the bridge chip https://forum.radxa.com/t/stock-fedora-support/30893/16
  5.
    - **Problem:** The effect of Q6A Wi-Fi 6, USB 3.1 and the SoC itself on L/S-band reception inside one box is unmeasured.
    - **Why it matters for us:** The S-band (2.2 GHz) and HRPT (1.7 GHz) margins are small. Community fixes (distance, linear supplies) are hard to apply in a palm-sized device.
    - **Evidence:** Only Pi 4 data exists (~10 dB on HF/VHF, https://community.libre.space/t/hf-noise-from-raspberypi-4/8302)
  6.
    - **Problem:** Random reboots with the Radxa 256 GB Kioxia UFS module are unresolved. It is not thermal: temperatures stay under 40-60 C.
    - **Why it matters for us:** Storage for raw IQ depends on UFS because the M.2 slot holds the SDR. Do not misdiagnose these reboots as overheating; prefer a Samsung-based UFS module.
    - **Evidence:** https://forum.radxa.com/t/ufs-random-reboots/30630
  7.
    - **Problem:** No official input voltage range for J21. A community answer says about 3.6-16 V.
    - **Why it matters for us:** A fully charged 4S pack reaches 16.8 V, so feeding J21 directly could exceed the limit. A buck to 12 V is needed. USB-C must never be connected at the same time.
    - **Evidence:** https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
  8.
    - **Problem:** The Q6A has exposed battery pogo pads (+/-/TS) on the bottom, with no guidance on clearance or isolation.
    - **Why it matters for us:** The planned aluminium mid-plate under the board, with a pad on the bottom-side UFS module, could short them. They need a cut-out or a Kapton barrier (my inference).
    - **Evidence:** https://forum.radxa.com/t/question-about-the-three-pogo-pads-ts-on-the-back-of-dragon-q6a/30090; https://forum.radxa.com/t/radxa-q6a-running-on-a-battery-and-charging/29650
  9.
    - **Problem:** Board size is inconsistent: the Radxa 2D drawing gives 85x56 mm, while a review and the project brief say 85x65 mm.
    - **Why it matters for us:** It changes the case layout and battery placement.
    - **Evidence:** https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5 vs. https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_2d_dimensions_v1.21.pdf
  10.
    - **Problem:** No data on sun load for a >=1000-nit display inside a closed printed case. High-nit monitors have unexplained black-screen reports in sun.
    - **Why it matters for us:** The panel adds several watts of internal heat on top of 17-25 W from electronics. LCD clearing or shutdown could happen before the SoC throttles.
    - **Evidence:** https://greyarro.ws/t/crystal-sky-monitor-screen-going-black/35877 (not fetched; seen in search only)
  11.
    - **Problem:** No community insertion-loss tests or quality reports for prom.ua or AliExpress MHF4-to-SMA pigtails.
    - **Why it matters for us:** Up to 6 of 10 cheap U.FL pigtails failed to mate in one LimeSDR case. MHF4 is smaller and rated for only about 30 cycles, and a bad one can tear a connector off the $249 SDR.
    - **Evidence:** https://discourse.myriadrf.org/t/plug-in-u-fl-pigtails/2620; vendor listings only for MHF4
  12.
    - **Problem:** BATC forum (Portsdown 4 + LimeSDR Mini thermal and noise experience) returned HTTP 503, so that experience is not verified.
    - **Why it matters for us:** Portsdown (Pi + LimeSDR + touchscreen in a box) is the closest existing LimeSDR-plus-SBC-plus-display product. A search snippet mentions Pi >75 C 'excessive temperature' warnings after about 5 minutes.
    - **Evidence:** https://forum.batc.org.uk/viewtopic.php?p=29854 (503 at fetch time)
- **Communities checked:**
  - Radxa forum (forum.radxa.com): reachable via search.json, about 20 threads read
  - MyriadRF/Lime Discourse (discourse.myriadrf.org): reachable, about 12 threads read
  - ClockworkPi forum (forum.clockworkpi.com): reachable with intermittent connection resets
  - SatNOGS community (community.libre.space): reachable
  - GitHub: geerlingguy/sbc-reviews#85, Calin23/dragon-q6a-fan-control, myriadrf/LimeSuiteNG issue search (read via WebFetch; gh API not enabled for these repos)
  - Crowd Supply LimeSDR Micro page and updates; myriadrf.org docs and stories
  - RTL-SDR.com articles (shielding, TS7-Pro, RasPad 3, Pi 4 HDMI and Wi-Fi)
  - Level1Techs forum (search.json)
  - Proxmox forum
  - AnandTech forums
  - Prusa forum
  - KrakenRF forum
  - Core Electronics forum
  - Jeff Geerling blog
  - Smart Home Circle review
  - sigidwiki
  - Armbian forum (search returned nothing relevant to the Q6A)
  - Carbide3D and Blue Robotics forums (via web search results)
  - UNREACHABLE: Reddit (blocked by network policy; site:reddit searches returned nothing), BATC forum (HTTP 503), Printables (403), Hackster (403), NVIDIA developer forums (403), MavicPilots (403), AliExpress listings (redirect / JS)
  - NOT CHECKED (budget): EEVblog direct search, mikrocontroller.net, Funkamateur, AMSAT-BB/UK/DL, groups.io, Qualcomm developer forums, Ubuntu Discourse, StackExchange
- **Recommendation impact:** The community evidence supports the recommended architecture (flex riser, separate RF bay, fan-cooled SoC, ASA shell with a metal mid-plate). It changes several details.
  
  (1) Riser. ADT-Link is the brand the community trusts, but no one has tested the R44SF on an ARM host.
  - Keep it to 5-10 cm, fold it once at most, and make sure no case surface presses on the flex. A Radxa ribbon pressed by an aluminium case failed after 6 months.
  - Acceptance test: 30+ cold boots to check enumeration, `lspci -vv` LnkSta, and a clean `dmesg | grep -i aer` during a 60-minute 61.44 Msps stream.
  - Fallbacks if errors appear: `pcie_aspm=off` on the kernel command line, then `max-link-speed = <2>` in the DT.
  - Check that the riser carries PERST#. The XTRX/Orin case shows passive cables without it fail on some hosts.
  - Radxa staff confirm a 2280 card plugs straight into J13 for bench tests. Use that first, to separate driver problems from riser problems.
  - If the riser fails, a QCS6490 board with a native M.2 2280 slot and a fan header (Thundercomm Rubik Pi 3) removes the riser entirely.
  
  (2) Cooling. For the Q6A, use the stepped copper block (with a second pad for the DDR5) or a custom fin stack, plus a Noctua NF-A4x10 5V PWM. Drive it with the Calin23 software-PWM script (pin 16, tach pin 18), so no MOSFET is needed. The Armor Case alone is not enough at 35-40 C ambient. For the LimeSDR Micro, plan a top-side heatsink in the airflow path from day one; XTRX and Mini precedents show 65-85 C without a fan and 38-55 C with one.
  
  (3) Pigtails. Buy Lime's $6 MHF4L-SMA cables or branded ones. If you buy prom.ua cables, test each one on a spare before it touches the SDR. Use 75-100 mm, strain-relieve both ends, and never re-mate them casually.
  
  (4) Shielding. The largest gains come from distance (LNA at the antenna), filtered or linear rails for the SDR, and well-bonded metal walls. Copper tape that is not bonded properly made one build 3 dB worse. Keep antenna leads several cm or more from the LCD. Choose an HDMI mode whose pixel and TMDS clocks avoid 137-138, 145.8, 435-438, 1698-1707 and 2200-2290 MHz. Put ferrites on the HDMI lead.
  
  (5) Shell. Use ASA, or MJF PA12 if you outsource; not PLA, PETG or SLA. Nylon and ASA also keep Wi-Fi and GNSS antennas working. Leave a cut-out or insulation over the Q6A's bottom battery pads where the mid-plate sits. Insulate the 21700 cells from the SDR and SoC heat. Do not charge during heavy passes.
  
  (6) Power. Feed J21 from a 12 V buck; the community says the limit is about 16 V, and a full 4S pack is 16.8 V. A constant 12 V supply is more robust than USB-PD with PCIe loads.
  
  (7) Tripod mount. Put the 1/4"-20 thread in the metal plate, or use a captured nut. Heat-set inserts can pull out.
  
  (8) Size and weight. The RasPad 3 weighs just under 1 kg, which supports the 1.0-1.2 kg estimate. Plan on a strap or boom mount, and calibrate the IMU in the finished assembly.
  
  (9) Price. LimeSDR Micro M.2 Basic is now $249, and new orders ship Dec 15, 2026.
  
  (10) Storage. Avoid the 256 GB Kioxia UFS module (unresolved reboots); this is a storage problem, not a thermal one.

## Власні виправлення (`fixes`)

_Run `wf_e6b8e5e2-124`_

- **Component:** Mechanical, thermal and enclosure: M.2 riser, LimeSDR Micro and Q6A cooling, case, RF shielding, power entry, display thermal, pigtails
- **Fixes:**
  1.
    - **Problem:** No public report of a LimeSDR Micro M.2 on a Dragon Q6A or any QCS6490 board, and no measured LimeSDR Micro temperature or idle power. Cooling is currently sized from Lime's '>=10 W' guidance and a '~4 W' forum figure.
    - **Proposed fix:** Measure on the first unit using sensors the board already has, and build the cooling for 10 W with a 55/45 C fan rule.
  
  Facts checked:
  - The Q6A M.2 slot has its own 3.3 V buck (ETA3521 U20, net VCC_3V3_MKEY, schematic v1.21 sheet 33). The LimeSDR draws all its power from M.2 3.3 V.
  - Lime's Zack says 2.5 A x 3.3 V = 8.25 W is only the PCIe spec limit; the board 'should consume about 4 W'.
  - The LimeSuiteNG limesdr-micro branch (commit 80ffad5, 1 Oct 2026) exposes the TMP1075 (IC10) as custom parameter 'Board Temperature' (id 1). `limeDevice --full` prints it next to 'Temperature(LMS7002)'. The SoapySDR plugin exposes the LMS7002M sensor as 'lms7_temp'.
  - The hot chips are on the card underside, which faces the riser carrier board. Heat must therefore leave through the card PCB to a top-side heatsink, plus forced air on both faces.
  
  Rough estimate (my calculation): a bare 22x80 mm card in still air (about 3500 mm2, h about 10 W/m2K) is about 28 K/W, so +110 K at 4 W. A passive card in a closed box will not work. With about 1.5 m/s of forced air it is about 7-9 K/W, or +30-35 K.
    - **Steps:**
      - Bench test first, open frame, in a 25 C room. Power the Q6A through J21 (see the power-entry fix) with the LimeSDR on the riser. Build the `limesdr-micro` branch of LimeSuiteNG, including drivers/linux/la9310_limesdr (DKMS), and load the module.
      - Power: put a DC power meter (or a shunt and DMM) in the 9 V J21 feed. Log five cases: Q6A idle; LimeSDR driver loaded and idle; RX-A at 61.44 Msps; RX-A+B at 30.72 Msps; each again with `stress-ng --cpu 8`. LimeSDR power is roughly the delta x 0.85 (assumed efficiency of the two bucks in the path).
      - Temperatures: run `limeDevice --full` before and after each run. While streaming, read the sensor from the recording process itself, because a second process cannot open the device: Python `sdr=SoapySDR.Device('driver=limesuiteng'); sdr.readSensor('lms7_temp')` every 10 s, logged next to the IQ file. Add an independent 10k NTC or thermocouple, Kapton-taped to the card top above the LMS7002M/LA9310.
      - Hardware: cut a cheap M.2 2280 SSD aluminium heatsink so it covers only the top-side area opposite the LMS7002M and LA9310 (check Lime's v1.2 top/bottom placement figures). Use a 1.0-1.5 mm gap pad rated at least 6 W/mK. Keep at least 3 mm clear around the X1/X2/X4 and J3-J6 MHF4 receptacles so the extraction tool fits. Raise the riser carrier on 3-4 mm standoffs inside the fan duct so air passes both faces of the card.
      - Optional, only after inspecting your riser: if the carrier has no copper under the card beyond the socket area (check against a bright light and with a continuity tester), cut a window about 25x20 mm under the LMS7002M/LA9310. Then stack 1.5 mm gap pad, a copper shim and the aluminium mid-plate.
      - Fan rule: copy Lime's own LimeSDR Mini 2.0 policy (fan on at 55 C, off at 45 C board temperature). Alarm and log at 70 C board temperature. That limit is my margin; Lime publishes none for the Micro.
      - Soak: run 60 min at 61.44 Msps in the closed case at about 35 C ambient, then repeat outdoors in sun.
    - **How to verify:** Pass criteria:
  - After 60 min at 35 C ambient in the closed case, TMP1075 'Board Temperature' settles at or below 65-70 C and LMS7002M at or below 75 C.
  - Zero overruns or lost packets reported by LimeSuiteNG.
  - RX DC/IQ calibration still succeeds after the soak (LimeSDR Mini users saw calibration failures when hot).
  - Measured LimeSDR power is 3-6 W. If it is above 6 W, enlarge the heatsink or increase airflow toward the 10 W target.
    - **Confidence:** medium
    - **Sources:**
      - https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/overview.html
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro (src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp, cli/limeDevice.cpp, plugins/soapysdr/Settings.cpp)
      - https://myriadrf.org/projects/limesdr-mini-2-0/reference/v2.4/tempsensor.html
      - https://discourse.myriadrf.org/t/limesdr-mini-thermal-pad/3132
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
  2.
    - **Problem:** Nobody has reported using the ADT-Link R44SF M.2-to-M.2 riser on an ARM host. Retention of its male end in the Q6A's 2230-only slot is unverified, and ARM hosts are known to fail enumeration occasionally with adapters.
    - **Proposed fix:** Fix retention with a printed clamp. Remove known Qualcomm-host risks (ASPM/L1SS, BAR space), then qualify the link with error counters and a boot-loop test. Keep Gen2 as a fallback.
  
  Facts checked:
  - The Q6A has only a 2230 standoff: an SMT nut at about (12.3, 12.2) mm from the left/HDMI-edge corner, per Radxa DXF/STEP v1.21.
  - The socket (APCI0107) spans x 1.4-23.3 mm and is 5.5 mm tall.
  - ADT's drawing shows the male end is about 21.2 mm to the cable start, with a 3.8 mm stack (3 mm FR4 pad). So the male board ends about 10 mm short of the nut: no screw retention.
  - The J21 3-pin header (8.5 mm tall, x 16.4-24.1) and the 4.7 mm standoff sit in the cable path.
  - In mainline pcie-qcom, sc7280-class controllers (cfg_1_9_0) run qcom_pcie_host_post_init_2_7_0, which enables all ASPM states including L1 substates on downstream devices.
  - pcie1's 32-bit MMIO window is 0x40300000 + 0x1fd00000 (about 509 MB, kodiak.dtsi). The LA9310 driver says BAR0 defaults to 256 MB, so it fits only at 0x50000000.
    - **Steps:**
      - Retention: print an ASA/PETG clamp bar. Fix it with an M2 screw into the 2230 SMT nut, reaching about 12 mm toward the socket, and press the riser's FR4 pad down through 1 mm EPDM or silicone foam. Fold the cable 90 degrees upward at least 5 mm after the FR4 pad so it clears the standoff, D19 and J21. Never put the cable under tension (ADT warning).
      - Baseline without the riser: plug the LimeSDR straight into J13 with the 2280 tail supported on a block. Power via J21. This separates host or driver problems from riser problems.
      - For bring-up, add `pcie_aspm=off` to the kernel command line. The kernel's __pci_enable_link_state honours aspm_disabled, so qcom's forced ASPM is skipped. Per-device alternative: write 0 to /sys/bus/pci/devices/<BDF>/link/{l0s_aspm,l1_aspm,l1_1_aspm,l1_2_aspm}.
      - Enumeration and BAR check:
  - `lspci -nn -d 1957:` and `lspci -nn -d 2058:`. Driver IDs are 1957:1c10, 1957:1c12 and 2058:001d.
  - `sudo lspci -vv -s <BDF> | grep -E 'LnkCap|LnkSta|Region'`. Expect LnkSta 8GT/s x1 and Region 0 = 256M assigned.
  - `dmesg | grep -iE 'BAR|no space|la9310'`.
      - Error counters: these work even if the AER interrupt is not wired on this DWC host.
  - Clear: `sudo setpci -s <BDF> ECAP_AER+0x10.L=0xffffffff` and `ECAP_AER+0x04.L=0xffffffff`, on both the endpoint and the root port.
  - Stream 60 min: `limeConfig --initialize --samplerate 61.44e6 --rxen 1 --rxlo 1700e6 --rxpath LNAW`, then `limeTRX --time 3600000 -o /data/t.iq`.
  - Re-read `lspci -vvv` CESta/UESta.
  - If present, check /sys/kernel/debug/pcie@1c08000/link_transition_count.
      - Boot loop: a systemd oneshot appends `lspci -d 1957: -d 2058:` plus LnkSta to a log, then reboots. Run 50 warm reboots and 20 cold power cycles (switch off the 9 V feed).
      - If you see errors or failed boots, force Gen2 at runtime on the root port: `setpci -s <RP> CAP_EXP+0x30.w=0x2:0xf; setpci -s <RP> CAP_EXP+0x10.w=0x20:0x20` (sets the target speed, then retrains). Make it permanent with a DT overlay `&pcie1 { max-link-speed = <2>; };`. Gen2 x1 gives about 400 MB/s usable, enough for one RX at 61.44 Msps I16 (246 MB/s).
      - If the BAR0 'no space' message appears, keep pcie1 for the LimeSDR only (no switch). Shrinking BAR0 to 64 MB is commented out in la9310_pci.c because it can cause 'Imprecise bus access' faults, so treat it as a last resort only.
    - **How to verify:** Pass criteria:
  - 70/70 boots enumerate at 8GT/s x1 (or at 5GT/s if you chose Gen2).
  - CESta/UESta stay all-zero after a 60-min stream on both the root port and the endpoint.
  - No LimeSuiteNG overruns.
  - The clamp holds the card with the case shaken.
  - Running the same test without the riser gives an A/B comparison.
    - **Confidence:** medium
    - **Sources:**
      - https://www.adt.link/product/R44SF.html
      - http://www.adt.link/Uploads/download/ADT_R44SS%20dimension%2020200326.pdf
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_3d_stp_v1.21.zip
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_2d_dxf_v1.21.zip
      - https://github.com/torvalds/linux/blob/master/drivers/pci/controller/dwc/pcie-qcom.c
      - https://github.com/torvalds/linux/blob/master/drivers/pci/pcie/aspm.c
      - https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/qcom/kodiak.dtsi
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro/drivers/linux/la9310_limesdr/la9310_pci.c
  3.
    - **Problem:** Nobody has reported fitting a Q6A copper cooler or the Armor Case with a card or riser in the M.2 slot. The Q6A also has no fan header.
    - **Proposed fix:** Size the cooler from Radxa's STEP model. The Q6A has no fan header, but Radxa's own PoE-HAT fan overlay gives kernel-controlled fan PWM.
  
  Geometry I took from STEP v1.21 (origin at the left corner of the HDMI/USB-C edge):
  - SoC U1: x 38.9-50.9, y 28.0-42.0 mm.
  - LPDDR5 U2: x 38.4-53.4, y 14.4-26.8. Both are 1.0 mm tall.
  - M.2 socket/riser zone: x 1.4-23.3. The gap to the SoC is 15.6 mm.
  - Tall neighbours: HDMI (x 24.5-39.6, y <=9.7, 6.4 mm), audio jack (x 50-58, y <=11.4, 5.3 mm), 2x2 header (x 59-64, y 43.9-48.9, 7.5 mm), 40-pin header (y >=48.7, 9.65 mm).
  
  Result: a heatsink base inside x 26-58, y 12-43 mm (32x31 mm) clears all of these and stays at least 2.7 mm from the riser. A fan above it at 10 mm or more can overhang the riser's 3.8 mm stack.
  
  Fan control: the radxa-overlays file qcs6490-radxa-dragon-q6a-poe-hat.dtso defines pwm-gpio on tlmm GPIO 56 (header pin 33), a pwm-fan, and active trips at 60 C on the cpu0 and gpu zones.
    - **Steps:**
      - Print the top-layer DXF at 1:1. Lay the cooler (or its drawing) on it. Accept only a base inside the 32x31 mm keep-in; otherwise trim the base on the M.2 side.
      - For the stepped AliExpress copper cooler: paste on the SoC, the supplied pad on the LPDDR5. Mount with M2.5 screws and springs in the 58x49 mm holes. A forum user found wrong standoff placement leaves the block floating, so check contact with a paste imprint.
      - Copy the PoE-HAT overlay. Remove the w1 node. Fix the zone names: the file says 'cpu0-thermall' and 'olling-delay-passive', but kodiak.dtsi uses 'cpu0-thermal'. Lower the trips to 50 C. Compile with `dtc -@ -I dts -O dtb` and enable it with rsetup.
      - Wiring: header pin 33 drives a 2N7002 or AO3400 open-drain that pulls the PWM pin of a 4-pin 5 V fan (Noctua NF-A4x10 5V PWM) low. This stage inverts, which matches the overlay's GPIO_ACTIVE_LOW. Feed the fan from your own 5 V buck, not the header.
      - Duct order: intake, then the display back channel, then the LimeSDR, then the Q6A fins, then the exhaust. Coolest air goes to the most temperature-sensitive parts.
    - **How to verify:** 1. Put modelling clay on the riser male end and the SoC area, close the case and measure the imprint: at least 1 mm clearance.
  2. Run `stress-ng --cpu 8 --timeout 30m` with a LimeSDR stream. Watch `paste <(cat /sys/class/thermal/thermal_zone*/type) <(cat /sys/class/thermal/thermal_zone*/temp)`. CPU zones should stay at or below 80 C at 25 C ambient, with no frequency drop in scaling_cur_freq.
  3. Check that `cat /sys/class/thermal/cooling_device*/type` lists pwm-fan and that its cur_state rises at the trip.
    - **Confidence:** medium
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_3d_stp_v1.21.zip
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_2d_dimensions_v1.21.pdf
      - https://github.com/radxa-pkg/radxa-overlays/blob/main/arch/arm64/boot/dts/qcom/overlays/qcs6490-radxa-dragon-q6a-poe-hat.dtso
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/pin-gpio
      - https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
      - https://noctua.at/en/nf-a4x10-5v-pwm/specification
  4.
    - **Problem:** No measurements of RF emissions from the Q6A HDMI path or a higher-than-FHD panel near 137/145/435/740/1575/1700/2200 MHz.
    - **Proposed fix:** Pick a video mode whose pixel-clock harmonics avoid every band, shorten and shield the HDMI run, then measure with your own SDRs.
  
  Facts checked:
  - HDMI comes from a Radxa RA620 DP-to-HDMI bridge fed by 2 DP lanes of the USB-1 QMP combo PHY. The other 2 lanes go to the USB 3 Type-A port (Radxa vendor DTS).
  - Maximum output is 3840x2160@30 (297 MHz).
  - A May 2026 kernel patch caps RA620 link training at voltage-swing level 2.
  
  My harmonic scan up to 2.4 GHz, against 137-138, 144-146, 435-438, 739-750 (LNB IF), 1565-1586 (GNSS), 1690-1710 and 2200-2290 MHz:
  - 1920x1080@60 (148.5 MHz) is the worst. 5x = 742.5 is inside the LNB IF and 15x = 2227.5 is inside S-band. The fundamental is 2.5 MHz from the 2 m band and 3x = 445.5 is 7.5 MHz from 438.
  - 1920x1200@60 CVT-RB (154.0): 11x = 1694 is inside HRPT.
  - 2560x1440@60 RB (241.5): 7x = 1690.5 is at the HRPT edge.
  - 2560x1600@60 CVT-RB (268.5): every harmonic is at least 25 MHz clear (nearest 6x = 1611). At 270.5 MHz the clearance is at least 36 MHz.
  - 4K@30 (297): at least 72 MHz clear, but 30 Hz is sluggish.
  
  Broadband TMDS/DP noise cannot be tuned away; only shielding and measurement deal with it.
    - **Steps:**
      - Choose a native 2560x1600 panel, or one that accepts that mode. Find the connector name with `ls /sys/class/drm` (probably HDMI-A-1). Force the mode with the kernel argument `video=HDMI-A-1:2560x1600R@60` (R = CVT reduced blanking). Check the clock with `modetest -M msm -c` or /sys/kernel/debug/dri/0/state.
      - Optional: for 270.5 MHz, make a custom EDID detailed timing, check it with edid-decode, and load it via `drm.edid_firmware=HDMI-A-1:edid/q6a.bin` (include the file in the initramfs).
      - Never let it fall back to 1080p60. Many HDMI driver boards advertise 1080p as the preferred mode, so pin the mode in the kernel argument.
      - Hardware: keep the HDMI path as short as possible (rigid coupler or a 10-15 cm shielded cable). Put snap-on ferrites at both ends. Cover the display driver board and cable in copper tape soldered or bonded to the aluminium mid-plate. Route them on the opposite side from the RF bay.
      - Measure with a 50-ohm load on each SDR input, and then with a short whip inside the case. Example: `rtl_power -f 136M:147M:5k -g 40 -i 10 -e 600 on.csv`, repeated for 430-450 M, 735-755 M and 1.55-1.75 G, display on versus HDMI unplugged. Use LimeSDR+SDR++ (averaging) for 2.2 GHz. Look for lines at n x pclk.
      - If S-band shows broadband desense from the DP link: by my sinc^2 model, HBR2 (needed for 2560x1600@60) has about 9 dB more noise density at 2245 MHz than HBR. Test a mode that fits 2-lane HBR, for example 1920x1200 at 153 MHz (at least 5 MHz clear), and check in debugfs which link rate the msm DP driver actually trains.
    - **How to verify:** With the antenna and LNA connected:
  - Turning the display on or off changes the noise floor by less than 0.5 dB in each band.
  - No discrete spur inside any band is more than 3 dB above the floor.
  - The spurs you do see sit at the predicted n x pclk positions, which confirms the source.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/radxa/kernel/blob/linux-6.18.2/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
      - https://lkml.indiana.edu/2605.2/12737.html
      - https://www.sigidwiki.com/wiki/HDMI_RFI_Clock
      - https://www.rtl-sdr.com/using-a-hackrf-to-investigate-why-wifi-on-the-raspberry-pi-4-doesnt-work-when-running-hdmi-at-1440p/
      - https://www.usb.org/sites/default/files/327216.pdf
  5.
    - **Problem:** The effect of the Q6A Wi-Fi 6, USB 3.1 and the SoC on L/S-band reception inside one box is unmeasured.
    - **Proposed fix:** Put the gain at the antenna, shield the RF bay, turn off the internal emitters while receiving, and quantify the remainder with a noise-floor delta test.
  
  Facts checked:
  - Wi-Fi/BT is an FCU760K module (USB ID a69c:8d80, AIC8800D80) on port 4 of the on-board USB 2.0 hub. The three USB 2.0 Type-A ports, including the RTL-SDR's, share that hub.
  - USB 3 Type-A shares the QMP combo PHY with the DP lanes that feed HDMI.
  - Intel measured a 2.4 GHz noise floor raised by nearly 20 dB with a USB 3 HDD attached. Fully shielding the device cut it by about 12 dB.
  - Slot leakage (my calculation, 20log(lambda/2L)): at 2.25 GHz a 15 mm slot gives only about 13 dB, a 7 mm slot about 20 dB.
    - **Steps:**
      - Mount the L/S-band LNAs (25-30 dB gain) at the antenna feed. Internal pickup after the LNA then counts 25-30 dB less, referred to the antenna.
      - RF bay: a copper-clad FR4 box soldered on all seams around the LimeSDR and the riser's female end. Keep slots and gaps at or below 7 mm, or use spring fingers or overlapped copper tape. Bring the riser cable in through one short slot. Bond the SMA bulkheads to the plate.
      - Wi-Fi off while receiving: `rfkill block all`, plus a udev rule that deauthorises the module: `ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="a69c", ATTR{authorized}="0"`. Re-enable it between passes if needed, or use Ethernet. If Wi-Fi is never needed, leave its U.FL antennas unplugged.
      - Leave the USB 3 Type-A port empty (storage is UFS). If something must use it, use a USB 2.0-only cable or hub so the SuperSpeed pairs stay idle.
      - Test matrix: 50-ohm load on RX, then antenna+LNA pointed at cold sky. Toggle one at a time: Wi-Fi, USB 3 device, HDMI, backlight 10/100%, `stress-ng --cpu 8`, NPU inference, fan, charger. Record 1 MHz-bin averaged PSD at 1690-1710 and 2200-2290 MHz.
      - Fix whichever source exceeds the limit: add shielding, move it or switch it off. As a last resort change the video mode, per the HDMI fix.
    - **How to verify:** With the antenna and LNA connected, each source changes the in-band noise floor by less than 0.5 dB. The final check is an end-to-end decode: an HRPT or S-band pass decoded with SatDump reaches the same SNR as with the internal sources off.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/radxa/kernel/blob/linux-6.18.2/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://www.usb.org/sites/default/files/327216.pdf
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://community.libre.space/t/hf-noise-from-raspberypi-4/8302
  6.
    - **Problem:** Random reboots and stutter with the Radxa 256 GB Kioxia UFS module (THGJFGT1E45BAILB), noted as unresolved in the research.
    - **Proposed fix:** This is now fixed in Radxa's kernel.
  - Radxa PR #551 (merged 11 May 2026 into radxa/kernel linux-6.18.2, commit 559f4f9) adds UFS_DEVICE_QUIRK_PA_TACTIVATE (PA_TACTIVATE = 1 ms) for this Kioxia part.
  - The cause was failed hibernate (H8) exit at idle, not heat.
  - Users report no errors after the patch, about 1.0-1.3 GB/s single-stream read, about 1.9 GB/s queued read and about 0.5 GB/s write.
  - Deepin carries the quirk in core ufs_fixups.
  - Mainline ufshcd.c (master, checked Oct 2026) does not yet list this model. A non-Radxa kernel needs the one-line quirk.
    - **Steps:**
      - Identify the module: `cat /sys/class/scsi_device/*/device/model`.
      - On Radxa's Ubuntu image: `sudo apt update && sudo apt full-upgrade` to a linux-6.18.2 build dated after 11 May 2026.
      - On any other kernel, add `{ .wmanufacturerid = UFS_VENDOR_TOSHIBA, .model = "THGJFGT1E45BAILB", .quirk = UFS_DEVICE_QUIRK_PA_TACTIVATE },` to ufs_fixups[] in drivers/ufs/core/ufshcd.c. Kioxia parts use the Toshiba vendor ID there.
      - Stop-gap only: Radxa's keep-alive (a write to /tmp every 0.1 s) prevents H8. Alternatively buy a Samsung-based module, which Radxa found trouble-free.
      - Thermal watch: the DTS has a 'ufs-thermal' zone. Log it during long IQ writes so you can tell overheating apart from this bug.
    - **How to verify:** 1. Leave the system idle for 24 h with occasional bursts. `dmesg | grep -iE 'ufshcd.*(abort|reset|err)'` must stay empty.
  2. Run a sustained write larger than the SLC cache: `fio --name=iq --rw=write --bs=1M --size=60G --ioengine=libaio --iodepth=8 --direct=1 --filename=/data/fio.bin`. It should hold at least 300 MB/s for 56 MHz IQ (246 MB/s).
    - **Confidence:** high
    - **Sources:**
      - https://forum.radxa.com/t/ufs-random-reboots/30630?page=2
      - https://github.com/radxa/kernel/pull/551
      - https://github.com/torvalds/linux/blob/master/drivers/ufs/core/ufshcd.c
      - https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
  7.
    - **Problem:** Radxa gives no official input range for J21. A community answer says 3.6-16 V, while a full 4S pack reaches 16.8 V.
    - **Proposed fix:** The schematic settles it.
  - Sheet 30 (v1.21): J21 pin 1 (ADP12V_IN) and the USB-C path (CH224D PD sink, CFG1 = 24 kOhm, which requests 12 V) join one ADP12V rail.
  - That rail has an SMBJ15CA TVS (VRWM 15 V, VBR min 16.7 V, VC 24.4 V), 22 uF/16 V input capacitors, and an SY81012VDC buck (2.7-16 V input) to 4.2 V VPH_PWR.
  - Practical continuous maximum is therefore about 15 V. 16.8 V from a full 4S pack exceeds the TVS standoff, the 16 V capacitors and the regulator's limit.
  
  Fix: feed J21 from a regulated 9 V synchronous buck. 9 V stays in regulation across the whole 12.0-16.8 V pack range; 12 V would sag on an empty pack. The Q6A only needs 3.6-16 V; Radxa recommends at least 24 W for full USB/PCIe load.
    - **Steps:**
      - Buck: Pololu D36V50F9 (9 V, 5 A typical, 9.9-50 V input, $39.95, stock 'rationed'), or any sync buck rated at least 4 A.
      - Protection: a 5 A fuse at the pack and reverse-polarity protection (ideal-diode or P-FET). At J21, 470 uF low-ESR plus 10 uF ceramic, fed by a short twisted pair.
      - The J21 header is 8.5 mm tall and sits in the riser cable path. Desolder it and solder the wires to the pads from the bottom side, or fit a right-angle header.
      - Do not use the Q6A USB-C (J8) at all. The riser cable passes over it; cover it so nobody plugs in. Battery charging goes to the pack's own charger.
      - Double duty: the buck's EN pin is the master off switch (sleep draw about 10-20 uA per volt of VIN). A panel momentary switch between J21 PWR and GND is the Q6A power key.
    - **How to verify:** 1. With a 16.8 V pack, J21 reads 9.0 V +/-4%.
  2. Scope J21 during power-on and during load steps (stress-ng plus LimeSDR start): no overshoot above 10 V and ripple below 100 mV p-p.
  3. With the pack at 12.0 V, J21 is still 9 V.
  4. Logged input stays at or below about 30 W with no resets.
    - **Confidence:** high
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
      - https://www.diodes.com/part/view/SMBJ15CA
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
      - https://www.pololu.com/product/4094
  8.
    - **Problem:** The Q6A has exposed battery pogo pads (+, -, TS) on its underside, close to where the aluminium mid-plate and the UFS thermal pad will go.
    - **Proposed fix:** Assume the + pad is live.
  - Schematic sheet 37 ('PM7250 RESERVED') shows TP64/TP69 (3x6 mm) and TP70 (2x4 mm, BATT_THERM) on the PM7250B battery pins.
  - R7 (0 ohm, fitted) appears to tie VBATT_PWR to VPH_PWR_IN, the 4.2 V output of the 12 A SY81012 buck. A short to a grounded plate would load the main system rail.
  - The - pad may reach GND only through an unfitted 2 mOhm sense resistor (R24).
  - This is my reading of the schematic; measure before relying on it.
  
  Other bottom-side keep-outs from the STEP model: a 2-pin RTC-battery connector 3.7 mm deep, inductors L46/L47 2.9 mm deep, and through-hole pins.
    - **Steps:**
      - Power the board from J21 and measure + to -, and each pad to GND (J21 GND). Expect about 4.2 V on +.
      - In the plate, cut a window at least 2 mm larger than the pad group, positioned from the bottom DXF.
      - Cover the plate with an insulating sheet (0.25-0.4 mm polycarbonate, fish paper or two layers of 50 um Kapton), with windows only for the UFS thermal boss and the standoffs.
      - Use 6 mm M2.5 standoffs, or recess the plate. Make the UFS heat path an aluminium boss under the module plus a 0.5-1 mm pad, sized from the measured gap.
      - Bond the plate to GND at one standoff on purpose (chassis and shield). Check that nothing else touches.
    - **How to verify:** 1. DMM: plate to + pad is open (over 10 MOhm); plate to GND is a short at the intended bond only.
  2. Idle input current is the same before and after assembly.
  3. Inspect for pad imprint marks in the insulating sheet after a full tighten.
    - **Confidence:** medium
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_3d_stp_v1.21.zip
      - https://forum.radxa.com/t/question-about-the-three-pogo-pads-ts-on-the-back-of-dragon-q6a/30090
  9.
    - **Problem:** The board size is inconsistent: the Radxa drawing says 85x56 mm, while a review and the brief say 85x65 mm.
    - **Proposed fix:** Use 85.0 x 56.0 mm. Radxa's 2D drawing v1.21 shows it, and the bottom-layer outline in the DXF measures 85.01 x 56.00 mm.
  
  Mounting holes: 4x 3.5 mm on a 58 x 49 mm pattern, 3.5 mm from the edges (at x 3.5/61.5, y 3.5/52.5).
  
  Envelope from the STEP model:
  - Footprint about 88.3 x 58.9 mm including connector overhang: RJ45 +3.3 mm; HDMI 2.3 mm, audio 2.6 mm and USB-C 1.2 mm past the bottom edge.
  - Above the PCB: stacked USB-A 16.3 mm, RJ45 13.6, 40-pin header 9.65, J21 header 8.5, M.2 socket 5.5.
  - Below the PCB: up to 3.7 mm.
  - Total about 21.6 mm with the 1.6 mm PCB.
    - **Steps:**
      - Import radxa_dragon_q6a_3d_stp_v1.21 into CAD as the master model.
      - Size the battery bay and riser routing against the 88.3 x 58.9 mm envelope.
      - Measure the first board with calipers.
    - **How to verify:** Calipers on the delivered board: 85.0 +/-0.2 by 56.0 +/-0.2 mm, and the hole pitch is 58/49 mm.
    - **Confidence:** high
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_2d_dimensions_v1.21.pdf
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_2d_dxf_v1.21.zip
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_3d_stp_v1.21.zip
  10.
    - **Problem:** No data on sun load for a display of 1000 nits or more inside a closed printed case. High-brightness monitors have black-screen reports in direct sun.
    - **Proposed fix:** The blackout is LCD clearing: the liquid crystal turns isotropic when the cell overheats from solar and infrared load.
  - Vendors and patents say many commercial panels black out from about 60 C. High-temperature panels are rated to about 110 C.
  - Elo saw an unfilmed panel go black in a 4-hour sun test, and warns that an air gap behind a cover glass acts as a greenhouse.
  
  My rough budget for a 7-inch module (about 0.017 m2): about 15 W absorbed at 1000 W/m2 normal incidence, plus 4-6 W of backlight. Front-face cooling only (about 0.2 W/K) gives +75-115 K, which is certain blackout. Adding forced air on the back (about 0.5-0.75 W/K total) gives about +26-39 K, so about 60-75 C at 35 C ambient.
  
  The design therefore needs all of: a high-temperature panel, shade, an infrared-reflecting cover, airflow behind the panel, and backlight derating.
    - **Steps:**
      - Panel: require an operating spec of at least 70 C (industrial, wide-temperature). Ask the seller for the clearing point (Tni/TNI); reject 0-50 C consumer panels.
      - Front: an infrared-reflective (not absorptive) film or hot-mirror cover. Either no extra cover glass, or a vented gap; never a sealed air gap.
      - Shell: light-grey or white bezel. A slide-on hood that shades the panel when not being viewed.
      - Thermal separation: foam between the panel and the warm mid-plate. A 4-6 mm air channel behind the panel fed first by the fan duct.
      - Sensor: an NTC or DS18B20 on the panel back. Derate the backlight at 60 C (`ddcutil setvcp 10 <n>` if the board supports DDC/CI, otherwise a PWM pot) and warn on screen at 65 C.
    - **How to verify:** 1. Indoors: set a 500 W halogen floodlight to 1000 W/m2 with a solar power meter. Halogen is IR-rich, so this is conservative. Run 60 min at full backlight while logging panel-back temperature and watching for darkening.
  2. Repeat at July noon outdoors.
  3. Pass: no darkening, and the panel back stays at least 10 K below the panel's rated maximum.
    - **Confidence:** low
    - **Sources:**
      - https://elosupport.elotouch.com/hc/en-us/articles/31648421556247
      - https://elosupport.elotouch.com/hc/en-us/articles/31648633630743
      - https://patents.google.com/patent/US6211934B1/en
      - https://greyarro.ws/t/crystal-sky-monitor-screen-going-black/35877
  11.
    - **Problem:** No community insertion-loss or quality data for prom.ua or AliExpress MHF4-to-SMA pigtails. MHF4 is rated for about 30 mating cycles, and a bad plug can damage the SDR's receptacle.
    - **Proposed fix:** Treat the pigtails as fixed internal wiring and screen every one before it touches the SDR. Keep a known-good reference cable and the right tool.
  - Reference cable: Lime's own $6 MHF-4L to SMA(f) bulkhead.
  - Genuine alternative: Taoglas CAB.S225 (MHF4L to SMA(F) bulkhead, 150 mm, 1.13 mm). Avnet shows a 70-week lead time, and RS lists the gender inconsistently, so verify before ordering.
  - Tool: I-PEX 90435-001 MHF4 mating/unmating tool, EUR 15.89 at DigiKey, in stock.
    - **Steps:**
      - Buy about twice as many cheap 1.13 mm cables as you need. Inspect each plug under a 10x loupe: centre contact present, outer ring round, crimp intact. Check the SMA end is plain SMA, not RP-SMA.
      - NanoVNA open-end S11: round-trip loss should be about 2x (about 0.3 dB cable plus connector) at 2.2 GHz, i.e. about 0.6-1.0 dB. Reject anything over 1.5 dB, or with an impedance bump over 10 ohm in NanoVNA-Saver TDR.
      - Mate vertically with the tool or a flat pusher until it clicks. Unmate only with the tool, never by pulling the cable.
      - Strain relief: a printed clip 5-10 mm from each plug. The panel bulkhead nut torque must never reach the MHF4.
      - Log mating cycles per port. Never use MHF4 as a user connector.
      - Functional check: a broadband noise source with a 20 dB pad feeds each port, first through the Lime reference cable and then through the cheap one. Compare received power at 435, 1700 and 2250 MHz.
    - **How to verify:** Each installed cable is within 0.5 dB of the Lime reference cable on the noise-source test, and the plug stays seated after a shake test.
    - **Confidence:** medium
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
      - https://www.digikey.es/en/products/detail/i-pex/90435-001/25819261
      - https://www.taoglas.com/product/cab-s225-i-pex-mhf4lhsc-comp-to-150mm-1-13mm-coax-black-cable-smaf-bulkhead-straight/
      - https://www.avnet.com/americas/product/taoglas/cabs225/evolve-118405069/
      - https://prom.ua/Ipex-mhf4-gnezdo-sma.html
      - https://discourse.myriadrf.org/t/plug-in-u-fl-pigtails/2620
  12.
    - **Problem:** The BATC forum (Portsdown 4 + LimeSDR Mini thermal and noise experience) was unreachable (HTTP 503 again in Oct 2026).
    - **Proposed fix:** Use the other sources that are reachable. Their lesson matches this design: a closed SBC+SDR+display box needs active cooling on both the SBC and the SDR.
  - BATC search snippet (unverified): the Pi 4 running BandViewer passed 75 C with an over-temperature warning after about 5 minutes, and the maintainer advised a heatsink or fan.
  - LimeSDR Mini thermal-pad thread: about 50 C uncooled, 41.8 C with a copper plate to the lid, 60 to 38 C with a small 5 V fan, and TX calibration failing when hot.
  - Lime's Mini 2.0 has an on-board fan header with 55/45 C hysteresis.
  - BATC wiki: Portsdown's Lime issues were mostly USB power and connector strain. Both are avoided here because the Lime sits on PCIe and the SMA panel is strain-relieved.
    - **Steps:**
      - Adopt the 55/45 C SDR fan rule and the at least 50 C CPU fan trip from the fixes above.
      - Retry forum.batc.org.uk viewtopic p=29854 later, or ask on the BATC forum for Portsdown 4 internal temperatures with a fan.
    - **How to verify:** Your own soak test (first fix) replaces this evidence.
    - **Confidence:** medium
    - **Sources:**
      - https://forum.batc.org.uk/viewtopic.php?p=29854
      - https://wiki.batc.org.uk/Using_LimeSDR_with_Portsdown
      - https://discourse.myriadrf.org/t/limesdr-mini-thermal-pad/3132
      - https://myriadrf.org/projects/limesdr-mini-2-0/reference/v2.4/tempsensor.html
- **Residual risks:**
  - LA9310 BAR0 defaults to 256 MB. pcie1's 509 MB window has exactly one aligned slot for it. Adding a PCIe switch or a second device on pcie1 could make BAR assignment fail.
  - LimeSDR thermal and power figures stay unknown until measured. The riser carrier blocks the bottom-side heat path, and Lime publishes no maximum temperature for the Micro.
  - The msm DP driver may train at HBR2 regardless of mode. By my model that puts about 9 dB more broadband noise density at 2.2 GHz than HBR. The RA620 bridge also has known link-training quirks (swing level 2), and its emissions are unmeasured.
  - Radxa's PoE-HAT overlay contains typos ('cpu0-thermall', 'olling-delay-passive') and may change. The header pin 33 = GPIO_56 mapping came from a flattened docs table; check it with gpioinfo.
  - The Kioxia UFS quirk is only in Radxa's and Deepin's kernels, not mainline. A distro kernel update could drop it.
  - The J21 limit (about 15 V) and the live pogo '+' pad come from my reading of the schematic, not from a Radxa spec. Measure both before assembly.
  - The sun-load estimate is accurate to perhaps +/-50%. Panel datasheets rarely state the clearing point, so blackout risk remains until tested at noon.
  - Supply risk: the Pololu D36V50F9 is 'rationed', Taoglas CAB.S225 shows a 70-week lead time, and ADT-Link stock and shipping to Ukraine are unverified.
  - Mainline Linux has no HDMI/RA620 description for the Q6A, so display output depends on Radxa's vendor kernel.
  - The LimeSDR RX-B port is labelled X4 in the v1.2 overview but X3 in the setup table. Check the silkscreen before wiring the SMA panel.
  - Weight and handling (about 1.0-1.2 kg) and magnetometer bias from the fan and battery currents are not addressed here.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e6b8e5e2-124`_

- **Component:** Mechanical, thermal and enclosure: M.2 riser, MHF4-to-SMA pigtails and SMA panel, Q6A and LimeSDR Micro cooling, case, RF shielding, ergonomics, size and weight
- **Recommendation holds:** так
- **Issues:**
  1.
    - **Claim:** LimeSDR Micro cooling: cut an M.2 SSD heatsink to cover the top-side area opposite the LMS7002M and LA9310, and push forced air over both faces of the card.
    - **Problem:** Lime's v1.2 drawings put the LMS7002M about 50-61.5 mm from the edge connector on the bottom side. The top side directly opposite it carries the RF front-end: RF switch IC3, baluns and matching parts next to X2/X4. Metal and pads there can detune the RF; Lime staff warned about this on the LimeSDR Mini. Heat that has to cross the card PCB to reach a top-side heatsink also conducts poorly. The same fix list also asks for a sealed, soldered copper-clad RF bay with slots of 7 mm or less, which cannot also carry forced air across both faces of the card.
    - **Correction:** Take the heat straight off the package tops, which face the riser's female board. The R4F female board is mostly empty FR4 with 2230/2242/2260 holes and a 2280 standoff, so cut a window of about 26x20 mm under the region 36-62 mm from the edge. Raise an aluminium pedestal from the mid-plate through the window and add a 0.5-1.5 mm gap pad (at least 6 W/mK) onto the LMS7002M and LA9310. Fit external fins on the plate in the fan path, so the RF bay stays sealed. Add a small top-side heatsink only over the LA9310/digital area (37-45 mm from the edge). Keep 3 mm clear of the MHF4 receptacles and away from the RF area at the far end.
    - **Source:** https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/overview.html (LimeSDR-Micro_M.2_2280_v1.2_components_top/bot.png); https://discourse.myriadrf.org/t/limesdr-mini-thermal-pad/3132; https://www.adt.link/product/R44SF.html
  2.
    - **Claim:** Internal heat is about 17-25 W, and the display adds 'several W'.
    - **Problem:** The user now wants a panel of at least 1000 nits, higher than FHD. Panels like that draw far more: the BenQ PVS7 (7-inch, 1920x1200, 2000 nits) is 10 W typical and 18 W maximum, and an IMA 7-inch 1920x1200 2000-nit unit is 16 W maximum. Even a 1000-nit 1024x600 module draws 4.5-7.8 W. About 15 W of sun on the display face comes on top of that.
    - **Correction:** Plan for 25-35 W of internal heat plus solar load. Battery runtime from 72 Wh is then about 2-3 h. Active cooling is required, not optional. Derate the backlight with temperature.
    - **Source:** https://www.benq.eu/en-eu/monitor/creative-pro/pvs7/spec.html; https://www.litemax.com/product-detail/0765-I-durapixel-industrial-display/
  3.
    - **Claim:** A single 40 mm NF-A4x10 fan in series (intake, display back, LimeSDR, Q6A fins, exhaust, or the reverse order).
    - **Problem:** The NF-A4x10 gives 8.9 m3/h at only 1.95 mm H2O. At 25-35 W, air rises about 10-14 K even at free-air flow (P/(rho*cp*V)); behind meshes, a fin stack and ducts the flow roughly halves, so the last part in line sees air 20 K or more above ambient. Air that has passed the sun-loaded display preheats everything after it.
    - **Correction:** Use two parallel paths:
  - (a) The proven setup: a 30-40 mm fan blowing straight down onto the Q6A stepped copper fin stack.
  - (b) A separate small 5 V radial blower (4010/5015 class, unverified price $3-5) through the 4-6 mm channel behind the display and over the external fins of the mid-plate, which carry the LimeSDR heat.
  The LimeSDR cools by conduction, so its shielded bay needs no airflow.
    - **Source:** https://noctua.at/en/nf-a4x10-5v-pwm/specification; https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
  4.
    - **Claim:** Size about 200-205 x 130-135 x 42-48 mm and 1.0-1.2 kg. The display is modelled as a Raspberry Pi Touch Display 2 (about 250 g). Heatsinks, fan and plate together weigh 80-110 g.
    - **Problem:** The Pi Touch Display 2 is a DSI, 720x1280, non-sunlight-readable panel, so it is not usable here and is the wrong weight and power class. A 2 mm aluminium plate of 200x130 mm alone weighs about 140 g (52 cm3 x 2.7 g/cm3). The stack is thicker than estimated: front wall 2.5 + panel 5-6 + air channel 4-6 + plate 2 + 6 mm standoffs + 1.6 mm PCB + 10-13 mm fin stack + 10 mm fan + back wall 2.5, about 50-55 mm. Radxa's STEP model confirms 16.3 mm stacked USB-A and 3.7 mm of parts below the PCB.
    - **Correction:** With a bare high-brightness panel plus an HDMI driver board, expect about 205-215 x 130-140 x 50-55 mm and 1.2-1.4 kg. With a cased field monitor (520-700 g) it is 1.4-1.6 kg. A 5.7 mm low-profile copper cooler with a side-blowing blower can bring the thickness to about 45 mm.
    - **Source:** https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_3d_stp_v1.21.zip (parsed); https://www.benq.eu/en-eu/monitor/creative-pro/pvs7/spec.html
  5.
    - **Claim:** The 4x21700 pack as a detachable 2x2-cell grip, about 46x46x145 mm.
    - **Problem:** The geometry is wrong. Four 21700 cells in a 2x2 bundle measure about 44x44x72 mm; a 46x46x145 mm block holds eight cells.
    - **Correction:** Two rows of two cells end to end, about 46x25x150 mm, makes a good flat grip. A 2x2 block is about 46x46x80 mm with the BMS.
    - **Source:** 21700 cell = 21 x 70 mm (standard format)
  6.
    - **Claim:** R44SF dimensions: male end 21.2 mm with a 3.8 mm stack, and an 80 mm female board with M2 screws and nuts.
    - **Problem:** These figures come from the R44SS drawing, which is a male-to-male jumper (a 21.2 mm male end plus an 80 mm male board), not the R44SF. The R44SF photo and schematic show a short R4S male end with an FR4 clamp pad and a separate R4F female board carrying a socket, 2230/2242/2260 holes and a 2280 standoff. The female socket height, and so the gap under the card, is not published.
    - **Correction:** The male end is probably the same R4S board. Confirm the female socket height and pad clearance with the ADT_R44_3D.zip STEP before designing the pedestal. The schematic confirms that PERST#, CLKREQ#, PEWAKE#, REFCLK and 3.3 V are carried, so the XTRX 'missing PERST' failure does not apply to ADT. Check this point on any generic FPC riser.
    - **Source:** https://www.adt.link/product/R44SF.html; http://www.adt.link/Uploads/download/ADT_R44SF%20schematic%2020191105.pdf; http://www.adt.link/Uploads/download/ADT_R44SS%20dimension%2020200326.pdf
  7.
    - **Claim:** Bench baseline: plug the LimeSDR straight into J13 with the tail supported ('even 2280 devices can be just plugged in').
    - **Problem:** From Radxa STEP v1.21 (my parse): the 2230 standoff is 4.7 mm tall at about X 9.8-14.8, Y 10.8-13.3, which sets the card plane at about 4.7 mm. LimeSDR bottom-side parts (IC16 clock buffer and IC27 LDO, about 24-30 mm from the edge) can land on that standoff. The LA9310 (37.5-45.4 mm from the edge) would sit about 0.4 mm above the USB-C shell (top at 3.10 mm). The J21 header (8.5 mm) collides outright. An SSD is single-sided; the LimeSDR is not.
    - **Correction:** Before any direct-plug test, measure with calipers. Put Kapton on the standoff, or confirm the bottom-side parts clear it. Remove or move the J21 header first. Never use direct plug in the final build.
    - **Source:** https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_3d_stp_v1.21.zip; https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/overview.html
  8.
    - **Claim:** HDMI mode: use 2560x1600 CVT-RB at 268.5 MHz to keep pixel-clock harmonics out of the bands.
    - **Problem:** The harmonic arithmetic is correct (I re-ran it: nearest 6x = 1611 MHz, 25 MHz clear). But most sunlight-readable 7-inch panels are 1920x1200, and every standard timing for that resolution hits a band:
  - 148.5 MHz: 5x = 742.5 MHz (LNB IF) and 15x = 2227.5 MHz (S-band).
  - 154.0 MHz CVT-RB: 11x = 1694 MHz (HRPT).
  The panel's own HDMI-to-MIPI/eDP bridge clocks are not covered at all. FPV-style unshielded HDMI FFC ribbons radiate broadband TMDS noise.
    - **Correction:** For a 1920x1200 panel, force a custom pixel clock of about 166 MHz (60 Hz, Htotal about 2240, Vtotal about 1235). It has at least 19 MHz clearance to all bands and needs 3.98 Gb/s, which fits 2-lane HBR (4.32 Gb/s). An alternative is CVT standard blanking at 193.25 MHz (19 MHz clear), but that needs HBR2. Use a shielded micro-coax HDMI cable, not an FFC ribbon, and measure the panel's own spurs.
    - **Source:** https://www.sigidwiki.com/wiki/HDMI_RFI_Clock; my own harmonic scan up to 2.4 GHz
  9.
    - **Claim:** Power J21 from a Pololu D36V50F9 9 V buck ($39.95).
    - **Problem:** The 9 V choice is right: the schematic shows an SMBJ15CA TVS, a CH224D PD sink and an SY81012 buck on the ADP12V rail, so 16.8 V from a full 4S pack is too high. But Pololu lists the part as 'Rationed', and it costs $40 plus shipping to Ukraine.
    - **Correction:** A cheaper choice is a Mini560 fixed-9 V synchronous buck (about 11-20 V in, 5 A nominal, about 500 kHz, 29x18 mm, about $2-4, unverified). It covers 12.0-16.8 V and the Q6A's 10-15 W. Add an LC pi-filter and a ferrite on its output. Keep the Pololu as the premium option.
    - **Source:** https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf; https://www.pololu.com/product/4094; https://hubtronics.in/dc-dc-power-converter-modules/mini560-9v-5a-step-down-stabilized-module
  10.
    - **Claim:** Noctua NF-A4x10 5V PWM runs 0-5000 rpm and is speed-controlled through the PoE-HAT pwm-gpio overlay.
    - **Problem:** Scan UK lists it at 1000-5000 rpm, so it does not stop at 0 %. The overlay sets a 1 ms period (1 kHz), far below the 21-28 kHz PC fan-PWM spec, so expect ticking and coarse steps. Running pwm-gpio at 25 kHz costs CPU. Rozetka (Ukraine) stocks only the 12 V NF-A4x10 PWM (1019 UAH), which will not run correctly on 5 V.
    - **Correction:** Order the 5 V version from the EU (Dateks about EUR 26 incl. VAT), or use a cheap 5 V fan with on/off 60/50 C hysteresis through an AO3400. Test noise before relying on 1 kHz PWM.
    - **Source:** https://www.scan.co.uk/products/40mm-noctua-nf-a4x10-5v-pwm-beige-brown-7-blade-sso2-bearing-1000-5000rpm-52cfm-airflow-196db-4-pin; https://github.com/radxa-pkg/radxa-overlays/blob/main/arch/arm64/boot/dts/qcom/overlays/qcs6490-radxa-dragon-q6a-poe-hat.dtso; https://hard.rozetka.com.ua/ua/373960119/p373960119/
  11.
    - **Claim:** Budget option: a PETG shell is fine if the device is not left in direct sun.
    - **Problem:** The brief says the device is used outdoors, often in sunlight, and the user wants a 1000-nit display for that reason. PETG softens at about 75-80 C. ASA filament costs about the same.
    - **Correction:** Use light-coloured ASA in the budget build too. The saving from PETG is about $0-3.
    - **Source:** https://forum.prusa3d.com/forum/english-forum-general-discussion-announcements-and-releases/my-print-melted-on-my-window-sill
- **Forum and fix assessment:** Most of the research holds up under independent checks. I verified these points:
  - The Q6A board is 85.0 x 56.0 mm (Radxa 2D drawing v1.21).
  - J13 is a top-side M.2 socket at X 1.4-23.3, Y 37.9-46.1 mm, 5.5 mm tall.
  - The 2230 standoff is 4.7 mm tall at about 12 mm from the HDMI edge. J21 is 8.5 mm tall and USB-C is 3.1 mm tall, both under the 2280 path (my parse of STEP v1.21).
  - The SoC is at X 38.9-50.9, Y 28-42 and the LPDDR5 at X 38.4-53.4, Y 14.4-26.8, so the 32x31 mm heatsink keep-in is valid.
  - The LimeSDR LMS7002M, LA9310 and switchers are on the bottom side (Lime v1.2 drawings).
  - LimeSDR M.2 Basic is $249 / $299 with GNSS, new orders ship Dec 15 2026, and Lime's MHF4L-SMA bulkhead cable is $6 plus $18 shipping.
  - Lime asks for cooling rated at 10 W or more; Zack's '~4 W' is confirmed (Aug 24 2026). No measured Micro temperatures exist yet.
  - The ADT R44SF exists at $19 for 5 or 10 cm on adt.link (a Newegg snippet shows $29.99 for 10 cm), is PCIe 3.0 x4 tested, and carries PERST#, CLKREQ# and REFCLK. Its male end has no 2230 screw, so it needs a clamp.
  - pcie1 has a 32-bit window of 0x1fd00000 at 0x40300000, so the 256 MB BAR0 fits in exactly one aligned slot.
  - Radxa kernel PR #551 (Kioxia UFS PA_TACTIVATE quirk) was merged on May 11 2026.
  - The PoE-HAT overlay uses pwm-gpio on GPIO 56 with a 60 C trip and contains the 'cpu0-thermall' typo.
  - The Calin23 fan script exists and was tested on Armbian 25.11.2.
  - The schematic contains an SMBJ15CA, CH224D and SY81012VDC on ADP12V, and the M.2 3.3 V rail comes from a 4 A ETA3521, so the slot can supply the LimeSDR.
  - MHF4 is rated for 30 mating cycles (DigiKey, I-PEX PRS-1745).
  - The setup page names RX-B 'X3' while the v1.2 overview names it 'X4'.
  
  The proposed fixes are mostly sound: 9 V into J21, the clamp and acceptance tests for the riser, pcie_aspm=off, Gen2 fallback, the pogo-pad insulation window, Wi-Fi rfkill, the pixel-clock plan, and branded or screened pigtails.
  
  Three fixes need correcting:
  - **LimeSDR cooling:** the top-side heatsink would sit over RF matching parts. Cool the chips from the bottom through a window in the female board instead.
  - **Airflow:** a single series duct cannot cool a sealed RF bay; use two paths and conduction.
  - **Heat budget and enclosure:** the high-nit display was underestimated, which makes the heat budget, size and weight figures optimistic.
  
  The forum record still has no Q6A + PCIe SDR or R44SF-on-ARM report, so the riser acceptance test (70 boots, AER/CESta counters, 60-minute stream) remains mandatory.
- **Final recommendation:**
  - **Name:** Hybrid build: light-grey ASA shell, 2 mm aluminium mid-plate (chassis, ground, shield wall, heat spreader), ADT-Link R44SF 5 cm riser with a windowed female board, conduction-cooled LimeSDR, copper fin stack plus fan on the Q6A, separate blower for the display channel, 9 V buck into J21, shielded RF bay with 1.13 mm MHF4-SMA bulkheads, captured 1/4"-20 nut in the plate
  - **Price:** About $130-200, excluding the SDR, board, display and cells:
  - R44SF 5 cm: $19 plus shipping (shipping not verified).
  - Two Lime MHF4L-SMA cables: $12, bundled with the SDR order; or prom.ua RF1.13 cables at 63 UAH each, screened with a NanoVNA.
  - I-PEX 90435-001 MHF4 tool: about EUR 16.
  - Q6A stepped copper cooler: $17-30 (AliExpress, intermittent stock), or a fin stack plus NF-A4x10 5V PWM (about EUR 26 in the EU).
  - 5 V blower: $3-5 (unverified).
  - Aluminium plate, pedestal and gap pads: $15-25 (unverified).
  - ASA filament, 0.4 kg: about $8-12.
  - Copper-clad FR4 and tape: about $5.
  - SMA bulkheads: $8-15.
  - 9 V buck: Mini560, about $3 (unverified), or Pololu D36V50F9 at $39.95 (rationed).
  - IR-reflective film and printed sun hood: $5-10.
  - Strap, buttons, EC11 encoder and TPU bumpers: $10-20.
  - **Sources:**
    - https://www.adt.link/product/R44SF.html
    - http://www.adt.link/Uploads/download/ADT_R44SF%20schematic%2020191105.pdf
    - https://www.crowdsupply.com/lime-micro/limesdr-micro
    - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
    - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/overview.html
    - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_2d_dimensions_v1.21.pdf
    - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_3d_stp_v1.21.zip
    - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
    - https://github.com/radxa-pkg/radxa-overlays/blob/main/arch/arm64/boot/dts/qcom/overlays/qcs6490-radxa-dragon-q6a-poe-hat.dtso
    - https://github.com/Calin23/dragon-q6a-fan-control
    - https://github.com/radxa/kernel/pull/551
    - https://www.pololu.com/product/4094
    - https://www.benq.eu/en-eu/monitor/creative-pro/pvs7/spec.html
    - https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
  - **Why:** The architecture survives scrutiny, with corrected details.
  - **Riser:** The R44SF is the only riser found with a published Gen3 x4 test and confirmed sideband wiring. It is needed because direct plug collides with J21 and possibly the 2230 standoff, and puts the LA9310 0.4 mm above USB-C.
  - **SDR cooling:** The LimeSDR's hot chips face the female board. A window plus pedestal to the plate is the only heat path that avoids metal over the RF front-end on the top side, and it keeps the RF bay sealed.
  - **Airflow:** The Q6A keeps the proven fin-stack-plus-fan setup (55-80 C in forum and review reports). The display and plate get their own blower path, because a high-nit panel adds 6-18 W and fights sun load.
  - **Power:** 9 V into J21 stays below the 15 V TVS limit across 12.0-16.8 V. The Q6A USB-C stays unused (cover it).
  - **Shell:** ASA in a light colour survives sun.
  - **Tripod mount:** A captured nut or a thread tapped in the plate replaces heat-set inserts.
  - **Expected result:** about 205-215 x 130-140 x 50-55 mm and 1.2-1.4 kg, so it needs a strap and a boom/tripod mount.
- **Final budget option:**
  - **Name:** ASA print (not PETG) + generic AliExpress M.2 M-key FPC extender (validate it; check that PERST#/CLKREQ#/REFCLK are wired) + Pi-style 30-40 mm heatsink/fan on 5 V with on/off hysteresis + windowed riser board and aluminium-strip pedestal for the LimeSDR + soldered copper-clad FR4 shields + prom.ua RF1.13 MHF4-SMA pigtails + Mini560 9 V buck
  - **Price:** About $45-75 total (several items unverified):
  - Generic riser: $2-9.
  - Pi-style heatsink and fan: $3-6.
  - AO3400 MOSFET: under $1.
  - Pigtails: 2-4 x 63 UAH.
  - ASA filament: $8-12.
  - Aluminium strip and a gap pad: $5-8.
  - FR4 and copper tape: about $5.
  - Mini560 buck: about $3.
  - SMA bulkheads and a captured 1/4"-20 nut: $10-15.
  - Strap: about $5.
  - **Why:** It keeps the same safe architecture: SDR on a riser, conduction-cooled LimeSDR, fan on the Q6A, sealed RF bay, 9 V into J21. It cuts about $80-120 from the main build. ASA costs about the same as PETG and survives sun. Upgrade to the $19 ADT R44SF if the cheap riser fails 70-boot enumeration or shows non-zero CESta/UESta after a 60-minute stream.
- **Known problems and fixes to apply:**
  - Riser retention: the R44SF male end (about 21 mm) ends about 9 mm short of the Q6A 2230 standoff (4.7 mm tall, about 12 mm from the HDMI edge). Print an ASA clamp bar screwed into that standoff (M2) that presses the FR4 pad down through 1 mm foam. Fold the cable 90 degrees upward within about 5 mm after the pad. No case surface may press on the flex.
  - J21 header (8.5 mm) and USB-C (J8) lie in the 2280/riser path. Desolder J21 and wire 9 V/GND/PWR from the bottom pads with a twisted pair, 470 uF plus 10 uF at the board. Tape over J8 and never feed USB-C and J21 at the same time.
  - Power: 4S (16.8 V full) exceeds J21's SMBJ15CA TVS (15 V standoff). Feed J21 at 9 V through a synchronous buck (Mini560 9 V or Pololu D36V50F9) with an LC filter. Fit a 5 A fuse and reverse-polarity protection at the pack.
  - LimeSDR cooling: the hot chips are on the bottom side, facing the riser board. Cut a window in the R4F female board under the region 36-62 mm from the edge (check first for traces). Add an aluminium pedestal from the mid-plate and a 0.5-1.5 mm gap pad of at least 6 W/mK. Fit plate fins in the blower path. Put no metal over the top-side RF area (IC3 and the baluns near X1/X2/X4). Log 'Board Temperature' (TMP1075) and lms7_temp; fan rule 55/45 C, alarm at 70 C. Soak 60 min at 61.44 Msps.
  - Q6A cooling: use a stepped copper block (paste on the SoC, pad on the LPDDR5, check with an imprint) inside the 32x31 mm keep-in X 26-58, Y 12-43 mm, plus a 30-40 mm 5 V fan. Control it with the fixed PoE-HAT overlay (GPIO 56, 'cpu0-thermal' spelling corrected, trip 50 C) through an AO3400/2N7002, or with the Calin23 script, or with plain on/off at 60/50 C. Expect 1 kHz PWM ticking on Noctua fans.
  - Display heat: a panel of 1000 nits or more adds 6-18 W. Fit a 4-6 mm air channel behind the panel fed by its own blower, an IR-reflective film (no sealed air gap), a light bezel and a slide-on sun hood. Put an NTC on the panel back and derate the backlight at 60 C. Require a panel rated to 70 C or more.
  - Bring-up acceptance for the riser:
  - pcie_aspm=off during bring-up.
  - lspci LnkSta 8GT/s x1 and BAR0 256M assigned.
  - 50 warm and 20 cold boots, all enumerating.
  - Clear AER CESta/UESta, stream 60 min, then re-read; they must stay zero.
  - Fallbacks: setpci Gen2 retrain, then the DT max-link-speed = <2>.
  - HDMI RFI:
  - 2560x1600 panel: pin 2560x1600R@60 (268.5 MHz) with video= on the kernel command line.
  - 1920x1200 panel: use a custom ~166 MHz EDID timing.
  - Never fall back to 1080p60 (742.5 MHz and 2227.5 MHz harmonics).
  - Use a shielded micro-coax HDMI cable (not an FFC ribbon) with ferrites, routed away from the RF bay.
  - Measure on/off noise-floor deltas in every band.
  - RF bay: solder copper-clad FR4 on all seams, slots of 7 mm or less, and bond the SMA bulkheads to the plate. Keep the RTL-SDR in its own aluminium case grounded to the plate, with a short SMA jumper. LNAs go at the antennas. rfkill Wi-Fi/BT and leave USB 3 empty during L/S-band work.
  - Pigtails: 1.13 mm, 75-100 mm long, plain SMA (not RP-SMA). Screen each one with a NanoVNA (reject over 1.5 dB round trip at 2.2 GHz). Mate and unmate only with the I-PEX 90435-001 tool. Add strain-relief clips; 30 mating cycles maximum. Do not bring TX X1 to the panel. Check the X3/X4 silkscreen for RX-B.
  - Mid-plate: cut a window over the Q6A bottom battery pogo pads and add an insulating sheet (+ pad assumed live at about 4.2 V). Use 6 mm M2.5 standoffs (bottom parts reach 3.7 mm). Bond the plate to GND at one standoff. Give the UFS module a pad to a boss on the plate.
  - Tripod/boom mount: a captured 1/4"-20 nut, or a thread tapped in the aluminium plate. Do not use heat-set inserts alone for a device of about 1.3 kg on a boom.
  - IMU: mount the BNO085 rigidly in line with the boom mount, several cm from the fan, battery leads and speaker. Use brass or nylon screws nearby and calibrate in the finished assembly.
  - Storage on the Kioxia UFS module: use a Radxa kernel built after May 11 2026 (PR #551), or add the PA_TACTIVATE quirk on other kernels. Do not mistake those reboots for overheating.
  - Batteries: insulate the cells from the SDR/SoC heat. Do not charge during heavy passes or above 45 C cell temperature.
- **Remaining uncertainties:**
  - The R4F female socket height and the gap between the LimeSDR underside and the female board are unpublished. Pedestal height depends on the ADT_R44_3D STEP or calipers.
  - Exact LimeSDR bottom-side part heights, and whether a part lands on the Q6A's 4.7 mm 2230 standoff in a direct-plug test, come from my reading of 2D drawings (+/-2 mm).
  - No measured LimeSDR Micro power or temperatures and no Q6A + PCIe SDR report exist yet. New orders ship Dec 15 2026.
  - No R44SF-on-ARM report. ADT shipping to Ukraine and the AliExpress price are unverified (adt.link $19; Newegg snippet $29.99 for 10 cm).
  - The display model is not chosen. Weight (180-700 g), power (6-18 W), its internal bridge clocks, and whether it accepts 268.5 MHz or a custom 166 MHz timing are unknown.
  - Whether the msm DP driver trains HBR or HBR2 for a given mode (it affects broadband S-band noise) is untested.
  - Pololu D36V50F9 is rationed. Mini560 specs vary between listings (11-20 V vs 11-32 V input, under 4 A sustained without a heatsink).
  - AliExpress Q6A copper cooler stock and price ($17-30) are intermittent and unverified. Its clearance next to the riser's folded cable is unverified.
  - Blower, aluminium, gap pad, SMA bulkhead and strap prices are estimates, not dated quotes.
  - Thundercomm RUBIK Pi 3 as a no-riser fallback: its M.2 2280 support was not confirmed (official spec only says M.2 Key M, PCIe 3.0 x2). Launch price was $179.
- **Confidence:** medium

