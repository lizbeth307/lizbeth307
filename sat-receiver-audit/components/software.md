# Software: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_e49d4f53-8d4`_

- **Component:** Software stack on the Radxa Dragon Q6A (QCS6490): OS/kernel, LimeSDR Micro PCIe driver, SDR apps, GPU waterfall, NPU classifier
- **Current pick assessment:** The stack can work, but it is not plug-and-play. Most of the SDR userspace installs from apt. The SDR driver and SatDump have to be built from source. The NPU is the most fragile part and should be treated as an accelerator you add later, not something the device depends on.
  
  1) Kernel and OS. Radxa OS r2 (Ubuntu 24.04 noble, systemd-boot) ships kernel 6.18.2-4-qcom. Radxa's qcs6490-noble apt repo (dated 24 Sep 2026) now carries linux-image and linux-headers-radxa-dragon-q6a 7.0.11-7, so matching headers exist for DKMS. Armbian "current" is 6.18.2. Mainline 7.3-rc7 (Oct 2026): the Q6A device tree enables the GPU, PCIe0/1, ADSP/CDSP, eMMC/SD, USB2 and Venus, but not UFS, USB3 or HDMI/DP. The HDMI/USB3 patches posted in May 2026 are not merged. A mainline-only kernel is therefore not viable for a build that needs UFS and a display.
  - Firmware gotcha: the new BIOS 260916 is marked "Not compatible with Radxa OS (Ubuntu 24)". Stay on 260120 if you run Ubuntu 24.04.
  
  2) LimeSDR Micro. It does NOT use limepcie. It uses a separate out-of-tree module, la9310_limesdr, which exists only on the LimeSuiteNG branches limesdr-micro and limesdr-micro-staging (last commit 16 Oct 2026). The develop branch (2 Oct 2026) has no LimeSDR_Micro board code.
  - What the driver needs: exactly 8 plain MSI vectors (it fails with fewer). It uses streaming DMA: a 4 MiB kzalloc buffer with dma_map_single, IOVAs written into the LA9310 iATU windows, dma_sync ioctls, and dma_mmap_coherent to user space. It ships a DKMS config.
  - What Q6A pcie1 offers (mainline kodiak.dtsi): 8 DWC MSI lines (msi0-msi7), dma-coherent, and an SMMU iommu-map. On paper the requirements are met and the IOMMU path is correct.
  - Tested hosts: Lime demoed it on ARM64 (Raspberry Pi CM5 in a uConsole, Gqrx at 40 Msps), and NXP targets i.MX8MP/i.MX95. No Qualcomm host has been shown.
  - Other limits in the host code: the link is forced to I16 (no 12-bit packing), and the minimum sample rate is 7 Msps.
  - Purchase: the price is now $249 (Basic) and new orders ship 15 Dec 2026.
  
  3) Decoders and viewers.
  - SatDump: noble's archive has only 1.1.2, which is too old and has no LimeSuiteNG support. Upstream master is 2.0.0-alpha (29 Sep 2026). Its ARM64 nightly is a "Pi64" .deb built on a Raspberry Pi runner. It supports LimeSuiteNG (through the limesuiteng-legacyapi library) and SoapySDR, so build it from source.
  - SDR++: the official nightly includes sdrpp_ubuntu_noble_aarch64. That .deb is built with the legacy-LimeSuite source and without the Soapy source, so it will not see the Micro. Rebuild with -DOPT_BUILD_SOAPY_SOURCE=ON. The upstream README warns against Ubuntu's own sdrpp package.
  - apt on noble arm64: GNU Radio 3.10.9.2, VOLK 3.1.2 (NEON kernels; run volk_profile), gr-satellites 5.5.0, SoapySDR 0.8.1, Gpredict 2.3, Hamlib 4.5.5, rtl-sdr 2.0.1. The rtl-sdr 2.0.1 tag already contains the Blog V4 commits from Aug and Nov 2023. Version 2.0.3 (Aug 2026) adds V4L support and a fix for hangs on USB errors.
  
  4) GPU. Mesa 25.2.8 Turnip/freedreno from noble-updates works: Radxa measured 808 GFLOPS FP32 with vkpeak. Proprietary Adreno OpenCL (qcom-adreno-opencl 1.855.3) is in Radxa's repo. RustiCL works but is slow.
  
  5) NPU.
  - Packages: Radxa's repo has qcom-qnn-sdk-v68 (libQnnHtp, the V68 skel, libQnnTFLiteDelegate, qnn-net-run) plus fastrpc 1.0.7. Canonical's qcom-ppa has qairt-sdk 2.49 with v68 DSP binaries, but it installs them under the RB3gen2 path.
  - ONNX Runtime: Radxa documents a forked onnxruntime-qnn 1.23.2 wheel built against QAIRT 2.42.0.251225. Qualcomm's onnxruntime-qnn 2.7.0 (13 Oct 2026) now ships manylinux aarch64 wheels, but v68 support is unverified.
  - Field reports (Apr-Sep 2026): FastRPC error 0x80000600 keeps coming back, depending on the kernel, firmware and device tree. Fixes so far are a device-tree overlay that adds the missing DMA memory region, matched firmware (CDSP c4-00004 and ADSP c9-00028, upstreamed in linux-msm/hexagon-dsp-binaries on 26 Jan 2026), and pinning matching SDK versions. Once fixed, users report working HTP vision models, Llama 3.2 1B via Genie, and Qwen3.5 via the ONNX Runtime QNN path.
  - A small modulation-classifier CNN runs in real time on the CPU anyway: ULCNN (9,751 parameters) takes 0.775 ms per sample on a Raspberry Pi.
- **Alternatives:**
  1.
    - **Name:** Radxa OS r2 (Ubuntu 24.04) + Radxa qcs6490-noble apt repo (baseline)
    - **Key specs:** Kernel 6.18.2-4-qcom, optionally 7.0.11-7-qcom with headers from the repo. Mesa 25.2.8 Turnip. fastrpc 1.0.7, qcom-qnn-sdk-v68, qcom-adreno-opencl 1.855.3. UFS supported by the Radxa kernel (Radxa lists dd writes of 388 MB/s for the Samsung 128 GB module and 557 MB/s for the Kioxia 256 GB module).
    - **Price:** $0
    - **Pros:** Vendor kernel with UFS, HDMI and DSI. Kernel headers are available for DKMS. NPU, OpenCL and Vulkan packages install with apt. It is the reference platform for Radxa's docs.
    - **Cons:** NPU needs per-version fixes. A community image author cites Radxa docs warning that HDMI breaks after a plain apt upgrade. BIOS 260916 is incompatible with this image. Kernel churn: 7.0.11-5 had CDSP/VPU regressions.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/download
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/main/binary-arm64/Packages.gz
      - https://forum.radxa.com/t/non-functional-npu-support-on-dragon-q6a-qcs6490-under-ubuntu-24-04-noble/30699
      - https://dl.radxa.com/dragon/q6a/images/dragon-q6a-bios-changelog.md
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
      - https://docs.radxa.com/en/dragon/q6a/system-config/vulkan
    - **Availability:** Available now (rsdk-r2). The repo was updated 24 Sep 2026.
    - **Q6a compatibility:** Native. Use BIOS 260120.
  2.
    - **Name:** Armbian 26.x for Dragon Q6A (Ubuntu 24.04/26.04, 'current' 6.18.2; edge mainline 7.1 PR open)
    - **Key specs:** Radxa-patched 6.18.2. GNOME, XFCE and minimal builds (Aug 2026). Can be flashed to UFS with edl-ng. Needs the latest UEFI.
    - **Price:** $0
    - **Pros:** Cleaner base, armbian-config, community NPU install scripts. A working QNN/HTP setup was reported on 26.5.1.
    - **Cons:** The NPU only works after transplanting the RadxaOS firmware and userspace. Users call it fragile, and one saw speed regress after an update. Armbian shipped a mismatched CDSP firmware (c3-00098). Edge 7.x lacks UFS and HDMI.
    - **Sources:**
      - https://www.armbian.com/boards/radxa-dragon-q6a
      - https://docs.radxa.com/en/dragon/q6a/other-system/armbian
      - https://github.com/armbian/build/pull/10162
      - https://forum.radxa.com/t/finally-got-llama-3-2-1b-running-on-the-dragon-q6a-npu-armbian-ubuntu-24-04/31144
    - **Availability:** Available now
    - **Q6a compatibility:** Good on the 'current' branch. Avoid edge for this build.
  3.
    - **Name:** Community Ubuntu 26.04.1 image for Q6A (rafaelwms v1.3.0, Linux 7.2.9)
    - **Key specs:** Server and GNOME images. FastRPC and DSP firmware preinstalled, with uaccess permissions. HDMI, audio, Wi-Fi/BT and NVMe boot confirmed by the author. Newer apt packages: GNU Radio 3.10.12, gr-satellites 5.8.0, SatDump 1.2.2.
    - **Price:** $0
    - **Pros:** The NPU runtime works out of the box (Llama 3.2 1B on HTP via Genie). An apt upgrade does not break HDMI. Newer SDR packages.
    - **Cons:** Third-party image. UFS support is not documented (unverified). The QAIRT SDK is not bundled. A 7.2.3 HDMI regression shows how fast this kernel line changes.
    - **Sources:**
      - https://github.com/rafaelwms/ubuntu-26.04.1-dragon-q6a
      - https://forum.radxa.com/c/dragon/q6a/71
      - https://packages.ubuntu.com/resolute/gnuradio
    - **Availability:** Released Oct 2026 (v1.3.0)
    - **Q6a compatibility:** Boots on Q6A. UFS root plus an M.2 SDR is unverified.
  4.
    - **Name:** Mainline distro kernel (Debian or Ubuntu 26.04 generic, Linux 7.x)
    - **Key specs:** Mainline Q6A device tree: GPU, PCIe0/1, ADSP/CDSP, eMMC/SD, USB2, Venus. No UFS, no USB3, no HDMI/DP (patches posted May 2026, not merged as of 7.3-rc7).
    - **Price:** $0
    - **Pros:** Long-term the cleanest path, and out-of-tree modules build against stock headers.
    - **Cons:** Cannot use the UFS module or HDMI today, which blocks this design.
    - **Sources:**
      - https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://lore.gitlab.freedesktop.org/drm-ai-reviews/20260522060645.4399-1-graham.oconnor@gmail.com/
    - **Availability:** Available, but incomplete
    - **Q6a compatibility:** Not suitable before UFS and display land upstream.
  5.
    - **Name:** Canonical/Qualcomm IoT PPA: qairt-sdk 2.49 + qcom-fastrpc 1.0.15 + tensorflow-lite-qcom 2.16.1
    - **Key specs:** arm64 debs for noble. qairt-dsp-binaries includes Hexagon v68 (QCS6490). Packages: qairt-libs, qairt-tools, qairt-headers. Built 15 Sep 2026.
    - **Price:** $0
    - **Pros:** Newest packaged QAIRT, with QNN, SNPE and Genie, installable by apt.
    - **Cons:** The v68 skels go to /usr/share/qcom/qcm6490/Thundercomm/RB3gen2/dsp/cdsp, so on Q6A they need a symlink or ADSP_LIBRARY_PATH. The host SDK version must match exactly. It mixes badly with Radxa's fastrpc 1.0.7.
    - **Sources:**
      - https://launchpad.net/~ubuntu-qcom-iot/+archive/ubuntu/qcom-ppa
      - https://forum.radxa.com/t/radxa-dragon-q6a-dragon-q6a-ubuntu-24-04-qnn-htp-backend-fails-with-qnn-open-0x80000600/30850
    - **Availability:** Available
    - **Q6a compatibility:** Works with manual path fixes. Not officially supported.
  6.
    - **Name:** onnxruntime-qnn 2.7.0 (PyPI, Qualcomm plugin EP)
    - **Key specs:** manylinux_2_34 aarch64 wheels for CPython 3.11-3.14 (Ubuntu 24.04 has glibc 2.39). Released 13 Oct 2026.
    - **Price:** $0
    - **Pros:** Official pip install, no fork. The same ONNX model can fall back to the CPU EP.
    - **Cons:** Whether it supports HTP v68 (QCS6490) and which QAIRT it bundles are not stated (unverified). Radxa still documents a forked 1.23.2 wheel built against QAIRT 2.42.0.251225.
    - **Sources:**
      - https://pypi.org/project/onnxruntime-qnn/
      - https://docs.radxa.com/en/dragon/q6a/app-dev/npu-dev/qnn-onnxrt-execution-provider
    - **Availability:** Available
    - **Q6a compatibility:** Uncertain, test first
  7.
    - **Name:** CPU or GPU inference fallback: ONNX Runtime CPU or LiteRT XNNPACK; LiteRT GPU delegate (Adreno OpenCL) or ncnn-Vulkan
    - **Key specs:** 4x A78 cores. Turnip delivers 808 GFLOPS FP32 and 1581 GFLOPS FP16 (vkpeak). A 10k-200k parameter CNN takes about 1 ms or less per 128-1024-sample IQ window.
    - **Price:** $0
    - **Pros:** No FastRPC or firmware dependency, deterministic, and the same ONNX file works everywhere. Easily real-time for one classifier stream.
    - **Cons:** Takes CPU from the DSP chain at 56 Msps. Leaves the NPU, which the user wants, idle.
    - **Sources:**
      - https://arxiv.org/pdf/2208.04659
      - https://docs.radxa.com/en/dragon/q6a/system-config/vulkan
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/main/binary-arm64/Packages.gz
    - **Availability:** Available
    - **Q6a compatibility:** Full
  8.
    - **Name:** CyberEther v1.15.0 (GPU spectrum and waterfall)
    - **Key specs:** Vulkan rendering, Linux aarch64 tarball/AppImage builds, SoapySDR source block, ONNX Runtime Infer block (CPU, CoreML or TensorRT providers), 3D waterfall. Released 17 Oct 2026.
    - **Price:** $0
    - **Pros:** Draws a 56-100 MHz waterfall on the Adreno through Turnip instead of the CPU. Visualization and the classifier can run in one flowgraph.
    - **Cons:** Has no QNN execution provider (needs a patch or CPU EP). Not validated on Turnip/A643. It is a viewer and DSP framework, not a decoder.
    - **Sources:**
      - https://github.com/luigifcruz/CyberEther
      - https://github.com/luigifcruz/CyberEther/releases/tag/v1.13.0
    - **Availability:** Available
    - **Q6a compatibility:** Likely (aarch64 plus Vulkan 1.3). Unverified on Q6A.
  9.
    - **Name:** Hardware analog: Raspberry Pi 5 16GB + AI HAT+ 26 TOPS (Hailo-8)
    - **Key specs:** BCM2712 (4x A76), one PCIe lane (Gen2, Gen3 unofficial). Hailo-8 rated 26 TOPS.
    - **Price:** Pi 5 16GB about $220-300 after 2026 RAM price hikes, plus AI HAT+ $110-132
    - **Pros:** Most mature software. The LimeSDR Micro has been shown on a CM5 (Gqrx at 40 Msps). Hailo has a stable Linux SDK.
    - **Cons:** Costs more than the Q6A. The SDR and NPU must share one PCIe lane through a switch HAT. Weaker CPU and GPU.
    - **Sources:**
      - https://www.tomshardware.com/raspberry-pi/component-shortages-drive-raspberry-pi-prices-up-by-up-to-23-percent-escalating-lpddr4-lpddr5-costs-trigger-the-third-price-hike-of-the-year
      - https://www.jeffgeerling.com/blog/2026/dram-pricing-is-killing-the-hobbyist-sbc-market/
      - https://www.raspberrypi.com/news/raspberry-pi-ai-hat/
      - https://www.crowdsupply.com/lime-micro/limesdr-micro/updates/thanks-and-uconsole-gqrx-demo
    - **Availability:** In stock widely (EU and Ukraine resellers)
    - **Q6a compatibility:** Replaces the Q6A. Not recommended given the user's NPU/Q6A decision.
  10.
    - **Name:** Hardware analog: Thundercomm RUBIK Pi 3 (same QCS6490)
    - **Key specs:** 8 GB LPDDR4X, 128 GB UFS 2.2, M.2 M-key PCIe 3.0 x2, 2x USB 3.0, 100x75x25 mm. Qualcomm Linux, Debian 13 and Ubuntu.
    - **Price:** $299 now ($99 listing out of stock)
    - **Pros:** Same SoC with a Qualcomm-maintained board and an upstream DSP firmware path. The QNN/TFLite workflow is documented.
    - **Cons:** Costs more, has less RAM, a larger board, and the same QNN fragility.
    - **Sources:**
      - https://www.thundercomm.com/product/rubik-pi/
      - https://www.thundercomm.com/rubik-pi-3/en/docs/rubik-pi-3-user-manual/1.1.1/ai-developer-workflow
    - **Availability:** Limited (8 in stock at $299)
    - **Q6a compatibility:** Replaces the Q6A. Not better value.
- **Recommended:**
  - **Name:** Pinned Radxa OS r2 (Ubuntu 24.04) on BIOS 260120 + Radxa qcs6490-noble repo; source-built LimeSuiteNG (limesdr-micro-staging, la9310_limesdr via DKMS, SoapyLMS, legacy API) + SatDump 2.0 from source + SDR++ rebuilt with Soapy + apt GNU Radio/gr-satellites/Gpredict + CyberEther for the GPU waterfall; classifier CPU-first in ONNX Runtime, NPU (QNN HTP v68 context binary or LiteRT + libQnnTFLiteDelegate) as an optional accelerator
  - **Why:** It is the only image that combines UFS, HDMI/DSI, kernel headers for the out-of-tree LA9310 module, and apt-packaged NPU (qcom-qnn-sdk-v68, fastrpc), OpenCL and Vulkan support. Every SDR application has an ARM64 build path. The Q6A's pcie1 meets the driver's 8-MSI, coherent-DMA and SMMU requirements, at least on paper. Keeping the classifier CPU-first means the device works even when FastRPC breaks after an update.
  - **Price:** $0. The QAIRT SDK is free with a Qualcomm account. The model-conversion host must be an x86-64 machine running Ubuntu 22.04.
  - **Sources:**
    - https://docs.radxa.com/en/dragon/q6a/download
    - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/main/binary-arm64/Packages.gz
    - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro-staging/drivers/linux/la9310_limesdr
    - https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/qcom/kodiak.dtsi
    - https://github.com/SatDump/SatDump/blob/master/plugins/sdr_sources/limesdr_sdr_support/CMakeLists.txt
    - https://github.com/AlexandreRouma/SDRPlusPlus/blob/master/.github/workflows/build_all.yml
    - https://docs.radxa.com/en/dragon/q6a/app-dev/npu-dev/qairt-install
    - https://docs.radxa.com/en/dragon/q6a/app-dev/npu-dev/tflite-delegate-demo
    - https://github.com/luigifcruz/CyberEther
- **Budget option:**
  - **Name:** Same Radxa OS r2, apt-only, starting with the RTL-SDR: GNU Radio 3.10.9 + gr-satellites 5.5 + SoapySDR 0.8.1 + Gpredict 2.3 + rtl-sdr 2.0.1 (or 2.0.3 from source) + the SDR++ noble aarch64 nightly .deb + ONNX Runtime CPU classifier; add the LimeSDR and NPU later
  - **Why:** It covers the 137/145/435 MHz targets and the 1.7 GHz targets (via the L-band LNA) with the RTL-SDR, using no fragile pieces: no out-of-tree kernel module, no FastRPC, no SDK version pinning. The LimeSDR Micro does not ship until 15 Dec 2026 for new orders anyway. The CPU handles a small CNN well under 1 ms per window.
  - **Price:** $0
- **Risks:**
  - The LimeSDR Micro driver (la9310_limesdr) and its board support exist only on unmerged branches, with commits as late as 16 Oct 2026. The API and firmware may change. Nobody has published a test on a Qualcomm host; the known ARM64 hosts are RPi CM5 and NXP i.MX8MP/i.MX95.
  - The driver aborts unless it gets exactly 8 MSI vectors. Mainline pcie1 provides msi0-msi7, but the Radxa vendor device tree may differ. Check dmesg for '8 MSI successfully created'.
  - SMMU context faults or DMA problems are possible. The driver uses streaming DMA through dma_map_single, which is IOMMU-safe in principle. Mitigations if faults appear: iommu.passthrough=1, or forcing the link to Gen2 (max-link-speed=2), which still gives about 500 MB/s, more than the 246 MB/s needed.
  - The 4 MiB contiguous kzalloc IQ buffer is the kmalloc maximum with 4K pages and can fail on a fragmented system. Load the module early at boot.
  - The 2230-to-2280 M.2 extension may cause Gen3 link errors (check AER messages in dmesg). Mitigation: force Gen2.
  - The NPU fails intermittently: FastRPC 0x80000600/0x80000406 errors, missing DMA memory-region in the device tree, DSP firmware and skel mismatches, and host/runtime QAIRT version mismatches (for example, AI Hub artifacts built with 2.45 fail on a 2.42 runtime). One user reported only 2 MB of the 8 MB VTCM usable.
  - Kernel and firmware churn: BIOS 260916 is incompatible with Radxa OS on Ubuntu 24. Kernel 7.0.11-5 had CDSP and VPU regressions, and 7.2.3 broke HDMI. A community image author says a plain apt upgrade breaks HDMI on the stock image. Hold the kernel packages (apt-mark hold).
  - Mainline Linux has no Q6A UFS or HDMI support as of 7.3-rc7. The build is tied to Radxa's vendor kernel.
  - The LimeSDR Micro host code forces 16-bit samples on the link and has a 7 Msps minimum. Narrowband reception means decimating on the CPU. 160 Msps (640 MB/s) exceeds sustained UFS write speed (388-557 MB/s by Radxa's dd test), so bursts at that rate must go to RAM first.
  - Packaging traps: SDR++'s nightly deb lacks the Soapy source and its LimeSDR module links legacy LimeSuite, which cannot see the Micro. Legacy LimeSuite (Ubuntu 23.11 package) and LimeSuiteNG may clash over the SoapySDR LMS7 plugin. SatDump 2.0-alpha had a config-path bug on 24.04 (launch it from /usr/share/satdump).
  - Live 56 MHz processing in SDR++ or GNU Radio on 4x A78 cores is unbenchmarked (no published VOLK NEON or SatDump-on-Q6A numbers). Profile with volk_profile and expect to offload the waterfall to the GPU.
  - Prices: the Q6A 16GB launch price of $124.29 is gone. Current listings run about $180-250 (unverified). The LimeSDR Micro Basic is now $249, not $199.
- **Integration notes:**
  - 1. Flash Radxa OS r2 (the 4096-byte-sector UFS build) with edl-ng and keep BIOS 260120. Add the Radxa qcs6490-noble repo. Choose one kernel (6.18.2-4-qcom, or 7.0.11-7-qcom after testing), install the matching linux-headers-radxa-dragon-q6a, then apt-mark hold the kernel, firmware and fastrpc packages.
  - 2. LimeSuiteNG: git clone -b limesdr-micro-staging https://github.com/myriadrf/LimeSuiteNG. Build with -DBUILD_DRIVERS=ON and the Soapy plugin, the legacy API (limesuiteng-legacyapi) and gr-limesuiteng enabled. Install la9310_limesdr through DKMS. Verify: lspci, then dmesg for '8 MSI successfully created' and SMMU faults, then limeDevice, then a sustained-rate test at 61.44 Msps.
  - 3. Do not install Ubuntu's legacy limesuite or soapysdr-module-lms7 23.11 packages next to LimeSuiteNG. Check with SoapySDRUtil --find.
  - 4. SatDump: build master (2.0.0-alpha) from source with libvolk-dev, libfftw3-dev, libglfw3-dev, libzstd-dev, libhdf5-dev and the LimeSuiteNG legacy API. Optionally add OpenCL through qcom-adreno-opencl. Use LimeSDR/Soapy for HRPT/S-band and the RTL-SDR for LRPT/APT.
  - 5. SDR++: build from source with -DOPT_BUILD_SOAPY_SOURCE=ON (needed for the LimeSDR Micro) plus the RTL-SDR source. The nightly noble aarch64 deb is fine for RTL-SDR-only use.
  - 6. apt: gnuradio 3.10.9.2, gr-satellites 5.5.0, soapysdr-tools 0.8.1, gpredict 2.3, libhamlib-utils 4.5.5, librtlsdr 2.0.1 (has V4 support; build osmocom 2.0.3 if USB hangs appear). Blacklist dvb_usb_rtl28xxu and run volk_profile once.
  - 7. GPU: install mesa-vulkan-drivers (Turnip, 25.2.8) and check vulkaninfo for 'Adreno 643'. Install qcom-adreno-opencl for OpenCL. Run CyberEther (aarch64 build) with a SoapySDR source for the wide waterfall. Use cage or weston as a kiosk compositor for the handheld UI.
  - 8. Classifier model: train in PyTorch on a PC (RadioML 2018.01A plus your own recordings). Use a Conv2d network with 1xK kernels, BatchNorm, ReLU and global average pooling, and no LSTM (the HTP is happiest with static-shape CNNs). Export to ONNX with a fixed input shape, for example [32,1,2,1024].
  - 9. Classifier on CPU (default): pip install onnxruntime in a venv and run the classifier off the GNU Radio or CyberEther stream at a few windows per second.
  - 10. Classifier on the NPU (optional): on an x86 machine running Ubuntu 22.04 with QAIRT 2.42.0.251225 (Radxa-pinned), run qairt-converter, then qairt-quantizer with about 200 calibration windows (w8a8), then qnn-context-binary-generator for dsp_arch v68 / soc_id 35. On the device, install qcom-qnn-sdk-v68 and fastrpc, confirm fastrpc_test -a v68 passes, then run qnn-net-run or LiteRT with load_delegate('libQnnTFLiteDelegate.so', backend htp). Keep the host SDK version identical to the device libraries.
  - 11. If FastRPC fails with 0x80000600: check dmesg for 'no reserved DMA memory for FASTRPC'. Apply the device-tree overlay that adds memory-region and shared-dma-pool, use CDSP c4-00004 and ADSP c9-00028 from linux-msm/hexagon-dsp-binaries (qcs6490/radxa/dragon-q6a), and add a udev rule (or uaccess) for /dev/fastrpc-* and /dev/dma_heap/system.
  - 12. Pointing aid: Gpredict for passes, plus a small Python app (skyfield + BNO085 + GNSS over gpsd) drawing azimuth/elevation on screen. SatDump's tracking app and rotctld can share the TLEs.
  - 13. Recording: write raw IQ (cs16) to UFS at up to about 60 Msps single channel. For 160 Msps bursts, record to a RAM ring buffer (about 12 GB is roughly 19 s), or use SatDump's cs8 or compressed ziq formats.
- **Double duty opportunities:**
  - Adreno GPU: Turnip Vulkan and the proprietary OpenCL (qcom-adreno-opencl) can run the waterfall (CyberEther), SatDump's OpenCL projections, and a GPU fallback for the classifier (LiteRT GPU delegate or ncnn-Vulkan). The device then never depends on the NPU.
  - CyberEther combines a SoapySDR source, the GPU waterfall and an ONNX Runtime Infer block, so one application replaces a separate viewer and a separate classifier daemon.
  - The CPU ONNX model doubles as the NPU model: the same ONNX file is the source for the QNN context binary, so there is no separate training or export pipeline.
  - The LimeSDR Micro's LA9310 VSPA DSP (up to 80 GFLOPS) could later do on-card decimation or FFT and cut PCIe, CPU and storage load (the firmware toolchain went public in May 2026). This is future work, not available in the current host code.
  - The LimeSDR Micro GNSS variant ($299) has a GNSS module that could replace the separate u-blox M10. But GPSDO and NMEA/PPS output to the host are not implemented in the LimeSuiteNG Micro branch, so this is not yet a real saving.
  - Gpredict, Hamlib's rotctld and SatDump's tracker share the TLE and pass data, which feed the BNO085-based on-screen pointing aid without extra hardware.
- **Confidence:** medium

## Форуми та досвід спільноти (`forums`)

_Run `wf_e49d4f53-8d4`_

- **Component:** Software stack feasibility on the Radxa Dragon Q6A (QCS6490): OS/kernel/firmware, LimeSDR Micro la9310 PCIe driver, SDR apps (SatDump, SDR++, GNU Radio/VOLK, gr-satellites, SoapySDR, Gpredict/Hamlib, librtlsdr), GPU waterfall (Turnip/CyberEther), NPU classifier (QAIRT/QNN, LiteRT delegate, ONNX Runtime QNN EP), CPU fallback
- **Experiences:**
  1.
    - **Product:** Radxa OS r2 (Ubuntu 24.04), kernel 6.18.2-4-qcom, NPU/FastRPC
    - **Source url:** https://forum.radxa.com/t/dragon-q6a-fastrpc-npu-fails-fastrpc-ioctl-init-create-returns-0x80000600-on-cdsp/31078
    - **Community:** Radxa forum
    - **What they built:** QNN/HTP/TFLite-delegate inference on the Q6A NPU
    - **Problems:**
      - fastrpc_test -a v68 fails with 0x80000600 'Unable to create FastRPC session on domain 3'
      - dmesg: 'no reserved DMA memory for FASTRPC' on both ADSP and CDSP fastrpc nodes
      - dpkg -V radxa-firmware-qcs6490 showed modified fastrpc_shell_3 / fastrpc_shell_unsigned_3 in /usr/lib/dsp/cdsp/
      - Boot path is systemd-boot under /boot/efi, so extlinux.conf edits do nothing
    - **Fixes:**
      - DTBO adding memory-region to the fastrpc nodes under remoteproc@a300000 and remoteproc@3700000, pointing to adsp-rpc-remote-heap made compatible with shared-dma-pool
      - Install the overlay in the active EFI dtbo folder and reference it in /boot/efi/loader/entries/RadxaOS-6.18.2-4-qcom.conf
      - apt download the exact radxa-firmware-qcs6490 0.2.29, extract it with dpkg-deb, and restore the mismatched DSP payload files until dpkg -V is clean
      - Do not run apt upgrade/autoremove afterwards
    - **Outcome:** User (okay, 9 Jul 2026): fastrpc_test passes all tests. Leandro (22 Jul) reports a model runs, but only ~2 MB of the 8 MB VTCM is usable. GitHub issue radxa-pkg/fastrpc#18 is still open, with no maintainer reply.
  2.
    - **Product:** Radxa OS r2, kernel 7.0.11-5-qcom, radxa-firmware 0.2.41, fastrpc 1.0.7
    - **Source url:** https://forum.radxa.com/t/cdsp-fastrpc-session-still-fails-0x80000600-remotectl1-domains-not-supported-after-fixing-the-missing-memory-region-r2-ubuntu-24-04-kernel-7-0-11-5/31391
    - **Community:** Radxa forum
    - **Problems:**
      - 0x80000600 on CDSP after upgrading to 7.0.11
      - After the memory-region overlay was applied, cdsprpcd logs 'remotectl1 domains not supported for domain 3', which suggests the userspace daemon does not match the DSP shell/firmware
      - Bug in rsetup: update_entry_overlays in /usr/lib/rsetup/cli/edk2-menu.sh calls an undefined get_product_id, so the loader entry picks another board's DTB (the first alphabetically)
    - **Fixes:**
      - shared-dma-pool memory-region overlay (dtc -@ -I dts -O dtb, placed in /boot/efi/RadxaOS/<kernel>/dtbo/, devicetree-overlay line in the systemd-boot entry)
      - Suggested diagnostics: strings on fastrpc_shell_unsigned_3 and cdsp.mbn to compare CDSP.HT versions, and dpkg -S to find the owning packages
    - **Outcome:** Unresolved on Radxa OS. The poster abandoned Radxa OS for Armbian (8 Sep 2026). Radxa staff did not respond.
  3.
    - **Product:** Armbian 26.2.4 (6.18.2-current-qcs6490) + QAIRT 2.46 + ONNX Runtime QNN EP
    - **Source url:** https://forum.radxa.com/t/radxa-dragon-q6a-dragon-q6a-ubuntu-24-04-qnn-htp-backend-fails-with-qnn-open-0x80000600/30850
    - **Community:** Radxa forum
    - **Problems:**
      - DspTransport.openSession qnn_open failed 0x80000600 / 0x80000406, 'Failed to load skel'
      - libc++.so.1 missing on the DSP side; host runtime 2.46 vs DSP skel 2.42 mismatch
      - HTP described as 'very fragile, breaking sometimes'
      - Some ORT workloads partly fall back to CPU; all LLM workloads run on CPU
    - **Fixes:**
      - Copy the matching V2.46 libQnnHtpV68Skel.so to /usr/lib/rfsa/adsp/cdsp/
      - Symlink libc++.so.1 and libc++abi.so.1 to /usr/share/qcom/qcs6490/radxa/dragon-q6a/dsp/cdsp/
      - Replace adsp.mbn/cdsp.mbn with matching versions (back them up first)
      - Add /usr/lib/rfsa/adsp/cdsp/ to ADSP_LIBRARY_PATH and LD_LIBRARY_PATH, then restart the CDSP remoteproc
    - **Outcome:** User-reported working: fastrpc_test 3/3, and qnn-net-run plus ORT QNN EP run vision models on HTP. Radxa did not confirm the fix.
  4.
    - **Product:** Armbian 26.5.1 + Radxa r2 DSP firmware (CDSP c4-00004, ADSP c9-00028) for an Immich ML port
    - **Source url:** https://forum.radxa.com/t/dragon-q6a-qnn-htp-pipeline-working-but-int8-only-firmware-blocks-real-ml-workloads/31217
    - **Community:** Radxa forum + GitHub (immich discussion #25112)
    - **What they built:** ArcFace and CLIP ViT-SO400M on the Hexagon v68 HTP
    - **Problems:**
      - DSP rejects non-INT8 graphs: 'The SocModel doesn't support FP16'
      - ArcFace in INT8 drops to ~51% LFW accuracy, blamed on pre-activation BatchNorm
      - CLIP embeddings collapse in INT8 (cosine similarity 0.99+ instead of 0.70-0.91)
      - Firmware supports only QNN interface 2.32.0 (QAIRT 2.42): QAIRT 2.46+ fails with QNN_DEVICE_ERROR_INVALID_CONFIG
      - The official onnxruntime-qnn plugin needs QAIRT 2.48.40, and per-channel INT8 needs ORT 1.24+/QAIRT 2.45+
    - **Fixes:**
      - Matched firmware and userspace set: extract cdsp.mbn/adsp.mbn from the Radxa r2 rootfs, install libcdsprpc and cdsprpcd/adsprpcd, the /usr/lib/dsp/cdsp/ tree, and a udev rule giving /dev/fastrpc-* and /dev/dma_heap/* to group fastrpc with mode 0660 (community script vladisUl/npu_runtime_armbian)
    - **Outcome:** The pipeline runs, but the author calls it not production-ready because of the INT8-only limit. Radxa gave no answer on FP16 or newer firmware (22 Jul 2026). Also reported: https://github.com/immich-app/immich/discussions/25112
  5.
    - **Product:** Radxa OS r2 6.18.2-4 with fastrpc 1.0.6-3 listener libs
    - **Source url:** https://forum.radxa.com/t/non-functional-npu-support-on-dragon-q6a-qcs6490-under-ubuntu-24-04-noble/30699
    - **Community:** Radxa forum
    - **Problems:**
      - /dev/fastrpc* missing on some fresh r2 installs; 'Direct firmware load failed with error -2'
      - DSPs do not auto-boot
      - Leaving the DSPs running hung the board twice, and one hang needed fsck
      - radxa-firmware-qcs6490 0.2.38 depends on firmware-qcom-audioreach, which had no install candidate
      - One user returned the board and bought a Raspberry Pi 5 + AI Kit
    - **Fixes:**
      - echo start > /sys/class/remoteproc/remoteprocN/state
      - Upgrade fastrpc/libcdsprpc1 so libadsp/libcdsp-default-listener1 get pulled in
      - Radxa says audioreach-topology is in the qcs6490-noble repo
    - **Outcome:** No official root cause. strongtz (Radxa) disputes that CDSP needs reserved DMA memory and suspects extra packages overwrote the firmware.
  6.
    - **Product:** Radxa OS R2, NVMe boot, NPU
    - **Source url:** https://forum.radxa.com/t/collecting-q6a-npu-fastrpc-issues/30321
    - **Community:** Radxa forum
    - **Problems:**
      - 0x00000072 'createUnsignedPD ... not supported by HTP'
      - adsprpcd crash-loops
      - Firmware load -2 at early boot when the root filesystem is on NVMe
    - **Fixes:**
      - initramfs hook that includes adsp.mbn and cdsp.mbn so the DSP firmware loads early
      - udev rule giving fastrpc-* and the DMA heap mode 0666
      - Create the output_bin directory before running qnn-net-run
      - Radxa staff: keep BIOS 6.0.260120 (older SPI firmware tied to the early-boot firmware load failure)
    - **Outcome:** User-reported working. Radxa had said the R2 image 'resolved' the NPU issues (Feb 2026), but failures continued afterwards.
  7.
    - **Product:** QAIRT 2.37.1 (aarch64-ubuntu-gcc9.4 build) + Ubuntu apt libqnn1 2.40, kernel 6.18.2-2
    - **Source url:** https://forum.radxa.com/t/qnn-npu-error/30287
    - **Community:** Radxa forum
    - **Problems:**
      - qtld-net-run HTP fails with error 14001, qnn_open 0x80000406, skel load failure
      - The same workflow worked on another QCS6490 device
    - **Fixes:**
      - Radxa (Morgan): remove the non-Radxa QNN/SNPE apt packages
      - sudo apt install fastrpc fastrpc-dev libcdsprpc1 radxa-firmware-qcs6490
      - Use the aarch64-oe-linux-gcc11.2 QAIRT build, not aarch64-ubuntu-gcc9.4
      - Run the Radxa NPU Quick Validation first
    - **Outcome:** Staff guidance only; the user did not confirm the result.
  8.
    - **Product:** Qualcomm AI Hub context binaries (QAIRT 2.45) on Q6A runtime 2.42.0.251225
    - **Source url:** https://forum.radxa.com/t/qcs6490-radxa-q6a-qairt-sdk-version-mismatch-ai-hub-artifacts-2-45-x-incompatible-with-runtime-2-42-0-251225/30908
    - **Community:** Radxa forum
    - **Problems:**
      - 'Using newer context binary on old SDK', 'Failed to create context from binary with err 0x1388'
    - **Fixes:**
      - Radxa: the context binary's SDK version must match the runtime, so specify the QNN version when compiling on AI Hub or build locally with 2.42
    - **Outcome:** No confirmation that the user succeeded. Community tools posted: onnx2qnn and QAIRT_Model_Quantization_Toolkit.
  9.
    - **Product:** QAIRT 2.49 offline flow (qairt-converter -> qairt-quantizer -> qnn-net-run), YOLOv8n
    - **Source url:** https://forum.radxa.com/t/issues-running-yolov8n-with-qairt-sdk-2-49-on-radxa-dragon-q6a-qcs6490/31462
    - **Community:** Radxa forum
    - **Problems:**
      - UINT8-quantized output is mostly zeros and boxes are nonsense, on both the board and the PC
      - The FP16 conversion path fails validation
    - **Fixes:**
      - Splitting the boxes/scores outputs did not help
    - **Outcome:** Unanswered (Sep 2026).
  10.
    - **Product:** YOLOv8n context binary for Q6A via AI Hub (RB3 Gen 2 Vision Kit used as the target)
    - **Source url:** https://forum.radxa.com/t/yolov8n-context-binary-generation-for-q6a/30899
    - **Community:** Radxa forum
    - **Problems:**
      - Garbage outputs after quantization, caused by the shared output scale
      - onnxsim breaks the modified graph
      - Graph-name mismatch ('yolov8 not found')
      - NHWC vs NCHW input mixup
    - **Fixes:**
      - Split the head outputs with ONNX GraphSurgeon before quantization
      - Clear graph.value_info instead of running onnxsim
      - Upload calibration data with hub.upload_dataset
      - Use NCHW input, dequantize each output with its own scale and zero point, and match the graph name in QNNContext
    - **Outcome:** Worked by 27 May 2026, at ~20 ms vs 10-12 ms for the official binary. Published as an offline pipeline (ImRIzo/onnx2qnn).
  11.
    - **Product:** Frigate 0.17 + QAIRT 2.46.0.260424 HTP via a ZeroMQ detector (Docker)
    - **Source url:** https://forum.radxa.com/t/running-custom-frigate-with-full-npu-support-dragon-q6a/31047
    - **Community:** Radxa forum
    - **What they built:** Real-time YOLOv8n INT8 detector on the Q6A NPU
    - **Problems:**
      - Container needs privileged mode, /dev/fastrpc-cdsp and /dev/ion, and the firmware copied in
      - Frigate's zmq detector config validation and a None model path crash
    - **Fixes:**
      - Patch zmq_ipc.py at build time; set ADSP paths in the compose environment
    - **Outcome:** ~10 ms per inference, 0.2% CPU. No long-run stability data. This contradicts the 'QAIRT 2.46+ fails' report, so results evidently depend on the firmware/skel set.
  12.
    - **Product:** TFLite + QNN delegate (ai-engine-direct-helper samples), int8 models
    - **Source url:** https://forum.radxa.com/t/npu-htp-usage-in-radxa-dragon-q6a/29949
    - **Community:** Radxa forum
    - **Problems:**
      - Inference on HTP works for about an hour, then hangs after 'htp initialized'
      - The log also shows qnn_open failed and 'Restored original execution plan after delegate application failure'
    - **Fixes:**
      - Radxa only asked the user to run the NPU Quick Validation
    - **Outcome:** No root cause or fix.
  13.
    - **Product:** Radxa image after a system upgrade (6.17 kernel era)
    - **Source url:** https://forum.radxa.com/t/npu-not-starting-on-dragon-q6a-qcs6490/30397
    - **Community:** Radxa forum
    - **Problems:**
      - NPU samples and the TFLite delegate stop working after apt upgrade: 0x80000600, skel error 1002, 'Power config id either NULL or invalid'
    - **Fixes:**
      - Radxa: a known bug to be fixed in the next image; reinstall the OS or apply the adsp.mbn -2 workaround thread
    - **Outcome:** Fixed only by reflashing or by a later image.
  14.
    - **Product:** Q6A + QAIRT Llama 3.2 1B (kernel 6.17.1-4) and aic8800-usb-dkms
    - **Source url:** https://forum.radxa.com/t/report-dragon-q6a-experience-npu-kernel-panics-with-llms-aic8800-driver-instability/29959
    - **Community:** Radxa forum
    - **Problems:**
      - Kernel panic 'virt_to_cache: Object is not a Slab page!' during NPU buffer allocation
      - apt upgrade repeatedly hangs while configuring aic8800-usb-dkms
    - **Fixes:**
      - Power ruled out (<10 W drawn from a 65 W PD supply); larger CMA did not help
      - sudo apt remove aic8800-usb-dkms lets the upgrade finish
    - **Outcome:** The poster concluded the RAM module was defective (no evidence given).
  15.
    - **Product:** Kioxia 256 GB UFS 3.1 module (THGJFGT1E45BAILB) on Radxa OS 6.18.2-3/-4 and SUSE MicroOS mainline 6.19
    - **Source url:** https://forum.radxa.com/t/ufs-random-reboots/30630?page=2
    - **Community:** Radxa forum
    - **Problems:**
      - Stutters, freezes and random reboots when booting from UFS; fio only ~60 MB/s
      - ufshcd-qcom: Device abort task, pa_err/dl_err, HW_H8_EXIT_CNT=0 (PHY cannot exit hibern8), eh_device_reset failed -110
      - limit-hs-gear=<2> and disabling auto-hibern8 did not help
      - The Samsung module did not show the problem
    - **Fixes:**
      - Temporary: a keep-alive script that prevents hibern8 entry (24 h without errors)
      - Permanent: UFS_DEVICE_QUIRK_PA_TACTIVATE (PA_TACTIVATE=1 ms) in Radxa kernel linux-6.18.2, PR radxa/kernel#551, merged 11 May 2026
    - **Outcome:** Fixed on the Radxa 6.18.2 kernel. Post-fix: ~1.0-1.8 GB/s reads, writes ~0.5 GB/s. Upstream, Armbian-edge and MicroOS status unconfirmed; the MicroOS user called UFS 'too unstable for use' (https://forum.radxa.com/t/radxa-poe-hat-overlay-on-microos/30704).
  16.
    - **Product:** Radxa OS kernel 7.0.11-4-qcom (apt full-upgrade from 6.18.2-4)
    - **Source url:** https://forum.radxa.com/t/linux-7-0-hdmi-not-working/31304
    - **Community:** Radxa forum
    - **Problems:**
      - HDMI black after boot (card1-HDMI-A-1 'disconnected', 'Unexpected DP AUX IRQ', 'Cannot find any crtc or sizes')
      - HPD dead for the session; rebinding msm_dpu leads to a NULL dereference
      - Audio broken; phantom 50-60% CPU0 load on a headless board
      - Black screen after a warm 'sudo reboot'
    - **Fixes:**
      - Roll back to 6.18.2
      - Update the SPI firmware, then sudo poweroff plus a long power-button press instead of a warm reboot
      - Use a USB-TTL serial console for recovery
    - **Outcome:** One user reported 'HDMI works now after the latest kernel updates' (9 Sep 2026) without naming the version. No official Radxa statement.
  17.
    - **Product:** Radxa desktop image kernel update (6.18.2-1-qcom era)
    - **Source url:** https://forum.radxa.com/t/q6a-hanging-in-boot-after-update/30106
    - **Community:** Radxa forum
    - **Problems:**
      - Board hangs at boot after a kernel update; gdm fails to start; several users reflashed
    - **Fixes:**
      - apt-mark hold the kernel image and headers
      - Ctrl+Alt+F2, then: sudo mount -o remount,rw /; apt-get update --fix-missing; dpkg --configure -a; apt-get install -f; reinstall gnome-session/gnome-shell; check journalctl -u gdm.service -b
    - **Outcome:** Holding the kernel worked. No official fix.
  18.
    - **Product:** Mainline DTB vs Radxa DTB on Arch Linux ARM kernel 6.19 (NVMe on PCIe)
    - **Source url:** https://forum.radxa.com/t/catastrophic-i-o-slowdown-on-mainline-dtbs-on-6-19/30440
    - **Community:** Radxa forum
    - **Problems:**
      - Mainline DTB: NVMe ~27 MiB/s vs ~584-681 MiB/s with the Radxa DTB (~30x slower)
      - arm-smmu and msm-mdss probe failures (-110) and qupv3 firmware errors with the mainline DTB
    - **Fixes:**
      - Apply the Radxa commit 'Enable USB 3.0 and HDMI ports' (marked DNM upstream), or let UEFI supply the Radxa DTB (the default)
    - **Outcome:** Restored with the Radxa DTB. Root cause unexplained. Shows that PCIe/SMMU behaviour depends heavily on the DT.
  19.
    - **Product:** Mainline Gentoo 7.0.9 with patches
    - **Source url:** https://forum.radxa.com/t/mainline-gentoo-7-0-9-all-working/30884
    - **Community:** Radxa forum
    - **Problems:**
      - Vanilla mainline does not boot without patches; HDMI needs a bridge patch; Wi-Fi needs out-of-tree aic8800; others hit no-display installs
    - **Fixes:**
      - dts.patch, hdmi.patch, optional qcom-scm.patch; cmdline clk_ignore_unused pd_ignore_unused regulator_ignore_unused
    - **Outcome:** USB2/3, GPU (GL/Vulkan), HDMI and the NPU node work for the author. UFS and PCIe were not covered.
  20.
    - **Product:** Community Ubuntu 26.04.1 image (rafaelwms v1.3.0, Linux 7.2.9 from Armbian edge)
    - **Source url:** https://forum.radxa.com/t/ubuntu-26-04-1-lts-images-for-the-radxa-dragon-q6a-now-on-linux-7-2-9-hdmi-works-wi-fi-bt-audio-npu-apt-upgrade-safe/31574
    - **Community:** Radxa forum
    - **Problems:**
      - The author's experience of the stock image: 'HDMI dying after an apt upgrade, and no working audio'
      - Kernels 7.0 and 7.2.3 broke HDMI on the author's board
      - Tested on one board only; UFS, PCIe and USB3 not mentioned; QAIRT not bundled
    - **Fixes:**
      - Pinned 7.2.9 with DP/DPU patches; apt pin against a Firefox update loop
    - **Outcome:** HDMI, Wi-Fi/BT, audio, NPU device nodes and apt-upgrade survival confirmed by the author only.
  21.
    - **Product:** Armbian current 6.18.2 + out-of-tree aic8800-usb-dkms
    - **Source url:** https://forum.armbian.com/topic/60133-wifi-gone-on-current-version/
    - **Community:** Armbian forum
    - **Problems:**
      - After a kernel upgrade DKMS did not rebuild the module, so no Wi-Fi
      - DKMS build fails because the kernel was built with gcc 14 while Ubuntu 24.04 has gcc 13.3 (unknown flag -fmin-function-alignment=8)
    - **Fixes:**
      - sudo dpkg-reconfigure aic8800-usb-dkms, then reboot
      - Install Radxa's aic8800-firmware and aic8800-usb-dkms debs (5.0+git20260123), then depmod -a
      - Proposed: install gcc-14 so it matches the kernel compiler
    - **Outcome:** Mixed; some users fixed it, the gcc mismatch was not confirmed fixed. A direct analogue for the la9310_limesdr DKMS module.
  22.
    - **Product:** HDMI with high-resolution monitors (Radxa OS / Fedora 44)
    - **Source url:** https://forum.radxa.com/t/samsung-g80sd-can-not-negotiate-resolution-refresh-rate/31118
    - **Community:** Radxa forum
    - **Problems:**
      - 4K monitor negotiates only 1024x768@60 on the latest Radxa OS
      - Fedora: GDM/SDDM freeze on displays above 1080p, KDE works (https://forum.radxa.com/t/stock-fedora-support/30893)
      - HDMI comes from a DP-to-HDMI bridge chip, not the SoC
    - **Fixes:**
      - Force the mode manually (commands not given)
    - **Outcome:** No documented fix.
  23.
    - **Product:** Q6A cooling and power
    - **Source url:** https://forum.radxa.com/t/recommended-heatsink-fan-for-q6a/30413
    - **Community:** Radxa forum
    - **Problems:**
      - Passive homemade heatsink: CPU repeatedly hits 90 °C and throttles
      - No dedicated fan header
      - Q6A cannot be powered from the 5 V pins of the 40-pin header (Radxa staff, https://forum.radxa.com/t/powering-the-q6a-via-the-5v-pin-on-the-40-pin-header/30833)
    - **Fixes:**
      - 5 V 30 mm fan (e.g. Pi CM5 3007 fan) on the header 5 V/GND pins, copper-fin cooler with fan, or Armor Case 7056A (~40 °C idle)
    - **Outcome:** Active cooling solves throttling. Power must come in via USB-C PD (12 V) or the 12 V DC header.
  24.
    - **Product:** Q6A boards after SPI/BIOS flashing (DDR training)
    - **Source url:** https://forum.radxa.com/t/help-radxa-q6a-infinite-boot-loop-reset-every-10-seconds-hardware-issue-suspected/30749
    - **Community:** Radxa forum
    - **Problems:**
      - Reset loops every 10-20 s, RCW_TRAINING_FAIL / DRAM_DCC_FAIL / NO_MEMORY_DEVICE_DETECTED, often after an SPI NOR update (also https://forum.radxa.com/t/dragon-q6a-won-t-boot-ddr-rcw-training-fails-on-cold-boot-board-loops-into-edl/30841 and https://forum.radxa.com/t/radxa-dragon-q6a-with-ddr-problem/29863)
      - An AliExpress return produced only store bonus points, not a replacement
    - **Fixes:**
      - Radxa: treat it as hardware and get warranty via the seller; one user's issue was a faulty charger
    - **Outcome:** Several boards dead; no software recovery.
  25.
    - **Product:** Adreno 643 compute backends (rusticl, Qualcomm OpenCL, Turnip Vulkan)
    - **Source url:** https://forum.radxa.com/t/how-to-install-qualcomm-opencl-sdk-on-dragon-q6a/30787
    - **Community:** Radxa forum
    - **Problems:**
      - rusticl up to 4x slower than Qualcomm OpenCL; building Qualcomm's OpenCL SDK on the board fails
      - clpeak float GFLOPS: rusticl 553, Qualcomm 0838.5 650, Vulkan 25.2.8 748, vs Android 1247
      - llama.cpp Vulkan backend aborts, and Radxa said the Q6A 'does not support Vulkan as a GPU backend' (https://forum.radxa.com/t/vulkan-crashes-and-npu-setup-for-llm-inference-on-dragon-q6a-need-guidance/30264)
      - QNN GPU backend needs the proprietary driver, so the GPU is unusable for QNN AI (https://forum.radxa.com/t/gpu-enabled-ubuntu-image-like-the-rubik-pi/30965)
    - **Fixes:**
      - Use the qcom-adreno-cl binary package; Turnip Vulkan is the fastest open option
    - **Outcome:** GPU usable for graphics and Vulkan/OpenCL compute at about half of Android throughput. No SDR/waterfall reports.
  26.
    - **Product:** LimeSDR Micro on Raspberry Pi CM5 (ClockworkPi uConsole)
    - **Source url:** https://www.crowdsupply.com/lime-micro/limesdr-micro/updates/thanks-and-uconsole-gqrx-demo
    - **Community:** Crowd Supply (Lime Microsystems updates)
    - **What they built:** Handheld Linux + PCIe SDR, Gqrx
    - **Problems:**
      - No OS/kernel/driver details published
    - **Fixes:** []
    - **Outcome:** Gqrx at 40 Msps shown in a demo video. This is the only public ARM-host result; no Qualcomm host shown.
  27.
    - **Product:** Lime XTRX (litepcie, LimeSuiteNG) on Raspberry Pi 5
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-xtrx-not-found/8342
    - **Community:** MyriadRF Discourse
    - **Problems:**
      - 'arch assigned 64-bit MSI address 0xffffffe000 but device only supports 32 bits', 'Failed to enable MSI', probe error -5
      - After the MSI fix, litepcie_mmap fails with 'io_remap_pfn_range failed -22'
      - Module built against mismatched kernel headers (symlink hack)
      - Device often not detected; needs several reboots
    - **Fixes:**
      - Install headers matching uname -r; -DKERNELHEADERS_DIR=/lib/modules/$(uname -r)/source
      - dtoverlay=pciex1-compat-pi5,no-mip cleared the MSI error; pcie-32bit-dma overlays did not help
    - **Outcome:** Unresolved on Pi 5; the same card worked on a CM4 IO board. Shows the class of MSI/DMA/mmap failures an out-of-tree PCIe SDR driver can hit on a new ARM SoC.
  28.
    - **Product:** Lime XTRX + GNU Radio 3.10.9.2 throughput on different hosts
    - **Source url:** https://discourse.myriadrf.org/t/optimizing-for-max-sample-rate-out-of-xtrx-gnuradio/13054
    - **Community:** MyriadRF Discourse
    - **Problems:**
      - Overruns are caused by the flowgraph not consuming fast enough; a single-threaded FIR/LPF pins one core
    - **Fixes:**
      - Raise decimation early so each block keeps up with the source rate
    - **Outcome:** Same graph: Raspberry Pi CM4 6 Msps, i5-3570K 29 Msps, Ryzen 7 5700G 60 Msps (Ubuntu 24.04). Single-core speed sets the ceiling.
  29.
    - **Product:** LimeSuiteNG SoapySDR plugin
    - **Source url:** https://github.com/myriadrf/LimeSuiteNG/issues/127
    - **Community:** GitHub (LimeSuiteNG)
    - **Problems:**
      - GQRX/CubicSDR via Soapy never start streaming ('No samples or timeout')
    - **Fixes:**
      - PR #228: create the hardware stream on activateStream instead of setupStream (merged 21 Jul 2026)
    - **Outcome:** Fixed in recent LimeSuiteNG; older builds affected.
  30.
    - **Product:** LimeSuiteNG Soapy plugin coexisting with legacy LimeSuite
    - **Source url:** https://github.com/myriadrf/LimeSuiteNG/issues/139
    - **Community:** GitHub (LimeSuiteNG)
    - **Problems:**
      - Segfault when an app linked to legacy LimeSuite loads the LimeSuiteNG Soapy plugin (clashing exported symbols)
    - **Fixes:**
      - Commit c3eabb9 (Jul 2025); only one of the two libraries should be linked
    - **Outcome:** Fixed. Do not mix legacy LimeSuite packages with LimeSuiteNG.
  31.
    - **Product:** LimeSuiteNG on Raspberry Pi 4 (arm64)
    - **Source url:** https://github.com/myriadrf/LimeSuiteNG/issues/91
    - **Community:** GitHub (LimeSuiteNG)
    - **Problems:**
      - limeDevice: 'No devices found' after an update; depended on leftover build files
    - **Fixes:**
      - Commit 750b5d4 fixing CMake file processing order; do fresh builds
    - **Outcome:** Fixed (Aug 2024).
  32.
    - **Product:** la9310_limesdr kernel module (limesdr-micro-staging)
    - **Source url:** https://github.com/myriadrf/LimeSuiteNG/pull/412
    - **Community:** GitHub (LimeSuiteNG)
    - **Problems:**
      - Reserved PCI BARs not released on module unload, so a reload cannot reserve them
    - **Fixes:**
      - Merged into limesdr-micro-staging on 1 Oct 2026 (commit 80ffad5)
    - **Outcome:** Shows the driver is still getting basic lifecycle fixes weeks before shipping.
  33.
    - **Product:** SatDump + LimeSuiteNG (XTRX fork) real-time decoding
    - **Source url:** https://github.com/SatDump/SatDump/issues/1034
    - **Community:** GitHub (SatDump)
    - **Problems:**
      - At high rates (30-120 Msps) the constellation looks fine but CADU output is gibberish and every second packet is lost; a larger buffer did not help (i7-14700)
    - **Fixes:**
      - Record IQ and decode offline (worked)
      - Maintainer: 'This should be working now' (30 Sep 2026)
    - **Outcome:** Closed on x86, with no details of the change. Not verified on ARM.
  34.
    - **Product:** SatDump 2.0.0-alpha with rotctld (Hamlib)
    - **Source url:** https://github.com/SatDump/SatDump/issues/1207
    - **Community:** GitHub (SatDump)
    - **Problems:**
      - With LC_NUMERIC set to a comma-decimal locale (bg_BG), the rotator position is never parsed ('Error getting rotator position!')
    - **Fixes:**
      - LC_NUMERIC=C satdump-ui
    - **Outcome:** Open upstream; the workaround works. The uk_UA locale also uses a comma decimal separator.
  35.
    - **Product:** SatDump 2.0.0-alpha nightly .deb on Ubuntu 24.04
    - **Source url:** https://github.com/SatDump/SatDump/issues/1129
    - **Community:** GitHub (SatDump)
    - **Problems:**
      - 'Couldn't load config file! Was trying : satdump_cfg.json'
    - **Fixes:**
      - cd /usr/share/satdump && satdump-ui
    - **Outcome:** Workaround only.
  36.
    - **Product:** SatDump TLE/OMM handling (1.2.2 and 2.0 master)
    - **Source url:** https://github.com/SatDump/SatDump/issues/1221
    - **Community:** GitHub (SatDump)
    - **Problems:**
      - Alpha-5 TLEs (NORAD >99999, issued since July 2026) are silently dropped; the SupGP CSV reader rejects the 19-column files; numbers are clamped to 99999
    - **Fixes:**
      - None; the maintainer says Alpha-5 is not supported yet and an OMM rewrite is coming; 1.2.x will not be fixed
    - **Outcome:** Unresolved. Gpredict also decodes Alpha-5 numbers as 0 (https://github.com/csete/gpredict/pull/412, unmerged).
  37.
    - **Product:** SatDump on Raspberry Pi 4 (arm64) and remote SDR server
    - **Source url:** https://github.com/SatDump/SatDump/issues/864
    - **Community:** GitHub (SatDump)
    - **Problems:**
      - Build freezes at ~45% with make -j$(nproc); the nightly arm64 deb was rejected by apt
      - Separately: the live pipeline freezes after hours with satdump_sdr_server on a Pi 4 (https://github.com/SatDump/SatDump/issues/1166, open)
    - **Fixes:**
      - make -j3 (one core fewer) to avoid OOM/crash during compile
    - **Outcome:** The build workaround works. The live-pipeline freeze is still open.
  38.
    - **Product:** SDR++ prebuilt .deb (Ubuntu/Raspberry Pi aarch64)
    - **Source url:** https://github.com/AlexandreRouma/SDRPlusPlus/issues/1805
    - **Community:** GitHub (SDR++)
    - **Problems:**
      - The prebuilt deb fails to load modules when driver libraries were built from source (version mismatch)
      - Soapy source module missing from Ubuntu debs (https://github.com/AlexandreRouma/SDRPlusPlus/issues/1577)
    - **Fixes:**
      - Maintainer: use distro driver libs with the deb, otherwise build SDR++ from source
    - **Outcome:** Building from source worked for the reporter.
  39.
    - **Product:** gr-satellites on arm64 (Raspberry Pi 4, SatNOGS)
    - **Source url:** https://github.com/daniestevez/gr-satellites/issues/416
    - **Community:** GitHub (gr-satellites)
    - **Problems:**
      - BPSK decoders spin at 100% CPU and output nothing: NaNs from the complex RMS AGC (1e-20 epsilon too small on aarch64)
    - **Fixes:**
      - 'Fix RMS AGC on aarch64 systems' commits, releases of 19 Nov 2022
    - **Outcome:** Fixed (load ~20%). Ubuntu's 5.5.0 contains the fix.
  40.
    - **Product:** VOLK ORC kernels on ARM
    - **Source url:** https://github.com/gnuradio/volk/issues/622
    - **Community:** GitHub (VOLK)
    - **Problems:**
      - ORC volk_32fc_magnitude_32f / volk_32f_sqrt_32f return NaN for zero input on ARM and are 6-14x slower than NEON
    - **Fixes:**
      - ORC kernels disabled on ARM (PR #658, Oct 2023); run volk_profile
    - **Outcome:** Fixed in VOLK 3.1+ (noble ships 3.1.2).
  41.
    - **Product:** CyberEther on aarch64 (Raspberry Pi 4, V3D Vulkan)
    - **Source url:** https://github.com/luigifcruz/CyberEther/issues/81
    - **Community:** GitHub (CyberEther)
    - **Problems:**
      - 'Can't create swapchain', VK_ERROR_INITIALIZATION_FAILED, 'No DRI3 support detected'
    - **Fixes:**
      - None specific; closed as 'likely solved in the newest version'
    - **Outcome:** No report of CyberEther on Adreno/Turnip exists.
  42.
    - **Product:** RTL-SDR Blog V4L (R828S)
    - **Source url:** https://www.rtl-sdr.com/v4l/
    - **Community:** RTL-SDR.com
    - **Problems:**
      - Older drivers 'will not operate the R828S ... correctly and may result in no received signal'
      - Diplexed input (less strong-signal protection than the V4) and no notch filter (https://rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase)
    - **Fixes:**
      - sudo apt purge ^librtlsdr; build the current osmocom/rtl-sdr with -DINSTALL_UDEV_RULES=ON; blacklist dvb_usb_rtl28xxu; keep the EEPROM strings 'RTLSDRBlog'/'Blog V4L'
    - **Outcome:** Works with updated drivers. Apps linked against the distro librtlsdr must be rebuilt or relinked.
  43.
    - **Product:** SatNOGS + SatDump Meteor decoding on Raspberry Pi CM4 / Pi 5 with RTL-SDR V4 (Docker)
    - **Source url:** https://community.libre.space/t/first-waterfall-from-mumbai-india-station-4763-mumbai-rtl-1/14581
    - **Community:** SatNOGS community (libre.space)
    - **What they built:** Ground station decoding Meteor M2-3/M2-4 LRPT
    - **Problems:**
      - SatDump 'cannot execute: required file not found' (arm64/armhf mismatch in the container)
      - Low gain (default) gave no decodes
      - Pi 5: meteor.sh 'Could not open input file' and 0 MPDUs (https://community.libre.space/t/struggling-with-automatic-meteor-m-lrpt-demodulation/13440)
    - **Fixes:**
      - Use the matching arm64 SatDump build
      - SATNOGS_RF_GAIN=48.0
      - knegge/satnogs-client:lsf-addons image, read_only:false, meteor.sh decoding the IQ file directly
    - **Outcome:** Meteor images decoded on ARM. A wired LNA was needed for quality.
  44.
    - **Product:** Qualcomm fastrpc 1.0.6/1.0.7 on RB3 Gen 2 (QCS6490 reference board)
    - **Source url:** https://github.com/qualcomm/fastrpc/issues/371
    - **Community:** GitHub (qualcomm/fastrpc)
    - **Problems:**
      - CDSP signed/unsigned sessions fail 0/3 ('Unable to create FastRPC session on domain 3') after updates; fastrpc group membership moved to startup
    - **Fixes:**
      - udev workaround patch in the debs; Qualcomm adding fastrpc tests to meta-qcom CI
    - **Outcome:** Open and stale (Sep 2026). Qualcomm's own QCS6490 board regresses too, and the regression is said to be still latent in 1.0.7.
  45.
    - **Product:** Raspberry Pi 5 Ubuntu 26.04 + Hailo-8 hailo_pci DKMS (alternative platform)
    - **Source url:** https://discourse.ubuntu.com/t/raspberry-pi-linux-image-dkms/84806
    - **Community:** Ubuntu Discourse
    - **Problems:**
      - The kernel update installed linux-image but not the matching headers, so hailo_pci was not rebuilt and A/B boot rolled back
    - **Fixes:**
      - Install linux-headers-<ver>-raspi, let DKMS build, update-initramfs -u -k <ver>; install the linux-headers-raspi meta-package to prevent a repeat
    - **Outcome:** Fixed. Shows the same DKMS trap applies to any out-of-tree PCIe driver.
- **Common problems:**
  1.
    - **Problem:** FastRPC/CDSP session failure (0x80000600, 0x80000406, 0x72, 14001, 'Failed to load skel'). Causes: a missing fastrpc memory-region in the DT, mismatched DSP firmware/shell/skel/libc++, non-Radxa QNN packages, early-boot firmware load failure on NVMe/UFS root
    - **Affected products:** Radxa OS r1/r2 (6.17/6.18/7.0 kernels), Armbian 26.x, Debian testing; also Qualcomm RB3 Gen 2 with fastrpc 1.0.6
    - **Frequency:** common
    - **Known fix:** Use the Radxa fastrpc + radxa-firmware-qcs6490 set only, and restore its payload with dpkg -V and dpkg-deb if modified. Add a DTBO with memory-region -> shared-dma-pool to both fastrpc nodes, placed in the active systemd-boot entry. Use matched CDSP c4-00004 / ADSP c9-00028 with the matching fastrpc_shell and skel. Symlink libc++.so.1/libc++abi.so.1. Add an initramfs hook for adsp.mbn/cdsp.mbn. Add a udev rule for /dev/fastrpc-* and /dev/dma_heap/*. Use the aarch64-oe-linux-gcc11.2 QAIRT build. Verify with fastrpc_test -a v68.
    - **Fix sources:**
      - https://forum.radxa.com/t/dragon-q6a-fastrpc-npu-fails-fastrpc-ioctl-init-create-returns-0x80000600-on-cdsp/31078
      - https://forum.radxa.com/t/radxa-dragon-q6a-dragon-q6a-ubuntu-24-04-qnn-htp-backend-fails-with-qnn-open-0x80000600/30850
      - https://forum.radxa.com/t/collecting-q6a-npu-fastrpc-issues/30321
      - https://forum.radxa.com/t/qnn-npu-error/30287
      - https://forum.radxa.com/t/non-functional-npu-support-on-dragon-q6a-qcs6490-under-ubuntu-24-04-noble/30699
  2.
    - **Problem:** QAIRT/QNN version mismatches: context binaries from a newer SDK fail on an older runtime (0x1388), and the current DSP firmware caps the QNN interface at 2.32.0 (QAIRT 2.42), so QAIRT 2.46+ can fail with INVALID_CONFIG and the official onnxruntime-qnn 2.x plugin (needs QAIRT 2.48+) is blocked
    - **Affected products:** QCS6490 HTP v68 on Q6A; Qualcomm AI Hub exports; onnxruntime-qnn 1.23.2 fork vs 2.x plugin
    - **Frequency:** common
    - **Known fix:** Pin one QAIRT version (Radxa-documented 2.42.0.251225) on both the x86 conversion host and the device, and export AI Hub jobs for that version. Some users run 2.46 after swapping the skel and firmware, so the result depends on the firmware.
    - **Fix sources:**
      - https://forum.radxa.com/t/qcs6490-radxa-q6a-qairt-sdk-version-mismatch-ai-hub-artifacts-2-45-x-incompatible-with-runtime-2-42-0-251225/30908
      - https://forum.radxa.com/t/dragon-q6a-qnn-htp-pipeline-working-but-int8-only-firmware-blocks-real-ml-workloads/31217
      - https://forum.radxa.com/t/running-custom-frigate-with-full-npu-support-dragon-q6a/31047
  3.
    - **Problem:** HTP v68 is INT8-only: FP16/FP32 graphs are rejected ('SocModel doesn't support FP16'), U16 quantization is unsupported, and some INT8-quantized models lose accuracy badly (ArcFace 51%, CLIP collapse, YOLO zero outputs from a shared output scale)
    - **Affected products:** QCS6490 NPU with any runtime (QNN, LiteRT delegate, ORT QNN EP)
    - **Frequency:** common
    - **Known fix:** Quantize w8a8 with QDQ, fold BatchNorm into conv, split outputs with different ranges so each gets its own scale, use NCHW static shapes, and calibrate on representative data. Compare INT8 vs FP32 accuracy on the device before trusting it. ORT QNN EP is adding v68 FP rejection so FP nodes fall back to CPU (PR #708, open).
    - **Fix sources:**
      - https://github.com/onnxruntime/onnxruntime-qnn/pull/708
      - https://github.com/onnxruntime/onnxruntime-qnn/pull/361
      - https://forum.radxa.com/t/yolov8n-context-binary-generation-for-q6a/30899
      - https://github.com/immich-app/immich/discussions/25112
  4.
    - **Problem:** Kernel/package upgrades break HDMI, boot (gdm), audio, NPU or VPU (6.18.2-1 boot hang, 7.0.11-4 HDMI black, 7.0.11-5 CDSP/VPU, 7.2.3 HDMI)
    - **Affected products:** Radxa OS r1/r2 apt upgrades; community images
    - **Frequency:** common
    - **Known fix:** Stay on 6.18.2-4-qcom, apt-mark hold linux-image/linux-headers/firmware/fastrpc, and keep a USB-TTL serial console. Recover from a TTY with dpkg --configure -a / apt-get install -f, or roll back the kernel. Use poweroff plus a long power-button press instead of a warm reboot on 7.0.
    - **Fix sources:**
      - https://forum.radxa.com/t/q6a-hanging-in-boot-after-update/30106
      - https://forum.radxa.com/t/linux-7-0-hdmi-not-working/31304
      - https://forum.radxa.com/t/npu-not-starting-on-dragon-q6a-qcs6490/30397
  5.
    - **Problem:** Out-of-tree DKMS modules fail after kernel updates (headers not installed, or the kernel built with gcc 14 while the distro has gcc 13: '-fmin-function-alignment=8')
    - **Affected products:** aic8800-usb-dkms on Armbian/Radxa OS; hailo_pci on Pi 5 Ubuntu; litepcie on Pi 5; would apply to la9310_limesdr
    - **Frequency:** common
    - **Known fix:** Install the headers meta-package matching the kernel flavour, check that the compiler matches the kernel's (cat /proc/version), run dpkg-reconfigure <pkg>-dkms or dkms autoinstall after each kernel change, update the initramfs, and hold kernel packages.
    - **Fix sources:**
      - https://forum.armbian.com/topic/60133-wifi-gone-on-current-version/
      - https://discourse.ubuntu.com/t/raspberry-pi-linux-image-dkms/84806
      - https://discourse.myriadrf.org/t/limesdr-xtrx-not-found/8342
  6.
    - **Problem:** Kioxia THGJFGT1E45BAILB UFS (Radxa 256 GB module) fails to exit hibern8, causing stutters, freezes and reboots
    - **Affected products:** Q6A + Kioxia UFS on Radxa 6.18.2 before May 2026, on mainline 6.19 (MicroOS), and likely on other non-Radxa kernels
    - **Frequency:** occasional
    - **Known fix:** Radxa kernel linux-6.18.2 with UFS_DEVICE_QUIRK_PA_TACTIVATE (radxa/kernel PR #551, merged 11 May 2026). Interim: a keep-alive script that prevents H8 entry. The Samsung module was unaffected.
    - **Fix sources:**
      - https://forum.radxa.com/t/ufs-random-reboots/30630?page=2
      - https://github.com/radxa/kernel/pull/551
  7.
    - **Problem:** Boards fail DDR training or loop on reset, often after SPI firmware flashing; some warranty returns are poor (AliExpress points instead of a replacement)
    - **Affected products:** Dragon Q6A 6/12 GB various revisions
    - **Frequency:** occasional
    - **Known fix:** None in software; RMA via the seller. Avoid unnecessary SPI reflashing; rule out the charger first.
    - **Fix sources:**
      - https://forum.radxa.com/t/help-radxa-q6a-infinite-boot-loop-reset-every-10-seconds-hardware-issue-suspected/30749
      - https://forum.radxa.com/t/dragon-q6a-won-t-boot-ddr-rcw-training-fails-on-cold-boot-board-loops-into-edl/30841
      - https://forum.radxa.com/t/radxa-dragon-q6a-with-ddr-problem/29863
  8.
    - **Problem:** Prebuilt SDR app packages do not match the needed drivers: SDR++ Ubuntu debs lack the Soapy source and break when driver libs are source-built; SatDump noble 1.1.2 is too old and the 2.0 nightly has a config-path bug; the SatDump arm64/armhf mix-up in containers
    - **Affected products:** SDR++ nightly debs, SatDump debs on Ubuntu 24.04/RPi
    - **Frequency:** common
    - **Known fix:** Build librtlsdr (osmocom current / rtl-sdr-blog), LimeSuiteNG, SoapySDR modules, SDR++ (-DOPT_BUILD_SOAPY_SOURCE=ON) and SatDump from source against the same libraries. Launch SatDump 2.0 from /usr/share/satdump. Compile with make -j3 on low-RAM systems.
    - **Fix sources:**
      - https://github.com/AlexandreRouma/SDRPlusPlus/issues/1805
      - https://github.com/AlexandreRouma/SDRPlusPlus/issues/1577
      - https://github.com/SatDump/SatDump/issues/1129
      - https://github.com/SatDump/SatDump/issues/864
  9.
    - **Problem:** Out-of-tree PCIe SDR drivers on new ARM hosts: 64-bit MSI address vs 32-bit device, probe -5, mmap io_remap_pfn_range -22, intermittent enumeration
    - **Affected products:** Lime XTRX (litepcie) on Raspberry Pi 5; risk class for la9310_limesdr on QCS6490
    - **Frequency:** occasional
    - **Known fix:** Platform DT tweaks (Pi: dtoverlay=pciex1-compat-pi5,no-mip), matched headers, and newer gateware with 64-bit DMA. No QCS6490 recipe exists.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/limesdr-xtrx-not-found/8342
      - https://discourse.myriadrf.org/t/dma-problem-with-xtrx-rev5/8445
  10.
    - **Problem:** Wideband flowgraphs overrun because single-threaded DSP blocks (FIR/LPF) cannot keep up on ARM cores; real-time high-rate decoding drops packets
    - **Affected products:** GNU Radio + LimeSuiteNG on CM4/x86; SatDump + LimeSuiteNG at 30-120 Msps
    - **Frequency:** common
    - **Known fix:** Decimate as early as possible (ideally in hardware), split the work across threads, record IQ and decode offline, and size each block's throughput against single-core speed.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/optimizing-for-max-sample-rate-out-of-xtrx-gnuradio/13054
      - https://github.com/SatDump/SatDump/issues/1034
  11.
    - **Problem:** Comma-decimal locales break the SatDump to rotctld (Hamlib) parsing
    - **Affected products:** SatDump 2.0.0-alpha with LC_NUMERIC set to a comma locale (uk_UA has the same separator)
    - **Frequency:** occasional
    - **Known fix:** LC_NUMERIC=C satdump-ui (or set LC_NUMERIC=C system-wide for the SDR user).
    - **Fix sources:**
      - https://github.com/SatDump/SatDump/issues/1207
  12.
    - **Problem:** 6-digit NORAD catalog numbers (Alpha-5 TLEs since 11 Jul 2026) are silently dropped or decoded as 0
    - **Affected products:** SatDump 1.2.2 and 2.0 master; Gpredict 2.3
    - **Frequency:** common
    - **Known fix:** None upstream yet; SatDump plans an OMM rewrite. Workaround: track new objects with a custom tool that reads OMM/JSON GP data (e.g. the Python sgp4/skyfield stack, unverified here).
    - **Fix sources:**
      - https://github.com/SatDump/SatDump/issues/1221
      - https://github.com/csete/gpredict/pull/412
  13.
    - **Problem:** Passive cooling: CPU reaches 90 °C and throttles
    - **Affected products:** Dragon Q6A with passive or homemade heatsinks
    - **Frequency:** common
    - **Known fix:** 5 V fan from the 40-pin header 5 V/GND, copper-fin cooler with fan, or Armor Case 7056A.
    - **Fix sources:**
      - https://forum.radxa.com/t/recommended-heatsink-fan-for-q6a/30413
  14.
    - **Problem:** ARM numerical edge cases producing NaNs in DSP (ORC sqrt/magnitude, complex RMS AGC epsilon)
    - **Affected products:** VOLK <3.1 with ORC on ARM; gr-satellites before Nov 2022
    - **Frequency:** rare
    - **Known fix:** Already fixed in noble's VOLK 3.1.2 and gr-satellites 5.5.0; run volk_profile once.
    - **Fix sources:**
      - https://github.com/gnuradio/volk/issues/622
      - https://github.com/daniestevez/gr-satellites/issues/416
  15.
    - **Problem:** HDMI mode negotiation with high-resolution monitors (falls back to 1024x768; GDM freezes above 1080p on Fedora)
    - **Affected products:** Q6A HDMI via the DP-to-HDMI bridge on Radxa OS / Fedora 44
    - **Frequency:** occasional
    - **Known fix:** Force the mode manually (video= cmdline or xrandr); use KDE or a lightweight compositor instead of GDM. No vendor fix.
    - **Fix sources:**
      - https://forum.radxa.com/t/samsung-g80sd-can-not-negotiate-resolution-refresh-rate/31118
      - https://forum.radxa.com/t/stock-fedora-support/30893
  16.
    - **Problem:** RTL-SDR Blog V4L (R828S) is not driven correctly by older librtlsdr (no signal)
    - **Affected products:** V4L with Ubuntu noble librtlsdr 2.0.1 and apps built against it
    - **Frequency:** common
    - **Known fix:** Purge the distro librtlsdr, build the current osmocom rtl-sdr (V4L support) with udev rules, blacklist dvb_usb_rtl28xxu, then rebuild SDR++/SatDump against it.
    - **Fix sources:**
      - https://www.rtl-sdr.com/v4l/
      - https://rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase
- **Unresolved problems:**
  1.
    - **Problem:** Nobody has published the LimeSDR Micro (la9310_limesdr) running on any Qualcomm host, let alone on the Q6A's pcie1 with its SMMU/MSI setup. The only public ARM result is a CM5 Gqrx demo at 40 Msps with no details. The driver lives only on limesdr-micro(-staging), still receiving basic fixes (BAR release on unload, 1 Oct 2026). The closest analogue (XTRX on Pi 5) hit MSI-address, mmap (-22) and enumeration failures that stayed unresolved.
    - **Why it matters for us:** The whole 56-100 MHz live-view and wideband IQ goal depends on this driver working at sustained rates on the Q6A. Failure means falling back to the RTL-SDR (2.4 Msps).
    - **Evidence:** https://www.crowdsupply.com/lime-micro/limesdr-micro/updates/thanks-and-uconsole-gqrx-demo ; https://github.com/myriadrf/LimeSuiteNG/pull/412 ; https://discourse.myriadrf.org/t/limesdr-xtrx-not-found/8342 ; no Q6A/QCS6490 SDR reports found on the Radxa forum (search 'sdr q6a' returned nothing)
  2.
    - **Problem:** PCIe/SMMU behaviour depends on the device tree: on the mainline DTB, NVMe ran ~30x slower with arm-smmu probe failures (-110). The Radxa vendor DT's pcie1 MSI count, dma-coherent and iommu-map have not been confirmed against the driver's exact-8-MSI and streaming-DMA requirements.
    - **Why it matters for us:** Wrong IOMMU or coherency settings would cause DMA faults, corrupted IQ or throughput far below the ~246 MB/s needed. The 8-MSI requirement is a hard abort.
    - **Evidence:** https://forum.radxa.com/t/catastrophic-i-o-slowdown-on-mainline-dtbs-on-6-19/30440
  3.
    - **Problem:** The NPU is INT8-only, and the firmware caps the QNN interface at 2.32 (QAIRT 2.42). Reports conflict: Dual-O says 2.46+ fails with INVALID_CONFIG, while Frigate and Rahul007 run 2.46 with swapped skel/firmware. The official onnxruntime-qnn 2.x plugin (needs QAIRT 2.48+) is therefore probably unusable. Radxa has not answered requests for FP16 or newer CDSP firmware.
    - **Why it matters for us:** The RadioML-style CNN must be fully INT8-quantized and checked for accuracy. The findings' suggestion to try onnxruntime-qnn 2.7.0 is likely a dead end on current firmware. Only the QAIRT 2.42 + forked ORT 1.23.2 / qnn-net-run / LiteRT-delegate paths are realistic.
    - **Evidence:** https://forum.radxa.com/t/dragon-q6a-qnn-htp-pipeline-working-but-int8-only-firmware-blocks-real-ml-workloads/31217 ; https://forum.radxa.com/t/running-custom-frigate-with-full-npu-support-dragon-q6a/31047 ; https://forum.radxa.com/t/qcs6490-onnxruntime-qnn-1-23-2-qairt-2-42-0-segfault-loading-precompiled-qnn-onnx-on-htp-backend/31046 (segfault on the 1.23.2 + 2.42 combo, unanswered)
  4.
    - **Problem:** Long-run NPU stability is unknown. One report has HTP inference hanging after ~1 hour; running DSPs hung a board twice (one hang needed fsck); a kernel panic occurred during NPU allocation; VTCM was limited to ~2 MB of 8 MB. No multi-hour classifier soak test has been published.
    - **Why it matters for us:** The classifier would run for whole passes or sessions next to a heavy SDR DMA load. A DSP hang that takes down the board would lose recordings.
    - **Evidence:** https://forum.radxa.com/t/npu-htp-usage-in-radxa-dragon-q6a/29949 ; https://forum.radxa.com/t/non-functional-npu-support-on-dragon-q6a-qcs6490-under-ubuntu-24-04-noble/30699 ; https://forum.radxa.com/t/report-dragon-q6a-experience-npu-kernel-panics-with-llms-aic8800-driver-instability/29959
  5.
    - **Problem:** On Radxa kernel 7.0.11 with firmware 0.2.41, the CDSP still fails with 'remotectl1 domains not supported' even after the memory-region fix. No matched firmware/fastrpc pair has been published for 7.0.x.
    - **Why it matters for us:** Moving off 6.18.2, for example for newer packages or the Ubuntu 26 image required by BIOS 260916, may lose the NPU entirely.
    - **Evidence:** https://forum.radxa.com/t/cdsp-fastrpc-session-still-fails-0x80000600-remotectl1-domains-not-supported-after-fixing-the-missing-memory-region-r2-ubuntu-24-04-kernel-7-0-11-5/31391
  6.
    - **Problem:** The Kioxia UFS quirk is confirmed only in Radxa linux-6.18.2. Its presence in Radxa 7.0.11, Armbian edge, the community 7.2.9 image and mainline is undocumented. Only ~0.5 GB/s write (fio) has been reported after the fix. Nobody has published sustained multi-minute IQ writes concurrent with PCIe DMA.
    - **Why it matters for us:** Raw IQ recording at ~246 MB/s (and 160 Msps bursts) depends on stable, sustained UFS writes. An H8 stall mid-pass drops samples or reboots the device.
    - **Evidence:** https://forum.radxa.com/t/ufs-random-reboots/30630?page=2 ; https://forum.radxa.com/t/radxa-poe-hat-overlay-on-microos/30704
  7.
    - **Problem:** Live 56 Msps DSP on 4x A78 + 4x A55 is unbenchmarked. The XTRX data shows single-threaded filters cap throughput (CM4 6 Msps, i5-3570K 29 Msps, Ryzen 5700G 60 Msps). SatDump real-time decoding at high rates with LimeSuiteNG dropped packets even on an i7 (closed as fixed on x86 only).
    - **Why it matters for us:** The live 56-100 MHz waterfall plus S-band/HRPT decode may need hardware decimation (LMS7002M/LA9310 VSPA) or record-then-decode, so the classifier and UI must not starve the receive thread.
    - **Evidence:** https://discourse.myriadrf.org/t/optimizing-for-max-sample-rate-out-of-xtrx-gnuradio/13054 ; https://github.com/SatDump/SatDump/issues/1034
  8.
    - **Problem:** SatDump and Gpredict cannot handle Alpha-5 / 6-digit NORAD numbers (catalog passed 99999 on 11 Jul 2026). SatDump silently drops them, and Gpredict decodes them as 0.
    - **Why it matters for us:** Newly launched amateur CubeSats (435-438 MHz goal) will be missing from pass prediction and the pointing aid unless a custom OMM-based tracker is written.
    - **Evidence:** https://github.com/SatDump/SatDump/issues/1221 ; https://github.com/csete/gpredict/pull/412
  9.
    - **Problem:** The HDMI path to a >1080p panel is fragile: EDID negotiation falls back to 1024x768 on a 4K monitor, GDM freezes above 1080p (Fedora), and HDMI regressed in kernels 7.0.11-4, 7.0 and 7.2.3. No report covers a high-resolution, high-brightness HDMI touch panel on the Q6A.
    - **Why it matters for us:** The user wants a bright display above Full HD over HDMI (DSI third-party panels are unsupported). The panel may need a forced mode, a lightweight compositor, and a frozen kernel.
    - **Evidence:** https://forum.radxa.com/t/samsung-g80sd-can-not-negotiate-resolution-refresh-rate/31118 ; https://forum.radxa.com/t/stock-fedora-support/30893 ; https://forum.radxa.com/t/linux-7-0-hdmi-not-working/31304
  10.
    - **Problem:** Firmware/OS fork in the road: BIOS 260916 (needed for UKI-boot and other fixes) is 'Not compatible with Radxa OS (Ubuntu 24)' and targets a Radxa Ubuntu 26 image that exists only as pre-release 'dragon-midstream' test builds (t1-t3, with display tearing). Mainline still lacks Q6A UFS/HDMI.
    - **Why it matters for us:** The build will be stuck on the Ubuntu 24 + BIOS 260120 + 6.18.2 combination for an unknown period. Any later migration means re-validating UFS, HDMI, NPU and the out-of-tree driver together.
    - **Evidence:** https://dl.radxa.com/dragon/q6a/images/dragon-q6a-bios-changelog.md ; https://forum.radxa.com/t/uki-boot-on-20250120-firmware/30896 ; https://forum.radxa.com/t/new-version-os-like-ubuntu-26-04/30468
  11.
    - **Problem:** Whether the la9310_limesdr DKMS build will hit the same compiler-mismatch trap as aic8800 is unknown: it depends on whether the Radxa kernel is built with a gcc version different from Ubuntu's.
    - **Why it matters for us:** A kernel security update could silently leave the SDR without a driver in the field.
    - **Evidence:** https://forum.armbian.com/topic/60133-wifi-gone-on-current-version/
  12.
    - **Problem:** CyberEther and other Vulkan-compute waterfalls are unverified on Turnip/Adreno 643. Radxa staff said the Q6A 'does not support Vulkan as a GPU backend' (llama.cpp context), and the only aarch64 CyberEther bug report (Pi 4) failed at swapchain creation.
    - **Why it matters for us:** GPU offload of the wide waterfall is the main plan to save CPU for DSP. If it fails, SDR++'s OpenGL waterfall or a reduced FFT rate is the fallback.
    - **Evidence:** https://forum.radxa.com/t/vulkan-crashes-and-npu-setup-for-llm-inference-on-dragon-q6a-need-guidance/30264 ; https://github.com/luigifcruz/CyberEther/issues/81 ; https://forum.radxa.com/t/how-to-install-qualcomm-opencl-sdk-on-dragon-q6a/30787
  13.
    - **Problem:** No reports exist of a 2230-to-2280 M.2 extension or flex adapter carrying a PCIe Gen3 endpoint on the Q6A. The LimeSDR Micro also has a non-standard ~4 mm component height.
    - **Why it matters for us:** Link errors (AER) or mechanical fit problems in the handheld case would force a Gen2 link cap or a case redesign.
    - **Evidence:** https://forum.radxa.com/t/dragon-q6a-ai-acceleration/30500 ; https://www.cnx-software.com/2026/04/15/limesdr-micro-m-2-2280-sdr-card-pairs-nxp-la9310-baseband-processor-with-lms7002m-rf-transceiver/
  14.
    - **Problem:** The SatDump live pipeline freezes after hours with a remote SDR server (Pi 4 server), and the Meteor HRPT live-decode crash is still open. Neither has a maintainer response.
    - **Why it matters for us:** Hours-long unattended sessions (or splitting the RTL-SDR into a separate server process) could stall without warning.
    - **Evidence:** https://github.com/SatDump/SatDump/issues/1166 ; https://github.com/SatDump/SatDump/issues/1134
- **Communities checked:**
  - Radxa forum (forum.radxa.com): Q6A category pages 0-1 plus search.json queries for pcie, ufs, sdr, hailo, m.2, tflite delegate, onnxruntime-qnn, vulkan, hdmi, dkms, linux-headers, iommu, coral. About 45 threads read. The HTML /search page is blocked; search.json works.
  - Armbian forum (forum.armbian.com): Q6A search, Wi-Fi/DKMS thread
  - MyriadRF / Lime Discourse (discourse.myriadrf.org) via search.json: LimeSDR Micro, XTRX on Pi/CM4, DMA/MSI threads
  - Crowd Supply LimeSDR Micro project updates
  - CNX Software (LimeSDR Micro article: 0 reader comments; no Q6A review comments found)
  - GitHub issues/PRs: SatDump, SDR++ (SDRPlusPlus), LimeSuiteNG, gr-satellites, VOLK, CyberEther, gpredict, microsoft/onnxruntime, onnxruntime/onnxruntime-qnn, radxa/kernel, radxa-pkg/fastrpc, qualcomm/fastrpc, rtlsdrblog/rtl-sdr-blog, immich-app/immich discussions
  - SatNOGS community (community.libre.space) via search.json
  - RTL-SDR.com articles and comments (V4L guide, V4L launch, RTL-ML)
  - Ubuntu Discourse (Pi 5 DKMS headers thread)
  - Hailo community (via search results only)
  - Radxa docs and BIOS changelog (official, for context)
  - Reddit: unreachable (WebFetch blocked; WebSearch returned no Reddit threads on the Q6A)
  - Mesa GitLab (gitlab.freedesktop.org): blocked by Anubis bot protection
  - BATC forum: HTTP 503 (unreachable)
  - NXP community: searched, no LA9310 host-side reports
  - Qualcomm developer forums, AMSAT, EEVblog, mikrocontroller.net, StackExchange: not reached or no relevant hits within the search budget
- **Recommendation impact:** The community record supports the recommended base, with some changes. Pin Radxa OS r2 (Ubuntu 24.04) on BIOS 260120, specifically kernel 6.18.2-4-qcom. Only that Radxa kernel line has the confirmed Kioxia UFS PA_TACTIVATE fix, working HDMI and the most NPU success reports. apt-mark hold the kernel, headers, firmware and fastrpc packages, and do not move to 7.0.11 yet: it has HDMI regressions and an unresolved 'remotectl1' CDSP failure. Keep a USB-TTL serial cable in the kit.
  
  Changes to the plan:
  
  1. NPU: drop the onnxruntime-qnn 2.7.0 option for now. Users report the Q6A DSP firmware caps the QNN interface at QAIRT 2.42, and the official plugin needs 2.48+. Target QAIRT 2.42.0.251225 (OE gcc11.2 build) on both the x86 host and the device. Make the classifier a fully INT8 QDQ CNN with BatchNorm folded and static NCHW shapes, and validate INT8 accuracy on the device against FP32. HTP v68 rejects FP16, and INT8 has wrecked accuracy for some models. Keep the CPU ONNX Runtime path as the default, because HTP hangs after ~1 h and DSP-induced board hangs have been reported.
  
  2. LimeSDR Micro: there is no Qualcomm-host evidence, and the XTRX-on-Pi 5 analogue failed on MSI/mmap. Treat the Micro as an experiment with a bring-up checklist:
     - lspci and the 8-MSI line in dmesg
     - SMMU faults
     - a sustained 61.44 Msps test
     - module reload, after PR #412
     - a DKMS rebuild after a kernel change, with compiler-version parity checked
     Have the RTL-SDR path working first. Plan for hardware decimation or record-then-decode instead of live 56 Msps DSP on CPU. CM4/x86 data shows single-threaded filters set the ceiling, and SatDump real-time decoding at high rates with LimeSuiteNG dropped packets even on x86.
  
  3. RTL-SDR: buying the V4L means purging noble's librtlsdr, building current osmocom rtl-sdr, and then building SDR++ (with -DOPT_BUILD_SOAPY_SOURCE=ON) and SatDump from source against the same libraries. Prebuilt SDR++ debs break with mismatched libs and lack the Soapy source.
  
  4. Operations: run SatDump with LC_NUMERIC=C, because the Ukrainian locale's comma decimal breaks rotctld parsing. Launch SatDump 2.0 from /usr/share/satdump. Write the pointing aid to read OMM/JSON GP data. SatDump and Gpredict drop the 6-digit NORAD numbers issued since July 2026, which affects new CubeSats.
  
  5. Display: test the chosen high-resolution HDMI panel's EDID early. Run a kiosk compositor (cage/weston) rather than GDM, and be ready to force the mode.
  
  6. Hardware: active cooling is mandatory (90 °C throttling when passive). Power must enter via USB-C PD 12 V or the 12 V DC header; the 5 V header cannot power the board. Buy from a seller with a real RMA path, because several boards died from DDR training failures and avoidable SPI reflashing.
  
  7. Mainline, Armbian edge and BIOS 260916 / Ubuntu 26 are not viable for this build until UFS, HDMI and the NPU stack are proven there.
  
  Net effect: the software stack stays feasible on the Q6A, but the confidence that the LimeSDR Micro and NPU parts will work out of the box drops from medium to low-medium. The RTL-SDR + CPU-classifier budget path is the configuration with real community evidence behind it.

## Власні виправлення (`fixes`)

_Агент цього етапу ще працює (run `wf_e49d4f53-8d4`)._

