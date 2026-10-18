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

## Адверсаріальна перевірка (`verify`)

_Run `wf_d3593e9c-5ce`_

- **Subsystem:** targets_link_budgets
- **Verdict:** Mostly holds, with corrections. The live-target picture for 18 Oct 2026 checks out against primary sources: both Meteor-M on 137.900 MHz, Meteor HRPT on 1700 MHz, Metop-B AHRPT listed "Yes", AWS operational, Elektro-L5 at 76.05E, ISS Series 34 on 22-25 Oct on 437.55 MHz, FY-2H at 79.2E. Five findings change the spec.
  (1) SatDump plugin allow-list is not enough. Pipelines aimed at military transmitters (Syracuse-3 TLM, Cosmos-2558, Gazelle/OTB-3, Cosmos-2518, Chinese spaceplane, PAZ) use only core modules (pm_demod, psk_demod, ccsds_*), so they run with PLUGINS_ALL=OFF. SatDump also loads ./pipelines.json from the working directory and pipelines.json from the user directory. The only real control is deleting pipeline JSON files plus a controlled working directory. Because the Lime is now kept, the S-band military pipelines (DMSP 2252.5, WSF-M 2252.5, Cosmos-2558 2284, PAZ 2285 MHz) fall inside the device's own 2170-2300 MHz chain.
  (2) With region = Europe, Elektro-L5 and FY-2H are below or near the horizon in western Europe (Lisbon -4.9/-7.3 deg, London -0.1/-2.1 deg, Paris +1.9/-0.1 deg; usable only east of about 13E). FY-2G, GK-2A and FY-4B are not visible, and GOES-East is at most about 10 deg from Iberia. The region rows from stage 1 and the FY-2G row from stage 2 do not apply to this user.
  (3) The Lime is kept, so it should replace the gated Airspy Mini for Metop/AWS at 6 Msps or more.
  (4) Several numbers from stage 2 are wrong: GGAK is 7-8 dB easier than LRIT, not 10.7 dB; the CRC errors in #600 were a software regression fixed by PR #616; gr-satellites commit 71dc9a1 does not exist; the egc-gate "frame IDs" are 6-bit descriptor types, not raw bytes.
  (5) The SatNOGS cache importer must be an allow-list, not a denylist. The ISS entry alone carries Soyuz, suit, EVA and EMU voice, Dragon/Falcon telemetry and ICARUS.
- **Confirmed:**
  - Meteor-M N2-4 (NORAD 59051) and N2-3 (57166) LRPT on 137.900 MHz: 25 + 25 SatNOGS 'good' observations from 15-18 Oct 2026. Demod data on 23/25 (N2-4, lowest max elevation 18 deg) and 20/25 (N2-3, lowest 22 deg; 5 without data at 16, 39, 41, 77 and 87 deg). Fixed QFH/turnstile stations, not a V-dipole.
  - WMO OSCAR (updated 2026-01-23): N2-4 Operational, EOL 2029 or later; N2-3 'Working with limitations', the cause given is the X-band failure, no VHF-antenna mention. Both list LRPT on 137.1/137.9/137.9125 MHz (80 kbps nominal) and AHRPT on 1700 and 1705 MHz, 3000 kHz, RHCP, 665.4 kbps. N2-5 is Planned, 2027 or later.
  - N2-3 antenna: IU1QPR (Meteor guide v1.0.1) says the LRPT antenna 'failed to properly deploy and rests in a tilted position', causing fading. This is a community diagnosis, not an official one. The same guide: 72k standard, 80k only if no sync, 1.024 Msps, never 250 ksps, never RTL or tuner AGC, DC blocking on.
  - NOAA OSPO: NOAA-18 decommissioned 6 Jun 2025 17:40 UTC, NOAA-19 13 Aug 2025 18:55 UTC, NOAA-15 19 Aug 2025 20:37 UTC. No APT source remains.
  - Meteor HRPT uses 1700 MHz in practice: SatDump 'meteor_hrpt' (pm_demod, 665400 sym/s, 1700.0 MHz only); IU1QPR HRPT guide v1.0.2 lists N2-3 and N2-4 at 1700 MHz; SatNOGS JF6FYI (L-band helix + HackRF) 'with-signal' at 1700 MHz on 17 Oct 2026, 87 deg pass, no demod data. The SatNOGS 1705 MHz N2-4 entry is dated 2024-02-23, before the 29 Feb 2024 launch.
  - OSPO Metop status (updated 3 Sep 2026): MetOp-B 'AHRPT: Yes', MetOp-C 'AHRPT: No', APT/LRPT RED on both. SatDump metop_ahrpt: QPSK 2333333 sym/s, alpha 0.5, 1701.3 MHz.
  - AWS PFM (OSCAR 2026-08-24): Operational, 1707 MHz, 3400 kHz, RHCP, 3570 kbps, no EIRP. SatDump aws_pfm: QPSK 1785000 sym/s, alpha 0.45. Model: 2.59 MHz occupied (fits 2.88 Msps); Metop 3.50 MHz (82% captured at 2.88 Msps).
  - FY-2H (OSCAR 2026-10-12): Operational, 'Only Limited access', 79E (TLE 18 Oct: 79.21E), EOL 2026 or later. S-VISSR 1687.5 MHz (2000 kHz), LRIT and primary ranging 1690.5 MHz, all linear. SatDump fengyun_svissr: 1687.5 MHz, 660 ksym/s.
  - Elektro-L5: OSCAR 'Commissioning' (2026-04-20), 76E, LRIT 1691 MHz 200 kHz RHCP 64/128 kbps, HRIT 1691 and 1693 MHz. RTL-SDR.com (mid-Oct 2026) says commissioned at 76E and sending GGAK, LRIT, HRIT and RDAS. TLE of 17 Oct: 76.05E, drift -0.01 deg/day.
  - Elektro-L2 TLE of 18 Oct: 14.52W, inclination 7.0 deg, stationary. Elektro-L3 TLE epoch 9 Oct 14:12 UTC: about 6.7W, drifting west at 3.07 deg/day. No newer TLE on SatNOGS. Roscosmos has not announced the move (RTL-SDR.com); one reader claims about 25W.
  - SatDump: master HEAD 1aedd60 (30 Sep 2026 06:22 UTC), project VERSION 2.0.0 'alpha', last tag 1.2.2. c0b6f88 (CLI add_flag to add_option, fixes #1191), 6b5957f (clock-recovery buffer leak) and 96bb626 (HRIT DecompWT) are on dev only. 7bcd531 (80k LRPT hang) is in master. #1212 is open; maintainer workaround is dd bs=8192 skip=4 on the CADU file.
  - SatDump plugins/CMakeLists.txt: PLUGINS_ALL defaults to ON; every protocol plugin is if(PLUGIN_X OR PLUGINS_ALL). Network/source plugins default ON regardless: SPYSERVER, RTLTCP, SDRPP_SERVER, NET_SOURCE, REMOTE_SDR, TOOLS_APP, WEBHOOK_APP (only with BUILD_GUI), EXPERIMENTAL_DEVICES. BUILD_OPENCL is ON. elektro_arktika, gk2a, goes and fengyun4 link xrit_support.
  - gr-satellites: v5.9.0 tagged 14 Dec 2025. 10d27cb 'Sanitize filenames in FileReceiver' (17 Mar 2026); 1bcf1d8 'Fix bug in file receiver' (29 May 2026, pathlib .dirname replaced by .parent). main HEAD 4210dc4 (22 Sep 2026), version 5.10.0-git, needs GNU Radio 3.10 and C++17. Ubuntu: noble 5.5.0-2build2, resolute 5.8.0-2build2, stonking/tenacious 5.8.0-2.1.
  - gpsd: noble 3.25-3ubuntu3.2 in noble-security/updates (8 Jan 2026); upstream 3.27.5 (14 Jan 2026); 3.27.1 fixed CVE-2025-67268 and CVE-2025-67269; 3.27.6~dev lists more buffer-overrun fixes. gpsd JSON: SBAS is gnssid 1, svid 120-158.
  - EGNOS August 2026 monthly report (published 7 Sep 2026): 'GEO-combined values for PRN121 - PRN136'.
  - ARISS: Series 34 'ARISS Hardware', 22-25 Oct 2026, times TBD, 437.55 MHz, Robot 36, 36 s on / 2 min off, power not stated; Series 33 ran 2 Oct 09:00 to 6 Oct 15:55 UTC; 10 W stated only for Series 31. Station status of 7 Oct 2026: Columbus D710GA voice repeater 145.990 up (PL 67) / 437.800 down; Zvezda radio on APRS 437.825 MHz, still being tested; SSTV scheduled from the Zvezda radio; HamTV test signal on 2395.00 MHz.
  - AMSAT status API, 720 h to 18 Oct 2026: ISS [FM] 100/100 heard, QO-100 [NB] 44/44, SO-50 [FM] 81/84, AO-7 [U/v] 33 heard of 44, AO-91 [FM] 2 heard / 6 not heard.
  - AMSAT-DL bandplan: beacons 10489.500 (CW F1A), 10489.750 (400 bit/s BPSK), 10489.9935 (8APSK 7200 bit/s), 10490.000 MHz; no EIRP or dish size published. Lower-beacon IF on a 9750 MHz LNB is 739.5 MHz.
  - RTL-SDR Blog Active L-Band 1525-1660 patch set: $59.95, RHCP, 3.3-5 V at 20 mA, in stock at the Amazon USA and China warehouses. V4L $37.95.
  - Black Kite-1 (SatNOGS ID 98527): 2288 MHz GMSK 38400. Black Kite-2 (98371): 2286 MHz GMSK 38400. HamTV test carrier on 2395 MHz.
  - Galileo SAR repeaters use 'the 1544 - 1545 MHz downlink band' (GSC). This supports masking the whole 1544.0-1545.0 MHz band.
  - Independent model (scratchpad/tlb3/scripts/lb3.py), all models, not measurements. ISS SSTV CNR in 15 kHz at 0 dBi with 4 dB loss: 13.3-19.3 dB at 10 deg and 23.2-29.2 dB at 60 deg (5-10 W, 300-600 K), so STACK's 18.8-22 dB is consistent. CubeSat 1 W 9k6, margin over 13 dB Eb/N0: -5.8/-0.4/+2.1/+3.6/+4.5/+4.8 dB (600 K) to -2.8/+2.6/+5.1/+6.6/+7.5/+7.8 dB (300 K) at 10/30/45/60/75/90 deg; STACK values sit within this range. Quiet-Sun rise at 1420 MHz on 15.7 dBic with 60 sfu and Tsys 125 K: about 0.9 dB, consistent with STACK's 0.7-1.2 dB.
- **Corrections:**
  1.
    - **Claim in stack:** Stage 1 and 2: build SatDump with -DPLUGINS_ALL=OFF and an allow-list, and package only allow-listed pipeline JSONs. STACK #30: 'without inmarsat_support'.
    - **Finding:** Plugin selection does not disable the most sensitive pipelines. Their modules are in src-core/pipeline/modules (pm_demod, psk_demod, ccsds_conv_concat_decoder, ccsds_simple_psk_decoder), so they run with no plugin:
  - syracuse3_tlm (pm_demod)
  - cosmos_2558_dump (pm_demod + ccsds_simple_psk_decoder, 2284 MHz)
  - gazelle_l_band (OTB-3/Gazelle, 1703 MHz)
  - cosmos_2518_sband and chinese_spaceplane_sband (Work-In-Progress.json)
  - paz_s_tlm (2285 MHz)
  Stage 1 missed Work-In-Progress.json and several entries in Others.json: angels_l_band (USAF ANGELS, 1698.4 MHz, 'angels_argos'), gazelle_l_band (1703 MHz), yunhai_ahrpt (1704 MHz). Also unwanted: Analog.json (generic analog demod, i.e. voice to audio), Ominous.json (137.5 MHz TLM), SpaceX.json, DVB_Test.json ('ISS HamTV to UDP'), and the '..._tcp' pipelines in GOES.json and GK2A.json.
  src-core/pipeline/pipeline.cpp also loads './pipelines.json' from the current directory, or '<user_path>/pipelines.json', on top of the system pipelines.
  The Lime is now kept, and the cf2235-kt30 (2170-2300 MHz) S-band chain passes DMSP/WSF-M (2252.5), Cosmos-2558 (2284) and PAZ (2285 MHz).
    - **Verdict:** new_risk
    - **Action:** Ship a resources/pipelines directory containing only:
  - Meteor-M.json
  - MetOp.json
  - AWS.json
  - FengYun-2.json
  - Elektro_Arktika.json, edited to remove elektro_ggak_mqtt
  Ship no other JSON and no .json.inc files.
  Run every satdump unit with WorkingDirectory set to an empty root-owned directory and the user directory read-only and free of pipelines.json (ProtectHome=read-only, or a dedicated user with no HOME config).
  CI packaging audit fails on any pipeline ID outside the allow-list, at build time and in the device self-check. The deny regex must include syracuse, cosmos, dmsp, wsf, yunhai, angels, gazelle, spaceplane, paz, orbcomm, inmarsat, ominous, analog, spacex, _tcp, _udp and mqtt.
    - **Impact:** Closes a rule-compliance gap that the plugin allow-list does not close, now inside the Lime's S-band coverage too.
    - **Sources:**
      - https://github.com/SatDump/SatDump/tree/master/resources/pipelines
      - https://github.com/SatDump/SatDump/tree/master/src-core/pipeline/modules
      - https://raw.githubusercontent.com/SatDump/SatDump/master/src-core/pipeline/pipeline.cpp
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Work-In-Progress.json
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Others.json
  2.
    - **Claim in stack:** STACK #30: 'master (2.0.0-alpha) from source with Soapy and the LimeSuiteNG legacy API'. Stage 2: all SDR source plugins OFF except RTLSDR, built against the +lab librtlsdr.
    - **Finding:** In this architecture SatDump never opens an SDR. labrx is the only opener; SatDump decodes recordings, or labrx's file/FIFO feed. PLUGIN_SOAPY_SDR_SUPPORT is OFF by default and labelled 'NOT RECOMMENDED', so 'with Soapy' is unnecessary. Keeping SatDump's rtlsdr or limesdr plugin would create a second SDR opener that bypasses labd's bias-tee token and labrx's voice and band masks. Other defaults also need changing:
  - satdump_cfg.json fetches OMM/TLE from plain-HTTP http://orbicentral.net at every launch (kepler_update_interval '1 day').
  - PLUGIN_EXPERIMENTAL_DEVICES_SUPPORT, PLUGIN_PORTAUDIO_SINK and PLUGIN_AAUDIO_SINK default ON.
    - **Verdict:** corrected
    - **Action:** Turn every sdr_sources plugin OFF, including RTLSDR, LIMESDR, AIRSPY and SOAPY. Also set:
  - BUILD_GUI=OFF
  - PLUGIN_EXPERIMENTAL_DEVICES_SUPPORT=OFF and the audio sinks OFF
  - kepler_update_interval 'Never', with TLE/OMM supplied by labd
  - PrivateNetwork=yes (or IPAddressDeny=any) on the pass unit
  The CI ldd check then only has to show no librtlsdr, LimeSuite or soapy linkage. This drops the librtlsdr-dev conflict risk from #1030/#864.
    - **Impact:** Removes a bypass of the receive-only token and masks, network fetches, and a dependency conflict.
    - **Sources:**
      - https://raw.githubusercontent.com/SatDump/SatDump/master/plugins/CMakeLists.txt
      - https://raw.githubusercontent.com/SatDump/SatDump/master/satdump_cfg.json
  3.
    - **Claim in stack:** Stage 2: pin SatDump to dev 96bb626, or master 1aedd60 plus cherry-picks.
    - **Finding:** Each fix is tiny and self-contained:
  - c0b6f88: 2 lines in src-core/core/cli/pipeline.cpp
  - 6b5957f: 6 lines in the clock_recovery gardner, mm and mm_fast files
  - 96bb626: 1 line in xrit DecompWT
  Dev also carries unrelated UI commits (4822fca, c33a2549, 993eb1da). On master, CLI11 add_flag may still accept '--key=value' (unverified).
    - **Verdict:** corrected
    - **Action:** Pin master 1aedd60 with c0b6f88 and 6b5957f cherry-picked (96bb626 optional, HRIT only). The pass wrapper always passes '--key=value'. The arm64 CI decodes one stored baseband per allowed pipeline.
    - **Impact:** Lowest-risk pin that fixes headless CLI decoding.
    - **Sources:**
      - https://github.com/SatDump/SatDump/commits/dev
      - https://github.com/SatDump/SatDump/issues/1191
      - https://github.com/SatDump/SatDump/commit/c0b6f8876c514990c2f22ca98b2a6c8a6f290a5d
  4.
    - **Claim in stack:** STACK #109 and 4.1 rows: FY-2H at 79E is the second L-band reference after the Inmarsat NCS; Elektro-L 76E LRIT. Stage 1: add GOES/GK-2A/FY-4A region rows. Stage 2: add FY-2G at 99.2E as a redundant reference.
    - **Finding:** The user region is now Europe. My geometry model (spherical Earth, GEO 42164 km) gives these elevations for Elektro-L5 76.05E / FY-2H 79.2E / FY-2G 99.2E:
  - Lisbon: -4.9 / -7.3 / -22.2 deg
  - London: -0.1 / -2.1 / -14.2 deg
  - Paris: +1.9 / -0.1 / -13.0 deg
  - Berlin: 7.6 / 5.8 / -6.1 deg
  - Rome: 10.8 / 8.5 / -6.2 deg
  - Warsaw: 12.0 / 10.3 / -1.5 deg
  - Athens: 20.6 / 18.2 / 2.7 deg
  - Kyiv: 18.3 / 16.5 / 4.7 deg
  GOES-East (75.2W) is at most 9.9 deg (Lisbon) and below the horizon east of about Paris. GK-2A and FY-4B are not visible. A satellite at 14.5W would be at 8-45 deg over all of Europe. Alphasat/QO-100 (about 25E) is at 12-46 deg.
    - **Verdict:** corrected
    - **Action:** Europe build: no PLUGIN_GOES, GK2A or FY4 (keep them only as an optional travel profile). Drop the FY-2G row. Label the Elektro-L5 and FY-2H rows 'eastern/central Europe only (about east of 13E), elevation from the GNSS fix and live TLE'. For western Europe the only robust L-band GEO reference is the Inmarsat NCS (Alphasat or I-4).
    - **Impact:** Prevents planning tests against satellites below the horizon. Fewer plugins.
    - **Sources:**
      - https://db.satnogs.org/api/tle/?norad_cat_id=67756
      - https://db.satnogs.org/api/tle/?norad_cat_id=43491
      - https://space.oscar.wmo.int/satellites/view/fy_2g
      - https://db.satnogs.org/api/tle/?norad_cat_id=39215
  5.
    - **Claim in stack:** Stage 2: Elektro-L3 'had not stopped at 14.5 deg W' as of the 9 Oct TLE; about 32W by 18 Oct.
    - **Finding:** At the 9 Oct epoch, L3 was 7.8 deg east of 14.5W moving at 3.07 deg/day. That matches the reported ETA of about 12 Oct, so the TLE cannot show whether it stopped. Its status since 9 Oct is unknown: no newer TLE, and one unverified reader report of about 25W. If L3 is commissioned at 14.5W, it becomes the best Elektro target for all of Europe.
    - **Verdict:** corrected
    - **Action:** Keep stage 2's TLE stationarity gate: |n - 1.00274| < 0.0005 rev/day, longitude from the TLE. Mark L3 'unknown since 9 Oct; becomes a target automatically when stationary'.
    - **Impact:** Wording fix. The mechanism stands.
    - **Sources:**
      - https://db.satnogs.org/api/tle/?norad_cat_id=44903
      - https://www.rtl-sdr.com/?p=67091
  6.
    - **Claim in stack:** STACK: Elektro LRIT on the helicone is about 3 dB below 65 cm dish reports and decodes at about +1 dB SNR. Stage 2: the anchor is 3-4 dB SNR with errors, the helicone is about equal, and +1 dB should be removed.
    - **Finding:** In #600 (Elektro-L4, 65 cm dish, linear feed), the CRC errors and segment misalignment at 3-4 dB were a SatDump regression. PR #616 fixed it, and after the fix perfect images were reported below 3 dB. The maintainer wrote 'on paper, even under 1db is enough' and 'all ELEKTROs ... have somewhat of a linear component'. The reporter saw about 2 dB change from feed-angle tuning.
  My model: the 65 cm dish is 18.2-19.0 dBi. Against it, the 15.7 dBic RHCP helicone is about equal if the signal is pure RHCP, and 3-5 dB worse if it is strongly linear. Expected helicone SNR is about -2 to +4 dB, against a theoretical threshold of about -1 to +1 dB.
  The SatDump pipeline runs 294 ksym/s BPSK r1/2 + RS, which is 128.5 kbps of info, matching OSCAR's 128 kbps but not its 200 kHz bandwidth.
    - **Verdict:** corrected
    - **Action:** Keep 'on the edge'. Rewrite the basis: 'dish anchor 3-4 dB (post-#616 below 3 dB still clean); helicone 0 to -5 dB versus anchor (polarisation unknown); threshold about +1 dB (maintainer, theory)'. Success means frame sync plus CRC-valid segments at a 1 Msps capture. Note on the row that tilting the helicone does not recover the linear component.
    - **Impact:** The rating is unchanged; the basis is now accurate.
    - **Sources:**
      - https://github.com/SatDump/SatDump/issues/600
      - https://github.com/SatDump/SatDump/issues/1141
      - https://space.oscar.wmo.int/satellites/view/electro_l_n5
  7.
    - **Claim in stack:** Stage 2 new option: Elektro-L5 GGAK 1693 MHz 5k is about 10.7 dB easier than LRIT, so it should be the first Elektro test.
    - **Finding:** The SatDump elektro_ggak pipeline runs pm_demod at 5000 sym/s and then ccsds_simple_psk_decoder (1792-byte CADU, no derandomising, rs_i 0, uncoded). It has no products step and needs no plugin.
  Required C/N0 (model, equal EIRP): LRIT about 53.6 dB-Hz (Eb/N0 2.5 dB on info bits); GGAK 45.4-46.6 dB-Hz (uncoded Eb/N0 8.4-9.6 dB). GGAK is therefore 7-8 dB easier, not 10.7 dB, before any PM residual-carrier loss.
  OSCAR also lists HRIT on 1693 MHz. The GGAK EIRP is unpublished. #1141 reports only that the signal 'looks ok' on a 10-turn helix.
    - **Verdict:** corrected
    - **Action:** Keep GGAK as the first Elektro test (eastern/central Europe only, or L2/L3 at 14.5W if a carrier is present). Success means frame sync plus the CADU count. Quote 'about 7-8 dB easier than LRIT (model, equal EIRP)'.
    - **Impact:** The ranking holds; the margin claim is reduced by about 3 dB.
    - **Sources:**
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Elektro_Arktika.json
      - https://github.com/SatDump/SatDump/issues/1141
  8.
    - **Claim in stack:** Stage 2 egc-gate spec: keep a packet only if frame ID is 0x30/0x31/0x32 and the service code in byte 2 is one of {0x04,0x13,0x14,0x24,0x31,0x34,0x44,0x73}; decide on the first fragment; never read byte 8 or beyond.
    - **Finding:** SatDump stdc/packets_structs.h shows how the packet header is laid out:
  - The descriptor's first byte encodes length class and type. Short (bit7 = 0): type 3 bits, so EGC can never be short. Medium (bits 7-6 = 10): type is pkt[0] & 0x3F and length is pkt[1]+2. Long (11): length is pkt[1..2]+3.
  - So 0x30/0x31/0x32 are 6-bit types: raw first byte 0xB0-0xB2 (medium) or 0xF0-0xF2 (long).
  - SatDump hard-codes service code at pkt[2], which is correct only for medium descriptors.
  - Multiframe start (0x3D) carries the inner descriptor at pkt[2].
  - Every packet ends with a 2-byte checksum (compute_crc).
  The SatDump code table is: SafetyNET {04,13,14,24,31,34,44,73}, FleetNET {02,72}, System {00 all ships, 11, 23, 33 download group identity}. SatDump's inmarsat_stdc_parser defaults to save_files=true.
    - **Verdict:** corrected
    - **Action:** egc-gate rules:
  - Parse the descriptor class.
  - service_code offset = descriptor length (2 or 3).
  - Decide on the first fragment.
  - Drop rejected packets without computing their CRC and without copying them.
  - For accepted SafetyNET packets, verify the CRC before reassembly. A corrupted header could otherwise pass a private packet.
  - Drop all System and FleetNET codes, including 0x00.
  - Derive the frame decoder from SatDump module_stdc_decoder. Never compile pkt_parser, egc_parser or msg_parser.
  - Cross-check the code table against the International SafetyNET Services Manual C2 table (pending).
  Unit tests use synthetic medium, long and multiframe packets.
    - **Impact:** Makes the header-only rule implementable without misparsing.
    - **Sources:**
      - https://github.com/SatDump/SatDump/blob/master/plugins/inmarsat_support/stdc/packets_structs.h
      - https://github.com/SatDump/SatDump/blob/master/plugins/inmarsat_support/stdc/pkt_structs.cpp
      - https://github.com/SatDump/SatDump/blob/master/plugins/inmarsat_support/stdc/pkt_parser.cpp
  9.
    - **Claim in stack:** Stage 2: the SatNOGS cache importer drops transmitters in 1544-1545 MHz or 406.0-406.1 MHz, or named SARSAT/Cospas.
    - **Finding:** A denylist is not enough. The SatNOGS ISS (25544) transmitter list includes, as 'active':
  - Soyuz VHF voice: 143.625 and 130.167 MHz
  - suit and EVA voice: 121.100, 121.275, 121.750, 139.208 and 400.575 MHz
  - EMU 414.2 and 417.1 MHz
  - Dragon telemetry 2205.5 and 2216 MHz; Falcon 9 telemetry 2232.5 and 2272.5 MHz
  - ICARUS 468.1 MHz; ISS Ku data 15003.4 MHz; TORU 2.725 and 2.86 GHz
  Metop-C has ARGOS-3 A-DCS on 465.9875 MHz. Elektro-L5 has a 465 MHz 'Data relay' entry. Meteor N2-3 and N2-4 have SARSAT entries on 1544.5 MHz.
    - **Verdict:** corrected
    - **Action:** Make the importer an allow-list keyed on (NORAD, frequency +/- 10 kHz, mode). For the ISS that means 437.550 SSTV, 437.825 APRS, 437.800 FM, 145.800 SSTV and 2395 HamTV. Keep the 1544-1545 / 406.0-406.1 / name denylist as a second layer. Any unknown transmitter goes to a 'review' list and is never added to profiles.
    - **Impact:** Keeps the voice, DCP and military exclusions intact through updates.
    - **Sources:**
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=25544
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=43689
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=67756
  10.
    - **Claim in stack:** Stage 1: Cospas-Sarsat downlinks include 'the return link at 1544.9 MHz'.
    - **Finding:** GSC confirms Galileo SAR uses the 1544-1545 MHz downlink band. The Galileo Return Link is a service delivered in the Galileo navigation message, not a 1544.9 MHz downlink. Whatever is at 1544.9 MHz is not identified in this pass (unverified).
    - **Verdict:** corrected
    - **Action:** Keep the mask at 1544.0-1545.0 MHz. Label it 'Cospas-Sarsat MEOSAR/LEOSAR downlinks (Galileo SAR 1544-1545 MHz; LEOSAR 1544.5)' and drop 'return link 1544.9'.
    - **Impact:** Wording only.
    - **Sources:**
      - https://www.gsc-europa.eu/node/6925
  11.
    - **Claim in stack:** Stage 1: the SSTV watch list is 437.550, 437.825 and 145.800 MHz.
    - **Finding:** 145.800 MHz is also the ARISS crew-contact FM voice downlink: SatNOGS 'Mode V/V FM (crew)', active. Series 26-28 SSTV used 145.800 PD120; November and December 2025 used 437.825 (RS-38S retread), and 2026 used 437.55.
    - **Verdict:** new_risk
    - **Action:** Record IQ on 145.800 MHz only inside ARISS-announced SSTV windows. Apply the labrx voice mask: FM-demodulate to slowrx live and keep no IQ when speech is classified. Never record 145.800 outside events.
    - **Impact:** Keeps the voice-IQ rule intact.
    - **Sources:**
      - https://www.ariss.org/upcoming-sstv-events.html
      - https://db.satnogs.org/api/transmitters/?satellite__norad_cat_id=25544
  12.
    - **Claim in stack:** STACK: Metop/AWS 'Airspy Mini only if gate (a) fails' (#91, BOM 2.11, about $140-160).
    - **Finding:** The user kept the LimeSDR Micro M.2 (0.3-3.8 GHz, 12-bit, up to 56 MHz). At 6 Msps or more it captures Metop's full 3.5 MHz and AWS's 2.59 MHz, removing the 82% truncation that the V4L has at 2.88 Msps. Community data: #727, a V4 decoded MetOp at 2.88 with DC block and AGC. IU1QPR: Metop 'require[s] a wider SDR than the normal RTL-SDR'. Behind the 38 dB SAWbird+ GOES, the Lime's own NF does not matter.
    - **Verdict:** new_option
    - **Action:** Drop the Airspy Mini. Before the Lime arrives (ships 15 Dec 2026), run Metop/AWS on the V4L at 2.88 Msps with DC block. After that, route helicone + SAWbird+ GOES to the Lime RX at 6 Msps ci16. Add a 15-minute zero-drop Lime capture at 6 Msps to the Lime acceptance tests. The RF-frontend owner confirms the switch path.
    - **Impact:** Saves about $140-160 and removes the bandwidth penalty on the L-band experiments.
    - **Sources:**
      - https://github.com/SatDump/SatDump/issues/727
      - https://www.a-centauri.com/articoli/beyond-poes-amateur-satellite-reception
      - https://www.a-centauri.com/articoli/easy-hrpt-guide
  13.
    - **Claim in stack:** Stage 2: Metop-C is 'receivable in Europe per community decodes, Aug 2026'.
    - **Finding:** #1208 is a single report about the AVHRR roll_offset. It is from an unspecified 'amateur L-band station in Athens' (antenna not stated), and the maintainer closed it as 'not planned'. OSPO still shows MetOp-C AHRPT 'No'.
    - **Verdict:** corrected
    - **Action:** Label it 'one community report (Athens, Aug 2026, antenna unknown)'. Run gate (b) on both B and C.
    - **Impact:** Small.
    - **Sources:**
      - https://github.com/SatDump/SatDump/issues/1208
      - https://www.ospo.noaa.gov/operations/metop/status.html
  14.
    - **Claim in stack:** Stage 2: AWS SYNCED-but-filler is a current failure mode; AWS dumps only near Kiruna.
    - **Finding:** #854 dates from 3 Nov 2024, during commissioning: 'AWS is only transmitting filler right now over most of the world'. IU1QPR ('Beyond POES', written about Sep-Oct 2025) says AWS dumps on the same frequency when in view of Kiruna. That favours Europe, the user's region.
    - **Verdict:** corrected
    - **Action:** Keep the third gate outcome ('link OK, no payload'), labelled as a historical observation. Over Europe, imagery is expected when Kiruna is in view.
    - **Impact:** Small.
    - **Sources:**
      - https://github.com/SatDump/SatDump/issues/854
      - https://www.a-centauri.com/articoli/beyond-poes-amateur-satellite-reception
  15.
    - **Claim in stack:** STACK Meteor HRPT patch tier (4-turn helix + SAWbird+ GOES): +1.5...+3 dB. Stage 1: the 1704.0 MHz spur in a 1705 MHz band can cost several dB. D10: a line 3 dB or more over the floor in the 2.3 Hz bin fails.
    - **Finding:** Stage 2 carries the helicone margin as +3...+9 dB. The helix is about 6.4-7.4 dB below the helicone in STACK's own numbers, so the patch-tier margin is about -4...+3 dB (model).
  CW-spur physics: a line X dB above the floor in a 2.3 Hz bin is X - 60.4 dB relative to noise in a 2.5 MHz HRPT band. Even X = 30 dB costs less than 0.01 dB of Es/N0. A CW spur near a wideband signal matters only by capturing the PM/PLL carrier loop: the 1700.000 MHz spur at the HRPT centre (25 MHz x 68 NIC, 100 MHz x 17, 10 MHz x 170) is the real risk. 1699.2 and 1704.0 MHz are not blockers. D10's 2.3 Hz criterion fits CW beacons, Inmarsat 1200 sym/s near the carrier, and H1.
    - **Verdict:** corrected
    - **Action:** Rate the patch tier 'on the edge to unreachable (-4...+3 dB, model)'. For HRPT and AHRPT, judge spurs by integrated in-band power, which must be at least 20 dB below noise in the band, plus 'no line within +/-50 kHz of 1700.000 MHz above the floor + 10 dB' with pcie0 and GPSDO off. Remove the 1704.0 item from the HRPT gate.
    - **Impact:** Removes a false blocker and gives the patch tier an honest rating.
    - **Sources:**
      - https://www.a-centauri.com/articoli/easy-hrpt-guide
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Meteor-M.json
  16.
    - **Claim in stack:** Stage 2: build gr-satellites main at 1bcf1d8 or later, 'or v5.9.0 plus 10d27cb and 71dc9a1'.
    - **Finding:** 71dc9a1 is not a revision in the repository. The fix pair is 10d27cb plus 1bcf1d8. main (4210dc4, 22 Sep 2026) also adds 45b146f (Viterbi error-path free) and 882e503 (BCH uint8 overflow).
  Residual case: a filename of '..' passes the check, since Path('..').parent == Path('.'). File(path/'..') then raises an error when it tries to open a directory (a crash, not a write).
    - **Verdict:** corrected
    - **Action:** Build main 4210dc4 (5.10.0-git) as a +labN deb against noble's GNU Radio 3.10.9.2, or v5.9.0 with 10d27cb and 1bcf1d8 cherry-picked. Use a sandboxed systemd unit as stage 2 said. CI feeds the filenames '../x', '/etc/x', '..' and 'a/b'.
    - **Impact:** The stage-2 cherry-pick recipe would have failed.
    - **Sources:**
      - https://github.com/daniestevez/gr-satellites/commit/10d27cb
      - https://github.com/daniestevez/gr-satellites/commit/1bcf1d8
      - https://github.com/daniestevez/gr-satellites/commits/main
  17.
    - **Claim in stack:** Stage 1: label SBAS as 'any PRN 120-158 the receiver reports, labelled by system, no hard-coded list'. Stage 2: the LC76G loses its config on power loss (Waveshare).
    - **Finding:** Labelling by system needs a PRN-to-system table; that is assignment data, not a location table, so the rules allow it. gpsd reports SBAS as gnssid 1, svid 120-158. The Waveshare 'reverts on power loss' FAQ is about the L76, not the LC76G. Its wiring tables show PPS as NC. The user set SBAS = EGNOS (PRN 121/123/136); SDCM may also appear in eastern Europe.
    - **Verdict:** corrected
    - **Action:** labd labels SBAS from gpsd SKY (gnssid 1) using a versioned PRN-to-system table, with unknown PRNs shown as 'SBAS PRN n'. Re-applying the LC76G config at boot stays as cheap insurance. PPS wiring is confirmed by the GNSS owner. Pin gpsd at 3.25-3ubuntu3.2 or later.
    - **Impact:** Small.
    - **Sources:**
      - https://gpsd.gitlab.io/gpsd/gpsd_json.html
      - https://www.waveshare.com/wiki/LC76G_GNSS_Module
      - https://egnos.gsc-europa.eu/node/12832
      - https://launchpad.net/ubuntu/+source/gpsd
  18.
    - **Claim in stack:** STACK 4.1: Meteor-M N2-4 LRPT 'QPSK 72k'.
    - **Finding:** The SatDump meteor_m2-x_lrpt pipeline is OQPSK 72000 sym/s with NRZ-M, k=7 Viterbi and RS 223 interleave 4. The 80k pipeline uses meteor_lrpt_decoder (interleaved, differential).
    - **Verdict:** corrected
    - **Action:** Write 'OQPSK 72k (SatDump meteor_m2-x_lrpt), fallback 80k interleaved (meteor_m2-x_lrpt_80k)'.
    - **Impact:** Labelling only.
    - **Sources:**
      - https://raw.githubusercontent.com/SatDump/SatDump/master/resources/pipelines/Meteor-M.json
  19.
    - **Claim in stack:** STACK QO-100 rows: 'region-gated (LNB in the optional kit)'. Stage 1/2: the margin constant is unverified.
    - **Finding:** The user confirmed Europe on 18 Oct. Es'hail-2 is at 12-46 deg elevation across Europe (model), so the LNB kit is bought. AMSAT-DL still publishes no beacon EIRP and no dish size. The 739.5 MHz IF sits inside the European LTE B28 uplink (703-748 MHz).
    - **Verdict:** corrected
    - **Action:** Turn the QO-100 rows from region-gated to active (Europe). Keep the conservative model, and make the A/B test the source of the constant. Add 'LTE B28 uplink near the IF' to the CW-beacon row's risk.
    - **Impact:** Status update.
    - **Sources:**
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
  20.
    - **Claim in stack:** Stage 1/2: mask the TDF 162 kHz Tuesday 08:00-12:00 gap.
    - **Finding:** Wikipedia gives 'every Tuesday from 08:00 to 12:00' without a time zone. If that is local time, it is 06:00-10:00 UTC (CEST) or 07:00-11:00 UTC (CET).
    - **Verdict:** corrected
    - **Action:** Mask Tuesday 06:00-12:00 UTC, the union of the readings, and refine it from on-air logs.
    - **Impact:** Avoids false SID events.
    - **Sources:**
      - https://en.wikipedia.org/wiki/ALS162_time_signal
  21.
    - **Claim in stack:** STACK S-band rows: 'Lime only if kept'.
    - **Finding:** The user kept the Lime, so these rows are the default build. Black Kite-1 and -2 have SatNOGS IDs 98527 and 98371, which are in SatNOGS's temporary 9xxxx range, so TLE availability for pass prediction is a risk.
    - **Verdict:** corrected
    - **Action:** Make S-band rows default (opportunistic). Schedule S-band passes only for allow-listed objects (Black Kite-1/2, PHASMA-LAMARR/DIRAC). The pass planner never offers other 2200-2300 MHz objects.
    - **Impact:** Status update plus a compliance guard.
    - **Sources:**
      - https://db.satnogs.org/api/satellites/BMYD-8328-6159-7072-4807/
      - https://db.satnogs.org/api/satellites/PKWP-7958-4818-1008-2291/
  22.
    - **Claim in stack:** Stage 2 dates the IU1QPR guides as '2026'.
    - **Finding:** Version and date details:
  - 'Beyond POES': refers to Elektro status 'as of August 2025' and to an upcoming launch on 22 Oct 2025, so it was written about Sep-Oct 2025 (footer © 2026).
  - HRPT guide: v1.0.2.
  - Meteor guide: v1.0.1.
  - Neither guide is dated.
    - **Verdict:** corrected
    - **Action:** Cite them as 'IU1QPR, 2025-2026, undated versions'.
    - **Impact:** Citation accuracy.
    - **Sources:**
      - https://www.a-centauri.com/articoli/beyond-poes-amateur-satellite-reception
  23.
    - **Claim in stack:** Metop-B 'intermittent modulator losses of about 7 dB'.
    - **Finding:** Not found in OSPO, SatDump issues or IU1QPR. Web search was unavailable in this pass (shared search budget used up), so no EUMETSAT notice could be searched.
    - **Verdict:** unverified
    - **Action:** Keep it out of the margin. Measure the Metop-B C/N0 envelope across a pass on the bench.
    - **Impact:** Small.
    - **Sources:**
      - https://www.ospo.noaa.gov/operations/metop/status.html
- **New risks:**
  - SatDump pipelines that use only core modules (Syracuse-3 TLM, Cosmos-2558, Gazelle/OTB-3, Cosmos-2518, Chinese spaceplane, PAZ) run whatever plugins are built. Only removing the JSON files and keeping user-supplied pipelines.json out of the working and user directories stops them.
  - With the Lime kept, the S-band chain (7-turn helix, cf2235-kt30 2170-2300 MHz, Lime) covers DMSP and WSF-M (2252.5), Cosmos-2558 (2284) and PAZ (2285 MHz). The guard is a NORAD allow-list in the pass planner plus the pipeline deny audit.
  - Region Europe: Elektro-L5 and FY-2H are below the horizon or under 2 deg from Lisbon, Dublin, London, Madrid and Paris, and only 6-12 deg from Berlin, Rome, Warsaw and Helsinki (model). Western Europe has no LRIT/FY-2 target unless Elektro-L3 is commissioned at 14.5W.
  - SatDump's default config fetches OMM/TLE over plain HTTP (orbicentral.net) at every launch. Without kepler_update_interval 'Never' and PrivateNetwork=yes, field units would try the network and home runs would use unauthenticated ephemeris.
  - The SatNOGS ISS transmitter list carries active voice entries (Soyuz, suit, EVA, EMU), Dragon/Falcon telemetry and ICARUS. A denylist importer would bring them into profiles.
  - 145.800 MHz SSTV watch overlaps ARISS crew-contact voice on the same downlink.
  - egc-gate header misparse: a long descriptor shifts the service-code offset to byte 3. SatDump's own parser assumes byte 2.
  - gr-satellites FileReceiver: a filename of '..' still passes the 1bcf1d8 check and crashes the receiver. This is denial of service, not a file write.
  - Black Kite-1/2 have only temporary SatNOGS catalogue numbers, so TLEs for pass prediction may be missing or stale.
  - The 1700.000 MHz self-spur sits at the Meteor HRPT residual-carrier frequency, where it can pull the pm_demod PLL on weak passes. This is the HRPT spur that matters, not 1699.2 or 1704.0.
- **Refuted findings:**
  1.
    - **Finding:** Stage 1: the 1704.0 MHz self-spur inside a 1705 MHz HRPT band 'can cost several dB'.
    - **Why:** Nobody uses 1705 MHz (SatDump, IU1QPR, SatNOGS all use 1700). Also, a CW line even 30 dB above the floor in a 2.3 Hz bin is about -30 dB relative to noise in a 2.5 MHz band, which is negligible. Only PLL capture near the carrier matters.
  2.
    - **Finding:** Stage 1: add GOES HRIT, GK-2A LRIT and FY-4A LRIT region rows (and their plugins).
    - **Why:** The user region is Europe. GK-2A and FY-4B are not visible, and GOES-East reaches at most about 10 deg from Iberia and is below the horizon east of Paris (model). These belong in an optional travel profile, not the default build.
  3.
    - **Finding:** Stage 2: add FY-2G at 99.2E as a redundant reference for when FY-2H goes silent.
    - **Why:** FY-2G is at -22 to +4.7 deg elevation across Europe (model), so it cannot back up FY-2H for this user.
  4.
    - **Finding:** Stage 2: Elektro GGAK is about 10.7 dB easier than LRIT.
    - **Why:** With LRIT's real requirement (Eb/N0 about 2.5 dB on info bits, about 53.6 dB-Hz) against uncoded BPSK (8.4-9.6 dB, 45.4-46.6 dB-Hz), the advantage is 7.0-8.2 dB, before any PM carrier-power loss.
  5.
    - **Finding:** Stage 2: in #600 the 65 cm dish at 3-4 dB SNR gave CRC errors and misaligned segments, so remove +1 dB as a threshold.
    - **Why:** Those errors were a SatDump regression (MAX_SPS and rtlsdr buffer) fixed by PR #616; afterwards perfect images were reported below 3 dB. The maintainer's 'under 1 dB on paper' supports keeping about +1 dB as the theoretical threshold.
  6.
    - **Finding:** Stage 2: build SatDump's rtlsdr source plugin against the +lab librtlsdr.
    - **Why:** SatDump decodes offline from labrx recordings, so it needs no SDR source plugin. Building one would create a second SDR opener that bypasses the bias-tee token and the labrx masks.
  7.
    - **Finding:** Stage 2: gr-satellites cherry-pick 'v5.9.0 + 10d27cb + 71dc9a1'.
    - **Why:** 71dc9a1 does not exist in the repository. The needed second fix is 1bcf1d8.
  8.
    - **Finding:** Stage 2: egc-gate keeps 'frame ID 0x30/0x31/0x32' and reads the service code from byte 2.
    - **Why:** These are 6-bit descriptor types (raw first byte 0xB0-0xB2 or 0xF0-0xF2), and the service code sits after a 2- or 3-byte descriptor. Matching raw bytes would never match.
  9.
    - **Finding:** Stage 2: the LC76G loses its configuration on power loss (Waveshare wiki).
    - **Why:** The wiki FAQ says this of the L76, not the LC76G. Re-applying the config at boot is still fine as insurance.
  10.
    - **Finding:** Stage 2: Elektro-L3 'had not stopped at 14.5W' per the 9 Oct TLE.
    - **Why:** At that epoch it was still 7.8 deg short of 14.5W and on schedule for about 12 Oct, so the TLE cannot show a missed stop. Its status is simply unknown.
  11.
    - **Finding:** Stage 2: the ARISS SSTV image gallery is offline.
    - **Why:** The ARISS upcoming-events page has no such notice. Its only outage note (15 Nov 2025) is about transmissions. The claim remains unconfirmed.
  12.
    - **Finding:** Stage 1: STACK's 'with Soapy' SatDump build.
    - **Why:** In SatDump master, PLUGIN_SOAPY_SDR_SUPPORT is OFF by default and labelled 'NOT RECOMMENDED', and nothing in the stack needs it.
- **Corrected spec:** TARGET CATALOGUE AND LINK BUDGETS (18 Oct 2026; region Europe; Lime kept). All margins are models unless marked 'on air'.
  
  137 MHz
  - Meteor-M N2-4 LRPT. 137.900 MHz (backup 137.100). OQPSK 72k, pipeline meteor_m2-x_lrpt; fallback meteor_m2-x_lrpt_80k.
    - V-dipole: 53.4 cm legs, 120 deg, axis N-S, 1-1.1 m above ground.
    - Capture: 1.024 Msps, RTL and tuner AGC off, DC block on.
    - Rating: reliable. On air: SatNOGS decodes from 18 deg max elevation on fixed stations.
    - Wrapper: if 72k gives sync but no products, re-run products on the CADU after dd bs=8192 skip=4 (#1212).
  - Meteor-M N2-3 LRPT. Same frequency and settings.
    - Rating: on the edge, with fades. Fixed stations decode from 22 deg; the V-dipole is expected to need about 25-35 deg (estimate).
    - The -3...-6 dB figure is a community estimate. Replace it with N2-3 vs N2-4 SatDump SNR on similar passes.
  - No APT. NOAA-15/18/19 ended 19.08/06.06/13.08.2025. Meteor-M N2-5: 2027 or later.
  
  L-band polar
  - Meteor HRPT. 1700.000 MHz only; 1705 MHz is a power-only fallback check. Pipeline meteor_hrpt (pm_demod, 665.4 ksym/s). Capture: RTL-B at 2.4 Msps, or Lime.
    - Helicone + SAWbird+ GOES: reliable (model, +3...+9 dB; community says 'easily receivable on a portable helicone'). First passes from a tripod above 40 deg.
    - 4-turn helix: on the edge to unreachable (-4...+3 dB, model).
    - Spur gate: integrated in-band spur power at least 20 dB below noise; no line within +/-50 kHz of 1700.000 MHz above floor + 10 dB, with pcie0 and GPSDO off.
  - Metop-B and Metop-C AHRPT. 1701.3 MHz, QPSK 2.333 Msym/s, metop_ahrpt.
    - Patch tier: unreachable. Helicone: on the edge (experiment).
    - OSPO lists B 'Yes' and C 'No'; C has one community decode (Athens, Aug 2026).
    - SDR: V4L at 2.88 Msps with DC block (82% of the band) until the Lime arrives; then Lime at 6 Msps or more, ci16. The Airspy Mini is dropped.
    - The 7 dB modulator-loss figure is unverified and not in the budget.
  - AWS PFM. 1707 MHz, QPSK 1.785 Msym/s, aws_pfm.
    - Helicone: on the edge. Same SDR plan; the 2.59 MHz band fits 2.88 Msps.
    - Gate outcomes: decode / 'SYNC but filler: link OK, no payload' / fail. Over Europe, dumps are expected while Kiruna is in view.
  - FengYun-3: unreachable (X-band 7.8 GHz; FY-3C ended 28.11.2024).
  
  GEO L-band. Elevation comes from the GNSS fix and the live TLE. A target is listed only if its TLE is stationary (|n - 1.00274| < 0.0005 rev/day) and its elevation is at least 5 deg.
  - Inmarsat-C NCS: the primary reference for all of Europe (Alphasat at 24.9E is at 12-46 deg).
  - Elektro-L5 (76.05E). GGAK first: 1693 MHz, PM 5 ksym/s, elektro_ggak, success = frame sync + CADU count, about 7-8 dB easier than LRIT (model). Then LRIT: 1691 MHz, BPSK 294 ksym/s (128.5 kbps info), 1 Msps capture, success = sync + CRC-valid segments, expected SNR -2...+4 dB on the helicone (model).
    - Only eastern and central Europe (about east of 13E; Berlin 7.6, Warsaw 12.0, Athens 20.6 deg). Below or near the horizon from Lisbon, Dublin, London, Madrid and Paris.
  - FY-2H (79.2E). Carrier only: 1687.5 MHz S-VISSR first, then 1690.5 MHz; linear, -3 dB on RHCP. Same longitude limit.
  - Elektro-L3: target automatically if it becomes stationary near 14.5W (would be 8-45 deg over Europe). Elektro-L2 at 14.5W: L-band carrier check only (unknown).
  - FY-2G, GK-2A, FY-4B, GOES: not in the Europe build (optional travel profile).
  
  Inmarsat-C EGC SafetyNET
  - Patch tier: RTL-SDR Blog L-band patch ($59.95) to RTL-B. Profile disabled until egc-gate passes.
  - Power-only NCS scan over 1537.0-1543.9 MHz. Demodulation is masked from 1544.0 MHz upward; 1544.0-1545.0 MHz is a no-demod / no-data band for every satellite.
  - egc-gate:
    1. Decode the descriptor (medium = 10xxxxxx, long = 11xxxxxx; type = byte0 & 0x3F).
    2. EGC types are 0x30, 0x31, 0x32. The service code is at offset 2 (medium) or 3 (long).
    3. Accept only {0x04, 0x13, 0x14, 0x24, 0x31, 0x34, 0x44, 0x73}. Drop all System codes {0x00, 0x11, 0x23, 0x33} and FleetNET {0x02, 0x72}.
    4. Decide on the first fragment of 0x3D/0x3E multiframe packets (inner descriptor at byte 2).
    5. Verify the 2-byte checksum only on accepted packets. Never copy or CRC rejected packets.
    6. The frame decoder is derived from SatDump module_stdc_decoder. No pkt_parser, egc_parser or msg_parser; no SatDump inmarsat_support or SDRangel demodinmarsat.
  - SAWbird+ iO only after egc-gate passes.
  
  ISS
  - SSTV: 437.550 primary; 437.825 and 145.800 secondary. Robot 36 or PD120 via slowrx. Event frequencies from the ARISS page and the SatNOGS cache.
  - 145.800 MHz: record only inside announced SSTV windows, with the voice mask applied; it is also the crew-contact voice downlink.
  - Series 34 (22-25 Oct 2026, 437.55 MHz) is the first on-air validation: tilted vs vertical whip A/B and measured CNR. Model CNR at 10 deg: 13.3 dB or more (5 W, 600 K).
  - APRS 437.825: expected off during SSTV events (same Zvezda radio).
  - FM repeater 437.800: listen only, no IQ.
  - HamTV 2395 MHz: Lime carrier check only.
  
  CubeSats and amateur satellites
  - CubeSat 1 W 9k6, patch tier: -5.8...+4.8 dB (600 K) to -2.8...+7.8 dB (300 K) over 10-90 deg; passes above about 30 deg. Folding Yagi: reliable.
  - Decoders: gr-satellites main 4210dc4 (5.10.0-git) as a +labN deb, or v5.9.0 + 10d27cb + 1bcf1d8. Never 5.5.0 or plain 5.9.0. Sandboxed systemd unit with ProtectHome=yes and ReadWritePaths set to the output directory.
  - AO-73: telemetry only. JO-97: 145.840 MHz, EIRP is a model.
  - Beacons AO-7 / RS-44 / FO-29 and SO-50 as in STACK. AO-91: 'rarely active' (2 of 8 heard), removed from the test plan.
  
  S-band (Lime kept, so this is the default; opportunistic)
  - Black Kite-1 2288 MHz and Black Kite-2 2286 MHz, GMSK 38k4. PHASMA-LAMARR and DIRAC 2210/2208 MHz.
  - Chain: 7-turn helix, cf2235-kt30, Lime. The pass planner schedules only these NORAD IDs.
  - PHASMA UHF 400.55/400.60 MHz FSK 50k: folding tier only, budget not modelled.
  
  QO-100 NB (Europe, 12-46 deg; LNB kit bought)
  - Bare LNB: CW beacon at 10489.500 MHz (IF 739.5 MHz).
  - Cone: PSK beacon (10489.750 MHz) on the edge.
  - Horn 21/23 dBi: beacons and beacon-level SSB.
  - DATV and typical SSB are unreachable.
  - The constant comes from the A/B test. IF risk: LTE B28 uplink.
  
  GNSS
  - LC76G to gpsd (3.25-3ubuntu3.2 or later from noble-security) to chrony.
  - SBAS = EGNOS (PRN 121 and 136 operational per the Aug 2026 report). Labels from gpsd SKY gnssid 1 / svid 120-158 via a versioned PRN-to-system table.
  - LC76G configuration re-applied at boot.
  
  Terrestrial
  - Unchanged, except: the TDF 162 kHz mask is Tuesday 06:00-12:00 UTC.
  - NAVTEX on 490/518/4209.5 kHz (Europe). The US profile stays 'check on air'.
  
  SATDUMP BUILD AND RUN
  - Source: master 1aedd60 with c0b6f88 and 6b5957f cherry-picked (96bb626 optional).
  - cmake:
    - -DBUILD_GUI=OFF -DBUILD_TOOLS=OFF -DBUILD_TESTING=OFF -DBUILD_OPENCL=OFF
    - -DPLUGINS_ALL=OFF -DPLUGIN_METEOR=ON -DPLUGIN_NOAA_METOP=ON -DPLUGIN_AWS=ON -DPLUGIN_ELEKTRO_ARKTIKA=ON -DPLUGIN_XRIT=ON -DPLUGIN_FY2=ON
    - Every sdr_sources plugin OFF, by name: AIRSPY, HYDRASDR, AIRSPYHF, HACKRF, LIMESDR, SDRPLAY, PLUTOSDR, BLADERF, LITEXM2SDR, USRP, RTLSDR, MIRISDR, SPYSERVER, RTLTCP, SDRPP_SERVER, AARONIA, RFNM, FOBOSSDR, NET_SOURCE, REMOTE_SDR, SOAPY, SDDC
    - -DPLUGIN_EXPERIMENTAL_DEVICES_SUPPORT=OFF -DPLUGIN_TOOLS_APP=OFF -DPLUGIN_WEBHOOK_APP=OFF -DPLUGIN_PORTAUDIO_SINK=OFF -DPLUGIN_AAUDIO_SINK=OFF
    - CMAKE_INSTALL_RPATH set to the plugin directory.
  - Package: pipelines Meteor-M.json, MetOp.json, AWS.json, FengYun-2.json and Elektro_Arktika.json (with elektro_ggak_mqtt removed); nothing else.
  - Config: kepler_update_interval 'Never'; TLE/OMM file supplied by labd.
  - Pass unit:
    - One time-bounded systemd-run per pass; dedicated user.
    - Empty WorkingDirectory; no pipelines.json in the working or user directory.
    - PrivateNetwork=yes, LC_ALL=C.UTF-8.
    - CLI always uses '--key=value'.
    - Fail the unit on 'CALCEPH ERROR'.
    - No autotrack, no satdump_sdr_server.
  - CI:
    - Deny-regex audit of pipeline IDs.
    - ldd shows no SDR or network libraries.
    - One offline decode per allowed pipeline on arm64.
  
  CATALOGUE HYGIENE
  - SatNOGS importer is an allow-list on (NORAD, frequency +/- 10 kHz, mode).
  - Second layer: deny 1544-1545 MHz, 406.0-406.1 MHz and names matching SARSAT/Cospas/ARGOS/DCS/relay/voice/suit/EVA/Soyuz.
  - Exclusion table adds:
    - 'Cospas-Sarsat 1544.0-1545.0 MHz'
    - 'SatDump pipelines not packaged: Syracuse, Cosmos-2558/2518, DMSP, WSF-M, PAZ, Chinese spaceplane, ANGELS, Gazelle, Yunhai, Orbcomm, Inmarsat STD-C/Aero, Analog, Ominous, SpaceX, network-output (_tcp/_udp/mqtt) pipelines'
- **Bench tests:**
  - SatDump packaging audit on the arm64 build: list every loaded pipeline ID (satdump with a trace log) and fail if any matches the deny regex. Place a crafted pipelines.json defining syracuse3_tlm in the working directory and in the user directory, and confirm the pass unit refuses or ignores it.
  - SatDump CLI on the pinned build: decode a stored Meteor 72k baseband with '--samplerate=1024000 --baseband_format=cu8' and with '--samplerate 1024000'. Both must work after c0b6f88. Separately test whether '--k=v' alone works on unpatched 1aedd60.
  - SatDump network check: run a pass unit with PrivateNetwork=yes and kepler 'Never', strace -f -e trace=connect, and expect zero connect() calls. TLEs load from the labd file.
  - Series 34 (22-25 Oct, 437.55 MHz): IQ record, slowrx decode, measure CNR per elevation, and A/B the tilted vs vertical whip. Compare against the model (13.3 dB or more at 10 deg).
  - Meteor N2-4 vs N2-3 on the V-dipole: 5 passes each at matched maximum elevations. Log SatDump SNR, the elevation where sync is first gained and lost, and the 72k/80k/skip=4 fallbacks. This replaces the -3...-6 dB estimate.
  - HRPT spur gate: 60 s IQ at 1700 MHz, 2.4 Msps, lid closed. Measure integrated spur power in 1698.75-1701.25 MHz relative to noise (pass at -20 dB or lower), and any line within +/-50 kHz of 1700.000 with pcie0 and GPSDO on and off.
  - Meteor HRPT helicone vs 4-turn helix on passes above 40 deg from a tripod: SatDump SNR and the deframer sync percentage. Gives the real helicone margin (+3...+9 dB model) and the patch-tier figure (-4...+3 dB model).
  - Metop-B and Metop-C on 1701.3 MHz and AWS on 1707 MHz: V4L at 2.88 Msps with DC block now, then Lime at 6 Msps ci16 after delivery. Record the hump C/N0, sync and the AWS fill ratio. Run a 15-minute zero-drop Lime capture at 6 Msps as an acceptance item.
  - GEO visibility self-test: feed fixes for Lisbon, Paris, Berlin and Athens and check that labd hides Elektro-L5/FY-2H below 5 deg. Check that Elektro-L3 appears only when its live TLE is stationary.
  - Elektro-L5 GGAK on 1693 MHz from an eastern/central European site with the helicone: frame sync and CADU count. Then LRIT on 1691 MHz at 1 Msps: SNR and CRC-valid segments. From western Europe, run a power-only check on 1691/1693 MHz toward 14.5W (L2/L3).
  - egc-gate unit tests: synthetic medium and long EGC packets, multiframe start/continue packets, a bad checksum, and every service code. Mixed-recording test: no byte of a non-SafetyNET packet reaches disk, text or screen, and no carrier at or above 1544.0 MHz is demodulated.
  - SatNOGS importer test against the live ISS, Metop-C, Elektro-L5 and Meteor transmitter lists: only allow-listed rows import; Soyuz, suit, EVA, EMU, Dragon, Falcon, ICARUS, ARGOS, 465 MHz relay and SARSAT rows are rejected.
  - gr-satellites sandbox test: replay a crafted FileReceiver frame with filenames '../x', '/etc/x', '..' and 'a/b'. Expect writes only inside the output directory and no unhandled crash, or a supervised restart.
  - QO-100 A/B (bare LNB, cone, 3 and 6 segments): log C/N0 of the 10489.500 MHz beacon to set the conservative constant, and log the LTE B28 level at the 739.5 MHz IF.
  - SBAS labelling: confirm gpsd SKY shows gnssid 1 for PRN 121/123/136 within 10 minutes of a cold start, and that labels survive a power cycle with config re-applied at boot.
  - ALS162 at 162 kHz: log amplitude for 4 Tuesdays to find the real maintenance window in UTC, then narrow the 06:00-12:00 UTC mask.
- **Confidence:** medium

