# Додаткові дослідження: повні відповіді субагентів

## lab:instruments (run `wf_1dd437c5-0cf`)

- **Area:** Portable RF test and measurement instruments (VNA, spectrum analyzer, noise source, frequency reference, counter, power meter, near-field probes, attenuators, loads) for the receive-only handheld lab built around the Radxa Dragon Q6A, RTL-SDR Blog V4L and LimeSDR Micro M.2
- **Items:**
  1.
    - **Name:** LiteVNA 64 (Zeenko), 50 kHz-6.3 GHz handheld VNA
    - **Category:** Vector network analyzer
    - **Purpose in lab:** Measures S11/S21 of cables, MHF4-SMA pigtails, adapters, SAW and FM-bandstop filters, bias tees, attenuators and powered LNAs from 137 MHz to 2.4 GHz and beyond. TDR/DTF mode locates bad crimps. The input files already rely on 'screen it with a NanoVNA' for the RF1.13 pigtails, LMR-240/RG316 and cheap bias tees, which lose 3-7 dB at 100-200 MHz. This is that instrument.
    - **Key specs:** 50 kHz-6.3 GHz. Dynamic range after calibration above 70 dB below 3 GHz and above 50 dB at 3 GHz and up. S11 noise floor below -50 dB under 3 GHz and below -40 dB above. 0.5 ppm frequency stability (0-50 °C). 21-1024 points on the device, up to 65535 over USB. TDR/DTF by IFFT. microSD for Touchstone files and screenshots. Stimulus output level is not published on the pages I read.
    - **Size weight power:** 140 x 75 x 20 mm (Lab401 listing). Weight not published. 3.95 in 480x320 IPS touchscreen. Internal 2000 mAh Li-ion, charges over USB-C.
    - **Interface and linux:** USB-C serial. NanoVNA-Saver lists LiteVNA as supported. It is Python >=3.10 with PySide6/numpy/scipy, installed with 'pipx install git+https://github.com/NanoVNA-Saver/nanovna-saver' (the DEB/RPM builds are marked broken). Radxa OS r2 (Ubuntu 24.04, Python 3.12) meets the Python requirement. PySide6 arm64 wheels on the Q6A are NOT verified, so test this first. Fallback: run standalone on its own touchscreen and copy .s2p files from the microSD. A PC is not required.
    - **Price:** EUR 144.59 ex VAT at Eleshop (seen only in a search snippet; the page returned 403). 9,990 UAH incl. VAT at Selteq, about $223 at 44.86 UAH/USD. Switch Science JPY 23,800, sold out. AliExpress: buy only from the Zeenko factory store (price not verified).
    - **Tier:** core
    - **Integration notes:** Bench/pouch instrument, not mounted inside the ASA case. Connect it to a Q6A USB 2.0 port only for data. It is low-bandwidth CDC traffic, so the shared FE1.1s hub is fine. Do not leave it connected during satellite passes (USB noise). Its 6.3 GHz ceiling covers every band in the build except the 10 GHz LNB input; measure the LNB at its 739 MHz IF only. Always put an SMA DC block on any line that carries bias-tee (4.5 V) or LNB (13/18 V) power.
    - **Sources:**
      - https://www.zeenko.tech/litevna
      - https://selteq.com.ua/en/litevna-64/
      - https://lab401.com/products/litevna
      - https://eleshop.eu/litevna.html
      - https://github.com/NanoVNA-Saver/nanovna-saver
      - https://raw.githubusercontent.com/NanoVNA-Saver/nanovna-saver/main/docs/INSTALLATION.md
    - **Availability:** Zeenko factory store (AliExpress), Eleshop (EU), Lab401 (EU), Selteq (UA). Switch Science (JP) sold out.
    - **Cheaper alternative:** LiteVNA 62: same 50 kHz-6.3 GHz RF design, smaller battery (1300 mAh) and screen. About EUR 130 ex VAT at Eleshop (search snippet; which model that price belongs to is not confirmed).
    - **Safety notes:** Port 1 is a signal generator. Use it only in conducted tests into cables, filters, attenuators, LNAs or 50-ohm loads. An antenna S11/VSWR sweep makes the antenna radiate the sweep, which breaks the receive-only rule. Do not do it unless local rules explicitly allow low-power test emissions; use the receive-only antenna checks instead. On LNA tests, put a 20-30 dB pad after the LNA so port 2 is not overdriven (the VNA's maximum input is not published on the pages I read).
  2.
    - **Name:** tinySA Ultra+ ZS407 handheld spectrum analyzer with low-level signal generator
    - **Category:** Spectrum analyzer
    - **Purpose in lab:** An independent, level-calibrated analyzer covering 100 kHz-7.3 GHz. It hunts self-interference that the receivers inside the same box cannot measure on themselves: HDMI pixel-clock harmonics, PCIe 100 MHz refclk x17 = 1700 MHz, Lime 30.72 MHz harmonics, buck converters, USB3 near 2.4 GHz. It also surveys sites for overloading signals and acts as the detector for near-field probes. Its built-in noise-figure menu can estimate noise-source ENR and LNA NF, and its generator gives low-level conducted test signals.
    - **Key specs:** Normal mode 100 kHz-900 MHz. ULTRA mode up to 7.3 GHz, level-calibrated to 7.3 GHz; signals visible up to 12 GHz (uncalibrated). RBW 0.2-850 kHz. DANL -102 dBm at 30 MHz with 30 kHz RBW (no LNA), -145 dBm with 200 Hz RBW and the built-in 20 dB LNA. Internal 0-31 dB attenuator. Absolute maximum input +6 dBm at 0 dB attenuation, +20 dBm short peak at 30 dB attenuation, ±5 V DC. Generator: sine -115 to -19 dBm in 1 dB steps up to 900 MHz, ±2 dB from -72 to -19 dBm up to 800 MHz; square wave up to 6.3 GHz; 'highest accuracy' mode up to 7.3 GHz. 4 in 480x320 resistive touch plus jog switch. microSD.
    - **Size weight power:** Size and weight not published on the pages read. Internal battery, at least 3 h for Ultra+. Charges in about 1 h from a USB port rated 500 mA or more. USB-C.
    - **Interface and linux:** USB serial control. QtTinySA (PySide6 + pyqtgraph, GPL-3) is written primarily for Linux and supports the tinySA Ultra; ARM/arm64 is not mentioned, so it is unverified on the Q6A. NanoVNA-Saver can also read tinySA data. A plain pyserial script on the Q6A is the fallback; the command set was not re-read this session. It works fully standalone with no PC.
    - **Price:** 9,486 UAH incl. VAT at Selteq (official distributor), about $211. eBay US $210.99 (seller unknown, clone risk). eBay.de about EUR 199-225. Official sellers include the Zeenko AliExpress store, R&L Electronics (US), Eleshop (EU), Mirfield (UK), Neven (CEE), GOTRONIK (PL), Switch Science (JP) and Selteq (UA).
    - **Tier:** core
    - **Integration notes:** Keep it outside the case and run it on its own battery during EMI hunts, so its supply does not couple into the receiver. When connecting it after an LNA or onto LNB/bias-tee coax, always use a DC block and a 20-30 dB pad: the SAWbird+ output can reach about +14 dBm at strong-signal sites (rf_frontend), which is above its +6 dBm maximum. The generator's low ceiling (-19 dBm sine) suits safe conducted SDR tests. The tinySA wiki warns of bad clones; buy only from the official list.
    - **Sources:**
      - https://tinysa.org/wiki/
      - https://tinysa.org/wiki/pmwiki.php?n=TinySA4.Specification
      - https://tinysa.org/wiki/pmwiki.php?n=Main.Buying
      - https://www.zeenko.tech/tinysa
      - https://selteq.com.ua/en/tinysa-ultra/
      - https://www.ebay.com/shop/tiny-spectrum-analyzer
      - https://www.ebay.de/shop/tinysa
      - https://github.com/g4ixt/QtTinySA
      - https://qsl.net/n8dmt/test-page/diy-test-equipment/low-cost-diy-noise-source/index.html
    - **Availability:** In the official channels listed; stock was not shown on the Selteq page.
    - **Cheaper alternative:** tinySA Ultra ZS405 or Ultra+ ZS406 (ULTRA mode to 5.3 GHz, level-calibrated to 6 GHz, enough for 137 MHz-2.4 GHz); price not verified. Free: use the SDRs as analyzers (next item), accepting uncalibrated levels and self-spurs.
    - **Safety notes:** The generator output is for conducted use only: cable to an SDR input, a filter, an attenuator or a load. Never connect it to an antenna. Receiving with it on an antenna is fine.
  3.
    - **Name:** SDRs as spectrum analyzers (RTL-SDR V4L + LimeSDR Micro with soapy_power / rtl_power / SDR++ / GNU Radio)
    - **Category:** Spectrum analyzer (software)
    - **Purpose in lab:** Wide sweeps and long-term spectrum logging from 500 kHz to 3.8 GHz with the radios already in the build: band occupancy, waterfall logs, before/after EMI comparisons, and scalar filter sweeps with a noise source. It complements the tinySA; it does not replace it.
    - **Key specs:** soapy_power: FFT sweeps on any SoapySDR device (README lists RTL-SDR, Airspy, SDRplay, HackRF, bladeRF, USRP, LimeSDR), with frequency hopping, crop/overlap, averaging, rtl_power-compatible or binary output and Welch windowing. Coverage: RTL-SDR V4L 500 kHz-1.766 GHz, about 2.56 MS/s stable; LimeSDR Micro 30 MHz-3.8 GHz. Levels are in dBFS and gain-dependent, with no absolute calibration. Each radio sees its own spurs (Lime 30.72 MHz harmonics, PCIe refclk, HDMI).
    - **Size weight power:** No extra hardware. CPU load on the Q6A: pin the sweeps away from the Lime RX thread (CPU7), as compute.json advises.
    - **Interface and linux:** Runs natively on the Q6A: soapy_power (Python 3 + NumPy + SimpleSoapy/SimpleSpectral; install pyFFTW or SciPy because numpy.fft is slow and memory-hungry), rtl_power from rtl-sdr-blog, SDR++, GNU Radio.
    - **Price:** $0
    - **Tier:** core
    - **Integration notes:** Calibrate dBFS to dBm per gain setting with the GPSDO tone or tinySA generator through the step attenuator (procedure below). Always take a 50-ohm-terminated baseline, so self-noise can be told apart from real signals. Turn Wi-Fi off during sweeps (shared USB hub).
    - **Sources:**
      - https://github.com/xmikos/soapy_power
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
    - **Cheaper alternative:** This is already the zero-cost option.
    - **Safety notes:** Receive-only.
  4.
    - **Name:** Leo Bodnar Mini Precision GPS Reference Clock (Mini GPSDO)
    - **Category:** Frequency reference (GPSDO)
    - **Purpose in lab:** A GPS-locked frequency reference and known-frequency test tone. Uses: calibrate the LimeSDR Micro VCTCXO DAC (stored in EEPROM XO_DAC); measure RTL-SDR V4L ppm error; correct the tinySA frequency; and, as an experiment, feed the LimeSDR Micro external reference input J4 (10-52 MHz, 1.8-3.3 V).
    - **Key specs:** 400 Hz-810 MHz programmable. One SMA output, 3.3 V CMOS square wave into 50 ohms, +6.4 dBm (8 mA drive) to +10.3 dBm (32 mA) at 10 MHz. Phase noise at 10 MHz: -125 dBc/Hz at 100 Hz, -145 at 1 kHz, -155 at 1 MHz. Antenna SMA supplies 3.3 V at up to 30 mA (needs an active GNSS antenna). The square-wave odd harmonics give usable markers well above 810 MHz.
    - **Size weight power:** 70 x 41 x 15 mm including SMAs. Weight not listed. 5 V at up to 250 mA (1.25 W or less) over mini-USB. No OCXO, so it fits the heat budget.
    - **Interface and linux:** Official configuration tools are Windows (.exe) and macOS (App Store). On Linux the open-source lbgpsdo (Python + hidapi, udev rule 99-lbgpsdo.rules) supports the 'Classic GPSDO mini'. It sets the PLL dividers, drive current and output enable, and does offline frequency-plan analysis, so the Q6A can configure it without a PC. Whether the Mini keeps its settings across power cycles is not verified.
    - **Price:** GBP 132, in stock at leobodnar.com (VAT treatment not stated). Roughly $170-180 (conversion approximate).
    - **Tier:** core
    - **Integration notes:** Plan it as a pouch or bench module powered from a Q6A USB 2.0 port or the pack's 5 V rail, with its own small active GNSS patch. It cannot share the LC76G antenna without a GNSS splitter. Add a case bulkhead 'REF IN' wired to Lime J4 with an MHF4-SMA pigtail. Before driving J4, use lbgpsdo to check that 30.72 MHz (the Lime's native VCTCXO frequency) is exactly reachable; otherwise use 10 MHz. Use the lowest drive (8 mA), keep the cable short, and confirm Lime PLL lock. Selecting the external reference in LimeSuiteNG for the Micro is NOT documented (only 'VCTCXO DAC (volatile)' and EEPROM XO_DAC are exposed), so the DAC-calibration route is the dependable one. The Lime's 1PPS input is not populated (resistor mod) and its firmware PPS handler is a stub.
    - **Sources:**
      - https://www.leobodnar.com/shop/index.php?main_page=product_info&products_id=301
      - https://github.com/hamarituc/lbgpsdo
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/clock.html
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
    - **Availability:** In stock (leobodnar.com, 18 Oct 2026 fetch).
    - **Cheaper alternative:** A software GPSDO built from the existing LC76G PPS plus an RP2040-Zero counter (optional item below), about $3-5. Free fallback: calibrate against a received carrier of known frequency.
    - **Safety notes:** This is the strongest emitter in the kit (+6 to +10 dBm square wave with harmonics). Into any SDR, use conducted paths only through 60-70 dB of fixed pads plus a DC block. Never connect it to an antenna. Leave the output disabled when not in use.
  5.
    - **Name:** Software GPSDO / PPS-gated frequency counter: RP2040-Zero counting LimeSDR Micro clock-out (J3) against the LC76G PPS
    - **Category:** Frequency counter / reference disciplining
    - **Purpose in lab:** Disciplines the LimeSDR Micro from the GNSS already in the build, with no extra GNSS receiver. The RP2040 counts the Lime's 30.72 MHz clock output (J3, 3.3 V CMOS) between LC76G PPS edges; the Q6A then steers the VCTCXO DAC through LimeSuiteNG. The same board works as a general PPS-gated counter for 3.3 V logic clocks up to about 60 MHz.
    - **Key specs:** LC76G PPS: under 100 ns RMS (gnss_imu). Resolution is 1 count per gate, 33 ppb at a 1 s gate and about 0.3 ppb averaged over 100 s, against the ±50 ppb stock VCTCXO. The RP2040 PWM slice can count edges on its B input up to about sys_clk/2 (about 62 MHz at 125 MHz); this is from the RP2040 datasheet as I recall it and was not re-read this session.
    - **Size weight power:** About 0.1 W. RP2040-Zero is thumb-sized. Fits inside the case next to the Lime.
    - **Interface and linux:** USB-CDC to the Q6A, or UART on the 40-pin header. A Python loop on the Q6A writes 'VCTCXO DAC (volatile)' through LimeSuiteNG and the final value to EEPROM XO_DAC.
    - **Price:** About $3-5 (RP2040-Zero clone 109-130 UAH per gnss_imu) plus an MHF4 pigtail (~$6) and firmware you write yourself.
    - **Tier:** optional
    - **Integration notes:** UNVERIFIED as a whole: nobody has published this for the Micro. Not confirmed: whether J3 is enabled by default, and whether the DAC steps are fine enough. Tee the PPS from Q6A pin 7 (GPIO96) to an RP2040 GPIO (both 3.3 V). Keep the J3 cable short and shielded, because 30.72 MHz harmonics (737.28, 1689.6, 1720.32 MHz) are already listed as spur risks. Gate it with the existing GNSS spoofing/time-sanity gates, so a bad fix cannot steer the oscillator.
    - **Sources:**
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/clock.html
    - **Cheaper alternative:** A one-time manual DAC calibration against the GPSDO tone, or against a broadcast carrier known to be GPS-locked; measure only the carrier offset.
    - **Safety notes:** Receive and measure only; it generates nothing.
  6.
    - **Name:** Uncalibrated broadband noise source (DIY Mini-Circuits ZFL-500-class amplifier source per N8DMT, or a generic SMA 'noise generator' module)
    - **Category:** Noise source
    - **Purpose in lab:** A wideband stimulus for scalar filter sweeps with the SDRs (passband, rejection, ripple of SAW and bandstop filters), relative LNA comparisons, and the 'hot' source in rough Y-factor tests. Its ENR can be characterized with the tinySA Ultra noise-figure menu.
    - **Key specs:** N8DMT DIY ZFL-500(LN) source, 12 V, with 5 dB input pad and 10 dB output pads. Measured ENR: 20.5 dB at 28-52 MHz, 21.0 at 146, 20.1 at 440, 17.0 at 902, 16.1 at 1296 and 8.4 dB at 2400 MHz (about 30 dB without the output pads). The tinySA Ultra became unreliable for this above about 4 GHz. Generic AliExpress modules: ranges, ENR, flatness and prices NOT verified this session.
    - **Size weight power:** Small module. 12 V DC switched on/off (ZFL-500 current not given on the page). Takes 12 V from the pack's 9-12 V rail.
    - **Interface and linux:** No data interface. Switch it with a MOSFET from a Q6A 40-pin GPIO (libgpiod) for automatic on/off Y-factor runs. Measure with the SDRs (soapy_power / GNU Radio) or the tinySA.
    - **Price:** About $20 used for a ZFL-500 (N8DMT). Generic modules: price not verified.
    - **Tier:** core
    - **Integration notes:** Characterize it once with the tinySA NF menu at 137, 435, 740, 1700 and 2200 MHz and keep the ENR table with the unit. Expect ±1-2 dB uncertainty (my estimate), which is good enough for filter sweeps and comparisons but not for absolute NF claims. Add a 6-10 dB output pad: it improves source match and lowers the level going into the SDR.
    - **Sources:**
      - https://qsl.net/n8dmt/test-page/diy-test-equipment/low-cost-diy-noise-source/index.html
      - https://qsl.net/n8dmt/rf-noise-source-part-1/index.html
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
    - **Cheaper alternative:** No generator at all: sky/ground Y-factor (procedure below) gives system temperature receive-only.
    - **Safety notes:** Conducted only, into an LNA input, filter, attenuator or SDR. Never connect it to an antenna: a broadband noise source on an antenna is a wideband jammer. Avoid amplified AWGN modules with about -10 dBm total output.
  7.
    - **Name:** Calibrated 346-class noise head (used Noisecom NC346/NC3404-class or Agilent/HP 346B, or new Pasternack PE85N1001) with a switched 28 V supply
    - **Category:** Noise source (calibrated)
    - **Purpose in lab:** Absolute Y-factor noise figure of the SAWbird+ LNAs and of whole receive chains, plus system noise temperature, with a traceable ENR table.
    - **Key specs:** Pasternack PE85N1001: 10 kHz-2 GHz, ENR 30 dB minimum, calibrated at 10/100/1000/2000 MHz. PE85N1005: 1-18 GHz, ENR 23 dB, 28 V at 25 mA, SMA female. NoiseWave NW3G-CS: 10 kHz-3 GHz, ±0.25 dB typical flatness, 15 or 30 dB ENR, 28 V. HP application note: 15 dB and 6 dB nominal ENR heads are common, ENR is calibrated at spot frequencies, and a low-ENR head lowers uncertainty when the instrument NF is low. The N8DMT used NC3404T reads 13.0-15.1 dB ENR at 440-2400 MHz through a 20 dB pad.
    - **Size weight power:** Coaxial head about the size of a thick SMA barrel (not measured here). 28 V at about 20-25 mA, switched on and off. Generate it from the 4S pack (12-16.8 V) with a small boost converter and a GPIO-driven MOSFET.
    - **Interface and linux:** No data interface. A GPIO-switched supply plus SDR power measurement on the Q6A (GNU Radio or Python), or the tinySA NF menu.
    - **Price:** New Pasternack/NoiseWave/kTB: price not published (quote only). Used 346-class heads on the surplus market: price not verified. Check that the ENR label or calibration sheet comes with the unit.
    - **Tier:** extended
    - **Integration notes:** Buy one only if you need absolute NF numbers. Below 2 GHz the PE85N1001 range covers 137 MHz-1.7 GHz; 2.2 GHz needs a 10 MHz-18 GHz 346-class head. A 30 dB ENR head needs a 15-20 dB pad for low-NF LNAs; add the pad loss to the ENR table carefully.
    - **Sources:**
      - https://www.pasternack.com/images/productpdf/PE85N1001.pdf
      - https://www.everythingrf.com/products/noise-sources/pasternack-enterprises-inc/608-20-pe85n1005
      - https://www.mwrf.com/markets/article/21840544/noise-source-promises-025-db-flatness-over-10-khz-to-3-ghz
      - https://www.everythingrf.com/products/noise-sources/ktb-solutions/608-2403-k2218a
      - https://xdevs.com/doc/HP/pub/5980-0288E.pdf
      - https://qsl.net/n8dmt/rf-noise-source-part-1/index.html
    - **Availability:** New units are quote-only; used units depend on the surplus market (not checked).
    - **Cheaper alternative:** The uncalibrated source with a tinySA-measured ENR table (core item above), or sky/ground Y-factor.
    - **Safety notes:** Conducted only; never on an antenna. Check the 28 V polarity, and keep the boost converter away from the RF bay (switching noise).
  8.
    - **Name:** Bench RF accessory set: fixed SMA attenuators (3/6/10/20/30 dB, DC-6 GHz, 2 W), SMA DC blocks, 50-ohm SMA terminations (dummy loads), adapters and two short low-loss test cables
    - **Category:** Attenuators, dummy loads, DC protection
    - **Purpose in lab:** Enables safe conducted testing. The pads drop the GPSDO tone (+6 to +10 dBm) by 60-70 dB to SDR-safe levels and protect the tinySA/VNA after LNAs. DC blocks protect instruments from bias-tee (4.5 V) and LNB (13/18 V) supplies. The terminations give a 'cold' 50-ohm reference for SDR noise floors, terminate unused Lime RX ports, and serve as VNA LOAD standards.
    - **Key specs:** Choose DC-6 GHz parts so they cover 137 MHz-2.4 GHz with margin. Specs and prices of specific AliExpress or Mini-Circuits parts are NOT verified this session. Verify every pad and DC block with the LiteVNA (S21 and S11) on arrival and label the measured loss at 137/435/740/1700/2200 MHz.
    - **Size weight power:** Passive. A few grams each.
    - **Interface and linux:** None.
    - **Price:** Not verified (generic SMA pads and loads are commonly cheap on AliExpress; budget roughly $40-80 for a set as an estimate).
    - **Tier:** core
    - **Integration notes:** The rf_frontend file already calls for a 6 dB pad after the SAWbird+ (Lime maximum input +10 dBm) and a 3-6 dB pad at the SDR if intermodulation shows up. Buy these pads from the same set. Keep at least 2 DC blocks and 3 terminations.
    - **Sources:**
      - https://tinysa.org/wiki/pmwiki.php?n=TinySA4.Specification
      - https://www.leobodnar.com/shop/index.php?main_page=product_info&products_id=301
    - **Cheaper alternative:** The LOAD standard that comes with the VNA calibration kit can stand in as one termination.
    - **Safety notes:** Terminations used with generators must be rated for the generator power (the GPSDO at +10 dBm, 10 mW, is far below a 2 W rating).
  9.
    - **Name:** Digital step attenuator module, PE4302 (DC-4 GHz) or HMC472 (DC-3.8 GHz), 0-31.5 dB in 0.5 dB steps
    - **Category:** Step attenuator
    - **Purpose in lab:** Programmable attenuation for SDR dBFS-to-dBm calibration, gain-linearity and minimum-discernible-signal tests, AGC/overload checks and automated sweeps driven from the Q6A.
    - **Key specs:** 0-31.5 dB in 0.5 dB steps, 6-bit parallel or serial control. PE4302: DC-4 GHz; the chip has been obsolete since 2018, so modules are remaining stock; the PE4312 is the pin-compatible successor. HMC472 module: DC-3.8 GHz. Insertion loss and step accuracy are not verified, so measure every state with the VNA and keep a correction table.
    - **Size weight power:** Small PCB module with SMA connectors. Logic-level supply; exact current not verified.
    - **Interface and linux:** Drive the parallel or serial lines from Q6A 40-pin GPIO (libgpiod, 3.3 V logic; confirm the module's logic level) or from an RP2040. No PC needed.
    - **Price:** PE4302: EUR 9.88 (~$11.49) + EUR 5.88 shipping on eBay (listing updated July 2025); $27.14 on Newegg; eBay.de $17.97 + $6.90. HMC472: about $30 + $6.70 shipping (Banggood, 2021, dated).
    - **Tier:** extended
    - **Integration notes:** Use it only at low levels, after the 60-70 dB fixed pads and never in front of the GPSDO's raw output. Keep it on the bench; its control wiring should not run through the RF bay during passes. Note: the UART6 overlay disables i2c6/spi6 on pins 3/5, so plan the GPIO lines around the GNSS wiring.
    - **Sources:**
      - https://www.ebay.com/itm/265899138812
      - https://siliconchip.com.au/Issue/2018/June/El+Cheapo+Modules+17%3A+4GHz+digital+attenuator
      - https://siliconchip.com.au/Issue/2021/October/El+Cheapo+Modules%3A+3.8GHz+Digital+Attenuator
      - https://www.newegg.com/p/2S7-090G-01GH3
      - https://www.rfmw.com/Products/Detail/PE4312-Peregrine-Semiconductor/472826/?pid=1130
    - **Cheaper alternative:** Stack fixed pads from the accessory set (1 dB resolution is enough for most checks). Manual 0-90 dB knob step attenuators exist, but none was verified this session.
    - **Safety notes:** Passive. Keep its input low, because its power rating was not verified.
  10.
    - **Name:** AD8318 log-detector power meter module (1 MHz-8 GHz) read by an ADS1115-class I2C ADC on the Q6A
    - **Category:** RF power meter / detector
    - **Purpose in lab:** Absolute RF level checks: verify generator and GPSDO-tone levels before they reach an SDR (Lime maximum +10 dBm), measure LNA output levels at strong-signal sites, measure noise-source total power, and optionally run a live 'overload alarm' on a coupler tap after the LNA.
    - **Key specs:** Module rated -65 to +5 dBm. About 60 dB is accurate (-5 to -60 dBm, ±1 dB agreement between 100 MHz and 4 GHz in Silicon Chip's test). Log conformance 1 MHz-6 GHz, usable to 8 GHz. Vout 0.5-4.6 V with a negative slope, measured -24.33 mV/dB (nominal -25).
    - **Size weight power:** 33 x 24.5 mm PCB with SMA. Needs 7.5-9 V (78L05 regulator), 68 mA typical, about 0.6 W from the pack's 9 V rail.
    - **Interface and linux:** Analog output. Read it with an ADS1115 on Q6A i2c0 (pins 13/15) or i2c2 (27/28), not i2c6 (disabled by the UART6 overlay). Vout reaches 4.6 V, so add a resistive divider for a 3.3 V ADC. Python on the Q6A converts volts to dBm using a calibration table.
    - **Price:** About $16.50 (Silicon Chip, 2018); eBay $39.00. AliExpress price not verified.
    - **Tier:** extended
    - **Integration notes:** Calibrate it against the tinySA at 3 levels per band (137/435/740/1700/2200 MHz), because absolute accuracy is not specified. Bench use only, unless you build the optional overload monitor with a directional coupler (coupler not specified here).
    - **Sources:**
      - https://www.siliconchip.com.au/Issue/SC/2018/March/El+Cheapo+Modules+14%3A+Logarithmic+RF+Detector
      - https://www.ebay.com/itm/AD8318-RF-Log-Detector-70dB-RSSI-Measurement-Power-Meter-1-MHz-to-8000-MHz/133029848381
    - **Cheaper alternative:** The tinySA's own level readout (±2 dB below 800 MHz) covers most needs.
    - **Safety notes:** Receive and measure only; keep inputs at or below +5 dBm.
  11.
    - **Name:** Near-field H/E probe set for EMI hunting (step-up: Com-Power PS-500, 9 kHz-5 GHz)
    - **Category:** EMI near-field probes
    - **Purpose in lab:** Locates the noise sources the input files flag inside the handheld: HDMI cable and pixel clock, the RA620 bridge, PCIe riser refclk, USB3 NVMe, SY81012/SY7120 and IP2368 switchers, the display backlight. Use them with the tinySA (independent battery and built-in 20 dB LNA, so no extra preamp) to verify ferrites, shields and filtered rails.
    - **Key specs:** Com-Power PS-500: 9 kHz-5 GHz, in stock at The EMC Shop. Generic AliExpress H/E-field sets: specs and prices NOT verified this session. DIY: small shielded loops made from semi-rigid coax.
    - **Size weight power:** Passive, pocket-sized.
    - **Interface and linux:** SMA to the tinySA, or to an SDR via soapy_power. No software needed.
    - **Price:** Com-Power PS-500 $109 (The EMC Shop). Langer XF1 (30 MHz-6 GHz) from $275, Keysight N9311X-100 (30 MHz-3 GHz) $325. Generic sets: not verified. DIY loops: about $0-10.
    - **Tier:** core
    - **Integration notes:** Start with a cheap or DIY set. Relative readings (before/after a fix) are what matter, and absolute antenna factors are not needed. Probe with the case open on the bench, then repeat the SDR noise-floor A/B tests.
    - **Sources:**
      - https://theemcshop.com/test-equipment/near-field-probes-e-h/emc-probes/kits/
    - **Availability:** Com-Power PS-500 in stock (The EMC Shop).
    - **Cheaper alternative:** DIY semi-rigid coax loop probe.
    - **Safety notes:** Passive, receive-only.
  12.
    - **Name:** Leo Bodnar LBE-1421 dual-output GPSDO (upgrade path)
    - **Category:** Frequency reference (GPSDO)
    - **Purpose in lab:** Two simultaneous GPS-locked outputs: for example 30.72 MHz or 10 MHz into Lime J4 plus a calibration tone or comb into the RTL-SDR or tinySA, with a switchable PPS output on output 1 for timing tests.
    - **Key specs:** Output 1: 1 Hz-800 MHz. Output 2: 1 Hz-1.4 GHz. Switchable 1-PPS on output 1. PLL or FLL mode. Per-output low/normal drive. Ships with an active GPS antenna on 5 m of cable.
    - **Size weight power:** Size not stated on the reseller page. Ships with a USB A-to-C cable (USB-C power implied, not confirmed).
    - **Interface and linux:** Linux configuration through lbgpsdo's lbe142x.py: frequencies, saving to flash, PLL/FLL, output enable, PPS, drive level.
    - **Price:** EUR 225 net / EUR 267.75 incl. 19% VAT (Batronix, in stock).
    - **Tier:** optional
    - **Integration notes:** Only worth it if the Mini proves limiting. The time-nuts list warns that the newer Bodnar PPS outputs are the raw GNSS PPS and fairly jittery.
    - **Sources:**
      - https://www.batronix.com/shop/frequency-references/GPSDO/index.html
      - https://github.com/hamarituc/lbgpsdo
      - https://febo.com/pipermail/time-nuts_lists.febo.com/2024-November/109355.html
    - **Availability:** In stock at Batronix (DE).
    - **Cheaper alternative:** Leo Bodnar Mini (GBP 132) as above.
    - **Safety notes:** Same as the Mini: conducted only through heavy pads; never connect to an antenna.
- **Capabilities added:**
  - Two-port VNA measurement from 50 kHz to 6.3 GHz (S11, S21, S22, S12, TDR/DTF) for cables, MHF4 pigtails, adapters, filters, bias tees, attenuators and powered LNAs, saved as Touchstone files the Q6A can process
  - Independent level-calibrated spectrum analysis from 100 kHz to 7.3 GHz (visible to 12 GHz), separate from the receivers under test
  - Self-EMI localisation with near-field probes, plus A/B noise-floor audits with terminated SDR inputs (display, Wi-Fi, USB3, charger and bucks on/off)
  - GPS-traceable frequency accuracy: Lime VCTCXO DAC calibration to the ppb level, RTL-SDR ppm correction, tinySA frequency correction, and an experimental external reference into Lime J4
  - Noise measurements: ENR characterisation, approximate or calibrated Y-factor LNA noise figure, SDR noise floor, receive-only sky/ground system temperature
  - Scalar filter sweeps with a noise source and SDR, and tracking-generator sweeps with the tinySA (conducted)
  - SDR dBFS-to-dBm calibration, gain linearity and MDS tests with a programmable step attenuator
  - Absolute RF power checks (-60 to -5 dBm accurate) with an AD8318 detector read by the Q6A, and an optional live LNA-overload monitor
  - Receive-only site surveys for strong signals that could overload the LNAs or SDRs before a satellite pass
  - Long-term spectrum logging (rtl_power-format) with soapy_power on the existing SDRs
- **Procedures:**
  1.
    - **Name:** P1. VNA calibration and coax/pigtail screening
    - **Steps:**
      - Power the LiteVNA 64 from its own battery and let it warm up about 10 minutes. Choose the lowest stimulus level the firmware offers (the level is not published).
      - Set 100 MHz-3 GHz (or 50 kHz-6.3 GHz for TDR) and 401 or more points. Calibrate SOLT at the far ends of the two test cables: open, short and load on port 1, thru between the cables, isolation with two loads.
      - Measure each RF1.13 MHF4-SMA pigtail, LMR-240 and RG316 run. Record S21 loss at 137, 145.8, 435, 740, 1700 and 2200 MHz and S11. My suggested pass mark: S11 at or below -20 dB and loss within about 0.5 dB of the cable datasheet.
      - Switch to TDR/DTF with the cable velocity factor entered, to find a bad crimp or a damaged MHF4 mating.
      - Save .s2p files (microSD, or NanoVNA-Saver on the Q6A) and build a per-cable loss table for the link budget.
    - **Needs:**
      - LiteVNA 64 (or LiteVNA 62)
      - SOLT calibration kit and two short test cables
      - SMA adapters
      - Optional: NanoVNA-Saver on the Q6A
  2.
    - **Name:** P2. Filter and bias-tee characterisation (conducted)
    - **Steps:**
      - Calibrate as in P1 over the filter's span plus 2x margin, e.g. 50-300 MHz for the FM bandstop or 1.4-2.5 GHz for an L/S SAW.
      - Insert the DUT with a DC block on any port that has a DC path. Measure S21 (insertion loss, rejection, ripple) and S11/S22 (match).
      - For bias tees, measure RF-port S21 at 100-200 MHz and 740 MHz. The input files report 3-7 dB loss at VHF on cheap units, so keep only units that pass at your band.
      - Cross-check one filter with the tinySA tracking generator (sine at -19 dBm or lower, up to 900 MHz) to confirm the VNA calibration.
      - Archive the .s2p files, and add the loss to the system noise budget (filter loss in front of an LNA adds directly to NF).
    - **Needs:**
      - LiteVNA 64
      - tinySA Ultra+ (optional cross-check)
      - DC blocks
      - SAWbird filters, FM bandstop, bias tees
  3.
    - **Name:** P3. Powered LNA gain, match and stability (conducted only)
    - **Steps:**
      - Calibrate thru with a 20-30 dB pad already in the port-2 path, so the pad is normalised out and port 2 is never overdriven.
      - Wire VNA port 1 to the DC block, then the LNA input. Wire the LNA output to the bias-tee RF+DC port, then the bias-tee RF port, the pad and port 2. Feed the bias-tee DC port from the pack's 4.5-5 V supply with a current limit.
      - At the lowest VNA output, read S21 (gain), S11 (input match), S22 and S12 (reverse isolation) at 137, 435, 740, 1700 and 2200 MHz.
      - Stability check: terminate the LNA input with 50 ohms, power it, and look at the output with the tinySA (through a pad and DC block) for oscillation tones from 100 kHz to 7 GHz.
      - Record gain G1 for the Y-factor second-stage correction in P7.
    - **Needs:**
      - LiteVNA 64
      - Bias tee
      - 20-30 dB pad
      - DC block
      - 50-ohm termination
      - tinySA Ultra+
  4.
    - **Name:** P4. GPSDO frequency calibration of Lime VCTCXO, RTL-SDR ppm and tinySA (conducted)
    - **Steps:**
      - Connect the Leo Bodnar Mini to the Q6A over USB with its active GNSS patch outdoors or at a window. Use lbgpsdo to set drive to 8 mA (about +6.4 dBm) and a frequency whose odd harmonic lands in the band of interest; check exactness with lbgpsdo's frequency-plan analysis. Wait for lock.
      - Route the output through 60-70 dB of fixed pads plus a DC block into the SDR input. Never connect it to an antenna. Target about -60 to -100 dBm at the SDR.
      - On the Lime, record I/Q and measure the tone offset with a long FFT (SDR++ or GNU Radio; sub-Hz bins). Adjust 'VCTCXO DAC (volatile)' in LimeSuiteNG until the offset is under about 1 ppb, then write the value to EEPROM XO_DAC. Re-check after 30 minutes at operating temperature.
      - On the RTL-SDR V4L, measure the offset at about 137 and 435 MHz, compute ppm, and enter it in the SatDump/SDR++ settings.
      - Feed the same tone (padded) into the tinySA and set its frequency correction.
      - Optional: once the Lime is disciplined, receive the QO-100 beacon to log the LNB LO drift against the now-trusted Lime clock.
    - **Needs:**
      - Leo Bodnar Mini GPSDO + active GNSS patch
      - lbgpsdo on the Q6A
      - Fixed attenuators (30+30+10 dB) and DC block
      - LimeSuiteNG, SDR++/GNU Radio
  5.
    - **Name:** P5. LimeSDR Micro external reference (experimental)
    - **Steps:**
      - Fit an MHF4-SMA pigtail from Lime J4 to a case 'REF IN' bulkhead.
      - Set the GPSDO to 30.72 MHz if lbgpsdo shows it is exactly reachable, otherwise 10 MHz. J4 accepts 10-52 MHz at 1.8-3.3 V. Use the minimum drive and a short cable.
      - Find and set the external-reference option in LimeSuiteNG for the Micro. This is NOT documented on the pages read, so stop here if it does not exist.
      - Confirm PLL lock and repeat the P4 tone test. The offset should stay within GPSDO accuracy while the case warms up.
      - If unstable, revert to the VCTCXO plus the EEPROM DAC value (P4). Lime warns that improper clock signals can damage the device.
    - **Needs:**
      - Leo Bodnar Mini or LBE-1421
      - MHF4-SMA pigtail
      - LimeSuiteNG
  6.
    - **Name:** P6. Self-EMI and noise-floor audit
    - **Steps:**
      - Terminate each SDR input with 50 ohms and record the noise floor (dBFS at fixed gain) at 137, 145, 435, 740, 1700 and 2200 MHz with soapy_power. Do it with the display on and off, Wi-Fi on and off (nmcli radio wifi off), the USB3 NVMe on and off, and the charger on and off (the A/B matrix from the input files).
      - Put the antenna back and repeat, to see what couples in through the antenna and feed.
      - With the case open on the bench, sweep the tinySA (on battery, LNA on) with an H-field probe over the HDMI cable, RA620 bridge, PCIe riser, buck converters, IP2368 and display backlight. Note peaks at frequencies that matter (e.g. 1700 MHz = PCIe refclk x17, Lime 30.72 MHz harmonics).
      - Apply fixes (ferrites, shield cans, filtered rails, clean-clock EDID) and repeat steps 1-3. Keep the before/after logs.
    - **Needs:**
      - 50-ohm terminations
      - soapy_power / rtl_power on the Q6A
      - tinySA Ultra+
      - Near-field probe set
  7.
    - **Name:** P7. Y-factor LNA noise figure (conducted; never radiated)
    - **Steps:**
      - Use a noise source with an ENR table: calibrated head, or the uncalibrated source with a tinySA-measured ENR. Add a 6-10 dB pad on its output and correct the ENR for the pad.
      - Calibration step: connect the noise source directly to the measurement receiver (SDR at fixed gain, AGC off, fixed bandwidth, e.g. 100-500 kHz). Read N_on and N_off and compute the receiver's own F2.
      - Insert the DUT LNA, powered through its bias tee. Read N_on and N_off again. Y = N_on/N_off (linear), F12 = ENR_lin/(Y-1), assuming the source cold temperature is about 290 K.
      - Second-stage correction: F1 = F12 - (F2-1)/G1, with G1 from P3. NF = 10*log10(F1). Repeat at 137, 435, 740 and 1700 MHz.
      - Switch the noise source with a GPIO-driven MOSFET and automate the run on the Q6A. Average enough samples that the N_on/N_off scatter is under about 0.05 dB.
    - **Needs:**
      - Calibrated noise head + 28 V switched supply, or uncalibrated source + tinySA ENR table
      - LNA under test + bias tee
      - RTL-SDR or Lime as the detector, or the tinySA NF menu
      - Fixed pads
  8.
    - **Name:** P8. Receive-only antenna and system-temperature checks (no generator)
    - **Steps:**
      - Sky/ground Y-factor: with the full chain (antenna, LNA, filters, SDR) at fixed gain, measure noise power with the antenna pointed at clear zenith sky away from the sun and the galactic plane (cold sky, a few K to about 10 K at L-band, approximate). Then measure it pointed at the ground, or covered with an absorber at ambient (about 290 K).
      - Tsys = (T_hot - Y*T_cold)/(Y-1), with Y = P_hot/P_cold. Compare antennas and LNA placements by Tsys (and later G/T) instead of by S11.
      - Cross-check against real signals: compare SNR on the same satellite passes, the QO-100 beacon via the LNB, or the LC76G's reported C/N0 with different patch placements.
      - Use VNA S11 on an antenna only where local rules explicitly allow low-power test emissions; by default this lab does not radiate.
    - **Needs:**
      - Existing antennas, LNA, SDR
      - soapy_power or GNU Radio power probe
      - Optional absorber or ground plane
  9.
    - **Name:** P9. SDR level calibration and linearity with the step attenuator
    - **Steps:**
      - Source: tinySA generator at -40 dBm (±2 dB below 800 MHz), or the GPSDO tone after 60-70 dB of pads, with its level confirmed on the tinySA or AD8318.
      - Chain: source, then the digital step attenuator (correction table from the VNA), then the SDR input.
      - Step 0 to 31.5 dB and log dBFS at each SDR gain setting. Fit the linear range, then find compression at the top and the MDS at the bottom.
      - Store the dBFS-to-dBm tables per band and gain so soapy_power and SatDump logs can be quoted in dBm.
    - **Needs:**
      - tinySA Ultra+ or GPSDO + fixed pads
      - PE4302/HMC472 step attenuator driven from Q6A GPIO
      - VNA correction table
      - soapy_power
  10.
    - **Name:** P10. Scalar filter sweep with noise source and SDR (no VNA needed)
    - **Steps:**
      - Noise source (padded), then the filter under test, then the SDR. Record an averaged spectrum across the span with soapy_power, using hops wider than the filter.
      - Repeat with a thru barrel in place of the filter. S21 is approximately sweep(DUT) minus sweep(thru), in dB.
      - Use this for quick field checks of SAW filters or the FM bandstop when the VNA is not with you.
    - **Needs:**
      - Noise source
      - Thru barrel
      - RTL-SDR or Lime with soapy_power
  11.
    - **Name:** P11. Receive-only site overload survey before a pass
    - **Steps:**
      - Connect the antenna and LNA, then a 20-30 dB pad and DC block, to the tinySA (or sweep with soapy_power on the SDR).
      - Sweep 50 MHz-3 GHz and note the strongest carriers (broadcast FM, cellular, Wi-Fi) and their levels at the LNA output.
      - If any carrier would put the SAWbird+ output near +14 dBm or the Lime input near +10 dBm, add the 6 dB pad, move the FM bandstop in front of the LNA, or change site (rf_frontend guidance).
      - Optional: leave an AD8318 on a coupler tap after the LNA as a live overload alarm read by the Q6A.
    - **Needs:**
      - tinySA Ultra+ or SDR
      - Fixed pads, DC block
      - Optional AD8318 + ADC
- **Rejected:**
  1.
    - **Name:** NanoVNA-H4 (Hugen)
    - **Why:** Officially effective only to about 1.5 GHz (40 dB dynamic range up to 1.5 GHz, with 'substantial noise floor and other uncertainties above 1.5 GHz'), so it fails the 2.4 GHz requirement. Vendors selling '2.7 GHz NanoVNA Plus' are flagged as usually fake. Price not verified.
  2.
    - **Name:** NanoVNA-F V3 as the primary VNA
    - **Why:** Covers 1 MHz-6 GHz in a 125x75x20 mm metal case with 4500 mAh (about 5 h), but costs 2-3x a LiteVNA 64 (Newegg $479.99, date unclear; Gotronik 1,375 zl, May 2025). Its rated dynamic range is lower (S21 65 dB, S11 50 dB), and NanoVNA-Saver names only 'NanoVNA-F', not the F V3, so Q6A software support is unverified. Acceptable only if you specifically want the metal case and the longer battery life.
  3.
    - **Name:** SAA-2N / NanoVNA V2 family (NanoRFE V2 Plus4 / Plus4 Pro)
    - **Why:** Ceiling is 4-4.4 GHz instead of 6 GHz. The V2 Plus4 was $299 and out of stock; the Plus4 Pro is $399 (nanorfe.com/shop). Good dynamic range (90 dB at 1 GHz, 300 g, NanoVNA-QT on Linux), but more expensive than the LiteVNA for less range. The older third-party 'SAA-2N' units were not verified this session (clone risk).
  4.
    - **Name:** tinySA Basic
    - **Why:** Tops out at 960 MHz (and only 350 MHz on the good input), so it cannot see 1.7/2.2 GHz or the self-spurs at 1.7 GHz.
  5.
    - **Name:** ImmersionRC RF Power Meter v2
    - **Why:** Built for FPV transmitters: -20 to +30 dBm, fixed bands (35/72/433/1200/2400/5600-6000 MHz). The -20 dBm floor is useless for receive-chain levels, and retail prices are $99-239 with patchy stock. The tinySA plus an AD8318 cover the lab's needs.
  6.
    - **Name:** Leo Bodnar LBE-1420
    - **Why:** EUR 155 net / EUR 184.45 gross, 1 Hz-1.1 GHz, single output. lbgpsdo does not support it on Linux (only a separate project is acknowledged), and reports on its PPS output conflict. The cheaper Mini (Linux-supported) or the LBE-1421 (Linux-supported, PPS) fits better.
  7.
    - **Name:** LimeSDR Micro GNSS variant or its 1PPS input as the reference
    - **Why:** Per the input files and Lime docs: no NMEA or PPS reaches the host, there is no GPSDO loop in the firmware (the PPS handler is a stub), and the 1PPS input is 'not populated' without moving resistors. GPSDO support 'is not guaranteed'.
  8.
    - **Name:** OCXO-based bench GPSDOs (generic Chinese 10 MHz units)
    - **Why:** Not verified this session. OCXO warm-up power and size do not fit the Q6A case heat and volume budget, and the USB-powered Bodnar Mini (1.25 W or less) already gives a GPS-locked reference. Bench-only at best.
  9.
    - **Name:** Dedicated bench frequency counter
    - **Why:** Redundant. A GPSDO tone plus a long FFT on the SDRs or tinySA gives Hz or better accuracy at UHF/L-band, and the optional RP2040 PPS-gated counter covers clock-level counting. No specific counter model was verified.
  10.
    - **Name:** New calibrated lab noise sources (NoiseWave NW3G-CS, kTB k2218A, Pasternack PE85N1005) as the first purchase
    - **Why:** Prices not published (quote-only), 28 V supply, and accuracy beyond what a hobby receive chain needs. Consider them only after the uncalibrated source and sky/ground method run out of accuracy.
  11.
    - **Name:** Amplified AWGN modules (e.g. Maury NC1113A/B, Pasternack PE85N1012)
    - **Why:** About -10 dBm total output with ±2-2.5 dB flatness at 15 V and 250-300 mA. Too strong and power-hungry for Y-factor work, and dangerous if ever connected to an antenna (wideband jamming). A low-ENR coaxial head is the right tool.
  12.
    - **Name:** Premium near-field sets (Langer XF1 $275+, Keysight N9311X-100 $325, ETS-Lindgren 7405 $1,500)
    - **Why:** Relative EMI hunting in a hobby handheld does not need calibrated antenna factors. Start cheap or DIY, and step up to the Com-Power PS-500 ($109) if needed.
  13.
    - **Name:** Antenna S11/VSWR sweeps on air with the VNA or tinySA generator
    - **Why:** Feeding a stimulus into an antenna radiates it, which breaks the lab's receive-only rule. Use the receive-only checks (P8) by default. Do S11 on antennas only if local rules explicitly allow low-power test emissions.
  14.
    - **Name:** Mounting the VNA, tinySA or power meter inside the ASA case
    - **Why:** Limited internal volume and heat budget, and their own switching supplies and USB activity would add noise next to the SDRs. Keep them as pouch instruments; only the Mini GPSDO (1.25 W or less) and the RP2040 counter are candidates for internal mounting.
- **Notes:** CORE KIT (about $620-800 before shipping/VAT; accessory prices are estimates): LiteVNA 64, tinySA Ultra+ ZS407, Leo Bodnar Mini GPSDO, uncalibrated noise source, fixed pads, DC blocks and terminations, a cheap or DIY near-field probe set, plus free SDR-analyzer software. EXTENDED: PE4302/HMC472 step attenuator, AD8318 power meter, calibrated noise head. OPTIONAL: RP2040 software GPSDO/counter, LBE-1421.
  
  USB/Q6A: the Q6A has 3x USB 2.0 Type-A on one shared FE1.1s hub (shared with the AIC8800 Wi-Fi) plus 1x USB 3.1 (reserved for the NVMe recorder). The RTL-SDR and the IMU puck already take 2 of the 3 USB 2.0 ports, so bench instruments get 1 port. Use a small USB 2.0 hub powered from the pack's 5 V rail, not from Q6A VBUS. The task says about 500 mA per port; compute.json's schematic reading says the WS4612 switches limit at about 2.1 A, so treat 500 mA as the safe planning figure. All the instruments are low-bandwidth USB serial devices with their own batteries. Unplug them during passes, because USB activity adds noise.
  
  Software on the Q6A, unverified on arm64: NanoVNA-Saver (pipx, Python >=3.10, PySide6), QtTinySA (PySide6/pyqtgraph, Linux-first, ARM not mentioned), lbgpsdo (python-hidapi), soapy_power. Every instrument also works standalone on its own screen, so no PC is required.
  
  Safety and legal (generic, country unknown): the lab is receive-only on air. The VNA port 1, tinySA generator, GPSDO and noise sources are used only into cables, attenuators, filters, LNAs or 50-ohm loads, never into an antenna. Keep the GPSDO (the strongest emitter, +6 to +10 dBm) behind 60-70 dB of pads, and always put DC blocks on bias-tee and LNB lines (tinySA ±5 V DC maximum, LNB 13/18 V). Rules on reception, test emissions and importing test equipment vary by country, so check national rules yourself. Nothing here is aimed at private or military communications. The only carriers used for calibration are GNSS, satellite beacons, or test tones on cables.
  
  Unverified or gaps: tinySA size and weight; LiteVNA stimulus level and weight; whether LimeSuiteNG can select the Micro's external reference; whether J3 clock-out is on by default; AliExpress prices for noise sources, probe sets, pads and loads; whether the Mini keeps its settings after power-off; Eleshop LiteVNA prices (seen only in a search snippet, page returned 403). Prices are as fetched 18 Oct 2026; UAH conversions use 44.86 UAH/USD from the input files. All 12 WebSearch calls in the budget were used; several primary pages (Eleshop, ImmersionRC, analog.com, Tekbox, Switch Science) were unreachable (403/404/429/503).

## lab:rf_accessories (run `wf_1dd437c5-0cf`)

- **Area:** RF bench accessories for the portable receive-only lab: antenna/front-end switch matrix, programmable and fixed attenuators, filter bank, LNA bank, bias-tee/DC-block kit, terminations, splitter, cables/adapters/tools, RF protection, and calibration standards. All prices were checked on 18 Oct 2026 unless marked otherwise.
- **Items:**
  1.
    - **Name:** Mini-Circuits ZSWA4-63DR+ SP4T absorptive solid-state switch (GPIO-controlled), first stage of the switch matrix
    - **Category:** RF switch matrix
    - **Purpose in lab:** Software selection between front-end chains on one Lime RX port (e.g. RX-L: 70 cm chain / QO-100 LNB IF / bench input / 50 ohm reference load) with no re-mating of the 30-cycle MHF4 connectors. It also gives an always-available terminated port for noise-floor checks and lets you run time-multiplexed A/B tests.
    - **Key specs:** 1-6000 MHz, absorptive (unselected ports are terminated in 50 ohm). Insertion loss 1.3 dB typical / 2.0 dB max (1-2700 MHz), 1.7 dB (2.7-5 GHz). Isolation from COM to a terminated port: 80 dB typical (55 min) at 1-1000 MHz, 58 dB (44 min) at 1-2.7 GHz. Port-to-port isolation 73 / 57 dB. VSWR 1.25. P0.1dB +35 dBm at 900 MHz; IP3 +58 dBm; switching 320 ns. Absolute maximums: RF +34 dBm, DC at RF ports 8 V, ESD 4 kV HBM on RF ports.
    - **Size weight power:** 2.00 x 1.5 x 0.6 in (51 x 38 x 15 mm), aluminium case, 5x SMA-F plus a DB-9 for power and control. Vdd 2.3-3.6 V at 0.1 mA typical (up to 3 mA at startup), so it draws effectively nothing. The datasheet text does not give the weight.
    - **Interface and linux:** 2-pin logic (V1, V2; V3 open or grounded) or 3-pin logic for an all-off state. Low is at most 0.2xVDD; high is at least 0.8xVDD (2.64 V at 3.3 V) and at most 5.5 V. Control current 0.015 mA per pin. Truth table (V3 V2 V1): 000=RF4, 001=RF1, 010=RF2, 011=RF3, 101/110=all off, 111 unsupported. All control pins have internal 100 kOhm pull-downs, so with undriven pins the switch sits on RF4. Linux: two lines from the Q6A 40-pin header (3.3 V) or from an I2C expander, driven with libgpiod (gpioinfo to find the lines; v2 syntax: gpioset -c gpiochipN -z A=1 B=0) or python gpiod. Wrap it in a small 'rfsel <chain>' script that the pass scheduler calls before SatDump/SDR++ starts.
    - **Price:** $307.32 (qty 1-9, Mini-Circuits web store, USD, before shipping and VAT)
    - **Availability:** Mini-Circuits showed 0 units in stock on 18 Oct 2026 and says to contact sales@minicircuits.com. Lead time unknown.
    - **Tier:** extended
    - **Integration notes:** Port plan for SW-A (Lime RX-L): RF1 = 70 cm chain (Uputronics 435 or LNA V2, then its bias-tee injector); RF2 = QO-100 IF (LNB, then a 13/18 V injector with the DC-blocked RF port toward the switch, then VLF-1000+); RF3 = bench-input SMA bulkhead with a permanent VLM-33-S+ limiter and 20 dB pad; RF4 = ANNE-50+ load, which is the power-on default. COM goes to the 10 dB pad, then the MHF4L pigtail, then the Lime. Put the switch after every LNA and after every injector. The datasheet allows 8 V DC at most on the RF ports and does not say the ports are DC-blocked. My inference is that LNA bias reaching an OFF (terminated) port would be dumped into the internal load, so keep every port DC-free and keep 13/18 V LNB power out of it. Supply Vdd from the header's 3.3 V pin. Do not use header pins 7 (PPS), 8/10 (debug UART), 13/15 (I2C0), 16/18 (GNSS UART6) or 22/33/36/37 (spi14, enabled by default). Mount it on the aluminium mid-plate. The Lime's own SKY13414 still selects its internal L/W/H path through LimeSuiteNG; this switch selects the external chain.
    - **Cheaper alternative:** An HMC7992-based 0.1-6 GHz SP4T SMA board from AliExpress or Amazon. Sellers claim 0.6 dB insertion loss, 45 dB isolation and a 3-5 V supply. Price not verified (the listing pages would not load). Qualify one with Procedure 2 before building it in.
    - **Safety notes:** Receive-path device only. Keep total input under +24 dBm into an OFF port; this lab never gets near that.
    - **Sources:**
      - https://www.minicircuits.com/WebStore/dashboard.html?model=ZSWA4-63DR%2B
      - https://www.minicircuits.com/pdfs/ZSWA4-63DR+.pdf
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
  2.
    - **Name:** Generic HMC7992 SP4T switch board (cheaper first stage, or a second stage for the Lime RX-W / RTL input)
    - **Category:** RF switch matrix
    - **Purpose in lab:** Low-cost second switch: Lime RX-W choice between L-band GOES chain / S-band chain / bench / load, or an RTL-SDR input selector. Together with the ZSWA4 it makes a 2 x SP4T matrix.
    - **Key specs:** Seller claims only: 0.1-6 GHz SP4T non-reflective, about 0.6 dB insertion loss, about 45 dB isolation, 3-5 V supply. The ADI datasheet could not be fetched (analog.com returned 503), so logic levels and DC-block capacitors are unverified. 0.1 GHz does not reach the RTL's HF range.
    - **Size weight power:** Small SMA board or metal box. Size, weight and current not verified.
    - **Interface and linux:** Presumably 2 logic lines (decoder), driven from the header GPIO or an I2C expander through libgpiod. Confirm the logic thresholds against 3.3 V before use.
    - **Price:** Not verified. AliExpress and Amazon pages for HMC7992/HMC349/HMC849 boards were found but would not load.
    - **Availability:** Several AliExpress and Amazon listings (Oct 2026).
    - **Tier:** optional
    - **Integration notes:** Same rules as the ZSWA4: place it after the LNAs and injectors and keep its ports DC-free. Accept it only if Procedure 2 measures insertion loss of 1.5 dB or less, isolation of at least 40 dB below 1 GHz, and at least 30 dB at 1.7-2.3 GHz. Avoid HMC241 boards (see rejected).
    - **Cheaper alternative:** No switch: swap chains by hand at the SMA bulkheads, never at the MHF4 connectors.
    - **Safety notes:** An unknown clone may have poor isolation, which lets strong off-air signals from an unselected antenna leak in. Measure before trusting it.
    - **Sources:**
      - https://www.aliexpress.us/item/3256808840783740.html
      - https://www.amazon.com/clp/B0F63XF4K6
      - https://www.amazon.com/Switch-Communication-Electronic-Component-Portable/dp/B0D4YNYYKC
  3.
    - **Name:** I2C GPIO expander for RF control (PCF8574- or MCP23017-class breakout) plus a 74LVC/74HC buffer
    - **Category:** Control interface
    - **Purpose in lab:** Gives push-pull control lines for the switches (2-3 each), the PE4302 attenuator (6 lines) and the LNA load-switch enables and FAULT inputs (TPS2553), without using up the few free header pins.
    - **Key specs:** 8 lines (PCF8574) or 16 lines (MCP23017); 3.3 V. Silicon Chip used a PCF8574 piggyback plus a 74HC367 buffer for exactly this PE4302 module.
    - **Size weight power:** A small breakout board using milliwatts. Price, size and current not verified.
    - **Interface and linux:** The mainline kernel drivers gpio-pcf857x and pinctrl-mcp23s08, bound through a device-tree overlay, expose a gpiochip, so the same libgpiod and rfsel scripts work. Put it on a different I2C bus from the BNO085, which clock-stretches (mainline DTS enables i2c0, i2c2 and i2c6).
    - **Price:** Not verified (commodity breakout).
    - **Availability:** Commodity part.
    - **Tier:** extended
    - **Integration notes:** The Q6A header GPIOs pass through weak auto-direction 1.8-to-3.3 V translators (UM3204H/UM3304, schematic v1.21). The PE4302 module's 10 kOhm pull-downs load its control pins, so drive them from the expander or a buffer, not straight from the header.
    - **Cheaper alternative:** Direct header GPIOs for the switch only; the ZSWA4's 100 kOhm pull-downs are a light load.
    - **Safety notes:** None.
    - **Sources:**
      - https://siliconchip.com.au/Issue/2018/June/El+Cheapo+Modules+17%3A+4GHz+digital+attenuator
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
  4.
    - **Name:** PE4302 digital step attenuator module (0-31.5 dB, 0.5 dB steps)
    - **Category:** Programmable attenuator
    - **Purpose in lab:** Scriptable attenuation for the 3 dB overload test with no re-cabling, gain-staging sweeps, and conducted MDS/sensitivity tests (Procedure 7).
    - **Key specs:** 1 MHz-4 GHz, 6-bit, 0-31.5 dB in 0.5 dB steps, 50 ohm. Silicon Chip measurements: 0 dB-setting loss about 1-1.5 dB below 2.5 GHz and about 3.5 dB at 4 GHz; accuracy good to about 1.5 GHz and worse above. The module is hard-wired for parallel control (serial disabled). The PE4302 chip is obsolete; the PE4312 is its pin-compatible replacement.
    - **Size weight power:** PCB 33 x 24.5 mm with edge SMA connectors. Silicon Chip's module runs from 3.3 V; some listings say DC 5 V, so check your board. Current draw not verified.
    - **Interface and linux:** 6 parallel lines with 10 kOhm pull-downs. Drive them through the I2C expander and buffer; set with gpioset or python gpiod.
    - **Price:** About $11.49 + $6.84 shipping (eBay seller in Shenzhen; listing last updated July 2025); $27.14 (Newegg, shipped from China); about $11 (Banggood, 2018 article).
    - **Availability:** eBay, Newegg, AliExpress (clone boards).
    - **Tier:** extended
    - **Integration notes:** Put it after the LNA (after 38-41 dB of gain its loss barely affects NF) and before the switch or SDR. Fit an earthed metal shield over the chip, which Silicon Chip found improves high-frequency accuracy. Characterise every setting you use with the VNA (Procedure 1); do not trust the nominal values above 1.5 GHz.
    - **Cheaper alternative:** Nooelec fixed attenuator kit combinations (manual).
    - **Safety notes:** Not a protection device. EEVblog members advise against relying on a step attenuator to protect an input; use fixed pads and a limiter for that.
    - **Sources:**
      - https://siliconchip.com.au/Issue/2018/June/El+Cheapo+Modules+17%3A+4GHz+digital+attenuator
      - https://www.ebay.com/itm/265899138812
      - https://www.newegg.com/p/2S7-090G-01GH3
      - https://eevblog.com/forum/rf-microwave/digital-step-attenuator-pe4302-anybody
  5.
    - **Name:** Fixed attenuator set: Nooelec SMA Attenuator Kit (1, 2, 3, 6, 10, 20 dB) plus 2x Mini-Circuits VAT-10W2+
    - **Category:** Attenuators
    - **Purpose in lab:** Gain staging, the 3 dB pad test, the 10-12 dB protective pads after each 38-41 dB SAWbird on the Lime ports (from the rf_frontend audit), and 40-60 dB of padding in front of any LNA during conducted tests.
    - **Key specs:** Nooelec: DC-6 GHz, +/-0.1 dB (DC-3 GHz), +/-0.4 dB (DC-6 GHz), 2 W; the six pads give 1-42 dB in 1 dB steps (connector genders not stated). VAT-10W2+: 10 dB, DC-6000 MHz, SMA (power rating not on the store page).
    - **Size weight power:** Passive inline SMA barrels; no power.
    - **Interface and linux:** None.
    - **Price:** Nooelec kit $47.95; VAT-10W2+ $31.43 each (qty 1-4).
    - **Availability:** Nooelec ships in 1 business day (no stock count shown). Mini-Circuits lists over 1,000 VAT-10W2+; DigiKey 165.
    - **Tier:** core
    - **Integration notes:** Keep the two VAT-10W2+ permanently on the Lime ports. The Nooelec six-pack is the bench set. Label every pad with its measured S21 at band centres (Procedure 1).
    - **Cheaper alternative:** Generic AliExpress 2 W 6 GHz SMA pads (price not verified). Accept them only after a VNA check.
    - **Safety notes:** Two or more pads in series in front of an LNA are mandatory whenever an instrument generator is used (conducted tests only).
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/attenuator-bundle.html
      - https://www.minicircuits.com/WebStore/dashboard.html?model=VAT-10W2%2B
  6.
    - **Name:** DC-block kit: 2x Mini-Circuits BLK-89-S+ (or Nooelec SMA In-Line DC Block)
    - **Category:** Bias-tee and DC-block kit
    - **Purpose in lab:** Keeps SAWbird USB or header power and LNB 13/18 V off SDR inputs, instrument ports and switch ports. Also protects VNA and tinySA ports during LNA measurements.
    - **Key specs:** BLK-89-S+: 0.1-8000 MHz, +50 V DC maximum, 4 W RF maximum at 25 C, SMA-F to SMA-M. Nooelec: 50 kHz-8 GHz, 50 V, 2 W, loss under 0.3 dB below 6 GHz (under 0.8 dB below 8 GHz), VSWR under 1.2 below 6 GHz.
    - **Size weight power:** BLK-89-S+ is a barrel about 30 mm long (datasheet outline 1.18 in); passive.
    - **Interface and linux:** None.
    - **Price:** BLK-89-S+ $20.26 (qty 1-4); Nooelec $24.95.
    - **Availability:** Mini-Circuits lists over 1,000 (DigiKey showed 0); Nooelec ships in 1 business day.
    - **Tier:** core
    - **Integration notes:** The rf_frontend audit already uses the bias-tee injector's RF port as the DC block in each chain. These two are for the bench: one permanently on the VNA or tinySA port, one spare. Use the Nooelec one (50 kHz) below 100 kHz.
    - **Cheaper alternative:** Generic SMA DC blocks (price not verified); VNA-check them at 137 MHz, where cheap blocks can be lossy.
    - **Safety notes:** Lime RX ports already have 510 pF DC blocks and ESD8472 TVS diodes (5.3 V stand-off, 7-12 V breakdown), so they tolerate 5 V but conduct above about 7 V. Never let 13/18 V reach them.
    - **Sources:**
      - https://www.minicircuits.com/WebStore/dashboard.html?model=BLK-89-S%2B
      - https://www.minicircuits.com/pdfs/BLK-89-S+.pdf
      - https://www.nooelec.com/store/sdr/sdr-addons/dc-block.html
  7.
    - **Name:** Bias-tee kit: 3x generic 10 MHz-6 GHz SMA bias tees plus 1x Mini-Circuits ZFBT-4R2GW+ reference/LNB injector
    - **Category:** Bias-tee and DC-block kit
    - **Purpose in lab:** GPIO-switched 5 V into each LNA on the Lime side (the Lime has no bias tee) and 13.4/18.2 V into the QO-100 LNB. The ZFBT also serves as the known-good reference when qualifying the cheap tees.
    - **Key specs:** ZFBT-4R2GW+: 0.1-4200 MHz; insertion loss 0.6 dB typical / 1.2 dB max (1-2100 MHz); RF-to-DC isolation 40 dB typical; DC resistance 4.5 ohm; specs guaranteed to +20 dBm RF and 200 mA. Absolute maximums: 30 V and 500 mA at the DC port, +30 dBm input. Ports: RF SMA-F (DC-blocked), RF&DC SMA-M, DC SMA-F. Generic tees: the rf_frontend audit found 3-7 dB loss at 100-200 MHz, so use them only at 740 MHz and above after a VNA sweep.
    - **Size weight power:** Passive. The DC feed comes from a TPS2553 load switch with a polyfuse (from the rf_frontend design).
    - **Interface and linux:** Bias on/off through the TPS2553 EN (GPIO); FAULT goes to a GPIO input (libgpiod).
    - **Price:** ZFBT-4R2GW+ $111.57 (qty 1-4). Generic tees about $5-10 each (rf_frontend figure, not re-verified).
    - **Availability:** Mini-Circuits lists over 100 ZFBT (DigiKey showed 0).
    - **Tier:** core
    - **Integration notes:** Use the ZFBT as the LNB injector: LNB on the RF&DC port through an F-SMA adapter, 13.4/18.2 V regulated supply on the DC port (30 V maximum is fine), RF port toward the VLF-1000+, switch and Lime. VHF chains keep using the RTL's own 4.5 V/180 mA tee or the Flamingo+ pass-through.
    - **Cheaper alternative:** Generic tees for every position, including the LNB, after a VNA check at 740 MHz.
    - **Safety notes:** Never leave bias on into a 50 ohm load or a shorted antenna: 4.5 V into 50 ohm is 90 mA and 0.4 W.
    - **Sources:**
      - https://www.minicircuits.com/WebStore/dashboard.html?model=ZFBT-4R2GW%2B
      - https://www.minicircuits.com/pdfs/ZFBT-4R2GW+.pdf
  8.
    - **Name:** 50 ohm terminations: 3x Mini-Circuits ANNE-50+
    - **Category:** Terminations / dummy loads
    - **Purpose in lab:** Reference port on each switch (RF4, the power-on default), terminated-floor measurements on the RTL and the Lime, a 290 K source for Procedure 7, and terminating unused splitter or filter ports.
    - **Key specs:** SMA-M, 50 ohm, DC-18 GHz. Power rating not on the store page.
    - **Size weight power:** Small SMA cap; passive.
    - **Interface and linux:** None.
    - **Price:** $14.84 each (qty 1-4).
    - **Availability:** Mini-Circuits lists over 1,000 (DigiKey showed 0).
    - **Tier:** core
    - **Integration notes:** Not a calibration standard (its return loss is not characterised here); use the OSL kit loads for VNA calibration.
    - **Cheaper alternative:** The load from a generic NanoVNA OSL kit.
    - **Safety notes:** Turn the bias tee off before terminating a bias-fed input (power rating unverified).
    - **Sources:**
      - https://www.minicircuits.com/WebStore/dashboard.html?model=ANNE-50%2B
  9.
    - **Name:** Filter bank, core part (already in the stack): Nooelec Flamingo+ FM, RTL-SDR Blog FM bandstop, SAWbird+ NOAA (137 MHz), SAWbird+ GOES (1688 MHz), Uputronics 435 MHz CubeSat SAW preamp
    - **Category:** Filter bank
    - **Purpose in lab:** Per-band preselection. The Lime has no preselection and shows FM and LTE images, and the V4L has no built-in notch. These parts are the lab's swap-in filters for overload diagnosis (Procedure 4).
    - **Key specs:** Flamingo+ FM: 0.5 dB typical / 1.2 dB max passband loss, passes 250 mA DC or more, +18 dBm max input. RTL-SDR Blog FM bandstop: more than 50 dB rejection, under 0.5 dB loss below 1 GHz, DC pass confirmed at 80 mA or more. SAWbird+ NOAA: 41 dB, 2.6 MHz 3 dB bandwidth, NF 1.1 dB, 170 mA. SAWbird+ GOES: 38 dB, 70 MHz 3 dB bandwidth, NF 1.2 dB, 140 mA, 0 dBm max input. Uputronics 435: 19 dB or more, about 0.75 dB NF, 30 MHz SAW centred at 440 MHz.
    - **Size weight power:** Inline metal-cased modules. LNA currents as listed.
    - **Interface and linux:** LNA bias switched by GPIO through TPS2553 (see the bias-tee item).
    - **Price:** Flamingo+ FM $24.95; RTL-SDR Blog FM bandstop $16.95; SAWbird+ NOAA $44.95 barebones / $49.95 enclosed; SAWbird+ GOES $44.95 barebones / $49.95 enclosed; Uputronics 435 EUR 47.64 incl. VAT (Kubii, stock uncertain).
    - **Availability:** Prices as given in the rf_frontend audit and on the Nooelec listing pages, Oct 2026.
    - **Tier:** core
    - **Integration notes:** Use Flamingo+ as a plug-in pre-filter in front of any LNA at strong-FM sites. The rf_frontend audit notes that LTE Band 3 uplink (1710+ MHz) falls inside the SAWbird GOES passband; it cannot be filtered out, so rely on the 10 dB pad and low gain.
    - **Cheaper alternative:** Nooelec Distill:FM Barebones broadcast-FM bandstop, $17.95.
    - **Safety notes:** None.
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/flamingo-plus-fm.html
      - https://www.nooelec.com/store/sdr/sdr-addons/distill-fm-broadcast-fm-filter.html
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird-plus-goes.html
      - https://www.rtl-sdr.com/new-products-in-our-store-wideband-lna-spare-metal-v3-enclosures/
      - https://kubii.com/en/network-modules/3349-lna-amplifier-modules-with-saw-filter-and-single-frequency-3272496306646.html
  10.
    - **Name:** sysmocom cf2235-kt30 S-band cavity band-pass filter (2170-2300 MHz)
    - **Category:** Filter bank
    - **Purpose in lab:** S-band (2.2-2.3 GHz) preselection on the Lime RX-W. Rejects the 2.1 GHz cellular downlink and helps against 2.4 GHz Wi-Fi.
    - **Key specs:** Passband 2170-2300 MHz; insertion loss 1.0 dB or less; at least 30 dB rejection below 2160 MHz.
    - **Size weight power:** 124 x 47 x 33 mm, 186 g, indoor-rated; passive.
    - **Interface and linux:** None.
    - **Price:** EUR 65.45 (VAT status unclear).
    - **Availability:** sysmocom ships by UPS only, weekly. Check that your destination is served.
    - **Tier:** extended
    - **Integration notes:** Mount it after the LNA V2 in the S-band chain (move it in front only if a site survey shows LNA overload). Too big for the case interior; carry it on the antenna boom or in the kit pouch.
    - **Cheaper alternative:** None verified that is narrow enough. Mini-Circuits ZX75BP-2250-S+ is rejected as too wide.
    - **Safety notes:** None.
    - **Sources:**
      - https://shop.sysmocom.de/S-Band-cavity-filter-2170-2300-MHz/cf2235-kt30
      - https://www.sysmocom.de/downloads/rf_filter_cf2235-kt30.pdf
  11.
    - **Name:** Mini-Circuits VLF-1000+ LTCC low-pass filter (DC-1000 MHz)
    - **Category:** Filter bank
    - **Purpose in lab:** Removes 1.8/2.1 GHz LTE, 2.4 GHz Wi-Fi and USB 3 noise from the Lime RX-L when it handles 435 MHz or the 740 MHz QO-100 IF. Also serves as a general-purpose roofing filter for bench tests below 1 GHz.
    - **Key specs:** DC-1000 MHz LTCC low-pass, 50 ohm, SMA, case style FF704. The store page does not give loss or rejection figures, so read the datasheet and S-parameters.
    - **Size weight power:** FF704 case: the same body style as the VLM-33-S+, about 36 mm long. Passive.
    - **Interface and linux:** None.
    - **Price:** $33.81 (qty 1-4).
    - **Availability:** Mini-Circuits lists over 1,000; DigiKey 50.
    - **Tier:** extended
    - **Integration notes:** Sweep it to the VNA's upper limit. LTCC filters can have spurious passbands far above cutoff (general behaviour, not checked for this part).
    - **Cheaper alternative:** The SAW in the Uputronics 435 preamp already band-limits the 70 cm path; skip the LPF there.
    - **Safety notes:** None.
    - **Sources:**
      - https://www.minicircuits.com/WebStore/dashboard.html?model=VLF-1000%2B
  12.
    - **Name:** Nooelec Ham Filter Bank Barebones (2 m / 1.25 m / 70 cm / 33 cm / 23 cm band-pass plus pass-through)
    - **Category:** Filter bank
    - **Purpose in lab:** Swap-in VHF/UHF preselector for the unfiltered Lime or for bench comparisons at 2 m and 70 cm. It does not cover 137 MHz.
    - **Key specs:** Passbands 144-148, 220-225, 420-450, 902-928 and 1240-1300 MHz plus pass-through. Nooelec's page does not state how the filter is selected, the insertion loss, the rejection or the size.
    - **Size weight power:** Powered: 3-5 V over the SMA output (bias tee) or 3.3-5.5 V on micro-USB or a barrel connector (adapter included). A pushbutton enables 4.5 V bias at the input SMA. Current not stated.
    - **Interface and linux:** No host control documented.
    - **Price:** $66.95
    - **Availability:** Nooelec; ships in 1 business day (no stock count shown).
    - **Tier:** optional
    - **Integration notes:** Characterise insertion loss and rejection with the VNA before use. Disable the input bias pushbutton unless an LNA is connected there.
    - **Cheaper alternative:** Uputronics 435 (70 cm) plus the FM bandstop (2 m), both already owned.
    - **Safety notes:** Its input bias feature can push 4.5 V into an antenna; keep it off with DC-shorted antennas.
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/ham-filter-bank.html
  13.
    - **Name:** LNA bank (already in the stack) plus 1 spare RTL-SDR Blog Wideband LNA V2
    - **Category:** LNA bank
    - **Purpose in lab:** Substitution tests (LNA A vs B with Procedure 5), the S-band chain LNA, and a known-good spare for field failures caused by ESD.
    - **Key specs:** Existing: SAWbird+ NOAA, SAWbird+ GOES, 2x LNA V2, Uputronics 435 (see the filter bank item). Spare LNA V2: Qorvo QPL9547, 100 MHz-6 GHz, NF under 1 dB, 3-5 V bias. Board-level P1dB not published.
    - **Size weight power:** Small metal enclosure; about 150 mA or less (measure the real draw, per the rf_frontend audit).
    - **Interface and linux:** Bias switched by GPIO through TPS2553.
    - **Price:** $19.95 (spare)
    - **Availability:** RTL-SDR Blog store (208 in stock when the rf_frontend audit checked).
    - **Tier:** core
    - **Integration notes:** Measure its gain once with Procedure 7 (conducted, low level), since no board-level curve is published.
    - **Cheaper alternative:** None; this is already the cheapest verified part.
    - **Safety notes:** Discharge antennas before connecting. Put a 100-160 mA polyfuse in each bias feed.
    - **Sources:**
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
      - https://www.rtl-sdr.com/new-products-in-our-store-wideband-lna-spare-metal-v3-enclosures/
  14.
    - **Name:** Hydrogen-line add-on: Nooelec SAWbird+ H1 plus Mini-Circuits VBFZ-1400-S+
    - **Category:** LNA bank / filter bank
    - **Purpose in lab:** Adds 1420 MHz neutral-hydrogen radio astronomy (passive reception). Detectability with antennas inside the 35 cm rule is unverified.
    - **Key specs:** SAWbird+ H1: 1420 MHz, 65 MHz band-pass region, at least 40 dB gain, NF about 0.8 dB, 120 mA nominal, 3-5.5 V (bias tee, micro-USB or header). VBFZ-1400-S+: 1350-1450 MHz band-pass, SMA; loss not on the page.
    - **Size weight power:** SAWbird metal case at 120 mA; the VBFZ is passive.
    - **Interface and linux:** Bias by GPIO. Software: SDR++ or GNU Radio spectral integration.
    - **Price:** SAWbird+ H1 $49.95; VBFZ-1400-S+ $54.13.
    - **Availability:** Nooelec (ships in 1 business day); Mini-Circuits lists over 100 VBFZ.
    - **Tier:** optional
    - **Integration notes:** The VBFZ goes after the LNA as a second stage when 1.4 GHz interference is present. Feed it through an injector with the RF port toward the SDR (the SAWbird puts DC on its output when externally powered).
    - **Cheaper alternative:** SAWbird+ H1 alone.
    - **Safety notes:** None.
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird-h1.html
      - https://www.minicircuits.com/WebStore/dashboard.html?model=VBFZ-1400-S%2B
  15.
    - **Name:** Mini-Circuits ZFRSC-42-S+ 2-way resistive splitter (DC-4200 MHz)
    - **Category:** Splitter
    - **Purpose in lab:** Same-antenna A/B tests (RTL vs Lime, or two decoders), as the rf_frontend audit requires before moving 137/145.8 MHz to the Lime.
    - **Key specs:** DC-4200 MHz, 2-way resistive, 50 ohm, SMA. Loss and isolation are not on the store page (a resistive 2-way splitter is about 6 dB per path by design). DC pass not stated.
    - **Size weight power:** Passive SMA block.
    - **Interface and linux:** None.
    - **Price:** $78.86
    - **Availability:** Mini-Circuits lists over 100 (DigiKey showed 0).
    - **Tier:** optional
    - **Integration notes:** Always put it after at least 20 dB of LNA gain. Never split before the LNA.
    - **Cheaper alternative:** Time-multiplexed A/B through the SP4T (Procedure 5), at no extra cost.
    - **Safety notes:** Do not pass bias through it.
    - **Sources:**
      - https://www.minicircuits.com/WebStore/dashboard.html?model=ZFRSC-42-S%2B
  16.
    - **Name:** Mini-Circuits VLM-33-S+ limiter (30-3000 MHz)
    - **Category:** RF protection
    - **Purpose in lab:** Permanent insurance on the bench-input port and in front of the Lime whenever an unknown conducted source or test chain is attached.
    - **Key specs:** 30-3000 MHz; 0.23 dB typical loss (0.7 dB max) below +5 dBm; VSWR 1.05; limits over +12 to +30 dBm input; +11.5 dBm typical output while limiting; 2 ns response; 2 W absolute maximum input; SMA-F in, SMA-M out.
    - **Size weight power:** FF704 barrel, about 36 mm long; passive.
    - **Interface and linux:** None.
    - **Price:** $69.60 (rf_frontend audit, Mini-Circuits).
    - **Availability:** Mini-Circuits.
    - **Tier:** extended
    - **Integration notes:** Its leakage (+11.5 dBm) is above the Lime's +10 dBm maximum, so always follow it with a pad of 3 dB or more. On the bench port: limiter, then 20 dB, then the switch. The datasheet gives no DC rating; keep it on the DC-free side.
    - **Cheaper alternative:** The 10-12 dB pads alone (the rf_frontend audit's choice for normal operation).
    - **Safety notes:** Not lightning protection.
    - **Sources:**
      - https://www.minicircuits.com/pdfs/VLM-33-S+.pdf
  17.
    - **Name:** Gas-discharge (GDT) coaxial arrestor, DC-pass: ProXicast ANT-241-002 (or Sectron AO-LA-SMA)
    - **Category:** RF protection
    - **Purpose in lab:** Surge protection only for an antenna left mounted outdoors (for example a fixed base antenna feeding the portable lab).
    - **Key specs:** ANT-241-002: 0-6 GHz; SMA-F to SMA-F bulkhead; DC pass-through; 230 V DC discharge; loss under 0.2 dB; VSWR under 1.2; 200 W. Sectron: 0-6 GHz, SMA-m/SMA-f, 230 V +/-20% DC breakdown, 700 V or less impulse, loss figure 0.5 dB; DC pass not stated.
    - **Size weight power:** ANT-241-002: 61 x 31 mm, 113 g. Sectron: 52.2 x 23 mm.
    - **Interface and linux:** None.
    - **Price:** ANT-241-002 $19.95 (MSRP $31.95); Sectron EUR 16.84 ex VAT / EUR 20.38 incl. 21% VAT.
    - **Availability:** ProXicast: 93 in stock. Sectron: in stock (EU).
    - **Tier:** optional
    - **Integration notes:** Useful only when bonded to a real earth at the cable entry. It passes LNA bias (ANT-241-002), so it can sit ahead of a bias-fed LNA. Not needed for handheld use.
    - **Cheaper alternative:** For handheld use, none: discharge the antenna before connecting (rf_frontend audit) and do not operate in thunderstorms.
    - **Safety notes:** A 230 V GDT does nothing against the few-volt ESD that kills LNAs; that protection comes from diodes or TVS parts (BAV99 at the LNA input, ESD8472 on the Lime). Follow local electrical or earthing codes when installing.
    - **Sources:**
      - https://www.proxicast.com/shopping/ANT-241-002
      - https://eshop.sectron.eu/en/bleskojistka-sma-m-sma-f/p-1371/
  18.
    - **Name:** SMA OSL calibration standards, both genders (Chelegance-type SMA-M OSL plus a generic female set)
    - **Category:** Calibration standards
    - **Purpose in lab:** VNA calibration at the end of the test cables (the reference plane) for all conducted characterisation in Procedure 1.
    - **Key specs:** Chelegance OSL SMA-M: DC-6 GHz; the listing claims load VSWR below 1.025. Generic NanoVNA SMA OSL kits: DC-6 GHz, uncharacterised.
    - **Size weight power:** Small SMA caps; passive.
    - **Interface and linux:** Used with whichever VNA the instruments area picks (e.g. LiteVNA 64, NanoVNA). NanoVNA-Saver and the device firmware handle SOL(T).
    - **Price:** Chelegance about 250 SEK (Limmared; seen in a search result, page not re-fetched). Generic kit about $10 + shipping (eBay; search result).
    - **Availability:** Limmared (EU), eBay.
    - **Tier:** core
    - **Integration notes:** Buy standards of the opposite gender to your cable ends. Cables ending in SMA-M need SMA-F standards. Add an SMA-F to SMA-F barrel as the 'through'.
    - **Cheaper alternative:** The OSL set that ships with most NanoVNA-class instruments.
    - **Safety notes:** The VNA is a signal source. Use it only into cables, standards, pads, filters and LNAs, never into an antenna, at its lowest output setting.
    - **Sources:**
      - https://butik.limmared.nu/en/antenna-analysis/2099-chelegance-osl-calibration-kit-smam-50-ohm.html
      - https://www.ebay.de/itm/283649921796
  19.
    - **Name:** Short characterised cable kit: 4x Mini-Circuits 086-6SM+ hand-flex (15 cm) plus 2x CBL-1FT-SMSM+ precision test cables (0.3 m)
    - **Category:** Cables
    - **Purpose in lab:** Repeatable inter-module jumpers inside the case (switch to pad to pigtail) and stable VNA port cables. Each cable's measured loss goes into the lab's parts table.
    - **Key specs:** 086-6SM+: 0.086 in hand-formable cable, 6.0 in, rated to 18 GHz, SMA. CBL-1FT-SMSM+: precision test cable, 1.0 ft (0.3 m), 18 GHz, SMA.
    - **Size weight power:** Passive.
    - **Interface and linux:** Store measured S21 per cable (e.g. /etc/rflab/parts.yaml) for use by the measurement scripts.
    - **Price:** 086-6SM+ $16.67 each; CBL-1FT-SMSM+ $82.05 each.
    - **Availability:** Mini-Circuits lists over 1,000 (086-6SM+) and over 100 (CBL-1FT; DigiKey 50).
    - **Tier:** core
    - **Integration notes:** The 086-6SM+ are core. The CBL-1FT pair is extended (VNA port cables only). Hand-flex is for fixed routing: bend it once, not repeatedly. Lime-side MHF4L-SMA bulkhead pigtails stay as already planned (Lime $6 + $18 shipping, or Taoglas CAB.S225); buy 2 spares.
    - **Cheaper alternative:** RG316 SMA jumpers (AliExpress, price not verified), each one VNA-measured and labelled.
    - **Safety notes:** None.
    - **Sources:**
      - https://www.minicircuits.com/WebStore/dashboard.html?model=086-6SM%2B
      - https://www.minicircuits.com/WebStore/dashboard.html?model=CBL-1FT-SMSM%2B
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
  20.
    - **Name:** SMA torque wrench, 8 mm (5/16 in), 0.9 N·m break-over (TOJOIN-type), plus an 8 mm open-end spanner
    - **Category:** Tools
    - **Purpose in lab:** Repeatable SMA mating for measurement-grade results; prevents over-torquing PCB-mount SMA jacks on the SAWbirds, LNAs and switch.
    - **Key specs:** 0.9 N·m (8 in-lb), 8 mm opening, break-over type. The Amazon appliedEM listing quotes +/-0.25 in-lb accuracy.
    - **Size weight power:** Hand tool, about 17 cm.
    - **Interface and linux:** None.
    - **Price:** $35.89 on eBay (TOJOIN, 66 sold); open-box $30.71; other listings about $43-53 (search-result prices).
    - **Availability:** eBay, Amazon.
    - **Tier:** core
    - **Integration notes:** 0.9 N·m is for stainless connectors. A NanoVNA-users thread notes the original MIL figure for brass SMA was about 3 in-lb, and that a 0.59 N·m preset wrench sits just below the brass upper limit. For brass parts (cheap adapters, many PCB jacks) use a lower-set or adjustable wrench, or finger-tight. Turn only the coupling nut and hold the body with the spanner.
    - **Cheaper alternative:** Finger-tight plus careful practice. Not recommended for measurements.
    - **Safety notes:** None.
    - **Sources:**
      - https://www.ebay.com/itm/354284038356
      - https://www.amazon.com/SMA-Torque-Wrench-%C2%B7lbs-0-9/dp/B08B548833
      - https://groups.io/g/nanovna-users/topic/sma_torque_wrench/75689254
  21.
    - **Name:** I-PEX 90435-001 MHF 4 mating/unmating tool (and 90609-0001 for MHF 4L)
    - **Category:** Tools
    - **Purpose in lab:** Safe extraction and insertion of the Lime's MHF4 RX/TX leads (rated for only about 30 mating cycles, per the antennas audit).
    - **Key specs:** I-PEX's MHF 4 'Pushing & Pulling JIG'. The I-PEX manual says to lift it vertically from the PCB; angled pulls are prohibited. 90609-0001 is DigiKey's 'MHF 4L Mating/Unmating Tool' (price not checked).
    - **Size weight power:** Stainless-steel hand tool.
    - **Interface and linux:** None.
    - **Price:** $18.10 (DigiKey, 474 in stock); EUR 15.89 (DigiKey EU, antennas audit).
    - **Availability:** DigiKey; Future Electronics quotes about 12 weeks factory lead time.
    - **Tier:** core
    - **Integration notes:** Mate each pigtail once, strain-relieve it, and terminate it on a fixed SMA bulkhead. All lab re-cabling then happens at SMA. Keep a mating-cycle log per Lime port.
    - **Cheaper alternative:** None advisable. Tweezers damage MHF4 plugs.
    - **Safety notes:** None.
    - **Sources:**
      - https://www.digikey.com/en/products/detail/i-pex/90435-001/25819261
      - https://www.i-pex.com/sites/default/files/downloads/pdf/MANUAL_MHF_4_HIM-10003-08EN.pdf
      - https://www.i-pex.com/sites/default/files/downloads/pdf/MANUAL_MHF_4L_HIM-12012-08EN.pdf
  22.
    - **Name:** Purpose-picked adapter set (SMA/N/BNC/F/MMCX), not a 'universal' kit
    - **Category:** Adapters
    - **Purpose in lab:** Connect instruments, the LNB IF (F), any N-type field antenna or BNC gear without stacking adapters.
    - **Key specs:** Suggested set: 2x SMA-M/M and 2x SMA-F/F barrels (one used as the VNA 'through'), 2x SMA right-angle, SMA-F/N-M and SMA-M/N-F, SMA-F/BNC-M and BNC-F/SMA-M, 2x F-F/SMA-M (75 ohm LNB IF; the mismatch is negligible at 740 MHz), 1x MMCX-SMA pigtail, plus 'connector savers' (sacrificial SMA barrels) on frequently used ports. Keep RP-SMA parts in a separate bag; they look the same and do not mate correctly with SMA.
    - **Size weight power:** Passive, about 100-200 g (estimate).
    - **Interface and linux:** None.
    - **Price:** Not verified. The Amazon listings found (e.g. onelinkmore 20-type SMA kit, ConnectoRF 40-piece) showed no prices in the results.
    - **Availability:** Amazon, AliExpress, EU shops.
    - **Tier:** core
    - **Integration notes:** VNA-check one of each type (Procedure 1) and discard any with more than 0.3 dB loss at 2.3 GHz (my threshold). If any module uses U.FL (MHF1), its extraction tool is a different part (not verified here).
    - **Cheaper alternative:** Buy only the SMA barrels and F-SMA adapters now; add N and BNC when needed.
    - **Safety notes:** None.
    - **Sources:**
      - https://www.amazon.com/SMA-Type-Connectors-Kits-Adapter/dp/B06Y5PDJYY
      - https://www.amazon.com/Universal-Coaxial-Connector-Mini-UHF-Adapters/dp/B079K3HQZ8
- **Capabilities added:**
  - Software-selected antenna and front-end routing on each Lime RX port (SP4T, 3.3 V GPIO, about 0.3 mW), scriptable from the pass scheduler, so lab work no longer wears out the 30-cycle MHF4 connectors.
  - An always-available 50 ohm reference port (switch RF4, the power-on default) for terminated-floor and self-noise/EMI surveys before every session (Wi-Fi, HDMI pixel clock, PCIe, USB 3 spurs).
  - Overload and intermod diagnosis with the 3 dB pad test, and gain staging using calibrated pads or a scriptable 0.5 dB step attenuator.
  - Time-multiplexed A/B comparison of antennas or LNAs on the same live pass (receive-only), plus same-antenna RTL-vs-Lime comparison through a resistive splitter.
  - Conducted bench characterisation of every filter, LNA, bias tee, DC block, pad, switch and cable (S21/S11 tables), with a VNA from the instruments area. Generators are conducted only, behind 40-60 dB of pads, never into an antenna.
  - Conducted MDS/sensitivity and approximate system noise-figure measurement against a 290 K termination using a low-level CW source and known attenuation.
  - Per-band preselection for the unfiltered Lime: FM stop, 2 m/70 cm/23 cm bank, 1 GHz low-pass, L-band SAW, S-band cavity, optional 1.4 GHz band-pass.
  - Controlled DC management: GPIO-switched 5 V LNA bias and 13.4/18.2 V LNB bias injected on the antenna side, with DC kept off switches, instruments and the Lime (whose ESD8472 TVS conducts above about 7 V).
  - Input protection: a limiter plus pad on the bench port and the Lime, and an optional GDT surge arrestor for a fixed outdoor antenna.
  - Measurement repeatability: torque-controlled SMA mating, OSL calibration at the cable ends, characterised and labelled cables, a mating-cycle log for MHF4.
  - Optional 1420 MHz hydrogen-line radio astronomy chain (detectability with antennas under 35 cm unverified).
- **Procedures:**
  1.
    - **Name:** P1. Accessory acceptance and cable characterisation (conducted VNA sweep)
    - **Steps:**
      - Disconnect every antenna. Under the receive-only rule the VNA is never connected to an antenna. Warm the VNA up for about 20 minutes and set the lowest output power that gives clean traces.
      - Fit the CBL-1FT-SMSM+ port cables with a DC block on port 1 and torque them (0.9 N·m for stainless; lower for brass). Do a SOLT calibration at the cable ends using OSL standards of the opposite gender plus an SMA-F/F through. Save the calibration.
      - Sweep 50 MHz to the VNA's upper limit. Record S21 and S11 at 137.5, 145.8, 436, 740, 1420, 1700 and 2250 MHz for every pad, DC block, bias tee (RF port to RF&DC port), filter, switch path (each RFx to COM, plus isolation to every other port), splitter path, cable, pigtail and adapter.
      - Acceptance (my thresholds): pads within spec (+/-0.1 dB to 3 GHz for the Nooelec set) plus about 0.2 dB VNA uncertainty. DC blocks and the ZFBT under 0.6-1 dB in use. Generic bias tees rejected for any band where loss exceeds 1 dB (the audit saw 3-7 dB at 100-200 MHz). Switch insertion loss 1.5 dB or less; isolation at least 40 dB below 1 GHz and at least 30 dB at 1.7-2.3 GHz. Filters: record rejection at 88-108, 791-960, 1805-1880, 2110-2170 and 2400-2483 MHz; check the VLF-1000+ far stopband.
      - Check bias tees and the GDT with a multimeter: DC continuity from the DC port to the RF&DC port, and an open circuit from the DC port to the RF port.
      - Label each part with an ID and its measured loss, store the table (e.g. /etc/rflab/parts.yaml under git), and re-measure cables after any damage or every few months.
    - **Needs:**
      - VNA from the instruments area (LiteVNA 64 or NanoVNA class)
      - SMA OSL calibration standards (both genders)
      - CBL-1FT-SMSM+ test cables
      - SMA torque wrench
      - DC-block kit
      - All passives under test
  2.
    - **Name:** P2. Switch-matrix bring-up and Linux control
    - **Steps:**
      - With the switch unpowered, measure resistance COM-RFx and RFx-GND. Treat every port as DC-free whatever the result.
      - Wire the DB-9: Vdd to the header 3.3 V pin, GND, and V1/V2 (plus V3 if you want all-off) to free GPIO lines or I2C-expander lines. Do not use header pins 7, 8/10, 13/15, 16/18 or 22/33/36/37. Find the chip and line names with gpioinfo.
      - Connect the chains: RF1 = 70 cm (LNA, then injector), RF2 = QO-100 IF (LNB, then ZFBT injector, then VLF-1000+), RF3 = bench port (VLM-33-S+, then 20 dB pad), RF4 = ANNE-50+ load. COM goes to the 10 dB pad, then the MHF4L pigtail, then the Lime RX-L.
      - Write 'rfsel' to map names to bits (load=00, 70cm: V1=1 V2=0, qo100: V1=0 V2=1, bench=11), held by one long-running gpiod process. With libgpiod v2: gpioset -c gpiochipN -z V1=1 V2=0. Kill the holder before changing state. Log every change with a timestamp next to the IQ recording.
      - Confirm that a reboot or a crash returns the switch to RF4 (the internal 100 kOhm pull-downs), which leaves the Lime safely on the load.
      - Run the P1 switch sweep, or with the antennas still disconnected, inject a conducted low-level tone into each RFx through 40 dB of pads and read it on the Lime with each other port selected, to get the isolation table. Accept or reject against the P1 thresholds.
    - **Needs:**
      - Mini-Circuits ZSWA4-63DR+ (or an HMC7992 board)
      - DB-9 lead
      - ANNE-50+
      - Bias-tee injectors
      - VAT-10W2+ pads
      - VLM-33-S+
      - I2C GPIO expander (optional)
      - libgpiod / python3 gpiod
      - Multimeter
  3.
    - **Name:** P3. Terminated-floor and self-noise survey (before each session or after any hardware change)
    - **Steps:**
      - Turn every bias tee off (4.5 V into 50 ohm is 0.4 W). Select RF4 (load) on the Lime switches; put an ANNE-50+ on the RTL input.
      - At fixed gain and sample rate, record 30 s at 137.1, 145.8, 436, 740, 1420, 1700 and 2250 MHz.
      - Repeat with Wi-Fi off (nmcli radio wifi off), the HDMI mode changed, the USB 3 NVMe idle vs writing, and the Lime streaming vs idle. Note which spurs move or disappear.
      - Save a per-band spur mask. Spurs that are present with the input terminated are self-generated, not satellite or interference signals.
      - Switch to the antenna chain with its LNA on. The noise floor must rise 6-10 dB above the terminated floor (rf_frontend gain-staging rule); if not, raise the SDR gain or move the LNA to the feed.
    - **Needs:**
      - ANNE-50+ terminations
      - Switch matrix
      - SDR++ or SatDump baseband recorder
  4.
    - **Name:** P4. Gain staging and the 3 dB pad overload test (site survey)
    - **Steps:**
      - With antenna and LNA connected, set the SDR gain so the floor sits 6-10 dB above the terminated floor and the strongest carriers stay below about -10 dBFS.
      - Insert 3 dB between the LNA and the SDR (Nooelec 3 dB pad, or set the PE4302 to 3.0 dB).
      - Real signals drop by about 3 dB. Spurs that drop by clearly more than 3 dB are intermod or overload products generated inside the chain.
      - Fix in this order: FM bandstop in front of the LNA (Flamingo+), band filter (Ham Filter Bank 70 cm, VLF-1000+, cavity), keep the 10 dB Lime pad, lower the SDR gain. Repeat steps 2-3.
      - Record the final chain (filters, pads, gain) per site and per band in the lab log.
    - **Needs:**
      - Nooelec attenuator kit or PE4302
      - Filter bank
      - FM bandstop filters
  5.
    - **Name:** P5. Time-multiplexed A/B comparison of two antennas or LNAs on a live pass (receive-only)
    - **Steps:**
      - Put chain A on switch RF1 and chain B on RF2, each after its own LNA and injector and with the same pad toward the SDR. Take the port-to-port loss difference from P1.
      - Before the pass, record the terminated floor on RF4 and on each chain with its antenna pointed at the sky, away from the satellite.
      - During the pass, record baseband continuously and toggle RF1/RF2 every 5-10 s with rfsel, logging the timestamps.
      - Afterwards, compute carrier or beacon power over floor for each segment, pair segments at matching elevation, and correct for the P1 loss difference. The result is the relative performance in dB.
      - Repeat over 2-3 passes and report the mean and spread. For decode-quality comparisons, which need an uninterrupted signal, use P6 instead.
    - **Needs:**
      - Switch matrix
      - Two receive chains
      - SDR++ or SatDump baseband recording
      - Python/NumPy analysis script
  6.
    - **Name:** P6. Same-antenna RTL-SDR vs Lime comparison with the resistive splitter
    - **Steps:**
      - Antenna to LNA (20 dB or more) to injector to ZFRSC-42-S+; one output to the RTL-SDR, the other through the 10 dB pad to the Lime. Terminate any unused port.
      - Equalise or record the path losses from P1.
      - Record the same pass on both SDRs at the rates SatDump uses for that satellite.
      - Compare decoded SNR, frame counts and Viterbi/BER statistics. The rf_frontend audit's rule: move 137/145.8 MHz to the Lime only if it is within 1-2 dB of the RTL.
    - **Needs:**
      - ZFRSC-42-S+
      - ANNE-50+
      - Attenuators
      - RTL-SDR V4L and LimeSDR Micro
  7.
    - **Name:** P7. Conducted MDS / approximate noise-figure test with a low-level CW source
    - **Steps:**
      - Disconnect every antenna and switch all unused ports to their loads. Nothing in the setup may be connected to an antenna.
      - Generator (instruments area, lowest output setting) to at least 50 dB of fixed pads (Nooelec 20+10+6 plus 2x VAT-10W2+) to the PE4302 to a DC block to the LNA input. The LNA is powered through its injector on the output side. Then the SDR.
      - From the P1 values, work out the level at the LNA input (Pgen minus all attenuation) and start below -60 dBm, far under the SAWbird+ GOES 0 dBm maximum input.
      - In SDR++ with a fixed FFT, raise the level in 0.5 dB steps until the tone sits 3 dB above the floor (S = N). Record P_MDS in dBm.
      - Approximate NF = P_MDS + 174 - 10*log10(ENBW in Hz). The pads present a 290 K source, so the estimate is valid; its accuracy is limited by pad tolerances and the ENBW estimate.
      - Repeat with the LNA bypassed (SDR alone) and at several gain settings. Disconnect the generator first when finished.
    - **Needs:**
      - Low-level signal generator (conducted only)
      - Nooelec attenuator kit plus VAT-10W2+
      - PE4302
      - DC block
      - ANNE-50+
      - Parts table from P1
  8.
    - **Name:** P8. Connector care: torque, MHF4 handling, mating-cycle log
    - **Steps:**
      - Inspect the connector faces and pins; reject bent pins and debris.
      - Align the connectors and thread the nut by finger. Hold the body with the 8 mm spanner and turn only the nut. Finish with the torque wrench (0.9 N·m stainless, lower for brass).
      - Put connector-saver barrels on frequently used ports (instrument ports, bench bulkhead) and replace them when they wear.
      - MHF4: slide the I-PEX 90435-001 jig on from the cable side up to its stop and lift vertically, never at an angle. Note each mating in the port log, since MHF4 is rated for about 30 cycles.
      - Never re-cable at an MHF4 for a test; use the switch or the SMA bulkheads.
    - **Needs:**
      - SMA torque wrench
      - 8 mm spanner
      - I-PEX 90435-001 / 90609-0001
      - Adapter set (barrels)
  9.
    - **Name:** P9. Optional: surge protection for a fixed outdoor antenna
    - **Steps:**
      - Fit the ANT-241-002 GDT where the coax enters the building or shelter, and bond it with a short heavy conductor to an earth that meets the local electrical code.
      - Check DC pass: measure LNA current through the arrestor with bias on.
      - Check its loss with the VNA (spec under 0.2 dB) at the band in use.
      - Keep the BAV99 or TVS protection at the LNA input; the GDT does not stop ESD.
      - Disconnect and stow antennas before thunderstorms, and replace the GDT after any strike.
    - **Needs:**
      - ProXicast ANT-241-002 or Sectron AO-LA-SMA
      - Earthing hardware
      - Multimeter
      - VNA
- **Rejected:**
  1.
    - **Name:** Mini-Circuits USB-SP4T-63 (USB-controlled SP4T, 1-6000 MHz)
    - **Why:** $602.65 with 0 in stock. It would take one of the Q6A's few USB ports (the three USB 2.0 ports share a hub with Wi-Fi). It has good Linux support (Mini-Circuits API for Linux, 30-80 mA from USB, built-in DC blocking), but the GPIO-driven ZSWA4-63DR+ covers the same range for half the price and no USB port. Fine for a home bench PC.
  2.
    - **Name:** Mini-Circuits ZFSWA2-63DR+ SPDT
    - **Why:** 500-6000 MHz only, so it misses 137, 145.8 and 435 MHz. $159.81.
  3.
    - **Name:** HMC241-based SP4T boards
    - **Why:** ADI's Japanese product page lists HMC241 as discontinued (search result; the English page returned 503). AliExpress boards are unmeasured clones or old stock, need 5 V and external DC blocks. Use the ZSWA4 or a qualified HMC7992 board instead.
  4.
    - **Name:** Surplus electromechanical SMA coaxial relays (e.g. Radiall R514373427 SP4T DC-6 GHz on eBay, sold out)
    - **Why:** Surplus only. Coil voltage and current not verified (typically higher-voltage coils), heavy, and shock-sensitive in a handheld. Fine for a fixed bench.
  5.
    - **Name:** Mini-Circuits ZVBP-435-S+ cavity band-pass (425-445 MHz, 0.9 dB, 80 dB rejection)
    - **Why:** $802.45 and too large. The Uputronics 435 SAW preamp plus the VLF-1000+ does the job.
  6.
    - **Name:** Mini-Circuits ZX75BP-2250-S+ (2000-2500 MHz ceramic band-pass, $121.88)
    - **Why:** Too wide: it passes the 2110-2170 MHz cellular downlink and 2.4 GHz Wi-Fi. The sysmocom cf2235-kt30 is narrower and cheaper.
  7.
    - **Name:** Dedicated SMA 'LTE notch' filter
    - **Why:** No verified SMA notch found for the bands that matter. LTE Band 3 uplink (1710-1785 MHz) sits directly above the 1698-1707 MHz HRPT band, so a notch would also cut the wanted signal. Elsewhere, band-pass parts (cavity, SAW, LPF) give the rejection. TV-antenna '5G/LTE' F-type low-pass filters are a cheap category but were not verified here.
  8.
    - **Name:** Nooelec SAWbird+ iO / IR and the Inmarsat / Iridium antenna bundles
    - **Why:** Built for commercial satellite communications services, which are out of scope under the project rules.
  9.
    - **Name:** Nooelec LaNA Barebones (20 MHz-4 GHz, $32.95)
    - **Why:** Pre-order, and it duplicates the role of the RTL-SDR Blog LNA V2 already in the stack.
  10.
    - **Name:** Name-brand SMA torque wrenches (Fairview ST-SMA8 $689-854 on DigiKey; L-com LC-TWC08516 NZ$643.51)
    - **Why:** About 20 times the price of a break-over 0.9 N·m wrench, with no benefit at this lab's accuracy level.
  11.
    - **Name:** Professional calibration kits (Megiq SMA-CAL-6F about GBP 555 ex VAT; Tekbox TBVC-SM6 EUR 475 ex VAT)
    - **Why:** Their accuracy exceeds what NanoVNA/LiteVNA-class instruments can use. Reconsider only if a better VNA is bought.
  12.
    - **Name:** LibreCAL 4-port eCal (9 kHz-6 GHz)
    - **Why:** Documented support is LibreVNA-GUI and SCPI scripts only; price and availability not verified.
  13.
    - **Name:** 'Universal' 40-piece interchangeable-centre adapter kits (e.g. ConnectoRF on Amazon)
    - **Why:** Mostly irrelevant types (UHF, mini-UHF, RCA), price not shown, and stacked adapters add loss and mismatch. Buy direct SMA adapters.
  14.
    - **Name:** VLM-33-S+ as the only protection on the Lime
    - **Why:** Its +11.5 dBm leakage is above the Lime's +10 dBm maximum, so it must always be followed by a pad.
  15.
    - **Name:** Using the LimeSDR Micro TX port as a test-signal source
    - **Why:** It is a transmitter, and the lab is receive-only. If a test signal is needed, use a low-output instrument generator, conducted only, behind 50 dB or more of pads.
- **Notes:** RULES APPLIED: Nothing in this kit transmits. The VNA and signal generator come from the instruments area and are used only for conducted tests into cables, pads, filters, LNAs and loads: lowest output setting, 40-60 dB of pads in front of any LNA, all antennas disconnected and every switch port parked on a load. Never connect a VNA or generator to an antenna (that includes antenna SWR sweeps). Legal: reception and use of received data, surge-arrestor installation (electrical and earthing codes) and import of RF parts all depend on the country. Check local rules; no country-specific claims are made. Commercial satellite communications (Inmarsat, Iridium) are deliberately excluded.
  
  COST (USD, Mini-Circuits and Nooelec store prices on 18 Oct 2026, before shipping and VAT):
  - Core new purchases about $284 (Nooelec attenuator kit 47.95, 2x BLK-89-S+ 40.52, 3x ANNE-50+ 44.52, 4x 086-6SM+ 66.68, torque wrench 35.89, I-PEX 90435-001 18.10, spare LNA V2 19.95, generic OSL kit about 10). Add the Chelegance OSL kit (about 250 SEK) and the adapter set (price not verified). Generic bias tees are already counted in the rf_frontend small-parts budget.
  - Extended about $768 plus EUR 65.45: ZSWA4-63DR+ 307.32, PE4302 about 18.33 delivered, ZFBT-4R2GW+ 111.57, VLF-1000+ 33.81, VLM-33-S+ 69.60, 2x CBL-1FT-SMSM+ 164.10, 2x VAT-10W2+ 62.86, sysmocom cavity EUR 65.45; I2C expander price not verified.
  - Optional about $270: ZFRSC-42-S+ 78.86, Ham Filter Bank 66.95, SAWbird+ H1 49.95, VBFZ-1400-S+ 54.13, ANT-241-002 19.95; a second HMC7992 switch, price not verified.
  DigiKey often showed 0 stock when the Mini-Circuits store had stock. The ZSWA4-63DR+ itself showed 0 stock, so ask Mini-Circuits for a lead time or start with an HMC7992 board.
  
  FIT, POWER, THERMAL: Only the switch (51x38x15 mm), PE4302 (33x24.5 mm PCB), the permanent pads and the DC blocks go inside the ASA case, on the aluminium mid-plate. Everything else lives in a kit pouch; its weight is not estimated, since most item weights are unpublished. Added power is negligible (ZSWA4 0.1 mA at 3.3 V). LNA currents are unchanged from the rf_frontend budget. No new heat source.
  
  GPIO BUDGET: Each switch needs 2-3 lines and the PE4302 needs 6; add the LNA TPS2553 enables and FAULT lines. That is more than the free header pins once pins 7, 8/10, 13/15, 16/18 and 22/33/36/37 are excluded, hence the I2C expander, on a bus other than the BNO085's. The header's weak auto-direction translators are another reason to buffer the PE4302's 10 kOhm pull-downs.
  
  UNVERIFIED (check on arrival):
  - AliExpress and Amazon HMC7992 board prices and specs (pages blocked); HMC7992 logic levels (ADI site returned 503).
  - PE4302 board supply voltage (3.3 V vs 5 V variants).
  - Ham Filter Bank selection method, insertion loss and size.
  - Power ratings of the ANNE-50+ and VAT-10W2+.
  - DC pass of the ZFRSC-42-S+ and of the Sectron GDT; DC handling of the VLM-33-S+.
  - Adapter-kit and generic bias-tee prices.
  - Chelegance and eBay cal-kit prices (seen only in search results).
  - MHF4L-plug to MHF4-jack compatibility (antennas audit flag).
  About 11 WebSearch calls were used; the remaining facts come from WebFetch of manufacturer pages and datasheets, plus the audited input files (rf_frontend, compute, gnss_imu, antennas).

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

## small:ku_qo100 (run `wf_41027870-8e7`)

- **Band group:** Ku / 10-12.75 GHz: QO-100 (Es'hail-2, 25.9°E) narrowband and wideband downlinks at 10.489-10.499 GHz, plus other geostationary Ku signals. Antennas: a bare LNB with its own feed (strict tier) and small conical horns on the LNB (strict at 12 cm or less, small tier up to about 15 x 18 cm). Receiver: Bullseye TCXO LNB, then the RTL-SDR V4L at the 739.5-740 MHz IF.
- **Small antennas:**
  1.
    - **Name:** Othernet Bullseye TCXO LNB used bare, with no reflector (current stack part)
    - **Type:** buy
    - **Band:** Input 10489-12750 MHz; LO 9750/10600 MHz; QO-100 narrowband IF 739.5-740 MHz
    - **Size cm:** About 6 cm feed by about 11-14 cm long. This is a typical single-LNB size; the rtl-sdr.com page gives no dimensions. 40 mm collar.
    - **Gain or efficiency:** About 9-12 dBi (estimate; no measured datasheet value), beamwidth about 40-50°. NF 0.5 dB, gain 50-66 dB. Stability ±10 kHz at 23°C, ±30 kHz from -20 to 60°C.
    - **Price:** $29.95, 70 in stock (rtl-sdr.com, read 18 Oct 2026)
    - **Availability incl ukraine:** rtl-sdr.com store only. Not found in Ukrainian shops; shipping to Ukraine not verified.
    - **Sources:**
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
      - http://ok1dx.cz/techinfo/qo100/qo100.html
      - https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
  2.
    - **Name:** QRO.cz / RemoteQTH QO-100 LNB with 0.2 ppm TCXO (or 10 MHz external-reference version), used bare
    - **Type:** buy
    - **Band:** 10.489 GHz QO-100; IF 739 MHz
    - **Size cm:** Palm-sized LNB (dimensions not published)
    - **Gain or efficiency:** Same feed class, about 9-12 dBi (estimate). TCXO about ±1 kHz after 5 min warm-up (about 10x better than Bullseye). Rated 11-15 V, about 400 mA (about 5 W); never feed 18 V. WiMo lists 12 V = H, 15 V = V; the vendor documents disagree.
    - **Price:** From €65 incl. VAT plus €54.62 shipping (WiMo), about €120 delivered. External-reference dual-LO version €199 ex VAT (hamparts.shop).
    - **Availability incl ukraine:** EU (WiMo, hamparts.shop). Shipping to Ukraine not verified.
    - **Sources:**
      - https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz
      - https://hamparts.shop/blog/lnb-dual-lo-ref-manual.html
  3.
    - **Name:** Local universal linear 'Single' TV LNB (e.g. Eurosky 107A Single Universal, Sat-Integral T-011 Single), used bare
    - **Type:** buy
    - **Band:** 10.7-12.75 GHz specified. 10.489 GHz is below the spec, but plain LNBs have received QO-100 (OK1DX).
    - **Size cm:** Palm-sized, 40 mm collar
    - **Gain or efficiency:** About 9-12 dBi feed (estimate). LO stability not stated (PLL or DRO unknown); plain LNBs are reported 50-180 kHz off or more. For QO-100 narrowband it is usable only with the wide-acquisition beacon tracker. Fine as a finder, as a test unit for cutting horns, and for Ku TV-carrier experiments. Avoid 'circular' models.
    - **Price:** 104 UAH (Eurosky 107A), 111-121 UAH (Sat-Integral T-011), in stock on Prom.ua. The Inverto IDLP-SNL410 PLL at 219 UAH was listed but unavailable. EU alternative: Goobay 67269 PLL at €5.90 ex VAT (Passion Radio, not re-checked).
    - **Availability incl ukraine:** Ukraine, Prom.ua: 'Готово до відправки' (ready to ship), 18 Oct 2026
    - **Sources:**
      - https://prom.ua/ua/search?search_term=%D0%BA%D0%BE%D0%BD%D0%B2%D0%B5%D1%80%D1%82%D0%B5%D1%80%20single%20%D1%81%D1%83%D0%BF%D1%83%D1%82%D0%BD%D0%B8%D0%BA%D0%BE%D0%B2%D0%B8%D0%B9
      - https://passion-radio.com/lnb-pll/universal-goobay-1154.html
      - http://ok1dx.cz/techinfo/qo100/qo100.html
  4.
    - **Name:** DIY clamp-on conical cone, 10 cm mouth (strict tier)
    - **Type:** diy
    - **Band:** 10.49 GHz (works across 10-12.75 GHz with gain scaling as f²)
    - **Size cm:** Calculated: 10.0 cm mouth, about 6.3 cm long from the 40 mm LNB collar (11.7 cm slant from apex). Overall about 17-20 cm with the LNB body.
    - **Gain or efficiency:** About 18.0 dBi (calculated: optimum conical horn, efficiency 0.52, slant length = D²/3λ, λ = 28.6 mm). Beamwidth about 20°. Expected +6 to +9 dB over the bare LNB; check with a same-day A/B beacon test. Mating to the LNB's scalar feed is not proven (±2 dB).
    - **Price:** About $3-10 (aluminium flashing or tinplate, rivets, aluminium tape; or a PETG print covered in copper tape)
    - **Availability incl ukraine:** Local hardware-store sheet metal and tape; 3D print
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap2.pdf
  5.
    - **Name:** DIY conical horn, 12 cm mouth (largest strict-tier horn)
    - **Type:** diy
    - **Band:** 10.49 GHz
    - **Size cm:** Calculated: 12.0 cm mouth by 10.5 cm long on the 40 mm collar (13.1 cm from a 20 mm throat). Overall about 21-24 cm with the LNB body.
    - **Gain or efficiency:** About 19.6 dBi (calculated, efficiency 0.52), beamwidth about 17°. Expected +7 to +11 dB over the bare LNB. Also usable for sun-noise calibration (about 0.2-0.4 dB rise, calculated).
    - **Price:** About $5-10 in materials
    - **Availability incl ukraine:** DIY with local materials. ASA clamp ring with 40.2 mm ID and an M4 pinch bolt (antennas.json design).
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap2.pdf
  6.
    - **Name:** DIY conical horn, 12.7 cm mouth (20 dBi; the earlier 'handheld' horn)
    - **Type:** diy
    - **Band:** 10.49 GHz
    - **Size cm:** 12.7 cm mouth by 12.1 cm long on the 40 mm collar (18.8 cm slant; 14.9 cm from a 20 mm throat). Small tier; just over the strict 12 cm.
    - **Gain or efficiency:** About 20.1 dBi (calculated), beamwidth about 16°
    - **Price:** About $5-15
    - **Availability incl ukraine:** DIY
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap2.pdf
      - https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz
  7.
    - **Name:** DIY conical horn, 15 cm mouth by about 18.5 cm (largest small-tier horn)
    - **Type:** diy
    - **Band:** 10.49 GHz
    - **Size cm:** 15.0 cm mouth by 18.4 cm long on the 40 mm collar (26.2 cm slant from apex). The horn itself fits 20 cm; with the LNB the overall length is about 29-32 cm. If overall length must stay at 20 cm, the limit is an 11 cm by 8.3 cm cone (about 18.8 dBi).
    - **Gain or efficiency:** About 21.5 dBi (calculated), beamwidth about 13°. Needs a small tripod.
    - **Price:** About $5-15
    - **Availability incl ukraine:** DIY
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap2.pdf
  8.
    - **Name:** Commercial WR75/WR90 standard-gain horn with SMA output (not recommended)
    - **Type:** buy
    - **Band:** 8.2-15 GHz
    - **Size cm:** About 10-15 cm for 15-20 dBi (not verified)
    - **Gain or efficiency:** 15-20 dBi, calibrated
    - **Price:** $220.80 (WR75, eBay); $228-356 (WR90, eBay); $1,520 (Pasternack)
    - **Availability incl ukraine:** eBay (China/US). Needs a separate SMA-input 10 GHz LNA and downconverter, so it does not fit the stack.
    - **Sources:**
      - https://www.ebay.de/itm/317537757638
      - https://www.pasternack.com/wr-90-waveguide-standard-gain-horn-antenna-20-dbi-sma-pewan090-20elsf-p.aspx
- **Satellites:**
  1.
    - **Satellite:** QO-100 (Es'hail-2, 25.9°E) narrowband lower beacon
    - **Band:** 10489.500 MHz, vertical (IF 739.500 MHz)
    - **Signal:** CW/F1A beacon, 400 Hz shift
    - **Capability:** Finding and pointing at the satellite, reference for correcting LNB drift (beacon lock), CW copy by ear
    - **Status oct 2026:** Operational. AMSAT-DL news of 10 May 2026 reports XU7AMO starting regular QO-100 operation; amsat-dl.org shows no outage notice up to Oct 2026.
    - **Antenna:** Bare TCXO LNB
    - **Antenna size cm:** About 6 x 12 (LNB)
    - **Tier:** strict
    - **Link margin:** Calculated: C/N0 about 23.6 dB-Hz (21-27): about +6 dB in a 50 Hz bin (3-11) and about +23 dB in a 1 Hz FFT bin. Detection and beacon lock have more than 15 dB margin; copy by ear is marginal.
    - **Reachability:** reliable
    - **Receiver:** RTL-SDR V4L via a 13 V injector, DC block and 10-20 dB pad. FFT bins of 50 Hz or less. GNU Radio tracker that acquires wide (about ±800 kHz) first.
    - **Legal:** Amateur-satellite downlink, receive only: OK. Do not post geotagged screenshots.
    - **Evidence:** OK1DX copied the CW beacon with an LNB alone. A Passion Radio buyer could receive QO-100 'directly without using the dish'. OK1DX found window glass blocks the signal.
    - **Sources:**
      - http://ok1dx.cz/techinfo/qo100/qo100.html
      - https://www.passion-radio.com/satellite-qo-100/converter-432-936.html
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
      - https://destevez.net/2019/03/qo-100-beacons-power/
      - https://amsat-dl.org/en/
  2.
    - **Satellite:** QO-100 narrowband lower beacon
    - **Band:** 10489.500 MHz, vertical
    - **Signal:** CW/F1A
    - **Capability:** Strong copy, accurate pointing, A/B gain measurement of the horn
    - **Status oct 2026:** Operational (as above)
    - **Antenna:** 10-15 cm conical horn on the LNB (18-21.5 dBi)
    - **Antenna size cm:** 10x6.3 to 15x18.4 (horn only)
    - **Tier:** small
    - **Link margin:** Calculated: C/N0 about 32.5-36 dB-Hz; about +15 to +18 dB in 50 Hz (±2.5)
    - **Reachability:** reliable
    - **Receiver:** As above
    - **Legal:** Amateur-satellite downlink, receive only: OK
    - **Evidence:** Scaled from the bare-LNB reports and the EA4GPZ beacon C/N0 measurement. No published horn-on-LNB QO-100 report exists.
    - **Sources:**
      - https://destevez.net/2019/03/qo-100-beacons-power/
      - https://destevez.net/2019/03/weekend-maintenance-to-qo-100-nb-beacons/
      - http://www.w1ghz.org/antbook/chap2.pdf
  3.
    - **Satellite:** QO-100 narrowband middle beacon
    - **Band:** 10489.750 MHz, vertical (IF 739.750 MHz)
    - **Signal:** 400 bit/s BPSK telemetry beacon (AO-40-style FEC)
    - **Capability:** Decoding beacon frames
    - **Status oct 2026:** Listed in the AMSAT-DL bandplan; believed operational
    - **Antenna:** Bare TCXO LNB
    - **Antenna size cm:** About 6 x 12
    - **Tier:** strict
    - **Link margin:** Calculated: C/N0 about 24.6 dB-Hz (22-27) against about 26 dB-Hz needed (my estimate) = about -1.4 dB (-4 to +1)
    - **Reachability:** opportunistic
    - **Receiver:** RTL-SDR V4L plus a decoder for the AO-40-format beacon (which decoder runs on Linux ARM is not verified)
    - **Legal:** Amateur telemetry: OK
    - **Evidence:** Calculation only. The carrier is visible for beacon lock even when frames do not decode.
    - **Sources:**
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
      - https://destevez.net/2019/03/qo-100-beacons-power/
  4.
    - **Satellite:** QO-100 narrowband middle beacon
    - **Band:** 10489.750 MHz
    - **Signal:** 400 bit/s BPSK
    - **Capability:** Decoding beacon frames
    - **Status oct 2026:** As above
    - **Antenna:** 10-15 cm horn
    - **Antenna size cm:** 10x6.3 to 15x18.4
    - **Tier:** small
    - **Link margin:** Calculated: +6.5 to +10 dB over about 26 dB-Hz
    - **Reachability:** reliable
    - **Receiver:** As above
    - **Legal:** OK
    - **Evidence:** Calculation only; antennas.json reached the same result (Eb/N0 about 7 dB with a 20 dBi horn)
    - **Sources:**
      - https://destevez.net/2019/03/qo-100-beacons-power/
  5.
    - **Satellite:** QO-100 narrowband digital segment
    - **Band:** 10489.540-10489.650 MHz, vertical
    - **Signal:** FT8/FT4/Q65/JT65 weak-signal digital user stations. Bandplan: stations should stay at or below beacon level.
    - **Capability:** Decoding FT8/FT4 (receive-only listening)
    - **Status oct 2026:** Active user traffic (amateur)
    - **Antenna:** Bare TCXO LNB
    - **Antenna size cm:** About 6 x 12
    - **Tier:** strict
    - **Link margin:** Calculated: a beacon-level FT8 signal is at about -9 dB SNR (2.5 kHz), range -13 to -5, against a decode limit of about -20 dB. That is about 10 dB margin, so stations up to about 10 dB below the beacon decode. FT4 margin is about 8 dB.
    - **Reachability:** reliable
    - **Receiver:** RTL-SDR V4L, WSJT-X. Needs a TCXO LNB plus beacon-lock drift correction (RigExpert used a GPSDO-locked LNB).
    - **Legal:** Amateur traffic, public by definition: OK. Do not publish logs tied to your location.
    - **Evidence:** RigExpert TBR-AN-1 decoded FT8 at -11 to -15 dB with an LNB alone ('Satellite dish – you do not need it!'). SARTS slide (search snippet only): 'some FT8/JT65 with bare LNB'.
    - **Sources:**
      - https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
      - https://www.sarts.org.sg/wp/wp-content/uploads/2025/09/QO-100-Presentation-1.pdf
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
  6.
    - **Satellite:** QO-100 narrowband digital segment
    - **Band:** 10489.540-10489.650 MHz
    - **Signal:** FT8/FT4/Q65 plus PSK31/RTTY
    - **Capability:** FT8/FT4 for almost all stations; PSK31 at beacon level; RTTY marginal
    - **Status oct 2026:** Active
    - **Antenna:** 10-15 cm horn
    - **Antenna size cm:** 10x6.3 to 15x18.4
    - **Tier:** small
    - **Link margin:** Calculated: beacon-level FT8 at about -1.4 to +2 dB SNR, a margin of +18 to +22 dB
    - **Reachability:** reliable
    - **Receiver:** As above
    - **Legal:** OK
    - **Evidence:** Scaled from the RigExpert result plus about 8-11 dB of horn gain
    - **Sources:**
      - https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
  7.
    - **Satellite:** QO-100 narrowband CW user stations
    - **Band:** 10489.505-10489.540 MHz
    - **Signal:** CW
    - **Capability:** Copying CW stations by ear or with a decoder
    - **Status oct 2026:** Active
    - **Antenna:** Bare TCXO LNB
    - **Antenna size cm:** About 6 x 12
    - **Tier:** strict
    - **Link margin:** Calculated: a beacon-level station is about +6 dB in 50 Hz; stations 5 dB or more below the beacon are lost
    - **Reachability:** marginal
    - **Receiver:** RTL-SDR V4L, narrow CW filter of 50-100 Hz
    - **Legal:** OK
    - **Evidence:** Same signal levels as the CW beacon (OK1DX)
    - **Sources:**
      - http://ok1dx.cz/techinfo/qo100/qo100.html
  8.
    - **Satellite:** QO-100 narrowband CW user stations
    - **Band:** 10489.505-10489.540 MHz
    - **Signal:** CW
    - **Capability:** CW copy down to about 10 dB below the beacon
    - **Status oct 2026:** Active
    - **Antenna:** 10-15 cm horn
    - **Antenna size cm:** 10x6.3 to 15x18.4
    - **Tier:** small
    - **Link margin:** Calculated: +15 to +18 dB in 50 Hz at beacon level
    - **Reachability:** reliable
    - **Receiver:** As above
    - **Legal:** OK
    - **Evidence:** Calculation
    - **Sources:**
      - https://destevez.net/2019/03/qo-100-beacons-power/
  9.
    - **Satellite:** QO-100 narrowband SSB voice
    - **Band:** 10489.650-10489.850 MHz
    - **Signal:** SSB, 2.7 kHz
    - **Capability:** Listening to SSB contacts
    - **Status oct 2026:** Active
    - **Antenna:** Bare TCXO LNB
    - **Antenna size cm:** About 6 x 12
    - **Tier:** strict
    - **Link margin:** Calculated: a beacon-level station is about -10 dB in 2.7 kHz (-13 to -7). Even the strongest legal stations are about 13 dB short of barely readable (+3 dB).
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** OK if heard
    - **Evidence:** No bare-LNB SSB report exists; OK1DX and RigExpert report only CW and FT8
    - **Sources:**
      - http://ok1dx.cz/techinfo/qo100/qo100.html
      - https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
  10.
    - **Satellite:** QO-100 narrowband SSB voice
    - **Band:** 10489.650-10489.850 MHz
    - **Signal:** SSB
    - **Capability:** The strongest (beacon-level) stations only, copied by an experienced ear with DSP noise reduction
    - **Status oct 2026:** Active
    - **Antenna:** 10-15 cm horn
    - **Antenna size cm:** 12x10.5 (19.6 dBi) to 15x18.4 (21.5 dBi)
    - **Tier:** small
    - **Link margin:** Calculated: about -0.2 dB (12 cm horn) to +1.7 dB (15 cm horn) in 2.7 kHz at beacon level, ±2.5 dB, plus beacon variation of up to 2 dB per day. Readable SSB (+6 dB) needs about 26 dBi. Typical stations 5-15 dB below the beacon are lost.
    - **Reachability:** opportunistic
    - **Receiver:** RTL-SDR V4L, 1.8-2.4 kHz filter, beacon lock
    - **Legal:** OK
    - **Evidence:** Calculation, consistent with antennas.json's G/T model (-1 to +2 dB). This replaces dish_replacement.json's 14-17 dB estimate, which was wrong.
    - **Sources:**
      - https://destevez.net/2019/03/qo-100-beacons-power/
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
  11.
    - **Satellite:** QO-100 narrowband SSB voice
    - **Band:** 10489.650-10489.850 MHz
    - **Signal:** SSB
    - **Capability:** Beacon-level SSB readable
    - **Status oct 2026:** Active
    - **Antenna:** EXCLUDED: 23 dBi horn (17.8 cm mouth by about 28 cm) or 30 cm W1GHZ lens with a 17.5 dBi feed horn (about 60-70 cm deployed)
    - **Antenna size cm:** 18x28; lens about 30x30, about 65 cm long
    - **Tier:** borderline_excluded
    - **Link margin:** Calculated: +3.2 dB (23 dBi horn) and +7.5 dB (27.4 dBi lens) in 2.7 kHz
    - **Reachability:** marginal
    - **Receiver:** As above
    - **Legal:** OK
    - **Evidence:** W1GHZ measured 27.4 dBi for the lens at 10.368 GHz with a 17.5 dBi horn
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap3.pdf
  12.
    - **Satellite:** QO-100 narrowband multimedia beacon
    - **Band:** 10489.9935 MHz
    - **Signal:** 8APSK, 7200 bit/s
    - **Capability:** Data decoding
    - **Status oct 2026:** Listed in the AMSAT-DL bandplan; current activity not verified
    - **Antenna:** Any strict- or small-tier antenna
    - **Antenna size cm:** 12 or less to 15x18
    - **Tier:** small
    - **Link margin:** Calculated, assuming beacon-level power (not verified): needs about 41 dB-Hz. Small tier gives 32.5-36, a shortfall of 5-8 dB; strict bare LNB is about 16 dB short.
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** OK
    - **Evidence:** Calculation only
    - **Sources:**
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
  13.
    - **Satellite:** QO-100 wideband DATV transponder
    - **Band:** 10491.5 MHz beacon (1.5 MS/s DVB-S2 QPSK 4/5) plus DATV stations at 10491-10499 MHz, horizontal (18 V)
    - **Signal:** DVB-S2 DATV
    - **Capability:** Video decoding. LOST in both tiers. With a horn only a spectrum hump is visible.
    - **Status oct 2026:** Believed operational (BATC); not re-checked
    - **Antenna:** Bare LNB or horns of 21.5 dBi or less
    - **Antenna size cm:** 12 or less to 15x18
    - **Tier:** small
    - **Link margin:** Calculated from a fit to the BATC MER table: C/N in 1.5 MHz is -17 dB (bare LNB) and -9 to -5 dB (10-15 cm horns), against about +3 to +4.7 dB needed, so 8-21 dB short. Decoding needs about 31-32 dBi (a dish of about 45 cm or larger); DATV user stations need 90 cm or more.
    - **Reachability:** not_reachable
    - **Receiver:** n/a (a hump of about 0.5-1.1 dB is visible on an averaged spectrum with a horn)
    - **Legal:** Amateur TV: OK
    - **Evidence:** BATC MER table: 60 cm 6 dB, 70 cm 7 dB, 80 cm 8 dB, 1.2 m 10 dB
    - **Sources:**
      - https://wiki.batc.org.uk/Receiving_Oscar_100_DATV_signals
  14.
    - **Satellite:** Geostationary Ku broadcast carriers (e.g. Hot Bird 13F/13G at 13.0°E and other European positions between 5°E and 42°E)
    - **Band:** 10.7-11.7 GHz on the low-band LO (IF 950-1950 MHz; the RTL-SDR reaches 11.516 GHz) and 11.7-12.75 GHz on the high band (needs 22 kHz tone and the LimeSDR)
    - **Signal:** DVB-S2 TV multiplexes, e.g. Hot Bird 13G 11116.70 V, 8PSK 3/4, 27.5 MS/s (an encrypted carrier, used only as a power reference)
    - **Capability:** Seeing that carriers are present (noise humps), Clarke-belt survey. No decoding.
    - **Status oct 2026:** Hot Bird 13F/13G active at 13°E (Wikipedia; KingOfSat)
    - **Antenna:** Bare LNB
    - **Antenna size cm:** About 6 x 12
    - **Tier:** strict
    - **Link margin:** Calculated, assuming EIRP 48-53 dBW over Ukraine (not verified), slant range 38,625 km, Tsys 150 K: C/N0 59-64 dB-Hz, so -15 to -10 dB in 27.5 MHz (humps of 0.1-0.4 dB). The 40-50° beam overlaps several orbital positions.
    - **Reachability:** opportunistic
    - **Receiver:** RTL-SDR V4L averaged spectrum or rtl_power, 13/18 V for V/H
    - **Legal:** Public broadcast: measure RF power only. Never attempt to decrypt pay-TV; skip contribution feeds.
    - **Evidence:** Calculation only
    - **Sources:**
      - https://en.kingofsat.info/tp243
      - https://en.wikipedia.org/wiki/Hot_Bird
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
  15.
    - **Satellite:** Geostationary Ku broadcast carriers (Hot Bird 13°E etc.)
    - **Band:** 10.7-12.75 GHz
    - **Signal:** DVB-S/S2 multiplexes
    - **Capability:** Clear carrier humps for horn/LNB calibration and pointing practice. Decoding still not possible.
    - **Status oct 2026:** Active
    - **Antenna:** 12-15 cm horn
    - **Antenna size cm:** 12x10.5 to 15x18.4
    - **Tier:** small
    - **Link margin:** Calculated: C/N -4 to +3 dB in 27.5 MHz (humps of 1.5-5 dB), against 7.9 dB needed for 8PSK 3/4, so decoding is about 5-12 dB short. Adjacent satellites stay inside the 13-17° beam.
    - **Reachability:** reliable
    - **Receiver:** As above. The LimeSDR Micro covers the whole IF (ships 15 Dec 2026).
    - **Legal:** As above
    - **Evidence:** Calculation only
    - **Sources:**
      - https://en.kingofsat.info/tp243
  16.
    - **Satellite:** Geostationary Ku tracking beacons (unmodulated carriers)
    - **Band:** Frequencies NOT verified. A satbeams listing for the retired Hot Bird 8 showed 11699.8 H, 11701 H, 12500 V and 12500.5 H; I could not verify these for 13F/13G.
    - **Signal:** CW carrier
    - **Capability:** Narrow calibration carrier for frequency or gain checks
    - **Status oct 2026:** Unverified
    - **Antenna:** Bare LNB or horn
    - **Antenna size cm:** About 6 x 12 or larger
    - **Tier:** strict
    - **Link margin:** Calculated: 10 dB in a 10 Hz bin needs a beacon EIRP of about 9 dBW (bare LNB) or about -3 dBW (12 cm horn). Real beacon EIRP is not verified.
    - **Reachability:** opportunistic
    - **Receiver:** LimeSDR for IF above 1766 MHz; narrow FFT
    - **Legal:** Observe the carrier only. Do not demodulate operator telemetry (private).
    - **Evidence:** Search snippet only (satbeams), not opened
    - **Sources:**
      - https://www.satbeams.com/
  17.
    - **Satellite:** Starlink and OneWeb Ku user downlinks (LEO)
    - **Band:** About 10.7-12.7 GHz (not re-verified here)
    - **Signal:** Private user data
    - **Capability:** EXCLUDED. Starlink is a front-line military communications system in Ukraine; since 2026 only whitelisted terminals work there.
    - **Status oct 2026:** Active; military use
    - **Antenna:** none
    - **Antenna size cm:** n/a
    - **Tier:** none
    - **Link margin:** n/a
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** Do not record, track, characterise, decode or publish. At most: if moving bursts or a noise rise appear during a GEO measurement, ignore and discard them.
    - **Evidence:** Wikipedia: 'Most Ukrainian units have one Starlink terminal'; Starlink 'eliminated service to all terminals in Ukraine not on a whitelist'
    - **Sources:**
      - https://en.wikipedia.org/wiki/Starlink_in_the_Russo-Ukrainian_War
  18.
    - **Satellite:** Military or government SATCOM (X and Ku band)
    - **Band:** Various
    - **Signal:** Military
    - **Capability:** EXCLUDED
    - **Status oct 2026:** n/a
    - **Antenna:** none
    - **Antenna size cm:** n/a
    - **Tier:** none
    - **Link margin:** n/a
    - **Reachability:** not_reachable
    - **Receiver:** n/a
    - **Legal:** Excluded by the safety frame; under martial law do not search for it
    - **Evidence:** Policy
    - **Sources:** []
- **Lost vs foldable:**
  1.
    - **Target:** QO-100 narrowband SSB from the strongest (beacon-level) stations
    - **Needed:** +3 dB in 2.7 kHz to barely copy needs about 23 dBi; +6 dB readable needs about 26 dBi; +10 dB comfortable needs about 30 dBi (calculated)
    - **Gap db:** Best small-tier horn (21.5 dBi) is 1.5 dB below the baseline 23 dBi horn and 6 dB below the 27.4 dBi lens. Strict (19.6 dBi) is 3.4 and 8 dB below. Bare LNB is about 13 dB below the horn.
    - **What would bring it back:** The 23 dBi horn (17.8 cm by about 28 cm) for barely-readable copy, or the 30 cm W1GHZ lens with a 17.5 dBi feed (about 65 cm deployed, packs flat) for readable copy, or a 35 cm dish (+9.5 dB). Software gains only 1-2 dB (narrower filter, noise reduction).
  2.
    - **Target:** QO-100 typical SSB stations 5-15 dB below the beacon
    - **Needed:** About 30-40 dBi (dish of 35-90 cm)
    - **Gap db:** 8-20 dB short in the small tier. The foldable baseline had only partial copy here: the lens reached about +2.5 dB for stations 5 dB down.
    - **What would bring it back:** A 35-60 cm dish only
  3.
    - **Target:** QO-100 multimedia beacon (8APSK, 7.2 kbit/s)
    - **Needed:** About 41 dB-Hz (estimate, assuming beacon-level power), which is about 27 dBi
    - **Gap db:** 5-8 dB short (small tier); about 16 dB short (bare LNB)
    - **What would bring it back:** The 30 cm lens (marginal) or a dish
  4.
    - **Target:** QO-100 wideband DATV beacon and stations
    - **Needed:** About 31-32 dBi for the beacon; a dish of 90 cm or more for user stations (BATC)
    - **Gap db:** 10-12 dB short (small tier). The foldable baseline could not decode this either.
    - **What would bring it back:** A dish of 45 cm or more only; no non-dish option reaches it
  5.
    - **Target:** Comfortable QO-100 pointing and SNR headroom (strict bare LNB versus horn)
    - **Needed:** 18-21.5 dBi horn
    - **Gap db:** 8-11 dB between the bare LNB and the small-tier horn. PSK beacon frames, beacon-level SSB and CW 10 dB below the beacon all depend on it.
    - **What would bring it back:** The 10-12 cm cone already fits the strict tier by its own dimensions. Only the overall length with the LNB (about 17-24 cm) pushes it into the small tier.
- **Borderline note:** BORDERLINE (excluded by the new size rule; for reconsideration only). The 23 dBi conical horn (17.8 cm mouth, about 28 cm long on the LNB collar, 37 cm slant) adds only about 1.5 dB over the best small-tier horn. With it, beacon-level SSB rises from about 0 dB to +3 dB, which is barely copyable. The 30 cm W1GHZ metal-plate lens is foam and foil, packs flat, and stands about 65 cm deployed with a 17.5-18 dBi feed horn. It adds about 6 dB: beacon-level SSB about +7.5 dB (readable) and the multimedia beacon marginal. Neither reaches DATV (31-32 dBi) or typical SSB stations (about 30 dBi or more). If listening to QO-100 SSB matters, the lens is the only item worth reconsidering. Otherwise the small tier loses little in this band.
- **Notes:** TIERS AS APPLIED. Strict: the bare LNB counts as strict (the rule says so explicitly), and so does a cone with mouth and length of 12 cm or less (about 19.6 dBi). Small: horns up to 15 cm by 18.5 cm (21.5 dBi). If the 11-14 cm LNB body must be counted in the overall length, the small-tier limit drops to an 11 x 8.3 cm cone (about 18.8 dBi). Excluded: dishes, flat panels (Selfsat H21D/H30D are about 47-52 cm and not specified below 10.7 GHz), the 23 dBi horn and the lens. I found no flat Ku panel of 20 cm or less with an LNB covering 10.489 GHz.
  
  ERROR FOUND IN THE INPUTS (corrected here). dish_replacement.json's QO-100 budget, 'beacon C/N0 is about 28 + G dB-Hz', is about 14 dB too optimistic. It gave the bare LNB a beacon C/N of 3-6 dB in 2.7 kHz, a 20/23 dBi horn 14/17 dB, and the lens 21 dB. The anchor it used, the BATC '>30 dB on 90 cm' snippet, must have been measured in a narrow FFT bin, not in 2.7 kHz.
  
  The primary measurement: EA4GPZ measured the BPSK beacon at about 45 dB-Hz on a dish he describes as comparable to 60 cm (about 34.2 dBi). After maintenance the beacons were about 3 dB stronger, and the beacon C/N0 against transponder noise was 56 dB-Hz. From that I derive, as a calculation: beacon C/N0 is about G + 14.6 dB-Hz (±2.5 dB), capped by transponder noise at 56 dB-Hz. This is the model behind every number above. It matches antennas.json's G/T model (-1 to +2 dB in 2.5 kHz for 20-23 dBi horns). It also matches the field evidence: the CW beacon was only just copyable on a bare LNB (OK1DX), and FT8 decoded at -11 to -15 dB, which is close to beacon level since the bandplan says users must stay 'not stronger than the Beacon'. The horn geometry and the DATV verdict do not change.
  
  PHYSICS. At 10.49 GHz the wavelength is 28.6 mm, so a 12 cm horn is 4.2λ across. It is not electrically short, and its aperture efficiency (about 0.52 for an optimum horn) carries no small-antenna penalty. What limits it is aperture area against a system temperature of about 100-150 K: the LNB's 0.5 dB NF (35 K) plus ground spillover. Sky noise at 32° elevation is small. Transponder noise only matters above about 35 dBi, and band noise from outside does not set the limit. Every +3 dB of gain costs 1.41x the mouth diameter and about 2x the length.
  
  CHAIN.
  - LNB: Bullseye (or QRO.cz at 12-15 V only). Use a regulated 13 V buck-boost through an injector; never the raw 4S pack, which reaches 16.8 V and can flip polarisation.
  - Then DC block, then a 10-20 dB pad, into the RTL-SDR V4L at 739.5-740 MHz.
  - Keep LNB DC away from the LimeSDR (its RX ESD protection is rated 5.3 V). The Lime also has a 737.28 MHz spur 2.2 MHz from the narrowband IF.
  - HDMI 1080p60 has a 5th harmonic at 742.5 MHz, close to the wideband IF. Use a 1080p52 EDID and shielding.
  - Cap the Bullseye's red F port: it is a +15 V serial calibration port.
  - The beacon tracker must acquire wide (about ±800 kHz around IF 739.625 MHz) before narrowing; this fixes the earlier acquisition bug.
  - Pointing: Kyiv 186°/32°, Lviv 178°/33°, Kharkiv 193°/32°, Odesa 187°/36°. Rotate the LNB for polarisation skew. Operate outdoors: window glass blocks 10 GHz.
  - Ku TV carriers above 11.516 GHz on the low band, and the high band (22 kHz tone), need the LimeSDR (ships 15 Dec 2026).
  
  CALIBRATION EXTRAS (calculated, assuming 250-400 sfu at 11 GHz). With the 12-15 cm horn the Sun gives about a 0.2-0.5 dB noise rise; with the bare LNB about 0.03 dB, which is not practical. A cold-sky versus ground comparison gives a quick check of the LNB and horn. Ku broadcasts from the 25.5-26°E cluster (Es'hail/Badr) might help confirm the QO-100 pointing, but whether their beams cover Ukraine is not verified.
  
  LEGAL AND SAFETY. Receive only.
  - Fine to receive: QO-100 amateur traffic, FTA broadcast carriers measured as RF power only.
  - Never: decrypt pay-TV or demodulate operator telemetry.
  - Excluded entirely: Starlink/OneWeb (private and military in Ukraine) and all military SATCOM.
  - Martial law: never publish geotagged spectra or photos, and do not set up near military or critical sites.
  - GNSS is widely jammed or spoofed, so enter your coordinates by hand and aim with the BNO085 plus the Sun or landmarks.
  - Fields may hold unexploded ordnance: if you find one, call 101.
  
  UNVERIFIED.
  - Bullseye dimensions and current draw.
  - Bare-LNB gain (9-12 dBi is an estimate).
  - How well a clamp-on cone mates to the scalar feed (±2 dB; check with an A/B beacon test, expect +6 to +11 dB).
  - Multimedia-beacon power.
  - Ku EIRP over Ukraine (48-53 dBW assumed).
  - Ku tracking-beacon frequencies.
  - Stability of the local Prom.ua LNBs.
  - Bullseye and WiMo shipping to Ukraine.
  - The OK1DX page returned HTTP 503 today, so its content comes from the earlier agents' reading.
  
  WebSearch used: 3 calls.

## small:catalog_legal (run `wf_41027870-8e7`)

- **Satellites:**
  1.
    - **Name:** Meteor-M N2-4 (NORAD 59051)
    - **Band:** VHF 137.900 MHz LRPT (137.100 alternate), L-band 1700/1705 MHz HRPT
    - **Service:** Weather imagery (MSU-MR): LRPT 72 ksym/s, 3 JPEG channels at 1 km; HRPT 665.4 ksym/s, 6 channels
    - **Status:** ACTIVE. LRPT decoded on 137.900 MHz by European SatNOGS stations on 17-18 Oct 2026 (e.g. a Greek station, 18 Oct 00:36 UTC, 7 data frames). HRPT listed active by SatDump. Tier note: a quarter wave at 137.9 MHz is 54 cm, so any LRPT antenna in either tier is electrically short. HRPT anchor from the inputs: the 12.75 dBic helix gives about 7 dB average SNR against 0.5 dB needed. The 4-5 turn helix on an 18 cm plate (11.6-12.0 dBic modelled, 19-22 cm tall) sits at the SMALL-tier edge; the 47 cm helix and the helicone are EXCLUDED.
    - **Status date and source:** 2026-10-18 SatNOGS Network good observations with decoded data; SatDump sat_list.json, last commit 2 Jul 2026; WMO OSCAR 'operational' (2026-01-23, from the inputs)
    - **Sources:**
      - https://network.satnogs.org/api/observations/?norad_cat_id=59051&status=good
      - https://network.satnogs.org/observations/15230698/
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
      - https://space.oscar.wmo.int/satellites/view/meteor_m_n2_4
  2.
    - **Name:** Meteor-M N2-3 (NORAD 57166)
    - **Band:** VHF 137.900 MHz LRPT (137.100 alternate), L-band 1700 MHz HRPT
    - **Service:** Weather imagery (LRPT and HRPT, same instrument as N2-4)
    - **Status:** ACTIVE. LRPT decoded on 137.900 MHz by SatNOGS stations in Germany, Poland, the Netherlands and Hungary on 17 Oct 2026. SatDump notes that its VHF antenna did not deploy properly (so LRPT is weaker than N2-4's) and that the LRPT compressor causes occasional pixelation and watchdog restarts. HRPT is active. Same tier notes as N2-4.
    - **Status date and source:** 2026-10-17 SatNOGS Network (e.g. obs 15229039, decoded data); SatDump list, 2 Jul 2026
    - **Sources:**
      - https://network.satnogs.org/observations/15229039/
      - https://network.satnogs.org/api/observations/?norad_cat_id=57166&status=good
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  3.
    - **Name:** NOAA-15 / NOAA-18 / NOAA-19 (POES)
    - **Band:** APT 137.62 / 137.9125 / 137.1 MHz; HRPT 1702.5 / 1707 / 1698 MHz
    - **Service:** Weather APT and HRPT
    - **Status:** ENDED. NOAA-18 was decommissioned on 6 Jun 2025 at 17:40 UTC, NOAA-19 on 13 Aug 2025 at 18:55 UTC (battery cell failure), and NOAA-15 on 19 Aug 2025 at 20:37 UTC. No APT remains anywhere.
    - **Status date and source:** NOAA OSPO POES status page (fetched 18 Oct 2026); SatDump list end dates match
    - **Sources:**
      - https://www.ospo.noaa.gov/operations/poes/status.html
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  4.
    - **Name:** Metop-B (NORAD 38771)
    - **Band:** L-band 1701.3 MHz AHRPT (2.33 Msym/s); LRPT 137 MHz is OFF
    - **Service:** Weather AHRPT (EUMETSAT)
    - **Status:** ACTIVE but degraded. OSPO lists AHRPT 'Yes', with APT/LRPT and HIRS red. SatDump reports intermittent modulator problems that lower SNR. Tier note: unreachable in both tiers. The inputs put even the 12.75 dBic helix about 1.6 dB below threshold on a pass average.
    - **Status date and source:** NOAA OSPO Metop status, updated 3 Sep 2026; SatDump list, 2 Jul 2026
    - **Sources:**
      - https://www.ospo.noaa.gov/operations/metop/status.html
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  5.
    - **Name:** Metop-C (NORAD 43689)
    - **Band:** L-band 1701.3 MHz AHRPT (2.33 Msym/s); LRPT OFF
    - **Service:** Weather AHRPT
    - **Status:** CONFLICTING. OSPO says AHRPT 'No' (3 Sep 2026) and lists data-loss notices for 9 Aug and 5-7 Oct 2026. SatDump (2 Jul 2026) and the SatNOGS DB list AHRPT as active. Out of reach for 20 cm antennas in any case.
    - **Status date and source:** OSPO, 3 Sep 2026; SatDump, 2 Jul 2026
    - **Sources:**
      - https://www.ospo.noaa.gov/operations/metop/status.html
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  6.
    - **Name:** Arctic Weather Satellite AWS (NORAD 60543)
    - **Band:** L-band 1707 MHz, 1.785 Msym/s RHCP
    - **Service:** Microwave sounder direct broadcast (ESA prototype for EPS-Sterna)
    - **Status:** ACTIVE per SatDump; its signal fades when the satellite faces away. EIRP is unpublished. Small-antenna reception is unknown and probably out of reach, since its rate is about 2.7x Meteor HRPT.
    - **Status date and source:** SatDump list, 2 Jul 2026
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
      - https://space.oscar.wmo.int/satellites/view/aws_pfm
  7.
    - **Name:** Elektro-L N3 / N5 (76°E) and N2 (14.5°W)
    - **Band:** L-band 1691 MHz LRIT/HRIT
    - **Service:** Geostationary weather imagery
    - **Status:** NOT AVAILABLE as of SatDump's July 2026 update. L3's transmissions are paused pending L5 commissioning. L5's LRIT and HRIT are 'off for commissioning' (only telemetry is active), although the SatNOGS DB entry dated 7 Apr 2026 still lists L5 LRIT as active. L2 cannot transmit xRIT after a power-supply failure. Calculation: 76°E is about 18° elevation and 127° azimuth from Kyiv. This contradicts the inputs, which use Elektro-L5 LRIT as the antenna A/B test source. Check on air before relying on it.
    - **Status date and source:** SatDump list, 2 Jul 2026 ('Elektro updates' commit); SatNOGS DB, 7 Apr 2026
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
      - https://github.com/SatDump/satdump.org/commits/master/sat-list/sat_list.json
      - https://db.satnogs.org/api/transmitters/?format=json
  8.
    - **Name:** FengYun-2H (79°E)
    - **Band:** L-band 1687.5 MHz S-VISSR (660 ksym/s), 1690.5 MHz test-pattern carrier every 3 h from 00:48 UTC; linear polarisation
    - **Service:** Geostationary weather imagery
    - **Status:** ACTIVE per SatDump. Calculation: about 16.6° elevation and 124° azimuth from Kyiv. Treat it as a fixed reference carrier for comparing antennas, not as a decode target for small antennas (unverified).
    - **Status date and source:** SatDump list, 2 Jul 2026
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  9.
    - **Name:** ISS amateur stations (NA1SS Columbus, RS0ISS Zvezda)
    - **Band:** UHF 437.800 MHz FM repeater downlink (uplink 145.990, CTCSS 67); 437.825 MHz APRS; SSTV event-based (latest listed on 437.550 MHz); HamTV 2395 MHz test signal
    - **Service:** Amateur voice repeater, APRS packet, SSTV
    - **Status:** ACTIVE. ARISS (7 Oct 2026): the FM repeater is active, and APRS is active on 437.825 MHz from Zvezda. 145.825 MHz is no longer listed, and the Zvezda radio is still being troubleshot. AMSAT has 'ISS [FM]' heard on 18 Oct 2026 and the UHF digipeater heard on 18 Oct 2026. AMSAT also shows 3 'VHF Digi heard' reports from one station on 17 Oct (conflicting, unverified). SSTV: the last listed event is ARISS Series 32, 8-12 May 2026, on 437.550 MHz Robot 36. No later event is posted, and AMSAT ISS SSTV was 'not heard' on 15 Oct 2026. Tier note: a quarter wave at 437 MHz is 17 cm, so it fits the SMALL tier at full size; in the STRICT tier it is about 0.7 of a quarter wave. The move of ISS SSTV and APRS to UHF benefits this rule.
    - **Status date and source:** ARISS status, 7 Oct 2026; ARISS SSTV gallery (fetched 18 Oct 2026); AMSAT status, 13-18 Oct 2026; SatNOGS obs 15227798 (APRS 437.825, 17 Oct 2026)
    - **Sources:**
      - https://www.ariss.org/current-status-of-iss-stations.html
      - https://ariss.pzk.org.pl/sstv/
      - https://www.amsat.org/status/
      - https://network.satnogs.org/observations/15227798/
  10.
    - **Name:** SO-50 (SaudiSat-1C)
    - **Band:** UHF 436.795 MHz FM downlink
    - **Service:** Amateur FM repeater
    - **Status:** ACTIVE. AMSAT 'Heard' on 18 Oct 2026 00:46 UTC and on 39 of 72 slots over 6 days. SatNOGS had 25 good observations from 15-17 Oct 2026.
    - **Status date and source:** AMSAT status 18 Oct 2026; SatNOGS 17 Oct 2026
    - **Sources:**
      - https://www.amsat.org/status/
      - https://network.satnogs.org/observations/15229379/
  11.
    - **Name:** AO-91 (Fox-1B)
    - **Band:** VHF 145.960 MHz FM downlink plus DUV telemetry
    - **Service:** Amateur FM repeater
    - **Status:** DEGRADED/INTERMITTENT. AMSAT 13-18 Oct 2026: 2 'Heard' reports (15 and 16 Oct) against 7 'Not Heard'. DUV telemetry was decoded by SatNOGS on 17 Oct 2026. The SatNOGS DB notes the repeater no longer needs CTCSS. VHF, so a quarter wave is 51 cm and the antenna is electrically short.
    - **Status date and source:** AMSAT status 17 Oct 2026; SatNOGS obs 15222852 (17 Oct 2026)
    - **Sources:**
      - https://www.amsat.org/status/
      - https://network.satnogs.org/observations/15222852/
  12.
    - **Name:** AO-27 (EYESAT-1)
    - **Band:** UHF 436.795 MHz FM / AFSK beacon
    - **Service:** Amateur FM repeater (part-time)
    - **Status:** INTERMITTENT. The last SatNOGS good observation was 1 Oct 2026. It does not appear on the AMSAT 6-day page. Its operating schedule was not verified.
    - **Status date and source:** SatNOGS obs 15088170, 1 Oct 2026
    - **Sources:**
      - https://network.satnogs.org/observations/15088170/
  13.
    - **Name:** AO-123 (ASRTU-1)
    - **Band:** UHF 435.400 MHz FM downlink and BPSK 9k6 telemetry; SSDV 436.210
    - **Service:** Amateur FM repeater, telemetry, SSDV
    - **Status:** ACTIVE. AMSAT 'Heard' on 17 Oct 2026 (also many 'telemetry only' reports). SatNOGS good observation on 17 Oct 2026 23:55 UTC.
    - **Status date and source:** AMSAT status 17 Oct 2026; SatNOGS obs 15229208
    - **Sources:**
      - https://www.amsat.org/status/
      - https://network.satnogs.org/observations/15229208/
  14.
    - **Name:** PO-101 (Diwata-2)
    - **Band:** VHF 145.900 MHz FM downlink
    - **Service:** Amateur FM repeater (scheduled activations)
    - **Status:** INTERMITTENT. Last SatNOGS good observation 29 Sep 2026; AMSAT 'Not Heard' on 16 Oct 2026.
    - **Status date and source:** SatNOGS obs 15082384; AMSAT 16 Oct 2026
    - **Sources:**
      - https://network.satnogs.org/observations/15082384/
      - https://www.amsat.org/status/
  15.
    - **Name:** IO-117 GreenCube
    - **Band:** UHF 435.310 MHz GMSK 1k2 digipeater/telemetry
    - **Service:** Amateur digipeater (MEO)
    - **Status:** SILENT/PRESUMED ENDED (cause unverified). The last SatNOGS good observation was 25 Jul 2025, with only failed or bad observations until 5 Aug 2025, after which stations stopped scheduling it. It is absent from the AMSAT status page. A decommissioning was planned for 5 Feb 2024 and postponed.
    - **Status date and source:** SatNOGS Network (latest good 2025-07-25, latest bad 2025-08-05); AMSAT-UK, Jan 2024
    - **Sources:**
      - https://network.satnogs.org/api/observations/?norad_cat_id=53106&status=good
      - https://amsat-uk.org/2024/01/25/io-117-greencube-to-cease-operating-on-february-5/
      - https://www.amsat.org/amsat-responds-planned-decommissioning-io-117-greencube/
  16.
    - **Name:** RS-44 (DOSAAF-85)
    - **Band:** UHF 435.610-435.670 MHz linear transponder downlink; CW beacon 435.605
    - **Service:** Amateur SSB/CW linear transponder
    - **Status:** ACTIVE. AMSAT 'Heard' on 18 Oct 2026, active in 54 of 72 slots. SatNOGS good observation on 16 Oct 2026. SSB user signals are weaker than FM birds.
    - **Status date and source:** AMSAT 18 Oct 2026; SatNOGS obs 15213134
    - **Sources:**
      - https://www.amsat.org/status/
      - https://network.satnogs.org/observations/15213134/
  17.
    - **Name:** FO-29 (JAS-2)
    - **Band:** UHF 435.800-435.900 MHz linear transponder; CW beacon 435.795
    - **Service:** Amateur linear transponder
    - **Status:** ACTIVE. AMSAT active in 47 of 72 slots over 13-18 Oct 2026; SatNOGS CW beacon observation on 17 Oct 2026.
    - **Status date and source:** AMSAT 13-18 Oct 2026; SatNOGS obs 15214291
    - **Sources:**
      - https://www.amsat.org/status/
      - https://network.satnogs.org/observations/15214291/
  18.
    - **Name:** AO-7, JO-97, AO-73 (VHF-downlink linear and telemetry birds)
    - **Band:** AO-7: 145.925-145.975 MHz (mode B) and 435.100 MHz beacon; JO-97: 145.855-145.875 and BPSK 145.840; AO-73: BPSK 145.935
    - **Service:** Amateur linear transponders and telemetry
    - **Status:** AO-7 ACTIVE (sunlight-dependent; beacon decoded 12 Oct 2026). JO-97 ACTIVE (AMSAT active in 26 of 72 slots; SatNOGS 15 Oct 2026). AO-73 is telemetry-only (AMSAT 17 Oct 2026). All are VHF except the AO-7 435.100 MHz beacon.
    - **Status date and source:** AMSAT 13-18 Oct 2026; SatNOGS obs 15188324, 15209178, 15228423
    - **Sources:**
      - https://www.amsat.org/status/
      - https://network.satnogs.org/observations/15188324/
      - https://network.satnogs.org/observations/15209178/
      - https://network.satnogs.org/observations/15228423/
  19.
    - **Name:** Chinese CAS/XW/LilacSat birds
    - **Band:** UHF 435-437 MHz (CAS-3H 437.200/437.225; XW-3 435.725; CAS-2T 435.710); VHF (TO-108 145.910 CW)
    - **Service:** Amateur telemetry and FM/linear transponders
    - **Status:** MIXED. CAS-3H (LilacSat-2) telemetry decoded on 18 Oct 2026, but its FM repeater was 'Not Heard' on 14 Oct (AMSAT). XW-3 (CAS-9/HO-113) telemetry was good on 12 Oct 2026. CAS-2T CW was last good on 29 Aug 2026. TO-108 (CAS-6) CW was last good on 24 Sep 2026 and 'Not Heard' on 15 Oct. LilacSat-3 (new, 2026) has no good SatNOGS observation (unverified). XW-2A to F, CAS-5A (FO-118), CAS-10 (HO-119) and LilacSat-1 have re-entered.
    - **Status date and source:** SatNOGS Network / DB, 18 Oct 2026; AMSAT 13-18 Oct 2026
    - **Sources:**
      - https://network.satnogs.org/observations/15229995/
      - https://network.satnogs.org/observations/15186279/
      - https://network.satnogs.org/observations/14908809/
      - https://network.satnogs.org/observations/15044280/
      - https://db.satnogs.org/api/satellites/?format=json
  20.
    - **Name:** 435-438 MHz CubeSats regularly decoded (representative)
    - **Band:** UHF 435.8-437.7 MHz
    - **Service:** Amateur/educational telemetry beacons, some FM repeaters, APRS and SSTV
    - **Status:** ALIVE (SatNOGS good observations; 'strong' is not quantified because EIRP is unpublished). TEVEL2-1 to -9: 436.400 BPSK 9k6, good 15-17 Oct 2026. SONATE-2: 437.025 GMSK 9k6, plus APRS 145.825 and SSTV 145.880 (VHF), 17 Oct. UmKA-1 (RS40S): 437.625 GMSK 9k6 and SSTV, 18 Oct. Geoscan-1 (RS92S1): 435.970 GFSK 9k6, 16 Oct. HADES-SA: 436.875 FSK 800, 17 Oct. HADES-L: 436.665 FSK 800 plus FM/USB repeater, 17 Oct. UNNE-1B (HADES-E2): 436.888 FM repeater and 200 bps telemetry, 17 Oct. SCION-X: 437.500 GFSK 9k6, 17 Oct. DISCO-2: 437.075 FSK 4k8, 15 Oct. MESAT-1 (MO-122): 435.800 BPSK 1k2, 30 Sep. MARMOTSat (CO-128): 436.125, plus 145.875 digipeater, 4 Oct.
    - **Status date and source:** SatNOGS Network good observations, 30 Sep-18 Oct 2026 (latest per satellite)
    - **Sources:**
      - https://network.satnogs.org/observations/15229936/
      - https://network.satnogs.org/observations/15229454/
      - https://network.satnogs.org/observations/15228008/
      - https://network.satnogs.org/observations/15213014/
      - https://network.satnogs.org/observations/15224594/
      - https://network.satnogs.org/observations/15215597/
      - https://network.satnogs.org/observations/15224574/
      - https://network.satnogs.org/observations/15218429/
      - https://network.satnogs.org/observations/15210626/
      - https://network.satnogs.org/observations/15091869/
      - https://network.satnogs.org/observations/15122755/
  21.
    - **Name:** QO-100 (Es'hail-2, 25.9°E)
    - **Band:** 10489.500-10490.000 MHz narrowband transponder (IF 739.5-740.0 MHz with a 9750 MHz LO); beacons 10489.500 (CW) and 10489.750 (BPSK400); 10491-10499 MHz DATV wideband
    - **Service:** Amateur geostationary transponder
    - **Status:** ACTIVE. AMSAT 'QO-100 [NB] Heard' by many European stations, last on 17 Oct 2026. AMSAT-DL news through Oct 2026 shows no outage. Tier note: a bare TCXO LNB with its own feed is STRICT-tier, and gives beacon, CW and FT8 per documented reports in the inputs. The 20 dBi conical horn (126 mm mouth, 147 mm cone) fits the SMALL tier. The 23 dBi horn (319 mm), the 300 mm lens and any dish are EXCLUDED, and DATV (about 31-32 dBi) is lost.
    - **Status date and source:** AMSAT status 13-17 Oct 2026; AMSAT-DL news (fetched 18 Oct 2026); calculation: Kyiv 186°/32.0°
    - **Sources:**
      - https://www.amsat.org/status/
      - https://amsat-dl.org/en/
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
  22.
    - **Name:** Orbcomm OG2
    - **Band:** VHF 137.25-137.80 MHz downlinks (e.g. 137.288, 137.713, 137.800)
    - **Service:** Commercial M2M messaging. RECEIVE CARRIER/DOPPLER ONLY; user messages EXCLUDED
    - **Status:** OPERATING. SatNOGS good observations of FM108, FM112 and FM118 on 17 Oct 2026. Celestrak's orbcomm group lists 14 objects with 17 Oct 2026 epochs.
    - **Status date and source:** SatNOGS obs 15224838, 15228533 and 15224772 (17 Oct 2026); Celestrak, 17 Oct 2026
    - **Sources:**
      - https://network.satnogs.org/observations/15224838/
      - https://network.satnogs.org/observations/15228533/
      - https://celestrak.org/NORAD/elements/gp.php?GROUP=orbcomm&FORMAT=json
  23.
    - **Name:** Inmarsat-C EGC SafetyNET (Alphasat 24.9°E, Inmarsat-6 F1 83.8°E)
    - **Band:** L-band 1537-1545 MHz STD-C NCS (1200 bps BPSK)
    - **Service:** GMDSS maritime safety broadcasts (SafetyNET MSI) ONLY. FleetNET, LES traffic and Aero are EXCLUDED.
    - **Status:** NETWORK OPERATING, but which satellite serves EMEA is UNVERIFIED. Calculation from Celestrak 17 Oct 2026 elements: Alphasat is at 24.9°E (31.9° elevation from Kyiv), I-6 F1 at 83.8°E (13.9° elevation), and I-4 F2 at about 143.5°E (Celestrak names it SouthPAN PRN 122, so it is out of view from Ukraine). I-6 F2 is drifting at about +2.5°/day. Find the NCS by scanning 1537-1545 MHz. Tier note: an amplified, filtered patch of about 10 cm is the documented antenna for Inmarsat-C, so this target is STRICT-tier.
    - **Status date and source:** Celestrak element sets, 17 Oct 2026 (longitudes are my calculation, about ±0.5°); sigidwiki (2022); UHF-Satcom (2009); no 2026 primary source found
    - **Sources:**
      - https://celestrak.org/NORAD/elements/gp.php?NAME=INMARSAT&FORMAT=json
      - https://celestrak.org/NORAD/elements/gp.php?GROUP=sbas&FORMAT=json
      - https://sigidwiki.com/wiki/Inmarsat-C_TDM
      - https://uhf-satcom.com/satellite-reception/l-band
      - https://www.rtl-sdr.com/rtl-sdr-tutorial-decoding-inmarsat-std-c-egc-messages/
  24.
    - **Name:** Iridium NEXT
    - **Band:** L-band 1616-1626.5 MHz (the ring-alert/simplex channel is near 1626.27 MHz, from gr-iridium documentation, not re-verified)
    - **Service:** Commercial MSS. EXCLUDED from decoding (see excluded list)
    - **Status:** OPERATING. Celestrak's iridium-NEXT group lists 80 objects with 17 Oct 2026 epochs. Ring-alert frames carry subscriber paging identities alongside beam and satellite positions, so only carrier/Doppler observation is allowed.
    - **Status date and source:** Celestrak, 17 Oct 2026
    - **Sources:**
      - https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-NEXT&FORMAT=json
  25.
    - **Name:** GNSS constellations (GPS, GLONASS, Galileo, BeiDou, SBAS)
    - **Band:** L1/E1/B1 1559-1610 MHz (plus L5/E5 1176 MHz)
    - **Service:** Open navigation signals only (GPS C/A, L1C, L5; Galileo OS; GLONASS L1OF; BeiDou B1I/B1C); encrypted military codes EXCLUDED
    - **Status:** OPERATING. Celestrak gps-ops lists 32 objects, glo-ops 29, galileo 32, beidou 54 (BDS-2 and BDS-3 combined) and sbas 21 (EGNOS PRN 121, 123, 136; SDCM Luch-5), all with 17 Oct 2026 epochs. Galileo GSC: 28 usable and 4 not usable (GSAT0201, 0202, 0204, 0210). Jamming and spoofing are widespread in Ukraine (see legal rules). Tier note: a 25 mm ceramic patch is STRICT-tier.
    - **Status date and source:** Celestrak, 17 Oct 2026; GSC constellation page (fetched 18 Oct 2026); NAVCEN returned 403
    - **Sources:**
      - https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=json
      - https://celestrak.org/NORAD/elements/gp.php?GROUP=glo-ops&FORMAT=json
      - https://celestrak.org/NORAD/elements/gp.php?GROUP=beidou&FORMAT=json
      - https://www.gsc-europa.eu/system-service-status/constellation-information
- **Ended or dead:**
  - NOAA-18: decommissioned 6 Jun 2025 17:40 UTC; APT 137.9125 MHz and HRPT 1707 MHz ended (NOAA OSPO).
  - NOAA-19: decommissioned 13 Aug 2025 18:55 UTC after a Battery 1A cell failure; APT 137.1 MHz and HRPT 1698 MHz ended (NOAA OSPO).
  - NOAA-15: decommissioned 19 Aug 2025 20:37 UTC; APT 137.62 MHz and HRPT 1702.5 MHz ended (NOAA OSPO). All 137 MHz APT is gone.
  - Metop-A: decommissioned (NOAA OSPO). Metop-B and Metop-C LRPT on 137 MHz are off (SatDump: off because of interference with HIRS; OSPO shows APT/LRPT red).
  - Meteor-M N2-2: LRPT inoperable after a micrometeorite strike in Dec 2019; in storage mode since Jul 2024 (SatDump).
  - FengYun-3A, 3B and 3C L-band AHRPT ended; FY-3C was the last, in Nov 2024. FY-3D to 3H AHRPT is X-band only (7.8 GHz, 6-38 Msym/s) and needs a dish (SatDump).
  - Elektro-L N2: no xRIT after a power-supply failure. Elektro-L N3: transmissions paused pending L5 commissioning. Elektro-L N5: LRIT/HRIT off for commissioning (SatDump, 2 Jul 2026). Not dead, but there is currently no geostationary L-band LRIT for Ukraine. The SatNOGS DB entry of 7 Apr 2026 conflicts.
  - EWS-G1 (GOES-13): ended 31 Oct 2023 (SatDump). GOES-East and West are below the horizon from Ukraine (calculation).
  - IO-117 GreenCube: no SatNOGS good observation after 25 Jul 2025, and stations stopped scheduling it after 5 Aug 2025. Presumed silent; cause unverified.
  - ISS VHF APRS on 145.825 MHz: no longer listed by ARISS (7 Oct 2026), which gives APRS on 437.825 MHz instead. Three AMSAT 'VHF Digi heard' reports on 17 Oct 2026 conflict.
  - ISS SSTV on 145.800 MHz: the latest listed ARISS event (Series 32, 8-12 May 2026) used 437.550 MHz Robot 36. The last 145.800 MHz events on the ARISS SSTV blog date from Oct-Nov 2024. No event is announced after May 2026.
  - Re-entered (SatNOGS DB; record-update dates are not decay dates): XW-2A, 2B, 2C, 2D, 2E, 2F and CAS-3G (KAITUO-1B); CAS-5A (FO-118); CAS-10 (HO-119); LilacSat-1 (LO-90); Nayif-1 (EO-88); HADES (SO-115); URESAT-1 (SO-120); HADES-D (SO-121); HADES-R (SO-124); HADES-ICM (SO-125); Tevel-1 to -8 (first generation); UVSQ-SAT; Geoscan-Edelveis; SONATE (the first one); INSPIRESat-1; INSPIRE-SAT 7; I-INSPIRE II.
  - Inmarsat-6 F2: drifting at about +2.5°/day (calculation from Celestrak elements); not a usable EGC source. Inmarsat-4 F2 now sits near 143.5°E (Celestrak SBAS group: SouthPAN PRN 122), out of view from Ukraine.
  - Degraded or intermittent rather than dead: AO-91 FM (2 'heard' against 7 'not heard', 13-18 Oct 2026); PO-101 and AO-27 (scheduled or part-time); CAS-3H FM repeater; TO-108; CAS-2T (last good 29 Aug 2026); Metop-B AHRPT (modulator problems).
- **Excluded private or military:**
  - Iridium: voice, SMS/SBD, pager traffic and ring-alert/paging frames, which carry subscriber identities with beam and satellite positions. Under martial law these could help locate users. Carrier and Doppler observation only; no demodulation guide.
  - Inmarsat: STD-C LES and private messages, FleetNET (commercial EGC), Aero ACARS, C-channel voice, Classic Aero, BGAN/GX. Only EGC SafetyNET maritime safety broadcasts are in scope.
  - Orbcomm: subscriber and user message content. Carrier and Doppler only.
  - Starlink, OneWeb, Kuiper and other broadband constellations: all user data. These also need phased arrays or dishes.
  - Thuraya and other MSS voice and data in 1525-1559 / 1626-1660 MHz.
  - Military UHF SATCOM 240-320 MHz (UFO/FLTSATCOM, Skynet, Sicral, Syracuse and others) and MUOS around 360-380 MHz.
  - Military-operated or military payloads: EWS-G2 (GOES-15, US Space Force, 61.5°E; it also needs a dish), reconnaissance and military Kosmos satellites, and Russian military relay systems.
  - Encrypted or restricted GNSS signals (GPS P(Y) and M-code, Galileo PRS, GLONASS P). Do not map or publish GNSS jamming or spoofing sources, since that could reveal EW positions.
  - ISS non-amateur channels: Soyuz/Progress VHF-1/VHF-2 crew voice (143.625 / 130.167 MHz), EVA suit radios (121.x / 139.208 MHz), Dragon/Falcon/Kvant/TORU links. Only NA1SS/RS0ISS amateur modes are in scope.
  - COSPAS-SARSAT 1544.5 MHz repeater downlinks on Meteor-M and Metop, and 406 MHz distress beacons: distress identities and positions.
  - ARGOS/A-DCS (465.9875 MHz) and DCP downlinks of Elektro, Arktika, GOES and FengYun: user platform data such as animal tags and buoys.
  - Terrestrial military, drone or FPV video and telemetry, or police links heard incidentally while scanning: do not record, decode or share.
- **Legal rules:**
  1.
    - **Topic:** Receive-only equipment: licence and registration
    - **Rule:** I found no licence, permit or registration requirement for a receive-only receiver. NKEK's list of radio equipment requiring a frequency assignment (Resolution No. 361, 3 Jul 2024, under Art. 68 of Law 1089-IX) puts broadcast receivers under code ЗД-7: general authorisation, no entry in the frequency-assignment register. Assignments and registration apply to transmitting equipment. Nothing explicitly covers SDR or satellite receivers, so this is an inference. Ask the Ukrainian Amateur Radio League (ЛРУ/UARL) and NKEK in writing, as the inputs already advise.
    - **Source:** https://nkek.gov.ua/static-objects/nkek/sites/1/%D0%A0%D0%9E%20%D1%82%D0%B0%20%D0%92%D0%9F/dodatok-do-postanovy-361-03072024.pdf
  2.
    - **Topic:** Law on Electronic Communications (1089-IX)
    - **Rule:** Law 1089-IX of 16 Dec 2020 has been in force since 1 Jan 2022 and replaced the Law on the Radio Frequency Resource. Under Art. 64, each unit of radio equipment must come with an EU-style declaration of conformity, which matters for imported SDRs and LNBs. Its secrecy-of-communications article was not re-fetched, because zakon.rada.gov.ua returned 503 or reset the connection.
    - **Source:** https://zakon.rada.gov.ua/laws/show/1089-20 (title only fetched); https://protocol.ua/ua/pro_elektronni_komunikatsii_stattya_64/ (search snippet)
  3.
    - **Topic:** Martial law: transmission ban
    - **Rule:** Art. 8 of Law 389-VIII 'On the legal regime of martial law' allows authorities to 'забороняти роботу приймально-передавальних радіостанцій особистого і колективного користування' (ban the operation of personal and collective transmit-receive radio stations) and to restrict information transmission over computer networks (item 11 in the edition checked). An amateur transmit ban has been reported since Feb 2022, and I found no source lifting it. So: receive only, never transmit or uplink (no SO-50 or ISS repeater access), and keep the LimeSDR TX port disabled and terminated.
    - **Source:** https://kodeksy.com.ua/pro_pravovij_rezhim_voyennogo_stanu/8.htm (2019 edition); https://www.arrl.org/news/ukraine-maintains-ham-radio-silence-in-state-of-emergency
  4.
    - **Topic:** Martial law: seizure of equipment
    - **Rule:** Art. 8 (item 12 in the edition checked) allows seizure of telecom equipment, TV, video and audio equipment, computers and 'інші технічні засоби зв’язку' (other technical means of communication) from people who violate the martial-law regime. Expect the receiver to be inspected or seized if it raises suspicion. Carry a Ukrainian-language explanation that it is a receive-only hobby device.
    - **Source:** https://kodeksy.com.ua/pro_pravovij_rezhim_voyennogo_stanu/8.htm
  5.
    - **Topic:** Martial law: term
    - **Rule:** Martial law runs until 31 Oct 2026 under Decree No. 596/2026: 90 days from 05:30 on 2 Aug 2026, approved by Law No. 4928-IX on 14 Jul 2026 and in force from 25 Jul. Another extension is expected but was not found as of 18 Oct 2026. Re-check after 31 Oct.
    - **Source:** https://nfront.org.ua/?p=62502 (secondary); https://www.president.gov.ua/documents/5962026-60509 (returned 403)
  6.
    - **Topic:** Secrecy of communications: Constitution
    - **Rule:** Constitution Art. 31 guarantees the secrecy of correspondence, telephone conversations, telegraph and other correspondence; exceptions are made only by a court in cases set by law. Private satellite traffic is therefore out of scope (see the excluded list). The text was not re-fetched this run because zakon.rada.gov.ua was unavailable.
    - **Source:** https://zakon.rada.gov.ua/laws/show/254к/96-вр (not re-fetched)
  7.
    - **Topic:** Secrecy of communications: Criminal Code Art. 163
    - **Rule:** Violating the secrecy of correspondence, telephone conversations, telegraph or other correspondence sent by means of communication or by computer is punishable by a fine of 50-100 untaxed minimum incomes, correctional labour up to 2 years, or restriction of liberty up to 3 years. Part 2 (repeat offences, or use of special means for covert information removal) carries 3-7 years' imprisonment. This is why Iridium, Inmarsat LES/ACARS and Orbcomm user data are excluded.
    - **Source:** https://urst.com.ua/kku/st-163 (mirror, 05.01.2022 edition)
  8.
    - **Topic:** Special technical means: Criminal Code Art. 359
    - **Rule:** Illegally acquiring, selling or using special technical means for covert information gathering is punishable by a fine of 200-1000 untaxed minimum incomes or up to 4 years; parts 2-3 carry 4-10 years. Whether a general-purpose SDR counts is not settled in commentary. Keep the device a general receiver for public broadcasts, and do not configure, describe or sell it as an interception tool.
    - **Source:** https://urst.com.ua/kku/st-359 (mirror, 05.01.2022 edition)
  9.
    - **Topic:** Publishing receptions: Criminal Code Art. 114-2
    - **Rule:** Added in March 2022 and amended by Law 2178-IX. It punishes unauthorised dissemination, under martial law, of information on the movement of weapons into Ukraine and on the movement or location of the Armed Forces and other formations (part 1: 3-5 years). Part 2 covers locations identifiable on the ground that the General Staff or MoD has not published, and courts have imposed 10 years under part 3. So: no live streams or geotagged photos. Do not publish exact station coordinates (SatNOGS publishes station latitude and longitude; AMSAT reports include grid squares). Do not post imagery or recordings that show or locate strike damage, infrastructure, or military or drone signals.
    - **Source:** https://i.factor.ua/ukr/law-455/section-1525/article-33548/; https://court.gov.ua/press/news/1797902
  10.
    - **Topic:** GNSS jamming and spoofing
    - **Rule:** Ukrainian anti-drone EW spoofs GPS. The General Staff acknowledged that it disrupts smartphone GPS and clocks (2024), and NovAtel (Sep 2025) reported spoofed receivers in Ukraine showing a future GPS week. Do not trust GNSS time or position. Use the RTC and a manually entered locator for pass prediction. Never publish GNSS-derived positions or analyses of interference sources.
    - **Source:** https://therecord.media/ukraine-anti-drone-gps-spoofing-affects-civilian-mobile-phones; https://novatel.com/support/bulletins-alerts-release-notices/technical-update-gnss-spoofing-attacks-in-ukraine
  11.
    - **Topic:** Field safety: unexploded ordnance
    - **Rule:** Set up only on known-safe ground: your own property, paved areas, or areas cleared by the State Emergency Service (ДСНС/SES). Do not enter fields, forest edges or former combat areas, and do not touch suspicious objects. Call 101 (ДСНС). Avoid infrastructure, checkpoints and military sites, where pointing antennas attracts attention.
    - **Source:** Required by the task; 101 = ДСНС emergency number (general knowledge, not re-verified this run)
- **Notes:** INTERPRETATION OF THE 18 OCT 2026 RULE (applied throughout):
  - STRICT tier: largest deployed dimension at most about 12 cm (patches, chip/ceramic antennas, a bare LNB with its own feed, stubby or helical-loaded whips, small loops).
  - SMALL tier: at most about 20 cm (short loaded whips, rubber ducks, a 20 cm patch or loop).
  - EXCLUDED: dishes of any size and anything with a deployed size of about 20-25 cm or more, even if it folds (Yagis, helicone, full telescopic V-dipoles, the 47 cm helix, the 23 dBi horn, the 300 mm lens).
  
  QUARTER-WAVE LENGTHS (calculation, free space):
  - 137.1/137.9 MHz: 54.7/54.3 cm. 145.8-145.96 MHz: about 51.4 cm.
  - 436.8-437.8 MHz: 17.1-17.2 cm (half wave 34 cm).
  - 1544-1700 MHz: 4.4-4.9 cm.
  - Consequences: all VHF targets (Meteor LRPT, AO-91, PO-101, AO-7 mode B, JO-97, AO-73, Orbcomm, SONATE-2 APRS/SSTV) need electrically short antennas in both tiers, and I have not quantified those losses here. That is for the antenna/link agent; at 137-146 MHz, external noise rather than antenna efficiency may set the limit. UHF 435-438 MHz fits the SMALL tier at full quarter-wave size and is about 0.7 of a quarter wave in the STRICT tier. L-band and GNSS are naturally STRICT-tier.
  
  BIGGEST STATUS CHANGES AFFECTING THE RULE:
  (1) ISS APRS is now 437.825 MHz (ARISS, 7 Oct 2026), and the latest ISS SSTV series used 437.550 MHz (May 2026). Both now sit in the small-antenna-friendly UHF band.
  (2) All NOAA APT ended in 2025. 137 MHz weather now means only Meteor-M N2-3 and N2-4 LRPT, both observed on 137.900 MHz this week.
  (3) There is no geostationary L-band LRIT for Ukraine right now. Elektro-L3 is paused and L5 is off for commissioning (SatDump, 2 Jul 2026). This contradicts the inputs' plan to validate antennas on Elektro-L5 LRIT; use FengYun-2H (79°E, 16.6° elevation, linear polarisation) as the reference carrier instead.
  (4) GreenCube IO-117 has been silent since about Aug 2025.
  (5) Inmarsat-4 F2 has moved to about 143.5°E and is out of view. Inmarsat-C EGC for Ukraine must come from Alphasat (24.9°E) or I-6 F1 (83.8°E); which one is unverified.
  
  REACHABILITY HINTS (reusing input numbers; not new link budgets):
  - QO-100 narrowband: the bare TCXO LNB is STRICT-tier (beacon, CW, FT8 documented). The 20 dBi horn (126 mm mouth, 147 mm cone) is SMALL-tier. DATV is lost.
  - Meteor HRPT: only the 4-5 turn helix on an 18 cm plate (11.6-12.0 dBic modelled, 19-22 cm tall, about +5 dB margin) sits at the SMALL-tier edge. A STRICT-tier patch of about 7-8 dBic (aperture estimate) would cut the inputs' roughly 7 dB average SNR to about 1-2 dB against 0.5 dB needed. That is my estimate, assuming SNR scales dB for dB with gain: marginal, high passes only, and unverified.
  - Metop AHRPT and AWS are out of reach in both tiers.
  - Inmarsat EGC SafetyNET and GNSS are STRICT-tier with patches.
  
  METHOD:
  - SatNOGS Network API (good observations, 30 Sep-18 Oct 2026, most with European stations and decoded frames). SatNOGS DB 'alive' flags are often stale, so I relied on observations instead.
  - AMSAT status page, parsed for 13-18 Oct 2026 (the JSON API returned empty).
  - SatDump sat_list.json (last commits 2 Jul 2026); NOAA OSPO Metop (3 Sep 2026) and POES pages.
  - ARISS status (7 Oct 2026) and the ARISS SSTV gallery.
  - Celestrak element sets (17 Oct 2026). GEO longitudes and elevations are my calculations, good to about ±0.5°.
  
  GAPS:
  - zakon.rada.gov.ua returned 503 or reset, so the legal texts come from mirrors with old editions (Criminal Code 05.01.2022; martial-law law 2019 edition). Item numbers and penalties may have changed; re-check on the official site.
  - No 2026 primary source for Inmarsat EGC configuration, Iridium ring-alert frequency, ISS SSTV after May 2026, the martial-law extension past 31 Oct 2026, any lifting of the amateur transmit ban, or LilacSat-3 activity.
  - The president.gov.ua and NAVCEN pages returned 403.
  
  Budget: 12 WebSearch calls. Raw downloads are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/status_dl and scripts in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/status_scripts.

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

## dispmkt:check2 (run `wf_a429c611-ea2`)

- **Name:** AliExpress '2000nit High Brightness Incell Touch CTP 7" 1200*1080 FHD HDMI-Compatible IPS LCD Module' (brand SURENOO, model SUR12001080H070K), item 1005006176909405 / US 3256805990594653
- **Exists and orderable:** ні
- **Confirmed specs:** Only these points could be confirmed, all from search-engine snippets of the AliExpress page. Every primary page was captcha-walled (AliExpress .com/.us/.ru/m., Alibaba) or returned 403 (eBay, surenoo.com).
  - Exact listing title: '2000nit High Brightness Incell Touch CTP 7" 1200*1080 FHD HDMI-Compatible IPS LCD Module Monitor Display Panel Sunlight Outdoor'.
  - Item specifics in the snippet: Brand SURENOO, Model Number SUR12001080H070K, Type TFT.
  - The global ID 1005006176909405 (= US ID 3256805990594653 minus 2^51) answers with a 302 redirect to the US item page, not to an 'item not found' page. So the listing probably still exists, but stock, price and shipping could not be seen.
  - Size 7 in. Calculated PPI is 314.7 if the panel really is 1920x1080.
  Related context, also from snippets only:
  - The two other 7in FHD 2000-nit in-cell offers found are MIPI panels. One is item 3256805881153921, 'Sunlight Readable Screen 7 Inch 1920x1080 2000 Nits ... Wide Temperature ... Automotive LCD'. The other is a Wisecoco 'TOP070FHD03HB', described as 7in 1920x1080, 2000 nits, in-cell, MIPI.
  - So this HDMI module is most likely a MIPI phone-type glass behind an HDMI-to-MIPI bridge board. That is an inference, not confirmed.
- **Refuted or doubtful:**
  - Brightness of 2000 nit is a listing-title claim only. No datasheet, panel part number or independent luminance measurement was found for SUR12001080H070K.
  - Resolution is not established. The '1200*1080' is not a one-off title typo: the seller's own model number SUR12001080H070K encodes the same figure. No standard 7in 1200x1080 panel is known, so the true panel could be 1920x1080 or 1080x1920 (portrait MIPI), or 1200x1920 (a common 7in MIPI format). The candidate's assumed 1920x1080 is unverified.
  - 'Same glass and board as the current Wisecoco pick' is refuted as stated. The brand is SURENOO, not Wisecoco. There is no evidence that it uses the same panel, the same bridge board, or the CH57x USB-HID touch bridge.
  - The touch path to the host is not documented. In-cell TDDI touch outputs I2C/SPI, and the board would need an MCU that converts it to USB HID. No VID:PID, controller chip or USB connector was found.
  - The $106.09 price comes from an earlier search snippet. It could not be re-read, and shipping and the final price to Ukraine are unverified.
  - Does not meet the 'above Full HD' wish. At best it is exactly FHD, and if 1200x1080 were real it would be below FHD.
  - Cover glass, AR/AG coating and optical bonding are unknown. The listing says only 'in-cell CTP'.
  - If the native mode is portrait 1080x1920 (likely for MIPI glass), the host must rotate the picture. The vertical blanking on phone-panel EDIDs is often under 24 lines (e.g. VFP+VSW+VBP of about 20 to 22), which would break the Q6A DP rule. This is unverified, so an EDID dump is needed.
- **Touch reaches host as usb hid:** unknown
- **Q6a mode line and link check:** All figures below are calculations. The native EDID is unknown, so several native-mode cases are covered.
  - Native 1920x1080@60:
    - CVT-RB v1 timing: 2080x1111, vblank 31 (meets the 24-line rule), 138.5 MHz. That is 3.32 Gbps, or 38% of the 8.64 Gbps 2-lane HBR2 payload.
    - 1920 px is under the 2400 px DPU linewidth, so no virtual planes are needed.
  - Native portrait 1080x1920@60 (likely for MIPI glass):
    - RB v1: 1240x1975, vblank 55, 146.75 MHz, 3.52 Gbps (41%).
    - RB v2: 1160x1975, 137.46 MHz.
  - Native 1200x1920@60: RB v1 1360x1975, 161.0 MHz, 45% of the link.
  - Every case fits the link with a large margin and under 330 MHz, and stays under the 2400 px limit.
  - The real constraint: an HDMI-to-MIPI bridge (LT6911/TC358870 class) usually passes timing through to the panel. The host must then send the panel's native porches. If the EDID's VFP+VSW+VBP is under 24, add lines to VFP (and lower the refresh rate) in a custom mode, then confirm the panel and the in-cell touch tolerate it.
  - RF-clean examples, checked against harmonics 1 to 40 with a 1 MHz guard:
    - Portrait: 1080x1920 at htotal 1240, vtotal 1975, 135.7 MHz = 55.4 Hz. The same timing at 128.6 MHz gives 52.5 Hz.
    - Landscape: 1920x1080 RB at 2080x1111 and 135.7 MHz = 58.7 Hz. CEA 2200x1125 at 128.7 MHz = 52 Hz.
    - Each needs about 3.1 to 3.3 Gbps (36 to 38% of the link).
  - Clean pixel-clock windows between 125 and 160 MHz: 127.85-129.35, 135.4-135.95, 153.4-153.5 and 155.55-157.05 MHz.
- **Rf harmonics check:** All calculations; native clocks are assumed.
  - 148.5 MHz (CEA 1080p60): x5 = 742.5 MHz (QO-100 IF), x15 = 2227.5 MHz.
  - 138.5 MHz (CVT-RB 1080p60): the fundamental sits 0.5 MHz above the 137-138 MHz weather-satellite band; x16 = 2216 MHz.
  - 146.75 MHz (RB v1 1080x1920@60): x15 = 2201.25 MHz.
  - 137.46 MHz (RB v2 portrait 60 Hz): the fundamental is inside 137-138 MHz.
  - About 145.2 MHz (a common portrait clock): the fundamental is in 144-146 MHz and x3 = 435.6 MHz.
  - 1080x1920@52 RB v1 (126.75 MHz) is not clean: x18 = 2281.5 MHz. 1200x1920@52 RB v2 (130.99 MHz) hits 1702.9 and 2226.8 MHz.
  - Clean choices: see the modes and windows in the mode-line check (e.g. 135.7 MHz or 128.6/128.7 MHz).
  - Extra source on a MIPI bridge board: the 4-lane DSI clock lane runs at about 3 x the pixel clock.
    - At 145.2 MHz pixel clock, the clock lane is at 435.6 MHz, inside the 435-438 band.
    - At 141 MHz, x4 of the clock lane is 1692 MHz.
    - At 148.5 MHz, x5 is 2227.5 MHz.
    - The bridge's DSI rate is often set independently, so ask for it.
  - The LED boost converter and the TDDI scan are further broadband sources. Plan shielding, ferrites on the HDMI and USB cables, and test with the SDR before final assembly.
- **Power and thermal:** No power figure was found for this item. Everything below is an engineering estimate, not a sourced number.
  - Power: a 7in, 314 ppi IPS panel at 2000 nits typically means a strong edge-lit LED bar. The estimate is about 6-12 W total for backlight, panel and bridge at full brightness.
  - Supply: this rules out powering it from a Q6A USB-A port (500 mA x 5 V = 2.5 W). Use the 12 V rail and a dedicated buck, budgeting about 1-1.5 A at 12 V until a measurement exists.
  - Heat from sunlight: about 13.5 W of sun lands on the 155.0 x 87.2 mm active area at 1000 W/m² (calculation), and much of it is absorbed in the polarizers and the backlight.
  - Total heat: together with the backlight, roughly 20 W of heat in a 7in handheld.
  - Overheating risk: blackout above the liquid crystal's clearing point and accelerated LED ageing.
  - Mitigation: an aluminium back plate or heat spreader on the LED-bar edge, a sun hood, and running below 100% where possible. Brightness control must exist (button, USB or DDC), and its PWM frequency matters for RF and flicker.
- **Sunlight readability estimate:** Calculation for 100 klx direct sun on the screen, using diffuse reflectance R; specular glare is not included.
  | Luminance | R = 0.5% | R = 1% | R = 2% |
  |---|---|---|---|
  | 2000 nit (if true) | 13.6:1 | 7.3:1 | 4.1:1 |
  | 1000 nit (if the title overstates) | 7.3:1 | 4.1:1 | 2.6:1 |
  | 700 nit | | 3.2:1 | |
  - In-cell touch avoids the extra touch sensor and air gap of a separate touch layer, which lowers reflections. That is a plus.
  - Uncoated cover glass still gives about 4% specular reflection per surface, so AR/AG coating and optical bonding decide real-world readability.
  - With an IPS polarizer at 0°/90°, the screen can black out through polarized sunglasses in one orientation. Ask for the polarizer axis.
  - Verdict: readable in direct sun only if the 2000 nits is real and the front stack is coated or bonded; neither is confirmed.
- **Real price and shipping to ukraine:** Not verified. The only figure is the earlier search snippet of $106.09 (Oct 2026); the page itself is captcha-protected and could not be read.
  - Shipping to Ukraine for this item, and the final landed price, are unknown. AliExpress generally ships to Ukraine, but that was not confirmed for this listing.
  - Add Ukrainian import VAT or duty if the parcel exceeds the current duty-free threshold; check the rules that apply on the order date.
  - Comparison prices, all from snippets: Wisecoco site kit $132 (current pick); MIPI-only 2000-nit 7in FHD in-cell item 3256805881153921 at $160.32; VSDISPLAY 6.97in 1080x1920 2000-nit MIPI on-cell with an 'HD board' at about £119 on eBay.de 256679793470.
- **Questions for seller:**
  - What is the real native resolution and orientation? Your title and model number SUR12001080H070K both say 1200*1080. Is it 1920x1080, 1080x1920 or 1200x1920?
  - What is the panel's part number and manufacturer, and can you send its datasheet? Is the 2000 cd/m2 figure typical or minimum, and is it measured at the cover glass with touch?
  - Please send the full EDID dump (hex) from the HDMI board: preferred mode, pixel clock, porches and sync widths. Does it accept 50-58 Hz, a modified VFP, or custom pixel clocks such as 128.6 or 135.7 MHz?
  - Which bridge chip is on the board (e.g. LT6911UXC, TC358870)? What is the DSI lane count and per-lane bit rate?
  - How does touch reach the host: a separate USB port, the touch controller chip, and the 'lsusb' VID:PID? Is it a standard HID multitouch device that works on Linux without drivers, and how many touch points does it report?
  - Does in-cell touch keep working if the refresh rate is changed from 60 Hz (e.g. 52-58 Hz)?
  - What is the supply voltage and current at 100% brightness? How is brightness controlled (buttons, USB, DDC/CI), and what are the backlight PWM frequency and LED driver switching frequency?
  - What are the operating and storage temperature ranges, and the clearing-point or sunlight-heating behaviour? Is there a metal back frame?
  - What are the cover glass thickness, AR/AG coating and optical bonding, and the polarizer orientation?
  - What exactly is in the box (FPC, HDMI and USB cables, board)? What is the shipping method and cost to Ukraine (Nova Poshta/Ukrposhta), and is there a warranty or DOA policy?
- **Keep:** ні
- **Reason:** It does not survive checking. Every key claim rests on one AliExpress title, and that title contradicts itself ('1200*1080' and 'FHD'). The seller's model number SUR12001080H070K repeats the odd 1200x1080, so the resolution is unknown, not merely a typo.
  - Brightness has no datasheet or measurement behind it.
  - The brand is SURENOO, not Wisecoco, so the 'same glass and board as the current pick' assumption is unfounded.
  - There is no evidence of how touch reaches the host (no chip or VID:PID).
  - Price, stock and shipping to Ukraine could not be read because the pages are captcha-walled.
  - Even in the best case it is only FHD, not above FHD.
  Electrically, any of the plausible native modes fits the Q6A link easily: 36-45% of 2-lane HBR2 and under 2400 px wide. But a MIPI-bridge board may expose phone-panel porches with fewer than 24 blanking lines. Likely default clocks (138.5, 145, 146.75 or 148.5 MHz) also land harmonics or fundamentals in our bands, so a custom clean mode (e.g. 135.7 MHz) must be confirmed to work with the panel and its in-cell touch.
  Treat it as a lead only: re-evaluate if the seller supplies the panel datasheet, an EDID dump and the lsusb VID:PID. Until then, the current pick stays ahead.
- **Sources:**
  - https://www.aliexpress.com/item/1005006176909405.html (search-snippet title + item specifics SURENOO / SUR12001080H070K; 302 redirect to the US page; page captcha-protected)
  - https://www.aliexpress.us/item/3256805990594653.html (captcha / login-cookie redirect loop, unreadable)
  - https://www.aliexpress.us/item/3256805881153921.html (snippet: 'Sunlight Readable Screen 7 Inch 1920x1080 2000 Nits ... Wide Temperature ... Automotive LCD', MIPI)
  - https://www.aliexpress.us/item/3256805758322161.html (snippet: '7 Inch 2400Nits IPS LCD Touchscreen Module')
  - https://www.alibaba.com/product-detail/7-Inch-1920-1080-FHD-IPS_10000041147858.html (captcha, unreadable)
  - https://www.ebay.de/itm/256679793470 (snippet: VSDISPLAY 6.97in 1080x1920 2000 nits IPS MIPI 39-pin on-cell + HD board, ~GBP 119; 403 to fetch)
  - https://www.ebay.de/itm/176657492046 (snippet: Wisecoco 7in 1920x1080 2000 nits touch HDMI kit, listing ended; 403 to fetch)
  - https://www.surenoo.com/ (403 Access Denied to fetch)
  - Calculation scripts: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/calc/t.py and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/calc/m.py

## dispmkt:check3 (run `wf_a429c611-ea2`)

- **Name:** Youritech ET070WU10-TT / ET070WU15-TT, 7.02in 1200x1920 MIPI, 1500 cd/m2 typ., CTP optional (HDMI board only "by quote")
- **Exists and orderable:** ні
- **Confirmed specs:** Two Youritech product pages exist with the same specs. ET070WU10-TT (page slug 7-02-inch-...-1500nits-lcd-module) and ET070WU15-TT (its page sits under a wrong 4-inch ILI9806E slug) both list: 7" 1200x1920, "Panel Interface: MIPI" (lane count not stated), Transmissive, outline 114.04x178.25 mm (with touch), active area 94.5x151.2 mm, viewing angle 85/85/85/85, "Brightness (cd/m2): 1500(Typ.)", operation -20~70 C / storage -30~80 C, "Touch: yes". On the ET070WU10-TT page, the reference table has a 1200x1920 row: HX8279 driver, bare LCM 105.18x163.34x3.65 mm, the same 94.5x151.2 mm active area, "MIPI 4 LANE", reference brightness 1600, no CTP. That is probably the bare glass under the TT part, but the page does not tie the row to the TT part. The page also has generic marketing copy ("Brightness from 0-3000", "100% NTSC", "Touch Screens are Available and Optional", "Driver board/adapter board ... DEMO board, H-DMI board", "H-DMI display solution"). These are not specs of this part. Calculated: diagonal 7.02", 322.5 PPI. 1200x1920 (WUXGA) has 11% more pixels than FHD. The only purchase action is "Get a quote". Vendor: Youritech, Dalang, Longhua, Shenzhen.
- **Refuted or doubtful:**
  - The candidate's second source URL (...1500nits-ips-1200x1920-mipi-tft-lcd-display-2.html) is a different part: ET070WU18-OT, 'Touch: no', -10~60 C, 80/80/80/80, outline 113.89x176.6 mm. It does not support the touch claim.
  - The quoted 'ET070WU15-TT reference line ... CTP' is not in the page's reference table. The table's 7in 1200x1920 HX8279 row says 1600 nits, 105.18x163.34 mm, no CTP. The ET070WU15-TT specs are on its own (wrongly slugged) product page.
  - Brightness: '1500(Typ.)' is a vendor spec-table value on the product page. No datasheet, no minimum value and no independent measurement. Youritech's own figures disagree: the reference table says 1600 for the bare LCM, and sister parts with the same active area (ET070WU01-TT 1300 typ., ET070WU12-O 1500 typ., no touch) differ.
  - 'Customizable 0-3000 nits' is generic marketing copy, not a spec for this part.
  - Touch: the controller IC, the interface (I2C vs USB) and VID:PID are all unstated. No Youritech page shows a 7in 1200x1920 HDMI kit. The only Youritech HDMI kit that documents touch is a 4in 720x720 one ('USB touch', FT6336U), which suggests USB touch is possible but proves nothing for this part.
  - The HDMI board is not a product. There is no chip, EDID, input timing, power input or price. Youritech's 4in kit describes its board as 'HDMI1.4 to Dual-port MIPI DSI/CSI/LVDS with Audio', which looks like a Lontium LT6911C-class bridge (my inference, not stated).
  - Not orderable now: quote only, no price, MOQ or lead time, and no Alibaba/AliExpress listing found.
  - No datasheet, power figure, contrast ratio, surface treatment or optical-bonding statement.
  - No community reports found for Youritech parts.
  - The candidate's 'clean at 51.3-51.8 Hz (128-129 MHz)' only holds for ~1280x1950 totals. With an HX8279-7in-style native timing (1340x1946 totals), 51.5 Hz = 134.3 MHz, whose 17th harmonic is 2283 MHz (in band), and 52 Hz = 135.6 MHz, which is 1.4 MHz from 137 MHz (calculated).
- **Touch reaches host as usb hid:** unknown
- **Q6a mode line and link check:** The Youritech panel's own timing is unpublished. As a proxy I used the mainline Linux panel-himax-hx8279 driver's timing for the Startek KD070FHFID078, a 7in 1200x1920 HX8279 panel of 95x151 mm: 156.458 MHz, H 1200/1250/1274/1340, V 1920/1934/1936/1946, 60.0 Hz. As a modeline: 156.458 1200 1250 1274 1340 1920 1934 1936 1946. Checks (calculated):
  (a) Width 1200 px is under the sc7280 DPU 2400-px max_linewidth, so no virtual planes are needed. Landscape use needs compositor rotation.
  (b) V blanking is VFP 14 + VSW 2 + VBP 10 = 26 lines. That passes the 24-line rule, with little margin.
  (c) Link: 156.458 MHz x 24 bpp = 3.755 Gbit/s, which is 43% of 2-lane HBR2 (8.64) and also fits 2-lane HBR (4.32), but not RBR (2.59). The pixel clock is far below the 268.5/330 MHz ceilings.
  (d) Generic CVT timings: CVT-RB v1 1200x1920@60 = 1360x1975, 161.00 MHz. CVT-RB v2 = 1280x1975, 151.68 MHz. Both pass the link and blanking rules but are RF-bad (see RF check).
  The real constraint is the HDMI-to-MIPI board's EDID/firmware. It must present a mode the panel accepts, and the panel's legal porch and pixel-clock range is unknown. Direct MIPI-DSI to the Q6A is unproven: mainline has an HX8279 driver, but the init sequence for this glass is unknown.
- **Power and thermal:** No power, backlight or supply figures are published. Estimates (calculated, not vendor data): backlight about 4-5 W at 1500 nits for 7" (a 7" panel at ~450 nits is typically ~1-1.3 W), LCD and driver IC 0.3-0.5 W, and an HDMI-to-MIPI bridge board plus USB-touch MCU 0.5-1 W. Total about 5-7 W, roughly 0.45-0.6 A from the 12 V rail through the separate buck. The Q6A's 500 mA USB-A ports cannot power it. Board input voltage is unknown.
  Sun load: about 20 W of sunlight falls on the 114x178 mm face at 1000 W/m2 (calculated), on top of the backlight heat. Rated operation tops out at 70 C, and the LC clearing point is not stated. In a Ukrainian summer the panel can approach that limit, so plan a metal backplate heat path, PWM/auto-dimming and thermal derating.
- **Rf harmonics check:** Pixel-clock harmonics against 137-138, 144-146, 435-438, 739-750, 1690-1710 and 2200-2300 MHz (calculated):
  - HX8279-7in native-style 156.458 MHz @60: no harmonic in any band. Nearest is 14x = 2190.4 MHz (9.6 MHz below 2200); others are 11x = 1721 and 15x = 2347. GOOD.
  - CVT-RB v1 161.00 MHz: 14x = 2254.0 (in band). BAD.
  - CVT-RB v2 151.68 MHz: 15x = 2275.2 (in band). BAD.
  - Candidate's 149.8 MHz: 5x = 749.0 (QO-100 IF) and 15x = 2247. BAD.
  - With 1340x1946 totals, the windows with at least 3 MHz margin to all bands are 59.75-60.15 Hz (155.8-156.85 MHz) and 49.10-49.55 Hz (128.0-129.2 MHz). 51.5 Hz (134.3 MHz) hits 2283 MHz, and 52 Hz (135.6 MHz) sits 1.4 MHz from 137.
  - Bridge-side DSI, if 4 lanes at 6x pclk (938.8 Mbit/s, 469.4 MHz clock at 60 Hz): odd harmonics 1408 and 2347 MHz are clean. The bridge's real DSI lane rate is unknown and must be asked; at a 151.68 MHz pclk the DSI clock's 5th harmonic would be 2275 MHz.
- **Sunlight readability estimate:** Estimate (calculated, assuming 1500 cd/m2, CR 1000:1). Unbonded panel with an air-gap CTP and anti-glare polarizer, about 2% diffuse reflectance: ambient contrast about 3.4 at 100 klx (sun on the screen) and 5.7 at 50 klx. The air gap also adds about 8% specular reflection, so a 6000 cd/m2 sky adds about 480 cd/m2 of glare unless the screen is tilted. If Youritech optically bonds the CTP with an AR cover (about 1% diffuse), contrast rises to about 5.7 at 100 klx and 10 at 50 klx. Verdict: readable but marginal in full direct sun unless it is bonded with AR/AG. Bonding is not stated on any page.
- **Real price and shipping to ukraine:** Unknown. Every ET070WU page offers only 'Get a quote', and no Alibaba or AliExpress listing or Ukrainian seller was found. Shipping must be quoted by Youritech (express from Shenzhen). Budget for Ukrainian import VAT and duty if the parcel is over the current duty-free threshold.
- **Keep:** ні
- **Reason:** The panel and part numbers exist, and the technical fit looks good on paper. Portrait 1200 px avoids the DPU 2400-px limit. A native-style 156.46 MHz @60 mode uses 43% of 2-lane HBR2, has 26 lines of V blank, and is RF-clean, while generic CVT-RB EDIDs land at 2254 or 2275 MHz. But it fails the 'orderable and verifiable' test. The brightness comes only from a vendor spec table, with conflicting 1300/1500/1600 figures across sister parts. There is no datasheet or power data. Touch is 'optional' with no controller, interface or USB-HID evidence. The HDMI board exists only as a generic 'H-DMI board' offer, with no chip, EDID, power or price. The second source URL is a non-touch part. Quote only, with no community reports. I'd park it as an RFQ-only backup and revive it only if Youritech returns a datasheet, a concrete HDMI board with USB-HID touch (VID:PID) and an EDID dump, plus a price.
- **Sources:**
  - https://www.youritech.com/products/7-02-inch-tft-lcd-display-1200x1920-mipi-high-brightness-1500nits-lcd-module.html
  - https://www.youritech.com/products/4-inch-ips-lcd-display-paypal-mipi-interface-ili9806e-driver-ic-with-back-light-for-3d-printing-ar-vr-application.html
  - https://www.youritech.com/products/7-inch-high-brightness-display-1500nits-ips-1200x1920-mipi-tft-lcd-display-2.html
  - https://www.youritech.com/products/7-inch-high-brightness-display-1500nits-ips-1200x1920-mipi-tft-lcd-display.html
  - https://www.youritech.com/products/7-inch-high-brightness-display-1300nits-ips-1200x1920-mipi-tft-lcd-display.html
  - https://www.youritech.com/products/5-2-7-inch-displays/
  - https://www.youritech.com/products/4-inch-720x720-tft-lcd-display-mipi-dsi-lcd-module-with-hdmi-driver-board.html
  - https://www.youritech.com/products/hdmi-raspberry-solutions/
  - https://raw.githubusercontent.com/torvalds/linux/master/drivers/gpu/drm/panel/panel-himax-hx8279.c
  - https://unisystem.com/product/displays-lcd-tft/wf70c6tyab5mnn0-winstar-7-1200x1920-lcd-tft-display
- **Questions for seller:**
  - Which exact part, ET070WU10-TT or ET070WU15-TT, and what is the difference? Please send the full datasheet: panel OEM, glass part number, driver IC (HX8279?), DSI lanes, timing table with min/typ/max pixel clock, porches and refresh range.
  - Is 1500 cd/m2 typical or minimum, and measured with or without the CTP? Please send a luminance test report and backlight specs: LED strings, Vf, If, LED driver, power at full brightness, PWM dimming range and frequency.
  - Is the CTP optically bonded? Cover-glass thickness, AR/AG coating and reflectance? Can you bond it with an AR glass?
  - Touch controller IC (GT911/FT5x?) and interface. Can the HDMI board give native USB HID multitouch (Windows/Linux hid-multitouch, no driver)? Please send the USB VID:PID and the lsusb -v / HID descriptor.
  - Which bridge chip is on the HDMI board (LT6911C?), with which firmware? Please send the EDID dump. Can you program a custom EDID: 1200x1920, 156.458 MHz, H 1200/1250/1274/1340, V 1920/1934/1936/1946 (VBP+VSW+VFP 24 lines or more), and optionally ~49.3 Hz / 128.5 MHz? Do you accept portrait-native 1200x1920 HDMI input without scaling?
  - What DSI lane rate does the bridge use for this panel (fixed or derived from pclk)?
  - HDMI board input voltage and current (5 V or 12 V), total power at full brightness, connector type, and board size?
  - Clearing point and max operating temperature under sun load. Is there a thermal or metal-frame recommendation?
  - Price for 1-2 samples (panel + CTP + HDMI board + cables), lead time, and an express quote to Ukraine (DDP if possible).

## dispmkt:check4 (run `wf_a429c611-ea2`)

- **Name:** Youritech ET070WU07-O, 7.0 in 1200x1920 MIPI panel claimed at 1500 nits, no touch. The claim that it is "identical to the Wisecoco $69 500-nit kit panel" is tested here.
- **Exists and orderable:** ні
- **Confirmed specs:** These are Youritech's own pages and images only. No datasheet is published anywhere.
  (1) Two live Youritech product pages carry part number ET070WU07-O. Both are "Get a quote" only, with no price, MOQ, stock or datasheet. Images on the first page were uploaded 2021/08 and on the second 2020/03.
  (2) 7.0 in (7.02 in calculated from the active area), 1200(RGB)x1920 portrait, RGB vertical stripe, 0.07875 mm pitch, active area 94.5x151.2 mm. 322.5 PPI (calculated).
  (3) Interface is MIPI DSI 4-lane, per the image banners "MIPI 4 lane" (2020/03/ET070WU07-O_01.jpg) and "MIPI 4 lane interface" (2021/08/ET070WU07-O_01.jpg). The text field reads "Dgital".
  (4) IPS, normally black, 80/80/80/80 viewing angle, contrast 1200:1 (typ). Hard-coat surface treatment, no TSP, no cover glass.
  (5) Backlight is "45 PCS WHITE LED, 20Khours", and the field "Backlight power consumption" says "9~11v". Logic is 5.5 V typ at 60 mA.
  (6) Luminance is 1500 cd/m2 typ. This comes only from Youritech's spec table and a marketing banner ("1200(RGB)x1920 · 1500 cd/m2 Brightness"). There is no minimum value, no measurement conditions and no independent measurement.
  (7) The photos show an orange FPC folded across the back of one short edge, with a connector on its top edge and two bonded tails. A separate 2-wire backlight lead exits the long side. A dark backlight/frame strip sticks out past the glass on one long side.
- **Refuted or doubtful:**
  - OPERATING TEMPERATURE REFUTED: the candidate says -20 to 70 C and calls the sisters 'only -10 to 60 C'. Youritech's second ET070WU07-O page (7-inch-high-brightness-display-1500nits-1200x1920-mipi-tft-lcd-display.html) says -10~60 C operating and -30~70 C storage. Youritech's own cross-reference list on its 7-inch pages also says 'ET070WU07-O (LCD, 1200x1920, MIPI, 1500nits, -10~60 C, 160.8x98.7mm)'. Only the 2021 page says -20~70 C.
  - OUTLINE CONTRADICTED: the text says 160.80x98.70x1.97 mm. The 'Product parameters' dimension image on the same page (uploads/2021/08/ET070WU07-O_02.jpg) gives 107.98 x 163.8 mm overall. That is exactly the outline Youritech lists for ET070WU12-O, and for ET070WU10-O (107.98x163.8x4.05 mm, 1350 nits, 4-lane MIPI 40 pins). The photographed module has a backlight frame wider than the glass and external LED leads. A 1.97 mm thickness is doubtful for a 45-LED, 1500-nit module, since the same-outline ET070WU10-O is 4.05 mm. The text outline is probably the bare base cell copied from another datasheet.
  - PANEL TECHNOLOGY CONTRADICTED: the text table says 'a-Si TFT-LCD', but the page's own banner image says 'LTPS TFT active matrix'. Wisecoco's panel is listed as LTPS.
  - WISECOCO-COMPATIBILITY HYPOTHESIS UNSUPPORTED AND VISUALLY CONTRADICTED: the FPC in Wisecoco's rear photo (wp-content/uploads/2026/05/7-inch-1920-1200-lcd-2-2.webp) has two green rigid islands with inductors, a board-to-board connector, a flex tail and the label '8813070'. It has no separate backlight wires. Youritech's FPC is a different wide flex with a top-edge connector (it looks marked '30', unconfirmed) and has external backlight wires. Different FPC means a different pinout and power scheme. Wisecoco's 40-pin adapter and HDMI-to-MIPI board cannot be assumed to work. The only things that match are the text outline 160.8x98.7 and the -10~60 / -30~70 C temperatures. Those hint at a shared base glass with a re-backlit module, but that is not proven.
  - Contrast differs: Youritech says 1200:1 and Wisecoco says 1100:1. Not decisive, but more evidence the documents are not for the same part.
  - 1500 nits is vendor marketing and a table value only. Youritech lists a same-outline sibling at 1350 nits (ET070WU10-O). There is no datasheet minimum and no measured value from anyone.
  - The backlight field '9~11v' is garbled: no current is given, and it is unclear whether a driver is on board. The external 2-wire lead suggests a bare LED string that needs a constant-current driver. Assuming 3S x 15P (an inference from 45 LEDs and 9-11 V), current would be about 300-600 mA. Unverified.
  - No HDMI path exists for this panel. Youritech advertises driver boards in general but none for this part. The Q6A's MIPI-DSI only supports Radxa panels, so the panel cannot be driven directly.
  - No touch, which fails a hard requirement.
  - No community reports, teardown, or luminance review found. Not on prom.ua (search for 'ET070WU07' returns nothing). No Alibaba or Made-in-China listing found.
- **Touch reaches host as usb hid:** no
- **Q6a mode line and link check:** Calculated, assuming some unknown HDMI-to-MIPI bridge sits in front of the panel. The Q6A cannot drive this MIPI panel directly.
  
  Width and blanking: 1200 px is under the 2400 px DPU linewidth, so no virtual planes are needed.
  
  Standard modes and their harmonics:
  - CVT-RBv2 1200x1920@60: htotal 1280, vtotal 1975 (55 lines vertical blanking, meets the 24-line rule). 151.68 MHz, 3.64 Gbps. Fits 2-lane HBR (4.32) and HBR2 (8.64). The 15th harmonic, 2275.2 MHz, falls in 2200-2300.
  - CVT-RBv1 @60: htotal 1360, vtotal 1975, 161.0 MHz, 3.86 Gbps. The 14th harmonic, 2254 MHz, falls in 2200-2300.
  - JDI LT070ME05000-style native timing (from memory of the mainline panel driver, not verified): 1340x1934@60, 155.49 MHz, only 14 lines of vertical blanking. If a bridge's EDID copied this, it would break the 24-line DP rule. Its 11th harmonic, 1710.4 MHz, sits on the 1690-1710 edge.
  - RBv2 @50: 125.82 MHz. The 18th harmonic, 2264.8 MHz, falls in 2200-2300.
  
  Harmonic-clean custom modes (up to the 20th harmonic, calculated):
  - 1360x2042@60: 166.63 MHz, 4.0 Gbps, 122 lines vertical blanking. Nearest harmonic is 20.6 MHz from any band. Fits HBR.
  - 1304x1994@60: 156.01 MHz. Only 6 MHz margin: the 11th harmonic is 1716.1 MHz.
  - 1296x1986@50: 128.69 MHz, 3.09 Gbps. Same clock as your known-clean 1080p@52 mode.
  
  These modes only help if the bridge's EDID or scaler accepts custom timings. The bridge's own DSI clock is free-running: about 455-483 MHz at 4 lanes x ~0.9-0.97 Gbps. At 151.68 MHz input its 5th harmonic is about 2275 MHz, which is in band. Its scaler and DDR clocks are also uncontrolled and need sniffing with the receiver itself.
- **Rf harmonics check:** All figures calculated.
  - CVT-RB 60 Hz modes (151.68 and 161.0 MHz) land in 2200-2300 MHz at the 14th-15th harmonic.
  - A JDI-like 155.49 MHz timing hits 1710.4 MHz.
  - 50 Hz RBv2 (125.82 MHz) hits 2264.8 MHz.
  - Clean choices: 1360x2042@60 at 166.63 MHz (at least 20 MHz margin), or 1296x1986@50 at 128.69 MHz (8.3 MHz margin).
  - The bridge board adds its own DSI HS clock (about 455-483 MHz; at 455 MHz the 5th harmonic is 2275 MHz) plus scaler and DDR clocks the host cannot control. Real emissions are broadband around these lines, so a near-field scan with the SDR across all six bands is mandatory.
- **Sunlight readability estimate:** Calculated ambient contrast (ACR) in 100 klx sun, with diffuse reflectance Rd:
  - At the claimed 1500 nits: about 5.7 with the bare hard-coat (Rd about 1%), about 3.4 with an air-gapped add-on CTP (Rd about 2%), about 10 with a bonded AR cover (Rd about 0.5%).
  - If real luminance is only 750-1000 nits (plausible, given the 1350-nit sibling and no minimum spec): about 3.3-4.1 bare, and about 2.2-2.6 with an air-gapped touch panel.
  - Readable in direct sun only if the 1500 nits is real and any touch layer is optically bonded. The hard-coat (non-AR) surface gives strong specular glare.
- **Power and thermal:** Estimated, not from a datasheet.
  - Backlight: assuming 45 LEDs as 3S x 15P at 9-11 V (inference) and 20-40 mA per string, about 3-6.6 W.
  - Panel logic: 5.5 V x 60 mA = 0.33 W (Youritech figure).
  - HDMI-to-MIPI scaler or bridge board: about 1-2.5 W (estimate).
  - Total: about 4.5-9 W, roughly 0.35-0.7 A from the 4S pack.
  - An external constant-current LED driver is probably needed. A buck driver from the 12 V Pololu rail has only about 1 V of headroom at an 11 V string voltage, so a buck-boost or SEPIC CC driver from the pack is safer.
  - Heat: about 75-80% of backlight power becomes heat inside a thin module. Full sun adds about 14.3 W incident on the active area (1000 W/m2 x 0.0143 m2, calculated).
  - Youritech's own catalog line rates operating temperature at only -10~60 C. That is easy to exceed in a closed handheld in Ukrainian summer sun. Expect forced derating of the backlight and possible LC blackening near the clearing point.
- **Real price and shipping to ukraine:** Unknown. Youritech publishes no price: both ET070WU07-O pages are quote-only B2B with MOQ not stated. For reference, the Wisecoco 500-nit kit is $69.00 with the HDMI-to-MIPI 40-pin board (verified on wisecocodisplay.com). Its compatibility with this panel is not established. No Ukrainian seller: prom.ua search for ET070WU07 returns nothing. Shipping would be express courier from Shenzhen (cost not verified). Budget for customs and VAT, and confirm the current Ukrainian duty-free threshold. Add the cost of a separate LED driver, a bridge board and a bonded PCAP with a USB controller, none of which is quoted.
- **Questions for seller:**
  - Send the full spec-approval datasheet for ET070WU07-O, with minimum and typical luminance, the measurement method, and the LED configuration (series/parallel, Vf, If per string, total power).
  - Your two ET070WU07-O pages conflict. Which outline is correct: 160.8x98.7x1.97 mm or 107.98x163.8 mm (and what thickness)? Which temperature range: -20~70 C or -10~60 C? Which technology: a-Si or LTPS?
  - Who makes the base glass and what is its part number? Which driver IC? What is the FPC pin count, pinout and mating connector part number? Please provide the DSI init sequence and the native timing (HFP/HBP/HSA, VFP/VBP/VSA, pixel clock).
  - Is the backlight a bare LED string on a separate cable? Which constant-current driver and dimming method (PWM frequency) do you recommend?
  - Do you supply an HDMI-to-MIPI board proven with this exact panel? Which bridge chip? What EDID (preferred mode, portrait 1200x1920 input or scaled 1920x1200)? Does it accept custom timings such as 1360x2042@60 at 166.6 MHz or 1296x1986@50 at 128.7 MHz, with at least 24 lines of vertical blanking? What are its supply and power?
  - Can you optically bond a PCAP with a USB-HID controller (give the controller IC and USB VID:PID) and an AR or AG cover glass? Price and MOQ?
  - Can you provide a luminance measurement report from a production sample at rated current, plus backlight derating versus temperature and the LC clearing point?
  - What are the sample price, MOQ and lead time? Is there DDP or DAP shipping to Ukraine, and what warranty applies?
- **Keep:** ні
- **Reason:** Drop. The candidate fails a hard requirement: it has no touch. It has no HDMI path; the only proposed path, Wisecoco's 40-pin HDMI-to-MIPI board, rests on a text outline that Youritech's own dimension drawing (107.98x163.8 mm) and FPC photos contradict. The FPC differs from Wisecoco's panel and the backlight uses separate wires. Its specs conflict across Youritech's own two pages (-20~70 vs -10~60 C, a-Si vs LTPS, 1.97 mm thickness against a 4.05 mm, 1350-nit sibling of the same outline). The 1500 nits is a vendor table and banner value only, with no datasheet. There is no price or availability, and nothing sold in Ukraine. The 1200x1920 resolution itself would fit the Q6A, which is why the receiver could cope with it given a known bridge. If Youritech is pursued at all, ask instead about ET070WU01-HLT (7 in 1200x1920, 2000 nits typ, in-cell touch, listed on the Youritech site). It still needs a bridge and a USB-HID touch path, so it would need its own check.
- **Sources:**
  - https://www.youritech.com/products/oem-odm-high-brightness-1500-nits-mipi-lcd-display-screen-for-outdoor-7-inch-tft-ips-lcd-display-1200x1920-lcd-module.html
  - https://www.youritech.com/uploads/2021/08/ET070WU07-O_01.jpg
  - https://www.youritech.com/uploads/2021/08/ET070WU07-O_02.jpg
  - https://www.youritech.com/uploads/2021/08/ET070WU07-O-7.0-inch-1200x1920-IPS-LCD-Display-MIPI-interface-3.jpg
  - https://www.youritech.com/products/7-inch-high-brightness-display-1500nits-1200x1920-mipi-tft-lcd-display.html
  - https://www.youritech.com/uploads/2020/03/ET070WU07-O_01.jpg
  - https://www.youritech.com/products/7-inch-high-brightness-display-1500nits-ips-1200x1920-mipi-tft-lcd-display.html
  - https://www.youritech.com/products/7-inch-lcd-display-1200x1920-high-resolution-lcd-panel-40-pins-mipi-16-7m-tft-lcd-module.html
  - https://www.youritech.com/products/7-inch-high-brightness-display-1300nits-ips-1200x1920-mipi-tft-lcd-display.html
  - https://www.youritech.com/products/7-inch-tft-lcd-display-1200x1920-high-brightness-2000nits-mipi-lcd-display-with-in-cell-touch.html
  - https://www.wisecocodisplay.com/product/7-inch-tft-lcd-module-mipi-40-pin-1920x1200-ips-lcd-display/
  - https://www.wisecocodisplay.com/wp-content/uploads/2026/05/7-inch-1920-1200-lcd-2-2.webp
  - https://prom.ua/ua/search?search_term=ET070WU07

## dispmkt:decide (run `wf_a429c611-ea2`)

- **Verdict:** The Wisecoco 7in 1920x1080 2000+ nit HDMI kit stays the main pick, but buy it only after the seller confirms two things in writing: the touch reaches the host as USB HID (with VID:PID), and the cover glass is optically bonded. If the seller cannot confirm both, buy the 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000 instead: 1000 nits, optical bonding stated in the datasheet, USB-C touch, 12 V input, in stock in Ukraine at 9,520 UAH. I found no buyable plug-and-play kit above 1920x1080 at 1000 nits or more in 5.5-8in. The closest is a bring-up project around the bare Midas MDT0700F1IHHC-MIPI (1200x1920, up to 2500 nits): EUR 324.37 ex VAT at Farnell, 12-week lead time, plus a bridge board, an LED driver and a touch bridge. At 30-35 cm, going above FHD gains almost nothing visible (7in FHD is already 315 PPI, against an acuity limit of 249-291 PPI). It costs money, time, about 1-3 W and Q6A mode risk. By my calculation, optical bonding, an AR film and a hood improve sun contrast more than another 1000 nits does.
- **Main pick:**
  - **Name:** Wisecoco 7in 1920x1080 LTPS IPS sunlight-readable panel with HDMI-in board and capacitive touch (the description table's active area of 154.368x86.832 mm makes it 6.97in diagonal, my calculation)
  - **Resolution:** 1920x1080, landscape by default per the product page; 316 PPI at 6.97in (calc)
  - **Brightness:** '2000+ cd/m2 (Typ.)' in the spec table; '2500Nits' in the title only; no datasheet or measurement. A Youritech part, ET070FH01-HT, is listed at 2000 cd/m2 typ with in-cell touch, the same 164.2x98 mm outline and 85/85/85/85 viewing angles. It is very likely the same glass, which is an inference.
  - **Price:** $132 (was $135), Add to cart, 0 reviews, re-read on wisecocodisplay.com 18 Oct 2026. The page lists no variants or package contents and says nothing on shipping. Below Ukraine's EUR 150 duty-free threshold if shipped alone.
  - **Why:** - **Brightness:** the brightest option with HDMI, capacitive touch and a cart price. If it is bonded, 2000 nits gives about 6.2:1 at 100 klx with an AR film and about 26:1 under a hood (calc). A bonded 1000-nit module gives 3.6:1 and 13.9:1.
  - **Q6A safety:** 1920 px wide splits as 2x960, so it never hits the sc7280 2400-px or UBWC split limits. It needs no virtual planes on the held 6.18.2 kernel.
  - **RF:** the board's EDID can be rewritten to a harmonic-clean 128.70 MHz 1080p52 mode.
  - **Touch evidence:** the in-cell touch is I2C at the panel. A different Wisecoco 7in kit enumerated as WCH CH57x USB HID (1a86:e5e3) under hid-multitouch (Pi forum t=368455), so a USB bridge on this board is plausible but unproven.
  - **Not chosen:** no new 2026 candidate beats it on verified data. The SURENOO AliExpress '2000nit' module and the Youritech 1200x1920 parts were refuted or remain quote-only.
  - **Possible second source (unverified lead):** VSDISPLAY lists a 6.97in 1080x1920 2000-nit on-cell panel with HD board at about GBP 119 on eBay.de (seen only as a snippet). It is the same 6.97in size.
  - **Fallback if any condition fails:** the 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000.
  - **Sources:**
    - https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
    - https://forums.raspberrypi.com/viewtopic.php?t=368455
    - https://www.youritech.com/products/7-inch-tft-lcd-display-1920x1080-mipi-2000nits-high-brightness-lcd-display-with-in-cell-touch-for-healthcare-medical-display-solution.html
    - https://www.youritech.com/products/7-inch-tft-lcd-display-1920x1080-high-brightness-4500nits-mipi-lcd-display-with-in-cell-touch-for-ev-charger.html
    - https://www.ebay.de/itm/256679793470
    - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_0.pdf
  - **Conditions before buying:**
    - Written confirmation of USB-HID touch from the HDMI board: controller IC, number of touch points and lsusb VID:PID. If it is bare I2C only, budget an I2C-to-USB-HID bridge or plan for the header-I2C goodix/edt-ft5x06 fallback.
    - Is the cover glass fully laminated (OCA/OCR) or air-gapped? Is it AR- or AG-treated? An air-gapped 2000-nit panel (1.5:1 at 100 klx, calc) is worse than the bonded 1000-nit 4D (1.7:1).
    - An EDID hex dump: preferred mode, landscape or portrait, porches. VFP+VSW+VBP must be at least 24 lines. Does the board accept an edited EDID at 1080p52 (128.70 MHz)?
    - Board input voltage and current at full brightness (12 V input preferred), backlight driver IC, dimming method (keys, PWM pad or DDC/CI) and PWM frequency.
    - Exactly what the $132 includes (touch panel, FPC, HDMI and USB cables), the panel part number, typical and minimum nits, polariser transmission axis, and the LC clearing point.
    - DHL/FedEx cost to Ukraine and an invoice under EUR 150; pay by PayPal or card for buyer protection.
- **Above fhd tier:**
  - **Name:** No plug-and-play option is buyable. Closest: Midas MDT0700F1IHHC-MIPI 7.02in bare panel, driven through a vendor-flashed HDMI-to-4-lane-MIPI bridge (LT6911C-class), an external constant-current LED driver and an I2C-to-USB-HID touch bridge. Alternative: a quote-only Youritech ET070WU01-HLT (2000 nits, in-cell) or ET070WU15-TT (1500 nits, CTP), only if Youritech supplies a tested HDMI board with USB-HID touch.
  - **Resolution:** 1200x1920, portrait-native, 322.5 PPI (calc). The 1200 px width stays under the 2400-px DPU limit, so it needs no virtual planes, but the compositor must rotate it.
  - **Brightness:** Datasheet: 1000/1500/2000/2500 cd/m2 at 200/300/400/500 mA, Vf 16 V typ (19.2 V max). The 2500 point is footnoted 'stable at room temperature, open air', so plan for 2000 nits (400 mA, about 6.4 W of LED power). AR cover lens; in-cell FT7250 touch.
  - **Price:** EUR 324.37 ex VAT for 1 unit (EUR 302.74 at 5+) at ie.farnell.com: available to order, 12-week standard lead time, not in stock (Oct 2026 search result). Add a bridge board (about $30-60, estimate), an LED driver and a touch bridge (about EUR 20-60, estimate), and Ukrainian duty and VAT on the amount above EUR 150, about EUR 56 (calc). Landed total about EUR 420-500 plus weeks of bring-up.
  - **Why:** - It is the only above-FHD panel of 1000 nits or more with a real datasheet: current-to-luminance table, AR cover lens, in-cell touch with no touch-layer air gap, -20 to 70 C.
  - Everything else above FHD is ruled out:
    - **Youritech:** brightness exists only on vendor web pages, quote only, catalog part numbers reused, no HDMI board for these models.
    - **VIEWE 8in transflective:** 369 nits transmissive, out of stock, board does not fit.
    - **Wisecoco 8.4in 1600x2560:** dual-port 8-lane MIPI, -10 to 50 C, no touch.
    - **Field and drone monitors at 1920x1200:** touch works only their own menus, and the LUT7 accepts broadcast formats only, so it shows scaled 1080p.
    - **Consumer handheld and tablet panels:** 287-706 nits measured.
  - **Blockers:** no porch timings (the datasheet says 'Refer to Focal Tech FT7250'). The JDI-class native vertical blanking may be only 14 lines, against the 24 the Q6A needs. TDDI touch scanning is tied to display timing. No community build exists.
  - **Verdict:** a lab project, not a purchase for this handheld.
  - **Sources:**
    - https://www.farnell.com/datasheets/3984938.pdf
    - https://ie.farnell.com/midas-displays/mdt0700f1ihhc-mipi/lcd-tft-display-7-1200x1920p-mipi/dp/4248109
    - https://www.youritech.com/products/7-inch-tft-lcd-display-1200x1920-high-brightness-2000nits-mipi-lcd-display-with-in-cell-touch.html
    - https://www.youritech.com/products/7-02-inch-tft-lcd-display-1200x1920-mipi-high-brightness-1500nits-lcd-module.html
    - https://viewedisplay.com/download/73/smart-display-datasheet/11743/uedx6911-hdmi-driver-board-spec-v2-0.pdf
    - https://raw.githubusercontent.com/torvalds/linux/master/drivers/gpu/drm/panel/panel-himax-hx8279.c
  - **Conditions before buying:**
    - Get the FT7250 video-mode timing table from Midas or Farnell: pclk, H and V porches, minimum and maximum refresh, and maximum VFP. Confirm that 24 or more lines of vertical blanking and 49-60 Hz work, and that touch still works at those timings.
    - A bridge vendor must commit to flashing LT6911C-class firmware for this panel and provide an EDID of 1340x1946 at 156.458 MHz (26 lines) or 1340x1956 at 128.5 MHz (36 lines).
    - Pass the gate test: prove an LED driver for 400 mA at up to 19.2 V from the 12 V rail (cheap LT6911 boards are rated only about 1.3 W total) and an I2C(1.8 V)-to-USB-HID bridge before ordering.
    - Accept a 12-week lead time and no community precedent. Keep the Wisecoco or 4D as the working screen in the meantime.
- **Budget pick:**
  - **Name:** Waveshare 5DP-CAPLCD-B (5in 1024x600 IPS, optically bonded toughened glass, HDMI with 5-point USB capacitive touch). If about 1000 nits is a hard floor, the cheapest verified step up is the Newhaven NHD-7.0-HDMI-HR-RSXP-CTU (7in 1024x600, 940 nits, USB-HID touch).
  - **Resolution:** 1024x600 (237 PPI at 5in; the Newhaven is 169.5 PPI at 7in)
  - **Brightness:** 800 cd/m2 (Waveshare spec). Newhaven: 940 nits (manufacturer page and datasheet). Neither is independently measured.
  - **Price:** $46.99-54.99 at the Waveshare store (variant price not shown). Newhaven: $120.20, shown as 'IN STOCK' but with a low-stock notice (18 Oct 2026).
  - **Why:** - **Waveshare:** the cheapest option with known driver-free USB-HID touch on Linux and optical bonding (-B variant only). Bonded plain glass gives about 1.6:1 at 100 klx, about 3.1:1 with an AR film and about 11:1 in a hood (calc), so it is usable in sun only with the hood. Draw is 4.2 W and it needs at least 850 mA. The Q6A needs video=HDMI-A-1:1024x600@60 (Radxa FAQ case).
  - **Newhaven:**
    - Datasheet-stated 'PCAP (USB-HID)' with an FT5426 controller and a TI TFP401A receiver with no scaler. Its EDID has 35 lines of vertical blanking, which meets the 24-line rule.
    - Optical bonding is not stated.
    - The stock 62.00 MHz clock puts its 12th harmonic at 744.0 MHz (QO-100 IF) and its 7th at 434.0 MHz (calc), so override the EDID to 52.00 MHz at 1344x645 (60 Hz).
    - 5 V supply at 6-7.5 W.
  - **Sources:**
    - https://www.waveshare.com/5dp-caplcd.htm
    - https://www.waveshare.com/wiki/5DP-CAPLCD
    - https://www.newhavendisplay.com/nhd70hdmihrrsxpctu-p-9649.html
    - https://newhavendisplay.com/content/specs/NHD-7.0-HDMI-HR-RSXP-CTU.pdf
  - **Conditions before buying:**
    - Order the -B variant specifically; -H is air-bonded and -G is resistive.
    - Give it its own 5 V rail of at least 1 A, and use a 25-35 mm matte-black hood.
    - Newhaven: ask whether the cover glass is optically bonded or air-gapped, and ask the international shipping cost (or route through a US forwarder such as Nova Poshta Global or Meest).
- **Ranked candidates:**
  1.
    - **Rank:** 1
    - **Name:** Wisecoco 7in (6.97in) 1920x1080 LTPS 2000+ nit kit with HDMI-in board and capacitive touch
    - **Resolution:** 1920x1080 landscape
    - **Nits:** 2000+ typ (spec table); 2500 in the title; unmeasured
    - **Touch to host:** Capacitive (in-cell likely), listed 'Interface Type: I2C'. USB HID through the board is unconfirmed (another Wisecoco 7in kit shows CH57x 1a86:e5e3).
    - **Price:** $132 (wisecocodisplay.com, 18 Oct 2026)
    - **Status:** MAIN PICK, conditional on written confirmation of USB-HID touch and bonding
  2.
    - **Rank:** 2
    - **Name:** 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000
    - **Resolution:** 1280x800 (panel drawing shows 800x1280; OSD board)
    - **Nits:** 1000 typ (datasheet R1.0, adjustable via OSD); 800:1
    - **Touch to host:** Capacitive (Goodix GT928 per the drawing) over the USB-C 'Power and Touch Interface'. USB class not stated; HID likely.
    - **Price:** 9,520 UAH (about $229), neostore.in.ua via prom.ua, in stock, 12-month warranty
    - **Status:** VERIFIED FALLBACK. Datasheet: 'Optical Bonded to LCD'; no AR as standard; 12 V barrel at 540 mA (6.5 W); -20 to 70 C
  3.
    - **Rank:** 3
    - **Name:** Midas MDT0700F1IHHC-MIPI with a vendor-flashed HDMI-to-MIPI bridge, LED driver and touch bridge
    - **Resolution:** 1200x1920 portrait
    - **Nits:** 1000-2500 by drive current (datasheet); plan 2000
    - **Touch to host:** In-cell FT7250 over I2C at 1.8 V; needs an I2C-to-USB-HID bridge
    - **Price:** EUR 324.37 ex VAT (Farnell IE, 12 weeks, not in stock) plus electronics
    - **Status:** ABOVE-FHD PROJECT ONLY: no timings published, no community build
  4.
    - **Rank:** 4
    - **Name:** 4D Systems 4DHDMI-80-1280-800-CT-EAR-1000
    - **Resolution:** 1280x800 (188.7 PPI)
    - **Nits:** 1000 typ (datasheet)
    - **Touch to host:** GT928 over USB-C (class not stated)
    - **Price:** 10,060 UAH (about $242), prom.ua, in stock
    - **Status:** Verified alternative: larger, lower PPI, 12 V at 580 mA (about 7 W), bonded
  5.
    - **Rank:** 5
    - **Name:** Xenarc 702GSH
    - **Resolution:** 1024x600 with scaler
    - **Nits:** 1000 (manufacturer)
    - **Touch to host:** USB PCAP multitouch
    - **Price:** $429, XenarcDirect, in stock
    - **Status:** Rugged fallback: bonded with AR+AF, 10-35 V direct from the 4S pack, under 10 W, 0.70 kg, low resolution
  6.
    - **Rank:** 6
    - **Name:** 4D Systems 4DHDMI-70-1024-600-CT-EAR-1000
    - **Resolution:** 1024x600
    - **Nits:** 1000 typ (datasheet)
    - **Touch to host:** GT1151QM over USB-C (class not stated)
    - **Price:** 8,140 UAH (about $196), neostore.in.ua, in stock
    - **Status:** Best nits per watt (5 V at 790 mA, about 4 W), bonded, low resolution, push-button dimming
  7.
    - **Rank:** 7
    - **Name:** Newhaven NHD-7.0-HDMI-HR-RSXP-CTU
    - **Resolution:** 1024x600, no scaler (TFP401A)
    - **Nits:** 940 (manufacturer)
    - **Touch to host:** USB-HID PCAP, FT5426 (datasheet)
    - **Price:** $120.20, low stock
    - **Status:** Step-up budget option. Bonding unstated; 5 V at 6-7.5 W; stock 62 MHz EDID is RF-bad, so override to 52 MHz
  8.
    - **Rank:** 8
    - **Name:** Youritech ET070WU01-HLT (2000) / ET070WU10-TT and ET070WU15-TT (1500)
    - **Resolution:** 1200x1920
    - **Nits:** 2000 / 1500 typ (vendor web pages only; sister parts list 1300/1350/1600)
    - **Touch to host:** In-cell TDDI or optional CTP over I2C; no USB-HID path offered
    - **Price:** Quote only
    - **Status:** Unverified RFQ backup. Revive only with a datasheet, a concrete HDMI board, an EDID and a VID:PID
  9.
    - **Rank:** 9
    - **Name:** VIEWE UEED080FH-RB39-A003 transflective with UEDX6911 board
    - **Resolution:** 1200x1920 (8in, 283 PPI)
    - **Nits:** 369 typ transmissive (datasheet); 7% reflectance, 15:1 reflective contrast
    - **Touch to host:** Board offers 5-point USB HID, but its fit with this 45-pin panel is not listed
    - **Price:** $92.99 bundle; out of stock (viewedisplay.com, 18 Oct 2026)
    - **Status:** Sun-specialist curiosity. Pale colours (15-20% NTSC), 300:1 indoors, the board's 1.3 W rating cannot drive the 2.9 W backlight; rejected
  10.
    - **Rank:** 10
    - **Name:** Waveshare 5DP-CAPLCD-B
    - **Resolution:** 1024x600 (5in)
    - **Nits:** 800 (vendor)
    - **Touch to host:** USB HID, driver-free
    - **Price:** $46.99-54.99
    - **Status:** BUDGET PICK, below the 1000-nit target
  11.
    - **Rank:** 11
    - **Name:** Youritech ET070FH01-HTT
    - **Resolution:** 1920x1080
    - **Nits:** 4500 typ (vendor page)
    - **Touch to host:** In-cell over I2C, no HDMI board offered
    - **Price:** Quote only
    - **Status:** Lead only: same outline as the Wisecoco glass, possibly a brighter twin; would need about 10 W+ of backlight
  12.
    - **Rank:** 12
    - **Name:** SURENOO SUR12001080H070K '2000nit Incell 7in 1200*1080 FHD HDMI' (AliExpress 1005006176909405)
    - **Resolution:** Unknown: title and model number both say 1200*1080
    - **Nits:** 2000 (title only)
    - **Touch to host:** Unknown
    - **Price:** $106.09 (old snippet; page captcha-walled)
    - **Status:** REJECTED as unverifiable; not Wisecoco
  13.
    - **Rank:** 13
    - **Name:** Wisecoco 8.4in 1600x2560 bare panel
    - **Resolution:** 1600x2560
    - **Nits:** 2000 typ (listing)
    - **Touch to host:** None listed
    - **Price:** $158 panel only
    - **Status:** REJECTED: dual-port 8-lane MIPI with no bridge, -10 to 50 C
  14.
    - **Rank:** 14
    - **Name:** FEELWORLD P7 / LUT7, DJI High-Bright Remote Monitor (1920x1200, 2000-2200 nits)
    - **Resolution:** 1920x1200
    - **Nits:** 2000-2200 (listings)
    - **Touch to host:** None (menu-only touch or no touch)
    - **Price:** $380 to EUR 1,459
    - **Status:** REJECTED: no host touch; LUT7 HDMI input is broadcast formats only
- **What above fhd costs us:** All figures are my calculations unless stated. Script: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final_calc/fc.py
  
  COSTS:
  1) Brightness.
  - Every buyable above-FHD 5.5-9in kit is 287-706 nits: Waveshare 9in about 350; Wisecoco 2.5K 500; Sharp 7.9in QXGA kits 460 per listing; Legion Go 413 and AYANEO KUN 678 measured by Notebookcheck.
  - At 100 klx with a bonded AR-film front (1.2% reflectance) that gives about 2.3-3.2:1, against 6.2:1 at 2000 nits.
  - The bright above-FHD glass exists only as bare MIPI panels.
  2) Power.
  - A 2000-nit 1200x1920 build is about 8-10 W: 6.4 W of LEDs per the Midas datasheet, plus about 1 W for the bridge, plus logic.
  - That compares with about 6-8 W estimated for the Wisecoco FHD kit.
  - Runtime with 15 W for the rest of the system and 61 Wh usable: about 2.5 h against about 2.8 h. An 8.4in 2.5K 2000-nit panel at about 10 W gives about 2.4 h.
  3) GPU fill.
  - 1200x1920 is 1.11x the FHD pixel count; 1600x2560 is 1.98x.
  - Portrait-native panels also need a full-screen rotation pass in the compositor.
  4) Q6A mode risk.
  - No above-1080p display has been reported stable on Q6A HDMI.
  - Portrait panels 1200 or 1600 px wide avoid the 2400-px DPU split. A landscape 2560-wide mode needs msm.dpu_use_virtual_planes=1 on the held 6.18.2.
  - Bridge EDIDs often have fewer than the required 24 lines of vertical blanking (JDI-class 1200x1920 native is 14), so a custom EDID is needed. The bridge vendor must flash the firmware.
  - 1600x2560 RB at 276.9 MHz uses 77% of the 2-lane HBR2 link; 348.5 MHz CVT is out.
  - RF: CVT-RB 1200x1920 at 161.0 MHz hits 2254 MHz and RBv2 at 151.68 MHz hits 2275 MHz. The HX8279-style 156.458 MHz timing is clean in the six RX bands, but its 10th harmonic lands at 1564.6 MHz in the GNSS band.
  5) Money and time.
  - Midas EUR 324.37 ex VAT, plus about EUR 50-120 of bridge, LED and touch electronics (estimate), plus about EUR 56 UA duty and VAT, plus a 12-week lead time and unbounded bring-up.
  - Compared with $132 under the EUR 150 threshold and a plug-in HDMI kit.
  
  GAINS:
  - The 1-arcminute acuity limit is 291 PPI at 30 cm and 249 PPI at 35 cm.
  - 7in FHD is already 315 PPI. 7.02in 1200x1920 is 322.5 PPI, only 2.5% denser linearly and invisible. 8in 1200x1920 is 283 PPI, actually less dense. 8.4in 2560x1600 is 359 PPI, beyond acuity.
  - The only real gain is 11% more pixels on the short axis (1200 vs 1080) for UI space, or a physically larger 8-8.4in face.
  
  NET: not worth it for a sunlit handheld. Spend the effort on bonding, AR, a hood and auto-dimming.
- **Refuted claims:**
  1.
    - **Claim:** The AliExpress '2000nit Incell 7in FHD HDMI' module ($106.09) is the same glass and board as the Wisecoco pick, and is 1920x1080.
    - **Why:** - The brand is SURENOO, model SUR12001080H070K.
  - Both the title and the model number encode '1200*1080', so the resolution is unknown.
  - No datasheet, touch path or price is readable; every page is captcha-walled.
  2.
    - **Claim:** Youritech ET070WU07-O (1500 nits) uses the same panel as Wisecoco's $69 500-nit kit and is rated -20 to 70 C.
    - **Why:** - Youritech's own dimension drawing gives 107.98x163.8 mm.
  - Its FPC and separate backlight wires differ from the Wisecoco photo.
  - Its second page and catalogue line say -10 to 60 C.
  - It has no touch, so it fails a hard requirement.
  3.
    - **Claim:** Youritech ET070WU01-HLT is a buyable 2000-nit above-FHD candidate.
    - **Why:** - 2000 cd/m2 appears only on the vendor web page: no datasheet, quote only.
  - No HDMI board is offered for it.
  - In-cell TDDI touch is I2C/SPI with no USB-HID path.
  - The catalogue reuses one part number (ET070WU01-TT) for 350-nit and 1300-nit products.
  4.
    - **Claim:** ET070WU15-TT has a 'reference line ... CTP' entry, and the second Youritech URL supports its touch claim.
    - **Why:** - The reference-table row for 7in 1200x1920 HX8279 says 1600 nits and no CTP.
  - The second URL is ET070WU18-OT ('Touch: no', -10 to 60 C).
  5.
    - **Claim:** 1200x1920@60 at about 150 MHz hits 748.8/2246 MHz, and 51.3-51.8 Hz is clean.
    - **Why:** - It depends on the totals.
  - The HX8279-style 1340x1946 timing at 156.458 MHz is clean in all six RX bands.
  - With those totals, 51.5 Hz (134.3 MHz) hits 2283 MHz.
  - CVT-RB v1 (161.0 MHz) hits 2254 MHz; RBv2 (151.68 MHz) hits 2275.2 MHz.
  - Calculations.
  6.
    - **Claim:** A cheap LT6911 board (VIEWE UEDX6911) can drive a 1500-2500 nit 7-8in panel.
    - **Why:** - The UEDX6911 datasheet rates the whole board at 5 V, 150-260 mA (about 1.3 W).
  - A 2000-nit 7in backlight is about 6.4 W (Midas datasheet), so an external LED driver is mandatory.
  - The board datasheet does not list the 45-pin UEED080FH panel.
  7.
    - **Claim:** A 2000-nit panel is always more sun-readable than a 1000-nit one.
    - **Why:** - At 100 klx an air-gapped, uncoated 2000-nit panel is about 1.5:1, while a bonded 1000-nit panel is about 1.7:1 (calc, from Planar reflectance values).
  - Bonding and AR are worth more than doubling the nits.
  8.
    - **Claim:** Wisecoco touch is USB HID, and the panel is 2500 nits.
    - **Why:** - The page lists 'Interface Type: I2C' and '2000+ cd/m2 (Typ.)'; 2500 appears only in the title.
  - The CH57x USB-HID evidence comes from a different Wisecoco 7in kit.
  - The page has no package contents, power, bonding or chip information (re-read 18 Oct 2026).
  9.
    - **Claim:** 4D Systems 4DHDMI modules come with an AR/AG front.
    - **Why:** The datasheet says 'As a standard option, the displays do not have any Cover Glass Treatments'. AR, AG and AF are a custom order. Bonding is standard only on the 1024x600 and 1280x800 models; the smaller ones are air-bonded.
  10.
    - **Claim:** Newhaven 'Sunlight Readable' implies an optically bonded, RF-safe module.
    - **Why:** - The page lists only 'USB-HID Capacitive + Cover Glass'; bonding is not stated.
  - Its stock EDID clock of 62.00 MHz puts the 12th harmonic at 744.0 MHz (QO-100 IF) and the 7th at 434.0 MHz (calc).
  11.
    - **Claim:** 1920x1200 field or drone monitors (FEELWORLD P7/LUT7, DJI High-Bright) are an above-FHD path.
    - **Why:** - Their touch controls only their own menus.
  - The LUT7 HDMI input accepts broadcast formats only, so it shows scaled 1080p.
  12.
    - **Claim:** Above-FHD kits will work on any recent kernel.
    - **Why:** - Mainline v7.3-rc has no Q6A display device tree, and 7.0.x breaks HDMI.
  - Only Radxa 6.18.2 (held) or patched community kernels drive HDMI.
  - On 6.18, landscape modes wider than 2400 px also need msm.dpu_use_virtual_planes=1.
- **Q6a settings:**
  - Kernel: stay on Radxa 6.18.2-x-qcom. Hold it with: sudo apt-mark hold linux-image-radxa-dragon-q6a linux-headers-radxa-dragon-q6a embloader (confirm the names with dpkg -l | grep -E 'linux-image|embloader'). Add the same names to Unattended-Upgrade::Package-Blacklist. Keep the old boot entry, a dd+zstd golden image and a USB-UART cable; measure the header voltage first.
  - Inspect the panel before choosing a mode: edid-decode /sys/class/drm/card1-HDMI-A-1/edid; cat /sys/class/drm/card1-HDMI-A-1/modes; modetest -M msm -c. The chosen mode needs VFP+VSW+VBP of at least 24 lines. If dmesg shows 'low vbp+vfp', shearing or underrun, edit the EDID.
  - Wisecoco bring-up: append video=HDMI-A-1:1920x1080@60 to /etc/kernel/cmdline, then sudo kernel-install add $(uname -r) /boot/vmlinuz-$(uname -r) and reboot. This is CEA 148.5 MHz, which hits 742.5 and 2227.5 MHz, so use it for bring-up only.
  - Wisecoco field mode, RF-clean (calc): Modeline "1920x1080_52" 128.700 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync. That is 45 lines of vertical blanking and 3.09 Gbps, 36% of 2-lane HBR2. Clean alternative: 135.760 1920 1968 2000 2080 1080 1083 1088 1111 (58.75 Hz, 31 lines). Avoid 1080p CVT-RB at 138.5 MHz: its fundamental sits 0.5 MHz above the 137-138 MHz band.
  - Apply the clean mode by EDID override:
  1. cp /sys/class/drm/card1-HDMI-A-1/edid edid.bin
  2. python3 -c "b=bytearray(open('edid.bin','rb').read());b[54:56]=(12870).to_bytes(2,'little');b[127]=(-sum(b[:127]))&255;open('wisecoco52.bin','wb').write(b)". This only gives 52 Hz if DTD#1 totals are 2200x1125. Otherwise choose a pixel clock in 127.85-129.35 or 135.4-135.95 MHz for the real totals.
  3. Check the result with edid-decode, then sudo cp wisecoco52.bin /lib/firmware/edid/.
  4. Add 'drm.edid_firmware=HDMI-A-1:edid/wisecoco52.bin video=HDMI-A-1:1920x1080@52' to /etc/kernel/cmdline.
  5. Add the file to the initramfs with an initramfs-tools hook, then run kernel-install add.
  - Portrait 1200x1920 bridge (above-FHD route): set the bridge EDID to Modeline 156.458 1200 1250 1274 1340 1920 1934 1936 1946 (60 Hz, 26 lines, 43% of the link; clean in the RX bands, but the 10th harmonic is at 1564.6 MHz in GNSS). RF-quiet option: 128.500 1200 1250 1274 1340 1920 1944 1946 1956 (49.0 Hz, 36 lines; panel and touch tolerance unknown). Rotate in GNOME Settings > Displays > Orientation, or under X11: xrandr --output HDMI-1 --rotate right plus xinput map-to-output <id> HDMI-1.
  - Virtual planes: not needed for any recommended mode, since all are 1920 px wide or less. Only for a landscape 2560-wide test on 6.18.2: append msm.dpu_use_virtual_planes=1, run kernel-install add, and check that cat /sys/module/msm/parameters/dpu_use_virtual_planes prints Y. Use 2560x1600 CVT-RB at 268.6 MHz (totals 2720x1646, 75% of the link); never the 348.5 MHz CVT mode.
  - 4D 1280x800: video=HDMI-A-1:1280x800@60 (CVT 83.77 MHz, 31 lines). Its only hits are weak high-order harmonics: the 19th at 1591.5 MHz (GNSS) and the 27th at 2261.6 MHz. Auto-dim by having an RP2040 pull the OSD button-board lines (10-pin 2.0 mm: Menu, Down, Up, Enter, Power) through open-drain GPIOs.
  - Newhaven 1024x600: replace the stock 62.00 MHz EDID with Modeline 52.000 1024 1184 1204 1344 600 612 622 645 (60.0 Hz, 45 lines). The TFP401A has no scaler, so the panel itself must accept this timing.
  - Touch: run only D+/D-/GND from the display board to a Q6A USB 2.0 port, and power the board's VBUS from its own 12 V or 5 V buck so it never back-feeds the Q6A. Check with lsusb, sudo libinput list-devices and sudo evtest. Map it in GNOME with: gsettings set org.gnome.desktop.peripherals.touchscreen:/org/gnome/desktop/peripherals/touchscreens/<vid>:<pid>/ output "['VEN','Product','Serial']".
  - SDR++/SatDump touch (GLFW has no Wayland touch support): launch them with Exec=env XDG_SESSION_TYPE=x11 sdrpp and Exec=env XDG_SESSION_TYPE=x11 satdump-ui so they run under XWayland.
  - DDC brightness test, expected to fail on cheap boards: sudo modprobe i2c-dev; sudo ddcutil detect --verbose; ddcutil --bus N setvcp 10 30. Otherwise use the RP2040 PWM or button route with a VEML7700 lux sensor and NTC derating.
- **Sunlight measures:**
  - Optical bonding first. The 100 klx model (calc) at 2000 nits: air gap 1.5:1, bonded plain glass 2.4:1, bonded plus a 1.2% AR film 6.2:1, factory bonded AR 9.9:1. At 1000 nits the same cases give 1.2, 1.7, 3.6 and 5.5:1. Reject an air-gapped front; check by holding a pen tip on the glass at a grazing angle, where a doubled reflection means an air gap.
  - Add an AR front: an AR screen film of about 0.7% reflectance (vendor claim class, e.g. TELESIN) or AR-coated cover glass. Do not use matte AG on a 315-PPI panel, because it sparkles and softens the image. Ask 4D or Wisecoco whether AR cover glass is available as a custom option.
  - Hood: 25-35 mm deep, matte-black interior, hinged so it folds down as a lid. Tilt the screen so it mirrors the hood interior or dark clothing, not the sky or a white shirt: a sunlit white shirt is about 25,000 cd/m2, which becomes about 1000 nits of glare at 4% reflectance (calc). In 20 klx shade the bonded 2000-nit panel reaches 8.1:1 with plain glass and 26.5:1 with AR film; the 4D reaches 4.6:1 and 13.9:1 (calc).
  - Polariser: ask the seller for the transmission-axis angle. Test with polarized sunglasses at 0, 45 and 90 degrees before fixing the panel orientation in the case. If the axis is wrong, use non-polarized glasses; a quarter-wave retarder film (Relec and Digiwise sell TFTs fitted with one) makes the output circular, but I found no tested DIY sheet.
  - Thermal:
  - Light-coloured ASA case, never PLA.
  - A fan pulls air through a 4-6 mm gap behind the backlight frame into the Q6A heatsink.
  - 1 mm aluminium plate, doubling as RF shield and heat spreader.
  - NTC on the frame: derate to 50% above 60 C and 20% above 68 C (panel rated -20 to 70 C).
  - IR-rejecting film only if it shows no rainbow effect against the LCD polariser.
  - Brightness discipline:
  - Auto-dim from a VEML7700 behind a diffuser facing the same way as the screen.
  - Run at 30-50% most of the time and full only in direct sun.
  - Never exceed the datasheet LED current; the Midas 2500-nit point is rated only at room temperature in open air.
  - Use DC/analog dimming or 20-25 kHz PWM-to-analog, not burst PWM, for RF.
  - Do not rely on transflective or e-paper: the VIEWE 8in transflective has 15-20% NTSC colour and 300:1 contrast indoors, and e-paper smears a scrolling waterfall.
- **Acceptance tests:**
  - Luminance: show full white in a dark room and press a lux meter flat on the glass (L is about E/pi). Pass: Wisecoco at least 5600 lx (about 1800 nits); 4D or Newhaven at least 2800 lx (about 900 nits). Expect about 25% error; return the unit if it fails.
  - Touch: lsusb shows the touch VID:PID (WCH boards use 1a86). dmesg shows hid-multitouch bound. evtest shows ABS_MT_SLOT with the advertised number of points and X/Y ranges matching the panel. Touch must keep working at the 52 Hz clean mode.
  - EDID: edid-decode shows the preferred mode and its orientation, with VFP+VSW+VBP of at least 24 (or the edited EDID is accepted). The board must show no flicker, shear or colour fault at 128.70 MHz.
  - Boot robustness on held 6.18.2: the correct mode on 20 cold boots, 20 reboots and 10 HDMI re-plugs. Log head -1 /sys/class/drm/card1-HDMI-A-1/modes from a boot service each time.
  - Power on the 12 V rail with a 1.5 A limit: Wisecoco 9 W or less at full white; 4D about 6.5 W or less (datasheet 540 mA). Record the current at minimum and at full brightness.
  - Back-feed: with the display powered and the Q6A off, the USB VBUS at the Q6A side must read 0 V.
  - Optics: the pen-tip test shows no doubled reflection (bonded), and the polarized-sunglasses test passes at the chosen mounting orientation.
  - Thermal: a 30-minute full-white soak, then a 45-minute noon test face-on to the sun with hood and fan. Pass: frame 60 C or less, glass 65 C or less, no darkening or retention, no case deformation.
  - RF A/B: rtl_power sweeps (130-150, 430-440, 735-755, 1685-1715 MHz) and LimeSDR averaging (2200-2300 MHz), first into a terminator, then on the antenna. Compare display off, minimum, full, black screen, white screen and each mode. Pass: 1-2 dB or less rise. Also check u-blox UBX-MON-RF and C/N0 change by 1 dB-Hz or less.
  - Application: SDR++ and SatDump launched with XDG_SESSION_TYPE=x11 tune by tap and drag. With the screen rotated, a touch in a corner lands in the same corner.
- **Ukraine purchase:** - **Bought locally:** the only module with 1000 nits or more, optical bonding and USB touch that is stocked in Ukraine is the 4D Systems range from neostore.in.ua on prom.ua (in stock, 12-month warranty, Nova Poshta, cash on delivery):
    - 7in 1280x800 1000-nit: 9,520 UAH
    - 8in 1280x800 1000-nit: 10,060 UAH
    - 7in 1024x600 1000-nit: 8,140 UAH
  
    prom.ua has no Wisecoco 7in FHD kit, no Lilliput 719, and nothing for ET070WU01 or ET070WU07. Its field monitors (Portkeys, SmallHD, FEELWORLD) have menu-only touch.
  - **Wisecoco:** order direct (wisecocodisplay.com, 'Add to cart' at $132) or from the Wisecoco AliExpress store. Ask for DHL or FedEx with a correct invoice under EUR 150.
  - **Customs (searches, Oct 2026):** Ukraine still applies the EUR 150 duty-free limit per international shipment. Above it, 10% duty and 20% VAT are charged; my understanding is that this applies to the amount over EUR 150, so verify on the order date. The Cabinet re-approved bills in Sept 2026 to charge VAT from EUR 0 (non-commercial up to EUR 45 exempt). Reports say not before July 2027, but the Rada has not passed them, so check before ordering.
  - **Midas:** Farnell export, EUR 324.37 ex VAT, 12 weeks. Expect about EUR 56 duty and VAT (calc) plus courier and broker fees; confirm Farnell ships to Ukraine at checkout.
  - **US items (Xenarc $429, Newhaven $120.20):** use a forwarder with a US warehouse such as Nova Poshta Global or Meest, or the vendor's own international shipping if quoted.
  - **Payment:** PayPal or card for buyer protection.
  - **Quality check:** get luminance and touch photos or video from the seller before shipping, and run the acceptance tests within the dispute window. AliExpress generally ships to Ukraine, but the SURENOO item could not be checked.
- **Open questions:**
  - Wisecoco: what is the panel part number? Is it the in-cell ET070FH01-HT-class glass (6.97in, active area 154.368x86.832 mm)? Is the 4500-nit backlight variant available, and can the board's LED driver supply it?
  - Wisecoco: which touch controller, and does the HDMI board output USB HID? Please give the lsusb VID:PID and the number of touch points. Is a separate USB cable included in the $132?
  - Wisecoco: please send the EDID hex: preferred mode, landscape or portrait, porches and vertical blanking. Does the board accept an edited EDID at 1080p52 (128.70 MHz), and which bridge chip and DSI lane rate does it use?
  - Wisecoco: board input voltage range and current at full brightness? Backlight driver IC, PWM frequency, and how brightness is set (keys, PWM pad or DDC/CI)?
  - Wisecoco: is the cover glass fully laminated (OCA/OCR) or air-gapped? AR or AG treatment, cover thickness, polariser transmission axis, and the LC clearing point or high-Tni rating?
  - Wisecoco: DHL or FedEx cost to Ukraine, invoice value, DDP option, and warranty or DOA policy?
  - 4D Systems: does the USB-C touch enumerate as standard HID multitouch (VID:PID)? What is the EDID native mode, and does the board scale? Can you supply DDC/CI brightness firmware, the OSD button board, and AR cover glass on a 1-off order?
  - Midas/Farnell: please send the FT7250 video timing table and the minimum and maximum frame rate. Does in-cell touch need a host firmware download? Do you ship to Ukraine, and what is the current stock date?
  - Youritech: can you supply ET070WU01-HLT or ET070WU15-TT with a tested HDMI board giving USB-HID touch, an EDID with at least 24 lines of vertical blanking, a datasheet with luminance test report, and a price for 1-2 samples with DDP to Ukraine?
  - Newhaven: is the cover glass optically bonded? Do you ship internationally, and is the part being retired?
  - VIEWE: does UEDX6911 firmware support the 45-pin UEED080FH panel and its touch IC, and what LED drive current does the board provide?
  - VSDISPLAY (eBay.de 256679793470): what is the board's input (HDMI?), how does touch reach the host, which panel part is it, and is it the same 6.97in glass as Wisecoco?
- **Confidence:** medium

