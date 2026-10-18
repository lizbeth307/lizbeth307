# Sma torque wrench 0 9 n m adapter set: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** SMA torque wrench 0.9 N·m (8 mm / 5/16 in, break-over) + SMA adapter set. Bench tier, RF accessories, qty 1 set.
- **Current pick:** TOJOIN 5/16 in SMA torque wrench, 0.9 N·m, 8 mm, break-over (eBay item 354598266754, TOJOIN Official Store, ships from Texas). Plus an RTL-SDR Blog SMA adapter set: Straight ($14.95, 6 pcs) or Semi-Rigid RG402 ($26.95, 10 pcs).
- **Current price usd:** 50.84-62.84 = wrench $35.89 + adapter set $14.95-26.95. The wrench price comes from earlier eBay snippets. I could not re-verify it: eBay returned 403 to both WebFetch and curl on 18 Oct 2026, so the listing is still unconfirmed and needs a manual check. On rtl-sdr.com on 18 Oct 2026 I confirmed the Straight set at $14.95 (9 in stock) and the RG402 set at $26.95 (4 in stock). Estimated EU landed cost of the wrench, which ships from the US: about $49. This assumes about 21% import VAT via IOSS, the EUR 3 per-line duty and the EUR 2 handling fee from about 1 Nov 2026 (operator notes 34-35).
- **Decision:** keep
- **Chosen:** KEEP the current part. Every candidate is either dearer or fails to prove a stated 0.9 N·m preset. Wrench: TOJOIN 0.9 N·m. Adapters: the RTL-SDR Blog set, from the official store only.
- **Chosen price usd:** 50.84-62.84 (list). EU landed is roughly $73 with the Straight set: about $49 for the wrench and about $24 for the set, plus unknown shipping. These are estimates.
- **Saving usd:** 0
- **Equivalence proof:** No replacement made, so nothing needs proving. These specs set the bar:
  (1) Preset 0.9 N·m (8 in-lb) for stainless SMA and 3.5/2.92 mm. Mini-Circuits rates its 086-6SM+, BLK-89-S+ and VAT pads at 8 in-lb max.
  (2) Break-over mechanism, so the joint cannot be over-torqued. Not a click or ratchet type.
  (3) 8 mm (5/16 in) open steel head.
  (4) A stated tolerance. TOJOIN-type tools have only a reseller claim: VXB's generic copy, which I fetched, says "Calibrated to 0.9 ±0.1 N·m with 3% torque error", with an internal ball structure and an alloy-steel body.
  (5) Legitimate seller.
  A cheap analog has to state the 0.9 N·m preset. None of the cheaper ones do. The only candidate with a datasheet that beats the TOJOIN (TekBox TBTWR-05NM) costs more for an EU buyer.
  
  Adapter set: the RG402 set is better than the Straight set in strain relief and far-end gender options (the analogs_G1 finding). Each set is the cheapest in its own function, and no third-party set was shown to have equal pin depth or loss. Hard rules are unaffected: these are passive hand tools and adapters, nothing radiates, and no loops are involved.
- **Rejected:**
  1.
    - **Name:** TekBox TBTWR-05NM (break-over, ±0.05 N·m, 8 mm, 0.5 N·m default, 0.9 N·m on request)
    - **Why:** Better on paper but NOT cheaper, so the user's rule excludes it.
  - Datasheet V1.1 (Meilhaus PDF, read with pdftotext): ±0.05 N·m, bidirectional break-over, 5/16 in (8 mm) head, factory default 0.5 N·m, 0.9 N·m or custom torque on request, adjusted by a spring set screw.
  - Lieske: EUR 41.32 net / EUR 49.17 incl. VAT, hand-calibrated, non-accredited certificate on request.
  - EU price: EUR 47.60 incl. VAT at Meilhaus, about $53.5 plus shipping and out of stock (18 Oct 2026). Lieske is EUR 49.17 incl. VAT (about $55.3), stock not shown. Electrokit SE sells only the 0.5 N·m unit (529 SEK incl. 25% VAT, 4 in stock).
  - That is about $4.5-6 or more above the TOJOIN's estimated landed cost of about $49, before TekBox shipping.
  - No EU shop lists a stocked 0.9 N·m SKU. Turning the set screw to 0.9 N·m without a torque reference voids the factory calibration.
  - The US TEquipment price ($36 / $43.20) is unverified (page blocked) and does not apply to an EU buyer.
  - Keep it as the optional 0.5 N·m brass-jack wrench (an addition, not a replacement).
  2.
    - **Name:** gnss.store ELT0491 'Torque Wrench for SMA 8 mm HF Connectors' (Eltehs SIA, Riga, EU stock)
    - **Why:** Proven to be a rebadge with an unstated preset.
  - The product photos (downloaded and viewed) show the engraving 'MXITA SMA-8' on a gold anodised aluminium tube body with a threaded rear end, so it is the AliExpress Mxita tool.
  - Page (Shopify product JSON and HTML, 18 Oct 2026): EUR 24.99 'Tax excluded', more than 10 in stock, datasheet 'Log in to download'.
  - No torque value or tolerance anywhere in the description, and no torque marking in the photos.
  - The same Mxita family has a 3.5-star rating on its 254-sold AliExpress listing, a quality warning.
  - Landed about EUR 30-31 plus shipping (about $34-35+), possibly about $10-15 under the TOJOIN, but the 0.9 N·m spec is unproven.
  - Reopen only if Eltehs supplies a datasheet stating 0.9 N·m at ±0.1 N·m or better AND the unit passes the dead-weight test below.
  3.
    - **Name:** AliExpress Mxita SMA torque wrench, 8 mm (items 3256811968955217, 3256806231826906, 2251832605408705), $21.56-25.71
    - **Why:** Same tool as ELT0491 (see above).
  - No torque stated in the titles.
  - Item pages are bot-blocked (AliExpress 'punish' page on curl), so the variants and preset cannot be checked.
  - The search-page price may be the cheapest variant, not an 8 mm / 0.9 N·m one.
  - 3.5-star rating on the high-volume listing.
  - EU landed adds about 21% VAT plus EUR 3 duty and EUR 2 handling (from about 1 Nov 2026).
  4.
    - **Name:** AliExpress 'AA83 SMA torque wrench 8 mm straight' (item 3256809218457447), $17.87
    - **Why:** Preset torque, tolerance, mechanism and material are all unstated.
  - The item page redirects into a login/cookie loop (50 redirects) and cannot be verified.
  - The search-page price may belong to another variant.
  - Landed in the EU about $27, but an unknown preset fails 'never trade away a spec silently'.
  - The WebSearch budget (shared limit) was exhausted before I could look for third-party specs.
  5.
    - **Name:** AliExpress '920L SMA torque wrench, 6.5/8/20 mm openings' (item 3256808438875101), $13.69
    - **Why:** Torque unstated, and the item page returned a bot challenge.
  - The multi-opening design suggests an adjustable or multi-range tool.
  - EEVblog evidence that this class can arrive mis-set: an eBay 1-3 N·m adjustable SMA wrench at its default of about 1 N·m 'was too much', chipped thread metal and turned a sacrificial adapter (Mechatrommer, 29 Jan 2019).
  - Worse in assured preset.
  6.
    - **Name:** TOJOIN 0.9 N·m open-box (eBay 354284038356), $30.71
    - **Why:** Price and availability are not real-checkable: eBay returned 403 to WebFetch and curl, and the price comes from earlier research, not re-verified.
  - Unknown handling history: a dropped break-over tool can drift, and there is no calibration record.
  - Return terms are unknown.
  - Saving about $5 list (about $6 landed).
  - Fails the reliability criterion unless it is live AND passes the dead-weight test.
  7.
    - **Name:** Used Keysight/Agilent 8710-1765 (8 in-lb, 5/16 in)
    - **Why:** Not worse in spec, but not cheaper: about $75 + $20.58 shipping (sold eBay.de, snippet only).
  - Counterfeit 'Keysight' wrenches circulate.
  - No calibration on used units.
  8.
    - **Name:** Used Utica A5 5/16 in (EEVblog 2018, about $12.50-13)
    - **Why:** No live 2026 listing.
  - The only evidence is TheSteve's qualitative 'break the same as the Keysight ones', with no numbers (re-read on EEVblog 18 Oct 2026).
  - Adjustable: needs user calibration.
  9.
    - **Name:** DIY wrench (EEVblog EMT tube, spring and marble)
    - **Why:** Worse: the builder reports asymmetric release, it is uncalibrated and 'not quite as repeatable as a torque wrench'.
  10.
    - **Name:** VXB 2-pack (same generic 0.9 ±0.1 N·m tool)
    - **Why:** $132.95 (Shopify product JSON, 18 Oct 2026), far dearer.
  11.
    - **Name:** AliExpress ratcheting SMA wrench $51.49; Pasternack PE5011-1; L-com LC-TWC08516; Fairview ST-SMA8; Copper Mountain TW-SMA; Telegaertner 100025826; Keonn ADTL-TW-SMA-09
    - **Why:** Each fails for at least one of these reasons:
  - Dearer: $51.49 to $854 (Telegaertner and Keonn publish no price).
  - Click or ratchet type rather than break-over (Pasternack, L-com, the AliExpress ratchet).
  - Wider tolerance: the Keonn datasheet allows 0.79-1.13 N·m.
  - Not sold or no stock (Copper Mountain, Pasternack).
  12.
    - **Name:** RTL-SDR Blog SMA Straight set ($14.95) as a substitute for the RG402 set ($26.95)
    - **Why:** Worse in strain relief (analogs_G1: rigid N/UHF/BNC bodies lever on the LiteVNA, tinySA and dongle PCB jacks).
  - 6 pieces instead of 10, and no male-gender far ends.
  - Verified on rtl-sdr.com 18 Oct 2026: $14.95, 9 in stock, 6 adapters (SMA-M to N-F, UHF-F, BNC-F, PAL-F, F-F, plus SMA M-M), no loss or VSWR figures.
  - If the Straight set is the line's actual pick, it is already the floor of this line.
  13.
    - **Name:** Generic AliExpress SMA adapter kits or singles; Nooelec singles; sdrstore.eu resale
    - **Why:** AliExpress: no return-loss, pin-depth or plating data, which puts the LiteVNA and tinySA ports at risk, and no PAL adapter in the kits seen. The 24-piece kit costs $27.99. Nooelec singles at $3.95-5.95 each are not cheaper for 6 pieces. sdrstore.eu charges EUR 43-53 for the same RTL-SDR Blog sets.
- **Confidence:** medium
- **Conditions or tests:** ACCEPTANCE TEST for the wrench actually bought (the TOJOIN included, since it has no datasheet):
  - Clamp a stainless SMA barrel or bulkhead and hold the handle horizontal.
  - Hang a water bottle on a thread at a measured radius r and fill it until the wrench breaks over. Torque = m·9.81·r (0.917 kg at 100 mm or 0.765 kg at 120 mm for 0.9 N·m). KrudyZ's EEVblog check, 2 lb at 4 in, equals 8 in-lb.
  - Do 10 breaks in each direction. Accept a mean of 0.81-0.99 N·m and a spread of ±5% or less. Repeat yearly and after any drop.
  - Until it passes, do not use it on VNA calibration joints.
  
  BEFORE BUYING:
  - Open eBay item 354598266754 by hand. It was unreachable here (403). Confirm it is live, the price, that the title says 0.9 N·m / 8 mm, and whether the EU price includes VAT.
  - If the listing is dead, the fallback is the TekBox at 0.9 N·m on order (about $54+), not an unstated AliExpress tool.
  
  LIMITS:
  - The WebSearch budget (shared limit) was exhausted on my first query. Everything above comes from direct WebFetch/curl of primary pages, datasheet PDF text and product photos.
  - AliExpress item pages, eBay, Amazon, eleshop.eu and groups.io were all blocked.
- **Stack changes:** Rails, drivers, connectors and case: no change. These are passive tools, stored in the Pelican lab case RF roll.
  
  Line items to fix in v2:
  (1) Add the 8 mm hold spanner (about $5, unverified). It is in radio_lab but not in this line's price.
  (2) Brass gap (reaudit_D) stays open. Never use the 0.9 N·m wrench on brass PCB jacks (LiteVNA, tinySA, SAWbird, LNA V2, V4L): finger-tight plus connector savers until Zeenko confirms the port torque. Optional add-on, not a replacement: TekBox TBTWR-05NM at its default 0.5 N·m, ±0.05 N·m:
    - Electrokit SE: 529 SEK incl. VAT, 4 in stock.
    - Lieske: EUR 49.17 incl. VAT.
  (3) Adapter-set overlap. The cable line (analogs_G1) already keeps the RTL-SDR Blog Pigtail Adapter Set ($18.95) with the same far-end types. If this line's set is kept, make it the RG402 set ($26.95), which has strain relief and both genders, not the Straight set. Also add the parts neither set contains:
    - an SMA F-F barrel for the SOLT thru (radio_lab procedure)
    - SMA connector savers
    Screen every adapter on the LiteVNA, accepting 0.3 dB or less at 2.3 GHz.
  (4) EU landed cost (operator notes 34-35): the TOJOIN ships from the US and rtl-sdr.com from outside the EU. Book about $49 for the wrench and about $24 plus shipping for the Straight set, instead of the list prices. Re-check the start date of the EUR 2 handling fee.
  (5) Add the wrench acceptance test above to the bench bring-up checklist.
- **Sources:**
  - https://www.meilhaus.de/cosmoshop/default/articleMedia/tbtwr/en/Datasheet_Tekbox_TBTWR-05NM_en.pdf
  - https://meilhaus.de/en/tbtwr.htm
  - https://industry-electronics.com/tekbox/tbtwr-05nm-sma-torque-wrench-printview-2113408.htm
  - https://www.electrokit.com/en/momentnyckel-for-sma-kontakter-0.5nm
  - https://gnss.store/products/elt0491
  - https://gnss.store/products/elt0491.js
  - https://gnss.store/cdn/shop/files/torque-wrench-for-sma-8-mm-hf-connectors-8926197.jpg
  - https://vxb.com/products/pro-grade-sma-torque-wrench-set-for-rf-connectors
  - https://www.eevblog.com/forum/rf-microwave/sma-torque-wrench/
  - https://www.rtl-sdr.com/product/rtl-sdr-blog-sma-straight-antenna-adapter-set/
  - https://www.rtl-sdr.com/product/rtl-sdr-blog-semi-rigid-rg402-sma-antenna-adapter-set/
  - https://www.ebay.com/itm/354598266754 (HTTP 403, unverified)
  - https://www.ebay.com/itm/354284038356 (HTTP 403, unverified)
  - https://www.aliexpress.com/item/3256809218457447.html (blocked)
  - https://www.aliexpress.us/item/3256808438875101.html (blocked)
  - https://www.aliexpress.com/item/3256811968955217.html (blocked)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/analogs_G1_receivers_rf.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md

