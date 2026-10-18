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

## Форуми та досвід спільноти (`forums`)

_Агент цього етапу ще працює (run `wf_e6b8e5e2-124`)._

