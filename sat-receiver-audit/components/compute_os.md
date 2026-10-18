# Compute os: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_9603e249-d87`_

- **Subsystem:** compute_os (Radxa Dragon Q6A, which stays: RAM tier, BIOS/SPI, held kernel and apt holds, DT overlays, USB/VBUS, M.2, cooling, NPU firmware, QAIRT 2.42, FastRPC)
- **Findings:**
  1.
    - **Claim in stack:** C2/2.1: buy the 12 GB board RS701-D12J0R44S32Y13W28 now. Prices: TinyTronics EUR 148 incl. VAT (10+ in stock), Allnet $189.99. 8 GB sold out at Allnet, Arace sold out.
    - **Finding:** The 12 GB board is the right buy and the prices hold. Product brief rev 1.7 (10 Oct 2026) lists LPDDR5-5500 in 4/6/8/12/16 GB. Allnet's Shopify JSON shows 12 GB RS701-D12J0R44S32Y13W28 at $189.99 available, 8 GB RS701-D8J0R44S32Y13W28 at $159.99 not available, and 6 GB RS701-D6 at $149.99, listed as WiFi5/BT5.4 (a different radio). TinyTronics shows the 12 GB at EUR 148.00 incl. VAT (EUR 122.31 ex.), '10+ pieces in stock'. Arace has every variant sold out (12 GB $169, plus a 16 GB SKU RS701-D16J0R44S32Y13W28). The $166.37 figure is EUR 148 at about 1.124 USD/EUR (a model rate). The '26 EU countries only' limit (TinyTronics) and the 7-day unused-return rule (Allnet) were not re-verified.
    - **Verdict:** confirmed
    - **Action:** Keep the 12 GB purchase. Check stock again at checkout. Keep the 12 h stressapptest + memtester and 50-100 cold-boot gate inside the return window.
    - **Impact:** No change to the BOM.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.7_g21b2881.pdf
      - https://shop.allnetchina.cn/products/radxa-dragon-q6a.js
      - https://www.tinytronics.nl/en/development-boards/single-board-computers/radxa-dragon-q6a-qcs6490-12gb
      - https://arace.tech/products/radxa-dragon-q6a.js
  2.
    - **Claim in stack:** C2: the RAM choice is 12 GB vs 8 GB. 'RAM cannot be added later.'
    - **Finding:** 16 GB is an official tier (product brief) and has an SKU at Arace (RS701-D16J0R44S32Y13W28), but it is sold out. No Radxa-listed distributor with 16 GB stock was found. The only 16 GB listing found (Hubtronics, India) carries the 12 GB SKU, so it is not trustworthy.
    - **Verdict:** new_option
    - **Action:** Buy 16 GB only if Allnet, TinyTronics or Arace shows it in stock before the 12 GB order ships, for no more than about $30-40 extra. Otherwise stay on 12 GB.
    - **Impact:** It would add about 4 GiB of headroom for the with-Lime training case (model margin 0.8-3.1 GiB free).
    - **Sources:**
      - https://arace.tech/products/radxa-dragon-q6a.js
      - https://hubtronics.in/single-board-computers/radxa-dragon-q6a-16gb-qcs6490-sbc
  3.
    - **Claim in stack:** 5.5: about 11.3 GiB visible on 12 GB, extrapolated from 6 GB = 5609 MB and 8 GB = 7604 MiB.
    - **Finding:** 7604 MiB on 8 GB is confirmed, but it was measured on kernel 6.17.1 with the older 251013-era firmware (sbc-reviews #85). One forum user says the 260120 'wp' (Gunyah) firmware costs about 0.5 GB of available memory (not verified). Model: 12288 MiB minus 588 MiB reserved gives 11.43 GiB; minus a further 512 MiB gives 10.93 GiB.
    - **Verdict:** new_risk
    - **Action:** Measure MemTotal on BIOS 260120 + 6.18.2-4 at gate W1-2. Re-run the free-RAM table with up to 0.5 GiB less; the with-Lime training row drops to about 0.3-2.6 GiB (model).
    - **Impact:** Small. Only the Lime + training case gets tight.
    - **Sources:**
      - https://github.com/geerlingguy/sbc-reviews/issues/85
      - https://forum.radxa.com/t/radxa-dragon-q6a-firmware-snapshot/28886/29
  4.
    - **Claim in stack:** #13: QCS6490 with 1x A78 2.7 + 3x A78 2.4 + 4x A55 1.9 GHz, Adreno 643, Hexagon v68 HTP 12 TOPS. 2.9 W idle, 9.3 W stress-ng, 10.1 W peak. 12 V/2 A (24 W) recommended.
    - **Finding:** Product brief rev 1.7: 1x Kryo Prime 2.7 + 3x Kryo Gold 2.4 + 4x Kryo Silver 1.9 GHz, Adreno 643 (OpenCL corrected to 2.0 in rev 1.7), Hexagon with HTA. Minimum 18 W (12 V/1.5 A), 24 W (12 V/2 A) with full USB3/PCIe load. The power figures are confirmed (2.9 W idle, 9.3 W stress-ng --matrix, 9.5 W Geekbench, 10.1 W HPL), but they were measured at the wall on an 8 GB board running 6.17.1. The Radxa brief does not state '12 TOPS' (not re-verified).
    - **Verdict:** confirmed
    - **Action:** Keep the budget. Measure NPU/GPU/USB add-ons with the A/B battery method as planned.
    - **Impact:** None.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.7_g21b2881.pdf
      - https://github.com/geerlingguy/sbc-reviews/issues/85
  5.
    - **Claim in stack:** #23: Radxa OS r2 on SPI BIOS 6.0.260120. 'BIOS 260916 is marked Not compatible with Radxa OS (Ubuntu 24)' (register: 'only one on the download page').
    - **Finding:** Partly corrected. The docs download page (EN and ZH markdown) still links only dragon-q6a_flat_build_wp_260120.zip and says R1+ images need BIOS 20251230 or newer. The 260916 build is not linked there. It exists on dl.radxa.com as dragon-q6a_flat_build_wp_260916.zip (10.2 MiB, uploaded 13 Oct 2026). Its dragon-q6a-bios-changelog.md says 'Compatible and tested with Radxa OS (Ubuntu 26)', 'Not compatible with Radxa OS (Ubuntu 24)', and 'With Radxa OS (Ubuntu 26.04) Video encoding and decoding are unavailable after enabling the hypervisor.' The bigger issue is apt: the noble repo package edk2-qcs6490 0.1.0-8 (17 Sep 2026, 'update firmware to 6.0.260916...KODIAKWP-1') and 0.1.0-9 (current) carry 260916, while 0.1.0-5 to 0.1.0-7 carry 260120. I verified the imagefv.elf stamps: 260120125234Z in 0.1.0-7 and 260916065317Z in 0.1.0-9. The package has no postinst, so it does not flash itself, but rsetup's bootloader update would flash 260916.
    - **Verdict:** corrected
    - **Action:** Add apt holds on edk2-qcs6490, edk2-radxa-dragon-q6a and rsetup. Mirror edk2-qcs6490_0.1.0-7_all.deb (GitHub release radxa-pkg/edk2-qualcomm 0.1.0-7, sha256 6216fc863dcc9c48ade407eebb8edf6e8dd81568a9d6eacb04fd32be353b5483). Never run the rsetup bootloader update. Archive both the 260120 and 260916 zips.
    - **Impact:** Without the hold, one 'apt upgrade' followed by an rsetup bootloader update would install a BIOS that Ubuntu 24 cannot boot.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/download
      - https://dl.radxa.com/dragon/q6a/images/
      - https://dl.radxa.com/dragon/q6a/images/dragon-q6a-bios-changelog.md
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/main/binary-arm64/Packages
      - https://github.com/radxa-pkg/edk2-qualcomm/releases/download/0.1.0-7/edk2-qcs6490_0.1.0-7_all.deb
  6.
    - **Claim in stack:** W1-2: the board arrives with a compatible BIOS (implicit).
    - **Finding:** Boards made or reflashed after Sep 2026 may ship with 260916 pre-flashed, since it is Radxa's newest build for its Ubuntu 26 path. No shipping statement was found, so this is unverified.
    - **Verdict:** unverified
    - **Action:** First boot step: run 'sudo dmidecode -s bios-version'. If it shows 260916, take a full SPI dump, then flash 260120 over EDL (or stop and decide). Treat a refusal to boot r2 as a warranty or reflash case, not an OS bug.
    - **Impact:** It could block the noble/6.18.2-4 path on day 1.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/images/dragon-q6a-bios-changelog.md
      - https://docs.radxa.com/en/dragon/q6a/download
  7.
    - **Claim in stack:** #22: back up SPI NOR (partitions cdt/ddr) with edl-ng before any firmware change. Known failures: RCW_TRAINING_FAIL, DRAM_DCC_FAIL, ONLY_RANK_1. EDL needs an A-A cable.
    - **Finding:** The known failures are confirmed, but the backup scope is too narrow. The SPI is a Winbond W25Q256 (32 MiB, per the upstream DTS and edl-ng log 'Device size: 32.00 MiB'). The documented partitions are ddr, uefi, devcfg, xbl and VarStore. Radxa staff wrote (27 May 2026) 'there are some data on the SPI that is not part of the BIOS update package.' Several boards fail DDR training right after SPI updates, including after updating to 260120; Radxa called these hardware faults and sent them to RMA (threads 30841 and 29863: NO_MEMORY_DEVICE_DETECTED, one 12 GB board labelled 'revision v1.216'). EDL-NG v1.6.0 (Aug 2026) is current; the repo package is edl-ng 1.4.1. The docs specify an A-A cable; a user reports that a USB A-to-C data cable also works.
    - **Verdict:** corrected
    - **Action:** Make a full raw 32 MiB spinor read with edl-ng v1.6.0 plus SHA-256 before any change, not only cdt/ddr. Avoid SPI updates unless needed. An A-to-C data cable can replace the A-A cable (A-A remains the documented one).
    - **Impact:** A full image is the only way to restore per-board data that the BIOS zip does not contain.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/low-level-dev/spi-fw
      - https://forum.radxa.com/t/dragon-q6a-wont-boot-ddr-rcw-training-fails-on-cold-boot-board-loops-into-edl/30841
      - https://forum.radxa.com/t/radxa-dragon-q6a-with-ddr-problem/29863
      - https://forum.radxa.com/t/radxa-dragon-q6a-firmware-snapshot/28886
      - https://docs.radxa.com/en/dragon/q6a/low-level-dev/edl-mode
  8.
    - **Claim in stack:** #23/#24: hold linux-image-6.18.2-4-qcom. 'Repo index (24.09.2026) contains only 7.0.11-7'. Headers come from the GitHub release.
    - **Finding:** Confirmed, with a bring-up correction. The qcs6490-noble Release is dated 24 Sep 2026 and lists only 7.0.11-7 kernels. Old versions are purged from the pool (6.18.2-4, fastrpc 1.0.3-1, edk2 0.1.0-5/-7 and radxa-overlays 0.2.18 all return 404). 6.18.2-4 exists only as GitHub release radxa-pkg/linux-qcom 6.18.2-4 (30 Mar 2026: image 65.1 MB, headers 8.61 MB, metapackages). It is the last 6.18 release; the newer ones are 7.0.2-1 to 7.0.11-7 (17 Sep 2026). The r2 image manifest ships linux-image-6.18.2-3-qcom (not -4), radxa-firmware-qcs6490 0.2.29, fastrpc 1.0.3-1, radxa-overlays-dkms 0.2.18 and edk2 0.1.0-5. A first 'apt upgrade' on r2 would pull the 7.0.11-7 metapackage.
    - **Verdict:** corrected
    - **Action:** Bring-up order: flash r2; before any apt upgrade, apt-mark hold the whole list (see the hold-gaps finding); dpkg -i the 6.18.2-4 image and headers from the GitHub release; record SHA-256; mirror into aptly. Ship the golden disk image as planned.
    - **Impact:** This prevents an unplanned jump to 7.0.11 (HDMI and CDSP regressions per the register).
    - **Sources:**
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/Release
      - https://github.com/radxa-pkg/linux-qcom/releases
      - https://github.com/radxa-pkg/linux-qcom/releases/expanded_assets/6.18.2-4
      - https://github.com/radxa-build/radxa-dragon-q6a/releases/download/rsdk-r2/radxa-dragon-q6a_noble_gnome_r2.manifest
  9.
    - **Claim in stack:** #26/#25: built in CONFIG_PPS, GPIO_PCA953X, I2C_CHARDEV, HIDRAW, ARM_SMC_WATCHDOG. Modules PWM_GPIO, QCOM_WDT, ina238. Not built PPS_CLIENT_GPIO/LDISC, PINCTRL_MCP23S08. Also PREEMPT_DYNAMIC, NO_HZ_FULL, RCU_NOCB_CPU, DRM_LOAD_EDID_FIRMWARE.
    - **Finding:** All confirmed from include/config/auto.conf in linux-headers-6.18.2-4-qcom: PPS=y; PPS_CLIENT_GPIO and PPS_CLIENT_LDISC unset; PREEMPT_DYNAMIC=y; NO_HZ_FULL=y; RCU_NOCB_CPU=y; DRM_LOAD_EDID_FIRMWARE=y; GPIO_PCA953X=y; I2C_CHARDEV=y; HIDRAW=y; ARM_SMC_WATCHDOG=y; QCOM_WDT=m; PWM_GPIO=m; SENSORS_INA238=m; PINCTRL_MCP23S08 unset; QCOM_FASTRPC=m; DMABUF_HEAPS_SYSTEM=y and DMABUF_HEAPS_CMA=y; CMA_SIZE_MBYTES=32; HZ=1000; GPIO_CDEV_V1=y; SERIAL_QCOM_GENI_UART_PORTS=8. Noble ships libgpiod 1.6.3-1.1build1 (in r2 too), so the v1-uAPI note holds.
    - **Verdict:** confirmed
    - **Action:** Keep pps-gpio as a DKMS package and MCP23017 control through smbus2.
    - **Impact:** None.
    - **Sources:**
      - https://github.com/radxa-pkg/linux-qcom/releases/download/6.18.2-4/linux-headers-6.18.2-4-qcom_6.18.2-4_arm64.deb
      - https://packages.ubuntu.com/noble/libgpiod-dev
  10.
    - **Claim in stack:** #26: watchdog = QCOM_WDT ('confirm the watchdog node in DT on the board').
    - **Finding:** Corrected. In radxa/kernel linux-6.18.2 sc7280.dtsi the node watchdog@17c10000 (qcom,apss-wdt-sc7280) has status = "reserved" /* Owned by Gunyah hyp */. QCOM_WDT therefore cannot bind on BIOS 260120, which boots under Gunyah. There is no arm,smc-wdt node, so ARM_SMC_WATCHDOG has nothing to bind to either. Mainline gained drivers/watchdog/gunyah_wdt.c on 2026-05-03 (SMCCC-based, registered via qcom_scm, max timeout 32 s). It is not in Radxa 6.18.2.
    - **Verdict:** corrected
    - **Action:** Make the Pico the hardware watchdog: systemd sends a labinput heartbeat over UART7; on loss, the Pico pulses J21 pin 3 and then cuts power through #2813 OFF. Do not enable a RuntimeWatchdog in systemd. A gunyah_wdt backport is optional later and needs a qcom_scm change, so it cannot be a simple DKMS package.
    - **Impact:** Without this there is no hang recovery in the field.
    - **Sources:**
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/arch/arm64/boot/dts/qcom/sc7280.dtsi
      - https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/log/drivers/watchdog/gunyah_wdt.c
  11.
    - **Claim in stack:** C6/5.2/5.4: one lab-q6a.dtso built from the Radxa overlays uart6, uart7, i2c0 and i2c2, plus pps-gpio on GPIO96. Pins: 7 PPS, 13/15 I2C0, 16/18 UART6, 27/28 I2C2, 32/29 UART7, 3/5 = GPIO24/25. Open question: is the UART7 overlay on the held image?
    - **Finding:** The pin map is confirmed by the product brief (rev 1.7) GPIO table. The overlays exist in radxa-overlays-dkms 0.2.31: uart6 claims only gpio26/27 (TX/RX), so GPIO24/25 on pins 3/5 stay free; only uart6-flowctl takes them. uart7 claims gpio30/31 (pins 32 and 29, copyright 2026). i2c0 and i2c2 run at 100 kHz. All use qcom,enable-gsi-dma. Correction: r2 ships radxa-overlays-dkms 0.2.18, which has no uart7 (and no uart14) overlay. The qup_uart7_tx/rx labels exist in the 6.18.2 sc7280.dtsi, so the 0.2.31 fragment applies. In the Radxa DTS, GPIO96 is only gpio-line-name PIN_7 and no node claims it. I2C0, I2C2 and I2C6 are off by default in Radxa's DTS; upstream enables I2C6 on pins 3/5.
    - **Verdict:** corrected
    - **Action:** Build lab-q6a.dtso from the 0.2.31 fragments (copy them in; do not depend on the DKMS package version). Install it in the active systemd-boot entry under /boot/efi (extlinux is not the active path, per forum 31078). Keep the pinmux-pins audit.
    - **Impact:** Without the 0.2.31 fragment, UART7 (Pico) would not exist on the r2 package set.
    - **Sources:**
      - https://radxa-repo.github.io/qcs6490-noble/pool/main/r/radxa-overlays/radxa-overlays-dkms_0.2.31_all.deb
      - https://github.com/radxa-pkg/radxa-overlays/releases/download/0.2.18/radxa-overlays-dkms_0.2.18_all.deb
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://dl.radxa.com/dragon/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.7_g21b2881.pdf
  12.
    - **Claim in stack:** #79: LC76G on UART6 = /dev/ttyHS1 (udev /dev/gnss0).
    - **Finding:** The device name is not guaranteed. The Radxa DTS has only the alias serial0 = &uart5. In qcom_geni_serial.c (6.18.2), a non-console port without an alias takes ida_alloc_range(max_alias+1, ...), so ports are numbered ttyHS1, ttyHS2 and so on in probe order. With both UART6 and UART7 enabled, which one gets ttyHS1 depends on probe order (GSI-DMA deferral can reorder them).
    - **Verdict:** new_risk
    - **Action:** Add serial1 = &uart6 and serial2 = &uart7 in an overlay fragment on /aliases, or match udev on the platform paths 998000.serial (to /dev/gnss0) and 99c000.serial (to /dev/lab/pico) instead of on ttyHS numbers.
    - **Impact:** Prevents gpsd and labinput swapping ports after a reboot.
    - **Sources:**
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/drivers/tty/serial/qcom_geni_serial.c
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
  13.
    - **Claim in stack:** #36: golden FastRPC set from linux-msm/hexagon-dsp-binaries (CDSP.HT.2.5.c4-00004, ADSP c9-00028, fastrpc_shell_3 and unsigned_3 with recorded SHA-256). A DT overlay adds memory-region (shared-dma-pool) to both fastrpc nodes. An initramfs hook loads adsp.mbn and cdsp.mbn. fastrpc_test -a v68 passes 3/3.
    - **Finding:** Confirmed, with two corrections.
  (1) The directories qcs6490/radxa/dragon-q6a/CDSP.HT.2.5.c4-00004-KODIAK-1 and ADSP.HT.5.5.c9-00028-KODIAK-2 exist (WHENCE: Redistributable, LICENSE.qcom; repo HEAD 16 Oct 2026, unchanged for Q6A). The SHA-256 values are identical in hexagon-dsp-binaries, radxa-firmware-qcs6490 0.2.29 and 0.2.42: fastrpc_shell_3 d6ef508a4051429bb231b8e1323683d847cb6dcc1b83af187c60f97c36a5a02d; fastrpc_shell_unsigned_3 655a003255ae01d8b9c3eb2e978765d7dacbdf1ac5c7cf7ac8e171ac09f03dff; ADSP fastrpc_shell_0 17078ae470a13477a6f6b0663a0cd828cdd5d109c3b1ee9f3f02bff70108d68e.
  (2) The .mbn files are NOT identical across packages, although the version strings and build stamps match (CDSP ..._20250508_050001, ADSP ..._20250819_030546). In 0.2.29, cdsp.mbn a9645c94... and adsp.mbn 01fea794... (9,871,840 B). In 0.2.42 (17 Sep 2026, 'update qcs6490 dsp firmware'), cdsp.mbn 644cb94c... and adsp.mbn da35227f... (14,012,896 B).
  Package 0.2.30 (May 2026) moved the DSP libraries from /usr/lib/dsp/{cdsp,adsp} to /usr/share/qcom/qcs6490/radxa/dragon-q6a/dsp/ and added Radxa's own initramfs hook.
  The proven fix (forum 31078, 9 Jul 2026) is: 6.18.2-4 + pristine radxa-firmware-qcs6490 0.2.29 + an overlay that adds memory-region = <&adsp_rpc_remote_heap_mem> (@0xc6500000, 8 MiB, no-map in the Q6A DTS) and compatible = "shared-dma-pool" + the entry added to systemd-boot. Result: fastrpc_test -a v68 PASSED. Forum 30674 adds that rebuilding the whole base DTB caused EFI boot failure and that 'cma=' was ignored.
    - **Verdict:** corrected
    - **Action:** Freeze on radxa-firmware-qcs6490 0.2.29 (GitHub release, deb sha256 f59a5e5b14d95650c9d248ae223fa293b753530ebb46bb96e27e635b0f457e98) and record both mbn hashes. Keep your own initramfs hook (0.2.29 has none). Do not mix in 0.2.42 files; verify with 'dpkg -V radxa-firmware-qcs6490'. Use a DTBO only, never a rebuilt base DTB.
    - **Impact:** 'Same version string' is not the same binary, so the golden set must be pinned by hash.
    - **Sources:**
      - https://github.com/linux-msm/hexagon-dsp-binaries
      - https://github.com/radxa-pkg/radxa-firmware/releases/download/0.2.29/radxa-firmware-qcs6490_0.2.29_all.deb
      - https://radxa-repo.github.io/noble/pool/main/r/radxa-firmware/radxa-firmware-qcs6490_0.2.42_all.deb
      - https://forum.radxa.com/t/dragon-q6a-fastrpc-npu-fails-fastrpc-ioctl-init-create-returns-0x80000600-on-cdsp/31078
      - https://forum.radxa.com/t/critical-blockers-for-npu-cma-allocation-on-radxa-dragon-q6a-qcs6490/30674
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
  14.
    - **Claim in stack:** #24: hold fastrpc, libcdsprpc1 and the listener libraries (no version given). udev rule for /dev/fastrpc-* and /dev/dma_heap/*.
    - **Finding:** No version is pinned, and the candidate versions all differ: r2 has 1.0.3-1, the forum fix used 1.0.4-1, the Radxa repo now has 1.0.7-3, and upstream is v1.0.8 (11 Sep 2026; HEAD 9 Oct 2026). Upstream issue #371 is open and marked stale: a CDSP 0/3 regression with fastrpc 1.0.6 on qcs6490-rb3gen2, where group creation was moved to startup and the deb packages carry a udev workaround. The maintainer expects the bug to still be present in 1.0.7. The default DSP search path compiled into v1.0.7 is ';/usr/lib/rfsa/adsp;/usr/lib/dsp;'.
    - **Verdict:** new_risk
    - **Action:** Pin fastrpc, libcdsprpc1, libadsprpc1, the *-default-listener1 libraries, fastrpc-dev and fastrpc-test to one version tested in Phase 0 (1.0.4-1 has a forum pass on Q6A; try 1.0.7-3 only on the second medium). Ship your own udev rule and the fastrpc group.
    - **Impact:** An unpinned upgrade can break CDSP sessions with 0x80000600 or 0x72 errors.
    - **Sources:**
      - https://github.com/qualcomm/fastrpc/issues/371
      - https://github.com/qualcomm/fastrpc
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/main/binary-arm64/Packages
  15.
    - **Claim in stack:** #37: QAIRT 2.42.0.251225 on the device (qcom-qnn-sdk-v68 0.1.0-2) and on an x86-64 Ubuntu 22.04 / Python 3.10 host. Zip size 1,543,955,191 bytes. Open questions: soc_model 35 vs 93, and VTCM.
    - **Finding:** Confirmed. qcom-qnn-sdk-v68_0.1.0-2_all.deb (sha256 306fd647b88902d170831980ca68a31d77d77923534e2070783fbeca132a6e54) contains 'AISW_VERSION: 2.42.0' and v2.42.0.251225135753_193295. A range-GET on 18 Oct 2026 returned content-range bytes */1543955191, Last-Modified 7 Jan 2026. The Radxa docs still require 2.42.0.251225 on Ubuntu 22.04 / Python 3.10 and list QCS6490 as dsp_arch v68, soc_id 35. New details: the deb installs libQnnHtpV68Skel.so in /usr/lib/aarch64-linux-gnu, which is outside fastrpc's default DSP search paths. A forum report on 2.42/6.18 says 'Request feature vtcm size with value 4194304 unsupported'; only 2 MB works. Current status: AI Hub moved to QAIRT 2.50.0 on 14 Sep 2026 (2.49 on 17 Aug), so 2.42 is 8 minor versions behind.
    - **Verdict:** confirmed
    - **Action:** Set ADSP_LIBRARY_PATH (or DSP_LIBRARY_PATH) to include /usr/lib/aarch64-linux-gnu in the labclassify unit. Use soc_id 35 and VTCM 2 MB. Archive the zip and deb with SHA-256 now, while the zip is still downloadable. Never use AI Hub artifacts.
    - **Impact:** Without the library path, the HTP skel fails to load (error 1002 / 0x80000600).
    - **Sources:**
      - https://radxa-repo.github.io/qcs6490-noble/pool/main/q/qcom-qairt/qcom-qnn-sdk-v68_0.1.0-2_all.deb
      - https://raw.githubusercontent.com/radxa-docs/docs/main/i18n/en/docusaurus-plugin-content-docs/current/common/ai/qualcomm/_qairt-install.mdx
      - https://docs.radxa.com/en/dragon/q6a/app-dev/npu-dev/qairt-sdk
      - https://forum.radxa.com/t/31208
      - https://workbench.aihub.qualcomm.com/docs/hub/release_notes.html
  16.
    - **Claim in stack:** C5/5.2: the bottom J5 port is the blue USB 3.1 port (USB0, EDL), on U35 WS4612 (about 2.1 A, shared with the top J5 port). J2a and J2b are on U33. FE1.1s hub P1-P3 go to the ports and P4 to Wi-Fi/BT (FCU760K).
    - **Finding:** Confirmed by schematic v1.21. U33 WS4612 feeds VDD_USB_VBUSTYPEA to J2 (dual USB2). U35 WS4612 feeds VDD_FUSB to J5 (USB3_TYPE_A_TOP and _BOTTOM). Both ISET resistors are 3.24 kΩ (R229, R235). The WS4612EA datasheet gives 6.8 kΩ for 1.0 A and 2.72 kΩ for 2.5 A (2.15-2.85 A), so ILIM is about 6.8/RSET: 2.10 A typical, roughly 1.8-2.4 A (model scaled from the datasheet). The switch has built-in reverse protection. The DTS has the FE1.1s hub (usb1a40,0101) on usb_2 with three connector ports and wifi@4 (usba69c,8d80, labelled FCU760K). The EDL docs specify the USB 3.1 Type-A port.
    - **Verdict:** confirmed
    - **Action:** No change. Keep VBUS cut and backfeed checks with the FNB58.
    - **Impact:** None.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://atta.szlcsc.com/upload/public/pdf/source/20220218/3A9AA13941855B445B773B21A878E856.pdf
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
  17.
    - **Claim in stack:** #21/#69 (Lime only): M.2 2230 M-key, Gen3 x2 on pcie1 through a short shielded riser (ADT-Link R44SF 5 cm, $19), Gen2 fallback via max-link-speed=2, acceptance at 8 GT/s.
    - **Finding:** The slot facts are confirmed: pcie1 has num-lanes 2 and goes to the top-side M.2 M-key slot (2230 NVMe only, no SATA); pcie0 is x1 (Ethernet). New: Radxa's Android 15 RC of 8 Oct 2026 'Limited the M.2 M-Key slot to PCIe 2.0 to improve compatibility', which suggests thin Gen3 margins even without a riser. One forum report (May 2026) describes an M.2 socket that died after hours and went to RMA. The R44SF 5 cm at $19 was not found; Newegg lists R44SF 10 cm at $25.58 and other lengths at $29.99-82.40. A 2230 host-end fit was not verified.
    - **Verdict:** new_risk
    - **Action:** If Lime stays, make Gen2 (max-link-speed=2) the default through the riser, and allow Gen3 only after 60 min with zero AER errors. Test the M.2 slot inside the return window, even without Lime. Re-price the riser at purchase.
    - **Impact:** Only matters if Lime is kept (decision due 1 Dec 2026).
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/download
      - https://dl.radxa.com/dragon/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.7_g21b2881.pdf
      - https://forum.radxa.com/t/nvme-2230-not-detected/30807
      - https://www.newegg.com/SULE-Gadgets/BrandSubCat/ID-206580-3282/Page-3
  18.
    - **Claim in stack:** #16/2.1/5.6: Radxa Armor 7056A or a stepped Cu block plus a 30-40 mm 5 V fan (Adafruit 6101, $4.95). Tj 95 °C, throttling about 90-91 °C. Reset ladder at 80/85 °C.
    - **Finding:** Mostly confirmed; the thermal limits needed correcting.
  The Armor Case 7056A (Allnet AE036, $9.90, in stock) is a two-piece fanless metal enclosure: top cover 70x56x15 mm, bottom cover 85x56x15 mm, about 200 g shipping weight, 2 pads and 4 screws. A forum user at 35-40 °C ambient saw CPU/GPU above 90 °C with throttling on the Armor alone and fixed it with a 5 V fan; copper heatsink + 40 mm fan setups are reported to work.
  In the 6.18.2 DT, the CPU zones have passive trips at 90 and 95 °C and a critical trip at 110 °C; the GPU has passive trips at 95/100/105 °C; NSP and DDR have 'hot' at 90 °C. So 95 °C is the second throttle step, not Tj max.
  Adafruit 6101 is a 4 cm 5 V USB-plug fan ($4.95, in stock) with no PWM or tach. Adafruit says to cut the plug and add a flyback diode.
  The DT also exposes the thermistor zones ufs-thermal, msm-skin-thermal, quiet-thermal and xo-thermal.
    - **Verdict:** corrected
    - **Action:** Use the copper block + 40 mm fan as the primary cooler; use the Armor case only if its 15 mm top and bottom covers fit the 55-60 mm enclosure and the UFS pad plan. Add a flyback diode on the Pico fan FET. Log the skin and UFS zones. Keep 80/85 °C as the app-level ladder; it sits below the 90 °C kernel throttle.
    - **Impact:** Mechanical fit and slightly more accurate thermal limits.
    - **Sources:**
      - https://shop.allnetchina.cn/products/radxa-heatsink-7056a
      - https://radxa.com/products/accessories/armor-case-7056a
      - https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/arch/arm64/boot/dts/qcom/sc7280.dtsi
      - https://www.adafruit.com/product/6101
  19.
    - **Claim in stack:** #25 open questions: which package ships systemd-bless-boot, and whether UEFI variables persist.
    - **Finding:** Both answered. In noble, systemd-bless-boot (the binary, the .service and the generator) is shipped by the systemd-boot package; r2 has 255.4-1ubuntu8.12. The 260120 release notes say: 'UEFI variables are now persistent across reboots... accessible from Linux... depends on the new v6.18 kernel in RadxaOS T7 or newer.' The same notes: 'OS images using the old v6.17 kernel will no longer be able to access the onboard SPI flash.'
    - **Verdict:** confirmed
    - **Action:** Keep systemd-boot (held) for boot counting and keep loader.conf as the default. Boot counting does not need EFI variables.
    - **Impact:** Closes 2 of the W1-2 unknowns.
    - **Sources:**
      - https://packages.ubuntu.com/search?searchon=contents&keywords=systemd-bless-boot&mode=filename&suite=noble&arch=arm64
      - https://forum.radxa.com/t/radxa-dragon-q6a-firmware-snapshot/28886
  20.
    - **Claim in stack:** #24/C22: one hold list (kernel metapackages, radxa-firmware-qcs6490, linux-firmware, fastrpc, libcdsprpc1, listener libraries, qcom-qnn-sdk-v68, Mesa 25.2.8-0ubuntu0.24.04.4 + libdrm 2.4.125, xwayland/wlroots/labwc/qt6, systemd-boot, pipewire).
    - **Finding:** The pinned versions are current: Mesa 25.2.8-0ubuntu0.24.04.4 in noble-updates, libdrm2 2.4.125-1ubuntu0.1~24.04.2, labwc 0.7.1-1build1. The list is missing packages that can change boot or NPU state:
  - edk2-qcs6490 and edk2-radxa-dragon-q6a (BIOS 260916 risk)
  - rsetup (0.4.26 in r2, 0.4.28 in the repo)
  - radxa-overlays-dkms (a dependency of the kernel metapackage)
  - libadsprpc1, libsdsprpc1, fastrpc-dev, fastrpc-test, task-qualcomm-npu and task-qcs6490
  - radxa-qcom-qairt
  - linux-firmware-dragonwing (1.0.0+20251203 in r2)
  - radxa-system-config-qcs6490
    - **Verdict:** corrected
    - **Action:** Extend the hold list and the aptly mirror with these packages at their r2 or Phase-0 versions. Take old debs from the radxa-pkg GitHub releases (the apt pool purges them; checked: 0.1.0-7, 0.2.29, 1.0.7-3 and 0.2.31 download fine).
    - **Impact:** Closes the drift paths the current list leaves open.
    - **Sources:**
      - https://packages.ubuntu.com/noble-updates/libgl1-mesa-dri
      - https://packages.ubuntu.com/noble/labwc
      - https://github.com/radxa-build/radxa-dragon-q6a/releases/download/rsdk-r2/radxa-dragon-q6a_noble_gnome_r2.manifest
      - https://radxa-repo.github.io/noble/dists/noble/main/binary-arm64/Packages
  21.
    - **Claim in stack:** 2.1 recovery kit: ALLNET microSD 64 GB, Adafruit 5212 reader, Adafruit 6324 cable, USB3 A-A cable. UFS 128 GB RA022-B10J0U2 $65.90 at Allnet. RTC battery $0.95.
    - **Finding:** Confirmed live on 18 Oct 2026: ALLNET 64GB microSDXC $16.99 in stock; Adafruit 5212 USB-C microSD reader $6.95 in stock; Adafruit 6324 2 m USB-C to A cable $2.95 (93 in stock); Allnet UFS 128GB RA022-B10J0U2 $65.90 in stock (64/256/512 GB out of stock); 'RTC Battery for RADXA SBC' $0.95 in stock. Also: the 3D STEP file was re-uploaded on 17 Aug 2026 under the same v1.21 name; the schematic is still v1.21 (Sep 2025).
    - **Verdict:** confirmed
    - **Action:** Re-download the STEP file before enclosure CAD and diff it against the earlier copy.
    - **Impact:** None.
    - **Sources:**
      - https://shop.allnetchina.cn/products/high-performance-ufs-3-1-module.js
      - https://www.adafruit.com/product/5212
      - https://www.adafruit.com/product/6324
      - https://dl.radxa.com/dragon/q6a/hw/
  22.
    - **Claim in stack:** #23: Path B (7.0.11-7 + clk_ignore_unused) only for Kioxia UFS. Notes in the register on HDMI black screen and CDSP failures on 7.0.x.
    - **Finding:** Not re-verified. The 7.0.11-7 release notes say only 'chore: update submodules'. A Radxa resolute (Ubuntu 26.04) repo now exists (qcs6490-resolute, 24 Sep 2026) with the same 7.0.11-7 kernel and edk2 0.1.0-9 (260916). The noble + 6.18 path is therefore frozen: there has been no 6.18 kernel release since 30 Mar 2026.
    - **Verdict:** unverified
    - **Action:** Keep Path A for v1. Later, evaluate a Path C (resolute + 7.0.11 + BIOS 260916) on a second medium only, with an SPI backup first, and only if Phase 0 or HDMI on Path A fails.
    - **Impact:** Strategic: future fixes from Radxa will land only on 7.0/resolute.
    - **Sources:**
      - https://github.com/radxa-pkg/linux-qcom/releases/tag/7.0.11-7
      - https://radxa-repo.github.io/qcs6490-resolute/dists/qcs6490-resolute/Release
- **Current status oct 2026:** As of 18 Oct 2026:
  - Hardware: no new revision. The schematic is still v1.21 (Sep 2025); the STEP file was re-uploaded on 17 Aug 2026 under the same name. Product brief rev 1.7 (10 Oct 2026) only corrects OpenCL to 2.0 and promises availability until at least Sep 2035; no EOL notice. Radxa's firmware package now links the Q6A DSP firmware to a 'dragon-q6b' board (irrelevant here: the Q6A stays).
  - BIOS: the docs link only 260120. 260916 (on dl.radxa.com since 13 Oct 2026; in the apt package edk2-qcs6490 since 0.1.0-8, 17 Sep 2026) targets Radxa OS Ubuntu 26 and is explicitly not compatible with Ubuntu 24. The Android 15 RC (8 Oct 2026) limits M.2 to PCIe 2.0.
  - OS and kernel: r2 (14 Feb 2026) is still the latest Radxa OS. It ships kernel 6.18.2-3, radxa-firmware-qcs6490 0.2.29, fastrpc 1.0.3-1 and edk2 0.1.0-5. 6.18.2-4 (30 Mar 2026) exists only as a GitHub release. The apt repos (noble, and the new qcs6490-resolute; both 24 Sep 2026) carry only 7.0.11-7 (17 Sep 2026).
  - NPU stack: fastrpc upstream v1.0.8 (11 Sep 2026); the Radxa repo has 1.0.7-3. hexagon-dsp-binaries HEAD is 16 Oct 2026, with Q6A still on CDSP c4-00004 / ADSP c9-00028. QAIRT 2.42.0.251225 is still downloadable (1,543,955,191 B); AI Hub is on QAIRT 2.50.
  - Stock: Allnet 12 GB $189.99 in stock (8 GB sold out); TinyTronics 12 GB EUR 148 (10+); Arace sold out on all tiers, including 16 GB. Armor 7056A $9.90 at Allnet in stock.
- **Notes:** Method: primary sources only. These were the Radxa docs markdown on GitHub, dl.radxa.com listings and changelog, the apt indexes Release, Packages and Contents, and the downloaded debs: edk2-qcs6490 0.1.0-7 and -9, radxa-firmware-qcs6490 0.2.29 and 0.2.42, radxa-overlays-dkms 0.2.18 and 0.2.31, qcom-qnn-sdk-v68 0.1.0-2, and the linux-headers 6.18.2-4 auto.conf. I also used the radxa/kernel linux-6.18.2 DTS, sc7280.dtsi and qcom_geni_serial.c; clones of linux-msm/hexagon-dsp-binaries and qualcomm/fastrpc; the schematic v1.21 PDF; and the WS4612 datasheet. Distributor pages were Shopify JSON for Allnet and Arace, TinyTronics through WebFetch, and the Adafruit API. Forum threads 28886, 31078, 31208, 30674, 30123, 30413, 30841, 29863, 30807 and 31047 were read through Discourse JSON.
  
  Models (not measurements): the 2.10 A VBUS limit uses ILIM of about 6.8 kΩ·A divided by RSET, from the datasheet table, with a 1.8-2.4 A spread. The 10.9-11.4 GiB visible RAM is extrapolated from 8 GB = 7604 MiB, minus an optional 0.5 GiB that one forum user reports for the wp firmware. The USD conversion of EUR 148 uses about 1.124 USD/EUR.
  
  Not verified: the TinyTronics '26 EU countries' limit; the Allnet 7-day return terms; the R44SF 5 cm at $19 and its 2230 fit; the J21 pin order (the schematic text confirms only a CON_1X3 on ADP12V_IN with D19 SMBJ15CA on TYPEC_IN); the SY7120RAC current rating for VCC_5V_PERI (datasheet link dead); the Path B 7.0.11-7 fixes; and a forum claim that QAIRT 2.46 works on Q6A.
  
  Rule compliance: no alternative boards are proposed; Q6B is mentioned only as a firmware-sharing note. All changes are receive-only software, firmware or accessory items. Key SHA-256 values are in the findings: the edk2 0.1.0-7 deb, radxa-firmware 0.2.29 deb, both mbn sets, the DSP shells and the QNN deb.
  
  Scratch downloads are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_compute.

## Адверсаріальна перевірка (`verify`)

_Run `wf_9603e249-d87`_

- **Subsystem:** compute_os: Radxa Dragon Q6A, which stays. Covers RAM tier, BIOS/SPI, the held 6.18.2-4 kernel and apt holds, DT overlays, USB/VBUS, M.2, cooling, NPU firmware, QAIRT 2.42 and FastRPC. This is stage 3, adversarial verification of stages 1 and 2 against primary sources, 18 Oct 2026.
- **Verdict:** Stages 1 and 2 mostly survive, but the spec needs eight changes.
  
  **Re-checked from primary sources.** I re-downloaded and re-hashed these myself:
  - debs: edk2-qcs6490 0.1.0-5, -7 and -9; radxa-firmware-qcs6490 0.2.29 and 0.2.42; radxa-overlays-dkms 0.2.18 and 0.2.31; linux-headers-6.18.2-4; qcom-qnn-sdk-v68; fastrpc 1.0.4-1; sdboot-is-embloader 0.7; linux-firmware-dragonwing 20260825;
  - the r2 manifest and the Radxa, resolute and Launchpad PPA indexes;
  - the radxa/kernel linux-6.18.2 sources at 559f4f9, the embloader git tags 0.1-0.7 and HEAD, the systemd v255 and main boot.c, and the rsetup, rsdk and radxa-system-config sources;
  - the schematic v1.21, the WS4612 datasheet and product brief rev 1.7;
  - about 35 forum threads, read through Discourse JSON.
  
  **What survives:**
  - the 12 GB purchase and its prices;
  - BIOS 260916 is not compatible with Ubuntu 24, and the apt path carries it;
  - 6.18.2-4 exists only as a GitHub release;
  - every kernel-config item;
  - the APSS watchdog node is reserved for Gunyah;
  - the overlay and pin map, with uart7 only in overlays 0.2.31;
  - the DSP shell hashes, and the mbn files differ by hash between 0.2.29 and 0.2.42;
  - the QAIRT 2.42 pin, with the skel library outside the fastrpc search path;
  - the WS4612 current-limit model;
  - embloader has no boot counting, and systemd-boot 255 has no devicetree-overlay key;
  - the PPA drift path;
  - the UKI reboot bug on 260120;
  - the Kioxia UFS quirk exists only on the branch HEAD.
  
  **What changes:**
  1. **Gunyah watchdog module is possible (refutes stage 1).** gunyah_wdt can be built out of tree as one module: the driver plus a call to platform_device_register_simple. The needed symbols are exported in 6.18.2-4.
  2. **Wrong reason for UART renumbering.** The GSI-DMA flag is ignored by the UART driver, so it cannot reorder the ports. The serial aliases fix stays.
  3. **BIOS flashing wipes the chip.** The edk2 setup.sh update_spinor runs flash_erase on the whole /dev/mtd0, then writes a generic 24-byte CDT (board configuration data) and a zeroed ddr partition. Every BIOS flash therefore destroys per-board data and forces DDR retraining. This makes the full SPI dump mandatory.
  4. **Cmdline package rewrites boot entries.** radxa-system-config-kernel-cmdline-ttymsm0 0.7.4 appends clk_ignore_unused to /etc/kernel/cmdline in its postinst and re-runs kernel-install for every kernel. All radxa-system-config-* packages must be held at 0.6.30.
  5. **More hidden drift paths:**
     - qcom-iot-defaults 1.21 pulls in dragonwing-defaults 1.1.4 (machine-id-from-soc-serial, linux-firmware-dragonwing, ubuntu-release-upgrader-core).
     - radxa-firmware-qcs6490 0.2.42 depends on firmware-qcom-hlosfw, which linux-firmware-dragonwing provides, and on firmware-qcom-audioreach.
     - qcom-qnn-sdk-v68 depends on fastrpc-dev with no version, so apt would mix in fastrpc-dev 1.0.7-3.
  6. **Kioxia quirk covers one model only.** It matches only THGJFGT1E45BAILB. The stock 6.18.2-4 binary stays the default.
  7. **No kernel throttling of the NPU.** The NSP and DDR thermal zones have only a 'hot' trip at 90 °C and a critical trip at 110 °C, with no passive cooling, so the app ladder must watch them.
  8. **No BIOS upgrade needed to hold.** r2's own edk2 0.1.0-5 already carries 260120 (same imagefv stamp, 260120125234Z), so the hold can stay at 0.1.0-5.
  
  **Still open, settled only on the bench:** the A/B bootloader path, UART6 TX, the FastRPC pass on this exact set, MemTotal, UEFI QUPV3 modes, the J21 pin order and auto power-on.
- **Confirmed:**
  - Stock, 18 Oct 2026, Allnet Shopify JSON: 12 GB RS701-D12J0R44S32Y13W28 $189.99 available; 8 GB RS701-D8J0R44S32Y13W28 $159.99 not available; 6 GB 'RS701-D6' $149.99 WiFi5/BT5.4 available. Arace: every tier sold out (4/6/8/12/16 GB).
  - TinyTronics 12 GB: EUR 148.00 incl. VAT (EUR 122.31 ex.), '10+ pieces in stock', SKU 007479. TinyTronics has no 16 GB page (HTTP 404).
  - Product brief rev 1.7 (10 Oct 2026): LPDDR5 5500 MT/s in 4/6/8/12/16 GB; 1x Kryo Prime 2.7 + 3x Gold 2.4 + 4x Silver 1.9 GHz; Adreno 643 with OpenCL 2.0; M.2 M-key PCIe Gen3 x2, 2230 NVMe only (no SATA); 18 W minimum (12 V/1.5 A), 24 W (12 V/2 A) at full USB3/PCIe load; available until at least Sep 2035; 1x USB 3.1 OTG Type-A + 3x USB 2.0 Type-A. The brief does not state '12 TOPS'.
  - sbc-reviews #85 numbers: 8 GB board on kernel 6.17.1-3; 2.9 W idle, 9.3 W stress-ng --matrix, 9.5 W Geekbench, 10.1 W HPL, measured at the wall; RAM 7604 MiB.
  - dl.radxa.com: dragon-q6a_flat_build_wp_260916.zip (10.2 MiB, 13 Oct 2026). Its changelog says 'Compatile and tested with Radxa OS (Ubuntu 26)', 'Not compatible with Radxa OS (Ubuntu 24)', and that video encoding/decoding is unavailable with the hypervisor on Ubuntu 26.04. The docs download page links only 260120 and says R1+ images need 20251230 or newer.
  - edk2-qcs6490: 0.1.0-8 (17 Sep 2026) = '6.0.260916...KODIAKWP-1'; 0.1.0-9 (24 Sep 2026, sha256 1f7bcc82...0103) still carries the 260916 stamps (imagefv 260916065317Z). 0.1.0-7 (sha256 6216fc86...3b5483) and r2's 0.1.0-5 (sha256 2a311f20...51ae) both carry imagefv 260120125234Z. No postinst, so the package never flashes by itself.
  - rsetup's 'Update SPI Bootloader' calls the installed edk2 setup.sh update_spinor. rsetup system_update runs 'apt-get dist-upgrade --allow-downgrades' twice.
  - SPI NOR is 32 MiB: edl-ng log 'Device size: 32.00 MiB (33554432 bytes)', erase block 4096 B; Radxa DTS compatible winbond,w25q256. edl-ng v1.6.0 on dl.radxa.com (21 Aug 2026); the repo package is edl-ng 1.4.1.
  - qcs6490-noble Release is dated 24 Sep 2026 and lists only the 7.0.11-7 kernels. qcs6490-resolute (24 Sep 2026) has the same 7.0.11-7 kernel, edk2 0.1.0-9, fastrpc 1.0.7-3 and overlays 0.2.31. Release 6.18.2-4: image deb 68,282,992 B; headers deb 9,025,048 B, sha256 696e4279fe530e6974c5b3e388e41f82e6c02aa617cbe009115561f4a74fef2d. Tag 6.18.2-4 points src at 5bed5a3 (30 Mar 2026).
  - r2 manifest: linux-image-6.18.2-3-qcom; edk2 0.1.0-5; embloader 0.4 + sdboot-is-embloader 0.4; systemd-boot 255.4-1ubuntu8.12; fastrpc and libcdsprpc1 1.0.3-1 (no separate listener packages); radxa-firmware-qcs6490 0.2.29; radxa-overlays-dkms 0.2.18; rsetup 0.4.26; radxa-system-config-* 0.6.30; task-qcs6490 0.1.0-7; task-radxa-dragon-q6a 0.4.42; alsa-ucm-conf 1.2.14-1radxa2; linux-firmware 0ubuntu2.23; linux-firmware-dragonwing 1.0.0+20251203; qcom-iot-defaults 1.19; libgpiod 1.6.3-1.1build1; Mesa 25.2.8-0ubuntu0.24.04.1; u-boot-menu 4.2.3ubuntu1; no unattended-upgrades.
  - 6.18.2-4 config from auto.conf, all as the stack states: PPS=y; PPS_CLIENT_GPIO and PPS_CLIENT_LDISC unset; PREEMPT_DYNAMIC, NO_HZ_FULL, RCU_NOCB_CPU and DRM_LOAD_EDID_FIRMWARE =y; GPIO_PCA953X, I2C_CHARDEV, HIDRAW and ARM_SMC_WATCHDOG =y; QCOM_WDT, PWM_GPIO and SENSORS_INA238 =m; PINCTRL_MCP23S08 unset; QCOM_FASTRPC=m; DMABUF_HEAPS_SYSTEM and CMA =y; CMA_SIZE_MBYTES=32; HZ=1000; GPIO_CDEV_V1=y; SERIAL_QCOM_GENI_UART_PORTS=8. Also: GUNYAH_WATCHDOG unset, SOFT_WATCHDOG=m, PSTORE_RAM=m, QCOM_PD_MAPPER=m, OF_OVERLAY=y, OF_CONFIGFS unset.
  - sc7280.dtsi in linux-6.18.2: watchdog@17c10000 has status "reserved" /* Owned by Gunyah hyp */. No arm,smc-wdt node exists. Mainline has drivers/watchdog/gunyah_wdt.c (SMCCC calls, max_timeout 32 s), registered by qcom_scm only under Gunyah and only when no qcom,kpss-wdt or sbsa node is available.
  - Pin map from Q6A DTS gpio-line-names: GPIO0/1 = pins 13/15 (I2C0); GPIO8/9 = 27/28 (I2C2); GPIO22/23 = 8/10 (console); GPIO24/25 = 3/5; GPIO26/27 = 16/18 (UART6 TX/RX); GPIO30/31 = 32/29 (UART7 TX/RX); GPIO56 = 33; GPIO96/97/98/99/100 = 7/12/38/40/35. No Q6A DTS node or 0.2.31 overlay claims GPIO96-100 (they are only defined as mi2s0 pinctrl states).
  - radxa-overlays-dkms 0.2.31 has uart7 (exclusive spi7/uart7/i2c7/gpio30/31, pins 32 TX / 29 RX). 0.2.18 has no uart7 or uart14. The uart6, i2c0 and i2c2 bodies are identical in both versions: only the metadata changed; i2c0 and i2c2 run at 100 kHz.
  - qcom_geni_serial.c: a non-console port without an alias gets ida_alloc_range(max_alias+1, ...), so ttyHS numbers follow probe order. 'Invalid FW loaded, proto' returns -ENXIO when the serial engine holds another protocol; an empty engine gets UART firmware loaded from Linux (qupv3fw.elf).
  - hexagon-dsp-binaries HEAD 32fe407 (16 Oct 2026): qcs6490/radxa/dragon-q6a has CDSP.HT.2.5.c4-00004-KODIAK-1 and ADSP.HT.5.5.c9-00028-KODIAK-2 (WHENCE: LICENSE.qcom, Redistributable). Hashes: fastrpc_shell_3 d6ef508a...a02d; fastrpc_shell_unsigned_3 655a0032...3dff; ADSP fastrpc_shell_0 17078ae4...d68e. They are identical in radxa-firmware 0.2.29 and 0.2.42.
  - radxa-firmware-qcs6490 0.2.29 deb sha256 f59a5e5b...7e98: cdsp.mbn a9645c94... (3,612,672 B) and adsp.mbn 01fea794... (9,871,840 B). 0.2.42 (17 Sep 2026): cdsp.mbn 644cb94c... (same size, about 1.33 M bytes differ) and adsp.mbn da35227f... (14,012,896 B). Version strings and build stamps are identical (20250508_050001 and 20250819_030546). 0.2.42 adds an initramfs hook and an update-initramfs trigger; 0.2.29 has neither. 0.2.29 also ships a660_zap.mbn and qcm6490/qupv3fw.elf.
  - fastrpc: upstream tags v1.0.4 (6 Mar 2026) to v1.0.8 (11 Sep 2026); Radxa repo 1.0.7-3, which Replaces, Provides and Conflicts with qcom-fastrpc1. Issue #371 is open and marked Stale (30 Sep 2026); the maintainer said on 30 Aug 2026 that he expects the regression in 1.0.7 code.
  - QAIRT: zip v2.42.0.251225.zip answers a range-GET with content-range */1543955191 and Last-Modified 7 Jan 2026. qcom-qnn-sdk-v68 0.1.0-2 (sha256 306fd647...6e54) contains 'AISW_VERSION: 2.42.0' and v2.42.0.251225135753_193295, with libQnnHtpV68Skel.so in /usr/lib/aarch64-linux-gnu. The Radxa docs require 2.42.0.251225 with Ubuntu 22.04 / Python 3.10 and list QCS6490 as dsp_arch v68, soc_id 35. AI Hub moved to QAIRT 2.50.0 (14 Sep 2026) and removed the QCS6490 proxy (26 Jan 2026).
  - Schematic v1.21: U33 WS4612 feeds VDD_USB_VBUSTYPEA (J2) and U35 WS4612 feeds VDD_FUSB (both J5 ports) from VCC_5V_PERI; ISET resistors R229 and R235 are 3.24 kΩ. WS4612 datasheet: 2.72 kΩ gives 2.15/2.5/2.85 A and 6.8 kΩ gives 0.86/1.0/1.14 A, with 1 µA reverse current. Model: about 2.10 A typical (1.8-2.4 A).
  - Thermal trips in 6.18.2: CPU zones passive at 90 and 95 °C, critical at 110 °C; GPU passive at 95/100/105 °C, critical at 110 °C; NSP, DDR, video, camera, cpuss and aoss 'hot' at 90 °C, critical at 110 °C. The Q6A DTS adds msm-skin, quiet, ufs and xo thermistor zones.
  - Armor Case 7056A (AE036) $9.90 in stock at Allnet; Adafruit 6101 4 cm 5 V USB fan $4.95 in stock; Allnet UFS 128 GB RA022-B10J0U2 $65.90 in stock (64/256/512 GB out of stock); Adafruit 5212 in stock. On dl.radxa.com the STEP zip is dated 17 Aug 2026 and the schematic 15 Sep 2025, both v1.21.
  - systemd-bless-boot (binary, service and generator) ships in the noble systemd-boot package (noble-updates is now 255.4-1ubuntu8.17). The 260120 release notes say UEFI variables persist (needs the 6.18 kernel), the firmware auto-loads a 6.17 or 6.18 DTB if the bootloader provides none, QUP/GPIO configuration is available in UEFI, 6.17 images cannot reach the SPI flash, and alsa-ucm-conf 1.2.14-1radxa2 or newer is needed for audio.
  - embloader: tags 0.1-0.7 (0.7 = 16 Jul 2026) and HEAD 8912189 (20 Aug 2026) contain no boot-counting code. The LoaderEntryOneShot, LoaderEntryDefault and @saved variables arrive only in 37bc5b9 (authored 2 Aug, committed 20 Aug 2026; not in any tag). sdboot-is-embloader diverts systemd-bootaa64.efi and keeps the original as .distrib. systemd v255 and main boot.c have no 'overlay' handling in Type #1 entries.
  - rsetup update_entry_overlays writes 'devicetree' and 'devicetree-overlay' lines, names entries '+$tries', and picks the DTB with 'find ... -name "*${product}.dtb" | head -n 1' (wrong DTB when product is empty, as reported in forum 31391).
  - rsdk socs.json, qualcomm family: extra_ppa 'ubuntu-qcom-iot/qcom-ppa' and 'kisak/turtle'. PPA noble Release dated 16 Oct 2026: qairt-* and libqnn1 2.49.0-0ubuntu1~bpo24.04.2; linux-firmware-dragonwing 20260825 (57,175,084 B, depends linux-firmware >= ...0ubuntu2.27, installs under /usr/lib/firmware/updates/qcom/qcs6490/ with no radxa, a660 or qupv3 files); qcom-fastrpc1 1.0.15+repack2; qcom-adreno 1.855.3+rev3.
  - Forum statements re-read: strongtz in 30699 #20 ('fastrpc on cdsp doesn't need reserved DMA memory... misleading... pd-mapper is in-kernel'); 31078 #8 (DTBO memory-region + shared-dma-pool in the systemd-boot entry, plus restoring the pristine DSP payload); 30288 #2 (MODULES=most puts remoteproc into the initramfs, causing request_firmware -2); 31217 and 31234 (users: firmware c4-00004 'only supports QNN interface 2.32.0 (QAIRT 2.42)'; 2.46+ fails; INT8 only, ArcFace drops to 51%); 30896 (UKI silent reboot on 260120, reproduced by strongtz; on 14 Oct 2026 staff pointed to the 260916 zip); 31611 (strongtz 15 Oct 2026: '12V header pins can only handle 4.5V to 16V'); 30400 (BigfootACA: 3.6-16 V, SY81012, ETA3521 for the 3.3 V rail, no USB-C together with 12 V); 30852 (auto power-on differs between boards); 29642 #12 (UEFI 'Radxa Platform Configuration -> GPIO -> QUPV3_xxx Mode'); 30630 #36-#50 (Kioxia test build and the apt revert); 31304 (7.0.11-4 HDMI black, embloader 0.6 to 0.7); 31352 (two UVC cameras per USB 2.0 bus); 30452 (GNOME idle suspend).
  - Failure reports, all reproduced in the threads: 29863 (NO_MEMORY_DEVICE_DETECTED, RMA), 30841 (12 GB, CXMT, V1.21, RCW_TRAINING_FAIL after flashing 260120 and 251013), 31080 (new board, ONLY_RANK_1 after the first shutdown), 30749 (reset loop; AliExpress refund paid as store points), 31450 (cold boot never completes while EDL works), 31509 (failed after 3-4 months), 30202 (12 GB v1.214 shipped with old firmware).
- **Corrections:**
  1.
    - **Claim in stack:** C2 / 2.1: 'Allnet returns only 7 days, unused; a burn-in failure is a warranty case'; TinyTronics 'only 26 EU countries'.
    - **Finding:** Allnet refund policy: 7-day return, unused and in original packaging. Shipments into the EU also get a 14-day cooling-off period, but likewise only for unused items. Defects: 'inspect upon reception and contact us immediately'. The TinyTronics 26-country limit is still unverified (their shipping page returns 404). The user is in Europe. Allnet's $189.99 excludes EU import VAT and handling, which a buyer in Europe pays on top (not quantified).
    - **Verdict:** corrected
    - **Action:** Europe: buy only from TinyTronics (EUR 148 incl. VAT, EU seller, no import VAT). Use Allnet only if TinyTronics is out of stock. Treat any burn-in failure as a defect claim reported on the same day with UART logs, not as a return.
    - **Impact:** Clearer, cheaper purchase path for the user's region.
    - **Sources:**
      - https://shop.allnetchina.cn/policies/refund-policy
      - https://www.tinytronics.nl/en/development-boards/single-board-computers/radxa-dragon-q6a-qcs6490-12gb
  2.
    - **Claim in stack:** Stage 1 new option: buy 16 GB if Allnet, TinyTronics or Arace shows stock for no more than about $30-40 extra.
    - **Finding:** No 16 GB stock anywhere checked. Arace lists 16 GB RS701-D16J0R44S32Y13W28 as sold out at $119.50, less than its 12 GB ($169), so the price is a placeholder. TinyTronics has no 16 GB page. Allnet has no 16 GB variant.
    - **Verdict:** corrected
    - **Action:** Drop the 16 GB branch from the order plan. Buy 12 GB now.
    - **Impact:** None on the BOM. Removes a wait on a phantom SKU.
    - **Sources:**
      - https://arace.tech/products/radxa-dragon-q6a.js
      - https://shop.allnetchina.cn/products/radxa-dragon-q6a.js
  3.
    - **Claim in stack:** #22: back up SPI NOR (cdt/ddr partitions) with edl-ng before any firmware change. Stage 1: full raw 32 MiB dump. Stage 2: flash 260120 only if the board is older than 20251230.
    - **Finding:** The flash procedure itself destroys per-board data:
  - edk2 setup.sh update_spinor runs 'flash_erase /dev/mtd0 0 0' (whole chip), then 'edl-ng --hostdev-as-target /dev/mtd0 rawprogram rawprogram0.xml patch0.xml'.
  - rawprogram0.xml (28 entries, 4096-B sectors, data up to sector 6177 of about 25.3 MB) writes the generic cdt_rs701_wp.bin (a 24-byte stub per forum 30841) and zeros_5sectors.bin into 'ddr'.
  - SD_MGR, VarStore, limits, SSD, SECDATA, APDP, DPP and LOGO are left erased.
  So every reflash wipes the original CDT, the trained DDR data and any per-board blobs, and forces DDR retraining at the next cold boot, which is the stage where the reported boards die. The 260120 layout has no separate 'uefi' partition (the 251013 log still had 'UEFI (uefi.elf)'). The schematic v1.21 labels U11 'QSPI FLASH FOR BOOT' as W25Q64FWZPIG (8 MiB), but edl-ng reports 32.00 MiB and the DTS says w25q256, so the label is stale.
    - **Verdict:** corrected
    - **Action:** Before any SPI write:
  - Make two full raw reads of the whole chip (size as edl-ng reports it, expected 33,554,432 B); the two SHA-256 values must match.
  - On 6.18.2 + 260120 the on-device read is 'dd if=/dev/mtd0 bs=4096'; on an older BIOS use the EDL read. The exact edl-ng v1.6.0 read sub-command is not verified, so check it with --help.
  - Never use rsetup or setup.sh to flash.
  - If a reflash is unavoidable, flash 260120 over EDL and keep the dump for restoring cdt, ddr, DPP, SECDATA and APDP if the board fails to train.
  - Store the dump off-device together with the board serial.
    - **Impact:** Makes a reflash recoverable to factory per-board state, and explains why reflashing is high risk.
    - **Sources:**
      - https://radxa-repo.github.io/qcs6490-noble/pool/main/e/edk2-qualcomm/edk2-qcs6490_0.1.0-9_all.deb
      - https://forum.radxa.com/t/28886
      - https://forum.radxa.com/t/30841
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://raw.githubusercontent.com/radxa/kernel/559f4f921a01e5358602153364c618fe2a3e431e/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
  4.
    - **Claim in stack:** Stage 1: mirror edk2-qcs6490_0.1.0-7 (260120) and hold edk2.
    - **Finding:** r2 already ships edk2-qcs6490 and edk2-radxa-dragon-q6a 0.1.0-5. Its imagefv.elf carries the same 260120125234Z stamp as 0.1.0-7 (deb sha256 2a311f20d32ab814b6e624b304011cca822d1bbf3ece0a5904f8b43b3de951ae). 0.1.0-9 differs from -8 only on sc8280xp and still carries 260916 for qcs6490.
    - **Verdict:** corrected
    - **Action:** Hold edk2-qcs6490, edk2-radxa-dragon-q6a and edl-ng at the r2 versions (0.1.0-5, 1.4.1). Mirror 0.1.0-5 and keep 0.1.0-7 only as an archive. Add 'edk2-* (>= 0.1.0-8)' to the -1 pin list.
    - **Impact:** Removes an unneeded package change on day 1.
    - **Sources:**
      - https://github.com/radxa-pkg/edk2-qualcomm/releases/download/0.1.0-5/edk2-qcs6490_0.1.0-5_all.deb
      - https://github.com/radxa-build/radxa-dragon-q6a/releases/download/rsdk-r2/radxa-dragon-q6a_noble_gnome_r2.manifest
  5.
    - **Claim in stack:** #26 / stage 1: the Pico is the hardware watchdog; a gunyah_wdt backport 'needs a qcom_scm change, so it cannot be a simple DKMS package'.
    - **Finding:** Refuted. gunyah_wdt.c is a platform driver bound by name ('gunyah-wdt'). Mainline qcom_scm only checks the Gunyah UUID, checks that no qcom,kpss-wdt or arm,sbsa-gwdt node is available (the Q6A node is 'reserved', so none is), and calls platform_device_register_simple('gunyah-wdt'). Everything this needs is exported in the 6.18.2-4 Module.symvers: arm_smccc_hypervisor_has_uuid (GPL), __arm_smccc_smc, platform_device_register_full and watchdog_register_device (GPL). So one out-of-tree module (driver plus self-registration) builds against the held headers. Unknown: whether the 260120 WP Gunyah exposes the watchdog SMCCC service at all.
    - **Verdict:** corrected
    - **Action:** Keep the Pico heartbeat watchdog as the primary. Add an optional bench test: a lab-gunyah-wdt DKMS module. If its probe passes the STATUS call and /dev/watchdog1 appears, use it as a second layer (RuntimeWatchdogSec=20s, under the 32 s maximum). Otherwise leave it out.
    - **Impact:** Possible in-SoC hang recovery with no extra hardware. Not on the critical path.
    - **Sources:**
      - https://raw.githubusercontent.com/torvalds/linux/master/drivers/watchdog/gunyah_wdt.c
      - https://raw.githubusercontent.com/torvalds/linux/master/drivers/firmware/qcom/qcom_scm.c
      - https://github.com/radxa-pkg/linux-qcom/releases/download/6.18.2-4/linux-headers-6.18.2-4-qcom_6.18.2-4_arm64.deb
      - https://raw.githubusercontent.com/radxa/kernel/559f4f921a01e5358602153364c618fe2a3e431e/arch/arm64/boot/dts/qcom/sc7280.dtsi
  6.
    - **Claim in stack:** #79 / stage 1: ttyHS numbering depends on probe order ('GSI-DMA deferral can reorder them').
    - **Finding:** The numbering rule is confirmed, but the reason given is wrong. qcom_geni_serial.c never reads qcom,enable-gsi-dma; UART uses SE DMA, and the flag in the uart6 and uart7 overlays is a no-op. The order can still change through other probe deferrals (interconnect, power-domain, OPP), so the fix stands.
    - **Verdict:** corrected
    - **Action:** In lab-q6a.dtso, add serial1 = full path of uart6 (…/serial@998000) and serial2 = full path of uart7 (…/serial@99c000) under /aliases; take the paths from /proc/device-tree on the board. Also add udev symlinks keyed on the platform path (998000.serial to /dev/gnss0, 99c000.serial to /dev/lab/pico).
    - **Impact:** Port names stay stable regardless of probe order.
    - **Sources:**
      - https://raw.githubusercontent.com/radxa/kernel/559f4f921a01e5358602153364c618fe2a3e431e/drivers/tty/serial/qcom_geni_serial.c
  7.
    - **Claim in stack:** #25 / 5.4: kernel command line only through /etc/kernel/cmdline and kernel-install; the stack lists only lab parameters. Stage 2: hold all radxa-system-config-*.
    - **Finding:** New concrete drift path. radxa-system-config 0.7.4 (29 Sep 2026; r2 has 0.6.30): the postinst of radxa-system-config-kernel-cmdline-ttymsm0 appends ' clk_ignore_unused' to /etc/kernel/cmdline if it is missing ('HDMI workaround') and then runs 'kernel-install add' for every /boot/vmlinuz-*, which regenerates every boot entry. 0.7.2 added plymouth.enable=0. The Radxa base cmdline is 'console=ttyMSM0,115200n8 ... rw earlycon consoleblank=0 console=tty1 coherent_pool=2M irqchip.gicv3_pseudo_nmi=0 cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory swapaccount=1 kasan=off', plus root=UUID.
    - **Verdict:** new_risk
    - **Action:** Hold radxa-system-config-* at 0.6.30. Write /etc/kernel/cmdline as the full line: r2's base line exactly as found on first boot (record it), then the lab additions. Never only the lab additions. Do not add clk_ignore_unused on Path A unless the HDMI test needs it, since it leaves unused clocks running (an RF-spur and power cost). CI check: SHA-256 of /etc/kernel/cmdline and /proc/cmdline.
    - **Impact:** Prevents a silent cmdline change and entry regeneration on one upgrade, and prevents losing root= or console= when lab parameters are added.
    - **Sources:**
      - https://github.com/radxa-pkg/radxa-system-config/blob/main/debian/radxa-system-config-kernel-cmdline-ttymsm0.postinst
      - https://radxa-repo.github.io/noble/pool/main/r/radxa-system-config/radxa-system-config-kernel-cmdline-ttymsm0_0.7.4_all.deb
  8.
    - **Claim in stack:** Stage 2 hold and PPA finding: mirror qcom-iot-defaults 1.19 and linux-firmware-dragonwing; -1 pin on qairt-* and qcom-fastrpc*.
    - **Finding:** Two more transitive pulls:
  (1) qcom-iot-defaults 1.21 is a transitional package that depends on dragonwing-defaults 1.1.4. That package Provides machine-id-from-soc-serial, depends on linux-firmware-dragonwing, linux-image-qcom and ubuntu-release-upgrader-core, and Breaks qcom-iot-defaults < 1.21.
  (2) radxa-firmware-qcs6490 0.2.42 depends on 'firmware-qcom-hlosfw | firmware-qcom-soc | linux-firmware-qualcomm-misc' and on firmware-qcom-audioreach. linux-firmware-dragonwing 20260825 Provides firmware-qcom-hlosfw and needs linux-firmware >= 0ubuntu2.27, so one firmware upgrade drags in the PPA firmware and a newer linux-firmware.
    - **Verdict:** new_risk
    - **Action:** Add to the hold list: qcom-iot-defaults 1.19, linux-firmware 20240318.git3b128b60-0ubuntu2.23, radxa-firmware 0.2.29. Add to the -1 pins: dragonwing-defaults, firmware-qcom-audioreach, firmware-qcom-soc, linux-firmware-qualcomm-misc, qairt-dsp-binaries, qnn-tools, snpe-tools, libsnpe*. CI: 'apt-get -s dist-upgrade' must show 0 changes against the full source list.
    - **Impact:** Closes the remaining upgrade paths that could change firmware or machine-id.
    - **Sources:**
      - https://ppa.launchpadcontent.net/ubuntu-qcom-iot/qcom-ppa/ubuntu/dists/noble/main/binary-arm64/Packages.gz
      - https://radxa-repo.github.io/noble/dists/noble/main/binary-arm64/Packages
  9.
    - **Claim in stack:** #24 / stage 1: pin fastrpc, libcdsprpc1, the listener libraries, fastrpc-dev and fastrpc-test to one Phase-0 version (1.0.4-1). Stage 2: install fastrpc-dev 1.0.4-1 or ship the libcdsprpc.so symlink (forum 31144).
    - **Finding:** radxa-pkg/fastrpc 1.0.4-1 release assets exist (sha256: fastrpc 715b61ae0b5b4366..., libcdsprpc1 3bcf469fee422a80..., fastrpc-dev 492982e2f8806b7a..., fastrpc-test eea7a9af61a9d2ef...).
  - The fastrpc 1.0.4-1 package itself ships /usr/lib/libcdsprpc.so, libadsprpc.so, libsdsprpc.so and the listener .so symlinks, so the 31144 symlink step applies to Armbian, not to RadxaOS with 1.0.4-1.
  - 1.0.4-1 ships no udev rule and no fastrpc group.
  - Its built-in DSP search path is ';/usr/lib/rfsa/adsp;/usr/lib/dsp;', plus YAML from /usr/share/qcom/conf.d/.
  - qcom-qnn-sdk-v68 Depends on 'fastrpc-dev' with no version, so installing it from the repo would pull fastrpc-dev 1.0.7-3 and skew versions.
    - **Verdict:** corrected
    - **Action:** Install the whole 1.0.4-1 set (fastrpc, libcdsprpc1, libadsprpc1, libsdsprpc1, lib{a,c,s}dsp-default-listener1, fastrpc-dev, fastrpc-test) from the GitHub release before qcom-qnn-sdk-v68, then hold it. Ship your own udev rule (KERNEL=="fastrpc-*" and dma_heap/*, GROUP="fastrpc", MODE="0660") and a sysusers.d fastrpc group. Set ADSP_LIBRARY_PATH="/usr/lib/aarch64-linux-gnu;/usr/lib/dsp/cdsp;/usr/lib/rfsa/adsp". Keep the symlink check only as a CI assertion.
    - **Impact:** Prevents a mixed 1.0.4/1.0.7 stack on the first QNN install.
    - **Sources:**
      - https://github.com/radxa-pkg/fastrpc/releases/download/1.0.4-1/fastrpc_1.0.4-1_arm64.deb
      - https://github.com/radxa-pkg/fastrpc/releases/download/1.0.4-1/libcdsprpc1_1.0.4-1_arm64.deb
      - https://radxa-repo.github.io/qcs6490-noble/dists/qcs6490-noble/main/binary-arm64/Packages
      - https://forum.radxa.com/t/31144
  10.
    - **Claim in stack:** #36 / stage 2: use exactly one DSP-boot method (our initramfs copy hook).
    - **Finding:** Confirmed. 0.2.29 has no hook. 0.2.42's hook is 'cp -r /lib/firmware/qcom/qcs6490/radxa/* ${DESTDIR}/lib/firmware/qcom/qcs6490/radxa' plus an update-initramfs trigger. Forum 30288: MODULES=most pulls the remoteproc modules into the initramfs, which then load firmware before /lib/firmware exists (error -2). The DTS firmware-name paths are qcom/qcs6490/radxa/dragon-q6a/{adsp,cdsp}.mbn and qcom/qcs6490/a660_zap.mbn; qupv3fw is qcom/qcm6490/qupv3fw.elf.
    - **Verdict:** confirmed
    - **Action:** Ship /etc/initramfs-tools/hooks/lab-dsp-fw. It copies the dragon-q6a {adsp,cdsp}.mbn and *.jsn and a660_zap.mbn into the initramfs, and checks their SHA-256 against the 0.2.29 values at build time. CI: no 'request_firmware failed: -2' in dmesg on 20 cold boots.
    - **Impact:** DSPs boot every time with the pinned binaries.
    - **Sources:**
      - https://forum.radxa.com/t/30288
      - https://radxa-repo.github.io/noble/pool/main/r/radxa-firmware/radxa-firmware-qcs6490_0.2.42_all.deb
      - https://github.com/radxa-pkg/radxa-firmware/releases/download/0.2.29/radxa-firmware-qcs6490_0.2.29_all.deb
  11.
    - **Claim in stack:** #23/#25 and stage 2: A/B via systemd-boot boot counting. Stage 2 option (a): purge sdboot-is-embloader and use systemd-boot 255.4 with a merged DTB; it cites forum 30896 for real systemd-boot working.
    - **Finding:** Confirmed: embloader (all tags, and HEAD) has no boot counting, and systemd-boot (v255 and main) has no devicetree-overlay. Correction: the 30896 user who booted real systemd-boot used systemd 260.2 on Gentoo with kernel 7.0.11, not 255.4 with Radxa's 6.18 DTB, so option (a) is unproven on this stack. Further facts:
  - rsetup writes 'devicetree-overlay' lines that real systemd-boot ignores silently, so overlays vanish without a merged DTB.
  - noble-updates now has systemd-boot 255.4-1ubuntu8.17 (r2 has 8.12).
    - **Verdict:** corrected
    - **Action:** Primary (a): 'apt purge sdboot-is-embloader' (restores the .distrib binary), then 'bootctl install'. Build one merged DTB per kernel with 'fdtoverlay -i qcs6490-radxa-dragon-q6a.dtb -o lab.dtb lab-q6a.dtbo' through your own kernel-install plugin. Set 'devicetree' explicitly, /etc/kernel/tries=3 and boot-complete.target. Hold systemd-boot and systemd-boot-efi at one version (8.12 from r2, or 8.17, mirrored).
  Fallback (b), my own design and untested: keep embloader 0.4 held with a 'write-back default' trial. The update sets loader.conf 'default' to root B, B's initramfs immediately resets it to A, and B sets it permanently only after boot-complete. A failure before the initramfs still needs the rescue microSD.
    - **Impact:** Gives real automatic fallback in the field, or makes clear what remains manual.
    - **Sources:**
      - https://github.com/BigfootACA/embloader
      - https://raw.githubusercontent.com/systemd/systemd/v255/src/boot/efi/boot.c
      - https://forum.radxa.com/t/30896
      - https://radxa-repo.github.io/noble/pool/main/e/embloader/sdboot-is-embloader_0.7_all.deb
      - https://packages.ubuntu.com/noble-updates/arm64/systemd-boot/filelist
  12.
    - **Claim in stack:** Stage 2: replace Path B with a self-built 'linux-image-6.18.2-4+lab1' from 559f4f9; use it if the UFS is Kioxia, 'or by default if the A/B build test passes'.
    - **Finding:** 559f4f9 adds a single table entry { UFS_VENDOR_TOSHIBA (0x198), model "THGJFGT1E45BAILB", UFS_DEVICE_QUIRK_PA_TACTIVATE }. It is two commits ahead of 6.18.2-4 (5bed5a3); the other commit is a Radxa ZERO DTS fix. A Kioxia part with a different model string gets nothing from it. The fault shows on power-mode transitions (START STOP UNIT, resume).
    - **Verdict:** corrected
    - **Action:** Keep the stock 6.18.2-4 binary as the default for Samsung (wManufacturerID 0x1CE). Build +lab1 only if day-1 shows vendor 0x198, and if the model string differs, add that model to the quirk table. Bench mitigation to test first: no system suspend plus UFS rpm_lvl=0 (no SSU transitions). Drop 7.0.11 and clk_ignore_unused from v1.
    - **Impact:** Avoids maintaining a self-built kernel unless the hardware needs it.
    - **Sources:**
      - https://github.com/radxa/kernel/commit/559f4f921a01e5358602153364c618fe2a3e431e
      - https://forum.radxa.com/t/30630
  13.
    - **Claim in stack:** #16 / 5.6: drop ladder at 80/85 °C; 'Tj max 95 °C; throttling about 90-91 °C'.
    - **Finding:** 95 °C is the second CPU passive step, not Tj max; critical is 110 °C. Only the CPU and GPU zones have passive cooling. nspss0/1 (NPU), ddr, video and camera have only a 'hot' trip at 90 °C and a critical trip at 110 °C, so the kernel never throttles the HTP. A runaway NPU load runs until the 110 °C critical shutdown.
    - **Verdict:** corrected
    - **Action:** The labd and labclassify ladder must read the cpu*, gpuss*, nspss0/1 and ddr zones. At 80 °C on any of them: pause the trainer and reduce the HTP duty cycle. At 85 °C: stop the HTP inference loop. Keep the fan on at 60 °C and off at 50 °C. Log the skin, ufs and xo zones.
    - **Impact:** Prevents an NPU-driven critical shutdown in the sun.
    - **Sources:**
      - https://raw.githubusercontent.com/radxa/kernel/559f4f921a01e5358602153364c618fe2a3e431e/arch/arm64/boot/dts/qcom/sc7280.dtsi
  14.
    - **Claim in stack:** Stage 2: 'sbc-reviews #85 (strongtz, Dec 2025): retail boards shipped with firmware 251013, and r2 needs 20251230 or newer'.
    - **Finding:** sbc-reviews #85 says only 'Retail boards should have been shipped with the latest firmware (251013)'. The 20251230 requirement comes from the Radxa download page. The 7604 MiB figure was measured on 6.17.1-3 with an unstated firmware.
    - **Verdict:** corrected
    - **Action:** Fix the citations only. The day-1 dmidecode check stands. Expect 251013, 260120 or 260916 on a board bought in Oct 2026.
    - **Impact:** Accurate sourcing; no design change.
    - **Sources:**
      - https://github.com/geerlingguy/sbc-reviews/issues/85
      - https://raw.githubusercontent.com/radxa-docs/docs/main/i18n/en/docusaurus-plugin-content-docs/current/dragon/q6a/download.md
  15.
    - **Claim in stack:** Stage 1 (#21/#69): the Android 15 RC 'Limited the M.2 M-Key slot to PCIe 2.0' suggests thin Gen3 margins.
    - **Finding:** The text is confirmed, but it is from the Android 15 RC (20261008) release notes and Android's own device tree. It is no evidence about Linux 6.18 margins. A Samsung 980 trained at Gen3 x2 on Linux (forum 26723, per stage 2).
    - **Verdict:** corrected
    - **Action:** Keep Gen2 (max-link-speed=2) as the default only for the riser path (Lime). Gen3 needs the 60-minute zero-AER test.
    - **Impact:** Lime only; no change.
    - **Sources:**
      - https://raw.githubusercontent.com/radxa-docs/docs/main/i18n/en/docusaurus-plugin-content-docs/current/dragon/q6a/download.md
  16.
    - **Claim in stack:** #15 / C4: J21 pin 1 = 12 V, pin 2 = GND, pin 3 = PWR key; input 4.5-16 V.
    - **Finding:** Radxa staff confirm the range: strongtz 4.5-16 V (15 Oct 2026); BigfootACA 3.6-16 V with 5/9/12 V recommended. The schematic text puts J21 (CON_1X3) between ADP12V_IN and PWR_ON_KEY with ESD5311N diodes, which suggests pin 1 = ADP12V_IN, pin 2 = GND, pin 3 = PWR_ON_KEY, but the text extraction cannot prove the order. Auto power-on with 12 V applied differs between boards (forum 30852).
    - **Verdict:** unverified
    - **Action:** Before wiring, check J21 by continuity: pin to C602-area input caps, GND and PWR key. Keep regulated 12 V. Keep the Pico rule: pulse pin 3 if the Q6A 3.3 V is absent 1-2 s after power is restored.
    - **Impact:** Avoids a wrong-polarity or wrong-pin connection on the main power input.
    - **Sources:**
      - https://forum.radxa.com/t/31611
      - https://forum.radxa.com/t/30400
      - https://forum.radxa.com/t/30852
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
  17.
    - **Claim in stack:** 5.5: about 11.3 GiB visible on 12 GB; stage 1: up to 0.5 GiB less with the WP firmware.
    - **Finding:** Still unmeasured. Model: 8 GB board 8192 - 7604 = 588 MiB reserved. Scaled to 12 GB, with an extra 64 MiB of struct-page metadata (64 B per 4 KiB page), that gives 11,636 MiB = 11.36 GiB. Minus the unverified 512 MiB WP penalty: 10.86 GiB. The WP reserved-memory layout change (b486ae6) is real; its size is not published.
    - **Verdict:** unverified
    - **Action:** Keep the W1-2 MemTotal gate on 260120 + 6.18.2-4. Plan with 10.9 GiB (model) for the with-Lime training row.
    - **Impact:** Small; only the with-Lime training case is tight.
    - **Sources:**
      - https://github.com/geerlingguy/sbc-reviews/issues/85
- **New risks:**
  - **BIOS flash wipes the chip.** Every SPI flash through setup.sh/rsetup erases the whole chip, writes a generic 24-byte CDT and a zeroed DDR-training partition, and leaves SECDATA, DPP, APDP, SSD and VarStore empty. The forced DDR retraining at the next cold boot is the stage where the reported boards fail.
  - **Cmdline package upgrade.** radxa-system-config-kernel-cmdline-ttymsm0 0.7.4 rewrites /etc/kernel/cmdline (adds clk_ignore_unused) and re-runs kernel-install for every kernel during an ordinary upgrade.
  - **PPA defaults package.** qcom-iot-defaults 1.21 pulls dragonwing-defaults 1.1.4 (machine-id-from-soc-serial, ubuntu-release-upgrader-core, linux-firmware-dragonwing).
  - **Firmware dependency chain.** radxa-firmware-qcs6490 0.2.42 needs firmware-qcom-hlosfw or audioreach providers, which pull PPA firmware and a newer linux-firmware.
  - **QNN install pulls new fastrpc-dev.** qcom-qnn-sdk-v68 depends on fastrpc-dev with no version, so installing it from the repo mixes fastrpc-dev 1.0.7-3 into a held 1.0.4-1 stack.
  - **No NPU throttling.** The NSP and DDR thermal zones have no passive cooling; the kernel never throttles the HTP before the 110 °C critical shutdown.
  - **Kioxia quirk is model-specific.** It covers only THGJFGT1E45BAILB; other Kioxia UFS model strings stay exposed to the resume and OCS errors.
  - **Schematic flash label is stale.** v1.21 labels the boot flash W25Q64FWZPIG (8 MiB) while the populated part is 32 MiB. A dump script that hard-codes 8 MiB would be truncated; use the size edl-ng reports.
  - **Stage 2 option (a) is unproven here.** No report shows real systemd-boot 255.4 with Radxa's 6.18 DTB on 260120; the only report is systemd 260.2 with kernel 7.0.11.
  - **fastrpc 1.0.4-1 has no udev rule or group.** Without ours, /dev/fastrpc-* permissions break non-root inferd-htp (the same failure class as the group-at-startup change in issue #371).
  - **Return and warranty terms.** Allnet's 7-day and EU 14-day returns require unused goods, so burn-in failures fall to the defect path. AliExpress RMAs have ended in store points (forum 30749).
- **Refuted findings:**
  1.
    - **Finding:** Stage 1: a gunyah_wdt backport 'needs a qcom_scm change, so it cannot be a simple DKMS package'.
    - **Why:** gunyah_wdt binds by platform-device name, and qcom_scm only calls platform_device_register_simple('gunyah-wdt') after a UUID check. Every symbol needed is exported in the 6.18.2-4 Module.symvers (arm_smccc_hypervisor_has_uuid GPL, __arm_smccc_smc, platform_device_register_full, watchdog_register_device). One out-of-tree module that registers its own device works. Whether the WP Gunyah offers the service is a separate, open question.
  2.
    - **Finding:** Stage 1: 'GSI-DMA deferral can reorder' the UART6/UART7 ttyHS numbering.
    - **Why:** qcom_geni_serial.c has no GSI handling; qcom,enable-gsi-dma is read only by the I2C and SPI drivers, so the flag is a no-op on UARTs. Probe order can still vary for other reasons, so the alias fix stays, but this mechanism is wrong.
  3.
    - **Finding:** Stage 2: on RadxaOS, Genie/QNN need a hand-made libcdsprpc.so symlink (cited from forum 31144).
    - **Why:** Thread 31144 is about Armbian. The radxa-pkg fastrpc 1.0.4-1 package already ships /usr/lib/libcdsprpc.so, libadsprpc.so, libsdsprpc.so and the listener .so symlinks, so the step is unnecessary with the pinned set.
  4.
    - **Finding:** Stage 2: forum 30896 supports option (a), real systemd-boot 255.4 on 260120.
    - **Why:** The 30896 report is systemd 260.2 (Gentoo) with kernel 7.0.11. It shows that non-embloader EFI loaders start on 260120, not that Ubuntu's systemd-boot 255.4 with Radxa's 6.18.2-4 DTB boots.
  5.
    - **Finding:** Stage 2: 'sbc-reviews #85 (strongtz, Dec 2025): ... r2 needs 20251230 or newer'.
    - **Why:** sbc-reviews #85 never mentions 20251230; that requirement is on the Radxa download page. The substance holds, the attribution does not.
  6.
    - **Finding:** Stage 2: use the self-built 6.18.2-4+lab1 'by default if the A/B build test passes'.
    - **Why:** The only functional change in 559f4f9 is one quirk entry for model THGJFGT1E45BAILB. For the planned Samsung UFS (0x1CE) it changes nothing and adds a self-built kernel to maintain. The default should stay the stock 6.18.2-4 binary.
  7.
    - **Finding:** Stage 1: an edk2 0.1.0-7 mirror is needed to get 260120.
    - **Why:** r2's own edk2-qcs6490 0.1.0-5 carries the same 260120 stamp (imagefv 260120125234Z), so holding the shipped version is enough.
- **Corrected spec:** ## Board and purchase
  - **Radxa Dragon Q6A 12 GB**, RS701-D12J0R44S32Y13W28, Wi-Fi 6/BT 5.4.
  - **Europe (primary):** TinyTronics NL, EUR 148.00 incl. VAT (EUR 122.31 ex.), 10+ in stock on 18 Oct 2026. The USD figure ($166.37) uses a model rate.
  - **Fallback:** ALLNET $189.99 plus EU import VAT and handling. 7-day or EU 14-day return, unused only.
  - Not 8 GB (sold out), no 16 GB (no stock anywhere), never AliExpress.
  - Also from Allnet: UFS 128 GB RA022-B10J0U2 $65.90; Armor 7056A $9.90; RTC battery $0.95.
  
  ## Day 1, inside the return window
  1. UART console on pins 8/10 (ttyMSM0, 115200).
  2. Record:
     - `dmidecode -s bios-version` (target 6.0.260120.BOOT.MXF.1.0.1-00549-KODIAKWP-1);
     - board revision;
     - LPDDR vendor from the XBL log;
     - UFS wManufacturerID and model.
  3. Two full raw SPI reads with matching SHA-256 (expected 33,554,432 B).
     - On 6.18.2-4 + 260120: `dd if=/dev/mtd0 bs=4096`.
     - Otherwise: an EDL read with edl-ng v1.6.0.
  4. Reflash only if the BIOS is older than 20251230 or is 260916. Use EDL with flat_build_wp_260120 only.
  5. Archive offline with SHA-256: 260120.zip (10.9 MiB), 260916.zip (10.2 MiB) and edl-ng-dist-v1.6.0.zip (31.3 MiB).
  6. Burn-in: 12 h stressapptest + memtester; 50-100 cold boots; a 1-2 h HTP loop with large DMA buffers alongside memtester.
  
  ## Base OS and kernel
  - RadxaOS r2, noble, output_4096 image for UFS.
  - **Before any apt upgrade**, dpkg -i from GitHub release 6.18.2-4:
    - linux-image-6.18.2-4-qcom (68,282,992 B);
    - linux-headers-6.18.2-4-qcom (9,025,048 B, sha256 696e4279fe530e6974c5b3e388e41f82e6c02aa617cbe009115561f4a74fef2d);
    - linux-image/headers-radxa-dragon-q6a 6.18.2-4.
  - Keep 6.18.2-3 as the rescue entry.
  - Kioxia UFS (0x198): build 6.18.2-4+lab1 from radxa/kernel 559f4f9, adding the model string if it differs. Otherwise stay on stock 6.18.2-4.
  - No 7.0.x, no 260916, no UKI.
  
  ## Holds (apt-mark hold plus aptly at priority 1001)
  - **Kernel:** 6.18.2-4 image, headers and metapackages.
  - **BIOS and recovery:** edk2-qcs6490 and edk2-radxa-dragon-q6a 0.1.0-5; edl-ng 1.4.1; rsetup and rsetup-config-first-boot 0.4.26.
  - **Bootloader** (one of):
    - option a: systemd-boot and systemd-boot-efi 255.4-1ubuntu8.12 (or 8.17, mirrored) with sdboot-is-embloader purged;
    - option b: embloader 0.4 + sdboot-is-embloader 0.4.
  - **Also held:** u-boot-menu 4.2.3ubuntu1; radxa-overlays-dkms 0.2.18.
  - **Firmware:** radxa-firmware and radxa-firmware-qcs6490 0.2.29 (deb sha256 f59a5e5b14d95650c9d248ae223fa293b753530ebb46bb96e27e635b0f457e98; cdsp.mbn a9645c94..., adsp.mbn 01fea794...); linux-firmware 20240318.git3b128b60-0ubuntu2.23; linux-firmware-dragonwing 1.0.0+20251203; qcom-iot-defaults 1.19.
  - **System config:** radxa-system-config-* 0.6.30; task-qcs6490, task-qualcomm, task-qualcomm-npu and task-qualcomm-gstreamer 0.1.0-7; task-radxa-dragon-q6a 0.4.42; alsa-ucm-conf 1.2.14-1radxa2; aic8800-usb-dkms and aic8800-firmware 4.0+git20250410.b99ca8b6-5.
  - **FastRPC set 1.0.4-1** (from GitHub, installed before QNN): fastrpc, libcdsprpc1, libadsprpc1, libsdsprpc1, lib{a,c,s}dsp-default-listener1, fastrpc-dev, fastrpc-test.
  - **QNN:** qcom-qnn-sdk-v68 0.1.0-2 (sha256 306fd647b88902d170831980ca68a31d77d77923534e2070783fbeca132a6e54).
  - **Graphics and desktop:** Mesa 25.2.8-0ubuntu0.24.04.4; libdrm2 2.4.125-1ubuntu0.1~24.04.2; labwc 0.7.1-1build1; xwayland, wlroots, qt6, pipewire.
  
  ## -1 pins and sources
  - **-1 pins:**
    - linux-image-7.* and linux-headers-7.*; edk2-* (>= 0.1.0-8);
    - qairt-*, libqnn*, libsnpe*, qnn-tools, snpe-tools;
    - qcom-fastrpc*, qcom-adreno*, dragonwing-defaults;
    - firmware-qcom-audioreach, firmware-qcom-soc, linux-firmware-qualcomm-misc;
    - kisak Mesa.
  - **Sources:** remove ubuntu-qcom-iot/qcom-ppa, kisak/turtle and mozillateam. The field image uses only the signed aptly repo.
  - **Tools:** never run rsetup System Update or Update SPI Bootloader.
  - **CI checks:**
    - `apt-get -s dist-upgrade` shows 0 changes;
    - no launchpad origin;
    - `dpkg -V` is clean for the firmware and FastRPC packages;
    - SHA-256 of /etc/kernel/cmdline.
  
  ## Boot
  - BLS Type #1 entries only, written by our own kernel-install plugin (not rsetup).
  - Every entry has an explicit `devicetree`.
  - Option a uses a merged DTB built with fdtoverlay (base 6.18.2-4 DTB + lab-q6a.dtbo).
  - Never rebuild the base DTB from source.
  - /etc/kernel/tries=3 plus boot-complete.target (option a only).
  - /etc/kernel/cmdline = r2's full base line as found on first boot (console=ttyMSM0,115200n8 … coherent_pool=2M irqchip.gicv3_pseudo_nmi=0 … kasan=off, root=UUID), followed by:
    - `preempt=full drm.edid_firmware=HDMI-A-1:edid/field.bin video=HDMI-A-1:1920x1080@60`;
    - with Lime also: `pcie_aspm=off isolcpus=nohz,domain,managed_irq,7 nohz_full=7 rcu_nocbs=7 irqaffinity=0-6`.
  - No clk_ignore_unused.
  - Mask sleep, suspend, hibernate and hybrid-sleep targets; set IdleAction=ignore.
  
  ## DT overlay lab-q6a.dtbo (fragments copied from radxa-overlays 0.2.31)
  - **uart6:** spi6 and i2c6 disabled; pins 16 TX / 18 RX (GPIO26/27).
  - **uart7:** spi7 and i2c7 disabled; pins 32 TX / 29 RX (GPIO30/31).
  - **i2c0:** 100 kHz, pins 13 SDA / 15 SCL (GPIO0/1).
  - **i2c2:** 100 kHz, pins 27 SDA / 28 SCL (GPIO8/9).
  - **/aliases:** serial1 = uart6 path (…serial@998000), serial2 = uart7 path (…serial@99c000).
  - **PPS:** pps-gpio on tlmm 96 (pin 7); the pps-gpio.ko DKMS builds against the held headers (pps_register_source is exported).
  - **Optional FastRPC fragment**, only if Phase 0 shows that it changes the result: memory-region = <&adsp_rpc_remote_heap_mem>, and compatible "shared-dma-pool" on the reserved node @0xc6500000 (8 MiB).
  - **UEFI:** the QUPV3 modes are SE0/SE2 = I2C and SE6/SE7 = UART (or not loaded); note them with the SPI dump.
  - **libgpiod:** address lines by TLMM chip label.
  
  ## NPU
  - Firmware: CDSP.HT.2.5.c4-00004-KODIAK-1 / ADSP.HT.5.5.c9-00028-KODIAK-2 from the 0.2.29 payload.
  - Shell hashes:
    - fastrpc_shell_3 d6ef508a4051429bb231b8e1323683d847cb6dcc1b83af187c60f97c36a5a02d;
    - fastrpc_shell_unsigned_3 655a003255ae01d8b9c3eb2e978765d7dacbdf1ac5c7cf7ac8e171ac09f03dff;
    - fastrpc_shell_0 17078ae470a13477a6f6b0663a0cd828cdd5d109c3b1ee9f3f02bff70108d68e.
  - Initramfs hook lab-dsp-fw copies the dragon-q6a mbn/jsn files and a660_zap.mbn, with a hash check.
  - udev rule for fastrpc-* and dma_heap/* (group fastrpc, mode 0660) plus a sysusers.d group.
  - ADSP_LIBRARY_PATH="/usr/lib/aarch64-linux-gnu;/usr/lib/dsp/cdsp;/usr/lib/rfsa/adsp".
  - QAIRT 2.42.0.251225 everywhere: the device deb, and the host zip (1,543,955,191 B), archived with SHA-256.
  - dsp_arch v68, soc_id 35 (Radxa docs) until 35 vs 93 is compared; VTCM 2 MB; INT8 w8a8.
  - Never AI Hub artifacts (its QCS6490 proxy was removed in Jan 2026).
  
  ## Watchdog and recovery
  - Primary: the Pico heartbeat over UART7. On loss, the Pico cuts power through #2813 OFF, restores it, then pulses J21 pin 3 if the 3.3 V rail does not appear within 1-2 s.
  - No QCOM_WDT (the node is reserved).
  - Optional lab-gunyah-wdt DKMS module, used only if its probe passes.
  
  ## USB and VBUS
  - U35 WS4612 is shared by both J5 ports (bottom = blue USB 3.1, USB0/EDL); U33 WS4612 feeds J2.
  - Current limit (model): about 2.10 A typical (1.8-2.4 A) per switch, RSET 3.24 kΩ.
  - Reverse current 1 µA.
  - At most one isochronous device on the FE1.1s tree.
  
  ## M.2 (only with Lime)
  - 2230 NVMe, Gen3 x2 on pcie1.
  - Through the riser: max-link-speed=2 by default; Gen3 only after 60 min with zero AER errors.
  
  ## Cooling
  - Copper block of 35x35 mm or less plus a 40 mm 5 V two-wire fan (Adafruit 6101, $4.95, add a flyback diode), switched on and off by a Pico FET: on at 60 °C, off at 50 °C.
  - Armor 7056A only if the 15 mm covers fit.
  - Kernel trips: CPU passive 90/95 °C; GPU passive 95/100/105 °C; NSP and DDR 'hot' at 90 °C with no cooling; critical 110 °C everywhere.
  - App ladder on the maximum of cpu*, gpuss*, nspss* and ddr:
    - 80 °C: pause the trainer and reduce the HTP duty cycle;
    - 85 °C: stop HTP inference.
  - Train only when the SoC is below 75 °C.
  
  ## Power
  - J21 fed with regulated 12 V (staff-stated range 4.5-16 V).
  - Probable pin order 1 = ADP12V_IN, 2 = GND, 3 = PWR_ON_KEY; verify by continuity.
  - Never together with USB-C.
  - Budget: 2.9 W idle, 9.3-10.1 W CPU load measured at the wall (8 GB board); 18 W minimum, 24 W with full USB3/PCIe load.
- **Bench tests:**
  - **B1. Identification and SPI dump (day 1):**
  - Record: dmidecode BIOS string; board revision silkscreen; LPDDR manufacturer ID from the UART XBL log; UFS vendor/model (/sys/class/scsi_device/*/device/vendor and model, plus the device descriptor manufacturer ID).
  - Two full SPI reads; SHA-256 equal; size 33,554,432 B.
  - **B2. MemTotal:** /proc/meminfo on 12 GB with 260120 + 6.18.2-4. Pass if 10.9 GiB or more (model 10.86-11.36 GiB). Re-run the RAM table with the measured value.
  - **B3. Bootloader A/B, option a:**
  - purge sdboot-is-embloader; bootctl install; merged lab.dtb via fdtoverlay; tries=3.
  - Pass: 20 cold boots each show the lab nodes in /sys/firmware/devicetree/base (aliases, pps, uart7).
  - A deliberately broken root B (init=/bin/false) falls back to A after 3 tries, and systemd-bless-boot marks the good entry.
  - If it fails: option b (embloader 0.4 with write-back default) and the rescue-microSD drill.
  - **B4. UART6/UART7:**
  - Read the UEFI QUPV3 modes.
  - dmesg has no 'Invalid FW loaded' or 'UART firmware load failed'.
  - TX-to-RX jumper loopback at 115200 and 921600 on both ports, 1e6 bytes with zero errors.
  - After 20 reboots, /dev/ttyHS1 resolves to 998000.serial and /dev/ttyHS2 to 99c000.serial.
  - LC76G answers $PQTMVERNO.
  - **B5. PPS:** the pps-gpio DKMS module loads on GPIO96; 'ppstest /dev/pps0' gives 1 Hz with a 3D fix; 'chronyc sourcestats' shows a PPS offset under 1 µs after 30 min. pinmux-pins shows one owner per header pin.
  - **B6. FastRPC Phase 0:**
  - 'dpkg -V radxa-firmware-qcs6490 fastrpc libcdsprpc1' clean; SHA-256 of cdsp.mbn, adsp.mbn and the three shells match the spec.
  - fastrpc_test -a v68 passes 3/3 both with and without the shared-dma-pool fragment; ship the fragment only if the results differ.
  - No remoteproc '-2' in 20 cold boots.
  - 8 h soak with a CDSP stop/start every 30 min: zero hangs and zero fsck events.
  - **B7. QNN 2.42:**
  - qnn-net-run on the HTP with the ADSP_LIBRARY_PATH from the spec.
  - VTCM 2 MB succeeds and 4 MB fails as reported; compare soc_id 35 vs 93.
  - Per-channel conv-weight encoding: qnn-context-binary-generator compiles and the result runs on the device.
  - INT8 SpecDet vs FP32 on the CPU: AP drop of 2 points or less per class family, with BatchNorm folded.
  - **B8. Optional Gunyah watchdog:**
  - Build lab-gunyah-wdt DKMS (gunyah_wdt.c plus a platform_device_register_simple shim) and modprobe it.
  - Pass: the probe's STATUS call succeeds and /dev/watchdog1 exists.
  - Then a sysrq hang test: the board resets within 32 s.
  - If the probe fails, drop it.
  - **B9. Thermal:**
  - 45 min HTP + CPU load in the closed enclosure, logging cpu*, gpuss*, nspss0/1, ddr, skin, ufs and xo.
  - Confirm that NSP is not throttled by the kernel, and that the app ladder acts at 80/85 °C before any zone reaches 90 °C.
  - **B10. VBUS:** with an e-load or the FNB58 on the J5 pair, find the U35 trip current (model 1.8-2.4 A). Pass if the sum of the planned J5 loads stays under 1.5 A. Check 0 V backfeed on every Q6A USB port with the Q6A off and LAB5 on.
  - **B11. J21 and power-on:**
  - Continuity map of J21 against the schematic (ADP12V_IN, GND, PWR_ON_KEY).
  - With 12 V applied: note whether the board auto-starts.
  - The Pico pulse starts it every time in 20 power cycles.
  - Run at 11.0 V and at 16.0 V input.
  - **B12. Package drift CI:**
  - With all original r2 sources re-enabled in a test chroot, 'apt-get -s dist-upgrade' lists 0 changes to held or pinned packages.
  - Installing qcom-qnn-sdk-v68 keeps fastrpc-dev at 1.0.4-1.
  - 'apt-cache policy' shows no launchpad origin in the field image.
  - /etc/kernel/cmdline hash is unchanged after a simulated reinstall of radxa-system-config 0.6.30.
  - **B13. UFS (only if Kioxia):**
  - First 24 h of fio with system suspend masked and rpm_lvl=0; zero 'OCS invalid' or 'pa_err' events.
  - If errors appear: build and test 6.18.2-4+lab1 with the read model string in the quirk table.
  - **B14. M.2 slot (in the return window even without Lime):** a 2230 NVMe enumerates and passes 60 min of fio with zero AER errors. With the Lime riser: Gen2 by default; Gen3 only after zero AER in 60 min.
- **Confidence:** medium

