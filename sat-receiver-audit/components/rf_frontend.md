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

_Агент цього етапу ще працює (run `wf_30889068-251`)._

