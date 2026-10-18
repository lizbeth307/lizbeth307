# Litevna 64: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** LiteVNA 64 (Zeenko), bench VNA, Lab instruments, qty 1, conducted use only
- **Current pick:** LiteVNA 64 at Passion Radio (FR), SKU NANO-LITEVNA64-2730, HW 3.1. Re-verified live on 18 Oct 2026: base EUR 182.50 ex VAT minus EUR 26.17 (reduction_tax=0, no end date) = EUR 156.33 ex / EUR 187.60 incl. 20% FR VAT. quantityAvailable=5, In stock. Box: LiteVNA64, SMA cal kit (OSL), USB cable, 2x 30 cm SMA M-M, 1x SMA F-F. Shipping 'to be determined'.
- **Current price usd:** 175.73 ex VAT / 210.88 incl. FR VAT (EUR 156.33 / 187.60 at 1.1241), verified live 18 Oct 2026
- **Decision:** replace_conditionally
- **Chosen:** The same Zeenko LiteVNA 64 from Eleshop (eleshop.eu/litevna-5341.html, house SKU ELE005341). This applies ONLY if the live checks in conditions_or_tests pass. Until then the booked line stays Passion Radio. If Eleshop cannot be confirmed the same day, buy at Passion Radio (5 units left), because the possible saving is too small to risk losing the verified unit.
- **Chosen price usd:** 162.53 ex VAT (EUR 144.59). UNVERIFIED: this comes only from search-index snapshots. eleshop.eu/.de/.nl return a Cloudflare 403 to curl and WebFetch, and I re-tried. About 195.04 incl. 20% VAT. Shipping unknown.
- **Saving usd:** 13.20 ex VAT (15.84 incl. 20% VAT) before shipping. Unverified. It may shrink to zero or go negative once Eleshop's EU shipping is compared with Passion Radio's.
- **Equivalence proof:** The candidate is the identical product, not an analog. The official LiteVNA User Guide (nanovna.com PDF, read 18 Oct 2026) states performance per HARDWARE REVISION, not per seller.
  - Frequency: 50 kHz-6.3 GHz.
  - System DR below 3 GHz: >90 dB (v0.3.1 at IFBW 90 Hz; v0.3.2 and later at 225 Hz).
  - DR at 3 GHz and above: >50 dB (v0.3.2 and earlier); >70 dB (v0.3.3).
  - S11 floor: <-50 dB below 3 GHz, <-40 dB at 3 GHz and above.
  - Stability: <0.5 ppm over 0-50 C.
  - Sweep: >1600 pts/s for HW v0.3.2 and later.
  - Points: 21-1001 on the device, 1-65535 over USB.
  - Model rows for the 64: USB 5 V +/-0.5 V at 1 A max; 2000 mAh Li-po; SMA female; 3.95 in 480x320.
  
  Passion Radio's unit is HW 3.1, the LOWEST revision in that table. So any genuine LiteVNA 64 with HW v0.3.1 or later ties it on every spec this stack uses, and HW v0.3.2 or later is strictly better (faster sweep; 90 dB reached at a 2.5x wider IFBW). Eleshop's snippet claims >90/>70 dB, which would mean v0.3.3, but that is not confirmed. Even at v0.3.1 it ties.
  
  The host side is the same: SAA2/NanoVNA-V2 binary protocol per the guide, so no change for NanoVNA-Saver or scikit-rf on arm64. Box per the eleshop.de snippet: USB cable, 2x 30 cm SS405 SMA M-M, male OPEN/SHORT/LOAD, SMA F-F. That meets the stack's need for a male OSL plus an F-F barrel.
  
  Authenticity: Eleshop is on tinySA.org's authorised list ('in Europe'; verified). That satisfies the stack's rule 'tinySA.org-listed sellers or Passion Radio'. The search agent's claim that 'Eleshop is Elektor's own shop' is NOT supported: elektor.com's Shopify search and suggest API return zero LiteVNA products. Origin must therefore be confirmed from Eleshop's GPSR/manufacturer field.
  
  Hard rules are unchanged: same instrument, port 1 conducted only, Bench-gated S11 page, no antenna sweeps, no loops.
  
  Note: the WebSearch budget for this turn was exhausted after my first query, so no further searches were made. The Eleshop figures could not be re-read beyond the original snapshots.
- **Rejected:**
  1.
    - **Name:** LiteVNA 62 (Zeenko): GOTRONIK $137.82 ex (535.77 zl net, card dated 18-10-2026 17:19, verified); Neven $152.40 ex (3,990 CZK incl., verified); Eleshop about $146.13 (snippet)
    - **Why:** Fails two critical specs. The official guide gives it a 2.8 in 320x240 display (vs 3.95 in 480x320) and a 1500 mAh battery (GOTRONIK and Neven say 1300 mAh) vs 2000 mAh. It would save up to $37.91, but only if the user explicitly accepts a smaller screen and battery. That is a trade, not a not-worse analog.
  2.
    - **Name:** LiteVNA 64 at GOTRONIK (PL), Producent Zeenko, EAN 5903815313127
    - **Why:** Not cheaper: 699.19 zl net = EUR 160.00 = $179.85 ex VAT, +$4.12 (verified on the product card of 18 Oct 2026). HW revision not stated; the DR text is muddled ('>70 dB (do 3 GHz), 90 dB (v0.3.1 20avg)'). Box includes the F-F adapter. Valid fallback only.
  3.
    - **Name:** LiteVNA 64 at Neven.cz
    - **Why:** Not cheaper: 4,690 CZK incl. 21% = EUR 159.36 = $179.13 ex VAT, +$3.40 (verified, in stock). The page claims 'LiteVNA 62/64 ZN-406 HW ver. 0.3.3', but its DR table is the older >70/>50 dB row, and the manufacturer field reads 'NANOLAB', not Zeenko. If Neven confirms v0.3.3 in writing, it is a better-for-$3.40 upgrade (>70 dB above 3 GHz), but it is not the cheapest not-worse option.
  4.
    - **Name:** LiteVNA 64 at Lab401 (vendor field 'DeepElec', SKU ZEENKO-LITEVNA)
    - **Why:** Not cheaper under either VAT reading. Shopify JSON shows EUR 192.00, taxable=true (updated 18 Oct 2026). If that is ex VAT: $215.83. If it includes 20% VAT: EUR 160 ex = $179.86. Both exceed $175.73. The vendor field is not Zeenko.
  5.
    - **Name:** LiteVNA 64 at Astroradio (ES)
    - **Why:** Not cheaper: $189.51 ex VAT (from the search agent; not re-read by me).
  6.
    - **Name:** LiteVNA 64 at R&L Electronics (US)
    - **Why:** Not cheaper: $189.95 (unverified, page returned 503). US-to-EU import adds VAT and a clearance fee.
  7.
    - **Name:** LiteVNA 64 at the Zeenko AliExpress factory store
    - **Why:** Price and store identity unprovable. My curl was redirected to login.aliexpress.com, and the search snapshots ($200-213) are US-site prices. The store behind the listing (it must be 5800447) is not confirmed, returns and the 14-day arrival test are harder, and the GPSR person is unknown. Not shown cheaper.
  8.
    - **Name:** Grey-market 'LiteVNA-64' (HamGeek AliExpress $151.31, eBay $160 / EUR 164.48, 'Hugen' $245.44; all unverified)
    - **Why:** Cannot be shown genuine. The stack's authenticity rule rejects non-listed sellers, Lab401 warns about clones with cheaper parts, and there is no measured evidence and no EU warranty path.
  9.
    - **Name:** Used LiteVNA 64
    - **Why:** None available: kleinanzeigen.de and marktplaats.nl had 0 results on 18 Oct 2026 (search agent). Acceptable later only with a CONFIG>VERSION photo, an isolation screenshot of 90/50 dB or better, and a clearly lower landed price.
  10.
    - **Name:** NanoVNA V2 Plus4 / Plus4 Pro (NanoRFE)
    - **Why:** Range is 50 kHz-4.4 GHz (verified on nanorfe.com), so 4.4-6.3 GHz checks (HMC7992 to 6 GHz, 5.8 GHz, pads and DC blocks) are lost. Not shown cheaper. It is better in DR near 3 GHz (80-90 dB).
  11.
    - **Name:** NanoVNA-F V3
    - **Why:** Range 1 MHz-6 GHz and S21 DR 65 dB (verified at sdrstore.eu, EUR 307.86). That fails the 60 kHz choke and LF filter work and gives 25 dB less DR below 3 GHz. Different protocol. More expensive.
  12.
    - **Name:** Chelegance SV6301A / SV4401A
    - **Why:** SV6301A: starts at 1 MHz, 75 dB below 3 GHz, about EUR 949, 1.15 kg. SV4401A: 50 kHz-4.4 GHz with 75 dB S21 DR, EUR 489 incl. VAT at Passion Radio (seen on the cross-sell block). Both are worse in range or DR, more expensive, and not V2-protocol.
  13.
    - **Name:** DeepVNA 101 / NanoVNA-H4
    - **Why:** Range 10 kHz-1.5 GHz (DeepVNA confirmed on the Passion Radio listing; H4 on GOTRONIK): misses L-band above 1.5 GHz, S-band and 3-6.3 GHz, with lower DR.
  14.
    - **Name:** DIY NanoVNA V2_2 build, or tinySA Ultra+ plus a return-loss bridge
    - **Why:** V2_2 covers only 50 kHz-3 GHz at 60 dB (nanorfe.com). The tinySA plus bridge is scalar only: no phase, no vector OSL, no TDR.
  15.
    - **Name:** LibreVNA, LiteVNA 67
    - **Why:** More expensive (search-agent figures, not re-checked). Out of scope for cheaper not-worse. LibreVNA also has no built-in screen or battery.
- **Confidence:** medium
- **Conditions or tests:** BEFORE ORDERING (do this in a normal browser, since automated fetch is blocked by Cloudflare; same day, so Passion Radio's last 5 units are not lost):
  (1) eleshop.eu/litevna-5341.html shows the LiteVNA 64 (not the 62; the snapshots mix 'litevna.html' pages at EUR 130 ex and EUR 172.06 incl.) at EUR 144.59 ex VAT or less, and in stock.
  (2) Checkout to the user's EU country, compared on the same VAT basis: Eleshop goods + shipping must be below Passion Radio's EUR 156.33 + its shipping. Otherwise keep Passion Radio.
  (3) GPSR/manufacturer field, or a written reply from Eleshop, confirms: manufacturer Zeenko; HW revision v0.3.1 or later (prefer v0.3.3); box includes male OSL, SMA F-F and 2x 30 cm M-M; plain unit with no Wi-Fi/BT variant.
  If any of (1)-(3) fails or cannot be confirmed promptly, buy at Passion Radio.
  
  ON ARRIVAL (inside the 14-day EU withdrawal window):
  - Read CONFIG > VERSION.
  - lsusb shows 04b4:0008.
  - NanoVNA-Saver @3445a0a and scikit-rf NanoVNAv2 each complete a sweep on the Q6A through labd /dev/lab/litevna.
  - After SOL + thru cal, with both ports terminated (ANNE-50+): S21 floor of -90 dB or lower below 3 GHz (IFBW 90 Hz on v0.3.1, 225 Hz on v0.3.2 and later), and -50 dB or lower at 3-6.3 GHz (-70 dB or lower if v0.3.3).
  - S11 floor with the load after cal: -50 dB or lower below 3 GHz and -40 dB or lower above.
  - Power levels 1-3 respond through registers 0x41/0x42.
  - Charging stays within 5 V and 1 A or less; battery holds charge.
  Return the unit if any check fails.
- **Stack changes:** No knock-on changes: same device, USB-C CDC-ACM 04b4:0008, same driver path, same 5 V/1 A rail, SMA-F ports, same box and size, so rails, connectors, drivers and the Pelican/Apache case are unaffected.
  - BOM: if the conditions pass, change the LiteVNA line's seller to Eleshop at $162.53 ex VAT, plus shipping. Otherwise no change.
  - Authenticity list: add the tinySA.org-listed EU resellers Eleshop, Neven and GOTRONIK as LiteVNA fallbacks. Require a Zeenko manufacturer/GPSR check, because Neven's field reads 'NANOLAB' and Lab401's reads 'DeepElec'.
  - Correction: drop the claim 'Eleshop = Elektor's shop'; elektor.com does not list the LiteVNA.
  - If a v0.3.3 unit arrives, raise the planned rejection ceiling above 3 GHz from about 45 dB to about 65 dB in the lab procedures. Otherwise keep the HW 3.1 plan (90/50 dB).
- **Sources:**
  - https://www.passion-radio.com/analyzer-spectrum/lite-vna64-2730.html (curl 18 Oct 2026: productPriceTaxExcluded=182.5, specific_price reduction 26.17 reduction_tax=0 to=0000-00-00, offer price 187.60, quantityAvailable=5, taxRate=20, 'Hardware version : 3.1', scope of delivery)
  - http://nanovna.com/wp-content/uploads/2021/11/LiteVNA_User-Guide.pdf (official spec table per HW revision and per model 62/64/67)
  - https://tinysa.org/wiki/pmwiki.php?n=Main.Buying (Eleshop 'in Europe', Neven, GOTRONIK, astroradio, Zeenko factory store; no LiteVNA-specific list)
  - https://eleshop.eu/litevna-5341.html (Cloudflare 403 to curl and WebFetch; price from search snapshot only, UNVERIFIED)
  - https://www.elektor.com/search?q=litevna and /search/suggest.json (0 LiteVNA products)
  - https://www.gotronik.pl/litevna-64-analizator-sieci-wektorowej-50khz-6-3ghz-kartapdf-10197.html (860.00 zl gross / 699.19 zl net, Producent Zeenko, dated 18-10-2026 17:19)
  - https://www.gotronik.pl/litevna-62-przenosny-analizator-sieci-wektorowych-50-khz-63-ghz-zeenko-kartapdf-13581.html (659.00 / 535.77 zl, 2.8 in 320x240, 1300 mAh)
  - https://www.neven.cz/p/litevna-6ghz-prenosny-vektorovy-sitovy-analyzator (62: 3,990 CZK; 64: 4,690 CZK, Skladem; 'HW ver. 0.3.3'; Vyrobce NANOLAB; 62 at 600 mA / 1300 mAh)
  - https://lab401.com/products/litevna.json (EUR 192.00, vendor DeepElec, taxable true, updated 2026-10-18)
  - https://nanorfe.com/nanovna-v2.html (V2 Plus4 50 kHz-4.4 GHz; DR figures)
  - https://www.sdrstore.eu/test-and-measurement/spectrum-analyzer/nanovna-f-v3-1mhz-6ghz-portable-vector-network-analyzer-vna-for-mf-hf-vhf-uhf-shf/ (EUR 307.86; 1 MHz-6 GHz; S21 65 dB)
  - https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml (16 Oct 2026: PLN 4.3700, CZK 24.323; USD 1.1253, while the stack rate 1.1241 is kept)
  - https://www.aliexpress.com/item/1005003551867442.html (redirects to login; unverifiable)
  - Note: the WebSearch budget for this turn was exhausted, so no new searches were run and the Eleshop data remain search snapshots.

