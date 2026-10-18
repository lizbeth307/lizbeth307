# Antennas foldable: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_d3593e9c-5ce`_

- **Subsystem:** antennas_foldable (telescopic V-dipole for Meteor LRPT; foldable crossed 2 m/70 cm Yagi; L-band petal helicone and shared helix; QO-100 bare Bullseye LNB, 11 cm clamp cone and gore horn; packed sizes, gains, build steps without on-air S11)
- **Findings:**
  1.
    - **Claim in stack:** V-dipole LRPT = RTL-SDR Blog multipurpose dipole kit #1, $17.95, 357 in stock, 23 cm collapsed, up to 1 m, M5 thread; arms 53.4 cm, 120 deg, axis N-S
    - **Finding:** Product page (18 Oct 2026): SKU 3, USD 17.95, '357 in stock'. Two large telescopics 23 cm to 1 m (5 sections), two small 5-13 cm, M5 thread into base, 1/4in camera thread, 60 cm RG174 base lead plus 3 m RG174. The vendor's 137 MHz V-dipole recipe is 53.4 cm per arm, 120 deg, V pointing N-S; about 2 cm of element sits inside the base. No new revision. A May 2026 libre.space V-dipole paper (Meteor M2-4 decodes on RTL-SDR V4) gives the same about 53.4 cm arm and a 1.087 m height.
    - **Verdict:** confirmed
    - **Action:** Keep. Mark the 53.4 cm extension on the tube; carry one spare telescopic pair (unchanged).
    - **Impact:** Part, price, stock and packed size (23 cm) are confirmed. This meets the 20-23 cm rule.
    - **Sources:**
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-multipurpose-dipole-antenna-kit/
      - https://www.rtl-sdr.com/DIPOLE
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://community.libre.space/t/mathematical-modeling-and-physical-optimization-of-v-dipole-antennas-for-vhf-imaging-satellite-reception/14844
  2.
    - **Claim in stack:** V-dipole 'NEC 3.0 dBi at zenith, SWR 1.47' while mounted 1-1.1 m above ground; M2-3 'expect only above about 40-60 deg'
    - **Finding:** 3.0 dBi at zenith is a free-space figure; the foldable study itself labels it 'NEC2 free-space'. At 1.087 m, h is 0.50 lambda at 137.9 MHz, so a horizontal dipole has a ground-reflection null at zenith. My MODEL (straight half-wave dipole times Fresnel ground factor, average ground eps 13, sigma 5 mS/m) gives, in the broadside plane: +2.1/+6.3/+7.0/+4.7/-0.5/-4.8/-5.1 dBi at 10/20/30/45/60/75/90 deg. After the extra path loss relative to zenith (830 km orbit), the best elevations are 30-45 deg (+2 dB) and the worst is zenith (-5 dB). The libre.space paper confirms that 1.087 m puts the main lobe peak near 29.5 deg. At 0.5-0.75 m the net response rises toward zenith instead: +4.5 to +6 dB at 90 deg in the model.
    - **Verdict:** corrected
    - **Action:** Replace '3.0 dBi at zenith' with the over-ground pattern (model, +/-2-3 dB, real ground varies). Add a per-pass height rule: 1.0-1.1 m for passes peaking below about 50 deg, 0.5-0.75 m for passes peaking above about 60 deg. That matters most for Meteor-M N2-3, which the STACK expects only on high passes. Confirm with A/B passes (receive-only).
    - **Impact:** Without the change, high passes (the only ones useful for M2-3) land in the dipole's weakest region. No hardware cost: the tripod height changes.
    - **Sources:**
      - https://community.libre.space/t/mathematical-modeling-and-physical-optimization-of-v-dipole-antennas-for-vhf-imaging-satellite-reception/14844
      - https://www.rtl-sdr.com/DIPOLE
  3.
    - **Claim in stack:** Optional 2 m tape Yagi re-marked to 137.5 MHz gives about 7.7 dBi, '+6 dB vs the V-dipole' when pointed
    - **Finding:** The 7.7 dBi figure is a model and its arithmetic is consistent (WB2HOL lengths x1.060). The '+6 dB' assumes a free-space V-dipole. With the over-ground V-dipole pattern above (model), the pointed Yagi advantage depends on elevation: about 0-1 dB near 25-40 deg broadside, and up to about +10-12 dB near zenith. Both antennas are linear, so the 3 dB RHCP loss cancels out.
    - **Verdict:** corrected
    - **Action:** State the Yagi gain at 137.5 MHz as elevation-dependent. Use it mainly for high passes or for passes along the dipole's N-S end-fire plane.
    - **Impact:** Clarifies when carrying or using the Yagi for LRPT is worth it.
    - **Sources:**
      - https://www.w9rh.org/wp-content/uploads/2024/01/2m-tape-measure-yagi-instructions.pdf
  4.
    - **Claim in stack:** Meteor-M N2-4 LRPT 137.900 MHz (backup 137.100), QPSK 72k, observed 17-18.10.2026; M2-3 marginal
    - **Finding:** SatNOGS DB (18 Oct 2026): METEOR M2-4 (59051) is Operational. LRPT transmitters are listed at 137.9 / 137.1 / 137.9125 MHz in both 72k and 80k modes, plus HRPT at 1700/1705 MHz. Observers are logged 2026-10-17 12:27 UTC and 2026-10-18 03:50 UTC. METEOR M2-3 (57166) is Operational, with HRPT at 1700 MHz and observations on 2026-10-17. WMO OSCAR lists Meteor-M N2-5 as Planned, launch no earlier than 2027 (page updated 2026-01-23), so no new LRPT satellite arrives in 2026.
    - **Verdict:** confirmed
    - **Action:** Keep both 72k and 80k LRPT profiles in SatDump. Don't plan for N2-5 before 2027.
    - **Impact:** The target catalog for this tier is still valid in October 2026.
    - **Sources:**
      - https://db.satnogs.org/satellite/59051
      - https://db.satnogs.org/satellite/57166
      - https://space.oscar.wmo.int/satellites/view/meteor_m_n2_5
  5.
    - **Claim in stack:** Crossed Yagi 2 m half = WB2HOL 3-el: R 105.1 / DE 2x45.1 / D 89.2 cm at 145.8 (re-marked x1.060 to R 111.4, DE 2x47.8, D 94.6 cm for 137.5), positions 0 / 0.20 / 0.51 m, straight split DE with hairpin
    - **Finding:** The original WB2HOL page (theleggios.net) is offline (404/405). The W9RH copy of the instructions gives reflector 41-3/8 in (105.1 cm), driven element 2 x 17-3/4 in (45.1 cm), director 35-1/8 in (89.2 cm), a 3/4-1 in DE gap and a 5 in hairpin wire. Its boom tubes are 7 in and 11.5 in plus fittings, about 8 in and 12 in centre to centre, which matches 0.20 / 0.51 m. The x1.060 re-marked lengths check out arithmetically. The original builders tune by moving the DE ends with an SWR meter.
    - **Verdict:** confirmed
    - **Action:** Keep the lengths. Fix the DE gap at 0.75-1 in (19-25 mm) instead of SWR tuning: this is receive-only, and SWR 2 costs about 0.5 dB (calculation). Note in the build file that the original source is offline.
    - **Impact:** The dimensions are sound. Removing the SWR step keeps the no-S11 rule.
    - **Sources:**
      - https://www.w9rh.org/wp-content/uploads/2024/01/2m-tape-measure-yagi-instructions.pdf
      - https://nt1k.com/vhf-3el-tape-measure-yagi/
  6.
    - **Claim in stack:** 2 m tapes on 'Axotron v3' spools, free 3MF files, on a 20x20 mm square boom (ultracompact 5 pieces)
    - **Finding:** Axotron '2 m Fox Hunting Antenna v3' (Per Magnusson, published 2026-01-14). The zip 2m-antenna-v3.zip is online (764,141 bytes, last modified 2026-01-14) and contains 18 3MF parts and a drawing PDF; no license is stated. The design differs from the STACK in four ways. (1) The boom is 16 mm OD round PVC conduit (rear 347 mm, front 279 mm), not 20x20 mm square. (2) Axotron's own geometry is reflector 1041 mm, DE 2x466 mm (987 mm tip to tip), director 887 mm, spacing R-DE 373 mm and DE-D 266 mm. (3) It matches with a CX2041ANLT balun, not a hairpin. (4) Spool capacity is not documented, and the 137.5 MHz re-mark needs 55.7 cm reflector halves against Axotron's 52 cm.
    - **Verdict:** corrected
    - **Action:** Re-model the spool clamps for the 20x20 mm square boom (3MF is a mesh, so this means redrawing), or use a 16 mm round boom with keyed printed joints so the planes stay orthogonal within +/-5 deg. Verify that a spool holds 56 cm of 25 mm tape before relying on the 137.5 MHz marks. Add the hairpin pads to the driven clamp. Use the files for personal builds only, since no license is stated.
    - **Impact:** Mechanical fit risk for the default ultracompact Yagi. The electrical design is unaffected.
    - **Sources:**
      - https://axotron.se/blog/?p=1619
      - https://axotron.se/blog/wp-content/uploads/2025/02/2m-antenna-v3.zip
  7.
    - **Claim in stack:** 70 cm half = N2SPI 6-el (not 7): elements at 0.030/0.094/0.170/0.316/0.475/0.640 m, longest 34.0 cm (13-3/8 in), 11.0 dBi; straight split DE '0.95 x 13 in' with hairpin; half-elements no longer than 17 cm
    - **Finding:** AMSAT Journal Jul/Aug 2006, Table 3, gives positions from the wide end of D4 0.25, D3 6.75, D2 13, D1 18.75, DE 21.75 and REF 24.25 in. Lengths are 11, 12, 12, 12-3/8, 13 (folded DE) and 13-3/8 in. Measured from the reflector, that is 0 / 6.35 / 13.97 / 28.6 / 44.45 / 60.96 cm, which matches the STACK offsets exactly. There are 6 elements on 7 holes, because the folded DE uses two holes. The electrical design is WA5VJB's: his paper says 'NEC predicts 11.2 dBi for the 6 element' with about 30 dB F/B predicted. N2SPI publishes no gain. The straight split DE with hairpin is the STACK's own modification and has not been built.
    - **Verdict:** confirmed
    - **Action:** Keep. Label 11.0-11.2 dBi as NEC (WA5VJB/STACK). Treat the hairpin DE as unverified. Its acceptance test is receive-only (beacon or satellite C/N against the uncut folded-DE version if one is built).
    - **Impact:** Dimensions and gain basis are verified from primary sources. Half-elements of 17.0 cm meet the rule.
    - **Sources:**
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
      - https://wa5vjb.com/yagi-pdf/cheapyagi.pdf
  8.
    - **Claim in stack:** Ultracompact boom: 5 pieces with joints at 0.13/0.25/0.40/0.56 m, each piece 16 cm or shorter and at least 3.6 cm from any element
    - **Finding:** Recomputed against the element positions above (2 m at 0/0.20/0.51; 70 cm at 0.030-0.640): pieces are 13/12/15/16/14 cm. The nearest element to a joint is 3.6 cm (the 0.094 m DE at the 0.13 joint).
    - **Verdict:** confirmed
    - **Action:** None. The 3.6 cm clearance is the tightest point; keep metal ferrules away from the 70 cm DE.
    - **Impact:** Meets the rule that each piece is no more than 20-23 cm.
    - **Sources:**
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
  9.
    - **Claim in stack:** 2 m half optional because ISS SSTV is on 437.550 MHz (series 34 on 22-25.10.2026), APRS on 437.825 and FM down on 437.800
    - **Finding:** ARISS lists SSTV Series 34 'ARISS Hardware' for Thu Oct 22 to Sun Oct 25, 2026 on 437.55 MHz, Robot 36. All 2026 events use 437.550 MHz. The status page (7 Oct 2026) lists the FM repeater down on 437.800 MHz as active and the RS0ISS APRS digipeater on 437.825 MHz as 'active, still being troubleshot/tested'.
    - **Verdict:** confirmed
    - **Action:** Keep the 70 cm half as primary and the 2 m half as optional.
    - **Impact:** Confirms that the foldable kit's main use this month is the 70 cm half.
    - **Sources:**
      - https://www.ariss.org/upcoming-sstv-events.html
      - https://www.ariss.org/current-status-of-iss-stations.html
  10.
    - **Claim in stack:** DIY instead of commercial portable Yagis (Arrow and Elk fail the 35 cm piece limit)
    - **Finding:** Searches found no 2026 commercial 2 m/70 cm handheld Yagi with all parts 35 cm or shorter. The Arrow II, ARRL dual-band handheld, EAntenna DUOSAT and Elk LPDA either have no published folded length or have long elements.
    - **Verdict:** confirmed
    - **Action:** Keep the DIY design.
    - **Impact:** No better buy option exists.
    - **Sources:**
      - https://www.arrl.org/arrl-dual-band-2-m-70-cm-handheld-yagi-antenna
      - https://community.libre.space/t/collapsible-yagi-antennas/14441
  11.
    - **Claim in stack:** Petal helicone: 18 cm disc and 8 petals (6.9/16.8 cm, 17.7 cm slant), cone 18 to 44 cm, 12 cm deep; RHCP helix C=1.1 lambda (61.7 mm), pitch 43 mm, 2 mm Cu; 15.7 dBic, beam 24-28 deg (model)
    - **Finding:** The geometry checks out. At 1.70 GHz, C=1.1 lambda gives D 61.75 mm and the pitch is 0.244 lambda. The octagon chords are 6.89/16.84 cm and the edge slant is 17.7 cm. The aperture limit for 44 cm at 1.70 GHz is about 17.9 dBi at 100%, so 15.7 dBic implies about 60% aperture efficiency, the optimistic end for a short helix in a cone. No measured helicone gain exists anywhere. The field-proven reference geometry (t0nito, Thingiverse 6436342) is a 134 mm base, 440 mm top and 88 mm high (29.7 deg). It also folds into 8 petals of about 17.7 cm slant. The STACK's deeper cone models about +1.7 dB better but has not been built.
    - **Verdict:** unverified
    - **Action:** Budget 14-15.7 dBic in link budgets, not 15.7. Make the petal tabs allow both the t0nito angle and the deeper one, then A/B on NCS/GNSS C/N0 (receive-only).
    - **Impact:** The HRPT 'reliable (model)' and Metop/AWS 'marginal' margins may be about 1-2 dB lower.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
  12.
    - **Claim in stack:** 'No documented dishless hand-held HRPT decode' for the helicone
    - **Finding:** In the libre.space thread (pe2bz, 27 Jan 2024), a relayed report from the original Facebook group says 'nice Meteor images being received with this antenna' using a 'Nooelec GOES preamp and RTL device directly connected to the antenna, usually hand tracking'. This is second-hand but documented. The chain matches the STACK's (SAWbird+ GOES plus RTL).
    - **Verdict:** corrected
    - **Action:** Change the wording to 'second-hand report of hand-tracked Meteor HRPT with helicone plus Nooelec GOES plus RTL (2024); no gain measured'.
    - **Impact:** Raises confidence in the foldable HRPT path somewhat.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
  13.
    - **Claim in stack:** SAWbird+ GOES (100792) at the helix feed, powered over coax from injector ch3, serves HRPT 1700 MHz / AHRPT 1701.3 / AWS 1707
    - **Finding:** Nooelec page: USD 49.95. An '80 MHz bandpass region centered around 1.688 GHz' (about 1648-1728 MHz by inference) covers 1700-1707 MHz. Gain is at least 30 dB. Bias via the SMA port at 3-5 V, or micro-USB or header at 3.3-5.5 V (use one only). Nominal draw 180 mA.
    - **Verdict:** confirmed
    - **Action:** Keep. The 180 mA load fits the 300 mA nominal TPS2553 channel.
    - **Impact:** Compatible with the shared helix and helicone.
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-goes-302.html
  14.
    - **Claim in stack:** Othernet Bullseye TCXO LNB $29.95 (70 in stock); +/-10 kHz at 23 C, +/-30 kHz over -20..60 C, NF 0.5 dB; LO 9750; 13.2 V vertical only; close the 25 MHz port
    - **Finding:** RTL-SDR Blog product page (18 Oct 2026): 'Bullseye 10 kHz BE01', USD 29.95, 70 in stock. LO 9750/10600 MHz; internal 2 ppm TCXO in a PLL, factory-calibrated to 1 kHz; gain 50-66 dB; NF 0.5 dB; return loss 8 dB (low band); a 25 MHz reference OUTPUT on a second (red) F connector. Passion Radio: EUR 29.94 ex VAT, in stock but marked 'last items'. It lists vertical at 11.5-14 V, horizontal at 16-19 V and a 40 mm LNB support diameter. 13.2 V is therefore inside the vertical window.
    - **Verdict:** confirmed
    - **Action:** Keep. Fit a 75 ohm F terminator or a metal cap on the red 25 MHz output port. Keep the 15/20 dB pad because gain can reach 66 dB.
    - **Impact:** Part, specs and world price are confirmed. Two worldwide sources are in stock.
    - **Sources:**
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
      - https://www.passion-radio.com/lnb-pll/lnb-othernet-978.html
  15.
    - **Claim in stack:** 11 x 8.3 cm clamp cone and 6-gore horn start at a printed 40.2 mm clamp on the LNB neck (gore inner slant radius 84 mm, which is a 40 mm throat)
    - **Finding:** Passion Radio's Bullseye spec gives a 'LNB support diameter: 40mm' and a 'Red cover diameter: 64mm'. The feed cover in front of the 40 mm neck is therefore 64 mm wide. A cone with a 40 mm throat clamped at the neck reaches 64 mm only 28 mm forward (cone, 22.9 deg half-angle) or 49 mm forward (horn, 13.8 deg), so it collides with any feed cover that protrudes further. A 40 mm throat also matches neither the feed aperture nor the single-mode waveguide (16.75-21.88 mm). Gain depends on the apex position and mouth size, not on where the throat is cut. If the throat moves to the feed-cover plane (about 64-66 mm), the inner gore radius becomes about 134-138 mm instead of 84, the gores get shorter and the 21/23 dBi figures stay the same (model). The transition from the LNB's own feed is still unmodelled.
    - **Verdict:** corrected
    - **Action:** Before cutting anything, measure the cover protrusion and the feed aperture under the cover. Put the cone or horn throat ring at the feed aperture (about 64-66 mm or the measured value), held by a printed adapter onto the 40 mm neck. Recompute the inner gore radius as R_in = r_throat / sin(13.8 deg). Keep the 127/180 mm rings.
    - **Impact:** Without this, the printed parts as specified may not fit the Bullseye. This applies to both the patch-tier cone and the foldable horn.
    - **Sources:**
      - https://www.passion-radio.com/lnb-pll/lnb-othernet-978.html
      - http://www.w1ghz.org/antbook/chap3.pdf
  16.
    - **Claim in stack:** Horn: 6 gores, half-angle 13.8 deg, 3 per ring at 28.6 deg; inner set about 21 dBi, all 6 about 23 dBi; cone 11 x 8.3 cm about 18.8 dBi
    - **Finding:** Recomputed MODEL (Balanis conical-horn loss L(s)=0.8-1.71s+26.25s^2-17.79s^3, ideal walls, 10.4895 GHz, lambda 28.58 mm). Inner set: D 127.4 mm, L 267 mm, s 0.266, 21.06 dBi. Full horn: D 180.3 mm, L 378 mm, s 0.376, 23.02 dBi. Cone: half-angle 22.9 deg, L 142 mm, s 0.374, 18.75 dBi. The developed sector is 360 x sin 13.8 = 85.9 deg, so 3 gores of 28.6 deg. Flat gore bounding boxes are about 13.2 x 18.6 cm (inner) and 18.7 x 13.1 cm (outer) before tabs. Rings are 127/180 mm, axial length 286 mm. Every piece is 20 cm or less.
    - **Verdict:** confirmed
    - **Action:** Keep as model figures. Allow -0.2 to -0.5 dB for taped seams (unverified) and the unmodelled feed transition.
    - **Impact:** The STACK's gain numbers and packed sizes are internally consistent.
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap2.pdf
      - http://www.w1ghz.org/antbook/chap3.pdf
  17.
    - **Claim in stack:** Conservative QO-100 model: beacon C/N0 about G + 13...16 dB-Hz; bare LNB gives the CW beacon at +6...+9 dB in 50 Hz; 21/23 dBi horn gives PSK Eb/N0 8-13 dB
    - **Finding:** EA4GPZ (2019) measured the 400 Bd BPSK beacon at 'around 45 dB-Hz' on a 95 cm dish he describes as off focus, 'comparable to a 60 cm dish' (about 33-34 dBi). That implies about G + 11...12 dB-Hz, 1-5 dB below the STACK's 'conservative' model. Applied to the STACK's cases, this gives about +2...+6 dB for the bare-LNB CW beacon in 50 Hz, and PSK Eb/N0 of about 6-7 dB (21 dBi) or 8-9 dB (23 dBi). This is a single 2019 data point with an estimated dish gain. No published horn-only or bare-LNB C/N0 measurement was found, only anecdotes.
    - **Verdict:** new_risk
    - **Action:** Derate the planning model to G + 11...16 dB-Hz. Call the bare-LNB CW beacon 'marginal to probable' and decide using the A/B C/N0 test (bare / cone / 3 gores / 6 gores) after the region gate.
    - **Impact:** The patch-tier PSK beacon with the cone and SSB at beacon level with the horn may drop from marginal to not reachable.
    - **Sources:**
      - https://destevez.net/2019/03/qo-100-beacons-power/
      - https://forum.batc.org.uk/viewtopic.php?p=36476
  18.
    - **Claim in stack:** Beacons 10489.500 (CW/FSK) and 10489.750 MHz (BPSK 400 bit/s), IF 739.500/739.750; '10489.55 MHz' is an error
    - **Finding:** The AMSAT-DL NB bandplan confirms: lower beacon 10489.500 CW (F1A), middle beacon 10489.750 BPSK 400 bit/s, multimedia beacon 10489.9935 8APSK 7200 bit/s, upper/experimental beacon 10490.000 CW. Downlink is vertical linear. SatNOGS DB still lists the pre-2020 frequencies 10489.550 and 10489.795. The upper beacon's IF of 740.000 MHz coincides with the GPSDO x74 spur that STACK section 5.7 already lists at 740.000 MHz.
    - **Verdict:** confirmed
    - **Action:** Take frequencies only from AMSAT-DL (not SatNOGS) in qo100_beacon_track.py. Use the 10490.000 beacon as a third A/B reference only with the GPSDO off.
    - **Impact:** Avoids tracking a wrong beacon and avoids confusing a spur with the beacon.
    - **Sources:**
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
      - https://db.satnogs.org/satellite/43700
  19.
    - **Claim in stack:** Upgrade path: QRO.cz LNB (0.2 ppm)
    - **Finding:** WiMo lists QRO.cz QO-100 LNBs 'as low as EUR 65.00 incl. VAT' (in stock, plus EUR 54.62 shipping). It has a 25 MHz 0.2 ppm TCXO, IF 432 or 739/618 MHz and an optional 10 MHz reference on the bias-T version. The polarity voltages are '12 V: hor, 15 V: vert. Pol.', the reverse of a standard LNB. On the STACK's 13.2 V-only bus it would probably select horizontal (the threshold is not published). A 4S pack through the TPS7A4701 LDO cannot hold 15 V near empty (about 12-13 V).
    - **Verdict:** new_risk
    - **Action:** If upgrading, order the 739 MHz version and plan to rotate it 90 deg (receive vertical on its horizontal probe at 12-13.2 V), or add a separate boost to 15 V. Otherwise keep the Bullseye. State this in the BOM note.
    - **Impact:** Without the note, the upgrade would silently receive the wrong polarization, roughly a 20 dB or larger loss on NB.
    - **Sources:**
      - https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz
  20.
    - **Claim in stack:** Travel tripod 35 cm or shorter folded, from 1.2 m, mini pan head, 1/4-20, $40-100 (model, no model named)
    - **Finding:** Two concrete candidates appeared, both from retailer snippets. Manfrotto BeFree One Aluminium: 32 cm closed, 130 cm max with column, EUR 119.95 sale. Rollei Compact Traveler No. 1: 31.5 cm folded, 134 cm max, 1/4 in screw, price not found. The $40-100 range may be low for a branded tripod that meets 32 cm.
    - **Verdict:** new_option
    - **Action:** Name one model in the BOM and re-price it in P5 (unverified). Check the head type (ball vs pan) and payload for the horn and helicone.
    - **Impact:** Turns a generic line into a sourceable part.
    - **Sources:**
      - https://bigbearsound.com/products/manfrotto-befree-one-aluminium-travel-tripod-with-head-black
      - https://justmore.dk/images/media/ProductsDocs/Rollei-Compact-Traveler-No-I-kamerastativ-sort.pdf
  21.
    - **Claim in stack:** Packed sizes: V-dipole 23 cm; ultracompact Yagi pieces 17 cm or less; petals 17.7 cm, disc 18 cm; helix 4 turns (5 turns 21.5 cm); horn gores 20 cm or less; rings 127/180 mm
    - **Finding:** All recomputed. V-dipole 23 cm (vendor). Yagi pieces 13-16 cm (boom) and 17.0 cm (half of the 34.0 cm reflector). Petals 17.7 cm. A 4-turn helix is 4 x 43 = 17.2 cm and a 5-turn 21.5 cm. Gores are about 18.6 cm or less before about 1 cm tabs; rings 18 cm. Bullseye length is not published (64 mm cover).
    - **Verdict:** confirmed
    - **Action:** None beyond measuring the Bullseye.
    - **Impact:** Every foldable-tier piece meets the 20-23 cm preference.
    - **Sources:**
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-multipurpose-dipole-antenna-kit/
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
  22.
    - **Claim in stack:** Build steps without on-air S11; hairpin (DC short) blocks bias; no loops, no dishes
    - **Finding:** The STACK steps use fixed calculated lengths and receive-only acceptance tests (beacon C/N, GNSS or NCS C/N0, sun noise). The original WB2HOL and W9RH instructions tune with an SWR meter, which the STACK correctly drops. A hairpin is a shorted transmission-line stub, not a loop antenna, and the WA5VJB folded DE is replaced by a straight split DE. Horns and cones are not dishes. One conflict remains: the foldable study's 'Re-check S11 on both ports after first assembly' line must not be copied into build/.
    - **Verdict:** confirmed
    - **Action:** In build/, write the WB2HOL DE gap as fixed at 19-25 mm. Remove any 'tune with VNA' or 'check S11' text inherited from foldable_antennas.json (options 2 and 4).
    - **Impact:** Keeps the build within the no-on-air-S11 rule.
    - **Sources:**
      - https://www.w9rh.org/wp-content/uploads/2024/01/2m-tape-measure-yagi-instructions.pdf
      - https://wa5vjb.com/yagi-pdf/cheapyagi.pdf
  23.
    - **Claim in stack:** 'Technofix is no longer in stock' (QO-100 kit note)
    - **Finding:** Not checked in this pass. Bullseye stock is confirmed at RTL-SDR Blog (70 units) and Passion Radio ('last items').
    - **Verdict:** unverified
    - **Action:** Drop the Technofix note or re-check it in P5. List Passion Radio as the EU source.
    - **Impact:** Minor sourcing detail.
    - **Sources:**
      - https://www.passion-radio.com/lnb-pll/lnb-othernet-978.html
- **Current status oct 2026:** As of 18 Oct 2026: The RTL-SDR Blog multipurpose dipole kit (SKU 3) is USD 17.95 with 357 in stock; no new revision. The Othernet Bullseye BE01 TCXO LNB is USD 29.95 with 70 in stock at RTL-SDR Blog, and EUR 29.94 ex VAT, in stock but marked 'last items', at Passion Radio. The QRO.cz QO-100 LNB costs from EUR 65 incl. VAT at WiMo (in stock), but it uses 15 V for vertical. The Nooelec SAWbird+ GOES is USD 49.95 (80 MHz passband at 1688 MHz). Axotron '2 m Fox Hunting Antenna v3' was published 2026-01-14 and its 3MF zip is online (no license stated, 16 mm round boom). The WB2HOL original page is offline; the W9RH copy has the dimensions. The N2SPI and WA5VJB PDFs are online. Meteor-M N2-3 and N2-4 are both Operational in SatNOGS, with observations on 17-18 Oct 2026. N2-4 LRPT is listed at 137.9/137.1 MHz in 72k and 80k modes. Meteor-M N2-5 is Planned, no earlier than 2027 (OSCAR, updated 2026-01-23). ISS: SSTV Series 34 runs Oct 22-25 2026 on 437.55 MHz (Robot 36); the FM repeater downlink 437.800 is active; RS0ISS APRS on 437.825 is active but still being troubleshot (status 7 Oct 2026). QO-100 is Operational; the AMSAT-DL bandplan beacons are 10489.500, 10489.750, 10489.9935 and 10490.000, while SatNOGS still shows the outdated .550/.795. No EOL notices or firmware/driver items apply to these passive antennas. No measured gain exists for any helicone, gore horn or bare Bullseye; all those gains remain models.
- **Notes:** Method: 13 WebSearch calls, plus WebFetch and curl on primary pages: the vendor product pages, AMSAT-DL, ARISS, SatNOGS, OSCAR, Nooelec and WiMo, the Axotron blog and zip, and the N2SPI, WA5VJB and W9RH PDFs. The downloaded files are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_axotron/ (v3.zip and the drawing PDF), /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_n2spi/n2spi.pdf, /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_vjb/cy.pdf and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_w9rh/w9rh.pdf.
  
  Numbers that are my MODELS, computed in Python. (a) The V-dipole over-ground pattern: straight half-wave dipole times Fresnel reflection, average ground, h = 1.087 m (0.50 lambda), giving a partial zenith null of about -5 dBi and a peak of about +7 dBi at 30 deg broadside; the V shape and real ground move these by +/-2-3 dB. (b) The conical horn and cone gains (Balanis L(s) formula, ideal walls): 21.06, 23.02 and 18.75 dBi. (c) Gore developed geometry, helix geometry and boom joint clearances.
  
  Most important actions:
  1. Re-derive the cone and horn throat from the measured Bullseye feed. The 64 mm feed cover conflicts with the 40 mm-neck throat.
  2. Re-model or adapt the Axotron clamps for the 20x20 square boom; v3 is built for a 16 mm round boom.
  3. Restate the V-dipole gain as an over-ground pattern and add the per-pass height rule (lower the dipole for high M2-3 passes).
  4. Derate the QO-100 model to G + 11...16 dB-Hz.
  5. Record the QRO.cz reversed polarity voltages (15 V = vertical) before calling it an upgrade.
  6. Remove all inherited 'check S11 / tune with VNA' text from build files.
  
  The WB2HOL original page is offline, so its dimensions come from a secondary copy (W9RH), whose lengths agree with the STACK. Unverified: Technofix stock, tripod prices (retailer snippets only), Axotron spool capacity for 137.5 MHz marks, and the hairpin DE on the N2SPI Yagi.

