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

_Агент цього етапу ще працює (run `wf_e6b8e5e2-124`)._

