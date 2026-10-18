# Rf frontend: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_30889068-251`_

- **Component:** RF front-end (LNAs, filters, bias tees, LNB power, antenna sharing, protection)
- **Current pick assessment:** Mostly the right idea, but two of the specific parts need changing.
  
  (1) SPF5189Z: replace it. Qorvo announced end-of-life on 8 Mar 2021 (PCN 21-0060), the last-time-buy was 15 Sep 2021, and Qorvo's recommended replacement is the QPL9547. So the $4-10 AliExpress boards on sale in 2026 carry old stock, remarked chips or fakes. An EEVblog user reports fakes with 13-15 dB gain instead of the genuine 18.7 dB. The genuine chip is 0.6 dB NF at 900 MHz, 90 mA at 5 V. The cheap boards have no filter, no shield and usually no bias-tee input, so they need separate 5 V wiring. A SatNOGS VNA test measured about 1 dB less gain than the datasheet, and no NF was measured. The RTL-SDR Blog Wideband LNA V2 ($19.95) uses the QPL9547 replacement chip and is powered over the coax (bias tee).
  
  (2) FM bandstop: keep it, but pick one confirmed to pass DC. The Nooelec Flamingo+ FM ($24.95) gives >60 dB attenuation and passes bias-tee DC (rated at least 250 mA). The RTL-SDR Blog FM bandstop ($16.95, >50 dB, <0.5 dB loss up to 1 GHz) does not state whether it passes DC.
  
  (3) L-band LNA + SAW: correct concept. The concrete product to buy is the Nooelec SAWbird+ GOES ($44.95): 1688 MHz SAW filter, 80 MHz passband, two LNAs, at least 30 dB gain, 180 mA. The HRPT band (1698-1710 MHz) sits inside that passband. Do NOT buy the SAWbird+ H1: it is centred on 1420 MHz with a 70 MHz passband, so it misses 1.7 GHz.
  
  (4) Bias tee facts:
  - RTL-SDR V4: 4.5 V, up to 180 mA continuous, switched in software (rtl_biast -b 1). Protected by a self-resetting thermal fuse and LDO overcurrent limiting. It cannot power a 13 V LNB.
  - LimeSDR Micro M.2: no bias tee is documented anywhere. The RX ports are bare MHF4 connectors behind SKY13414 SP4T switches. Matched ranges are RX_L 0.3-2.2 GHz, RX_W 0.7-2.6 GHz and RX_H 3.3-3.8 GHz. Maximum safe input is +10 dBm. So every LNA and the LNB on the Lime side need external DC injection, and 137/145 MHz is below the Lime's matched range: put VHF on the RTL-SDR.
  
  (5) Note for the SDR component: as of the June 2026 page update, Crowd Supply lists the LimeSDR Micro M.2 2280 Basic at $249 (+$18 worldwide shipping), pre-order, shipping 15 Dec 2026. That does not match the $199 / ~Sept 30 figures in the stack.
- **Alternatives:**
  1.
    - **Name:** Generic SPF5189Z 50-4000 MHz LNA board (current pick)
    - **Key specs:** Genuine chip: 50-4000 MHz, NF 0.6 dB at 900 MHz, 18.7 dB gain, 5 V at 90 mA. No filter, no shield, usually no bias-tee input.
    - **Price:** $4-10 (user's figure; not re-verified)
    - **Pros:** Cheapest option; wideband; easy to find.
    - **Cons:** Chip end-of-life since 2021 (last-time-buy Sep 2021), so a high risk of fakes or remarked parts. EEVblog reports fakes at 13-15 dB gain. Real NF of the boards is unmeasured. Unshielded and unfiltered, so FM and DVB-T signals get amplified straight into the SDR. Needs separate 5 V wiring.
    - **Availability:** AliExpress and Prom.ua sellers (Prom.ua stock not verified). Genuine stock is gone at distributors.
    - **Q6a compatibility:** Works electrically, but needs a 5 V rail plus a shield can in the case.
    - **Sources:**
      - https://www.qorvo.com/products/p/SPF5189Z
      - https://wiki.satnogs.org/SPF5189_LNA_measurements
      - https://eevblog.com/forum/rf-microwave/lna-spf5189z-issue/msg4074856
  2.
    - **Name:** RTL-SDR Blog Wideband LNA V2 (Qorvo QPL9547)
    - **Key specs:** 100 MHz-6 GHz, NF <1 dB, powered over the coax at 3-5 V. A reseller lists 15-20 dB gain and up to 150 mA. Chip spec: 19.5 dB gain, OIP3 +39 dBm, 0.3 dB NF at 1.9 GHz. Enclosed, SMA connectors.
    - **Price:** $19.95 (208 in stock when checked)
    - **Pros:** Uses Qorvo's official SPF5189Z replacement chip. Runs straight from the RTL-SDR V4's 4.5 V bias tee. Very linear (OIP3 +39 dBm). One part covers 145, 435, 740 MHz, 1.7 and 2.2 GHz.
    - **Cons:** No filtering, so it needs an FM, LTE or SAW filter in strong-signal areas. The board's own gain curve and P1dB are not published. One buyer warns it can saturate the SDR.
    - **Availability:** In stock at rtl-sdr.com store; also EU resellers (Passion Radio).
    - **Q6a compatibility:** Excellent: powered over the coax, no wiring in the case. On the Lime ports it needs a bias tee injector.
    - **Sources:**
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
      - https://forum.qorvo.com/t/qpl9547-noise-figure-data-with-input-6ghz/22808
  3.
    - **Name:** Nooelec SAWbird+ NOAA (137.5 MHz)
    - **Key specs:** 137.5 MHz centre, 5 MHz SAW passband, at least 30 dB gain, two LNAs. 3-5.5 V via SMA bias tee, micro-USB or 0.1" header; 180 mA. EMI shield, M3 mounting holes.
    - **Price:** $44.95 (Nooelec); ~EUR 57 ex-VAT at Passion Radio (older listing)
    - **Pros:** Strong rejection of FM, pager and airband signals for Meteor LRPT. Built-in shield. Can be powered from micro-USB.
    - **Cons:** The 5 MHz passband excludes ISS 145.8 MHz. 180 mA equals the RTL-SDR V4 bias tee's 180 mA limit, so power it from micro-USB instead. NF and rejection in dB are not published.
    - **Availability:** Nooelec store, Newegg (~$72), EU resellers.
    - **Q6a compatibility:** Good. Power from the 5 V rail through micro-USB; mount at the V-dipole.
    - **Sources:**
      - https://www.nooelec.com/store/sawbird-plus-noaa.html
      - https://www.passion-radio.com/sat-accessory/lna-sawbird-1061.html
  4.
    - **Name:** Nooelec SAWbird NOAA (non-plus)
    - **Key specs:** 137.5 MHz, NF ~0.7 dB, at least 20 dB gain, 3-5 V bias tee at ~80 mA (tolerates 12 V, not long-term).
    - **Price:** $49.95 (Nooelec)
    - **Pros:** 80 mA is safely within the RTL-SDR V4's 180 mA bias tee. Published NF.
    - **Cons:** Costs more than the Plus version while giving less gain. Excludes 145.8 MHz.
    - **Availability:** Nooelec store.
    - **Q6a compatibility:** Good: no wiring needed on the RTL-SDR V4.
    - **Sources:**
      - https://www.nooelec.com/store/sawbird-noaa.html
  5.
    - **Name:** Nooelec SAWbird+ GOES (1688 MHz)
    - **Key specs:** 1688 MHz SAW filter with 80 MHz passband (covers 1698-1710 MHz HRPT), two LNAs, at least 30 dB gain, 3-5.5 V, 180 mA, shielded. Power via SMA bias tee, micro-USB or header.
    - **Price:** $44.95 (Nooelec); Newegg $77-84
    - **Pros:** The standard choice for Meteor, Metop and FengYun HRPT; 30 dB gain covers cable and switch losses; rejects LTE downlink at 1805+ MHz (amount not quantified).
    - **Cons:** NF and rejection in dB are not published. LTE Band 3 uplink (1710-1785 MHz, from nearby phones) falls partly inside the 80 MHz passband. 180 mA is too much for the RTL-SDR V4 bias tee (irrelevant here because HRPT goes to the Lime).
    - **Availability:** Nooelec store; Newegg; EU resellers.
    - **Q6a compatibility:** Good. Mount at the helix feed; power from internal 5 V via micro-USB or a bias tee into the Lime RX port.
    - **Sources:**
      - https://www.nooelec.com/store/sawbird-plus-goes.html
      - https://itu.int/dms_pub/itu-r/opb/rep/R-REP-SA.2329-2014-PDF-E.pdf
      - https://www.sdrplay.com/satellite-decoding-software-now-supports-all-rsps/
  6.
    - **Name:** Nooelec SAWbird GOES (non-plus)
    - **Key specs:** 1688 MHz, 80 MHz SAW passband, at least 20 dB gain, ~30 mA at 3-5 V.
    - **Price:** $39.95 (Nooelec)
    - **Pros:** Low current: any bias tee can power it, including the RTL-SDR V4. Cheapest filtered L-band LNA found from a brand-name maker.
    - **Cons:** 10 dB less gain and slightly higher noise than the Plus.
    - **Availability:** Nooelec store.
    - **Q6a compatibility:** Good.
    - **Sources:**
      - https://www.nooelec.com/store/sawbird-goes.html
  7.
    - **Name:** LNA4ALL (9A4QV, PSA4-5043+)
    - **Key specs:** 28 MHz-2.5 GHz. ~16 dB gain per unit. NF ~0.7 dB measured at 1420 MHz for two units in series (chip: 0.75 dB at 1 GHz, 0.98 dB at 2 GHz). IP3 ~33.5 dBm. 6-9 V at 55-65 mA, or 5 V with a jumper. ESD protection on the chip die.
    - **Price:** EUR 20-23 + EUR 7 tracked shipping worldwide
    - **Pros:** Proven in SatNOGS use; EU seller (Croatia); low noise.
    - **Cons:** Bare board with no filter. Running it over the coax needs a DIY mod (DIY bias tee; the seller no longer supplies the parts). Ordered by email. Stock listed as 250 pcs in May 2025; current stock not verified for Oct 2026.
    - **Availability:** Direct from lna4all.blogspot.com (email order).
    - **Q6a compatibility:** OK, but needs a case and power wiring.
    - **Sources:**
      - https://lna4all.blogspot.com/
      - https://www.minicircuits.com/pdfs/PSA4-5043+.pdf
  8.
    - **Name:** Uputronics 137.5 MHz filtered preamp
    - **Key specs:** High-pass filter, then a 137.5 MHz SAW filter (7.6 MHz passband, ~1.4 dB loss), then a PSA4-5043 LNA; at least 21 dB gain. Powered by USB or bias tee. Metal case.
    - **Price:** ~EUR 48 incl. VAT (Kubii, 'last items')
    - **Pros:** Filter-first layout survives strong FM very well; ready to use in a metal case.
    - **Cons:** Filtering before the LNA adds ~1.4 dB to the noise figure. Stock is thin. No 435 MHz or 1.7 GHz versions were found.
    - **Availability:** Kubii, The Pi Hut (EU/UK).
    - **Q6a compatibility:** Good.
    - **Sources:**
      - https://kubii.com/en/network-modules/3349-lna-amplifier-modules-with-saw-filter-and-single-frequency-3272496306646.html
      - https://thepihut.com/collections/uputronics
  9.
    - **Name:** GPIO Labs PSA4-5043+ inline LNA (bias tees on input and output) / GPIO Labs Airband filtered LNA
    - **Key specs:** Inline LNA: 10 MHz-2 GHz, 22 dB at 100 MHz, 18 dB at 500 MHz, 12 dB at 1 GHz; NF 0.7 dB at 100 MHz; 3.3-10 V. Airband LNA: 118-140 MHz, 20 dB gain, NF <1 dB, built-in bias tee.
    - **Price:** $60 (inline LNA); $99 (Airband LNA)
    - **Pros:** Can pass DC through to an active antenna. Good published data.
    - **Cons:** Expensive. The Airband LNA's 118-140 MHz range excludes 145.8 MHz. The Tindie page showed no shipping option for the default destination, so shipping to Ukraine is unverified.
    - **Availability:** Tindie (ships from Canada).
    - **Q6a compatibility:** OK.
    - **Sources:**
      - https://www.tindie.com/products/gpio/low-noise-inline-amplifier-2ghz-w-bias-tee/
      - https://www.tindie.com/products/gpio/airband-pre-filtered-lna-w-bias-tee-118-140-mhz/
  10.
    - **Name:** Chinese '0.1-2000 MHz 30 dB' wideband LNA boards
    - **Key specs:** Seller lists 32 dB at 0.1 MHz, 31 dB at 500 MHz, 29 dB at 1 GHz, 25 dB at 1.5 GHz, 20 dB at 2 GHz. Noise figure NOT published. Similar Chinese wideband modules state 3.2-3.5 dB typical NF.
    - **Price:** ~$10-20 (not verified for Oct 2026)
    - **Pros:** Cheap, high gain.
    - **Cons:** Unknown and probably multi-dB NF, so unsuitable as the first stage at 1.7 GHz. No filter. 30 dB of wideband gain will overload the RTL-SDR with FM and DVB-T.
    - **Availability:** AliExpress, Newegg marketplace.
    - **Q6a compatibility:** Not recommended.
    - **Sources:**
      - https://www.newegg.com/p/2S7-09HN-01T96
      - https://www.com-mw.com/en/product/8117336958.html
  11.
    - **Name:** Nooelec Flamingo+ FM vs RTL-SDR Blog FM bandstop
    - **Key specs:** Flamingo+: >60 dB average (>70 dB peak) in the FM stopband; -3 dB edges at 75 and 120 MHz; <0.25 dB loss out of band; passes DC (at least 250 mA). RTL-SDR Blog: >50 dB at 88-108 MHz; <0.5 dB loss 0-1 GHz, <1.5 dB 1-3 GHz; DC pass not stated.
    - **Price:** Flamingo+ $24.95; RTL-SDR Blog $16.95 (131 in stock)
    - **Pros:** Flamingo+ rejects more and is confirmed to pass bias-tee DC. The RTL-SDR Blog filter is cheaper.
    - **Cons:** Flamingo+'s upper -3 dB edge at 120 MHz means some loss at 137 MHz is possible (not specified). The RTL-SDR Blog filter's DC behaviour needs checking with a multimeter.
    - **Availability:** Nooelec store; rtl-sdr.com store.
    - **Q6a compatibility:** Passive; no power needed.
    - **Sources:**
      - https://www.nooelec.com/store/flamingo-plus-fm.html
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-broadcast-fm-band-stop-filter/
  12.
    - **Name:** Bias tees / LNB injectors (generic 10 MHz-6 GHz, Passion Radio BT4G, RF Konnect module, GPIO Labs)
    - **Key specs:** Generic 10 MHz-6 GHz: <1.2 dB loss, <0.5 A, 1-50 V. BT4G: 30 MHz-4 GHz, SMA. RF Konnect module: 30 V / 500 mA max. GPIO Labs: 10 MHz-7 GHz; 0.2 dB loss at 100 MHz, 0.7 dB at 1 GHz, 0.8 dB at 2 GHz; 250 mA; +15 V max.
    - **Price:** Generic ~$5-10 (AliExpress, not verified); RF Konnect EUR 6.73 ex-VAT; BT4G EUR 18.50 ex-VAT; GPIO Labs $57
    - **Pros:** Needed for every powered device on the Lime side and for the 13/18 V LNB. Cheap units are adequate at 740 MHz.
    - **Cons:** Cheap units have no published response curve. GPIO Labs' 15 V maximum rules out 18 V horizontal polarisation. All add 0.2-1.2 dB of loss, so place them after the LNA.
    - **Availability:** AliExpress; Passion Radio (FR); Tindie.
    - **Q6a compatibility:** Mount inside the case; feed from a regulated 5 V or 13/18 V rail.
    - **Sources:**
      - https://passion-radio.com/satellite-qo-100/63T301-2194.html
      - https://www.passion-radio.com/satellite-qo-100/bias-t-bt4g-760.html
      - https://www.passion-radio.com/satellite-qo-100/bias-tee-rf-power-supply-module-for-lnb-qo100-and-lna-head-1267.html
      - https://www.tindie.com/products/gpio/bias-tee-operates-from-10mhz-to-7000mhz/
  13.
    - **Name:** Spacewalker LNA 434 MHz (Decent Labs)
    - **Key specs:** Two QPL9547 LNAs, NF ~0.2 dB, 25 dB gain at 434 MHz, three 434 MHz SAW filters (~425.7-443 MHz at -3 dB, per an rtl-sdr.com comment), three shield cans, USB-C or bias-tee power.
    - **Price:** Not announced
    - **Pros:** Best-specified filtered 70 cm LNA for CubeSats; used by SatNOGS stations.
    - **Cons:** Crowd Supply page still says 'launching soon': cannot be bought in Oct 2026. The schematics are open on GitHub (zodoczi/Spacewalker-LNA) for a DIY build.
    - **Availability:** Not available yet.
    - **Q6a compatibility:** Would be ideal.
    - **Sources:**
      - https://www.crowdsupply.com/decent-labs/spacewalker-lna-434-mhz
      - https://www.rtl-sdr.com/spacewalker-lna-434-mhz-in-prelaunch-at-crowdsupply/
  14.
    - **Name:** HMC241-based SP4T RF switch board (antenna/SDR routing)
    - **Key specs:** Switch chip HMC241AQS16: DC-3.5 GHz, 0.7 dB loss at 2 GHz, ~36 dB isolation, single +5 V supply, TTL control with an on-chip 2:4 decoder.
    - **Price:** Not verified (a Fruugo listing exists; cheaper on AliExpress)
    - **Pros:** The Q6A's GPIO can select an antenna from software. Covers every band including the 740 MHz LNB IF.
    - **Cons:** Must sit AFTER the LNAs (adds 0.7 dB loss) and does not pass DC, so power the LNAs on the antenna side. Clone boards may use the obsolete HMC241 or a different variant. Check the logic level (3.3 V vs 5 V).
    - **Availability:** AliExpress / marketplaces.
    - **Q6a compatibility:** Good with a 5 V rail and 2 GPIO lines.
    - **Sources:**
      - https://www.analog.com/en/products/HMC241AQS16.html
      - https://www.fruugo.ca/sp4t-rf-switch-board-dc%25E2%2580%259035ghz-high-isolation-low-loss-easy-use-for-base-stations/p-392573442
  15.
    - **Name:** LimeFEA M.2 2280 (Lime's official front-end)
    - **Key specs:** Receive 100 MHz-4 GHz with LNAs (preliminary: NF 0.8 dB / 18.2 dB gain at 900 MHz, 0.8 dB / 12.9 dB at 1900 MHz). Adapter for a full-size PCIe x4 slot.
    - **Price:** $299 + $18 shipping; pre-order, ships 15 Dec 2026
    - **Pros:** Integrated LNAs and switching.
    - **Cons:** Desktop PCIe card form factor: unusable in a palm-sized handheld. No filter banks or bias tee mentioned. Expensive.
    - **Availability:** Crowd Supply pre-order.
    - **Q6a compatibility:** Not compatible (needs a full-size PCIe slot).
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
- **Recommended:**
  - **Name:** Per-band filtered chain: Nooelec SAWbird+ NOAA (137) + Flamingo+ FM with RTL-SDR Blog Wideband LNA V2 (145.8 / 435 / 2.2 GHz) + Nooelec SAWbird+ GOES (HRPT) + 13/18 V bias-tee injector for the Bullseye LNB
  - **Why:** Each chain is listed as antenna to SDR.
  
  (a) 137 MHz Meteor LRPT: V-dipole -> SAWbird+ NOAA at the antenna ($44.95; 5 MHz SAW, at least 30 dB gain), powered over micro-USB from a clean 5 V rail because its 180 mA equals the V4 bias tee limit -> RTL-SDR V4 (VHF triplexer path 28-250 MHz plus FM notch).
  
  (b) 145.8 MHz ISS: WB2HOL Yagi -> Flamingo+ FM ($24.95; >60 dB; passes DC) -> RTL-SDR Blog LNA V2 ($19.95), powered by the V4's 4.5 V bias tee -> RTL-SDR V4. The ISS signal is strong, so the LNA is optional; the FM filter is the important part.
  
  (c) 435-438 MHz: 70 cm Yagi -> LNA V2 at the antenna ($19.95) -> bias tee (5 V) -> Lime RX (L path, 0.3-2.2 GHz) or the RTL-SDR. Do not add a generic 433.92 MHz ISM SAW filter: they are too narrow for 435-438 MHz.
  
  (d) 1.70 GHz HRPT: 11-turn helix -> SAWbird+ GOES at the feed ($44.95; 1688 MHz / 80 MHz SAW, at least 30 dB gain) -> short coax -> Lime RX1 (W path, 0.7-2.6 GHz). Power it from 5 V via micro-USB or a bias tee. The RTL-SDR V4 tops out at 1.766 GHz and 2.56 MHz bandwidth, so it is marginal or unusable for HRPT.
  
  (e) QO-100: dish + Bullseye LNB (50-66 dB gain, NF 0.5 dB; needs 13-18 V on the coax) -> bias tee injector fed with regulated 13.0 V (18 V for the wideband horizontal transponder) -> Lime RX2 or the RTL-SDR. No LNA is needed.
  
  (f) S-band 2.2 GHz: LNA V2 on the Lime W path. A suitable bandpass filter was not identified in this research.
  
  Why this beats the current picks: it replaces an end-of-life, likely counterfeit SPF5189Z with Qorvo's own replacement chip in a ready, coax-powered case. Every band where interference is known (FM and pagers at 137, LTE 1800 at 1.7 GHz) gets a SAW or bandstop filter. Every part has a published maker spec. Total is about $175-200 excl. shipping and VAT: SAWbird+ NOAA 44.95 + Flamingo+ 24.95 + 2x LNA V2 39.90 + SAWbird+ GOES 44.95 + 2 bias tees ~EUR 7-18.50 each.
  - **Price:** ~$175-200 (amplifiers, filters, injectors); + MHF4L-SMA bulkhead pigtails $6 each (Crowd Supply); HMC241 switch optional (price unverified)
  - **Sources:**
    - https://www.nooelec.com/store/sawbird-plus-noaa.html
    - https://www.nooelec.com/store/sawbird-plus-goes.html
    - https://www.nooelec.com/store/flamingo-plus-fm.html
    - https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
    - https://www.rtl-sdr.com/v4/
    - https://www.rtl-sdr.com/wp-content/uploads/2024/12/RTLSDR_V4_Datasheet_V_1_0.pdf
    - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
    - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
    - https://www.elektor.com/products/bullseye-10-khz-tcxo-lnb-for-qo-100
    - https://www.crowdsupply.com/lime-micro/limesdr-micro
- **Budget option:**
  - **Name:** RTL-SDR Blog FM bandstop + RTL-SDR Blog Wideband LNA V2 (all VHF/UHF) + Nooelec SAWbird GOES (non-plus) for HRPT + generic bias tee for the LNB
  - **Why:** About $85 plus shipping: $16.95 + $19.95 + $39.95 + ~EUR 7 for the RF Konnect or a generic 10 MHz-6 GHz bias tee.
  
  - One LNA V2 is moved between the V-dipole, 2 m and 70 cm Yagis. It is powered by the RTL-SDR V4's 4.5 V bias tee, with the FM bandstop in front of it at VHF.
  - The SAWbird GOES (20 dB, 30 mA) is low enough current for any bias tee, and its SAW filter still blocks LTE 1800 downlink.
  - The LNB gets 13 V from a buck-boost converter through the generic bias tee.
  
  Compared with the primary option, it gives up Meteor-specific SAW filtering at 137 MHz (fine at rural or quiet sites) and has 10 dB less HRPT gain. It is still better than unfiltered SPF5189Z boards of unknown origin. Check the RTL-SDR Blog FM filter for DC pass-through with a multimeter before putting it between the bias tee and the LNA.
  - **Price:** ~$85 + shipping/VAT
- **Risks:**
  - SPF5189Z: end-of-life since 2021 (last-time-buy 15 Sep 2021). Boards sold in 2026 may carry fakes (EEVblog: 13-15 dB gain instead of 18.7 dB), and no published measurements exist for their real noise figure.
  - The SAWbird+ boards draw 180 mA, exactly the RTL-SDR V4 bias tee's 180 mA continuous rating; in a warm case the thermal fuse may trip. Power them from micro-USB, or use the non-plus versions (80 mA / 30 mA).
  - LimeSDR Micro: no documented bias tee. RX ports are matched only from 300 MHz (L path) and 700 MHz (W path), so performance at 137/145 MHz is unspecified; keep VHF on the RTL-SDR. Maximum safe input is +10 dBm: always use a DC-blocked injector, never raw LNB voltage.
  - Lime price and date have changed: Crowd Supply now lists the M.2 Basic at $249 with shipping on 15 Dec 2026, not $199 / Sept 30. A pre-order can slip further.
  - LTE Band 3 uplink (1710-1785 MHz) partly overlaps the SAWbird GOES 80 MHz passband (nominally ~1648-1728 MHz), so nearby phones can still interfere. Nooelec publishes no numeric rejection at 1805+ MHz.
  - QO-100 polarisation: the narrowband transponder is vertical (12-14 V) and the wideband one is horizontal (18 V). A full 4S pack is 16.8 V, which may cross a typical LNB's polarisation threshold (general LNB convention, not measured), so feed a regulated 13.0 V, not raw battery. The Bullseye's current draw is not published.
  - Bias tee into DC-shorted antennas (hairpin-matched WB2HOL, folded dipoles) shorts the supply. The V4 is protected, but RTL-SDR warns that days of shorting can damage the LDO or fuse.
  - Generic 433.92 MHz ISM SAW filters are too narrow to pass 435-438 MHz. The Spacewalker 434 filtered LNA (QPL9547, 0.2 dB NF) is not purchasable yet.
  - Chinese '0.1-2000 MHz 30 dB' LNAs publish no noise figure (similar modules: 3.2-3.5 dB) and have too much wideband gain; avoid them as a first stage.
  - Shipping to Ukraine was not verified for Nooelec, RTL-SDR Blog or GPIO Labs (the Tindie page showed no shipping to the default destination). EU resellers (Passion Radio FR, Kubii, The Pi Hut) are fallbacks. Prom.ua and Rozetka prices could not be checked.
  - Research gap: the session's web-search limit ran out mid-task. Generic bias tee, HMC241 board and Ukrainian LNB-injector prices, a 2.2 GHz bandpass filter, and the RTL-SDR Blog FM filter's DC pass-through remain unverified.
- **Integration notes:**
  - Port plan with no RF switch needed: RTL-SDR V4 for VHF (137 / 145.8); Lime RX1 W path (0.7-2.6 GHz) for HRPT and 2.2 GHz; Lime RX2 L path (0.3-2.2 GHz) for 435 MHz or the QO-100 IF (739.5-740 MHz). Use MHF4L-to-SMA(f) bulkhead pigtails ($6, Crowd Supply) to bring the Lime ports out to SMA connectors on the case.
  - Lime-side powering: no bias tee on the Lime. Either run the SAWbird and LNA V2 from a clean 5 V LDO rail (micro-USB cable) when the antenna is within ~1 m, or put a 10 MHz-6 GHz bias tee inside the case (DC-block side to the Lime). Switch the bias with a Q6A GPIO driving a P-MOSFET load switch plus a polyfuse.
  - LNB supply: make 13.0 V (optionally 18 V by switching a feedback resistor from a GPIO) with a buck-boost from the 4S pack (12-16.8 V). Allow roughly 200-300 mA (the Bullseye's draw is unpublished, so this is an assumption). Add an F-to-SMA adapter. A 6-10 dB attenuator may be needed on the RTL-SDR because the LNB's 50-66 dB gain is high.
  - Order of stages: where a strong interferer is known (FM, LTE 1800), filter before or inside the LNA (the SAWbird+ does this internally). For 435 MHz and 2.2 GHz, put the LNA first. Any splitter or SP4T switch (HMC241: 0.7 dB, 5 V, TTL) goes after the LNAs. The HMC241 needs DC blocking caps, so inject LNA power on the antenna side of it.
  - Sharing one antenna with both SDRs: a 2-way splitter after a gain stage of at least 20 dB costs ~3.5 dB, which is negligible. Do not split before the LNA.
  - Noise reality: at 137/145 MHz, galactic and man-made noise dominate, so a 0.7 dB vs 1.5 dB LNA barely matters and filtering and linearity matter most. At 1.7 GHz the sky is cold, so the LNA's noise figure and its placement at the feed decide whether HRPT works (a Reddit builder blamed 5 m of coax ahead of the LNA for failure).
  - EMI inside the case: the Q6A, its fan and the buck converters radiate. Keep the LNAs at the antennas, use shielded boards, put ferrites on the RTL-SDR's USB lead, and consider turning off the Q6A's 2.4 GHz Wi-Fi during S-band and L-band captures.
  - Current budget (excluding the LNB): 2x SAWbird+ at 180 mA plus LNA V2 at up to 150 mA, about 0.5 A at 5 V. The RTL-SDR V4 itself draws 250-270 mA on a USB 2.0 port, so the V4 plus its bias-tee LNA stays under 500 mA.
  - ESD and overload: the Lime's maximum safe input is +10 dBm. Discharge the coax shield and centre to ground before connecting antennas. LNA4ALL and Spacewalker have ESD protection on the die or the pigtail. PIN-diode limiters (Mini-Circuits VLM-33+/RLM-33+; prices not verified) can sit ahead of the SDR; the TAPR limiter is meant for 54 MHz and below, so it does not suit 1.7 GHz.
- **Double duty opportunities:**
  - The Nooelec Flamingo+ FM passes bias-tee DC (rated at least 250 mA), so the RTL-SDR V4's 4.5 V bias tee can feed an LNA through it: no separate injector on the VHF chain.
  - The RTL-SDR V4's built-in 4.5 V / 180 mA bias tee powers the LNA V2 or the SAWbird NOAA (80 mA): no external bias tee for the whole RTL-SDR path.
  - SAWbird boards accept 3.3-5.5 V on micro-USB or a 0.1" header, so a handheld-mounted helix or dipole LNA can run off the internal 5 V rail with no bias tee at all.
  - The Bullseye LNB has 50-66 dB of gain, so the QO-100 path needs no LNA, only a 13 V bias tee. Making the supply switchable 13/18 V also adds the wideband DATV transponder (horizontal polarisation).
  - Lime RX1 + RX2 + RTL-SDR give three antennas connected at once, so no RF switch is needed for v1; an HMC241 SP4T can be added later under Q6A GPIO control.
  - One LNA type (RTL-SDR Blog V2, 100 MHz-6 GHz) covers 145.8, 435-438 and 2.2 GHz: buy 2-3 identical units as interchangeable spares.
  - Cross-component note: the LimeSDR Micro M.2 GNSS variant ($299 vs $249 Basic) has a GNSS chip with an active-antenna MHF4 connector, which could replace the separate u-blox or ATGM module. That costs $50 more than an M10 module, so it is only worth it for tight time and frequency sync.
- **Confidence:** medium

## Форуми та досвід спільноти (`forums`)

_Run `wf_30889068-251`_

- **Component:** RF front-end: LNAs, filters, bias tees, LNB power, antenna sharing, ESD protection
- **Experiences:**
  1.
    - **Product:** RTL-SDR Blog Wideband LNA V1 (SPF5189Z, bias-tee powered) + RTL-SDR Blog FM bandstop vs 'Distill FM' bandstop
    - **Source url:** https://community.libre.space/t/fm-bandstop-not-working/13752
    - **Community:** SatNOGS community (community.libre.space)
    - **What they built:** SatNOGS UHF station (F4NER, Sept 2025). Chain: QFH -> FM bandstop -> RTL-SDR Blog wideband LNA -> RTL-SDR, LNA powered from the dongle's bias tee. Three FM transmitters 1-2.5 km away.
    - **Problems:**
      - Without a bandstop, FM overload put the same FM station every ~10 MHz, including in the 70 cm band.
      - With the RTL-SDR Blog bandstop plus the powered LNA, the noise floor rose a lot at 100 MHz and interference appeared at 437 MHz. The 'Distill FM' filter worked, but after re-cabling the problem moved to the Distill filter, so the filter was not the cause.
      - A 10 m 75-ohm TV cable alone picked up FM.
      - pe2bz (1.2 km from a 60 kW FM station) sees FM harmonics around 1550 and 1700 MHz when running unfiltered S-band with a preamp.
    - **Fixes:**
      - Put the FM bandstop BEFORE the LNA when FM is strong. SA2KNG: a decent filtered LNA has a low-loss filter first or an LNA-filter-LNA design.
      - Keep the LNA at the antenna and filters at the SDR when FM is not overloading the LNA.
      - Check that a filter passes DC with an ohmmeter before putting it between the bias tee and the LNA.
      - Re-adjust SDR gain whenever an LNA is added.
      - pe2bz removes the FM harmonics at L/S band with an FM bandstop or with 1550/2150 MHz bandpass filters.
    - **Outcome:** Not cleanly resolved. The user concluded the bandstop was not the issue. The wideband SPF5189Z LNA was judged 'not a very good LNA' for a strong-FM site.
  2.
    - **Product:** RTL-SDR Blog Wideband LNA V1 (SPF5189Z) with RTL-SDR Blog V3 bias tee
    - **Source url:** https://community.libre.space/t/rtl-sdr-com-wideband-lna-w-rtl-sdr-com-dongle-bias-t/4601
    - **Community:** SatNOGS community
    - **What they built:** SatNOGS station with a bias-tee-powered LNA (K3RLD, 2019).
    - **Problems:**
      - The LNA looked dead. The bias tee measured 4.7 V after rtl_biast, but the next program to open the dongle switched it off again.
      - The SatNOGS image's old gr-osmosdr/librtlsdr had no bias-tee API.
      - The bias tee stayed on after observations.
    - **Fixes:**
      - Device string rtl=0,bias=1 (gqrx), with no spaces.
      - SATNOGS_DEV_ARGS rtl,buffers=32,buflen=16384,bias=1.
      - Upgrade to the Buster image.
      - Post-observation script /path/rtl_biast -b 0.
    - **Outcome:** Working bias tee and LNA confirmed (signal scale -50 dB -> -20 dB on an FS-3 pass).
  3.
    - **Product:** RTL-SDR Blog V4 bias tee + SatNOGS kit LNA (2026)
    - **Source url:** https://community.libre.space/t/v4-rtl-sdr-bias-tee-issue/14699
    - **Community:** SatNOGS community
    - **What they built:** SatNOGS kit (WT0DX, Apr-May 2026): Raspberry Pi, RTL-SDR V4, turnstile, sealed LNA box.
    - **Problems:**
      - No satellites received; 0 V measured at the LNA input.
      - With 'bias=1' or 'biastee=1' in the soapy string, the client actively turned the bias tee OFF at the start of each observation.
    - **Fixes:**
      - Use driver=rtlsdr,biastee=true. It is a bool, not 1.
      - Debug with docker exec satnogs_satnogs-client rtl_biast -d 0 -b 1.
      - Check the V4's red bias LED.
    - **Outcome:** Resolved. The bias stays on between passes, which PE0SAT says is harmless. PE0SAT runs RF gain 36.4 with an LNA.
  4.
    - **Product:** RTL-SDR Blog V4 + Nooelec SAWbird+ NOAA on internal bias tee (ARM, Raspberry Pi 3B+)
    - **Source url:** https://community.libre.space/t/satnogs-3649-rtl-sdr-blog-v4-issues/11942
    - **Community:** SatNOGS community
    - **What they built:** 137 MHz SatNOGS station: V4 + SAWbird+ NOAA powered by the V4 bias tee, on a Pi 3B+ (2024).
    - **Problems:**
      - Blank spectrum.
      - Stock Debian librtlsdr does not support the V4. The RTL-SDR Blog .deb build can be replaced by apt upgrades.
      - SoapySDR 'make(): no match' error.
    - **Fixes:**
      - Install a V4-capable librtlsdr: SatNOGS package 2.0.2 (SA2KNG/Acinonyx builds) or the RTL-SDR Blog driver.
      - Verify with SoapySDRUtil --probe="driver=rtlsdr". It must print 'RTL-SDR Blog V4 Detected'.
      - Enable the bias tee with driver=rtlsdr,biastee=true.
    - **Outcome:** Fixed for the other posters (va2wbt, w6msu: 'dead to the world until I read this'). The original poster still had 'no match' at the end of the thread.
  5.
    - **Product:** RTL-SDR Blog V4 bias tee under SatDump CLI (Raspberry Pi 4, Docker)
    - **Source url:** https://github.com/SatDump/SatDump/issues/1030
    - **Community:** GitHub issues (SatDump)
    - **What they built:** Headless SatDump autotrack station on 137.5 MHz (Aug 2025).
    - **Problems:**
      - The 'bias' parameter in autotracker.json was ignored, and gain and DC-block were not applied.
      - The GUI checkbox needed toggling off and on.
      - The same behaviour appeared in SDR++.
    - **Fixes:**
      - Workaround: rtl_eeprom -b1, which forces the bias tee on permanently in EEPROM.
      - Real cause: the Docker build copied Debian's default librtlsdr (no V4 support) instead of the self-built driver. Fixed the build.
    - **Outcome:** Resolved by the user; no SatDump code change.
  6.
    - **Product:** Generic AliExpress/eBay SPF5189Z LNA modules
    - **Source url:** https://www.eevblog.com/forum/rf-microwave/lna-spf5189z-issue/
    - **Community:** EEVblog forum
    - **What they built:** SPF5189Z module at 5 V in front of an RTL-SDR V3 (2019-2020).
    - **Problems:**
      - After hours of use the output shorted. Current jumped to the 200 mA limit, and the input/output measured 17/6.3 ohms.
      - The replacement chip from AliExpress was fake: 145 mA, very hot, ~10 dB less gain below 100 MHz, burned out overnight.
      - OH2LIY (Dec 2020): eBay module drew >150 mA at 3 V with gain and NF far off spec. Suspected to be a remarked different MMIC, possibly a TQP3M9009.
    - **Fixes:**
      - Do not power the module by touching a wire to the supply; use a switched supply that ramps up gently.
      - Add a uF bulk capacitor and twist long leads.
      - Add a series resistor or an L78L05 as a current limiter, plus a TVS diode near the device.
      - Solder supply leads directly to the PCB.
      - Buy from reputable sources. eBay refunded the fake.
    - **Outcome:** No root cause for the first failure. Several posters confirmed that counterfeit SPF5189Z parts are common. Genuine parts draw 70-90 mA at 5 V.
  7.
    - **Product:** RTL-SDR Blog Wideband LNA V1 (SPF5189Z) - buyer reports
    - **Source url:** https://www.rtl-sdr.com/new-products-in-our-store-wideband-lna-spare-metal-v3-enclosures/
    - **Community:** RTL-SDR.com article comments
    - **What they built:** Bias-tee-powered LNA ahead of an RTL-SDR V3 for airband and VHF.
    - **Problems:**
      - Oleg (Feb 2020, Russia): the LED lit but the LNA gave no gain. Weak stations disappeared and the board stayed cold.
      - robert (Sep 2023): the same symptom.
      - Questions about the BT jumper and the J2 Vcc header (Feb 2026) were undocumented.
    - **Fixes:**
      - Admin: connecting the LNA backwards will not break it.
      - Admin: put the FM trap after the LNA unless FM overloads the LNA; if images appear, put it before.
      - Admin: the BT jumper disables DC on the output when powering through the Vcc pads at 3-5 V.
    - **Outcome:** The no-gain units were treated as defective. No root cause was posted.
  8.
    - **Product:** SPF5189Z on a 137 MHz V-dipole; FM block in front
    - **Source url:** https://community.libre.space/t/seem-to-have-similar-worse-performance-with-lna/5867
    - **Community:** SatNOGS community
    - **What they built:** Indoor V-dipole -> SPF5189Z -> RTL-SDR on a Pi (2020).
    - **Problems:**
      - Worse reception with the LNA. There was no 5 V at the LNA because the bias was not actually on.
      - A second user saw local BBC FM breaking through at 137 MHz once the LNA worked.
      - Putting an FM block in front of the LNA removed the FM harmonics but also 'seemed to trash any satellite reception'.
    - **Fixes:**
      - SatNOGS pre/post-observation scripts running rtl_biast -b 1 / -b 0.
      - Check the LNA voltage with a meter.
      - Reduce SDR gain.
      - Move the Pi and its PSU away from the indoor antenna.
    - **Outcome:** Partial. Confirms that 137 MHz needs filtering ahead of an unfiltered wideband LNA, and that the filter's loss and placement matter.
  9.
    - **Product:** LNA4ALL as a 2 m mast preamp
    - **Source url:** https://community.libre.space/t/2m-lna4all-imd-with-moxon-antenna/3946
    - **Community:** SatNOGS community
    - **What they built:** 2 m Moxon -> LNA4ALL -> receiver tuned to 144.8 MHz (2019).
    - **Problems:**
      - Each time a 152.48 MHz pager transmitter keyed, the 96.1 FM station was heard clearly on 144.8 MHz (intermod).
      - A coax stub notch did not help.
    - **Fixes:**
      - An inline FM broadcast filter removed the intermod.
    - **Outcome:** Partial. The pager still raised the noise floor by ~5 dB; dedicated pager filters (Par Electronics) were considered expensive.
  10.
    - **Product:** LNA4ALL / SPF5189 / INA02184 / Mini-Circuits ZX60-P103LN+
    - **Source url:** https://community.libre.space/t/tested-and-recommended-lnas/3585
    - **Community:** SatNOGS community
    - **What they built:** Various SatNOGS stations (2019).
    - **Problems:**
      - Two LNA4ALLs 'failed': one broke mechanically and after repair only raised the noise floor; the second behaved the same.
      - ZX60-P103LN+ picked up FM harmonics far up into VHF.
      - A generic SPF5189 gave only ~15 dB gain.
    - **Fixes:**
      - Add an FM notch.
      - One user replaced the SPF5189 with a 12 V INA02184 (~30 dB) behind a 2 m filter.
      - HobbyPCB 144 MHz bandpass: ~1.4 dB loss at 137 MHz, used instead of an FM notch.
    - **Outcome:** Improvement over the dongle's own gain was described as 'perhaps not by much'.
  11.
    - **Product:** Broadband vs filtered LNAs (SHF Mini-BB, HA8ET, vhfdesign SAW LNAs, Uputronics, MiniKits)
    - **Source url:** https://community.libre.space/t/rx-only-filtered-lnas-for-vhf-and-uhf-where-to-find/6897
    - **Community:** SatNOGS community
    - **What they built:** SatNOGS VHF/UHF station with strong local interference (SM0TGU, 2020).
    - **Problems:**
      - With only -1.5 dB coax loss, an unfiltered broadband LNA gave no major improvement over the RTL-SDR V3 at higher gain.
    - **Fixes:**
      - Moved to filtered RX LNAs (HA8ET, Hungary).
      - Other options named: vhfdesign 70 cm SAW LNAs (SAV-541+ or ATF-53189; NF <0.3-0.4 dB; -3 dB BW <20 MHz; OIP3 33-37 dBm), Uputronics filtered preamps, MiniKits EME220/221, TGN twin-notch filters.
    - **Outcome:** Consensus: with short feedlines, filtering matters more than more gain.
  12.
    - **Product:** Chinese preamps on a QFH; Uputronics 137 MHz filtered LNA
    - **Source url:** https://community.libre.space/t/qfh-antennas-can-burn-pre-amps/1959
    - **Community:** SatNOGS community
    - **What they built:** QFH -> preamp -> SDR (2018-2019).
    - **Problems:**
      - Two Chinese preamps burned when connected to the same QFH (DC-shorted loop). Static or handling ESD is the likely cause.
    - **Fixes:**
      - Anti-parallel BAV99 diodes at the LNA input (9A4QV's advice), which solved it for didierp09.
      - Uputronics 137 MHz filtered LNA ran 2 years without failure.
    - **Outcome:** Resolved with input protection and a commercial filtered LNA.
  13.
    - **Product:** Nooelec SAWbird+ NOAA
    - **Source url:** https://community.libre.space/t/observation-10391348-noaa-19-33591/12377
    - **Community:** SatNOGS community
    - **What they built:** V-dipole (resonant at 136 MHz) -> 3 ft Mini8 -> SAWbird+ NOAA -> NESDR SMArTee v2, near a 104 MHz FM station (2024).
    - **Problems:**
      - Empty waterfall on an overhead pass, although the same dipole without LNA/SAW had worked well before.
    - **Fixes:**
      - Suggestions only: run manual passes in SDR++/GQRX and look for local interference; check cable lengths.
    - **Outcome:** Unresolved in the thread. Another SatNOGS user (hb9fxx, https://community.libre.space/t/raspberry-pi-zero-2w/8575) notes that the SAWbird+ NOAA restricts the station to ~137 MHz.
  14.
    - **Product:** Nooelec SAWbird GOES / SAWbird+ GOES for HRPT
    - **Source url:** https://sgcderek.github.io/blog/beginner-hrpt-guide.html
    - **Community:** Builder blog (OK9SGC Derek) / rtl-sdr.com coverage
    - **What they built:** HRPT stations with a helix feed and RTL-SDR or other SDRs.
    - **Problems:**
      - Wideband LNAs (LNA4ALL, SPF5189Z) work at 1.7 GHz but strong lower-band signals, especially FM, can completely overwhelm HRPT.
      - A SAWbird powered externally 'has been proven to leak current into the RF output port and into the SDR'.
      - The SAWbird+ (180 mA) stresses the SDR and the USB port when bias-tee powered.
    - **Fixes:**
      - Use a filtered LNA; Derek states a 1650-1720 MHz passband.
      - For short coax runs he prefers the non-plus SAWbird GOES (30 mA).
      - Add a separate DC block at the SDR input when the LNA is powered from USB or the header.
      - Nooelec's product page likewise says to add a DC block between an externally powered LNA and the SDR, because the NESDR's ESD diode can trip.
    - **Outcome:** Widely used setup. The DC-leak warning matters for powering a SAWbird into the LimeSDR Micro's bare MHF4 ports.
  15.
    - **Product:** 3D-printed helicone for 1.7 GHz, hand-tracked
    - **Source url:** https://www.rtl-sdr.com/saveitforparts-testing-a-3d-printable-satellite-antenna-for-noaa-meteor-and-other-polar-orbiting-l-band-satellites/
    - **Community:** RTL-SDR.com article (Saveitforparts video)
    - **What they built:** Handheld helicone + RTL-SDR + SatDump on a phone, hand tracking NOAA HRPT.
    - **Problems:**
      - The printed scaffold legs warped.
      - The article does not name the LNA or filter.
    - **Fixes:**
      - Modified the model with centre supports.
    - **Outcome:** NOAA HRPT images received by hand tracking with a handheld helix-type antenna and no dish. The 0-comment article gives no front-end details.
  16.
    - **Product:** LimeSDR-USB / LimeSDR Mini (LMS7002M), no RF preselection
    - **Source url:** https://discourse.myriadrf.org/t/gsm-images-over-fm-band-on-lnal/3263
    - **Community:** MyriadRF / Lime discourse
    - **What they built:** LimeSDR on the LNAL path with a 2 m antenna (2018).
    - **Problems:**
      - GSM/LTE images across the FM band.
      - K6MSM: in the USA, '700 MHz LTE images onto the 2 m band', worst close to an LTE tower (1/5 LO-harmonic products).
      - Related thread https://discourse.myriadrf.org/t/fm-images-all-over-hf-and-vhf-bands/7245 (2021): FM images at 25/58/125/155 MHz on a LimeSDR Mini.
    - **Fixes:**
      - External bandpass or lowpass filters (M0GLO: 'you NEED to use external filters'); K6MSM uses cable-TV lowpass filters.
      - Set the RX analog LPF slightly above the sample rate.
      - Reduce gain when spurs fall faster than the gain change (harmonics).
    - **Outcome:** Accepted as inherent: the LMS7002M has no tracking filters, unlike R820T/R828D tuners. Expect the same on the LimeSDR Micro.
  17.
    - **Product:** LimeSDR Mini 2.4 at VHF; on-board RF switch configuration
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-mini-2-4-receiver-gain/8857
    - **Community:** MyriadRF / Lime discourse
    - **What they built:** LimeSDR Mini 2.4 with SatDump/SDR Console, comparing against an RTL-SDR on 162.4 MHz (2025).
    - **Problems:**
      - Signal at -117 dB on the Lime vs -85 dB on the RTL-SDR.
      - Changing LNA gain did nothing.
    - **Fixes:**
      - ricardas: a LimeSuite older than the board revision may not configure the on-board RF switches, so almost nothing is received.
      - G8GKQ: screen the RF cable from the digital section, use a USB2 cable (less noise than USB3), and add a low-noise preamp near the aerial.
    - **Outcome:** Root cause pointed to driver and antenna-switch configuration. The LimeSDR Micro also has software-controlled SP4T switches and depends on a LimeSuiteNG dev branch.
  18.
    - **Product:** LimeSDR Micro M.2 RX matching below 300 MHz
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-micro-m-2-pcie-frequency-range/13348
    - **Community:** MyriadRF / Lime discourse
    - **What they built:** Prospective Micro user (Oct 2026).
    - **Problems:**
      - The docs show both RX paths starting at 300 MHz while the product page says 30 MHz.
    - **Fixes:**
      - Lime (andrewback, 13 Oct 2026): there are no gaps; the bands show only where the matching networks are optimised.
    - **Outcome:** Coverage is confirmed, but no sensitivity data exists for 137/145 MHz on the Micro.
  19.
    - **Product:** Lime boards and LNB/active-antenna power
    - **Source url:** https://discourse.myriadrf.org/t/lime-sdr-how-to-send-voltage-to-lnb/5903
    - **Community:** MyriadRF / Lime discourse
    - **What they built:** QO-100 and GNSS users powering an LNB or active antenna from Lime RX ports.
    - **Problems:**
      - There is no bias voltage on Lime RX ports.
      - The LimeNET Micro QO-100 user (https://discourse.myriadrf.org/t/limenet-micro-clock-setting/13082, 2026) needs a 25 MHz reference for the LNB, but the board only has 30.72 MHz.
      - The XTRX bias-tee option is unpopulated (https://discourse.myriadrf.org/t/bias-tee-option-on-limesdr-xtrx/13105).
    - **Fixes:**
      - G8GKQ: 'You'll need a bias-T'.
      - XTRX: solder the MN53/MN54 inductors.
      - 25 MHz reference: no easy fix (FPGA PLL gateware change or swapping the oscillator).
    - **Outcome:** An external bias-T is mandatory on Lime hardware. The Bullseye TCXO LNB avoids the reference-injection problem.
  20.
    - **Product:** RTL-SDR Blog Broadcast FM bandstop: DC pass and VHF loss
    - **Source url:** https://www.rtl-sdr.com/rtl-sdr-com-broadcast-fm-band-stop-filter-88-108-mhz-reject-now-for-sale/
    - **Community:** RTL-SDR.com article comments
    - **What they built:** Buyers putting the filter between a bias tee and an LNA.
    - **Problems:**
      - DC pass-through was undocumented.
      - The filter cuts 108-118 MHz; insertion loss is <4 dB only from ~120 MHz.
      - Several buyers saw 'little effect' in very strong FM areas.
    - **Fixes:**
      - Admin (May 2019): safe to pass 80 mA, and possibly up to 200 mA.
      - Tom Strum: shield the setup and check in/out direction in strong-FM areas.
    - **Outcome:** Safe for the LNA V2 (<=150 mA). Marginal for the SAWbird+ NOAA (180 mA).
  21.
    - **Product:** GPIO Labs FM filter vs Nooelec Flamingo; Pi noise mitigation
    - **Source url:** https://community.libre.space/t/system-optimization-and-terrestrial-rfi/11939
    - **Community:** SatNOGS community
    - **What they built:** Eggbeater 2 m/70 cm SatNOGS station on an Airspy Mini and Pi (K2PI, 2024).
    - **Problems:**
      - Terrestrial RFI and Pi-generated noise.
    - **Fixes:**
      - GPIO Labs FM filter in front of the preamp: 'a full 10dB more attenuation than the Nooelec Flamingo'.
      - Linear 5 V supply, toroids on the USB lead, grounded lightning arrestors.
      - SA2KNG: metal case for the Pi, common plate, chokes on USB and coax.
    - **Outcome:** The user is pleased with the GPIO filter. Some Pi noise remained.
  22.
    - **Product:** S-band chains: Sysmocom 2170-2300 MHz cavity, Osmocom S-band bandpass, wideband LNAs
    - **Source url:** https://community.libre.space/t/station-4125-s-band/13718
    - **Community:** SatNOGS community
    - **What they built:** S-band stations (2025-2026):
  - NuSpace: helix -> RF AMP 04A LNA -> Sysmocom cavity cf2235-kt30 -> B205mini on a Pi 4.
  - PE0SAT: 5-turn LHCP helix -> Osmocom S-band bandpass -> Nooelec wideband LNA -> 4 m Aircell 7 -> bias-T -> B200mini (https://community.libre.space/t/artemis-ii-mission/14334).
  - EelkeVisser: Mini-Circuits ZX60-242GLN-S+ + Sysmocom cavity.
    - **Problems:**
      - Out-of-band interference at 2.2 GHz (Wi-Fi, LTE).
    - **Fixes:**
      - Put a commercial S-band cavity or bandpass filter (EU source: Sysmocom) before or next to the LNA.
    - **Outcome:** Working S-band receptions, including Artemis II tracking at 2210 MHz.
  23.
    - **Product:** Spacewalker LNA 434 MHz (QPL9547 + triple SAW)
    - **Source url:** https://community.libre.space/t/spacewalker-lna-434-mhz/11431
    - **Community:** SatNOGS community
    - **What they built:** Beta units at SatNOGS stations (PE0SAT station 2173: EggBeater -> Spacewalker -> HydraSDR RFOne).
    - **Problems:**
      - Launch blocked on CE paperwork and manufacturing quotes (Mar 2026).
    - **Fixes:**
      - None. Only via Crowd Supply, or a DIY build from the open schematics.
    - **Outcome:** Beta testers say it 'works perfect', but it was not purchasable as of Mar 2026.
  24.
    - **Product:** SPF5189Z + homemade 436.5 MHz cavity filter
    - **Source url:** https://community.libre.space/t/unwanted-harmonic-radiation-spurious-signal/12220
    - **Community:** SatNOGS community
    - **What they built:** 5-element Yagi -> SPF5189Z (linear PSU) -> cavity filter -> RTL-SDR V4 / HackRF (2024).
    - **Problems:**
      - The cavity is too narrow, so reception at 435 and 438 MHz is poor.
      - A persistent spur sits at 436.75 MHz.
    - **Fixes:**
      - Building an interdigital filter with proper bandwidth.
      - SA2KNG: SMPS, CPU clocks and Ethernet can modulate or create spurs; use small filters and a triplexer to isolate the source.
    - **Outcome:** In progress. Narrow 70 cm filters cut the CubeSat band.
  25.
    - **Product:** RTL-SDR Blog V4L (R828S) and V3/V4 bias-tee failures
    - **Source url:** https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
    - **Community:** RTL-SDR.com article comments
    - **What they built:** V4L buyers (Aug-Sep 2026); a V3 owner with five damaged dongles.
    - **Problems:**
      - The V4L has NO notch filters because the R828S has no open_d pin, so there is no built-in FM/AM notch as on the V4.
      - Anthony9: bias-tee LDOs damaged on five V3 dongles.
      - An AliExpress EU-wide listing block in Aug 2026.
      - The V4 is now EOL; one commenter on https://www.rtl-sdr.com/rtl-sdr-blog-v4-end-of-line/ bought a claimed 'V4' from a third-party AliExpress store and is unsure it is genuine.
    - **Fixes:**
      - Replacement LDO: a Chinese part, pin-compatible with the 4.5 V LP5907.
      - Buy from the official eBay or AliExpress store.
      - The V4L needs the updated RTL-SDR Blog drivers (https://www.rtl-sdr.com/v4l/).
    - **Outcome:** The FM bandstop becomes mandatory on the V4L path. Bias-tee LDOs do fail in the field.
  26.
    - **Product:** RTL-SDR Blog Wideband LNA V2 (QPL9547) - early review
    - **Source url:** https://www.passion-radio.com/sdr-accessory/lna-rtlsdr-764.html
    - **Community:** Reseller reviews (Passion Radio, FR)
    - **What they built:** Discone -> LNA V2 -> SDR (F1MCF, 3 May 2026).
    - **Problems:**
      - Warning: it can saturate the SDR, so gain must be managed.
    - **Fixes:**
      - Lower the SDR gain.
    - **Outcome:** Rated 5/5 ('big advantage: powered by the coax'). Listed at EUR 29.78 ex-VAT, in stock, 15-20 dB gain, 150 mA max. No long-term or measured reports yet.
  27.
    - **Product:** Generic 10 MHz-6 GHz bias tee (Ciglow-type)
    - **Source url:** https://www.desertcart.com.ar/products/145520503
    - **Community:** Amazon reviews mirrored on desertcart. Only the search-engine excerpt was available; the page returned 403.
    - **What they built:** Bias-T injection for LNAs at 137 MHz, 1575 MHz and 1.7 GHz.
    - **Problems:**
      - One reviewer measured -3 dB at 200 MHz, -7 dB at 100 MHz and -15 dB at 30 MHz ('specs wildly optimistic').
      - One of two units was dead on arrival.
    - **Fixes:**
      - Another reviewer reports flawless use at 137 MHz, 1.575 GHz and 1.7 GHz.
      - Sweep each unit with a NanoVNA before use.
    - **Outcome:** Quality varies between units. Acceptable at L-band and 740 MHz; check before using on VHF.
  28.
    - **Product:** LNA4ALL (9A4QV) build and powering notes
    - **Source url:** https://lna4all.blogspot.com/
    - **Community:** Maker blog (LNA4ALL)
    - **What they built:** LNA4ALL powered from the RTL-SDR, AirSpy or HackRF bias tee.
    - **Problems:**
      - A damaged LNA can draw >250 mA.
      - MMICs are ESD-sensitive.
      - Plastic 3D-printed housings build up static.
      - BAV99 input diodes degrade NF and can cause intermod.
    - **Fixes:**
      - Fit a 10 uH inductor at L2 plus a 0-ohm bridge at J3 for 5 V coax power (~60 mA on the RTL-SDR).
      - Use a 100-160 mA resettable fuse instead of the bridge.
      - Add a DC block toward the receiver.
      - Discharge the antenna before connecting.
    - **Outcome:** Stock was listed as 250 pcs in May 2025; ordering is by email at EUR 20-23 + EUR 7 tracked shipping.
  29.
    - **Product:** Radxa Dragon Q6A power header (cross-component, affects LNB/LNA rails)
    - **Source url:** https://forum.radxa.com/t/radxa-q6a-4s1p-powering/31611
    - **Community:** Radxa forum
    - **What they built:** A user asking to power the Q6A from 4S LiPo (12-16.8 V) via the 2-pin header (14-15 Oct 2026).
    - **Problems:**
      - Radxa (strongtz): the 12 V header accepts only 4.5-16 V, so a fully charged 4S pack at 16.8 V exceeds it.
    - **Fixes:**
      - Not given in the thread. Implication: regulate the pack before the Q6A, and use separate regulated rails for the 13/18 V LNB and the 5 V LNAs.
    - **Outcome:** Constrains the power design that also feeds the RF front-end.
- **Common problems:**
  1.
    - **Problem:** Strong FM broadcast (and DVB-T, pagers) overloads unfiltered wideband LNAs, causing images every ~10 MHz, FM breakthrough at 137/145 MHz, and FM harmonics near 1550/1700 MHz.
    - **Affected products:** SPF5189Z boards incl. RTL-SDR Blog Wideband LNA V1, LNA4ALL, Mini-Circuits ZX60-P103LN+, likely the RTL-SDR Blog LNA V2 (unfiltered), any unfiltered front-end on the LimeSDR
    - **Frequency:** common
    - **Known fix:** Where FM is strong (within ~1-2.5 km of a transmitter), put the FM bandstop before the LNA; otherwise after it. Better still, use a filtered LNA (SAW-LNA or LNA-SAW-LNA). Reduce SDR gain after adding an LNA. The GPIO Labs FM filter gives ~10 dB more rejection than the Nooelec Flamingo. At L/S band, use a band-specific bandpass (SAWbird GOES, Sysmocom/Osmocom S-band).
    - **Fix sources:**
      - https://community.libre.space/t/fm-bandstop-not-working/13752
      - https://www.rtl-sdr.com/new-products-in-our-store-wideband-lna-spare-metal-v3-enclosures/
      - https://community.libre.space/t/system-optimization-and-terrestrial-rfi/11939
      - https://sgcderek.github.io/blog/beginner-hrpt-guide.html
  2.
    - **Problem:** The bias tee is not actually on during capture. Causes: the next program re-initialises the dongle, a soapy argument given as 1 instead of true, stock Debian/Ubuntu librtlsdr that does not support the V4/V4L, or a Docker image built with the wrong librtlsdr. The LNA then acts as an attenuator.
    - **Affected products:** RTL-SDR Blog V3/V4/V4L with SatNOGS, SatDump CLI, SDR++, gqrx; any bias-tee-powered LNA (SAWbird, LNA V1/V2)
    - **Frequency:** common
    - **Known fix:** Build the RTL-SDR Blog driver (the V4L needs the new one); purge apt librtlsdr first. Check with SoapySDRUtil --probe="driver=rtlsdr". Use driver=rtlsdr,biastee=true (or rtl=0,bias=1 in gr-osmosdr). Debug with rtl_biast -d 0 -b 1. Confirm with the V4 LED and a voltmeter on the centre pin (~4.5-5 V). rtl_eeprom -b 1 forces the bias on, but only if no DC-shorted antenna is ever connected.
    - **Fix sources:**
      - https://community.libre.space/t/v4-rtl-sdr-bias-tee-issue/14699
      - https://community.libre.space/t/satnogs-3649-rtl-sdr-blog-v4-issues/11942
      - https://github.com/SatDump/SatDump/issues/1030
      - https://community.libre.space/t/rtl-sdr-com-wideband-lna-w-rtl-sdr-com-dongle-bias-t/4601
      - https://www.rtl-sdr.com/v4l/
  3.
    - **Problem:** Counterfeit or remarked SPF5189Z modules: 145-150 mA instead of 70-90 mA, running hot, ~10 dB low gain, NF off spec, dying overnight. Genuine modules can also die from turn-on transients.
    - **Affected products:** AliExpress/eBay/Banggood SPF5189Z '50-4000 MHz' boards
    - **Frequency:** common
    - **Known fix:** Avoid these boards; use QPL9547-based or brand-name filtered LNAs. If used anyway, check the supply current on arrival. Add a soft-start supply, a uF bulk capacitor, a series resistor or L78L05 current limit, and a TVS diode; solder leads directly to the PCB.
    - **Fix sources:**
      - https://www.eevblog.com/forum/rf-microwave/lna-spf5189z-issue/
  4.
    - **Problem:** LNA destroyed by static or ESD from antennas, especially DC-shorted loops and hairpin-matched Yagis, or by handling.
    - **Affected products:** Bare Chinese MMIC preamps, LNA4ALL (on-die Class 1B ESD only); risk higher in plastic or 3D-printed housings
    - **Frequency:** occasional
    - **Known fix:** Discharge the antenna before connecting. Fit anti-parallel BAV99 at the LNA input (costs a little NF and IMD) or use commercial filtered LNAs with protection (Uputronics). Put a 100-160 mA resettable fuse in the bias feed. Prefer metal or shielded enclosures.
    - **Fix sources:**
      - https://community.libre.space/t/qfh-antennas-can-burn-pre-amps/1959
      - https://lna4all.blogspot.com/
  5.
    - **Problem:** An externally powered (micro-USB or header) Nooelec SAWbird puts DC onto its RF output and into the SDR, which can trip the SDR's ESD diode or damage the input.
    - **Affected products:** Nooelec SAWbird / SAWbird+ (NOAA, GOES); relevant to LimeSDR Micro MHF4 RX ports (max +10 dBm, no DC rating published)
    - **Frequency:** occasional
    - **Known fix:** Add a DC block (series capacitor or inline DC-block) between the SAWbird and the SDR whenever it is not powered over the coax from the SDR. Alternatively, power it through a bias-T injector whose RF port faces the SDR.
    - **Fix sources:**
      - https://sgcderek.github.io/blog/beginner-hrpt-guide.html
      - https://www.nooelec.com/store/sawbird-plus-goes.html
  6.
    - **Problem:** Lime LMS7002M receivers have no preselection or tracking filters. FM and LTE appear as images and LO-harmonic products; for example, 700 MHz LTE lands on 2 m and FM images spread across HF and VHF.
    - **Affected products:** LimeSDR-USB, LimeSDR Mini 1/2; by architecture expected on the LimeSDR Micro
    - **Frequency:** common
    - **Known fix:** Fit a band-specific filter on every Lime RX port (SAW or cavity per band; LPF or HPF where useful). Set the RX analog LPF just above the sample rate and lower the gain. Keep VHF on the RTL-SDR, which has tracking filters.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/gsm-images-over-fm-band-on-lnal/3263
      - https://discourse.myriadrf.org/t/fm-images-all-over-hf-and-vhf-bands/7245
  7.
    - **Problem:** The Lime board's on-board RF switches are not configured by an older driver, giving near-zero signal (-117 dB vs -85 dB on an RTL-SDR); USB3 cabling adds noise.
    - **Affected products:** LimeSDR Mini 2.x; analogous risk for the LimeSDR Micro (SP4T switches, dev-branch LimeSuiteNG)
    - **Frequency:** occasional
    - **Known fix:** Use a LimeSuite/LimeSuiteNG version that knows the board revision and select the antenna port explicitly. Screen the RF cable from the digital section. Put a preamp at the aerial.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/limesdr-mini-2-4-receiver-gain/8857
  8.
    - **Problem:** Filters that are too narrow or off-centre for 435-438 MHz: a homemade 436.5 MHz cavity, or 433.92 MHz ISM SAW parts.
    - **Affected products:** DIY cavity filters, generic ISM SAW filters
    - **Frequency:** occasional
    - **Known fix:** Use an interdigital filter or a SAW LNA with about 20 MHz -3 dB bandwidth centred near 435 MHz, such as the vhfdesign 70 cm SAW LNAs or HA8ET filtered LNAs. The Spacewalker 434 is not yet sold.
    - **Fix sources:**
      - https://community.libre.space/t/unwanted-harmonic-radiation-spurious-signal/12220
      - https://community.libre.space/t/rx-only-filtered-lnas-for-vhf-and-uhf-where-to-find/6897
  9.
    - **Problem:** VHF land-mobile or pager transmitters (~150-170 MHz) mixing with FM into 2 m and 137 MHz, raising the noise floor even after an FM trap.
    - **Affected products:** Any wideband or 2 m LNA (LNA4ALL documented); the SAWbird+ NOAA's 5 MHz SAW would help at 137 MHz
    - **Frequency:** occasional
    - **Known fix:** An FM trap removes the FM half of the intermod. For pagers use a narrow 137 MHz or 2 m bandpass or SAW filter ahead of the gain (e.g. Uputronics 137, SAWbird NOAA, HobbyPCB 144 MHz BPF at ~1.4 dB loss at 137 MHz).
    - **Fix sources:**
      - https://community.libre.space/t/2m-lna4all-imd-with-moxon-antenna/3946
      - https://community.libre.space/t/tested-and-recommended-lnas/3585
  10.
    - **Problem:** Too much LNA gain saturates the SDR. With short coax an unfiltered LNA gives little or no benefit over raising the SDR gain.
    - **Affected products:** RTL-SDR Blog LNA V2, SPF5189Z, SAWbird+ (30 dB) into RTL-SDR
    - **Frequency:** common
    - **Known fix:** Reduce SDR gain (PE0SAT uses 36.4 on the V4 with an LNA). Prefer filtered, lower-gain LNAs on short runs; Derek recommends the 20 dB SAWbird GOES (non-plus) for HRPT with short coax.
    - **Fix sources:**
      - https://www.passion-radio.com/sdr-accessory/lna-rtlsdr-764.html
      - https://community.libre.space/t/rx-only-filtered-lnas-for-vhf-and-uhf-where-to-find/6897
      - https://sgcderek.github.io/blog/beginner-hrpt-guide.html
  11.
    - **Problem:** Host computer, PSU and SMPS noise entering the front-end. Seen with Raspberry Pi based stations; expected from the Q6A plus buck converters inside a handheld case.
    - **Affected products:** All chains, especially an indoor or close-in antenna next to the SBC
    - **Frequency:** common
    - **Known fix:** Metal case for the SBC, a common ground plate, ferrite chokes on USB and coax, linear or well-filtered supplies, LNA at the antenna, and distance between the antenna and the computer.
    - **Fix sources:**
      - https://community.libre.space/t/system-optimization-and-terrestrial-rfi/11939
      - https://community.libre.space/t/unwanted-harmonic-radiation-spurious-signal/12220
  12.
    - **Problem:** Cheap generic bias tees with large low-frequency loss (-3 dB at 200 MHz, -7 dB at 100 MHz) and dead-on-arrival units.
    - **Affected products:** Generic '10 MHz-6 GHz' bias tees (AliExpress/Amazon)
    - **Frequency:** occasional
    - **Known fix:** Use them only on the 740 MHz LNB IF and at 1.7/2.2 GHz; sweep each unit with a NanoVNA first. For VHF use the RTL-SDR's internal bias tee, or a characterised injector (GPIO Labs: 0.2 dB at 100 MHz, but 15 V max).
    - **Fix sources:**
      - https://www.desertcart.com.ar/products/145520503
      - https://www.tindie.com/products/gpio/bias-tee-operates-from-10mhz-to-7000mhz/
  13.
    - **Problem:** Bias-tee hardware failures in the field: V3 bias-tee LDO deaths, and a V4 bias LED lit while the bias tee was suspected dead.
    - **Affected products:** RTL-SDR Blog V3, V4
    - **Frequency:** occasional
    - **Known fix:** Do not enable the bias tee into DC-shorted antennas. Keep the load well under 180 mA. A failed V3 LDO can be replaced with a 4.5 V LP5907-compatible part.
    - **Fix sources:**
      - https://github.com/rtlsdrblog/rtl-sdr-blog/issues/39
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
- **Unresolved problems:**
  1.
    - **Problem:** No community field or long-term reports, and no published gain curve, P1dB or OIP3, for the board-level RTL-SDR Blog Wideband LNA V2 (QPL9547).
    - **Why it matters for us:** It is the planned workhorse for 145.8, 435 and 2.2 GHz. Its overload behaviour near Ukrainian FM, DVB-T and LTE sites is unknown. Its unfiltered predecessor (V1) failed at a strong-FM SatNOGS site. The only user note warns about SDR saturation.
    - **Evidence:** The V2 product image dates from Sept 2026; the product page has no specs or comments; one Passion Radio review (F1MCF, May 2026). V1 overload: https://community.libre.space/t/fm-bandstop-not-working/13752
  2.
    - **Problem:** No measured performance of the LimeSDR Micro below 300 MHz, no bias tee, and no community reports of any external front-end (LNA, SAW, DC injection) with the Micro. It ships Dec 2026.
    - **Why it matters for us:** It decides whether 435 MHz or VHF can go on the Lime, how much LNA gain the Lime needs, and whether DC from a USB-powered SAWbird into a bare MHF4 port is tolerated. Earlier Lime boards show the receive path can be damaged by overload (LNA_W path damage: https://discourse.myriadrf.org/t/limesdr-mini-test-lnaw-fail/4163).
    - **Evidence:** https://discourse.myriadrf.org/t/limesdr-micro-m-2-pcie-frequency-range/13348 ; Micro reference docs (rfcontrol, changelog) mention no bias option.
  3.
    - **Problem:** No community measurement of SAWbird GOES or GOES+ rejection at LTE Band 3 (uplink 1710-1785 MHz, partly inside the stated 1650-1720 or 80 MHz passband; downlink 1805-1880 MHz). No report of HRPT reception next to LTE 1800 sites.
    - **Why it matters for us:** LTE 1800 is dense in Ukraine. A handheld helix without a dish has much less gain margin than the dish setups most HRPT reports use, so LTE desense or intermod may decide success. FM harmonics near 1700 MHz were also reported at strong-FM sites.
    - **Evidence:** The Nooelec page gives no dB figures. FM harmonics at 1550/1700 MHz: https://community.libre.space/t/fm-bandstop-not-working/13752. The triple-SAW homebrew claim was seen only in a Reddit search snippet; Reddit was unreachable.
  4.
    - **Problem:** No successful no-dish (helix-only) Meteor or Metop HRPT report that documents the front-end. The only hand-tracked helix-type success (Saveitforparts helicone, NOAA HRPT) does not name the LNA or filter.
    - **Why it matters for us:** The user has abandoned dishes. Whether an 11-turn helix plus a SAWbird at the feed closes the link for Meteor-M HRPT is unproven in the communities reached.
    - **Evidence:** https://www.rtl-sdr.com/saveitforparts-testing-a-3d-printable-satellite-antenna-for-noaa-meteor-and-other-polar-orbiting-l-band-satellites/ (0 comments); the Thingiverse/3dgo page returned 403.
  5.
    - **Problem:** Still unpublished: the Bullseye LNB current draw, whether cheap satellite-TV power inserters (often rated 950-2150 MHz) pass the 739.5 MHz QO-100 IF without loss, and the 13/18 V switching threshold when fed from a 4S pack (12-16.8 V).
    - **Why it matters for us:** Sizes the 13/18 V regulator and the injector choice. An unregulated 16.8 V can flip the LNB to horizontal polarization, which is unintended. Radxa also confirms the Q6A header tolerates only 4.5-16 V, so every rail must be regulated.
    - **Evidence:** No data on rtl-sdr.com Bullseye pages/comments. BATC forum blocked by a browser check; the BATC wiki only lists a G0MJW current-limited LNB supply (CQ-TV). Q6A limit: https://forum.radxa.com/t/radxa-q6a-4s1p-powering/31611
  6.
    - **Problem:** No community measurements of AliExpress HMC241 SP4T switch boards: real chip vs clone, logic level, isolation, DC-block caps.
    - **Why it matters for us:** It would be the GPIO-controlled antenna and SDR router. The datasheet requires DC blocks, so bias for LNAs cannot pass through it, and a clone with poor isolation would leak strong signals between ports.
    - **Evidence:** Search returned only datasheets and distributor pages.
  7.
    - **Problem:** Unknown whether the RTL-SDR Blog FM bandstop passes 180 mA continuously (admin: 'safe 80 mA, possibly up to 200 mA'), and whether the V4/V4L bias tee runs a 180 mA SAWbird+ at its full 180 mA rating reliably inside a warm, closed case.
    - **Why it matters for us:** It decides whether the SAWbird+ NOAA can be fed through the FM filter from the dongle, or needs separate 5 V power, which then needs a DC block.
    - **Evidence:** https://www.rtl-sdr.com/rtl-sdr-com-broadcast-fm-band-stop-filter-88-108-mhz-reject-now-for-sale/ ; V3 bias-tee LDO failures: https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
  8.
    - **Problem:** No data on the Dragon Q6A's per-port USB 2.0 current limit or protection behaviour, nor on RF noise from Q6A peripherals (fan PWM, Wi-Fi/BT USB chip) at 137 MHz-2.2 GHz.
    - **Why it matters for us:** The V4/V4L (~250-270 mA) plus a bias-tee LNA (up to 150-180 mA) approaches 500 mA on one port; a brown-out or over-current trip would kill captures. The Q6A's Wi-Fi is a USB AIC8800 chip on the same bus family.
    - **Evidence:** Radxa forum searches ('q6a usb current', 'overcurrent', 'noise') returned no relevant threads; Wi-Fi chip mention: https://forum.radxa.com/t/wi-fi-bt-support-for-windows-on-q6a/31091
  9.
    - **Problem:** No user reports yet of the RTL-SDR Blog V4L with LNAs or filters. The V4L drops the V4's built-in notch filters.
    - **Why it matters for us:** The V4 is end-of-life, so the VHF path will likely be a V4L. Without a notch, the external FM bandstop and the SAW selectivity carry all the FM rejection at 137/145 MHz.
    - **Evidence:** https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
  10.
    - **Problem:** Price, stock and Ukraine shipping not verified for the EU filtered 70 cm/2 m LNA sources found in the community (HA8ET, vhfdesign, TGN, Sysmocom S-band cavity). The Spacewalker 434 is still blocked on CE paperwork.
    - **Why it matters for us:** These replace the missing purchasable 435-438 MHz filtered LNA and the 2.2 GHz bandpass gap from the initial research. EU shipping is the realistic route into Ukraine, given AliExpress regional blocks (Aug 2026).
    - **Evidence:** https://community.libre.space/t/rx-only-filtered-lnas-for-vhf-and-uhf-where-to-find/6897 ; https://community.libre.space/t/station-4125-s-band/13718 ; https://community.libre.space/t/spacewalker-lna-434-mhz/11431
- **Communities checked:**
  - SatNOGS community (community.libre.space): reachable via the Discourse JSON API; about 25 topics read
  - MyriadRF / Lime discourse (discourse.myriadrf.org): reachable; about 10 topics read
  - Radxa forum (forum.radxa.com): reachable; searched rtl-sdr/SDR/Q6A USB power/noise; Q6A 4S power thread read
  - RTL-SDR.com article and product comments (wpDiscuz): LNA V1, FM bandstop (2 articles), V4L launch, V4 EOL, Bullseye LNB (3 articles), HRPT articles; the LNA V2 product page has no visible comments
  - GitHub issues via web pages (the REST/GraphQL API was blocked in this session): rtlsdrblog/rtl-sdr-blog (#39, #55, #70), SatDump (#1030; LNA and HRPT searches), SDR++ (#361, #1785), LimeSuiteNG ('micro' search)
  - EEVblog forum (rf-microwave): SPF5189Z thread
  - Qorvo forum: QPL9547 thread
  - Crowd Supply LimeSDR Micro updates page (the FAQ URL returned 404)
  - Maker and builder sites: LNA4ALL blog, sgcderek (OK9SGC) HRPT guide, Nooelec SAWbird+ GOES product page, Passion Radio LNA V2 listing with reviews
  - BATC: the forum is UNREACHABLE (JavaScript browser-verification wall); the BATC wiki search worked
  - AMSAT-DL forum: the front page loads, but WoltLab search is not usable without a session; site: web search found nothing
  - Reddit (www, old, and the Redlib mirrors nyc1.lr.ggtyler.dev and r.datuan.dev): UNREACHABLE (network-policy block, 503, 502). Only search-engine snippets were seen, and they are not used as experiences.
  - Thingiverse mirror 3dgo.app and desertcart (Amazon review mirror): 403. Only the desertcart search snippet is cited, with a caveat.
  - Ukrainian-language web search on SPF5189Z fakes and local purchase: no Ukrainian community results
  - Not reached for budget reasons: groups.io, AMSAT-BB archives, mikrocontroller.net, StackExchange, CNX Software comments, YouTube comments
- **Recommendation impact:** The community evidence supports the per-band filtered chain and confirms dropping the SPF5189Z. It also forces several changes.
  
  1. **DC blocking on the Lime side.** A SAWbird powered from micro-USB or its header leaks DC onto its RF output (OK9SGC; Nooelec also says to add a DC block). On the Lime side, either feed every SAWbird and LNA V2 through a proper bias-T injector, with its DC-blocked RF port facing the Lime, or add an inline DC block before every Lime MHF4 port. Never wire a USB-powered SAWbird straight into the Lime.
  
  2. **HRPT LNA choice.** For HRPT with a short feed at the helix, the community expert prefers the non-plus SAWbird GOES (20 dB, 30 mA). That makes the RTL-SDR bias-tee current problem disappear. Keep the GOES+ only if the Lime's L-band noise figure proves poor. LTE 1800 rejection and helix-only HRPT remain unproven, so plan a fallback: a second SAW stage or cavity after the LNA.
  
  3. **VHF path.**
     - The V4 is end-of-life and the V4L has no built-in notch, so the FM bandstop is mandatory.
     - At Ukrainian urban sites put it before any unfiltered LNA.
     - The RTL-SDR Blog bandstop is confirmed to pass at least 80 mA (admin says possibly 200 mA). That is fine for the LNA V2 at up to 150 mA, but marginal for the 180 mA SAWbird+ NOAA.
     - A stronger alternative is the GPIO Labs FM filter, about 10 dB better than the Flamingo per SatNOGS.
     - For 137 MHz with pagers or land-mobile nearby, keep the SAWbird+ NOAA (or Uputronics 137) as the selective first stage. It excludes 145.8 MHz, so ISS needs its own path: FM bandstop, then the LNA V2 or no LNA, since ISS is strong.
  
  4. **Software setup on Ubuntu 24.04.** Purge the stock librtlsdr and build the RTL-SDR Blog driver (required for the V4L). Use biastee=true in Soapy strings, and verify bias with the LED or a meter. Do not use rtl_eeprom -b 1, because the WB2HOL hairpin Yagi is a DC short. Toggle the bias tee per band in software instead.
  
  5. **70 cm band.** The Spacewalker is still not for sale. The community-proven, purchasable EU options are vhfdesign SAW LNAs (about 20 MHz bandwidth) and HA8ET filtered LNAs, or the LNA V2 followed by a wide interdigital filter. Avoid narrow 433.92 MHz SAW parts and narrow cavities.
  
  6. **2.2 GHz band.** This fills the earlier gap: the Sysmocom S-band cavity filter (2170-2300 MHz, cf2235-kt30, EU supplier) or the Osmocom S-band bandpass, both in proven SatNOGS chains with helix antennas.
  
  7. **Lime preselection.** Lime boards have no preselection and show FM/LTE images. Every Lime port needs a band filter, not just an LNA. Keep VHF on the RTL-SDR.
  
  8. **Protection.**
     - Fit BAV99 diodes or use commercially protected filtered LNAs.
     - Put a 100-160 mA polyfuse in each bias feed.
     - Discharge antennas before connecting.
     - Mount bare boards in metal shields rather than directly in the 3D-printed plastic case.
     - Add ferrites on USB and coax, and keep LNAs at the antennas away from the Q6A and the buck converters.
  
  9. **Cheap bias tees.** Use them only at 740 MHz and above, after a NanoVNA sweep; they lose 3-7 dB at 100-200 MHz.
  
  10. **LNB supply.** Make it a regulated 13.0/18 V rail with a current limit (the BATC/G0MJW design approach). Separately, Radxa confirms the Q6A power header tolerates only 16 V, so the 4S pack (16.8 V) must be regulated for both the computer and the RF rails.
  
  The revised core BOM keeps costs similar (about $175-210 before VAT and shipping). It adds about $5-15 for DC blocks, polyfuses and BAV99 diodes and about $30-60 for an S-band cavity. It may swap the GOES+ for the cheaper non-plus GOES. Buy from EU resellers, because AliExpress had EU-wide listing blocks in Aug 2026.

## Власні виправлення (`fixes`)

_Run `wf_30889068-251`_

- **Component:** RF front-end (LNAs, filters, bias tees, LNB power, antenna sharing, protection)
- **Fixes:**
  1.
    - **Problem:** RTL-SDR Blog Wideband LNA V2 (QPL9547) has no published board-level gain curve, P1dB or OIP3, and no field reports. Its unfiltered predecessor overloaded an RTL-SDR at a strong-FM SatNOGS site.
    - **Proposed fix:** Treat the V2 as a linear gain block and measure it once. Chip data: OP1dB about +22 dBm (distributor 22.7 dBm), P3dB about 1 dB higher (Qorvo forum), OIP3 +39 dBm and 19.5 dB gain at 1.9 GHz. So the LNA is rarely the part that overloads; the SDR behind it is.
  
  Fixes:
  - Put the LNA at the antenna and a band filter at the SDR end. The filter must pass DC, because the LNA is powered back through the coax.
  - Set the SDR gain by measurement instead of by habit.
  - Drop the LNA altogether on 145.8 MHz ISS SSTV, which is a strong signal.
  - If the pad test shows intermodulation, add a 3-6 dB SMA attenuator at the SDR input. After about 20 dB of LNA gain this costs very little noise figure.
  - At sites with strong FM (under ~2 km from a transmitter), move the FM bandstop in front of the LNA. Read from the datasheet plot, the Flamingo+ loses about 0.3 dB at 145 MHz and about 1 dB at 137 MHz. At VHF, sky and man-made noise dominate, so that loss is negligible.
    - **Steps:**
      - Measure the unit on the bench. Read the supply current with a multimeter in series with the bias line, or a USB power meter on the dongle with bias on and off.
  Then measure S21 at 145.8, 435, 740, 1700 and 2250 MHz. Use a LiteVNA 64 (50 kHz-6.3 GHz, EUR 144.59 ex-VAT at eleshop.eu; also listed by the Ukrainian shop selteq.com.ua, price not checked) or a NanoVNA-H (up to 1.5 GHz). Put a 20 dB pad on the LNA input. Keep the gain table.
      - Survey each site with the antenna connected straight to the RTL-SDR (no LNA) at 0 dB gain:
    rtl_power -f 24M:1760M:200k -g 0 -i 10 -e 5m site.csv
    heatmap.py site.csv site.png
  List the FM (87.5-108), DVB-T2 (470-790), GSM/LTE 900, LTE 1800 and 2100 peaks.
      - Chain for 145.8 MHz: Yagi -> LNA V2 at the feed -> coax -> Flamingo+ FM (passes DC) -> RTL-SDR, with the RTL bias tee switched on.
  Chain for 435 MHz: Yagi -> LNA V2 -> coax -> 10 MHz-6 GHz bias tee (RF+DC port toward the LNA) -> 70 cm filter (see fix 10) -> SDR. A SAW or cavity filter does not pass DC, so inject the LNA power on the antenna side of it.
      - Set the gain. With the antenna connected, raise SDR gain until the noise floor in an empty part of the band sits 6-10 dB above the floor measured with the SDR input terminated in 50 Ohm. Stop there, and keep every carrier below about -10 dBFS.
      - Run the pad test, which is the decisive overload check. Insert a 3 dB SMA pad in front of the SDR.
  - Real signals and the noise floor drop by about 3 dB.
  - Spurs that drop by 6-9 dB are intermodulation products made inside the receiver. Lower the gain, keep the pad, or add a filter.
      - If spurs remain at a strong-FM site, move the FM filter in front of the LNA and repeat the pad test.
    - **How to verify:** Pass criteria:
  - The 3 dB pad test shows no spurs that drop by more than 3 dB in 136-146 MHz and 430-440 MHz.
  - On a CubeSat or ISS pass through at least 5 m of coax, SatDump or SDR++ SNR with the LNA is equal to or better than without it.
  - The measured gain table is the reference for every later gain-staging decision.
    - **Confidence:** medium
    - **Sources:**
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
      - https://www.qorvo.com/products/p/QPL9547
      - https://forum.qorvo.com/t/qpl9547-saturated-output-power/22133
      - https://www.rfmw.com/ProductDetail/QPL9547-Qorvo/675339
      - https://community.libre.space/t/fm-bandstop-not-working/13752
      - https://www.nooelec.com/store/downloads/dl/file/id/96/product/320/flamingo_fm_filter_datasheet_revision_1.pdf
      - https://eleshop.eu/litevna.html
      - https://selteq.com.ua/en/litevna-64/
  2.
    - **Problem:** LimeSDR Micro M.2 (ships Dec 2026): no bias tee, unknown DC tolerance of the bare MHF4 RX ports, no measured performance below 300 MHz, and earlier Lime boards were damaged by overload.
    - **Proposed fix:** Assume the RX ports must never see DC.
  
  The RX switches are SKY13414-485LF (Lime rfcontrol page). Skyworks' wording for this switch family is "No external blocking capacitors are required on the RF paths unless VDC is externally applied". The Micro's schematic is not public, so whether DC blocks are fitted is unknown.
  
  Feed every powered device through a bias tee whose RF-only port faces the Lime. That one part both powers the LNA and blocks DC from the Lime. Power the bias tees from a GPIO-switched, current-limited 5 V switch: TI TPS2553 (2.5-6.5 V input, 75-1700 mA adjustable limit, active-high EN, FAULT output, SOT-23-6).
  
  Add overload protection, because both LNAs can push the Lime past its +10 dBm maximum safe input:
  - SAWbird+ GOES: OP1dB +20 dBm, 38 dB gain.
  - QPL9547: OP1dB about +22 dBm.
  - Example: a 5 W 70 cm handheld 5 m away puts about -2 dBm into the LNA (free-space loss 39 dB), which drives the LNA into saturation.
  - Protection: a Mini-Circuits VLM-33-S+ limiter (30-3000 MHz, 0.23 dB typical loss, ~+11.5 dBm typical output when limiting, 2 W maximum input) plus a 3 dB pad. On L-band, a 6 dB pad after the SAWbird alone is enough.
  
  Keep 137 and 145.8 MHz on the RTL-SDR until the A/B test below. Lime staff said on 13 Oct 2026 that 0.3 and 0.7 GHz are the edges of the matching-optimised ranges and that "there are no gaps in frequency coverage".
    - **Steps:**
      - With the Lime unpowered, measure DC resistance from the centre pin of each RX port to ground through the MHF4-SMA pigtail, and record it.
  - Open circuit: a switch port or series capacitor.
  - About 0 Ohm: a balun or inductor to ground.
  Either way, never apply DC to the port.
      - Build one bias module per Lime RX port:
    5 V rail -> TPS2553 (limit about 250 mA, set R_ILIM with TI's calculator) -> 10 uH + 10 uF filter -> DC port of a 10 MHz-6 GHz SMA bias tee.
  - EN goes to a Q6A 40-pin header GPIO (3.3 V logic).
  - FAULT goes to a GPIO input.
  - The bias tee's RF port goes to the Lime through a MHF4L-SMA pigtail.
      - Power the LNA and confirm with a multimeter that the SMA on the Lime side reads 0 V DC while the LNA side reads about 5 V.
      - Fit the VLM-33-S+ plus a 3 dB pad on the UHF chain, and a 6 dB pad after the SAWbird+ GOES on the L-band chain. This is mandatory at hamfests, near repeaters, or on rooftops with other transmitters.
      - A/B test below 300 MHz: antenna -> LNA (at least 20 dB gain) -> 2-way splitter -> RTL-SDR and Lime LNAL. Record the same Meteor LRPT pass at 137.9 MHz and the same ISS pass at 145.8 MHz on both radios. Compare SatDump SNR and noise floor. Repeat on a 435 MHz CubeSat.
      - In software, use the LNAL path (0.3-2.2 GHz) for 435 MHz and the 739.5 MHz QO-100 IF, and LNAW (0.7-2.6 GHz) for 1.7 and 2.2 GHz. Under the limesdr-micro LimeSuiteNG branch, confirm the device key and antenna names with:
    SoapySDRUtil --find
    SoapySDRUtil --probe
    - **How to verify:** Pass criteria:
  - 0 V DC on every Lime RX port with all LNAs powered.
  - The TPS2553 FAULT line stays high in normal use and asserts when the coax is deliberately shorted.
  - In the A/B test, Lime SNR at 137/145 MHz is within 1-2 dB of the RTL-SDR. If it is not, VHF stays on the RTL-SDR permanently.
  - The pad test on the Lime shows no intermodulation.
    - **Confidence:** medium
    - **Sources:**
      - https://discourse.myriadrf.org/t/limesdr-micro-m-2-pcie-frequency-range/13348
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/rfcontrol.html
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/overview.html
      - https://atta.szlcsc.com/upload/public/pdf/source/20180126/C150901_15169562034341309383.pdf
      - https://www.ti.com/product/TPS2553
      - https://www.minicircuits.com/pdfs/VLM-33-S+.pdf
      - https://www.nooelec.com/store/sawbird-plus-goes.html
  3.
    - **Problem:** Unknown rejection of LTE Band 3 (uplink 1710-1785 MHz, downlink 1805-1880 MHz) by the SAWbird(+) GOES, which matters for HRPT next to dense Ukrainian LTE 1800.
    - **Proposed fix:** Nooelec's own datasheet (Rev 1, 2022-06-24) answers most of this. The gain plot below is read by eye, about +/-3 dB.
  
  SAWbird+ GOES specs: LNA -> SAW -> LNA, 38 dB gain at 1694 MHz, 70 MHz 3 dB bandwidth, 80 MHz 10 dB bandwidth, NF 1.2 dB (Tn 100-120 K), 140 mA, OP1dB +20 dBm, maximum input 0 dBm.
  
  Gain read from the plot:
  - About 37 dB from 1650 to 1720 MHz.
  - 28 dB at 1730 MHz, 18 dB at 1740, 10 dB at 1750, 0 dB at 1760, -10 dB at 1780-1795.
  - About -5 dB flat from 1.8 to 2.6 GHz.
  
  What that means for LTE:
  - LTE 1800 downlink and 2100 are about 42-45 dB below the HRPT gain, so they reach the SDR about 5 dB weaker than at the antenna. A typical -25 to -35 dBm near a mast is harmless at moderate SDR gain.
  - The real threat is LTE Band 3 uplink from nearby phones. 1710-1730 MHz gets full gain and cannot be filtered: it is only 2 MHz above the FY-3 band edge.
  - Worked example: a phone at +23 dBm 3 m away gives about -24 dBm at the antenna and about +14 dBm out of the SAWbird+, which is above the Lime's +10 dBm maximum. Hence the 6 dB pad.
  
  Fixes:
  1. A 6 dB pad after the SAWbird. With 38 dB in front of it, the noise figure cost is under 0.1 K.
  2. Low SDR gain.
  3. Pick sites and passes away from crowds and masts.
  4. Only if the survey shows a problem, a second filter after the SAWbird, where its loss costs nothing:
     - DIY interdigital or combline filter, 3-4 resonators, passband about 1695-1712 MHz.
     - Or a commercial cavity: Anatech AB1690B865 (1674-1706 MHz, insertion loss <2.5 dB, >45 dB at 1730-2150 MHz). It is 164x84x57 mm, the price is unlisted, and its 1706 MHz upper edge clips FY-3 at 1704.5 MHz, so ask for a custom 1690-1712 MHz version.
    - **Steps:**
      - Phase 1 can run before the Lime arrives, because the RTL-SDR V4/V4L reaches 1.766 GHz. Chain: helix -> SAWbird+ GOES at the feed (140 mA from the dongle's 4.5 V / 180 mA bias tee) -> RTL-SDR at about 20 dB gain.
  Point the helix at the horizon toward the nearest mast, then at zenith:
    rtl_power -f 1650M:1766M:100k -g 20 -i 5 -e 10m lte.csv
  Later, repeat to 1.9 GHz with the Lime (soapy_power; check the flags with --help).
      - Record 2 s of IQ with the Lime at the planned rate (6-10 Msps) and gain. Check that the peak |IQ| stays below 0.5 of full scale (-6 dBFS) with a short numpy script. Repeat with people using phones nearby.
      - Pad test: add 3 dB between the SAWbird and the SDR, and check that nothing in 1695-1712 MHz drops by more than 3 dB.
      - If the downlink or uplink residue clips the ADC at the gain you need, build or buy the second filter. Tune it with a LiteVNA to: insertion loss under 2 dB at 1698-1710 MHz, at least 30 dB at 1750 MHz, and at least 40 dB at 1805 MHz.
      - Treat 1710-1730 MHz uplink interference as something filtering cannot fix. Record raw IQ and note phone activity. Prefer Meteor (1700 MHz), which is furthest from the LTE edge.
    - **How to verify:** Pass criteria:
  - A spectrum survey and IQ peak test showing more than 6 dB of headroom.
  - The pad test is clean.
  - An HRPT pass decoded in SatDump at a site within about 500 m of an LTE 1800 mast. Compare SNR with and without the extra filter.
    - **Confidence:** medium
    - **Sources:**
      - https://www.nooelec.com/store/downloads/dl/file/id/108/product/296/sawbird_goes_datasheet_revision_1.pdf
      - https://www.nooelec.com/store/sawbird-plus-goes.html
      - https://anatechelectronics.com/1690-mhz-cavity-band-pass-filter.html
      - https://itu.int/dms_pub/itu-r/opb/rep/R-REP-SA.2329-2014-PDF-E.pdf
      - https://community.libre.space/t/fm-bandstop-not-working/13752
  4.
    - **Problem:** No documented no-dish (helix-only) Meteor or Metop HRPT success that names its front end, so the 11-turn helix plus SAWbird HRPT link is unproven.
    - **Proposed fix:** Treat this as a link to engineer and verify, not to hope for.
  
  Nearest evidence:
  - A hand-tracked 1.7 GHz helical feed in a 3D-printed cone, with a Nooelec GOES preamp and an RTL-SDR, gave "nice Meteor images" (libre.space).
  - An 11-turn RHCP helix with no dish decoded Elektro-L3 LRIT at 1.5 dB SNR, against 5-6 dB on a 70 cm dish.
  - saveitforparts got NOAA HRPT hand-tracked with an RTL-SDR and SatDump.
  
  Gain comparison:
  - A realistic 11-turn helix gives about 13-15 dBic. The Kraus formula says 16 dBi but overestimates.
  - A 60 cm dish gives about 18.0 dBi and a 90 cm dish about 21.5 dBi (55% efficiency), so the helix is 3-8 dB short of typical HRPT dish setups.
  - The helix's half-power beamwidth is about 31 degrees, so hand pointing with the BNO085 is easy.
  
  Recover the margin with:
  - The LNA right at the feed, with no coax before it.
  - High passes. Slant range for an 820 km orbit is about 820 km at zenith, 1430 km at 30 degrees elevation and 2800 km at 5 degrees. Path loss at 1.7 GHz is 155.3, 160.3 and 166.4 dB. That is up to about 11 dB, partly offset by the satellites' shaped antennas.
  - Meteor HRPT first (665.4 kbps, about 3 MHz wide, works on an RTL-SDR at 2.4 Msps).
  - Then Metop (4.5 MHz) and FY-3 on the Lime.
  - Optionally a cone reflector, the 'helicone' design.
    - **Steps:**
      - Screw the SAWbird+ GOES straight onto the helix SMA with a right-angle adapter. Add a weather cover. Use one short cable, 1-2 m of low-loss coax, to the SDR.
      - Y-factor check of the antenna and LNA. Measure power in about 1 MHz of empty spectrum near 1690 MHz, first with the helix at clear zenith sky and then pointed at the ground.
  Expect Y of about 3.5-4.5 dB: roughly 290 K + 110 K against 40 K + 110 K, using Tn 100-120 K from the datasheet.
  If Y is under 2 dB, look for coax before the LNA, a bad match, or interference.
      - Sun-noise check: point at the Sun and expect about 0.5-1 dB rise. The calculation: Ae is about 0.06 m^2 at 14 dBic, and about 100 sfu gives a ~22 K rise against a system temperature of ~150 K.
  Use the Sun peak to calibrate the BNO085 azimuth and elevation offsets, which also removes magnetic declination and mounting error.
      - Record raw IQ on every pass: RTL at 2.4 Msps for Meteor, Lime at 6-8 Msps for Metop and FY-3. Decode offline in SatDump with the Meteor HRPT, Metop AHRPT and FY-3 pipelines.
      - Start with passes above 40 degrees maximum elevation. Log SNR against elevation and keep pointing within +/-10 degrees.
      - If SNR at 30 degrees is still marginal, add a cone or wider ground-plane reflector, or a longer helix (15-20 turns), or hand the problem to the antenna component.
    - **How to verify:** Pass criteria:
  - Y-factor of at least 3 dB.
  - A repeatable Sun-noise peak.
  - A Meteor HRPT pass decoded in SatDump with most scan lines valid on a pass above 40 degrees.
  - The SNR-versus-elevation log shows the minimum usable elevation.
    - **Confidence:** medium
    - **Sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://www.rtl-sdr.com/receiving-elektro-l3-lrit-weather-satellite-images-with-an-11-turn-helix-antenna-and-no-dish/
      - https://www.rtl-sdr.com/saveitforparts-testing-a-3d-printable-satellite-antenna-for-noaa-meteor-and-other-polar-orbiting-l-band-satellites/
      - https://www.nooelec.com/store/downloads/dl/file/id/108/product/296/sawbird_goes_datasheet_revision_1.pdf
      - https://sigidwiki.com/wiki/METEOR-M_High_Resolution_Picture_Transmission_(HRPT)
  5.
    - **Problem:** Bullseye LNB current draw is unpublished. Cheap TV power inserters (rated 950-2150 MHz) may not pass the 739.5 MHz QO-100 IF. A raw 4S pack (12.0-16.8 V) can flip the LNB's polarisation.
    - **Proposed fix:** Typical LNB datasheets switch to vertical at 11.5-14 V and horizontal at 16-19 V, and draw under 200 mA (Fagor; Inverto lists about 110 mA). A 4S pack therefore spans both states: at full charge, 16.8 V selects horizontal. So use a regulated, current-limited, switchable supply.
  
  Option A, cleanest:
  - TI TPS65233 LNB regulator: active part, 4.5-20 V input, 13.4/18.2 V output selected over I2C, resistor-set current limit up to 1 A, 22 kHz tone, fault flags.
  - One part gives polarisation select, current limit and fault reporting on the Q6A I2C bus.
  - Evaluation board: TPS65233EVM.
  
  Option B, hobby modules:
  - A boost module from the 5 V rail (for example MT3608-class, price not verified) trimmed to 13.4 V.
  - For 18.2 V, a second feedback resistor switched in by a GPIO-driven N-MOSFET.
  - A 10 uH + 100 uF + 100 nF filter plus a ferrite to suppress switching noise.
  - A 300 mA polyfuse.
  - An INA219 on I2C to log current.
  
  Inject through an SMA bias tee rated 10 MHz-6 GHz (covers 740 MHz by spec) rather than an F-type TV inserter, and measure whichever injector you use.
    - **Steps:**
      - Measure the Bullseye current: bench supply at 13.0 V -> mA meter -> bias tee DC port -> LNB, then repeat at 18 V. Note the start-up surge.
      - Set the current limit to 1.5-2x the measured value (probably 250-300 mA).
      - Measure the injector with a NanoVNA, DC port unpowered. Target: S21 loss of 0.5 dB or less and S11 of -10 dB or better at 730-750 MHz. Reject any TV inserter that fails.
      - Check the regulation: supply the regulator from 12.0 V and from 16.8 V (a full 4S pack). The LNB voltage must stay at 13.4 +/-0.2 V at full load, with ripple under 20 mV p-p measured on an oscilloscope or with an AC voltmeter.
      - Polarity check: on the QO-100 narrowband beacon, which is vertical, compare beacon SNR at 13.4 V and 18.2 V. It should drop markedly at 18 V.
      - If the 50-66 dB LNB gain pushes the RTL-SDR into intermodulation (3 dB pad test), add a 6-10 dB pad at the SDR.
    - **How to verify:** Pass criteria:
  - A logged LNB current figure.
  - Regulator output steady across the whole battery voltage range.
  - Injector loss measured at 740 MHz.
  - Beacon SNR changes as expected when switching between 13.4 and 18.2 V.
  - The current limit trips cleanly on a deliberate coax short.
    - **Confidence:** high
    - **Sources:**
      - https://www.ti.com/product/TPS65233
      - https://fagorelectronica.com/site/assets/files/15826/lnb-18.pdf
      - https://www.inverto.tv/download/file/59560f47059b9-1498812231.pdf
      - https://www.rtl-sdr.com/the-othernet-bullseye-tcxo-lnb-for-qo-100-reception/
      - https://m0aws.co.uk/?p=1811
      - https://www.passion-radio.com/satellite-qo-100/bias-tee-rf-power-supply-module-for-lnb-qo100-and-lna-head-1267.html
  6.
    - **Problem:** AliExpress HMC241 SP4T switch boards are unmeasured: genuine chip or clone, logic level, isolation, and whether DC-block capacitors are fitted.
    - **Proposed fix:** First choice: skip the switch. A handheld uses one antenna per pass, and three ports are available at once (RTL-SDR + Lime RX1 + Lime RX2), so antennas can simply be swapped by hand.
  
  If you want switching anyway, qualify one board on the bench before building it in.
  
  Known datasheet facts:
  - Analog Devices: DC-blocking capacitors are required on RFC and RF1-4, so DC must never pass through the switch.
  - The HMC241QS16 predecessor: control low 0 to +0.8 V, high +2.0 to +5.0 V at about 70 uA, supply +5 V +/-10%.
  
  The Q6A 40-pin header GPIOs pass through UM3204H/UM3304 1.8-to-3.3 V auto-direction translators (schematic v1.21). That gives 3.3 V logic, which meets the 2.0 V high threshold. These translators drive weakly, so do not add strong pull-ups or pull-downs.
  
  Always mount the switch after the LNAs and inject LNA power on the antenna side of it.
    - **Steps:**
      - Check the board visually: chip marking, 5 V supply input, and series capacitors on all five RF ports.
      - With the board unpowered, measure resistance RFx to RFC and RFx to ground with a multimeter. Any DC path means the board needs inline DC blocks.
      - Power it at 5 V and drive A/B from the header. Find the lines with gpioinfo, then (libgpiod v2 on Ubuntu 24.04):
    gpioset -c gpiochipN -z <lineA>=1 <lineB>=0
  Confirm that each code selects the expected port.
      - RF test with a wideband noise source (price not verified) into RF1 and RFC into the SDR. Sweep 100 MHz-1.76 GHz on the RTL-SDR and up to 2.3 GHz on the Lime.
  - Insertion loss: compare against a through-barrel.
  - Isolation: P(RF1 selected) - P(RF2 selected), port by port.
      - Accept the board only if insertion loss is 1.5 dB or less, and isolation is at least 40 dB below 1 GHz and at least 30 dB at 1.7-2.3 GHz.
    - **How to verify:** A measured insertion-loss and isolation table.
  
  On air: a strong FM or DVB-T signal on an unselected antenna must not appear above the noise floor on the selected path.
    - **Confidence:** medium
    - **Sources:**
      - https://www.analog.com/en/products/HMC241AQS16.html
      - https://cdn.components.ru/media/PDF/1445148.pdf
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
  7.
    - **Problem:** Unknown whether the RTL-SDR Blog FM bandstop passes 170-180 mA, and whether the V4/V4L 4.5 V / 180 mA bias tee runs a SAWbird+ reliably in a warm, closed case.
    - **Proposed fix:** Datasheets show the margins are thin. The SAWbird+ NOAA draws 170 mA over bias tee and 175 mA over USB. The SAWbird+ GOES draws 140 mA (120-160). The V4 bias tee is rated 180 mA continuous, the V4L article gives no current figure, and its LDO is pin-compatible with the LP5907. The RTL-SDR Blog FM filter is "safe to 80 mA, possibly 200 mA".
  
  Redesign the chains so the question no longer matters:
  (a) 137 MHz chain: delete the FM filter. The SAWbird+ NOAA plot already shows about 65 dB of rejection across 88-108 MHz (about -25 dB gain against +41 dB). Power it from the internal GPIO-switched 5 V (TPS2553) through a bias tee placed at the RTL input, with the dongle's bias tee off. The bias tee's capacitor also keeps DC away from the dongle input, which avoids the ESD-diode trip that Nooelec warns about for externally powered LNAs.
  (b) 145.8 MHz chain: use the FM filter between the LNA V2 and the dongle only after measuring the LNA current. At 80 mA or less either filter works; above that, use the Flamingo+.
  (c) Any 140-180 mA load that still runs from the dongle's bias tee must pass a soak test first.
    - **Steps:**
      - Measure the current of each LNA: bench 5 V -> mA meter -> bias tee -> LNA.
      - Load-test the FM filter: 5.0 V -> filter -> 27 Ohm / 1 W resistor (about 185 mA) for 60 minutes. Log the DC drop across the filter (should stay under 50 mV) and the case temperature.
      - Soak-test the dongle: V4 or V4L with bias on plus the LNA, inside the closed case at the worst-case internal temperature (about 45-50 C) for 2 hours. Log the LNA supply voltage with a multimeter in min/max mode and the dongle current with a USB power meter. Any dropout means switching to the external supply.
      - Set the bias explicitly in every application, because a SatNOGS user (May 2026) found the bias tee switched off when an observation started:
  - SDR++: 'Bias-T' checkbox.
  - SatDump: the bias option in the RTL source settings.
  - SoapyRTLSDR: biastee=true.
  - Command line: rtl_biast -b 1.
  The hardware GPIO supply avoids this software dependence entirely.
    - **How to verify:** Pass criteria:
  - The logged voltage at the LNA never falls below 4.3 V during the 2-hour soak.
  - The filter's DC drop is stable.
  - The SAWbird LED stays on.
  - The noise-floor rise with the LNA powered stays constant through the soak.
    - **Confidence:** high
    - **Sources:**
      - https://www.nooelec.com/store/downloads/dl/file/id/112/product/301/sawbird_noaa_datasheet_revision_1.pdf
      - https://www.nooelec.com/store/downloads/dl/file/id/108/product/296/sawbird_goes_datasheet_revision_1.pdf
      - https://www.rtl-sdr.com/wp-content/uploads/2024/12/RTLSDR_V4_Datasheet_V_1_0.pdf
      - https://www.rtl-sdr.com/rtl-sdr-com-broadcast-fm-band-stop-filter-88-108-mhz-reject-now-for-sale/
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
      - https://community.libre.space/t/v4-rtl-sdr-bias-tee-issue/14699
      - https://www.nooelec.com/store/sawbird-plus-noaa.html
  8.
    - **Problem:** No data on the Dragon Q6A's per-port USB 2.0 current limit, or on RF self-noise from the Q6A (Wi-Fi/BT, fan, HDMI, PCIe, UFS) between 137 MHz and 2.2 GHz.
    - **Proposed fix:** Answered from the Radxa schematic v1.21 (dl.radxa.com).
  
  USB data:
  - The three USB 2.0 Type-A ports sit behind a Terminus FE1.1S 4-port USB 2.0 hub (U23).
  - The hub's 4th port feeds the Quectel FCU760K Wi-Fi 6 / BT 5.4 USB module (U21), whose power is switched by WIFI_PWR_EN.
  - All of these share one 480 Mb/s uplink. An RTL-SDR at 2.4 Msps needs only about 38 Mb/s.
  
  USB power:
  - VBUS comes from two WS4612 current-limit switches, each with Rset = 3.24 kOhm. The schematic note "Ilim (A)=6800/Rset (ohm)" gives about 2.1 A per switch.
  - U33 feeds VDD_USB_VBUSTYPEA (the J2 dual USB 2.0 stack). U35 feeds VDD_FUSB (the USB 2.0 port under the USB 3 port in J5).
  - So there is no per-port 500 mA trip. Dongle (270 mA) plus LNA (170 mA) is about 0.45 A, well inside the limit.
  
  Noise to test for (hypotheses):
  - PCIe 100 MHz reference clock: the 17th harmonic is 1700.0 MHz, spread to 1691.5-1700 MHz with -0.5% spread-spectrum clocking. That lands right on Meteor HRPT, and the Lime sits on that PCIe link. The 22nd and 23rd harmonics fall at 2200 and 2300 MHz.
  - HDMI 1080p60 pixel clock (148.5 MHz): x5 = 742.5 MHz, next to the 739.5-740 MHz QO-100 IF; x15 = 2227.5 MHz, inside S-band.
  - The Lime's 30.72 MHz VCTCXO: x24 = 737.28 MHz.
  - 2.4 GHz Wi-Fi and Bluetooth next to S-band.
  
  Mitigation:
  - Plug the RTL-SDR into the lower USB 2.0 port of J5, alone on U35, using a 20-30 cm shielded extension with clip-on ferrites.
  - Disable Wi-Fi/BT during L-band and S-band captures.
  - Shield the M.2 extension and Lime with copper tape bonded to ground.
  - Choose an HDMI mode whose harmonics miss the bands.
    - **Steps:**
      - Run lsusb -t and confirm the RTL-SDR sits under the FE1.1s hub (usually 1a40:0101). Put a USB power meter in line and read the current with bias off and on.
      - Take a terminated baseline: 50 Ohm terminators on the RTL-SDR and both Lime ports, then
    rtl_power -f 24M:1766M:100k -g 40 -i 10 -e 2m base.csv
  Do the same with a Lime sweep up to 2.3 GHz.
      - Toggle one subsystem at a time and re-sweep:
  - Wi-Fi/BT off: nmcli radio wifi off; rfkill block all. For a hard off: echo 0 | sudo tee /sys/bus/usb/devices/<port>/authorized
  - HDMI off, then 1080p60 / 1440p60 / 4K30.
  - Fan off, then on.
  - fio sequential write to the UFS.
  - NPU and GPU load.
  - Lime streaming (PCIe active).
      - Look closely at 1691-1701 MHz (PCIe), 739-743 MHz (HDMI and VCTCXO) and 2200-2290 MHz with the Lime at 10 Msps on a 50 Ohm terminator.
      - Mitigate what shows up, re-test, and record which configuration is clean for each band (for example: no Wi-Fi during HRPT and S-band; HDMI mode X while on QO-100).
    - **How to verify:** Pass criteria:
  - A diff of each spectrum against the terminated baseline shows no spur more than 3 dB above it in 136-138, 145-146, 435-438, 739-741, 1698-1710 and 2200-2290 MHz in the planned capture configuration.
  - The USB meter shows stable VBUS (at least 4.75 V) with the LNA powered.
    - **Confidence:** medium
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://docs.radxa.com/en/dragon/q6a/download
      - https://www.quectel.com/product/wi-fi-bluetooth-fcu760k/
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/overview.html
  9.
    - **Problem:** The RTL-SDR Blog V4L (R828S, $37.95) has no switchable FM notch, and its input is diplexed rather than triplexed. There are no field reports of it with LNAs or filters.
    - **Proposed fix:** Accept it and move all FM rejection outside the dongle.
  
  137 MHz:
  - The SAWbird+ NOAA's SAW gives about 65 dB of FM rejection (datasheet plot).
  - Its 2.6 MHz 3 dB passband (136.2-138.8 MHz) covers 137.1 and 137.9 MHz.
  - Gain: 41 dB. NF: 1.1 dB. OP1dB: +20 dBm. Maximum input: 0 dBm.
  
  145.8 MHz:
  - Flamingo+ FM: 70 dB typical stopband depth, 0.5 dB typical passband loss (plot: about 0.3 dB at 145 MHz), passes DC.
  - Optionally a filtered 2 m preamp (fix 10).
  
  If a V4 (R828D, triplexer plus notch) is still in stock, it is the better VHF dongle. Otherwise the V4L plus external filters is equivalent at the antenna port.
    - **Steps:**
      - Before and after fitting the filter, sweep 80-150 MHz with the antenna connected and compare. FM carriers should fall by at least 50 dB.
      - Run the 3 dB pad test (fix 1) at 137.9 MHz and 145.8 MHz with the planned gain.
      - Record a Meteor LRPT pass and an ISS pass. The SatDump SNR and the absence of FM-image spurs in the waterfall confirm the chain.
    - **How to verify:** Pass criteria:
  - No FM or FM-image spurs in 136-146 MHz with the pad test passing.
  - SNR on Meteor LRPT and ISS is comparable to reports from V4 users at similar sites.
    - **Confidence:** high
    - **Sources:**
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-v4l-lite-r828s-rtl2832u-1ppm-tcxo-sma-software-defined-radio-dongle-only/
      - https://www.nooelec.com/store/downloads/dl/file/id/112/product/301/sawbird_noaa_datasheet_revision_1.pdf
      - https://www.nooelec.com/store/downloads/dl/file/id/96/product/320/flamingo_fm_filter_datasheet_revision_1.pdf
  10.
    - **Problem:** Price, stock and shipping to Ukraine are unverified for the EU filtered 2 m / 70 cm LNAs and the S-band filter. The Spacewalker 434 is still not purchasable.
    - **Proposed fix:** Prefer a domestic source.
  
  VHFDesign: the team's callsigns (US4ICI, US2IDR, UR3IQO, UR7IJM, UR6ISU) carry Ukrainian prefixes, so it is very likely a Ukrainian team. Products:
  - LNA-70cm-ATF531-SAW: >22 dB, NF <0.4 dB at 432 MHz, OIP3 37 dBm, 3 dB filter bandwidth <20 MHz, +24 dBm maximum input, 12 V / 140 mA over the feeder.
  - LNA-70cm-EME-SAV541-SAW: >18 dB, NF <0.3 dB, OIP3 33 dBm, 12 V / 40 mA.
  - LNA 2m ATF531: >26 dB, NF <0.3 dB, filter bandwidth <15 MHz.
  - N-female connectors as standard, SMA on request.
  - Prices are behind a login; ask by email.
  
  The 12 V LNAs need a 12 V bias tee from a regulated rail. Do not share the 13.4 V LNB rail: the ATF531 maximum is 12 V.
  
  Fallback for 70 cm: build a Spacewalker-style LNA. The open schematic SWL434 v1.3 uses 2x QPL9547 and 3x Shoulder HDF434A1-S6 SAW filters. Only the schematic is published, no layout, so you would draw your own PCB.
  
  S-band: sysmocom cf2235-kt30 cavity filter.
  - EUR 65.45 (VAT status unclear).
  - 2170-2300 MHz, insertion loss 1.0 dB or less, at least 30 dB rejection below 2160 MHz (the 2.1 GHz cellular band).
  - 124x47x33 mm, 186 g, indoor-rated.
  - Ships UPS only, once a week.
  - Mount it after the LNA V2. Move it before the LNA only if UMTS/LTE 2100 overloads the LNA.
    - **Steps:**
      - Email admin@vhfdesign.com and ask for: price, SMA option, delivery inside Ukraine (Nova Poshta?), and the measured S21 of the 70 cm SAW unit across 425-445 MHz. Their spec only says the passband is under 20 MHz wide, so 437-438 MHz must be confirmed.
      - Ask sysmocom whether UPS will deliver to your oblast. If not, ask about a forwarding route through an EU address.
      - Build a 12 V feed for the VHFDesign LNA: regulated 12.0 V -> polyfuse -> SMA/N bias tee DC port, switched by GPIO through a P-MOSFET.
      - Measure every received unit with the LiteVNA, plus the 3 dB pad test, before field use.
    - **How to verify:** Pass criteria:
  - The measured S21 of the 70 cm unit is flat within 1 dB from 435 to 438 MHz and at least 40 dB down at 470 MHz (DVB-T2).
  - The S-band filter loses 1 dB or less at 2200-2290 MHz and gives at least 30 dB at 2160 MHz.
  - A CubeSat pass at 435-438 MHz shows equal or better SNR than the LNA V2 chain, with no DVB-T2 or LTE spurs.
    - **Confidence:** medium
    - **Sources:**
      - https://community.libre.space/t/rx-only-filtered-lnas-for-vhf-and-uhf-where-to-find/6897
      - https://www.vhfdesign.com/
      - https://vhfdesign.com/lnas/lna-eme-atf531-for-2m-and-70cm-bands.html
      - https://vhfdesign.com/lnas/lna-eme-sav541-for-73cm-and-70cm-bands.html
      - https://vhfdesign.com/contacts
      - https://github.com/zodoczi/Spacewalker-LNA
      - https://www.crowdsupply.com/decent-labs/spacewalker-lna-434-mhz
      - https://shop.sysmocom.de/S-Band-cavity-filter-2170-2300-MHz/cf2235-kt30
      - https://www.sysmocom.de/downloads/rf_filter_cf2235-kt30.pdf
      - https://community.libre.space/t/station-4125-s-band/13718
- **Residual risks:**
  - LimeSDR Micro M.2: the Crowd Supply page says shipping 15 Dec 2026 (pre-order; it could slip further). Its RX schematic is not public, so the presence of DC blocks and the real performance below 300 MHz stay unknown until the board is in hand. Until then, run phase 1 (VHF, UHF and Meteor HRPT) on the RTL-SDR alone.
  - LTE Band 3 uplink at 1710-1730 MHz cannot be filtered. It sits only 2 MHz above the FY-3 band edge and inside the SAWbird passband. Phones within ~10 m can desensitise or overload the HRPT chain; the 6 dB pad and limiter only protect the hardware.
  - SAWbird rejection figures were read by eye from Nooelec's Rev 1 plots (about +/-3 dB). Unit-to-unit spread is unknown.
  - Helix-only HRPT link margin is still unproven for Meteor, Metop and FY-3. If high passes are marginal, a reflector or a larger antenna will be needed (covered by the antenna component).
  - The board-level P1dB and gain curve of the QPL9547 LNA V2 remain unmeasured; the VNA gives small-signal gain only.
  - PCIe reference-clock, HDMI and VCTCXO spur predictions are hypotheses until the terminated-input audit is run on the real hardware.
  - Bullseye LNB current is unknown until measured. The design assumes under 300 mA, based on generic LNB datasheets.
  - The V4L bias-tee current rating appears only on a third-party listing (180 mA), not on the official V4L page.
  - Prices not verified: VHFDesign LNAs, Anatech AB1690B865, TPS65233/EVM, MT3608 modules, VLM-33-S+, DC blocks (a third-party Nooelec DC-block listing at $91.99 looks marked up), noise sources and HMC241 boards. Shipping to Ukraine also not verified for Nooelec, rtl-sdr.com and sysmocom (UPS only).
  - The Q6A 40-pin header GPIOs go through auto-direction level translators. Heavy loads, or strong pull-ups/pull-downs on those lines, can misbehave, so buffer any load that needs current.
  - Hamfests and nearby transmitters: limiters cap the SDR input at about +8 to +12 dBm, but direct coupling from a co-located transmitter can still exceed ratings. Keep receive-only gear away from active transmitters.

## Адверсаріальна перевірка (`verify`)

_Run `wf_30889068-251`_

- **Component:** RF front-end (LNAs, filters, bias tees, LNB power, antenna sharing, protection)
- **Recommendation holds:** так
- **Issues:**
  1.
    - **Claim:** Recommended chain (e) for QO-100 is 'dish + Bullseye LNB -> 13/18 V injector'.
    - **Problem:** This contradicts the update that the user has abandoned dishes.
    - **Correction:** QO-100 still needs an LNB, because nothing in the stack tunes 10.489 GHz, so the 13.4/18 V injector chain is unchanged. The LNB goes on whatever non-dish 10 GHz antenna the antenna component picks (horn, patch, or the bare LNB feed). The Bullseye is $29.95 with 70 in stock. Its 50-66 dB gain means no extra LNA is ever needed. The weaker no-dish signal is the antenna component's problem, not a front-end one.
    - **Source:** https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
  2.
    - **Claim:** The RTL-SDR V4 tops out at 1.766 GHz with 2.56 MHz of bandwidth, so it is 'marginal or unusable for HRPT'.
    - **Problem:** This is wrong for Meteor-M HRPT. OK9SGC's HRPT guide says RTL-SDRs have 'no trouble recording and decoding POES and Meteor-M'. MetOp works at 2.56 Msps with reduced performance. Only FengYun-3 needs a wider SDR.
    - **Correction:** Phase 1 (now, before the Lime ships): helix -> SAWbird+ GOES -> RTL-SDR V4/V4L at 2.4-2.56 Msps for Meteor HRPT. Use the Lime later for MetOp and FY-3.
    - **Source:** https://sgcderek.github.io/blog/beginner-hrpt-guide.html
  3.
    - **Claim:** SAWbird+ GOES: 'at least 30 dB, 180 mA, too much for the V4 bias tee'. SAWbird+ NOAA: '5 MHz SAW passband'.
    - **Problem:** Nooelec's own datasheets are more precise and partly contradict the product pages. The two are inconsistent on current.
    - **Correction:** Datasheet values:
  - GOES+: LNA -> SAW -> LNA; 38 dB gain; 70 MHz 3 dB bandwidth; NF 1.2 dB; 140 mA typical (120-160 mA); OP1dB +20 dBm; maximum input 0 dBm. The product page still says 180 mA nominal.
  - NOAA+: 41 dB gain; 2.6 MHz 3 dB / 3 MHz 10 dB bandwidth; NF 1.1 dB; 170 mA over bias tee; OP1dB +20 dBm.
  The GOES+ therefore fits under the V4/V4L's 180 mA, but only just: soak-test it. The NOAA+ at 170 mA is too close to the limit, so power it separately.
    - **Source:** https://www.nooelec.com/store/downloads/dl/file/id/108/product/296/sawbird_goes_datasheet_revision_1.pdf ; https://www.nooelec.com/store/downloads/dl/file/id/112/product/301/sawbird_noaa_datasheet_revision_1.pdf
  4.
    - **Claim:** Recommended chain (a): power the SAWbird+ NOAA from micro-USB on a clean 5 V rail and connect it straight to the RTL-SDR.
    - **Problem:** The SAWbird's RF output is also its DC input ('RF Output + DC Power'). Powered from USB or the header, it puts 5 V on the SDR input. Nooelec warns this trips some SDRs' ESD diodes and calls for a DC block.
    - **Correction:** Feed it through an SMA bias-tee injector placed at the SDR input: DC port from a GPIO-switched 5 V, RF port toward the SDR. The injector both powers the LNA and blocks DC. Keep the SDR's own bias tee off. Do the same on every Lime port.
    - **Source:** https://www.nooelec.com/store/sawbird-plus-goes.html
  5.
    - **Claim:** Own-fix: delete the FM filter from the 137 MHz chain because the SAWbird+ NOAA rejects FM by about 65 dB.
    - **Problem:** The datasheet schematic shows an LNA BEFORE the SAW. The first MMIC sees FM, pagers and land-mobile signals unfiltered. Intermod products it creates can land in-band, where the SAW cannot remove them. The 65 dB is a small-signal S21 figure, not a large-signal rejection figure. The plot also shows weak rejection just above the passband: roughly +15 dB of gain at 140 MHz and 0 dB at 145 MHz, against +41 dB in-band.
    - **Correction:** Keep the Flamingo+ FM ($24.95; 0.5 dB typical / 1.2 dB maximum passband loss; passes 250 mA of DC) as a plug-in pre-filter in front of the SAWbird at strong-FM or urban sites. At VHF, sky noise makes its loss irrelevant.
    - **Source:** https://www.nooelec.com/store/downloads/dl/file/id/96/product/320/flamingo_fm_filter_datasheet_revision_1.pdf
  6.
    - **Claim:** Research: 'No 435 MHz or 1.7 GHz Uputronics versions were found', and no purchasable filtered 70 cm LNA exists.
    - **Problem:** Missed product. Uputronics makes a 435 MHz CubeSat filtered preamp:
  - PSA4-5043+ LNA, at least 19 dB gain, about 0.75 dB NF.
  - 440 MHz SAW with 30 MHz bandwidth (about 425-455 MHz), so 435-438 MHz is inside.
  - Metal case, SMA-F connectors, powered by USB or bias tee.
    - **Correction:** Make it the preferred 70 cm front-end, at EUR 47.64 incl. VAT from Kubii (stock not confirmed; the page shows 'last items' and a stock alert form). This matters most on the Lime, which has no preselection. Kubii says the bias-tee input is 5-26 V, but other Uputronics listings say 5 V maximum and the RTL gives only 4.5 V, so verify before relying on the RTL bias tee. Fallback: RTL-SDR Blog LNA V2 ($19.95).
    - **Source:** https://kubii.com/en/network-modules/3349-lna-amplifier-modules-with-saw-filter-and-single-frequency-3272496306646.html
  7.
    - **Claim:** Own-fix: a Mini-Circuits VLM-33-S+ limiter plus a 3 dB pad is mandatory overload protection for the Lime.
    - **Problem:** The VLM-33-S+ costs $69.60 each (Mini-Circuits web store), which is overkill for a hobby handheld. A 3 dB pad after a +20-22 dBm OP1dB LNA does not keep the Lime under +10 dBm on its own.
    - **Correction:** Fit a 10-12 dB SMA attenuator after each 38-41 dB SAWbird on the Lime ports. With 38 dB of gain ahead of it, a 10 dB pad changes system NF by less than 0.05 dB. It also caps a saturated LNA output (about +21 dBm) near the Lime's +10 dBm limit and trims excess gain. Buy a limiter only for use near transmitters.
    - **Source:** https://www.minicircuits.com/WebStore/dashboard.html?model=VLM-33-S%2B ; https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
  8.
    - **Claim:** Own-fix: 'The V4L bias-tee current rating appears only on a third-party listing (180 mA).'
    - **Problem:** This is wrong.
    - **Correction:** The official rtl-sdr.com/v4l page states a 4.5 V bias tee that 'can continuously pull up to 180 mA'. The V4L also lists at $37.95 with 455 in stock, but it is a limited edition: R828S stock is expected to last about one year, so buy a spare.
    - **Source:** https://www.rtl-sdr.com/v4l/ ; https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
  9.
    - **Claim:** Forum: 'The V4L has no notch filters, so the FM bandstop becomes mandatory.'
    - **Problem:** Overstated. RTL-SDR Blog says the V4's notch filters 'only attenuate by a few dB'. The V4L's diplexer also removes some filter loss.
    - **Correction:** External FM filtering was needed in Ukrainian cities with either dongle. The V4L is not materially worse at the antenna port.
    - **Source:** https://www.rtl-sdr.com/rtl-sdr-blog-v4-dongle-initial-release/
  10.
    - **Claim:** Stack: LimeSDR Micro at $199, delivering from about Sept 30, 2026.
    - **Problem:** Outdated.
    - **Correction:** Crowd Supply now lists the M.2 2280 Basic at $249 + $18 worldwide shipping (GNSS variant $299), pre-order, shipping Dec 15, 2026. None of the Lime-side front-end can be built or tested in October 2026.
    - **Source:** https://www.crowdsupply.com/lime-micro/limesdr-micro
  11.
    - **Claim:** Own-fix: build the LNB supply around the TI TPS65233.
    - **Problem:** The part exists and is active (4.5-20 V in, 13.4/18.6 V out, I2C, up to 1 A limit). But it comes only in a 3x3 mm WQFN-16, which is hard to hand-solder, and TI shows its EVM as both 'in stock' and 'not available'.
    - **Correction:** For a hobbyist, use an MT3608 or XL6009 boost module from 5 V set to 13.4 V, switch in a second feedback resistor from a GPIO for 18.2 V, and add an LC filter, a 300 mA polyfuse and an optional INA219. Keep the TPS65233 for a custom PCB later.
    - **Source:** https://www.ti.com/product/TPS65233
  12.
    - **Claim:** Buy locally via Prom.ua or Ukrainian stores.
    - **Problem:** Prom.ua (seller Robika) lists:
  - SAWbird+ NOAA: 4,692.78 UAH (about 2.5x the US price), made to order.
  - Both SAWbird+ GOES listings: unavailable.
    - **Correction:** Order directly from Nooelec. It advertises free worldwide shipping on orders over $100, and SAWbird+ NOAA + SAWbird+ GOES + Flamingo+ = $114.85, about EUR 100. That stays under Ukraine's EUR 150 duty-free parcel limit, which is still in force in October 2026 (abolition is pending and targeted for 2027 at the earliest). Buy RTL-SDR Blog items through their official AliExpress store; RTL-SDR Blog says AliExpress delivery to Ukraine works.
    - **Source:** https://prom.ua/search?search_term=sawbird ; https://www.nooelec.com/store/sawbird-plus-goes.html ; https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/ ; https://dev.ua/en/news/rada-provalyla-holosuvannia-pro-skasuvannia-limitu-na-bezmytni-posylky-z-za-kordonu-1779802509
  13.
    - **Claim:** Own-fix: sysmocom cf2235-kt30 S-band cavity, EUR 65.45, ships by UPS.
    - **Problem:** The price and specs are confirmed (EUR 65.45 incl. VAT, 2170-2300 MHz, at most 1.0 dB loss, 30 dB rejection below 2160 MHz). But sysmocom ships only by UPS, and UPS still lists all service to Ukraine as suspended. The filter is also 124x47x33 mm and 186 g, IP50, indoor-rated.
    - **Correction:** Treat S-band as a later phase that needs a forwarder (an EU address, then Nova Poshta or Meest). Mount the filter at the antenna in a cover, not in the palm-sized case. A compact alternative to evaluate is the Mini-Circuits BFCN-2275+ LTCC filter (2170-2380 MHz, 3.2x1.6 mm), which needs a small SMA PCB; price not verified.
    - **Source:** https://shop.sysmocom.de/S-Band-cavity-filter-2170-2300-MHz/cf2235-kt30 ; https://shop.sysmocom.de/Information/Payment-Shipping/
  14.
    - **Claim:** Research: 'Bias tee into DC-shorted antennas (hairpin WB2HOL) shorts the supply.'
    - **Problem:** This applies only when the antenna connects directly to a biased SDR port. With an LNA at the antenna, the bias feeds the LNA output, and the antenna's DC short sits on the LNA's DC-blocked input.
    - **Correction:** Keep the bias tee off whenever an antenna connects to the SDR without an LNA in between. Never use rtl_eeprom -b 1 (bias always on). RTL-SDR Blog warns that days of shorting can kill the LDO or fuse.
    - **Source:** https://www.rtl-sdr.com/v4/
- **Forum and fix assessment:** Mostly sound, and better than the original research on four points:
  - the DC-leak and DC-block issue;
  - using the SAWbird datasheets (140 mA, 38/41 dB gain, NF 1.2/1.1 dB, OP1dB +20 dBm);
  - gain staging with the 3 dB pad test;
  - the Q6A USB analysis. I checked it against the Radxa v1.21 schematic: a WS4612 switch with Rset 3.24 kOhm, 'Ilim (A)=6800/Rset' (about 2.1 A), an FE1.1S hub, and the FCU760K Wi-Fi on that hub. So a dongle plus a 170 mA LNA on one USB 2.0 port is not a problem.
  
  Confirmed:
  - SPF5189Z discontinued (Qorvo PCN 21-0060; QPL9547 recommended).
  - LNA V2: $19.95, QPL9547, 100 MHz-6 GHz, NF under 1 dB, 3-5 V bias.
  - Flamingo+ passes at least 250 mA of DC.
  - RTL-SDR FM bandstop: $16.95, DC pass not stated.
  - Lime: no bias tee documented, +10 dBm maximum input, needs 10 W of cooling.
  - Lime staff (13 Oct 2026) say there are no coverage gaps below 300 MHz, but give no data.
  
  Corrections to the fixes:
  1. 'Delete the FM filter on 137 MHz' is unsafe at strong-FM sites. Both SAWbird+ models are LNA -> SAW -> LNA, so the first MMIC is unprotected. Keep the Flamingo+ as a plug-in pre-filter.
  2. The VLM-33-S+ limiter costs $69.60. A 10-12 dB pad after the 38-41 dB SAWbirds gives the same Lime protection for a few dollars, with no measurable NF cost.
  3. The TPS65233 is a 3x3 mm WQFN with uncertain EVM availability. A boost module is the hobby path.
  4. The V4L 180 mA rating is on the official page, not only on a third-party listing.
  5. sysmocom (UPS only) cannot currently ship straight to Ukraine.
  6. The research's claim that the RTL-SDR is unusable for HRPT is wrong for Meteor-M. Phase-1 HRPT can start on the RTL-SDR before the Lime ships on Dec 15, 2026.
  7. Missed product: the Uputronics 435 MHz CubeSat filtered preamp (30 MHz SAW centred at 440 MHz) fills the '70 cm filtered LNA not purchasable' gap.
  
  The PCIe 17th-harmonic (1691.5-1700 MHz) and HDMI 742.5 MHz spur predictions are plausible but untested. The user's planned higher-than-FHD HDMI mode changes the pixel clock, so run the terminated-input survey again after choosing the display mode.
- **Final recommendation:**
  - **Name:** Per-band filtered chain: Nooelec SAWbird+ NOAA (137) + Flamingo+ FM; RTL-SDR Blog Wideband LNA V2 (QPL9547) for 145.8 and 435 MHz, upgraded to the Uputronics 435 MHz CubeSat filtered preamp for the Lime; Nooelec SAWbird+ GOES at the helix feed (HRPT); SMA bias-tee injectors as DC blocks; 10 dB pads before the Lime; switchable 13.4/18.2 V supply for the QO-100 LNB on a non-dish antenna
  - **Price:** Core about $155: SAWbird+ NOAA 44.95 + SAWbird+ GOES 44.95 + Flamingo+ 24.95 (Nooelec subtotal 114.85, qualifies for free worldwide shipping) + 2x LNA V2 39.90.
  Small parts about $30-50 (prices unverified): 3x generic 10 MHz-6 GHz SMA bias tees, 2x 10 dB SMA pads, 2x TPS2553 load switches, polyfuses, an MT3608 or XL6009 boost module, an F-SMA adapter, and MHF4L-SMA pigtails at $6 each.
  Total about $185-205 before shipping. Optional: Uputronics 435 CubeSat preamp EUR 47.64; S-band later with sysmocom cf2235-kt30 EUR 65.45 + forwarding.
  - **Why:** Each chain is listed antenna to SDR.
  
  (a) 137 MHz Meteor LRPT: V-dipole -> [Flamingo+ only at strong-FM sites] -> SAWbird+ NOAA at the feed -> 1-2 m coax -> SMA bias tee at the RTL input -> RTL-SDR V4/V4L.
  - SAWbird+ NOAA: 41 dB gain, 2.6 MHz bandwidth, NF 1.1 dB, 170 mA.
  - The bias tee's DC port takes GPIO-switched 5 V through a TPS2553. The RTL's own bias tee stays off.
  - Run the RTL at low gain (about 10-25 dB), because 41 dB of LNA gain is a lot.
  
  (b) 145.8 MHz ISS: WB2HOL Yagi -> Flamingo+ -> RTL-SDR.
  - The ISS is loud, so the LNA is optional.
  - If you add the LNA V2, put it at the feed and power it from the RTL's 4.5 V bias tee through the Flamingo+, which passes 250 mA of DC.
  
  (c) 435-438 MHz: 70 cm Yagi -> LNA V2 at the feed (RTL bias tee) -> RTL-SDR in phase 1.
  - On the Lime, use the Uputronics 435 CubeSat SAW preamp (or LNA V2 + filter) -> injector -> 10 dB pad if needed -> Lime RX (L path).
  - Avoid 433.92 MHz ISM SAWs.
  
  (d) 1.7 GHz HRPT: 11-turn RHCP helix -> SAWbird+ GOES screwed onto the feed -> 1-2 m coax.
  - SAWbird+ GOES: 38 dB gain, NF 1.2 dB, 140 mA typical.
  - Phase 1 (now): RTL-SDR at 2.4-2.56 Msps, powered from its bias tee after a 2-hour soak test, for Meteor HRPT.
  - Phase 2 (Lime, from Dec 2026 or later): injector -> 10 dB pad -> Lime RX (W path) at 6-8 Msps for MetOp and FY-3.
  
  (e) QO-100: Bullseye TCXO LNB ($29.95; 50-66 dB gain; 11.5-14 V vertical, 16-19 V horizontal) on the non-dish 10 GHz antenna -> SMA bias tee fed by a regulated, current-limited 13.4 V supply, GPIO-switchable to 18.2 V -> RTL or Lime at the 739.5 MHz IF.
  - No LNA. Add a 6-10 dB pad if the 3 dB pad test shows intermod.
  - Never feed the raw 4S pack (12.0-16.8 V) to the LNB: at full charge it would select horizontal polarisation.
  
  (f) S-band (later): LNA V2 -> S-band bandpass filter -> injector -> Lime RX (W path).
  
  Why this beats the original picks:
  - It drops the end-of-life, often-counterfeit SPF5189Z.
  - Every band with known interference gets a SAW or bandstop filter.
  - All DC injection doubles as DC blocking for the SDR inputs.
  - It uses parts with published datasheets that a Ukrainian buyer can import under the EUR 150 duty-free limit.
  - **Sources:**
    - https://www.nooelec.com/store/sawbird-plus-noaa.html
    - https://www.nooelec.com/store/downloads/dl/file/id/112/product/301/sawbird_noaa_datasheet_revision_1.pdf
    - https://www.nooelec.com/store/sawbird-plus-goes.html
    - https://www.nooelec.com/store/downloads/dl/file/id/108/product/296/sawbird_goes_datasheet_revision_1.pdf
    - https://www.nooelec.com/store/flamingo-plus-fm.html
    - https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
    - https://www.rtl-sdr.com/v4l/
    - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
    - https://kubii.com/en/network-modules/3349-lna-amplifier-modules-with-saw-filter-and-single-frequency-3272496306646.html
    - https://sgcderek.github.io/blog/beginner-hrpt-guide.html
    - https://myriadrf.org/projects/limesdr-micro/user/M.2/setup.html
    - https://www.crowdsupply.com/lime-micro/limesdr-micro
    - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
- **Final budget option:**
  - **Name:** RTL-SDR Blog FM bandstop + one RTL-SDR Blog Wideband LNA V2 (moved between antennas) + Nooelec SAWbird GOES (non-plus) for HRPT + one generic SMA bias tee + boost module for the LNB
  - **Price:** About $85-95 plus shipping: $16.95 + $19.95 + $39.95 + about $5-10 bias tee + about $3-5 boost module and polyfuse (the last two unverified AliExpress prices). The Nooelec part alone is under the $100 free-shipping line, so expect a shipping charge.
  - **Why:** Everything runs from the RTL-SDR V4/V4L's 4.5 V / 180 mA bias tee:
  - The LNA V2 sits behind the FM bandstop at VHF (filter first at strong-FM sites). The RTL-SDR Blog says the filter is safe to pass 80 mA, so measure the LNA V2's draw first.
  - The SAWbird GOES draws 30 mA, has at least 20 dB of gain and an LNA-SAW-LNA 1650-1720 MHz filter. OK9SGC recommends it for short coax.
  
  It still does Meteor LRPT, ISS, 70 cm CubeSats and Meteor HRPT on the RTL-SDR now, with no injectors or DC blocks needed while everything stays on the RTL.
  
  You give up:
  - SAW selectivity at 137 MHz (pager and land-mobile intermod risk);
  - about 18 dB of HRPT gain and published NF data;
  - 70 cm filtering.
  
  Later additions: 10 dB pads and injectors for the Lime ports, and the 13.4/18.2 V LNB supply when QO-100 starts.
- **Known problems and fixes to apply:**
  - Install a V4/V4L-capable driver. Ubuntu 24.04's stock librtlsdr does not support the V4 or V4L (the V4L gives no signal at all). Purge the apt package, build rtlsdrblog/rtl-sdr-blog, check that 'SoapySDRUtil --probe=driver=rtlsdr' prints the V4 detection line, and rebuild SatDump, SDR++ and GNU Radio against that driver.
  - Bias tee silently switched off. Set it explicitly in every application: SoapyRTLSDR biastee=true (a bool, not 1), the SDR++ Bias-T checkbox, the SatDump RTL source option, or rtl_biast -b 1. Confirm with the V4 LED or by measuring about 4.5 V at the LNA. Never use rtl_eeprom -b 1.
  - SAWbird DC on its RF output. When a SAWbird is powered from USB, the header or an external rail, it puts 5 V on its output. Always feed it through an SMA bias-tee injector at the SDR input (RF port toward the SDR), or add a DC block. Never connect it straight to a bare Lime MHF4 port. Check with a meter that the SDR side reads 0 V DC.
  - Lime has no bias tee and a +10 dBm absolute maximum input. Use one injector per Lime RX port, a GPIO-switched TPS2553 load switch (limit about 250 mA, FAULT line to a GPIO), and a 10-12 dB SMA pad after each 38-41 dB SAWbird. The pad costs less than 0.05 dB of system NF.
  - SAWbird+ NOAA current (170 mA typical) versus the RTL bias tee's 180 mA limit. Do not run it from the dongle in a warm case; use the external 5 V injector. For the SAWbird+ GOES (140 mA typical, 160 mA maximum per the datasheet, 180 mA per the product page), do a 2-hour soak test inside the closed case at 45-50 C and log the LNA voltage (it must stay at or above 4.3 V) before relying on the dongle's bias tee.
  - Strong FM in front of the SAWbirds. Both SAWbird+ models put an LNA ahead of the SAW. At urban or strong-FM sites, keep the Flamingo+ FM (0.5 dB typical loss, passes 250 mA of DC, +18 dBm maximum input) in front of the SAWbird+ NOAA and in front of any unfiltered LNA V2 at VHF. Run the 3 dB pad test: a spur that drops by more than 3 dB is intermod made in the receiver.
  - Lime has no preselection. LMS7002M boards show FM and LTE images. Put a band filter on every Lime port (SAWbird GOES at L-band, Uputronics 435 SAW at 70 cm, a cavity or LTCC filter at S-band). Keep 137 and 145.8 MHz on the RTL-SDR until a split-antenna A/B test shows the Lime within 1-2 dB.
  - LTE Band 3 uplink (1710-1730 MHz) is inside the SAWbird GOES passband: about 37 dB of gain at 1720 MHz and about 28 dB at 1730 MHz. Filtering cannot remove it. Keep the 10 dB pad, use low SDR gain, avoid crowds, and prefer Meteor at 1700 MHz. Add a second 1695-1712 MHz filter after the LNA only if a survey shows clipping.
  - LNB supply. Never put the raw 4S pack (12.0-16.8 V) on the LNB: it can flip polarisation, and the Q6A header also tolerates only 16 V. Use a boost or buck-boost regulator set to 13.4 V, GPIO-switchable to 18.2 V, with an LC filter, a ferrite and a 300 mA polyfuse. Measure the Bullseye's current at 13 V and 18 V (not published) and set the limit to 1.5-2x that value. Sweep cheap injectors at 730-750 MHz; generic '10 MHz-6 GHz' tees lose 3-7 dB at 100-200 MHz, so use them only at 740 MHz and above.
  - ESD and handling. Discharge each antenna before connecting it. Prefer metal-cased LNAs (SAWbird, LNA V2 enclosure, Uputronics) to bare boards in 3D-printed plastic. Put a 100-160 mA polyfuse in each bias feed. Keep the bias off when no LNA sits between the antenna and the SDR.
  - Host self-noise. Plug the RTL-SDR into the J5 lower USB 2.0 port (U35 switch) with a 20-30 cm shielded extension and ferrites. Disable Wi-Fi/BT (FCU760K on the same USB hub) during L-band and S-band captures. Shield the M.2 extension and the Lime (which needs at least 10 W of cooling). Run a terminated-input sweep for PCIe 100 MHz harmonics (17th = 1691.5-1700 MHz with spread-spectrum clocking) and HDMI pixel-clock harmonics after choosing the final higher-than-FHD HDMI mode.
  - Gain staging. After adding any LNA, raise SDR gain only until the noise floor sits 6-10 dB above the terminated floor, and keep carriers below about -10 dBFS. At 41 dB the SAWbird+ NOAA needs low RTL gain, and the LNA V2 user review warns it can saturate the SDR.
  - Supply chain.
  - Order the Nooelec parts in one order of at least $100 for free worldwide shipping, and check that Ukraine is accepted at checkout.
  - Buy RTL-SDR Blog parts from their official AliExpress store (RTL-SDR Blog confirms AliExpress delivery to Ukraine works).
  - Keep each parcel under EUR 150 while the duty-free limit lasts.
  - Buy a spare V4L now, because R828S stock is expected to last only about a year.
  - Use an EU-address forwarder for UPS-only shops such as sysmocom.
- **Missed better options:**
  - Uputronics 435 MHz CubeSat filtered preamp: at least 19 dB gain, about 0.75 dB NF, 30 MHz SAW centred at 440 MHz, metal case, SMA-F, USB or bias-tee power. EUR 47.64 incl. VAT at Kubii, stock uncertain. It is a purchasable filtered 70 cm CubeSat LNA, which the research said did not exist (the Spacewalker 434 is still 'launching soon').
  - Run Meteor HRPT on the RTL-SDR V4/V4L now with the SAWbird+ GOES. OK9SGC's guide confirms the RTL-SDR decodes Meteor-M HRPT and MetOp (reduced) at 2.56 Msps. There is no need to wait for the Lime (ships Dec 15, 2026, $249).
  - A 10-12 dB SMA attenuator after each high-gain SAWbird replaces the $69.60 VLM-33-S+ limiter. It trims gain and protects the Lime's +10 dBm input with no measurable NF penalty.
  - The SMA bias-tee injector at the SDR end does three jobs at once: it powers the LNA, blocks DC from the SDR input, and lets the GPIO switch the bias. That removes separate DC blocks (a Mini-Circuits BLK-89-S+ costs about $15-25).
  - Nooelec SAWbird NOAA (non-plus): $49.95, about 0.7 dB NF, at least 20 dB gain, about 80 mA. It runs straight from the V4L bias tee with no injector, at the cost of unpublished selectivity data. It is a simpler 137 MHz alternative if wiring count matters more than documented FM rejection.
  - Mini-Circuits BFCN-2275+ LTCC bandpass filter (2170-2380 MHz, 3.2x1.6 mm) on a small SMA board: a palm-sized alternative to the 186 g sysmocom cavity for later S-band work. Price and Ukraine sourcing not verified.
  - VHFDesign: a 2 m / 70 cm LNA maker whose team's callsigns are Ukrainian (US4ICI, UR3IQO and others). Products include ATF-53189 and SAV-541 SAW LNAs, 0.3-0.4 dB NF, 12 V on the feeder. They are possibly domestic, but use N connectors, prices are hidden, and the 70 cm SAW is specified only as under 20 MHz wide and characterised at 432 MHz. Ask by email for S21 at 435-438 MHz before buying.
- **Remaining uncertainties:**
  - LimeSDR Micro: there is no public RX schematic (whether DC blocks are fitted is unknown), no sensitivity data below 300 MHz, and the Dec 15, 2026 ship date may slip.
  - Uputronics 435 CubeSat preamp: current stock is unclear, and the bias-tee voltage range conflicts between listings (Kubii says 5-26 V, other listings say 5 V maximum). Whether it runs from the RTL's 4.5 V bias tee is unverified.
  - The RTL-SDR V4L's upper frequency limit (R828S) is not stated on the official pages. It is assumed to match the V4's 1.766 GHz; confirm before relying on it for 1.7 GHz HRPT.
  - The board-level gain curve and P1dB of the RTL-SDR Blog LNA V2 are unpublished, and there are no long-term field reports.
  - Bullseye LNB current draw is unpublished. The helix-only HRPT link margin and the no-dish QO-100 antenna are unproven (antenna component).
  - Not verified for October 2026: Nooelec shipping to Ukraine (USPS or UPS); prices of generic SMA bias tees, pads, the MT3608/XL6009, TPS2553 and BFCN-2275+; the RF Konnect injector, shown out of stock at Passion Radio; and VHFDesign prices.
  - SAWbird rejection values were read by eye from Nooelec's Rev 1 plots (about +/-3 dB). Unit-to-unit spread is unknown, and the product pages and datasheets disagree on current (180 mA vs 140 or 170 mA).
  - The PCIe, HDMI and VCTCXO spur predictions are hypotheses until the terminated-input survey is run on the real Q6A with the final display mode.
  - The Ukrainian parcel VAT reform (abolishing the EUR 150 limit) is pending second reading and targeted for 2027 at the earliest. The timing could change.
- **Confidence:** medium

_Агент цього етапу ще працює (run `wf_30889068-251`)._

