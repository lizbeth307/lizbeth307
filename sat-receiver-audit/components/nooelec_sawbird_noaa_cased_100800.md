# Nooelec sawbird noaa cased 100800: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e32114dd-52d`_

- **Part:** LNA+SAW 137 MHz, VHF-137 front end (P1 chain: Flamingo+ FM v2 -> SAWbird+ NOAA -> injector ch1 TPS2553 -> C0G DC block -> HMC7992 -> RTL-A), tier core, group RF, qty 1
- **Current pick:** Nooelec SAWbird+ NOAA, cased with aluminium enclosure, SKU 100800 (UPC 0616469146472)
- **Current price usd:** 49.95 (Nooelec direct, before EU VAT; I checked it on 18 Oct 2026. Nooelec ships from its USA headquarters by USPS or UPS, with free worldwide shipping on orders over $100. Its shipping page does not mention VAT, duties or IOSS, so the buyer should expect to pay about 20-21 % EU import VAT, about $60 landed, plus any carrier handling fee (amount unverified).)
- **Decision:** keep
- **Chosen:** Keep the Nooelec SAWbird+ NOAA cased, SKU 100800. No cheaper part survived the check without being worse.
- **Chosen price usd:** 49.95 (before VAT; about 59.9-60.4 with 20-21 % EU import VAT)
- **Saving usd:** 0
- **Equivalence proof:** The current part is the reference. I checked these figures myself against datasheet Rev 1 (2022-06-29; its ordering table covers both 100799 barebones and 100800 with enclosure) and the 100800 product page:
  - 41 dB gain at 137.5 MHz (the page only promises a 30 dB minimum).
  - Two MMIC stages with a SAW between them (LNA, then SAW, then LNA).
  - Bandwidth 2.6 MHz at 3 dB and 3 MHz at 10 dB (the page says '5 MHz'; the datasheet value governs).
  - NF 1.1 dB (84 K), OP1dB +20 dBm, maximum input 0 dBm.
  - S11 -9 dB, S22 -9.5 dB.
  - Supply 3.3-5.5 V; 170 mA on bias-tee, 175 mA on USB, '180 mA nominal' on the page.
  - Bias is fed through the SMA output; two EMI shields per LNA plus the free aluminium enclosure; 73.7 x 30.6 x 18.7 mm, 36 g; M3 holes; made in the USA; 2-year warranty.
  
  Selectivity, read by me from the datasheet's 110-160 MHz S21 plot:
  - About -25 dB from 110 to 133 MHz, i.e. about 65 dB below the passband.
  - About +15 to +20 dB at 140 MHz, i.e. only about 20-25 dB of rejection.
  - About -5 to -10 dB at 144-146 MHz, i.e. about 45-50 dB of rejection.
  - About -20 to -30 dB above 150 MHz.
  - Wideband (1 MHz-1 GHz plot): about -20 to -25 dB from 250 to 500 MHz, rising to about 0 dB near 1 GHz.
  
  Any replacement has to match all of this.
  
  Why the only cheaper part with the same electronics, the SAWbird+ NOAA Barebones 100799 at $44.95, fails the not-worse rule (I checked both Nooelec pages myself on 18 Oct 2026):
  - The electronics really are identical: same datasheet, same topology and the same three power options.
  - Its warranty is 1 year, against 2 years on the cased 100800. That is a real loss in reliability cover.
  - It has no aluminium enclosure, so the SMA connectors are unbraced in a handheld and the SAW section has no second shield layer. That layer matters in an RF compartment it shares with two V4L dongles (own spur at 144.0 MHz) and near the Q6A and display.
  - The $5 saving (about $6 with VAT) shrinks once M3 standoffs or a shield can are added.
  
  The rule says not to trade a spec silently, so the barebones is not an analog.
  
  Every other candidate is either not cheaper, worse in gain or selectivity, or both; see the rejected list. The datasheet NF and selectivity are vendor data only. No independent measurement exists, and that applies to every candidate equally.
- **Rejected:**
  1.
    - **Name:** Nooelec SAWbird+ NOAA Barebones, SKU 100799
    - **Why:** Price verified at $44.95, $5 cheaper. The electronics are identical (one datasheet, Rev 1, covers both SKUs). It is worse on warranty (1 year, verified on the product page, against 2 years for 100800) and has no aluminium enclosure, so the SMA connectors are unbraced in a handheld and the SAW section loses the second shield layer next to two V4L dongles and the Q6A. It needs M3 standoffs or a shield can, which eat most of the $5. It is not not-worse; it is acceptable only if the user explicitly accepts the trade.
  2.
    - **Name:** Nooelec SAWbird+ NOAA Barebones at Passion Radio (FR), ref NOOELEC-100799-NOAA-1061
    - **Why:** Verified 18 Oct 2026: EUR 59.05 including 20 % VAT (EUR 49.21 before VAT), about $66.38, 3 in stock. It costs more than the cased 100800 direct even after EU VAT (about $60), and it is still the barebones SKU with no case.
  3.
    - **Name:** Nooelec SAWbird NOAA (non-plus), SKU 100852
    - **Why:** Verified at $49.95, the same price as the cased plus, so there is no saving. It has at least 20 dB of gain against 41 dB, and its bandwidth and topology are not published. It is better only on NF (about 0.7 dB) and current (about 80 mA). The STACK.md line 191 note calling it the 'budget' option is wrong.
  4.
    - **Name:** Uputronics Filtered Preamp 137.5 MHz NOAA (HAB-FPA1375)
    - **Why:** Price from the store's variant JSON, checked by me: GBP 59.99, about $79.89, more expensive. The angle-B figures of GBP 44.39 and Kubii EUR 47.64 belong to other variants (1090/162 MHz at Uputronics, 915 MHz at Kubii; the Kubii page lists no price for the 137.5 MHz variant). The angle-A Kubii figure of EUR 69.90 is unverified. Gain is at least 21-22 dB against 41 dB, the SAW passband is 7.6 MHz against 2.6 MHz (weaker toward 2 m and 141-145 MHz), it is a single LNA stage, OP1dB is not published, and the case is larger. It is better on current, temperature range and its limiter, but it is worse and not cheaper.
  5.
    - **Name:** RTL-SDR Blog Wideband LNA V2 (QPL9547)
    - **Why:** About $19.95, but it has no SAW and no band-pass at all, so no rejection of airband, 2 m, pagers or DVB-T ahead of the notchless V4L. It has about 20 dB less gain and no published NF at 137 MHz. It fails selectivity and gain.
  6.
    - **Name:** LNA4ALL (9A4QV), assembled
    - **Why:** About EUR 30 with shipping, VAT status unclear. It is a wideband single MMIC with no filter and no enclosure, and has no gain or NF measurement at 137 MHz. It fails selectivity and gain.
  7.
    - **Name:** LNA4ALL + AliExpress 130-145 MHz LC band-pass filter
    - **Why:** The roughly 15 MHz wide LC filter passes 2 m and airband. Insertion loss and rejection are unpublished and the listing is old (current price unverified). Nothing has been measured. It fails selectivity and has no evidence.
  8.
    - **Name:** Generic SPF5189Z LNA boards
    - **Why:** No filter, about 15-19 dB of gain, and no NF measured at 137 MHz. The SPF5189Z is EOL at Qorvo, so cheap boards carry a risk of remarked or counterfeit MMICs. It fails selectivity, gain and the authenticity rule.
  9.
    - **Name:** DIY PGA-103+ with LC band-pass (NuclearRambo design)
    - **Why:** An LC band-pass about 34 MHz wide, about 18 dB of gain, an NF measured only by the designer with a tinySA, and no enclosure. It is not purchasable (sold out). It fails selectivity, gain and build quality.
  10.
    - **Name:** DIY two-stage MMIC + TST TB1103A 137.5 MHz SAW
    - **Why:** The SAW alone costs about $22.36 before VAT. Its guaranteed -1 dB bandwidth is only 0.8 MHz and insertion loss is up to 8 dB, so the 137.1 and 137.9 MHz Meteor channels fall at the passband edges. It would need a custom PCB, bias tee and enclosure, and no built unit has been measured. It fails passband and build quality.
  11.
    - **Name:** DIY MMIC + Shoulder HDF137T SAW
    - **Why:** The passband is only 1.34 MHz (136.83-138.17 MHz). It is quote-only with no price, and no unit has been measured. It is unverified and fails passband margin.
  12.
    - **Name:** Used SAWbird+ NOAA (eBay or classifieds)
    - **Why:** No listing could be found or checked (403 responses). The warranty does not transfer and the unit's history is unknown, so it is worse on warranty and unverified on price.
  13.
    - **Name:** Kuhne KU LNA BB 1018 A, SSB-Electronic LNA 137 A, WiMo LNAs
    - **Why:** The Kuhne is broadband with no SAW and at least 20 dB of gain. The WiMo LNA range starts at about EUR 226 including VAT. None is cheaper and not worse.
- **Confidence:** high
- **Conditions or tests:** No replacement is made, so no condition is needed to accept a swap. Optional acceptance checks on arrival, all conducted on the bench and never on air:
  (1) Gain and selectivity: LiteVNA S21 with at least 40 dB of attenuation ahead of the input, so the input stays far below the 0 dBm maximum. Expect about 41 dB at 136.5-138 MHz, about 45-50 dB of rejection at 144-146 MHz, about 60 dB or more at 110-133 MHz, and only about 20-25 dB at 140-142 MHz (the known weak spot).
  (2) NF: Y-factor at 137.5 MHz with the stack's noise source and the tinySA Ultra+. Expect about 1.1 dB, within the method's accuracy.
  (3) Current on injector ch1 at 4.5 V via the INA3221: expect 170-180 mA, comfortably below the TPS2553 trip of 262-342 mA (re-audit, RILIM 88.7 kOhm; STACK.md gives 240 mA as the minimum). Store it as the labd baseline.
  
  Use only one power path: bias through the output SMA. Leave the USB and header unpowered.
  
  Buy direct from Nooelec in one order with the Flamingo+ FM v2 ($24.95) and the SAWbird+ GOES ($49.95). That makes $124.85, above $100, so worldwide shipping is free. Expect EU import VAT on delivery; Nooelec's shipping page does not say whether VAT is collected at checkout.
  
  Open checks: Amazon US/DE and eBay prices for the genuine cased 100800 could not be checked (503/403 earlier, and the shared web-search budget ran out after my first search). An EU seller listing the genuine cased 100800 below about $60 including VAT would be the same part at a lower price, not an analog. A follow-up search could check this.
- **Stack changes:** No changes to the part, rails, connectors, drivers or case: ch1 stays 4.5 V via the TPS2553 at 300 mA nominal, SMA female in and out, 73.7 x 30.6 x 18.7 mm in the RF compartment.
  
  Corrections to the text of STACK.md:
  (a) Line 191, the note 'Бюджет: SAWbird NOAA без «+» (80 mA)', is wrong. The non-plus 100852 costs the same $49.95 and has at least 20 dB of gain. Replace it with: 'Opt-in trade only: SAWbird+ NOAA Barebones 100799 $44.95, same electronics, 1-year warranty and no case (needs M3 standoffs in the shielded RF compartment); not an equivalent.'
  (b) Line 148 and the BOM: cite the datasheet values (41 dB typ., 2.6 MHz at 3 dB), not the product page's '30 dB min / 5 MHz'. Also note the weak rejection of only about 20-25 dB at 140-142 MHz.
  (c) Sourcing: Nooelec ships from the USA (USPS/UPS) with free worldwide shipping over $100. Budget EU import VAT, about $60 landed.
  (d) Record in the analog log that the angle-B Uputronics and Kubii prices referred to the wrong variants. The 137.5 MHz NOAA variant is GBP 59.99 in the Uputronics store.
- **Sources:**
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-noaa-308.html
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-noaa.html
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-noaa.html
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird.html
  - https://www.nooelec.com/store/sdr/sdr-addons/sawbird.html?p=2
  - https://www.nooelec.com/store/downloads/dl/file/id/112/product/301/sawbird_noaa_datasheet_revision_1.pdf
  - https://www.nooelec.com/store/shipping-delivery-info/
  - https://www.passion-radio.com/sat-accessory/lna-sawbird-1061.html
  - https://store.uputronics.com/products/uputronics-filtered-preamps.js
  - https://kubii.com/en/network-modules/3349-lna-amplifier-modules-with-saw-filter-and-single-frequency-3272496306646.html
  - https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf
  - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
  - https://lna4all.blogspot.com/
  - https://wiki.satnogs.org/SPF5189_LNA_measurements
  - https://www.digikey.ie/en/products/detail/tst/TB1103A/16906793
  - https://www.rtl-sdr.com/the-design-and-test-of-a-filtered-low-noise-amplifier-for-lrpt-weather-satellite-reception/
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md (lines 46, 69, 148, 191, 559, 680, 895)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_B_receivers_rf.json

