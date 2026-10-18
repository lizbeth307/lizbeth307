# Фінальні перевірки: повні відповіді субагентів

## completeness:lens2 (run `wf_6ce87eb1-883`)

- **Lens:** MISSING PARTS: cables and adapters, RF switching and its drive, bias tees, DC blocks, pads, loads, filters, fuses, PTCs and TVS, connectors and DC jacks, power key, charger input, fasteners, thermal parts, fan, sun hood, strap and tripod mount, weather protection, bags, spares, tools, flashing media, and the home-base PC for QAIRT 2.42.
- **Issues:**
  1.
    - **Area:** RF switching
    - **Components:**
      - RTL-A
      - RTL-B
      - Airspy HF+ input selector
      - HMC7992 SP4T
      - MCP23017
    - **Problem:** The core receivers have no input-routing hardware. In the patch tier, RTL-A has two VHF/UHF whip bulkheads (137 MHz and 2 m/70 cm). RTL-B has an L-band SMA and the LNB F port. Each RTL has one SMA input. The HF+ needs an HF / VHF-AIS / 50 ohm selector, but no part is named and it is missing from every BOM. The only switch in the files is the extended-tier sled (HMC7992), which was designed around the Lime COM port. The 'VHF bus' that feeds the HF+ for AIS is not defined anywhere. As specified, swapping chains means opening the case, and the menu cannot route inputs.
    - **Severity:** major
    - **Fix:** Fit two internal SP4T selectors. RTL-A: 137 / 2 m / 70 cm / terminated. RTL-B: L-band / LNB IF / BENCH or sled / terminated. Every port must be DC-free, with bias tees ahead of the switch. The HMC7992 board class from the files is enough here: expect about 30-37 dB isolation, and verify logic levels at 3.3 V. For the HF+, use a latching relay pair on a small PCB with SMA edge jacks (HF / VHF-AIS / 50 ohm). Accept it only if conducted isolation is 35 dB or more at 162-260 MHz on the LiteVNA. Do not buy commercial latching SMA relays: they are 12/28 V coil parts at about $242 or more. Drive everything from the new expander described in the GPIO issue. Fallback: the 'connect X' prompt, using external bulkheads only.
    - **Fix cost:** About $40-65: 2x HMC7992 board at CA$20.49 each (files, third-party listing, unverified), plus relays and PCB at $10-25 (estimate).
    - **Evidence:** small_antenna_stack.final.revised_stack[27] (two whip bulkheads, plus RTL-B SMA and the F port); report_research register decision #93 (selector part TBD, missing from the BOM); radio_lab.final.lab_bom[36] (sled HMC7992 is extended and Lime-oriented); lab_ui_hf.final.hf_receiver.setup ('VHF bus' undefined).
    - **Sources:**
      - https://www.datasheets.com/radiall/r570342100
      - https://www.pasternack.com/spdt-electromechanical-relay-latching-switch-accessory-pwb-3-ghz-12v-sma-pe71s8001-p.aspx
  2.
    - **Area:** Control I/O
    - **Components:**
      - MCP23017 #1 (0x20)
      - TPS2553 bias switches
      - LNB enable
      - Boni-Whip switch
      - selectors
    - **Problem:** One internal MCP23017 has 16 lines, but the core design needs about 24. Outputs (17): LAB EN, AUX EN, 3 VBUS cuts (RTL-A, RTL-B, HF+), 4 bias enables (137, L-band, 70 cm, H1), LNB EN, Boni EN, relay set/reset (2), and 2x2 SP4T control lines. Inputs (7): LAB FAULT, 4 bias FAULTs, LNB PG/FAULT, Boni FAULT. GPA4-GPA6 are already reserved for Lime bias.
    - **Severity:** major
    - **Fix:** Add MCP23017 #3 at 0x22 inside the handheld on I2C2. Alternatively use a TCA9535 with the built-in pca953x driver; avoid the PCA9555/TCA9555. Add the new lines to the single pin map before the schematic (P7). Use pull-downs so every switch and bias line is off and every selector sits on its terminated port at power-up.
    - **Fix cost:** $5.95 (Adafruit MCP23017 #5346, price from radio_lab), plus about $1 of resistors.
    - **Evidence:** radio_lab.integ.connections (MCP23017 #1 pin map: GPA0-3 used, GPA4-6 Lime bias, GPB0-1 FAULT); register decision #56; my count in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/missing_calc/b.py.
    - **Sources:** []
  3.
    - **Area:** LNB supply
    - **Components:**
      - LNB 13.2 V regulator
      - Pololu #2813
      - Othernet Bullseye LNB
    - **Problem:** The named LNB regulators are boost parts: 'TPS65233-class or a trimmed boost' in radio_lab, and an 'MT3608/XL6009-class boost' in the small stack. On the chosen 4S pack (12.0-16.8 V), the input is above 13.2 V for most of the discharge, and a boost cannot step down. A plain boost would pass roughly the pack voltage minus a diode drop, up to about 16 V, to the LNB. That is the horizontal-select range (16-19 V), outside the 11.5-14 V vertical window, so QO-100 NB would fail silently. TPS65233 behaviour with VIN above VOUT was not checked.
    - **Severity:** major
    - **Fix:** Use a SEPIC or buck-boost set to 13.2 V ±0.2 V: the Pololu S18V20AHV adjustable 9-30 V (same family as the S18V20F12). Pololu states the SEPIC output is 'not completely disconnected' when EN is low, so keep a second #2813 (or an eFuse rated 20 V or more) after it as the true disconnect. Then an LC filter, a PTC set from the measured LNB current, and an SMBJ15A at the F port. Strike the boost options from radio_lab lab_bom[34] and the small stack row 18.
    - **Fix cost:** About $40-50: S18V20F12 sibling $29.95 (pololu.com, rationed; S18V20AHV price not checked), #2813 $8.95, LC/PTC/TVS about $3.
    - **Evidence:** radio_lab.final.lab_bom[34]; small_antenna_stack.final.revised_stack[18]; register decisions #102/#103 (buck-boost or boost with true disconnect; 4S swings 12-16.8 V).
    - **Sources:**
      - https://www.pololu.com/product/2577
      - https://www.pololu.com/product/2813
  4.
    - **Area:** Bias tees / DC injection
    - **Components:**
      - SAWbird+ NOAA/GOES/iO/H1
      - RTL-SDR Blog LNA V2
      - LNB IF tee
      - TPS2553
    - **Problem:** No bias-tee part is named for the internal injectors. The files say 'specify an injector rated down to about 100 MHz', '2 generic 10 MHz-6 GHz bias tees (lose 3-7 dB at 100-200 MHz)', and 'the handheld's internal LNB bias tee', and the ZFBT was dropped. The current ratings are unchecked against the limits. The obvious SMD part, Mini-Circuits TCBT-14+, is rated 200 mA DC, which is below the TPS2553 250-300 mA limit for each SAWbird+ (180 mA budget). The LNB tee must carry 1.5-2x the measured LNB draw, which could be 0.4-0.8 A if a QRO.cz LNB (about 400 mA) is used.
    - **Severity:** major
    - **Fix:** Build one internal bias board with 5 channels (137, 2 m/70 cm, L-band, H1, LNB). Use inductors rated 0.5 A or more on the LNA channels and 1 A or more on the LNB channel, plus C0G DC blocks. Verify S21/S11 conducted on the LiteVNA over 100-1800 MHz (LNB channel 700-800 MHz) and record the results in parts.yaml. Use the TCBT-14+ only on lines of 80 mA or less. Where a bench-grade connectorised tee is wanted, use the ZFBT-4R2GW+ ($111.57 in the files).
    - **Fix cost:** $15-30 DIY (estimate). TCBT-14+ about $8.45 at qty 10 (old datasheet price).
    - **Evidence:** register decision #96 ('Specify an injector rated down to about 100 MHz'); register decision #100 (TPS2553 250-300 mA); radio_lab.integ ('2 generic 10 MHz-6 GHz bias tees'); radio_lab.final.lab_bom[34] (internal LNB tee unnamed).
    - **Sources:**
      - https://www.minicircuits.com/pdfs/TCBT-14+.pdf
      - https://www.mouser.at/new/mini-circuits/mini-circuits-tcbt14-plus-bias-tee/
  5.
    - **Area:** Cables and adapters
    - **Components:**
      - SMA bulkhead pigtails
      - RG316/RG174 jumpers
      - 75 ohm F lead
      - USB pigtails
      - HDMI lead
      - Adafruit CH334F #5997
    - **Problem:** No file has a cable schedule. Each study leaves cables out or guesses: foldable 'Not included: cables and pigtails ($40-60), DC blocks (about $25)'; antennas 'about $40-60 (estimate)'; small stack '2-3 thin leads $15-30'. Concrete gaps:
  - The Baofeng A-V85 is SMA-female, so it needs an M-M adapter.
  - The CH334F hub's 4 downstream ports are 4-pin pads only (Adafruit page), so LAB USB-A, the HF+, the HMI RP2040 and the puck all need pigtails.
  - The internal V4Ls need short USB extensions and SMA jumpers to their bulkheads.
  - The LNB needs a 75 ohm F lead.
  - The Boni-Whip needs a BNC lead.
  - The GNSS needs an IPX-to-SMA pigtail if the antenna is external.
  - The touch USB needs a VBUS-cut lead.
  - EDL recovery needs an A-to-A cable.
  - The HF+ USB connector type is not recorded (airspy.com does not list it).
    - **Severity:** major
    - **Fix:** Adopt the cable schedule in budget_tables, with every run's length, genders and qty. Buy branded RG316 jumpers or VNA-screen generic ones. Keep RP-SMA in a separate bag.
    - **Fix cost:** About $90-170: internal RF $25-45, external RF and adapters $40-80, USB $25-45 (estimates).
    - **Evidence:** foldable_antennas.final.total_cost; antennas.json (cables/pigtails/adapters estimate); small_antenna_stack.final.revised_stack[14] and [23]; radio_lab.final.lab_bom[30] (CH334F H1-H4); lab_ui_hf hf_antenna (BNC-to-SMA lead).
    - **Sources:**
      - https://www.adafruit.com/product/5997
      - https://www.waveshare.com/LC76G-GNSS-Module.htm
  6.
    - **Area:** Filters / LNA per band
    - **Components:**
      - Nooelec Flamingo+ FM
      - SAWbird+ NOAA
      - LNA V2
      - 70 cm BPF
    - **Problem:** The register picks 'one filter, permanently in the 137/145 MHz path', but the patch tier has two VHF/UHF entry points. The SAWbird+ NOAA has a 2.6 MHz passband at 137 MHz, so it blocks 145.8 MHz. The planned 70 cm BPF ahead of the LNA V2 blocks 2 m. As a result, no filtered 2 m path exists for the Yagi's 2 m half, 2 m CubeSats or APRS. The 70 cm BPF is still unnamed.
    - **Severity:** major
    - **Fix:** Write one band-to-filter/LNA matrix:
  - 137: Flamingo+ then SAWbird+ NOAA.
  - 2 m: Flamingo+ #2 then LNA V2.
  - 70 cm: BPF then LNA V2.
  - L-band: SAWbird+ GOES or iO.
  - 1420: SAWbird+ H1.
  - LNB IF: pad.
  Buy a second Flamingo+ and run two LNA V2s in service plus one spare. For the 70 cm BPF, either buy the Nooelec Ham Filter Bank Barebones ($66.95, files, includes 70 cm) now, or get a quote for the Anatech 9531 cavity (432-438 MHz, SMA, 1.0 dB or less, no price listed).
    - **Fix cost:** $24.95 Flamingo+ + $19.95 extra LNA V2 + $66.95 filter bank, about $112 in total.
    - **Evidence:** register decision #85 (one Flamingo+); register decision #96 (SAWbird+ NOAA 2.6 MHz 3 dB bandwidth); small_antenna_stack.final.revised_stack[9]/[10]/[14]; foldable_antennas.final.foldable_kit[1] (145.8 MHz feed to the RTL).
    - **Sources:**
      - https://anatechelectronics.com/435-mhz-band-pass-filter-9531.html
  7.
    - **Area:** Battery build
    - **Components:**
      - Molicel P50B x4 (+1 spare)
      - nickel strip
      - balance lead
      - BMS
      - welding
    - **Problem:** The pack is a welded 4S1P from bare cells ('test capacity and IR before spot-welding'), but no file budgets a welder or pack-build service, a nickel grade, fish paper, a balance-lead connector (the ISDT 608PD needs a JST-XH 5-pin balance lead) or a cell tester. The P50B also had only UAH prices.
    - **Severity:** major
    - **Fix:** Buy 5 P50B: NKON lists EUR 6.75 incl. VAT (EUR 5.58 ex VAT) per cell on a page dated 31 Jul 2026. Add 0.15x8 mm pure-nickel strip, fish-paper rings, Kapton, 4S wrap, a JST-XH 5-pin balance lead to an internal service connector, and an XT30 main lead. Have a battery shop or pack builder weld it. Buy a capacitor welder (third-party listings $270-305, unverified) only if more packs will be built. Reject spring holders (contact resistance and vibration in a handheld) and soldering to cells. Check cell IR and capacity before welding with a cell tester, or by individual charge and discharge.
    - **Fix cost:** $70-105: cells about $39 at EUR 33.75, sundries $10-25, welding service $20-40 (estimate).
    - **Evidence:** power.json verify.known_problems_and_fixes_to_apply (last item); power.json final_recommendation (P50B priced only on Prom.ua); register decision #59 ('No world price is given').
    - **Sources:**
      - https://www.nkon.nl/rechargeable/molicel-inr21700-p50b-5000mah-50a.html
  8.
    - **Area:** Mechanical mount
    - **Components:**
      - 1/4-20 tripod/boom mount
      - 2 mm aluminium mid-plate
    - **Problem:** mechanical_thermal offers 'a captured 1/4-20 nut, or a thread tapped in the aluminium plate'. A 1/4-20 thread has a 1.27 mm pitch, so a 2 mm plate gives only 1.57 engaged threads. About 9.5 mm (1.5 D) is a common aluminium rule of thumb. The tapped option would strip under a 1.05-1.4 kg device on a boom or tripod.
    - **Severity:** major
    - **Fix:** Strike the tapped-plate option. Use a 10-12 mm aluminium boss with a steel 1/4-20 insert or rivet nut, bolted to the mid-plate with 4x M3 and fitted with an anti-rotation pin, or a captured steel nut in a printed pocket backed by the plate. Pull-test it at 3x device weight.
    - **Fix cost:** $3-8 (estimate).
    - **Evidence:** mechanical_thermal.json verify.known_problems_and_fixes_to_apply ('Tripod/boom mount: a captured 1/4"-20 nut, or a thread tapped in the aluminium plate'); arithmetic in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/missing_calc/b.py (model).
    - **Sources:** []
  9.
    - **Area:** Antenna supports
    - **Components:**
      - travel tripod
      - pan-tilt head
      - collapsible mast
      - guy cords and stake
    - **Problem:** The procedures need supports that no BOM buys:
  - V-dipole at 1-1.1 m.
  - HRPT 'from a tripod at least 50 cm above ground'.
  - Tripod-mounted Yagi and 23 dBi horn.
  - Boni-Whip at least 2 m up on 'a pole that collapses to 35 cm or less'.
  The dipole kit includes only a flexible mini tripod, and foldable_antennas explicitly excludes 'a mini pan-tilt tripod'. The packed-size rule also applies to these supports.
    - **Severity:** major
    - **Fix:** Buy a travel tripod that folds to 35 cm or less, reaches 1.2 m or more, takes a 1/4-20 and has a small pan-tilt head. Add a shock-corded aluminium tent-pole mast (7x35 cm sections, about 2.4 m) with 2-3 guy cords and a ground stake. Add a throw cord and weight for the HF wire. Count 0.35-0.9 kg more in the sling.
    - **Fix cost:** $55-150 (estimate; no model priced).
    - **Evidence:** foldable_antennas.final.foldable_kit[0] (fold_method lists only the flexible tripod); foldable_antennas.final.total_cost ('Not included: ... A mini pan-tilt tripod'); foldable build step 7; lab_ui_hf.final.hf_antenna.setup (Boni-Whip pole).
    - **Sources:** []
  10.
    - **Area:** Weather protection
    - **Components:**
      - handheld case
      - fan and blower intakes
      - encoders and keys
      - feed-point LNAs
      - connectors
    - **Problem:** No study sets an ingress target or budgets weather parts:
  - The case has a fan and a blower intake; the encoders are not sealed.
  - The cased SAWbird+ units at the antenna feeds are not waterproof.
  - Only antennas.json mentions self-amalgamating tape, adhesive heat-shrink and drain holes; no file mentions desiccant.
  Physics versus wish: with 11-32 W internal (no Lime) plus 13.5-17 W solar on the display face, a sealed passive case cannot shed the heat, so IP67 is not reachable with this thermal design.
    - **Severity:** major
    - **Fix:** Target IPX4/IP54. Parts:
  - Baffled intakes with stainless mesh and hydrophobic foam.
  - Adhesive ePTFE vents on the sealed RF bay and the LNA boxes.
  - Silicone dust caps on every SMA, F and USB port.
  - A clear rain sleeve.
  - IP65 ABS boxes with cable glands for the feed LNAs.
  - Self-amalgamating tape and dielectric grease.
  - Silica gel in the Pelican and pouches.
  Add a rule: LOCK plus encoder-only operation in rain, and no fan intake facing up.
    - **Fix cost:** $45-110 (estimate).
    - **Evidence:** grep over final/*.json: 'desiccant' 0 hits; 'gasket' 2 hits (mechanical only); IP ratings only for displays; antennas.json sealing advice; mechanical_thermal decision #17 (25-35 W internal with the Lime, 11-17/24-32 W without; solar 13.5-17 W).
    - **Sources:** []
  11.
    - **Area:** Home-base PC
    - **Components:**
      - x86-64 PC
      - NVIDIA GPU 8-16 GB
      - Ubuntu 22.04 / Python 3.10 for QAIRT 2.42
    - **Problem:** The user's PC is unconfirmed (register #45, open question 9), and the Ubuntu 22.04 VM route is untested. Without a GPU there is no T3 detector retraining. Without any x86-64 machine there is no QAIRT 2.42 conversion: its Python converter and quantizer are x86-64 only.
    - **Severity:** major
    - **Fix:** Minimum: any x86-64 machine with 16 GB RAM or more, running an ubuntu:22.04 container (Python 3.10) with the archived QAIRT 2.42.0.251225 zip. No GPU needed; $0 if owned; container use is untested. Recommended for T3: an NVIDIA 12 GB card (RTX 3060 12 GB class), 32-64 GB RAM, 1-2 TB NVMe, and a 2-4 TB backup disk for golden images and datasets. Private captures stay off Colab/Kaggle.
    - **Fix cost:** $0 if a PC exists. GPU about EUR 298 (France low, GPUPrix, 6 Jul 2026) to about $500 (US listings after the relaunch, Guru3D, Jul 2026); backup disk $60-100 (estimate).
    - **Evidence:** npu_training.final.hardware_needs; register decision #45; register open_questions[9].
    - **Sources:**
      - https://www.guru3d.com/story/geforce-rtx-3060-12gb-prices-reportedly-jump-after-relaunch/
      - https://gpuprix.com/zh/france/gpus/geforce-rtx-3060-12gb
  12.
    - **Area:** Power accessories
    - **Components:**
      - Pololu #2813 pushbutton
      - power key
      - XT30 arming plug
      - IP2368 USB-C
      - wall PD charger
    - **Problem:** The #2813 needs a physical pushbutton, but the six sealed HMI keys have no POWER key. There is no transport disconnect, although the Pelican note says to 'pack so the master switch cannot be pressed'. The IP2368 needs a PD source of 60 W or more, but only a power bank is listed: no wall charger, no 3-5 A C-C cable, and no sealing for the charge port. The IP67 panel USB-C extensions found have inconsistent ratings (60 vs 100 W).
    - **Severity:** minor
    - **Fix:** Fit a recessed sealed 12-16 mm momentary button for the #2813, and an XT30 loop 'arming plug' that disconnects the pack for travel. Mount the IP2368 USB-C at the wall with an O-ring and silicone cap instead of an extension, which avoids CC-line problems. Add a 65-100 W PD wall charger and a 1 m 5 A C-C cable.
    - **Fix cost:** $40-70 (estimate). Panel extensions found: about $11 + $10 shipping (eBay) to $58.99 (Newegg).
    - **Evidence:** power.json final_recommendation (#2813 switch); radio_lab.final.lab_bom[48] note; radio_lab.final.lab_bom[26] (bank only).
    - **Sources:**
      - https://www.newegg.com/p/3C6-00V6-02DG1
      - https://www.ebay.de/itm/174361134723
  13.
    - **Area:** Protection ratings
    - **Components:**
      - pack fuse
      - J21 branch fuse
      - LAB 5 V fuse
      - PTCs
      - TVS
    - **Problem:** The protection table is incomplete and inconsistent:
  - Pack fuse 7.5 A vs 5 A.
  - The J21 branch is 'behind a fuse' with no value.
  - No Boni-Whip polyfuse value.
  - No TVS on the raw pack node.
  - No bias-PTC temperature derating (a 0.25 A-hold PTC at 25 C holds only about 0.17-0.19 A at 60-70 C; typical derating, unverified).
  - No fuse type or holder.
    - **Severity:** minor
    - **Fix:** Use the fuse/PTC/TVS table in budget_tables: ATM mini-blade 32 V fuses in holders, 18 AWG on the pack lead, SMBJ18A on the pack node, SMBJ14A after the 12 V regulator, SMBJ15A on the LNB port. A bias PTC (only where no TPS2553 is fitted) of 0.35-0.5 A hold at 25 C.
    - **Fix cost:** $13-25 (estimate).
    - **Evidence:** register decision #64 (fuse conflict); register decision #15 (J21 'behind a fuse'); register decision #95 (Boni polyfuse); register decision #100 (PTC hold 250 mA or more at maximum temperature).
    - **Sources:** []
  14.
    - **Area:** Flashing and recovery media
    - **Components:**
      - Radxa RA019-E1U1 UFS/eMMC reader
      - USB A-to-A cable
      - microSD rescue card
      - USB stick
      - card reader
    - **Problem:** The recovery and flashing kit is spread across files and never consolidated. storage.json gives the reader as an 'older listing ~$25'. Without the T7, offline update bundles and lab-snap need a USB stick or SD card, and neither is budgeted.
    - **Severity:** minor
    - **Fix:** One recovery kit:
  - RA019-E1U1 reader, EUR 13.00 at TinyTronics (A vs C connector differs between listings; check).
  - USB 3 A-to-A cable for edl-ng EDL on the blue port.
  - 32-64 GB A2 microSD with the rescue image.
  - USB 3 card reader.
  - 64 GB USB stick for signed offline bundles.
  Also archive the BIOS 260120 zip, edl-ng, the image and QAIRT 2.42 with SHA-256 on the home-base disk.
    - **Fix cost:** $40-55 (reader verified; rest estimate).
    - **Evidence:** storage.json (Radxa UFS/eMMC USB reader 'older listing ~$25'; microSD rescue image; edl-ng A-to-A); compute.json (EDL recovery kit); register decision #35 (lab-snap on the T7).
    - **Sources:**
      - https://www.tinytronics.nl/nl/data-opslag/modules/radxa-ufs-emmc-naar-usb-3.0-lezer-module
  15.
    - **Area:** Duplicate instrument / rule
    - **Components:**
      - NanoVNA 3 GHz (small stack)
      - LiteVNA 64 (core)
    - **Problem:** small_antenna_stack adds a NanoVNA covering 3 GHz or more ($60-130) as 'essential for tuning the helical whip ... sweep briefly indoors'. That use radiates, which breaks the receive-only rule, and the purchase duplicates the core LiteVNA 64.
    - **Severity:** minor
    - **Fix:** Drop it. Use the LiteVNA 64 conducted only, and tune antennas receive-only.
    - **Fix cost:** Saves $60-130.
    - **Evidence:** small_antenna_stack.final.revised_stack[29]; radio_lab.final.lab_bom[0]; user_requirements.md hard rule 1.
    - **Sources:** []
  16.
    - **Area:** HF chain connectors
    - **Components:**
      - Boni-Whip injector
      - 12.5 V active-antenna rail
    - **Problem:** The Boni-Whip injector is fed 'from the lab's active-antenna rail', but no output jack, cable or polyfuse value exists. The Boni-Whip current is unpublished.
    - **Severity:** minor
    - **Fix:** Fit a 2-pin locking 'ANT PWR' jack on the HF panel, with a 1-2 m DC lead to the injector. Use a 0.2 A-hold polyfuse and resize it after measuring the current. Put the labd switch and a FAULT input on MCP23017 #3.
    - **Fix cost:** $5-10 (estimate).
    - **Evidence:** lab_ui_hf.final.hf_antenna.setup ('BONI-WHIP: POWER'); register decision #95 (12.5 V; current not listed).
    - **Sources:** []
  17.
    - **Area:** HMI and audio
    - **Components:**
      - 2 push encoders
      - 6 sealed keys
      - knobs
      - VEML7700
      - RGB LED
      - piezo
      - 3.5 mm audio
      - headphones
    - **Problem:** The HMI parts are unpriced: lab_ui_hf open question 11 asks for 'part prices for the EC11 encoder, switches and knob', and mechanical gives '$10-20' for strap, buttons and encoder together. EC11-class encoders are not sealed. Audio uses the Q6A 3.5 mm jack, but there is no panel extension and no headphones. No speaker is planned, and a class-D amplifier would add switching noise near the RF bay.
    - **Severity:** minor
    - **Fix:** Budget 2 push encoders (sealed or O-ring-shafted), 6 IP67 tact keys, knobs, a VEML7700 breakout, an RGB LED and a piezo. Add a 3.5 mm panel extension and wired headphones. Fit a speaker only after a terminated-floor A/B with a linear amplifier.
    - **Fix cost:** $30-65 (estimate).
    - **Evidence:** lab_ui_hf.final open questions (item 11); lab_ui_hf (second push-encoder fix; PipeWire to the 3.5 mm jack); mechanical_thermal final_recommendation price line.
    - **Sources:** []
  18.
    - **Area:** Fasteners and consumables
    - **Components:**
      - heat-set inserts
      - screws
      - nylon screws near IMU
      - strap lugs
      - thermal pads/paste
      - KSD9700
      - AR film
    - **Problem:** There is no fastener schedule for the ASA shell: the file only says 'no heat-set inserts alone' for the tripod. Strap anchors are not defined, although 'Strap required'. The AR film needed for the 6.2:1 sun contrast is only 'e.g. TELESIN', with no price. The thermal pad grade and thickness are given only for the Lime pedestal, which is conditional.
    - **Severity:** minor
    - **Fix:** List:
  - M2.5 and M3 brass heat-set inserts for the shell joints.
  - A2 stainless screws, plus nylon or brass screws within 15-20 cm of the IMU.
  - 2 metal strap lugs bonded to the plate, a hand strap and a sling strap.
  - Pads of 1-2 mm and 3-6 W/mK for the UFS and IP2368, and paste for the SoC.
  - A KSD9700 70 C switch on the IP2368.
  - A 7in AR film of about 0.7% reflectance.
    - **Fix cost:** $55-105 (estimate).
    - **Evidence:** mechanical_thermal.json verify (tripod note; M2.5 standoffs; 'Strap required'); display_market.final.sunlight_measures; power.json (KSD9700).
    - **Sources:** []
  19.
    - **Area:** Bags and spares
    - **Components:**
      - antenna roll/pouch
      - Yagi element tube
      - 10-12 L sling
      - antenna spares
      - spare Q6A
    - **Problem:** Bags and spares are unpriced or uncounted:
  - foldable_antennas says the kit 'fits a 35 x 25 x 10 cm pouch', unpriced.
  - Foldable step 10 lists spares (telescopic pair, 2 x 70 cm elements, a petal, clips, a spare spool), unpriced.
  - The register's 'budget a spare board' for the Q6A is in no total.
  - The petals and gores have sharp 0.3-0.5 mm aluminium edges and need a padded roll.
    - **Severity:** minor
    - **Fix:** Buy a padded antenna roll, an element tube and a 10-12 L sling. Use a second RTL-SDR Blog dipole kit as the source of spare telescopic elements. A spare Q6A 12 GB is optional.
    - **Fix cost:** $68-113 (bags $50-95 estimate, dipole kit $17.95 in files); spare Q6A $189.99 (optional).
    - **Evidence:** foldable_antennas.final.total_packed_volume_and_weight; foldable build_and_test_steps[9]; register decision #22.
    - **Sources:** []
  20.
    - **Area:** Build tools
    - **Components:**
      - calipers
      - sheet-metal snips/deburr
      - M5 tap/die
      - heat gun
      - coax crimper
      - enclosed 3D printer for ASA
    - **Problem:** The antenna and case build needs tools that no list includes:
  - Calipers, for the LNB neck and waveguide ID (16.8-21.9 mm) that 'must be measured first', and for the helix geometry.
  - Snips and a deburring tool for the petals and gores.
  - An M5 tap and die for rod couplers.
  - A heat gun for adhesive heat-shrink.
  - A crimper, unless jumpers are bought ready-made.
  - An enclosed printer for ASA. Whether the user owns a 3D printer is unknown.
    - **Severity:** minor
    - **Fix:** Add a tool list. Use a print service for the ASA shell if there is no enclosed printer.
    - **Fix cost:** $80-140, plus a $30-80 print service if needed (estimates).
    - **Evidence:** register decision #106 (measure LNB neck and waveguide on arrival); foldable build steps 1-5; radio_lab.final.lab_bom[22] (only drivers, cutters, stripper, tweezers).
    - **Sources:** []
  21.
    - **Area:** Inconsistent LNA powering
    - **Components:**
      - SAWbird+ GOES on the helicone
    - **Problem:** foldable_antennas build step 3 powers the SAWbird+ GOES '5 V through its micro-USB, with a DC block before the Lime'. That needs a 5 V cable run to the feed, and it puts DC on the RF output. It contradicts the register rule that every SAWbird+ is fed through a coax injector from a TPS2553.
    - **Severity:** minor
    - **Fix:** Strike the micro-USB step. Power the LNA over the coax from the internal bias board.
    - **Fix cost:** $0
    - **Evidence:** foldable_antennas.final.build_and_test_steps[2]; register summary ('every SAWbird+ runs from a TPS2553 at 250-300 mA'); rf_frontend verify (micro-USB-powered SAWbird leaks DC to RF out).
    - **Sources:** []
  22.
    - **Area:** Puck, GNSS and service access
    - **Components:**
      - IMU puck enclosure/connector/cable
      - GNSS IPX-SMA pigtail + external antenna
      - RJ45/UART service access
      - Wi-Fi antennas
    - **Problem:** The puck's 'sealed boom connector', its 1-2 m cable and its enclosure or shield are unpriced. The external GNSS antenna 'on a 1-3 m lead' needs an IPX-to-SMA bulkhead and a cable antenna. The Waveshare kit ships with a ceramic active antenna, connector unconfirmed. The register's 'Keep UART access in the case' and storage's 'offload over GbE' have no hatch or panel part. Whether the FCU760K Wi-Fi needs U.FL antennas is not recorded.
    - **Severity:** minor
    - **Fix:** Puck: GX12 4-pin pair plus 2 m shielded 4-core cable and a shield can. GNSS: IPX-SMA bulkhead pigtail plus an active antenna with a 3 m SMA lead, if the antenna is not on the lid. Add a service hatch with UART and RJ45 access, or a panel RJ45 extension. Confirm the Wi-Fi antenna provision from the schematic.
    - **Fix cost:** $30-55 (estimate).
    - **Evidence:** radio_lab.integ.connections (H2 'sealed boom connector'); gnss_imu verify (external active antenna 1-3 m lead); register decision #22; storage.json (GbE offload).
    - **Sources:**
      - https://www.waveshare.com/LC76G-GNSS-Module.htm
  23.
    - **Area:** Carried weight
    - **Components:**
      - sling kit
    - **Problem:** The register's sling figure of 3.7-4.4 kg leaves out the supports, coax set, bag and weather kit. With them the sling is 4.4-6.05 kg, or 5.0-6.7 kg with the 630 g PD bank (model).
    - **Severity:** minor
    - **Fix:** Restate the weights in STACK.md. Offer a light patch-tier sling (whips, 4-turn helix, bare LNB, about 0.6-0.9 kg of antennas) as the everyday kit.
    - **Fix cost:** $0
    - **Evidence:** register decision #71; foldable_antennas.final.total_packed_volume_and_weight; /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/missing_calc/b.py.
    - **Sources:** []
- **Proposed decisions:**
  1.
    - **Question:** C1 LimeSDR Micro keep or drop
    - **Decision:** Gated optional. Keep the cancellable pre-order, confirm it is a refundable store order, and decide on 31 Jan 2027 or on delivery. Buy no Lime-only parts before the gate: R44SF $19, MHF4 tool $18.10, 2x MHF4L-SMA $12, REF IN, port DC blocks and pads, VLM-33-S+, cavity.
    - **Reason:** No core receive function needs it. The M.2 slot can take it later. The deposit is refundable before shipping.
    - **Consequences:** Its dependents are tagged conditional: RAM ring, T7, CPU7, LIME profiles, riser, 7.5 A fuse, sled COM. The core input selectors (RTL-A/B SP4T) are needed either way.
    - **Alternatives rejected:** Drop now: loses S-band and the 56 Msps NPU data with no saving that cannot be recovered. Firm keep: the driver is validated on x86 only.
  2.
    - **Question:** C2 Q6A RAM tier
    - **Decision:** Buy the 12 GB board now ($189.99, Allnet) and re-check stock on the order date. Budget RAM at 1.5 GiB or less for the ring without the Lime, and 4 GiB with it.
    - **Reason:** RAM cannot be added later, and the cost is only about $65-75 more than 8 GB.
    - **Consequences:** The 8 GB board is used only if the Lime is dropped before purchase.
    - **Alternatives rejected:** 8 GB board (would close the training and Lime options).
  3.
    - **Question:** C3 Pack 3S vs 4S
    - **Decision:** 4S1P P50B (72 Wh) with a regulated 12 V rail into J21. Cells come from NKON (EUR 6.75 incl. VAT each) or another established EU/US seller, plus 1 spare. The pack is welded by a shop or pack builder.
    - **Reason:** The 13.2 V LNB, 12.5 V Boni-Whip LDO, AUX 12 V and ENR stability all need headroom above 12 V.
    - **Consequences:** The LNB regulator must be buck-boost (see C8). Fuse is 5 A without the Lime and 7.5 A with it.
    - **Alternatives rejected:** 3S: needs a boost for every 12 V or higher load.
  4.
    - **Question:** C4 12 V regulator
    - **Decision:** Buy the D36V50F12 ($39.95) with the EN hardware cut at 13.4 V or above. Replace it with a forced-PWM buck-boost rated 5 A or more only if the terminated-floor A/B shows wandering spurs, or the sealed-case current test fails at 3.5 A.
    - **Reason:** It is the only verified, priced part. The model load is 3.5 A (42 W).
    - **Consequences:** Its 13.3 V dropout fixes the cut-off order: Linux at 13.6 V, then the hardware cut at 13.4 V.
    - **Alternatives rejected:** 9 V into J21 (based on a misplaced-TVS reading).
  5.
    - **Question:** C5 USB port map
    - **Decision:** Freeze the Lime-agnostic map:
  - Blue port: RTL-A, or the T7 if the Lime is kept.
  - FE1.1s P1: RTL-B. P2: touch. P3: CH334F.
  - CH334F: H1 HMI RP2040, H2 IMU puck, H3 LAB USB-A, H4 HF+, each through soldered pigtails (the board has pads only).
  With the Lime and T7, the IMU moves to the UART7 relay so that H2 can take RTL-A.
    - **Reason:** The CH334F has no USB-A ports (Adafruit page). The model FE1.1s load is 13.4 MB/s, 38% of 35 MB/s.
    - **Consequences:** Zero spare ports in the core; a 4th V4L can go only on LAB USB.
    - **Alternatives rejected:** A second CH334F (adds a 12 MHz harmonic source and hub depth).
  6.
    - **Question:** C6 40-pin header and bus map
    - **Decision:** Adopt the register map: PPS on pin 7, UART6 on 16/18, I2C0 for the INA228 only, I2C2 for the MCP23017s. Add MCP23017 #3 at 0x22 for the extra lines. The IMU uses USB-CDC on CH334F H2 until UART7 is proven. Fan PWM on pin 33 after the test, else GPIO56.
    - **Reason:** The core needs 24 control lines against 16 on one expander. UART7 is unverified.
    - **Consequences:** One extra $5.95 part and one I2C address.
    - **Alternatives rejected:** Header GPIOs for bias enables (the header is already crowded).
  7.
    - **Question:** C7 Hardware ownership
    - **Decision:** labd is the sole owner of the GPIO, expanders, selectors, bias and LNB. labrx owns the single ring and recorder. labclassify runs inferd and fusiond. rflab becomes a labd module.
    - **Reason:** Two owners of the same hardware lines cannot be made safe.
    - **Consequences:** The new selector and relay lines get labd leases and safe defaults.
    - **Alternatives rejected:** flock-based sharing.
  8.
    - **Question:** C8 LNB supply
    - **Decision:** A SEPIC or buck-boost (Pololu S18V20AHV class) set to 13.2 V ±0.2 V, then a second #2813 as true disconnect, then LC, a PTC, and an SMBJ15A at the F port. No 18 V branch. Set one current limit at 1.5-2x the measured draw. The internal LNB tee inductor is rated 1 A or more.
    - **Reason:** A boost cannot step a 12-16.8 V pack down to 13.2 V. Pololu says the SEPIC output is not fully disconnected when EN is low.
    - **Consequences:** About $40-50. Acceptance test: 0 V at the port when off.
    - **Alternatives rejected:** MT3608/XL6009 or TPS65233-class boost; switching with a TPS2553.
  9.
    - **Question:** C9 LNA bias rule
    - **Decision:** Each SAWbird+ gets a TPS2553 at 250-300 mA. Every bias tee is rated 0.5 A or more. The V4L tee is used only for LNAs of 80 mA or less. The TCBT-14+ (200 mA) is allowed only on lines of 80 mA or less.
    - **Reason:** A tee rated below the current limit is the weak link in a fault.
    - **Consequences:** The DIY bias board needs a conducted VNA check.
    - **Alternatives rejected:** The 100-160 mA PTC; the GOES+ on the V4L tee.
  10.
    - **Question:** C10 FM filter
    - **Decision:** Flamingo+ FM. Buy 2: one at the 137 MHz entry and one at the 2 m entry, each ahead of its LNA.
    - **Reason:** The patch tier has two VHF entry points, and the SAWbird+ NOAA blocks 145.8 MHz.
    - **Consequences:** +$24.95. The 70 cm path uses a BPF instead.
    - **Alternatives rejected:** One filter moved by hand; the RTL-SDR Blog band-stop (no DC rating published).
  11.
    - **Question:** C11 librtlsdr
    - **Decision:** Use only the .so.2 rebuild of noble 2.0.1 with commits 0204c9c and 65f0658, held. Delete the other recipes.
    - **Reason:** It keeps the consumers' ABI.
    - **Consequences:** First arm64 build on the Q6A.
    - **Alternatives rejected:** 2.0.3 .so.0; purge and fork.
  12.
    - **Question:** C12 Display field clock
    - **Decision:** 127.9 MHz (51.7 Hz, 2200x1125), or 164.4-168.4 MHz if the panel accepts it. Use a shielded 10-15 cm HDMI with Mix 31/61 ferrites.
    - **Reason:** 128.70 MHz has harmonics at 1544.4 and 1415.7 MHz.
    - **Consequences:** Change all files and the cmdline together.
    - **Alternatives rejected:** 128.70 MHz; 1080p60.
  13.
    - **Question:** C13 Kernel and PPS
    - **Decision:** Out-of-tree pps-gpio built as a DKMS deb on 6.18.2-4. Build pps-ldisc too, only if the FT232RL fallback is kept.
    - **Reason:** CONFIG_PPS=y is set on the held kernel.
    - **Consequences:** Route B (7.0.11) is dropped.
    - **Alternatives rejected:** Moving to the 7.0.11 kernel.
  14.
    - **Question:** C14 INA228
    - **Decision:** I2C0, user-space i2c-dev, no DT binding. Shunt in the pack lead ahead of the IP2368 tap.
    - **Reason:** A bound driver blocks access to the CHARGE register.
    - **Consequences:** Fix power.json and npu_training.
    - **Alternatives rejected:** The ina238 hwmon driver on i2c6.
  15.
    - **Question:** C15 Antenna tiers
    - **Decision:** Two tiers. The LRPT default is the V-dipole; the Yagi defaults to the ultra-compact build. Reverse the small-stack removals: Lime gated, T7 tied to the Lime, 12 GB kept. Strike the loops. Supports (tripod 35 cm or less folded, tent-pole mast) are in the foldable kit.
    - **Reason:** The governing size rule allows folded pieces of 35 cm or less.
    - **Consequences:** Sling weight 4.4-6.05 kg (model).
    - **Alternatives rejected:** Small-stack-only removals.
  16.
    - **Question:** C16 Policy leftovers
    - **Decision:** Strike everything listed before STACK.md:
  - VNA S11 into antennas, and the small-stack NanoVNA purchase.
  - Inmarsat-C decode-then-filter.
  - VLF SID.
  - BT rfkill and the Artemis stop (add both).
  - Voice IQ and Set B.
  - Iridium IRA/IBC and CARTOSAT-3.
  - H-probes.
  - City lists and Kyiv constants.
  - wsjtx GUI and fldigi.
  - The bearing log.
    - **Reason:** Each item breaks the rules in user_requirements.md.
    - **Consequences:** Saves $60-130 (NanoVNA) and $50-109 (H-probes).
    - **Alternatives rejected:** Keeping them with warnings.
  17.
    - **Question:** C17 HF antenna chain
    - **Decision:** Boni-Whip at 12.5 V via an LDO, behind an ANT PWR jack with a 0.2 A polyfuse (resize after measuring). HF+ selector: a latching relay pair accepted at 35 dB or more of conducted isolation at 162-260 MHz. Ask the user to confirm the HF-loop removal.
    - **Reason:** The selector was missing from the BOM, and commercial latching SMA relays are $242 or more with 12/28 V coils.
    - **Consequences:** $15-35 extra.
    - **Alternatives rejected:** HMC241 (DC blocks hurt LF); Radiall/Pasternack relays.
  18.
    - **Question:** C18 Storage
    - **Decision:** T7 only with the Lime. Otherwise a 64-128 GB A2 microSD plus a USB stick for bundles, with the rescue and A/B layout on UFS. Retention: products by default, raw only when pinned.
    - **Reason:** The no-Lime peak is 16.4 MB/s.
    - **Consequences:** The flashing kit must include an SD card and a stick.
    - **Alternatives rejected:** Buying the T7 unconditionally.
  19.
    - **Question:** C19 CPU allocation
    - **Decision:** A55: UI, daemons and CPU inference. CPU4-6: DSP and T2 between passes. CPU7 isolated only with the Lime.
    - **Reason:** T2 is 4.5-10.8 min on the A78 cores (model).
    - **Consequences:** Fix lab_ui_hf.
    - **Alternatives rejected:** Trainer on the A55 cores.
  20.
    - **Question:** C20 Roadmaps
    - **Decision:** NPU Phase 0 inside the W1-2 gates (19 Oct-1 Nov 2026). Minimal labeller in P0b. HF-F and second-RTL profiles before the HF classes are shown in the UI.
    - **Reason:** The labeller is needed about 3 months before the UI schedules it.
    - **Consequences:** The schedules in STACK.md are merged.
    - **Alternatives rejected:** Keeping two separate roadmaps.
  21.
    - **Question:** C21 V4L count
    - **Decision:** Buy 3: 2 in service plus 1 spare. Monitoring time-shares a receiver, or AIS runs on the HF+. A 4th ($37.95) only for continuous monitoring, on LAB USB.
    - **Reason:** R828S stock is finite, and there are no spare ports.
    - **Consequences:** $113.85.
    - **Alternatives rejected:** Using the spare as a full-time monitor.
  22.
    - **Question:** C22 Software recipes
    - **Decision:** One venv per tool, as in the register: NanoVNA-Saver via pipx, PySide6 6.12, libgpiod v1, Skyfield 1.55 from pip, SatDump 2.0-alpha from source.
    - **Reason:** These are the versions available in noble.
    - **Consequences:** Each is tested on the Q6A within the return window.
    - **Alternatives rejected:** apt nanovna-saver 0.6.3; libgpiod v2.
  23.
    - **Question:** C23 Region unknown
    - **Decision:** Hold the region-dependent purchases until the user names the region: LNB, horn materials, SAWbird+ iO, MAX-M10S. Everything else is bought at world prices.
    - **Reason:** GEO visibility depends on the region.
    - **Consequences:** QO-100 parts are about $35-90 deferred.
    - **Alternatives rejected:** Assuming Europe.
  24.
    - **Question:** C24 Costs and weights
    - **Decision:** Recompute with the missing-parts list: about $870-1,520 gross, about $830-1,450 net of lines already partly budgeted (mostly estimates). Sling 4.4-6.05 kg.
    - **Reason:** Cables, supports, weather parts, tools, the pack build and recovery media were never budgeted.
    - **Consequences:** The P5 analog search should include these lines.
    - **Alternatives rejected:** Keeping the old subtotals.
  25.
    - **Question:** C25 P1b completion
    - **Decision:** report_research.json now exists (minute-log 04:52). Still to do: add errata blocks to summaries.md and minute-log.md. grep finds no 'errata' in either file.
    - **Reason:** Uncorrected entries can propagate into P2 through digest.md.
    - **Consequences:** A small task before STACK.md.
    - **Alternatives rejected:** None.
  26.
    - **Question:** Lens: how chains are routed to the two RTLs and the HF+
    - **Decision:** Internal SP4T selectors on both RTLs, a latching relay pair for the HF+, and MCP23017 #3 for the extra control lines.
    - **Reason:** The one-touch menu wish needs software routing. Manual swaps would mean opening the sealed RF bay.
    - **Consequences:** $40-65. Isolation of 30-37 dB is enough for chain selection but not for an A/B leakage test.
    - **Alternatives rejected:** Manual swaps only; ZSWA4-63DR+ at $307.32 each.
  27.
    - **Question:** Lens: tripod mount implementation
    - **Decision:** An aluminium boss of 10-12 mm with a steel 1/4-20 insert, bolted to the plate.
    - **Reason:** A 2 mm plate gives only 1.57 engaged threads.
    - **Consequences:** About +15 g.
    - **Alternatives rejected:** A thread tapped in the plate; heat-set inserts in ASA.
  28.
    - **Question:** Lens: ingress target vs thermal physics
    - **Decision:** IPX4/IP54 with baffled, filtered intakes and ePTFE vents, not IP67.
    - **Reason:** The case must shed 11-32 W internal plus 13.5-17 W solar, so it needs forced air.
    - **Consequences:** Rain operation uses LOCK plus the encoder. The LNAs go in IP65 boxes.
    - **Alternatives rejected:** A sealed passive case (would overheat); no protection at all.
  29.
    - **Question:** Lens: home-base PC minimum
    - **Decision:** Any x86-64 machine with an ubuntu:22.04 / Python 3.10 container for QAIRT 2.42. A GPU (12 GB class) only for T3 training.
    - **Reason:** The QAIRT 2.42 converter is x86-64 only, and the CPU and on-device paths carry the system without a GPU.
    - **Consequences:** With no GPU, the detector is not retrained locally.
    - **Alternatives rejected:** ARM conversion; cloud training with private captures; an untested WSL2 setup as the only path.
- **Budget tables:**
  - CURRENT PER RAIL (model; 4S, cut-off 13.6 V, 90% efficiency)
  | Rail | Loads | Est. max | Protection |
  |---|---|---|---|
  | Pack 12.0-16.8 V | all | 2.61 A no-Lime peak 32 W; 4.25 A Lime peak 52 W; Pinecil 3.16 A (receiver off) | ATM 5 A (52-63%) / 7.5 A (57%); BMS 15-20 A |
  | 12 V D36V50F12 | Q6A 2.0 A, display ≤0.75 A, AUX ≤0.75 A | 3.5 A = 42 W (3.43 A input) | J21 branch 3.15 A fuse (proposal), display 1.5 A limit, AUX 0.75 A PTC |
  | LAB 5 V D36V28F5 (3.2 A) | hub 0.05, puck 0.10, HMI 0.05, HF+ ≤0.20 (unpublished), LAB port ≤1.0, 2x SAWbird+ 0.36, LNA V2 0.08, blower 0.10 | 1.94 A (61%); 0.79 A input | 2 A input fuse; TPS2553 1 A (LAB) / 250-300 mA (each LNA) |
  | LNB 13.2 V SEPIC | Bullseye 0.2-0.3 A (unpublished) | ≤4 W | 1.5-2x measured; #2813 disconnect; SMBJ15A |
  | Boni 12.5 V LDO | current unpublished | — | 0.2 A PTC (proposal) |
  - FUSE / PTC / TVS (proposal)
  | Point | Part | Rating |
  |---|---|---|
  | Pack lead | ATM mini-blade, 32 V | 5 A (no Lime) / 7.5 A (Lime), 18 AWG |
  | J21 branch | ATM | 3.15 A |
  | LAB 5 V input | ATM | 2 A |
  | Pinecil lead | inline | 5 A |
  | AUX 12 V | PTC | 0.75 A hold |
  | LNA bias (no TPS2553) | PTC | 0.35-0.5 A hold at 25 C (derates to about 0.25 A at 60-70 C) |
  | Pack node | SMBJ18A | standoff 18 V |
  | After 12 V regulator | SMBJ14A | — |
  | LNB F port | SMBJ15A | — |
  - USB PORTS AND BANDWIDTH
  | Port | Device | MB/s |
  |---|---|---|
  | Blue USB 3.1 | RTL-A (or the T7 with the Lime) | 5.12 (T7: up to 224) |
  | FE1.1s P1 | RTL-B | 5.12 |
  | FE1.1s P2 | touch | ~0 |
  | FE1.1s P3 | CH334F: HMI, puck, LAB, HF+ | 3.1 + LAB |
  | LAB USB | 2nd V4L or one instrument | 5.12 |
  FE1.1s total 13.4 MB/s, 38% of 35 MB/s. Spare ports: 0.
  - CONTROL LINES
  | Group | Out | In |
  |---|---|---|
  | LAB/AUX EN, 3 VBUS cuts | 5 | 1 |
  | 4 bias EN plus FAULT | 4 | 4 |
  | LNB EN/PG, Boni EN/FAULT | 2 | 2 |
  | HF+ relay set/reset, 2x SP4T V1/V2 | 6 | 0 |
  | Total | 17 | 7 = 24 lines, against 16 on MCP23017 #1, so add #3 (0x22) |
  - POWER AND RUNTIME (register figures, models)
  | Mode | W | h on 72 Wh at 85% |
  |---|---|---|
  | No Lime, single RTL | 11-17 | 3.6-5.6 |
  | QO-100 or dual RTL | 13-21 | 2.9-4.7 |
  | No-Lime peak | 24-32 | 1.9-2.6 |
  | Lime typical | 25-28 | 2.2-2.4 |
  | Lime peak | 45-52 | 1.2-1.4 |
  - RAM (12 GB board, about 11 GiB visible (unverified); app sizes are estimates)
  | Item | No Lime | Lime |
  |---|---|---|
  | OS + labwc + Lab Shell | 1.5-2 | 1.5-2 |
  | SatDump / SDRangel / OWRX+ | 1.3-2.5 | 1.3-2.5 |
  | Ring | ≤1.5 | 4 |
  | inferd-htp + cpu | 1.3 | 1.3 |
  | Trainer | ≤2 | ≤2 |
  | Total | 7.6-9.3 | 10.1-11.8 (tight) |
  - CPU
  | Cores | Use |
  |---|---|
  | CPU0-3 A55 | UI, daemons, NPU host, ORT fallback |
  | CPU4-6 A78 2.4 GHz | DSP, labrx, T2 between passes |
  | CPU7 A78 2.7 GHz | lime:Rx0 only with the Lime, otherwise free |
  - STORAGE (UFS 128 GB, estimates)
  | Item | GB |
  |---|---|
  | OS, apps, venvs, QAIRT runtime | 20-28 |
  | NPU dataset quota | 20 |
  | Offline map tiles (not budgeted in any file) | 2-10 |
  | Models, journald | 0.4 |
  | Left for recordings | 62-78, i.e. 1.7-2.1 h of dual-RTL raw at 36.9 GB/h |
  - CARRIED WEIGHT (sling, model)
  | Item | kg |
  |---|---|
  | Handheld (no Lime) | 1.05-1.25 |
  | Foldable kit + LNB + LNAs + jumpers | 1.3-1.8 |
  | HF wire kit | 0.4 |
  | 2 L pouch | 0.8 |
  | Tripod + mast | 0.35-0.9 |
  | Coax set | 0.15-0.3 |
  | Bag | 0.3-0.5 |
  | Weather kit | 0.05-0.1 |
  | Total | 4.4-6.05 (5.0-6.7 with the PD bank) |
  - CABLE SCHEDULE (proposal; prices are estimates)
  | Run | Type | Length | Qty |
  |---|---|---|---|
  | Bulkhead to internal (137, 2 m, 70 cm, L-band, HF, VHF-AIS) | SMA-F bulkhead to SMA-M RG316 | 10-15 cm | 6 |
  | LNB port | F-F bulkhead + 75 ohm lead to the tee | 10 cm | 1 |
  | GNSS external | IPX to SMA-F bulkhead | 10 cm | 1 |
  | V4L USB | A-M to A-F + ferrite | 15 cm | 2 |
  | FE1.1s P3 to CH334F | A-M to C-M, VBUS cut | 10 cm | 1 |
  | CH334F pads | panel USB-A / HF+ plug / RP2040 USB-C / puck GX12 | 5-15 cm | 4 |
  | Touch | USB with VBUS cut | 15 cm | 1 |
  | HDMI | shielded micro-coax + Mix 31/61 | 10-15 cm | 1 |
  | Feed LNA to handheld | RG316 SMA-M/M (about 0.5 dB/m at 137 MHz, 1.3 dB/m at 1.7 GHz, after the LNA) | 1-2 m | 4 |
  | LNB | 75 ohm thin F-F | 1 m | 1 |
  | HF | RG174 + Mix 31 clamps (in the HF kit) | 5-10 m | 1 |
  | Boni-Whip | BNC lead + BNC-SMA + DC lead | 1-2 m | 1 each |
  | Adapters | SMA M-M (A-V85), F-SMA, SMA barrels | — | set |
  | EDL | USB 3 A-A | 1 m | 1 |
  - MISSING-PARTS COST (USD, mostly estimates)
  | Group | $ |
  |---|---|
  | Selectors, expander, current monitors, bias board | 61-121 |
  | LNB SEPIC + disconnect | 40-50 |
  | Filters (2nd Flamingo+, filter bank) + pads | 102-117 |
  | Cables and adapters | 90-170 |
  | Panel connectors, power key | 23-45 |
  | Pack cells, sundries, welding, ISDT 608PD ($32.99-42.99) | 103-148 |
  | Protection parts | 13-25 |
  | Mechanical and thermal consumables | 55-105 |
  | Weather kit | 45-110 |
  | Supports | 55-150 |
  | Bags and antenna spares | 68-113 |
  | Tools | 80-140 |
  | Flashing media | 40-55 |
  | HMI, audio, puck | 35-80 |
  | Wall PD charger | 35-60 |
  | Total | about 870-1,520 gross (about 830-1,450 net) |
  Optional: GPU EUR 298 to about $500; spare Q6A $189.99; print service $30-80.
  - HOME-BASE PC
  | Need | Minimum | Recommended |
  |---|---|---|
  | CPU/OS | any x86-64; ubuntu:22.04 container, Python 3.10 (untested) | same |
  | GPU | none (conversion only) | 12 GB NVIDIA (RTX 3060 class) |
  | RAM | 16 GB | 32-64 GB |
  | Disk | 50 GB free | 1-2 TB NVMe + 2-4 TB backup |
  | Link | Wi-Fi | GbE to the device (needs RJ45 access on the case) |
- **Checks passed:**
  - The core lab RF accessories are specified with verified prices in radio_lab.final.lab_bom[5]-[12]: Nooelec pad kit $47.95, 2x BLK-89-S+ at $20.26, 3x ANNE-50+ at $14.84, 086-6SM+ at $16.67, OSL, torque wrench $35.89.
  - The LAB 5 V rail fits the D36V28F5: 1.94 A of 3.2 A (model), drawing 0.79 A at the input against its 2 A fuse.
  - The 12 V rail load of 3.5 A (42 W) sits within the D36V50F12's published 2.3-6.5 A range. A sealed-case test is still required.
  - Pack fuse loading is reasonable (model): 7.5 A runs at 57% at the 52 W Lime peak; 5 A runs at 52% at the 32 W no-Lime peak and 63% with the Pinecil.
  - USB 2.0 tree load is 13.4 MB/s, 38% of the practical 35 MB/s, even with a second V4L on LAB USB.
  - A spares kit exists (radio_lab lab_bom[23], $80-130): fuses, XT30, SMBJ14A, a spare IP2368, CR2032, RP2040-Zero, pigtails, barrels, a DC block, M2.5 hardware, thermal pads, Kapton.
  - Bench tools and ESD control are covered: Mako kit, cutters, stripper, ESD mat, Pinecil with a 5 A fused lead and IronOS Bluetooth off.
  - The transport case is specified: Pelican 1450, interior 37.1x25.8x15.2 cm, with the 35 cm Yagi pieces fitting. The PD bank and the back-power-protected bench hub are covered.
  - Cooling hardware is specified: Armor case or copper block, NF-A4x10 5V PWM, a 5 V blower, AO3400 drive. The printed sun hood, IR film and light bezel are in mechanical.
  - The QAIRT 2.42 host requirement (x86-64, Ubuntu 22.04, Python 3.10) is consistent across npu_training and the register.
  - New world prices this session: P50B EUR 6.75 incl. VAT at NKON (31 Jul 2026); ISDT 608PD $32.99-42.99; Radxa RA019-E1U1 reader EUR 13.00 at TinyTronics. These replace UAH-only or stale prices.
  - The Waveshare LC76G ships with an active ceramic antenna and has an MS621FE backup cell, so the lid-patch option needs no extra antenna.
- **Notes:** I read user_requirements.md and the full register in report_research.json: summary, 143 decisions, compliance, corrections, the 25 conflicts and the open questions. I also read the verdict notes and the cross-system conflicts. For my lens I read radio_lab.final (lab_bom, totals, usb_power_case_plan, connections, stack_changes), the foldable kit, totals and steps, small_antenna_stack.revised_stack, and the power, mechanical, GNSS, display and NPU hardware sections. I grepped all final/*.json files for about 60 part terms.
  
  Main finding: the studies cover instruments and the main modules well. What is missing is the layer between them:
  - Input routing and its control lines.
  - Correctly rated bias tees.
  - A buck-boost LNB supply. On 4S, every boost option named in the files is wrong.
  - A cable and adapter schedule.
  - A filter matrix with a real 2 m path.
  - The pack-building process, supports, weather protection, tools, bags, recovery media and the home-base PC.
  
  Web use was 10 searches and 4 fetches. Many accessory prices are still estimates and are marked as such.
  
  Unverified:
  - HF+ Discovery USB connector type.
  - S18V20AHV price.
  - HMC7992 board logic levels.
  - Bias-tee and relay parts beyond the TCBT-14+ 200 mA rating.
  - RTX 3060 October prices (latest data is July 2026: EUR 298 in France to about $500 at US retail).
  - Container use for QAIRT 2.42.
  
  Calculation scripts: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/missing_calc/b.py and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/missing_calc/cost.py. All their outputs are models.
  
  Sources:
  - https://www.adafruit.com/product/5997
  - https://www.pololu.com/product/2577
  - https://www.nkon.nl/rechargeable/molicel-inr21700-p50b-5000mah-50a.html
  - https://racedayquads.com/products/isdt-608pd-240w-10a-1-6s-dc-smart-charger-black
  - https://www.tinytronics.nl/nl/data-opslag/modules/radxa-ufs-emmc-naar-usb-3.0-lezer-module
  - https://www.minicircuits.com/pdfs/TCBT-14+.pdf
  - https://www.datasheets.com/radiall/r570342100
  - https://www.guru3d.com/story/geforce-rtx-3060-12gb-prices-reportedly-jump-after-relaunch/
  - https://gpuprix.com/zh/france/gpus/geforce-rtx-3060-12gb
  - https://www.waveshare.com/LC76G-GNSS-Module.htm
  - https://anatechelectronics.com/435-mhz-band-pass-filter-9531.html
  - https://www.newegg.com/p/3C6-00V6-02DG1</notes>
  </invoke>
  

## sourcing:group2 (run `wf_b9cc0186-94e`)

- **Group:** SDR + RF FRONT END + ANTENNAS (final verified picks; loops, H-field probes, YouLoop, VNA antenna sweeps and the 18 V LNB branch are excluded by the user's rules)
- **Offers:**
  1.
    - **Item:** RTL-SDR Blog V4L (Lite) R828S RTL2832U 1 ppm TCXO SMA, dongle only (buy 3: RTL-A, RTL-B, 1 spare)
    - **Seller:** RTL-SDR Blog official store (rtl-sdr.com)
    - **Url:** https://www.rtl-sdr.com/product/rtl-sdr-blog-v4l-lite-r828s-rtl2832u-1ppm-tcxo-sma-software-defined-radio-dongle-only/
    - **Price:** USD 37.95 each (3 = USD 113.85)
    - **Price usd:** 37.95
    - **In stock:** yes, 455 in stock (18 Oct 2026)
    - **Ships to:** Worldwide from the China warehouse, free economy shipping or paid express. Not to RU/BY or sanctioned countries. The webstore does not ship to the EU directly: EU buyers use the official eBay (rtl-sdr-blog) or AliExpress 'RTLSDRBlog Store' no. 4523039, or a listed reseller.
    - **Official channel:** так
    - **Notes:** HIGH clone risk. Blue/green cases, square silver 4-screw cases and 'Pro' labels are fakes, so buy only from the official store, eBay or AliExpress store, or a listed reseller. The R828S is end of life, so buy all 3 now. Amazon USA had not stocked it yet. Needs the patched librtlsdr .so.2.
  2.
    - **Item:** Airspy HF+ Discovery
    - **Seller:** ITEAD Studio (Airspy's official manufacturing partner)
    - **Url:** https://itead.cc/product/airspy-hf-discovery/
    - **Price:** USD 169.00
    - **Price usd:** 169.00
    - **In stock:** add-to-cart active; no stock count shown
    - **Ships to:** EU warehouse (3-6 days, card only); US warehouse (3-6 days); rest of world from China (15-35 days standard, 4-10 days expedited)
    - **Official channel:** так
    - **Notes:** MEDIUM clone risk. Buy only from the dealers listed at airspy.com/purchase: ITEAD, RTL-SDR.com (Amazon), WiMo, Moonraker, Ham Shop NL, FB Radio, AstroRadio, Neven, SDR UA (Ukraine only), AOR Japan. Its current draw is unpublished, so measure it.
  3.
    - **Item:** Airspy HF+ Discovery
    - **Seller:** AstroRadio, Barcelona (official Airspy dealer)
    - **Url:** https://www.astroradio.com/p/airspy_hf_discovery/
    - **Price:** EUR 214.17
    - **Price usd:** 248.44
    - **In stock:** not shown
    - **Ships to:** Spain/EU
    - **Official channel:** так
    - **Notes:** EU price including VAT. Converted at 1.16 USD/EUR.
  4.
    - **Item:** Airspy HF+ Discovery (SKU 10-201)
    - **Seller:** Moonraker (official Airspy dealer, UK/EU/US storefronts)
    - **Url:** https://moonrakeronline.com/eu/airspy-hf-plus-discovery-high-peformance-sdr-receiver
    - **Price:** EUR 231.99 (EU page) / USD 223.95 (US page, moonrakeronline.com/us/...)
    - **Price usd:** 223.95
    - **In stock:** 'in stock' per search snippet only; the page returned 403
    - **Ships to:** UK/EU (duty and tax paid at checkout) and US
    - **Official channel:** так
    - **Notes:** Search snippet only, so treat as unconfirmed.
  5.
    - **Item:** LimeSDR Micro M.2 2280 Basic (no GNSS); GATED OPTIONAL, cancellable pre-order
    - **Seller:** Crowd Supply (Lime Microsystems' official channel)
    - **Url:** https://www.crowdsupply.com/lime-micro/limesdr-micro
    - **Price:** USD 249 + shipping USD 8 (US) / USD 18 (worldwide) = USD 267 worldwide
    - **Price usd:** 267.00
    - **In stock:** pre-order; estimated ship date 15 Dec 2026
    - **Ships to:** Worldwide (USD 18). Buyer pays import VAT/duty.
    - **Official channel:** так
    - **Notes:** The GNSS variant is USD 299 and is not wanted. The listing has no 2230 variant, so the 80 mm card needs a support post or a riser in the Q6A 2230 M-key socket. The last campaign update was 17 Jun 2026. Store pre-orders are refundable before shipment.
  6.
    - **Item:** MHF4L to SMA(f) bulkhead coax cable, 100 mm (2x, only if the Lime is kept)
    - **Seller:** Crowd Supply (Lime accessory)
    - **Url:** https://www.crowdsupply.com/lime-micro/limesdr-micro
    - **Price:** USD 6 each (2 = USD 12), same shipping as the Lime order
    - **Price usd:** 6.00
    - **In stock:** yes (listed as in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Order with the Lime to share shipping. Label the pigtails X2/X4.
  7.
    - **Item:** ADT-Link R44SF M.2 NVMe M-key male-to-female extender, 5 cm (M.2 riser, only if the Lime is kept)
    - **Seller:** ADT-Link (manufacturer webshop)
    - **Url:** http://www.adt.link/product/R44SF.html
    - **Price:** USD 19.00 (5 cm); 3 cm USD 21, 10 cm USD 19
    - **Price usd:** 19.00
    - **In stock:** not shown (order via webshop R44-Shop.html or adt-sales@adt.link)
    - **Ships to:** From China; PayPal accepted. Destinations not listed.
    - **Official channel:** так
    - **Notes:** PCIe 3.0 x4 rated, which covers the Lime's Gen3 x1/x2. Third-party Newegg R44SF 4.0 listings are USD 39.99+ (20 cm) and are not official. Check whether it connects the M.2 SMBus pins (host-freeze risk).
  8.
    - **Item:** I-PEX 90435-001 MHF4 mating/unmating tool (only if the Lime is kept)
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=90435-001
    - **Price:** USD 18.10
    - **Price usd:** 18.10
    - **In stock:** yes, 474 (DigiKey part 5378-90435-001-ND)
    - **Ships to:** Worldwide (DigiKey international)
    - **Official channel:** так
    - **Notes:** Lime-only item.
  9.
    - **Item:** RTL-SDR Blog Wideband LNA V2 (QPL9547, bias-tee powered, 100 MHz-6 GHz)
    - **Seller:** RTL-SDR Blog official store
    - **Url:** https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
    - **Price:** USD 19.95
    - **Price usd:** 19.95
    - **In stock:** yes, 208 in stock
    - **Ships to:** Worldwide from China; Amazon USA in stock
    - **Official channel:** так
    - **Notes:** The vendor's buy page lists 3-5 V at 90 mA. That is above the register's 80 mA V4L-tee rule; see the notes for the decision. The radio_lab core spare adds a second unit.
  10.
    - **Item:** Nooelec SAWbird+ GOES, enclosed (SKU 100792; 1688 MHz, includes free aluminium enclosure)
    - **Seller:** Nooelec official store
    - **Url:** https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-goes-302.html
    - **Price:** USD 49.95
    - **Price usd:** 49.95
    - **In stock:** add-to-cart active; no stock text; ships in 1 business day
    - **Ships to:** From the USA; free worldwide shipping on orders over USD 100
    - **Official channel:** так
    - **Notes:** Use the cased version at the helix feed. 180 mA nominal, 3-5 V on the SMA. Feed it from a TPS2553 injector at 250-300 mA, never from the V4L tee. The Barebones SAWbird+ GOES is USD 44.95 (inside a shielded case only).
  11.
    - **Item:** Nooelec SAWbird+ iO, enclosed (SKU 100788; 1542 MHz, 60 MHz passband, 30 dB or more)
    - **Seller:** Nooelec official store
    - **Url:** https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-io-303.html
    - **Price:** USD 49.95
    - **Price usd:** 49.95
    - **In stock:** add-to-cart active; no stock text
    - **Ships to:** From the USA; free worldwide shipping over USD 100
    - **Official channel:** так
    - **Notes:** 180 mA nominal; TPS2553 injector. Used for Inmarsat-C EGC SafetyNET only, with header-level discard. The non-plus iO Barebones is USD 39.95.
  12.
    - **Item:** Nooelec Flamingo+ FM v2 broadcast FM band-stop (SKU 100813) - THE FM filter
    - **Seller:** Nooelec official store
    - **Url:** https://www.nooelec.com/store/flamingo-plus-fm.html
    - **Price:** USD 24.95
    - **Price usd:** 24.95
    - **In stock:** add-to-cart active; no stock text
    - **Ships to:** From the USA; free worldwide shipping over USD 100
    - **Official channel:** так
    - **Notes:** Over 60 dB average rejection; under 0.25 dB loss out of band; 250 mA minimum DC pass. Fitted permanently in the 137/145 MHz path. An SMA M-M barrel is included.
  13.
    - **Item:** RTL-SDR Blog Broadcast FM Band-Stop Filter (alternative only, not the pick)
    - **Seller:** RTL-SDR Blog official store
    - **Url:** https://www.rtl-sdr.com/product/rtl-sdr-blog-broadcast-fm-band-stop-filter/
    - **Price:** USD 16.95
    - **Price usd:** 16.95
    - **In stock:** yes, 131 in stock
    - **Ships to:** Worldwide from China; Amazon USA
    - **Official channel:** так
    - **Notes:** Over 50 dB rejection, under 0.5 dB loss to 1 GHz, no published DC rating. Not bought, because the standard is the Flamingo+.
  14.
    - **Item:** Nooelec SMA in-line DC block (2 W maximum)
    - **Seller:** Nooelec official store
    - **Url:** https://www.nooelec.com/store/dc-block.html
    - **Price:** USD 24.95
    - **Price usd:** 24.95
    - **In stock:** add-to-cart active
    - **Ships to:** From the USA; free worldwide over USD 100
    - **Official channel:** так
    - **Notes:** Its frequency and voltage ratings are not shown, so VNA-check it (conducted) on arrival. Mini-Circuits BLK-89-S+ is the better-specified choice.
  15.
    - **Item:** Mini-Circuits BLK-89-S+ DC block, SMA-F/SMA-M (2x in the core set)
    - **Seller:** Mini-Circuits webstore
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=BLK-89-S%2B
    - **Price:** USD 20.26 each (qty 1)
    - **Price usd:** 20.26
    - **In stock:** yes, more than 1,000 at Mini-Circuits (DigiKey 0)
    - **Ships to:** Mini-Circuits ships internationally, subject to export screening
    - **Official channel:** так
    - **Notes:** Matches the register's core accessory set (2x).
  16.
    - **Item:** Mini-Circuits BLK-18-S+ DC block, SMA-F/SMA-M (higher-frequency alternative)
    - **Seller:** Mini-Circuits webstore
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=BLK-18-S%2B
    - **Price:** USD 29.73
    - **Price usd:** 29.73
    - **In stock:** yes, more than 1,000
    - **Ships to:** International
    - **Official channel:** так
    - **Notes:** Use only if a block rated above 8 GHz is wanted. Not needed: the highest SDR-side frequency is the 739 MHz LNB IF or 2.2 GHz.
  17.
    - **Item:** Mini-Circuits TCBT-2R5G+ surface-mount bias tee (20 MHz-2.5 GHz), for the DIY 5 V LNA injectors in the shielded bay (3x)
    - **Seller:** DigiKey (3157-TCBT-2R5G+CT-ND)
    - **Url:** https://www.digikey.com/en/products/result?keywords=TCBT-2R5G%2B
    - **Price:** USD 11.31 each (qty 1, cut tape)
    - **Price usd:** 11.31
    - **In stock:** yes, 1,350 at DigiKey; Mini-Circuits 71 (its minimum order there is 10 at USD 9.05)
    - **Ships to:** Worldwide (DigiKey)
    - **Official channel:** так
    - **Notes:** Meets the register's 'injector rated down to about 100 MHz' requirement (20 MHz low edge), unlike generic 10 MHz-6 GHz boxes that lose 3-7 dB at 100-200 MHz. Check the datasheet DC current limit against 180 mA SAWbird+ loads and against the measured Bullseye current if used for the LNB.
  18.
    - **Item:** Mini-Circuits ZFBT-4R2GW+ connectorized bias tee, SMA (premium LNB / VHF injector option)
    - **Seller:** Mini-Circuits webstore
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=ZFBT-4R2GW%2B
    - **Price:** USD 111.57
    - **Price usd:** 111.57
    - **In stock:** yes, more than 100 at Mini-Circuits (DigiKey 0)
    - **Ships to:** International
    - **Official channel:** так
    - **Notes:** radio_lab dropped the ZFBT from its core set. Only worth it as a ready-made, characterised LNB injector; confirm the datasheet DC voltage/current rating against 13.2 V and the measured LNB draw. ZFBT-6GW+ is USD 125.54 (5 in stock) and not needed.
  19.
    - **Item:** Othernet QO-100 Bullseye TCXO LNB
    - **Seller:** RTL-SDR Blog official store
    - **Url:** https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
    - **Price:** USD 29.95
    - **Price usd:** 29.95
    - **In stock:** yes, 70 in stock
    - **Ships to:** Worldwide from China; also an Amazon UK/EU reseller
    - **Official channel:** так
    - **Notes:** HOLD until the region is known to be inside the QO-100 footprint. It needs 11.5-14 V for vertical: the plan supplies 13.2 V with true disconnect and no 18 V branch. Supply current, length and neck size are unpublished, so measure them on arrival before building the horn.
  20.
    - **Item:** Bullseye Ultra High Stability Single LNB for QO-100, 2 ppm TCXO (code LNBBullseye)
    - **Seller:** Technofix UK (official RTL-SDR Blog reseller)
    - **Url:** https://shop.technofix.uk/bullseye-ultra-high-stability-single-lnb-for-qo-100-2ppm-tcxo
    - **Price:** GBP 31.99 incl. UK VAT
    - **Price usd:** 42.87
    - **In stock:** OUT OF STOCK
    - **Ships to:** UK; non-UK buyers may owe import tax/duty
    - **Official channel:** так
    - **Notes:** Confirms a 'universal 40 mm LNB fixing', so the horn's 40.2 mm collar is consistent. Converted at 1.34 USD/GBP.
  21.
    - **Item:** RTL-SDR Blog Multipurpose Dipole Antenna Kit (foldable 137 MHz V-dipole; also AIS/sonde/ADS-B arms)
    - **Seller:** RTL-SDR Blog official store
    - **Url:** https://www.rtl-sdr.com/product/rtl-sdr-blog-multipurpose-dipole-antenna-kit/
    - **Price:** USD 17.95
    - **Price usd:** 17.95
    - **In stock:** yes, 357 in stock
    - **Ships to:** Worldwide from China (Amazon USA stock unclear)
    - **Official channel:** так
    - **Notes:** Contents: base with 60 cm RG174, 2x telescopics 23 cm-1 m, 2x 5-13 cm, 3 m RG174 extension, flexible tripod, suction mount. A second kit is the only official source of spare telescopic elements.
  22.
    - **Item:** RTL-SDR Blog Active L-band Patch Antenna (1525-1660 MHz RHCP, SAW filtered; Inmarsat-C / GNSS patch tier)
    - **Seller:** RTL-SDR Blog official store
    - **Url:** https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
    - **Price:** USD 59.95
    - **Price usd:** 59.95
    - **In stock:** in stock (Amazon USA and China warehouse, per the buy page)
    - **Ships to:** Worldwide from China; Amazon USA
    - **Official channel:** так
    - **Notes:** 3.3-5 V at 20 mA, so the V4L tee is fine. It does not cover HRPT (1.7 GHz) or L5. The product URL returned 404, so the price and stock come from the official buy page.
  23.
    - **Item:** Waveshare GNSS L1+L5 dual-frequency active antenna, SMA-J (SKU 25346, 'GPS External Antenna (D)')
    - **Seller:** Waveshare official store
    - **Url:** https://www.waveshare.com/gps-external-antenna-d.htm
    - **Price:** USD 16.99
    - **Price usd:** 16.99
    - **In stock:** add-to-cart active; no stock indicator
    - **Ships to:** Worldwide except IR/KP/CU/SD/SY
    - **Official channel:** так
    - **Notes:** The GNSS-SDR / EGNOS patch for the V4L: L1/E1/B1 plus L5/E5a/B2a, 2 dBi, 28 dB LNA, 3-18 V at 20 mA or less (V4L tee OK), 50x50x19 mm, 3 m RG174. Budget pick.
  24.
    - **Item:** u-blox ANN-MB5 multi-band active GNSS antenna L1/L5 (SparkFun GPS-25071)
    - **Seller:** SparkFun
    - **Url:** https://www.sparkfun.com/u-blox-multi-band-active-gnss-antenna-l1-l5-ann-mb5.html
    - **Price:** USD 42.50
    - **Price usd:** 42.50
    - **In stock:** yes, in stock
    - **Ships to:** US; SparkFun ships internationally
    - **Official channel:** так
    - **Notes:** Higher-grade L1/L5 alternative (L1 1559-1608 MHz, L5 1164-1186 MHz), 3 m RG174, SMA. Core Electronics AU sells it at AUD 73.55.
  25.
    - **Item:** Nooelec Balun One Nine v2, enclosed (9:1 HF balun/unun)
    - **Seller:** Nooelec official store
    - **Url:** https://www.nooelec.com/store/balun-one-nine-v2.html
    - **Price:** USD 26.95 (v2 Barebones USD 21.95; old v1 USD 15.95)
    - **Price usd:** 26.95
    - **In stock:** listed (search result); stock not shown
    - **Ships to:** From the USA; free worldwide over USD 100
    - **Official channel:** так
    - **Notes:** For the HF wire, HF only. It is a DC short, so labd locks bias off. LF time signals go to the Boni-Whip.
  26.
    - **Item:** Bonito Boni-Whip active E-field whip, 10 kHz-300 MHz, BNC (WiMo item 18067; includes its bias-tee power crossover)
    - **Seller:** WiMo (Germany, official Bonito dealer)
    - **Url:** https://www.wimo.com/es/18067
    - **Price:** EUR 159.00 incl. VAT (EUR 133.61 net) plus shipping
    - **Price usd:** 184.44
    - **In stock:** no; available from 20 Nov 2026
    - **Ships to:** EU and international (WiMo)
    - **Official channel:** так
    - **Notes:** 9-15 V supply, about 14 cm, 189 g. Feed 12.5 V from the LDO on the 4S pack. Current unpublished, so measure it. The net price (USD 155) applies to buyers outside the EU. Converted at 1.16 USD/EUR.
  27.
    - **Item:** Bonito Boni-Whip active antenna (SKU 34-010)
    - **Seller:** Moonraker (UK/EU/US storefronts)
    - **Url:** https://moonrakeronline.com/us/bonito-boni-whip-active-antenna
    - **Price:** USD 123.95 sale (US page) / EUR 127.27 (EU page) / GBP 109.95 (UK page)
    - **Price usd:** 123.95
    - **In stock:** unknown (search snippet only; page 403)
    - **Ships to:** UK, Eurozone (DPD, duties included), US
    - **Official channel:** так
    - **Notes:** Moonraker gives the length as 17 cm (WiMo says 14 cm). Unconfirmed snippet; cheaper than WiMo if live.
  28.
    - **Item:** Tecsun AN-05 FM/SW reel antenna with clip, 7.0 m (HF wire reel)
    - **Seller:** Moonraker
    - **Url:** https://moonrakeronline.com/us/an-05-fm-sw-reel-antenna-with-clip
    - **Price:** USD 14.49 sale (US page) / EUR 15.41 (EU) / GBP 12.95 (UK)
    - **Price usd:** 14.49
    - **In stock:** unclear: the page shows both 'In stock' and 'Out of stock' (search snippet; page 403)
    - **Ships to:** UK/EU/US
    - **Official channel:** ні
    - **Notes:** Retailer, not Tecsun-official. An eBay.de UK seller had GBP 14.94 (2 left, Aug 2025 listing). The alternative is 10-15 m of wire on a winder of 20 cm or less.
  29.
    - **Item:** Mini-Circuits 086-24SM+ hand-flex 0.086 in coax jumper, SMA-SMA, 24 in (61 cm)
    - **Seller:** Mini-Circuits webstore
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=086-24SM%2B
    - **Price:** USD 24.73 (qty 1-9)
    - **Price usd:** 24.73
    - **In stock:** yes, 356
    - **Ships to:** International
    - **Official channel:** так
    - **Notes:** Quality short lead for the helix/LNA feed and the bench. 086-6SM+ (USD 16.67, per the register) for internal jumpers.
  30.
    - **Item:** RTL-SDR Blog SMA pigtail adapter set (6 pcs); SMA straight adapter set (6 pcs); semi-rigid RG402 SMA adapter set (10 pcs)
    - **Seller:** RTL-SDR Blog official store
    - **Url:** https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
    - **Price:** USD 18.95 / USD 14.95 / USD 26.95
    - **Price usd:** 18.95
    - **In stock:** yes (Amazon USA and China warehouse)
    - **Ships to:** Worldwide from China; Amazon USA
    - **Official channel:** так
    - **Notes:** Covers the SMA/F/BNC adapters the chains need, such as BNC for the Boni-Whip and an F-SMA for the LNB IF (check the set contents). RTL-SDR Blog sells no coax: the kits ship with RG174.
  31.
    - **Item:** 3M 1170 aluminium foil tape with conductive adhesive, 1/4 in x 18 yd (horn gore seams)
    - **Seller:** DigiKey (3M 1170-1/4"X18YD)
    - **Url:** https://www.digikey.com/en/products/result?keywords=3M%201170%20aluminum%20foil%20tape
    - **Price:** USD 35.70 (1/2 in x 15 ft: USD 46.01)
    - **Price usd:** 35.70
    - **In stock:** yes, 196
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** A distributor-grade option. Hardware-store aluminium HVAC tape plus binder clips is the cheap route (seams cost 0.2-0.5 dB either way).
  32.
    - **Item:** Analog Devices EV1HMC7992LP3D evaluation board (HMC7992 SP4T 0.1-6 GHz), the official HMC7992 board
    - **Seller:** DigiKey (505-EV1HMC7992LP3D-ND)
    - **Url:** https://www.digikey.com/en/products/result?keywords=EV1HMC7992LP3D
    - **Price:** USD 319.28
    - **Price usd:** 319.28
    - **In stock:** yes, 2
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Too expensive for the extended sled. Farnell CH lists it at CHF 249.15 (search snippet). The bare HMC7992LP3DE chip is USD 13.10 at DigiKey, which suits a DIY board in the shielded sled.
  33.
    - **Item:** Generic 'HMC7992 non-reflective SP4T RF switch module 0.1-6 GHz' board
    - **Seller:** Walmart.ca marketplace seller 'Joystore'
    - **Url:** https://www.walmart.ca/en/ip/HMC7992-Non-Reflective-SP4T-RF-Switch-Module-PCB-Material-0-1-6GHz-Frequency-Range-3V-5V-Power-Supply-45dB-Isolation-0-6dB-Insertion-Loss-58dBm-IIP3/4LT6JIAL4ULJ
    - **Price:** CAD 20.49 (was CAD 25.27)
    - **Price usd:** 14.70
    - **In stock:** unknown (search snippet; page blocked by bot check)
    - **Ships to:** Canada (marketplace)
    - **Official channel:** ні
    - **Notes:** No official maker; quality and counterfeit-chip risk. The seller claims 45 dB isolation; expect 30-37 dB. Qualify it with the conducted P1/P13 procedure (40 dB or more below 1 GHz, 30 dB or more at 1.7-2.3 GHz) before use. Converted at about 0.72 USD/CAD.
  34.
    - **Item:** Mini-Circuits ZSWA4-63DR+ absorptive SP4T 1-6000 MHz
    - **Seller:** Mini-Circuits webstore
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=ZSWA4-63DR%2B
    - **Price:** USD 307.32 (qty 1-4)
    - **Price usd:** 307.32
    - **In stock:** NO, current stock 0 (DigiKey 0); contact sales
    - **Ships to:** International
    - **Official channel:** так
    - **Notes:** Premium switch (58 dB isolation per the register). Out of stock, so the extended sled stays on a qualified HMC7992 board or manual SMA swaps.
- **Not found:**
  1.
    - **Item:** RTL-SDR Blog official AliExpress store (no. 4523039) and official eBay (rtl-sdr-blog) prices for the V4L/LNA/filters
    - **Closest equivalent:** RTL-SDR Blog webstore at USD 37.95 / 19.95 / 16.95 / 17.95 / 29.95 / 59.95
    - **Note:** The AliExpress store page rendered empty. The official buy page confirms both channels exist and that Ukraine is reachable only via AliExpress. EU buyers must use eBay/AliExpress or a reseller (WiMo, Passion Radio, Technofix, AstroRadio, etc.).
  2.
    - **Item:** Generic SMA bias-tee injector 10 MHz-6 GHz (GPIO Labs on Tindie; Passion Radio BT4G)
    - **Closest equivalent:** DIY injector on Mini-Circuits TCBT-2R5G+ (USD 11.31, DigiKey) with a TPS2553 at 250-300 mA, or Mini-Circuits ZFBT-4R2GW+ (USD 111.57)
    - **Note:** Tindie returned 403 and Passion Radio a redirect loop. Generic boxes lose 3-7 dB at 100-200 MHz, so any bought unit must be VNA-checked (conducted) at 137/145/740/1700 MHz.
  3.
    - **Item:** Horn materials: 0.3 mm aluminium or 0.2 mm brass sheet (6 gores, largest about 19.7 x 13 cm), printed 40.2 mm collar, 127/180 mm rings
    - **Closest equivalent:** Local metal or hobby supplier: K&S 0.016 in (0.4 mm) aluminium sheets exist but the common 4x10 in size is too narrow; buy 200x300 mm or larger blanks
    - **Note:** Not sourced from an official international store. Budget USD 10-20 (estimate). Ace, True Value and Hemlock list K&S 4x10 in 0.016 in aluminium at about USD 2-2.6 (US only, search snippets).
  4.
    - **Item:** Helix/helicone materials: 2 mm (12 AWG) bare copper wire (about 1.5 m per 5-turn L helix plus about 1 m for the S helix), 18 cm x 1.5 mm Al disc, 8 petals of 0.3-0.5 mm Al (blanks at least 17 x 18 cm), PETG/ASA former, SMA panel jack
    - **Closest equivalent:** Local metal and electrical supplier, or electrician's 2.5 mm2 solid copper earth wire (stripped)
    - **Note:** DigiKey, Mouser and Farnell searches failed (no results or 503). Budget USD 20-35 (foldable study estimate). Build it rigid: the spring-helix idea is refuted.
  5.
    - **Item:** Tape-measure crossed Yagi parts: 25 mm steel tape (5 m or more), 20x20 mm square PVC/GRP tube (0.7 m, cut to 5 pieces of 16 cm or less), #8 (3.26 mm) or 1/8 in aluminium rod (about 2.5 m), Axotron v3 printed spools (free 3MF), hairpin match, two SMA/BNC feeds
    - **Closest equivalent:** Local hardware store; any 1 in-blade 25 ft tape measure
    - **Note:** No official world-shipping offer verified. Budget USD 25-40 (estimate). Tune receive-only; no VNA sweep into the antenna.
  6.
    - **Item:** Chip antennas
    - **Closest equivalent:** None needed
    - **Note:** Final picks use no chip antenna for satellite links (the Johanson 433 MHz chip at -4 dBi was rejected). The LC76G board brings its own active GNSS antenna.
  7.
    - **Item:** LMR-240-class jumpers and RG316/RG174 0.5-1 m SMA leads with ferrites
    - **Closest equivalent:** Mini-Circuits 086-24SM+ (USD 24.73), the RTL-SDR Blog dipole kit's 3 m RG174, RTL-SDR Blog pigtail set (USD 18.95)
    - **Note:** A DigiKey RG316 search returned only an out-of-stock Wi-Fi antenna. Ferrite clip-ons are not sourced here.
  8.
    - **Item:** Spare telescopic element pair for the dipole kit
    - **Closest equivalent:** A second RTL-SDR Blog dipole kit, USD 17.95
    - **Note:** No separate official listing seen.
  9.
    - **Item:** HF+ input selector relay (HF / VHF / 50 ohm, latching, DC-capable)
    - **Closest equivalent:** Part still TBD (a latching signal relay, measured on the LiteVNA conducted)
    - **Note:** Not in this group's list, but the AIS-on-HF+ default depends on it. Add it plus a BNC-SMA lead (USD 5-10) to the HF-chain BOM.
  10.
    - **Item:** Loop antennas (YouLoop, HF active loops, VHF loops) and H-field near-field probes
    - **Closest equivalent:** Excluded by the user's rule
    - **Note:** The RTL-SDR Blog store (USD 39.95) and AstroRadio (EUR 44.00) sell the YouLoop. It is deliberately NOT sourced.
- **Notes:** PICKS USED (latest study and verifier win): 3x RTL-SDR Blog V4L; Airspy HF+ Discovery; LimeSDR Micro M.2 2280 Basic, gated optional, plus the R44SF 5 cm riser, 2x MHF4L-SMA and the I-PEX tool only if kept; RTL-SDR Blog Wideband LNA V2; SAWbird+ GOES and SAWbird+ iO (cased); Flamingo+ FM as the single FM filter; TPS2553 injectors built on TCBT-2R5G+; 2x BLK-89-S+; Bullseye TCXO LNB bare or with gore horn; RTL-SDR Blog dipole kit as the V-dipole; tape Yagi, petal helicone and gore horn as DIY; RTL-SDR Blog active L-band patch plus a separate L1/L5 patch for GNSS-SDR; Tecsun AN-05 plus Balun One Nine v2 (HF only); Boni-Whip at 12.5 V; HMC7992 board or Mini-Circuits switch for the extended sled. Every price was seen on 18 Oct 2026. Rates: 1.16 USD/EUR, 1.34 USD/GBP, 0.72 USD/CAD.
  
  GROUP TOTAL (core, official channels, before shipping/VAT; Lime excluded): about USD 872. That is 3 V4L 113.85, HF+ 169, LNA V2 19.95, GOES+ 49.95, iO+ 49.95, Flamingo+ 24.95, Balun 26.95, Boni-Whip about 184 at WiMo, AN-05 14.49, dipole kit 17.95, L-band patch 59.95, Waveshare L1/L5 16.99, Bullseye 29.95, 2x BLK-89-S+ 40.52, 3x TCBT-2R5G+ 33.93, pigtail set 18.95. DIY Yagi, helicone and horn materials add about USD 55-95, for about USD 930-970. The SAWbird+ NOAA (USD 49.95, same Nooelec order) sits in the 137 chain but outside this list. Lime-if-kept adds USD 316 (249 + 18 shipping + 12 + 19 + 18.10).
  
  Shipping: one Nooelec order (GOES+, iO+, Flamingo+, Balun, plus NOAA+) exceeds USD 100, so worldwide shipping is free. RTL-SDR Blog ships free economy from China. ITEAD ships from EU/US/CN warehouses. Crowd Supply charges USD 18 worldwide.
  
  Clone risk: RTL-SDR HIGH (official store, eBay or AliExpress store 4523039 only; never 'V4'/'Pro'/blue cases). Airspy MEDIUM (airspy.com/purchase dealers only). Generic HMC7992 boards: quality and counterfeit risk, so qualify them conducted.
  
  Correction found: the vendor page says the LNA V2 draws 90 mA, not 80 mA or less.
  
  CONFLICT RESOLUTIONS (decision and reason):
  1. Lime: gated optional. Keep the refundable Crowd Supply store pre-order and decide on 31 Jan 2027 or on delivery. No core function depends on it, and its dependents (riser, MHF4, T7, CPU7, LIME NPU profiles, pads, REF IN, P5/P7/P14/P18) are tagged conditional. Reason: it ships 15 Dec 2026, has had no update since 17 Jun 2026, its driver is x86-validated only, and it adds only S-band and 56 Msps NPU IQ.
  2. Q6A: buy the 12 GB now (USD 189.99) and re-check Allnet stock. Reason: RAM cannot be added later, and the Lime and training options stay open.
  3. Pack: 4S1P P50B with a regulated 12 V into J21. Reason: it alone fits the 13.2 V LNB, the 12.5 V Boni-Whip LDO, AUX 12 V and the noise-source ENR.
  4. 12 V regulator: the D36V50F12 is provisional. A forced-PWM buck-boost rated 5 A or more replaces it if the terminated-floor spur A/B or the sealed-case current test fails. Reason: the choice depends on measurement.
  5. USB: freeze the Lime-agnostic map as written (blue = RTL-A, or the T7 with the Lime). The HF+ and injectors run from LAB 5 V. The Wi-Fi part is FCU760K (schematic label).
  6. Header: adopt the map as listed. The IMU uses USB-CDC through the RP2040 puck (gnss_imu final), with no BNO085 on I2C2. UART7 stays to be verified at bring-up.
  7. labd is the sole hardware owner and lock authority (rflab becomes a module). labrx owns the ring and recorder. labclassify runs inferd and fusiond. Reason: one owner prevents contention.
  8. LNB: 13.2 V ±0.2 V with true disconnect and a switch rated 20 V or more; no 18 V. One current limit at 1.5-2x the measured Bullseye draw. Reason: horizontal DATV is lost in every tier.
  9. LNA bias: every SAWbird+ runs from a TPS2553 at 250-300 mA. The V4L-tee threshold is amended to 90 mA or less, half the 180 mA tee rating, so the LNA V2 (90 mA per vendor) stays on the tee. Reason: the vendor figure, with the 2x margin kept.
  10. FM filter: Flamingo+ only (published 250 mA DC pass). Reason: the RTL-SDR Blog filter has no DC rating.
  11. librtlsdr: adopt only the noble 2.0.1 .so.2 rebuild (0204c9c + 65f0658).
  12. Display: 127.9 MHz field-mode clock, or 164.4-168.4 MHz if the panel accepts it. Reason: 128.7 MHz hits 1544.4 and 1415.7 MHz.
  13. PPS: out-of-tree pps-gpio on 6.18.2-4. Route B is dropped.
  14. INA228: on I2C0 with user-space i2c-dev, shunt in the pack lead.
  15. Antennas: the V-dipole is the LRPT default, the crossed Yagi defaults to the ultra-compact build, and all loops are struck. Small rigid pieces of 20-23 cm or less stay in the patch tier pending the user. Reason: the size rule is met.
  16. Strike every policy leftover (S11 antenna sweeps, decode-then-filter Inmarsat, VLF SID, Bluetooth and Artemis gaps, voice IQ, Set B, Iridium/CARTOSAT rows, H-probes, city list, wsjtx GUI/fldigi, bearing log). This sourcing list carries none of them.
  17. HF: Boni-Whip at 12.5 V. The 9:1 wire is HF only and LF goes to the whip. The selector relay is added to the BOM (part TBD). Confirmation of the loop removal remains a user question.
  18. Storage: the T7 only with the Lime; otherwise microSD V30/A2 or UFS A/B. Keep products by default and raw IQ only when pinned.
  19. CPU: adopt as written (A55 fallback, T2 on CPU4-6, CPU7 isolated only with the Lime).
  20. Roadmap: NPU Phase 0 in W1-2 (19 Oct-1 Nov 2026). The minimal labeller moves to P0b. HF-F and second-RTL profiles come before HF classes.
  21. Buy 3 V4L (USD 113.85, 455 in stock, R828S end of life). A 4th only for continuous ADS-B/AIS/sonde monitoring.
  22. Software: adopt the single venv-per-tool recipe and test it on the Q6A.
  23. Region: hold only the Bullseye and horn until the user is confirmed inside the QO-100 footprint. Buy the SAWbird+ iO now. Reason: Inmarsat-C EGC is broadcast in all four ocean regions (about ±75° latitude), and it lifts the Nooelec order over the free-shipping line. Stock risk: Technofix is already out of stock.
  24. Costs: the world prices above replace the estimates for this group. The extended, HF-chain and sled subtotals must be recomputed with these lines.
  25. P1b: report_research.json now exists. The summaries.md and minute-log errata blocks are still pending for the writer step.
  
  Sources (WebFetch/WebSearch, 18 Oct 2026): rtl-sdr.com buy page and product pages, itead.cc, airspy.com/purchase, astroradio.com, crowdsupply.com/lime-micro/limesdr-micro, adt.link/product/R44SF.html, nooelec.com, minicircuits.com, digikey.com, waveshare.com, sparkfun.com, wimo.com/es/18067, shop.technofix.uk. Moonraker and Walmart.ca figures come from search snippets only.

## sourcing:group1 (run `wf_b9cc0186-94e`)

- **Group:** COMPUTE + STORAGE + DISPLAY + HMI (Radxa Dragon Q6A 12 GB / 8 GB fallback, Radxa UFS 128 GB, heatsink and fan, Samsung T7 1 TB or microSD, Wisecoco 7in 2000-nit kit and 4D Systems fallback, HDMI/FPC cables, HMI RP2040, encoders, sealed keys, CH334F hub, flashing media)
- **Offers:**
  1.
    - **Item:** Radxa Dragon Q6A 12 GB (RS701-D12J0R44S32Y13W28, Wi-Fi 6/BT 5.4)
    - **Seller:** TinyTronics (Eindhoven, NL; Radxa reseller)
    - **Url:** https://www.tinytronics.nl/en/development-boards/single-board-computers/radxa-dragon-q6a-qcs6490-12gb
    - **Price:** EUR 148.00 incl. NL VAT / EUR 122.31 ex VAT
    - **Price usd:** 166.37 incl. VAT / 137.49 ex VAT
    - **In stock:** yes, 10+ pieces (18 Oct 2026)
    - **Ships to:** EU by DPD; outside the EU on request (contact form, DHL Express or own courier); UK private orders need EUR 170 ex VAT minimum
    - **Official channel:** так
    - **Notes:** New finding: cheapest in-stock 12 GB source, cheaper than Allnet. Ex-VAT price applies only if the seller exports without VAT. Run the burn-in inside the return window (decision #22).
  2.
    - **Item:** Radxa Dragon Q6A 12 GB (RS701-D12J0R44S32Y13W28, Wi-Fi 6/BT 5.4)
    - **Seller:** ALLNET China (official Radxa distributor)
    - **Url:** https://shop.allnetchina.cn/products/radxa-dragon-q6a
    - **Price:** USD 189.99
    - **Price usd:** 189.99
    - **In stock:** yes (Shopify available=true, 18 Oct 2026)
    - **Ships to:** Worldwide (the store country list covers most countries, all priced in USD)
    - **Official channel:** так
    - **Notes:** Answers the #75/#86 stock conflict: 12 GB is in stock. On the same page 8 GB is USD 159.99 (sold out) and 6 GB (Wi-Fi 5) is USD 149.99 (in stock). Shipping is added at checkout.
  3.
    - **Item:** Radxa Dragon Q6A 12 GB
    - **Seller:** Arace Tech (official Radxa store)
    - **Url:** https://arace.tech/products/radxa-dragon-q6a
    - **Price:** USD 169.00
    - **Price usd:** 169.00
    - **In stock:** no, sold out (all variants: 4 GB $95, 6 GB $115, 8 GB $139, 12 GB $169)
    - **Ships to:** Worldwide (multi-currency checkout)
    - **Official channel:** так
    - **Notes:** Cheapest list price, but not purchasable now.
  4.
    - **Item:** Radxa Dragon Q6A 12 GB (SKU E1037)
    - **Seller:** Ameridroid (US Radxa reseller; same listing is mirrored on sp-siliconpower.com)
    - **Url:** https://ameridroid.com/products/radxa-dragon-q6a
    - **Price:** USD 249.95
    - **Price usd:** 249.95
    - **In stock:** no, out of stock (6 GB $169.95, also out of stock)
    - **Ships to:** US (international shipping not verified)
    - **Official channel:** так
    - **Notes:** Most expensive of the official channels.
  5.
    - **Item:** Radxa Dragon Q6A 8 GB (fallback, only if the Lime is dropped before purchase)
    - **Seller:** TinyTronics (NL)
    - **Url:** https://www.tinytronics.nl/en/development-boards/single-board-computers/radxa-dragon-q6a-qcs6490-8gb
    - **Price:** EUR 121.00 incl. VAT / EUR 100.00 ex VAT
    - **Price usd:** 136.02 incl. VAT / 112.41 ex VAT
    - **In stock:** yes, 20+ pieces
    - **Ships to:** EU by DPD; outside the EU on request
    - **Official channel:** так
    - **Notes:** The 12 GB board at the same shop costs only EUR 27 more, which supports buying 12 GB (conflict #2).
  6.
    - **Item:** Radxa Dragon Q6A 8 GB
    - **Seller:** ALLNET China
    - **Url:** https://shop.allnetchina.cn/products/radxa-dragon-q6a
    - **Price:** USD 159.99
    - **Price usd:** 159.99
    - **In stock:** no, sold out
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** 
  7.
    - **Item:** Radxa UFS 3.1 Module 128 GB (RA022-B10J0U2)
    - **Seller:** ALLNET China
    - **Url:** https://shop.allnetchina.cn/products/high-performance-ufs-3-1-module
    - **Price:** USD 65.90
    - **Price usd:** 65.90
    - **In stock:** yes (the 64/256/512 GB modules are sold out)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** The only in-stock source at world price. Read the chip ID on arrival (0x01CE = Samsung, which is wanted).
  8.
    - **Item:** Radxa UFS 3.1 Module 128 GB (RA022-B10J0U2)
    - **Seller:** TinyTronics (NL)
    - **Url:** https://www.tinytronics.nl/en/data-storage/modules/radxa-ufs-module-128gb
    - **Price:** EUR 58.00 incl. VAT / EUR 47.93 ex VAT
    - **Price usd:** 65.20 incl. VAT / 53.88 ex VAT
    - **In stock:** no, not in stock (2-4 weeks)
    - **Ships to:** EU; outside the EU on request
    - **Official channel:** так
    - **Notes:** Could be combined with the TinyTronics 12 GB board order if the 2-4 week wait is acceptable.
  9.
    - **Item:** Radxa UFS 3.1 Module 128 GB (RA022-B10J0U2)
    - **Seller:** Arace Tech
    - **Url:** https://arace.tech/products/radxa-ufs-module
    - **Price:** USD 49.00
    - **Price usd:** 49.00
    - **In stock:** no, sold out
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** 
  10.
    - **Item:** Radxa UFS 3.1 Module 128 GB (SKU A0818)
    - **Seller:** Ameridroid (US)
    - **Url:** https://ameridroid.com/products/high-performance-ufs-3-1-module-128gb
    - **Price:** USD 89.95
    - **Price usd:** 89.95
    - **In stock:** yes
    - **Ships to:** US (international not verified)
    - **Official channel:** так
    - **Notes:** In stock, but $24 more than Allnet.
  11.
    - **Item:** Radxa Armor Case 7056A (AE036), heatsink case for the Q6A
    - **Seller:** Arace Tech
    - **Url:** https://arace.tech/products/radxa-armor-case-7056a
    - **Price:** USD 4.99
    - **Price usd:** 4.99
    - **In stock:** yes
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Allnet describes it as a passive (noiseless) case: top 70x56x15 mm. Active cooling is mandatory (#16), so add one 40 mm 5 V fan, switched at 60/50 C.
  12.
    - **Item:** Radxa Armor Case 7056A (AE036)
    - **Seller:** ALLNET China
    - **Url:** https://shop.allnetchina.cn/products/radxa-heatsink-7056a
    - **Price:** USD 9.90
    - **Price usd:** 9.90
    - **In stock:** yes
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Convenient to add to the Allnet board and UFS order.
  13.
    - **Item:** Noctua NF-A4x10 5V PWM 40x10 mm fan
    - **Seller:** The Pi Hut (UK)
    - **Url:** https://thepihut.com/products/noctua-nf-a4x10-5v-pwm-40x10mm-quiet-cooling-fan
    - **Price:** GBP 14.00 incl. UK VAT
    - **Price usd:** 18.65
    - **In stock:** yes
    - **Ships to:** UK and international
    - **Official channel:** ні
    - **Notes:** Authorized retailer, not Noctua's own store, which returned HTTP 429. It never stops on PWM (1000 rpm minimum), so on/off switch it through the AO3400 (#17).
  14.
    - **Item:** Sunon MF40100V2-1000U-A99 40x40x10 mm 5 V fan (0.094 A, 7 CFM, wire leads)
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=MF40100V2-1000U-A99
    - **Price:** USD 4.87
    - **Price usd:** 4.87
    - **In stock:** listed; the page did not clearly show stock for this exact part
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Cheapest named 40 mm 5 V fan.
  15.
    - **Item:** Adafruit 5V Square USB Fan - 4 cm (PID 6101)
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/6101
    - **Price:** USD 4.95
    - **Price usd:** 4.95
    - **In stock:** yes (in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** It has a USB plug; cut it and wire through the AO3400 switch.
  16.
    - **Item:** Samsung Portable SSD T7 1 TB (MU-PC1T0T/AM), only if the Lime is kept
    - **Seller:** Samsung US online store
    - **Url:** https://www.samsung.com/us/memory-storage/portable-ssd/portable-ssd-t7-usb-3-2-1tb-gray-sku-mu-pc1t0t-am/
    - **Price:** USD 274.99 (search-result snippet; page fetch blocked, HTTP 403)
    - **Price usd:** 274.99
    - **In stock:** unclear (the snippet shows an 'Out of stock' label that may refer to another capacity)
    - **Ships to:** US
    - **Official channel:** так
    - **Notes:** Not seen on a live page. Flash prices are high in Oct 2026: a Silicon Power 1 TB portable SSD lists at $245.97 on its own store.
  17.
    - **Item:** Samsung Portable SSD T7 1 TB Titan Gray (MU-PC1T0T/AM)
    - **Seller:** B&H Photo (US)
    - **Url:** https://www.bhphotovideo.com/c/product/1559836-REG/samsung_mu_pc1t0t_am_1tb_t7_portable_ssd.html
    - **Price:** USD 229.99 (search-result snippet; page fetch blocked)
    - **Price usd:** 229.99
    - **In stock:** in stock per the snippet
    - **Ships to:** US and international (B&H ships worldwide; not re-checked)
    - **Official channel:** ні
    - **Notes:** Large US retailer. Best Buy ($229.99, an old snapshot) and Newegg (third-party PlatinumMicro, $229.99) also appear in snippets. The /WW part number is the international SKU; buy the suffix for your region.
  18.
    - **Item:** microSD V30/A2 alternative to the T7: Silicon Power Superior 512 GB UHS-I U3 V30 A2 (SU512GBSTXDA2V20AC)
    - **Seller:** Ameridroid (US)
    - **Url:** https://ameridroid.com/products/silicon-power-512gb-superior-uhs-1u3-v30-a2-microsd-memory-card-with-adapter-not-compatible-with-switch-2
    - **Price:** USD 104.50
    - **Price usd:** 104.50
    - **In stock:** yes
    - **Ships to:** US (international not verified)
    - **Official channel:** ні
    - **Notes:** Of the official/reseller pages I checked, this is the only in-stock V30 A2 card. The 256 GB V30 A2 ($54.41) is out of stock. The 128 GB Superior is $32.63 in stock but is only A1. Q6A microSD was measured at 61 MB/s write; one forum card failed after 3-4 months, so use it only for products and snapshots, never for wideband.
  19.
    - **Item:** microSD alternative: Samsung PRO Plus 128 GB microSDXC A2 V30 (MB-MD128SA)
    - **Seller:** RS Components Austria
    - **Url:** https://at.rs-online.com/web/p/sd-karten/0566937
    - **Price:** EUR 33.58 ex VAT (search-result snippet; page blocked)
    - **Price usd:** 37.75
    - **In stock:** supply-shortage notice
    - **Ships to:** EU
    - **Official channel:** так
    - **Notes:** Coolblue DE lists EUR 59.90 incl. VAT ($67.33) and is sold out. NAND shortage: confirm the price live.
  20.
    - **Item:** Wisecoco 7in 1920x1080 LTPS IPS high-brightness panel with HDMI-in board and capacitive touch (store SKU id 4681)
    - **Seller:** Wisecoco (manufacturer's own store)
    - **Url:** https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
    - **Price:** USD 132.00 ex VAT (list price USD 135.00)
    - **Price usd:** 132.00
    - **In stock:** yes (schema.org InStock; Add to cart)
    - **Ships to:** North America, Europe, Australia and Asia by DHL/FedEx/UPS express (3-5 days), small parcel or air; shipping cost on request; payment by PayPal, T/T or Alibaba Trade Assurance
    - **Official channel:** так
    - **Notes:** The page still lists touch as I2C, gives no input voltage, says '2000+ cd/m2 typ' (2500 only in the title) and lists no package contents. Buy only after written answers on USB-HID VID:PID, bonding/AR, input V/I, the EDID and acceptance of a 127.9 MHz (51.7 Hz) mode (#74, #77). Pay by PayPal for buyer protection.
  21.
    - **Item:** 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000 (7in 1280x800, 1000 nits, bonded, GT928 capacitive touch over USB-C, 12 V)
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=4DHDMI-70-1280-800-CT-EAR-1000
    - **Price:** USD 128.95
    - **Price usd:** 128.95
    - **In stock:** yes, 13 in stock (manufacturer lead time 4 weeks)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** This fills the missing world price for the fallback (#76): about $100 less than the old UAH 9,520 (about $229) reference.
  22.
    - **Item:** 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000
    - **Seller:** 4D Systems (manufacturer's own store, Australia)
    - **Url:** https://4dsystems.com.au/products/4dhdmi-7-0
    - **Price:** USD 141.85
    - **Price usd:** 141.85
    - **In stock:** purchasable (Shopify available=true); 4D says only select models ship from stock and others may have MOQ and lead time
    - **Ships to:** Worldwide (country selector covers about 60 countries, all priced in USD)
    - **Official channel:** так
    - **Notes:** Ships with one USB cable and one HDMI cable. Choose the 'Display Tabs' variant to get the EAR mounting.
  23.
    - **Item:** Short HDMI cable: Adafruit Slim HDMI Cable 450 mm (PID 2420)
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/2420
    - **Price:** USD 9.95
    - **Price usd:** 9.95
    - **In stock:** yes (in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** The decision calls for a short shielded HDMI lead with ferrites; prefer this to an unshielded FPC. At The Pi Hut this length is discontinued (GBP 9.90); the 0.9 m is GBP 12.00 and out of stock.
  24.
    - **Item:** HDMI flat cable 30 cm (Adafruit PID 2197)
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/2197
    - **Price:** USD 3.95
    - **Price usd:** 3.95
    - **In stock:** yes (in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** The same item is GBP 3.40 ($4.53), in stock, at The Pi Hut (https://thepihut.com/products/hdmi-flat-cable-1-foot-30cm-long).
  25.
    - **Item:** DIY HDMI FPC kit: straight HDMI plug adapter (PID 3548) + 10 cm ribbon (PID 3560, $1.50) or 20 cm ribbon (PID 3561, $1.95); straight mini-HDMI plug adapter (PID 3552, $6.50) if the display board uses mini-HDMI
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/3548
    - **Price:** USD 6.50 per adapter + USD 1.50-1.95 per ribbon
    - **Price usd:** 14.50-14.95 per cable (2 adapters + 1 ribbon)
    - **In stock:** yes (all listed in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Only if case routing needs an FPC. The ribbon is unshielded, so wrap it in grounded copper tape and run the display on/off A/B test.
  26.
    - **Item:** Würth WE-STAR-TEC snap-on ferrite 74271140 (3.0 mm ID, 178 ohm at 100 MHz) for the touch, USB and display power leads
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=Wurth%20WE-STAR-TEC%20742711
    - **Price:** USD 3.91
    - **Price usd:** 3.91
    - **In stock:** yes, 541 in stock
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** A thicker HDMI lead needs a larger-ID clamp; size it to the cable you buy.
  27.
    - **Item:** HMI RP2040 board: Waveshare RP2040-Zero (no header, SKU 20187) / RP2040-Zero-M (pre-soldered header, SKU 20335)
    - **Seller:** Waveshare (manufacturer's own store)
    - **Url:** https://www.waveshare.com/rp2040-zero.htm
    - **Price:** USD 3.99 (no header) to USD 4.99 (with header)
    - **Price usd:** 3.99-4.99
    - **In stock:** both SKUs marked saleable; no stock count shown
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Buy 2 (HMI plus the spare that radio_lab lists for the IMU puck). The Pi Hut marks its RP2040-Zero listing 'Discontinued' (WAV-25506), so check Waveshare stock when ordering. Avoid unbranded AliExpress RP2040-Zero clones (flash and regulator vary).
  28.
    - **Item:** Raspberry Pi Pico RP2040 (SC0915 no headers / SC0917 with headers), fallback HMI MCU
    - **Seller:** The Pi Hut (Raspberry Pi Approved Reseller)
    - **Url:** https://thepihut.com/products/raspberry-pi-pico
    - **Price:** GBP 3.80 (no headers) / GBP 4.80 (with headers), incl. UK VAT
    - **Price usd:** 5.06 / 6.39
    - **In stock:** yes
    - **Ships to:** UK and international
    - **Official channel:** так
    - **Notes:** Larger (51x21 mm), same firmware. Adafruit PID 4864 ($4.00) is on backorder.
  29.
    - **Item:** Push-encoder (x2: tune, volume): Bourns PEC11R-4215F-S0024 (24 detents/24 PPR, push switch, 6 mm flatted shaft)
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=PEC11R-4215F-S0024
    - **Price:** USD 2.95 each (USD 2.376 at qty 10)
    - **Price usd:** 2.95
    - **In stock:** yes, 13,117 in stock
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** EC11-class part; chosen because the Alps EC11E15244G1 ($4.92) has 0 in stock (1,200 due 17 Dec 2026). Buy 3 (one spare).
  30.
    - **Item:** Main knob 35 mm for the tune encoder: Adafruit Scrubber Knob 35 mm (PID 2055)
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/2055
    - **Price:** USD 0.95
    - **Price usd:** 0.95
    - **In stock:** yes (in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Matches the 30-35 mm main knob spec. Check the fit on the 6 mm D shaft.
  31.
    - **Item:** Sealed keys (x6), premium: APEM IPR3SAD2 IP67 momentary panel pushbutton, black, SPST-NO 0.5 A/48 V, 13.6 mm cut-out
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/detail/apem-inc/IPR3SAD2/1280167
    - **Price:** USD 16.16 each
    - **Price usd:** 16.16 (six = 96.96)
    - **In stock:** yes, 5,079 in stock
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** A genuinely sealed panel key at about 12-14 mm with a defined click for gloves. Red IPR3SAD6 is $21.22 if a coloured REC key is wanted.
  32.
    - **Item:** Sealed keys (x6), budget: C&K KSC641J LFS IP67 sealed tact switch (6.2 mm SMT, 7.7 mm actuator, 340 gf) under printed caps of 12 mm or more and a case gasket
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=KSC641J%20LFS
    - **Price:** USD 0.82 each (USD 0.70 at qty 10)
    - **Price usd:** 0.82 (ten = 7.00)
    - **In stock:** yes, 30,086 in stock
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** The switch is IP67; the 12 mm key and its seal come from the case design.
  33.
    - **Item:** Adafruit CH334F Mini 4-Port USB Hub Breakout (MTT), PID 5997
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/5997
    - **Price:** USD 4.95 (USD 4.46 at 10+)
    - **Price usd:** 4.95
    - **In stock:** yes (in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** The internal hub of the frozen USB map (#5/#129). Buy 2 (one spare).
  34.
    - **Item:** Adafruit CH334F Mini 4-Port USB Hub Breakout (ADA5997)
    - **Seller:** The Pi Hut (UK)
    - **Url:** https://thepihut.com/products/adafruit-ch334f-mini-4-port-usb-hub-breakout
    - **Price:** GBP 4.80 incl. UK VAT
    - **Price usd:** 6.39
    - **In stock:** yes
    - **Ships to:** UK and international
    - **Official channel:** так
    - **Notes:** Pimoroni lists it at GBP 4.15 but out of stock (its 2-port version is in stock).
  35.
    - **Item:** Flashing/rescue microSD: ALLNET 64 GB microSDXC UHS-I (ALN-TFUHS1-64)
    - **Seller:** ALLNET China
    - **Url:** https://shop.allnetchina.cn/products/allnet-micro-sd
    - **Price:** USD 16.99
    - **Price usd:** 16.99
    - **In stock:** yes
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** For the rescue image only (boot from SD with the UFS pulled). Speed class is not stated.
  36.
    - **Item:** Flashing/rescue microSD: Official Raspberry Pi A2-class microSD 64 GB (PID 6011)
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/6011
    - **Price:** USD 12.79
    - **Price usd:** 12.79
    - **In stock:** backorder
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Cheapest branded A2 card, but not shipping now.
  37.
    - **Item:** USB Type-C microSD card reader/writer (PID 5212)
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/5212
    - **Price:** USD 6.95
    - **Price usd:** 6.95
    - **In stock:** yes (in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** For writing the rescue and golden images on the home PC.
  38.
    - **Item:** USB-A to USB-C data cable 2 m (PID 6324) for EDL flashing (edl-ng / Armbian Imager) and SPI-NOR backup
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/6324
    - **Price:** USD 2.95
    - **Price usd:** 2.95
    - **In stock:** yes, 93 in stock
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Use it only on the bench. Never connect USB-C while J21 is powered (Q5 back-feed).
  39.
    - **Item:** Radxa eMMC/UFS Module Reader (RA019, USB 3.0, UFS up to 1 TB)
    - **Seller:** ALLNET China
    - **Url:** https://shop.allnetchina.cn/products/emmc-ufs-module-reader-copy
    - **Price:** USD 12.99
    - **Price usd:** 12.99
    - **In stock:** no, sold out
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Not required. Flash the UFS in place over EDL, or boot from microSD and dd to UFS (storage known fix). Arace's RA004 ($7.90, sold out) and Ameridroid's readers ($11.95/$12.95, in stock) are eMMC-only and do not fit UFS.
- **Not found:**
  1.
    - **Item:** OKdo listing for the Radxa Dragon Q6A
    - **Closest equivalent:** TinyTronics NL (EUR 148 for 12 GB, in stock) or ALLNET China ($189.99)
    - **Note:** okdo.com returned HTTP 503 on every fetch (product and search pages).
  2.
    - **Item:** Radxa official AliExpress store listing for the Q6A
    - **Closest equivalent:** ALLNET China / Arace own stores
    - **Note:** The AliExpress search showed only third-party listings at $197.79-344.99 with unclear RAM and copy-pasted RK3568/LPDDR4 text. Decision #22 says to avoid third-party AliExpress sellers (DDR-training dead boards), so none are recorded.
  3.
    - **Item:** Samsung T7 1 TB price seen on a live official page
    - **Closest equivalent:** Search-snippet prices: Samsung US $274.99, B&H $229.99, Best Buy $229.99, CDW $194.99 advertised
    - **Note:** Samsung, B&H, Best Buy, Newegg, CDW, Geizhals, PriceSpy and idealo returned 403/503; Amazon hides the price for bots ('add to cart to see price'). Purchase is deferred to the Lime gate anyway (#72, conflict 18).
  4.
    - **Item:** Wisecoco official AliExpress store listing for the 7in 1920x1080 2000-nit HDMI kit
    - **Closest equivalent:** wisecocodisplay.com own store at $132
    - **Note:** No AliExpress listing found. Search shows eBay listings from 'Wisecoco-official-store' with conflicting HDMI/MIPI and 2000-2400 nit specs; eBay returned 403.
  5.
    - **Item:** Radxa UFS reader in stock
    - **Closest equivalent:** EDL in-place flashing with the USB-A to C cable, or boot from microSD and write the UFS
    - **Note:** RA019 is sold out at Allnet. No other official seller lists a UFS-capable reader.
  6.
    - **Item:** Noctua NF-A4x10 5V price at Noctua's own store or Amazon
    - **Closest equivalent:** The Pi Hut GBP 14.00 (NF-A4x10 5V PWM, in stock)
    - **Note:** noctua.at returned HTTP 429; Amazon hides the price.
  7.
    - **Item:** Mouser, LCSC, TME and Farnell/Newark prices for the encoders, keys, ferrites and 4D display
    - **Closest equivalent:** DigiKey (product and search pages readable)
    - **Note:** Mouser, TME and Farnell/RS block bots (403/Cloudflare); LCSC search is rendered client-side and its API returned 403.
  8.
    - **Item:** In-stock Samsung PRO Plus / PRO Endurance microSD at an official channel
    - **Closest equivalent:** Silicon Power Superior 512 GB V30 A2 at Ameridroid ($104.50, in stock)
    - **Note:** Snippets show shortage or sold-out notices (RS AT EUR 33.58 ex VAT with a shortage notice; Coolblue EUR 59.90, sold out).
- **Notes:** FX: open.er-api.com, 18 Oct 2026 00:02 UTC: 1 EUR = 1.1241 USD, 1 GBP = 1.3318 USD. Every price is a live store read on 18 Oct 2026 (Shopify JSON, Adafruit API, schema.org data or WebFetch) unless the offer says 'search-result snippet'. 8 WebSearch calls were used. Catalog dumps and parsers are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/src_cmp/ and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/shop_grep.py.
  
  KEY FINDINGS
  1. Q6A 12 GB is in stock at two official channels:
  - TinyTronics: EUR 148 incl. VAT ($166.37), or EUR 122.31 ex VAT ($137.49) if exported VAT-free.
  - ALLNET China: $189.99, ships worldwide.
  Arace ($169) and Ameridroid ($249.95) are sold out. Decision #14's '$189.99 Allnet' is therefore no longer the cheapest source. The 8 GB board is only EUR 27 cheaper at TinyTronics, which strengthens the 12 GB choice.
  2. UFS 128 GB: ALLNET ($65.90) is the only in-stock world source. Arace ($49) is sold out; TinyTronics (EUR 58) has a 2-4 week wait.
  3. The 4D fallback now has a world price: DigiKey $128.95 (13 in stock), or $141.85 from the 4D store. This closes the 'UAH-only price' gap in #76 and requirement_compliance item 6.
  4. Wisecoco is $132 ex VAT and InStock on its own store. Shipping is quoted on request (DHL/FedEx/UPS to NA/EU/AU/Asia). The listing still says touch is I2C and gives no input voltage, so keep the written-confirmation gate.
  5. HMI parts are cheap and available:
  - Bourns PEC11R-4215F-S0024 at $2.95 (the Alps EC11E is out of stock until Dec 2026).
  - Sealed keys: C&K KSC641J IP67 at $0.82 each (budget), or APEM IPR3SAD2 IP67 panel keys at $16.16 each (premium).
  - CH334F: $4.95 at Adafruit.
  - RP2040-Zero: $3.99-4.99 at Waveshare.
  6. Flash prices are high in Oct 2026: T7 1 TB about $230-275 in snippets, Silicon Power 1 TB portable $245.97, Samsung PRO Plus 128 GB in shortage. This supports deferring the T7 to the Lime gate.
  
  SUGGESTED CORE BUY (cheapest in-stock official offers, before shipping and duties), about $440:
  - Q6A 12 GB, TinyTronics: $166.37 (Allnet $189.99 instead adds about $24).
  - UFS 128 GB, Allnet: $65.90.
  - Armor Case 7056A, Arace: $4.99.
  - Sunon 40 mm 5 V fan: $4.87.
  - Wisecoco kit: $132.00.
  - Slim HDMI 45 cm: $9.95, plus 2 ferrites at $3.91.
  - RP2040-Zero: $3.99.
  - 2x PEC11R: $5.90, plus a 35 mm knob at $0.95.
  - 6x KSC641J: $4.92.
  - CH334F: $4.95.
  - 64 GB rescue microSD: $16.99.
  - USB-C card reader: $6.95.
  - USB A-C cable: $2.95.
  Variants: APEM keys instead of KSC add about $92. The T7, if the Lime is kept, adds about $230-275. Buying from two shops (TinyTronics plus Allnet) doubles shipping; an all-Allnet order (board $189.99, UFS, case $9.90, microSD) is about $283 from one seller.
  
  AUTHENTICITY AND CLONE RISK: none of the clone-prone instruments (tinySA, LiteVNA, RTL-SDR, Airspy) are in this group. Risks here:
  - Third-party AliExpress Q6A listings: overpriced, wrong specs, RMA risk.
  - Unbranded RP2040-Zero clones.
  - Wisecoco listing inconsistencies: 2000 vs 2500 nits, I2C touch.
  - The T7 /AM vs /WW regional SKUs.
  
  CONFLICTS_FOR_FINAL_CHECKS (decision; reason):
  1. Lime: gated optional, decide on 31 Jan 2027 or on delivery; nothing in this group depends on it except the T7 (deferred).
  2. RAM: buy 12 GB now (TinyTronics EUR 148, or Allnet $189.99 for non-EU delivery); RAM cannot be added later. One budget: 4 GiB ring with the Lime, 1.5 GiB or less without it.
  3. Pack: 4S1P P50B with a regulated 12 V rail; fixes the LNB, Boni-Whip and J21 topologies.
  4. 12 V regulator: choose after the spur A/B and sealed-case current test; neither candidate is proven.
  5. USB map: freeze the Lime-agnostic map, using Adafruit CH334F #5997 (buy 2) for H1-H4.
  6. Header map: adopt the proposed map, with the HMI RP2040 on UART7 and a CH334F port as fallback; RP2040-Zero or Pico both fit.
  7. labd is the sole hardware owner; one lock authority prevents conflicts.
  8. LNB: 13.2 V ±0.2 V, true disconnect, no 18 V, one current limit at 1.5-2x the measured draw.
  9. LNA bias: TPS2553 at 250-300 mA for every SAWbird+; the V4L tee only for loads of 80 mA or less.
  10. FM filter: Flamingo+ FM (published 250 mA DC pass).
  11. librtlsdr: only the .so.2 rebuild of noble 2.0.1, which keeps the SONAME.
  12. Display: field mode at about 127.9 MHz; the Wisecoco purchase is gated on written acceptance of that mode plus the HID/bonding answers; 4D fallback at $128.95 DigiKey.
  13. PPS: out-of-tree pps-gpio on 6.18.2-4 (CONFIG_PPS=y); keeps the kernel hold.
  14. INA228: I2C0 with i2c-dev, shunt in the pack lead; no DT conflict.
  15. Antenna tiers: re-decide under the two-tier rule, strike loop leftovers (user rule).
  16. Policy leftovers: strike all before STACK.md (hard rules).
  17. HF chain: Boni-Whip at 12.5 V; meets both published supply ranges.
  18. Storage: T7 only with the Lime; otherwise UFS plus a V30/A2 microSD for products. Buy only the 64 GB rescue card now because of NAND prices.
  19. CPU: adopt the register allocation; it is the measured-plan default.
  20. Roadmaps: run NPU Phase 0 inside W1-2; aligns the gates.
  21. V4L: buy 3; 2 in service plus 1 spare.
  22. Software: one venv-per-tool recipe; avoids conflicting installs.
  23. Region unknown: prefer worldwide shippers (Allnet, Arace, DigiKey, Adafruit, 4D, Wisecoco); TinyTronics and Pi Hut are cheaper only for EU/UK buyers; duties are not included.
  24. Costs: this group is re-priced above at world prices.
  25. P1b completion: outside this group; write report_research.json errata before P2.

