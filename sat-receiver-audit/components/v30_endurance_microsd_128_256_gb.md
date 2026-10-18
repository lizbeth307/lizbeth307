# V30 endurance microsd 128 256 gb: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a7487549-f90`_

- **Part:** V30 endurance microSD 128-256 GB (second storage: raw overflow plus a second snapshot copy; tier optional, group Optional / gated, qty 1). Under the 18 Oct 2026 decision (Lime kept, T7 1 TB in the default build) it is optional overflow only.
- **Current pick:** STACK v1 names no SKU. Its $25-82 band traces to Samsung PRO Endurance prices (reaudit_D: Slickdeals tracker), so the concrete reference is Samsung PRO Endurance (2022) 128 GB, MB-MJ128KA/EU (EAN 8806092767256). Specs from the Samsung 2024 PRO Endurance datasheet v1.1, all verified:
  - UHS-I SDR104, Class 10 / U3 / V30
  - up to 100 MB/s read and 40 MB/s write
  - endurance 70,080 h of Full HD at 26 Mbps (3.25 MB/s), which is about 820 TB of sequential writes
  - operating -25 to 85 C
  - 5-year limited warranty for 128 GB and 256 GB
  The 256 GB card is rated 140,160 h, also with 5 years.
- **Current price usd:** The STACK band of $25-82 is not supported by any source. Real prices for the 128 GB card on 18 Oct 2026, incl. VAT (1 EUR = 1.1241 USD):
  - arvutitark.ee (EE): EUR 63.85 = $71.77, 276 pcs available to order, 2-5 working days. The page does not say whether VAT is included, and shipping to the user's country is not verified.
  - Reichelt (DE): EUR 64.95 = $73.01, currently unavailable.
  - Alternate (DE): EUR 77.90 = $87.57, 1 pc in stock, shipping from EUR 7.99.
  - eBay.de: new from EUR 78.99-80.46 = $88.79-90.45.
  - MediaMarkt BE: EUR 59.99 = $67.43 seen only in a search snippet (page 403), NOT verified.
  - 256 GB: Reichelt EUR 129 = $145.01, unavailable.
  Realistic range for 128 GB: $71.77-87.57.
- **Decision:** keep
- **Chosen:** KEEP the current part, pinned to a concrete SKU: Samsung PRO Endurance (2022) microSDXC 128 GB, MB-MJ128KA/EU (EAN 8806092767256).
  Where to buy:
  1. Reichelt, if restocked (EUR 64.95). It can ride the planned Reichelt order for the rescue cards and the Goobay A-A cable, so it adds no extra shipping.
  2. Otherwise arvutitark.ee (EUR 63.85, once shipping is confirmed) or Alternate (EUR 77.90, 1 pc).
  Still optional/deferred in the with-Lime default build. No cheaper card survived the not-worse test.
- **Chosen price usd:** 71.77-87.57 incl. VAT (EUR 63.85-77.90), plus shipping. $73.01 at Reichelt once restocked.
- **Saving usd:** 0 (kept). The cheaper SanDisk High Endurance 128 GB ($42.60) would save about $29-45, but only by giving up 7x of rated endurance and 3 years of warranty. It is NOT a not-worse analog (see rejected).
- **Equivalence proof:** The specs that matter for this role are: capacity of 128 GB or more; UHS-I (the Q6A slot is the ceiling: 61.45 MB/s write and 73.7 MB/s read measured, Geerling #85); a guaranteed V30 sustained write (30 MB/s), above the 13.3 MB/s worst disk stream; rated write of at least 40 MB/s; rated endurance for continuous writing; a warranty that covers continuous recording; operating -25 to 85 C; the standard Linux mmc driver; and genuine EU retail supply.
  
  The decisive axis is endurance plus warranty. The Samsung and SanDisk High Endurance datasheets use the SAME basis (Full HD at 26 Mbps = 3.25 MB/s), so their hours can be compared directly:
  - Samsung PRO Endurance 128 GB: 70,080 h, about 820 TB, about 6,400 full-card writes. 5-year warranty.
  - SanDisk High Endurance 128 GB: 10,000 h, about 117 TB, about 914 full-card writes. 2-year warranty (SanDisk set-up sheet, Rev. 04/19). This is 7x lower.
  Angle A's '20,000 h for 128 GB' is wrong: 20,000 h is the 256 GB figure, and Berrybase/Reichelt copy the family maximum.
  
  Every other candidate is either worse on at least one of rated endurance, warranty or speed class, or cannot be priced and bought today (details in rejected).
  
  So no cheaper card is equal or better on every relevant spec, and the reference stays.
  
  There are no electrical, driver or mechanical differences to prove, because the part is unchanged. One reference figure: the Samsung datasheet gives SDR104 at 1.8 V with a maximum of 800 mA, which is the same load as before.
- **Rejected:**
  1.
    - **Name:** SanDisk High Endurance 128 GB SDSQQNR-128G-GN6IA (Berrybase EUR 37.90 = $42.60, 48 in stock; Reichelt EUR 38.95, unavailable)
    - **Why:** Worse on rated endurance and warranty. The datasheet gives 10,000 h at 26 Mbps (about 117 TB) against Samsung's 70,080 h at the same 26 Mbps (about 820 TB), and a 2-year warranty against 5. Retailers that list 20,000 h are quoting the 256 GB figure. Price and stock are real. It is only an explicit downgrade the user could choose, never a silent swap.
  2.
    - **Name:** SanDisk High Endurance 256 GB SDSQQNR-256G-GN6IA (Berrybase EUR 73.90 = $83.07)
    - **Why:** Worse: 20,000 h (about 234 TB) against 70,080 h, and a 2-year warranty against 5. It is also not cheaper than the reference at arvutitark or Reichelt.
  3.
    - **Name:** SanDisk Max Endurance 128 GB SDSQQVR-128G-GN6IA (Reichelt EUR 71.95 = $80.88, limited stock; Welectron EUR 61.90 = $69.58, out of stock)
    - **Why:** Rated 60,000 h (SanDisk footnote via Welectron) against Samsung's 70,080 h, about 14% lower, and the bitrate basis is not stated, so it cannot be proven not-worse. The warranty is inconsistent: Welectron says 3 years, other listings say 10. Reichelt shows 120,000 h, which is the 256 GB figure. Where it is in stock, it is not cheaper than the reference.
  4.
    - **Name:** ADATA High Endurance 128 GB AUSDX128GUI3V30SHA2-RA1 (Alternate EUR 59.90 = $67.33, 9-15 business-day lead)
    - **Why:** Worse on warranty: 2 years (dateks.lv; galaxus.at gives 24 months) against 5. Its endurance is unproven: ADATA documents give 40,000 h or 80,000 h with no stated basis. Its 80 MB/s write gives nothing over the 61 MB/s slot limit and does not offset that.
  5.
    - **Name:** KIOXIA EXCERIA HIGH ENDURANCE 128 GB LMHE1G128GG2 (TME, 0 stock, price aggregate only)
    - **Why:** Worse on warranty: 3 years at retailers. Its endurance is lower: the family figure is about 40,000 h at 256 GB, and Kioxia gives no 128 GB figure. Its price is not real today: zero stock and no qty-1 price.
  6.
    - **Name:** Kingston High Endurance SDCE/128GB (Reichelt EUR 20.95, unavailable/stale; Alternate EUR 77.90)
    - **Why:** Worse on speed class: UHS-I U1 / Class 10 with no V30 (Kingston datasheet), so only 10 MB/s is guaranteed, below the 13.3 MB/s stream, against V30's 30 MB/s. The EUR 20.95 price cannot be bought today.
  7.
    - **Name:** Samsung PRO Plus 128 GB MB-MD128SA (Reichelt EUR 41.95 = $47.16)
    - **Why:** Has no endurance rating. Samsung's warranty excludes continuous recording and data logging, so it effectively has no warranty in this role, against 5 years for the reference.
  8.
    - **Name:** Hiksemi GUARD PRO / GUARD / CITY
    - **Why:** 2-year warranty, or a 0-70 C operating range (GUARD, CITY). No published endurance and no independent measurement. EU price not verified.
  9.
    - **Name:** Unbranded or marketplace 'endurance' cards; used or pulled endurance cards
    - **Why:** Counterfeit and fake-capacity risk, unknown remaining wear (no wear telemetry is readable in Linux), and the warranty needs the original proof of purchase. This breaks the 'legally sold, not counterfeit' and 'not worse' rules.
  10.
    - **Name:** DIY: no card, overflow to T7 + UFS ($0)
    - **Why:** Not like-for-like:
  - The T7 is rated 0-60 C, against -25 to 85 C.
  - The T7 is deauthorized during L-band, S-band and GNSS sessions (operator note 7), so it cannot take overflow then.
  - The second snapshot copy loses its independent medium.
  This is an explicit trade-off for the user, not an analog.
  11.
    - **Name:** DIY: reuse the 64 GB rescue card
    - **Why:** 64 GB is below the 128 GB minimum, and it has no endurance rating. A bootable rescue card left in the slot takes over boot (USB > SD > ... > UFS).
- **Confidence:** high
- **Conditions or tests:** This is a keep, so there is no replacement condition. On-arrival gate for the kept card:
  1. Read /sys/block/mmcblk*/device/{manfid,oemid,name}. Expect Samsung manfid 0x00001b and oemid 0x534d ('SM'). These are commonly reported values; confirm them on the card.
  2. Run a full-card f3write/f3read.
  3. On the Q6A, run a 30-minute sequential fio write with preallocated files. Pass: at least 30 MB/s sustained, no stall longer than 1 s, and zero I/O errors.
  4. Format ext4 or exFAT with no ESP. Do a cold boot with the card inserted and confirm the board boots from UFS (20-boot acceptance as in STACK).
  5. Do a power-cut drill during a write and confirm the filesystem recovers.
  6. Before ordering, confirm that arvutitark.ee ships to the user's country and shows VAT-inclusive pricing; otherwise use Reichelt (when restocked) or Alternate.
  7. Buy only when the T7 is absent, or when a separate snapshot medium is wanted.
- **Stack changes:** 1. BOM row 'Друге сховище' (STACK line 297):
  - Replace the generic name with 'Samsung PRO Endurance (2022) 128 GB MB-MJ128KA/EU'.
  - Replace the price '25-82' with '71.77-87.57 (EUR 63.85-77.90 incl. VAT; Reichelt EUR 64.95 = $73.01 when restocked); verified 18 Oct 2026'.
  - Keep it optional/deferred in the with-Lime default.
  2. Update the 'microSD $25-82' text in the group total note (line 302) to match.
  3. Add the corrections to v2:
  - The SanDisk High Endurance 128 GB is rated 10,000 h, not 20,000 h.
  - Reichelt titles SDSQQNR (High Endurance) as 'Max Endurance', and shows 120,000 h (the 256 GB figure) on SDSQQVR-128G. Order by part number.
  4. If the user ever wants the cheaper SanDisk High Endurance 128 GB ($42.60), record it as an explicit downgrade (7x lower rated endurance, 2-year warranty), never as an equal analog.
  5. No changes to rails, connectors, drivers (standard sdhci-msm/mmc) or the case. The slot, the no-ESP rule and the boot-order rule are unchanged.
- **Sources:**
  - https://download.semiconductor.samsung.com/resources/data-sheet/2024_Samsung_Data_sheet_microSD_Card_PRO_Endurance_v.1.1.pdf
  - https://media.bechtle.com/asrc/180712/1c4b3d4ee288fc9434f5175bf56070570/c3/-/bf1810916b55428dbd0b01cf136c1cea/microsdxc-64-go-sandisk-high-endurance-fiche-technique-1
  - https://www.reichelt.com/de/en/shop/product/microsdxc_memory_card_128gb_samsung_pro_endurance-336143
  - https://www.arvutitark.ee/en/photo-and-videocameras/malukaardid/samsung-pro-endurance-mb-mj128kaeu-128-gb-microsd-memory-c-1129634
  - https://www.alternate.de/Samsung/PRO-Endurance-128-GB-microSDXC-2022-Speicherkarte/html/product/1843451
  - https://www.ebay.de/p/22054814207
  - https://www.mediamarkt.be/en/product/_samsung-memory-card-microsd-pro-endurance-128-gb-v30-2022-mb-mj128kaeu-128-gb-2033052.html (snippet only, 403, unverified)
  - https://www.berrybase.de/en/sandisk-high-endurance-microsdxc-uhs-i-u3-memory-card-adapter-128gb
  - https://www.reichelt.com/de/en/shop/product/microsdhc_memory_card_128_gb_sandisk_max_endurance-298162
  - https://www.welectron.com/SanDisk-Max-Endurance-microSD-Card
  - https://katalog.atcomp.cz/katalog/205A000001080/HE.pdf
  - https://www.dateks.lv/en/cenas/flash-karsu-lasitaji/624686-adata-128gb-microsdxc-with-adapter
  - https://personal.kioxia.com/en-emea/micro-sd/exceria-high-endurance.html
  - https://www.inet.se/produkt/5303196/kioxia-exceria-high-endurance-microsd-128gb
  - https://www.tme.eu/en/details/lmhe1g128gg2/memory-cards/kioxia/
  - https://www.kingston.com/datasheets/SDCE_us.pdf
  - https://semiconductor.samsung.com/consumer-storage/support/warranty/
  - https://github.com/geerlingguy/sbc-reviews/issues/85
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/g6_parts/v30_endurance_microsd_128_256_gb.json

