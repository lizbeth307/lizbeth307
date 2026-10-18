# Compute: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_88090a59-878`_

- **Component:** Compute board (NPU): Radxa Dragon Q6A (Qualcomm QCS6490) vs. alternatives, October 2026
- **Current pick assessment:** VERDICT: KEEP THE DRAGON Q6A. It is still the best value among palm-sized boards that have a usable Linux NPU and a PCIe Gen3 M.2 slot free for the SDR. The planned price and RAM size are out of date, though.
  
  HARDWARE (Radxa product brief rev 1.7, 2026-10-10):
  - Size is 85 x 56 mm. The plan says 85x65 mm, which is wrong.
  - CPU: 1x Kryo Prime 2.7 GHz + 3x Gold 2.4 GHz + 4x Silver 1.9 GHz.
  - Adreno 643 GPU (Vulkan 1.3, OpenCL 2.0). Hexagon DSP with HVX and the Tensor Accelerator, 12 TOPS.
  - LPDDR5-5500 in 4, 6, 8, 12 or 16 GB.
  - M.2 M-key 2230 slot, PCIe Gen3 x2. Radxa measured an NVMe drive at 1649 MB/s read and 1467 MB/s write, so Gen3 x2 really works under Linux. The Android 15 RC limits this slot to Gen2.
  - USB: 1x USB 3.1 OTG Type-A and 3x USB 2.0.
  - Display: HDMI 2.0 (4K30) and a 4-lane MIPI DSI connector. Three CSI camera connectors.
  - Power: 12 V only. Input is through USB-C PD (the PD source must offer a 12 V profile) or the 12 V header. Radxa asks for at least 18 W, and 24 W (12 V/2 A) when the USB 3.1 port and PCIe slot are fully loaded.
  
  STORAGE: Radxa measured its UFS modules with dd:
  - Samsung UFS 3.1 128 GB: 1703 MB/s read, 388 MB/s write.
  - Kioxia 256 GB: 1811 MB/s read, 557 MB/s write.
  So a 256 GB Radxa UFS module meets the 250 MB/s target. Radxa warns against using untested UFS modules.
  
  CPU CLOCKS AND THERMALS: I found no published cpufreq log from Linux. SBCwiki measured Geekbench 6 at 1170 single-core and 3105 multi-core, which is in line with other QCS6490/QCM6490 boards. That suggests the CPU is not capped, but I am inferring this.
  - Peak power under Linux was 10.17 W, including a fan of about 1.5-2 W. CPU-only load was about 6 W.
  - Under Windows the chip reached 94°C. The hardware throttle point is 95°C (105°C for the 300-AA part), per Qualcomm's thermal documentation.
  - Radxa did not sell an official cooler (as of the January 2026 review). A heatsink plus fan is mandatory.
  
  LINUX SUPPORT: Radxa OS r2 is a GNOME desktop built on Ubuntu 24.04 'noble'. It needs BIOS 20251230 or newer, and the NPU runtime comes preinstalled. Armbian runs mainline kernel 6.18.
  
  NPU FROM LINUX: Usable, but rough.
  - Radxa documents fastrpc/libcdsprpc1 and a `fastrpc_test -a v68` self-test, plus QAIRT, the QNN ONNX Runtime execution provider, the TFLite/LiteRT delegate, QAI AppBuilder and AIMET.
  - A community user (June 2026) runs YOLOv8n in about 10 ms with QAIRT 2.46.
  - Forum threads from April to August 2026 report broken Python 3.12 onnxruntime-qnn wheels. Staff said in May that a wheel had been built. Users also report FastRPC session failures (0x80000600) that have no official fix, and mismatches between the QAIRT version and AI Hub artifacts.
  
  PRICE AND AVAILABILITY (October 2026): The $124 16 GB launch price no longer exists.
  - Arace (checked 18 Oct 2026) lists the 4/6/8/12 GB versions at $95/115/139/169, all sold out. Its 16 GB entry ($119.50) is also sold out and looks stale.
  - Allnet China has the 6 GB ($149.99) and 12 GB ($189.99) in stock. The 8 GB ($159.99) is out of stock, and there is no 16 GB listing.
  - Ameridroid (6 GB $169.95, 12 GB $249.95) is out of stock.
  - Prom.ua has no listings, so the board must be imported. I could not check the current AliExpress price because the page would not load.
  - Price rises across the market are driven by DRAM costs; CNX documents +44% to +233% on SBCs since launch.
  
  Every alternative I checked costs more, misses the Gen3 M.2 requirement, draws far more power, or is not palm-sized.
- **Alternatives:**
  1.
    - **Name:** Thundercomm RUBIK Pi 3 (same QCS6490)
    - **Key specs:** QCS6490, 12 TOPS. 8 GB LPDDR4x and 128 GB UFS 2.2 onboard. M.2 M-key 2280, PCIe 3.0 x2. 1x USB-C 3.1 Gen1 with DisplayPort output, 2x USB 3.0 Type-A, 1x USB 2.0. HDMI 1.4. Power is 12 V/3 A over USB-C PD. Size 100x75x25 mm. OS: Qualcomm Linux, Debian 13 and Android 13. Ubuntu 24.04 can be flashed with Qualcomm Launcher, but the spec table still marks it 'Planning'.
    - **Price:** $299 direct from Thundercomm (Oct 2026; 8 units in stock). The listing says the price was raised because of memory costs. The $99 Programmer's Day promo (Oct 2025) has ended and that SKU is 'Restocking'. Launch price was $179. Not listed on Prom.ua.
    - **Pros:** Same SoC, NPU and QAIRT stack as the Q6A, so no software risk is added. The 2280 slot takes the LimeSDR Micro M.2 2280 directly, with no 2230-to-2280 extension. It has more USB 3 ports, plus USB-C with DisplayPort output for a one-cable portable display. Storage is soldered on, so no separate module is needed.
    - **Cons:** About 1.6x the Q6A 12 GB price, with only 8 GB of slower LPDDR4x. The board is larger. Onboard UFS 2.2 write speed is unpublished, so it may not reach 250 MB/s. Ubuntu support is described inconsistently by Thundercomm. The EU distributors (Codico, ATEstore, Consult Red) target B2B buyers.
    - **Availability:** In stock at Thundercomm direct at $299 (low quantity). Sold through Arrow (US) and Codico/ATEstore/Consult Red (EU). Not stocked in Ukrainian shops.
    - **Q6a compatibility:** Drop-in in software terms: same SoC, same Hexagon v68 NPU and the same QAIRT models. The mechanical design changes: the board is 100x75 mm and the M.2 slot takes a 2280 card.
    - **Sources:**
      - https://www.thundercomm.com/product/rubik-pi/
      - https://www.thundercomm.com/rubik-pi-3/en/docs/about-rubikpi
      - https://www.cnx-software.com/2025/01/09/qualcomm-qcs6490-rubik-pi-3-ai-sbc-supports-android-linux-and-lu-operating-systems/
      - https://www.thundercomm.com/rubik-pi-3-99/
      - https://prom.ua/ua/search?search_term=rubik%20pi%203
  2.
    - **Name:** Radxa Dragon Q8B (Snapdragon 8cx Gen 3 / SC8280XP)
    - **Key specs:** 4x Cortex-X1 at 3.0 GHz + 4x A78 at 2.4 GHz, Adreno 690, NPU 29+ TOPS. Up to 32 GB LPDDR4X. Two M.2 M-key 2280 slots, one PCIe Gen3 x4 and one Gen3 x2, plus an M.2 E-key slot and a PCIe Gen3 x1 FFC. 2x USB 3.2 Gen2 Type-C with DisplayPort and 2x USB 3.2 Gen2 Type-A. HDMI 2.1. UFS 3.1 connector. 2x 2.5GbE. Power is 12 V or 20 V USB-PD (switch-selected). Size 100x75 mm. Radxa's FastRPC test uses the same v68 flag as the Q6A.
    - **Price:** Pre-order at Arace: 4 GB $149, 8 GB $209, 16 GB $329, 32 GB $569, estimated to ship 15 Nov 2026. Allnet China has the 8 GB in stock at $289.99 (16 and 32 GB out of stock). Heatsink $3.90.
    - **Pros:** The strongest choice from the Radxa/Qualcomm family. One slot holds the PCIe SDR and the other an NVMe drive for raw IQ (over 1.4 GB/s), so 160 Msps bursts can be recorded continuously and the UFS module becomes unnecessary. Ten-gigabit USB ports. Much faster CPU for SatDump HRPT decoding and 56 MHz FFT. The NPU is 2.4x the Q6A's. The chip has mainline Linux support (the same SoC as the ThinkPad X13s).
    - **Cons:** Power: bret.dk measured 5.9 W idle, 25.1 W under load and 27.9 W running Ollama. On a 72 Wh pack that gives only about 2-3 hours under load. A Linpack run made the PMICs overheat and shut down. The software was immature in May 2026: the Ethernet ports and the UFS slot did not work on the early builds, and the reviewer called Linux support 'patchy and hacky' in places. NPU use from Linux has not been reviewed. It is larger and costs more than the Q6A.
    - **Availability:** Pre-order at Arace (ships about 15 Nov 2026). 8 GB in stock at Allnet China.
    - **Q6a compatibility:** Same Radxa OS and Qualcomm toolchain family, so QAIRT models should port. Needs a larger case and cooler, and a 12 V or 20 V PD supply rated over 30 W.
    - **Sources:**
      - https://bret.dk/?p=7574
      - https://www.cnx-software.com/2026/06/01/radxas-2026-qualcomm-hardware-dragon-q8b-and-q5e-sbcs-dragonstation-and-dragonbay-nas-systems/
      - https://arace.tech/products/radxa-dragon-q8b
      - https://shop.allnetchina.cn/products/radxa-dragon-q8b
      - https://docs.radxa.com/en/dragon/q6a/app-dev/npu-dev/fastrpc-setup
  3.
    - **Name:** Orange Pi 5 Max (Rockchip RK3588)
    - **Key specs:** RK3588: 4x A76 at 2.4 GHz + 4x A55 at 1.8 GHz, Mali-G610. NPU 6 TOPS (RKNN). 4, 8 or 16 GB LPDDR5. M.2 M-key, PCIe 3.0 x4. 2x USB 3.0 and 2x USB 2.0. 2x HDMI 2.1 and MIPI DSI. Power is 5 V/5 A over USB-C. Size 89x57 mm.
    - **Price:** Launch price was $125 for 16 GB (AliExpress, 2024). Oct 2026: Prom.ua seller RADIOMAG lists the 16 GB at 21,490.95 UAH, in stock. That is about $510-525 at an assumed 41-42 UAH/USD. AliExpress snapshots show about $300-600 for 16 GB (not verified). CNX reports the sister Orange Pi 5 Ultra 16 GB at $309 (April 2026).
    - **Pros:** Its NPU toolchain (RKNN-Toolkit2) is the most mature and best documented in hobby use. The M.2 slot is x4 Gen3, more headroom than the SDR needs. Same footprint class as the Q6A. It can be bought inside Ukraine. Large community and Armbian support.
    - **Cons:** Half the NPU TOPS of the Q6A. It now costs 1.6-2.7x the Q6A 12 GB. The 5 V/5 A input needs a 25 W 5 V buck regulator. Its CPU is not meaningfully faster than the QCS6490.
    - **Availability:** In stock in Ukraine (Prom.ua) at about 21.5k UAH. Elsewhere availability is patchy and prices are inflated.
    - **Q6a compatibility:** Different NPU stack: models must be converted to RKNN instead of QAIRT. Linux SDR software (SatDump, SDR++, GNU Radio) runs the same. Feed it 5 V instead of 12 V.
    - **Sources:**
      - https://liliputing.com/orange-pi-5-max-is-a-credit-card-sized-rk3588-pc-with-2-5-gbe-ethernet-pcie-3-0-and-wifi-6e/
      - https://prom.ua/ua/search?search_term=orange%20pi%205%20max
      - https://www.cnx-software.com/2026/04/28/what-a-difference-two-years-make-comparing-sbc-prices-in-2024-and-2026/
  4.
    - **Name:** Radxa ROCK 5T / ROCK 5B+ (Rockchip RK3588)
    - **Key specs:** RK3588 with a 6 TOPS NPU. Radxa's interface document for the ROCK 5T shows an M.2 M-key on PCIe 3.0 (signals labelled PCIE30X4) and a second M.2 B-key on PCIe 3.0 x2. Both boards have two M.2 slots, so the SDR and an NVMe drive can both fit. Board sizes were not re-verified this session; both are larger than the Q6A.
    - **Price:** ROCK 5T 8 GB: $259.99 in stock at Allnet China (other variants are placeholders or out of stock). ROCK 5B+ 8 GB: $239.99 at Allnet (out of stock). Arace lists both, all sold out.
    - **Pros:** Two PCIe Gen3 M.2 slots, so the SDR and NVMe recording can run together. Mature RK3588 Linux and RKNN support.
    - **Cons:** Costs $70+ more than the Q6A 12 GB with less RAM and a weaker NPU. Larger board. Mostly sold out.
    - **Availability:** ROCK 5T 8 GB in stock at Allnet China. Everything else sold out at Arace.
    - **Q6a compatibility:** Requires an RKNN port of the model and a 5 V or PD power design. The SDR M.2 card fits natively.
    - **Sources:**
      - https://docs.radxa.com/en/rock5/rock5t/hardware-design/hardware-interface
      - https://shop.allnetchina.cn/products/rock-5t
      - https://arace.tech/products/radxa-rock-5t
      - https://shop.allnetchina.cn/products/rock5-model-b-1
  5.
    - **Name:** NVIDIA Jetson Orin Nano Super Developer Kit
    - **Key specs:** 6x Cortex-A78AE, Ampere GPU, 8 GB RAM. 7-25 W. The carrier has two M.2 M-key slots (PCIe Gen3 x4 and x2) and an M.2 E-key; these details are from my prior knowledge and were not re-verified. JetPack (Ubuntu 22.04 based).
    - **Price:** $399. NVIDIA raised it from $249 in July 2026. SparkFun, Newegg and Amazon list $399. Resellers ask $529-599.
    - **Pros:** CUDA can accelerate the SDR DSP (FFT, channelizers), and the AI software stack is the most mature. Two M.2 slots allow SDR plus NVMe.
    - **Cons:** Twice the Q6A price. Sold out on NVIDIA's marketplace. Higher power. Larger than palm-sized (roughly 100x80 mm and taller with the heatsink). Only 8 GB RAM. Weaker single-thread CPU than the Q6A's 2.7 GHz A78.
    - **Availability:** Sold out at NVIDIA US. Limited retail stock at $399.
    - **Q6a compatibility:** A completely different stack (CUDA/TensorRT). Needs a full redesign of power, case and thermals.
    - **Sources:**
      - https://hwbusters.com/news/nvidia-jetson-prices-jump-up-to-101-the-249-orin-nano-super-is-now-399/
      - https://www.sparkfun.com/nvidia-jetson-orin-nano-developer-kit.html
  6.
    - **Name:** Particle Tachyon (QCM6490, 5G)
    - **Key specs:** QCM6490 with the same clocks as the Q6A (1x 2.7, 3x 2.4, 4x 1.9 GHz), 12 TOPS. 4 or 8 GB RAM, 64 or 128 GB UFS. A PCIe 3.0 expansion connector instead of an M.2 slot; the datasheet gives the width as both x1 and 2-lane. USB-C 3.1 with PD and DisplayPort. 4-lane DSI. Accepts a 1-cell 3.7 V LiPo directly. 85x56 mm.
    - **Price:** 8 GB/128 GB $529, 4 GB/64 GB $399; with a 9300 mAh battery $554/$424 (Particle store, Oct 2026).
    - **Pros:** Built-in LiPo input and charging could replace the BMS, the USB-C charging board and the PD source. Same footprint and NPU stack as the Q6A.
    - **Cons:** Nearly 3x the price. An adapter from the FFC connector to M.2 would be needed for the SDR. Single-cell power would complicate the 13 V LNB rail. The 5G modem is unnecessary for this build.
    - **Availability:** In stock at the Particle store, shipping worldwide.
    - **Q6a compatibility:** Same SoC family and QAIRT stack. Different PCIe connector and power architecture.
    - **Sources:**
      - https://docs.particle.io/reference/datasheets/tachyon/tachyon-datasheet/
      - https://store.particle.io/products/tachyon-5g-single-board-computer
  7.
    - **Name:** Arduino VENTUNO Q (Qualcomm Dragonwing IQ-8275)
    - **Key specs:** IQ-8275 with an NPU of 40 dense TOPS, plus an STM32H5 microcontroller. 16 GB LPDDR5, 64 GB eMMC. M.2 socket for Gen4 NVMe. Power input 5 V USB-C or 12-24 V DC. Size 160x100x25.8 mm. Runs Ubuntu and Debian.
    - **Price:** $299 introductory price, limited to 2 per order, about 4 weeks lead time. The IQ-8275 EVK is $749 at DigiKey.
    - **Pros:** Newest Qualcomm NPU (more than 3x the Q6A). Accepts 12-24 V input, so it could run almost directly from the 4S pack. The microcontroller could handle the IMU and GNSS.
    - **Cons:** 160x100 mm is not palm-sized and needs a large heatsink and fan. Costs about $110 more than the Q6A 12 GB.
    - **Availability:** Pre-orders through Newark and Mouser (Aug-Oct 2026).
    - **Q6a compatibility:** Same QAIRT family. The mechanical design is incompatible with a palm-sized handheld.
    - **Sources:**
      - https://www.cnx-software.com/2026/08/25/299-arduino-ventuno-q-sbc-combines-qualcomm-dragonwing-iq8-soc-and-stm32h5-mcu/
      - https://www.digikey.com/en/products/detail/qualcomm/EVK-IQ8275-STARTER-1-0/29479998
  8.
    - **Name:** Raspberry Pi 5 + AI HAT+ 2 (Hailo-10H)
    - **Key specs:** Hailo-10H accelerator, 40 TOPS (INT4), 8 GB onboard RAM. It plugs into the Pi 5's single PCIe lane.
    - **Price:** AI HAT+ 2 costs $200. Pi 5 8 GB MSRP is $175 (April 2026). Total about $375.
    - **Pros:** Large ecosystem and a strong vision accelerator.
    - **Cons:** Fails the hard constraint: the Pi 5 and CM5 have only one PCIe Gen2 x1 lane, so the HAT and the PCIe SDR cannot both be used without a PCIe switch. Also expensive.
    - **Availability:** Generally available.
    - **Q6a compatibility:** Not compatible with the PCIe-SDR architecture.
    - **Sources:**
      - https://www.raspberrypi.com/products/ai-hat-plus-2/
      - https://www.cnx-software.com/2026/04/28/what-a-difference-two-years-make-comparing-sbc-prices-in-2024-and-2026/
  9.
    - **Name:** Boards that fail the PCIe Gen3 requirement: Radxa ROCK 5C (RK3588S2), ROCK 4D (RK3576), NIO 5A (Genio 520), Dragon Q5E (QCS6690)
    - **Key specs:** ROCK 5C: PCIe 2.1 through an FPC connector only. NIO 5A: Genio 520 with a 10 TOPS NPU and a 16-pin PCIe Gen2 x1 FFC, 85x56 mm. Dragon Q5E: QCS6690 (6 TOPS), 65x56 mm, with no M.2 slot and no PCIe exposed. ROCK 4D (RK3576): stated from prior knowledge, not re-verified; it has PCIe 2.1 only.
    - **Price:** ROCK 5C 8 GB $159-270 (both listings out of stock). ROCK 4D 6 GB $98.99 at Allnet. NIO 5A and Q5E have no announced price.
    - **Pros:** Smaller and cheaper NPU boards.
    - **Cons:** No PCIe Gen3 x1 M.2 slot for the LimeSDR Micro, which is a hard-constraint failure.
    - **Availability:** Mostly sold out, or not yet released (NIO 5A, Q5E).
    - **Q6a compatibility:** Not suitable.
    - **Sources:**
      - https://radxa.com/blog/ROCK-5C-Official-Announcement
      - https://www.cnx-software.com/2025/05/20/radxa-nio-5a-credit-card-sized-mediatek-genio-520-sbc-showcased-at-computex-2025/
      - https://www.cnx-software.com/2026/06/01/radxas-2026-qualcomm-hardware-dragon-q8b-and-q5e-sbcs-dragonstation-and-dragonbay-nas-systems/
      - https://shop.allnetchina.cn/products/rock-4d
- **Recommended:**
  - **Name:** Keep the Radxa Dragon Q6A, but buy the 12 GB version (16 GB if you can find it), with a Radxa 256 GB UFS module, and run Radxa OS r2
  - **Why:** No board checked in October 2026 beats it on the combination of price, size (85x56 mm), power (about 6-10 W measured) and NPU (12 TOPS) while keeping a PCIe Gen3 M.2 slot free.
  
  The nearest alternatives are worse buys:
  - RUBIK Pi 3: same chip, now $299.
  - Dragon Q8B: faster, two M.2 slots, but 25 W under load and immature software.
  - RK3588 boards: half the NPU TOPS, $240-520.
  - Jetson Orin Nano Super: $399 and out of stock.
  
  Why 12 GB instead of 6-8 GB: RAM is the burst buffer. 160 Msps at 16-bit IQ is 640 MB/s, more than the UFS write speed (557 MB/s max), so a capture has to land in RAM. About 10 GB free holds roughly 15 seconds of capture.
  
  The 256 GB Kioxia UFS module (557 MB/s write) is the one that clears the 250 MB/s target. The 128 GB module writes only 388 MB/s.
  
  Radxa OS r2 has the NPU runtime preinstalled. Check the NPU with `fastrpc_test -a v68`, then deploy the CNN through QAIRT (ONNX to QNN with INT8 quantization) or the LiteRT QNN delegate.
  - **Price:** 12 GB: $189.99 at Allnet China (in stock, 18 Oct 2026). Arace lists it at $169 but sold out. Ameridroid lists $249.95, also sold out. Budget about $190-200 plus shipping and Ukrainian import VAT. The $124 16 GB launch price is not available anywhere I could check.
  - **Sources:**
    - https://dl.radxa.com/q6a/docs/radxa_dragon_q6a_product_brief.pdf
    - https://shop.allnetchina.cn/products/radxa-dragon-q6a
    - https://arace.tech/products/radxa-dragon-q6a
    - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
    - https://docs.radxa.com/en/dragon/q6a/hardware-use/nvme
    - https://docs.radxa.com/en/dragon/q6a/app-dev/npu-dev/fastrpc-setup
    - https://sbcwiki.com/news/articles/radxa-dragon-q6a-full-review/
- **Budget option:**
  - **Name:** Radxa Dragon Q6A 8 GB (or the 6 GB, which is in stock now)
  - **Why:** It is the same board, NPU and software as the main pick, so nothing in the design changes. 8 GB is enough for SDR++, SatDump and a small CNN together. The trade-off is shorter 160 Msps captures held in RAM, about 8-10 seconds instead of 15.
  
  No cheaper board with an NPU and a PCIe Gen3 M.2 slot exists in October 2026. RK3576/RK3588S boards and the Genio 520 have only PCIe 2.x, and the $99 RUBIK Pi promo has ended.
  
  Note: Allnet's 6 GB listing says Wi-Fi 5 rather than Wi-Fi 6.
  - **Price:** 8 GB: $139 at Arace (sold out; wait for restock) or $159.99 at Allnet (out of stock). 6 GB: $149.99 at Allnet (in stock) or $115 at Arace (sold out). At Allnet the 12 GB costs only $40 more than the 6 GB, so the 12 GB is usually the better buy.
- **Risks:**
  - Price and stock swing with the DRAM shortage. Every Q6A variant was sold out at Arace on 18 Oct 2026, and Ameridroid, Amazon and Newegg are also out of stock. Allnet China has only the 6 GB and 12 GB. Buy as soon as an acceptable listing appears. I could not check the current AliExpress price because the page would not load.
  - Getting the NPU working takes effort. Forum threads from April to August 2026 report FastRPC session failures (0x80000600) with no official fix, Python 3.12 onnxruntime-qnn wheel problems, and mismatches between QAIRT versions and AI Hub artifacts. Mitigation: use only the official Radxa OS r2 image, pin one QAIRT version (2.46 is reported working), and keep a CPU fallback with ONNX Runtime or LiteRT XNNPACK. A small 1D CNN for modulation classification runs comfortably on the A78 cores anyway.
  - Thermals: the hardware throttle point is 95°C, and SBCwiki saw 94°C under heavy load. Radxa sold no official cooler (as of the January 2026 review). A sealed handheld case needs a heatsink with a fan and vents.
  - Power is 12 V only. Common 5 V/9 V USB-C power banks or PD triggers will not start the board. Supply at least 24 W at 12 V with the SDR and USB 3 loaded.
  - Fitting the 2280 SDR card in the 2230 slot: Gen3 signal integrity through a riser is not guaranteed, and a 2280 card may cover the area next to the SoC where the heatsink sits. Check the layout on the board itself before buying a rigid extender.
  - LimeSDR Micro on ARM64/Qualcomm PCIe is unverified. Its Crowd Supply page names no host OS or CPU-architecture requirements, and new M.2 orders now ship 15 Dec 2026 at $249. Test the driver (LimeSuiteNG kernel module) on the Q6A early.
  - Not sold in Ukrainian shops (no Prom.ua listings), so add import VAT and shipping time. Warranty claims mean shipping the board back to China or Hong Kong.
  - Research gap: my web-search budget ran out mid-task. I did not verify ROCK 5T/5B+ board sizes, Jetson carrier details, or Orange Pi AIpro (Ascend 310B) pricing. Their entries are marked where they rely on prior knowledge.
- **Integration notes:**
  - Power: feed the Q6A through its 12 V external power header from a 4S-to-12 V buck converter rated 3 A or more, instead of a USB-C PD source board. Do not connect the raw 12.0-16.8 V pack, because the header's tolerance is not published. Give the 13 V/18 V LNB its own buck-boost converter.
  - Size correction: the Q6A is 85 x 56 mm (Radxa drawing), not 85x65. Mounting holes are 3.5 mm in diameter at 58 x 49 mm spacing. Plan the case from Radxa's drawing.
  - M.2 slot: 2230 M-key, PCIe Gen3 x2, about 1.6 GB/s measured with NVMe. The LimeSDR Micro needs only Gen3 x1. Use a short Gen3-rated flexible riser so the SDR sits away from the SoC and RAM, which also cuts digital noise in the SDR. The Android 15 RC limits this slot to Gen2, so use Linux.
  - Storage: use the Radxa 256 GB Kioxia UFS module (557 MB/s write). Skip the 128 GB Samsung module (388 MB/s write) for IQ recording. Radxa warns that untested third-party UFS or eMMC modules can short the board.
  - Bursts above the UFS write speed (160 Msps x 4 bytes = 640 MB/s) need a RAM ring buffer. This is the main reason to choose 12-16 GB.
  - OS: Radxa OS r2 (GNOME, Ubuntu 24.04 'noble' base) needs BIOS 20251230 or newer (package flat_build_260120). Choose the 4096 image when booting from UFS. Install SatDump, SDR++, GNU Radio and gr-satellites from source or packages for arm64.
  - NPU workflow: run `sudo apt install fastrpc libcdsprpc1 fastrpc-test` and then `fastrpc_test -a v68`. Then use QAIRT with the QNN HTP backend and an INT8 context binary, or onnxruntime-qnn, or the LiteRT QNN delegate.
  - Peripherals: connect the GNSS UART and the BNO085 over I2C/UART on the 3.3 V 40-pin header (several UART and I2C ports available), so no USB adapters are needed. The RTL-SDR goes on a USB 2.0 port. Keep the single USB 3.1 port free.
  - Display: the 4-lane MIPI DSI connector drives a DSI panel directly. HDMI 2.0 (4K30) remains available for bench use.
- **Double duty opportunities:**
  - The Q6A's 12 V header lets one 12 V buck converter replace the USB-C PD source board.
  - With the Dragon Q8B upgrade, the second M.2 slot (Gen3 x2) holds an NVMe drive for raw IQ. That removes the UFS module and makes 160 Msps bursts recordable continuously, at the cost of about 25 W under load.
  - With the RUBIK Pi 3, USB-C DisplayPort output could drive a USB-C portable touchscreen over one cable (video and touch). Its 2280 slot also removes the 2230-to-2280 extension.
  - Particle Tachyon's built-in 1-cell LiPo input and charger would replace the BMS and USB-C charging board, but the board costs $399-529.
  - The onboard Wi-Fi 6 and BT 5.4 can move IQ files and fetch TLEs for Gpredict without a dongle. Turn the radio off during weak-signal reception to cut self-interference.
  - The Adreno 643 (Vulkan 1.3, OpenCL 2.0) and the Hexagon HVX DSP could later take FFT and channelizer work. The NPU would then be one of three accelerators, so the SoC covers both DSP offload and AI.
- **Confidence:** medium

## Форуми та досвід спільноти (`forums`)

_Run `wf_88090a59-878`_

- **Component:** Compute board (NPU): Radxa Dragon Q6A (QCS6490) and alternatives (RUBIK Pi 3, Dragon Q8B, Particle Tachyon, RK3588 boards such as Orange Pi 5 Max and ROCK 5T, Pi 5 with PCIe SDR, Jetson), October 2026
- **Experiences:**
  1.
    - **Product:** Radxa Dragon Q6A + Radxa 256 GB UFS module (Kioxia THGJFGT1E45BAILB)
    - **Source url:** https://forum.radxa.com/t/ufs-random-reboots/30630
    - **Community:** Radxa forum
    - **What they built:** Desktop and server boards booting Radxa OS r2 from the Kioxia UFS module (users datum and pamvdam). One board ran on a 36 W DC12 adapter with a copper heatsink and fan (below 60 °C under stress), the other on PoE.
    - **Problems:**
      - 1-5 s stutters every few minutes, then hard freezes and reboots, only when booting from UFS (Apr 2026)
      - dmesg showed repeated ufshcd-qcom errors: 'Device abort task', pa_err/dl_err, and eh_device_reset 'failed with err -110'
      - fio measured about 60 MB/s during the fault, against Radxa's rated 557 MB/s write
      - Disabling auto-hibern8 did not help
      - Staff's first workaround (limit-hs-gear=2) left the errors in place and cut speed to 480 MB/s read and 377 MB/s write
    - **Fixes:**
      - Interim fix: a staff keep-alive script that stops the UFS from entering H8 (Apr 29)
      - Final fix: a kernel quirk that sets PA_TACTIVATE to 1 ms for the Kioxia THGJFGT1E45BAILB, shipped as a test 6.18.2 .deb and then merged as radxa/kernel PR #551 on 11 May 2026 (https://github.com/radxa/kernel/pulls?q=is%3Apr+kioxia)
    - **Outcome:** Both reporters confirmed the fix: no UFS errors and no freezes, with about 1.2 GB/s buffered reads. Staff could not reproduce the fault on Samsung UFS. Nobody confirmed whether the quirk reached Armbian or mainline.
  2.
    - **Product:** Radxa Dragon Q6A (early hands-on: NVMe, UFS, thermals, power)
    - **Source url:** https://forum.radxa.com/t/upcoming-radxa-dragon-q6a/26723?page=2
    - **Community:** Radxa forum (posts by Willy Tarreau, Sept 2025)
    - **What they built:** Early bench evaluation running builds and benchmarks, with a Samsung 980 NVMe drive and a UFS module.
    - **Problems:**
      - The board throttled at once: hwmon reported 90-91 °C, then power draw and CPU clock dropped. A 40x40 heatsink only delayed it, and the heatsink itself reached about 53 °C
      - UFS caused boot errors and reboot loops with USB timeouts on the original firmware
      - The 12 V header sits about 1.5 mm from the USB-C ground and could short
      - Boot order is NVMe, then UFS, then SD, then USB, so a leftover OS on an SSD took over the boot
      - Idle draw was 2.05 W with the GUI off, peaking at about 7.8 W
    - **Fixes:**
      - A strong fan kept the board under 79 °C with no throttling
      - A boot firmware update fixed the UFS errors
      - Willy suggested adding a diode or MOSFET on the 12 V input
    - **Outcome:** NVMe linked at Gen3 x2 and read at 1.3 GB/s. UFS read at 1.6-1.8 GB/s. The board was stable with active cooling.
  3.
    - **Product:** Radxa Dragon Q6A (independent benchmark)
    - **Source url:** https://github.com/geerlingguy/sbc-reviews/issues/85
    - **Community:** GitHub (Jeff Geerling's sbc-reviews) plus commenters
    - **What they built:** Standard SBC review: power at the wall, Geekbench, HPL, network, GPU and llama.cpp.
    - **Problems:**
      - The official image failed Etcher verification, and the board then showed no HDMI and no Ethernet link
      - 'Updating the board with rsetup makes it non boot anymore' (francorbacho, May 2026)
      - The PoE HAT fan is noisy, and its speed cannot be controlled over GPIO (irusensei)
      - llama.cpp on the Vulkan backend is 'kinda crashy', and NPU 'model selection for this board is quite anemic'
      - GravityMark segfaulted on the official image
    - **Fixes:**
      - Pre-expanding the .img, or trimming unallocated space in Etcher, fixed the flashing error
      - A user script switches the fan on at 70 °C and off at 60 °C
    - **Outcome:** Measured 2.9 W idle and 9.3-10.1 W under full CPU load. Geekbench 6: 1176 single, 3103 multi. Wi-Fi 6 gave about 187 Mbps and Ethernet about 940 Mbps. The board works, but the software needs care.
  4.
    - **Product:** Radxa Dragon Q6A and Thundercomm RUBIK Pi 3 (sbc-bench clock and thermal validation)
    - **Source url:** https://raw.githubusercontent.com/ThomasKaiser/sbc-bench/master/results/KBw_.txt
    - **Community:** GitHub (ThomasKaiser sbc-bench results); RUBIK Pi run: https://raw.githubusercontent.com/ThomasKaiser/sbc-bench/master/results/8WlQ.txt
    - **What they built:** Ran sbc-bench under Linux: a cpufreq sweep and sustained 7-zip and cpuminer load.
    - **Problems:**
      - The Q6A peaked at 81.8 °C during multi-core 7-zip (kernel 6.16.7-qcom, Sept 2025)
      - The prime core read 823 MHz at the start of the run, an idle governor artefact
      - The RUBIK Pi 3 peaked at 82.2 °C
    - **Fixes:**
      - None needed. Both runs had cooling fitted.
    - **Outcome:** Clocks held at their rated maximum under load. The Q6A measured 2698, 2391 and 1944 MHz; the RUBIK Pi 3 measured 2705, 2397 and 1952 MHz. sbc-bench reported 'No throttling'. Under Linux both boards run at the advertised CPU clocks.
  5.
    - **Product:** Radxa Dragon Q6A (cooling)
    - **Source url:** https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
    - **Community:** Radxa forum; also https://forum.radxa.com/t/recommended-heatsink-fan-for-q6a/30413
    - **What they built:** Owner-made cooling and 3D-printed cases, including El_Sattchmo's 'Q6A Case V4' on Printables and custom enclosures.
    - **Problems:**
      - A passive homemade heatsink 'repeatedly hits 90 degrees and throttles' (drake, Feb 2026)
      - In 35-40 °C ambient the CPU/GPU went over 90 °C and throttled (Rahul007, May 2026)
      - The board has no fan header
      - The included pad is too small to cover both the SoC and the LPDDR5
      - AliExpress cooler listings disappeared, and one seller never shipped
      - Wrongly placed standoffs leave the cooler sitting above the chips
    - **Fixes:**
      - A copper fin cooler with a 5 V fan powered from the 40-pin header's 5V/GND pins. drake: 'does indeed work very well'
      - A Noctua 40x10 mm 5 V fan with a speed-reducing cable
      - A Raspberry Pi CM5 cooler with the retaining plates removed, fixed with thermal tape
      - The Radxa Armor Case 7056A (about 40 °C idle), available from Arace in June 2026
      - A two-level copper heatsink: thermal paste on the SoC, a pad on the RAM
    - **Outcome:** Active cooling removed throttling in every report. Stressed temperatures were 55-60 °C.
  6.
    - **Product:** Radxa Dragon Q6A NPU (FastRPC/QNN HTP), Radxa OS R1/R2
    - **Source url:** https://forum.radxa.com/t/collecting-q6a-npu-fastrpc-issues/30321
    - **Community:** Radxa forum (staff-run collection thread)
    - **What they built:** ResNet50 qnn-net-run validation and QNN workloads.
    - **Problems:**
      - On the R1 image, qnn_open failed with 0x80000600 and libQnnHtpV68Skel failed to open (Feb 2026)
      - On R2 booted from NVMe, 'adsp.mbn failed with error -2' at early boot, then 'createUnsignedPD ... not supported by HTP', and adsprpcd crash-looped every 10 s
    - **Fixes:**
      - Staff: flash the R2 image (radxa-dragon-q6a_noble_gnome_r2), which ships FastRPC pre-enabled
      - Check `dmidecode -s bios-version` and update the SPI firmware to 6.0.260120
      - For NVMe or UFS boot (community fix by nalbakri): add an initramfs hook that copies adsp.mbn and cdsp.mbn from /lib/firmware/qcom/qcs6490/radxa/dragon-q6a/, then run update-initramfs -u
      - Add /etc/udev/rules.d/99-fastrpc.rules with KERNEL=="fastrpc-*", MODE="0666" plus a dma_heap rule
    - **Outcome:** ResNet50 classification worked after the fix. Root cause: the R2 image did not account for NVMe boot timing.
  7.
    - **Product:** Radxa Dragon Q6A NPU on Armbian/Ubuntu 24.04
    - **Source url:** https://forum.radxa.com/t/radxa-dragon-q6a-dragon-q6a-ubuntu-24-04-qnn-htp-backend-fails-with-qnn-open-0x80000600/30850
    - **Community:** Radxa forum
    - **What they built:** QNN EP for ONNX Runtime, QAI AppBuilder vision models, and LLM experiments (Rahul007, May 2026).
    - **Problems:**
      - qnn_open failed with 0x80000600, then 0x80000406
      - Host runtime 2.46 did not match the DSP skeleton 2.42, and libc++.so.1 was missing on the DSP side
      - Some ONNX Runtime QNN workloads silently fell back to the CPU
    - **Fixes:**
      - Copy the matching libQnnHtpV68Skel.so into /usr/lib/rfsa/adsp/cdsp/ and symlink libc++.so.1 and libc++abi.so.1
      - Replace adsp.mbn and cdsp.mbn, set ADSP_LIBRARY_PATH and LD_LIBRARY_PATH, and restart the CDSP remoteproc
      - Staff asked for checks of `ls /dev/fast*`, `ls /usr/lib/dsp` and the fastrpc_test output
    - **Outcome:** fastrpc_test passed 3/3, and qnn-net-run and vision models ran on the HTP. The author called it 'a very fragile state'. LLM acceleration did not work.
  8.
    - **Product:** Radxa Dragon Q6A NPU (DT overlay and firmware-file fix)
    - **Source url:** https://forum.radxa.com/t/dragon-q6a-fastrpc-npu-fails-fastrpc-ioctl-init-create-returns-0x80000600-on-cdsp/31078
    - **Community:** Radxa forum (thread with an accepted answer); related: https://forum.radxa.com/t/cdsp-fastrpc-session-still-fails-0x80000600-remotectl1-domains-not-supported-after-fixing-the-missing-memory-region-r2-ubuntu-24-04-kernel-7-0-11-5/31391
    - **What they built:** QNN, HTP and TFLite-delegate workloads on Ubuntu 24.04 with kernel 6.18.2-4-qcom.
    - **Problems:**
      - fastrpc_test failed with 0x80000600 on domain 3, with 'no reserved DMA memory for FASTRPC' in dmesg
      - `dpkg -V` showed modified fastrpc_shell_3 and fastrpc_shell_unsigned_3 files
      - On kernel 7.0.11-5 and RadxaOS, the error 'remotectl1 domains not supported' stayed unresolved, and that poster moved to Armbian
      - VTCM use is capped: 'only able to pass 2MB through it, even though the SRAM has 8MB'
    - **Fixes:**
      - A DTBO adding `memory-region = <&adsp_rpc_remote_heap_mem>` to the ADSP and CDSP FastRPC nodes, with `compatible = "shared-dma-pool"` on adsp-rpc-remote-heap@c6500000
      - Install the overlay through the active systemd-boot entry in /boot/efi/loader/entries/, not extlinux
      - Restore the fastrpc_shell files from `apt download radxa-firmware-qcs6490=0.2.29`
      - Do not run apt upgrade or autoremove afterwards
    - **Outcome:** 'All applicable tests PASSED' (Jul 9, 2026). Radxa staff did not confirm the fix. Staff later said the reserved-DMA warning is misleading (thread 30699).
  9.
    - **Product:** Radxa Dragon Q6A NPU: INT8-only HTP v68 and firmware locked to QAIRT 2.42
    - **Source url:** https://forum.radxa.com/t/dragon-q6a-qnn-htp-pipeline-working-but-int8-only-firmware-blocks-real-ml-workloads/31217
    - **Community:** Radxa forum (Dual-O, Jul 22, 2026)
    - **What they built:** Immich machine learning (ArcFace, CLIP ViT) on a working QNN HTP pipeline.
    - **Problems:**
      - FP16 models are rejected with 'The SocModel doesn't support FP16', so every layer must be INT8
      - ArcFace LFW accuracy collapsed to about 51%, chance level. CLIP embeddings collapsed to cosine similarity above 0.99
      - DSP firmware CDSP.HT.2.5.c4-00004-KODIAK-1 supports only QNN interface 2.32 (QAIRT 2.42)
      - QAIRT 2.46+ returns QNN_DEVICE_ERROR_INVALID_CONFIG
      - onnxruntime-qnn 2.4.0 needs QAIRT 2.48.40, and per-channel INT8 needs ORT 1.24+ or QAIRT 2.45+
    - **Fixes:**
      - None. The author asked for newer DSP firmware and got no staff answer.
    - **Outcome:** Unresolved. The author contrasts this with the RK3588 NPU, which supports FP16 per layer.
  10.
    - **Product:** Radxa Dragon Q6A NPU (QAIRT and AI Hub version matching)
    - **Source url:** https://forum.radxa.com/t/qcs6490-radxa-q6a-qairt-sdk-version-mismatch-ai-hub-artifacts-2-45-x-incompatible-with-runtime-2-42-0-251225/30908
    - **Community:** Radxa forum
    - **What they built:** YOLOv8 and Real-ESRGAN context binaries compiled on Qualcomm AI Hub for qualcomm-qcs6490 (w8a8).
    - **Problems:**
      - qnn-net-run failed with '[ERROR] Using newer context binary on old SDK' (error 5000/0x1388)
      - AI Hub built with 2.45.x, but the board runtime is 2.42.0.251225
    - **Fixes:**
      - Pin the QNN version when compiling on AI Hub, or install the matching QAIRT SDK version (Morgan, Jun 2, 2026)
      - Community converters: github.com/ImRIzo/onnx2qnn and QAIRT_Model_Quantization_Toolkit
    - **Outcome:** The workaround is known, but no exact commands were posted.
  11.
    - **Product:** Radxa Dragon Q6A NPU (custom YOLOv8n and Frigate)
    - **Source url:** https://forum.radxa.com/t/yolov8n-context-binary-generation-for-q6a/30899
    - **Community:** Radxa forum; also https://forum.radxa.com/t/running-custom-frigate-with-full-npu-support-dragon-q6a/31047 and https://forum.radxa.com/t/issues-running-yolov8n-with-qairt-sdk-2-49-on-radxa-dragon-q6a-qcs6490/31462
    - **What they built:** A custom-trained YOLOv8n context binary, and Frigate 0.17 with a ZMQ detector backed by QAIRT 2.46 on the HTP.
    - **Problems:**
      - Quantizing the concatenated YOLO output gave all-zero or garbage detections
      - The Q6A is not an AI Hub target, so the RB3 Gen2 (same chip) served as a proxy
      - A Sept 2026 report: pure-QAIRT 2.49 quantization collapsed to zeros, with no replies
      - Frigate's zmq detector crashed on a None model path
    - **Fixes:**
      - Split the box and score outputs before quantization
      - Upload real calibration data with hub.upload_dataset
      - Use submit_compile_and_link_jobs with explicit input_specs and --target_runtime qnn_dlc
      - Dequantize each output separately
      - For Frigate: pass /dev/fastrpc-cdsp and /dev/ion into the container, patch zmq_ipc.py, run an HTP INT8 high-performance config
    - **Outcome:** The custom YOLOv8n ran at about 20 ms (the official binary takes 10-12 ms). Frigate got about 10 ms inference at 0.2% CPU. The NPU is usable once quantization is done carefully.
  12.
    - **Product:** Radxa Dragon Q6A NPU (Python stack)
    - **Source url:** https://forum.radxa.com/t/non-functional-npu-support-on-dragon-q6a-qcs6490-under-ubuntu-24-04-noble/30699
    - **Community:** Radxa forum
    - **What they built:** Python ONNX Runtime and QNN pipelines.
    - **Problems:**
      - No working Python 3.12 onnxruntime-qnn wheels; the poster called the NPU 'dead silicon' (Apr 2026)
      - Missing /dev/fastrpc* nodes and firmware load error -2
      - radxa-firmware-qcs6490 0.2.38 would not install because firmware-qcom-audioreach was missing (Aug 2026)
      - As of Aug 6, FastRPC still failed on RadxaOS
    - **Fixes:**
      - Staff (May 14): a Python 3.12 wheel was built and installs with pip3
      - Matched cdsp.mbn and shell binaries got fastrpc_test passing on Armbian
      - Dual-O reached a working pipeline using firmware taken from Radxa OS r2
    - **Outcome:** Mixed. The first poster returned the board for a Raspberry Pi 5 with the AI Kit. Others got it working, but NPU and VPU concurrency was never tested.
  13.
    - **Product:** QCS6490 FastRPC userspace (Qualcomm RB3 Gen2; affects all QCS6490 boards)
    - **Source url:** https://github.com/qualcomm/fastrpc/issues/371
    - **Community:** GitHub (qualcomm/fastrpc); also https://github.com/radxa-pkg/fastrpc/issues/18
    - **What they built:** Qualcomm's own CI tests on qcs6490-rb3gen2-vision-kit.
    - **Problems:**
      - fastrpc 1.0.6 fails the CDSP signed and unsigned tests (0x72, 'Unable to create FastRPC session on domain 3')
      - 1.0.2 passes on the same board
      - The radxa-pkg/fastrpc #18 report (Debian, kernel 7.0.11) is still open with no maintainer reply
    - **Fixes:**
      - Loïc Minier carries a udev patch in the Debian packages as a workaround
      - Practical workaround: stay on a known-good fastrpc version
    - **Outcome:** Open and marked stale on 30 Sep 2026. The NPU userspace is fragile even on Qualcomm's reference board.
  14.
    - **Product:** Radxa Dragon Q6A (kernel 7.0 regressions; community Ubuntu 26.04 images)
    - **Source url:** https://forum.radxa.com/t/linux-7-0-hdmi-not-working/31304
    - **Community:** Radxa forum; also https://forum.radxa.com/t/ubuntu-26-04-1-lts-images-for-the-radxa-dragon-q6a-now-on-linux-7-2-9-hdmi-works-wi-fi-bt-audio-npu-apt-upgrade-safe/31574
    - **What they built:** Desktop and headless systems updated through apt full-upgrade.
    - **Problems:**
      - Upgrading from 6.18.2-4-qcom to 7.0.11-4-qcom killed HDMI ('Cannot find any crtc or sizes', dead hotplug)
      - Audio devices went missing
      - CPU0 sat at 50-60% while idle
      - An unbind/rebind attempt caused a NULL-pointer crash in thermal code
    - **Fixes:**
      - Roll back to and boot kernel 6.18.2
      - Later Radxa kernel updates fixed HDMI (drake, Sep 9)
      - Community v1.3.0 images (rafaelwms, Oct 7, 2026): Ubuntu 26.04.1 on Armbian-edge 7.2.9 with DP/DPU patches; HDMI, Wi-Fi, BT, audio and NPU device nodes reported working
    - **Outcome:** Fixed after a few weeks. The lesson is to pin a known-good kernel on a field device.
  15.
    - **Product:** Radxa Dragon Q6A (dead boards, DDR training failures, boot loops)
    - **Source url:** https://forum.radxa.com/t/radxa-dragon-q6a-with-ddr-problem/29863
    - **Community:** Radxa forum; also https://forum.radxa.com/t/dragon-q6a-wont-boot-ddr-rcw-training-fails-on-cold-boot-board-loops-into-edl/30841 , https://forum.radxa.com/t/help-radxa-q6a-infinite-boot-loop-reset-every-10-seconds-hardware-issue-suspected/30749 , https://forum.radxa.com/t/spi-firmware-flash-bricked-my-q6a/31450
    - **What they built:** Ordinary 6 GB and 12 GB boards bought from Arace, AliExpress and resellers.
    - **Problems:**
      - DDR_ABORT errors (NO_MEMORY_DEVICE_DETECTED, RCW_TRAINING_FAIL, DRAM_DCC_FAIL) after the first boot or a shutdown
      - A reset every 10 s, even in EDL mode
      - A cold-boot hang after an SPI flash
      - At least 5 reports in one thread, more in others (Dec 2025 to Sep 2026)
    - **Fixes:**
      - Reflash SPI over EDL (edl-ng with prog_firehose_lite.elf) and erase the cdt/DDR partitions (staff)
      - One case was fixed by replacing a charger labelled 12 V that 'did not actually provide 12V'
      - Otherwise RMA. Staff: 'very likely a hardware issue'
    - **Outcome:** Most cases ended in warranty returns. The AliExpress buyer received store points instead of a replacement: 'Be careful when purchasing from AliExpress.'
  16.
    - **Product:** Radxa Dragon Q6A M.2 slot (NVMe)
    - **Source url:** https://forum.radxa.com/t/nvme-2230-not-detected/30807
    - **Community:** Radxa forum; also https://forum.radxa.com/t/nvme-ssd-m-2-2230-gen3x4-not-enumerated-by-uefi/31195 and https://forum.radxa.com/t/windows-on-radxa-dragon-q6a/29913?page=3
    - **What they built:** Windows 11 and Linux on 2230 NVMe drives.
    - **Problems:**
      - After a sudden reboot the M.2 socket detected nothing; three SSDs tested, and Radxa OS also saw nothing (May 2026)
      - BIOS 260120 UEFI did not enumerate an ARES Gen3x4 drive, though Linux saw /dev/nvme0n1 (Jul 2026)
      - An SM2267XT-based SSD failed under Windows
    - **Fixes:**
      - Brushing dust off the slot fixed one user's boot problem
      - Board RMA for the dead socket
      - Drives reported working: Crucial P310, Kioxia BC150/BG6, Samsung 980
    - **Outcome:** The dead socket went back on warranty, and the UEFI enumeration case is unresolved. Every report involves NVMe; none involves a non-storage PCIe card.
  17.
    - **Product:** Radxa Dragon Q6A power input and battery options
    - **Source url:** https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
    - **Community:** Radxa forum; also https://forum.radxa.com/t/powering-the-q6a-via-the-5v-pin-on-the-40-pin-header/30833 , https://forum.radxa.com/t/radxa-q6a-running-on-a-battery-and-charging/29650 , https://forum.radxa.com/t/question-about-the-three-pogo-pads-ts-on-the-back-of-dragon-q6a/30090
    - **What they built:** Outdoor battery-powered setups using DC-DC converters.
    - **Problems:**
      - The 40-pin 5V pins cannot power the board (staff, May 18, 2026)
      - The +/−/TS battery pogo pads only work after fitting the unpopulated R24, VPH_PWR must stay at or below 4.5 V, charging is disabled, and there is no official battery module
    - **Fixes:**
      - Staff (BigfootACA, Mar 2, 2026): the 12 V pin accepts 3.6-16 V, with 5, 9 or 12 V recommended. It feeds an SY81012 buck to 4.2 V
      - 'Do not use the USB Type-C interface if you are supplying 12V power externally'
      - USB-C accepts 12 V PD and also 5 V/3 A
      - The 40-pin 3.3 V rail comes from an ETA3521 (in theory up to 4 A), but staff advise an external step-down for peripherals
    - **Outcome:** The board can run from a regulated 12 V feed on the header. The researcher's claim of '12 V only' is wrong. A raw 4S pack (12.0-16.8 V) exceeds 16 V when full, so it must be regulated.
  18.
    - **Product:** Radxa Dragon Q6A onboard Wi-Fi (AIC8800, USB-attached) on Armbian
    - **Source url:** https://forum.armbian.com/topic/60133-wifi-gone-on-current-version/
    - **Community:** Armbian forum
    - **What they built:** Armbian Ubuntu 24.04 desktops on the Q6A.
    - **Problems:**
      - After apt upgrades or a reinstall, lsusb shows a69c:8d80 but no wlan interface appears
      - aic8800-usb-dkms fails to build because the kernel was built with gcc 14 and the image defaults to gcc 13 (unknown flag -fmin-function-alignment=8)
    - **Fixes:**
      - Install aic8800-firmware and aic8800-usb-dkms straight from Radxa's GitHub releases (radxa-pkg/aic8800), run depmod -a, then reboot
      - dpkg-reconfigure works for some users only
    - **Outcome:** Recurs on kernel updates. The onboard Wi-Fi is a USB device, which matters for USB bus sharing.
  19.
    - **Product:** Radxa Dragon Q6A GPU compute (OpenCL/Vulkan for DSP offload)
    - **Source url:** https://forum.radxa.com/t/how-to-install-qualcomm-opencl-sdk-on-dragon-q6a/30787
    - **Community:** Radxa forum; also https://forum.radxa.com/t/gpu-enabled-ubuntu-image-like-the-rubik-pi/30965
    - **What they built:** clpeak benchmarks, and an attempt at AdaFace inference on the GPU.
    - **Problems:**
      - Mesa rusticl OpenCL is up to 4x slower than Qualcomm's OpenCL. clpeak half/float GFLOPS: rusticl 405/553, Qualcomm 0838.5 943/650, Vulkan 1096/748, Android 1600/1247
      - The Qualcomm OpenCL SDK does not build on the board
      - The QNN GPU backend fails because Radxa OS uses Freedreno; RUBIK Pi images ship the proprietary driver
    - **Fixes:**
      - The qcom-adreno-cl-dev binary package works better than rusticl
      - Vulkan compute is the fastest path under Linux
    - **Outcome:** The GPU is usable for FFT through Vulkan. OpenCL is suboptimal, and GPU inference through QNN is not available on Radxa OS.
  20.
    - **Product:** Thundercomm RUBIK Pi 3 (QCS6490)
    - **Source url:** https://github.com/rubikpi-ai/linux/issues/20
    - **Community:** GitHub (rubikpi-ai org); also https://github.com/rubikpi-ai/documentation/issues/12 and https://lkml.iu.edu/2511.2/09492.html
    - **What they built:** OpenCL llama.cpp on the Adreno 643L under Ubuntu (kernel 6.8.0-1057-qcom), a custom MobileNetV2 on the HTP through the TFLite delegate, and mainline DTS testing.
    - **Problems:**
      - clinfo found 0 platforms because installing ocl-icd-opencl-dev silently removed qcom-adreno1, and that package was then pulled from the PPA (404)
      - The QNN TFLite delegate failed on a custom MobileNetV2 with 'Restored original execution plan after delegate application failure' (Jan 2026, open, no maintainer reply)
      - On linux-next (Nov 2025), PCIe probe hit a 'synchronous external abort'; the board booted only with pcie0 and pcie1 disabled
    - **Fixes:**
      - Run dpkg-repack on qcom-adreno1 from a working board and install it with dpkg -i
      - For the linux-next PCIe failure, Roger Shimizu reverted two commits (b15ce3c0882c, 03e928442d46)
    - **Outcome:** Same SoC and similar rough edges as the Q6A. The vendor driver stack is better for GPU work, but NPU custom-model support is just as unanswered.
  21.
    - **Product:** Radxa Dragon Q8B (SC8280XP)
    - **Source url:** https://github.com/geerlingguy/sbc-reviews/issues/108
    - **Community:** GitHub (sbc-reviews); also https://forum.radxa.com/t/usb-issues-in-bios-on-q8b/31582 and https://hackaday.com/2026/10/10/poking-at-the-radxa-dragon-q8b-raspberry-pi-5-killer/
    - **What they built:** Full SBC review, plus OS installs from USB to NVMe.
    - **Problems:**
      - Power: 4.9 W idle; 20.9 W stress-ng; 23.7-24.3 W llama.cpp; 33 W HPL, up to 43.5 W
      - Geerling: 'Definitely need a 65W power adapter' when peripherals are attached
      - The X1C cores are capped at 2.5 GHz, not 3.0 GHz
      - The BIOS did not detect USB ISOs, the installer reset-looped, and BIOS builds after 260923 broke display output for third-party OSes
      - Units shipped months late
    - **Fixes:**
      - New BIOS builds flashed with edl-ng (a Thunderbolt cable was needed from a Mac)
      - Use the Ubuntu 26.04 desktop ISO with all Third-Party OS Compatibility Options enabled (strongtz, Oct 14)
    - **Outcome:** Fast (GB6 1405/6302), but the BIOS is still being fixed as of October 2026 and power is 2-4x the Q6A's. A poor fit for a 72 Wh handheld.
  22.
    - **Product:** Particle Tachyon (QCM6490)
    - **Source url:** https://community.particle.io/t/ubuntu-24-04-1-0-172-hard-reboots-every-5-10-minutes/70992
    - **Community:** Particle community forum; also https://community.particle.io/t/is-this-project-dead/71385 and https://community.particle.io/search.json?q=tachyon%20npu
    - **What they built:** Ubuntu 24.04 desktops, Frigate with the Hexagon NPU, modem projects.
    - **Problems:**
      - Hard reboots every 5-10 minutes on Ubuntu 24.04 (builds 1.0.172 and 1.1.43) on every power source, including the battery
      - The QNN TFLite delegate fails with 'createUnsignedPD ... not supported by HTP' (Apr 2026)
      - Desktop mode needs a battery attached
      - Ubuntu 24.04 runs kernel 6.8, so newer drivers such as RTL8125 are missing
      - Users complained of slow staff responses ('Is this project dead?')
    - **Fixes:**
      - Staff blamed low-quality USB PD supplies and recommended the latest release; neither fixed the reboots
    - **Outcome:** Unresolved. Stability and NPU support are worse than on the Q6A, at three times the price.
  23.
    - **Product:** Orange Pi 5 / 5 Plus / 5 Max (RK3588 family)
    - **Source url:** https://forum.armbian.com/topic/45507-opi-5-16gb-random-fails-with-nvme/
    - **Community:** Armbian forum; also https://forum.armbian.com/topic/61753-orangepi-5-nvme-pcie-voltage-regulator-gpio-bug/ , https://forum.armbian.com/topic/62281-driving-orange-pi-5-max-fan/ , https://raw.githubusercontent.com/ThomasKaiser/sbc-bench/master/results/XyIw.txt
    - **What they built:** NVMe-booted desktops and servers; Orange Pi 5 Max benchmarks.
    - **Problems:**
      - Random NVMe probe failures ('Removing after probe failure status: -19') linked to the 5 V supply droop ('If voltage breaks below 4.9 to 5V issues are to be expected'), and to particular drives such as the WD SN750
      - On Orange Pi 5 v1.3.2 the M.2 power-enable GPIO differs from the mainline DTS ('PCIe Link Fail, LTSSM is 0x3')
      - On the Orange Pi 5 Max, the Armbian image does not drive the fan control pin (GPIO3_D1)
    - **Fixes:**
      - A 5.1 V/5 A supply, or a 90 W laptop PD supply, fixed the heavy-I/O failures for one user
      - Switching to a Team Group or Crucial P3 Plus drive fixed it for others
      - A user DT overlay moving the regulator to gpio2 pin 1, or a patched SPI U-Boot (for v1.3.2 only)
    - **Outcome:** The Orange Pi 5 Max held 2283/1833 MHz with no throttling and peaked at 52.7 °C in sbc-bench. Software is mature, but the 5 V/5 A power path and per-revision DTS quirks are recurring problems.
  24.
    - **Product:** Radxa ROCK 5T / ROCK 5B+ (RK3588)
    - **Source url:** https://forum.radxa.com/t/rock-5b-m-2-b-key-connector-support-sata-expansion-card/23758
    - **Community:** Radxa forum; also https://forum.radxa.com/t/nvme-disconnecting-automatically-on-rock-5t-debian-12/28369 and https://docs.radxa.com/en/rock5/rock5t/hardware-design/hardware-interface
    - **What they built:** NAS and NVMe setups with SATA and other adapters in the M.2 slots.
    - **Problems:**
      - The M.2 B-key on the 5B+ and 5T carries USB 2.0 only. Staff: 'only connected to the usb signal'. PCIe pins 29/31/35/37 are not connected
      - On the ROCK 5T, NVMe drops after hours and the filesystem remounts read-only (36 W adapter, Aug 2025)
    - **Fixes:**
      - The kernel log suggests nvme_core.default_ps_max_latency_us=0 and pcie_aspm=off; nobody confirmed it
    - **Outcome:** Correction to the findings: the ROCK 5T's second PCIe slot is a second M-key (PCIE30 x2 per the Radxa docs), not the B-key. The NVMe dropout is unresolved.
  25.
    - **Product:** Raspberry Pi 5 + LimeSDR XTRX (PCIe SDR on an ARM SBC, nearest analogue to Q6A + LimeSDR Micro)
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-xtrx-operation-on-raspberry-pi-5-via-mpcie-hat/8850
    - **Community:** MyriadRF Discourse
    - **What they built:** An XTRX v1.2 on a 52Pi M02 mPCIe HAT on a Pi 5, running LimeSuiteNG.
    - **Problems:**
      - Older boards needed the R114 mod (PERST controlling the power supply)
      - The board runs warm even at idle and 'uncomfortably warm' near maximum sample rate
      - TX-like activity at power-on knocked out Wi-Fi
      - Other threads report intermittent lspci detection through adapters, blamed on signal integrity
    - **Fixes:**
      - Add `dtparam=pciex1` and build LimeSuiteNG; `limeDevice --full` then detected the card
      - A 40 mm fan held 50-55 °C
      - BOM_VER 1 boards no longer need R114
    - **Outcome:** The card enumerates and works on an ARM host. Heat and startup TX remain issues. Nobody reported sustained sample rates.
  26.
    - **Product:** LimeSDR Micro M.2 (as a load on the host's M.2 slot)
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
    - **Community:** MyriadRF Discourse; also https://discourse.myriadrf.org/t/limesdr-micro-m-2-pcie-frequency-range/13348
    - **What they built:** Carrier-board design for the M.2 version (jonsnow, Aug 2026), and checks on the RX frequency range.
    - **Problems:**
      - The schematic lists 2.5 A at 3.3 V (8.25 W). Lime explained that figure is the PCIe allowance
      - Idle power was asked about and never answered
      - The docs show RX matching bands starting at 300 MHz
    - **Fixes:**
      - Zack (Lime): 'Board should consume about 4 W, depending on configuration'
      - Andrew Back: 'There are no gaps in frequency coverage'; the bands only show where the matching networks are optimised
    - **Outcome:** Expect about 4 W drawn from the Q6A's M.2 3.3 V rail. No performance data exists near 30-137 MHz.
  27.
    - **Product:** M.2 riser/extension cable carrying a Gen3 PCIe endpoint (risk analogue for the Q6A 2230-to-2280 extension)
    - **Source url:** https://forum.proxmox.com/threads/force-pcie-port-downgrade-at-boot-or-solve-aer-errors.173498/
    - **Community:** Proxmox forum (found via search)
    - **What they built:** An Intel X540 10GbE NIC on a 25 cm M.2 riser from a 2242 slot.
    - **Problems:**
      - Correctable AER errors (Data Link Layer timeouts, RxErr), then reset loops under sustained iperf3 load
    - **Fixes:**
      - Forcing the link down to a lower generation was the poster's goal; a related thread fixed AER floods by forcing Gen3 in the BIOS
    - **Outcome:** Shows that long risers can break sustained-throughput PCIe links. The Q6A cannot force a lower link speed from a BIOS menu.
- **Common problems:**
  1.
    - **Problem:** NPU (Hexagon HTP v68) FastRPC session failures: 0x80000600, 0x80000406, 'createUnsignedPD not supported', 'no reserved DMA memory'. Causes are mismatched DSP firmware, fastrpc_shell and libQnnHtpV68Skel versions, early-boot firmware loading, and missing device-node permissions.
    - **Affected products:** Radxa Dragon Q6A (R1, R2, Armbian, kernel 7.0), Particle Tachyon (Ubuntu 24.04), Qualcomm RB3 Gen2 (fastrpc 1.0.6)
    - **Frequency:** common
    - **Known fix:** Use the Radxa OS r2 image with SPI BIOS 6.0.260120. For NVMe or UFS boot, put adsp.mbn and cdsp.mbn in the initramfs and add udev rules for fastrpc-* and dma_heap. If the shells were overwritten, restore fastrpc_shell_3 and fastrpc_shell_unsigned_3 from radxa-firmware-qcs6490=0.2.29. Optionally add a DT overlay that sets memory-region and shared-dma-pool. Check with `fastrpc_test -a v68`. Once it works, hold the packages (no apt upgrade or autoremove).
    - **Fix sources:**
      - https://forum.radxa.com/t/collecting-q6a-npu-fastrpc-issues/30321
      - https://forum.radxa.com/t/dragon-q6a-fastrpc-npu-fails-fastrpc-ioctl-init-create-returns-0x80000600-on-cdsp/31078
      - https://forum.radxa.com/t/radxa-dragon-q6a-dragon-q6a-ubuntu-24-04-qnn-htp-backend-fails-with-qnn-open-0x80000600/30850
      - https://github.com/qualcomm/fastrpc/issues/371
  2.
    - **Problem:** QAIRT version lock. The Q6A DSP firmware (CDSP.HT.2.5.c4) supports only QNN interface 2.32, i.e. QAIRT 2.42. AI Hub context binaries built with 2.45+ fail with 'Using newer context binary on old SDK', and QAIRT 2.46+ can fail with INVALID_CONFIG. Reports conflict: some users run 2.46 successfully.
    - **Affected products:** Radxa Dragon Q6A; likely all QCS6490 boards with vendor DSP firmware
    - **Frequency:** common
    - **Known fix:** Pin one QAIRT version that matches the board's DSP firmware and runtime (2.42 on stock r2), and pin the same QNN version in AI Hub compile jobs. Version reports vary, so test both 2.42 and 2.46 against fastrpc_test and qnn-net-run on your own image.
    - **Fix sources:**
      - https://forum.radxa.com/t/qcs6490-radxa-q6a-qairt-sdk-version-mismatch-ai-hub-artifacts-2-45-x-incompatible-with-runtime-2-42-0-251225/30908
      - https://forum.radxa.com/t/dragon-q6a-qnn-htp-pipeline-working-but-int8-only-firmware-blocks-real-ml-workloads/31217
  3.
    - **Problem:** The NPU is INT8-only: FP16 is rejected with 'SocModel doesn't support FP16'. Naive quantization can wreck accuracy (ArcFace at chance level) or zero out outputs (YOLO with concatenated outputs).
    - **Affected products:** All QCS6490/QCM6490 boards (Q6A, RUBIK Pi 3, Tachyon)
    - **Frequency:** common
    - **Known fix:** Design the classifier for INT8. Split multi-head outputs before quantizing, use real calibration data and per-channel quantization where the runtime supports it, compare INT8 accuracy against FP32 on the PC, and keep a CPU fallback (ONNX Runtime CPU or LiteRT XNNPACK).
    - **Fix sources:**
      - https://forum.radxa.com/t/yolov8n-context-binary-generation-for-q6a/30899
      - https://forum.radxa.com/t/dragon-q6a-qnn-htp-pipeline-working-but-int8-only-firmware-blocks-real-ml-workloads/31217
  4.
    - **Problem:** Thermal throttling at about 90-91 °C with passive or no cooling, worse in 35-40 °C ambient. There is no fan header and no bundled cooler.
    - **Affected products:** Radxa Dragon Q6A; RUBIK Pi 3 (the manual says active cooling is required)
    - **Frequency:** common
    - **Known fix:** Fit a copper heatsink with a 5 V fan powered from the 40-pin 5V/GND pins (30-40 mm fans, Noctua with a low-noise cable, or a modified Pi CM5 cooler), or the Radxa Armor Case 7056A. Put thermal paste on the SoC and a pad on the LPDDR5. Reported results: 55-79 °C with no throttling, and sbc-bench peaks around 82 °C at full clocks.
    - **Fix sources:**
      - https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
      - https://forum.radxa.com/t/recommended-heatsink-fan-for-q6a/30413
      - https://forum.radxa.com/t/upcoming-radxa-dragon-q6a/26723?page=2
  5.
    - **Problem:** Updates break the system: kernel 7.0.x killed HDMI and audio; DKMS Wi-Fi drivers fail to build against new kernels (gcc 13 vs 14); rupdate or rsetup updates left boards stuck at the boot menu or unbootable.
    - **Affected products:** Radxa Dragon Q6A (Radxa OS and Armbian); Radxa Dragon Q8B BIOS regressions
    - **Frequency:** common
    - **Known fix:** Pin a known-good kernel (6.18.2-x-qcom) with apt-mark hold, and only update deliberately. If Wi-Fi breaks, reinstall aic8800-firmware and aic8800-usb-dkms from Radxa's GitHub releases and run depmod -a. Keep a UART console cable and an EDL recovery kit (edl-ng, a USB-A-to-A cable on the blue USB 3 port).
    - **Fix sources:**
      - https://forum.radxa.com/t/linux-7-0-hdmi-not-working/31304
      - https://forum.armbian.com/topic/60133-wifi-gone-on-current-version/
      - https://forum.radxa.com/t/q6a-no-longer-autoboots-into-radxaos/30925
  6.
    - **Problem:** The Kioxia 256 GB UFS module froze, stuttered and rebooted the system, with ufshcd abort and reset errors and about 60 MB/s fio.
    - **Affected products:** Radxa Dragon Q6A with the Radxa 256 GB Kioxia THGJFGT1E45BAILB UFS module
    - **Frequency:** occasional
    - **Known fix:** Run a Radxa kernel that includes the PA_TACTIVATE=1 ms quirk (radxa/kernel PR #551, merged 11 May 2026). The Samsung 128 GB module did not show the problem.
    - **Fix sources:**
      - https://forum.radxa.com/t/ufs-random-reboots/30630?page=2
      - https://github.com/radxa/kernel/pulls?q=is%3Apr+kioxia
  7.
    - **Problem:** Dead-on-arrival or early-life failures: DDR training aborts, reset loops every 10 s, a dead M.2 socket, cold-boot hangs after an SPI flash.
    - **Affected products:** Radxa Dragon Q6A (6 GB and 12 GB; Arace, AliExpress and resellers)
    - **Frequency:** occasional
    - **Known fix:** Test the board fully as soon as it arrives. Reflash SPI over EDL and erase the cdt partition, check that the 12 V supply really delivers 12 V, then RMA. Buy from Arace or an official store rather than AliExpress third-party sellers: one AliExpress RMA ended with store points instead of a replacement.
    - **Fix sources:**
      - https://forum.radxa.com/t/radxa-dragon-q6a-with-ddr-problem/29863
      - https://forum.radxa.com/t/dragon-q6a-wont-boot-ddr-rcw-training-fails-on-cold-boot-board-loops-into-edl/30841
      - https://forum.radxa.com/t/help-radxa-q6a-infinite-boot-loop-reset-every-10-seconds-hardware-issue-suspected/30749
      - https://forum.radxa.com/t/nvme-2230-not-detected/30807
  8.
    - **Problem:** Marginal power causes resets or NVMe dropouts: weak USB-C PD supplies, '12 V' chargers that don't deliver 12 V, and 5 V droop on RK3588 boards.
    - **Affected products:** Q6A, Tachyon, Dragon Q8B (Geerling suspected his 65 W Anker), Orange Pi 5 / 5 Plus, ROCK 5T
    - **Frequency:** common
    - **Known fix:** On the Q6A, feed a regulated 12 V (3.6-16 V allowed) into the 12 V header from a buck converter rated at least 2-3 A. Never connect USB-C power at the same time. On RK3588 boards use a 5.1 V/5 A supply. Size the Q8B supply at 65 W.
    - **Fix sources:**
      - https://forum.radxa.com/t/how-to-power-the-dragon-q6a/30400
      - https://forum.armbian.com/topic/45507-opi-5-16gb-random-fails-with-nvme/
      - https://github.com/geerlingguy/sbc-reviews/issues/108
  9.
    - **Problem:** The GPU compute stack on Radxa OS is immature: rusticl OpenCL is up to 4x slower, there is no QNN GPU backend (Freedreno), and installing generic ocl-icd packages on RUBIK Pi silently removed the vendor Adreno driver.
    - **Affected products:** Radxa Dragon Q6A; Thundercomm RUBIK Pi 3
    - **Frequency:** common
    - **Known fix:** Use Vulkan compute (1096/748 GFLOPS half/float) or the qcom-adreno-cl-dev package on the Q6A. On the RUBIK Pi, don't install ocl-icd-* alongside qcom-adreno1; to recover, dpkg-repack the package from a working board.
    - **Fix sources:**
      - https://forum.radxa.com/t/how-to-install-qualcomm-opencl-sdk-on-dragon-q6a/30787
      - https://github.com/rubikpi-ai/linux/issues/20
  10.
    - **Problem:** Wrong or incompatible storage modules: Orange Pi eMMC modules shut the Q6A down immediately, and microSD cards fail after months of use.
    - **Affected products:** Radxa Dragon Q6A
    - **Frequency:** occasional
    - **Known fix:** Use only Radxa UFS or eMMC modules, and don't run the OS from microSD long-term.
    - **Fix sources:**
      - https://forum.radxa.com/t/radxa-q6a-only-blinks-green-light/30202
      - https://forum.radxa.com/t/radxa-dragon-q6a-was-running-stable-for-3-4-months-then-failed-and-would-no-longer-boot/31509
- **Unresolved problems:**
  1.
    - **Problem:** No one has documented a non-NVMe PCIe endpoint (SDR, FPGA, accelerator or Wi-Fi card) in the Q6A's M.2 slot. Every report involves an NVMe SSD.
    - **Evidence:** Radxa forum searches for 'q6a pcie', 'q6a lspci', 'q6a gen3', 'q6a hailo', 'sdr q6a' and 'q6a m.2 extension 2280' returned NVMe-only threads, plus one post noting that 2280 accelerators won't fit the 2230 slot (topic 30500).
    - **Why it matters for us:** The whole wideband architecture rests on the LimeSDR Micro (LA9310 plus LMS7002M) running over the Q6A's PCIe with DMA, MSI and BAR mapping. That combination is untested on QCS6490. Make it the first test before buying anything else.
  2.
    - **Problem:** LimeSDR Micro host support on arm64 is undocumented.
    - **Evidence:** The LimeSuiteNG 'limesdr-micro' branch (updated 1 Oct 2026) and 'limesdr-micro-staging' (15 Oct 2026) exist, but the README on the branch lists only USB/Mini/Mini v2/XTRX and states no architecture. The only arm64 PCIe report is XTRX on a Pi 5 (enumeration only, no sample-rate data).
    - **Why it matters for us:** A kernel driver or DMA problem on arm64 would remove the reason for the M.2 design, leaving only the USB 3 fallback with its uncertain 246 MB/s.
  3.
    - **Problem:** Nobody has published SatDump, SDR++, GNU Radio or gr-satellites running on any QCS6490 board.
    - **Evidence:** Searches of the Radxa forum, SatNOGS community, SatDump GitHub issues and general web for QCS6490/Q6A/RUBIK Pi plus SDR software found nothing.
    - **Why it matters for us:** CPU headroom for a 56 MHz live FFT, HRPT decoding and the NN classifier together on 1x A78 at 2.7 GHz plus 3x A78 at 2.4 GHz is unverified. The 32-bit memory bus (about 8.4 GB/s memcpy per sbc-bench) may limit large FFTs and IQ ring buffers.
  4.
    - **Problem:** Long-run NPU stability and concurrency.
    - **Evidence:** In topic 29949 the HTP stalls after about an hour with 'qnn_open failed, 0xffffffff' (unresolved). NPU and VPU concurrency is untested (topic 30699). VTCM appears capped at 2 MB (topic 31078). The remotectl1 failure on Radxa OS with kernel 7.0.11 is unresolved (topic 31391). The upstream fastrpc 1.0.6 regression is open (qualcomm/fastrpc #371).
    - **Why it matters for us:** A field classifier must run for whole passes, and HRPT passes last 10-15 minutes. Add a watchdog and CPU fallback, and keep the model small enough for 2 MB of VTCM.
  5.
    - **Problem:** INT8 accuracy for an RF modulation classifier on HTP v68.
    - **Evidence:** No FP16 support. Dual-O saw ArcFace collapse to 51% after INT8, and YOLO outputs collapsed without split quantization. Nobody has reported a 1D CNN or IQ classifier on QCS6490.
    - **Why it matters for us:** If INT8 badly degrades the modulation classifier, the 'must have NPU' goal fails on the Q6A. RK3588 boards do FP16 per layer, which makes them the fallback.
  6.
    - **Problem:** The current capacity of the Q6A's M.2 3.3 V rail is not published.
    - **Evidence:** Lime gives about 4 W typical and 2.5 A at 3.3 V as the PCIe spec allowance, with idle power unanswered (MyriadRF 13304). Radxa only states that the 40-pin 3.3 V rail (ETA3521) is shared and that peripherals should use an external buck.
    - **Why it matters for us:** Brown-outs during LMS7002M or LA9310 calibration or TX-path startup could look like the 'random reboot' reports. Measure the rail current and voltage under load.
  7.
    - **Problem:** Q6A 12 V header tolerance and layout.
    - **Evidence:** Staff give 3.6-16 V and warn against using USB-C at the same time. Willy notes the header is about 1.5 mm from the USB-C ground. No reverse-polarity or surge protection is documented.
    - **Why it matters for us:** A 4S Li-ion pack reaches 16.8 V when full, above 16 V, so it needs a regulated 12 V buck plus a protection diode or ideal-diode MOSFET. A slip in a handheld case could short the input.
  8.
    - **Problem:** USB topology and throughput are undocumented.
    - **Evidence:** The onboard AIC8800 Wi-Fi is a USB device (lsusb a69c:8d80). No community USB 3.1 throughput measurement exists. Nobody has run an RTL-SDR on the Q6A's USB 2.0 ports.
    - **Why it matters for us:** The RTL-SDR at 2.4-3.2 Msps may share a hub with Wi-Fi, and the USB 3.1 fallback for a wideband SDR is unproven. Check with lsusb -t and a sustained-throughput test.
  9.
    - **Problem:** Sustained UFS write for raw IQ is unmeasured by the community, and the Kioxia fix is vendor-kernel only.
    - **Evidence:** Only Radxa's dd figures exist (557 MB/s Kioxia, 388 MB/s Samsung). During the fault Kioxia gave about 60 MB/s. The PA_TACTIVATE quirk exists only in radxa/kernel; whether Armbian or mainline has it is unknown (Dual-O's question went unanswered).
    - **Why it matters for us:** Recording 56 MHz IQ needs 250 MB/s or more sustained without stalls, and stalls can drop samples even when the average speed is fine. Run a long fio sequential-write test with fan and temperature logging, and stay on the Radxa kernel if you use the Kioxia module.
  10.
    - **Problem:** HDMI to high-resolution or high-brightness monitors.
    - **Evidence:** A Samsung G80SD (4K) fell back to 1024x768 with no reply (topic 31118). The kernel 7.0 HDMI hotplug regression is described as fixed only by unspecified later updates.
    - **Why it matters for us:** The user wants a sunlight-readable display above Full HD over HDMI, since third-party DSI panels are unproven (topic 29646 has no confirmed panel). Check the EDID of the chosen panel on the Q6A before buying.
  11.
    - **Problem:** The root cause and failure rate of Q6A DDR, boot-loop and dead-socket faults are unknown.
    - **Evidence:** Five or more DDR_ABORT reports, several reset loops and one dead NVMe socket. Staff could only offer RMA. One board failed again weeks after a service repair.
    - **Why it matters for us:** Importing into Ukraine makes an RMA slow and costly. A failure in the field cannot be fixed, and a spare board may be worth budgeting.
  12.
    - **Problem:** M.2 2230-to-2280 extension signal integrity at Gen3 on the Q6A.
    - **Evidence:** No Q6A reports. A Proxmox analogue shows a 25 cm riser causing AER errors and reset loops. The Q6A BIOS has no documented setting to force the link to Gen2.
    - **Why it matters for us:** The LimeSDR Micro needs only Gen3 x1, about 1 GB/s, but link errors under streaming could cause dropped samples. Use the shortest riser you can, and watch AER counters in dmesg.
- **Communities checked:**
  - Radxa forum (forum.radxa.com): Q6A and Q8B categories plus search.json. Reachable and the richest source.
  - Armbian forum (forum.armbian.com): Q6A, Q8B, Orange Pi 5/5 Plus/5 Max threads.
  - GitHub: geerlingguy/sbc-reviews (#85 Q6A, #108 Q8B), radxa/kernel PRs, radxa-pkg/fastrpc issues, qualcomm/fastrpc #371, rubikpi-ai org issues, SatDump issues, myriadrf/LimeSuiteNG issues and branches.
  - ThomasKaiser sbc-bench results (Results.md and raw result files for Q6A, RUBIK Pi 3, Orange Pi 5 Max, Q8B).
  - MyriadRF / Lime Discourse (discourse.myriadrf.org): LimeSDR Micro and XTRX-on-ARM threads.
  - Particle community forum (community.particle.io): Tachyon.
  - CNX Software article comments (Q6A launch article) and CNX search.
  - Hackaday article and comments (Dragon Q8B).
  - LKML archive (lkml.iu.edu): RUBIK Pi 3 DTS and PCIe thread.
  - SatNOGS community (community.libre.space): searched; no QCS6490 or RK3588 hits.
  - Ubuntu Discourse: searched; no relevant user reports for RUBIK Pi or Q6A.
  - Proxmox forum (via web search): M.2 riser AER analogue.
  - Thundercomm RUBIK Pi 3 docs (fan/thermal page).
  - Not reachable: Reddit (www.reddit.com and old.reddit.com blocked for fetch, so r/RTLSDR, r/SBCs, r/radxa and others were not read).
  - Not reachable: NVIDIA developer forum (HTTP 403), so no Jetson Orin Nano community data.
  - Not checked (budget): Qualcomm developer forums, EEVblog, BATC, AMSAT, mikrocontroller.net, RTL-SDR.com comments, Ukrainian forums, Arduino forum (VENTUNO Q has no hands-on reports yet in web search).
- **Recommendation impact:** KEEP THE RADXA DRAGON Q6A, but only with the conditions below. The community evidence does not show any alternative to be better for this build.
  
  **Why the alternatives lose:**
  - **RUBIK Pi 3:** same SoC and the same NPU and GPU rough edges.
  - **Particle Tachyon:** reboot loops and stalled NPU support, at three times the price.
  - **Dragon Q8B:** measured 20-43 W, plus a BIOS still being fixed in October 2026.
  - **RK3588 boards:** mature software and FP16 on the NPU, but the 5 V/5 A supply causes NVMe dropouts and the NPU has half the TOPS.
  - **Jetson:** no community data reachable.
  
  **Corrections to the researcher's findings:**
  - **Power input:** the Q6A is not '12 V only'. Staff say the 12 V pin accepts 3.6-16 V, and USB-C takes 12 V PD or 5 V/3 A. Do not use USB-C and the header at the same time. A full 4S pack (16.8 V) exceeds 16 V, so keep a regulated 12 V buck. Add a protection diode or MOSFET, because the header sits about 1.5 mm from the USB-C ground.
  - **UFS:** the recommended Kioxia 256 GB module caused freezes and reboots until Radxa's kernel quirk (PR #551, May 2026). Stay on a Radxa kernel that includes the fix, or use the Samsung 128 GB module (388 MB/s, still above the 250 MB/s target). Verify sustained write with a long fio run.
  - **CPU clocks:** sbc-bench confirms full clocks under Linux (2698/2391/1944 MHz) with cooling. Without active cooling the board throttles at about 90 °C. A 5 V fan from the 40-pin header is mandatory.
  - **ROCK 5T:** the second slot is an M-key x2. The B-key carries USB 2.0 only.
  
  **NPU plan (the biggest software risk):**
  - The HTP v68 is INT8-only, and the DSP firmware is tied to QAIRT 2.42 (some users run 2.46).
  - Pin one QAIRT version, build models with the matching AI Hub or QNN version, and validate INT8 accuracy against FP32 for the modulation classifier.
  - Keep a CPU fallback and a watchdog, because of an unresolved report of the HTP stalling after about an hour.
  - Freeze the system with apt-mark hold once fastrpc_test passes.
  
  **Process:**
  - Buy from Arace or an official store, not an AliExpress third-party seller, and test the board as soon as it arrives. DDR and boot-loop DOAs are recurring.
  - Pin the kernel (6.18.2-x-qcom or a known-good later one) to avoid the HDMI and Wi-Fi breakage seen with 7.0.
  - Make "LimeSDR Micro enumerates and streams over the Q6A M.2 slot through a short riser" the gating milestone before the rest of the build. No community report shows any non-NVMe PCIe device in this slot.
  
  **Fallback:** if INT8 accuracy or the PCIe SDR path fails, an RK3588 board is the most viable alternative. It has FP16 on the NPU and a Gen3 x4 M.2 slot, at the cost of a 5.1 V/5 A power design and half the TOPS.

## Власні виправлення (`fixes`)

_Агент цього етапу ще працює (run `wf_88090a59-878`)._

