# Display: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_0e70c405-a03`_

- **Component:** Display: very bright, ideally higher than Full HD, capacitive touch, 5.5-8 in, for a Radxa Dragon Q6A handheld used in direct sunlight
- **Current pick assessment:** The current pick, a generic "5-7 inch DSI or HDMI touchscreen at $60-100", does not meet the new requirement. Displays in that class are 300-500 nit panels at 1024x600 or 1080p (examples: Waveshare 7" FHD 1080x1920 at about 350 nits, Waveshare 7HP-CAPQLED at 500 nits), and they wash out in direct sun. A rough estimate, assuming about 1% diffuse reflectance at about 100 klx, gives these contrast ratios: 350 nits about 2:1, 1000 nits about 4:1, 2000 nits about 7:1, 3000 nits about 10:1. DSI is not a real option either. Radxa documents that only its own Display 10 FHD (1200x1920) and Display 8 HD (800x1280) are supported. A Feb-2026 forum thread shows the official 8HD panel staying black on Ubuntu 24.04, because that image has no panel driver or overlay, and no staff reply has appeared. So HDMI plus USB touch is the realistic path.
  
  What the Q6A HDMI port can do:
  - Radxa's docs state up to 4K@30.
  - The port is a QCS6490 DisplayPort output (data-lanes <0 1>, i.e. 2 lanes) feeding Radxa's passive RA620 DP-to-HDMI bridge. Mainline patches (May 2026) cap the DP voltage swing at level 2 because link training fails at level 3.
  - The same RA620 drives a 4K@60 HDMI port on the ROCK 5 ITX, so the 4K30 cap comes from the 2-lane DP link, not the bridge.
  - My own calculation: a 2-lane HBR2 link carries 8.64 Gbps. 4K30 at 297 MHz needs 7.13 Gbps, which matches Radxa's cap. 2560x1600@60 with reduced-blanking timing (268.5 MHz) needs 6.44 Gbps, so it should fit. 1920x1080/1200@60 (3.6-3.7 Gbps) is safe.
  - I found no forum report of anyone running more than 1080p on a Q6A.
  
  Market reality in October 2026, after many searches: I could not find any plug-and-play module that is above FHD, at least 1000 nits, 5.5-8 in, and has both HDMI and USB touch.
  - Above-FHD small panels you can actually buy are dim: Waveshare 9" 2560x1600 about 350 nits, Wisecoco 8.9"/9" 2560x1600 500 nits, LS055R1SX04 5.5" 1440x2560 450 nits, Waveshare 5.5" AMOLED about 310 nits max.
  - Very bright small panels are 1920x1080 or 1920x1200. Camera field monitors with 1920x1200 at 2200-2600 nits do exist, but their touchscreen runs the monitor's own menus. No spec sheet I found lists a USB-HID touch output, so they will not act as a touchscreen for the Q6A.
  - Pixel density at 7" 1080p is already 315 PPI. At a 35 cm handheld distance, 1-arcminute visual acuity is about 250 PPI, so 2.5K at 8-8.4" (359-377 PPI) adds little sharpness while costing brightness, power and GPU fill (about 1.8x the pixels).
  Brightness matters far more than resolution for this device.
- **Alternatives:**
  1.
    - **Name:** Wisecoco 7in 1920x1080 sunlight-readable LTPS IPS kit, 2000-2500 nits, with HDMI-in board and capacitive touch
    - **Key specs:** - 7in 1920x1080, 315 PPI, LTPS IPS.
  - Brightness: 2000+ cd/m2 typ. in the spec table; the title says 2500; eBay listings say 2000 or 2000-2400.
  - 1000:1 contrast, 85/85/85/85 viewing angle.
  - MIPI 4-lane panel on an HDMI-in board; capacitive touch.
  - Outline 164.2x98.0 mm; rated -20 to 70 C.
  - Thickness, power draw and touch-to-host interface are not stated. Midas datasheet scaling for a similar 7in panel suggests about 6-8 W total at 2000 nits (estimate).
    - **Price:** $132 on wisecocodisplay.com ("LCD panel with HDMI in board"). The Wisecoco eBay kit (2000 nits, touch, HDMI) sold for $177.64 in June 2025, plus $80 expedited shipping. October 2026 price is unverified.
    - **Pros:** - Among the options I could verify, it is the only one that combines at least 2000 nits, HDMI input, capacitive touch and a hobby price.
  - 315 PPI looks retina-sharp at arm's length.
  - 1080p60 is the safest mode on the Q6A's RA620 HDMI path.
  - Wide temperature rating; thin and light compared with field monitors.
  - Roughly half the power draw of a 2200-3000 nit field monitor at a comparable outdoor brightness.
    - **Cons:** - Not above FHD.
  - Specs are inconsistent across listings (2000 / 2400 / 2500 nits; HDMI vs MIPI).
  - Touch-to-host interface (USB HID?), board input voltage, lamination and anti-glare finish are all unconfirmed.
  - No datasheet or panel part number published.
  - Shipping to Ukraine via eBay is expensive.
    - **Sources:**
      - https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
      - http://www.wisecocodisplay.com/product-category/high-brightness-display/
      - https://www.ebay.com/itm/176657492046
      - https://www.ebay.de/itm/176594983531
      - https://www.aliexpress.us/item/3256805758322161.html
    - **Availability:** Wisecoco B2B site ("Get a Quote"), Wisecoco eBay and AliExpress official stores. AliExpress pages need a login and could not be read; ask the seller for the datasheet and photos of the board and touch controller before ordering.
    - **Q6a compatibility:** Good, via HDMI at 1920x1080@60 plus USB touch on a USB 2.0 port (hid-multitouch, no driver needed if the board exposes USB HID). If the board advertises a portrait mode (1080x1920), force the mode with video= and rotate in the compositor.
  2.
    - **Name:** Midas MDT0700F1IHHC-MIPI, 7.02in 1200x1920, 2500 nits (the brightest verified above-FHD panel)
    - **Key specs:** - 7.02in 1200x1920 (WUXGA), 323 PPI, ADS 8-bit + FRC.
  - 2500 cd/m2, cover lens with anti-reflection coating, in-cell capacitive touch (FT7250, I2C), so there is no extra touch layer or air gap.
  - MIPI DSI, 4 lanes, 40-pin 0.5 mm FFC. Init is only 2 DCS commands (sleep out, display on).
  - Module 115.7x177.06x5.4 mm; rated -20 to 70 C.
  - Backlight from the datasheet at 16 V Vf typ.: 200 mA = 1000 nits (about 3.2 W), 300 mA = 1500 nits (4.8 W), 400 mA = 2000 nits (6.4 W), 500 mA = 2500 nits (8 W, with a thermal caveat).
  - Needs IOVCC 1.8 V and VSP/VSN +/-5.5 V supplies.
    - **Price:** About EUR 324 each at Farnell, 12-week lead time (from a search snippet; the live page was unavailable).
    - **Pros:** - Best optics found: 2500 nits, AR-coated cover glass, in-cell touch, so reflections stay low in sun.
  - Its 1920x1200 resolution is in the user's above-FHD list.
  - Datasheet-backed power curve allows real battery planning.
  - The trivial init sequence makes a Linux panel-simple-dsi style driver feasible.
  - Wired directly to DSI, it frees the HDMI port and removes the bridge board.
    - **Cons:** - Not plug-and-play. You either build a custom adapter PCB for the Q6A's 39-pin 0.3 mm DSI (+/-5.5 V, 1.8 V, a 16-19 V LED boost, plus device-tree and kernel work), or find an HDMI-to-MIPI board flashed for this panel.
  - FT7250 is not in the mainline edt-ft5x06 compatible list (unverified whether it works).
  - Expensive, with a long lead time.
    - **Sources:**
      - https://www.farnell.com/datasheets/3984938.pdf
      - https://export.farnell.com/midas-displays/mdt0700f1ihhc-mipi/lcd-tft-display-7-1200x1920p-mipi/dp/4248109
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/mipi-dsi
      - https://docs.kernel.org/7.1/_sources/input/devices/edt-ft5x06.rst.txt
    - **Availability:** Farnell (UK/EU export), about 12-week lead time. Stock in October 2026 not verified.
    - **Q6a compatibility:** Hard. Radxa supports only its own DSI panels, so a DSI build means your own device-tree overlay and panel entry. An HDMI build needs a third-party HDMI-to-MIPI bridge configured for this panel. Advanced builders only.
  3.
    - **Name:** Wisecoco 8.4in 1600x2560, 2000 nits (bare MIPI panel)
    - **Key specs:** - 8.4in 1600x2560, 359 PPI, 2000 cd/m2 typ., 1500:1 contrast, 60 Hz.
  - MIPI 8 lanes on 2 ports.
  - Backlight 32 LEDs (8S4P, 80 mA).
  - 115.84x190.71x2.05 mm.
  - Operating range only -10 to 50 C.
  - Touch and HDMI board are not stated.
    - **Price:** $158 (panel only, Wisecoco site)
    - **Pros:** - The only option found that is both 2.5K and about 2000 nits in the target size.
    - **Cons:** - Dual-port MIPI, so it cannot be driven from the Q6A's single 4-lane DSI. It needs a dual-DSI HDMI bridge board that is not listed.
  - No touch listed.
  - 50 C maximum operating temperature is risky in summer sun.
  - No datasheet; title and alt text disagree on orientation.
  - I found no off-the-shelf 8.4in 2560x1600 HDMI kit anywhere.
    - **Sources:**
      - https://www.wisecocodisplay.com/product/8-4-inch-ips-tft-lcd-display-1600x2560-2000nits-high-brightness-screen-with-mipi-interface/
      - http://www.wisecocodisplay.com/product-category/high-brightness-display/
    - **Availability:** Quote-based from Wisecoco; kit availability unverified.
    - **Q6a compatibility:** HDMI only, through a custom dual-MIPI bridge. 2560x1600@60 with reduced blanking (6.44 Gbps) should fit the Q6A's 2-lane DP link, but is untested. Uncertain.
  4.
    - **Name:** FEELWORLD LUT7 / LUT7S PRO (7in field monitor)
    - **Key specs:** - 7in 1920x1200, 323 PPI, 2200 nits, 1200:1 contrast, IPS touch.
  - 4K30 HDMI input; LUT7S PRO adds SDI.
  - Light sensor for auto-dimming.
  - 7-21/24 V DC, up to 20 W (Adorama lists 20 W).
  - 450 g without battery, 460 g with battery plate.
    - **Price:** $379.99 at Newegg; about EUR 387-469 in the EU (LUT7S PRO). Used units around $312 on eBay.
    - **Pros:** - Above FHD (WUXGA) and very bright, in a rugged finished product.
  - Sun-readable, with auto-dimming.
  - Runs directly from the 4S pack voltage.
  - Accepts any input mode up to 4K30 and scales it.
    - **Cons:** - Touch controls only the monitor's menus; no spec sheet lists a USB touch output for the host, so you would need an encoder or buttons for SDR++.
  - Heavy and thick; up to 20 W; runs very warm (user review).
    - **Sources:**
      - https://www.newegg.com/p/0UF-017N-00083
      - https://syntex.tv/feelworld-lut7s-pro
      - https://www.adorama.com/felut7.html
      - https://www.adorama.com/used-feelworld-7-3d-lut-4k-hdmi-ultra-bright-2200nits-on-camera-touchscreen-monitor/p/us2015131
    - **Availability:** EU photo/video shops; Prom.ua lists other FEELWORLD models in stock.
    - **Q6a compatibility:** Video works over HDMI at 1920x1200@60. No touch to the host.
  5.
    - **Name:** Desview R72 (7in, 2600 nits, field monitor)
    - **Key specs:** - 7in 1920x1200 IPS, 2600 nits, 1100:1 contrast, 90% DCI-P3.
  - Touch plus scroll wheel.
  - 4K HDMI in and out.
  - Power and weight not listed.
    - **Price:** $549 (Camera House AU; currency appears to be AUD); low stock
    - **Pros:** - Brightest 1920x1200 field monitor found.
  - Wide colour gamut.
    - **Cons:** - Touch is for the monitor menu only.
  - Expensive.
  - Power draw unknown (expect 15-20 W class).
  - Poor availability in EU and Ukraine.
    - **Sources:**
      - https://www.camerahouse.com.au/desview-r72-7-2600-nits-touch-screen-4k-hdmi-on-camera-field-monitor-1
    - **Availability:** Limited; not found in Ukrainian shops.
    - **Q6a compatibility:** Video over HDMI only.
  6.
    - **Name:** FEELWORLD LUT5 (5.5in, 3000 nits)
    - **Key specs:** - 5.5in 1920x1080, 368 PPI, 3000 nits, IPS touch.
  - 4K30 HDMI input; light sensor auto-dimming.
  - 142x86x28 mm, 270 g.
  - 7-24 V DC; some listings say up to 20 W. LUT5E variant listed at 9 W.
    - **Price:** EUR 229 (Ireland) to about EUR 275-290 (Baltics); UK RRP GBP 329, street GBP 249
    - **Pros:** - Brightest small option found.
  - Compact and light; auto-dimming.
  - Runs directly from 4S pack voltage.
    - **Cons:** - FHD only, and small for the SatDump/SDR++ UI.
  - Up to 20 W at full brightness.
  - Touch is not usable by the host.
    - **Sources:**
      - https://www.photospecialist.ie/feelworld-5-5-lut-5-monitor-3000-nits
      - https://www.masterfoto.lv/en/external-lcd-displays/5133-feelworld-55-lut-5-monitor-3000-nits-lut-5.html
      - https://www.adorama.com/felut5e.html
    - **Availability:** EU shops (IE, LV, EE); no UAH listing found.
    - **Q6a compatibility:** Video over HDMI at 1080p60. No touch to the host.
  7.
    - **Name:** FEELWORLD F6 PLUSX (5.5in, 1600 nits), available in Ukraine
    - **Key specs:** - 5.5in 1920x1080 IPS, 1600 nits, 1000:1 contrast, touch (menu).
  - Up to 9-10 W; 7-24 V DC.
  - 235 g; 148x93x20 mm.
    - **Price:** 8,250-13,834 UAH on Prom.ua (about $200-335 at about 41.5 UAH/USD, approximate). The related F5 PROX (1600 nits) is 7,660 UAH.
    - **Pros:** - In stock locally in Ukraine.
  - Lowest power of the bright field monitors.
  - Light, and runs directly from the pack.
    - **Cons:** - 1600 nits is only adequate in direct sun.
  - FHD at 5.5in.
  - No touch to the host.
    - **Sources:**
      - https://prom.ua/Feelworld-f5.html
      - https://www.bhphotovideo.com/c/product/1771211-REG/feelworld_f6plusx_f6_plus_x_5_5.html
      - https://masterfoto.lv/en/external-lcd-displays/11376-feelworld-f6-plusx-55-hdmi-monitor-1600nit-d252811.html
    - **Availability:** Prom.ua, several sellers, ready to ship.
    - **Q6a compatibility:** Video over HDMI. Needs a separate input device.
  8.
    - **Name:** Other no-host-touch bright monitors: Lilliput H7s, BenQ PVS7, NEEWER F700, Portkeys LH5P II
    - **Key specs:** - Lilliput H7s: 7in 1920x1200, 1800 nits, no touch, up to 15 W, 7-24 V, 535 g, 225x155x23 mm.
  - BenQ PVS7: 7in 1920x1200, 2000 nits, HDMI 2.0, 10 W typ. / 18 W max, DC 6.5-16.8 V, 693 g, 38.6 mm deep.
  - NEEWER F700: 7in 1920x1080, 2000 nits, menu touch, 12-26 V DC or USB-C 5V/3A.
  - Portkeys LH5P II: 5.5in FHD, 2200 nits, menu touch, 285 g.
    - **Price:** H7s $299 (out of stock); PVS7 price not listed; F700 GBP 309.99 / EUR 399.99 (2025 sale listings); LH5P II $399
    - **Pros:** - Bright, finished, rugged units.
  - PVS7's 6.5-16.8 V input exactly matches a 4S pack.
    - **Cons:** - None provide touch to the host.
  - Heavy (285-693 g), 10-18 W.
  - Poor value for this project.
    - **Sources:**
      - https://avlgear.com/products/lilliput-h7s-7-inch-ultra-brightness-on-camera-monitor
      - https://www.benq.eu/uk-ua/monitor/professional/pvs7/spec.html
      - https://uk.neewer.com/products/neewer-f700-7-camera-field-touch-screen-monitor-66605230
      - https://www.glazerscamera.com/collections/all/products/portkeys-lh5p-ii15-5-monitor
    - **Availability:** EU and global photo retailers; BenQ has a Ukrainian product page.
    - **Q6a compatibility:** Video over HDMI only.
  9.
    - **Name:** Lilliput 719/T (7in industrial, 1000 nits, PCAP touch over USB-C, IP65)
    - **Key specs:** - 7in 1280x800 (216 PPI), 1000 nits, 800:1 contrast, 10-point PCAP.
  - HDMI, VGA and USB-C (video, touch and power).
  - DC 9-36 V, up to 8.5 W at 12 V.
  - 410 g; 184.5x118.8x32 mm; IP65 frame; -20 to 60 C; auto-dimming.
    - **Price:** EUR 289 incl. VAT at Syntex (on request); $289 at Markertek (out of stock)
    - **Pros:** - Finished, rugged unit with touch delivered to the host.
  - Runs directly from 4S pack voltage (9-36 V) with no buck converter.
  - Moderate power draw.
    - **Cons:** - Low resolution (below FHD).
  - Thick and heavy for a handheld.
  - Only 1000 nits.
    - **Sources:**
      - https://syntex.tv/lilliput-719-t
      - https://www.markertek.com/product/lil-719h-t/lilliput-719h-t-7in-1000-nit-touch-screen-4k-monitor-w-ip65-frame-hdmi-extension-cable-1280x800-hdmi-usb-a
      - https://www.syntex.tv/introducing-the-latest-offerings-from-lilliput
    - **Availability:** Syntex (CZ, EU), on request.
    - **Q6a compatibility:** HDMI video plus USB touch (USB-C to USB-A cable). Needs video=HDMI-A-1:1280x800@60 if the boot mode is wrong.
  10.
    - **Name:** Industrial 7in 1024x600 high-brightness HDMI modules: Riverdi 7.0in HDMI (800-1000 nits) and Orient Display AFY1024600A2-7.0INTH-C-HDMI (900 nits)
    - **Key specs:** - Riverdi: 7in 1024x600 IPS, up to 1000 cd/m2 (optically bonded version 850), USB-C touch and power, backlight about 2.4-2.6 W.
  - Orient Display: 7in 1024x600, 900 cd/m2, PCAP, RTD2662 controller, 12 V, 167x115x12 mm.
    - **Price:** Riverdi RVT70HSHFWCA0 about $397 (RS NZ, ex GST). Orient Display $107.88.
    - **Pros:** - Low power for the brightness; proper industrial parts with datasheets.
  - Orient Display is cheap.
    - **Cons:** - 170 PPI looks coarse; small UI area.
  - Riverdi is expensive.
    - **Sources:**
      - https://www.mouser.at/riverdi-7inch-hdmi-displays
      - https://sg.rs-online.com/web/p/lcd-colour-displays/0672204
      - https://orientdisplay.com/products/7-0-raspberry-pi-tft-with-pcap-1024x600-900-nits-vga-hdmi-usb-interface/
    - **Availability:** Riverdi via TME, Mouser and RS (EU). Orient Display ships from the US.
    - **Q6a compatibility:** HDMI plus USB touch. Radxa's FAQ shows exactly this case: a 1024x600 panel garbles until video=HDMI-A-1:1024x600@60 is set.
  11.
    - **Name:** Waveshare 9in 2560x1600 monitor (SKU 18184) / Wisecoco 8.9in and 9in 2560x1600 touch kits
    - **Key specs:** - Waveshare: 9in 2560x1600 IPS (335 PPI), about 350 nits, optically bonded 10-point capacitive touch over USB, mini HDMI, 5 V at 410-580 mA (about 2-2.9 W).
  - Wisecoco: 8.9in or 9in 2560x1600, 500 nits, touch, HDMI and Type-C board; the 8.9in panel is dual-channel MIPI.
    - **Price:** Waveshare: INR 10,933 + GST (about $130 + GST) at Hubtronics; about EUR 180 at Grobotronics (out of stock); discontinued at Switch Science. Wisecoco: $107-148 + about $50 shipping (eBay).
    - **Pros:** - The only real plug-and-play above-FHD touch options.
  - Very low power; beautiful indoors.
    - **Cons:** - 350-500 nits is unreadable in direct sun.
  - 9in is larger than the target size.
  - 2.5K over the Q6A's HDMI is untested.
  - The Waveshare unit is being discontinued.
    - **Sources:**
      - https://www.waveshare.com/wiki/9inch_2560x1600_Monitor
      - https://grobotronics.com/pi-display-9-mini-hdmi-2560x1600-2k-ips-capacitive-touchscreen-usb.html
      - https://hubtronics.in/display-devices/lcds/hdmi-lcds/9inch-2560x1600-monitor
      - https://www.switch-science.com/products/7552
      - https://www.ebay.de/itm/176550075238
      - https://www.ebay.de/itm/176619193823
    - **Availability:** Limited and fading for Waveshare; Wisecoco available on eBay and AliExpress.
    - **Q6a compatibility:** Probable at 2560x1600@60 with reduced blanking (6.44 Gbps, below the 2-lane DP limit), but unverified on the Q6A. Fall back to 1920x1200 scaling if the link fails.
  12.
    - **Name:** Waveshare 5.5in HDMI AMOLED (1080x1920)
    - **Key specs:** - 5.5in 1080x1920 AMOLED (401 PPI), about 90% NTSC.
  - 5 brightness steps: 75 / 140 / 210 / 260 / 310 cd/m2.
  - 5-point USB touch.
  - 5 V at about 650 mA all-white, 250 mA all-black; 4.8 mm thick.
    - **Price:** Not verified in this search (historically about $70-90)
    - **Pros:** - Beautiful contrast and colour; very thin.
  - Low power on dark UIs like SDR++ waterfalls.
    - **Cons:** - Only about 310 nits maximum, useless in sun.
  - Burn-in risk: Waveshare warns against static images longer than about 1 hour, and the SDR++/SatDump UI is static.
  - Portrait-native.
    - **Sources:**
      - https://www.waveshare.com/wiki/5.5inch_HDMI_AMOLED
      - https://sudomod.com/forum/viewtopic.php?p=67896
    - **Availability:** Waveshare and AliExpress
    - **Q6a compatibility:** HDMI plus USB touch; needs a forced 1080x1920 mode and rotation. A Sudomod user's similar Wisecoco OLED board worked on Windows but not on a Pi, which points to EDID/timing quirks.
  13.
    - **Name:** Waveshare 5in high-brightness capacitive LCD 5DP-CAPLCD-B (budget)
    - **Key specs:** - 5in 1024x600 IPS (237 PPI), 800 cd/m2.
  - Toughened glass, optically bonded (-B variant; -H is narrow-bezel and air-bonded).
  - HDMI plus USB capacitive touch.
    - **Price:** About $63 (RobotShop US) / GBP 50.76 / EUR 64.95 (Openelab, -H variant, sold out)
    - **Pros:** - Cheap and proven driver-free USB touch on Linux.
  - Optical bonding reduces reflections.
  - Low power.
    - **Cons:** - 800 nits is marginal in full sun.
  - Low resolution and a small screen.
    - **Sources:**
      - https://www.robotshop.com/products/waveshare-5-high-brightness-touch-screen-1024x600-pixels-toughened-glass-panel-hdmi-interface-ips-panel
      - https://openelab.io/a/s/products/waveshare-5inch-narrow-bezel-capacitive
    - **Availability:** Waveshare store, AliExpress, EU resellers (stock varies)
    - **Q6a compatibility:** HDMI plus USB touch. Set video=HDMI-A-1:1024x600@60 (Radxa FAQ fix).
- **Recommended:**
  - **Name:** Wisecoco 7in 1920x1080 2000-2500-nit sunlight-readable LTPS IPS "Full Kit" (panel + HDMI-in driver board + capacitive touch), run from the Q6A HDMI port with USB touch; upgrade path to the Midas MDT0700F1IHHC 7in 1200x1920 2500-nit panel
  - **Why:** Brightness matters more than resolution for a sunlit handheld:
  - About 7:1 contrast in about 100 klx sun at 2000 nits, versus about 2:1 for the 350-500 nit 2.5K panels (my estimate).
  - 7in 1080p is 315 PPI, already past what the eye resolves at 35 cm (about 250 PPI).
  - 1080p60 is the safest, best-supported mode on the Q6A's RA620/2-lane-DP HDMI path.
  - HDMI avoids the DSI problem: Radxa supports only its own panels, and even those fail on Ubuntu 24.04.
  - The only verified-price product that combines 2000+ nits, capacitive touch and HDMI at a hobby price. Field monitors with the same brightness cost $230-550, weigh 235-693 g, draw 9-20 W, and their touch does not reach the host.
  - Expected draw is about 6-8 W at full brightness and about 4-5 W at 1000 nits. This is an estimate scaled from the Midas datasheet (backlight 3.2 W at 1000 nits, 6.4 W at 2000 nits, plus board).
  - With a $2 lux sensor and a sun hood, average draw can be much lower.
  
  Before paying, insist that the seller confirms:
  - the exact nit rating
  - that the touch reaches the host as USB HID
  - the board's input voltage (ideally 12 V)
  - whether the touch glass is optically laminated.
  
  If you specifically want above-FHD with bonded AR glass and will do some electronics work, the Midas 7.02in 1200x1920, 2500-nit panel (about EUR 324, 12-week lead time) is the best verified panel. The cost is a custom DSI adapter and device-tree overlay, or an HDMI-to-MIPI board flashed for that panel. No verified plug-and-play above-FHD, 1000-nit-plus HDMI touch module in 5.5-8in existed in this search.
  - **Price:** $132 (Wisecoco site, panel + HDMI board; confirm touch is included) to about $178 + shipping (Wisecoco eBay kit with touch, 2025 sale). Upgrade path: about EUR 324 for the Midas panel + about $30-60 adapter (estimate).
  - **Sources:**
    - https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
    - https://www.ebay.com/itm/176657492046
    - https://www.farnell.com/datasheets/3984938.pdf
    - https://docs.radxa.com/en/dragon/q6a
    - https://docs.radxa.com/en/dragon/q6a/hardware-use/mipi-dsi
    - https://forum.radxa.com/t/dragon-q6a-radxa-display-8hd-not-detected-on-ubuntu-24-04-noble-problem/30422
    - https://lore.gitlab.freedesktop.org/drm-ai-reviews/20260522060645.4399-6-graham.oconnor@gmail.com/
- **Budget option:**
  - **Name:** Waveshare 5in high-brightness capacitive LCD 5DP-CAPLCD-B (1024x600, 800 nits, optically bonded, HDMI + USB touch). For a bigger budget screen, the Orient Display 7in 1024x600 900-nit PCAP HDMI module at $107.88 is the step up.
  - **Why:** - Cheapest option that is still semi-sun-readable and has known-good, driver-free USB HID touch on Linux.
  - Optical bonding cuts reflections.
  - Very low power, about 2-3 W (estimate).
  - Works on the Q6A over HDMI once video=HDMI-A-1:1024x600@60 is set, which is exactly the case Radxa's FAQ documents.
  - Trade-off: low resolution and marginal readability in full midday sun. Pair it with a deep 3D-printed sun hood.
  - **Price:** About $63 (RobotShop US) / EUR 65 in the EU; Orient Display 7in at $107.88
- **Risks:**
  - Above FHD and bright do not coexist off the shelf. Every above-FHD 5.5-9in module found is 310-500 nits. The only bright above-FHD parts are bare panels (Midas 7in WUXGA 2500 nits; Wisecoco 8.4in 2560x1600 2000 nits) that need custom drive electronics.
  - Wisecoco listings contradict each other (2000 / 2400 / 2500 nits; HDMI vs MIPI; touch interface, input voltage and lamination not stated; no datasheet). Get written confirmation and photos of the HDMI board and touch controller before paying. eBay expedited shipping was $50-80.
  - Camera field monitors (FEELWORLD, Desview, Portkeys, NEEWER, BenQ, Lilliput H7s): touch controls only the monitor's on-screen menus. None of the spec sheets I read list a USB-HID touch output, so they cannot replace a touchscreen. They are also 9-20 W and 235-693 g.
  - Q6A HDMI caveats. The official cap is 4K@30. The output is a 2-lane DP link through the RA620 bridge, and mainline patches cap DP voltage swing at level 2 because link training failed at level 3. Radxa warns that 'some monitors may be incompatible'. I found no community report above 1080p on the Q6A, so 2560x1600@60 is theoretically within the link but untested.
  - DSI route: Radxa supports only its own two panels. The official 8HD stays black on Ubuntu 24.04 because the image lacks the panel driver and overlay (Feb 2026 thread, no staff answer). Any third-party DSI panel needs your own device tree and driver work.
  - Thermal: in direct sun an LCD can reach its liquid-crystal clearing point and go fully black until it cools (Elo). Ratings: Wisecoco 8.4in -10 to 50 C only; Midas -20 to 70 C, and its 2500-nit drive mode carries a thermal warning. A 2000-nit backlight dissipates about 6 W inside the case.
  - Polarized sunglasses can black out an LCD at certain rotations, typically portrait vs landscape. Test before fixing the screen orientation in the case.
  - Battery cost of brightness (estimates, assuming the rest of the system draws about 15 W and about 61 Wh is usable from the 72 Wh pack): 350-nit 2.5K panel (+3 W) about 3.4 h; 2000-nit 7in at full (+8 W) about 2.6 h; 3000-nit field monitor at its 20 W spec maximum about 1.7 h.
  - AMOLED HDMI kits: only about 310 nits, plus burn-in with the static SDR++/SatDump UI. Waveshare warns against static images longer than about 1 hour.
  - Cheap HDMI-to-MIPI boards often report wrong or portrait-only EDID modes. A Sudomod user's Wisecoco OLED board worked on Windows but showed nothing on a Pi. Touch does not rotate together with the image.
  - Midas lead time is about 12 weeks; Waveshare's 9in 2.5K is discontinued at some resellers. October 2026 prices and stock for most items were not live-verified, and the UAH/USD conversion (about 41.5) is approximate.
- **Integration notes:**
  - Connection: use HDMI from the Q6A (DSI only for the advanced Midas build). Put touch on a USB 2.0 port; the hid-multitouch driver needs no setup. The LimeSDR is on PCIe, so the RTL-SDR, touch and one spare port fit on the 3x USB 2.0.
  - Forcing a mode (Radxa FAQ fix): echo "$(cat /etc/kernel/cmdline) video=HDMI-A-1:1920x1080@60" | sudo tee /etc/kernel/cmdline; then sudo kernel-install add $(uname -r) /boot/vmlinuz-$(uname -r); then reboot. Check the panel's EDID first with: sudo edid-decode /sys/class/drm/card1-HDMI-A-1/edid
  - Bad EDID (my own fix, not found on forums): load a corrected EDID with drm.edid_firmware=HDMI-A-1:edid/panel.bin (file in /lib/firmware/edid). Append 'e' to the video= argument (e.g. video=HDMI-A-1:1920x1080@60e) to force the output on even when the board is not detected at boot.
  - Above-1080p tests: use reduced-blanking modes. 2560x1600@60 RB is 268.5 MHz (6.44 Gbps) and fits the 2-lane HBR2 limit of 8.64 Gbps. Standard CVT is 348.5 MHz and exceeds the 340 MHz HDMI 1.4 TMDS limit, so avoid it. Generate modes with cvt -r.
  - Rotation for portrait-native boards: rotate in GNOME/KDE settings, or with xrandr --output HDMI-1 --rotate left. Then fix touch with a udev rule setting ENV{LIBINPUT_CALIBRATION_MATRIX} (e.g. '0 -1 1 1 0 0' for 90 degrees) and map the touch device to the HDMI output. Riverdi and Pi forum reports say a reboot or compositor restart may be needed, and that OSD rotation breaks touch alignment.
  - GPU: the Adreno 643 works under Freedreno/Turnip (OpenGL 4.6, Vulkan 1.3, KDE Plasma Wayland reported in May 2026 mainline patches). Radxa's own image uses the open Mesa drivers. 1080p waterfalls are easy; 2.5K costs about 1.8x the fill rate.
  - UI: on a 7in FHD screen set SDR++ UI scaling to about 150-200%. The SDRIAK fork (formerly SDR++ iak; v1.4.0-beta2, Sept 2026) adds a touch overlay, drag-to-tune, a frequency keypad and high-DPI fixes. It ships Linux AppImage/deb builds, but ARM64 is not confirmed, so you may have to build it from source.
  - Power: feed the display board from a dedicated 12 V buck converter off the 4S pack, not from a Q6A USB port. A 2000-nit backlight needs about 16-19 V at 0.4-0.5 A, which the board generates by boosting its input (Midas datasheet). Power the display before or together with the Q6A so EDID is readable at boot.
  - Cabling: keep the HDMI run short (about 20 cm or less) with a quality flat or FPC HDMI cable. The Q6A's DP-to-HDMI link already needs a voltage-swing workaround, so marginal cables cause blanking or sparkles.
  - Mechanics: the 7in kit outline is about 164x98 mm, with the board stacked behind it. Plan a front face of about 175x110 mm, a 15-25 mm 3D-printed sun hood, a light-coloured case, and an air gap or vent behind the backlight (about 6 W at 2000 nits). Mount with the polarizer axis tested against polarized sunglasses.
  - Optics: prefer full lamination or optical bonding with AR glass (Midas has an AR cover lens with in-cell touch). Air-gap touch glass adds two reflective interfaces and destroys sunlight contrast. A matte anti-glare film helps against specular glare but slightly softens a high-PPI image.
- **Double duty opportunities:**
  - One 12-13 V buck rail can feed both the display driver board (if it accepts 12-13 V) and the QO-100 LNB bias-tee injector (13 V). Give each load its own LC filter, because backlight PWM noise on the LNB feed would show up in the RF.
  - Field monitors (7-24 V), the Lilliput 719/T (9-36 V) and the BenQ PVS7 (6.5-16.8 V) can run directly from the 4S pack (12.8-16.8 V), so the display needs no separate buck converter.
  - A $2-5 BH1750 or VEML7700 ambient-light sensor on the same I2C bus as the BNO085 can auto-dim the backlight and save about 3-5 W in shade or at dusk. With the DSI-direct Midas build, the backlight sits under the Linux backlight class, which makes this trivial. With HDMI boards, check whether brightness can be set over DDC/CI (ddcutil) or a PWM pin; this is unverified.
  - Driving the Midas panel directly over DSI removes the HDMI-to-MIPI bridge board (about 1-2 W and about $30-60) and frees the HDMI port for an external monitor at home.
  - A hinged 3D-printed sun hood doubles as a protective screen lid in the backpack.
  - Field monitors' built-in light sensor and auto-dimming (LUT5/LUT7) replaces a separate lux sensor if you go that route, but you would still need an encoder for input.
- **Confidence:** medium

_Run `wf_2f1a700c-867`_

- **Component:** Display (high-res, beautiful, sunlight-readable touchscreen for Radxa Dragon Q6A handheld)
- **Current pick assessment:** The v3 spec ("5-7 inch DSI or HDMI touchscreen, ~$60-100") has two weak points. (1) DSI is high-risk on the Q6A. Radxa's Q6A MIPI DSI page (one 4-lane port, 39-pin 0.3 mm FPC) says that "only the Radxa official displays listed are supported": Display 8 HD (8", 800x1280) and Display 10 FHD (10.1", 1200x1920). It adds that third-party panels, including Raspberry Pi panels, are not adapted. Neither Radxa product page lists the Q6A under "works with". Forum reports from Feb to May 2026 show even the official 8HD failing on the Q6A: the driver is missing from the Ubuntu 24.04 kernel 6.1.y image, and on Radxa's noble image the panel is detected as DSI-1 800x1280 with the backlight on but the screen stays black. No fix has been posted. (2) Typical $60-100 hobby screens give 300-500 nits, which washes out in direct sun. Examples: RPi Touch Display 2 at 500 cd/m2, Waveshare 7" FHD 1080x1920 at about 350 nits, Waveshare 8" 2K at 470 cd/m2. The obvious "beautiful" pick, the Waveshare 5.5" AMOLED 1080x1920 ($121.99), tops out at only 310 cd/m2 (5 steps: 75-310) and has burn-in risk with a static SDR UI. The Q6A's USB-C is a 12 V power input only, with no DP alt mode, so USB-C-only portable monitors are out. Use HDMI (HDMI 2.0, up to 4K30, so 1080p60 is fine) plus a USB-HID touch connection. That path needs no drivers and is the lowest-risk route.
- **Alternatives:**
  1.
    - **Name:** Lilliput 719/T (7in, 1000 nit, PCAP)
    - **Key specs:** 7in 1280x800 (216 PPI), 1000 nits, 10-point PCAP touch over USB-C to host; HDMI + VGA + USB-C video inputs; DC 9-36 V input; 8.5 W max at 12 V; 184.5x118.8x32 mm; 410 g. Optical bonding not stated. Variant 719H/T adds an IP65 frame.
    - **Price:** $259 (Markertek list, out of stock in Oct 2026, ships 5-14 days when available); EU via Syntex (CZ), price not verified
    - **Pros:** Only verified option that is ≥1000 nits AND sends multi-touch to the host. Plain HDMI + USB HID with zero drivers. Runs directly from the 4S pack (12-16.8 V sits inside 9-36 V), so no separate display buck is needed. Rugged metal housing.
    - **Cons:** Thick (32 mm) and heavy (410 g), so it pushes the device to tablet size. Resolution is only 1280x800. Expensive. Stock is spotty.
    - **Sources:**
      - https://www.markertek.com/product/lil-719-t/lilliput-719-t-7in-1000-nit-highbright-10-point-touch-screen-monitor-1280x800-hdmi-vga-usb-c
      - https://www.syntex.tv/lilliput-719-t
    - **Q6a compatibility:** HDMI video + USB touch: generic, low risk. Q6A USB-C cannot feed it video (power-only port), so use an HDMI cable plus a USB-C-to-A cable for touch.
    - **Availability:** US Markertek out of stock; EU distributor Syntex lists it; check before ordering
  2.
    - **Name:** FEELWORLD F6 PLUSX / F5 PROX (5.5in 1080p 1600-nit field monitors)
    - **Key specs:** 5.5in IPS 1920x1080 (400 PPI), 1600 cd/m2, 1000:1. F6 PLUSX: HDMI in/out + USB-C, DC 7-24 V, ≤10 W, about 148x93x20 mm, about 235 g. F5 PROX: HDMI + USB-C, powered from 5 V/2 A USB-C or a battery. The touchscreen controls the monitor's own OSD only; no host touch confirmed.
    - **Price:** F6 PLUSX €178-232 at EU shops, €269 at Calumet (about 3-month lead time); F5 PROX $159.99 (Walmart), €174 incl. VAT (Adcom IT), €185 (Mediagear EE)
    - **Pros:** Most 'beautiful + sunlight' image found: 1080p at 400 PPI and 1600 nits in a palm-size 5.5in body. F6 PLUSX runs directly from the 4S pack (7-24 V). Sun hoods and mounts are widely available. HDMI only, zero drivers.
    - **Cons:** No touch input to the Q6A (OSD touch only), so it needs encoder/buttons or a mini trackpad for SDR++/SatDump. About 20 mm thick. Up to 10 W. The 3000-nit LUT5 draws about 20 W and has a fan, so avoid it.
    - **Sources:**
      - https://www.calumet.de/product/feelworld-fieldmonitor-f6-plusx-5-5
      - https://masterfoto.lv/en/external-lcd-displays/11376-feelworld-f6-plusx-55-hdmi-monitor-1600nit-d252811.html
      - https://www.bhphotovideo.com/c/product/1771210-REG/feelworld_f5prox_f5_pro_x_5_5.html
      - https://mediagear.ee/product/5-5-feelworld-monitor-f5prox/
      - https://www.adcom.it/en/richiedi-consiglio/71064
      - https://cined.com/?p=218333
    - **Q6a compatibility:** HDMI 1080p60: no risk. No touch HID.
    - **Availability:** EU photo retailers, some with long lead times; widely sold on AliExpress (price not verified)
  3.
    - **Name:** Waveshare 8inch 2K Capacitive Touch Display (1536x2048, optical bonding)
    - **Key specs:** 8in IPS 1536x2048 (320 PPI), 470 cd/m2, 1000:1, optically bonded toughened glass, 10-point USB-C touch, standard HDMI, 4 W (800 mA at 5 V), 190x128x11 mm, CNC alloy case, speaker + 3.5 mm jack, button backlight control
    - **Price:** $109.99 (Waveshare)
    - **Pros:** Sharpest and best-looking LCD found at hobby price. Optical bonding cuts reflections. Thin (11 mm) and low power. HDMI audio goes to the built-in speaker and jack, which handles SSTV/voice monitoring with no USB sound card.
    - **Cons:** 470 nits is marginal in direct sun (shade or sun hood needed). 8in is beyond palm size. Portrait-native 1536x2048 timing through the Q6A's HDMI path has not been tested (Waveshare warns weak GPUs struggle; the Adreno 643 should be fine).
    - **Sources:**
      - https://www.waveshare.com/8inch-1536x2048-lcd.htm
      - https://www.waveshare.com/wiki/8inch_1536x2048_LCD
    - **Q6a compatibility:** HDMI + USB HID touch: low risk. Needs rotation and a touch-matrix transform (xrandr/GNOME + libinput). Odd mode acceptance on the Q6A is unverified.
    - **Availability:** In stock at Waveshare; also AliExpress Waveshare store
  4.
    - **Name:** Waveshare 5.5inch HDMI AMOLED (1080x1920)
    - **Key specs:** 5.5in AMOLED 1080x1920 (400 PPI), 170 deg viewing angle, 5-point USB touch, 6H glass. Max 310 cd/m2 (steps 75/140/210/260/310). 5 V: about 650 mA all-white, 250 mA all-black. Panel+PCB 4.8 mm, 11 mm with HDMI holder. 3.5 mm audio.
    - **Price:** $121.99 (Waveshare)
    - **Pros:** Deepest blacks and most 'beautiful' look indoors. Very thin. Low power on a dark SDR++ theme.
    - **Cons:** NOT sunlight-readable (310 nits max). Waveshare warns about burn-in from static content beyond about 1 hour, a poor fit for fixed waterfalls and menus. Glass is fragile.
    - **Sources:**
      - https://www.waveshare.com/5.5inch-HDMI-AMOLED.htm
      - https://www.waveshare.com/wiki/5.5inch_HDMI_AMOLED
    - **Q6a compatibility:** HDMI + USB touch: low driver risk; portrait-native, needs rotation
    - **Availability:** In stock (Waveshare, Core Electronics, Switch Science). The 6in 1080x2160 AMOLED sibling ($139.99) is discontinued.
  5.
    - **Name:** Riverdi RVT70HSHNWC00-B (7in HDMI, optical bonding)
    - **Key specs:** 7in IPS 1024x600 (170 PPI), about 850 cd/m2 (Unisystem listing), optically bonded uxTouch PCAP, USB-C touch, HDMI
    - **Price:** $177.68 (Riverdi web shop); air-bonded RVT70HSHNWC00 $156.65
    - **Pros:** Industrial quality, optically bonded and bright. Made in Poland, so EU shipping to Ukraine is easy.
    - **Cons:** Low resolution, not 'beautiful'. Brightness and power figures come from distributor listings only.
    - **Sources:**
      - https://riverdi.com/product-category/hdmi-displays
      - https://unisystem.com/product/ecrans-lcd-tft/rvt70hshnwc00-b-riverdi-hdmi-display
      - https://www.mouser.it/riverdi-7inch-hdmi-displays
    - **Q6a compatibility:** HDMI + USB HID: low risk
    - **Availability:** Riverdi shop, Mouser, Unisystem (EU)
  6.
    - **Name:** Raspberry Pi Touch Display 2 (5in / 7in)
    - **Key specs:** 720x1280 (5in: 294 PPI, 7in: 210 PPI), 500 cd/m2, anti-glare, 5-finger touch, DSI 2-lane, power from GPIO; 5in 91.5x143.4 mm, 7in 120.2x189.3 mm, about 15 mm deep; -20 to +70 C
    - **Price:** $40 (5in) / $60 (7in) list
    - **Pros:** Cheap, well documented, in production to at least Jan 2030
    - **Cons:** Not supported on the Q6A (Radxa explicitly names the RPi 7in as not adapted). The Q6A connector is 39-pin 0.3 mm, so it needs a custom adapter plus a panel driver and device tree. 500 nits is not sunlight-grade.
    - **Sources:**
      - https://pip-assets.raspberrypi.com/categories/1083-raspberry-pi-touch-display-2/documents/RP-009106-MM-8-touch-display-2-product-brief.pdf
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/mipi-dsi
    - **Q6a compatibility:** HIGH RISK / effectively unsupported
    - **Availability:** Widely available
  7.
    - **Name:** Radxa Display 8 HD (official DSI)
    - **Key specs:** 8in TFT 800x1280 (189 PPI), 5-point capacitive, MIPI DSI 2/4-lane, 39-pin 0.3 mm to 40-pin 0.5 mm FPC; brightness not published
    - **Price:** Not published (Approved Partners only); not verified
    - **Pros:** Only DSI panel Radxa names for the Q6A; single-cable
    - **Cons:** Low resolution. Unknown brightness. Q6A users (Feb-May 2026) report black screen or no driver on Ubuntu 24.04, with no fix posted. Not listed under 'works with' on its own product page.
    - **Sources:**
      - https://radxa.com/products/accessories/display-8hd
      - https://forum.radxa.com/t/dragon-q6a-radxa-display-8hd-not-detected-on-ubuntu-24-04-noble-problem/30422
      - https://forum.radxa.com/t/radxa-dragon-q6a-firmware-snapshot/28886?page=2
    - **Q6a compatibility:** Officially listed, but practically unproven and buggy
    - **Availability:** Through Radxa partners / AliExpress
  8.
    - **Name:** Generic AliExpress/eBay 7in 1920x1080 2000-2400 nit IPS + HDMI driver board + touch kits (Wisecoco-type)
    - **Key specs:** Listings claim 7in 1920x1080 IPS, 2000-2400 nits, 1000:1, HDMI driver board, touch. Panel model, touch type, power and thickness NOT verified (pages blocked).
    - **Price:** Unverified
    - **Pros:** Potentially the ideal combination (1080p + sunlight + host touch) if the claims hold
    - **Cons:** Specs unverified and inconsistent between listings. A 2000-nit backlight probably draws well over 10 W (unverified). DIY bare module.
    - **Sources:**
      - https://www.ebay.de/itm/405247794619
      - https://www.ebay.de/itm/176594983531
    - **Q6a compatibility:** HDMI + USB HID expected: low driver risk, but quality is unknown
    - **Availability:** Uncertain
- **Recommended:**
  - **Name:** Lilliput 719/T (7in 1280x800, 1000 nits, 10-pt USB PCAP, 9-36 V DC) on HDMI + USB. Beauty-first fallback if mostly used in shade: Waveshare 8in 2K (1536x2048, 470 nits, $109.99).
  - **Why:** Among verified products, only the 719/T meets all the hard requirements together: ≥1000 nits for direct sun, real multi-touch to the host over USB, and a zero-driver HDMI + HID path that avoids the Q6A's broken/unsupported DSI path. Its 9-36 V input lets it run straight off the 4S 21700 pack, so no display buck converter is needed, and it draws 8.5 W max. At 7in, 216 PPI is crisp enough for SDR++ waterfalls and SatDump. Accept the trade-offs: about 32 mm thick, 410 g, $259, and spotty stock. If the device will mostly be used in shade or under a hood, the Waveshare 8in 2K is the most beautiful low-risk option: 320 PPI, optically bonded, 4 W, 11 mm, plus a built-in speaker. If you would give up touch for 400 PPI at 1600 nits in a true palm size, use a FEELWORLD F6 PLUSX (≤10 W, 7-24 V direct) with a rotary encoder or mini trackpad.
  - **Price:** $259 (Markertek list); Waveshare 8in 2K $109.99
  - **Sources:**
    - https://www.markertek.com/product/lil-719-t/lilliput-719-t-7in-1000-nit-highbright-10-point-touch-screen-monitor-1280x800-hdmi-vga-usb-c
    - https://www.waveshare.com/wiki/8inch_1536x2048_LCD
    - https://docs.radxa.com/en/dragon/q6a/hardware-use/mipi-dsi
    - https://docs.radxa.com/en/dragon/q6a
- **Budget option:**
  - **Name:** Waveshare 5inch High-Brightness Capacitive Touch Screen, 1024x600 IPS, HDMI, 800 cd/m2 (5DP-CAPLCD-H narrow-bezel or -B)
  - **Why:** Cheapest verified screen that is genuinely brighter than the hobby norm: 800 cd/m2 per Robotshop and The Pi Hut, about 1.6x a Pi Touch Display 2. 237 PPI at 5in is sharp enough for a palm-size device. Toughened glass and USB multi-touch, connected over HDMI with no drivers on the Q6A. Avoid the resistive -G variant (single-point). Power, thickness and bonding are not verified.
  - **Price:** $46.99-54.99 (Waveshare), $63.16 (Robotshop US), £52.80 (The Pi Hut), €64.95 (openelab EU, sold out at time of listing)
- **Risks:**
  - Q6A DSI: Radxa supports only its own 8HD/10FHD panels, and Q6A users reported black screens or missing drivers on Ubuntu 24.04 from Feb to May 2026 with no fix posted. Do not plan on any DSI panel, including the RPi Touch Display 2 and Waveshare DSI panels.
  - Q6A USB-C is a 12 V power input only (no DP alt mode). USB-C-only portable monitors and the 719/T's single-cable USB-C video will not work; use HDMI.
  - Brightness vs power: 1000-1600 nit backlights draw 8.5-10 W at full brightness, about 12-14% of a 72 Wh pack per hour. Unverified 2000+ nit kits likely draw more. Use auto/manual dimming.
  - AMOLED (Waveshare 5.5in) is limited to 310 cd/m2 and Waveshare warns about burn-in after about 1 hour of static content, a poor match for a fixed SDR UI.
  - Portrait-native HDMI panels (1080x1920, 1536x2048) need rotation and a libinput touch calibration matrix. Acceptance of non-standard HDMI timings on the Q6A HDMI path has not been verified.
  - Direct-sun heating: LCDs can black out when the panel overheats (RPi TD2 is rated for up to +70 C). Use a sun hood and leave an air gap behind the panel.
  - Field monitors (FEELWORLD) touch only their own OSD, so you must add an encoder or trackpad for host control.
  - Availability: Lilliput 719/T was out of stock at Markertek; F6 PLUSX showed about 3-month lead time at Calumet; Waveshare 6in AMOLED is discontinued.
  - Research limit: the web-search budget ran out mid-task, so AliExpress 7in 1080p 2000-2400 nit kits, Waveshare 5in HB power/thickness, and Ukrainian-store prices (Prom.ua/Rozetka) could not be verified.
- **Integration notes:**
  - Use the Q6A HDMI port (HDMI 2.0, up to 4K30): 1080p60 or 1280x800 is no problem. Connect touch to a USB 2.0 Type-A port (3 available; the RTL-SDR uses one).
  - Lilliput 719/T / FEELWORLD F6 PLUSX: feed from the 4S pack (12.0-16.8 V) through a 2 A fuse and a soft switch; this is within the 9-36 V and 7-24 V ranges.
  - Waveshare 8in 2K / 5.5in AMOLED / 5in HB: feed from a 5 V buck rated ≥1.5 A (8in 2K needs 800 mA, AMOLED about 650 mA all-white), not from a Q6A USB port.
  - To keep the stack thin, use flat FPC HDMI cables with right-angle HDMI and micro-HDMI adapters. Mount the Q6A behind the display with the fan exhausting away from the panel.
  - Software: on Ubuntu 24.04 GNOME (Wayland), set rotation in display settings and map touch to the HDMI output. On X11, use xrandr --rotate plus xinput set-prop 'Coordinate Transformation Matrix'. hid-multitouch should give multi-touch, but Waveshare only certifies multi-touch on Pi OS and Windows.
  - For sunlight: add a fold-out matte sun hood (field monitor hoods fit 5.5-7in). Use a matte anti-glare film only on non-bonded panels. Use a high-contrast SDR++ theme and larger UI scaling.
  - Physical controls (rotary encoder for frequency or zoom, plus 2-3 buttons via the 40-pin GPIO or a USB HID macro pad) are worth adding with any touch screen, since gloves and sweat make touch unreliable outdoors.
- **Double duty opportunities:**
  - Wide-input displays (Lilliput 719/T 9-36 V, FEELWORLD F6 PLUSX 7-24 V) run straight from the 4S pack, removing a dedicated display buck converter.
  - HDMI audio from the Q6A to the display's speaker or 3.5 mm jack (Waveshare 8in 2K, 5.5in AMOLED, 7in FHD) gives an audio monitor for ISS voice, SSTV tones and CubeSat beacons with no USB sound card or amplifier.
  - A display with a metal CNC case (Waveshare 8in 2K) can double as the front structural plate of the 3D-printed enclosure and a mounting point for the IMU and GNSS, away from the fan.
  - FEELWORLD F6 PLUSX has an HDMI loop-out, so a second viewer or goggles can be attached for demos without any extra hardware on the Q6A.
- **Confidence:** medium

## Форуми та досвід спільноти (`forums`)

_Run `wf_0e70c405-a03`_

- **Component:** Display: very bright (ideally 1000 nits or more), ideally above Full HD, capacitive touch, for a Radxa Dragon Q6A (QCS6490) handheld used in direct sun. Candidates: Wisecoco 7in 1080p 2000-2500 nit HDMI kit (recommended), Midas 7in 1200x1920 2500 nit DSI panel (upgrade), Waveshare 5DP-CAPLCD 800 nit (budget), field monitors (FEELWORLD LUT7/LUT5/F6 PLUSX), Waveshare/Wisecoco 2560x1600 kits, Lilliput 719/T.
- **Experiences:**
  1.
    - **Product:** Radxa Dragon Q6A HDMI + Samsung G80SD 4K monitor
    - **Source url:** https://forum.radxa.com/t/samsung-g80sd-can-not-negotiate-resolution-refresh-rate/31118
    - **Community:** Radxa forum
    - **What they built:** Q6A desktop on Radxa OS with a 4K HDMI monitor (3 Jul 2026)
    - **Problems:**
      - Mode negotiation failed and the output fell back to 1024x768@60
    - **Fixes:**
      - The poster forced 4K 'by messing with commands' but did not post the commands or the refresh rate
    - **Outcome:** Unresolved. No replies and no staff answer. This is the only above-FHD report on Q6A HDMI besides the 2.5K one below.
  2.
    - **Product:** Radxa Dragon Q6A HDMI on a 2.5K screen (T4 image)
    - **Source url:** https://forum.radxa.com/t/upcoming-radxa-dragon-q6a/26723/51
    - **Community:** Radxa forum
    - **What they built:** Willy Tarreau ran the Q6A desktop on a screen he describes as 2.5K and tested YouTube in Firefox (25 Oct 2025)
    - **Problems:**
      - Video playback was jerky (software decode)
      - The SoC reached about 77 C on a thermal camera
    - **Fixes:**
      - A small aluminium heatsink helped
      - Mecid suggested Chromium from amazingfate's PPA for hardware decode and forcing H.264, because of a Venus VP9 bug
    - **Outcome:** An above-FHD desktop worked (implied by 'matches my screen resolution'). Heat matters even with no SDR load.
  3.
    - **Product:** Radxa Dragon Q6A HDMI after the kernel 7.0.11 upgrade
    - **Source url:** https://forum.radxa.com/t/linux-7-0-hdmi-not-working/31304
    - **Community:** Radxa forum
    - **What they built:** Ubuntu 24.04 Q6A desktops
    - **Problems:**
      - After apt full-upgrade from 6.18.2 to 7.0.11, HDMI went black once Linux started and the connector read 'disconnected'
      - Logs showed a DP AUX IRQ error and 'Cannot find any crtc or sizes'; hotplug then stayed dead
      - Unbinding and rebinding msm_dpu crashed the board
    - **Fixes:**
      - Roll back the complete 6.18.2 kernel, initramfs and DTB (the 6.18 DTB alone with 7.0.11 did not help)
      - Oleksii_Bezuhlyi: update the SPI firmware, then use a LONG press of the power button after poweroff (a short press or reboot stayed black)
      - Use a serial console (1.8 V UART) for recovery
    - **Outcome:** On 9 Sep 2026 Mr Dragon reported 'HDMI works now after the latest kernel updates' (version not given). Radxa never blocked the bad package.
  4.
    - **Product:** Radxa Dragon Q6A HDMI on Linux 7.0 via rsetup
    - **Source url:** https://forum.radxa.com/t/latest-q6a-update-to-linux-7-0-no-hdmi/31288
    - **Community:** Radxa forum
    - **What they built:** Ubuntu desktop on Q6A
    - **Problems:**
      - No HDMI after the first boot on 7.0.11-4-qcom
      - 6.18.2-4-qcom had HDMI but no sound card
    - **Fixes:**
      - Radxa staff (chenchongbiao, 1 Sep 2026): the 7.0 kernel switches off clocks left on by EDK2, which causes DP AUX interrupt storms. Fix: sudo sed -i 's/kasan=off/kasan=off clk_ignore_unused/' /etc/kernel/cmdline; sudo kernel-install add $(uname -r) /boot/vmlinuz-$(uname -r); reboot
    - **Outcome:** The workaround was posted, but the OP never confirmed it. The sed only matches if the cmdline already contains kasan=off.
  5.
    - **Product:** Community Ubuntu 26.04.1 image for Q6A (kernel 7.2.9, Armbian edge)
    - **Source url:** https://forum.radxa.com/t/ubuntu-26-04-1-lts-images-for-the-radxa-dragon-q6a-now-on-linux-7-2-9-hdmi-works-wi-fi-bt-audio-npu-apt-upgrade-safe/31574
    - **Community:** Radxa forum
    - **What they built:** rafaelwms' v1.3.0 desktop and server images (7 Oct 2026)
    - **Problems:**
      - HDMI broke on 7.0 and 7.2.3 kernels
    - **Fixes:**
      - Kernel 7.2.9 with the DisplayPort/DPU patches Armbian carries for QCS6490 makes HDMI work; KERNEL_BRANCH=current is the fallback
    - **Outcome:** HDMI works on one board, tested by one person. No reports on specific monitors or touchscreens.
  6.
    - **Product:** Radxa Dragon Q6A + Acer Nitro XV272U (a 2560x1440-class monitor)
    - **Source url:** https://forum.radxa.com/t/dragon-q6a-no-video-output/29681
    - **Community:** Radxa forum
    - **What they built:** Q6A desktop on the T4 image
    - **Problems:**
      - No video signal at all, while the board booted
    - **Fixes:**
      - Mecid: test a plain 1080p60 monitor; newer images fix this by enabling DPU 'virtual planes' (freedesktop msm issue #86)
    - **Outcome:** Not confirmed by the OP. My own check: in mainline the sc7280/QCS6490 DPU catalog has .max_linewidth = 2400, so any mode wider than 2400 px (2560x1440, 2560x1600 landscape) needs virtual planes (two SSPPs per plane). Current mainline sets dpu_use_virtual_planes = true by default.
  7.
    - **Product:** Radxa Display 8 HD (official DSI panel) on Q6A
    - **Source url:** https://forum.radxa.com/t/only-backlight-on-8hd/30822
    - **Community:** Radxa forum
    - **What they built:** Q6A with the official 8in DSI touch panel
    - **Problems:**
      - Only the backlight lit, with no image; HDMI also stopped after running rsetup
      - In related threads (30422, 30454) the panel stayed black on Ubuntu 24.04. The image has no panel module and no Qualcomm overlay in /boot/dtbo. In one case DRM reported DSI-1 connected and the Goodix touch worked, but vblank ran at exactly half the mode rate
    - **Fixes:**
      - liliiii (29 Jul 2026): the panel flex is revision AD001, but rsetup loads the AD002 overlay. Check the flex marking and use a matching overlay or driver
    - **Outcome:** The fix is user-found. Radxa staff asked for the image version and never posted a fix. Thread 30454 (Sep 2026) is still unresolved.
  8.
    - **Product:** Q6A HDMI + Waveshare 3.5in SPI LCD (dual display)
    - **Source url:** https://forum.radxa.com/t/dragon-q6a-spi-display-overlay-disables-hdmi-output-in-gnu-mode/30490
    - **Community:** Radxa forum
    - **What they built:** HDMI main screen plus a small SPI status screen
    - **Problems:**
      - With the SPI overlay enabled, both screens went blank; hot-plugging HDMI blanked both
    - **Fixes:**
      - None. Under Xorg, HDMI works and the SPI panel stays in standby
    - **Outcome:** Accepted staff answer (24 Mar 2026): 'no current plans to support dual-display (HDMI + SPI)'. A secondary SPI status display is not an option.
  9.
    - **Product:** Q6A DSI connector J10 with a third-party 7in DSI touch screen
    - **Source url:** https://forum.radxa.com/t/radxa-q6a-connection-to-7-inch-dsi-touch-screen/31373
    - **Community:** Radxa forum
    - **What they built:** Attempt to connect a 7in DSI panel
    - **Problems:**
      - The J10 pin count, pitch and pinout are not documented; no Pi-style 0.3 mm to 1.0 mm adapter is known
    - **Fixes:** []
    - **Outcome:** Unanswered (27 Aug 2026).
  10.
    - **Product:** QCS6490 mainline DP: RA620 bridge link-training patch
    - **Source url:** https://lore.gitlab.freedesktop.org/drm-ai-reviews/20260522060645.4399-4-graham.oconnor@gmail.com/
    - **Community:** Linux kernel lists (drm, via lore)
    - **What they built:** Graham O'Connor's mainline enablement series for the Q6A
    - **Problems:**
      - The RA620 'does not acknowledge DP link training at voltage swing level 3', so HDMI fails on mainline
    - **Fixes:**
      - Set DP_TRAIN_LEVEL_MAX to 2 in drivers/gpu/drm/msm/dp/dp_link.h, matching the vendor kernel
    - **Outcome:** Patch posted 22 May 2026 and under review. The series' patch 5/6 also disables DSI as 'not present', which conflicts with the Q6A's real DSI connector, so mainline DSI support is behind.
  11.
    - **Product:** Wisecoco 5.5in HDMI-to-MIPI kit (1080x1920 portrait EDID)
    - **Source url:** https://forums.raspberrypi.com/viewtopic.php?t=373978
    - **Community:** Raspberry Pi forums
    - **What they built:** CM4 with a Wisecoco 5.5in panel
    - **Problems:**
      - The image filled only part of the screen, with flicker lines, a green tint and wrong scaling, while the panel worked on Windows
      - The EDID holds a single portrait timing: 1080x1920, 134.49 MHz, HFP48/HS6/HBP25, VFP8/VS2/VBP4
    - **Fixes:**
      - 6by9 (Raspberry Pi engineer): don't hand-edit timings; use KMS and let the EDID drive the mode
      - sanore1 (1 Nov 2024) posted a working config: hdmi_force_hotplug=1, hdmi_force_mode=1, hdmi_group=2, hdmi_mode=87, hdmi_timings=1080 1 8 2 4 1920 1 48 6 25 0 0 0 60 0 134490000 3, dtoverlay=vc4-fkms-v3d
    - **Outcome:** Worked for one user with exact EDID-matched timings. The board is portrait-native and needs rotation.
  12.
    - **Product:** Wisecoco 8.9in 2560x1600 HDMI kit
    - **Source url:** https://forums.raspberrypi.com/viewtopic.php?t=384136
    - **Community:** Raspberry Pi forums
    - **What they built:** Pi Zero 2W handheld with a 2.5K panel
    - **Problems:**
      - Console worked but X failed, because the vendor config disabled vc4-kms-v3d
      - The board's 225.18 MHz pixel clock exceeds the 162 MHz Pi0-3 limit
    - **Fixes:**
      - 6by9: patch the kernel limit to about 226 MHz, or move to a CM4/CM5 carrier
    - **Outcome:** Unresolved. Useful data point: this 2560x1600 board uses a tight 225 MHz timing, which is about 5.4 Gbps at 24 bpp and well within the Q6A's 2-lane DP budget (my calculation).
  13.
    - **Product:** Wisecoco 7in HDMI touchscreen on Pi 5
    - **Source url:** https://forums.raspberrypi.com/viewtopic.php?t=368455
    - **Community:** Raspberry Pi forums
    - **What they built:** Pi 5 kiosk
    - **Problems:**
      - Touch stopped working after an OS update; a few days later the display also failed on a Pi 3
    - **Fixes:**
      - Diagnosis only: the touch enumerated as a CH57x USB HID device handled by hid-multitouch, with no dmesg errors
    - **Outcome:** Judged a display or cable hardware fault; the user moved to another display. It also shows that Wisecoco touch boards present standard USB HID (CH57x MCU).
  14.
    - **Product:** LT6911-based HDMI-to-DSI board (720x720) replaced by Wisecoco boards
    - **Source url:** https://forums.raspberrypi.com/viewtopic.php?t=393606
    - **Community:** Raspberry Pi forums
    - **What they built:** Pi 5 with a round panel via an HDMI-to-DSI bridge
    - **Problems:**
      - Wrong colours after every boot, fixed by re-plugging the cable; 6by9 suspected the bridge's initialisation
    - **Fixes:**
      - video=HDMI-A-1:720x720M@60D; workaround xrandr --output HDMI-1 --off && xrandr --output HDMI-1 --auto after login
      - Final fix: swap to Wisecoco interface boards
    - **Outcome:** Resolved by changing the board (Nov 2025). Cheap bridge boards vary in quality.
  15.
    - **Product:** Wisecoco 2K (2560x1600) and 2880x1440 HDMI kits on Pi 4
    - **Source url:** https://forums.raspberrypi.com/viewtopic.php?t=368182
    - **Community:** Raspberry Pi forums
    - **What they built:** Pi 4 with high-resolution Wisecoco panels
    - **Problems:**
      - 2560x1600: the image was duplicated twice on the right side (t=368182)
      - 2880x1440 (t=366160): the desktop boots in portrait and rotating it bounces back
    - **Fixes:**
      - 2880x1440: a 'resolution swap fixed the issue perfectly' (not detailed)
    - **Outcome:** 2560x1600: unresolved. 2880x1440: fixed. High-resolution kits often need a manual mode or EDID work.
  16.
    - **Product:** Waveshare 9in 2560x1600 HDMI monitor (USB touch)
    - **Source url:** https://www.waveshare.com/wiki/9inch_2560x1600_Monitor
    - **Community:** Waveshare wiki FAQ (vendor support notes)
    - **What they built:** Pi and PC secondary display
    - **Problems:**
      - 'You must set the resolution manually' on the Pi (hdmi_mode=87 plus custom hdmi_timings)
      - Flicker from an undersupplied USB power cable
      - Screen goes black on DPMS idle
    - **Fixes:**
      - External 5 V/2 A on the Power port
      - xserver-command=X -s 0 -dpms
      - Reboot the host if HDMI hot-plug is not detected
    - **Outcome:** Works with manual setup. Brightness is not even listed (about 350 nits per earlier research), so it is unsuitable in sun.
  17.
    - **Product:** Waveshare 5DP-CAPLCD 5in 1024x600 800 nit (budget pick)
    - **Source url:** https://www.waveshare.com/wiki/5DP-CAPLCD
    - **Community:** Waveshare wiki FAQ
    - **What they built:** HDMI plus USB-touch display for Pi and PC
    - **Problems:**
      - Typical draw is 4.2 W, and 'the input current must be >=850mA, otherwise it will cause startup failure or abnormal display'
      - The resolution must be set manually (the EDID does not drive 1024x600)
      - Brightness is adjustable only via the OSD
    - **Fixes:**
      - Pi: hdmi_cvt 1024 600 60 6 0 0 0. Q6A equivalent: video=HDMI-A-1:1024x600@60 (Radxa FAQ)
      - Power it from a dedicated 5 V/1-2 A rail
    - **Outcome:** Known-good. Power is about 4.2 W, not the 2-3 W estimated earlier.
  18.
    - **Product:** Waveshare 7in 1024x600 HDMI LCD on Pi 3 (KlipperScreen)
    - **Source url:** https://forum.core-electronics.com.au/t/problems-with-waveshare-7-lcd-screen/15007
    - **Community:** Core Electronics forum
    - **What they built:** 3D-printer touchscreen
    - **Problems:**
      - Interlace-like flicker and corruption
      - Ghost images, a purple edge line, then a white inverted screen
    - **Fixes:**
      - hdmi_drive=2 removed the flicker
      - The ghosting followed the panel to a Windows PC, so it was a hardware fault
    - **Outcome:** Warranty replacement (Sep 2022). Cheap HDMI kits have unit-to-unit quality variance.
  19.
    - **Product:** FEELWORLD LUT7 (7in 1920x1200, 2200 nit field monitor)
    - **Source url:** https://kounio.gr/katastima/video-2/monitors/feelworld-lut7-7-3d-lut-4k-hdmi-monitor/
    - **Community:** Retailer spec sheet + Adorama user review (https://www.adorama.com/felut7.html)
    - **What they built:** Camera field monitor considered as an SBC screen
    - **Problems:**
      - The HDMI input list contains only broadcast formats: 4K24/30, 1080p up to 60, 1080i, 720p, SD. No 1920x1200 or other PC modes
      - 20 W rated draw at 7-24 V/2 A
      - An Adorama reviewer (William R., Jul 2021) says it 'gets very warm to the touch during use'
    - **Fixes:**
      - Feed 1080p60 from the Q6A (video=HDMI-A-1:1920x1080@60) and accept the scaling to the 1920x1200 panel
    - **Outcome:** Its above-FHD panel cannot be used at native resolution from a PC source. Combined with no host touch and 20 W, this rules field monitors out of the primary role.
  20.
    - **Product:** FEELWORLD LUT5 (5.5in 3000 nit) / Osee T7
    - **Source url:** https://forum.blackmagicdesign.com/viewtopic.php?p=1039971
    - **Community:** Blackmagic Design forum (seen via search snippet; the page returned 403)
    - **What they built:** Outdoor camera rig
    - **Problems:**
      - A user reported the 3000-nit Osee T7 got very hot in direct sun
      - The vendor states the LUT5 runs about 2.5 h on an F970 7.4 V 6600 mAh battery, which is about 19.5 W average (my calculation)
    - **Fixes:**
      - The user moved to the smaller LUT5 with a cage and a sun hood for lower power
    - **Outcome:** Expect 15-20 W and significant heat at full brightness.
  21.
    - **Product:** SDR++ with a touchscreen on Linux Wayland
    - **Source url:** https://github.com/AlexandreRouma/SDRPlusPlus/issues/1569
    - **Community:** GitHub issues (SDR++, also #1631; GLFW #2791)
    - **What they built:** SDR++ on touch laptops (Arch, Ubuntu, Fedora)
    - **Problems:**
      - Touch is ignored in Wayland sessions but works on X11 and Windows, because GLFW has no wl_touch support (GLFW #2791; tracking issue #42 open since 2013)
    - **Fixes:**
      - The maintainer says the fix belongs upstream in GLFW and won't patch SDR++
      - My own fix from GLFW 3.4 platform.c: GLFW follows XDG_SESSION_TYPE, so launching with XDG_SESSION_TYPE=x11 sdrpp (or satdump) uses XWayland, where touch gets pointer emulation. Alternatives: log into a GNOME/KDE X11 session, or link against the X11-only libglfw3 build
    - **Outcome:** Unfixed upstream. The workaround is to run under XWayland or X11. SatDump also uses GLFW/ImGui, so the same applies.
  22.
    - **Product:** USB touchscreen to monitor mapping under GNOME/mutter
    - **Source url:** https://discourse.gnome.org/t/external-touch-screen-is-mapped-to-wrong-display/26089
    - **Community:** GNOME Discourse + Peter Hutterer's blog
    - **What they built:** Laptop with an external HDMI/USB touch monitor
    - **Problems:**
      - Touch landed on the wrong display; the device enumerated as a 'tablet', and the gsettings tablet output key and a libwacom entry did not help
    - **Fixes:**
      - Hutterer (https://who-t.blogspot.com/2024/03/enforcing-touchscreen-mapping-in-gnome.html): read vendor/product/serial from ~/.config/monitors.xml, then gsettings set org.gnome.desktop.peripherals.touchscreen:/org/gnome/desktop/peripherals/touchscreens/<vid>:<pid>/ output "['VEN','Product','Serial']"
    - **Outcome:** The Discourse case stayed unresolved for a tablet-class device. The blog method works for normal touchscreens. On a single-display handheld, mapping is simpler, but rotation must follow the mapped output.
  23.
    - **Product:** SDRIAK (formerly SDR++ iak) touch-oriented fork
    - **Source url:** https://github.com/bubnikv/sdriak/releases
    - **Community:** GitHub releases
    - **What they built:** Touch and Android-friendly SDR++ fork
    - **Problems:**
      - Release notes do not say whether Linux builds are aarch64
      - Wayland touch handling is not mentioned
    - **Fixes:**
      - v1.4.0-alpha/beta/beta2 (Jul-Sep): touch overlay, drag-scroll with fling, a frequency keypad (hold a digit 0.5 s), drag-to-tune inside the VFO, 125/175% scale presets, native-DPI handling
    - **Outcome:** The best UI candidate for a 7in touch screen, but it likely needs a source build on ARM64 and the X11/XWayland trick above.
  24.
    - **Product:** LimeSDR Mini + Raspberry Pi with a 5in TFT vs an HDMI display
    - **Source url:** https://discourse.myriadrf.org/t/80mhz-bandwidth-spectrogram-on-limesdr-mini/3356?page=2
    - **Community:** MyriadRF / Lime discourse
    - **What they built:** 80 MHz FPGA spectrogram on a LimeSDR Mini with Pi 3 + GQRX
    - **Problems:**
      - '5' TFT-Display created some noise in the spectrogram. This was not a problem with HDMI display' (gasparka, 6 Feb 2019)
      - Higher HDMI resolution with a large waterfall maxed the CPU
    - **Fixes:**
      - Switch to an HDMI display; keep the waterfall window size moderate
    - **Outcome:** An HDMI display was quieter than an SPI/TFT one near the SDR. Waterfall rendering cost scales with resolution.
  25.
    - **Product:** Raspberry Pi + RTL-SDR SatNOGS station (137 MHz)
    - **Source url:** https://community.libre.space/t/observation-1617402-noaa-18-28654-terrestrial-interference-on-its-frequency/5424
    - **Community:** SatNOGS community (libre.space)
    - **What they built:** NOAA/137 MHz ground station
    - **Problems:**
      - S9-level interference at 137.912 MHz (plus near 137.0) that swamped NOAA-18; traced to the Pi itself
    - **Fixes:**
      - vk2byf: ground the RTL-SDR and metal Pi cases, replace switch-mode supplies with linear ones, add ferrites on leads
      - Others proposed disabling Pi HDMI (also topic 3151) as a mitigation
    - **Outcome:** Noise eliminated for one user. This is directly relevant to Meteor LRPT at 137 MHz with an SBC, display and backlight converter inside a palm-sized case.
  26.
    - **Product:** Particle Tachyon (QCM6490, same SoC family) with third-party DSI panels
    - **Source url:** https://community.particle.io/t/confirmed-working-dsi-display/70237
    - **Community:** Particle community
    - **What they built:** Tachyon with Raspberry Pi Touch Display 2 and Waveshare DSI panels
    - **Problems:**
      - Waveshare 4.3in/5in DSI: detected but blank
      - RPi Touch Display 2: green pulsing pattern, 'dsi PLL unlock error: 0x140'
      - Particle CTO: each DSI panel needs kernel driver enablement, board detection and a DTS loaded by the bootloader
    - **Fixes:**
      - A display overlay from the Ubuntu 24.04 beta image made the RPi panel and touch work (Feb 2026)
      - Bjorn Andersson pointed to WIP LKML Waveshare panel-driver patches for v6.18+ (topic 70037)
    - **Outcome:** Third-party DSI on QCM/QCS6490 is per-panel kernel work even for the vendor. This is a strong warning for a Midas DSI build on the Q6A.
  27.
    - **Product:** Chinese Realtek-based HDMI driver board, DDC/CI brightness control
    - **Source url:** https://github.com/rockowitz/ddcutil/issues/134
    - **Community:** GitHub issues (ddcutil)
    - **What they built:** Surface Pro 3 panel on a generic driver board with a Raspberry Pi
    - **Problems:**
      - The OSD offers DDC/CI, but nothing answers at I2C 0x37 (only the EDID at 0x50), so ddcutil can't set brightness
    - **Fixes:** []
    - **Outcome:** Closed without a fix. Software auto-dimming over DDC on cheap boards is unreliable. Waveshare documents a hardware PWM mod instead (remove a 22 ohm resistor and drive the pad from GPIO PWM: https://www.waveshare.com/wiki/7inch_HDMI_LCD_(H)_(with_case)).
  28.
    - **Product:** Lilliput / Xenarc small HDMI touch monitors on Linux (CNC)
    - **Source url:** https://forum.linuxcnc.org/18-computer/36241-lilliput-monitors-resolution
    - **Community:** LinuxCNC forum
    - **What they built:** CNC control screens
    - **Problems:**
      - Low native resolution panels upscaling 1024x768 looked 'a disaster'
    - **Fixes:**
      - Match the output to the panel's native mode; touch appeared as a USB mouse and worked in Linux Mint with no configuration (rodw)
    - **Outcome:** USB touch on Lilliput-type monitors works driver-free. Always run native resolution (1280x800 for the 719/T).
  29.
    - **Product:** Outdoor Pi touchscreens (10in Chalkboard HDMI; 5-7in options)
    - **Source url:** https://forums.raspberrypi.com/viewtopic.php?t=144176
    - **Community:** Raspberry Pi forums (also t=216464)
    - **What they built:** Outdoor and marine Pi displays
    - **Problems:**
      - A 10in Chalkboard HDMI capacitive screen was 'almost impossible to read in daylight'
      - t=216464 quotes guidance of about 400 nits for shade and 700 nits for direct sun; high-brightness screens drain batteries faster than the Pi
    - **Fixes:**
      - Suggested: commercial sunlight-readable TFTs, e-ink or transflective panels, a 1300-nit 5in MakerPlane HAT
    - **Outcome:** No successful outdoor build was documented. It confirms that sub-500-nit panels fail outdoors.
  30.
    - **Product:** uConsole / DevTerm handhelds used outdoors
    - **Source url:** https://forum.clockworkpi.com/t/higher-res-display/14069
    - **Community:** ClockworkPi forum (also topics 9444, 10051)
    - **What they built:** Handheld Linux terminals (also used for SatDump via DragonOS)
    - **Problems:**
      - The stock IPS is glossy and hard to read in sun
      - A proposed 1200x1920 MIPI swap needs a pinout adapter and a kernel driver (HX8399C)
    - **Fixes:**
      - Collapsible sun shroud / 'HAMVISOR' visor accessories to shade the screen
    - **Outcome:** The resolution upgrade was never completed. Shading hoods are the practical community fix.
  31.
    - **Product:** Outdoor LCD enclosures (solar clearing and heat)
    - **Source url:** https://community.element14.com/challenges-projects/design-challenges/experimenting-with-extreme-environments/b/blog/posts/exploring-hidden-extremes-of-sheltered-environment---extra-blog-4--greenhouse-in-the-box
    - **Community:** element14 community (+ Elo support KB https://elosupport.elotouch.com/hc/en-us/articles/31648421556247)
    - **What they built:** Pi CM4 in a sealed outdoor box
    - **Problems:**
      - Black and transparent-lid enclosures overheat in sun; the CPU throttles at about 80 C
      - Elo: an air gap under touch glass creates a greenhouse effect, and the LCD reaches its clearing point (goes black until it cools)
    - **Fixes:**
      - Light-coloured enclosure, no clear window over hot parts, shading, orientation, solar-rejection film
    - **Outcome:** Recoverable, but repeated clearing shortens LCD life.
- **Common problems:**
  1.
    - **Problem:** Q6A HDMI goes black after kernel or firmware updates: 7.0.x regression, DP AUX interrupt storm, dead hotplug
    - **Affected products:** Radxa Dragon Q6A (all HDMI displays)
    - **Frequency:** common
    - **Known fix:** - Add clk_ignore_unused to /etc/kernel/cmdline, then run kernel-install add (Radxa staff).
  - Or stay on the full 6.18.2 kernel + initramfs + DTB, or move to newer kernels (fixed for one user by Sep 2026) or the community 7.2.9 image.
  - After poweroff, use a long press of the power button.
  - Once the display works, hold the kernel packages (apt-mark hold) so a field update cannot kill the screen (my recommendation).
    - **Fix sources:**
      - https://forum.radxa.com/t/latest-q6a-update-to-linux-7-0-no-hdmi/31288
      - https://forum.radxa.com/t/linux-7-0-hdmi-not-working/31304
      - https://forum.radxa.com/t/ubuntu-26-04-1-lts-images-for-the-radxa-dragon-q6a-now-on-linux-7-2-9-hdmi-works-wi-fi-bt-audio-npu-apt-upgrade-safe/31574
  2.
    - **Problem:** Wrong default mode on small or odd panels: the Q6A defaults to 1080p, so the image garbles or a 4K monitor falls back to 1024x768
    - **Affected products:** Q6A with 1024x600 kits (Waveshare 5DP-CAPLCD, Orient 7in), Samsung G80SD; any panel with a sparse EDID
    - **Frequency:** common
    - **Known fix:** - Check the modes: sudo edid-decode /sys/class/drm/card1-HDMI-A-1/edid.
  - Append video=HDMI-A-1:WxH@60 (add 'e' to force the output on) to /etc/kernel/cmdline, run kernel-install add, then reboot and re-plug HDMI (Radxa FAQ).
    - **Fix sources:**
      - https://docs.radxa.com/en/dragon/q6a/faq
      - https://forum.radxa.com/t/samsung-g80sd-can-not-negotiate-resolution-refresh-rate/31118
  3.
    - **Problem:** Cheap HDMI-to-MIPI bridge boards have portrait-only or minimal EDIDs, tight non-standard timings, and init races (wrong colours or no image until re-plug)
    - **Affected products:** Wisecoco 5.5in/7in/8.9in/2K kits, LT6911-based boards, Waveshare 9in 2.5K
    - **Frequency:** common
    - **Known fix:** - Drive the mode from the EDID under KMS.
  - Otherwise force the exact EDID timing (video= or a custom modeline matching the EDID porches).
  - Workaround for an init race: xrandr --output HDMI-1 --off && xrandr --output HDMI-1 --auto.
  - Fix a bad EDID with drm.edid_firmware=HDMI-A-1:edid/x.bin; Pi users patched a Wisecoco EDID for audio.
  - Swapping to a better board fixed it in one case.
    - **Fix sources:**
      - https://forums.raspberrypi.com/viewtopic.php?t=373978
      - https://forums.raspberrypi.com/viewtopic.php?t=393606
      - https://forums.raspberrypi.com/viewtopic.php?t=366160
      - https://www.waveshare.com/wiki/9inch_2560x1600_Monitor
  4.
    - **Problem:** Modes wider than 2400 px fail or give no output on QCS6490 unless DPU virtual planes are enabled (SSPP max_linewidth = 2400)
    - **Affected products:** Q6A with 2560x1440/2560x1600 landscape displays (Waveshare 9in, Wisecoco 2.5K, Wisecoco 8.4in via a bridge)
    - **Frequency:** occasional
    - **Known fix:** Community: newer Radxa images enable virtual planes.
  
  My own fix, from the kernel source:
  - Use a kernel where dpu_use_virtual_planes defaults to true (current mainline), or add msm.dpu_use_virtual_planes=1 to the cmdline.
  - Alternatively, drive portrait-native panels in their native portrait mode (1200x1920, 1600x2560: width at most 2400) and rotate in the compositor.
    - **Fix sources:**
      - https://forum.radxa.com/t/dragon-q6a-no-video-output/29681
      - https://raw.githubusercontent.com/torvalds/linux/master/drivers/gpu/drm/msm/disp/dpu1/catalog/dpu_7_2_sc7280.h
      - https://raw.githubusercontent.com/torvalds/linux/master/drivers/gpu/drm/msm/disp/dpu1/dpu_kms.c
  5.
    - **Problem:** Touch does nothing in SDR++/SatDump (GLFW apps) under Wayland
    - **Affected products:** Any USB-touch display with SDR++, SDRIAK or SatDump on a GNOME/KDE Wayland session
    - **Frequency:** common
    - **Known fix:** - Run under X11 or XWayland: XDG_SESSION_TYPE=x11 sdrpp (GLFW 3.4 honours this; my fix from the GLFW source), or use an Xorg session or the X11-only libglfw3.
  - XWayland and X11 emulate a pointer from touch.
    - **Fix sources:**
      - https://github.com/AlexandreRouma/SDRPlusPlus/issues/1569
      - https://github.com/AlexandreRouma/SDRPlusPlus/issues/1631
      - https://github.com/glfw/glfw/issues/2791
      - https://raw.githubusercontent.com/glfw/glfw/3.4/src/platform.c
  6.
    - **Problem:** Touch mapped to the wrong output, or it does not follow rotation (portrait-native boards rotated to landscape)
    - **Affected products:** Wisecoco and Waveshare portrait-native kits, any HDMI+USB touch under GNOME/mutter
    - **Frequency:** occasional
    - **Known fix:** - GNOME: gsettings set org.gnome.desktop.peripherals.touchscreen:/org/gnome/desktop/peripherals/touchscreens/<vid>:<pid>/ output "['VEN','Product','Serial']" (from monitors.xml).
  - Under X11: xinput map-to-output, or a libinput calibration-matrix udev rule.
    - **Fix sources:**
      - https://who-t.blogspot.com/2024/03/enforcing-touchscreen-mapping-in-gnome.html
      - https://discourse.gnome.org/t/external-touch-screen-is-mapped-to-wrong-display/26089
  7.
    - **Problem:** Field monitors do not act as a host touchscreen and accept only broadcast video formats, so their 1920x1200 panels show scaled 1080p. They draw about 20 W and run hot
    - **Affected products:** FEELWORLD LUT7/LUT5/F6 PLUSX, Osee T7, Desview, Portkeys, NEEWER, Lilliput H7s
    - **Frequency:** common
    - **Known fix:** - Feed 1080p60.
  - Add a separate input (encoder, buttons, or a small USB touch overlay).
  - Use the built-in light sensor or auto-dimming, a sun hood or cage, and budget 15-20 W.
    - **Fix sources:**
      - https://kounio.gr/katastima/video-2/monitors/feelworld-lut7-7-3d-lut-4k-hdmi-monitor/
      - https://www.adorama.com/felut7.html
      - https://forum.blackmagicdesign.com/viewtopic.php?p=1039971
  8.
    - **Problem:** Undersupplied display boards flicker, fail to start or show abnormal output
    - **Affected products:** Waveshare 5DP-CAPLCD (needs at least 850 mA, 4.2 W typ), Waveshare 9in 2.5K (5 V/2 A), any HDMI kit fed from SBC USB
    - **Frequency:** common
    - **Known fix:** - Power the display from its own rail (5 V/2 A, or a 12 V buck for 2000-nit kits), not from the SBC's USB.
  - Power it before or with the SBC so the EDID is readable at boot.
    - **Fix sources:**
      - https://www.waveshare.com/wiki/5DP-CAPLCD
      - https://www.waveshare.com/wiki/9inch_2560x1600_Monitor
      - https://forum.radxa.com/t/poe-hat-for-radxa-dragon-q6a/29237
  9.
    - **Problem:** RF noise from the SBC, HDMI and display electronics lands in VHF satellite bands
    - **Affected products:** Any SBC + display + RTL-SDR/LimeSDR in one box; 137 MHz is especially exposed
    - **Frequency:** occasional
    - **Known fix:** - Ground the SDR and SBC cases.
  - Use linear or well-filtered supplies and ferrites on leads.
  - Disable or shorten HDMI, and use a shielded HDMI cable with a ferrite.
  - HDMI displays were quieter than an SPI TFT in one Lime report.
    - **Fix sources:**
      - https://community.libre.space/t/observation-1617402-noaa-18-28654-terrestrial-interference-on-its-frequency/5424
      - https://discourse.myriadrf.org/t/80mhz-bandwidth-spectrogram-on-limesdr-mini/3356?page=2
      - https://www.amateurradio.com/rfi-is-either-giving-or-receiving/
  10.
    - **Problem:** DSI panels on the Q6A/QCS6490 stay black: missing overlays and drivers, panel revision mismatch, per-panel kernel work
    - **Affected products:** Radxa Display 8HD/10FHD, any third-party DSI panel including the Midas MDT0700F1IHHC
    - **Frequency:** common
    - **Known fix:** - Official 8HD: match the overlay to the flex revision (AD001 vs AD002).
  - Third-party panels: write your own panel driver and device tree (Tachyon experience); no Q6A J10 pinout has been published on the forum.
    - **Fix sources:**
      - https://forum.radxa.com/t/only-backlight-on-8hd/30822
      - https://forum.radxa.com/t/radxa-display-8-hd-black-screen-on-dragon-q6a/30454
      - https://community.particle.io/t/dsi-display-issue/70037
  11.
    - **Problem:** Displays under about 500 nits are unreadable in daylight; glossy air-gap glass and the greenhouse effect make it worse (solar clearing)
    - **Affected products:** Waveshare 2.5K/AMOLED/FHD 7in, Pi 7in, uConsole and similar
    - **Frequency:** common
    - **Known fix:** - Use at least 1000-2000 nits with optical bonding.
  - Add a sun hood or visor, a light-coloured case and a vented gap behind the backlight; avoid an air gap under the glass.
    - **Fix sources:**
      - https://forums.raspberrypi.com/viewtopic.php?t=144176
      - https://forum.clockworkpi.com/t/higher-res-display/14069
      - https://elosupport.elotouch.com/hc/en-us/articles/31648421556247
  12.
    - **Problem:** Brightness can't be controlled in software (OSD only; DDC/CI does not respond on cheap boards), so there is no auto-dimming
    - **Affected products:** Waveshare HDMI kits, Realtek-scaler and HDMI-to-MIPI boards
    - **Frequency:** occasional
    - **Known fix:** Hardware PWM mod: Waveshare's documented removal of a 22 ohm resistor so a GPIO PWM drives the backlight. Or a DSI-direct panel under the Linux backlight class.
    - **Fix sources:**
      - https://www.waveshare.com/wiki/7inch_HDMI_LCD_(H)_(with_case)
      - https://github.com/rockowitz/ddcutil/issues/134
  13.
    - **Problem:** Polarized sunglasses black out the LCD at some orientations
    - **Affected products:** All LCDs (IPS/LTPS); not AMOLED with circular polarizers to the same degree
    - **Frequency:** occasional
    - **Known fix:** Rotate the screen 90 degrees. Test with your sunglasses before fixing the panel orientation in the case.
    - **Fix sources:**
      - https://www.allaboutvision.com/eyewear/sunglasses/lenses/polarized-lenses-and-lcd-screens/
      - https://www.r3owners.net/threads/fuelbot-enhancement.34043
- **Unresolved problems:**
  1.
    - **Problem:** Nobody has documented a stable above-FHD (2560x1600/1440) HDMI touch panel on the Q6A
    - **Evidence:** - Only two data points exist. Willy Tarreau's implied 2.5K screen worked (Oct 2025).
  - The Samsung G80SD fell back to 1024x768 and the thread is unresolved.
  - An XV272U-class monitor got no signal until 'virtual planes' were enabled.
  - The SC7280 DPU caps SSPP width at 2400 px; the 2-lane DP and RA620 limit is 4K30.
    - **Why it matters for us:** Buying a 2.5K kit is a gamble on mode negotiation, virtual planes, EDID and link training at swing level 2. A portrait-native 1200x1920/1600x2560 mode avoids the 2400-px limit but still needs real testing.
  2.
    - **Problem:** The Wisecoco 7in 1920x1080 2000-2500 nit HDMI kit has no community build or review
    - **Evidence:** - The product page says 'There are no reviews yet'.
  - The spec lists the touch interface as I2C and the brightness inconsistently (2000+ typ vs 2500 in the title).
  - No board chip, input voltage or power figure is given.
  - Searches of the Raspberry Pi forums found only other Wisecoco models. Those show EDID and timing quirks, but also that Wisecoco touch boards enumerate as CH57x USB HID.
    - **Why it matters for us:** It is the recommended part. You must get written confirmation of USB-HID touch, board input voltage, EDID mode list (landscape 1920x1080 vs portrait) and lamination before paying, and expect to force the mode with video= or an EDID override.
  3.
    - **Problem:** No community experience exists for the Midas MDT0700F1IHHC 2500-nit 1200x1920 DSI panel, and none for any third-party DSI panel on the Q6A
    - **Evidence:** - No Midas threads were found on the Pi forums.
  - The Q6A J10 pinout question went unanswered (Aug 2026).
  - The official 8HD fails on Ubuntu images.
  - Mainline Q6A patches disable DSI as 'not present'.
  - The FT7250 touch controller has no confirmed mainline driver.
  - Tachyon (QCM6490) shows that each panel needs kernel driver and DT work, plus a DSI PLL unlock error.
    - **Why it matters for us:** The above-FHD 'upgrade path' is an unbounded kernel-bring-up project. Treat it as experimental and do not plan the enclosure around it.
  4.
    - **Problem:** Recurring Q6A kernel regressions in the display path have no root-cause fix from Radxa
    - **Evidence:** - 7.0.x broke HDMI for several users.
  - Radxa offered only the clk_ignore_unused workaround.
  - A 'latest kernel updates' fix arrived for one user without a version.
  - A community image relies on unlisted Armbian DP/DPU patches.
    - **Why it matters for us:** A field device whose screen dies after apt upgrade is bricked for practical purposes. You need a kernel hold, a serial console and a known-good image backup.
  5.
    - **Problem:** Software brightness control over HDMI (DDC/CI through the msm DP to RA620 path) is undocumented
    - **Evidence:** - No Q6A or RA620 DDC/CI report was found.
  - Cheap Realtek boards claim DDC/CI but do not answer at 0x37 (ddcutil #134).
  - The Waveshare boards documented here dim via OSD only.
    - **Why it matters for us:** Auto-dimming from a lux sensor is the main battery saver (about 3-5 W at 2000 nits). Without DDC you need a PWM hardware mod on the driver board or a DSI-direct panel.
  6.
    - **Problem:** No measurements exist of RF emissions from a 2000-nit backlight boost converter or HDMI-to-MIPI board next to 137/435 MHz and 1.7 GHz receivers
    - **Evidence:** The only community data are general: a Pi at 137.912 MHz (SatNOGS), an SPI TFT noisier than HDMI (Lime), and HDMI cables as an RF path. Nothing was found about bright LED drivers.
    - **Why it matters for us:** In a palm-sized case the LED boost (16-19 V at 0.4-0.5 A, PWM-dimmed) sits a few cm from the LNAs. Plan shielding, LC filtering of the display rail, and an A/B noise test with the backlight at full and at minimum.
  7.
    - **Problem:** Heat and solar clearing behaviour of a 6-8 W, 2000-nit panel inside a closed 3D-printed handheld in summer sun is unknown
    - **Evidence:** - Field-monitor users report 'very warm' units and very hot 3000-nit monitors in sun.
  - Elo and element14 document the greenhouse effect and clearing.
  - No handheld-scale data exist.
    - **Why it matters for us:** In Ukrainian summer sun, PLA/PETG cases soften around 55-60 C, and the LCD may black out. Use ASA/PETG, a light colour, a vented gap behind the backlight, and a hood.
  8.
    - **Problem:** Native Wayland touch support for GLFW apps (SDR++, SatDump)
    - **Evidence:** GLFW issue #42 has been open since 2013; #2791 was closed as a support query; the SDR++ maintainer refuses an app-side fix.
    - **Why it matters for us:** The UI must run under X11 or XWayland, which may break if future Ubuntu images drop the Xorg session. The XWayland env-var trick remains, but needs verification on the Q6A image.
- **Communities checked:**
  - Radxa forum (forum.radxa.com): reached via Discourse search JSON; about 15 Q6A display/HDMI threads read
  - Raspberry Pi forums (forums.raspberrypi.com): reached; Wisecoco, HDMI-to-MIPI, sunlight-readable, Lilliput and Midas searches
  - GitHub issues/releases: SDR++ (#1569, #1631), SatDump (touch search), GLFW (#2791, platform.c), ddcutil (#134), SDRIAK releases; read via web pages because the gh API is restricted to the session's repos
  - Linux kernel source (torvalds/linux msm DPU catalog and dpu_kms.c) and the drm mailing-list mirror (lore.gitlab.freedesktop.org drm-ai-reviews)
  - MyriadRF / Lime discourse (discourse.myriadrf.org): reached
  - SatNOGS community (community.libre.space): reached
  - ClockworkPi forum (uConsole/DevTerm): reached
  - Particle community (Tachyon, QCM6490): reached
  - Armbian forum (Q6A subforum): reached, but no HDMI/display threads beyond audio and gaming
  - GNOME Discourse + Peter Hutterer's blog: reached
  - Core Electronics forum: reached
  - LinuxCNC forum: reached
  - element14 community: reached
  - Waveshare wiki FAQs (9in 2.5K, 5DP-CAPLCD, 7in HDMI LCD H): reached
  - Radxa docs (FAQ, HDMI page): reached
  - Adorama reviews: reached; retailer spec pages (kounio.gr, wisecocodisplay.com): reached
  - Reddit (r/cyberDeck, r/RTLSDR etc.): NOT reachable (blocked for both WebFetch and WebSearch)
  - Sudomod forum: NOT reachable (HTTP 503)
  - BATC forum: NOT reachable (HTTP 503)
  - EEVblog forum: search not fetchable; site-filtered web search returned no EEVblog hits
  - freedesktop GitLab (drm/msm issue #86) and Arch Wiki: NOT reachable (Anubis bot wall)
  - Blackmagic Design forum, B&H reviews, eBay: NOT reachable (HTTP 403); one Blackmagic post seen only as a search snippet
  - Hackaday.io: login wall; AliExpress: login required
- **Recommendation impact:** 1. Brightness-first holds. No community report changes the core pick: a roughly 7in 1920x1080 panel at 2000 nits or more on HDMI with USB touch. But the Wisecoco kit has zero community reports or reviews, so it stays "recommended but unvalidated."
  - Before buying, demand: a USB-HID touch board (Wisecoco touch boards seen on the Pi forums enumerate as CH57x USB HID), the board's input voltage, an EDID dump (landscape vs portrait) and a lamination photo.
  - Budget time for video= or EDID-override work. HDMI-to-MIPI boards commonly need it.
  
  2. Field monitors are downgraded further. Their HDMI inputs accept only broadcast formats (1080p60 maximum below 4K30), so the LUT7's 1920x1200 panel would show scaled 1080p from the Q6A. They also draw about 20 W (the LUT5 empties about 49 Wh in about 2.5 h) and run hot, with no host touch. Use them only as a stopgap with a separate input device.
  
  3. Going above FHD now has a concrete technical gate on the QCS6490: the DPU's SSPP line width is limited to 2400 px.
  - Any landscape 2560-wide mode needs DPU virtual planes: a recent kernel, or msm.dpu_use_virtual_planes=1.
  - It also needs the swing-level-2 link training patch and a cooperative EDID.
  - If you do go above FHD, prefer a portrait-native panel (1200x1920 or 1600x2560) driven natively and rotated in the compositor.
  - Keep the Midas DSI route experimental only. Radxa's own DSI panels fail, third-party DSI on QCM6490 is per-panel kernel work, and no J10 pinout has been answered.
  
  4. Software plan changes:
  - Run SDR++/SDRIAK/SatDump under X11 or XWayland (XDG_SESSION_TYPE=x11). Under native Wayland, touch is dead because GLFW lacks wl_touch.
  - Map the touchscreen with Hutterer's gsettings method.
  - Hold the kernel and keep clk_ignore_unused once HDMI works. Keep a 1.8 V UART cable and an image backup, because Q6A kernel updates have repeatedly killed HDMI.
  
  5. Power and RF budgets:
  - The budget Waveshare 5DP-CAPLCD draws 4.2 W typical and needs at least 850 mA, not the 2-3 W estimated earlier. Give every display its own supply rail.
  - Add RF hygiene from day one: a short shielded HDMI cable with a ferrite, LC filtering on the display and backlight rail, grounded metal shielding around the SBC and display board, and an A/B noise test at 137 MHz with the backlight at maximum and minimum. Community evidence shows SBC and display noise right at 137 MHz.
  
  6. Mechanical: build in a sun hood or visor, a light-coloured ASA/PETG case and a vented gap behind the backlight, and test the polarizer orientation with sunglasses. These are the community-proven fixes for outdoor readability and solar clearing.

## Власні виправлення (`fixes`)

_Агент цього етапу ще працює (run `wf_0e70c405-a03`)._

