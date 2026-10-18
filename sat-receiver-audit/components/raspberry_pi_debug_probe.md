# Raspberry pi debug probe: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** Raspberry Pi Debug Probe (SC0889). Bench/field SWD (CMSIS-DAP v2) and 3.3 V UART tool for the Pico supervisor, the IMU-pack RP2040-Zero and the Q6A console. Tier bench, group Bench electronics, qty 1.
- **Current pick:** Raspberry Pi Debug Probe SC0889 from Adafruit (5699), on the bring-up step-2 Adafruit launch order.
- **Current price usd:** 12.00, US list price excluding tax (Adafruit 5699, in stock). For a buyer in the EU this is not the landed cost. Modelled for DE at 19% VAT: at least 14.28 (12.00 + import VAT). If the order ships postal or via IOSS, about 18.29 after the EUR 3/item temporary duty (VAT is charged on price + duty), or about 20.54 once the EUR 2/item Union handling fee starts (~1 Nov 2026). A share of shipping and any carrier fee come on top. Not verified: whether Adafruit ships EU orders postal/IOSS or by courier.
- **Decision:** replace_conditionally
- **Chosen:** Same part, seller change only. No different product survives as an analog. Buy the identical Raspberry Pi Debug Probe SC0889 (EAN 5056561803265, reichelt item 'RPI DEBUG PROBE') from reichelt elektronik, Germany, which is on raspberrypi.com's Approved Reseller list. Add it to the reichelt cart that other P5 decisions already create (G1 Goobay 58814 F lead; G2 Verbatim microSD + Goobay 95717 EDL cable; G3 CELLCON tape, tesa 56223 tape, Jamara bag). Fallback 1, if no reichelt order is placed: DigiKey DE 2648-SC0889-ND on the step-7 DigiKey order (PEC11R/KSC641J/ferrites). Fallback 2: welectron (EUR 11.90) or BerryBase (EUR 12.20) only if an order from them exists. Keep Adafruit only for a non-EU build, or if no EU order exists at all.
- **Chosen price usd:** 10.86 ex VAT (EUR 9.66, computed) / 12.93 incl. 19% DE VAT (EUR 11.50, verified 18 Oct 2026: in stock, 1-2 business days). Shipping is DHL EUR 5.95 up to 10 kg (DE), already paid by the shared reichelt cart. On a separate order the total is EUR 17.45 = 19.62. Fallback DigiKey DE: 11.85 ex VAT / 14.10 incl. VAT (EUR 10.54 / 12.54, 2,782 in stock). Its shipping is EUR 25 under EUR 75 and free from EUR 75; that charge is already paid by the step-7 order, so the probe adds only its own price. FX 1.1241 USD/EUR.
- **Saving usd:** 1.14 on the stack's USD ex-tax base (12.00 to 10.86). Landed in DE, modelled: 12.93 against Adafruit's 14.28 minimum, a saving of at least 1.35. Against about 18.3-20.5 once the EUR 3 duty and EUR 2 UHF apply, the saving is about 5.4-7.6. With the DigiKey DE fallback: 0.15 ex VAT, and landed 14.10 vs 14.28-20.54. The saving is zero or negative if reichelt is used as a dedicated order (19.62).
- **Equivalence proof:** Identity check (the identical SKU, so every spec is equal):
  - reichelt lists manufacturer part SC0889 and EAN 5056561803265. BerryBase, welectron (HAN SC0889) and Botland list the same EAN. DigiKey and TME list MPN SC0889.
  - reichelt's contents list matches the product brief: board in a transparent plastic case, USB cable, JST-JST cable, JST to 0.1in female cable, JST to 0.1in male cable.
  - Authenticity: reichelt, BerryBase, welectron, Kiwi, Botland, Digi-Key, Mouser and Farnell are on raspberrypi.com/resellers (fetched 18 Oct 2026). TinyTronics is not.
  
  Specs that matter here, re-checked on primary sources. All are carried over unchanged by the same SKU:
  (1) CMSIS-DAP v2 with DAP_SWD_Sequence. OpenOCD needs it for RP2040 multidrop TARGETSEL (cmsis_dap.c: CMD_DAP_SWD_SEQUENCE 0x1D, cmsis_dap_metacmd_targetsel). OpenOCD's adapter docs list only 'cmsis_dap (use an adapter with CMSIS-DAP version 2.0), ftdi, all bitbang based' as multidrop-capable.
  (2) USB 2e8a:000c, product string 'Debug Probe (CMSIS-DAP)' (debugprobe usb_descriptors.c / board_debug_probe_config.h).
  (3) 3.3 V nominal I/O; -20 to +70 C; 22x32 mm.
  (4) Protection, from the schematic PDF: 100R series resistors on TX, RX, CLK and DIO, and 74AUP1T17GW Schmitt buffers on UART RX and SWDI (PROBE_IO_SWDI). There is no reset pin.
  (5) Two SM03B-SRSS-TB JST-SH connectors to the RPi 3-pin debug spec, and five LEDs.
  (6) Production lifetime: the live product page says 'until at least January 2030'. The Feb 2023 brief says January 2028, so the stack should use 2030.
  (7) Same RP2040 and 12 MHz crystal, so the spur family in the D10 matrix is unchanged.
  (8) Host side: upstream OpenOCD v0.12.0 contrib/60-openocd.rules matches ATTRS{product}=="*CMSIS-DAP*" (GROUP plugdev, uaccess), so the probe gets access with no custom rule. Not verified: that Ubuntu noble's package installs this file.
  
  Adversarial findings against the chosen seller:
  - The price is real: fetched, in stock.
  - reichelt does not show an ex-VAT price; mine is computed.
  - Shipping for EU countries other than DE was not shown, and the incl.-VAT price changes with the buyer's country VAT.
  - Units may ship with older firmware. Re-flash debugprobe v2.3.1 UF2, exactly as for an Adafruit unit.
  None of these is a spec loss.
- **Rejected:**
  1.
    - **Name:** Raspberry Pi Pico / Pico H (RP2040) + official debugprobe_on_pico.uf2 (reichelt EUR 4.80 incl. VAT; Adafruit 4864 $4.00 out of stock)
    - **Why:** Worse in protection and build. board_pico_config.h sets PROBE_IO_RAW: SWDIO goes straight to GP3 and UART RX to GP5, with none of the Debug Probe's 100R series resistors or 74AUP1T17GW Schmitt buffers (confirmed in the schematic PDF and the board_debug_probe_config.h PROBE_IO_SWDI comment). Also bare PCB with no case (the product brief warns against contact with conductive items, and the probe travels in the field pouch); no JST-SH 3-pin probe-side connectors or leads; 1 LED instead of 5; no compliance as a debug tool. Better in one point only: a reset output on GP1. Fails 'same or better build quality'. Keep it only as an emergency spare.
  2.
    - **Name:** Raspberry Pi Pico 2 (RP2350) + debugprobe_on_pico2.uf2 (Adafruit 6006 $6.25, out of stock)
    - **Why:** Has every deficit of the Pico DIY (raw I/O, no case, no JST-SH, 1 LED, no leads). The RP2350 board is also not characterised in the D10 self-interference matrix.
  3.
    - **Name:** ST-LINK family (STLINK-V3MINIE, V2; V2 clones are counterfeit-prone)
    - **Why:** Hard incompatibility. OpenOCD's Debug-Adapter-Configuration page (fetched) lists multidrop SWD only for cmsis_dap v2.0, ftdi and bitbang drivers, not hla/st-link. RP2040 SWD is multidrop, so it cannot attach to the Pico supervisor or the RP2040-Zero. Price not fetched (moot).
  4.
    - **Name:** WCH-LinkE (WCH, DAP mode)
    - **Why:** Unproven on the critical spec. The wch-ic.com/wch.cn product pages and the LCSC search are JavaScript-only (fetched, no content), so CMSIS-DAP v2 / DAP_SWD_Sequence support for RP2040 multidrop, I/O protection, case and price are all unverified. It is also worse or different where it is known: closed firmware vs open debugprobe, no RPi 3-pin JST-SH harness, a different MCU and crystal (a new, uncharacterised spur family in the field pouch). Rejected under 'never trade away a spec silently'.
  5.
    - **Name:** Generic unbranded 'CMSIS-DAP'/'DAPLink' dongles (typically STM32F103)
    - **Why:** Firmware version unknown. v1 HID builds without DAP_SWD_Sequence cannot write TARGETSEL, so they cannot reach an RP2040. I/O protection and build unknown, unbranded supply (counterfeit risk), new spur family. No price or measurement verified.
  6.
    - **Name:** pico-debug (majbthrd, CMSIS-DAP on the target's own core 1)
    - **Why:** Intrusive. It takes the target's USB port, reserves SRAM, forces CLK_SYS from PLL_USB and debugs one core only. It has no separate UART, so it cannot be the Q6A console. Incompatible with the supervisor firmware's use of both cores and UART7.
  7.
    - **Name:** Q6A GPIO bitbang SWD (header pins 12/35/38 via UM3304, OpenOCD)
    - **Why:** Not an analog: it already exists and complements the probe. It reaches only the in-chassis Pico, not the IMU-pack RP2040-Zero, has no USB-UART for the Q6A's own console, and is unavailable when the Q6A is down. Its multidrop support is inferred from 'all bitbang based', not stated for linuxgpiod.
  8.
    - **Name:** Used Raspberry Pi Debug Probe (eBay/marketplaces)
    - **Why:** No verified listing or price (eBay.de returned HTTP 403). Unknown condition, cables possibly missing, no warranty. Unlikely to land below EUR 11.50 with shipping (model).
  9.
    - **Name:** Same SKU, TinyTronics NL (SKU 004911)
    - **Why:** Not cheaper on the base: EUR 11.98 ex VAT = $13.47 (> $12.00); EUR 14.50 incl. 21% NL VAT = $16.30. Not on the raspberrypi.com Approved Reseller list. Its only merit is that it rides on today's step-1 Q6A order with no added shipping (still cheaper landed than Adafruit with duty, about $16.30 vs about $18.3). Acceptable only if the UART console is needed at the Q6A's first boot before a reichelt/DigiKey parcel arrives.
  10.
    - **Name:** Same SKU, Botland PL
    - **Why:** EUR 10.97 net = $12.33 (> $12.00); EUR 13.05 gross. Not cheaper.
  11.
    - **Name:** Same SKU, Kiwi Electronics NL
    - **Why:** EUR 10.89 ex VAT = $12.24 per search 1 (not re-fetched: my URL guess returned 404). Not cheaper ex VAT.
  12.
    - **Name:** Same SKU, TME (sc0889)
    - **Why:** Price not real on the page: the visible page shows 'no-prices' and '0 in TME stock', while the structured data says $12 and 110 in stock. Unverified.
  13.
    - **Name:** Same SKU, Mouser DE
    - **Why:** HTTP 503; price and stock unverified.
  14.
    - **Name:** Same SKU, Pimoroni / The Pi Hut (UK)
    - **Why:** Non-EU: the flat EUR 3/item duty, EUR 2 UHF from ~1 Nov, import VAT and DHL Express (Pi Hut) apply on top of GBP 10.25 / 11.50 incl. UK VAT. Not cheaper landed than the EU sellers.
  15.
    - **Name:** Same SKU, BerryBase DE (RPIP-DEBUGP) and welectron DE (RP1-709260)
    - **Why:** Not rejected on specs (identical, approved resellers; BerryBase 96 in stock, welectron 100+). They cost more than reichelt: BerryBase EUR 12.20 incl. ($11.53 ex VAT), welectron EUR 11.90 incl. ($11.24 ex VAT). Shipping not verified. Use only if an order with them already exists.
- **Conditions or tests:** Condition for the seller change:
  - Buy at reichelt only on a reichelt cart that exists for other v2 parts. Today the P5 analog picks G1/G2/G3 create one; confirm it survives the P6 re-verification.
  - If there is no reichelt order, use DigiKey DE on the step-7 order. That order is probably below EUR 75 (encoders, switches and ferrites are about $20 per the BOM), so it pays EUR 25 shipping anyway. Prefer UPS/FedEx (DDP). DHL is CPT, so VAT and duty are due on delivery. DigiKey's page does not say how it handles the new EUR 3 duty or the UHF; check the cart total.
  - Never open a dedicated order for the probe alone (reichelt alone is $19.62).
  - Timing: place the reichelt/DigiKey order in week 1 so the probe arrives before the Pico supervisor bring-up. The Q6A first boot can use HDMI. If the UART console is needed at first boot, put it on the TinyTronics step-1 order instead (EUR 14.50).
  
  Acceptance on arrival, ~15 min:
  1. Check it is genuine: SC0889/EAN label, case, 3 cables + USB cable.
  2. lsusb shows 2e8a:000c 'Debug Probe (CMSIS-DAP)'.
  3. Flash debugprobe v2.3.1 UF2.
  4. On the Q6A (Ubuntu 24.04 arm64), run `openocd -f interface/cmsis-dap.cfg -f target/rp2040.cfg -c 'adapter speed 5000'`. It must attach both RP2040 cores (multidrop) on the Pico supervisor and on the IMU-pack RP2040-Zero, and program and verify one image on each.
  5. picocom 115200 on Q6A header pins 8/10: 10 min with zero framing errors.
  6. Confirm the probe is accessible without root: either 60-openocd.rules is installed, or the service user is in plugdev.
- **Stack changes:** Only sourcing and BOM text change. No rails, connectors, drivers, case or D10 spur matrix change, because it is the same device.
  1. BOM line 'Відлагоджувач': seller Adafruit -> reichelt (RPI DEBUG PROBE, MPN SC0889). Price $10.86 ex VAT / EUR 11.50 incl. 19% VAT, verified 18 Oct 2026. Fallback DigiKey DE 2648-SC0889-ND ($11.85 ex / EUR 12.54 incl.). Adafruit 5699 $12.00 only for a non-EU build.
  2. Bring-up step 2: remove the Debug Probe from the Adafruit launch order (BOM total -$12.00). This also removes that line's import VAT, the EUR 3 per-item duty and, from ~1 Nov, the EUR 2 UHF, if the order goes postal/IOSS. Add it to the reichelt cart (or the DigiKey step-7 order) in week 1.
  3. Production lifetime: 'until at least January 2030' (live product page). The Feb 2023 brief says 2028; use 2030.
  4. udev: upstream OpenOCD 0.12.0 60-openocd.rules already matches ATTRS{product}=="*CMSIS-DAP*", and the Debug Probe's product string is 'Debug Probe (CMSIS-DAP)'. The note to add a 2e8a:000c rule becomes 'verify the packaged rules file exists'. On the headless Q6A, add the labd/service user to plugdev, because uaccess applies only to a local seat. The UART stays cdc_acm /dev/ttyACM*, with labd /dev/lab naming keyed on 2e8a:000c plus the interface number.
  5. Bench note to keep: the Debug Probe build has no target-reset pin. The IMU-pack RP2040-Zero needs a manual reset or its RUN pad wired. In-system, RUN stays on Q6A pin 38.
  6. Optional spare: a Pico flashed with debugprobe_on_pico may be kept as an emergency probe, but it is not the BOM part and should not be used in the field pouch without a case.
  
  Method limits:
  - The shared WebSearch budget was already exhausted, so I ran no web search and found no forum measurements. Everything comes from WebFetch/curl of primary pages, plus the locally downloaded schematic and product brief.
  - TinyTronics pages work via WebFetch but curl gets 403. Mouser returned 503. WCH and LCSC are JavaScript-only.
- **Confidence:** high
- **Sources:**
  - https://www.reichelt.com/de/en/shop/product/raspberry_pi_debug_probe-343288
  - https://www.reichelt.com/de/en/shop/service/-12_28
  - https://www.digikey.de/en/products/result?keywords=SC0889
  - https://www.digikey.de/en/help-support/delivery-information
  - https://www.berrybase.de/raspberry-pi-debug-probe
  - https://www.welectron.com/Raspberry-Pi-Debug-Probe_1
  - https://botland.store/rp2040-microcontroller-boards/22625-raspberry-pi-debug-probe-usb-debugger-for-raspberry-pi-pico-5056561803265.html
  - https://www.tinytronics.nl/en/development-boards/microcontroller-boards/raspberry-pi-pico/raspberry-pi-debug-probe
  - https://www.tinytronics.nl/en/delivery-information
  - https://www.tme.eu/en/details/sc0889/raspberry-pi-acessories/raspberry-pi/debug-probe/
  - https://www.raspberrypi.com/resellers/
  - https://www.raspberrypi.com/products/debug-probe/
  - https://datasheets.raspberrypi.com/debug/raspberry-pi-debug-probe-product-brief.pdf
  - https://datasheets.raspberrypi.com/debug/raspberry-pi-debug-probe-schematics.pdf
  - https://raw.githubusercontent.com/raspberrypi/debugprobe/master/include/board_debug_probe_config.h
  - https://raw.githubusercontent.com/raspberrypi/debugprobe/master/include/board_pico_config.h
  - https://raw.githubusercontent.com/raspberrypi/debugprobe/master/src/usb_descriptors.c
  - https://openocd.org/doc/html/Debug-Adapter-Configuration.html
  - https://github.com/openocd-org/openocd/blob/master/src/jtag/drivers/cmsis_dap.c
  - https://raw.githubusercontent.com/openocd-org/openocd/v0.12.0/contrib/60-openocd.rules
  - https://www.adafruit.com/product/5699
  - https://www.wch-ic.com/products/WCH-Link.html
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/analogs_G2_display_hmi_storage.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/analogs_G3_power_gnss_imu.json
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md

