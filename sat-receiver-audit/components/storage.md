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

_Агент цього етапу ще працює (run `wf_3e735695-e00`)._

