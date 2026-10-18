# Додаткові дослідження: повні відповіді субагентів

## small:lband_sband (run `wf_41027870-8e7`)

- **Band group:** L-band 1.5-1.7 GHz and S-band 2.2-2.4 GHz with antennas of at most 12 cm (STRICT) or 20 cm (SMALL). Dishes and anything tens of cm deployed are EXCLUDED, including the foldable helicones, the 11-turn helix and the 2x2 helix arrays. Rule interpretation as given: STRICT means the largest deployed dimension is about 12 cm or less; SMALL means about 20 cm or less; foldable or telescopic antennas that are larger when deployed are excluded and appear only in the borderline note.
- **Small antennas:**
  1.
    - **Name:** DIY 'universal' 2-turn RHCP axial helix for L-band on a 12 cm aluminium disc
    - **Type:** diy
    - **Band:** 1525-1710 MHz from one antenna: Inmarsat-C 1537-1545, GNSS L1 1575, Iridium 1618-1626.5, HRPT 1700-1707
    - **Size cm:** Helix 6.2 cm diameter (C = 1.1λ at 1.70 GHz), 43 mm pitch, about 9 cm tall, on a 12 cm disc. Largest dimension 12 cm, so STRICT.
    - **Gain or efficiency:** My NEC2 model (PyNEC, same code as foldable_partial.json) gives RHCP 7.99 / 8.05 / 8.16 / 8.32 / 8.59 dBic at 1525 / 1542 / 1575 / 1621 / 1700 MHz, with cross-polar 11-12 dB down. The same code models the 11-turn helix about 1.2 dB above its field anchor (13.98 vs 12.75 dBic), so expect roughly 7-7.4 dBic on air. Feed impedance is about 140-160 Ω -j55, so it needs a matching strip or a quarter-wave transformer to 50 Ω. At 9 cm it is not electrically short (0.5λ): conductor loss is under 0.1 dB, and the limit is directivity, not efficiency. Beam about 60-70°, so it is easy to hand-point.
    - **Price:** About $5-10 in copper wire, aluminium disc and PETG former (estimate). Add one band LNA: Nooelec SAWbird+ iO (1542 MHz), SAWbird+ IR (1620 MHz) or SAWbird+ GOES (1688 MHz), each $49.95 (dual-LNA and Barebones versions $44.95) on today's Nooelec listing.
    - **Availability incl ukraine:** Materials are local hardware-store items in Ukraine. Nooelec ships internationally (Ukraine delivery not verified). The SAWbird+ GOES already in the stack covers only about 1648-1728 MHz, so Inmarsat and Iridium need the iO or IR variant, or a wideband LNA where there is no strong LTE nearby.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lband_small/scripts/helix_univ.py
      - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird.html
  2.
    - **Name:** DIY 2-turn or 3-turn RHCP helix for S-band on a 12 cm disc
    - **Type:** diy
    - **Band:** 2.2-2.45 GHz (S-band CubeSats and science downlinks at 2.2-2.3 GHz, amateur 2.40-2.45 GHz)
    - **Size cm:** Helix 4.7 cm diameter, 32.5 mm pitch. 2 turns is 6.9 cm tall, 3 turns is 10.1 cm tall, on a 12 cm disc. STRICT.
    - **Gain or efficiency:** NEC2 model: 2 turns 8.97 dBic at 2.25 GHz and 9.37 at 2.40 GHz; 3 turns 9.75 and 10.29. Allow about -1 dB for real builds. A 3 cm cup rim changes it by 0.1 dB or less, so it is not worth adding. The aperture of a 12 x 12 cm broadside antenna caps it at 10.1 dBi (2.25 GHz). An end-fire helix can slightly exceed that because its length counts.
    - **Price:** About $3-5 in materials (estimate). Plus an S-band LNA and a Sysmocom cf2235-kt30 cavity (2170-2300 MHz, EUR 65.45) for 2.2-2.3 GHz, or a 2.4 GHz band-pass filter for the amateur band.
    - **Availability incl ukraine:** DIY with local materials. Sysmocom ships within the EU; forwarding to Ukraine not verified.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lband_small/scripts/helix_small.py
      - https://shop.sysmocom.de/S-Band-cavity-filter-2170-2300-MHz/cf2235-kt30
  3.
    - **Name:** DIY air-dielectric corner-truncated RHCP square patch on a 12 cm plate
    - **Type:** diy
    - **Band:** One band per patch: about 1541 MHz (Inmarsat), 1621 MHz (Iridium) or 1700 MHz (HRPT)
    - **Size cm:** Patch about 9.0 cm (1.54 GHz) or about 8.3 cm (1.70 GHz), 6-8 mm air gap, 12 x 12 cm ground plate, about 1.5 cm thick. STRICT.
    - **Gain or efficiency:** Estimate 6-7.5 dBic. The 12 x 12 cm aperture limit at 100% efficiency is 6.8 dBi at 1.54 GHz and 7.6 dBi at 1.70 GHz (calculation). With a single truncated-corner feed the axial ratio stays under 3 dB over only about 1-2% (about 20-30 MHz), so one patch cannot cover Inmarsat, Iridium and HRPT. I did not model it, and the helix above beats it at the same size.
    - **Price:** About $3-8 (aluminium or copper sheet, nylon spacers, SMA) (estimate)
    - **Availability incl ukraine:** DIY, local materials
    - **Sources:**
      - https://ntrs.nasa.gov/api/citations/19670009367/downloads/19670009367.pdf
  4.
    - **Name:** Generic active GPS 'puck' with its 1575 MHz band-pass filter bridged (rtl-sdr.com method)
    - **Type:** modify
    - **Band:** Inmarsat-C 1537-1545 MHz (off-tune); GNSS L1
    - **Size cm:** About 4-5 cm puck, 25 mm ceramic patch. STRICT.
    - **Gain or efficiency:** Not published. The ceramic patch is tuned to 1575 MHz with about 10-20 MHz bandwidth, so at 1541 MHz it is mismatched (estimate -2 to 0 dBic). rtl-sdr.com: the modified GPS antenna is 'just on the edge of being able to decode' STD-C NCS. Bridge the filter marked '1575'/'1575P' with wire, or with about 100 pF if it sits between amplifier stages with no DC block.
    - **Price:** Low (a few dollars); Ukrainian prices not verified
    - **Availability incl ukraine:** Widely sold in Ukraine (Prom.ua/Rozetka class listings; specific listing not verified). Needs 3-5 V bias, for example from the RTL-SDR V4L bias tee.
    - **Sources:**
      - https://www.rtl-sdr.com/rtl-sdr-tutorial-decoding-inmarsat-std-c-egc-messages/
  5.
    - **Name:** Waveshare LC76G GNSS board with its own active antenna (already in the stack)
    - **Type:** buy
    - **Band:** GNSS L1: GPS, GLONASS, Galileo, BeiDou, QZSS
    - **Size cm:** Small ceramic active antenna supplied with the board, a few cm. STRICT.
    - **Gain or efficiency:** Not published (typical small active ceramic patch). Fit for timing and position. Spoofing and jamming in Ukraine are the real limit, not antenna gain.
    - **Price:** $14.99 direct; 1,344-1,502 UAH on Prom.ua (made to order), per gnss_imu.json
    - **Availability incl ukraine:** Prom.ua (made to order), per gnss_imu.json
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/gnss_imu.json
  6.
    - **Name:** RTL-SDR Blog active L-band patch (1525-1660 MHz)
    - **Type:** buy
    - **Band:** Inmarsat 1525-1559, GNSS L1, Iridium 1616-1626.5. NOT 1.70 GHz HRPT.
    - **Size cm:** Patch 17.5 x 17.5 cm (vendor page). This puts it in SMALL, not STRICT.
    - **Gain or efficiency:** Gain not published. RHCP, built-in LNA followed by a SAW filter, 3.3-5 V bias tee at about 20 mA maximum (admin comment), 'higher gain and wider radiation pattern' than the old model. The vendor says it 'cannot' be used for weak signals that need a dish, such as HRPT or GOES. thebaldgeek ranked GPS puck < this patch < 7-turn helix < Discovery Dish on Inmarsat. SA2KNG called it 'not super strong'.
    - **Price:** $59.95 at the RTL-SDR store per the October 2026 audit (antennas.json); earlier pre-order $44.95 with free worldwide shipping to most countries
    - **Availability incl ukraine:** RTL-SDR Blog store and official AliExpress store. Delivery to Ukraine not verified.
    - **Sources:**
      - https://www.rtl-sdr.com/preorder-sale-active-l-band-1525-1660-inmarsat-and-iridium-patch-back-in-stock-for-44-95/
      - https://community.airframes.io/t/discovery-dish-rtlsdr-blog-l-band-acars/181
      - https://community.libre.space/t/equipment-for-l-band-and-s-band-rx/11031
  7.
    - **Name:** DIY 4-turn RHCP L-band helix on a 20 cm disc
    - **Type:** diy
    - **Band:** 1525-1710 MHz (same helix geometry as the strict 2-turn)
    - **Size cm:** Helix 6.2 cm diameter, 17.6 cm tall, on a 20 cm disc. SMALL.
    - **Gain or efficiency:** NEC2 model: 10.20 / 10.27 / 10.40 / 10.59 / 10.92 dBic at 1525 / 1542 / 1575 / 1621 / 1700 MHz. Allow about -1.2 dB on air (about 9.7 dBic at 1.7 GHz). A 3-turn helix on a 20 cm disc (13.3 cm tall) models 10.23 dBic at 1.70 GHz. The 20 x 20 cm broadside aperture limit is 12.1 dBi at 1.70 GHz.
    - **Price:** About $5-12 plus a SAWbird+ GOES (in stack) or iO/IR ($49.95)
    - **Availability incl ukraine:** DIY, local materials
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lband_small/scripts/helix_univ.py
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lband_small/scripts/helix_small.py
  8.
    - **Name:** DIY 4-turn RHCP S-band helix on a 20 cm disc
    - **Type:** diy
    - **Band:** 2.2-2.45 GHz
    - **Size cm:** Helix 4.7 cm diameter, 13.4 cm tall, on a 20 cm disc. SMALL.
    - **Gain or efficiency:** NEC2 model: 11.43 dBic at 2.25 GHz and 11.63 at 2.40 GHz; a 3-turn models 10.85 / 11.13. Allow about -1 dB on air. Aperture limit for 20 x 20 cm is 14.5 dBi (2.25 GHz).
    - **Price:** About $3-8 plus the S-band LNA and cavity (as above)
    - **Availability incl ukraine:** DIY
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lband_small/scripts/helix_small.py
  9.
    - **Name:** DIY 2x2 air-patch array on a 20 x 20 cm board with a Wilkinson or branch-line feed
    - **Type:** diy
    - **Band:** L (1.54-1.70 GHz) or S (2.2-2.3 GHz), one design per band
    - **Size cm:** 20 x 20 x 1.5 cm. SMALL. Element spacing is only about 0.57λ at 1.70 GHz.
    - **Gain or efficiency:** Estimate 10-11 dBic at 1.70 GHz and 12-13 dBic at 2.25 GHz, against aperture limits of 12.1 and 14.5 dBi. No tested 1.7 GHz RHCP 2x2 design or Gerber was found, and it is no better than the 4-turn helix of the same size.
    - **Price:** About $15-40 (estimate)
    - **Availability incl ukraine:** DIY only
    - **Sources:**
      - https://oar.a-star.edu.sg/communities-collections/articles/19720
  10.
    - **Name:** YUST 4G LTE MIMO 2x17 dBi panel, 200 x 200 x 40 mm (or the R-Net 'Kvadrat' 2x17, 205 x 205 x 50 mm)
    - **Type:** modify
    - **Band:** Sold for 1700-2700 MHz LTE (the YUST listing title does not state the band). Usable for HRPT at the 1.70 GHz band edge and for S-band.
    - **Size cm:** 20 x 20 x 4 cm (YUST) / 20.5 x 20.5 x 5 cm (R-Net). SMALL, at the 20 cm limit.
    - **Gain or efficiency:** '17 dBi' is impossible for this aperture, which caps it at 12.1 dBi at 1.70 GHz and 14.5 dBi at 2.25 GHz. Realistic is about 10-11 dBi linear per port at 1.7 GHz and 11-13 at 2.25 GHz (foldable_partial.json). On RHCP satellites one port loses 3 dB (about 7-8 dBic-equivalent). Both ports through a DIY 90° branch-line hybrid recover about 10 dBic. Measure the match at 1.70 GHz with a VNA.
    - **Price:** YUST 1,018 UAH; R-Net 1,900 UAH (Prom.ua). Connectorised hybrids cost $504 or more, so build a DIY branch-line coupler.
    - **Availability incl ukraine:** In stock on Prom.ua (Ukraine), checked 18 Oct 2026
    - **Sources:**
      - https://prom.ua/Antenny-mimo-2x2.html
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_partial.json
- **Satellites:**
  1.
    - **Satellite:** Inmarsat-C network control station (NCS) common channel. For Ukraine: Alphasat (logical IOR, migrated to 'Alphasat EMEA') at about 25°E, elevation 32° azimuth 187° from Kyiv (36° from Odesa). The MEAS Inmarsat-4 satellite near 64°E is at about 24° elevation (longitude is general knowledge, not verified).
    - **Band:** L, 1537.0-1544.2 MHz (Inmarsat-C receive band). sigidwiki NCS channels: 1537.10 (IOR), 1537.70 (AOR-W), 1541.45 (AOR-E/POR).
    - **Capability:** EGC SafetyNET maritime safety information (NAVAREA/METAREA III warnings, SAR and met broadcasts) and NCS bulletin-board/system packets only
    - **Status oct 2026:** Inmarsat-C is still a GMDSS service. That IOR now runs on Alphasat comes from UK MIN 582. That the IOR NCS stays on 1537.10 MHz after migration is my inference, not verified: scan 1537-1544 MHz on air.
    - **Antenna:** STRICT: 2-turn helix + SAWbird+ iO, or a 12 cm air patch at 1541 MHz. STRICT fallback: modified GPS puck. SMALL: RTL-SDR Blog active L-band patch.
    - **Antenna size cm:** 12 (helix/patch); 4-5 (GPS puck); 17.5 (RTL-SDR Blog patch)
    - **Tier:** strict
    - **Link margin:** Calculation of G/T against the Inmarsat-C ship-terminal G/T of -23 dB/K (spec from general knowledge, not re-fetched):
  - 2-turn helix (~7.5 dBic, Tsys 200 K): -15.5 dB/K, +7.5 dB.
  - 4-turn helix on 20 cm: +10 dB.
  - RTL-SDR Blog patch (gain unpublished, 5-6 dBic assumed): about +5.5 dB.
  - Modified GPS puck: about -3 dB, consistent with rtl-sdr.com's 'on the edge'.
    - **Reachability:** reliable
    - **Receiver:** RTL-SDR V4L, USB about 4 kHz wide, 1200 sym/s BPSK, decoded with stdcdec or Scytale-C (available now)
    - **Legal:** Allowed: SafetyNET is a public safety broadcast.
  - Configure the decoder to keep only SafetyNET and bulletin-board packets.
  - Excluded: FleetNET (commercial subscriber broadcasts), LES TDM channels and any addressed message, Aero ACARS, C-channel voice, BGAN/Fleet traffic.
  - Martial law: do not publish logs tied to your location, and do not redistribute analysis of Black Sea warnings.
    - **Signal:** Geostationary, about 2.5 kHz wide, always on
    - **Evidence:** rtl-sdr.com tutorial: RTL-SDR Blog patch 'near-guaranteed', modified GPS antenna 'just on the edge', helix best. thebaldgeek ranking: puck < patch < helix < dish.
    - **Sources:**
      - https://www.rtl-sdr.com/rtl-sdr-tutorial-decoding-inmarsat-std-c-egc-messages/
      - https://sigidwiki.com/wiki/Inmarsat-C_TDM
      - https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/750319/MIN_582__M_F__Change_to_Inmarsat_Satellite_Services_including_GMDSS.pdf
      - https://www.furuno.com/en/products/satellite-communications/felcom20/index.html
      - https://www.rtl-sdr.com/preorder-sale-active-l-band-1525-1660-inmarsat-and-iridium-patch-back-in-stock-for-44-95/
  2.
    - **Satellite:** Iridium constellation (LEO): ring-alert and system broadcast frames
    - **Band:** L, 1618-1626.5 MHz (gr-iridium)
    - **Capability:** Satellite and beam IDs, satellite position and broadcast timing from the ring alert (IRA) and broadcast (IBC) frames, used for timing, positioning and tracking experiments
    - **Status oct 2026:** Operational (general knowledge). The RTL-SDR Blog patch page lists Iridium decoding as a use case.
    - **Antenna:** STRICT: 2-turn helix (8.3 dBic modelled at 1621 MHz) pointed up + SAWbird+ IR, or a modified GPS puck. SMALL: RTL-SDR Blog patch.
    - **Antenna size cm:** 12 / 4-5 / 17.5
    - **Tier:** strict
    - **Link margin:** Iridium is designed for roughly 0 dBi handset antennas, and a 7-8 dBic helix is about 7 dB better (qualitative calculation). gr-iridium: the burst count 'is largely dependent on your antenna'.
    - **Reachability:** reliable
    - **Receiver:** RTL-SDR V4L centred near 1622 MHz captures only part of the 8.5 MHz band (README). The LimeSDR at 10 Msps or more captures all of it.
    - **Legal:** Decode and keep only the IRA/IBC system frames, and strip the paging identifier (TMSI) fields. Never decode IMS/IDA/MSG (pager/SMS) or VOC (voice). Those are private content and excluded.
    - **Signal:** Bursty TDMA, Doppler up to about ±36 kHz (general knowledge)
    - **Evidence:** gr-iridium README; RTL-SDR Blog patch product page
    - **Sources:**
      - https://github.com/muccc/gr-iridium
      - https://www.rtl-sdr.com/preorder-sale-active-l-band-1525-1660-inmarsat-and-iridium-patch-back-in-stock-for-44-95/
  3.
    - **Satellite:** GNSS: GPS, Galileo, GLONASS and BeiDou L1 (LC76G receiver in the stack, and optionally raw L1 recorded through the RTL-SDR)
    - **Band:** L, 1561-1606 MHz (B1, E1/L1, G1)
    - **Capability:** Position, time, PPS; raw L1 recording for GNSS-SDR experiments
    - **Status oct 2026:** Operational. Widespread jamming and spoofing in Ukraine.
    - **Antenna:** LC76G board active antenna (STRICT); active GPS puck or the 2-turn helix (8.2 dBic at 1575 MHz) on the RTL-SDR bias tee
    - **Antenna size cm:** a few cm to 12
    - **Tier:** strict
    - **Link margin:** Designed for omnidirectional patches, so antenna gain is not the limit. Jamming, spoofing and urban LTE are. The narrower helix beam (about 60-70°) sees fewer satellites, so use the patch for navigation.
    - **Reachability:** reliable
    - **Receiver:** LC76G on UART (in stack); RTL-SDR V4L for raw recording (GNSS-SDR on the Q6A is unverified)
    - **Legal:** Receive-only navigation signals are allowed. Never publish position or timing logs from Ukraine. Treat fixes as untrusted, using the IMU/RTC spoofing gate from gnss_imu.json.
    - **Signal:** Spread spectrum below the noise floor
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/gnss_imu.json
  4.
    - **Satellite:** EGNOS SBAS geostationary satellites: PRN 123 Astra 5B (31.5°E, elevation 32° from Kyiv), PRN 136 SES-5 (5°E, 27°), PRN 121 Eutelsat 5WB (5°W, 23°)
    - **Band:** L1 1575.42 MHz (and L5)
    - **Capability:** SBAS correction and integrity messages from a geostationary navigation signal
    - **Status oct 2026:** PRN 121 joined the operational platform in September 2025 (GPS World). PRN 123 and 136 are listed, but sources conflict on test or operational mode, and Astra 5B's slot is given as 23.5°E or 31.5°E. No 2026 operational notice was found.
    - **Antenna:** Any GNSS antenna above
    - **Antenna size cm:** a few cm to 12
    - **Tier:** strict
    - **Link margin:** Same signal class as GPS L1, so it is not antenna-limited
    - **Reachability:** reliable
    - **Receiver:** LC76G (whether it uses or outputs SBAS is not verified) or an SDR GNSS receiver (not verified on the Q6A)
    - **Legal:** Public navigation signal; allowed
    - **Sources:**
      - https://en.wikipedia.org/wiki/European_Geostationary_Navigation_Overlay_Service
      - https://www.gpsworld.com/tag/eutelsat-satellite
      - https://www.gps.gov/sites/default/files/2026-02/L1CA-PRN-code-assignments-2026-Jan_2.pdf
  5.
    - **Satellite:** Meteor-M N2-3 and N2-4 HRPT, STRICT tier
    - **Band:** L, 1700 MHz RHCP, 2x 665.4 ksym/s
    - **Capability:** Full-resolution 6-channel MSU-MR imagery at 1 km/px, on high passes only
    - **Status oct 2026:** Both active (SatDump sat_list)
    - **Antenna:** 2-turn universal helix on a 12 cm disc + SAWbird+ GOES at the feed, or a 12 cm air patch at 1.70 GHz
    - **Antenna size cm:** 12
    - **Tier:** strict
    - **Link margin:** Calculation from the field anchor: 12.75 dBic 11-turn helix gave 7 dB average SNR (metislair), and SatDump needs 0.5 dB.
  - 2-turn helix at 7.4-8.6 dBic: average 1.7-2.8 dB, margin +1.2 to +2.3 dB. Zenith 5.6-6.8 dB, so it decodes only above about 22-28° elevation.
  - 12 cm patch (about 7 dBic): +0.8 dB, decodes above about 31°.
  Assumptions: the anchor average corresponds to about 35° elevation; no isoflux shaping; patch pointing gain and ground-noise loss cancel to ±1 dB. Meteor EIRP is not verified (±2-3 dB).
    - **Reachability:** marginal
    - **Receiver:** RTL-SDR V4L at 2.4-2.56 Msps, SatDump meteor_hrpt (works now)
    - **Legal:** Public weather broadcast; allowed. Do not publish imagery of Ukrainian territory that could reveal infrastructure.
    - **Evidence:** No dish-free or patch-based Meteor HRPT decode was found (one search). The result is calculated only.
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
      - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lband_small/scripts/budget.py
  6.
    - **Satellite:** Meteor-M N2-3 and N2-4 HRPT, SMALL tier
    - **Band:** L, 1700 MHz RHCP
    - **Capability:** Full HRPT on most passes with maximum elevation above about 25°
    - **Status oct 2026:** Both active (SatDump)
    - **Antenna:** 4-turn helix on a 20 cm disc + SAWbird+ GOES, or the YUST/R-Net 20 cm LTE panel through a 90° hybrid
    - **Antenna size cm:** 20 (helix 17.6 cm tall)
    - **Tier:** small
    - **Link margin:** Calculation, same anchor and assumptions as the strict entry:
  - 4-turn helix at 9.7-10.9 dBic: average SNR 3.9-5.2 dB, margin +3.4 to +4.7 dB, decodes above about 13-18° elevation.
  - LTE panel with hybrid (about 10 dBic): +3.8 dB, above about 16°.
  - LTE panel single port (about 7.5 dBic-equivalent): only +1.2 dB.
  - RTL-SDR Blog patch: no, 1700 MHz is outside its SAW filter.
    - **Reachability:** reliable
    - **Receiver:** RTL-SDR V4L + SatDump
    - **Legal:** Allowed (as above)
    - **Evidence:** Calculated only, with no field precedent. Validate first on a high pass.
    - **Sources:**
      - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  7.
    - **Satellite:** Metop-B / Metop-C AHRPT
    - **Band:** L, 1701.3 MHz RHCP, 2.33 Msym/s QPSK (needs at least 4 dB SNR)
    - **Capability:** Full AVHRR/IASI direct broadcast
    - **Status oct 2026:** Sources conflict:
  - NOAA OSPO (3 Sep 2026): Metop-C AHRPT 'No'.
  - WMO OSCAR: 1701.3 MHz 'not in use'.
  - SatDump: both active, with Metop-B suffering intermittent modulator issues.
    - **Antenna:** None within 20 cm
    - **Antenna size cm:** needs about 56-60 cm (2x2 helix array) or a 60 cm dish
    - **Tier:** none
    - **Link margin:** Calculation from the EUMETSAT flux-density spec (dish_replacement.json): a 13 dBic helix gives Es/N0 of -1 to +3 dB.
  - SMALL (9.7-10.9 dBic): -4.3 to +0.9 dB, short by 3.1-8.3 dB.
  - STRICT (7.4-8.6 dBic): short by 5.4-10.6 dB.
    - **Reachability:** not_reachable
    - **Receiver:** Would need the LimeSDR (above 2.56 Msps)
    - **Legal:** Public weather broadcast
    - **Sources:**
      - https://www.ospo.noaa.gov/operations/metop/status.html
      - https://user.eumetsat.int/s3/eup-strapi-media/TD_18_Metop_Direct_Readout_AHRPT_Technical_Description_v3_A_1cb789b653.pdf
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  8.
    - **Satellite:** Arctic Weather Satellite (AWS, ESA)
    - **Band:** L, 1707 MHz RHCP, 1.785 Msym/s, 600 km orbit
    - **Capability:** MWR microwave imager direct broadcast (unencrypted)
    - **Status oct 2026:** Active (SatDump). 'Signal usually suffers from significant fading when facing away from you at lower elevations.'
    - **Antenna:** 4-turn helix on a 20 cm disc + SAWbird+ GOES (passes 1707 MHz)
    - **Antenna size cm:** 20
    - **Tier:** small
    - **Link margin:** Calculation only. EIRP is not published; I assumed it equals Meteor HRPT's (not verified), with a -4.3 dB symbol-rate penalty and +2.8 dB for the closer orbit.
  - SMALL (10.3 dBic): about 7 dB at zenith, about 2 dB at 30°.
  - STRICT (8 dBic): about 4.7 dB at zenith.
  - Decode threshold unknown (3-4 dB assumed).
    - **Reachability:** opportunistic
    - **Receiver:** LimeSDR Micro (needs at least 3.6 Msps; ships 15 Dec 2026), SatDump aws pipeline
    - **Legal:** Public weather broadcast
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
      - https://space.oscar.wmo.int/satellites/view/aws_pfm
  9.
    - **Satellite:** Elektro-L N3 / N5 LRIT (76°E; elevation 18° from Kyiv, 15° from Lviv, 21° from Kharkiv)
    - **Band:** L, 1691 MHz RHCP, 294 ksym/s
    - **Capability:** Reduced-resolution geostationary imagery every 3 h
    - **Status oct 2026:** SatDump: N3 transmissions paused pending N5 commissioning; N5 LRIT 'off for commissioning', with sporadic transmissions. N4 (165.75°E) is not visible from Ukraine.
    - **Antenna:** None within 20 cm
    - **Antenna size cm:** needs about 12.5 dBic or more (the 47 cm 11-turn helix or the 44 cm fold cone)
    - **Tier:** none
    - **Link margin:** Calculation: the 11-turn helix gave only about 1.5 dB-equivalent against about +1 dB needed.
  - SMALL: -1.6 to -0.3 dB, short by 1.3-2.6 dB.
  - STRICT: short by 3.7-4.8 dB.
    - **Reachability:** not_reachable
    - **Receiver:** RTL-SDR V4L, SatDump
    - **Legal:** Public weather broadcast (Russian state satellite). Receiving it is allowed; avoid publishing anything that ties your location to the reception.
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
      - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
  10.
    - **Satellite:** FengYun-2H (79°E; elevation 17° from Kyiv, 13° from Lviv, 20° from Kharkiv): geostationary L-band carriers
    - **Band:** L. 1690.5 MHz LRIT test-pattern carrier every 3 h from 00:48 UTC ('fairly strong carrier'); 1702.5 MHz analogue telemetry, always on. Both linearly polarised.
    - **Capability:** Carrier detection only, as a fixed beacon for comparing antennas. S-VISSR imagery at 1687.5 MHz (660 ksym/s) needs a dish.
    - **Status oct 2026:** Active per SatDump
    - **Antenna:** 4-turn helix on a 20 cm disc on a tripod; long-FFT carrier detection
    - **Antenna size cm:** 20
    - **Tier:** small
    - **Link margin:** Not computable: EIRP is not published. Linear polarisation costs 3 dB on a CP antenna. Reception with small antennas is not verified.
    - **Reachability:** opportunistic
    - **Receiver:** RTL-SDR V4L, narrow FFT
    - **Legal:** Public weather satellite
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  11.
    - **Satellite:** Black Kite-1 and Black Kite-2 (RapidTek, Taiwan): S-band telemetry
    - **Band:** S, 2288.0 / 2286.0 MHz, GMSK 38.4 kbps ('S-band 38k4 Telemetry', SatNOGS DB)
    - **Capability:** Decoding housekeeping telemetry frames
    - **Status oct 2026:** In orbit. Decoded frames on SatNOGS through 17 Oct 2026.
    - **Antenna:** 2-turn or 3-turn S-band helix on a 12 cm disc + LNA + Sysmocom cf2235-kt30 cavity
    - **Antenna size cm:** 12
    - **Tier:** strict
    - **Link margin:** Evidence:
  - Pi Station 1 (Belgium), listed antenna a discone, decoded frames on passes with maximum elevation 9-32° (for example observation 15185665, 18°).
  - SM0TGU (fixed 4-turn helix, which the owner calls 'very weak') decoded both satellites.
  Relative calculation: the 2-turn S helix (about 8-9 dBic) is about 9-11 dB above a discone (0-2 dBi linear, -3 dB on CP).
    - **Reachability:** reliable
    - **Receiver:** LimeSDR Micro (ships 15 Dec 2026) + gr-satnogs GMSK. The RTL-SDR V4L cannot tune 2.29 GHz.
    - **Legal:** Commercial satellite telemetry. Keep only housekeeping telemetry, and do not inspect or publish any IoT user payload.
    - **Signal:** LEO, GMSK 38.4 kbps
    - **Sources:**
      - https://network.satnogs.org/observations/15185665/
      - https://network.satnogs.org/observations/15200762/
      - https://network.satnogs.org/stations/2830/
      - https://db.satnogs.org/api/transmitters/?format=json
  12.
    - **Satellite:** CARTOSAT-3 (ISRO Earth observation): S-band CW carrier
    - **Band:** S, 2224.797 MHz CW
    - **Capability:** Carrier and Doppler logging only (no data)
    - **Status oct 2026:** SM0TGU logged the signal on passes with 11-82° maximum elevation (Aug-Sep 2026)
    - **Antenna:** 2-turn S helix on a 12 cm disc + LNA + cavity
    - **Antenna size cm:** 12
    - **Tier:** strict
    - **Link margin:** A fixed, non-tracking 4-turn helix (about 9-10 dBic) sees it, and a CW carrier gains a lot of processing gain in a narrow FFT. A hand-pointed 8-9 dBic helix is comparable (relative estimate).
    - **Reachability:** reliable
    - **Receiver:** LimeSDR Micro (from Dec 2026)
    - **Legal:** Civil Earth-observation satellite; record carrier and Doppler only
    - **Sources:**
      - https://network.satnogs.org/observations/14910274/
      - https://network.satnogs.org/stations/2830/
  13.
    - **Satellite:** PHASMA-DIRAC and PHASMA-LAMARR (Libre Space Foundation, Greece; spectrum-monitoring CubeSats, about 492-505 km)
    - **Band:** S, 2208.0 / 2210.0 MHz, FSK 400 kbps
    - **Capability:** Telemetry frames
    - **Status oct 2026:** In orbit. The good S-band SatNOGS observations in my sample (Oct 2026) come only from NuSpace SN3 (Singapore, helix) and the ISAE 3 m dish.
    - **Antenna:** 4-turn S-band helix on a 20 cm disc
    - **Antenna size cm:** 20
    - **Tier:** small
    - **Link margin:** Calculation with an assumed EIRP of 0-5 dBW (not published): 400 kbps FSK needs about 68 dB-Hz. A 10.5 dBic antenna gives 62-67 dB-Hz at zenith and 54-59 dB-Hz at 20° elevation, so it falls short unless the EIRP is higher.
    - **Reachability:** opportunistic
    - **Receiver:** LimeSDR Micro
    - **Legal:** Open science/amateur-friendly mission; telemetry allowed
    - **Sources:**
      - https://network.satnogs.org/observations/15220201/
      - https://libre.space/projects/phasma/
      - https://network.satnogs.org/stations/4125/
  14.
    - **Satellite:** Other S-band science and weather telemetry or dumps: PROBA-2 (2235 MHz, dumps over Redu), Hinode (2256.22 MHz), Metop-B/C S-band telemetry (2230 MHz), NOAA-20/NOAA-21/Suomi-NPP global telemetry (2247.5 MHz), TRISAT-S (2280.5 MHz)
    - **Band:** S, 2.2-2.3 GHz, mostly 65 ksym/s to 2 Msym/s
    - **Capability:** Seeing the signal hump and Doppler; decoding unlikely
    - **Status oct 2026:** Active per SatDump. SatNOGS 'with-signal' observations in Aug-Sep 2026 used larger antennas: S59MZ's 50 cm Wi-Fi grid (PROBA-2, TRISAT-S) and JF6FYI's helix (Hinode).
    - **Antenna:** 4-turn S-band helix on a 20 cm disc
    - **Antenna size cm:** 20
    - **Tier:** small
    - **Link margin:** Those stations used 50 cm grids or helices that are 3-6 dB better than a 20 cm helix. Rates up to 2 Msym/s need 66 dB-Hz or more (calculation).
    - **Reachability:** opportunistic
    - **Receiver:** LimeSDR Micro
    - **Legal:** Civil science and weather telemetry; allowed
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
      - https://network.satnogs.org/stations/1260/
      - https://network.satnogs.org/stations/5242/
  15.
    - **Satellite:** ISS HamTV (ARISS)
    - **Band:** S, 2395 MHz RHCP, DVB-S 2.0 Msym/s, FEC 1/2, 2 W into a patch
    - **Capability:** Carrier hump only. Video needs a dish.
    - **Status oct 2026:** Powered on again on 29 Jul 2025 (BATC wiki, no later update). SM0TGU's fixed helix logged the signal in Jan 2026. Current schedule not verified.
    - **Antenna:** 4-turn S helix on a 20 cm disc
    - **Antenna size cm:** 20
    - **Tier:** small
    - **Link margin:** BATC recommends 'a dish of 0.6-1.2 meters', about 21-27 dBi, which is 10-16 dB more than a 20 cm helix. A naive budget (2 W, no ISS-side losses) would be near threshold at high elevation, but I trust the field guidance.
    - **Reachability:** opportunistic
    - **Receiver:** LimeSDR Micro + a 2.4 GHz filter (the cf2235 cavity blocks 2395 MHz); Q6A Wi-Fi off
    - **Legal:** Amateur broadcast; allowed
    - **Sources:**
      - https://wiki.batc.org.uk/HAMTV_from_the_ISS
      - https://db.satnogs.org/api/transmitters/?format=json
  16.
    - **Satellite:** Other 2.4 GHz amateur-satellite downlinks (UmKA-1 2402.4 MHz BPSK 2 Mbps; DELFI-N3XT 2405 MHz; about 35 other active 2400-2450 MHz transmitters in SatNOGS DB)
    - **Band:** S, 2400-2450 MHz
    - **Capability:** Telemetry
    - **Status oct 2026:** SatNOGS shows no good 2.4 GHz observations since the latest ones listed here: UmKA-1 Nov 2025 (Mogielnica station), DELFI-N3XT Oct 2025. For most of the newer CubeSats, the latest 25 good observations each contain no 2.4 GHz entry.
    - **Antenna:** None verified
    - **Antenna size cm:** 20
    - **Tier:** none
    - **Link margin:** Most run 0.25-10 Mbps and need 62-70 dB-Hz or more (calculation), with no evidence of reception on small antennas. 2.4 GHz Wi-Fi interference is severe.
    - **Reachability:** not_reachable
    - **Receiver:** LimeSDR Micro
    - **Legal:** Amateur; allowed
    - **Sources:**
      - https://db.satnogs.org/api/transmitters/?format=json
      - https://network.satnogs.org/api/observations/
  17.
    - **Satellite:** FengYun-3 series AHRPT
    - **Band:** FY-3C L-band ended Nov 2024; FY-3D to FY-3H AHRPT is X-band (7.79-7.86 GHz)
    - **Capability:** None
    - **Status oct 2026:** No L-band FengYun-3 in service (dish_replacement.json, SatDump)
    - **Antenna:** Tracked dish of about 1 m
    - **Antenna size cm:** about 100
    - **Tier:** none
    - **Link margin:** Not applicable
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** Public weather
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  18.
    - **Satellite:** Meteosat-11 (9.5°E, elevation 29° from Kyiv): PGS raw data at 1686.83 MHz
    - **Band:** L, 3.75 Msym/s, linear
    - **Capability:** Raw SEVIRI
    - **Status oct 2026:** Active (SatDump)
    - **Antenna:** Dish needed
    - **Antenna size cm:** dish
    - **Tier:** none
    - **Link margin:** Ground-station downlink at a high symbol rate; far below a 20 cm antenna (qualitative)
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** Allowed, but not reachable
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  19.
    - **Satellite:** EXCLUDED, military: Yunhai-1 01-04 (1704 MHz, SatDump calls it an 'encrypted military satellite'), DMSP F17/F18 (2252.5 MHz, USSF), Coriolis (2221.5 MHz, USSF), EWS-G2 (1676 MHz, USSF), OPS 5644 (2237.5 MHz), EMISAT (2255.14 MHz)
    - **Band:** L/S
    - **Capability:** Excluded: no decoding guidance
    - **Status oct 2026:** Some appear in SatNOGS and SatDump listings
    - **Antenna:** n/a
    - **Antenna size cm:** n/a
    - **Tier:** none
    - **Link margin:** n/a
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** EXCLUDED under the military rule. Do not record or share.
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  20.
    - **Satellite:** EXCLUDED, private communications: Inmarsat Aero/ACARS, C-channel voice, BGAN/Fleet, FleetNET and LES message channels; Iridium voice/SMS/pager (IMS/IDA/VOC); Thuraya user traffic; Globalstar 2483.5-2500 MHz downlinks
    - **Band:** L/S
    - **Capability:** Excluded
    - **Status oct 2026:** Active
    - **Antenna:** n/a
    - **Antenna size cm:** n/a
    - **Tier:** none
    - **Link margin:** n/a (several of these are physically receivable with the same patch, which is why the decoder filter matters)
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** EXCLUDED: private communications content
    - **Sources:**
      - https://www.rtl-sdr.com/preorder-sale-active-l-band-1525-1660-inmarsat-and-iridium-patch-back-in-stock-for-44-95/
  21.
    - **Satellite:** EXCLUDED, Cospas-Sarsat L-band relay downlinks (1544.5 MHz SARP/MEOSAR on Meteor, Metop, NOAA, GOES, Elektro, BeiDou)
    - **Band:** L, 1544.5 MHz
    - **Capability:** Excluded
    - **Status oct 2026:** Listed in SatNOGS DB
    - **Antenna:** n/a
    - **Antenna size cm:** n/a
    - **Tier:** none
    - **Link margin:** n/a
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** EXCLUDED: relays of personal distress-beacon data and positions to ground stations. This is not a published broadcast.
    - **Sources:**
      - https://db.satnogs.org/api/transmitters/?format=json
- **Lost vs foldable:**
  1.
    - **Target:** Meteor-M N2-3/N2-4 HRPT (1700 MHz)
    - **Needed:** 0.5 dB SNR (SatDump); about 12.75 dBic for +6.5 dB average margin
    - **Gap db:** Calculation:
  - Foldable helicone (15.7 dBic model): +9.4 dB average, decodes from about 5° elevation.
  - SMALL 4-turn helix: +3.4 to +4.7 dB, from about 13-18°.
  - STRICT 2-turn helix: +1.2 to +2.3 dB, from about 22-28°.
  Loss vs foldable: about 5-6 dB (SMALL) or 7-8 dB (STRICT). In practice STRICT keeps only high passes and the middle of each pass.
    - **What would bring it back:** The 11-turn helix (47 cm tall) or the 44 cm fold-flat helicone, both excluded by size. Within the rule: use the SMALL 4-turn helix on a tripod, put the LNA at the feed, and accept only passes above 25-30°.
  2.
    - **Target:** Metop-B/C AHRPT (1701.3 MHz, 2.33 Msym/s)
    - **Needed:** 4 dB SNR; about 16-19 dBic
    - **Gap db:** Foldable helicone: about 0 to +0.5 dB average (degraded but possible on high passes). SMALL: short by 3.1-8.3 dB. STRICT: short by 5.4-10.6 dB (calculation).
    - **What would bring it back:** The 56-60 cm 2x2 spring-helix array (17-18 dBic after the combiner, model) on a tripod, or the EUMETSAT archive instead of live reception. Check on air first, since the AHRPT status conflicts between sources.
  3.
    - **Target:** AWS 1707 MHz
    - **Needed:** Unknown (about 3-4 dB assumed); EIRP unpublished
    - **Gap db:** Foldable: about 12 dB at zenith and 7 dB at 30° (if EIRP equals Meteor's; unverified). SMALL: about 7 / 2 dB. STRICT: about 4.7 / -0.3 dB. About 5 dB lost.
    - **What would bring it back:** Fold helicone (borderline). The LimeSDR is needed in any case.
  4.
    - **Target:** Elektro-L LRIT 1691 MHz
    - **Needed:** About +1 dB; at least 12.5 dBic
    - **Gap db:** SMALL short by 1.3-2.6 dB; STRICT short by 3.7-4.8 dB (calculation). The transmitter is paused or commissioning anyway (SatDump).
    - **What would bring it back:** 11-turn helix or fold helicone (borderline), once Elektro-L5 or L3 resumes LRIT. For antenna A/B tests, use the always-on Inmarsat NCS carrier at 1537-1541 MHz instead.
  5.
    - **Target:** Weak S-band CubeSats and science dumps (PHASMA 400 kbps, PROBA-2, Hinode, Metop/JPSS S-band telemetry)
    - **Needed:** About 62-68 dB-Hz or more for 125 kbps to 2 Msym/s
    - **Gap db:** Foldable S options model 14.2 dBic (helix in the L cone) or 15.5 dBic (33 cm S cone), against 10.9-11.4 dBic (SMALL 20 cm helix) and 9-9.75 dBic (STRICT): about 3-6.5 dB lost.
    - **What would bring it back:** 33 cm fold S-band cone (packs to about 14 cm across; borderline). Strong targets need nothing: Black Kite-1/2 and the CARTOSAT-3 carrier remain reachable at 12 cm.
  6.
    - **Target:** Inmarsat-C SafetyNET, Iridium system frames, GNSS, EGNOS
    - **Needed:** Designed for small or omnidirectional antennas
    - **Gap db:** 0 dB. Nothing lost. The 12 cm 2-turn helix is about 5-10 dB above what these systems need (G/T calculation).
    - **What would bring it back:** Not needed
- **Borderline note:** BORDERLINE, EXCLUDED by the 18 Oct rule and shown only so the user can reconsider. Each of these is tens of centimetres when deployed:
  - 44 cm fold-flat petal or fabric helicone (15.7 dBic modelled; packs to about 19 x 19 x 4 cm), or the rigid 11-turn helix (47 cm tall). Either would add 5-8 dB at 1.7 GHz. That restores Meteor HRPT from about 5° elevation, brings Elektro-L LRIT back to its threshold when it transmits, and makes Metop and AWS possible on high passes.
  - 33 cm S-band fold cone (15.5 dBic). Adds 4-6.5 dB, enough for PHASMA-class 400 kbps CubeSats and the science dumps.
  - 56-60 cm 2x2 spring-helix array (17-18 dBic). The only non-dish route to Metop AHRPT.
  None of them is needed for Inmarsat-C SafetyNET, Iridium system frames, GNSS/EGNOS, Black Kite or CARTOSAT-3. Those are fully reachable within 12 cm.
- **Notes:** BOTTOM LINE: at 1.5-2.4 GHz the 12/20 cm rule removes little.
  - STRICT (12 cm or less), one DIY 2-turn helix: Inmarsat-C SafetyNET, Iridium system frames, GNSS/EGNOS, and the strong S-band telemetry and carriers (Black Kite-1/2, CARTOSAT-3) are reliable. Meteor HRPT works only on high passes.
  - SMALL (20 cm or less): Meteor HRPT becomes reliable on most passes. AWS, the FY-2H carriers, PHASMA and the HamTV carrier stay opportunistic.
  - Lost: Metop AHRPT (3-10 dB short), Elektro-L LRIT (1.3-4.8 dB short and paused anyway), weak S-band dumps, and video or data from the 2.4 GHz amateur satellites.
  
  PHYSICS:
  - 12-20 cm is 0.6-1.5λ at these bands, so nothing is electrically short. Radiation efficiency stays above 90% (helix conductor loss under 0.1 dB modelled). The limit is aperture and directivity.
  - Broadside aperture limits at 100% efficiency (calculation): 12 x 12 cm gives 6.8 / 7.6 / 10.1 dBi at 1.54 / 1.70 / 2.25 GHz; 20 x 20 cm gives 11.2 / 12.1 / 14.5 dBi. End-fire helices exceed the cross-section limit slightly because their length counts, which is why they beat patches of the same size.
  - External sky noise is low (about 5-50 K). Tsys is set by the LNA (NF about 1 dB, about 75 K), ground pick-up through wide beams (+30-60 K estimated) and, above all, man-made interference: LTE B3 at 1805-1880 MHz, B1 at 2110-2170 MHz, and Wi-Fi at 2.4 GHz, including the Q6A's own Wi-Fi.
  - Possibly also GNSS jammers near the front raising the noise floor at 1.5-1.6 GHz. Plausible, not verified.
  - So SAW or cavity filtering at the feed matters more than another dB of gain.
  
  RECEIVERS:
  - The RTL-SDR V4L (up to 1.766 GHz) covers every L-band target today: Inmarsat, Iridium (partial band), GNSS and Meteor HRPT at 2.4-2.56 Msps.
  - AWS, Metop and all S-band need the LimeSDR Micro (30 MHz-3.8 GHz, $249, ships 15 Dec 2026). The S-band chain is LNA then Sysmocom cf2235-kt30 (2170-2300 MHz), or a 2.4 GHz band-pass filter for HamTV and the amateur band, since the cf2235 blocks 2.4 GHz.
  
  LNAs:
  - SAWbird+ GOES (in stack, passband about 1648-1728 MHz) blocks Inmarsat and Iridium. Add a SAWbird+ iO (1542 MHz) or SAWbird+ IR (1620 MHz) and swap at the helix feed.
  - Today's Nooelec listing: $49.95 each; dual-LNA and Barebones versions $44.95.
  - Correction: the files quote the SAWbird+ GOES at $44.95, but that is the Barebones price; the SAWbird+ GOES itself is now $49.95.
  
  CORRECTION: the RTL-SDR Blog L-band patch is 175 x 175 mm (vendor). That makes it SMALL tier, not STRICT, and it is out of band for HRPT.
  
  MODELS: NEC2 (PyNEC), reusing fold() from the foldable work. Scripts:
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lband_small/scripts/helix_small.py
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lband_small/scripts/helix_univ.py
  - Link budgets and geostationary look angles: budget.py and geo.py in the same folder.
  - Assumed model optimism is about 1.2 dB, from the 11-turn cross-check (13.98 modelled vs 12.75 anchor).
  
  LINK BUDGETS: all are calculations. I reused the dish_replacement.json anchors and did not redo them:
  - Meteor: 7 dB average with 12.75 dBic, 0.5 dB needed.
  - Metop: Es/N0 -1 to +3 dB with a 13 dBic helix, 4 dB needed.
  - LRIT: 1.5 dB-equivalent, +1 dB needed.
  - Added assumption: the Meteor pass average sits at about 35° elevation (zenith about +3.9 dB). Slant-range penalty at 830 km is 9.3 / 6.8 / 4.8 / 2.5 dB at 10 / 20 / 30 / 45° elevation.
  - Generic S-band CubeSat EIRP of 0-5 dBW is an assumption.
  - Black Kite reachability rests on real SatNOGS decodes (a discone and a fixed helix), not on an assumed EIRP.
  
  FIRST TESTS:
  1. 2-turn helix + SAWbird+ iO on the Inmarsat NCS. This also gives an always-on fixed A/B reference at 1.54 GHz, now that Elektro is off.
  2. Iridium.
  3. A high Meteor pass with the SAWbird+ GOES.
  4. After December, Black Kite on the Lime.
  Check S11 better than -10 dB with a NanoVNA after matching the 140-160 Ω helix.
  
  LEGAL AND SAFETY: receive-only.
  - Filter the decoders to SafetyNET, bulletin-board and Iridium IRA/IBC frames only.
  - Military and private-content targets are listed as excluded, with no decoding guidance.
  - Under martial law, do not publish receptions, imagery or logs that reveal your position or infrastructure. Expect GNSS jamming and spoofing.
  - In the field, watch for unexploded ordnance and call 101.
  
  UNVERIFIED:
  - That the IOR NCS stays on 1537.10 MHz after the move to Alphasat.
  - Alphasat at 25°E and the MEAS satellite at 64°E (general knowledge).
  - The Inmarsat-C G/T spec of -23 dB/K (general knowledge).
  - The RTL-SDR patch's gain.
  - Meteor and AWS EIRP.
  - LC76G SBAS output.
  - HamTV's Oct 2026 schedule.
  - Ukrainian prices for GPS pucks and shipping to Ukraine.
  
  SEARCH BUDGET: 5 WebSearch calls used. SatNOGS DB and Network APIs, the SatDump sat_list, and the vendor and BATC pages were read directly.

## small:vhf_uhf (run `wf_41027870-8e7`)

- **Band group:** VHF/UHF, 137-138 MHz, 144-146 MHz and 435-438 MHz, under the 18 Oct 2026 rule of no dishes and no antennas tens of cm in size. How I read the rule: STRICT means the largest deployed dimension is about 12 cm or less; SMALL means about 20 cm or less; anything of about 20-25 cm or more is EXCLUDED even if it folds. A quarter wave is 54.5 cm at 137.5 MHz, 51.4 cm at 145.8 MHz and 17.2 cm at 436 MHz. So only the 70 cm band gets a full-size antenna inside the SMALL tier; every 137 and 145 MHz antenna here is electrically short. Removed from the stack: the RTL-SDR Blog dipole kit used as the 92 cm V-dipole, the WB2HOL and crossed 2 m/70 cm Yagis, the N2SPI 6-element and 4-element 70 cm Yagis, Moxons, the QFH, Arrow, Elk and WiMo antennas. Kept: RTL-SDR V4L for 137/145 MHz, LimeSDR Micro (or the V4L until Dec 2026) for 435 MHz, the FM band-stop or Flamingo+, the SAWbird+ NOAA, the LNA V2 or Uputronics 435 preamp, and the BNO085 IMU. The LNAs must now sit AT the small antenna, because these antennas have a low noise temperature.
- **Small antennas:**
  1.
    - **Name:** DIY 20 cm tuned small loop for 137-146 MHz: 10 mm copper tube, C0G fixed capacitor plus an air trimmer of about 1-10 pF turned by a small stepper, 4 cm Faraday coupling loop
    - **Type:** diy
    - **Band:** 137.1-137.9 MHz (Meteor LRPT, Orbcomm) and 144-146 MHz, by retuning
    - **Size cm:** 20 cm diameter (plus a short insulating mast; keep it at least 1 diameter from the aluminium mid-plate)
    - **Gain or efficiency:** My calculation, not measured. At 137.5 MHz: radiation resistance 1.36 ohm; copper loss 0.06 ohm; capacitor ESR 0.22 ohm at Q 1500. Efficiency -0.9 dB, or -1.5 dB with a construction allowance. Realised gain about +0.3 dBi broadside, linear polarisation, antenna factor about 12.7 dB/m. Tuning capacitance 3.5 pF (137.5 MHz) and 3.1 pF (145.8 MHz); 3 dB bandwidth about 1.4 MHz. A varactor (Q about 200) instead of an air trimmer costs about 2.7 dB more. Pattern is a figure-eight with nulls along the loop axis, so orient it with the IMU.
    - **Price:** About $15-30 in materials (estimate)
    - **Availability incl ukraine:** DIY. Copper plumbing tube is sold in Ukrainian hardware stores. Air trimmers come from radio-parts shops (local stock not verified).
    - **Sources:**
      - https://www.qsl.net/v/vk5br/LoopAntennas/VHFLoopAntenna.htm
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/small_ant/phys.py
  2.
    - **Name:** DIY 12-13 cm tuned small loop (VK5BR 'lunchbox' 2 m loop class)
    - **Type:** diy
    - **Band:** 137-146 MHz (STRICT tier)
    - **Size cm:** 12 cm diameter (VK5BR's build is 13.3 cm, 6.4 mm tube)
    - **Gain or efficiency:** Calculated: radiation resistance 0.18 ohm (137.5 MHz) / 0.22 ohm (145.8 MHz). Efficiency -3.0 to -3.8 dB with a C0G capacitor of Q 1500; -8 to -9 dB with a varactor. Realised gain about -2 dBi, antenna factor about 15 dB/m. VK5BR calculated 85% efficiency with an air butterfly capacitor and measured 'comparable S-meter readings' to a J-pole at 2 m on receive. Bandwidth is very narrow: VK5BR measured about 100 kHz at SWR 1.5 (my estimate 0.55 MHz at 3 dB), so it needs motorised retuning (peak on sky noise) and the hand must stay away from the capacitor.
    - **Price:** About $10-25 (estimate)
    - **Availability incl ukraine:** DIY
    - **Sources:**
      - https://www.qsl.net/v/vk5br/LoopAntennas/VHFLoopAntenna.htm
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/small_ant/phys.py
  3.
    - **Name:** Normal-mode helical (rubber-duck type) whip retuned to 137.5 MHz: extra turns or a ferrite core, as G4ILO did on 2 m
    - **Type:** modify
    - **Band:** 137-138 MHz
    - **Size cm:** 20 cm (SMALL) or 12 cm (STRICT)
    - **Gain or efficiency:** Calculated on an ideal ground: 20 cm has 3.3 ohm radiation resistance, loading-coil loss of 2.4-6 ohm at Q 150-60, efficiency -2.7 to -4.7 dB. 12 cm has 1.2 ohm radiation resistance and efficiency -6.6 to -9.7 dB. 5 cm gives -15.6 to -19.4 dB. After about 2 dB of hand/body loss, realised gain is about -4 dBi (20 cm) or -9 dBi (12 cm), antenna factor 17 / 22 dB/m. An unloaded 17 cm whip into 50 ohm has -26.6 dB mismatch at 137.5 MHz, so loading is mandatory.
    - **Price:** Under $10
    - **Availability incl ukraine:** Base antennas are on Prom.ua; tuning is DIY with a nanoVNA
    - **Sources:**
      - https://www.amateurradio.com/2m-ht-antenna-shootout/
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/small_ant/phys.py
  4.
    - **Name:** Nagoya NA-701 dual-band whip, genuine, SMA-male (fits the RTL/Lime SMA-female jacks)
    - **Type:** buy
    - **Band:** 144-146 / 430-440 MHz (usable off-resonance at 137 MHz)
    - **Size cm:** 21 cm (Nagoya chart; 7.9 in in W9MDB); at the SMALL limit
    - **Gain or efficiency:** Vendor claims 2.15 dBi. W9MDB measured -2.3 dB vs a Nagoya NA-771 (38 cm whip, the test's reference) at 146 MHz (±2 dB), but a black-sticker 'NA-701' measured -10.3 dB (clone risk). G4ILO found it identical to the Yaesu stock whip and about 3 dB below a 48 cm quarter-wave telescopic. My estimate: about -3 dBi at 145.8 MHz, about 0 dBi at 436 MHz, and -6 to -9 dBi at 137.5 MHz because of mismatch off its 2 m resonance.
    - **Price:** EUR 15.95 (k-po.com, SMA-male); $18.98 (BTECH)
    - **Availability incl ukraine:** Prom.ua: 'Антенна Nagoya NA-701 SMA-male', 950 UAH, in stock at ТЕХ-ІНФОРМ (checked 18 Oct 2026). SMA-female versions are 719 UAH. Listings at 101-334 UAH are likely clones, so check them with a VNA.
    - **Sources:**
      - https://www.miklor.com/COM/pdf/AntennaTestingW9MDB.pdf
      - https://www.amateurradio.com/2m-ht-antenna-shootout/
      - https://baofengtech.com/wp-content/uploads/2023/12/BTECHnagoya_AntennaCompSheet_Final.pdf
      - https://www.k-po.com/product/nagoya-na-701-sma-male
      - https://prom.ua/ua/search?search_term=nagoya%20na-701
  5.
    - **Name:** Diamond SRH-701
    - **Type:** buy
    - **Band:** 2 m / 70 cm
    - **Size cm:** 19 cm
    - **Gain or efficiency:** Vendor: 0 dBi (144 MHz) / 3 dBi (432 MHz). Same class as the NA-701; my estimate is about -3 dBi at 145.8 MHz and about 0 dBi at 436 MHz. No independent measurement found.
    - **Price:** EUR 16.90 incl. VAT + EUR 14.20 shipping (WiMo, in stock)
    - **Availability incl ukraine:** WiMo (DE). Shipping to Ukraine not verified.
    - **Sources:**
      - https://www.wimo.com/en/srh-701
  6.
    - **Name:** Baofeng A-V85 short whip
    - **Type:** buy
    - **Band:** 2 m / 70 cm
    - **Size cm:** 16.8 cm (6.6 in)
    - **Gain or efficiency:** W9MDB: -0.8 dB vs the NA-771 at 146 MHz, the best sub-20 cm antenna in that test. At 435 MHz about -8.7 dB, but those UHF figures were not calibrated. It has an SMA-female connector, so it needs an SMA-male-to-male adapter on the RTL.
    - **Price:** Not verified (typically a few dollars)
    - **Availability incl ukraine:** Not verified (Baofeng accessories are common on Prom.ua)
    - **Sources:**
      - https://www.miklor.com/COM/pdf/AntennaTestingW9MDB.pdf
  7.
    - **Name:** 12 cm UV-5R-type stock stubby
    - **Type:** buy
    - **Band:** 2 m / 70 cm (STRICT)
    - **Size cm:** 12.2 cm (4.8 in)
    - **Gain or efficiency:** W9MDB: -9.8 dB vs the NA-771 at 146 MHz. My estimate is about -10 dBi realised, antenna factor about 24 dB/m at 145.9 MHz.
    - **Price:** A few dollars (not verified)
    - **Availability incl ukraine:** Common; not verified
    - **Sources:**
      - https://www.miklor.com/COM/pdf/AntennaTestingW9MDB.pdf
  8.
    - **Name:** Diamond SRH805S 5 cm stubby
    - **Type:** buy
    - **Band:** 2 m / 70 cm (STRICT)
    - **Size cm:** 5 cm
    - **Gain or efficiency:** W9MDB: -29.8 dB vs the NA-771 at 146 MHz, and about -14 dB at 435 MHz (uncalibrated). G4ILO's generic 5 cm 2 m stubby was only -5 dB vs the stock whip, so results vary by unit and tuning. The vendor's 2.15/3.0 dBi claim is not plausible for 5 cm. Use it at 70 cm only; my estimate there is -5 to -14 dBi.
    - **Price:** Not verified
    - **Availability incl ukraine:** Not verified
    - **Sources:**
      - https://www.miklor.com/COM/pdf/AntennaTestingW9MDB.pdf
      - https://www.amateurradio.com/2m-ht-antenna-shootout/
  9.
    - **Name:** DIY quarter-wave 70 cm whip: SMA-male plug plus a 16.5-17 cm brass or steel rod; use a common-mode choke if it is on a lead
    - **Type:** diy
    - **Band:** 435-438 MHz
    - **Size cm:** 17 cm
    - **Gain or efficiency:** Calculated: radiation resistance about 24 ohm, unmatched mismatch -0.6 dB. On the case with about 2 dB hand/body loss: about 0 dBi realised, antenna factor about 23 dB/m. That is -11 dB vs the foldable 6-element Yagi (11.0 dBi).
    - **Price:** Under $5
    - **Availability incl ukraine:** Parts available locally
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/small_ant/phys.py
  10.
    - **Name:** DIY 12 cm loaded whip or inverted-L for 435-438 MHz
    - **Type:** diy
    - **Band:** 435-438 MHz (STRICT)
    - **Size cm:** 12 cm
    - **Gain or efficiency:** Calculated: radiation resistance about 12 ohm and a reactance of about 104 ohm to cancel. With a Q 60-150 coil or a short top bend, efficiency is -0.4 to -0.7 dB; realised gain about -0.7 dBi. Left straight and unmatched it loses 8.6 dB to mismatch.
    - **Price:** Under $5
    - **Availability incl ukraine:** DIY
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/small_ant/phys.py
  11.
    - **Name:** Johanson 0433AT62A0020E ceramic chip antenna on its evaluation board 0433AT62A0020-EB1SMA
    - **Type:** buy
    - **Band:** 423-443 MHz (covers 435-438)
    - **Size cm:** Chip 2.5 x 0.5 x 0.12 cm; evaluation board 7.3 x 5 cm
    - **Gain or efficiency:** Datasheet: -4.0 dBi peak and average (XZ plane), return loss 9.5 dB minimum, measured on the evaluation board. Expect less once it is near a hand or the case.
    - **Price:** Not verified (Farnell/element14 list it)
    - **Availability incl ukraine:** Via distributors; not verified
    - **Sources:**
      - https://www.johansontechnology.com/datasheets/antennas/0433AT62A0020.pdf
      - https://uk.farnell.com/johanson-technology/0433at62a0020e/antenna-at62/dp/2148530
  12.
    - **Name:** DIY 7 cm tuned loop for 435-438 MHz
    - **Type:** diy
    - **Band:** 435-438 MHz (STRICT)
    - **Size cm:** 7 cm diameter
    - **Gain or efficiency:** Calculated: C/λ 0.32, radiation resistance 2.1 ohm, efficiency -0.7 dB, about +1 dBi, bandwidth about 6 MHz, tuning capacitance about 1 pF. Hard to tune because the capacitance is tiny. The 12 cm whip is simpler.
    - **Price:** Under $10
    - **Availability incl ukraine:** DIY
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/small_ant/phys.py
  13.
    - **Name:** Active (high-impedance buffered) 12-17 cm whip, mini-whip style. REJECTED for VHF/UHF.
    - **Type:** diy
    - **Band:** 137-438 MHz
    - **Size cm:** 12-17 cm
    - **Gain or efficiency:** Calculated with an amplifier noise voltage of 1 nV/√Hz. The sky noise induced in a 12-17 cm whip is only 0.17-0.58 nV/√Hz, so the amplifier dominates. SNR penalty vs an external-noise-limited antenna: 6-9 dB in a rural site at 137 MHz, 12-15 dB in a quiet site, 6-8.5 dB at 436 MHz. A tuned loop or loaded whip is better.
    - **Price:** n/a
    - **Availability incl ukraine:** n/a
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/small_ant/phys.py
- **Satellites:**
  1.
    - **Satellite:** Meteor-M N2-4 (NORAD 59051)
    - **Band:** 137.900 MHz (137.1 alternate)
    - **Capability:** LRPT 72 ksym/s QPSK weather imagery
    - **Signal:** RHCP, about 150 kHz wide
    - **Status oct 2026:** Active. SatNOGS 'good' LRPT observations at 137.900 MHz on 17-18 Oct 2026, including one on a discone. WMO OSCAR: operational (updated 2026-01-23). SatDump: 72k is the normal mode.
    - **Antenna:** 20 cm tuned loop with SAWbird+ NOAA at its feed (alternative: 20 cm helical retuned to 137.5 MHz)
    - **Antenna size cm:** 20
    - **Tier:** small
    - **Link margin:** Calculation. Assumptions: EIRP calibrated so the V-dipole with LNA in a rural site has 0 dB at 15° (gives +1.5 dBW); requirement Es/N0 4 dB = 52.6 dB-Hz; 3 dB polarisation loss; rural noise T_ext 2300 K. Loop: decodes from about 17°, +4/+6/+8 dB at 40/60/90°, i.e. 0.3-1.3 dB below the V-dipole. 20 cm helical: from about 24°, +6 dB at zenith. Residential noise: from about 40°. Quiet site: from horizon terrain. About 70% of passes that rise above 10° also reach 20°.
    - **Reachability:** marginal
    - **Receiver:** RTL-SDR V4L at 1.024 MS/s, SatDump 'METEOR M2-x LRPT 72k'. SAWbird+ NOAA at the antenna with external 5 V, Flamingo+ in front at strong-FM sites. Leaving the LNA out costs another 1-3 dB with small antennas.
    - **Legal:** Public weather broadcast, receive-only. Do not publish geotagged images or station positions.
    - **Evidence:** No published LRPT decode with an antenna under 20 cm was found (2 searches). The rating is model-based and becomes 'reliable' once validated on 2-3 high passes. VK5BR's 13 cm 2 m loop matched a J-pole on receive.
    - **Sources:**
      - https://network.satnogs.org/observations/15230698/
      - https://network.satnogs.org/observations/15225852/
      - https://space.oscar.wmo.int/satellites/view/meteor_m_n2_4
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
      - https://www.qsl.net/v/vk5br/LoopAntennas/VHFLoopAntenna.htm
  2.
    - **Satellite:** Meteor-M N2-4 (NORAD 59051)
    - **Band:** 137.900 MHz
    - **Capability:** LRPT imagery
    - **Status oct 2026:** Active (as above)
    - **Antenna:** 12 cm tuned loop (alternative: 12 cm helical retuned to 137.5 MHz)
    - **Antenna size cm:** 12
    - **Tier:** strict
    - **Link margin:** Calculation, rural site with LNA. 12 cm loop: decodes from about 20°, +6.9 dB at zenith. 12 cm helical: from about 38°, +3.6 dB at zenith (about 38% of passes above 10°). 5 cm stubby: -3.5 dB even at zenith.
    - **Reachability:** marginal
    - **Receiver:** As for the SMALL tier. The loop needs motorised retuning because its bandwidth is 0.1-0.55 MHz.
    - **Legal:** Public weather broadcast, receive-only
    - **Evidence:** Model only. The 12 cm helical alone would be 'opportunistic'; the 5 cm stubby is not reachable.
    - **Sources:**
      - https://www.qsl.net/v/vk5br/LoopAntennas/VHFLoopAntenna.htm
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/small_ant/lb.py
  3.
    - **Satellite:** Meteor-M N2-3 (NORAD 57166)
    - **Band:** 137.900 MHz
    - **Capability:** LRPT imagery
    - **Status oct 2026:** Active. SatNOGS 'good' observations on 17 Oct 2026. SatDump: the VHF antenna did not deploy properly, with 'pixelation issues from time to time'.
    - **Antenna:** 20 cm loop (SMALL) / 12 cm loop (STRICT)
    - **Antenna size cm:** 12-20
    - **Tier:** small
    - **Link margin:** Same budget as N2-4 minus an unquantified antenna-deployment loss (assume 3-6 dB). Expect decodes only above about 40-60°; the STRICT 12 cm loop needs zenith passes.
    - **Reachability:** opportunistic
    - **Receiver:** RTL V4L, SAWbird+ NOAA at the antenna, SatDump
    - **Legal:** Public weather broadcast
    - **Evidence:** RTL-SDR.com reports the N2-4 signal is 'much better than M2-3'.
    - **Sources:**
      - https://network.satnogs.org/observations/15229039/
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
      - https://www.rtl-sdr.com/meteor-m2-4-successfully-deployed-to-orbit-and-now-transmitting-weather-images/
  4.
    - **Satellite:** NOAA-15/18/19 APT; Metop-B/C LRPT; Meteor-M N2-2
    - **Band:** 137-138 MHz
    - **Capability:** APT / LRPT
    - **Status oct 2026:** Not transmitting. NOAA POES decommissioned in 2025 (inputs). SatDump: Metop LRPT broadcast off; N2-2 in storage mode since 07-2024. No APT source remains.
    - **Antenna:** Any
    - **Antenna size cm:** n/a
    - **Tier:** none
    - **Link margin:** No signal
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** n/a
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  5.
    - **Satellite:** Orbcomm constellation (system/ephemeris frames only)
    - **Band:** 137.2-137.8 MHz
    - **Capability:** Unencrypted system frames: satellite ID, ephemeris, frequency plan
    - **Status oct 2026:** Not re-verified for Oct 2026
    - **Antenna:** 20 cm loop retuned to about 137.5 MHz, or 20 cm helical
    - **Antenna size cm:** 12-20
    - **Tier:** small
    - **Link margin:** No EIRP found. RTL-SDR.com calls the signals 'fairly strong'; COAA says a simple VHF scanner picks them up.
    - **Reachability:** marginal
    - **Receiver:** RTL V4L; the SAWbird+ NOAA passband covers it
    - **Legal:** System and ephemeris frames only. User messages are private, and encrypted, so they are EXCLUDED: do not decode or decipher them.
    - **Evidence:** Second-hand
    - **Sources:**
      - https://www.rtl-sdr.com/tag/orbcomm/
  6.
    - **Satellite:** ISS (RS0ISS) SSTV
    - **Band:** 437.550 MHz FM
    - **Capability:** SSTV in Robot 36, 36 s on / 2 min off
    - **Status oct 2026:** Next event Series 34, 22-25 Oct 2026, on 437.55 MHz. The 2026 events moved from 145.800 to 437.55 MHz, with ISS transmit power stated as 10 W (ARISS). The AMSAT status page logged ISS SSTV 'not heard' during 13-18 Oct, i.e. between events.
    - **Antenna:** 12 cm loaded whip or inverted-L, or the Johanson chip on its evaluation board
    - **Antenna size cm:** 7-12
    - **Tier:** strict
    - **Link margin:** Calculation: 10 W EIRP, 3 dB polarisation and 1.5 dB other losses, Tsys 343 K. CNR in 15 kHz is 17.5 / 20.8 / 23.3 / 27.4 dB at 10/20/30/60°. FM threshold is about 10-12 dB. The 5 cm stubby gives about 12.9 dB at 10° (could be up to 9 dB worse, per W9MDB).
    - **Reachability:** reliable
    - **Receiver:** RTL V4L or Lime, with the LNA V2 or Uputronics 435 preamp at the antenna. FM with Doppler correction (about ±10 kHz). SSTV decoder.
    - **Legal:** Amateur broadcast, receive-only. Fine to submit images to the ARISS gallery, but without location metadata.
    - **Evidence:** Official ARISS schedule; the budget is my calculation
    - **Sources:**
      - https://www.ariss.org/upcoming-sstv-events.html
      - https://www.amsat.org/status/
  7.
    - **Satellite:** ISS (RS0ISS) SSTV
    - **Band:** 437.550 MHz
    - **Capability:** SSTV Robot 36
    - **Status oct 2026:** As above
    - **Antenna:** 17 cm quarter-wave whip, NA-701 or SRH-701
    - **Antenna size cm:** 17-21
    - **Tier:** small
    - **Link margin:** CNR 18.3 / 21.5 / 24.0 / 28.1 dB at 10/20/30/60°; -11 dB vs the 6-element Yagi but still far above threshold
    - **Reachability:** reliable
    - **Receiver:** As above
    - **Legal:** Amateur broadcast
    - **Sources:**
      - https://www.ariss.org/upcoming-sstv-events.html
  8.
    - **Satellite:** ISS APRS digipeater (RS0ISS) and FM cross-band repeater (NA1SS)
    - **Band:** APRS 437.825 MHz (1200 AFSK); repeater downlink 437.800 MHz FM
    - **Capability:** APRS packets; amateur voice
    - **Status oct 2026:** ARISS, 7 Oct 2026: 'APRS is currently active on 437.825 MHz' from Zvezda, still being tested. Columbus D710GA is in voice-repeater mode. AMSAT 13-18 Oct: ISS [FM] and [UHF Digi] active.
    - **Antenna:** 17 cm whip (SMALL) / 12 cm loaded whip (STRICT)
    - **Antenna size cm:** 12-17
    - **Tier:** strict
    - **Link margin:** Calculation with an ASSUMED 5 W (not published). Margin over 12 dB CNR is +2.5 / +5.7 / +8.2 / +12.3 dB at 10/20/30/60° (STRICT); about +0.7 dB more for SMALL. The 5 cm stubby is -2 dB at 10° and positive above 20°.
    - **Reachability:** reliable
    - **Receiver:** RTL or Lime + UHF LNA; Direwolf or SatDump for APRS; FM demod for the repeater
    - **Legal:** Receive-only. Under martial law, do NOT iGate, publish or forward APRS position reports, because they reveal the locations of Ukrainian stations. Keep logs offline.
    - **Sources:**
      - https://www.ariss.org/current-status-of-iss-stations.html
      - https://www.amsat.org/status/
  9.
    - **Satellite:** 1 W-class UHF CubeSat telemetry (9k6 GMSK/FSK, 1k2 AFSK). Examples active on AMSAT 13-18 Oct: CO-128 TLM, LASARsat/KOSTKA/CroCube UHF digis. Frequencies not individually re-verified.
    - **Band:** 435-438 MHz
    - **Capability:** Telemetry and beacon frames (gr-satellites / SatDump)
    - **Status oct 2026:** Many active (AMSAT status and SatNOGS)
    - **Antenna:** 17 cm whip (SMALL); 12 cm loaded whip or chip (STRICT)
    - **Antenna size cm:** 7-17
    - **Tier:** small
    - **Link margin:** Calculation using the foldable model (EIRP 27 dBm, losses 4.5 dB, 51.8 dB-Hz required, h 500 km). 17 cm whip: -5.8 / -2.8 / -0.4 / +2.0 / +3.6 / +4.8 dB at 10/20/30/45/60/90°. 12 cm STRICT: about 0.8 dB worse. Chip (-4 dBi): about +0.7 dB at zenith (opportunistic). 0.5 W satellites and 19k2+ links: not reachable.
    - **Reachability:** marginal
    - **Receiver:** Lime (or V4L) with a filtered 435 preamp at the antenna. Record IQ and decode offline; fall back to SatNOGS network data.
    - **Legal:** Amateur and scientific telemetry, receive-only
    - **Sources:**
      - https://www.amsat.org/status/
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_partial.json
  10.
    - **Satellite:** SO-50 (SaudiSat-1C)
    - **Band:** 436.795 MHz FM
    - **Capability:** Amateur FM voice
    - **Status oct 2026:** Active (39 'active' reports on AMSAT, 13-18 Oct). Orbit 577 x 675 km (Celestrak TLE, day 289 of 2026).
    - **Antenna:** 17 cm whip / 12 cm loaded whip
    - **Antenna size cm:** 12-17
    - **Tier:** small
    - **Link margin:** Calculation with an ASSUMED 0.25 W EIRP. Clean FM (12 dB CNR) is -5 dB even at zenith. Noisy but readable (7 dB CNR) needs passes above about 60°, at -1 to 0 dB.
    - **Reachability:** opportunistic
    - **Receiver:** Lime/V4L + UHF LNA, FM with Doppler correction
    - **Legal:** Amateur voice, receive-only
    - **Evidence:** The EIRP is not verified, so this could be 3+ dB better
    - **Sources:**
      - https://www.amsat.org/status/
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=27607
      - https://celestrak.org/NORAD/elements/gp.php?CATNR=27607&FORMAT=TLE
  11.
    - **Satellite:** RS-44 and FO-29 (linear transponders)
    - **Band:** RS-44: CW beacon 435.605, passband 435.61-435.67 MHz. FO-29: CW beacon 435.795, passband 435.8-435.9 MHz.
    - **Capability:** CW telemetry beacons; SSB/CW amateur QSOs
    - **Status oct 2026:** Both active (AMSAT: 54 and 47 'active' reports). Orbits 1182 x 1517 km and 807 x 1328 km.
    - **Antenna:** 17 cm whip / 12 cm loaded whip
    - **Antenna size cm:** 12-17
    - **Tier:** small
    - **Link margin:** Calculation with ASSUMED EIRPs. CW beacons at 0.1 W: RS-44 +3 to +11 dB, FO-29 +5 to +13 dB over aural CW (27 dB-Hz) from 10° to 90°; the 12 cm STRICT whip is about 0.7 dB worse. SSB stations assumed at a 20 mW share: -13 to -21 dB, so audible only for strong stations.
    - **Reachability:** marginal
    - **Receiver:** Lime/V4L, USB/CW with Doppler correction
    - **Legal:** Amateur, receive-only
    - **Evidence:** Beacons are reliable to marginal; SSB traffic is opportunistic
    - **Sources:**
      - https://www.amsat.org/status/
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=44909
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=24278
  12.
    - **Satellite:** AO-73 (FUNcube-1) and JO-97 (JY1Sat) BPSK telemetry
    - **Band:** AO-73 145.935 MHz BPSK 1k2; JO-97 145.840 MHz BPSK 1k2, SSB passband 145.855-145.875 MHz
    - **Capability:** FEC BPSK telemetry; JO-97 also a linear transponder
    - **Status oct 2026:** AO-73: telemetry/beacon only (AMSAT 9 reports). JO-97: active (26 reports), orbit now about 458-465 km and decaying.
    - **Antenna:** 20 cm loop or NA-701 (SMALL) / 12 cm loop (STRICT)
    - **Antenna size cm:** 12-21
    - **Tier:** small
    - **Link margin:** Calculation with an ASSUMED 0.3 W and 36 dB-Hz required. AO-73: +5 / +10 / +15 dB at 10/30/90°. JO-97: +8 / +13.5 / +19 dB. The 12 cm loop is about the same; a 12 cm stubby is 4-5 dB worse but still positive. SSB on JO-97 is opportunistic.
    - **Reachability:** reliable
    - **Receiver:** RTL V4L + LNA V2 + FM band-stop at the antenna; FUNcube-style decoders / gr-satellites
    - **Legal:** Amateur/educational telemetry
    - **Sources:**
      - https://www.amsat.org/status/
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=39444
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=43803
  13.
    - **Satellite:** AO-7 mode B and AO-91 FM (VHF downlinks)
    - **Band:** AO-7: 145.925-145.975 MHz SSB, beacon 145.9775 MHz. AO-91: 145.960 MHz FM plus DUV telemetry.
    - **Capability:** CW beacon, SSB, FM voice
    - **Status oct 2026:** AO-7: active in sunlight (21 'active' / 13 'not heard' reports), orbit about 1450 km. AO-91: intermittent (2 'active' / 7 'not heard'), 430 x 630 km.
    - **Antenna:** 20 cm loop or NA-701 (SMALL) / 12 cm loop (STRICT)
    - **Antenna size cm:** 12-21
    - **Tier:** small
    - **Link margin:** Calculation with ASSUMED EIRPs. AO-7 beacon at 0.2 W: +7 to +15 dB. AO-91 FM at 0.5 W: clean only at zenith (about +1 dB); noisy but readable from about 30° (+1 to +6 dB). Rural noise: the 12 cm loop is about 0.6 dB better than the NA-701.
    - **Reachability:** marginal
    - **Receiver:** RTL V4L + LNA V2 at the antenna
    - **Legal:** Amateur
    - **Evidence:** AO-7 beacon: reliable. AO-91 voice: marginal to opportunistic. Mode B SSB: opportunistic.
    - **Sources:**
      - https://www.amsat.org/status/
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=7530
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=43017
  14.
    - **Satellite:** VHF APRS digipeaters (SONATE-2, GRBBeta, KNACKSAT-2, Marina, CO-128 [VHF Digi])
    - **Band:** Mostly 145.825 MHz 1200 AFSK (frequencies not individually re-verified)
    - **Capability:** APRS/AX.25 digipeat and telemetry
    - **Status oct 2026:** Logged active on AMSAT 13-18 Oct (SONATE-2: 11 reports). NO-44 not heard. The ISS VHF APRS has moved to UHF.
    - **Antenna:** 20 cm loop / NA-701 (SMALL); 12 cm loop (STRICT)
    - **Antenna size cm:** 12-21
    - **Tier:** small
    - **Link margin:** Calculation with an ASSUMED 1 W: -6.5 / -1.3 / +1.2 / +2.7 / +3.9 dB at 10/30/45/60/90°. A 12 cm stubby is negative everywhere.
    - **Reachability:** opportunistic
    - **Receiver:** RTL + LNA V2 + FM band-stop; Direwolf
    - **Legal:** Do not iGate or publish heard positions under martial law
    - **Sources:**
      - https://www.amsat.org/status/
  15.
    - **Satellite:** ISS SSTV on 145.800 MHz (legacy; 2025 events were PD120 on 145.800)
    - **Band:** 145.800 MHz FM
    - **Capability:** SSTV
    - **Status oct 2026:** No 2026 events on 145.800 MHz; they moved to 437.55 MHz. Included in case a future event returns to VHF.
    - **Antenna:** 12 cm stubby or loop, or NA-701
    - **Antenna size cm:** 12-21
    - **Tier:** strict
    - **Link margin:** Calculation at 10 W: +8 to +19 dB over 12 dB CNR from 10° to 90° with the 12 cm loop or NA-701; a 12 cm stubby gives +4 to +15 dB
    - **Reachability:** reliable
    - **Receiver:** RTL + FM band-stop. Avoid 1080p HDMI timing (148.5 MHz clock).
    - **Legal:** Amateur broadcast
    - **Sources:**
      - https://www.ariss.org/upcoming-sstv-events.html
      - https://amsat-uk.org/beginners/iss-sstv/
  16.
    - **Satellite:** GreenCube IO-117 (MEO, about 5800 km)
    - **Band:** 435.310 MHz 1k2 GMSK
    - **Capability:** Digipeater / telemetry
    - **Status oct 2026:** Probably inactive. Last SatNOGS 'good' observation was 25 Jul 2025, it is not on the AMSAT status list for 13-18 Oct, and Celestrak returned 'No GP data found' on 18 Oct 2026 (unexplained).
    - **Antenna:** Any small antenna
    - **Antenna size cm:** n/a
    - **Tier:** none
    - **Link margin:** Path loss 160.8-164.3 dB at 6000-9000 km, about 16-20 dB worse than LEO at 30°
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** Amateur
    - **Sources:**
      - https://network.satnogs.org/observations/12031860/
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=53106
  17.
    - **Satellite:** IO-86 (LAPAN-A2)
    - **Band:** 435.880 MHz FM
    - **Capability:** FM voice, APRS
    - **Status oct 2026:** Logged active on AMSAT, but in a near-equatorial orbit (about 6° inclination, shared AstroSat launch, from memory). Celestrak had no current element set, so this was not re-verified.
    - **Antenna:** Any
    - **Antenna size cm:** n/a
    - **Tier:** none
    - **Link margin:** Geometry: never above the horizon from about 45-52°N
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** Amateur
    - **Sources:**
      - https://www.amsat.org/status/
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=40931
  18.
    - **Satellite:** EXCLUDED: Iridium voice/SMS/pager; Inmarsat and aero ACARS or private messages; Orbcomm user messages; Starlink or other user data; UHF military SATCOM 240-320 MHz; ISS/Soyuz operational VHF voice (SatNOGS lists 143.625 / 130.167 MHz)
    - **Band:** various
    - **Capability:** Private, operational or military communications
    - **Status oct 2026:** n/a
    - **Antenna:** n/a
    - **Antenna size cm:** n/a
    - **Tier:** none
    - **Link margin:** Not assessed
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** EXCLUDED by the project's legal frame. No decoding steps are given.
    - **Sources:**
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=25544
- **Lost vs foldable:**
  1.
    - **Target:** Meteor-M N2-4 LRPT 137.9 MHz
    - **Needed:** Es/N0 of about 4 dB (52.6 dB-Hz) for SatDump lock; about 6 dB for clean images
    - **Gap db:** Calculated SNR change vs the 92 cm V-dipole, including the noise-temperature effect: 20 cm loop -0.3 to -1.3 dB; 12 cm loop -0.6 to -3.0; 20 cm helical -0.9 to -4.9; NA-701 off-resonance -1.7 to -7.7; 12 cm helical -2.2 to -9.1; 5 cm -7.6 to -17.5. The penalty is smallest in residential noise and largest at a quiet rural site. The optional re-marked 137 MHz tape Yagi (+6 dB) is lost entirely.
    - **What would bring it back:** Build the 20 cm tuned copper loop with the SAWbird+ NOAA at its feed and use the IMU to keep the satellite in the loop plane; this keeps about 95% of the V-dipole margin (model). Borderline alternatives are the dipole kit as a V-dipole (92 cm) or the 137 MHz tape Yagi (111 cm).
  2.
    - **Target:** Meteor-M N2-3 LRPT (weaker, VHF antenna not properly deployed)
    - **Needed:** As above, plus an unknown 3-6 dB deployment loss
    - **Gap db:** The same -0.3 to -9 dB as N2-4, with no Yagi option for low passes
    - **What would bring it back:** Only the excluded 137 MHz tape Yagi (+6 dB) or the V-dipole. Otherwise use N2-4 or SatNOGS data.
  3.
    - **Target:** ISS SSTV (now 437.55 MHz, 10 W)
    - **Needed:** FM CNR of about 10-12 dB in 15 kHz
    - **Gap db:** -11 dB vs the 6-element Yagi (12 dB for the 12 cm antenna), but the model still leaves 17.5-18.3 dB CNR at 10°. Nothing is lost in practice. The foldable baseline assumed 145.8 MHz; that is outdated for 2026.
    - **What would bring it back:** Nothing needed
  4.
    - **Target:** 1 W 9k6/1k2 UHF CubeSat telemetry
    - **Needed:** 51.8 dB-Hz (Eb/N0 12 dB at 9600 bps)
    - **Gap db:** -10.8 dB (17 cm whip) / -11.6 dB (12 cm STRICT) vs the 11.0 dBi Yagi. Margin -5.8 / +2.0 / +4.8 dB at 10/45/90°, so only passes above about 40-45° work (about 30% of passes above 10°). 0.5 W satellites and 19k2+ links are lost. Polarisation diversity from crossed Yagi elements is also lost.
    - **What would bring it back:** Borderline: the 70 cm wire Moxon (25 x 10 cm, 5.4 dBi) gives -0.5 / +2.6 / +4.9 dB at 10/20/30°, and the 4-element 70 cm Yagi (29 x 34 cm, 9.5 dBi) gives +3.9 dB at 10°. Within the rule: filtered preamp at the antenna, IQ recording, SatNOGS network fallback.
  5.
    - **Target:** VHF FM, APRS and SSB (AO-91, VHF digipeaters, JO-97/AO-7 SSB)
    - **Needed:** FM/AFSK about 53.8 dB-Hz; SSB about 44 dB-Hz
    - **Gap db:** Antenna gain -9 to -11 dB vs the WB2HOL 7.9 dBi (loop or NA-701), -18 dB for a 12 cm stubby. In rural noise the SNR penalty is about 6.4-7.5 dB (20 cm loop / NA-701) and about 12 dB (12 cm stubby). Only high passes remain.
    - **What would bring it back:** WB2HOL tape Yagi (105 x 51 cm, excluded). Within the rule, a 20 cm loop instead of the NA-701 gains about 1 dB. FUNcube-type BPSK telemetry and CW beacons are not affected in practice: they still have +5 to +19 dB.
  6.
    - **Target:** UHF FM voice (SO-50) and linear-transponder SSB traffic (RS-44, FO-29)
    - **Needed:** FM 48.8-53.8 dB-Hz; SSB about 44 dB-Hz
    - **Gap db:** -11 dB vs the 6-element Yagi. SO-50 drops to opportunistic (overhead passes, noisy). SSB QSOs drop to the strongest stations only. CW beacons are kept (+3 to +13 dB).
    - **What would bring it back:** 70 cm Moxon or 4-element Yagi (borderline), or the 6-element Yagi (excluded)
- **Borderline note:** BORDERLINE, NOT IN THE STACK; listed only so you can reconsider. The single most useful borderline item is the 70 cm wire Moxon (25 x 10 cm, 31 g vendor weight, 5.4 dBi modelled / 6.1 dBi vendor). It adds about +5.4 dB over the 17 cm whip and turns 1 W 9k6 CubeSats from 'passes above 45° only' into 'passes above about 15-20°'; SO-50 and SSB improve by the same 5 dB. The 4-element 70 cm Yagi (29 x 34 cm deployed, packs into 17 cm pieces, 9.5 dBi) recovers all but 1.5 dB of the foldable 6-element Yagi. On VHF, only the WB2HOL tape Yagi (105 x 51 cm, 7.9 dBi) brings back VHF FM, APRS and SSB, and about +6 dB at 137 MHz. The V-dipole kit (92 cm) adds only about 0.3-1.3 dB over a well-built 20 cm tuned loop (model), so it is not worth reinstating unless the loop fails validation. A 34 cm 70 cm dipole adds only about 2 dB over the case whip, so skip it.
- **Notes:** **Bottom line.** Within the rule, what remains:
  - **ISS 70 cm services:** SSTV, APRS and the FM repeater are all reliable, even in the STRICT tier, because ISS SSTV moved to 437.55 MHz.
  - **Meteor-M N2-4 LRPT:** marginal, and close to V-dipole performance, but only with a carefully built tuned loop and an LNA at the feed.
  - **Telemetry and beacons:** FUNcube/JO-97 BPSK telemetry and CW beacons are reliable to marginal.
  - **High passes only:** 1 W UHF CubeSat telemetry works above about 45°.
  - **Mostly lost:** FM voice and SSB QSOs, VHF APRS digipeaters, Meteor N2-3 and low passes.
  
  **Physics.**
  - A quarter wave is 54.5 cm at 137.5 MHz, 51.4 cm at 145.8 MHz and 17.2 cm at 436 MHz. Short monopoles on an ideal ground have very low radiation resistance:
    - 137.5 MHz: 0.21 ohm (5 cm), 1.2 ohm (12 cm), 3.3 ohm (20 cm).
    - 436 MHz: 12 cm has 12 ohm, and a 17 cm whip about 24 ohm, which is essentially resonant.
  - Unloaded short whips are reactive by 400-1200 ohm and lose 24-45 dB to mismatch at VHF, so they must be loaded or tuned. Loading-coil loss then sets efficiency (see small_antennas).
  - **External noise softens the efficiency penalty.** At 137/145 MHz, man-made plus galactic noise is about 2000-2300 K (rural) or 5700-6600 K (residential), against about 100 K for an LNA at the feed. The noise levels are ITU-R P.372 formulas as I recall them; I did not re-fetch the recommendation.
    - A -10.5 dB-efficient 12 cm helical therefore costs only about 4.4 dB of SNR in a rural site and 2.2 dB in a residential one, but about 9 dB at a truly quiet site.
    - Without an LNA at the antenna, small antennas lose another 1-3 dB, so the SAWbird+ NOAA and LNA V2 belong at the antenna.
    - At 436 MHz the sky is only about 170-420 K. Efficiency is not the problem there (17 cm is full size); the gap is lost directivity, which external noise cannot hide.
  
  **Method.**
  - Every gain and margin is my analytic calculation, ±3 dB, using the scripts in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/small_ant/ (phys.py, lb.py, sats.py, extra.py).
  - Relative anchors are W9MDB (2013, calibrated at 146 MHz ±2 dB, UHF uncalibrated), G4ILO (2011) and VK5BR (13 cm 2 m loop). Johanson figures are from its datasheet.
  - The CubeSat model reproduces foldable_partial.json (+5.7 dB at 10° for 11 dBi; I get +5.4 dB because I subtract the Yagi's 0.3 dB efficiency loss).
  - The LRPT EIRP was calibrated to V-dipole reports (+1.5 dBW). EIRPs for SO-50, AO-91, AO-73, beacons and ISS APRS are ASSUMPTIONS and are labelled as such.
  - Budget used: 8 WebSearch calls plus WebFetch and curl on AMSAT, ARISS, SatNOGS DB/network, Celestrak, WMO OSCAR, SatDump, Prom.ua and WiMo.
  
  **Corrections to the input files.**
  1. ISS SSTV is no longer on 145.800 MHz. The 2026 Series 31-34 events are on 437.55 MHz in Robot 36; Series 31 lists 10 W; the next event is 22-25 Oct 2026.
  2. ISS APRS is on 437.825 MHz, not 145.825 (ARISS, 7 Oct 2026).
  3. Both Meteor-M N2-3 and N2-4 currently use 137.900 MHz (SatNOGS, 17-18 Oct 2026). N2-3's VHF antenna is partly undeployed.
  4. GreenCube shows no good SatNOGS data since Jul 2025.
  5. IO-86 is not visible from Ukraine.
  6. The foldable baseline's WB2HOL is no longer needed for ISS SSTV.
  
  **Integration.**
  - Small antennas mounted on the case sit within centimetres of the Q6A, HDMI and buck converters. Their low antenna temperature (400-1200 K at VHF, about 350 K at UHF) makes host self-noise the likely real limit. Put the antenna on a 0.5-1 m thin coax with a ferrite common-mode choke and hold it away from the box; the cable is not counted as antenna size. Keep avoiding 1080p HDMI timings.
  - Mount the loop at least one diameter above the aluminium mid-plate.
  - Validate on the ISS SSTV event of 22-25 Oct 2026 first (an easy target), then on high Meteor N2-4 passes. Compare the loop with the NA-701 by A/B testing, using SatDump SNR as the measure.
  
  **Legal and safety.** Receive-only. Exclusions are as listed. Under martial law, do not publish or iGate APRS positions, geotagged images or station locations. Expect GNSS jamming or spoofing, so enter the location manually for pass prediction. Choose field sites with UXO risk in mind and call 101 if you find anything.
  
  **Unverified.**
  - Real EIRPs of SO-50, AO-91, AO-73 and the ISS APRS radio.
  - Orbcomm status in 2026.
  - Ukrainian stock of the SRH-701, SRH805S, A-V85 and the Johanson chip, and their prices.
  - No published LRPT decode with an antenna under 20 cm exists.

## fold:vhf_uhf (run `wf_4a343103-e9e`)

- **Band group:** VHF/UHF: 137 MHz Meteor-M LRPT, 145.8 MHz ISS SSTV, 435-438 MHz CubeSats (RTL-SDR V4L for 137/145.8 MHz, LimeSDR Micro for 435 MHz). Targets unchanged. Packing targets unchanged: recommended tier has no piece longer than about 35 cm; ultra-compact tier no piece longer than about 20 cm.
- **Options:**
  1.
    - **Band:** 137 MHz (also 145.8 MHz retuned, 435 MHz as a test dipole)
    - **Name:** RTL-SDR Blog multipurpose dipole kit as a 137 MHz V-dipole (current pick, already telescopic)
    - **Type:** buy
    - **Fold method:** Telescopic elements screw into the base on M5 threads. The large pair runs 23 cm to 1 m and the small pair 5-13 cm. The base, flexible tripod and RG174 lead are loose parts.
    - **Packed size cm:** Longest piece 23 cm (collapsed element, verified). Whole kit about 23 x 8 x 5 cm (my estimate; the vendor gives no packed size).
    - **Deployed size cm:** Arms 53.4 cm at 120 deg, about 92 cm tip to tip x 27 cm deep. Hold about 1-1.1 m above ground, axis north-south.
    - **Weight g:** Not published (estimate 150-250 g with tripod)
    - **Setup time:** About 1-2 min: extend the elements to marked lengths and set the angle (estimate)
    - **Gain:** About 1.5-3 dBi toward zenith (NEC2 free-space model, sensitive to feed geometry). Linear polarisation, about 3 dB loss on the RHCP Meteor signal.
    - **Gain vs current pick db:** 0 (this is the current pick)
    - **Price:** $17.95 (RTL-SDR Blog store, in stock Oct 2026, from antennas.json)
    - **Availability:** In stock, ships worldwide from China
    - **Durability notes:** Telescopic sections work loose or pull out, and the tripod legs and terminal block are weak. Carry a spare pair of telescopics. The verify stage's advice to fit fixed 53 cm rods breaks the new folding rule; use 2-3 piece rods joined with M5 couplers instead.
    - **Evidence:** Proven on Meteor LRPT (RTL-SDR.com, SatNOGS). Element lengths and M5 thread are verified on the product page.
    - **Sources:**
      - https://www.rtl-sdr.com/DIPOLE
      - https://www.rtl-sdr.com/simple-noaameteor-weather-satellite-antenna-137-mhz-v-dipole/
      - https://community.libre.space/t/mathematical-modeling-and-physical-optimization-of-v-dipole-antennas-for-vhf-imaging-satellite-reception/14844
      - https://www.ebay.de/urw/RTL-SDR-Blog-Multipurpose-Dipole-Antenna-Kit-DE-SPJS-1110-1874-/product-reviews/9013164391?pgn=1
  2.
    - **Band:** 145.8 MHz, re-markable to 137 MHz
    - **Name:** Roll-up tape-measure 3-el Yagi: WB2HOL dimensions on Axotron-style spools with a split boom
    - **Type:** modify
    - **Fold method:** Each tape half-element rolls onto its own 3D-printed spool at the clamp (Axotron v3: six spools/clamps, one hex pin to wind them). The 16 mm PVC boom splits at the driven-element clamp, and the handle swings aside. Ultra variant: cut the boom into 3 sections of 17-18 cm or less.
    - **Packed size cm:** Axotron boom pieces are 34.7 cm and 27.9 cm (verified), so about 35 x 8 x 6 cm with the spools (estimate). With a 3-piece boom, 18 cm or less.
    - **Deployed size cm:** 105 cm wide (reflector) x 51 cm boom. Axotron boom is 62.6 cm.
    - **Weight g:** About 200-300 g (estimate: 25 mm steel tape about 25 g/m, PVC boom, six spools)
    - **Setup time:** About 2-3 min to unroll six tapes to their marks and join the boom (estimate)
    - **Gain:** 7.9 dBi, F/B 17.7 dB at 145.8 (NEC2; same geometry as the rigid WB2HOL). Steel-tape loss about 0.1 dB. Remarked to 137.5 MHz (all lengths x1.060: R 111.4, DE 2x47.8, D 94.6 cm) on the same boom: 7.7 dBi, F/B 20 dB. The same hairpin gives SWR 1.33 (model).
    - **Gain vs current pick db:** 0 at 145.8 (model). Setting errors of up to 1 cm per half cost at most 0.4 dB gain, but F/B can fall to 12 dB. As a 137 MHz antenna it is about +6 dB over the V-dipole when pointed.
    - **Price:** About $15-30 (tape measure, PVC conduit, PETG prints, hose clamps; estimate)
    - **Availability:** DIY. The Axotron 3MF files are a free zip; tape and PVC are sold in any Ukrainian hardware store.
    - **Durability notes:** The spools stop the tape from kinking, which is the main failure of folded tape elements. Lacquer the tape, use adhesive heat-shrink on the hairpin, and mark lengths for both 145.8 and 137.5 MHz. Check that the clamp bridges the reflector and director halves electrically, because a split parasitic element is detuned.
    - **Evidence:** Axotron v3 is a published, built 2 m fox-hunting tape Yagi with roll-up spools; no gain figure is published. The WB2HOL is proven on ISS. My NEC2 numbers are a model.
    - **Sources:**
      - https://axotron.se/blog/?p=1619
      - https://axotron.se/blog/improved-2-m-fox-hunting-antenna/
      - https://axotron.se/blog/wp-content/uploads/2025/02/2m-antenna-v3.zip
      - https://www.w9rh.org/wp-content/uploads/2024/01/2m-tape-measure-yagi-instructions.pdf
      - https://hamradioprep.com/how-to-build-a-tape-measure-yagi-antenna/
  3.
    - **Band:** 145.8 + 435 MHz (crossed, two feeds)
    - **Name:** Packable crossed 2 m/70 cm Yagi: the current crossed pick rebuilt with roll-up 2 m tapes, pivoting 70 cm elements and a 2 x 35 cm keyed boom
    - **Type:** modify
    - **Fold method:** The 0.70 m boom (20x20 mm square PVC/GRP or wood) splits at 0.35 m with a printed square spigot. The square section keeps the two element planes orthogonal (the ±5 deg rule from the NEC study). The 2 m WB2HOL tapes roll onto spools. Each 70 cm N2SPI #8 Al element turns on one centre screw with a 90 deg detent and lies flat along the boom. Both feeds (2 m DE at 0.20 m, 70 cm DE at 0.094 m) sit on the rear half, so no coax crosses the joint.
    - **Packed size cm:** Two boom halves of 35 cm. The longest 70 cm element is 34 cm and folds along the boom. Bundle about 35 x 10 x 6 cm (estimate).
    - **Deployed size cm:** 105 cm (2 m reflector) x 70 cm boom, with 34 cm vertical 70 cm elements
    - **Weight g:** About 350-500 g (estimate)
    - **Setup time:** About 3-4 min (estimate). A similar folding crossband (alpha_adhito 3x6) takes 1-2 min by its builder's report.
    - **Gain:** 7.9 dBi (2 m) and 11.0 dBi (70 cm), from the existing NEC2 crossed-boom study in antennas.json, if orthogonality stays within ±5 deg
    - **Gain vs current pick db:** 0 / 0 (model). The joint gap of 3.4 cm or more from the 70 cm D2 at 0.316 m keeps the element positions unchanged.
    - **Price:** About $25-40 materials (estimate)
    - **Availability:** DIY
    - **Durability notes:** Use a wing-nut pivot with a detent so elements cannot creep off 90 deg. Use PETG/ASA for the prints. Re-check S11 on both ports after the first assembly, and after any re-marking of the tapes.
    - **Evidence:** Mechanism proven separately: Axotron spools; K6ARK-style and alpha_adhito rotating or folding elements. The combination is my design and untested.
    - **Sources:**
      - https://axotron.se/blog/?p=1619
      - https://community.libre.space/t/collapsible-yagi-antennas/14441
      - https://wiki.oarc.uk/2m0iig-satellite-yagi
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
      - https://www.w9rh.org/wp-content/uploads/2024/01/2m-tape-measure-yagi-instructions.pdf
  4.
    - **Band:** 435-438 MHz
    - **Name:** N2SPI/WA5VJB 6-el 70 cm Yagi on a 2-piece boom with pivoting elements (current pick, made packable)
    - **Type:** modify
    - **Fold method:** Split the 64 cm boom at about 32 cm with a keyed ferrule. Elements pivot on centre screws to lie along the boom, or are pushed through grommets and removed. They stay one-piece, so there is no contact at the current maximum.
    - **Packed size cm:** 34 x 4 x 3 cm per half, about 34 x 5 x 4 cm for the pair (estimate). Longest element 34.0 cm (13-3/8 in reflector).
    - **Deployed size cm:** 64 x 34 cm
    - **Weight g:** About 150-250 g (estimate: #8 Al elements about 42 g plus boom)
    - **Setup time:** About 1-2 min (estimate)
    - **Gain:** 11.0 dBi, F/B 24.9 dB, flat 435-438 MHz (NEC2, reproduced: 11.05/11.03/10.99 dBi at 435/436.5/438)
    - **Gain vs current pick db:** 0
    - **Price:** About $10-15 materials (estimate)
    - **Availability:** DIY
    - **Durability notes:** The half-folded driven element can stay on its pivot with the coax attached. Replace the foam board with a varnished batten or GRP tube.
    - **Evidence:** The N2SPI design was used hand-held for FM LEOs. The split boom and pivots are my modification (untested).
    - **Sources:**
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
      - https://wa5vjb.com/yagi-pdf/cheapyagi.pdf
  5.
    - **Band:** 435-438 MHz (ultra-compact)
    - **Name:** 4-el 70 cm Yagi (N2SPI first four elements on a 28.6 cm boom) with screw-in or banana-plug half-elements
    - **Type:** diy
    - **Fold method:** Boom in two 15 cm pieces. Each element is two 17 cm or shorter half-rods (3-4 mm brass/Al) with M3/M4 threads or 4 mm banana plugs. Parasitic sockets are bridged inside the boom by a brass strip. The driven element becomes a straight split dipole with a hairpin, because the half-folded DE cannot be split. A 5-el variant on a 44.5 cm boom (2 x 22 cm) gives 10.6 dBi.
    - **Packed size cm:** About 17 x 4 x 3 cm (estimate)
    - **Deployed size cm:** 29 x 34 cm
    - **Weight g:** About 80-120 g (estimate)
    - **Setup time:** About 2-3 min for 8 half-elements (estimate)
    - **Gain:** 9.5 dBi, F/B 13 dB (NEC2). DE shortened to 0.97x plus a hairpin gives SWR 1.03-1.47 across 435-438 MHz (model).
    - **Gain vs current pick db:** -1.5 (model)
    - **Price:** About $10-20 materials (estimate)
    - **Availability:** DIY
    - **Durability notes:** 12 loose parts is the risk; colour-code them. A threaded centre joint adds about 0.1 dB at most (estimate). Tune with a VNA.
    - **Evidence:** Model only. No build of this exact cut-down was found.
    - **Sources:**
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
      - https://www.makerworld.com/en/models/2781656
  6.
    - **Band:** 145.8 MHz (also 137 and 435 MHz)
    - **Name:** Telescopic-element 3-el 2 m Yagi (M5 telescopics like the dipole-kit ones on a split boom; ZL1SWW/K6ARK concept)
    - **Type:** diy
    - **Fold method:** Telescopic elements pivot or unscrew at the boom, and the boom splits in 2-3 pieces. Lengths are continuously adjustable, so one antenna covers 137.5 and 145.8 MHz.
    - **Packed size cm:** 23-35 cm (23 cm collapsed telescopics, verified for the RTL-SDR kit; boom pieces 25-35 cm)
    - **Deployed size cm:** About 105 x 51 cm
    - **Weight g:** About 200-300 g (estimate)
    - **Setup time:** About 2-3 min (estimate)
    - **Gain:** About 7.5-7.9 dBi if lengths are set to the WB2HOL values (my NEC model of that geometry). ZL1SWW's 7-el telescopic contest Yagi reached 11 dBi (author's figure).
    - **Gain vs current pick db:** 0 to -0.4 (model)
    - **Price:** About $36 if built from two extra dipole kits (2 x $17.95), or generic telescopics (price unverified)
    - **Availability:** DIY
    - **Durability notes:** Telescopics loosen and wobble (dipole-kit reviews). Mark lengths, and expect element sag in wind. The DE impedance of about 15-25 ohm needs a hairpin, or accept about 1-2 dB mismatch on receive.
    - **Evidence:** Concept proven by ZL1SWW (pivoting telescopics) and the OARC K6ARK-based dual-band. The OARC build is low gain: it starts hearing satellites only at about 40-45 deg elevation.
    - **Sources:**
      - https://www.qsl.net/zl1sww/2mPortable%20Yagi.htm
      - https://wiki.oarc.uk/2m0iig-satellite-yagi
      - https://www.rtl-sdr.com/DIPOLE
  7.
    - **Band:** 145.8 + 435 MHz
    - **Name:** alpha_adhito folding crossband Yagi 3x6 V/U (YD1BDE-based), Thingiverse thing:7090427
    - **Type:** diy
    - **Fold method:** The VHF elements fold, with solder wick bridging the hinge of the parasitic element. The UHF elements are removable. The builder says it folds 'into a small bag'.
    - **Packed size cm:** Not quantified (unverified; the Thingiverse page returned 403)
    - **Deployed size cm:** Not published (3-el 2 m / 6-el 70 cm class, about 1 m x 0.5-0.7 m, estimate)
    - **Weight g:** Not published
    - **Setup time:** 1-2 min (builder's report)
    - **Gain:** Not published. A 3-el / 6-el class is about 7.5-8 / 10-11 dBi (class estimate, not measured).
    - **Gain vs current pick db:** About 0 / 0 (unverified)
    - **Price:** DIY, printed parts plus rods (estimate under $30)
    - **Availability:** Free STL on Thingiverse
    - **Durability notes:** The builder calls it 'not the most sturdy but it works'. 400-500 QSOs in about a year.
    - **Evidence:** First-hand SatNOGS forum report, 24 Feb 2026
    - **Sources:**
      - https://community.libre.space/t/collapsible-yagi-antennas/14441
      - https://www.thingiverse.com/thing:7090427
  8.
    - **Band:** 137 MHz (one per band; 145.8 version also possible)
    - **Name:** Wire Moxon on fiberglass spreaders (homebrew; QRP Lifestyle sells a 144/432 version)
    - **Type:** diy
    - **Fold method:** Wire elements coil up. The X-frame of thin fiberglass rods (not carbon) unplugs from a printed hub.
    - **Packed size cm:** About 30-35 cm, set by the spreader segment length (unverified for any specific rod)
    - **Deployed size cm:** 137 MHz: 80 x 29 cm. 145.8 MHz: 76 x 28 cm (scaled Cebik/Moxgen-class dimensions, model).
    - **Weight g:** About 100-200 g (estimate). The QRP Lifestyle 144 MHz Moxon is 133 g (listing).
    - **Setup time:** About 2-3 min (estimate)
    - **Gain:** About 5.5 dBi, F/B about 16 dB, SWR 1.2-1.4 directly on 50 ohm (NEC2). QRP Lifestyle claims 6.1 dBi and F/B over 15 dB on 2 m. Wide beam, so pointing is easy.
    - **Gain vs current pick db:** 137 MHz: about +4 over the V-dipole. 145.8 MHz: -1.8 to -2.4 vs WB2HOL.
    - **Price:** DIY about $15-25 (estimate). QRP Lifestyle price not found.
    - **Availability:** DIY; QRP Lifestyle via pileupdx (product page 404 at check time)
    - **Durability notes:** Wire geometry must be held taut; fiberglass rods only.
    - **Evidence:** Model plus the vendor benchmark
    - **Sources:**
      - https://pileupdx.com/product/qrp-lifestyle-moxon-144-432
      - https://www.jpole-antenna.com/?p=16440
  9.
    - **Band:** 435-438 MHz
    - **Name:** 70 cm wire Moxon (QRP Lifestyle 432 part or DIY)
    - **Type:** buy
    - **Fold method:** No fold needed: it is already only 25 x 10 cm, and the wire version can be flattened.
    - **Packed size cm:** 25 x 10 x 1-2 cm
    - **Deployed size cm:** 25 x 10 cm (vendor) / about 25 x 9 cm (model)
    - **Weight g:** 31 g (vendor listing)
    - **Setup time:** Under 1 min
    - **Gain:** About 5.4 dBi (NEC2, scaled) / 6.1 dBi (vendor)
    - **Gain vs current pick db:** -4.9 to -5.6
    - **Price:** Not found (DIY under $5)
    - **Availability:** Vendor page 404 at check time
    - **Durability notes:** Robust; small enough to hand-hold with the IMU
    - **Evidence:** Vendor listing via search snippet, plus model
    - **Sources:**
      - https://pileupdx.com/product/qrp-lifestyle-moxon-144-432
  10.
    - **Band:** 137 MHz
    - **Name:** Collapsible QFH (DIY concept: 2-piece mast, screw-in half cross-arms, coiled coax or wire loops)
    - **Type:** diy
    - **Fold method:** Mast in two sections of 30 cm or less. Eight screw-in half-arms of about 18 cm. Flexible loops coiled.
    - **Packed size cm:** About 30-35 cm (estimate; full 137 MHz cross-arms are about 34-37 cm, so they must be split)
    - **Deployed size cm:** About 55-60 cm tall x 35-37 cm (approximate standard 137 MHz QFH dimensions, not re-verified). The rigid Diamond KE-137 is 100 cm tall and 1100 g.
    - **Weight g:** About 300-500 g (estimate)
    - **Setup time:** About 5-10 min, and the geometry must be exact
    - **Gain:** Circular and omni. Expect roughly equal to the V-dipole: no 3 dB polarisation loss, but home builds lose about 1 dB, and one user saw it work only above about 35 deg elevation.
    - **Gain vs current pick db:** About 0 to +2 (unverified)
    - **Price:** About $15-30 (estimate)
    - **Availability:** No tested portable build found. The jcoppens site listing an 'Ekkehard portable construction' was unreachable.
    - **Durability notes:** Fussy, and the loops change shape each time. Not recommended.
    - **Evidence:** Weak: no collapsible 137 MHz QFH product or documented build found
    - **Sources:**
      - https://www.wimo.com/en/ke-137
      - https://www.rtl-sdr.com/simple-noaameteor-weather-satellite-antenna-137-mhz-v-dipole/
  11.
    - **Band:** 435-438 MHz
    - **Name:** Cheap collapsible UHF Yagis (eBay/AliExpress 'Collapsible YAGI Gamma 3/5 element 430-450 MHz', MagicalANT Yagi-U)
    - **Type:** buy
    - **Fold method:** Elements fold along the boom on hinges; gamma match
    - **Packed size cm:** 3-el: '17.7 in' (45 cm) in a search snippet (unverified). 5-el: unknown, likely more than 35 cm.
    - **Deployed size cm:** Unknown
    - **Weight g:** 5-el YID05Q: 530 g (listing snippet)
    - **Setup time:** About 1 min (fold-out)
    - **Gain:** 3-el: 7 dBi claimed, beamwidth 53/45 deg. The 5-el '13 dBi' claim is implausible: NEC of a 5-el on a 44.5 cm boom gives 10.6 dBi.
    - **Gain vs current pick db:** About -4 (3-el, claim-based)
    - **Price:** About $54-75 (eBay listings via search snippets; the 5-el listing has ended)
    - **Availability:** eBay/AliExpress; pages returned 403, so unverified
    - **Durability notes:** Rigidity unknown (unanswered question on SatNOGS). SO-239 connector needs an adapter.
    - **Evidence:** Seller claims only
    - **Sources:**
      - https://community.libre.space/t/collapsible-yagi-antennas/14441
      - https://www.ebay.de/itm/256998624992
      - https://www.ebay.com/itm/175847102985
  12.
    - **Band:** 145.8 + 435 MHz
    - **Name:** Arrow II 146/437-10BP (split boom, two BNC feeds)
    - **Type:** buy
    - **Fold method:** Two-piece boom. Aluminium arrow-shaft elements come off the boom. Fits Arrow's optional roll-up bag.
    - **Packed size cm:** Longest part under 22 in (56 cm), per the vendor. Fails the 35 cm target.
    - **Deployed size cm:** Boom 37.5 in (95 cm) x about 1 m (2 m elements; width unverified)
    - **Weight g:** About 19 oz + 1 oz for the split boom, about 570 g (vendor)
    - **Setup time:** A few minutes. Elements are unlabelled, so colour-code them (NT1K).
    - **Gain:** Not published by Arrow. 3-el / 7-el class.
    - **Gain vs current pick db:** About 0 (class estimate, unverified)
    - **Price:** $156.95 (Moonraker US, from antennas.json)
    - **Availability:** Moonraker UK/EU/US; stock not confirmed
    - **Durability notes:** Arrow shafts and inserts can break or go missing; carry spares
    - **Evidence:** The classic proven satellite handheld
    - **Sources:**
      - https://www.arrowantennas.com/arrowii/146-437.html
      - https://moonrakeronline.com/us/arrow-ii-146-437-10bp-without-duplexer-handheld-portable-satellite-antenna
      - https://nt1k.com/antenna-reviews-arrow-satellite-ii-vs-elk-log-periodic/
  13.
    - **Band:** 145.8 + 435 MHz
    - **Name:** Elk Antennas 2M/440L5 log-periodic
    - **Type:** buy
    - **Fold method:** Elements come off; one-piece boom
    - **Packed size cm:** 24 x 3 x 3 in (61 cm), per the vendor. Fails the target.
    - **Deployed size cm:** 61 cm boom x about 1 m
    - **Weight g:** 822 g (1.8125 lb, vendor)
    - **Setup time:** About 2-3 min (estimate)
    - **Gain:** 8.7 dBi (2 m) / 9 dBi (70 cm), manufacturer figures via Gigaparts
    - **Gain vs current pick db:** +0.8 (2 m) / -2.0 (70 cm)
    - **Price:** $137.95-170.95 (elkantennas.com)
    - **Availability:** US only; shipping to Ukraine not verified
    - **Durability notes:** Rugged, but pointing tolerance is tight. Single feed, so it needs a diplexer to feed both SDRs at once.
    - **Evidence:** Owner reports (NT1K, AMSAT-BB)
    - **Sources:**
      - https://elkantennas.com/product/dual-band-2m440l5-log-periodic-antenna/
      - https://www.gigaparts.com/2m-440l5-dual-band-directional-yagi-antenna.html
  14.
    - **Band:** 145.8 + 435 MHz
    - **Name:** WiMo SOTA-Antenne Dualband 2m/70cm (art. 18503, 5-el log-periodic)
    - **Type:** buy
    - **Fold method:** Breaks down to a 64 cm pack
    - **Packed size cm:** 64 cm (vendor). Fails the target.
    - **Deployed size cm:** 61 x 96 cm
    - **Weight g:** About 600 g
    - **Setup time:** Not stated
    - **Gain:** 5 dBi (2 m) / 7 dBi (70 cm), free space (vendor)
    - **Gain vs current pick db:** -2.9 / -4.0
    - **Price:** EUR 139 incl. VAT (WiMo)
    - **Availability:** In stock, ships in 1-2 days
    - **Durability notes:** Single BNC, so both bands share one feed
    - **Evidence:** Vendor data
    - **Sources:**
      - https://www.wimo.com/de/sota-antenne
  15.
    - **Band:** 145.8 MHz (and 435 MHz)
    - **Name:** Dipole kit only (straight dipole, arms about 49 cm for 145.8; small elements for 435)
    - **Type:** buy
    - **Fold method:** Telescopic
    - **Packed size cm:** 23 cm
    - **Deployed size cm:** About 98 cm span (145.8) / about 33 cm (435)
    - **Weight g:** Same kit as the 137 MHz V-dipole
    - **Setup time:** Under 1 min
    - **Gain:** 2.1 dBi (NEC2)
    - **Gain vs current pick db:** -5.8 at 145.8 / -8.9 at 435
    - **Price:** $0 extra (same kit)
    - **Availability:** In stock
    - **Durability notes:** See the dipole kit entry
    - **Evidence:** AMSAT-UK: 'a 2m handheld with a 1/4 wave antenna will be enough' for ISS SSTV (about 25 W output)
    - **Sources:**
      - https://amsat-uk.org/beginners/iss-sstv/
      - https://community.libre.space/t/iss-sstv-ariss-sstv-experiment-october-8-14/12325
- **Recommended:** Recommended foldable kit (no piece longer than 35 cm, all three bands at the same modelled gain as the rigid picks):
  
  (1) **137 MHz:** keep the RTL-SDR Blog dipole kit as the V-dipole ($17.95). It already packs to 23 cm. Carry a spare telescopic pair. Do not follow the verify stage's advice to fit fixed 53 cm rods.
  
  (2) **145.8 + 435 MHz:** the current crossed Yagi rebuilt to pack:
  - The 0.70 m boom becomes two keyed 35 cm halves of square section, which keeps the planes within ±5 deg.
  - The WB2HOL 2 m tape elements roll onto Axotron-style printed spools.
  - The N2SPI 6-el 70 cm #8 Al elements pivot flat on centre screws.
  - The two feeds stay on the rear half.
  - Packed size is about 35 x 10 x 6 cm and weight about 350-500 g (estimate).
  - Setup takes about 3-4 min and materials cost about $25-40.
  - Gain stays 7.9 / 11.0 dBi (NEC model), so 0 dB change.
  
  Bonus: mark the 2 m tapes for 137.5 MHz too (R 111.4, DE 2x47.8, D 94.6 cm). The 2 m half then becomes a 7.7 dBi Meteor Yagi, about +6 dB over the V-dipole (model), for Meteor-M N2-3 and low passes. The same hairpin gives SWR 1.33.
  
  If you don't want the crossed build, use two separate packable antennas instead, at the same gains: the Axotron-style tape Yagi (boom pieces 34.7 and 27.9 cm) and the split-boom N2SPI (34 cm).
  
  No commercial antenna meets 35 cm. The Arrow II 10BP packs to 56 cm, the Elk to 61 cm and the WiMo SOTA to 64 cm.
- **Ultra compact:** Ultra-compact kit (aim: no piece longer than 20 cm):
  
  - **137 and 145.8 MHz:** the dipole kit: V-dipole at 53.4 cm arms, straight dipole at about 49 cm arms for ISS. Its collapsed elements are 23 cm, 3 cm over the target; no shorter M5 telescopic was found. To reach 20 cm, use 3-piece M5-coupled rods or tape arms on spools (concept, untested).
  - **435 MHz:** a 4-element 70 cm Yagi using the first four N2SPI elements on a 28.6 cm boom split into two 15 cm pieces. Half-elements of 17 cm or less screw in or use banana plugs, with a split DE plus hairpin. It models at 9.5 dBi (-1.5 dB vs the 6-el), F/B 13 dB, SWR 1.03-1.47 across 435-438 MHz.
  
  Total about 23 x 8 x 6 cm and under about 400 g (estimate), about $30-40.
  
  Optional: the 2 m roll-up tape Yagi with a 3-piece boom (18 cm or shorter sections) restores 7.9 dBi at 145.8 and 7.7 dBi at 137.5. It costs about 4 min of setup.
- **Losses:**
  1.
    - **Target:** Meteor-M LRPT 137 MHz, recommended kit
    - **With foldable kit:** kept
    - **Margin change db:** 0 (same V-dipole). Optional +6 dB (model) using the re-marked 2 m tape Yagi, hand-pointed.
    - **What we lose:** Nothing in RF terms. The only loss is the verify stage's 'fixed 53 cm rods' durability fix, so telescopic wear remains.
    - **Workaround:** Carry a spare telescopic pair or 3-piece M5 rods. Mount at about 1-1.1 m. Fit the FM band-stop. Use the tape Yagi on N2-3 and low passes.
  2.
    - **Target:** ISS SSTV 145.8 MHz, recommended kit
    - **With foldable kit:** kept
    - **Margin change db:** 0 (model). Worst-case length-setting error costs 0.4 dB gain, and F/B may fall from 17.7 to about 12 dB.
    - **What we lose:** About 2-3 min more setup than the rigid boom (unrolling six tapes). Steel tape needs care against kinks and rust.
    - **Workaround:** Print length marks on the tapes, use a VNA check once, and lacquer the tape
  3.
    - **Target:** CubeSats 435-438 MHz, recommended kit
    - **With foldable kit:** kept
    - **Margin change db:** 0 (11.0 dBi model). Margin model for a 1 W 9k6 FSK satellite: about +5.7 dB at 10 deg and +11 dB at 30 deg elevation.
    - **What we lose:** Nothing in gain. A pivot that creeps more than 10-20 deg off 90 deg costs 0.2-0.8 dB and some F/B (crossed-boom NEC data).
    - **Workaround:** Detented pivots and a square keyed boom joint
  4.
    - **Target:** Meteor-M LRPT 137 MHz, ultra-compact kit
    - **With foldable kit:** kept
    - **Margin change db:** 0
    - **What we lose:** No Yagi option unless the 3-piece tape Yagi is added. The longest piece is 23 cm, not 20 cm.
    - **Workaround:** Add the 3-section tape Yagi (+6 dB, model) for weak passes
  5.
    - **Target:** ISS SSTV 145.8 MHz, ultra-compact kit (dipole only)
    - **With foldable kit:** degraded
    - **Margin change db:** -5.8 vs the WB2HOL (2.1 vs 7.9 dBi). Model CNR in 15 kHz is still about +28 dB at 10 deg (25 W; about +21 dB if only 5 W), far above the FM threshold of about 12 dB.
    - **What we lose:** Directivity: no 17.7 dB F/B against terrestrial QRM such as APRS 144.800 and local noise. Less robustness on low and terrain-blocked passes and in dipole pattern nulls. Image quality is unaffected on normal passes (AMSAT-UK: a 1/4-wave handheld is enough).
    - **Workaround:** Higher ground, the FM band-stop, passes above about 20 deg, IQ recording. Add the 3-section tape Yagi to restore 0 dB.
  6.
    - **Target:** CubeSats 435-438 MHz, ultra-compact kit (4-el 70 cm)
    - **With foldable kit:** degraded
    - **Margin change db:** -1.5 (9.5 vs 11.0 dBi). Model margin for 1 W 9k6 is about +4.2 dB at 10 deg vs +5.7 dB.
    - **What we lose:** F/B drops from 25 to about 13 dB. The weakest 0.5 W satellites lose about 1.5 dB at the horizon. Setup involves 8 loose half-elements.
    - **Workaround:** Filtered 70 cm LNA at the feed (e.g. Uputronics 435 preamp from rf_frontend). Pick passes above 20 deg, or use the 5-el 44.5 cm variant (-0.4 dB) if 22 cm pieces are acceptable.
  7.
    - **Target:** CubeSats 435-438 MHz, dipole-only fallback (no 70 cm Yagi at all)
    - **With foldable kit:** degraded
    - **Margin change db:** -8.9 (2.15 vs 11.0 dBi). Model margin for 1 W 9k6 is -3.2 dB at 10 deg, about 0 at 20 deg, +2.2 at 30 deg, +6 to +7 above 60 deg.
    - **What we lose:** Effectively lost: low-elevation passes, 0.5 W and weaker satellites, and higher-rate (19k2+) links. Only high passes of 1 W 9k6 satellites remain, with polarisation fades.
    - **Workaround:** Fly only passes above about 45-60 deg; FSPL is 8-9 dB lower than at 10 deg, which offsets the gain loss. Add an LNA and use SatNOGS network data for missed satellites.
- **Other ways out:**
  - Choose high passes: at 500 km altitude, path loss at 436.5 MHz is 149.8 dB at 10 deg elevation, 144.4 dB at 30 deg and 140.4 dB at 60 deg. Flying only passes above 45-60 deg recovers 8-9 dB, about what a dipole loses to the 6-el Yagi, at the cost of fewer usable passes per day.
  - Polarisation diversity on 435 MHz: two crossed 70 cm element sets on the same split boom feed both LimeSDR RX channels, which share one LO and so can both sit on 435. Software maximum-ratio or RHCP combining then removes most of the 3 dB polarisation loss and the deep fades from tumbling CubeSats. The cost is a second set of six pivot elements (about 40 g).
  - LNA at the feed: at 435 MHz the Lime's noise figure matters, so a filtered 70 cm preamp recovers about 1-3 dB of system noise (estimate). At 137/145.8 MHz external noise dominates, so an LNA buys little; use the FM band-stop instead.
  - Record IQ and decode offline (SatDump, gr-satellites with the satellite's .yml). Several demodulator settings can be retried on marginal passes.
  - Use the SatNOGS network as a fallback for CubeSat frames the handheld cannot close: you lose your own reception but keep the data.
  - A rigid Yagi kept at a home or car base is unaffected by the backpack rule. Only the travel kit has to fold.
  - Mount on the dipole kit's tripod or the Arrow-style 1/4-20 tripod thread to remove arm fatigue on 10-15 min Meteor passes. The re-marked 137 MHz tape Yagi's wide beam (3-el) tolerates rough pointing.
- **Notes:** **Basis.** I reused antennas.json:
  - picks: V-dipole kit, crossed WB2HOL 7.9 dBi + N2SPI 11.0 dBi on a 0.7 m boom
  - the NEC crossed-boom study
  - the ISS and dipole evidence
  
  The digest and dish_replacement.json have no VHF/UHF link budgets. The absolute margins above therefore come from my own simple model (scripts/nec_vhf/lb.py), and are good to about ±5 dB:
  - CubeSat: 1 W EIRP minus 3 dB pattern loss, 3 dB polarisation and 1.5 dB miscellaneous loss, Tsys 300 K with an LNA, Eb/N0 of 12 dB required at 9600 bps
  - ISS: 25 W per AMSAT-UK, Tsys 1500 K
  
  Treat the relative dB changes as the reliable output.
  
  **Models.** All gains marked 'NEC2' are my free-space, perfect-conductor PyNEC models: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/nec_vhf/m.py, m2.py and m3.py. Steel tape adds about 0.1 dB of loss. My tape-arm V-dipole runs gave unreliable junction results, so I do not quote them; tune tape arms with a VNA. The WB2HOL and N2SPI reproductions match the earlier study (7.89 and 11.03 dBi).
  
  **Key physical constraint.**
  - 70 cm elements, 34 cm at most, fit the 35 cm tier unsplit.
  - 2 m and 137 MHz elements (89-111 cm) must roll, telescope or split into 3+ pieces in any tier.
  - The ultra 20 cm tier also forces split 70 cm elements.
  
  **Errors and conflicts in the input.** The verify stage's fix 'fit fixed 53 cm rods' to the V-dipole now breaks the fold rule. The 0.7 m crossed boom and the 76 cm N2SPI batten are both non-compliant as specified, and must be split as described.
  
  **Commercial check.**
  - No commercial dual-band satellite antenna packs to 35 cm or less: Arrow II 10BP under 56 cm, Elk 2M/440L5 61 cm, WiMo SOTA LPDA 64 cm (EUR 139, 5/7 dBi).
  - Cheap eBay/AliExpress collapsible UHF Yagis exist ($54-75; 7 dBi claimed for the 3-el). Their 13 dBi claim for a 5-el is implausible. I could not inspect them: eBay returned 403.
  
  **Not verified.**
  - Thingiverse 7090427 (403)
  - homingin.com KC6MEH folding tape Yagis (503)
  - jcoppens QFH 'portable construction' (DNS failure)
  - the QRP Lifestyle Moxon page (404; figures from a search snippet)
  
  **Rejected as non-compliant.**
  - KB6NU-listed Thingiverse 3042505: tape elements stored inside the tube, so it packs to about the boom length
  - OARC K6ARK-based telescopic: 1 m boom, low gain
  
  **What is documented and what is new.** Axotron v3's roll-up spools and split boom are a documented build; the crossed packable variant and the split or pivot N2SPI are my untested modifications. Budget: 17 WebSearch calls.

## fold:lband_sband (run `wf_4a343103-e9e`)

- **Band group:** L-band HRPT/AHRPT 1.69-1.71 GHz and S-band 2.2-2.3 GHz (foldable replacements for the rigid 11-turn helix (473 mm on a 20x20 cm plate) and the rigid helicone (440 mm cone))
- **Options:**
  1.
    - **Band:** L (1.69-1.71 GHz); S-band via a swap-in helix in the same cone
    - **Name:** Fold-flat PETAL helicone: 18 cm base disc + 8 clip-on aluminium petals (cone 18 to 44 cm, 12 cm deep) + 5-turn C=1.1λ RHCP spring helix
    - **Type:** diy
    - **Fold method:** The cone is 8 trapezoid petals of 0.3-0.5 mm aluminium, each about 6.9 cm wide at the bottom, 16.8 cm at the top and 17.7 cm along the slant, plus 1 cm overlap tabs. They clip onto the rim of a 1.5 mm aluminium base disc 18 cm across, with no tools, and lie flat in a stack for transport. The cone wall sits 47° from the axis. The helix is 2 mm phosphor-bronze or copper-clad-steel spring wire wound at 61.7 mm diameter with a 43 mm pitch. It compresses flat onto a 2-section fibreglass rod and is pulled up into printed pitch stops. The SAWbird+ GOES bolts under the disc.
    - **Packed size cm:** Petal stack plus disc about 19 x 19 x 3-4 cm. Helix compressed is about 7 cm across x 3 cm; the rod collapses to about 20 cm (or use a rigid 5-turn helix tube about 7 x 23 cm). All within the 30-35 cm tier.
    - **Deployed size cm:** Cone 44 cm across x 12 cm deep; helix 21.5 cm tall; about 44 x 44 x 23 cm overall
    - **Weight g:** About 350-450 g (estimate)
    - **Setup time:** 2-3 min: 8 clips, pull up the helix, screw on the SMA
    - **Gain:** 15.7 dBic at 1.70 GHz (my NEC2 model), flat at 15.6-15.7 from 1.65 to 1.75 GHz, beam 24-28° wide. A 4-turn helix models 15.7 and a 7-turn 16.0 dBic. A t0nito-like shallower cone (9 cm deep) models 14.8-15.3.
    - **Gain vs current pick db:** +2.2 dB vs the rigid 11-turn helix (13.5). Like-for-like in my model it is +1.7 dB (13.98 for an 11-turn on a 20 cm disc). +1.0 dB vs the rigid 40 cm/15 cm helicone (14.7; my model reproduces 14.74). Models are ±1-3 dB.
    - **Price:** About $20-35 in materials (aluminium sheet and disc, wire, PETG stops, clips; estimate), plus the SAWbird+ GOES ($44.95) already in the kit
    - **Availability:** DIY from hardware-store aluminium, wire and fibreglass rod (available in Ukraine; prices not verified)
    - **Durability notes:** Overlap the petals at least 1 cm so the radial seams don't break the surface currents (an assumption, not modelled). Store the petals flat in a stiff sleeve because dents only cost a little. Don't use soft copper for the spring helix: it work-hardens. Phosphor bronze, Cu-clad steel and even stainless model within 0.06 dB of copper. Per-turn pitch errors of ±6 mm cost 0.3 dB or less, and a ±15% overall stretch error costs 0.3 dB or less (model). The cone catches wind like a small umbrella.
    - **Evidence:** Field precedent for the shape: the t0nito/pe2bz helicone (134 mm base to 440 mm top, 88 mm high, mesh on 8 printed holders) gave clearly stronger signals than a flat reflector at 1545, 1700 and 2250 MHz. Saveitforparts hand-tracked NOAA HRPT with it. No folding version and no SNR figures were published. The gains here are my NEC2 models (PyNEC 2.3.4, wire-grid cone), scripts in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/nec_fold/.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://www.rtl-sdr.com/saveitforparts-testing-a-3d-printable-satellite-antenna-for-noaa-meteor-and-other-polar-orbiting-l-band-satellites/
      - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
  2.
    - **Band:** L (1.69-1.71 GHz)
    - **Name:** Pocket FABRIC helicone ('umbrella cone'): same 18 to 44 cm, 12 cm deep cone in copper-nickel ripstop on 8 hinged fibreglass ribs + 4-turn spring helix
    - **Type:** diy
    - **Fold method:** Eight 3 mm fibreglass ribs (kite spars) about 17.7 cm long are hinged at the edge of an 18 cm base disc and fold inward over it. The CuNi ripstop cone is cut as a 265° annular sector, inner radius 12.2 cm and outer 29.9 cm, and is taped or sewn to the ribs. An elastic cord holds the rim. The 4-turn spring helix (61.7 mm diameter, 172 mm tall) compresses to about 1 cm.
    - **Packed size cm:** A disc about 19 cm across x 3-4 cm thick, plus a rod 18 cm or shorter. Everything is 20 cm or less, so it meets the ultra-compact tier.
    - **Deployed size cm:** 44 cm across x 12 cm cone; helix 18 cm
    - **Weight g:** About 250-350 g (estimate)
    - **Setup time:** 1-2 min
    - **Gain:** 15.6 dBic modelled with octagonal flat facets between the ribs (an ideal cone gives 15.7)
    - **Gain vs current pick db:** +2.1 dB vs the rigid 11-turn (+1.6 like-for-like); +0.9 vs the rigid helicone (models)
    - **Price:** About $15-30 (estimate). A 1 m x 1.1 m piece of CuNi fabric costs about $10-15 (UK listing GBP 83 for an 8 x 1.1 m roll; not verified for Ukraine), plus kite spars, disc and wire.
    - **Availability:** CuNi 'Faraday/RFID' fabric is sold on AliExpress, Walmart and U-buy. No Prom.ua per-metre listing was found. Aluminium fly-screen mesh is a stiffer local alternative.
    - **Durability notes:** Fabric only works as a continuous conductive sheet. Laird and Schlegel CuNi ripstop measures 0.07 Ω/sq or less with more than 62-96 dB of shielding, and Holland's mesh 0.13 Ω/sq or less up to 10 GHz. My model shows sparse radial wires without fabric collapse the gain (8 radials: 10.9 dBic; 4 radials: 8.4), so the fabric must not tear. The ribs can splinter, so cap them with heat-shrink. The fabric is the part most likely to wear first.
    - **Evidence:** There is no field precedent for a fabric helicone. The cone shape follows the t0nito mesh-on-8-holders build. The fabric figures are vendor datasheets. The gains are my model.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://www.directindustry.com/prod/schlegel-electronic-materials/product-229436-2314787.html
      - https://hollandshielding.com/pdfs/Conductive-mesh-8900-TDS-rev-02-06-2026.pdf
      - https://marianinc.com/wp-content/uploads/2025/08/PS-1373.pdf
      - https://www.u-buy.co.uk/product/QV08DUB3A-military-grade-faraday-fabric-5g-emf-protection-signal-shielding-fabric-faraday-material-nickel-copper-faraday-cloth-conductive-for-shields-rfid
  3.
    - **Band:** L (1.69-1.71 GHz)
    - **Name:** Spring/telescopic 11-turn C=1.1λ helix + foldable ground plane (hinged 20x20 plate OR a 30 cm pop-up CuNi disc, optional 4 cm cup rim)
    - **Type:** modify
    - **Fold method:** The existing 11-turn design (61.7 mm diameter, 43 mm pitch, 473 mm) is wound from spring wire. It is stretched along a 3-section telescopic fibreglass rod into printed pitch stops and compresses to about 3 cm. For the ground plane there are three choices: (a) two 10x20 cm aluminium halves on a piano hinge; (b) a twist-fold spring-steel hoop covered in CuNi fabric (a 56 cm photo reflector folds to 23 cm and weighs 274 g, so a 30 cm hoop should fold to about 12 cm); (c) an 18 cm disc with a 4 cm fabric rim flaring to 24 cm.
    - **Packed size cm:** Ground plane 20 x 10 x 0.5 cm (hinged) or about 12-13 cm across x 2 cm (pop-up); rod about 18-20 cm; helix about 7 cm across x 3 cm
    - **Deployed size cm:** 20-30 cm ground plane; 48-50 cm tall
    - **Weight g:** About 200-300 g (estimate)
    - **Setup time:** 1-2 min
    - **Gain:** Modelled: 20 cm disc 13.98, 30 cm disc 13.88, 14 cm disc 13.71, cup rim 14.48 dBic. A 40 cm disc drops to 13.14. 8-turn 12.9, 6-turn 12.0, 5-turn 11.6.
    - **Gain vs current pick db:** -0.3 to +0.5 dB (cup rim) vs the rigid 11-turn helix, i.e. essentially the same if the ground is solid or fabric. -1.0 to -1.5 dB vs the rigid helicone.
    - **Price:** About $10-25 (estimate); the photo-reflector frame price was not verified
    - **Availability:** DIY. Photo pop-up reflectors are widely sold; the stock 'silver' cover's conductivity is unverified, so test it with an ohmmeter or recover it with CuNi fabric.
    - **Durability notes:** It is the simplest to get right because the geometry is the proven rigid pick. It is tolerant: ±6 mm per-turn pitch error costs 0.3 dB or less and ±4 mm radius error 0.4 dB or less (model). The hinge must be continuous metal.
    - **Evidence:** The rigid version is field-proven: Meti's 11-turn helix gave about 7 dB average SNR on Meteor-M2-3, and bending up the ground-plane edges gained about 1.5 dB. The collapsible version is untested; the gains are my model.
    - **Sources:**
      - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
      - https://www.skroutz.mt/s/65550879/smallrig-foldable-photography-reflector-60cm.html
      - https://patents.google.com/patent/US9142882
      - https://patents.google.com/patent/DE202010013085U1/en
  4.
    - **Band:** L and S (one antenna)
    - **Name:** Dual-band C=0.9λ 7-turn helix in the fold-flat 44 cm cone
    - **Type:** diy
    - **Fold method:** Same petal or fabric cone. The helix is 50.5 mm across with a 35.2 mm pitch and is 246 mm long as a spring. Swap the LNA at the feed (SAWbird+ GOES for L-band; wideband LNA plus Sysmocom cf2235-kt30 cavity for S-band) or use a diplexer.
    - **Packed size cm:** As for the petal or fabric helicone: about 19 x 19 x 4 cm plus a rod of about 20-25 cm
    - **Deployed size cm:** 44 cm across x about 25 cm
    - **Weight g:** About 300-450 g (estimate)
    - **Setup time:** 2-3 min plus an LNA swap
    - **Gain:** 14.4 dBic at 1.70 GHz and 15.4 dBic at 2.25 GHz (model)
    - **Gain vs current pick db:** L-band: +0.9 vs the rigid 11-turn, but -1.3 vs the C=1.1 fold helicone. S-band: +1.9 to +2.2 vs the rigid C=0.9 11-turn S helix (13.2-13.5 dBic).
    - **Price:** About $20-35 in materials (estimate). The S-band chain is extra: Sysmocom cf2235-kt30 EUR 65.45 plus an LNA.
    - **Availability:** DIY
    - **Durability notes:** Same as the cone options. The SAWbird+ GOES passes only 1648-1728 MHz, so S-band always needs its own LNA and filter.
    - **Evidence:** Model only. The 75%-scaled t0nito helicone did receive S-band on SatNOGS.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://shop.sysmocom.de/S-Band-cavity-filter-2170-2300-MHz/cf2235-kt30
  5.
    - **Band:** S (2.2-2.3 GHz)
    - **Name:** S-band helix in the L-band fold cone (7-turn C=1.1λ at 2.25 GHz) OR a dedicated 33 cm S-band fold cone with a 5-turn helix
    - **Type:** diy
    - **Fold method:** (a) A 7-turn helix, 46.7 mm across with a 32.5 mm pitch and 228 mm long, on its own SMA. It nests inside the 61.7 mm L-band helix for transport. (b) A separate cone scaled to 75% (13.6 cm base to 33 cm rim, 9 cm deep) in petals or fabric, with a 5-turn helix about 16 cm tall.
    - **Packed size cm:** (a) No extra bulk beyond the helix. (b) About 14 cm across x 3 cm, plus a 16-17 cm helix. Ultra-compact tier.
    - **Deployed size cm:** (a) 44 cm cone. (b) 33 cm cone.
    - **Weight g:** (a) About 30-50 g extra. (b) About 200-250 g (estimate).
    - **Setup time:** (a) 30 s to swap. (b) 1-2 min.
    - **Gain:** (a) 14.2 dBic (a 5-turn in the L cone gives only 13.0). (b) 15.5 dBic. Both at 2.25 GHz, modelled.
    - **Gain vs current pick db:** (a) +0.7 to +1.0 dB. (b) +2.0 to +2.3 dB vs the rigid C=0.9 11-turn S helix (13.2-13.5 dBic).
    - **Price:** (a) About $3-5. (b) About $10-20 (estimate). Plus the S-band LNA and cavity.
    - **Availability:** DIY
    - **Durability notes:** Same as the L-band cones. Wi-Fi 2.4 GHz and LTE sit near the band, so the cavity filter is mandatory.
    - **Evidence:** pe2bz: the 75%-scaled helicone 'There is reception' at 2250 MHz, and after 72 h it found three weak S-band satellites missed before. The gains here are my model.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://community.libre.space/t/station-4125-s-band/13718
  6.
    - **Band:** L (Metop-oriented)
    - **Name:** Fold-flat 2x2 array of spring helices on a 56-60 cm pop-up CuNi ground + 4-way Wilkinson combiner
    - **Type:** diy
    - **Fold method:** Four 7- or 11-turn spring helices on telescopic fibreglass rods stand at about 28-30 cm spacing on a twist-fold spring-hoop ground. A 56 cm photo reflector folds to 23 cm, 274 g; recover it in CuNi fabric. Four equal-length cables run to an RF ONE PDM-00503-S4 combiner (0.7 dB loss, 0.5-3 GHz).
    - **Packed size cm:** A disc about 23 cm across x 2-3 cm, plus 4 compressed helices (about 7 x 3 cm each), 4 rods 20 cm or shorter, a combiner and cables. The 30-35 cm tier.
    - **Deployed size cm:** About 56-60 x 56-60 cm; 30-50 cm tall
    - **Weight g:** About 0.9-1.3 kg with a tripod head (estimate)
    - **Setup time:** 5-10 min plus a pan-tilt tripod
    - **Gain:** Modelled before the combiner: 11-turn 18.75, 7-turn 17.8, 5-turn 16.8 dBic. After the 0.7 dB combiner: 18.0 / 17.1 / 16.1 dBic.
    - **Gain vs current pick db:** +4.5 dB (11-turn) / +3.6 dB (7-turn) vs the rigid 11-turn helix
    - **Price:** About $40-80 in materials (estimate). Combiner and pop-up frame prices are not verified. Optionally 4 SAWbirds at $44.95 each instead of combining before the LNA.
    - **Availability:** DIY. The combiner is from RF ONE through distributors.
    - **Durability notes:** The most complex option. Phase matching needs equal cables and a matching strip per helix, checked with a VNA covering 3 GHz or more. Do not use LimeSDR RX1/RX2 software combining until channel alignment is fixed: LimeSuiteNG issue #356 is open and the LMS7002M flips phase by 0/180° on retune.
    - **Evidence:** Model only. Nobody has documented a dish-free Metop decode.
    - **Sources:**
      - https://www.everythingrf.com/products/power-dividers/rf-one-electronics/612-1911-pdm-00503-s4
      - https://www.skroutz.mt/s/65550879/smallrig-foldable-photography-reflector-60cm.html
      - https://discourse.myriadrf.org/t/limesdr-xtrx-rx-data-out-of-sync/13290
      - https://www.amrita.edu/publication/design-of-axial-mode-helical-antenna-array-for-noaa-18-hrpt-reception-at-1700mhz/
  7.
    - **Band:** L and S
    - **Name:** Flat 2x2 CP patch-tile array (4 air-dielectric corner-truncated patches on 13x13 cm tiles + 4-way combiner)
    - **Type:** diy
    - **Fold method:** Four separate tiles stack like coasters and clip onto a folding X-frame at about 0.75λ spacing (about 13 cm), with 4 equal SMA cables to a Wilkinson combiner. Or one 26x26 cm board hinged once.
    - **Packed size cm:** About 13 x 13 x 4 cm (tiles), or 26 x 13 x 1 cm (hinged board). Ultra-compact.
    - **Deployed size cm:** About 26 x 26 x 1-2 cm
    - **Weight g:** About 300-500 g (estimate)
    - **Setup time:** 3-5 min (4 SMA connections)
    - **Gain:** About 11-13 dBic (estimate). The physical limit for 26x26 cm is 14.4 dBi at 100% efficiency; a measured A*STAR 2x2 L-band array gives more than 11.0 dBic over 1.51-1.68 GHz.
    - **Gain vs current pick db:** -0.5 to -2.5 dB vs the rigid 11-turn helix
    - **Price:** About $20-50 DIY (estimate). No commercial 1.7 GHz RHCP 2x2 board or Gerber was found.
    - **Availability:** DIY only (would need a design scaled and simulated for 1.70 GHz)
    - **Durability notes:** Robust once built, but the CP patch tuning and feed network are the hardest DIY step. No advantage over the helicone.
    - **Evidence:** Only the literature: A*STAR EuCAP 2024, an INMARSAT/GNSS band 2x2. No HRPT use found.
    - **Sources:**
      - https://oar.a-star.edu.sg/communities-collections/articles/19720
      - https://ntrs.nasa.gov/api/citations/19670009367/downloads/19670009367.pdf
  8.
    - **Band:** L and S
    - **Name:** 20 cm dual-polarised 4G/LTE MIMO panel, 1700-2700 MHz (R-Net 'Kvadrat' 2x17, 205x205x50 mm)
    - **Type:** buy
    - **Fold method:** Does not fold. It is a flat 'book', so it fits the size targets but not the spirit of 'must fold'. Bigger panels (Energy 2x24, 43x43 cm) fail the packing target.
    - **Packed size cm:** 20.5 x 20.5 x 5 cm
    - **Deployed size cm:** 20.5 x 20.5 x 5 cm
    - **Weight g:** About 600 g (listing)
    - **Setup time:** 0-1 min
    - **Gain:** The '17 dBi' label is impossible: its aperture caps it at 12.3 dBi at 1.70 GHz. Realistic is about 10-11 dBi linear, and 1.70 GHz is below its 1710 MHz band edge. On an RHCP satellite one port gives about 7-8 dBic-equivalent. Both ports through a 90° hybrid give about 10-10.5 dBic. At 2.25 GHz, about 11-13 dBi per port.
    - **Gain vs current pick db:** L-band: -5.5 to -6.5 dB on a single port; -3 to -4 dB with a hybrid. S-band: -3.5 to -5.5 dB single port; -0.5 to -2.5 dB with a hybrid.
    - **Price:** 1900 UAH for the R-Net (Energy 2x15 at 230 mm: 935 UAH). Connectorised 90° hybrids are expensive (E-meca 1.7-2.2 GHz N-type $504; Pasternack 1-18 GHz $1,100), so use a DIY branch-line coupler or software combining.
    - **Availability:** In stock on Prom.ua (Ukraine)
    - **Durability notes:** Rugged and weatherproof. Real gain and match at 1.70 GHz are unverified, so measure with a VNA. Software combining hits the LimeSDR phase-alignment issue.
    - **Evidence:** Only Prom.ua specs and my aperture calculation. No HRPT reports with these panels.
    - **Sources:**
      - https://prom.ua/Antenny-mimo-2x2.html
      - https://e-meca.com/collections/3-db-hybrids-couplers
      - https://www.pasternack.com/sma-coupler-18-ghz-pe2cp1144-p.aspx
  9.
    - **Band:** L
    - **Name:** Segmented 1.7 GHz loop Yagi (26 elements, 1.81 m boom in 6 push-fit 30 cm sections)
    - **Type:** diy
    - **Fold method:** Square aluminium boom in 6 plug-together sections of about 30 cm. The loops (about 6 cm across) stay riveted to their section.
    - **Packed size cm:** About 31 x 8 x 8 cm bundle
    - **Deployed size cm:** 181 cm long
    - **Weight g:** About 400-700 g (estimate)
    - **Setup time:** 2-3 min, plus a tripod or mount
    - **Gain:** About 20 dBi linear. This is a reader's estimate, not measured. On RHCP that is about 17 dBic-equivalent after the 3 dB polarisation loss.
    - **Gain vs current pick db:** About +3.5 dB vs the rigid 11-turn (unverified). A 1 m version would be about +1.5 (my rough scaling).
    - **Price:** About $20-40 DIY (estimate)
    - **Availability:** DIY
    - **Durability notes:** Narrowband, so it needs tuning. Hand-tracking a 1.8 m boom through a LEO pass is hard and it catches wind. One user found it much cleaner than a helix against terrestrial interference. A linear single port loses a constant 3 dB on CP signals.
    - **Evidence:** rtl-sdr.com RSP2 HRPT tutorial and its comments: decoded HRPT, no SNR figures.
    - **Sources:**
      - https://www.rtl-sdr.com/a-tutorial-on-receiving-hrpt-weather-satellite-images-with-an-sdrplay-rsp2/
  10.
    - **Band:** L and S
    - **Name:** Folding short-backfire (35 cm pop-up fabric main reflector + 4.4 cm fabric rim + 7 cm sub-reflector on a rod + crossed-dipole feed)
    - **Type:** diy
    - **Fold method:** The main reflector is a twist-fold spring hoop with CuNi fabric (35 cm should fold to about 14 cm). The rim is a fabric band. The sub-reflector disc sits on a fibreglass rod about 8.8 cm above. CP comes from a crossed-dipole feed through a 90° hybrid.
    - **Packed size cm:** About 14-15 cm across x 3 cm, plus a 10 cm rod. Ultra-compact.
    - **Deployed size cm:** 35 cm across x about 10 cm
    - **Weight g:** About 200-300 g (estimate)
    - **Setup time:** 2-4 min
    - **Gain:** 12-16 dBi (literature for a 2-2.5λ rim). After the hybrid that is about 11.5-14.5 dBic.
    - **Gain vs current pick db:** -2 to +1 dB vs the rigid 11-turn
    - **Price:** About $15-30 plus a DIY hybrid (estimate)
    - **Availability:** DIY
    - **Durability notes:** Needs a CP feed network that the helix gives for free. No HRPT precedent. It does no better than the helicone, so it is not preferred.
    - **Evidence:** Only the literature. Gain was not modelled here.
    - **Sources:**
      - https://en.wikipedia.org/wiki/Short_backfire_antenna
      - https://ntrs.nasa.gov/api/citations/19670009367/downloads/19670009367.pdf
  11.
    - **Band:** L
    - **Name:** Foil-lined umbrella reflector + linear PCB feed (Saveitforparts build)
    - **Type:** modify
    - **Fold method:** An ordinary umbrella lined with foil tape folds like an umbrella, with the feed on a short rod.
    - **Packed size cm:** About 25-35 cm (travel-umbrella class; estimate)
    - **Deployed size cm:** About 90-100 cm across (estimate; the article gives no size)
    - **Weight g:** About 400-700 g (estimate)
    - **Setup time:** 1-2 min
    - **Gain:** Not measured. The builder calls it 'not a great antenna, but it's something that can be used in a pinch'. A linear feed loses 3 dB on RHCP, and a helix feed in a reflector must be LHCP.
    - **Gain vs current pick db:** Unknown (unverified). It could match or beat the helix if the shape is close to a paraboloid, but there is no data.
    - **Price:** About $10-20 (estimate)
    - **Availability:** DIY
    - **Durability notes:** This brings back a dish-shaped reflector, which the user abandoned. It is not a paraboloid and is very wind-sensitive. The builder had trouble with the helical feed.
    - **Evidence:** Received GOES, NOAA and Meteor HRPT signals. The PCB linear feed 'worked much better' than the helix feed.
    - **Sources:**
      - https://www.rtl-sdr.com/saveitforparts-building-an-l-band-satellite-antenna-out-of-an-umbrella/
  12.
    - **Band:** L and S
    - **Name:** Commercial compact or deployable antennas checked: none qualifies
    - **Type:** buy
    - **Fold method:** None is a hobby-priced folding 1.7 GHz RHCP antenna
    - **Packed size cm:** Not applicable
    - **Gain:** RTL-SDR Blog L-band patch: 1525-1660 MHz, and the vendor says it is not for HRPT. Southwest Antennas 1005-007 conical helix: 1.7-2.7 GHz, 4 dBic. PRC-Com HC-1400-10: 1.1-1.7 GHz, 14.5 dBi, 4.7 kg (10.4 lb), rigid. Discovery Dish: 65 cm in 3 petals, still a dish. HCT Helios deployable helix: space-grade, 400-3000 MHz, memory-alloy deployment, no price.
    - **Gain vs current pick db:** Not applicable (the patch and the Southwest helix are 9-10 dB worse; the PRC-Com is not portable)
    - **Price:** Patch $59.95; the others are not hobby-priced or are unpriced
    - **Availability:** No commercial folding 1.7 GHz antenna for hobbyists was found
    - **Sources:**
      - https://www.rtl-sdr.com/preorder-sale-active-l-band-1525-1660-inmarsat-and-iridium-patch-back-in-stock-for-44-95/
      - https://everythingrf.com/products/all-antennas/southwest-antennas/741-685-1005-007
      - https://www.everythingrf.com/products/all-antennas/prc-com/741-2369-hc-1400-10
      - https://www.rtl-sdr.com/discovery-dish-pre-launch-a-lightweight-dish-and-feed-for-l-band-weather-satellites-and-hydrogen-line-reception/comment-page-4
      - https://satsearch.co/products/helical-communication-technologies-helios-deployable-antenna
- **Recommended:** Fold-flat PETAL helicone with swap-in helices.
  
  - **Build:** an 18 cm 1.5 mm aluminium base disc with the SAWbird+ GOES bolted underneath. Eight clip-on 0.3-0.5 mm aluminium petals form an 18 to 44 cm cone, 12 cm deep, overlapping at least 1 cm.
  - **L-band helix:** 5 turns, C=1.1λ, RHCP, 61.7 mm across, 43 mm pitch, 2 mm phosphor-bronze or Cu-clad-steel spring wire on a 2-section fibreglass rod with printed pitch stops.
  - **S-band helix:** 7 turns, C=1.1λ at 2.25 GHz, 46.7 mm across, 32.5 mm pitch, 228 mm. It nests inside the L-band helix and needs the wideband LNA plus a Sysmocom cf2235-kt30 cavity.
  - **Packed:** about 19 x 19 x 4 cm plus a rod of about 20-23 cm, roughly 0.4-0.5 kg. Setup is 2-3 min with no tools.
  - **Gain (my NEC2 model, ±1-3 dB):** L-band 15.7 dBic, which is +2.2 dB vs the rigid 11-turn (+1.7 like-for-like) and +1.0 vs the rigid helicone. S-band 14.2 dBic, +0.7 to +1.0 vs the rigid S helix. A dedicated 33 cm S cone would give 15.5 dBic.
  - **Why:** it is the only foldable option that improves gain rather than losing it, keeps native RHCP, needs no combiner and no 2-channel software, and copies a field-tested shape (the t0nito mesh-on-8-holders helicone).
  - **First test:** validate on Elektro-L5 LRIT at 1691 MHz against the rigid helix before trusting the numbers.
- **Ultra compact:** Pocket FABRIC helicone: the same 18 to 44 cm, 12 cm cone made of copper-nickel ripstop (0.07 Ω/sq or less) on 8 hinged 3 mm fibreglass ribs that fold in over the 18 cm base disc, with a 4-turn C=1.1λ spring helix (172 mm, compresses to about 1 cm).
  
  - **Packed:** a disc about 19 cm across x 3-4 cm plus a rod 18 cm or shorter. Every part is 20 cm or less, about 250-350 g, 1-2 min setup.
  - **Gain:** 15.6 dBic modelled with octagonal facets, about +2 dB vs the rigid 11-turn.
  - **If no fabric is wanted:** the 11-turn spring helix on a 30 cm twist-fold pop-up disc (about 12-13 cm across x 2 cm packed, plus a 20 cm rod) models 13.7-13.9 dBic, essentially the same as the rigid pick (-0.3 to +0.4 dB).
  - **Fallback with no folding at all:** a rigid 4-5 turn helix on an 18 cm plate (18 x 18 x 19-22 cm) models 11.6-12.0 dBic, -1.5 to -1.9 dB. Meteor is still kept; Metop is lost.
- **Losses:**
  1.
    - **Target:** Meteor-M N2-3/N2-4 HRPT, 1.70 GHz, 665 kbps (needs 0.5 dB SNR in SatDump)
    - **With foldable kit:** kept
    - **Margin change db:** +1.7 to +2.2 dB vs the rigid 11-turn helix (model). Estimated average SNR is about 8.5-9.5 dB, a margin of about +8.9 to +9.4 dB, against about +7.2 dB with the rigid pick. Spring 11-turn with pop-up ground: -0.3 to +0.4 dB. No-fold 5-turn helix on a plate: -1.9 dB, margin still about +5 dB.
    - **What we lose:** Nothing in link margin if the fold helicone is built correctly. What we do lose:
  - 2-3 min of setup.
  - Wind tolerance: the 44 cm cone catches wind like an umbrella.
  - Spare-part risk: petals, ribs and clips can get lost.
  - The beam is slightly narrower (24-28° vs 28-32°), so a ±7° hand-pointing error costs about 0.9 dB instead of 0.65 dB.
  - Certainty: the gain is a model, and no first-hand dish-free hand-tracked Meteor HRPT decode has been documented.
    - **Workaround:** Use a 20-25 cm folding mini tripod with a pan-tilt head and the BNO085 pointing aid. Hold the antenna at least 50 cm above ground. A/B test against the rigid helix on Elektro-L5 LRIT.
  2.
    - **Target:** Metop-B AHRPT, 1.70 GHz, about 3.5 Mbps / 2.333 Msym/s (needs 4 dB SNR). Metop-C AHRPT is 'No' per NOAA OSPO, Sept 2026.
    - **With foldable kit:** degraded
    - **Margin change db:** The rigid 11-turn is about -1.6 dB below threshold on a pass average, effectively lost. The fold helicone is about 0 to +0.5 dB average (+1.7 to +2.2 dB better), but minus 0.5-1 dB of pointing loss and about 0.5 dB of build tolerance. Slant range costs 6.8 dB at 20° elevation and 2.5 dB at 45°, relative to zenith.
    - **What we lose:** Low and medium passes (maximum elevation below about 45°) and the ends of every pass. At best, partial AVHRR swaths near the time of closest approach on high passes. Decode reliability will be poor. The Metop EIRP is not verified, so the estimate is ±2-3 dB. Nobody has documented a dish-free Metop decode.
    - **Workaround:** Fold-flat 2x2 spring-helix array on a 60 cm pop-up ground: 17.1-18.0 dBic after the combiner (model), about +2 to +3 dB average margin, 5-10 min setup on a tripod. Or a segmented 1.8 m loop Yagi (about 17 dBic-equivalent, unverified). Or the umbrella reflector (gain unknown). Or Metop data from online archives instead of reception.
  3.
    - **Target:** FengYun-3 AHRPT
    - **With foldable kit:** lost
    - **Margin change db:** Not applicable
    - **What we lose:** Lost with any antenna, rigid or foldable. FY-3C L-band ended in 2024, and FY-3D to FY-3H AHRPT is X-band at 7.8 GHz and 30-38 Msym/s, which needs a tracked dish of roughly 1 m.
    - **Workaround:** None within this kit
  4.
    - **Target:** Elektro-L5 LRIT, 1691 MHz, geostationary at 76°E (bonus target and gain-test source)
    - **With foldable kit:** kept
    - **Margin change db:** +1.7 to +2.2 dB vs the rigid helix (model). LRIT decodes at about +1 dB SNR.
    - **What we lose:** Nothing. It needs no tracking, so the fold helicone can sit on a mini tripod.
    - **Workaround:** Use it as the A/B reference to measure the real gain of each foldable build
  5.
    - **Target:** S-band 2.2-2.3 GHz downlinks (CubeSat/SatNOGS-class)
    - **With foldable kit:** kept
    - **Margin change db:** +0.7 to +1.0 dB (7-turn S helix in the L cone) or +2.0 to +2.3 dB (dedicated 33 cm S cone) vs the rigid C=0.9 11-turn S helix (13.2-13.5 dBic). The dual-band C=0.9 helix gives +1.9 to +2.2 on S-band but costs 1.3 dB on L-band vs the C=1.1 helix in the same fold cone. Our files hold no absolute S-band link budget.
    - **What we lose:** Simultaneous L/S reception from one feed. You must swap the helix and the LNA, because the SAWbird+ GOES passes only 1648-1728 MHz. The S chain needs its own LNA and cavity (Sysmocom cf2235-kt30, EUR 65.45). There is a 30 s swap per band change. Whether a given weak CubeSat decodes remains unknown, as it was with the rigid pick.
    - **Workaround:** Keep a dedicated 33 cm fold S cone (packs about 14 cm across x 3 cm) if S-band matters more than one-cone simplicity
  6.
    - **Target:** Kit-level: setup time, reliability, mechanics (all L/S options)
    - **With foldable kit:** degraded
    - **Margin change db:** 0 to -0.5 dB per assembly from build tolerance: modelled ±6 mm per-turn pitch error costs 0.3 dB or less, octagonal fabric facets 0.15 dB. Sparse radial wires without fabric cost 1.8-5.6 dB, so avoid them.
    - **What we lose:** - Setup goes from 0 to 1-3 min (5-10 min for the 2x2 array).
  - More parts to lose.
  - Repeat-folding wear on the fabric, ribs and spring wire. Soft copper fatigues; use phosphor bronze or Cu-clad steel.
  - Each fold or unfold can shift the geometry slightly.
  - Every gain figure is an unmeasured NEC2 model, ±1-3 dB.
    - **Workaround:** Print pitch stops into the rod, key the petals so they fit only one way, carry 2 spare ribs and clips, and keep the matching strip glued. Check S11 better than -10 dB over 1690-1710 MHz after each trip with a VNA covering 3 GHz or more.
- **Other ways out:**
  - Meteor LRPT at 137 MHz with the V-dipole already in the kit, as the fallback when HRPT fails. LRPT is 72 kbps and carries fewer MSU-MR channels than HRPT (3 vs 6, which is general knowledge and was not re-verified in this run). No 1.7 GHz antenna is needed.
  - Elektro-L5 LRIT at 1691 MHz from a fixed mini tripod. It is geostationary at 76°E and about 19° up from Kyiv, so it needs no tracking. It decodes at about +1 dB SNR, keeps an L-band target alive even on a 4-5 turn plate helix, and serves as the gain test source.
  - For Metop-B: a fold-flat 2x2 spring-helix array on a 60 cm twist-fold CuNi ground (packs to a disc about 23 cm across). It models 17.1-18.0 dBic after a 0.7 dB Wilkinson combiner. Use passive combining into a single RX, not LimeSDR RX1/RX2, until LimeSuiteNG channel alignment (issue #356) is fixed.
  - For Metop-B: a segmented 1.8 m loop Yagi in 6 sections of 30 cm (about 20 dBi linear per a reader estimate, unverified, so about 17 dBic-equivalent on RHCP). It is also cleaner against LTE than a helix, but hard to hand-track.
  - A foil-lined travel umbrella with a linear PCB feed (Saveitforparts received GOES, NOAA and Meteor HRPT with one). It folds to umbrella size, but its gain is unmeasured and it brings back a dish shape.
  - Mount any of the antennas on a 20-25 cm folding tripod with a pan-tilt head to remove 0.5-1.5 dB of hand-pointing loss with the 24-28° beams.
  - If the user also rejects fabric and petals: a rigid 4-5 turn helix on an 18 cm plate (11.6-12.0 dBic modelled, packs 18 x 18 x 19-22 cm). Meteor HRPT keeps about 5 dB of margin, Metop is lost, and S-band uses a 5-turn S helix (11.4 dBic modelled, about -2 dB).
  - Use online archives (for example the EUMETSAT Data Store, not checked in this run) for Metop and FengYun imagery that the kit can no longer receive.
- **Notes:** Working targets unchanged: packed 30-35 cm for the backpack tier and 20 cm or less for the ultra-compact tier, with a large deployed size allowed if setup takes a few minutes. The recommended fold helicone has no part over about 19-23 cm, so it also meets the ultra-compact tier with a 4-turn or spring helix.
  
  **Modelling (all gains are my models, unmeasured)**
  - NEC2 via PyNEC 2.3.4. Wire-grid discs and cones, 2 mm copper wire, gain as maximum RHCP.
  - Cross-check against earlier results: the same code reproduces the earlier helicone figure (40 cm rim, 15 cm deep: 14.74 dBic vs 14.7). It gives 13.98 dBic for the 11-turn on a 20 cm round disc, against the earlier 13.5 on a square plate, so deltas are quoted both ways (±0.5 dB).
  - Main new finding: a shallower, wider cone (18 cm base to 44 cm rim, 12 cm deep) with only 4-7 turns models 15.6-16.0 dBic, flat across 1.65-1.75 GHz, with a 24-28° beam. So the long helix is unnecessary. The cone is the part that folds, and the 17-23 cm helix fits the packing target even when rigid.
  - Tolerance results:
    - ±6 mm per-turn pitch error costs 0.3 dB or less; ±10 mm costs up to 0.6 dB.
    - ±4 mm radius error costs 0.4 dB or less.
    - ±10-15% overall stretch error costs 0.1-0.3 dB.
    - Phosphor bronze or stainless instead of copper costs 0.06 dB or less.
    - Octagonal fabric facets cost 0.15 dB.
    - A radial-wire-only ground plane is bad: 8.4-12.2 dBic.
    - A 40 cm flat disc is worse than a 20-30 cm one.
    - A 4 cm cup rim adds 0.5 dB.
  - 2x2 arrays (before the combiner): 11-turn 18.75, 7-turn 17.8, 5-turn 16.8 dBic on a 56 cm ground.
  - S-band: a scaled 33 cm helicone gives 15.5 dBic; a C=1.1λ 7-turn S helix in the L-band cone gives 14.2; a 5-turn on a 15 cm disc gives 11.4.
  - Scripts are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/nec_fold/ (fold.py, t2-t10.py).
  
  **Margin anchor (reused from dish_replacement.json, not redone)**
  - Meti's 11-turn helix (about 12.75 dBic) gave about 7 dB average SNR on Meteor-M2-3, against 0.5 dB needed.
  - Metop is estimated at about 1.6 dB average, against 4 dB needed (5.4 dB symbol-rate penalty, EIRP unverified).
  - I assumed SNR scales dB-for-dB with antenna gain.
  - Slant range at about 830 km orbit height costs 9.3 dB at 10° elevation, 6.8 dB at 20°, 4.8 dB at 30° and 2.5 dB at 45°, relative to zenith.
  
  **Evidence gaps**
  - I found no hobby or commercial folding 1.7 GHz antenna anywhere. The evidence for the concept is patents (US9142882 compressible spiral; DE202010013085U1 self-expanding helix; US8970447 nanosat deployable helix), the Georgia Tech origami helix and the HCT Helios space-grade deployable helix.
  - The closest real precedent is the t0nito/pe2bz helicone: mesh on 8 holders, stronger signals at 1545, 1700 and 2250 MHz, no SNR figures.
  - Unverified prices: CuNi fabric (about GBP 83 for 8 x 1.1 m), the pop-up reflector frame, the combiner, and all DIY materials.
  - Unverified gains: the 4G panel at 1.70 GHz (below its band edge), and the umbrella and loop-Yagi figures.
  
  **Polarisation**
  - Linear antennas (LTE panels, loop Yagi, umbrella with a PCB feed) lose a constant 3 dB on RHCP Meteor and Metop signals.
  - Fixing that takes a 90° hybrid. Connectorised hybrids cost $504 (E-meca 1.7-2.2 GHz) to $1,100 (Pasternack), so use a DIY branch-line coupler or software combining. Software combining is blocked on the LimeSDR Micro by the RX phase-alignment issue.
  
  **Search budget:** 16 web searches used.

## fold:qo100 (run `wf_4a343103-e9e`)

- **Band group:** QO-100 downlink 10.489-10.499 GHz through the Bullseye TCXO LNB (narrowband IF about 739.5-740 MHz, wideband IF about 741-749 MHz). Narrowband is vertical (13 V), wideband/DATV is horizontal (18 V) or the LNB is rotated 90°.
- **Options:**
  1.
    - **Band:** QO-100 narrowband downlink 10489.5-10490 MHz. Either polarisation by rotating the LNB; the wideband band is covered but gain is far too low for DATV.
    - **Name:** Modular flat-pack conical horn made of gores: inner section about 21 dBi, plus an outer ring for about 23 dBi
    - **Type:** diy
    - **Fold method:** Two cone sections laid out as flat annular-sector gores. W1GHZ: a conical-horn template is 'just two concentric sections of a circle'. Cut from 0.3 mm aluminium flashing or 0.2 mm brass shim, with the same 13.8° half-angle as the current 23 dBi pick. Inner section (40 to 127 mm diameter): 3 gores, slant radii 84-267 mm, 28.6° each, plus a 10 mm overlap flap. Outer ring (127 to 180 mm): 3 gores, radii about 255-378 mm (12 mm overlap onto the inner section), 28.6° each. Overlap seams by at least 10 mm and press them flat with mini binder clips every 4-5 cm (gap under about 0.2 mm), or tape them with aluminium tape. A printed collar clamp (ID 40.2 mm, thumb screw, no tools) fits the LNB's 40 mm collar. Printed 127 mm joint ring and 180 mm mouth ring keep it round.
    - **Packed size cm:** Inner gores 14.2 x 18.5; outer gores 19.7 x 12.0. Whole kit is a flat stack of about 20 x 19 x 1.5 (rings lie flat; the 18 cm mouth ring is the widest part). Meets the <=20 cm ultra-compact tier.
    - **Deployed size cm:** 21 dBi: mouth Ø12.7 x 17.7 long. 23 dBi: Ø18 x 28.5 long. Both in front of the LNB.
    - **Weight g:** About 150-200 (0.3 mm Al sheet about 82 g plus overlaps, clips and 3 printed rings; estimate; brass is about 2.5x heavier)
    - **Setup time:** About 1.5-2 min for the 21 dBi inner section, 2-4 min for 23 dBi (estimate, untested)
    - **Gain:** Inner section alone about 21.0 dBi; full horn about 23.0 dBi. MODEL: optimum-cone / King phase-error formula at 10.4895 GHz. Allow -0.2 to -0.5 dB for clipped seams (unverified).
    - **Gain vs current pick db:** Inner section: +1.0 vs the 20 dBi rigid horn (it is longer than the 12 cm optimum horn). Full horn: 0 to -0.5 vs the 23 dBi rigid horn.
    - **Price:** About $10-20 in materials (sheet, clips, filament; estimate). The LNB (Bullseye $29.95) is already in the plan.
    - **Availability:** DIY. Lay out with W1GHZ HDL_ANT or a compass. Sheet from hardware or craft stores; rings print on any 200 mm bed.
    - **Durability notes:** Thin aluminium creases if folded, so store the gores flat between two pieces of card; brass shim is springier and survives more cycles. Clips get lost: carry spares. Horn walls are tolerant (W1GHZ: dishes 'have more critical dimensions than horns and lenses'), so a 1-2 mm kink is harmless but an open seam is not. Check beacon C/N after every assembly.
    - **Evidence:** Same cone geometry as the verified rigid pick. W1GHZ says home-built horns 'almost always' match prediction 'with no tuning adjustments required'. A folded-film X-band horn (PolyU, ICMMT 2024, 8.2-12.4 GHz, 10/15/20 dBi; the abstract does not say whether these are measured) shows foldable horns work in this band. No QO-100 horn report exists anywhere. Validate with the A/B test: horn minus bare LNB should be +8 to +12 dB for 20 dBi and +11 to +15 dB for 23 dBi.
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap2.pdf
      - http://www.w1ghz.org/antbook/chap4.pdf
      - https://research.polyu.edu.hk/en/publications/origami-horn-antenna-with-adjustable-gain-based-on-graphene-assem/
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/qo_calc/horns2.py
  2.
    - **Band:** QO-100 narrowband downlink 10489.5-10490 MHz. The square section passes both polarisations (rotate the LNB).
    - **Name:** Flat-pack 4-plate square pyramidal horn, hinged so it flattens like a carton
    - **Type:** diy
    - **Fold method:** Four identical trapezoids of 0.5 mm aluminium (or brass). Three corners are hinged with conductive aluminium or copper foil tape on the outside, so the horn folds flat like a carton. The fourth corner is closed by an aluminium angle strip and 3 binder clips. A printed adapter with a square socket fits the 40 mm LNB collar (thumb screw). Corner joints must conduct, because wall current crosses the corners.
    - **Packed size cm:** 20 cm plates: 12.4 x 19.7 x about 0.6 (meets the <=20 cm tier). 30 cm plates: 15.2 x 29.7 x 0.6 (meets the 30-35 cm tier).
    - **Deployed size cm:** 12.4 x 12.4 mouth x about 19 long, or 15.2 x 15.2 x about 29
    - **Weight g:** About 120 with 20 cm plates (about 77 g of aluminium plus adapter, tape and clips); about 180-200 with 30 cm plates (estimate)
    - **Setup time:** Under 1 min: unfold, clip one corner, push onto the adapter (estimate)
    - **Gain:** About 20.5-21.5 dBi (124 mm mouth, 19.7 cm plates) or about 22.5-23 dBi (152 mm mouth, 29.7 cm plates). MODEL: Balanis pyramidal-horn directivity, ideal walls. Allow -0.3 to -1 dB for corner joints and the round-to-square throat transition (unverified).
    - **Gain vs current pick db:** +0.5 to +1.5 vs the 20 dBi rigid horn (20 cm plates); -0.5 to 0 vs the 23 dBi rigid horn (30 cm plates)
    - **Price:** About $10-15 in materials (estimate)
    - **Availability:** DIY. HDL_ANT prints pyramidal templates.
    - **Durability notes:** The most robust and fastest foldable option. Plates do not crease. Tape hinges wear out after many cycles but are cheap to replace. Keep plates from bowing more than 1-2 mm. The round-to-square throat is an untested adaptation, so A/B-test it against the bare LNB.
    - **Evidence:** W1GHZ: HDL_ANT pyramidal templates are meant to 'fold on the dotted lines' and be soldered together; pyramidal horns are the standard home-built 10 GHz antenna. The hinged flat-fold and the 40 mm round-to-square adapter are my own adaptation. No QO-100 report.
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap2.pdf
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/qo_calc/horns2.py
  3.
    - **Band:** QO-100 narrowband downlink 10489.5-10490 MHz
    - **Name:** One-piece roll-up 20 dBi cone: the current handheld horn made from one flat sheet
    - **Type:** diy
    - **Fold method:** One annular sector (slant radii 59.5-188 mm, 122°) of 0.3 mm aluminium or brass. One overlap seam held by 3-4 clips, plus the printed 40 mm collar clamp and a 127 mm mouth ring. It can be cut into 2 gores to reach the 20 cm tier.
    - **Packed size cm:** Flat sheet 33.8 x 15.9 x 0.3 (30-35 cm tier), or 2 gores of 20.0 x 13.7 (<=20 cm tier)
    - **Deployed size cm:** Ø12.7 x 12.1 long, in front of the LNB
    - **Weight g:** About 50-80 (estimate)
    - **Setup time:** 30-60 s (estimate)
    - **Gain:** About 20.1 dBi (MODEL; same design as the current pick), with -0.1 to -0.3 dB seam allowance
    - **Gain vs current pick db:** 0 to -0.3 vs the 20 dBi rigid horn; about -3 vs the 23 dBi rigid horn
    - **Price:** About $5-10 in materials (estimate)
    - **Availability:** DIY
    - **Durability notes:** Only one seam, so it is the simplest build. The single sheet is wider than 30 cm unless it is cut into 2 gores.
    - **Evidence:** Same W1GHZ optimum-cone design as the current pick (127 mm mouth, 188 mm slant). The flat-sheet form is the W1GHZ template itself.
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap2.pdf
  4.
    - **Band:** QO-100 narrowband downlink 10489.5-10490 MHz
    - **Name:** Small rigid 18 dBi 'cup' horn: the small-horn option, needs no folding
    - **Type:** diy
    - **Fold method:** None. A rigid cone with a 100 mm mouth, 63 mm long from the 40 mm collar (84 mm from a 20 mm throat). It can stay mounted on the LNB, and it doubles as the feed for the lens (option 7).
    - **Packed size cm:** Ø10 x 6.3; adds about 6 cm to the LNB
    - **Deployed size cm:** Ø10 x 6.3
    - **Weight g:** About 25-50 (estimate)
    - **Setup time:** 0-10 s
    - **Gain:** About 18.0 dBi (MODEL). W1GHZ's comparable 10 GHz Gunnplexer horn measured 17.5 dBi.
    - **Gain vs current pick db:** -2.1 vs the 20 dBi rigid horn; -5.1 vs the 23 dBi rigid horn
    - **Price:** About $3-5 in materials (estimate)
    - **Availability:** DIY (rolled sheet or 3D-printed and copper-taped)
    - **Durability notes:** Robust and nothing to assemble. A 10 cm rigid cup clearly passes the pack rule.
    - **Evidence:** W1GHZ Table 3-1: 17.5 dBi horn measured at 10.368 GHz.
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap3.pdf
  5.
    - **Band:** QO-100 narrowband downlink 10489.5-10490 MHz
    - **Name:** Bare Bullseye TCXO LNB with no horn
    - **Type:** buy
    - **Fold method:** None; the LNB only.
    - **Packed size cm:** LNB only (the Bullseye's dimensions are not published; measure yours)
    - **Deployed size cm:** LNB only
    - **Weight g:** LNB only (not published)
    - **Setup time:** About 1 min to aim (about 40° beam)
    - **Gain:** About 9-12 dBi (estimate from the input files; built-in dish feed)
    - **Gain vs current pick db:** -8 to -11 vs the 20 dBi rigid horn; -11 to -14 vs the 23 dBi rigid horn
    - **Price:** $29.95
    - **Availability:** RTL-SDR store showed 70 in stock on 18 Oct 2026.
    - **Durability notes:** Nothing to break. Also useful as a wide-beam finder before fitting a horn.
    - **Evidence:** Field reports exist: OK1DX copied the CW beacon; RigExpert TBR-AN-1 decoded FT8 at -11 to -15 dB with an LNB alone (GPSDO-locked LNB, aimed within ±20°); a Passion Radio buyer received QO-100 'without using the dish'.
    - **Sources:**
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
      - https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
      - https://www.passion-radio.com/satellite-qo-100/converter-432-936.html
  6.
    - **Band:** QO-100 narrowband downlink 10489.5-10490 MHz
    - **Name:** Nesting rigid 23 dBi cone in 3 sections that stack inside each other
    - **Type:** diy
    - **Fold method:** Three rigid frusta, each about 95 mm long axially (40 to 87, 87 to 133 and 133 to 180 mm), all at the 13.8° half-angle, so the smaller ones nest inside the largest. Friction or twist-lock joints with at least 10 mm overlap. Made from 3D-printed PETG/ASA lined with copper foil tape, or rolled aluminium.
    - **Packed size cm:** Ø18.5 x about 10.5-11 as a nested stack (about 2.8 L bounding volume)
    - **Deployed size cm:** Ø18 x 28.5 long
    - **Weight g:** About 250-450 printed (estimate)
    - **Setup time:** 30-60 s
    - **Gain:** About 23 dBi (MODEL), with -0.3 to -0.8 dB allowance for two joints and the tape lining (unverified)
    - **Gain vs current pick db:** 0 to -0.8 vs the 23 dBi rigid horn; +2.2 to +3 vs the 20 dBi horn
    - **Price:** About $10-20 (filament and copper tape; estimate)
    - **Availability:** DIY
    - **Durability notes:** Rigid and robust, but bulky (small-saucepan size, not 'a few cm thick'). Copper tape can lift at the joints.
    - **Evidence:** ITU: a PLA X-band horn coated with copper tape showed good matching and gain over 8-12 GHz. UCT printed X-band horns metallised with paint or plating. Abraxas3d keeps a GitHub repo of 3D-printed ham microwave horns, including 10 GHz. No QO-100 use found.
    - **Sources:**
      - https://research.itu.edu.tr/en/publications/a-rapid-prototyping-approach-for-3d-printed-horn-antennas-in-x-ba/
      - https://open.uct.ac.za/items/9f9c05e8-2c66-452a-b1bd-35fababc44c1/full
      - https://github.com/Abraxas3d/3D-printed-horn-antennas
  7.
    - **Band:** QO-100 narrowband downlink, vertical. The lens is polarisation-specific: rotate it with the LNB.
    - **Name:** Flat-pack W1GHZ metal-plate lens, 300 mm, fed by the 18 dBi cup horn on a telescopic boom
    - **Type:** diy
    - **Fold method:** 15-16 parallel aluminium plates (foil on 2 mm Correx, or 0.3 mm aluminium) with the curved edges computed by HDL_ANT, slotted into two printed combs at 19.05 mm pitch. The lens is held about 53 cm in front of the horn on a collapsible rod or tripod arm. Plates run parallel to the E-field. W1GHZ's original is a glued foam block (about 30 x 30 x 7 cm, rigid); the slotted flat-pack version is my adaptation.
    - **Packed size cm:** Plate stack about 30 x 7 x 2, plus two 30 cm combs and a rod collapsed to about 30 cm (30-35 cm tier; not ultra-compact)
    - **Deployed size cm:** 30 x 30 lens about 53 cm from the horn; about 65 cm overall
    - **Weight g:** About 250-400 plus the rod (estimate)
    - **Setup time:** 5-10 min, including focusing on the beacon (estimate)
    - **Gain:** 27.4 dBi measured by W1GHZ at 10.368 GHz (foam-block lens, 17.5 dBi horn, about 21 in focus, about 50% efficiency). The 10.489 GHz redesign and the slotted version are unverified.
    - **Gain vs current pick db:** +7.3 vs the 20 dBi rigid horn; +4.4 vs the 23 dBi rigid horn
    - **Price:** About $10-25 in materials (estimate from the prior study)
    - **Availability:** DIY
    - **Durability notes:** Plate spacing is the critical dimension (W1GHZ). An error of ±0.5 mm moves the index from 0.661 to 0.635-0.684, about ±7% in focal length, so refocus on the beacon. The beam is about 7°, so a tripod is mandatory; it is also wind-sensitive.
    - **Evidence:** W1GHZ Table 3-1 (horn 17.5, +150 mm lens 20.9, +300 mm lens 27.4 dBi, all measured). It was used portable in contests with a 'light weight' lens. No QO-100 use found.
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap3.pdf
  8.
    - **Band:** QO-100 narrowband downlink (zone rings are polarisation-independent)
    - **Name:** Folding reflective phase-reversal Fresnel zone plate, 40 cm, fed by the bare LNB (experimental)
    - **Type:** diy
    - **Fold method:** Four 20 x 20 cm tiles of about 7 mm foam board (λ/4 = 7.1 mm), hinged with tape. Aluminium foil on the back; aluminium-tape rings for alternate Fresnel zones (F about 24 cm) on the front. The bare LNB sits on a 25-30 cm arm at the focus; F/D about 0.6 suits a TV-LNB feed.
    - **Packed size cm:** 20 x 20 x about 3, plus the arm
    - **Deployed size cm:** 40 x 40 plate with the LNB 24 cm in front
    - **Weight g:** About 200-350 plus the arm (estimate)
    - **Setup time:** 3-5 min (estimate)
    - **Gain:** About 25-27 dBi. MODEL: 40 cm aperture 32.9 dBi x 2-level phase efficiency 0.405 x 0.5-0.6 illumination. No 10 GHz or QO-100 build was found.
    - **Gain vs current pick db:** +5 to +7 vs the 20 dBi rigid horn; +2 to +4 vs the 23 dBi rigid horn
    - **Price:** About $10-20 (estimate)
    - **Availability:** DIY
    - **Durability notes:** Tiles must stay flat to about ±1.5 mm across the hinges, and the spacer must be 7 ±1 mm. Foam dents easily. The beam is about 5°, so a tripod is needed. In practice this is a folding flat dish, with feed blockage. A 60 cm, 9-tile version (packs to 20 x 20 x about 6.5) models about 29-30 dBi, close to the dropped 35 cm dish.
    - **Evidence:** Theory only. The SETI League zone-plate article is a 1.42 GHz simulation, not a measurement. The prior study estimated that a transmissive zone plate needs 40-50 cm to beat a 23 dBi horn. A transmissive amplitude plate of 30 cm models only about 17 dBi, worse than the horn, which is why only the reflective phase-reversal type is listed.
    - **Sources:**
      - https://setileague.org/articles/fresnel.htm
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/qo_calc/horns2.py
- **Recommended:** The modular flat-pack conical horn (option 1) on the Bullseye LNB. Its 3 inner gores make a horn of about 21 dBi for handheld use; adding the 3 outer-ring gores gives about 23 dBi on a tripod. All six gores are at most 20 x 19 cm, the kit weighs about 150-200 g and assembles in 2-4 minutes without tools (estimates). It keeps the RF design of the current rigid pick: the same 13.8° cone and the same 40 mm collar clamp. It therefore keeps everything the rigid 20/23 dBi horns keep, minus a modelled 0.2-0.5 dB for the clipped seams. Two alternatives: if setup under a minute matters more than design certainty, use the 4-plate square horn (option 2, about 20.5-21.5 dBi from 20 cm plates). If SSB copy matters and you accept a tripod, 5-10 minutes of setup and 30 cm plates, add the flat-pack 300 mm metal-plate lens (option 7, +4.4 dB over 23 dBi, measured by W1GHZ at 10.368 GHz).
- **Ultra compact:** The inner section of option 1 on its own: 3 gores of 14.2 x 18.5 cm, the collar clamp and a 127 mm ring, about 60-90 g. It gives about 21 dBi (model), about 1 dB more than the current 20 dBi handheld horn. If you want nothing to assemble, use the rigid 18 dBi cup (Ø10 x 6.3 cm, stays on the LNB), which is 2.1 dB below the 20 dBi horn. The absolute minimum is the bare LNB (8-11 dB below the 20 dBi horn). It keeps the CW beacon and strong FT8 signals, but under the conservative model it loses the PSK beacon (Eb/N0 about -3 dB) and all SSB.
- **Losses:**
  1.
    - **Target:** CW beacon 10489.500 MHz (pointing, beacon-lock drift correction)
    - **With foldable kit:** kept
    - **Margin change db:** 0 to -0.5 vs the rigid 20/23 dBi horns (seam allowance, model). Ultra-compact: inner section +1 vs 20 dBi; 18 dBi cup -2.1; bare LNB -10.
    - **What we lose:** Nothing practical. Conservative model (EA4GPZ anchor): about 17 dB in 50 Hz at 21 dBi and about 19 dB at 23 dBi; the optimistic model is about 15 dB higher. With the bare LNB it is still about 6 dB in 50 Hz (OK1DX copied it).
    - **Workaround:** None needed.
  2.
    - **Target:** PSK 400 bit/s beacon 10489.750 MHz
    - **With foldable kit:** kept
    - **Margin change db:** 0 to -0.5 vs rigid. 18 dBi cup -2.1; bare LNB -10.
    - **What we lose:** Nothing with the foldable horn: Eb/N0 about 8 dB (21 dBi) or 10 dB (23 dBi) in the conservative model. The 18 dBi cup gives about 5 dB (marginal). The bare LNB gives about -3 dB, so the beacon is lost in the conservative model but about +12 dB in the optimistic one.
    - **Workaround:** Use at least the 18 dBi cup if you rely on PSK decoding.
  3.
    - **Target:** FT8 and CW user stations
    - **With foldable kit:** kept
    - **Margin change db:** 0 to -0.5 vs rigid
    - **What we lose:** Nothing new. The weakest FT8 signals stay marginal, as with the rigid horn. FT8 was decoded at -11 to -15 dB even with a bare LNB (RigExpert, GPSDO-locked LNB).
    - **Workaround:** Beacon-lock software is required for the Bullseye's ±10-30 kHz drift.
  4.
    - **Target:** SSB stations at beacon level
    - **With foldable kit:** degraded
    - **Margin change db:** 0 to -0.5 vs rigid; lens +4.4 vs 23 dBi
    - **What we lose:** The same as with the rigid pick. Conservative model: about 0 dB (21 dBi) to +2 dB (23 dBi) SNR in 2.5 kHz, which is hard copy. Optimistic model: +15 to +17 dB.
    - **Workaround:** Flat-pack 300 mm lens (about +6 dB in 2.5 kHz in the conservative model) or the zone plate (+2 to +4 dB, model only), both on a tripod.
  5.
    - **Target:** Typical SSB stations 5-15 dB below the beacon
    - **With foldable kit:** lost
    - **Margin change db:** 0 to -0.5 vs rigid; still 3-13 dB short at 23 dBi in the conservative model
    - **What we lose:** In the conservative model they were already lost with the rigid horn (-3 to -13 dB in 2.5 kHz at 23 dBi). In the optimistic model they are degraded but mostly readable (+2 to +12 dB). Folding changes neither case.
    - **Workaround:** The lens brings them to about -9 to +1 dB in the conservative model. Comfortable copy needs about 27-30 dBi or more, i.e. a 60 cm folding zone plate (model) or a dish.
  6.
    - **Target:** Weak / QRP SSB stations
    - **With foldable kit:** lost
    - **Margin change db:** Needs 33 dBi or more; the foldable kit is about 10 dB short
    - **What we lose:** Same as the rigid pick: not receivable.
    - **Workaround:** None without dish-class aperture.
  7.
    - **Target:** Wideband DATV beacon 10491.5 MHz (1.5 MS/s DVB-S2)
    - **With foldable kit:** lost
    - **Margin change db:** Needs about 31-32 dBi (BATC MER data). 23 dBi foldable horn: 8-9 dB short. Lens: about 4 dB short. 60 cm zone plate: about 1-3 dB short (model).
    - **What we lose:** Already lost with the rigid pick. The horizontal (18 V) polarisation is irrelevant without the gain.
    - **Workaround:** Only an aperture of about 45 cm or more (dish-sized), or a WebSDR when online.
  8.
    - **Target:** DATV user stations
    - **With foldable kit:** lost
    - **Margin change db:** BATC recommends a dish of 90 cm or more
    - **What we lose:** Same as the rigid pick.
    - **Workaround:** None that fits a backpack.
  9.
    - **Target:** Setup time and handling
    - **With foldable kit:** degraded
    - **Margin change db:** n/a
    - **What we lose:** Assembly adds about 1.5-4 min (gores) or under 1 min (4-plate horn) compared with a push-on rigid horn. Pointing is unchanged: about 15° beam at 21 dBi (handheld OK), about 10° at 23 dBi (tripod).
    - **Workaround:** Leave the 18 dBi cup on the LNB for quick looks; assemble the gores only for longer sessions.
  10.
    - **Target:** Decode repeatability
    - **With foldable kit:** degraded
    - **Margin change db:** -0.2 to -0.5 dB typical (model); several dB if a seam is left open
    - **What we lose:** Each assembly can leave a gap or an out-of-round mouth.
    - **Workaround:** After assembly, log beacon C/N for 1 minute and compare with the first A/B measurement. Re-clip if it is more than 1 dB down.
  11.
    - **Target:** Ultra-compact tier only (inner section; 23 dBi ring left at home)
    - **With foldable kit:** degraded
    - **Margin change db:** -2.0 vs the 23 dBi rigid horn; +1.0 vs the 20 dBi horn
    - **What we lose:** The 23 dBi tripod mode: in the conservative model, SSB at beacon level drops from about +2 to about 0 dB in 2.5 kHz.
    - **Workaround:** The outer ring adds only about 40-50 g and 20 x 12 cm of flat sheet, so carry it.
- **Other ways out:**
  - Drop QO-100 entirely. We lose all 10 GHz reception: CW and PSK beacons, FT8/CW, beacon-level SSB, and the only geostationary target. We save the Bullseye ($29.95), the 13/18 V injector and RG6/F-SMA (about $20, estimate), the horn materials (about $10-20), about 0.3-0.5 kg and one SDR input. Nothing else in the kit depends on QO-100.
  - Bare LNB only. Zero extra pack size. Keeps the CW beacon and strong FT8 (field-proven). In the conservative model it loses the PSK beacon and all SSB.
  - Keep a rigid 23 dBi horn (or a dish) at a home or vehicle station and carry only the flat-pack kit in the backpack.
  - When internet is available, use a WebSDR (e.g. the Goonhilly QO-100 WebSDR) for SSB and DATV. It is not standalone, so it does not meet the handheld goal.
  - DATV needs an aperture of at least about 45 cm (31-32 dBi) for the beacon and a dish of 90 cm or more for user signals. The closest packable approach, a folding 60 cm zone plate (model about 29-30 dBi), is still short. DATV is therefore out for any backpack kit.
  - The QRO.cz 0.2 ppm TCXO LNB (about €120 delivered) helps only if SSB tuning drift becomes the limit. It adds no gain.
- **Notes:** Pack-size verdict for rigid horns. The 18 dBi horn (Ø10 x 6.3-8.4 cm) already meets even the 20 cm tier and needs no folding. The 20 dBi horn (Ø12.7 x 12-15 cm, about 1.5 L bounding volume) fits under 20 cm in every dimension but is not 'a few cm thick'. Flat gores cost nothing (0 to -0.3 dB), so it should be built flat. The 23 dBi horn (Ø18 x 28.5-33 cm) fails the rule and must fold. The LNB itself is rigid; its size is not published.
  
  Link-model conflict found in the inputs. antennas.json uses C/N0 of about G+13 dB-Hz, anchored to EA4GPZ, who measured 'a CN0 of around 45dB-Hz' on a 95 cm off-focus dish 'comparable to a 60cm dish', in 2 kHz with noise taken 3 kHz below the beacon (https://destevez.net/2019/03/qo-100-beacons-power/). dish_replacement.json and the digest's final pick use about G+28 dB-Hz, anchored to a BATC '>30 dB' figure of unknown bandwidth, which its own verify step flagged. That is a 15 dB difference: for a 20 dBi horn, beacon-level SSB is -1 dB or +14 dB in 2.5 kHz. If the BATC figure was read in a 50-100 Hz FFT bin, the two models roughly agree (my reconciliation, not verified). I therefore use the EA4GPZ model as the planning baseline; EA4GPZ later reported the beacons about 3 dB stronger. The gain differences between options do not depend on the anchor. Settle it with the bare-LNB vs horn A/B measurement.
  
  Status of the gain figures. Every gain here is a model (scripts in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/qo_calc/horns2.py) except: W1GHZ's measured 17.5 dBi horn and 20.9/27.4 dBi lenses (at 10.368 GHz), and the bare-LNB field reports. Two more searches today found no published QO-100 reception with a horn, lens, zone plate or flat-pack antenna.
  
  Excluded options:
  - Selfsat flat panels. H10D is about 47.5 x 26 x 7.4 cm (forum data, unverified). H21D is 475 x 258 x 74 mm. H30D1 is 51.7 x 27.7 x 5.8 cm, 4.0 kg, 33.7 dBi at 12.75 GHz, specified for 10.7-12.75 GHz, with no LO stability published (https://www.b2b.satking.de/en/selfsat-h30d1-flat-antenna-single). They are rigid, longer than 35 cm and heavy, so they fail the hard requirement, and their gain and LNB drift at 10.489 GHz are unknown.
  - Kathrein BAS panels (DD1US got the CW beacon to S4-5 on a resealed panel). Discontinued and large.
  - 10 GHz patch or slot arrays. They need an SMA-input 10 GHz LNA and mixer, and no hobby product exists. An 8x8 Rogers array (about 17 x 17 cm) models about 22-24 dBi before feed loss, which is no gain over a 21 dBi horn.
  - 3D-printed dielectric lens. Loughborough measured 18 dBi directivity; the lens is rigid and heavy.
  - Transmissive amplitude zone plate. A 30 cm plate models only about 17 dBi.
  - WR90/WR75 standard-gain horns. $220 or more, rigid, and they need a waveguide or SMA LNB.
  
  Polarisation. The cone and the square horn are rotationally symmetric, so rotate the LNB to pick the polarisation (Bullseye: 13 V vertical for narrowband, 18 V horizontal). The lens must rotate with the LNB. The zone-plate rings are polarisation-independent.
  
  Seams. Keep the overlap tight (gap under about 0.2 mm) or tape it. A loose overlap of about 10 mm is not a reliable RF short at 10.5 GHz.

## fold:verify (run `wf_4a343103-e9e`)

- **Verdict:** Deployed antennas tens of centimetres across can't be avoided. A resonant 137/145.8 MHz element is about 1 m long. 15 dBic at 1.7 GHz needs a 40-45 cm aperture, and 23 dBi at 10.49 GHz needs an 18 cm horn mouth. But none of them has to be rigid. Every band has a folding version that keeps the rigid kit's modelled gain (0 to -0.5 dB), and at L-band the folding helicone models +1.7 to +2.2 dB better.
  
  Recommended kit (longest piece 35 cm, everything else 23 cm or less, about 6-6.5 L, about 1.0-1.4 kg, about $76-118 for the antennas themselves):
  - **137 MHz:** the RTL-SDR Blog telescopic dipole kit (verified 23 cm collapsed to 1 m, M5 thread).
  - **145.8 + 435 MHz:** one crossed 2 m/70 cm Yagi. The 2 m elements are steel tape that rolls onto Axotron-style spools (Axotron v3 verified: six spools, boom pieces 347 and 279 mm). The 70 cm elements CLIP IN, and the 0.70 m square boom splits into two 35 cm halves.
  - **L/S-band:** a fold-flat petal helicone (18 cm disc plus 8 aluminium petals, 44 cm cone) with a short rigid L-band helix and a swap-in S-band helix.
  - **QO-100:** a flat-pack 6-gore conical horn (21 dBi with 3 gores, 23 dBi with all 6) on the Bullseye LNB.
  
  Folding costs time and certainty, not targets:
  - Deploying everything takes about 8-13 min.
  - There are more parts to lose.
  - Every folding design is an untested DIY build with NEC or formula gains of ±1-3 dB, so the A/B tests below are mandatory.
  
  Every target that is lost or degraded was already lost or degraded with the rigid kit: FengYun AHRPT, QO-100 DATV, typical QO-100 SSB, and Metop-B (now effectively lost).
  
  Corrections to the band studies:
  - (1) The centre-pivot fold of the 70 cm elements does not fit 35 cm. Use clip-in elements.
  - (2) QO-100 SSB must be planned on the conservative link model.
  - (3) The ultra-compact (20 cm) tier can be lossless. The petal cone with a 4-turn helix and the full gore horn already fit it, and a split-element 6-el 70 cm Yagi models 11.05 dBi.
  
  Verified on primary pages:
  - Dipole kit lengths.
  - Axotron v3 boom and spools.
  - The Arrow II BP split boom's longest part is under 22 in (56 cm), and the WiMo SOTA LPDA packs to 64 cm (5/7 dBi, EUR 139). So no commercial dual-band antenna fits.
  - The t0nito helicone is 134 to 440 mm and 88 mm high, with no published SNR.
  - The SmallRig reflector opens to 56 cm, folds to 23 cm and weighs 274 g.
  - Bullseye: $29.95, 70 in stock.
  
  My average-gain test of the NEC helicone model gives 0.96 (-0.2 dB), so the 15.7 dBic figure is numerically sound. It is a 60% aperture efficiency.
- **Foldable kit:**
  1.
    - **Band:** 137 MHz (Meteor-M LRPT)
    - **Pick:** RTL-SDR Blog multipurpose dipole kit as a V-dipole: arms 53.4 cm, 120 deg, axis N-S, about 1-1.1 m above ground, plus the FM band-stop in the path. Carry a spare telescopic pair. Do not fit the verify stage's fixed 53 cm rods.
    - **Fold method:** Telescopic elements: 2x 23 cm to 1 m and 2x 5-13 cm, on M5 threads (verified). The base, flexible tripod (1/4 in), 60 cm + 3 m RG174 and the suction mount are loose parts.
    - **Packed size cm:** Longest piece 23 (verified); kit about 23 x 8 x 5 (estimate, no vendor figure)
    - **Gain:** About 1.5-3 dBi toward zenith (NEC; 3.0 dBi, SWR 1.47 in my re-run). Linear, so a constant -3 dB on the RHCP signal.
    - **Price:** $17.95 (RTL-SDR Blog store), plus FM band-stop $16.95
    - **Budget or ultra compact alternative:** Ultra: re-mark the crossed Yagi's 2 m tapes for 137.5 MHz (R 111.4, DE 2x47.8, D 94.6 cm): 7.7 dBi, F/B 20 dB (model), about +6 dB, but it must be pointed or tripod-mounted. A hands-free tape-arm V-dipole on two spools would fit 20 cm, but it is an untested concept and must be VNA-tuned (the thick-tape NEC runs are unreliable). Otherwise the dipole kit is the one item over 20 cm, at 23 cm.
    - **Sources:**
      - https://www.rtl-sdr.com/DIPOLE
      - https://www.rtl-sdr.com/simple-noaameteor-weather-satellite-antenna-137-mhz-v-dipole/
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/nec_vhf/m3.py
  2.
    - **Band:** 145.8 MHz (ISS SSTV)
    - **Pick:** Packable crossed 2 m/70 cm Yagi, 2 m half. WB2HOL 3-el (R 105 cm at 0, DE 2x45 cm at 0.20 m, D 89 cm at 0.51 m) in 25 mm steel tape on Axotron v3-style spools, horizontal, hairpin match. RTL-SDR port.
    - **Fold method:** Each half-element rolls onto its own printed spool at the boom (Axotron v3: 6 spools, one hex pin). The 20x20 mm square PVC/GRP boom (0.70 m) splits at 0.35 m with a keyed square spigot, which holds the two planes within ±5 deg. Both feeds are on the rear half.
    - **Packed size cm:** About 35 x 10 x 6 for the whole crossed Yagi (estimate)
    - **Gain:** 7.9 dBi, F/B 17.7 dB (NEC, same geometry as the rigid pick; steel tape costs about 0.1 dB). Tape-mark errors of up to 1 cm cost at most 0.4 dB.
    - **Price:** About $25-40 materials for the whole crossed Yagi (estimate; Axotron 3MF files are free)
    - **Budget or ultra compact alternative:** Ultra: the same tapes and spools on a 5-piece square boom, joints at 0.13/0.25/0.40/0.56 m, pieces 16 cm or less, at least 3.6 cm from any element. 0 dB, about 6-8 min setup (estimate). Budget: the dipole kit as a straight dipole with about 49 cm arms, 2.1 dBi (-5.8 dB), still about +21 to +28 dB CNR at 10 deg (model).
    - **Sources:**
      - https://axotron.se/blog/?p=1619
      - https://www.w9rh.org/wp-content/uploads/2024/01/2m-tape-measure-yagi-instructions.pdf
      - https://amsat-uk.org/beginners/iss-sstv/
  3.
    - **Band:** 435-438 MHz (CubeSats)
    - **Pick:** Packable crossed Yagi, 70 cm half: N2SPI/WA5VJB 6-el, #8 Al (3.26 mm), vertical, at 0.030/0.094/0.170/0.316/0.475/0.640 m, LimeSDR port. Elements CLIP IN; centre pivots do not fit 35 cm.
    - **Fold method:** The 6 one-piece elements (longest 34.0 cm) snap into colour-coded clips or grommets and are carried alongside the boom halves. The half-folded DE stays soldered to its coax and lies along the boom.
    - **Packed size cm:** Shares the 35 x 10 x 6 Yagi bundle; the longest element is 34.0
    - **Gain:** 11.0 dBi, F/B about 25 dB, flat over 435-438 MHz (NEC, reproduced 11.05/11.03/10.99). A creep of 10-20 deg off orthogonal costs 0.2-0.8 dB.
    - **Price:** Included in the crossed-Yagi $25-40
    - **Budget or ultra compact alternative:** Ultra: screw-in half-elements of 17 cm or less on a boom in pieces of 16 cm or less, with a straight split DE (0.95 x 13 in) plus hairpin. My NEC model: 11.05 dBi, F/B 26 dB, SWR 1.07-1.24 over 435-438, so 0 dB, but 12 half-elements and about 4-5 min more. Lighter: the 4-el on a 2 x 15 cm boom, 17 x 4 x 3 cm: 9.5 dBi, F/B 13 dB (confirmed in my re-run), -1.5 dB.
    - **Sources:**
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/verify_fold/yagi6_split.py
  4.
    - **Band:** 1.69-1.71 GHz (Meteor-M HRPT, Metop AHRPT, Elektro-L5 LRIT)
    - **Pick:** Fold-flat PETAL helicone with a rigid 5-turn (or 4-turn) C=1.1λ RHCP helix: 61.7 mm diameter, 43 mm pitch, 2 mm Cu on a PETG/ASA former, feed 30.9 mm off-centre, matching strip, SAWbird+ GOES on the SMA under the disc.
    - **Fold method:** An 18 cm, 1.5 mm Al base disc. 8 keyed trapezoid petals of 0.3-0.5 mm Al (6.9 cm wide at the bottom, 16.8 cm at the top, 17.7 cm slant, plus 1 cm overlap tabs) clip on with no tools to form a cone 18 to 44 cm across and 12 cm deep, and lie flat for transport. Use a rigid helix: it is only 21.5 cm (5 turns) or 17.2 cm (4 turns) long, so a spring helix is unnecessary.
    - **Packed size cm:** Disc plus petal stack 19 x 19 x 4; helix 7 x 7 x 21.5 (5 turns) or 17.2 (4 turns); the S helix nests inside
    - **Gain:** 15.7 dBic, flat over 1.65-1.75 GHz, beam 24-28 deg (NEC; my average-gain test 0.96, so the model is sound; 60% of the 17.9 dBi aperture limit). Unmeasured, ±1-3 dB. +1.7 to +2.2 dB vs the rigid 11-turn helix.
    - **Price:** About $20-35 materials (estimate), plus the SAWbird+ GOES $44.95
    - **Budget or ultra compact alternative:** Ultra: the same cone with the rigid 4-turn helix already fits 20 cm (15.7 dBic, model, 0 dB). The CuNi-fabric umbrella cone gives 15.6 dBic and is about 100 g lighter, but no Prom.ua source for the fabric was found. No-fold fallback: a rigid 4-5 turn helix on an 18 cm plate, 11.6-12.0 dBic (-1.5 to -1.9 dB).
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/nec_fold/t7.py
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/verify_fold/agt.py
  5.
    - **Band:** 2.2-2.3 GHz (S-band downlinks)
    - **Pick:** Swap-in 7-turn C=1.1λ S-band helix (46.7 mm diameter, 32.5 mm pitch, 228 mm) on its own SMA in the same petal cone, with its own LNA and Sysmocom cf2235-kt30 cavity (the SAWbird GOES passes only 1648-1728 MHz). Wind a second, LHCP copy for LHCP satellites.
    - **Fold method:** Rigid; it nests inside the 61.7 mm L-band helix
    - **Packed size cm:** No extra volume (bundle length becomes 23)
    - **Gain:** 14.2 dBic at 2.25 GHz (NEC), +0.7 to +1.0 dB vs the rigid S helix (13.2-13.5 dBic)
    - **Price:** About $3-5 per helix, plus the S chain (cavity EUR 65.45; LNA price unverified)
    - **Budget or ultra compact alternative:** Ultra: a 5-turn S helix of about 16 cm in the L cone gives 13.0 dBic (-0.2 to -0.5 dB). Or a dedicated 33 cm S petal cone (packs about 14 x 3 cm) with a 5-turn helix gives 15.5 dBic (+2.0 to +2.3 dB, about 200-250 g extra).
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://shop.sysmocom.de/S-Band-cavity-filter-2170-2300-MHz/cf2235-kt30
  6.
    - **Band:** 10.489 GHz (QO-100 via Bullseye TCXO LNB)
    - **Pick:** Flat-pack conical horn made of gores, at the same 13.8 deg half-angle as the rigid pick. The 3 inner gores (40 to 127 mm) give about 21 dBi handheld; adding 3 outer gores (to 180 mm) gives about 23 dBi on a tripod. 0.3 mm Al or 0.2 mm brass, Al-tape or binder-clip seams with gaps under 0.2 mm, a printed 40.2 mm collar clamp, and 127/180 mm rings. 13 V for vertical narrowband; 18 V or rotate the LNB for horizontal.
    - **Fold method:** Annular-sector gores (inner: slant radii 84-267 mm; outer: 255-378 mm; each 28.6 deg) lie flat and clip together without tools in 2-4 min
    - **Packed size cm:** Flat stack about 20 x 19 x 1.5, plus the LNB (size not published)
    - **Gain:** About 21 dBi (65% of the aperture limit) and 23 dBi (51%), from the W1GHZ formula model, minus 0.2-0.5 dB for seams. The throat transition onto the LNB's 40 mm neck (40 mm per a BATC forum reply, search snippet only) is unverified, so A/B test it.
    - **Price:** About $10-20 materials, plus Bullseye $29.95 and 13/18 V injector + RG6/F-SMA about $20 (estimate)
    - **Budget or ultra compact alternative:** Ultra: the full 6-gore horn already fits 20 cm (the largest gore is about 19.7 x 13 cm, the mouth ring 18 cm), so 0 dB. For quick looks: a rigid 18 dBi cup, Ø10 x 6.3 cm, that stays on the LNB (-2.1 / -5.1 dB). Or a 4-plate hinged square horn, 12.4 x 19.7 x 0.6 cm packed, 20.5-21.5 dBi, under 1 min.
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap2.pdf
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
      - https://forum.batc.org.uk/viewtopic.php?p=31230
      - https://destevez.net/2019/03/qo-100-beacons-power/
- **Loss table:**
  1.
    - **Target:** Meteor-M LRPT 137 MHz
    - **With foldable kit:** kept
    - **Margin change db:** 0 (same telescopic V-dipole). Optional +6 dB (model) with the 2 m tapes re-marked to 137.5 MHz, pointed.
    - **What we lose:** Nothing in RF terms. We lose the verify stage's fixed-rod durability fix, so telescopic wear and loosening remain. 1-2 min setup.
    - **Workaround:** Spare telescopic pair, FM band-stop, tripod at 1-1.1 m. Use the 137.5 tape Yagi on low or weak passes.
  2.
    - **Target:** ISS SSTV 145.8 MHz
    - **With foldable kit:** kept
    - **Margin change db:** 0 (7.9 dBi model). Worst-case tape-mark error -0.4 dB, and F/B may fall from 17.7 to about 12 dB.
    - **What we lose:** About 2-3 min of unrolling 6 tapes. Steel tape needs care against kinks and rust. Ultra dipole-only option: -5.8 dB and no F/B against APRS 144.800 or local QRM, but still about +21 to +28 dB CNR in 15 kHz at 10 deg (model), so images are fine on normal passes.
    - **Workaround:** Printed length marks, lacquered tape, one VNA check per re-mark
  3.
    - **Target:** CubeSats 435-438 MHz
    - **With foldable kit:** kept
    - **Margin change db:** 0 (11.0 dBi model). 1 W 9k6 FSK margin about +5.7 dB at 10 deg and +11 dB at 30 deg (simple model, ±5 dB).
    - **What we lose:** Six loose clip-in elements to lose (centre pivots were refuted). A plane creep of 10-20 deg costs 0.2-0.8 dB. Ultra 4-el: -1.5 dB (low-elevation 0.5 W satellites suffer, F/B 25 to 13 dB). Ultra 6-el split: 0 dB but 12 half-elements.
    - **Workaround:** Keyed square boom joint, colour-coded clips, two spare elements, filtered 70 cm LNA at the feed, both Lime RX for polarisation diversity
  4.
    - **Target:** Meteor-M N2-3/N2-4 HRPT 1.70 GHz
    - **With foldable kit:** kept
    - **Margin change db:** +1.7 to +2.2 dB vs the rigid 11-turn (NEC, AGT-checked). Average margin about +8.9 to +9.4 dB vs about +7.2 dB rigid (scaled from Meti's about 7 dB SNR; needs 0.5 dB).
    - **What we lose:** 2-3 min setup. The 44 cm cone catches wind like an umbrella. The beam is narrower (24-28 deg), so a ±7 deg hand error costs about 0.9 dB instead of 0.65. Clips or petals can be lost. The gain is unmeasured, and no dish-free hand-tracked Meteor HRPT decode is documented.
    - **Workaround:** Mini tripod with a pan-tilt head and the BNO085 aid, at least 50 cm above ground, A/B test on Elektro-L5 LRIT first
  5.
    - **Target:** Metop-B AHRPT 1.70 GHz (2.333 Msym/s, needs about 4 dB)
    - **With foldable kit:** lost
    - **Margin change db:** Rigid helix about -1.6 dB average. Fold helicone about 0 to +0.5 dB before pointing (-0.5 to -1) and build (-0.5) losses, so about -1.5 to 0 dB. Plus an intermittent modulator loss of about 7 dB (SatDump/metislair, in dish_replacement.json).
    - **What we lose:** Metop-B as a dependable target, as it already was with the rigid kit. At best, chance partial AVHRR swaths near closest approach on passes above about 45 deg while the modulator is healthy. Metop EIRP is unverified (±2-3 dB).
    - **Workaround:** Fold-flat 2x2 helix array on a 56 cm twist-fold ground (17.1-18.0 dBic after the combiner, model; +2-3 dB average, experimental, 5-10 min, still fails during modulator faults). AWS at 1707 MHz as an alternative target (EIRP unknown). EUMETSAT archives.
  6.
    - **Target:** FengYun-3 AHRPT
    - **With foldable kit:** lost
    - **Margin change db:** n/a (unchanged by folding)
    - **What we lose:** Lost with any portable antenna. FY-3C L-band ended in Nov 2024. FY-3D to FY-3H AHRPT is X-band at about 7.8 GHz, which needs a tracked dish of about 1 m.
    - **Workaround:** None in this kit. Use online archives.
  7.
    - **Target:** S-band 2.2-2.3 GHz downlinks
    - **With foldable kit:** kept
    - **Margin change db:** +0.7 to +1.0 dB (7-turn S helix in the L cone), or +2.0 to +2.3 dB (dedicated 33 cm S cone), vs the rigid S helix (model). No absolute S-band link budget exists in the inputs.
    - **What we lose:** No simultaneous L/S: a 30 s helix and LNA swap. The S chain needs its own LNA and cavity. An RHCP helix loses about 20 dB on LHCP satellites and 3 dB on linear ones. Whether a given weak CubeSat decodes is still unknown, as with the rigid pick.
    - **Workaround:** Carry an LHCP copy of the S helix (30-50 g). Use the cf2235-kt30 cavity against Wi-Fi and LTE. Use the 33 cm S cone if S-band matters most.
  8.
    - **Target:** QO-100 CW + PSK beacons (and FT8)
    - **With foldable kit:** kept
    - **Margin change db:** 0 to -0.5 dB vs the rigid 20/23 dBi horns (seams). With C/N0 about G+13 to G+16 dB-Hz: at 21 dBi, CW beacon 17-20 dB in 50 Hz and PSK Eb/N0 8-11 dB. At 23 dBi: 19-22 dB and 10-13 dB.
    - **What we lose:** Nothing practical. 1.5-4 min assembly. The 18 dBi cup gives PSK 5-8 dB (marginal). The bare LNB gives PSK -3 to 0 dB (lost) but keeps the CW beacon (6-9 dB, consistent with OK1DX).
    - **Workaround:** Beacon-lock software for the ±10-30 kHz Bullseye drift. Re-check beacon C/N within 1 dB after each assembly.
  9.
    - **Target:** QO-100 SSB
    - **With foldable kit:** degraded
    - **Margin change db:** 0 to -0.5 dB vs rigid. Beacon-level SSB in 2.5 kHz: 0 to +3 dB (21 dBi), +2 to +5 dB (23 dBi), +6 to +9 dB (300 mm lens). Typical stations 5-15 dB below the beacon: -3 to -13 dB at 23 dBi.
    - **What we lose:** Same as the rigid pick. Only the strongest, beacon-level stations are copyable with effort. Typical and QRP SSB stations are lost. The optimistic 14-17 dB beacon C/N in the digest was refuted.
    - **Workaround:** Flat-pack 300 mm metal-plate lens on a tripod (+4.4 dB, 5-10 min, 30 cm tier). A 60 cm folding zone plate (model only). Home dish or WebSDR.
  10.
    - **Target:** QO-100 DATV (beacon 1.5 MS/s and user stations)
    - **With foldable kit:** lost
    - **Margin change db:** The beacon needs about 31-32 dBi (BATC MER data). The 23 dBi horn is 8-9 dB short, the lens about 4 dB short, and the 60 cm zone plate 1-3 dB short (model). Users need a dish of 90 cm or more.
    - **What we lose:** All DATV, as with the rigid pick. The horizontal (18 V) polarisation is irrelevant without the gain.
    - **Workaround:** Only a dish of about 45 cm or more, at home, or a WebSDR when online
  11.
    - **Target:** Elektro-L5 LRIT 1691 MHz (bonus and gain-test source)
    - **With foldable kit:** kept
    - **Margin change db:** +1.7 to +2.2 dB vs the rigid helix (model). LRIT decodes at about +1 dB SNR.
    - **What we lose:** Nothing. It is geostationary (76E, about 19 deg elevation from Kyiv), so no tracking is needed.
    - **Workaround:** Use it as the A/B reference for every L-band build
  12.
    - **Target:** Kit-level: setup, reliability, ultra-compact tier
    - **With foldable kit:** degraded
    - **Margin change db:** 0 to -0.5 dB per assembly. An open horn seam or a missing petal costs several dB. Lighter ultra options: -1.5 dB (435, 4-el), -5.8 dB (145.8, dipole only), -0.2 to -0.5 dB (S, 5-turn).
    - **What we lose:** - Setup goes from 0 to about 1-2 min (dipole), 3-4 (Yagi), 2-3 (helicone) and 1.5-4 (horn), about 8-13 min for everything; the lossless ultra set takes about 15-20 min.
  - More parts to lose.
  - Wear on the tapes, clips and petals.
  - Every gain is an unmeasured model.
  - The dipole kit is the only item over 20 cm, at 23 cm.
    - **Workaround:** Deploy only the antenna for the next pass. Key and colour-code the parts, and carry spares (telescopic pair, 2 x 70 cm elements, petal and clips, Al tape). Check S11 or beacon C/N after each trip.
- **Ultra compact tier:** Ultra-compact tier: every piece 20 cm or less, with one optional exception (the 23 cm dipole kit). It can be lossless if you accept a longer setup.
  
  - **137 MHz:** re-mark the crossed Yagi's 2 m tapes for 137.5 MHz: 7.7 dBi (model), pointed or on a tripod. For a hands-free omni, carry the dipole kit (23 cm, verified) or try a tape-arm V-dipole on two spools (untested concept; VNA-tune it).
  - **145.8 + 435 MHz:**
    - Main option: the same crossed Yagi on a 5-piece 20x20 mm square boom. Joints at 0.13, 0.25, 0.40 and 0.56 m give pieces of 16 cm or less, each joint at least 3.6 cm from any element. The 2 m tapes stay on spools. The 70 cm elements become screw-in half-elements of 17 cm or less, with a straight split DE (0.95 x 13 in) plus a hairpin.
    - Gain: 7.9 / 11.05 dBi, F/B 26 dB, SWR 1.07-1.24 across 435-438 (my NEC model), so 0 dB.
    - Size and setup: about 17 x 10 x 7 cm, about 6-8 min to set up, and 12 half-elements to lose (estimates).
    - Lighter option: the 4-el 70 cm (17 x 4 x 3 cm, 9.5 dBi, -1.5 dB, confirmed by my re-run) plus the dipole kit as a straight dipole for ISS (-5.8 dB; still about +21 to +28 dB CNR at 10 deg).
  - **L-band:** the recommended petal helicone already fits: a 19 x 19 x 4 cm stack plus a rigid 4-turn helix 17.2 cm long, 15.7 dBic (model), so 0 dB. The CuNi-fabric umbrella cone (15.6 dBic, about 250-350 g) is only lighter, and I found no Prom.ua source for the fabric.
  - **S-band:** a 5-turn S helix (about 16 cm) in the L cone gives 13.0 dBic (-0.2 to -0.5 dB vs the rigid S helix). A 33 cm S petal cone (packs about 14 cm) with a 5-turn helix gives 15.5 dBic.
  - **QO-100:** the full 6-gore 23 dBi horn already fits (largest gore about 19.7 x 13 cm, mouth ring 18 cm), so 0 dB. Use the 18 dBi rigid cup (Ø10 x 6.3 cm) for quick looks.
  
  Totals (estimates): about 4.5-5.5 L, about 1.0-1.4 kg, same cost as the recommended tier. Losses are 0 dB, or -1.5 dB at 435 and -5.8 dB at 145.8 if you choose the lighter VHF/UHF set.
- **Other ways out:**
  - Two-tier station: keep rigid or larger antennas at home or in the car (rigid 23 dBi horn, 300 mm lens, 2x2 helix array, rigid Yagis), and only the foldable kit travels. The travel targets lose nothing extra. Metop, typical SSB and DATV stay home-only (or unavailable).
  - Smaller target set: drop QO-100 to save the Bullseye, injector and horn (about 0.3-0.5 kg, about 1 L, about $60), but lose all 10 GHz reception including the only geostationary amateur target. Drop S-band to save the S LNA and cavity (EUR 65.45 plus the LNA).
  - No-assembly rigid mini set (every part 25 cm or less, no folding):
  - dipole kit
  - 70 cm wire Moxon, 25 x 10 cm, 5.4-6.1 dBi (-5 dB; vendor page 404, so the figures come from a snippet)
  - rigid 4-5 turn helix on an 18 cm plate, 11.6-12.0 dBic (-1.5 to -1.9 dB)
  - 18 dBi cup horn on the LNB
  Result:
  - Meteor LRPT, Meteor HRPT (about +5 dB margin), ISS and the QO-100 CW beacon are kept.
  - CubeSats keep only high passes.
  - Metop is lost, the QO-100 PSK beacon is marginal and QO-100 SSB is lost.
  - Pass selection: flying only passes above 45-60 deg recovers 8-9 dB at 435 MHz (path loss 149.8 dB at 10 deg vs 140.4 dB at 60 deg) and 2.5-6.8 dB at L-band. That offsets a dipole-only or lighter kit, at the cost of fewer passes per day.
  - Fixed geostationary targets that need no tracking: Elektro-L5 LRIT 1691 MHz (76E, about 19 deg from Kyiv), FengYun-2H 1687.5 MHz (linear, test only) and QO-100 (Kyiv about 186 deg / 32 deg).
  - Metop-class upgrade without a dish: a fold-flat 2x2 helix array on a 56 cm twist-fold photo reflector re-covered with CuNi fabric. The SmallRig unit opens to 56 cm, folds to 23 cm and weighs 274 g (listing verified). The array models 17.1-18.0 dBic after a 0.7 dB Wilkinson combiner. It is experimental, takes 5-10 min, and needs passive combining because LimeSDR channel alignment (LimeSuiteNG #356) does not cover the Micro.
  - Online fallbacks (not standalone): the SatNOGS network for missed CubeSat frames, the EUMETSAT Data Store for Metop and FengYun imagery, and the Goonhilly/BATC WebSDR for QO-100 SSB and DATV.
  - Pointing aids: a 20-25 cm folding tripod with a pan-tilt head plus the BNO085 on-screen aid removes 0.5-1.5 dB of hand-pointing loss on the 24-28 deg helicone beam and the 10-15 deg horn beams.
  - 435 MHz extras: a filtered 70 cm LNA at the feed (about 1-3 dB of system noise, estimate). Polarisation diversity: both LimeSDR RX channels tuned to 435 MHz (they share one LO), with a crossed 70 cm element set combined by MRC in software, to beat CubeSat spin fades.
- **Refuted claims:**
  1.
    - **Claim:** The 70 cm elements of the crossed Yagi (and of the split-boom N2SPI) 'pivot on one centre screw and lie flat along the boom', so the bundle packs to 35 cm.
    - **Why:** Geometry: the 28-34 cm elements at 0.030/0.094/0.170/0.316/0.475/0.640 m, turned about their centres, overhang the boom ends. The rear 35 cm half then spans 60.8 cm and the front half 45.7 cm (my calculation). Fix: clip-in or grommet elements carried alongside the halves (longest 34.0 cm), with the DE left on its coax. For the 20 cm tier, use screw-in half-elements.
  2.
    - **Claim:** QO-100 'optimistic' anchor: beacon C/N0 about G+28 dB-Hz, so a 20 dBi horn gives about 14-17 dB beacon C/N in 2.7 kHz and the 300 mm lens makes typical SSB stations readable (digest / dish_replacement.json).
    - **Why:** It is inconsistent with both primary measurements in the inputs:
  - EA4GPZ measured about 45 dB-Hz on the BPSK beacon, against transponder noise measured in 2 kHz, with a dish 'comparable to a 60cm dish' (about 34.5 dBi). That gives about G+11 to G+13 dB-Hz, or +3 dB with his later report.
  - RigExpert's bare-LNB FT8 decodes at -11 to -15 dB match G+13 with a roughly 10 dBi LNB (beacon level -11 to -8 dB in 2.5 kHz). They do not match G+28 (about +4 dB).
  Plan on 0 to +3 dB for beacon-level SSB at 21 dBi, and -9 to +4 dB for typical SSB even with the lens.
  3.
    - **Claim:** Collapsible eBay/AliExpress 5-el 70 cm Yagi '13 dBi'.
    - **Why:** Implausible: NEC of a 5-el on a 44.5 cm boom gives 10.6 dBi. The 3-el listing's '17.7 in' (45 cm) packed length also fails the 35 cm rule. Seller pages returned 403, so the listings are unverified.
  4.
    - **Claim:** R-Net 'Kvadrat' 2x17 4G panel (20.5 x 20.5 cm) gives '17 dBi' and could serve 1.7 GHz.
    - **Why:** The aperture limit for 20.5 x 20.5 cm at 1.70 GHz is 12.3 dBi at 100% efficiency, so 17 dBi would need 295% efficiency. 1.70 GHz is also below its 1710 MHz band edge, it is linear (-3 dB on RHCP), and it does not fold.
  5.
    - **Claim:** Verify stage: 'fit fixed 53 cm rods' to the V-dipole for durability.
    - **Why:** Superseded: it breaks the new fold rule. Use a spare telescopic pair, or 2-3 piece rods joined with M5 couplers.
  6.
    - **Claim:** L-band study: the helix should be a 'spring helix of phosphor-bronze or copper-clad steel' compressed flat for transport.
    - **Why:** My spring-stress estimate: compressing a 2 mm, 61.7 mm coil from 43 mm pitch to solid gives about 294 MPa shear in phosphor bronze (about 87% of a typical allowable) and about 537 MPa in Cu-clad steel (above about 360 MPa allowable), so Cu-clad steel takes a permanent set. A spring is unnecessary anyway: the 4-5 turn helix that the cone needs is only 17.2-21.5 cm long, so build it rigid. If a spring is wanted, use stainless spring wire (0.06 dB or less loss in the model).
  7.
    - **Claim:** Metop-B AHRPT with the fold helicone becomes 'about 0 to +0.5 dB average', i.e. merely 'degraded'.
    - **Why:** That figure ignores the study's own pointing loss (-0.5 to -1 dB) and build tolerance (-0.5 dB). It also ignores the intermittent modulator loss of about 7 dB recorded in dish_replacement.json (SatDump, metislair). Net about -1.5 to 0 dB average and worse during faults, so it is effectively lost as a dependable target.
  8.
    - **Claim:** Ultra-compact tier must lose 2 dB at QO-100 (inner gores only) and 1.5 dB at 435 MHz (4-el), and needs fabric at L-band.
    - **Why:** - QO-100: all six gores (largest about 19.7 x 13 cm) and the 18 cm mouth ring already fit 20 cm, so the full 23 dBi horn qualifies.
  - 435 MHz: the full 6-el with screw-in half-elements and a straight split DE (x0.95) plus hairpin models 11.05 dBi, F/B 26 dB and SWR 1.24 or less over 435-438 (my NEC run), so 0 dB, only slower to set up.
  - L-band: the petal cone stack is 19 x 19 x 4 cm and a rigid 4-turn helix is 17.2 cm (15.7 dBic model), so no fabric is needed.
  9.
    - **Claim:** L-band study: fold helicone 'estimated average SNR about 8.5-9.5 dB, margin about +8.9 to +9.4 dB'.
    - **Why:** Arithmetic inconsistency: with a 0.5 dB threshold that margin implies an SNR of about 9.4-9.9 dB, i.e. the rigid pick's about 7.75 dB plus 1.7-2.2 dB. The margin figure is the consistent one.
- **Total packed volume and weight:** Recommended tier, bounding boxes (estimates):
  - Dipole kit: 23 x 8 x 5 cm, 0.9 L
  - Crossed Yagi: 35 x 10 x 6 cm, 2.1 L
  - Helicone disc and petals: 19 x 19 x 4 cm, 1.4 L
  - L/S helix bundle: 7 x 7 x 23 cm, 1.1 L
  - QO-100 gores and rings: 20 x 19 x 1.5 cm, 0.6 L
  - Bullseye LNB: size not published, about 0.3-0.5 L assumed
  
  That makes about 6-6.5 L in all. It fits a 35 x 25 x 10 cm pouch in a small backpack. The longest pieces are the 35 cm Yagi boom halves and 34 cm elements; everything else is 23 cm or less.
  
  Weight (estimates; no vendor publishes weights for these items):
  - Dipole kit: 150-250 g
  - Crossed Yagi: 350-500 g
  - Helicone with L and S helices: 380-500 g
  - Gore horn: 150-200 g
  
  The antennas alone weigh about 1.0-1.4 kg, and about 1.3-1.8 kg with the LNB, SAWbird and jumpers. Ultra-compact tier: about 4.5-5.5 L and 1.0-1.4 kg, every piece 20 cm or less except the optional 23 cm dipole kit.
- **Total cost:** Antennas: about $76-118.
  - Dipole kit $17.95
  - Crossed 2 m/70 cm Yagi materials $25-40
  - Petal helicone plus L and S helices $23-40
  - Gore horn $10-20
  DIY prices are estimates; only the kit and the parts below are vendor prices.
  
  With the band-specific front-end parts these antennas need (SAWbird+ GOES $44.95, FM band-stop $16.95, Bullseye TCXO LNB $29.95, and a 13/18 V injector with RG6/F-SMA at about $20, estimated), the total is about $188-230.
  
  Not included:
  - S-band LNA and Sysmocom cf2235-kt30 (EUR 65.45)
  - DC blocks (about $25)
  - Cables and pigtails ($40-60)
  - A VNA covering 3 GHz or more ($60-130, unverified)
  - A mini pan-tilt tripod
  - Shipping and customs to Ukraine. The RTL-SDR Blog store ships from China in 1-8 weeks, but Ukraine is not explicitly confirmed. Nooelec shipping to Ukraine is unverified (eBay.de resellers are the fallback).
  
  The total is about the same as the rigid kit (core $185-215 plus a QO-100 add-on of about $60). Folding adds only about $0-20 for clips, prints and spares.
- **Build and test steps:**
  - 1. Order: the RTL-SDR Blog dipole kit, FM band-stop and Bullseye LNB (RTL-SDR store, or its AliExpress/eBay shops), the SAWbird+ GOES (Nooelec or eBay.de), and a VNA covering 3 GHz or more. Buy locally: 1.5 mm and 0.3-0.5 mm aluminium sheet, 20x20 mm square PVC/GRP tube, 25 mm steel tape measure, 3-3.3 mm aluminium rod, 2 mm copper wire, PETG/ASA filament, binder clips and aluminium tape.
  - 2. Crossed Yagi:
  - Cut the 0.70 m square boom at 0.35 m and print a keyed square spigot.
  - Mount the 2 m WB2HOL tapes on Axotron v3 spools (free 3MF) at 0, 0.20 and 0.51 m. Mark lengths for both 145.8 MHz and 137.5 MHz (R 111.4, DE 2x47.8, D 94.6 cm).
  - Fit snap-in clips (not centre pivots) for the six 70 cm elements at 0.030, 0.094, 0.170, 0.316, 0.475 and 0.640 m, and colour-code them.
  - Check: S11 below -10 dB on both ports, planes orthogonal within ±5 deg, and the parasitic tape halves bridged electrically.
  - 3. Helicone:
  - Base: an 18 cm disc of 1.5 mm Al.
  - Petals: 8 keyed petals of 0.3-0.5 mm Al (6.9/16.8 cm wide, 17.7 cm slant, 1 cm tabs), clipped on with at least 1 cm overlap.
  - Helix: a rigid RHCP helix of 5 or 4 turns, 61.7 mm diameter, 43 mm pitch, 2 mm Cu on a printed former, feed 30.9 mm off-centre, with a matching strip.
  - LNA: the SAWbird+ GOES on the SMA under the disc, powered by 5 V through its micro-USB, with a DC block before the Lime.
  - Check: S11 below -10 dB over 1690-1710 MHz.
  - 4. S-band helix: 7 turns, 46.7 mm diameter, 32.5 mm pitch, 228 mm, RHCP. Optionally wind an LHCP copy. Add the S-band LNA and cf2235-kt30 cavity, and check S11 over 2200-2300 MHz.
  - 5. QO-100 horn:
  - Measure the LNB's neck and waveguide inside diameter first (single mode needs 16.8-21.9 mm).
  - Lay out the gores with HDL_ANT or a compass (13.8 deg half-angle; inner radii 84-267 mm, outer 255-378 mm, 28.6 deg each).
  - Seal the seams with aluminium tape (gap under 0.2 mm).
  - Print the 40.2 mm collar clamp and the 127/180 mm rings.
  - 6. QO-100 A/B test, which also settles the link-model conflict: on the RTL, measure the C/N0 of 10489.500 and 10489.750 MHz (IF 739.500/739.750) with the bare LNB, the 18 dBi cup, the 3 inner gores and all 6 gores. Expect +8 to +12 dB (21 dBi) and +11 to +15 dB (23 dBi) over the bare LNB. An absolute beacon C/N0 of about G+13 to G+16 dB-Hz confirms the conservative model.
  - 7. L-band A/B test: compare the rigid 11-turn helix and the petal helicone on Elektro-L5 LRIT at 1691 MHz (76E, about 19 deg elevation from Kyiv), or on FengYun-2H at 1687.5 MHz. Expect +1.5 to +2.2 dB. Then try high Meteor-M N2-3/N2-4 HRPT passes from a tripod at least 50 cm above ground.
  - 8. VHF test: compare the V-dipole with the 137.5 MHz-marked tape Yagi on one Meteor pass, and the WB2HOL with the dipole on one ISS pass. Keep the FM band-stop in the path.
  - 9. Spur scan with 50 Ω terminators, host idle and then streaming, as specified in antennas.json (HDMI, PCIe and SDR clock harmonics near 145.8, 1690-1700 and 739 MHz).
  - 10. Field drill:
  - Time each setup. Targets: dipole 2 min, Yagi 4, helicone 3, horn 4.
  - After every trip, recheck S11, or beacon C/N within 1 dB of the baseline.
  - Carry spares: a telescopic pair, 2 x 70 cm elements, a petal plus clips, binder clips, aluminium tape and a spare tape spool.
- **Confidence:** medium

## dispmkt:industrial_rugged (run `wf_a429c611-ea2`)

- **Angle:** Industrial and rugged sunlight-readable modules and small monitors with HDMI plus USB touch to the host (Lilliput, Xenarc, Faytech, Litemax, Winmate/Kontron via search, Geekland, Beetronics, Eagle Touch, Densitron, Waveshare DP series), drone ground-station monitors, field monitors that pass touch to the host, and industrial bare panels from a Chinese B2B maker (Youritech) that turn out to share the Wisecoco 7in glass. I used all 12 WebSearch calls, then WebFetch on primary pages. AliExpress and eBay item pages could not be read (empty page or HTTP 403); figures from those sites are search-snippet titles only.
- **Candidates:**
  1.
    - **Name:** Xenarc 702GSH 7in sunlight-readable, optically bonded PCAP monitor
    - **Size in:** 7
    - **H res:** 1024
    - **V res:** 600
    - **Ppi:** 169.5
    - **Brightness nits:** 1000
    - **Brightness evidence:** Manufacturer spec page (1,000 cd/m2, 700:1 contrast); same on XenarcDirect. No independent measurement found.
    - **Panel tech:** TFT LCD 16:9 with scaler (accepts input up to 1920x1080 per listing)
    - **Host interface:** HDMI x1 (HDCP), VGA, DVI via adapter, 2x composite
    - **Touch to host:** Projected-capacitive multi-touch over USB (manufacturer page); a commercial USB touchscreen, expected to be standard HID
    - **Optical bonding and coating:** Touch panel optically bonded to the LCD (no air gap); anti-reflective plus anti-fingerprint coating
    - **Power w:** under 10 W (manufacturer)
    - **Supply:** DC 12 V nominal, 10-35 V operating range, so it runs straight from the 4S pack (12.8-16.8 V)
    - **Dimensions weight:** 196 x 121.5 x 35 mm; 1.54 lb, about 0.70 kg (my conversion)
    - **Operating temp:** -20 to 70 C
    - **Price:** $429 base at XenarcDirect, listed In Stock (Oct 2026 fetch)
    - **Availability:** XenarcDirect (US). International shipping is not stated on the page.
    - **Ukraine availability:** No Ukrainian reseller found; import from the US
    - **Q6a compatibility:** Good for video and touch: HDMI plus a USB-HID touch on one Q6A USB 2.0 port. Force the native mode (video=HDMI-A-1:1024x600@60) because the scaler also advertises 1080p and would downscale. Use standard CVT, not reduced blanking, for 1024x600. My calculation: CVT-RB gives only 19 vertical blanking lines, below the sc7280 DP minimum of 24, while standard CVT (about 49 MHz, vtotal 624) gives exactly 24.
    - **Rf notes:** My calculation: a 49.0-49.1 MHz CVT clock puts its 3rd harmonic at about 147.0-147.4 MHz, only about 1-1.4 MHz above the 2 m band edge. Its only other band hits are the 45th/46th harmonics in S-band. The internal scaler-to-panel clock is unknown and cannot be chosen from the host, and the backlight boost runs from 10-35 V. Budget filtering and shielding.
    - **Community reports:** None found for this model. LinuxCNC users report that similar USB-touch industrial monitors work driver-free (from the earlier audit).
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.xenarc.com/702GSH.html
      - https://www.xenarcdirect.com/702GSH.html
      - https://www.xenarc.com/all-lcd-small-form-factor-display-monitors/
  2.
    - **Name:** Xenarc 892GFC (and 892CFH) 8in IP65-front sunlight-readable PCAP monitor
    - **Size in:** 8
    - **H res:** 1280
    - **V res:** 720
    - **Ppi:** 183.6
    - **Brightness nits:** 1000
    - **Brightness evidence:** Manufacturer spec page (1,000 cd/m2, 1000:1)
    - **Panel tech:** TFT LCD 16:9 with scaler (accepts 640x480 to 1920x1080)
    - **Host interface:** 2x HDMI plus 1x USB-C 3.1 Gen 2 that 'can handle both the display and touchscreen' (implies DP Alt Mode input, not stated explicitly). The Q6A has no verified DP Alt Mode output, so use HDMI. The 892CFH variant has 2x HDMI and no USB-C.
    - **Touch to host:** Projected-capacitive multi-touch over USB, via USB-C (manufacturer page)
    - **Optical bonding and coating:** Optically bonded; anti-reflective plus anti-fingerprint
    - **Power w:** 20 W or less (manufacturer)
    - **Supply:** DC 9-36 V (12 V nominal); USB-C bidirectional PD
    - **Dimensions weight:** 220.7 x 142.7 x 33 mm; 1.89 lb, about 0.86 kg (my conversion)
    - **Operating temp:** -35 to 85 C; IP65/NEMA4 front
    - **Price:** Not listed on the manufacturer page (sold via XenarcDirect)
    - **Availability:** XenarcDirect (US)
    - **Ukraine availability:** None found
    - **Q6a compatibility:** HDMI plus USB touch works in principle. Avoid CEA 720p (74.25 MHz) for RF reasons. Plain CVT-RB 1280x720 has 21 blanking lines (fewer than 24), so use standard CVT or send 1080p and let the scaler downscale.
    - **Rf notes:** My calculation: 720p CEA 74.25 MHz x10 = 742.5 MHz, and CVT 74.5-74.7 MHz x10 = 745-747 MHz, both inside the QO-100 IF. CVT 1280x720 at 56.5 Hz (about 70.3 MHz) leaves only the 32nd harmonic, at about 2250 MHz.
    - **Community reports:** None found
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.xenarc.com/892GFC.html
      - https://www.xenarc.com/all-lcd-small-form-factor-display-monitors/
  3.
    - **Name:** Lilliput 819H/T 8in 1000-nit IP65 industrial touch monitor
    - **Size in:** 8
    - **H res:** 1024
    - **V res:** 768
    - **Ppi:** 160
    - **Brightness nits:** 1000
    - **Brightness evidence:** Reseller listing (Markertek) and the Lilliput Touch Monitor index title ('8 inch 1000 nits IP65'). Resolution is inconsistent on the listing: 1024x768 in the features vs 1280x768 in the spec table.
    - **Panel tech:** 8in 4:3 LCD, 170/170 viewing angle, 800:1
    - **Host interface:** HDMI x1, VGA x1
    - **Touch to host:** 10-point PCAP over USB-A ('for touch only'); a USB-A-to-C cable is included
    - **Optical bonding and coating:** Optically bonded, anti-glare, anti-fingerprint (listing)
    - **Power w:** 11 W or less at 12 V
    - **Supply:** DC 9-36 V (12 V/2 A adapter included), so it runs straight from the 4S pack
    - **Dimensions weight:** Listing gives 12x9x6 in and 5 lb, which look like shipping-box figures; the real unit size is not stated
    - **Operating temp:** -25 to 75 C; IP65
    - **Price:** $359 (list $399) at Markertek, out of stock, 'usually ships in 5-14 days'
    - **Availability:** Markertek (US); Lilliput distributors in the EU (Syntex carries the 719 line)
    - **Ukraine availability:** Not found on prom.ua (a Lilliput 719 search returned nothing)
    - **Q6a compatibility:** HDMI plus USB-HID touch. Force the native 4:3 mode. Standard-CVT 1024x768 is a normal VESA mode, so EDID trouble is unlikely.
    - **Rf notes:** Fixed internal scaler and panel clocks. The host mode can be chosen from a harmonic check (for example, 1024x768 at a non-60 Hz rate).
    - **Community reports:** Lilliput USB touch works driver-free on Linux (LinuxCNC forum, from the earlier audit)
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.markertek.com/product/lil-819h-t/lilliput-819h-t-8-inch-1000-nits-ip65-industrial-touchscreen-monitor-ip65-unit-with-hdmi
      - https://www.lilliput.com/touch-montior/
  4.
    - **Name:** Litemax Durapixel 0708-T (DLF0708-T panel / DLH0708-T / DLD0708-T) 7in 1600-nit
    - **Size in:** 7
    - **H res:** 1280
    - **V res:** 800
    - **Ppi:** 215
    - **Brightness nits:** 1600
    - **Brightness evidence:** Manufacturer product page spec table (1600 cd/m2, 1000:1, 55% NTSC). The features text is generic.
    - **Panel tech:** 7in TFT, 176/176 viewing angle, 35 ms
    - **Host interface:** Variants: LVDS (bare panel) or VGA/DVI-D/HDMI (kit or monitor). The page does not say which model number has which interface.
    - **Touch to host:** Not stated on the page. Ask Litemax whether a USB PCAP option exists.
    - **Optical bonding and coating:** Not stated
    - **Power w:** 5.5 W (one variant, probably the bare panel) or 8.9 W (another variant); the mapping is not given
    - **Supply:** DC 12 V
    - **Dimensions weight:** 161 x 107 x 6.22 mm, 0.12 kg (panel variant) or 171.3 x 117.8 x 42 mm, 1 kg (enclosed variant)
    - **Operating temp:** -20 to 70 C
    - **Price:** Not listed (quote)
    - **Availability:** Litemax direct or distributors (quote-based)
    - **Ukraine availability:** None found
    - **Q6a compatibility:** If the HDMI A/D-board variant is used: native 1280x800 over HDMI. Standard CVT 1280x800 (83.5 MHz) has 31 blanking lines, fine for the DP minimum of 24. Touch is unconfirmed, which disqualifies it unless Litemax supplies USB PCAP.
    - **Rf notes:** My calculation: 1280x800 CVT at about 83.5-83.8 MHz has only its 27th harmonic in band (about 2254-2262 MHz). That makes it the RF-friendliest of the low-resolution modes.
    - **Community reports:** None found
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.litemax.com/product-detail/0708-T-durapixel-industrial-display/
  5.
    - **Name:** Faytech FT07TMIP65HBHDMI 7in high-brightness IP65 HDMI touch monitor
    - **Size in:** 7
    - **H res:** 1024
    - **V res:** 600
    - **Ppi:** 169.5
    - **Brightness nits:** 1000
    - **Brightness evidence:** Manufacturer page ('1000+ cd/m2'). 1920x1080 is the maximum input resolution, not the native one.
    - **Panel tech:** TFT LCD with scaler
    - **Host interface:** HDMI or VGA
    - **Touch to host:** 4-wire resistive over USB (not capacitive)
    - **Optical bonding and coating:** Not stated
    - **Power w:** 10 W
    - **Supply:** 8-36 V DC
    - **Dimensions weight:** 214 x 134 x 38.5 mm; 1.1 kg
    - **Operating temp:** -25 to 75 C; IP65
    - **Price:** $530.60 (3-4 week lead time if not stocked). The 8in sibling FT08TMIP65HDMI is $539.43, also resistive.
    - **Availability:** Faytech North America / Faytech EU
    - **Ukraine availability:** None found
    - **Q6a compatibility:** HDMI plus USB touch works, but resistive touch has no multitouch and poor optics.
    - **Rf notes:** Same as the other 1024x600 scaler monitors
    - **Community reports:** None found
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.faytech.us/product/ft07tmip65hbhdmi7-7-inch-high-brightness-ip65-hdmi-touchscreen-monitor/
      - https://www.faytech.us/touchscreen-monitor/high-brightness/sunlight-readable/
  6.
    - **Name:** Youritech ET070WU01-HLT 7in 1200x1920 2000-nit in-cell-touch MIPI panel (bare, B2B)
    - **Size in:** 7
    - **H res:** 1200
    - **V res:** 1920
    - **Ppi:** 323.5
    - **Brightness nits:** 2000
    - **Brightness evidence:** Manufacturer product page spec table (2000 cd/m2 typ.). No datasheet; quote only.
    - **Panel tech:** Transmissive TFT (IPS-class, 80/80/80/80 viewing angle), portrait-native
    - **Host interface:** MIPI DSI only (lane count not stated). Needs a third-party HDMI-to-MIPI bridge (for example LT6911-class) flashed for this panel; none is listed.
    - **Touch to host:** In-cell touch on the panel; the touch IC is not stated (I2C). It reaches the host only through a bridge MCU that converts I2C to USB HID.
    - **Optical bonding and coating:** In-cell touch means no separate touch layer or air gap. Cover glass and AR are not stated (the vendor offers optical bonding as customization).
    - **Power w:** Not stated. My estimate scaled from the Midas 7in datasheet: about 6.4 W backlight at 2000 nits, plus the board.
    - **Supply:** Panel rails plus an LED boost; depends on the bridge board
    - **Dimensions weight:** Outline 105.46 x 162.82 mm; active area 94.5 x 151.2 mm; thickness not stated
    - **Operating temp:** -20 to 70 C
    - **Price:** Not listed ('Get a quote'); MOQ unknown
    - **Availability:** Youritech (Shenzhen) B2B
    - **Ukraine availability:** None; direct import
    - **Q6a compatibility:** In principle the best above-FHD bright option over HDMI. It is portrait-native at 1200 px wide, under the sc7280 2400 px DPU line limit, so no virtual planes are needed. My calculation: 1200x1920@60 CVT-RB is about 161 MHz and 3.86 Gbps, inside the 2-lane HBR2 8.64 Gbps budget, with 55 blanking lines (24 or more needed). Rotate in the compositor. Practically unverifiable: no timings, no bridge board, no touch-IC data. DSI direct on the Q6A is unproven for third-party panels.
    - **Rf notes:** My calculation: 161 MHz (CVT-RB 60 Hz) hits 14x = 2254 MHz in S-band. The same totals at 58 Hz (about 155.8 MHz) are clean in all six bands (1 MHz guard).
    - **Community reports:** None found
    - **Verdict vs current pick:** unverifiable
    - **Sources:**
      - https://www.youritech.com/products/7-inch-tft-lcd-display-1200x1920-high-brightness-2000nits-mipi-lcd-display-with-in-cell-touch.html
      - https://www.youritech.com/size/7-inch/
  7.
    - **Name:** Youritech ET070FH01-HTT 7in 1920x1080 4500-nit in-cell-touch MIPI panel (EV-charger grade, bare)
    - **Size in:** 7
    - **H res:** 1920
    - **V res:** 1080
    - **Ppi:** 314.7
    - **Brightness nits:** 4500
    - **Brightness evidence:** Manufacturer product page spec table (4500 cd/m2 typ.). The sibling ET070FH01-HT is listed at 2000 cd/m2.
    - **Panel tech:** Transmissive IPS TFT, 85/85/85/85 viewing angle, landscape
    - **Host interface:** MIPI only. The page says no HDMI board is offered for this model.
    - **Touch to host:** In-cell touch (IC not stated); needs a bridge MCU for USB HID
    - **Optical bonding and coating:** Not stated for this model; the vendor generally offers AG/anti-scratch cover glass and optical bonding
    - **Power w:** Not stated. My estimate: well over 10 W of backlight at full 4500 nits, scaling the Midas figure of about 3.2 W per 1000 nits. It would have to be run dimmed on a handheld.
    - **Supply:** Board-dependent
    - **Dimensions weight:** Outline 164.19 x 97.87 mm, the same as the Wisecoco 7in kit (164.2 x 98.0); active area 154.368 x 85.92 mm
    - **Operating temp:** -20 to 70 C
    - **Price:** Quote only
    - **Availability:** Youritech B2B
    - **Ukraine availability:** None; direct import
    - **Q6a compatibility:** Identical outline, resolution, viewing angle and temperature range to the Wisecoco 7in panel. If the FPC pinout also matches (unverified), it could fit the Wisecoco HDMI board as a brighter-backlight swap, provided that board's LED driver can supply the higher current. Q6A side: identical to the current pick (1080p, 1920 px wide).
    - **Rf notes:** Same as the current pick: avoid CEA 148.5 MHz. Clean options (my calculation) are 1080p at 52 Hz (128.7 MHz) or CVT-RB totals at 58.75 Hz (about 135.8 MHz). A higher-current LED boost adds switching noise.
    - **Community reports:** None found
    - **Verdict vs current pick:** unverifiable
    - **Sources:**
      - https://www.youritech.com/products/7-inch-tft-lcd-display-1920x1080-high-brightness-4500nits-mipi-lcd-display-with-in-cell-touch-for-ev-charger.html
      - https://www.youritech.com/products/7-inch-tft-lcd-display-1920x1080-mipi-2000nits-high-brightness-lcd-display-with-in-cell-touch-for-healthcare-medical-display-solution.html
  8.
    - **Name:** AliExpress '2000nit High Brightness Incell Touch CTP 7in FHD HDMI-Compatible IPS LCD Module' (alternative source for the current-pick class)
    - **Size in:** 7
    - **H res:** 1920
    - **V res:** 1080
    - **Ppi:** 314.7
    - **Brightness nits:** 2000
    - **Brightness evidence:** Listing title only, seen in a search snippet. The title literally says '1200*1080', which is probably a typo for 1920x1080. The page could not be read (empty response).
    - **Panel tech:** IPS, in-cell CTP (per title)
    - **Host interface:** HDMI (per title, via a driver board)
    - **Touch to host:** Not verifiable; probably the same CH57x USB-HID bridge class seen on Wisecoco boards
    - **Optical bonding and coating:** In-cell touch per title; cover glass unknown
    - **Price:** $106.09 (search snippet, Oct 2026), versus $132 for the Wisecoco site kit. A separate MIPI-only 2000-nit 7in FHD in-cell listing (item 3256805881153921) was $160.32.
    - **Availability:** AliExpress (store not identified)
    - **Ukraine availability:** AliExpress normally ships to Ukraine; not verified for this item
    - **Q6a compatibility:** Same as the current pick, if it is the same glass and board
    - **Rf notes:** Same as the current pick
    - **Community reports:** None found
    - **Verdict vs current pick:** comparable
    - **Sources:**
      - https://www.aliexpress.us/item/3256805990594653.html
      - https://www.aliexpress.us/item/3256805881153921.html
      - https://www.alibaba.com/product-detail/7-Inch-1920-1080-FHD-IPS_10000041147858.html
- **Best above fhd:** I found no new plug-and-play option that is above FHD and at least 1000 nits in 5.5-8in with HDMI and USB touch.
  - Industrial and rugged vendors top out at 1280x800 (Litemax 1600 nits, Lilliput 719/T 1000 nits) or 1280x720 (Xenarc 892GFC) in this size.
  - Above-FHD HDMI kits are dim: an eBay 7in 1200x1920 HDMI touch kit is listed at 500 cd/m2 ($100.09 + $35 shipping, snippet only, eBay returned 403), and the Densitron DMT070F3NHCMU-1A 7in 1200x1920 HDMI is 550 cd/m2 (snippet only).
  - The best new above-FHD part is the Youritech ET070WU01-HLT: 7in 1200x1920, 2000 cd/m2, in-cell touch, MIPI, -20 to 70 C, quote only. It is in the same class as the Midas MDT0700F1IHHC (2500 nits) but has no published timings, touch IC or bridge board.
  - It would fit the Q6A well over an HDMI-to-MIPI bridge: 1200 px wide, about 161 MHz and 3.86 Gbps at 60 Hz CVT-RB, or harmonic-clean at 58 Hz / about 155.8 MHz (my calculation).
  - Treat it as a bring-up project, not a purchase.
- **Best overall:** The current pick stands: the Wisecoco 7in 1920x1080 2000-nit LTPS/IPS kit with HDMI board and USB-HID touch.
  - No industrial or rugged maker checked (Lilliput, Xenarc, Faytech, Litemax, Geekland, Beetronics, Eagle Touch; Winmate and Kontron via search) sells a 7-8in FHD or WUXGA sunlight-readable monitor with host touch. Their 7-8in units are 800x480 to 1280x800 at 1000-1600 nits, weigh 0.4-1.1 kg, are 33-42 mm deep and draw 7-20 W.
  - No drone ground-station monitor or field/director monitor found passes touch to the host. Examples: DJI High-Bright Remote Monitor (7in 1920x1200, 2000 cd/m2 on the listing, EUR 1,459); Feelworld P7 (7in 1920x1200, 2200 nits, no touch); Portkeys LH7/LH7H/LH7P and SmallHD Indie 7 on prom.ua, all with menu-only touch.
  
  If a finished, verified, rugged host-touch unit is required despite the low resolution, the best-optics fallback is the Xenarc 702GSH:
  - 1000 nits, optically bonded, AR + anti-fingerprint coating, USB PCAP.
  - 10-35 V straight from the 4S pack, under 10 W, 0.70 kg, -20 to 70 C.
  - $429, in stock at XenarcDirect.
  
  The Lilliput 719/T (1280x800, 1000 nits, USB-C touch, 9-36 V, 8.5 W or less) stays the cheaper, sharper fallback; Markertek now lists it at $259.
  
  A cheaper source for the current-pick class may exist on AliExpress: a 2000-nit in-cell 7in FHD HDMI module at $106.09 (title only, unverified).
- **Wisecoco 7in open questions resolved:** Partly resolved, by inference, not confirmation.
  - Youritech, a Shenzhen panel maker, lists the ET070FH01-HT: 7in 1920x1080 IPS, 2000 cd/m2 typ., in-cell PCAP touch, MIPI, outline 164.19 x 97.87 mm, 85/85/85/85 viewing angle, -20 to 70 C. These match the Wisecoco 7in figures (outline 164.2 x 98.0 mm, 85/85/85/85, -20 to 70 C, 2000+ typ.) almost exactly. The two very likely share the same panel glass.
  - This explains why Wisecoco lists touch as 'Interface Type: I2C': the touch is in-cell, its IC speaks I2C on the panel FPC, and USB-HID to the host depends entirely on the HDMI board's MCU. The Raspberry Pi forum report of a Wisecoco 7in touch enumerating as WCH CH57x (1a86:e5e3, hid-multitouch) fits that design.
  - In-cell touch also means no separate touch sensor and no air gap. That is good for sunlight contrast, but the cover glass and AR coating are still unknown.
  - The same outline also exists as a 4500-nit variant (ET070FH01-HTT). The 2000/2400/2500-nit spread across Wisecoco listings is therefore plausibly backlight binning or drive current, not different glass.
  - Still unresolved: the HDMI board chip and its EDID (landscape or portrait, vertical blanking of at least 24 lines), board input voltage and current, real power at 2000 nits (my estimate is still 6-8 W), cover glass/AR, October 2026 price and stock, and shipping to Ukraine.
  - An AliExpress title ('2000nit High Brightness Incell Touch CTP 7in FHD HDMI-Compatible', $106.09) independently describes the same in-cell + HDMI configuration, but the page could not be read.
- **Notes:** Method and budget: all 12 WebSearch calls were used. AliExpress item pages came back empty, and eBay (176622684637) and Densitron product pages returned 403 or only navigation, so their figures are from search snippets only and are marked as such. Newhaven's sunlight-readable HDMI page returned 404. The search snippet shows it as NHD-7.0-HDMI-N-RSXN-CTU, 800x480 with USB-HID capacitive touch, so it is too low resolution anyway.
  
  Viable host-touch units that are clearly worse (not listed as candidates):
  - Beetronics 7TS7M: 1280x800, 250 nits, USB-HID PCAP, 9-36 V, 7 W, about 0.68 kg, $389.
  - Waveshare 8DP-CAPLCD: 8in 1280x800, only 400 cd/m2 per its wiki, optically bonded, USB-C touch, 5 V/0.8 A (4 W), 406 g, $73.99. Its wiki says brightness is settable over DDC/CI with ddcutil setvcp 10; that is the only DDC-dimmable bonded HDMI touch panel found, which is useful for auto-dimming.
  - Lilliput TK701/T: 800x480, 1000 nits.
  - Geekland GKTK701TC: 800x480, 1000 nits, 12-24 V, 8.5 W or less, 710 g, touch interface unclear.
  - Xenarc 709CNH/709GNK: IP65/IP67, 1024x600, 1000 nits, USB PCAP; 709CNH is $517.44 at TouchWindow.
  - Xenarc RT71-FHD: a 7in FHD 2600-nit rugged tablet PC, not a monitor, so it cannot take the Q6A's HDMI.
  - Eagle Touch: configurable 700/1000/1200/1500-nit PCAP monitors from 7in up, with USB touch and 9-36 V options, but no 7in FHD model is confirmed. Contact info@eagle-touch.com if you want a custom quote.
  
  Bare-panel note: the Youritech ET070WU01-R is 7in 1920x1200, 1500 cd/m2, 2.41 mm thick, -20 to 80 C, with no touch. It is bright and thin, but would need a separate touch sensor.
  
  Ukraine:
  - prom.ua has no Lilliput 719 listing (the search returned nothing).
  - A prom.ua search for 7in 1000-nit touch monitors returned only field monitors with menu-only touch: Portkeys LH7 at 21,363 UAH in stock, LH7H from 17,400 UAH and LH7P from 23,300 UAH made to order, and SmallHD Indie 7 (1920x1200, 1000 nits) from 95,100 UAH.
  - So every industrial host-touch option would be imported, from Xenarc in the US, Faytech US/EU, Syntex CZ for Lilliput, or Litemax/Youritech by quote.
  
  Q6A notes for scaler-based industrial monitors:
  - They accept standard VESA/CEA modes and rescale, so EDID and portrait problems mostly disappear.
  - But they advertise up to 1080p, so force the native mode with video=HDMI-A-1:<native>@60.
  - Avoid CVT-RB at low resolutions. My calculation: 1024x600 RB has 19 and 1280x720 RB 21 vertical blanking lines, below the DP minimum of 24. Standard CVT gives 24 (1024x600) and 31 (1280x800).
  - The host timing sets only the HDMI/TMDS clock. The scaler's own panel clock and backlight boost are fixed, so these monitors are less controllable for RF than an HDMI-to-MIPI kit whose EDID you can override.
  
  RF calculations (Python, this session; harmonics up to 2.31 GHz with a 1 MHz guard):
  - 720p CEA 74.25 MHz x10 = 742.5 MHz and CVT 74.5 MHz x10 = 745 MHz both fall in the QO-100 IF.
  - 1280x800 CVT 83.5 MHz has only its 27th harmonic in band (about 2254-2262 MHz).
  - 1024x600 CVT at about 49 MHz has its 3rd harmonic about 1-1.4 MHz above the 2 m band edge.
  - 1920x1200 CVT-RB at 154 MHz hits 11x = 1694 MHz; clean alternatives are 59.75 Hz (153.5 MHz) or 52.75 Hz (135.5 MHz).
  - 1200x1920 RB at 60 Hz (161 MHz) hits 14x = 2254 MHz; 58 Hz (155.8 MHz) is clean.
  - 1920x1080 RB at 58.75 Hz (135.8 MHz) or 52 Hz (128.7 MHz) is clean.
  - Any clock below 100 MHz always has some high-order harmonic in the 100 MHz-wide 2200-2300 band, so the harmonic order (higher means weaker) is what matters there.
  
  Power and weight for handheld use: the finished industrial units cost 7-20 W, 0.4-1.1 kg and 33-42 mm of depth, against an estimated 6-8 W for the Wisecoco kit, which is about 5 mm thick plus its board. The Wisecoco kit is better on brightness, PPI, weight and probably power. The industrial units win only on verified USB touch, wide-input supplies (9-36 V straight from the 4S pack) and documented specs.
  
  Also mentioned in search results but not verified: a VIEWE UEDX6911 HDMI-to-MIPI board 'up to 1200x1920' with 'native USB touch transmission'. Its page came back empty. If it is real, it is a candidate bridge for the Youritech or Midas 1200x1920 panels.

## dispmkt:bright_kits (run `wf_a429c611-ea2`)

- **Angle:** Chinese bright panel kits and bare bright panels (5.5-8 in, at least 1000 nits, above FHD preferred, with an HDMI board and USB touch). Covered: Wisecoco (whole high-brightness category plus site searches), VIEWE, Youritech, Kingtech, Panox, Waveshare, BOE broker listings, Microtech (HKTDC), and Ukrainian availability on prom.ua.
- **Candidates:**
  1.
    - **Name:** VIEWE UEED080FH-RB39-A003 8in 1200x1920 transflective IPS with capacitive touch (same glass is sold by Youritech as ET080TR01-VT), paired with VIEWE UEDX6911 LT6911C HDMI-to-MIPI + USB-touch board
    - **Size in:** 8
    - **H res:** 1200
    - **V res:** 1920
    - **Brightness nits:** 369
    - **Brightness evidence:** VIEWE datasheet ALL-UEED080FH-RB39-A003A V1.0 (2025-11-06):
  - Transmissive: 369 cd/m2 typ, 329 min (with touch; 435 without touch per the listing), contrast 300:1.
  - Reflective: white reflectance 7% typ (6.5% min), contrast 15:1, 15-20% NTSC.
  My calculation, assuming an extra 1% front-surface reflection: in 100 klx sun the reflected white is about 2230 cd/m2 and contrast is about 6-17:1, against about 7:1 for a 2000-nit transmissive panel. The panel gets better the brighter the sun is. The Youritech page lists the same 369 nits and the same 132.6x202.6x4.98 mm outline.
    - **Host interface:** - Panel: MIPI DSI 4-lane on a 45-pin 0.3 mm FPC; VDD 3.3 V; VLED 25.2 V at 115 mA (45 LEDs).
  - Board: UEDX6911 uses an LT6911C (HDMI 1.4 to 1/2-port DSI, up to 1.5 Gbps per lane) and accepts HDMI input.
  - Fit is unconfirmed. The board datasheet lists only 30-pin and 40-pin VIEWE panels (2.1-10.1 in), not this 45-pin panel. VIEWE only shows the two as 'Frequently bought together'.
    - **Touch to host:** - The panel's touch is I2C at 1.8 V on the FPC (pins 10-14); the touch IC is not named.
  - The UEDX6911 has an IIC touch header and presents 5-point USB HID, driver-free per its datasheet.
  - Whether its firmware supports this panel's touch IC is unconfirmed; ask VIEWE.
    - **Price:** $74.99 for the panel (was $75.99); UEDX6911 $18 (was $20); bundle $92.99 on viewedisplay.com, checked 18 Oct 2026. Youritech: quote only.
    - **Availability:** OUT OF STOCK on viewedisplay.com (18 Oct 2026); 'Get a Quote' is available. Youritech sells the same panel B2B. Not found in Ukrainian shops (prom.ua searches). Ship-to-Ukraine terms unknown.
    - **Q6a compatibility:** Plausible over HDMI, but not plug-and-play (calculations below).
  - Portrait-native 1200 px wide, below the sc7280 2400 px linewidth, so no virtual planes are needed; rotate in the compositor.
  - 1200x1920@60 with 30 lines of vertical blanking is about 150 MHz and 3.6 Gbps: it needs at least DP HBR on 2 lanes (RBR is too small). It is well inside the 8.64 Gbps limit and within the LT6911C's HDMI 1.4 limit.
  - Check that the board's EDID has at least 24 lines of vertical blanking.
  - Driver ICs are HX8279D x2; mainline has a panel-boe-himax8279d driver for BOE 8in 1200x1920 panels, so a later direct-DSI route is conceivable, but Q6A DSI is unproven.
  - Biggest risk: the UEDX6911 is rated at 5 V, 150 mA with backlight off and 260 mA at maximum backlight (about 1.3 W total). That is far below this panel's 2.9 W backlight, so the board's LED driver may not reach full brightness; plan an external 25 V constant-current driver (the panel exposes a PWMOUT pin).
    - **Verdict vs current pick:** unverifiable
    - **Sources:**
      - https://viewedisplay.com/product/8-inch-1200x1920-transflective-tft-sunlight-readable-and-low-power-high-resolution-touch-display/
      - https://viewedisplay.com/download/72/display-datasheet/10529/all-ueed080fh-rb39-a003a-spec-1-0.pdf
      - https://viewedisplay.com/product/hdmi-to-mipi-dsi-converter-board/
      - https://viewedisplay.com/download/73/smart-display-datasheet/11743/uedx6911-hdmi-driver-board-spec-v2-0.pdf
      - https://www.youritech.com/products/8-inch-transflective-display-1200x1920-mipi-4-lanes-sunlight-readable-lcd-display-with-capacitive-touch.html
      - https://kernel.org/doc/Documentation/devicetree/bindings/display/panel/boe%2Chimax8279d.txt
    - **Panel tech:** a-Si IPS transflective, normally black, 283 PPI (calculated). Gamut 36-40% NTSC transmissive, 15-20% reflective. Viewing angle 60/60/60/60 at CR>2.
    - **Optical bonding and coating:** - Datasheet drawing: full OCA lamination of cover glass and touch ('全贴OCA'); 1.8 mm cover glass; 2.4 mm touch stack.
  - AF (anti-fingerprint) surface coating; UV-resistant ink.
  - Not stated as AR or AG.
    - **Power w:** Datasheet module power:
  - 3.27 W transmissive (backlight 2.898 W).
  - 0.18 W reflective with the backlight off.
  Board: 5 V at 150 mA with backlight off, about 0.75 W.
  My estimate: about 1 W in sun with the backlight off, about 4 W indoors.
    - **Supply:** Panel: VDD 2.5-3.3 V, VLED 25.2 V at 115 mA. Board: 5 V (4.0-5.5 V), 1 A recommended. Can run from the existing 5 V buck.
    - **Dimensions weight:** Panel 132.6 x 202.6 x 4.98 mm (6.98 mm max at the FPC area per drawing); active area 108 x 172.8 mm. Listing weight 0.51 kg (probably packed weight). Board 66 x 58 mm.
    - **Operating temp:** -20 to 70 C operating; storage -30 to 80 C (page) or -40 to 80 C (drawing). 240 h tests at 70 C and -20 C operating.
    - **Rf notes:** Calculations:
  - 1200x1920@60 at about 149.8 MHz puts its 5th harmonic at 748.8 MHz (QO-100 IF) and its 15th at 2246 MHz.
  - Clean alternative: 1280x1950 total at 51.3-51.8 Hz (about 128.0-129.3 MHz) has no harmonics in any listed band up to 2.3 GHz with 1 MHz margin, if the LT6911C accepts it.
  - At 60 Hz the DSI lane rate is about 899 Mbps (449 MHz DDR clock, 5th harmonic 2246 MHz). At 51.5 Hz the DDR clock is about 386 MHz and its harmonics miss the listed bands (6th = 2314 MHz).
  - Switching the 25 V backlight boost off in sun removes a noise source.
    - **Community reports:** None found. No forum, Reddit or Radxa post on this panel or on the UEDX6911.
    - **Ukraine availability:** Not listed on prom.ua; order from VIEWE or Youritech directly.
  2.
    - **Name:** Youritech ET070WU01-HLT 7in 1200x1920, 2000 nits, in-cell touch (bare MIPI). Microtech MTF070UG53A-V1 (7.02in 1920x1200, title '2000 high brightness', no touch) has the identical 105.46x162.82 mm outline
    - **Size in:** 7
    - **H res:** 1200
    - **V res:** 1920
    - **Brightness nits:** 2000
    - **Brightness evidence:** - Youritech product page spec: '2000 cd/m2 (Typ.)'. No datasheet or measurement.
  - Microtech lists '2000 high brightness' in its HKTDC title only; brightness is absent from its spec table.
  - The matching outline (105.46x162.82 mm) and active area (94.5x151.2 mm) suggest the same glass from two vendors.
    - **Host interface:** MIPI DSI (lanes and pins not stated). Needs an HDMI-to-MIPI bridge. Youritech advertises 'H-DMI board' and driver-board solutions generically, not for this model.
    - **Touch to host:** In-cell touch; controller not stated. A raw in-cell controller is normally I2C and would need a USB-HID bridge, either from the HDMI board or a separate MCU.
    - **Price:** Quote only (Youritech 'Get a quote'). Microtech: no price, 25-45 day lead time.
    - **Availability:** Youritech (Shenzhen) and Microtech (HK/China) B2B. Not in Ukrainian shops.
    - **Q6a compatibility:** Possible only via a vendor-flashed HDMI-to-MIPI board.
  - 1200 px wide portrait fits the DPU; about 150 MHz at 60 Hz needs DP HBR on 2 lanes (calculated); rotate in the compositor.
  - A 2000-nit 7in backlight draws about 6-7 W (estimate scaled from the Midas datasheet: 400 mA at 16 V for 2000 nits). Cheap LT6911 boards such as the UEDX6911 (about 1.3 W total) cannot drive it, so an external LED driver or a vendor board is required.
    - **Verdict vs current pick:** unverifiable
    - **Sources:**
      - https://www.youritech.com/products/7-inch-tft-lcd-display-1200x1920-high-brightness-2000nits-mipi-lcd-display-with-in-cell-touch.html
      - https://www.youritech.com/resolution/1200x1920/
      - https://www.hktdc.com/event/electronicasia/en/product/1Z03HV3K9
    - **Panel tech:** Transmissive TFT; viewing angle 80/80/80/80; 323 PPI (calculated).
    - **Optical bonding and coating:** In-cell touch, so there is no separate touch layer or air gap. Cover glass not stated.
    - **Power w:** Not stated. Estimate 6-8 W at full brightness, from Midas datasheet scaling.
    - **Supply:** Not stated. Typical for this panel class: 1.8 V IOVCC, +/-5.5 V, and an LED string of about 16 V.
    - **Dimensions weight:** Outline 105.46 x 162.82 mm; active area 94.5 x 151.2 mm. Microtech gives 2.4 mm thickness without touch. Weight not stated.
    - **Operating temp:** -20 to 70 C (Youritech)
    - **Rf notes:** Same calculations as the other 1200x1920 panels: 60 Hz at about 150 MHz hits 748.8 and 2246 MHz; 51.3-51.8 Hz (about 128-129 MHz) is clean. The backlight boost at 2000 nits is a strong switching-noise source: shield it.
    - **Community reports:** None found.
    - **Ukraine availability:** None.
  3.
    - **Name:** Youritech ET070WU15-TT / ET070WU10-TT 7.02in 1200x1920, 1500 nits, with capacitive touch; driver, DEMO and 'H-DMI' boards offered
    - **Size in:** 7.02
    - **H res:** 1200
    - **V res:** 1920
    - **Brightness nits:** 1500
    - **Brightness evidence:** Youritech product page: '1500 cd/m2 (typical)', 'customizable from 0 to 3000'. The ET070WU15-TT reference line reads '1200x1920, MIPI, 1500nits, -20~70C, 114.04x178.25mm, CTP'. No datasheet or measurement.
    - **Host interface:** MIPI DSI (lanes not stated). The page says a 'Driver board/adapter board, standard type and design customization: DEMO board, H-DMI board' and an 'H-DMI display solution' are available, so an HDMI kit can be ordered by quote.
    - **Touch to host:** Capacitive touch panel, optional ('CTP'); controller and interface not stated. Ask for USB-HID output on the HDMI board.
    - **Price:** Quote only.
    - **Availability:** Youritech (Shenzhen) B2B; lead time unknown. Not in Ukraine.
    - **Q6a compatibility:** Good on paper if Youritech supplies the HDMI board flashed for the panel with USB touch.
  - Portrait 1200 px wide: no DPU split problems.
  - About 150 MHz at 60 Hz needs DP HBR (calculated).
  - Require an EDID with at least 24 lines of vertical blanking.
    - **Verdict vs current pick:** unverifiable
    - **Sources:**
      - https://www.youritech.com/products/7-02-inch-tft-lcd-display-1200x1920-mipi-high-brightness-1500nits-lcd-module.html
      - https://www.youritech.com/products/7-inch-high-brightness-display-1500nits-ips-1200x1920-mipi-tft-lcd-display-2.html
    - **Panel tech:** Transmissive TFT; 85/85/85/85; 100% NTSC claimed; 322.5 PPI (calculated).
    - **Optical bonding and coating:** Not stated; Youritech offers custom cover glass.
    - **Power w:** Not stated. Estimate 4-6 W at 1500 nits.
    - **Supply:** Not stated.
    - **Dimensions weight:** Outline 114.04 x 178.25 mm (with touch); active area 94.5 x 151.2 mm.
    - **Operating temp:** -20 to 70 C
    - **Rf notes:** As above: avoid 60 Hz near 149.8 MHz; 51.3-51.8 Hz (about 128-129 MHz) is clean (calculated).
    - **Community reports:** None found.
    - **Ukraine availability:** None.
  4.
    - **Name:** Youritech ET070WU07-O 7in 1200x1920, 1500 nits (no touch). Its outline (160.80x98.70x1.97 mm) is identical to the panel in Wisecoco's $69 7in 1920x1200 500-nit HDMI-to-MIPI 40-pin kit
    - **Size in:** 7
    - **H res:** 1200
    - **V res:** 1920
    - **Brightness nits:** 1500
    - **Brightness evidence:** Youritech spec table: luminance 1500 cd/m2 typ, contrast 1200:1, 45 white LEDs, backlight '9~11v', hard coating. No datasheet or measurement.
    - **Host interface:** MIPI (the page says 'Dgital'; 5.5 V supply).
  Hypothesis, not verified: the outline and active area (151.2x94.5 mm) match the Wisecoco 500-nit 1920x1200 panel. If the pinout and driver IC also match, Wisecoco's HDMI-to-MIPI 40-pin board could drive this brighter glass. The backlight current would need checking.
    - **Touch to host:** None; it would need an add-on CTP plus a USB-HID controller.
    - **Price:** Quote only. Reference: Wisecoco 500-nit kit with driver board $69.
    - **Availability:** Youritech B2B.
    - **Q6a compatibility:** As for the other 1200x1920 portrait panels (fits the DPU, needs HBR, needs at least 24 lines of vertical blanking). Lacks touch, so it fails the touch requirement unless a touch layer is added.
    - **Verdict vs current pick:** unverifiable
    - **Sources:**
      - https://www.youritech.com/products/oem-odm-high-brightness-1500-nits-mipi-lcd-display-screen-for-outdoor-7-inch-tft-ips-lcd-display-1200x1920-lcd-module.html
      - https://www.wisecocodisplay.com/product/7-inch-tft-lcd-module-mipi-40-pin-1920x1200-ips-lcd-display/
    - **Panel tech:** a-Si TFT, normally black, 80/80/80/80, 323 PPI (calculated).
    - **Optical bonding and coating:** Hard coating; no touch or cover glass.
    - **Power w:** Not stated (45 LEDs, backlight 9-11 V; panel 60 mA). Estimate 4-6 W at 1500 nits.
    - **Supply:** 5.5 V typ panel supply plus a 9-11 V backlight.
    - **Dimensions weight:** 160.80 x 98.70 x 1.97 mm; active area 94.5 x 151.2 mm.
    - **Operating temp:** -20 to 70 C (the sister ET070WU12-O and ET070WU18-OT are only -10 to 60 C).
    - **Rf notes:** As other 1200x1920 panels (calculated).
    - **Community reports:** None found.
    - **Ukraine availability:** None.
  5.
    - **Name:** BOE GV070WUM-L50-1SP0 7in 1200x1920, 1000 nits, in-cell touch (bare industrial panel)
    - **Size in:** 7
    - **H res:** 1200
    - **V res:** 1920
    - **Brightness nits:** 1000
    - **Brightness evidence:** Broker listing (slw-ele.com): 1000 cd/m2 typ, contrast 1200:1 min. Not a BOE datasheet.
    - **Host interface:** MIPI DSI 4-lane, 40-pin; 1.8 V VDDI, +/-5.5 V. No HDMI board is offered pre-configured.
    - **Touch to host:** In-cell, I2C; needs a USB-HID bridge.
    - **Price:** 'US$50-200 (estimated)', RFQ; MOQ 1.
    - **Availability:** Broker shows 500 in stock with a 1-2 day lead time (unverified); not in Ukraine.
    - **Q6a compatibility:** Needs a custom LT6911 or LT8912-class bridge flashed for its init sequence, plus a touch bridge. Hard for a hobbyist.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.slw-ele.com/gv070wum-l50-1sp0.html
    - **Panel tech:** TFT, 323 PPI (calculated).
    - **Optical bonding and coating:** Hard coating; in-cell touch.
    - **Power w:** Not stated.
    - **Supply:** 1.8 V, 5.5 V, -5.5 V plus the LED string.
    - **Dimensions weight:** 109.8 x 173 x 5.25 mm
    - **Operating temp:** -20 to 70 C
    - **Rf notes:** As other 1200x1920 panels.
    - **Community reports:** None found.
    - **Ukraine availability:** None.
  6.
    - **Name:** Youritech ET080WU05-OT 8in 1200x1920, 1100 nits, capacitive touch (bare MIPI)
    - **Size in:** 8
    - **H res:** 1200
    - **V res:** 1920
    - **Brightness nits:** 1100
    - **Brightness evidence:** Youritech page: 1100 cd/m2 typ. No datasheet.
    - **Host interface:** MIPI; no HDMI board listed for this model.
    - **Touch to host:** Capacitive; interface not stated.
    - **Price:** Quote only.
    - **Availability:** Youritech B2B.
    - **Q6a compatibility:** Same as other 1200x1920 panels, but it needs a sourced bridge and touch bridge.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.youritech.com/products/8-inch-high-brightness-display-1100nits-ips-1200x1920-mipi-tft-lcd-display-with-capacitive-touch.html
    - **Panel tech:** IPS transmissive, 283 PPI (calculated).
    - **Optical bonding and coating:** Not stated.
    - **Power w:** Not stated.
    - **Supply:** Not stated.
    - **Dimensions weight:** 119.41 x 184.84 mm; active area 107.64 x 172.22 mm.
    - **Operating temp:** 0 to 50 C only (risky in summer sun).
    - **Rf notes:** As other 1200x1920 panels.
    - **Community reports:** None found.
    - **Ukraine availability:** None.
- **Best above fhd:** No new above-FHD candidate is a verified plug-and-play kit; on paper there are two routes.
  
  **Route 1: VIEWE UEED080FH 8in 1200x1920 transflective + UEDX6911 board ($74.99 + $18).**
  - It is the only above-FHD option with a full datasheet and a retail price.
  - Datasheet: full OCA lamination and 7% reflectance with 15:1 reflective contrast. My calculation gives about 6-17:1 contrast in 100 klx sun at about 1-4 W, against about 7:1 at 6-8 W for the 2000-nit pick.
  - Drawbacks:
    - pale colours in sun (15-20% NTSC)
    - only 369 nits and 300:1 indoors
    - 60-degree viewing cone
    - out of stock
    - 45-pin panel versus the 30/40-pin board
    - the board's 1.3 W rating is too weak for the 2.9 W backlight.
  - Before ordering, VIEWE must confirm the board-to-panel firmware, cable and touch IC.
  
  **Route 2: a quote from Youritech for the 7in 1200x1920 ET070WU01-HLT (2000 nits, in-cell touch) or ET070WU15-TT (1500 nits, CTP) with their 'H-DMI' board and USB touch.**
  - This keeps transmissive colour quality, but is unverified B2B.
- **Best overall:** Keep the Wisecoco 7in 1920x1080 2000+ nit HDMI kit as the main pick. None of the new candidates beats it with verified data.
  - It is still the only listing found that combines at least 2000 nits, an HDMI board and touch, and can be bought with a cart button ($132, 18 Oct 2026).
  - New fact: the page says 'Landscape by Default', so the EDID should be 1920x1080 landscape. 1920 px is below the 2400 px DPU limit and needs no rotation.
  - Treat the VIEWE 8in transflective (sun-optimised, low power) or a Youritech 7in 1200x1920 1500-2000 nit quote as the above-FHD alternatives.
- **Wisecoco 7in open questions resolved:** From the wisecocodisplay.com product page, fetched 18 Oct 2026.
  
  Resolved or newly stated:
  - Price $132 (struck-through $135), with both 'Add to cart' and 'Get a Quote'; 0 reviews.
  - New: 'Landscape by Default - Pre-configured widescreen orientation', so the EDID should be 1920x1080 landscape (my reading).
  - The spec lists 'Capacitive touch', 'MIPI (4 data lanes)' and an 'Interface Type: I2C' field. I2C is most likely the bare touch panel's interface, so USB-HID depends on the HDMI board.
  - Brightness: '2000+ cd/m2 (Typ.)' in the spec versus '2500Nits' in the title. No measurement exists.
  - Outline 164.22 x 97.98 mm; active area 155.82 x 87.83 mm (the table swaps the axes); operating -20 to 70, storage -30 to 80 (units not given, presumably C).
  
  Still unresolved:
  - the exact contents of the $132 kit
  - touch VID:PID (the CH57x USB-HID evidence comes from a different Wisecoco 7in, Pi forum t=368455)
  - board input voltage, current and power
  - lamination and AG/AR
  - panel part number, thickness, weight.
  
  Blocked or caveats:
  - eBay listings 176657492046, 177315425196 ('7'' Touch Screen High Brightness 1920x1080 HMDI LCD Display Driver Board DIY KIT') and ebay.de 405247794619 return HTTP 403 here, and AliExpress needs a login, so no current marketplace price.
  - Ukraine: prom.ua resellers carry only Wisecoco's 12.6in and 7.84in bar monitors, not this kit, so it must be imported.
  - Warning: Wisecoco's 7in 1024x600 'sunlight readable' listing has '2000nits' in its URL, '1000nits' in its title and '400 cd/m2' in its spec. Insist on a datasheet plus a luminance-meter photo before paying.
- **Notes:** **Searches:** 12 WebSearch calls were used; everything else was WebFetch or curl on primary pages.
  
  **Not found:** no plug-and-play 5.5-8in kit that is above FHD, at least 1000 nits, with an HDMI board and USB touch, from Wisecoco, VIEWE, Youritech, Kingtech, Panox, Waveshare or the Shenzhen B2B listings that were reachable. Searches mostly returned 1024x600 1000-nit industrial monitors (Xenarc, Geekland) or camera monitors.
  
  **Below threshold (dim or wrong format), not viable:**
  - Waveshare's brightest in this range is 800 nits (5in 1024x600; 9.3in 1600x600).
  - Kingtech 8in 1200x1920 PV08004TD31C-C: 500 nits.
  - Wisecoco 7in 1920x1200 with HDMI board: 500 nits, $69.
  - Wisecoco 6in 2560x1440 with HDMI + USB board: 450 nits, $80-85.
  - Youritech Tianma TL070FVXS01-02 7in FHD eDP: 500 nits.
  - Youritech 8in AMOLED 2480x1860: 600 nits, no touch.
  - Wisecoco 5.5in 2160x3840: 4K60 exceeds the Q6A's 4K30 cap.
  
  **Key component fact (UEDX6911 datasheet):**
  - The generic $18 VIEWE UEDX6911 HDMI-to-MIPI board uses an LT6911C (HDMI 1.4, 1-4 lanes per port, 80 Mbps to 1.5 Gbps per lane) and gives driver-free 5-point USB HID touch.
  - It runs from 5 V (4.0-5.5 V); input current is 150 mA with the backlight off and 260 mA at maximum backlight, i.e. about 1.3 W.
  - That means cheap LT6911 boards cannot power 1500-2500 nit 7-8in backlights (4-8 W). Any bright bare panel needs a vendor board with a strong LED driver, or an external constant-current driver.
  
  **Calculations (mine):**
  - PPI: 7in 1200x1920 323.5; 7.02in 322.5; 8in 1200x1920 283; 7in FHD 314.7.
  - 1200x1920@60 (1280x1950 total) is 149.76 MHz and 3.59 Gbps. It needs DP HBR on 2 lanes (RBR 2-lane gives only 2.59 Gbps).
  - RF: harmonics land at 748.8 and 2246 MHz. Clean refresh for that total: 51.3-51.8 Hz (128.0-129.3 MHz) or 54.3-54.4 Hz (135.5-135.8 MHz).
  - Sunlight contrast (1% front-surface diffuse reflection):
  
  | Ambient | 2000 nits | 1500 nits | 1000 nits |
  |---|---|---|---|
  | 100 klx | 7.2:1 | 5.7:1 | 4.1:1 |
  | 50 klx | 13.4:1 | 10.3:1 | 7.2:1 |
  
  - The transflective 8in is 6.2-17.3:1 at 100 klx with its backlight on.
  
  **Inaccessible:** eBay (HTTP 403), AliExpress (login), Alibaba and Raystar (empty pages), Youritech category pages (HTTP 500/503). prom.ua is reachable: no new candidate is stocked there; it lists BenQ PVS7 2000-nit on order (already evaluated) and Wisecoco bar monitors.
  
  **Community reports:** none found for any new candidate.
  
  **Local copies:** the panel datasheet is saved at /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/pdf/ueed080.pdf and the board datasheet at /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/pdf/uedx6911.pdf. The calculation script is /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/calc_disp.py.

## dispmkt:consumer_reuse (run `wf_a429c611-ea2`)

- **Angle:** Reusing consumer panels: 7-8in 2.5K portable monitors, spare screens from handheld gaming PCs (AYANEO, Legion Go/Go S, MSI Claw, OneXPlayer, Steam Deck OLED), tablet panels with HDMI driver boards (iPad mini, Sharp 7.9in QXGA, Nexus 7 JDI, Legion Tab, Galaxy Tab Active5), and phone or foldable AMOLED panels with HDMI boards. For each: realistic full-screen brightness through a third-party board, whether touch reaches the host, and availability (including Ukraine).
- **Candidates:**
  1.
    - **Name:** AYANEO KUN 8.4in 2.5K IPS panel (brightest measured consumer above-FHD panel)
    - **Size in:** 8.4
    - **H res:** 1600
    - **V res:** 2560
    - **Brightness nits:** 678
    - **Brightness evidence:** Independent measurement (Notebookcheck, X-Rite i1Pro 2, inside the device): 677.6 nits average, 706 max, 684 center, 91% uniformity, 1360:1 contrast. The reviewer still found it 'significantly impaired outdoors'. My estimate of sun contrast is about 3.1:1, against 7.3:1 for 2000 nits.
    - **Panel tech:** IPS LCD. Portrait-native: the kernel's drm_panel_orientation_quirks entry for 'AYA NEO KUN' is lcd1600x2560_rightside_up. 10-point touch. DC dimming, with 20 kHz flicker between 30% and 80%.
    - **Ppi:** 359
    - **Host interface:** Inside the device it is almost certainly eDP (x86 APU), but that is my inference. No spare panel and no HDMI board found.
    - **Touch to host:** Unknown. The touch controller sits on the device's internal bus; no USB HID path exists.
    - **Optical bonding and coating:** Glossy cover glass, laminated in the device.
    - **Power w:** Not published for the panel alone.
    - **Supply:** n/a (no driver board)
    - **Dimensions weight:** Not published.
    - **Operating temp:** Not published.
    - **Price:** Not sold as a spare. An AliExpress search on 18 Oct 2026 for KUN screens returned only a $70 KUN battery.
    - **Availability:** No spare panel listing found.
    - **Ukraine availability:** None found.
    - **Q6a compatibility:** Good on paper, but no board exists. It is 1600 px wide in its native portrait mode, so it fits the 2400 px DPU limit without virtual planes. 1600x2560@60 CVT-RB is about 278 MHz (6.67 Gbps, my calculation), under the 330 MHz practical ceiling.
    - **Rf notes:** My calculation: 278 MHz has its 8th harmonic at 2224 MHz (S-band). 59.3 Hz CVT-RB (274.5 MHz) has no hits in any receive band. Behind a scaler board, the HDMI clock follows whichever EDID mode the host picks.
    - **Community reports:** Notebookcheck: readable outdoors only at an angle. No DIY reuse reports found.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.notebookcheck.net/Ayaneo-Kun-gaming-handheld-in-review-Performance-beast-for-individualists.797526.0.html
      - https://raw.githubusercontent.com/torvalds/linux/master/drivers/gpu/drm/drm_panel_orientation_quirks.c
      - https://www.aliexpress.com/w/wholesale-ayaneo-kun-lcd-screen.html
  2.
    - **Name:** Lenovo Legion Go (8APU1) 8.8in 2560x1600 144 Hz screen + digitizer assembly, with a generic 40-pin eDP-to-HDMI/Type-C board
    - **Size in:** 8.8
    - **H res:** 1600
    - **V res:** 2560
    - **Brightness nits:** 413
    - **Brightness evidence:** Independent measurement (Notebookcheck): 413.3 nits average, 460 max, 444 center, 80% uniformity, 979:1 contrast. Lenovo claims 500. A generic eDP board can at best match this if it drives the panel's backlight PWM at 100%. Sun contrast about 2.3:1 (my estimate).
    - **Panel tech:** IPS LCD, 144 Hz. Portrait-native: kernel quirk 'Legion Go 8APU1' is lcd1600x2560_leftside_up. PWM 700 Hz.
    - **Ppi:** 343
    - **Host interface:** The panel is eDP (my inference from the AMD Z1 platform). Generic '40-pin EDP 2560x1600/2560x1440 Type-C/HDMI driver board' listings cost $21.34-22.45, but none claims Legion Go fit. The panel's FPC connector and pinout are unverified and may not be the standard 40-pin laptop connector.
    - **Touch to host:** The digitizer comes laminated in the spare assembly. Its controller interface is unknown and probably not USB. You would need to wire it to the Q6A header I2C as I2C-HID, which is unverified.
    - **Optical bonding and coating:** Laminated, glossy and reflective (Notebookcheck: outdoor use is 'a bit of a nuisance').
    - **Power w:** Not published.
    - **Supply:** Generic eDP boards take 5 V USB-C or 12 V, depending on the board.
    - **Dimensions weight:** Not published for the assembly.
    - **Operating temp:** Not published (consumer part).
    - **Price:** AliExpress (18 Oct 2026): $43.92 (25 sold) and $79.80 for '8APU1 WT001' assemblies; $207.60 for the Lenovo FRU 5D10S40055 assembly. Generic eDP board about $22.
    - **Availability:** AliExpress. Assemblies are plentiful; a driver board that fits is not.
    - **Ukraine availability:** A prom.ua search turned up only screen protectors (134-799 UAH), no display assemblies. AliExpress ships to Ukraine.
    - **Q6a compatibility:** Uncertain. The portrait 1600 px width avoids the DPU 2400 px limit, and 278 MHz CVT-RB fits the DP link (my calculation). Unknowns: whether the board offers a 60 Hz 1600x2560 EDID, whether the eDP connector and pinout match, and whether touch can be wired.
    - **Rf notes:** 278 MHz 8th harmonic at 2224 MHz; 59.3 Hz (274.5 MHz) is clean (my calculation). The board's eDP link is a separate emitter (HBR is 2.7 Gbps).
    - **Community reports:** Notebookcheck review only. No DIY HDMI conversion reports found.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.notebookcheck.net/Lenovo-Legion-Go-gaming-handheld-review-Good-idea-not-quite-perfectly-executed.794034.0.html
      - https://www.aliexpress.com/w/wholesale-legion-go-screen-driver-board.html
      - https://www.aliexpress.com/w/wholesale-legion-go-screen-hdmi-type-c-controller-board.html
      - https://raw.githubusercontent.com/torvalds/linux/master/drivers/gpu/drm/drm_panel_orientation_quirks.c
      - https://prom.ua/search?search_term=Legion%20Go%20дисплей
  3.
    - **Name:** Lenovo Legion Go S / MSI Claw 8 AI+ 8.0in 1920x1200 120 Hz IPS panel (PN8007QB1-1)
    - **Size in:** 8
    - **H res:** 1920
    - **V res:** 1200
    - **Brightness nits:** 509
    - **Brightness evidence:** Independent measurement (Notebookcheck, Legion Go S): 509.3 nits average, 538.8 max, 1171:1 contrast, no PWM. Notebookcheck's ICC profile file name is 'NS080WUM_LX1'. Sun contrast about 2.6:1 (my estimate).
    - **Panel tech:** IPS LCD, 120 Hz, glossy.
    - **Ppi:** 283
    - **Host interface:** eDP in the device (my inference). No HDMI board listed for it.
    - **Touch to host:** The $112.50 'Legion Go S LCD with touch panel digitizer' includes a digitizer; its interface is unknown. The $87.71 PN8007QB1-1 listing does not mention touch.
    - **Optical bonding and coating:** Glossy; strong reflections (Notebookcheck).
    - **Price:** $87.71 (PN8007QB1-1) or $112.50 (with digitizer) on AliExpress, 18 Oct 2026.
    - **Availability:** AliExpress spare parts.
    - **Ukraine availability:** Not found on prom.ua.
    - **Q6a compatibility:** Video should be easy (1920 px wide, about 154 MHz), but you need an eDP board that supports this panel. Only marginally above FHD.
    - **Rf notes:** 1920x1200@60 CVT-RB at 154 MHz has its 11th harmonic at 1694 MHz (L-band HRPT/HRIT). 50.6 Hz (129.25 MHz) is clean (my calculation).
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.notebookcheck.net/Lenovo-Legion-Go-S-gaming-handheld-review-Steam-Deck-killer-or-Windows-victim.961296.0.html
      - https://www.aliexpress.com/w/wholesale-legion-go-screen-driver-board.html
  4.
    - **Name:** OneXPlayer 2 Pro 8.4in 2560x1600 IPS (handheld panel)
    - **Size in:** 8.4
    - **H res:** 2560
    - **V res:** 1600
    - **Brightness nits:** 287
    - **Brightness evidence:** Independent measurement (Notebookcheck): 287 nits in the comparison table, 311 nits in the review text, 'much less bright than the competition'.
    - **Panel tech:** IPS LCD
    - **Ppi:** 358
    - **Host interface:** No spare panel or HDMI kit found.
    - **Touch to host:** None available.
    - **Price:** Not found as a spare.
    - **Availability:** None found.
    - **Q6a compatibility:** Not applicable.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.notebookcheck.net/OneXPlayer-2-Pro-gaming-handheld-tablet-or-detachable-in-review-multifaceted-device-with-strong-Ryzen-7.798258.0.html
  5.
    - **Name:** Lenovo Legion Tab / Legion Y700 8.8in 2560x1600 (and Gen 5 3040x1904) tablet panels
    - **Size in:** 8.8
    - **H res:** 1600
    - **V res:** 2560
    - **Brightness nits:** 421
    - **Brightness evidence:** Independent measurement (Notebookcheck, TB320FC): 420.8 nits average, 472 max. Gen 3: about 420 full-screen, 441 SDR max, 900 HDR peak. Gen 5 (3040x1904): Notebookcheck news quotes 600 nits typical from Lenovo's spec.
    - **Panel tech:** IPS LCD, 144-165 Hz
    - **Ppi:** 343
    - **Host interface:** Android SoC, so probably MIPI DSI (my inference). An AliExpress search for 8.8in 2560x1600 HDMI kits (18 Oct 2026) found none; the results were 16-17in laptop panels only.
    - **Touch to host:** None available.
    - **Price:** No panel-plus-board kit found.
    - **Availability:** None as a usable kit.
    - **Q6a compatibility:** 2560x1600: about 278 MHz in portrait would fit, but no board exists. Gen 5's 3040x1904@60 CVT-RB needs 376-387 MHz (my calculation), above the about 330 MHz ceiling.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.notebookcheck.net/Lenovo-Legion-Tab-review-How-well-does-the-gaming-tablet-perform-despite-its-older-SoC.875790.0.html
      - https://www.notebookcheck.net/Lenovo-Legion-Tab-Series.994031.0.html
      - https://www.aliexpress.com/w/wholesale-8.8-inch-2560x1600-144hz-lcd-panel.html
  6.
    - **Name:** Sharp LQ079L1SX01 7.9in 1536x2048 (QXGA) IPS with HDMI/Type-C-to-MIPI driver board (tablet panel kit)
    - **Size in:** 7.9
    - **H res:** 1536
    - **V res:** 2048
    - **Brightness nits:** 460
    - **Brightness evidence:** Datasheet-style listing, not a measurement: Wisecoco's 7.9in 1536x2048 MIPI panel (2 ch, 4 data lanes, 50-pin) lists '460 cd/m2 (Typ.)', 1000:1. That listing gives no part number; I infer it is the same Sharp-class panel the AliExpress LQ079L1SX01 kits use. Cheap boards may run the LEDs below typical current. Sun contrast about 2.4:1 (my estimate).
    - **Panel tech:** IPS LCD, dual-port MIPI
    - **Ppi:** 324
    - **Host interface:** HDMI (and Type-C DP) into an HDMI-to-dual-MIPI board. One kit advertises 90-degree rotation to 2048x1536.
    - **Touch to host:** No touch in any kit. Wisecoco says 'Touch Panel Available' without naming the interface.
    - **Optical bonding and coating:** Bare panel, no cover glass.
    - **Power w:** Not published. My estimate is 2-3 W at about 460 nits.
    - **Supply:** The panel needs 1.8 / +5.6 / -5.6 V (Wisecoco); the board generates these. Board input is not stated, typically 5 V USB-C.
    - **Dimensions weight:** 125.55 x 171.3 x 3.15 mm (Wisecoco)
    - **Operating temp:** -20 to 60 C (Wisecoco)
    - **Price:** AliExpress (18 Oct 2026): $34.45 (LQ079L1SX01 HDMI-to-MIPI kit, 7 sold), $36.62 (HDMI/Type-C kit with rotation, 26 sold), $49.14. Wisecoco panel + board $75.
    - **Availability:** AliExpress and Wisecoco.
    - **Ukraine availability:** prom.ua (MobiDance) lists LQ079L1SX01/SX02/SX04/SX06/SX09 panels at 1,571 UAH, 'ready to ship'. That is the panel only, no board.
    - **Q6a compatibility:** Good for video. It is 1536 px wide, so planes are never split. CVT-RB 1536x2048@60 is 214.25 MHz, 5.14 Gbps (my calculation). The board's EDID decides the actual timing, and touch must be added separately.
    - **Rf notes:** 214.25 MHz has no harmonic in any receive band up to 2.3 GHz (my calculation), if the board's EDID uses that timing.
    - **Community reports:** None specific to Linux or Radxa found.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.aliexpress.com/w/wholesale-7.9-inch-2048x1536-hdmi-driver-board.html
      - https://www.wisecocodisplay.com/product/7-9-inch-tft-lcd-display-1536x2048-portrait-type-lcd-panel/
      - https://prom.ua/search?search_term=LQ079L1SX01
  7.
    - **Name:** JDI LT070ME05000 7.0in 1200x1920 (Nexus 7 2013 panel) with HDMI-to-MIPI controller
    - **Size in:** 7
    - **H res:** 1200
    - **V res:** 1920
    - **Brightness nits:** 450
    - **Brightness evidence:** Distributor listing, seen only as a search snippet (aeri.com page returned 403): 450 cd/m2. Not measured. Sun contrast about 2.4:1 (my estimate).
    - **Panel tech:** IPS LCD, MIPI DSI
    - **Ppi:** 323
    - **Host interface:** HDMI through an HDMI-to-MIPI board. A search snippet says Digitalview's MIP-1000 lists LT070ME05000 as supported, with a possible 30 Hz HDMI input limit (page returned 503, unverified).
    - **Touch to host:** None (bare panel).
    - **Price:** Bare panel $23.75 on AliExpress (5 sold). Board price unknown.
    - **Availability:** Panel on AliExpress; matching board unverified.
    - **Ukraine availability:** Not checked separately; AliExpress ships.
    - **Q6a compatibility:** 1200 px wide, so planes are never split; 161 MHz (3.86 Gbps) is easy. Needs a board; no touch.
    - **Rf notes:** CVT-RB 161 MHz has its 14th harmonic at 2254 MHz; 58.4 Hz (156.75 MHz) is clean (my calculation).
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.aeri.com/pn/JDI/lt070me05000
      - https://digitalview.com/controllers/mip-1000-lcd-controller.html
      - https://www.aliexpress.com/w/wholesale-LT070ME05000-hdmi.html
  8.
    - **Name:** Wisecoco 7in AMOLED 1920x1080 90-165 Hz, on-cell touch ('High Bright 900 Nits' HDMI kit for Raspberry Pi)
    - **Size in:** 7
    - **H res:** 1920
    - **V res:** 1080
    - **Brightness nits:** 850
    - **Brightness evidence:** Listing figures only: Wisecoco page 'Brightness: 850 nits'; AliExpress title '900 Nits'. Neither says whether this is full-white or peak/HBM. On an OLED, full-white through a generic board is usually well below the peak. Sun contrast at most about 3.7:1 (my estimate).
    - **Panel tech:** AMOLED, MIPI 4-lane, 10-bit, on-cell touch
    - **Ppi:** 315
    - **Host interface:** HDMI (AliExpress kit 'For Raspberry Pi'). The Wisecoco page lists the bare panel with 'driver board integration' as an option.
    - **Touch to host:** The kit title says touch screen. Interface is unconfirmed; Wisecoco touch boards have shown up on the Pi forum as CH57x USB HID, but not for this model.
    - **Optical bonding and coating:** On-cell touch, so no separate touch layer or air gap.
    - **Operating temp:** -30 to 70 C (Wisecoco)
    - **Price:** $150 panel (Wisecoco); $234 kit (AliExpress, 21 sold, 18 Oct 2026).
    - **Availability:** AliExpress Wisecoco store and Wisecoco site.
    - **Ukraine availability:** Via AliExpress; no local stock found.
    - **Q6a compatibility:** 1080p60 is safe. Not above FHD.
    - **Rf notes:** CEA 148.5 MHz hits 742.5 and 2227.5 MHz. Use 1080p@52 Hz (128.7 MHz) only if the board accepts it.
    - **Community reports:** None. Burn-in risk with the static SDR++/SatDump UI, as with the Waveshare AMOLED.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.wisecocodisplay.com/product/7-inch-1920-1080-165hz-850nits-oled-amoled-display/
      - https://www.aliexpress.com/w/wholesale-wisecoco-7-inch-1920x1080-high-brightness-hdmi.html
  9.
    - **Name:** Wisecoco 8in foldable / flexible AMOLED 2480x1860 (foldable-phone-class panel) with driver board and integrated touch
    - **Size in:** 8
    - **H res:** 2480
    - **V res:** 1860
    - **Brightness nits:** 600
    - **Brightness evidence:** Listing figure: '600 Cd/m2' on the $350 kit page. The bare MIPI versions list 450 and 473 nits, '473 nit Peak Brightness'. Not measured; OLED full-white will be lower. Sun contrast about 2.5-2.9:1 (my estimate).
    - **Panel tech:** Flexible AMOLED, MIPI
    - **Ppi:** 388
    - **Host interface:** 'With Driver Board' and 'Compatible with Raspberry Pi PC', but the board's inputs are not stated (assume HDMI/Type-C).
    - **Touch to host:** 'Multi-point touch, integrated'; interface not stated.
    - **Dimensions weight:** Outline 165.68 x 137.91 (kit) / 165.89 x 126.12 mm (bare); active area 162.69 x 122.02 mm
    - **Price:** $350 kit; $180-209 bare MIPI panel (Wisecoco).
    - **Availability:** Wisecoco quote; no reviews.
    - **Ukraine availability:** None found.
    - **Q6a compatibility:** Poor. Landscape 2480 px is above the 2400 px DPU limit, so it needs virtual planes (msm.dpu_use_virtual_planes=1 on 6.18). CVT-RB 303 MHz / 7.27 Gbps landscape, or 309 MHz portrait (my calculation), is close to the practical ceiling. 4:3 aspect.
    - **Rf notes:** 303-309 MHz: no harmonics in the receive bands (my calculation).
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.wisecocodisplay.com/product/8-inch-flexible-amoled-display-2480x1860-ips-oled-bendable-ultrathin-screen/
      - https://www.wisecocodisplay.com/product/8-inch-foldable-oled-2480x1860-60hz-mipi-ultra-thin-flexible-amoled/
      - https://www.wisecocodisplay.com/product/custom-8-inch-2k-qhd-oled-screen-2480x1860-ultra-thin-amoled-display/
  10.
    - **Name:** Wisecoco 6in flexible AMOLED 2880x1440 with Type-C/HDMI driver board
    - **Size in:** 6
    - **H res:** 2880
    - **V res:** 1440
    - **Brightness nits:** 600
    - **Brightness evidence:** Listing figure: '600 cd/m2 (typical)' on Wisecoco's panel page, which is internally inconsistent (one table says 2560x1440). Not measured.
    - **Panel tech:** Flexible AMOLED, MIPI-DSI 4-lane, landscape-native
    - **Ppi:** 537
    - **Host interface:** HDMI / Type-C board (AliExpress kit)
    - **Touch to host:** Not stated.
    - **Dimensions weight:** 150.06 x 71.28 mm outline
    - **Operating temp:** -20 to 70 C
    - **Price:** $226.79 AliExpress kit (16 sold); $239 bare panel (Wisecoco).
    - **Availability:** AliExpress Wisecoco store.
    - **Ukraine availability:** Via AliExpress only.
    - **Q6a compatibility:** Poor. 2880 px wide needs DPU virtual planes; CVT-RB about 270 MHz (my calculation). The earlier audit's Pi forum thread shows this resolution booting in portrait. 18:9 at 6in is a cramped UI area.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.wisecocodisplay.com/product/6-inch-2k-flexible-oled-display-2880-1440/
      - https://www.aliexpress.com/w/wholesale-amoled-hdmi-touch-screen-6-inch.html
  11.
    - **Name:** Wisecoco 7.8in flexible AMOLED 1440x1920 with driver board
    - **Size in:** 7.8
    - **H res:** 1440
    - **V res:** 1920
    - **Brightness nits:** 300
    - **Brightness evidence:** Listing: '300cd/m2 (Typ.)'.
    - **Panel tech:** Flexible AMOLED, MIPI
    - **Ppi:** 308
    - **Host interface:** Listed as 'HDMI ; Micro usb' (Type-C board in the image alt text).
    - **Touch to host:** Not stated.
    - **Dimensions weight:** 166 x 129.5 mm outline
    - **Price:** $343 (Wisecoco)
    - **Availability:** Wisecoco quote.
    - **Q6a compatibility:** Fine for video (1440 wide, about 190 MHz), but far too dim.
    - **Rf notes:** CVT-RB 189.5 MHz hits 1705.5 and 2274 MHz (my calculation).
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.wisecocodisplay.com/product/7-8-inch-1920x1440-flexible-touch-display/
  12.
    - **Name:** Steam Deck OLED 7.4in 1280x800 HDR OLED
    - **Size in:** 7.4
    - **H res:** 1280
    - **V res:** 800
    - **Brightness nits:** 482
    - **Brightness evidence:** Independent measurement (Notebookcheck): 481.9 nits average, 485 max in desktop mode; 580 nits center in Game Mode with auto-brightness off. Valve advertises 600 SDR. No full-field HDR figure published.
    - **Panel tech:** OLED, 90 Hz, portrait-native 800x1280 (kernel quirk). Notebookcheck lists an ANX7530 bridge in the device.
    - **Ppi:** 204
    - **Host interface:** No third-party HDMI board found.
    - **Touch to host:** None available.
    - **Optical bonding and coating:** Optional anti-reflective etched glass. Notebookcheck says it 'can also be used in the sunshine'.
    - **Price:** n/a
    - **Availability:** No usable kit.
    - **Q6a compatibility:** Not applicable; below FHD.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.notebookcheck.net/Steam-Deck-1-TB-OLED-review-Minimalist-performance-maximum-gaming-fun.802764.0.html
  13.
    - **Name:** Samsung Galaxy Tab Active5 8in 1920x1200 rugged tablet panel
    - **Size in:** 8
    - **H res:** 1920
    - **V res:** 1200
    - **Brightness nits:** 600
    - **Brightness evidence:** Manufacturer spec, 600 nits, repeated by retailers and reviews. No lab measurement found. Trusted Reviews says it is 'fully legible' in spring sunlight.
    - **Panel tech:** TFT LCD
    - **Ppi:** 283
    - **Host interface:** No spare panel with an HDMI board found.
    - **Touch to host:** None available.
    - **Price:** n/a
    - **Availability:** No reuse kit.
    - **Q6a compatibility:** Not applicable.
    - **Verdict vs current pick:** unverifiable
    - **Sources:**
      - https://www.trustedreviews.com/reviews/samsung-galaxy-tab-active-5
      - https://mynexttablet.com/samsung-galaxy-tab-active5-review/
  14.
    - **Name:** Apple iPad mini panels: 6/7 (8.3in 2266x1488) and 2-5 (7.9in 2048x1536, LP079QX1)
    - **Size in:** 8.3
    - **H res:** 1488
    - **V res:** 2266
    - **Brightness nits:** 500
    - **Brightness evidence:** Apple's published spec for the mini 6/7, from prior knowledge; not re-fetched this session.
    - **Panel tech:** IPS LCD
    - **Ppi:** 327
    - **Host interface:** AliExpress searches on 18 Oct 2026 ('ipad mini 6 screen driver board hdmi', 'LP079QX1 hdmi', '7.9 inch 2048x1536 hdmi driver board') found no board for any iPad mini panel. Boards exist only for the 9.7in iPad 3/4/5/Air panels (LP097QX1/QX2), at $15.75-59.79, too large for this project. One 9.7in kit includes a digitizer ($55.69).
    - **Touch to host:** None available.
    - **Price:** n/a
    - **Availability:** No mini-size kit.
    - **Q6a compatibility:** Not applicable. A hypothetical 2266x1488@60 CVT-RB mode would be about 223 MHz (my calculation).
    - **Verdict vs current pick:** unverifiable
    - **Sources:**
      - https://www.aliexpress.com/w/wholesale-ipad-mini-6-screen-driver-board-hdmi.html
      - https://www.aliexpress.com/w/wholesale-LP079QX1-hdmi.html
      - https://www.aliexpress.com/w/wholesale-ipad-mini-lcd-hdmi-driver-board.html
- **Best above fhd:** No new consumer-reuse candidate is both above FHD and bright enough for direct sun.
  - The brightest above-FHD consumer panel measured is the AYANEO KUN 8.4in 1600x2560 (Notebookcheck: 678 nits average, 706 max), but it is not sold as a spare and has no HDMI board.
  - The only purchasable above-FHD reuse kit is the Sharp LQ079L1SX01 7.9in 1536x2048 HDMI-to-MIPI kit: $34-49 on AliExpress, 460 nits typical per the Wisecoco listing, no touch. Bare panels are on prom.ua at 1,571 UAH.
  - Close behind is the Legion Go 8.8in 1600x2560 assembly with digitizer ($44-80), but it is only 413 nits measured and needs an unverified generic eDP board and wiring work for touch.
  
  All of these sit at about 2.3-3.1:1 in sun, against about 7.3:1 at 2000 nits (my estimate). The earlier audit's Midas 7.02in 1200x1920 2500-nit panel therefore stays the only above-FHD panel that is bright in sun.
- **Best overall:** Keep the Wisecoco 7in 1920x1080 2000+ nit LTPS kit with HDMI board and capacitive touch.
  - Every consumer handheld or tablet panel reachable through third-party boards measures 287-706 nits full-screen: Notebookcheck measurements for Legion Go, Legion Go S, Legion Tab, OneXPlayer 2 Pro, AYANEO KUN and Steam Deck OLED; listing figures for the Wisecoco and AliExpress AMOLED and Sharp kits.
  - Phone and foldable AMOLED kits list only 300-900 nits, and those are peak or listing figures; high-brightness mode is not reachable through such boards.
  - None of the reuse kits found has documented USB-HID touch.
  - The best consumer AMOLED alternative, the Wisecoco 7in 1920x1080 AMOLED kit with touch ('850/900 nits', $150 panel / $234 kit), is still FHD, much dimmer than 2000 nits, and at risk of burn-in from the static SDR++/SatDump UI.
- **Notes:** Method:
  - 11 WebSearch calls.
  - WebFetch on primary pages: Notebookcheck reviews, Wisecoco product and search pages, AliExpress search-result pages (readable; individual item pages render empty), prom.ua search, and the Linux drm_panel_orientation_quirks.c source.
  
  Key facts:
  1. Consumer handheld and tablet panels top out at about 400-700 nits full-screen, measured in the original device. A third-party board can match that only if it drives the backlight fully.
     - eDP handheld panels usually have an integrated LED driver, so 100% PWM gets the OEM maximum.
     - MIPI tablet panels depend on the board's LED current, which is often below typical on cheap boards.
     - Phone and foldable AMOLED boards cannot reach high-brightness mode, and full-white is far below peak.
  2. Several handheld panels are portrait-native per the kernel quirk table: Legion Go 1600x2560, AYANEO KUN 1600x2560, GPD Win Mini 1080x1920, Steam Deck 800x1280. This suits the 2400 px DPU limit.
  3. No 7-8in 2.5K portable monitor exists in searches. The only 7-8in portable monitors found are 1280x800 or 1920x1080 at about 300-500 nits (Elecrow SH080T 300 nits; Wisecoco 7in portable monitors, one titled 500 nits; Waveshare 8in 1280x800, optically bonded).
  4. Legion Tab Gen 5 (3040x1904) needs 376-387 MHz (my calculation), which exceeds the Q6A's practical ceiling.
  
  Ukraine:
  - prom.ua lists LQ079L1SX0x 7.9in panels at 1,571 UAH, ready to ship.
  - No Legion Go or handheld screen assemblies were found on prom.ua; AliExpress remains the route.
  
  My own calculations (Python):
  - Pixel clocks: CVT-RB v1 approximation.
  - Sun contrast: 100 klx x 1% diffuse reflectance / pi, about 318 nits reflected.
  
  Unverified:
  - Legion Go eDP connector and pinout vs the generic 40-pin boards.
  - Digitalview MIP-1000 support for LT070ME05000 (from a search snippet; page returned 503).
  - Apple's 500-nit iPad mini spec (from prior knowledge).
- **Wisecoco 7in open questions resolved:** Not resolved.
  - An AliExpress search on 18 Oct 2026 for Wisecoco 7in 1920x1080 high-brightness HDMI listings found no Wisecoco-branded listing titled 2000 or 2500 nits. The Wisecoco 7in titles found were 500-nit 120 Hz units, 1080p portable monitors with USB-C/Type-C, and the 900-nit AMOLED.
  - One non-Wisecoco listing could be a second source for the same panel class: 'Sunlight Readable Display 7 Inch 1920x1080 2000 Nits High Brightness Wide Temperature LCD Display Outdoor Automotive Display', $156.03, 14 sold (https://www.aliexpress.us/item/3256805747391997.html). Its title mentions neither HDMI nor touch, and the item page could not be read.
  - No listing title mentions USB-HID touch, 12 V input or optical bonding.
  - So the open points from the audit remain: touch interface (USB HID vs I2C), board input voltage and current, EDID and orientation, and lamination. Get them in writing from the seller.

## dispmkt:sunlight_tech (run `wf_a429c611-ea2`)

- **Angle:** Sunlight readability per watt: transflective and reflective LCDs, optical bonding with AR/AG, circular polarizers versus polarized sunglasses, sun hoods, e-paper, and backlight overdrive. Concrete buyable 5-8 in HDMI + USB-touch products that use these techniques, with a quantified ambient-contrast model at 100 klx.
- **Candidates:**
  1.
    - **Name:** 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000 (7in IPS, optically bonded capacitive glass, HDMI + USB-C touch)
    - **Size in:** 7
    - **H res:** 1280
    - **V res:** 800
    - **Ppi:** 215.6
    - **Brightness nits:** 1000
    - **Brightness evidence:** 4D Systems 4DHDMI datasheet R1.0, model table and section 4.24: 1000 cd/m2 typical, 800:1 contrast, adjustable via OSD. The Ukrainian Prom.ua listing also says 1000 cd/m2. Not independently measured. The mechanical drawing shares one sheet with the 500-nit version: 36 LEDs, 6S6P, If 180 mA, Vf 18 V, which is about 3.2 W of backlight (my calculation).
    - **Host interface:** Mini-HDMI (HDMI 1.4). The panel is natively 800x1280 portrait (drawing: '7.0in 800*1280 TFT', driver IC JD9365). The board has an OSD and audio out, so it is probably a scaler board; this is my inference.
    - **Touch to host:** Goodix GT928 capacitive, delivered to the computer over the board's USB-C 'Power and Touch Interface'. The datasheet does not state the USB class; HID is likely but unconfirmed.
    - **Optical bonding and coating:** Datasheet: 'Capacitive Touch, Glass 1:1 size of LCD. Optical Bonded to LCD.' G+F+F stack, 1.1 mm cover glass, transmittance at least 85%. 'As a standard option, the displays do not have any Cover Glass Treatments'. AR, AG and AF are a custom order. Planar's numbers put a bonded plain-glass front at about 4.4%. Adding a 0.7% AR film should bring it to about 1.2% (my calculation).
    - **Power w:** Datasheet: 12 V barrel jack 540 mA typical (about 6.5 W), or 5 V USB-C 1300 mA typical (about 6.5 W). RS lists 790 mA, which conflicts. About 154 nits per watt (my calculation).
    - **Supply:** 12 V DC, 5.5 mm barrel jack, centre positive. It runs straight from the existing 12 V rail with no extra buck. 5 V via USB-C is the alternative, but a Q6A USB port is not enough.
    - **Dimensions weight:** Outline about 100.2 x 164.7 mm (BL/CTP outer dimension), total thickness 15.98 mm including the board, from the datasheet drawing. Weight not stated.
    - **Operating temp:** -20 to +70 C operating, -30 to +80 C storage (datasheet)
    - **Price:** 9,520 UAH (about $229 at 41.5 UAH/USD) from neostore.in.ua on Prom.ua. No international price was verified; RS UK showed it temporarily out of stock (search snippet).
    - **Availability:** In stock in Ukraine: Prom.ua seller neostore.in.ua, 12-month warranty, Nova Poshta delivery, cash on delivery.
    - **Ukraine availability:** Yes, in stock at 9,520 UAH (neostore.in.ua via Prom.ua, checked 18 Oct 2026).
    - **Q6a compatibility:** Good. 1280 or 800 px wide is far below the sc7280 2400 px SSPP limit. A 1280x800@60 mode is about 71-84 MHz, which is about 1.7-2.0 Gbps of the 8.64 Gbps 2-lane HBR2 budget (my calculation). The EDID is unknown, so check edid-decode for portrait-only or landscape modes and confirm VBP+VSW+VFP is at least 24 lines. Power it from the 12 V rail. Pass only the USB data lines to the Q6A if the board back-feeds VBUS. Brightness is changed through the OSD from an optional button board; auto-dimming means emulating the buttons from GPIO/RP2040, or asking 4D for the DDC/CI firmware the datasheet says 'may be implemented'.
    - **Rf notes:** No EMI data. The board carries a scaler and an LED boost converter. If the EDID uses CVT-RB 71.0 MHz, the 2nd harmonic lands at 142 MHz (2 MHz below 2 m) and the 24th at 1704 MHz, inside 1690-1710 (my calculation). A custom EDID with a pixel clock of 77.8-80.4 MHz (e.g. 79.0 MHz) avoids every band except S-band, which it reaches only at harmonic 28 and above (my calculation). Shield the boost converter and filter the 12 V feed.
    - **Community reports:** None found in this pass. This is a new product line: datasheet drawings are dated Dec 2024 and datasheet R1.2 is dated 2026.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_0.pdf
      - https://prom.ua/ua/p3231815115-komplektuyuschie-dlya-matrits.html
      - https://uk.rs-online.com/web/p/lcd-colour-displays/0721600
  2.
    - **Name:** 4D Systems 4DHDMI-80-1280-800-CT-EAR-1000 (8in IPS, optically bonded capacitive glass, HDMI + USB-C touch)
    - **Size in:** 8
    - **H res:** 1280
    - **V res:** 800
    - **Ppi:** 188.7
    - **Brightness nits:** 1000
    - **Brightness evidence:** 4D Systems datasheet R1.0, section 4.28: 1000 cd/m2 typical, adjustable via OSD; the Prom.ua listing says the same. The drawing shows 42 LEDs, 6S7P, If 210 mA, Vf 18 V, about 3.8 W of backlight (my calculation). Not independently measured.
    - **Host interface:** Mini-HDMI (HDMI 1.4). The panel is natively 800x1280 portrait with a JD9365 driver, the same driver family as Radxa's Display 8 HD (jadard-jd9365da).
    - **Touch to host:** Goodix GT928 over the board's USB-C power-and-touch port. USB class not stated (HID likely).
    - **Optical bonding and coating:** Datasheet: 'Optical Bonded to LCD', 1.1 mm cover glass. No AR/AG as standard; available as a custom order.
    - **Power w:** Datasheet: 12 V 580 mA typical (about 7 W), or 5 V 1500 mA typical. About 144 nits per watt (my calculation).
    - **Supply:** 12 V barrel jack (5.5 mm) or 5 V USB-C
    - **Dimensions weight:** About 122.6 x 198.6 mm outline, 15.98 mm total thickness (datasheet drawing). Weight not stated.
    - **Operating temp:** -20 to +70 C (datasheet)
    - **Price:** 10,060 UAH (about $242) from neostore.in.ua on Prom.ua
    - **Availability:** In stock in Ukraine (Prom.ua, neostore.in.ua)
    - **Ukraine availability:** Yes, in stock at 10,060 UAH
    - **Q6a compatibility:** Good. Same notes as the 7in 1280x800 model: low pixel clock, 1280 px or less wide, 12 V input, check the EDID and the 24-line vertical blanking requirement.
    - **Rf notes:** Same as the 7in model. Pick an EDID pixel clock of 77.8-80.4 MHz to keep harmonics out of the 137-1710 MHz bands (my calculation).
    - **Community reports:** None found.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_0.pdf
      - https://prom.ua/ua/m-4515543037690202415-displej-tft-systems.html
  3.
    - **Name:** 4D Systems 4DHDMI-70-1024-600-CT-EAR-1000 (7in IPS BOE panel, optically bonded, lowest-power 1000-nit option)
    - **Size in:** 7
    - **H res:** 1024
    - **V res:** 600
    - **Ppi:** 169.5
    - **Brightness nits:** 1000
    - **Brightness evidence:** 4D datasheet R1.0, section 4.20: 1000 cd/m2 typical, 800:1 contrast. The drawing shows the 1000-nit backlight at Vf 19.2 V and If 180 mA (about 3.5 W), against 9.3 V and 180 mA for the 500-nit version. Prom.ua (Zirka) listing title says 1000 cd/m2.
    - **Host interface:** Mini-HDMI (HDMI 1.4). BOE 7.0in panel with a JD9165A-A3 driver.
    - **Touch to host:** GT1151QM capacitive over one of two USB-C '5V power and USB touch' ports. USB class not stated.
    - **Optical bonding and coating:** Datasheet: 'Optical Bonded to LCD', 1.1 mm cover glass plus ITO film. No AR/AG as standard.
    - **Power w:** Datasheet: 5 V 790 mA typical, about 4.0 W total, or about 253 nits per watt (my calculation). This is the best nits per watt among the plug-and-play modules found.
    - **Supply:** 5 V USB-C only (no barrel jack listed). Needs its own 5 V buck of 1 A or more.
    - **Dimensions weight:** About 165 x 100 mm outline, about 13 mm total thickness (read from the low-resolution datasheet drawing, approximate). Weight not stated.
    - **Operating temp:** -20 to +70 C (datasheet)
    - **Price:** 8,140 UAH (about $196) from neostore.in.ua; 10,227 UAH at Zirka (unavailable)
    - **Availability:** Prom.ua: neostore.in.ua in stock; Zirka out of stock
    - **Ukraine availability:** Yes (neostore.in.ua via Prom.ua)
    - **Q6a compatibility:** Good, with the Radxa FAQ fix video=HDMI-A-1:1024x600@60 if the EDID default is wrong. Brightness is a push button on the PCBA that steps through levels (no OSD), so auto-dimming means wiring a GPIO to the button.
    - **Rf notes:** Unknown EDID clock. A 1024x600@60 timing at 51.9-52.7 MHz is clean in every band except high-order (43rd and above) S-band harmonics (my calculation).
    - **Community reports:** None found.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_0.pdf
      - https://prom.ua/ua/search?search_term=%D0%B4%D0%B8%D1%81%D0%BF%D0%BB%D0%B5%D0%B9%207%20hdmi%201000%20nit
  4.
    - **Name:** Newhaven NHD-7.0-HDMI-HR-RSXP-CTU (7in IPS 940-nit HDMI module, USB-HID PCAP)
    - **Size in:** 7
    - **H res:** 1024
    - **V res:** 600
    - **Ppi:** 169.5
    - **Brightness nits:** 940
    - **Brightness evidence:** Newhaven product page and datasheet: 'Normally Black, Transmissive, 940cd/m2', marketed as 'IPS, Sunlight Readable'. Vendor figure, not independently measured.
    - **Host interface:** HDMI through a TI TFP401A DVI/HDMI receiver. There is no scaler, so the host must send the native timing. The datasheet EDID DTD is 1024x600, 62.00 MHz, htotal 1344, vtotal 635 = 72.6 Hz, vertical blanking 35 lines (VFP 12 / VSW 10 / VBP 13), all decoded by me from the EDID array.
    - **Touch to host:** FT5426G PCAP; the datasheet table says 'PCAP (USB-HID)'. It works with hid-multitouch without a driver.
    - **Optical bonding and coating:** Cover glass is included. Optical bonding and AR/AG are not stated, so assume air-gap or plain glass until confirmed.
    - **Power w:** Datasheet: VDD 5.0-7.0 V. At 5 V, 1.2 A typical and 1.5 A max (6-7.5 W). At 7 V, 0.9 A typical (about 6.3 W). About 157 nits per watt (my calculation).
    - **Supply:** 5-7 V DC; needs its own buck converter
    - **Dimensions weight:** 189.68 x 106.7 x 27.8 mm including a steel mounting bracket. Weight not stated.
    - **Operating temp:** -20 to +70 C operating, -30 to +80 C storage
    - **Price:** $120.20 (Newhaven web store)
    - **Availability:** Product page shows 'IN STOCK' with a low-stock notice; one search snippet called the listing retired. Ships from the US. Shipping to Ukraine not checked.
    - **Ukraine availability:** Not found locally; import only
    - **Q6a compatibility:** Good. The 35-line vertical blanking meets the sc7280 DP requirement of 24 lines or more. 62 MHz is trivial for the link. The TFP401A has no scaler, so keep exactly 1024x600. The Radxa FAQ video=HDMI-A-1:1024x600@60 fix applies. The EDID asks for 72.6 Hz, and a 60 Hz custom EDID should also work but is unverified.
    - **Rf notes:** The vendor states an 'upgraded EMI-shielded FPC'. With the stock EDID at 62.00 MHz, the 12th harmonic is 744.0 MHz (inside the 739-750 MHz QO-100 IF) and the 7th is 434.0 MHz (1 MHz below 435). A replacement EDID at 52.0 MHz (htotal 1344 x vtotal 645 = 60.0 Hz) is clean except S-band orders 43 and above (my calculation).
    - **Community reports:** Two reviews on the vendor page, both about support, not sunlight performance.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.newhavendisplay.com/nhd70hdmihrrsxpctu-p-9649.html
      - https://newhavendisplay.com/content/specs/NHD-7.0-HDMI-HR-RSXP-CTU.pdf
  5.
    - **Name:** CarTFT CTFHD840-SH (8.4in transflective HDMI monitor, USB touchscreen)
    - **Size in:** 8.4
    - **H res:** 800
    - **V res:** 600
    - **Ppi:** 119
    - **Brightness nits:** 450
    - **Brightness evidence:** CarTFT product page: 450 cd/m2 with a transflective panel; a 1000-nit 'Ultra' version is available on request. The page gives no reflectance figure, so the transflective claim is vendor marketing.
    - **Host interface:** HDMI (accepts 640x480 up to 1600x1024 and scales to 800x600)
    - **Touch to host:** USB touchscreen; the technology (resistive or capacitive) is not stated
    - **Optical bonding and coating:** Anti-glare surface and AR coating are stated; bonding is not mentioned
    - **Power w:** Max 10 W
    - **Supply:** 12 V DC (12/24 V for project customers)
    - **Dimensions weight:** Case 232 x 162 x 36 mm; weight not stated
    - **Operating temp:** -30 to +85 C
    - **Price:** EUR 729 including 19% VAT, plus shipping
    - **Availability:** In stock (27 pcs) at cartft.com (Germany)
    - **Ukraine availability:** Not checked; EU shipping only
    - **Q6a compatibility:** Works as an HDMI and USB touch monitor through its scaler, but it is far below the resolution and quality the user asked for.
    - **Rf notes:** Unknown. A scaled 800x600 mode allows any clean input clock.
    - **Community reports:** None found.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://cartft.com/catalog/il/2008
  6.
    - **Name:** CarTFT CTFHD800-WMS (8in 'transflective' 1000-nit HDMI open-frame, USB touch)
    - **Size in:** 8
    - **H res:** 1024
    - **V res:** 600
    - **Ppi:** 148.4
    - **Brightness nits:** 1000
    - **Brightness evidence:** CarTFT page: 1000 nits, 300:1 contrast, 104% NTSC. The page's 'dot resolution 2400x480' contradicts its stated 1024x600 physical resolution, so the panel may really be 800x480. A transflective panel with 104% NTSC is unusual. Treat both claims as unverified.
    - **Host interface:** HDMI plus 2x composite
    - **Touch to host:** USB touchscreen (technology not stated); RS232 option
    - **Optical bonding and coating:** AG touch surface with AR coating; bonding not mentioned
    - **Power w:** Max 10 W
    - **Supply:** 9-36 V DC (works directly from a 4S pack)
    - **Dimensions weight:** 195.4 x 119.5 x 32.6 mm; weight not stated
    - **Operating temp:** -30 to +85 C
    - **Price:** EUR 529 including 19% VAT
    - **Availability:** On request, 6 weeks
    - **Ukraine availability:** Not checked
    - **Q6a compatibility:** HDMI and USB touch through a scaler; low resolution
    - **Rf notes:** Unknown
    - **Community reports:** None found.
    - **Verdict vs current pick:** worse
    - **Sources:**
      - https://www.cartft.com/catalog/il/2021
- **Best above fhd:** This angle turned up no new above-FHD candidate. I found no transflective, reflective, bonded-AR or other sun-optimized 5-8 in module above FHD that has HDMI and USB touch. Small transflective parts are WVGA to 1024x600 class: Ortustech COM70H7M24ULC 800x480, and CarTFT's 800x600 and 1024x600 units. Reflective LCD (RLCD) HDMI monitors exist only at 24-32 in (Eazeye 24in, SDC 32in), or as 4.2in SPI modules (Waveshare RLCD). The best above-FHD option is still the already-evaluated Midas MDT0700F1IHHC (7.02in 1200x1920, 2500 nits). It has an AR cover lens and in-cell touch, so it has no air gap and is the only bright above-FHD panel with low reflectance. It still needs custom drive electronics and has no timing table.
- **Best overall:** Keep the Wisecoco 7in 2000-nit FHD only if the seller confirms in writing, with a photo, that the touch glass is optically bonded. Then add an AR film of about 0.7% and a hood with a matte-black interior. If it is air-gapped or the seller cannot answer, buy the 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000 instead: datasheet-confirmed optical bonding, 1000 nits, 12 V input, USB touch, in stock in Ukraine at 9,520 UAH. Use it with the same AR film and hood. The 4DHDMI-70-1024-600-CT-EAR-1000 (about 4 W, bonded) is the per-watt budget variant. My calculation at 100 klx: Wisecoco 2000 nits gives 1.5:1 air-gapped, 2.4:1 bonded with plain glass, and 6.2:1 bonded with AR film. The 4D at 1000 nits gives 1.7:1 bonded with plain glass and 3.6:1 bonded with AR film. In a hood (about 20 klx on the screen) the 4D with AR film reaches about 14:1. So bonding, AR and shading are worth more than another 1000 nits.
- **Wisecoco 7in open questions resolved:** Not resolved. I re-read the product page on 18 Oct 2026. It still shows:
  - $132 (was $135), 'Capacitive touch', and a field 'Interface Type: I2C'.
  - 2000+ cd/m2 typical in the table against 2500 in the title.
  - 1000:1 contrast and LTPS, MIPI 4-lane panel.
  - Conflicting active-area figures and 0 reviews.
  - No input voltage, power, driver chip, bonding or AR/AG statement.
  
  New point from this angle: whether the touch glass is optically bonded matters more than any of the open questions. At 100 klx, 2000 nits gives 1.5:1 with an air gap and no AR, 2.4:1 bonded with plain glass, 6.2:1 bonded with a 0.7% AR film, and 9.9:1 with factory bonding plus AR (my calculation, using Planar's reflectance values). An air-gapped 2000-nit Wisecoco is no better in direct sun than a bonded 1000-nit module.
  
  Add these to the seller questions:
  1. 'Is the CTP optically bonded (OCA/OCR) or air-gap/frame-taped?'
  2. 'Is the cover glass AR- or AG-treated?'
  3. 'What is the polarizer transmission axis angle?' This decides the polarized-sunglasses behaviour.
  
  Check it yourself on arrival: at a grazing angle, a pen tip on the glass shows a doubled reflection if there is an air gap.
- **Notes:** METHOD
  - I used 11 WebSearch calls plus WebFetch on primary pages and datasheets.
  - PDFs were parsed locally: 4D Systems 4DHDMI datasheet R1.0, Newhaven datasheet, Planar white paper.
  - Every number marked 'calc' is my own Python calculation.
  
  1) AMBIENT CONTRAST MODEL (calc)
  Formula: ACR = (L + R*E/pi) / (L/1000 + R*E/pi). Native contrast is 1000:1, and R*E/pi is the worst case where the screen mirrors a sunlit, near-white scene.
  
  Reflectance values from Planar's optical-bonding primer:
  - air gap, no AR: 3.9% + 4.4% + 4.4% = 12.7%; at 10,000 fc this gives 4251 nits of glare;
  - bonded + AR: 0.2% + 0.5% = 0.7%, which gives 239 nits of glare;
  - Planar's rule of thumb is that legibility needs at least 7:1, and it says the air-gap case would need about 26,000 nits.
  Values I derived from Planar's per-interface numbers (calc): bonded with a plain glass front is about 4.4%; air gap with AR only on the outer face is about 9%. That matches a patent's finding that a single AR film cuts reflection to only about 2/3.
  
  ACR at 100 klx (E/pi = 31,831 cd/m2) for 1000 / 2000 / 3000 nits:
  - bonded + AR 0.7%: 5.5 / 9.9 / 14.3
  - bonded + AR film (~1.2%): 3.6 / 6.2 / 8.8
  - bonded, plain glass (4.4%): 1.7 / 2.4 / 3.1
  - air gap + AR outer face (9%): 1.3 / 1.7 / 2.0
  - air gap, no AR (12.7%): 1.2 / 1.5 / 1.7
  
  Nits needed for 5:1 at 100 klx: 896 (0.7%), 1536 (1.2%), 5630 (4.4%), 16,251 (12.7%).
  So going from air gap to bonded + AR is worth about 18x the backlight luminance, and from bonded plain glass to AR about 6x. A 0.7% AR retrofit film exists: TELESIN advertises 0.7% against 4-5% for standard protectors (vendor claim).
  
  Real-world caveat: most of the 4% glass reflection is specular. Its luminance is R x (luminance of whatever the screen mirrors):
  - a sunlit white shirt is about 25,000 cd/m2 (calc, 0.8 x E/pi), which gives about 1000 nits of glare at 4%;
  - a matte-black hood interior or dark clothing cuts this by an order of magnitude.
  
  2) SUN HOOD
  Wikipedia lists direct sun at 32-100 klx against 10-25 klx for 'full daylight, not direct sun'. Shading the screen face therefore cuts E by about 4-10x (calc).
  
  At 20 klx, ACR for 1000 nits: 22.9 with bonded + AR, 13.9 with AR film, 4.6 with bonded plain glass, 2.2 with an air gap.
  
  A 25-35 mm hood, lined matte black, tilted so the screen mirrors the hood interior and not the sky or your chest, is the cheapest and largest single gain, and it costs 0 W.
  
  3) TRANSFLECTIVE AND REFLECTIVE
  In reflective mode the reflected luminance scales with the sun, so ACR is independent of E. My model (calc, assumed values): reflectance 10-30% with an intrinsic reflective contrast of 15-20 gives an ACR of about 9-15 with an AR front, but only about 3-6 with a 4.5% glass front. Colour and resolution are poor.
  
  Market status, October 2026:
  - Ortustech/Toppan Blanview: COM70H7M24ULC is 7in 800x480 transflective, 400 nits, LVDS, -30 to 85 C (eeNews 2019). Toppan Display Solutions is ending LCD production (Embedded Computing Design, 3 Aug 2026, seen as a search snippet; the page returned 403). Not a viable new design.
  - CarTFT 7in CTFHD400-SH, transflective HDMI with USB touch: 'currently not available'.
  - Kyocera: I found only a 2012 note on 'Inner Touch' glass-glass bonding that reduces reflections (2.16 W backlight). I verified no current Kyocera 5-8 in transflective part with an HDMI board.
  - Sharp and JDI reflective (memory-in-pixel) panels: no 5-8 in HDMI product found. Pixel Qi is defunct (my own knowledge).
  - RLCD HDMI monitors: Eazeye 24in FHD about 4 W average for about $999, and SDC 32in at $1549. Both are far too large.
  Conclusion: transflective gives the best physics per watt, but no buyable 5-8 in part is anywhere near 'high quality'.
  
  4) POLARIZERS AND SUNGLASSES
  - LCD output is linearly polarized, so polarized sunglasses pass cos^2 of the angle between the axes: 0-100% depending on orientation.
  - Laminating a quarter-wave retarder on top of the LCD's front polarizer makes the output circular, so about 50% passes at any rotation (calc). Relec and Digiwise sell TFTs with this film; I found no verified DIY sheet vendor.
  - The circular polarizer on AMOLED is a different thing: an anti-reflection device. AMOLED HDMI kits are only about 310 nits, so they are not useful here.
  - Sunglasses do not change the screen's ACR. They cut some s-polarized glare at oblique angles and ease eye adaptation.
  - Practical fix: before fixing the panel in the case, find the orientation where the axis is near vertical, or ask the seller for the polarizer axis.
  
  5) E-PAPER (not for waterfalls)
  Waveshare 7.8in (1872x1404) data:
  - 450 ms full refresh, 2-16 grey levels, 0-50 C operating;
  - colour cast when refreshing cold; ghosting builds up after repeated partial refreshes and needs full refreshes;
  - 1.2 W during refresh.
  A scrolling 10-30 line/s waterfall needs continuous partial updates, so it smears, ghosts, has no colour map and slows further in the cold. Only usable for a static pass-schedule or status pane.
  
  6) OVERDRIVING THE BACKLIGHT
  Datasheet data points:
  - Midas: luminance is linear at 200-500 mA (1000-2500 nits), but the 2500-nit point is footnoted 'stable at room temperature, open air';
  - 4D 7in 1024x600: the 1000-nit version uses twice the series LEDs (Vf 19.2 V) at the same 180 mA, rather than overdriving.
  Safe practice:
  - stay at or below the panel datasheet's LED current;
  - use DC/analog dimming at 20-25 kHz, not burst PWM, for RF;
  - derate on an NTC (50% above 60 C);
  - remember sun adds about 13 W to a 7in face (from the earlier audit), so overdrive and solar load add up toward the LC clearing point;
  - expect diminishing returns from LED droop.
  Reflectance reduction is the cheaper 'nits'.
  
  7) BEST SUN-READABILITY PER WATT (conclusion)
  In order of value:
  1. Matte-black hood: 0 W, about 5x effective.
  2. Optically bonded touch glass: no power cost, about 3x over an air gap.
  3. AR front surface (film or treated glass): about 4x over bonded plain glass.
  4. A 1000-1500 nit backlight, run at about 30-50% via a lux sensor most of the time, with a time-limited, temperature-derated boost to full when the sun is behind you.
  
  Example: 4D 7in bonded with AR film in a hood is about 14:1 at about 6.5 W (datasheet total). A 2000-nit air-gapped panel unhooded is about 1.5:1 at about 7 W.
  
  Nits per watt from datasheet totals (calc): 4D 7in 1024x600 253, Newhaven 157, 4D 7in 1280x800 154, 4D 8in 144. Wisecoco is estimated at about 286, unverified.
  
  OTHER FINDS, NOT VIABLE
  - Litemax EUD0705-TIB-Q11: 7in 1280x800, '1000' or '1600' nits (the page contradicts itself), HDMI, no touch, out of stock, NT$12,458.
  - Waveshare 7in/8in 1280x800 optically bonded HDMI: about 350 nits.
  
  KEY SOURCES
  - https://www.planar.com/media/98794/planar-optical-bonding-achieving-greater-legibility.pdf
  - https://en.wikipedia.org/wiki/Lux
  - https://www.telesinstore.com/products/anti-reflection-screen-protector-for-pocket-3
  - https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9557448
  - https://www.epdtonthenet.net/article/177664/Polarised-sunglasses-friendly-TFT-solutions-from-Relec.aspx (403; search snippet)
  - https://www.waveshare.com/wiki/7.8inch_e-Paper_HAT
  - https://www.eenewseurope.com/en/robust-sunlight-readable-7-inch-tft-blanview-display/
  - https://embeddedcomputing.com/application/industrial/industrial-computing/data-modul-supports-customers-as-toppan-display-solutions-ends-industrial-lcd-display-production (403; snippet)
  - https://www.eenewseurope.com/en/7-tft-display-with-optimized-readability-for-difficult-lighting-conditions/
  - https://cartft.com/catalog/il/2629
  - https://itc.ua/en/news/e-ink-alternative-this-1000-lcd-uses-ambient-light-and-consumes-up-to-7-watts
  - https://www.e-ink-info.com/sdc-32-inch-color-rlcd-monitor
  - https://docs.waveshare.com/ESP32-Peripheral-Tutorials/Display/RLCD
  - https://eshop.litemax.com/product/1
  - https://www.farnell.com/datasheets/3984938.pdf
  
  Scratch calculations are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/acr2.py and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/harm.py.

## dispmkt:check1 (run `wf_a429c611-ea2`)

- **Name:** Youritech ET070WU01-HLT (7.02in 1200x1920 MIPI, in-cell touch, "2000 nits"); Microtech MTF070UG53A-V1 has the same outline
- **Exists and orderable:** ні
- **Confirmed specs:** Youritech product page (images uploaded 2026/06), with only "Get a quote" as a way to order. It lists: ET070WU01-HLT, 7in, 1200x1920, MIPI, transmissive, outline 105.46x162.82 mm, active area 94.5x151.2 mm, viewing angle 80/80/80/80, "2000 cd/m2 (Typ.)", operating -20 to 70 C (storage -30 to 80 C), touch "yes (In-Cell)". The page does not list a driver IC, MIPI lane count, touch controller, backlight figures, contrast, datasheet, price or MOQ.
  
  The Microtech MTF070UG53A-V1 HKTDC listing has the title "7 inch LCD screen 1920*1200 ... 2000 high brightness 40pin display panel with MIPI interface". Its table gives outline 105.46x162.82x2.4 mm, active area 94.5x151.2 mm, pitch 0.07875 mm, 8-bit, "Without TP", LED white backlight and a 25-45 day lead time. Brightness is missing from the table.
  
  Calculated: 7.02in diagonal, 323 PPI.
  
  The same active area, pitch and pin count appear in the Midas MDT0700F1IHHC-MIPI datasheet (a different product). It specifies ADS 8-bit+FRC, in-cell FocalTech FT7250 TDDI with touch on I2C (TP_SCL/SDA/INT at 1.8 V), a 40-way 0.5 mm FFC, IOVCC 1.8 V, VSP/VSN +/-5.5 V, CR >=1200, and a cover lens with AR. Its backlight table gives Vf 16 V typ (19.2 V max at 240 mA) and If 200/300/400/500 mA for 1000/1500/2000/2500 nits, with "thermal considerations apply" at 2500. This is probably the same upstream glass as the Youritech and Microtech parts, but that is an inference.
- **Refuted or doubtful:**
  - The 2000 nits figure is only a vendor web-page 'Typ.' value (Youritech) and a listing-title phrase (Microtech). No datasheet or independent measurement exists for either part number. Web searches for both part numbers return nothing.
  - Youritech's catalog is unreliable. Its 1200x1920 listing uses the part number ET070WU01-TT for two different products: a 350-nit, 115x176 mm in-cell panel and a '1300nits IPS' panel.
  - The two vendors' parts are 'identical' only in outline and active area. Youritech lists in-cell touch; Microtech lists 'Without TP'.
  - No HDMI board exists for this model. The only Youritech product with an HDMI driver board is a 4in 720x720 module. The generic 'controller board integration' text is a service offer, not a product.
  - Touch cannot reach the host as USB HID as sold. An in-cell TDDI (FT7250 on the same-glass Midas part) reports over I2C/SPI, and TDDI touch sensing runs in the display blanking intervals (the OVT TD4160 brief, for example, says '120/60 Hz long H-blank'). A custom MCU bridge is needed, and so is the vendor's touch protocol and firmware. Off-spec refresh rates chosen for RF reasons may break touch.
  - The candidate's RF claim ('60 Hz ~150 MHz hits 748.8/2246 MHz') rests on an assumed htotal. With JDI-like htotal 1340 and 24-line vblank (156.30 MHz) no harmonic falls in a band. With JDI's exact 14-line timing (155.49 MHz) the 11th harmonic is 1710.4 MHz, on the band edge. With CVT-RBv2-like 1280x1944 (149.3 MHz) the 5th harmonic lands at 746.5 MHz. The real EDID is unknown.
  - The native DSI timing of this glass class (JDI LT070ME05000 in mainline Linux) has only 14 lines of vertical blanking, below the Q6A DP minimum of 24. Whether the panel and the touch accept a longer VFP is unverified.
  - Not orderable off the shelf: request-for-quote only, no price, MOQ unknown, Microtech lead time 25-45 days. Not sold in Ukraine: prom.ua finds nothing for ET070WU01. It does carry low-brightness JDI 7in 1920x1200 31-pin MIPI replacement panels, which are a different part.
- **Touch reaches host as usb hid:** no
- **Q6a mode line and link check:** This is a bare MIPI panel, so it needs a 4-lane HDMI-to-MIPI bridge (LT6911C/UXC class) flashed with this panel's init code and timing. No such bridge is offered for this model, and the EDID will come from the bridge firmware.
  
  Reference timing (mainline panel-jdi-lt070me05000.c, same 94.5x151.2 mm format, not confirmed for this part): 1200+48+32+60 = 1340 htotal, 1920+3+5+6 = 1934 vtotal, 155.493 MHz at 60 Hz, 4 lanes, video mode.
  
  Calculated mode that meets the 24-line rule: 1340x1944 at 60 Hz = 156.30 MHz. At 24 bpp that is 3.75 Gbps, 43% of HBR2 x2 (8.64 Gbps) and 87% of HBR x2. That is far below the ~330 MHz ceiling and within RA620 HDMI limits.
  
  Width is 1200 px, under the 2400 px DPU limit, so virtual planes are not needed. The panel is portrait-native, so landscape means rotating in the compositor (GPU).
  
  Risks: the panel's tolerance for VFP >= 10 lines and for refresh rates below 55 Hz is unknown, and TDDI touch timing depends on the display timing.
  
  Calculated RF-clean option: 1340x1944 at 49.2-49.5 Hz (128.2-129.0 MHz), with at least 7 MHz harmonic margin. It may be outside the panel and touch spec.
- **Power and thermal:** All figures below are calculated. Backlight values come from the same-glass Midas datasheet, not from this part.
  
  - Backlight: 2000 nits = 400 mA x 16 V = 6.4 W of LED power, up to about 7.7 W if Vf approaches the 19.2 V maximum. With 85-90% boost efficiency that is about 7.1-9 W from the 12 V rail.
  - Logic: up to about 0.9 W (Midas maximum IDD: IOVCC 50 mA, VSP/VSN 75 mA each).
  - Bridge board: plus about 1 W.
  - Display total: about 8-10 W, roughly 0.6-0.7 A from a 4S pack. A UEDX6911-class board (about 1.3 W) cannot drive this backlight, so an external constant-current LED driver is needed.
  - Sun load: 1000 W/m2 on the 172 cm2 front is about 17 W, most of it absorbed, on top of 6-8 W of backlight. In a sealed handheld this can push the panel past its 70 C operating limit; the LC then clears and the screen goes black. Midas adds a thermal caveat even at 2500 nits in open air.
  - Mitigations: ambient-light and temperature-based dimming, a rear heat spreader with venting, and shielding of the boost converter.
- **Keep:** ні
- **Reason:** It does not survive checking. The 2000-nit figure is a vendor web-page claim only, with no datasheet, no measurement, and a catalog that reuses one part number for two products. It is a bare MIPI panel with no HDMI board offered for this model. Its in-cell TDDI touch is I2C/SPI, tied to display timing, and has no USB HID path. Its native timing class has 14-line vblank, below the 24 the Q6A needs, and the RF picture depends on an unknown EDID. The backlight needs about 7-9 W plus a separate LED driver. It is request-for-quote only, price unknown, and not sold in Ukraine. To build a 7in 1200x1920 2000-nit panel from parts, the Midas MDT0700F1IHHC-MIPI is the better-documented sibling: it has a real datasheet with a current-vs-luminance table, the FT7250 touch controller, and an AR cover lens. A search snippet put it at about EUR 324 ex VAT with a 12-week lead time on Farnell; the page itself returned 503 to me. It still needs an HDMI-to-MIPI bridge and an I2C-to-USB-HID bridge.
- **Sources:**
  - https://www.youritech.com/products/7-inch-tft-lcd-display-1200x1920-high-brightness-2000nits-mipi-lcd-display-with-in-cell-touch.html
  - https://www.youritech.com/resolution/1200x1920/
  - https://www.hktdc.com/event/electronicasia/en/product/1Z03HV3K9
  - https://www.hktdc.com/event/electronicasia/en/product/1Z03H5SXH
  - https://www.farnell.com/datasheets/3984938.pdf
  - https://export.farnell.com/midas-displays/mdt0700f1ihhc-mipi/lcd-tft-display-7-1200x1920p-mipi/dp/4248109
  - https://raw.githubusercontent.com/torvalds/linux/master/drivers/gpu/drm/panel/panel-jdi-lt070me05000.c
  - https://www.ovt.com/wp-content/uploads/2024/01/TD4160-PB-v1.0-WEB.pdf
  - https://prom.ua/ua/search?search_term=ET070WU01
- **Questions for seller:**
  - Please send the full specification or approval sheet for ET070WU01-HLT, including luminance measurement conditions, minimum luminance, and the LED string configuration (number of strings, Vf, If at 2000 nits).
  - Which display/TDDI IC does it use (FT7250?), is touch on I2C or SPI, and is the touch firmware stored in flash or does the host have to download it at every boot?
  - What are the MIPI lane count, video or command mode, and full timing (HFP/HBP/HSA/VFP/VBP/VSA, pixel clock)? What are the minimum and maximum frame rate and the maximum VFP? Does the panel accept 24 or more lines of vertical blanking and 50-52 Hz, and does touch still work at those settings?
  - Can you supply a tested HDMI-to-MIPI board for this exact model? Which chip and EDID does it use, does it include an LED driver, and does it provide touch as USB HID (VID:PID, tested on Linux)?
  - What are the backlight driver input voltage, PWM dimming frequency and efficiency, and the panel's high-temperature derating and LC clearing point at 2000 nits?
  - Can you add bonded AR/AG cover glass, and what is the resulting thickness?
  - Is this the same glass as Microtech MTF070UG53A-V1 or Midas MDT0700F1IHHC-MIPI?
  - Why does part number ET070WU01-TT appear as both a 350-nit and a 1300-nit product on your site?
  - What are the price and MOQ for 1-2 samples, the lead time, courier (DHL/FedEx) shipping cost to Ukraine, and the Incoterms?
- **Real price and shipping to ukraine:** There is no public price; Youritech sells by quote only, and Microtech lists no price and a 25-45 day lead time. The closest documented reference is the Midas MDT0700F1IHHC-MIPI (2500 nits, same active area). A search snippet put it at about EUR 324 ex VAT at quantity 1 with a 12-week lead time on Farnell; the page returned 503 to me, so that is unverified. Shipping from Shenzhen to Ukraine would be by courier (DHL/FedEx), and no cost is stated. Ukrainian import VAT and duty above the duty-free threshold apply, so check the current threshold. Neither part is sold in Ukrainian shops.
- **Rf harmonics check:** All values are calculated, harmonics up to 2.4 GHz.
  
  | Timing | Pixel clock | Result |
  |---|---|---|
  | 1340x1944 at 60 Hz (24-line vblank) | 156.30 MHz | No hits. Near misses: fundamental 10.3 MHz above 146 MHz, 11th at 1719.3 MHz (9.3 MHz above 1710), 14th at 2188.2 MHz (11.8 MHz below 2200). |
  | JDI exact 1340x1934 at 60 Hz | 155.49 MHz | 11th harmonic at 1710.4 MHz, on the 1690-1710 band edge: a hit. |
  | CVT-RBv2-like 1280x1944 at 60 Hz | 149.30 MHz | 5th at 746.5 MHz (QO-100 IF) and 15th at 2239.5 MHz: hits. |
  | CVT-RB v1 1360x1975 at 60 Hz | 161.16 MHz | 14th at 2256 MHz: a hit. |
  | 1340x1944 at 49.2-49.5 Hz | 128.2-129.0 MHz | Clean, at least 7 MHz margin. |
  
  - Bridge DSI clock (4-lane non-burst, about 3x pixel clock): 468.9 MHz at 60 Hz, no harmonics in band. In burst mode the rate is set by the bridge firmware, so ask the seller.
  - The 6-8 W backlight boost converter and its PWM are a strong broadband noise source and need shielding.
- **Sunlight readability estimate:** Calculated, and valid only if the 2000 nits is real. Using CR 1200 from the Midas sibling:
  - At 100 klx: about 13:1 with 0.5% diffuse reflectance (bonded AR cover), about 7:1 at 1%, about 4:1 at 2%.
  - At 50 klx: about 26:1, 13:1 and 7:1 respectively.
  
  In-cell touch adds no separate touch layer. Cover glass is not stated: an air-gapped cover would add about 8% specular glare. Bonded AR glass is needed to be truly sunlight-readable. Because the brightness is unverified, this estimate is conditional.

