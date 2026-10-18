# Radxa ufs 3 1 128 gb ra022 b10j0u2: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_071e1025-145`_

- **Part:** Radxa UFS 3.1 Module 128 GB RA022-B10J0U2 (boot and A/B root storage for the Radxa Dragon Q6A, eMMC/UFS combo connector)
- **Current pick:** Radxa UFS 3.1 128 GB RA022-B10J0U2 from ALLNET China, in stock. Radxa measured it on the Q6A with the Samsung KLUDG4UHDC-B0E1 chip (ID 0x01CE): 1703 MB/s read and 388 MB/s write.
- **Current price usd:** 65.90 ex VAT, in stock. Re-checked live today in the ALLNET Shopify JSON: variant RA022-B10J0U2 price 6590, available=true. Landed in the EU at 19-21 % import VAT this is $78.42-79.74, plus shipping and any carrier handling fee. ALLNET's shipping policy page is empty, so the shipping cost and IOSS handling are unverified.
- **Decision:** keep
- **Chosen:** Keep the same part, Radxa RA022-B10J0U2. No analog survived. The only saving that gives up nothing is buying the identical SKU from a cheaper Radxa-listed partner. For an EU buyer the preferred source is TinyTronics B.V. (NL, Radxa-listed EU distributor), EUR 58.00 incl. VAT, 2-4 week lead time. If Arace restocks at $49 ex VAT before the order, buy there instead, but only if its landed price including shipping beats TinyTronics. ALLNET ($65.90) stays the fallback, for when the UFS is needed before the TinyTronics lead time ends or when the Q6A itself is bought from ALLNET.
- **Chosen price usd:** 65.20 incl. 21 % NL VAT (EUR 58.00); 53.88 ex VAT (EUR 47.93). Re-fetched today: 'Not in stock', 'Availability: 2-4 Weeks', Add to Cart button present. Shipping: NL EUR 2.95-6.95 incl. VAT. Other EU countries EUR 7.29-25.54 ex VAT (for example DE EUR 8.35-8.49, PL EUR 15.05). Marginal shipping is zero only if the UFS travels in the same parcel as the Q6A.
- **Saving usd:** On the part itself: 0, because no analog replaces it. From switching seller to TinyTronics: $12.02 ex VAT (65.90 - 53.88), which is $14.30-14.54 landed at 19-21 % VAT, before ALLNET's unknown shipping and handling. If TinyTronics is compared incl. VAT against ALLNET ex VAT, the nominal gap is only $0.70. If the UFS has to ship as a separate TinyTronics parcel, subtract that parcel's cost: about $3.3-7.8 in NL, or about $10-34 incl. VAT to other EU countries (model). ALLNET's own shipping, which is unknown, would partly offset this. Arace, if restocked: $49.00 ex VAT is $58.31-59.29 landed at 19-21 % VAT, plus unknown Hong Kong shipping. That is about $6-7 below TinyTronics before shipping.
- **Equivalence proof:** The TinyTronics, Arace and ALLNET listings all name the same Radxa manufacturer part number, RA022-B10J0U2. TinyTronics confirms it on its page: 'manufacturer model RA022-B10J0U2', 30 x 22 mm, 1 g, clamp mount. All three sellers are Radxa-listed partners on radxa.com/distributors: TinyTronics B.V. (Netherlands, Europe list) and Allnet and Arace Limited (Global list). Radxa sells this module only through approved partners, so the part is genuine, not a counterfeit, and covered by Radxa's availability guarantee to at least Sep 2035 (brief rev 1.2, section 8). Every spec that matters is therefore identical:
  - Interface: UFS 3.1 JESD220E, 2-lane HS-Gear4, with WriteBooster.
  - Connectors: GB042-30S-H10 for signal and GB042-34S-H10 for mounting only, same pinout per brief rev 1.2.
  - Rails: VCC_3V3, VCC_1V8 and VCC_1V2.
  - Compatibility: the Q6A is on Radxa's list (brief section 7).
  - Speed on the Q6A: 1703/388 MB/s with the Samsung KLUDG4UHDC-B0E1 (Radxa Q6A docs, re-fetched today).
  - Capacity: 128 GB.
  - Same stock 6.18.2-4 kernel path.
  
  Things no source can guarantee, so they are equal across all sources: no seller names the chip vendor (the TinyTronics page lists no chip or speed, and neither does ALLNET), so the day-1 ID check applies wherever it is bought. Correction to the stack: Radxa brief rev 1.2 does NOT state a 0-70 C standard-grade range. It lists only the 'Optional industrial-grade version (-25 C to +85 C)'. The 0-70 C figure stays unverified for every source and should be settled from ufs-hwmon temp1_crit/lcrit on arrival.
- **Rejected:**
  1.
    - **Name:** Same SKU RA022-B10J0U2 from Arace Limited, $49.00 ex VAT
    - **Why:** No spec is worse, but it cannot be bought today: re-checked the live Shopify JSON, variant 'UFS Module 128G' shows available=false, with no restock date. It ships from Hong Kong, so EU VAT and unknown shipping apply. It only becomes the choice if restocked at checkout and cheaper landed than TinyTronics.
  2.
    - **Name:** Radxa UFS 256 GB (Arace RA022-B60J0U4 $49.00; ALLNET RA022-B10J0U4 $75.90)
    - **Why:** Worse in compatibility. Radxa's measured 256 GB uses the Kioxia THGJFGT1E45BAILB, which needs the UFS_DEVICE_QUIRK_PA_TACTIVATE entry from radxa/kernel commit 559f4f9: the commit message says it 'fails to resume from suspend with OCS and PHY adapter errors'. That entry is not in the held 6.18.2-4 (re-audit A: it is on the branch HEAD only), so this module needs the self-built +lab1 kernel or no-suspend plus rpm_lvl=0. It is not cheaper ($49 equals Arace's own 128 GB price; ALLNET's is $10 more). Sold out at both (live JSON). Arace's SKU suffix B60 differs from ALLNET's B10, so the chip in that SKU is unknown.
  3.
    - **Name:** Radxa UFS 64 GB RA022-B10J0U1, $19.00
    - **Why:** Worse in capacity: about 59.6 GiB cannot hold ESP 1 + 2 x 22 GiB roots + about 74 GiB /data (46 GiB recordings + 20 GB NPU quota). Not measured on the Q6A. Sold out at ALLNET and Arace (live JSON).
  4.
    - **Name:** Radxa UFS 512 GB RA022-B10J0U8 (Arace $79.00, ALLNET $89.90)
    - **Why:** Not cheaper, sold out at both (live JSON), chip vendor unknown, so there is a Kioxia quirk risk. Not measured on the Q6A.
  5.
    - **Name:** Radxa eMMC Module Blue Edition 128 GB (Arace $49.99)
    - **Why:** Worse in performance: eMMC 5.1 HS400 has a ceiling of about 400 MB/s, and Radxa's eMMC table shows 217/143 MB/s for 128 GB, against 1703/388 MB/s for the UFS. No WriteBooster. No Q6A-tested eMMC module is named in Radxa's Q6A docs (re-fetched). Sold out. Only $3.89 below TinyTronics ex VAT, and that small saving would cost a large drop in speed.
  6.
    - **Name:** AliExpress 'Radxa UFS Module, Up to 256G' $57.99 (item 3256808897564410) and other listings at $109.89-194.09
    - **Why:** Provenance is unproven: the search page shows no store names, and the item page returned a captcha or 'punish' page, so it is not confirmed as Radxa's official store. It is also unknown which capacity carries $57.99. EU AliExpress orders add VAT at checkout (IOSS; model), so $57.99 becomes about $69-70, above TinyTronics' $65.20. Chip unknown. Rejected on authenticity and price.
  7.
    - **Name:** Hubtronics (India) about $32 (INR 2,815)
    - **Why:** Unverified: the page is behind a Cloudflare challenge (saved snapshot) and a 403. The price comes from a search snippet that showed Stock 0. It is a domestic Indian seller with no confirmed EU shipping.
  8.
    - **Name:** Evelta (India)
    - **Why:** Out of stock (schema.org OutOfStock in the page snapshot), and INR 6,200-7,316 is not cheaper once converted. No EU shipping confirmed.
  9.
    - **Name:** Ameridroid $89.95; Amazon B0FCM5KGX8 $99.00 (third-party reseller); Amazon B0GX92F11S (unavailable)
    - **Why:** More expensive, or not available. The third-party Amazon reseller adds provenance risk.
  10.
    - **Name:** SB Components, IF Blackdevice, RS (other Radxa-listed partners)
    - **Why:** No offer found. SB Components' 'radxa ufs' search JSON lists no UFS module. Blackdevice's site search for 'ufs' returned 0 results. RS returned HTTP 403, so it was not checked.
  11.
    - **Name:** FriendlyElec UFS 2.0 module; generic or clone GB042 modules; DIY BGA153 module; used modules
    - **Why:** FriendlyElec: UFS 2.0 (HS-G3) is slower, and its connector and rails are not proven on the Q6A. No other-brand GB042 module or used listing was found. DIY has no measurements and carries signal-integrity and counterfeit-chip risk. Radxa's Q6A docs say: 'Do not use untested third-party UFS or eMMC modules', which 'may short the board'.
- **Conditions or tests:** 1. At checkout, re-check Arace (variant RA022-B10J0U2) and TinyTronics. Buy at Arace only if it is restocked and its landed price, including shipping and VAT, is below TinyTronics.
  2. TinyTronics: the delivery page does not say whether an out-of-stock line holds the whole order. Put the UFS in a SEPARATE order, or get partial shipment confirmed in writing, so the Q6A (and the Daly BMS) ship at once for the W1-2 board gate. Count that extra parcel's shipping in the saving.
  3. If the Q6A is bought from ALLNET (the non-EU plan), keep the ALLNET UFS in the same parcel instead.
  4. Until the module arrives, boot from microSD, as STACK.md already plans. Make sure that card is actually ordered: the planned card is the ALLNET 64 GB in the recovery kit, so a TinyTronics-only order needs another EU-sourced card.
  5. Within the EU 14-day withdrawal period after the UFS is delivered, on the Q6A:
     - read wManufacturerID and the model. 0x01CE / KLUDG4UHDC means stay on stock 6.18.2-4. 0x0198 means run bench test B13 and the +lab1 kernel;
     - run 10 min of fio;
     - fill to about 70 % to measure sustained write after the WriteBooster cache. The pass floor stays well above 13.3 MB/s and the Lime decimated streams;
     - read the health descriptor (life_time_estimation_a/b, wb_life_time_est);
     - read ufs-hwmon temp1_crit/lcrit to settle the operating range, which brief rev 1.2 does not state.
  6. Because of the lead time, the Q6A's UFS connector may first be exercised after the board's own 14-day withdrawal window. In that case rely on the 2-year EU legal guarantee, or, if the Q6A return window matters more than the saving, buy the in-stock ALLNET unit.
- **Stack changes:** There are no electrical, mechanical, driver or case changes: identical SKU, same connectors, the same 3V3/1V8/1V2 rails, the same stock 6.18.2-4 kernel path, and the same pad to the case boss.
  
  Changes to the BOM and plan:
  - BOM storage row: make TinyTronics (EUR 58 incl. VAT, $65.20 / $53.88 ex VAT, 2-4 weeks) the primary EU source. Keep ALLNET $65.90 ex VAT (about $78.4-79.7 landed) as the in-stock fallback and Arace $49 ex VAT as 'if restocked'.
  - Wave-1 order plan: the TinyTronics UFS goes in a separate order, or with confirmed partial shipment, so it does not hold the Q6A. Its shipping cost is NL EUR 2.95-6.95, or EUR 7.29-25.54 ex VAT to other EU countries.
  - Schedule: move 'UFS chip ID' out of the W1-2 board gate to 'on UFS arrival' (about W3-5). That step covers the ID read, fio, the post-WriteBooster fill and the ufs-hwmon limits.
  - Text corrections:
    - Mark the 'standard 0-70 C' rating as unverified: Radxa brief rev 1.2 names only the optional -25 to +85 C industrial grade.
    - Note that a 512 GB SKU (RA022-B10J0U8) exists, at $79-89.90 and sold out, as a rejected option.
    - The rule 'avoid the 256 GB Kioxia' stands (verified via radxa/kernel 559f4f9).
  
  Limits of this check: the shared WebSearch budget was exhausted after my first query, so these checks used WebFetch and curl on primary pages only. The RS listing, ALLNET's shipping and IOSS terms, and the AliExpress store identity remain unverified.
- **Confidence:** high
- **Sources:**
  - https://shop.allnetchina.cn/products/high-performance-ufs-3-1-module.js (re-fetched 18 Oct 2026: RA022-B10J0U2 $65.90 available=true; U1 $19, U4 $75.90, U8 $89.90 sold out)
  - https://arace.tech/products/radxa-ufs-module.js (re-fetched 18 Oct 2026: 128G RA022-B10J0U2 $49.00 available=false; 256G RA022-B60J0U4 $49.00, 512G $79.00, 64G $19.00, all sold out)
  - https://www.tinytronics.nl/en/data-storage/modules/radxa-ufs-module-128gb (EUR 58.00 incl. VAT / EUR 47.93 ex VAT, 'Not in stock', 'Availability: 2-4 Weeks', model RA022-B10J0U2)
  - https://www.tinytronics.nl/en/delivery-information (shipping NL EUR 2.95-6.95; DE EUR 8.35-8.49, BE EUR 7.29-9.75, PL EUR 15.05 ex VAT; no backorder or partial-shipment policy stated)
  - https://radxa.com/distributors/ (Europe: TinyTronics B.V. NL, IF Blackdevice S.L. ES; Global: Allnet, RS, SB Components, Arace, Radxa Amazon, Radxa AliExpress)
  - https://docs.radxa.com/en/dragon/q6a/hardware-use/ufs-emmc-com (128 GB Samsung KLUDG4UHDC-B0E1 1703/388 MB/s; 256 GB Kioxia THGJFGT1E45BAILB 1811/557 MB/s; untested third-party module warning)
  - https://dl.radxa.com/accessories/ufs-module/rad-doc-0154_radxa_ufs_module_product_brief__revision_1.2_g69c4d5d.pdf (UFS 3.1 JESD220E, 2-lane HS-G4, GB042-30S/34S-H10, 3V3/1V8/1V2, optional -25 to +85 C industrial grade, Q6A in compatibility list, availability to Sep 2035; no standard-grade range stated)
  - https://github.com/radxa/kernel/commit/559f4f921a01e5358602153364c618fe2a3e431e (PA_TACTIVATE quirk for Kioxia THGJFGT1E45BAILB, tested on Q6A)
  - https://www.aliexpress.com/w/wholesale-radxa-ufs-module.html (listings $57.99-194.09, no store names; item page captcha)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/ufs_verify/ (live JSON, brief.pdf/brief.txt, AliExpress captures)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/ufs_dl/ (earlier snapshots: sb.json, bd.html, hub.html Cloudflare challenge, evelta.html OutOfStock)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_A_compute_software.json (Kioxia quirk only on branch HEAD; +lab1 build path)

