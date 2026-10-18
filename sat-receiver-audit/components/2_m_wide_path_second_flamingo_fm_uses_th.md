# 2 m wide path second flamingo fm uses th: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_72b78d37-bec`_

- **Part:** 2 m/WIDE path (port P8, optional/gated): second FM broadcast band-stop filter ahead of the bench RTL-SDR Blog Wideband LNA V2 (P8 SMA -> Flamingo+ #2 -> LNA V2 -> injector ch4 -> HMC7992-A RF4 -> RTL-A/V4L)
- **Current pick:** Nooelec Flamingo+ FM v2, SKU 100813, qty 1, Nooelec direct (ships inside the existing Nooelec order of more than $100, so shipping is free)
- **Current price usd:** 24.95 ex-VAT. I re-verified it on nooelec.com on 18 Oct 2026 (Add to Cart, 'usually shipped in 1 business day', 2-year warranty). Landed in the EU it is about 29.7-30.2 with 19-21% import VAT, plus any carrier handling fee (not verified).
- **Decision:** keep
- **Chosen:** Keep the Nooelec Flamingo+ FM v2 (100813) from Nooelec direct, in the same core Nooelec order. EU fallback: the same part from Passion Radio (FR) at EUR 33.90 incl. VAT. That price comes from G1 on 18 Oct 2026; my fetch did not re-confirm it.
- **Chosen price usd:** 24.95 ex-VAT (about 29.7-30.2 landed in the EU)
- **Saving usd:** 0.00
- **Equivalence proof:** No cheaper candidate is not-worse, so the current part stays. These are the reference specs a replacement would have to match or beat. I verified them myself on 18 Oct 2026 from the Nooelec page and the datasheet Rev 1 in the scratchpad.
  
  (1) FM stop-band depth, EU band 87.5-108 MHz
  - Datasheet: S21 -77.5/-70 dB (min/typ) over 80.5-114.8 MHz.
  - Read from the S21 plot (+-1 dB): about -47 dB at 87.5 MHz, -50 at 88, -70 to -77 at 90-101, about -45 at 105, about -32 at 108. Mean about -63.6 dB.
  - Vendor page: '>60dB typical average & >70dB typical maximum'.
  
  (2) Loss on 2 m and at 137 MHz
  - Passband IL 0.01/0.5/1.2 dB (min/typ/max); about 0.5 dB at 145 MHz on the plot.
  - -3 dB edges at 75/120 MHz; -10 dB at 80/116 MHz.
  
  (3) Wideband loss up to the V4L limit of 1.766 GHz
  - Vendor: '<0.25dB out-of-band insertion loss'.
  - 1-2000 MHz plot: about 0 to -1 dB.
  
  (4) Match: S11/S22 typ -20 dB.
  
  (5) Survivability: Pin max +18 dBm, and an 'ESD diode meant for RF applications' on the front end. P8 is an exposed panel SMA feeding an ungrounded whip, so this diode is the only static protection ahead of the LNA V2.
  
  (6) Build: 'custom anodized aluminum enclosure' with an EMI frame; 2-year warranty; authorised seller.
  
  (7) Interface: passive, 50 ohm, SMA-F, no rail and no driver. DC pass (250 mA min) does not matter on P8, because LNA V2 bias enters at its output from ch4.
  
  Why every cheaper option fails:
  - Nooelec's own cheaper SKUs give '>40dB typical', about 20 dB shallower.
  - The RTL-SDR Blog filter ($16.95) is shallower mid-band, has no ESD diode, no max-input rating and no stated warranty. It only wins at the 104-108 MHz edge, so it is a trade, not an equivalent.
  - The Tindie copy, generic modules, DIY builds, used units and TV traps have no measured proof, or are proven worse.
  - GPIO Labs ($30) and Mini-Circuits (about $92-184) are not cheaper.
  
  Spec trade stated openly (not silent): the Flamingo+ is weak at the 108 MHz edge, about 32 dB. The RTL-SDR Blog filter gives about 45-50 dB there by vendor sweep, and about 60 dB at 107 MHz in one forum VNA measurement.
- **Rejected:**
  1.
    - **Name:** RTL-SDR Blog Broadcast FM Band-Stop Filter 88-108 MHz (rtl-sdr.com, USD 16.95, 131 in stock, verified 18 Oct 2026)
    - **Why:** Worse mid-band rejection. Its own page says 'over 50dB'; the launch post says 'around 50 dB or more'; reader DrTune measured a notch of about -60 dB. The Flamingo+ gives 70-77 dB at 90-101 MHz, so the RTL-SDR is about 10-25 dB shallower there. At 88 MHz the vendor claims 'almost 60 dB', but one RadioReference VNA measurement gives about 47 dB, no better than the Flamingo+ (about 50 dB). No ESD diode stated: P8 is an exposed port in front of the LNA V2, so an extra part would be needed. No max-input rating, and no warranty term. Loss above 1 GHz is 'mostly less than 1.5 dB' up to 3 GHz, against about 1 dB or less on the Flamingo+ 1-2 GHz plot; this matters for WIDE use at 1090 MHz and 1.7 GHz. The direct store does not ship to the EU (G1); official AliExpress/eBay prices are unverified. It is better at 104-108 MHz (45-60 dB against about 32 dB), so it is a spec trade, not a not-worse analog.
  2.
    - **Name:** Nooelec Flamingo FM v1, SKU 100780 (USD 22.95, verified 18 Oct 2026)
    - **Why:** Stop band is '>40dB typical' against >60 dB average, about 20 dB shallower. Its -3 dB points of 80/115 MHz give a narrower notch with weaker skirts. Insertion loss is unquantified ('minimal'). It saves only USD 2. ESD diode, +18 dBm, enclosure and 2-year warranty are the same.
  3.
    - **Name:** Nooelec Distill:FM Barebones, SKU 100758 (USD 17.95, verified 18 Oct 2026)
    - **Why:** Rejection '>40dB typical', about 20 dB shallower. No aluminium enclosure (EMI frame plus 2 mounting holes only). No warranty stated, only a 30-day return policy. Insertion loss unquantified.
  4.
    - **Name:** Maker go (adz1122) Tindie 'Broadcast FM Band-Stop Filter' (USD 11.90 plus unquoted shipping from Shenzhen, verified 18 Oct 2026)
    - **Why:** Its spec text copies the RTL-SDR Blog listing word for word ('over 50dB', 76/122 MHz, '<0.5 dB 0-1 GHz'). It has no measurements of its own, and the listing gives no enclosure, ESD protection, max input or DC rating. The seller has 5 reviews. It inherits every RTL-SDR Blog shortfall, and its origin cannot be verified (likely clone), which fails the counterfeit/provenance rule. The EU landed price with shipping and VAT is unknown.
  5.
    - **Name:** GPIO Labs FM Notch Filter 88-108 MHz, Tindie (USD 30.00, 9 in stock, verified 18 Oct 2026)
    - **Why:** Not cheaper. It is also worse at 108 MHz (25 dB against about 32 dB) and on 2 m (0.8 dB at 150 MHz against about 0.5 dB). No ESD protection stated, and no enclosure on this listing. Its +30 dBm max input is better, but that does not offset these losses.
  6.
    - **Name:** Mini-Circuits NSBP-108+ (USD 184.22, Mini-Circuits store per angle A) and ZX75BS-88108-S+ (about USD 92-114 per Mouser/Findchips search snippets, not verified on a primary page)
    - **Why:** Several times the price. The NSBP-108+ stop band is 89-105 MHz, missing the EU band edges, and it has N connectors and a bulky case. Neither is a cheaper analog.
  7.
    - **Name:** Generic AliExpress/eBay '88-108 MHz BSF' SMA modules (about EUR 11, unverified)
    - **Why:** No independent sweep. The only user report (via G1, unverified) gives 25-30 dB, about 35 dB worse. No ESD, shielding or max-input data, unknown origin, and some listings are actually band-pass filters.
  8.
    - **Name:** VXB-listed FM notch / FM block filters (USD 61.95-65.95 'regular price', inconsistent listing per search snippet)
    - **Why:** Not cheaper. The listing text looks like resold Nooelec/RTL-SDR descriptions, the price display is inconsistent, and I did not verify it.
  9.
    - **Name:** DIY 9A4QV 3-pole FM trap
    - **Why:** The designer's own measurement gives '30dB or better', 44.6 dB at best. That fails the mean of 60 dB or more. No ESD, an improvised shield, per-unit tuning and no warranty.
  10.
    - **Name:** Used Flamingo+ FM v2
    - **Why:** No verifiable listing (eBay HTTP 403). It loses the 2-year warranty, and its ESD history is unknown. It would be acceptable only if landed clearly below USD 24.95, it passes the LiteVNA intake sweep, and the warranty loss is accepted. None of these could be shown.
  11.
    - **Name:** 75-ohm TV FM trap (F connectors, about USD 5)
    - **Why:** rtl-sdr.com's VNA comparison shows the stop band attenuated 'significantly less' and losses elsewhere 'much larger'. It also has a 75/50 ohm mismatch, needs 2 adapters, has no ESD protection, and adds loss ahead of the LNA V2, which raises noise figure.
  12.
    - **Name:** Topology: no second filter, share Flamingo+ #1 between P1 and P8
    - **Why:** Placed after the HMC7992, it leaves the LNA V2's first stage unfiltered against FM (0 dB protection), breaking the C10 'filter first on VHF' rule. Moving it by hand breaks D8 (no manual 'connect X' by default).
  13.
    - **Name:** Same Flamingo+ from Passion Radio (FR)
    - **Why:** Same part but dearer: EUR 33.90 incl. VAT, about USD 38.1. This is G1's figure; my fetch hit a redirect loop. Keep it only as the EU fallback.
- **Confidence:** high
- **Conditions or tests:** Intake test for unit #2 on the LiteVNA, conducted only, with the DUT between the ports and never on air:
  - FM band: mean S21 <= -60 dB over 88-108 MHz; <= -45 dB at 87.5-88 MHz; <= -65 dB at 92-100 MHz; <= -28 dB at 107.9 MHz. These limits come from reading the datasheet plot.
  - 2 m: S21 >= -1.2 dB at 144-146 MHz.
  - 400-406 MHz: S21 >= -1.0 dB and S11 <= -15 dB.
  - 1090 MHz and 1.7 GHz: S21 >= -1.2 dB; S11 <= -10 dB up to 1.766 GHz.
  - If the LiteVNA's dynamic range at 90-100 MHz cannot resolve -70 dB, record the reading as floor-limited instead of failing the unit. Also note the rtl-sdr.com admin's warning that cheap VNAs can misread these filters, and cross-check one point with the tinySA and the noise source.
  
  Site condition, stated so the trade is not hidden: the Flamingo+ gives only about 32 dB at 108 MHz. If the site survey shows that the strongest local FM station is at 104-108 MHz and the LNA V2 or V4L shows intermod on P8, the fix is a new design decision. For example, add a second filter section or accept the RTL-SDR Blog filter as an explicit trade together with an added RF ESD part. That is not a 'not-worse' swap.
- **Stack changes:** No change to rails, connectors, drivers or the case: the part is unchanged. Text fixes for STACK v2:
  (a) Row 299 (2 m/WIDE path), 'Budget alternative': replace '-' with: 'none not-worse. RTL-SDR Blog band-stop USD 16.95 is a trade: better at 104-108 MHz (about 45-60 dB against about 32 dB), but shallower mid-band (about 50-60 dB against 70-77 dB), with no ESD diode, no max-input rating and no warranty. Nooelec Flamingo v1 USD 22.95 and Distill:FM USD 17.95 give only >40 dB.'
  (b) C10 and row 192 reject the RTL-SDR filter for having 'no DC rating'. That reason does not apply on P8, where bias enters at the LNA V2 output through ch4. The real P8 reasons are mid-band depth, the RF ESD diode on an exposed port, the +18 dBm rating, published IL and S11 up to 2 GHz, and the 2-year warranty.
  (c) Add the P8 intake limits above to the commissioning table, next to the existing VNA step 10.
  (d) Add a site-survey note: check the per-station margin for FM stations at 104-108 MHz, because the Flamingo+ edge rejection is about 32 dB, not 60 dB.
- **Sources:**
  - https://www.nooelec.com/store/flamingo-plus-fm.html (USD 24.95, >60/>70 dB, -3 dB 75/120 MHz, <0.25 dB out-of-band, +18 dBm, RF ESD diode, anodized Al EMI enclosure, 250 mA, 2-year warranty; fetched 18 Oct 2026)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/flam_ds/ds_en.pdf (Flamingo+ datasheet Rev 1: 80.5-114.8 MHz, S21 -77.5/-70 dB, IL 0.01/0.5/1.2 dB, S11/S22 typ -20 dB, Pin max 18 dBm)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/flam_ds/s21_zoom.png (50-150 MHz S21 plot, read for the 87.5/88/105/108/145 MHz values)
  - https://www.nooelec.com/store/flamingo-fm.html (Flamingo v1, USD 22.95, >40 dB typical, -3 dB 80/115 MHz)
  - https://www.nooelec.com/store/distill-fm-broadcast-fm-filter.html (Distill:FM, USD 17.95, >40 dB typical, EMI frame only, 30-day returns)
  - https://www.nooelec.com/store/catalogsearch/result/?q=fm (no barebones Flamingo+ and no multi-pack discount)
  - https://www.rtl-sdr.com/product/rtl-sdr-blog-broadcast-fm-band-stop-filter/ (USD 16.95, 131 in stock, 'over 50dB', <0.5 dB 0-1 GHz, 'mostly less than 1.5 dB' 1-3 GHz)
  - https://www.rtl-sdr.com/rtl-sdr-com-broadcast-fm-band-stop-filter-88-108-mhz-reject-now-for-sale/ (vendor sweeps: almost 60 dB at 88 MHz, 45-50 dB at 108 MHz, -3 dB 76/122 MHz, 80 mA DC, no ESD or max-input stated; reader VNA comments)
  - https://forums.radioreference.com/threads/fm-bandstop-filter-comparison.394943 (independent VNA: RTL-SDR filter about 47 dB at 88 MHz, about 60 dB at 107 MHz, about 11.5 dB at 119 MHz; read via search snippet, page returned HTTP 503)
  - https://www.tindie.com/products/adz1122/broadcast-fm-band-stop-filter-88-108-mhz-fm-trap/ (USD 11.90, ships from China, copied spec text, 5 reviews)
  - https://www.tindie.com/products/gpio/fm-notch-filter-88-108mhz-sma-m-sma-f/ (USD 30.00; 60/85/25 dB at 88/98/108 MHz; 0.8 dB at 150 MHz; +30 dBm)
  - https://www.minicircuits.com/WebStore/dashboard.html?model=NSBP-108%2B (USD 184.22 per angle A)
  - https://lna4all.blogspot.com/2015/10/diy-fm-trap-or-88-108-mhz-band-stop.html (DIY trap 30-44.6 dB)
  - https://www.passion-radio.com/sdr-accessory/flamingo-v2-2539.html (EU fallback, EUR 33.90 incl. VAT per G1; not re-confirmed)
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md (rows C10, D8, 192, 299, 687)

