# Antennas patch chip: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_d3593e9c-5ce`_

- **Subsystem:** antennas_patch_chip (GNSS L1/L5 patch, RTL-SDR Blog L-band patch for Inmarsat-C EGC SafetyNET, 435 MHz small antennas, chip antennas)
- **Findings:**
  1.
    - **Claim in stack:** 2.4 / C15 / D8: L-band patch = RTL-SDR Blog active L-band patch (1525-1660 MHz, 20 mA), $59.95, on the buy page; product URL is 404; status 'verified'.
    - **Finding:** Confirmed. The rtl-sdr.com buy page lists the 'RTL-SDR Blog Active L-Band 1525-1660 Inmarsat to Iridium Patch Antenna Set' at $59.95 (add-to-cart id 35592). It is version two (gray housing). The set contains an RHCP active patch in a weatherproof housing, a 2 m RG174 extension, a flexible tripod and a suction cup. Stock is shown at the Amazon USA warehouse and the Chinese worldwide warehouse. Older posts give $44.95/$49.95 and a 3 m cable; the store now says 2 m. The image captions still say 1525-1637 MHz, a leftover from v1.
    - **Verdict:** confirmed
    - **Action:** Keep. Order through the buy-page add-to-cart, AliExpress 4000311955837 or eBay. Budget about 2 dB of RG174 loss at 1.54 GHz for the 2 m lead (model: about 0.98 dB/m), or use a shorter RG316 jumper to P3.
    - **Impact:** No change to the BOM ($59.95).
    - **Sources:**
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://www.rtl-sdr.com/preorder-sale-active-l-band-1525-1660-inmarsat-and-iridium-patch-back-in-stock-for-44-95/
      - https://www.rtl-sdr.com/rtl-sdr-blog-active-l-band-patch-antenna-for-inmarsat-iridium-gps-back-in-stock/
  2.
    - **Claim in stack:** #112 / 2.4 / 5.2 P3: patch is 175 mm with SAW 1525-1660 MHz, draws 20 mA, is powered at 4.5 V from injector ch3 after DC-sense, and does not cover HRPT.
    - **Finding:** Vendor confirms: 175 x 175 mm patch, RHCP (author's reply in comments), SAW filter after the LNA, 3.3-5 V bias, 15-20 mA (20 mA max), 50 ohm. The vendor also says it is not for HRPT or GOES; 1698-1707 MHz is outside the 1525-1660 MHz range. The 4.5 V on ch3 is inside 3.3-5 V. Still unpublished: LNA gain, noise figure, exact SAW passband edges, and the connector gender on the housing.
    - **Verdict:** confirmed
    - **Action:** Treat the patch's gain and NF as unknown in the Inmarsat-C link model. Measure receive-only: the noise-floor step on RTL-B between a 50 ohm load and the patch pointed at the sky, plus the NCS carrier C/N0. DC-sense must classify a 15-20 mA load as a valid active antenna. Check the connector gender when the part arrives.
    - **Impact:** The patch tier's Inmarsat-C margin rests on community decode reports, not on a vendor gain figure.
    - **Sources:**
      - https://www.rtl-sdr.com/preorder-sale-active-l-band-1525-1660-inmarsat-and-iridium-patch-back-in-stock-for-44-95/
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
  3.
    - **Claim in stack:** 4.1 row Inmarsat-C: 'RF covered (rtl-sdr.com reports decoding with the patch)'; GNSS-SDR on RTL-B with the L-band patch.
    - **Finding:** Partly confirmed. The vendor lists Inmarsat STD-C EGC, AERO, Iridium and GPS/GNSS as uses. The SignalsEverywhere test post demonstrates only JAERO decoding an 8400 bps AERO voice channel, which is private aeronautical content and out of scope. No vendor STD-C SNR figure was found. RHCP polarisation matches the Inmarsat and GNSS downlinks. The SAW range covers GPS L1, Galileo E1, BDS B1 and GLONASS G1, so GNSS-SDR on this patch is valid.
    - **Verdict:** confirmed
    - **Action:** Do not reproduce the vendor's AERO or Iridium demos: AERO and Iridium are private-content decoders and stay unbuilt. Keep the egc-gate as the only Inmarsat path. Cite the EGC claim as 'vendor-listed use, community reports', not as measured.
    - **Impact:** Compliance note only; no hardware change.
    - **Sources:**
      - https://www.rtl-sdr.com/signalseverywhere-tests-our-rtl-sdr-blog-active-l-band-patch-antenna/
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
  4.
    - **Claim in stack:** #2 / C16: search for the NCS by a power-only scan of 1537-1545 MHz; Inmarsat-C EGC SafetyNET stays in scope.
    - **Finding:** Inmarsat-C continues. Riviera (20 May 2025) quotes Inmarsat Maritime/Viasat: the network is being upgraded and all hardware renewed 'to keep that network going out to 2040'. About 130,000 terminals are active, and the I-8 satellites are planned for 2028. I found no 2025-2026 notice of an NCS channel change. The community list of NCS TDM channels (1537.10, 1537.70, 1541.45 MHz) falls inside the 1537-1545 MHz scan.
    - **Verdict:** confirmed
    - **Action:** Keep the power-only scan rather than a fixed channel table. Re-check the channel plan when the I-8 satellites enter service (about 2028).
    - **Impact:** There is no risk of the target vanishing during the device's life.
    - **Sources:**
      - https://www.rivieramm.com/news-content-hub/technology-advances-gmdss-for-safety-data-and-communications-84881
      - https://sigidwiki.com/wiki/Inmarsat-C_TDM
  5.
    - **Claim in stack:** 2.4: GNSS antenna = Waveshare GNSS L1+L5 active (25346), $16.99, on P7 with 3.3 V from the LC76G, lead 1-3 m.
    - **Finding:** SKU 25346 ('GPS External Antenna (D)') is confirmed at $16.99 (tiers from $16.59). Specs: RHCP, axial ratio <=3 dB, 2 dBi, LNA 28±2 dB, NF <=2 dB, VSWR <=2, 3.0-18.0 V, <=20 mA, SMA-J plug, 50x50x19.1 mm, 102 g, magnetic or tape mount, -40 to 85 C. Corrections: the RG174 lead is a fixed 3 m (customisable only at order), not 1-3 m; that is about 3 dB at L1 (model), which the 28 dB LNA covers. The band list (BDS B1I/B1C/B2a, GPS L1/L1C/L5, Galileo E1/E5a, QZSS L5, NavIC L5) does not include GLONASS. The Pi Hut shows it sold out; Waveshare shows Add to Cart but no stock count.
    - **Verdict:** corrected
    - **Action:** Change the note to '3 m RG174 fixed; coil the excess away from the HDMI/USB 3 edge'. Accept weaker or absent GLONASS on this antenna, or use the ANN-MB5 (1559-1608 MHz, which includes G1) if GLONASS matters for the plausibility gate.
    - **Impact:** Minor: possible loss of GLONASS satellites on the LC76G; GPS, Galileo and BDS are unaffected.
    - **Sources:**
      - https://www.waveshare.com/gps-external-antenna-d.htm
      - https://thepihut.com/products/gnss-l1-l5-dual-frequency-active-antenna
  6.
    - **Claim in stack:** 2.4 / 2.8: the antenna is fed at 3.3 V by the LC76G (Waveshare 24370) through P7 via an IPX-SMA pigtail.
    - **Finding:** The Waveshare LC76G schematic shows module pin VCC_RF (=VCC, from an RT9193-33 LDO) feeding the RF line through a 10 ohm resistor (R5) and a 68 nH choke onto the IPEX connector, so active-antenna bias is present. Model: 3.3 V minus 10 ohm x 15-20 mA gives 3.10-3.15 V at the antenna. With LDO tolerance of -2 %, the worst case is about 3.03 V against the 25346's 3.0 V minimum, a margin of roughly 30 mV. The board ships with an active ceramic patch (the 'lid patch' option). The gender chain works: board IPEX, an IPX to SMA-female bulkhead pigtail (already in 2.10) at P7, then the SMA-J antenna.
    - **Verdict:** new_risk
    - **Action:** Bench-measure DC at P7 under antenna load. If below about 3.05 V, bridge R5 (0 ohm) or bias P7 from the 4.5 V injector, with a DC block toward the LC76G RF_IN. The 25346 accepts 3-18 V. Specify the bulkhead as SMA-K (female).
    - **Impact:** Low-probability loss of LNA gain at cold temperatures or low supply; costs nothing to check.
    - **Sources:**
      - https://files.waveshare.com/wiki/LC76G/manual/LC76G%20GNSS%20Module.pdf
      - https://www.waveshare.com/wiki/LC76G_GNSS_Module
      - https://www.waveshare.com/LC76G-GNSS-Module.htm
  7.
    - **Claim in stack:** 2.4 / 4.1: 'GNSS L1+L5' antenna; 'also the L1 reference for the lab'; region gate chooses LC76G or MAX-M10S.
    - **Finding:** The Waveshare wiki lists the LC76G as an 'L1 Receiver' (GPS/GLONASS/Galileo/BDS/QZSS, 47 tracking channels); Quectel's page gives no L5. The u-blox M10 (MAX-M10S) is also L1-only (platform fact, not re-fetched). The L-band patch used for GNSS-SDR does not cover L5 (1176 MHz). So the L5 half of the 25346 is unused by every receiver in the stack. It is harmless, but the stack must not claim L5 capability.
    - **Verdict:** corrected
    - **Action:** Describe it as an 'L1 antenna (L5 unused)'. Keep it for price. If a dual-band receiver is ever chosen, revisit then.
    - **Impact:** Wording only; no extra accuracy from L5.
    - **Sources:**
      - https://www.waveshare.com/wiki/LC76G_GNSS_Module
      - https://www.quectel.com/product/gnss-lc76g/
  8.
    - **Claim in stack:** 2.4: alternative u-blox ANN-MB5 at $42.50 ('more expensive').
    - **Finding:** Confirmed. SparkFun GPS-25071 is $42.50 and in stock: L1 1559-1608 MHz (includes GLONASS G1), L5/E5a/B2a/NavIC 1164-1186 MHz, peak 4.5 dBic on L1, RHCP, SMA, 3 m RG174, 49.1x46.1x15.9 mm, 103.8 g. Distributor search snippets (not opened) show Mouser at about $35.64 for one unit, and Future lists 3-5 V supply. One aggregator (ic-direct) claims 'obsolete'; that is unverified and contradicted by SparkFun stock.
    - **Verdict:** new_option
    - **Action:** Relabel it as the quality alternative, not a budget one: it gains about 2.5 dB of peak antenna gain and GLONASS coverage for about $25 more. Check its minimum supply against the roughly 3.1 V from VCC_RF before choosing it.
    - **Impact:** Optional +$25.51.
    - **Sources:**
      - https://www.sparkfun.com/u-blox-multi-band-active-gnss-antenna-l1-l5-ann-mb5.html
      - https://www.futureelectronics.com/p/9183797
  9.
    - **Claim in stack:** #82 / 5.7 item 8: 'USB 3 jams GNSS within about 2 m'; external antenna on a lead; lid patch only after a C/N0 on/off test.
    - **Finding:** The mechanism is supported: Inertial Labs' knowledge base names USB3 and PCIe as EMI sources in the GNSS bands, and USPTO patents 11238001 and 11714773 describe USB-3 products interfering with GPS L1. I found no primary measurement giving the '2 m' figure; the Intel white paper commonly cited concerns 2.4 GHz.
    - **Verdict:** unverified
    - **Action:** Keep the rule and the C/N0 <=1 dB-Hz acceptance test. Drop '2 m' as a sourced number, or label it 'rule of thumb'.
    - **Impact:** None on parts; wording of the evidence only.
    - **Sources:**
      - https://resources.inertiallabs.com/en-us/knowledge-base/device-is-not-seeing-proper-number-of-satellites
      - https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11238001
  10.
    - **Claim in stack:** #111: W9MDB measurements at 146 MHz vs NA-771: A-V85 -0.8 dB, NA-701 -2.3 dB, UV-5R -9.8 dB, SRH805S -29.8 dB; one NA-701 copy 8-10 dB worse. Used to justify A-V85/SRH-701 as the 70 cm antenna.
    - **Finding:** The numbers match the W9MDB PDF (v1.2, 15 Oct 2013): 146 MHz column, ±2 dB, measured on an HT held about 2 in from the face; the second NA-701 read -10.3 dB. But the use here is 435-438 MHz. W9MDB's own 435 MHz column (uncalibrated, 'not even dB intervals for sure') shows A-V85 -21.8 vs NA-771 -13.1, about -8.7 dB, and NA-701 -23.5/-25.6, about -10 to -12.5 dB. The Diamond SRH-701 was never measured. The 146 MHz ranking does not support the 70 cm choice.
    - **Verdict:** corrected
    - **Action:** In #111, quote the UHF column with its caveat, or drop W9MDB as evidence for 70 cm. Use the dipole option below as the 70 cm default.
    - **Impact:** The CubeSat and ISS link margins in 4.1 may be optimistic if a short whip is materially below the assumed gain.
    - **Sources:**
      - https://www.miklor.com/COM/pdf/AntennaTestingW9MDB.pdf
  11.
    - **Claim in stack:** 2.4 / 5.3: 70 cm whip = DIY 17 cm, Diamond SRH-701 (19 cm) or Baofeng A-V85 (16.8 cm), screwed onto the Uputronics 440 on P2; $3-25.
    - **Finding:** SRH-701 confirmed: 19 cm, SMA male, 26 g, vendor gain 0 dBi at 144 MHz and 3 dBi at 432 MHz (an HT-ground claim), WiMo EUR 16.90 incl. VAT, in stock, ships in 1-2 days (+EUR 14.20 shipping). The Uputronics 440 MHz CubeSAT preamp (GBP 51.59) has SMA female connectors on both ports, so the SRH-701 mates directly. The A-V85 length (6.6 in = 16.8 cm) is confirmed by W9MDB, but I found no current listing. Baofeng-family antennas are SMA-female, because the UV-5R has an SMA-male jack; that is a general fact, not checked on this listing. So the A-V85 would need an SMA male-male adapter on the preamp. The DIY 17 cm whip matches lambda/4 at 437.5 MHz (17.1 cm, calculation). A whip plus a roughly 40 g preamp cantilevered on the P2 bulkhead stresses the SMA.
    - **Verdict:** corrected
    - **Action:** Remove the A-V85 from the BOM, or note 'SMA-F, needs adapter; availability unverified'. Keep the SRH-701 or the DIY 17 cm whip on an SMA-male base. Fit the preamp with a short SMA M-F jumper or a printed Uputronics bracket rather than hanging it off P2.
    - **Impact:** Avoids a connector-gender surprise; the price range is unchanged.
    - **Sources:**
      - https://www.wimo.com/en/srh-701
      - https://store.uputronics.com/products/uputronics-filtered-preamps
      - https://www.miklor.com/COM/pdf/AntennaTestingW9MDB.pdf
  12.
    - **Claim in stack:** C15 / 5.3 table: patch-tier 70 cm reception (ISS SSTV 437.550, APRS 437.825, FM 437.800, CubeSats 435-438) uses a rigid whip that 'needs your confirmation' (open question 3).
    - **Finding:** Better option: the RTL-SDR Blog dipole kit, already carried twice in the patch tier ($17.95 each, in stock). Its short telescopic elements (5-13 cm, M5 thread, plus about 2 cm inside the base) give a half-wave dipole resonant near 445 MHz per the vendor's cheat sheet ('14 cm + 2 cm'). The base has a ferrite choke, and its 60 cm RG174 lead ends in SMA male, which mates directly with the Uputronics 440 SMA-female input. Model: at 437.5 MHz the mismatch loss is about 0.26 dB and the 60 cm RG174 about 0.3 dB, against 2.15 dBi for a lambda/2 dipole versus about 0 dBi assumed for a whip. That is about +1 to +2 dB net. The kit telescopes, so it is a folding antenna and needs no user confirmation. The 60 cm lead also moves the antenna away from the device's display and USB 3 noise.
    - **Verdict:** new_option
    - **Action:** Make 'dipole kit, short elements fully extended, Uputronics 440 at the 60 cm lead' the patch-tier 70 cm default; reuse kit #2 between AIS sessions or add a third kit ($17.95). Keep the SRH-701 or 17 cm whip as the quick-look fallback. Tilt the dipole broadside to the pass.
    - **Impact:** $0 to +$17.95. Removes most of open question 3 and gives about +1 to 2 dB on marginal CubeSat links (model).
    - **Sources:**
      - https://www.rtl-sdr.com/using-our-new-dipole-antenna-kit/
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://store.uputronics.com/products/uputronics-filtered-preamps
  13.
    - **Claim in stack:** #112: 'Johanson 433 MHz chip: -4 dBi'; chips are not used below L-band.
    - **Finding:** Confirmed. Johanson 0433AT62A0020002U, Rev 4.0 (legacy P/N 0433AT62A0020E-AEC; 25x5x1.2 mm, AEC-Q200): passband 423-443 MHz, peak gain -4.0 dBi typical (mounting config 1) or -6.8 dBi (config 2), average -4.0/-7.2 dBi. These figures are measured on Johanson's evaluation boards with a pi-matching network.
    - **Verdict:** confirmed
    - **Action:** Keep chips out of the 70 cm chain. A chip is 4 to 7 dB below the dipole, which erases the -5 to +5 dB CubeSat margins.
    - **Impact:** None.
    - **Sources:**
      - https://johansontechnology.com/docs/4353/0433AT62A0020002U.pdf
  14.
    - **Claim in stack:** #112: half-wave patch at 137 MHz is about 52 cm on FR4 or 25 cm on er 20 ceramic; aperture limit at 1.70 GHz is 7.6 dBi for 12x12 cm and 12.1 dBi for 20x20 cm.
    - **Finding:** Recalculated (model, 100 % aperture efficiency, no fringing): 51.8 cm (er 4.4) and 24.3 cm (er 20) at 137.9 MHz; 7.65 dBi and 12.09 dBi at 1.70 GHz.
    - **Verdict:** confirmed
    - **Action:** None.
    - **Impact:** Supports D16: patch and chip cannot serve 137-146 MHz or HRPT/Metop.
    - **Sources:**
      - calculation (python, this session)
  15.
    - **Claim in stack:** Rule compliance of the patch tier (patch or chip, or folding pieces of 20-23 cm, max 35 cm; no loops).
    - **Finding:** Compliant: L-band patch 175 mm, GNSS puck 50 mm, LC76G ceramic patch, and the dipole kit (folding, 23 cm collapsed). None of them is a loop. The rigid SRH-701 (19 cm), the 17 cm whip and the 4-turn helix on an 18 cm disc are neither patch, chip nor folding; they stay under 20-23 cm but remain open for the user's confirmation, as STACK says. No part in this tier targets military bands. The L-band patch also passes Iridium (1616-1626 MHz), but no Iridium decoder exists in the stack.
    - **Verdict:** confirmed
    - **Action:** Keep open question 3, now limited to the whip and the helix if the dipole becomes the 70 cm default.
    - **Impact:** Fewer items depend on the user's answer.
    - **Sources:**
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://www.waveshare.com/gps-external-antenna-d.htm
  16.
    - **Claim in stack:** 2.4: HRPT 4-turn RHCP helix on a shared 18 cm disc (DIY, $10-20), -0.3 to -0.5 dB versus a 20 cm disc (model).
    - **Finding:** Outside the strict patch/chip scope (it is an axial helix). Not re-modelled in this pass; no primary source exists for a DIY build. The rule classification is as stated in STACK (needs the user's confirmation).
    - **Verdict:** unverified
    - **Action:** Leave it to the NEC re-run already listed in STACK.
    - **Impact:** None from this audit.
    - **Sources:** []
  17.
    - **Claim in stack:** 2.4 subtotal $175.79-207.79.
    - **Finding:** The arithmetic reproduces: 2x$17.95 + $3-25 + $59.95 + $10-20 + $49.95 + $16.99 = $175.79-207.79. The SRH-701 at EUR 16.90 incl. VAT (about $19 at STACK's implied EUR rate of 1.124) fits inside the $3-25 range, excluding shipping, as STACK's convention requires.
    - **Verdict:** confirmed
    - **Action:** If the dipole option is adopted with a third kit, the subtotal becomes $193.74-225.74; with kit reuse it is unchanged, or lower if the whip is dropped.
    - **Impact:** Within ±$18.
    - **Sources:**
      - https://www.wimo.com/en/srh-701
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
  18.
    - **Claim in stack:** 2.4 GNSS antenna mounting (magnetic base or tape); IMU pack (BNO085) used for pointing.
    - **Finding:** The 25346 ships with a magnetic base. Placed close to the BNO085 pack, the magnet would bias the magnetometer heading used for satellite pointing. General physics, not measured.
    - **Verdict:** new_risk
    - **Action:** Keep the GNSS puck at least about 30 cm from the IMU pack, or use the tape mount on the lid; include it in the IMU calibration check.
    - **Impact:** Minor; avoids pointing errors.
    - **Sources:**
      - https://www.waveshare.com/gps-external-antenna-d.htm
- **Current status oct 2026:** The parts are all still sold as of 18 Oct 2026, and I found no end-of-life notices.
  
  - **RTL-SDR Blog L-band patch set (v2, gray):** $59.95 on the rtl-sdr.com buy page (add-to-cart id 35592). In stock at the Amazon USA and China worldwide warehouses. The standalone product URL still returns 404. No newer revision found, and LNA gain and noise figure are still unpublished.
  - **Waveshare 25346 L1+L5 antenna:** listed at $16.99 with Add to Cart but no stock count; The Pi Hut shows it sold out.
  - **Waveshare LC76G (24370):** $14.99 and ships with an active ceramic patch. The schematic confirms antenna bias through VCC_RF, a 10 ohm resistor and a 68 nH choke onto the IPEX connector.
  - **u-blox ANN-MB5:** SparkFun GPS-25071, $42.50, in stock.
  - **Diamond SRH-701:** WiMo, EUR 16.90 incl. VAT, in stock, ships in 1-2 days.
  - **Baofeng A-V85:** no current listing found.
  - **Uputronics 440 MHz CubeSAT preamp:** GBP 51.59; SMA female in and out; vendor says bias-tee input is 5 V.
  - **RTL-SDR Blog dipole kit:** $17.95, in stock at the China warehouse.
  - **Johanson 433 MHz chip:** current datasheet is 0433AT62A0020002U Rev 4.0 (2023), legacy P/N 0433AT62A0020E-AEC; active.
  - **Inmarsat-C:** Inmarsat Maritime/Viasat say they are renewing the network hardware to keep it running to 2040 (Riviera, May 2025). I-8 satellites are planned for 2028. I found no 2025-2026 NCS channel-change notice; the community list of NCS channels (1537.10, 1537.70, 1541.45 MHz) sits inside the 1537-1545 MHz power-only scan.
  
  These antennas have no firmware or drivers.
- **Notes:** Method: about 12 WebSearch calls and primary pages via WebFetch or curl. Pages read: the rtl-sdr.com buy page and release posts, the Waveshare product pages, wiki and LC76G schematic PDF, SparkFun, WiMo, the Uputronics Shopify product JSON, the Johanson datasheet PDF, the W9MDB PDF and the Riviera article. Two sources are search snippets only (Mouser and Future prices for the ANN-MB5, and the Inertial Labs EMI note) and are marked as such.
  
  Calculations in Python are models: aperture and patch sizes, the LC76G bias margin, dipole mismatch (Q=8 assumed) and RG174 loss (Belden-8216-class 0.79 dB/m at 1 GHz, scaled by the square root of frequency).
  
  Main corrections:
  - **70 cm whip evidence:** the W9MDB numbers in #111 come from the 146 MHz column. The 435 MHz column (uncalibrated) puts the A-V85 about 8.7 dB and the NA-701 about 10-12.5 dB below the NA-771. The SRH-701 was never tested.
  - **A-V85:** likely SMA-female and no longer listed.
  - **GNSS antenna lead:** a fixed 3 m, not 1-3 m.
  - **GNSS antenna bands:** no GLONASS, and L5 is unused because the LC76G and the M10 are L1-only.
  - **LC76G antenna bias:** about 3.03-3.17 V against a 3.0 V minimum; measure it.
  
  Main new option: use the dipole kit's short elements (about 445 MHz resonance, ferrite-choked base, SMA-male lead that mates with the Uputronics SMA-female input) as the patch-tier 70 cm antenna. Model gain is about +1-2 dB over a whip, it is rule-compliant because it folds, and it costs $0-17.95.
  
  Cross-subsystem items for rf_frontend:
  - The Uputronics page says bias-tee input is 5 V, but STACK feeds 4.5 V on ch2; confirm that the preamp works at 4.5 V.
  - The Uputronics 434 MHz HABAmp/CubeSAT/ISM variant (GBP 41.99) is cheaper than the 440 MHz variant (GBP 51.59), but its SAW bandwidth was not checked.
  
  Unverified: L-band patch LNA gain, NF, SAW edges and housing connector gender; the '2 m' USB 3 jamming distance; the ANN-MB5 minimum supply voltage. Downloads are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/pa_dl/.

## Адверсаріальна перевірка (`verify`)

_Run `wf_d3593e9c-5ce`_

- **Subsystem:** antennas_patch_chip (GNSS L1 puck on P7/LC76G, RTL-SDR Blog active L-band patch for Inmarsat-C EGC SafetyNET and optional GNSS-SDR, 435 MHz small antennas with the Uputronics 440 preamp, chip antennas): stage 3, adversarial verification
- **Verdict:** The patch/chip tier survives with corrections. No part has to be swapped, but six stage 1-2 findings are refuted or partly refuted, and there are three new wiring or usage risks.
  
  **Re-confirmed on primary sources, 18 Oct 2026:**
  - RTL-SDR Blog L-band patch v2: $59.95; RHCP; 175x175 mm; LNA then SAW; 3.3-5 V; 15-20 mA; 2 m RG174; not for HRPT or GOES.
  - Waveshare 25346 at $16.99.
  - LC76G is L1-only (Quectel spec V1.1).
  - u-blox ANN-MB5 datasheet R03 (mass production); SparkFun $42.50, in stock.
  - Uputronics 440 MHz CubeSAT preamp: GBP 51.59, available; FPA datasheet Rev 3.0.
  - Diamond SRH-701 at WiMo: EUR 16.90, in stock.
  - Johanson 0433AT62A0020002U Rev 4.0.
  - W9MDB columns.
  - ARISS Series 34: 22-25 Oct 2026 on 437.55 MHz.
  - Inmarsat-C network renewed to keep it running to 2040.
  
  **What changes:**
  1. The LC76G board is wired with VCC from the 3.3 V header pin (gnss_imu.json). That puts its RT9193-33 LDO in dropout. Modelled antenna bias is 2.91-3.04 V at 20 mA, against the 3.0 V minimum of both GNSS antennas. Feed the board's VCC from 5 V instead; Waveshare's own wiring tables do this.
  2. Any external bias on P7 needs a DC block between the bias tee and the board's IPEX connector. The board's 68 nH + 10 ohm network ties the antenna line to VCC_RF.
  3. The "no GLONASS" claim for the 25346 is only half true. The text list omits GLONASS, but the vendor's own S21 plot shows 39 dB at 1.602 GHz.
  4. The 70 cm default becomes the dipole kit's short elements, fully extended. It reuses kit #1, not kit #2, because RTL-A is time-shared between LRPT and UHF while kit #2 runs AIS at the same time. Stage 2's 16.3 cm per-side tape length cannot be reached with these elements.
  5. The cheaper Uputronics 434 MHz variant is unsuitable: the vendor plot shows about 4 dB down at 437.7 MHz. The 440 MHz passband is about 427-452 MHz at -3.4 dB, not "30 MHz".
  6. Stage 2 misattributed the Honeywell source. Honeywell describes FCC-authorised terrestrial L-band networks overlapping the Inmarsat receive band (US Band 24, 1526-1536 MHz), not EU SDL.
  
  Web search budget ran out on the first call in this stage. Every check above uses curl or WebFetch on primary pages.
- **Confirmed:**
  - RTL-SDR Blog Active L-Band 1525-1660 MHz Patch Antenna Set, version two (gray): $59.95 on https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/ (add-to-cart=35592; AliExpress item 4000311955837). The set is 'Active RHCP L-Band Patch Antenna ... in Weather Proof Enclosure, 1x 2 meter RG174 extension cable, 1x Flexible Tripod Mount, 1x Suction Cup Mount'. It needs 3.3-5 V at 20 mA bias. Amazon USA and Chinese worldwide warehouses both show 'in stock' (18 Oct 2026).
  - The release post confirms the 175 x 175 mm patch, 'SAW filter after the LNA', 3.3-5 V bias, and 'you cannot use it for weak signals that require a dish like HRPT or GOES'. In the comments the vendor answers 'RHCP', '20mA' maximum and '15 – 20 mA'. It adds: 'should be used with one meter or more of coax ... may perform poorly if the RTL-SDR is placed right at the antenna due to interference.' https://www.rtl-sdr.com/preorder-sale-active-l-band-1525-1660-inmarsat-and-iridium-patch-back-in-stock-for-44-95/
  - 4.5 V from ch3 is inside the patch's 3.3-5 V range. DC-sense must accept 15-20 mA as a valid active antenna.
  - Community STD-C reception with this patch exists: TechMinds with Scytale-C; Bert: 'The standard patch 600 bps and 1200 bps signal are received good'. Use it as RF evidence only; those decoders stay banned and egc-gate stays the only path. https://www.rtl-sdr.com/techminds-reviews-our-rtl-sdr-blog-l-band-patch-antenna-horn-dish-mod/
  - Pointing matters. The vendor says 'Angling it towards the satellite will yield significantly higher gain'. Bert reports that a 5 degree turn moved SNR between 2 and 10 dB. The TechMinds post's 'Inmarsat signals are LHCP' contradicts the vendor's own RHCP product statement and must not be copied.
  - Inmarsat-C continues (Riviera, 20 May 2025, Peter Broadhurst, Inmarsat Maritime): 'renewing all the hardware required to keep that network going out to 2040'; about 130,000 terminals; I-8 satellites planned for 2028. https://www.rivieramm.com/news-content-hub/technology-advances-gmdss-for-safety-data-and-communications-84881
  - The sigidwiki NCS TDM list (AOR-W 1537.70, IOR 1537.10, AOR-E and POR 1541.45 MHz; page last modified 16 Apr 2022) lies inside the 1537-1545 MHz power-only scan. Keep the scan and do not ship a fixed table. https://sigidwiki.com/wiki/Inmarsat-C_TDM
  - Waveshare 25346 'GPS External Antenna (D)': $16.99 (tiers $16.59/$16.39/$16.31). RHCP, 2 dBi, LNA 28±2 dB, NF ≤2 dB, VSWR ≤2.0, DC 3.0-18.0 V, ≤20 mA, fixed 3 m RG174, SMA-J, 50x50x19.1 mm, 0.102 kg, magnetic base or double-sided tape, -40 to 85 C. Listed bands: BDS B1I/B1C/B2a, GPS L1/L1C/L5C, Galileo E1/E5a, QZSS L5, IRNSS S-L5. https://www.waveshare.com/gps-external-antenna-d.htm
  - The LC76G is L1-only: GPS L1 C/A, GLONASS L1, Galileo E1, BDS B1I/B1C, QZSS L1 C/A (Quectel LC76G Series GNSS Specification V1.1). The L5 half of the 25346 is unused by every receiver in the stack. https://quectel.com/content/uploads/2024/03/Quectel_LC76G_Series_GNSS_Specification_V1.1-1-1.pdf
  - Waveshare LC76G schematic: RT9193-33 LDO feeds VCC; module pin 14 VCC_RF goes through R5 10R, C4 100 pF / C5 100 nF and L1 68 nH onto the IPEX DATA line; RF_IN goes through C6 100 pF and R7 0R. So active-antenna bias is present on the IPEX connector. https://files.waveshare.com/wiki/LC76G/manual/LC76G%20GNSS%20Module.pdf
  - u-blox ANN-MB5 datasheet UBX-22038811 R03 (6 Nov 2023, Mass production): L1 1559-1608 MHz; L5/E5a/B2a/NavIC 1164-1186 MHz; 4.5 dBic at zenith on a 12 cm ground plane; axial ratio 3.2 dB; LNA 15±3 dB; NF 2.0 dB including the SAW pre-filter; RG174 3 m loss 3.6 dB at L1; supply 3.0-5.0 V, 17 mA; out-of-band rejection 45 dB below 1459 MHz and 35 dB above 1708 MHz; not protected against overvoltage or reverse voltage. SparkFun GPS-25071: $42.50, 'In stock'. https://cdn.sparkfun.com/assets/0/b/a/5/2/ANN-MB5_Datasheet.pdf
  - RG174 loss: u-blox's measured 3.6 dB per 3 m at L1 (1.2 dB/m) replaces stage 1's 0.98 dB/m. Model: 2 m at 1541 MHz is about 2.4 dB (up to 3.6 dB for copper-clad-steel RG174); 3 m at L1 is 3.6 dB; 0.6 m at 437.5 MHz is 0.38-0.57 dB.
  - Uputronics FPA datasheet Rev 3.0 (18/10/2024): bias-tee input 3.5-5.5 V ('Exceeding 5.5V will cause permanent damage'); about 50 mA; NF average 0.75 dB; 440 MHz gain at least 19 dB; LNA before the SAW; 'Antenna Connector DC Blocked (No Bias-tee passthrough)'; Skyworks limiter; HPF below 100 MHz; V3 enclosure 69x40x12 mm; SMA female in and out; 'If the unit is not powered there is no passthrough of signal'. Shopify .js shows 440MHz CubeSAT at GBP 51.59, available=True (product updated 2026-10-18). https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf?v=1729257808
  - Diamond SRH-701 at WiMo (SKU 17039): EUR 16.90 incl. VAT (+EUR 14.20 shipping), 'In stock, shipped in 1 to 2 days', SMA male, 19 cm, 26 g, vendor 0 dBi at 144 MHz and 3 dBi at 432 MHz, no reviews. That is about $19.00 at STACK's implied EUR rate. https://www.wimo.com/en/srh-701
  - W9MDB v1.2 (15 Oct 2013): the #111 numbers come from the 146 MHz column. The 435 MHz column is labelled 'not calibrated so can only rely on relative values and not even dB intervals for sure'. A-V85 reads -21.8 against NA-771 -13.1, and NA-701 reads -25.6/-23.5. The SRH-701 was not tested. The test was a 2 mi terrestrial HT link, not a satellite geometry. https://www.miklor.com/COM/pdf/AntennaTestingW9MDB.pdf
  - RTL-SDR Blog dipole kit: $17.95. Contents: base with 60 cm RG174 and an SMA male connector, 'decoupled from the base elements with a ferrite choke'; 2x 23 cm-1 m and 2x 5-13 cm telescopic elements (M5 thread); 3 m RG174 extension; tripod; suction cup. Cheat sheet: 'Small Antenna, 4 Sections, 14cm + 2cm is resonant @ ~445 MHz'. The admin quotes a '~1.7% defect rate'. 'Designed for portable and temporary outside usage.' https://www.rtl-sdr.com/using-our-new-dipole-antenna-kit/
  - Johanson 0433AT62A0020002U, Revision 4.0 (legacy P/N 0433AT62A0020E-AEC; 25x5x1.2 mm; AEC-Q200): passband 423-443 MHz; peak gain -4.0 / -6.8 dBi and average gain -4.0 / -7.2 dBi (mounting configurations 1 and 2) on Johanson evaluation boards. Chips stay out of the 70 cm chain. https://johansontechnology.com/docs/4353/0433AT62A0020002U.pdf
  - The physics in #112 recomputes (model): a half-wave patch at 137.9 MHz is 51.8 cm (er 4.4) or 24.3 cm (er 20); the aperture limit at 1.70 GHz is 7.65 dBi for 12x12 cm and 12.09 dBi for 20x20 cm.
  - ARISS: Series 34 'ARISS Hardware' runs 22-25 Oct 2026, times TBD, '437.55 MHz (+/- Doppler shift), decode with Robot 36 mode, transmission 36 seconds on, two minutes off'. Series 31 was announced at 10 W. Model: Doppler is about ±10.2-10.5 kHz, and an FM filter without tracking costs about 3.8 dB. https://www.ariss.org/upcoming-sstv-events.html
  - USB 3 '2 m' is a community rule of thumb, not a measurement. OpenMarine: Didier B, 'moving from 0m90 to 1m80 was a significant relief'; 'Connecting my SSD to an USB2 port solved immediately the case'; shielding the USB3 bridge took him from 'no fix' to 'instantaneous Fix'. Another user got perfect reception at about 1.5 m. No C/N0 numbers are given. https://forum.openmarine.net/printthread.php?tid=3062
  - Magnet distance: on the ArduPilot forum (8 Jun 2024) the compass problem appeared at 9 cm from magnets and disappeared at 15 cm (6 in). Keep the 25346 magnet at least 30 cm from the BNO085 pack, or use the tape mount. https://discuss.ardupilot.org/t/compass-variance-and-mag-field/119041
  - GNSS-SDR on an RTL-SDR with the RTL-SDR Blog L-band patch has produced a 'live GPS position' (DragonOS write-up). It remains a bring-up test only. https://rtl-sdr.com/dragonos-running-gnss-sdr-and-obtaining-a-gps-position-with-an-rtl-sdr-and-patch-antenna
  - The 2.4 subtotal arithmetic reproduces: 2x17.95 + (3-25) + 59.95 + (10-20) + 49.95 + 16.99 = 175.79-207.79.
- **Corrections:**
  1.
    - **Claim in stack:** 2.8 / gnss_imu.json wiring: the LC76G board's VCC comes from the 40-pin 3V3 pin (pin 1/17). 2.4 / 5.3: P7 is '3.3 V from LC76G'.
    - **Finding:** The Waveshare board regulates its own 3.3 V with an RT9193-33. Datasheet DS9193-18: VIN 2.5-5.5 V; ±2 %; dropout 170 mV at 200 mA and 220-300 mV at 300 mA. The board's VCC pin is rated '3.3V/5V', and Waveshare's own wiring tables use 5 V. Fed from 3.3 V, the LDO sits in dropout. The antenna feed then drops a further 10 ohm (R5) plus 68 nH, and the 3 m RG174. Model, with the LC76G at 36 mA: at 20 mA the antenna sees 3.04 V nominal and 2.91 V worst case (3.3 V header -3 %). At 15 mA it is 3.10 / 2.97 V. Fed from 5 V, it is 3.08 / 3.00 V at 20 mA and 3.14 / 3.06 V at 15 mA. The 25346 and the ANN-MB5 both specify a 3.0 V minimum.
    - **Verdict:** corrected
    - **Action:** Wire the LC76G board's VCC to 40-pin 5 V (pin 2 or 4) instead of 3V3. UART and PPS stay at 3.3 V logic, because the module runs from the LDO. Bench-measure DC at P7 under a 20 mA load, accepting at least 3.05 V. If it fails, use the external-bias fallback (see the next correction). Never bridge R5.
    - **Impact:** Removes a probable out-of-spec LNA supply for the GNSS antenna. $0.
    - **Sources:**
      - https://www.richtek.com/assets/product_file/RT9193/DS9193-18.pdf
      - https://files.waveshare.com/wiki/LC76G/manual/LC76G%20GNSS%20Module.pdf
      - https://www.waveshare.com/wiki/LC76G_GNSS_Module
      - https://www.waveshare.com/LC76G-GNSS-Module.htm
  2.
    - **Claim in stack:** Stage 1/2 fallback: bias P7 from the 4.5 V injector 'with a DC block toward the LC76G RF_IN'.
    - **Finding:** The module's RF_IN already has a 100 pF DC block (C6). The hazard is elsewhere: the board's L1 68 nH + R5 10 ohm network ties the IPEX line to VCC_RF = 3.3 V. If 4.5 V is injected on the antenna side without a block ahead of the IPEX, about 117 mA (model) back-drives into VCC_RF and the LDO output.
    - **Verdict:** corrected
    - **Action:** If external bias is ever needed, do it this way: TPS2553 channel, then bias tee at P7, then an inline SMA DC block placed between the bias tee and the IPX pigtail of the board. With external bias, LC76G antenna-status reporting is no longer meaningful.
    - **Impact:** Prevents a 4.5 V-to-3.3 V back-feed. About $5-10 for an SMA DC block, only if the fallback is used.
    - **Sources:**
      - https://files.waveshare.com/wiki/LC76G/manual/LC76G%20GNSS%20Module.pdf
  3.
    - **Claim in stack:** 2.4: 'GNSS L1+L5 (25346)'; 'lead 1-3 m'. Stage 1/2: 'no GLONASS'.
    - **Finding:** The vendor page confirms a fixed 3 m RG174 lead ('supports mass customization' only on bulk orders); that is about 3.6 dB at L1, covered by the 28 dB LNA. The text band list omits GLONASS. However, the vendor's own detail image GPS-External-Antenna-D-details-7.jpg (an S21 plot) has a marker at 1.602 GHz reading 39.09 dB, next to 1.5754 GHz at 37.93 dB. So the LNA chain passes GLONASS G1. Two inconsistencies: the plot's 37-41 dB conflicts with the text's 28±2 dB, and its markers at 1.227/1.268 GHz suggest a generic LNA plot. The patch element's response at G1 is unpublished.
    - **Verdict:** corrected
    - **Action:** Describe it as 'L1 antenna, L5 unused; 3 m RG174 fixed; GLONASS not listed but the LNA plot covers 1.602 GHz; confirm by LC76G GLONASS C/N0'. Coil the excess lead away from the USB 3, HDMI and DC-DC edge. Use 28 dB in budgets.
    - **Impact:** Wording, plus one receive-only bench check. The ANN-MB5 is no longer needed just for GLONASS.
    - **Sources:**
      - https://www.waveshare.com/gps-external-antenna-d.htm
      - https://www.waveshare.com/img/devkit/accessories/GPS-External-Antenna-D/GPS-External-Antenna-D-details-7.jpg
  4.
    - **Claim in stack:** 2.4 'Budget alternative: u-blox ANN-MB5 $42.50 (more expensive)'.
    - **Finding:** It is not a budget item. With an LNA of only 15±3 dB, the model system NF is 2.3-3.0 dB, against about 2.0 dB for the 25346 (LC76G NF assumed at 3-5 dB). The ANN-MB5's 4.5 dBic is measured on a 12 cm ground plane, while the 25346's '2 dBi' has no condition stated. The net advantage is about +2 dB (model, low confidence). Its real advantages are SAW filtering ahead of the LNA (45 dB below 1459 MHz, 35-45 dB at cellular bands) and a specified 1559-1608 MHz L1 band. It has the same 3.0 V minimum and no reverse or overvoltage protection.
    - **Verdict:** corrected
    - **Action:** Relabel it 'robustness option (pre-LNA SAW, specified GLONASS), +$25.51'. Use it with a ground plane of at least 10-12 cm and the same P7 bias check.
    - **Impact:** Optional +$25.51. No sensitivity case for it.
    - **Sources:**
      - https://cdn.sparkfun.com/assets/0/b/a/5/2/ANN-MB5_Datasheet.pdf
      - https://www.sparkfun.com/u-blox-multi-band-active-gnss-antenna-l1-l5-ann-mb5.html
  5.
    - **Claim in stack:** #111: W9MDB at 146 MHz (A-V85 -0.8 dB etc.) justifies the A-V85/SRH-701 as the 70 cm whip.
    - **Finding:** The wrong column is used for a 70 cm claim. The 435 MHz column (uncalibrated) puts the A-V85 about 8.7 dB and the NA-701 about 10.4-12.5 dB below the NA-771. The test is a terrestrial HT link held near the face, which says nothing about satellite reception. The SRH-701 was never measured.
    - **Verdict:** corrected
    - **Action:** In #111, quote the 435 MHz column with its caveat, or drop W9MDB as 70 cm evidence. No source gives a measured gain for any small 70 cm whip on a handheld.
    - **Impact:** The tilted-whip CubeSat margins (-5.3 to +5.3 dB) are unsupported by measurement. This is the case for the dipole default.
    - **Sources:**
      - https://www.miklor.com/COM/pdf/AntennaTestingW9MDB.pdf
  6.
    - **Claim in stack:** 2.4 / 5.3 / 4.1: 70 cm antenna = DIY 17 cm, Diamond SRH-701 or Baofeng A-V85, screwed onto the Uputronics 440 on P2; 'needs your confirmation'.
    - **Finding:** New default: the dipole kit's short elements fully extended, about 14 + 2 cm per side, resonant near 445 MHz per the vendor. The base lead is 60 cm RG174, SMA male, with a ferrite choke, and plugs straight into the Uputronics ANT port (SMA female). Model at 437.5 MHz: mismatch 0.22-0.32 dB (Q 6-10), lead 0.38-0.57 dB, so net +1.3 to +1.5 dB over a 0 dBi whip. The whip's gain is itself unmeasured. The kit is telescopic (folding), so it is rule-compliant and needs no user confirmation. RTL-A serves both VHF-137 and UHF through one SP4T, so LRPT and 70 cm never run at once; kit #2, by contrast, sits on HF+ for AIS, which can run concurrently. Kit #1's base is therefore the one to reuse. The A-V85 is likely SMA female (Baofeng convention), has no current listing found, and measured poorly at UHF.
    - **Verdict:** corrected
    - **Action:** Patch-tier 70 cm default: kit #1's base re-fitted with its short elements, fully extended, straight (180°), broadside to the pass, lead into the Uputronics 440. Doppler tracking on. Optional third kit (+$17.95) to avoid swapping elements between LRPT and UHF passes. Fallback: SRH-701 (about $19.00) or a DIY 17.1 cm whip on SMA-M. Delete the A-V85 from 2.4, 4.1 and the 5.3 2 m row (keep the SRH-701 there). Do not hang the Uputronics plus whip off the P2 bulkhead; use a short SMA M-F jumper or a bracket. Open question 3 then shrinks to the whip and the helix.
    - **Impact:** Subtotal 175.79-201.79 (A-V85 dropped; the whip row becomes DIY $3 to SRH-701 $19.00). +$17.95 if a third kit is bought. Margin about +1.3-1.5 dB (model). The antenna also moves 60 cm away from the device's own noise.
    - **Sources:**
      - https://www.rtl-sdr.com/using-our-new-dipole-antenna-kit/
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://www.wimo.com/en/srh-701
      - https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf?v=1729257808
  7.
    - **Claim in stack:** D8 / 5.3: 'Uputronics 440 MHz CubeSAT filtered preamp (LNA, then SAW 30 MHz)'.
    - **Finding:** The vendor's 440 MHz plot (marked UNCAL) reads 19.63 dB at 440 MHz, with markers at 427.33 MHz (16.27 dB) and 452.0 MHz (16.17 dB). That is about 25 MHz between the -3.4 dB points, flat across 435-438 MHz. The 434 MHz variant reads 20.25 dB at 434 MHz and 16.08 dB at 437.67 MHz (-4.2 dB), so it is too narrow for 437.55-437.825.
    - **Verdict:** corrected
    - **Action:** Write 'SAW passband about 427-452 MHz (-3.4 dB, vendor plot)'. Never substitute the GBP 41.99 434 MHz variant.
    - **Impact:** Wording only. Blocks a false economy.
    - **Sources:**
      - https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf?v=1729257808
      - https://store.uputronics.com/products/uputronics-filtered-preamps
  8.
    - **Claim in stack:** #82: 'USB 3 jams GNSS within about 2 m'.
    - **Finding:** Supported only by community anecdote (OpenMarine 2020-21: trouble at 0.9 m, relief at 1.8 m, a fix at 1.5 m; USB 2 mode or shielding cured it). No C/N0 data exist.
    - **Verdict:** corrected
    - **Action:** Label the 2 m figure as 'community rule of thumb (OpenMarine 2020-21)'. Keep the C/N0 on/off acceptance at ≤1 dB-Hz. If it fails, run storage at USB 2 speed during GNSS-critical work, or shield the drive and its cable.
    - **Impact:** Evidence wording only. Adds a free fallback.
    - **Sources:**
      - https://forum.openmarine.net/printthread.php?tid=3062
  9.
    - **Claim in stack:** 4.1 Inmarsat-C row: 'RF covered (rtl-sdr.com reports decoding with the patch)'.
    - **Finding:** Several community STD-C receptions exist (TechMinds, Bert, DK8OK per stage 2). The vendor publishes no LNA gain or NF. The vendor requires at least 1 m of coax between the patch and the SDR.
    - **Verdict:** corrected
    - **Action:** Reword to 'community decodes (TechMinds 2019, blog comments); vendor gain/NF unpublished'. Run the patch on its 2 m lead at least 1 m from the device. Add a pointing step before demodulation: IMU az/el, then a hand sweep of tilt and rotation on the live power-only NCS C/N0, then lock the tripod.
    - **Impact:** Wording, plus a cheap operating step that can decide a marginal decode.
    - **Sources:**
      - https://www.rtl-sdr.com/techminds-reviews-our-rtl-sdr-blog-l-band-patch-antenna-horn-dish-mod/
      - https://www.rtl-sdr.com/preorder-sale-active-l-band-1525-1660-inmarsat-and-iridium-patch-back-in-stock-for-44-95/
  10.
    - **Claim in stack:** (new option) Passive gain for the patch tier on Inmarsat-C.
    - **Finding:** One user (Bert) put a horn made from half a foil-lined 1 L drink box, plus a back-plate reflector, over the patch. AERO 10500 SNR rose from 8-9 dB to 12-14 dB, about +4-5 dB. This is anecdotal and from one user; the AERO reading is RF evidence only. A folding aluminium shroud (pieces ≤20 cm) is not a dish, and STACK already accepts segment horns.
    - **Verdict:** new_option
    - **Action:** Optional DIY item, under $5: 4 flat sheets of about 10 x 15 cm plus a back plate. Put it on the user-confirmation list. Accept it only after a receive-only before/after test on NCS C/N0.
    - **Impact:** Possible +4 dB (anecdotal).
    - **Sources:**
      - https://www.rtl-sdr.com/techminds-reviews-our-rtl-sdr-blog-l-band-patch-antenna-horn-dish-mod/
- **New risks:**
  - The LC76G board is fed 3.3 V on VCC, so its RT9193 is in dropout. The model puts the GNSS antenna LNA at 2.91-3.04 V at 20 mA, below its 3.0 V minimum (cold starts and low C/N0 likely at the margin). Fix: VCC from 5 V. See corrections.
  - External bias on P7 without a DC block between the bias tee and the board's IPEX would back-feed about 117 mA into VCC_RF (model). A short at the IPEX through R5 would draw about 0.32 A and dissipate about 1 W in R5, which would likely fail open. The RT9193 limit is 360-400 mA, so R5 is not the only current limit, but bridging R5 is still forbidden.
  - In-band uplinks: the patch's SAW passband (1525-1660 MHz) contains the Iridium (1616-1626.5 MHz) and Inmarsat terminal uplink (1626.5-1660.5 MHz) bands. A transmitting ship, aircraft or BGAN terminal nearby is unfiltered and can saturate the patch LNA or the 8-bit RTL-B. Magnitude unverified; this matters most at sea or near terminals.
  - Adjacent and in-band terrestrial networks. EU LTE Band 75 SDL is 1432-1517 MHz (deployments on Band 32 in IT, UK, DE and LV per Wikipedia); Japan Bands 11/21 reach 1510.9 MHz; US Band 74 downlink is 1475-1518 MHz. All of these reach the patch's LNA ahead of its SAW. US Band 24 (1526-1536 MHz, Ligado) is in-band and cannot be filtered at all. Ligado's 2026 deployment status is unverified. Log 1.43-1.52 GHz and 1.616-1.66 GHz power next to NCS C/N0 and relocate if the floor rises. https://en.wikipedia.org/wiki/LTE_frequency_bands
  - The Uputronics 440 passes no signal when unpowered. A DC-sense fault or a bias-token refusal on ch2 therefore looks like 'dead band'. The UI must say so.
  - Dipole kit QC: about 1.7 % defect rate (vendor), including damaged M5 threads and braid strands touching the other element (a center-shield short). Commenters also say the ferrite choke sits too far down the lead. Check on arrival.
  - The 25346 magnet near the BNO085 pack: problem seen at 9 cm and gone at 15 cm (ArduPilot). Keep the puck at least 30 cm away or use tape.
  - Unverified: RTL-SDR Blog patch LNA gain, NF, SAW edges and housing connector gender; the 25346's patch response at GLONASS G1 and its out-of-band rejection; any measured gain for any small 70 cm whip on a handheld; A-V85 availability; whether the dipole kit's Amazon USA line ('out in stock') means in stock.
- **Refuted findings:**
  1.
    - **Finding:** Stage 2: 'Honeywell says terrestrial 5G/LTE networks in this spectrum (CEPT SDL 1452-1492 MHz) can cause interference to Inmarsat L-band receivers.'
    - **Why:** The Honeywell Type J page says the FCC authorised spectrum previously used for satcom for terrestrial ATC/5G, and that it 'overlaps the receive band of the Inmarsat L-Band spectrum'. That is the US in-band case (Band 24, downlink restricted to 1526-1536 MHz), and the page names no SDL frequencies. The EU risk is adjacent SDL: Band 75 at 1432-1517 MHz, the closer edge, rather than 1452-1492. Re-attributed under new_risks.
  2.
    - **Finding:** Stage 2: 'R5 is the only current limit on the antenna feed.'
    - **Why:** The RT9193 datasheet gives a 360-400 mA current limit. R5 restricts a short to about 0.32 A but would dissipate about 1 W. The conclusion (do not bridge R5) survives; the reasoning does not.
  3.
    - **Finding:** Stage 1/2: 'The 25346 band list does not include GLONASS' (taken as no GLONASS coverage).
    - **Why:** Only the text list omits it. The vendor's own S21 image marks 1.602 GHz at 39.09 dB, so the LNA passband covers G1. The patch-element response is unknown, so the result is downgraded to 'verify by C/N0'.
  4.
    - **Finding:** Stage 2: 'Set the 70 cm dipole length by tape: about 16.3 cm per side including the 2 cm inside the base.'
    - **Why:** That needs about 14.3 cm of extension, but the kit's short elements reach 13 cm per the listing or 14 cm per the cheat sheet (445 MHz). The only achievable setting is fully extended. The model mismatch at 437.5 MHz is then only 0.22-0.32 dB.
  5.
    - **Finding:** Stage 1: 'Reuse kit #2 between AIS sessions' for 70 cm.
    - **Why:** Kit #2 feeds HF+ for AIS, which STACK runs at the same time as RTL-A. Kit #1 (LRPT) shares RTL-A with the UHF port through the SP4T, so it is never in use during a UHF pass. Reuse kit #1.
  6.
    - **Finding:** Stage 1: 'The Uputronics 434 MHz HABAmp/CubeSAT/ISM variant (GBP 41.99) is cheaper'; its bandwidth was unchecked.
    - **Why:** The vendor plot shows 437.67 MHz at 16.08 dB against 20.25 dB at 434 MHz, which is -4.2 dB at the ISS, CubeSat and APRS channels. Unsuitable.
  7.
    - **Finding:** Stage 1: 'Uputronics page says bias-tee input is 5 V' (possible conflict with 4.5 V).
    - **Why:** Datasheet Rev 3.0 gives 3.5-5.5 V. 4.5 V on ch2 is in range.
  8.
    - **Finding:** Stage 1: an aggregator says the ANN-MB5 is 'obsolete'.
    - **Why:** Datasheet R03 says 'Mass production', and SparkFun shows 'In stock' at $42.50 on 18 Oct 2026.
  9.
    - **Finding:** Stage 1 'reliable' ISS SSTV on the whip; stage 1/2 dipole '+1 to +2 dB'.
    - **Why:** Both are models. The dipole delta is trimmed to +1.3-1.5 dB, relative to a whip gain no source has measured. 'Reliable' stays labelled as a model until a Series 34 pass is decoded with Doppler tracking on.
- **Corrected spec:** ## Patch/chip tier antennas (v1, corrected 18 Oct 2026)
  
  ### 1. GNSS (P7)
  - **Antenna:** Waveshare 25346 'GPS External Antenna (D)', $16.99.
    - RHCP, 2 dBi, LNA 28±2 dB, NF ≤2 dB.
    - 3.0-18 V, ≤20 mA.
    - Fixed 3 m RG174 (about 3.6 dB at L1, model from u-blox's measured RG174 loss).
    - SMA-J plug.
  - **Chain:** P7 is an SMA-K (female) bulkhead, then an IPX pigtail to the Waveshare LC76G 24370 IPEX connector.
  - **Use:** L1 only. The LC76G tracks GPS L1 C/A, GLONASS L1, Galileo E1, BDS B1I/B1C and QZSS; L5 is unused. GLONASS is not listed on the antenna, but the vendor's LNA plot covers 1.602 GHz; confirm by C/N0.
  - **Board supply:** LC76G board VCC from 40-pin **5 V** (not 3V3), so the RT9193-33 regulates. Expected antenna bias is 3.06-3.19 V at 10-20 mA (model). Bench acceptance: at least 3.05 V at P7 under a 20 mA load.
  - **Fallback bias:** TPS2553 channel, then bias tee at P7, then an inline SMA DC block between the bias tee and the board's IPX pigtail. Never bridge R5. Never connect a DC-shorted antenna.
  - **Placement:**
    - Tape mount, or magnet at least 30 cm from the BNO085 pack.
    - About 1-2 m from USB 3, HDMI and DC-DC (community rule of thumb).
    - Acceptance: C/N0 on/off at ≤1 dB-Hz.
    - The LC76G's included active ceramic antenna goes on the lid only after it passes the same test.
  - **Option:** u-blox ANN-MB5-00 (SparkFun GPS-25071, $42.50, +$25.51).
    - Bands: L1 1559-1608 MHz and L5 1164-1186 MHz.
    - SAW ahead of the LNA: 45 dB below 1459 MHz, 35 dB above 1708 MHz.
    - LNA 15±3 dB, NF 2.0 dB; 3.0-5.0 V, 17 mA; no reverse or overvoltage protection.
    - 4.5 dBic on a 12 cm ground plane, so it needs a ground plate of at least 10-12 cm.
    - Choose it for robustness, not sensitivity (model system NF 2.3-3.0 dB, against about 2.0 dB for the 25346).
  
  ### 2. L-band (P3, ch3 at 4.5 V, 4.30 V since v2.1, after DC-sense, which accepts 15-20 mA)
  - **Antenna:** RTL-SDR Blog Active L-Band 1525-1660 MHz Patch Antenna Set, v2 (gray), $59.95 (buy page add-to-cart 35592; AliExpress 4000311955837).
    - RHCP; 175x175 mm patch; LNA then SAW.
    - 3.3-5 V, 15-20 mA (20 mA maximum).
    - 2 m RG174 extension: 2.4 dB at 1541 MHz (model), up to 3.6 dB for the copper-clad-steel type.
    - Tripod (preferred) and suction cup.
  - **Siting:** keep at least 1 m of coax between the patch and the device (vendor).
  - **Pointing:** IMU az/el, then a hand sweep of tilt and rotation on the live power-only NCS C/N0, then lock the tripod.
  - **Uses:**
    - Inmarsat-C EGC SafetyNET via labd egc-gate only, with a power-only scan of 1537-1545 MHz and no fixed channel table.
    - GNSS-SDR on RTL-B as a bring-up test only.
  - **Excluded:**
    - HRPT and GOES (vendor).
    - AERO, Iridium and full STD-C decoders.
  - **Logging:** record 1.43-1.52 GHz and 1.616-1.66 GHz power alongside NCS C/N0 (adjacent SDL and in-band uplink blockers).
  - **Optional, user confirmation needed:** folding aluminium shroud plus back plate (pieces ≤20 cm), anecdotal +4-5 dB.
  
  ### 3. 70 cm (P2, ch2 at 4.5 V, 4.30 V since v2.1, after DC-sense, which accepts about 50 mA)
  - **Preamp:** Uputronics Filtered Preamp, 440 MHz CubeSAT variant, GBP 51.59 (about $68.71).
    - 3.5-5.5 V, about 50 mA; NF 0.75 dB; gain at least 19 dB.
    - Passband about 427-452 MHz at -3.4 dB (vendor plot).
    - LNA before the SAW; limiter; HPF below 100 MHz.
    - ANT port DC-blocked; no passthrough when unpowered.
    - SMA-F both ports; 69x40x12 mm.
    - Mount on a short SMA M-F jumper or bracket, not cantilevered on P2.
    - Never substitute the 434 MHz variant.
  - **Default antenna:** RTL-SDR Blog dipole kit #1's base (reused, $0; RTL-A is time-shared).
    - The two 5-13 cm elements fully extended (about 14 + 2 cm per side, about 445 MHz resonance).
    - Straight 180°, broadside to the pass.
    - 60 cm RG174 lead (SMA-M, ferrite choke) straight into the ANT port.
    - Model: mismatch 0.22-0.32 dB, lead 0.38-0.57 dB, net about +1.3-1.5 dB over a 0 dBi whip.
    - Optional third kit: +$17.95.
  - **Fallback antennas:** Diamond SRH-701 (WiMo SKU 17039, EUR 16.90, about $19.00; SMA-M, 19 cm, 26 g; vendor 3 dBi at 432 MHz, unmeasured) or a DIY 17.1 cm λ/4 whip on SMA-M.
  - **A-V85:** removed everywhere (SMA-F, no listing found, poor UHF result).
  - **ISS SSTV (437.55 MHz, Robot 36):** Doppler tracking required. Without it the filter must be about 36 kHz wide, which costs about 3.8 dB (model).
  
  ### 4. Chips and physics limits
  - No chip in any VHF or UHF chain. Johanson 0433AT62A0020002U Rev 4.0 is -4.0 / -6.8 dBi.
  - Patch and chip antennas cannot serve 137-146 MHz or HRPT. A half-wave patch at 137.9 MHz is 51.8 cm (er 4.4) or 24.3 cm (er 20). The aperture limit at 1.70 GHz is 7.65 dBi for 12 cm and 12.09 dBi for 20 cm.
  
  ### 5. Group subtotal
  - 175.79-201.79 USD with the A-V85 dropped (whip row $3-19.00).
  - +$17.95 with a third dipole kit.
  - +$25.51 with the ANN-MB5.
  
  ### 6. Rule status
  - The L-band patch, GNSS puck, LC76G ceramic antenna and dipole kit (telescopic) are compliant; none is a loop and none is a dish.
  - Only the rigid SRH-701 or 17 cm whip, the 4-turn helix (not assessed here) and the optional shroud stay on the user-confirmation list.
- **Bench tests:**
  - P7 DC margin. With the LC76G VCC on 3V3, then on 5 V, put a 150 ohm DC load (about 20 mA at 3.0 V) on P7 and read the volts; then repeat with the 25346 connected through an SMA DC-pass tee. Accept at least 3.05 V. Also read LC76G VCC at the module, expecting 3.26 V on 3V3 and 3.30 V on 5 V. DC only, nothing radiated.
  - GNSS C/N0 acceptance (receive-only, LC76G GSV, open sky, 10 min each). Step 1: 25346 against the LC76G's included ceramic antenna, and against the ANN-MB5 if bought. Step 2: USB 3 SSD idle versus streaming, and HDMI or display off versus on. Accept ≤1 dB-Hz loss. If it fails, repeat with the drive in USB 2 mode or shielded. Record per-constellation C/N0, including GLONASS, to settle the 25346 G1 question.
  - Magnet check: BNO085 heading change with the 25346 puck at 10, 20 and 30 cm in four orientations. Accept less than 1°, otherwise use the tape mount.
  - L-band patch on arrival: inspect the case seal and screw bosses and record the connector gender. With ch3 at 4.30 V (v2.1; was 4.5 V), check that DC-sense reads 15-20 mA.
  - L-band patch noise-floor step on RTL-B T1 (receive-only): first a 50 ohm load at P3, then the patch powered and aimed at clear sky away from the GEO arc, on the 2 m lead at least 1 m from the device. A step of 8 dB or more shows the patch LNA dominates the chain NF.
  - Inmarsat-C acquisition (receive-only, power-only). Run the 1537-1545 MHz scan with IMU az/el, then sweep tilt and rotation by hand and lock at peak NCS C/N0. Log NCS C/N0 together with 1.43-1.52 GHz and 1.616-1.66 GHz band power. Repeat at a second site near an LTE/NR SDL cell if one is known. Demodulate only through egc-gate after its mixed-recording test.
  - Dipole kit on arrival (DC ohmmeter, no RF). Centre to shield must read open (>1 MΩ), each element must have continuity to its own conductor, and the M5 threads must engage cleanly.
  - Uputronics 440, conducted bench only. Check that DC-sense reads about 50 mA at 4.30 V (v2.1; was 4.5 V). Use the tinySA as a source at ≤ -40 dBm into the ANT port (Bench mode, 50 ohm terminations, conducted) to check gain of at least 19 dB at 437.5 MHz and the -3 dB edges near 427/452 MHz. Check that unpowered, the path is heavily attenuated.
  - 70 cm A/B (receive-only, on air) during ISS SSTV Series 34, 22-25 Oct 2026, 437.55 MHz, Doppler tracking on. Alternate the kit #1 short-element dipole and the SRH-701 on the Uputronics on successive passes, or on beacons in the same pass, and log carrier SNR at matched elevation. Adopt the dipole as default if it is at least 0 dB better; record the decoded image as the first field confirmation of 'reliable'.
  - Optional shroud (only if the user approves it): NCS C/N0 before and after fitting, same pointing procedure; keep it only if the gain is at least 2 dB.
- **Confidence:** medium

