# Ad8318 class log detector power meter: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_22e49a73-ef5`_

- **Part:** AD8318-class log detector power meter (extended/optional, qty 1): a detector module plus an ADS1115 ADC, a 9 V pre-regulator and a divider in a small box on the LAB BUS (I2C-B + AUX12 + GND)
- **Current pick:** A generic AD8318 module of the design Silicon Chip measured (33 x 24.5 mm, 78L05, edge SMA, 1 MHz-8 GHz), read by an Adafruit ADS1115 #1085, powered from AUX12 through a 9 V pre-regulator and a divider, in a box
- **Current price usd:** 25-60 for the whole box (STACK.md 2.11, a model estimate). The module figures behind it are old: $16.50 (Banggood 2018, no longer listed) and $39.00 (eBay, old listing, eBay returned 403). ADC: Adafruit #1085 at $14.95, or EUR 13.13 ex VAT / EUR 15.62 incl. VAT ($14.76 / $17.56) at DigiKey DE (price checked in search B).
- **Decision:** replace_conditionally
- **Chosen:** The same AD8318 module design, bought from the cheapest live AliExpress listing. First choice: item 3256809368914605, 'Rf logarithmic detector Power detection AD8318 (1-8000MHz)', $12.09, 31 sold, rating 4. Take it only if its photos show the classic board. Otherwise take item 3256805661032022, '1-8000MHz AD8318 RF Logarithmic Detector 70dB RSSI Measurement Power Meter', $13.35, 47 sold, rating 4.2. Its title is word for word the classic eBay design. The ADC stays the genuine Adafruit ADS1115 #1085. The 9 V pre-regulator, the divider and the box stay as planned.
- **Chosen price usd:** Module $12.09 or $13.35: AliExpress search-page prices, US-located view, 18 Oct 2026, without VAT and shipping. Both listings were re-confirmed on the wholesale pages this session. EU landed cost (model, per operator notes 34-35): VAT x1.19-1.25, plus EUR 3 duty ($3.37), plus EUR 2 Union handling fee ($2.25, from about 1 Nov 2026). That gives about $20.0-22.3 plus shipping (not seen). Box: about $26.85-28.11 ex VAT, or about $37.6-39.9 EU-landed with the Adafruit ADS1115 from DigiKey DE ($17.56 incl. VAT), plus shipping, the 9 V regulator, the 3.3 V LDO, the divider and the enclosure (not priced).
- **Saving usd:** On the module line: $3.15-26.91 against the old reference listings ($16.50-39.00), at listing prices without VAT. On the box: it now lands at the bottom of the $25-60 band (about $27-28 ex VAT, about $38-40 EU-landed plus small parts). The $60 top of the band is no longer needed, but nothing is saved against the $25 low end. If the conditions fail, nothing is saved: return the module and keep the current pick.
- **Equivalence proof:** Neither listing is proven equivalent yet. It is the same part class and design, so equivalence holds only if the board is the classic PCB with a genuine AD8318. Then every spec that matters is identical, because it is the board Silicon Chip measured (SC Mar 2018, re-read this session):
  - Frequency: 1 MHz-8 GHz chip. Input coupling cutoff about 300 kHz.
  - Linear range: about -5 to -60 dBm (60 dB in practice, about 55 dB strictly linear, about 70 dB usable). Rated -65 to +5 dBm.
  - Slope: -24.33 mV/dB measured (-25 nominal). The 100 MHz, 1, 2 and 4 GHz curves sit within +/-1 dB of each other.
  - Power: 68 mA. Needs at least 7.5 V (78L05, 2 V dropout); 9 V was used in the test.
  - Output 0.5-4.6 V, board 33 x 24.5 mm, edge SMA.
  - Interfaces are unchanged (analog into the ADS1115, ti-ads1015 IIO or smbus2 on Ubuntu 24.04 arm64, AUX12 through the 9 V regulator), so drivers, rails and case do not change.
  - Hard rules: it is a passive, measure-only, conducted-only bench detector. It does not transmit and is not a loop.
  - Unverified: AliExpress item pages return a captcha ('punish' page, checked with curl and WebFetch this session), so store, PCB revision, variants and shipping could not be seen. That is why this is conditional.
  - Price plausibility: grey-market AD8318ACPZ chips sell at $6.75 on AliExpress, and DigiKey sold the discontinued ACPZ-R2 at $6.96 each at 250 pcs. A $12 module with a real die is plausible but not proven.
- **Conditions or tests:** Before ordering:
  - The listing photos must show the classic board: 33 x 24.5 mm, SOT-89 78L05, edge SMA, 0603 Clpf/Cobp pads, 510 ohm Tadj, and a chip with the ADI logo, 'AD8318' and a date code. If the $12.09 listing does not show this, use the $13.35 listing.
  - Pay with AliExpress buyer protection.
  
  On arrival (bench, conducted only):
  1. Current: feed 9.0 V. Accept 60-75 mA (my band around the 68 mA measured). A lower draw points to a substituted part such as an AD8317 or AD8319, which draw much less (from memory; analog.com returned 503).
  2. Slope and range: hold the tinySA Ultra+ sine output at -20 dBm. Its sine output tops out at -19 dBm, is +/-2 dB, keeps harmonics below -40 dBc and runs up to 900 MHz (tinysa.org spec, re-read). Step the level down with LiteVNA-measured pads and the PE4312 step attenuator, using their measured S21 at each frequency. Test at 137, 435 and 740 MHz.
     - Pass: slope between -24.0 and -26.0 mV/dB, straight within +/-1 dB from -20 to -60 dBm, and still tracking at -65 dBm.
     - AD8317 and AD8319 substitutes show about -22 mV/dB and a floor near -55 or -45 dBm (from memory, not re-checked), so they fail here.
  3. Top segment, -20 to -5 dBm: the tinySA cannot source more than -19 dBm sine. Either use an amplifier whose gain the LiteVNA has measured, run at least 10 dB below its P1dB (for example the ZFL-500LN+ from the noise-source build), or record this segment as unverified on this unit (the design was measured by Silicon Chip). Never exceed +5 dBm at the detector input.
  4. Flatness at 1700 and 2200 MHz: use the tinySA 'highest accuracy' mode, which has no level spec. Read the level on the tinySA analyzer input first, then on the detector. Pass if it is within +/-1 dB of the 435 MHz line after calibration.
  5. Fit Clpf 1 nF and Cobp 10 nF (0603). Then check that a 10 MHz tone gives no ripple. The 100 kHz video bandwidth is still far faster than the ADS1115's 860 SPS.
  6. Record S11 with the LiteVNA (low drive, conducted) and use it as a match correction.
  7. If any check fails, return the module and try the other listing. If that also fails, keep the current pick.
- **Rejected:**
  1.
    - **Name:** AliExpress 3256811787185958, AD8318 module, $21.69 (was $30.99)
    - **Why:** Not worse on paper, but it costs $8-10 more than the $12.09/$13.35 listings and shows no sales count. Specs come from the title only. Fallback only.
  2.
    - **Name:** AliExpress 3256812931208143, AD8318 module '7-15VDC', $29.99, 1 sold
    - **Why:** Its only gain is running from AUX12 without a 9 V pre-regulator, which is a part costing cents to a few dollars, while the module costs $16.6-17.9 more. Regulator type and dropout are unknown and it has one sale. Fallback only if running straight from AUX12 becomes a requirement.
  3.
    - **Name:** AliExpress multi-variant AD8310/AD8313/AD8318 listings 3256809377096025 ($7.55, 166 sold) and 3256811776336425 ($5.45, 147 sold)
    - **Why:** The headline price belongs to an unknown variant, and the AD8318 variant's price could not be seen (item pages return a captcha, confirmed this session), so the price cannot be treated as real. The AD8310 (up to 440 MHz) and AD8313 (about 0.1-2.5 GHz) variants are worse in frequency coverage.
  4.
    - **Name:** AliExpress 3256808302198918, 'AD8318 ... 50dB Dynamic Range', $32.19
    - **Why:** The seller's own title claims 50 dB, worse than about 60 dB, and it costs more.
  5.
    - **Name:** Other AD8318 module listings at $35.29-112.19 (3256812746486737, 3256812910336010, 3256809956425895, 3256808194454594, 3256813050317834, 3256812261260399, 3256813192661825)
    - **Why:** Same chip claims with no proof of better build, priced well above $12-13, with 0-3 sales.
  6.
    - **Name:** AliExpress 3256809304996792, 'AD8318 True RMS', $160.69
    - **Why:** The AD8318 is a log detector, not RMS, so the listing is mislabeled and the seller is unreliable. It is also 13 times the price.
  7.
    - **Name:** MikroElektronika RF Meter Click MIKROE-2034 (AD8318 + MCP3201)
    - **Why:** - Price: TME $52.31 with 0 in stock (checked); DigiKey $53 (from search A, not re-read). Dearer than the module + ADS1115 route.
  - ADC: the MCP3201 is 12-bit with no PGA, against the 16-bit ADS1115 with PGA.
  - Interface: SPI, which the LAB BUS does not carry (it has I2C-B, AUX12 and GND only), so it needs a new cable and header pins.
  - Supply: the AD8318 side needs 5 V, and the LAB BUS has no 5 V.
  8.
    - **Name:** AD8317 modules ($6.41-59.39)
    - **Why:** 55 dB range (the listing says -55 to 0 dBm) against about 60-65 dB, so it loses 5-10 dB at the low end. Worse.
  9.
    - **Name:** MikroE RF Meter 3 Click (LT5581), $29
    - **Why:** 10 MHz-6 GHz and about 40 dB: loses 1-10 MHz and about 20-26 dB of range. Worse.
  10.
    - **Name:** LTC5582 RMS detector, chip/DIY
    - **Why:** Its low end is 40 MHz, so all of HF is lost. Chip only, so a DIY RF layout. Grey-market chips at $5.89-6.65 sell below DigiKey's $20.97, which suggests counterfeits.
  11.
    - **Name:** ADL5513, chip only
    - **Why:** Tops out at 4 GHz against 8 GHz. Chip only, so a DIY build of unproven quality. At $18.85 the chip alone costs more than the module, and DigiKey shows 0 stock.
  12.
    - **Name:** HMC611
    - **Why:** Obsolete, 106 mA against 68 mA, no module, grey market only.
  13.
    - **Name:** Mini-Circuits ZX47-60LN-S+
    - **Why:** $177.73 with 0 in stock. Not cheaper.
  14.
    - **Name:** Standalone OLED 1 MHz-8 GHz meter, AliExpress 3256801533533451, $26.79
    - **Why:** The title range of -55 to -5 dBm is 50 dB against about 60 dB. The chip is not named, the USB protocol and Ubuntu arm64 support are unknown, and it cannot sit on the I2C LAB BUS.
  15.
    - **Name:** 'LF-8000MHz RF Power Meter V1.0 -65~15 dBm' (3256812384783120 / 3256812057791397), $27.39 / $48.49
    - **Why:** Chip, interface and linearity are not stated, and no independent measurement turned up (one search). It cannot be read by the Q6A on the LAB BUS. Not provable.
  16.
    - **Name:** Passion Radio RF-Power8000 (EU seller, France)
    - **Why:** Stated range -45 to -5 dBm (40 dB), and its data sheet gives 1 MHz-5 GHz. Worse in range and frequency. Seen only in a search snippet.
  17.
    - **Name:** Fruugo AD8318 module, EUR 34.95 incl. delivery (.fi storefront)
    - **Why:** Same module at a higher price than the AliExpress landed cost, seller origin unknown. Seen only in a search snippet.
  18.
    - **Name:** DIY board from a bare AD8318 chip ($6.75 'original' or $18.75 'REEL7' on AliExpress)
    - **Why:** High remark/counterfeit risk, a home RF layout of unproven quality, and not cheaper than a $12 assembled module once a PCB is made.
  19.
    - **Name:** Reading the detector with the RP2040 supervisor's ADC instead of an ADS1115
    - **Why:** 12-bit with documented DNL errata, and it ties lab code to the safety supervisor. Worse.
  20.
    - **Name:** Generic ADS1115 boards (AliExpress $1.09-1.96 listing prices; AZ-Delivery EUR 6.99 incl. VAT from a search snippet, its page returned 429) in place of the Adafruit #1085
    - **Why:** Not adopted by default.
  - Documented boards step in 16-count jumps, which is 12-bit ADS1015 behaviour. One case was an AZDelivery 3-pack (Arduino forum).
  - ESPEasy lists the markings (BOGI/N4J for ADS1115, BRPI/N7J for ADS1015) and warns about boards with the markings removed.
  - A unit could save about $13-16 only if it passes the marking check, a 1-LSB step test and a conversion-time test. The Adafruit board stays the default.
  21.
    - **Name:** Used HP 435B/437B or Agilent E4418B with a thermal sensor
    - **Why:** Mains-powered GPIB bench units, not portable and not on the LAB BUS. Price not verified.
  22.
    - **Name:** Dropping the box and using tinySA channel power only
    - **Why:** This is already the core path at $0 extra. It is not a like-for-like replacement for the box, because the tinySA cannot also be a live coupler-tap overload alarm while it is busy elsewhere.
- **Confidence:** medium
- **Stack changes:** - Rails: unchanged. The module still needs 7.5-9 V from AUX12 (regulated 12 V, behind the PTC) through the 9 V pre-regulator, about 70 mA, about 0.6 W.
  - I2C address bug in the plan: radio_lab.json puts the box's ADS1115 at 0x48, but the sled's ADS1115 already sits at 0x48 on the same LAB BUS (I2C2 through the TCA9517; STACK.md lines 74, 631 and 672). Tie the box ADS1115's ADDR pin to VDD to get 0x49, and add 0x49 to the I2C address map and to labd.
  - ADS1115 supply: it needs 3.3 V, because the LAB BUS pull-ups are at 3.3 V and the ADS1115 logic-high threshold is 0.7 x VDD (datasheet value, not re-read this session). So the box needs a small 3.3 V LDO. Keep the divider, because VOUT can reach 4.6 V (Silicon Chip), above VDD + 0.3 V.
  - Fit Clpf 1 nF and Cobp 10 nF (0603) on the module before any use below 22 MHz.
  - Software: the volts-to-dBm table tool stays. Store the slope and intercept of each unit from the acceptance test.
  - Case: same 33 x 24.5 mm board, no change.
  - Drivers: no change (ti-ads1015 IIO or smbus2 on Ubuntu 24.04 arm64).
  - Cost: change the STACK.md 2.11 row from 'AD8318 box $25-60 (model)' to about $27-28 ex VAT, or about $38-40 EU-landed (model) plus small parts, conditional on the acceptance test.
- **Sources:**
  - https://www.siliconchip.com.au/Issue/SC/2018/March/El+Cheapo+Modules+14%3A+Logarithmic+RF+Detector
  - https://www.aliexpress.com/w/wholesale-AD8318-RF-power-meter.html
  - https://www.aliexpress.com/w/wholesale-ad8318-module.html
  - https://www.aliexpress.us/item/3256809368914605.html (captcha, details unverified)
  - https://www.aliexpress.us/item/3256805661032022.html (captcha, details unverified)
  - https://www.tme.eu/en/details/mikroe-2034/expansion-boards/mikroelektronika/rf-meter-click/
  - https://tinysa.org/wiki/pmwiki.php?n=TinySA4.Specification
  - https://forum.arduino.cc/t/ads1115-problems-or-fake/658746
  - https://espeasy.readthedocs.io/en/latest/Plugin/P025.html
  - https://www.aliexpress.com/w/wholesale-ADS1115-module.html
  - https://az-delivery.de/en/products/analog-digitalwandler-ads1115-mit-i2c-interface (HTTP 429; price from search snippet)
  - https://www.passion-radio.com/swr-power-meter/rf-power8000-926.html (search snippet only)
  - https://www.fruugo.fi/detecteur-logarithmique-ad8318-1m-8ghz-70db-controle-alc-agc-dynamique/p-417278213-880458364 (search snippet only)
  - https://www.digikey.de/en/products/detail/adafruit-industries-llc/1085/5761229 (from search B)
  - https://www.digikey.com/en/products/filter/rf-detectors/862?keywords=AD8318 (from search A)
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md (lines 74, 301, 631, 672: I2C map and 2.11 row)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (items 34-35: EU EUR 3 duty and EUR 2 handling fee)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json (box ADS1115 at 0x48)

