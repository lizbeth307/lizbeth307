# Wideband sdr: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_e64436d6-ae7`_

- **Component:** Wideband PCIe SDR (M.2 slot of Radxa Dragon Q6A)
- **Current pick assessment:** The LimeSDR Micro M.2 2280 is still the right choice, but two facts in v3 are out of date. (1) Price: the $199 early-bird ended in May 2026. Basic is now $249 and GNSS is $299, plus $18 worldwide shipping. (2) Timing: the first run was scheduled to ship to backers on Sept 30, 2026 (Lime's June 2026 roadmap says "fulfillment from end of September"). The Crowd Supply page now says new orders ship Dec 15, 2026, and I found no public update confirming that the first batch actually shipped. The last updates I found are dated Jun 17 and Jul 31, 2026.
  Verified specs: LMS7002M in analogue-I/Q mode, with the ADCs and DACs inside the NXP LA9310 (NXP lists 5 I/Q ADCs at up to 153 Msps; Lime says 12-bit sample depth). 30 MHz-3.8 GHz. 100 MHz bandwidth with up to 160 Msps in half-duplex/TDD mode, which covers RX-only use. 50 MHz with 61.44 Msps in FDD. Analogue filter 0.75-100 MHz. Rx gain range 89 dB. Max safe RX input +10 dBm. 1T2R: 3x MHF4 (X1 TX, X2 RX-A, X3 RX-B). RX3/RX4 come in only as analogue baseband I/Q over the 15-pin FPC, not as RF ports. PCIe Gen3 x1 on an M.2 B+M edge. 3.3 V from the slot. Card is up to ~4 mm tall.
  Caveats: (a) The RX matching networks cover only 0.3-2.2 GHz (Low), 0.7-2.6 GHz (Wide) and 3.3-3.8 GHz (High), so 137 and 145 MHz are below the matched range. Keep VHF on the RTL-SDR V4. 435 MHz, 739 MHz (QO-100 IF), 1.7 GHz and 2.2-2.3 GHz are all inside matched paths. (b) Noise figure and board power are not published. Lime says to design cooling for at least 10 W. (c) There is no bias tee. (d) The 160 Msps figure slightly exceeds NXP's 153 Msps ADC rating, and 160 Msps sc16 is 640 MB/s, more than UFS can write. The useful sustained mode is 61.44 Msps sc16 at 246 MB/s. (e) Driver support was still maturing in mid-2026: Micro support sat on a LimeSuiteNG feature branch to be merged before shipping, and Lime's roadmap item was "harden PCIe driver and streaming". On the plus side, it ran Gqrx at 40 Msps on an Arm host (Raspberry Pi CM5 in a uConsole), but QCS6490 with its SMMU is untested.
  GNSS variant ($299): adds only an Antenova M10578-A3 receiver, used today for location, time of day and a one-time VCTCXO DAC value. Lime calls GPSDO a possible future firmware feature, "not guaranteed". PPS input comes from that GNSS by default, and the docs do not say whether PPS or time is exposed to the host. The stock VCTCXO is already ±50 ppb, so the GNSS variant is not worth $50.
  The 3.8 GHz ceiling does not matter for this project. S-band (2.2-2.3 GHz) is covered natively, QO-100 comes through the LNB at ~739 MHz, and C- or X-band would need a downconverter even with a 6 GHz AD9361.
  Verdict: keep the Micro, order the Basic now, and treat its delivery and its aarch64/Qualcomm driver support as the two main risks.
- **Alternatives:**
  1.
    - **Name:** LiteX M2SDR (Enjoy Digital), SI5351C variant
    - **Key specs:** AD9361 2T2R, 70 MHz-6 GHz, 12-bit, 61.44 Msps (122.88 Msps / ~100 MHz in the RFIC-oversampling mode), Artix-7 XC7A200T, M.2 2280 M-key, PCIe Gen2 x1/x2/x4 (~14 Gbps on x4; the 122.88 Msps mode uses 7.9 Gbps and needs Gen2 x2 or x4), m2sdr kernel module (LitePCIe), SoapySDR (LiteXM2SDR), libm2sdr, GNU Radio
    - **Price:** About EUR 699 / $800-830, from cached shop listings (unverified today because the shop returned HTTP 429). The GitHub page says stock is sold out and pre-orders cost slightly more, with a new batch starting at about 50 orders.
    - **Availability:** Sold out. Pre-order only, delivery date unknown.
    - **Pros:** Most mature open PCIe SDR driver, with documented Arm host guides (Raspberry Pi 5, Orange Pi 5 Max, Jetson Orin) and a fix for zero-copy DMA under IOMMU/SMMU, which matters on Qualcomm. Reaches 6 GHz, 2 full RX channels, White Rabbit/PPS timing support.
    - **Cons:** About 3x the Micro's price. Not in stock. Only PCIe Gen2, so on the Q6A's x2 slot it gets Gen2 x2, enough for 61.44 Msps but marginal for the 122.88 mode. The 70 MHz-6 GHz range brings no satellite benefit here. Power is not published (Artix-7 200T is not low-power).
    - **Q6a compatibility:** Electrically fits: M-key and 2280, so it needs the same 2230-to-2280 extension. Gen2 x2 link. Arm-ready driver, untested on QCS6490.
    - **Sources:**
      - https://github.com/enjoy-digital/litex_m2sdr
      - https://github.com/enjoy-digital/litex_m2sdr/blob/main/doc/hosts/raspberry-pi-5.md
      - https://enjoy-digital-shop.myshopify.com/products/litex-m2-sdr-si5351c
  2.
    - **Name:** HamGeek M2SDR (Chinese AD9361 M.2 board, SKU 101071)
    - **Key specs:** XC7A200 + AD9361, M.2 PCIe (x1 lane-mode firmware option), onboard GPSDO with active GPS antenna input, external PPS input, 40 MHz clock output, UHD 4.2-4.9 in 'B210 mode', Linux PCIe driver for Ubuntu 18.04-25.04, Arm support claimed (Raspberry Pi, Orange Pi, RK3588)
    - **Price:** $376 on hgeek.com, plus 4PX shipping (10-20 days). Duties not included.
    - **Availability:** Out of stock on hgeek.com as of this check. I could not verify an AliExpress listing.
    - **Pros:** Cheapest AD9361 M.2 PCIe card found. A real GPSDO onboard, which could replace the separate GNSS module for timing. UHD compatibility means SatDump and GNU Radio work through UHD as well as SoapyUHD.
    - **Cons:** Out of stock. The listing gives no clear frequency range, sample rate or PCIe lane/gen specs. It notes a known TX bug below 1.9 MS/s. Software quality and long-term support are unknown. Clone-board risk.
    - **Q6a compatibility:** Probably fits the M-key slot through an extension, but size and keying are not stated. Arm support claimed, untested on QCS6490.
    - **Sources:**
      - https://www.hgeek.com/products/hamgeek-m2sdr-software-defined-radio-m-2-xc7a200-rf-transceiver-module-gpsdo-40m-clock-output
      - https://www.hgeek.com/products/hamgeek-libresdr-m2sdr-software-defined-radio-development-board-xc7a200t-ad9361-support-hot-swapping-2
  3.
    - **Name:** Wavelet Lab xSDR
    - **Key specs:** LMS7002M 2x2 MIMO, 30 MHz-3.8 GHz, 0.1-122.88 Msps SISO / 80+ Msps MIMO, 0.5-90 MHz channel bandwidth, Artix-7 (XC7A50T or XC7A35T; the page is inconsistent), M.2 2230 A+E key, PCIe 2.0 x2 plus USB 2.0, 4x MHF4, 0.5 ppm clock, SoapySDR, GNU Radio
    - **Price:** $549 (the page's comparison table says $649), plus $18 worldwide. M.2-to-PCIe breakout $89-99.
    - **Availability:** Funded Mar 26, 2026. Pre-orders ship Oct 30, 2026. 'Limited items in stock.'
    - **Pros:** 2230 size fits the Q6A without an extension. 4 RF ports. 122.88 Msps.
    - **Cons:** A+E keying means an A+E-to-M adapter is needed for the Q6A's M-key slot (lane mapping uncertain). More than twice the Micro's price. Kernel driver and Arm support are not stated. No DSP offload.
    - **Q6a compatibility:** Mechanically good (2230) but keyed wrong. Needs an adapter, and PCIe Gen2 x2 through it is unverified.
    - **Sources:**
      - https://www.crowdsupply.com/wavelet-lab/xsdr
  4.
    - **Name:** LimeSDR XTRX
    - **Key specs:** LMS7002M 2T2R, 30 MHz-3.8 GHz, 120 Msps SISO / 90 Msps MIMO, 120 MHz bandwidth, 12-bit, Mini PCIe, LimeSuiteNG limepcie driver
    - **Price:** $960, free US shipping or $18 worldwide. LimeFEA mPCIe Lite adapter $49.
    - **Availability:** In stock, ships within 3 business days.
    - **Pros:** Shipping now, with the same LimeSuiteNG stack as the Micro.
    - **Cons:** Nearly 4x the Micro's price. Mini PCIe form factor needs an mPCIe-to-M.2 adapter. Arm users have reported DMA problems: on a Pi 5 it needed the pcie-32bit-dma overlay, and one user still could not get it to work.
    - **Q6a compatibility:** Poor. Needs an mPCIe-to-M.2 M-key adapter (probably x1 only), and the Arm DMA issues are documented.
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-xtrx
      - https://discourse.myriadrf.org/t/xtrx-not-found/8386/18
  5.
    - **Name:** Fairwaves XTRX (original)
    - **Key specs:** LMS7002M, Mini PCIe
    - **Price:** n/a
    - **Availability:** Discontinued, replaced by LimeSDR XTRX. Used units only.
    - **Pros:** Was cheap (about $200) when new.
    - **Cons:** Not purchasable new. Old driver stack.
    - **Q6a compatibility:** Same mPCIe adapter problem as the LimeSDR XTRX.
    - **Sources:**
      - https://limemicro.com/news/lime-micro-opens-orders-for-the-limesdr-xtrx-an-open-hardware-mpcie-software-defined-radio
      - https://www.rtl-sdr.com/xtrx-soon-to-be-crowdfunding-mini-pcie-based-txrx-sdr/
  6.
    - **Name:** Epiq Sidekiq M.2 / Sidekiq Stretch
    - **Key specs:** Sidekiq M.2: AD9361 + Artix-7, 70 MHz-6 GHz, M.2 3042 B+M, 2.1 W typical. Stretch: AD9361 1R1T, 50 MHz per channel, 12-bit, PCIe Gen2 x1, M.2 2280 B+M, 2.5 W typical, integrated GPSDO, tunable RX preselect filters.
    - **Price:** Not published. Quote or dev kit only through Epiq's contact form.
    - **Availability:** Professional/defense channel. Realistically not obtainable by a hobbyist in Ukraine.
    - **Pros:** Lowest published power (2.1-2.5 W). Preselect filters and GPSDO on the Stretch.
    - **Cons:** No public price. Export and sales channel barriers. Proprietary libsidekiq stack.
    - **Q6a compatibility:** Stretch would fit electrically (2280 B+M, Gen2 x1), but it is not a realistic purchase.
    - **Sources:**
      - https://epiqsolutions.com/products/sdr/sidekiq-m.2
      - https://epiqsolutions.com/products/sdr/sidekiq-stretch
  7.
    - **Name:** Wavelet Lab uSDR
    - **Key specs:** LMS6002D 1T1R, 300-3700 MHz, up to 30.72 Msps, 0.75-28 MHz bandwidth, M.2 2230 A+E (USB 2.0 or PCIe legacy), Linux 5.4+ GPL PCIe driver, SoapySDR
    - **Price:** $359. M.2 B+M adapter $12.
    - **Availability:** Pre-order, ships Feb 28, 2027.
    - **Pros:** Tiny. Cheap B+M adapter. Web UI.
    - **Cons:** Only about 28 MHz bandwidth, so it misses the 56-100 MHz goal. Starts at 300 MHz. Ships in 2027. Costs more than the Micro.
    - **Q6a compatibility:** Would work with the $12 B+M adapter, but it is a step down.
    - **Sources:**
      - https://www.crowdsupply.com/wavelet-lab/usdr
  8.
    - **Name:** USB3 alternative: Nuand bladeRF 2.0 micro xA4
    - **Key specs:** AD9361 2x2, 47 MHz-6 GHz, 61.44 Msps (122.88 possible), 56 MHz usable bandwidth, USB 3.0, bus-powered, software-controlled bias tee on every RF port
    - **Price:** $540
    - **Availability:** In stock (ships in 1-2 business days).
    - **Pros:** In stock. Bias tees built in, which removes the external bias tee for the L-band LNA. Mature libbladeRF and SoapySDR support on Arm. Leaves the M.2 slot free for a 2230 NVMe SSD (Radxa measured about 1467 MB/s write), so there is no UFS write bottleneck.
    - **Cons:** More than twice the Micro's price. The Q6A's single USB 3.1 port (5 Gbps) has no published sustained-throughput test, and 61.44 Msps sc16 at 246 MB/s is unproven on the QCS6490 DWC3 controller. Larger than an M.2 card.
    - **Q6a compatibility:** Plugs into the only USB 3.1 port. Throughput at 56-61 Msps is unverified. A 'dedicated Renesas USB3 controller' would itself have to sit in the M.2 slot, so it gains nothing over a PCIe SDR.
    - **Sources:**
      - https://www.nuand.com/product/bladerf-xa4/
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/usb
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/nvme
  9.
    - **Name:** USB3 alternative: LibreSDR B220 mini (AD9361 + XC7A200T, B210-compatible clone)
    - **Key specs:** AD9361 2R2T, 70 MHz-6 GHz, 12-bit, 61.44 Msps, USB 3.0 Type-C, 10 MHz reference and PPS inputs, onboard VCTCXO (±0.5 ppm per the seller), UHD/B210 firmware
    - **Price:** EUR 447.84 at sdrstore.eu (EU, in stock). About $250-330 on eBay listings (XC7A100T/200T versions).
    - **Availability:** In stock at the EU shop. eBay stock varies.
    - **Pros:** Widely sold clone. Works with UHD, SatDump, GNU Radio and SDR++ through SoapyUHD. External 10 MHz/PPS. Frees the M.2 slot for NVMe.
    - **Cons:** Same unverified Q6A USB3 throughput. Clone quality and firmware vary (sellers mix up B210/B220 naming). No bias tee.
    - **Q6a compatibility:** Same as the bladeRF: depends on the Q6A's USB 3.1 port sustaining about 246 MB/s, which is unverified.
    - **Sources:**
      - https://www.sdrstore.eu/software-defined-radio/instruments/plutosdr/70mhz-6ghz-2r2t-b210-mini-ad9361-sdr-development-board-libresdr-uhd-pluto-oai-support/
      - https://www.ebay.de/itm/176489014212
- **Recommended:**
  - **Name:** LimeSDR Micro M.2 2280 Basic (no GNSS), plus 2-3 MHF4L-to-SMA(f) bulkhead cables
  - **Why:** It is still the cheapest wideband PCIe SDR I could verify that is open, sold to the public and the right form factor for the Q6A. Key: B+M card into the M-key slot. Bandwidth: Gen3 x1 at ~985 MB/s easily carries 61.44 Msps on 2 channels (~492 MB/s sc16). Range: 100 MHz receive bandwidth, two RX ports, 3.8 GHz. That covers 435 MHz, the 739 MHz QO-100 IF, 1.7 GHz HRPT and 2.2-2.3 GHz S-band through matched paths, so you can leave the helix on RX-A and the LNB IF on RX-B. It has the lowest likely power of the PCIe options (LA9310 1.5 W max; LMS7002M 0.55-0.88 W typical), with optional VSPA DSP offload later. Every alternative is either 2-4x the price (M2SDR about $800, xSDR $549, bladeRF $540, XTRX $960), out of stock (M2SDR, HamGeek), or narrower (uSDR). Skip the GNSS variant: it adds only an Antenova receiver for location, time and one-time VCTCXO calibration, and GPSDO is 'not guaranteed'. A $2-20 ATGM336H or u-blox M10 module is cheaper and is needed for the pointing UI anyway. Order now, since new orders ship Dec 15, 2026. If it slips past about Q1 2027 or the driver fails on QCS6490, fall back to the LiteX M2SDR (best Arm/SMMU driver support) or a USB3 AD9361 board.
  - **Price:** $249 + $18 worldwide shipping = $267. MHF4L-SMA cables $6 each, about $12-18. Total about $280-285 before Ukrainian import VAT or duty, which I did not verify.
  - **Sources:**
    - https://www.crowdsupply.com/lime-micro/limesdr-micro
    - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
    - https://myriadrf.org/projects/limesdr-micro/user/M.2/clock.html
    - https://openairinterface.org/wp-content/uploads/2026/06/Summer-2026-OAI-Workshop-Ricardas.pdf
    - https://myriadrf.org/stories/ota-limesdr-micro-uconsole-cyberether-web-lunar-ctf-more/
    - https://nxp.com/docs/en/fact-sheet/LA9310-FS.pdf
- **Budget option:**
  - **Name:** Defer the wideband card and run the RTL-SDR V4 alone first. If a card has to be bought now, the Micro Basic ($249) is still the cheapest verified wideband PCIe option.
  - **Why:** No wideband M.2 SDR cheaper than the Micro Basic was verifiable in Oct 2026. The HamGeek M2SDR ($376, out of stock) and the LibreSDR B220 mini (about $250-330 on eBay, USB3) are not cheaper and are riskier. Most listed downlinks need under 3 MHz of bandwidth. The RTL-SDR V4 already in the stack covers 137 MHz LRPT, 145.8 SSTV and 435-438 CubeSats. It also covers the QO-100 narrowband transponder through the LNB IF (about 739 MHz). It is commonly reported to decode Meteor HRPT at 1.7 GHz at about 2.4-3.2 Msps, but I did not re-verify that here. What it cannot do: S-band 2.2 GHz (above its ~1.77 GHz limit), full-rate Metop/FengYun AHRPT (needs about 6 Msps or more) and the 56-100 MHz live view. So the budget path is $0 extra now and adds the Micro when it actually ships.
  - **Price:** $0 extra now. Later $267 for the Micro Basic shipped.
- **Risks:**
  - Delivery: the first manufacturing run was scheduled for Sept 30, 2026. New orders now show 'ships Dec 15, 2026'. As of Oct 17, 2026 I found no public update confirming that units shipped. The latest updates I found are Jun 17 and Jul 31, 2026.
  - Price creep: the $199 early-bird ended in May 2026, and Basic is now $249. The Micro Pro dropped from $799 to $749, so pricing is still moving.
  - Driver maturity: Micro support lived on a LimeSuiteNG feature branch (to be merged before shipping). Lime's June 2026 roadmap lists 'Harden LimeSuiteNG PCIe driver and streaming' as current work. OAI is validated on x86 only.
  - Arm/Qualcomm DMA: limepcie has a history of 32/64-bit DMA trouble on Arm. The XTRX on a Pi 5 needed dtoverlay=pcie-32bit-dma and still failed for one user. LiteX M2SDR documents zero-copy DMA bugs under an active SMMU. The QCS6490 has an Arm SMMU, so expect iommu.passthrough=1 or other tweaks. DKMS needs kernel headers for the Radxa/Qualcomm kernel. None of this is tested on the Q6A.
  - M.2 extension: running PCIe Gen3 (8 GT/s) over a 2230-to-2280 extender or ribbon can cause link errors. You may have to force Gen2, which still gives about 500 MB/s, enough for 61.44 Msps sc16 at 246 MB/s but not for 160 Msps.
  - Power/thermal: board power is not published (listed as 'TBC'). Lime says to design cooling for at least 10 W. The Q6A M.2 3.3 V rail current limit is undocumented. Radxa recommends a 24 W (12 V/2 A) supply or more when PCIe and USB3 are loaded.
  - RF: the RX matching networks start at 300 MHz, so 137/145 MHz sensitivity on the Micro will be poor. No published noise figure. No bias tee. Absolute max RX input is +10 dBm, so an LNA plus a strong local signal can hurt the front end. Use an FM stopband filter and keep LNA gain sane.
  - Spec claims: 160 Msps exceeds the 153 Msps ADC rating in NXP's LA9310 fact sheet, and it is only available in half-duplex/TDD mode. At 640 MB/s (sc16) it is far above UFS write speed (Radxa dd results: Samsung 128 GB 388 MB/s, Kioxia 256 GB 557 MB/s). 160 Msps captures will be RAM-buffered bursts (16 GB is about 20 s).
  - Mechanical: the card is non-standard height (up to about 4 mm components) and 80 mm long, which overhangs the 85x65 mm Q6A. It needs a mount and a heatsink in the case.
  - Import: the Crowd Supply parcel goes to Ukraine from the US with $18 shipping. I did not verify Ukrainian VAT or customs rules for Oct 2026.
  - Research limit: the web-search budget ran out during this task. M.2 extender prices, Ukrainian store stock, AliExpress M2SDR listings and the live Enjoy Digital price (HTTP 429) could not be verified.
- **Integration notes:**
  - Slot: the Micro is an M.2 2280 B+M card and the Q6A slot is M-key 2230 PCIe Gen3 x2, so it is electrically compatible and the link trains as x1. Use a Gen3-rated M.2 M-key extender or flex ribbon and mount the card on the case. Keep the ribbon short.
  - Ports: X2 (RX-A) to the 1.7 GHz helix LNA chain (Low or Wide path). X3 (RX-B) to the QO-100 LNB IF at about 739 MHz, or to S-band. X1 (TX) unused, which suits receive-only. VHF and UHF CubeSats can stay on the RTL-SDR V4 to avoid the unmatched VHF range.
  - Cables: buy 2-3 MHF4L-to-SMA(f) bulkhead cables ($6 each, Crowd Supply). One more is optional for the PPS input on MHF4 J5.
  - Bias tee: the Micro has none. Add an external SMA bias tee fed from the 5 V rail for the L-band LNA. The RTL-SDR V4's built-in bias tee can power the VHF/UHF LNA.
  - Software: build LimeSuiteNG (Micro support merged to main by shipping) with the limepcie kernel module through DKMS on Ubuntu 24.04 aarch64. Install kernel headers for the Q6A kernel first. Use the LimeSuiteNG SoapySDR plugin for SatDump and SDR++, and gr-limesuiteng for GNU Radio. On first bring-up check dmesg for SMMU faults and try iommu.passthrough=1 if DMA returns no samples.
  - Data rates: 61.44 Msps sc16 is about 246 MB/s per channel, and 2-channel MIMO about 492 MB/s, both inside Gen3 x1 (~985 MB/s). Record to the 256 GB Kioxia UFS module (Radxa measured 557 MB/s write), not the 128 GB Samsung (388 MB/s), to leave margin for 56-61 Msps IQ.
  - Power: budget 5-10 W extra on the Q6A's 12 V input. Radxa recommends 24 W or more with PCIe and USB3 loaded. Size the 4S-to-12 V converter and PD source for about 30-35 W peak including the display.
  - Thermal: put a thermal pad and an aluminium heatsink on the LA9310 and LMS7002M, in the fan's airflow. Watch the TMP1075 temperature sensor through LimeSuiteNG. The commercial operating range is 0-85 °C.
  - Clock: the onboard 30.72 MHz VCTCXO is ±50 ppb, about 85 Hz at 1.7 GHz, which is fine for HRPT. External reference input accepts 10-52 MHz. Using an external PPS (for example from the ATGM336H or u-blox M10) needs a resistor change: remove R176 and fit R179 on v1.1/v1.2 boards.
- **Double duty opportunities:**
  - Skip the $299 GNSS variant. A $2-20 ATGM336H or u-blox M10 serves the pointing UI and gpsd and can also feed PPS into the Micro's MHF4 J5 input after the resistor change. One part does both jobs for less.
  - Two RX ports on one card: leave the 1.7 GHz helix and the QO-100 LNB IF permanently connected to RX-A and RX-B and switch in software. No cable swapping in the field, and no RF switch to buy.
  - LA9310 VSPA (80 GFLOPs) can later run FFT, FIR and channelization on the card ('Next' on Lime's roadmap). That would offload the Q6A CPU and leave the Hexagon NPU free for the modulation classifier.
  - Choosing a USB3 SDR such as the bladeRF xA4 instead would free the M.2 slot for a 2230 NVMe SSD (about 1467 MB/s write, per Radxa), removing the UFS write bottleneck. The bladeRF's built-in bias tees would also replace the external bias tee. That trade only makes sense if Q6A USB 3.1 throughput turns out to be good.
  - The HamGeek M2SDR clone ($376, when in stock) has an onboard GPSDO plus a PPS input, so it could double as the timing and GNSS source. Unlike the Lime GNSS variant, its GPSDO is a real, existing feature.
- **Confidence:** medium

_Run `wf_feb0e95a-cfc`_

- **Subsystem:** wideband_sdr: LimeSDR Micro M.2 2280 (conditional, gate C1)
- **Findings:**
  1.
    - **Claim in stack:** C1/BOM 2.11: Crowd Supply pre-order, ships 15.12.2026; decide by 1.12.2026; full refund only before shipment.
    - **Finding:** The Crowd Supply page (checked 18 Oct 2026) shows Basic and GNSS as 'Pre-order' with 'Orders placed now ship Dec 15, 2026'. The campaign raised $119,875 from 130 backers and closed May 28, 2026. The last of its 8 updates is dated Jun 17, 2026 ('component sourcing has started… ship in September'). No update or forum post confirms that the Sept 30, 2026 first run actually shipped. Crowd Supply policy says stock and pre-orders 'can be canceled and fully refunded any time before they ship'. Dec 15 is an estimate, so the date can move either way. If stock arrives early, shipment could come before the 1 Dec decision and close the free-cancel window.
    - **Verdict:** confirmed
    - **Action:** Keep the 1.12.2026 gate, but check the order status weekly, and decide at once if Crowd Supply announces shipping. Treat a shipping email as the effective deadline.
    - **Impact:** The only free exit depends on shipping not happening before the decision.
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
      - https://www.crowdsupply.com/lime-micro/limesdr-micro/updates
      - https://www.crowdsupply.com/returns
  2.
    - **Claim in stack:** BOM: LimeSDR Micro M.2 2280 Basic + $18 shipping + 2x MHF4L-SMA = $279 (verified).
    - **Finding:** Prices are confirmed: Basic $249, GNSS $299, $18 worldwide shipping, and MHF4L-to-SMA(f) bulkhead cable $6 (in stock; 100 mm, 1.13 mm coax, MHF-4L plug). The $279 total is right for 2 cables. However, the panel plan with Lime has RX1, RX2 and REF IN, and the TX port is to be closed with 50 Ohm. That needs 3-4 cables, or 3 cables plus an MHF4 terminator. Import VAT and duty are the buyer's responsibility (Crowd Supply shipping page).
    - **Verdict:** corrected
    - **Action:** Change the BOM line to 3x MHF4L-SMA ($285), or 4x if TX is terminated through a cable and an SMA 50 Ohm load ($291). Keep duties out of the totals as the stack already does.
    - **Impact:** +$6-12.
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
      - https://www.crowdsupply.com/shipping
  3.
    - **Claim in stack:** Board model and revision implied: v1.x, module height ~4 mm, pedestal with a >=6 W/mK thermal pad.
    - **Finding:** Current docs list M.2 board revisions v1.0, v1.1 and v1.2 (v1.2 docs added 22 Jun 2026), all treated the same in software. The v1.2 changelog adds: boot from the I2C EEPROM by default (JP1 selects ROM boot for recovery), SMBus pins, and LMS RBB routed to ADCIN for DC/RSSI calibration. It also states that top-side parts (VCTCXO, RF baluns, RF shield) are 'up to 4.5mm', while Crowd Supply says ~4 mm. The bottom side meets D3 (<=1.35 mm).
    - **Verdict:** corrected
    - **Action:** Design the pedestal, the shield-lid clearance and the riser stack for 4.5 mm top-side height. Record the delivered board's revision (HW_VER) at bring-up.
    - **Impact:** Mechanical clearance; 0.5 mm more than planned.
    - **Sources:**
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/changelog.html
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/versions.html
  4.
    - **Claim in stack:** #87/#88: maker's range 30 MHz-3.8 GHz; matched RX 0.3-2.2 (LNAL), 0.7-2.6 (LNAW), 3.3-3.8 GHz (LNAH); below 300 MHz unmatched and untested; 137/145.8 MHz always on RTL.
    - **Finding:** Confirmed by the docs table and by code: LimeSDR_Micro.cpp sets antennaRange LNAH {3.3e9,3.8e9}, LNAL {0.3e9,2.2e9}, LNAW {0.7e9,2.6e9}, while the software frequencyRange stays at the LMS7002M default of 100 kHz-3.8 GHz. On 13 Oct 2026 Lime (andrewback, forum t/13348) said: 'There are no gaps in frequency coverage'; the listed bands only show where the matching networks are optimised. No noise-figure or sensitivity data exists below 300 MHz or for 2.6-3.3 GHz.
    - **Verdict:** confirmed
    - **Action:** Keep the rule (Lime 'Tune' from 300 MHz; 137/145.8 MHz on RTL). Treat 2.6-3.3 GHz like the sub-300 MHz range: covered but unmatched and uncharacterised.
    - **Impact:** None on the plan.
    - **Sources:**
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/rfcontrol.html
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp
      - https://discourse.myriadrf.org/t/13348
  5.
    - **Claim in stack:** Lime sessions on L-band, S-band and GNSS are decimated to <=1 Msps by labrx; LIME-W/F/B profiles at 56 Msps.
    - **Finding:** In the driver the sample-rate range is {7e6, 160e6}, with the comment 'going below 7MHz without decimation introduces noise'. The firmware also rejects an LA9310 system clock below 15 MHz. So the Micro cannot natively stream at 1-3 Msps for narrow sessions. It must run at >=7 Msps (28 MB/s per channel, ci16), and labrx decimates on the host. The FDD limit is 61.44 Msps; 160 Msps is half-duplex or TDD only.
    - **Verdict:** new_risk
    - **Action:** Set every Lime narrow profile to >=7 Msps with host decimation. Add the extra ingest (28 MB/s per channel) and its CPU cost to the Lime load model. Check that SatDump's Lime source does not offer rates below 7 Msps.
    - **Impact:** Small CPU and memory-bandwidth increase. A profile set below 7 Msps would fail or give noisy data.
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
  6.
    - **Claim in stack:** Two RX share one LO, so 739 MHz and 1.7 GHz at the same time is impossible.
    - **Finding:** This matches the LMS7002M architecture: one RX synthesiser (SXR) drives both RX channels. The bandwidth is 100 MHz TDD or half-duplex and 50 MHz FDD, so 739 MHz and 1.7 GHz cannot fit in one capture. A recent staging commit ('Fix LMS7002M SDRDevice LO frequency config if first channel is not used', 10 Sep 2026) also handles LO setup per direction. I did not re-fetch the LMS7002M datasheet in this pass.
    - **Verdict:** confirmed
    - **Action:** No change.
    - **Impact:** —
    - **Sources:**
      - https://github.com/myriadrf/LMS7002M-docs
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
  7.
    - **Claim in stack:** #69: absolute max Lime input +10 dBm; 10-12 dB attenuators after SAWbird; DC blocks on each port.
    - **Finding:** Confirmed. The setup page warns that 'the maximum safe input power of +10 dBm' must not be exceeded. The Micro has no bias tee.
    - **Verdict:** confirmed
    - **Action:** Keep the attenuators. Do not put DC blocks or attenuators on REF IN or PPS: those are CMOS logic inputs (see the next item).
    - **Impact:** —
    - **Sources:**
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
  8.
    - **Claim in stack:** #69/P7: REF IN on J4 (external reference experiment); limeConfig is allowed only with refclk options.
    - **Finding:** The spec is confirmed: external clock input on M.2 pin 28 or MHF4 J4, 10-52 MHz, 1.8-3.3 V CMOS. The onboard Rakon E6245LF 30.72 MHz VCTCXO is ±50 ppb over temperature, but the factory calibration is only ±1 ppm and ageing is ±2 ppm in the first year. New problem: firmware issue #6 (opened 9 Oct 2026, still open). The external-reference select writes MCP23017 register 0x09 (INTCONB) instead of OLATA (0x14), so 'the reference clock never switches' while the command still reports success. The fix (commit 1f70189, 16 Oct 2026) is only on the LimeSDR-Micro_FW staging branch. It is not in master, and not in the limesdr-micro-m4.bin bundled with LimeSuiteNG staging (that firmware was last updated 16 Oct at 01:43, before the fix). The host loads the M4 firmware from /lib/firmware/limesdr-micro-m4.bin each time the device is opened, so it can be updated without flashing.
    - **Verdict:** new_risk
    - **Action:** Before P7, install an M4 firmware that contains 1f70189: build it from LimeSDR-Micro_FW staging or wait for a merge, and pin its hash in the lab manifest. Prove the switch with a measured frequency offset (for example, a deliberately offset reference). Drive J4 with a 1.8-3.3 V CMOS square wave, never a 50 Ohm sine through a DC block or pad.
    - **Impact:** Without the fix, P7 would silently run on the internal TCXO and give false calibration results.
    - **Sources:**
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/clock.html
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/clock.html
      - https://github.com/myriadrf/LimeSDR-Micro_FW/issues/6
      - https://github.com/myriadrf/LimeSDR-Micro_FW/commit/1f701897ca1a9e91c0ba4a6d6d573d977a7bfe72
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp
  9.
    - **Claim in stack:** #83: do not buy the GNSS variant (+$50) because the firmware does not pass NMEA, PPS or GPSDO regulation; P5 'Lime VCTCXO steering from GPS' is optional.
    - **Finding:** The +$50 is confirmed ($299 vs $249). The reason has changed. Crowd Supply says the GNSS receiver 'may be used for location, time of day, and generating a VCTCXO DAC value', with GPSDO 'not guaranteed'. On 16 Oct 2026 the firmware staging branch added 'initial PPSDO support' (ppsdo.c, 454 lines): it measures PPS_IN over 1, 10 and 100 s windows, discards intervals more than 100 ppm off, and trims the VCTCXO DAC. LimeSuiteNG develop refactored host PPSDO code on 2 Oct 2026 (for LimeSDR USB). I found no NMEA path in the host code.
    - **Verdict:** corrected
    - **Action:** Keep the decision (no GNSS variant; the separate LC76G stays). Rewrite the reason as: 'PPSDO is only initial and staging-only (Oct 2026); no NMEA path to the host; external PPS can be used instead.'
    - **Impact:** Saves $50; the earlier wording is out of date.
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
      - https://github.com/myriadrf/LimeSDR-Micro_FW/commit/ee1acd02d29f3f80838450f4eadd63376da68c90
  10.
    - **Claim in stack:** P5/P7: Lime frequency reference comes from REF IN (LBE-1420 in extended) or a PPS counter.
    - **Finding:** New option: feed the LC76G's 3.3 V PPS into Lime J5 (MHF4) and let the new PPSDO firmware discipline the VCTCXO. That needs no 10 MHz source. On v1.1 and v1.2 boards J5 must be selected as the PPS input by removing R176 and fitting a 0 Ohm at R179 (by default PPS comes from the onboard GNSS footprint, which is not fitted on Basic). A reworked board can no longer go back under the 30-day RMA.
    - **Verdict:** new_option
    - **Action:** Add an optional P7b to run only after the acceptance tests pass: rework R176 to R179, split the LC76G PPS through a buffer to J5 and pin 7, enable PPSDO, and compare against the GNSS-SDR ppm.
    - **Impact:** Could make the LBE-1420 unnecessary for the Lime. The firmware is immature (staging).
    - **Sources:**
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/clock.html
      - https://github.com/myriadrf/LimeSDR-Micro_FW/commit/ee1acd02d29f3f80838450f4eadd63376da68c90
  11.
    - **Claim in stack:** C1: 'arm64 driver not verified'.
    - **Finding:** Partly out of date. Lime demonstrated the Micro on arm64: a ClockworkPi uConsole with a Raspberry Pi CM5 ran Gqrx at 40 Msps (update of 17 Jun 2026; story of 31 Jul 2026). Nothing has been published for Qualcomm QCS6490, and LimeSuiteNG CI builds only ubuntu-22.04/24.04 x86, Windows and macOS (no arm64). In mainline kodiak.dtsi, pcie1 is 'dma-coherent' with an iommu-map to apps_smmu. The driver uses the DMA API with a 64-bit mask, falling back to 32-bit.
    - **Verdict:** corrected
    - **Action:** Reword as: 'arm64 shown by Lime on Pi CM5 at 40 Msps; QCS6490 with SMMU untested; no arm64 CI'. Keep the bring-up checks (dmesg for arm-smmu faults, link status) in the W gate.
    - **Impact:** Lower risk than stated, but still not proven on the Q6A.
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro/updates/thanks-and-uconsole-gqrx-demo
      - https://myriadrf.org/stories/ota-limesdr-micro-uconsole-cyberether-web-lunar-ctf-more/
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro-staging/.github/workflows
      - https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/kodiak.dtsi
  12.
    - **Claim in stack:** 5.4/#30: LimeSuiteNG from limesdr-micro-staging; la9310-limesdr-dkms+lab built with -DBUILD_PLUGINS_AMARISOFT=OFF.
    - **Finding:** Micro support exists only on limesdr-micro-staging (head 37cb1833, 16 Oct 2026) and on limesdr-micro (80ffad5c, 1 Oct 2026). Staging is 206 commits ahead of develop and is not merged. The only release tag is v25.1.0 (28 Jan 2025), which has no Micro support. Basic streaming is still being fixed: Rx timestamp recovery after overruns (16 Oct), stream pacing (9 Oct), BAR release on unload (1 Oct), IRQ handler before interrupt enable (28 Sep), multi-channel Rx (10 Sep). The kernel module is la9310_limesdr 0.2.1, installed through CMake with LA9310_LIMESDR_DKMS. The Debian packaging builds only limepcie-dkms; no upstream la9310 DKMS .deb exists. debian/rules already passes -DBUILD_PLUGINS_AMARISOFT=FALSE. The module has a class_create branch for kernels >=6.4; a build against 6.18 has not been shown.
    - **Verdict:** corrected
    - **Action:** Describe la9310-limesdr-dkms+lab as a local package built from the CMake DKMS output. Pin both the LimeSuiteNG commit and the M4/VSPA firmware hash. Add a CI job that compiles the module against the linux-headers-6.18.2-4-qcom headers before the 1.12 gate.
    - **Impact:** Software is pre-release; expect API and firmware churn at delivery.
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro-staging
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/debian/control
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/drivers/linux/la9310_limesdr/CMakeLists.txt
  13.
    - **Claim in stack:** #21: PCI class fixup (1957:1c10, 1957:1c12, 2058:001d -> 0x118000) if BARs do not come up.
    - **Finding:** The IDs match the driver's pci_device_id table. The driver also has FixBARResources(), which calls pci_assign_resource() for BARs left unassigned because 'LA9310 ROM bootloader PCI descriptor has a PCI class type of 00'. v1.2 boards boot from EEPROM by default; the docs were fixed on 17 Sep 2026 for the PCIe-boot device ID. An early class quirk is still the safer route, because a late assignment can fail if the bridge window was sized without the device's BARs.
    - **Verdict:** confirmed
    - **Action:** Keep the fixup as a fallback, applied only if lspci shows unassigned BARs.
    - **Impact:** —
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/drivers/linux/la9310_limesdr/la9310_pci.c
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/changelog.html
  14.
    - **Claim in stack:** #21: M.2 on pcie1 works; no BAR-space constraint noted.
    - **Finding:** A driver comment says 'Default BAR0 size is 256MB', and warns that shrinking it can cause an 'Imprecise bus access' fault on the M4. In mainline kodiak.dtsi, pcie1 has only one 32-bit memory window: 0x40300000, size 0x1fd00000 (509 MiB). My model: a 256 MiB-aligned BAR0 fits only at 0x50000000-0x5FFFFFFF, which is exactly the top of the window, leaving 253 MiB below for BAR1 (16 MiB TCM) and BAR2. It should fit, but with no margin. Radxa's 6.18-qcom device tree may differ.
    - **Verdict:** new_risk
    - **Action:** Check the pcie1 ranges in the Radxa DT now (dtc -I fs /sys/firmware/devicetree). At first bring-up, check for 'BAR 0: no space' in dmesg and the lspci -vv BAR sizes. Do not shrink BAR0.
    - **Impact:** If the Radxa window is smaller, the device would not probe.
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/drivers/linux/la9310_limesdr/la9310_pci.c
      - https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/kodiak.dtsi
  15.
    - **Claim in stack:** #21: Q6A M.2 2230 M-key, Gen3 x2 on pcie1; Lime trains x1; separate ETA3521 4 A 3.3 V rail.
    - **Finding:** Radxa docs confirm 'M.2 M Key 2230 Slot' with 'PCIe Gen3 x2' (NVMe reference 1649 MB/s read, 1467 MB/s write). The Lime is M.2 2280 B+M with 'one-lane PCIe Gen 3' and needs host 3.3 V. The ETA3521 datasheet confirms a 2 MHz, 4 A synchronous buck with 2.5-6 V input. The U20/VCC_3V3_MKEY detail comes from the Radxa v1.21 schematic and was not re-opened in this pass.
    - **Verdict:** confirmed
    - **Action:** No change. About 1.2 A typical Lime draw (next item) is well inside the 4 A rating.
    - **Impact:** —
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/nvme
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
      - https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2403151643_etasolution-ETA3521FSG_C22362743.pdf
  16.
    - **Claim in stack:** Thermal/power: a 10 W heat path through the pedestal; Lime about 4 W typical with 8.25 W allowance; VCC_5V_PERI gate <=14 W.
    - **Finding:** Lime docs: 'the LimeSDR Micro M.2 cooling solution should be designed to dissipate at least 10 W'. Lime staff (Zack, forum t/13304, 24 Aug 2026) said 2.5 A x 3.3 V 'is taken from PCIe specification… Board should consume about 4 W, depending on configuration'. No idle figure was given. Board temperature (TMP1075) is exposed as a LimeSuiteNG custom parameter. No operating-temperature range is published on the product or docs pages.
    - **Verdict:** confirmed
    - **Action:** Keep the 10 W path and the 14 W gate. Log the TMP1075 board temperature through labd. Measure idle and 56 Msps power at acceptance. Mark the operating range 'not published'.
    - **Impact:** —
    - **Sources:**
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
      - https://discourse.myriadrf.org/t/13304
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp
  17.
    - **Claim in stack:** #69/#133: ADT-Link R44SF 5 cm riser, $19 (verified); shielded.
    - **Finding:** The ADT-Link page lists R44SF 'M.2 NVMe to M.2 NVMe Extender', 'PCIe 3.0 x4 full speed', 5 cm $19.00 (3 cm $21, 10 cm $19). Each flat cable has conductive-polymer EMI shielding. Several variants exist (R44SF/UF/MF/NF). The page does not state which variant has the right connector orientation for a 2230 host slot feeding a 2280 card, and it gives no shipping cost.
    - **Verdict:** confirmed
    - **Action:** Before ordering, confirm with ADT-Link which variant suits a 2230 male plug to 2280 female board, and the board's mounting holes. Keep the 8 GT/s x1 AER acceptance test.
    - **Impact:** —
    - **Sources:**
      - http://www.adt.link/product/R44SF.html
  18.
    - **Claim in stack:** #69: MHF4 is to be mated and unmated only with the I-PEX 90435-001 tool.
    - **Finding:** DigiKey lists 90435-001 as an MHF 4 mating/unmating tool, active, about $15-18. The Crowd Supply cables are MHF-4L plugs ('also compatible with Murata HSC'). radio_lab.json names a separate 90609-0001 for MHF 4L, which I could not verify.
    - **Verdict:** unverified
    - **Action:** Confirm with I-PEX or DigiKey that 90435-001 handles MHF 4L plugs; otherwise add the MHF 4L tool.
    - **Impact:** Low cost; it protects connectors rated for about 30 mating cycles.
    - **Sources:**
      - https://www.digikey.com/en/products/detail/i-pex/90435-001/25819261
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
  19.
    - **Claim in stack:** #21/#3: Lime RX DMA ring 16 x 16 KiB = 256 KiB (1.17 ms at 56 Msps); lime:Rx0 runs SCHED_OTHER nice -20 or FIFO 10.
    - **Finding:** Confirmed in LA9310_TRX.cpp: dmaBatchSize = 16*1024 and SubdivideBuffer(..., dmaBatchSize, 16) per lane, with 2048-byte packets. The thread is named 'lime:Rx0'. Upstream has deliberately commented out SetOSThreadPriority, with the note that REALTIME 'can trigger RT throttling which can cause unexpected data packet losses'. With 2 RX channels the iqflood region is split per lane. Arithmetic: 262144 B / 224 MB/s = 1.17 ms.
    - **Verdict:** confirmed
    - **Action:** No change. Keep the A/B test of loss counters between FIFO 10 and nice -20.
    - **Impact:** —
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LA9310_TRX.cpp
  20.
    - **Claim in stack:** #30: SatDump master from source with Soapy and the LimeSuiteNG legacy API.
    - **Finding:** Confirmed. SatDump's limesdr_sdr_support CMake builds a separate 'LimeSDR-NG' plugin when it finds limesuiteng-legacyapi. The limesuiteng-legacyapi Debian package exists on the staging branch.
    - **Verdict:** confirmed
    - **Action:** Combine with the 7 Msps minimum-rate item.
    - **Impact:** —
    - **Sources:**
      - https://raw.githubusercontent.com/SatDump/SatDump/master/plugins/sdr_sources/limesdr_sdr_support/CMakeLists.txt
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/debian/control
  21.
    - **Claim in stack:** #11/#95: Lime is TX-capable (1T2R); receive-only is enforced by patching LimeSuiteNG/Soapy to fail TX setup, plus a 50 Ohm load on TX.
    - **Finding:** Hardware TX capability is confirmed: 1T2R, TX low 0.03-1.9 GHz, TX high 3.3-3.8 GHz. Every M.2 wideband alternative checked (xSDR, LiteX/HamGeek M2SDR, XTRX) is also a transceiver. New detail: the M4 and VSPA firmware are open source (LimeSDR-Micro_FW) and are loaded by the host from /lib/firmware each time the device opens. A firmware build with the TX DMA and TX switch path removed would enforce the block on the device itself, not just in the host library. Effort and toolchain were not tested.
    - **Verdict:** new_option
    - **Action:** Optional hardening: build and pin an RX-only M4 firmware, and keep the LimeSuiteNG patch and the 50 Ohm load. The self-test must confirm that a TX stream fails.
    - **Impact:** Stronger compliance with the receive-only rule.
    - **Sources:**
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp
      - https://github.com/myriadrf/LimeSDR-Micro_FW
  22.
    - **Claim in stack:** C18/2.11: Samsung T7 1 TB, $229.99-274.99 (unverified), only with Lime, on the blue port.
    - **Finding:** I could not open a primary Samsung or B&H page (404/403). Search snippets show US listings at $219.99-274.99 (July 2026 history) and about EUR 138 at one EU reseller, so the price stays unverified. Radxa confirms one USB 3.1 Type-A port at 5 Gbps (blue). Model: at 56 Msps ci16 (224 MB/s), the 46 GiB recording area on UFS lasts about 221 s, and the 4 GiB RAM ring about 19 s. Live NPU tiles need no storage.
    - **Verdict:** unverified
    - **Action:** Re-price at the gate. Option: keep the Lime but defer the T7 until long raw 56 Msps captures are actually needed. Bursts and short captures fit in RAM and UFS.
    - **Impact:** Could postpone about $220-275.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/usb
      - https://www.cdw.com/product/samsung-portable-ssd-t7-mu-pc1t0t-solid-state-drive-1-tb-usb-3-2-gen/6171776
      - https://www.listofdisks.com/products/samsung-t7-1tb-mu-pc1t0t-am-b7f3c2
  23.
    - **Claim in stack:** C1/1090: acceptance tests within a '30-day guarantee after delivery'.
    - **Finding:** Crowd Supply: defective or damaged units must be reported 'within 30 days of receiving the product' for an RMA. Other returns are also within 30 days, but return freight is prepaid by the customer and the refund is 'less a restocking fee of at least $20 USD, or possibly more' (freight, customs). This is an RMA window, not a warranty. Any rework (PPS resistors, J21) forfeits it.
    - **Verdict:** corrected
    - **Action:** Rename it the '30-day RMA window'. Run all acceptance tests before any rework.
    - **Impact:** —
    - **Sources:**
      - https://www.crowdsupply.com/returns
  24.
    - **Claim in stack:** #90/C1 keep criterion: S-band (Black Kite 2286/2288, PHASMA 2208/2210 MHz) only with Lime.
    - **Finding:** A receive-only alternative exists: the Nooelec Ham It Down (SKU 100846), $89.95, ships in 1 business day. It converts 1.55-3.1 GHz to an IF of 50 MHz-1.6 GHz with a 1.5 GHz LO (TCXO, ppm not stated), powered by bias tee or USB at 4-5.5 V. With the planned S-band helix, LNA and cf2235-kt30 resonator, 2286 MHz lands at 786 MHz and 2208 MHz at 708 MHz on an RTL-SDR V4, enough for GMSK 38k4. It has no TX path, no M.2, DKMS, riser or T7, and much lower power. It does not provide the 56 MHz NPU survey or 3.3-3.8 GHz. Model risks: the low-side image is at 712-792 MHz (LTE 700/800), which the resonator must reject; the IF at 708-788 MHz sits in LTE Band 28/20 downlink, so the IF run must be short and shielded; the 1.5 GHz LO leak must go into the spur mask.
    - **Verdict:** new_option
    - **Action:** Add to the C1 gate: if S-band is the only 'yes' in criterion (1), buy the Ham It Down path instead of the Lime and cancel the pre-order. Keep the Lime only if 56 MHz wideband NPU survey or 3.3-3.8 GHz is wanted.
    - **Impact:** About $90 instead of about $596-681 for the Lime set, and one fewer TX-capable device.
    - **Sources:**
      - https://www.nooelec.com/store/ham-it-down.html
      - https://www.rtl-sdr.com/receiving-2-2-ghz-with-the-rtl-sdr-and-nooelec-ham-it-down/
  25.
    - **Claim in stack:** Implied: the Micro Basic is the cheapest wideband M.2 option.
    - **Finding:** Still true in Oct 2026. The Wavelet Lab xSDR is $549, M.2 2230 A+E key (PCIe 2.0 x2), 'Orders placed now ship Oct 30, 2026', with power and arm64 support not stated, and it needs a key adapter for the Q6A M-key slot. Its 0.1 Msps minimum rate is a plus, but it costs more than twice as much and is also a transceiver. No EOL notice was found for the Micro.
    - **Verdict:** confirmed
    - **Action:** No change.
    - **Impact:** —
    - **Sources:**
      - https://www.crowdsupply.com/wavelet-lab/xsdr
  26.
    - **Claim in stack:** 5.6/#69: Lime spur lines at 737.28, 1597.44, 1689.6 and 1720.32 MHz are in the mask.
    - **Finding:** The arithmetic is correct: 30.72 MHz x 24, 52, 55 and 56. That these lines actually show up is a model, not a measurement.
    - **Verdict:** confirmed
    - **Action:** Replace with lines measured in the Lime A/B run.
    - **Impact:** —
    - **Sources:**
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/clock.html
- **Current status oct 2026:** As of 18 Oct 2026: LimeSDR Micro M.2 2280 Basic is $249 and GNSS $299, both on pre-order at Crowd Supply, with 'Orders placed now ship Dec 15, 2026' and $18 worldwide shipping. The MHF4L-SMA cable is $6, in stock. The campaign closed 28 May 2026 with 130 backers and $119,875. The last update is from 17 Jun 2026, and nothing public confirms that the 30 Sep 2026 first run shipped. I found no Mouser listing and no EOL notice. The current hardware revision in the docs is v1.2 (EEPROM boot by default, top-side height up to 4.5 mm). Software: Micro support exists only on the LimeSuiteNG limesdr-micro-staging branch (head 37cb1833, 16 Oct 2026). It is 206 commits ahead of develop and not merged, and the last release, v25.1.0 (Jan 2025), has no Micro support. Recent staging commits still fix streaming: overrun timestamp recovery, stream pacing, BAR release, the IRQ init order, and multi-channel Rx (Sep 2026). The kernel module is la9310_limesdr 0.2.1 (CMake DKMS; no Debian package). CI is x86 only. On the LimeSDR-Micro_FW staging branch (16 Oct 2026), 'initial PPSDO support' was added, and issue #6 (external reference select writes the wrong register, so the external reference never engages) was fixed. That fix is not in master and not in the firmware bundled with LimeSuiteNG. On the Lime forum, staff stated on 24 Aug 2026 that the board draws about 4 W ('depending on configuration'), and on 13 Oct 2026 that 30 MHz-3.8 GHz has no coverage gaps, with matching optimised only in the listed bands. Lime has demonstrated the board on arm64 (Raspberry Pi CM5 in the uConsole, 40 Msps). Nothing has been shown on Qualcomm QCS6490.
- **Notes:** Keep/drop gate, recommended changes to C1. (1) Split criterion (1). If the user only wants S-band, choose the receive-only Ham It Down path ($89.95 + LNA + resonator on an RTL-SDR) and cancel the Lime. Keep the Lime only if the 56 MHz wideband NPU survey or 3.3-3.8 GHz is wanted. Under the no-dish rule, 3.3-3.8 GHz has few receivable targets; that is my analysis. (2) Add software preconditions: pin the LimeSuiteNG staging commit; pin an M4 firmware that contains 1f70189 if REF IN is used; compile la9310_limesdr against the 6.18.2-4-qcom headers in CI before 1 Dec; read the pcie1 ranges from the Radxa DT to confirm BAR0 (256 MiB) fits. (3) Watch the order weekly: shipment ends the free cancel, and Dec 15 is only an estimate. (4) After delivery, all acceptance tests come first, inside the 30-day RMA window; any rework comes after. Unverified items: current T7 price; the R44SF variant and orientation; whether the I-PEX 90435-001 fits MHF 4L plugs; the Lime operating-temperature range; the Ham It Down TCXO ppm and noise figure. The U20/ETA3521 schematic detail comes from the earlier audit, but the ETA3521 4 A rating is confirmed. Labelled models: BAR fit, storage durations, IF and image frequencies, spur lines. Local working copies: /home/user/myriadrf/limesuiteng (partial clone, all branches) and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/ws_dl (downloaded docs, driver sources, firmware repo clones).

## Форуми та досвід спільноти (`forums`)

_Run `wf_e64436d6-ae7`_

- **Component:** Wideband PCIe SDR for the Radxa Dragon Q6A M.2 slot: LimeSDR Micro M.2 2280 (recommended), with LiteX M2SDR, HamGeek M2SDR, Wavelet Lab xSDR/uSDR, LimeSDR XTRX and USB3 alternatives (bladeRF 2.0 micro, B210-class LibreSDR B220 mini); budget path is running the RTL-SDR alone
- **Experiences:**
  1.
    - **Product:** LimeSDR Micro M.2 2280 (shipping status)
    - **Source url:** https://www.crowdsupply.com/lime-micro/limesdr-micro/updates
    - **Community:** Crowd Supply campaign page and updates
    - **What they built:** n/a (status check, 17 Oct 2026)
    - **Problems:**
      - The last public update is dated Jun 17, 2026 ('component sourcing has started… ship in September'). No update since then confirms that the Sept 30 first run actually shipped.
      - The product page now says 'Orders placed now ship Dec 15, 2026'. Basic is $249, GNSS $299, plus $18 worldwide shipping. 130 backers. The main variants are listed as Pre-order. Mouser handles distribution.
    - **Fixes:**
      - None. The only option is to order and wait, or to watch the updates page.
    - **Outcome:** Delivery to backers is unconfirmed. I found no independent hands-on reports anywhere (Lime forum, CNX comments section shows 0 comments, web search).
  2.
    - **Product:** LimeSDR Micro M.2 2280 (driver maturity)
    - **Source url:** https://github.com/myriadrf/LimeSuiteNG/branches/all
    - **Community:** GitHub myriadrf/LimeSuiteNG (branches, commits, compare)
    - **What they built:** n/a (developer activity)
    - **Problems:**
      - As of Oct 16, 2026, Micro support still lives on separate 'limesdr-micro' (updated Oct 9) and 'limesdr-micro-staging' (updated Oct 16) branches. The develop...limesdr-micro-staging compare shows 206 commits and 196 files changed, so it is not merged into develop.
      - Commits from Sep to Oct 2026 are still fixing basic streaming: 'Recover Rx timestamps after overruns' (Oct 15), 'Fix stream pacing issues' (Oct 9), 'la9310_limesdr: release reserved BARs after kernel module unload' (Oct 1), 'initialize IRQ handler before enabling interrupts' (Sep 27), 'Add multiple Rx channel streaming' (Sep 10), and 'Direct access to DMA TCD tables; add cache flushing' (Sep 6).
      - No commit mentions arm64, IOMMU or page size.
    - **Fixes:**
      - Build from limesdr-micro-staging, or from whatever branch Lime names at delivery. The kernel module is la9310_limesdr.
    - **Outcome:** The driver is in active stabilization. Two-channel RX streaming was only added in Sep 2026.
  3.
    - **Product:** LimeSDR Micro (vendor validation status)
    - **Source url:** https://openairinterface.org/wp-content/uploads/2026/06/Summer-2026-OAI-Workshop-Ricardas.pdf
    - **Community:** OpenAirInterface Summer 2026 workshop (Lime presentation)
    - **What they built:** OAI 5G NR gNB on LimeSDR Micro, band n78 TDD, 20 MHz
    - **Problems:**
      - OAI integration is 'Validated on x86'.
      - 'COTS UE attaches to network. Limited sustained stack up-time due to on-going firmware development work.'
      - The roadmap item under 'Now' is 'Harden LimeSuiteNG PCIe driver and streaming'. VSPA FFT/filter offload is under 'Next'.
    - **Fixes:** []
    - **Outcome:** In June 2026 Lime itself described the firmware and driver as not yet stable for long sustained sessions.
  4.
    - **Product:** LimeSDR Micro on Raspberry Pi CM5 (ClockworkPi uConsole)
    - **Source url:** https://myriadrf.org/stories/ota-limesdr-micro-uconsole-cyberether-web-lunar-ctf-more/
    - **Community:** MyriadRF blog / Crowd Supply update (vendor demo)
    - **What they built:** uConsole (CM5) with LimeSDR Micro running Gqrx
    - **Problems:**
      - The demo only says Gqrx was 'configured for 40Msps'. It gives no sustained-throughput figures, kernel or DMA notes, and does not name the adapter.
    - **Fixes:** []
    - **Outcome:** This is the only ARM-host evidence for the Micro, and it is a vendor demo, not a user report.
  5.
    - **Product:** LimeSDR Micro (power)
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
    - **Community:** MyriadRF Discourse
    - **What they built:** A user (jonsnow) designing a carrier board for the Micro
    - **Problems:**
      - The schematic shows 2.5 A at 3.3 V (8.25 W) on the M.2 pins, and the user asked whether that is the real draw.
      - His follow-up question about idle power (SDR on, not transmitting) went unanswered.
    - **Fixes:**
      - Lime (Zack, 24 Aug 2026): the 2.5 A is the PCIe spec limit. 'Board should consume about 4 W, depending on configuration.'
    - **Outcome:** Partly answered: about 4 W typical. Idle and RX-only figures are unknown. Lime's setup docs still ask for cooling of at least 10 W.
  6.
    - **Product:** LimeSDR Micro (frequency coverage / RX matching)
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-micro-m-2-pcie-frequency-range/13348
    - **Community:** MyriadRF Discourse
    - **What they built:** n/a (pre-purchase question, Oct 2026)
    - **Problems:**
      - The docs list discontinuous RX bands (0.3-2.2, 0.7-2.6 and 3.3-3.8 GHz) while the product page says 30 MHz-3.8 GHz.
      - A user asked for data on RX at 30 MHz. A separate thread asking for hardware match/return-loss validation of the 700 MHz-2.6 GHz port got no answer (https://discourse.myriadrf.org/t/limesdr-micro-m-2-xtrx-match-validation-of-700mhz-2-6ghz-rx-port/13292).
    - **Fixes:**
      - Lime (andrewback, 13 Oct 2026): 'no gaps in frequency coverage'. The bands 'indicate where the RF matching networks are optimised'.
    - **Outcome:** Coverage is continuous, but nobody has published sensitivity, noise figure or return loss below 300 MHz or on any port.
  7.
    - **Product:** LimeSDR XTRX (same LMS7002M + limepcie stack) on Raspberry Pi 5 / CM4
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-xtrx-not-found/8342
    - **Community:** MyriadRF Discourse
    - **What they built:** XTRX on Pi 5 through mPCIe/M.2 HAT adapters, and on a CM4 IO board
    - **Problems:**
      - The module failed to build: '/lib/modules/6.6.31-v8-16k+/build: No such file or directory'.
      - Header mismatch errors: 'disagrees about version of symbol' and 'Unknown symbol … (err -22)'.
      - MSI error: 'arch assigned 64-bit MSI address … but device only supports 32 bits', then 'probe … failed with error -5'.
      - Streaming failed: 'mmap io_remap_pfn_range failed -22' and 'failed to MMAP Rx DMA buffer'. Cause: the driver assumed 4 KB pages, but the Pi 5 uses 16 KB.
      - After about 30 reboots across several Pi 5 adapters, detection was intermittent. Some adapters never showed the card in lspci.
    - **Fixes:**
      - Install matching headers: 'sudo apt-get install linux-headers-`uname -r`' (do not symlink a different header tree).
      - Pass '-DKERNELHEADERS_DIR=/lib/modules/`uname -r`/source' to CMake.
      - Add 'dtoverlay=pciex1-compat-pi5,no-mip' to get past the MSI error.
      - Lime changed the driver for 16 KB pages and the gateware for 64-bit DMA. Flash it with 'limeFLASH combined_flash_programming.bin', power-cycle, then 'limeFLASH -t FPGA/user-image user_flash_programming_file.bin'. After that, remove the 32-bit-DMA overlays.
      - Of the adapters tried, the official M.2 HAT+ worked best.
    - **Outcome:** basicRX and basicTX worked after the driver and gateware fixes. Adapter-dependent enumeration failures on the Pi 5 were never fully resolved.
  8.
    - **Product:** LimeSDR XTRX (heat)
    - **Source url:** https://discourse.myriadrf.org/t/temperature-of-limesdr-xtrx/8366
    - **Community:** MyriadRF Discourse
    - **What they built:** XTRX in CM4 IO boards, PCs and PCIe adapters
    - **Problems:**
      - The LMS7002M reached 60 °C five minutes after a cold boot in open air at 25 °C ambient.
      - Above 85 °C near maximum sample rates.
      - 80 °C just running an FM receiver with no room for a fan.
      - The thermal pad and bracket listed for the PCIe adapter were missing from one shipment.
    - **Fixes:**
      - A 40 mm fan held the onboard sensor at about 50-55 °C.
      - A thermal pad to the adapter's copper pour (one user bought one from Mouser for about $20).
    - **Outcome:** Lime said this heat is normal and that users should test with their own enclosure and sample rate. The Micro uses the same LMS7002M (about 1 W typical, per https://discourse.myriadrf.org/t/lms7002m-package-thermal-resistance/13300) plus the LA9310.
  9.
    - **Product:** LimeSDR XTRX (RX spurs)
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-xtrx-narrow-internal-spurs-in-rx-spectrum-can-they-be-removed/13288
    - **Community:** MyriadRF Discourse
    - **What they built:** XTRX at 122.88 Msps, LO 1585 MHz, gr-limesuiteng
    - **Problems:**
      - Spurs at fixed offsets (about ±15, ±31, ±46, +61 MHz) at -90 to -95 dB with nothing connected. They do not move with sample rate and RX DC/IQ calibration has no effect.
    - **Fixes:**
      - Diagnostic: set the LNAW input shorting switch (LMS7002M register 0x010D[1], EN_INSHSW_W_RFE). The spectrum turned symmetrical, which points to RFI picked up inside a noisy PC case.
    - **Outcome:** Partial. The spurs are at least partly radiated pickup, which argues for shielding the card from the SBC and display in a compact handheld.
  10.
    - **Product:** limepcie kernel module and DKMS (XTRX)
    - **Source url:** https://discourse.myriadrf.org/t/limepcie-load-failure-after-kernel-tag-update/8666
    - **Community:** MyriadRF Discourse
    - **What they built:** XTRX on an Ubuntu 24.04 laptop with a vendor kernel
    - **Problems:**
      - After a kernel package update that kept the same version number but changed the tag, modprobe failed with 'Exec format error' and 'disagrees about version of symbol module_layout'.
      - DKMS did not rebuild because 'there already are built files'.
    - **Fixes:**
      - Remove the limepcie modules from the DKMS tree and rebuild them against the running kernel.
    - **Outcome:** 'all works as expected'. The same failure applies to any vendor kernel that updates frequently, which includes the Q6A.
  11.
    - **Product:** LimeSuiteNG on arm64 (NVIDIA Orin NX) and on a custom BSP
    - **Source url:** https://discourse.myriadrf.org/t/failed-to-build-limwsuite-under-ubuntu-22-arm64/8447
    - **Community:** MyriadRF Discourse
    - **What they built:** XTRX on Jetson Orin NX, and XTRX on an embedded Debian 12 BSP board
    - **Problems:**
      - CMake errors ('target_sources may only set INTERFACE properties…').
      - A spurious 'LinuxKernelHeaders' requirement.
      - On the BSP board, the vendor image had no kernel headers, so the limepcie DKMS build failed and limeDevice reported 'No devices found' even though lspci listed the card (https://discourse.myriadrf.org/t/limesdr-xtrx-not-found-while-listed-on-lspci/13044).
    - **Fixes:**
      - Pull the latest develop branch (Lime fixed the CMake errors). The headers warning can be ignored if headers are actually installed.
      - Without headers, cross-compile the module with the BSP toolchain and load it at boot.
    - **Outcome:** Both cases ended with the XTRX working over PCIe on ARM.
  12.
    - **Product:** LimeSuiteNG PCIe code (shared with the Micro)
    - **Source url:** https://github.com/myriadrf/LimeSuiteNG/issues?q=pcie
    - **Community:** GitHub myriadrf/LimeSuiteNG issues
    - **What they built:** n/a (July 2026 code audit issues)
    - **Problems:**
      - #196 (open): 'Kernel driver control path has a disabled lock, a no-op LOCK command, and a busy-wait'.
      - #283: ReadySlots assumed a 16-bit DMA counter where the PCIe path is 64-bit. Closed.
      - #285: DMA lock not released on the Initialize() error path. Closed.
      - #286: EnableContinuous checked the ioctl return value instead of errno. Closed.
      - #380 (open): RunControlCommand copies an unbounded length into a 64-byte packet.
    - **Fixes:**
      - Most items were fixed in PRs #253, #321, #322 and #376 (Jul-Aug 2026).
    - **Outcome:** The kernel control-path issue (#196) was still open at last check.
  13.
    - **Product:** SatDump with LimeSuiteNG devices (XTRX)
    - **Source url:** https://github.com/SatDump/SatDump/issues/1034
    - **Community:** GitHub SatDump issues and PR #1041
    - **What they built:** XTRX at up to 120 Msps for satellite decoding
    - **Problems:**
      - Live decoding gave a good QPSK constellation, but the deframer was unstable and the CADUs were garbled ('every second packet lost'). Bigger buffers and 30 Msps did not help. A bladeRF on the same PC was fine.
      - Old LimeSuite does not support PCIe Lime devices.
    - **Fixes:**
      - Record IQ, then decode offline. That worked.
      - Maintainer Aang23 added LimeSuiteNG support to SatDump on Sep 17, 2026 ('This has been added now') and closed the bandwidth issue on Sep 30, 2026 ('This should be working now').
    - **Outcome:** SatDump now supports LimeSuiteNG. Whether that covers the Micro depends on Micro support reaching the LimeSuiteNG branch SatDump builds against. Expect to record first and decode afterwards at high rates on the Q6A.
  14.
    - **Product:** LiteX M2SDR on NVIDIA Jetson Orin (aarch64, SMMU active)
    - **Source url:** https://github.com/enjoy-digital/litex_m2sdr/issues/156
    - **Community:** GitHub enjoy-digital/litex_m2sdr issues
    - **What they built:** M2SDR in Gen2 x1, kernel 6.8.12-tegra
    - **Problems:**
      - Under sustained DMA (about 245 MB/s each way) or a module reload, the link dies: 'AER: Uncorrectable (Fatal)… CmpltTO', 'can't recover (no error_detected callback)'.
      - Recovery needs a full reboot, and the next probe stalls the machine for about 56 s.
      - Logs show 'Reading too late, 256 buffers lost' and 'RT throttling activated'.
    - **Fixes:**
      - The reporter's PR #157 adds AER recovery handlers, so the host no longer has to reboot (rescan plus probe in 143 ms).
      - RX-only streaming at 8-245 MB/s ran for minutes without errors.
    - **Outcome:** Open, with no maintainer reply. The board itself still needs a reboot after a fatal event. This shows that even the most mature open PCIe SDR driver is fragile on ARM.
  15.
    - **Product:** LiteX M2SDR SoapySDR path on Jetson Orin
    - **Source url:** https://github.com/enjoy-digital/litex_m2sdr/issues/149
    - **Community:** GitHub enjoy-digital/litex_m2sdr issues
    - **What they built:** M2SDR with SoapySDR 0.8.1 on Ubuntu 24.04 aarch64, gateware 2026-05-15
    - **Problems:**
      - SoapySDR RX returns 'almost entirely zero buffers'. About 76% of windows are still all-zero after calibration.
      - The C tool m2sdr_record streams clean data.
    - **Fixes:**
      - Run 'm2sdr_rf --calibrate-delay' before streaming. The reporter's local patch calls the delay calibration from setSampleRate().
    - **Outcome:** Open. SatDump and SDR++ would use this Soapy path.
  16.
    - **Product:** LiteX M2SDR on Orange Pi 5 Max (RK3588)
    - **Source url:** https://github.com/enjoy-digital/litex_m2sdr/issues/31
    - **Community:** GitHub enjoy-digital/litex_m2sdr issues
    - **What they built:** M2SDR in the Orange Pi M.2 M-key slot
    - **Problems:**
      - The card did not enumerate. Its LED went dark after boot.
      - A second user saw zero DMA throughput.
      - When it did stream at about 1.95 Gbps, the kernel logged 'Reading too late' buffer losses.
    - **Fixes:**
      - Decompile the DTB and set num-lanes in node pcie@fe150000 from <0x04> to <0x02>, then recompile.
      - 'iommu.passthrough=1 arm-smmu.disable=1' had no effect on detection.
      - Zero throughput was a permissions problem: run with sudo or 'chmod 666 /dev/m2sdr0'.
      - Record to RAM rather than eMMC or SD.
    - **Outcome:** Working for the reporter. The second user's buffer loss was not confirmed fixed.
  17.
    - **Product:** LiteX M2SDR, IOMMU/SMMU handling (Jetson Orin Nano, x86, Pi 5 doc)
    - **Source url:** https://github.com/enjoy-digital/litex_m2sdr/issues/70
    - **Community:** GitHub enjoy-digital/litex_m2sdr issues and docs
    - **What they built:** M2SDR on Jetson Orin Nano, an i9-13900K PC and a Raspberry Pi 5
    - **Problems:**
      - Disabling the SMMU globally, as the old instructions said, left a Jetson unable to accept input or booting to a black screen.
      - Zero-copy DMA mapped the wrong pages behind an IOMMU because the driver used __pa (#77).
    - **Fixes:**
      - #77 rewrote litepcie_mmap to use dma_mmap_coherent (commit 270f3cf, Oct 2025).
      - Maintainer advice: try 'iommu.passthrough=1' first, never use 'arm-smmu.disable=1' as a default, and keep a known-good boot entry or serial console.
      - Pi 5 doc: 'kernel=kernel8.img' (4K pages), 'dtoverlay=pcie-32bit-dma-pi5', 'dtoverlay=pciex1-compat-pi5,l1ss=off,no-l0s=on,no-mip=off', and append 'pci=noaer pcie_aspm=off' to cmdline.txt (https://github.com/enjoy-digital/litex_m2sdr/blob/main/doc/hosts/raspberry-pi-5.md).
    - **Outcome:** Resolved in the current driver and docs. These are the closest documented SMMU recipes to what a QCS6490 may need.
  18.
    - **Product:** LiteX M2SDR (price and stock)
    - **Source url:** https://enjoy-digital-shop.myshopify.com/products/litex-m2-sdr-si5351c
    - **Community:** Enjoy Digital shop
    - **What they built:** n/a
    - **Problems:**
      - €699, 'Currently out of stock' because AD9361 and XC7A200T component costs went up. The shop page shows no pre-order button. Buyers are asked to email about a small batch at a slightly higher price.
    - **Fixes:** []
    - **Outcome:** Not purchasable on demand as of Oct 2026.
  19.
    - **Product:** LiteX M2SDR / LitePCIe on Raspberry Pi CM4
    - **Source url:** https://github.com/enjoy-digital/litex_m2sdr/issues/37
    - **Community:** GitHub enjoy-digital/litex_m2sdr issues
    - **What they built:** CM4 Rev 1.1 on Ubuntu kernel 5.4
    - **Problems:**
      - 'Failed to allocate dma buffers', then 'kernel BUG at drivers/pci/msi.c:396!' on probe.
    - **Fixes:**
      - Error-path fix #141 makes a failed probe unwind cleanly.
      - Suggested checks: 64 KB page size, and the doc's 'Tweaking the system' section.
    - **Outcome:** Open, waiting for a retest on a current kernel. The DMA allocation failure is unexplained.
  20.
    - **Product:** HamGeek M2SDR (AD9361 + XC7A200, GPSDO)
    - **Source url:** https://www.hgeek.com/products/hamgeek-m2sdr-software-defined-radio-m-2-xc7a200-rf-transceiver-module-gpsdo-40m-clock-output
    - **Community:** Vendor store (no community reports found)
    - **What they built:** n/a
    - **Problems:**
      - $376, sold out (SKU 101071). No customer reviews.
      - The vendor notes the Raspberry Pi M.2 slot is electrically x1 and the x1 firmware option is 'untested'.
      - Known bug: TX below 1.9 MS/s errors out.
      - Frequency range, sample rate and PCIe generation are not stated.
    - **Fixes:** []
    - **Outcome:** I found no user experience on any forum.
  21.
    - **Product:** bladeRF 2.0 micro (USB3) on Raspberry Pi 5
    - **Source url:** https://github.com/Nuand/bladeRF/issues/977
    - **Community:** GitHub Nuand/bladeRF issues
    - **What they built:** bladeRF 2.0 on a Pi 5 USB 3.0 port
    - **Problems:**
      - Errors: 'Failed to send NIOS II request', 'Transfer timed out for buffer', 'Timed out waiting for buf_ready after 3000 ms', 'Write Error -5'.
      - Buffers drop after about 10 s.
      - Powering from the DC jack did not help. No problems on x86 or a Khadas VIM3.
    - **Fixes:**
      - A maintainer pointed to stability fixes in libbladeRF 2.6.0.
      - Keep the bladerf_sync_rx() thread free of DSP: save samples and return immediately.
    - **Outcome:** Closed as fixed, but a user reported on v2.6.0 that 'this issue persists' on the Pi 5. USB 2.0 ports were steadier but still overran.
  22.
    - **Product:** USRP B210 / B205-mini (B210-class, like the LibreSDR B220 mini) on a Qualcomm RB5 (QRB5165)
    - **Source url:** https://forum.modalai.com/post/9064
    - **Community:** ModalAI forum
    - **What they built:** B210 on a Qualcomm Flight RB5 drone through the 5G daughter-card USB header
    - **Problems:**
      - It enumerates as USB 3.0 but only streams about 15 MSps TX+RX (about 480 Mbps) without over/underruns. The same benchmark gives 56 MS/s on an Intel PC.
      - USB3 Ethernet reached about 250 Mbps on the RB5 against about 520 Mbps on a laptop. ModalAI: 'It's unclear at this time why there is such a difference.'
    - **Fixes:**
      - Stopping camera/VIO services, adding a fan, changing UHD buffer and over-the-wire settings, and a replacement cable did not fix it.
    - **Outcome:** Unresolved. A cable or hub may be involved, but this is the only Qualcomm-SoC USB3 SDR throughput report found, and it points to well below 61.44 Msps.
  23.
    - **Product:** LibreSDR B220 mini (AD9361 + XC7A200T)
    - **Source url:** https://community.libre.space/t/libre-sdr-b220-mini-xc7a200t/14046
    - **Community:** SatNOGS / Libre Space community
    - **What they built:** A newcomer's satellite and radio astronomy station (Nov 2025)
    - **Problems:**
      - No hands-on results posted.
    - **Fixes:**
      - PE0SAT: it 'looks te be an Ettus Research B200 clone so all B200 information should be helpful'.
    - **Outcome:** There is no real user evidence for the B220 mini. The Habr and rtl-sdr.com LibreSDR reviews cover the different AD9363/Zynq Pluto-clone model.
  24.
    - **Product:** Wavelet Lab uSDR (PCIe) on Raspberry Pi 5 / xSDR
    - **Source url:** https://github.com/wavelet-lab/usdr-lib/issues/86
    - **Community:** GitHub wavelet-lab/usdr-lib issues
    - **What they built:** uSDR rev.2 on a Pi 5 through a HAT and M.2 adapter
    - **Problems:**
      - 'pcie_uram_plugin_create… Unable to initialize device, error -110'.
      - Link 'Speed 5GT/s, Width x1 (downgraded)'.
      - An interrupted firmware flash bricked the FPGA, which needed JTAG recovery.
      - xSDR issue #117 (https://github.com/wavelet-lab/usdr-lib/issues/117): MIMO at high rate errors with 'In double pump mode only SISO mode is allowed', after which the stream will not reopen until the device is reconnected.
    - **Fixes:**
      - Maintainer: a rev.2 incompatibility; use old_r2 firmware or 'USDR_BARE_DEV=1 usdr_flash -w'.
      - The card works from an x86 PC over Thunderbolt 3.
    - **Outcome:** Both issues are open. The xSDR campaign shipped to Mouser on Jul 8, 2026 (https://www.crowdsupply.com/wavelet-lab/xsdr/updates/xsdr-campaign-is-shipping-soon), but I found no ARM-host user reports.
  25.
    - **Product:** Radxa Dragon Q6A M.2 slot
    - **Source url:** https://forum.radxa.com/t/nvme-2230-not-detected/30807
    - **Community:** Radxa forum
    - **What they built:** NVMe 2230 boot drives, and a 2280 drive on an extender
    - **Problems:**
      - After about 3 h of uptime the board rebooted and no 2230 SSD was ever detected again, under RadxaOS or Windows, with three different drives.
      - Another user's boot problems were caused by dust in the slot.
      - No Q6A forum post shows any non-storage PCIe device (accelerator or SDR) in the slot.
    - **Fixes:**
      - Cleaning the slot with a soft brush fixed it for one user. Radxa's advice was to test other M.2 devices, then claim warranty; the board went back to the seller.
      - One user runs 'a full sized drive on an extender' successfully (https://forum.radxa.com/t/windows-on-radxa-dragon-q6a/29913/40), but the extender model is not given.
    - **Outcome:** An M.2 extender works with NVMe on at least one Q6A. A dead slot is possible, so test the slot with a cheap NVMe drive before installing the SDR.
  26.
    - **Product:** Radxa Dragon Q6A 256 GB Kioxia UFS (IQ recording target)
    - **Source url:** https://forum.radxa.com/t/ufs-random-reboots/30630
    - **Community:** Radxa forum
    - **What they built:** Q6A desktop and cluster nodes on the Kioxia THGJFGT1E45BAILB UFS module
    - **Problems:**
      - 1-5 s freezes every few minutes, permanent freezes and reboots, ufshcd-qcom PM/hibern8/abort errors.
      - Firmware 6.0.260120 and 'limit-hs-gear = <2>' did not help.
    - **Fixes:**
      - chenchongbiao's PA_TACTIVATE quirk for the Kioxia part (radxa/kernel linux-6.18.2 branch). Test package linux-image-6.18.2-4-qcom installed with 'sudo apt reinstall'.
    - **Outcome:** Two users confirmed it fixed (no errors, no stutter). Measured afterwards: about 1005 MiB/s single-stream read, about 1828 MiB/s at QD32, writes about 0.5 GB/s.
  27.
    - **Product:** Radxa Dragon Q6A power input and 3.3 V rail (M.2 supply)
    - **Source url:** https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
    - **Community:** Radxa forum
    - **What they built:** Battery and DC-DC powered Q6A
    - **Problems:**
      - The 3.3 V rail is supplied by an ETA3521, 'theoretically capable of up to 4A output', shared with on-board peripherals.
      - The 12 V header accepts 3.6-16 V (BigfootACA) or 4.5-16 V (strongtz, https://forum.radxa.com/t/radxa-q6a-4s1p-powering/31611), so a full 4S pack at 16.8 V exceeds it.
      - Do not use USB-C while feeding 12 V externally.
    - **Fixes:**
      - Feed a regulated 12 V (or 5/9 V) to the header.
    - **Outcome:** Nobody has measured the M.2 3.3 V budget with a high-draw card. A Micro at about 4 W is roughly 1.2 A from that shared rail.
  28.
    - **Product:** LMS7002M-based LimeSDRs for satellite RX (SatNOGS stations)
    - **Source url:** https://community.libre.space/t/looking-for-advice-on-sdr/9842
    - **Community:** SatNOGS / Libre Space community
    - **What they built:** SatNOGS ground stations
    - **Problems:**
      - vk4jbe: 'without a preamp they are pretty deaf at VHF & UHF…plus they don't have an internal bias-tee'.
      - LimeSDR Mini V2.0 at 2245 MHz (S-band, 30.72 Msps) showed many signals folded in at Freq ± SR (https://community.libre.space/t/strf-and-the-limesdr-mini-v2-0/15071).
    - **Fixes:**
      - Put an LNA at the antenna with an external bias tee.
      - For the images: set the analog RX bandwidth explicitly. The user built darkstar007's rx_tools fork to get '-B', patched the setupStream call for the new SoapySDR API, and used '-B 22 MHz' at 30.72 Msps.
    - **Outcome:** After setting -B the out-of-band LoRa signals were 'much weaker'. Several active stations use LimeSDRs successfully with LNAs.
- **Common problems:**
  1.
    - **Problem:** The PCIe SDR kernel module will not build or load because kernel headers are missing or mismatched, and DKMS silently fails to rebuild after a vendor kernel update (vermagic or symbol-version errors, 'Exec format error').
    - **Affected products:** LimeSDR XTRX and LimeSDR Micro (limepcie / la9310_limesdr), LiteX M2SDR (m2sdr.ko). Any out-of-tree module on the Q6A, whose kernel moved from 6.18.2 to 7.0.x to 7.2.x in 2026 and broke HDMI and the AIC8800 module on some updates.
    - **Frequency:** common
    - **Known fix:** Install headers that exactly match uname -r. If DKMS keeps a stale build, remove the module from the DKMS tree and rebuild. Without headers, cross-compile with the BSP toolchain. On the Q6A, pin the kernel package (apt-mark hold) once the SDR works, and rebuild the module before rebooting into any new kernel.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/limepcie-load-failure-after-kernel-tag-update/8666
      - https://discourse.myriadrf.org/t/limesdr-xtrx-not-found/8342
      - https://discourse.myriadrf.org/t/limesdr-xtrx-not-found-while-listed-on-lspci/13044
      - https://forum.radxa.com/t/linux-7-0-hdmi-not-working/31304
      - https://forum.radxa.com/t/aic8800-module-broken-with-linux-7-1-3/31150
  2.
    - **Problem:** DMA problems on ARM hosts: 32-bit MSI/DMA addressing limits, drivers assuming 4 KB pages (16 KB on Pi 5), and DMA buffer allocation or mmap failures ('io_remap_pfn_range failed -22', 'Failed to allocate dma buffers').
    - **Affected products:** LimeSDR XTRX (Pi 5/CM4), LiteX M2SDR (CM4, Pi 5)
    - **Frequency:** common
    - **Known fix:** Update the driver and gateware (Lime's 64-bit DMA gateware plus the 16 KB page fix, flashed with limeFLASH). Use a 4 KB-page kernel (kernel=kernel8.img on Pi). On the Pi 5, dtoverlay=pciex1-compat-pi5,no-mip (Lime) or pcie-32bit-dma-pi5 plus pciex1-compat-pi5,l1ss=off,no-l0s=on,no-mip=off (M2SDR). On the Q6A, check 'getconf PAGESIZE' first.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/limesdr-xtrx-not-found/8342?page=2
      - https://github.com/enjoy-digital/litex_m2sdr/blob/main/doc/hosts/raspberry-pi-5.md
      - https://github.com/enjoy-digital/litex_m2sdr/issues/37
  3.
    - **Problem:** IOMMU/SMMU breaks zero-copy DMA (the card enumerates but returns no samples), and disabling the SMMU globally breaks other peripherals.
    - **Affected products:** LiteX M2SDR (Jetson Orin, x86). Likely relevant to any PCIe SDR on the QCS6490, whose Qualcomm SMMU firmware traps S2CR bypass writes, so the kernel emulates bypass with context banks.
    - **Frequency:** occasional
    - **Known fix:** Use a driver that maps buffers with dma_mmap_coherent (M2SDR commit 270f3cf). If samples are still missing, try iommu.passthrough=1, not arm-smmu.disable=1. Keep a known-good boot entry or a serial console before changing cmdline.
    - **Fix sources:**
      - https://github.com/enjoy-digital/litex_m2sdr/issues/77
      - https://github.com/enjoy-digital/litex_m2sdr/issues/70
      - https://lkml.iu.edu/hypermail/linux/kernel/2009.0/05751.html
  4.
    - **Problem:** The card intermittently fails to enumerate through M.2 adapters, extenders or HATs, or only with a wrong lane count in the device tree.
    - **Affected products:** LimeSDR XTRX on Pi 5 (several adapters), LiteX M2SDR on Orange Pi 5 Max, uSDR on Pi 5 (link downgraded to x1)
    - **Frequency:** common
    - **Known fix:** Try a different adapter (the official Pi M.2 HAT+ was the most reliable for the XTRX). On RK3588, set num-lanes = <0x02> in the pcie node. Keep the extender short and Gen3-rated, and be ready to force a lower PCIe generation.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/limesdr-xtrx-not-found/8342?page=2
      - https://github.com/enjoy-digital/litex_m2sdr/issues/31
      - https://github.com/wavelet-lab/usdr-lib/issues/86
  5.
    - **Problem:** The PCIe link dies under sustained DMA or on module reload/teardown (CmpltTO, AER fatal), and recovery needs a reboot.
    - **Affected products:** LiteX M2SDR on Jetson Orin (aarch64, SMMU active)
    - **Frequency:** occasional
    - **Known fix:** Partial: the AER recovery handlers in PR #157 avoid the host reboot. Do not reload the module while streaming, and run long RX-only soak tests before relying on it in the field.
    - **Fix sources:**
      - https://github.com/enjoy-digital/litex_m2sdr/issues/156
  6.
    - **Problem:** Real-time decoding drops data or overruns at high sample rates on modest hosts ('Reading too late', garbled CADUs, every second packet lost).
    - **Affected products:** XTRX with SatDump, LiteX M2SDR on RK3588 and Jetson, bladeRF on Pi 5
    - **Frequency:** common
    - **Known fix:** Record raw IQ, then decode offline. Record to RAM or fast storage, not SD or eMMC. Keep the RX thread free of DSP. Set the CPU governor to performance. Use the lowest sample rate the signal needs.
    - **Fix sources:**
      - https://github.com/SatDump/SatDump/issues/1034
      - https://github.com/enjoy-digital/litex_m2sdr/issues/31
      - https://github.com/Nuand/bladeRF/issues/977
      - https://github.com/enjoy-digital/litex_m2sdr
  7.
    - **Problem:** Heat: LMS7002M boards run at 60-85+ °C without airflow.
    - **Affected products:** LimeSDR XTRX. LimeSDR Micro by extension (same RFIC, about 1 W, plus the LA9310; Lime says to design for at least 10 W of cooling).
    - **Frequency:** common
    - **Known fix:** A 40 mm fan (brought it to 50-55 °C) and a thermal pad to a copper pour or heatsink. Monitor the chip temperature in LimeSuiteNG.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/temperature-of-limesdr-xtrx/8366
      - https://discourse.myriadrf.org/t/lms7002m-package-thermal-resistance/13300
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
  8.
    - **Problem:** Weak VHF/UHF sensitivity without an LNA, no internal bias tee, and spurs or images (from RFI pickup, or an analog LPF left wider than the sample rate).
    - **Affected products:** LMS7002M LimeSDRs (Mini, USB, XTRX; the Micro has the same RFIC, with matching optimised only from 300 MHz)
    - **Frequency:** common
    - **Known fix:** An LNA at the antenna with an external bias tee. Set the RX analog bandwidth to match the sample rate (for example -B 22 MHz at 30.72 Msps). Shield the card from the SBC and display. Use the LNAW input-short register (0x010D[1]) to tell internal spurs from RFI.
    - **Fix sources:**
      - https://community.libre.space/t/looking-for-advice-on-sdr/9842
      - https://community.libre.space/t/strf-and-the-limesdr-mini-v2-0/15071
      - https://discourse.myriadrf.org/t/limesdr-xtrx-narrow-internal-spurs-in-rx-spectrum-can-they-be-removed/13288
  9.
    - **Problem:** USB3 SDR streaming on ARM or Qualcomm hosts falls far short of 56-61 Msps (timeouts, NIOS errors, about 15 Msps ceiling).
    - **Affected products:** bladeRF 2.0 micro on Pi 5; USRP B210/B205 on a Qualcomm RB5. B210 clones such as the LibreSDR B220 mini by extension.
    - **Frequency:** common
    - **Known fix:** None reliable. A USB 2.0 port is more stable but limited to about 15-20 Msps. libbladeRF 2.6.0 helped some users. On x86 the same hardware reaches 56 MS/s.
    - **Fix sources:**
      - https://github.com/Nuand/bladeRF/issues/977
      - https://forum.modalai.com/post/9064
  10.
    - **Problem:** Availability: products are sold out or in pre-order, with unconfirmed delivery.
    - **Affected products:** LimeSDR Micro (new orders 'ship Dec 15, 2026', no post-June update), LiteX M2SDR (€699, sold out), HamGeek M2SDR ($376, sold out), uSDR (ships Feb 2027)
    - **Frequency:** common
    - **Known fix:** Order the Micro Basic early and watch Crowd Supply. Of the PCIe alternatives, only the LimeSDR XTRX ($960, mPCIe) and the xSDR (A+E key) were in stock or shipped.
    - **Fix sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
      - https://enjoy-digital-shop.myshopify.com/products/litex-m2-sdr-si5351c
      - https://www.hgeek.com/products/hamgeek-m2sdr-software-defined-radio-m-2-xc7a200-rf-transceiver-module-gpsdo-40m-clock-output
      - https://www.crowdsupply.com/wavelet-lab/xsdr/updates/xsdr-campaign-is-shipping-soon
  11.
    - **Problem:** The Q6A's Kioxia UFS module freezes, stutters and reboots (ufshcd-qcom hibern8/abort errors). That would corrupt long IQ recordings.
    - **Affected products:** Radxa Dragon Q6A with the 256 GB Kioxia UFS module
    - **Frequency:** occasional
    - **Known fix:** A kernel with the PA_TACTIVATE quirk for THGJFGT1E45BAILB (radxa/kernel linux-6.18.2 branch, test package linux-image-6.18.2-4-qcom). Two users confirmed it.
    - **Fix sources:**
      - https://forum.radxa.com/t/ufs-random-reboots/30630?page=2
- **Unresolved problems:**
  1.
    - **Problem:** There is no public confirmation that LimeSDR Micro units have reached backers, and no independent hands-on report exists.
    - **Evidence:** The Crowd Supply updates page has nothing after Jun 17, 2026. The product page says new orders ship Dec 15, 2026. No user reports on MyriadRF Discourse, CNX (0 comments) or the web as of Oct 17, 2026.
    - **Why it matters for us:** The whole wideband path (56-100 MHz view, S-band, full-rate AHRPT) depends on a card that nobody outside Lime has publicly used, so the build schedule can slip by months.
  2.
    - **Problem:** LimeSDR Micro driver support has not been merged into LimeSuiteNG develop, and Lime has validated it only on x86.
    - **Evidence:** The limesdr-micro and limesdr-micro-staging branches are 206 commits ahead of develop (Oct 16, 2026), with overrun, pacing and IRQ fixes still landing in Oct 2026. The OAI slides say 'Validated on x86' and 'Limited sustained stack up-time due to on-going firmware development work'. LimeSuiteNG #196 (kernel control path lock and busy-wait) is open.
    - **Why it matters for us:** SatDump, SDR++ and GNU Radio builds need a stable LimeSuiteNG plus SoapySDR. Early adopters on aarch64 will be debugging, not observing satellites.
  3.
    - **Problem:** No PCIe SDR of any kind has been reported working on a QCS6490 or Dragon Q6A, and Qualcomm SMMU behaviour with these drivers is unknown.
    - **Evidence:** Radxa forum searches (PCIe, M.2, Hailo) found no third-party PCIe device other than NVMe on the Q6A. Qualcomm SMMU firmware traps S2CR bypass writes, which the kernel emulates (LKML patch series). LiteX M2SDR needed SMMU-specific fixes on Jetson. I found no QCS6490 example of iommu.passthrough=1 working.
    - **Why it matters for us:** If DMA returns zeros or SMMU faults, the fallback switches (passthrough, disabling the SMMU) may be ignored or may break display, UFS or the NPU on a Qualcomm board. That would block the chosen architecture.
  4.
    - **Problem:** The Micro's power draw and the Q6A's M.2 3.3 V capacity are not characterized together.
    - **Evidence:** Lime says 'about 4 W, depending on configuration'. The idle question went unanswered, and the setup docs say to design cooling for at least 10 W. The Q6A 3.3 V rail is an ETA3521 'theoretically capable of up to 4A' shared with other peripherals.
    - **Why it matters for us:** Battery runtime, buck-converter sizing and brown-out risk at stream start on a 4S pack. A sagging 3.3 V rail can drop the PCIe link mid-pass.
  5.
    - **Problem:** There are no measured noise figure, sensitivity or return-loss data for the Micro's RX ports.
    - **Evidence:** The Oct 2026 frequency-range thread has no performance data below 300 MHz. The Aug 2026 match-validation thread is unanswered. SatNOGS users call LimeSDRs 'deaf' without a preamp.
    - **Why it matters for us:** Sizing the L-band and S-band LNA chains, and judging whether 435 MHz could move off the RTL-SDR, has to be done by guesswork.
  6.
    - **Problem:** Running PCIe Gen3 through an M.2 2230-to-2280 extender to an SDR card is untested.
    - **Evidence:** On the Q6A only NVMe on an unnamed extender is reported working. On the Pi 5, several adapters made the XTRX enumerate intermittently. LiteX M2SDR on Jetson showed CmpltTO link deaths.
    - **Why it matters for us:** The mechanical design (card overhanging the 85x65 mm board) depends on the extender. Link errors would look like driver bugs.
  7.
    - **Problem:** Sustained USB 3.1 throughput on the Q6A is unmeasured. The only Qualcomm-SoC data point is poor.
    - **Evidence:** A B210 on a Qualcomm RB5 streamed only about 15 MSps against 56 MS/s on x86, and USB3 Ethernet did about 250 Mbps against 520 on a laptop (unresolved, cable or hub confounded). A bladeRF on Pi 5 USB3 still times out on libbladeRF 2.6.0.
    - **Why it matters for us:** This decides whether a USB3 fallback (bladeRF xA4, B220 mini) is viable if the Micro slips or fails. As things stand it may not reach the 56 MHz goal either.
  8.
    - **Problem:** The LiteX M2SDR still has open ARM and Soapy issues, and it is sold out.
    - **Evidence:** #156: link dies under sustained DMA or reload on Jetson, still needs a reboot. #149: SoapySDR returns mostly-zero buffers on the 2026-05-15 gateware. The shop lists €699, out of stock.
    - **Why it matters for us:** It is the best-documented ARM fallback, but it is neither available nor trouble-free. It should not be treated as a guaranteed plan B.
  9.
    - **Problem:** The HamGeek M2SDR and LibreSDR B220 mini have no community track record.
    - **Evidence:** No forum or GitHub user reports were found. HamGeek says its x1 firmware is 'untested' and has a known TX bug below 1.9 MS/s. The only B220 mini thread has no results.
    - **Why it matters for us:** Their GPSDO and price appeal cannot be weighed against unknown driver and quality risk.
  10.
    - **Problem:** Sustained recording of 61.44 Msps sc16 to UFS on the Q6A while also streaming over PCIe is unverified.
    - **Evidence:** After the Kioxia fix, users measured writes of about 0.5 GB/s, but those were short tests. No one has reported concurrent PCIe DMA plus UFS writes, or behaviour under heat.
    - **Why it matters for us:** Raw IQ capture of full-rate HRPT or S-band passes (about 246 MB/s for 10-15 minutes) could drop samples or throttle.
  11.
    - **Problem:** Several communities could not be checked.
    - **Evidence:** Reddit (WebFetch blocked, and a site: search returned nothing), EEVblog (captcha), BATC forum (HTTP 503), Nuand forum (search needs login), Qualcomm developer forum (redirects to a login portal).
    - **Why it matters for us:** Some user reports, particularly Reddit r/sdr and r/RTLSDR posts on bladeRF, B210 clones or early Micro deliveries, may have been missed.
- **Communities checked:**
  - MyriadRF/Lime Discourse (discourse.myriadrf.org, via search.json and topic pages): reachable
  - Crowd Supply: LimeSDR Micro page and updates, xSDR updates
  - GitHub myriadrf/LimeSuiteNG (issues, PRs, branches, commits, compare)
  - GitHub myriadrf/LimeSDR-Micro issues
  - myriadrf.org docs and stories (LimeSDR Micro setup/software pages, OTA posts)
  - OpenAirInterface Summer 2026 workshop slides (Lime)
  - GitHub enjoy-digital/litex_m2sdr (issues #31, #37, #70, #77, #149, #156; host docs)
  - Enjoy Digital shop
  - HamGeek store (hgeek.com)
  - GitHub Nuand/bladeRF issues
  - GitHub wavelet-lab/usdr-lib issues; docs.wsdr.io (landing page only)
  - GitHub SatDump issues/PRs (#1034, #1041); GitHub SDR++ issues
  - Radxa forum (forum.radxa.com, via search.json: PCIe, M.2, USB, kernel headers, Hailo; topics 30400, 30500, 30630, 30807, 30884, 29913, 31611)
  - SatNOGS / Libre Space community (community.libre.space)
  - ModalAI forum (Qualcomm RB5 USB3 + USRP)
  - CNX Software (LimeSDR Micro article: 0 comments)
  - Habr (LibreSDR article, different model), rtl-sdr.com (via search)
  - LKML archives (Qualcomm arm-smmu bypass quirk)
  - Selteq.com.ua (Ukrainian bladeRF listing: xA9 54,900 UAH incl. VAT)
  - Not reachable: Reddit (WebFetch blocked; site: search found nothing), EEVblog (captcha), BATC forum (503), Nuand forum (search requires login), redlib mirror (502), Qualcomm developer forum (login portal)
- **Recommendation impact:** Keep the LimeSDR Micro M.2 2280 Basic ($249 + $18) as plan A, but treat it as an unverified, early-adopter part, not a known-good one. As of Oct 17, 2026 there is no public proof that units shipped. Driver support is still on unmerged branches, about 206 commits ahead of develop, with streaming fixes landing every week. Lime validates only on x86 and admits limited sustained uptime. Nobody has run any PCIe SDR on a QCS6490.
  
  Practical consequences:
  (1) Build and commission the narrowband RTL-SDR path first (the budget option). It should be the station's working baseline until the Micro streams reliably on the Q6A.
  (2) When the Micro arrives, bring it up in this order:
  - test the M.2 slot with a cheap NVMe drive first (one Q6A slot was dead);
  - pin the Q6A kernel, build la9310_limesdr against exact headers, and rebuild before any kernel update (Q6A kernels moved 6.18 to 7.2 in 2026 and broke out-of-tree modules);
  - check page size and dmesg for SMMU faults;
  - run a long RX-only soak at 30-61 Msps before any field use;
  - record IQ first and decode offline (SatDump users lose packets decoding live at high rates).
  (3) Mechanical and power: budget about 4 W typical and design cooling for 10 W (fan plus pad). XTRX users saw 60-85 °C without airflow. The 3.3 V comes from the Q6A's shared ETA3521 rail, and the 12 V header tops out at 16 V, so a 4S pack needs a regulator.
  (4) RF: keep VHF on the RTL-SDR. Put LNAs at the antennas with an external bias tee. Set the LMS7002M analog bandwidth to match the sample rate to avoid images, and shield the card from the SBC and display.
  (5) Storage: run the Kioxia UFS module only on a kernel with the PA_TACTIVATE fix.
  (6) Do not pre-buy a fallback. The LiteX M2SDR (€699) and HamGeek M2SDR ($376) are sold out, and even the M2SDR's mature driver still has open ARM link-death and SoapySDR zero-buffer bugs. USB3 alternatives look weak on Qualcomm and ARM hosts: a B210 got about 15 Msps on a Qualcomm RB5, and the bladeRF has Pi 5 USB3 timeouts. A bladeRF or B220 only makes sense after someone measures the Q6A's USB 3.1 throughput.
  
  Confidence in the Micro being the right pick stays medium. Confidence that it will work on the Q6A on day one is low to medium.

## Власні виправлення (`fixes`)

_Run `wf_e64436d6-ae7`_

- **Component:** Wideband PCIe SDR: LimeSDR Micro M.2 2280 in the M.2 slot of the Radxa Dragon Q6A
- **Fixes:**
  1.
    - **Problem:** There is no public confirmation that LimeSDR Micro units have shipped, and no independent hands-on report exists.
    - **Proposed fix:** Make the Micro a cancellable dependency that blocks nothing. Pre-order the Basic now. Crowd Supply lets you cancel a pre-order for a full refund any time before it ships. Before the card arrives, validate everything around it: driver build, M.2 bay, thermal path, scheduling latency and UFS throughput, using a 2280 NVMe as a stand-in. Set a hard decision date. The fallback choice is decided by a USB3 test you run now (see the USB3 fix). On arrival, run an acceptance test and publish the results; that becomes the missing independent report.
    - **Steps:**
      - Order the LimeSDR Micro M.2 2280 Basic: $249 plus $18 worldwide shipping. The product page (checked Oct 2026) says 'Pre-order, ships Dec 15, 2026'. The campaign was funded May 28 with 130 backers, and the last update is dated Jun 17, 2026. Skip the GNSS variant.
      - Track progress weekly in two places. Code: in a LimeSuiteNG clone, run `git fetch && git log --since=2.weeks --oneline origin/limesdr-micro-staging`. Recent commits are from Oct 16, 2026, for example 'implement Rx timestamps recovery after overruns'. Forum: `curl -s 'https://discourse.myriadrf.org/search.json?q=limesdr%20micro%20order:latest'`.
      - Until delivery, run all narrowband work on the RTL-SDR V4/V4L: LRPT, SSTV, CubeSats, QO-100 narrowband through the LNB IF, and Meteor HRPT at about 2.4-3.2 Msps.
      - Build the 2280 M.2 bay, heatsink and cable routing now. Put a cheap 2280 NVMe in it as a placeholder to test the extender, thermals and PCIe+UFS concurrency (see those fixes).
      - Decision gate, 31 Jan 2027. If there is still no shipping notice, choose from measured data. If the USB3 gate test passes (at least 350 MB/s sustained), buy the bladeRF 2.0 micro xA4 ($540, in stock, built-in bias tees). If it fails, keep waiting, because every PCIe alternative is sold out (LiteX M2SDR) or has the wrong key (xSDR is A+E).
      - Do not buy a HackRF clone as a stopgap. Prom.ua listings looked like roughly 10,000-15,000 UAH (I did not verify individual listings), which is close to the Micro's price for an 8-bit, 20 Msps radio.
      - On arrival, run the acceptance script: `limeDevice --full`, check dmesg, then 15-minute `limeTRX` runs at 7.68, 30.72 and 61.44 Msps while logging loss/overrun counts, temperatures and power. Post the results on MyriadRF Discourse.
    - **How to verify:** The order page shows a pre-order you can cancel. The fallback is chosen from logged USB3 measurements, not guesses. On arrival, the acceptance runs show 0 loss events at the sample rate you actually need.
    - **Confidence:** high
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
      - https://www.crowdsupply.com/lime-micro/limesdr-micro/updates
      - https://crowdsupply.com/guide/policies-and-procedures
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro-staging
      - https://prom.ua/ua/search?search_term=hackrf%20one
      - https://www.nuand.com/product/bladerf-xa4/
  2.
    - **Problem:** Micro support is not merged into LimeSuiteNG develop (limesdr-micro-staging is 206 commits ahead of and 163 behind develop as of Oct 16, 2026), and Lime has validated it only on x86. The Q6A runs Radxa's 7.0.11-qcom kernel.
    - **Proposed fix:** Build and pin the staging branch on the Q6A (aarch64) now, before the hardware arrives. Kernel driver, host library and firmware must all come from the same commit, because the driver rejects firmware whose HIF version does not match. Install the la9310_limesdr kernel module through DKMS against Radxa's own header package, and confirm it compiles and loads on kernel 7.0 while there is still time to fix problems.
    - **Steps:**
      - Install the build dependencies: `sudo apt install linux-headers-radxa-dragon-q6a dkms build-essential cmake git pkg-config libusb-1.0-0-dev libsoapysdr-dev soapysdr-tools`. Radxa's linux-qcom packaging (7.0.11-7, Sep 17, 2026) builds a linux-headers-radxa-dragon-q6a package.
      - Clone and pin a commit: `git clone -b limesdr-micro-staging https://github.com/myriadrf/LimeSuiteNG && cd LimeSuiteNG && git checkout 37cb1833`, the branch head as of 2026-10-16. Write the hash down. The prebuilt firmware (firmware/limesdr-micro/limesdr-micro-m4.bin, limesdr-micro-iqplayer.eld and limesdr-micro-eeprom.bin) lives in the same commit and is installed by INSTALL_FIRMWARE=ON.
      - Configure, build and install: `cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_DRIVERS_LA9310=ON -DBUILD_DRIVERS_LIMEPCIE=OFF -DLA9310_LIMESDR_DKMS=ON -DBUILD_PLUGINS_SOAPYSDR=ON -DBUILD_GUI=OFF && cmake --build build -j8 && sudo cmake --install build && sudo ldconfig`.
      - Confirm the module works on kernel 7.0 without hardware: `dkms status`, `modinfo la9310_limesdr`, `sudo modprobe la9310_limesdr; dmesg | tail`. The source already has version guards for kernel 6.3, 6.4, 6.10 and 6.16 API changes, but nobody has reported building it on 7.0.
      - Load the module at boot: `echo la9310_limesdr | sudo tee /etc/modules-load.d/la9310.conf`. The driver kzalloc()s two 4 MiB physically contiguous DMA buffers (scratch and IQ flood), and that allocation can fail on a fragmented system after a long uptime.
      - Check `SoapySDRUtil --info` lists the limesuiteng module. Build SatDump and SDR++ against the same system SoapySDR (0.8.x).
      - Freeze the kernel for field use: `sudo apt-mark hold linux-image-radxa-dragon-q6a linux-headers-radxa-dragon-q6a`. Radxa moved from 6.18 to 7.0 during 2026. Try new kernels on a spare SD card first; DKMS rebuilds automatically, but the driver may not.
      - Move to Lime's arm64 APT repo (repo.myriadrf.org) or a tagged release only after the Micro code reaches develop and your acceptance test passes again.
    - **How to verify:** `dkms status` shows la9310_limesdr installed for `uname -r`, and modprobe loads it with no oops. With the card fitted, dmesg shows 'using 64bit DMA mask', 'HIF Version', and an 'IQ Flood Buffer size: 4194304' line with no errors, and `limeDevice --full` lists the LimeSDR Micro.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro-staging/drivers/linux/la9310_limesdr
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/docs/user/linux/apt.rst
      - https://github.com/radxa-pkg/linux-qcom
      - https://forum.radxa.com/t/dragon-q6a-fastrpc-npu-fails-fastrpc-ioctl-init-create-returns-0x80000600-on-cdsp/31078
  3.
    - **Problem:** New finding from the code: the receive DMA ring holds only about 1.1-1.6 ms of samples, so a non-realtime aarch64 system will drop samples. In LA9310_TRX.cpp, RxSetup uses 16 transfers (SubdivideBuffer(..., 16 KB, 16)), each sized to about 100 µs of samples. At 61.44 Msps that is 16 x 16 KB = 256 KB = 1.07 ms. At 7.68 Msps it is 16 x 2 KB, again 1.07 ms. The RX worker thread 'lime:Rx0' runs at normal priority (the SetOSThreadPriority call is commented out). Any scheduling stall over about 1 ms (UFS writeback, GPU, compositor) overwrites data and shows up as 'loss' or 'samples discontinuity'. This is a likely reason it was validated on x86 only.
    - **Proposed fix:** Measure scheduling latency now. Then make the RX thread realtime and pin it to an A78 core, enable full preemption, and deepen the ring to 32 transfers. The VSPA TCD and output-block FIFOs are 32 deep (MFIFO_SIZE=32), and every transfer can use the full 16 KB batch. The resulting buffer depth is 2.1 ms at 61.44 Msps, 4.3 ms at 30.72 Msps and about 17 ms at 7.68 Msps.
    - **Steps:**
      - Before the card arrives: `sudo apt install rt-tests stress-ng fio`. Run the UFS write load (fio at 250 MB/s) with SDR++ and the display active, plus `sudo cyclictest -m -S -p 80 -i 200 -h 2000 -D 15m -q`. Record the maximum latency for each CPU.
      - Add `preempt=full` to the kernel command line; Radxa's kernel is PREEMPT_DYNAMIC. Set `sudo cpupower frequency-set -g performance`, because Radxa's config defaults to ondemand. Optionally add `isolcpus=7 nohz_full=7 rcu_nocbs=7`. Re-run cyclictest; the target is under 300 µs on the chosen core.
      - After SatDump or SDR++ starts, run `for t in /proc/$(pgrep -f satdump)/task/*; do [ "$(cat $t/comm)" = "lime:Rx0" ] && sudo chrt -f -p 70 ${t##*/} && sudo taskset -cp 7 ${t##*/}; done`. This is safe because usePoll defaults to true, so the thread blocks waiting for an interrupt (WaitSIRQ). Never give SCHED_FIFO to a busy-yield loop.
      - Quick test with no code change: `limeTRX --rxPacketsInBatch 8 --time 900000 -o /dev/null -l info` at low sample rates. This makes every transfer 16 KB.
      - Two-line library patch in src/boards/LimeSDR_Micro/LA9310_TRX.cpp: change `SubdivideBuffer(rx_lane_dma_mem[l], dmaBatchSize, 16)` to `..., 32)`. After packetsToBatch is computed, set `mRx.packetsToBatch = dmaBatchSize / packetSize;`. Rebuild, and keep the patch with the pinned commit.
      - In /proc/interrupts, watch the PCI-MSI line for the card (about 15k interrupts/s at 61.44 Msps with 16 KB transfers). Test with that IRQ on the same A78 core as lime:Rx0 and on a different one.
    - **How to verify:** The LimeSuiteNG stream log (limeTRX -l info) reports overrun and loss deltas. Targets: 0 loss in 15 minutes at 61.44 Msps while UFS records in parallel, and 0 loss in 1 hour at decode rates (7.68 Msps). If the 32-entry ring breaks streaming (garbage samples or VSPA timeouts), revert to 16 and report it to Lime; the VSPA firmware may assume 16.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LA9310_TRX.cpp
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/chips/LA9310/firmware/dma_tcd_fifo.h
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/chips/LA9310/firmware/IQStreamer_DMA.cpp
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/cli/limeTRX.cpp
      - https://github.com/radxa-pkg/linux-qcom
  4.
    - **Problem:** No PCIe SDR has been reported working on a QCS6490 or Q6A, and it is unknown how Qualcomm's SMMU behaves with these drivers.
    - **Proposed fix:** Most of this risk goes away on inspection. Radxa's vendor device tree (kernel linux-7.0.11) lists devices tested on the M.2 PCIe controller: QPS615, ASM1182e and ASM2824 switches, an NVIDIA dGPU and a Chelsio T520-CR 10GbE NIC. It maps every requester ID to SMMU stream 0x1c80, and kodiak.dtsi marks pcie1 dma-coherent. la9310_limesdr uses the standard DMA API: a 64-bit dma_set_mask_and_coherent, kzalloc plus dma_map_single, and the resulting IOVA programmed into the LA9310's outbound address translation. A NIC uses the same path, so SMMU translation should be transparent. MSI goes through the DesignWare controller's internal MSI (msi0-msi7). Keep translation on. If context faults appear, switch only this device's IOMMU group to identity at runtime. Do not set iommu.passthrough=1 globally, because it can also affect the NPU (FastRPC), video and display.
    - **Steps:**
      - Before the card arrives, the NVMe stand-in proves DMA through the SMMU on this slot. Radxa measured 1467 MB/s write.
      - On first boot with the card: `sudo dmesg | grep -iE 'la9310|smmu|iommu|qcom-pcie'` and `ls -l /sys/bus/pci/devices/0001:01:00.0/iommu_group`. pcie1 is PCI domain 1.
      - Stream for 10 minutes and watch for `arm-smmu 15000000.iommu: Unhandled context fault ... iova=0x... cbfrsynra=0x1c80`. Compare the faulting IOVA with the 'bus:0x...' addresses the driver prints for the scratch and IQ flood buffers. A fault outside those ranges means the firmware is writing somewhere it was never mapped.
      - If faults appear: `D=0001:01:00.0; G=$(basename $(readlink /sys/bus/pci/devices/$D/iommu_group)); echo $D | sudo tee /sys/bus/pci/drivers/la9310_limesdr/unbind; echo identity | sudo tee /sys/kernel/iommu_groups/$G/type; echo $D | sudo tee /sys/bus/pci/drivers/la9310_limesdr/bind`. The kernel's iommu_group_store_type only refuses while a DMA-API driver is bound. Make it persistent with a systemd oneshot that runs before modprobe.
      - Only if that fails: try `iommu.passthrough=1` from a spare boot entry, and check that the NPU (FastRPC), HDMI and UFS still work.
      - If the link drops on idle-to-stream transitions, also test `pcie_aspm=off`.
    - **How to verify:** No SMMU faults in 1 hour of streaming. Samples are non-zero and a known carrier (for example the QO-100 beacon on the IF) is visible. The NPU demo still runs.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/boot/dts/qcom/kodiak.dtsi
      - https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://github.com/torvalds/linux/blob/master/drivers/iommu/iommu.c
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/drivers/linux/la9310_limesdr/la9310_pci.c
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/drivers/linux/la9310_limesdr/la9310_base.c
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/nvme
  5.
    - **Problem:** The Micro's power draw and the Q6A M.2 3.3 V capacity have not been characterized together, raising brown-out and runtime concerns.
    - **Proposed fix:** The Q6A schematic (v1.21, M_KEY page) settles the rail question. The M.2 slot has its own ETA3521 buck, U20, running from VCC_5V_PERI to VCC_3V3_MKEY. It uses a 1 µH/4 A inductor (L24) and 3x 22 µF output capacitors, and the divider R88 91k / R133 20k gives 0.6 x (1 + 91/20) = 3.33 V. The ETA3521 is rated at 4 A. This regulator is not the one feeding the 40-pin header's 3.3 V. Lime says the Micro draws 'about 4 W, depending on configuration' (about 1.2 A at 3.3 V), and calls 2.5 A the M.2 specification allowance. That leaves about 3x margin. What remains is to measure the real draw and the thermal behaviour.
    - **Steps:**
      - Fit an INA226 module (about $2-5) with a 10 mΩ shunt in the 12 V feed to the Q6A, read over I2C on the 40-pin header with the ina2xx hwmon driver or python smbus2. It doubles as battery and power telemetry for the UI. Log idle, then streaming at 7.68, 30.72 and 61.44 Msps with 1 and 2 RX channels. Micro power is roughly ΔP at 12 V x 0.8, since the board converts 12 V to 4.2 V (SY81012), then 5 V, then 3.3 V.
      - Budget 5 W at 12 V for the Micro until you have measurements. VCC_5V_PERI also feeds the USB ports (RTL-SDR plus LNA bias tee), the HDMI 5 V and the USB hub, so keep extra 5 V loads small.
      - For brown-out, run `dmesg -w` across 20 stream start/stop cycles and check `lspci -vv -s 0001:01:00.0 | grep LnkSta` after each one.
      - If the link drops at stream start, add a 220-470 µF low-ESR polymer capacitor across 3.3 V and GND at the card end of the extender or breakout.
      - Thermal: Lime says to design for at least 10 W. Use thermal pads of mixed thickness, since components reach about 4 mm, under an aluminium heatsink in the fan's airflow. Every 10 s, log `readSensor("lms7_temp")` through SoapySDR Python and the 'Board Temperature' custom parameter (TMP1075) through LimeSuiteNG.
    - **How to verify:** Measured ΔP is 5 W or less. There are no link-down events over 20 start cycles. In a 30-minute run at 61.44 Msps and 35 °C ambient, board temperature levels off below about 70 °C.
    - **Confidence:** high
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2403151643_etasolution-ETA3521FSG_C22362743.pdf
      - https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
      - https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
      - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/plugins/soapysdr/Settings.cpp
  6.
    - **Problem:** There are no measured noise figure, sensitivity or return-loss figures for the Micro's RX ports.
    - **Proposed fix:** Design the chain so the Micro's noise figure barely matters, then measure the whole system with a sky/ground Y-factor. For chip-level reference, Lime's LMS7002M measurement report gives a DSB noise figure at maximum gain of about 2 dB at 800 and 1850 MHz and about 4 dB at 2600 MHz. It rises to 5-12 dB at low gain or away from the matched frequency. Board-level figures will be worse. One LNA with at most 1 dB NF and at least 18 dB gain at the antenna fixes this: for example the RTL-SDR Blog Wideband LNA V2 (QPL9547, about 1 dB and 15-20 dB on the board). By the Friis formula, a 1 dB/18 dB LNA, then 1 dB of cable, then a Micro at 6 dB NF gives a 1.2 dB system NF. With the Micro at 10 dB, the system is still only 1.6 dB.
    - **Steps:**
      - 1.7 GHz chain: helix, 1.7 GHz SAW filter, LNA powered by bias tee, at most 1 m of low-loss coax, then X2 (RX-A). S-band 2.2-2.3 GHz: S-band filter, LNA, then X3, using the LNAW path (0.7-2.6 GHz), since LNAL is only matched up to 2.2 GHz. QO-100 IF at about 740 MHz: the LNB's gain is enough, so no extra LNA.
      - At 1.7 GHz, try both LNAL (0.3-2.2 GHz) and LNAW, which both cover the band, and keep whichever gives the higher Y-factor.
      - Set gain: raise RX gain until the sky noise floor stops rising relative to the ADC floor, then back off about 3 dB. Keep the strongest in-band signal well below the +10 dBm damage limit and below compression.
      - Y-factor test: point the antenna at cold sky (above 40° elevation, away from the Sun), then at ground or trees. Measure mean power in a quiet sub-band with SDR++'s averaged FFT or a short Python script. Y = P_ground / P_sky. Then Trx = (290 - Y x Tsky) / (Y - 1), with Tsky about 30-50 K including spillover. A system NF near 1 dB (Trx about 75 K) should give a Y of about 5 dB at 1.7 GHz.
      - On the same pass, compare the identical LNA chain into the RTL-SDR V4 and into the Micro, using SatDump SNR and Viterbi BER on Meteor HRPT.
      - Optional: a NanoVNA V2 (to 3 GHz) measures X2/X3 S11 at 435, 740, 1700 and 2250 MHz.
    - **How to verify:** The sky/ground Y-factor with the Micro is within 0.5 dB of the RTL-SDR plus the same LNA. HRPT locks from about 10° elevation and decodes cleanly above 20°.
    - **Confidence:** high
    - **Sources:**
      - https://www.limemicro.com/downloads/lms7002m_measurements-v1_05.pdf
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp
      - https://www.qorvo.com/products/p/QPL9547
      - https://www.passion-radio.com/accessoires-sdr/filtre-adsb-764.html
      - https://discourse.myriadrf.org/t/limesdr-micro-m-2-pcie-frequency-range/13348
  7.
    - **Problem:** Running PCIe Gen3 through an M.2 2230-to-2280 extender to an SDR is untested, and link errors would look like driver bugs.
    - **Proposed fix:** First choice is no extender: plug the 80 mm card straight into the 2230 slot and support its far end. Use an extender only if the board's layout forces it, and then the shortest Gen4-rated shielded flex. Measure link errors directly with the PCIe status registers and the DesignWare RAS-DES counters. If errors appear, force Gen2. Gen2 x1 still carries one channel at 61.44 Msps but not two.
    - **Steps:**
      - Check the geometry. If the 80 mm card can run past the board edge, or over an area with no tall components, plug it in directly and support the 80 mm end with a 3D-printed post and an M2 screw. The B+M-keyed card fits the M-key socket.
      - Otherwise use the shortest available Gen4-rated M.2 M-key to M-key flex, for example the ADT-Link R44SF family. Newegg lists the 20 cm version at $39.99; shorter AliExpress lengths and prices are not verified.
      - Check the link: `sudo lspci -vv -s 0001:01:00.0 | grep -E 'LnkCap|LnkSta'` should show 8GT/s x1. Read and clear the error status with `sudo setpci -s 0001:01:00.0 CAP_EXP+0a.w` and `sudo setpci -s 0001:01:00.0 CAP_EXP+0a.w=000f`. The CESta/UESta lines in `lspci -vvv` for 0001:00:00.0 and the card also latch errors.
      - If the kernel has CONFIG_PCIE_DW_DEBUGFS, enable and read /sys/kernel/debug/dwc_pcie_1c08000.pcie/rasdes_event_counter/{lcrc_err,receiver_err,bad_tlp,replay_timeout}/counter_value.
      - Run a 15-minute 61.44 Msps stream; with the stand-in NVMe, run `fio --rw=read --bs=1M --direct=1 --iodepth=16 --runtime=900` instead. Any correctable errors mean you should force Gen2: `sudo setpci -s 0001:00:00.0 CAP_EXP+30.w=0002:000f; sudo setpci -s 0001:00:00.0 CAP_EXP+10.w=0020:0020`. To make it persistent, add a device-tree overlay `&pcie1 { max-link-speed = <2>; };`; the DesignWare driver reads max-link-speed.
      - At Gen2 x1 (about 400 MB/s usable), limit use to one RX channel at 61.44 Msps (246 MB/s). Two channels need 492 MB/s, because the card always DMAs 16-bit complex samples; I12 conversion happens on the host after the DMA.
    - **How to verify:** 0 correctable errors and an unchanged LnkSta after 1 hour at the chosen link speed, and 0 sample-loss events at the same time.
    - **Confidence:** medium
    - **Sources:**
      - https://www.newegg.com/p/2S7-01Z1-00EH8
      - https://github.com/torvalds/linux/blob/master/drivers/pci/controller/dwc/pcie-designware-debugfs.c
      - https://github.com/torvalds/linux/blob/master/drivers/pci/controller/dwc/pcie-designware.c
      - https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LA9310_TRX.cpp
  8.
    - **Problem:** Sustained USB 3.1 throughput on the Q6A is unmeasured, so a USB3 fallback (bladeRF xA4, B220 mini) cannot be judged.
    - **Proposed fix:** Run a cheap gate test now with a USB3 NVMe enclosure, after tuning the USB stack. The vendor device tree runs usb_1 in host mode, with USB3 on two lanes of the USB/DisplayPort combo PHY and DisplayPort on the other two (mdss_dp data-lanes <0 1>, feeding the RA620 HDMI bridge). USB3 and HDMI can therefore run at the same time.
    - **Steps:**
      - Tune first: `echo 0 | sudo tee /sys/module/usbcore/parameters/usbfs_memory_mb` (0 removes the limit libusb SDRs hit), add `usbcore.autosuspend=-1` to the kernel command line, set the performance governor, and pin the xHCI interrupt (`grep -i xhci /proc/interrupts`, then write an A78 core mask to /proc/irq/N/smp_affinity).
      - Gate test: put a USB3 NVMe enclosure (about $15-20) on the USB 3.1 Type-A port and run `sudo fio --name=usb --filename=/dev/sdX --rw=read --bs=1M --direct=1 --ioengine=libaio --iodepth=16 --time_based --runtime=900`. Repeat with --rw=write, and log CPU with `mpstat -P ALL 5`.
      - Pass means at least 350 MB/s sustained for 15 minutes using less than 50% of one core. That makes a 61.44 Msps USB3 SDR (246 MB/s) viable. Below 250 MB/s, a USB fallback is capped at about 20-30 Msps.
      - Optional libusb-level test: an FX3 SuperSpeed Explorer kit (CYUSB3KIT-003, about £56-93 at Farnell) running the streamer firmware. FX3 is the same USB3 chip used in the bladeRF and B210.
      - If you buy an SDR: UHD args `num_recv_frames=256,recv_frame_size=16360` for B2xx clones; bladeRF via SoapyBladeRF with larger buffers/transfers settings.
    - **How to verify:** fio bandwidth and mpstat logs. With a real SDR, `benchmark_rate --rx_rate 61.44e6 --duration 600` (UHD) or a 10-minute bladeRF-cli receive to /dev/null reports zero overflows.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://uk.farnell.com/infineon/cyusb3kit-003/dev-board-usb-controller/dp/2448471
      - https://www.nuand.com/product/bladerf-xa4/
  9.
    - **Problem:** Sustained recording at 61.44 Msps sc16 to UFS while streaming over PCIe is unverified.
    - **Proposed fix:** Recording at the full rate is mainly a capacity problem. 61.44 Msps sc16 is 245.76 MB/s, so one 15-minute pass is 221 GB, almost the whole 256 GB UFS module. Use tiered capture instead: (1) record only what decoding needs, which is 7.68 Msps (AHRPT and Meteor HRPT need about 3-8 Msps): 30.7 MB/s in cs16, about 28 GB per pass, or half that in cs8 or SatDump's ZIQ; (2) send 61.44 Msps only into a RAM ring and write snapshots to disk on a trigger; (3) prove PCIe and UFS concurrency now with the NVMe stand-in. The Kioxia UFS stalls were fixed by Radxa's PA_TACTIVATE quirk in May 2026, and measured writes after the fix were about 473 MB/s.
    - **Steps:**
      - Check that the UFS fix is present: run `uname -r` (7.0.11-qcom or later), and check that `dmesg | grep -iE 'ufshcd|ufs'` shows no errors over 1 hour.
      - Concurrency test with the 2280 NVMe stand-in in the M.2 bay: `sudo fio --name=dma --filename=/dev/nvme0n1 --rw=read --bs=1M --direct=1 --ioengine=libaio --iodepth=8 --rate=260m --time_based --runtime=900 &` while running `sudo fio --name=rec --directory=/data --size=200G --rw=write --bs=4M --direct=1 --ioengine=libaio --iodepth=4 --rate=250m --time_based --runtime=900 --write_bw_log=rec --log_avg_msec=1000`. Run cyclictest alongside, and log `/sys/class/thermal/thermal_zone*/temp`.
      - Pass means per-second write bandwidth never drops below 250 MB/s, no ufshcd errors, and the SoC stays below about 85 °C.
      - For buffered writers such as SatDump, set `sudo sysctl vm.dirty_background_bytes=268435456 vm.dirty_bytes=1073741824` and mount the data partition with noatime (ext4), or use f2fs.
      - RAM ring for wideband snapshots: `sudo mount -t tmpfs -o size=8G tmpfs /mnt/iqring`. 8 GB holds about 32 s at 61.44 Msps. Copy to UFS after the pass, or when the NPU classifier triggers.
      - For decode recordings, use 7.68 Msps (the Micro needs at least 7 Msps without decimation; otherwise use the Soapy OVERSAMPLING setting) in cs8 or ZIQ format.
    - **How to verify:** The fio bandwidth logs stay at or above 250 MB/s for 15 minutes. With the Micro, recordings show 0 loss events, and each file's size equals rate x duration x bytes per sample.
    - **Confidence:** medium
    - **Sources:**
      - https://forum.radxa.com/t/ufs-random-reboots/30630
      - https://raw.githubusercontent.com/SatDump/SatDump/master/src-core/common/dsp/io/baseband_type.h
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/plugins/soapysdr/Settings.cpp
  10.
    - **Problem:** The LiteX M2SDR still has open Arm and SoapySDR issues and is sold out.
    - **Proposed fix:** Do not count it as plan B. Both issues are still open: #156 (opened Jul 27, 2026; last comment Jul 28) is a link death under sustained DMA on a Jetson with an active SMMU, root cause unknown; #149 (opened Jul 22, 2026) is SoapySDR returning mostly-zero buffers on the 2026-05-15 gateware. If you do get one, use it the way the reporters got clean data.
    - **Steps:**
      - Use the C tools (m2sdr_rf, m2sdr_record), not SoapySDR, until #149 is fixed.
      - Run `m2sdr_rf --calibrate-delay` after every sample-rate change, because changing the AD9361 rate resets the interface delay.
      - Build the driver with PR #157 (AER error_detected/slot_reset handlers) so a fatal PCIe event does not hang the host.
      - Start at Gen2 x1 and step up only after 1 hour with no errors.
      - Pre-order only where the pre-order is cancellable.
    - **How to verify:** m2sdr_record files contain more than 99% non-zero samples, and a 1-hour stream has no AER fatal events.
    - **Confidence:** high
    - **Sources:**
      - https://github.com/enjoy-digital/litex_m2sdr/issues/156
      - https://github.com/enjoy-digital/litex_m2sdr/issues/149
      - https://github.com/enjoy-digital/litex_m2sdr
  11.
    - **Problem:** The HamGeek M2SDR and LibreSDR B220 mini have no community track record.
    - **Proposed fix:** Avoid both as fallbacks. If the USB3 gate passes, choose the bladeRF 2.0 micro xA4 instead: it is in stock, vendor-supported, has bias tees and a mature libbladeRF. If you buy a clone anyway, buy where returns are possible and run an acceptance test inside the return window.
    - **Steps:**
      - `uhd_find_devices` and `uhd_usrp_probe`: check that the FPGA image matches your UHD version and that the B210-mode USB or PCIe enumeration is stable across 10 reboots.
      - `benchmark_rate --rx_rate 30.72e6 --duration 600`, then the same at 61.44e6: zero overflows (no 'O' markers).
      - Check frequency error against a known carrier, for example the QO-100 beacon on the IF or a GSM/LTE downlink. Compare with the claimed ±0.5 ppm VCTCXO, and check GPSDO lock on the HamGeek if it is fitted.
      - Decode one real Meteor HRPT pass in SatDump and compare SNR with the RTL-SDR plus the same LNA.
    - **How to verify:** All four checks pass inside the return window; otherwise return the unit.
    - **Confidence:** medium
    - **Sources:**
      - https://www.hgeek.com/products/hamgeek-m2sdr-software-defined-radio-m-2-xc7a200-rf-transceiver-module-gpsdo-40m-clock-output
      - https://www.sdrstore.eu/software-defined-radio/instruments/plutosdr/70mhz-6ghz-2r2t-b210-mini-ad9361-sdr-development-board-libresdr-uhd-pluto-oai-support/
      - https://www.nuand.com/product/bladerf-xa4/
  12.
    - **Problem:** Several communities could not be checked (Reddit, EEVblog, BATC, Nuand forum, Qualcomm forum).
    - **Proposed fix:** Use the Discourse JSON APIs, which return clean data where HTML scraping fails; both worked in this research. Check the blocked sites by hand in a normal browser once a month.
    - **Steps:**
      - `curl -s 'https://discourse.myriadrf.org/search.json?q=limesdr%20micro%20order:latest'` and `curl -s 'https://forum.radxa.com/search.json?q=q6a%20pcie'`. Read whole threads with `/t/<id>.json`. Stay within rate limits; MyriadRF throttles bursts.
      - Check by hand: r/RTLSDR and r/sdr (search 'LimeSDR Micro', 'bladeRF Pi 5', 'B210 clone'), EEVblog RF section, BATC forum QO-100 threads, and the Nuand forum after logging in.
      - Post your own Q6A acceptance results (fixes 1-3) on MyriadRF Discourse and the Radxa forum.
    - **How to verify:** A monthly search log with dates and links, and replies to your posts.
    - **Confidence:** high
    - **Sources:**
      - https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
      - https://forum.radxa.com/t/radxa-q6a-4s1p-powering/31611
- **Residual risks:**
  - Delivery date is outside your control. Crowd Supply says 'ships Dec 15, 2026', and there has been no project update since Jun 17. Your acceptance test will probably be the first independent data on this board.
  - The 32-entry RX ring patch is untested. If the VSPA firmware assumes 16 entries, only realtime scheduling remains, which leaves about 1.07 ms of buffering at 61.44 Msps. Full-rate streaming would then depend on worst-case latency staying low.
  - No one has publicly built or run la9310_limesdr on Linux 7.0 or the QCS6490. A Lime firmware or HIF change can also break a mixed setup, so driver, library and firmware must stay on one commit.
  - Forcing Gen2 because of extender signal integrity rules out 2 x 61.44 Msps, since the card always DMAs 16-bit samples. Only one full-rate channel would then be possible.
  - The 12 V header accepts 4.5-16 V (Radxa staff, Oct 15, 2026). A 4S Li-ion pack reaches 16.8 V when full, so it must be regulated before the board. That belongs to the power component, but a brown-out or overvoltage would also take out the SDR.
  - HDMI is a 2-lane DisplayPort feeding the RA620 bridge, on the same combo PHY as USB3 (vendor device tree mdss_dp data-lanes <0 1>). Whether a high-resolution sunlight-readable HDMI panel works on 2 lanes needs checking by the display component. There was also a Linux 7.0 HDMI regression thread on the Radxa forum (Aug 2026).
  - Global iommu.passthrough=1 may break the NPU (FastRPC), video or display. Use only the per-group identity switch.
  - The upstream device tree maps the endpoint to SID 0x1c81, while Radxa's maps everything to 0x1c80. Distributions using mainline device trees, such as Armbian, may behave differently from Radxa's image.
  - Not verified: the AliExpress M.2 extender prices and lengths, Prom.ua prices for individual listings, the UAH/USD rate, and Ukrainian import VAT or duty.
  - Micro noise figure and power figures are still Lime's statements or chip-level data until you measure them. The Friis margin covers the noise figure risk only if an LNA with at least 18 dB gain sits at the antenna.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e64436d6-ae7`_

- **Component:** Wideband PCIe SDR (M.2 slot of the Radxa Dragon Q6A): LimeSDR Micro M.2 2280
- **Recommendation holds:** так
- **Issues:**
  1.
    - **Claim:** v3 stack: LimeSDR Micro costs $199 on Crowd Supply.
    - **Problem:** The $199 early-bird price ended in May 2026. The page also leaves out the Ukrainian landed cost.
    - **Correction:** Basic (no GNSS) is $249 + $18 worldwide shipping; GNSS is $299. Crowd Supply does not prepay VAT for Ukraine, so the buyer pays the duty. Under the current rules that is 10% duty + 20% VAT on the value above EUR 150, roughly $30-35 on this parcel, plus any courier brokerage fee. The Rada passed the repeal of the EUR 150 exemption on Oct 15, 2026; its effective date is not confirmed and is probably 2027. Plan on about $300-320 landed, plus $12-18 for MHF4L-SMA cables.
    - **Source:** https://www.crowdsupply.com/lime-micro/limesdr-micro ; https://www.crowdsupply.com/guide/fulfillment-and-logistics ; https://english.nv.ua/nation/tax-exemption-for-international-packages-worth-up-to-150-euros-repealed-by-ukraine-s-parliament-50650346.html
  2.
    - **Claim:** v3: deliveries from about Sept 30, 2026. Research: latest updates are Jun 17 and Jul 31, 2026.
    - **Problem:** The updates page lists only 8 updates and the newest is Jun 17, 2026 ('component sourcing has started… ship in September'). There is no Jul 31 update. Nobody has confirmed a backer delivery on Crowd Supply, MyriadRF Discourse (searched Oct 18) or the web.
    - **Correction:** Treat it as a pre-order with no confirmed shipments. New orders show 'ships Dec 15, 2026'. Ukraine is not on Crowd Supply's restricted-country list, and store orders can be cancelled for a full refund before shipment.
    - **Source:** https://www.crowdsupply.com/lime-micro/limesdr-micro/updates ; https://discourse.myriadrf.org/search.json?q=limesdr%20micro%20order:latest ; https://www.crowdsupply.com/guide/policies-and-procedures
  3.
    - **Claim:** v3: install the card in the Q6A slot 'via a 2230->2280 extension'.
    - **Problem:** Most products sold as '2230 to 2280 adapters' are SSD length brackets. They let a short SSD sit in a long slot, which is the opposite of what is needed here. The Q6A has a 2230 M-key slot (PCIe Gen3 x2) and the Micro is an 80 mm B+M card, so the card would overhang by about 50 mm.
    - **Correction:** Option 1: plug the card straight into the 2230 socket and hold its 80 mm end with a 3D-printed post and an M2 screw. First check which side of the board the slot is on and what it clears; that was not verified. Option 2: use a short M-key male-to-female flex extender (ADT-Link R44SF 20 cm about $40 on Newegg, generic 5 cm Gen4 flex about $27 + shipping on eBay). Then check that LnkSta reads 8GT/s x1.
    - **Source:** https://docs.radxa.com/en/dragon/q6a/hardware-use/nvme ; https://www.newegg.com/p/2S7-01Z1-00EH8
  4.
    - **Claim:** Research: 'Lime says 12-bit sample depth'; ADCs are in the LA9310.
    - **Problem:** The Crowd Supply and CNX spec lists do not give an ADC bit depth, and the NXP pages I found give 153 Msps but no resolution. In LimeSuiteNG the Micro always uses 16-bit samples on the PCIe link ('mConfig.linkFormat = DataFormat::I16; // always force I16 link').
    - **Correction:** Treat the bit depth as unverified. Because the link is always 16-bit, 2 channels x 61.44 Msps = 492 MB/s, which needs Gen3. At Gen2 x1 (about 400 MB/s usable) only one full-rate channel fits.
    - **Source:** https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LA9310_TRX.cpp ; https://www.cnx-software.com/2026/04/15/limesdr-micro-m-2-2280-sdr-card-pairs-nxp-la9310-baseband-processor-with-lms7002m-rf-transceiver/
  5.
    - **Claim:** Research: up to 160 Msps; sample rates are flexible down to decode rates.
    - **Problem:** Not mentioned in the research: LimeSDR_Micro.cpp sets samplingRateRange = {7e6, 160e6} ('going below 7MHz without decimation introduces noise'). Applications cannot ask for less than 7 Msps.
    - **Correction:** Run the Micro at 7.68 Msps or more and decimate on the host. SatDump does this; the cost is about 31 MB/s and some CPU. For decode recordings use 7.68 Msps in cs8/ZIQ. Meteor/Metop/FY HRPT all fit.
    - **Source:** https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp
  6.
    - **Claim:** Research: the Arm/Qualcomm SMMU is a major unknown for DMA (by analogy with the LiteX M2SDR __pa mmap bug).
    - **Problem:** Overstated. The la9310_limesdr code is SMMU-safe by construction. It allocates with kzalloc + dma_map_single and programs the IOVA into the outbound window. It mmaps through dma_mmap_coherent, which on the IOMMU path uses virt_to_page(cpu_addr), not __pa. The DMA mask is set with dma_set_mask_and_coherent. Radxa's 7.0.11 DTS gives pcie1 an iommu-map to SID 0x1c80 and lists an NVIDIA dGPU and a Chelsio NIC as tested, and kodiak.dtsi marks pcie1 dma-coherent.
    - **Correction:** Keep the SMMU in translation mode. If faults appear, switch only the device's IOMMU group to identity; never use a global arm-smmu.disable. The risk is now low to medium, not high.
    - **Source:** https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/drivers/linux/la9310_limesdr/la9310_character_device.c ; https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts ; https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/boot/dts/qcom/kodiak.dtsi
  7.
    - **Claim:** Fixes: the card's MSI goes through the DesignWare controller's internal MSI (msi0-msi7).
    - **Problem:** kodiak.dtsi pcie1 has 'msi-map = <0x0 &intc 0x0 0x1000>' to the GICv3 (msi-controller). When msi-map is present, the DWC host driver does not use its internal MSI controller, so MSI doorbell writes go through the SMMU (the kernel maps them).
    - **Correction:** No action is needed. When debugging missing interrupts, look at GIC/SMMU MSI mapping, not the DWC iMSI-RX.
    - **Source:** https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/boot/dts/qcom/kodiak.dtsi
  8.
    - **Claim:** No one discusses BAR sizing; the slot is assumed to accept any PCIe device.
    - **Problem:** New finding: la9310_pci.c says 'Default BAR0 size is 256MB, some systems can't map that much'. It assigns BARs at probe time because the ROM bootloader reports PCI class 00. The Q6A pcie1 32-bit window is 0x40300000 + 0x1fd00000 (about 509 MB). The kernel sizes the bridge window at 384 MB with 128 MB alignment, which lands at 0x48000000-0x60000000 and ends exactly at the window limit, so there is no margin.
    - **Correction:** This probably works, since Radxa lists an NVIDIA dGPU as tested on pcie1. Still, verify on first boot: 'sudo lspci -vv -s 0001:01:00.0' must show Region 0 [size=256M] assigned, and dmesg must not show 'Failed to assign BAR resources'. Do not put a PCIe switch or a second device on that link.
    - **Source:** https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/drivers/linux/la9310_limesdr/la9310_pci.c ; https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/boot/dts/qcom/kodiak.dtsi
  9.
    - **Claim:** Research: the Q6A M.2 3.3 V current limit is undocumented and possibly shared.
    - **Problem:** The schematic answers this.
    - **Correction:** Schematic v1.21, sheet 33 (M_KEY) shows a dedicated ETA3521 buck (U20, 1 µH/4 A inductor, R88 91k/R133 20k giving 3.33 V) from VCC_5V_PERI to VCC_3V3_MKEY. The PCIe lanes are on standard M.2 lanes 0-1 (pins 41-49 and 29-37), so an x1 B+M card works. Lime states about 4 W, roughly 1.2 A at 3.3 V, which leaves about 3x margin. VCC_5V_PERI also feeds USB, so keep the 5 V USB loads modest.
    - **Source:** https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf ; https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
  10.
    - **Claim:** Research integration: keep the helix on RX-A and the QO-100 LNB IF on RX-B; S-band 2.2-2.3 GHz is covered and is a reason for the card.
    - **Problem:** This was not updated after the user dropped dishes. Without a dish, S-band (and later X-band) downlinks are not realistically receivable on handheld antennas. QO-100 narrowband needs less than 1 MHz, which the RTL-SDR handles through whatever non-dish downconverter the antenna component picks.
    - **Correction:** The card's real value is now the 56-100 MHz live view, high-rate raw IQ for the NPU classifier, and two simultaneous L-band/IF inputs. None of the decoding goals strictly needs it.
    - **Source:** Project update (dish abandoned); https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
  11.
    - **Claim:** Research budget option: the RTL-SDR V4 alone covers everything except S-band and the wide view.
    - **Problem:** It also cannot do full-rate Metop or FengYun AHRPT, which need about 6 Msps or more; the RTL-SDR tops out at about 2.4-3.2 Msps stable.
    - **Correction:** If you need AHRPT before the Micro is proven, a USB 2.0 Airspy Mini (6 Msps, 24-1700/1800 MHz, about £110 at Moonraker) or Airspy R2 (10 Msps, about £200) is the cheaper path. See the budget option.
    - **Source:** https://moonrakeronline.com/airspy-mini-sdr ; https://www.rtl-sdr.com/review-airspy-mini/
  12.
    - **Claim:** Fixes: the 32-entry RX ring patch plus isolcpus=7 for the RX thread.
    - **Problem:** The ring analysis checks out in code. RxSetup uses SubdivideBuffer(...,16 KB,16), and at 61.44 Msps packetsToBatch is clamped to 8 x 2048 B, giving 16 x 16 KB = 1.07 ms. The firmware MFIFO_SIZE is 32. Two corrections: (a) the SoapySDR plugin does not expose packetsInBatch, so SatDump/SDR++ users need the source patch, not just limeTRX flags; (b) on QCS6490, cpu7 is the single 2.7 GHz prime core, and isolating it takes the fastest core away from SatDump DSP.
    - **Correction:** Pin lime:Rx0 to an A78 2.4 GHz core (cpu4-6) at SCHED_FIFO and leave cpu7 for DSP, or measure both. For the patch, try 24 entries first, then 32, and revert if the VSPA times out.
    - **Source:** https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/boards/LimeSDR_Micro/LA9310_TRX.cpp ; https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/src/chips/LA9310/firmware/dma_tcd_fifo.h ; https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/plugins/soapysdr/Settings.cpp
- **Forum and fix assessment:** The forum findings are accurate. The only small error is a non-existent 'Jul 31' Crowd Supply update.
  
  - **Delivery:** there are still no confirmed deliveries or independent hands-on reports. The Crowd Supply updates page ends at Jun 17, 2026, and MyriadRF Discourse has no delivery topics.
  - **Driver branches:** confirmed with git ls-remote. limesdr-micro-staging head is 37cb1833 (Oct 16, 2026) and limesdr-micro is 80ffad5. The recent commits fix overrun recovery, stream pacing and IRQ init, so this is early-adopter software.
  - **Q6A platform (checked in Radxa's linux-7.0.11 DTS, kodiak.dtsi and schematic v1.21):** pcie1 is domain 1, num-lanes 2, dma-coherent, with an iommu-map to SID 0x1c80. The tested-device list includes an NVIDIA dGPU and a Chelsio NIC. The M.2 slot has its own 4 A ETA3521 3.3 V buck and standard lane-0/1 wiring. USB3 and the 2-lane DP for HDMI sit on separate combo-PHY lanes.
  - **Fixes that hold up:** the DKMS/CMake option names (BUILD_DRIVERS_LA9310, LA9310_LIMESDR_DKMS, BUILD_PLUGINS_SOAPYSDR, INSTALL_FIRMWARE). The firmware files are in-tree and the HIF check is real. The setpci Gen2 force sequence (LnkCtl2 0x30, retrain bit in LnkCtl 0x10) is correct, as are usbfs_memory_mb=0, the Friis numbers (1.2/1.6 dB) and the Y-factor formula. The data-rate and storage arithmetic (221 GB per 15-minute pass at 61.44 Msps; 8 GB RAM ring is about 32 s) is right, and the per-IOMMU-group identity fallback is the right call.
  - **Fixes that need correcting:** (1) MSI goes to the GIC through msi-map, not the DWC internal MSI. (2) isolcpus=7 sacrifices the prime core. (3) The ring-depth patch is required for Soapy users, because packetsInBatch is not exposed through Soapy. (4) The mechanical plan must avoid '2230-to-2280' SSD length brackets, which go the wrong way.
  - **Missed by all three agents:** the LA9310 256 MB BAR0 against the about-509 MB pcie1 window. By calculation it fits exactly, and the dGPU test suggests it works, but it needs checking. Also missed: the 7 Msps minimum sample rate, and the fact that SatDump now has a native LimeSuiteNG source plugin (limesdrng_sdr_support, linking limesuiteng-legacyapi).
  - **Effect on the pick:** none of this overturns it. It does make the driver's SMMU risk lower than the research claimed, and the delivery and stream-stability risks remain the main ones.
- **Final recommendation:**
  - **Name:** LimeSDR Micro M.2 2280 Basic (no GNSS), cancellable pre-order, plus 2x MHF4L-to-SMA(f) bulkhead cables. Mount it directly in the Q6A M-key 2230 socket with a support post at 80 mm, or on a short Gen3/Gen4 M-key flex extender.
  - **Price:** $249 + $18 worldwide shipping = $267. Cables 2 x $6 = $12. Ukrainian import about $30-35 under the current EUR 150 rule (10% duty + 20% VAT on the excess) plus possible courier brokerage. Total about $310-320. Add $27-44 if you use a flex extender.
  - **Why:** It is still the only wideband SDR that is all of these: about $250, sold to the public, PCIe, and the right size for the Q6A.
  
  Why it fits the Q6A:
  - B+M card in the M-key slot, Gen3 x1, about 4 W from a dedicated 4 A 3.3 V buck.
  - 100 MHz / up to 160 Msps half-duplex RX, 2 RF RX ports, 30 MHz-3.8 GHz.
  - The 3.8 GHz ceiling does not matter now that dishes are dropped.
  - The driver's DMA path uses the standard DMA API in an SMMU-safe way. Radxa's device tree shows pcie1 is dma-coherent and tested with dGPU and NIC endpoints.
  
  Why not the alternatives (checked Oct 18, 2026):
  - Out of stock: LiteX M2SDR (EUR 699), HamGeek M2SDR ($376) and HamGeek LibreSDR M2SDR ($299).
  - About twice the price or more: bladeRF xA4 ($540, in stock) and xSDR ($549, A+E key).
  - No usable PCIe-class bandwidth: HackRF Pro (20 Msps).
  - USB3 options depend on unmeasured Q6A USB3 throughput.
  
  Treat it as an early-adopter part:
  - No confirmed deliveries yet; new orders ship Dec 15, 2026.
  - Driver on the limesdr-micro-staging branch.
  - RX DMA ring of only about 1 ms.
  
  Order now, since the order can be cancelled. Build and test the driver on the Q6A before the card arrives, keep the RTL-SDR path as the working baseline, and decide on 31 Jan 2027.
  - **Sources:**
    - https://www.crowdsupply.com/lime-micro/limesdr-micro
    - https://www.crowdsupply.com/lime-micro/limesdr-micro/updates
    - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
    - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro-staging
    - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro-staging/drivers/linux/la9310_limesdr/la9310_base.c
    - https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
    - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
    - https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
    - https://www.crowdsupply.com/guide/fulfillment-and-logistics
    - https://github.com/enjoy-digital/litex_m2sdr
    - https://www.nuand.com/product/bladerf-xa4/
    - https://www.crowdsupply.com/wavelet-lab/xsdr
- **Final budget option:**
  - **Name:** Defer the wideband card: RTL-SDR V4/V4L only. If you need full-rate Metop or FengYun AHRPT before the Micro is proven, add an Airspy Mini on a USB 2.0 port.
  - **Price:** $0 extra. With the Airspy Mini, about £110 at Moonraker UK (about $140; launch price was $99). An Airspy R2 (10 Msps) is about £200. The Micro can be added later for about $310 landed.
  - **Why:** With dishes dropped, every decoding goal fits in 10 MHz or less:
  - LRPT, SSTV and CubeSats need under 0.2 MHz.
  - QO-100 narrowband through the IF needs under 1 MHz.
  - Meteor HRPT needs about 3 Msps.
  - Metop and FY-3 AHRPT need about 6 Msps.
  
  The RTL-SDR handles all of these except AHRPT. The Airspy Mini (12-bit, 6 Msps, up to about 1.7-1.8 GHz) covers AHRPT on a USB 2.0 port, where throughput is not a concern. SatDump supports both natively.
  
  You give up the 56-100 MHz live view, wideband IQ for the NPU classifier, and S-band, which is not realistic without a dish anyway. No wideband PCIe or USB3 SDR cheaper than the Micro Basic was in stock on Oct 18, 2026: the LibreSDR M2SDR ($299) and HamGeek M2SDR ($376) were sold out, and the bladeRF xA4 costs $540.
- **Known problems and fixes to apply:**
  - Ordering: buy the Micro Basic ($249 + $18), skip GNSS ($299), and add 2 MHF4L-SMA(f) cables ($6 each). It is a store pre-order (ships Dec 15, 2026), cancellable for a full refund before shipment. Budget about $30-35 Ukrainian duty+VAT under the current EUR 150 rule, which becomes VAT-from-first-euro once bill 16051-1 takes effect. Set a decision gate of 31 Jan 2027.
  - Mechanics: do NOT buy a '2230-to-2280 SSD adapter' bracket, which goes the wrong way. Either insert the card directly and support its 80 mm end with a printed post and M2 screw (check the slot side and clearance first), or use a short M-key male-to-female flex (ADT-Link R44SF 20 cm about $40, generic 5 cm about $27). The card is up to about 4 mm tall on top; use mixed-thickness thermal pads under an aluminium heatsink in the fan's airflow.
  - Slot pre-test: before the SDR arrives, run a cheap 2280 NVMe in the same mount or extender. Then run 'lspci -vv -s 0001:01:00.0' (expect LnkSta 8GT/s x1 for the Micro) and a 15-minute fio read. One Q6A slot died on the forum, and cleaning the slot fixed another board.
  - PCIe link errors: read and clear 'setpci -s 0001:01:00.0 CAP_EXP+0a.w'. If correctable errors appear, force Gen2 with 'setpci -s 0001:00:00.0 CAP_EXP+30.w=0002:000f' followed by 'CAP_EXP+10.w=0020:0020'. Make it persistent with a DT overlay '&pcie1 { max-link-speed = <2>; };'. At Gen2, use only 1 RX channel at 61.44 Msps, because the link is always I16.
  - BAR check (new): LA9310 BAR0 is 256 MB and the Q6A pcie1 window is about 509 MB, so it fits with no margin. On first boot, confirm 'Region 0 ... [size=256M]' in lspci and no 'Failed to assign BAR resources' in dmesg. Do not add a PCIe switch.
  - Driver build on the Q6A now (aarch64): install linux-headers for the running kernel plus dkms. Clone LimeSuiteNG -b limesdr-micro-staging and pin a commit (37cb1833 as of Oct 16). Configure with -DBUILD_DRIVERS_LA9310=ON -DLA9310_LIMESDR_DKMS=ON -DBUILD_PLUGINS_SOAPYSDR=ON -DBUILD_GUI=OFF. Take driver, library and firmware from the same commit, because of the HIF version check. Load la9310_limesdr at boot, since it kzallocs 4 MiB (order-10) DMA buffers. Run 'apt-mark hold' on the kernel and header packages. Rebuild DKMS before any kernel change, and remove stale DKMS builds if you see 'Exec format error' or 'disagrees about version of symbol'.
  - SMMU: keep translation on. If you see 'Unhandled context fault … cbfrsynra=0x1c80', unbind the driver, set /sys/kernel/iommu_groups/<G>/type=identity, then rebind. Use iommu.passthrough=1 only from a spare boot entry, and check that the NPU (FastRPC), HDMI and UFS still work. Never use arm-smmu.disable=1.
  - Sample loss (about 1.07 ms hardware ring): set the performance governor and preempt=full. After the app starts, set the lime:Rx0 thread to 'chrt -f 70' and pin it to cpu4-6. Optionally patch SubdivideBuffer(...,16) to 24, then 32 (firmware MFIFO_SIZE is 32), and set packetsToBatch=dmaBatchSize/packetSize; this is required for Soapy users. Verify with 'limeTRX -l info' that 15-minute runs show 0 loss deltas.
  - Minimum 7 Msps: the Micro will not stream below 7 Msps. Use 7.68 Msps and host decimation, and record decode captures as cs8/ZIQ (about 28 GB per 15-minute pass in cs16, half that in cs8). Keep 61.44 Msps for a tmpfs RAM ring (8 GB is about 32 s) and write snapshots on a trigger.
  - Software: build SatDump after LimeSuiteNG. It has a native 'limesdrng_sdr_support' plugin that links limesuiteng-legacyapi. Use SoapySDR (LimeSuiteNG plugin) for SDR++ and GNU Radio, or gr-limesuiteng. At high rates, record first and decode offline, because XTRX users saw garbled CADUs when decoding live.
  - Thermal and power: budget 5 W at the 12 V input (Lime says about 4 W) and design cooling for 10 W, per Lime. Log the TMP1075 'Board Temperature' and lms7_temp. XTRX boards with the same RFIC hit 80 °C without airflow. Optionally fit an INA226 shunt in the 12 V feed; it doubles as battery telemetry for the UI.
  - RF: the card has no bias tee, so use an external SMA bias tee for the L-band LNA. Keep VHF (137/145 MHz) on the RTL-SDR, because the Micro's RX matching starts at 300 MHz. Put the LNA (≤1 dB NF, ≥18 dB gain) at the antenna. Keep inputs below +10 dBm. Set the RX analog LPF to match the sample rate to avoid images. Shield the card from the SBC and the HDMI display to reduce spurs.
  - Storage: if the Kioxia 256 GB UFS is used, run only on a Radxa kernel with the PA_TACTIVATE quirk. Prove that 250 MB/s sustained UFS writes run alongside PCIe DMA with fio before relying on full-rate captures.
  - PPS/GNSS: use the separate u-blox M10 or ATGM336H for the pointing UI and gpsd. Feed its PPS to the Micro's MHF4 PPS input only after the documented resistor change (remove R176, fit R179 on v1.1/v1.2 boards).
- **Remaining uncertainties:**
  - Whether any LimeSDR Micro units have shipped yet, and whether the Dec 15, 2026 date holds. No backer or independent reports existed as of Oct 18, 2026.
  - Whether la9310_limesdr builds and loads on Radxa's 7.0.x qcom kernel; the source has version guards up to 6.16. Also whether multi-channel and 61.44 Msps streaming are stable on aarch64; Lime has validated on x86 only.
  - Whether the 256 MB BAR0 is actually assigned in the Q6A's 509 MB pcie1 window. It fits exactly by calculation and a dGPU is listed as tested, but this is untested with the Micro.
  - Whether the 32-entry RX ring patch works with the VSPA firmware, and what worst-case scheduling latency the Q6A shows under UFS and GPU load.
  - Which side of the Q6A the M.2 slot is on, and whether a direct-plugged 80 mm card clears the other components; I did not verify the board drawing. Extender signal integrity at Gen3 is also unverified.
  - The ADC bit depth (12-bit is claimed but not documented on Crowd Supply or NXP pages I found), the noise figure and return loss per port, and idle or RX-only power.
  - The effective date of Ukraine's repeal of the EUR 150 parcel exemption, and which carrier and brokerage fees apply to Crowd Supply's $18 worldwide shipping.
  - Sustained Q6A USB 3.1 throughput, which decides whether the bladeRF xA4 or RFNM USB3 options are viable fallbacks. It is still unmeasured.
  - Current Airspy Mini/R2 retail prices in USD and EUR (only undated UK listings found), and RFNM's 2026 availability.
- **Missed better options:**
  - HamGeek LibreSDR M2SDR (SKU 100912; AD9361 + XC7A200T, M.2): $299, cheaper than the $376 HamGeek board the research listed. Sold out on hgeek.com (Shopify availability=false, Oct 18, 2026) with no community track record, so it is not better today.
  - Airspy Mini or R2 (USB 2.0): about £110 or £200. This was missed as a budget path for full-rate Metop and FY AHRPT, which the RTL-SDR-only budget option cannot do. It is not a wideband replacement.
  - RFNM (also LA9310-based; USB3; 12-bit, 122 MHz on one cable, 160+ MHz on two): pre-order prices were a $299 motherboard plus a $179 Lime daughterboard. 2026 availability is unverified and it depends on the Q6A's unproven USB3 throughput, so it is not better.
  - Wavelet xSDR (2230, 122.88 Msps, 4 RF ports, ships Oct 30, 2026): Wavelet sells a $12 M.2 B+M-key adapter for the uSDR that might fit the xSDR into the Q6A slot without overhang, but that is unverified. At $549 and with no Arm reports it is not better value.
  - None of these is strictly better or cheaper and also available. The Micro Basic remains the pick.
- **Confidence:** medium

_Агент цього етапу ще працює (run `wf_e64436d6-ae7`)._

