# Adafruit ch334f mtt hub 5997: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_071e1025-145`_

- **Part:** Internal USB 2.0 MTT hub behind FE1.1s P3 (Interface group, core tier), qty 2 (1 fitted, 1 like-for-like spare)
- **Current pick:** Adafruit CH334F Mini 4-Port USB Hub Breakout, PID 5997 (WCH CH334F QFN24, 12 MHz crystal, schematic rev C)
- **Current price usd:** 9.90 (2 x 4.95 at adafruit.com, in stock, re-checked 18 Oct 2026; the 10-99 tier of $4.46 does not apply at qty 2)
- **Decision:** keep
- **Chosen:** Keep the Adafruit CH334F 5997, qty 2. For an EU buyer the identical part from DigiKey DE (1528-5997-ND, EUR 4.35 net / EUR 5.18 incl. 19% DE VAT, 829 in stock) is equivalent, and it makes sense to buy it there if it ships with the planned DigiKey order. Otherwise buy it in the planned Adafruit bring-up order. This is a sourcing choice only, not a part change.
- **Chosen price usd:** 9.90 (Adafruit). The same part from DigiKey DE is 9.79 ex VAT (2 x EUR 4.35 at the ECB rate of 16 Oct 2026, 1 EUR = 1.1253 USD), or about 11.65 incl. DE VAT.
- **Saving usd:** 0.00. Buying the same part from DigiKey DE would save at most $0.11 for 2 ex VAT, which is within FX noise. No different part that is not worse is cheaper.
- **Equivalence proof:** Nothing replaces the 5997, so this is the reference spec I re-verified from primary documents. Every candidate was tested against it.
  (1) WCH CH334/335 datasheet V2.5 (local copy ch334ds1.pdf):
  - Table 1-1 lists every CH334/CH335 variant as MTT.
  - ICC is 85 mA typ. with HS upstream and 4 HS downstream ports.
  - V5 (LDO input) is 4.5/5.0/5.25 V, which suits LAB5 at 5.0 V.
  - ESD is 6 kV HBM Class 3A. Temperature range is -40 to 85 C.
  - CH334F has GANG power control only, so per-port VBUS has to come from external switches, as the stack already plans.
  - Crystal-free operation is optional, but WCH says it 'may deviate from the USB specification' and is 'only applicable to non-precision occasions'. A crystal-free board therefore counts as worse.
  (2) Adafruit schematic rev C (local copy schem4_orig.png, which I inspected):
  - A 12 MHz crystal is fitted on XI/XO.
  - USB-C VBUS is the 5.0 V net (chip V5). It runs through PTC2 (5V/2A) to the VBUS net.
  - The JP5 header pin 1 and pin 1 of all four port pad sets JP1-JP4 are on that VBUS net, each port with a 100 uF capacitor (C3-C6; the angle-A report said 10 uF, which is wrong).
  - The LEDs can be removed by cutting SJ1.
  (3) adafruit.com/product/5997, re-read today: $4.95, in stock; 31.6 x 20.4 x 4.8 mm, 2.9 g, 4 mounting holes; downstream ports are solder pads ('We expect folks to solder directly to the pads').
  Why no candidate passes:
  - The only cheaper 4-port CH334F board is the 8086 Consultancy hub at $4.45 net. It cannot be shown to be not-worse on interface, mechanics and reliability; see the rejected list.
  - Every other cheaper option fails on port count, TT mode or a missing spec.
  FX: ECB reference rates of 16 Oct 2026, 1 EUR = 1.1253 USD and 0.84385 GBP, so GBP/USD = 1.3335. This replaces the unverified 1.124 and 1.332 rates in the search reports. Both were close, so no conclusion changes.
- **Rejected:**
  1.
    - **Name:** 8086 Consultancy 'Mini 4-Port USB-C USB 2.0 Hub' (The Pi Hut SKU 106383)
    - **Why:** Price is real: GBP 4.00 incl. 20% UK VAT, in stock (live Shopify JSON, 18 Oct 2026), which is GBP 3.33 net = $4.45, or $1.01 saved on 2.
  
  What I could NOT prove worse: the product photos show a QFN24 chip marked CH334F with an SMD crystal beside it, so the silicon, MTT and clocking class match. No LEDs are fitted, which is slightly better for light leaks.
  
  What IS worse:
  (a) All ports are fixed USB-C receptacles, not solder pads. That fails the explicit interface spec. Every link would need a custom USB-C-plug lead: the upstream lead carrying LAB5 VBUS plus FE1.1s D+/D-/GND, plus the Pico, RTL-A, LAB USB-A (VBUS from TPS2553) and HF+ (VBUS from load switch, LC and Mix-31) leads. That is at least 5 extra mated contact pairs, which can fret or work loose in a handheld, compared with soldered joints.
  (b) There is no separate 5 V pad. The hub can only be powered through the IN connector's VBUS and a 1 A polyfuse, and downstream VBUS is hard-wired to that net.
  (c) The board is 30 x 32 x 5 mm (960 mm²), against 645 mm² for the 5997 (+47%), and the plug overmolds stick out on all four sides, so it does not fit the mid-plate footprint.
  (d) No schematic and no ESD or board data are published. It is not listed on 8086.net, so the only source is The Pi Hut (UK), and UK-to-EU shipping and VAT are not verified (the shipping page returned HTTP 429).
  (e) The $1.01 saving would have to pay for at least 5 USB-C plug terminations (plug price not verified) before shipping. No verified net saving remains.
  2.
    - **Name:** Adafruit CH334F Mini 2-Port USB Hub Breakout (PID 5999)
    - **Why:** Price and stock verified: $4.50 at Adafruit, in stock; Pimoroni GBP 3.75 incl. VAT (about $4.17 net), in stock; Kiwi EUR 4.19 ex VAT. The Adafruit page says 'on this breakout only 2 of the ports' are present. With the Lime kept, H2, H3 and H4 are in use and H1 is reserved, so it fails the 4-port requirement. It also cannot serve as the like-for-like spare.
  3.
    - **Name:** Olimex USB-HUB (USB-A cable input, 4x USB-A)
    - **Why:** EUR 3.50 (about $3.94; the page does not say whether VAT is included), in stock (verified). It publishes no hub chip, TT mode, size, power input or schematic; only EU and UKCA declarations of conformity. The page warns that it 'will not work correctly with Neo6502'. MTT cannot be shown. There are no pads and no separate 5 V input, so it cannot be fed from LAB5 with Q6A VBUS cut without modification. As a cable-form consumer hub it is bulkier.
  4.
    - **Name:** Olimex USB-C-HUB (USB 3.0, 4x USB-A)
    - **Why:** EUR 3.50; this is the search report's data, not re-fetched. No chip or TT mode is published. It is about 84 mm long with a cable, has no pads and no external 5 V input. USB 3.0 brings no benefit behind the USB 2.0 FE1.1s and could become a SuperSpeed noise source. Worse on interface and size, and MTT is unproven.
  5.
    - **Name:** The Pi Hut 'USB Mini Hub with Power Switch - OTG Micro-USB' (SKU 102877)
    - **Why:** GBP 4.30 incl. VAT (about $4.78 net), from search B's cached data, not re-verified. Chip and TT mode are not stated. It is a 72 x 25 x 19 mm cased dongle with a captive lead, downstream VBUS tied to upstream, and no pads. It fails on MTT proof, size and power-path separation.
  6.
    - **Name:** Generic FE1.1s / GL850G / SL2.1A 4-port modules (AliExpress class)
    - **Why:** These chips are single-TT hubs (the FE1.1s already in the stack is STT), so they are worse on the TT spec. No listing prices were verified. Counterfeit and relabelled parts and uncontrolled layouts are common in this class.
  7.
    - **Name:** DIY board with a bare WCH CH334F and a 12 MHz crystal
    - **Why:** The silicon is the same, but PCB fab, assembly and shipping at qty 2 are not shown to be under $9.90 (the LCSC price was unverifiable, HTTP 403). The HS signal integrity, soak and emissions of a new layout would be unproven, and a hand-soldered QFN is a reliability risk.
  8.
    - **Name:** Used Adafruit 5997
    - **Why:** No listings were found. There is no realistic saving against $4.95 new, and the pads' solder and ESD history would be unknown.
  9.
    - **Name:** Same part from other sellers (not a replacement, sourcing only)
    - **Why:** - The Pi Hut ADA5997: GBP 4.80 incl. UK VAT, in stock, which is $5.33 net. It is NOT cheaper, so the stack's 'budget alternative' label is wrong.
  - Pimoroni ADA5997: GBP 4.15 incl. VAT ($4.61 net), OUT OF STOCK (verified).
  - BerryBase: EUR 5.45 incl. VAT, 6 in stock (search report).
  - DigiKey DE: EUR 4.35 net ($4.90 net), equal within FX noise.
  - DigiKey US: $4.95.
  None gives a real saving.
- **Confidence:** high
- **Conditions or tests:** Bring-up checks for the kept 5997. None of these is a condition for keeping it.
  (1) `lsusb -v` on the hub shows bDeviceProtocol 2 (TT per port).
  (2) 30-min soak plus 50 start/stop cycles with HF+ (3.1-3.7 MB/s), RTL-A (5.12 MB/s) and one LAB device: zero drops.
  (3) Run the spur A/B with SJ1 intact and with SJ1 cut. Cut it if the LEDs show up as light leaks or spurs near the HF+ chain.
  (4) Inrush on LAB5: the hub VBUS net carries 4 x 100 uF (C3-C6) plus 10 uF. Scope LAB5 and the 3 A fuse at switch-on.
  (5) Continuity check: hub pad 1 on H3 and H4 must NOT connect to the pigtail VBUS (see stack_changes).
  Not verified in this run:
  - The WebSearch budget was already used up when I started, so no new sweep for AliExpress or official-store CH334F modules was possible.
  - The Pi Hut shipping and EU VAT page returned HTTP 429.
  - USB-C plug prices were not checked.
- **Stack changes:** No part change. Three corrections and notes for v2:
  (1) BOM note: replace 'Budget alternative: Pi Hut GBP 4.80' with 'Pi Hut GBP 4.80 is incl. UK VAT (= $5.33 net, not cheaper). EU source of the same part: DigiKey DE 1528-5997-ND, EUR 4.35 net / EUR 5.18 incl. 19% VAT, in the DigiKey order; Pimoroni GBP 4.15 incl. VAT when in stock.'
  (2) Wiring, verified on schematic rev C: on the 5997 the JP5 '5V' pin is the shared VBUS net. It lands on pin 1 of all four port pad sets (100 uF each) and back through PTC2 (5V/2A) onto chip V5. So the H3 pigtail must take VBUS only from the TPS2553 output, and the H4 pigtail only from the load switch, LC and Mix-31 path, with hub pad 1 left unconnected on those ports. Otherwise LAB5 bypasses the switches.
  (3) Same issue on H2 in the Lime build: the USB map lists H2 VBUS as 'LAB5', but MCP #1 GPA2 is the RTL-A VBUS cut used by the labrx watchdog. With the Lime kept, RTL-A on H2 needs its VBUS through the GPA2 switch, not from hub pad 1, or the watchdog's VBUS cut does nothing.
  Optional: cut SJ1 to remove the port LEDs.
  No changes to rails, drivers (stock usbcore hub driver on Ubuntu 24.04 arm64), case footprint or connectors.
- **Sources:**
  - https://www.adafruit.com/product/5997
  - https://www.adafruit.com/product/5999
  - https://cdn-learn.adafruit.com/assets/assets/000/131/435/original/CH334DS1.PDF (local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/hub_ch334_dl/ch334ds1.pdf, Table 1-1, sec. 3.1, 4.2, 6.2)
  - https://cdn-learn.adafruit.com/assets/assets/000/131/436/original/components_schem.png (local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/hub_ch334_dl/schem4_orig.png)
  - https://www.digikey.de/en/products/result?keywords=1528-5997-ND
  - https://thepihut.com/products/mini-4-port-usb-c-usb-2-0-hub.js (8086 hub listing; photos saved in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/verify_hub_dl/)
  - https://thepihut.com/products/adafruit-ch334f-mini-4-port-usb-hub-breakout.js
  - https://shop.pimoroni.com/products/adafruit-ch334f-mini-4-port-usb-hub-breakout.js
  - https://shop.pimoroni.com/products/adafruit-ch334f-mini-2-port-usb-hub-breakout.js
  - https://www.kiwi-electronics.com/en/search?search=CH334F
  - https://8086.net/products
  - https://www.olimex.com/Products/USB-Modules/Hub/USB-HUB/
  - https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml (16 Oct 2026: USD 1.1253, GBP 0.84385 per EUR)
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md (USB map lines 606-619, MCP23017 line 644, BOM line 236)

