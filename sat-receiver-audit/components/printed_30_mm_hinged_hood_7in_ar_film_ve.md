# Printed 30 mm hinged hood 7in ar film ve: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_071e1025-145`_

- **Part:** Display sun kit (1 set): printed 30 mm hinged hood + 7in AR film + VEML7700 lux breakout (core, Display group). STACK.md line 232.
- **Current pick:** Printed 30 mm hinged ASA hood + unspecified 7in clear AR film (target class about 0.7% vendor claim, no SKU in STACK) + Adafruit 4162 VEML7700 STEMMA QT breakout, mounted outside the hood on the outer top face of the bezel.
- **Current price usd:** 15-25 (STACK estimate; the film has no SKU). A realistic price is about $23-26 plus film shipping and EU import VAT:
  - hood: about EUR 1.7 of the case's ASA (50 g at EUR 34.50/kg incl. VAT);
  - VEML7700 4162: $4.95, plus a $0.95 cable;
  - film: GBP 11.11 ex VAT if it is the Diamox sheet.
- **Decision:** keep
- **Chosen:** Keep the set. No candidate is both cheaper and proven not worse.
  
  (1) Hood: keep the printed 30 mm hinged hood. Print it from the case's existing light-grey ASA spool (STACK line 274), not from a new black spool, and make the interior matte black with paint or flock.
  
  (2) Sensor: keep the Adafruit 4162 VEML7700. The 5378 right-angle version is an equal choice at the same price if the window geometry needs side-looking. Buy it in the DigiKey order the stack already places.
  
  (3) AR film: the line has no SKU yet, so there is nothing to replace. Use Diamond Coatings Diamox AR1617 as the provisional SKU (250x250 mm sheet, which gives 2 pieces). Its 0.74% luminous reflectance against the 0.7% target must be stated in the BOM, not hidden. Accept it only after the bench tests below.
- **Chosen price usd:** Realistic set price is about $23-26 plus film shipping and EU import VAT, which pushes it above the 15-25 estimate:
  - hood: about $2 of filament, plus paint or flock (price not verified);
  - VEML7700 4162: $4.95 at Adafruit, or EUR 4.35 ex VAT / EUR 5.18 incl. VAT at DigiKey DE, plus a $0.95 cable;
  - Diamox AR1617: GBP 11.11 ex VAT, about $14.8; UK-to-EU shipping, import VAT and handling are not stated by the seller.
- **Saving usd:** 0. The only possible saving is a DIY VEML7700-TT tab, at about $1-3. It is real only if the tab rides free in the existing custom-PCB order (STACK line 257) and is reflowed properly; neither is shown. On its own order the tab costs about $5-8, which is more than the Adafruit board.
- **Equivalence proof:** The current parts are kept, so this records why each challenger fails (everything below was checked on 18 Oct 2026).
  
  VEML7700 die, Vishay datasheet Rev 1.8, 28-Nov-2024 (PDF text extracted):
  - 0 to 140,000 lx max at gain 1/8, IT 25 ms;
  - 0.0042 lx/step at gain x2, IT 800 ms;
  - fixed 7-bit address 0x10;
  - VDD 2.5-3.6 V; operating and storage -25 to +85 C; pull-ups 2.2-4.7 k suggested;
  - MSL 4 with 72 h floor life;
  - VEML7700-TT is top view and VEML7700-TR is side view.
  
  Adafruit 4162:
  - $4.95, in stock; DigiKey DE EUR 4.35 ex VAT, 209 in stock, Active; Botland EUR 6.98 gross / 5.87 net, in stock;
  - 3-5 V regulator, 4.7 k pull-ups since Dec 2019, two STEMMA QT connectors;
  - a green 'on' LED on the front, which a jumper on the back can cut.
  
  Adafruit 5378: same $4.95 (28 in stock) and the same Botland price. It senses parallel to the PCB. The page states neither the regulator nor the pull-ups.
  
  Bare VEML7700-TT:
  - DigiKey $1.53 at qty 1 / $1.282 at qty 10, Active, 6,254 in stock, no NRND note;
  - LCSC $1.20, 2,764 in stock, but the page shows no lifecycle status and no authorised-distributor statement. The NRND flag one search reported is not confirmed, and Vishay's page shows no NRND notice.
  
  Diamox AR1617 (datasheet v2.1, PDF text extracted):
  - luminous reflectance 0.74% (absolute, 5 deg), minimum 0.59% at 588 nm;
  - transmission 94.4% and haze 0.1%, both measured on 1 mm float glass;
  - 100 um PET + 20 um OCA;
  - 2-3H at 750 g; steel wool grade A at 200 g/cm2; water contact angle 103 deg;
  - -30 to +60 C x50 cycles and 60 C / 90% RH for 500 h, both unchanged; the heat test is printed as '103Deg 500 h' (ambiguous);
  - peel 8.0 N/25 mm, no residue; cleanable with IPA;
  - 'not done by an independent laboratory';
  - wet application. There is no retardation or birefringence spec for the PET, and the UK page does not publish shipping or EU terms.
  
  Sun contrast model (my calculation; 1000:1 panel, E/pi = 31,831 cd/m2 at 100 klx): 1.24% total reflectance against 1.2% gives 6.0:1 vs 6.2:1 at 2000 nit, 3.5:1 vs 3.6:1 at 1000 nit, and about 13.5:1 vs 13.9:1 under the hood at 20 klx.
  
  ASA hood material: 123-3D gives 96 C heat resistance for PolyLite ASA (retailer figure, not a TDS), against 65 C glass and the 80 C storage case.
  
  Sanwa free-cut range (Sanwa page): LCD-70KFP and 70WBCF are glossy with no AR. LCD-101/125WABVNGF are matte, with no reflectance figure.
- **Rejected:**
  1.
    - **Name:** Adafruit 5378 Right Angle VEML7700 (STEMMA QT)
    - **Why:** Not cheaper. It is $4.95 at Adafruit and EUR 6.98 at Botland, the same as the 4162. The Berrybase EUR 4.90 price was not deliverable and I did not re-check it. The sensor spec is equal (same die). It is an alternative to pick by window geometry, not a saving. Its regulator and pull-ups are not stated.
  2.
    - **Name:** DIY tab: Vishay VEML7700-TT + 0.1 uF + pull-ups + 100 ohm/TVS on our own PCB
    - **Why:** The chip spec is equal (Rev 1.8), but the saving is not proven real. Chip $1.53 at DigiKey; the PCB adds about $0-2, plus a connector or soldered leads, for a net saving of about $1-3. That holds only if the tab rides free in the existing power/injector PCB order (STACK line 257); multi-design fees were not verified. On its own order it costs about $5-8, which is more. Build quality matches the factory-assembled Adafruit board only with stencil or hotplate reflow and MSL-4 handling (72 h floor life). Hand soldering risks flux on the optical window. LCSC ($1.20) shows no lifecycle status and no Vishay-authorised status, so buy from DigiKey, Mouser, TME or Farnell only.
  3.
    - **Name:** Generic AliExpress VEML7700 module ('120k lux, 3.3/5 V')
    - **Why:** The $1.09 is a discount over struck-through prices of $2.98 and up, with no store named. I found no independent measurement and no proof the die is genuine. Pull-ups and LDO are undocumented. The real saving is about $1-3 or less after shipping. The 0x07 ID check (0xC481) cannot detect a recycled or remarked die. Rejected.
  4.
    - **Name:** DFRobot SEN0228 Gravity VEML7700
    - **Why:** No saving: Botland EUR 6.98 gross, the same as the 4162 (verified); DigiKey and RobotShop are higher or out of stock. Its PH2.0 connector forces a cable change. Rejected.
  5.
    - **Name:** SparkFun SEN-15436 VEML6030 (Qwiic)
    - **Why:** More expensive ($5.95), and the default address 0x48 needs a jumper. I did not check its range against the VEML7700's 140 klx. Rejected on price.
  6.
    - **Name:** ams TSL2591, TI OPT3001, ROHM BH1750, Maxim MAX44009 breakouts
    - **Why:** Figures are from datasheet memory and were not re-verified this round. TSL2591 tops out at about 88 klx, OPT3001 at about 83 klx and BH1750 at 65.5 klx by default, so all saturate below the 120-140 klx of direct sun. MAX44009 reaches 188 klx, but its 0.045 lx resolution is 10x coarser than 0.0042. All need new drivers. Worse on range or resolution.
  7.
    - **Name:** Diamox AR1617 PET AR film (as a cheaper analog)
    - **Why:** It is not cheaper. The line had no SKU; it costs GBP 11.11 ex VAT (about $14.8), plus UK-to-EU shipping and import VAT that are not stated. On paper it is 0.04 pp worse than the 0.7% target (0.74% luminous). The PET has no birefringence spec, and the tests are the maker's own. It is NOT rejected as the fill for the empty film line: it is the only datasheet-backed 7in-capable clear AR film found, and is recommended provisionally with that gap disclosed (see conditions).
  8.
    - **Name:** ELECOM AVA-PA10FLG low-reflection iPad film (to be cut)
    - **Why:** Claims 0.77% (vendor claim from a search snippet), which is worse than 0.7% and than Diamox's 0.74%. The price is unknown (page returned 403). Cutting may damage the edge. Rejected.
  9.
    - **Name:** Sanwa CAR-F52P car-nav AR film
    - **Why:** 1.1% reflectance (Sanwa manual), so about 1.6% in total and about 4.9:1 at 2000 nit and 100 klx. Size and price not verified. Worse.
  10.
    - **Name:** ELECOM CAR-FL7W 7in-wide car-nav AR film
    - **Why:** 153.5x79.5 mm is smaller than the 154.4x86.8 mm active area, so it cannot cover the image. No reflectance figure. Not compatible.
  11.
    - **Name:** Sanwa LCD-101WABVNGF / LCD-125WABVNGF free-cut 'anti-reflection'
    - **Why:** The Sanwa page confirms they are matte (AG) with no reflectance figure; JPY 4,950 / 5,280. Matte AG raises haze and blurs a 316 PPI image. Worse and not cheaper.
  12.
    - **Name:** Sanwa LCD-70KFP / LCD-70WBCF free-cut 7in glossy
    - **Why:** Glossy anti-fingerprint and blue-cut films with no AR coating (Sanwa page), so about 4% surface reflectance against about 0.7%, which cuts sun contrast to about 2.4:1 at 2000 nit. JPY 2,728 / 2,948 plus shipping from Japan. Worse.
  13.
    - **Name:** SmallHD Ultra Matte, upscreen Reflection Shield, BROTECT matte films
    - **Why:** Matte AG with no reflectance or haze data: diffuse scatter, a softer image, and reflectance about at glass level. SmallHD is $39.99. Worse.
  14.
    - **Name:** Accsoon ACC37 AR+AF tempered glass (7in monitor)
    - **Why:** Not cheaper ($18.90). It cannot be cut, the outline is made for the Accsoon M7 and is unlikely to match the accepted panel glass, the thicker glass layer is a risk for capacitive touch, and the '<=0.5' reflectance has no unit. Rejected.
  15.
    - **Name:** Hood printed from a new black ASA spool (variant in search A)
    - **Why:** It costs more, because it needs a new EUR 34.50 spool for about 50 g when the case's light-grey ASA spool is already budgeted. A black exterior also breaks the light-exterior spec: more solar heating next to glass limited to 65 C. Use the light-grey ASA with a matte-black interior.
  16.
    - **Name:** Commercial fabric or velcro 7in monitor sunhoods
    - **Why:** They do not fold flat as a protective lid, do not fit the case, and none costs less than about $2 of filament. Rejected.
  17.
    - **Name:** Budget 'hood only' (no AR film, no sensor)
    - **Why:** Worse: bonded glass without AR is about 4.5% reflectance, so about 1.7:1 at 1000 nit against 3.6:1 with AR. It also loses auto-brightness, the Day/Night/Red themes and the L = E/pi check. Not an analog.
- **Confidence:** medium
- **Conditions or tests:** AR film (Diamox AR1617, provisional):
  (a) Polarised sunglasses at 0/45/90 deg in landscape, with no rainbow mura. Its 100 um PET has no retardation spec; if mura shows, the film fails for sunglass users, so record it and keep looking.
  (b) Specular A/B: a torch at about 15 deg, the VEML7700 at the mirror angle, bare bonded glass against filmed glass. A ratio of about 0.2 or less is consistent with about 0.7-0.9% (method, not evidence).
  (c) Touch through the film, bare-handed and gloved, after the 24-48 h wet-application dry-out.
  (d) The existing 45 min noon-sun run with the hood: no lifting, bubbles, haze or yellowing, and glass at or below 65 C.
  (e) Check haze at 316 PPI by eye.
  
  VEML7700 4162:
  - Cut the 'on' LED jumper on the back before fitting. The green LED sits beside the sensor behind the bezel window, would leak into low-light readings and would glow in Night/Red mode. Check the 5378 for the same LED.
  - Read the 0x07 ID register; expect 0xC481.
  - Direct-sun reading at gain 1/8 and IT 25 ms must be below full scale.
  - Total SDA/SCL pull-up, from the 4.7 k on the 4162 in parallel with the PCA9555 board's own, must stay within the datasheet's 2.2-4.7 k class. Remove one set if it is lower.
  
  DIY tab, only if adopted later:
  - the chip comes from an authorised distributor;
  - the tab goes into the existing PCB order at no extra design fee;
  - stencil or hotplate reflow within the MSL-4 72 h floor life (or bake first);
  - the same ID and lux checks against a 4162 reference.
  
  Hood: CAD only after the panel passes acceptance. Light-grey ASA with a matte-black interior, nothing conductive. Hinge cycle check.
- **Stack changes:** STACK line 232 (sun kit):
  (1) Name the film SKU: 'Diamox AR1617, 250x250 mm sheet (2 pieces), GBP 11.11 ex VAT plus UK-to-EU shipping and import VAT; maker data 0.74% luminous reflectance against the 0.7% target, so the model gives about 6.0:1 instead of 6.2:1 at 2000 nit and 100 klx and 3.5:1 instead of 3.6:1 at 1000 nit (disclosed); wet application; passes only after the sunglasses and touch tests'. Keep searching for a datasheet-backed film at 0.7% or less and low birefringence (TAC or super-retarder PET); this round's shared WebSearch budget ran out before that search.
  (2) Raise the set price to about $23-26 plus film shipping and VAT. The 15-25 estimate is too low once the film is real.
  (3) Hood: print from the case's light-grey ASA (STACK line 274), not a separate black spool; matte-black paint or flock inside (cost not verified).
  (4) VEML7700: buy the 4162 in the existing DigiKey order (EUR 4.35 ex VAT, 209 in stock) to avoid extra shipping. Add 'cut the on-LED jumper' to the assembly steps, and add the 0x07 = 0xC481 check and the pull-up total check to bring-up.
  
  No change to power rails (3.3 V from the Pico), connectors (JST-SH / STEMMA QT), drivers (own RP2040 driver; nothing on Ubuntu 24.04 arm64), the I2C map (0x10 and 0x20) or the case outline. The film and hood are passive and non-conductive, with no RF effect. Every hard rule holds: receive-only, no loops, conducted-only sources.
- **Sources:**
  - https://www.vishay.com/docs/84286/veml7700.pdf
  - https://www.vishay.com/en/product/84286/
  - https://www.digikey.com/en/products/detail/vishay-semiconductor-opto-division/VEML7700-TT/6210690
  - https://www.lcsc.com/product-detail/VEML7700-TT_C1850416.html
  - https://www.adafruit.com/product/4162
  - https://learn.adafruit.com/adafruit-veml7700/pinouts
  - https://www.adafruit.com/product/5378
  - https://www.digikey.de/en/products/detail/adafruit-industries-llc/4162/9997696
  - https://botland.store/search?s=VEML7700
  - https://diamondcoatings.com/wp-content/uploads/2020/09/Diamond-AR1617-Film-Datasheet-v2.1.pdf
  - https://diamondcoatings.co.uk/product/diamox-ar1617-anti-reflective-film-sheet/
  - https://diamondcoatings.com/antireflective-film/
  - https://www.sanwa.co.jp/product/acc/protectfilm/free_cut.html?pan_list=1
  - https://www.123-3d.nl/Polymaker-PolyLite-ASA-filament-1-75-mm-Black-1-kg-70195-PF01001-PM70195-i7641-t104864.html
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md (lines 66, 134, 232, 257, 274)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/display_market.json
  - Not verified (fetch returned 429): https://www.telesinstore.com/products/anti-reflection-screen-protector-for-pocket-3, so the definition of the 0.7% baseline (luminous or minimum, glass or film) is unconfirmed

