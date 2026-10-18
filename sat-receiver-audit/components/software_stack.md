# Software stack: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_9603e249-d87`_

- **Subsystem:** software_stack
- **Findings:**
  1.
    - **Claim in stack:** C11/5.4: rebuild noble rtl-sdr 2.0.1-2build1 with commits 0204c9c (R828S/V4L) and 65f0658 (USB hang fix), keep SONAME librtlsdr.so.2 for all librtlsdr2 consumers
    - **Finding:** Both commits exist in osmocom rtl-sdr: 0204c9c 'Add RTL-SDR Blog V4L Support' (R828S, detected through the 'RTLSDRBlog'/'Blog V4L' EEPROM strings; committed 2026-08-11) and 65f0658 'Fix application hang on USB transfer errors' (2026-01-26). Both cherry-pick cleanly onto tag v2.0.1. A test build (x86-64 host, no hardware) produced SONAME librtlsdr.so.2. The .so.2 choice is correct, because noble consumers depend on librtlsdr2: soapysdr0.8-module-rtlsdr, welle.io (welle-cli) and the OpenWebRX+ noble rtl-connector (librtlsdr2 >= 2.0.1). Upstream went back to SOVERSION 0 in 2.0.2 (commit 7ebcb04). Debian 2.0.3-1 (sid/forky, 6 Sep 2026) ships librtlsdr0 with Breaks/Replaces librtlsdr2 (<< 2.0.2), so Debian's newer packages must never be mirrored.
    - **Verdict:** confirmed
    - **Action:** Keep the recipe. Build on the arm64 builder and check for 'RTL-SDR Blog V4 Lite Detected'. Pin librtlsdr0 and Debian rtl-sdr >= 2.0.2 at -1.
    - **Impact:** Load-bearing for SoapyRTLSDR, welle-cli, OpenWebRX+, SatDump, SDR++, readsb, AIS-catcher and auto_rx.
    - **Sources:**
      - https://github.com/osmocom/rtl-sdr/commit/0204c9cfb1c5ff7bd64f466ce5b8fe53b40a636a
      - https://github.com/osmocom/rtl-sdr/commit/65f0658
      - https://github.com/osmocom/rtl-sdr/commit/7ebcb04
      - https://launchpad.net/ubuntu/+source/rtl-sdr
      - https://sources.debian.org/src/rtl-sdr/2.0.3-1/debian/control/
      - https://luarvique.github.io/ppa/noble/Packages
  2.
    - **Claim in stack:** C11: bias-tee token patch - rtlsdr_set_bias_tee() and rtlsdr_set_bias_tee_gpio() refuse 'on' unless LAB_BIAS_OK equals the device serial
    - **Finding:** A naive gate in rtlsdr_set_bias_tee_gpio() breaks the V4 and the V4L. In tuner_r82xx.c (2.0.3, and after the cherry-pick) the upconverter/input switch on V4/V4L calls rtlsdr_set_bias_tee_gpio(priv->rtl_dev, 5, !cable_x_in) inside r82xx_set_freq. A refused 'on' returns rc<0 and takes 'goto err', so tuning across the HF/VHF/UHF switch points fails. Separately, a token held in an environment variable can be set by any process that is started by hand.
    - **Verdict:** corrected
    - **Action:** Gate only the public entry points, and only the bias pin (GPIO 0). Route internal tuner calls through an ungated static helper (rtlsdr_set_gpio_output/bit). Read the token from a root-owned /run/lab/bias/<serial> file, not only from an environment variable. Add a test: V4L without a token tunes 7 MHz -> 145 MHz -> 435 MHz -> 7 MHz with no error, and the bias pin stays off.
    - **Impact:** Without the fix, HF upconversion and band switching on both V4L receivers fail as soon as the patch ships.
    - **Sources:**
      - https://github.com/osmocom/rtl-sdr/blob/v2.0.3/src/tuner_r82xx.c
      - https://github.com/osmocom/rtl-sdr/blob/v2.0.3/src/librtlsdr.c
  3.
    - **Claim in stack:** C11: fix the 'zerocopy typo' during the rebuild
    - **Finding:** Confirmed and located. Ubuntu noble debian/rules line 12 passes -DENABLE_ZEROCOPY=$DEB_ZEROCOPY_OPTION. Make expands this as $D + 'EB_ZEROCOPY_OPTION', so CMake receives a non-false string and turns zero-copy ON on arm64, although the rules intend OFF on arm64/armel/armhf. The same typo is still in Debian 2.0.3-1.
    - **Verdict:** confirmed
    - **Action:** Change the line to $(DEB_ZEROCOPY_OPTION) in the +lab package. Check that the build log says 'zero-copy support disabled' on arm64.
    - **Impact:** Avoids usbfs mmap problems on the ARM USB stack.
    - **Sources:**
      - https://git.launchpad.net/ubuntu/+source/rtl-sdr/plain/debian/rules?h=ubuntu/noble
      - https://sources.debian.org/src/rtl-sdr/2.0.3-1/debian/rules/
  4.
    - **Claim in stack:** C11: cherry-pick only two commits onto 2.0.1
    - **Finding:** Cherry-picking leaves out the 2.0.2 r82xx fixes: faster and more precise retuning with batched register writes (2acb75c, 0b64f07, f5978e8), gain rounding (d81ef9a) and fc0012 init. osmocom released 2.0.3 on 2026-08-12 with all of these fixes plus both wanted commits. A one-line change of SOVERSION 0 -> 2 in src/CMakeLists.txt would give the same .so.2 package name. The public API is unchanged, but the ABI has not been compared.
    - **Verdict:** new_option
    - **Action:** Optionally build 2.0.3 with SOVERSION=2 as librtlsdr2 +lab, after running abi-compliance-checker against 2.0.1. Otherwise keep the minimal cherry-pick.
    - **Impact:** Faster retune for scanning and survey with the same consumer compatibility.
    - **Sources:**
      - https://github.com/osmocom/rtl-sdr/compare/v2.0.1...v2.0.3
  5.
    - **Claim in stack:** #30/5.4: SatDump master (2.0.0-alpha) from source, without inmarsat_support; last numbered release 1.2.2
    - **Finding:** Confirmed: master HEAD 1aedd60 (2026-09-29) declares project VERSION 2.0.0 with SATDUMP_VERSION_TYPE 'alpha'. The only tags are 1.2.2 and 'nightly'. The build recipe is wrong, though. plugins/CMakeLists.txt has option PLUGINS_ALL default ON, and each plugin is added with if(PLUGIN_X OR PLUGINS_ALL), so passing -DPLUGIN_INMARSAT=OFF on its own still builds inmarsat_support. orbcomm_support (Orbcomm STX demodulator and deframer) is also built, although the STACK bans Orbcomm frame demodulation.
    - **Verdict:** corrected
    - **Action:** Configure with -DPLUGINS_ALL=OFF and an explicit allow-list (METEOR, NOAA_METOP, ELEKTRO_ARKTIKA, FY/GK2A/xRIT as needed, CUBESAT, RADIOSONDE, sdr_sources rtlsdr/airspyhf/soapy/net_source). Keep PLUGIN_INMARSAT and PLUGIN_ORBCOMM OFF. Make the CI audit fail on libinmarsat_support.so or liborbcomm_support.so. Pin the build to a commit hash.
    - **Impact:** As written, the recipe would ship both a banned Inmarsat-C/Aero decoder and a banned Orbcomm decoder.
    - **Sources:**
      - https://github.com/SatDump/SatDump/blob/master/plugins/CMakeLists.txt
      - https://github.com/SatDump/SatDump/tree/master/plugins/orbcomm_support
      - https://github.com/SatDump/SatDump/blob/master/CMakeLists.txt
  6.
    - **Claim in stack:** Decoder allow-list: SatDump (only inmarsat_support removed)
    - **Finding:** SatDump master also builds dmsp_support (DMSP RTD/OLS/SSMIS) and wsf_support (WSF-M MWI). Both are meteorological satellites run by the US military (DoD / Space Force). It also builds spacex_support (Falcon telemetry and video; the STACK already turns off the Falcon9 decoder in SDR++), bluewalker3_support (AST SpaceMobile direct-to-cell test satellite), and two network source plugins, PLUGIN_SDRPP_SERVER_SUPPORT and PLUGIN_REMOTE_SDR_SUPPORT (both default ON).
    - **Verdict:** new_risk
    - **Action:** Apply the WEFAX/Northwood precedent (no military-operated stations) and exclude PLUGIN_DMSP and PLUGIN_WSF. Also exclude PLUGIN_SPACEX and PLUGIN_BLUEWALKER3 for consistency. Set the SDR++ server and remote-SDR source plugins OFF. Record this as a decision.
    - **Impact:** Brings the satellite decoders into line with the hard rule 'nothing aimed at military transmitters'.
    - **Sources:**
      - https://github.com/SatDump/SatDump/tree/master/plugins/dmsp_support
      - https://github.com/SatDump/SatDump/tree/master/plugins/wsf_support
      - https://github.com/SatDump/SatDump/blob/master/plugins/CMakeLists.txt
  7.
    - **Claim in stack:** C7/5.4: SatDump decodes from the recorded baseband; a live feed only 'if 2.0-alpha supports it'; SatDump uses the legacy LimeSuiteNG API
    - **Finding:** Live input is possible. Master keeps the legacy CLI 'satdump live <pipeline> <out> --source ...' (src-cli/legacy/live.cpp), and the net_source_support plugin accepts UDP or nng_sub, so labrx can feed SatDump live over UDP. The Lime plugin uses the legacy LimeSuite API (lime/LimeSuite.h, LIMESUITENG=0). LimeSuiteNG packages this as limesuiteng-legacyapi.
    - **Verdict:** confirmed
    - **Action:** Add a bench test: labrx UDP -> satdump live meteor_m2-x_lrpt on a recorded pass. Keep the decode-from-file path as the default.
    - **Impact:** Removes an open question in the access model.
    - **Sources:**
      - https://github.com/SatDump/SatDump/tree/master/src-cli/legacy
      - https://github.com/SatDump/SatDump/tree/master/plugins/sdr_sources/net_source_support
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro-staging/debian
  8.
    - **Claim in stack:** #31: SDR++ from source; Soapy and airspyhf sources on; pager, M17, Falcon9 and recorder off
    - **Finding:** SDR++ has no tagged release after 1.0.4. Master version.h says 1.3.0, and the last commit (8c9f5ee, 2026-07-04) adds a README warning not to use the distro 'sdrpp' package, so building from source is right. The CMake defaults change the picture: OPT_BUILD_SOAPY_SOURCE is OFF (it must be set ON), PAGER_DECODER ON, RECORDER ON, M17/FALCON9 already OFF. Also ON by default and missing from the STACK: OPT_BUILD_IQ_EXPORTER (streams raw IQ over the network, a bypass of the labrx voice and band masks just like the recorder), DISCORD_PRESENCE, and RIGCTL_CLIENT (drives an external rig as a panadapter).
    - **Verdict:** corrected
    - **Action:** Configure with -DOPT_BUILD_SOAPY_SOURCE=ON -DOPT_BUILD_PAGER_DECODER=OFF -DOPT_BUILD_RECORDER=OFF -DOPT_BUILD_IQ_EXPORTER=OFF -DOPT_BUILD_DISCORD_PRESENCE=OFF -DOPT_BUILD_RIGCTL_CLIENT=OFF. Keep RIGCTL_SERVER for Gpredict Doppler. Make the build audit fail on iq_exporter.so and recorder.so, and never start 'sdrpp --server'. Pin to a commit.
    - **Impact:** Closes a second IQ-export path around the labrx masks.
    - **Sources:**
      - https://github.com/AlexandreRouma/SDRPlusPlus/blob/master/CMakeLists.txt
      - https://github.com/AlexandreRouma/SDRPlusPlus/blob/master/readme.md
      - https://github.com/AlexandreRouma/SDRPlusPlus/tree/master/misc_modules/iq_exporter
  9.
    - **Claim in stack:** 5.4: SDRangel 7.27.2 RX-only on Qt 5.15; forbidden: TX and DSD .so, demodinmarsat, heatmap, doa2, interferometer, beamsteeringcwmod, simpleptt, limerfe, FileSink, SigMF file sink
    - **Finding:** v7.27.2 (tag 97e9e21, 2026-08-19) is the latest tag; master has moved on to 2026-10-17. ENABLE_QT6 defaults OFF, so Qt5 is right. Every plugin name in the forbidden list exists in v7.27.2, and switches exist: ENABLE_CHANNELTX, ENABLE_CHANNELMIMO, ENABLE_CHANNELRX_DEMODINMARSAT/HEATMAP/DEMODDSD/FILESINK/SIGMFFILESINK, ENABLE_FEATURE_SIMPLEPTT/LIMERFE. Banned-category items present but missing from the STACK list: channelrx demodpager (POCSAG), demodmeshtastic and demodmeshcore (LoRa mesh messaging), feature ambe (DV vocoder) and pertester (sends packets). Also missing: samplemimo audiocatsiso (CAT + PTT transceiver control, built automatically when hamlib-dev is found), metismiso (HPSDR transceivers), and the network IQ sinks remotesink, remotetcpsink and udpsink (mask bypass). The samplesink plugins testsink/fileoutput/localoutput/audiooutput are always built, and soapysdroutput is built when Soapy is on.
    - **Verdict:** corrected
    - **Action:** Configure with -DENABLE_CHANNELTX=OFF -DENABLE_CHANNELMIMO=OFF and turn OFF ENABLE_CHANNELRX_{DEMODPAGER,DEMODMESHTASTIC,DEMODMESHCORE,DEMODDSD,DEMODINMARSAT,HEATMAP,FILESINK,SIGMFFILESINK,REMOTESINK,REMOTETCPSINK,UDPSINK} and ENABLE_FEATURE_{AMBE,PERTESTER,SIMPLEPTT,LIMERFE}. Also set ENABLE_METIS=OFF and ENABLE_HACKRF/IIO/BLADERF/USRP/XTRX=OFF. Do not install libhamlib-dev on the builder. Delete every samplesink and samplemimo .so during packaging and add them to the build audit. Optionally drop ENDOFTRAIN.
    - **Impact:** Several banned or mask-bypassing plugins would otherwise ship.
    - **Sources:**
      - https://github.com/f4exb/sdrangel/releases/tag/v7.27.2
      - https://github.com/f4exb/sdrangel/blob/v7.27.2/CMakeLists.txt
      - https://github.com/f4exb/sdrangel/blob/v7.27.2/plugins/samplesink/CMakeLists.txt
      - https://github.com/f4exb/sdrangel/blob/v7.27.2/plugins/samplemimo/CMakeLists.txt
  10.
    - **Claim in stack:** OpenWebRX+ 1.2.126 with --no-install-recommends and exact pins; -1 pins on digiham, codecserver, rtl-433, acarsdec, dumphfdl, dumpvdl2, js8call
    - **Finding:** 1.2.126 is current: changelog dated 5 Oct 2026, and 1.2.127 is still being prepared. It is published as 'Architecture: all' in the luarvique noble repo (arm64 helpers available; the site calls the Noble build experimental). Depends are only owrx-connector >= 0.6.5 and python3-csdr >= 0.18.40; every decoder is a Recommends, so the -1 pins do not conflict. New in 1.2.125: 'optional ability to press RigControl PTT'. owrx/rigcontrol.py starts the 'rigctl' binary and can key a transceiver. The libhamlib-utils ban blocks this, but it must be locked off. The noble repo also ships modes and packages missing from the -1 list: TETRA (dxlaprs-tetra/tetrarx), LoRa and Meshtastic (dxlaprs-lora, python3-meshtastic, python3-pycryptodome, python3-bleak), wM-Bus (through rtl-433), m17-demod, codecserver-driver-ambe3k, libacars-tools, dump978-fa, and its own multimon-ng 1.5.0 (noble has 1.3.0).
    - **Verdict:** corrected
    - **Action:** Mirror openwebrx 1.2.126 together with owrx-connector, rtl-connector, soapy-connector, csdr/python3-csdr 0.18.40-41 and redsea 1.3.1 from the same repo. Add to the -1 list: dxlaprs-tetra, dxlaprs-lora, python3-meshtastic, python3-bleak, m17-demod, codecserver-driver-*, libacars-tools, dump978-fa*, msk144decoder (optional). Ship a config with rig control disabled, and test that the mode list contains no tetra, meshtastic, lora, wmbus, page, selcall, dmr, ysf, p25, hfdl, vdl2 or acars. Disable or hide the built-in MP3 audio recorder.
    - **Impact:** Keeps OpenWebRX+ inside the rules for pager, trunked and private-messaging decoding and for transmitting.
    - **Sources:**
      - https://github.com/luarvique/openwebrx/blob/master/debian/changelog
      - https://github.com/luarvique/openwebrx/blob/master/debian/control
      - https://github.com/luarvique/openwebrx/blob/master/owrx/rigcontrol.py
      - https://github.com/luarvique/openwebrx/blob/master/owrx/modes.py
      - https://luarvique.github.io/ppa/
  11.
    - **Claim in stack:** 5.4: OpenWebRX+ does not see the real multimon-ng (the wrapper is outside its PATH), so pager and selcall modes stay off
    - **Finding:** OWRX+ decides which modes exist by checking the binaries on PATH: FeatureDetector.has_multimon() runs 'multimon-ng --help', and page, selcall and eas all need it. The apt multimon-ng installs to /usr/bin, which is on the PATH of the openwebrx service. Hiding only the wrapper does not hide the real binary.
    - **Verdict:** corrected
    - **Action:** dpkg-divert /usr/bin/multimon-ng to /usr/lib/lab/multimon-ng.real (mode 0750, group labeas). Run openwebrx with a restricted PATH. Self-test: the OWRX+ /features page reports multimon as unavailable.
    - **Impact:** Otherwise POCSAG/FLEX/selcall decoding would appear on any device with multimon-ng installed.
    - **Sources:**
      - https://github.com/luarvique/openwebrx/blob/master/owrx/feature.py
  12.
    - **Claim in stack:** #10/C16: WSJT-X decoders only as jt9/wsprd, through dpkg-divert of /usr/bin/wsjtx; libhamlib-utils (rigctl/rigctld) forbidden
    - **Finding:** These two rules contradict each other. In noble, wsjtx 2.7.0~rc3+repack-1build2 has a hard Depends on libhamlib-utils (and libhamlib4t64), so installing wsjtx to get jt9 and wsprd brings in the forbidden rigctl/rigctld. A divert also keeps the GUI binary on disk under another name. WSJT-X 2.7.0 GA is tagged on SourceForge (wsjtx-2.7.0).
    - **Verdict:** corrected
    - **Action:** Build only jt9 and wsprd (plus any helpers OWRX+ needs) from the wsjtx-2.7.0 source into a lab-wsjt-decoders +lab deb with no Hamlib dependency. Pin wsjtx and libhamlib-utils at -1. OWRX+ finds jt9 on PATH.
    - **Impact:** Removes a packaging dead end and keeps the device free of transmit-capable rig control.
    - **Sources:**
      - https://packages.ubuntu.com/noble/wsjtx
      - https://packages.ubuntu.com/noble/arm64/wsjtx/filelist
      - https://sourceforge.net/p/wsjt/wsjtx/ci/wsjtx-2.7.0/tree/
  13.
    - **Claim in stack:** #29/5.4: Hamlib 4.5.5 from apt, library only, if some dependency pulls it in
    - **Finding:** noble hamlib is 4.5.5-3.2build2 (confirmed); upstream is 4.7.2 (2026-06-21). Nothing in the corrected stack needs the library. Gpredict speaks the rigctld protocol over TCP to the SDR++ rigctl_server and only Recommends libhamlib-utils. Only wsjtx (replaced above) and SDRangel's audiocatsiso (excluded above) link libhamlib.
    - **Verdict:** new_option
    - **Action:** Drop Hamlib completely. Pin libhamlib4t64, libhamlib-utils and libhamlib-dev at -1 on the device and keep libhamlib-dev off the builder. The self-test checks that no libhamlib is loaded.
    - **Impact:** A simpler, smaller attack surface for transmit control.
    - **Sources:**
      - https://launchpad.net/ubuntu/+source/hamlib
      - https://packages.ubuntu.com/noble/gpredict
      - https://github.com/Hamlib/Hamlib/releases
  14.
    - **Claim in stack:** #29: Gpredict 2.3 from noble apt with a 5-digit alias bridge; radios only of type 'RX only'
    - **Finding:** noble ships gpredict 2.3-115-g0f3beb6-3build3, a 2018-era snapshot built without libgps. Upstream has released 2.4 (2025-12-27), 2.5/2.5.1 (2026-03-22), 2.5.2 (2026-07-20, 'support for more recent versions of gpsd', second-rig fix, data-race fix) and 2.6 (2026-08-16, satellite filter in the radio and rotator controllers; NOAA groups removed). 2.6 is still TLE-only, with no OMM or Alpha-5 support, so the alias bridge stays necessary. CelesTrak serves objects numbered 100000 and up only as OMM; the exact run-out date of 5-digit numbers was not checked, because celestrak.org returned 503. The rig controller contains PTT code (set_ptt), so the ban on TX radio types is justified.
    - **Verdict:** new_option
    - **Action:** Build Gpredict 2.6 as a +lab deb (GTK3). Even if it is linked with libgps, keep the QTH written by the location service (a static .qth after the plausibility gate) and never read raw gpsd, so the gate still applies. Keep the alias bridge and the RX-only radio check.
    - **Impact:** Seven years of fixes to rotator, autotrack and map; the gate is preserved.
    - **Sources:**
      - https://github.com/csete/gpredict/blob/v2.6/NEWS
      - https://launchpad.net/ubuntu/+source/gpredict
      - https://celestrak.org/NORAD/elements/
  15.
    - **Claim in stack:** #29/5.4: GNU Radio 3.10.9.2, VOLK 3.1.2, gr-satellites 5.5.0, SoapySDR 0.8.1, SoapyRTLSDR 0.3.3 from noble apt
    - **Finding:** Every version matches noble on Launchpad (gnuradio 3.10.9.2-1.1ubuntu2, volk 3.1.2-1.1build1, gr-satellites 5.5.0-2build2, soapysdr 0.8.1-4build1, soapyrtlsdr 0.3.3-1build1). Upstream in Oct 2026: GNU Radio 3.10.12.0, VOLK 3.3.0, SoapySDR 0.9.0 (2026-10-10, new module ABI), SoapyRTLSDR 0.3.4 (2026-10-10, minor CMake fixes). Do not mix SoapySDR 0.9 with modules built for 0.8. soapysdr-module-all / soapysdr0.8-module-all depend on soapysdr0.8-module-remote, which is SoapyRemote and forbidden.
    - **Verdict:** confirmed
    - **Action:** Keep the noble 0.8 ABI. Pin soapysdr-module-all, soapysdr0.8-module-all and soapysdr0.8-module-remote at -1, and SoapySDR >= 0.9 at -1.
    - **Impact:** Stable module ABI; no hidden route to SoapyRemote.
    - **Sources:**
      - https://launchpad.net/ubuntu/noble/+source/gnuradio
      - https://github.com/pothosware/SoapySDR/blob/master/Changelog.txt
      - https://github.com/pothosware/SoapyRTLSDR/blob/master/Changelog.txt
      - https://packages.ubuntu.com/noble/soapysdr0.8-module-all
  16.
    - **Claim in stack:** gr-satellites 5.5.0 (noble apt)
    - **Finding:** Noble's 5.5.0 dates from 2023-12-28. Upstream has 5.6.0 (2024-09), 5.7.0 (2025-02), 5.8.0 (2025-07) and 5.9.0 (2025-12-14). 5.9.0 adds many 2024-2026 CubeSats (Geoscan-1..6, BOTAN, CroCube, FORESAIL-1P, HYDRA-T/W, INNOCUBE and others) and requires only GNU Radio 3.10 (find_package(Gnuradio "3.10")).
    - **Verdict:** new_option
    - **Action:** Rebuild gr-satellites 5.9.0 as a +lab deb against noble GNU Radio 3.10.9.2 and numpy 1.26. Run its satyaml tests on the device.
    - **Impact:** Covers CubeSats that are currently in orbit; this matters for the Satellites > CubeSats hub.
    - **Sources:**
      - https://github.com/daniestevez/gr-satellites/blob/v5.9.0/CHANGELOG.md
      - https://github.com/daniestevez/gr-satellites/blob/v5.9.0/CMakeLists.txt
  17.
    - **Claim in stack:** #31/5.4: SoapyAirspyHF from source; HF+ ppm correction in labrx or libairspyhf because SoapyAirspyHF does not call airspyhf_set_calibration; libairspyhf from apt
    - **Finding:** SoapyAirspyHF is not in noble (confirmed). 0.2.1 was released 2026-10-10 (CMake updates) and still never calls airspyhf_set_calibration (confirmed). noble libairspyhf is 1.6.8 (2020 tag), but upstream master declares AIRSPYHF_VERSION 1.8.1, with fixes from 2025-07 (4k-sample buffers, IQ-balancer change, use-after-free fix, bias-tee control-call fix) and 2026 build fixes (GCC 15, static libs). There is no newer git tag.
    - **Verdict:** new_option
    - **Action:** Build SoapyAirspyHF at tag soapy-airspyhf-0.2.1 against SoapySDR 0.8.1. Optionally build libairspyhf from a pinned master commit (1.8.1) as libairspyhf0 +lab, after checking the SONAME and ABI. Keep ppm correction in labrx.
    - **Impact:** Better HF+ stability; no change to the access model.
    - **Sources:**
      - https://github.com/pothosware/SoapyAirspyHF/blob/master/Changelog.txt
      - https://github.com/airspy/airspyhf/commits/master
      - https://launchpad.net/ubuntu/+source/airspyhf
  18.
    - **Claim in stack:** #11/5.4 (only if Lime is kept): LimeSuiteNG with -DBUILD_PLUGINS_AMARISOFT=OFF, la9310-limesdr-dkms+lab, TX stream patched to fail
    - **Finding:** The only release, v25.1.0 (2025-01-28), has no LimeSDR Micro or LA9310 code. Micro support exists only on the unreleased branches limesdr-micro (last commit 2026-10-01) and limesdr-micro-staging (2026-10-16). BUILD_PLUGINS_AMARISOFT exists and defaults ON on UNIX (confirmed). The kernel module is la9310_limesdr v0.2.1 with its own DKMS config; it is not in the upstream debian/control (which only has limepcie-dkms). gr-limesuiteng is always added and includes sink blocks. The Soapy module registers the driver key 'limesuiteng'. noble also has legacy limesuite 23.11 (soapysdr0.8-module-lms7).
    - **Verdict:** confirmed
    - **Action:** Pin one staging commit hash. Package la9310_limesdr-dkms yourself for the held kernel. Build with -DBUILD_PLUGINS_AMARISOFT=OFF, without gr-limesuiteng (or audit its sink blocks), and with the TX setupStream patch. Pin limesuite and soapysdr0.8-module-lms7 at -1.
    - **Impact:** The Lime path depends on unreleased code that changes week to week.
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro-staging
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/plugins/CMakeLists.txt
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro-staging/drivers/linux/la9310_limesdr
  19.
    - **Claim in stack:** #7/5.4: gpsd 3.25 with GPSD_OPTIONS="-n -p -s 115200" and DEVICES="/dev/gnss0"; chrony 4.5 with 'refclock PPS /dev/pps0 lock NMEA', 'maxchange 5 1 -1', rtcsync
    - **Finding:** Versions match noble (gpsd 3.25-3ubuntu3.2, chrony 4.5-1ubuntu4.2). The gpsd man page confirms -n (poll without clients), -p (passive, no autoconfiguration) and -s (fixed speed, 115200 allowed). chrony 4.5 docs confirm maxchange: a negative ignore value turns off the limit, so all large offsets are ignored and chronyd never exits. 'lock NMEA' pairs the PPS refclock with another refclock whose refid is NMEA, but the STACK defines no such refclock. Naming the udev link /dev/gnss0 collides with the kernel GNSS subsystem's /dev/gnssN names.
    - **Verdict:** corrected
    - **Action:** Add 'refclock SHM 0 refid NMEA offset <measured> delay 0.2 noselect' (gpsd SHM 0) and write 'refclock PPS /dev/pps0 lock NMEA refid PPS prefer'. Add a bounded makestep for the first sync. Rename the link to /dev/lab/gnss, matching the /dev/lab/<name> rule. Check 'chronyc sources' in W1-2.
    - **Impact:** As written, the PPS refclock has no NMEA source to lock to and never becomes selectable.
    - **Sources:**
      - https://gpsd.gitlab.io/gpsd/gpsd.html
      - https://chrony-project.org/doc/4.5/chrony.conf.html
      - https://launchpad.net/ubuntu/+source/gpsd
      - https://launchpad.net/ubuntu/+source/chrony
  20.
    - **Claim in stack:** C13/C22: pps-gpio as an out-of-tree DKMS module for 6.18.2-4 (CONFIG_PPS=y); libgpiod 1.6.3 (v1 uAPI) in labd
    - **Finding:** noble libgpiod is 1.6.3-1.1build1 (confirmed). libgpiod 1.x uses GPIO character-device uAPI v1, which only works if the held Radxa kernel has CONFIG_GPIO_CDEV_V1=y. In this pass I could not check the 6.18.2-4 kernel config: neither CONFIG_GPIO_CDEV_V1 nor the absence of PPS_CLIENT_GPIO.
    - **Verdict:** unverified
    - **Action:** In W1-2, run 'zcat /proc/config.gz | grep -E "GPIO_CDEV_V1|PPS_CLIENT_GPIO|CONFIG_PPS="'. If CDEV_V1 is missing, move labd to the uAPI v2 ioctl (as Route A already does) or to python3 gpiod v2 in the venv.
    - **Impact:** labd GPIO access fails at boot if CDEV_V1 is off.
    - **Sources:**
      - https://launchpad.net/ubuntu/+source/libgpiod
      - https://docs.kernel.org/userspace-api/gpio/chardev_v1.html
  21.
    - **Claim in stack:** #24/5.4: hold linux-image-6.18.2-4-qcom and the radxa-dragon-q6a metapackages, radxa-firmware-qcs6490, fastrpc, libcdsprpc1, qcom-qnn-sdk-v68; the repository index (24.09.2026) holds only 7.0.11-7
    - **Finding:** Confirmed on the live index. qcs6490-noble Release is dated Thu 24 Sep 2026 and lists only linux-image-7.0.11-7-qcom. linux-image-radxa-dragon-q6a 7.0.11-7 depends on that kernel and on radxa-overlays-dkms. qcom-qnn-sdk-v68 is 0.1.0-2 and fastrpc/libcdsprpc1 1.0.7-3. radxa-firmware-qcs6490 lives in the radxa 'noble' repo. The hold list is missing edk2-radxa-dragon-q6a 0.1.0-9 (depends edk2-qcs6490; SPI BIOS images), radxa-overlays-dkms 0.2.31 and radxa-qcom-qairt 0.1.0-2.
    - **Verdict:** new_risk
    - **Action:** Add edk2-radxa-dragon-q6a, edk2-qcs6490, radxa-overlays-dkms and radxa-qcom-qairt to the hold list and to the aptly mirror. Keep the golden disk image, because 6.18.2-4 cannot be fetched from Radxa any more.
    - **Impact:** An unheld EDK2 or overlays package could change firmware or DT overlays on an update, under the held kernel.
    - **Sources:**
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/Release
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/main/binary-arm64/Packages
      - https://radxa-repo.github.io/noble/dists/noble/main/binary-arm64/Packages
  22.
    - **Claim in stack:** C22/#24: hold Mesa 25.2.8-0ubuntu0.24.04.4 and libdrm 2.4.125; Qt 6.4.2, labwc 0.7.1, greetd 0.9.0, cage 0.1.5, gtk-layer-shell 0.8.2; aptly 1.5.0
    - **Finding:** All match Launchpad: mesa 25.2.8-0ubuntu0.24.04.4 is in noble-updates (noble-security has only .2), libdrm 2.4.125-1ubuntu0.1~24.04.2, qt6-base 6.4.2+dfsg-21.1build5, labwc 0.7.1-1build1, greetd 0.9.0-4ubuntu1, cage 0.1.5+20240127-2build1, gtk-layer-shell 0.8.2-1build2, aptly 1.5.0+ds1-2ubuntu0.24.04.3.
    - **Verdict:** confirmed
    - **Action:** Mirror Mesa from noble-updates, not from -security only.
    - **Impact:** None.
    - **Sources:**
      - https://launchpad.net/ubuntu/+source/mesa
      - https://launchpad.net/ubuntu/+source/libdrm
      - https://launchpad.net/ubuntu/+source/labwc
  23.
    - **Claim in stack:** #35/5.4: aptly repo with lab packages at priority 1001, -1 pin list, Install-Recommends false, unattended-upgrades removed
    - **Finding:** apt_preferences(5) in noble: P >= 1000 installs even if it means a downgrade, and P < 0 prevents the version from being installed. Both mechanisms work as the STACK uses them.
    - **Verdict:** confirmed
    - **Action:** Extend the -1 list with the entries from the other findings: librtlsdr0, wsjtx, libhamlib*, soapysdr*-module-all, soapysdr0.8-module-remote, dxlaprs-tetra, dxlaprs-lora, python3-meshtastic, python3-bleak, m17-demod, codecserver-driver-*, limesuite, soapysdr0.8-module-lms7.
    - **Impact:** None.
    - **Sources:**
      - https://manpages.ubuntu.com/manpages/noble/man5/apt_preferences.5.html
  24.
    - **Claim in stack:** 5.4 update/rollback: A/B root on UFS, systemd-boot with boot counting and a rescue entry; signed offline bundle; bless or roll back
    - **Finding:** noble ships systemd-boot 255.4-1ubuntu8.18 with systemd-bless-boot(.service, -generator) and systemd-bootaa64.efi, so boot assessment is available. Not checked: that the Q6A EDK2 (SPI BIOS 6.0.260120) runs systemd-boot reliably, and how the DTB is provided per slot (a firmware DT, or a 'devicetree' line per BLS entry).
    - **Verdict:** unverified
    - **Action:** In W1-2, boot a two-slot setup with BLS entries carrying +3 tries and a devicetree line for 6.18.2-4. Force a failed boot and confirm that rollback happens.
    - **Impact:** The rollback path is the safety net for every update.
    - **Sources:**
      - https://packages.ubuntu.com/noble/systemd-boot
      - https://packages.ubuntu.com/noble/arm64/systemd-boot/filelist
      - https://systemd.io/AUTOMATIC_BOOT_ASSESSMENT/
  25.
    - **Claim in stack:** C16/5.4: slowrx from source, fed by labrx through shm, UDP or FIFO
    - **Finding:** Upstream windytan/slowrx master (last commit 2024-07-30) is a GTK3 GUI whose only input is an ALSA capture device (pcm.c); it cannot read a FIFO, UDP or file. File and stdin input exist only on the abandoned 2016 'dev' branch. A headless daemon, slowrxd, exists on sjlongland/slowrx branch slowrx-daemon (2024-12-17), but it also reads from ALSA.
    - **Verdict:** corrected
    - **Action:** Feed slowrx or slowrxd through an ALSA PCM: a PipeWire virtual source fed by labrx with pw-cat, or snd-aloop. Prefer slowrxd for the headless path and pin its commit. Keep OWRX+ SSTV as the fallback.
    - **Impact:** The ISS SSTV 437.550 MHz chain would not run as described.
    - **Sources:**
      - https://github.com/windytan/slowrx
      - https://github.com/sjlongland/slowrx/tree/slowrx-daemon
  26.
    - **Claim in stack:** #34/C22: per-tool venvs - NanoVNA-Saver main via pipx; QtTinySA with PySide6 6.12 aarch64 wheels (manylinux_2_39); Skyfield 1.55, sgp4 2.27; lab-venv numpy<2; ONNX Runtime 1.31
    - **Finding:** PyPI as of Oct 2026: Skyfield 1.55 (2026-08-07), sgp4 2.27 (2026-07-03), from_omm present since Skyfield 1.49. PySide6 6.12.0 (2026-10-08) has a pyside6-6.12.0-cp310-abi3-manylinux_2_39_aarch64 wheel. onnxruntime 1.31.0 (2026-10-09) has cp312 manylinux_2_28_aarch64. NanoVNA-Saver is not on PyPI; the latest tag is v0.7.3 (requires-python <3.13, pyside6~=6.8, numpy~=2.1, scipy~=1.14; fine on noble Python 3.12). QtTinySA v2.0.1 uses PySide6 and pyqtgraph and is developed on Python 3.14 / Kubuntu 26.04.
    - **Verdict:** confirmed
    - **Action:** Pin NanoVNA-Saver to tag v0.7.3 instead of 'main'. Test QtTinySA v2.0.1 on Python 3.12 inside the return window. Keep numpy<2 only in the venv that imports apt GNU Radio.
    - **Impact:** Reproducible builds.
    - **Sources:**
      - https://pypi.org/project/skyfield/
      - https://pypi.org/project/sgp4/
      - https://pypi.org/project/PySide6/#files
      - https://pypi.org/project/onnxruntime/#files
      - https://github.com/NanoVNA-Saver/nanovna-saver/blob/v0.7.3/pyproject.toml
      - https://github.com/g4ixt/QtTinySA
  27.
    - **Claim in stack:** Decoder allow-list: readsb/tar1090 with dbFlags&1 suppressed, AIS-catcher, radiosonde_auto_rx (uploads off), welle-cli, redsea, Virgo, GNSS-SDR 0.0.19 (or 0.0.22 from source), multimon-ng (EAS only), Artemis 4.2.0
    - **Finding:** Current versions and dates. readsb v3.16.17 (2026-09-27); README-json defines military = dbFlags & 1. AIS-catcher v0.70 (2026-06-19); it shares data with aiscatcher.org only with -X. radiosonde_auto_rx 1.9.0 (2026-09-19); its example station.cfg ships sondehub_enabled = True, so uploads must be switched off explicitly. noble welle.io 2.4 includes /usr/bin/welle-cli and depends on librtlsdr2 (upstream 2.7). redsea 1.3.1 arm64 is in the OWRX+ noble repo but not in Ubuntu. GNSS-SDR 0.0.22 was released 2026-10-04 (noble has 0.0.19). multimon-ng 1.6.2 upstream (2026-09-26). Virgo's newest tag v3.8.9 is from 2022, and PyPI astro-virgo 3.8.2 is older. Artemis 4.2.0 confirmed. The STACK's 'AIS type 35' is the AIS ship-type code 35 (military operations), not a message type.
    - **Verdict:** confirmed
    - **Action:** Pin each tool to its tag. Ship auto_rx with sondehub_enabled = False and test it. Build readsb and AIS-catcher against the librtlsdr2 +lab package. Optionally use GNSS-SDR 0.0.22. Correct the wording to 'AIS ship type 35'.
    - **Impact:** None.
    - **Sources:**
      - https://github.com/wiedehopf/readsb/blob/dev/README-json.md
      - https://github.com/jvde-github/AIS-catcher
      - https://github.com/projecthorus/radiosonde_auto_rx/blob/master/auto_rx/station.cfg.example
      - https://packages.ubuntu.com/noble/arm64/welle.io/filelist
      - https://github.com/gnss-sdr/gnss-sdr/releases
      - https://github.com/AresValley/Artemis/releases
  28.
    - **Claim in stack:** Other apt versions in the stack: nanovna-saver 0.6.3 and skyfield 1.48 rejected; QSSTV 9.5.8, fldigi 4.2.03 and wsjtx 2.7.0~rc3 named as TX-capable; PulseView 0.4.2, fx2lafw 0.1.7
    - **Finding:** All match noble on Launchpad: nanovna-saver 0.6.3-1, skyfield 1.48+ds-1, qsstv 9.5.8-3build3, fldigi 4.2.03-1build3, wsjtx 2.7.0~rc3+repack-1build2, js8call 2.2.0, direwolf 1.7, pulseview 0.4.2-3build4, sigrok-firmware-fx2lafw 0.1.7-1, sigrok-cli 0.7.2, openocd 0.12.0, picocom 3.1.
    - **Verdict:** confirmed
    - **Action:** None.
    - **Impact:** None.
    - **Sources:**
      - https://launchpad.net/ubuntu/noble
- **Current status oct 2026:** Status as of 18 Oct 2026, from primary git, apt and PyPI indexes.
  
  Receivers and libraries:
  - osmocom rtl-sdr 2.0.3 (12 Aug 2026) includes V4L (R828S) support (0204c9c) and the USB-hang fix (65f0658), but uses SOVERSION 0. Debian sid/forky moved to librtlsdr0 (2.0.3-1, 6 Sep 2026). noble still has 2.0.1-2build1 (librtlsdr2), and the zerocopy typo is still in its debian/rules.
  - libairspyhf master is 1.8.1 with no new tag (noble has 1.6.8).
  - SoapySDR 0.9.0, SoapyRTLSDR 0.3.4 and SoapyAirspyHF 0.2.1 were all released 10 Oct 2026.
  - LimeSuiteNG: the only release is v25.1.0 (Jan 2025). LimeSDR Micro (LA9310) support exists only on limesdr-micro-staging (commit 16 Oct 2026).
  
  Main applications:
  - SatDump: still 2.0.0-alpha on master (29 Sep 2026); last numbered release 1.2.2.
  - SDR++: no release after 1.0.4; master is 1.3.0, last commit 4 Jul 2026, and the README warns against the distro package.
  - SDRangel: v7.27.2 (19 Aug 2026) is the latest tag; master is active (17 Oct 2026).
  - OpenWebRX+: 1.2.126 (5 Oct 2026) is in the luarvique noble repo (experimental); 1.2.127 is in preparation. 1.2.125 added RigControl PTT.
  
  GNU Radio, satellite and tracking:
  - GNU Radio 3.10.12.0 and VOLK 3.3.0 upstream; noble has 3.10.9.2 and 3.1.2.
  - gr-satellites 5.9.0 (14 Dec 2025); noble has 5.5.0.
  - Gpredict 2.6 (16 Aug 2026), still TLE-only; noble has a 2.3 snapshot.
  - GNSS-SDR 0.0.22 (4 Oct 2026).
  
  Decoders:
  - readsb 3.16.17, AIS-catcher 0.70, radiosonde_auto_rx 1.9.0, multimon-ng 1.6.2, Hamlib 4.7.2.
  - WSJT-X 2.7.0 GA (noble has rc3, which hard-depends on libhamlib-utils).
  - slowrx master is unchanged since Jul 2024 and has ALSA-only input.
  
  Python:
  - Skyfield 1.55, sgp4 2.27, PySide6 6.12.0 (aarch64 manylinux_2_39), ONNX Runtime 1.31.0, NanoVNA-Saver v0.7.3, QtTinySA v2.0.1, TorchSig 2.2.0, SigMF spec 1.2.6.
  
  Radxa and noble pockets:
  - The Radxa qcs6490-noble index (24 Sep 2026) carries only kernel 7.0.11-7; the 6.18.2-4 kernel must come from the mirror or the golden image. Also present there: EDK2 meta 0.1.0-9, radxa-overlays-dkms 0.2.31, qcom-qnn-sdk-v68 0.1.0-2.
  - noble-updates: Mesa 25.2.8-0ubuntu0.24.04.4, libdrm 2.4.125, systemd-boot 255.4-1ubuntu8.18 with bless-boot.
  
  No EOL notices were found for any component. All components are free open-source software, so there are no prices or stock to report.
- **Notes:** Method: shallow or blobless git clones of upstream repositories (read only), the Launchpad API for noble versions, packages.ubuntu.com for dependency and file lists, sources.debian.org, the OpenWebRX+ and Radxa apt indexes, PyPI JSON, the gpsd and chrony docs, and 2 WebSearch calls. The GitHub REST API was blocked in this session, so release dates come from tag or commit dates.
  
  Compile test: v2.0.1 with 65f0658 and 0204c9c cherry-picked builds on x86-64 with SONAME librtlsdr.so.2. This was not built for arm64 and not tested on hardware.
  
  Not verified:
  - Radxa 6.18.2-4 kernel config (GPIO_CDEV_V1, PPS_CLIENT_GPIO).
  - systemd-boot with DTB handling on the Q6A EDK2.
  - The exact CelesTrak date when 5-digit catalog numbers ran out (site returned 503).
  - Whether github.com/wsjtx/wsjtx (v3.x tags) is the official WSJT-X home. SourceForge tag wsjtx-2.7.0 is the confirmed GA.
  - CPU load of any engine on the Q6A.
  
  Highest-impact fixes, in order:
  1. Narrow the bias-tee token gate to GPIO 0, or it breaks V4/V4L band switching.
  2. SatDump needs PLUGINS_ALL=OFF; otherwise inmarsat_support and orbcomm_support still get built.
  3. wsjtx in noble hard-depends on libhamlib-utils; build jt9/wsprd yourself.
  4. Turn off SDR++ iq_exporter and SDRangel demodpager/meshtastic/meshcore/audiocatsiso/network sinks.
  5. Move the real multimon-ng off PATH and extend the OWRX+ -1 list (TETRA, Meshtastic/LoRa).
  6. Add a chrony NMEA refclock for 'lock NMEA'.
  7. slowrx needs ALSA or PipeWire input.
  8. Hold the EDK2 and overlays packages.
  
  Policy question for the decision register: exclude SatDump DMSP and WSF-M (US military-operated weather satellites) under the Northwood precedent.
  
  Working files (scratch, not deliverables): /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/sw_repos (clones), /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/owrx_noble_Packages, /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/radxa_qcs6490_Packages, /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/radxa_noble_Packages, /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/chrony45.txt.

