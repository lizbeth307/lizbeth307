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

