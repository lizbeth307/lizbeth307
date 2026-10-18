# Wisecoco 7in 1920x1080 2000 nit hdmi kit: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_071e1025-145`_

- **Part:** Display: Wisecoco SKU 4681, 7in (6.97in) 1920x1080 LTPS IPS "2000+ nit" panel with HDMI-in board and capacitive touch (gated on written D5 answers). Tier core, group Display, qty 1.
- **Current pick:** Wisecoco SKU 4681, 7in 1920x1080 2000+ nit kit with HDMI-in board (wisecocodisplay.com, direct). It stays gated on the written D5 answers and the 30-day acceptance tests.
- **Current price usd:** 132.00 (list 135.00). I re-read it on 18 Oct 2026 from the page's schema.org data: sku 4681, price 132.00 USD, availability InStock, dateModified 2026-09-17, 0 reviews. The price excludes shipping, which the page does not show, and EU import VAT. At 19-21% VAT that is about 157-160 USD before shipping (calculation).
- **Decision:** keep
- **Chosen:** Keep the Wisecoco SKU 4681. No candidate is both cheaper and proven not-worse. The 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000 stays only as the documented fallback (if the D5 gate or acceptance fails). It is a declared downgrade, not a not-worse analog.
- **Chosen price usd:** 132.00, ex shipping and ex EU import VAT. Unchanged.
- **Saving usd:** 0.00
- **Equivalence proof:** There is no replacement, so there is nothing to prove equivalent. To beat the current part, a candidate must be equal or better on every point below:
  1. At least 1800 cd/m2 measured on full white.
  2. Native 1920x1080 landscape, about 7in (315 PPI).
  3. Optically bonded cover glass, with an AR film possible.
  4. Contrast at least 1000:1. IPS viewing angle 85/85/85/85.
  5. HDMI input that accepts the field EDID (DTD1 151.50 MHz at 2200x1148, DTD2 127.90 MHz at 2200x1125, at least 24 lines of vertical blanking).
  6. USB-HID touch that enumerates with VBUS open, in 20/20 cold boots. No 2.4 GHz emission.
  7. 12 V barrel power, stable at 11.0 V, at most 14 W at 100% and at most 7.5 W at 50%.
  8. A dimming path the software can drive.
  9. -20..70 C operating, -30..80 C storage.
  10. Outline about 164x98 mm or smaller.
  11. A legal EU sale with buyer protection.
  
  I checked each candidate against these. Only five are cheaper than 132, and none survives:
  - SURENOO SUR12001080H070K: about 106, unverified. Fails on evidence: the page is captcha-walled and there is no datasheet, so every point above is unknown. Even the resolution is ambiguous ('1200*1080').
  - Newhaven NHD-7.0-HDMI-HR-RSXP-CTU: 120.20, re-fetched today. Documented worse: 940 nits and 1024x600. Bonding is not stated. It needs a 5.0 V rail.
  - 4D 4DHDMI-70-1280-800-CT-EAR-1000: 128.95. Documented worse: 1000 cd/m2, 1280x800, 800:1.
  - Wisecoco's own cheaper SKUs (75-130): 500-1200 nits, and MIPI or LVDS without an HDMI board.
  
  Every other candidate costs more: the Kimmybow (168.50, re-fetched today), VSDISPLAY, the Wisecoco eBay channel, the Lincoln LCDK132, the Feelworld LUT7 class and the DIY route.
  
  The current part's own claims are still unproven: 2000+ nits rests only on a vendor lux photo, which implies at least about 770 cd/m2 (model), and bonding is unconfirmed. That is why the D5 gate and the acceptance tests stay load-bearing. It is not a reason to swap to an equally unproven part.
- **Rejected:**
  1.
    - **Name:** SURENOO SUR12001080H070K '2000nit Incell Touch CTP 7in 1200*1080 FHD HDMI' (AliExpress 1005006176909405 / US 3256805990594653)
    - **Why:** About 106 USD comes only from an old search snippet. I re-tried today with WebFetch and curl: aliexpress.com returns a 1 KB 'punish/captcha' page and aliexpress.us loops through login redirects. So the price, shipping and EU VAT cannot be verified. There is no datasheet, and 'Surenoo' search pages return 403. Each of these could be worse and none can be checked: resolution (1200x1080 is not a real panel mode, so it may be 1080x1920 portrait or 1200x1920), in-cell TDDI touch with no documented USB-HID bridge, bonding and AR, 12 V current, EDID or timing acceptance (an LT6911-class pass-through bridge would void the field-EDID plan), temperature range, and 2.4 GHz behaviour. It fails the not-worse proof. The landed saving (about 26 USD list, VAT applies to both) does not justify the bring-up risk.
  2.
    - **Name:** Newhaven NHD-7.0-HDMI-HR-RSXP-CTU
    - **Why:** Re-fetched today: 120.20 USD incl. tax, 'IN STOCK' with a low-stock notice. Worse in brightness (940 vs at least 1800 nits) and resolution (1024x600, about 169.5 PPI, vs 1920x1080). Bonding is not stated and contrast is not listed. It needs 5.0 V instead of DISP12 12 V. It is better only in naming its parts (FT5426G USB-HID touch, TFP401A receiver).
  3.
    - **Name:** 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000 (fallback)
    - **Why:** 128.95 at DigiKey, 3.05 cheaper. I read datasheet Rev 1.5 myself: 1000 cd/m2 (adjustable via OSD), 1280x800, 800:1, optically bonded, no AR as standard. Worse in nits (about half), PPI (216 vs 315) and contrast. It also corrects one claim in the search results: the whole 4DHDMI line tops out at 1100 cd/m2, on the 15.6in 4DHDMI-156-1920-1080-*-1100, not 1000. No 7in model is above 1000. It stays the fallback only.
  4.
    - **Name:** Wisecoco cheaper SKUs (7in 1200x1920 500-nit MIPI $75; 7in 1920x1200 MIPI $115; 5.5in FHD 1200-nit MIPI $119; 7in 1280x768 1200-nit LVDS $130)
    - **Why:** 500-1200 nits against at least 1800. Three of the four have no HDMI board, and the Q6A DSI supports only Radxa panels. Touch is not stated. The 500-nit parts are rated only -10..60 C. The others are smaller or lower resolution. A site search today ('2000 nits') returned only SKU 4681 as the 7in FHD HDMI kit (plus an 8.4in 1600x2560 MIPI panel at $158 with no board).
  5.
    - **Name:** Kimmybow 'Sunlight Readable Display 7 Inch Touch LCD Monitor, 2000 Nits' (Amazon US B0H7BQDZR9)
    - **Why:** Not cheaper. The page fetched today shows 168.50 USD, ships from Amazon, sold by Kimmybow, 30-day returns; the search had marked the price unknown. The listing names no input (no HDMI or USB anywhere on the page), no touch technology or host path, no supply voltage, no contrast and no bonding. Its 'Glossy' surface gives no AR evidence, and 'wide temperature' comes with no numbers. Its 6.46x3.86 in (164.1x98.0 mm) size suggests the same glass as the Wisecoco (inference), but it adds nothing verified. US-only listing.
  6.
    - **Name:** Wisecoco eBay channel (176657492046, 176594983531, 405247794619)
    - **Why:** More expensive: about 177.64 USD, or about EUR 180-188, plus 30-80 shipping. These are search snippets only, because eBay returns 403. Whether the board revision matches SKU 4681 is unverified.
  7.
    - **Name:** VSDISPLAY 6.97in 1080x1920 2000-nit + 'HD board' (eBay 256679793470)
    - **Why:** Not cheaper: GBP 119 is about 150-160 USD (unverified snippet, page 403). It is portrait-native MIPI, so it needs rotation and an EDID rework. HDMI input and USB-HID touch are unconfirmed, and there is no datasheet.
  8.
    - **Name:** AliExpress 1005005946591911 '7in 2000 nits FHD with touch controller board'
    - **Why:** No verified data at all: the page returns a captcha (re-tried today with curl) and the only description is a third-party wiki article. The price is unknown.
  9.
    - **Name:** DIY: bare 2000-nit in-cell MIPI panel + VIEWE UEDX6911 LT6911 board + own touch bridge + own CC LED driver
    - **Why:** Not cheaper (at least about 180, model). The LT6911 is a pass-through bridge, so the 151.50/127.90 MHz field DTDs are not guaranteed. The touch-to-USB-HID path needs new firmware. Worse in build quality and reliability.
  10.
    - **Name:** Lincoln Technology Solutions LCD132 / LCDK132 kit
    - **Why:** The only one with real datasheet numbers: 2000 cd/m2 minimum, AR lens, USB-HID, 10.6 W. But the panel alone is about 420 (unverified snippet; RS no longer stocks it). The kit is also worse here: rated -10..50 C operating, and its 11.4-12.6 V supply window fails the 11.0 V brown-out test. Portrait-native, with a 162.56 MHz stock EDID.
  11.
    - **Name:** Feelworld LUT7 / LUT7S / LUT7 Pro class (new or used)
    - **Why:** More expensive (about EUR 318 new, about 312 used). Its touch drives only the monitor's own menus, so no USB-HID reaches the host, which is a hard requirement. Brightness is a maker claim only.
  12.
    - **Name:** Lilliput HT7S, Xenarc 702GSH/702CSH, Faytech, Lilliput 819H/T, Litemax
    - **Why:** From the search results; I did not re-check them (WebSearch budget exhausted). Either more expensive (359-530 USD, or quote only) at 1000-1600 nits, or, for the HT7S, a camera monitor with no USB-HID touch to the host.
- **Confidence:** high
- **Conditions or tests:** No replacement condition applies. The Wisecoco itself stays bound by the existing gates:
  - D5 written answers before paying by PayPal: USB-HID VID:PID with VBUS open; bonding, AR and lens thickness; scaler or bridge part and clocks; EDID dump and acceptance of 151.50/127.90 MHz; backlight driver, frequency and dimming method; audio amplifier; polariser axis; 12 V current at 25/50/100%; package contents.
  - Acceptance within 30 days: at least 1800 cd/m2 on full white with a luminance meter; at most 14 W at 100% and at most 7.5 W at 50% at 11.0 V; touch in 20/20 cold boots; the BLE-silence test over 2400-2483.5 MHz; a working dimming path (DDC/CI, then KEY emulation, then own CC driver).
  - No clear answer in about 7 days, or a failed acceptance test: switch to the 4D 4DHDMI-70-1280-800-CT-EAR-1000 ($128.95 DigiKey). This is an explicit, logged downgrade in nits, PPI and contrast, not a silent one.
  
  SURENOO SUR12001080H070K could be re-opened only if all of the following hold:
  - The seller gives written proof of: native 1920x1080 landscape; at least 1800 cd/m2 (datasheet minimum or a measurement); optical bonding; USB-HID touch with VID:PID; a board that accepts the field EDID timings; 12 V input and power at 25/50/100%; -20..70 C.
  - Its landed EU price (list plus shipping plus VAT) is verifiably below the Wisecoco's landed price.
  - It then passes the same bench tests.
  
  Decide before the case CAD freeze.
- **Stack changes:** None to the build: rails (DISP12 to the barrel, eFuse 1.5 A), HDMI A-A cable and ferrite, touch D+/D-/GND to FE1.1s P2, field EDID, kanshi profiles and case are all unchanged.
  
  Data corrections for stack v2 and the P6 re-verify:
  1. Wisecoco SKU 4681 re-verified on 18 Oct 2026 from the schema: 132.00 / 135.00 USD, InStock, dateModified 2026-09-17, 0 reviews. The page still lists no shipping, VAT, warranty, bonding or AR.
  2. 4DHDMI datasheet Rev 1.5: the line maximum is 1100 cd/m2 (15.6in 4DHDMI-156-1920-1080-*-1100). The 7in maximum is 1000 cd/m2. Replace the line "the whole 4DHDMI line tops out at 1000".
  3. The Kimmybow B0H7BQDZR9 price is 168.50 USD on Amazon US, no longer 'unknown'. Rejected, not cheaper.
  4. Newhaven NHD-7.0-HDMI-HR-RSXP-CTU re-confirmed at 120.20 incl. tax, 940 nits, 5.0 V, low stock.
  
  Scratch data: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p5disp_v/4d/ds.txt (4D R1.5 text) and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p5disp_v/dl/amz.txt (Kimmybow page text).
  
  Method limit: the shared WebSearch budget was exhausted, so I did 0 searches and used only WebFetch and curl on primary pages. Market discovery beyond the two input searches was not extended.
- **Sources:**
  - https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
  - https://www.wisecocodisplay.com/?s=2000+nits&post_type=product
  - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_5.pdf
  - https://www.digikey.com/en/products/result?keywords=4DHDMI-70-1280-800-CT-EAR-1000
  - https://www.newhavendisplay.com/nhd70hdmihrrsxpctu-p-9649.html
  - https://www.amazon.com/dp/B0H7BQDZR9
  - https://www.aliexpress.com/item/1005006176909405.html
  - https://www.aliexpress.us/item/3256805990594653.html
  - https://www.aliexpress.com/item/1005005946591911.html
  - https://www.ebay.de/itm/176594983531
  - https://www.ebay.de/itm/256679793470
  - https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/4228/LCDK132CTL1ARH01.pdf
  - https://www.syntex.tv/feelworld-lut7-pro
  - https://forums.raspberrypi.com/viewtopic.php?t=368455

