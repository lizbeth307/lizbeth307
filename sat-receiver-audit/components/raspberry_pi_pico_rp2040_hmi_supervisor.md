# Raspberry pi pico rp2040 hmi supervisor: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_071e1025-145`_

- **Part:** Raspberry Pi Pico (RP2040, SC0915, no headers): HMI and supervisor MCU on switched LAB5 via VSYS, qty 2 (1 spare)
- **Current pick:** Raspberry Pi Pico SC0915 from The Pi Hut (STACK v1). reaudit_A already moved the source to DigiKey 2648-SC0915CT-ND.
- **Current price usd:** 10.12 for 2 (2 x GBP 3.80 incl. 20% UK VAT, The Pi Hut). I re-checked this on 18 Oct 2026 in the Pi Hut product JSON: variant SC0915, GBP 3.80. Ex UK VAT it is GBP 3.17 = $4.22 each, $8.43 for 2. reaudit_A's corrected line is DigiKey at $4.59 each = $9.18 ex VAT. FX: 1 GBP = 1.3318 USD, 1 EUR = 1.1241 USD.
- **Decision:** keep
- **Chosen:** Keep the genuine Raspberry Pi Pico SC0915 (non-wireless) with no change to the part. No analog survived. Sourcing: buy it in the planned DigiKey basket by default. Use Berrybase (RPI-PICO) or Welectron (RP1-709150), both on the raspberrypi.com Approved Reseller list, only when the Picos share a basket with other items from that shop. Do not use The Pi Hut for an EU delivery.
- **Chosen price usd:** Default, DigiKey: $9.18 for 2 at the US list price ex VAT (reaudit_A). At DigiKey DE it is EUR 4.03 ex VAT / EUR 4.7957 incl. 19% VAT each, which is $9.06 / $10.78 for 2 (40,279 in stock, Active). Conditional, Berrybase or Welectron: EUR 3.45 ex VAT / EUR 4.10 incl. 19% DE VAT each, which is $7.76 / $9.22 for 2.
- **Saving usd:** 0.00 on the part, because no cheaper analog is not-worse. Sourcing only: $0.94 against v1 was already booked by reaudit_A (DigiKey $9.18). A further $1.30 for 2 ex VAT (DigiKey DE $9.06 to Berrybase $7.76) is real only if the Picos ride on another Berrybase or Welectron order. On the incl.-VAT basis Berrybase is $9.22 against v1's $10.12, a $0.90 saving. A standalone Berrybase or Welectron order loses money: Berrybase shipping is EUR 4.95 in DE and EUR 9.90 to the EU below EUR 200/250; Welectron is EUR 4.95 in DE and EUR 14.90 to the EU.
- **Equivalence proof:** Every surviving source sells the identical board, so every spec that matters is equal by identity.
  - Berrybase: 'Manufacturer ID: SC0915', product RPI-PICO, 100+ in stock, EUR 4.10 incl. VAT.
  - Welectron: HAN SC0915, art. RP1-709150, EUR 4.10 gross / 3.45 net, 10+ in stock.
  - Kiwi: MPN SC0915, EAN 5056561801445, EUR 3.49 ex VAT, 250+ in stock.
  - DigiKey DE: SC0915, Active.
  - Pi Hut: SC0915, barcode 5056561801445.
  - GTIN note: Berrybase and Welectron both list GTIN 0617588405587, not 5056561801445. Both shops are approved resellers, so this is probably a second Raspberry Pi GTIN (possibly reel stock; not verified). Check the board markings on arrival anyway.
  
  Specs I re-checked in the Pico datasheet RP-008307-DS-2 (build 03/07/2026), against the stack's critical list:
  - Flash W25Q16JV; crystal Abracon ABM8-272-T3 at 12 MHz, which keeps the spur plan valid.
  - VSYS 1.8-5.5 V into the RT6150 buck-boost; D1 Schottky from VBUS to VSYS, so the ORing scheme in the re-audit holds.
  - GPIO24 is VBUS sense, GPIO23 is the RT6150 PS pin, GPIO29 reads VSYS/3.
  - 3V3_EN on pin 37 with a 100k pull-up to VSYS; keep the 3V3 load under 300 mA.
  - R7 is a removable 0603, so an LM4040 can drive ADC_VREF.
  - 4 x 2.1 mm mounting holes.
  - -20 to +85 C, 70 C recommended maximum ambient.
  - 26 GPIO, 2 UART, PIO, 3 external ADC inputs, SWD plus RUN on pin 30.
  
  Approved-reseller status was confirmed on raspberrypi.com/resellers for BerryBase (listed with a pizero.shop link), Welectron, Kiwi, DigiKey, TME, The Pi Hut and Pimoroni. Firmware, wiring, rails, drivers (cdc_acm, picotool, OpenOCD on Ubuntu 24.04 arm64) and the case are unchanged. The part has no RF emission role, so the receive-only, no-loop and conducted-only rules are unaffected.
- **Rejected:**
  1.
    - **Name:** WeAct Studio RP2040 core board (2-16 MB, USB-C)
    - **Why:** Worse on specs the stack uses. I checked the official HDK PINout.PNG myself:
  - Right header order is VBUS, VSYS, GND, 3V3, GP24, ADC_VREF, GP29, GND, GP28... RUN exists only on the NRST button, so there is no RUN edge pin for Q6A pin 38 SWD/OpenOCD service.
  - No 3V3_EN pin. GP23 is a user key, so there is no RT6150 PS control and the regulator is unknown. GP24 is a plain pin, so there is no on-board VBUS sense.
  - Not pin-compatible with Pico pins 30-37. No mounting holes are visible.
  - No published schematic, so the VBUS-to-VSYS diode (the back-feed rule), regulator spurs, crystal and temperature rating cannot be verified.
  - Sold on AliExpress only; no price could be verified, so no saving is shown.
  2.
    - **Name:** VCC-GND Studio YD-RP2040 (V1.1, 4/16 MB)
    - **Why:** Documented ADC defect. Repo issue #1 'YD-2040 and ADC' (opened 1 Dec 2025, still open) reports boards reading 65535 on every ADC channel. VREF measured about 0 V because the VREF-to-3V3 link is unpopulated; a jumper fixed it. The schematic shows ADC_VREF only on a 0-ohm link pad. Pin 35 is GP29 instead of ADC_VREF, pin 37 is GP23 instead of 3V3_EN, pin 40 is the ORed Vout instead of VBUS, and GP24 is a user key with a 10k pull-up, so there is no VBUS sense. ME6215 LDO current not verified. No temperature rating, no mounting holes shown, no price or seller verified.
  3.
    - **Name:** Unbranded 'Pico-compatible' RP2040 boards (AliExpress, $1.09-3.39 listed)
    - **Why:** No schematic and no measurements. Flash, crystal, regulator and the VBUS diode vary by listing, so the back-feed rule, ADC_VREF, temperature range and genuine flash cannot be verified. Listing and store identity are unverified, with a counterfeit or variant lottery. This fails the not-worse and legally-sold/not-counterfeit tests.
  4.
    - **Name:** Used genuine Pico (eBay etc.)
    - **Why:** No verified price. ESD and flash-wear history unknown, no warranty, and shipping exceeds any possible saving against EUR 3.45 net new.
  5.
    - **Name:** DIY bare RP2040 (RP2-B2) on a custom carrier
    - **Why:** Not cheaper at qty 2 once PCB and PCBA are added (not quoted). Crystal, RF layout and back-feed protection would need fresh validation, and there is no measured evidence. Revisit only if P7 commits to a custom HMI PCB.
  6.
    - **Name:** TME SC0915 (PL, approved reseller)
    - **Why:** Price and stock not real enough to book. The page shows 'no-prices'; structured data gives an aggregate of $3.71-4.00 with no tiers; visible stock reads 0 while the data says 1929.
  7.
    - **Name:** TinyTronics SC0915 (SKU 003407)
    - **Why:** EUR 5.50 incl. / EUR 4.55 ex VAT and 'Not in stock'. That is dearer than Berrybase, so it cannot ride on the day-1 TinyTronics Q6A order. Also not on the RPi Approved Reseller list.
  8.
    - **Name:** Adafruit 4864
    - **Why:** $4.00 but out of stock on 18 Oct 2026. Could ride on the day-1 Adafruit order if it returns. It ships from the US, so EU import VAT and the new EU flat duty apply.
  9.
    - **Name:** The Pi Hut (v1 source) for an EU delivery
    - **Why:** The price is real (GBP 3.80, product JSON). But per the delivery page (fetched 18 Oct 2026), EU shipping is currently 'only DHL Express' at GBP 30 ($39.95), and since the EU change on 1 July 'all shipments now require a mandatory flat-rate customs duty' (amount not stated). VAT is collected through IOSS for orders up to EUR 150. That makes it the most expensive landed source for a $8 line.
  10.
    - **Name:** Kiwi Electronics KW-2772 (NL, approved reseller)
    - **Why:** Not worse, but EUR 3.49 ex VAT is EUR 0.04 dearer than Berrybase or Welectron at EUR 3.45. NL/EU shipping not verified. Acceptable only if a Kiwi basket already exists.
  11.
    - **Name:** Pico 2 (RP2350), Pico H, Waveshare RP2040-Plus, other RP2040 boards (XIAO, Tiny 2040, KB2040, RP2040-Zero, etc.)
    - **Why:** Per search 1, not re-verified by me: dearer (Pico 2 EUR 4.90-5.50, Pico H EUR 4.80-5.50, RP2040-Plus $6.99-8.99), or fewer than the 26 edge GPIO the pin map uses (RP2040-Zero has 20 and was already rejected in D12).
- **Confidence:** high
- **Conditions or tests:** Source rule:
  - Buy the 2 Picos in the DigiKey HMI basket (PEC11R, KSC641J, ferrites, TCA9555).
  - Switch to Berrybase or Welectron only if that shop's basket already exists (or, for Berrybase, reaches EUR 200 in DE / EUR 250 to the EU for free shipping). Never as a standalone order.
  - Never buy the W, WH or Pico 2 W variants, which add a radio.
  
  Incoming inspection:
  - RP2040 marked RP2-B2, Winbond W25Q16JV, Abracon 12 MHz crystal, Raspberry Pi Pico silkscreen and logo, R7 (0603) present.
  - Enumerates as RPI-RP2 in BOOTSEL; flash JEDEC ID EF4015 read by test firmware.
  - Applies to either GTIN in circulation.
  
  Bench test, changes the stack's 'drive GP23 high' rule. Mark Omo's measurement (pico-adc.markomo.me, which I verified):
  - Supply noise: 1.0 mV RMS in PSM vs 1.3 mV RMS in forced PWM ('Low-Noise Mode').
  - Input-referred noise: 0.97 vs 1.36 LSB RMS.
  - ENOB: 8.92 vs 8.84 by sine fit.
  - DNL 8.9 / INL 7.85 LSB, unchanged.
  So A/B test GP23 low vs high at bring-up. Measure ADC noise on the 1:6 SW divider, and the RT6150 spurs in the HF/VHF harmonic scan. Keep PWM only if its fixed-frequency spur suits the RF plan better; accuracy comes from the LM4040 plus the INA228 cross-calibration.
  
  Re-audit fixes still apply:
  - A Schottky from LAB5 into VSYS.
  - The divider taps SW, not N.
  - Flash the Pico only with the main switch ON or with the board unplugged from LAB5.
  - TX goes high-impedance while the Q6A 3.3 V rail is absent.
  - B11: the Pico J21 pulse starts the board in 20 of 20 cycles.
  
  Verification limits: the shared WebSearch budget was exhausted (my one search was refused). All findings come from direct fetches of seller pages, the RPi reseller list, the Pico datasheet, the WeAct pinout, and the YD schematic and issue. Not verified:
  - Mouser and Farnell prices.
  - Berrybase and Welectron VAT handling for non-DE EU destinations.
  - Kiwi shipping.
  - DigiKey's free-delivery threshold outside DE.
  - The amount of the EU flat customs duty.
- **Stack changes:** 1. BOM row 'MCU HMI і супервізора':
  - Seller: The Pi Hut changes to DigiKey 2648-SC0915CT-ND.
  - Price: $9.18 ex VAT (US list); DigiKey DE EUR 8.06 ex / EUR 9.59 incl. 19% VAT for 2.
  - Status: verified 18 Oct 2026, 40,279 in stock, Active.
  - Budget note: Berrybase RPI-PICO or Welectron RP1-709150 at EUR 3.45 net / 4.10 incl. 19% DE VAT, on a shared basket only. Kiwi KW-2772 EUR 3.49 net.
  - Spec text: 'SC0915 non-wireless only'.
  
  2. Shopping order: move '2 Pico' from row 6 (no seller named) into the DigiKey basket, and pull that basket into week 1. The Pico is needed for the W1-2 board gate (J21 pulse test B11, boot with the Pico in reset).
  
  3. DigiKey DE delivers free only from EUR 75; below that it charges EUR 25 ($28.10). The HMI basket (3 PEC11R, 10 KSC641J, 2 ferrites, 2 Pico, TCA9555) is about EUR 27 ex VAT, so the sourcing pass must consolidate DigiKey lines (4D panel fallback, Lime sled parts) or budget the EUR 25.
  
  4. The Pi Hut for an EU buyer: DHL Express only (GBP 30) plus a mandatory flat-rate EU customs duty since 1 July 2026, with IOSS VAT up to EUR 150.
  - Re-cost the remaining Pi Hut lines (MTT hub GBP 18.50, Pro Stick Plus GBP 52.50) or move them to EU sellers.
  - Correct the customs section: 'UK: sellers collect VAT up to GBP 135' is the rule for UK buyers.
  - Note the new EU flat duty for every non-EU parcel (Adafruit, Pololu, LCSC, Waveshare, AliExpress, Nooelec); amount to be verified.
  
  5. HMI firmware/bring-up: replace 'drive GPIO23 high' with the GP23 A/B test above.
  
  6. No change to rails (LAB5 through a Schottky into VSYS), connectors, pin map, drivers, firmware build or case. The part is identical.
- **Sources:**
  - https://thepihut.com/products/raspberry-pi-pico.json
  - https://thepihut.com/pages/delivery
  - https://www.berrybase.de/en/raspberry-pi-pico-rp2040-mikrocontroller-board
  - https://www.berrybase.de/en/footer/information/payment-dispatch/
  - https://www.welectron.com/Raspberry-Pi-Pico_1
  - https://www.welectron.com/Shipping-cost
  - https://www.digikey.de/en/products/detail/raspberry-pi/SC0915/13684020
  - https://www.kiwi-electronics.com/en/raspberry-pi-pico-10494
  - https://www.tme.eu/en/details/sc0915/raspberry-pi-minicomputers/raspberry-pi/
  - https://www.tinytronics.nl/en/development-boards/microcontroller-boards/raspberry-pi-pico/raspberry-pi-pico-rp2040
  - https://www.adafruit.com/product/4864
  - https://www.raspberrypi.com/resellers/
  - https://pip-assets.raspberrypi.com/categories/610-raspberry-pi-pico/documents/RP-008307-DS-2-pico-datasheet.pdf (local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/pico_dl_ds/pico-ds.pdf)
  - https://pico-adc.markomo.me/
  - https://raw.githubusercontent.com/WeActStudio/WeActStudio.RP2040CoreBoard/master/HDK/PINout.PNG (local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/pico_dl_weact/pinout.png)
  - https://github.com/initdc/YD-RP2040/issues/1
  - https://raw.githubusercontent.com/initdc/YD-RP2040/master/YD-2040-2022-V1.1-SCH.pdf (local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/pico_dl_yd/sch.pdf)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_A_compute_software.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json

