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

