# Pinecil v2 ironos bluetooth off: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** Soldering iron, Bench tier, Bench electronics, qty 1: Pinecil V2 (PINE64 SKU PINECIL-BB2), IronOS >=2.23 with Bluetooth Off, PD Mode No Dynamic, 60 W limit, non-EPR cable. Fed from the Anker 737 at 20 V. Fallback is DC5525 from the fused 5 A node-N service port (4S, 3.3 V/cell cutoff).
- **Current pick:** Pinecil V2 (PINECIL-BB2) from the PINE64 global store (pine64.com). One ST-B2 tip is included.
- **Current price usd:** 25.99. This is the community price (retail 35.99). In stock on 18 Oct 2026; I re-checked the product page today. Ships from CN/HK. Shipping cost is shown only at checkout (unverified). Per the PINE64 shipping page, the buyer pays import VAT and duties on arrival. EU-stocked sellers of the same part: PINE64 EU EUR 67.50 incl. VAT, free shipping, 2-year warranty, OUT OF STOCK (verified today). Blinkyparts EUR 58.99 incl. VAT plus shipping. Keycapsss EUR 56.00, 'currently not available'.
- **Decision:** keep
- **Chosen:** Keep the Pinecil V2 (PINECIL-BB2), bought new from pine64.com or a PINE64-listed reseller. No candidate is both cheaper and not worse.
- **Chosen price usd:** 25.99 (plus shipping and import VAT, both unverified)
- **Saving usd:** 0.00
- **Equivalence proof:** This is the current part, so it is equal by definition. I tried to break every cheaper candidate on the specs this stack needs. Each one fails at least one; details are in the rejected list.
  
  What the stack needs and how the Pinecil V2 meets it (verified today on pine64.com and the PINE64 wiki):
  - (a) USB-C PD/QC 12-20 V 3 A from the Anker 737. That gives 60 W under the IronOS limit (64 W model with the 6.2 Ohm short tip).
  - (b) A real DC5525 barrel, 12-24 V, centre-positive. This is what the XT30-DC5525 lead on the 5 A-fused 4S service port (STACK D7) plugs into.
  - (c) Peak current on that path is V/R with no DC/DC: 13.6/6.2 = 2.2 A to 16.4/6.2 = 2.65 A. That is well under the 5 A fuse.
  - (d) Open IronOS with a per-cell cutoff (RECOM_VOL_CELL 3.3 V), power limit, PD Mode No Dynamic and Power pulse.
  - (e) TS100-family tips with tip sense, including the heavy 'Gross' sets (BC2/D24/C4) for XT30, SMA and ground planes.
  - (f) 100-400 C. Rear M2x4 earth screw bonds to the iFixit mat.
  - (g) FCC/CE RED/RoHS. Genuine units can be identified: white box, green grip, BL706, Authenticity Checker.
  
  The only cheaper offers are:
  - The SEQURE S60P at 24.50 (-1.49).
  - The SEQURE SI012 Pro Max 'single host without tip' at 25.00 (-0.99, but it has no tip).
  - The FNIRSI HS-01 at 21.99, which needs an unverified coupon; its list price of 25.99 equals the Pinecil.
  
  Each loses at least one of (b), (c), (d) or (e), or stops being cheaper once a tip is added.
  
  Their real advantages, which I did not drop silently:
  - No BLE radio on the S60P and HS-01.
  - 50-500 C range on the S60P.
  - 5.60 USD Sequre tips.
  None of these makes up for losing the barrel input and fuse compatibility, the programmable cutoff, or the heavy-tip range.
  
  Price ranking: Sequre and FNIRSI also ship from China with the same landed-cost terms (operator note 35: price + shipping + import VAT + EUR 3/line + EUR 2 UHF from about 1 Nov 2026). So landed cost does not change the order.
- **Rejected:**
  1.
    - **Name:** SEQURE S60P, 'without power plug' variant (K/I/IS/BC1 tip), sequremall.com, 24.50 USD (compare-at 26.99), in stock per store JSON 18 Oct 2026
    - **Why:** Worse on specs this stack needs:
  (1) No DC5525 barrel. The store page lists only Type-C (PD2/3, QC2/3, PPS, 'DC Max 21V'). The D7 4S fallback would need a raw-DC-on-USB-C lead, which can put 16.4 V on the VBUS of the Q6A or an instrument if misplugged.
  (2) The tip is about 2.5 Ohm (IronOS Sequre configuration.h: 'TIP_RESISTANCE 20 // actually 2.5 ish'; 'We dont have DC/DC but have reallly fast PWM'). At full duty that draws 13.6/2.5 = 5.4 A to 16.4/2.5 = 6.6 A on the 4S path, over the 5 A service-port fuse. At 20 V PD the PWM peaks are about 8 A (model); conducted EMI from this is unmeasured.
  (3) The IronOS README marks the S60P DC unsupported, Tip Sense unsupported and 'Full OLED resolution not yet supported'. The stock firmware publishes no per-cell cutoff.
  (4) Sequre sells only fine C210 tips (K, I, IS, BC1 at 5.60 USD), with no heavy chisel or bevel for XT30, SMA or ground planes.
  (5) No documented earth point on the S60P. Sequre's clamp wire is listed for the S20/S60, and its generic GND set says 'USB spring wire or O-end'.
  (6) It is a sale item. Sequre's refund policy says sale items cannot be refunded, the buyer pays return shipping, and there are no refunds once the parcel is with the courier.
  (7) No independent measurement of temperature accuracy or recovery was found. The search budget was exhausted, so this is unverified, not disproven.
  Its advantages (no BLE, 50-500 C, 22 g, cheaper tips) do not offset (1)-(5).
  2.
    - **Name:** FNIRSI HS-01 (base, no adapter), fnirsi.com, 25.99 USD list (21.99 only with code HS014, which I could not verify; the store JSON shows 25.99)
    - **Why:** Not cheaper at a verified price: it equals the Pinecil.
  Also worse on specs:
  - Closed FNIRSI firmware with no documented per-cell low-voltage cutoff, power limit or PD-mode lock. IronOS does not support it.
  - DC 9-24 V only through a raw-DC Type-C cable, with no barrel (same misplug hazard).
  - Proprietary integrated tips at 14.99 USD each (store JSON) vs about 9-10 USD TS tips, from a single source.
  - No earth point documented. CE/WEEE only. The 'PID accuracy <2%' claim is marketing only.
  - Under 30 USD it misses free shipping.
  3.
    - **Name:** SEQURE SI012 Pro Max, host only 25.00 USD (no tip); with a tip 29.00 (T12-B2) or 31.50 (TS-B2), sequremall.com
    - **Why:** The closest functional analog: DC 12-25 V with an XT60-to-DC5525 lead in the kit, PD3.0, power-limit adjustment, low-voltage protection, and IronOS lists DC as supported.
  But it is not cheaper: the 25.00 USD host has no tip, the Pinecil price includes an ST-B2, and the cheapest bundle with a tip is 29.00 USD (+3.01 over the Pinecil).
  Also worse: IronOS shows no tip sense, it is 188 mm with a tip vs 155 mm, and there are no measurements.
  4.
    - **Name:** SEQURE S99 (C245, 5.5/2.5 Ohm), 26.20 USD
    - **Why:** Not cheaper (+0.21). It has no barrel (raw DC on USB-C). At 20 V it draws about 3.6 A with the 5.5 Ohm tip, which exceeds the stack's 3 A PD rule unless the cable and settings change.
  5.
    - **Name:** SEQURE SI012 / SI012 Pro (DC5525) / SQ-D60B
    - **Why:** None is cheaper. SI012 Pro is 28.00-31.00 USD (store JSON). The SQ-D60B kit is 63.80 USD in my capture of the store JSON (search A quoted 27.80). SI012 is 26.50 per search A.
  6.
    - **Name:** FNIRSI HS-02
    - **Why:** 35.99 USD, not cheaper.
  7.
    - **Name:** Used genuine Pinecil V2 (eBay/Kleinanzeigen/Vinted)
    - **Why:** I found no verifiable listing price: eBay.de returned HTTP 403 to my fetch as well. It has no warranty and may have worn tips or contacts or blown MOSFETs (wiki warning about bad DC bricks). It can be accepted only with an Authenticity Checker pass and a return option, and only at a proven price below 25.99 plus shipping. That is not met, so it is rejected.
  8.
    - **Name:** Pinecil V1 and AliExpress 'Pinecils'
    - **Why:** The PINE64 wiki says 'There are no PINE64 Pinecils sold on AliExpress', so these are counterfeits. V1 is worse anyway: 21 V DC max, 8 Ohm tips giving 50 W at 20 V, no tip sense, and IronOS marks it 'not recommended'.
  9.
    - **Name:** EU-stocked Pinecil V2 (PINE64 EU EUR 67.50, Blinkyparts EUR 58.99, Keycapsss EUR 56.00)
    - **Why:** Same part, not an analog, and 2.2-2.6x the sticker price. Use only if the 2-year EU warranty is wanted and the HK landed cost turns out higher than expected. PINE64 EU is out of stock and Keycapsss is unavailable.
- **Confidence:** high
- **Conditions or tests:** No replacement, so these are the existing re-audit acceptance tests plus authenticity checks.
  1. Authenticity on arrival: white box, black handle with green grip, BL706. Update IronOS to >=2.23 and pass the pinecil.pine64.org Authenticity Checker inside the 30-day warranty.
  2. First boot settings: Bluetooth Off, PD Mode = No Dynamic set explicitly, Power limit 60 W, Power pulse on if the 737 sleeps. The IronOS dev README now says 28 V EPR is disabled by default, while the re-audit read the 2.23 'safe' default as not disabling EPR. The explicit No Dynamic setting covers both readings.
  3. On the 737 with a non-EPR cable, the FNB58 must show 20 V and <=3 A, never 28 V.
  4. D7 path: DC5525 from the fused service port at 13.6-16.4 V with the IronOS 4S cutoff at 3.3 V/cell. Peak current <=2.7 A on the FNB58 or a clamp meter; the 5 A fuse must not blow during heat-up.
  5. Tip-to-earth resistance through the rear M2x4 screw lead to the iFixit mat snap, measured with the AN8008. Record the value (target: a few ohms or less, as in common bench-iron practice, e.g. Sequre's own '<2 Ohm' station spec).
  6. tinySA 2.4 GHz quiet check with the iron on, to confirm no BLE advertising.
  Sourcing: order only from pine64.com or a PINE64-listed reseller. Read shipping at checkout. Landed cost = 25.99 + shipping + import VAT (collected on import, not at checkout) + EUR 3 customs duty per tariff line if postal + EUR 2 Union handling fee (from about 1 Nov 2026) + any carrier handling fee.
- **Stack changes:** None for rails, connectors, drivers or case. Keep the D7 XT30-DC5525 service-port lead, the 60 W / No Dynamic / BT Off settings and the QUIET rule as they are.
  Two text notes for v2:
  (a) The BOM line should state that the 25.99 price excludes shipping, import VAT, the EUR 3 duty and the EUR 2 handling fee, and that EU-stock alternatives are EUR 56-67.50 (PINE64 EU out of stock).
  (b) Add 'buy only from PINE64 or listed resellers; no AliExpress' plus the Authenticity Checker step to the arrival checks.
- **Sources:**
  - https://pine64.com/product/pinecil-smart-mini-portable-soldering-iron/ (fetched 18 Oct 2026: 25.99 community / 35.99 retail, in stock, ST-B2 included, USB-C 12-20 V 3 A, DC5525 12-24 V 3 A, 100-400 C, 30-day warranty)
  - https://pine64.com/shipping/ (ships from CN/HK; customer pays import duties and VAT)
  - https://wiki.pine64.org/wiki/Pinecil (resellers, counterfeit warning, 6.2/8 Ohm power table, DC5525 polarity and limits, M2x4 ground screw)
  - https://pine64eu.com/product/pinecil-smart-mini-portable-soldering-iron/ (EUR 67.50 incl. VAT, out of stock, 2-year warranty)
  - https://shop.blinkyparts.com/en/search?sSearch=pinecil (EUR 58.99 incl. VAT plus shipping)
  - https://keycapsss.com/search?search=pinecil (EUR 56.00, not available; local capture /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/iron_dl/keyc.html)
  - https://raw.githubusercontent.com/Ralim/IronOS/dev/README.md (hardware table: S60P DC unsupported, no tip sense, partial OLED; Si012 Pro Max DC supported; Pinecil V1 not recommended; EPR disabled by default footnote)
  - https://raw.githubusercontent.com/Ralim/IronOS/dev/source/Core/BSP/Sequre/configuration.h (S60P: TIP_RESISTANCE 'actually 2.5 ish', no DC/DC, fast PWM, USB_PD_VMAX 20, 60 W; local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/iron_b_dl/sequre_cfg.h)
  - https://sequremall.com/products/sequer-s60p-upgraded-version-electric-soldering-iron-supports-pd-qc-dc-pps-power-supply-compatible-with-c210-soldering-iron-tip-precision-electronic-mobile-phone-repair-tool-anti-static-soldering-pen-60w (store products JSON capture /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/iron_dl/sequremall.com.json: 24.50 USD, Type-C only, DC max 21 V, K/I/IS/BC1 tips 5.60 USD)
  - https://sequremall.com/policies/refund-policy (sale items non-refundable; buyer pays return shipping)
  - https://sequremall.com/policies/shipping-policy (buyer pays import duties; no refunds once with the courier)
  - https://www.fnirsi.com/products/hs-01 (store JSON capture /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/iron_dl/www.fnirsi.com.json: 25.99 USD, PD 9-20 V 65 W, DC 9-24 V 96 W via Type-C, HS-01 tips 14.99 USD, CE/WEEE)
  - https://www.fnirsi.com/policies/shipping-policy (free shipping over 30 USD; EU duty service under 150 USD)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md items 34-35 (EU landed-cost rule)
  - NOTE: the shared WebSearch budget was exhausted, so no independent measurement reviews (tip temperature accuracy, recovery, tip-to-earth resistance) could be searched for any candidate. eBay.de and eleshop.eu returned HTTP 403.

