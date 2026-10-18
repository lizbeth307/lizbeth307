# Mech thermal storage: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_d9388111-e66`_

- **Subsystem:** mech_thermal_storage (case, layout, thermal with 2000-nit display, Q6A, optional Lime and pack; connectors; kit bags; storage: 128 GB UFS, T7 / microSD, rolling caps)
- **Findings:**
  1.
    - **Claim in stack:** Storage: Radxa UFS 3.1 128 GB RA022-B10J0U2, ALLNET China $65.90 / TinyTronics EUR 58 (2-4 weeks); 256 GB Kioxia not to be taken
    - **Finding:** Re-checked 18 Oct 2026. ALLNET sells 128GB RA022-B10J0U2 for $65.90 and has it in stock. Its 64GB (RA022-B10J0U1, $19), 256GB (RA022-B10J0U4, $75.90) and 512GB (RA022-B10J0U8, $89.90) are out of stock. TinyTronics sells RA022-B10J0U2 for EUR 58.00 incl. VAT (EUR 47.93 ex), shown as 'Not in stock, 2-4 Weeks'. Arace has every UFS capacity out of stock (128G listed at $49). The ALLNET listing still points to the Radxa eMMC/UFS module reader, which is out of stock ($12.99).
    - **Verdict:** confirmed
    - **Action:** Keep. Buy the 128 GB from ALLNET together with the board. Treat 256/512 GB as unavailable.
    - **Impact:** Price and stock unchanged; the only in-stock world source remains ALLNET.
    - **Sources:**
      - https://shop.allnetchina.cn/products/high-performance-ufs-3-1-module
      - https://www.tinytronics.nl/en/data-storage/modules/radxa-ufs-module-128gb
      - https://arace.tech/products/radxa-ufs-module
  2.
    - **Claim in stack:** UFS 1703 MB/s read / 388 MB/s write (Samsung KLUDG4UHDC); write speed only within a WriteBooster cache of about 4 GiB; sustained write unknown
    - **Finding:** Radxa's Q6A UFS page gives dd figures: Samsung KLUDG4UHDC-B0E1 128GB 1703/388 MB/s, Kioxia THGJFGT1E45BAILB 256GB 1811/557 MB/s. The Radxa UFS product brief (rev 1.2, 2026-01-13) claims 'up to 2100 MB/s read and 1800 MB/s write with WriteBooster', host-dependent. It lists 64 GB-1 TB and an optional industrial grade (-25 to +85 C). Neither document states the WriteBooster cache size, so 'about 4 GiB' has no primary source.
    - **Verdict:** confirmed
    - **Action:** Keep 388 MB/s as the planning figure. Mark the 4 GiB WriteBooster size as unverified and measure it at bring-up (fio sequential fill past 10 GiB).
    - **Impact:** No design change. Worst-case raw stream is 13.3 MB/s, so even a slow post-cache rate is fine.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
      - https://dl.radxa.com/accessories/ufs-module/rad-doc-0154_radxa_ufs_module_product_brief__revision_1.2_g69c4d5d.pdf
  3.
    - **Claim in stack:** The Kioxia UFS quirk exists only in kernel 7.0.11-7, not in the held 6.18.2-4
    - **Finding:** radxa/kernel PR #551 ('ufs: qcom: add PA_TACTIVATE quirk for Kioxia THGJFGT1E45BAILB') was merged on 11 May 2026 into the linux-6.18.2 branch. The current linux-6.18.2 ufs-qcom.c contains the THGJFGT1E45BAILB / UFS_DEVICE_QUIRK_PA_TACTIVATE entry. On 18 May 2026 Radxa staff wrote that 'linux-image 6.18 has not released a new version. We will update to linux-image 7.0'. Armbian 26.05 carries the fix. So the quirk is in the 6.18.2 source branch, but probably not in the 6.18.2-4 binary package.
    - **Verdict:** corrected
    - **Action:** Reword: 'fix is in the radxa linux-6.18.2 branch since 11 May 2026 but not in the published 6.18.2-4 package; a self-built 6.18.2 kernel or 7.0.11 has it'. Keep the decision to avoid the Kioxia module; it is out of stock anyway.
    - **Impact:** Wording only. It opens a path to 256 GB later via a kernel rebuild.
    - **Sources:**
      - https://github.com/radxa/kernel/pull/551
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/drivers/ufs/host/ufs-qcom.c
      - https://forum.radxa.com/t/ufs-random-reboots/30630?page=3
  4.
    - **Claim in stack:** UFS manufacturer ID 0x01CE = Samsung, 0x0198 = Kioxia
    - **Finding:** Mainline include/ufs/ufs_quirks.h defines UFS_VENDOR_SAMSUNG 0x1CE and UFS_VENDOR_TOSHIBA 0x198. Kioxia is the former Toshiba memory business and keeps the Toshiba ID.
    - **Verdict:** confirmed
    - **Action:** Keep the on-arrival ID check.
    - **Impact:** None.
    - **Sources:**
      - https://raw.githubusercontent.com/torvalds/linux/master/include/ufs/ufs_quirks.h
  5.
    - **Claim in stack:** UFS operating range 0-70 C; 'UFS and T7 are rated from 0 C' (cold rule)
    - **Finding:** The 0-70 C range has no primary source. The Radxa module brief gives no range for the standard module and only mentions an optional industrial version (-25 to +85 C), which is not offered in the ALLNET or Arace listings. No datasheet for KLUDG4UHDC-B0E1 was found. A reseller lists the sibling Samsung UFS 3.1 KLUEG8UHGC-B0E1 at -25 to +85 C. The T7 range (0-60 C) is confirmed separately.
    - **Verdict:** unverified
    - **Action:** Mark the UFS 0-70 C range as unverified. Keep the conservative 'no operation of storage below 0 C' rule. Replace the modelled UFS temperature with the measured board thermistor (see next finding).
    - **Impact:** The cold rule stays as a conservative assumption, not a spec.
    - **Sources:**
      - https://dl.radxa.com/accessories/ufs-module/rad-doc-0154_radxa_ufs_module_product_brief__revision_1.2_g69c4d5d.pdf
      - https://trustcompo.com/product/detail/TCE000026953-KLUEG8UHGC-B0E1
  6.
    - **Claim in stack:** Thermal section 5.6: UFS about 60 C and other temperatures are model-only until the midday soak test
    - **Finding:** The Q6A device tree in radxa/kernel linux-6.18.2 defines board-thermistor zones read through the PMK8350 ADC: ufs-thermal (ADC_TM ch3), msm-skin-thermal (ch2), quiet-thermal (ch1) and xo-thermal (ch0). None has trips, so they are read-only sensors. Mainline also has ufs-hwmon, which reports the UFS device's own case temperature (QUERY_ATTR_IDN_CASE_ROUGH_TEMP) where the device supports it.
    - **Verdict:** new_option
    - **Action:** Log ufs-thermal and msm-skin-thermal (and the ufs hwmon if it is present) in labpowerd. Use them in the 45-minute midday acceptance and the derating ladder instead of model values. Check /sys/class/thermal/*/type at bring-up.
    - **Impact:** Measured UFS and skin temperatures at no BOM cost.
    - **Sources:**
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://raw.githubusercontent.com/torvalds/linux/master/drivers/ufs/core/ufs-hwmon.c
  7.
    - **Claim in stack:** SoC: Tj max 95 C; throttling about 90-91 C ('verified, forum 30123')
    - **Finding:** Forum thread 30123 states neither a Tj max nor a throttle threshold. Its only figure is one user (17 May 2026) whose CPU/GPU 'would exceed 90C' with throttling in the passive Armor case at 35-40 C ambient; a glued-on 5 V fan removed the throttling. The device-tree trips (radxa linux-6.18.2 sc7280.dtsi and mainline kodiak.dtsi) are: CPU passive at 90 C and 95 C, critical shutdown at 110 C; GPU passive at 95/100/105 C, critical 110 C; NSP and DDR at 90 C, critical 110 C. So 95 C is the second throttle step, and shutdown is at 110 C.
    - **Verdict:** corrected
    - **Action:** Rewrite as: 'kernel throttles CPU at 90 C (second step 95 C), GPU from 95 C, critical shutdown 110 C'. Keep the labd derating ladder at 80/85 C and the training gate below 75 C.
    - **Impact:** Gives 15 K more margin to shutdown than stated; throttling starts where the stack assumed.
    - **Sources:**
      - https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/arch/arm64/boot/dts/qcom/sc7280.dtsi
      - https://raw.githubusercontent.com/torvalds/linux/master/arch/arm64/boot/dts/qcom/kodiak.dtsi
  8.
    - **Claim in stack:** Cooling: 'Radxa Armor 7056A OR stepped Cu block (32x31 mm zone)' + 40 mm 5 V fan; ALLNET $9.90, Arace $4.99
    - **Finding:** Prices and stock confirmed: ALLNET AE036 at $9.90 in stock, Arace at $4.99 in stock. However, the Armor Case 7056A is a passive, fanless two-piece metal enclosure, not a heatsink. Per ALLNET the top cover is 70x56x15 mm and the bottom cover 85x56x15 mm; Radxa lists the contents as top cover, bottom cover, 2 thermal pads and 4 screws, with no fan. The bottom shell sits between the board and the 2 mm Al mid-plate. That blocks direct board-to-plate mounting and the UFS pad path, because the UFS sits on the board underside. Model: the two shells add roughly 30 mm of stack height, which strains the 55-60 mm case depth. Radxa still sells no official active cooler for the Q6A; a passive Armor alone was reported throttling above 90 C at 35-40 C ambient.
    - **Verdict:** new_risk
    - **Action:** In the handheld, make the stepped Cu block (with a pad on the LPDDR5) plus a 40 mm fan the primary cooler, mounted on the board top side. Use the Armor case only for bench/home or after a STEP v1.21 fit check. Do not treat the two options as interchangeable in CAD.
    - **Impact:** Avoids a depth and mounting conflict and keeps the UFS-to-plate heat path. Cost difference is about $10-25 (Cu block price unverified).
    - **Sources:**
      - https://radxa.com/products/accessories/armor-case-7056a
      - https://shop.allnetchina.cn/products/radxa-heatsink-7056a
      - https://arace.tech/products/radxa-armor-case-7056a
      - https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
  9.
    - **Claim in stack:** Fan: Adafruit 6101 40 mm 5 V ($4.95); thermal model assumes two air paths totalling about 5.4 m3/h, h about 10 W/m2K
    - **Finding:** Adafruit 6101 is a '5V Square USB Fan - 4 cm': 40x40x10.6 mm, 5 V 0.2 A (about 1 W), 32 mm hole pitch, coiled USB-A lead about 1 m. $4.95, in stock. Adafruit lists no airflow, static pressure, RPM or bearing. The 5.4 m3/h model input therefore cannot be tied to a spec. Noctua NF-A4x10 5V is fully specified: 8.2 m3/h max, 1.78 mmH2O max static pressure, 0.22 W typical, 17.9 dB(A), 0-4500 rpm. QuietPC lists the 5 V FLX at GBP 13.96 (about $18.6; reseller, not re-verified). Arithmetic check: dT = P/(rho*cp*Vdot) at 5.4 m3/h gives 9.8 / 12.7 / 20.8 / 30.6 K for 17 / 22 / 36 / 53 W. That matches the stated exit rises, so the model is self-consistent. But a 40x10 fan's roughly 17 Pa maximum pressure through a Cu fin block, stainless mesh and hydrophobic foam may not deliver about 2.7 m3/h per path.
    - **Verdict:** new_risk
    - **Action:** Either keep the 6101 and measure path airflow at bring-up (anemometer or a dT-at-known-power method), or specify the NF-A4x10 5V for a known fan curve. Size the intake foam area for at most 5 Pa drop. Keep DC on/off control (the Q6A has no fan header).
    - **Impact:** The thermal margins in 5.6 depend on an airflow figure that currently has no source.
    - **Sources:**
      - https://www.adafruit.com/product/6101
      - https://noctua.at/en/products/fan/nf-a4x10-5v/specification
      - https://www.quietpc.com/nf-a4x10-flx-5v
  10.
    - **Claim in stack:** Thermal model built for the old 210x135x52 mm box; plan D15 is 220-225 x 135-140 x 55-60 mm, so the model must be recalculated
    - **Finding:** Recalculated (model). At 222.5x137.5x57.5 mm the external surface is 0.103 m2 against 0.093 m2 for the old box (+11%), giving about 1.03 W/K passive at h=10. The front face is 0.0306 m2 (+8%), so the solar term scales from 13.5-17 W to about 14.6-18.4 W. Forced-air exit rises do not depend on box size. Net change is small: under 1 K on the mean internal air in modes B and D.
    - **Verdict:** confirmed
    - **Action:** Update 5.6 with the D15 numbers: solar 14.6-18.4 W (model), passive 1.0 W/K. Keep forced air mandatory, since a 36 W peak would need about 35 K passive rise.
    - **Impact:** Confirms forced cooling is required; no part changes.
    - **Sources:** []
  11.
    - **Claim in stack:** Q6A footprint 85x56 mm from Radxa STEP v1.21; holes; CAD from STEP v1.21
    - **Finding:** The Radxa download page still lists every hardware file (schematic, 2D, DXF, STEP, placement) at V1.21 as of 18 Oct 2026. The 2D drawing shows 85.0x56.0 mm, 4x dia 3.5 mm holes on a 58.0x49.0 mm pattern (M2.5 hardware), and the UFS/eMMC B2B connectors on the underside. Product brief rev 1.5 (2026-04-28) warns that the 'board layout or component locations may change over time'. Wall power (Geerling, 8 GB board): 2.9 W idle, 9.3-10.1 W under full CPU load.
    - **Verdict:** confirmed
    - **Action:** Keep. Before printing, confirm the delivered board matches V1.21 against the STEP.
    - **Impact:** None.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/download
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_2d_dimensions_v1.21.pdf
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
      - https://github.com/geerlingguy/sbc-reviews/issues/85
  12.
    - **Claim in stack:** UFS is pressed by a pad against a case boss (about 60 C)
    - **Finding:** The UFS module is on the board underside, which faces the 2 mm Al mid-plate. A boss on the printed ASA case is a poor heat path; polymer conductivity is around 0.2 W/mK (general value, not from a datasheet). The module is held only by two B2B connectors (TinyTronics lists mounting as 'Clamp'). A pad pressing it against a metal boss therefore also adds shock retention in a handheld.
    - **Verdict:** corrected
    - **Action:** Change to: 'UFS pressed by a 1-1.5 mm pad onto a raised boss on the Al mid-plate'. Verify with the ufs-thermal zone.
    - **Impact:** Better UFS cooling and retention at no cost.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_2d_dimensions_v1.21.pdf
      - https://www.tinytronics.nl/en/data-storage/modules/radxa-ufs-module-128gb
  13.
    - **Claim in stack:** Boot order USB > SD > NVMe > eMMC > UFS; rescue microSD kept outside the case; no ESP on data media
    - **Finding:** Radxa's quick-start page states 'Boot priority: USB > microSD > NVMe SSD > eMMC Module > UFS Module', and the UFS install guide (SPI BIOS path) needs no hardware change. However, Radxa's boot page also documents a 'boot directly from UFS' mod (remove R137, fit 10 kOhm at R207), after which the board 'will no longer be able to boot the system from a microSD card, eMMC module, or NVMe SSD'.
    - **Verdict:** new_risk
    - **Action:** Add to the build notes: never perform the R137/R207 mod; boot UFS via the SPI BIOS (UEFI) only, so microSD rescue keeps working. Keep the 'no ESP on data media' rule, because any bootable SD or USB stick takes priority.
    - **Impact:** Protects the recovery plan.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/getting-started/quickly-start
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/boot
      - https://docs.radxa.com/en/dragon/q6a/getting-started/install-system/ufs-system/no-ufs-reader
  14.
    - **Claim in stack:** Service hatch: UART console and access to the blue USB-A for EDL with an A-A cable; recovery kit ALLNET 64 GB microSD + Adafruit 5212 + 6324 + A-A cable = $31.89; Radxa RA019 reader sold out
    - **Finding:** EDL needs the EDL button held while power is applied, then a USB-A to USB-A cable on the USB 3.1 Type-A port. The hatch spec does not mention the button. Prices: ALLNET 64GB microSDXC UHS-1 (ALN-TFUHS1-64) $16.99, in stock, 42 MB/s write / 80.6 MB/s read. Adafruit 5212 USB-C microSD reader $6.95, in stock. Adafruit 6324 USB-C-to-A 2 m cable $2.95, 93 in stock. ALLNET eMMC/UFS Module Reader $12.99, out of stock. Total without the A-A cable is $26.89, consistent with $31.89.
    - **Verdict:** new_risk
    - **Action:** Make the EDL button reachable through the service hatch, or wire it to a recessed pushbutton. Keep the recovery kit prices.
    - **Impact:** Without button access, EDL recovery means opening the case.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/low-level-dev/edl-mode
      - https://shop.allnetchina.cn/products/allnet-micro-sd
      - https://www.adafruit.com/product/5212
      - https://www.adafruit.com/product/6324
  15.
    - **Claim in stack:** Blue USB 3.1 port: T7 limit 395 MB/s (1.76x the Lime 224 MB/s); USB 3 near GNSS/L-band is a known jammer, so T7 never writes during L-band, S-band or GNSS sessions
    - **Finding:** The Q6A device tree shows one QMP USB/DP combo PHY: lanes 0-1 go to the RA620 HDMI bridge and lanes 2-3 to the USB-A port. HDMI and the blue port therefore share one PHY, a single noise source zone. The 395 MB/s figure is a single unattributed data point (no adapter, parameters or sustained run), so it is unverified. Intel's USB 3.0 RFI white paper shows the USB 3 data spectrum is broadband from DC to 5 GHz and that a connected drive raised the 2.4 GHz noise floor by nearly 20 dB. That supports the no-write-during-L-band/GNSS rule.
    - **Verdict:** confirmed
    - **Action:** Keep the rule and the layout (RF bay away from the HDMI/J5 edge). Mark 395 MB/s as unverified; measure with fio on the actual T7 at bring-up, only if Lime is kept.
    - **Impact:** The Lime storage headroom (1.76x) rests on one unverified figure.
    - **Sources:**
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://www.usb.org/sites/default/files/327216.pdf
  16.
    - **Claim in stack:** Second storage without Lime: V30 endurance microSD 128-256 GB; Q6A microSD measured write 61 MB/s = 4.6x the worst stream 13.3 MB/s
    - **Finding:** Geerling (Q6A 8 GB, Samsung Pro+ 32 GB, iozone): 1M sequential write 61.45 MB/s and read 73.70 MB/s, but 1M random write only 2.32 MB/s and 4K random write 0.80 MB/s. The SD I/O supply (vreg_l6c, 1.65-3.544 V) allows UHS-I 1.8 V signalling. The 4.6x and 2.3x ratios check out (61/13.3, 30/13.3).
    - **Verdict:** confirmed
    - **Action:** Keep. Add: recorders write large preallocated sequential files to microSD; no journald, SQLite or small-file workloads on microSD; occupancy DB stays on UFS.
    - **Impact:** Avoids random-write stalls on the card.
    - **Sources:**
      - https://github.com/geerlingguy/sbc-reviews/issues/85
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
  17.
    - **Claim in stack:** V30 endurance microSD price $25-82 (model, prices unstable)
    - **Finding:** $25 is a 2024 deal price. Slickdeals price tracker (updated 5 Apr 2026) for Samsung PRO Endurance 256 GB: Amazon $81.99, Newegg $115.85, Best Buy $153.99, Samsung $153.99. RS Netherlands showed it temporarily out of stock in January 2026, and RS Hong Kong noted expected shortages. No October 2026 price was found.
    - **Verdict:** corrected
    - **Action:** Budget $82-154 for 256 GB (or buy 128 GB). Keep it as 'buy when NAND prices allow'. Re-price at order time.
    - **Impact:** Optional tier rises by about $0-70 at the top end.
    - **Sources:**
      - https://slickdeals.net/f/17686464-25-256gb-samsung-pro-endurance-uhs-i-microsdxc-memory-card-w-sd-adapter-at-amazon
      - https://benl.rs-online.com/web/p/sd-cards/0566936
  18.
    - **Claim in stack:** Samsung T7 1 TB $229.99-274.99 (B&H/Samsung snippets, unverified); outside on the bottom edge; rated 0-60 C; Lime only
    - **Finding:** Samsung T7 datasheet rev 2.0: operating 0-60 C (Tc at the hottest case point; 'sufficient airflow is recommended'), non-operating -40 to 85 C, 85x57x8 mm, 72 g, USB 3.2 Gen2, up to 1050/1000 MB/s. A new variant, 'T7 Resurrected' (MU-PD1T0G and siblings, 2025 datasheet, created Dec 2025), has the same specs and ships with a C-to-C cable only. ssd-tester: 42 GB pSLC cache and a 614 MB/s average over 100 GB, which implies about 480 MB/s after the cache (model) and covers 224 MB/s. Price: PCWorld (8 Jun 2026) reported $190 at Amazon against an 'absurd street price' of $275, tied to the storage shortage. No October price was obtained (Samsung and B&H returned 403). Risk: a T7 strapped to the bottom edge in sun can exceed the 60 C case limit.
    - **Verdict:** unverified
    - **Action:** Keep the T7 only with Lime. Re-price at the C1 gate (expect $190-275). Mount it on the shaded side with a sun flap and log its SMART temperature. The T7 Shield (IP65, rugged) is the better-suited option for an outside mount; its price was not verified.
    - **Impact:** Optional tier only; the price may come in $40-85 lower than the stated range.
    - **Sources:**
      - https://download.semiconductor.samsung.com/resources/data-sheet/Samsung_Portable_SSD_T7_Datasheet_Rev2.0.pdf
      - https://download.semiconductor.samsung.com/resources/data-sheet/Samsung_Portable_SSD_T7_Resurrected_Datasheet_Rev.1.0.pdf
      - https://ssd-tester.com/samsung_portable_ssd_t7_1tb.html
      - https://www.pcworld.com/article/3158933/samsung-fast-t7-portable-ssd-finally-drops-in-price-190-was-285.html
  19.
    - **Claim in stack:** Lime (optional): 10 W heat path via pedestal and pad of at least 6 W/mK; ship date 15 Dec 2026; $249 + $18
    - **Finding:** Crowd Supply (18 Oct 2026): LimeSDR Micro M.2 2280 Basic $249, GNSS $299, shipping $18 worldwide, pre-order, 'Orders placed now ship Dec 15, 2026'. Board 22x80 mm, top-side height about 4 mm, TMP1075 sensor on board; no power or temperature spec is given. A MyriadRF team member (24 Aug 2026) said the board 'should consume about 4 W, depending on configuration'. The 2.5 A at 3.3 V (8.25 W) figure is the PCIe slot limit, not consumption.
    - **Verdict:** corrected
    - **Action:** Keep the 10 W pedestal design as a margin. Change the thermal modes H and I to use about 4 W typical for the Lime (8.25 W ceiling), and log TMP1075.
    - **Impact:** Lime-build thermal modes are conservative by about 4-6 W.
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
      - https://discourse.myriadrf.org/t/limesdr-micro-m-2-power-consumption/13304
  20.
    - **Claim in stack:** Case material: light-grey ASA (PETG rejected because it softens at 75-80 C); ASA 1 kg + CNC Kitchen M3 inserts (EUR 9.40)
    - **Finding:** Polymaker PolyLite ASA TDS: Tg 98 C, Vicat 105 C, HDT 100 C at 1.8 MPa and 103 C at 0.45 MPa; needs an enclosed printer, bed at 75-95 C. Polymaker shop: ASA 1 kg Grey $26.99, White $25.99, in stock. CNC Kitchen Heat Set Insert M3x5.7, 100 pcs (TC-M3x5.7), EUR 9.40, in stock.
    - **Verdict:** confirmed
    - **Action:** Keep ASA. Print in an enclosure or use a print service.
    - **Impact:** None.
    - **Sources:**
      - https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polylite-tm-asa
      - https://shop.polymaker.com/products/asa
      - https://cnckitchen.store/products/heat-set-insert-m3-x-5-7-100-pieces
  21.
    - **Claim in stack:** Top edge: P1-P7 (incl. F port P4) at 20 mm pitch, optional P8; with Lime also RX1, RX2 and REF IN; case 220-225 mm wide
    - **Finding:** Model: without Lime, 8 ports need 140 mm of centre span (about 150 mm with nuts), which fits. With Lime, 11 ports need 200 mm of centre span plus about 5 mm nut half-width at each end, about 210 mm. The top edge is 220-225 mm outside, minus walls and corner radii, leaving roughly 0-5 mm margin. That collides with the right HMI column and HF+ shield corner.
    - **Verdict:** new_risk
    - **Action:** In the Lime top strip, put RX2 and REF IN on the left side wall, or use a second staggered row. Keep 20 mm pitch for gloves.
    - **Impact:** Avoids a forced reprint or squeezed glove-unfriendly pitch.
    - **Sources:** []
  22.
    - **Claim in stack:** IMU socket GX12 on the rear wall; weather target IPX4/IP54
    - **Finding:** Generic GX12 4-pin datasheets (Olimex via DigiKey) state temperature, vibration and 5 A ratings but no IP rating; DigiKey's ingress field is blank. IP65/IP67 claims come only from seller listings.
    - **Verdict:** new_risk
    - **Action:** Specify a 4-pin circular connector whose datasheet gives an IP67 mated rating (M8/M12 class), or fit a tethered cap on the GX12 and test with spray. The same check applies to the 6-pin LAB BUS and the USB-C inlet (use capped or gasketed parts).
    - **Impact:** Keeps the IPX4/IP54 claim honest.
    - **Sources:**
      - https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/5560/Olimex%20-%20CONNECTOR-GX12-4.pdf
      - https://olimex.com/Products/Components/Connectors/CONNECTOR-GX12-4
  23.
    - **Claim in stack:** Bench kit case: Pelican 1450 (14.5 L, filled about 8.8 L = 61%) or Apache 3800; Pelican figures unverified (403)
    - **Finding:** Retailers (Pelican site returned 403): 1450 interior 14.66x10.24x6.12 in (about 15.0 L, listed as 0.53 ft3); weight 6.39 lb (2.9 kg) with foam, 5.51 lb empty. Apache 3800 (Harbor Freight; US stores only): interior 14-7/8 x 10-5/8 x 6-1/8 in, IP65; current Harbor Freight price not verified (resellers list $42.99-49.99).
    - **Verdict:** corrected
    - **Action:** Use 15.0 L (fill about 59%) and 2.9 kg case weight. Outside the US, the Pelican 1450 or an equivalent IP65 case is the world option.
    - **Impact:** Minor.
    - **Sources:**
      - https://www.wiltronics.com.au/product/67862/1450-pelican-protector-case-with-foam-filler/
      - https://www.glazerscamera.com/collections/hard-cases/products/pelican-1450-black
      - https://superarbor.io/products/63927-3800-weatherproof-protective-case-large-black
  24.
    - **Claim in stack:** Travel: the home-built 72 Wh pack never flies (IATA requires UN 38.3); Anker 737 and Li-cell instruments in carry-on; Pelican may be checked
    - **Finding:** IATA passenger lithium battery guidance says: 'Batteries must be of a type that meets the requirements of the UN Manual of Tests and Criteria, Part III, subsection 38.3'. Spare batteries and power banks are carry-on only, with terminals protected. Batteries of 100 Wh or less inside equipment may go in checked bags.
    - **Verdict:** confirmed
    - **Action:** Keep. Add: the checked Pelican must contain no spare cells (e.g. the 5th Molicel) and no power banks.
    - **Impact:** None.
    - **Sources:**
      - https://www.iata.org/contentassets/6fea26dd84d24b26a7a1fd5788561d6e/passenger-lithium-battery.pdf
  25.
    - **Claim in stack:** Battery bay 46x25x150 mm in an insulated compartment; cells about 68 g; IP2368 charge window 0-45 C
    - **Finding:** Molicel INR-21700-P50B TDS: max diameter 21.55 mm, max height 70.15 mm, max weight 71 g. A 2x2 layout is 43.1 x 21.55 x 140.3 mm bare, which fits 46x25x150 with about 3 mm per axis for nickel, Kapton and the barrier. Charge -20 to 60 C and discharge -40 to 60 C per the TDS, so the 0-45 C IP2368 window is conservative.
    - **Verdict:** confirmed
    - **Action:** Keep the bay size. Use 71 g per cell (284 g for the cells) in the weight table.
    - **Impact:** About +12 g.
    - **Sources:**
      - https://www.fsaeonline.com/content/Molicel-TDS--INR-21700-P50B-80122.pdf
  26.
    - **Claim in stack:** Rolling caps and partitions: ESP 1 + root A 22 + root B 22 + /data about 74 GiB; raw cap 30 GiB; NPU 20 GB; rates 18.4 / 36.9 / 48 GB/h; 30 GiB is about 40 min; ring 1.5 GiB is about 98 s; Lime 224 MB/s is about 74 min/TB; Burst 7 GiB is about 30 s
    - **Finding:** Recomputed. 128e9 B = 119.2 GiB, and 1+22+22+74 = 119 GiB, leaving only about 0.2 GiB. 2xV4L cu8 + HF+ ci16 = 13.31 MB/s = 47.9 GB/h, so the 30 GiB cap lasts 40.3 min. Ring 1.5 GiB at 16.38 MB/s = 98.3 s (121 s if ci16). A 15-minute HRPT pass is 4.61 GB. Lime ci16 is 224 MB/s = 74.4 min/TB; 7 GiB at 640 MB/s with a 395 MB/s drain lasts about 30.7 s. /data leftover after quotas is 46.6 GiB. All figures match.
    - **Verdict:** confirmed
    - **Action:** Define /data as 'rest of device' rather than a fixed 74 GiB, because the module's exposed capacity may be under 128e9 B. Keep the caps.
    - **Impact:** Avoids a partitioning failure on a slightly smaller UFS.
    - **Sources:** []
  27.
    - **Claim in stack:** Display thermal: panel about 71 C at 35 C in sun at 100% (above the 70 C rating); sustained about 1000 nits at midday
    - **Finding:** The 70 C panel rating is not documented for the Wisecoco 6.97in panel; vendor pages for similar 7in panels give conflicting values (-20 to 70 C and -10 to 60 C). The panel thermal model and the 2000-nit duty limits rest on this unverified number.
    - **Verdict:** unverified
    - **Action:** Make the operating temperature one of the written Wisecoco questions (already in D5). Until answered, plan derating from 60 C (50%) as in 5.6 and validate with the panel NTC.
    - **Impact:** May lower the sustained brightness ceiling if the rating is 60 C.
    - **Sources:** []
- **Current status oct 2026:** Status as of 18 Oct 2026:
  - **Radxa Dragon Q6A:** all hardware files (schematic, 2D, DXF, STEP) are still V1.21. Product brief is rev 1.5 (2026-04-28). The download page still lists SPI BIOS flat_build_260120. Android 15 RC images dated 20261008 were added (the UFS image needs provision_ufs31.xml). ALLNET has the 12 GB board (RS701-D12J0R44S32Y13W28) in stock at $189.99.
  - **Kernel:** the Kioxia UFS quirk (PR #551) was merged into radxa/kernel linux-6.18.2 on 11 May 2026. Radxa said it would move packages to 7.0 rather than re-release 6.18. Armbian 26.05 carries the fix.
  - **Radxa UFS 128 GB (RA022-B10J0U2):**
    - ALLNET: $65.90, in stock. Its 64/256/512 GB are out of stock.
    - TinyTronics: EUR 58, not in stock, 2-4 weeks.
    - Arace: all capacities out of stock.
    - Radxa eMMC/UFS reader: out of stock at ALLNET.
  - **Radxa Armor Case 7056A (AE036):** ALLNET $9.90 and Arace $4.99, both in stock. Radxa still has no official active cooler for the Q6A.
  - **Adafruit (all in stock):** 6101 fan $4.95; 5212 reader $6.95; 6324 cable $2.95.
  - **ALLNET 64 GB microSD:** $16.99, in stock.
  - **Samsung T7:** datasheet unchanged (0-60 C). A 'T7 Resurrected' variant (MU-PD*) appeared with a 2025 datasheet. Prices are shortage-inflated: about $190 deal against $275 street in June 2026. No October figure was obtained (Samsung and B&H returned 403).
  - **microSD endurance cards:** shortage pricing, e.g. Samsung PRO Endurance 256 GB $82-154 in April 2026.
  - **LimeSDR Micro M.2:** pre-order, $249 + $18 shipping, ships 15 Dec 2026. About 4 W typical per MyriadRF (Aug 2026).
  - **Case materials:** Polymaker ASA 1 kg $25.99-26.99, in stock. CNC Kitchen M3 inserts EUR 9.40 per 100, in stock.
  - **No EOL notices** were found for any part in this subsystem.
- **Notes:** Method: primary pages fetched on 18 Oct 2026. Sources were Radxa docs and product briefs, Shopify product JSON for ALLNET, Arace, CNC Kitchen and Polymaker, radxa/kernel and mainline device-tree and driver sources, Samsung datasheets, the Polymaker TDS, the IATA PDF, Crowd Supply, MyriadRF discourse, the Radxa forum, and Geerling's sbc-reviews. I used 14 WebSearch calls.
  
  Blocked or rate-limited:
  - pelican.com, samsung.com and B&H returned 403.
  - noctua.at and the Gelid pages returned 429 or 404. Noctua specs come from Noctua's spec page via search snippets.
  - The Pelican 1450 and Apache 3800 figures are from retailers.
  
  Model calculations (not measurements) were run in Python: air rise, case surface, port span, partitions, rates and the T7 post-cache estimate.
  
  Unverified and left as such: the UFS operating range and WriteBooster size, the 395 MB/s USB write figure, prices for the Cu block and blower, the T7 and T7 Shield price in October, the Wisecoco panel temperature rating, and the Gelid pad specs.
  
  The main design changes to carry into stage 2/6:
  1. The Armor 7056A is a two-shell enclosure. It is not a drop-in alternative to the Cu block inside the handheld.
  2. Fan airflow is unspecified for the Adafruit 6101. Measure it or use the NF-A4x10 5V.
  3. Pad the UFS to the Al plate, not to the printed case.
  4. Never do the R137/R207 UFS-boot mod.
  5. Expose the EDL button in the service hatch.
  6. Lime top-edge port crowding.
  7. Specify IP-rated circular connectors.
  8. Correct the SoC thermal trips (90/95 C throttle, 110 C critical).
  
  Files used:
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/storage.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/mechanical_thermal.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/final_world_sourcing.json
  
  Downloaded primary files were kept in separate directories under /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/ (dl_kodiak, dl_ufsbrief, dl_q6abrief, dl_q6a2d, dl_t7, dl_shop*, dl_iata, dl_usbrfi).

