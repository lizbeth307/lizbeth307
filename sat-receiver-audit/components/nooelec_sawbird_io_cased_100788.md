# Nooelec sawbird io cased 100788: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_467ce110-ee4`_

- **Part:** Nooelec SAWbird+ iO cased (100788): 1542 MHz L-band LNA with SAW filter for the gated Inmarsat-C EGC SafetyNET path (helicone feed, then P3 ch3 at 4.5 V, then HMC7992-B, then RTL-B)
- **Current pick:** Nooelec SAWbird+ iO cased, SKU 100788 (optional tier, qty 1, bought only after the egc-gate passes)
- **Current price usd:** 49.95 (nooelec.com, Add to Cart, "usually shipped in 1 business day", re-checked 18 Oct 2026, ex-VAT, ships from North America). EU landed cost is higher: import VAT, plus under the 2026 EU rules (operator_notes item 35) either EUR 3 duty per tariff line for a consignment of EUR 150 or less sent postal/IOSS, or normal duty above EUR 150, plus the EUR 2 per item handling fee from about 1 Nov 2026. Newegg sells it for $82.99, which is not cheaper. No EU dealer stock was verified.
- **Decision:** keep
- **Chosen:** Keep the Nooelec SAWbird+ iO cased (100788). None of the cheaper candidates matches or beats it on every spec that matters here.
- **Chosen price usd:** 49.95
- **Saving usd:** 0
- **Equivalence proof:** What has to be at least as good, and what 100788 is guaranteed on its own page today (nooelec.com, 18 Oct 2026):
  - Centre 1542 MHz with a 60 MHz bandpass, covering the 1537-1545 MHz NCS window.
  - Gain of at least 30 dB in band.
  - "Very high attenuation" outside the band. No number is given.
  - 180 mA nominal at 3-5 V through the SMA output. That fits under the ch3 TPS2553 300 mA limit.
  - Survives up to 12 V DC without damage.
  - Two EMI shields per LNA, aluminium enclosure, female SMA, 1-year warranty, sold by the maker.
  - Receive-only and passive, with no TX path or loop element.
  
  Not published for the iO+ at all: NF, OP1dB, maximum input and numeric rejection. The page has no datasheet and its Downloads section is empty. The NF 1.2 dB, OP1dB +20 dBm and Pin 0 dBm figures in the stack come from the SAWbird+ GOES sibling and must not be quoted as iO data.
  
  Adversarial result for each cheaper candidate:
  
  (1) SAWbird+ iO Barebones 100787, $44.95. Its page gives the same RF text: 1542 MHz, 60 MHz, at least 30 dB, 180 mA, 3-5 V through the SMA output, up to 12 V tolerated, 2 shields per LNA. So it is probably electrically equal, but it ships with no enclosure. STACK.md line 149 allows a Barebones only inside a shielded housing, and this unit sits at the outdoor helicone feed. Nooelec sells no SAWbird enclosure: its enclosures category has only NESDR, HackRF and Ubertooth kits. A comparable extruded aluminium box costs more than the $5 saved: Hammond 1455C801 is EUR 12.63 incl. VAT at Bürklin and $13.65 at Jameco, before drilling the SMA holes. Putting the LNA behind coax inside the main shielded compartment instead would put cable loss ahead of the LNA and raise the NF. Net result: not cheaper once it is made not-worse.
  
  (2) SAWbird iO non-plus, cased, 100782, $44.95.
  - Nooelec gives about 80 MHz at -6 dB and says to use it for 1.50-1.58 GHz, against 60 MHz for the iO+.
  - No gain figure and no 30 dB minimum. On the matching IR pair, Nooelec states the non-plus has "a minimum of 20dB" and that the plus has "higher gain and a slightly lower noise figure" (sawbird-ir-307 page).
  - Its only response data is Nooelec's 2016 Rigol noise-source sweep (download id 64, product 300), which I read myself. Peak is -32.6 dBm at 1542.7 MHz, with -6 dB markers at 1505.7 and 1576.7 MHz, so GNSS L1 at 1575.4 MHz sits inside the passband. Rejection is only about 18 dB at 1490 MHz (the LTE B32 SDL edge), about 28 dB at 1442 MHz and about 25 dB at 1642 MHz.
  - In the same plot the trace that looks like the reference sits about 18-19 dB below the peak. If that trace is the bare noise source, net gain is about 19 dB, consistent with the IR 20 dB minimum. That is my reading of an unlabelled plot, so it is unverified.
  - With 20 dB instead of 30 dB of gain ahead of the RTL-B (NF about 13 dB, plus about 2 dB of switch and cable loss), the model system NF rises from about 1.3 dB to about 1.9 dB. That is a real loss on a link the stack already marks as marginal.
  - Its one advantage is current (35 mA minimum against 180 mA), and it does not offset the gain and selectivity loss. Worse, so rejected.
- **Rejected:**
  1.
    - **Name:** Nooelec SAWbird+ iO Barebones 100787 ($44.95)
    - **Why:** Probably the same RF (same spec text, unmeasured), but it has no enclosure and the stack's Barebones-only-in-shielded-housing rule applies at the outdoor feed. Nooelec sells no SAWbird case. A comparable Hammond 1455C801 box costs EUR 12.63 (Bürklin) or $13.65 (Jameco), which is more than the $5 saving, and drilling comes on top. Moving the LNA inside behind coax would raise the NF. Not cheaper once made not-worse.
  2.
    - **Name:** Nooelec SAWbird iO non-plus cased 100782 ($44.95)
    - **Why:** Gain is unspecified with no 30 dB minimum. The non-plus line is rated at 20 dB minimum on the IR sibling, and the vendor 2016 sweep suggests about 19 dB (unverified reading). The passband is wider: about 71-80 MHz at -6 dB, with GNSS L1 inside and only about 18 dB down at 1490 MHz. The model system NF is about 0.6 dB worse. Its lower 35 mA draw does not offset this.
  3.
    - **Name:** Nooelec SAWbird iO Barebones non-plus 100722 ($39.95)
    - **Why:** All the non-plus deficits (gain, selectivity), and it also has no enclosure, against the cased-at-feed rule. Passion Radio lists the EU stock as no longer available.
  4.
    - **Name:** eBay.de 326374889757, 'Nooelec LNA Verstärker und Sägefilter für L-Band (Inmarsat/AERO) 1542 MHz', GBP 25 + GBP 7 shipping, private seller reportedly in Greece (search snippet only)
    - **Why:** eBay returned 403, so the listing could not be read. The title matches the old non-plus/Outernet LNA, not the SAWbird+ iO. Model, condition and whether it is still live are all unverified. No warranty or returns, and the ESD history is unknown. Not a verified not-worse part.
  5.
    - **Name:** RTL-SDR Blog Wideband LNA (SPF5189Z, $19.95)
    - **Why:** No band filter at all, so it gives no rejection of LTE B32/B3/900/2100. It is a single stage with 18.7 dB at 900 MHz per the Qorvo datasheet and less at 1.5 GHz, against at least 30 dB. Adding the GPIO Labs 1525-1559 MHz filter ($42) brings the cost to $61.95 at about 15 dB net gain, which is both dearer and worse.
  6.
    - **Name:** LNA4ALL (9A4QV, EU)
    - **Why:** About 16 dB gain per unit and unfiltered. It needs a modification to run from a bias tee. Two units plus a filter cost more than the iO.
  7.
    - **Name:** GPIO Labs L-band filter 1525-1559 MHz ($42, Tindie)
    - **Why:** A passive filter with insertion loss under 3 dB and no LNA. Any added LNA pushes the total over $49.95, and it publishes no numeric rejection.
  8.
    - **Name:** GPIO Labs pre-filtered GNSS LNA ($102)
    - **Why:** More expensive. Its 1100-1700 MHz prefilter is less selective.
  9.
    - **Name:** Uputronics filtered preamps
    - **Why:** The full Shopify catalogue, which I re-checked, has no L-band model. Its range runs 137.5 MHz to 978 MHz, plus a wideband 100 MHz-4 GHz unit.
  10.
    - **Name:** Mini-Circuits ZX60-P162LN+ ($128.77)
    - **Why:** Dearer and unfiltered.
  11.
    - **Name:** SAWbird+ IR / GOES / H1 ($49.95)
    - **Why:** Wrong band: the IR centres on 1620 MHz and is aimed at Iridium (rule), the GOES SAW blocks 1537-1545 MHz, and the H1 is for 1420 MHz. None is cheaper.
  12.
    - **Name:** Generic AliExpress 1.5 GHz LNA+SAW module
    - **Why:** A domain-restricted search found none. The only filtered hits were 1090 MHz modules.
  13.
    - **Name:** Newegg marketplace SAWbird+ iO ($82.99)
    - **Why:** The same part at a higher price.
- **Confidence:** high
- **Conditions or tests:** No replacement. Acceptance test for the kept part on arrival, conducted only into a load or DUT, with bias from injector ch3 at 4.5 V:
  - Gain: S21 of at least 30 dB across 1537-1545 MHz on the LiteVNA, at low source power with a 20-30 dB pad on the output.
  - Rejection, recorded at 1452-1496, 1575.4, 1620, 925-960 and 1710-1880 MHz.
  - NF: Y-factor check with the lab noise source and the tinySA Ultra+, target about 1.5 dB or better.
  - Current: at or below 200 mA at 4.5 V, below the ch3 300 mA limit.
  If the gain comes in under 30 dB or the NF above about 2 dB, claim the 1-year warranty. A used unit is acceptable only if it passes the same tests and lands under about $35 delivered in the EU; none is verified today.
- **Stack changes:** No changes to the part, rails, connectors, drivers or case: female SMA, bias over the SMA at 4.5 V on P3 ch3, DC block before the Lime, cased unit at the feed.
  
  Corrections for v2:
  (a) STACK line 149 and the iO rows must not quote GOES-sibling NF, OP1dB or Pin values as iO data. Mark them unpublished and measured at acceptance.
  (b) The warranty is 1 year.
  (c) Landed EU cost has to include import VAT plus the 2026 EU rules (EUR 3 per tariff line, or normal duty above EUR 150, plus the EUR 2 UHF from about 1 Nov 2026). Put the iO in the same Nooelec order to share the consignment.
  (d) Keep the $0 path: if the egc-gate passes on the core RTL-SDR Blog L-band patch and the helicone path is not needed, the iO stays unbought.
- **Sources:**
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-io-303.html
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-io.html
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-io.html
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-ir-307.html
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird.html
  - https://www.nooelec.com/store/sdr/sdr-addons/enclosures.html
  - https://www.nooelec.com/store/downloads/dl/file/id/64/product/300/x.png
  - https://www.rtl-sdr.com/review-outernet-lna-and-patch-antenna/
  - https://store.uputronics.com/products.json
  - https://www.tindie.com/products/gpio/l-band-filter-bandpass-1525-to-1559-mhz/
  - https://www.buerklin.com/en/aluminium-gehaeuse/p/60h3000
  - https://www.jameco.com/z/1455C801-Hammond-Manufacturing-Extruded-Aluminum-Enclosure-Clear-Anodized-Rounded-Rectangle-80x54x23mm_2292663.html
  - https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
  - https://www.passion-radio.com/sat-accessory/lna-outernet-467.html
  - https://www.ebay.de/itm/326374889757 (HTTP 403, snippet only)
  - https://www.newegg.com/p/3C6-00ZE-01ER2
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md lines 149, 296, 1129
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md item 35

