# Hantek 6022be fx2lafw la: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** Bench oscilloscope + logic analyser set: Hantek 6022BE (2 ch, 20 MHz, 8 bit, USB, OpenHantek6022) + generic CY7C68013A 8-ch fx2lafw LA (Tier bench, group Bench electronics, qty 1 set)
- **Current pick:** Hantek 6022BE from The Debug Store (UK) + generic CY7C68013A 8-ch 24 MS/s fx2lafw LA
- **Current price usd:** 141-172 list. Scope: GBP 100 ex VAT / GBP 120 inc VAT = $133-160 (ECB 16 Oct 2026: GBP/USD 1.3335). LA: $8-12. For a Europe-based buyer the UK source also adds import VAT, the EUR 3/item temporary duty (if postal/IOSS), the EUR 2/item UHF (from about 1 Nov 2026) and a courier clearance fee (operator notes 34-35), so the landed cost is above $172. The exact amount is not verified. The Debug Store product and search URLs return 404 today, so the live listing is unconfirmed.
- **Decision:** replace_conditionally
- **Chosen:** The SAME Hantek 6022BE bought from Botland (Polish EU importer), through the consumer storefront botland.de (DE) or botland.com.pl (PL/EU). Not through botland.store, which is B2B-only. The same generic CY7C68013A 8-ch fx2lafw LA is kept unchanged. This changes the seller only: no spec, software or hardware change.
- **Chosen price usd:** 89-102 landed for the set. Scope: botland.de EUR 67.30 incl. 19% DE VAT (EUR 56.55 net) = $75.73, plus GLS EUR 4.69 = $81.0 to Germany. botland.com.pl: PLN 299.00 incl. 23% VAT (PLN 243.09 net) = $77.0 (ECB 16 Oct 2026: 4.37 PLN/EUR, 1.1253 USD/EUR). Other EU countries: EUR 56.55 net plus destination VAT (17-27%), plus GLS EU from EUR 8.07, about $83-90 (model). Plus the unchanged LA at $8-12.
- **Saving usd:** About $52-70 like-for-like ($141 to $89 at the low end, $172 to $102 at the high end), with an extreme range of $39-83 against the list price. The real saving is larger, because the UK source's import VAT, duty, UHF and clearance fee no longer apply.
- **Equivalence proof:** Same model, same hardware class. The Botland listing (botland.com.pl, botland.de and botland.store, all read 18 Oct 2026, SKU UPM-06716) gives: 2 ch, 20 MHz, 48 MS/s, 8 bit, 1 MOhm/25 pF, max input 35 Vpp, DC accuracy +/-3%, USB 2.0 bus-powered, 205 x 120 x 35 mm, two 1x/10x passive probes, USB cable and manual. Every critical spec matches the current pick and the hantek.com 6022BE page (20 MHz, 48 MS/s max, 8 bit, 1 MOhm/25 pF, DC +/-3%, diode-clamp input protection). Spec items that apply to every genuine 6022BE, and so do not differ between sellers:
  - 30 MS/s CH1-only and 15 MS/s 2-channel streaming limit; +/-5 V clipping; DC-coupled only (OpenHantek limitations.md, verified).
  - Hardware ranges 5/2.5/1/0.5 V (sigrok protocol section, verified).
  - Bandwidth below 20 MHz on small ranges (EEVblog figure, not verified by me).
  Software is identical: VID:PID 04b4:6022 (sigrok also lists 04b5:6022 at attach), firmware loaded into RAM on every plug-in (FW0210), OpenHantek6022 arm64 .deb, sigrok hantek-6xxx. The LA is unchanged. Purchase terms are better: 24-month warranty plus a 30-day consumer withdrawal right on botland.com.pl and botland.de (verified), against a post-Brexit UK cross-border purchase.
  Hard rules kept: passive instrument; the only output is the 1 kHz probe-comp signal, used into the probe only; no loops or H-field probes.
  What I could NOT disprove, and why the replacement is only conditional:
  - The GPSR 'manufacturer' field on all three Botland sites is 'SHEN ZHEN YOU MAI KE TECHNOLOGY CO LTD' (Longhua, Shenzhen), not Qingdao Hantek Electronic Co., Ltd. (Qingdao address, verified on hantek.com/contact). Hantek lists no distributors, only an Amazon official store, so genuineness cannot be proven before purchase.
  - Stock shows conflicting messages: botland.de search says 'currently unavailable' while the product page says 'Auf Lager' and InStock. The live price widget failed to load, so the prices come from the page's structured data.
- **Conditions or tests:** BEFORE ORDER:
  (1) Order as a private buyer on botland.de (DE address) or botland.com.pl (PL or other EU, if the checkout accepts your country). botland.store does not qualify ('sells to registered businesses only', VAT ID required).
  (2) Checkout shows the item in stock and a landed total of EUR 80 or less for the scope.
  (3) Buy the LA from an EU seller, or accept the AliExpress landed cost: price + IOSS VAT + EUR 3 duty + EUR 2 UHF.
  
  ON ARRIVAL, inside the 30-day withdrawal window:
  (a) Authenticity:
  - The case is Hantek-labelled, with a model and serial label and CE marking.
  - Open the case: the PCB must match the sigrok teardown (AD9288 dual ADC, 4x AD8065, Mornsun A0505S-2WR2 isolated DC-DC, CY7C68013A-100AXC, 2x 74HC4051, 24LC02 EEPROM, 24 MHz crystal). Any substitution means a possible clone: return it.
  (b) lsusb shows 04b4:6022 (or 04b5:6022) before firmware load. On the Q6A (Ubuntu 24.04 arm64), OpenHantek6022 3.4.1-rc2 loads FW0210, and sigrok hantek-6xxx also works after a replug.
  (c) Offset calibration with shorted inputs; the 1 kHz probe-comp square is clean with the x10 probe after compensation.
  (d) Conducted-only bandwidth check:
  - Source: tinySA generator in low-output mode into a 50 Ohm feed-through, with no antenna connected anywhere.
  - Setup: CH1 only at 30 MS/s on the +/-0.5 V range.
  - Pass: -3 dB at 8 MHz or above relative to 100 kHz. This threshold is my estimate from the unverified EEVblog figure (a bit under 10 MHz at 100 mV/div). If a known-good 6022BE is available, compare against it instead.
  (e) DC accuracy within +/-3% against the AN8008 at about 5 V (x1) and about 13 V (x10 probe).
  (f) Open-input noise at 20 mV/div is no more than about 10 mVpp (forum figure, unverified). Record it as the unit's baseline.
  (g) Current draw on the FNB58 is 0.5 A or less at 5 V. A 10-minute 2-channel 15 MS/s stream through the bench hub runs with zero overruns, while the LA runs a 24 MS/s capture alongside.
  
  Any failure: return to Botland within 30 days and fall back to the current source (The Debug Store; re-check that its listing is live, since its URLs return 404 today).
- **Rejected:**
  1.
    - **Name:** Hantek 6022BE via botland.store (EUR 67.30, EUR 56.55 net)
    - **Why:** Same item, but the store states 'This store sells to registered businesses only' and requires a VAT ID, so a private buyer cannot use it. Use botland.de or botland.com.pl instead.
  2.
    - **Name:** Hantek 6022BE from AliExpress listings titled 'Hantek Official Store' ($87.12) / 'Hantek Official Shop' ($92.62)
    - **Why:** Costs more than Botland even before IOSS VAT, the EUR 3 duty and the EUR 2 UHF. hantek.com links only an Amazon official store (verified), so 'official' appears only in the listing titles. There is no 30-day EU withdrawal right or EU importer.
  3.
    - **Name:** Hantek 6022BE from unnamed AliExpress stores ($59.99-74.69, US-region prices)
    - **Why:** The EU landed cost (about 21% IOSS VAT + EUR 3 duty + EUR 2 UHF) is about $78-96, roughly the same as Botland's $81-90. There is no store attribution, so it fails the counterfeit and build-quality rule before purchase. No EU warranty or withdrawal right.
  4.
    - **Name:** Hantek 6022BL (scope + 16-ch LA in one unit)
    - **Why:** Worse in simultaneity: the OpenHantek README (verified) says it 'can either be used as oscilloscope or as logic analyzer, but not both at the same time' (H/P button at plug-in), which breaks the labd Bench profile of scope plus LA together. The LA moves into a 200 x 100 x 35 mm box instead of a dongle on the LAB USB port. Its front end differs and has no measured equality. Store unconfirmed. Not cheaper ($84-102) than the Botland BE + LA.
  5.
    - **Name:** Used Hantek 6022BE / Voltcraft DSO-2020
    - **Why:** Price not verifiable (eBay and Kleinanzeigen return 403). No warranty against 24 months new. Probes may be missing. Earlier over-voltage damage to the front end is invisible. Cannot be shown not-worse.
  6.
    - **Name:** SainSmart DDS120
    - **Why:** The OpenHantek README (verified) says it 'has a different analog front end' with modified sigrok firmware and 'some limitations'. Price and availability unverified (SainSmart returned 429).
  7.
    - **Name:** OWON VDS1022 / VDS1022I
    - **Why:** Price unverified (OWON site 503, no EU listing found). Not supported by OpenHantek or sigrok, so it breaks the pinned labd tooling and procedures; the community arm64 driver is untested on the Q6A. Record length unverified.
  8.
    - **Name:** Joy-IT Scope Mega50 (reichelt, JOY-IT SCOPE M50, EUR 128.30 incl. 19% VAT, in stock)
    - **Why:** Found in this pass. About $144, so not cheaper than Botland's 6022BE ($76-90). Linux arm64 and sigrok/OpenHantek support not shown.
  9.
    - **Name:** Raspberry Pi Pico DIY LA (gusmanb LogicAnalyzer / sigrok-pico) in place of the FX2 LA
    - **Why:** Buffered block capture (at most 131,071 samples in 8-ch mode) instead of fx2lafw streaming, which breaks the 24 h PPS-to-NMEA log. sigrok-pico needs sigrok newer than noble's PulseView 0.4.2 / sigrok-cli 0.7.2. Saves $5 at most.
  10.
    - **Name:** Buffered MCU123-type FX2 LA (74HC245) as a cheaper LA
    - **Why:** Same $5-10 price class as the current generic LA (sigrok wiki), so there is no saving. The sigrok page lists a CY7C68013-56PVC with an NXP 74HC245 and fixed VIH 2.0 V / VIL 0.8 V, but whether it really tolerates 5 V depends on the buffer supply, which is not documented (the claimed 0925:3881 VID:PID is also not on that page). Acceptable as the same-price generic LA; not a replacement.
  11.
    - **Name:** Voltcraft DSO-2020 USB (new, 6022BE rebadge)
    - **Why:** Conrad listing blocked (403), so the price and current availability are unverified.
- **Confidence:** medium
- **Stack changes:** BOM/sourcing (STACK line 349 and procurement week 2-3, line 1125):
  - Seller for the 6022BE becomes Botland: botland.de for DE consumers, or botland.com.pl (EU importer BOTLAND B. DERKACZ SP. K., Gola 25A, Bralin, PL).
  - Scope $76-90 landed; set $89-102 instead of $141-172. This follows the EU-stock preference in operator notes 34-35.
  - Buy the LA from an EU seller where possible. From AliExpress, add IOSS VAT + EUR 3 duty + EUR 2 UHF (about $12-18 landed).
  
  Remove the '6022BL on AliExpress $84-102' budget note, and the 6022BL from the lab budget minimum (line 373). It is rejected on simultaneity; replace it with the Botland 6022BE + LA ($89-102, net change about +$0-5 on that line).
  
  Authenticity section (line 1134): Hantek from Botland is accepted only after the arrival teardown and the checks in conditions_or_tests. Note that the GPSR manufacturer field names a Shenzhen trading company, not Qingdao Hantek.
  
  Spec corrections for v2 (they apply to every 6022BE):
  - Usable streaming is 30 MS/s CH1-only and 15 MS/s 2-channel.
  - Hardware full-scale ranges are 5/2.5/1/0.5 V; 20 and 50 mV/div are digital zoom.
  - Input is DC-coupled only.
  Knock-on: the G4 ripple test in analogs_G3 ('Hantek 6022BE, AC-coupled') needs one of these added to the bench kit: a BNC DC-block, the documented OpenHantek AC-coupling hardware mod, or the CHx AC math mode. On DC coupling a 20 V rail cannot resolve 33 mV rms ripple. DC-block price and part are not verified.
  
  udev: check that 60-openhantek.rules also covers 04b5:6022, which sigrok lists as an alternative attach ID.
  
  No change to rails, the USB power budget (LAB port TPS2553 about 0.75 A), connectors, drivers, the Pelican 1450 layout or the labd Bench profile.
- **Sources:**
  - https://botland.com.pl/oscyloskopy/6716-oscyloskop-hantek-6022be-usb-pc-20mhz-2-kanaly-5904422359867.html
  - https://botland.de/oszilloskope/6716-hantek-6022be-usb-pc-20mhz-oszilloskop-2-kanale-5904422359867.html
  - https://botland.de/suche?s=hantek+6022
  - https://botland.store/oscilloscopes/6716-oscilloscope-hantek-6022be-usb-pc-20mhz-2-channels-5904422359867.html
  - https://botland.com.pl/szukaj?s=analizator+stan%C3%B3w+logicznych
  - https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
  - https://www.hantek.com/products/detail/31
  - https://www.hantek.com/contact
  - https://sigrok.org/wiki/Hantek_6022BE
  - https://sigrok.org/wiki/MCU123_Saleae_Logic_clone
  - https://raw.githubusercontent.com/OpenHantek/OpenHantek6022/main/README.md
  - https://raw.githubusercontent.com/OpenHantek/OpenHantek6022/main/docs/limitations.md
  - https://www.reichelt.de/de/de/shop/produkt/usb-oszilloskop_mega50_48_mhz_8-bit_2_kanaele-209715
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/analogs_G3_power_gnss_imu.json
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md
  - NOT VERIFIED IN THIS PASS: the shared WebSearch budget was used up (0 searches ran). These pages failed to load: The Debug Store product and search URLs (404), Amazon.de (503), AZ-Delivery (429) and the TinyTronics category pages (404). The EEVblog bandwidth and noise figures were not re-checked.

