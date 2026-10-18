# Storage: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_3e735695-e00`_

- **Component:** Storage (raw IQ recording + OS) for Radxa Dragon Q6A handheld satellite receiver
- **Current pick assessment:** The plan is mostly sound, with caveats. A UFS 3.1 module in the Q6A eMMC/UFS combo connector is the fastest storage left once the LimeSDR takes the M.2 slot.
  
  Measured on the Q6A (Radxa docs, dd, Radxa OS):
  - Radxa UFS 128GB (Samsung KLUDG4UHDC-B0E1): 1703 MB/s read, 388 MB/s write.
  - Radxa UFS 256GB (Kioxia THGJFGT1E45BAILB): 1811 MB/s read, 557 MB/s write.
  
  The module is UFS 3.1, 2-lane HS-G4. It is rated up to 2100 MB/s read and 1800 MB/s write, but only with WriteBooster (an SLC cache). Radxa's own brief says its ROCK 4D gets about 250 MB/s write in typical benchmarks.
  
  The mainline Qualcomm UFS driver (ufs-qcom.c) does turn WriteBooster on (UFSHCD_CAP_WB_EN). So the short dd results above are probably inside the cache, and what happens after the cache fills on these modules is unknown. One UFS 3.1 data point (a Pixel 6 / gs101 kernel patch thread) measured 945 MB/s with WriteBooster, dropping to about 260 MB/s after the cache filled. Expect roughly 250-300 MB/s on the module once the cache is full (an inference, not measured).
  
  Verdict against the targets:
  - 56 MHz raw IQ (61.44 Msps cs16 = 245.76 MB/s, one RX channel): achievable but marginal after the cache. It is comfortable as cs8 (123 MB/s) or packed 12-bit (184 MB/s).
  - 160 Msps cs16 sustained (640 MB/s): not achievable. This needs a RAM buffer.
  
  Capacity is the bigger limit: at 246 MB/s, 128 GB holds about 8 minutes and 256 GB about 17 minutes.
  
  Endurance: Radxa publishes no TBW (Evelta's listing says "not specified"). Linux exposes life_time_estimation_a/b and wb_life_time_est in sysfs, so wear can be monitored.
  
  Temperature: the standard module is rated 0 to 70 C; an industrial version is rated -25 to 85 C. Ukrainian winter field use is below spec.
  
  Prices:
  - 2025 prices ($20 / $35.59 / $55.68 for 64 / 128 / 256GB) are obsolete because of the 2026 NAND shortage (Phison: NAND prices more than doubled).
  - Allnet China lists 64GB $19, 128GB $65.90, 256GB $75.90, 512GB $89.90, but only the 128GB is in stock; the 64GB, 256GB and 512GB are sold out.
  - Tinytronics (NL) has the 128GB at EUR 58, not in stock, 2-4 weeks.
  
  The Q6A officially lists UFS 128/256/512GB and eMMC 16/32/64GB modules. Radxa warns that untested third-party modules can short the board.
  
  Research note: the shared web-search budget ran out mid-research. TBW figures for UFS and NVMe drives, AliExpress and Ukrainian prices for USB-NVMe enclosures, and the T7 Shield's Ukrainian price could not be checked and are marked unverified.
- **Alternatives:**
  1.
    - **Name:** Radxa UFS 3.1 Module 128GB (RA022-B10J0U2) - current pick, smallest size
    - **Key specs:** UFS 3.1, 2-lane HS-G4, 30x22 mm, dual B2B connector (GB042-30S + 34S). Measured on Q6A: 1703 MB/s read / 388 MB/s write (dd). Standard grade 0-70 C. Radxa guarantees supply until Sept 2035.
    - **Price:** $65.90 Allnet China (in stock); EUR 58 incl. VAT Tinytronics NL (2-4 wk lead time); ~INR 2,815 Hubtronics
    - **Pros:** Officially supported and bootable. Fastest storage left once the M.2 slot is taken. Very small; no cable. The kernel enables WriteBooster.
    - **Cons:** Only about 8 min of 56 MHz cs16 recording; OS plus a few passes leaves little room. Post-cache write speed unknown (likely ~250-300 MB/s). No TBW published. Price roughly doubled since 2025.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
      - https://shop.allnetchina.cn/products/high-performance-ufs-3-1-module
      - https://www.tinytronics.nl/en/data-storage/modules/radxa-ufs-module-128gb
      - https://dl.radxa.com/accessories/ufs-module/rad-doc-0154_radxa_ufs_module_product_brief__revision_1.2_g69c4d5d.pdf
    - **Availability:** In stock at Allnet China; EU (Tinytronics) 2-4 weeks
    - **Q6a compatibility:** Official; listed in Q6A product brief and UFS module brief
  2.
    - **Name:** Radxa UFS 3.1 Module 256GB (RA022-B10J0U4, Kioxia THGJFGT1E45BAILB)
    - **Key specs:** UFS 3.1 2-lane. Measured on Q6A: 1811 MB/s read / 557 MB/s write (dd), the fastest Q6A write figure published. About 17 min of 61.44 Msps cs16 or 34 min of cs8.
    - **Price:** $75.90 Allnet China (sold out); Evelta India INR 7,316 incl. GST (stock status contradictory)
    - **Pros:** Best measured Q6A write speed, about 43% above the 128GB. Only about $10 more than the 128GB (Allnet). Enough for OS plus many HRPT/LRPT pass recordings.
    - **Cons:** Often out of stock. No TBW or post-cache data. Standard grade only 0-70 C.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
      - https://shop.allnetchina.cn/products/high-performance-ufs-3-1-module
      - https://evelta.com/ufs-module-detachable-ufs-redefined-embedded-storage-module-radxa/
    - **Availability:** Intermittent; check Radxa's AliExpress store, Allnet China, Arace, Evelta
    - **Q6a compatibility:** Official (256GB listed for Q6A; measured by Radxa on Q6A)
  3.
    - **Name:** Radxa UFS 3.1 Module 512GB (RA022-B10J0U8)
    - **Key specs:** UFS 3.1 2-lane. Rated up to 2100 MB/s read / 1800 MB/s write with WriteBooster (Evelta lists the 512GB as the rated-speed version). No Q6A measurement.
    - **Price:** $89.90 Allnet China (sold out)
    - **Pros:** Best $/GB of the UFS line (about $0.18/GB). About 35 min of 56 MHz cs16 recording. Single-part solution.
    - **Cons:** Sold out; real Q6A write speed unverified; no TBW published.
    - **Sources:**
      - https://shop.allnetchina.cn/products/high-performance-ufs-3-1-module
      - https://evelta.com/ufs-module-detachable-ufs-redefined-embedded-storage-module-radxa/
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
    - **Availability:** Sold out at Allnet (Oct 2026); 1TB listed in specs but no price found
    - **Q6a compatibility:** Official (512GB listed in Q6A product brief)
  4.
    - **Name:** External USB SSD on the free USB 3.1 Gen1 port: TLC NVMe (2230/2242) in a UAS enclosure, or Samsung T7 / T7 Shield 1TB
    - **Key specs:** Q6A USB 3.1 Type-A is 5 Gbps. Measured on Q6A: about 395 MB/s write (fio) with a USB3-to-NVMe adapter on the 5000M bus with the uas driver (SmartHomeCircle, Jan 2026). Samsung T7: up to 1050/1000 MB/s on 10 Gbps, so capped at ~400 MB/s here. TweakTown, citing Samsung, says the T7 Shield 1TB sustains ~900 MB/s writes until full.
    - **Price:** Samsung T7 1TB Indigo Blue (MU-PC1T0H/WW): 7,499 UAH on Rozetka (in stock per listing snapshot; Grey 11,499 UAH, out of stock); US $230-275. WD SN740 512GB: 4,925-6,886 UAH (hotline.ua, 14 offers); SN740 1TB ~$160-196 US. Enclosure price not verified (AliExpress RTL9210B/ASM2362 types).
    - **Pros:** About 395 MB/s covers 56 MHz cs16 with ~60% headroom. 1TB is about 68 min of 56 MHz cs16. Hot-swappable for moving data to a PC (no network offload or card reader needed). Wear lands on a cheap replaceable drive instead of the boot UFS. The T7 Shield is IP65-rugged for outdoor use. Also suggests Q6A USB3 bulk throughput (~395 MB/s) is better than feared.
    - **Cons:** Cannot reach 640 MB/s. Adds a cable, 2-4 W and bulk. The standard T7's post-cache speed is uncertain (one forum user reported ~80 MB/s). Bus power may be marginal for some NVMe drives. Prices inflated by the 2026 NAND shortage. Avoid QLC drives such as the Crucial P310 (ServeTheHome: ~330 MB/s steady at 85% full, throttles at 82 C).
    - **Sources:**
      - https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/usb
      - https://hard.rozetka.com.ua/ua/samsung_mu_pc1t0h_ww/p234908281/
      - https://hotline.ua/ua/computer/diski-ssd/301688-21877391/?series=true
      - https://ssd-tester.com/samsung_portable_ssd_t7_shield_1tb.html
      - https://forums.anandtech.com/threads/usb-c-slows-down-but-only-after-time.2623756/post-41353697
      - https://www.servethehome.com/crucial-p310-review-a-tiny-2tb-m-2-2230-nvme-ssd/3/
    - **Availability:** Widely available in Ukraine (Rozetka, hotline.ua) and on AliExpress
    - **Q6a compatibility:** Works (UAS confirmed on Q6A); uses the USB 3.1 port, which the stack leaves free
  5.
    - **Name:** NVMe 2230 SSD in the M.2 slot (only if the SDR moves off M.2)
    - **Key specs:** Q6A M.2 M-key 2230, PCIe Gen3 x2. Radxa measured 1649 MB/s read / 1467 MB/s write. M.2 SATA not supported.
    - **Price:** WD SN740 512GB 4,925-6,886 UAH; 1TB ~$160-196 US
    - **Pros:** The only option that sustains 640 MB/s (160 Msps cs16) in hardware, with TLC drives like the SN740.
    - **Cons:** Conflicts with the LimeSDR Micro M.2, which is M.2-only (2280, B+M key, PCIe Gen3 x1). Not usable in the v3 stack.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/nvme
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
    - **Availability:** Widely available
    - **Q6a compatibility:** Official, but the slot is taken by the SDR
  6.
    - **Name:** PCIe switch / dual-M.2 adapter sharing the Q6A M.2 slot between the SDR and an NVMe
    - **Key specs:** ASM1182e boards (Pineboards HatDrive Dual, Pimoroni NVMe Base Duo, Geekworm X1004): Gen2 x1, 5 GT/s shared. Seeed PCIe 3.0 Dual M.2 HAT: ASM2806 (Gen3 x2 upstream, only x1 used), 2x M-key Gen3 x1 slots, 2230-2280, 8 GT/s shared, 3 A max, Pi 5 FFC input.
    - **Price:** Seeed ASM2806 HAT: $45 (Seeed site, CN warehouse; a reader estimates ~$90 to the EU after duties)
    - **Pros:** In theory gives the SDR plus an NVMe at ~800 MB/s shared bandwidth.
    - **Cons:** No verified M.2-edge-hosted Gen3 switch board for the Q6A; the Seeed board needs a Pi 5 FFC upstream. ASM1182e Gen2 (~400 MB/s total) would choke SDR (184-246 MB/s) plus recording (246 MB/s). Pi users report booting behind a switch is unsupported. Adds height and length to a 2280 SDR stack, plus power and enumeration risk. Untested on Q6A firmware.
    - **Sources:**
      - https://www.cnx-software.com/2025/01/21/pcie3-0-to-dual-m-2-hat-for-raspberry-pi-5-features-asmedia-asm2806-pcie-3-0-switch/
      - https://pipci.jeffgeerling.com/hats/pineboards-hatdrive-dual-nvme-m2.html
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/nvme
    - **Availability:** Pi-specific boards available; no Q6A-ready product found
    - **Q6a compatibility:** Unverified/experimental; not recommended
  7.
    - **Name:** Radxa eMMC module (16/32/64GB)
    - **Key specs:** Uses the same combo connector as UFS (one or the other, not both). No Q6A speed data published; eMMC 5.1 is generally far slower than UFS 3.1 (general knowledge, not measured here).
    - **Price:** Not verified
    - **Pros:** Cheap, officially supported boot media.
    - **Cons:** Too small and too slow for wideband IQ. Occupies the same connector as UFS, so it is strictly worse here.
    - **Sources:**
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
    - **Availability:** Radxa channels
    - **Q6a compatibility:** Official
  8.
    - **Name:** microSD on Q6A
    - **Key specs:** Measured on Q6A (Jeff Geerling, iozone, Samsung Pro Plus 32GB): 61.45 MB/s sequential write, 73.7 MB/s sequential read, 0.80 MB/s 4K random write.
    - **Price:** Cheap (a few dollars to ~$20; not price-checked)
    - **Pros:** Enough for LRPT and narrowband HRPT baseband (1-6 Msps cs16 = 4-24 MB/s); good as a spare boot/rescue card.
    - **Cons:** Far too slow for 56 MHz (needs 123-246 MB/s); poor random write as an OS drive.
    - **Sources:**
      - https://github.com/geerlingguy/sbc-reviews/issues/85
    - **Availability:** Ubiquitous
    - **Q6a compatibility:** Official slot
- **Recommended:**
  - **Name:** Three tiers: Radxa UFS 3.1 256GB (or 512GB if in stock) as OS plus pass storage; a 1TB TLC USB SSD (Samsung T7 Shield / T7 1TB, or TLC 2230 NVMe such as SN740 in a UAS enclosure) on the USB 3.1 port for wideband captures; and a RAM ring buffer of about 8-10 GB from the 16 GB for 160 Msps bursts
  - **Why:** 1. UFS module: the 256GB Kioxia module has the best measured Q6A write (557 MB/s dd) for only about $10 more than the 128GB. Choose the 512GB ($89.90) if it can be found, since it is the best $/GB. It boots the OS and stores normal pass recordings: Meteor HRPT at e.g. 6 Msps cs16 is 24 MB/s, about 22 GB per 15-minute pass, and LRPT is much less.
  
  2. USB SSD: measured about 395 MB/s fio write on the Q6A's USB 3.1 port, about 60% headroom over 56 MHz cs16 (245.76 MB/s). 1 TB holds about 68 min of cs16 or about 136 min of cs8. It hot-swaps to a PC for offline SatDump processing, so it doubles as the data-offload path, and it keeps heavy write wear off the boot module. The T7 Shield is preferred for its claimed ~900 MB/s sustained write until full and IP65 shell, but its Ukrainian price was not verified. The T7 1TB is 7,499 UAH on Rozetka.
  
  3. RAM ring buffer: 160 Msps cs16 (640 MB/s) cannot be sustained by any storage reachable alongside the SDR. Capture into a RAM ring and drain to UFS or USB afterwards:
  - 10 GB of RAM holds about 15.6 s of 160 Msps cs16 with no drain.
  - Draining at ~260-395 MB/s during capture stretches that to roughly 26-41 s.
  - 160 Msps cs8 (320 MB/s) roughly doubles those times, and drained to the USB SSD (~395 MB/s) it can roughly keep up.
  - Writing to UFS and the USB SSD in parallel (separate files or md RAID0) may reach about 640 MB/s, but this is untested.
  
  Write formats: record with the LimeSuiteNG linkFormat I12 (packed 12-bit on the link). Store cs8, cu8, cs16, wav16 or ziq/ziq2, all supported by SatDump. Use cs8 or decimation for surveys and keep cs16 for short high-dynamic-range captures.
  - **Price:** About $76-90 for UFS (Allnet list price; 256GB/512GB currently sold out there), plus about 7,499 UAH for a Samsung T7 1TB on Rozetka (US $230-275), or an SN740 512GB at 4,925-6,886 UAH plus an enclosure (enclosure price unverified). Total roughly $250-270 in October 2026 NAND-shortage pricing.
  - **Sources:**
    - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
    - https://shop.allnetchina.cn/products/high-performance-ufs-3-1-module
    - https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5
    - https://hard.rozetka.com.ua/ua/samsung_mu_pc1t0h_ww/p234908281/
    - https://ssd-tester.com/samsung_portable_ssd_t7_shield_1tb.html
    - https://raw.githubusercontent.com/myriadrf/LimeSuiteNG/develop/src/include/limesuiteng/types.h
    - https://raw.githubusercontent.com/SatDump/SatDump/master/src-core/common/dsp/io/baseband_type.h
- **Budget option:**
  - **Name:** Radxa UFS 3.1 Module 128GB only, recording cs8 or decimated, plus a RAM ring buffer; add any USB 3 SSD later
  - **Why:** This is the cheapest officially supported option that still writes 388 MB/s (dd, Q6A).
  - cs8 at 61.44 Msps is 123 MB/s, well under even a pessimistic post-cache rate of about 250 MB/s.
  - Narrowband pass recordings (LRPT, HRPT, CubeSats, QO-100 transponder slices) are 4-40 MB/s and fit easily.
  - Offload over the Q6A's GbE (about 110 MB/s, theoretical).
  - Avoid microSD for anything wideband (61 MB/s write measured).
  - Plugging any existing USB 3 SSD into the USB 3.1 port later gives the primary setup without redesign.
  - **Price:** $65.90 (Allnet China, in stock) or EUR 58 (Tinytronics NL, 2-4 weeks)
- **Risks:**
  - Post-cache write speed of Radxa UFS modules on Q6A is unpublished. Radxa's 388/557 MB/s figures are short dd runs that likely land in the WriteBooster SLC cache. Other UFS 3.1 data suggests about 250-260 MB/s once the cache is full, which is borderline for 56 MHz cs16. Test before trusting it: fio --rw=write --bs=1M --direct=1 --size=100G, logging speed over time.
  - No TBW or endurance rating is published for Radxa UFS modules (Evelta: not specified). At 246 MB/s the device writes about 885 GB per hour, roughly 3.5 full drive writes per hour on a 256GB module. Keep heavy captures on the replaceable USB SSD and watch /sys/.../health_descriptor/life_time_estimation_a/b and wb_life_time_est (exposed by mainline ufs-sysfs.c).
  - Temperature: the standard UFS module is rated 0 to 70 C and the industrial grade -25 to 85 C (SKU mapping unclear). Consumer NVMe and USB SSDs are typically 0-70 C. Winter field use in Ukraine is below spec at cold start. Pre-warm the device, use the industrial UFS if obtainable, and keep the SSD inside the warm case.
  - Thermal throttling: the QLC Crucial P310 2230 throttled at 82 C in ServeTheHome's test; a commenter saw transfers drop to about 60 MB/s at 85 C. In a sealed 3D-printed case next to the SoC and SDR, give the SSD and UFS module airflow or a thermal pad and log temperatures during long captures.
  - Availability and price volatility: 256GB and 512GB UFS modules were sold out at Allnet in Oct 2026. NAND prices more than doubled in 2026 (Phison CEO), and TrendForce expects another 15-20% in Q4 2026. The $35/$55 prices in 2025 articles are obsolete.
  - USB SSD power and stability: the Q6A brief recommends at least a 24 W (12 V/2 A) supply when USB 3.1 and PCIe are fully loaded. A bus-powered NVMe enclosure plus the LimeSDR plus the RTL-SDR can cause brownouts or UAS resets, so size the PD source accordingly. Only one Q6A USB storage write figure (~395 MB/s, SmartHomeCircle) exists, and no read figure was reported.
  - Using cs8 instead of cs16 cuts the LMS7002M's 12-bit dynamic range. Strong terrestrial signals near weak satellite downlinks may clip or raise the noise floor; set the gain carefully or use cs16 for short captures.
  - Third-party UFS or eMMC modules are risky: Radxa warns some can short the board and permanently damage it, voiding the warranty. Buy genuine RA022-B10J0Ux modules only.
  - The PCIe-switch route (sharing the M.2 slot) has no Q6A-proven product. ASM1182e boards are Gen2 and bandwidth-starved, the ASM2806 board needs a Pi 5 FFC upstream, and enumeration, power and boot behaviour on the Q6A are unknown.
  - Research gap: the shared web-search budget ran out before TBW, enclosure-price and T7 Shield Ukrainian-price lookups, so those items are unverified.
- **Integration notes:**
  - Data-rate math, per RX channel:
  - 61.44 Msps cs16 = 245.76 MB/s; cs8 = 122.9 MB/s; packed I12 = 184.3 MB/s.
  - 160 Msps cs16 = 640 MB/s; I12 = 480 MB/s; cs8 = 320 MB/s.
  - Two RX channels (2R) double all of these, so 2x56 MHz cs16 needs 491.5 MB/s and only works through the RAM buffer.
  - Partitioning: the UFS module holds Ubuntu plus SatDump/SDR++ plus a working area for pass recordings. Mount the USB SSD as /data/iq with ext4 or XFS, noatime, a large commit interval, and O_DIRECT or large (1-4 MB) writes. Avoid exFAT/NTFS on Linux for sustained writes; format ext4 and read it on the PC with a driver, or use the Q6A to export it over GbE.
  - RAM ring buffer: reserve 8-10 GB of the 16 GB for a hugepage-backed or tmpfs ring. A small C/Python recorder (SoapySDR or LimeSuiteNG) can fill it pre-trigger or post-trigger and drain it in the background. Leave about 4-6 GB for Ubuntu, SDR++/SatDump GUIs and the NPU classifier.
  - Use the right SatDump baseband formats: cs8/cu8 for wide surveys, cs16 for HRPT/S-band captures, ziq/ziq2 (compressed) for archiving when the CPU has headroom. The 8-bit-or-16-bit ziq depth is chosen when recording. Compression costs CPU, so benchmark it on the A78 cores before using it live.
  - Physical: the UFS module (30x22 mm) mounts on the board's B2B combo connector, with no cable. Route the USB SSD with a short right-angle USB-A to USB-C cable, strain-relieved in the case. For fast swaps, mount a small enclosure (2230/2242 class) with a 3D-printed latch.
  - First boot: flash Ubuntu to UFS with Radxa's UFS reader or the 'no UFS reader' procedure. Update the Q6A firmware/UEFI first; a forum report says a firmware upgrade made UFS unbootable, so keep a microSD rescue image.
  - Cross-component flag for the SDR owner: the LimeSDR Micro Crowd Supply page now lists $249 Basic / $299 GNSS, with new orders shipping Dec 15, 2026. The $199 early-bird price has ended; first batch was scheduled Sept 30, 2026. Separately, the measured ~395 MB/s UAS write on the Q6A's USB 3.1 port suggests Qualcomm USB3 bulk throughput may suffice for ~246 MB/s, which is useful if the SDR plan is revisited.
  - Double-duty: the USB SSD is both capture storage and offline data mule (removes the need for network offload or a card reader). The UFS module is both boot drive and pass storage (no separate eMMC or microSD needed). The 16 GB RAM is the burst buffer (no extra hardware). The Radxa UFS/eMMC USB reader (older listing ~$25; current price unverified) both flashes the OS and recovers data on a PC.
- **Double duty opportunities:**
  - USB 3 SSD as both the wideband capture target (~395 MB/s on Q6A) and a hot-swap data mule for offline SatDump/GNU Radio processing on a PC. No network offload or extra card reader needed, and write wear lands on a cheap replaceable part.
  - UFS 3.1 module as both OS boot drive and fast working storage for normal satellite passes, so no separate eMMC or microSD boot media is needed (keep one microSD only as a rescue image).
  - The 16 GB LPDDR5 doubles as a burst buffer for 160 Msps captures (about 15-40 s), replacing the need for an NVMe via a risky PCIe switch.
  - Samsung T7 Shield (IP65, rubberized) doubles as weather- and drop-tolerant field storage, so the case needs no separate protection for the drive.
  - Radxa UFS/eMMC USB 3 reader: OS flashing plus reading captures off the UFS module on any PC (optional; current price unverified).
- **Confidence:** medium

## Форуми та досвід спільноти (`forums`)

_Run `wf_3e735695-e00`_

- **Component:** Storage (raw IQ recording + OS): Radxa UFS 3.1 module on Dragon Q6A, USB 3 SSD on the Q6A's USB 3.1 port, RAM ring buffer; alternatives: PCIe switch, eMMC, microSD
- **Experiences:**
  1.
    - **Product:** Radxa UFS 3.1 Module 256GB (Kioxia THGJFGT1E45BAILB) on Dragon Q6A
    - **Source url:** https://forum.radxa.com/t/ufs-random-reboots/30630
    - **Community:** Radxa forum (thread 'UFS random reboots', 50 posts, pages 1-3, Apr-May 2026)
    - **What they built:** Two users with Q6A boards. datum: desktop with the Radxa Noble GNOME R2 image, kernel 6.18.2-3-qcom, 36 W DC12 or USB-C PD, copper heatsink and fan. pamvdam: three Q6A R2 boards on PoE for a SUSE MicroOS cluster.
    - **Problems:**
      - Boot was normal, then 1-5 s freezes every few minutes, followed by permanent hangs or reboots. 'reboot' sometimes timed out.
      - dmesg showed ufshcd-qcom errors: device abort on START STOP UNIT, pa_err/dl_err, invalid OCS, eh_device_reset failing with -110, and the link unable to exit hibernate (H8).
      - Radxa reproduced the fault on the Kioxia module only; their Samsung-based module had no problems. The same Kioxia chip worked fine on other (Rockchip) boards.
      - These did not help: SPI firmware 6.0.260120, turning off UFS auto-hibernate in sysfs, and Radxa's limit-hs-gear=<2> test kernel. The gear limit also cut speed: fio write 377 vs 499 MB/s, read 480 vs 1848 MB/s.
      - After the fix, an 'apt upgrade' replaced the patched kernel with stock 6.18.2-4-qcom and removed the fix.
    - **Fixes:**
      - Interim workaround from Radxa (chenchongbiao): a keep-alive shell loop that writes to a file every 0.1 s so the UFS never enters H8. datum saw no stutter or errors for about 24 h.
      - Permanent fix: a Kioxia-specific UFS_DEVICE_QUIRK_PA_TACTIVATE, which sets PA_TACTIVATE to 1 ms. It shipped as test kernel linux-image-6.18.2-4-qcom and was merged as radxa/kernel PR #551 (linux-6.18.2) on May 11, 2026.
      - Keep the fixed kernel with 'apt-mark hold'.
      - Armbian: build with board=radxa-dragon-q6a, branch=current, then dpkg -i the three .debs. The Armbian maintainer said the fix ships in Armbian 26.05.
      - Verified in this research: the quirk is in the radxa/kernel linux-7.0.11 branch (updated Oct 14, 2026) but NOT in mainline Linux (torvalds master, 7.3-rc7).
    - **Outcome:** Both users report the fix working, with no UFS errors or freezes after 1-2 days (pamvdam: ~9 days of uptime in a cluster node). Speeds after the fix:
  - fio read QD32: 1917 MB/s
  - hdparm --direct: 1298 MB/s
  - fio write: 473 MB/s, from a 2 GiB, 4.5 s run (so inside the WriteBooster cache)
  No write test lasting minutes or tens of GB was posted. pamvdam asked whether 128GB modules are always Samsung and 256GB always Kioxia; nobody answered.
  2.
    - **Product:** Radxa UFS module (Kioxia) under SUSE MicroOS with mainline kernel 6.19.x on Q6A
    - **Source url:** https://forum.radxa.com/t/radxa-poe-hat-overlay-on-microos/30704
    - **Community:** Radxa forum
    - **What they built:** SUSE MicroOS cluster nodes on Q6A with a PoE HAT.
    - **Problems:**
      - UFS3 (Kioxia) was 'too unstable for use' on mainline 6.19.x, the same as on the stock Radxa OS.
      - NVMe, eMMC and networking worked fine.
    - **Fixes:**
      - None on mainline. The fix exists only as the Radxa/Armbian vendor-kernel quirk (see the 'UFS random reboots' thread). pamvdam asked how it would reach upstream and MicroOS kernels.
    - **Outcome:** Unresolved for mainline and distribution kernels. Mainline master still lacks the quirk as of Oct 2026 (checked).
  3.
    - **Product:** Radxa UFS module + Q6A SPI boot firmware (early units)
    - **Source url:** https://forum.radxa.com/t/upcoming-radxa-dragon-q6a/26723?page=2
    - **Community:** Radxa forum (willy tarreau, strongtz, Sept 2025)
    - **What they built:** Early Q6A evaluation: UFS boot, NVMe test, build benchmarks.
    - **Problems:**
      - With UFS installed, early images did nothing; logs showed 'UFS GEAR: 4' and ufs_error_log entries.
      - With UFS connected, the board would not boot from SD or USB.
      - SoC hit 90-91 C and throttled during builds without a fan.
    - **Fixes:**
      - Update the SPI boot firmware with edl-ng (strongtz).
      - Press 'c' in GRUB and type 'exit' to try other boot media.
      - A powerful fan kept the SoC at or below 79 C with no throttling.
    - **Outcome:** After the firmware update, UFS read about 1.6-1.8 GB/s and a Samsung 980 NVMe read 1.3 GB/s at Gen3 x2. Boot priority was NVMe > UFS > SD/USB at the time.
  4.
    - **Product:** Q6A SPI firmware 250929 / 251013 / 260120 with UFS boot
    - **Source url:** https://forum.radxa.com/t/radxa-dragon-q6a-firmware-snapshot/28886
    - **Community:** Radxa forum
    - **What they built:** Q6A boards booting from UFS and SD while updating the boot firmware.
    - **Problems:**
      - Firmware 250929 stalled after 'Exit EBS' when booting from UFS. It did not load the embedded DTB correctly.
      - Because UFS is tried first, a failed UFS boot blocked SD recovery.
      - One user's board stopped booting after a 2025-11-13 update (SD only), with no resolution.
      - Firmware 260120 note: images with the old v6.17 kernel can no longer update the SPI flash.
    - **Fixes:**
      - Physically remove the UFS module and the board boots from SD.
      - Firmware 251013 fixed the DTB and set boot order to USB > SD > NVMe > eMMC > UFS.
      - Update on the device with 'sudo edl-ng --hostdev-as-target /dev/mtd0 rawprogram rawprogram0.xml patch0.xml', or from a host in EDL mode with 'edl-ng --memory spinor --loader prog_firehose_ddr.elf rawprogram rawprogram0.xml patch0.xml'.
      - Use RadxaOS r1 or newer images.
    - **Outcome:** Resolved for willy after 251013; he then flashed and booted the T4 image on UFS. Other bricked-after-update reports remain open.
  5.
    - **Product:** Radxa USB Transfer Module (UFS USB reader) for flashing a 128GB UFS 3.1 module
    - **Source url:** https://forum.radxa.com/t/load-systen-on-an-ufs-3-1-module-for-dragon-q6a/31102
    - **Community:** Radxa forum (June 2026)
    - **What they built:** Flashing an OS onto a UFS module for a Q6A.
    - **Problems:**
      - Neither Windows nor macOS detected the reader.
    - **Fixes:**
      - No replies in the thread.
      - Alternative routes documented elsewhere:
  - Armbian Imager 2.0 (Aug 2026) flashes Q6A images straight to UFS over EDL/USB with no third-party tools; set the UEFI boot order manually afterwards (https://forum.armbian.com/topic/61701-news-from-armbian-sbc-storage/).
  - Or boot from SD/USB and write the UFS on the board itself.
    - **Outcome:** Unresolved in the thread; workaround available via Armbian Imager EDL flashing.
  6.
    - **Product:** Radxa UFS module thermal behaviour on Q6A
    - **Source url:** https://forum.radxa.com/t/dragon-q6a-vpu-firmware-loading/31226
    - **Community:** Radxa forum (jvvv, July 2026)
    - **What they built:** Alpine Linux port and compile workloads on Q6A, in an 'armored' heatsink case with USB fans above and below.
    - **Problems:**
      - During builds the UFS module was the only part above 60 C. It runs hottest, probably because it sits next to the SoC.
    - **Fixes:**
      - Heatsink case plus two fans kept everything else below 60 C. Separately, datum's 256GB module stayed under 60 C in stress tests with a heatsink and fan.
    - **Outcome:** Works. The module still reaches about 60 C, against a commercial rating of 0-70 C, even with active cooling.
  7.
    - **Product:** Third-party (Orange Pi) eMMC module on Q6A's eMMC/UFS combo connector
    - **Source url:** https://forum.radxa.com/t/radxa-a7s-compatibility-with-emmc-module/30638
    - **Community:** Radxa forum (Apr 2026)
    - **What they built:** Trying cheaper non-Radxa eMMC modules on Q6A and A7S.
    - **Problems:**
      - The Orange Pi eMMC module shorts the Q6A's UFS power lines and trips shutdown protection immediately.
      - On the A7S a transplanted chip made the board draw under 1 mA.
    - **Fixes:**
      - Radxa (Sophon, in the Windows-on-Q6A thread) confirmed that removing the UFS-side connector from the Orange Pi module prevents the short.
      - Otherwise use genuine Radxa modules only.
    - **Outcome:** Third-party modules are unsafe without modification. No list of compatible eMMC chips exists; a request for one went unanswered.
  8.
    - **Product:** Q6A M.2 slot reliability vs UFS (Windows 11 ARM)
    - **Source url:** https://forum.radxa.com/t/nvme-2230-not-detected/30807
    - **Community:** Radxa forum (May 2026)
    - **What they built:** Windows 11 ARM64 install on an NVMe 2230 in the Q6A.
    - **Problems:**
      - After 2-3 h the system rebooted and the NVMe slot never detected any drive again: three different 2230 SSDs, under Windows and RadxaOS.
      - A separate thread reports a 512GB Gen3x4 2230 visible in Linux but not enumerated by UEFI firmware 260120 (https://forum.radxa.com/t/nvme-ssd-m-2-2230-gen3x4-not-enumerated-by-uefi/31195).
    - **Fixes:**
      - Clean the contacts and remove GPIO/fan devices: no effect.
      - Board returned under warranty.
      - The user switched to a Radxa UFS module, which then ran 'really well'.
    - **Outcome:** Slot failure root cause unknown. UFS served as a working fallback. Another user had a Crucial P310 working fine.
  9.
    - **Product:** USB3-to-NVMe adapter (unnamed) on Q6A USB 3.1 Gen1 port; UFS and NVMe comparison
    - **Source url:** https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5
    - **Community:** SmartHomeCircle review blog (Jan 2026)
    - **What they built:** Q6A benchmarked under Windows 11, Armbian and Radxa OS with NVMe, UFS and a USB-NVMe adapter.
    - **Problems:**
      - The bare board hit 105 C and shut down in a Vulkan benchmark.
      - Only one USB storage figure was published (fio write ~395 MB/s); no read figure, no fio parameters, adapter not named.
    - **Fixes:**
      - A 25 mm heatsink plus a fan on GPIO 5 V brought load temperatures under 80 C (Armbian) and 90-92 C (Windows).
      - USB link confirmed at 5000M with the uas driver via lsusb -t.
    - **Outcome:** USB 3 SSD write of about 395 MB/s on the Q6A.
  UFS read figures by OS:
  - Windows: ~1416 MB/s
  - Armbian: ~1384 MB/s
  - Radxa OS: ~1187 MB/s
  NVMe ~750-1644 MB/s depending on OS. Idle about 4 W and stress about 10 W with NVMe, UFS and a fan.
  10.
    - **Product:** Q6A USB3 SuperSpeed on mainline Linux (QMP combo PHY shared with DisplayPort/HDMI)
    - **Source url:** https://lore.gitlab.freedesktop.org/drm-ai-reviews/20260522060645.4399-1-graham.oconnor@gmail.com/
    - **Community:** Linux DRM/kernel patch review list (May 2026)
    - **What they built:** Mainline Linux 7.0.9 device-tree enablement for the Q6A: HDMI through the RA620 DP-to-HDMI bridge, plus USB3.
    - **Problems:**
      - The RA620 bridge fails DP link training at voltage-swing level 3.
      - USB3 and DP share the QMP combo PHY. The lane split is not documented.
    - **Fixes:**
      - Cap the DP swing at level 2, matching the vendor kernel.
    - **Outcome:** USB3 SuperSpeed at 5 Gbps confirmed via lsusb alongside working HDMI on mainline 7.0.9. No storage throughput figure given.
  11.
    - **Product:** microSD on Q6A (boot/rescue media)
    - **Source url:** https://github.com/geerlingguy/sbc-reviews/issues/85
    - **Community:** GitHub (geerlingguy/sbc-reviews)
    - **What they built:** Standard SBC benchmark run on the Q6A.
    - **Problems:**
      - Samsung Pro Plus 32GB: 61.45 MB/s sequential write and 0.80 MB/s 4K random write.
      - Balena Etcher verify errors left a board with no HDMI or network; reproduced with a second card.
      - Running rsetup on an r2 GNOME image left one board unbootable.
      - Separately, a Q6A that ran Armbian from an A2 microSD for 3-4 months failed when the card developed bad sectors (https://forum.radxa.com/t/radxa-dragon-q6a-was-running-stable-for-3-4-months-then-failed-and-would-no-longer-boot/31509).
    - **Fixes:**
      - Extract the .img before flashing, or enable Etcher's 'trim unallocated space on raw images in ext partitions' option (webfinder42).
    - **Outcome:** microSD works but is far too slow for wideband IQ and has a field-failure report. Suitable only as rescue or boot media.
  12.
    - **Product:** UFS 3.1 256GB on the same SoC (Critical Link MitySOM-QC6490)
    - **Source url:** https://git.criticallink.com/redmine/projects/mitysom_qc6490/wiki/UFS
    - **Community:** Critical Link SoM wiki (vendor engineering notes)
    - **What they built:** Production QCS6490 system-on-module with a 256 GB UFS 3.1 boot device, HS-G4 x2.
    - **Problems:**
      - Write speed swings between about 300 and 1500 MiB/s depending on the WriteBooster state. Their default provisioning uses a 4 GB WriteBooster buffer, and writes slow to the sustained rate once it fills.
    - **Fixes:**
      - Compute the WriteBooster size from sysfs: wb_shared_alloc_units x 512 x allocation_unit_size x segment_size, under /sys/devices/platform/soc@0/1d84000.ufs/.
      - For endurance, LU0 can be provisioned as pSLC: about 30k vs 3k P/E cycles, at one third of the capacity.
      - TBW is estimated as capacity x P/E / WAF; long sequential writes lower WAF.
    - **Outcome:** Best available same-SoC hint: a sustained write floor of roughly 300 MiB/s after the WriteBooster cache. Radxa modules ship pre-provisioned, so pSLC re-provisioning is not a user option without EDL tools.
  13.
    - **Product:** Samsung T7 1TB and T7 Shield 1TB (USB 3.2 Gen2 portable SSDs)
    - **Source url:** https://ssd-tester.com/samsung_portable_ssd_t7_shield_1tb.html
    - **Community:** ssd-tester.com reviews; Shuttermuse review; AnandTech forums
    - **What they built:** Sustained large-file write tests on PC hosts.
    - **Problems:**
      - T7 Shield 1TB: pSLC cache about 20 GB; HD Tune 200 GB write averaged 879 MB/s.
      - T7 1TB: cache about 42 GB; 100 GB write averaged 614 MB/s (https://ssd-tester.com/samsung_portable_ssd_t7_1tb.html).
      - T7 Shield operating range is 0-60 C (https://shuttermuse.com/samsung-t7-shield-ssd-review/).
      - An AnandTech user with a T7 and T9 saw transfers fall from ~1 GB/s to ~80 MB/s after seconds and stay low; root cause unknown. That case was reading from the T7 into a RAID (https://forums.anandtech.com/threads/usb-c-slows-down-but-only-after-time.2623756/post-41353697).
    - **Fixes:**
      - Shuttermuse saw ~800 MB/s on a 64 GB file and no significant slowdown at 75% full.
      - For the AnandTech case, suggestions were copying to a single disk, checking temperatures, and parallel copies. None was confirmed.
    - **Outcome:** Both drives sustain well above the Q6A's ~395 MB/s USB 3.1 Gen1 ceiling on PC hosts. By inference the T7's post-cache rate is about 480 MB/s. No Linux/ARM or SDR-recording report was found for either drive.
  14.
    - **Product:** USB-to-NVMe enclosures (RTL9210/RTL9210B, ASM2362, JMS583)
    - **Source url:** https://forums.anandtech.com/threads/stable-nvme-usb-adapter.2572973/post-41353234
    - **Community:** AnandTech forums (Dec 2024 - Mar 2025)
    - **What they built:** Daily-use and camera-recording NVMe USB enclosures.
    - **Problems:**
      - The RTL9210 bridge runs very hot; plastic enclosures (e.g. ORICO M2PV-C3) were called bad.
      - After a firmware flash, one M2PV-C3 slowed down every 3 s during copies.
      - An iDsonix RTL9210B adapter goes read-only after a while (unanswered).
      - A 4TB NVMe enclosure failed on several firmwares, suspected underpowered.
    - **Fixes:**
      - Use full-metal enclosures with a thermal pad to the lid.
      - Use known-good bridge firmware (e.g. 1.32.49 for the M2PV-C3; 'don't chase higher numbers if things work').
      - Budget about 7.5 W for USB-C bus power.
    - **Outcome:** Mixed: heat and firmware matter, and some read-only and slowdown cases remain unresolved.
  15.
    - **Product:** RAM-buffer / tmpfs capture for high-rate SDR recording (USRP community)
    - **Source url:** https://lists.ettus.com/empathy/thread/CKWAWM3RPO5XWQFGW7RF235G3HSQ3SJ4?page=3
    - **Community:** usrp-users mailing list (Ettus), 2014 thread
    - **What they built:** rx_samples_to_file / uhd_rx_cfile captures up to a 400 MB/s stream onto RAID0.
    - **Problems:**
      - Overruns ('O') at 400 MB/s even on a RAID0 benchmarked faster than that.
      - Page-cache writeback stalls the receive loop.
    - **Fixes:**
      - Diagnose by writing to /dev/null: if the 'O's vanish, the disk path is the bottleneck (Marcus Leech).
      - dirty_background_ratio=0 reduced but did not eliminate overruns (Peter Witkowski).
      - Decouple streaming from file I/O with a large buffer.
      - Marcus Mueller proposed a tmpfs + mkfifo + dd RAM FIFO and warned that swapping would defeat it.
      - Rob Kossler solved his overflows with a RAM filesystem, limiting capture length to its size.
    - **Outcome:** A RAM filesystem or RAM buffer with capture length bounded by RAM is the accepted working pattern. No universal disk-only fix was found.
  16.
    - **Product:** Long gap-free IQ capture tuning recipe (Ettus B206-mini, 4 Msps sc16, 1 h, 57.6 GB)
    - **Source url:** https://gist.github.com/Dygear/5be491d56d7e1e8fa45a7693bbf8f554
    - **Community:** GitHub gist
    - **What they built:** One-hour reference capture to NVMe on Fedora with UHD 4.9.
    - **Problems:**
      - A single 20-30 ms host stall causes a UHD overflow.
      - Btrfs copy-on-write metadata causes latency spikes.
    - **Fixes:**
      - Kernel arg irqaffinity to keep IRQs off capture cores.
      - Pin the capture process with SCHED_FIFO priority 50 and ionice -c1 -n0.
      - Use the performance governor and the latency-performance tuned profile.
      - Larger USB receive buffers (recv_frame_size=8000, num_recv_frames=256).
      - chattr +C on the capture directory.
      - Abort on the first overflow.
    - **Outcome:** Zero overflows over a 1 h, 57.6 GB capture. The recipe transfers to a Q6A recorder (CPU pinning on the A78 cores, IRQ isolation, ionice, no CoW filesystem).
  17.
    - **Product:** LimeSuiteNG limeTRX as the IQ recorder (LimeSDR family incl. Micro)
    - **Source url:** https://github.com/myriadrf/LimeSuiteNG/issues/405
    - **Community:** GitHub (myriadrf/LimeSuiteNG issues #405, #374)
    - **What they built:** CLI capture to SigMF files.
    - **Problems:**
      - limeTRX did not check whether the .sigmf-data/.sigmf-meta files opened. Writes to a failed stream were silently dropped and main still returned 0, so a capture to an unwritable or full path looked successful.
      - limeTRX writes only complex int16 (4 bytes/sample) to disk. The I12 link format does not carry over to files, and BIQ/packed output was only proposed as a separate converter (#374, Jul 2026: https://github.com/myriadrf/LimeSuiteNG/issues/374).
    - **Fixes:**
      - The fix was submitted in PR #376, a stability batch merged Aug 3, 2026, but issue #405 still shows open.
      - Maintainers suggest piping raw ci16 to an external compressor or converter.
    - **Outcome:** Use a LimeSuiteNG build from after Aug 3, 2026, and check that output files grow. Storing packed 12-bit or cs8 needs your own recorder or converter.
  18.
    - **Product:** SatDump baseband recording disk usage
    - **Source url:** https://github.com/SatDump/SatDump/issues/766
    - **Community:** GitHub (SatDump issues)
    - **What they built:** Unattended auto-track station decoding Meteor LRPT and NOAA APT on Raspberry Pi OS and Ubuntu.
    - **Problems:**
      - With 'record' enabled, each pass saved an 8-10 GB baseband; 128 GB filled after 10-15 passes.
    - **Fixes:**
      - Uncheck 'record' and keep 'live' if only products are needed.
      - Otherwise set IQ decimation (e.g. 10 at 2.4 Msps).
      - Baseband-type selection (cs8/ZIQ) was planned and is now available.
      - Nightly cron cleanup.
    - **Outcome:** Resolved by settings. Shows that automatic pass recording fills a 128 GB UFS quickly without decimation, cs8 or ZIQ.
  19.
    - **Product:** PCIe switch to share one M.2 link between NVMe and another PCIe device (Seeed ASM2806 / ASM1182E boards, Pi 5)
    - **Source url:** https://wiki.seeedstudio.com/raspberry_pi_5_uses_pcie_hat_dual_hat/
    - **Community:** Seeed wiki (vendor test); CNX Software comments (https://www.cnx-software.com/2025/01/21/pcie3-0-to-dual-m-2-hat-for-raspberry-pi-5-features-asmedia-asm2806-pcie-3-0-switch/)
    - **What they built:** Raspberry Pi 5 with an NVMe SSD plus a Hailo-8 accelerator behind one switch.
    - **Problems:**
      - SSD throughput while the Hailo-8 ran: 416 MB/s on Gen3 (ASM2806) vs 233 MB/s on Gen2 (ASM1182E).
      - Seeed warns that not every NVMe works.
      - CNX readers: about $90 landed in the EU, CN warehouse only; 'baseboard not HAT' so it does not fit standard cases.
    - **Fixes:**
      - Use the Gen3 ASM2806 version and Seeed-recommended SSDs.
    - **Outcome:** Works on a Pi 5 FFC host only. No one on the Radxa forum has tried a PCIe switch or a 2280 extension on the Q6A M.2 slot (forum search returned no results).
  20.
    - **Product:** Q6A OS image auto-suspend / random resets (relevant to unattended recording)
    - **Source url:** https://forum.radxa.com/t/q6a-rebooting-constantly/30452
    - **Community:** Radxa forum (Mar 2026)
    - **What they built:** Q6A on eMMC/SD with an Armbian minimal Noble image, 35 W USB-C PD supply.
    - **Problems:**
      - Instant resets after 3-30 min with no kernel panic.
      - willy noted the default image config suspends after prolonged idle, and the PSU may cut out during suspend.
    - **Fixes:**
      - Switching to the official radxa-dragon-q6a_noble_gnome_r2 image stopped the resets.
    - **Outcome:** Worked around; root cause unidentified. For a field recorder, disable suspend/idle sleep explicitly.
- **Common problems:**
  1.
    - **Problem:** 256GB Radxa UFS module (Kioxia THGJFGT1E45BAILB) freezes, stutters and reboots on the Q6A. The UFS link fails to exit H8 hibernate.
    - **Affected products:** Radxa UFS 3.1 256GB on Dragon Q6A, with Radxa 6.18.2 kernels before the fix, mainline 6.19.x (MicroOS), and any kernel without the quirk. Samsung-based 128GB modules were not affected in Radxa's tests.
    - **Frequency:** common
    - **Known fix:** Use a kernel with the Kioxia UFS_DEVICE_QUIRK_PA_TACTIVATE quirk (PA_TACTIVATE = 1 ms):
  - radxa/kernel PR #551 (linux-6.18.2, merged May 11, 2026)
  - also present in the radxa/kernel linux-7.0.11 branch (verified)
  - Armbian 26.05 and later
  Run 'apt-mark hold' on the kernel package so an apt upgrade does not revert to an unpatched kernel. Interim workaround: a keep-alive loop writing a file every 100 ms. The quirk is NOT in mainline Linux (7.3-rc7), so distro or mainline kernels need a patch.
    - **Fix sources:**
      - https://forum.radxa.com/t/ufs-random-reboots/30630?page=2
      - https://forum.radxa.com/t/ufs-random-reboots/30630?page=3
      - https://github.com/radxa/kernel/pull/551
      - https://forum.radxa.com/t/radxa-poe-hat-overlay-on-microos/30704
  2.
    - **Problem:** Every published UFS write figure on the Q6A is a short burst inside the WriteBooster SLC cache. None is a sustained figure.
    - **Affected products:** All Radxa UFS modules on the Q6A: Radxa docs dd 388/557 MB/s; forum fio 473-499 MB/s from 2 GiB / 4.5 s runs.
    - **Frequency:** common
    - **Known fix:** No measured fix. Data from the same SoC (MitySOM-QC6490, 256 GB UFS 3.1, 4 GB WriteBooster buffer) shows writes ranging from about 300 to 1500 MiB/s depending on the cache state. Measure your own module:
  - WriteBooster size: wb_shared_alloc_units x 512 x allocation_unit_size x segment_size, from the UFS sysfs.
  - Sustained rate: a long fio direct sequential write (e.g. 100 GB, logged per second).
    - **Fix sources:**
      - https://forum.radxa.com/t/ufs-random-reboots/30630?page=2
      - https://git.criticallink.com/redmine/projects/mitysom_qc6490/wiki/UFS
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
  3.
    - **Problem:** Boot-firmware regressions and boot-order traps with UFS fitted: a failed UFS boot blocks SD/USB recovery, and some SPI updates brick boards.
    - **Affected products:** Q6A SPI firmware 250929 and early units; scattered reports on later firmware (2025-11-13, 260120).
    - **Frequency:** occasional
    - **Known fix:** - Update to firmware 251013 or newer (boot order USB > SD > NVMe > eMMC > UFS) with edl-ng.
  - If a UFS boot hangs, remove the UFS module to boot from SD.
  - Keep a microSD rescue image and a USB-A data cable for EDL.
  - Use RadxaOS r1 or newer, since v6.17-kernel images can't update the SPI flash after 260120.
    - **Fix sources:**
      - https://forum.radxa.com/t/radxa-dragon-q6a-firmware-snapshot/28886
      - https://forum.radxa.com/t/upcoming-radxa-dragon-q6a/26723?page=2
  4.
    - **Problem:** Flashing UFS: the Radxa USB transfer module (UFS reader) is not detected by the PC.
    - **Affected products:** Radxa UFS USB reader + 128GB UFS 3.1 module
    - **Frequency:** rare
    - **Known fix:** Flash in place over EDL with Armbian Imager 2.0, which writes Q6A images directly to UFS (set the UEFI boot order afterwards). Or boot the Q6A from SD/USB and write the UFS on the board.
    - **Fix sources:**
      - https://forum.radxa.com/t/load-systen-on-an-ufs-3-1-module-for-dragon-q6a/31102
      - https://forum.armbian.com/topic/61701-news-from-armbian-sbc-storage/
  5.
    - **Problem:** The UFS module runs hot (about 60 C) because it sits next to the SoC. Its standard rating is 0-70 C.
    - **Affected products:** Radxa UFS modules on Q6A
    - **Frequency:** occasional
    - **Known fix:** Active cooling: a heatsink case plus fans, or a heatsink and fan with a 36 W supply, kept the module at or below about 60 C. In a sealed 3D-printed case, add airflow over the module or a thermal pad to the case.
    - **Fix sources:**
      - https://forum.radxa.com/t/dragon-q6a-vpu-firmware-loading/31226
      - https://forum.radxa.com/t/ufs-random-reboots/30630
  6.
    - **Problem:** Third-party eMMC modules short the Q6A's UFS power rails.
    - **Affected products:** Orange Pi eMMC modules on Q6A and A7S
    - **Frequency:** occasional
    - **Known fix:** Use only genuine Radxa RA022 modules. Radxa says removing the UFS-side connector from the Orange Pi module prevents the short.
    - **Fix sources:**
      - https://forum.radxa.com/t/radxa-a7s-compatibility-with-emmc-module/30638
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
  7.
    - **Problem:** Disk write stalls (page-cache writeback, IRQ and scheduler jitter) cause SDR overflows or dropped samples even when average disk bandwidth is enough.
    - **Affected products:** Any SDR to storage recorder (USRP reports; applies to LimeSDR Micro to UFS/USB SSD on Q6A)
    - **Frequency:** common
    - **Known fix:** - Test by writing to /dev/null first.
  - Decouple RX from file I/O with a large RAM ring buffer, or a tmpfs capture whose length is bounded by RAM.
  - Pin the RX thread with SCHED_FIFO and set ionice -c1.
  - Use the performance governor and keep IRQs off the capture cores (irqaffinity).
  - Use bigger driver buffers.
  - Avoid CoW filesystems (or chattr +C).
  - Tune the dirty ratios.
  - Make sure tmpfs cannot swap.
    - **Fix sources:**
      - https://lists.ettus.com/empathy/thread/CKWAWM3RPO5XWQFGW7RF235G3HSQ3SJ4?page=3
      - https://gist.github.com/Dygear/5be491d56d7e1e8fa45a7693bbf8f554
  8.
    - **Problem:** Recorder software pitfalls:
  - limeTRX silently ignored output-file open failures.
  - limeTRX writes only ci16 (4 B/sample); there is no packed 12-bit or cs8 file output.
  - SatDump auto-recording fills disks (8-10 GB per pass).
    - **Affected products:** LimeSuiteNG limeTRX (LimeSDR family incl. Micro); SatDump
    - **Frequency:** occasional
    - **Known fix:** - Use LimeSuiteNG with PR #376 (merged Aug 3, 2026).
  - Pipe ci16 to your own packer or compressor for 12-bit or 8-bit storage.
  - In SatDump, use decimation, the cs8/ZIQ baseband types, or live-only mode, plus scheduled cleanup.
    - **Fix sources:**
      - https://github.com/myriadrf/LimeSuiteNG/issues/405
      - https://github.com/myriadrf/LimeSuiteNG/issues/374
      - https://github.com/SatDump/SatDump/issues/766
  9.
    - **Problem:** USB-NVMe bridge heat and firmware problems (slowdowns, read-only mode), plus bus-power limits.
    - **Affected products:** RTL9210/RTL9210B, ASM2362, JMS583 enclosures (e.g. ORICO M2PV-C3, iDsonix)
    - **Frequency:** occasional
    - **Known fix:** - Use a full-metal enclosure with a thermal pad.
  - Run known-good bridge firmware rather than the newest.
  - Budget about 7.5 W for USB bus power.
  - A Samsung T7/T7 Shield avoids the DIY-enclosure variance.
    - **Fix sources:**
      - https://forums.anandtech.com/threads/stable-nvme-usb-adapter.2572973/post-41353234
  10.
    - **Problem:** microSD is slow for wideband IQ (61 MB/s write) and fails in the field: bad sectors after 3-4 months; Etcher-induced corrupt flashes.
    - **Affected products:** microSD on Dragon Q6A
    - **Frequency:** occasional
    - **Known fix:** Use microSD only as rescue or boot media. Flash an extracted .img, or enable Etcher's trim option.
    - **Fix sources:**
      - https://github.com/geerlingguy/sbc-reviews/issues/85
      - https://forum.radxa.com/t/radxa-dragon-q6a-was-running-stable-for-3-4-months-then-failed-and-would-no-longer-boot/31509
  11.
    - **Problem:** Images that auto-suspend after idle, plus unexplained resets on a minimal image, could kill unattended recordings.
    - **Affected products:** Q6A Armbian minimal / default image configs
    - **Frequency:** rare
    - **Known fix:** Use the official noble_gnome_r2 image, or disable suspend explicitly (systemd sleep targets / logind idle actions).
    - **Fix sources:**
      - https://forum.radxa.com/t/q6a-rebooting-constantly/30452
- **Unresolved problems:**
  1.
    - **Problem:** No sustained (post-WriteBooster) write measurement exists for any Radxa UFS module on the Q6A, and the WriteBooster buffer size of the Samsung 128GB and Kioxia 256GB modules is unpublished.
    - **Why it matters for us:** 56 MHz cs16 needs 245.76 MB/s with no gaps. Same-SoC data suggests a floor of about 300 MiB/s, which is only about 20% headroom. Radxa's own ROCK 4D figure is about 250 MB/s. Captures longer than the cache, plus concurrent OS writes, could drop samples.
    - **Evidence:** The longest posted write test was 2 GiB in 4.5 s (datum, forum thread 30630). MitySOM-QC6490 shows 300-1500 MiB/s depending on cache state. No other long-write data was found.
  2.
    - **Problem:** The Kioxia fix is not in mainline Linux, and nothing documents which chip a given module SKU carries. Nobody answered whether 128GB is always Samsung and 256GB always Kioxia; the 512GB chip is unknown.
    - **Why it matters for us:** The 256GB module is the findings' recommended pick. On a generic or custom Ubuntu kernel without the quirk, it can stutter, freeze or reboot mid-capture. Buying blind risks getting the problematic chip, and a future kernel switch could reintroduce the bug.
    - **Evidence:** Mainline master (7.3-rc7) ufs-qcom.c and ufshcd.c lack THGJFGT1E45BAILB (checked). The quirk is in radxa/kernel linux-6.18.2 and linux-7.0.11. pamvdam's SKU question went unanswered in thread 30630.
  3.
    - **Problem:** The Kioxia fix's long-term stability is lightly tested: reports cover 1-2 days to about 9 days of uptime, mostly at light load.
    - **Why it matters for us:** Field recording means long bursts of heavy writes with idle gaps between them. Idle gaps are exactly the H8 enter/exit pattern that triggered the bug.
    - **Evidence:** Thread 30630 page 2-3 (May 9-28, 2026). No later follow-ups found.
  4.
    - **Problem:** No endurance (TBW) rating exists for Radxa UFS modules, and no community wear data.
    - **Why it matters for us:** At 246 MB/s the module absorbs about 885 GB/hour, so a 256GB module could see several full drive writes per hour of wideband capture. Wear-out could kill the boot drive. It can only be monitored via health_descriptor life_time_estimation_a/b.
    - **Evidence:** No TBW on the Radxa product brief or docs. FriendlyELEC's wiki only explains how to read the health descriptor. The Critical Link wiki gives only a generic P/E-based formula.
  5.
    - **Problem:** Only one USB3 storage throughput datapoint exists on the Q6A (about 395 MB/s fio write, adapter unnamed, no parameters, no read figure, no sustained run).
    - **Why it matters for us:** The USB SSD is the proposed primary wideband capture target. Its real sustained rate, UAS stability over long captures, and behaviour with HDMI active on the shared QMP combo PHY are unverified.
    - **Evidence:** SmartHomeCircle review (Jan 2026). A kernel patch confirms USB3 at 5 Gbps alongside HDMI but gives no throughput. Forum searches for Q6A USB SSD / UAS / USB3 found no reports.
  6.
    - **Problem:** Nobody has reported concurrent load: a PCIe SDR stream (184-246 MB/s) plus USB3 or UFS recording plus NPU inference on the Q6A.
    - **Why it matters for us:** Interrupt load, memory bandwidth, thermals and power draw under combined load decide whether 56 MHz recording is gap-free. The SoC hits 90+ C and throttles without a fan, and reached 105 C and shut down bare.
    - **Evidence:** No Radxa forum, GitHub or blog reports found. Thermal data from willy (thread 26723) and SmartHomeCircle.
  7.
    - **Problem:** Cold-weather operation is unverified: the UFS standard grade is rated 0-70 C and the T7 Shield 0-60 C, and no one reports below-zero use.
    - **Why it matters for us:** Ukrainian winter passes are often well below 0 C at cold start. Write errors or failure to enumerate at low temperature would lose captures. The industrial UFS SKU (-25 to +85 C) has unclear availability and SKU mapping.
    - **Evidence:** Radxa UFS brief (optional industrial grade, -25 to +85 C). Shuttermuse lists the T7 Shield at 0-60 C. No community cold-start reports found.
  8.
    - **Problem:** Sharing the Q6A M.2 slot through a PCIe switch, or using a 2230-to-2280 extension, is untested on the Q6A.
    - **Why it matters for us:** The LimeSDR Micro itself depends on an extension in the 2230 slot. A switch for NVMe adds unknown enumeration, power and signal-integrity risk, and UEFI already fails to enumerate some NVMe drives.
    - **Evidence:** Radxa forum searches for 'Q6A pcie switch' returned nothing. The 'AI acceleration' thread only says 2280 cards need an 'awkward extension cable', with no test. Thread 31195 covers UEFI non-enumeration on 260120. Thread 30807 covers an M.2 slot dying.
  9.
    - **Problem:** No community report of a RAM ring-buffer recorder at 160 Msps (640 MB/s) on the Q6A or similar ARM boards.
    - **Why it matters for us:** The burst strategy depends on the Q6A sustaining DMA from the PCIe SDR plus a memcpy into a ring buffer at 640 MB/s, plus a concurrent drain, without overflow. Only x86 USRP experience exists, and one 2024 tmpfs attempt still overran.
    - **Evidence:** usrp-users threads (2014 RAM-filesystem success; 2024 tmpfs overruns, unresolved). No ARM/Q6A data.
  10.
    - **Problem:** Mechanical retention of the UFS module: it is held by two B2B connectors, the second for mounting only, and no handheld vibration or drop reports exist.
    - **Why it matters for us:** A portable device that gets carried and bumped could unseat the boot and recording module.
    - **Evidence:** Radxa UFS module brief rev 1.2 (Connector 2 'reserved NC for mounting only'). No community reports either way.
- **Communities checked:**
  - Radxa forum (forum.radxa.com): search.json queries for UFS Q6A, UFS write speed, Q6A USB SSD, Q6A USB3, Q6A uas, Q6A usb disconnect, Q6A power supply reboot, Q6A pcie switch, Q6A M.2 extension, and UFS order:latest. Threads read: 30630 (3 pages), 30704, 31102, 26723 (pages 1-3), 28886, 30638, 30807, 31195, 31226, 31509, 30452, 30500.
  - GitHub: geerlingguy/sbc-reviews #85; radxa/kernel (PR #551, issue search, linux-7.0.11 branch source checked); torvalds/linux master ufs-qcom.c and ufshcd.c (checked for the quirk); SatDump issues (#766, #703, searches); myriadrf/LimeSuiteNG issues (#405, #374, limeTRX search); AlexandreRouma/SDRPlusPlus issues (recorder searches, nothing relevant); Dygear gist.
  - MyriadRF / Lime discourse (discourse.myriadrf.org): search.json for 'record to disk' and 'limesdr micro record'; topic 5776.
  - SatNOGS community (community.libre.space): searches for iq recording ssd and sd card corruption; nothing storage-specific for this build.
  - Ettus usrp-users mailing list (lists.ettus.com): rx_samples_to_file overrun / RAM buffer thread.
  - Armbian forum: search for Q6A UFS; Armbian 'SBC storage' newsletter (Imager 2.0 EDL flashing).
  - CNX Software: Q6A launch article comments; ASM2806 dual M.2 HAT article comments.
  - AnandTech forums: USB-C slowdown thread (T7/T9); stable NVMe USB adapter thread.
  - freedesktop DRM / kernel patch list (Q6A mainline USB3 + HDMI series).
  - Vendor and engineering wikis: Critical Link MitySOM-QC6490 UFS wiki, FriendlyELEC UFS wiki, Seeed wiki (via search), Radxa docs and UFS product brief.
  - Review sites: SmartHomeCircle (Q6A), ssd-tester.com (T7, T7 Shield), Shuttermuse (T7 Shield), Jeff Geerling pipci (HatDrive Dual).
  - Unreachable or blocked: Reddit (WebFetch and WebSearch both refused reddit.com, so r/RTLSDR, r/sdr, r/radxa and r/SBCs were not checked); Samsung US Community (HTTP 403); Core Electronics (403); Elektor (429); Tom's Hardware T7 Shield review (content truncated).
  - Not checked for lack of storage-relevant content or budget: BATC forum, AMSAT lists, EEVblog, Hackaday.io, StackExchange, Raspberry Pi forums (a site-filtered search returned no hits), Ubuntu Discourse, Qualcomm developer forums.
- **Recommendation impact:** Community evidence changes four things about the storage plan.
  
  1. Which UFS module. The 256GB Kioxia module, which has the best published Q6A write figure, is also the module with a well-documented stutter/freeze/reboot bug on the Q6A.
  - The fix (a PA_TACTIVATE quirk) exists only in Radxa's and Armbian's kernels (radxa/kernel linux-6.18.2 after PR #551, and linux-7.0.11). It is not in mainline.
  - So either buy the Samsung-based 128GB module (no quirk needed, Radxa found no faults), or take the 256GB/512GB only if you will stay on the Radxa or Armbian vendor kernel. In that case pin the kernel (apt-mark hold) and check dmesg for ufshcd errors after every update.
  - Ask the seller which flash chip a module carries; Radxa does not document the SKU-to-chip mapping.
  
  2. Usable UFS write speed is still unknown. Every Q6A write figure (388/473/499/557 MB/s) comes from runs of a few seconds inside the WriteBooster cache. A same-SoC module suggests about 300 MiB/s after the cache fills.
  - Before relying on UFS for 56 MHz cs16, measure the WriteBooster size from sysfs and run a long fio direct write (for example 100 GB, logged per second).
  - Until then, plan wideband captures as cs8 or packed 12-bit on UFS. Note that limeTRX only writes ci16, so you would need your own packer.
  - Use the USB SSD for long cs16 captures.
  
  3. The USB SSD role stays, but rests on one data point (about 395 MB/s, unnamed adapter). Prefer:
  - a Samsung T7 Shield or T7 (sustained 879 / 614 MB/s on a PC, so the ~395 MB/s Q6A USB 3.1 Gen1 port is the cap), or a metal-bodied RTL9210/ASM2362 enclosure with known-good firmware;
  - keeping it warm, since the T7 Shield is rated 0-60 C;
  - a power budget of about 7.5 W.
  Validate with a long capture before trusting it.
  
  4. The RAM ring buffer is endorsed by the community pattern (USRP users who solved overruns with RAM filesystems or buffers). Build the recorder as:
  - RX thread pinned with SCHED_FIFO on an A78 core, IRQs moved off that core;
  - ionice -c1 and the performance governor;
  - capture length bounded by RAM; tmpfs only if swap is off; no CoW filesystem;
  - /dev/null tested first;
  - auto-suspend disabled.
  
  Drop the PCIe-switch idea: no Q6A user has tried one, and the M.2 slot and UEFI enumeration already have failure reports.
  
  Operational additions:
  - Update the SPI firmware to 251013 or newer (preferably 260120) before fitting UFS.
  - Keep a microSD rescue card and know that pulling the UFS lets the board boot from SD.
  - Flash UFS via Armbian Imager EDL if the Radxa USB reader misbehaves.
  - Give the UFS module airflow; it reaches about 60 C even with fans.
  - Monitor UFS wear through health_descriptor, since no TBW is published.
  
  Overall confidence that the recommended three-tier setup (UFS for OS and passes, USB SSD for wideband, RAM for bursts) works stays medium. The changes are the module choice and kernel requirement for UFS, and the need to verify sustained write rates before relying on UFS for 56 MHz cs16.

## Власні виправлення (`fixes`)

_Run `wf_3e735695-e00`_

- **Component:** Storage (raw IQ recording + OS) for the Radxa Dragon Q6A handheld satellite receiver: Radxa UFS 3.1 module, USB 3 SSD, RAM burst buffer
- **Fixes:**
  1.
    - **Problem:** No sustained (post-WriteBooster) write figure exists for any Radxa UFS module on the Q6A, and the WriteBooster (WB) buffer size of the Samsung 128GB and Kioxia 256GB modules is unpublished. 56 MHz cs16 needs 245.76 MB/s with no gaps.
    - **Proposed fix:** Read the module's WB size from sysfs and measure the post-cache floor in about an hour. Separately, design the recorder so the UFS only has to sustain the average rate:
  - a RAM FIFO in front of the disk;
  - lossless 12-bit packing (184.3 MB/s instead of 245.76 MB/s);
  - the UFS link pinned at max gear during captures;
  - WB flushing between passes;
  - the module kept under ~50% full.
  
  What the code shows about the Q6A's Qualcomm driver:
  - WB is switched together with clock scaling (UFSHCD_CAP_WB_WITH_CLK_SCALING).
  - Writing the wb_on sysfs node returns EOPNOTSUPP.
  - Each gear-scaling event quiesces the I/O queue, which is a source of write stalls.
  
  For scale: Radxa's own Q6A UFS provisioning XML (Android) configures a 4 GiB shared WB with preserve-user-space=1. A 4 GiB cache lasts only about 17.5 s at 245.76 MB/s.
  
  It is also possible that Linux-shipped modules have no WB configured at all. In that case Radxa's 388/557 MB/s figures are already the true TLC speeds. Sysfs shows which case applies.
    - **Steps:**
      - Find the UFS host node: U=$(ls -d /sys/bus/platform/devices/1d84000.ufs*) (Radxa kernels name it 1d84000.ufshc; mainline uses 1d84000.ufs).
      - Dump the WB configuration: for f in capabilities/write_booster device_descriptor/wb_type device_descriptor/wb_presv_us_en device_descriptor/wb_shared_alloc_units geometry_descriptor/wb_max_alloc_units geometry_descriptor/wb_buff_cap_adj geometry_descriptor/allocation_unit_size geometry_descriptor/segment_size attributes/wb_cur_buf attributes/wb_avail_buf attributes/wb_flush_status wb_on enable_wb_buf_flush clkscale_enable; do echo "$f=$(cat $U/$f)"; done
      - Compute the WB size as wb_shared_alloc_units x allocation_unit_size x segment_size x 512 bytes (Critical Link's QCS6490 formula). If wb_shared_alloc_units is 0, no WB is configured and the write speed is flat. wb_avail_buf is in 10% steps (0x0A = full).
      - Pin the link at max gear for tests and captures: echo 0 | sudo tee $U/clkscale_enable. This also leaves WB permanently enabled on Qualcomm.
      - Fill test: on an ext4 data partition, size the file to about 70% of free space and run sudo fio --name=sus --filename=/data/fio.bin --size=80G --rw=write --bs=1M --ioengine=libaio --iodepth=16 --direct=1 --write_bw_log=/root/ufs --log_avg_msec=1000 --lat_percentiles=1. In parallel, log the cache: while sleep 1; do echo $(date +%s),$(cat $U/attributes/wb_avail_buf); done > /root/wb.csv. Bytes written when wb_avail_buf reaches 0 is the effective cache size; the plateau after that is the TLC floor.
      - Optional fast floor test (keep clkscale disabled first): build ufs-utils (github.com/westerndigitalcorporation/ufs-utils), clear fWriteBoosterEn with sudo ufs-utils fl -t 14 -c -p /dev/bsg/ufs-bsg0, run fio for 60 s, then restore with -e or reboot. This needs CONFIG_SCSI_UFS_BSG (check that ls /dev/bsg shows ufs-bsg0).
      - Between passes, let the cache drain without hibernate: echo 1 | sudo tee $U/enable_wb_buf_flush. Keep the module under 50% full and run sudo fstrim -av after deleting captures. In preserve-user-space mode the cache shrinks as the drive fills, and the kernel logs 'dCurWBBuf: 0 WB disabled'.
      - Cut the data rate losslessly. The LMS7002M is a 12-bit ADC. LimeSuiteNG's host-side I12 is still stored in int16 (types.h), so it saves no bytes. Pack each I/Q pair of 12-bit values into 3 bytes in the recorder: 61.44 Msps becomes 184.32 MB/s instead of 245.76 MB/s. Unpack to cs16 offline for SatDump, or use cs8 (122.9 MB/s) for surveys.
      - Put an mlocked RAM FIFO of at least 2 GiB in front of every wideband write (see the RAM ring-buffer fix). Size it as at least 2 x data rate x the worst stall seen in the fio p99.99 latency.
      - Decision rule: record 56 MHz cs16 to UFS only if the 10-s moving minimum is at least 295 MB/s (1.2 x 245.76). Record packed-12 to UFS only if it is at least 221 MB/s. Otherwise send wideband to the USB SSD and keep UFS for narrowband passes (HRPT 6 Msps cs16 = 24 MB/s).
    - **How to verify:** 1. In the fio bandwidth log, the 1-s samples are in KiB/s: sort -t, -k2 -n /root/ufs_bw.1.log | head gives the worst seconds.
  2. Plot /root/wb.csv against cumulative bytes written to find where the cache runs out.
  3. Run a real 10-minute capture through the FIFO, e.g. limeConfig --initialize --samplerate=61.44e6 --rxen=1 --rxlo=1.7e9, then limeTRX --output=/data/iq/t --time=600000.
  4. Check t.sigmf-meta. limeTRX adds a 'captures' entry at every timestamp discontinuity, so exactly one entry means no samples were dropped.
  5. Repeat with the module about 60% full to confirm the preserve-user-space effect.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/torvalds/linux/blob/master/drivers/ufs/host/ufs-qcom.c
      - https://github.com/torvalds/linux/blob/master/drivers/ufs/core/ufshcd.c
      - https://github.com/torvalds/linux/blob/master/drivers/ufs/core/ufs-sysfs.c
      - https://github.com/torvalds/linux/blob/master/Documentation/ABI/testing/sysfs-driver-ufs
      - https://dl.radxa.com/q6a/images/android/provision_ufs31.xml
      - https://ftp.criticallink.com/redmine/projects/mitysom_qc6490/wiki/UFS
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
      - https://forum.radxa.com/t/30630?page=2
      - https://github.com/myriadrf/LimeSuiteNG/blob/develop/cli/limeTRX.cpp
      - https://github.com/myriadrf/LimeSuiteNG/blob/develop/src/include/limesuiteng/types.h
      - https://github.com/westerndigitalcorporation/ufs-utils
  2.
    - **Problem:** The Kioxia fix is not in mainline Linux, and nothing documents which chip a given module SKU carries. The 128GB/Samsung and 256GB/Kioxia pairing is not guaranteed, and the 512GB chip is unknown.
    - **Proposed fix:** Identify the chip on arrival. Run only kernels that contain the quirk, pin them, and add a boot-time self-check that reads back the setting the quirk applies.
  
  The fix itself (Radxa PR #551) is three lines in ufs_qcom_dev_fixups: Kioxia/Toshiba (0x198) model THGJFGT1E45BAILB gets UFS_DEVICE_QUIRK_PA_TACTIVATE. In ufshcd_tune_unipro_params that sets the host PA_TActivate (MIB 0x15A8) to 10, i.e. 1 ms.
  
  Verified in source:
  - Present in radxa/kernel branches linux-6.18.2 and linux-7.0.11.
  - Absent from mainline 7.3-rc7, both in ufs-qcom.c and in the generic ufs_fixups table.
  
  Because the effect is a readable link attribute, the self-check is deterministic.
    - **Steps:**
      - Before buying: ask Arace, Allnet or the Radxa AliExpress store for a photo of the chip marking (KIOXIA THGJFGT1E45BAILB or SAMSUNG KLUDG4UHDC-B0E1). Radxa staff said they are not certain which brand future batches will use.
      - On arrival, boot Radxa OS from microSD with the module fitted, then check the chip: cat /sys/class/scsi_device/*/device/vendor /sys/class/scsi_device/*/device/model; cat $U/device_descriptor/manufacturer_id. 0x0198 is Kioxia/Toshiba and 0x01CE is Samsung (ufs_quirks.h).
      - Use Radxa OS r2 (Ubuntu noble userspace) with a Radxa kernel built from linux-6.18.2 HEAD or linux-7.0.11, or Armbian 26.05 or later (the maintainer said the fix ships there; not verified). Do not use Canonical generic or mainline kernels with a Kioxia module.
      - Pin the kernel, because a forum user's apt upgrade replaced the fixed kernel with stock 6.18.2-4-qcom: sudo apt-mark hold linux-image-$(uname -r), plus the matching linux-headers and meta packages.
      - Boot self-check (systemd oneshot): sudo ufs-utils uic -t 1 -r -i 0x15a8 -p /dev/bsg/ufs-bsg0. The local value should read 0x0000000a on a Kioxia module. If it does not, apply the no-hibernate field profile from the next fix, show a warning on screen, and make the recorder refuse the UFS target.
      - Fallback for a kernel without the quirk, option (a): apply the PR #551 hunk and rebuild. If CONFIG_SCSI_UFS_QCOM=m, rebuilding only drivers/ufs/host against the matching source tree is enough. Then run update-initramfs -u, because the root filesystem is on UFS.
      - Fallback option (b): use the no-hibernate sysfs profile from the next fix. This is the equivalent of the keep-alive workaround that ran 24.5 h without errors.
      - Fallback option (c), experimental: write the value at boot with sudo ufs-utils uic -t 1 -w 0xa -i 0x15a8 --local -p /dev/bsg/ufs-bsg0. It is lost after any host reset or link re-init, so re-check it periodically.
      - Get it upstream: send the 3-line PR #551 patch to linux-scsi (the ufs-qcom maintainers), or ask Radxa to. Until then, treat every non-Radxa/non-Armbian kernel as unfixed.
    - **How to verify:** 1. journalctl -k | grep -cE 'ufshcd.*(OCS invalid|pa_err|dl_err|timed-out|abort)' returns 0.
  2. All counters in sudo cat /sys/kernel/debug/ufshcd/*/stats (PA/DL errors, host resets, aborts) stay at 0 across the 72 h soak in the next fix.
  3. The ufs-utils readback shows 0xa after every boot and after every kernel update.
    - **Confidence:** high
    - **Sources:**
      - https://patch-diff.githubusercontent.com/raw/radxa/kernel/pull/551.diff
      - https://github.com/radxa/kernel/blob/linux-7.0.11/drivers/ufs/host/ufs-qcom.c
      - https://github.com/radxa/kernel/blob/linux-6.18.2/drivers/ufs/host/ufs-qcom.c
      - https://github.com/torvalds/linux/blob/master/drivers/ufs/core/ufshcd.c
      - https://github.com/torvalds/linux/blob/master/include/ufs/ufs_quirks.h
      - https://forum.radxa.com/t/30630
      - https://forum.radxa.com/t/30630?page=2
      - https://forum.radxa.com/t/30630?page=3
      - https://github.com/westerndigitalcorporation/ufs-utils
  3.
    - **Problem:** The Kioxia fix's long-term stability is lightly tested. Reports cover about 10 h to about 1 day; the earlier "9 days" reading was most likely "up 9:51", i.e. 9 h 51 min one day after install. Field recording is exactly the burst-plus-idle pattern that triggers hibernate (H8) enter/exit.
    - **Proposed fix:** Remove H8 entirely during a field session with a sysfs "field profile", independent of the quirk.
  
  On Qualcomm, clock gating enters H8 after clkgate_delay_ms (150 ms by default) because of UFSHCD_CAP_HIBERN8_WITH_CLK_GATING. That explains the forum results: disabling auto_hibern8 alone did not help, while a 100 ms keep-alive write did.
  
  Also:
  - Prove stability with a 72 h soak that reproduces the field pattern.
  - Have the recorder fail over to the USB SSD on any UFS error.
    - **Steps:**
      - Field profile (run as root at session start; reboot or revert at the end):
  echo 0 > $U/clkgate_enable
  echo 0 > $U/auto_hibern8
  echo 0 > $U/rpm_lvl   (device active, link active)
  echo 0 > $U/clkscale_enable
  echo 1 > $U/enable_wb_buf_flush   (the cache still flushes when idle, without H8)
      - Measure what the profile costs on battery with an inline USB-C PD meter, idle with and without it. No figure is published; expect tens to a few hundred mW (estimate).
      - Soak test A (quirk kernel, default power management) for 72 h. Loop: sudo fio --name=burst --filename=/data/soak.bin --size=20G --rw=write --bs=1M --direct=1 --rate=250m --runtime=600 --time_based, then sleep a random 120-1200 s. Log the error grep from the previous fix plus /sys/kernel/debug/ufshcd/*/stats every hour.
      - Soak test B: the same 72 h loop with the field profile applied.
      - In the recorder: on EIO, a write latency over 2 s, or a new ufshcd error line, switch the write target to the USB SSD. The RAM FIFO holds the samples during the switch.
      - Keep a microSD rescue image, but never use microSD as primary storage: forum thread 31509 reports A2 cards corrupting after months on a Q6A.
    - **How to verify:** Both soaks finish 72 h with:
  - uptime not reset;
  - no stutter (fio clat max under 1 s);
  - zero UFS error lines and zero debugfs error counters.
  
  If A fails and B passes, make the field profile mandatory. If both pass, use the profile only for long sessions.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/torvalds/linux/blob/master/drivers/ufs/core/ufshcd.c
      - https://github.com/torvalds/linux/blob/master/drivers/ufs/host/ufs-qcom.c
      - https://github.com/torvalds/linux/blob/master/Documentation/ABI/testing/sysfs-driver-ufs
      - https://github.com/torvalds/linux/blob/master/drivers/ufs/core/ufs-debugfs.c
      - https://forum.radxa.com/t/30630
      - https://forum.radxa.com/t/30630?page=2
      - https://forum.radxa.com/t/31509
  4.
    - **Problem:** No endurance (TBW) rating exists for Radxa UFS modules, and there is no community wear data. At 245.76 MB/s the module absorbs about 885 GB per hour.
    - **Proposed fix:** 1. Measure wear yourself, and derive a TBW from the device's own wear steps.
  2. Keep long wideband captures off the boot module.
  3. Use the NPU classifier as a write gate: the RAM ring holds everything, and only segments containing a detected signal are committed to disk. This is a double duty for the NPU.
  4. Optional and experimental: reprovision the module with a dedicated enhanced-memory (pseudo-SLC) capture LUN. Radxa's own Q6A provisioning XML uses bMemoryType=3 for its boot LUNs with bConfigDescrLock=0, which suggests these modules accept such a layout.
  
  Prior estimate (an assumption, not a spec): TBW ≈ capacity x P/E / WAF (Critical Link formula). With 1,000-3,000 P/E for TLC and WAF about 1.1 for large sequential files, a 256 GB module gives about 230-700 TB. That is about 260-790 h of continuous 56 MHz cs16 written to UFS.
    - **Steps:**
      - Wear log, run at boot and after every capture: echo "$(date +%s),$(cat $U/health_descriptor/life_time_estimation_a),$(cat $U/health_descriptor/life_time_estimation_b),$(cat $U/health_descriptor/eol_info),$(cat $U/attributes/wb_life_time_est),$(cat $U/critical_health),$(awk '{print $7*512}' /sys/block/sda/stat)" >> /var/log/ufs_wear.csv. Field 7 of /sys/block/sda/stat counts sectors written since boot, so also keep a running total across boots.
      - Derive TBW empirically: when life_time_estimation_a or _b steps from 0x01 to 0x02 (10% used), TBW ≈ 10 x the cumulative host bytes written at that moment.
      - Set alarms: life_time_estimation at 0x08 or above, eol_info at 0x02 or above (pre-EOL warning: 80% of reserved blocks used), or critical_health above 0. On an alarm, move captures off UFS and order a replacement module.
      - Route data: put wideband (56 MHz) captures on the replaceable USB SSD and keep narrowband passes on UFS. A 15-minute HRPT pass at 6 Msps cs16 is about 21.6 GB.
      - Cut background writes: mount with noatime; set journald Storage=volatile during sessions.
      - For the USB SSD, prefer a retail TLC 2230/2242 drive that publishes a TBW figure, so wear is budgetable (check the vendor datasheet; not verified here).
      - Optional pSLC LUN (experimental; wipes the module; can void the warranty): (1) read $U/geometry_descriptor/memory_types, enh1_memory_max_alloc_units and enh1_memory_capacity_adjustment_factor (0x300 means 3:1, i.e. SLC on TLC), and confirm $U/attributes/configuration_descriptor_lock is 0x00. (2) Write a provisioning XML based on Radxa's provision_ufs31.xml: LU0 = OS (TLC, rest of device), LU1 = capture LUN (bMemoryType=3, e.g. 32 GiB), drop the Android-only LUNs, and keep bConfigDescrLock=0. (3) Put the board in EDL mode and connect the USB 3.1 Type-A port to a PC with an A-to-A cable. (4) Run edl-ng --loader <firehose from Radxa flat_build> --memory UFS provision my.xml (syntax inferred from the edl-ng README). (5) Reflash the Radxa OS 4096-byte-sector image to LU0.
    - **How to verify:** 1. The CSV grows on each boot and capture, and its counters only increase.
  2. For the pSLC option:
     - the capture LUN's unit_descriptor/lun_memory_type reads 0x03;
     - its capacity is as provisioned;
     - a fio sustained write to it shows no cache cliff over the LUN's full size.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/torvalds/linux/blob/master/Documentation/ABI/testing/sysfs-driver-ufs
      - https://github.com/torvalds/linux/blob/master/drivers/ufs/core/ufs-sysfs.c
      - https://ftp.criticallink.com/redmine/projects/mitysom_qc6490/wiki/UFS
      - https://dl.radxa.com/q6a/images/android/provision_ufs31.xml
      - https://docs.radxa.com/en/dragon/q6a/download
      - https://github.com/strongtz/edl-ng
  5.
    - **Problem:** Only one USB 3 storage data point exists on the Q6A: about 395 MB/s fio write with an unnamed adapter, no parameters, no read figure and no sustained run. UAS stability over long captures and the interaction with HDMI on the shared QMP combo PHY are unverified.
    - **Proposed fix:** The bandwidth question is mostly settled by the device tree. The Radxa linux-7.0.11 DT statically wires QMP PHY lanes 0-1 to the RA620 HDMI bridge (DP) and lanes 2-3 to the USB-A port, so HDMI does not take USB 3 bandwidth; only the PHY block is shared.
  
  What remains is to qualify one specific SSD and enclosure on the Q6A:
  - a 60-minute sustained-write test;
  - temperature logging;
  - an HDMI hot-plug test;
  - ruling out USB power and link-power-management problems.
  
  Hardware: a TLC NVMe of 512 GB or more (1 TB preferred) in an RTL9210B or ASM2362 UAS enclosure, or a Samsung T7 Shield 1 TB. Avoid QLC drives.
    - **Steps:**
      - Check the link: lsusb -t should show Driver=uas at 5000M.
      - Sustained write on a scratch drive (this destroys its data): sudo fio --name=usbw --filename=/dev/sdX --rw=write --bs=4M --ioengine=libaio --iodepth=8 --direct=1 --time_based --runtime=3600 --write_bw_log=/root/usb --log_avg_msec=1000. Then do a 10-minute --rw=read run for the missing read figure.
      - Log SSD temperature every 30 s with smartctl (smartmontools 7.4 in Ubuntu 24.04): sudo smartctl -d sntrealtek -A /dev/sdX (RTL9210), -d sntasmedia (ASM2362) or -d sntjmicron (JMS583).
      - Watch the kernel log during the run: dmesg -w | grep -iE 'uas|reset|xhci|over-current|I/O error'.
      - HDMI hot-plug: unplug and replug HDMI 10 times during the run.
      - Power: measure the SSD current with an inline USB tester. If it peaks near or above 0.9 A, or resets occur, feed the enclosure from the system 5 V buck through a USB 3 power-injection Y cable. Radxa's brief asks for a 24 W (12 V/2 A) supply when USB 3.1 and PCIe are fully loaded.
      - Stability knobs, if resets appear: usbcore.autosuspend=-1 and usbcore.quirks=<vid>:<pid>:k (k disables link power management). As a last resort, usb-storage.quirks=<vid>:<pid>:u disables UAS and lowers throughput. Otherwise try another bridge chip.
      - Format the capture filesystem as ext4 or XFS with noatime (not exFAT/NTFS), and use preallocated files (fallocate -l 200G /data/iq/cap.bin) with large O_DIRECT writes.
      - Mount the SSD where the cold-weather fix keeps it warm, and give it a thermal pad to the case wall.
    - **How to verify:** Pass if all of the following hold:
  - over 60 min, the minimum 1-s bandwidth is at least 300 MB/s for direct cs16, or the average is at least 270 MB/s when writing behind the RAM FIFO;
  - zero UAS or xhci resets, including during HDMI replugs;
  - SSD temperature stays under 70 C;
  - a limeTRX 56 MHz capture of 30 minutes or more produces exactly one SigMF 'captures' entry.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://lore.gitlab.freedesktop.org/drm-ai-reviews/20260522060645.4399-1-graham.oconnor@gmail.com/
      - https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/usb
  6.
    - **Problem:** No one has reported concurrent load on the Q6A: the PCIe SDR stream (184-246 MB/s), plus USB 3 or UFS recording, plus NPU inference. The SoC reaches 90 C and above under stress and shut down at 105 C without a heatsink.
    - **Proposed fix:** Treat this as a qualification run: add one load at a time and keep each one on its own CPU cores and IRQs.
  
  Memory bandwidth is not the limit (LPDDR5-5500 against well under 1 GB/s of I/O). The risks are scheduling latency, IRQ collisions, thermal throttling and supply droop.
  
  Placement:
  - the SDR receive thread on the 2.7 GHz A78 core;
  - the writer on another A78 core;
  - UFS, xHCI and PCIe interrupts on separate cores;
  - the GUI and the NPU host process on the A55 cores.
  
  The classifier runs on decimated or FFT frames at a limited duty cycle.
    - **Steps:**
      - Map the cores: grep . /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_max_freq. Expect CPU0-3 A55, CPU4-6 A78 at 2.4 GHz and CPU7 A78 at 2.7 GHz.
      - IRQ placement: sudo systemctl stop irqbalance. Find the IRQs with grep -iE 'ufs|xhci|dwc3|pcie|msi' /proc/interrupts, then: echo 4 > /proc/irq/<ufs>/smp_affinity_list; echo 5 > /proc/irq/<xhci>/smp_affinity_list; echo 6 > /proc/irq/<pcie-msi>/smp_affinity_list.
      - CPU frequency during a session: echo performance | sudo tee /sys/devices/system/cpu/cpufreq/policy*/scaling_governor. Add preempt=full to the kernel command line (the Radxa kernel is PREEMPT_DYNAMIC).
      - Pinning: taskset -c 7 chrt -f 50 <SDR receive/recorder>; taskset -c 5-6 <writer/mbuffer>; taskset -c 0-3 nice -n 10 <SDR++/SatDump GUI, NPU host app>. Raise the LimeSuiteNG batch size (limeTRX --rxPacketsInBatch=8..32) to reduce interrupt rate.
      - Test matrix, 30 minutes per stage:
  (A) SDR at 61.44 Msps streamed to /dev/null: SoapySDRUtil --args=driver=limesuiteng --rate=61.44e6 --direction=RX;
  (B) A plus recording to UFS through the FIFO;
  (C) A plus recording to the USB SSD;
  (D) C plus NPU inference in a loop, e.g. LiteRT benchmark_model --external_delegate_path=libQnnTFLiteDelegate.so --external_delegate_options='backend_type:htp';
  (E) D plus the SDR++ waterfall on HDMI.
      - Log every second: cpufreq scaling_cur_freq of each core, all /sys/class/thermal zones, mbuffer fill %, overflow markers, and board input power from an inline USB-C PD meter. Run a fan curve: off below 60 C, full at 75 C on the CPU zone.
      - If a stage fails: drop GUI frame rate first, then the NPU duty cycle, then the sample format (cs16 to packed-12 to cs8), then the sample rate.
    - **How to verify:** Each stage passes if, for the full 30 minutes:
  - SigMF 'captures' count is 1 and SoapySDRUtil shows no 'O' overflows;
  - the FIFO never goes above 50% full;
  - no CPU zone exceeds 85 C and no core's frequency drops;
  - the input supply stays within PD source limits.
  
  Keep the logs as the baseline for future software updates.
    - **Confidence:** medium
    - **Sources:**
      - https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
      - https://github.com/myriadrf/LimeSuiteNG/blob/develop/cli/limeTRX.cpp
      - https://github.com/myriadrf/LimeSuiteNG/blob/develop/plugins/soapysdr/Registration.cpp
      - https://github.com/myriadrf/LimeSuiteNG/blob/develop/plugins/soapysdr/Streaming.cpp
      - https://forum.radxa.com/t/30630
  7.
    - **Problem:** Cold-weather operation is unverified. The standard UFS module is rated 0-70 C and the T7 Shield 0-60 C, and Ukrainian winter passes start well below 0 C.
    - **Proposed fix:** Gate heavy writes on measured temperature, and use the SoC itself as the heater inside a removable insulated winter sleeve.
  
  1. The Q6A device tree (mainline and Radxa) defines a board NTC labelled ufs_therm, exposed as thermal zone "ufs-thermal" (presumably next to the UFS connector). This gives a direct reading for the module area.
  2. If the module supports UFS temperature notification, the kernel also registers a "ufs" hwmon device that reads the device's case temperature.
  3. The Q6A draws about 9.5-10 W under stress (SmartHomeCircle). That is enough to warm an insulated bay before captures, and it also keeps the Li-ion cells warmer.
  4. Industrial module: Radxa's brief lists an optional -25 to +85 C grade (SKU and price not found).
  
  The mobile UFS 3.1 chips themselves are commonly listed at -25 to +85 C (distributor listings for similar Samsung and Kioxia parts; not confirmed for the exact chips).
    - **Steps:**
      - Find the sensors: for z in /sys/class/thermal/thermal_zone*; do echo "$z $(cat $z/type) $(cat $z/temp)"; done (look for ufs-thermal). Also run sensors, which shows a 'ufs' hwmon if the module supports it. Or read sudo ufs-utils attr -t 0x18 -p /dev/bsg/ufs-bsg0 (bDeviceCaseRoughTemperature, value minus 80 = degC; may be unsupported).
      - Warm-up gate (systemd unit before the recorder): if ufs-thermal is below +5 C, turn the fan off and run stress-ng --cpu 4 --timeout 600 until ufs-thermal exceeds +10 C and the SSD (smartctl) exceeds +5 C. Only then allow wideband writes. Narrowband 24 MB/s writes may start earlier.
      - Insulation: a removable 5 mm closed-cell foam (EVA/neoprene) sleeve around the electronics and battery bay, with a closable fan duct and a thermostatic fan (on above 70 C CPU). Remove the sleeve in summer.
      - Optional heater if the gate is too slow: a 5-10 W polyimide heater film on the battery/board bay, switched by a 10 C normally-closed bimetal thermostat (KSD9700 type) or a GPIO-driven MOSFET from the 4S pack. Part and price not verified.
      - Batteries (general Li-ion rule): never charge below 0 C. Use a BMS or charger with an NTC charge inhibit.
      - Condensation: when coming indoors, seal the unit in a zip bag until it reaches room temperature, and keep a silica-gel sachet in the case.
      - Ask Radxa, Arace or Allnet for the industrial-grade UFS SKU before winter.
    - **How to verify:** Freezer test, 5 cycles:
  1. Keep the powered-off unit at -18 C for 2 h.
  2. Boot it outdoors or in a cold room and log ufs-thermal, the SSD temperature and CPU zones every 5 s.
  3. Record the time to reach the gate.
  4. At the gate, run fio --verify=crc32c with a 10 GB write and verify on both UFS and the SSD.
  
  Pass: boot succeeds every time, zero UFS/USB errors, zero verify mismatches, and the gate is reached in under 15 min.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://github.com/torvalds/linux/blob/master/drivers/ufs/core/ufs-hwmon.c
      - https://dl.radxa.com/accessories/ufs-module/rad-doc-0154_radxa_ufs_module_product_brief__revision_1.2_g69c4d5d.pdf
      - https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5
      - https://trustcompo.com/product/detail/TCE000026953-KLUEG8UHGC-B0E1
      - https://static-lang.dasenic.com/product/kioxia-america-inc-thgjfgt1e45bail-8125684
  8.
    - **Problem:** Sharing the Q6A M.2 slot through a PCIe switch, and the 2230-to-2280 extension for the LimeSDR Micro, are both untested on the Q6A.
    - **Proposed fix:** Do not use a switch for storage: the USB SSD (about 395 MB/s) covers the need. None of the products found is a palm-sized, M.2-edge-hosted Gen3 switch:
  - the Seeed ASM2806 board needs a Pi 5 FFC;
  - ASM1182e boards are Gen2 x1;
  - ASM2812 dual-M.2 cards are x8 slot cards.
  
  One point in favour: the Q6A DT already maps SMMU stream IDs for a QPS615 switch topology on pcie1 (BDFs 0x100-0x501). A generic switch with up to 3 endpoints might enumerate, but that remains untested.
  
  For the SDR's extension:
  - Prefer a mechanical-only mounting: a 2280 card in the 2230 socket with a 3D-printed support at 80 mm, if the overhang is free (the brief's drawing shows an 85 x 56 mm board). Otherwise use a short rigid extender PCB, not a flexible ribbon.
  - Validate the link, and fall back to Gen2, which is enough for 61.44 Msps but not 160 Msps.
    - **Steps:**
      - Check the link: sudo lspci -tv to find the SDR and its root port (RP), then sudo lspci -vv -s <SDR BDF> | grep -E 'LnkCap|LnkSta'. Expect Speed 8GT/s, Width x1.
      - Error watch during a 1-hour stream at 61.44 Msps: cat /sys/bus/pci/devices/<BDF>/aer_dev_correctable (if present, before and after) and dmesg | grep -iE 'aer|pcie.*(error|link down)'.
      - If errors appear, force Gen2 at runtime: sudo setpci -s <RP> CAP_EXP+0x30.w=0x2:0xf; sudo setpci -s <RP> CAP_EXP+0x10.w=0x20:0x20 (retrain), then re-check LnkSta for 5GT/s. To make it permanent, use a DT overlay: &pcie1 { max-link-speed = <2>; };
      - Gen2 x1 gives about 400 MB/s usable: enough for 61.44 Msps I12 (184 MB/s) or I16 (246 MB/s), not for 160 Msps (480-640 MB/s).
      - Mechanical: support the far end of the 2280 card with a screw boss and avoid board flex. Mount the Q6A on all 4 corner holes (3.5 mm diameter per the brief).
      - Only if NVMe-in-M.2 ever becomes essential: bench-test a switch outside the handheld first. Check enumeration under UEFI 260120 (thread 31195 reports some NVMe drives not enumerating) and under Linux, and watch for SMMU faults in dmesg.
    - **How to verify:** Pass if:
  - LnkSta is stable at the target speed;
  - the AER counters do not increase;
  - a 1-hour stream shows zero gaps (one SigMF captures entry, no Soapy 'O' overflows);
  - all of this repeats after a cold-soak cycle and a moderate tap test on the case.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/nvme
      - https://www.cnx-software.com/2025/01/21/pcie3-0-to-dual-m-2-hat-for-raspberry-pi-5-features-asmedia-asm2806-pcie-3-0-switch/
      - https://pipci.jeffgeerling.com/hats/pineboards-hatdrive-dual-nvme-m2.html
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
      - https://forum.radxa.com/t/30807
  9.
    - **Problem:** No one has reported a RAM ring-buffer recorder at 160 Msps (640 MB/s) on the Q6A or a similar ARM board.
    - **Proposed fix:** Prove it in two steps with existing tools, then build a small dedicated recorder.
  
  Step 1, ingest-only: limeTRX writing into tmpfs, where writes are just memcpy, so this isolates PCIe/driver/CPU limits from storage.
  
  Step 2, streaming: limeTRX into a named pipe, then mbuffer with a mlocked 8 GiB buffer (-L, so no page faults during the capture), then disk.
  
  Production recorder: SoapySDR readStream into an mmap(MAP_POPULATE)+mlock ring, packing to 12 bits (480 MB/s), with writer threads doing 4 MiB O_DIRECT writes to the USB SSD and UFS in parallel (separate files) and a pre-trigger buffer.
  
  Sizing:
  - an 8 GiB ring holds 13.4 s of 160 Msps cs16 with no drain;
  - with a 395 MB/s drain to the USB SSD, about 35 s;
  - packed 12-bit (480 MB/s) with a 395 MB/s drain, about 101 s;
  - cs8 (320 MB/s) is below the USB SSD's measured rate, so it should be sustainable (verify).
    - **Steps:**
      - Free RAM for the ring: sudo swapoff -a (and disable zram if present); sudo sysctl vm.dirty_background_bytes=268435456 vm.dirty_bytes=1073741824.
      - Ingest-only test:
  sudo mount -o remount,size=12G /dev/shm
  limeConfig --initialize --samplerate=160e6 --rxen=1 --rxlo=2.2e9 --rxlpf=100e6
  taskset -c 7 chrt -f 50 limeTRX --output=/dev/shm/b160 --time=10000 --linkFormat=I12 --rxPacketsInBatch=16
  The result should be about 6.4 GB. CLI flags are from LimeSuiteNG develop; the limesdr-micro branch may differ.
      - Streaming test:
  mkfifo /dev/shm/cap.sigmf-data   (limeTRX appends .sigmf-data to the --output name)
  sudo mbuffer -i /dev/shm/cap.sigmf-data -m 8G -L -s 4M -o /data/iq/cap.cs16 &
  taskset -c 7 chrt -f 50 limeTRX --output=/dev/shm/cap --time=60000 --linkFormat=I12
  Watch mbuffer's fill %. -L needs root or ulimit -l unlimited.
      - Compare link formats: I12 on the link is 480 MB/s, about 60% of PCIe Gen3 x1, but costs CPU to unpack. I16 is 640 MB/s, about 80% of the link. Keep whichever runs with zero gaps.
      - Recorder design notes: preallocate output files (fallocate); pack 2 x 12 bits into 3 bytes with NEON; trigger saves from the NPU classifier; write a SigMF meta file recording the format (custom ci12 packed). Ship a converter to cs16 for SatDump.
      - Repeat the tests at 61.44 Msps on two RX channels (491.5 MB/s cs16), since 2R is also planned.
    - **How to verify:** 1. The ingest test produces exactly one SigMF 'captures' entry and no log errors over 10 consecutive bursts.
  2. The streaming test shows mbuffer's maximum fill matching the predicted fill rate (e.g. 640-395 = 245 MB/s), and the output file size equals samples x 4 bytes.
  3. SoapySDRUtil --args=driver=limesuiteng --rate=160e6 --direction=RX prints no 'O' over 60 s.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/blob/develop/cli/limeTRX.cpp
      - https://github.com/myriadrf/LimeSuiteNG/blob/develop/cli/limeConfig.cpp
      - https://github.com/myriadrf/LimeSuiteNG/blob/develop/plugins/soapysdr/Streaming.cpp
      - https://github.com/myriadrf/LimeSuiteNG/blob/develop/src/include/limesuiteng/types.h
      - https://manpages.ubuntu.com/manpages/noble/man1/mbuffer.1.html
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
  10.
    - **Problem:** Mechanical retention of the UFS module: it is held only by two B2B connectors (a 30-pin GB042-30S for signals and a 34-pin GB042-34S for mounting only). There are no handheld vibration or drop reports.
    - **Proposed fix:** Clamp the module softly from the case. A 3D-printed boss or rib in the bottom shell presses on the module through a 1.0-1.5 mm soft silicone thermal pad compressed about 20-30%. This is how phones retain B2B connectors, and the pad also sinks module heat into the case.
  
  Also:
  - add a Kapton strip as secondary retention;
  - mount the board on all four corner holes to prevent flex. Signal-integrity margin is already thin: Radxa's DT limits UFS to Gear-4 Rate-A because Rate-B is "unstable due to board and UFS module design limitations".
    - **Steps:**
      - The UFS and eMMC connectors are on the board's bottom side (brief drawing). With the board mounted on its standoffs, measure the gap from the module's top surface to the case floor with calipers or a clay squash test.
      - Design a rib or boss about 28 x 20 mm, avoiding the connector housings. Boss height = gap - 0.75 x pad thickness (e.g. a 1.0 mm pad leaves 0.25 mm of compression).
      - Fit a soft silicone thermal pad (3-6 W/mK class, cut to 28 x 20 mm). Add a Kapton strip over the module onto bare PCB areas.
      - Use all four 3.5 mm corner holes with M3 standoffs, and do not let the case press on the board elsewhere.
      - After field trips, inspect seating and check dmesg for UFS errors.
    - **How to verify:** 1. Run sudo fio --name=v --filename=/data/v.bin --size=10G --rw=write --bs=1M --direct=1 --verify=crc32c --do_verify=1.
  2. During the run: 50 firm taps on the case and 10 drops from 30 cm onto a padded surface, then a 10-minute walk with the device in a backpack.
  3. Pass: zero verify errors, zero new counters in /sys/kernel/debug/ufshcd/*/stats, and no ufshcd lines in dmesg.
  4. Bonus check: ufs-thermal reads lower under sustained writes than before the pad.
    - **Confidence:** medium
    - **Sources:**
      - https://dl.radxa.com/accessories/ufs-module/rad-doc-0154_radxa_ufs_module_product_brief__revision_1.2_g69c4d5d.pdf
      - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
      - https://github.com/radxa/kernel/blob/linux-7.0.11/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
      - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
      - https://github.com/torvalds/linux/blob/master/drivers/ufs/core/ufs-debugfs.c
- **Residual risks:**
  - The post-cache UFS speed and the factory WriteBooster provisioning of Linux-shipped modules are still unknown until the user runs the sysfs dump and the fill test. Radxa's 4 GiB WriteBooster setting comes from its Android provisioning XML and may not match what Linux modules ship with.
  - Re-provisioning the module with a pseudo-SLC capture LUN via edl-ng is unproven on Radxa modules. The edl-ng provision syntax is inferred, a mistake can make the module unusable, and it may void the warranty.
  - The runtime PA_TActivate write through ufs-utils is untested, needs CONFIG_SCSI_UFS_BSG, and is lost after any host reset.
  - The no-hibernate field profile's battery cost has not been measured. If the Kioxia root cause is not only hibernate entry/exit, the profile may not fully prevent the problem.
  - The Kioxia quirk is absent from mainline (7.3-rc7). Any kernel switch (Canonical, mainline, future Radxa 7.x without the patch) can bring the bug back. Pinning the kernel blocks security updates until the patch is upstream.
  - LimeSDR Micro support lives in a LimeSuiteNG branch, so CLI flags may differ from develop. 160 Msps half-duplex RX over PCIe Gen3 x1 has not been demonstrated on any ARM SBC. Pre-orders ship Dec 15, 2026 at $249 (Basic) or $299 (GNSS), so testing cannot start before then.
  - USB SSD: only one Q6A data point exists, the USB-A port's current limit is unpublished, and the T7 Shield is rated 0-60 C. The chosen drive and enclosure must pass the 60-minute test.
  - Cold weather: operating ranges for the exact chips (KLUDG4UHDC-B0E1, THGJFGT1E45BAILB) were not confirmed from vendor datasheets. Availability and price of the industrial-grade UFS SKU are unknown.
  - The TBW figures are an estimate (assumed 1,000-3,000 P/E, WAF 1.1), not a vendor specification. Real endurance comes only from the empirical method in the wear-logging fix.
  - Board-geometry note for the case designer: the product-brief drawing shows 85 x 56 mm, not the 85 x 65 mm in the stack list. The M.2 socket's position and whether a 2280 card can overhang were not confirmed from Radxa documents.
  - Prices for the enclosure, heater film, thermal pad and power-injection cable were not verified, and NAND-shortage pricing in 2026 remains volatile.

## Адверсаріальна перевірка (`verify`)

_Run `wf_3e735695-e00`_

- **Component:** Storage (OS + raw IQ recording) for the Radxa Dragon Q6A handheld: Radxa UFS 3.1 module + USB 3 SSD + RAM ring buffer
- **Recommendation holds:** ні
- **Issues:**
  1.
    - **Claim:** Recommended UFS: Radxa UFS 3.1 256GB (Kioxia) or 512GB, about $76-90 at Allnet.
    - **Problem:** Both are sold out at Allnet. Arace lists all four capacities (64/128/256/512GB) as sold out. The 256GB carries the Kioxia THGJFGT1E45BAILB chip, which freezes and reboots on the Q6A unless the kernel has a quirk that mainline lacks. Nobody knows which chip the 512GB uses. Once wideband captures go to the USB SSD, the higher write figure of the 256GB part no longer matters.
    - **Correction:** Use the Radxa UFS 128GB (RA022-B10J0U2, Samsung KLUDG4UHDC-B0E1) as the OS and narrowband-pass drive. It costs $65.90 at Allnet China and is in stock (Tinytronics: EUR 58, not in stock, 2-4 weeks). Radxa reproduced no faults with the Samsung module. Check the chip on arrival.
    - **Source:** https://shop.allnetchina.cn/products/high-performance-ufs-3-1-module ; https://arace.tech/products/radxa-ufs-module ; https://forum.radxa.com/t/ufs-random-reboots/30630
  2.
    - **Claim:** Samsung T7 1TB costs 7,499 UAH on Rozetka; the total setup is about $250-270.
    - **Problem:** Rozetka returned 403, so I could not verify it. Hotline.ua today lists the T7 1TB at 9,299-13,813 UAH (Titan Gray, 49 offers) and 9,700-15,958 UAH (Indigo, 65 offers). The T7 Shield 1TB Blue is 11,980-14,451 UAH and the Black is 13,587-17,899 UAH. The NBU rate on Oct 15, 2026 was about 44.98 UAH/USD.
    - **Correction:** T7 1TB is about $207 or more; T7 Shield 1TB is about $266 or more. With the 128GB UFS, the realistic total is about $273 (T7) or about $332 (Shield), plus shipping and customs on the UFS.
    - **Source:** https://hotline.ua/ua/sr/?q=Samsung%20T7%20Shield%201TB ; https://unn.ua/en/amp/exchange-rates-as-of-october-15-what-happened-to-the-dollar-after-its-historic-high
  3.
    - **Claim:** Record with LimeSuiteNG linkFormat I12 (packed 12-bit on the link). I12 at 160 Msps is 480 MB/s, about 60% of PCIe Gen3 x1.
    - **Problem:** In the limesdr-micro branch, LA9310_TRX.cpp hard-codes 'mConfig.linkFormat = DataFormat::I16; // always force I16 link', and the RX DMA buffers are complex16_t. The LimeSDR Micro ignores I12, so 160 Msps always crosses PCIe as 640 MB/s.
    - **Correction:** Budget PCIe at 4 bytes per complex sample (640 MB/s at 160 Msps, 245.76 MB/s at 61.44 Msps). Any reduction to 12-bit or 8-bit has to happen on the CPU after receive.
    - **Source:** https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro/src/src/boards/LimeSDR_Micro/LA9310_TRX.cpp
  4.
    - **Claim:** Store packed 12-bit to save space (184 MB/s instead of 246 MB/s at 61.44 Msps).
    - **Problem:** LimeSuiteNG's DataFormat::I12 is 'stored as int16_t' (types.h), so it saves no bytes. The limesuiteng SoapySDR plugin advertises SOAPY_SDR_CS12 but maps it to that int16-stored I12. A Soapy-based recorder that assumes the Soapy convention for CS12 (3 bytes per sample) would write corrupt or mis-sized files. SatDump has no 12-bit baseband type (CF32/CS32/CS16/CS8/CU8/WAV16/ZIQ/ZIQ2).
    - **Correction:** Request CS16. Then either pack 2x12 bits into 3 bytes yourself with NEON and convert back to cs16 for SatDump, or save cs8 or ZIQ.
    - **Source:** https://raw.githubusercontent.com/myriadrf/LimeSuiteNG/develop/src/include/limesuiteng/types.h ; https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro/plugins/soapysdr/Streaming.cpp ; https://raw.githubusercontent.com/SatDump/SatDump/master/src-core/common/dsp/io/baseband_type.h
  5.
    - **Claim:** limeTRX silent output-failure bug: use a LimeSuiteNG build from after Aug 3, 2026 (PR #376).
    - **Problem:** The fix ('Failed to open Rx output file') is in develop only. The limesdr-micro branch, which LimeSDR Micro users must run (tip Oct 1, 2026), still opens the .sigmf-data file without checking. Its RX loop also writes the file synchronously with std::ofstream. The LA9310 RX FIFO is only 512 batches of about 100 us, roughly 50 ms, so any disk stall longer than that drops samples.
    - **Correction:** Do not record wideband by pointing limeTRX straight at UFS or the SSD. Either use the FIFO pipeline (limeTRX into a named pipe, then mbuffer -L -m 8G, then disk), or a small custom recorder with an mlocked ring and a separate writer thread. Check that output files grow, and count SigMF 'captures' entries: exactly one means no gaps.
    - **Source:** https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro/cli/limeTRX.cpp ; https://github.com/myriadrf/LimeSuiteNG/issues/405
  6.
    - **Claim:** The Kioxia fix exists in Radxa/Armbian kernels; the 9-day uptime report shows it is stable.
    - **Problem:** The uptime line reads 'up 9:51', which is 9 h 51 min, not 9 days. Mainline (7.3-rc7, checked) has no Q6A UFS node at all, nor the Kioxia quirk. Armbian 'edge' (mainline v7.2.3 plus patches) adds the UFS device-tree node and the HS-G4 PHY fix but not the Kioxia quirk. Only Armbian 'current' (radxa/kernel linux-6.18.2) and radxa/kernel linux-7.0.11 have it.
    - **Correction:** Run the Radxa vendor kernel (Radxa OS noble, or Armbian current). Never use a Canonical generic, mainline or Armbian-edge kernel with a Kioxia module. Hold the kernel and its matching headers. With the Samsung 128GB the quirk does not apply, but you still need the vendor kernel for UFS and USB 3.
    - **Source:** https://forum.radxa.com/t/ufs-random-reboots/30630?page=2 ; https://github.com/armbian/build/blob/main/config/sources/families/qcs6490.conf ; https://github.com/radxa/kernel/blob/linux-7.0.11/drivers/ufs/host/ufs-qcom.c ; https://github.com/torvalds/linux/blob/master/arch/arm64/boot/dts/qcom/qcs6490-radxa-dragon-q6a.dts
  7.
    - **Claim:** Budget: 128GB UFS handles cs8 at 61.44 Msps (123 MB/s), well under even a pessimistic post-cache rate of about 250 MB/s.
    - **Problem:** The roughly 250-300 MB/s floor comes from 256GB parts (Critical Link's 256GB QCS6490 module: 300-1500 MiB/s depending on WriteBooster). A 128GB TLC part has about half the dies, so its post-cache write is probably lower, possibly near 120-200 MB/s (inference, not measured). Radxa's 388 MB/s is a short dd run inside the cache. Radxa's own Q6A provisioning uses only a 4 GiB WriteBooster buffer, about 10 s at 388 MB/s.
    - **Correction:** Treat even 56 MHz cs8 to the 128GB UFS as unproven until a long fio fill test passes. Plan the UFS for narrowband passes (7 Msps cs16 = 28 MB/s, the LimeSDR Micro minimum without decimation) and short RAM-buffered bursts.
    - **Source:** https://git.criticallink.com/redmine/projects/mitysom_qc6490/wiki/UFS ; https://dl.radxa.com/q6a/images/android/provision_ufs31.xml ; https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
  8.
    - **Claim:** Alternative USB storage: TLC 2230 NVMe such as the WD SN740 in a UAS enclosure.
    - **Problem:** The SN740 is DRAM-less and relies on HMB. USB bridges (RTL9210/ASM2362/JMS583) do not pass HMB, so behind USB it runs without its host-memory map cache. I found no post-cache data for the 512GB SN740. The cheapest 1TB portable SSD in Ukraine, the Kingston XS1000 (6,726 UAH), drops to about 140 MB/s after about 60 GB of cache (Mezha 1TB test).
    - **Correction:** Prefer the Samsung T7 1TB. ssd-tester measured a 614 MB/s average over 100 GB with a 42 GB cache, which implies about 480 MB/s after the cache. The T7 Shield 1TB averaged 879 MB/s over 200 GB with a 20 GB cache. Both stay above the Q6A's ~395 MB/s USB ceiling. Or use a DRAM-equipped TLC NVMe in a metal enclosure. Use the XS1000 only for cs8 or short cs16 bursts.
    - **Source:** https://ssd-tester.com/samsung_portable_ssd_t7_1tb.html ; https://ssd-tester.com/samsung_portable_ssd_t7_shield_1tb.html ; https://mezha.media/en/?p=145948 ; https://hotline.ua/ua/sr/?q=Kingston%20XS1000%201TB
  9.
    - **Claim:** The USB-A port power limit is unpublished.
    - **Problem:** Schematic v1.21 page 26 shows one WS4612 load switch feeding VDD_USB_VBUSTYPEA for the stacked USB3/USB2 Type-A pair. Its ISET resistor is 3.24 kOhm, and the formula Ilim = 6800/Rset gives about 2.1 A shared between the two ports. This is read from the schematic text, not measured.
    - **Correction:** A T7 (under 1 A) plus an RTL-SDR (about 0.3 A) on that pair fits. Do not add a bus-powered hub or a Gen4 2280 NVMe enclosure to the same pair. Keep Radxa's 24 W (12 V/2 A) minimum when USB 3.1 and PCIe are both loaded.
    - **Source:** https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf ; https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
  10.
    - **Claim:** Optional: reprovision the UFS module with a pSLC capture LUN via edl-ng.
    - **Problem:** edl-ng does have a 'provision <xml>' command, but on a 128GB module a 32 GiB pSLC LUN uses about 96 GiB of TLC (3:1), leaving almost nothing for the OS. The procedure wipes the module, is untested on Radxa modules and can brick it. The USB SSD already makes it unnecessary.
    - **Correction:** Skip it. Keep wideband captures on the replaceable USB SSD.
    - **Source:** https://github.com/strongtz/edl-ng ; https://dl.radxa.com/q6a/images/android/provision_ufs31.xml
  11.
    - **Claim:** The SDR is available for testing from about Sept 30, 2026 at $199.
    - **Problem:** Crowd Supply now lists $249 Basic / $299 GNSS, with 'orders placed now ship Dec 15, 2026'. The Micro also needs the out-of-tree la9310_limesdr kernel module (DKMS).
    - **Correction:** Storage qualification with the real SDR cannot start before about mid-December. Run the UFS and SSD fio tests now. Install the linux-headers package for the pinned Radxa kernel so the la9310 DKMS module builds.
    - **Source:** https://www.crowdsupply.com/lime-micro/limesdr-micro ; https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro/drivers/linux/la9310_limesdr
- **Forum and fix assessment:** The forum work holds up, and I re-verified the parts that matter:
  - Radxa PR #551 (merged May 11, 2026) adds UFS_DEVICE_QUIRK_PA_TACTIVATE for THGJFGT1E45BAILB. It is present in radxa/kernel linux-6.18.2 and linux-7.0.11, and absent from torvalds master (7.3-rc7).
  - The mainline Q6A device tree does not even enable UFS or USB 3. Armbian current builds from radxa/kernel linux-6.18.2, so it includes the fix. Armbian edge (v7.2.3 plus patches) adds the UFS node and HS-G4 PHY fix but not the Kioxia quirk.
  
  Correction: the '9 days uptime' was 9 h 51 min. The fixes agent already caught this.
  
  The proposed sysfs and driver mechanics check out against mainline source:
  - ufs-qcom sets CLK_GATING, HIBERN8_WITH_CLK_GATING, CLK_SCALING, WB_WITH_CLK_SCALING and WB_EN.
  - wb_on_store returns -EOPNOTSUPP when WriteBooster is tied to clock scaling.
  - The quirk writes PA_TACTIVATE = 10 (1 ms).
  - The ufs-utils syntax is valid: 'uic -t 1 -r -i 0x15a8 -p', and 'fl -t 14 -c' to clear fWriteBoosterEn.
  
  That makes the H8-suppression field profile (clkgate_enable=0, auto_hibern8=0, rpm_lvl=0, clkscale_enable=0), the WriteBooster-size measurement and the long fio fill test technically sound and worth doing.
  
  Also confirmed:
  - Radxa's Q6A provisioning XML has a 4 GiB shared WriteBooster with preserve-user-space=1.
  - HDMI and USB 3 use separate QMP PHY lanes (DP on 0-1, USB on 2-3).
  - pcie0 is used by the RTL8111K Ethernet, so there is no spare PCIe lane for an NVMe. The switch idea stays dead.
  
  The weak points are in the recorder plan, not the forum fixes:
  - The Micro forces an I16 link, so I12 saves nothing.
  - Soapy CS12 from limesuiteng is int16-stored.
  - The limeTRX file-open fix is not in the limesdr-micro branch.
  - limeTRX writes synchronously into an LA9310 FIFO that holds only about 50 ms.
  
  The RAM-FIFO approach (mbuffer -L or a custom mlocked ring with thread pinning, swap off and no copy-on-write filesystem) is therefore mandatory, not optional.
  
  Drop the pSLC reprovisioning; it is high-risk and redundant. The thermal pad, the cold-start gate and NPU-gated commits are sensible low-cost additions.
- **Final recommendation:**
  - **Name:** Two drives plus a RAM buffer: Radxa UFS 3.1 Module 128GB (RA022-B10J0U2, Samsung KLUDG4UHDC-B0E1) for the OS and narrowband passes, a Samsung T7 1TB (MU-PC1T0T/WW or MU-PC1T0H/WW) on the blue USB 3.1 port for all wideband captures, and an 8 GiB mlocked RAM ring for 160 Msps bursts
  - **Price:** About $273 total:
  - UFS 128GB: $65.90 (Allnet China, in stock; Tinytronics EUR 58, 2-4 weeks), plus shipping and customs (not verified).
  - Samsung T7 1TB: from 9,299 UAH, about $207 (hotline.ua, 49-65 offers).
  Option: a T7 Shield 1TB from 11,980 UAH (about $266) instead of the T7 brings the total to about $332.
  - **Why:** 1. The 128GB Samsung module is the only Q6A-listed UFS module actually in stock. Radxa found no faults with the Samsung chip, and it measured 1703/388 MB/s (dd) on the Q6A. It is the fastest storage left with the SDR in M.2. It only has to carry the OS plus narrowband passes: HRPT/LRPT at 7 Msps cs16 is 28 MB/s, about 25 GB per 15-minute pass.
  
  2. The Q6A's USB 3.1 Gen1 port has one measured write figure: about 395 MB/s fio with UAS at 5000M. The T7 sustains above that after its cache: about 614 MB/s average over 100 GB, implying about 480 MB/s post-cache; the Shield averaged 879 MB/s over 200 GB. So the port, not the drive, is the limit, giving about 60% headroom over 56 MHz cs16 (245.76 MB/s). 1 TB holds about 68 min of cs16 or 136 min of cs8. It hot-swaps to a PC for SatDump, keeps write wear off the boot drive, and avoids the HMB loss that DRAM-less NVMe drives suffer behind USB bridges.
  
  3. 160 Msps always crosses PCIe as I16, 640 MB/s. No reachable storage sustains that, so record into an 8 GiB mlocked ring and drain to the T7 while capturing:
  - about 35 s of cs16;
  - about 101 s of CPU-packed 12-bit;
  - cs8 (320 MB/s) roughly real-time, but only about 19% under the USB ceiling.
  
  Run everything on the Radxa vendor kernel (or Armbian current), held together with its headers for the la9310 DKMS module.
  - **Sources:**
    - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com
    - https://shop.allnetchina.cn/products/high-performance-ufs-3-1-module
    - https://www.tinytronics.nl/en/data-storage/modules/radxa-ufs-module-128gb
    - https://forum.radxa.com/t/ufs-random-reboots/30630
    - https://smarthomecircle.com/radxa-dragon-q6a-best-alternative-to-the-raspberry-pi-5
    - https://ssd-tester.com/samsung_portable_ssd_t7_1tb.html
    - https://ssd-tester.com/samsung_portable_ssd_t7_shield_1tb.html
    - https://hotline.ua/ua/sr/?q=Samsung%20T7%20Shield%201TB
    - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro/src/src/boards/LimeSDR_Micro/LA9310_TRX.cpp
    - https://github.com/armbian/build/blob/main/config/sources/families/qcs6490.conf
    - https://dl.radxa.com/q6a/docs/rad-doc-0150_radxa_dragon_q6a_product_brief__revision_1.5_gbc16bac.pdf
- **Final budget option:**
  - **Name:** Radxa UFS 3.1 Module 128GB only, recording narrowband or decimated, with short wideband bursts through the RAM ring; add a Samsung T7 1TB later without redesign
  - **Price:** $65.90 (Allnet China, in stock) or EUR 58 (Tinytronics NL, 2-4 weeks), plus shipping and customs
  - **Why:** It is the cheapest officially supported boot drive that is actually in stock, it avoids the Kioxia bug, and it costs only about EUR 13 more than a slower 64GB eMMC module (EUR 45 at Tinytronics).
  
  Narrowband passes fit easily: LRPT, HRPT, CubeSats and QO-100 slices at 7 Msps or less (cs16) or decimated, 28 MB/s or less.
  
  Wideband needs care:
  - An 8 GiB RAM ring gives 56 MHz cs16 bursts of about 35 s with no drain.
  - Do not plan on sustained 56 MHz cs8 to this module until a long fio fill test proves its post-cache floor. A 2-die 128GB TLC part may fall well below the ~300 MiB/s seen on 256GB QCS6490 modules.
  
  Offload over GbE (RTL8111K on pcie0, about 110 MB/s). Do not substitute a Kingston XS1000 as the later USB SSD for long cs16 captures: it drops to about 140 MB/s after about 60 GB of cache.
- **Known problems and fixes to apply:**
  - Kernel: run only the Radxa vendor kernel (Radxa OS noble, from radxa/kernel linux-6.18.2 after May 11, 2026, or linux-7.0.11) or Armbian 'current'. Mainline has no Q6A UFS or USB 3 device-tree support. Armbian 'edge' (7.2.3) lacks the Kioxia quirk. Hold the kernel, its headers and the meta packages (apt-mark hold), because an apt upgrade has already reverted the fix once. Keep the headers so the la9310_limesdr DKMS module builds.
  - On arrival, identify the UFS chip from /sys/class/scsi_device/*/device/model and the UFS device_descriptor/manufacturer_id: 0x01CE is Samsung, 0x0198 is Kioxia. Radxa says future batches may change brand. If it is the Kioxia THGJFGT1E45BAILB:
  - confirm the quirk is active: zero ufshcd OCS, pa_err or dl_err lines in journalctl -k, and 'ufs-utils uic -t 1 -r -i 0x15a8' reads 0xa;
  - for long sessions, apply the H8-suppression profile: clkgate_enable=0, auto_hibern8=0, rpm_lvl=0, clkscale_enable=0.
  - Boot firmware: update the SPI firmware to 251013 or newer (260120 preferred) with edl-ng before fitting the UFS. Keep a microSD rescue card; removing the UFS module lets the board boot from SD. If the Radxa USB reader is not detected, flash UFS on the board over EDL (Armbian Imager) or boot from SD and write it in place.
  - Before trusting UFS for any wideband capture, measure it:
  - WriteBooster size = wb_shared_alloc_units x 512 x allocation_unit_size x segment_size, from sysfs;
  - a long run of 'fio --rw=write --bs=1M --direct=1 --iodepth=16' sized to about 70% of free space, with --write_bw_log, while logging attributes/wb_avail_buf.
  Record 56 MHz to UFS only if the 10-s minimum bandwidth is at least 295 MB/s for cs16, or comfortably above 123 MB/s for cs8.
  - Recorder: never point limeTRX straight at disk.
  - The limesdr-micro branch has no output-file open check, writes synchronously in the RX loop, and the LA9310 FIFO holds only about 50 ms.
  - Use limeTRX into a named pipe, then 'mbuffer -L -m 8G -s 4M' to the target, or a custom recorder: SoapySDR CS16 into a mmap+mlock ring, with a writer thread doing 4 MiB O_DIRECT writes to a preallocated (fallocate) file.
  - Run swapoff -a, pin the RX thread with taskset -c 7 chrt -f 50, use the performance governor, move UFS, xHCI and PCIe IRQs to separate cores, and disable auto-suspend.
  - Check that exactly one SigMF 'captures' entry exists.
  - Formats: the LimeSDR Micro forces an I16 PCIe link (--linkFormat=I12 is ignored), and limesuiteng's Soapy 'CS12' is int16-stored, not 3-byte packed. Request CS16, then convert on the CPU to cs8 or your own packed-12 (with an offline cs16 converter for SatDump), or use SatDump ZIQ. Budget 4 bytes per sample on PCIe: 640 MB/s at 160 Msps.
  - USB SSD: use a Samsung T7 or T7 Shield on the blue USB 3.1 port and confirm 'lsusb -t' shows Driver=uas at 5000M.
  - Format ext4 or XFS with noatime (not exFAT or NTFS), and preallocate capture files.
  - Run a 60-minute fio write qualification while logging 'smartctl -A' temperature and watching dmesg for uas/xhci resets, including 10 HDMI replugs.
  - If resets appear, set usbcore.autosuspend=-1 and add the 'k' (no LPM) quirk for the drive.
  - Avoid QLC drives, DRAM-less HMB NVMe drives in USB bridges, and the Kingston XS1000 for long cs16 captures.
  - Power: the stacked USB3/USB2 Type-A pair shares one WS4612 switch limited to about 2.1 A (schematic v1.21, read from the schematic, not measured). Put only the T7, plus at most the RTL-SDR, on that pair. Supply the Q6A with at least 24 W (12 V/2 A) through USB-C PD or the 12 V header when PCIe and USB 3 are both loaded.
  - Thermal and cold:
  - The UFS module reaches about 60 C even with fans. Press it from the case with a 1.0-1.5 mm silicone pad on a printed boss (this also retains the B2B connector) and log the 'ufs-thermal' zone.
  - The T7 Shield is rated 0-60 C (case), and the standard UFS module 0-70 C (Evelta listing).
  - Gate wideband writes until ufs-thermal is above +10 C, warming the board with stress-ng inside a foam winter sleeve.
  - Never charge the Li-ion pack below 0 C.
  - Wear: no TBW is published for Radxa UFS modules. Log health_descriptor/life_time_estimation_a/b, eol_info and wb_life_time_est at every boot and capture. Keep 56 MHz captures on the replaceable T7 (885 GB/h at cs16). Optionally let the NPU classifier decide which RAM-ring segments get written to disk.
- **Missed better options:**
  - For this role the 128GB Samsung UFS beats the 256GB Kioxia: it is in stock, $10 cheaper on paper, and needs no vendor-only quirk. Its lower burst write does not matter once wideband goes to the USB SSD.
  - The Samsung T7 1TB (from 9,299 UAH) is the price/performance pick in Ukraine, since any drive sustaining more than ~400 MB/s saturates the Q6A port. The T7 Shield adds IP65 and about 870 MB/s post-cache for about 2,700 UAH more. The Kingston XS1000 is cheaper (6,726 UAH) but falls to about 140 MB/s after its cache, so it is not a real substitute.
  - Double duty: the NPU classifier can gate which RAM-ring segments are committed to disk. That cuts storage size and UFS wear without extra hardware.
  - No hidden second PCIe lane exists: pcie0 is used by the RTL8111K Ethernet, and Wi-Fi is a USB module on the onboard USB 2.0 hub. Sharing the M.2 slot through a switch remains the only, and not recommended, route to NVMe.
- **Remaining uncertainties:**
  - Post-WriteBooster sustained write of both Radxa modules on the Q6A is unknown. It may be below 200 MB/s on the 128GB Samsung part (inference from die count). The WriteBooster provisioning of Linux-shipped modules is also unknown; Radxa's 4 GiB value comes from its Android XML.
  - Only one Q6A USB 3 storage figure exists: about 395 MB/s fio write with an unnamed adapter, no parameters and no sustained run. Long-run UAS stability is untested.
  - The chip in future 128GB and 512GB batches is not guaranteed; Radxa staff said they are 'not certain which brand will be used in the next batch'.
  - Allnet China shipping to Ukraine and the landed cost were not verified. The AliExpress Radxa store price could not be fetched (redirect or login wall). The Rozetka 7,499 UAH T7 price could not be re-checked (HTTP 403).
  - The roughly 2.1 A Type-A VBUS limit is read from schematic text (WS4612, Rset 3.24 kOhm). Exactly which ports share the switch is inferred from page 26.
  - 160 Msps RX over PCIe Gen3 x1 into a RAM ring has not been demonstrated on the Q6A or any ARM SBC. The LimeSDR Micro ships Dec 15, 2026, so end-to-end tests wait until then.
  - Cold-start behaviour below 0 C for the UFS module and the T7 is untested. Availability, SKU and price of the industrial -25 to +85 C UFS grade are unknown.
  - The Kioxia quirk has not been upstreamed to mainline, so a future Radxa kernel rebase could drop it. Re-verify after every kernel update.
- **Confidence:** medium

_Агент цього етапу ще працює (run `wf_3e735695-e00`)._

