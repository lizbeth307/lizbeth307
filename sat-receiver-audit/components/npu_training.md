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

