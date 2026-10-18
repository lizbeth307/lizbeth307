# Nooelec sawbird goes cased 100792: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e32114dd-52d`_

- **Part:** L-band LNA + SAW filter at the helix/helicone feed (1687-1705 MHz: Meteor HRPT 1700, Metop AHRPT 1701.3, FY-3 1704.5, Elektro-L3 LRIT 1691, FY-2H 1687.5/1690.5). Qty 1, shared by both antenna tiers.
- **Current pick:** Nooelec SAWbird+ GOES cased, SKU 100792
- **Current price usd:** 49.95 (Nooelec direct; re-checked 18 Oct 2026: US$49.95, "Add to Cart", ships in 1 business day, 1-year warranty, aluminium enclosure included). EU import VAT of 19-27% is added on arrival. If Nooelec does not use IOSS, the carrier may also charge a handling fee (not verified). The Nooelec order (NOAA + GOES + Flamingo+) stays above the $100 free-shipping threshold.
- **Decision:** keep
- **Chosen:** Nooelec SAWbird+ GOES cased, SKU 100792 (unchanged)
- **Chosen price usd:** 49.95
- **Saving usd:** 0.00
- **Equivalence proof:** No candidate is cheaper and also not-worse, so the current part stays. These are the reference specs I checked myself against the local datasheet copy (Rev 1, 2022-06-24; it lists both SKU 100791 and 100792) and the page-3 plot:
  - Gain: 38 dB at f0 (Max column). The product page guarantees at least 30 dB.
  - 3 dB bandwidth is 70 MHz and 10 dB bandwidth is 80 MHz, centred at 1688 MHz. The plot is flat at 37-39 dB from about 1655 to 1720 MHz, so every target from 1687.5 to 1704.5 MHz is at full gain.
  - NF is 1.2 dB typical (Tn 100/110/120 K).
  - OP1dB is +20 dBm and maximum input is 0 dBm.
  - S11 is at most -12 dB and S22 at most -15 dB at f0.
  - Supply current is 120/140/160 mA (the product page says 180 mA nominal; the stack budgets 180 mA).
  - Reverse gain is about -60 dB in band.
  - Read off the plot: rejection is about 35-40 dB at 1525-1610 MHz, about 43-55 dB at 1805-1880 MHz and about 43 dB at 2.1-2.7 GHz. The high-side skirt is about 25 dB of gain at 1730 MHz and about 10 dB at 1750 MHz, so the LTE B3 uplink edge is in band, as the stack already records.
  
  Every cheaper candidate either loses one of these specs, or loses build quality and its saving disappears once that is restored:
  - Barebones 100791 ($44.95): RF identical, but it has no enclosure for the outdoor feed mount. Nooelec sells no standalone SAWbird enclosure. Its cheapest extruded enclosure kit is $7.95-9.95 and made for another product, so restoring the case brings the cost back to $49.95 or more.
  - Non-plus 100786/100785: gain is at least 20 dB instead of 38 dB, and the NF is higher (Nooelec's own statement).
  - Everything else is unfiltered, more expensive, or covers the wrong passband.
  
  My cascade model, with the stage after the LNA at about 10 dB NF on the RTL-B path: 38 dB of gain adds less than 0.01 dB to the system NF, while 20 dB adds about 0.3 dB. Behind the 10 dB pad on the Lime path, 20 dB of gain adds about 0.6-1.3 dB. This is a model, not a measurement.
- **Rejected:**
  1.
    - **Name:** Nooelec SAWbird+ GOES Barebones, SKU 100791 ($44.95)
    - **Why:** Electrically identical: the same datasheet covers it, both boards have 2 EMI shields per LNA, and both carry a 1-year warranty (both pages checked). It is worse in build: no aluminium enclosure, but the stack hangs it on SMA under the 18 cm disc outdoors, so the board, connectors and solder joints are exposed to drip, dust, knocks and coax strain. Nooelec sells no standalone SAWbird enclosure (I checked the first 11 of 57 'enclosure' search results); its cheapest extruded kit is $7.95-9.95 and made for the NESDR Mini, fit not verified. A third-party box costs about the same as the $5 saving (estimate). A bulkhead adapter in front of the first LNA adds its loss directly to the NF. Net saving is about $0 or negative. It is acceptable only if a suitable metal box is already on hand (see conditions).
  2.
    - **Name:** Nooelec SAWbird GOES non-plus cased, SKU 100786 ($44.95)
    - **Why:** Worse on gain: at least 20 dB against at least 30 dB (38 dB typical). Worse on NF: the product page says 'SAWbird+ GOES has a higher gain and a slightly lower noise figure', and gives no figure for the non-plus. There is no datasheet (Downloads is empty), and OP1dB, maximum input and S11 are unpublished. Cascade model: system NF rises by about 0.3 dB on the RTL-B path and by about 0.6-1.3 dB on the Lime path through the 10 dB pad. HRPT on the 4-turn helix is already marginal. Its only advantage is current (30 mA against 140-180 mA), which does not offset the NF and gain loss.
  3.
    - **Name:** Nooelec SAWbird GOES non-plus Barebones, SKU 100785 ($39.95)
    - **Why:** Has every deficit of 100786 (at least 20 dB gain, higher and unpublished NF, no datasheet, unknown linearity) and also has no enclosure for the outdoor feed mount.
  4.
    - **Name:** RTL-SDR Blog Wideband LNA V2, QPL9547 ($19.95), alone or with the GPIO Labs 1685 MHz BPF ($54, total $73.95)
    - **Why:** Alone: no filter at all (100 MHz-6 GHz), so the first stage at the feed sees all of DCS1800/LTE, UMTS, GNSS and ISM. Its gain at 1.7 GHz is not published; I could not fetch the Qorvo page (HTTP 429). With the GPIO filter, checked in gpio.com's product JSON: the passband is only 1675-1695 MHz, which misses Meteor HRPT 1700, Metop AHRPT 1701.3 and FY-3 1704.5 MHz. The filter also has up to 3.5 dB insertion loss, a 'Max DC voltage on In/Out port = 3 VDC' limit that blocks the 4.5 V bias over coax, and a +10 dBm maximum input. It also costs more ($73.95 against $49.95).
  5.
    - **Name:** GPIO Labs PGA-103+ LNA plus GPIO Labs 1685 MHz BPF ($93-111)
    - **Why:** About twice the price. It has the same filter problem as above: the 1675-1695 MHz passband misses the HRPT and AHRPT targets, insertion loss is up to 3.5 dB, and the ports take 3 V DC at most. It needs two boxes at the feed.
  6.
    - **Name:** LNA4ALL (9A4QV, Croatia), EUR 23 with SMA + EUR 3 bias-T mod + EUR 7 shipping = EUR 33
    - **Why:** No filter, so it loses the roughly 40-55 dB of out-of-band rejection. Single-unit gain at L-band is about 16 dB, inferred from the maker's figure of 31.35 dB for two units in series at 1420 MHz; nothing is published at 1.7 GHz. NF figures are the maker's own and taken at 1420 MHz only. The default supply is 6-9 V, so bias at 4.5 V needs the mod. It is a bare PCB ordered by email; the only stock note is 'May, 2025 Stock 250 pcs', so current availability is unverified.
  7.
    - **Name:** Used SAWbird+ GOES (eBay or EU classifieds)
    - **Why:** No price could be verified (eBay returned HTTP 403). The 1-year warranty does not transfer. An ESD-degraded first stage can raise NF without visible loss of gain, and our bench (tinySA plus noise source, about +/-0.5 dB) cannot prove 1.2 dB. Units can be mislabelled (non-plus or barebones sold as cased).
  8.
    - **Name:** DIY SAWbird-style build (two MMICs around a 1.69-1.71 GHz SAW)
    - **Why:** No off-the-shelf 1.69-1.71 GHz SAW was identified and no measured design exists. NF, rejection and stability are unproven, and the cost is not established.
  9.
    - **Name:** Unbranded 'Barebones GOES LNA and SAW filter module' (VXB Bearings, ID 1169-4574)
    - **Why:** More expensive: the page lists $88.88 'regular' and $130.00 'sale', which contradict each other. It names no maker and gives no gain, NF, bandwidth or current, and it is bare.
  10.
    - **Name:** AliExpress generic LNAs (Zeenko 100 kHz-6 GHz; multi-band 'Active SAW Filter LNA')
    - **Why:** No 1.69-1.71 GHz SAW-plus-LNA module was found. The Zeenko has no filter and no published NF, and the cheap SAW LNAs come only in other bands. MMIC provenance is unknown, with a counterfeit risk.
  11.
    - **Name:** Uputronics filtered preamps
    - **Why:** No 1.7 GHz variant exists. The store's product JSON lists only 1090, 137.5, 162, 403, 434, 440, 868, 915 and 978 MHz plus a 100 MHz-4 GHz wideband model.
- **Conditions or tests:** Keep the cased 100792 and buy it from Nooelec direct or an authorised reseller (Amazon DE/FR/IT/ES/UK under Nooelec, Passion Radio, Neven CZ, Antratek) to avoid clones. I could not read EU reseller prices: Antratek is behind a Cloudflare 403 and Amazon.de returned 503.
  
  Incoming check:
  - LiteVNA S21 from 1.6 to 1.8 GHz, conducted only with a 30-40 dB pad at the output. Expect at least 36 dB from 1687 to 1705 MHz, matching the datasheet plot.
  - S11 at -10 dB or better.
  - Current of 120-160 mA at 4.5 V through injector ch3; the labd baseline stays at 180 mA.
  - Y-factor NF sanity check with the lab noise source.
  
  Only conditional saving: the Barebones 100791 ($44.95, saves $5) is acceptable only if a sealed metal box is already in the kit. The input SMA must pass through directly, with no extra adapter or bulkhead before the first LNA. The box needs a drip loop and strain relief on both coax runs. Then run the same incoming check. If a box has to be bought, keep the cased unit.
  
  Coverage limit: the shared WebSearch budget was already exhausted at my first query. Verification therefore rests on direct fetches of primary pages (Nooelec x4, gpio.com JSON, Uputronics store JSON, RTL-SDR Blog buy page, LNA4ALL, VXB) and on the local datasheet and plot.
- **Confidence:** high
- **Sources:**
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-goes-302.html
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-goes.html
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-goes-305.html
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird.html?p=2
  - https://www.nooelec.com/store/downloads/dl/file/id/108/product/296/sawbird_goes_datasheet_revision_1.pdf (local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfdl/sawbird_goes_datasheet_revision_1.pdf, plot /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/goesB/p-3.png)
  - https://www.nooelec.com/store/catalogsearch/result/?q=enclosure
  - https://gpio.com/products/1685-mhz-band-pass-filter (product JSON fetched to /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/goesV/dl/gpio_bpf.json)
  - https://store.uputronics.com/products/uputronics-filtered-preamps (JSON)
  - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
  - https://lna4all.blogspot.com/
  - https://vxb.com/products/barebones-goes-lna-and-saw-filter-module-for-noaa
  - https://www.rtl-sdr.com/comparing-two-lnas-hritlrit-goes-reception/
- **Stack changes:** No changes to rails, connectors, drivers or the case. The part is a passive RF block and needs no driver. It stays on injector ch3 at 4.5 V (TPS2553, 240 mA minimum limit, 180 mA budget), SMA in and out, mounted under the disc, with the static bleed at the input.
  
  Three documentation notes:
  (1) Record that the GOES cased warranty is 1 year, not the 2 years of the NOAA cased unit.
  (2) Do not use the GPIO Labs 1685 MHz BPF anywhere in the HRPT chain as a selectivity add-on. Its 1675-1695 MHz passband excludes 1700-1704.5 MHz, and it limits DC on its ports to 3 V.
  (3) Rejection figures read off the plot: about 35-40 dB at 1525-1610 MHz and about 43-55 dB at 1805-1880 MHz. The high-side skirt is about 25 dB of gain at 1730 MHz and about 10 dB at 1750 MHz, so the 'phones at least 5 m away during HRPT' procedure stays.

