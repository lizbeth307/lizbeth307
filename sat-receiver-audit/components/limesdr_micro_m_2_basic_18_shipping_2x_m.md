# Limesdr micro m 2 basic 18 shipping 2x m: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_0cedef2b-2a3`_

- **Part:** LimeSDR Micro M.2 2280 Basic + $18 shipping + MHF4L-SMA(f) bulkhead cables (2 in BOM v1; reaudit_B requires 4)
- **Current pick:** LimeSDR Micro M.2 2280 Basic (LMS7002M + NXP LA9310, 1T2R, PCIe Gen3 x1, 3x MHF4) from Crowd Supply, plus 2x Crowd Supply 'MHF4L to SMA(f) Bulkhead Coax Cable' (Taoglas Coaxial Cables project, $6 each)
- **Current price usd:** 279 = 249 + 18 worldwide shipping + 2 x 6 (re-verified on crowdsupply.com, 18 Oct 2026: Basic $249 pre-order, 'Orders placed now ship Dec 15, 2026'; cable $6, in stock). With the 4 cables reaudit_B requires: 291. Both figures exclude EU import VAT, duty above EUR 150, the EUR 2 UHF (from about 1 Nov 2026) and the courier fee. If Crowd Supply charges the cable project's own '$18 Worldwide' fee separately, the totals are 297 and 309 (unverified).
- **Decision:** replace_conditionally
- **Chosen:** KEEP the LimeSDR Micro M.2 2280 Basic board from Crowd Supply; no cheaper board survived. The replacement applies only to the cable line: buy the MHF4L-SMA(f) cables as Taoglas CAB.01075 from DigiKey DE (931-CAB.01075-ND), 4 pieces per reaudit_B, added to the existing DigiKey order. Remove the cables from the Crowd Supply cart so that order holds the board only.
- **Chosen price usd:** 276.18 for the v1 line with 2 cables (249 + 18 + 2 x 4.59). With 4 cables: 285.36 (249 + 18 + 4 x 4.59). DigiKey US is $4.59 at qty 1, 1,010 in stock, Active. DigiKey DE is EUR 4.03 ex VAT (EUR 4.80 with 19% VAT), DDP by UPS/FedEx, free delivery to DE on orders of EUR 75 or more, otherwise EUR 25.
- **Saving usd:** 2.82 on the v1 line (2 cables); 5.64 with the 4 cables reaudit_B specifies. If Crowd Supply bills the Taoglas cable project's $18 worldwide shipping separately (unverified), the saving is 20.82 or 23.64, and one non-EU import declaration (VAT, UHF, courier fee) is avoided. The saving is lost if the DigiKey DE order is under EUR 75, because of the EUR 25 delivery charge. Board saving: 0.
- **Equivalence proof:** CABLES (same maker and same published spec): Crowd Supply sells its cable through the Taoglas 'Coaxial Cables' project (crowdsupply.com/taoglas/coaxial-cables). It is described as an 'I-PEX MHF-4L plug (also compatible with Murata HSC) to a female SMA bulkhead connector, 100 mm long, made of 1.13 mm black coax'. Taoglas names CAB.01075 'I-PEX MHF4L(HSC Comp) to 100mm 1.13mm Coax Black Cable SMA(F) Bulkhead Straight'; this title comes from the URL and a search snippet, since the page returned 403. DigiKey lists CAB.01075 as 'Cable Assembly Coaxial I-PEX MHF4L to SMA 1.13mm OD', with a right-angle MHF4L plug, an SMA jack bulkhead with front-side nut, 100 mm, Active. Maker, connector pair, HSC compatibility note, coax OD and colour, and length all match, so insertion loss, mating with the Lime's '3x MHF4' receptacles, and bulkhead fit are identical. Neither listing publishes a frequency rating, so that point is equal-unknown (unverified for both). Whether Crowd Supply's item is exactly part number CAB.01075 is inferred, not confirmed; every published spec is equal.
  
  BOARD (why nothing replaces it): the Lime is the only option at or under $279 that meets every gate. It tunes 30 MHz-3.8 GHz with matched LNAL 0.3-2.2, LNAW 0.7-2.6 and LNAH 3.3-3.8 GHz. It offers 100 MHz half-duplex and 50 MHz FDD bandwidth, 61.44 Msps FDD, a 12-bit LMS7002M, two RX channels on one LO, PCIe Gen3 x1 M.2 2280, about 4 W, and register-level TX block (Crowd Supply page plus reaudit_B). Every cheaper candidate fails at least one hard spec: bandwidth, coverage, channel count, throughput, matched inputs or real availability. Every candidate that meets the specs costs more: bladeRF xA4 $540, XTRX $960, B206mini-i $1,599. Same part elsewhere: Lime's store shows a $10,000 sold-out placeholder, and Mouser has no LimeSDR Micro listing. Mouser lists Lime items as CS-LIME-xx at about 2x the Crowd Supply price (XTRX CS-LIME-29 $1,991.27 against $960), so no cheaper seller exists. Caveat kept, not traded: the Micro's NF/IIP3 advantage is chip-level and vendor-sourced (LMS7002M datasheet and Lime measurement report v1.05), and no board-level measurement exists.
- **Rejected:**
  1.
    - **Name:** Crowd Supply 'MHF4L to SMA(f) Bulkhead Coax Cable' (current cable source, Taoglas project)
    - **Why:** Same part and spec as CAB.01075, but $6 against $4.59 each. It is sold by a separate Crowd Supply project ('$8 US / $18 Worldwide' listed on it) and is in stock while the board is a pre-order, so a separate shipment, fee and import declaration are possible (unverified). Crowd Supply's guide says fees rise with item count and gives no combining rule.
  2.
    - **Name:** LimeSDR Micro M.2 2280 GNSS ($299, Crowd Supply)
    - **Why:** Same RF section, $50 more. Not cheaper.
  3.
    - **Name:** Analog Devices ADALM-PLUTO ($253.32 DigiKey, 1,573 in stock, verified)
    - **Why:** AD9363: 325 MHz-3.8 GHz, so it misses 300-325 MHz. 20 MHz bandwidth against 56 MHz. USB 2.0 (480 Mbit/s) cannot stream 56 Msps (about 1.8 Gbit/s at 16-bit IQ). Only 1 RX on SMA. TX-capable with an on-board Linux. Fails bandwidth, throughput and channel count.
  4.
    - **Name:** SDRplay RSPdx-R2 (about $235-252; prices from snippets, unverified)
    - **Why:** 1 kHz-2 GHz: no S-band, no 3.3-3.8 GHz. 10 MHz bandwidth. 1 tuner, USB 2.0. Fails coverage and bandwidth.
  5.
    - **Name:** Airspy Mini ($99 ITEAD)
    - **Why:** 24-1700 MHz, 6 MHz usable bandwidth, 1 RX, USB 2.0. Fails coverage and bandwidth; useful only as an AHRPT-rate fallback.
  6.
    - **Name:** Used LimeSDR-USB (EUR 99, myriadrf forum, Sweden)
    - **Why:** Availability is not real: one listing (3 Apr 2026), last activity 28 May 2026 with a buyer asking, status unknown. Its matched inputs are only LNAL 0.7-0.9, LNAW 0.7-2.6 and LNAH 2-2.6 GHz (MyriadRF team), so 3.3-3.8 GHz and 0.3-0.7 GHz are unmatched. The forum measured 3.6-3.9 W idle and 5.2-5.3 W in loopback against about 4 W. It needs USB 3 (displacing the T7) and uses U.FL connectors, not MHF4. It is used and discontinued, with no warranty. Fails power, matching, availability and reliability.
  7.
    - **Name:** 'B210 Mini' AD9361 clone (about $285 eBay.de snippet, unverified)
    - **Why:** Not cheaper. Ettus B210 sheet: 30.72 MHz in 2x2 (against 2x56 Msps needed) and IIP3 -20 dBm at typical NF. USB 3 displaces the T7. Trades on the Ettus name, with a relabelled-AD9363 risk and no warranty.
  8.
    - **Name:** Full-size B210 clone (about $540-685 + shipping, snippets)
    - **Why:** About 2x the price. Same AD9361 limits. 97x155 mm and 350 g, too large for the handheld.
  9.
    - **Name:** LibreSDR / Pluto+ class (AD9363 + Zynq, GbE/USB 2; price unverified)
    - **Why:** AD9363 run beyond its 325 MHz-3.8 GHz / 20 MHz rating. GbE (125 MB/s) and USB 2 cannot carry 56 Msps at 16-bit (about 224 MB/s). Full on-board Linux with TX. Fails throughput and the receive-only posture.
  10.
    - **Name:** Nuand bladeRF 2.0 micro xA4 ($540 new; used unverified)
    - **Why:** About 2x the price. Librespace measured NF 9.0-9.5 dB at 2.25-2.43 GHz.
  11.
    - **Name:** LimeSDR Mini 2.0 ($600) / used LimeSDR Mini v1 (unverified)
    - **Why:** 10 MHz-3.5 GHz (no 3.5-3.8 GHz), 30.72 MHz bandwidth, 1 RX. Librespace measured poor NF (11-15.6 dB). Fails coverage, bandwidth and channel count.
  12.
    - **Name:** LimeSDR XTRX ($960 Crowd Supply; Mouser CS-LIME-29 $1,991.27)
    - **Why:** 3.4x the price or more. mPCIe, needs an adapter.
  13.
    - **Name:** Wavelet Lab uSDR ($359)
    - **Why:** More expensive and worse: LMS6002D, 0.3-3.7 GHz, 28 MHz, M.2 2230 A+E.
  14.
    - **Name:** RigExpert Fobos (about $395), MicroPhase ANTSDR E200 (about EUR 615) / U220 (about EUR 854), LiteX M2SDR (EUR 699, sold out)
    - **Why:** All more expensive. Fobos imaging was reported (TechMinds); the E200's 1 GbE cannot carry 56 Msps.
  15.
    - **Name:** Ettus USRP B206mini-i (AD9364)
    - **Why:** $1,599 board-only / $1,820 kit (ettus.com). 1x1 only. AD936x IIP3 class.
  16.
    - **Name:** HackRF One and clones
    - **Why:** 8-bit ADC, 20 Msps, USB 2, measured NF about 11 dB without LNA. Fails.
  17.
    - **Name:** DIY build of the open LimeSDR Micro M.2 1v2 design
    - **Why:** No measured unit exists. It needs BGA LA9310/LMS7002M assembly on a multilayer RF PCB, which is unlikely to cost under $279 for one unit. The EEPROM and firmware images are not shipped. Build quality is unproven.
- **Confidence:** high
- **Conditions or tests:** Cable swap conditions:
  (1) Put the 4x CAB.01075 on a DigiKey DE order that is EUR 75 or more. The stack already has DigiKey lines: PEC11R, KSC641J, ferrites and Lime parts. Ship by UPS/FedEx, which is DDP; not by DHL, which is CPT with VAT and duty due on delivery. Check DigiKey's terms for the user's actual EU country.
  (2) Order at the 1 Dec 2026 Lime keep/cancel gate, so nothing is sunk if the Lime is cancelled. DigiKey has 1,010 in stock; lead time is 16 weeks if that runs out.
  (3) In the Crowd Supply cart, keep only the board. Confirm the cart shows a single $18 worldwide fee.
  (4) On arrival, check that the bag label reads CAB.01075, then do a continuity and centre-to-shield isolation check. Mate to the Lime's MHF4 receptacles only with the I-PEX tool.
  (5) Optional, Bench mode, conducted only: tinySA through-loss at 1.7, 2.25 and 3.5 GHz, within ±0.2 dB of a reference cable.
  
  Board (kept): the reaudit_B acceptance tests within the 30-day guarantee are unchanged. Add a conducted NF check (Y-factor/MDS with the bench noise source into the RX ports, never radiated) at about 437, 1700, 2250 and 3500 MHz on RX1 and RX2. NF clearly above about 8 dB in the matched bands is an RMA reason, which closes the unmeasured board-NF gap.
- **Stack changes:** BOM 2.11 splits into two lines.
  (a) 'LimeSDR Micro M.2 2280 Basic + $18 worldwide shipping, Crowd Supply, board only': $267 before EU import VAT, duty above EUR 150, the EUR 2 UHF from about 1 Nov 2026 and the courier fee. There is no EU seller; the order ships from Mouser, Texas.
  (b) '4x Taoglas CAB.01075 MHF4L to SMA(f) bulkhead, 1.13 mm, 100 mm, DigiKey DE 931-CAB.01075-ND': $18.36 (EUR 16.12 ex VAT), for X2 RX-A, RX-B, J4 REF IN, and X1 TX to the internal 50 Ohm load.
  
  Shopping-order step 4: the Crowd Supply cart holds the board only. The DigiKey batch gains 4x CAB.01075 at the 1 Dec gate.
  
  Unchanged: rails (Lime about 4 W on the M.2 3.3 V, VCC_5V_PERI ≤14 W gate, plus the operator-note-30 load switch), drivers (la9310_limesdr DKMS, LimeSuiteNG RX-only packages with the TX patch), riser (ADT-Link R44SF), case and bulkhead holes (same front-nut SMA bulkhead, same 100 mm length and 1.13 mm bend radius), receive-only TX block (TXEN_A/B read-back plus 50 Ohm on X1).
  
  Inconsistency to fix in v2: the I-PEX tool is listed as 90435-001 in STACK.md and as 90609-0001 in reaudit_B. Verify the correct MHF4 tool before ordering (not checked here).
- **Sources:**
  - https://www.crowdsupply.com/lime-micro/limesdr-micro
  - https://www.crowdsupply.com/taoglas/coaxial-cables
  - https://www.crowdsupply.com/guide/ordering-paying-shipping-details
  - https://www.crowdsupply.com/shipping
  - https://www.digikey.com/en/products/detail/taoglas-limited/CAB-01075/26766217
  - https://www.digikey.de/en/products/detail/taoglas-limited/CAB-01075/26766217
  - https://taoglas.com/product/cab-01075-i-pex-mhf4lhsc-comp-to-100mm-1-13mm-coax-black-cable-smaf-bulkhead-straight (HTTP 403; title from URL and search snippet)
  - https://www.digikey.com/en/products/detail/analog-devices-inc/ADALM-PLUTO/6624230
  - https://www.ettus.com/wp-content/uploads/2019/01/b200-b210_spec_sheet.pdf
  - https://www.ettus.com/all-products/usrp-b206mini-i/
  - https://discourse.myriadrf.org/t/limesdr-usb/13089
  - https://discourse.myriadrf.org/t/rf-receive-path-bandwidth-for-limesdr-usb/6392
  - https://discourse.myriadrf.org/t/board-specification-vs-api-for-lnaw-minimum-frequency/1503
  - https://discourse.myriadrf.org/t/rf-connection-10-u-fl-connectors-6-rx-4-tx/305
  - https://discourse.myriadrf.org/t/power-consumption-limesdr-usb/2610
  - https://www.mouser.com/c/?m=Lime (search snippet: CS-LIME-29 XTRX $1,991.27)
  - https://store.limemicro.com/products/limesdr-micro (search snippet: $10,000 sold-out placeholder)
  - https://www.limemicro.com/downloads/lms7002m_measurements-v1_05.pdf
  - https://gitlab.com/librespacefoundation/sdrmakerspace/sdreval/-/raw/master/Report/pdf/Evaluation_of_SDR_Boards-1.0.pdf
  - https://www.rtl-sdr.com/adalm-pluto-new-149-tx-capable-sdr-325-3800-mhz-range-12-bit-adc-20-mhz-bandwidth/
  - https://airspy.com/airspy-mini/
  - https://www.sdrplay.com/RSPdxR2

