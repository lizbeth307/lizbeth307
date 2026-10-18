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

## Адверсаріальна перевірка (`verify`)

_Run `wf_feb0e95a-cfc`_

- **Subsystem:** hf_receiver: Airspy HF+ Discovery (arm64 driver stack, firmware, USB/EMI/power, VHF backup role, HF/LF decoders) with HF wire + 9:1 balun and Bonito Boni-Whip (no loops). Stage 3, adversarial verification.
- **Verdict:** The subsystem holds up once the corrections below are applied. The part choice, specs, firmware history, DAB removal, the calibration behaviour in each app, the SoapyAirspyHF 0.2.1 gain fix, the decode-only WSJT-X build and the Bonito source and price all check out against primary sources and code as of 18 Oct 2026.
  
  Refuted or corrected:
  (1) Debian testing/sid and Ubuntu 25.10/26.04 do NOT ship 1.6.8 code. Their "1.6.8-5" is upstream 1.8.1 (87cf12a) under soname 1, with the exported airspyhf_flash_calibration symbol dropped and no symbols file to catch it. Only trixie and noble are true 1.6.8.
  (2) Stage 2's "labrx must call airspyhf_flash_configuration" would not compile against the default noble 1.6.8. Use the name airspyhf_flash_calibration, which works with both headers, or better, the airspyhf_calibrate tool.
  (3) The use-after-free window is e1dcc17 (Feb 2024) to 0130450 (Jul 2025), not "1.8.0 to 0130450".
  (4) Dream as packaged (luarvique 2.2-20251114 arm64) contains a DRM transmitter mode (-t/--transmitter, or launch through a symlink named 'dreamt'). An argument-filtering wrapper cannot make it RX-only, so v1 DRM needs a source-patched Dream or must wait for an SDRangel release.
  (5) Bonito rates 12-15 V at the 2.1 mm barrel of its supplied bias tee, not at the antenna. 13.8 V stays, but the acceptance gate moves to the barrel.
  
  New risks:
  - OpenWebRX+ hard-codes a 256 kS/s HF+ rate that firmware R4.0.0+ no longer offers, and SoapyAirspyHF ignores the error.
  - FLASH.bat writes -152 ppb if the saved calibration is 0.
  - The SDRangel master adds a new TX plugin (modbfm).
  - With the LF window centred at 290 kHz, the mirror of 0-40 kHz, VLF included, lands inside the alias-free band. The 3-30 kHz mask must be applied by |f|. This is a model result.
  - The Boni LDO runs in dropout below about a 14.0 V pack. This is a model result.
  
  Still unmeasured: HF+ current, shield A/B, balun LF loss, Boni current and whip length, and USB stability on the Q6A.
  
  Limits: the shared WebSearch budget was already used up when this stage started (0 searches done). All checks used WebFetch on primary pages, git clones of airspyhf, SoapyAirspyHF, SDRangel and Dream, the Debian/Launchpad APIs, the ITEAD store API, and reading the firmware zip and Dream .deb as text (nothing was executed). The Omron G6K, Moonraker/AN-05 and xHCI-era SDRangel issues were not re-fetched (403/503 or out of reach).
- **Confirmed:**
  - Airspy HF+ Discovery is current: airspy.com lists it (with HF+ Dual Port, R2, Mini, SpyVerter R2, YouLoop) with no EOL or successor notice. libairspyhf master knows an unannounced board ID AIRSPYHF_BOARD_ID_AIRSPYHF_RANGER_REV_A (since e1dcc17, Feb 2024), but airspy.com shows no such product.
  - Specs verbatim on airspy.com (fetched 18 Oct 2026): HF 0.5 kHz-31 MHz; VHF 64-260 MHz ('second Band-III tuner up to 260 MHz, but with reduced performance'); IIP3 +15 dBm HF / +13 dBm VHF at max gain; BDR 110/95 dB; MDS -140.0 dBm at 15 MHz in 500 Hz, -141.5 dBm (64-118 MHz), -141.0 dBm (118-260 MHz); +10 dBm max RF input; 660 kHz alias/image-free at 768 ksps; 2x sigma-delta ADC up to 36 MSPS, 18-bit DDC; 0.5 ppm clock, 1 ppb adjust; -45 to +85 C; 45x60x10 mm. No current, connector or DC-input rating published.
  - ITEAD USD 169.00 (WooCommerce store API, 18 Oct 2026): generic SKU IM190522001 in stock; EU-warehouse variant '310 in stock'; US variant '96 in stock'. The product text still says 'Firmware Updates R2.0.0 2019-05-02'. VAT/duty treatment is not shown.
  - WiMo HF+ Discovery: EUR 232.00 incl. VAT, in stock, ships in 1-2 days, 32 g, box contains 'USB cable (USB-A to USB Micro-B)'. The device port is micro-USB B, inferred from the cable.
  - Firmware changelog (airspy.com): latest R5.0.1 (2024-12-11). R2.2.0 'Better underrun/overrun handling'; R2.9.0 fixed calibration save/restore; R2.9.6 fragmented streaming (hubs); R2.8.0 and R3.0.7 added 912 (and 456) ksps; R4.0.0 replaced 256k with 228k; R4.0.4 added 650 ksps Low-IF; R4.0.5 buffering for slow controllers/hubs; R4.0.7 fixed 384k/192k init; R5.0.0 new gain distribution and AGC/ATT/Preamp; R1.6.1 low-current standby when not streaming.
  - Firmware zip contents: FLASH.bat finds the SAM-BA port with 'wmic path Win32_SerialPort' (VID_03EB&PID_6124). It picks hfplus-firmware-bb.bin or -cd.bin from hfplus_fw.exe output, saves the ppb with hfplus_ppb.exe, reboots with hfplus_reboot.exe, then runs bossac -u, bossac -e -b -v -w and bossac --reset, and restores the ppb. README prerequisite: 'Windows 10 or Windows 7'.
  - Microsoft: WMIC was removed from supported Windows 11 in the August 2026 preview update (24H2/25H2) and the September 2026 preview update (26H1). It is no longer a Feature on Demand. wmic_dlc.zip is a 'temporary mitigation', 'not a secure, long-term solution'. No removal is listed for Windows 10 or Server.
  - SoapyAirspyHF #8: firmware R2.0.0 gave 'readStream failed: TIMEOUT, disabling' after about 1.5 h on a Raspberry Pi. R2.2.0 fixed it (reporter, 8 Jun 2019).
  - libairspyhf master head 24fe8ff (2026-07-22). AIRSPYHF_VERSION 1.8.1 (c0bb66d, 2025-07-12); upstream SOVERSION 0. SAMPLES_TO_TRANSFER 4096 (was 2048 in 1.6.8); RAW_BUFFER_COUNT 8. Adds set_att/get_att_steps, frontend options, set/get bias-tee calls with no capability check; airspyhf_flash_calibration is now only '#define ... airspyhf_flash_configuration'. Only tags: 1.0, 1.1.2, 1.1.3, 1.1.5, 1.6.8 (2020-04-09). Upstream refused to tag ('No.', touil, #62, 7 Jan 2026).
  - 1.6.8 does not have the use-after-free: it frees transfer->buffer before libusb_free_transfer. The bad order came in with e1dcc17 and was fixed in 0130450.
  - Ubuntu noble: airspyhf 1.6.8-4build1 (universe). Debian 1.6.8-4 carries only the bump-soversion (SOVERSION 0 to 1) and libusb-freebsd patches, so it is true 1.6.8 with soname 1. The udev rule is SUBSYSTEM=usb 03eb:800c GROUP=plugdev TAG+=uaccess ('use group plugdev along with uaccess to allow for systemd services').
  - SoapyAirspyHF: tag soapy-airspyhf-0.2.1 = 0b3daf0, 2026-10-10. CMake uses check_function_exists(airspyhf_set_hf_att). 0.2.0 Settings.cpp uses '#if MAJOR>=1 / MINOR>=1 / REVISION>=2', which fails for 1.8.1 (revision 1). airspyhf_set_hf_att is still exported in 1.8.1. Packaged only in Ubuntu 26.04+ (0.2.0-1, 0.2.0-1.1), not in noble. It makes no calibration call.
  - libairspyhf (1.6.8 and master) reads calibration_ppb from flash at open (CALIBRATION_MAGIC 0xA5CA71B0) and applies it in set_freq. SDR++, SatDump, AIS-catcher and SoapyAirspyHF never call set_calibration. OpenWebRX+ AirspyhfDeviceDescription.supportsPpm() returns False ('not currently supported by the SoapySDR module').
  - SDRangel v7.27.2 (tag 2026-08-19) airspyhfinput.cpp calls airspyhf_set_calibration(m_dev, m_LOppmTenths*100) in applySettings with force=true from both init() and startInput(); the default LOppmTenths is 0. This overwrites the flash value in that session.
  - SDRangel v7.27.2 has demodnavtex, demodrtty, demodft8, demoddsc, demoddab, demodbfm, demodvor and radioclock. demoddrm (first commit 2d7bef00d, 2026-10-14) and demodwefax (606ab8f98, 2026-10-01) exist only on master.
  - Radio Clock readme at v7.27.2 lists MSF 60, DCF77 77.5, TDF 162, WWVB 60 and JJY 40 kHz. RBU and PCSK-225 arrived in 9cc4a5440 (2026-09-29), master only.
  - DAB cannot run on the HF+. welle.io README: 'Airspy HF+ is not supported due to limited bandwidth'. OpenWebRX+ defines DAB with ifRate=2048000. The HF+ maximum is 912 ksps.
  - AIS-catcher README lists AirSpy HF+. Its driver enumerates rates and sets HF AGC.
  - noble wsjtx 2.7.0~rc3+repack-1build2 hard-depends on libhamlib-utils (also libhamlib4t64, Qt5 GUI, qcustomplot). WSJT-X CMake: wsprd links FFTW3 and libm; jt9 links wsjt_fort(_omp), wsjt_cxx and fort_qt (Qt5::Core); Hamlib is linked only into wsjt_qt (and wsjtx_app_version); find_package(Hamlib REQUIRED) is a build-host dependency only. OpenWebRX+ has_wsjtx() needs only jt9 and wsprd runnable; FST4/Q65 parse 'WSJT-X x.y' from wsjtx_app_version --version.
  - OpenWebRX+ debian/control Recommends wsjtx, js8call, direwolf, dumphfdl, dumpvdl2, acarsdec, rtl-433 and more, so --no-install-recommends is mandatory. The noble PPA's latest openwebrx is 1.2.126; 1.2.127 exists only in the master changelog, dated 19 Oct 2026. The PPA has no SoapyAirspyHF module. The 'fax' mode needs no external binary.
  - HF+ streaming uses libusb bulk transfers (libusb_fill_bulk_transfer) and calls libusb_clear_halt at start/stop. A periodic-bandwidth limit does not apply. The 1.6.8 ring is 8x2048 samples, 21.3 ms at 768 ksps (model).
  - Sample format: the library converts int16 to cf32 with scale 1/32768 x filter_gain (10^(-gain/20)). With DSP on it applies the IQ balancer (Zero-IF) and an NCO freq_shift. ci16 written from cf32 is post-DSP.
  - EMI: Airspy's author (tweet 26 Feb 2022, quoted by rtl-sdr.com) says shielding is 'a small anechoic chamber made from the PCB itself', 'the metal can, and some EMI absorbing material'; an alu case 'can help with the heat dissipation in systems running 24/7/365'.
  - HF+ current is still unpublished. The rtl-sdr.com USB-power article gives no numbers in text. AB9IL gives 'about 170 mA at 5V (≈0.85W)' for an unnamed 'Airspy HF+' with no method.
  - Boni-Whip, manufacturer shop hamradioshop.net (18 Oct 2026): EUR 149.00 incl. VAT, 'Sofort verfügbar, Lieferzeit: 1-5 Tage'; 20 kHz-300 MHz; 'Spannungsversorgung: 12V -15V (2,1mm Hohlstecker)'; 'Typ: 65mAh' (read as 65 mA); +3 dB; IP3 >+30 dBm, IP2 >+50 dBm; about 17 cm; BNC; includes antenna, Strahler (whip), Einspeiseweiche and manual; no coax; PSU optional. bonito.net: 20 kHz-300 MHz, 12-15 V, IP3 +32.5 dBm, IP2 +55 dBm, interchangeable whips; whip length not stated.
  - WiMo Boni-Whip (SKU 18067): EUR 159.00 incl. VAT, 'Available from 20.11.2026'; title 10 kHz-300 MHz, tech data 9 kHz-300 MHz; 'about 14 cm'; 189 g; bias tee included.
  - Nooelec Balun One Nine v2: US$26.95, 'usually shipped in 1 business day', 9:1, 'accurate to frequencies up to 80MHz+', no lower limit stated, max +24 dBm, AntennaGuard varistor, SMA plus 3 terminal-block inputs, 38x25 mm, no part number, DC continuity not stated, 0 reviews.
  - Coilcraft WB9-1L/WB9-1SL: 1:9, 0.125-125 MHz 3 dB bandwidth, 0.57 dB max insertion loss, primary L min 25 uH, secondary L min 225 uH. Shunt-L model reproduced: 12.26/9.05/7.17/2.93/0.44/0.39 dB at 40/60/77.5/162/490/518 kHz (model).
  - TI TPS7A47: Vin 3-36 V; ANY-OUT 1.4-20.5 V; adjustable TPS7A4701 1.4-34 V; dropout 307 mV at 1 A; PSRR ≥55 dB from 10 Hz to 10 MHz (60 dB at 100 kHz); 4 uVrms noise; ACTIVE. Both 12.5 V and 13.8 V are settable.
  - The HF+ is receive-only; the antenna path is an E-field whip plus wire/unun, with no loop or H-field part.
- **Corrections:**
  1.
    - **Claim in stack:** #31 / labrx row: 'HF+ ppm correction in labrx or libairspyhf (SoapyAirspyHF does not call airspyhf_set_calibration)'. Stage 2: labrx must call airspyhf_flash_configuration.
    - **Finding:** The flash-stored ppb is applied automatically by libairspyhf in SDR++, SatDump, AIS-catcher, SoapyAirspyHF and OpenWebRX+ (supportsPpm False). SDRangel 7.27.2 overwrites it with LOppmTenths x 100 on init and start (default 0). airspyhf_flash_configuration does not exist in noble's 1.6.8 header or library. airspyhf_flash_calibration is a real function in 1.6.8 and a macro to flash_configuration in 1.8.1, so only that name compiles against both. The noble 'airspyhf' package ships airspyhf_calibrate (-s serial, -c ppb), which writes flash.
    - **Verdict:** corrected
    - **Action:** Remove labrx's own ppm correction. Calibrate once at bench with 'airspyhf_calibrate -s <SN> -c <ppb>' (streaming stopped), after any firmware flash. labd writes LOppmTenths = round(ppb/100) into every SDRangel AirspyHF preset over REST and checks it after each preset load. If labrx ever writes flash itself, the source uses the name airspyhf_flash_calibration and is rebuilt with the library.
    - **Impact:** Every engine sees the same frequency correction; no double correction; labrx builds against noble 1.6.8.
    - **Sources:**
      - https://github.com/airspy/airspyhf
      - https://raw.githubusercontent.com/f4exb/sdrangel/v7.27.2/plugins/samplesource/airspyhf/airspyhfinput.cpp
      - https://raw.githubusercontent.com/luarvique/openwebrx/master/owrx/source/airspyhf.py
      - https://raw.githubusercontent.com/AlexandreRouma/SDRPlusPlus/master/source_modules/airspyhf_source/src/main.cpp
      - https://raw.githubusercontent.com/SatDump/SatDump/master/plugins/sdr_sources/airspyhf_sdr_support/airspyhf_sdr.cpp
      - https://raw.githubusercontent.com/jvde-github/AIS-catcher/main/Source/Device/AIRSPYHF.cpp
  2.
    - **Claim in stack:** lab_ui_hf / #31: noble libairspyhf 1.6.8-4build1. Stage 1: 'Debian stable/testing/sid and Ubuntu 26.04 still ship 1.6.8'; if 1.8.1 is needed, build upstream pinned at 24fe8ff.
    - **Finding:** Partly refuted. trixie 1.6.8-4 and noble 1.6.8-4build1 are true 1.6.8 with soname 1. Debian 1.6.8-5 (sid/forky; Ubuntu 25.10 1.6.8-5; 26.04/stonking/tenacious 1.6.8-5build1) is 'update to 1.6.8-59-g87cf12a ... (would be 1.8.1 if upstream released)': 46 cherry-picked patches including the UAF fix (0044) and 4k buffers (0045), still soname 1. It drops the exported airspyhf_flash_calibration symbol inside the same soname, and the package has no symbols file to catch that.
    - **Verdict:** corrected
    - **Action:** Default: noble 1.6.8-4build1. If 1.8.1 features are needed, backport the Debian 1.6.8-5 source package to noble as +lab (not an upstream 'make install'). Rebuild airspyhf tools, SoapyAirspyHF 0.2.1, SDR++, SDRangel, SatDump, AIS-catcher and labrx against it in the same repo snapshot. Never mix it with binaries built against 1.6.8-4.
    - **Impact:** A tested 1.8.1 path; no runtime symbol breaks.
    - **Sources:**
      - https://sources.debian.org/src/airspyhf/1.6.8-5/debian/changelog
      - https://sources.debian.org/src/airspyhf/1.6.8-5/debian/patches/series
      - https://sources.debian.org/src/airspyhf/1.6.8-4/debian/patches/
      - https://api.launchpad.net/1.0/ubuntu/+archive/primary?ws.op=getPublishedSources&source_name=airspyhf&exact_match=true&status=Published
      - https://github.com/AlexandreRouma/SDRPlusPlus/issues/1805
  3.
    - **Claim in stack:** Stage 1: never build a commit 'between 1.8.0 and 0130450' (use-after-free).
    - **Finding:** There is no 1.8.0 tag. The bad free order arrived in e1dcc17 (2024-02-12, 'Improved the threading code') and was fixed in 0130450 (2025-07-11).
    - **Verdict:** corrected
    - **Action:** If upstream is ever built, never use a commit in e1dcc17..0130450^. Preferred: Debian 87cf12a, or head 24fe8ff.
    - **Impact:** Precise pin rule.
    - **Sources:**
      - https://github.com/airspy/airspyhf
  4.
    - **Claim in stack:** STACK names no firmware. Stage 1/2: minimum R4.0.5, then R4.0.7; flash on Windows with WMIC.
    - **Finding:** Confirmed. FLASH.bat also runs 'bossac -u' before erase/write, and it substitutes '-152' when the saved calibration is 0 ('if !Calibration!==0 set Calibration=-152'). WMI itself is not removed, only wmic.exe, so the COM-port lookup can be done in Device Manager or PowerShell CIM (my suggestion, untested).
    - **Verdict:** corrected
    - **Action:** On arrival, run airspyhf_info and record S/N, firmware and rate list. Minimum R4.0.7, target R5.0.1. Flash on Windows 10 (README prerequisite), on Windows 11 with wmic_dlc, or by hand: hfplus_fw.exe (BB/CD), hfplus_ppb.exe > Calib, hfplus_reboot.exe, find the COM port of VID_03EB&PID_6124, then 'bossac -u -pCOMx', 'bossac -e -b -v -w -pCOMx hfplus-firmware-<bb|cd>.bin', 'bossac --reset -pCOMx'. Then recalibrate on the bench (do not trust the restored value) and store it with airspyhf_calibrate.
    - **Impact:** Avoids the R2.0.0 1.5 h TIMEOUT stall, broken Low-IF rates and a silent -152 ppb offset.
    - **Sources:**
      - https://airspy.com/downloads/airspy-hf-flash-2024-12-11_5.0.1.zip
      - https://airspy.com/downloads/hfplus_changelog.txt
      - https://support.microsoft.com/en-us/topic/windows-management-instrumentation-command-line-wmic-removal-from-windows-e9e83c7f-4992-477f-ba1d-96f694b8665d
      - https://github.com/pothosware/SoapyAirspyHF/issues/8
  5.
    - **Claim in stack:** #31: SoapyAirspyHF from source; OpenWebRX+ reaches the HF+ through it.
    - **Finding:** Confirmed; use tag 0.2.1 (0b3daf0). New: OpenWebRX+ hard-codes HF+ rates [192000, 256000, 384000, 456000, 768000, 912000]. Firmware ≥R4.0.0 offers 228k instead of 256k. libairspyhf_set_samplerate returns AIRSPYHF_ERROR for an unlisted exact rate, and SoapyAirspyHF ignores that return in activateStream. The device then streams at a different rate than OpenWebRX+ assumes (inferred from code, not observed).
    - **Verdict:** new_risk
    - **Action:** Build soapy-airspyhf-0.2.1 as +lab. OpenWebRX+ HF+ profiles may use only 768000 (default), 912000, 456000, 384000 or 192000, each checked against the airspyhf_info rate list. CI rejects 256000 for airspyhf. Fix gain and AGC per profile.
    - **Impact:** Prevents a silent wrong-sample-rate profile (wrong frequency axis and demodulation).
    - **Sources:**
      - https://raw.githubusercontent.com/luarvique/openwebrx/master/owrx/source/airspyhf.py
      - https://github.com/pothosware/SoapyAirspyHF
      - https://github.com/airspy/airspyhf
      - https://airspy.com/downloads/hfplus_changelog.txt
  6.
    - **Claim in stack:** 4.2 rows 509/510, #3, P20: HF WEFAX via 'sdrangelsrv WEFAX'; DRM via SDRangel / OpenWebRX+.
    - **Finding:** DRM and WEFAX are master-only in SDRangel (DRM first commit 14 Oct 2026, WEFAX 1 Oct 2026). Master is 713 commits past v7.27.2 and adds a new TX plugin, channeltx/modbfm. The OpenWebRX+ DRM path needs 'dream' (feature 'drm' = ['dream']). The luarvique arm64 binary dream 2.2-20251114 contains '-t, --transmitter DRM transmitter mode' and CDRMTransmitter (strings only, not executed). The wwek/dream source (fddf0cc) also enters transmitter mode when invoked as 'dreamt' (IsReceiver(argv0)), so a wrapper cannot make it RX-only. The OpenWebRX+ 'fax' mode is built in.
    - **Verdict:** corrected
    - **Action:** v1: WEFAX = OpenWebRX+ 'fax' behind the civil-only allow-list (Northwood excluded). DRM = none in v1, unless Dream is rebuilt from source with the transmitter removed (reject -t/--transmitter, IsReceiver always true, delete the 'transmit' branch in main.cpp). The CI check fails on the strings '--transmitter' or 'CDRMTransmitter'. Otherwise DRM waits for the first SDRangel release with demoddrm. Any SDRangel master build adds modbfm to the TX-plugin removal list. Update rows 509, 510 and P20.
    - **Impact:** Keeps P2 (no TX-capable software). DRM may slip past v1.
    - **Sources:**
      - https://github.com/f4exb/sdrangel
      - https://luarvique.github.io/ppa/noble/Packages
      - https://luarvique.github.io/ppa/noble/arm64/dream_2.2-20251114_arm64.deb
      - https://github.com/wwek/dream
      - https://raw.githubusercontent.com/luarvique/openwebrx/master/owrx/feature.py
      - https://raw.githubusercontent.com/luarvique/openwebrx/master/owrx/modes.py
  7.
    - **Claim in stack:** Summary line 3, rows 505/685/710: HF+ covers AIS, FM-RDS and DAB.
    - **Finding:** DAB is impossible on the HF+ (912 ksps max; DAB needs 2.048 Msps). Confirmed by welle.io and the OpenWebRX+ DAB ifRate. AIS and FM-RDS hold.
    - **Verdict:** corrected
    - **Action:** Remove DAB from every HF+ row. DAB+ (user: on) runs on the spare V4L or the Lime. The HF+ VHF role is AIS (default), FM-RDS, NFM, airband and VOR.
    - **Impact:** Removes a capability that could not work.
    - **Sources:**
      - https://raw.githubusercontent.com/AlbrechtL/welle.io/master/README.md
      - https://raw.githubusercontent.com/luarvique/openwebrx/master/owrx/modes.py
  8.
    - **Claim in stack:** #3 and 4.2 row 513: time signals DCF77/MSF/WWVB/JJY 40/60/TDF; 'JJY 60 amplitude only'.
    - **Finding:** 7.27.2 lists JJY 40 kHz decoding; JJY 60 is not listed. RBU and PCSK-225 are master-only. For a European user JJY and WWVB are rarely receivable on a handheld (my assessment, not measured). TDF has weekly maintenance on Tuesdays 08:00-12:00 (Wikipedia, secondary source).
    - **Verdict:** corrected
    - **Action:** Decode allow-list on 7.27.2: DCF77, MSF, TDF (priority), WWVB and JJY 40. JJY 60 stays amplitude-only until tested on a recording. RBU (66.666 kHz) stays blocked in labd. SID logs flag TDF Tuesday-morning gaps.
    - **Impact:** No cost.
    - **Sources:**
      - https://github.com/f4exb/sdrangel
      - https://en.wikipedia.org/wiki/TDF_time_signal
  9.
    - **Claim in stack:** #10 / 6.1: install wsjtx and dpkg-divert /usr/bin/wsjtx; use only jt9/wsprd.
    - **Finding:** apt install wsjtx pulls libhamlib-utils (rigctl/rigctld), a hard dependency. A decode-only build is practical from WSJT-X CMake targets.
    - **Verdict:** corrected
    - **Action:** Build 'wsjtx-decoders+lab': make jt9 wsprd. Runtime deps: libgfortran5, libfftw3-single3, libgomp1, Boost.Log, libqt5core5t64. Add a one-line wsjtx_app_version stub printing 'WSJT-X 2.7.0' for FST4/Q65. CI checks that wsjtx, libhamlib-utils, js8call and direwolf are not installed and that rigctl/rigctld are absent. SDRangel demodft8 is the alternative for FT8/FT4.
    - **Impact:** Keeps P2; build effort only.
    - **Sources:**
      - https://packages.ubuntu.com/noble/wsjtx
      - https://sourceforge.net/p/wsjt/wsjtx/ci/master/tree/CMakeLists.txt
      - https://raw.githubusercontent.com/luarvique/openwebrx/master/owrx/feature.py
  10.
    - **Claim in stack:** C17 / BONI12V5 / BOM row 220: Boni-Whip 9 kHz-300 MHz, supply 9-15 V, about 14 cm, 189 g; fed 12.5 V ±0.25 V; '12.5 V fits both published ranges'; current 0.05-0.1 A not published. Stage 1/2: 13.8 V, accept if antenna end ≥12.3 V.
    - **Finding:** Manufacturer: 20 kHz-300 MHz, 12-15 V, typ 65 mA, about 17 cm, BNC; bias tee (Einspeiseweiche) included, fed by a 5.5/2.1 mm barrel. The voltage is specified with the barrel connector, so Bonito's rating point is the bias-tee input, not the antenna. Model at 65 mA with PTC 1-4 Ω before the barrel: 13.8±0.2 V gives 13.34-13.54 V at the barrel, and 12.0-13.4 V at the antenna over the stage-1 resistance range; 12.5±0.25 V gives 11.99-12.19 V at the barrel. Model: the TPS7A4701 drops out once the pack is below about 13.9-14.0 V, about the Economy threshold, and still gives about 13.1 V at the 13.2 V shutdown.
    - **Verdict:** corrected
    - **Action:** Rename the rail BONI13V8: TPS7A4701 at 13.8 V ±0.2 V, PTC hold 0.15-0.2 A ahead of the barrel. Gate: ≥12.0 V at the Einspeiseweiche barrel with the pack at 13.2 V; record the antenna-end voltage, target ≥12.0 V. Correct the specs to 20 kHz-300 MHz (vendor), 12-15 V at the barrel, 65 mA typ (vendor), about 17 cm (Bonito) / about 14 cm (WiMo), 189 g (WiMo). Energy model: about 0.90 W.
    - **Impact:** Meets the vendor rating with margin; slightly lower energy budget than 12.5 V x 0.1 A.
    - **Sources:**
      - https://hamradioshop.net/Boni-Whip-Aktivantenne/0125.2
      - https://bonito.net/en/boni-whip-2/
      - https://www.wimo.com/en/18067
      - https://www.ti.com/product/TPS7A47
  11.
    - **Claim in stack:** BOM row 220 / 9.1 step 9: Boni-Whip $123.95 Moonraker (unverified) / $178.73 WiMo from 20.11.2026.
    - **Finding:** Bonito's own shop has it in stock at EUR 149.00 incl. VAT (about $167.49 at 1.1241), delivery 1-5 days. WiMo is EUR 159.00 ($178.73), available from 20.11.2026. The Moonraker $123.95 is not traceable.
    - **Verdict:** new_option
    - **Action:** Buy from hamradioshop.net (Bonito) now; WiMo is the second source; drop Moonraker $123.95. Add a BNC-SMA lead and a 5.5/2.1 mm barrel plug to the BOM.
    - **Impact:** Removes the 20.11.2026 lead-time risk; BOM $167.49 plus adapters.
    - **Sources:**
      - https://hamradioshop.net/Boni-Whip-Aktivantenne/0125.2
      - https://www.wimo.com/en/18067
  12.
    - **Claim in stack:** C17 / 5.3: DC-sense locks bias when the 9:1 balun (DC short) is attached.
    - **Finding:** Nooelec does not state DC continuity and has an input varistor. The WB9-1 primary DCR is ≤100 (mΩ class) if the part ID is right. DC-sense alone cannot tell an open port or a DC-blocked accessory from a valid Boni-Whip.
    - **Verdict:** new_risk
    - **Action:** Measure the balun DCR. Keep the DC-sense short lock (<10 Ω at about 1 mA sense current; set it from the measurement). After enable, add a current-window check: 30-150 mA within 2 s, set from the measured Boni current, else disable and log. Bias only in the explicit Boni profile.
    - **Impact:** No DC into a short or an unexpected accessory.
    - **Sources:**
      - https://www.nooelec.com/store/balun-one-nine-v2.html
      - https://www.coilcraft.com/pdfs/wb.pdf
  13.
    - **Claim in stack:** Stage 1 bias tee: about 2.2 mH + about 10 uH series choke, 1 uF C0G/film DC block; L ≥0.6 mH and C ≥0.7 uF for ≤0.5 dB at 20 kHz.
    - **Finding:** Model: for 0.5 dB each alone at 20 kHz, L ≥0.57 mH and C ≥0.23 uF; with a 0.25 dB split, ≥0.82 mH and ≥0.33 uF; at 9 kHz, 1.27-1.82 mH and 0.51-0.73 uF. Stage 1's values hold with margin. X7R is a poor choice for a DC block carrying 13.8 V bias in the signal path (voltage coefficient, piezo).
    - **Verdict:** confirmed
    - **Action:** Keep 2.2 mH (≥0.15 A, low DCR) + about 10 uH, and use a 1 uF PPS/PEN film or C0G DC block, not X7R. Or use Bonito's Einspeiseweiche if it fits inside the shield (size unpublished). Measure S21 at 20 kHz-30 MHz conducted on the LiteVNA, and DC leakage at the HF+ SMA.
    - **Impact:** None.
    - **Sources:**
      - https://bonito.net/en/boni-whip-2/
      - https://airspy.com/airspy-hf-discovery/
  14.
    - **Claim in stack:** #88 / 4.2 row 513: one HF+ window centred about 290 kHz covers 60/77.5/490/518 kHz; 3-30 kHz masked in logging.
    - **Finding:** With 768 ksps (±330 kHz alias-free), 290 kHz covers -40..620 kHz absolute; all targets fit (JJY 40 at -250, NAVTEX 518 at +228). libairspyhf keeps the hardware LO ≥180 kHz (Zero-IF) and adds a +5 kHz IF shift with DSP on, so the LO is at 295 kHz. Model: with a complex baseband, the negative-frequency image of real 0-40 kHz signals (VLF 3-30 kHz included) appears at -40..0 kHz absolute, inside the alias-free band, where a positive-only 3-30 kHz mask does not reach. A 330 kHz centre (0..660 kHz) puts those images into the DDC transition band.
    - **Verdict:** new_risk
    - **Action:** labrx masks every bin with |f_abs| < 30 kHz, including negative absolute frequencies, before storage. Prefer centre 330 kHz at 768 ksps for the LF window (targets at -290..+188 kHz offset). Verify with a conducted 35 kHz tone.
    - **Impact:** Closes a VLF logging leak (policy, P2 survey mask).
    - **Sources:**
      - https://github.com/airspy/airspyhf
      - https://airspy.com/airspy-hf-discovery/
  15.
    - **Claim in stack:** 2.3 / 5.7.6: HF+ VBUS LC + Mix-31; stage 1 suggests about 100 uH / 100 uF ≈ 1.6 kHz.
    - **Finding:** Corner 1.59 kHz confirmed (model). An undamped LC peaks at resonance and rings on load-switch turn-on. 100 uF behind a USB port exceeds the 10 uF device inrush norm unless the upstream switch limits current or soft-starts.
    - **Verdict:** corrected
    - **Action:** Add damping (series R-C across the 100 uF, or a lossy electrolytic). Rely on the TPS2553/load-switch current limit for inrush. Rate the inductor for ≥1.5x the measured streaming current. The Mix-31 bead covers HF only; LF filtering comes from the LC.
    - **Impact:** Clean VBUS without ringing; parts about $2.
    - **Sources:**
      - https://www.rtl-sdr.com/a-new-aftermarket-airspy-hf-discovery-aluminum-enclosure-for-sale/
  16.
    - **Claim in stack:** Section 8: HF+ current not published; budget 0.3 A; TPS2553 at 1.5-2x measured. Stage 2: AB9IL 170 mA is the original HF+.
    - **Finding:** Still unpublished. The AB9IL figure names no model and gives no method. Firmware R1.6.1 standby means idle and streaming currents differ.
    - **Verdict:** unverified
    - **Action:** Bring up at ≥0.75 A. Measure idle (open, not streaming) and streaming at 768 and 912 ksps, cold and after 60 min sealed. Then set the limit to 1.5-2x streaming. Keep 0.3 A as the placeholder.
    - **Impact:** Mode E runtime (7.1 h / 6.1 h) stays provisional.
    - **Sources:**
      - https://www.ab9il.net/software-defined-radio/2025-06-22_12-15-50.html
      - https://www.rtl-sdr.com/measuring-the-usb-power-consumption-of-various-software-defined-radios/
      - https://airspy.com/downloads/hfplus_changelog.txt
  17.
    - **Claim in stack:** Section 8 open item 'HF+ USB connector type'; stage 1: CH334 MTT makes the stream fit.
    - **Finding:** Micro-USB B, inferred from WiMo's 'USB-A to USB Micro-B' cable. MTT is irrelevant: the HF+ is a high-speed device and transaction translators only serve FS/LS devices. Bulk at 3.07-3.65 MB/s fits easily. The noble udev rule needs plugdev for headless services.
    - **Verdict:** corrected
    - **Action:** Close the item: micro-USB B, short shielded lead, strain relief, shell bonded to the mid plate, ferrite. Put the labrx and sdrangel users in plugdev. Run the soak test (below).
    - **Impact:** About $3-5.
    - **Sources:**
      - https://www.wimo.com/en/airspy-discovery
      - https://sources.debian.org/src/airspyhf/1.6.8-4/debian/libairspyhf1.udev
      - https://github.com/airspy/airspyhf
  18.
    - **Claim in stack:** #94: Balun One Nine v2 ($26.95, WB9-1 by photo); extra loss about 7/9/12/3 dB at 77.5/60/40/162 kHz; LF time only on the whip.
    - **Finding:** Price and specs confirmed; part ID unverified (no part number on the page, 0 reviews). The 25 uH shunt-L numbers are a matched-50 Ω lower bound. A 7-15 m wire is mostly capacitive at LF, so the real LF loss is larger (qualitative model).
    - **Verdict:** confirmed
    - **Action:** Keep the rule (LF time signals on the Boni-Whip; NAVTEX on either path). Measure DCR and S21 at 40-500 kHz conducted, including with a series 50-150 pF wire-simulator capacitor.
    - **Impact:** None.
    - **Sources:**
      - https://www.nooelec.com/store/balun-one-nine-v2.html
      - https://www.coilcraft.com/pdfs/wb.pdf
  19.
    - **Claim in stack:** BOM row 184: HF+ $169 at ITEAD, EU/US/CN warehouses.
    - **Finding:** USD 169.00; EU warehouse 310 in stock, US 96 in stock (store API, 18 Oct 2026). $169 ≈ EUR 150.34 at STACK's rate. Whether the EU-warehouse price includes VAT is not shown. Model landed price at 19-25% VAT: $201-211.
    - **Verdict:** confirmed
    - **Action:** Keep ITEAD (EU warehouse); check VAT at checkout; WiMo EUR 232 ($260.79) is the fallback.
    - **Impact:** BOM $169 (+VAT if not included).
    - **Sources:**
      - https://itead.cc/wp-json/wc/store/v1/products?slug=airspy-hf-discovery-eu
      - https://itead.cc/wp-json/wc/store/v1/products?slug=airspy-hf-discovery-us
      - https://www.wimo.com/en/airspy-discovery
  20.
    - **Claim in stack:** C17 / 2.3: 2x Omron G6K-2F-RF series-shunt, ≥35 dB isolation at 162-260 MHz, ≤0.3 dB from 10 kHz to 260 MHz; RS UK GBP 43-52.
    - **Finding:** Not re-verified in stage 3 (Omron 403, Mouser and Farnell 503). Stage 1's datasheet figures (1 GHz: 0.2 dB IL max, isolation 20/30 dB min) and the 35 dB target (model) are unchanged.
    - **Verdict:** unverified
    - **Action:** Keep. Accept only on the conducted LiteVNA measurement.
    - **Impact:** None.
    - **Sources:**
      - https://www.mouser.se/omron-g6k-2f-rf-relays
  21.
    - **Claim in stack:** Stage 1: libairspyhf master bias-tee API; labd never calls set_bias_tee.
    - **Finding:** Confirmed in code (vendor request with no capability check; 247bed4 'Fixed the bias-tee control call'). Noble 1.6.8 has none of these symbols, so the rule holds automatically there.
    - **Verdict:** confirmed
    - **Action:** Only for a 1.8.1 build: CI grep that forbids airspyhf_set_bias_tee outside a test, and a bench check that get_bias_tee_count returns 0.
    - **Impact:** None.
    - **Sources:**
      - https://github.com/airspy/airspyhf
- **New risks:**
  - OpenWebRX+ offers a hard-coded 256 kS/s HF+ rate that firmware ≥R4.0.0 replaced with 228k. airspyhf_set_samplerate fails and SoapyAirspyHF ignores the error, so the stream runs at a rate other than the one assumed (inferred from code). Allow only rates from airspyhf_info.
  - Packaged Dream 2.2-20251114 (arm64, luarvique PPA) has a DRM transmitter mode (-t/--transmitter, or launch through a symlink named 'dreamt'). Unpatched it breaks P2 the same way fldigi or QSSTV would, and a wrapper is not enough.
  - SDRangel master (713 commits past v7.27.2) adds the TX plugin channeltx/modbfm. Building master for DRM/WEFAX widens the TX-plugin audit list.
  - Debian/Ubuntu 1.6.8-5 is the 1.8.1 code under soname 1 with the exported airspyhf_flash_calibration removed and no symbols file. Mixing a backport with noble-built binaries can fail at load time.
  - FLASH.bat writes -152 ppb when the saved calibration is 0. Always recalibrate after a firmware flash.
  - Model: with the LF window centred at 290 kHz (768 ksps), the negative-frequency image of real 0-40 kHz signals, VLF 3-30 kHz included, falls at -40..0 kHz absolute inside the alias-free band. A 3-30 kHz mask on positive frequencies only would let VLF energy into stored data. Mask by |f| or centre at 330 kHz.
  - Model: the BONI LDO at 13.8 V enters dropout below a pack of about 13.9-14.0 V, about the Economy threshold, and loses PSRR. Buck ripple near 500 kHz (D36V50F12) could reach the antenna feed next to NAVTEX 490/518 kHz. Needs a ripple test in dropout.
  - DC-sense cannot tell an open port or a DC-blocked accessory from a valid Boni-Whip (Nooelec does not state DC continuity). Add a post-enable current-window check.
  - Boni-Whip whip (Strahler) length is unpublished (Bonito: interchangeable whips; body about 17 cm). Measure it against the 20-23 cm / 35 cm piece rule; a shorter whip lowers LF output.
  - The VBUS LC (100 uH / 100 uF, 1.6 kHz) can ring and draws inrush above the USB 10 uF norm unless damped and current-limited upstream.
  - The flashing host is a Windows dependency. Windows 11 has no WMIC after the Aug/Sep 2026 preview updates, wmic_dlc is temporary, and consumer Windows 10 is past end of support. Treat the flash host as an offline, one-off machine (Windows 10 lifecycle from Microsoft's published dates, not re-fetched).
- **Refuted findings:**
  1.
    - **Finding:** Stage 1: 'Debian stable/testing/sid and Ubuntu 26.04 still ship 1.6.8.'
    - **Why:** Only trixie (1.6.8-4) and noble/plucky (1.6.8-4build1) are 1.6.8 code. sid/forky 1.6.8-5, Ubuntu 25.10 1.6.8-5 and 26.04+ 1.6.8-5build1 are 'update to 1.6.8-59-g87cf12a (would be 1.8.1 if upstream released)', a 46-patch series up to the version bump (Debian changelog, patches/series, Launchpad API).
  2.
    - **Finding:** Stage 2: 'Labrx must call airspyhf_flash_configuration, not airspyhf_flash_calibration.'
    - **Why:** With the default noble 1.6.8 that function does not exist, so the build fails. airspyhf_flash_calibration is the only name that works with both versions: a real symbol in 1.6.8 and a macro in 1.8.1.
  3.
    - **Finding:** Stage 1: avoid commits 'between 1.8.0 and 0130450'.
    - **Why:** There is no 1.8.0 tag. The use-after-free window starts at e1dcc17 (2024-02-12) and ends at the fix 0130450 (2025-07-11), from git log -G on free_transfers.
  4.
    - **Finding:** Stage 2: Dream with a transmit option could ship 'behind a wrapper that passes receive arguments'.
    - **Why:** The packaged binary contains '-t, --transmitter', and the source enters transmitter mode when argv[0] is 'dreamt' (CSettings::IsReceiver). Any symlink bypasses an argument wrapper, so only a source patch, or not shipping Dream, meets P2.
  5.
    - **Finding:** Stage 1/2 premise: 12.5 V (or 13.8 V) must give ≥12 V 'at the antenna' because Bonito's 12 V minimum applies at the antenna.
    - **Why:** Bonito lists 'Spannungsversorgung: 12V-15V (2,1mm Hohlstecker)', which is the barrel input of the supplied bias tee. The vendor rating point is the inserter input. 13.8 V is still kept, but the gate moves to the barrel (antenna end recorded).
  6.
    - **Finding:** Stage 2: the AB9IL 170 mA figure is 'the original HF+, not the Discovery'.
    - **Why:** The AB9IL page says only 'the Airspy HF+' with no model and no method. It is an unattributed figure, not one for a known model.
  7.
    - **Finding:** Stage 1: ITEAD 'states no stock count'.
    - **Why:** ITEAD's WooCommerce store API shows the EU-warehouse variant '310 in stock' and the US variant '96 in stock' at USD 169.00 (18 Oct 2026).
  8.
    - **Finding:** Stage 1: 'the CH334 family supports MTT, so the 3.1-3.7 MB/s stream fits.'
    - **Why:** The conclusion holds, but the reason does not: the HF+ is a high-speed USB 2.0 device, and transaction translators serve only full/low-speed devices. The fit comes from 480 Mb/s bulk bandwidth, not MTT.
- **Corrected spec:** RECEIVER
  - Airspy HF+ Discovery, from ITEAD (EU warehouse; USD 169.00, 310 in stock 18 Oct 2026; check VAT) or WiMo (EUR 232 incl. VAT).
  - Specs: 0.5 kHz-31 MHz and 64-260 MHz; IIP3 +15/+13 dBm; BDR 110/95 dB; MDS -140 dBm (500 Hz, 15 MHz) and -141.5/-141.0 dBm VHF; +10 dBm max input (no DC rating, so DC is blocked toward it); -45..+85 C; 45x60x10 mm; 32 g; micro-USB B; single SMA input; no bias tee.
  - Firmware: minimum R4.0.7, target R5.0.1 (2024-12-11).
    - Flash on Windows 10, on Windows 11 with wmic_dlc, or by hand: bossac -u, then -e -b -v -w with the bb/cd binary chosen by hfplus_fw.exe, then --reset.
    - Recalibrate after every flash (FLASH.bat substitutes -152 ppb when the saved value is 0).
  - Bring-up record: airspyhf_info (S/N, firmware, rate list).
  
  HOST SOFTWARE (noble arm64)
  - Library: airspyhf / libairspyhf1 / libairspyhf-dev 1.6.8-4build1 (true 1.6.8, soname 1; udev 03eb:800c GROUP=plugdev TAG+=uaccess). labrx and sdrangel service users are in plugdev.
  - Optional 1.8.1: backport Debian 1.6.8-5 (87cf12a, soname 1) as +lab and rebuild every consumer against it. No upstream make install. Never a commit in e1dcc17..0130450^.
  - SoapyAirspyHF: tag soapy-airspyhf-0.2.1 (0b3daf0), built as +lab.
  - SDRangel 7.27.2 RX-only (Qt5): NAVTEX, RTTY, FT8, DSC, BFM/RDS, VOR, Radio Clock.
  - OpenWebRX+ 1.2.126, --no-install-recommends. Allowed HF+ rates: 768000 (default), 912000, 456000, 384000, 192000; never 256000. Gain and AGC are fixed per profile.
  - FT8/FT4/WSPR: 'wsjtx-decoders+lab' (make jt9 wsprd), plus a wsjtx_app_version stub printing 'WSJT-X 2.7.0'.
  - Forbidden: wsjtx, libhamlib-utils, js8call, direwolf, unpatched dream.
  - WEFAX v1: OpenWebRX+ 'fax' with the civil allow-list.
  - DRM v1: only with a source-patched Dream (transmitter removed; CI string check), else deferred to the first SDRangel release with demoddrm.
  - An SDRangel master build adds channeltx/modbfm to the TX removal list.
  
  CALIBRATION
  - Measure ppb against a conducted GNSS-disciplined reference.
  - Store it with 'airspyhf_calibrate -s <SN> -c <ppb>'.
  - labd pushes LOppmTenths = round(ppb/100) into every SDRangel AirspyHF preset (REST) and checks it after each preset load.
  - labrx adds no correction of its own.
  
  RECORDING
  - SigMF ci16 at 3.072 MB/s (768k) or 3.648 MB/s (912k).
  - Metadata: scale 1/32768 x filter_gain, lib_dsp state, firmware version, gain/AGC state.
  
  PROFILES
  - HF-F: 768 ksps Zero-IF.
  - LF window: centre 330 kHz at 768 ksps (alias-free 0..660 kHz; JJY 40 at -290, DCF77 at -252.5, TDF at -168, NAVTEX 490/518 at +160/+188 kHz; model). Or 290 kHz with negative-frequency masking.
  - Band mask: |f_abs| < 30 kHz, including negative bins, set to 'no data' before storage.
  - Radio Clock allow-list: DCF77, MSF, TDF (Europe priority), WWVB, JJY 40. JJY 60 amplitude-only. RBU blocked.
  
  USB AND POWER
  - CH334F H4, behind FE1.1s P3.
  - Short shielded micro-USB lead with strain relief, shell bonded to the mid plate, Mix-31 ferrite.
  - VBUS: load switch (MCP #1 GPA4) with current limit, then 100 uH (≥1.5x measured current, low DCR) and 100 uF with R-C damping (about 1.6 kHz corner, model).
  - Current limit ≥0.75 A at bring-up, then 1.5-2x measured streaming current. 0.3 A stays as the energy-model placeholder.
  - Tin shield with thermal contact to the mid plate, in the corner farthest from the bucks. Accepted only after the A/B test.
  
  INPUT SELECTOR
  - 2x Omron G6K-2F-RF series-shunt (K1 = P5 HF, K2 = P6 VHF2). De-energised: the HF+ sits on 50 Ω.
  - Acceptance: ≥35 dB isolation at 162-260 MHz and ≤0.3 dB loss from 10 kHz to 260 MHz, conducted on the LiteVNA (figures unverified until measured).
  
  ANTENNAS
  - Wire: Tecsun AN-05 7 m or 7-15 m of wire on a winder ≤20 cm; Nooelec Balun One Nine v2 (USD 26.95; 9:1; ≤80 MHz+; +24 dBm); counterpoise 3-5 m; feed point 5-10 m away on thin coax. HF only (above about 0.15 MHz).
  - Boni-Whip: buy from Bonito (hamradioshop.net, EUR 149 ≈ $167.49, in stock), WiMo (EUR 159, from 20.11.2026) as second source. 20 kHz-300 MHz, 12-15 V at the 5.5/2.1 mm barrel of the supplied Einspeiseweiche, 65 mA typ (vendor), about 17 cm body, BNC. BOM adds a BNC-SMA lead and a barrel plug.
  - Boni-Whip mounting: mast ≥2 m, ground stake or counterpoise; two-stage common-mode choke (FT-240-77 + FT-240-31) near P5; the bulkhead is bonded to the plate.
  - BONI13V8 rail: battery SW, then LC, then TPS7A4701 at 13.8 V ±0.2 V (EN on MCP #1 GPB1, PG on MCP #3), then PTC 0.15-0.2 A hold, then the Einspeiseweiche barrel inside the shield (or a DIY tee).
  - DIY tee: 2.2 mH (≥0.15 A, low DCR) + about 10 uH series choke and a 1 uF PPS/PEN film or C0G DC block (not X7R). Targets: ≤0.5 dB from 20 kHz to 30 MHz; ≤10 mV DC at the HF+ SMA.
  - Interlock: Boni profile only. DC-sense locks the rail below about 10 Ω at about 1 mA (set from the measured balun DCR). After enable, a current window of 30-150 mA (set from measurement) must hold, else the rail goes off.
  - Boni gate: ≥12.0 V at the barrel with the pack at 13.2 V; antenna-end voltage recorded. Energy model about 0.90 W.
  
  VHF ROLE
  - AIS (default), FM-RDS, NFM, airband and VOR on P6 through K2. No DAB on the HF+: DAB+ runs on the spare V4L or the Lime. VHF AGC, LNA and ATT do not take effect.
- **Bench tests:**
  - Arrival: airspyhf_info. Record S/N, firmware string and rate list; on firmware ≥R4.0.0 expect 228k, not 256k. Flash to R5.0.1 if older than R4.0.7, then run airspyhf_info again.
  - Calibration: feed a GNSS-locked 10 MHz (Bodnar/tinySA/GPSDO) conducted through ≥40 dB attenuation. Measure ppb and store it with airspyhf_calibrate -c, then re-open and confirm the read-back. The same carrier must read within 1 Hz in SDR++, SDRangel (LOppmTenths pushed by labd), labrx and OpenWebRX+.
  - Current: an FNB58 inline on HF+ VBUS. Idle (open, not streaming), and streaming at 768 and 912 ksps, cold and after 60 min sealed. Set the TPS2553/load-switch limit to 1.5-2x the streaming figure and update the mode E runtime.
  - USB soak behind FE1.1s and CH334F on kernel 6.18: 30 min with zero dropped buffers at 768k and 912k, with RTL-B and one LAB device streaming. Add 50 start/stop cycles and one 2 h run (excludes the R2.0.0-type 1.5 h TIMEOUT). Fail on any xhci 'refuse reset' or 'clear toggle' in dmesg or any callback stall.
  - SoapySDRUtil --probe=driver=airspyhf must report a non-zero gain range and the device rate list. Every OpenWebRX+ profile rate must actually apply: a known carrier must sit at the right frequency and the waterfall span must be right.
  - SDRangel: after each preset load, REST GET the AirspyHF settings and check that LOppmTenths equals round(ppb/100).
  - Shield and EMI A/B: terminated input (50 Ω through K1/K2 de-energised), RBW 1 Hz at 40, 60, 77.5, 162, 490, 518 and 4209.5 kHz and at 1, 7 and 14 MHz. Compare with and without the tin shield, with and without the USB-lead ferrite and shell bond, LF Quiet on and off, and D36V50F12/D36V28F5/IP2368 load steps.
  - VBUS LC: ripple at the HF+ VBUS pin from 1 kHz to 30 MHz, turn-on ringing and inrush current through the load switch.
  - BONI rail from a bench supply standing in for the pack at 16.4, 14.4, 14.0, 13.6 and 13.2 V: barrel and antenna-end voltage at the measured Boni current, and rail ripple spectrum at 60/77.5/162/490/518 kHz in dropout and out of it. Gate: ≥12.0 V at the barrel at 13.2 V.
  - Boni-Whip on arrival: DC input resistance at about 1 mA sense current, supply current cold and hot, and whip (Strahler) length against the 20-23 cm / 35 cm piece rule.
  - DC-sense and interlock: resistance seen at P5 for the balun, the Boni-Whip, open and a 50 Ω load. Set the short threshold and the 30-150 mA current window; check that the rail turns off on a short, on open and on an out-of-window current.
  - Bias tee (DIY or the Bonito Einspeiseweiche): S21 from 20 kHz to 30 MHz conducted on the LiteVNA, ≤0.5 dB. DC at the HF+ SMA with bias on, ≤10 mV.
  - Balun: DCR, and S21 at 40-500 kHz conducted, in 50/450 Ω and with a series 50-150 pF wire-simulator capacitor, to confirm the LF-on-whip rule.
  - G6K selector: conducted isolation (K1/K2, both de-energised) at 162-260 MHz ≥35 dB, and insertion loss from 10 kHz to 260 MHz ≤0.3 dB, with loads on the ports.
  - LF-window image test (conducted): a 35 kHz tone at centre 290 kHz should show an image near -35 kHz absolute (model). Repeat at centre 330 kHz. Check that stored data has every |f| < 30 kHz bin set to 'no data'.
  - Decode checks on the Boni-Whip in LF Quiet: DCF77, MSF and TDF (not Tuesday 08-12) in SDRangel 7.27.2 Radio Clock, and NAVTEX 490/518 kHz. Replay one DCF77/MSF recording at 768/32 and at the chosen Low-IF rate.
  - Policy CI on the image: dpkg shows no wsjtx, libhamlib-utils, js8call or direwolf; rigctl and rigctld absent. OpenWebRX+ detects FT8/WSPR (jt9/wsprd) and FST4/Q65 through the stub. If dream is present: its strings contain no '--transmitter' or 'CDRMTransmitter', 'dream -t' fails, and a 'dreamt' symlink does not enter transmit mode. The SDRangel plugin list contains no TX plugins (including modbfm if master is built).
  - Only for a 1.8.1 build: airspyhf_get_bias_tee_count returns 0 on the Discovery, no code calls airspyhf_set_bias_tee, and every consumer was rebuilt against the same library.
- **Confidence:** medium

