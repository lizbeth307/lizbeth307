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

_Run `wf_feb0e95a-cfc`_

- **Subsystem:** narrowband_sdr (RTL-SDR Blog V4L x2 + spare: RTL-A VHF/UHF, RTL-B L-band/LNB IF, spare on LAB USB)
- **Findings:**
  1.
    - **Claim in stack:** Part/model: RTL-SDR Blog V4L (R828S + RTL2832U, 1 ppm TCXO), 3 units (RTL-A, RTL-B, spare); 500 kHz-1.766 GHz; 2.56 Msps stable; 250-270 mA (~1.3 W); bias tee 4.5 V/180 mA; RX-only
    - **Finding:** Datasheet V1.0 (PDF created 2026-08-11) lists: R828S, RTL2832U 8-bit, 500 kHz-1.766 GHz, '2.56 MHz stable (up to 3.2 MHz with drops)', 250-270 mA, HF upconverter with 28.8 MHz LO, 1 PPM TCXO, bias tee 4.5 V/180 mA (software switchable), aluminium case with thermal pad, diplexer front end, 'Transmit Capability: None'. The 1.3 W figure is derived: 5 V x 0.25-0.27 A = 1.25-1.35 W. The hardware cannot transmit, so the RX-only rule is met. The datasheet has a typo ('better sensitivity than the V4L' should read V4).
    - **Verdict:** confirmed
    - **Action:** Keep the part and the specs as written.
    - **Impact:** Basis of the whole VHF/UHF/L-band receive chain.
    - **Sources:**
      - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-v4l-lite-r828s-rtl2832u-1ppm-tcxo-sma-software-defined-radio-dongle-only/
  2.
    - **Claim in stack:** Price $37.95 each, $113.85 for 3; '455 in stock' at the official store; R828S out of production, so buy now
    - **Finding:** Live product page on 2026-10-18: 'USD $37.95', '455 in stock'. A search-engine snapshot from an earlier date showed '105 in stock', so the count moves between batches. The launch post says the V4L is 'a limited edition product', relies on 'a large stockpile of a chip that is no longer in production', and the stockpile should 'last about one year' (from about Aug 2026). First batches ship only from the China warehouse. The V4 is EOL: the R828D stockpile is gone and the last chips were faulty. A V5 is in early design, with no news expected until 2027.
    - **Verdict:** confirmed
    - **Action:** Order all 3 now. Totals exclude shipping, VAT and US tariffs.
    - **Impact:** After about mid/late 2027 the only like-for-like replacement is the V3, until a V5 exists.
    - **Sources:**
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-v4l-lite-r828s-rtl2832u-1ppm-tcxo-sma-software-defined-radio-dongle-only/
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4-end-of-line/
  3.
    - **Claim in stack:** Channels: official store (not EU); EU buyers use official eBay or AliExpress 4523039; US buyers should prefer 'RTL-SDR Blog on Amazon USA' (customs section, line 1132)
    - **Finding:** The store does not ship to the EU (VAT compliance) and excludes RU/BY/IR/KP. The official channels are eBay 'rtl-sdr-blog' and AliExpress 'RTLSDRBlog Store' No. 4523039 (alt. No. 1101427871). For the V4L, the store page says 'Amazon USA warehouse not stocked yet'; the kit is 'expected in 2-3 months'. I could not verify the eBay and AliExpress V4L prices (eBay showed a bot wall; the AliExpress page came back empty), so the earlier '$34.20 on AliExpress' is unverified. sdrstore.eu asks EUR 83.44 and is out of stock.
    - **Verdict:** corrected
    - **Action:** Line 1132: the V4L is not on Amazon USA yet. US buyers order from the store (China warehouse) and check tariff and de minimis rules. EU buyers keep using eBay or AliExpress 4523039/1101427871. Recheck Amazon US before ordering.
    - **Impact:** Changes US lead time and duties only.
    - **Sources:**
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://www.rtl-sdr.com/GENUINE
      - https://www.sdrstore.eu/software-defined-radio/instruments/rtl-sdr/rtl-sdr-blog-v4l-lite-r828s-sdr-dongle-500khz1-766ghz/
  4.
    - **Claim in stack:** Counterfeit risk high: official channels only; no blue cases, no 'Pro', no 'V4' copies; the driver prints 'RTL-SDR Blog V4 Lite Detected' as the W1-2 check
    - **Finding:** The official guidance confirms this. Blue or green cases, square silver 4-screw cases and 'Pro' listings are fakes. Cloned black cases have horizontal side screws; genuine ones have diagonal screws. V4 fakes are a V3-clone board in a copied case. Detection in osmocom is purely string-based: strcmp on the EEPROM strings 'RTLSDRBlog'/'Blog V4L', after the R828S answers as an R820T. A clone with copied EEPROM strings would therefore also print 'V4 Lite Detected'.
    - **Verdict:** confirmed
    - **Action:** Add an incoming genuineness test. With direct sampling OFF, a genuine V4L hears HF broadcast or time signals at 5-15 MHz through its upconverter; a V3-clone board cannot. Also check the screw orientation.
    - **Impact:** Stops a fake unit from entering the build.
    - **Sources:**
      - https://www.rtl-sdr.com/GENUINE
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4-end-of-line/
      - https://github.com/osmocom/rtl-sdr/commit/0204c9cfb1c5ff7bd64f466ce5b8fe53b40a636a
  5.
    - **Claim in stack:** Gain/overload: the V4L desense threshold is -20...-40 dBm at 300-1600 MHz (95 MHz blocker), so the filter goes first on VHF (C10) and a 15/20 dB attenuator on the LNB IF; RTL gain about 10-25 dB behind the SAWbird+ NOAA
    - **Finding:** Read from the datasheet two-tone chart for a 95 MHz blocker. V3 and V4L are identical: -12 dBm at 50-160 MHz, -20 at 300, -24 at 400-600, -27 at 800, -28 at 1000, -30 at 1200 and -40 dBm at 1600 MHz. The V4 is -7 dBm at 50-160 MHz and +8 dBm at 300-1400 MHz. At the 739.5 MHz LNB IF the V4L threshold is about -26 dBm. The R828S has no open_d pin, so there is no FM notch. MDS from the chart (500 Hz): about -140.7 dBm at 100-550 MHz, about -133 at 1.0-1.5 GHz, about -130 at 1.7 GHz. Implied NF (model, 3 dB MDS): about 3.3 dB at VHF/UHF and about 14 dB at 1.7 GHz, which a 30-40 dB LNA in front makes negligible. Comparing a single-CW-blocker chart with broadband LNB noise is a model, not a measurement.
    - **Verdict:** confirmed
    - **Action:** Keep C10 and the LNB attenuator. Record the -12 dBm figure for the 137 MHz path in the gain plan.
    - **Impact:** Confirms the filter-first topology.
    - **Sources:**
      - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
  6.
    - **Claim in stack:** Spare V4L on LAB USB with bare whiskers for radiosondes (17.7 cm, 400-406 MHz) and ADS-B (6.5 cm), with no filter named in that path
    - **Finding:** The V4L has no FM/AM/DAB notches and no VHF/UHF triplexer. With a 95 MHz blocker, 3 dB desense starts at about -24 dBm at 400 MHz and about -29 dBm near 1090 MHz. A handheld whip near a high-power FM site can reach those levels. Neither the spare-on-LAB-USB rows nor the C10 decision (filter first on VHF-137 and on P8 WIDE only) put an FM filter in this path.
    - **Verdict:** new_risk
    - **Action:** Add an inline FM band-stop to the spare V4L kit: the RTL-SDR Blog FM band-stop ($16.95, in stock) or Flamingo+ #2. The spare's tee is off, so the band-stop's missing DC rating does not matter.
    - **Impact:** Moderate near FM transmitters, otherwise low.
    - **Sources:**
      - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
      - https://www.rtl-sdr.com/store/
  7.
    - **Claim in stack:** C11 driver: rebuild noble 2.0.1-2build1 with commits 0204c9c (R828S) and 65f0658 (USB hang), fix the zerocopy typo, keep SONAME .so.2 with apt-mark hold; blacklist dvb_usb_rtl28xxu; W1-2 must show 'RTL-SDR Blog V4 Lite Detected'
    - **Finding:** Both commits exist in osmocom/rtl-sdr: 0204c9c (2026-05-01, 'Add RTL-SDR Blog V4L Support') and 65f0658 (2026-01-10, 'Fix application hang on USB transfer errors'). I cherry-picked both onto tag v2.0.1 without conflicts and built librtlsdr.so.2.0.1 with SONAME librtlsdr.so.2 (amd64 only; arm64 not built). The exact log string is 'RTL-SDR Blog V4 Lite Detected', printed after 'Found Rafael Micro R820T tuner'. The zerocopy typo is real: noble's debian/rules (2.0.1-2build1 tarball) and Debian 2.0.3-1 both pass -DENABLE_ZEROCOPY=$DEB_ZEROCOPY_OPTION. Make expands that to 'EB_ZEROCOPY_OPTION' (I reproduced it), which CMake treats as true. Keeping .so.2 is required: the OpenWebRX+ noble repo packages rtl-connector 0.6.5, rtl-433 25.12-1, dump1090-fa-minimal 8.2-1, acarsdec, dumpvdl2 and nrsc5 all Depend on librtlsdr2 (>= 2.0.1). The packaging already ships the dvb_usb_rtl28xxu/rtl2832/e4000 blacklist and plugdev udev rules.
    - **Verdict:** confirmed
    - **Action:** Keep C11, with the bias-patch correction in the next finding. Use $(DEB_ZEROCOPY_OPTION), or pass OFF explicitly. Run the arm64 build in W1-2.
    - **Impact:** The core driver path works; an upstream librtlsdr0 install would remove the OpenWebRX+/rtl-433/dump1090 packages.
    - **Sources:**
      - https://github.com/osmocom/rtl-sdr/commit/0204c9cfb1c5ff7bd64f466ce5b8fe53b40a636a
      - https://github.com/osmocom/rtl-sdr/commit/65f06585ea46160cd2d7bee8b3f641c14771c2ee
      - http://archive.ubuntu.com/ubuntu/pool/universe/r/rtl-sdr/rtl-sdr_2.0.1-2build1.debian.tar.xz
      - https://sources.debian.org/data/main/r/rtl-sdr/2.0.3-1/debian/rules
      - https://luarvique.github.io/ppa/noble/Packages
  8.
    - **Claim in stack:** C11 bias-tee token: 'rtlsdr_set_bias_tee() and rtlsdr_set_bias_tee_gpio() refuse "on" unless LAB_BIAS_OK equals the device serial'
    - **Finding:** As written, this breaks VHF/UHF on the V4L, and on the V4. On every HF to VHF/UHF band change, r82xx_set_freq() calls rtlsdr_set_bias_tee_gpio(priv->rtl_dev, 5, !cable_1_in), i.e. GPIO 5 'on'; GPIO 5 is the upconverter switch ('newer batches'). The bias tee itself is GPIO 0. If that call returns <0, the code jumps to err after priv->input = band has already been set. The input-select registers are never written, and later tunes in the same band skip the switch. Result: 'r82xx_set_freq: failed' and a receiver that is deaf above 28.8 MHz. Also, the core V4Ls sit behind DC blocks (C9/line 692), so their tee cannot reach an antenna anyway; the token really matters only for the spare.
    - **Verdict:** corrected
    - **Action:** Gate only gpio==0 (rtlsdr_set_bias_tee and rtlsdr_set_bias_tee_gpio with gpio 0) and pass every other GPIO through unchanged. CI test with LAB_BIAS_OK unset: tune 137.9 -> 1700 -> 7 -> 437 MHz, require no 'r82xx_set_freq: failed', require signal at 437 MHz, require that a bias-on request is refused.
    - **Impact:** High. The patch as specified would make both core receivers deaf on VHF/UHF/L-band.
    - **Sources:**
      - https://github.com/osmocom/rtl-sdr/blob/v2.0.3/src/tuner_r82xx.c
      - https://github.com/osmocom/rtl-sdr/blob/v2.0.3/src/librtlsdr.c
      - https://github.com/osmocom/rtl-sdr/commit/0204c9cfb1c5ff7bd64f466ce5b8fe53b40a636a
  9.
    - **Claim in stack:** C11 base version: noble 2.0.1 plus two cherry-picks
    - **Finding:** osmocom v2.0.3 was released 2026-08-12 and contains 0204c9c, 65f0658, the r82xx tuning-speed commits (2acb75c, 0b64f07, f5978e8) and the gain-rounding fix d81ef9a. Reverting 7ebcb04 ('set SOVERSION back to 0') makes 2.0.3 build librtlsdr.so.2; I built it and it exports the same 37 rtlsdr_* symbols as the patched 2.0.1, with no header/API change between 2.0.1 and 2.0.3. 0204c9c was written on top of the fast-retune code. 2.0.3 is therefore the combination upstream and RTL-SDR Blog actually ship; 2.0.1 plus cherry-picks is an untested mix. The fast retune also helps labrx sweeps.
    - **Verdict:** new_option
    - **Action:** Prefer building librtlsdr2 '2.0.3-0+lab1' from upstream v2.0.3, with the SOVERSION revert, the noble debian/ packaging, zerocopy OFF and the corrected GPIO0-only token patch. Keep 2.0.1 plus cherry-picks as the fallback.
    - **Impact:** Less custom patching, faster sweeps, a configuration upstream has tested.
    - **Sources:**
      - https://github.com/osmocom/rtl-sdr/releases/tag/v2.0.3
      - https://github.com/osmocom/rtl-sdr/commit/7ebcb041f2ce887ef4d1a64607558889a86ff169
      - https://sources.debian.org/data/main/r/rtl-sdr/2.0.3-1/debian/changelog
  10.
    - **Claim in stack:** EEPROM bias default off; never 'rtl_eeprom -b 1'
    - **Finding:** osmocom rtl_eeprom has no -b option, and the osmocom library never reads an EEPROM force-bias flag. Only the rtlsdrblog fork (and the Windows DLLs built from it) does: at open it forces bias ON when EEPROM byte 7 bit 0x02 is 0. That is the same IR-endpoint bit that osmocom's 'rtl_eeprom -i 0' clears. The fork also maps rtlsdr_set_offset_tuning() to the bias tee; osmocom does not. 'rtl_eeprom -g ...' overwrites the 'RTLSDRBlog'/'Blog V4L' strings, after which the V4L gets no signal.
    - **Verdict:** corrected
    - **Action:** Self-test reads the EEPROM and asserts the IR bit = 1 (no forced bias) and intact strings. Forbid rtl_eeprom -g, -w and -i 0. Restore with rtl_eeprom -m "RTLSDRBlog" -p "Blog V4L". Never ship the rtlsdrblog fork on the device.
    - **Impact:** Closes a bias path that the token does not cover (blog-fork drivers, Windows host).
    - **Sources:**
      - https://github.com/osmocom/rtl-sdr/blob/v2.0.3/src/rtl_eeprom.c
      - https://github.com/rtlsdrblog/rtl-sdr-blog/blob/master/src/librtlsdr.c
      - https://www.rtl-sdr.com/V4L
  11.
    - **Claim in stack:** 'Unique serial numbers in EEPROM' (row 183, C21); udev /dev/lab/<name> by serial
    - **Finding:** Unique serials are not a factory property. Users report that RTL-SDR Blog V4 units ship as serial 00000001, and the RTL-SDR Blog pages say nothing about serials. SatDump opens devices with rtlsdr_get_index_by_serial(), so two dongles with the same serial collide.
    - **Verdict:** corrected
    - **Action:** Programming serials is an assembly step. With one dongle attached: rtl_eeprom -r backup.bin, then rtl_eeprom -s LAB-RTLA (and so on), then replug and verify. Do it before any 2-dongle test.
    - **Impact:** Without it, udev naming and SatDump device selection fail.
    - **Sources:**
      - https://forum.sdr-radio.com/viewtopic.php?p=11166
      - https://discussions.flightaware.com/t/how-to-change-serial-number-of-dongle-adsb-1090-uat-978-dongles-plugged-into-same-pi/31980
      - https://github.com/SatDump/SatDump/blob/master/plugins/sdr_sources/rtlsdr_sdr_support/rtlsdr_dev.cpp
  12.
    - **Claim in stack:** Software compatibility: SoapyRTLSDR 0.3.3 (noble) and SDRangel/OpenWebRX+/SatDump/SDR++ work with the V4L once librtlsdr is updated; budget HF = second V4L in upconverter mode
    - **Finding:** SoapyRTLSDR 0.3.3 (noble 0.3.3-1build1) and the new upstream 0.3.4 (tagged 2026-10-10, build changes only) advertise 0-1764 MHz only for tuner R828D plus product 'Blog V4'. The V4L reports tuner R820T and product 'Blog V4L', so Soapy apps get a 24 MHz minimum. SDRangel's native RTL-SDR plugin (master 2026-10-17) does the same (m_frequencyHighRangeMin = 0 only for 'Blog V4'). SDR++ does not clamp, and labrx calls librtlsdr directly. SatDump links the system librtlsdr. On the RTL-SDR Blog V4L guide, the 'not supported' entries for SDR++ and SDRangel are for Android.
    - **Verdict:** new_risk
    - **Action:** If the budget V4L-HF path is ever used, add one-line patches matching 'Blog V4L' in SoapyRTLSDR and SDRangel, or use SDR++/labrx for V4L HF. Force direct_samp=0 in every config.
    - **Impact:** Low for the main build (HF is on the HF+); blocks HF in Soapy/SDRangel on the V4L.
    - **Sources:**
      - https://github.com/pothosware/SoapyRTLSDR/blob/master/Settings.cpp
      - https://launchpad.net/ubuntu/+source/soapyrtlsdr
      - https://github.com/f4exb/sdrangel/blob/master/plugins/samplesource/rtlsdr/rtlsdrinput.cpp
      - https://www.rtl-sdr.com/V4L
  13.
    - **Claim in stack:** HF mode: V4L HF via the 28.8 MHz upconverter; budget HF = second V4L 'without LW'; V4L is not the main HF receiver
    - **Finding:** The driver adds 28.8 MHz automatically below 28.8 MHz and switches the input. Since 0204c9c it also bypasses the tracking filter on HF. Direct sampling yields nothing on V4/V4L. The 500 kHz lower limit means no LW/LF (DCF77, MSF, WWVB, JJY, TDF stay on the HF+). Chart MDS is about -133 to -135 dBm (500 Hz) at 3-28 MHz, about -129 dBm at 1 MHz, with a spike near 28.8 MHz.
    - **Verdict:** confirmed
    - **Action:** No change. Keep the HF+ as the HF receiver.
    - **Impact:** Confirms C21 and the budget note.
    - **Sources:**
      - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
      - https://github.com/osmocom/rtl-sdr/commit/0204c9cfb1c5ff7bd64f466ce5b8fe53b40a636a
      - https://www.rtl-sdr.com/V4L
  14.
    - **Claim in stack:** Cooling: V4L inside the closed RF bay on 15 cm shielded extensions; aluminium case with thermal pad; RTL-B serves Meteor HRPT 1700, Metop 1701.3 and AWS 1707 MHz
    - **Finding:** The datasheet confirms the thermal pad to the aluminium enclosure and 'slightly less heat' than the V3; no operating temperature is published. R820T-family tuners lose PLL lock at L-band as the chip heats, with unit-to-unit variation (rtl-sdr.com measurements on R820T/R820T2 above 1.4-1.5 GHz). The R828S answers as an R820T. Here it runs within 59-66 MHz of its 1.766 GHz ceiling, beside a second 1.3 W dongle in a closed bay. Not measured for the R828S.
    - **Verdict:** new_risk
    - **Action:** Add a W1-2/thermal gate: 60 min at 1707 MHz and 1700 MHz, closed case, worst-case ambient; grep for '[R82XX] PLL not locked!' and watch for dropouts. Bond the dongle cases to the plate or airflow with a thermal pad.
    - **Impact:** Could cost HRPT/AHRPT passes in summer heat.
    - **Sources:**
      - https://www.rtl-sdr.com/?p=9747
      - https://rtl-sdr.com/beta-testing-a-modified-rtl-sdr-driver-for-l-band-heat-issues/
      - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
  15.
    - **Claim in stack:** USB: 5.12 MB/s per V4L at 2.56 Msps (18.4 GB/h); RTL-A on the blue USB 3.1 port running as USB 2 HS; FE1.1s tree at 13.3 MB/s or less
    - **Finding:** The arithmetic holds: 2.56 Msps x 2 B = 5.12 MB/s = 18.4 GB/h. HF+ at 768 ksps x 4 B = 3.07 MB/s. Current is 250-270 mA plus up to 180 mA of tee, under the 500 mA USB 2 limit. Radxa documents 3 black USB 2.0 ports plus 1 blue USB 3.1 port 'OTG and HOST' and a 30.8/25.8 MB/s flash-drive dd result (port not stated). The blue port's default role (host or device) is not documented.
    - **Verdict:** unverified
    - **Action:** Keep the existing W1-2 gate: lsusb -t shows the V4L at 480M on the blue port, plus the 15-min rtl_test at 2.4/2.56/2.88 Msps. Force host role in the DT if needed.
    - **Impact:** Low. A gate already exists.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/usb
      - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
  16.
    - **Claim in stack:** Own spurs: 1699.2 MHz (28.8 x 59) in Meteor HRPT; 403.2 MHz ignored by auto_rx; 144.000/432.000 MHz harmonics
    - **Finding:** Calculation: 28.8 x 59 = 1699.2 MHz, 0.8 MHz from the 1700 MHz HRPT centre. x14 = 403.2, x5 = 144.0, x15 = 432.0. No 28.8 MHz harmonic falls in LRPT 137.1-137.9, AIS, ADS-B 1088-1092, LNB IF 738.5-740.5, Inmarsat-C 1537-1545, H1 1419-1422, L1, Metop 1699.55-1703.05 or AWS 1705.8-1708.2 MHz. The 1704.0 MHz spur is not a 28.8 MHz harmonic; it belongs to another subsystem.
    - **Verdict:** confirmed
    - **Action:** Keep the spur-mask entries.
    - **Impact:** None.
    - **Sources:**
      - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
  17.
    - **Claim in stack:** Metop/AWS gate (a): 15 min rtl_test at 2.88 Msps; SatDump #727 cited for the V4 at 2.88 Msps
    - **Finding:** The datasheet's 2.56 stable / 3.2 with drops makes 2.88 Msps a legitimate gate value. SatDump #727 ('MetOp NOSYNC', closed 2024-06-13) is a V4 report: the user fixed it with 2.88 plus DC block plus AGC, and a maintainer called RTL defaults 'on the edge'. It is not V4L evidence.
    - **Verdict:** confirmed
    - **Action:** Keep the gate. Label #727 as V4 evidence.
    - **Impact:** None.
    - **Sources:**
      - https://github.com/SatDump/SatDump/issues/727
  18.
    - **Claim in stack:** Alternatives (note only): V3 as budget; Airspy Mini as the >2.56 Msps fallback for Metop/AWS
    - **Finding:** V3 R860: $34.95-39.95, in stock at Amazon USA and China (USB-A and USB-C), works with stock noble librtlsdr2. Per the V4L chart it is about 2 dB worse at 137 MHz, about 2-3 dB worse at 400-600 MHz and about 3 dB worse at 1.7 GHz, has the same two-tone behaviour, and its direct-sampling HF is poor (about -115 to -122 dBm). Airspy Mini and Airspy R2 official pages both state '24-1700 MHz native RX range', so Metop 1701.3 and AWS 1707 MHz are above spec (whether they work in practice was not checked). A V4L USB-C version is mentioned only in a reply on the blog launch post (unverified). V5 not before 2027.
    - **Verdict:** new_risk
    - **Action:** Keep the V3 as the budget/after-stockpile replacement. Mark the Airspy Mini AHRPT fallback as out of spec and confirm with an owner report before buying.
    - **Impact:** Affects only the conditional Airspy purchase.
    - **Sources:**
      - https://www.rtl-sdr.com/store/
      - https://airspy.com/airspy-mini/
      - https://airspy.com/airspy-r2/
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
- **Current status oct 2026:** Status on 2026-10-18.
  
  Hardware:
  - RTL-SDR Blog V4L is on sale at USD 37.95, with 455 in stock at the official store (China warehouse). It is not yet at Amazon USA; the kit is expected in 2-3 months.
  - It is officially a limited edition. The R828S stockpile is expected to last about one year from launch (Aug 2026).
  - The datasheet is V1.0 (2026-08-11). No new revision, EOL notice or USB-C V4L has been announced (USB-C appears only in a reply on the blog launch post).
  - V4 is EOL. A V5 is not expected before 2027. The V3 stays in production at $34.95-39.95.
  
  Drivers and software:
  - osmocom rtl-sdr v2.0.3 was released 2026-08-12. It is the first release with V4L support (0204c9c) and the USB-hang fix (65f0658). There are no post-release commits and I found no 2.0.3 bug reports.
  - Debian 2.0.3-1 (librtlsdr0) entered unstable 2026-09-06 and testing 2026-09-12. Ubuntu 26.10 ships 2.0.3-1. Ubuntu 26.04 (2.0.2-2build1) and noble 24.04 (2.0.1-2build1) have no V4L support, so the Q6A still needs the lab rebuild. The zerocopy typo persists in noble and Debian 2.0.3-1.
  - The rtlsdrblog fork added the V4L in March 2026 (tag V1.4.0); Windows DLL V1.4.0 and ExtIO v2026-08-10.
  - SoapyRTLSDR 0.3.4 was tagged 2026-10-10 (noble has 0.3.3-1build1). Neither version recognises 'Blog V4L' for the HF range, and neither does SDRangel master (2026-10-17).
  - OpenWebRX+ noble packages (openwebrx 1.2.126, rtl-connector 0.6.5) depend on librtlsdr2 (>= 2.0.1).
  
  Sourcing: EU buyers use eBay 'rtl-sdr-blog' or AliExpress 4523039/1101427871, since the store does not ship to the EU. Live eBay and AliExpress V4L prices could not be verified.
- **Notes:** How this was checked:
  - I read the V4L datasheet PDF, including its MDS and two-tone charts (rendered to images and read at chart resolution, so values are about ±0.5 dB), and fetched the live store, user-guide, launch, EOL and genuine-unit pages.
  - I cloned osmocom/rtl-sdr (GitHub and gitea), rtlsdrblog/rtl-sdr-blog, SoapyRTLSDR, and sparse checkouts of SDRangel, SDR++ and SatDump.
  - I pulled the noble 2.0.1-2build1 debian tarball from archive.ubuntu.com, the Debian 2.0.3-1 packaging and the OpenWebRX+ noble Packages index.
  - I built both librtlsdr variants on amd64; arm64 was not built. No hardware tests were done.
  - Working copies are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/nb_git and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/nb_dl.
  
  Most important result: the bias-tee token patch in C11, as written (refuse 'on' in rtlsdr_set_bias_tee_gpio for any GPIO), would make both core V4Ls deaf above 28.8 MHz, because the tuner driver uses GPIO 5 through that same function as the upconverter band switch. Gate GPIO 0 only.
  
  Cross-subsystem observation (software): the OpenWebRX+ 'openwebrx' package Recommends wsjtx, js8call and direwolf, which are banned TX-capable tools. apt installs Recommends by default, so install it with --no-install-recommends and keep the CI ban list.
  
  Unverified items:
  - eBay and AliExpress V4L prices.
  - The default role of the Q6A blue port.
  - R828S PLL lock behaviour at 1.70-1.707 GHz when hot.
  - Airspy Mini or R2 operation above their 1700 MHz spec.
  - The V4L USB-C version.
  - Factory serials on the V4L specifically (00000001 is reported for V4 units).
  
  Model numbers, labelled as models in the findings: the implied NF from MDS, the about -26 dBm threshold at 739.5 MHz (interpolated), and power derived from the datasheet current.

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

_Run `wf_eb446444-464`_

- **Component:** Second / narrowband SDR: RTL-SDR Blog V4L on the Radxa Dragon Q6A, alongside the LimeSDR Micro
- **Fixes:**
  1.
    - **Problem:** Nobody has published a working or failed USB-SDR build on the Dragon Q6A or any QCS6490 board. Sample loss, conducted noise and heat on this board are all untested.
    - **Proposed fix:** Run a one-evening bench acceptance test before trusting the board in the field. Use the hub-free blue USB 3.1 port (see the USB topology fix) and the patched librtlsdr2 (see the packaging fix). The test has fixed pass/fail criteria for enumeration, sample loss under full system load, zero-copy state, conducted/radiated noise and a real decode. Note on the stock library: Ubuntu's librtlsdr2 2.0.1-2build1 has zero-copy (usbfs mmap) buffers enabled on arm64, even though Debian bug #1041701 meant to disable it. The cause is a Makefile typo in debian/rules: -DENABLE_ZEROCOPY=$DEB_ZEROCOPY_OPTION expands to the literal string 'EB_ZEROCOPY_OPTION', which CMake treats as TRUE. I reproduced this on Ubuntu 24.04: the compile line shows -DENABLE_ZEROCOPY=1. The same typo is still in Debian 2.0.3-1. That bug caused silent all-zero samples and lost bytes on another arm64 board (Odroid N2+), so treat it as a prime suspect for sample loss on the Q6A's SMMU-backed xHCI.
    - **Steps:**
      - Plug the V4L into the BLUE USB 3.1 port. Run 'lsusb -t' and expect the dongle under Bus 002 at 480M, not behind the 1a40:0101 hub on Bus 001.
      - Run 'readlink -f /sys/bus/usb/devices/2-1' to note which DWC3 controller it uses. I expect a600000.usb from the SC7280 device tree, but this is unverified on the Q6A.
      - Run 'rtl_test -s 2400000 2>&1 | head'. You must see 'RTL-SDR Blog V4 Lite Detected'. With the stock or unpatched package you will also see 'Allocating 15 zero-copy buffers'; after the rules fix that line must be gone.
      - Stress test: run 'timeout 900 rtl_test -s 2400000 | tee rtltest.log' while running 'stress-ng --cpu 8 --io 2 --timeout 900', a Wi-Fi 'iperf3 -c <host> -t 900', the HDMI display at full brightness and an NPU benchmark. Then grep for 'lost at least'. Repeat at 2.56 MS/s and 3.2 MS/s to find the margin.
      - Noise survey: put a 50-ohm SMA terminator on the V4L input. Run 'rtl_power -f 24M:1766M:100k -g 40 -i 10 -e 120 term_X.csv' three times: Q6A on a lab/linear supply, Q6A on the 4S pack with the buck converters, and a third run on the 4S pack with the LimeSDR and display active. Compare with Debian's heatmap.py or a short numpy diff, looking for buck-harmonic spur combs at 130-150, 430-440 and 735-745 MHz.
      - If buck spurs show up: feed the dongle from its own filtered 5 V (ferrite bead about 600 ohm at 100 MHz plus 220-470 uF low-ESR plus 100 nF, using the VBUS-cut pigtail from the 'stuck noisy' fix). Put a clip-on ferrite on the USB extension and keep the dongle 10 cm or more from the Q6A SoC and buck inductors.
      - Thermal: after 30 minutes at 2.4 MS/s inside the closed case, measure the dongle case temperature with a thermocouple. Also run 'rtl_test -p 600' and the drift must stay within about 1 ppm. Use 1.024 MS/s for LRPT to cut heat and USB load.
      - Real-signal acceptance: decode one Meteor-M LRPT pass with SatDump at 1.024 MS/s on 137.9 or 137.1 MHz, while the NPU and display are loaded.
    - **How to verify:** Pass criteria: (1) zero 'lost at least' lines in 15 minutes at 2.4 MS/s under full load; (2) no zero-copy line from the patched library; (3) the terminated noise floor differs by 1 dB or less, with no new spurs more than 3 dB above the floor in the satellite bands, between the bench supply and battery runs; (4) PPM drift of 1 ppm or less after warm-up; (5) an LRPT image is decoded. Post the results on the Radxa forum, since this would be the first public report.
    - **Confidence:** medium
    - **Sources:**
      - https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1041701
      - https://launchpad.net/ubuntu/+source/rtl-sdr/2.0.1-2build1
      - https://sources.debian.org/data/main/r/rtl-sdr/2.0.3-1/debian/rules
      - https://github.com/osmocom/rtl-sdr/blob/v2.0.1/src/librtlsdr.c
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/usb
      - https://community.libre.space/t/observation-12326506-weird-waterfall/13732
  2.
    - **Problem:** The Q6A's USB 2.0 topology and per-port power are undocumented. A shared hub, Wi-Fi traffic or a brown-out could cause dropped samples.
    - **Proposed fix:** Resolved from Radxa's own schematic (V1.21, sheet 'USB'). U23 is a Terminus FE1.1s 4-port hub on the SoC's USB1 high-speed-only controller. Its port 1 goes to the top socket of the J5 stack, ports 2 and 3 go to the dual USB 2.0 stack J2, and port 4 goes to the onboard AIC8800D80 Wi-Fi/BT module (USB2_WLAN). So ALL three black USB 2.0 ports share one 480 Mb/s hub (a single transaction translator) with Wi-Fi. The BLUE USB 3.1 port (bottom of J5) connects directly to the SoC's USB0 controller, with its own high-speed root hub (Bus 002). Because the LimeSDR sits on PCIe, that port is free, so put the V4L there. Power is not a constraint. VBUS for J2 comes from U33 and VBUS for J5 from U35. Both are WS4612 current-limited switches with Rset = 3.24 kOhm (Ilim = 6800/Rset, about 2.1 A per switch). EN is hard-tied high through 100 kOhm, and the FE1.1s PWRJ pin is not connected. The V4L plus bias tee needs at most about 270 + 180 = 450 mA, well inside that limit. The flip side is that NO port's VBUS can be switched in software: uhubctl or sysfs port 'disable' only drop the data connection, which matters for the 'stuck noisy' recovery.
    - **Steps:**
      - Use the blue USB 3.1 port for the V4L. Put GNSS and IMU on UART/I2C on the 40-pin header rather than USB, or if they must use USB, on the black ports.
      - If the black ports must carry a high-rate device such as an Airspy at 10 MS/s, turn off Wi-Fi during passes with 'nmcli radio wifi off' or rfkill, to free hub bandwidth.
      - Disable USB autosuspend for the dongle with a udev rule: ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="0bda", ATTR{idProduct}=="2838", ATTR{power/control}="on".
      - Keep the bias-tee load at 180 mA or less. With the LNA powered, check the actual draw with an inline USB meter.
      - Note the trade-off: the blue port is the only USB 3 port. If you ever need USB 3 storage, move the V4L to a black port and accept sharing with Wi-Fi (about 5 MB/s at 2.4 MS/s is still small).
    - **How to verify:** 'lsusb -t' shows the V4L alone on Bus 002 at 480M. A USB meter shows at most 450 mA with the bias tee on. The 15-minute 'rtl_test -s 2400000' run shows no lost bytes while an iperf3 Wi-Fi load runs (which proves isolation from the hub).
    - **Confidence:** high
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/usb
      - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
  3.
    - **Problem:** Nobody has reported the V4L working with SatDump, GNU Radio or gr-satellites on Linux arm64, and there is no clean Ubuntu package path. Purging librtlsdr removes the apt SDR stack, and the SDR++/SoapyRTLSDR/gr-osmosdr builds for noble link librtlsdr.so.2.
    - **Proposed fix:** Don't purge anything. Rebuild Ubuntu noble's own rtl-sdr source package (2.0.1-2build1) with two upstream commits added as quilt patches: 0204c9c (RTL-SDR Blog V4L support, May 2026) and 65f0658 (fix for an application hang on USB transfer errors, Jan 2026). Also fix the zero-copy typo. The result is a drop-in 'librtlsdr2 2.0.1-2build1+v4l1' with the same SONAME (librtlsdr.so.2), so every noble package that uses it gains V4L support without a rebuild: soapysdr0.8-module-rtlsdr, libgnuradio-osmosdr0.2.0t64 (gr-osmosdr), gqrx-sdr, rtl-433, and SDR++'s sdrpp_ubuntu_noble_aarch64.deb, whose rtl_sdr_source.so needs librtlsdr.so.2. This is safe because include/rtl-sdr.h has no changes between v2.0.1 and v2.0.3, and upstream v2.0.2 only reverted the SONAME. I verified the full recipe in an Ubuntu 24.04 container: both patches apply cleanly with offsets only, dpkg-buildpackage succeeds, and the output carries SONAME librtlsdr.so.2. The build ran on amd64; arm64 is the same recipe but untested. SatDump has no usable arm64 package for noble: the rpi64 .deb needs libvolk.so.2.5 and librtlsdr.so.0, while noble ships libvolk3.1t64. Build SatDump master from source; it then links the patched library.
    - **Steps:**
      - Enable source repositories: sudo sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources && sudo apt update && sudo apt install -y build-essential devscripts quilt && sudo apt build-dep -y rtl-sdr
      - Get the source: mkdir -p ~/pkg && cd ~/pkg && apt-get source rtl-sdr && cd rtl-sdr-2.0.1 && mkdir -p debian/patches
      - Add the patches: curl -L https://github.com/osmocom/rtl-sdr/commit/0204c9cfb1c5ff7bd64f466ce5b8fe53b40a636a.patch -o debian/patches/0001-v4l.patch ; curl -L https://github.com/osmocom/rtl-sdr/commit/65f06585ea46160cd2d7bee8b3f641c14771c2ee.patch -o debian/patches/0002-usb-hang.patch ; printf '0001-v4l.patch\n0002-usb-hang.patch\n' > debian/patches/series
      - Fix the zero-copy typo: sed -i 's/\$DEB_ZEROCOPY_OPTION/$(DEB_ZEROCOPY_OPTION)/' debian/rules. I checked with 'make -n' that arm64 now gets OFF.
      - Build: dch --local +v4l 'V4L support, USB hang fix, zerocopy off on arm64' && dpkg-buildpackage -b -us -uc -j6
      - Install and pin: sudo apt install ../librtlsdr2_*+v4l1_arm64.deb ../librtlsdr-dev_*+v4l1_arm64.deb ../rtl-sdr_*+v4l1_arm64.deb && sudo apt-mark hold librtlsdr2 librtlsdr-dev rtl-sdr. The hold is required, because a future 2.0.1-2build2 would sort higher than +v4l1.
      - Blacklist the DVB drivers yourself, since the package ships /etc/modprobe.d empty: printf 'blacklist dvb_usb_rtl28xxu\nblacklist rtl2832\nblacklist r820t\n' | sudo tee /etc/modprobe.d/rtl-sdr-blacklist.conf ; then sudo usermod -aG plugdev $USER and reboot.
      - Install the stack from apt: sudo apt install soapysdr-tools soapysdr0.8-module-rtlsdr gr-osmosdr gnuradio gr-satellites gqrx-sdr. Then install SDR++ from the nightly sdrpp_ubuntu_noble_aarch64.deb.
      - Build SatDump master from source: follow its README apt list (libvolk-dev, libnng-dev, libzstd-dev, libhdf5-dev, libglfw3-dev, librtlsdr-dev and so on), then cmake -DCMAKE_BUILD_TYPE=Release .. && make -j6 on UFS with 4-8 GB zram, then sudo make install. Build LimeSuiteNG (limesdr-micro branch) BEFORE SatDump so that its limesdrng plugin gets built.
      - Never use AppImages or Flatpaks that bundle their own librtlsdr for the V4L.
    - **How to verify:** 'objdump -p /usr/lib/aarch64-linux-gnu/librtlsdr.so.2 | grep SONAME' prints librtlsdr.so.2, and 'dpkg -l librtlsdr2' shows +v4l1. 'rtl_test' prints 'RTL-SDR Blog V4 Lite Detected'. 'SoapySDRUtil --find' lists the dongle. In SDR++, broadcast FM shows at about 100 MHz (the old library gives no signal). 'ldd' on SDR++'s rtl_sdr_source.so and on SatDump's librtlsdr_sdr_support.so both resolve to the patched file. A GNU Radio osmocom source with args 'rtl=0' shows signals. Finally, decode a Meteor LRPT pass with 'satdump live'.
    - **Confidence:** high
    - **Sources:**
      - https://github.com/osmocom/rtl-sdr/commit/0204c9cfb1c5ff7bd64f466ce5b8fe53b40a636a
      - https://github.com/osmocom/rtl-sdr/commit/65f06585ea46160cd2d7bee8b3f641c14771c2ee
      - https://github.com/osmocom/rtl-sdr/tags
      - https://packages.ubuntu.com/source/noble/rtl-sdr
      - https://launchpad.net/ubuntu/+source/rtl-sdr
      - https://tracker.debian.org/pkg/rtl-sdr
      - https://sources.debian.org/data/main/r/rtl-sdr/2.0.3-1/debian/rules
      - https://github.com/AlexandreRouma/SDRPlusPlus/releases/tag/nightly
      - https://github.com/SatDump/SatDump/releases/tag/nightly
      - https://github.com/SatDump/SatDump/blob/master/README.md
  4.
    - **Problem:** The V4L lacks the V4's triplexer and notch filters, so a broadband LNA near FM, DVB-T2 or other strong transmitters can desensitise 137, 145 and 435 MHz reception. Nobody has measured this in the field.
    - **Proposed fix:** Put the filter BEFORE any gain, and give each band its own front end instead of one broadband SPF5189Z or QPL9547 LNA. Why it matters, using free-space estimates (assumptions: 10 kW ERP FM, dipole, line of sight): a mast at 2 km delivers about -4 dBm, and at 10 km about -18 dBm. The V4L datasheet's two-tone test (95 MHz blocker) shows 3 dB desense at about -12 dBm for low-VHF targets and -20 to -40 dBm for 300-1600 MHz targets. So an unfiltered 20 dB LNA puts about +16 dBm of FM into the dongle, which is badly overloaded. An RTL-SDR Blog FM bandstop (more than 50 dB rejection, less than 0.5 dB insertion loss) placed BEFORE that LNA brings it to about -29 dBm at 2 km or -43 dBm at 10 km, which is marginal or OK for 435 MHz. SAW-filtered preamps add a further 30-50 dB. Per-band chains: (a) 137 MHz LRPT: Nooelec SAWbird(+) NOAA, $49.95, at least 20 dB gain, NF about 0.7 dB, 3-5 V at about 80 mA, so the V4L's 4.5 V/180 mA bias tee can power it. An alternative is the Uputronics 137.5 MHz filtered preamp (7.6 MHz SAW with a high-pass filter before the LNA). (b) 145.8 MHz ISS SSTV: usually strong, so use NO LNA, just the RTL-SDR Blog FM bandstop. At high-RF sites add a Mini-Circuits SBP-150+ (140-160 MHz, about EUR 67 at DigiKey with long lead time; Mouser had stock). (c) 435-438 MHz CubeSats: Uputronics '435 MHz CubeSat' filtered preamp (440 MHz SAW with 30 MHz bandwidth, at least 19 dB gain, NF 0.75 dB, about EUR 48 at Kubii, stock uncertain). Its regulator wants 5-26 V, so power it from the main 5 V buck through USB-mini or an external bias tee, NOT from the 4.5 V V4L tee (uncertain whether it works at 4.5 V). Keep the broadband QPL9547 LNA only for the L-band/IF chains of the other components, always behind a band filter.
    - **Steps:**
      - Order: antenna -> band filter or SAW-LNA (whose first stage is a filter) -> coax -> FM bandstop at the dongle (optional extra) -> V4L. Never put a broadband LNA ahead of the FM bandstop.
      - Use manual gain: SatDump '--gain <dB>' without agc, and SDR++ with AGC off. Start with no LNA at 30-35 dB tuner gain and with a SAW-LNA at about 20-30 dB.
      - Overload check on every new site: insert a 6 dB SMA attenuator in front of the V4L. If the target SNR on the Meteor carrier or a 70 cm beacon stays the same or improves, the chain is overloaded, so lower the gain or add filtering until 6 dB of attenuation costs about 1-2 dB of SNR.
      - Spur check: with the antenna connected, scan 136-139, 144-147 and 434-439 MHz for FM-audio-modulated or wide 'smear' products that move when you retune by 100 kHz. Those are mixing products, not real signals.
      - Measure each filter's S21 with a NanoVNA (about $50-70, which also tunes the Yagis and helix): check at least 40 dB rejection at 88-108 MHz on the 137 and 145 chains, and at 470-790 MHz (DVB-T2) on the 435 chain.
      - Bias-tee safety: the WB2HOL tape-measure Yagi's hairpin match is a DC short. Enable '--bias' only when a bias-powered LNA sits between the dongle and the antenna, or add a DC block.
    - **How to verify:** Near the strongest FM site you use, record the same Meteor pass or 70 cm beacon twice, with and without the filtered chain. The filtered chain must show higher SNR in SatDump's constellation/SNR plot and no new spurs. The 6 dB attenuator test must show a small SNR drop, not an improvement. The NanoVNA plots must confirm the filter rejection figures.
    - **Confidence:** medium
    - **Sources:**
      - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-broadcast-fm-band-stop-filter/
      - https://www.rtl-sdr.com/?p=17883
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-noaa.html
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird.html
      - https://kubii.com/en/network-modules/3349-lna-amplifier-modules-with-saw-filter-and-single-frequency-3272496306646.html
      - https://www.digikey.be/en/products/detail/mini-circuits/SBP-150/25963569
      - https://www.mouser.kr/c/passive-components/filters/?series=SBP
  5.
    - **Problem:** V4L long-term reliability and supply are unknown. The R828S is end-of-life (stock expected to last about one year), there is no field thermal data in a closed printed case, and the USB-A plug needs strain relief.
    - **Proposed fix:** Treat the V4L as a consumable. Buy two now and protect their EEPROMs. V4L detection in librtlsdr depends ONLY on the EEPROM strings 'RTLSDRBlog' / 'Blog V4L' (the R828S identifies itself as an R820T). A corrupted EEPROM silently turns the dongle back into a 'no signal' generic device, so back up the EEPROM image. Handle heat and mechanics in the case design. Keep the RTL-SDR Blog V3 (in stable production, same software stack) as the supply fallback, and the Airspy Mini as the performance upgrade.
    - **Steps:**
      - Buy 2 x V4L from the official RTLSDRBlog AliExpress store (no. 4523039), about $34-38 each. Keep the spare sealed in an ESD bag.
      - On arrival, back up each EEPROM: 'rtl_eeprom -d 0 -r v4l_A_eeprom.bin'. Then set a unique serial only: 'rtl_eeprom -d 0 -s 00000137'. Re-check that 'rtl_test' still prints 'RTL-SDR Blog V4 Lite Detected'. If it ever stops, restore with 'rtl_eeprom -w v4l_A_eeprom.bin'.
      - Mechanics: mount the dongle in a printed cradle with a cable-tied 10-15 cm USB-A extension and a strain-relief loop. Clamp the aluminium case to a vented wall or to a small aluminium plate. Print the case in PETG or ASA, not PLA, which softens at about 55-60 C.
      - Thermal: put the dongle in its own vented bay, upstream of or away from the Q6A heatsink exhaust. Use 1.024 MS/s for LRPT. Log case temperature and 'rtl_test -p' drift during a 30-minute soak.
      - Fallbacks: the RTL-SDR Blog V3 ($34.95-39.95) works with the same patched library and all the apps; you lose only HF quality. The Airspy Mini ($99 list, often on sale) is the 12-bit upgrade. Re-check RTL-SDR Blog V5 news in 2027.
    - **How to verify:** Both units pass the bench acceptance test from the first fix. Both EEPROM backups exist and the readback after setting the serial still detects V4L. After a 30-minute soak at 2.4 MS/s in the closed case, the PPM drift is about 1 ppm or less and the case temperature is stable and below about 55 C (target; no vendor limit is published). A tug test on the cable does not interrupt streaming.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/osmocom/rtl-sdr/commit/0204c9cfb1c5ff7bd64f466ce5b8fe53b40a636a
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
      - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://community.libre.space/t/observation-12326506-weird-waterfall/13732
  6.
    - **Problem:** The RTL-SDR 'stuck noisy until replugged' fault has no known root cause. PE0SAT and others report that only removing power from the dongle clears it.
    - **Proposed fix:** You can't fix the root cause, but you can detect the fault automatically and recover from it in the field. The Q6A cannot cut VBUS in software (the WS4612 EN pins are hard-wired and the FE1.1s PWRJ pin is not connected), so add a GPIO-controlled VBUS-cut pigtail that is ON by default, plus a pre-pass health check with an escalating recovery ladder. The patched library's USB-hang fix (65f0658) makes apps exit cleanly on USB errors instead of freezing, so systemd can restart them. Pigtail circuit, fed from the main 5 V buck rather than the Q6A port: 5 V_buck -> 0.5 A PTC -> ferrite bead -> Q1 AO3401A P-MOSFET (source on the 5 V side, drain to the dongle VBUS). R1 = 100 kOhm gate-to-GND, so Q1 is ON by default. Q2 is an MMBT3906 PNP: emitter to 5 V, collector to the gate, R3 = 47 kOhm base-emitter, R2 = 10 kOhm base to the collector of Q3. Q3 is an MMBT3904 NPN: emitter to GND, R4 = 10 kOhm from the Q6A GPIO to its base, R5 = 100 kOhm base-to-GND. GPIO high turns Q3 and Q2 on, pulls the gate up to 5 V and turns the dongle OFF. This works whether the header is 1.8 V or 3.3 V logic (unconfirmed for the Q6A). Add 22 uF + 100 nF at the dongle VBUS. Build it into a USB-A extension: cut and insulate the host-side VBUS wire, pass D+, D-, GND and the shield straight through.
    - **Steps:**
      - Before each pass (T-3 min): 'timeout 10 rtl_sdr -d 00000137 -f <quiet freq near target> -s 2048000 -g 30 -n 4096000 /dev/shm/hc.u8 2> /dev/shm/hc.log'. Then a numpy script computes the mean power in dBFS, the DC offset, the fraction of 0/255 samples and the spectral flatness, and compares them with the median of the last 20 good checks.
      - Fail the check if: rtl_sdr fails or times out; 'PLL not locked' appears in the log; the power is more than 6 dB from the baseline; or more than 1e-4 of samples are clipped.
      - Recovery ladder: (1) re-run, which reopens the device and fully re-initialises the R82xx; (2) 'usbreset 0bda:2838' (usbreset ships in noble's usbutils 1:017); (3) 'echo 1 > /sys/bus/usb/devices/2-0:1.0/usb2-port1/disable; sleep 2; echo 0 > ...' to force re-enumeration (data only, VBUS stays on); (4) hardware power cut with 'gpioset --mode=time --sec=3 gpiochip4 96=1' (libgpiod 1.6.3 syntax on noble; Radxa's example maps GPIO_96 = gpiochip4 line 96 on pin 7; confirm with 'gpioinfo gpiochip4'), then wait 3 s for enumeration and re-check.
      - Run decoders as systemd units with Restart=on-failure, so a USB error now exits the process instead of hanging it.
      - Log every recovery with a timestamp, temperature and sample rate, so the root cause (thermal, USB or power) can be correlated over months.
    - **How to verify:** Bench: with the GPIO held high, 'lsusb' no longer lists 0bda:2838 and a meter on VBUS reads under 0.1 V. Releasing the GPIO re-enumerates the dongle within 3 s. Fault injection: wiggle the USB plug or briefly short the input to provoke a bad state, and confirm the health check flags it and the ladder restores the baseline power within 1 dB. Over a month of scheduled passes, the log should show zero failed passes caused by the dongle.
    - **Confidence:** medium
    - **Sources:**
      - https://community.libre.space/t/observation-12326506-weird-waterfall/13732
      - https://community.libre.space/t/observation-13477706-acs3-59588-eggbeater-not-a-valid-pass-what-what-could-cause-it/14461
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://github.com/osmocom/rtl-sdr/commit/65f06585ea46160cd2d7bee8b3f641c14771c2ee
      - https://raw.githubusercontent.com/torvalds/linux/master/Documentation/ABI/testing/sysfs-bus-usb
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/pin-gpio
  7.
    - **Problem:** Running SatDump on two sources at once (V4L plus LimeSDR Micro through LimeSuiteNG) is undocumented, and issue #1177 shows SatDump instances interfering with each other's devices.
    - **Proposed fix:** From the SatDump source: 'satdump live' and 'satdump record' call dsp::getAllAvailableSources(), which runs every plugin's enumerator. The Lime enumerator calls LMS_Open() and LMS_Close() on every Lime device. So a second SatDump process can open the LimeSDR that the first process is streaming from; that is a plausible cause of #1177-type conflicts, although this is not confirmed for the Micro. The RTL enumerator only reads USB strings, which is harmless. The fix is plugin isolation, plus two CLI instances bound by --source_id, and no satdump_sdr_server. Use SatDump master (2.0 alpha): only master has the 'limesdrng' plugin built against LimeSuiteNG's limesuiteng-legacyapi. SatDump 1.2.2 knows only legacy LimeSuite, and SDR++'s limesdr_source links legacy libLimeSuite as well. The LimeSuiteNG limesdr-micro branch (last commit Oct 1, 2026) builds the legacy API (BUILD_LEGACYAPI=ON), the SoapyLMS plugin, gr-limesuiteng and the la9310_limesdr kernel module.
    - **Steps:**
      - Build LimeSuiteNG from branch limesdr-micro (cmake defaults keep BUILD_LEGACYAPI=ON), run sudo make install and ldconfig. Then build SatDump master, and check that liblimesdrng_sdr_support.so was produced.
      - Isolate the Lime plugin: sudo mkdir -p /opt/satdump-lime/plugins && sudo mv $(find /usr -name liblimesdrng_sdr_support.so) /opt/satdump-lime/plugins/. SatDump loads ./plugins from the current directory first, then the system directory, so only processes started from /opt/satdump-lime will see the Lime.
      - Find the device IDs: 'satdump sdr_probe'. The rtlsdr unique_id is the EEPROM serial; the limesdrng ID is the device index '0'.
      - RTL instance (any working directory except /opt/satdump-lime): satdump live meteor_m2-x_lrpt /data/lrpt_$(date +%F_%H%M) --source rtlsdr --source_id 00000137 --samplerate 1.024e6 --frequency 137.9e6 --gain 30 --bias --timeout 900
      - Lime instance: cd /opt/satdump-lime && satdump live meteor_hrpt /data/hrpt_$(date +%F_%H%M) --source limesdrng --source_id 0 --samplerate 8e6 --frequency 1700e6 --path_id 3 --lna_gain 30 --tia_gain 12 --pga_gain 10 --timeout 900. Here path_id 3 = LNAW (0.7-2.6 GHz) and 2 = LNAL. Stay at 7 MS/s or above: the Micro driver says lower rates without decimation add noise. Check pipeline IDs and gain keys against your build's 'satdump live' help and pipeline list.
      - CPU: check the core layout with 'lscpu -e'. Run both, monitor with 'pidstat -u 5' and watch the logs for overflow warnings. If HRPT drops data, pin it to the A78 cores (taskset -c 4-7) and LRPT to the A55 cores (0-3).
      - Fallback if live decoding overruns: record HRPT baseband with 'satdump record' (cs16, about 32 MB/s at 8 MS/s, well within UFS write speed) and decode right after the pass.
    - **How to verify:** 'satdump sdr_probe' run from the RTL working directory does NOT list a LimeSDR; run from /opt/satdump-lime it lists both. One Meteor-M pass yields both an LRPT and an HRPT product from the two processes. Starting and stopping the RTL instance during an HRPT capture causes no glitch in the HRPT SNR trace. Combined CPU stays below about 70% of the A78 cores.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/SatDump/SatDump/issues/1177
      - https://github.com/SatDump/SatDump/blob/master/src-cli/legacy/live.cpp
      - https://github.com/SatDump/SatDump/blob/master/src-core/core/plugin.cpp
      - https://github.com/SatDump/SatDump/blob/master/plugins/sdr_sources/limesdr_sdr_support/lime_sdr.cpp
      - https://github.com/SatDump/SatDump/blob/master/plugins/sdr_sources/limesdr_sdr_support/CMakeLists.txt
      - https://github.com/SatDump/SatDump/blob/1.2.2/plugins/sdr_sources/limesdr_sdr_support/CMakeLists.txt
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro
  8.
    - **Problem:** LimeSDR Micro performance at 137-146 MHz is unmeasured.
    - **Proposed fix:** The LimeSuiteNG Micro driver confirms the concern: its RX path ranges are LNAH 3.3-3.8 GHz, LNAL 0.3-2.2 GHz and LNAW 0.7-2.6 GHz, so 137 and 145.8 MHz fall below every matched path, and the minimum sample rate without decimation is 7 MS/s. Plan on the V4L as the PRIMARY VHF receiver. Measure the Lime once with a same-signal A/B test before giving it any VHF job.
    - **Steps:**
      - Feed one antenna, plus the SAWbird NOAA if used, into a 2-way 50-ohm splitter (for example Mini-Circuits ZFSC-2-1 class or a cheap Wilkinson), with one output to the V4L and one to the Lime RX on LNAL (path_id 2).
      - Record the same Meteor LRPT pass on both. SatDump: V4L at 1.024 MS/s; Lime at 8 MS/s with LNAL, LNA gain at maximum and TIA/PGA adjusted.
      - Compare SatDump's SNR and Viterbi BER traces and the number of decoded lines. Repeat on 145.8 MHz during an ISS SSTV event and on a 435 MHz CubeSat.
      - Optional lab test: a signal generator (or an ADF4351 board plus at least 90 dB of step attenuation, with careful shielding) to find each radio's MDS at 137 MHz; or a noise source and attenuator to compare relative noise rise (a relative noise-figure comparison).
    - **How to verify:** If the Lime's LRPT SNR is within 1 dB of the V4L chain on two passes, the Lime may take VHF jobs. Otherwise, keep VHF on the V4L permanently and use the Lime only for 700 MHz and above (QO-100 IF, L- and S-band).
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro
  9.
    - **Problem:** HydraSDR and Airspy alternatives have open Linux gaps: a SatDump Airspy Stop deadlock (PR #1172 unmerged), no ppm correction in SoapyAirspy, unimplemented SoapyHydraSDR bandwidth queries, and HydraSDR alias folding (issue #25).
    - **Proposed fix:** These matter only if you upgrade to a 12-bit dongle. Workarounds: (1) We build SatDump from source anyway, so apply PR #1172 locally. It is a one-file change in airspy_sdr.cpp that calls output_stream->stopWriter() before airspy_stop_rx(). (2) ppm correction isn't needed: the Airspy Mini's 0.5 ppm clock is about ±220 Hz at 437 MHz and ±850 Hz at 1.7 GHz, far inside the carrier-recovery range of LRPT, HRPT and GMSK demodulators and smaller than the Doppler shift. If needed, offset --frequency instead. (3) HydraSDR: use the native SatDump hydrasdr plugin and SDR++'s mainline hydrasdr_source (now in the noble aarch64 nightly, so no fork is needed) instead of Soapy. Keep targets in the central about 8.5 MHz of the 10 MS/s span, since issue #25 shows strong signals just outside the window folding inside its edges.
    - **Steps:**
      - In the SatDump source tree: curl -L https://github.com/SatDump/SatDump/pull/1172.patch | git am, then rebuild.
      - For Airspy or HydraSDR in SDR++ or SatDump, tune so the satellite sits within ±4 MHz of the center at 10 MS/s, or use 6 MS/s.
      - Skip the SoapyAirspy and SoapyHydraSDR modules for decoding and use the native plugins.
    - **How to verify:** Ten Start/Stop cycles of an Airspy source in the SatDump GUI produce no freeze. A known strong out-of-span carrier, such as a local repeater, does not appear inside the used central span.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/SatDump/SatDump/pull/1172
      - https://github.com/hydrasdr/rfone_host/issues/25
      - https://github.com/AlexandreRouma/SDRPlusPlus/releases/tag/nightly
      - https://airspy.com/airspy-mini/
  10.
    - **Problem:** The landed price and shipping to Ukraine for an official V4L are unverified, and buying locally carries counterfeit risk.
    - **Proposed fix:** Order from the official RTLSDRBlog AliExpress store. RTL-SDR Blog itself says delivery to Ukraine through AliExpress is operational. Combine two V4L units and, if wanted, the FM bandstop into one order kept under EUR 150. Under current Ukrainian rules, international parcels up to EUR 150 pay no import VAT or duty. A law adopted on 15 Oct 2026 adds 20% VAT from the first euro, but it takes effect no earlier than July 2027, so buy spares now. The official Ukrainian reseller listed by RTL-SDR Blog, sdr.in.ua, shows 'online store temporarily not working' (Oct 2026). It lists V4 at 2,950 UAH and V3 at 2,500 UAH, and has no V4L. Treat Prom.ua and Rozetka 'V4' listings as probable fakes.
    - **Steps:**
      - Order from the AliExpress store no. 4523039 'RTLSDRBlog Store': 2 x V4L dongle-only (about $34.20 each on AliExpress, $37.95 list). Optionally add the FM bandstop. Keep the total under EUR 150.
      - On arrival, check genuineness: diagonal side screws and the QC batch sticker, then 'rtl_test' printing 'RTL-SDR Blog V4 Lite Detected', which reads the factory EEPROM strings.
      - Re-check sdr.in.ua before ordering, in case it reopens with V4L stock and Nova Poshta delivery.
    - **How to verify:** The AliExpress checkout shows the shipping cost to your Ukrainian address before you pay (record the final landed price). Both units pass the genuineness and acceptance checks.
    - **Confidence:** medium
    - **Sources:**
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://www.rtl-sdr.com/GENUINE
      - https://unn.ua/en/news/the-rada-introduced-a-tax-on-parcels-worth-up-to-euro150-what-is-changing-and-what-the-partners-money-has-to-do-with-it
      - https://sdr.in.ua/
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-v4l-lite-r828s-rtl2832u-1ppm-tcxo-sma-software-defined-radio-dongle-only/
- **Residual risks:**
  - The patched librtlsdr2 recipe was built and checked only on Ubuntu 24.04 amd64 in a container. The arm64 build on the Q6A, and V4L reception with it, are untested; the first real test is rtl_test on the board.
  - Whether zero-copy actually corrupts data on the Q6A's SMMU and DWC3 is unknown. Disabling it is a safe default that costs a little CPU at about 5 MB/s.
  - The controller mapping (Bus 002 = USB0 at a600000.usb) comes from the schematic and the SC7280 device tree. Confirm it with lsusb -t and readlink on the board.
  - The logic level of the 40-pin GPIO header (1.8 V or 3.3 V) is undocumented. The transistor VBUS-cut circuit works with either, but check the GPIO line number with gpioinfo.
  - SatDump master is a 2.0 alpha, and its CLI flags, pipeline IDs and Lime gain keys may change. The LimeSuiteNG legacy API with the LimeSDR Micro, and the interference from LMS_Open during enumeration, are inferred from source code and not tested on hardware.
  - The Uputronics preamps need 5-26 V and may not run from the V4L's 4.5 V bias tee. Stock of the 435 MHz CubeSat variant at Kubii looked uncertain. SBP-150+ lead times are long at DigiKey.
  - FM blocker levels are free-space estimates. Real levels depend on the antenna pattern and terrain, so measure with the attenuator test at each site.
  - R828S supply ends in about a year and the V5 is only in scoping, so plan for the V3 or Airspy Mini as the long-term fallback.
  - AliExpress shipping cost and transit time to Ukraine were not verified. Ukrainian parcel tax rules change from July 2027 at the earliest. sdr.in.ua may reopen.

## Адверсаріальна перевірка (`verify`)

_Run `wf_eb446444-464`_

- **Component:** Second / narrowband SDR (RTL-SDR Blog V4 is EOL; proposed: RTL-SDR Blog V4L on the Radxa Dragon Q6A, alongside the LimeSDR Micro)
- **Recommendation holds:** так
- **Issues:**
  1.
    - **Claim:** Community: 'a cleaner route on Ubuntu is to rebuild the Debian 2.0.3-1 source package so the librtlsdr2 SONAME is kept'.
    - **Problem:** Wrong. Debian 2.0.3-1 builds the package librtlsdr0 (SONAME .so.0), with Breaks/Replaces: librtlsdr2 (<< 2.0.2). Installing it on noble forces apt to remove librtlsdr2, and with it every noble package that depends on it: soapysdr0.8-module-rtlsdr, gr-osmosdr, gqrx, and the SDR++ noble .deb.
    - **Correction:** Rebuild noble's own 2.0.1-2build1 source package with osmocom commits 0204c9c (V4L support) and 65f0658 (USB-hang fix). I tested this: both patches apply cleanly to the noble source with offsets only, the library compiles, and objdump shows SONAME librtlsdr.so.2. I built on amd64; an arm64 build was not tested.
    - **Source:** https://sources.debian.org/data/main/r/rtl-sdr/2.0.3-1/debian/control ; https://launchpad.net/ubuntu/+source/rtl-sdr/2.0.1-2build1
  2.
    - **Claim:** Researcher integration note and RTL-SDR Blog V4L guide: 'apt purge ^librtlsdr', build osmocom master, then rebuild SoapyRTLSDR, gr-osmosdr, SatDump and SDR++ from source.
    - **Problem:** On Ubuntu 24.04 this is destructive and unnecessary. The purge removes the whole apt SDR stack. Upstream 2.0.2+ installs SONAME .so.0, so the SDR++ noble .deb and the distro Soapy/gr-osmosdr, which want .so.2, break. The official guide also clones osmocom/rtl-sdr and then runs 'cd rtl-sdr-blog', which fails.
    - **Correction:** Use the patched noble librtlsdr2 package (2.0.1-2build1+v4l1) and put it on apt-mark hold. Then only SatDump has to be built from source: its nightly has no Ubuntu arm64 .deb, only satdump_rpi64_latest_arm64.deb.
    - **Source:** https://www.rtl-sdr.com/V4L ; https://github.com/SatDump/SatDump/releases/tag/nightly
  3.
    - **Claim:** Debian/Ubuntu librtlsdr disables zero-copy on arm64 (Debian bug #1041701 fix).
    - **Problem:** It does not, because of a typo. debian/rules in noble 2.0.1-2build1 and in Debian 2.0.3-1 passes -DENABLE_ZEROCOPY=$DEB_ZEROCOPY_OPTION. Make expands that to the literal 'EB_ZEROCOPY_OPTION', which CMake treats as true. I reproduced it: the result is -DENABLE_ZEROCOPY=1. Upstream's default is OFF. The fixer is right, but the original Odroid failure ran on a 4.9 kernel, so on the Q6A's 6.x kernel this is a precaution rather than a proven cause.
    - **Correction:** In debian/rules, change $DEB_ZEROCOPY_OPTION to $(DEB_ZEROCOPY_OPTION) when building the patched package.
    - **Source:** https://sources.debian.org/data/main/r/rtl-sdr/2.0.3-1/debian/rules ; https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1041701
  4.
    - **Claim:** Researcher: the RTL-SDR Blog V3 has 'VHF/UHF performance close to the V4L'.
    - **Problem:** The V4L datasheet MDS chart shows the V3 about 2 dB worse at 137 MHz (about -138.6 vs -140.7 dBm) and about 3 dB worse at 435-740 MHz. That matters for no-LNA 145.8 MHz and 435 MHz use. With a 20 dB, 0.7 dB NF filtered LNA in front, the difference becomes negligible.
    - **Correction:** Say the V3 is about 2-3 dB less sensitive at VHF/UHF than the V4L and has identical overload behaviour (same two-tone curve).
    - **Source:** https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
  5.
    - **Claim:** Community: Ubuntu 26.04 has 2.0.2 and 'only the next Ubuntu dev series has 2.0.3-1'.
    - **Problem:** Launchpad lists 2.0.3-1 in the current stable release, Ubuntu 26.10 (published 2026-10-01). 26.04 LTS indeed has 2.0.2-2build1 and noble has 2.0.1-2build1. The Q6A images are 24.04, so the practical conclusion does not change.
    - **Correction:** Minor. Stock V4L support exists only in Ubuntu 26.10 and later; on the Q6A's 24.04 image, use the patched package.
    - **Source:** https://launchpad.net/ubuntu/+source/rtl-sdr
  6.
    - **Claim:** BOM: LimeSDR Micro costs $199 and ships from about Sept 30, 2026, and covers 30 MHz-3.8 GHz.
    - **Problem:** Outdated. Crowd Supply now lists $249 (Basic) and $299 (GNSS), and new orders ship Dec 15, 2026. Lime staff give about 4 W draw. In the LimeSuiteNG limesdr-micro code the matched RX paths are LNAL 0.3-2.2 GHz, LNAW 0.7-2.6 GHz and LNAH 3.3-3.8 GHz, with a minimum of 7 MS/s. So 137 MHz and 145.8 MHz fall below every optimised match. The Lime also needs the out-of-tree la9310_limesdr kernel module.
    - **Correction:** This strengthens the case for keeping the V4L. It is the primary VHF receiver, the only radio usable until at least mid-December, and about 1.3 W versus about 4 W.
    - **Source:** https://www.crowdsupply.com/lime-micro/limesdr-micro ; https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304 ; https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp
  7.
    - **Claim:** Fixer: the Uputronics 435 MHz preamp 'wants 5-26 V', so do not run it from the V4L's 4.5 V bias tee.
    - **Problem:** Probably outdated. Recent Uputronics filtered preamps are listed with the bias-tee input limited to 5 V maximum, because of component supply, and as '100% compatible with the Airspy bias-tee', which is 4.5 V. The 5-26 V regulator figure comes from older revisions. I found no datasheet for the 435 MHz model specifically.
    - **Correction:** Check the exact revision. A current unit is likely to run from the V4L's 4.5 V tee, and you must NOT feed it more than 5 V from the main rail.
    - **Source:** https://thepihut.com/products/162mhz-ais-filtered-preamplifier ; https://discussions.flightaware.com/t/biast-recommendation/82979
  8.
    - **Claim:** Community: mainline SDR++ does not recognise the HydraSDR, so a fork is needed.
    - **Problem:** Outdated. SDR++ master now contains source_modules/hydrasdr_source, and fobossdr_source as well.
    - **Correction:** No fork is needed for HydraSDR, but this only matters if you upgrade to a 12-bit radio.
    - **Source:** https://github.com/AlexandreRouma/SDRPlusPlus/tree/master/source_modules
  9.
    - **Claim:** Researcher: the Q6A USB 2.0 ports 'may share one hub (unverified)'.
    - **Problem:** Now confirmed from the Radxa V1.21 schematic, USB sheet (sheet 28). U23 is an FE1.1s hub on the SoC's HS-only USB1. It feeds the J5 top socket, both J2 sockets and the onboard AIC8800 Wi-Fi/BT. The blue USB 3.1 port (J5 bottom) connects directly to USB0, which appears as Bus 002/003. Both VBUS switches are WS4612 with EN tied to IN through 100 kOhm and Rset 3.24 kOhm, so about 2.1 A each; the '500mA' labels are trace annotations. The Q19/Q21 switch on the USB3 port's VBUS is driven by VDD_FUSB itself, not by a GPIO. So the fixer is right that no port's VBUS can be switched in software.
    - **Correction:** Put the V4L on the blue port. Use the fixer's external VBUS-cut pigtail if you want hard power-cycling.
    - **Source:** https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf ; https://docs.radxa.com/en/dragon/q6a/hardware-use/usb
  10.
    - **Claim:** No reviewer considered the display as an RFI source for the V4L.
    - **Problem:** The display is now likely HDMI. On the Q6A, HDMI is made by a DP-to-HDMI bridge from USB0's combo PHY (schematic sheets 28-29), inside the same palm-sized case. A 1080p60 HDMI TMDS clock is 148.5 MHz, only 2.7 MHz from ISS SSTV at 145.8 MHz; its 3rd harmonic is 445.5 MHz, close to the 435-438 MHz CubeSats. Higher resolutions bring other clocks and harmonics. This is an inference from standard CEA-861 timings and has not been measured on this build.
    - **Correction:** Add the display to the noise survey. Pick an HDMI mode and pixel clock whose harmonics avoid 136-138, 144-147, 435-438 and 739-741 MHz. Keep the HDMI link short and shielded with ferrites, and blank or dim the display during weak passes if spurs appear.
    - **Source:** https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
  11.
    - **Claim:** Researcher: the Airspy Mini is the 'optional upgrade' for RF-dense locations.
    - **Problem:** Missing caveats. The official Airspy page rates it for -10 to +40 C only, which is marginal in a sun-exposed sealed handheld. It uses the same R820T2-class tuner front end, so filtering remains the real fix for FM and DVB-T2 overload. Linux gaps remain: SoapyAirspy has no ppm correction, and the SatDump Stop-deadlock PR #1172 is unmerged.
    - **Correction:** Keep it as a conditional upgrade only after filtered LNAs prove insufficient, and give it a ventilated bay.
    - **Source:** https://airspy.com/airspy-mini/
  12.
    - **Claim:** Researcher: about $34.20 for the V4L on the official AliExpress listing.
    - **Problem:** Unverifiable. The AliExpress item page redirects to a geo page and renders empty for fetchers. The official store price ($37.95, 455 in stock) is verified.
    - **Correction:** Budget $37.95 plus shipping, and read the landed price to Ukraine at AliExpress checkout.
    - **Source:** https://www.rtl-sdr.com/product/rtl-sdr-blog-v4l-lite-r828s-rtl2832u-1ppm-tcxo-sma-software-defined-radio-dongle-only/
- **Forum and fix assessment:** The forum findings do not change the verdict. Keep a second SDR and make it the V4L. They do change how it is integrated, and the fixer's proposals are mostly sound. I checked these points independently.
  
  - **Packaging fix:** correct and the best route. The V4L and USB-hang patches apply to noble's 2.0.1 source and build with SONAME librtlsdr.so.2. That keeps the apt SDR stack (SoapyRTLSDR, gr-osmosdr, gqrx, gr-satellites 5.5.0 from noble universe, and SDR++ noble aarch64 nightly) working without rebuilds. The community's alternative of rebuilding Debian 2.0.3-1 is wrong, because that package is librtlsdr0/.so.0 and breaks librtlsdr2.
  - **Zero-copy typo:** real, reproduced with CMake.
  - **USB topology fix:** correct per the schematic. The blue port is on the separate USB0 controller. Both VBUS switches allow about 2.1 A and cannot be switched in software.
  - **VBUS-cut pigtail circuit:** electrically sound. The P-FET body diode blocks when off, it is on by default with the GPIO floating, and it works from 1.8 V or 3.3 V logic. A load-switch IC would be simpler but is not required.
  - **SatDump two-process isolation:** verified in source. plugin.cpp loads ./plugins before the system directory, and the Lime enumerator calls LMS_Open/LMS_Close on every device in getAvailableSources. The workaround is valid. #1177 is still open and has no maintainer reply.
  - **LimeSDR Micro VHF concern:** confirmed by the limesdr-micro branch code (LNAL from 0.3 GHz, 7 MS/s minimum). The V4L is the primary VHF receiver.
  - **Overload analysis:** matches the datasheet. With a 95 MHz blocker, 3 dB desense occurs at -12 dBm at low VHF and -20 to -40 dBm at 300-1600 MHz, versus -7 dBm and +8 dBm for the V4. The FSPL estimate of about -4 dBm at 2 km from a 10 kW ERP mast is arithmetically right.
  - **Per-band filtered LNAs and FM bandstop before any gain:** this is the right call. Verified figures: FM bandstop $16.95, more than 50 dB rejection, less than 0.5 dB loss below 1 GHz. SAWbird NOAA $49.95, at least 20 dB gain, NF 0.7 dB, about 80 mA at 3-5 V, so it runs from the V4L tee.
  - **Corrections to the fix set:** the Uputronics bias-voltage advice is probably outdated. SDR++ now supports HydraSDR in mainline. The explicit DVB blacklist is optional, because noble's package is built with DETACH_KERNEL_DRIVER=ON, but harmless.
  - **New risk not covered by any reviewer:** HDMI pixel-clock RFI (148.5 MHz for 1080p60) inside the case. It must go into the bench noise survey.
  - **Purchase path:** delivery to Ukraine via the RTLSDRBlog AliExpress store is confirmed by RTL-SDR Blog. The official Ukrainian reseller sdr.in.ua shows 'online store temporarily not working' but still lists genuine V4 at 2,950 UAH, V3 at 2,500 UAH and Airspy R2 at 10,800 UAH, with a phone and Telegram contact. Parcels up to EUR 150 are currently exempt from duty and VAT. The Rada voted on Oct 15, 2026 to add VAT from the first euro, effective no earlier than July 2027.
- **Final recommendation:**
  - **Name:** RTL-SDR Blog V4L (Lite), dongle only (R828S + RTL2832U, 500 kHz-1.766 GHz, 2.56 MS/s, 1 ppm TCXO, 4.5 V/180 mA bias tee, HF upconverter), bought from the official RTL-SDR Blog channels. Run it on the Q6A's blue USB 3.1 port with the patched noble librtlsdr2 package.
  - **Price:** $37.95 at the official store and eBay (455 in stock on the official store, Oct 2026; ships from China). The official AliExpress store (RTLSDRBlog Store no. 4523039) is the route to Ukraine; its listing price was not verifiable. Buying 2 units (about $76) plus the $16.95 FM bandstop stays under EUR 150, so no Ukrainian duty or VAT before July 2027.
  - **Sources:**
    - https://www.rtl-sdr.com/product/rtl-sdr-blog-v4l-lite-r828s-rtl2832u-1ppm-tcxo-sma-software-defined-radio-dongle-only/
    - https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
    - https://www.rtl-sdr.com/wp-content/uploads/2026/08/RTLSDR_V4L_Datasheet4.pdf
    - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
    - https://www.rtl-sdr.com/rtl-sdr-blog-v4-end-of-line/
    - https://github.com/osmocom/rtl-sdr/commit/0204c9cfb1c5ff7bd64f466ce5b8fe53b40a636a
    - https://launchpad.net/ubuntu/+source/rtl-sdr
    - https://www.crowdsupply.com/lime-micro/limesdr-micro
    - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp
    - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
  - **Why:** Keep a second SDR.
  - **The Lime cannot cover VHF at the same time as L/S-band.** Its two RX channels share one RX LO, so it cannot take 137 MHz together with 1.7 GHz. Its matched RX paths start at 300 MHz (LNAL), so the V4L is effectively the primary VHF receiver for 137 MHz LRPT and 145.8 MHz SSTV.
  - **It is the only radio available for months.** The Lime is now $249 and ships Dec 15, 2026, so the V4L is the only radio for building the SatDump, gr-satellites and NPU pipeline until then.
  - **It is the low-power mode** (about 1.3 W versus about 4 W for the Lime).
  
  The V4L is the genuine, in-stock successor of the EOL V4. It has the best VHF/UHF MDS of the RTL family on the datasheet (about -140.7 dBm from 100-550 MHz, versus about -138 for the V3 and -137 for the V4). It keeps the upconverter, TCXO and bias tee, the bias tee can power a SAWbird NOAA (80 mA), and it costs the same as a V3.
  
  Its weaknesses are both manageable:
  - **Overload is the same as the V3.** Fix it with the FM bandstop and band-filtered LNAs placed before any gain.
  - **It needs librtlsdr with commit 0204c9c.** On Ubuntu 24.04, rebuilding noble's own package with 2 patches (verified to apply and build with SONAME .so.2) solves this cleanly.
  
  It is also hardware-compatible: USB 2.0 HS at about 5 MB/s on a dedicated controller, 250-270 mA plus up to 180 mA for the bias tee against a port switch limited to about 2.1 A, and a USB-A dongle on a short extension.
  
  Buy a spare now: the R828S stockpile is expected to last about one year.
- **Final budget option:**
  - **Name:** RTL-SDR Blog V3 (R860), dongle only, or the V3c USB-C variant. Alternative: a genuine leftover V4 from an official reseller, e.g. sdr.in.ua, if it reopens or answers by phone/Telegram.
  - **Price:** V3 / V3c dongle only: $34.95-39.95 (official stores); V3 with dipole kit: $44.95-49.95. A genuine V4 is listed at 2,950 UAH (about $71) by sdr.in.ua, whose webshop is currently paused.
  - **Why:** The V3 is in stable production and works out of the box with stock Ubuntu 24.04 librtlsdr2, with no driver build. It has the same bias tee, TCXO and overload behaviour as the V4L, at about 2-3 dB worse VHF/UHF MDS and weak direct-sampling HF, which is not a project goal. The V3c's USB-C socket lets you use a strain-relieved cable instead of a dongle hanging off the port in a handheld. It saves only about $3, so choose it only for zero driver friction or if V4L stock runs out.
  
  A genuine V4 from a listed reseller is the other good fallback. It has the best strong-signal immunity (+8 dBm vs about -24 dBm blocker tolerance at 400 MHz) and works with stock 2.0.1 packages. Never buy a 'V4' from Prom.ua, Rozetka or third-party marketplace sellers. Dropping the second SDR entirely is not advisable.
- **Known problems and fixes to apply:**
  - Driver ('deaf, only DC spike'):
  - Do NOT apt purge.
  - Run: apt-get source rtl-sdr (noble 2.0.1-2build1).
  - Add osmocom commits 0204c9c (V4L) and 65f0658 (USB-hang fix) as quilt patches.
  - In debian/rules, change $DEB_ZEROCOPY_OPTION to $(DEB_ZEROCOPY_OPTION).
  - Build with dch --local +v4l and dpkg-buildpackage -b.
  - Install, then: apt-mark hold librtlsdr2 librtlsdr-dev rtl-sdr.
  - Verify: rtl_test prints 'RTL-SDR Blog V4 Lite Detected' and objdump shows SONAME librtlsdr.so.2.
  - Never use AppImages or Flatpaks with a bundled old librtlsdr.
  - Install the rest from noble apt: soapysdr-module-rtlsdr, gr-osmosdr, gnuradio, gr-satellites 5.5.0. Install SDR++ from sdrpp_ubuntu_noble_aarch64.deb. Build SatDump master from source; there is no Ubuntu arm64 .deb. Build LimeSuiteNG (limesdr-micro branch) before SatDump so the limesdrng plugin is built. Use make -j4 to -j6 with zram to avoid freezes.
  - USB placement: use the BLUE USB 3.1 port (USB0, Bus 002). All three black USB 2.0 ports share the FE1.1s hub with the onboard Wi-Fi. Put GNSS and IMU on UART/I2C. Disable autosuspend for 0bda:2838 via a udev rule. Check with 'lsusb -t'.
  - Overload (the V4L has no triplexer or notch):
  - Order the chain antenna -> band filter or SAW-LNA -> coax -> V4L. Never put a broadband SPF5189Z or QPL9547 LNA ahead of the FM bandstop.
  - 137 MHz: SAWbird NOAA ($49.95, 80 mA from the V4L tee).
  - 145.8 MHz: FM bandstop only ($16.95, more than 50 dB rejection).
  - 435 MHz: a 435 MHz SAW-filtered LNA; check its bias-voltage spec.
  - Set gain manually with AGC off. Run the 6 dB attenuator test at each new site.
  - Conducted and radiated noise: Q6A bucks, the 4S pack, the LimeSDR and now the HDMI display (1080p60 TMDS clock 148.5 MHz, 3rd harmonic 445.5 MHz). Do a terminated rtl_power survey with each source switched on and off. Pick a display mode whose clock harmonics avoid the satellite bands. Use a short shielded HDMI link with ferrites, a ferrite on the USB extension, and keep the dongle at least 10 cm from the SoC and buck inductors. If spurs appear, feed the dongle's 5 V from a filtered rail.
  - Bench acceptance before trusting it in the field (no Q6A + SDR report exists anywhere): 15 minutes of 'rtl_test -s 2400000' under CPU, NPU, Wi-Fi and display load with zero 'lost at least' lines; then 2.56 and 3.2 MS/s margin tests; a ppm drift check after a 30-minute soak in the closed case; one real Meteor LRPT decode at 1.024 MS/s.
  - 'Stuck noisy until replug': the Q6A cannot cut VBUS in software (WS4612 EN hard-wired). Add a GPIO-driven VBUS-cut pigtail fed from the 5 V buck, normally on (AO3401A plus PNP/NPN driver). Add a pre-pass health check with the recovery ladder: re-open, usbreset, sysfs port disable/enable, then hard power cycle. Run decoders as systemd units with Restart=on-failure.
  - Two SDRs in SatDump:
  - Set unique serials: back up first with 'rtl_eeprom -r', then 'rtl_eeprom -s 00000137'. Never change the 'RTLSDRBlog' / 'Blog V4L' strings, which V4L detection depends on.
  - Run two separate SatDump CLI processes. Move liblimesdrng_sdr_support.so into /opt/satdump-lime/plugins so the RTL process never LMS_Opens the Lime.
  - Do not use one satdump_sdr_server for both (#1177 is open).
  - Heat and mechanics: keep the thermal pad and aluminium case. Give it its own vented bay away from the Q6A exhaust. Use a 10-15 cm USB-A extension with strain relief. Print the case in PETG or ASA. Use 1.024 MS/s for LRPT.
  - Bias-tee safety: the WB2HOL Yagi's hairpin match is a DC short. Enable bias only with a bias-powered LNA in line, or use a DC block.
  - Counterfeits and supply: buy only from the RTLSDRBlog AliExpress store (4523039 / 1101427871), eBay 'rtl-sdr-blog', or listed resellers. Treat Prom.ua and Rozetka 'V4' / 'HTOOL' listings as fakes. Buy 2 V4Ls now while R828S stock lasts. Keep the V3 or V3c as the long-term fallback.
- **Missed better options:**
  - RTL-SDR Blog V3c (USB-C), same price and in stable production: better for handheld mechanics (a cable instead of a dongle hanging off the port) and plug-and-play on noble, at the cost of about 2-3 dB VHF/UHF MDS and HF quality.
  - A genuine leftover RTL-SDR Blog V4 from an official reseller. sdr.in.ua (Ukraine) lists it at 2,950 UAH but its webshop is paused; it has a phone and Telegram contact. It offers the best overload immunity and stock-driver support, which suits the RF-dense Ukrainian urban environment.
  - Not better, though worth knowing: RigExpert Fobos SDR (a Ukrainian brand). It is $395-445, a wideband 14-bit USB 3.0 receiver with reported FM-band mirror and image issues and mixed Linux reviews, and it duplicates the Lime's role. Not suitable as the narrowband second SDR.
- **Remaining uncertainties:**
  - The patched librtlsdr2 recipe was verified here only on amd64 (patch application, compile, SONAME .so.2). The arm64 build on the Q6A, and actual V4L reception with the 2.0.1-based library (which lacks the 2024 r82xx fast-retune changes the V4L code was written on top of), are untested.
  - USB sample-loss, conducted noise and thermal behaviour of any SDR on a Dragon Q6A or QCS6490 board are completely unreported. The bench test will be the first data.
  - HDMI or DSI display RFI at 137-146 MHz and 435-438 MHz is inferred from standard pixel clocks, not measured. The actual mode, the bridge spread-spectrum settings and the shielding decide it.
  - The landed AliExpress price and transit time to Ukraine for the V4L were not verifiable. The $34.20 listing price is unconfirmed.
  - The Q6A 40-pin GPIO logic level (1.8 V or 3.3 V) is undocumented. The proposed VBUS-cut driver works with either, but the line mapping (gpiochip4 line 96 = pin 7, per Radxa's example) should be confirmed with gpioinfo.
  - Bias-tee voltage tolerance of the specific 435 MHz Uputronics (or other) CubeSat LNA revision.
  - LimeSDR Micro real-world VHF sensitivity, below its 300 MHz matched range, is unmeasured. If it proves good, the V4L becomes a helper rather than the primary VHF receiver.
  - How long R828S/V4L stock will last (stated as about one year), when the USB-C V4L variant will ship, and V5 timing (2027 at the earliest).
- **Confidence:** high

_Агент цього етапу ще працює (run `wf_eb446444-464`)._

