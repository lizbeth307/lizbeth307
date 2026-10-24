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

## Адверсаріальна перевірка (`verify`)

_Run `wf_d3593e9c-5ce`_

- **Subsystem:** antennas_foldable (stage 3, adversarial verification): telescopic V-dipole for Meteor LRPT; crossed 2 m/70 cm Yagi (WB2HOL tapes on Axotron v3 parts plus N2SPI/WA5VJB 6-el); 4-turn L-band helix and petal helicone with SAWbird+ GOES; QO-100 Othernet Bullseye LNB, 11 cm cone and 6-gore horn; QRO.cz upgrade; travel tripod. User decisions of 18 Oct 2026 applied: region Europe (QO-100 kit is bought now), Lime kept (S-band helix in the cone is active).
- **Verdict:** Most part, price, stock and dimension claims hold against primary sources fetched on 18 Oct 2026. Four load-bearing items change.
  
  (1) V-dipole orientation. "Axis N-S" is ambiguous, and stages 1 and 2 read it as the tip line running N-S. 9A4QV's original rtl-sdr.com text puts the V's front and back (its bisector) N-S. My NEC2 model over Sommerfeld ground, integrated over simulated passes, shows the bisector-N-S orientation at 1.0-1.1 m gives about 9-10.6 min per pass above -6 dB on passes peaking at 40° or higher. The tips-N-S orientation gives about 6.6-7 min. The stage-1/2 rule of lowering the mount to 0.5-0.75 m for high passes is therefore the wrong fix. Keep 1.0-1.1 m and rotate the V for each pass instead (model).
  
  (2) QO-100 link constant. Stage 1 derated to G+11...12 dB-Hz from EA4GPZ's uncorrected 45 dB-Hz. His own corrected analysis gives about G+12-13 dB-Hz downlink-only, so plan on G+11...14. The STACK's G+16 upper end is optimistic.
  
  (3) Meteor-M N2-3. SatNOGS QFH and turnstile stations decoded N2-3 LRPT on passes peaking at only 22-39° on 17 Oct 2026. The STACK's "only above 40-60°" is too pessimistic.
  
  (4) Build-level gaps.
  - The 70 cm split parasitic elements need conductive couplers.
  - Axotron v3 clamps use drilled tape. This contradicts stage 2's "never drill" and makes the 137.5 MHz length re-marks impractical.
  - The horn and cone gains assume an ideal single-mode TE11 throat, but the Bullseye feeds them through a multimode 64 mm cap plane, so the gains are upper bounds.
  - European LNB skew of 0-36° must be set from the fix.
  - The named 32 cm tripods weigh 1.17-1.35 kg, not 0.3-0.6 kg.
  
  The WebSearch budget was exhausted (shared per-turn limit) after one attempt, so every check used direct fetches of primary pages. Thingiverse, MakerWorld and WiMo returned 403 and stay unverified.
- **Confirmed:**
  - RTL-SDR Blog multipurpose dipole kit, product page 18 Oct 2026: SKU 3, USD 17.95, '357 in stock'. Includes 2x 23 cm-1 m telescopics, 2x 5-13 cm, base with 60 cm RG174, 3 m RG174, flexible tripod, suction mount. The guide confirms the M5 element thread and the LRPT recipe: about 53.4 cm per arm ('about 2.5 sections'), horizontal V at about 120 deg. Vendor warns it is not for permanent outdoor mounting (grime gums the telescopics). https://www.rtl-sdr.com/product/rtl-sdr-blog-multipurpose-dipole-antenna-kit/ , https://www.rtl-sdr.com/DIPOLE
  - libre.space V-dipole thread (uzzam, 30 May 2026): 1.087 m recommended, lobe peak about 29.5 deg; h=0.5 m best for high passes and h=1 m for low passes. bali's station at about 55 cm is 'only good for high pass'. My PyNEC run (Sommerfeld, eps 13, 5 mS/m) reproduces the stage-1 Fresnel numbers within about 1 dB: at 1.087 m, zenith -4.3 dBi; peak +7.7 dBi at 30 deg in the bisector plane; free-space zenith 2.8 dBi.
  - Meteor-M N2-4 (59051) LRPT in SatNOGS DB: 137.900/137.100 MHz in 72k and 80k, plus 137.9125 MHz in 80k; HRPT at 1700/1705 MHz. SatNOGS Network has good LRPT observations with decoded MSU-MR images on 17-18 Oct 2026. M2-3 (57166): LRPT 137.9 MHz, HRPT 1700 MHz, good observations with images on 17-18 Oct 2026. WMO OSCAR (updated 2026-01-23): N2-3 Operational, 'working with limitations' (X-band failure); N2-5 Planned, launch 2027 or later.
  - WB2HOL 2 m tape Yagi via the W9RH copy: reflector 41-3/8 in, DE 2x 17-3/4 in with a 3/4-1 in gap, director 35-1/8 in, 5 in of 14-18 AWG hairpin wire, boom tubes of 7 and 11.5 in. The original theleggios.net page returns 404, and the Wayback Machine is unreachable from here. My NEC (lossless, 25 mm tape as an equivalent round wire): 8.3 dBi, F/B 18 dB, Z = 14-22j ohm at 145.8 MHz, so the hairpin is required. The x1.0604 re-mark gives 8.2 dBi at 137.5 MHz. STACK 7.9/7.7 dBi is plausible after steel-tape loss.
  - Axotron 2 m Fox Hunting Antenna v3 (Per Magnusson, 2026-01-14). Zip 2m-antenna-v3.zip: 764,141 bytes, last-modified 14 Jan 2026, 18 3MF parts plus a drawing PDF, no license stated. Drawing: reflector 1041, DE 2x466 (987 tip to tip), director 887 mm; spacing 373 and 266 mm. Boom: 16 mm OD PVC conduit, 347 + 279 mm. Feed: CX2041ANLT balun. Six spool and clamp sets, M3 hardware, 3.5 mm holes drilled through the tape with a steel-plated drill guide. https://axotron.se/blog/?p=1619
  - N2SPI, AMSAT Journal Jul/Aug 2006, Table 3 (from the wide end, inches): D4 1/4 (L 11), D3 6-3/4 (12), D2 13 (12), D1 18-3/4 (12-3/8), DE 21-3/4 (13), REF 24-1/4 (13-3/8). Elements are #8 AWG aluminium (3.26 mm). WA5VJB 'Cheap Yagi' 435 MHz: 'NEC predicts 11.2 dBi for the 6 element' with 30 dB F/B predicted. My NEC with the STACK's straight split DE (0.95 x 13 in): 10.9-11.0 dBi, F/B 25-27 dB over 435-437.8 MHz.
  - Ultracompact boom: joints at 0.13/0.25/0.40/0.56 m give pieces of 13/12/15/16/14 cm. The minimum element clearance is 3.6 cm (the 70 cm DE at 0.094 m). Half-elements are 16.99 cm (13-3/8 in / 2).
  - ARISS (fetched 18 Oct 2026): SSTV Series 34 'ARISS Hardware' runs Thu 22 Oct to Sun 25 Oct 2026 (times TBD) on 437.55 MHz, Robot 36. Status page of 7 Oct 2026: voice repeater 145.990 up / 437.800 down; APRS active on 437.825 MHz, 'still in the process of troubleshooting and testing'.
  - Helicone reference (libre.space 11309): t0nito, 4 Feb 2024, gives '134mm base 440mm top, 88mm height with a 29.7 deg angle. Optimized for 1.7 GHz.' pe2bz (27 Jan 2024) relays Facebook-group reports of Meteor images 'usually hand tracking' with a Nooelec GOES preamp and an RTL. pe2bz (28 Feb 2024): the helicone adds 'about 3 dB ... guesstimated on the waterfall' over his bare helical on fixed SatNOGS stations. Rotating the cone 90 deg made no difference.
  - Petal and helix geometry (recomputed): 1.70 GHz, C=1.1 lambda, D 61.75 mm, pitch 43 mm (0.244 lambda, 12.5 deg); octagon chords 6.89/16.84 cm; petal edge slant 17.7 cm; 44 cm aperture limit 17.9 dBi, so 15.7 dBic means about 60% efficiency; 4 turns = 17.2 cm, 5 turns = 21.5 cm.
  - Nooelec SAWbird+ GOES 100792: USD 49.95, ships in 1 business day, 80 MHz passband centred on 1.688 GHz, at least 30 dB gain, 180 mA nominal, SMA bias 3-5 V. The STACK's ch3 at 4.5 V with TPS2553 (at least 240 mA) is compatible.
  - Othernet Bullseye BE01 at RTL-SDR Blog: USD 29.95, '70 in stock', SKU 20. Specs: LO 9750/10600 MHz; +/-10 kHz at 23 C, +/-30 kHz over -20..60 C; gain 50-66 dB; NF 0.5 dB; 25 MHz reference out on the red F port. Passion Radio: EUR 29.94 ex VAT (USD 33.69 at ECB 1.1253 on 16 Oct 2026), 'In stock, More than 10 Items, Warning: Last items in stock!'. It also lists vertical 11.5-14 V, horizontal 16-19 V, 40 mm support, 64 mm red cover, and a 2 ppm initial + 2 ppm temperature + 1 ppm/year budget. Reviews from DL/DK/PA hams run to 24/09/2026.
  - Technofix is out of stock: shop.technofix.uk shows the Bullseye at GBP 31.99, 'Availability: Out Of Stock' (18 Oct 2026). This was unverified in stage 1.
  - AMSAT-DL NB bandplan: lower beacon 10489.500 CW F1A (400 Hz shift); middle beacon 10489.750 BPSK 400 bit/s; multimedia beacon 10489.9935 8APSK 7200 bit/s; upper/experimental beacon 10490.000 CW F1A; NB downlink vertical linear; the beacons are uplinked from a GPS-locked ground station.
  - QRO.cz LNB per the manufacturer (hamparts.shop, 18 Oct 2026): 'SDR LO 9750 classic' EUR 52.03 incl. VAT (EUR 43.00 ex VAT, USD 48.39), in stock, ships in 2-3 days. '+12 V for Vertical polarisation (NB), +15 V for Horizontal (WB)', 'NEW IF IC in LNB needs +18V to switch to H-pol'. '1 ppm temperature stability TCXO', '2 ppm production frequency tolerance', offset 0 to about 20 kHz (table: 0-30 kHz), 'Stability with TCXO 0.5 ppm (X 390)', typ. 180 mA. Stage 2's reversal of stage 1 holds.
  - Gore horn and cone math (recomputed, Balanis L(s), ideal TE11 throat): inner 3 gores D 127.4 mm, s 0.266, 21.06 dBi; all 6 gores D 180.3 mm, s 0.376, 23.02 dBi; cone 22.9 deg, D 110.5 mm, 18.77 dBi. Developed sector 85.87 deg, so 3 x 28.6 deg. R_in = r/sin 13.8 deg = 83.8 mm (40 mm throat) or 134.2-138.3 mm (64-66 mm throat). Flat gores are 20 cm or less.
  - UCT MSc thesis (Gao 2019) abstract: painted vs copper-plated 3D-printed Ku conical horns measured 12.0 vs 16.6 dBi at 15 GHz; pyramidal horns 17.5 vs 17.7 dBi. This supports stage 2's seam and wall-conductivity risk for conical horns (indirect evidence for sheet-metal gores).
  - Bare-LNB QO-100 reception is documented first-hand. OK1DX: standard LNB + RTL with about 20 dB attenuator, 'able to copy CW beacon just without any dish', no signal through balcony-door glass. RigExpert TBR-AN-1 (12 Jul 2022): 'Satellite dish - you do not need it!', LNB has 'a wide beam', +/-20 deg pointing, FT8 decodes with a GPSDO-locked LNB.
  - Saveitforparts helicone test on RTL-SDR Blog is dated 2025-01-06: NOAA HRPT 'using hand tracking, with a phone running an RTL-SDR and SatDump'; scaffold legs warped and needed extra centre supports.
  - libre.space 14441 (alpha_adhito, 24 Feb 2026): crossband 3x6 Yagi, 'solder wick to connect between the two side of the parasitic element so it can fold', '1-2 min to assemble', 'Not the most sturdy but it works'.
- **Corrections:**
  1.
    - **Claim in stack:** V-dipole: arms 53.4 cm, 120 deg, 'axis N-S' (вісь Пн-Пд), 1-1.1 m. Stages 1 and 2 read this as the tip line N-S (end-fire N-S) and added a height rule: 0.5-0.75 m for passes above about 60 deg.
    - **Finding:** 9A4QV's original text (rtl-sdr.com) says the V pattern is a skyward 'figure 0', 'optimal for satellites travelling in front, above and behind the antenna' and should be oriented N/S. That puts the bisector N-S, with the tip line running E-W. The libre.space paper says the opposite ('axis North-South ... broadside faces East and West').
  
  My PyNEC model (Sommerfeld average ground, 120 deg V, 53.4 cm arms) gives these gains at 1.087 m:
  - Bisector plane: +2.8/+7.0/+7.7/+5.4/+0.3/-4.3 dBi at 10/20/30/45/60/90 deg.
  - Tip plane: -7.3/-2.8/-0.1/+1.1/-1.0/-4.3 dBi.
  
  In a pass simulation (830 km orbit, 194 deg ground track, minutes per pass with slant-range-corrected level of -6 dB or better / -3 dB or better):
  - Bisector N-S at 1.087 m: 9.3/7.4 min (40 deg peak), 10.3/8.7 (60 deg), 10.6/7.6 (88 deg).
  - Tips N-S: 6.9/5.6, 6.8/5.3, 6.6/3.4.
  - For passes peaking at 25 deg or less, tips N-S wins: 6.4/4.9 vs 3.9/0.9.
  - Lowering to 0.55-0.75 m with tips N-S gives only 5.3-5.8/4.2-4.7 min on high passes.
  - The result holds on poor and wet ground. 1.3 m behaves like 1.087 m.
  - A fixed 45 deg compromise orientation is worse than rotating per pass.
    - **Verdict:** corrected
    - **Action:** Mount at 1.0-1.1 m always.
  - Passes peaking at 35 deg or higher (including every Meteor-M N2-3 attempt): V bisector N-S (opening toward N or S), tip line E-W.
  - Passes peaking at 30 deg or lower: rotate 90 deg so the tip line runs N-S and the broadside faces the pass side.
  - Unattended or fixed mount: bisector N-S.
  
  Drop the stage-1/2 low-mount rule. Write the orientation in build/ with a drawing (bisector arrow), not as 'axis'. labd's pass card shows 'V: bisector N-S' or 'V: tips N-S' from the predicted maximum elevation. All numbers are models; settle with the two-kit A/B.
    - **Impact:** Up to about 3-4 more minutes of usable signal per high pass (model), with no hardware cost. The STACK's 'NEC 3.0 dBi at zenith' line is replaced by the over-ground, orientation-dependent pattern.
    - **Sources:**
      - https://www.rtl-sdr.com/simple-noaameteor-weather-satellite-antenna-137-mhz-v-dipole/
      - https://www.rtl-sdr.com/DIPOLE
      - https://community.libre.space/t/mathematical-modeling-and-physical-optimization-of-v-dipole-antennas-for-vhf-imaging-satellite-reception/14844
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/s3fold_calc/nec_vdip_pass2.py
  2.
    - **Claim in stack:** Meteor-M N2-3 LRPT 'на межі', budget of N2-4 minus 3-6 dB, 'expect only above about 40-60 deg'
    - **Finding:** SatNOGS Network on 17 Oct 2026 has N2-3 LRPT observations with decoded MSU-MR products on passes peaking at 22 deg (station 5026, QFH), 27 and 34 deg (station 39, turnstile), 30 deg (station 2381, Diamond DP-KE137 QFH + Uputronics preamp), 34 deg (4084, turnstile) and 36 deg (4073). These are fixed circular or near-circular antennas, about 3 dB better on RHCP than a linear V-dipole near zenith.
    - **Verdict:** corrected
    - **Action:** Change the row to: 'decoded by SatNOGS QFH/turnstile stations on 22-39 deg passes (17.10.2026). With the linear V-dipole, plan on passes peaking at 30-35 deg or higher, bisector N-S at 1.0-1.1 m; confirm by own decodes.' Keep it rated 'на межі' until the device has its own results.
    - **Impact:** More usable N2-3 passes per day than the STACK assumes.
    - **Sources:**
      - https://network.satnogs.org/api/observations/?norad_cat_id=57166&status=good
      - https://network.satnogs.org/api/stations/?id=2381
  3.
    - **Claim in stack:** Optional: the 2 m tapes re-marked for 137.5 MHz (R 111.4, DE 2x47.8, D 94.6 cm), about 7.7 dBi, '+6 dB vs V-dipole'
    - **Finding:** The electrical model is fine: my NEC gives 8.2 dBi and F/B 21 dB at 137.5 MHz. The marks are mechanically incompatible with the Axotron v3 parts the STACK adopts. Axotron fixes each tape by M3 screws through 3.5 mm holes drilled at the clamp, and hooks the tips to spools by an M2.5 screw through a tip hole. Exposed length is set by the cut, so one tape cannot show two lengths. Against a correctly oriented V-dipole at 1.087 m (+7.0...+7.7 dBi at 20-30 deg in the bisector plane), the pointed Yagi gains only about +0.5...+1.2 dB at mid elevation. It gains more only near zenith and at the start and end of passes (model).
    - **Verdict:** corrected
    - **Action:** Remove the 137.5 MHz marks from build/. If the VHF Yagi option is kept for LRPT, cut a separate labelled set of three tapes (111.4 / 2x47.8 with 19-25 mm gap / 94.6 cm) and swap them at the clamps. Otherwise use the V-dipole only. The spool-capacity question then disappears.
    - **Impact:** Removes an unbuildable step. LRPT loses at most about 1-2 dB at mid elevations (model).
    - **Sources:**
      - https://axotron.se/blog/?p=1619
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/s3fold_calc/nec_yagi.py
  4.
    - **Claim in stack:** Stage 2 build note: 'Velcro or elastic retainers for folded tapes, never drill through the tape'
    - **Finding:** The Axotron v3 design that the STACK uses drills the tape on purpose. It supplies a printed drill guide with 5x15x37 mm steel plates for clean 3.5 mm holes, adds clamps that extend further to prevent kinks, and uses sports tape over the edges. The radioreference 'no drilling' advice applies to a different, clamp-only build.
    - **Verdict:** corrected
    - **Action:** In build/, follow Axotron: drill with the steel-plated guide on a drill press, deburr, use stainless M3 hardware and the extended rear, front and driven clamps, tape the edges. Keep elastic retainers only for the rolled spools. Carry one spare cut and drilled tape set.
    - **Impact:** Consistent build instructions; fewer kinked tapes.
    - **Sources:**
      - https://axotron.se/blog/?p=1619
  5.
    - **Claim in stack:** Ultracompact 70 cm half: 'screw-in half-elements of 17 cm or less' (N2SPI 6-el), straight split DE (0.95 x 13 in) plus hairpin
    - **Finding:** No source or STACK text says how the two halves of each PARASITIC element (REF, D1-D4) join electrically. If they screw into an insulating printed boom insert, each parasitic element becomes two isolated 17 cm stubs, resonant near 850 MHz. The Yagi then collapses to roughly a bare dipole, about 2 dBi instead of 11 (engineering estimate). My NEC of the straight split DE gives Z of about 14.2-23.6j ohm at 436.8 MHz. That fits an L-match: series X needed -22.5 ohm, shunt +31.5 ohm, which is about 11.5 nH, a hairpin of roughly 11-12 mm on about 2 mm wire at 12 mm spacing (calculation). The STACK's hairpin idea is therefore electrically consistent.
    - **Verdict:** new_risk
    - **Action:** Specify the couplers:
  - Parasitic elements: a conductive through-boom coupler (brass or stainless M3 threaded coupler or tube with set screws) so each element is continuous tip to tip.
  - DE: insulated split with a 12 mm gap, hairpin of 11-12 mm (calculated, fixed, no S11 tuning).
  - Measure exposed lengths tip to tip including the coupler.
  - DMM check after each assembly: each parasitic element under 1 ohm tip to tip; DE halves open to each other except through the hairpin.
    - **Impact:** Prevents a silent loss of about 9 dB on the primary ISS/CubeSat antenna.
    - **Sources:**
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
      - https://wa5vjb.com/yagi-pdf/cheapyagi.pdf
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/s3fold_calc/nec_yagi.py
  6.
    - **Claim in stack:** 2 m half = WB2HOL lengths on 'Axotron v3' spools on a 20x20 mm square boom
    - **Finding:** Confirmed mismatch (stage 1). Axotron v3 is its own YagiCAD geometry (1041 / 2x466 / 887 mm at 0 / 373 / 639 mm, 16 mm round boom, CX2041ANLT balun). My NEC gives Axotron 7.3 dBi, F/B 32 dB, Z = 36+11j (direct balun feed, no hairpin). WB2HOL gives 8.3 dBi, F/B 18 dB, Z = 14-22j (hairpin). The STACK's hybrid has never been built.
    - **Verdict:** corrected
    - **Action:** Keep WB2HOL electrically (fits the 0.13-0.56 m joints). Redraw the Axotron clamp bases for the 20x20 mm square boom, or use a 16 mm round boom with keyed printed couplers at +/-5 deg. Use Axotron spools and drill guide unchanged. Add hairpin pads to the driven clamp. Files are for personal builds only (no license).
    - **Impact:** Mechanical redraw is the only real cost. Electrical figures stand (model).
    - **Sources:**
      - https://axotron.se/blog/?p=1619
      - https://axotron.se/blog/wp-content/uploads/2025/02/2m-antenna-v3.zip
      - https://www.w9rh.org/wp-content/uploads/2024/01/2m-tape-measure-yagi-instructions.pdf
  7.
    - **Claim in stack:** Conservative QO-100 model 'G + 13...16 dB-Hz'. Stage 1 derated to 'G + 11...16' because EA4GPZ's 45 dB-Hz implies 'G + 11...12'.
    - **Finding:** EA4GPZ's first post (45 dB-Hz) measured 'transponder noise' that includes his own system noise. His follow-up analysis is the corrected one ('Changes to the QO-100 NB transponder settings', Mar 2019): 'CN0 of 48dB at the transponder' with 'a degradation of 3.5dB', and transponder noise of about -1.5 dB relative to his system noise. Downlink-only C/N0 is then 44.5 + 10 log(1+0.71) = 46.8 dB-Hz. With his off-focus dish 'comparable to a 60cm dish' (33.8-34.8 dBi at 55-70% efficiency), that gives G + 12.0...13.0 dB-Hz. The same post confirms the beacon downlink power was restored after the transponder-gain change.
  
  Planning with G+12.5 +/-1.5 (model):
  - Bare Bullseye (9-11 dBi, assumed feed gain): CW beacon +3...+8 dB in 50 Hz.
  - 18.8 dBi cone: BPSK400 Eb/N0 about 3.8-6.8 dB.
  - 21 dBi horn: CW 15-18 dB in 50 Hz, BPSK Eb/N0 6-9 dB, beacon-level SSB -2...+1 dB in 2.5 kHz.
  - 23 dBi horn: 17-20 dB, 8-11 dB, 0...+3 dB.
    - **Verdict:** corrected
    - **Action:** Set the planning model to G + 11...14 dB-Hz (central 12.5). Lower the STACK figures:
  - Bare-LNB CW beacon: '+3...+8 dB, probable' (OK1DX first-hand copy supports 'probable').
  - Cone PSK beacon: 'C/N0 monitor only'.
  - Horn SSB at beacon level: 'marginal, mostly below readability'.
  The A/B C/N0 log replaces the model.
    - **Impact:** Planning figures are 1-3 dB below the STACK upper end. Bare-LNB CW is not as bad as stage 1 suggested.
    - **Sources:**
      - https://destevez.net/2019/03/changes-to-the-qo-100-nb-transponder-settings/
      - https://destevez.net/2019/03/qo-100-beacons-power/
      - https://destevez.net/2019/03/new-dish-for-eshail-2-reception/
      - http://ok1dx.cz/techinfo/qo100/qo100.html
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/s3fold_calc/qo.py
  8.
    - **Claim in stack:** Horn 21/23 dBi and cone 18.8 dBi starting at a printed 40.2 mm clamp. Stage 1/2: move the throat to the about 64 mm cap plane and recompute R_in.
    - **Finding:** The geometric correction stands: R_in = 134-138 mm for a 64-66 mm throat. The gain figures, however, assume an ideal single-mode TE11 throat at the virtual apex. A 64 mm circular aperture is multimode at 10.49 GHz (TE11 cutoff about 2.75 GHz). The wave comes from the LNB's own scalar feed, whose phase centre is near the cap, not 134 mm behind it. Crude estimate with the phase centre at the cap plane: quadratic phase parameter s rises from 0.27/0.38 to about 0.5-0.6 for the horn and about 0.8 for the short cone. That is roughly 2-3 dB lower for the horn and more for the cone (model, unverified). A clean alternative exists: QRO.cz sells its LNB 'with POTY adapter' for a 22 mm Cu tube waveguide, and a 20 mm ID pipe is single-mode at 10.49 GHz (TE11 cutoff 8.79 GHz, TM01 11.47 GHz).
    - **Verdict:** new_risk
    - **Action:** Treat 21.1/23.0/18.8 dBi as upper bounds. Plan on about 18-21 dBi for the horn and 15-17 dBi for the cone until the A/B. For the horn tier, consider the QRO.cz POTY version with a 22 mm Cu pipe stub and a gore throat of 20 mm ID (R_in = 10/sin 13.8 deg = 41.9 mm; split the longer inner gores so each stays under 23 cm). First confirm with QRO.cz that the POTY version exposes a 22 mm pipe input, and get its price (unverified). Do not cut the Bullseye cap.
    - **Impact:** Prevents over-promising horn margins. The POTY route makes the Balanis model applicable.
    - **Sources:**
      - https://hamparts.shop/10-ghz-lnb-with-pll-and-tcxo.html
      - https://www.passion-radio.com/lnb-pll/lnb-othernet-978.html
      - http://www.w1ghz.org/antbook/chap3.pdf
  9.
    - **Claim in stack:** LNB 13.2 V vertical only; rotate the LNB 90 deg for horizontal. (Region was unknown in the STACK.)
    - **Finding:** Region is now Europe. The NB downlink is vertical linear as seen from the satellite, so the local polarization is skewed. tan(psi) = sin(dlon)/tan(lat), with the satellite at 25.9E. Western and central Europe (dlon -12...-35 deg) gives skew of about 9-36 deg. Uncorrected, that costs about 0.1-1.8 dB. Skew is near 0 deg near 26E. QO-100 elevation is about 22-46 deg across Europe (calculation).
    - **Verdict:** new_risk
    - **Action:** labd computes the skew and elevation from the GNSS fix (no city tables) and shows 'rotate LNB x deg'. Print the 40 mm neck adapter with a +/-45 deg scale and a locking screw. Peak by beacon C/N0 in 5 deg steps (receive-only).
    - **Impact:** Up to about 1.8 dB recovered in western Europe; no hardware cost.
    - **Sources:**
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/s3fold_calc/qo.py
  10.
    - **Claim in stack:** Upgrade path 'QRO.cz 0.2 ppm'; LNB rail 13.2 V +/-0.2 V
    - **Finding:** The manufacturer gives 1 ppm temperature, 2 ppm production tolerance, 'Stability with TCXO 0.5 ppm (X 390)', and an offset of 0-20 kHz (0-30 kHz in the parameter table). '0.2 ppm' (WiMo) does not appear on the manufacturer page; WiMo returned 403 so it could not be re-read. Old-IF-IC units switch to H at +15 V with an unpublished threshold, so 13.2 V sits between 12 V (V) and 15 V (H). The Bullseye's vertical window is 11.5-14 V.
    - **Verdict:** corrected
    - **Action:** BOM text: 'QRO.cz SDR LO 9750, EUR 52.03 incl. VAT (USD 58.55), +12 V = V-pol; 1 ppm temp / 2 ppm initial (0-20 kHz); 180 mA'. Ask the power owner to set the LNB LDO (TPS7A4701 ANY-OUT) to 12.5 V +/-0.2 V. This suits both LNBs and adds about 0.7 V of battery dropout margin. If 13.2 V is kept, verify V-pol on a QRO.cz unit with the beacon test.
    - **Impact:** Removes a possible silent cross-pol loss of about 20 dB on the upgrade path.
    - **Sources:**
      - https://hamparts.shop/10-ghz-lnb-with-pll-and-tcxo.html
      - https://www.passion-radio.com/lnb-pll/lnb-othernet-978.html
  11.
    - **Claim in stack:** QO-100 kit 'held until region known'; Bullseye USD 29.95 (70 in stock); 'Technofix no longer in stock'
    - **Finding:** Region is Europe (user decision, 18 Oct 2026), so the kit is bought. Stock today:
  - RTL-SDR Blog: 70 (ships from China).
  - Passion Radio (EU, France): EUR 29.94 ex VAT, 'last items' (more than 10).
  - Technofix UK: out of stock at GBP 31.99.
  One 2026 Passion Radio review says most shops have run out.
    - **Verdict:** confirmed
    - **Action:** Order now: one Bullseye from Passion Radio (EU VAT and customs simplest) or RTL-SDR Blog. Consider a second unit as a spare, since it is the only LNB, supply is thinning and the cost is low. Add a 75 ohm F terminator for the red 25 MHz port and F/75 ohm parts.
    - **Impact:** Supply risk is closed while stock lasts.
    - **Sources:**
      - https://www.passion-radio.com/lnb-pll/lnb-othernet-978.html
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
      - https://shop.technofix.uk/bullseye-ultra-high-stability-single-lnb-for-qo-100-2ppm-tcxo
  12.
    - **Claim in stack:** IF pad 15/20 dB after the LNB (stage 2: add a 30 dB step, unverified OK1PHU snippet)
    - **Finding:** Calculation (model): LNB output noise density with T about 100 K and G 50-66 dB is about -128 to -112 dBm/Hz, or about -38 to -22 dBm total over the 739-1950 MHz IF. A 30 dB pad still leaves the LNB noise about 8-16 dB above an RTL with 7 dB NF (-167 dBm/Hz), so the sensitivity cost is 0.1-0.6 dB. The 15 dB pad risks R828D front-end compression at 66 dB LNB gain. OK1DX used about 20 dB with no dish.
    - **Verdict:** corrected
    - **Action:** Carry 10+10 and 20 dB SMA pads (15/20/30 dB possible). Choose the pad that gives a noise rise of at least 10 dB with the beacon C/N0 unchanged when RTL gain is stepped (no compression).
    - **Impact:** Avoids desensitisation masking the bare-LNB beacon.
    - **Sources:**
      - http://ok1dx.cz/techinfo/qo100/qo100.html
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
  13.
    - **Claim in stack:** Stage 1: SatNOGS DB 'still lists pre-2020 10489.550 and 10489.795'
    - **Finding:** SatNOGS DB API (18 Oct 2026), QO-100 (43700): the 10489.550 CW and BPSK entries are marked inactive. A stale 'BPSK400 Upper Beacon 10489.795' (2019) is still 'active', alongside 'BPSK400 Middle Beacon 10489.745' and a new 2026-04-12 entry 'CW Lower Beacon 10489.503'. None of these equal AMSAT-DL's exact values.
    - **Verdict:** corrected
    - **Action:** Keep the rule: take frequencies from AMSAT-DL only (10489.500 / .750 / .9935 / 10490.000). The tracker should also expect the lower and upper CW beacons as F1A with a 400 Hz shift (two tones), not a single carrier.
    - **Impact:** Tracker correctness; minor.
    - **Sources:**
      - https://db.satnogs.org/api/transmitters/?format=json&satellite__norad_cat_id=43700
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
  14.
    - **Claim in stack:** Helicone '15.7 dBic (model)'; HRPT 'reliable (model)'; 'no documented dishless hand-held HRPT decode'
    - **Finding:** No measured gain exists. pe2bz's '+3 dB' is a waterfall guess on fixed zenith-pointed SatNOGS stations against an unspecified 'bare helical'. The 13-14 dBic lower bound from stage 2 is therefore an inference. Hand-tracked HRPT is documented: Saveitforparts video (RTL-SDR Blog, 2025-01-06) with NOAA HRPT, which is no longer replicable since NOAA POES ended in 2025; Meteor HRPT hand-tracked second-hand (pe2bz, Jan 2024).
    - **Verdict:** confirmed
    - **Action:** Budget 13-15.7 dBic. Wording: 'documented hand-tracked HRPT with a t0nito helicone + RTL + SatDump (NOAA, video 2025; Meteor second-hand 2024); no measured gain'. Keep Metop/AWS as experiments behind the gates.
    - **Impact:** No change beyond stage 2.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://www.rtl-sdr.com/saveitforparts-testing-a-3d-printable-satellite-antenna-for-noaa-meteor-and-other-polar-orbiting-l-band-satellites/
  15.
    - **Claim in stack:** Stage 1 action: make the petal tabs allow both the t0nito angle (29.7 deg) and the STACK's deeper cone (42.7 deg) with the same petals
    - **Finding:** Geometry: 17.7 cm petals on the 18 cm disc at 29.7 deg open to a 48.7 cm mouth at about 88 mm depth (t0nito's height). The octagon rim chord would need to be 18.6 cm, but the petal top edge is 16.8 cm. Wedge gaps of 0-1.8 cm open between adjacent petals at the rim (calculation). The effect on gain is unmodelled.
    - **Verdict:** corrected
    - **Action:** For an angle A/B, cut a second petal set to the t0nito angle (rim chord 18.6 cm, slant about 17.7 cm), or accept the wedge gaps and bridge them with aluminium tape. Do not compare the angles with gapped petals and call it the t0nito geometry.
    - **Impact:** A clean A/B; minor material cost.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
  16.
    - **Claim in stack:** Travel tripod: folded to 35 cm or less, from 1.2 m, mini pan head, 1/4-20, $40-100; weight 0.3-0.6 kg (kit table)
    - **Finding:** Two named options, vendor or retailer data:
  - Manfrotto BeFree One Aluminium: closed 32 cm, max 130 cm (113 cm with column down), min 49 cm, 1350 g, 2.5 kg payload, ball head 'not detachable', EUR 119.95 sale at bigbearsound (USD 134.98).
  - Rollei Compact Traveler No. 1 datasheet: folded 31.5 cm, max 134 cm, 1170 g with ball head, 5 kg load, 1/4 in screw; price not found.
  Both have ball heads, not pan heads, and weigh 2-4x the STACK's figure.
    - **Verdict:** new_option
    - **Action:** Name Rollei Compact Traveler No. 1 (5 kg load) as the default, with Manfrotto BeFree One Aluminium as an alternative. Re-price both in USD in P5. Change the kit weight line to 1.2-1.4 kg (backpack +0.6-1.0 kg). Accept a ball head (fine for a GEO horn and a static V). Check horn and helicone balance at 30 deg elevation.
    - **Impact:** A sourceable part; the weight budget becomes realistic.
    - **Sources:**
      - https://bigbearsound.com/products/manfrotto-befree-one-aluminium-travel-tripod-with-head-black
      - https://justmore.dk/images/media/ProductsDocs/Rollei-Compact-Traveler-No-I-kamerastativ-sort.pdf
  17.
    - **Claim in stack:** Antenna A/B 'on SSTV series 34, 22-25.10.2026' (bench section 8; stage 2 hairpin acceptance)
    - **Finding:** Series 34 is confirmed for 22-25 Oct 2026 (times TBD). The parts are not yet bought or built (P7 builds later), so this A/B cannot happen on that event.
    - **Verdict:** corrected
    - **Action:** Use the next ARISS SSTV event or daily CubeSat 9k6 beacons and ISS APRS 437.825 for the 70 cm hairpin-DE acceptance (receive-only). Optionally record series 34 with any existing receiver as a reference only.
    - **Impact:** Schedule realism.
    - **Sources:**
      - https://www.ariss.org/upcoming-sstv-events.html
  18.
    - **Claim in stack:** Stage 2: printed 120 deg holder from Thingiverse 3421430 or MakerWorld 1127183
    - **Finding:** Both pages, and Thingiverse 6436342 (t0nito), return 403 (Cloudflare) to curl and WebFetch. Existence, function and license are unverified. The base-arm looseness report comes from a reseller-quoted Amazon review (unverified). The RTL-SDR Blog page comments document a bad batch with unthreaded elements that was replaced free.
    - **Verdict:** unverified
    - **Action:** Design our own printed 120 deg V clamp (PETG/ASA): grips both telescopics at the base, has a 1/4-20 insert and a bisector arrow mark. Mark 53.4 cm on each tube. Inspect the M5 threads on arrival.
    - **Impact:** Removes the dependency on unverifiable third-party files.
    - **Sources:**
      - https://www.rtl-sdr.com/DIPOLE
  19.
    - **Claim in stack:** S-band (Lime now kept): 7-turn S helix (46.7 mm, 32.5 mm pitch, 228 mm) in the helicone cone, 14.2 dBic (NEC)
    - **Finding:** pe2bz (Feb 2024) found a 5.2-turn 2250 MHz helix in a 75%-scaled helicone 'still weak'. Cutting it to 'a bit more as 2 turns' increased signal strength and duration. A long helix inside the cone may underperform; the cone does most of the work. This is anecdotal, one station.
    - **Verdict:** new_risk
    - **Action:** Before finalising the S-band feed, run a receive-only A/B of the 7-turn helix vs a 2-3-turn helix in the same cone on S-band passes (Lime RX2 + cf2235-kt30). The S-band LNA is still unnamed (rf_frontend item).
    - **Impact:** Possible S-band gain shortfall; affects only opportunistic targets.
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
  20.
    - **Claim in stack:** Region Europe consequence: IF-penetration check near the LNB IF (user requirements)
    - **Finding:** The IF at 739.5-740.0 MHz lies in the European 700 MHz band, between the LTE B28 uplink (703-733 MHz) and downlink (758-788 MHz), in the duplex gap. Strong nearby DVB-T, LTE or SDL emitters can leak into an unshielded IF path (engineering reasoning; not measured).
    - **Verdict:** new_risk
    - **Action:** Add the field check in the bench tests. Use RG6 with compression F connectors and the DC-blocked injector in the shielded RF bay.
    - **Impact:** Protects the bare-LNB beacon margin, which is only +3...+8 dB.
    - **Sources:**
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
- **New risks:**
  - Orientation ambiguity of the V-dipole ('axis N-S'): the two readings differ by about 3-4 min of usable signal per high pass (model). The build file must show the bisector arrow, and labd must state the per-pass orientation.
  - 70 cm screw-in parasitic half-elements without a conductive through-boom coupler would make the N2SPI Yagi a bare dipole (about -9 dB, estimate). This is a DMM continuity check after every assembly.
  - Gore horn and cone fed through the Bullseye's multimode 64 mm cap plane: the Balanis gains (21.1/23.0/18.8 dBi) are upper bounds. Crude phase-error estimate is 2-3 dB lower for the horn and more for the short cone.
  - European LNB polarization skew of 0-36 deg (up to 1.8 dB) must be set from the GNSS fix.
  - QRO.cz old-IF-IC units switch to H at +15 V with an unpublished threshold. A 13.2 V rail lies between the 12 V (V) and 15 V (H) setpoints; prefer a 12.5 V rail (power owner) or verify.
  - Bullseye supply is thinning: Technofix out of stock, Passion Radio 'last items', RTL-SDR Blog 70 units. Buy now; a spare is advisable.
  - Tripod mass is underestimated: the named 32 cm tripods weigh 1.17-1.35 kg, not 0.3-0.6 kg (backpack +0.6-1.0 kg). Both have ball heads, not pan heads.
  - The 137.5 MHz tape re-mark cannot be built on Axotron's drilled clamps (fixed length per cut).
  - Axotron v3 3MF files have no stated license (personal use only), and the clamps must be redrawn for the 20x20 mm boom.
  - Lime kept: a 7-turn S helix in the helicone may underperform a 2-3-turn one (pe2bz anecdote); the S-band LNA is still unnamed.
  - Bare-LNB C/N0 margin is thin (+3...+8 dB CW in 50 Hz, model). The 700 MHz-band IF (739.5 MHz) in Europe needs a leakage check.
  - The lower and upper QO-100 CW beacons are F1A with a 400 Hz shift; a single-carrier 50 Hz tracker will see energy hop between two bins.
- **Refuted findings:**
  1.
    - **Finding:** Stage 1/2 height rule: mount the V-dipole at 0.5-0.75 m for passes peaking above about 60 deg, because 1.087 m has a zenith null.
    - **Why:** The zenith null is real (NEC -4.3 dBi), but the satellite spends little time near zenith. The rule also assumed the tip line runs N-S. With the 9A4QV orientation (bisector N-S) at 1.087 m, high passes give 10.3-10.6 / 7.6-8.7 min (at -6 / -3 dB or better). Tips N-S at 0.55-0.75 m gives 5.3-5.8 / 4.2-4.7 min (my PyNEC pass simulation, robust on poor and wet ground). Rotation, not lowering, is the fix.
  2.
    - **Finding:** Stage 1: EA4GPZ's measurement implies a QO-100 beacon C/N0 of about G + 11...12 dB-Hz, 1-5 dB below the STACK's conservative model.
    - **Why:** The 45 dB-Hz figure in the first post included transponder noise. EA4GPZ's own correction gives 48 dB-Hz at the transponder, 3.5 dB degradation and transponder noise -1.5 dB vs system noise. That puts the downlink-only C/N0 at about 46.8 dB-Hz, or G + 12-13 dB-Hz for a dish of about 34 dBi. G + 11 is a floor, not the central value.
  3.
    - **Finding:** Stage 2: 'never drill through the tape'.
    - **Why:** The Axotron v3 design adopted by the STACK drills 3.5 mm holes in the tape with a steel-plated drill guide and screws the tape to the clamps. The no-drill advice comes from a different, clamp-only build.
  4.
    - **Finding:** STACK: Meteor-M N2-3 LRPT expected 'only above about 40-60 deg'.
    - **Why:** SatNOGS QFH and turnstile stations decoded N2-3 MSU-MR images on passes peaking at 22, 27, 30, 34 and 36 deg on 17 Oct 2026.
  5.
    - **Finding:** Stage 1: SatNOGS DB 'still lists the pre-2020 frequencies 10489.550 and 10489.795'.
    - **Why:** Only partly true. The 10489.550 entries are marked inactive. The stale 10489.795 BPSK entry is still marked active, and an entry 'CW Lower Beacon 10489.503' was added on 2026-04-12. The action (use AMSAT-DL only) stands.
  6.
    - **Finding:** Stage 2: the Saveitforparts RTL-SDR Blog post 'is undated on the page'.
    - **Why:** The page carries article:published_time 2025-01-06 and 'January 6, 2025'. The NOAA HRPT result therefore predates the 2025 end of NOAA POES and cannot be reproduced now.
  7.
    - **Finding:** Stage 1: 'about 2 cm of element sits inside the base' given as a vendor recipe detail.
    - **Why:** It comes from a reader comment on the RTL-SDR guide, not from the vendor. The vendor recipe is '53.4 cm each (about 2.5 sections)'.
  8.
    - **Finding:** Stage 2: alpha_adhito's folding VHF halves 'are about 0.5 m'.
    - **Why:** The post gives no lengths. This is an inference from 2 m element size, not a sourced figure. The braid-bridge technique itself is confirmed.
  9.
    - **Finding:** Stage 1 (already withdrawn by stage 2): the QRO.cz LNB needs a 90 deg rotation or a 15 V boost to receive vertical.
    - **Why:** The manufacturer states +12 V = vertical (NB). The WiMo table appears transposed (WiMo returned 403, so it could not be re-read).
- **Corrected spec:** FOLDABLE ANTENNA TIER v1.1 (18 Oct 2026; region Europe; Lime kept). Receive-only, no on-air S11, no loops, no dishes. "Model" means my NEC2/PyNEC run or a formula.
  
  1) 137 MHz Meteor LRPT: telescopic V-dipole
  - Part: RTL-SDR Blog multipurpose dipole kit (SKU 3), USD 17.95, 357 in stock (rtl-sdr.com, 18 Oct 2026).
  - Elements: 2x telescopic 23 cm to 1 m, M5 thread. Lead: 60 cm RG174 plus 3 m RG174. Packed length 23 cm.
  - Setup: each arm 53.4 cm (about 2.5 sections, tape mark), horizontal V at 120 deg in our own printed PETG/ASA 120 deg clamp with a 1/4-20 insert and a bisector arrow.
  - Height: 1.0-1.1 m (1.087 m = lambda/2 at 137.9 MHz) on the tripod, for every pass.
  - Orientation per pass (model):
    - Predicted maximum elevation 35 deg or higher (including all N2-3 attempts): bisector N-S, tip line E-W.
    - 30 deg or lower: rotated 90 deg (tip line N-S).
    - Unattended: bisector N-S.
  - Model gains at 1.087 m, average ground:
    - Bisector plane: +2.8/+7.0/+7.7/+5.4/+0.3/-4.3 dBi at 10/20/30/45/60/90 deg.
    - Tip plane: -7.3/-2.8/-0.1/+1.1/-1.0/-4.3 dBi.
    - Linear polarization: -3 dB on RHCP.
  - RF path: Flamingo+ FM, then SAWbird+ NOAA.
  - SatDump profiles: 72k and 80k on 137.900/137.100 MHz (N2-4 also 137.9125 MHz, 80k).
  - No 137.5 MHz tape re-marks. Optional separate LRPT tape set for the 2 m Yagi: R 111.4, DE 2x 47.8 (19-25 mm gap), D 94.6 cm.
  - Spare telescopic pair: kit #2.
  
  2) Crossed 2 m/70 cm Yagi, ultracompact
  - Boom: 20x20 mm PVC/GRP square tube in 5 pieces. Joints at 0.13/0.25/0.40/0.56 m give pieces of 13/12/15/16/14 cm, each joint at least 3.6 cm from any element. Keyed joints, planes orthogonal within +/-5 deg, no wingnuts.
  - 2 m half (optional), WB2HOL 3-el in 25 mm steel tape:
    - Elements: R 105.1 cm at 0; DE 2x 45.1 cm with a fixed 19-25 mm gap at 0.203 m; D 89.2 cm at 0.508 m.
    - Hairpin: 127 mm (5 in) of 14-18 AWG wire across the DE (W9RH), fixed length.
    - Model: 8.3 dBi lossless (about 7.9 dBi with steel loss), F/B 18 dB, Z 14-22j.
    - Mechanics: Axotron v3 spools, spring clamps and drill guide (3MF of 2026-01-14, personal use, no license). Clamp bases redrawn for the 20x20 boom, or a 16 mm round boom with keyed couplers. Tape drilled 3.5 mm with the steel-plated guide, stainless M3, extended clamps, taped edges.
  - 70 cm half, N2SPI/WA5VJB 6-el in #8 AWG (3.26 mm) Al rod with M3-threaded ends:
    - Positions on the boom: REF 0.0300, DE 0.0935, D1 0.1697, D2 0.3158, D3 0.4745, D4 0.6396 m.
    - Tip-to-tip lengths: REF 339.7 mm, DE 313.7 mm (straight split, 12 mm gap, insulated), D1 314.3, D2 304.8, D3 304.8, D4 279.4 mm.
    - Halves of 17.0 cm or less. Parasitic halves joined by a conductive brass or stainless M3 through-boom coupler (under 1 ohm tip to tip, checked with a DMM).
    - DE hairpin: about 11.5 nH, about 11-12 mm on 2 mm wire at 12 mm spacing (calculated, fixed).
    - Uputronics 440 at the feed.
    - Model: 10.9-11.0 dBi, F/B 25-27 dB (WA5VJB NEC 11.2 dBi for the folded-DE original).
  - Price: materials USD 25-40 (estimate).
  
  3) L-band helix and petal helicone
  - Helix: RHCP for direct reception, 4 turns (17.2 cm; 5 turns 21.5 cm). D 61.7 mm (C = 1.1 lambda at 1.70 GHz), pitch 43 mm (12.5 deg), 2 mm Cu on a printed former, feed 30.9 mm off-centre with a matching strip.
  - Disc: 18 cm x 1.5 mm Al.
  - LNA: Nooelec SAWbird+ GOES 100792 (USD 49.95; 80 MHz passband around 1688 MHz; at least 30 dB; 180 mA) on SMA under the disc. Bias 4.5 V (4.30 V since v2.1) over coax from injector ch3 (TPS2553, at least 240 mA). Never micro-USB.
  - Cone: 8 petals of 0.3-0.5 mm Al (chords 6.9/16.8 cm, edge slant 17.7 cm, 1 cm tabs, at least 1 cm overlap). Disc 18 cm to mouth 44 cm, 12 cm deep (42.7 deg from the disc plane).
  - Reference geometry (field-proven t0nito): 134 to 440 mm, 88 mm high, 29.7 deg. A t0nito-angle A/B needs its own petal set (rim chord 18.6 cm).
  - Gain budget: 13-15.7 dBic (no measurement exists).
  - S-band (Lime): 7-turn helix (46.7 mm, 32.5 mm pitch, 228 mm) in the same cone, pending an A/B against a 2-3-turn helix; cf2235-kt30; LNA to be named.
  
  4) QO-100 (buy now)
  - LNB: Othernet Bullseye 10 kHz BE01.
    - Prices: USD 29.95 at RTL-SDR Blog (70 in stock); EUR 29.94 ex VAT (USD 33.69 at ECB 1.1253) at Passion Radio ('last items'); Technofix out of stock (GBP 31.99). A spare unit is advised.
    - Specs: LO 9750 MHz, IF 739.500/739.750 MHz for the 10489.500 CW-F1A and 10489.750 BPSK400 beacons; vertical 11.5-14 V.
  - LNB rail: preferably 12.5 V +/-0.2 V (TPS7A4701 ANY-OUT; power owner to confirm), else 13.2 V. No 18 V.
  - Red 25 MHz port: 75 ohm F terminator.
  - Skew: rotation computed from the GNSS fix (0-36 deg in Europe) on a printed 40 mm neck adapter with a +/-45 deg scale.
  - IF: RG6 with compression F, DC-blocked injector, pad 15/20/30 dB chosen on the bench (noise rise of 10 dB or more without compression).
  - Throat: ring at the measured red-cap plane (Passion Radio gives 64 mm OD), held by a printed adapter on the 40 mm neck. Do not remove the cap.
  - Cone: 22.9 deg half-angle, 110.5 mm mouth, R_in = r/sin 22.9 deg (82-85 mm for a 64-66 mm throat).
  - Horn: 13.8 deg half-angle, 6 gores of 28.6 deg in 0.3-0.5 mm Al.
    - Inner 3 gores: R_in to 267 mm, with R_in = r_throat/sin 13.8 deg (134.2-138.3 mm for a 64-66 mm throat).
    - Outer 3 gores: 255 to 378 mm.
    - Rings 127/180 mm.
    - Seams overlapped at least 5 mm, riveted, with conductive-adhesive Al tape on top.
  - Gain (Balanis, ideal TE11): 21.06/23.02 dBi (horn), 18.77 dBi (cone). These are upper bounds; plan on about 18-21 and 15-17 dBi until the A/B.
  - Planning C/N0 = G + 11...14 dB-Hz (central 12.5, EA4GPZ corrected). Expected:
    - Bare LNB: CW beacon +3...+8 dB in 50 Hz.
    - Horn: CW 15-20 dB in 50 Hz; BPSK400 Eb/N0 6-11 dB; beacon-level SSB -2...+3 dB in 2.5 kHz.
    - Typical SSB and DATV: lost.
  - Upgrade option: QRO.cz 'SDR LO 9750' at EUR 52.03 incl. VAT (USD 58.55), in stock at hamparts.shop. +12 V = V-pol, +15 V (old IF IC) or +18 V (new) = H; 1 ppm temperature, 2 ppm initial (0-20 kHz); 180 mA. The 'with POTY adapter' version (22 mm Cu tube waveguide) would give a single-mode 20 mm ID horn throat (R_in 41.9 mm); confirm details and price with QRO.cz.
  
  5) Tripod
  - Requirements: folded 35 cm or less, at least 1.1 m, 1/4-20.
  - Default: Rollei Compact Traveler No. 1 (31.5 cm, 134 cm, 1170 g, 5 kg, ball head; price TBD in P5).
  - Alternative: Manfrotto BeFree One Aluminium (32 cm, 130 cm, 1350 g, 2.5 kg, fixed ball head; EUR 119.95 = USD 134.98 at one EU retailer).
  - Kit weight line: 1.2-1.4 kg.
  
  6) Packed sizes (all at or under the 23 cm preference)
  - Dipole kit 23 cm; boom pieces 16 cm or less; 70 cm halves 17.0 cm; spools small; petals 17.7 cm; disc 18 cm; 4-turn helix 17.2 cm; S helix 22.8 cm; gores 18.7 cm or less; rings 18 cm; tripod 31.5-32 cm (within the 35 cm maximum).
  
  7) Build acceptance: receive-only
  - Measures: beacon C/N0, GNSS/NCS C/N0, sun noise, satellite SNR, plus DMM continuity.
  - No VNA or S11 on any antenna; delete all inherited 'check S11 / tune with VNA' lines from foldable_antennas.json steps 2-4.
- **Bench tests:**
  - V-dipole orientation A/B (receive-only, settles the main correction): two dipole kits (#1 and #2), both 53.4 cm arms at 120 deg and 1.087 m, at least 3 m apart. Kit A has its bisector N-S, kit B its tip line N-S. Record the same Meteor-M N2-4/N2-3 pass on RTL-A and the spare V4L, both with Flamingo+ and an LNA. Swap the antennas between receivers on alternate passes. Log SatDump SNR vs time and decoded lines for at least 8 passes spanning 15-85 deg maximum elevation. Accept the per-pass rule if A beats B by at least 2 min of decodable time on passes of 40 deg or higher, and B beats A on passes of 25 deg or lower.
  - Height check (optional): kit A bisector N-S at 1.087 m vs 0.75 m on 4 high passes. Expected: 1.087 m equal or better on time at -6 dB or better (model).
  - 70 cm Yagi continuity (DMM, every assembly): each parasitic element under 1 ohm tip to tip through its coupler; DE halves open to each other except via the hairpin (DC short expected); labd DC-sense blocks bias with no LNA in line.
  - 70 cm Yagi on-air acceptance (receive-only): CubeSat 9k6 beacons and ISS APRS 437.825 MHz, or the next ARISS SSTV event (series 34 on 22-25 Oct 2026 is too early for the build). Compare SNR against the 17 cm whip on the same pass. Expect an advantage of about 8-11 dB at 30 deg or above (model). If under 5 dB, suspect a coupler or the hairpin.
  - QO-100 A/B after purchase: bare Bullseye / cone / 3 gores / 6 gores. Log the C/N0 of 10489.750 BPSK and 10489.500 CW-F1A with LNB skew set from the fix and peaked in 5 deg steps. Compare with G + 11...14 dB-Hz. Repeat one 6-gore run after re-taping the seams (a change of more than 1 dB means lossy seams). Record cap OD, protrusion and visible feed aperture before printing the throat ring.
  - LNB rail and polarization: measure Bullseye current cold and warm at 12.5 V and 13.2 V. With a QRO.cz unit (if bought), confirm V-pol at the chosen rail (beacon C/N0 vs LNB rotated 90 deg; cross-pol should be 15 dB or more down).
  - IF level and pad: with 15/20/30 dB pads, measure the noise rise (target 10 dB or more) and check for compression (beacon C/N0 constant while RTL gain steps 10 dB). Choose the smallest pad that passes.
  - Europe IF leakage: LNB unpowered with the F-port terminated, then the coax connected with the LNB off. Scan 730-750 MHz in the field (DVB-T, LTE B28, SDL); repeat with the LNB on. Any carrier within 739.4-740.1 MHz above the noise means better shielding or a different LO/IF plan.
  - Helicone A/B (receive-only): helicone vs bare 4-turn helix on the Inmarsat-C NCS carrier (European ocean-region NCS from the power-only scan) and GNSS C/N0, plus sun-noise rise. Optional second petal set at 29.7 deg. A gain of more than 4 dB over the helix moves Metop/AWS back to 'marginal (experiment)'.
  - S-band helix A/B (Lime): 7-turn vs 2-3-turn helix in the same cone on S-band passes (2208-2288 MHz) through cf2235-kt30, comparing carrier SNR and duration.
  - Tripod: Rollei/Manfrotto with the helicone (about 0.4-0.5 kg) and the horn + LNB at 30 deg elevation and 1.1-1.3 m in about 20 km/h wind. The head must not creep more than 2 deg in 10 min.
  - Axotron parts on a 20x20 boom: print the redrawn clamp bases, then do a fold/unfold cycle test (20x) with measured plane orthogonality (+/-5 deg) and a tape-kink inspection. Only if the separate LRPT tape set is kept: check that the reflector spool holds 55.7 cm of 25 mm tape.
- **Confidence:** medium

