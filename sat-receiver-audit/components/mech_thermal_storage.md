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

## Адверсаріальна перевірка (`verify`)

_Run `wf_d9388111-e66`_

- **Subsystem:** mech_thermal_storage: case, layout and thermal design (2000-nit display, Q6A, Lime and pack); connectors; kit bags; storage (Samsung 128 GB UFS, T7 / microSD, rolling caps). Stage 3 adversarial re-verification, 18 Oct 2026.
- **Verdict:** Most stage 1 and stage 2 findings hold up against primary sources: Radxa docs, briefs, the 2D drawing and schematic V1.21, the radxa/kernel 6.18.2 DTS, sc7280.dtsi, ufs-qcom.c, Shopify stock JSON, the Samsung/Molicel/Polymaker datasheets, Radxa forum raw threads and Crowd Supply. Seven items are refuted or misattributed:
  - Noctua "0.22 W typical, 0-4500 rpm".
  - The Samsung PRO Endurance tracker prices; the cited page does not show them.
  - The Geerling rsetup/Etcher attribution.
  - "7.0.11 HDMI breakage confirms the hold"; Radxa posted a workaround.
  - The "+30 mm" Armor stack height.
  - Apache 3800 as a world option; it is US in-store only, and the user is in Europe.
  - The stack's "Tj max 95 C / throttle 90-91 C".
  
  New risks from primary sources:
  1. Per the governing requirements, the Lime build is now the DEFAULT. So the T7 1 TB, the 11-port top edge and the J21 desolder all become the baseline, not options.
  2. J21 is a 3-pin header (12 V / GND / PWR_ON_KEY). A desolder must rewire all three pins.
  3. Any VBUS on the Q6A USB-C turns on the back-to-back PMOS Q5 and ties USB-C VBUS to the J21 12 V rail. A USB-C opening for EDL is therefore unsafe while J21 is live.
  4. The UFS uses 4096-byte logical blocks. Radxa ships a separate _4096 image, so partitions must be 4K-native.
  5. By default the UEFI firmware supplies the DTB, so overlays can be silently bypassed.
  6. In the model, a T7 in direct sun exceeds its 60 C case limit.
  7. A USB 3 cable run to an outside T7 can fall back to 480M, which cannot carry Lime at 224 MB/s.
  8. Padding the UFS to the mid-plate only helps if the plate is cooler than the UFS. With Lime, it may not be.
  
  New options:
  - ufs-hwmon exposes the UFS device's own temperature and its crit/lcrit bounds. This can settle the unverified 0-70 C range.
  - smartctl -d sntasmedia reads the T7 temperature.
  - The Armor 7056A top cover alone plus a 40 mm fan is an in-stock cooler. The AliExpress Cu block has supply gaps.
  
  Still open (blocked or WebSearch budget exhausted): the October T7 and endurance microSD prices, the Cu block price, the Pelican EU price, real airflow, and the firmware-side NPU thermal limits.
- **Confirmed:**
  - Radxa UFS 3.1 128 GB RA022-B10J0U2 prices and stock (18 Oct 2026):
  - ALLNET: $65.90, in stock. Its 64 GB ($19), 256 GB ($75.90) and 512 GB ($89.90) are out of stock.
  - TinyTronics: EUR 58.00 incl. VAT (EUR 47.93 ex), 'Not in stock, 2-4 Weeks'.
  - Arace: all out of stock (128G at $49).
  - Radxa Q6A UFS doc (dd figures): Samsung KLUDG4UHDC-B0E1 128 GB reads 1703 MB/s and writes 388 MB/s; Kioxia THGJFGT1E45BAILB 256 GB reads 1811 and writes 557. The doc gives no temperature or WriteBooster data.
  - UFS module brief rev 1.2 (2026-01-13):
  - 'Up to 2100MB/s read and 1800MB/s write with WriteBooster'; it says ROCK 4D reaches about 1000/250.
  - Capacities 64 GB to 1 TB; optional industrial grade -25 to +85 C.
  - Connector 2 (34-pin) is mechanical only.
  - Radxa provision_ufs31.xml sets a shared 4 GiB WriteBooster buffer (shared_wb_buffer_size_in_kb=4194304, PreserveUserSpace=1). LU1-LU7 add 14.08 GiB (computed). Critical Link's wiki gives the same 4 GB default and the sysfs size formula.
  - PR #551 (Kioxia PA_TACTIVATE quirk) was merged on 11 May 2026 into radxa:linux-6.18.2 (merge 559f4f9). radxa-pkg/linux-qcom releases: last 6.18.2 is 6.18.2-4 (30 Mar); latest is 7.0.11-7 (17 Sep). Radxa staff on 18 May: 'linux-image 6.18 has not released a new version. We will update to linux-image 7.0'. The quirk is in the linux-6.18.2 (line 1044) and linux-7.0.11 (line 1100) branches, and not in mainline master.
  - Mainline ufs_quirks.h: UFS_VENDOR_SAMSUNG 0x1CE, UFS_VENDOR_TOSHIBA 0x198 (Kioxia).
  - Q6A DTS (radxa linux-6.18.2) thermal zones:
  - ufs-thermal: ADC_TM ch3, PM7325 GPIO1, 100k pull-up, ratiometric NTC.
  - msm-skin-thermal: ch2. quiet-thermal: ch1. xo-thermal: ch0.
  - None has trips.
  - sc7280.dtsi trip points:
  - CPU: passive 90 and 95 C with cpufreq cooling maps per cluster; critical 110 C.
  - GPU: passive 95/100/105 C; critical 110 C.
  - NSP, video, aoss and cpuss: 'hot' 90 C with no cooling maps; critical 110 C.
  - Mainline kodiak.dtsi has the same values.
  - Q6A DTS: the QMP USB/DP PHY sends lanes 0-1 to the RA620 HDMI bridge and lanes 2-3 to the USB-A port, so they share one PHY. The microSD vqmmc supply (l6c) is 1.65-3.544 V, which allows UHS-I 1.8 V signalling.
  - Q6A 2D drawing V1.21 (dated 2025-09-12/15): board 85.0x56.0 mm; 4x dia 3.5 mm holes on a 58.0x49.0 mm pattern, 3.5 mm from the edges (community: M2.5 hardware). The UFS B2B connectors and the +/-/TS pogo pads are on the underside. Every hardware file on the download page is still V1.21.
  - Product brief rev 1.5 (2026-04-28): 'board layout or component locations may change over time'. It recommends at least 18 W (12 V/1.5 A), or 24 W with USB 3.1 and PCIe loaded.
  - Radxa quick-start: 'Boot priority: USB > microSD > NVMe SSD > eMMC Module > UFS Module'. The boot page's R137 removal plus 10 kOhm at R207 'will no longer be able to boot ... from a microSD card, eMMC module, or NVMe SSD'. Installing to UFS needs no hardware mod (boot microSD, then dd the image).
  - EDL doc: hold EDL, apply a 12 V PD Type-C adapter, release, connect an A-A cable to the USB 3.1 Type-A port; the device shows as 05c6:9008. Powering via the 12 V header is not mentioned.
  - Radxa staff (strongtz, 15 Oct 2026): the 12 V header handles 4.5-16 V. willy: the 12 V pin is 1.5 mm from USB-C ground and prone to shorts. PMIC is in fake-battery mode; R24 is NC; VPH_PWR must stay at or below 4.5 V; no charging; do not connect Type-C and a battery together.
  - Forum results on cooling and recovery:
  - Bare board throttles at about 90-91 C at 7.8 W.
  - 40x40 heatsink on one shared pad is interface-limited (heatsink about 53 C).
  - Powerful fan: no more than 79 C.
  - Stepped Cu cooler: about 55 C under stress; paste on the SoC step, pad on the RAM step; standoff order matters.
  - Armor alone throttles at 35-40 C ambient; a 5 V fan fixes it.
  - UFS is the only sensor above 60 C in jvvv's Armor+fans build.
  - EDL works on a board that will not cold-boot (31450) but did not enumerate on another (31509).
  - SPI BIOS: 260120 is the documented release. The R1+ images need BIOS 20251230 or newer.
  - Test build dragon-q6a_flat_build_wp_260916.zip: 10,732,405 B, Last-Modified 13 Oct 2026, posted 14 Oct. It fixes the systemd-stub UKI silent reboot (reproduced 11 Jun, fixed in code 21 Jul).
  - DDR failures after SPI updates: RCW_TRAINING_FAIL ended in RMA (30841); ONLY_RANK_1 got 'erase-part cdt' then after-sales (31080).
  - Mainline vs Radxa DTB (HoShiMin, 30440): NVMe 27-28 MB/s with the mainline DTB against 584/681 MiB/s with Radxa's. The cause is missing commit 56bb627 ('Enable USB 3.0 and HDMI ports').
  - Geerling sbc-reviews #85, 8 GB board: 2.9 W idle at the wall; 9.3/9.5/10.1 W under stress-ng/Geekbench/HPL. microSD (Samsung Pro+ 32 GB): 73.70 MB/s read and 61.45 MB/s write (1M sequential), 2.32 MB/s 1M random write, 8.91/0.80 MB/s 4K read/write.
  - SmartHomeCircle: USB 3 write about 395 MB/s (fio, unnamed USB3-NVMe adapter, uas, 5000M). The bare board shut down at about 105 C in vkmark.
  - Intel USB 3.0 RFI paper: with an HDD connected, the 2.4 GHz noise floor rose 'by nearly 20 dB'.
  - Samsung T7 datasheet Rev 2.0: 0-60 C operating (Tc at the hottest case point; airflow recommended), -40 to 85 C non-operating, 85x57x8 mm, 72 g, USB 3.2 Gen 2. T7 Resurrected (MU-PD1T0G etc.) has the same specs and ships with a C-to-C cable only.
  - Samsung T7 prices: PCWorld (8 Jun 2026) reported a $190 Amazon deal against a $275 street price. ssd-tester, T7 1 TB: about 42 GB pSLC cache and 614 MB/s average over 100 GB.
  - LimeSDR Micro M.2 (Crowd Supply, 18 Oct): Basic $249, GNSS $299, worldwide shipping $18; 'Orders placed now ship Dec 15, 2026'.
  - Board 22x80 mm, top-side height about 4 mm, TMP1075 sensor, PCIe Gen3 x1, up to 160 Msps half-duplex.
  - MyriadRF docs: design cooling for at least 10 W.
  - MyriadRF (Zack, 24 Aug 2026): about 4 W typical; 2.5 A at 3.3 V is the PCIe spec limit, not consumption.
  - Wisecoco 7in page: operating '-20~70', storage '-30~80'; '2000+ cd/m2 (Typ.)'; outline 164.22x97.98 mm; the detail table lists the touch interface as I2C.
  - Polymaker PolyLite ASA TDS: Tg 98 C, Vicat 105 C, HDT 100 C (1.8 MPa) and 103 C (0.45 MPa); enclosure needed. Prusa: 'up to 93 C'; significant warping; ventilate. Shop: Grey 1 kg $26.99, White 1 kg $25.99, both in stock. CNC Kitchen M3x5.7 100 pcs EUR 9.40, in stock.
  - Adafruit 6101: 5 V 0.2 A, 40x40x10.6 mm, 32x32 mm hole pattern (dia 3.3 mm), USB lead about 1 m, $4.95, in stock; no airflow spec. Adafruit 5212 reader $6.95, in stock. Adafruit 6324 C-to-A 2 m cable $2.95, 93 in stock. ALLNET 64 GB microSD (ALN-TFUHS1-64) $16.99, in stock, 42 MB/s write / 80.6 MB/s read.
  - Armor 7056A (AE036):
  - ALLNET $9.90 and Arace $4.99, both in stock.
  - Radxa page: Mg-Si aluminium, fanless, contents are top cover, bottom cover, 2 thermal pads and 4 screws CM2.5x8x4; no thermal data.
  - ALLNET: top cover 70x56x15 mm, bottom cover 85x56x15 mm.
  - Olimex GX12-4: 5 A, -50 to +70 C, zinc nickel-plated, no IP rating, EUR 1.55, out of stock.
  - Molicel INR-21700-P50B TDS (third-party hosted copy):
  - 5000 mAh / 18.0 Wh typical (so 4S1P = 72 Wh).
  - Max dia 21.55 mm, max height 70.15 mm, max weight 71 g.
  - Charge -20 to 60 C, discharge -40 to 60 C, 60 A continuous.
  - IATA passenger lithium battery guidance: batteries must meet UN Manual of Tests and Criteria Part III 38.3. Spare batteries and power banks are carry-on only with terminals protected. Batteries of 100 Wh or less inside equipment may be checked.
  - Arithmetic re-run (Python, all match the stack):
  - 128e9 B = 119.2 GiB.
  - 2xV4L cu8 + HF+ ci16 = 13.31 MB/s = 47.9 GB/h, so the 30 GiB cap lasts 40.3 min.
  - 1.5 GiB ring lasts 98.3 s (121 s if ci16).
  - 15-minute HRPT pass = 4.61 GB.
  - Lime 224 MB/s = 74.4 min/TB; 4 GiB ring = 19.2 s; Burst 7 GiB with a 395 MB/s drain = 30.7 s.
  - /data records after quotas: 46.6 GiB.
  - D15 case: surface 0.1026 m2 (+10.8%), front 0.0306 m2 (+7.9%), passive about 1.03 W/K at h=10.
  - Air rise at 5.4 m3/h: 9.8 / 12.7 / 17.3 / 20.7 / 30.5 K for 17 / 22 / 30 / 36 / 53 W.
  - SatDump #766 (closed 8 Aug 2024): 8-10 GB baseband per pass; 10-15 passes filled 128 GB. Fixes: record off (live only), IQ decimation, cs8/ZIQ formats.
  - Pelican 1450 (retailer, IP67): interior 37.2x26x15.5 cm = 15.0 L (0.53 ft3); 2.9 kg with foam, 2.5 kg empty.
- **Corrections:**
  1.
    - **Claim in stack:** Section 2.11 / C1: LimeSDR optional, v1 built without Lime; T7 1 TB optional ('лише з Lime')
    - **Finding:** The governing user_requirements.md (18 Oct 2026, the user's own decision) overrides C1. 'LimeSDR Micro M.2: KEPT ... The build default becomes the with-Lime configuration (T7 1 TB, Lime parts, third HMC7992, CPU7 isolation, 4 GiB ring + 3 GiB burst, J21 desolder only after the soak test, case top band reprint)'. Stages 1 and 2 still treated the Lime, the T7 and the 11-port top edge as optional.
    - **Verdict:** corrected
    - **Action:** Make these the baseline mechanical, thermal and storage design: the T7 1 TB (outside), the Lime pedestal and riser cut-outs, the 11-port top edge, and thermal modes H and I. Move the T7 out of 'optional' in the BOM. The microSD endurance card becomes optional overflow only.
    - **Impact:** Raises the default BOM by the Lime set (about $596-681 per the stack). Makes the port-crowding, T7-sun and USB3-cable risks default-case risks.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md
  2.
    - **Claim in stack:** J21 = '12V header' fed regulated 12 V; after the soak test J21 is desoldered and fed by a 20 AWG twisted pair from the pads
    - **Finding:** Schematic V1.21, page 28: J21 is CON_1X3 with pin 1 = ADP12V_IN, pin 2 = GND, pin 3 = PWR_ON_KEY. The stack itself uses J21 pin 3 for the Pico power-on pulse and the case button (C3/D3 rows). The ADP12V input caps are 22 uF 16 V (C611/C612) and the buck is an SY81012VDC. This matches Radxa's '4.5-16 V'.
    - **Verdict:** new_risk
    - **Action:** After the desolder, wire all three pads:
  - 12 V and GND as a 20 AWG twisted pair.
  - PWR_ON_KEY as a separate 26-28 AWG wire to the Pico open-drain / BAT54 OR node.
  - Put a 3-pin latching connector in the harness so J21 can be unplugged at the hatch.
  Sleeve every joint, put polyimide tape over the USB-C shell, and strain-relieve the harness to the mid-plate. Never exceed 16 V; the stack's 12.0 V SYS12 is fine.
    - **Impact:** Without the pin-3 wire, power-on by the Pico or the case button stops working after the Lime desolder.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://forum.radxa.com/t/31611
      - https://forum.radxa.com/t/26723
  3.
    - **Claim in stack:** Stage 2: if EDL fails on J21 power, expose the Q6A USB-C in the hatch for a PD adapter
    - **Finding:** Schematic page 28 (my reading; a model until measured):
  - The USB-C VBUS reaches ADP12V_IN through Q5, a DMP2160UFDB dual PMOS wired back-to-back.
  - Q5's gates are pulled low by NPN Q6, whose base is a 100k/100k divider from TYPEC_IN. The CH224D GATE pin is NC.
  - So any VBUS presence turns Q5 on and ties USB-C VBUS directly to the J21 12 V rail. With nothing plugged into USB-C, Q5 is off and there is no back-feed.
  - If a PD adapter is plugged in while J21 is wired, the adapter back-feeds SYS12 (display, AUX, D36V50F12 output). If J21 is live, SYS12 back-feeds the adapter.
    - **Verdict:** new_risk
    - **Action:** Prefer EDL with J21 power (bench test). If a USB-C opening is ever added, unplug the J21 harness connector before using it, and label the hatch 'J21 unplugged before USB-C'. Never have USB-C and J21 connected at the same time.
    - **Impact:** Prevents back-feeding a charger or the display rail during field recovery.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://docs.radxa.com/en/dragon/q6a/low-level-dev/edl-mode
  4.
    - **Claim in stack:** C18 / 5.5: UFS A/B layout ESP 1 + root A 22 + root B 22 + /data about 74 GiB
    - **Finding:** The UFS is 4K-native. Radxa ships a separate UFS image, radxa-dragon-q6a_noble_gnome_r2.output_4096.img.xz (the microSD/NVMe image is _512). The provisioning XML uses bLogicalBlockSize=0x0c (4096 B). The partition sizes themselves still fit (128e9 B = 119.2 GiB).
    - **Verdict:** new_risk
    - **Action:** Build the field image for 4096-byte sectors, or partition on the device with sgdisk. ESP: 1 GiB FAT32 made with mkfs.vfat -S 4096. Make /data 'rest of device'. Never dd a _512 image to UFS. The rescue microSD uses the _512 image.
    - **Impact:** Prevents an unbootable UFS or misaligned GPT.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/download
      - https://docs.radxa.com/en/dragon/q6a/getting-started/install-system/ufs-system/no-ufs-reader
      - https://dl.radxa.com/q6a/images/android/provision_ufs31.xml
  5.
    - **Claim in stack:** Field DT overlay disables pcie0; lab overlay adds PPS (stage 2: build overlays on the Radxa DTB)
    - **Finding:** Radxa staff (strongtz, 30440): 'let the UEFI firmware provide the DTB for the kernel (which is the default behavior anyway)'. So unless the boot entry loads a DTB explicitly, the running tree comes from the SPI firmware (260120), not from the 6.18.2-4 package. Users in 31304 did swap package DTBs, so this depends on the bootloader configuration.
    - **Verdict:** new_risk
    - **Action:** In the systemd-boot BLS entries, set 'devicetree /dtbs/6.18.2-4-qcom/qcom/qcs6490-radxa-dragon-q6a.dtb' and 'devicetree-overlay' lines for the field and lab overlays. At bring-up, check that sha256(/sys/firmware/fdt) matches the package DTB plus overlays, and that /proc/device-tree shows pcie0 disabled in the field profile. Run an fio smoke test after any DT change.
    - **Impact:** Prevents overlays (pcie0 off, PPS) being silently ignored, and a silent storage slowdown.
    - **Sources:**
      - https://forum.radxa.com/t/30440
      - https://forum.radxa.com/t/31304
  6.
    - **Claim in stack:** 5.6: 'SoC Tj max 95 C; throttling about 90-91 C'
    - **Finding:** sc7280.dtsi: the CPU throttles at 90 C with a second step at 95 C; GPU from 95/100/105 C; critical shutdown 110 C on all zones. NSP and DDR have only a 'hot' 90 C trip with no cooling maps, so the kernel does not throttle the NPU. Whether the CDSP firmware has its own limits is unknown. One review saw a shutdown at about 105 C (bare board, vkmark).
    - **Verdict:** corrected
    - **Action:** Rewrite as: 'CPU throttles at 90/95 C, GPU from 95 C, critical 110 C. labd stops NPU/HTP jobs when nspss0/1 exceeds 85 C. Training only when the SoC is below 75 C. Derating ladder at 80/85 C.'
    - **Impact:** Closes the gap where the NPU had no limit.
    - **Sources:**
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/arch/arm64/boot/dts/qcom/sc7280.dtsi
      - https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5
  7.
    - **Claim in stack:** Cooling: 'Radxa Armor 7056A OR stepped Cu block (32x31 mm zone) + Adafruit 6101' (stage 1: Cu block primary, Armor bench-only; stage 1 said the two shells add about 30 mm)
    - **Finding:** Armor 7056A covers per ALLNET: top 70x56x15 mm, bottom 85x56x15 mm. The '+30 mm' was never derived from a drawing, and the real increment depends on the STEP; that number is refuted. The bottom shell does block the plate path and the UFS pad, which stands.
  
  The AliExpress stepped Cu cooler (item 1005010333340740) had stock gaps: 'no longer available' (Jan and May 2026), 'only one link left and the price is stupid'. Its price is unverified.
  
  The Armor top cover is in stock ($4.99-9.90). Rahul007: Armor plus a glued 5 V fan removed throttling at 35-40 C ambient.
    - **Verdict:** new_option
    - **Action:** Cooler, in order of preference:
  - (A) Stepped Cu cooler: paste or PTM7950-class material on the SoC step, a 0.5-1 mm pad on the LPDDR5 step, footprint 35x35 mm or less, under a 40 mm fan.
  - (B) In-stock fallback: the Armor 7056A top cover only, bottom shell discarded. Screw it through the dia 3.5 mm holes into M2.5 standoffs on the mid-plate, with a 40 mm fan ducted onto the fins.
  - Run a fit check in STEP V1.21 before choosing.
  - Never use one pad over both chips.
    - **Impact:** Removes the single-source AliExpress dependency. Cost $4.99-9.90 for the cover.
    - **Sources:**
      - https://shop.allnetchina.cn/products/radxa-heatsink-7056a
      - https://arace.tech/products/radxa-armor-case-7056a
      - https://radxa.com/products/accessories/armor-case-7056a/
      - https://forum.radxa.com/t/best-heatsink-cooling-solutions-for-dragon-q6a/30123
      - https://forum.radxa.com/t/recommended-heatsink-fan-for-q6a/30413
      - https://forum.radxa.com/t/30737
  8.
    - **Claim in stack:** Fan Adafruit 6101; stage 1: Noctua NF-A4x10 5V '0.22 W typical, 0-4500 rpm'
    - **Finding:** QuietPC listing (18 Oct) for the NF-A4x10 5V:
  - 4500 rpm +/-10% fixed (lower with the L.N.A.); the '0-4500 rpm' range belongs to the PWM model.
  - 4.8 CFM (8.2 m3/h), 1.78 mmH2O, 17.9 dB(A).
  - Max 0.25 W / 0.05 A; 5 V only; 3-pin with tach; SSO2 bearing; MTBF over 150k h.
  - Includes the L.N.A. and a 3-to-2-pin adaptor. GBP 13.96, 6 in stock.
  Adafruit 6101: 5 V 0.2 A (about 1 W), no airflow, pressure or rpm data.
    - **Verdict:** corrected
    - **Action:** Specify the NF-A4x10 5V (non-PWM) for path 1: DC on/off from the Pico via a MOSFET with a flyback diode. Wire the tach to a Pico GPIO for a stall alarm. Keep the 6101 only as a spare. Size the intake for no more than 5 Pa at the design flow.
    - **Impact:** About 0.75 W less fan power, a known fan curve and stall detection. About +$14 (GBP 13.96 at about 1.33 = about $18.6, a converted model price).
    - **Sources:**
      - https://www.quietpc.com/nf-a4x10-flx-5v
      - https://www.adafruit.com/product/6101
  9.
    - **Claim in stack:** UFS operating range 0-70 C; 'UFS and T7 rated from 0 C'
    - **Finding:** Still no datasheet for KLUDG4UHDC-B0E1. However, mainline ufs-hwmon (probed from ufshcd when the device supports temperature notification) exposes temp1_input (QUERY_ATTR_IDN_CASE_ROUGH_TEMP), temp1_crit (HIGH_TEMP_BOUND) and temp1_lcrit (LOW_TEMP_BOUND). These are the device's own reported bounds.
    - **Verdict:** new_option
    - **Action:** At bring-up, read /sys/class/hwmon/hwmon*/name == 'ufs' and its temp1_crit/temp1_lcrit, and record them as the UFS limits. Pause raw writes to UFS at min(65 C on ufs-thermal, temp1_crit - 10 K). Keep 'no storage operation below 0 C' unless lcrit says otherwise.
    - **Impact:** Turns an unverified rating into a measured device value at no cost.
    - **Sources:**
      - https://raw.githubusercontent.com/torvalds/linux/master/drivers/ufs/core/ufs-hwmon.c
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/drivers/ufs/core/ufshcd.c
  10.
    - **Claim in stack:** Stage 1/2: 'UFS pressed by a 1-1.5 mm pad onto a raised boss on the Al mid-plate'
    - **Finding:** The direction is confirmed: the UFS is on the underside (2D drawing bottom view) and is retained only by B2B clicks. But the mid-plate also takes the D36V50F12, both TPS7A4701 and, by default now, the Lime pedestal (designed for at least 10 W). A pad only cools the UFS if the plate at the boss is cooler than the UFS. The +/-/TS pogo pads sit next to the UFS connectors.
    - **Verdict:** new_risk
    - **Action:** Put the boss at least 30 mm from the Lime pedestal and the regulators, or cut a thermal slot in the plate around the boss. Put 0.05-0.1 mm polyimide film under the whole board with one cut-out at the boss. Check in STEP that the boss misses the pogo pads. Accept the pad only if an A/B test (pad vs no pad) lowers ufs-thermal.
    - **Impact:** Avoids heating the UFS with Lime and regulator heat.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_2d_dimensions_v1.21.pdf
      - https://forum.radxa.com/t/30090
      - https://forum.radxa.com/t/31226
  11.
    - **Claim in stack:** T7 1 TB 'outside on the bottom edge', rated 0-60 C; price $229.99-274.99 (unverified)
    - **Finding:** The datasheet limit is 0-60 C Tc. My model gives about 2-3 W of T7 dissipation (an assumption; the datasheet gives no power).
  - Direct sun at 35 C: +20-36 K, so 55-71 C.
  - Shade: +8-16 K.
  Anything strapped flat to a sun-loaded case adds more. smartmontools drivedb lists the T7 (04e8:4001) and T7 Shield (04e8:61fb) as ASMedia ASM2362 bridges using '-d sntasmedia', so NVMe SMART temperature is readable. Price: only the June 2026 figures ($190 deal / $275 street); no October price obtained.
    - **Verdict:** new_risk
    - **Action:** Mount the T7 in a shaded holder on the lower rear with a 3-5 mm air gap and a reflective sun flap. Log 'smartctl -d sntasmedia -A' temperature every 30 s; labrx stops writing at 55 C. Budget $190-275 and re-price before ordering. The T7 Resurrected needs a separate C-to-A cable.
    - **Impact:** Avoids out-of-spec operation during Lime captures in sun.
    - **Sources:**
      - https://download.semiconductor.samsung.com/resources/data-sheet/Samsung_Portable_SSD_T7_Datasheet_Rev2.0.pdf
      - https://download.semiconductor.samsung.com/resources/data-sheet/Samsung_Portable_SSD_T7_Resurrected_Datasheet_Rev.1.0.pdf
      - https://raw.githubusercontent.com/smartmontools/smartmontools/master/smartmontools/drivedb.h
      - https://www.pcworld.com/article/3158933/samsung-fast-t7-portable-ssd-finally-drops-in-price-190-was-285.html
  12.
    - **Claim in stack:** Blue USB 3.1 port: T7 limit 395 MB/s = 1.76x Lime 224 MB/s; 'T7 cable exit' on the bottom edge
    - **Finding:** 395 MB/s is a single SmartHomeCircle fio write through an unnamed USB3-NVMe adapter (uas, 5000M). The T7 post-cache rate of about 480 MB/s is a model from ssd-tester. The internal blue USB-A port must reach an external T7. A panel-mount USB 3 coupler or a long cable can make the link drop to 480M (High-Speed), and 224 MB/s is then impossible.
    - **Verdict:** new_risk
    - **Action:** Use one continuous, shielded USB 3.x A-to-C cable of 0.5 m or less, with ferrites, through a strain-relief grommet; no couplers. Gate every Lime session on 'lsusb -t' showing 5000M and Driver=uas for the T7. Re-measure with fio on the real T7.
    - **Impact:** Protects Lime recording, which is now the default build.
    - **Sources:**
      - https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5
      - https://ssd-tester.com/samsung_portable_ssd_t7_1tb.html
      - https://www.usb.org/sites/default/files/327216.pdf
  13.
    - **Claim in stack:** Hold linux-image-6.18.2-4-qcom (stage 2: 7.0.11-4 breaks HDMI, which confirms the hold)
    - **Finding:** Radxa staff (chenchongbiao, 1 Sep 2026, thread 31288): kernel 7.0 needs 'clk_ignore_unused' in /etc/kernel/cmdline to stop AUX interrupt storms that break HDMI. So the HDMI breakage has a published workaround (not tested by us). Same thread: after an rsetup upgrade, booting back into 6.18.2-4 left 'no sound at all', so other packages changed too. 31304: the upgrade also moved embloader 0.6 to 0.7.
    - **Verdict:** corrected
    - **Action:** Keep 6.18.2-4 for v1, because the Samsung UFS is stable on it. Hold the whole set: linux-image-6.18.2-4-qcom, linux-image-radxa-dragon-q6a, linux-headers-radxa-dragon-q6a, embloader and the Radxa firmware packages. Never run full-upgrade or rsetup in the field. If 7.0.11 is ever needed (e.g. Kioxia), add clk_ignore_unused and re-run the A/B and boot tests.
    - **Impact:** Avoids a half-upgraded system that loses audio or display.
    - **Sources:**
      - https://forum.radxa.com/t/31288
      - https://forum.radxa.com/t/31304
      - https://github.com/radxa-pkg/linux-qcom/releases
  14.
    - **Claim in stack:** UFS WriteBooster about 4 GiB (stage 1: no source; stage 2: from Radxa provisioning)
    - **Finding:** Confirmed from provision_ufs31.xml (shared 4194304 KiB) and Critical Link (4 GB default, 300-1500 MiB/s write range on 256 GB). The Q6A DTS also caps the link at HS-G4 Rate-A ('Gear-4 Rate-B is unstable due to board and UFS module design limitations'). Factory Linux provisioning is undocumented.
    - **Verdict:** corrected
    - **Action:** Record it as '4 GiB in Radxa's Android provisioning; read the real value from sysfs (wb_shared_alloc_units x 512 x allocation_unit_size x segment_size)'. Measure the post-cache rate with a 16 GiB fio fill. Keep 388 MB/s as the in-cache planning figure.
    - **Impact:** No design change; worst-case need is 13.3 MB/s.
    - **Sources:**
      - https://dl.radxa.com/q6a/images/android/provision_ufs31.xml
      - https://git.criticallink.com/redmine/projects/mitysom_qc6490/wiki/UFS
      - https://raw.githubusercontent.com/radxa/kernel/linux-6.18.2/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
  15.
    - **Claim in stack:** Service hatch: UART console + blue USB-A EDL; stage 2: UEFI menu over UART unverified
    - **Finding:** In thread 30925 the 260120 UART log prints 'Press F2 to enter Setup, F5 to enter UEFI Shell, F12 to enter Boot menu'. So the prompt reaches the serial console; whether input over UART works is still untested. One user's board stalls at the boot menu after rupdate until Enter is pressed.
    - **Verdict:** new_risk
    - **Action:** The hatch exposes: UART (40-pin UART5, pins 8/10, plus GND), the EDL button (or a recessed button wired in parallel), the J21 harness connector and the blue USB-A. Bench-test F2/F12 over UART. If it fails, carry a USB keyboard in the service kit. Never run rupdate.
    - **Impact:** Field recovery without opening the case.
    - **Sources:**
      - https://forum.radxa.com/t/30925
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
  16.
    - **Claim in stack:** Top edge P1-P7 (+P8) at 20 mm pitch; with Lime also RX1, RX2, REF IN
    - **Finding:** Model re-run: 11 ports at 20 mm pitch = 200 mm centre span plus about 5 mm nut half-width at each end = 210 mm. The 220-225 mm outer edge, minus walls and corner radii, leaves about 0-5 mm. With Lime now the default, this is the baseline layout.
    - **Verdict:** new_risk
    - **Action:** Move RX2 and REF IN to the upper left side wall (20 mm pitch, above the battery compartment). Keep P1-P8 + RX1 on top at 20 mm. Check against the HF+ shield corner and the HMI column in CAD.
    - **Impact:** Avoids a forced reprint of the default case.
    - **Sources:** []
  17.
    - **Claim in stack:** Battery bay 46x25x150 mm 'in an insulated compartment' behind 3 mm closed-cell foam, reflective film and a 1 mm FR-4/mica barrier; battery+BMS+barrier 0.32 kg
    - **Finding:** P50B maximum dimensions give a 2x2 pack of 43.1x21.55x140.3 mm, so the margins in 46x25x150 are 2.9 / 3.45 / 9.7 mm. The foam, film and barrier (about 4 mm per side) cannot fit inside that envelope. The compartment's outer envelope is about 54x33x158 mm (model). The cells weigh 284 g (71 g max each).
    - **Verdict:** corrected
    - **Action:** In CAD, treat 46x25x150 as the bare pack envelope (nickel, Kapton and fishpaper inside it, the BMS in the 9.7 mm end gap or outside). Reserve about 54x33x158 mm for the insulated compartment. Weight row: 0.33-0.34 kg (model).
    - **Impact:** Prevents a layout clash in the 55-60 mm depth.
    - **Sources:**
      - https://www.fsaeonline.com/content/Molicel-TDS--INR-21700-P50B-80122.pdf
  18.
    - **Claim in stack:** Bench case: Pelican 1450 (14.5 L, about 8.8 L filled = 61%) or Apache 3800; $30-169 unverified
    - **Finding:** Pelican 1450: 15.0 L interior, 2.9 kg with foam, IP67; Glazer's (US) $169.95, in stock. Apache 3800: Harbor Freight $39.99, 'In-Store Only', US only, IP65. The user is in Europe, so the Apache is not a world option.
    - **Verdict:** corrected
    - **Action:** Bench case: Pelican 1450 with foam, $169.95 (US price, verified); fill 8.8/15.0 L = 59%. The EU price is unverified. Drop the Apache 3800 for this user, and drop the $30 low end.
    - **Impact:** The bench-case line becomes about $170 (low end up by about $130).
    - **Sources:**
      - https://www.wiltronics.com.au/product/67862/1450-pelican-protector-case-with-foam-filler/
      - https://www.glazerscamera.com/products/pelican-1450-black
      - https://www.harborfreight.com/3800-weatherproof-protective-case-large-black-63927.html
  19.
    - **Claim in stack:** Travel: IATA requires UN 38.3; Pelican may be checked
    - **Finding:** The IATA PDF content is confirmed, but the file is 'Revision 3 effective February 2019'. 2026 airline and ICAO changes for power banks were not verified, because the search budget was exhausted.
    - **Verdict:** corrected
    - **Action:** Keep the rule. Add: the checked Pelican carries no spare cells or power banks. Check the airline's current power-bank rules before each trip (Anker 737 is 86.4 Wh, carry-on).
    - **Impact:** None on the design.
    - **Sources:**
      - https://www.iata.org/contentassets/6fea26dd84d24b26a7a1fd5788561d6e/passenger-lithium-battery.pdf
  20.
    - **Claim in stack:** Rescue microSD outside the case; microSD only overflow/rescue
    - **Finding:** Confirmed (Gilles 31509: an A2 card developed bad sectors after 3-4 months, and a fresh card failed after its second boot). Stage 2 misattributed the 'Etcher flash -> no HDMI or network' result to Geerling. In #85, the rsetup failure (no video, no network) was francorbacho's. Geerling's Etcher run showed a verification error, fixed by pre-expanding the image.
    - **Verdict:** corrected
    - **Action:** Keep two rescue cards, flashed from an extracted .img with a hash check; f3-style write-verify on arrival. No OS or DB on SD.
    - **Impact:** Wording only.
    - **Sources:**
      - https://github.com/geerlingguy/sbc-reviews/issues/85
      - https://forum.radxa.com/t/31509
  21.
    - **Claim in stack:** V30 endurance microSD $25-82 (stage 1: Slickdeals tracker 5 Apr 2026 $81.99/$115.85/$153.99)
    - **Finding:** On 18 Oct 2026 the cited Slickdeals page shows only the expired 12 Aug 2024 $25 deal (list $48) and no tracker values. The RS page returned 403. So the stage-1 $82-154 range is not supported by its source.
    - **Verdict:** unverified
    - **Action:** With Lime now the default, the endurance card is optional overflow only. Keep it unpriced ('re-price at order'). Do not carry $82-154 as verified.
    - **Impact:** Optional tier only.
    - **Sources:**
      - https://slickdeals.net/f/17686464-25-256gb-samsung-pro-endurance-uhs-i-microsdxc-memory-card-w-sd-adapter-at-amazon
  22.
    - **Claim in stack:** IMU socket GX12; LAB BUS 6-pin; IPX4/IP54
    - **Finding:** GX12 still has no datasheet IP rating (Olimex). No specific IP67 M8 part was verified in this pass.
    - **Verdict:** unverified
    - **Action:** Specify a 4-pin A-coded M8 panel receptacle whose datasheet gives IP67 when mated or capped (part to be selected and priced). Or keep the GX12 with a tethered cap, and pass an IPX4 spray test with all caps fitted.
    - **Impact:** Keeps the IP claim honest.
    - **Sources:**
      - https://olimex.com/Products/Components/Connectors/CONNECTOR-GX12-4
- **New risks:**
  - The governing requirements make the Lime build the default. The T7 outside the case, the J21 desolder, the 11-port top edge and Lime heat on the mid-plate are now baseline risks, not optional ones.
  - J21 is 3-pin (ADP12V_IN, GND, PWR_ON_KEY). The desolder plan rewires only a twisted pair, which loses the Pico/case-button power-on.
  - Any USB-C VBUS turns on Q5 (back-to-back PMOS via Q6) and ties USB-C VBUS to the J21 12 V rail (schematic reading, a model). A PD adapter plugged in while J21 is wired back-feeds SYS12; if J21 is live, SYS12 back-feeds the adapter.
  - The UFS is 4K-native (_4096 image, bLogicalBlockSize 0x0c). A 512-sector image or GPT written to UFS will not boot.
  - By default the UEFI firmware supplies the DTB. Field and lab overlays can be silently bypassed unless the BLS entries load the DTB and overlays explicitly.
  - T7 in direct sun at 35 C: model case temperature 55-71 C, above the 60 C Tc limit.
  - An external USB 3 cable or coupler to the T7 can fall back to 480M, which cannot carry Lime at 224 MB/s.
  - The UFS pad-to-plate path can heat the UFS if the boss is near the Lime pedestal or the regulators.
  - The NPU (nspss) has no kernel throttle before the 110 C critical trip, and firmware CDSP limits are unknown. One review saw a shutdown at about 105 C.
  - Partial upgrades (kernel 7.0.11, embloader 0.7, firmware) caused HDMI or audio loss. Holding only linux-image is not enough.
  - The AliExpress stepped Cu cooler is effectively single-source, with stock gaps and an unverified price.
  - The battery compartment outer envelope (about 54x33x158 mm) is larger than the 46x25x150 pack envelope used in the plan.
- **Refuted findings:**
  1.
    - **Finding:** Stage 1: Noctua NF-A4x10 5V is '0.22 W typical, 0-4500 rpm'.
    - **Why:** The non-PWM 5 V model is fixed at 4500 rpm +/-10% (lower with the L.N.A.), 0.25 W / 0.05 A max (QuietPC listing). '0-4500 rpm' is the PWM variant. No source for '0.22 W typical' was found.
  2.
    - **Finding:** Stage 1: Slickdeals price tracker (updated 5 Apr 2026) shows Samsung PRO Endurance 256 GB at $81.99 Amazon / $115.85 Newegg / $153.99 Best Buy and Samsung.
    - **Why:** The cited page, fetched and grepped on 18 Oct 2026, shows only the expired Aug 2024 $25 deal and no tracker values. The claim is unsupported by its source.
  3.
    - **Finding:** Stage 2: 'Geerling: an Etcher flash produced a board with no HDMI or network' and 'rsetup on an r2 image left Geerling's board unbootable'.
    - **Why:** In sbc-reviews #85 the rsetup failure (no video, no network) was reported by francorbacho. Geerling's own Etcher flash gave a verification error, fixed by pre-expanding the image.
  4.
    - **Finding:** Stage 2: '7.0.11-4 breaks HDMI ... That confirms the hold is needed.'
    - **Why:** Radxa staff posted a fix on 1 Sep 2026: clk_ignore_unused in /etc/kernel/cmdline (thread 31288). The hold is still sensible for UFS stability and to avoid a mixed upgrade, but HDMI is not the reason.
  5.
    - **Finding:** Stage 1: the Armor 7056A 'two shells add roughly 30 mm of stack height'.
    - **Why:** Only the cover sizes are known (70x56x15 and 85x56x15 mm). The increment over standoffs plus a Cu block and fan depends on the STEP and was not derived. The qualitative mounting conflict stands; the number does not.
  6.
    - **Finding:** Stack D14 / stage 1: Apache 3800 as a world bench-case option ($30-50).
    - **Why:** Harbor Freight lists it at $39.99 'In-Store Only' (US stores). The user is in Europe, so it is not a world option.
  7.
    - **Finding:** Stack 5.6: 'Tj max 95 C; throttling about 90-91 C (verified, forum 30123)'.
    - **Why:** Thread 30123 states neither figure. The DT trips are CPU passive 90/95 C, GPU 95/100/105 C and critical 110 C, so 95 C is a throttle step, not Tj max.
- **Corrected spec:** MECH / THERMAL / STORAGE: corrected spec (18 Oct 2026; the with-Lime build is the default per user_requirements.md)
  
  COMPUTE MOUNT
  - Board: Radxa Dragon Q6A 12 GB, hardware files V1.21.
    - 85.0x56.0 mm; 4x dia 3.5 mm holes on 58.0x49.0 mm, 3.5 mm from the edges.
    - M2.5 standoffs to the 2 mm Al mid-plate.
    - Check the delivered board against the V1.21 STEP before printing.
  - Under the board: 0.05-0.1 mm polyimide film over the whole footprint, with one cut-out for the UFS boss. The boss must miss the +/-/TS pogo pads.
  - UFS cooling: a 1-1.5 mm pad onto a plate boss placed at least 30 mm from the Lime pedestal and the regulators, or isolated by a plate slot. Keep it only if the A/B test (pad vs no pad) lowers ufs-thermal.
  
  COOLER
  - (A) Stepped Cu cooler, footprint 35x35 mm or less: PTM7950-class material or paste on the SoC step, a 0.5-1 mm pad on the LPDDR5 step, short standoffs on the PCB side. Never one shared pad.
  - (B) In-stock fallback: Armor 7056A (AE036, Arace $4.99 / ALLNET $9.90), top cover only on M2.5 standoffs, bottom shell discarded. Fit-check first.
  - Fan, path 1: Noctua NF-A4x10 5V, non-PWM. 4500 rpm, 8.2 m3/h, 1.78 mmH2O, 17.9 dB(A), 0.25 W max. QuietPC GBP 13.96.
    - Powered from the 5 V rail, switched DC on/off by the Pico through a MOSFET with a flyback diode.
    - On at SoC 60 C, off at 50 C; 100% if the heartbeat is lost.
    - Tach wired to a Pico GPIO; stall alarm.
    - Adafruit 6101 ($4.95) as a spare only.
  - Path 2: blower over the display duct and plate fins; model not yet measured.
  - Intakes: stainless mesh plus hydrophobic foam sized for at most 5 Pa. ePTFE vents.
  
  THERMAL LIMITS
  - Kernel: CPU passive 90/95 C, GPU 95/100/105 C, critical 110 C.
  - labd:
    - Derating at 80/85 C SoC.
    - Training only when the SoC is below 75 C.
    - NPU/HTP stop when nspss0/1 exceeds 85 C.
    - Raw-to-UFS pause at min(65 C on ufs-thermal, ufs hwmon temp1_crit - 10 K).
    - T7 writes stop at 55 C (smartctl -d sntasmedia).
  - Log zones by type, never by index: ufs-thermal, msm-skin-thermal, quiet-thermal, xo-thermal, nspss0/1, cpu*, gpuss*, plus the ufs hwmon and the Lime TMP1075.
  
  THERMAL MODEL (D15 222.5x137.5x57.5 mm; a model)
  - Surface 0.103 m2; passive about 1.0 W/K at h=10.
  - Solar 14.6-18.4 W.
  - Exit rise at 5.4 m3/h: 9.8 / 12.7 / 17.3 / 20.7 / 30.5 K for 17 / 22 / 30 / 36 / 53 W.
  - Lime about 4 W typical in modes H/I; pedestal and pad designed for 10 W.
  - Forced air is mandatory.
  - Acceptance: 45 min at midday in modes B, D, G and H. Frame at most 60 C, glass at most 65 C, cells at most 45 C, no critical trip.
  
  POWER ENTRY (mechanical part)
  - J21 = 3 pins: 1 ADP12V_IN, 2 GND, 3 PWR_ON_KEY.
  - Fed 12.0 V SYS12; limit 4.5-16 V.
  - After the Lime soak-test desolder:
    - 20 AWG twisted pair for 12 V and GND, plus a 26-28 AWG wire for PWR_ON_KEY.
    - Through a 3-pin latching connector reachable at the hatch.
    - Heat-shrink on every joint, polyimide over the USB-C shell, strain relief to the plate.
    - 4 A fuse.
  - Q6A USB-C: no case opening. Never connect it while J21 is wired (Q5 back-feed).
  
  SERVICE HATCH
  - UART5 console (40-pin pins 8/10 plus GND), the EDL button (or a recessed parallel button), the J21 harness connector and the blue USB-A.
  - EDL: hold the button, apply J21 power (bench-verify), release; A-A cable; 05c6:9008.
  - UEFI keys over UART: F2 / F5 / F12 (bench-verify).
  - Never do the R137/R207 UFS-boot mod.
  
  STORAGE
  - Radxa UFS 3.1 128 GB RA022-B10J0U2 (Samsung KLUDG4UHDC-B0E1). ALLNET $65.90, in stock; TinyTronics EUR 58, 2-4 weeks.
    - On arrival, check the vendor ID is 0x01CE.
    - Link is HS-G4 Rate-A (DT limit).
    - 4096-byte logical blocks: use the _4096 image or partition on the device.
  - GPT on UFS: ESP 1 GiB FAT32 (mkfs.vfat -S 4096), root A 22 GiB, root B 22 GiB, /data = rest of device (about 74 GiB).
    - /data quotas: NPU dataset 20 GB, apt mirror 4 GiB, map tiles 4 GiB, models 0.3 GiB, logs 0.5 GiB (journald 200M). About 46.6 GiB is left for records.
    - Raw cap 30 GiB rolling (about 40 min at 13.3 MB/s); products kept, raw only when pinned.
  - WriteBooster: 4 GiB in Radxa provisioning; read the real value from sysfs. Planning write rate 388 MB/s in-cache; measure post-cache.
  - Never apply provision_ufs31.xml or the Android UFS image to the field module.
  - Kernel: hold linux-image-6.18.2-4-qcom and its meta-packages, embloader and the firmware packages. No full-upgrade, rsetup or rupdate in the field.
  - SPI BIOS: stay on 260120. The 260916 test build is not for the field; SPI updates on the bench only, with UART and the EDL kit ready.
  - Boot: systemd-boot with BLS entries (not UKI), boot counting, a rescue entry, and explicit 'devicetree' plus 'devicetree-overlay' lines. No ESP on any data medium; boot order is USB > SD > NVMe > eMMC > UFS.
  - T7 1 TB (default, Lime build), 85x57x8 mm, 72 g, 0-60 C Tc.
    - Budget $190-275; re-price before ordering.
    - Lower rear, shaded holder, 3-5 mm air gap, sun flap.
    - One continuous shielded USB 3 A-to-C cable of 0.5 m or less with ferrites, through a grommet. Gate on lsusb -t showing 5000M/uas.
    - Allocation: raw NPU 400 GB for 14 days, captures and bursts 300 GB, exFAT exchange 64 GiB, a snapshot copy.
    - Lime 56 Msps ci16 = 224 MB/s (74.4 min/TB). Ring 4 GiB (19.2 s); Burst +3 GiB (about 30.7 s at 160 Msps with a 395 MB/s drain).
    - The T7 never writes during L-band, S-band or GNSS sessions.
  - microSD: rescue kit is 2x ALLNET 64 GB ($16.99 each) + Adafruit 5212 ($6.95) + 6324 ($2.95) + an A-A cable; f3-type write-verify on arrival. A V30 endurance card for overflow is optional and unpriced. Sequential preallocated files only; no DB or journald on SD.
  - SatDump runs with record off; all raw IQ goes through labrx.
  
  CASE
  - Light-grey Polymaker ASA (1 kg Grey $26.99), printed enclosed and ventilated; heat limit 93 C (Prusa). CNC Kitchen M3x5.7 inserts EUR 9.40 per 100.
  - Outer plan 220-225 x 135-140 x 55-60 mm.
  - Battery compartment: outer envelope about 54x33x158 mm around the 46x25x150 pack (P50B 71 g max, cells 284 g).
  - Top edge: P1-P8 + RX1 at 20 mm pitch. Upper left side wall: RX2 + REF IN.
  - Bottom edge: IP2368 USB-C, capped LAB USB-A, latching 6-pin LAB BUS, 3.5 mm audio, T7 cable grommet.
  - Rear: 1/4-20 steel insert in a boss of at least 6 mm (pull test at 3x the device weight); strap lugs; IMU on an IP67 M8 4-pin connector (or a capped GX12 that passes the spray test); service hatch.
  - Target IPX4/IP54.
  
  KIT
  - Field: 15-20 L backpack (no change; prices are a model).
  - Bench: Pelican 1450 with foam, $169.95 (US), 15.0 L, 2.9 kg, about 59% filled.
  - Travel: the home-built 72 Wh pack never flies; no spare cells or power banks in checked bags.
- **Bench tests:**
  - UFS on arrival:
  - Vendor ID 0x01CE and model string from sysfs.
  - 'lsblk -o NAME,SIZE,LOG-SEC,PHY-SEC' shows 4096-byte sectors.
  - Record the LU layout (unit_descriptor).
  - WriteBooster size = wb_shared_alloc_units x 512 x allocation_unit_size x segment_size.
  - fio sequential write 16 GiB (bs=1M, direct=1); post-cache rate must be at least 50 MB/s.
  - ufs hwmon: find hwmon 'ufs' and read temp1_input, temp1_crit and temp1_lcrit. Set the UFS pause threshold and the cold rule from them. If the hwmon is absent, keep 65 C on ufs-thermal.
  - Thermal zones: list /sys/class/thermal/*/type and confirm ufs-thermal, msm-skin-thermal, quiet-thermal, xo-thermal and nspss0/1 are present. Log them by type in labpowerd.
  - Cooler fit and performance:
  - STEP V1.21 plus a physical paste-imprint check for both the Cu block and the Armor-top-only option.
  - stress-ng at about 10 W for 10 min with the inlet at a known temperature.
  - Pass: SoC-to-inlet of 3.5 K/W or less, no passive trip.
  - Airflow: measure path 1 and path 2 flow with a hot-wire anemometer at the exhaust, or from dT at a known heater power. Pass: at least 2.7 m3/h per path. Otherwise change the fan or intake area.
  - Midday soak, 45 min each in modes B, D, G and H (Lime), visor on, 35 C or measured ambient. Pass:
  - Frame at most 60 C, glass at most 65 C, cells at most 45 C.
  - UFS below its pause threshold; T7 SMART at most 55 C.
  - No critical trip; nspss below 85 C.
  - UFS pad A/B: ufs-thermal with and without the plate-boss pad, Lime loaded. Keep the pad only if it lowers the UFS temperature.
  - J21 and USB-C:
  - With J21 at 12 V and nothing on USB-C, VBUS on the USB-C pin must read under 0.5 V.
  - Never connect USB-C while J21 is wired.
  - Check that the power-on key on pin 3 still works after the desolder.
  - EDL powered only through J21 (USB-C empty) from a Linux host via the A-A cable: expect 05c6:9008. UEFI F2/F12 over the hatch UART at 115200.
  - DTB provenance: sha256 of /sys/firmware/fdt against the BLS-loaded DTB plus overlays. Field profile shows pcie0 status 'disabled'. fio smoke test on UFS and T7 after any DT change.
  - Boot safety: 20 cold boots with the T7 and the LAB USB stick attached, all must boot from UFS. 50 warm + 20 cold boots overall, with systemd-boot boot counting and a rollback test.
  - T7 link and endurance:
  - 'lsusb -t' shows 5000M and Driver=uas through the final cable.
  - fio rate-limited sequential write at 224 MB/s for 60 min, with 'smartctl -d sntasmedia -A' every 30 s, once in shade and once in sun with the flap.
  - Pass: zero I/O errors, no labrx drops, at most 55 C.
  - Kernel soak, 12 h: dmesg contains zero matches for 'ufshcd.*(error|timed-out)|OCS invalid|pa_err|dl_err'. 'apt-mark showhold' lists the kernel meta-packages, embloader and the firmware packages.
  - Weather: IPX4 spray test (IEC 60529 oscillating tube or hand-held spray, 10 min) with all caps fitted; then check the GX12 or M8 and the LAB BUS for water ingress.
  - Mechanical: pull test of the 1/4-20 insert at 3x the device weight; drop the strap-lug load; check the hatch latch.
  - Battery compartment: thermocouple on the middle cell during the midday soak; the 0-45 C charge window must hold. Check that the compartment's outer envelope matches CAD.
- **Confidence:** medium

