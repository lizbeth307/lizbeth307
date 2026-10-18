# Tinysa ultra zs407: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** tinySA Ultra+ ZS407 (spectrum analyser, conducted-only small-signal generator and reference channel-power meter; Bench tier, Lab instruments, qty 1)
- **Current pick:** tinySA Ultra+ ZS407 from Astroradio (ES, on the tinySA.org list). Store API check on 18 Oct 2026: 'Hay existencias' (in stock), product id 219649.
- **Current price usd:** $204.28 ex VAT (EUR 181.73) / $247.18 incl. 21% ES VAT (EUR 219.89); EUR 215.50 by bank transfer. That $247.18 is the landed price only for mainland Spain. For other countries Astroradio's own cart adds GLS shipping, a fixed EUR 5.92 'Insurance' fee and 21% ES VAT on the shipping. Landed totals: PT EUR 227.89 ($256.17); DE and FR EUR 244.81 ($275.19); NL, IT, AT and BE EUR 247.89 ($278.65); PL and CZ EUR 249.93 ($280.95). Source: WooCommerce Store API cart, 18 Oct 2026.
- **Decision:** replace_conditionally
- **Chosen:** The same genuine SKU from a cheaper seller; the part itself does not change. Primary: Elektor (NL), 'tinySA Ultra+ ZS407 Spectrum Analyzer', SKU 21021, vendor 'tinySA', allowed only under the conditions below. If the delivery address is in Poland, take GOTRONIK (on the tinySA.org list) instead: SKU TINYSA-ULTRA-ZS407, EAN 5902186301931, PLN 899.00 gross. If no condition is met, keep Astroradio.
- **Chosen price usd:** Elektor: EUR 196.02 incl. VAT = $220.35. Elektor says all prices include VAT. Ex VAT is EUR 162.00 = $182.10, my inference: 196.02/1.21 comes out exactly. Elektor charges a flat shipping fee (Shopify shipping_rates.json, 18 Oct 2026): EUR 7.95 to NL and DE, EUR 9.95 to FR, AT and BE, EUR 12.95 to ES, IT, PL and CZ. Landed: $229.28 (NL/DE), $231.53 (FR/AT/BE), $234.90 (ES/IT/PL/CZ). Not checked: whether checkout VAT changes for non-NL addresses. GOTRONIK (Poland only): PLN 730.89 net / 899.00 gross = $188.01 / $231.25 at 4.3700 PLN/EUR. InPost delivery in Poland costs PLN 0.00.
- **Saving usd:** Elektor, item price ex VAT: $22.18. Elektor against Astroradio, landed to the same country: ES mainland $12.28; FR $43.66; IT $43.75; DE $45.91; PL and CZ $46.04; AT and BE $47.12; NL $49.37. GOTRONIK (Poland only): $16.27 ex VAT; $49.70 landed against Astroradio delivered to Poland, and $3.65 cheaper than Elektor delivered to Poland.
- **Equivalence proof:** It is the identical product, so no spec is traded. Elektor's product JSON (elektor.com/products/tinysa-ultra-zs407-spectrum-analyzer.js) repeats the tinySA.org specification line for line. I checked it against tinySA.org TinySA4.Specification and zeenko.tech/tinysa:
  - Frequency: 0.1-900 MHz normal; ULTRA to 7.3 GHz, level-calibrated to 7.3 GHz.
  - Input: 50 Ohm at 10 dB attenuation or more; 0-31 dB attenuator; +/-5 V DC max; +6 dBm absolute max at 0 dB; +20 dBm peak at 30 dB.
  - Linearity: IIP3 +15 dBm; P1dB -1 dBm.
  - Level: 0.5 dB resolution; linearity +/-2 dB below 5.3 GHz and +/-5 dB from 5.3 to 6 GHz; +/-2 dB absolute after calibration.
  - LNA and sensitivity: 20 dB LNA with NF 5 dB up to 6 GHz (the ZS407 figure); LDS -102 dBm (30 kHz RBW) and -145 dBm (200 Hz RBW with LNA).
  - Purity and timing: phase noise -108/-115 dBc/Hz; SFDR 70 dB; RBW 0.2-850 kHz; 50 us burst.
  - Generator: sine 0.1-900 MHz with harmonics below -40 dBc; -115 to -19 dBm; +/-2 dB from -72 to -19 dBm up to 800 MHz; 57.2 Hz resolution; AM/FM; square wave to 6 GHz; test signal to 7.3 GHz.
  
  The kit matches the genuine Zeenko kit: 2 SMA cables, a barrel adapter, an SMA antenna, a USB-C cable and a 32 GB microSD card. GOTRONIK sells the same Zeenko SKU with an EAN code.
  
  Compatibility is the same because the device is the same: USB-C CDC command set, tinySA4_v1.4-252-g2b4aa51 firmware, the labd allow-list driver, QtTinySA and the udev match on CDC interface 00. Rails, size and the field case do not change.
  
  The one difference is provenance. Elektor is NOT on the tinySA.org Buying page (last modified 20 May 2026; checked 18 Oct 2026), and tinySA.org says a clone cannot be detected by testing ('You can't!'; the selftest can be patched). So no bench test can prove an Elektor unit is genuine. Only proof of the supply chain qualifies it, which is why the decision is conditional and not a plain replace.
- **Rejected:**
  1.
    - **Name:** Elektor without supply-chain confirmation
    - **Why:** Not on the tinySA.org seller list, so it breaks the stack's authenticity rule (tinySA only from tinySA.org-listed sellers). Its 'in stock' is not real stock evidence: Shopify shows inventory_management null, so the item is always orderable. VAT for non-NL destinations was not checked.
  2.
    - **Name:** GOTRONIK for any delivery address outside Poland
    - **Why:** Its terms (regulamin §5.1) say delivery is only within Poland. The search's 'Chwilowo niedostępny' (out of stock) and '+ kaucja' (deposit) are WRONG: both are hidden display:none elements. The page shows schema InStock, an active add-to-cart button and stock bar 5.gif. It is in stock, but only for Polish addresses.
  3.
    - **Name:** Eleshop ZS-407 (listed seller), EUR 159.46 ex / 192.95 incl. NL VAT from an old snippet
    - **Why:** Not rejected on substance, but it can't be checked: every eleshop.eu/.nl/.de page and the GraphQL endpoint return a Cloudflare 403 challenge. Use it only as condition 2 (checkout check).
  4.
    - **Name:** Zeenko AliExpress factory store 5800447
    - **Why:** The page renders by JavaScript and returned no price. Above EUR 150 there is normal duty, import VAT and the EUR 2 UHF on top, so a lower landed cost than an EU seller is not shown.
  5.
    - **Name:** Neven CZ ZS407
    - **Why:** CZK 5,790 incl. VAT = $267.59, more expensive, and 'Není skladem (0 ks)' (out of stock), checked 18 Oct 2026.
  6.
    - **Name:** Kami teknoloji (TR, listed)
    - **Why:** $260.00 incl. KDV (about $216.67 ex), above Astroradio ex VAT, and non-EU, so import VAT, duty and UHF are added.
  7.
    - **Name:** Selteq (UA, listed)
    - **Why:** UAH 9,486, conversion not checked. Non-EU, so import VAT, duty and UHF are added. Ukrainian prices count only as a reference under the user's rules.
  8.
    - **Name:** R&L (US) $219.95, Mirfield (UK) GBP 189.95, Switch Science (JP) JPY 33,800, Amazon.nl AURSINC EUR 319.99 / SeeSii EUR 366.03
    - **Why:** Not cheaper once landed in the EU: post-Brexit/US/JP import VAT, duty and UHF plus shipping. R&L and Switch Science are also out of stock. STACK's 'Budget: Mirfield' is not a budget option.
  9.
    - **Name:** tinySA Ultra+ ZS406 (Neven $159.65 ex, R&L $169.95, Lab401 EUR 163, Kami $90 reduced)
    - **Why:** Worse: ULTRA to 5.3 GHz, calibrated to 6 GHz (ZS407: 7.3 GHz); square wave to 4.4 GHz (6 GHz); test signal to 5.4 GHz (7.3 GHz); LNA NF rated to 4 GHz (6 GHz). That breaks the 0.8-7.3 GHz survey profile and the 5.8 GHz checks. Lab401 is also not on the list.
  10.
    - **Name:** tinySA Ultra ZS405
    - **Why:** Worse: normal range 800 MHz (900), ULTRA 5.3 GHz (7.3), battery 2 h (3 h), LNA rated to 4 GHz, smaller generator range.
  11.
    - **Name:** tinySA Basic
    - **Why:** Range 0.1-350 MHz and 240-960 MHz only; RBW 3-600 kHz; no LNA to 6 GHz.
  12.
    - **Name:** Unlisted 'tinySA Ultra/Ultra+' sellers (eBay generic, Banggood, TinyRFEquip, TinyRFLab, non-factory AliExpress)
    - **Why:** Counterfeit risk named by tinySA.org (it lists 9 AliExpress clone sellers). Nothing measured shows them equal, the firmware may be patched, and they are not even cheaper (about $200-263).
  13.
    - **Name:** Used ZS407
    - **Why:** No verified listing found, provenance can't be proven, the front end may be damaged, and there is no warranty.
  14.
    - **Name:** SA6 / SA6 Plus / SA8 generic
    - **Why:** Worse: starts at 35 MHz, measures to 4.5 GHz, fixed RBW of about 200 kHz, no LNA or NF routine, no Linux protocol. About EUR 263, so not cheaper.
  15.
    - **Name:** RF Explorer 6G Combo PLUS Slim
    - **Why:** More expensive (about $544), +/-3 dB, tops out at 6.1 GHz, RBW from 2.6 kHz, no generator, different protocol.
  16.
    - **Name:** Siglent SSA3015X Plus and other bench analysers
    - **Why:** About 6x the price, 1.5 GHz, mains-powered, no built-in generator, needs a new driver.
  17.
    - **Name:** RTL-SDR V4L / Airspy HF+ / HackRF as substitute
    - **Why:** No absolute +/-2 dB level, 8-bit, range gaps. HackRF can transmit, which breaks the receive-only rule. The tinySA is what calibrates these SDRs.
- **Confidence:** medium
- **Conditions or tests:** Order deadline: the ZS407 gates the 12 V regulator A/B, so the seller must be settled within 3 working days. Otherwise order from Astroradio (EUR 219.89, or 215.50 by bank transfer).
  1. Delivery address in Poland: buy from GOTRONIK at PLN 899 gross (a promotional price with a countdown). Confirm in the cart that it is in stock. No authenticity condition, because GOTRONIK is on the list.
  2. Any other EU address: first check Eleshop (on the list) at checkout. The model must be ZS-407, not ZS-406 (Eleshop sells both as 'Ultra+'), and the landed price must be at or below Elektor's. If so, buy from Eleshop.
  3. Elektor only if all of these hold: (a) written confirmation from Zeenko (mail@zeenko.tech) or tinySA.org that Elektor's ZS407 units come from Zeenko. A statement from Elektor alone is weaker and is acceptable only with an invoice trail naming Zeenko or a listed distributor. (b) Elektor confirms physical stock and a dispatch date, because its store does not track inventory. (c) The checkout total, with VAT recomputed for the destination, is at least $20 below Astroradio delivered to the same address. That holds for every EU country priced above except mainland Spain ($12.28): for Spain, stay with Astroradio.
  4. On arrival, whatever the seller (these are function checks and do NOT prove the unit is genuine):
  - CONFIG > VERSION shows HW V0.5.3 or later and a ZS407 label.
  - Flash tinySA4_v1.4-252-g2b4aa51 and run the selftest.
  - LDS about -102 dBm at 30 MHz, RBW 30 kHz, 50 Ohm load, LNA off.
  - LNA on/off noise floor to 6 GHz.
  - Internal calibration output level against a VNA-measured pad.
  - Check the labd CDC interface 00 udev match and QtTinySA on Ubuntu 24.04 arm64 within the return window.
  Limits of this check: the web-search budget was exhausted (one search was refused), so every figure here comes from primary pages and store APIs fetched on 18 Oct 2026. Eleshop and Zeenko AliExpress could not be read.
- **Stack changes:** Hardware, rails, connectors, drivers, firmware, udev and case: no change (same device, 117x72x23 mm, own battery, USB-C CDC).
  Changes to STACK.md, line 342 (Lab instruments table):
  - Delete 'Бюджет: Mirfield $252.98 (GBP 189.95)'. It is not a budget option for an EU buyer.
  - Mark Astroradio's $247.18 as landed for mainland Spain only. Other EU destinations are EUR 227.89-249.93 ($256-281), including GLS shipping and the EUR 5.92 insurance fee.
  - Add GOTRONIK PL as the cheapest listed seller for Polish addresses: $188.01 ex / $231.25 incl., free InPost, in stock.
  - Add Elektor as a conditional seller: $182.10 ex / $220.35 incl. plus EUR 7.95-12.95 flat shipping.
  Changes to STACK.md, line 1134 (authenticity rule): keep 'tinySA.org-listed sellers only'. Elektor counts only as a documented exception, and only with written supply-chain confirmation from Zeenko or tinySA.org.
  Correct the search record: GOTRONIK's 'temporarily unavailable' and '+ kaucja' are hidden page elements.
  Kit note: the Elektor and GOTRONIK kits include an SMA antenna (receive use only). The existing rule still applies: the tinySA generator is never on while an antenna is connected.
- **Sources:**
  - https://tinysa.org/wiki/pmwiki.php?n=Main.Buying
  - https://tinysa.org/wiki/pmwiki.php?n=TinySA4.Specification
  - https://www.zeenko.tech/tinysa
  - https://www.elektor.com/products/tinysa-ultra-zs407-spectrum-analyzer
  - https://www.elektor.com/products/tinysa-ultra-zs407-spectrum-analyzer.js
  - https://www.elektor.com/cart/shipping_rates.json (Shopify cart query, 18 Oct 2026)
  - https://www.elektor.com/pages/service
  - https://www.astroradio.com/p/tinysa-ultra-analizador-de-espectro-plus/
  - https://www.astroradio.com/wp-json/wc/store/v1/products?search=tinysa
  - https://www.astroradio.com/wp-json/wc/store/v1/cart/update-customer (shipping/tax per country, 18 Oct 2026)
  - https://www.gotronik.pl/tinysa-ultra-analizator-widma-100khz-7-3ghz-zs407-zeenko-p-13267.html
  - https://www.gotronik.pl/regulamin-pm-5.html
  - https://www.gotronik.pl/dostawa-pm-3.html
  - https://www.neven.cz/p/tinysa-ultra-zs-407-prenosny-spektralni-analyzator-a-generator
  - https://www.kamitekno.com/Arama?kelime=tinysa
  - https://selteq.com.ua/en/?s=tinysa&post_type=product
  - https://eleshop.eu/tinysa-ultra-zs-407-spectrum-analyser.html (HTTP 403 Cloudflare, unverified)
  - https://zeenko.aliexpress.com/store/5800447/pages/all-items.html?SearchText=tinysa (JS-only, unverified)
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md

