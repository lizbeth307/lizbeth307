# Targets link budgets: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_d3593e9c-5ce`_

- **Subsystem:** targets_link_budgets
- **Findings:**
  1.
    - **Claim in stack:** Meteor-M N2-4 LRPT on 137.900 MHz (backup 137.100), QPSK 72k, rated reliable on the V-dipole; observed on 137.900 MHz on 17-18 Oct 2026; decoded with SatDump.
    - **Finding:** Confirmed. SatNOGS Network has 'good' N2-4 observations on 137.900 MHz on 18 Oct 2026 (00:36-06:37 UTC, max elevations 23-90 deg). WMO OSCAR (updated 2026-01-23) lists it as Operational, EOL 2029 or later, with LRPT on 137.1, 137.9 and 137.9125 MHz, RHCP, 150 kHz. OSCAR gives the rate as 80 kbps. SatDump master has pipelines 'METEOR M2-x LRPT 72k' (137.9 primary, 137.1 backup) and 'METEOR M2-x LRPT 80k'.
    - **Verdict:** confirmed
    - **Action:** Keep. Install both the 72k and the 80k SatDump pipelines, and let the pass wrapper try 72k first and fall back to 80k. Keep 137.100 MHz as the backup frequency.
    - **Impact:** Primary validation target is live as of October 2026.
    - **Sources:**
      - https://network.satnogs.org/api/observations/?sat_id=VSVI-4798-5613-4587-2414&status=good
      - https://space.oscar.wmo.int/satellites/view/meteor_m_n2_4
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Meteor-M.json
  2.
    - **Claim in stack:** Meteor-M N2-3 LRPT on 137.900 MHz rated on the edge: the N2-4 budget minus 3-6 dB because the satellite's VHF antenna is partly undeployed (estimate not quantified); expect decodes only above about 40-60 deg.
    - **Finding:** The frequency and the 'live' status are confirmed: SatNOGS has 'good' N2-3 observations on 137.900 MHz on 17-18 Oct 2026, the lowest at 16 deg max elevation. WMO OSCAR (2026-01-23) says 'Operational, working with limitations' and gives the reason as the X-band radio link failure. It does not mention the VHF antenna. The 3-6 dB antenna penalty therefore has no primary source.
    - **Verdict:** unverified
    - **Action:** Keep the 'on the edge' rating, but label the -3...-6 dB as a community estimate. Replace it with an on-air number: compare the SatDump SNR of N2-3 and N2-4 on similar passes.
    - **Impact:** Affects only the expected success rate for N2-3.
    - **Sources:**
      - https://network.satnogs.org/api/observations/?sat_id=TLCE-8079-2988-7210-7028&status=good
      - https://space.oscar.wmo.int/satellites/view/meteor_m_n2_3
  3.
    - **Claim in stack:** 137 MHz carries only Meteor-M N2-4 and N2-3 LRPT. APT no longer exists: NOAA-18, -19 and -15 ended on 06.06, 13.08 and 19.08.2025.
    - **Finding:** Confirmed. NOAA OSPO: NOAA-18 was decommissioned on 6 Jun 2025 (S-band transmitter failure), NOAA-19 was passivated on 13 Aug 2025 at 1655 UTC, and NOAA-15 was decommissioned on 19 Aug 2025 at 2037 UTC. Meteor-M N2-5 has not launched: WMO OSCAR lists it as Planned, launch 2027 or later (updated 2026-01-23). No new 137 MHz weather source exists in October 2026. The NOAA OSPO Metop page shows APT/LRPT as RED on Metop-B and Metop-C.
    - **Verdict:** confirmed
    - **Action:** No change. Leave N2-5 out of the catalogue until it launches.
    - **Impact:** The catalogue is correct.
    - **Sources:**
      - https://www.ospo.noaa.gov/Operations/POES/status.html
      - https://ospo.noaa.gov/data/messages/2025/08/MSG_20250819_1547.html
      - https://space.oscar.wmo.int/satellites/view/meteor_m_n2_5
      - https://www.ospo.noaa.gov/operations/metop/status.html
  4.
    - **Claim in stack:** Meteor-M HRPT on 1700 MHz RHCP at 665.4 ksym/s. Patch tier (4-turn helix + SAWbird+ GOES) rated on the edge at +1.5...+3 dB; helicone tier +8.9...+9.4 dB (NEC). Own spurs at 1699.2 and 1704.0 MHz are scanned first.
    - **Finding:** WMO OSCAR lists AHRPT at both 1700 MHz and 1705 MHz (3000 kHz, RHCP, 665.4 kbps) for N2-3 and for N2-4. SatNOGS DB also lists 1700 and 1705 MHz for N2-4. The SatDump 'METEOR HRPT' pipeline defaults to 1700 MHz only. If a satellite uses 1705 MHz, its occupied band (about 1703.5-1706.5 MHz) contains the stack's known 1704.0 MHz self-spur. The margins themselves are NEC/model numbers and were not re-derived, because no satellite EIRP is published.
    - **Verdict:** new_risk
    - **Action:** Add a 1705.0 MHz HRPT profile alongside 1700.0 MHz and pick between them per pass by a power-only check. In the D10 A/B spur matrix, treat 1703.5-1706.5 MHz as an in-band window: if the 1704.0 MHz spur is at or above 3 dB over the floor, fix it with the display pixel-clock and shielding measures before claiming HRPT margins.
    - **Impact:** A self-spur inside the HRPT band can cost several dB on a link that is already on the edge at patch tier.
    - **Sources:**
      - https://space.oscar.wmo.int/satellites/view/meteor_m_n2_4
      - https://space.oscar.wmo.int/satellites/view/meteor_m_n2_3
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=59051
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Meteor-M.json
  5.
    - **Claim in stack:** Metop-B AHRPT on 1701.3 MHz at 2.333 Msym/s. Not reachable at patch tier; on the edge (experiment) on the helicone, with intermittent modulator losses of about 7 dB. Metop is 'unknown until checked on air'.
    - **Finding:** Metop-B AHRPT is still a live service. NOAA OSPO Metop status (updated 3 Sep 2026) shows 'MetOp-B AHRPT: Yes', and a EUMETSAT collision-avoidance notice of 6 May 2026 lists 'AVHRR AHRPT Metop-B'. The same OSPO page shows 'MetOp-C AHRPT: No', while SatNOGS DB lists Metop-C 'AHRPT Prime' on 1701.3 MHz as active, so Metop-C's state is in conflict between sources. I could not verify the 7 dB modulator loss: the satdump.org satellite list was behind an Anubis bot wall, and no EUMETSAT statement turned up. SatDump master metop_ahrpt is 2333333 sym/s, RRC alpha 0.5, default 6 Msps.
    - **Verdict:** confirmed
    - **Action:** Keep the row as experimental and gated. Run the gate (b) hump search on 1701.3 MHz on both Metop-B and Metop-C passes and record which one shows a carrier. Mark the 7 dB figure as an unverified community report.
    - **Impact:** The target exists, but whether Metop-B or Metop-C is the better one is open. The patch-tier 'not reachable' rating is unchanged.
    - **Sources:**
      - https://www.ospo.noaa.gov/operations/metop/status.html
      - https://www.ospo.noaa.gov/data/messages/2026/05/MSG_20260506_1452.html
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=43689
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/MetOp.json
  6.
    - **Claim in stack:** AWS on 1707 MHz at 1.785 Msym/s. Helicone tier on the edge, with the same gates as Metop. 2.88 Msps gives about 1.6 samples per symbol for AWS and about 1.2 for Metop. AWS bandwidth is about 1.2 dB below Metop. EIRP is not published.
    - **Finding:** Confirmed. WMO OSCAR (updated 2026-08-24) lists AWS PFM as Operational, launched 16 Aug 2024, EOL 2029 or later, with a direct-broadcast L-band link on 1707 MHz, RHCP, 3400 kHz, 3570 kbps, and no EIRP. SatDump aws_pfm is QPSK 1785000 sym/s, alpha 0.45. My arithmetic (Bash, model): AWS occupies 2.59 MHz, which fits inside 2.88 Msps (1.61 samples per symbol). Metop occupies 3.50 MHz, so 2.88 Msps captures only about 82% of it (1.23 samples per symbol): truncated roll-off plus ISI. AWS should be easier than Metop on the V4L.
    - **Verdict:** confirmed
    - **Action:** Keep. Rank AWS ahead of Metop in the gate order, since its whole spectrum fits the V4L capture and Metop's does not.
    - **Impact:** Sets the order of the L-band experiments.
    - **Sources:**
      - https://space.oscar.wmo.int/satellites/view/aws_pfm
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/AWS.json
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=60543
  7.
    - **Claim in stack:** FengYun-3 AHRPT is X-band at about 7.8 GHz and not available. FY-3C L-band ended in November 2024.
    - **Finding:** Confirmed. WMO OSCAR shows FY-3C Inactive with EOL 28 Nov 2024, and HRPT/DPT outside China not provided from 25 May 2020; its L-band AHRPT was 1706.7 MHz. FY-3E (Operational, updated 2026-08-27) lists only X-band MPT (7821.5-7898.5 MHz) and DPT downlinks.
    - **Verdict:** confirmed
    - **Action:** No change.
    - **Impact:** None.
    - **Sources:**
      - https://space.oscar.wmo.int/satellites/view/fy_3c
      - https://space.oscar.wmo.int/satellites/view/fy_3e
  8.
    - **Claim in stack:** FY-2H carrier on 1687.5 or 1690.5 MHz (to be confirmed on air): carrier only, linear polarisation, -3 dB. It is the second L-band reference source, after the Inmarsat NCS.
    - **Finding:** Confirmed with a new caveat. WMO OSCAR (updated 2026-10-12): FY-2H at 79 deg E is 'Operational, Only Limited access', EOL 2026 or later. S-VISSR is on 1687.5 MHz (linear, 2000 kHz, 660 kbps). LRIT and primary-station ranging are on 1690.5 MHz (linear). Secondary and backup ranging are on 1686.5 and 1684.5 MHz. SatDump fengyun_svissr uses 1687.5 MHz at 660 ksym/s.
    - **Verdict:** confirmed
    - **Action:** Keep it as a carrier-only reference source, with 1687.5 MHz as the first frequency to try. Because EOL is '2026 or later', add a fallback note: if FY-2H goes silent, use Elektro-L5 at 76 deg E (see the Elektro finding).
    - **Impact:** The reference source may end soon.
    - **Sources:**
      - https://space.oscar.wmo.int/satellites/view/fy_2h
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/FengYun-2.json
  9.
    - **Claim in stack:** Elektro-L LRIT on 1691 MHz: about 3 dB below reports made with a 65 cm dish, decodes at about +1 dB SNR, 'status of Elektro-L5 uncertain'. In the GEO visibility list it is 'Elektro-L 76E'.
    - **Finding:** Corrected. Elektro-L No.5 launched on 12 Feb 2026 to 76 deg E. WMO OSCAR (2026-04-20) shows it as 'Commissioning', with LRIT on 1691 MHz (200 kHz, RHCP, 64/128 kbps) and HRIT on 1691 and 1693 MHz. SatNOGS DB lists its LRIT on 1691 MHz, BPSK, approved 2026-04-07 but flagged unconfirmed. RTL-SDR.com (mid-October 2026) reports that L5 is commissioned at 76 deg E and transmitting GGAK, LRIT, HRIT and X-band RDAS. It also reports that Elektro-L3 is drifting from 76 deg E to 14.5 deg W (about 3.1 deg/day, ETA about 12 Oct 2026) to replace Elektro-L2, which never provided LRIT/HRIT there. L-band xRIT could therefore return to western Europe and the Atlantic side. My model check (formula): a 65 cm dish at 1691 MHz is about 18.6 dBi at 55% efficiency, against 15.7 dBic for the helicone, so the 3 dB shortfall is consistent.
    - **Verdict:** corrected
    - **Action:** Update the catalogue and the GEO visibility list: Elektro-L5 at 76 deg E is the active LRIT source, and Elektro-L3 at 14.5 deg W is 'pending commissioning, check on air'. Remove Elektro-L2 as an imagery source. Keep the row on the edge and experimental. The longitude of Elektro-L4 was not verified.
    - **Impact:** Elektro LRIT moves from 'uncertain' to a real experimental target over most of Eurasia and Africa, and possibly the Atlantic side.
    - **Sources:**
      - https://space.oscar.wmo.int/satellites/view/electro_l_n5
      - https://db.satnogs.org/satellite/67756
      - https://www.rtl-sdr.com/?p=67091
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Elektro_Arktika.json
  10.
    - **Claim in stack:** The L-band GEO reference list holds only the Inmarsat-C NCS, FY-2H at 79 deg E and Elektro-L at 76 deg E. The visibility flag notes that most of the Americas, East Asia and Oceania see none of these.
    - **Finding:** New option. SatDump master has pipelines for three other GEO L-band broadcasts, all inside the SAWbird+ GOES 1648-1728 MHz passband: GOES-R HRIT on 1694.1 MHz (927 ksym/s), GK-2A LRIT on 1692.14 MHz (128 ksym/s) and FengYun-4A LRIT on 1697 MHz (90 ksym/s). Together they cover the Americas and East Asia/Oceania, the regions the current list leaves blank. Budget scaling (model, by symbol rate only): GK-2A LRIT needs about the same as Elektro LRIT. GOES HRIT needs about 10*log10(927/128) = 8.6 dB more, so on the helicone it is a carrier check only. The current status of FY-4A was not verified.
    - **Verdict:** new_option
    - **Action:** Add region-gated rows, shown only when the GNSS-derived visibility flag is true: GK-2A LRIT (experimental, same gate as Elektro), GOES HRIT (carrier and C/N0 check only) and FY-4A LRIT (unverified status). Enable PLUGIN_GOES, PLUGIN_GK2A and PLUGIN_FY4 in the SatDump allow-list only if these rows are kept.
    - **Impact:** Gives every region at least one GEO L-band reference source, since the user's region is unknown.
    - **Sources:**
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/GOES.json
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/GK2A.json
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/FengYun-4.json
  11.
    - **Claim in stack:** Inmarsat-C EGC SafetyNET in 1537.0-1544.2 MHz, BPSK 1200 sym/s, received on the patch tier (RTL-SDR Blog L-band patch on RTL-B). Rated on the edge, with the profile disabled until egc-gate passes. The NCS is found by a power-only scan of 1537-1545 MHz.
    - **Finding:** Partly confirmed. The SatDump 'Inmarsat STD-C' pipeline uses 1200 sym/s, which matches the BPSK 1200 sym/s claim. The RTL-SDR Blog store lists the 'Active L-Band 1525-1660 Inmarsat to Iridium Patch Antenna Set': RHCP, 3.3-5 V at 20 mA bias, $59.95, in stock at the Amazon USA and China warehouses. My G/T model (Bash): G of +3 to +5 dBic with Tsys of 150-250 K gives -21 to -17 dB/K, which is 2-6 dB better than the -23 dB/K ship-terminal class. That supports the 'on the edge, works' rating. Current NCS frequencies per ocean region were not verified. Inmarsat moved the Pacific region from I-4 F1 to I-4 F2 on 21 Nov 2023, and the MEAS region is moving from I-4 F2 to I-6 F1. No 2026 sunset of Inmarsat-C was found.
    - **Verdict:** confirmed
    - **Action:** Keep the power-only NCS discovery, because it does not depend on per-region frequencies that are still changing. Keep the profile disabled until egc-gate passes.
    - **Impact:** The method holds up against the satellite migrations.
    - **Sources:**
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Inmarsat.json
      - https://www.rtl-sdr.com/store/
      - https://vishipel.com.vn/pic/FileLibrary/NCSR-11-5_638646866683478524.pdf
  12.
    - **Claim in stack:** The NCS power scan covers 1537-1545 MHz and the table row says 1537.0-1544.2 MHz, while Cospas-Sarsat 1544.5 MHz is excluded by the catalogue.
    - **Finding:** New risk. The Cospas-Sarsat downlinks occupy 1544-1545 MHz, not only 1544.5: Galileo SAR repeaters at 1544.1 MHz LHCP (90 kHz wide by default), BDS SAR moved to 1544.21 MHz, the return link at 1544.9 MHz, and SARSAT LEO at 1544.5 MHz. The scan window, and the 1544.2 MHz upper edge of the table row, both overlap an excluded service. A strong carrier there could be picked as an 'NCS candidate'.
    - **Verdict:** new_risk
    - **Action:** Cap NCS candidate selection at 1543.9 MHz. Mask 1544.0-1545.0 MHz as no-demodulation in egc-gate, and as occupancy-only or 'no data' in surveys. Add a test that egc-gate refuses to demodulate any carrier at or above 1544.0 MHz.
    - **Impact:** Keeps the Cospas-Sarsat exclusion airtight inside the one flow that does demodulate in this band.
    - **Sources:**
      - https://www.unoosa.org/pdf/icg/2016/pf-16/5.pdf
      - https://www.gsc-europa.eu/node/6925
      - https://www.unoosa.org/documents/pdf/icg/2018/icg13/wgs/wgs_04.pdf
  13.
    - **Claim in stack:** SatDump is built from master (2.0.0-alpha) from source 'without inmarsat_support'. The last numbered release is 1.2.2.
    - **Finding:** The version claim is confirmed. Master CMakeLists has project VERSION 2.0.0 with SATDUMP_VERSION_TYPE 'alpha', the last commit was 30 Sep 2026, and 1.2.2 is still the latest tagged release. Ubuntu packages lag behind (noble 1.1.2; resolute 1.2.2+git). The exclusion method has a gap. plugins/CMakeLists.txt sets option(PLUGINS_ALL ... ON) and every plugin is added with if(PLUGIN_X OR PLUGINS_ALL), so passing -DPLUGIN_INMARSAT=OFF alone still builds inmarsat_support, along with orbcomm_support, dmsp, wsf, spacex and the Webhook app (ON by default). The shipped resources/pipelines also contain targets the rules forbid: Inmarsat.json (STD-C plus Aero 0.6k-10.5k aircraft traffic), Orbcomm.json ('Orbcomm STX Auto' at 137.5 MHz, inside the VHF-137 SAWbird+ NOAA passband), Syracuse.json (Syracuse-3A/3B/4A/4B TLM, French military SATCOM, 7.7 GHz), Cosmos.json (Cosmos 2558 S-band, 2284 MHz), DMSP.json and WSF-M.json (DoD weather, 2252.5 MHz, 'Tactical DB') and Others.json ('Yunhai AHRPT - Encrypted' at 1704.0 MHz, inside the patch-helix and SAWbird+ GOES passband). Elektro_Arktika.json has a 'GGAK MQTT Test' (network) pipeline.
    - **Verdict:** new_risk
    - **Action:** Build with -DPLUGINS_ALL=OFF and switch on only the allow-list (PLUGIN_METEOR, PLUGIN_NOAA_METOP, PLUGIN_AWS, PLUGIN_ELEKTRO_ARKTIKA, PLUGIN_FY2, plus PLUGIN_GOES, PLUGIN_GK2A and PLUGIN_FY4 if the region rows are kept). Also set -DPLUGIN_WEBHOOK_APP=OFF and -DPLUGIN_REMOTE_SDR_SUPPORT=OFF. Package only allow-listed pipeline JSON files and delete Inmarsat, Orbcomm, Syracuse, Cosmos, DMSP, WSF-M, Others and the MQTT test. The CI packaging audit fails if any pipeline name outside the allow-list, or any of these plugin .so files, is present.
    - **Impact:** Rule compliance: as specified, the build would ship decoders aimed at military transmitters and at private traffic, three of them inside the device's own RF coverage.
    - **Sources:**
      - https://raw.githubusercontent.com/SatDump/SatDump/master/CMakeLists.txt
      - https://raw.githubusercontent.com/SatDump/SatDump/master/plugins/CMakeLists.txt
      - https://github.com/SatDump/SatDump/tree/master/resources/pipelines
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Orbcomm.json
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Syracuse.json
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Cosmos.json
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Others.json
      - https://github.com/SatDump/SatDump/releases
      - https://github.com/SatDump/SatDump/commits/master
  14.
    - **Claim in stack:** ISS: SSTV on 437.550 MHz Robot 36, with Series 34 on 22-25.10.2026. APRS on 437.825 MHz is 'active, still being tested'. The FM repeater is 437.800 MHz down / 145.990 MHz up with PL 67. The SSTV budget assumes 10 W.
    - **Finding:** Confirmed. The ARISS SSTV page (updated 2026-10-14) lists Series 34 'ARISS Hardware', Thu 22 Oct to Sun 25 Oct 2026, times TBD, 437.55 MHz, Robot 36, 36 s on and 2 min off, power not stated. Series 33 ran 2-6 Oct 2026 on 437.550 MHz; one bulletin's '437.500' is a typo. 10 W is stated only for Series 31. The ARISS station status of 7 Oct 2026 has the Columbus D710GA in voice-repeater mode (145.990 up, PL 67, 437.800 down) and the Zvezda D710GA running APRS on 437.825 MHz while it is 'still being troubleshooted and tested'. HamTV is sending a test signal on 2395.00 MHz. AMSAT reports for the 30 days to 18 Oct 2026: ISS [FM] heard 100 of 100, ISS [UHF Digi] heard 20, ISS [SSTV] 1 'not heard' (between events). SatNOGS DB has 'Mode U - SSTV - Robot-36' on 437.550 MHz (updated 2026-05-07) and 'Mode U APRS test' on 437.825 MHz (2026-02-24).
    - **Verdict:** confirmed
    - **Action:** Keep. Series 34 is the first on-air validation event. Record it as IQ (it is not voice) and use the pass to measure real CNR on the tilted whip.
    - **Impact:** Gives a validation event four days from now.
    - **Sources:**
      - https://www.ariss.org/upcoming-sstv-events.html
      - https://www.ariss.org/current-status-of-iss-stations.html
      - https://qsl.net/w3apl/news/2026/10/02/weekend-update.html
      - https://www.amsat.org/status/
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=25544
  15.
    - **Claim in stack:** 145.800 MHz was last used for SSTV in Series 28 (July 2025). Class 7 'sstv' and the profiles use 437.550 MHz only.
    - **Finding:** Not verified. The ARISS page gives 145.800 MHz PD120 for the July 2025 event but no frequency for the 3-9 Oct 2025 event. SatNOGS updated its '145.800 Mode V Imaging SSTV' entry on 2025-10-02, the day before that event, which hints that 145.800 MHz may have been used then. The December 2025 RS-38S 'retread' sent Robot 36 on 437.825 MHz. SSTV has used all three frequencies within the last 15 months.
    - **Verdict:** unverified
    - **Action:** Set the SSTV watch list to 437.550 MHz (primary), 437.825 MHz and 145.800 MHz. The 145.800 MHz entry needs the optional 2 m/WIDE path. Take event frequencies from the ARISS page and the SatNOGS cache, never hard-code them.
    - **Impact:** Avoids missing an event that moves band.
    - **Sources:**
      - https://www.ariss.org/upcoming-sstv-events.html
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=25544
  16.
    - **Claim in stack:** ISS SSTV on the patch tier: CNR 18.8-22 dB in 15 kHz at 10-60 deg against 10-12 dB needed (model, 10 W EIRP). CubeSat 1 W 9k6 on the patch tier: -5.3/+0.1/+2.5/+4.1/+5.0/+5.3 dB at 10/30/45/60/75/90 deg.
    - **Finding:** Confirmed as conservative, by an independent model (script at /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/tlb/scripts/lb.py: spherical-Earth slant range, free-space path loss, 3 dB polarisation and body loss). ISS at 420 km, 10 W, 0 dBi, Tsys 300-600 K: 17-20 dB at 10 deg and 27-30 dB at 60 deg. At 5 W it is still 17 dB or more at 10 deg (300 K). CubeSat at 500 km, 1 W, Eb/N0 13 dB needed: -1.8 to +8.8 dB over 10-90 deg at 300 K and 0 dBi; -4.8 to +5.8 dB at 600 K. The stack's figures fall at or below mine, and 'passes above about 30 deg' agrees. All of these are models, not measurements.
    - **Verdict:** confirmed
    - **Action:** Keep the ratings. Replace them with measured CNR from Series 34 and from one known 1 W 9k6 CubeSat pass.
    - **Impact:** The budgets are internally consistent and conservative.
    - **Sources:**
      - https://www.ariss.org/upcoming-sstv-events.html
  17.
    - **Claim in stack:** Amateur targets on the patch tier: AO-73 BPSK telemetry on 145.935 MHz; CW beacons of AO-7 (145.9775), RS-44 (435.605) and FO-29 (435.795) rated on the edge; SO-50 (436.795) at -5 dB even at zenith; AO-91 (145.960) about +1 dB only at zenith; JO-97 145.840 MHz with EIRP not verified.
    - **Finding:** Frequencies are confirmed in SatNOGS DB: AO-73 BPSK 1200 on 145.935 (updated 2026-06-27), RS-44 beacon 435.605 (2026-04-06), FO-29 beacon 435.795, SO-50 436.795 with CTCSS 67, AO-91 145.960 'no CTCSS any longer' (2026-06-26). AMSAT reports for the 30 days to 18 Oct 2026: AO-7 heard (U/v 33, V/a 14), AO-73 'telemetry only' 9, FO-29 heard 73, JO-97 heard 36, RS-44 heard 100, SO-50 heard 80, but AO-91 heard 2 against 6 'not heard'. My independent AO-73 model (30 mW, 600 km, Tsys 1000-3000 K) gives -1.7 to +13 dB over 10-90 deg; the stack's -5/0/+5 dB is conservative. The JO-97 frequency was not re-checked.
    - **Verdict:** new_risk
    - **Action:** Mark AO-91 as 'rarely active (AMSAT reports mostly not heard)' and remove it from the test plan. Keep the rest. AO-73 stays telemetry-only, which matches the target.
    - **Impact:** Small. It avoids wasted validation passes.
    - **Sources:**
      - https://www.amsat.org/status/api/v1/sat_info.php?name=AO-91_%5BFM%5D&hours=720
      - https://www.amsat.org/status/
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=39444
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=43017
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=44909
  18.
    - **Claim in stack:** gr-satellites 5.5 (5.5.0 from noble apt) decodes CubeSats offline from recordings.
    - **Finding:** Upstream is v5.9.0 (14 Dec; the year is not shown on the page, and its changelog cites '2025 launches'). It adds about two dozen satellites, including Geoscan-1 to 6, FORESAIL-1P, HYDRA-T/W and INNOCUBE, and moves the code to C++17. Ubuntu resolute, stonking and tenacious carry 5.8.0; noble is still on 5.5.0-2build2.
    - **Verdict:** new_option
    - **Action:** Build gr-satellites 5.9.0 from source as a +labN deb against noble's GNU Radio 3.10.9.2, and verify it with the bundled test recordings. Fall back to 5.5.0 if the build fails. Refresh SatNOGS DB frequencies anyway.
    - **Impact:** Covers CubeSats launched from 2024 to 2026 that 5.5.0 does not know.
    - **Sources:**
      - https://github.com/daniestevez/gr-satellites/releases/tag/v5.9.0
      - https://github.com/daniestevez/gr-satellites/releases
      - https://launchpad.net/ubuntu/+source/gr-satellites
  19.
    - **Claim in stack:** QO-100 NB: CW beacon on 10489.500 MHz (IF 739.500 MHz) and PSK beacon on 10489.750 MHz at 400 bit/s BPSK. Planned only on the conservative model (about G + 13...16 dB-Hz): the bare LNB gets the CW beacon, the cone gets the PSK beacon on the edge, the 21/23 dBi horn gets the beacons, CW and beacon-level SSB. DATV and typical SSB are lost.
    - **Finding:** Frequencies are confirmed by the AMSAT-DL bandplan: lower beacon 10489.500 MHz CW (F1A, 400 Hz shift), middle beacon 10489.750 MHz at 400 bit/s BPSK, multimedia beacon 10489.9935 MHz 8APSK at 7200 bit/s, upper beacon 10490.000 MHz CW. 10489.5 - 9750 = 739.5 MHz IF. The transponder is live: AMSAT QO-100 [NB] heard 43 of 43 in the 30 days to 18 Oct 2026. I found no primary measurement to anchor the 'G + 13...16 dB-Hz' constant, only an anecdote of bare-LNB reception without figures (passion-radio review).
    - **Verdict:** unverified
    - **Action:** Keep the conservative model and its region gate. Make the A/B test (bare LNB, cone, 3 segments, 6 segments) the source of the constant, and log C/N0 of the 10489.500 MHz beacon for each configuration.
    - **Impact:** Frequencies are right. The margin anchor is still a model.
    - **Sources:**
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
      - https://www.amsat.org/status/
      - https://www.passion-radio.com/satellite-qo-100/converter-432-936.html
  20.
    - **Claim in stack:** GNSS L1 plus regional SBAS. EGNOS is generalised to 'regional SBAS' (WAAS, MSAS, GAGAN by visibility). Chain: LC76G, gpsd 3.25, chrony.
    - **Finding:** EGNOS, from the EGNOS real-time performance page (9 Feb 2026): PRN 121 (Eutelsat 5WB) and PRN 136 (SES-5) are operational and PRN 123 (Astra 5B) is in test. Monthly reports up to August 2026 still use PRN121-PRN136. The regional list leaves out operating SBAS systems: SDCM, KASS, BDSBAS and SouthPAN (their PRNs were not verified in this pass). gpsd: upstream is 3.27.5 (14 Jan 2026), and 3.27.1 fixed CVE-2025-67268 (NMEA2000) and CVE-2025-67269 (NovAtel). Noble ships 3.25-3ubuntu3.2 in noble-security (8 Jan 2026).
    - **Verdict:** corrected
    - **Action:** Generalise to 'any SBAS PRN 120-158 the receiver reports, labelled by system', with no hard-coded list. Pin gpsd at 3.25-3ubuntu3.2 or later from noble-security, or build 3.27.5.
    - **Impact:** Better SBAS labelling worldwide, and no gpsd build with known CVEs.
    - **Sources:**
      - https://pre-egnos.gsc-europa.eu/services/open-service/open-service-realtime-performance
      - https://egnos.gsc-europa.eu/node/12832
      - https://gitlab.com/gpsd/gpsd/-/raw/master/NEWS
      - https://launchpad.net/ubuntu/+source/gpsd
  21.
    - **Claim in stack:** S-band targets Black Kite-1/2 (2286/2288 MHz, GMSK 38k4), PHASMA (2208/2210 MHz) and HamTV (2395 MHz) need the Lime. The cf2235-kt30 resonator (2170-2300 MHz) blocks HamTV.
    - **Finding:** Frequencies are confirmed in SatNOGS DB. Black Kite-1 ('8U RIoT-1', Rapidtek, Taiwan, launched 28 Nov 2025): 2288 MHz GMSK 38400. Black Kite-2 (launched 30 Mar 2026): 2286 MHz GMSK 38400. PHASMA-LAMARR and PHASMA-DIRAC (Libre Space, Greece, launched 28 Nov 2025): 2210 and 2208 MHz FSK 400k, plus UHF FSK 50k telemetry on 400.600 and 400.550 MHz. HamTV is sending a test signal on 2395.00 MHz (ARISS, 7 Oct 2026). The PHASMA UHF telemetry falls inside the 400-406 MHz radiosonde path, so it is reachable without the Lime. At 50 kbaud it needs about 7.2 dB more than 9k6 (model), so it is likely out of reach on the patch tier.
    - **Verdict:** confirmed
    - **Action:** No change to the S-band rows (Lime-gated, opportunistic). Optionally add PHASMA UHF 400.55/400.60 MHz as 'opportunistic, folding tier only, budget not modelled'. It sits next to the 400.000 MHz self-harmonic that the radiosonde scan ignores.
    - **Impact:** Small.
    - **Sources:**
      - https://db.satnogs.org/api/satellites/BMYD-8328-6159-7072-4807/
      - https://db.satnogs.org/api/satellites/PKWP-7958-4818-1008-2291/
      - https://db.satnogs.org/api/transmitters/?sat_id=KVUS-0486-2614-8565-9913
      - https://www.ariss.org/current-status-of-iss-stations.html
  22.
    - **Claim in stack:** Exclusions by rule: Iridium, Orbcomm frames, Starlink/OneWeb, Thuraya, Cospas-Sarsat 406.0-406.1 and 1544.5 MHz, ARGOS/DCP, Yunhai-1, GRAVES, MILSATCOM 240-320 MHz, MUOS, ISS/Soyuz service voice, pagers/trunking, ACARS/HFDL, and military entries in ADS-B and AIS.
    - **Finding:** The list is consistent with the rules, but incomplete in two places. (1) Cospas-Sarsat needs the whole 1544-1545 MHz band, not just 1544.5 MHz (see the Inmarsat-C scan finding). (2) Nothing at the decoder-package level covers the military and private-content pipelines that SatDump ships (see the SatDump build finding). SatNOGS DB confirms the voice exclusions are real transmitters: Soyuz 121.750 and 143.625 MHz and suit channels.
    - **Verdict:** corrected
    - **Action:** Add 'Cospas-Sarsat 1544.0-1545.0 MHz (MEOSAR 1544.1/1544.21/1544.9, LEOSAR 1544.5)' to the exclusion table. Also add one row: 'SatDump pipelines for Syracuse, Cosmos 2558, DMSP, WSF-M, Yunhai, Orbcomm, Inmarsat (STD-C/Aero): not built, not packaged'.
    - **Impact:** Closes the rule-compliance gaps.
    - **Sources:**
      - https://www.gsc-europa.eu/node/6925
      - https://github.com/SatDump/SatDump/tree/master/resources/pipelines
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=25544
  23.
    - **Claim in stack:** Public terrestrial time signals: DCF77 77.5 kHz, MSF/WWVB 60 kHz, JJY 40/60 kHz, TDF 162 kHz (amplitude-only SID). NAVTEX on 490/518/4209.5 kHz.
    - **Finding:** No ALS162 (162 kHz) shutdown announcement was found. It runs at 800 kW with a scheduled maintenance gap every Tuesday 08:00-12:00, and ANFR was asked to propose its future; I found no source newer than 2023. NAVTEX: the US Coast Guard proposed ending MF NAVTEX in 2019 (84 FR 47967), conditional on IMO-recognised satellite delivery. I found no final termination notice. The other frequencies are standard and unchanged.
    - **Verdict:** unverified
    - **Action:** Keep. In the SID and time-signal profile, flag the TDF Tuesday 08:00-12:00 gap so it is not logged as an ionospheric event. In the US regional profile, list NAVTEX as 'check on air (USCG MF NAVTEX may be terminated)'.
    - **Impact:** Small. It avoids false SID events and empty NAVTEX results in the US.
    - **Sources:**
      - https://en.wikipedia.org/wiki/ALS162_time_signal
      - https://www.banquedesterritoires.fr/lanfr-consulte-sur-le-signal-horaire-hertzien-dallouis
      - https://www.standard-club.com/knowledge-news/news-proposed-termination-of-us-coast-guard-medium-frequency-broadcast-of-navtex-1205
- **Current status oct 2026:** Status as of 18 Oct 2026:
  
  **137 MHz weather:**
  - Meteor-M N2-4 and N2-3 are both transmitting LRPT on 137.900 MHz. SatNOGS has good observations from 17-18 Oct 2026.
  - N2-3 is listed as 'working with limitations' (WMO OSCAR, 2026-01-23). The stated reason is its X-band failure.
  - Meteor-M N2-5 is planned for 2027 or later.
  - NOAA-15, -18 and -19 all ended in 2025, so there is no APT source left.
  
  **Polar L-band (1.7 GHz):**
  - WMO OSCAR lists Meteor AHRPT on both 1700 and 1705 MHz.
  - Metop-B AHRPT is a live service: 'Yes' on NOAA OSPO (3 Sep 2026), and named in a EUMETSAT notice of 6 May 2026.
  - Metop-C AHRPT is 'No' on OSPO but 'active' on SatNOGS. The two sources conflict.
  - AWS PFM is operational on 1707 MHz (3.57 Mbps, RHCP, EOL 2029 or later; OSCAR 2026-08-24).
  - FY-3 L-band has ended: FY-3C reached EOL on 28 Nov 2024, and FY-3E is X-band only.
  
  **Geostationary L-band:**
  - Elektro-L No.5 launched on 12 Feb 2026 to 76 deg E. OSCAR says it is commissioning; RTL-SDR.com reports it transmitting LRIT on 1691 MHz plus HRIT.
  - Elektro-L3 is drifting to 14.5 deg W (ETA about 12 Oct 2026), which could bring xRIT to western Europe and the Atlantic side.
  - FY-2H at 79 deg E is operational with 'limited access' and EOL 2026 or later (OSCAR 2026-10-12).
  
  **ISS:**
  - SSTV Series 34 'ARISS Hardware' runs 22-25 Oct 2026 on 437.55 MHz, Robot 36. Times and power are not stated.
  - Status of 7 Oct 2026: the FM repeater is on 145.990 up (PL 67) / 437.800 down; APRS is on 437.825 MHz and still being tested; HamTV is sending a test signal on 2395 MHz.
  
  **Amateur satellites:**
  - AMSAT reports for the last 30 days: AO-7, FO-29, JO-97, RS-44, SO-50, the ISS FM repeater and QO-100 NB were heard.
  - AO-73 is telemetry only.
  - AO-91 is mostly not heard.
  
  **Software:**
  - SatDump: the latest tagged release is still 1.2.2. Master is 2.0.0-alpha, last commit 30 Sep 2026.
  - gr-satellites: upstream v5.9.0; Ubuntu 26.x carries 5.8.0; noble has 5.5.0.
  - gpsd: upstream 3.27.5; noble's security build is 3.25-3ubuntu3.2.
  - EGNOS: PRN 121 and 136 are operational and PRN 123 is in test.
  
  **Hardware stock:** the RTL-SDR Blog L-band patch is $59.95 and in stock. The V4L is $37.95.
  
  **No EOL notice was found** for Inmarsat-C SafetyNET or for ALS162.
- **Notes:** **Method and limits:**
  - I used 18 WebSearch calls. Everything else came from primary pages: WMO OSCAR, NOAA OSPO, the ARISS station and SSTV pages, AMSAT-DL, the SatNOGS DB and Network APIs, the AMSAT status API, the gpsd NEWS file, the Launchpad API, and raw SatDump master files (CMakeLists and resources/pipelines).
  - satdump.org was behind an Anubis bot wall. That is why the Metop-B '7 dB modulator' claim stays unverified.
  - The GitHub REST API was blocked in this session, so release years shown only as day and month on GitHub pages are inferred. For example, gr-satellites 5.9.0 is dated '14 Dec', probably 2025.
  - Every margin I computed is a model, from /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/tlb/scripts/lb.py (free-space path loss, slant range, G/T). No satellite EIRP is published for Meteor, AWS, Metop or Elektro, so the L-band margins in STACK remain NEC/model numbers.
  - The downloaded pipeline JSON files and API dumps are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/tlb/dl/.
  
  **Highest-priority items:**
  1. SatDump build and packaging: PLUGINS_ALL=ON by default, and the shipped pipelines target Orbcomm STX at 137.5 MHz, Yunhai on 1704.0 MHz, Syracuse, Cosmos 2558, DMSP, WSF-M, and Inmarsat STD-C/Aero. This is a rule-compliance gap.
  2. Cospas-Sarsat 1544-1545 MHz overlaps the Inmarsat NCS scan window.
  3. Elektro-L5 and L3 status corrections, and possible Meteor HRPT on 1705 MHz colliding with the 1704.0 MHz self-spur.
  
  Not re-checked in this pass, because they belong to other subsystems: SDRangel, OpenWebRX+, readsb, AIS-catcher, radiosonde_auto_rx versions, and RF front-end part prices.

