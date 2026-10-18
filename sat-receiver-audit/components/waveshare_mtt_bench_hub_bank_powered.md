# Waveshare mtt bench hub bank powered: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** Bench USB 2.0 hub behind the handheld's LAB USB-A port, powered from the Anker 737 bank (tier bench, group Bench electronics, qty 1)
- **Current pick:** Waveshare USB-HUB-2IN-4OUT "Industrial Grade Dual-Host USB Hub (4x USB 2.0)" from The Pi Hut, SKU WAV-21686, with a UK 3-pin 5V 2A PSU. STACK.md wrongly calls it the "Waveshare MTT bench hub"; Waveshare's own page says STT.
- **Current price usd:** 24.64 = GBP 18.50 incl. 20% UK VAT. Re-checked live from the Pi Hut Shopify .json/.js on 18 Oct 2026: variant WAV-21686, price 18.50, available=true. Without UK VAT it is GBP 15.42 = $20.54. For an EU buyer the Pi Hut ships by DHL Express only (GBP 30) and adds EU VAT plus the per-item duty and fee (operator notes 34/35).
- **Decision:** replace_conditionally
- **Chosen:** Waveshare USB-HUB-2IN-4OUT-NP (Waveshare SKU 23062, power-plug option "Without Power Supply"), bought direct from waveshare.com. It is the same product as the current pick. Add it to the Waveshare order already planned in shopping step 7 (LC76G, RP2040-Zero, L1+L5 antenna) so it shares that shipment's shipping and customs clearance. If a mains fallback is wanted in Europe, SKU 21605 (EU-plug PSU) at $16.99 is the same hardware.
- **Chosen price usd:** 14.99 for qty 1 ($14.59 at qty 2), before tax and shipping. Checked live 18 Oct 2026 from the page HTML: the price for sku=23062 is $14.99 and the SKU map shows it orderable (unsaleable:false). Stock count is not shown. Waveshare does not collect EU VAT (no IOSS) and quotes shipping by hand per order; duties are the buyer's responsibility. Estimated EU landed cost for this line: $14.99 x 1.21 VAT (example rate) = $18.14, plus EUR 3 duty (about $3.37) if it comes by post/IOSS, plus the EUR 2 handling fee (about $2.25) from about 1 Nov 2026 = about $23.8. Extra shipping when added to the step-7 order is small (0.147 kg) but not quoted.
- **Saving usd:** 9.65 against the stack line ($24.64 - $14.99). Note the stack line includes UK VAT and the new price excludes tax. Like-for-like before VAT: 5.55 ($20.54 - $14.99). Estimated EU landed (21% VAT, same EUR 3 + EUR 2 per item on both): about 6.7 ($30.5 vs $23.8). Add about $40 more if the Pi Hut parcel would otherwise go by DHL Express (GBP 30) just for this line.
- **Equivalence proof:** The hardware is the same; only the accessory option differs.
  (1) One Waveshare product page, one product. The SKU map in the page source is {"US":"21380","EU":"21605","Without Power Supply":"23062"}, so the SKUs differ only in the "Power Plug" attribute. The package list on the page reads "USB-HUB-2IN-4OUT x1, USB-A to USB-C cable ~1m x2, OPTIONS 5V 2A power adapter x1". Only the adapter is optional, so the NP SKU still includes the hub and both cables.
  (2) The Pi Hut's WAV-21686 is listed with vendor Waveshare. Its body text gives the same spec block: USB 2.0 HS 480 Mb/s; 5V@1.2A per USB-A output; hub input through dual switchable USB-C; external DC 5V through DC jack or USB-C; -40 to 85 C. Box: hub + 2x 1 m USB-A to USB-C + UK 3-pin 5V 2A PSU.
  Spec by spec, every item is equal:
  - 4x USB-A downstream.
  - USB 2.0 High-Speed upstream.
  - 1.2 A per port with a short-circuit cut-off that latches (wiki: unplug to restore).
  - OVP, OCP, short-circuit, OTP, reverse-current and UVLO protection, plus filtering.
  - 8 kV ESD on every port.
  - -40 to +85 C (no condensation).
  - Metal case with flanges, 86 x 47.8 x 27.6 mm (Waveshare dimension drawing). 0.147 kg without the PSU.
  - Same connectors: DC 5V jack, IN1/IN2 USB-C, host switch.
  - Standard hub class, no driver needed (Waveshare lists Linux 2.4.20+), so it works on Ubuntu 24.04 arm64.
  - Same hub tier count.
  - Same TT type: STT on Waveshare's page (stated twice, MTT never). STT is accepted by the re-audit because no bench instrument is a full-speed isochronous device; the Hantek and FX2 LA are high-speed and do not use the TT.
  Genuineness: bought from the manufacturer, so there is no counterfeit risk. Seller status is no worse than now: the Pi Hut is a UK (non-EU) seller too, so neither purchase gets EU-seller VAT or returns handling.
  Nothing is traded away. The UK 3-pin PSU that is left out cannot be used in Europe, and the stack powers the hub from the bank in any case.
  Conditions:
  (a) Buy it inside the step-7 Waveshare order. Waveshare quotes shipping by hand, so a standalone parcel could cost more than the saving.
  (b) On arrival check the 2 cables are in the box. If not, use any USB-A to USB-C data cable.
  (c) Same arrival tests as for the current pick: lsusb -v bDeviceProtocol (1 = STT, 2 = MTT); lsusb -t showing one tier; FNB58 on the LAB port under 50 mA with the bank on the DC jack and 0 mA reverse current. Also confirm the hub stops drawing from IN1 VBUS when the DC jack is powered: "DC jack/USB-C power input" means either can power it.
  (d) Check that a 1.2 A per-port overload trips and latches.
- **Rejected:**
  1.
    - **Name:** Waveshare USB-HUB-2IN-4OUT-EU, SKU 21605 (waveshare.com)
    - **Why:** Not worse, and the hardware is identical, but it costs $16.99 (verified live), $2 more than SKU 23062. The only extra is an EU-plug 5V 2A PSU that the bank-powered stack does not need. It is the acceptable alternative if a mains fallback is wanted.
  2.
    - **Name:** Waveshare USB-HUB-7U-NP, SKU 23063 ($18.99 list; range $18.99-23.99 verified on the page)
    - **Why:** Better on one spec: Waveshare's page says MTT. But it is $4 dearer than SKU 23062 and has not been proven not-worse. It needs a USB-B upstream (1.2 m cable included), is a bigger box (weight from the search pass, not re-verified), and Waveshare recommends a supply above 4A for high loads. Its internal topology is not published, so a cascaded 2-chip design would break the 'no extra hub tier' rule. It is not the cheapest not-worse option.
  3.
    - **Name:** Waveshare USB-HUB-4U-NP, SKU 23061 (page range $14.99-16.99; NP price inferred, not fetched separately)
    - **Why:** Same STT chip class, protections and 1.2 A per port, but it is no cheaper than SKU 23062. Its upstream is USB-B with a different cable, and it has a single host. It has no advantage, so there is no reason to switch.
  4.
    - **Name:** BerryBase 'Waveshare Industrieller USB 2.0 Hub: 4-Port, Mehrfachschutz, ohne Netzteil', EUR 18.60 incl. MwSt (EU stock, DE)
    - **Why:** Not available ('Artikel aktuell nicht lieferbar', 18 Oct 2026). The model is probably the USB-HUB-4U-NP but is not confirmed. At about $20.91 incl. VAT plus DE shipping, it is no clear landed saving. Re-check it only as an EU-stock fallback.
  5.
    - **Name:** Olimex USB-NeoHub (CH334S), EUR 8.00 at olimex.com / GBP 6.00 at The Pi Hut
    - **Why:** MTT is better, but it is worse on the power path. The Rev A schematic (local copy hub_dl/neohub_sch.pdf) shows +5V_USB 'connected to USB port VBUS', with no separate 5 V input. One ganged CH217K switch (Ilim about 1.99 A) covers all 4 ports instead of 1.2 A per port. It has no OVP/UVLO, no per-port ESD parts, and is a bare PCB. Bank power would have to back-feed the LAB port, which breaks the under-50-mA / 0-reverse-current rule.
  6.
    - **Name:** Raspberry Pi USB 3 Hub SC1636 (GBP 11.50 Pi Hut, $12 list)
    - **Why:** The product brief (Nov 2024) gives no per-port OCP, no ESD rating, no temperature range and no back-power isolation for its USB-C input. Its warnings say 'indoor use only', 'avoid temperature extremes' and 'avoid dropping'. It has a plastic case and a captive 8 cm cable. That is worse on build and ruggedness for the Pelican travel case, and it is unproven on the power-path rule.
  7.
    - **Name:** Waveshare USB HUB HAT (B), SKU 20317 ($6.99; EUR 6.58 Botland)
    - **Why:** Bus-powered HAT PCB weighing 0.024 kg. There is no external 5 V input, no metal case, and no published per-port limit, OVP, reverse-current, ESD or temperature rating. It breaks the bank-powered rule.
  8.
    - **Name:** 8086 Consultancy Mini 4-Port USB-C USB 2.0 Hub (CH334), GBP 4.00 Pi Hut
    - **Why:** The downstream ports are USB-C only, so the instruments' USB-A cables do not fit. It is powered from upstream through a 1 A polyfuse, with 500 mA legacy per port, no per-port OCP/OVP/ESD and no case. It breaks the power-path rule.
  9.
    - **Name:** DIY CH334F + 4x TPS2553 + ESD + box
    - **Why:** Not cheaper than $14.99 once 4 limiters, receptacles, ESD arrays, an input and an enclosure are counted. Quality depends on the build, there are no measurements, and it takes labour.
  10.
    - **Name:** Used Waveshare 2IN-4OUT / 4U
    - **Why:** No verified listing or price; condition (latch, ESD damage) unknown.
- **Confidence:** high
- **Conditions or tests:** 1. Order SKU 23062 inside the step-7 Waveshare consignment (week 1-2), not as its own parcel. Ask Waveshare for the shipping quote with the hub included before paying. Before ordering, re-check the EUR 3 per-item duty (IOSS/postal) and the EUR 2 handling fee start date.
  2. On arrival:
  - Check the 2x USB-A to USB-C cables are in the box.
  - lsusb -v: bDeviceProtocol (expect 1 = STT).
  - lsusb -t: the bench hub adds exactly one tier (root -> FE1.1s -> CH334F -> bench hub).
  - With the bank feeding the DC 5V jack, FNB58 on the LAB port must read under 50 mA, and 0 mA reverse current with the host side unpowered (VBUS about 0 V on the AN8008).
  - Confirm the hub does not keep drawing from IN1 VBUS when the DC jack is powered.
  - A 1.2 A per-port overload must trip and latch.
  - Never charge the LiteVNA and tinySA at the same time through it.
  3. If Waveshare's standalone shipping quote would erase the saving, keep the Pi Hut purchase only if it shares a Pi Hut parcel with other lines; otherwise take the Waveshare unit.
- **Stack changes:** - STACK.md line 354: replace with "Bench hub | Waveshare USB-HUB-2IN-4OUT-NP (SKU 23062), STT per Waveshare, powered from the bank through the DC 5V jack | 1 | 14.99 | Waveshare direct | verified 18 Oct 2026 | Behind the LAB port. Alt: SKU 21605 with EU PSU $16.99".
  - Rename "MTT bench hub"/"MTT-хаб" to "bench hub (STT)" at lines 616, 903, 1125 and 1146, and wherever the reaudit/radio_lab text says MTT for it. The internal Adafruit CH334F stays MTT.
  - Shopping plan: move the hub from step 8/9 (Pi Hut, week 2-3) into the step-7 Waveshare order. If the Pro Stick Plus is also moved to an EU seller, the Pi Hut order and its GBP 30 DHL Express go away.
  - Power, new BOM line: a 5 V lead from the Anker 737 (USB-A or USB-C) to the hub's DC 5V barrel jack. The barrel size is not stated on Waveshare's page (likely 5.5x2.1; confirm on arrival). This lead was needed in Europe anyway, because the Pi Hut unit's UK 3-pin PSU cannot be used. It costs a few dollars; price not verified.
  - Quiet mode note: the bench instruments are bank-powered, so turning off LAB VBUS (TPS2553) does not power them down. Quiet mode must unplug the bank lead or the instruments.
  - No change to rails, drivers (in-kernel hub class), USB tier count, connectors (USB-C upstream with the included A-to-C cable into the LAB USB-A port), or case space: 86 x 47.8 x 27.6 mm, 0.147 kg, lighter than the PSU-bundled unit.
  - Limits of this pass:
    - The shared WebSearch budget was used up before I ran any search, so all checks came from direct fetches of the pages listed in sources.
    - Not checked (blocked, 403/503): Waveshare's official AliExpress store, Amazon.de, DigiKey, TinyTronics, Kamami, Conrad.
    - No EU stockist of the 2IN-4OUT was found at Botland, Kiwi, BerryBase, Welectron, Eckstein or Mouser.
- **Sources:**
  - https://www.waveshare.com/usb-hub-2in-4out.htm
  - https://www.waveshare.com/usb-hub-2in-4out.htm?sku=23062
  - https://www.waveshare.com/usb-hub-2in-4out.htm?sku=21605
  - https://www.waveshare.com/img/devkit/accBoard/USB-HUB-2IN-4OUT/USB-HUB-2IN-4OUT-details-size.jpg
  - https://www.waveshare.com/wiki/USB-HUB-2IN-4OUT
  - https://www.waveshare.com/shipping
  - https://thepihut.com/products/industrial-grade-dual-host-usb-hub-4x-usb-2-0.json
  - https://www.waveshare.com/usb-hub-7u.htm
  - https://www.waveshare.com/usb-hub-4u.htm
  - https://www.berrybase.de/search?search=waveshare+usb+hub
  - https://botland.store/search?s=waveshare+usb+hub
  - https://www.olimex.com/Products/Retro-Computers/Neo6502/USB-NeoHub/
  - https://github.com/OLIMEX/USB-NeoHub/blob/main/HARDWARE/USB-NeoHub-Rev.A/USB-NeoHUB_Rev_A.pdf
  - https://datasheets.raspberrypi.com/usb-3-hub/usb-3-hub-product-brief.pdf
  - https://thepihut.com/products/raspberry-pi-usb-3-hub
  - https://thepihut.com/products/mini-4-port-usb-c-usb-2-0-hub
  - https://www.waveshare.com/usb-hub-hat-b.htm
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (items 34-35, EU duty and handling fee)
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md (lines 354, 616, 903, 1124-1125, 1146)

