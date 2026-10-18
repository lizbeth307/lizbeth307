# Samsung t7 1 tb: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_32802e9c-2a4`_

- **Part:** Samsung Portable SSD T7 1 TB (raw-IQ capture drive, Q6A blue USB 3.1 Gen1 port, with-Lime default build)
- **Current pick:** Samsung T7 1 TB MU-PC1T0T/WW (grey) or MU-PC1T0H/WW (blue). Datasheet Rev 2.0: USB 3.2 Gen2, ASMedia ASM2362 bridge (04e8:4001, smartctl -d sntasmedia), 85x57x8 mm, 72 g, 0-60 C Tc, 2 m drop to metal, 1500 G/0.5 ms, 20-2000 Hz 20 G, AES-256, 3-year warranty, C-to-A and C-to-C cables in the box.
- **Current price usd:** STACK: $229.99-274.99 (US snippets). EU, fetched 18 Oct 2026: Alternate.de EUR 224.90 incl. VAT ($252.81), in stock. Reichelt EUR 205.90 incl. 19% VAT ($231.45), or EUR 173.03 ex VAT ($194.50), limited stock, shipping extra. FX 1.1241 USD/EUR.
- **Decision:** keep
- **Chosen:** KEEP the Samsung T7 1 TB, same SKU MU-PC1T0T/WW, bought new from Reichelt (EU seller). Fallbacks: blue MU-PC1T0H at Reichelt EUR 209.00, or Alternate EUR 224.90 (in stock). No other brand, used unit or DIY build is both cheaper and proven not worse.
- **Chosen price usd:** $231.45 incl. 19% DE VAT (EUR 205.90), or $194.50 ex VAT (EUR 173.03). Shipping extra. Reichelt shows 'limited stock'.
- **Saving usd:** $0 on the part itself, because it is the same SKU. Buying from Reichelt instead of Alternate (EUR 224.90) saves EUR 19.00, about $21.36. Against STACK's top figure of $274.99 it saves $43.54. Against STACK's low figure of $229.99 (a US price before import VAT and shipping) the cost is about equal (+$1.46).
- **Equivalence proof:** The chosen part is the same model, so it matches on every spec: MPN MU-PC1T0T/WW (the EU 'WW' box). Datasheet Rev 2.0, fetched and parsed: USB 3.2 Gen2 10 Gbps, up to 1050/1000 MB/s, 85x57x8 mm, 72 g, 2 m drop to a metal plate, 0-60 C operating (footnote 6: Tc at the hottest case point), -40 to 85 C non-operating, 1500 G / 0.5 ms shock, 20-2000 Hz 20 G vibration, 3-year limited warranty, C-to-A and C-to-C cables included.
  
  Stack fit is unchanged:
  - smartmontools drivedb lists 'USB: Samsung Portable SSD T7; ASMedia ASM2362' 0x04e8:0x4001 with -d sntasmedia, so the labd 55 C write-stop rule keeps working.
  - Uses the in-kernel uas driver, with no vendor driver.
  - The holder, grommet and 0.5 m A-to-C cable stay the same.
  
  Measured (ssd-tester): about 42 GB pSLC cache, and a 100 GB file averaged 614 MB/s. That implies roughly 480 MB/s after the cache (my inference). This is above the Q6A port ceiling of about 395 MB/s and the 224 MB/s Lime stream.
  
  Seller: Reichelt is an established German distributor selling new retail stock. That gives the Samsung warranty (which goes to 'the purchaser of the Product in its original sealed packaging') plus 2-year EU statutory seller liability and the 14-day distance-selling withdrawal window for the acceptance tests.
  
  Price checks: geizhals, idealo, Amazon.de, Mindfactory, Galaxus, Proshop, Conrad and computeruniverse were blocked (403, 503 or captcha). So no cheaper authorized EU new offer could be verified, but none can be ruled out either. Re-check at the 1 Dec 2026 gate.
- **Rejected:**
  1.
    - **Name:** Kioxia EXCERIA PLUS G2 Portable 1 TB LXD20K001TG8, Reichelt EUR 154.95 ($174.18)
    - **Why:** Proven worse in its own product brief (v1.0, fetched): drop rating 122 cm (MIL-STD-810H 516.8 IV, 26 drops) against the T7's 2 m; vibration rating 3.10 Grms at 2-500 Hz against 20 G at 20-2000 Hz; operating 0-45 C Ta (not directly comparable with 60 C Tc, so unproven). 'Up to 3-year' warranty. Linux is not in its OS list. Post-cache write is not published and I found no measurement (the ssd-tester page has no data). The G2 USB ID and SMART path are not in drivedb (the G1 was JMicron 0x30de:0x1000 -d sntjmicron), so the 55 C SMART stop rule is unverified. 72x40x11.8 mm needs a new holder. The EUR 51 saving does not offset a lower drop rating.
  2.
    - **Name:** SanDisk Extreme Portable SSD V2 1 TB SDSSDE61-1T00-G25, Reichelt EUR 187.00 ($210.21)
    - **Why:** Rated 0-45 C operating (SanDisk support pages and product brief) against 0-60 C. Body is 100.5x52.4x8.95 mm (LDLC listing), 15 mm longer than the T7, so it does not fit the 85 mm shaded holder. Reliability: the 2023 disconnect and data-loss episode led to a firmware recall. WD's official list covered the 4 TB V2 and the Extreme Pro 1/2/4 TB, not the 1 TB V2, but Ars staff reported data loss on 2 TB V2 units and a class action followed. So 'same or better reliability' is not shown. Some points are equal or better: drop 2 m (retailers), IP55/65, 5-year warranty, ASM2362 bridge with -d sntasmedia (drivedb 0x0781:0x55ae), and a post-cache rate of about 540 MB/s inferred from 551 MB/s average over 100 GB with a 5 GB cache. Saves only EUR 18.90.
  3.
    - **Name:** Kingston XS2000 1 TB SXS2000/1000G, Reichelt EUR 179.50 ($201.78)
    - **Why:** Datasheet (fetched): operating 0-40 C against 0-60 C. Only a 12-inch C-to-C cable is included, so a C-to-A cable is needed. No drop or shock figure (only 'internal controlled drop procedures'). Metal and plastic case. Not in smartmontools drivedb, so the SMART temperature path for the 55 C rule is unverified. Post-cache write unmeasured (the ssd-tester run stayed inside the 97 GB cache).
  4.
    - **Name:** Lexar SL500 1 TB (LSL500X001T)
    - **Why:** Official spec 0-50 C operating against 0-60 C. Also Gen2x2 (falls back to Gen1 on the Q6A), post-cache unmeasured, SMART path unverified. EU price not verified (digitec 503).
  5.
    - **Name:** SanDisk Portable SSD 1 TB SDSSDE30-1T00-G26, Reichelt EUR 164.50 ($184.91)
    - **Why:** SATA-class drive (drivedb uses -d sat for this family): read 520 MB/s against 1050 MB/s, which halves PC offload speed. Write and post-cache not specified, NAND type unknown, no drop or temperature data checked.
  6.
    - **Name:** Verbatim Store 'n' Go Portable SSD 1 TB (53230), Reichelt EUR 178.50 ($200.65)
    - **Why:** The listing gives USB 3.0 (5 Gbps) and no read, write, temperature or drop figures. Offload is capped, and nothing can be shown to be not worse.
  7.
    - **Name:** Crucial X9 1 TB CT1000X9SSD9, Reichelt EUR 199.90 ($224.71)
    - **Why:** QLC with a measured post-cache cliff: 210 MB/s average over 300 GB with a 256 GB cache, so about 40 MB/s once the cache is full (ssd-tester, per search A). That fails the 224 MB/s floor. Also Crucial consumer is end-of-line.
  8.
    - **Name:** Crucial X9 Pro 1 TB CT1000X9PROSSD9
    - **Why:** Measures better on sustained write, but Micron exited the Crucial consumer business (announced 3 Dec 2025, consumer-channel shipments ended Feb 2026; StorageReview, Evertiq). No verified current new EU offer below EUR 205.90 (EUR 116-139 listings are undated or stale; Galaxus 503). Operating temperature not found. In practice warranty claims reportedly get refunds rather than replacements (anecdotal, Aug 2026). Leftover or grey stock, so provenance is not equal.
  9.
    - **Name:** Kingston XS1000 1 TB
    - **Why:** Post-cache write about 176 MB/s, inferred from the 2 TB measurement, which is below the 224 MB/s stream. Operating 0-40 C. EU price not checked.
  10.
    - **Name:** Samsung T7 Resurrected 1 TB MU-PD1T0G/WW
    - **Why:** Same datasheet values, but no verified price below EUR 205.90 (Euronics EUR 274.99; Coolblue EUR 243.90 from a snippet; MediaMarkt BE EUR 199 unverified, page 403). Ships with C-to-C only, so it needs an extra C-to-A cable.
  11.
    - **Name:** Used Samsung T7 1 TB, private sale on Kleinanzeigen, EUR 120-175 ($134.89-196.72)
    - **Why:** Same hardware, but the Samsung warranty statement (fetched) says the warranty goes to 'the purchaser of the Product in its original sealed packaging' and 'is provided only to You and is not transferable'. Private sellers exclude statutory liability. Wear, heat and drop history are unknown, and fake-capacity or relabel risk is higher. Warranty and provenance are traded away, so it is not not-worse. It can be offered to the user only as an explicit trade.
  12.
    - **Name:** Sealed Samsung T7 1 TB, private sale, EUR 165-190 ($185.48-213.58)
    - **Why:** Same hardware, but there is no seller statutory liability, and Samsung warranty coverage for a second buyer is doubtful: the warranty is non-transferable, and without a valid proof of purchase the period runs from the manufacture date. There is also re-seal or fake risk, and one listing has a colour mismatch ('schwarz'). The EUR 15-40 saving is a warranty and provenance trade, not an equal part.
  13.
    - **Name:** Samsung T7 Shield 1 TB, private sale EUR 160 ($179.86); retail Reichelt EUR 249
    - **Why:** Better on performance (about 879 MB/s average over 200 GB) and IP65, with the same ASM2362 bridge and -d sntasmedia (drivedb 0x04e8:0x61fb). But it is about 88x59x13 mm and about 98 g (needs holder rework). The private unit has no transferable warranty, and its single listing is six weeks old. At retail it costs EUR 43 more. Kept as the fallback if the T7 fails acceptance, not as a cheaper analog.
  14.
    - **Name:** Samsung T9 1 TB MU-PG1T0B, Reichelt EUR 222.00
    - **Why:** Not cheaper (+EUR 16.10). 88x59x13 mm and 122 g, and Gen2x2 bridge power is likely higher (unverified).
  15.
    - **Name:** DIY: WD SN770 / SN7100 / SN770M in an ASUS Arion or UGREEN CM400 enclosure
    - **Why:** Per search B (not re-verified here): saves only $14-37 or costs more. No drop or shock rating, and the lid is user-openable. No measured fill test through a USB bridge, no measured bus power, larger size. RTL9210-class bridges carry a documented UAS-abort risk on Linux (LKML, Mar 2025). Bare drives come from private sellers, so warranty is unclear.
- **Confidence:** high
- **Conditions or tests:** Run the acceptance tests on the Reichelt T7 within the 14-day withdrawal window:
  1. Confirm genuine stock. The label MPN reads MU-PC1T0T/WW; lsusb shows 04e8:4001; Samsung Magician (on a PC) recognises the drive and its firmware.
  2. Check the link. lsusb -t shows Driver=uas at 5000M on the Q6A blue port with the final 0.5 m or shorter A-to-C cable and grommet.
  3. Check SMART. smartctl -d sntasmedia -a returns the temperature, Critical Warning 0 and Media Errors 0.
  4. Run a full-capacity anti-fake write and verify: fio with verify=crc32c, or f3.
  5. Run fio --rw=write --bs=1M --direct=1 --size=300G on the Q6A, logged every second, at ambient up to 35 C in the shaded holder. Pass: a floor of 250 MB/s or more, the 60-min 224 MB/s test held at 55 C SMART or less, and no uas resets or xHCI errors in dmesg. StorageReview saw a T7 Touch reach only about 240 MB/s in a steady state after preconditioning, so this test is required.
  6. Measure bus power during full writes with an inline USB meter. Pass: 4.5 W or less with no brownout. The plain T7's draw is unpublished.
  7. Run the operator-note noise-floor A/B test at 1541, 1575 and 1691 MHz, with the T7 connected and idle against the T7 deauthorized.
  
  If step 5 or 6 fails, step up to the T7 Shield 1 TB (Reichelt EUR 249) and re-dimension the holder. Do not step down to a cheaper brand.
- **Stack changes:** None to rails, connectors, drivers, firmware or the case. The same SKU keeps the 85x57x8 mm shaded holder, the USB 3 A-to-C cable of 0.5 m or less with ferrites, uas, the smartctl -d sntasmedia 55 C stop rule and the WS4612 USB budget.
  
  BOM and documentation edits:
  - (a) Change the T7 line from 'Optional / gated' to required in the with-Lime default, per the user decision of 18 Oct 2026. Delete the 'None needed without the Lime' note.
  - (b) Price it as Reichelt MU-PC1T0T EUR 205.90 incl. VAT ($231.45; $194.50 ex VAT), limited stock. Fallbacks: MU-PC1T0H EUR 209.00 at Reichelt, or Alternate EUR 224.90 in stock. Re-price at the 1 Dec 2026 gate because of NAND-shortage price moves.
  - (c) If other parts already ship from Reichelt (as search A suggests for the microSD cards and an A-A cable; not confirmed in the stack files), add the T7 to that order to share shipping.
  - (d) Add acceptance tests 1-7 to the Lime acceptance list.
  - (e) Keep the T7 Shield as the documented step-up if the T7 fails.
- **Sources:**
  - https://www.reichelt.com/de/en/shop/search/samsung%20t7
  - https://www.reichelt.com/de/en/shop/search/portable%20ssd%201tb
  - https://www.alternate.de/Samsung/Portable-SSD-T7-1TB-Externe-SSD/html/product/1639854
  - https://download.semiconductor.samsung.com/resources/data-sheet/Samsung_Portable_SSD_T7_Datasheet_Rev2.0.pdf
  - https://download.semiconductor.samsung.com/resources/warranty/Portable_SSD_Full_Warranty_Statement_English.pdf
  - https://ssd-tester.com/samsung_portable_ssd_t7_1tb.html
  - https://ssd-tester.com/sandisk_extreme_portable_ssd_v2_1tb.html
  - https://raw.githubusercontent.com/smartmontools/smartmontools/master/smartmontools/drivedb.h
  - https://europe.kioxia.com/content/dam/kioxia/shared/personal/support/download/ssd/asset/productbrief/KIOXIA_Exceria_Plus_G2_Portable_Product_Brief.pdf
  - https://www.kingston.com/datasheets/SXS2000_us.pdf
  - https://kb.sandisk.com/app/answers/detail/a_id/23513/~/sandisk-extreme-portable-v2-ssd-support-information
  - https://www.sandisk.com/tools/documentRequestHandler?docPath=%2Fcontent%2Fdam%2Fasset-library%2Fen_us%2Fassets%2Fpublic%2Fsandisk%2Fproduct%2Fportable-drives%2Fextreme-portable-ssd%2Fdata-sheet-extreme-portable-ssd.pdf
  - https://ldlc.com/en/product/PB00486401.html
  - https://talk.tidbits.com/t/sandisk-portable-ssd-failures-proliferate/23455?page=2
  - https://www.diyphotography.net/?p=224823
  - https://americas.lexar.com/product/lexar-sl500-portable-ssd/
  - https://www.storagereview.com/news/micron-exits-crucial-consumer-business-to-focus-on-higher-growth-segments
  - https://evertiq.com/design/2025-12-04-micron-to-exit-crucial-consumer-business-after-29-years
  - https://www.hostzealot.com/blog/news/a-dead-ssd-an-empty-warehouse-and-a-warranty-problem
  - https://www.kleinanzeigen.de/s-samsung-t7-1tb/k0

