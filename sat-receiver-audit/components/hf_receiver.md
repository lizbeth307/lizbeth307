# Hf receiver: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_feb0e95a-cfc`_

- **Subsystem:** hf_receiver (Airspy HF+ Discovery, arm64 driver stack, EMI and power, VHF backup role, HF/LF decoders, HF wire + 9:1 + Boni-Whip)
- **Findings:**
  1.
    - **Claim in stack:** Part choice: Airspy HF+ Discovery as the HF/LF receiver and second VHF receiver; $169 at ITEAD; buy only from dealers on the airspy.com list (STACK 2.2, #92, 1.1 C17).
    - **Finding:** Still current in Oct 2026. The airspy.com product page is live and no EOL notice or successor was found. ITEAD lists USD 169.00 with EU and US warehouses (3-6 business days) and China (15-35 days); it states no stock count. WiMo lists EUR 232.00 incl. VAT (EUR 194.96 net), in stock, ships in 1-2 days. airspy.com/purchase names ITEAD, WiMo, AOR, RTL-SDR Blog, AstroRadio, Ham Shop NL, FB Radio, Moonraker, Neven and SDR UA, and no AliExpress store. The 2026 summer sale ($135.20, 27 Jun-4 Jul 2026) is over. Airspy R2 clones have appeared on AliExpress before, so the dealer-only rule stands.
    - **Verdict:** confirmed
    - **Action:** Keep. Buy from ITEAD (US/EU warehouse) or WiMo. Record the serial number and firmware version on arrival (see the firmware finding).
    - **Impact:** No change to BOM price ($169).
    - **Sources:**
      - https://airspy.com/airspy-hf-discovery/
      - https://itead.cc/product/airspy-hf-discovery/
      - https://www.wimo.com/en/airspy-discovery
      - https://airspy.com/purchase
      - https://www.rtl-sdr.com/airspy-2026-summer-sale-20-off-all-airspy-products/
      - https://www.rtl-sdr.com/cloned-sdrplay-and-airspy-units-now-appearing-on-aliexpress-ebay/
  2.
    - **Claim in stack:** Specs: 0.5 kHz-31 MHz and 64-260 MHz; IIP3 +15 dBm (HF) / +13 dBm (VHF); BDR 110/95 dB; MDS -140 dBm in 500 Hz; 768 ksps = 660 kHz alias-free; 45x60x10 mm; 0.5 ppm.
    - **Finding:** Every figure matches airspy.com word for word. The HF MDS is quoted at 15 MHz. The page adds: VHF MDS -141.5 dBm (64-118 MHz) and -141.0 dBm (118-260 MHz); 2x sigma-delta ADCs at up to 36 MSPS with an 18-bit DDC; +10 dBm maximum input; 1 ppb frequency-adjust step; -45 to +85 C operating range. ITEAD and WiMo print 60-260 MHz and WiMo prints 9 kHz; use airspy.com's 64-260 MHz. WiMo gives 32 g, and ITEAD's 105.6 g most likely includes packaging. Airspy publishes no DC rating for the input.
    - **Verdict:** confirmed
    - **Action:** Keep the specs. Add the -45 to +85 C range to the thermal budget. The bias-tee path must block DC toward the HF+ input, because only +10 dBm RF is rated.
    - **Impact:** Thermal margin inside the sealed case is fine (85 C rating).
    - **Sources:**
      - https://airspy.com/airspy-hf-discovery/
      - https://www.wimo.com/en/airspy-discovery
      - https://rigpix.com/miscrx/airspy_hfplusdiscovery.htm
  3.
    - **Claim in stack:** Sample rate: HF-F profile at 768 ksps (660 kHz alias-free) is the maximum; ci16 at 3.07 MB/s.
    - **Finding:** The official firmware changelog lists more rates. R2.8.0/R3.0.7 added 912 ksps and 456 ksps. R4.0.0 replaced 256k with 228k. R4.0.4 added 650 ksps Low-IF. 768 ksps is the Zero-IF default, and 384/192 ksps are Low-IF. Airspy publishes the alias-free width only for 768 ksps. Scaling it to 912 ksps gives about 784 kHz, but that is my model, not a published figure. At 912 ksps, ci16 is 3.65 MB/s. Low-IF rates (650/384/192) avoid the centre DC/IQ spike in narrow LF and NAVTEX windows.
    - **Verdict:** new_option
    - **Action:** In labrx, enumerate rates with airspyhf_get_samplerates instead of hard-coding 768k. Measure the alias-free width at 912 ksps before using it for the survey profile. Consider 650 ksps Low-IF for the LF window around 290 kHz.
    - **Impact:** Up to about 18% wider HF waterfall (unverified width); +0.58 MB/s.
    - **Sources:**
      - https://airspy.com/downloads/hfplus_changelog.txt
      - https://airspy.com/downloads/airspy-hf-flash-2024-12-11_5.0.1.zip
  4.
    - **Claim in stack:** STACK names no firmware version; the HF+ sits behind the CH334F hub (port H4).
    - **Finding:** Latest stable firmware is R5.0.1 (2024-12-11). R5.0.0 improved gain distribution and AGC/ATT/preamp; R5.0.1 improved AGC hysteresis. R4.0.5 'Adjusted the buffering to support slow USB controllers and USB hubs', which matters behind the CH334F. ITEAD's page still shows firmware R2.0.0 (2019), so units may ship with old firmware. Two silicon variants exist, BB and CD (R2.1.0 added the STA709CD variant), and each takes its own binary. The official flasher works only on Windows. FLASH.bat finds the SAM-BA port (VID_03EB&PID_6124) with wmic, uses pnputil and hfplus_ppb/hfplus_reboot/hfplus_fw .exe, then bossac. Microsoft removed WMIC from supported Windows 11 in the August 2026 (24H2/25H2) and September 2026 (26H1) preview updates, and it can no longer be added back as a Feature on Demand. FLASH.bat's device search will therefore fail on an up-to-date Windows 11 PC.
    - **Verdict:** new_risk
    - **Action:** On arrival, run airspyhf_info. If the firmware is older than R5.0.1, flash at home base: use Windows 10 or a Windows 11 that still has WMIC, or Microsoft's temporary wmic_dlc package, or run the steps by hand (save ppb with hfplus_ppb.exe, run hfplus_reboot.exe, bossac -e -w -v -b -p COMx with the bb or cd binary that hfplus_fw.exe reports, bossac --reset, restore ppb). Minimum acceptable firmware is R4.0.5 (hub buffering). Add the firmware version to the bring-up checklist.
    - **Impact:** Risk of USB drops behind the hub on old firmware. The flashing step needs a Windows PC; no extra cost.
    - **Sources:**
      - https://airspy.com/airspy-hf-discovery/
      - https://airspy.com/downloads/hfplus_changelog.txt
      - https://airspy.com/downloads/airspy-hf-flash-2024-12-11_5.0.1.zip
      - https://itead.cc/product/airspy-hf-discovery/
      - https://support.microsoft.com/en-us/topic/windows-management-instrumentation-command-line-wmic-removal-from-windows-e9e83c7f-4992-477f-ba1d-96f694b8665d
  5.
    - **Claim in stack:** arm64 driver: Ubuntu noble airspyhf / libairspyhf1 / libairspyhf-dev 1.6.8-4build1, no source build needed (lab_ui_hf; STACK 5.4 labrx uses libairspyhf).
    - **Finding:** Noble 1.6.8-4build1 is in universe for arm64. Upstream has no tag after 1.6.8 (9 Apr 2020), but master is now 1.8.1: version bump on 12 Jul 2025, last commit 24fe8ff on 22 Jul 2026. Master adds airspyhf_set_att(float), airspyhf_get_att_steps, frontend options, a bias-tee API, 4096-sample transfers (was 2048), a GCC 15 fix and an INSTALL_STATIC_LIBS option. SOVERSION stays 0. A use-after-free in free_transfers() was introduced after 1.6.8 and fixed in 0130450; I checked that 1.6.8 does not have it. Debian stable/testing/sid and Ubuntu 26.04 still ship 1.6.8. Firmware R4.0.1 claims fallback support for old libraries.
    - **Verdict:** corrected
    - **Action:** Default: keep the noble 1.6.8 package (stable, already on arm64). If labrx needs finer attenuation or frontend options, build 1.8.1 as a +lab deb pinned at 24fe8ff (never at a commit between 1.8.0 and 0130450). Run a 1 h soak test with SDR++, SDRangel and SoapyAirspyHF before replacing 1.6.8, because ABI compatibility beyond the unchanged soname is not verified.
    - **Impact:** No cost. Avoids building a master with the use-after-free bug.
    - **Sources:**
      - https://packages.ubuntu.com/search?keywords=airspyhf&searchon=names&suite=all&section=all
      - https://tracker.debian.org/pkg/airspyhf
      - https://github.com/airspy/airspyhf/tags
      - https://github.com/airspy/airspyhf/commits/master
      - https://github.com/airspy/airspyhf/commit/c0bb66d
      - https://github.com/airspy/airspyhf/commit/0130450
      - https://raw.githubusercontent.com/airspy/airspyhf/master/libairspyhf/src/airspyhf.h
      - https://raw.githubusercontent.com/airspy/airspyhf/master/libairspyhf/src/CMakeLists.txt
  6.
    - **Claim in stack:** HF+ ppm correction must be done in labrx or libairspyhf because SoapyAirspyHF does not call airspyhf_set_calibration (STACK #31, labrx row).
    - **Finding:** Partly right. SoapyAirspyHF Settings.cpp makes no calibration call and uses only the legacy airspyhf_set_hf_att (6 dB steps), hf_lna and hf_agc. SDR++'s airspyhf_source makes no calibration call either. But libairspyhf, both 1.6.8 and master, reads calibration_ppb from device flash in airspyhf_open_init and applies it in set_freq. A ppb value stored once with airspyhf_set_calibration + airspyhf_flash_configuration (streaming stopped), or with the airspyhf_calibrate tool, therefore applies automatically in Soapy, SDR++, SDRangel, OpenWebRX+, AIS-catcher and SatDump. SoapyAirspyHF is packaged only in Ubuntu 26.04 (0.2.0-1), not in noble, so building it from source is confirmed. OpenWebRX(+) reaches the HF+ only through SoapySDR.
    - **Verdict:** corrected
    - **Action:** Calibrate once against the GNSS-SDR/PPS reference and store the value in HF+ flash. Remove the separate HF+ ppm correction from labrx, or make labrx read the stored value instead of adding its own, so the correction is not applied twice. Keep building SoapyAirspyHF from source on noble.
    - **Impact:** Simpler and consistent frequency accuracy in every engine; removes a double-correction bug path.
    - **Sources:**
      - https://raw.githubusercontent.com/pothosware/SoapyAirspyHF/master/Settings.cpp
      - https://raw.githubusercontent.com/AlexandreRouma/SDRPlusPlus/master/source_modules/airspyhf_source/src/main.cpp
      - https://raw.githubusercontent.com/airspy/airspyhf/master/libairspyhf/src/airspyhf.c
      - https://raw.githubusercontent.com/airspy/airspyhf/1.6.8/libairspyhf/src/airspyhf.c
      - https://github.com/airspy/airspyhf/tree/master/tools/src
      - https://packages.ubuntu.com/search?keywords=soapysdr0.8-module-airspyhf&searchon=names&suite=all&section=all
      - https://github.com/jketterl/openwebrx/wiki/Supported-Hardware
  7.
    - **Claim in stack:** Sample format: HF+ is cf32 natively in libairspyhf (kept in the ring), written to disk as ci16 at 3.07 MB/s (5.5, 5.4).
    - **Finding:** Confirmed. airspyhf_transfer_t delivers airspyhf_complex_float_t. The device sends int16 IQ, which the library scales by 1/32768 times a rate-dependent filter gain. With lib_dsp on, it also applies IQ balancing (Zero-IF only) and a fine frequency shift. ci16 written back from cf32 is therefore post-DSP and rescaled, not the raw USB stream.
    - **Verdict:** confirmed
    - **Action:** In labrx, store the scale factor and the lib_dsp on/off state in the SigMF metadata of HF+ ci16 recordings.
    - **Impact:** Recording metadata only.
    - **Sources:**
      - https://raw.githubusercontent.com/airspy/airspyhf/master/libairspyhf/src/airspyhf.h
      - https://raw.githubusercontent.com/airspy/airspyhf/master/libairspyhf/src/airspyhf.c
  8.
    - **Claim in stack:** USB: HF+ on CH334F H4 behind a load switch; open question 'HF+ USB connector type' (section 8).
    - **Finding:** ITEAD requires a high-speed USB 2.0 host. CH334F is a 480 Mb/s USB 2.0 hub, and the CH334 family supports MTT, so the 3.1-3.7 MB/s stream fits. Connector: WiMo's box contains a USB-A to Micro-USB-B cable, so the device port is micro-USB B (inferred from the cable; the port type itself is not stated). Firmware R2.9.6 added fragmented streaming for hubs and R4.0.5 added hub buffering.
    - **Verdict:** corrected
    - **Action:** Close the open item: micro-USB B. Use a short shielded micro-USB lead (right-angle if space needs it) with strain relief or a clamp inside the shield, because micro-USB retention is weak in a handheld that gets shaken. Require firmware ≥R4.0.5.
    - **Impact:** Mechanical detail; about $3-5 for the cable.
    - **Sources:**
      - https://itead.cc/product/airspy-hf-discovery/
      - https://www.wimo.com/en/airspy-discovery
      - https://core-electronics.com.au/adafruit-ch334f-mini-2-port-usb-hub-breakout.html.plain.md
      - https://airspy.com/downloads/hfplus_changelog.txt
  9.
    - **Claim in stack:** EMI: the HF+ case is plastic, so a tin shield + LC + Mix-31 on VBUS, placed farthest from the buck converters (2.3, 5.7.6/7).
    - **Finding:** The stock enclosure is plastic, confirmed. But RF shielding is already provided inside the unit by the PCB, a metal can and EMI-absorbing material. Airspy's author says a metal case is not needed for PCB noise rejection and mainly helps heat dissipation in 24/7 use. The remaining ingress paths are therefore the USB cable and ground common mode and the antenna coax. A Mix-31 bead gives little impedance at LF (60-500 kHz) (general ferrite behaviour, not measured here), so LF filtering must come from the LC stage.
    - **Verdict:** confirmed
    - **Action:** Keep the shield and filtering, and give the LC stage its job: set its corner far below 60 kHz (for example about 100 uH / 100 uF ≈ 1.6 kHz, model) and rate it for the measured current. Give the tin shield thermal contact to the mid plate. Run the A/B noise test with and without the shield before finalising.
    - **Impact:** Low cost ($8-15 as budgeted); clearer test criteria.
    - **Sources:**
      - https://www.rtl-sdr.com/a-new-aftermarket-airspy-hf-discovery-aluminum-enclosure-for-sale/
      - https://www.rtl-sdr.com/going-portable-with-the-airspy-hf-rapsberry-pi-and-7-inch-touch-lcd/
  10.
    - **Claim in stack:** Current draw: not published; preliminary budget 0.3 A at 5 V; set TPS2553 / PTC to 1.5-2x measured (section 8).
    - **Finding:** Still not published. Airspy, RigPix ('? mA') and RigReference give no figure. icholakov's USB-meter video includes the Discovery, but its numbers are not available as text. The only figure found is a speculative 2.2 W estimate (about 0.44 A) for the original HF+, not the Discovery. The 0.3 A budget is unverified and could trip a 0.3 A limit at bring-up.
    - **Verdict:** unverified
    - **Action:** Bring up with the TPS2553 limit at ≥0.75 A (or the LAB-port setting). Measure cold and hot at 768 and 912 ksps, then set the limit to 1.5-2x the measured value. Keep 0.3 A in the energy model only as a placeholder.
    - **Impact:** Mode E 'LF/HF Quiet' runtime (7.1 h / 6.1 h) is uncertain until measured.
    - **Sources:**
      - https://rigpix.com/miscrx/airspy_hfplusdiscovery.htm
      - https://rigreference.com/rigs/6437-hf-discovery
      - https://www.rtl-sdr.com/measuring-the-usb-power-consumption-of-various-software-defined-radios/
  11.
    - **Claim in stack:** VHF backup role: HF+ covers AIS, FM-RDS and DAB through relay K2 / P6 (summary line 3, 4.2 FM-RDS/DAB row, 5.3 P6 and the DAB row with welle-cli).
    - **Finding:** AIS is confirmed: the AIS-catcher README lists the Airspy HF+. FM/RDS is confirmed: one station fits in 768 ksps, and SDRangel's BFM demodulator decodes RDS. DAB is wrong. SDRangel's DAB demodulator uses 2.048 MHz sampling with a typical 1.537 MHz RF bandwidth, and welle.io states 'Airspy HF+ is not supported due to limited bandwidth.' The HF+ maximum is 912 ksps.
    - **Verdict:** corrected
    - **Action:** Remove DAB from the HF+ in every table (lines 3, 505, 685, 710). DAB/DAB+ goes only to the spare V4L (2.048 Msps) through welle-cli. The HF+ VHF role stays AIS (default), FM-RDS, NFM airband/VOR 108-118 MHz.
    - **Impact:** No cost. Fixes a capability claim that could not work.
    - **Sources:**
      - https://github.com/f4exb/sdrangel/blob/master/plugins/channelrx/demoddab/readme.md
      - https://github.com/AlbrechtL/welle.io
      - https://github.com/jvde-github/AIS-catcher
  12.
    - **Claim in stack:** Time signals: SDRangel Radio Clock decodes DCF77/MSF/WWVB/TDF; JJY 60 kHz amplitude only because 'Radio Clock does not support it' (#3, 4.2).
    - **Finding:** The current Radio Clock readme lists MSF 60 kHz, DCF77 77.5 kHz, TDF 162 kHz (phase), WWVB 60 kHz, JJY (40 kHz, OOK), RBU 66.666 kHz and PCSK-225 (Poland, 225 kHz). JJY is supported. NICT describes one JJY time code for both stations (Ohtakadoyayama 40 kHz, Haganeyama 60 kHz), so decoding at 60 kHz is likely but not verified in SDRangel. RBU is not on the civilian carrier list in user_requirements. PCSK-225 is a civil broadcaster's time code.
    - **Verdict:** corrected
    - **Action:** Allow JJY decoding (40 kHz verified; test 60 kHz on a recording). Keep RBU out of the allow-list by policy. PCSK-225 is optional as a civil time code (decode only, not SID). The SID list stays DCF77/MSF/WWVB/JJY/TDF, amplitude only.
    - **Impact:** Adds JJY time decoding; no cost.
    - **Sources:**
      - https://github.com/f4exb/sdrangel/blob/master/plugins/channelrx/radioclock/readme.md
      - https://jjy.nict.go.jp/jjy/trans/index-e.html
  13.
    - **Claim in stack:** NAVTEX 490/518 kHz via sdrangelsrv; DRM via SDRangel/OpenWebRX+; one HF+ window centred about 290 kHz covers 60/77.5/490/518 kHz.
    - **Finding:** SDRangel master has demodnavtex, demoddrm, radioclock, demodrtty, demodft8, demoddsc and demodwefax. The DRM plugin handles robustness modes A-D (4.5-20 kHz) at a 48 kHz channel rate, mode E (DRM+) needs ≥192 kHz, and it decodes AAC+SBR/PS and xHE-AAC. Latest SDRangel is v7.27.2 (19 Aug 2026; adds a Qt6 deb for Ubuntu 26.04, Qt5 build unchanged). Window check (model): 768 ksps gives ±330 kHz alias-free, so 290 kHz ±330 kHz spans -40 to 620 kHz and contains all four carriers. The mirror of a real LF carrier lands at -(f+290) kHz offset; for JJY 40 kHz that is at the -330 kHz band edge, harmless.
    - **Verdict:** confirmed
    - **Action:** Keep. Use SDRangel demoddrm for DRM (OpenWebRX needs an external Dream binary, whose OpenWebRX+ status I did not confirm). Optionally use 650 ksps Low-IF for the LF window.
    - **Impact:** None.
    - **Sources:**
      - https://github.com/f4exb/sdrangel/tree/master/plugins/channelrx
      - https://github.com/f4exb/sdrangel/blob/master/plugins/channelrx/demoddrm/readme.md
      - https://github.com/f4exb/sdrangel/releases
      - https://www.rtl-sdr.com/kiwisdr-now-supports-drm-decoding/
  14.
    - **Claim in stack:** FT8/WSPR decode-only: install wsjtx and dpkg-divert /usr/bin/wsjtx, use only jt9/wsprd; libhamlib-utils (rigctl/rigctld) removed by the TX-software rule (#10, 6.1).
    - **Finding:** Noble wsjtx 2.7.0~rc3+repack-1build2 (arm64) ships /usr/bin/jt9 and /usr/bin/wsprd. It also has a hard 'dep: libhamlib-utils', plus libhamlib4t64, Qt5 and others. 'apt install wsjtx' therefore installs exactly the rig-control utilities that STACK removes by rule, and dpkg-divert on the GUI does not stop that. SDRangel has an RX-only demodft8 plugin (FT8/FT4).
    - **Verdict:** new_risk
    - **Action:** Do not install the noble wsjtx package. Build jt9 and wsprd from WSJT-X source as a decode-only +lab deb with no hamlib-utils dependency, or ship an audited equivs stub for libhamlib-utils. Alternatively use SDRangel demodft8 for FT8/FT4 and source-built wsprd for WSPR. Add a CI policy check that rigctl/rigctld are absent.
    - **Impact:** Keeps the TX-software rule (user_requirements P2). Build effort only.
    - **Sources:**
      - https://packages.ubuntu.com/noble/wsjtx
      - https://packages.ubuntu.com/noble/arm64/wsjtx/filelist
      - https://github.com/f4exb/sdrangel/tree/master/plugins/channelrx
  15.
    - **Claim in stack:** Boni-Whip: 9 kHz-300 MHz, supply 9-15 V, about 14 cm, 189 g, bias tee included; fed at 12.5 V ±0.25 V from TPS7A4701 through PTC 0.2 A and an internal bias tee; 'fits both published ranges' (C17, 2.5, 1053).
    - **Finding:** The manufacturer (bonito.net) gives 20 kHz-300 MHz, supply 12-15 V, body about 17 cm, gain 3 dB, IP3 +32.5 dBm, IP2 +55 dBm, with a power inserter (bias tee) and whip included. WiMo gives 9 kHz-300 MHz, about 14 cm and 189 g, and its Spanish page gives 9-15 V. Current is not published; the sibling Boni-Whip Marine draws about 60 mA at 12 V. Model (assumed resistances, not measured): with the 12.25 V minimum setpoint, a 50-100 mA load, PTC 1-4 Ω, choke DCR 1-10 Ω and 5-10 m of thin coax at 0.35-1.0 Ω/m loop, the antenna sees 9.9-12.1 V, below Bonito's 12 V minimum in almost every case. The whip is E-field, not a loop, and the body fits the 20-23 cm piece rule.
    - **Verdict:** new_risk
    - **Action:** Raise BONI12V5 to about 13.8 V ±0.2 V (≤15 V). At the 4S end of discharge the LDO drops out to about 13.0 V, which is still acceptable. Accept it only if the measured antenna-end voltage is ≥12.3 V at the measured current. Correct the specs to 20 kHz (manufacturer) and 12-15 V. Keep PTC hold at 0.2 A until current is measured. Rename the rail.
    - **Impact:** Restores the whip's rated headroom; better LF/MW intermod margin. No cost.
    - **Sources:**
      - https://bonito.net/en/boni-whip-2/
      - https://bonito.net/hamradio/boni-whip-marine-aktivantenne/
      - https://www.wimo.com/en/18067
      - https://www.wimo.com/es/18067
  16.
    - **Claim in stack:** Internal bias tee for the Boni-Whip near the HF+ shield, DC up the HF coax, relay K1 to the HF+; DC-sense locks bias when the 9:1 balun (DC short) is attached (C17, 5.3).
    - **Finding:** Airspy publishes no DC tolerance for the input, so DC must be blocked toward the HF+ and the relay. For 20 kHz with ≤0.5 dB loss in 50 Ω (model), the feed choke needs ≥0.6 mH (≥1.3 mH for 9 kHz) and the DC block ≥0.7 uF. One choke cannot also stay inductive to 30 MHz, so use a series large-L + small-L stack. Bonito's supplied inserter is built for this whip's range and could be mounted inside the shield instead of a DIY tee.
    - **Verdict:** new_option
    - **Action:** Either use the Bonito inserter (internally, with its BNC output adapted to SMA) or specify the DIY tee: about 2.2 mH (≥0.15 A, low DCR) + about 10 uH series choke and a 1 uF C0G/film DC block. Measure S21 at 20 kHz-30 MHz on the LiteVNA, conducted only. Keep the DC-sense interlock.
    - **Impact:** Avoids LF loss or HF resonance in a DIY tee.
    - **Sources:**
      - https://bonito.net/en/boni-whip-2/
      - https://airspy.com/airspy-hf-discovery/
  17.
    - **Claim in stack:** Boni-Whip price and availability: WiMo EUR 159 incl. VAT ($178.73), available from 20.11.2026; Moonraker $123.95 (unverified).
    - **Finding:** WiMo SKU 18067: EUR 159.00 incl. VAT (EUR 133.61 net), 'Available from 20.11.2026' (fetched Oct 2026). Moonraker pages return 403 to my fetch. Undated search snippets show Moonraker UK £109.95 special / £119.99 regular and EU €126-138, and earlier WiMo snapshots at €135. I could not trace the STACK's $123.95.
    - **Verdict:** unverified
    - **Action:** Keep WiMo as the confirmed source with the 20.11.2026 date. Check Moonraker (UK/US store) live before ordering. The fallback is the PA0RDT-clone mini-whip (E-field, not a loop).
    - **Impact:** Price range $124-179 stands. Lead-time risk to 20.11.2026.
    - **Sources:**
      - https://www.wimo.com/en/18067
      - https://moonrakeronline.com/bonito-boni-whip-active-antenna
  18.
    - **Claim in stack:** HF wire: Nooelec Balun One Nine v2 ($26.95), identified from photos as Coilcraft WB9-1 (0.125-125 MHz, ≥25 uH); extra loss about 7/9/12/3 dB at 77.5/60/40/162 kHz; LF time signals therefore only on the active whip (#94, D16).
    - **Finding:** Nooelec: $26.95, 9:1, SMA plus terminal-block inputs, 'accurate up to 80 MHz+', max +24 dBm input, AntennaGuard varistor, aluminium case, 38x25 mm. It names no transformer part and no lower frequency limit, so the WB9-1 identification is still unverified. Coilcraft datasheet for WB9-1L/WB9-1SL: 1:9, 0.125-125 MHz 3 dB bandwidth, 0.57 dB max insertion loss, L min 25 uH primary. My shunt-L model at 25 uH in 50 Ω reproduces 12.3/9.1/7.2/2.9 dB at 40/60/77.5/162 kHz and 0.4 dB at 490/518 kHz. It uses L_min, so the real loss is probably a little lower.
    - **Verdict:** confirmed
    - **Action:** Keep the rule: LF time signals on the Boni-Whip; NAVTEX 490/518 kHz is fine on either path. Still measure the balun's DCR and S21 at 40-500 kHz, conducted.
    - **Impact:** None.
    - **Sources:**
      - https://www.nooelec.com/store/balun-one-nine-v2.html
      - https://www.coilcraft.com/pdfs/wb.pdf
  19.
    - **Claim in stack:** Tecsun AN-05 7 m wire reel about $14.50 as the HF wire option (2.5 #94).
    - **Finding:** Moonraker US lists the AN-05 7.0 m reel at $14.49 special / $17.95 regular (UK £12.95/£15.95, EU €15.41/€18.98). These come from search snippets with no date.
    - **Verdict:** confirmed
    - **Action:** Keep; check the price live when ordering.
    - **Impact:** None.
    - **Sources:**
      - https://moonrakeronline.com/us/an-05-fm-sw-reel-antenna-with-clip
  20.
    - **Claim in stack:** HF+ input switch: 2x Omron G6K-2F-RF series-parallel, ≥35 dB conducted isolation at 162-260 MHz, ≤0.3 dB loss from 10 kHz to 260 MHz (C17, 2.3).
    - **Finding:** Omron datasheet figures at 1 GHz: insertion loss 0.2 dB max; isolation 20 dB min (same polarity) and 30 dB min (different polarity); VSWR 1.2. The 162-260 MHz targets are plausible for two relays in series-parallel, but they are not published figures (model). I did not re-check the RS UK price.
    - **Verdict:** confirmed
    - **Action:** Keep. Measure conducted isolation and loss on the LiteVNA as planned (bench mode, load on the ports).
    - **Impact:** None.
    - **Sources:**
      - https://www.mouser.se/omron-g6k-2f-rf-relays
      - https://jp.farnell.com/en-JP/omron/g6k-2f-rf-dc12/relay-dpdt-30vdc-1a/dp/1448181
  21.
    - **Claim in stack:** No bias tee on the HF+; an active antenna needs an external injector.
    - **Finding:** The product page lists no bias tee. libairspyhf master nonetheless adds airspyhf_set_bias_tee / get_bias_tee_count / get_bias_tee_name with no capability check in the library. What the Discovery firmware does with these requests is not documented.
    - **Verdict:** confirmed
    - **Action:** Keep the external or internal tee. In labd/labrx, call get_bias_tee_count at open and never call set_bias_tee. Add an API-use check to CI.
    - **Impact:** Prevents an unexpected DC source on the shared HF input.
    - **Sources:**
      - https://airspy.com/airspy-hf-discovery/
      - https://raw.githubusercontent.com/airspy/airspyhf/master/libairspyhf/src/airspyhf.c
  22.
    - **Claim in stack:** Rule compliance for this subsystem: receive-only hardware, no loops, E-field whip and wire only, civil time signals, VLF 3-30 kHz masked in logging, decode-only digital modes.
    - **Finding:** The HF+ Discovery is receive-only. The antenna path is a wire + 9:1 unun and an E-field active whip (no loop or H-field part). Remaining compliance gaps found: the wsjtx package pulls libhamlib-utils (see the FT8/WSPR finding), and Radio Clock now also offers RBU (keep it out by policy). The HF+'s 0.5 kHz lower limit means the 3-30 kHz log mask in labrx is required, as STACK already states.
    - **Verdict:** confirmed
    - **Action:** Keep the masks. Apply the wsjtx and RBU actions above.
    - **Impact:** Policy only.
    - **Sources:**
      - https://airspy.com/airspy-hf-discovery/
      - https://github.com/f4exb/sdrangel/blob/master/plugins/channelrx/radioclock/readme.md
      - https://packages.ubuntu.com/noble/wsjtx
- **Current status oct 2026:** Airspy HF+ Discovery is still in production and sold. airspy.com shows no EOL notice or successor. ITEAD lists USD 169.00 with EU and US warehouses (3-6 business days); its page states no stock count and still shows firmware R2.0.0. WiMo has it in stock at EUR 232 incl. VAT. The 2026 summer sale ($135.20, 27 Jun-4 Jul) has ended. Latest stable firmware is R5.0.1 (2024-12-11); there has been no newer firmware since. The official flasher is Windows-only and its FLASH.bat relies on WMIC, which Microsoft removed from supported Windows 11 in the Aug/Sep 2026 preview updates. Host library: no upstream tag since 1.6.8 (Apr 2020). Master reports 1.8.1 (version bump Jul 2025), and the last commit is 24fe8ff (22 Jul 2026, CMake/libusb fixes). Debian stable/testing/sid and Ubuntu noble (1.6.8-4build1), 25.10 and 26.04 all still ship 1.6.8. SoapyAirspyHF 0.2.0 is packaged only in Ubuntu 26.04, not noble. SDRangel latest is v7.27.2 (19 Aug 2026) with DRM, NAVTEX, Radio Clock (now including JJY, RBU, PCSK-225) and FT8 RX plugins. SatDump master has airspyhf_sdr_support. Boni-Whip: WiMo EUR 159 incl. VAT, available from 20.11.2026. Nooelec Balun One Nine v2 $26.95, ships in 1 business day.
- **Notes:** Method: about 16 WebSearch calls plus primary WebFetch pages (airspy.com product page, changelog and purchase page; the official firmware zip, whose README.txt, FLASH.bat and changelog I read as text; GitHub source of airspyhf 1.6.8 and master, SoapyAirspyHF, SDR++, SDRangel, SatDump, AIS-catcher, welle.io; packages.ubuntu.com and tracker.debian.org; bonito.net, WiMo, Nooelec, Coilcraft datasheet; Microsoft support). Moonraker pages returned HTTP 403, so Moonraker prices come only from undated search snippets. Model calculations (Python, labelled as models): the Boni-Whip antenna-end voltage uses assumed resistances for PTC 1-4 Ω, choke 1-10 Ω and thin coax 0.35-1.0 Ω/m loop; the 9:1 shunt-L loss uses L = 25 uH (Coilcraft L_min) in 50 Ω; bias-tee component values are for ≤0.5 dB at 20 kHz; the 912 ksps alias-free width (about 784 kHz) is scaled from 660/768. Highest-impact changes for STACK: (1) DAB cannot run on the HF+ (welle.io says so explicitly; DAB needs 2.048 Msps), so move DAB to the spare V4L; (2) the noble wsjtx package hard-depends on libhamlib-utils, which breaks the no-TX-software rule, so build jt9/wsprd decode-only from source; (3) raise the Boni-Whip feed from 12.5 V to about 13.8 V, because the manufacturer minimum is 12 V at the antenna; (4) store the HF+ ppm in device flash (libairspyhf applies it automatically in every app) and drop labrx's separate correction to avoid applying it twice; (5) check firmware on arrival and require at least R4.0.5 (hub buffering), ideally R5.0.1, flashing from a Windows PC that still has WMIC; (6) Radio Clock does support JJY. HF+ current draw is still unpublished and unmeasured, so bring up with a ≥0.75 A limit. The micro-USB connector is inferred from the supplied cable, not from a stated port spec.

