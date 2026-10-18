# Lab instruments: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_d9388111-e66`_

- **Subsystem:** lab_instruments
- **Findings:**
  1.
    - **Claim in stack:** VNA: LiteVNA 64 (Zeenko), 50 kHz-6.3 GHz, 1-path (S22/S12 by reversing the DUT), TDR; kit: 2x 30 cm cables, OSL (male), F-F adapter
    - **Finding:** Passion Radio's page: manufacturer WUYI ZEENKO, hardware version 3.1, 50 kHz-6.3 GHz, dynamic range 90 dB below 3 GHz and only 50 dB at 3 GHz and above, S11 noise floor <-50 dB (<3 GHz) / <-40 dB (>=3 GHz), <0.5 ppm, 3.95in 480x320 touch screen, 2000 mAh battery, microSD, 10-1001 points on the device (1-1024 over USB). In the box: LiteVNA64, '1 SMA calibration kit', USB cable, 2x 30 cm SMA M-M cables, 1 SMA F-F. The page does not state the gender of the OSL kit. zeenko.tech confirms TDR/DTF and the 50 kHz-6.3 GHz range. Its 'latest firmware' is a Google Drive folder, so no version could be read; the Passion Radio manual is labelled firmware 1.4.
    - **Verdict:** confirmed
    - **Action:** Keep. Add to the spec text: 'DR 50 dB above 3 GHz'. Do not use the LiteVNA for filter-rejection claims deeper than about 45 dB above 3 GHz; use the tinySA plus noise source for those. Check the OSL gender when it arrives.
    - **Impact:** Rejection and isolation tests above 3 GHz (5.8 GHz Wi-Fi checks, sled isolation at upper frequencies) are limited to about 50 dB.
    - **Sources:**
      - https://www.passion-radio.com/analyzer-spectrum/lite-vna64-2730.html
      - https://www.zeenko.tech/litevna
  2.
    - **Claim in stack:** LiteVNA price: $175.73 ex VAT (export) / $210.88 with French VAT at Passion Radio, 5 in stock; budget option Lab401 $215.83 (EUR 192)
    - **Finding:** Page data: list price EUR 182.50 ex VAT / EUR 219 incl. VAT, minus a EUR 26.17 discount, gives EUR 156.33 ex VAT / EUR 187.60 incl. 20% VAT. quantityAvailable=5, flagged 'Last items in stock'. At the stack's implied 1.1241 USD/EUR that is exactly $175.73 / $210.88. Lab401 lists 'LiteVNA (NanoVNA Compatible)' at EUR 192.00, available ($215.83).
    - **Verdict:** confirmed
    - **Action:** Keep the numbers. Order early: only 5 units, and the price is a temporary discount (list price EUR 219 = $246.18).
    - **Impact:** If the discount ends, the core total rises by about $35.
    - **Sources:**
      - https://www.passion-radio.com/analyzer-spectrum/lite-vna64-2730.html
      - https://lab401.com/search/suggest.json?q=litevna
  3.
    - **Claim in stack:** Clone risk: buy only from Passion Radio or the tinySA.org list
    - **Finding:** The tinySA.org Buying page covers tinySA units only and names neither Passion Radio nor Lab401. It lists the Zeenko AliExpress factory store, R&L, Eleshop, Switch Science, Mirfield, astroradio, Neven and Kami, plus Selteq and GOTRONIK for Ultra only. It warns that TinyRFEquip/TinyRFLab are not authorized, that Banggood sells clones, and that passing the selftest does not prove a unit is genuine. Passion Radio's provenance comes instead from its EU GPSR block, which names Zeenko as manufacturer and Passion Radio as the EU responsible person.
    - **Verdict:** corrected
    - **Action:** Reword: 'tinySA: only sellers on tinySA.org Buying; LiteVNA: Passion Radio (GPSR names Zeenko), Lab401, or the Zeenko AliExpress factory store'. Do not treat the tinySA.org list as covering the LiteVNA.
    - **Impact:** Wording and provenance only; no change to parts.
    - **Sources:**
      - https://tinysa.org/wiki/pmwiki.php?n=Main.Buying
      - https://www.passion-radio.com/analyzer-spectrum/lite-vna64-2730.html
  4.
    - **Claim in stack:** Female OSL = the kit's male OSL + F-F adapter ($0)
    - **Finding:** This works only if the adapter's delay goes into the cal-kit definition. Model (my calculation): a 15-20 mm SMA F-F barrel adds about 50-96 ps one way, i.e. about 60-117 degrees of round-trip phase error on open/short at 1.7 GHz and 200-400 degrees at 5.8 GHz if left undefined. Return-loss magnitudes of well-matched DUTs are hurt less, but phase, TDR and Smith-chart data are wrong.
    - **Verdict:** new_risk
    - **Action:** In P1, enter an offset delay for the adapted standards in NanoVNA-Saver's calibration-kit settings, or calibrate at the male plane and use port extension / adapter de-embedding. Record which plane the parts.yaml results use.
    - **Impact:** Above about 1 GHz, S11 phase and TDR on female-port DUTs are unreliable without this.
    - **Sources:**
      - https://www.passion-radio.com/analyzer-spectrum/lite-vna64-2730.html
  5.
    - **Claim in stack:** tinySA Ultra+ ZS407: Normal mode to 900 MHz, ULTRA mode to 7.3 GHz; input up to +6 dBm and +/-5 V DC; DANL -102 dBm at RBW 30 kHz; sine output -115...-19 dBm +/-2 dB up to 800 MHz; channel power +/-2 dB
    - **Finding:** The spec page says: Normal 100 kHz-800 MHz (900 MHz for Ultra+); ULTRA up to 6 GHz (7.3 GHz for ZS407); +/-5 V DC max; +6 dBm absolute max at 0 dB internal attenuation; +20 dBm short-term peak with 30 dB attenuation; best measurements below -25 dBm. Lowest discernible signal is -102 dBm at 30 MHz, 30 kHz RBW, without LNA, and -145 dBm at 200 Hz RBW with LNA. Generator: -115 to -19 dBm in 1 dB steps, but +/-2 dB accuracy holds only from -72 to -19 dBm up to 800 MHz, with less accuracy below -72 dBm. Absolute level after calibration is +/-2 dB. Hardware V0.5.3 is the first ZS407, and no later hardware is listed.
    - **Verdict:** corrected
    - **Action:** Change the generator spec to '+/-2 dB only between -72 and -19 dBm (<=800 MHz)'. Stack procedure P10 already does this correctly (generator at -40 dBm, then VNA-measured pads), so keep it, and never use the generator's own setting below -72 dBm as a calibrated level.
    - **Impact:** Prevents a 'calibrated MDS' made by setting the generator directly to about -110 dBm.
    - **Sources:**
      - https://tinysa.org/wiki/pmwiki.php?n=TinySA4.Specification
  6.
    - **Claim in stack:** tinySA price: $204.28 ex VAT / $247.18 incl. VAT (EUR 219.89) at Astroradio (on the tinySA.org list); budget option Mirfield $252.98 (GBP 189.95)
    - **Finding:** Astroradio: 'tinySA ULTRA++' ZS407 at EUR 219.89 incl. 21% VAT (EUR 215.50 by bank transfer), 'En stock entrega inmediata', 24 h shipping. Ex VAT this is EUR 181.73 = $204.28. Astroradio is on the tinySA.org list. The Mirfield price could not be read (IONOS site).
    - **Verdict:** confirmed
    - **Action:** Keep Astroradio. Mark the Mirfield price unverified. The bank-transfer price saves EUR 4.39.
    - **Impact:** None.
    - **Sources:**
      - https://www.astroradio.com/p/tinysa-ultra-analizador-de-espectro-plus/
      - https://tinysa.org/wiki/pmwiki.php?n=Main.Buying
  7.
    - **Claim in stack:** labd tinySA driver refuses generator/output commands outside Bench; QtTinySA used as the GUI
    - **Finding:** Current tinySA4 firmware is v1.4-252-g2b4aa51 (binaries 2026-09-30; changelog updated 2026-10-13). Since Sept 2026 the Ultra is a composite USB device (serial plus disk), with a new USB DISK mode ('usbdisk on|off') and firmware update from SD ('fwupdate {file} [flash]', STORAGE > MORE). v1.4223 (2026-03-24) added a 'channel [1-3]' total-power command, and 'capture rle' was added. Windows assigns a new COM port. QtTinySA v2.0.1 (2026-08-28) predates the composite-USB change.
    - **Verdict:** new_risk
    - **Action:** (1) Make the labd command filter default-deny (allow-list), and explicitly block 'usbdisk' and 'fwupdate' as well as output and generator commands outside Bench. (2) Turn off udisks automount for the tinySA disk interface, and match the serial port by VID:PID plus interface number in udev. (3) Pin and record the firmware tested at bring-up. (4) Test QtTinySA and labd against v1.4-252 inside the return window. (5) Use the 'channel' command for the power-meter readout.
    - **Impact:** Without this an unexpected disk device or command path could appear. The new channel-power command makes the tinySA power-meter role easier to script.
    - **Sources:**
      - http://athome.kaashoek.com/tinySA4/DFU/
      - http://athome.kaashoek.com/tinySA4/DFU/changelog.txt
  8.
    - **Claim in stack:** QtTinySA with PySide6 6.12 aarch64 wheels (manylinux_2_39 = glibc 2.39 noble)
    - **Finding:** PyPI: PySide6 6.12.0 was released 2026-10-08 with a manylinux_2_39_aarch64 wheel (Python >=3.10,<3.16); 6.11.2 came out 2026-08-18. QtTinySA v2.0.1 (2026-08-28) ships a prebuilt QtTinySA_arm64_2404.zip (Ubuntu 24.04 arm64) alongside the source. v2.0.0 added multi-device support (up to 4) and .npy recording, with a known segfault on close. The README names PySide6 and pyqtgraph and says testing was on Kubuntu 26.04 / Python 3.14.
    - **Verdict:** new_option
    - **Action:** Try the prebuilt QtTinySA_arm64_2404.zip first; fall back to the venv. In the venv, pin PySide6==6.11.2 (or 6.12.0 only after a test), because 6.12.0 is 10 days old.
    - **Impact:** Removes the build/wheel dependency and lowers the risk from a fresh Qt release.
    - **Sources:**
      - https://pypi.org/pypi/PySide6/json
      - https://github.com/g4ixt/QtTinySA/releases/expanded_assets/v2.0.1
      - https://github.com/g4ixt/QtTinySA
  9.
    - **Claim in stack:** NanoVNA-Saver main via pipx (numpy~=2.1, scipy~=1.14); apt nanovna-saver 0.6.3 rejected
    - **Finding:** main/pyproject.toml requires Python >=3.10, pyserial~=3.5, pyside6~=6.8, numpy~=2.1, scipy~=1.14. The latest release is v0.7.3 (2025-02-24, plus a nanovna-saver.raspi asset 2025-03-10). LiteVNA support arrived in v0.7.0, together with the PyQt6-to-PySide6 move. The package is not on PyPI (404), so pipx must install from git. Ubuntu noble apt still has 0.6.3-1.
    - **Verdict:** confirmed
    - **Action:** Keep it. Add a constraints file to the pipx install (PySide6==6.11.2 or whichever version was tested), because pyside6~=6.8 will otherwise pull 6.12.0. Pin a commit hash, since there has been no release for about 20 months.
    - **Impact:** Reproducible install.
    - **Sources:**
      - https://raw.githubusercontent.com/NanoVNA-Saver/nanovna-saver/main/pyproject.toml
      - https://github.com/NanoVNA-Saver/nanovna-saver/releases
      - https://github.com/NanoVNA-Saver/nanovna-saver/releases/expanded_assets/v0.7.3
      - https://packages.ubuntu.com/noble/nanovna-saver
  10.
    - **Claim in stack:** Noise source: ZFL-500LN+ (or ZFL-500+) in a home-built N8DMT-type source, $104.55-126.81; ENR table at stabilized 12 V (N8DMT: 20.5 dB at 28-52 MHz ... 8.4 dB at 2400 MHz); NF results relative (+/-2-3 dB)
    - **Finding:** Mini-Circuits: ZFL-500LN+ $116.81 (qty 1-4), more than 100 in stock, no EOL. Datasheet: 0.1-500 MHz, NF 2.9 dB, gain 24 dB min, 15 V nominal / 60 mA max, 17 V absolute max, 'open load not recommended'. ZFL-500+ is $99.55, more than 100 in stock: 0.05-500 MHz, NF 4.2 dB, gain 25 dB, 15 V / 80 mA. The N8DMT page confirms the table exactly at +12 V (28/52 MHz 20.5, 146 MHz 21.0, 440 MHz 20.1, 902 MHz 17.0, 1296 MHz 16.1, 2400 MHz 8.4; none at 3-4 GHz). The amplifier with a terminated input is the noise source. Caveats: the table is for N8DMT's own ZFL-500 unit; everything above 500 MHz is outside the amplifier's spec; and a datasheet-based model (NF+G) predicts about 26.9 dB in band against the measured 20.5 dB.
    - **Verdict:** confirmed
    - **Action:** Keep. Use the N8DMT values only as a sanity reference. Measure your own unit's ENR at the 12 V actually used and store it as the ENR table. No Y-factor above about 2.4 GHz (use the Sun or cold sky there). Run it at 12 V; do not exceed 17 V.
    - **Impact:** Relative NF stays valid; absolute ENR must come from your own unit.
    - **Sources:**
      - https://www.minicircuits.com/WebStore/dashboard.html?model=ZFL-500LN%2B
      - https://www.minicircuits.com/pdfs/ZFL-500LN+.pdf
      - https://www.minicircuits.com/WebStore/dashboard.html?model=ZFL-500%2B
      - https://www.minicircuits.com/pdfs/ZFL-500+.pdf
      - https://qsl.net/n8dmt/test-page/diy-test-equipment/low-cost-diy-noise-source/index.html
  11.
    - **Claim in stack:** RF accessories $212.68: Nooelec attenuator kit $47.95 (1/2/3/6/10/20 dB, 2 W, 6 GHz), 2x 30 dB, 2x BLK-89-S+ $20.26, 3x ANNE-50+ $14.84 (1 W), 3x 086-6SM+; budget option VAT-30W2+ $31.43
    - **Finding:** Nooelec SKU 100815 is $47.95: 1, 2, 3, 6, 10 and 20 dB, 2 W, DC-6 GHz; genders not stated. BLK-89-S+ is $20.26, more than 1000 in stock: 0.1-8000 MHz, 50 V DC, 4 W, SMA F to M. ANNE-50+ is $14.84, more than 1000 in stock: DC-18 GHz, 1 W, SMA-M, RL >=30 dB to 4 GHz. 086-6SM+ is $16.67, more than 1000 in stock. The two 30 dB pads are Passion Radio's 'RF attenuator SMA 0-6 GHz' at EUR 13.20 incl. VAT = $14.84, in stock. Recomputed total: 47.95 + 2x14.84 + 2x20.26 + 3x14.84 + 3x16.67 = $212.68, exact. VAT-30W2+ is $31.43 (30+/-0.3 dB, DC-6 GHz, 2 W), which makes it the precision upgrade, not a budget option.
    - **Verdict:** confirmed
    - **Action:** Keep. Relabel VAT-30W2+ as the 'precision 30 dB option (+$33 for two)'. Measure every pad with the LiteVNA, as already planned.
    - **Impact:** Labelling only.
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/attenuator-bundle.html
      - https://www.minicircuits.com/WebStore/dashboard.html?model=BLK-89-S%2B
      - https://www.minicircuits.com/pdfs/BLK-89-S+.pdf
      - https://www.minicircuits.com/WebStore/dashboard.html?model=ANNE-50%2B
      - https://www.minicircuits.com/pdfs/ANNE-50+.pdf
      - https://www.minicircuits.com/WebStore/dashboard.html?model=VAT-30W2%2B
      - https://www.minicircuits.com/pdfs/VAT-30W2+.pdf
      - https://www.passion-radio.com/analyzer-spectrum/lite-vna64-2730.html
  12.
    - **Claim in stack:** E-field near-field probes only: home-made semi-rigid pieces; one 086-6SM+ is cut into probes
    - **Finding:** The 086-6SM+ datasheet describes a 'Hand-Flex' cable: 6 inch, SMA male on both ends, DC-18 GHz, silver-plated copper-clad steel centre conductor, tin-soaked copper BRAID outer. It is hand-formable, not a true semi-rigid tube. Cutting one yields at most two single-SMA stub (monopole) E-field probes. No H-field (loop) probe appears anywhere in the BOM.
    - **Verdict:** corrected
    - **Action:** Reword to 'hand-formable 086 Hand-Flex stubs (tin-soaked braid), 2 probes per cable'. Three cables give up to 6 probes, so 1-2 cables are enough. Keep the E-field-only rule: no loop formed at the tip.
    - **Impact:** Rule compliance confirmed; wording and quantity only.
    - **Sources:**
      - https://www.minicircuits.com/pdfs/086-6SM+.pdf
      - https://www.minicircuits.com/WebStore/dashboard.html?model=086-6SM%2B
  13.
    - **Claim in stack:** SMA 0.9 N·m torque wrench + adapter set, $50.84-62.84 (TOJOIN eBay + RTL-SDR Blog); budget option AliExpress ratcheting $51.49
    - **Finding:** No primary listing could be fetched for the TOJOIN wrench or the AliExpress ratcheting wrench. WebSearch was unavailable (the turn's shared search budget was used up), and no URL was in the files.
    - **Verdict:** unverified
    - **Action:** Keep as unverified. Before buying, confirm the listing states 0.9 N·m (8 in-lb) for 5/16in (8 mm) SMA nuts.
    - **Impact:** Small price uncertainty.
    - **Sources:** []
  14.
    - **Claim in stack:** Spare LNA: RTL-SDR Blog Wideband LNA V2, $19.95 (208 in stock), 90 mA
    - **Finding:** Vendor page: $19.95, 208 in stock. It is QPL9547-based, 100 MHz-6 GHz, NF <1 dB, needs 3-5 V bias tee. The page gives no current draw. The 90 mA figure goes back to the V1 product (SPF5189Z chip; a reader comment quoting 75-105 mA, typically 90 mA), not to the V2's QPL9547. The Qorvo datasheet could not be fetched (HTTP 429).
    - **Verdict:** corrected
    - **Action:** Mark '90 mA' as V1-derived and unverified for V2. Measure the V2's current with the DPS-150/FNB58 before relying on the <=90 mA V4L-tee budget and the TPS2553 limit.
    - **Impact:** Bias budget for the spare V4L tee (C9) may be off.
    - **Sources:**
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
      - https://www.rtl-sdr.com/new-products-in-our-store-wideband-lna-spare-metal-v3-enclosures/
  15.
    - **Claim in stack:** USB tester: FNIRSI FNB58 Std (no radio), $53.99, fnirsi.com; FNIRSI logger
    - **Finding:** fnirsi.com Shopify data: variant 'FNB58 Std.' SKU FNB58 at $53.99 (compare-at $88.99), available; 'FNB58 BT' SKU FNB58-BT at $58.99. The baryluk logger supports FNB48, C1 and FNB58 (pyusb, udev rule 90-usb-power-meter.rules).
    - **Verdict:** confirmed
    - **Action:** Keep. Order SKU 'FNB58' (Std), not FNB58-BT.
    - **Impact:** None.
    - **Sources:**
      - https://www.fnirsi.com/products/fnb58
      - https://raw.githubusercontent.com/baryluk/fnirsi-usb-power-data-logger/master/README.md
  16.
    - **Claim in stack:** DMM: ANENG AN8008/9, $26-53, AliExpress (store not confirmed); 10 nA range
    - **Finding:** A third-party review confirms 99.99 uA range with 10 nA resolution, 9999 counts, 600 V CAT III / 1000 V CAT II. The meter is also sold as Zotek ZT109. The AN8009 is not covered. No primary store price was fetched.
    - **Verdict:** unverified
    - **Action:** Keep the spec. Price and store stay unverified. Accept only units whose PCB/markings match the reviewed design (ZT109 PCB).
    - **Impact:** Small.
    - **Sources:**
      - https://www.markhennessy.co.uk/budget_multimeters/aneng_an8008.htm
  17.
    - **Claim in stack:** Scope and LA: Hantek 6022BE + fx2lafw analyser, $141-172, The Debug Store (6022BE GBP 100); 6022BL discontinued at The Debug Store; 20 MHz, 8 bit; OpenHantek6022 3.4.1-rc2 arm64 .deb
    - **Finding:** The Debug Store: 'Hantek 6022BE USB Oscilloscope' at £100.00 ex VAT / £120.00 inc VAT, listed available. The 6022BL URL now returns 404. sigrok: 20 MHz, 48 MS/s, 8 bit, 2 ch, 1 MOhm||25 pF, software triggers only; supported by the hantek-6xxx driver with fx2lafw >=0.1.4. OpenHantek6022 3.4.1-rc2 is marked Latest, and openhantek_3.4.1-rc2_arm64.deb is dated 2026-05-03; a 'devdrop' pre-release snapshot is dated 08 Oct. Price check: $133.18 ex VAT / $159.82 inc VAT + LA fits $141-172.
    - **Verdict:** confirmed
    - **Action:** Keep. Note that £100 is ex VAT. Pin the 3.4.1-rc2 .deb (not devdrop) in the aptly mirror.
    - **Impact:** None.
    - **Sources:**
      - https://thedebugstore.com/products/hantek-6022be-usb-oscilloscope-uk
      - https://thedebugstore.com/products/hantek-6022bl-oscilloscope-analyser-uk
      - https://sigrok.org/wiki/Hantek_6022BE
      - https://github.com/OpenHantek/OpenHantek6022/releases
      - https://github.com/OpenHantek/OpenHantek6022/releases/expanded_assets/3.4.1-rc2
  18.
    - **Claim in stack:** Capability: 'LA 8/16 channels 24 MHz' (AN8008, FNB58, Hantek 6022BE, fx2lafw); PulseView 0.4.2, fx2lafw 0.1.7
    - **Finding:** The sigrok fx2lafw table lists the 6022BE with 0 logic channels and the 6022BL with 8 or 16 logic channels. A generic FX2 24 MHz analyser uses PB0-PB7 (8 ch); 16 ch needs PD0-PD7 wired (6022BL or 16-bit FX2 boards). Ubuntu noble ships pulseview 0.4.2-3build4, sigrok-firmware-fx2lafw 0.1.7-1 and sigrok-cli 0.7.2-1build2.
    - **Verdict:** corrected
    - **Action:** Change the capability to 'LA 8 channels, 24 MHz' for the 6022BE + generic FX2 kit. 16 channels only if a 16-bit CY7C68013A board or a 6022BL is bought.
    - **Impact:** Capability list overstated by 8 channels.
    - **Sources:**
      - https://sigrok.org/wiki/Fx2lafw
      - https://packages.ubuntu.com/noble/pulseview
      - https://packages.ubuntu.com/noble/sigrok-firmware-fx2lafw
      - https://packages.ubuntu.com/noble/sigrok-cli
  19.
    - **Claim in stack:** Debugger: Raspberry Pi Debug Probe, $12.00, Adafruit; SWD for the Pico; OpenOCD
    - **Finding:** Adafruit 5699 'Raspberry Pi Debug Probe Kit' is $12.00, in stock: SWD (CMSIS-DAP) plus a UART bridge, with a USB cable and 3 JST-SH cables. Noble openocd is 0.12.0-1build2, which covers RP2040; the stack uses RP2040 and rejected the RP2350B. The latest debugprobe firmware tag is v2.3.1 (29 May; the year is not shown, likely 2026).
    - **Verdict:** confirmed
    - **Action:** Keep. Update the probe to debugprobe v2.3.1 at bring-up.
    - **Impact:** None.
    - **Sources:**
      - https://www.adafruit.com/product/5699
      - https://github.com/raspberrypi/debugprobe/releases
      - https://packages.ubuntu.com/noble/openocd
  20.
    - **Claim in stack:** Soldering iron: Pinecil V2 (IronOS Bluetooth Off), $25.99, PINE64 (unverified); powered from the 20 V PD bank (about 64 W)
    - **Finding:** PINE64: 'PINECIL ... (Version 2)', SKU PINECIL-BB2, $25.99 community price (retail $35.99), in stock. Inputs: USB-C PD/QC 12-20 V 3 A, DC5525 12-24 V 3 A; TS-B2 tip included. IronOS V2.23 (2025-08-31) makes BLE off by default 'for security reasons' and switches to a conservative 'safe' USB-PD profile. 64 W is a model figure (20 V into about 6.25 Ohm = 3.2 A). It needs the bank's 20 V/5 A PDO and a 5 A e-marked cable; with a 3 A cable the limit is <=60 W.
    - **Verdict:** confirmed
    - **Action:** Status -> verified. Flash IronOS >=2.23 on arrival (units may ship older) and confirm Bluetooth = Off in settings. Add a 5 A e-marked USB-C cable to the bench kit, or accept 60 W.
    - **Impact:** Rule compliance (no BLE) is now the firmware default.
    - **Sources:**
      - https://pine64.com/product/pinecil-smart-mini-portable-soldering-iron/
      - https://github.com/Ralim/IronOS/releases
  21.
    - **Claim in stack:** Anti-static mat: iFixit portable anti-static mat, $34.95 (unverified)
    - **Finding:** $34.95, 'Ready to ship', 60x60 cm. Includes a 1.8 m 1 MOhm wrist strap and a ground cord with clip (10 mm snap).
    - **Verdict:** confirmed
    - **Action:** Status -> verified.
    - **Impact:** None.
    - **Sources:**
      - https://www.ifixit.com/products/portable-anti-static-mat
  22.
    - **Claim in stack:** PD bank: Anker 737 (PDO 20 V/5 A, <=100 Wh), $109.99; carry-on (24,000 mAh, about 86-88 Wh)
    - **Finding:** Anker: 737 Power Bank (PowerCore 24K), A1289011, $109.99, in stock, 24,000 mAh. Each USB-C port offers 5V/3A, 9V/3A, 15V/3A, 20V/5A and 28V/5A, 140 W total. Wh is not listed; 24,000 mAh x 3.6 V = 86.4 Wh (model). Anker's recall page lists A1647/A1652/A1681/A1689/A1257 and PowerCore 10000 (June 2025); A1289 is not on it.
    - **Verdict:** confirmed
    - **Action:** Keep. Also usable at 28 V for the ISDT 608PD (USB-C 5-28 V input).
    - **Impact:** None.
    - **Sources:**
      - https://www.anker.com/products/a1289
      - https://www.anker.com/product-recalls
  23.
    - **Claim in stack:** Bench hub: Waveshare MTT bench hub (powered from the bank), $24.64 (GBP 18.50), The Pi Hut
    - **Finding:** The item is 'Industrial Grade Dual-Host USB Hub (4x USB 2.0)', Waveshare, SKU WAV-21686, £18.50, available. Features list says 'adopting MTT technology', but the product text also says it 'utilises STT technology'. Power: 5 V via DC jack or USB-C power input; ships with a UK-plug 5 V 2 A PSU; two switchable USB-C host ports; -40 to 85 C.
    - **Verdict:** new_risk
    - **Action:** Keep the part. Confirm MTT on arrival with lsusb -v (hub bDeviceProtocol 2 = multi-TT). If it is single-TT, never run two full-speed/isochronous instruments through it at once. Power it from the bank's 5 V USB-C.
    - **Impact:** With single-TT, several FS devices (FX2 LA, tinySA, FNB58) would share one TT.
    - **Sources:**
      - https://thepihut.com/products/industrial-grade-dual-host-usb-hub-4x-usb-2-0
  24.
    - **Claim in stack:** Balance charger: ISDT 608PD, $32.99-42.99 (unverified)
    - **Finding:** DarwinFPV official store: $49.99, available. Specs: DC 5-30 V / USB-C 5-28 V input, 240 W DC / 140 W USB-C, 1-6S LiPo/LiHV, balance current 0.8 A/cell, operating 0-40 C. The listing says 'Support APP connection'; the link type (Bluetooth or other) is not stated.
    - **Verdict:** corrected
    - **Action:** Price -> $49.99 (core total about +$7 to +$17). Check whether the 608PD has a built-in radio. If it does, it belongs on the QUIET/field checklist (charging only at home with the receiver off). Charge only within 0-40 C, which is tighter than the pack's 0-45 C NTC window.
    - **Impact:** Core lab total increases slightly; possible radio emitter on the bench.
    - **Sources:**
      - https://darwinfpv.com/products/isdt-608pd-lipo-charger-dc-240w-10a-usb-c-140w-5a-smart-digital-charger
  25.
    - **Claim in stack:** GPSDO (extended): Leo Bodnar LBE-1420, $175.80 (GBP 132; VAT basis not stated), in stock, antenna included; conducted, 80 dB attenuation + DC block; Bodnar Mini at the same price replaced
    - **Finding:** LBE-1420 page: £132.00 (VAT basis not stated), in stock. 1 Hz-1.1 GHz (operation possible to 1.5 GHz), +11 dBm at 10 MHz, 3.3 V CMOS square wave with 50 Ohm source, one SMA, USB-C 5 V 250 mA max, active magnetic-base GPS antenna with 5 m cable. The Mini GPSDO page (£132, 400 Hz-810 MHz, Mini-USB, FW 1.17) recommends the LBE-1420 as the newer version. The 2-port LBE-1421 is £198. Model: +11 dBm - 80 dB = -69 dBm at the DUT; a square wave carries strong odd harmonics.
    - **Verdict:** confirmed
    - **Action:** Keep. Keep the 80 dB + BLK-89-S+ rule and the 'off and disconnected' rule for H1/ADS-B/Inmarsat-C sessions.
    - **Impact:** None.
    - **Sources:**
      - https://www.leobodnar.com/shop/index.php?main_page=product_info&cPath=107&products_id=393
      - https://www.leobodnar.com/shop/index.php?main_page=product_info&products_id=301
  26.
    - **Claim in stack:** Software: lbgpsdo with python hid and a udev rule (for the LBE-1420)
    - **Finding:** In hamarituc/lbgpsdo, lbe142x.py enumerates only USB ID 1dd2:2444 (LBE-1421) and has 'TODO: 1420' comments; its 99-lbgpsdo.rules does include 2443 (LBE-1420). The README lists the classic GPSDO/Mini and the LBE-1421, not the 1420. simontheu/lbe-1420 (C, lbe-142x.c over hidraw) is written for the LBE-1420 (HID_ID 1DD2:2443, e.g. '--f1 10000000').
    - **Verdict:** corrected
    - **Action:** Use simontheu/lbe-1420 (build with gcc) for the LBE-1420, or patch USBIDS in lbe142x.py to add (0x1dd2, 0x2443) and test. Keep the udev rule for 2443.
    - **Impact:** As written, the stack's tool would not detect the LBE-1420.
    - **Sources:**
      - https://raw.githubusercontent.com/hamarituc/lbgpsdo/master/lbe142x.py
      - https://raw.githubusercontent.com/hamarituc/lbgpsdo/master/99-lbgpsdo.rules
      - https://github.com/hamarituc/lbgpsdo
      - https://raw.githubusercontent.com/simontheu/lbe-1420/main/README.md
  27.
    - **Claim in stack:** Bench supply (extended): FNIRSI DPS-150, $73-75, Elektor / various
    - **Finding:** Elektor lists the DPS-150 at EUR 59.00 incl. VAT, with orders redirected to Eleshop (= $66.32 at 1.1241). Specs: input 5-32 V DC (PD/QC/DC), output 0-30 V / 0-5 A / 150 W, <20 mV ripple, 0.01 V / 0.001 A resolution.
    - **Verdict:** corrected
    - **Action:** Price -> about $66 incl. VAT (extended total about -$7 to -$9).
    - **Impact:** Slightly cheaper.
    - **Sources:**
      - https://www.elektor.com/products/fnirsi-dps150-dc-power-supply-150-w
  28.
    - **Claim in stack:** Rule compliance of the lab kit (receive-only, conducted sources, E-field only, no radio emitters in QUIET)
    - **Finding:** No loop or H-field probe appears in the BOM. Every signal source (LiteVNA port 1, tinySA generator, ZFL noise source, LBE-1420) is described with conducted-only use plus pads and DC blocks. FNB58 Std is a separate SKU without BT. Pinecil BLE is off by default from IronOS 2.23. The remaining open items are the ISDT 'APP connection' and the tinySA's new firmware command paths.
    - **Verdict:** confirmed
    - **Action:** Add the ISDT radio check and the tinySA default-deny command filter (see above) to P0.
    - **Impact:** Compliance is kept.
    - **Sources:**
      - https://tinysa.org/wiki/pmwiki.php?n=TinySA4.Specification
      - https://github.com/Ralim/IronOS/releases
      - https://www.fnirsi.com/products/fnb58
- **Current status oct 2026:** As of 18 Oct 2026:
  - **LiteVNA 64:** hardware v3.1 at Passion Radio, discounted to EUR 156.33 ex VAT / EUR 187.60 incl. VAT, only 5 left ('last items'). Lab401 EUR 192, available. No newer hardware revision found; the firmware version could not be read (Zeenko publishes it in a Drive folder).
  - **tinySA Ultra+ ZS407:** current hardware (V0.5.3 is the latest listed). Astroradio EUR 219.89 incl. VAT, in stock. Firmware v1.4-252 (2026-09-30) adds composite USB (serial + disk), USB DISK mode, SD firmware update, a 'channel' power command and RLE capture.
  - **Lab software:** QtTinySA v2.0.1 (2026-08-28) has a prebuilt arm64 Ubuntu 24.04 zip. PySide6 6.12.0 came out 2026-10-08 (aarch64 manylinux_2_39 wheel); 6.11.2 is the conservative pin. NanoVNA-Saver's last release is v0.7.3 (2025-02-24), with LiteVNA support since v0.7.0; noble apt still has 0.6.3. OpenHantek6022 3.4.1-rc2 arm64 .deb (2026-05-03) is Latest, with a devdrop snapshot on 08 Oct. Noble ships PulseView 0.4.2, fx2lafw 0.1.7, sigrok-cli 0.7.2 and OpenOCD 0.12.0.
  - **Pinecil and Debug Probe:** IronOS V2.23 (2025-08-31) is current, with BLE off by default; Pinecil V2 $25.99, in stock. Debugprobe firmware v2.3.1.
  - **Mini-Circuits:** ZFL-500LN+ $116.81, ZFL-500+ $99.55, BLK-89-S+ $20.26, ANNE-50+ $14.84, 086-6SM+ $16.67, VAT-30W2+ $31.43. All in stock, no EOL notices.
  - **Other vendors:**
    - Nooelec attenuator kit $47.95.
    - RTL-SDR LNA V2 $19.95 (208 in stock).
    - FNB58 Std $53.99.
    - Debug Probe $12.
    - iFixit mat $34.95.
    - Anker 737 $109.99, in stock, not recalled.
    - Waveshare dual-host MTT hub £18.50.
    - Hantek 6022BE £100 ex VAT; the 6022BL is gone from The Debug Store.
    - LBE-1420 £132, in stock.
    - ISDT 608PD $49.99 (price corrected).
    - DPS-150 EUR 59.
- **Notes:** Method limits: WebSearch was unavailable from the first call (the turn's shared 200-search budget was already used up), so every check used WebFetch or curl on primary pages: manufacturer and distributor pages, Shopify product JSON, datasheet PDFs, PyPI JSON, packages.ubuntu.com, the tinySA firmware directory, raw.githubusercontent.com, and github.com release pages through WebFetch. The gh API and github.com via curl were blocked.
  
  Unverified:
  - TOJOIN SMA torque wrench and the AliExpress ratcheting wrench
  - ANENG AN8008/9 store and price, and whether AN8009 matches
  - Hantek 6022BL AliExpress price
  - Mirfield tinySA price
  - RTL-SDR LNA V2 current draw (Qorvo QPL9547 datasheet returned HTTP 429)
  - Gender of the LiteVNA OSL kit
  - LiteVNA firmware version
  - Whether the ISDT 608PD has a radio
  - Year of the debugprobe v2.3.1 release
  - VAT basis of the Leo Bodnar prices
  
  Model numbers (my calculations, not from sources):
  - Adapter delay and phase error: 50-96 ps; 60-117 deg at 1.7 GHz
  - ZFL ENR from datasheet NF+G: about 26.9 dB
  - Pinecil: 64 W = 20 V into 6.25 Ohm
  - Anker 737: 86.4 Wh
  - Currency conversions use the stack's implied 1.1241 USD/EUR and 1.3318 USD/GBP
  
  Net effect on the totals:
  - Core lab: about +$7 to +$17 (ISDT price).
  - Extended: about -$7 to -$9 (DPS-150).
  - If the Passion Radio discount ends, the LiteVNA costs about +$35 more (list EUR 219).
  
  Corrections to make in STACK.md:
  - Generator accuracy: +/-2 dB only from -72 to -19 dBm.
  - LA is 8 channels, not 8/16.
  - 086-6SM+ is Hand-Flex braid (2 probes per cable), not semi-rigid.
  - LBE-1420 needs simontheu/lbe-1420 or a patched lbgpsdo.
  - The 90 mA LNA figure is from V1.
  - VAT-30W2+ is the precision option, not the budget one.
  - The clone-avoidance rule needs rewording: the tinySA.org list covers tinySA only.
  
  New risks:
  - Female OSL made from a male kit plus an F-F adapter needs a delay definition.
  - tinySA firmware v1.4-252 adds a composite USB device and new commands, so labd needs a default-deny command filter, no automount and a pinned firmware.
  - Hub MTT vs STT wording contradiction: check with lsusb.
  
  New option: the prebuilt QtTinySA arm64 Ubuntu 24.04 zip.

