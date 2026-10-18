# Npu training: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_9603e249-d87`_

- **Subsystem:** npu_training: SpecDet INT8 on HTP v68 with QAIRT 2.42, CPU stage-2 embedder, Phase-0 gate, x86-64 Ubuntu 22.04 conversion host, ORT CPU fallback, class policy gate, data handling (no voice IQ), training budgets
- **Findings:**
  1.
    - **Claim in stack:** #37 / 5.4: QAIRT 2.42.0.251225 on the device comes from Radxa qcom-qnn-sdk-v68 0.1.0-2
    - **Finding:** Radxa's qcs6490-noble apt repo (Release dated 24 Sep 2026) still ships qcom-qnn-sdk-v68 0.1.0-2. The deb is 44,221,844 B, SHA-256 306fd647b88902d170831980ca68a31d77d77923534e2070783fbeca132a6e54, changelog dated 26 Jun 2026. I downloaded and opened it: libQnnHtp.so, libQnnHtpPrepare.so and libQnnHtpV68Skel.so contain 'AISW_VERSION: 2.42.0' and 'v2.42.0.251225135753_193295'. libQnnHtp, libQnnSystem, libQnnHtpPrepare, libQnnHtpV68Stub and libQnnCpu are byte-for-byte the same size as the SDK zip's lib/aarch64-oe-linux-gcc11.2 copies, and the V68 skel matches lib/hexagon-v68/unsigned. The deb includes qnn-context-binary-generator/-utility, qnn-net-run, qnn-throughput-net-run, qnn-platform-validator and qnn-profile-viewer. It has no qairt-converter or qairt-quantizer, so the x86 host is still needed.
    - **Verdict:** confirmed
    - **Action:** Put the deb's SHA-256 (306fd647...6e54) into the golden-set manifest and archive the deb. It counts as the same build as the host zip, so binaries built on the host with 2.42 match the device runtime.
    - **Impact:** high
    - **Sources:**
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/main/binary-arm64/Packages
      - https://radxa-repo.github.io/qcs6490-noble/pool/main/q/qcom-qairt/qcom-qnn-sdk-v68_0.1.0-2_all.deb
  2.
    - **Claim in stack:** #37: the SDK zip is 1,543,955,191 B and could still be downloaded on 18.10.2026
    - **Finding:** A range GET on 18 Oct 2026 returned content-range bytes 0-0/1543955191, Last-Modified 7 Jan 2026, ETag 8afeb63c22bd4bacb721648636c8829c. No login was needed (softwarecenter.qualcomm.com redirects 301 to apigwx-aws.qualcomm.com). sdk.yaml in the zip says product QAIRT, version 2.42.0, os Ubuntu 22.04 / Windows 11, qnn_backend_api_version 2.18.0. QAIRT_ReleaseNotes.txt dates 2.42.0 to 01/06/2026 with QNN API v2.32.0.
    - **Verdict:** confirmed
    - **Action:** Download the full zip now, compute its SHA-256 and archive it on the PC and the T7. The size and ETag above identify the right file.
    - **Impact:** high
    - **Sources:**
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
      - https://docs.radxa.com/en/dragon/q6a/app-dev/npu-dev/qairt-install
  3.
    - **Claim in stack:** #45 / 5.4: conversion host is x86-64 Ubuntu 22.04 / Python 3.10
    - **Finding:** Confirmed. bin/check-python-dependency in the 2.42 zip maps Ubuntu 22.04 to Python 3.10 only and rejects anything else. Radxa's qairt-install page asks for x86-64, Ubuntu 22.04 and Python 3.10 (conda). Qualcomm's revision history adds Ubuntu 24.04 / Python 3.12 host support only in 2.47.0 (May 2026). New risk: Python 3.10 reached upstream end of life on 2026-10-01 (3.10.22 was the last release), and Ubuntu 22.04 standard support ends 2027-06-01 (ESM continues to 2032).
    - **Verdict:** new_risk
    - **Action:** Keep the conversion host as a frozen, offline ubuntu:22.04 container with a pinned package set. Do not run training or anything internet-facing in it.
    - **Impact:** medium
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/app-dev/npu-dev/qairt-install
      - https://docs.qualcomm.com/doc/80-63442-10/topic/general_revision_history.html
      - https://endoflife.date/api/python.json
      - https://endoflife.date/api/ubuntu.json
  4.
    - **Claim in stack:** Home base: torch 2.14.1 / onnx 1.23.2 export, then QAIRT 2.42 conversion (opset and exporter listed as an open question)
    - **Finding:** sdk.yaml for 2.42 lists converter dependencies onnx 1.16.1, onnxruntime 1.17.1, torch 1.13.1 and onnxsimplifier 0.4.36. onnx 1.16.1 supports IR version 10 and opsets up to 21 (onnx VERSION_TABLE). The SupportedOps header in the 2.42 docs says 'Onnx(Opset <= 22)'. The training stack's onnx 1.23.2 is IR 14 / opset 28. A model saved from the training environment can therefore have an IR version above 10, which the converter's onnx 1.16.1 may reject.
    - **Verdict:** new_risk
    - **Action:** Export at opset 17-21, set model.ir_version=10, and run onnx 1.16.1 checker plus qairt-converter inside the 2.42 container as a CI step. This closes the open question on opset and exporter.
    - **Impact:** medium
    - **Sources:**
      - https://raw.githubusercontent.com/onnx/onnx/v1.23.2/onnx/helper.py
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
  5.
    - **Claim in stack:** Home base = one ubuntu:22.04 / Python 3.10 container; the toolset includes onnxruntime 1.31.0 and scikit-learn 1.9.1
    - **Finding:** From PyPI: the last onnxruntime with cp310 wheels is 1.23.2, and the last scikit-learn with cp310 wheels is 1.7.2. onnxruntime 1.31.0, onnxruntime-qnn 2.x and scikit-learn 1.9.1 all require Python 3.11 or newer. torch 2.14.1 (cp310 wheels), aimet-torch 2.41.0 (py310-none-any) and aimet-onnx 2.41.0 (cp310-abi3, manylinux_2_34 x86_64, fine on 22.04's glibc 2.35) do support 3.10. CPU-vs-HTP parity tests need the same ORT as the device (1.31.0), which cannot be installed on 3.10.
    - **Verdict:** corrected
    - **Action:** Split the home base into two environments: (a) ubuntu:22.04/py3.10 with QAIRT 2.42 and AIMET; (b) py3.12 for training and parity with torch 2.14.1 (CUDA), onnxruntime 1.31.0 and scikit-learn 1.9.1, the same versions as the device.
    - **Impact:** medium
    - **Sources:**
      - https://pypi.org/pypi/onnxruntime/json
      - https://pypi.org/pypi/scikit-learn/json
      - https://pypi.org/pypi/aimet-torch/json
      - https://pypi.org/pypi/aimet-onnx/json
      - https://pypi.org/pypi/torch/json
  6.
    - **Claim in stack:** ORT CPU fallback: onnxruntime 1.31.0 (MIT), aarch64 cp311-cp314 wheels
    - **Finding:** onnxruntime 1.31.0 was uploaded 2026-10-09, MIT licence, requires_python >=3.11. It has manylinux_2_28_aarch64 wheels for cp311, cp312, cp313(t) and cp314(t); the cp312 wheel is 21.4 MB and suits Radxa OS r2 noble on Python 3.12. Releases are now roughly monthly (1.26.0 on 8 May through 1.31.0 on 9 Oct 2026).
    - **Verdict:** confirmed
    - **Action:** Pin 1.31.0, archive the cp312 aarch64 wheel and the matching x86_64 wheel together with the golden set, and do not follow monthly upgrades.
    - **Impact:** medium
    - **Sources:**
      - https://pypi.org/pypi/onnxruntime/json
  7.
    - **Claim in stack:** C19 / 5.5: CPU-mode detector about 4-6 tiles/s on A55 cores with CPUQuota 100%
    - **Finding:** Not measured anywhere. Model only: 4-6 tiles/s x 0.57 GFLOP/tile (SpecDet-S) = 2.3-3.4 GFLOP/s, which is 15-22% of one Cortex-A55's roughly 15.2 GFLOPS FP32 peak (assumes 8 FLOP/cycle at 1.9 GHz). That is plausible only with good MLAS kernels or an INT8 QDQ model (A55 SDOT). The npu_training audit derived the CPU budget from 'all the big cores', which does not match the A55 placement in C19.
    - **Verdict:** unverified
    - **Action:** In Phase 0, benchmark ORT 1.31 with SpecDet-S FP32 and QDQ on one A55 and on one A78. If one A55 gives fewer than 4 tiles/s, lower the RTL-F rate (raise K) or allow CPUQuota of about 150% on CPU0-3. Do not borrow A78 time from RX.
    - **Impact:** medium
    - **Sources:**
      - https://pypi.org/pypi/onnxruntime/json
  8.
    - **Claim in stack:** Set A alternative: Radxa onnxruntime_qnn 1.23.2 cp312 fork (ZIFENG278) built on QAIRT 2.42.0.251225
    - **Finding:** Radxa's QNN EP page lists onnxruntime_qnn-1.23.2-cp312-cp312-linux_aarch64.whl from github.com/ZIFENG278/onnxruntime v1.23.2, with QNN_ARCH_ABI set to aarch64-oe-linux-gcc11.2 and env PRODUCT_SOC=6490, DSP_ARCH=68, using qairt/2.42.0.251225. Its sample log shows a 'rel/qairt-2.37.1' path, which the page does not explain. Forum 31046 (14 Jun 2026), a segfault loading a precompiled QNN ONNX with 1.23.2 + 2.42 on kernel 6.18, still has only one post and no answer.
    - **Verdict:** confirmed
    - **Action:** Keep the native QNN API / qnn-net-run path as primary and the ORT 1.23.2 EP as optional. Before relying on the EP, check which QNN libraries it loads (ldd / backend_path) against the golden libQnnHtp.so.
    - **Impact:** low
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/app-dev/npu-dev/qnn-onnxrt-execution-provider
      - https://forum.radxa.com/t/31046
  9.
    - **Claim in stack:** #39 / 5.4: input encoding pinned through offload_graph_io_quantization=0
    - **Finding:** offload_graph_io_quantization is an ONNX Runtime QNN EP provider option: '1' (the default) moves graph I/O Q/DQ to the CPU EP, and '0' keeps it in the QNN EP. It does not appear anywhere in the QAIRT 2.42 tools, HTP backend or release-notes docs. The native path is qairt-converter -> qairt-quantizer -> qnn-context-binary-generator. On that path the input encoding is pinned with the 2.42 flags --input_dtype, --input_layout, --custom_io, --preserve_io_datatype, --use_native_input_files and --quantization_overrides, all of which appear in the 2.42 tools doc.
    - **Verdict:** corrected
    - **Action:** Change #39 to read: native path pins I/O with the converter/quantizer flags (uint8 input, fixed scale, chosen layout); the ORT-EP path additionally sets offload_graph_io_quantization=0. Check the encodings with qnn-context-binary-utility in both cases.
    - **Impact:** medium
    - **Sources:**
      - https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
  10.
    - **Claim in stack:** #40: dsp_arch v68, soc_model 35 until checked ('QNN maps SM7325 to 35, QCM6490 to 93')
    - **Finding:** The 'Supported Snapdragon devices' table shipped in the 2.42 zip (docs/QAIRT-Docs/QNN/general/overview.html) lists QCM6490 as SOC Model 35, Hexagon V68, toolchains aarch64-android, aarch64-ubuntu-gcc9.4 and aarch64-oe-linux-gcc11.2. 778G (SM7325) is also 35. No device in the 2.42 table has SOC model 93.
    - **Verdict:** corrected
    - **Action:** Use soc_model 35 / dsp_arch v68 as the documented value for 2.42. Reduce the 35-vs-93 Phase 0 item to a quick check with qnn-platform-validator.
    - **Impact:** low
    - **Sources:**
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
  11.
    - **Claim in stack:** Architecture: HTP cannot train; weight sharing needs v73+, so detector is frozen INT8 and fine classes live in CPU stage 2
    - **Finding:** The 2.42 HTP backend doc says weight sharing 'Only supports Hexagon v73 and onward architectures' and only offline prepare on x86_Linux. Native KV-cache layout 'Cannot support v68 targets or lower'. QNN offers no training API. Binary weight-only and quant-only updates are listed as 'Not supported for QCLINUX'. The frozen-detector plus CPU-head split is therefore the right design.
    - **Verdict:** confirmed
    - **Action:** No change.
    - **Impact:** high
    - **Sources:**
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
  12.
    - **Claim in stack:** #39 / #42: conv-only INT8, ReLU/HardSwish, space-to-depth in the tiler to [1,32,128,128], separate Clip-bounded outputs
    - **Finding:** The 2.42 HTP guidelines say ReLU is the best activation and HardSwish/PReLU fuse in A8/A16. Channels should be rounded to multiples of 32. Space-to-depth should be used for low-depth inputs, and data movers such as SpaceToDepth should be avoided on the device, so doing it in the tiler is right. A 2x512x512 tile with 4x4 S2D gives exactly 32 channels. The converter supports every op used: Conv (1/11/22), Clip, HardSwish (14/22), SpaceToDepth (1/13), QuantizeLinear/DequantizeLinear (up to 21). The same guide says grouped convolutions with up to 32 channels per group are more efficient than group size 1 (depthwise).
    - **Verdict:** new_option
    - **Action:** Keep the Phase 0 S/M/G benchmark, but expect SpecDet-G or SpecDet-M to beat depthwise SpecDet-S per millisecond on HMX. Promote G if its AP is at least S's.
    - **Impact:** medium
    - **Sources:**
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
  13.
    - **Claim in stack:** #39: 'v68 firmware rejects FP16 and FP32'; A16W8 only after a test
    - **Finding:** The 2.42 docs do not give FP16 support per architecture; the claim rests only on a community log ('The SocModel doesn't support FP16'). The A16W8 path is available in the 2.42 quantizer through --act_bitwidth/--act_bw 16, --weights_bitwidth 8 and --use_per_channel_quantization. Forum 31462 (16 Sep 2026) reports YOLOv8n output collapse with QAIRT 2.49 on QCS6490, so a newer SDK does not fix detection-head quantisation by itself.
    - **Verdict:** unverified
    - **Action:** Keep INT8 as primary and run one A16W8 test (fam head only) in Phase 0. Keep the separate, Clip-bounded outputs with explicit encodings.
    - **Impact:** medium
    - **Sources:**
      - https://forum.radxa.com/t/31462
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
  14.
    - **Claim in stack:** #40: vtcm_mb=2; a 4,194,304-byte request fails with 0x138d
    - **Finding:** No primary source found for the QCS6490 VTCM size or for the 0x138d failure. The 2.42 release notes mention '2MB VTCM HTP targets' in general, and the HTP doc says the maximum VTCM depends on the SoC (QNN_HTP_GRAPH_CONFIG_OPTION_MAX).
    - **Verdict:** unverified
    - **Action:** In Phase 0, read the reported VTCM with qnn-platform-validator / the device info API, build at 2 MB, and check every binary with qnn-context-binary-utility.
    - **Impact:** low
    - **Sources:**
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
  15.
    - **Claim in stack:** #37: never use AI Hub QNN/DLC artifacts; 0x1388 = context binary newer than the runtime
    - **Finding:** Forum 30908 (27 May-14 Jun 2026) shows 'Using newer context binary on old SDK', 'err 5000' and '0x1388' (5000 decimal). Radxa (Morgan, 2 Jun 2026) replied: 'The new QNN context binary cannot run in older QAIRT runtime environments.' AI Hub Workbench added QAIRT 2.49.0 on 17 Aug, moved to 2.50.0 and removed 2.47 on 14 Sep 2026. QAIRT 2.42 was last listed on 14 Apr 2026, so AI Hub cannot produce 2.42 binaries now and its profiling numbers do not apply to 2.42.
    - **Verdict:** confirmed
    - **Action:** Keep the rule. Treat any AI Hub latency only as an upper-level reference, never as the Phase 0 number.
    - **Impact:** medium
    - **Sources:**
      - https://forum.radxa.com/t/30908
      - https://workbench.aihub.qualcomm.com/docs/hub/release_notes.html
  16.
    - **Claim in stack:** 5.4 / #23: golden NPU firmware set = CDSP c4-00004 + ADSP c9-00028 (identified by version), held
    - **Finding:** radxa-firmware-qcs6490 0.2.42 (17 Sep 2026, changelog 'fix: update qcs6490 dsp firmware') ships DSP images whose QC_IMAGE_VERSION_STRING still reads CDSP.HT.2.5.c4-00004-KODIAK-1 / ADSP.HT.5.5.c9-00028-KODIAK-2. However, the OEM_IMAGE_UUID is dated 20260804 and the files are new: cdsp.mbn SHA-256 644cb94cf4fe97ee47448ab698de6e0826ec1b9ba2ff9ed5009be501295e3de6, adsp.mbn da35227f410fd8d1da949d6d660504501e724b9c248a9ddf18d7103ab588ac8e. adsp.mbn is now 14,012,896 B, against 9,871,840 B reported from the r2 image (forum 30321). Neither file matches the community kit digests (a9645c94..., 01fea794...). The version string alone no longer identifies the golden set. The repo also has fastrpc/libcdsprpc1 1.0.7-3; forum 31391 shows that userspace/shell/firmware mismatches give 0x80000600.
    - **Verdict:** new_risk
    - **Action:** Pin the golden set by SHA-256 of the files from the r2 rootfs: cdsp/adsp.mbn, fastrpc_shell_unsigned_3, the /usr/lib/dsp tree, fastrpc and libcdsprpc1 versions. apt-mark hold radxa-firmware-qcs6490 and fastrpc*. Treat any firmware update as a runtime change: fastrpc_test 3/3, golden gate, then the 8 h soak.
    - **Impact:** high
    - **Sources:**
      - https://radxa-repo.github.io/noble/pool/main/r/radxa-firmware/radxa-firmware-qcs6490_0.2.42_all.deb
      - https://radxa-repo.github.io/noble/dists/noble/main/binary-arm64/Packages
      - https://forum.radxa.com/t/30321
      - https://forum.radxa.com/t/31391
  17.
    - **Claim in stack:** #23 / 5.4: hold linux-image-6.18.2-4-qcom together with the golden NPU set
    - **Finding:** The qcs6490-noble apt index (24 Sep 2026) no longer lists linux-image-6.18.2-4-qcom; the pool URL returns 404. The meta packages linux-image-radxa-dragon-q6a and -midstream (7.0.11-7) now depend on linux-image-7.0.11-7-qcom. The GitHub release radxa-pkg/linux-qcom 6.18.2-4 (30 Mar, 16 assets) still exists. Forum 31391 (31 Aug 2026) reports CDSP FastRPC failing on 7.0.11-5 with 'remotectl1 domains not supported'.
    - **Verdict:** new_risk
    - **Action:** Download the 6.18.2-4 image and header debs from the GitHub release now and archive them with SHA-256. Hold the meta packages so apt does not pull 7.0.11-7. (Shared with the compute subsystem.)
    - **Impact:** high
    - **Sources:**
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/main/binary-arm64/Packages
      - https://github.com/radxa-pkg/linux-qcom/releases/tag/6.18.2-4
      - https://forum.radxa.com/t/31391
  18.
    - **Claim in stack:** #38 / 6.1: Set B (ORT 1.27 + onnxruntime-qnn 2.3.0 on QAIRT 2.47) removed; user question 7 (newer QAIRT if 2.42 fails)
    - **Finding:** The onnxruntime-qnn v2.3.0 release states 'QAIRT SDK Compatibility: 2.47.0' and ORT >=1.24.1, so the Set B description is correct. Newer evidence: PrismPhi (forum 31448, 13 Sep 2026) runs Qwen3.5-0.8B entirely on Q6A HTP v68 with ORT 1.27.0 + QNN EP 2.3.0 on Ubuntu 24.04.4, CPU fallback disabled, after device-measured zero-input offset corrections. This shows Set B working on v68, which contradicts older '2.46+ fails' reports. The latest is onnxruntime-qnn 2.7.0 (13 Oct 2026), built for QAIRT 2.51.0, ORT >=1.24.1, with no v68 notes.
    - **Verdict:** new_option
    - **Action:** Keep Set B removed by rule. If Phase 0 fails on 2.42, present Set B to the user as the evidence-backed fallback for question 7, with its own golden set and soak.
    - **Impact:** medium
    - **Sources:**
      - https://github.com/onnxruntime/onnxruntime-qnn/releases/tag/v2.3.0
      - https://github.com/onnxruntime/onnxruntime-qnn/releases/tag/v2.7.0
      - https://forum.radxa.com/t/31448
      - https://pypi.org/pypi/onnxruntime-qnn/json
  19.
    - **Claim in stack:** C20: HTP gate p99 <= 28 ms at 50% load without Lime; <= 11.7 ms or <= 41 tiles/s with Lime
    - **Finding:** The arithmetic checks out (model): 17.6 tiles/s x 28 ms = 49.3%, 16.6 x 28 = 46.5%, 41 x 11.7 = 48.0%, 42.5 x 11.7 = 49.7%. There is still no published QAIRT 2.42 per-tile latency on the Q6A. One community data point: YOLOv8n at about 10 ms with QAIRT 2.46 (forum 31047), a much larger model than SpecDet-S at 0.29 GMAC, which suggests the 28 ms gate has margin.
    - **Verdict:** confirmed
    - **Action:** Keep the gates. In Phase 0, also log FastRPC overhead per call, because it can dominate for 0.3-GMAC graphs.
    - **Impact:** medium
    - **Sources:**
      - https://forum.radxa.com/t/31047
  20.
    - **Claim in stack:** #42: E-S embedder 16.3 MMAC / 0.16 M params; T2 4.5-10.8 min on A78 between passes
    - **Finding:** Reproduced analytically on a 2x64x64 input: 3x3 s2 stem 2->32, then DW-separable blocks 32->64 (s1), 64->128 (s2), 128->128, 128->256 (s2), 256->256, then FC 261->128. Result: 16.3 MMAC and 0.166 M params. T2 for 4000 crops x 20 epochs x 3x forward = 7.8 TFLOP, i.e. 4.5-10.9 min at 12-29 GFLOPS. That needs 10-25% of the roughly 115 GFLOPS FP32 peak of CPU4-6 (3 x A78 at 2.4 GHz, 16 FLOP/cycle, model). Depthwise backprop in PyTorch CPU is often below 10% efficient, so the upper end may be exceeded.
    - **Verdict:** confirmed
    - **Action:** Benchmark one T2 epoch with torch 2.14.1+cpu on CPU4-6 in Phase 0. If it runs over 11 min, use the frozen-early-layer variant by default.
    - **Impact:** low
    - **Sources:**
      - https://download.pytorch.org/whl/cpu/torch/
  21.
    - **Claim in stack:** #45 / 5.4: T3 at home, SpecDet-S 1.6-4.8 h, SpecDet-M 4.9-14.7 h per 100 epochs x 100k tiles; RTX 3060 12 GB class
    - **Finding:** Arithmetic checks out (model): SpecDet-S gives 17.4 PFLOP per run, 1.6-4.8 h at 1-3 TFLOPS effective, which is 8-24% of the RTX 3060's 12.74 TFLOPS FP32 peak. One epoch is 52.4 GB. Prices are not verified and come from undated 2026 snapshots: RTX 3060 12 GB about $330-370, now dearer than an RTX 5050; RTX 5060 Ti 16 GB about $580-615 (launch $429). TorchSig recommends 16 GB.
    - **Verdict:** unverified
    - **Action:** Keep 'GPU only for T3'. If the user buys a GPU, compare a 3060 12 GB with a 16 GB card (e.g. 5060 Ti 16 GB) on current listings. No GPU is needed for conversion.
    - **Impact:** low
    - **Sources:**
      - https://www.pcguide.com/news/rtx-3060-12gb-now-costs-more-than-the-rtx-5050-after-latest-price-hike/
      - https://dropreference.com/en/compare/gpu/nvidia-geforce-rtx-3060-12gb-vs-nvidia-geforce-rtx-5060-ti-16gb
  22.
    - **Claim in stack:** Software: torch 2.14.1+cpu (159 MB aarch64) on device; torchvision 0.29.1; aimet-torch 2.41.0 (also test 2.21/2.22); qai-hub 0.56.0; onnx 1.23.2; faiss-cpu 1.15.1
    - **Finding:** torch-2.14.1+cpu-cp312 manylinux_2_28_aarch64 is 159,242,183 B on download-r2.pytorch.org (Last-Modified 30 Sep 2026). The PyPI aarch64 wheel is 454 MB, so use the /whl/cpu index. torchvision 0.29.1 was uploaded 30 Sep 2026. aimet-torch and aimet-onnx 2.41.0 (5 Oct 2026, BSD-3) exist; 2.21.0 (15 Dec 2025) and 2.22.0 (13 Jan 2026) bracket QAIRT 2.42, as claimed. qai-hub 0.56.0 (28 Sep), onnx 1.23.2 (6 Oct) and faiss-cpu 1.15.1 (16 Sep) are current.
    - **Verdict:** confirmed
    - **Action:** Pin these versions and archive the wheels. Install torch on the device only from the /whl/cpu index.
    - **Impact:** low
    - **Sources:**
      - https://download.pytorch.org/whl/cpu/torch/
      - https://pypi.org/pypi/aimet-torch/json
      - https://pypi.org/pypi/torchvision/json
      - https://pypi.org/pypi/qai-hub/json
  23.
    - **Claim in stack:** #48: TorchSig 2.2.0 (MIT), SigMF v1.2.6, SatNOGS DB CC BY-SA 4.0, RadioML CC BY-NC-SA benchmark only, WBSig53 regenerated
    - **Finding:** The torchsig 2.2.0 wheel (31 Aug 2026) has License-Expression MIT, needs Python >=3.10 and numpy >=2, has no Sig53/WBSig53 module, and contains an LFM builder with a 'radar' type, so the policy exclusion is needed. sigmf-python 1.13.0 (LGPL-3.0+) sets __specification__ = '1.2.6'. The SatNOGS DB about page says data are under 'Creative Commons Atribution-Share Alike v4.0'. DeepSig states all datasets are CC BY-NC-SA 4.0.
    - **Verdict:** confirmed
    - **Action:** Keep. Block the TorchSig LFM 'radar' type in the generator config, not only in the label map.
    - **Impact:** low
    - **Sources:**
      - https://pypi.org/pypi/torchsig/json
      - https://pypi.org/pypi/sigmf/json
      - https://db.satnogs.org/about/
      - https://www.deepsig.ai/datasets/
  24.
    - **Claim in stack:** #48: HisarMod2019.1 is CC BY (usable for redistributable weights)
    - **Finding:** The IEEE DataPort page confirms HisarMod2019.1.zip (5.13 GB), 26 classes, 780,000 signals. It is marked 'Open Access' but also says 'This dataset requires an IEEE DataPort Subscription', and it states no licence. The CC BY claim depends on the DataPort Terms of Service and is not on the page.
    - **Verdict:** corrected
    - **Action:** Mark the licence as 'unverified, DataPort ToS'. Keep HisarMod out of redistributable weights until the ToS clause is checked; use it for the IQ stage only as pretraining or benchmark.
    - **Impact:** low
    - **Sources:**
      - https://ieee-dataport.org/open-access/hisarmod-new-challenging-modulated-signals-dataset
  25.
    - **Claim in stack:** #49: AI Stack licence forbids EAR Part 744 end uses, lets QTI terminate without cause, forbids standalone distribution
    - **Finding:** The LICENSE.pdf in the 2.42 zip ('AI Stack License') contains all three. Section 8: 'QTI may at any time terminate this Agreement, without cause, upon notice'. Section 1: no licence 'to distribute or sublicense the Software on a standalone basis', although object-code distribution 'as incorporated in Your software application' is allowed. The export clause names Part 744 (UAV, military end use) and section 744.21. There is also an 'Unacceptable Risk Applications' list. Nothing conflicts with a receive-only lab.
    - **Verdict:** confirmed
    - **Action:** Keep the CPU ORT path as the licence hedge. Never publish images or containers that bundle QAIRT on their own.
    - **Impact:** low
    - **Sources:**
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
  26.
    - **Claim in stack:** Roadmap / #47: first live recordings from ISS SSTV series 34 (22-25.10.2026), sstv class at 437.550 MHz
    - **Finding:** The ARISS page (posted 14 Oct 2026) lists Series 34 'ARISS Hardware': Thursday 22 Oct to Sunday 25 Oct, times TBD, 437.55 MHz (+/- Doppler), Robot 36, 36 s on and 2 min off. Series 33 (2-6 Oct 2026) and Series 32/31 also used 437.550 MHz.
    - **Verdict:** confirmed
    - **Action:** Schedule from the ARISS times once they are published. Record SigMF on RTL-A with the static voice mask active.
    - **Impact:** low
    - **Sources:**
      - https://www.ariss.org/upcoming-sstv-events.html
  27.
    - **Claim in stack:** 5.4 / #9 / P2 rule: voice spectrogram only, no voice IQ kept; static voice mask plus NPU nfm_voice before raw writes
    - **Finding:** Policy-wise the class list and gate match user_requirements: no radar, drone, EW, military or fingerprint classes; occupancy-only cellular classes; ADS-B/AIS oracles drop ICAO, MMSI and positions; the 3-30 kHz and 225-400 MHz masks apply to all boxes. Gap: the static mask covers only 437.800, 436.795 and 145.800 MHz. Any other FM voice inside a pinned raw capture is excluded only if the unmeasured NPU nfm_voice detector finds it, so the rule currently depends on detector recall.
    - **Verdict:** new_risk
    - **Action:** Add a fail-closed rule in labrx: any unclassified FM-like 8-25 kHz carrier with speech-like duty in amateur or land-mobile allocations is treated as voice for raw-IQ retention (bins dropped before write) until nfm_voice recall is measured at 0.99 or better on the test set. Add a unit test.
    - **Impact:** medium
    - **Sources:** []
- **Current status oct 2026:** Status on 18 Oct 2026:
  
  - **QAIRT versions.** Qualcomm's revision history goes up to 2.50.0 (Aug 2026). 2.51.0 also exists: onnxruntime-qnn 2.7.0 (13 Oct 2026) states compatibility with it. AI Hub Workbench moved to 2.50.0 on 14 Sep 2026 and dropped 2.47; 2.42 was last listed in April 2026. No deprecation of v68, QCM6490 or SM7325 is announced.
  - **What Radxa ships.** Radxa still documents QAIRT 2.42.0.251225 with an Ubuntu 22.04 / Python 3.10 host. qcom-qnn-sdk-v68 0.1.0-2 (26 Jun 2026) is the 2.42.0.251225135753 build. The 2.42 SDK zip (1,543,955,191 B) can still be downloaded anonymously.
  - **Kernel.** The qcs6490-noble repo (24 Sep 2026) has moved to kernel 7.0.11-7. The 6.18.2-4 debs are gone from apt and remain only on the GitHub release.
  - **DSP firmware and FastRPC.** radxa-firmware-qcs6490 0.2.42 (17 Sep 2026) has rebuilt cdsp.mbn and adsp.mbn. They keep the c4-00004 / c9-00028 version strings but have new hashes, and adsp.mbn is a different size. FastRPC is at 1.0.7-3.
  - **Python packages.** onnxruntime 1.31.0 (9 Oct), onnxruntime-qnn 2.7.0 (13 Oct), torch 2.14.1 (30 Sep), aimet 2.41.0 (5 Oct), torchsig 2.2.0 (31 Aug), sigmf 1.13.0 (spec 1.2.6), scikit-learn 1.9.1 and onnx 1.23.2.
  - **End-of-life dates.** Python 3.10 reached end of life on 1 Oct 2026. Ubuntu 22.04 standard support ends 1 Jun 2027.
  - **Community reports.**
    - Qwen3.5-0.8B runs fully on HTP v68 with ORT 1.27.0 + QNN EP 2.3.0 (13 Sep 2026).
    - YOLOv8n outputs collapse with QAIRT 2.49 (16 Sep 2026).
    - CDSP fails on kernel 7.0.11-5 (31 Aug 2026).
    - Community Ubuntu 26.04.1 images now run kernel 7.2.9 with NPU device nodes (7 Oct 2026).
  - **Upcoming event.** ARISS SSTV Series 34 runs 22-25 Oct 2026 on 437.55 MHz, Robot 36.
  
  No hardware purchase belongs to this subsystem. All software is $0; an optional home GPU is the only cost.
- **Notes:** **Method.** I used primary sources only:
  - Radxa apt indices; downloaded and unpacked qcom-qnn-sdk-v68 and radxa-firmware-qcs6490 debs (version strings, sizes, SHA-256).
  - The QAIRT 2.42 SDK zip, inspected through HTTP range requests on its central directory: sdk.yaml, check-python-dependency, release notes, LICENSE.pdf, and the bundled HTP, overview, tools and SupportedOps docs. The full 1.5 GB was not downloaded.
  - PyPI JSON and the PyTorch wheel index.
  - The onnx VERSION_TABLE.
  - ONNX Runtime QNN EP docs and the onnxruntime-qnn release pages.
  - Radxa forum JSON for threads 30321, 30908, 31046, 31047, 31368, 31391, 31448, 31462, 31466 and 31574.
  - ARISS, SatNOGS, DeepSig, IEEE DataPort and endoflife.date.
  
  I used 4 WebSearch calls. The GitHub REST API is blocked in this session (403), so I read GitHub release pages with WebFetch instead.
  
  **Model numbers.** The gate duty cycles, the T2/T3 budgets, the E-S MAC and parameter count, and the CPU-mode GFLOP need are my own Python arithmetic. They are labelled as models.
  
  **Still unverified:**
  - Physical or grantable VTCM on QCS6490.
  - FP16 rejection on v68 (community log only).
  - Per-tile HTP latency on 2.42.
  - CPU-mode tiles/s on an A55.
  - GPU prices (the snapshots are undated).
  - The HisarMod licence.
  
  **Cross-subsystem items for the compute and software owners:**
  - The 6.18.2-4 kernel debs are gone from the apt repo; the meta packages now pull 7.0.11-7.
  - The firmware hashes changed in radxa-firmware-qcs6490 0.2.42.
  
  **Local evidence files:**
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/npu_rr/q6490_Packages
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/npu_rr/deb_qnn/qnn.deb
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/npu_rr/deb_fw/fw.deb
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/npu_rr/zip/entries.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/npu_rr/zip/qairt__2.42.0.251225__sdk.yaml
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/npu_rr/zip/qairt__2.42.0.251225__QAIRT_ReleaseNotes.txt
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/npu_rr/zip/lic.txt
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/npu_rr/zip/tools.txt
  
  **Edits to STACK.md:**
  - #39: the I/O pinning mechanism differs between the native QNN path and the ORT EP path.
  - #40: soc_model is 35 in the 2.42 docs.
  - #45 / 5.4: the home base needs two Python environments, and exports must use opset 21 or lower with IR version 10 for the 2.42 converter.
  - 5.4: the golden set must be pinned by SHA-256, not by version strings.
  - The voice rule needs a fail-closed fallback.

## Адверсаріальна перевірка (`verify`)

_Run `wf_9603e249-d87`_

- **Subsystem:** npu_training (stage 3, adversarial verification): SpecDet INT8 on HTP v68 / QAIRT 2.42.0.251225, CPU stage-2 embedder, Phase-0 gate, x86-64 Ubuntu 22.04 conversion host, ORT CPU fallback, class policy gate, data handling (no voice IQ), training budgets
- **Verdict:** The design holds up: a frozen INT8 SpecDet on HTP v68, built offline with QAIRT 2.42.0.251225 on an x86 host, plus FP32 stage 2 and training on the CPU. I re-checked the load-bearing facts against primary sources on 18 Oct 2026.
  
  **Byte-level checks I ran myself.** I downloaded the full SDK zip: 1,543,955,191 B, MD5 equal to its ETag, SHA-256 1a744ed7...e321. I re-extracted the deb. Its libQnnHtp, V68 stub, V68 skel, System, Prepare, Cpu and qnn-net-run are SHA-256 identical to the zip's aarch64-oe-linux-gcc11.2 and hexagon-v68 copies.
  
  **Corrections to STACK.md:**
  - #36: source the golden DSP set from radxa-firmware-qcs6490, not linux-msm/hexagon-dsp-binaries.
  - #39: offload_graph_io_quantization exists only on the ORT EP path.
  - #40: soc_model 35 is documented for QCM6490; the "93" claim is wrong. vtcm_mb=2 must be set explicitly.
  - #44: T2b (re-quantising the head on the device) cannot run on the device: there is no aarch64 Linux qairt-quantizer, and HTP online composition is "Not supported for QCLINUX". It moves to the home base.
  - #45: split the home base into separate environments. Keep AIMET and TorchSig out of the converter environment: QAIRT pins numpy 1.26.4, TorchSig needs numpy>=2, and aimet-torch/aimet-onnx 2.41.0 pull onnxscript, whose current 0.7.2 needs onnx>=1.17, so an unpinned install will most likely replace onnx 1.16.1.
  - #48: HisarMod's licence is unverified. TorchSig 2.2.0 also ships dmr, p25 and lfm-radar generators, so the generator list must be an allowlist.
  - Voice: replace the stage-1 heuristic with a frequency allowlist for raw IQ.
  - Default gate: with-Lime (user kept the Lime).
  
  **New risks:**
  - No published NPU pass on kernel 6.18.2-4. Every working report is on 6.18.2-3 (31208 fastrpc_test 3/3, PrismPhi).
  - ADSP_LIBRARY_PATH is semicolon-separated and must also reach libc++.so.1 / libc++abi.so.1 from the DSP tree.
  
  **Stage-2 citations refuted:**
  - 31208 is an unresolved failure. It is not evidence that the container works.
  - qualcomm/fastrpc #371 is a group-membership regression, not a DSP defect.
  
  All timing, power and accuracy numbers are still models until Phase 0.
- **Confirmed:**
  - Radxa qcs6490-noble index (Release 24 Sep 2026) still lists qcom-qnn-sdk-v68 0.1.0-2: Size 44,221,844, SHA256 306fd647b88902d170831980ca68a31d77d77923534e2070783fbeca132a6e54, Depends fastrpc-dev. Re-hashed locally: match.
  - Deb contents are SHA-256 identical to the 2.42 zip: libQnnHtp.so 6a04a4b8e276b863eb1ea8550f6855a3f8345412c5548f5679d26d7c2609b02a (2,316,960 B); libQnnHtpV68Stub.so 1436f5337f6d469cb6aca1095fc7426ab1ac61d030c4a39b2cdf013fe17d9ec4; libQnnHtpV68Skel.so 2cf8b6662cd9c98049c6ac0285d83c4b6966e6a1c9abb00aa843cb8e7e706b3c (9,040,240 B); qnn-net-run cd778f561e5f553b44acc9b4d63f909e9f728cf00f536108f6ebf0cff7adc264. libQnnSystem, libQnnHtpPrepare and libQnnCpu also match. The string AISW_VERSION 2.42.0 / v2.42.0.251225135753_193295 is present. The deb has no qairt-converter or qairt-quantizer.
  - SDK zip v2.42.0.251225.zip is still downloadable anonymously (301 to apigwx-aws.qualcomm.com). Full download on 18 Oct 2026: 1,543,955,191 B; MD5 8afeb63c22bd4bacb721648636c8829c, which equals the ETag; SHA-256 1a744ed72a813fc9dd4a29e31b1685f784786102fd45414d74915bb3351ae321; Last-Modified 7 Jan 2026.
  - sdk.yaml in the zip: QAIRT 2.42.0, os Ubuntu 22.04 / Windows 11, qnn_backend_api_version 2.18.0, onnx 1.16.1, onnxruntime 1.17.1, torch 1.13.1, onnxsimplifier 0.4.36. Release notes: 2.42.0 dated 01/06/2026, QNN API v2.32.0.
  - bin/check-python-dependency maps Ubuntu 22.04 only to Python 3.10 and pins numpy 1.26.4 and protobuf 3.19.6. Qualcomm's revision history adds Ubuntu 24.04 and Python 3.12 host support only in 2.47.0 (May 2026). Radxa's qairt-install page still says 'Please use QAIRT SDK version 2.42.0.251225' with an x86-64 Ubuntu 22.04 / Python 3.10 host.
  - Python 3.10 reached end of life on 2026-10-01 (last release 3.10.22). Ubuntu 22.04 standard support ends 2027-06-01, ESM to 2032-04-21 (endoflife.date).
  - onnx VERSION_TABLE at v1.23.2: 1.16.1 = IR 10 / opset 21; 1.17.0 = IR 10 / opset 22; 1.22.0 = IR 13 / opset 27; 1.23.x = IR 14 / opset 28. The 2.42 SupportedOps header says 'Opset <= 22'. The ORT 1.31.0 notes say its ONNX dependency stays at 1.22.0.
  - The 2.42 converter supports every op SpecDet uses: Conv 1/11/22, Clip 1/6/11/12, HardSwish 14/22, SpaceToDepth 1/13, QuantizeLinear and DequantizeLinear 10/13/19/21.
  - 2.42 overview table: QCM6490 is SOC Model 35, Hexagon V68, with toolchains aarch64-android, aarch64-ubuntu-gcc9.4 and aarch64-oe-linux-gcc11.2. 778G (SM7325) is also 35.
  - 2.42 HTP doc: weight sharing 'Only supports Hexagon v73 and onward' and only offline prepare on x86_Linux. The native KV-cache layout 'Cannot support v68 targets or lower'. Quantised 8-bit and 16-bit networks run on all SoCs; float runs via FP16 only 'on select Qualcomm SoCs'.
  - 2.42 capability table, HTP column: binary weight-only and quant-only updates, updatable static tensors and graph COMPOSITION are all 'Not supported for QCLINUX'. This supports a frozen detector and offline-only context binaries.
  - The 2.42 tools doc lists --input_dtype, --input_layout, --custom_io, --preserve_io_datatype, --quantization_overrides, --use_native_input_files, --use_per_channel_quantization, --act_bitwidth/--act_bw and --weights_bitwidth.
  - ORT QNN EP doc: offload_graph_io_quantization takes '0' or '1', default '1' (offload graph I/O Q/DQ to the CPU EP). vtcm_mb defaults to 0, soc_model to '0', enable_htp_fp16_precision to '1'.
  - Forum 31208 (20 Jul 2026, QAIRT 2.42 on host and board, soc_id 35, fastrpc 1.0.4-1, kernel 6.18.2-3): context binary fails with 'Request feature vtcm size with value 4194304 unsupported ... err 0x138d', even when rebuilt with vtcm_mb=8 or 0. DLC prepare on the device crashed the CDSP ('crash detected in cdsp'). fastrpc_test -a v68 passed 3/3. The same user later wrote 'I can run my model ... only able to pass 2MB' (31078 #9, 22 Jul).
  - radxa-pkg/fastrpc 1.0.7-2 changelog: 'change Q8B soc_id from 498 to 460 for 4MB vtcm'. setup-dsp.sh fakes soc_id 460 on SC8280XP boards. qcom,ids.h: 498 = QCS6490, 460 = SA8295P. The runtime therefore sizes VTCM by soc_id, and Radxa itself treats QCS6490 (498) as below 4 MB.
  - FP16/FP32 is unavailable on this HTP. AI Hub Models v0.64.0 (QAIRT 2.50) MobileNet-v2 card lists QCS6490 only as w8a8/w8a16, no float rows, while Snapdragon 8 Elite has float rows. Community logs agree: 'The SocModel doesn't support FP16' (31217).
  - AI Hub QCS6490 reference latencies (QAIRT 2.50, RB3 Gen 2): MobileNet-v2 (3.49 M params, 224x224) w8a8 1.064 ms ONNX / 1.325 ms DLC, w8a16 1.811 / 2.385 ms; YOLOv8-Det w8a8 4.013 ms DLC / 4.709 ms ONNX, w8a16 10.458 / 18.671 ms.
  - Forum 30908: 'Using newer context binary on old SDK' and err 5000 = 0x1388. Morgan (Radxa Team) wrote 'The new QNN context binary cannot run in older QAIRT runtime environments.' AI Hub release notes: 2.42 last listed 14 Apr 2026; 2.47 added 22 Jun (list 2.45/2.46/2.47); 2.49 on 17 Aug; 2.50 added and 2.47 removed on 14 Sep 2026.
  - radxa-firmware-qcs6490 0.2.42 (noble index, 24 Sep 2026; Size 13,394,364, SHA256 20d99dcb241376d62c67e87c4af9c6cf0a44e45aedf68e15d5ba9ebba95261b5), changelog 17 Sep 2026 'fix: update qcs6490 dsp firmware'. Commit b3d3840 says 'To support PM7250B Type-C controller'. Files: cdsp.mbn 3,612,672 B 644cb94cf4fe97ee47448ab698de6e0826ec1b9ba2ff9ed5009be501295e3de6 (CDSP.HT.2.5.c4-00004-KODIAK-1, UUID dated 20260804); adsp.mbn 14,012,896 B da35227f410fd8d1da949d6d660504501e724b9c248a9ddf18d7103ab588ac8e (ADSP.HT.5.5.c9-00028-KODIAK-2). The r2 adsp.mbn was 9,871,840 B (30321 #7); the commit's 3.95 MiB delta matches. fastrpc_shell_unsigned_3 is 960,884 B, 655a003255ae01d8b9c3eb2e978765d7dacbdf1ac5c7cf7ac8e171ac09f03dff, a c4-00004 build of 20250508. fastrpc_shell_3 is d6ef508a4051429bb231b8e1323683d847cb6dcc1b83af187c60f97c36a5a02d. The deb ships an initramfs hook that copies /lib/firmware/qcom/qcs6490/radxa/* into the initramfs. The DSP tree includes libc++.so.1 and libc++abi.so.1 but no QNN skel.
  - The qcs6490-noble index holds only kernel 7.0.11-7; the meta packages linux-image-radxa-dragon-q6a/-midstream 7.0.11-7 depend on linux-image-7.0.11-7-qcom. The GitHub release radxa-pkg/linux-qcom 6.18.2-4 (30 Mar) still has linux-image-6.18.2-4-qcom (65.1 MB), headers (8.61 MB) and the 6.18.2-4 meta debs. Release 6.18.2-3 also remains (image 64.4 MB, headers 8.61 MB).
  - fastrpc/libcdsprpc1 in the repo are only 1.0.7-3 (17 Sep 2026; fastrpc Conflicts/Replaces/Provides qcom-fastrpc1). The GitHub release fastrpc 1.0.4-1 still has its 21 assets, including fastrpc, libcdsprpc1, the listeners and fastrpc-test.
  - setup-dsp.sh (run by fastrpc.service on every boot) does 'rm -rf /usr/lib/dsp' and links it to /usr/share/qcom/qcs6490/radxa/dragon-q6a/dsp, chosen by the DT model string 'Radxa Dragon Q6A'.
  - Forum 31391 (31 Aug 2026): kernel 7.0.11-5 + fastrpc 1.0.7-1 + firmware 0.2.41 gives 0x80000600 and 'remotectl1 domains not supported'. rsetup's update_entry_overlays calls the undefined get_product_id. The reporter moved to Armbian. Forum 30241/30397: kernel upgrades broke the NPU, and Radxa staff advised against apt upgrade.
  - strongtz (Radxa Team, 30699 #20, 6 Aug 2026): 'fastrpc on cdsp doesn't need reserved DMA memory ... The no reserved DMA memory for FASTRPC error is misleading'; the pd-mapper role is now the in-kernel qcom_pd_mapper.
  - The Radxa 'Quick Validation' ModelScope bundle radxa/resnet50_qairt/6490 (committed 2 Sep 2025) has its own libQnnHtp.so (2,366,112 B) and V68 skel (8,100,444 B), which differ from 2.42. Morgan (30264): 2.37.1 was the version tested on the Q6A, and 2.42 'can still be used'.
  - Detection-head quantisation hazards: a concatenated YOLOv8 (1,84,8400) output on one INT8 scale gives 'garbage detections' (30899). Per-class split tensors come back 'literal zero' (31368). YOLOv8n collapses with QAIRT 2.49 (31462).
  - PrismPhi repo (Apache-2.0) and forum 31448: Qwen3.5-0.8B fully on Q6A HTP v68 with ORT 1.27.0 + onnxruntime-qnn 2.3.0 (QAIRT 2.47.0.260601114230), vtcm_mb=2, htp_arch=68, graph-I/O offload off, CPU fallback off, on kernel 6.18.2-3. Device-measured zero-input offsets needed 50 bias corrections; 'native error could increase even when CPU QDQ looked better'; 1,033 MatMul weights were per-tensor despite the per-channel option. Contexts were built on Windows x64, serially.
  - onnxruntime-qnn v2.3.0 states QAIRT 2.47.0 and v2.7.0 (13 Oct 2026) states QAIRT 2.51.0; neither mentions v68. PyPI has cp312 manylinux_2_34_aarch64 wheels for 2.1.0-2.7.0 (2.3.0: 78.7 MB).
  - onnxruntime-qnn issue #892 (open): HTP sessions whose Run() is called from many threads 'silently return wrong results'. Maintainer reproduced it on 17 Oct 2026 and wrote it is 'very possible it is an issue in the QNN API'. Seen on v73 / QNN EP 2.6.0.
  - ORT threading doc: intra-op threads default to the number of physical cores with auto-affinity; spinning 'Default: 1 (Enabled)' and 'consumes more CPU cycles, resources, and power'; it is disabled with session.intra_op.allow_spinning=0 and session.inter_op.allow_spinning=0.
  - PyPI: onnxruntime 1.31.0 (9 Oct 2026, MIT, >=3.11; last cp310 release 1.23.2; cp312 aarch64 21,420,804 B sha256 35758d7606d578ec5b9d65f6e8a1f488013194c3f6097038a3223cb26d35ef9a; x86_64 sha256 5e129d6c56abd53e659cb70f00a108d6824086470ff99c2e47a82e5786563db3). scikit-learn 1.9.1 (>=3.11; last cp310 1.7.2). torch 2.14.1 (30 Sep 2026, cp310 wheels). The /whl/cpu cp312 aarch64 wheel is 159,242,183 B, sha256 2af649994b36dffc627175c3f306d9e513a309b58d4619ac7107577613336454; the PyPI aarch64 wheel is 453,998,918 B. torchvision 0.29.1; aimet-torch/aimet-onnx 2.41.0 (5 Oct 2026); qai-hub 0.56.0; onnx 1.23.2 (6 Oct); faiss-cpu 1.15.1; torchsig 2.2.0 (MIT, numpy>=2); sigmf 1.13.0 (__specification__ 1.2.6).
  - SatNOGS DB: 'freely distributed under the Creative Commons Atribution-Share Alike v4.0 license'. DeepSig: all datasets CC BY-NC-SA 4.0.
  - AI Stack License in the 2.42 zip (LICENSE.pdf identical): termination 'without cause, upon notice'; no standalone distribution; EAR Part 744 / 744.21; the Unacceptable Risk list (biometrics, policing and similar) does not touch a receive-only lab.
  - ARISS page (entry 2026-10-14, re-read 18 Oct): Series 34 'ARISS Hardware', 22-25 Oct, times TBD, 437.55 MHz +/- Doppler, Robot 36, 36 s on / 2 min off.
  - Model arithmetic reproduced. E-S: 16.26 MMAC, 0.166 M params. T2: 7.81 TFLOP, so 4.5-10.8 min at 12-29 GFLOPS. T3: SpecDet-S 17.4 PFLOP gives 1.6-4.8 h and SpecDet-M 52.8 PFLOP gives 4.9-14.7 h at 1-3 TFLOPS; one epoch is 52.4 GB. Gate duty: 17.6x28 ms = 49.3%, 16.6x28 = 46.5%, 41x11.7 = 48.0%, 42.5x11.7 = 49.7%. CPU mode needs 2.3-3.5 GFLOP/s against a 15.2 GFLOPS A55 FP32 peak. Scaled by MACs from MobileNet-v2: SpecDet-S about 1.0-1.3 ms, SpecDet-M about 3.1-3.9 ms (model).
- **Corrections:**
  1.
    - **Claim in stack:** #37: device QAIRT from qcom-qnn-sdk-v68 0.1.0-2 equals the host 2.42 build; archive zip and deb with SHA-256
    - **Finding:** Upgraded from the stage-1 size match to SHA-256 identity of all runtime libraries and qnn-net-run against the full zip, which I downloaded and hashed: 1a744ed72a813fc9dd4a29e31b1685f784786102fd45414d74915bb3351ae321, MD5 = ETag 8afeb63c22bd4bacb721648636c8829c. The local copy is /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/s3npu/zipdl/v2.42.0.251225.zip.
    - **Verdict:** confirmed
    - **Action:** Write the zip SHA-256, the deb SHA-256 and the per-library hashes (libQnnHtp 6a04a4b8..., V68 stub 1436f533..., V68 skel 2cf8b666..., qnn-net-run cd778f56...) into the golden manifest. Copy the zip to the PC and the T7, and never redistribute it (licence).
    - **Impact:** high
    - **Sources:**
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/main/binary-arm64/Packages
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
  2.
    - **Claim in stack:** #39: input encoding pinned via offload_graph_io_quantization=0
    - **Finding:** This is an ORT QNN EP provider option (default '1') and appears nowhere in the 2.42 native tools. The native path pins I/O with the converter flags --input_dtype, --input_layout, --custom_io and --preserve_io_datatype, plus the quantizer flags --use_native_input_files and --quantization_overrides.
    - **Verdict:** corrected
    - **Action:** Native path: uint8 [1,32,128,128] input with a fixed scale (0.25 dB/LSB), pinned with those flags, and verified in the qnn-context-binary-utility dump. The ORT-EP path (optional) additionally sets offload_graph_io_quantization=0.
    - **Impact:** medium
    - **Sources:**
      - https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
  3.
    - **Claim in stack:** #40: soc_model 35 until checked ('QNN maps SM7325 to 35, QCM6490 to 93'); vtcm_mb=2
    - **Finding:** The 2.42 table gives QCM6490 = 35 and SM7325 = 35; no SoC in the table is 93. The board's Linux soc_id is 498 (QCS6490). In 31208, binaries built with vtcm_mb=0 or 8 still requested 4,194,304 B and failed with 0x138d. Radxa's fastrpc packaging treats soc_id 498 as below 4 MB.
    - **Verdict:** corrected
    - **Action:** Set soc_model 35, dsp_arch v68 and an explicit vtcm_mb=2 in every qnn-context-binary-generator config. CI rejects any binary whose dump shows VTCM above 2 MB. Drop the 35-vs-93 item.
    - **Impact:** medium
    - **Sources:**
      - https://forum.radxa.com/t/31208
      - https://forum.radxa.com/t/31078
      - https://raw.githubusercontent.com/radxa-pkg/fastrpc/main/debian/changelog
      - https://raw.githubusercontent.com/torvalds/linux/master/include/dt-bindings/arm/qcom,ids.h
  4.
    - **Claim in stack:** #36: golden FastRPC set 'from linux-msm/hexagon-dsp-binaries' (CDSP c4-00004, ADSP c9-00028, shells)
    - **Finding:** The linux-msm/hexagon-dsp-binaries page shows qcs6490 and RB3gen2 trees but does not show CDSP.HT.2.5.c4-00004, and it mentions no Radxa board. Every working Q6A report uses the matched set from radxa-firmware-qcs6490. Mixing sources gives 0x80000600 (31078 #8: dpkg -V showed modified shells).
    - **Verdict:** corrected
    - **Action:** Source the golden set only from radxa-firmware-qcs6490: either the r2-installed files or 0.2.42, chosen by Phase 0. Pin hexagon-dsp-binaries*, linux-firmware-dragonwing and qcom-fastrpc1 to -1 if they ever appear.
    - **Impact:** high
    - **Sources:**
      - https://github.com/linux-msm/hexagon-dsp-binaries
      - https://forum.radxa.com/t/31078
      - https://radxa-repo.github.io/noble/pool/main/r/radxa-firmware/radxa-firmware-qcs6490_0.2.42_all.deb
  5.
    - **Claim in stack:** 5.4 / #36: golden NPU firmware set identified by version string (c4-00004 / c9-00028)
    - **Finding:** 0.2.42 keeps both version strings but carries new images (UUIDs dated 20260804; adsp.mbn 14,012,896 B against r2's 9,871,840 B; cdsp.mbn same size, new build). The shell is unchanged (c4-00004, 20250508). The hook copies whatever is on disk into the initramfs.
    - **Verdict:** new_risk
    - **Action:** Identify the set by SHA-256 only: cdsp.mbn, adsp.mbn, both shells, the whole dsp/cdsp tree (including libc++.so.1 / libc++abi.so.1), fastrpc and libcdsprpc1 versions. Run the hash check before every update-initramfs and before each NPU start (dpkg -V clean; dpkg -S single owner). apt-mark hold radxa-firmware-qcs6490 and fastrpc*.
    - **Impact:** high
    - **Sources:**
      - https://radxa-repo.github.io/noble/dists/noble/main/binary-arm64/Packages
      - https://github.com/radxa-pkg/radxa-firmware/commit/b3d3840
      - https://forum.radxa.com/t/30321
  6.
    - **Claim in stack:** #23 / 5.4: hold linux-image-6.18.2-4-qcom with the golden NPU set
    - **Finding:** 6.18.2-4 is gone from apt; the meta packages pull 7.0.11-7, and CDSP FastRPC fails on 7.0.11-5 (31391). The GitHub release 6.18.2-4 keeps image, headers and meta debs. I found no published NPU pass on 6.18.2-4. The passes I found are on 6.18.2-3 (31208 fastrpc_test 3/3; PrismPhi quickstart) and Armbian 6.18.2-current (30850). The only 6.18.2-4 report (30699 #16) fails.
    - **Verdict:** new_risk
    - **Action:** Archive the 6.18.2-4 and 6.18.2-3 image, headers and meta debs from the GitHub releases with SHA-256. Install the 6.18.2-4 meta and hold. Phase 0 tests the NPU on 6.18.2-4 first and falls back to 6.18.2-3 only for the NPU decision (compute must confirm that 6.18.2-3 has the NO_HZ_FULL/RCU_NOCB config the Lime build needs). Shared with compute.
    - **Impact:** high
    - **Sources:**
      - https://github.com/radxa-pkg/linux-qcom/releases/tag/6.18.2-4
      - https://github.com/radxa-pkg/linux-qcom/releases/tag/6.18.2-3
      - https://forum.radxa.com/t/31208
      - https://forum.radxa.com/t/30699
      - https://forum.radxa.com/t/31391
  7.
    - **Claim in stack:** #45: one ubuntu:22.04 / Python 3.10 home-base container (stage 1: split into py3.10 QAIRT+AIMET and py3.12 training)
    - **Finding:** Confirmed that it must be split. AIMET also does not belong in the converter env. QAIRT pins numpy 1.26.4 and protobuf 3.19.6 and was tested with onnx 1.16.1. aimet-torch 2.41.0 requires onnxscript>=0.2.0 and aimet-onnx 2.41.0 requires onnxscript>=0.4.0; onnxscript 0.7.2 requires onnx>=1.17, and both list onnx unpinned. An unpinned pip install will very likely replace onnx 1.16.1 with 1.23.2 (IR 14) (inferred from the metadata, not tried). TorchSig 2.2.0 needs numpy>=2. ORT 1.31.0 and sklearn 1.9.1 have no cp310 wheels.
    - **Verdict:** corrected
    - **Action:** Env A, converter (frozen, offline): ubuntu:22.04, apt python3.10, QAIRT 2.42 with constraints onnx==1.16.1 and numpy==1.26.4; no AIMET, no TorchSig. Env B, train/parity: Ubuntu 24.04 py3.12 with torch 2.14.1, torchvision 0.29.1, onnxruntime 1.31.0, scikit-learn 1.9.1, onnx 1.23.2, torchsig 2.2.0, sigmf 1.13.0. Env C (optional): AIMET in its own venv; it hands over ONNX plus encodings JSON to env A's --quantization_overrides.
    - **Impact:** medium
    - **Sources:**
      - https://pypi.org/pypi/aimet-torch/json
      - https://pypi.org/pypi/aimet-onnx/json
      - https://pypi.org/pypi/onnxscript/json
      - https://pypi.org/pypi/onnxruntime/json
      - https://pypi.org/pypi/scikit-learn/json
      - https://pypi.org/pypi/torchsig/json
  8.
    - **Claim in stack:** Home base export: torch 2.14.1 / onnx 1.23.2, opset/exporter open
    - **Finding:** onnx 1.23.x writes IR 14 / opset 28 by default (onnx.helper.make_model uses the current IR). The 2.42 converter env has onnx 1.16.1 (IR 10 / opset 21) and the table says 'Opset <= 22'. ORT 1.31 supports up to ONNX 1.22 (opset 27).
    - **Verdict:** new_risk
    - **Action:** Export at opset 17-21, then set model.ir_version=10 explicitly. CI runs the onnx 1.16.1 checker, qairt-converter and qairt-quantizer in env A, plus an ORT 1.31 load in env B, on every model.
    - **Impact:** medium
    - **Sources:**
      - https://raw.githubusercontent.com/onnx/onnx/v1.23.2/onnx/helper.py
      - https://github.com/microsoft/onnxruntime/releases/tag/v1.31.0
  9.
    - **Claim in stack:** #44: T2b experimental re-quantisation of the head on the device
    - **Finding:** The 2.42 zip has qairt-converter and qairt-quantizer only for x86_64 Linux and Windows. The aarch64-oe Python libs lack libPyIrQuantizer and libPyIrOptimizer. The HTP capability table marks graph composition and updatable static tensors 'Not supported for QCLINUX'. DLC prepare on the device crashed the CDSP (31208).
    - **Verdict:** corrected
    - **Action:** Remove T2b from the device. Re-quantisation and context rebuild happen only on the home base (env A) and return a new golden-gated context binary. On the device: T0, T1 and T2 on the CPU only. Optionally keep libQnnHtpPrepare.so off the inferd-htp library path, after the load-without-prepare bench test passes.
    - **Impact:** medium
    - **Sources:**
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
      - https://forum.radxa.com/t/31208
  10.
    - **Claim in stack:** #39 / #42: ReLU/ReLU6/HardSwish; grouped vs depthwise
    - **Finding:** 2.42 guidelines: ReLU is the best activation, and ReLU/ReLUX/ReLUMinMax are preferred for A8/A16. HardSwish/PReLU fusion is described for 'The latest hardware' and requires that the preceding conv is not used elsewhere. On grouped convolution the guide says 'try to have more channels in a group up to the hardware capacity of 32'. Its 'group size 1' means normal convolution, not depthwise.
    - **Verdict:** corrected
    - **Action:** Default to ReLU/ReLU6 (Clip 0..6) everywhere. Use HardSwish only after a Phase-0 profile shows it fused on v68. Keep channels at multiples of 32. Benchmark SpecDet-G (grouped, at most 32 channels per group) against depthwise S; promote G if its AP is at least S's.
    - **Impact:** low
    - **Sources:**
      - https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.42.0.251225/v2.42.0.251225.zip
  11.
    - **Claim in stack:** #36: DT overlay adds shared-dma-pool memory-region to both fastrpc nodes
    - **Finding:** Radxa Team (strongtz, 30699 #20) says CDSP FastRPC does not need reserved DMA memory and that the warning is misleading. fastrpc_test passed 3/3 without the overlay (31208); 31391 added it and still failed.
    - **Verdict:** corrected
    - **Action:** Make the overlay optional. Test without it first. If it is used, install it via the systemd-boot entry, never through rsetup (get_product_id bug), and CI checks that the loader entry names qcs6490-radxa-dragon-q6a.dtb.
    - **Impact:** low
    - **Sources:**
      - https://forum.radxa.com/t/30699
      - https://forum.radxa.com/t/31391
  12.
    - **Claim in stack:** 5.4 inferd-htp sandbox (no DSP library path, device nodes or group given)
    - **Finding:** The skel is installed only in /usr/lib/aarch64-linux-gnu. /usr/lib/dsp is recreated on every boot by setup-dsp.sh. The skel needs libc++.so.1 / libc++abi.so.1 on the DSP search path (30850: their absence plus a 2.46/2.42 stub/skel mismatch caused 0x80000406). Node owners are root:fastrpc and fastrpc:fastrpc with mode crw-r----- (31078 #4). Since fastrpc 1.0.6 the fastrpc group is created at startup (qualcomm/fastrpc #371).
    - **Verdict:** new_risk
    - **Action:** Unit settings: User=labnpu; SupplementaryGroups=fastrpc; Environment=ADSP_LIBRARY_PATH="/opt/lab/npu/2.42/dsp;/usr/lib/dsp/cdsp" (semicolon list; read-only golden copy of the skel); LD_LIBRARY_PATH=/opt/lab/npu/2.42/lib; DevicePolicy=closed with DeviceAllow /dev/fastrpc-cdsp rw, /dev/fastrpc-cdsp-secure rw, /dev/dma_heap/system rw; no PrivateDevices; Requires/After=fastrpc.service cdsprpcd.service. Log the backend, stub and skel 'build version' lines at start.
    - **Impact:** high
    - **Sources:**
      - https://raw.githubusercontent.com/radxa-pkg/fastrpc/main/fastrpc/usr/libexec/fastrpc/setup-dsp.sh
      - https://forum.radxa.com/t/30850
      - https://forum.radxa.com/t/31078
      - https://github.com/qualcomm/fastrpc/issues/371
  13.
    - **Claim in stack:** 5.4: fastrpc and libcdsprpc1 versions held
    - **Finding:** The repo now offers only 1.0.7-3. 1.0.4-1 (the working combination in 31208) survives only as a GitHub release. #371's 1.0.6 regression on RB3 Gen 2 traces to fastrpc group membership after group creation moved to startup; it is hidden in the debs by a udev patch. It is a permission issue, not shown to be a DSP defect.
    - **Verdict:** new_risk
    - **Action:** Archive 1.0.4-1 and 1.0.7-3 (fastrpc, libcdsprpc1, listeners, fastrpc-test, fastrpc-dev) with SHA-256. Run the Phase-0 matrix, then hold the one that passes. Never let apt move them.
    - **Impact:** high
    - **Sources:**
      - https://github.com/radxa-pkg/fastrpc/releases
      - https://github.com/qualcomm/fastrpc/issues/371
      - https://forum.radxa.com/t/31208
  14.
    - **Claim in stack:** C19 / 5.4: inferd-cpu ORT 1.31 on A55, CPUQuota 100%, 4-6 tiles/s
    - **Finding:** Not measured anywhere. With ORT defaults (threads = physical cores, auto-affinity, spinning on), the threads would spin against the quota. The rate needs 2.3-3.5 GFLOP/s from one A55 (15.2 GFLOPS FP32 peak, model). With a QDQ model, ORT's CPU kernels can use the A55's SDOT instructions.
    - **Verdict:** unverified
    - **Action:** Set intra_op_num_threads=1, inter_op_num_threads=1, session.intra_op.allow_spinning=0 and session.inter_op.allow_spinning=0; set no ORT affinity and let systemd pin. Prefer the QDQ model if its AP holds. If one A55 gives fewer than 4 tiles/s, raise K or allow CPUQuota of about 150% on CPU0-3; never take time from the A78s.
    - **Impact:** medium
    - **Sources:**
      - https://onnxruntime.ai/docs/performance/tune-performance/threading.html
      - https://pypi.org/pypi/onnxruntime/json
  15.
    - **Claim in stack:** C20: HTP gates (28 ms without Lime; 11.7 ms or 41 tiles/s with Lime)
    - **Finding:** The arithmetic is correct. The user has now KEPT the Lime, so the with-Lime gate is the default. MAC scaling from AI Hub (QAIRT 2.50) predicts SpecDet-S at about 1.0-1.3 ms graph time; FastRPC per-call overhead is unknown.
    - **Verdict:** confirmed
    - **Action:** Default gate: p99 at most 11.7 ms at 42.5 tiles/s, otherwise cap at 41 tiles/s. Keep the 28 ms gate for the no-Lime profile. In Phase 0, log per-call overhead and run an INA228 sweep over perf modes and RPC polling.
    - **Impact:** medium
    - **Sources:**
      - https://huggingface.co/qualcomm/MobileNet-v2
      - https://huggingface.co/qualcomm/YOLOv8-Detection
  16.
    - **Claim in stack:** #39 / #42: separate Clip-bounded outputs obj, box, fam(12), occ; AP gate INT8 vs FP32 within 2 points
    - **Finding:** Shared or calibration-derived scales collapse detection heads on QCS6490 (30899, 31368, 31462). CPU QDQ did not predict HTP error in PrismPhi's port (a W8A16 transformer, so this extrapolates to SpecDet).
    - **Verdict:** new_risk
    - **Action:** Keep fam as one 12-channel tensor. Fix every output encoding to its Clip range via --quantization_overrides, and make calibration class-balanced. Measure the AP gate only from HTP outputs (qnn-net-run 2.42). Add a zero-input probe and per-channel non-zero-variance checks. Audit per-channel scale counts for every Conv weight in the dump. Give inferd-cpu its own thresholds.
    - **Impact:** medium
    - **Sources:**
      - https://forum.radxa.com/t/30899
      - https://forum.radxa.com/t/31368
      - https://forum.radxa.com/t/31462
      - https://github.com/PrismPhi/radxa-dragon-q6a-qwen3.5-0.8b-qcs6490-qnn-npu
  17.
    - **Claim in stack:** #38 / question 7: Set B removed
    - **Finding:** onnxruntime-qnn 2.3.0 = QAIRT 2.47.0, with cp312 manylinux_2_34_aarch64 wheels (78.7 MB) on PyPI. It ran fully on Q6A v68 (31448). The ORT floor is >=1.24.2 per PyPI metadata and the 2.3.0 bug-fix note, not 1.24.1. The wheels bundle their own QNN libraries.
    - **Verdict:** new_option
    - **Action:** Keep Set B removed by rule, and never pip-install onnxruntime-qnn into any device venv. Offer Set B (ORT 1.27.0 + onnxruntime-qnn 2.3.0) only as an answer to question 7, with its own golden set and soak.
    - **Impact:** medium
    - **Sources:**
      - https://github.com/onnxruntime/onnxruntime-qnn/releases/tag/v2.3.0
      - https://pypi.org/pypi/onnxruntime-qnn/json
      - https://forum.radxa.com/t/31448
  18.
    - **Claim in stack:** #48: TorchSig 2.2.0; block lfm-radar
    - **Finding:** The TorchSig 2.2.0 signal list also includes 'dmr' and 'p25' (family 'lmr'). 'lfm-radar' maps to family 'chirp' together with 'lfm-data' and 'chirpss' (LoRa CSS), so a family-level label would hide radar inside 'chirp'.
    - **Verdict:** new_risk
    - **Action:** Use a generator ALLOWLIST by signal name. Exclude lfm-radar, dmr and p25, and never use TorchSig family labels. CI fails if any banned name appears in a dataset manifest. LoRa/chirpss is used only for lora_sat.
    - **Impact:** medium
    - **Sources:**
      - https://pypi.org/pypi/torchsig/json
  19.
    - **Claim in stack:** #48: HisarMod2019.1 is CC BY
    - **Finding:** The IEEE DataPort page states no licence. It says both 'Open Access' and 'requires an IEEE DataPort Subscription'. I could not read the DataPort ToS (403/404, no WebSearch budget left).
    - **Verdict:** unverified
    - **Action:** Mark as 'unverified (DataPort ToS)'. Use it only for pretraining or benchmarks, and keep it out of redistributable weights.
    - **Impact:** low
    - **Sources:**
      - https://ieee-dataport.org/open-access/hisarmod-new-challenging-modulated-signals-dataset
  20.
    - **Claim in stack:** 5.4 / P2: no voice IQ kept; static voice mask plus NPU nfm_voice before raw writes
    - **Finding:** The static mask covers only 437.800, 436.795 and 145.800 MHz, so any other FM voice depends on unmeasured nfm_voice recall. Stage 1's 'speech-like duty' heuristic is not deterministic.
    - **Verdict:** new_risk
    - **Action:** Make raw-IQ retention fail-closed by an allowlist. Raw bins are written only inside (a) predicted data-downlink windows (SatNOGS transmitter with a data mode, pass +/- Doppler + margin) or (b) bench/conducted captures. In amateur 144-146 / 430-440 MHz, PMR446, land-mobile, marine VHF and aero 118-137 MHz, bins outside allowlist windows are excised before write, whatever the NPU says. nfm_voice boxes stay spectrogram-only. Add a unit test with synthetic NFM voice at 145.500 / 433.500 / 446.006 MHz inside a pinned capture.
    - **Impact:** medium
    - **Sources:** []
- **New risks:**
  - No published NPU success on kernel 6.18.2-4; all working Q6A NPU reports are on 6.18.2-3 or Armbian 6.18.2-current. The 6.18.2-3 debs exist only on the GitHub release; archive them now.
  - AIMET 2.41.0 in the converter env would likely replace QAIRT's tested onnx 1.16.1 via onnxscript>=0.4 (0.7.2 needs onnx>=1.17, both list onnx unpinned; inferred from metadata). TorchSig needs numpy>=2 while QAIRT pins 1.26.4. Each tool needs its own environment with a constraints file.
  - On the device, HTP online composition and updatable tensors are 'Not supported for QCLINUX', and there is no aarch64 qairt-quantizer. Any on-device re-prepare or requantisation (T2b) is impossible; DLC prepare crashed the CDSP in 31208.
  - The 2.42 generator for soc_model 35 requests 4 MB VTCM even with vtcm_mb=0 or 8 (31208). Without an explicit vtcm_mb=2, every binary fails with 0x138d.
  - ADSP_LIBRARY_PATH is a semicolon-separated list. The QNN V68 skel needs libc++.so.1 / libc++abi.so.1 from the matched DSP tree. /usr/lib/dsp is deleted and relinked on every boot.
  - TorchSig 2.2.0 ships dmr, p25 and lfm-radar generators. The 'chirp' family label merges lfm-radar with LoRa CSS, so a policy gate based on families would leak radar into training.
  - radxa-firmware-qcs6490 0.2.42 changed adsp.mbn (+3.95 MiB) 'to support PM7250B Type-C controller' (ADSP-side Type-C/PD). Choosing the r2 or the 0.2.42 DSP set may change USB-C behaviour. Flag for power/compute.
  - fastrpc >= 1.0.6 creates the fastrpc group at service start (qualcomm/fastrpc #371). Service accounts and udev rules must reference that group after it exists, or sessions fail with permission-type errors.
  - The QNN multi-thread wrong-result bug (onnxruntime-qnn #892, maintainer suspects the QNN API) is unverified on v68. Keep one thread per context and run a canary hash during the soak.
  - SatNOGS DB data are CC BY-SA 4.0. ShareAlike may be argued to attach to published weights; keep the per-record licence field and exclude BY-SA and NC data from any weights you publish until this is reviewed.
  - QAIRT 2.42's own tested pins are inconsistent: protobuf 3.19.6, while onnx 1.16.x needs protobuf>=3.20.2. Run pip check in env A and pin the protobuf that the converter actually imports.
  - The Python 3.10 base of env A has been end of life since 2026-10-01. Ubuntu's apt python3.10 gets Canonical fixes only to 2027-06-01 (ESM after that). Keep env A offline and use it only for conversion.
- **Refuted findings:**
  1.
    - **Finding:** Stage 2: 'A matched x86 container with QAIRT 2.42.0.251225 ... produced binaries that load on the Q6A (forum 31208, once vtcm was right).'
    - **Why:** Forum 31208 has one post and it is an unresolved failure: 0x138d at a 4 MB VTCM request, and a CDSP crash on DLC prepare. Loading is only implied later by the same user in 31078 #9 ('I can run my model ... only able to pass 2MB'), without build details. The evidence is indirect, not from 31208.
  2.
    - **Finding:** Stage 2: 'fastrpc 1.0.6/1.0.7 have open problems' citing qualcomm/fastrpc #371 as a CDSP defect.
    - **Why:** #371 concerns qcom-deb-images on RB3 Gen 2. The maintainer traced it to the fastrpc group being created at startup, so the user was not in the group, and it is worked around with a udev patch. It shows a packaging and permission regression, not a DSP-side failure on Radxa.
  3.
    - **Finding:** Stage 1: 'grouped convolutions with up to 32 channels per group are more efficient than group size 1 (depthwise)'; 'HardSwish/PReLU fuse in A8/A16'.
    - **Why:** In the 2.42 guide, 'group size 1' means normal convolution, and the guide makes no comparison with depthwise. Fusion is stated for 'The latest hardware' with a constraint (the preceding conv is not used elsewhere), and ReLU/ReLUMinMax are preferred for A8. The design direction survives as an inference to benchmark, not as a documented fact.
  4.
    - **Finding:** Stage 1: onnxruntime-qnn 2.7.0 requires 'ORT >=1.24.1'.
    - **Why:** PyPI metadata for 2.7.0 lists onnxruntime>=1.24.2, and the 2.3.0 release notes say the floor was 'raised to >= 1.24.2'.
  5.
    - **Finding:** Community claims relayed in stage 2 (31217, Dual-O): 'firmware caps at QNN interface 2.32 / QAIRT 2.46+ all fail' and 'per-channel INT8 needs ORT 1.24+ / QAIRT 2.45+'.
    - **Why:** QAIRT 2.47 (QNN EP 2.3.0) runs fully on a Q6A v68 (31448), and 2.46 runs in 31047 (30850 also swapped the mbn files). The 2.42 qairt-quantizer documents --use_per_channel_quantization, so per-channel is available on the native 2.42 path. It must still be audited in the dump, because PrismPhi found per-tensor MatMul weights.
  6.
    - **Finding:** STACK #40: 'QNN maps SM7325 to 35, QCM6490 to 93'.
    - **Why:** The 2.42 'Supported Snapdragon devices' table lists both as SOC Model 35, and no device is 93.
  7.
    - **Finding:** STACK #48: 'HisarMod2019.1 (CC BY) — licences verified'.
    - **Why:** The dataset page states no licence at all. The CC BY claim depends on DataPort ToS text that I could not read.
- **Corrected spec:** NPU subsystem v1.1 (18 Oct 2026). Numbers marked (model) are not measured.
  
  DEVICE RUNTIME (golden set, identified by SHA-256 only)
  
  QAIRT runtime: QAIRT 2.42.0.251225 from qcom-qnn-sdk-v68 0.1.0-2.
  - Deb: 44,221,844 B, SHA-256 306fd647b88902d170831980ca68a31d77d77923534e2070783fbeca132a6e54.
  - Byte-identical to the zip's lib/aarch64-oe-linux-gcc11.2 and lib/hexagon-v68/unsigned copies:
    - libQnnHtp.so 6a04a4b8e276b863eb1ea8550f6855a3f8345412c5548f5679d26d7c2609b02a
    - libQnnHtpV68Stub.so 1436f5337f6d469cb6aca1095fc7426ab1ac61d030c4a39b2cdf013fe17d9ec4
    - libQnnHtpV68Skel.so 2cf8b6662cd9c98049c6ac0285d83c4b6966e6a1c9abb00aa843cb8e7e706b3c
    - qnn-net-run cd778f561e5f553b44acc9b4d63f909e9f728cf00f536108f6ebf0cff7adc264
  - SDK zip v2.42.0.251225.zip: 1,543,955,191 B, MD5 8afeb63c22bd4bacb721648636c8829c, SHA-256 1a744ed72a813fc9dd4a29e31b1685f784786102fd45414d74915bb3351ae321.
  - Never redistribute the zip; this is an AI Stack licence term.
  
  Kernel:
  - linux-image-6.18.2-4-qcom, its headers and the 6.18.2-4 meta packages, from the GitHub release radxa-pkg/linux-qcom 6.18.2-4. Hold them.
  - Archive 6.18.2-3 (image 64.4 MB) as the NPU fallback.
  - The 7.0.11-x kernels are not used for the NPU.
  
  DSP firmware: only from radxa-firmware-qcs6490. Phase 0 picks one of two candidate sets:
  - Set A: the r2-installed files, hashed at bring-up.
  - Set B: 0.2.42.
    - cdsp.mbn 644cb94cf4fe97ee47448ab698de6e0826ec1b9ba2ff9ed5009be501295e3de6 (3,612,672 B)
    - adsp.mbn da35227f410fd8d1da949d6d660504501e724b9c248a9ddf18d7103ab588ac8e (14,012,896 B)
    - fastrpc_shell_unsigned_3 655a003255ae01d8b9c3eb2e978765d7dacbdf1ac5c7cf7ac8e171ac09f03dff
    - fastrpc_shell_3 d6ef508a4051429bb231b8e1323683d847cb6dcc1b83af187c60f97c36a5a02d
  - Both sets report the same strings, CDSP.HT.2.5.c4-00004-KODIAK-1 and ADSP.HT.5.5.c9-00028-KODIAK-2. Only the SHA-256 decides.
  
  fastrpc userspace:
  - Candidates: 1.0.4-1 (GitHub release) and 1.0.7-3 (repo; fastrpc 1298866a..., libcdsprpc1 2a6c063e..., fastrpc-test 8375a9ac...). Hold the one that passes Phase 0.
  - Pin hexagon-dsp-binaries*, linux-firmware-dragonwing, firmware-qcom-dsp and qcom-fastrpc1 to -1.
  - The initramfs hook comes from the firmware package. Run the hash check before every update-initramfs.
  - The shared-dma-pool overlay is optional: only if Phase 0 needs it, and only via the systemd-boot entry.
  
  inferd-htp (systemd unit, native, never in a container):
  - User=labnpu, SupplementaryGroups=fastrpc.
  - ADSP_LIBRARY_PATH="/opt/lab/npu/2.42/dsp;/usr/lib/dsp/cdsp"
  - LD_LIBRARY_PATH=/opt/lab/npu/2.42/lib
  - DevicePolicy=closed. DeviceAllow /dev/fastrpc-cdsp rw, /dev/fastrpc-cdsp-secure rw, /dev/dma_heap/system rw.
  - Requires/After=fastrpc.service cdsprpcd.service.
  - CPUAffinity=0-3, MemoryMax=1G, WatchdogSec=5.
  - One thread creates the backend, device and context and calls every graphExecute; no shared contexts.
  - Loads offline context binaries only: no DLC, no online prepare, no on-device generator.
  - Restart ladder:
    1. Re-create the context.
    2. Stop/start the CDSP remoteproc, wait at least 15 s, run fastrpc_test.
    3. Mark the NPU dead, go to CPU mode, and reboot only between passes.
  
  MODEL / BUILD
  
  Detector: SpecDet-S by default; M and G are in the Phase-0 benchmark.
  - Input: uint8 [1,32,128,128], made by a 4x4 space-to-depth of 2x512x512 dB tiles at 0.25 dB/LSB, done in the tiler.
  - Input pinned with the converter flags --input_dtype, --input_layout, --custom_io and --preserve_io_datatype, plus the quantizer flag --use_native_input_files. Checked with qnn-context-binary-utility.
  - Outputs: obj, box, fam (one 12-channel tensor) and occ on a 64x64 grid. Each output is Clip-bounded, and its encoding is fixed to the Clip range via --quantization_overrides.
  - Quantisation: w8a8 with --use_per_channel_quantization. Calibration is class-balanced.
  - Architecture:
    - ReLU/ReLU6 activations; HardSwish only after a v68 fusion check.
    - Channels in multiples of 32; grouped conv (at most 32 channels per group) preferred over depthwise if AP holds.
    - Static shapes; Conv2d 1xK.
    - No Softmax, Sigmoid, TopK, NMS, RNN or attention in the graph.
  - ONNX export: opset 17-21, ir_version=10 set explicitly.
  - Generator settings: dsp_arch v68, soc_model 35, vtcm_mb=2 explicit. CI rejects any binary above 2 MB VTCM.
  - FP16/FP32 on HTP: not available. A16W8 gets one Phase-0 test on the fam head only, with a budget of 2-4x the INT8 latency.
  
  GATES
  
  Throughput, default with Lime: p99 at most 11.7 ms at 42.5 tiles/s, otherwise cap at 41 tiles/s. Without Lime: p99 at most 28 ms at 16.6-17.6 tiles/s.
  - Expected graph time: SpecDet-S about 1.0-1.3 ms (model).
  - Perf mode: the lowest-power DCVS mode that meets p99 with 2x margin. RPC polling is off by default.
  
  Accuracy, measured on HTP outputs from 2.42 qnn-net-run:
  - INT8 AP at least FP32 AP minus 2 points.
  - Every output channel has non-zero variance.
  - The zero-input probe stays within the manifest tolerance.
  - The per-channel scale count is correct for every Conv weight.
  
  Soak: 8 h with fault injection. A canary tile runs every 5 min and its output hash must equal the golden one. Includes one forced CDSP crash.
  
  CPU PATH
  
  inferd-cpu:
  - onnxruntime 1.31.0 cp312 manylinux_2_28_aarch64 (21,420,804 B, sha256 35758d7606d578ec5b9d65f6e8a1f488013194c3f6097038a3223cb26d35ef9a).
  - intra_op_num_threads=1, inter_op_num_threads=1, session.intra_op.allow_spinning=0, session.inter_op.allow_spinning=0.
  - CPUAffinity 0-3, CPUQuota 100%.
  - QDQ model if its AP holds.
  - Target at least 4 tiles/s on one A55 (unmeasured). When the HTP is down, CPU mode runs the about-5 tiles/s schedule with the 'reduced coverage' chip.
  
  Stage 2, FP32 on CPU:
  - E-S embedder: 16.3 MMAC / 0.166 M params (model).
  - Prototypes and a cosine head with an open 'unknown' output.
  - torch 2.14.1+cpu from the /whl/cpu index only (159,242,183 B, sha256 2af649994b36dffc627175c3f306d9e513a309b58d4619ac7107577613336454). faiss-cpu 1.15.1, scikit-learn 1.9.1.
  - Never move E-S to HTP INT8 without an embedding-diversity test.
  
  Training:
  - On the device: T0 under 0.1 s, T1 under 1 s, and T2 on CPU4-6 (4.5-10.8 min full, 1-3 min with frozen layers, model). T2 runs under the C19 guards: no pass for 15 min, SoC below 75 C, battery above 25% or charging, MemoryMax 2 GiB.
  - At the home base only: T2b requantisation and T3 retraining. T3 budget: SpecDet-S 1.6-4.8 h and SpecDet-M 4.9-14.7 h per 100 epochs of 100k tiles (model). A GPU is optional and needed only for T3; prices are unverified.
  
  HOME BASE
  
  Env A, converter (frozen and offline):
  - ubuntu:22.04 container, apt python3.10, QAIRT 2.42 at the zip hash above.
  - Constraints file: onnx==1.16.1, numpy==1.26.4; run pip check.
  - No AIMET and no TorchSig in this env.
  - Run qnn-context-binary-generator jobs one at a time; keep the logs.
  
  Env B, training and parity: Ubuntu 24.04, Python 3.12, with torch 2.14.1, torchvision 0.29.1, onnxruntime 1.31.0, scikit-learn 1.9.1, onnx 1.23.2, torchsig 2.2.0 and sigmf 1.13.0 (spec 1.2.6).
  
  Env C, optional: AIMET 2.41.0, with 2.22.0 as a fallback, in its own venv. It hands ONNX plus encodings to env A. Its accuracy is never trusted without an HTP measurement.
  
  AI Hub: never used for artifacts. It no longer offers 2.42.
  
  DATA / POLICY
  
  Class policy: no radar, drone/FPV/RC link, EW/jammer, military, emitter-fingerprint or private-content classes.
  - Occupancy-only classes are allowed (lte_dl, gsm_dl; wifi and bt_ble only with the Lime).
  - DMR/P25, Iridium and Orbcomm appear only as unnamed occupancy.
  - The 3-30 kHz and 225-400 MHz masks are applied before any write.
  - Decoder payloads are never stored. The ADS-B and AIS oracles drop ICAO, MMSI and positions.
  
  TorchSig: an allowlist by signal name. It excludes lfm-radar, dmr and p25, and family labels are not used. CI fails on any banned name in a dataset manifest.
  
  Voice: raw IQ is fail-closed by allowlist. Raw bins are kept only inside predicted data-downlink windows or bench captures. Voice allocations are excised before write: amateur 144-146 and 430-440 MHz, PMR446, land-mobile, marine VHF and aero 118-137 MHz. nfm_voice boxes keep the spectrogram only.
  
  Datasets:
  - Own SigMF recordings.
  - TorchSig 2.2.0 (MIT).
  - SatNOGS DB (CC BY-SA 4.0), with a licence field on every record.
  - HisarMod2019.1: licence unverified, so benchmark or pretraining only, never in redistributable weights.
  - RadioML (CC BY-NC-SA 4.0): benchmark only.
  - Quota 20 GB on UFS. Private recordings never leave the home base.
  
  First live recordings: ISS SSTV Series 34, 22-25 Oct 2026, 437.55 MHz, Robot 36. Times are still TBD; re-check the ARISS page on 20-21 Oct.
- **Bench tests:**
  - FastRPC/firmware matrix. On kernel 6.18.2-4 (fallback 6.18.2-3), test each combination of {r2 DSP set, 0.2.42 DSP set} and {fastrpc 1.0.4-1, 1.0.7-3}. For each: fastrpc_test -a v68 must pass 3/3; qnn-platform-validator must run; the 2.42 SpecDet-S context via qnn-net-run must produce the golden output hash; dmesg must show 'remote processor cdsp is now up' on 20 cold boots from UFS without a manual start; dpkg -V must be clean. Pin and hold the first fully passing combination.
  - VTCM and soc_model. Build SpecDet-S with soc_model 35 / v68 at vtcm_mb=2, and a control binary at the generator default. Expected: the 2 MB binary loads; the default binary requests 4,194,304 B and fails with 0x138d. Record the VTCM that qnn-platform-validator / the device info API reports.
  - HTP latency and power. Run SpecDet-S/M/G for 10,000 tiles each through single-threaded inferd-htp. Sweep perf modes {burst, sustained_high_performance, balanced, power_saver} against RPC polling {off, 9999 us}. Record p50, p99, per-call overhead (wall time minus graphExecute) and INA228 board power. Pass: with Lime, p99 at most 11.7 ms at 42.5 tiles/s; without Lime, p99 at most 28 ms at 17.6 tiles/s. Choose the lowest-power mode with 2x margin.
  - INT8 accuracy on HTP outputs. Compare AP of 2.42 qnn-net-run INT8 against FP32 on held-out tiles (target within 2 points). Check variance > 0 per obj/box/occ and per fam channel, the zero-input probe against the manifest, and per-channel scale counts for every Conv weight from the qnn-context-binary-utility dump.
  - A16W8 on the fam head only, plus HardSwish against ReLU6. Record the latency multiplier (expected 2-4x), the AP change, and whether the profile shows HardSwish fused on v68.
  - ORT CPU fallback. Run SpecDet-S FP32 and QDQ under ORT 1.31.0 with intra=1, inter=1, spinning off: on one A55 (CPUQuota 100%) and on one A78. Pass: at least 4 tiles/s on one A55; otherwise raise K or set CPUQuota of about 150% on CPU0-3.
  - T2 on device. Time one E-S epoch with torch 2.14.1+cpu on CPU4-6 (3 threads, SCHED_IDLE) and multiply by 20. Pass: at most 11 min; otherwise default to the frozen-early-layer variant.
  - Converter CI in env A. Export at opset 17-21 and ir_version 10; run the onnx 1.16.1 checker, qairt-converter, qairt-quantizer (with --quantization_overrides) and qnn-context-binary-generator. Two rebuilds must give the same context hash. pip check must be clean, and onnx must still be 1.16.1 after every install.
  - AIMET handoff in env C. Feed AIMET 2.41.0 (and 2.22.0) encodings to the 2.42 converter via --quantization_overrides; it must accept the schema without warnings.
  - Load without prepare. Load the context with libQnnHtpPrepare.so absent from LD_LIBRARY_PATH. If it works, remove it from the inferd-htp path so on-device prepare becomes impossible.
  - 8 h soak. Canary tile every 5 min with an output-hash check, one forced CDSP crash (remoteproc stop/start) with ladder timing measured, and zero silent output drift.
  - Policy unit tests. A TorchSig manifest containing lfm-radar, dmr or p25 must make CI fail. A synthetic named-class signal at 20 kHz and at 300 MHz must be masked before write. Synthetic NFM voice at 145.500, 433.500 and 446.006 MHz inside a pinned raw capture must be excised before write (allowlist), and an MARK/SNAP on an nfm_voice box must save the spectrogram only.
- **Confidence:** medium

