# Waveshare lc76g 24370 rtc cr2032 cell: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** GNSS + RTC: Waveshare LC76G Multi-GNSS Module (SKU 24370, Quectel LC76G(AB), AG3352) + pre-wired CR2032 RTC cell for Q6A J11 (core tier, group GNSS, qty 1)
- **Current pick:** Waveshare 24370 LC76G ($14.99) + ALLNET China "RTC Battery for RADXA SBC" ($0.95)
- **Current price usd:** 15.94 (14.99 + 0.95; both prices exclude VAT and shipping). Re-checked 18 Oct 2026: Waveshare shows $14.99 at qty 1. The ALLNET Shopify JSON shows $0.95, available=true, SKU 158782, 5 g. Waveshare quotes express shipping by hand (DHL/FedEx/UPS), and the buyer pays all EU import VAT, duties and fees.
- **Decision:** keep
- **Chosen:** Keep the Waveshare LC76G 24370 and the pre-wired CR2032 RTC cell. No cheaper analog survives. The only real option is a seller change for the same SKU: Botland (EU). It is not an analog and depends on conditions (see conditions_or_tests).
- **Chosen price usd:** 15.94 (unchanged)
- **Saving usd:** 0 on the part. Optional EU sourcing saving, same SKU: Botland's VAT-inclusive price ($16.95) is about $0.89-1.79 below Waveshare-direct plus import VAT ($17.84-18.74 at 19-25 % VAT, my calculation). Botland also avoids the new EU flat customs duty and the carrier fee. That holds only if the board ships with other Botland items. Bought alone, Botland charges shipping from EUR 4.69 ($5.27), which cancels the saving.
- **Equivalence proof:** Reference specs of the current part (verified): Waveshare page, 18 Oct 2026: GPS/BDS/GLONASS/Galileo/QZSS, SBAS supported, sensitivity -147 dBm acquisition / -159 dBm reacquisition / -166 dBm tracking, 1.5 m CEP, 10 Hz, UART 9600-921600, timing 30 ns, onboard MS621FE rechargeable backup, 3.3/5 V VCC, active ceramic antenna included, $14.99. Quectel LC76G spec V1.1 and protocol spec V1.4, re-checked in reaudit D: 47 channels, EGNOS, jamming status (PAIRSPF / PQTMJAMMINGSTATUS / JAM_IND), PQTMCFGPPS + PQTMSAVEPAR to NVM. Every cheaper candidate fails at least one of these, checked on primary pages. (1) Waveshare L76K ($12.99): Waveshare's own table lists GPS/GLONASS/BDS/QZSS with no Galileo, SBAS "N/A", tracking -162 dBm, CEP 2.0 m, 32 channels, 5 Hz, UART max 115200, and the CASIC command set (no PQTMSAVEPAR or PAIRSPF). (2) M5Stack U190 Unit GPS SMA ($12.50, available): tracking -162 dBm; the HY2.0-4P connector carries only GND/5V/RX/TX, so there is NO PPS; no backup cell listed; 40.9 mA. (3) M5Stack Module GPS v2.1 ($13.95, available): has PPS, but tracking is -162 dBm and the backup is a 20,000 uF supercap. Model: 0.02 F x about 1.8 V divided by 10-30 uA gives about 20-60 min of hold, against days for the MS621FE. Board is 54x63.6x13.1 mm. (4) Seeed Grove Air530 ($11.99 is the 10+ price): the wiki documents no PPS, 60 mA, and no published sensitivity. (5) ATGM336H-5N31/5N11/5NR32: no Galileo, CEP 2.5 m, 32 s TTFF; the 5NR32 is 5 Hz. (6) ATGM336H-6N-74 / AT6668 generics: -162 dBm tracking, no documented jamming status or NVM save, prices unverified. Same part from another seller: the Botland listing has the same SKU (WSR-23562; EAN 5904422385798 is Botland's own) and the same contents (LC76G board, attached active ceramic antenna, 8-pin MX1.25 cable). So every spec is identical by identity, not an analog. RTC cell: no cheaper verified pre-wired 1.25 mm cell exists. Electrokit ($3.23) and Hardkernel ($2.50) cost more. AliExpress no-name cells have no capacity evidence.
- **Rejected:**
  1.
    - **Name:** Same SKU Waveshare 24370 at Botland (botland.de EUR 15.08 incl. VAT = $16.95, net $14.24; botland.com.pl PLN 65.90 incl. VAT = $16.96, net $13.79)
    - **Why:** Not rejected on specs: it is the identical part, so it cannot be an analog. Kept as a conditional EU sourcing option. Price verified from structured data (DE: InStock, price 15.08 EUR; PL: 65.90 PLN, valid to 2026-11-02). Stock is NOT confirmed: the status loads by JS ('loading'), and the static page holds both the 'Auf Lager' and the 'nicht auf Lager, Lieferung unterwegs' templates. Shipping: DE from EUR 4.69 (free from EUR 100); PL from PLN 8.99. botland.store is B2B only.
  2.
    - **Name:** Waveshare L76K Multi-GNSS (SKU 23721, AT6558R), $12.99
    - **Why:** Worse per Waveshare's own comparison table: no Galileo, SBAS N/A (no EGNOS), tracking -162 vs -166 dBm, CEP 2.0 vs 1.5 m, 32 vs 47 channels, 5 vs 10 Hz, UART max 115200. CASIC command set, so no PQTMCFGPPS/PQTMSAVEPAR/PAIRSPF; jamming status not documented.
  3.
    - **Name:** M5Stack U190 Unit GPS SMA / GPS-BDS Unit (AT6668), $12.50
    - **Why:** No PPS: HY2.0-4P is GND/5V/RX/TX only (M5Stack docs), which breaks the pin-7 pps-gpio/chrony path. Tracking -162 dBm. No backup cell listed. 40.9 mA operating. No documented jamming status or NVM config save. Ships from CN, so EU VAT and duty come on top.
  4.
    - **Name:** M5Stack Module GPS v2.1 (M003-V21, AT6668), $13.95
    - **Why:** Tracking -162 dBm (4 dB worse). Backup is a 20,000 uF/3.3 V supercap: about 20-60 min hold (model) vs about 1-2.5 weeks for the MS621FE, so cold starts after storage. 54x63.6x13.1 mm M-Bus stacking board (handheld fit). PPS accuracy, EGNOS, jamming status and flash save not documented.
  5.
    - **Name:** Seeed Grove GPS (Air530), $11.99 (10+ price; qty-1 price unverified)
    - **Why:** No PPS documented on the 4-wire Grove lead. Up to 60 mA. Sensitivity, backup, jamming status, NVM save and antenna type are unpublished, so it cannot be shown not-worse.
  6.
    - **Name:** DIY carrier around a bare Quectel LC76GABMD (Comet BG $5.20 ex VAT, more than 25 in Sofia)
    - **Why:** Same silicon, but the board-level result is unproven: antenna-bias filtering, ground, LDO noise and backup charging are all hand layout and hand assembly, with no CE or factory test, which fails the build-quality rule. Comet lists 'LC76GAB (R12A02)', an older firmware than the A04S seen on Quectel's forum (A04S moved EASY to EPOC). Updating it needs login-gated Windows QGNSS. Comet's 16x16x6.95 mm dimensions contradict Quectel's 10.1x9.7x2.4 mm, so the listing data is unreliable. Loses the included active antenna. After PCB, MS621FE, LDO, IPEX/MX1.25, shipping and VAT, the saving is about $0-6 at best (model).
  7.
    - **Name:** Generic ATGM336H-6N-74 / AT6668 breakouts (AliExpress)
    - **Why:** Tracking -162 dBm. No documented jamming-status output for the labd gate, no NVM save, no PPS accuracy figure. Mislabelling is common. Board prices unverified.
  8.
    - **Name:** ATGM336H-5N31 / 5N11 / 5NR32 (AT6558) breakouts
    - **Why:** No Galileo (5N31 GPS+BDS; 5N11 GPS only), CEP 2.5 m, 32 s TTFF, -162 dBm tracking; the 5NR32 is 5 Hz max (Peter Tanner table; datasheet values, not measurements).
  9.
    - **Name:** Cheap drone 'M10' boards (UBX-M10050 on third-party PCBs)
    - **Why:** These usually lack a PPS pad and an IPEX/u.FL port, and the M10 has no flash. High clone/fake risk. No verified listing or price.
  10.
    - **Name:** 'NEO-6M/NEO-M8N'-labelled generic breakouts
    - **Why:** Counterfeit or relabelled silicon (AT6558 found under u-blox labels) fails the legality rule. A genuine NEO-6M is GPS-only.
  11.
    - **Name:** DFRobot TEL0157 ($17.90)
    - **Why:** Dearer than $14.99 and reported without Galileo (angle A; not re-fetched by me).
  12.
    - **Name:** Uputronics MAX-M10S 3V (GBP 28.79, about $38.34)
    - **Why:** Dearer, and no flash (config in supercap-backed BBR needs UART6 TX at every boot). Stays the optional spoof-flag build per reaudit D.
  13.
    - **Name:** Eckstein DE (EUR 18.94) / OpenCircuit NL (EUR 22.75), same SKU
    - **Why:** Same part at a higher price (figures from angle A; not re-fetched by me).
  14.
    - **Name:** RTC: Electrokit 'CR2032 with cable - 3V 210mAh' (SEK 32 incl. 25 % VAT = $3.23; 182 in stock; 1.25 mm 2-pin; 50 mm lead)
    - **Why:** Better documented (Li-MnO2, 210 mAh) but 3.4x the price, so not a cheaper analog. Polarity not stated. Kept as the EU fallback source (see conditions).
  15.
    - **Name:** RTC: Hardkernel RTC Backup Battery ($2.50) / Ameridroid wired CR2032 ($7.95)
    - **Why:** Dearer; non-EU shipping (not re-fetched by me).
  16.
    - **Name:** RTC: AliExpress no-name CR2032 with MX1.25 lead (about $0.3-0.6, unverified)
    - **Why:** No brand, capacity or self-discharge evidence, and the price is unverified. A weak cell matters because rtc-ds1307 (m41t11) has no oscillator-fail check, so a brown-out could give a plausible but wrong hctosys time.
- **Conditions or tests:** EU SOURCING (optional, same part): buy the 24370 from Botland (botland.de or botland.com.pl; not botland.store, which is B2B) only if (a) checkout confirms stock (the static page does not), and (b) it ships with other Botland items. In Germany the order then reaches the EUR 100 free-shipping threshold, or it shares the parcel. Otherwise keep it in the Waveshare order, which exists anyway for the RP2040-Zero and the 25346 antenna. Waveshare-direct landed cost is $14.99 + 19-25 % import VAT + a share of express shipping + the post-1-July-2026 EU flat customs duty (amount not verified here, per operator note 34) + the carrier fee. On arrival from either seller: check the Waveshare silkscreen and the Quectel LC76G label, and log the $PQTMVERNO*58 firmware string. RTC CELL: the $0.95 ALLNET price is real (Shopify available=true), but in the EU shopping plan the Q6A comes from TinyTronics, so no ALLNET order exists to carry the cell. Ordered alone from China, its shipping would exceed its price. If no ALLNET order is placed, buy Electrokit SKU 41036512 (SEK 32 incl. VAT = $3.23). The ALLNET listing gives no cell type or capacity: the photos show a shrink-wrapped coin cell with a white 2-pin plug, and Radxa's 2P RTC doc says 'CR2032, 2-Pin XH1.25mm'. Before plugging any cell into J11: read the cell marking (CR2032); measure open-circuit voltage (3.0 V or more); check plug polarity with a DMM against J11 on Radxa schematic v1.21 PDF p.16 (Radxa warns about polarity; Electrokit does not state it); check that the 50 mm Electrokit lead reaches the case mounting spot. The existing reaudit-D bench tests stay as they are: 5 V VCC feed, IPEX bias of 3.05 V or more under 150 ohm, PQTMCFGPPS + PQTMSAVEPAR persistence after draining the backup, PPS stops without a 3D fix, TTFF and MS621FE hold time, RTC drift. LIMITS OF THIS CHECK: the shared WebSearch budget ran out after my first search. So no new candidates could be searched (for example the Waveshare AliExpress store price or other EU stockists such as TinyTronics or DigiKey). All verification above used direct fetches of primary pages and the Shopify JSON.
- **Stack changes:** None to rails, connectors, drivers, case or software: same board, same 5 V feed, UART6 (pins 16/18), PPS on pin 7, IPEX to SMA-K pigtail to P7, gpsd/chrony config as in reaudit D. BOM and shopping-order text only: (1) GNSS row: add the EU alternative source 'Botland DE/PL, same SKU WSR-23562, EUR 15.08 / PLN 65.90 incl. VAT, stock to confirm at checkout; use only when it ships with other Botland items'. (2) RTC row: change 'CR2032 cell' to 'pre-wired coin cell, CR2032 per Radxa 2P RTC doc (ALLNET listing states no type or capacity)'. Add the EU fallback 'Electrokit 41036512, CR2032 210 mAh, 1.25 mm 2-pin, 50 mm lead, SEK 32 incl. VAT ($3.23)' for EU orders with no ALLNET shipment. Add the J11 polarity DMM check. (3) Shopping order line 1: the EU TinyTronics path has no RTC cell. Put it on the Electrokit or another EU order, or on an ALLNET order if one is placed. (4) Keep 'Budget alternative: Uputronics MAX-M10S' worded as an optional spoof-flag add-on (more expensive), not a budget option.
- **Confidence:** high
- **Sources:**
  - https://www.waveshare.com/lc76g-gnss-module.htm
  - https://www.waveshare.com/l76k-gps-module.htm
  - https://www.waveshare.com/shipping
  - https://quectel.com/content/uploads/2024/03/Quectel_LC76G_Series_GNSS_Specification_V1.1-1-1.pdf
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json (gnss_imu_location entry)
  - https://botland.de/gps-module/23562-multi-gnss-ortungsmodul-lc76g-gps-beidou-bds-glonass-galileo-qzss-waveshare-24370-5904422385798.html
  - https://botland.com.pl/moduly-gps/23562-modul-pozycjonowania-multi-gnss-lc76g-gps-beidou-bds-glonass-galileo-qzss-waveshare-24370-5904422385798.html
  - https://docs.m5stack.com/en/unit/Unit_GPS_SMA
  - https://shop.m5stack.com/products/gps-bds-unit-with-sma-antenna-at6668 (Shopify .json/.js: $12.50, available)
  - https://shop.m5stack.com/products/gps-module-v2-1-with-antenna-atgm336h (Shopify .json/.js: $13.95, available, 20000 uF supercap)
  - https://www.seeedstudio.com/Grove-GPS-Air530-p-4584.html
  - https://wiki.seeedstudio.com/Grove-GPS-Air530/
  - https://store.comet.bg/en/Catalogue/Product/41774
  - https://git.petertanner.dev/peter/peter-tanner.github.io/src/commit/e3bb886a8b99f673dd6a5a4095fc5133654d4ac7/_posts/2024-11-25-Chinese-ZHONGKEWEI-ATGM-GNSS-modules-comparison.md
  - https://shop.allnetchina.cn/products/rtc-battery-for-radxa-sbc (Shopify .json: $0.95, available)
  - https://docs.radxa.com/en/accessories/battery/2p-rtc-bat
  - https://www.electrokit.com/en/cr2032-med-kabel-3.0v-180mah
  - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (note 34, EU flat duty)

