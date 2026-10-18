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

_Агент цього етапу ще працює (run `wf_e49d4f53-8d4`)._

