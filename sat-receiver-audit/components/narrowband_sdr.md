# Narrowband sdr: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_eb446444-464`_

- **Component:** Second / narrowband SDR (currently RTL-SDR Blog V4 on a Q6A USB 2.0 port)
- **Current pick assessment:** KEEP a second SDR, but you can no longer buy the V4. Replace it with the RTL-SDR Blog V4L (Lite).
  
  Why the second SDR is still needed even with the LimeSDR Micro:
  (1) Both LMS7002M RX channels run off one RX PLL, so RX1 and RX2 must sit inside the same ≤61.44 MHz window. The Lime cannot take Meteor-M LRPT at 137.9 MHz and HRPT at 1700 MHz together, even though the same satellite sends both on the same pass. It also cannot do 137 MHz plus 435 MHz at once. Source: myriadrf forum.
  (2) The Lime's delivery and price have slipped. Crowd Supply now lists the M.2 2280 Basic at $249 (GNSS version $299), and new orders ship on Dec 15, 2026. That is not the $199 / Sept 30 in the BOM. Until then the small SDR is the only working radio for building the software stack.
  (3) HF. The Lime starts at 30 MHz and its LimeFEA HF Micro costs $199. The V4L's 28.8 MHz-LO upconverter covers 0.5-28.8 MHz for the price of the dongle.
  (4) Backup and fault isolation.
  (5) Low power. Datasheet draw is 250-270 mA at 5 V (~1.3 W). The LimeSDR Micro's power draw is not published.
  
  The V4 itself is end-of-line. The R828D tuner stockpile is gone and the last chips were faulty. RTL-SDR Blog says most "V4" listings on AliExpress, eBay and similar sites are fakes: a copied enclosure with a V3-clone circuit inside. So buying a "V4" in October 2026 carries a high risk of getting a counterfeit.
  
  The official successor is the V4L ($37.95):
  - R828S tuner, 500 kHz-1.766 GHz, 2.56 MS/s stable (3.2 with drops)
  - Same HF upconverter as the V4, 1 ppm TCXO, 4.5 V / 180 mA bias tee, aluminium case
  - About 2-4 dB better minimum discernible signal (MDS) than the V4 from roughly 100-500 MHz (~-141 vs ~-137 dBm, read from the datasheet chart)
  - Worse strong-signal immunity: no triplexer and no FM/AM notch, so its two-tone results equal the V3's. With a 95 MHz blocker, the V4 tolerates +8 dBm at 300-1400 MHz while the V4L/V3 drop to -20 to -40 dBm.
  - Needs a 2026 driver: Osmocom commit 0204c9c or the rtlsdrblog fork. With old drivers you get no signal.
  
  Your BOM already has an FM bandstop filter, which covers most of the V4L's filtering loss.
- **Alternatives:**
  1.
    - **Name:** RTL-SDR Blog V4L (Lite), dongle only
    - **Key specs:** RTL2832U 8-bit + R828S. 500 kHz-1.766 GHz. 2.56 MS/s stable (3.2 MS/s with drops). HF by upconverter (28.8 MHz LO). 1 ppm TCXO. 4.5 V / 180 mA software bias tee. Diplexer front end with no notch filter. 250-270 mA typical. Aluminium case with thermal pad. MDS about -141 dBm at 100-500 MHz (datasheet chart).
    - **Price:** $37.95 at the official store and eBay; about $34.20 on the official AliExpress listing. sdrstore.eu asks €83.44.
    - **Pros:** Direct successor to the V4, cheapest real option. Built-in HF upconverter. Slightly better VHF/UHF sensitivity than the V4. Lowest power. The bias tee can power a VHF/UHF LNA. Native support in SatDump, SDR++ and GNU Radio once the driver is updated. RTL-SDR Blog's store page says Ukraine is served via its AliExpress store.
    - **Cons:** 8-bit ADC and about 2.4 MHz bandwidth. Poorer overload behaviour than the V4 near FM, DAB or TV transmitters, so it needs the FM bandstop and careful LNA gain. Needs librtlsdr built from 2026 source; Ubuntu 24.04 packages predate V4L support. Also a limited edition: the R828S is out of production and the stockpile is expected to last about one year. Above about 1 GHz the MDS rises (~-130 dBm near 1.7 GHz), so it is not the tool for L-band HRPT.
    - **Sources:**
      - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-v4l-lite-r828s-rtl2832u-1ppm-tcxo-sma-software-defined-radio-dongle-only/
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://github.com/osmocom/rtl-sdr/commit/0204c9cfb1c5ff7bd64f466ce5b8fe53b40a636a
      - https://www.rtl-sdr.com/V4L
    - **Availability:** In stock: 455 units listed on the official store; ships from the China warehouse. Amazon US stock is expected in 2-3 months. Official AliExpress item: https://www.aliexpress.com/item/1005005952682051.html
    - **Q6a compatibility:** Good. It needs about 5 MB/s at 2.4 MS/s, far below the ~30 MB/s Radxa measured on a Q6A USB 2.0 port. You must purge Ubuntu's librtlsdr0, build Osmocom master or the rtlsdrblog fork, blacklist dvb_usb_rtl28xxu, and rebuild SoapyRTLSDR, gr-osmosdr, SatDump and SDR++ against the new library.
  2.
    - **Name:** RTL-SDR Blog V4 (current pick)
    - **Key specs:** R828D, 500 kHz-1.766 GHz, triplexed input with notch filtering, HF upconverter, 1 ppm TCXO, 4.5 V bias tee, 250-270 mA.
    - **Price:** Older Western retail kit listings: SparkFun $84.95, Pi Hut £81.60. No longer sold in the official store.
    - **Pros:** Best strong-signal and FM/DAB rejection of the RTL family.
    - **Cons:** End-of-line with no further production possible. Most marketplace 'V4' listings are fakes, so counterfeit risk is very high. Slightly worse VHF/UHF MDS than the V4L.
    - **Sources:**
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4-end-of-line/
      - https://www.rtl-sdr.com/GENUINE
      - https://www.rtl-sdr.com/wp-content/uploads/2024/12/RTLSDR_V4_Datasheet_V_1_0.pdf
      - https://www.sparkfun.com/rtl-sdr-blog-v4-usb-dongle-with-dipole-antenna-kit.html
    - **Availability:** Only leftover reseller stock remains. Not recommended to hunt for one in October 2026.
    - **Q6a compatibility:** Works with the same driver stack as the V4L.
  3.
    - **Name:** RTL-SDR Blog V3 (R860)
    - **Key specs:** RTL2832U + R860 (the R820T2 die). 500 kHz-1.766 GHz. HF by direct sampling (Q-branch), so it shows aliasing and poor HF MDS (about -115 to -120 dBm). 1 ppm TCXO. 4.5 V bias tee. Available with USB-A or USB-C.
    - **Price:** $34.95-39.95 dongle only; $44.95-49.95 with the dipole kit (the same kit the project's 137 MHz V-dipole comes from)
    - **Pros:** In stable production with the most mature drivers: works with stock Ubuntu 24.04 packages. VHF/UHF performance close to the V4L. A USB-C version exists.
    - **Cons:** Weak HF. Same overload behaviour as the V4L. Many counterfeits exist.
    - **Sources:**
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4-end-of-line/
      - https://www.sdrstore.eu/rtl-sdr-v3-vs-v4-vs-v4-lite-budget-sdr/
    - **Availability:** In stock through the official Amazon, AliExpress and eBay stores.
    - **Q6a compatibility:** Plug-and-play on Ubuntu 24.04 arm64.
  4.
    - **Name:** Nooelec NESDR SMArt v5
    - **Key specs:** RTL2832U + R820T2/R860, 100 kHz-1.75 GHz, 3.2 MHz maximum bandwidth, 0.5 ppm TCXO, HF by direct sampling, aluminium case. The SMArt page does not mention a bias tee (that is the separate SMArTee model).
    - **Price:** $44.95 at nooelec.com (free worldwide shipping only above $100). Third-party listings run $74-88.
    - **Pros:** Good build quality, 0.5 ppm TCXO, low counterfeit risk when bought direct.
    - **Cons:** Costs more than the RTL-SDR Blog V3 or V4L with no RF advantage. HF only by direct sampling. No bias tee on this model.
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-receivers/nesdr-smart-sdr.html
    - **Availability:** Orderable from Nooelec (US). Shipping cost to Ukraine not verified.
    - **Q6a compatibility:** Plug-and-play with stock librtlsdr.
  5.
    - **Name:** Airspy Mini
    - **Key specs:** R820T2/R860 + 12-bit ADC at 20 MS/s (10.4 ENOB). IQ output at 10, 6 or 3 MS/s, with up to 6 MHz usable view. 24-1700 MHz. NF 3.5 dB from 42-1002 MHz. IIP3 +35 dBm (front end). 0.5 ppm clock. 4.5 V bias tee. 77x26x10 mm, 50 g.
    - **Price:** $99 list (iTead). It dropped to $79.20 in the Jun 27-Jul 4, 2026 20% sale; Airspy has held recurring Black Friday sales in past years.
    - **Pros:** Clearly better dynamic range and overload resistance than any 8-bit RTL. Its 10 MS/s window covers 137-146 MHz, so LRPT and ISS SSTV fit together. Open-source libairspy with ARM Linux support. Native SatDump plugin. Still dongle-sized.
    - **Cons:** 2.6x the price of the V4L. No HF without the $49 SpyVerter. Range ends at 1700 MHz, the edge for Meteor HRPT. At 10 MS/s it needs up to about 30-40 MB/s on USB 2.0, which is tight if the Q6A's USB 2.0 ports share one hub (unverified). Current draw not published.
    - **Sources:**
      - https://airspy.com/airspy-mini/
      - https://itead.cc/product/airspy-mini/
      - https://www.rtl-sdr.com/?p=66258
    - **Availability:** iTead ships from its EU warehouse in 3-6 business days (Europe) or from China in 15-35 days (other countries). Shipping to Ukraine is not explicitly confirmed.
    - **Q6a compatibility:** Good. libairspy and SoapyAirspy build on arm64. Use 6 MS/s or packed mode if the USB 2.0 ports share a hub.
  6.
    - **Name:** HydraSDR RFOne
    - **Key specs:** Airspy R2-class design: LPC4370 MCU, 12-bit ADC, R828D tuner, 24-1800 MHz, 10 MS/s (~9-10 MHz bandwidth). USB-C (still USB 2.0). Better shielding than the R2. Open-source firmware, host library and SoapyHydraSDR. Enclosure is oversized (room for 3 boards).
    - **Price:** $193.67 at DigiKey (511 in stock, 1-week lead time). The 2025 launch price was $189.
    - **Pros:** Made in the USA, open source. Native SatDump hydrasdr plugin plus an SDR++ fork. About 0.5-1 dB better than the Airspy R2 in the RTL-SDR.com review. Reaches 1800 MHz, so it covers Meteor and NOAA HRPT bands.
    - **Cons:** Expensive for a secondary receiver and largely redundant once the Lime arrives. Larger aluminium case. Mainline SDR++ did not recognize it at review time (fork needed). Shipping to Ukraine via DigiKey not verified.
    - **Sources:**
      - https://www.digikey.com/en/products/detail/benjamin-vernoux/HYDRASDR-RFONE/26256067
      - https://hydrasdr.com/
      - https://github.com/hydrasdr
      - https://www.rtl-sdr.com/category/hydrasdr/
      - https://github.com/SatDump/SatDump/tree/master/plugins/sdr_sources
    - **Availability:** In stock at DigiKey.
    - **Q6a compatibility:** Linux host tools build with CMake. Ubuntu 20.04+ and Debian 11+ are listed. No arm64 package was found, so expect to build from source.
  7.
    - **Name:** Airspy HF+ Discovery
    - **Key specs:** 0.5 kHz-31 MHz and 64-260 MHz (no 435 MHz, L-band or 740 MHz LNB IF). Up to 660 kHz bandwidth at 768 ksps. MDS -140 dBm (HF) and -141 dBm (VHF). Blocking dynamic range 110 dB (HF) / 95 dB (VHF). 45x60x10 mm.
    - **Price:** $169 list ($135.20 in the summer 2026 sale)
    - **Pros:** Best-in-class HF and VHF dynamic range. Excellent for 137 MHz LRPT and 145.8 MHz SSTV near strong FM. Small. ARM Linux and SatDump airspyhf plugin supported.
    - **Cons:** Does not cover 435 MHz CubeSats, the QO-100 IF or L-band. Narrow bandwidth. 4.5x the V4L price. Only worthwhile if serious HF listening becomes a goal.
    - **Sources:**
      - https://airspy.com/airspy-hf-discovery/
      - https://www.rtl-sdr.com/?p=66258
    - **Availability:** Through Airspy dealers (iTead and others).
    - **Q6a compatibility:** Good. Open-source libairspyhf, low USB bandwidth.
  8.
    - **Name:** SDRplay RSP1B / RSPdx-R2
    - **Key specs:** Both: 1 kHz-2 GHz, 14-bit, up to 10 MHz, bias tee, AM/FM/DAB notch filters. RSP1B has 11 band filters. RSPdx-R2 has 3 antenna inputs (BNC input limited to 200 MHz). Both 98x94x35 mm, 315 g.
    - **Price:** RSP1B: £105.80 ex VAT (~$141), out of stock at SDRplay until end of October; Moonraker US $141.99; Passion Radio €154.87 ex VAT. RSPdx-R2: £188 ex VAT (~$250); Moonraker $255.95.
    - **Pros:** Excellent front-end filtering and 14-bit range. API 3.15 Linux installer includes an ARM64 build. Supported by SoapySDRPlay3 and SatDump's sdrplay plugin.
    - **Cons:** Closed-source API and service daemon, tested only on Ubuntu LTS up to 24.04. At 315 g and almost 10x10 cm, larger and heavier than the Q6A itself, which breaks the palm-size goal. Higher cost.
    - **Sources:**
      - https://www.sdrplay.com/rsp1b/
      - https://sdrplay.com/product/rspdxr2/
      - https://www.sdrplay.com/api/
      - https://www.sdrplay.com/docs/SDRplay_API_Specification_v3.15.pdf
      - https://www.passion-radio.com/sdr-receivers/rsp1-b-2669.html
      - https://moonrakeronline.com/us/brands/sdr-play
    - **Availability:** Sold by EU resellers such as Passion Radio and Anico. The RSP1B is temporarily out of stock at SDRplay.
    - **Q6a compatibility:** Possible on Ubuntu 24.04 arm64 via the proprietary API, but not open source and vendor-tested only on Ubuntu LTS.
  9.
    - **Name:** MSI.SDR (MSi2500 + MSi001 RSP1 clone)
    - **Key specs:** Advertised 10 kHz-1 GHz (some listings claim 2 GHz). 12-bit ADC. Up to about 8 MHz bandwidth.
    - **Price:** About $30-65 on AliExpress
    - **Pros:** Cheap. 12-bit. SatDump has a mirisdr plugin.
    - **Cons:** Unauthorized clone with no support. Reported weak on 2 m and 70 cm, the core satellite bands. Linux drivers are messy: libmirisdr forks, and the msi2500 kernel module must be blacklisted. One user got no decodes via SoapyMiri.
    - **Sources:**
      - https://vu3dxr.in/exploring-the-msi-sdr-a-low-cost-gateway-into-software-defined-radio/
      - https://www.revspace.nl/Msi2500SDR
      - https://github.com/vladisslav2011/libmirisdr-4
    - **Availability:** AliExpress, with quality varying by seller
    - **Q6a compatibility:** Works only with effort. Not recommended.
  10.
    - **Name:** Airspy Ranger (not yet released)
    - **Key specs:** 0.5 kHz-2.6 GHz. Two 36 MS/s sigma-delta ADCs with an 18-bit DDC. 710 kHz alias-free output (912 ksps IQ). USB-C, MCX 10 MHz clock input.
    - **Price:** No official price. About $250 was rumoured on forums.
    - **Pros:** Would be a top-tier narrowband receiver.
    - **Cons:** Not on sale. The last official update (2025-06-06) says production was being optimized. Narrow bandwidth.
    - **Sources:**
      - https://airspy.com/airspy-ranger/
    - **Availability:** Not available October 2026 (unverified beyond the June 2025 status)
    - **Q6a compatibility:** Unknown
- **Recommended:**
  - **Name:** RTL-SDR Blog V4L (Lite), dongle only, from the official RTLSDRBlog AliExpress store
  - **Why:** It replaces the EOL V4 like-for-like:
  - Same HF upconverter, bias tee and TCXO, and the same ~1.3 W power class.
  - Slightly better VHF/UHF sensitivity.
  - $37.95, versus $99-250 for the 12-bit alternatives.
  - Avoids the high counterfeit risk of any 'V4' still listed.
  
  In this stack it does jobs the Lime cannot do at the same moment, because the Lime's two RX channels share one LO. It can take Meteor LRPT at 137 MHz or the QO-100 narrowband transponder at the ~740 MHz LNB IF, while the Lime takes HRPT at 1.7 GHz or S-band. It also adds 0.5-28.8 MHz HF that the Lime lacks, saving the $199 LimeFEA HF Micro. And it is the only SDR you can use before the Lime ships: Crowd Supply now says Dec 15, 2026 for new orders.
  
  Your existing FM bandstop filter offsets the lost triplexer and notch. Consider buying two now (about $76), since the R828S is also out of production and the stockpile is expected to last about one year.
  
  Optional upgrade if the budget allows: Airspy Mini ($99), for 12-bit dynamic range and a 10 MS/s window in RF-dense locations.
  - **Price:** $37.95 (official store / eBay); about $34.20 on the official AliExpress listing. Shipping to Ukraine via AliExpress; final landed price not verified.
  - **Sources:**
    - https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
    - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
    - https://www.rtl-sdr.com/rtl-sdr-blog-v4-end-of-line/
    - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
    - https://www.rtl-sdr.com/GENUINE
    - https://discourse.myriadrf.org/t/channel-a-for-100mhz-channel-b-for-1090mhz-at-same-time-is-that-ok/2538
    - https://www.crowdsupply.com/lime-micro/limesdr-micro
- **Budget option:**
  - **Name:** RTL-SDR Blog V3 (R860), dongle only, preferably the USB-C variant
  - **Why:** It is in stable production with mature drivers that work out of the box on Ubuntu 24.04 arm64, with no source build. VHF/UHF performance for 137, 145.8 and 435 MHz and the 740 MHz QO-100 IF is close to the V4L, and it has the same 4.5 V bias tee and 1 ppm TCXO. The trade-off is HF: it uses direct sampling, with aliasing and an MDS of about -115 to -120 dBm versus about -135 dBm on the V4L.
  
  It costs only about $3 less than the V4L. Choose it only if you want zero driver friction. Dropping the second SDR entirely saves $35-40 but loses simultaneous LRPT+HRPT, HF, and the only usable radio until the Lime arrives, so dropping is not recommended.
  - **Price:** $34.95-39.95 dongle only; $44.95-49.95 with the dipole kit (official stores)
- **Risks:**
  - Counterfeits: RTL-SDR Blog says nearly all other marketplace sellers of 'RTL-SDR Blog V3/V4' sell fakes. V4 fakes use a copied case with a V3-clone board inside. Buy only from RTLSDRBlog Store on AliExpress (store no. 4523039 / 1101427871) or eBay 'rtl-sdr-blog'. Check for diagonally placed side screws and a QC batch sticker.
  - The V4L is also a limited edition: the R828S is out of production and the stockpile is expected to last about one year. A V5 is only in early scoping. Buy a spare now.
  - Driver: the V4L gives NO signal with older librtlsdr. Ubuntu 24.04's packaged rtl-sdr predates the 2026 V4L commit. Any app with its own bundled old librtlsdr (some AppImages or Flatpaks) will fail. Build from Osmocom master or the rtlsdrblog fork and rebuild the dependent tools.
  - Overload: the V4L has the same two-tone performance as the V3. With a 95 MHz blocker, it desensitizes by 3 dB at about -12 dBm for low-VHF targets and -20 to -40 dBm for 300-1600 MHz targets, versus -7 dBm and +8 dBm for the V4. A broadband SPF5189Z LNA (about 20 dB gain) in front of an 8-bit dongle makes this worse. Keep the FM bandstop before the LNA, or use a band-specific filtered LNA.
  - Q6A USB power: Radxa does not document per-port current on the USB 2.0 ports. The V4L draws 250-270 mA, plus up to 180 mA when the bias tee feeds an LNA, which approaches the 500 mA USB 2.0 limit. Verify with a USB meter, or power LNAs from the main 5 V buck.
  - Q6A USB topology: Radxa's lsusb output shows a Terminus Technology hub on bus 001, so the three USB 2.0 ports may share about 30 MB/s. That is fine for the RTL plus GNSS and IMU, but marginal if an Airspy at 10 MS/s is added. Which physical ports sit behind the hub is unverified.
  - The LimeSDR Micro facts used here (now $249 and shipping Dec 15, 2026) come from the live Crowd Supply page. Cross-check them with the LimeSDR component research.
  - Unverified, because the web-search budget ran out near the end of research: iTead and DigiKey shipping to Ukraine, Prom.ua/Rozetka UAH prices, measured current for the Airspy Mini/HydraSDR/SDRplay units, and the LimeSDR Micro's power draw.
- **Integration notes:**
  - Driver install on Ubuntu 24.04 arm64: apt purge ^librtlsdr, then build https://github.com/osmocom/rtl-sdr (master, with the V4L commit 0204c9c) or rtlsdrblog/rtl-sdr-blog. Install the udev rules, blacklist dvb_usb_rtl28xxu, run ldconfig, then rebuild SoapyRTLSDR, gr-osmosdr, SatDump and SDR++ from source against the new library.
  - SatDump has native plugins for rtlsdr, airspy, airspyhf, hydrasdr, sdrplay, mirisdr and limesdr, so it can run two sources in parallel: V4L on 137 MHz LRPT plus the Lime on 1.7 GHz HRPT.
  - The Lime cannot replace the second tuner: both LMS7002M RX channels share one RX PLL, and their NCO offsets must stay within ±30.72 MHz of it at 61.44 MS/s.
  - QO-100: the narrowband transponder is about 500 kHz wide and lands near 739.5-740 MHz at the LNB IF, well inside the V4L's 2.4 MHz window. The Bullseye LNB needs a separate 12-19 V injector; the dongle's 4.5 V bias tee cannot power it, and a DC block must protect the SDR input.
  - Mount the dongle inside the case on a short shielded USB extension with a ferrite. Keep it away from the Q6A SoC and the PCIe SDR. The V4L's aluminium case dissipates through a thermal pad, so give it some airflow.
  - Use an MHF4/SMA pigtail or an external SMA bulkhead. Route the 137/145/435 MHz antennas to the V4L and the L/S-band chain to the LimeSDR. A cheap SMA RF switch or diplexer can share a single VHF/UHF antenna port.
  - Use the V4L's 2.4 MS/s 8-bit IQ (about 4.8 MB/s) as a low-cost, low-power capture source for collecting NN-classifier training data while the Lime is busy.
- **Double duty opportunities:**
  - The V4L's software bias tee (4.5 V, up to 180 mA) can power the masthead VHF/UHF LNA through the coax, removing a separate bias tee for the 137/145/435 MHz chain. Check that your SPF5189Z board works at 4.5 V; many are specified for 5 V (unverified).
  - The V4L's built-in HF upconverter (0.5-28.8 MHz) replaces the $199 LimeFEA HF Micro if HF or 10 m reception is ever wanted.
  - The V4L can act as the dedicated QO-100 narrowband transponder receiver at the LNB IF, leaving the LimeSDR free for a wide DATV transponder capture or another band.
  - It is the development and fallback SDR: the full SatDump, SDR++, GNU Radio and NPU-classifier pipeline can be built and tested now, before the LimeSDR Micro ships (Dec 15, 2026 for new orders). Afterwards it stays as a backup.
  - The RTL-SDR Blog V3 dipole kit ($44.95-49.95) bundles the V-dipole antenna listed in the antenna BOM. If you buy the V4L dongle-only, buy the $17.95 dipole kit separately.
- **Confidence:** high

## Форуми та досвід спільноти (`forums`)

_Run `wf_eb446444-464`_

- **Component:** Second / narrowband SDR (current pick RTL-SDR Blog V4, now EOL; proposed replacement RTL-SDR Blog V4L; alternatives V3, Nooelec SMArt v5, Airspy Mini, HydraSDR RFOne, SDRplay RSP1B/RSPdx-R2) for the Radxa Dragon Q6A handheld receiver
- **Experiences:**
  1.
    - **Product:** RTL-SDR Blog V4L
    - **Source url:** https://www.reddit.com/r/RTLSDR/comments/1wze65t/rtlsdr_v4l_first_look/
    - **Community:** Reddit r/RTLSDR (read via safereddit.com mirror)
    - **What they built:** Beginner, Oct 2026: V4L bought from the official RTL-SDR AliExpress store, used for Meteor-M LRPT. Other commenters: an ESP32-P4 (M5Stack Tab5) handheld 'OrcSDR' decoding FT8 on 40 m, and a V4 and V4L running on one Pi.
    - **Problems:**
      - First Meteor M2-4 attempt: nothing heard.
      - Commenter Ok_Method6238: with the wrong Osmocom driver the V4L is 'as deaf as a post'.
      - V4L has no VHF/UHF split and no FM notch, so it saturates more easily.
    - **Fixes:**
      - Install the current Osmocom librtlsdr.
      - neekthefreak: an external FM trap filter was 'more than enough'.
      - Hardcorererik: V4 and V4L both decoded FT8 on 7.074 MHz with an MLA-30+ loop.
    - **Outcome:** Users who had the V4L since August say it 'works good' once the driver is right. The OP's LRPT failure was not followed up.
  2.
    - **Product:** RTL-SDR Blog V4L vs V4 (side by side)
    - **Source url:** https://www.reddit.com/r/RTLSDR/comments/1wm6ulc/buying_the_rtlsdr_blog_v4l/
    - **Community:** Reddit r/RTLSDR
    - **What they built:** Ok_Method6238 runs V4 and V4L on the same antenna and LNA on a Raspberry Pi 500 web SDR server. zsellera runs an RC lap-timing system using a 5 MHz BPSK signal. lynxooo built a Pi 3B FM radio.
    - **Problems:**
      - V4L is slightly more prone to overload; AGC sets it one gain step lower than the V4 for the same SNR.
      - zsellera measured a 1-1.5 dB higher noise floor than the V4 around 4-6 MHz.
      - Without the correct driver the V4L shows only a DC spike and looks like junk.
    - **Fixes:**
      - Install the proper Osmocom driver first.
      - Use an FM filter.
      - Ok_Method6238 added custom AGC handling for RTL dongles in his server software.
    - **Outcome:** Positive overall: 'decent radio, not noticed any issues compared to my V4s'. For the lap-timing job the two radios were practically identical.
  3.
    - **Product:** RTL-SDR Blog V4L
    - **Source url:** https://github.com/AlexandreRouma/SDRPlusPlus/issues/1807
    - **Community:** GitHub SDR++ issues
    - **Problems:**
      - Windows 10, SDR++ 1.3.0, V4L selected: no signal.
    - **Fixes:**
      - Per related issue #1813: replace SDR++'s bundled rtlsdr DLL with the newest librtlsdr.
      - On Android: rebuild with the updated library. A fork upgraded to osmocom v2.0.3.
    - **Outcome:** Closed Aug 28, 2026 without a documented fix. Android support for the V4L in mainline SDR++ is still open (#1813), so any app with a bundled old librtlsdr fails.
  4.
    - **Product:** RTL-SDR Blog V4L
    - **Source url:** https://www.reddit.com/r/RTLSDR/comments/1wb1ssf/rtl_sdr_v4l_drivers/
    - **Community:** Reddit r/RTLSDR
    - **Problems:**
      - Uncertainty about Android support.
      - SDR++ described as 'a bit wonky' with the V4L.
    - **Fixes:**
      - Update Martin Marinov's 'SDR driver' app. RF Analyzer then worked.
    - **Outcome:** Working on Android, SDR# and SDR++ after driver updates (Sep 2026).
  5.
    - **Product:** RTL-SDR Blog V4 (Linux / Pi; same driver chain as V4L)
    - **Source url:** https://community.libre.space/t/rtlsdr-v4-not-receiving/11441
    - **Community:** SatNOGS community (libre.space)
    - **What they built:** SatNOGS ground station on a Raspberry Pi
    - **Problems:**
      - Distro rtl-sdr was too old for the V4.
      - After building rtl-sdr, rtl_fm worked but SatNOGS failed with 'SoapySDR::Device::make() no match' because the SoapyRTLSDR module (librtlsdrSupport.so) was missing.
    - **Fixes:**
      - Build rtl-sdr >= 2.0.1.
      - Then build SoapyRTLSDR from git (cmake / make / sudo make install).
      - Verify with SoapySDRUtil --info and SoapySDRUtil --probe=driver=rtlsdr.
    - **Outcome:** The module appeared and the probe was expected to work; final confirmation is on page 2 of the thread. Lesson: rebuild every dependent layer, not just librtlsdr.
  6.
    - **Product:** RTL-SDR Blog V4
    - **Source url:** https://community.libre.space/t/satnogs-3649-rtl-sdr-blog-v4-issues/11942
    - **Community:** SatNOGS community
    - **What they built:** Pi 3B+ SatNOGS station with a SAWbird+ NOAA LNA powered from the dongle's bias tee
    - **Problems:**
      - Blank waterfall and Soapy 'no match'.
      - Mixing the rtl-sdr.com package method with make install caused library conflicts.
      - Local HF FT8 transmissions overloaded the receiver.
    - **Fixes:**
      - Install the rtl-sdr 2.0.2 packages (openSUSE Build Service, Debian 11) and upgrade via apt rather than make install.
      - Use device args driver=rtlsdr,biastee=true.
      - Check lsusb, dmesg -w and udev/plugdev permissions.
    - **Outcome:** VA2WBT and w6msu got working stations. The original poster's fix was never confirmed, and the FT8 overload was not solved.
  7.
    - **Product:** RTL-SDR Blog V4 + SatDump in Docker
    - **Source url:** https://github.com/SatDump/SatDump/issues/1030
    - **Community:** GitHub SatDump issues
    - **What they built:** Headless Pi 4 SatDump autotrack station
    - **Problems:**
      - Bias-T, gain and DC block were silently ignored: no LNA power, DC spike, gain effectively 0.
      - Cause: the final Docker image shipped Debian's old librtlsdr instead of the self-built V4 driver.
    - **Fixes:**
      - Copy the self-built rtl-sdr into the final image.
      - Alternatively run rtl_eeprom -b1 to make the bias tee permanently on; the UI checkbox then has no effect.
    - **Outcome:** Fixed and closed Aug 2025. A wrong library fails silently, with no error message.
  8.
    - **Product:** RTL-SDR (V4) + SDR++ on Ubuntu 24.04
    - **Source url:** https://github.com/AlexandreRouma/SDRPlusPlus/issues/1524
    - **Community:** GitHub SDR++ issues
    - **Problems:**
      - The RTL-SDR source is missing from the menu because the plugin fails to load: 'librtlsdr.so.2: cannot open shared object file'.
      - Ubuntu's packaged library uses SONAME .so.2; an upstream source build installs .so.0.
    - **Fixes:**
      - Symlink: sudo ln -s /usr/local/lib/librtlsdr.so.0.6git /usr/lib/sdrpp/plugins/librtlsdr.so.2
      - Or build SDR++ itself from source against your librtlsdr.
    - **Outcome:** Both workarounds confirmed by users through Dec 2025. The official .deb still hits the problem.
  9.
    - **Product:** RTL-SDR Blog V4 / Nooelec SMArTee on Pi 4 64-bit
    - **Source url:** https://github.com/SatDump/SatDump/issues/864
    - **Community:** GitHub SatDump issues
    - **Problems:**
      - SatDump 1.2.1 .deb: rtlsdr_sdr.cpp:214 error on Start, although rtl_test worked.
      - Building from source with make -j$(nproc) froze the Pi at about 45%.
      - The nightly .deb would not install.
    - **Fixes:**
      - Build with make -j3, one core fewer than available.
    - **Outcome:** Closed Feb 2026 without a documented root cause.
  10.
    - **Product:** RTL-SDR Blog V4 on Raspberry Pi 5
    - **Source url:** https://www.reddit.com/r/RTLSDR/comments/1va84rm/raspberry_pi_5_causing_rfi_that_kills_rtlsdr_blog/
    - **Community:** Reddit r/RTLSDR
    - **What they built:** Pi 5 + V4 + SatDump for Meteor-M LRPT
    - **Problems:**
      - Severe RFI only when the dongle is on the Pi: SNR 0-2.7 dB, no Viterbi sync, 0 bytes of CADU over a 14-minute pass.
      - A clean signal on a laptop.
      - Moving the dongle 0.8-2 m away on a USB extension did not help, which points to conducted noise via USB/power.
    - **Fixes:**
      - Suggested: ferrite on the cable, a USB isolator, powering from a power bank (ground loop), or a powered USB-OTG hub fed from a battery so the dongle does not take the host's noisy 5 V.
      - One commenter suggested an Intel N100 host instead of a Pi 5.
    - **Outcome:** Unresolved in the thread. This is the closest analogue to a Q6A plus buck-converter build.
  11.
    - **Product:** Airspy Mini on Raspberry Pi 4/5
    - **Source url:** https://www.reddit.com/r/RTLSDR/comments/1akc7vf/i_solved_rf_noise_from_pc_raspberry_but_dont_know/
    - **Community:** Reddit r/RTLSDR
    - **What they built:** VHF airband recorder: Diamond D777 antenna, Nooelec LNA, Airspy Mini, Pi 4
    - **Problems:**
      - Noise spikes injected from the Pi via USB.
      - A 5 m cable and wrapping the Pi in foil did not help.
      - Root cause found: poor contact between the USB shield and the Airspy Mini's metal body.
      - Another user traced Pi 5 spikes to poorly regulated USB 5 V from the Pi's switching PMIC.
    - **Fixes:**
      - Wrap or bond the Airspy body to the USB cable shield (common ground).
      - Alternatively switch to a quieter host (an ASRock J4125 mini-PC fixed it).
    - **Outcome:** Spikes were largely removed but came back when the cable moved. The OP eventually moved to an x86 mini-PC.
  12.
    - **Product:** RTL-SDR (generic, incl. Blog dongles) in 24/7 SatNOGS use
    - **Source url:** https://community.libre.space/t/observation-13477706-acs3-59588-eggbeater-not-a-valid-pass-what-what-could-cause-it/14461
    - **Community:** SatNOGS community
    - **Problems:**
      - Broadband noise above about 450 MHz appearing in observations.
      - PE0SAT: 'This is a RTL-SDR problem, the only way to correct this behavior is remove the RTL-SDR and reinsert'. Root cause unknown after a long time.
    - **Fixes:**
      - Replug the dongle (USB power cycle).
      - PE0SAT replaced all his production SDRs with HydraSDR RFOne, Airspy Mini/R2, HackRF etc.
    - **Outcome:** No root-cause fix (Feb 2026).
  13.
    - **Product:** RTL-SDR (8-bit) vs Airspy / HydraSDR (12-bit) for 70 cm CubeSats
    - **Source url:** https://community.libre.space/t/impact-of-sdr-adc-resolution-on-telemetry-decoding-qmr-kwt-2-sakhacube-cholbon/14525
    - **Community:** SatNOGS community
    - **What they built:** SatNOGS station 4394 on an RTL-SDR (biastee=true, gain 28, 2.048 Msps), compared with stations using Airspy, HydraSDR and UHD SDRs
    - **Problems:**
      - The RTL station could never decode QMR-KWT 2 or SAKHACUBE-CHOLBON; 12-bit stations could.
      - Its signals were off-centre (LO ppm error).
    - **Fixes:**
      - PE0SAT: correct the LO with the ppm setting.
      - Use gr-satellites (SatNOGS cannot decode USP framing).
      - He decoded the OP's own recording with gr_satellites SAKHACUBE-CHOLBON.yml --wavfile ... --samp_rate 48e3.
      - Noted that filtering and dynamic range matter, not only ADC bits.
    - **Outcome:** The decode was possible from the RTL recording, so the problem was the setup, not the 8 bits.
  14.
    - **Product:** RTL-SDR + RTL-SDR Blog wideband LNA (bias tee) + FM bandstop
    - **Source url:** https://community.libre.space/t/fm-bandstop-not-working/13752
    - **Community:** SatNOGS community
    - **What they built:** QFH antenna, FM bandstop, wideband LNA and RTL-SDR, 1-2.5 km from three FM transmitters
    - **Problems:**
      - FM station images every ~10 MHz, including at 70 cm, from LNA overload.
      - Bandstop results were inconsistent, swapping between filters.
      - Final cause: unshielded 10 m TV coax picking up FM.
    - **Fixes:**
      - Put the filter before the LNA when FM overloads the LNA.
      - SA2KNG: start with very low RTL gain (3-10 dB), change one thing at a time, put chokes on everything attached to the host and on the coax.
      - Use proper coax.
    - **Outcome:** Resolved Sep 23, 2025: interference was the TV cable. Shows a wideband LNA plus RTL near FM transmitters needs filtering and shielding discipline.
  15.
    - **Product:** RTL-SDR Blog V4 + LNAs for Meteor 137 MHz
    - **Source url:** https://www.reddit.com/r/amateursatellites/comments/1tviwhl/lna_choice_for_meteor_m2_137_mhz_with_rtlsdr_v4/
    - **Community:** Reddit r/amateursatellites
    - **Problems:**
      - The wideband RTL-SDR Blog LNA 'will amplify junk'.
      - The Nooelec SAWbird NOAA has DC 'backfeed' onto its output SMA that could damage the SDR.
    - **Fixes:**
      - Community default: an AliExpress '137 MHz BPF + LNA' filtered module, or a wideband LNA plus a SAW filter.
      - Add a DC block.
      - Some users run with no LNA and only a bandpass filter.
    - **Outcome:** Consensus: use a band-filtered LNA ahead of an RTL.
  16.
    - **Product:** RTL-SDR Blog V4 + SatDump (Meteor LRPT)
    - **Source url:** https://www.reddit.com/r/amateursatellites/comments/1s0la7b/getting_nothing_on_meteor_m23_lrpt_despite/
    - **Community:** Reddit r/amateursatellites
    - **What they built:** V-dipole, generic AliExpress 137 MHz SAW LNA on the bias tee, V4, SatDump 1.2.2
    - **Problems:**
      - NOSYNC with SNR 0 even on 70-degree passes after adding the LNA (gain 16 dB, decimation 8).
    - **Fixes:**
      - Decimation 1.
      - Raise gain while watching SNR.
      - Align the V-dipole with the AOS-LOS track instead of N-S. One user re-points a handheld dipole during the pass.
    - **Outcome:** Got signal after re-orienting the antenna. Relevant to the on-screen pointing aid.
  17.
    - **Product:** HydraSDR RFOne (portable LRPT/HRPT)
    - **Source url:** https://www.reddit.com/r/amateursatellites/comments/1oc8njb/meteorm_n23_phoenix_reception_at_the_bus_stop/
    - **Community:** Reddit r/amateursatellites
    - **What they built:** rad750: hand-held V-dipole, AliExpress SAW-filtered LNA, HydraSDR and SatDump, used in the city at a bus stop. Same user did Meteor-M2-4 HRPT 'while hiking' with a hand-held Discovery Dish, HydraSDR and a laptop (https://www.reddit.com/r/amateursatellites/comments/1ol0knp/meteorm_n24_hrpt_while_hiking/).
    - **Problems:**
      - In-city interference confused the Costas loop when the bandwidth was too wide.
    - **Fixes:**
      - Sample at 2.5 MHz and decimate 14x to about 180 kHz, the LRPT width.
    - **Outcome:** 'Works exceedingly well'. A horizon-to-horizon HRPT pass (~5820 lines) was also received hand-held.
  18.
    - **Product:** HydraSDR RFOne
    - **Source url:** https://github.com/hydrasdr/rfone_host/issues/25
    - **Community:** GitHub hydrasdr host issues
    - **Problems:**
      - A strong local DMR repeater (164.4 MHz) folded back as a phantom signal 33 dB above the noise, inside the advertised alias-free span at 10 MSPS.
      - The R828D IF filter leaves only about 370 kHz of guard band before ADC Nyquist.
      - SoapyHydraSDR getBandwidth/listBandwidths return nothing useful.
    - **Fixes:**
      - Reporter patched SDR++ to crop the outer 15% of the span, leaving about 8.5 MHz usable.
      - Register-level IF narrowing gave only 12-14 dB.
    - **Outcome:** Closed Sep 29, 2026 without a documented code or documentation change. The maintainer asked for IQ captures and dBm levels.
  19.
    - **Product:** HydraSDR RFOne
    - **Source url:** https://github.com/hydrasdr/rfone_host/issues/8
    - **Community:** GitHub hydrasdr host issues
    - **Problems:**
      - USB-C connector became loose and the unit failed about a month and ~10 insertions after purchase.
    - **Fixes:**
      - None. Redirected to HydraSDR sales (RMA).
    - **Outcome:** Closed as invalid (hardware, not software). Isolated report, but relevant for a field device: use strain relief and a fixed cable.
  20.
    - **Product:** HydraSDR RFOne (SatNOGS, ARM host)
    - **Source url:** https://community.libre.space/t/satnogs-client-v2-1-release/14021/45
    - **Community:** SatNOGS community
    - **What they built:** PE0SAT station 2173: EggBeater, Spacewalker LNA, HydraSDR RFOne, some units GPSDO-locked (see https://community.libre.space/t/spacewalker-lna-434-mhz/11431/15)
    - **Problems:**
      - Integration was new in SatNOGS client 2.1 (Docker): 'needs some polishing'.
    - **Fixes:**
      - Run SatNOGS client 2.1+, which ships HydraSDR udev rules and SoapyHydraSDR.
    - **Outcome:** Working production stations by Dec 2025 to Mar 2026, praised for 'no center spike and great performance'.
  21.
    - **Product:** HydraSDR RFOne (criticism thread)
    - **Source url:** https://www.reddit.com/r/RTLSDR/comments/1m2asn5/hydrasdr_rfone_8211_technical_limitations_and/
    - **Community:** Reddit r/RTLSDR
    - **Problems:**
      - A blog post claimed 'driver problems'. Commenters called it AI link-spam without sources; the HydraSDR creator disputed it point by point.
    - **Fixes:**
      - n/a
    - **Outcome:** No concrete driver defect was substantiated. The real early gaps were mainline SDR++ support (a fork is needed) and SDR# relying on Airspy VID/PID.
  22.
    - **Product:** Airspy Mini on Raspberry Pi 4
    - **Source url:** https://community.libre.space/t/rapsberry4-would-be-happy-with-an-updated-image/6311
    - **Community:** SatNOGS community
    - **Problems:**
      - The Pi 4 USB bug cut airspy_rx from 6 MSps to 2.1 (USB 2.0 port) and 2.9 (USB 3.0 port).
      - rtl_test lost 400-15000 samples per read.
    - **Fixes:**
      - apt update && apt upgrade, then rpi-update (newer kernel).
      - Fix CA certificates first: apt purge ca-certificates && apt install ca-certificates.
    - **Outcome:** Solved by the kernel update (2020). Shows SBC USB host-controller kernel quality decides whether 10 MSPS USB 2.0 SDRs work.
  23.
    - **Product:** Airspy Mini (SatNOGS / Linux)
    - **Source url:** https://community.libre.space/t/airspy-mini-frequency-offset/8984
    - **Community:** SatNOGS community
    - **Problems:**
      - Constant ~200 Hz offset broke demodulation.
      - The SoapyAirspy driver ignores ppm and bb_freq correction.
    - **Fixes:**
      - Only the Windows AirspyCalibrate.exe (from SDR#) was suggested.
    - **Outcome:** No Linux-native fix in the thread.
  24.
    - **Product:** Airspy (R2/Mini) + RTL in SatDump 2.0 alpha
    - **Source url:** https://github.com/SatDump/SatDump/issues/1169
    - **Community:** GitHub SatDump issues
    - **Problems:**
      - Clicking Stop on an Airspy source deadlocks the satdump-UI thread (libairspy streaming thread blocked in stream->swap()).
      - RTL sources are not affected.
    - **Fixes:**
      - Reporter's patch: call output_stream->stopWriter() before airspy_stop_rx(), and clearWriteStop() in start().
    - **Outcome:** Patch works for the reporter. PR #1172 open; not merged as of Oct 2026.
  25.
    - **Product:** Two SDRs in SatDump (RTL-SDR + Airspy R2)
    - **Source url:** https://github.com/SatDump/SatDump/issues/1177
    - **Community:** GitHub SatDump issues
    - **What they built:** Two satdump_sdr_server instances (ports 5656/5657) on one Linux host, for side-by-side comparison
    - **Problems:**
      - The first server instance holds every attached SDR, so the second gets 'Could not open Airspy device!'.
    - **Fixes:**
      - None yet. Proposed: the server should release SDRs it is not using.
    - **Outcome:** Open (Jul 2026). Directly relevant to running V4L plus LimeSDR concurrently.
  26.
    - **Product:** Two RTL dongles (Nooelec SMArt XTR + RTL-SDR Blog V4) with SatDump CLI
    - **Source url:** https://www.reddit.com/r/RTLSDR/comments/1fm3v0o/defining_which_rtl_sdr_in_satdump_cli/
    - **Community:** Reddit r/RTLSDR
    - **What they built:** Pi 4B: goestools on the Nooelec for GOES HRIT, SatDump autotrack on the V4 for polar passes
    - **Problems:**
      - SatDump always grabbed the first dongle. Every RTL ships with SN 00000001.
    - **Fixes:**
      - Set unique serials with rtl_eeprom -s.
      - Add 'source_id': '00000002' (quoted) to autotrack.json. This was found in a GitHub issue, not the documentation.
    - **Outcome:** Solved.
  27.
    - **Product:** RTL-SDR Blog V4 heat and power on SBCs
    - **Source url:** https://www.reddit.com/r/RTLSDR/comments/1qqr2bl/rtlsdr_temperature_on_raspberry_pi_vs_intel_does/
    - **Community:** Reddit r/RTLSDR
    - **Problems:**
      - The V4 got hot to the touch on a Pi but only warm on a PC.
      - One user said the Raspbian-repo driver runs the dongle hotter than the rtlsdrblog driver.
      - Two dongles on one Pi caused undervoltage warnings.
      - A CM4 in a closed case with a V4 ran at 50-70 C.
    - **Fixes:**
      - Short USB extension (strain and heat isolation).
      - Feed the dongles' 5 V from an external stabilised supply, keeping only GND/D+/D- to the Pi.
    - **Outcome:** Power warnings were solved by external 5 V. The heat cause was not settled.
  28.
    - **Product:** RTL-SDR (R820T family) at L-band when hot
    - **Source url:** https://www.rtl-sdr.com/showing-how-the-r820t-stops-receiving-at-1-4-ghz-with-increasing-temperature/
    - **Community:** RTL-SDR.com
    - **Problems:**
      - Tuner PLL loses lock as the dongle warms up, killing reception above about 1.4-1.5 GHz. Chip-to-chip variation.
    - **Fixes:**
      - Thermal pad to the metal case (RTL-SDR Blog design).
      - A driver tweak that sets VCO current at init (https://www.rtl-sdr.com/beta-testing-a-modified-rtl-sdr-driver-for-l-band-heat-issues/).
    - **Outcome:** Fixed for 'almost all dongles'. Some still fail after hours. The V4L's 1.766 GHz upper limit at L-band is therefore not dependable in a hot case.
  29.
    - **Product:** RTL-SDR Blog V4 HF upconverter spurs (same 28.8 MHz architecture in V4L)
    - **Source url:** https://www.reddit.com/r/RTLSDR/comments/1pfnvqa/rtlsdr_creates_fake_signals_that_spread_from_288/
    - **Community:** Reddit r/RTLSDR
    - **Problems:**
      - Families of spurs spreading from 28.8 MHz and around 1 MHz, present with no antenna connected.
    - **Fixes:**
      - Lower the LNA gain; set LNA, mixer and VGA gains separately.
      - One user: tune 28.801 MHz, 'centre on frequency', then untoggle.
    - **Outcome:** Accepted as a design artefact: the TCXO and upconverter LO are both 28.8 MHz.
  30.
    - **Product:** RTL-SDR Blog V4 counterfeits
    - **Source url:** https://www.reddit.com/r/RTLSDR/comments/1ug51f0/real_or_fake_v4/
    - **Community:** Reddit r/RTLSDR
    - **Problems:**
      - Since the V4 went EOL, 'real or fake' posts are frequent.
    - **Fixes:**
      - Genuine cues: offset (diagonal) screws, laser-etched rather than white-ink markings, the upconverter's big baluns, notch filter and triplexer, thermal pad, R828D with normal marking.
      - rtl_test should show 'RTLSDRBlog, Blog V4' and 'RTL-SDR Blog V4 Detected'; SN 00000001 is normal.
      - Commenters: avoid 'htool'-branded units.
    - **Outcome:** This unit was judged genuine. Fakes are now common.
  31.
    - **Product:** 'RTL-SDR V4' listings in Ukraine
    - **Source url:** https://prom.ua/ua/search?search_term=rtl-sdr%20v4l
    - **Community:** Prom.ua marketplace (Ukraine)
    - **Problems:**
      - Search for 'rtl-sdr v4l' (Oct 2026) returned about 29 receivers. All were labelled 'V4', none V4L, at 3,000-8,531 UAH (about $72-205), mostly unbranded boards, including 'HTOOL SDR V4' at 3,460 UAH.
    - **Fixes:**
      - Buy from the official RTLSDRBlog AliExpress store (no. 4523039 / 1101427871) or eBay rtl-sdr-blog instead.
    - **Outcome:** Local marketplace stock in Ukraine is high-risk for fakes and costs 2-5 times the official V4L price.
  32.
    - **Product:** Genuine V4 still at official resellers / V4 board revision
    - **Source url:** https://www.reddit.com/r/RTLSDR/comments/1x2tw7f/rtlsdr_blog_v4l_lite_anywhere_cheaper_then_75_in/
    - **Community:** Reddit r/RTLSDR
    - **Problems:**
      - The V4L costs up to GBP 75 at UK resellers.
      - A Technofix 'V4' bought Aug 2026 had a 2026-03-16 PCB that looked like the V4L but carried an R828D (https://www.reddit.com/r/RTLSDR/comments/1vn7abs/v4_or_v4_light_which_version_have_i_received/).
    - **Fixes:**
      - The official UK reseller TechnoFix still listed genuine V4s at GBP 46 in Oct 2026 and delivered in 2 days.
      - The updated driver supports V3, V4 and V4L, so install the newest driver regardless of which board you got.
    - **Outcome:** Genuine V4 leftovers can still be found at listed resellers in some countries.
  33.
    - **Product:** SDRplay RSP1A/RSP2/RSPduo on Raspberry Pi (SatNOGS 2.1.x Docker)
    - **Source url:** https://community.libre.space/t/sdrplay-and-client-version-2-1-1/14380
    - **Community:** SatNOGS community
    - **Problems:**
      - The closed-source sdrplay_apiService was not visible inside the container.
      - After reboot, SoapySDRUtil --probe hangs or reports 'no available RSP devices found' or a shm_open error.
      - Maintainers called the API service 'a black box'.
      - SatNOGS had no supported SDRplay path in 2.1 until a dev-branch MR.
    - **Fixes:**
      - Enable satnogs_non_free_sdrplay_enabled: true on the master Ansible branch.
      - Add the user to the docker group.
      - After every reboot: docker restart satnogs_satnogs-client satnogs_sdrplay.
    - **Outcome:** Works only with a manual service restart after boot (Feb 2026); root cause unknown. A related RPi4 + RSP1A user gave up and switched to an RTL-SDR V4 (https://community.libre.space/t/install-and-run-on-rpi4-and-sdrplay-rsp1a/12785).
  34.
    - **Product:** SDRplay RSP1A/RSP1B on Raspberry Pi 5 64-bit
    - **Source url:** https://discussions.flightaware.com/t/help-with-sdrplay-rsp1b-to-upload-adsb-data/92031
    - **Community:** FlightAware forum
    - **Problems:**
      - API 3.15.2 on Pi 5: dump1090-fa via SoapySDRPlay3 failed at activateStream() with 'Init() failed: sdrplay_api_Fail'.
      - dump978-fa does not work with Soapy-based SDRplay devices.
    - **Fixes:**
      - Use SDRplay's own dump1090 build (SDRPLAY=1 make dump1090, run with --dev-sdrplay).
      - Or forward its output with socat or readsb.
    - **Outcome:** RSP1B worked with the vendor-specific build. The Soapy path stayed broken for one user and worked for another on an RSP1/RSPduo.
  35.
    - **Product:** LimeSDR Mini v2.2 at 137 MHz (why a separate VHF SDR helps)
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-mini-v2-2-rx-interference-issues/8073
    - **Community:** MyriadRF discourse
    - **What they built:** NOAA APT on a roof discone, LimeSDR Mini v2.2 compared with an SDRplay RSPdx
    - **Problems:**
      - The Lime image had wavy interference lines; the RSPdx was clean on the same antenna.
    - **Fixes:**
      - Planned: extra shielding cans and bigger decoupling capacitors.
    - **Outcome:** Unresolved. Lime staff were not aware of the issue.
  36.
    - **Product:** LimeSDR (LMS7002M) dual-RX limits and LimeSDR Micro facts
    - **Source url:** https://discourse.myriadrf.org/t/xtrx-independent-dual-channel-rx/8480
    - **Community:** MyriadRF discourse
    - **Problems:**
      - 70 MHz plus 220 MHz at once is impossible because both RX channels share one LO.
      - The LimeSDR Micro docs show the RX lower end as 300 MHz (https://discourse.myriadrf.org/t/limesdr-micro-m-2-pcie-frequency-range/13348).
      - Board draw is about 4 W (https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304).
    - **Fixes:**
      - Put the LO midway and NCO-shift each channel, limited to ±30.72 MHz at 61.44 MSps.
      - Lime staff (Oct 13, 2026): there are no coverage gaps; matching networks are optimised from 300 MHz.
    - **Outcome:** Confirms that a separate low-power VHF/UHF receiver is needed for LRPT/SSTV/CubeSats concurrent with L/S-band on the Lime. The Lime's 137 MHz performance is below its optimised match and unmeasured.
  37.
    - **Product:** Radxa Dragon Q6A USB 2.0 subsystem (host for the narrowband SDR)
    - **Source url:** https://forum.radxa.com/t/dragon-q6a-four-usb-uvc-cameras-fail-due-to-excessive-bandwidth-reservation/31352
    - **Community:** Radxa forum
    - **Problems:**
      - Only two USB 2.0 UVC cameras per USB 2.0 bus work, because each reserves the maximum isochronous bandwidth.
      - Radxa docs show a Terminus FE1.1s hub (1a40:0101) on bus 001 that also carries the onboard AIC8800D80 Wi-Fi/BT (https://docs.radxa.com/en/dragon/q6a/hardware-use/usb).
      - No per-port current limit is documented.
    - **Fixes:**
      - None posted (no replies).
    - **Outcome:** No SDR-on-Q6A report exists. Searches of the Radxa forum (Discourse API: 'rtl-sdr', 'sdr', 'rtl2832', 'hackrf') and r/SBCs found nothing.
- **Common problems:**
  1.
    - **Problem:** The device is detected but 'deaf' (no signal, only a DC spike) because the loaded librtlsdr is too old. The V4L needs osmocom rtl-sdr v2.0.3 (tagged Aug 11, 2026; commit 0204c9c). Ubuntu 24.04 ships 2.0.1 (librtlsdr2) and 26.04 ships 2.0.2, so neither supports the V4L; only the next Ubuntu dev series has 2.0.3-1. The V4 is supported from 2.0.1, so it works with stock 24.04 packages.
    - **Affected products:** RTL-SDR Blog V4L, V4
    - **Frequency:** common
    - **Known fix:** Run apt purge ^librtlsdr and remove stale /usr/local copies. Build osmocom master or v2.0.3 with cmake -DINSTALL_UDEV_RULES=ON, then make install and ldconfig. Blacklist dvb_usb_rtl28xxu and reboot. Check with rtl_test for 'Blog V4L' detection and with ldconfig -p | grep rtlsdr to confirm only one library. Note the official V4L guide clones osmocom/rtl-sdr but then says cd rtl-sdr-blog, a documentation bug.
    - **Fix sources:**
      - https://www.rtl-sdr.com/V4L
      - https://github.com/osmocom/rtl-sdr/tags
      - https://packages.ubuntu.com/search?keywords=rtl-sdr&searchon=names&exact=1
      - https://www.reddit.com/r/RTLSDR/comments/1wm6ulc/buying_the_rtlsdr_blog_v4l/
      - https://www.sdrstore.eu/rtl-sdr-v4l-setup-guide-windows-linux-raspberry-pi-sdrpp-sdrsharp-adsb/
  2.
    - **Problem:** Dependent layers keep using or expecting the old library. The SoapyRTLSDR module is missing ('make() no match'). SDR++ .deb plugins want librtlsdr.so.2 (Debian SONAME) while upstream builds install .so.0. Docker images, AppImages and app-bundled DLLs carry an old librtlsdr. apt upgrades restore old packages. In every case bias tee, gain and DC-block settings are silently ignored.
    - **Affected products:** All RTL-SDR Blog models with SatDump, SDR++, SoapySDR, gr-osmosdr and SatNOGS on Linux/ARM
    - **Frequency:** common
    - **Known fix:** Rebuild SoapyRTLSDR, gr-osmosdr, SDR++ and SatDump from source against the new library, or symlink librtlsdr.so.2 to the new .so. Check with SoapySDRUtil --info and --probe=driver=rtlsdr. Put the new library inside any container image. Pin and hold librtlsdr packages. A cleaner route on Ubuntu (an inference, untested) is to rebuild the Debian 2.0.3-1 source package so the librtlsdr2 SONAME is kept.
    - **Fix sources:**
      - https://community.libre.space/t/rtlsdr-v4-not-receiving/11441
      - https://github.com/AlexandreRouma/SDRPlusPlus/issues/1524
      - https://github.com/SatDump/SatDump/issues/1030
      - https://community.libre.space/t/satnogs-3649-rtl-sdr-blog-v4-issues/11942
  3.
    - **Problem:** Noise from the SBC host conducted over USB 5V or ground ruins VHF reception. Pi 4/5 PMIC switching noise and poor USB-shield-to-case contact (Airspy Mini) are documented. Moving the dongle away on an extension does not help.
    - **Affected products:** RTL-SDR V4/V4L/V3, Airspy Mini, any USB SDR on an SBC with switching regulators
    - **Frequency:** common
    - **Known fix:** Bond the USB cable shield to the SDR case and antenna ground. Use a short shielded USB cable with clip-on ferrites. Feed the dongle's 5 V from a separate clean supply or a powered hub from the battery (power bank fixed some cases). Use a USB isolator as a last resort. Chokes on coax and host cables. Test with the antenna removed.
    - **Fix sources:**
      - https://www.reddit.com/r/RTLSDR/comments/1va84rm/raspberry_pi_5_causing_rfi_that_kills_rtlsdr_blog/
      - https://www.reddit.com/r/RTLSDR/comments/1akc7vf/i_solved_rf_noise_from_pc_raspberry_but_dont_know/
      - https://community.libre.space/t/fm-bandstop-not-working/13752
  4.
    - **Problem:** Overload or intermodulation from FM, DAB, DVB-T and nearby transmitters when a broadband LNA (SPF5189Z-class) feeds an 8-bit RTL. The V4L has no notch or VHF/UHF split, so its two-tone performance equals the V3's. Users see FM images every ~10 MHz up to 70 cm.
    - **Affected products:** RTL-SDR V4L, V3, Nooelec SMArt (any R820T2/R860/R828S dongle); less so V4, Airspy, HydraSDR, SDRplay
    - **Frequency:** common
    - **Known fix:** Use a band-specific filtered LNA (137 MHz BPF+LNA, 435 MHz SAW LNA) or put the filter before the LNA. Add an FM bandstop at the SDR. Turn AGC off. Raise gain only until the noise floor rises about 5 dB. Decimate to the signal width (about 180 kHz for LRPT). Add a DC block if the LNA back-feeds bias.
    - **Fix sources:**
      - https://www.reddit.com/r/amateursatellites/comments/1tviwhl/lna_choice_for_meteor_m2_137_mhz_with_rtlsdr_v4/
      - https://community.libre.space/t/fm-bandstop-not-working/13752
      - https://www.reddit.com/r/amateursatellites/comments/1oc8njb/meteorm_n23_phoenix_reception_at_the_bus_stop/
      - https://www.reddit.com/r/RTLSDR/comments/1wm6ulc/buying_the_rtlsdr_blog_v4l/
  5.
    - **Problem:** Counterfeit 'RTL-SDR Blog V4' units. The V4 is EOL; Prom.ua lists only unbranded 'V4' boards at 3,000-8,500 UAH, including 'HTOOL'. Fakes copy the case and contain a V3-clone circuit.
    - **Affected products:** RTL-SDR Blog V4 (and V3) bought from third-party marketplace sellers
    - **Frequency:** common
    - **Known fix:** Buy only from the RTLSDRBlog AliExpress store, eBay rtl-sdr-blog, or listed resellers. Check diagonal screws, laser-etched marking, thermal pad, R828D marking with no 'PCB squiggle', and rtl_test output 'RTL-SDR Blog V4 Detected'.
    - **Fix sources:**
      - https://www.rtl-sdr.com/GENUINE
      - https://www.reddit.com/r/RTLSDR/comments/1ug51f0/real_or_fake_v4/
      - https://prom.ua/ua/search?search_term=rtl-sdr%20v4l
  6.
    - **Problem:** Running two SDRs on one host. Every RTL ships with serial 00000001. SatDump picks the first device. One satdump_sdr_server instance claims all SDRs. Only one process can open a dongle at a time.
    - **Affected products:** RTL-SDR (any), Airspy, mixed RTL + Lime setups in SatDump
    - **Frequency:** occasional
    - **Known fix:** Set unique serials with rtl_eeprom -s. Select the device by source_id in SatDump autotrack.json. Run separate processes per SDR. Do not use one satdump_sdr_server for both (issue #1177 is open).
    - **Fix sources:**
      - https://www.reddit.com/r/RTLSDR/comments/1fm3v0o/defining_which_rtl_sdr_in_satdump_cli/
      - https://github.com/SatDump/SatDump/issues/1177
  7.
    - **Problem:** Heat and power. RTL dongles run hot on SBCs and in closed cases. R820T-family PLLs lose lock above about 1.4-1.5 GHz when hot. Several dongles plus bias-tee loads trigger host undervoltage.
    - **Affected products:** RTL-SDR V3/V4/V4L, Nooelec SMArt
    - **Frequency:** occasional
    - **Known fix:** Keep the thermal pad and aluminium case. Give airflow and keep the dongle away from the SoC heatsink. Use a short extension. Power dongles or LNAs from an external 5 V rail. Do not rely on an RTL for 1.7 GHz.
    - **Fix sources:**
      - https://www.rtl-sdr.com/showing-how-the-r820t-stops-receiving-at-1-4-ghz-with-increasing-temperature/
      - https://www.reddit.com/r/RTLSDR/comments/1qqr2bl/rtlsdr_temperature_on_raspberry_pi_vs_intel_does/
  8.
    - **Problem:** An RTL-SDR enters a noisy state (broadband noise above about 450 MHz) that only clears on replug. The root cause is unknown, even to an experienced SatNOGS operator.
    - **Affected products:** RTL-SDR dongles in long-running stations
    - **Frequency:** occasional
    - **Known fix:** Power-cycle the USB port (replug). The operator migrated production stations to Airspy and HydraSDR.
    - **Fix sources:**
      - https://community.libre.space/t/observation-13477706-acs3-59588-eggbeater-not-a-valid-pass-what-what-could-cause-it/14461
  9.
    - **Problem:** Weak FSK/BPSK CubeSat telemetry fails on 8-bit RTL stations while 12-bit stations decode, often compounded by LO ppm offset and missing gr-satellites framing.
    - **Affected products:** RTL-SDR (8-bit) vs Airspy/HydraSDR (12-bit)
    - **Frequency:** occasional
    - **Known fix:** Correct ppm (V4L TCXO is 1 ppm, but still check). Use gr-satellites with the satellite's .yml. Record IQ and decode offline. Consider a 12-bit SDR for marginal satellites.
    - **Fix sources:**
      - https://community.libre.space/t/impact-of-sdr-adc-resolution-on-telemetry-decoding-qmr-kwt-2-sakhacube-cholbon/14525
  10.
    - **Problem:** The SDRplay closed API service on ARM Linux is opaque. Probes hang after boot or replug ('no available RSP devices', shm_open errors). activateStream fails through Soapy on Pi 5 with API 3.15.2. Only Ubuntu LTS up to 24.04 is vendor-tested.
    - **Affected products:** SDRplay RSP1A/RSP1B/RSP2/RSPduo/RSPdx(-R2) on ARM64
    - **Frequency:** occasional
    - **Known fix:** Restart sdrplay_apiService (or its container) after boot or replug. Use vendor-specific builds. No root-cause fix exists.
    - **Fix sources:**
      - https://community.libre.space/t/sdrplay-and-client-version-2-1-1/14380
      - https://discussions.flightaware.com/t/help-with-sdrplay-rsp1b-to-upload-adsb-data/92031
  11.
    - **Problem:** Airspy and HydraSDR software gaps:
  - No Linux ppm correction in SoapyAirspy (Windows-only AirspyCalibrate).
  - SatDump 2.0-alpha Airspy Stop deadlock.
  - Mainline SDR++ needs a HydraSDR fork.
  - HydraSDR strong-signal aliasing near the band edge at 10 MSPS.
    - **Affected products:** Airspy Mini/R2, HydraSDR RFOne
    - **Frequency:** occasional
    - **Known fix:** Apply the stopWriter() patch from SatDump #1169. Crop the outer ~15% of the HydraSDR span or decimate. Use the HydraSDR SDR++ fork or SatDump's hydrasdr plugin. Correct the frequency offset in the demodulator.
    - **Fix sources:**
      - https://github.com/SatDump/SatDump/issues/1169
      - https://github.com/hydrasdr/rfone_host/issues/25
      - https://community.libre.space/t/airspy-mini-frequency-offset/8984
      - https://www.rtl-sdr.com/category/hydrasdr/
  12.
    - **Problem:** HF upconverter artefacts on V4/V4L: spur families from 28.8 MHz (shared TCXO and upconverter LO). Enabling direct sampling on a V4 gives nothing. A few users report about a 1-1.5 dB higher HF noise floor on the V4L than the V4.
    - **Affected products:** RTL-SDR Blog V4, V4L
    - **Frequency:** occasional
    - **Known fix:** Lower the LNA gain and set gain stages individually. Never enable direct sampling on the V4/V4L. Accept the spurs as a design artefact.
    - **Fix sources:**
      - https://www.reddit.com/r/RTLSDR/comments/1pfnvqa/rtlsdr_creates_fake_signals_that_spread_from_288/
      - https://www.rtl-sdr.com/V4L
      - https://www.reddit.com/r/RTLSDR/comments/1wm6ulc/buying_the_rtlsdr_blog_v4l/
  13.
    - **Problem:** Mechanical issues. Dongle width blocks adjacent USB ports on small hosts. Stress on USB connectors. One HydraSDR USB-C connector failed after about 10 insertions.
    - **Affected products:** RTL-SDR dongles on compact hosts; HydraSDR RFOne
    - **Frequency:** rare
    - **Known fix:** Use a short USB extension or a right-angle cable mounted inside the case with strain relief. Leave the SDR cable permanently connected.
    - **Fix sources:**
      - https://www.reddit.com/r/RTLSDR/comments/1w7tjn1/i_built_a_handheld_rtlsdr_around_the_m5stack_tab5/
      - https://github.com/hydrasdr/rfone_host/issues/8
- **Unresolved problems:**
  1.
    - **Problem:** No one has published a working (or failed) build of any USB SDR on the Radxa Dragon Q6A or another QCS6490 board on Linux.
    - **Evidence:** Radxa forum Discourse API searches for 'rtl-sdr', 'sdr', 'rtl2832', 'hackrf' and 'q6a usb' found no SDR posts; the only RTL post is a 2022 Rock Pi 4 thread. Reddit r/SBCs Q6A posts cover only OS images, NPU, cameras and gaming. Web searches combining 'Dragon Q6A' or 'QCS6490' with rtl-sdr, SatDump, SDR++ or SoapySDR returned nothing relevant.
    - **Why it matters for us:** Every known SBC SDR failure mode applies to us and is untested on this board: USB host-controller sample loss (Pi 4 needed a kernel fix), conducted PMIC noise (Pi 5 killed LRPT), and dongle heat. We would be first, so budget bench time with rtl_test -s 2400000 for lost samples, and check the noise floor with and without the Q6A and buck converters powered.
  2.
    - **Problem:** Q6A USB 2.0 topology and power are only partly documented.
    - **Evidence:** Radxa docs show a Terminus FE1.1s hub on bus 001 that also carries the onboard AIC8800D80 Wi-Fi/BT, plus a separate USB 2.0 root bus 002, but give no port-to-bus map. Radxa gives no per-port current limit. The UVC-camera thread got no answer.
    - **Why it matters for us:** The V4L draws 250-270 mA plus up to 180 mA of bias-tee load, and the GNSS and IMU may share the same hub. Wi-Fi traffic shares the hub's 480 Mbps. Over-current or brown-out would show up as dropped samples or USB resets mid-pass. Identify the hub-free port with lsusb -t, measure current with a USB meter, and preferably feed the dongle's or LNA's 5 V from the main buck.
  3.
    - **Problem:** No community report of the V4L with SatDump, GNU Radio or gr-satellites on Linux arm64, and no clean packaging path on Ubuntu.
    - **Evidence:** V4L community reports cover only Windows, Android and Pi FM-radio use; there are no V4L issues in the SatDump tracker. SatDump nightly ships only satdump_rpi64_latest_arm64.deb for arm64 and no Ubuntu arm64 build. SDR++ ships an ubuntu_noble_aarch64 .deb but links librtlsdr.so.2 from the distro's 2.0.1. Upstream source builds install .so.0, and purging ^librtlsdr also removes the apt gr-osmosdr, SoapyRTLSDR and gqrx packages.
    - **Why it matters for us:** On the Q6A's Ubuntu 24.04 the whole stack must be built from source (librtlsdr 2.0.3, SoapyRTLSDR, gr-osmosdr, SatDump, ideally SDR++) and protected from apt upgrades. Expect a day of build work; SatDump compiles slowly on ARM (use make -j3 to -j6 to avoid freezes). The alternative is a genuine V4 from a listed reseller, which works with stock 2.0.1 packages.
  4.
    - **Problem:** The V4L's real-world overload behaviour near strong transmitters with a broadband LNA is unmeasured by the community.
    - **Evidence:** Only vendor two-tone data exists. Users say it is 'slightly more prone to overload' and one gain step lower, but nobody has tested it with an SPF5189Z or QPL9547 LNA near FM or DVB-T masts.
    - **Why it matters for us:** A handheld used in Ukrainian cities sits near FM, DVB-T2 and possibly military or emergency VHF/UHF transmitters. Without the V4's triplexer and notch, a broadband masthead LNA can desensitise 137, 145 and 435 MHz reception. Plan band-specific filtered LNAs, or a switchable filter bank, for the V4L input.
  5.
    - **Problem:** V4L long-term reliability and supply are unknown.
    - **Evidence:** Launched Aug 2026; the R828S is out of production and stock is expected to last about one year. A USB-C 'V4Lc' is promised but not shipped. The V5 is in early scoping. The V3c exists.
    - **Why it matters for us:** No field data on thermal drift or failure in a closed 3D-printed case. A replacement may be unobtainable in 2027, so buy a spare. The USB-A connector needs strain relief in a handheld.
  6.
    - **Problem:** The RTL-SDR 'stuck noisy until replugged' failure has no known root cause.
    - **Evidence:** PE0SAT, Feb 2026: 'the only way to correct this behavior is remove the RTL-SDR and reinsert... still have no idea what the root cause is'.
    - **Why it matters for us:** In the field, a silent degradation can ruin a once-a-day pass. We should add a software USB power-cycle or rebind (unbind/bind via sysfs; uhubctl support on the Q6A's FE1.1s hub is unverified) and an automatic noise-floor sanity check before each pass.
  7.
    - **Problem:** Running SatDump on two sources at once (V4L plus LimeSDR Micro via LimeSuiteNG) is undocumented.
    - **Evidence:** SatDump #1177 (open): satdump_sdr_server holds all devices. Two-RTL setups work with source_id, but no report covers mixed RTL plus Lime. It is unverified whether SatDump's limesdr plugin supports the LimeSDR Micro or LimeSuiteNG yet; Micro support is in the limesdr-micro dev branch.
    - **Why it matters for us:** Simultaneous LRPT (V4L) plus HRPT (Lime) is the main justification for keeping a second SDR. Plan two separate SatDump processes, each bound to its device by serial or source_id, and verify CPU load on the Q6A A78 cores.
  8.
    - **Problem:** LimeSDR Micro performance at 137-146 MHz is unmeasured.
    - **Evidence:** Lime docs list the RX lower end as 300 MHz; staff say the frequency bands indicate where matching is optimised, not gaps. A LimeSDR Mini 2.2 NOAA comparison showed interference lines that an RSPdx did not, unresolved (2023).
    - **Why it matters for us:** If the Lime is weak at VHF, the V4L becomes the primary 137 and 145.8 MHz receiver, not just a helper. That raises the importance of its front-end filtering and clean power.
  9.
    - **Problem:** HydraSDR and Airspy alternatives have open software or calibration gaps on Linux.
    - **Evidence:** HydraSDR #25 was closed without a documented fix, and SoapyHydraSDR bandwidth queries are unimplemented. SatDump's Airspy Stop deadlock PR #1172 is unmerged. SoapyAirspy has no ppm correction; only a Windows calibration tool exists.
    - **Why it matters for us:** If we upgrade to a 12-bit dongle, which the evidence supports for weak CubeSats, the Q6A-only workflow needs these worked around: crop the span or decimate, apply the deadlock patch, and correct frequency in the demodulator.
  10.
    - **Problem:** Landed price and shipping to Ukraine for the official V4L are unverified.
    - **Evidence:** AliExpress had an EU-wide block that was fixed for the V4L listing (Poland/Italy reports, Sep 2026). Prom.ua shows only 'V4'-labelled third-party units at 3,000-8,531 UAH. DigiKey shipping of HydraSDR to Ukraine was not checked.
    - **Why it matters for us:** Budget and lead time; buying locally carries high counterfeit risk.
- **Communities checked:**
  - Reddit r/RTLSDR, r/amateursatellites, r/sdr, r/SBCs, read through the safereddit.com Redlib mirror; www.reddit.com and old.reddit.com were unreachable by WebFetch, r/radxa returned 404 on the mirror, and several other Redlib mirrors returned 403, 429 or 502
  - SatNOGS community forum (community.libre.space), via Discourse JSON API search and topic reads
  - Radxa forum (forum.radxa.com), via Discourse JSON API; the HTML search page is JS-only
  - MyriadRF / Lime discourse (discourse.myriadrf.org), via Discourse API
  - GitHub issues: SatDump/SatDump, AlexandreRouma/SDRPlusPlus, rtlsdrblog/rtl-sdr-blog, osmocom/rtl-sdr (commit and tags), hydrasdr/rfone_host, pothosware/SoapySDRPlay3, airspy/airspyone_host
  - GitHub release asset lists for SatDump nightly and SDR++ nightly
  - RTL-SDR.com articles and reader comments: V4L launch, V4L guide, V4 end-of-line, GENUINE page, HydraSDR review category, R820T L-band heat article
  - FlightAware discussions forum (SDRplay RSP1B on Pi 5)
  - Radxa docs (Q6A USB page)
  - packages.ubuntu.com (rtl-sdr versions per release)
  - Prom.ua (Ukrainian marketplace listings)
  - sdrstore.eu V4L setup guide; vu3dxr.in HydraSDR article
  - WebSearch snippets only, pages not opened: SDRplay community forum, RadioReference forum (Nooelec v5 drift/USB reports), Hackster/heise news
  - Not reached or nothing found: EEVblog, groups.io, BATC, AMSAT-BB/UK/DL, mikrocontroller.net, Funkamateur, Armbian forum, Ubuntu Discourse, Qualcomm developer forums, CNX Software comments, StackExchange, SatDump Discord, YouTube; a Ukrainian-language search returned only foreign retailer pages
- **Recommendation impact:** Community evidence supports the researcher's verdict: KEEP a second SDR and REPLACE the EOL V4 with the RTL-SDR Blog V4L. It also adds conditions.
  
  1. The V4L works well once the 2026 driver is in place; users rate it slightly more sensitive and slightly more overload-prone than the V4. The 'deaf, only DC spike' failure is the number-one pitfall. On the Q6A, Ubuntu 24.04 (2.0.1) and 26.04 (2.0.2) packages do NOT support the V4L, so plan a full source build: osmocom rtl-sdr 2.0.3 or master, SoapyRTLSDR, gr-osmosdr, SatDump, ideally SDR++. Fix the .so.2 vs .so.0 SONAME mismatch and hold the packages against apt. Purging ^librtlsdr removes distro gr-osmosdr, Soapy and gqrx.
  
  2. If a genuine V4 is still sold by a listed official reseller in the EU (the UK reseller TechnoFix still had stock at GBP 46 in Oct 2026), it is a valid alternative. It has better strong-signal immunity and works with stock Ubuntu 24.04 packages. Never buy a 'V4' from Prom.ua or third-party AliExpress or eBay sellers: all Ukrainian listings found were unbranded or 'HTOOL' 'V4' boards at $72-205.
  
  3. Design changes for this component:
  - Put band-specific filtered LNAs (137 MHz BPF+LNA, 435 MHz SAW LNA) ahead of the V4L instead of a broadband SPF5189Z. If a broadband LNA is kept, place the FM bandstop before it.
  - Treat conducted noise as a first-class risk: short shielded USB extension with ferrites, SDR case bonded to the USB shield and antenna ground, and dongle or bias-tee 5 V fed from a clean dedicated regulator rather than the Q6A port. Pi 5 and Pi 4 builds failed on exactly this, and distance did not help.
  - Use the Q6A USB port that is not behind the FE1.1s hub shared with Wi-Fi, if one exists (verify with lsusb -t).
  - Keep the thermal pad and airflow, and do not count on the V4L for 1.7 GHz.
  - Set unique serials with rtl_eeprom and run separate SatDump processes per SDR (source_id). A single satdump_sdr_server cannot share devices (#1177).
  - Add a USB rebind or power-cycle watchdog for the 'stuck noisy' RTL state.
  
  4. Upgrade path: the strongest community evidence favours a 12-bit dongle for weak 70 cm CubeSats. The HydraSDR RFOne (~$194) has portable hand-held LRPT and HRPT field reports and replaced RTLs in a top SatNOGS operator's production stations. It covers 24-1800 MHz, but needs SatDump's hydrasdr plugin or the SDR++ fork, and band-edge aliasing must be cropped. The Airspy Mini ($79-99) is the cheaper 12-bit option but lacks ppm correction on Linux and has an unmerged SatDump Stop-deadlock fix.
  
  5. Downgrade SDRplay RSP1B / RSPdx-R2 for this build: the closed API service on ARM needs manual restarts after boot or replug and fails via Soapy in some Pi 5 setups, on top of its size and weight. The Nooelec SMArt v5 offers no advantage over the V3/V4L. The MSI.SDR clone stays excluded.
  
  6. Because no Q6A + SDR report exists anywhere, schedule early bench validation before the LimeSDR arrives: rtl_test sample-loss check, noise floor with the Q6A and bucks on and off, USB current, and dongle temperature in the case. Buy two V4Ls now, since the R828S stock is expected to last about one year.

## Власні виправлення (`fixes`)

_Агент цього етапу ще працює (run `wf_eb446444-464`)._

