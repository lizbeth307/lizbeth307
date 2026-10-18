# Cable bulkhead set 7 sma 1 f bulkheads r: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e32114dd-52d`_

- **Part:** Cable/bulkhead set (core, RF group, 1 set). v2 contents: 6 SMA panel ports (P1-P3, P6, P7, optional P8), 1 BNC (P5) and 1 F (P4); internal RG316 jumpers; 4 RG316 field feeds of 1-2 m; IPX-SMA pigtail for P7; F-F bulkhead plus internal 75 ohm lead; 1 m 75 ohm F-F lead to the LNB; 2 shielded USB extensions with ferrites for the V4L dongles; 4 CH334F pigtails; touch lead with VBUS cut; adapters; USB3 A-A cable for EDL.
- **Current pick:** STACK line 283: "7 SMA + 1 F panel connectors; internal RG316 jumpers; 2 shielded 15 cm USB extensions with ferrites; pigtails; 75 ohm F lead". Supplier: RTL-SDR Blog SMA Pigtail Adapter Set plus unnamed generic parts. Budget alternative already in STACK: generic RG316 screened on the VNA. The reference ferrite is the Wurth 74271112 (reaudit_D).
- **Current price usd:** 90-170. This is a model, not an itemised price. The only verified line is the RTL-SDR Blog SMA Pigtail Adapter Set at $18.95 (re-checked 18 Oct 2026). The HDMI cable ($14.50-25, display line) and the Lime MHF4L bulkheads (Lime line) are priced in other lines, so they must not be counted here.
- **Decision:** replace_conditionally
- **Chosen:** Keep the set, but replace three of its lines. Each replacement is conditional on the tests below.
  (1) Panel ports P1, P2, P3, P6 and optional P8: generic one-piece RG316 pigtails, SMA female bulkhead with O-ring to right-angle SMA male, 20 cm. One 10-pack (AliExpress, $22.29) gives 4-5 used and 5-6 spares for culling. Each pigtail replaces a separate panel bulkhead plus the panel-to-board jumper. Board-to-board jumpers do not change.
  (2) USB extensions for the V4L dongles: 2x Lindy 36700 (USB 2.0 A male to A female, 0.2 m).
  (3) 1 m LNB lead: Goobay 58814, 75 ohm, F plug both ends, Class A+, 5.4 mm OD. The Goobay 66620 (5.0 mm, Class A 85 dB, same price) is the thinner alternative.
  Everything else stays as it is:
  - RTL-SDR Blog Pigtail Adapter Set ($18.95).
  - Wurth 74271112 ferrites.
  - The 4 RG316 field jumpers of 1-2 m.
  - P5 BNC bulkhead jumper, plus a BNC M-M lead for the Boni-Whip.
  - SAT-rated F-F bulkhead and the internal 75 ohm lead.
  - P7 IPX-SMA pigtail. The Taoglas CAB.011 ($4.44) is an optional quality upgrade, not a saving, and only fits if the LC76G has an MHF1 connector.
  - CH334F pigtails, touch lead, adapters and the USB3 A-A cable.
- **Chosen price usd:** Changed lines, verified: $30.62 = $22.29 (pigtail 10-pack) + 2x $2.70 (Lindy 36700, GBP 2.03 incl. UK VAT; GBP 1.69 = $2.25 ex VAT; plus GBP 3.99 shipping) + $2.92 (Goobay 58814, EUR 2.60 incl. 19% DE VAT, Reichelt). FX: 1 EUR = 1.1241 USD, 1 GBP = 1.3318 USD. Whole set: about $75-145 (model). Only these are verified: $18.95 pigtail set and $30.62 changed lines; the Wurth ferrites at about $8.30 for 2 come from the Mouser figure in the search result, which I could not re-fetch. The Lindy price is from the UK store. I could not read an EU store price (lindy.de returned HTTP 503).
- **Saving usd:** Cannot be verified: the current set is a model, not itemised. Model, at generic-baseline prices for the replaced lines: about $5-25 in total, made up of:
  - Panel ports: a 5x generic F-F bulkhead plus 5x generic M-M jumper baseline (about $12-28) against $22.29, so about $0-6. If the baseline jumpers were branded ($15-24 each), the saving is about $60-100.
  - USB: 2x (about $3-6 generic shielded, against $2.70), so about $1-7.
  - F lead: about $0-5.
  Separately, the $14.50-25 HDMI cable leaves this line for the display line. That is a re-allocation, not an analog saving.
- **Equivalence proof:** PANEL PIGTAILS (generic, O-ring SMA female bulkhead to right-angle SMA male, RG316, 20 cm)
  - Fewer interfaces: each path loses one SMA pair (the separate bulkhead). That is about 0.03-0.07 dB less loss and one reflection fewer per path (angle B's literature figure).
  - Cable: same RG316 class as the current jumpers. Habia RG316/C gives 0.54/0.86/1.29 dB/m at 0.4/1/2 GHz, so 20 cm costs 0.11/0.17/0.26 dB.
  - P1 at 137 MHz, before the LNA: about 0.06 dB, at the bottom of the 0.06-0.36 dB model.
  - DC: same centre conductor. P2/P3 at 4.5 V, 0.3 A drop about 20 mV (model).
  - Shielding: single braid, same as the baseline.
  - O-ring: stated on the listing. This is better than the unspecified generic bulkhead for IPX4/IP54.
  - Not provable on paper: VSWR, plating, pin depth, braid coverage, thread length, D-flat, durability. The current generic bulkheads and jumpers are also unproven on these, so the tie is broken only by the per-unit acceptance tests. Any unit that fails is replaced with a branded part, so the set can never end up below the current quality.
  
  LINDY 36700 USB EXTENSION
  - Published (Lindy UK page): USB 2.0 480 Mbit/s, A male to A female, tinned copper 26/28 AWG, 24K gold pins, nickel shells, 4.4 mm PVC, Al-Mg braid ("double shielded" in the summary), UL raw cable, RoHS/REACH, 10-year warranty.
  - Power-pair drop at 0.27 A: about 23 mV (model).
  - Every published spec is equal or better than the unspecified generic, except two points:
    - Length is 0.2 m instead of 0.15 m. This is still inside the 20 cm limit set in critical_specs.
    - Foil is not listed: the spec table names the braid only, and that inconsistency is the reason for the noise gate below.
  
  GOOBAY 58814 F LEAD (Reichelt)
  - 75 ohm, 1 m, moulded "fully shielded" F plugs at both ends. The spec table says F plug / F plug; the title says "connector, socket".
  - Triple shield (bonded Al foil, Al braid 128x, Al foil), declared Class A+ 95 dB. This is above the required double shield and Class A 85 dB.
  - 5.4 mm OD, which meets the "about 5 mm, thin" target. CCS 0.5 mm inner conductor.
  - DC loop about 0.3 ohm (model), under 0.1 V at 0.3 A. LNB DC passes.
  - Loss after the LNB, which has 50-66 dB gain, does not matter at the 739.5 MHz IF.
  
  ALL THREE ARE PASSIVE
  No TX, no loops, no change to drivers or rails.
- **Rejected:**
  1.
    - **Name:** RTL-SDR Blog SMA Straight Adapter Set ($14.95, saves $4)
    - **Why:** Verified $14.95, 6 adapters with no cable. Worse in strain relief: rigid N/UHF/BNC bodies lever on the jack they sit on. Angle A's 'bench-only' escape does not hold, because bench use puts them on LiteVNA/tinySA PCB-mounted SMA jacks, which are more fragile than the plate-bonded panel bulkheads. Neither set publishes VSWR. A real loss of function for $4.
  2.
    - **Name:** Fair-Rite 0431164281 Mix 31 snap-on ($2.85 at DigiKey, qty 1) instead of Wurth 74271112 ($4.15, Mouser figure from the search, not re-fetched)
    - **Why:** Electrically it holds up. Fair-Rite datasheet: 20/75/104/170/315/380 ohm at 1/5/10/25/100/250 MHz, minimum -20%. Wurth datasheet: 175/316 ohm at 25/100 MHz, ±25%; its curve shows about 11/45/85 ohm at 1/5/10 MHz. So Fair-Rite is equal at 25-100 MHz, has better guaranteed minimums, and is better at 1-10 MHz; the '773 ohm' Wurth figure in angle A was wrong. It fails on environment and qualification: TME lists 0 to +85 C for the polypropylene case, and the Fair-Rite datasheet gives no temperature range. Wurth gives -50 to +105 C, AEC-Q200 and a safety key. The handheld runs cold (cold-boot tests), so the Fair-Rite is not proven not-worse. Revisit if Fair-Rite confirms a rating of -20 C or lower. The saving would be only $2.60.
  3.
    - **Name:** Delock 82457 USB 2.0 A-A 15 cm (about $4.49)
    - **Why:** Shielding is not stated in the search snippet, and the Delock spec page returned HTTP 401. Shielding is a critical spec, so the part cannot be accepted, and it is not cheaper than the Lindy ($2.70).
  4.
    - **Name:** Good Connections SAT F-F 1 m, Class A+ 95 dB
    - **Why:** Price and OD are unverified (the page was not readable). It is likely RG6-class thick cable. Goobay 58814 gives the same declared A+ 95 dB at 5.4 mm for EUR 2.60, verified.
  5.
    - **Name:** Amphenol RF 135110-01-06.00 and branded SMA bulkhead jumpers
    - **Why:** Not cheaper. DigiKey now lists 135110-01-06.00 at $23.58, Cinch 415-0031-006 at $22.30, and the cheapest branded part, Lighthorse CBD-SAF3GT-SAMGT-6IN, at $15.23 (marketplace). They stay as the fallback for any generic pigtail that fails acceptance. RG316-DS (135110-03-06.00, $30.15) is used only if the noise baseline fails.
  6.
    - **Name:** Taoglas CAB.011 as a saving on the P7 IPX pigtail
    - **Why:** The spec is proven: VSWR 1.3 max to 6 GHz, about 0.3-0.4 dB S21 at 1.6 GHz, gold-plated brass, front nut, D-cut, 1/4-36 thread 11.4 mm. But at $4.44 it costs more than a generic IPX-SMA pigtail (an AliExpress MHF4 version is about $2.83), so it is not a cheaper analog. It also has no O-ring. The LC76G schematic says only 'IPEX' (GPS1), so the MHF1/MHF4 generation is unconfirmed. Optional upgrade only.
  7.
    - **Name:** Generic AliExpress RG316 SMA M-M jumpers for the 4 field feeds of 1-2 m
    - **Why:** No positive evidence of flex life outdoors. The DM1TBE report (2 of 3 AliExpress RG316 cables lost more than 4 dB at 28 MHz) is weak: it was measured into an antenna with a power meter, and commenters faulted the method. A WN3F eBay RG316 cable measured on spec. That makes it unproven either way, not proven equal, so the current field jumpers are kept.
  8.
    - **Name:** DIY Habia RG316/C or RG316D with branded crimp plugs
    - **Why:** Not cheaper: about 20 plugs at about $7 plus cable plus tool. Crimp quality would need proof unit by unit.
  9.
    - **Name:** Used branded jumpers (Huber+Suhner, Rosenberger) on eBay
    - **Why:** Unpriced (eBay blocked). Unknown wear and pin depth.
  10.
    - **Name:** Generic Ni-Zn clip ferrites, and generic shielded USB/HDMI leads
    - **Why:** No impedance or shielding data. The Wurth part and the Lindy have published specs for a few dollars.
- **Confidence:** medium
- **Conditions or tests:** All tests are conducted, on the bench, receive-only. No antenna sweeps.
  
  A. Panel pigtails. Test each unit before it goes near a V4L, LiteVNA or Lime jack.
  - Gender: it must be true SMA. The female bulkhead has a socket centre contact, not the RP-SMA pin.
  - Cable: brown or tan FEP jacket, OD 2.5 ±0.1 mm. Black PVC at about 2.8 mm is RG174 sold as RG316: reject it.
  - Pin gauge: the male centre pin must not protrude past the reference plane.
  - LiteVNA, far end terminated: S11 at or below -20 dB from 0.1 to 2.3 GHz. Insertion loss (|S21|) at or below 0.3 dB up to 1.7 GHz and at or below 0.45 dB at 2.3 GHz.
  - Then 10 mate/demate cycles, a pull test and 10 flexes, and sweep again with the same limits.
  - Mechanical: the thread must take the 4-5 mm wall (ASA plus 2 mm Al) with O-ring, lock washer and nut, and still leave 3 or more full threads for mating. It needs a D-flat or another anti-rotation method.
  - Record S11/S21 in parts.yaml.
  - The 10-pack listing shows 3 orders and no rating. If its store has no track record, buy listing #5 instead ($4.15 each, 147 sold, rating 5, O-ring).
  - Any port without a passing unit gets a branded part (Lighthorse $15.23 or Amphenol 135110-01-06.00).
  
  B. Lindy 36700
  - The 0.2 m length must fit the case CAD.
  - Shell-to-shell DC continuity check.
  - Terminated noise-floor A/B on each V4L, direct versus through the extension: rise must be under 0.5 dB.
  - The Wurth 74271112 is rated for 4.5-6 mm cable, so the 4.4 mm cable needs one layer of heat-shrink under it.
  - Buy from Lindy's EU store or an EU distributor, and re-check the EU price before ordering.
  
  C. Goobay 58814
  - Check on arrival that both ends are F plugs.
  - S11/S21 sweep, accounting for the 50/75 ohm mismatch.
  - Receive-only ingress A/B against a reference Class A lead, at 470-800 MHz including 733-758 MHz, with the LNB unpowered and then powered. There must be no new carriers above the reference.
  - DC drop under the LNB load: 0.1 V or less.
  - Fallback: 66620 (5.0 mm), or the current lead.
  
  D. Taoglas CAB.011 (optional): only if the LC76G receptacle is MHF1/U.FL (about 3 mm square; MHF4 is about 2 mm square). Add a panel O-ring.
  
  Note: the shared WebSearch budget was exhausted before I could search, so all of this rests on WebFetch of primary pages: DigiKey, Taoglas, Wurth and Fair-Rite datasheets, Lindy UK, Reichelt, the RTL-SDR Blog store and the Waveshare schematic.
- **Stack changes:** - Panel: 6 SMA ports (P1-P3, P6, P7, optional P8), 1 BNC (P5) and 1 F (P4). The Lime RX1/RX2/REF IN ports stay in the Lime line.
  - Drill the P1-P3, P6 and P8 holes for one-piece O-ring bulkheads (1/4-36 UNS, about 6.4 mm, with a D-flat if the part has one). These parts replace the separate F-F bulkheads and the panel-to-board jumpers.
  - Route the fixed 20 cm pigtails, with right-angle plugs at the boards, along the plate away from the HDMI and the bucks. Bend radius 15 mm or more.
  - USB: 0.2 m extensions (5 cm more slack in the RF bay) with heat-shrink build-up under the Wurth 74271112.
  - LNB lead: Goobay 58814, 0.5 mm CCS inner conductor. The LNB rail (13.2/18 V) and injector are unchanged.
  - BOM:
    - Remove the HDMI cable from this line (it is in the display line).
    - Replace the old BNC-SMA Boni lead with a P5 BNC-bulkhead-to-SMA RG316 jumper plus a BNC M-M lead.
    - Add a P7 O-ring if CAB.011 is used.
    - parts.yaml gets S11/S21 for each pigtail and the F lead.
  - No changes to rails, drivers or software. All items are passive, so receive-only, no-loop and conducted-only all hold.
- **Sources:**
  - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
  - https://www.digikey.com/en/products/detail/taoglas-limited/CAB-011/2332725
  - https://cdn.taoglas.com/datasheets/CAB.011.pdf
  - https://www.waveshare.com/lc76g-gnss-module.htm
  - https://files.waveshare.com/wiki/LC76G/manual/LC76G%20GNSS%20Module.pdf
  - https://www.lindy.co.uk/cables-adapters-c1/usb-c449/0-2m-usb-2-0-type-a-extension-cable-anthra-line-p11311
  - https://www.we-online.com/components/products/datasheet/74271112.pdf
  - https://www.digikey.com/en/products/result?keywords=0431164281
  - https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/9036/431164281.pdf
  - https://www.tme.eu/en/details/0431164281/ferrites-for-cables/fair-rite/
  - https://www.reichelt.com/de/en/shop/product/connection_cable_f_class_a_connector_socket_1_m-303277
  - https://www.reichelt.com/de/en/shop/product/connection_cable_f_class_a_connector_socket_1_m-303289
  - https://www.aliexpress.com/w/wholesale-sma-female-bulkhead-waterproof-o-ring-to-sma-male-rg316.html
  - https://qrper.com/2023/04/coax-cables-i-used-for-sota-pota-a-horror-story/
  - https://www.digikey.com/en/products/result?keywords=SMA%20bulkhead%20jack%20to%20SMA%20plug%20RG316%206%22
  - https://www.koax24.de/en/product-info/coaxial-cable/koaxialkabel-50-ohm/24-32-mm-size2/rg316d-rd316.html (angle B, not re-fetched)

