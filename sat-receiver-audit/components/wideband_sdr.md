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

_Агент цього етапу ще працює (run `wf_e64436d6-ae7`)._

