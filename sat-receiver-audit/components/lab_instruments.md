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

## Адверсаріальна перевірка (`verify`)

_Run `wf_d9388111-e66`_

- **Subsystem:** lab_instruments
- **Verdict:** The subsystem survives with corrections. All instrument choices stand: LiteVNA 64, tinySA Ultra+ ZS407, the ZFL-500LN+ noise source, E-field-only probes, Mini-Circuits and Nooelec passives, FNB58 Std, AN8008, Hantek 6022BE with an 8-channel FX2 LA, Debug Probe, Pinecil V2, Anker 737, LBE-1420 and DPS-150. Every signal source stays conducted-only and there is no loop or H-field probe anywhere. Most stage-1 and stage-2 findings were reproduced on primary sources. The adversarial pass found errors in both earlier stages.
  (1) The Passion Radio 30 dB pad was priced as the 3 dB variant (EUR 13.20). The 30 dB variant is EUR 18.20 incl. VAT and is out of stock.
  (2) The prebuilt QtTinySA arm64 zip is a Nuitka build made on PiOS 13 Trixie. Upstream has not tested it on Ubuntu 24.04, so 'noble glibc 2.39 is fine' is not established.
  (3) The LiteVNA 'POWER ATTENUATION' menu exists on the 7-inch LiteVNA only.
  (4) No vendor shows a LiteVNA 64 with hardware >=v0.4.5. Plan on the HW 3.1 figures (90 dB below 3 GHz, 50 dB above).
  (5) The ENR model at the real 12 V supply (gain 24.3-24.9 dB) predicts about 17.5 dB with N8DMT's 10 dB pad. That is about 3 dB under his 20.5 dB, so the pad does not fully explain the gap. Measuring your own unit is mandatory.
  (6) NanoVNA-Saver #841 is not tied to the LiteVNA.
  New risks:
  - Pinecil V2 IronOS negotiates up to 28 V EPR / 140 W, while PINE64 rates USB-C input at 12-20 V 3 A.
  - The bench hub's 5 V 1.2 A USB output.
  - The tinySA input is 50 Ohm only with >=10 dB internal attenuation.
  - QtTinySA probes the LiteVNA's VID:PID 04b4:0008.
  - scikit-rf 2.2.0 was released today.
  Net totals:
  - Core: +$18 to +$28 (Passion Radio pads, backorder) or +$40 to +$50 (VAT-30W2+, in stock). Of that, +$7 to +$17 is the ISDT price.
  - Extended: about -$7 to -$9 (DPS-150).
- **Confirmed:**
  - LiteVNA 64 at Passion Radio: SKU NANO-LITEVNA64-2730, manufacturer WUYI ZEENKO (EU GPSR block names Passion Radio as responsible person), 'Hardware version: 3.1', DR 90 dB (<3 GHz) / 50 dB (>=3 GHz), S11 floor <-50/<-40 dB, <0.5 ppm, 3.95in 480x320, 2000 mAh. List EUR 182.50 ex / EUR 219 incl. VAT; tax-excluded reduction EUR 26.17 gives EUR 156.33 ex / EUR 187.60 incl. = $175.73 / $210.88. quantityAvailable=5, 'Last items in stock!'. Box: 1 SMA cal kit, USB cable, 2x 30 cm SMA M-M, 1 SMA F-F.
  - LiteVNA user guide (PDF created 2026-07-06, 'based on v1.4 firmware') gives dynamic range by HW revision: >50 dB above 3 GHz for HW<=v0.3.2, >70 dB for v0.3.3, >80 dB for HW>=v0.4.5 (IFBW 225 Hz); >90 dB below 3 GHz (v0.3.x), >100 dB for HW>=v0.4.5 (IFBW 50 Hz). Supply USB 5 V +/-0.5 V, 1 A max (62/64). Battery protection state needs charging while powered off. SMA female ports. Device sweep 21-1001 points, USB 1-65535.
  - LiteVNA enumerates as 04B4:0008 ('S-A-A-2' entry in NanoVNA-Saver Hardware.py, then probed by is_lite_vna_64); binary V2 protocol; deviceVariant register 0xf0 = 0x02.
  - tinySA spec page: Normal 100 kHz-800 MHz (900 MHz Ultra+); ULTRA to 6 GHz (7.3 GHz ZS407); +/-5 V DC max; +6 dBm absolute max at 0 dB attenuation; +20 dBm short-term peak with 30 dB; suggested max 0 dBm in auto attenuation; best below -25 dBm; IIP3 +15 dBm; P1dB -1 dBm; linearity +/-2 dB <5.3 GHz and +/-5 dB 5.3-6 GHz; absolute +/-2 dB after calibration; LDS -102 dBm (30 MHz, RBW 30 kHz, no LNA). Generator: -115 to -19 dBm in 1 dB steps; +/-2 dB only from -72 to -19 dBm up to 800 MHz. Battery >=3 h (Ultra+); charge <=1 h on a >=500 mA port. HW V0.5.3 = first ZS407.
  - tinySA Limitations page: LNA on disables the input attenuator ('stronger signals will easily overload the LNA'); radiation from the MCU at 48 MHz and its harmonics.
  - tinySA4 firmware: only binary in the DFU directory is tinySA4_v1.4-252-g2b4aa51 (2026-09-30); changelog modified 2026-10-13. v1.4252 adds composite USB (serial + disk), 'usbdisk on|off', 'fwupdate {file} [flash]', 'capture rle', fixes for the 64-byte-multiple USB reply wait and a console race. v1.4223 (2026-03-24) adds the 'channel [1-3]' command and a fix for occasional serial hangs. Changelog labels are non-monotonic (V1.4245 dated 2026-09-27 sits above V1.4252 dated 2026-09-26).
  - tinySA.org Buying page (modified 2026-05-20) covers tinySA only. Ultra sellers: Zeenko AliExpress factory store, Eleshop, R&L, Switch Science, Mirfield, astroradio, Neven, Kami, Selteq, GOTRONIK, Aursinc and SeeSii on Amazon. TinyRFEquip and TinyRFLab are not authorised; Banggood sells clones; passing the selftest does not prove a unit is genuine. Neither Passion Radio nor Lab401 is listed.
  - Astroradio 'tinySA ULTRA++' ZS407: EUR 219.89 incl. 21% VAT, EUR 215.50 by bank transfer, 'En stock entrega inmediata'.
  - NanoVNA-Saver: pyproject requires pyserial~=3.5, pyside6~=6.8, numpy~=2.1, scipy~=1.14, Python>=3.10. Not on PyPI. Latest release v0.7.3 (24 Feb 2025). Main has 4852068 'Add TCP/IP support' and 2b872a4 socat notes (18 Apr 2026); the newest commit is 3445a0a 'Fix empty str check' (18 Apr 2026). Noble apt still has nanovna-saver 0.6.3-1.
  - NanoVNA-Saver #796 is open: LiteVNA64, Saver 0.7.1/0.7.2, Windows 11. The maintainer says 'The problem is in the serial communication with the LiteVNA64' (short reads, e.g. 5825 of 6432 bytes). No fix. #791 is open: wrong LiteVNA64 firmware/Vbat/serial info.
  - PySide6: 6.11.0 (2026-03-23), 6.11.1, 6.11.2 (2026-08-18) and 6.12.0 (2026-10-08) all have cp310-abi3 manylinux_2_39_aarch64 wheels. QtTinySA src/requirements.txt pins pyside6==6.11.0.
  - QtTinySA v2.0.1 (2026-08-28) assets include QtTinySA_arm64_2404.zip (142 MB). v2.0.0 added multi-device support (up to 4) and lists a segfault on close on any OS.
  - QtTinySA devices.py matches VID (0x0483, 0x1d50, 0x04b4) and PID (0x5740, 0x6108, 0x0008), identifies devices by USB product string, and opens the ttyACM itself. It sends no generator or output command. It does have 'reset' and a correction-table read and upload path.
  - scikit-rf NanoVNAv2 driver lists the LiteVNA (zeenko.tech), connects via 'ASRL/dev/ttyACM0::INSTR', and returns only uncalibrated networks.
  - ZFL-500LN+ datasheet: 0.1-500 MHz, NF 2.9 dB typ, gain 24 dB min, 15 V / 60 mA, +17 V max, 'Open load is not recommended'. Typical gain is 24.3-24.9 dB at 12 V and 27.8-28.2 dB at 15 V. Web store: $116.81 (qty 1-4), more than 100 in stock, no EOL. ZFL-500+: $99.55, 0.05-500 MHz, NF 4.2 dB, gain 25 dB, 15 V / 80 mA.
  - N8DMT: the source is a ZFL-500LN at +12 V with a 5 dB pad on the input and 2x 5 dB (10 dB) on the output, measured with the tinySA Ultra MEASURE > MORE > NOISE FIGURE routine with EXT GAIN = 0. Table: 28/52 MHz 20.5, 146 MHz 21.0, 440 MHz 20.1, 902 MHz 17.0, 1296 MHz 16.1, 2400 MHz 8.4 dB; no value at 3-4 GHz. Without the output pads he expects 'closer to 30 dB'. The tinySA Ultra 'seems to have difficulty' above about 4 GHz.
  - Mini-Circuits web store: BLK-89-S+ $20.26 (SMA F-M, 0.1-8000 MHz, 50 V DC, 4 W), ANNE-50+ $14.84 (DC-18 GHz, RL >=30 dB to 4 GHz, 1 W, SMA-M), 086-6SM+ $16.67 (Hand-Flex, copper-clad steel centre, tin-soaked copper braid, SMA M both ends, 8 in-lb max, use the anti-torque nut), VAT-30W2+ $31.43 (30+/-0.3 dB, DC-6 GHz, 2 W; VSWR 1.25 typ / 1.35 max DC-3 GHz). All show more than 1000 in stock; none has an EOL notice.
  - Nooelec SKU 100815: $47.95; 1/2/3/6/10/20 dB (1-42 dB total), 2 W, DC-6 GHz; +/-0.1 dB DC-3 GHz, +/-0.4 dB DC-6 GHz, VSWR <1.2 max.
  - RTL-SDR Blog Wideband LNA V2: $19.95, 208 in stock, QPL9547, 100 MHz-6 GHz, NF <1 dB, 3-5 V bias tee. Current draw not stated.
  - FNB58 at fnirsi.com: 'FNB58 Std.' SKU FNB58 $53.99 (compare-at $88.99), available; 'FNB58 BT' SKU FNB58-BT $58.99. baryluk logger supports FNB48, C1 and FNB58 (pyusb, udev rule 90-usb-power-meter.rules). Its README says firmware updates require Windows.
  - AN8008 review (Mark Hennessy): 9999 counts; 99.99 uA range with 10 nA resolution (+/-0.8%+3) on the V/Ohm input; mA via the 10 A shunt (0.1 mA resolution); 9.999 MOhm max; minimal protection; CAT claims doubtful, so low-energy bench use only; DM1106EN chip; 2x AAA not supplied; sold as Zotek ZT109. AN8009 not covered.
  - The Debug Store Hantek 6022BE: GBP 100.00 ex VAT / GBP 120.00 inc VAT, available. The 6022BL URL returns 404.
  - sigrok: 6022BE has 0 logic channels; 6022BL has 8/16. FX2 analysers use PB0-PB7 for 8 channels and need PD0-PD7 for 16; all use a 24 MHz crystal. Noble ships pulseview 0.4.2-3build4, sigrok-firmware-fx2lafw 0.1.7-1, sigrok-cli 0.7.2-1build2, openocd 0.12.0-1build2.
  - OpenHantek6022: 3.4.1-rc2 is Latest, with openhantek_3.4.1-rc2_arm64.deb; devdrop pre-release 08 Oct. Qt6 move, arm64 build, reconnect after USB disconnect (#467). Limitations doc: max 30 MS/s CH1 only or 15 MS/s for CH1+CH2 (8-bit vs 16-bit samples), all streamed as USB bulk. After sigrok use, replug the scope and confirm FW0210. GLES fallback with 'OpenHantek -e'.
  - Adafruit 5699 Debug Probe kit: $12.00, in stock; SWD (CMSIS-DAP) + UART; latest debugprobe tag v2.3.1 (29 May, year not shown).
  - Pinecil V2 (PINE64 SKU PINECIL-BB2): $25.99 community price, in stock; USB-C PD/QC 12-20 V 3 A, DC5525 12-24 V 3 A. IronOS V2.23 (31 Aug 2025): 'Bluetooth BLE is off by default (security)'; PD default changed to the 'safe' profile. Settings.md: 'No Dynamic disables EPR & PPS, Safe mode does not use padding resistance'; a Power pulse setting exists.
  - iFixit IF145-202-5: $34.95, 'Ready to ship', 60x60 cm, 1.8 m 1 MOhm wrist strap, ground cord with 10 mm snap, surface 10^7-10^9 Ohm.
  - Anker 737 (PowerCore 24K, images A1289011): $109.99, in stock, 24,000 mAh; each USB-C 5V/3A, 9V/3A, 15V/3A, 20V/5A, 28V/5A; 140 W total; 140 W needs a PD 3.1 cable and device. A1289 is not on Anker's recall page (A1647/A1652/A1681/A1689/A1257, June 2025).
  - Waveshare dual-host hub at The Pi Hut: SKU WAV-21686, GBP 18.50, available. The text says both 'utilises STT technology' and 'adopting MTT technology'. 5 V via DC jack or USB-C; ships with a UK 5 V 2 A PSU; 'USB Output 5V@1.2A'.
  - ISDT 608PD at DarwinFPV: $49.99, available. DC 5-30 V / USB-C 5-28 V in; 240 W DC / 140 W USB-C; USB-C discharge 100 W/5 A; balance 0.8 A/cell; operating 0-40 C; 85 g; 'Support APP connection'. ISDT's own page advertises phone-app control (ISD Link) and OTA cloud upgrade without naming the link type.
  - Leo Bodnar LBE-1420: GBP 132.00 (VAT basis not stated), in stock. 1 Hz-1.1 GHz (often to 1.5 GHz); +11 dBm at 10 MHz; 3.3 V CMOS square wave, 50 Ohm source; SMA out + SMA antenna (3.3 V / 30 mA); USB-C 5 V 250 mA max; active magnetic GPS antenna with 5 m cable; settings stored in the device.
  - hamarituc lbgpsdo lbe142x.py lists only (0x1dd2, 0x2444) and carries 'TODO: 1420' comments. bvernoux/lbe-142x v1.2 (20 Apr 2026) supports the LBE-1420 (0x2443, --f1 up to 1.6 GHz) and the Mini; libudev and CMake; tested on Windows 11 and Ubuntu 24.04 x64. simontheu/lbe-1420 is a gcc build over hidraw (HID_ID 1DD2:2443).
  - Elektor DPS-150: EUR 59.00 incl. VAT, ordered via Eleshop ('prices may vary'); 5-32 V DC in; 0-30 V / 0-5 A / 150 W out; <20 mV ripple; 0.01 V / 0.001 A resolution.
  - Rule compliance: no loop or H-field probe in the BOM; every signal source is conducted-only (LiteVNA port 1, tinySA generator, ZFL source, LBE-1420); FNB58 Std has no radio; Pinecil BLE is off by default.
- **Corrections:**
  1.
    - **Claim in stack:** RF accessories $212.68 incl. 2x 30 dB pads from Passion Radio at EUR 13.20 incl. VAT ($14.84), in stock (stage 1: confirmed, exact)
    - **Finding:** Passion Radio 'SMA RF attenuator 0-6 Ghz -3db...-30db' (sma-attenuator-826): EUR 13.20 incl. VAT is the base price of the -3 dB variant. The -30 dB combination (ref ADAPT-SMA-ATTENUA30-8263) adds EUR 4.17 ex VAT, giving EUR 15.17 ex / EUR 18.20 incl. VAT ($20.46). Its quantity is -6 (backorder; 'Out of stock, available within 1 month'). Mini-Circuits VAT-30W2+ is $31.43 (30+/-0.3 dB), more than 1000 in stock.
    - **Verdict:** corrected
    - **Action:** Either backorder 2x Passion Radio 30 dB at $20.46 each (line $223.92, +$11.24), placed separately so the 'last items' LiteVNA ships now; or, preferred for availability and specified accuracy, buy 2x VAT-30W2+ in the same Mini-Circuits order (line $245.86, +$33.18). Measure every pad on the LiteVNA either way.
    - **Impact:** Core total rises by $11.24-33.18. A combined order could delay the LiteVNA, of which only 5 are left.
    - **Sources:**
      - https://www.passion-radio.com/sma/sma-attenuator-826.html
      - https://www.minicircuits.com/WebStore/dashboard.html?model=VAT-30W2%2B
      - https://www.minicircuits.com/pdfs/VAT-30W2+.pdf
  2.
    - **Claim in stack:** LiteVNA 64 DR (stage 2: prefer HW >=v0.4.5 for about 80 dB above 3 GHz; use CAL > POWER ATTENUATION for LNA tests)
    - **Finding:** The guide's DR table is per hardware revision, not per model. Passion Radio lists HW 3.1 (90/50 dB). Lab401's text is stale (>70/>50 dB, 1300 mAh) yet claims 'guaranteed latest hardware'. No vendor page shows a LiteVNA 64 with HW >=v0.4.5, so that revision may exist only on the 7-inch LiteVNA 67 (unverified). The guide labels the POWER ATTENUATION menu 'Power Settings (7-inch liteVNA only)'. The binary protocol does expose registers 0x41 LowFrequencyPower (MS5351) and 0x42 HighFrequencyPower (MAX2871), each with levels 1-3 (default 1 and 3).
    - **Verdict:** corrected
    - **Action:** Spec the LiteVNA at 90 dB below 3 GHz and 50 dB at 3 GHz and above (S11 floor -50/-40 dB) unless the vendor confirms the revision in writing. Ask Passion Radio and Lab401 for the HW revision before ordering; read CONFIG > VERSION on arrival. For LNA tests use external pads: total pad >= LNA gain + 3 dB, split input/output. Optionally set register 0x42 to 0x01 from labd or scikit-rf. Do not plan on POWER ATTENUATION.
    - **Impact:** Rejection and isolation claims above 3 GHz stay limited to about 45 dB. Removes a menu step that does not exist on the 64.
    - **Sources:**
      - http://nanovna.com/wp-content/uploads/2021/11/LiteVNA_User-Guide.pdf
      - https://www.passion-radio.com/analyzer-spectrum/lite-vna64-2730.html
      - https://lab401.com/products/litevna
  3.
    - **Claim in stack:** LiteVNA price discount is temporary (stage 1); budget option Lab401 $215.83 (EUR 192)
    - **Finding:** The Passion Radio specific price has no end date (from/to 0000-00-00), though it can still be withdrawn at any time. Lab401 lists EUR 192.00, 'In Stock (EU, US)', vendor field 'DeepElec', SKU ZEENKO-LITEVNA. The site has an ex/inc VAT toggle, so the VAT basis of EUR 192 is unverified. For a European buyer the like-for-like gap is $210.88 (Passion Radio incl.) vs $215.83, i.e. about $5, not $40.
    - **Verdict:** corrected
    - **Action:** Compare incl. VAT for an EU buyer. If Lab401 confirms a newer HW revision in writing, the extra cost is about $5; otherwise buy from Passion Radio now.
    - **Impact:** Wording and a better-informed vendor choice.
    - **Sources:**
      - https://www.passion-radio.com/analyzer-spectrum/lite-vna64-2730.html
      - https://lab401.com/search/suggest.json?q=litevna
      - https://lab401.com/products/litevna
  4.
    - **Claim in stack:** Clone rule: tinySA and LiteVNA only from tinySA.org sellers or Passion Radio; reject unconfirmed AliExpress 'Zeenko'
    - **Finding:** The tinySA.org list covers tinySA only. It names the Zeenko AliExpress store as the factory store, plus Aursinc and SeeSii on Amazon, which stage 1 omitted. Passion Radio's GPSR block names WUYI ZEENKO as manufacturer.
    - **Verdict:** corrected
    - **Action:** Reword: tinySA only from sellers on tinySA.org Buying (incl. the Zeenko AliExpress factory store linked from it). LiteVNA from Passion Radio, Lab401 or that same Zeenko factory store. Reject other 'Zeenko'-named listings, Banggood, TinyRFEquip and TinyRFLab.
    - **Impact:** Wording only.
    - **Sources:**
      - https://tinysa.org/wiki/pmwiki.php?n=Main.Buying
      - https://www.passion-radio.com/analyzer-spectrum/lite-vna64-2730.html
  5.
    - **Claim in stack:** tinySA Ultra+: input up to +6 dBm and +/-5 V DC; DANL -102 dBm at RBW 30 kHz; sine -115...-19 dBm +/-2 dB to 800 MHz; channel power +/-2 dB as the reference power meter
    - **Finding:** +6 dBm is the absolute maximum at 0 dB attenuation. The suggested maximum is 0 dBm in auto attenuation, best below -25 dBm. Input impedance is 50 Ohm only with >=10 dB internal attenuation; the LNA disables the attenuator. -102 dBm is the lowest discernible signal at 30 MHz. Generator +/-2 dB holds only from -72 to -19 dBm. Linearity is +/-2 dB below 5.3 GHz and +/-5 dB from 5.3 to 6 GHz; nothing is specified for 6-7.3 GHz.
    - **Verdict:** corrected
    - **Action:** Rewrite the spec row as in corrected_spec. For power-meter and ENR use, set attenuation >=10 dB or put a >=10 dB external pad in front. Use LNA mode only behind a >=20 dB pad. Claim +/-2 dB only below 5.3 GHz. Never treat a generator setting below -72 dBm as calibrated; P10 (-40 dBm plus VNA-measured pads) stays.
    - **Impact:** Prevents mismatch-biased levels and ENR values, and over-claimed accuracy at 5.8 GHz.
    - **Sources:**
      - https://tinysa.org/wiki/pmwiki.php?n=TinySA4.Specification
      - https://tinysa.org/wiki/pmwiki.php?n=TinySA4.Limitations
  6.
    - **Claim in stack:** labd tinySA driver refuses generator/output commands outside Bench (stages 1-2: default-deny, block usbdisk/fwupdate, pin firmware v1.4-252)
    - **Finding:** v1.4-252-g2b4aa51 is the only binary offered. It adds composite USB, 'usbdisk', 'fwupdate' and 'capture rle', and fixes two serial hangs. The 'channel [1-3]' command dates from v1.4223.
    - **Verdict:** confirmed
    - **Action:** Ship firmware v1.4-252-g2b4aa51 and record the git-describe string. Fallback is v1.4241 (Sep 2026: has the March hang fix, no composite device), kept in the aptly mirror if the old/ folder still holds it. The labd allow-list default-denies generator, output, usbdisk, fwupdate, reset dfu and correction writes. udev matches VID:PID plus interface 00 for the CDC port, and udisks ignores the disk interface.
    - **Impact:** Deterministic serial behaviour; no new command paths.
    - **Sources:**
      - http://athome.kaashoek.com/tinySA4/DFU/
      - http://athome.kaashoek.com/tinySA4/DFU/changelog.txt
  7.
    - **Claim in stack:** QtTinySA with PySide6 6.12 aarch64 wheels (stage 1: try the prebuilt QtTinySA_arm64_2404.zip first; stage 2: noble glibc 2.39 makes it fine)
    - **Finding:** The QtTinySA wiki says the arm64 executable was compiled with Nuitka on PiOS 13 Trixie (glibc 2.41). The v1.2.2 notes say it 'runs ONLY on the latest PiOS Trixie (or probably Ubuntu 24.04 on the Pi - not tested)'. The 3D view does not work. Issue #126 (closed 3 May 2026): a Bookworm user got 'GLIBC_2.38 not found'; the maintainer says the PySide6 version needs Trixie. Upstream requirements pin pyside6==6.11.0, whose manylinux_2_39 wheel matches noble exactly.
    - **Verdict:** corrected
    - **Action:** Primary path: a venv with pyside6==6.11.0, pyqtgraph, numpy, pyserial, platformdirs (current) and Pillow. Use the prebuilt zip only after 'objdump -T' shows no GLIBC_2.40/2.41 symbols. The qsqlite driver ships inside the PySide6 wheel (check PySide6/Qt/plugins/sqldrivers); apt libqt6sql6-sqlite (6.4.2) matters only for a system-Qt install. Keep 3D off and use one tinySA per instance. labd ignores QtTinySA's non-zero exit on close.
    - **Impact:** Avoids a binary that may not start on noble.
    - **Sources:**
      - https://raw.githubusercontent.com/wiki/g4ixt/QtTinySA/1.-Installation-and-Dependencies.md
      - https://github.com/g4ixt/QtTinySA/releases/tag/v1.2.2
      - https://github.com/g4ixt/QtTinySA/releases/expanded_assets/v2.0.1
      - https://github.com/g4ixt/QtTinySA/issues/126
      - https://raw.githubusercontent.com/g4ixt/QtTinySA/main/src/requirements.txt
      - https://pypi.org/pypi/PySide6/json
  8.
    - **Claim in stack:** QtTinySA opens instruments directly (stage 2: it can silently change the level calibration; unplug the LiteVNA)
    - **Finding:** Correction tables are written only through an explicit upload dialog (upload_correction sends 'correction <mode> <entry> <freq> <dB>'), so the change is not silent. The probe matches 04b4:0008, which is the LiteVNA's VID:PID. If the LiteVNA's USB product string is not a known name, devices[i] stays None and .test() raises AttributeError. If the string is 'CDC-ACM Demo', QtTinySA opens it as an experimental text-protocol NanoVNA and sends 'version', 'info', 'SN' and 'scan ...'. In the binary V2 protocol a space (0x20) is the WRITE opcode, so that text could write registers (model; product string unverified).
    - **Verdict:** corrected
    - **Action:** labd owns /dev/lab/litevna (udev OWNER=labd, MODE=0600) and only exposes it through its Bench TCP proxy, so QtTinySA cannot open it. Otherwise unplug the LiteVNA while QtTinySA runs. Keep the read-back of correction tables against the stored baseline after each QtTinySA session.
    - **Impact:** Prevents a GUI crash, or stray register writes to the VNA, from the tinySA GUI.
    - **Sources:**
      - https://raw.githubusercontent.com/g4ixt/QtTinySA/main/src/modules/devices.py
      - https://raw.githubusercontent.com/g4ixt/QtTinySA/main/src/QtTinySA.py
      - https://raw.githubusercontent.com/NanoVNA-Saver/nanovna-saver/main/src/NanoVNASaver/Hardware/Hardware.py
      - http://nanovna.com/wp-content/uploads/2021/11/LiteVNA_User-Guide.pdf
  9.
    - **Claim in stack:** NanoVNA-Saver main via pipx (numpy~=2.1, scipy~=1.14); stage 2: pin at or after 4852068, three LiteVNA64 bugs open (#796, #791, #841)
    - **Finding:** The newest main commit is 3445a0a (18 Apr 2026), after 4852068 'Add TCP/IP support' and 2b872a4 socat notes. #796 and #791 are LiteVNA64 reports and still open. #841 (0.7.3, Windows) names no device and its body is an unfilled template, so it is not evidence against the LiteVNA. pyside6~=6.8 would resolve to 6.12.0.
    - **Verdict:** corrected
    - **Action:** pipx install git+https://github.com/NanoVNA-Saver/nanovna-saver@3445a0a with a constraints file pinning PySide6==6.11.2 (or the version tested). Keep the bring-up checks (repeated sweeps, raw O/S/L differ, firmware read on the device). Drop #841 from the risk list.
    - **Impact:** Reproducible install; accurate risk list.
    - **Sources:**
      - https://github.com/NanoVNA-Saver/nanovna-saver/commits/main
      - https://github.com/NanoVNA-Saver/nanovna-saver/issues/796
      - https://github.com/NanoVNA-Saver/nanovna-saver/issues/791
      - https://github.com/NanoVNA-Saver/nanovna-saver/issues/841
      - https://raw.githubusercontent.com/NanoVNA-Saver/nanovna-saver/main/pyproject.toml
      - https://pypi.org/pypi/nanovna-saver/json
  10.
    - **Claim in stack:** VNA control via NanoVNA-Saver only (stage 2 new option: scikit-rf path)
    - **Finding:** scikit-rf's NanoVNAv2 driver names the LiteVNA. scikit-rf 2.2.0 was uploaded on 2026-10-18 (today); 2.1.0 is from 2026-08-13. The 'visa' extra pulls PyVISA>=1.12 and pyvisa-py>=0.6 (current 1.16.2 and 0.8.1).
    - **Verdict:** new_option
    - **Action:** Lab venv: scikit-rf[visa]==2.1.0, pyvisa-py 0.8.1. Do SOL calibration in Python with offset-delay standards for the F-F adapter; Touchstone files go to parts.yaml. Move to 2.2.x only after a test.
    - **Impact:** A scripted fallback that does not depend on Saver's serial bug and handles the female plane properly.
    - **Sources:**
      - https://raw.githubusercontent.com/scikit-rf/scikit-rf/master/skrf/vi/vna/nanovna/nanovna.py
      - https://pypi.org/pypi/scikit-rf/json
  11.
    - **Claim in stack:** Female OSL = kit's male OSL + F-F adapter ($0) (stage 1: define the adapter delay)
    - **Finding:** The method is right. Model: a 16-20 mm PTFE barrel is about 77-97 ps one way, i.e. 95-118 degrees of round-trip phase at 1.7 GHz and 323-403 degrees at 5.8 GHz if left undefined.
    - **Verdict:** confirmed
    - **Action:** Measure the barrel's delay once (port extension on a known open). Enter it as the offset delay of the adapted O/S/L in Saver's calibration-kit settings or in scikit-rf, and record the reference plane in parts.yaml.
    - **Impact:** Correct phase, TDR and Smith data above about 1 GHz.
    - **Sources:**
      - https://www.passion-radio.com/analyzer-spectrum/lite-vna64-2730.html
  12.
    - **Claim in stack:** Noise source ENR table at stabilized 12 V (N8DMT); stage 2: the 26.9 vs 20.5 dB gap is explained by the 10 dB pad (28 dB gain + pad = 20.9 dB)
    - **Finding:** 28 dB is the 15 V gain. The datasheet's typical gain at 12 V is 24.3-24.9 dB. Model: ENR about G+NF = 27.2-27.9 dB unpadded and 17.2-17.9 dB with the 10 dB pad, against N8DMT's measured 20.5 dB (and 'closer to 30' unpadded). That leaves about 3 dB unexplained (tinySA +/-2 dB, unit spread, the open-ended 5 dB input pad). Model sensitivity: about 1.2 dB/V of supply (gain 24.5 dB at 12 V vs 28.1 dB at 15 V).
    - **Verdict:** corrected
    - **Action:** Build it as N8DMT did: 50 Ohm load (or 5 dB pad) on the input and a permanent 10 dB output pad, never an open output. Use a regulated 12.00 V +/-0.05 V. Measure your own ENR with the tinySA NF routine (EXT GAIN = 0, tinySA attenuation >=10 dB or an extra pad) from 28 to 2400 MHz, and repeat at 11.5 and 12.5 V to get the real slope. Never use the N8DMT numbers as ENR.
    - **Impact:** Avoids an ENR error of up to about 3 dB (or about 10 dB without the pad) in every Y-factor NF.
    - **Sources:**
      - https://qsl.net/n8dmt/test-page/diy-test-equipment/low-cost-diy-noise-source/index.html
      - https://www.minicircuits.com/pdfs/ZFL-500LN+.pdf
      - https://www.minicircuits.com/WebStore/dashboard.html?model=ZFL-500LN%2B
  13.
    - **Claim in stack:** E-field probes: home-made semi-rigid pieces; one 086-6SM+ is cut into probes
    - **Finding:** The 086-6SM+ is a Hand-Flex cable (copper-clad steel centre, tin-soaked copper braid), sold as a replacement for 0.086in semi-rigid. It has SMA male on both ends, so one cable yields 2 stub probes. Mini-Circuits specifies 8 in-lb max with the anti-torque nut braced.
    - **Verdict:** corrected
    - **Action:** Wording: '086 Hand-Flex stub monopoles, 2 per cable; open-ended stub only, never a loop at the tip'. Brace the anti-torque nut when tightening.
    - **Impact:** Wording; E-field-only rule kept.
    - **Sources:**
      - https://www.minicircuits.com/pdfs/086-6SM+.pdf
  14.
    - **Claim in stack:** Capability: LA 8/16 channels 24 MHz
    - **Finding:** The 6022BE has 0 logic channels. A generic FX2 board gives 8 channels on PB0-PB7 at a 24 MHz rate, which is 24 MB/s over USB.
    - **Verdict:** corrected
    - **Action:** 'LA 8 channels, up to 24 MS/s (generic CY7C68013A, fx2lafw 0.1.7)'. 16 channels only with a 16-bit FX2 board.
    - **Impact:** Capability list corrected.
    - **Sources:**
      - https://sigrok.org/wiki/Fx2lafw
      - https://sigrok.org/wiki/Hantek_6022BE
  15.
    - **Claim in stack:** Bench USB: scope/LA on the LAB port behind CH334F and FE1.1s; tree limit 25 MB/s
    - **Finding:** OpenHantek streams 30 MB/s at its maximum (30 MS/s CH1 8-bit, or 15 MS/s x2 16-bit). Model: 30 + RTL-B 5.12 + HF+ 3.07 = 38.2 MB/s, above the 25 MB/s budget and at the practical USB2 ceiling. An LA at 24 MS/s is another 24 MB/s.
    - **Verdict:** confirmed
    - **Action:** Bench profile in labd:
  - scope above 5 MS/s or LA above 12 MS/s only with RTL-B and HF+ streams paused;
  - otherwise cap the scope at 5 MS/s with 2 channels (10 MB/s) and the LA at 12 MS/s;
  - never run the scope and the LA at high rates together.
    - **Impact:** Prevents sample drops on RTL-B/HF+ and scope overruns.
    - **Sources:**
      - https://raw.githubusercontent.com/OpenHantek/OpenHantek6022/main/docs/limitations.md
  16.
    - **Claim in stack:** Bench hub: Waveshare 'MTT' hub powered from the bank (stage 1: if single-TT, never run two FS isochronous instruments)
    - **Finding:** The Pi Hut text says both STT and MTT, and gives 'USB Output 5V@1.2A' without saying whether that is per port or total. The supplied PSU is 5 V 2 A. None of the lab instruments is isochronous: tinySA, LiteVNA, Debug Probe and Pico are CDC bulk; FNB58 and LBE-1420 are HID interrupt; Hantek and FX2 are high-speed bulk and use no TT. So STT only shares 12 Mbit/s among the full-speed devices (model).
    - **Verdict:** corrected
    - **Action:** Keep the part. Check bDeviceProtocol with lsusb -v (1 = single TT, 2 = multi-TT); STT is acceptable for this instrument set. Budget power: charge the instruments before bench sessions and never charge the LiteVNA (up to 1 A) and the tinySA through the hub at once. Measure each draw with the FNB58 and feed the hub from the bank's 5 V/3 A. Add no further hub tier: Q6A, FE1.1s, CH334F, this hub (possibly 2 internal tiers) is already close to the 5-hub limit.
    - **Impact:** Avoids brownouts on the bench hub; the STT question becomes minor.
    - **Sources:**
      - https://thepihut.com/products/industrial-grade-dual-host-usb-hub-4x-usb-2-0
      - http://nanovna.com/wp-content/uploads/2021/11/LiteVNA_User-Guide.pdf
      - https://tinysa.org/wiki/pmwiki.php?n=TinySA4.Specification
  17.
    - **Claim in stack:** Pinecil V2 from the 20 V PD bank (about 64 W); stage 2: PD Mode No Dynamic plus a 100 W cable
    - **Finding:** IronOS Pinecilv2 configuration.h sets USB_PD_VMAX 28, POW_EPR 1 and USB_PD_EPR_WATTAGE 140. The 'safe' default only drops padding resistance and does not disable EPR. PINE64 rates USB-C input at 12-20 V 3 A. 64 W (20 V into about 6.25 Ohm) is a model and would draw 3.2 A, above PINE64's 3 A.
    - **Verdict:** corrected
    - **Action:** On first boot: Bluetooth Off, PD Mode = No Dynamic, Power limit = 60 W, and Power pulse on if the 737 sleeps. Use a non-EPR USB-C cable (3 A, or 5 A 100 W). Record the IronOS version (>=2.23). Expect 60 W, not 64 W.
    - **Impact:** Keeps the iron within the maker's input rating and off 28 V EPR from the field bank.
    - **Sources:**
      - https://raw.githubusercontent.com/Ralim/IronOS/dev/source/Core/BSP/Pinecilv2/configuration.h
      - https://raw.githubusercontent.com/Ralim/IronOS/dev/Documentation/Settings.md
      - https://github.com/Ralim/IronOS/releases
      - https://pine64.com/product/pinecil-smart-mini-portable-soldering-iron/
  18.
    - **Claim in stack:** Balance charger ISDT 608PD $32.99-42.99 (unverified)
    - **Finding:** DarwinFPV official store: $49.99, available, 0-40 C operating. ISDT advertises phone-app control (ISD Link) and OTA, link type unstated. PC firmware updates use 'ISD Go for Windows V2.0.0.2' (2025-12-08), not an 'ISD Link PC' tool as stage 2 named it.
    - **Verdict:** corrected
    - **Action:** Price $49.99. Treat it as a possible BLE emitter: charge only at home with the receiver off, and settle the question with the tinySA 2.4 GHz receive-only scan. Update firmware only over USB with ISD Go (Windows), never the phone app. Do not use its 100 W USB-C output as a lab supply.
    - **Impact:** Core total +$7 to +$17.
    - **Sources:**
      - https://darwinfpv.com/products/isdt-608pd-lipo-charger-dc-240w-10a-usb-c-140w-5a-smart-digital-charger
      - https://www.isdt.co/608pd.html
  19.
    - **Claim in stack:** USB tester FNB58 Std + baryluk logger (stage 2: V0.68 freeze, workaround unclear)
    - **Finding:** Issue #19: the reporter says setting refresh = 0.003 for the FNB58 (line 304 of fnirsi_logger.py) fixes the V0.68 freeze. The README says firmware updates require Windows; the drain-on-exit fix is merged.
    - **Verdict:** corrected
    - **Action:** Patched logger: refresh 0.003 for the FNB58, no dev.reset(), drain on exit. Record the FNB58 firmware on arrival and do not update it, since updates need Windows anyway. labd reports 'meter stalled - power-cycle FNB58'.
    - **Impact:** Reliable long power logs.
    - **Sources:**
      - https://github.com/baryluk/fnirsi-usb-power-data-logger/issues/19
      - https://raw.githubusercontent.com/baryluk/fnirsi-usb-power-data-logger/master/README.md
  20.
    - **Claim in stack:** lbgpsdo with python hid and udev rule for the LBE-1420
    - **Finding:** lbgpsdo still does not detect the 1420 (0x2443). bvernoux/lbe-142x v1.2 (20 Apr 2026) supports it, tested on Ubuntu 24.04 x64 only. Bodnar says a Linux CLI exists on GitHub and that settings persist in the device.
    - **Verdict:** corrected
    - **Action:** Build bvernoux/lbe-142x on arm64 (cmake, libudev-dev) and pin the commit; simontheu/lbe-1420 is the fallback. udev: hidraw 1dd2:2443, group plugdev. Limit --f1 to 1.1 GHz. Configure once and run without USB control.
    - **Impact:** The stack's tool would otherwise not see the LBE-1420.
    - **Sources:**
      - https://raw.githubusercontent.com/bvernoux/lbe-142x/main/README.md
      - https://raw.githubusercontent.com/simontheu/lbe-1420/main/README.md
      - https://raw.githubusercontent.com/hamarituc/lbgpsdo/master/lbe142x.py
      - https://www.leobodnar.com/shop/index.php?main_page=product_info&cPath=107&products_id=393
  21.
    - **Claim in stack:** Spare LNA: RTL-SDR Blog Wideband LNA V2, 90 mA
    - **Finding:** The vendor page gives QPL9547, 100 MHz-6 GHz, NF <1 dB, 3-5 V bias tee, and no current. The Qorvo page returned HTTP 429 again, so the current is unverified.
    - **Verdict:** unverified
    - **Action:** Mark the 90 mA as unverified (V1-derived). Measure at 4.5 V with the FNB58 or DPS-150 before enabling the spare V4L tee (<=90 mA rule).
    - **Impact:** Bias budget for C9 still open.
    - **Sources:**
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
  22.
    - **Claim in stack:** Bench supply FNIRSI DPS-150 $73-75
    - **Finding:** Elektor lists EUR 59.00 incl. VAT (about $66.32), fulfilled by Eleshop ('prices may vary'); stock not stated. The Eleshop page itself was not readable (HTTP 403).
    - **Verdict:** corrected
    - **Action:** Price about $66 (model, at the Elektor list price); extended total about -$7 to -$9. Check turn-on overshoot with the Hantek before connecting an LNA or LNB.
    - **Impact:** Slightly cheaper.
    - **Sources:**
      - https://www.elektor.com/products/fnirsi-dps150-dc-power-supply-150-w
  23.
    - **Claim in stack:** SMA 0.9 N·m torque wrench (TOJOIN eBay + RTL-SDR Blog), $50.84-62.84
    - **Finding:** No listing could be fetched (WebSearch budget exhausted). Mini-Circuits specifies 8 in-lb (0.9 N·m) maximum with a 5/16in wrench for its stainless SMA parts. The torque for the instruments' own SMA jacks, which may be brass, was not verified.
    - **Verdict:** unverified
    - **Action:** Before buying, confirm the listing says 0.9 N·m (8 in-lb) with a 5/16in (8 mm) head. Ask Zeenko for the recommended torque on the LiteVNA and tinySA ports; until then tighten them by hand plus the wrench's lowest click, or use a 0.56 N·m wrench if one is available (unverified practice).
    - **Impact:** Small cost and connector-wear risk.
    - **Sources:**
      - https://www.minicircuits.com/pdfs/086-6SM+.pdf
- **New risks:**
  - The Passion Radio 30 dB pad variant is out of stock (quantity -6, 'available within 1 month'). Ordering it with the 'last items' LiteVNA can hold up the VNA shipment.
  - There is no proof that any LiteVNA 64 ships with HW >=v0.4.5. Expect 50 dB DR above 3 GHz, and an S11 floor of -40 dB, from the Passion Radio HW 3.1 unit.
  - QtTinySA's VID:PID probe includes 04b4:0008 (the LiteVNA). Depending on the LiteVNA's product string, QtTinySA either raises AttributeError or opens it as a text-protocol NanoVNA and sends ASCII, in which a space (0x20) is the V2 WRITE opcode. Mitigate with labd-exclusive udev permissions on /dev/lab/litevna.
  - The QtTinySA arm64 Nuitka zip was built on PiOS 13 Trixie (glibc 2.41) and is untested on Ubuntu 24.04. It may fail on noble's glibc 2.39.
  - Pinecil V2 IronOS supports 28 V EPR up to 140 W, while PINE64 rates USB-C input at 12-20 V 3 A. Set No Dynamic and a 60 W power limit, and use a non-EPR cable.
  - Bench hub: 'USB Output 5V@1.2A' (per port vs total not stated) and a 5 V 2 A PSU. A charging LiteVNA (up to 1 A) plus a charging tinySA plus the Hantek can exceed it.
  - The tinySA is 50 Ohm only with >=10 dB internal attenuation, and LNA mode disables the attenuator. Power-meter and ENR readings at 0 dB attenuation carry mismatch error.
  - Noise-source ENR depends on supply voltage at about 1.2 dB/V (model from datasheet gain at 12 V and 15 V), so the 12 V rail must be regulated and logged with every Y-factor run.
  - A residual of about 3 dB between the datasheet ENR model (17.5 dB with the 10 dB pad at 12 V) and N8DMT's 20.5 dB means the published table can be off by several dB for another unit.
  - scikit-rf 2.2.0 was released today (2026-10-18); pin 2.1.0 until it has been tested.
  - FNB58 firmware can only be updated from Windows (logger README). A unit shipped on V0.68 needs the refresh = 0.003 logger patch.
  - The OpenHantek arm64 .deb is built in CI; the author tests only the amd64 .deb he builds locally. No Q6A or Adreno report exists.
  - USB tier depth: Q6A root, FE1.1s, CH334F, Waveshare hub (possibly 2 internal hub chips), then the instrument. This is near the USB 2.0 5-hub limit, so no further hub may be added.
  - The bench-hub USB load and the TPS2553 0.75 A LAB limit remain models until measured; the LiteVNA alone is specified at up to 1 A.
- **Refuted findings:**
  1.
    - **Finding:** Stage 1: the two 30 dB pads are Passion Radio's 'RF attenuator SMA 0-6 GHz' at EUR 13.20 incl. VAT = $14.84, in stock; accessories total $212.68 exact.
    - **Why:** EUR 13.20 is the -3 dB base variant. The -30 dB combination adds EUR 4.17 ex VAT (EUR 18.20 incl. = $20.46) and shows quantity -6 / 'available within 1 month'.
  2.
    - **Finding:** Stage 1: the LiteVNA price is a temporary discount.
    - **Why:** The Passion Radio specific price has no end date (from/to 0000-00-00). It can be withdrawn at any time, but it is not dated as temporary.
  3.
    - **Finding:** Stage 1: QtTinySA_arm64_2404.zip is a prebuilt Ubuntu 24.04 arm64 binary to try first. Stage 2: issue #126 shows that noble's glibc 2.39 makes it fine.
    - **Why:** The wiki says it was compiled with Nuitka on PiOS 13 Trixie. The release notes say it runs ONLY on PiOS Trixie, with Ubuntu 24.04 'probably... not tested'. #126 only proves that Bookworm (glibc 2.36) fails, not that 2.39 is enough.
  4.
    - **Finding:** Stage 2: on the LiteVNA 64, use CAL > POWER ATTENUATION (up to 31.5 dB) and recalibrate for LNA tests.
    - **Why:** The LiteVNA guide heads that section 'Power Settings (7-inch liteVNA only)'. Only the register-level source power (0x41/0x42, levels 1-3) applies to the 64.
  5.
    - **Finding:** Stage 2: prefer a LiteVNA 64 with HW >=v0.4.5 (about 80 dB above 3 GHz); the stack understates the LiteVNA by 30 dB.
    - **Why:** The guide's DR table is per hardware revision, not per model, and no vendor page shows a LiteVNA 64 at v0.4.5. The unit actually on offer is HW 3.1 at 90/50 dB, so the stack's 50 dB figure is correct for what can be bought.
  6.
    - **Finding:** Stage 2: NanoVNA-Saver #841 is one of three open LiteVNA64-related bugs.
    - **Why:** #841 names no VNA model and its behaviour and reproduction sections are unfilled template text.
  7.
    - **Finding:** Stage 2: the 10 dB output pad fully explains the stage-1 ENR mismatch (gain 28 dB + pad gives 20.9 dB).
    - **Why:** 28 dB is the datasheet gain at 15 V. At N8DMT's 12 V the typical gain is 24.3-24.9 dB, so the padded model gives about 17.5 dB, 3 dB under the measured 20.5 dB. The pad explains about 10 dB, not all of the gap.
  8.
    - **Finding:** Stage 2: for FNB58 issue #19 'the exact change is unclear'.
    - **Why:** The reporter states that setting refresh to 0.003 for the FNB58 (line 304) fixes the freeze.
  9.
    - **Finding:** Stage 2: QtTinySA can silently change the tinySA level calibration.
    - **Why:** Correction tables are written only through the explicit upload_correction dialog action. Reading back the tables is still prudent, but nothing happens silently.
  10.
    - **Finding:** Stage 1: with a single-TT hub, never run two full-speed/isochronous instruments at once.
    - **Why:** None of the lab instruments uses isochronous transfers: they are CDC bulk, HID interrupt, or high-speed bulk that needs no TT. STT only shares 12 Mbit/s among low-rate full-speed devices (model).
  11.
    - **Finding:** Stage 2: 'ISD Link PC software V2.0.0.2' updates the 608PD.
    - **Why:** ISDT's page lists 'ISD Go for Windows V2.0.0.2' (2025-12-08) as the PC updater that supports the 608PD; ISD Link is the phone app.
  12.
    - **Finding:** Stage 2: in P3, keep port 2 at or below 0 dBm by adding an LNA output pad.
    - **Why:** If the total attenuation is at least the LNA gain, port 2 receives no more than during the thru calibration, which is within its range by design. An output pad is optional for match; it is required only if pad < gain.
- **Corrected spec:** LAB INSTRUMENTS - corrected spec (18 Oct 2026). Prices in USD at the stack's 1.1241 USD/EUR and 1.3318 USD/GBP. 'model' = my calculation.
  
  RULES (unchanged, enforced)
  - Every source is conducted-only, into a cable, pad, filter, LNA or load: LiteVNA port 1, tinySA generator, ZFL noise source, LBE-1420.
  - No S11 sweeps on antennas. The SWR/S11 page is Bench-only after the 1.5 s 'antenna disconnected' hold.
  - E-field stub probes only; no loop or H-field probes.
  - Levels into receive chains: <=-40 dBm; >=30 dB of pad above 800 MHz; 80 dB plus a DC block for the GPSDO tone.
  
  CORE
  1. VNA: LiteVNA 64 (Zeenko), Passion Radio SKU NANO-LITEVNA64-2730.
     - Price: EUR 156.33 ex / EUR 187.60 incl. VAT ($175.73 / $210.88). 5 left; the discount has no end date. Alternative: Lab401 EUR 192 (VAT basis unverified).
     - Plan on HW 3.1: 50 kHz-6.3 GHz; DR >90 dB below 3 GHz and >50 dB at 3 GHz and above; S11 floor -50/-40 dB. Ask the vendor for the revision; read CONFIG > VERSION on arrival.
     - Supply 5 V, 1 A max; 2000 mAh; store it charged (the protection state needs charging while off).
     - USB 04b4:0008, binary V2 protocol; device sweep 21-1001 points, USB 1-65535.
     - Kit: male O/S/L, F-F barrel, 2x 30 cm M-M cables. Female standards = male O/S/L + F-F barrel, with the barrel delay measured and entered as offset delay (model: 77-97 ps).
     - LNA tests: total pad >= gain + 3 dB, split between input and output. Optional: register 0x42 = 0x01. POWER ATTENUATION does not exist on the 64.
     - Do not claim rejection or isolation deeper than about 45 dB above 3 GHz; use the tinySA plus noise source for those.
  2. Spectrum analyser: tinySA Ultra+ ZS407 from a tinySA.org-listed seller.
     - Price: Astroradio EUR 219.89 incl. VAT ($247.18; ex-VAT basis $204.28); EUR 215.50 by bank transfer.
     - Normal mode 100 kHz-900 MHz; ULTRA to 7.3 GHz.
     - Input: abs max +6 dBm at 0 dB attenuation; +20 dBm short-term peak at 30 dB; suggested max 0 dBm (auto attenuation); best below -25 dBm; +/-5 V DC max; P1dB -1 dBm; IIP3 +15 dBm. 50 Ohm only with >=10 dB attenuation.
     - LDS -102 dBm (30 MHz, RBW 30 kHz, no LNA). LNA (NF 5 dB to 6 GHz) only behind a >=20 dB pad.
     - Accuracy: +/-2 dB absolute after calibration; linearity +/-2 dB below 5.3 GHz and +/-5 dB from 5.3 to 6 GHz; 6-7.3 GHz uncharacterised.
     - Generator: -115 to -19 dBm in 1 dB steps, but +/-2 dB only from -72 to -19 dBm up to 800 MHz. Use -40 dBm plus VNA-measured pads for calibrated levels.
     - Power meter: channel power via 'channel [1-3]', with attenuation >=10 dB.
     - Battery >=3 h; charging <=1 h at >=500 mA.
     - Self-interference: the 48 MHz MCU and its harmonics (144.000 and 432.000 MHz, model) go into the D10 A/B matrix.
     - Firmware: tinySA4_v1.4-252-g2b4aa51 (composite CDC + disk). Fallback v1.4241.
  3. Noise source: ZFL-500LN+ ($116.81) or ZFL-500+ ($99.55) plus enclosure, $104.55-126.81.
     - Input: 50 Ohm load or 5 dB pad. Output: permanent 10 dB pad; never open.
     - Supply: regulated 12.00 V +/-0.05 V from AUX12 (+17 V max); BENCH only; budget 0.15 A until measured.
     - ENR: your own table from the tinySA NF routine (EXT GAIN 0), 28-2400 MHz, logged with the supply voltage. Model: about 17-18 dB padded; N8DMT's 20.5 dB is a sanity reference only. No Y-factor above 2.4 GHz.
  4. RF accessories:
     - Nooelec 100815 kit, $47.95: 1/2/3/6/10/20 dB, 2 W, DC-6 GHz, +/-0.1 dB to 3 GHz.
     - 2x 30 dB: VAT-30W2+ $31.43 each (preferred, in stock, 30+/-0.3 dB), or Passion Radio 30 dB $20.46 each on backorder.
     - 2x BLK-89-S+ $20.26; 3x ANNE-50+ $14.84 (RL >=30 dB to 4 GHz); 3x 086-6SM+ $16.67 (Hand-Flex; one cut into 2 E-field stubs).
     - Line total: $245.86 with VAT-30W2+, or $223.92 with Passion Radio pads.
  5. Torque wrench and adapters $50.84-62.84 (unverified): 0.9 N·m (8 in-lb), 5/16in head. Torque for the instruments' own ports is to be confirmed with Zeenko.
  6. Spare LNA: RTL-SDR Blog Wideband LNA V2, $19.95, QPL9547, 3-5 V. Current unverified; measure before using the <=90 mA V4L tee.
  7. FNIRSI FNB58 Std (SKU FNB58, no BT), $53.99. baryluk logger patched (refresh 0.003, no reset, drain on exit); record the firmware and do not update.
  8. DMM: ANENG AN8008 (ZT109 PCB), $26-53 (unverified). 99.99 uA range, 10 nA resolution; mA via the 10 A shunt at 0.1 mA resolution; 2x AAA; low-energy bench use only.
  9. Hantek 6022BE: GBP 100 ex / GBP 120 inc VAT, The Debug Store ($133.18 / $159.82). Plus a generic CY7C68013A 8-channel LA; set $141-172.
     - OpenHantek6022 3.4.1-rc2 arm64 .deb (60-openhantek.rules); FW0210; replug after sigrok.
     - PulseView 0.4.2, sigrok-cli 0.7.2, fx2lafw 0.1.7.
     - Capability: 2 ch 20 MHz 8 bit; LA 8 ch at up to 24 MS/s.
  10. Raspberry Pi Debug Probe (Adafruit 5699), $12.00; debugprobe v2.3.1; OpenOCD 0.12.0; picocom 3.1.
  11. Pinecil V2 (PINECIL-BB2), $25.99.
      - IronOS >=2.23: Bluetooth Off, PD Mode = No Dynamic, Power limit 60 W, Power pulse if needed.
      - Non-EPR USB-C cable; about 60 W, not 64 W.
  12. iFixit anti-static mat IF145-202-5, $34.95 (verified).
  13. Anker 737 PowerCore 24K, $109.99: 20 V/5 A and 28 V/5 A PDOs; 86.4 Wh (model); not recalled; carry-on.
  14. Bench hub: Waveshare dual-host 4x USB 2.0 (Pi Hut WAV-21686), GBP 18.50 ($24.64).
      - Fed from the bank's 5 V/3 A; check the TT type with lsusb.
      - Instruments are charged before sessions; no simultaneous LiteVNA + tinySA charging through it; no extra hub tier.
  15. ISDT 608PD, $49.99 (DarwinFPV).
      - 0-40 C; home charging only with the receiver off; possible BLE emitter until the scan proves otherwise.
      - Firmware via ISD Go for Windows only; the USB-C output is not used as a lab supply.
  16. Tools/consumables: $245-400 (model).
  Core total (model): $1,524.76-1,850.07 with VAT-30W2+, or $1,502.82-1,828.13 with Passion Radio pads (was $1,474.58-1,809.89).
  
  EXTENDED
  - GPSDO: Leo Bodnar LBE-1420, GBP 132 ($175.80; VAT basis unstated), in stock.
    - 1 Hz-1.1 GHz; +11 dBm at 10 MHz; 3.3 V CMOS square wave (odd harmonics); USB-C 5 V 250 mA; antenna included.
    - Always behind 80 dB + BLK-89-S+, giving -69 dBm at the DUT (model). Off and disconnected during H1, ADS-B and Inmarsat-C sessions.
    - Tool: bvernoux/lbe-142x v1.2 (pinned commit, arm64 build) with simontheu/lbe-1420 as fallback; hidraw udev 1dd2:2443; --f1 <=1.1 GHz.
  - FNIRSI DPS-150: EUR 59 incl. VAT (about $66.32; Elektor/Eleshop). 0-30 V / 0-5 A / 150 W from a 5-32 V input (20 V PD); dps150tool or the Python library from labd; overshoot test before any LNA or LNB.
  - The other extended items are unchanged. Extended total about $491-699 (model).
  
  SOFTWARE PINS
  - NanoVNA-Saver: pipx from git@3445a0a with a constraints file (PySide6==6.11.2), behind the labd Bench TCP proxy (labd owns /dev/lab/litevna, 0600).
  - scikit-rf[visa]==2.1.0 + pyvisa-py 0.8.1 in the lab venv (scripted P1/P2 with offset-delay standards).
  - QtTinySA v2.0.1 from source: venv pyside6==6.11.0, pyqtgraph, current platformdirs; prebuilt zip only after a GLIBC check; one device per instance; 3D off; read back the correction tables after each session.
  - labd tinySA allow-list: default-deny; generator/output/usbdisk/fwupdate/reset dfu/correction writes blocked outside Bench. udev matches CDC interface 00; udisks ignores the tinySA disk interface; ModemManager is masked.
  - USB Bench profile: scope above 5 MS/s or LA above 12 MS/s only with RTL-B and HF+ paused; never both at high rate.
- **Bench tests:**
  - LiteVNA arrival, inside the return window:
  - read CONFIG > VERSION (HW and FW);
  - isolation test with both ports terminated in ANNE-50+ at the lowest IFBW, 0.05-3 GHz and 3-6.3 GHz; pass if >=90 / >=50 dB;
  - calibrated ANNE-50+ S11 floor;
  - record the OSL gender.
  - Measure the F-F barrel's delay (port extension on the kit open until the phase is flat). Enter it as offset delay, recalibrate at the female plane, and confirm the open shows about 0 degrees +/-10 degrees to 6 GHz.
  - NanoVNA-Saver @3445a0a and scikit-rf 2.1.0 on the Q6A:
  - 20 sweeps each at 1001 and 10,000 points, 50 kHz-6.3 GHz;
  - log the byte counts and confirm there are no short reads (#796);
  - confirm raw O/S/L differ before saving a calibration;
  - test the TCP path through labd's proxy.
  - LiteVNA source power: set register 0x42 to 1, 2 and 3 and 0x41 to 1-3. Measure port-1 output through a 30 dB pad on the tinySA at 10 MHz, 500 MHz, 2 GHz and 5.8 GHz, and record the dBm for each setting.
  - LiteVNA and QtTinySA together: run 'udevadm info' on the LiteVNA to get the product string. With /dev/lab/litevna at labd 0600, start QtTinySA and confirm it neither crashes nor opens the VNA port.
  - tinySA arrival:
  - 'version' string = tinySA4_v1.4-252-g2b4aa51;
  - lsusb -v shows the CDC and MSC interfaces;
  - udev binds interface 00 only, and udisks does not mount the disk;
  - 1 h scripted 'scanraw' plus 'channel' loop with no hang;
  - read back the 'correction' tables as the baseline.
  - tinySA level check: generator at -40 dBm through VNA-measured Nooelec pads into each SDR. Then input-match check: tinySA S11 on the LiteVNA at attenuation 0 dB vs 10 dB, and with LNA on.
  - QtTinySA venv: start it with pyside6==6.11.0; check the PySide6/Qt/plugins/sqldrivers/libqsqlite.so database startup. If the prebuilt zip is considered, run 'objdump -T QtTinySA* | grep -o GLIBC_2\.[0-9]*' and reject it if any symbol is newer than 2.39.
  - Noise source:
  - ENR of your own unit with the 10 dB output pad from 28 to 2400 MHz (tinySA NF routine, EXT GAIN 0, attenuation >=10 dB);
  - repeat at 11.5, 12.0 and 12.5 V to measure the real dB/V slope (model 1.2);
  - hot/cold S22 on the LiteVNA;
  - measure the current at 12 V.
  - Bench hub:
  - lsusb -v bDeviceProtocol (1 = STT, 2 = MTT) and the tier depth with lsusb -t;
  - FNB58 draw of the LiteVNA, tinySA, Hantek and FX2 LA, each idle, sweeping and charging, plus the hub total against its 5 V 2 A / 1.2 A rating;
  - LAB-port draw against the TPS2553 0.75 A limit (P16).
  - USB throughput: 10 min of the Hantek at 30 MS/s CH1 plus RTL-B 2.56 Msps plus HF+ 768 ksps; count SDR drops and scope overruns. Repeat with the capped profile (5 MS/s x2 channels, LA 12 MS/s) and confirm zero drops.
  - OpenHantek 3.4.1-rc2 arm64 under labwc/XWayland on Mesa 25.2.8 freedreno; fallbacks 'OpenHantek -e' and LIBGL_ALWAYS_SOFTWARE=1. Confirm FW0210 after replugging from PulseView.
  - ISDT 608PD radio check: tinySA on its antenna (receive-only), 2400-2485 MHz, RBW 100 kHz, max-hold 5 min. Run it with the charger idle, charging, and with the ISD Link pairing screen open; look for BLE advertising on 2402, 2426 and 2480 MHz.
  - Pinecil:
  - IronOS version >=2.23;
  - Bluetooth Off, PD Mode No Dynamic, Power limit 60 W;
  - FNB58 on the 737 shows 20 V and <=3 A, never 28 V;
  - 30 min idle with Power pulse set so the bank does not sleep.
  - FNB58: record the firmware; 8 h logging run with the patched logger; confirm stall detection.
  - LBE-1420: build bvernoux/lbe-142x on arm64 and run --status; set 10 MHz. Through 80 dB + BLK-89-S+ into the tinySA, expect -69 dBm +/-3 dB (model); record the 30 MHz and 50 MHz harmonic levels.
  - RTL-SDR LNA V2: current at 4.5 V cold and warm, with the DPS-150 and FNB58; pass if <=90 mA, the V4L-tee rule.
  - DPS-150: turn-on overshoot at 13.2 V into a 100 Ohm load, measured on the Hantek at 1 MS/s; pass if <=13.6 V peak.
  - AN8008: check the uA-range reading and burden against the DPS-150 at 10 uA and 90 uA through a known resistor; confirm the PCB is marked ZT109.
- **Confidence:** medium

