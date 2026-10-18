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

_Run `wf_feb0e95a-cfc`_

- **Subsystem:** rf_frontend (LNAs, FM band-stop, bias tees and TPS2553 limits, LNB 13.2 V feed, RF switches, DC blocks, protection, lab sled)
- **Findings:**
  1.
    - **Claim in stack:** LNA+SAW 137 MHz: Nooelec SAWbird+ NOAA cased (100800), $49.95; 41 dB, NF 1.1 dB, 170 mA; placed inside the case after the Flamingo+, bias fed into the SAWbird output from injector ch1.
    - **Finding:** Confirmed. SKU 100800 (with enclosure) is $49.95 and orderable. Datasheet Rev 1 (2022-06-29) gives 41 dB at 137.5 MHz, 2.6 MHz 3 dB / 3 MHz 10 dB bandwidth, NF 1.1 dB, 170 mA via bias tee (175 mA via USB), OP1dB +20 dBm, maximum input 0 dBm, Vin 3.3-5.5 V, and 'RF Output + DC Power' on the output port. The live product page still says 'min 30 dB', '180 mA nominal' and a '5 MHz bandpass'. The stack's 180 mA budget covers both figures. 4.5 V minus the TPS2553 drop is inside the supply range.
    - **Verdict:** confirmed
    - **Action:** Keep. Keep the current budget at 180 mA (product-page figure). Make sure input power stays at or below 0 dBm (the max) at strong-signal sites; the Flamingo+ in front handles FM.
    - **Impact:** None
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-noaa-308.html
      - https://www.nooelec.com/store/downloads/dl/file/id/112/product/301/sawbird_noaa_datasheet_revision_1.pdf
  2.
    - **Claim in stack:** Budget option for 137 MHz: 'SAWbird NOAA without + (80 mA)'.
    - **Finding:** Not a budget option. The non-plus Nooelec SAWbird NOAA (SKU 100852) costs $49.95, the same as the cased SAWbird+ NOAA. Specs: at least 20 dB, about 0.7 dB NF, about 80 mA, no published bandwidth. The cheaper part is the SAWbird+ NOAA Barebones (SKU 100799) at $44.95, which is electrically the same as the plus model.
    - **Verdict:** corrected
    - **Action:** Change the budget entry to 'SAWbird+ NOAA Barebones 100799, $44.95, mounted inside the shielded RF compartment'. List the non-plus SAWbird NOAA only as a lower-current alternative (80 mA), not as a saving.
    - **Impact:** Budget line -$5. It was wrongly shown as a saving.
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-noaa.html
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-noaa.html
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird.html
  3.
    - **Claim in stack:** FM band-stop: Nooelec Flamingo+ FM v2 (100813), $24.95; >60 dB rejection, 0.5 dB typ / 1.2 dB max loss, 250 mA DC pass; filter first on VHF.
    - **Finding:** Confirmed. The product page shows $24.95 and 'v2'. It specifies more than 60 dB typical average and more than 70 dB typical maximum stopband rejection, -3 dB points at 75 and 120 MHz, out-of-band loss below 0.25 dB, at least 250 mA DC handling, and +18 dBm maximum input. Datasheet Rev 1 (2019) gives passband loss 0.01/0.5/1.2 dB (min/typ/max) and a stopband of 80.5-114.8 MHz. On P1 no DC crosses it (bias enters at the SAWbird output), so the DC rating does not matter there.
    - **Verdict:** confirmed
    - **Action:** Keep. The RTL-SDR Blog band-stop is still $16.95 on the buy page, and its DC rating is still unpublished (its old product URL now returns 404).
    - **Impact:** None
    - **Sources:**
      - https://www.nooelec.com/store/flamingo-plus-fm.html
      - https://www.nooelec.com/store/downloads/dl/file/id/96/product/320/flamingo_fm_filter_datasheet_revision_1.pdf
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
  4.
    - **Claim in stack:** Uputronics 440 MHz CubeSAT filtered preamp: bias input depends on revision ('5-26 V' vs '5V max', registry #98); running at 4.5 V via ch2 is not verified; GBP 51.59 incl. VAT = $68.71; in stock.
    - **Finding:** Resolved by Uputronics' FPA Series datasheet Rev 3.0 (18/10/2024):
  - Bias-tee input 3.5-5.5 V; above 5.5 V causes permanent damage. 4.5 V (minus the TPS2553 and choke drop) is inside the spec.
  - About 50 mA, average NF 0.75 dB, at least 19 dB gain for the 440 MHz model.
  - Antenna connector DC-blocked (no bias pass-through), a Skyworks limiter on the antenna input, and an HPF below 100 MHz.
  - USB-C and bias tee may be connected at the same time.
  - When unpowered there is no signal pass-through and the unit attenuates heavily.
  - Not rated for outdoor use and not IP rated.
  Vendor plot of the 440 MHz unit: 19.63 dB at 440 MHz, 16.27 dB at 427.3 MHz and 16.17 dB at 452 MHz, so 435-438 MHz sits on the flat top. All variants show available=true on 18 Oct 2026. The store price of GBP 51.59 appears to include 20% UK VAT: all FPA prices divide by 1.2 to x.99 values (inferred, not confirmed at checkout).
    - **Verdict:** corrected
    - **Action:** Remove the '5-26 V' / 'not verified at 4.5 V' caveat and mark it 'in spec, 3.5-5.5 V; still measure current'. In labd, never route more than 5.5 V to any port the Uputronics can reach. At about 50 mA, ch2 qualifies for the TCBT-2R5G+ budget injector. Add a rain cover at the Yagi feed. Use the ex-VAT world price: GBP 42.99, about $57.26, to be confirmed at checkout.
    - **Impact:** About -$11.45 against the stack's $68.71 if the export price is ex-VAT. Removes an open bring-up risk.
    - **Sources:**
      - https://store.uputronics.com/products/uputronics-filtered-preamps
      - https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf?v=1729257808
  5.
    - **Claim in stack:** Uputronics 434 MHz variant ($55.92 = GBP 41.99) is a narrow ISM SAW; do not buy.
    - **Finding:** Confirmed by the vendor plot. The 434 MHz unit measures 20.25 dB at 434 MHz, 15.92 dB at 429.97 MHz and 16.08 dB at 437.97 MHz. The top of the 435-438 MHz CubeSat band is therefore about 4 dB down.
    - **Verdict:** confirmed
    - **Action:** Keep the 440 MHz variant.
    - **Impact:** None
    - **Sources:**
      - https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf?v=1729257808
  6.
    - **Claim in stack:** RTL-A/RTL-B input switches: generic HMC7992 SP4T boards; the 50 Ohm load goes on the throw that the 'all low' power-up state selects (planned as T4); isolation >=30 dB; 3.3 V logic; all throws without DC.
    - **Finding:** Mapping error. In the HMC7992 datasheet (Rev 0, Table 6), A=Low, B=Low selects RFC-RF1, not RF4. RF4 needs A and B both high. The part has no EN pin and no all-off state, so one path is always connected. An MCP23017 resets to inputs (high-Z), so the A/B lines float at boot unless resistors define them.
  Other datasheet values:
  - 0.1-6 GHz, non-reflective.
  - Insertion loss 0.6 dB typ / 0.9 dB max (0.1-2 GHz). Isolation 40 dB min / 45 dB typ (0.1-2 GHz), 32/37 dB (2-4 GHz).
  - Off-state return loss only 7 dB at 0.1-0.4 GHz, so the internal termination of unused ports is a poor 50 Ohm at VHF.
  - VDD 3.0-5.4 V. VIH min is 1.15 V at VDD 3.3 V and 1.55 V at VDD 5 V, so 3.3 V logic is fine.
  - Every RF pin is DC-coupled and needs a blocking capacitor.
  - The chip is Active at DigiKey: $13.10 (qty 1), 4,655 in stock.
    - **Verdict:** corrected
    - **Action:** Either put the 50 Ohm park load on RF1, or fit pull-ups on A and B (for example 10k to 3.3 V) so power-up selects RF4. Fit the pull resistors either way. Check that the chosen generic board has DC-blocking capacitors on all five RF pins. Keep the conducted isolation qualification at >=30 dB.
    - **Impact:** Without this fix, at power-up the SDR would sit on an antenna path (VHF-137 / L-band) instead of the load, against the Bench/park rule.
    - **Sources:**
      - https://www.farnell.com/datasheets/2283884.pdf
      - https://www.digikey.com/en/products/detail/analog-devices-inc/HMC7992LP3DE/5873027
  7.
    - **Claim in stack:** HMC7992 generic boards, 2 pcs, $30-40, marketplace (unverified).
    - **Finding:** No primary marketplace listing was verified. A Walmart.ca listing shows a 'HMC7992 Non-Reflective SP4T RF Switch Module' at $20.49 (currency and date unclear). The bare chip costs $10.25-13.10 at DigiKey/Mouser/Newark (qty 1). The stack already has a custom 2-layer injector PCB with C0G blocks.
    - **Verdict:** new_option
    - **Action:** Option: place the two HMC7992LP3DE chips directly on the custom injector PCB (about $13 each), with your own C0G blocks, A/B pull resistors and a shield can. This removes the unknowns of a generic board (missing DC blocks, layout isolation) and two SMA jumpers per switch. Otherwise buy one generic board first and qualify it on the LiteVNA before buying the second.
    - **Impact:** About -$5 to -$15 and two fewer coax hops per receiver. Needs a 4-layer or carefully grounded QFN footprint (model).
    - **Sources:**
      - https://www.digikey.com/en/products/detail/analog-devices-inc/HMC7992LP3DE/5873027
      - https://www.walmart.ca/en/ip/HMC7992-Non-Reflective-SP4T-RF-Switch-Module-PCB-Material-0-1-6GHz-Frequency-Range-3V-5V-Power-Supply-45dB-Isolation-0-6dB-Insertion-Loss-58dBm-IIP3/4LT6JIAL4ULJ
  8.
    - **Claim in stack:** Scope alternative: Mini-Circuits connectorized SP4T switch instead of HMC7992.
    - **Finding:** The Mini-Circuits ZSWA4-63DR+ (absorptive SP4T, 1-6000 MHz, SMA) costs $307.32 at qty 1-9, with 0 in stock at Mini-Circuits and 0 at DigiKey.
    - **Verdict:** confirmed
    - **Action:** Keep the HMC7992. Do not use a Mini-Circuits connectorized switch.
    - **Impact:** None
    - **Sources:**
      - https://www.minicircuits.com/WebStore/dashboard.html?model=ZSWA4-63DR%2B
  9.
    - **Claim in stack:** TPS2553 current switches: LNA ch1-4 at 300 mA nominal (from 240 mA minimum), LAB port 0.75 A; check the latching TPS2553-1; 10 pcs $5.50 at LCSC; TI store out of stock.
    - **Finding:** Mostly confirmed.
  - TI status: ACTIVE (datasheet Rev F). VIN 2.5-6.5 V, adjustable limit 75 mA-1.7 A, RILIM 15-232 kΩ.
  - Fault behaviour: the plain part holds constant current; the '-1' suffix latches off.
  - Reverse-voltage comparator trips at VOUT-VIN 95-190 mV.
  - From the datasheet equations (my calculation), RILIM = 88.7 kΩ gives 265 / 299 / 339 mA (min/nom/max, resistor tolerance excluded). The stack's '240 mA min' is therefore conservative.
  - Price: a DigiKey listing shows TPS2553DBVR at $1.16. The LCSC $5.50 for 10 was not re-verified.
  - The TPS2553 cannot be used on the 12.5 V or 13.2 V rails (6.5 V maximum).
    - **Verdict:** confirmed
    - **Action:** Use TPS2553-1 (latch-off) on the outward-biased channels ch2-ch4, so a shorted feed does not sit in constant-current mode, and have labd clear the latch by toggling EN. Specify RILIM 88.7 kΩ 1%. The reverse-voltage block also covers the case where a user powers the Uputronics from USB-C while ch2 is on.
    - **Impact:** Low. Better fault behaviour on the antenna-facing ports.
    - **Sources:**
      - https://www.ti.com/product/TPS2553
      - https://www.ti.com/lit/ds/symlink/tps2553.pdf
      - https://www.digikey.com/en/products/result?keywords=TPS2553DBVR
  10.
    - **Claim in stack:** LNB13V2 rail: SW -> LC -> TPS7A4701 (3-36 V, 1 A, 307 mV dropout) -> 13.2 V ±0.2 V at the F connector; preliminary 0.45 A PTC; internal limit and OTP; PG to MCP #3; EN from MCP #1 GPB0 only when RTL-B is on T2. The BONI12V5 rail is the same, also with PG.
    - **Finding:** Part choice and these specs confirmed: Active; 3-36 V; 1 A; dropout 307 mV typ / 450 mV max at 1 A; θJA 30.5 °C/W.
  Three corrections:
  1. The TPS7A47 has no power-good pin (pins: OUT, NC, SENSE/FB, the ANY-OUT pins, GND, EN, NR, IN; 'PG' does not appear anywhere in the datasheet). 'PG on MCP #3' is impossible for both the LNB and Boni rails.
  2. Current limit is 1.0 A min / 1.26 A typ, and TI says the LDO is not designed to run steadily in current limit. A shorted F centre pin at 16.4 V input would dissipate about 20 W until thermal shutdown cycles, with only a slow PTC behind it.
  3. Overall accuracy is ±2.5%, so 13.2 V ±0.33 V, not ±0.2 V. That is still inside the LNB vertical-polarisation range (<14 V).
  The dissipation model (0.96 W at 0.3 A from 16.4 V) is confirmed.
    - **Verdict:** corrected
    - **Action:** After each TPS7A4701, add a TI TPS2596 eFuse (Active; 2.7-19 V; current limit adjustable 0.125-2 A, ±10.4% max; latch or auto-retry; FLT pin) set to about 1.5-2x the measured LNB current (Boni about 0.125 A). Wire FLT to MCP #3 in place of the nonexistent PG. The PTCs become optional. Option: a TPS25962x variant has a fast 13.8 V over-voltage clamp, which would keep the LNB from ever seeing horizontal-polarisation voltage if the LDO fails short (variant ordering not verified). Correct the tolerance to ±0.33 V, or trim it.
    - **Impact:** A design error in the power board netlist (PG pin). Fault protection on the only connector that carries 13.2 V.
    - **Sources:**
      - https://www.ti.com/product/TPS7A47
      - https://www.ti.com/lit/ds/symlink/tps7a47.pdf
      - https://www.ti.com/product/TPS2596
  11.
    - **Claim in stack:** QO-100 NB via a bare Bullseye LNB on P4 with 13.2 V (vertical); Bullseye $29.95, 70 in stock; gain 50-66 dB; current 0.2-0.3 A unpublished.
    - **Finding:** Confirmed. AMSAT-DL states 'Downlink polarisation for the NB transponder is V (vertical linear polarization)', so a 13 V class feed is correct. The Bullseye page shows $29.95, 70 in stock, gain 50-66 dB, NF 0.5 dB, LO 9750/10600 MHz, 2 ppm TCXO, ±30 kHz over -20 to 60 °C, factory calibration within 1 kHz, IF 739-1950 MHz, and a 25 MHz reference output on a second F connector. Current draw and the V/H voltage thresholds are still unpublished. The buy page says the LNB needs a 12-19 V bias tee and that the RTL's 4.5 V tee is not for this LNB.
    - **Verdict:** confirmed
    - **Action:** Keep it held behind the region gate. Measure the LNB current at 13.2 V before setting the eFuse limit. Leave the 25 MHz reference port unterminated or capped (it is an output).
    - **Impact:** None
    - **Sources:**
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines/
  12.
    - **Claim in stack:** LNB IF: total noise into the SDR -33...-22 dBm (model), so a 15 dB attenuator (20 dB if LNB gain is over 60 dB) sits between the injector and RTL-B T2.
    - **Finding:** My own model, kT·B over the 739-1950 MHz IF with Tsys 150-300 K and gain 50-66 dB, gives -36 to -17 dBm. That brackets the stack's range, with a slightly hotter top end. The HMC7992 (P1dB +33-35 dBm) is not a concern. Keeping the attenuator after the DC block is correct.
    - **Verdict:** confirmed
    - **Action:** Keep 15/20 dB and the 3 dB-pad intermod test. Choose 20 dB as the default if the measured LNB gain is unknown.
    - **Impact:** None (model)
    - **Sources:**
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
  13.
    - **Claim in stack:** 13.2 V into an ANNE-50+ (1 W) would dissipate about 3.5 W, so there is a DC block before every SDR and instrument; lab kit has 2x BLK-89-S+ ($20.26) and 3x ANNE-50+ ($14.84).
    - **Finding:** Confirmed. 13.2²/50 = 3.48 W. The ANNE-50+ datasheet (Rev H) gives 1 W at 50 °C, derated linearly to 0.35 W at 100 °C. It costs $14.84 with more than 1,000 in stock at Mini-Circuits. The BLK-89-S+ datasheet (Rev G) gives 0.1-8000 MHz, 50 V DC, 4 W RF (1 W at 100 °C), and insertion loss 0.10 dB typ at 100-1000 MHz. It costs $20.26 with more than 1,000 in stock at Mini-Circuits (DigiKey shows 0).
    - **Verdict:** confirmed
    - **Action:** Keep.
    - **Impact:** None
    - **Sources:**
      - https://www.minicircuits.com/WebStore/dashboard.html?model=ANNE-50%2B
      - https://www.minicircuits.com/pdfs/ANNE-50+.pdf
      - https://www.minicircuits.com/WebStore/dashboard.html?model=BLK-89-S%2B
      - https://www.minicircuits.com/pdfs/BLK-89-S+.pdf
  14.
    - **Claim in stack:** Budget injector: Mini-Circuits TCBT-2R5G+ $11.31, only on channels <=150 mA (200 mA maximum).
    - **Finding:** Specs confirmed: 20-2500 MHz; insertion loss 0.2 dB typ (20-2500 MHz), 0.35 dB (200-1250 MHz) and 0.7 dB (1250-2500 MHz); 200 mA DC; 25 V maximum at the DC port; a required external 0.01 µF capacitor. Price corrected: Mini-Circuits now lists only a 10-49 tier at $9.05 each (no 1-9 tier) with 71 in stock. DigiKey shows 1,589.
    - **Verdict:** corrected
    - **Action:** Update the price to $9.05 each at qty 10+ (about $90 minimum from Mini-Circuits), or buy singles from DigiKey. Eligible channels: Uputronics 440 (about 50 mA), the L-band patch (20 mA), H1 (120 mA) and LNA V2 (90 mA). Not eligible: SAWbird+ NOAA/GOES/iO (170-180 mA).
    - **Impact:** Small price change. Minimum-order trap.
    - **Sources:**
      - https://www.minicircuits.com/WebStore/dashboard.html?model=TCBT-2R5G%2B
      - https://www.minicircuits.com/pdfs/TCBT-2R5G+.pdf
  15.
    - **Claim in stack:** Spare LNA: RTL-SDR Blog Wideband LNA V2, $19.95, 208 in stock, 90 mA; also the LNA for the optional P8 WIDE/2 m path behind a second Flamingo+.
    - **Finding:** Confirmed. The product page shows $19.95, 208 in stock, 100 MHz-6 GHz, NF below 1 dB, 3-5 V, QPL9547-based. The buy page states 'Needs 3-5V, 90mA bias tee power'. Gain and P1dB are still unpublished. The Qorvo QPL9547 page could not be fetched (HTTP 429). No LNA V3 is listed.
    - **Verdict:** confirmed
    - **Action:** Keep. Measure gain and current at bring-up as already planned.
    - **Impact:** None
    - **Sources:**
      - https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
  16.
    - **Claim in stack:** L-band LNA: Nooelec SAWbird+ GOES cased (100792), $49.95; 38 dB, NF 1.2 dB, 140 mA typ / 180 mA budget, OP1dB +20 dBm, max input 0 dBm, passband 1648-1728 MHz (LTE B3 uplink inside); Barebones 100791 $44.95.
    - **Finding:** Confirmed. The product page shows SKU 100792, $49.95, an 80 MHz passband around 1688 MHz, '180 mA nominal' and 'at least 30 dB'. Datasheet Rev 1 (2022-06-24): 70 MHz 3 dB / 80 MHz 10 dB bandwidth, 38 dB (printed in the Max column), NF 1.2 dB, 120/140/160 mA, OP1dB +20 dBm, Pin max 0 dBm. The Barebones is $44.95 on the category page. No new SAWbird variants (17 products, all orderable).
    - **Verdict:** confirmed
    - **Action:** Keep. Keep the 180 mA budget on ch3.
    - **Impact:** None
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-goes-302.html
      - https://www.nooelec.com/store/downloads/dl/file/id/108/product/296/sawbird_goes_datasheet_revision_1.pdf
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird.html
  17.
    - **Claim in stack:** Inmarsat-C LNA: SAWbird+ iO cased (100788) $49.95, bought only after the egc-gate.
    - **Finding:** Confirmed. SKU 100788, $49.95, 1542 MHz centre, 60 MHz passband, at least 30 dB, 180 mA nominal, 3-5 V via SMA. The iO Barebones is $44.95.
    - **Verdict:** confirmed
    - **Action:** Keep it behind the egc-gate. The budget alternative is the Barebones at $44.95 inside the shielded compartment.
    - **Impact:** None
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-io-303.html
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird.html?p=2
  18.
    - **Claim in stack:** Extended: SAWbird+ H1, $45-50, unverified (URL gave 404); 120 mA, 65 MHz, >=40 dB, NF about 0.8 dB.
    - **Finding:** The product page now resolves: SKU 100811 at $49.95, at least 40 dB, NF about 0.8 dB (Barebones about 1.05 dB), 120 mA nominal, 65 MHz passband at 1420 MHz, 3-5.5 V, three feed options.
    - **Verdict:** corrected
    - **Action:** Set the price to $49.95 (verified 18 Oct 2026) and use the new URL.
    - **Impact:** Extended total moves to the top of its range ($49.95 instead of $45-50).
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-h1.html
  19.
    - **Claim in stack:** HF+ input switch: 2x Omron G6K-2F-RF 5 V in series-parallel; GBP 43-52 for two (RS UK); >=35 dB isolation at 162-260 MHz and <=0.3 dB loss from 10 kHz to 260 MHz; unpowered = HF+ on 50 Ohm.
    - **Finding:** Part is valid, but the brand has changed. OMRON's Device & Module Solutions business was spun off on 1 July 2026 as Aratas Corporation (Carlyle-owned, independent from 1 Oct 2026). DigiKey now lists 'G6K-2F-RF DC5, Aratas (formerly Omron Components)' at $25.06 and the 3 GHz 'G6K-2F-RF-T DC5' at $26.03, so about $50-52 for two. The datasheet rates it at 1 GHz: isolation at least 20 dB between same-polarity contacts and at least 30 dB between different-polarity contacts, insertion loss at most 0.2 dB. The '>=35 dB at 162-260 MHz' for the series-parallel pair is a model, not a datasheet value. The HMC7992 is no substitute: it is specified only from 0.1 GHz and has no defined unpowered state.
    - **Verdict:** new_risk
    - **Action:** Order by part number, accepting the Aratas or Omron marking; the part numbers are unchanged. Price from DigiKey (about $50-52 for two) or RS. Keep the relays; measure the isolation on the LiteVNA.
    - **Impact:** Sourcing/branding only. No reported spec change.
    - **Sources:**
      - https://www.digikey.com/en/products/result?keywords=G6K-2F-RF%20DC5
      - https://www.digikey.com/en/products/result?keywords=G6K-2F-RF-T%20DC5
      - https://www.omron.com/global/en/news/2026/07/c0701-1.html
      - https://www.electropages.com/blog/2026/07/omron-electronic-components-rebrands-aratas
      - https://electronicsdatasheets.com/download/51d58e51e34e242f4000002a.pdf?format=pdf
  20.
    - **Claim in stack:** RF sled (extended): HMC7992 SP4T + PE4302 + MCP23017 #2 + ADS1115 + buck->LC->LDO bias + enclosure, $104-168 marketplace; isolation 30-37 dB, not the vendor's 45 dB; RF4 50 Ohm default; source on RF3 <= -40 dBm with RF1/RF2 loaded.
    - **Finding:** Partly corrected. The PE4302 is on pSemi's discontinued list (2016 EOL group). The PE4312 is 'In Production' and is pin-compatible with the PE4302: 1 MHz-4 GHz, 31.5 dB in 0.5 dB steps, 2.3-5.5 V, 1.8 V logic compatible, and it does not need the PE4302's series resistors on C16/DATA. Marketplace 'PE4302' modules are therefore old stock or clones. The 30-37 dB isolation expectation is conservative against the chip spec (40 dB min at 0.1-2 GHz). As above, the HMC7992 default (A=B=low) selects RF1, not RF4. Marketplace module prices were not re-verified.
    - **Verdict:** corrected
    - **Action:** Specify a PE4312 module, or check the chip marking on arrival. Add A/B pull-ups so the sled powers up on RF4 (50 Ohm), or move the load to RF1. Keep the conducted-only rule (at most -40 dBm, antenna ports loaded).
    - **Impact:** EOL part in the sled BOM. Fails unsafe at power-up unless the pull-ups are added.
    - **Sources:**
      - https://psemi.com/?p=11471
      - https://www.psemi.com/products/digital-step-attenuators/pe4312
      - https://www.farnell.com/datasheets/2283884.pdf
  21.
    - **Claim in stack:** V4L bias tees off in core (librtlsdr token, EEPROM bias off); spare V4L tee only for LNAs <=90 mA; V4L tee rated 4.5 V / 180 mA.
    - **Finding:** Confirmed. rtl-sdr.com/v4l says the 4.5 V bias tee 'can continuously pull up to 180 mA', with a self-resetting thermal fuse and LDO overcurrent protection, and that updated drivers are required. The rtlsdrblog GitHub release V1.4.0 (marked Latest) adds V4L support; the release page shows a date without the year.
    - **Verdict:** confirmed
    - **Action:** Keep the gating. Pin the driver to rtl-sdr-blog V1.4.0 or later.
    - **Impact:** None
    - **Sources:**
      - https://www.rtl-sdr.com/v4l/
      - https://github.com/rtlsdrblog/rtl-sdr-blog/releases
  22.
    - **Claim in stack:** P5 (HF) is an SMA that tolerates DC and carries 12.5 V up the coax only in the Boni profile; DC-sense runs before any bias is enabled.
    - **Finding:** New risk. P2, P3 and P5 all use SMA. An Uputronics FPA plugged into P5 while the Boni profile is active would take 12.5 V (permanent damage above 5.5 V per its datasheet). A SAWbird is 'not recommended' above 5 V. DC-sense would see an LNA as a valid load, not a short. The Boni-Whip itself has a BNC connector (WiMo listing), ships with its own bias tee, and is specified for 12-15 V (WiMo ES says 9-15 V). A forum quote of the manual gives about 40 mA maximum; not verified at the primary source.
    - **Verdict:** new_risk
    - **Action:** Physically key P5: use a BNC bulkhead (it matches the Boni-Whip and HF wire baluns) so no SMA LNA can mate with the 12.5 V port. Keep DC-sense, and add an explicit 'Boni attached' confirmation in the menu. The Boni rail limit can be the TPS2596 set near 0.125 A.
    - **Impact:** Prevents destroying a $50-70 LNA through one wrong plug.
    - **Sources:**
      - https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf?v=1729257808
      - https://www.wimo.com/en/18067
      - https://forums.radioreference.com/threads/boni-whip-power-supply-questions.455226
  23.
    - **Claim in stack:** Protection: SMBJ TVS and fuses on power rails, DC-sense before bias, bias blocked on DC-short profiles, 'discharge antennas before connecting'; no RF ESD or limiter element is listed on the antenna ports.
    - **Finding:** New risk. The SAWbird+ NOAA sits behind a passive, DC-passing Flamingo+ on P1, and the SAWbird+ GOES sits directly on the helix feed. Nooelec publishes no ESD limiter for either; their first stage is a bare MMIC. By contrast the Uputronics FPA has a Skyworks limiter and a <100 MHz HPF on its input. The stack has no static bleed or limiter on P1, P3 or P6.
    - **Verdict:** new_risk
    - **Action:** Add a DC static-bleed shunt inductor at the no-DC ports P1 and P6 (high impedance at 137-260 MHz; value to be chosen and verified on the LiteVNA; model). On the biased ports P2 and P3, choose a low-capacitance RF TVS with a working voltage above 5 V (part not yet selected or verified). Qualify the insertion loss conducted. The earlier audit's Mini-Circuits VLM-33-S+ limiter ($69.60) was not re-verified and is overkill for the device; keep it only as a bench option.
    - **Impact:** Robustness of the unprotected first-stage LNAs in dry or windy field use.
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-noaa-308.html
      - https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf?v=1729257808
  24.
    - **Claim in stack:** ADS-B budget alternative: Uputronics 1090 preamp GBP 44.39 ($59.12).
    - **Finding:** Confirmed available at GBP 44.39; datasheet gives at least 14 dB. The same VAT inference applies: GBP 36.99 ex-VAT, about $49.27.
    - **Verdict:** corrected
    - **Action:** Use the ex-VAT world price after confirming at checkout.
    - **Impact:** About -$10 on the budget line.
    - **Sources:**
      - https://store.uputronics.com/products/uputronics-filtered-preamps
      - https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf?v=1729257808
  25.
    - **Claim in stack:** 137 MHz first stage is the SAWbird+ NOAA (no alternative listed).
    - **Finding:** Alternative exists: the Uputronics 137.5 MHz NOAA FPA (GBP 59.99 incl. VAT, about $66.58 ex-VAT inferred; available). Specs: at least 22 dB, about 50 mA, average NF 0.75 dB, Skyworks input limiter and HPF, but larger V2 enclosure. It is not better on price or gain. Its advantages are about one third of the current and ESD protection.
    - **Verdict:** new_option
    - **Action:** Do not switch now. Use it as a fallback if the SAWbird+ NOAA suffers ESD or overload failures in the field.
    - **Impact:** None now
    - **Sources:**
      - https://store.uputronics.com/products/uputronics-filtered-preamps
      - https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf?v=1729257808
  26.
    - **Claim in stack:** LNA4V5 bus from 2x ADI LT3045 in parallel (about 1 A); LCSC $8.33 each (unverified).
    - **Finding:** Not re-verified in this pass: analog.com returned HTTP 503 on every attempt, and the price was not checked. Only the interface matters for this subsystem: 4 x 300 mA TPS2553 limits (1.2 A) exceed the pair's about 1 A, which the stack already handles through the labd budget (LNA total <= 1.0 A).
    - **Verdict:** unverified
    - **Action:** Leave this to the power-subsystem audit. Keep the labd LNA budget at <= 1.0 A.
    - **Impact:** None for RF
    - **Sources:**
      - https://www.analog.com/en/products/lt3045.html
  27.
    - **Claim in stack:** Rule compliance of the RF front end: receive-only; signal sources (GPSDO, noise source, tinySA generator, VNA port 1) only in Bench mode, conducted, all switches on 50 Ohm, <= -40 dBm; no loop or H-field parts; no dish (bare LNB, horn, or cone).
    - **Finding:** Confirmed. No component in this subsystem transmits on air. The sled and HMC7992 isolation (40 dB min on the chip, 30-37 dB expected at board level) keeps a -40 dBm bench source at least 70 dB below 0 dBm at the loaded antenna ports. The Bullseye on a horn or cone is dish-free. Correcting the HMC7992 power-up state above is needed so that the park-at-50-Ohm rule actually holds at boot.
    - **Verdict:** confirmed
    - **Action:** Apply the HMC7992 A/B pull fix. Otherwise no change.
    - **Impact:** None once the fix is applied
    - **Sources:**
      - https://www.farnell.com/datasheets/2283884.pdf
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines/
- **Current status oct 2026:** As of 18 Oct 2026:
  - Nooelec: the SAWbird line is unchanged (17 products, all orderable, no EOL notices). Free worldwide shipping on orders over $100. Prices: SAWbird+ NOAA, GOES, iO and H1 cased $49.95; Barebones $44.95; Flamingo+ FM v2 $24.95. Datasheets are still Rev 1 (2019/2022).
  - Uputronics: every FPA variant shows available. The FPA datasheet is Rev 3.0 (18/10/2024) and settles the bias-voltage question at 3.5-5.5 V.
  - RTL-SDR Blog: Wideband LNA V2 $19.95 (208 in stock), Bullseye LNB $29.95 (70 in stock), FM band-stop $16.95. Admin comments on the buy page say the V4 is EOL; the V4L 'limited first batch' is sold from the China warehouse. Driver rtl-sdr-blog V1.4.0 (Latest) adds V4L support.
  - HMC7992LP3DE: Active at DigiKey, $13.10, 4,655 in stock.
  - Mini-Circuits: ZSWA4-63DR+ $307.32 with zero stock. TCBT-2R5G+ now $9.05 at qty 10-49 only. BLK-89-S+ $20.26 and ANNE-50+ $14.84 (more than 1,000 in stock each).
  - TI: TPS2553, TPS7A47 and TPS2596 are all Active.
  - Omron relays (G6K-2F-RF) are now sold under the Aratas brand (spun off 1 Jul 2026, independent 1 Oct 2026); DigiKey shows $25-26 each.
  - pSemi PE4302 is discontinued (2016 group); the PE4312 is In Production and pin-compatible.
- **Notes:** I checked against primary sources: manufacturer pages, datasheet PDFs downloaded and text-extracted, vendor response plots viewed, TI, Mini-Circuits, pSemi, DigiKey and AMSAT-DL. I used about 8 WebSearch calls.
  
  **Fixes that need a design change:**
  1. **HMC7992 power-up state.** With A=B=low the switch selects RF1, not RF4. Add pull resistors, or move the 50 Ohm park load to RF1.
  2. **TPS7A4701 has no PG pin.** It also has no usable short-circuit limit, since its current limit is 1.0 A min and it is not meant to run there. Add a TPS2596 eFuse with its FLT line to MCP #3 on both the LNB and the Boni rails.
  3. **P5 needs physical keying.** The 12.5 V Boni rail sits on an SMA like the LNA ports; a BNC on P5 stops an SMA LNA from mating with it.
  4. **PE4302 in the sled is EOL.** Specify the pin-compatible PE4312.
  
  **Resolved open item:** the Uputronics 440 runs on 3.5-5.5 V at about 50 mA, so the 4.5 V ch2 feed is in spec.
  
  **Price corrections:**
  - SAWbird NOAA (non-plus) is not cheaper ($49.95). The real budget part is the SAWbird+ NOAA Barebones at $44.95.
  - SAWbird+ H1 is verified at $49.95.
  - TCBT-2R5G+ is $9.05, at quantity 10 or more.
  - Uputronics store prices appear to include 20% UK VAT. This is inferred from all prices dividing to .99 values. The ex-VAT 440 price is about $57.26; confirm at checkout.
  
  **Numbers I computed (not datasheet values):**
  - TPS2553 RILIM 88.7 kΩ gives 265/299/339 mA (from TI's equations).
  - LNB IF noise: -36 to -17 dBm (kTB model).
  - ANNE-50+ at 13.2 V: 3.48 W.
  
  **Not verified:**
  - LT3045 and the ADI pages (analog.com returned 503); the HMC7992 datasheet was read from Farnell's copy instead.
  - QPL9547 gain and P1dB (Qorvo returned 429).
  - Generic HMC7992 and PE43xx module prices (only a Walmart.ca listing at $20.49).
  - LCSC TPS2553 price.
  - Bullseye LNB current.
  - Boni-Whip current (40 mA comes only from a forum quote).
  - Exact RF TVS part for the biased ports.
  - The G6K series-parallel isolation figure (a model).
  
  Downloaded datasheets are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfdl/.

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

_Run `wf_feb0e95a-cfc`_

- **Subsystem:** rf_frontend (stage 3, adversarial verification): LNAs, FM band-stop, bias tees and TPS2553 limits, LNB 13.2 V feed with eFuse, BONI rail, HMC7992 and G6K switches, DC blocks and loads, protection, lab sled, librtlsdr bias-tee gate
- **Verdict:** The subsystem holds up, with corrections. Every core part is real, current and orderable as of 18 Oct 2026, and the rules are respected: receive-only, conducted-only sources, no loops, no dishes. Two findings from stages 1 and 2 would have broken the hardware, and both now have a fix:
  1. The bias-tee token patch (C11, and stage 2's advice to gate inside rtlsdr_set_bias_tee_gpio()) would also block GPIO 5. Osmocom's V4/V4L code drives the HF/VHF-UHF input switch through that same function, so with the gate in place every core V4L, which runs without a bias token, would lose VHF/UHF switching. The gate must apply to gpio==0 only.
  2. HMC7992 power-up: A=B=low selects RF1, not RF4. The 50 Ohm park load goes on RF1, not pull-ups.
  
  Several stage-1/2 fixes needed refinement:
  - The TPS2596 FLT pin does not assert during overcurrent or short-circuit current limiting. It does not replace PG on its own, so per-rail current readback is needed (INA3221).
  - The TPS25962x clamp is rejected (confirmed). TPS259630DDAR is Active, $1.07 at DigiKey with 487 in stock.
  - RILM for a 0.125 A limit is 7.87 kOhm, not 7.5 kOhm.
  - Uputronics pricing: the store's own regional prices are EU EUR 52.95 (taxes at checkout) = $59.52 and US $62.00. This refutes both stage 1's $57.26 and stage 2's 'keep $68.71'.
  - The QO-100 IF-ingress check targeted the wrong services. In the EU, B28 uplink is 703-733 MHz. The 739.5 MHz IF sits in the optional 738-758 MHz SDL/PMSE gap.
  - The TCBT-2R5G+ (200 mA) cannot sit behind a TPS2553 set to 300 mA. A TCBT channel needs RILIM 162 kOhm.
  - TPS7A47 Rev G (May 2026) gives θJA 32.5 °C/W, not 30.5.
- **Confirmed:**
  - SAWbird+ NOAA cased SKU 100800 $49.95, Add to Cart. Datasheet Rev 1 (2022): 41 dB at 137.5 MHz, 2.6 MHz 3 dB / 3 MHz 10 dB bandwidth, NF 1.1 dB, 170 mA bias-T (175 mA USB), OP1dB +20 dBm, Pin max 0 dBm, Vin 3.3-5.5 V. Product page: bias through the SMA output port 3-5 V, '180 mA nominal', 2-year warranty (https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-noaa-308.html, datasheet id/112).
  - Non-plus SAWbird NOAA SKU 100852 costs $49.95 (about 80 mA, at least 20 dB, NF about 0.7 dB), so it is not a budget option. SAWbird+ NOAA Barebones SKU 100799 costs $44.95 but carries a 1-year warranty (https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-noaa.html, .../sawbird-plus-noaa.html).
  - Flamingo+ FM v2 SKU 100813 $24.95. Datasheet Rev 1 (2019-12-02, titled Flamingo+ FM): stopband 80.5-114.8 MHz, passband IL 0.01/0.5/1.2 dB, Pin max +18 dBm. Page: >60 dB typical average / >70 dB typical maximum, -3 dB at 75/120 MHz, <0.25 dB out-of-band loss, DC handling 250 mA min, 'front end protected by an ESD diode meant for RF applications'.
  - SAWbird+ GOES cased 100792 $49.95 (Barebones 100791 $44.95). Datasheet: 70/80 MHz bandwidth at 1688 MHz, 38 dB (Max column), NF 1.2 dB, 120/140/160 mA, OP1dB +20 dBm, Pin 0 dBm. SAWbird+ iO cased 100788 $49.95 (Barebones 100787 $44.95). SAWbird+ H1 100811 $49.95: at least 40 dB, NF about 0.8 dB, 120 mA, 65 MHz bandwidth.
  - Uputronics FPA datasheet Rev 3.0 (18/10/2024): bias 3.5-5.5 V ('Exceeding 5.5V will cause permanent damage'), about 50 mA, NF average 0.75 dB, 440 MHz gain at least 19 dB, V3 enclosure 69x40x12 mm, LNA before SAW, antenna port DC-blocked, Skyworks limiter, HPF <100 MHz, no signal pass-through when unpowered, not outdoor or IP rated. 440 plot markers: 19.63 dB at 440 MHz, 16.27 dB at 427.33 MHz, 16.17 dB at 452 MHz. All variants available=true.
  - The 434 MHz Uputronics variant is unsuitable for 435-438 MHz: its plot shows 20.25 dB at 434 MHz and 16.08 dB at 437.67 MHz.
  - HMC7992 (Rev 0 datasheet, Farnell copy) Table 6: A=B=Low selects RF1 and High/High selects RF4. All five RF pins are DC-coupled and need blocking capacitors. Power-up order is GND, then VDD, then control inputs; logic before VDD can damage the ESD structures. VDD 3.0-5.4 V. VIH min 1.15 V at VDD 3.3 V. Insertion loss 0.6/0.9 dB and isolation 40 min / 45 typ dB at 0.1-2 GHz. Specified 0.1-6 GHz only. DigiKey HMC7992LP3DE: Active, $13.10, 4,655 in stock.
  - TPS2553 (SLVS841F): VIN 2.5-6.5 V, RILIM 15-232 kOhm. Equations IOSmax=22980/R^0.94, IOSnom=23950/R^0.977, IOSmin=25230/R^1.016. RILIM 88.7 kOhm gives 265/299/339 mA (262-342 mA including 1% resistor tolerance; model). The -1 suffix latches off after a 7.5 ms typical deglitch. Reverse-voltage trip at 95-190 mV. TPS2553DBVR-1: DigiKey $1.06, 4,259 in stock, Active.
  - TPS7A47 (SBVS204G, revised May 2026): no PG pin (the pin list is OUT, NC, SENSE/FB, 6P4V1/2, 3P2V, 1P6V, 0P8V, 0P4V, 0P2V, 0P1V, EN, NR, IN, GND). ICL 1.0 A min / 1.26 A typ, 'not designed to operate at a steady-state current limit'. Overall accuracy ±2.5%, so 13.2 V is 12.87-13.53 V. Dropout 307 mV typ / 450 mV max at 1 A. VEN(HI) min 2.0 V. ANY-OUT reaches 13.2 V (1.4+6.4+3.2+1.6+0.4+0.2) and 12.5 V.
  - The TPS25962x 13.8 V clamp is wrong for a 13.2 V rail (stage 2 is right): VOVC is 12.97/13.77/14.52 V, VCLAMP is 13.13/13.58/13.97 V, and a footnote says to limit input to the selected clamp option. TPS25963x has an adjustable OVLO, rising 1.17/1.2/1.22 V and falling 1.08/1.10/1.13 V, with automatic recovery. RILM range 453-7869 Ohm; RILM = 903/(ILIM - 0.0112); accuracy ±10.4% max. TPS259630 latches off and TPS259631 auto-retries after thermal shutdown.
  - rtl-sdr-blog fork librtlsdr.c: rtlsdr_set_offset_tuning() calls rtlsdr_set_bias_tee(dev,on) for R820T/R828D tuner types, and the V4L reports as R820T. force_bt = (EEPROM byte 7 & 0x02) ? 0 : 1 forces the tee on and blocks 'off'. Osmocom master and v2.0.3 have neither path. rtl-sdr.com/v4l: 'legacy DVB-T TV drivers will activate the bias tee by default', and the EEPROM flag is 'ignored' by other drivers. The V4L tee is rated 4.5 V and can 'continuously pull up to 180 mA'.
  - Osmocom rtl-sdr tag v2.0.3 points to 797f814 'Release 2.0.3' (2026-08-12) and contains 0204c9c 'Add RTL-SDR Blog V4L Support' (2026-05-01) and 65f0658 'Fix application hang on USB transfer errors'. 7ebcb04 set SOVERSION back to 0, so 2.0.3 builds .so.0, not .so.2. rtl-sdr-blog V1.4.0 is titled 'RTL-SDR-BLOG Windows Release V1.4.0'.
  - V4L: diplexed rather than triplexed input; 'not as well filtered against strong signals' (two-tone result the same as the V3); 'No notch as there is no open_d pin on the R828S' (admin). This supports keeping the Flamingo+ first on VHF.
  - Bullseye LNB $29.95, 70 in stock: gain 50-66 dB, NF 0.5 dB, LO 9750/10600 MHz, ±10 kHz at 23 °C / ±30 kHz over -20 to 60 °C, factory calibration within 1 kHz, IF 739-1950 MHz with return loss only 8 dB, 25 MHz reference on a second F connector. Buy page: 'Requires a 12-19V bias tee... 11.5 - 14V enables vertical'. AMSAT-DL: 'Downlink polarisation for the NB transponder is V'. LNB current is still unpublished.
  - LNB IF noise model (kTB over 1.211 GHz, Tsys 150-300 K, gain 50-66 dB): -36 to -17 dBm. The 15/20 dB pad after the DC block is justified.
  - Mini-Circuits: TCBT-2R5G+ costs $9.05 at qty 10-20 (no 1-9 tier), stock 71. Datasheet Rev G: 20-2500 MHz, 200 mA, +25 V max at the DC port, external 0.01 µF required. BLK-89-S+ $20.26 (1-4), >1,000 in stock; Rev G: 0.1-8000 MHz, IL 0.10 typ / 0.3 max at 100-1000 MHz, +50 V DC, 4 W (1 W at 100 °C). ANNE-50+ $14.84, >1,000 in stock; Rev H: 1 W at 50 °C derated to 0.35 W at 100 °C, so 13.2 V into it is 3.48 W. ZSWA4-63DR+ $307.32 with 0 in stock.
  - RTL-SDR Blog Wideband LNA V2: $19.95, 208 in stock, QPL9547, 100 MHz-6 GHz, NF <1 dB, '3 - 5v, 90mA'. L-band patch: '3.3 - 5v 20mA'. RTL-SDR Blog FM band-stop: $16.95, no DC rating published.
  - pSemi: PE4302 is on the 'Discontinued Products' list under 2016. PE4312 is 'In Production', 1-4000 MHz, 31.5 dB in 0.5 dB steps, 2.3-5.5 V, and 'Pin-compatible to PE4302, PE4305 and PE4306'.
  - G6K-2F-RF DC5 is listed at DigiKey as 'Aratas (Formerly Omron Components)', $25.06. Electropages (23 Jul 2026): OMRON Electronic Components now operates as Aratas, with 'products and technical support continuing'.
  - Boni-Whip: WiMo lists '10 kHz - 300 MHz, BNC', '2x BNC', bias tee included, EUR 159.00 incl. VAT, 'Available from 20.11.2026'. Bonito (manufacturer) gives 'Spannungsversorgung: 12V -15V'. Current is unpublished; the manual link returns 404. Moving P5 to a BNC bulkhead is confirmed as the right physical key.
  - Nooelec states SAWbird+ overvoltage protection ('up to 12V DC should still work', not long-term, not covered by warranty) and that a DC block is needed with SDRs whose ESD diode trips. The Uputronics is permanently damaged above 5.5 V. A 12.5 V P5 must therefore never mate with an SMA LNA.
  - Rule compliance holds once the RF1 park fix is in: nothing transmits on air; bench sources are conducted only at ≤ -40 dBm with antenna throws loaded; no loop or H-field parts; the Bullseye is used bare, with a horn or cone and no dish.
- **Corrections:**
  1.
    - **Claim in stack:** C11 / stage 2: the librtlsdr token patch makes rtlsdr_set_bias_tee() AND rtlsdr_set_bias_tee_gpio() refuse 'on' without LAB_BIAS_OK. Stage 2 says to put the gate inside rtlsdr_set_bias_tee_gpio(), 'which all three paths call'.
    - **Finding:** Osmocom's own V4 code (since 2.0.1) and V4L code (0204c9c, in 2.0.3) call rtlsdr_set_bias_tee_gpio(priv->rtl_dev, 5, !cable_1_in) to drive the 'upconverter GPIO switch on newer batches'. For any VHF/UHF tune on a V4L, band==UHF, so cable_1_in=0 and the call asks for GPIO5 = on. A gate on every GPIO number either fails r82xx_set_freq (if it returns <0) or leaves the HF/UHF switch in the wrong position. The core V4Ls, which run without a token, would show dead or attenuated VHF/UHF.
    - **Verdict:** corrected
    - **Action:** Gate only gpio==0 inside rtlsdr_set_bias_tee_gpio(): `if (gpio == 0 && on && !lab_bias_ok(dev)) return -1;`. Never gate GPIO 5. Keep osmocom-based librtlsdr (noble 2.0.1 plus cherry-picks, or 2.0.3 with SOVERSION patched back to 2). Never install the rtl-sdr-blog fork (offset-tuning hack and EEPROM force_bt). Strengthen the DVB blacklist with 'install dvb_usb_rtl28xxu /bin/false' plus update-initramfs. Bring-up: tune 137/437/1700 MHz and 10 MHz with no token on the patched build and compare levels against the stock build.
    - **Impact:** Prevents a bring-up failure that would look like dead V4Ls on VHF/UHF.
    - **Sources:**
      - https://raw.githubusercontent.com/osmocom/rtl-sdr/master/src/librtlsdr.c
      - git show v2.0.3:src/tuner_r82xx.c lines 1195 and 1242 (https://github.com/osmocom/rtl-sdr)
      - https://raw.githubusercontent.com/rtlsdrblog/rtl-sdr-blog/master/src/librtlsdr.c
      - https://www.rtl-sdr.com/v4l/
  2.
    - **Claim in stack:** 5.3 / 2.3: 50 Ohm on the throw selected by 'all low' at power-up, planned as T4. Sled: RF4 50 Ohm default.
    - **Finding:** Datasheet Table 6 maps A=B=Low to RF1. D13 already pulls every MCP23017 pin down with 100k, so boot selects RF1. Pull-ups to the Q6A 3.3 V rail risk driving the logic pins before VDD, which the datasheet power-up sequence warns against.
    - **Verdict:** corrected
    - **Action:** Put the 50 Ohm park load on RF1 of every HMC7992 (RTL-A, RTL-B, the Lime switch and the sled).
  - RTL-A: RF1 50 Ohm, RF2 VHF-137, RF3 UHF, RF4 WIDE/2 m.
  - RTL-B: RF1 50 Ohm, RF2 L-band, RF3 LNB IF, RF4 BENCH/sled.
  - Lime switch: RF1 is the safe default route.
  Power HMC7992 VDD from the same 3.3 V rail as the MCP23017s, or add 1 kOhm series resistors in A/B. Fit 100 pF on A/B and C0G DC blocks on all five RF pins, RFC included.
    - **Impact:** The park-at-50-Ohm rule now actually holds at boot.
    - **Sources:**
      - https://www.farnell.com/datasheets/2283884.pdf
  3.
    - **Claim in stack:** C8 / 5.1 LNB13V2 and BONI12V5: 'PG to MCP #3'; 13.2 V ±0.2 V; PTC 0.45 A as the only current limit. Stage 1 says FLT replaces PG.
    - **Finding:** Three problems:
  - TPS7A47 has no PG pin, and its ICL is ≥1.0 A, which is not a usable short-circuit limit.
  - Accuracy is ±2.5%, so 12.87-13.53 V.
  - In the TPS2596, FLT asserts on overtemperature, OVLO and an ILM short to GND, but NOT in overcurrent or short-circuit current limiting (Table 3). A soft overload can sit in current limit with no flag.
  TPS259630DDAR is Active: DigiKey $1.07, 487 in stock; TI store out of stock. RILM = 903/(ILIM - 0.0112).
    - **Verdict:** corrected
    - **Action:** Each rail becomes: TPS7A4701 (ANY-OUT) → TPS259630DDAR (latch-off after thermal shutdown) → INA3221 shunt → choke.
  - LNB: RILM 2.05 kOhm 1% gives 0.405-0.499 A. Reset it to 1.5-2 times the measured Bullseye current.
  - Boni: RILM 7.87 kOhm gives 0.113-0.139 A (datasheet point). Stage 2's 7.5 kOhm gives about 0.132 A; the equation asks for 7.94 kOhm, above the 7869 Ohm maximum.
  - OVLO divider 110 kOhm / 10.0 kOhm 0.5% on both rails: trip 13.91-14.77 V (model), above the 13.53 V rail maximum and below the 16 V horizontal threshold.
  - FLT to MCP #3 through a pull-up. labd latches any FLT in software.
  - Drop the PTCs. Change the tolerance to ±0.33 V.
  - TPS259631DDAR (auto-retry) is the stock fallback.
    - **Impact:** Removes a netlist error (a PG pin that does not exist). A shorted F centre pin is now limited to about 0.45 A and then latched off. An LDO failing short can no longer put more than about 14.8 V on the LNB or Boni.
    - **Sources:**
      - https://www.ti.com/lit/ds/symlink/tps7a47.pdf
      - https://www.ti.com/lit/ds/symlink/tps2596.pdf
      - https://www.ti.com/product/TPS2596/part-details/TPS259630DDAR
      - https://www.digikey.com/en/products/result?keywords=TPS259630DDAR
  4.
    - **Claim in stack:** C8: LDO dissipation +29 K at 0.3 A with θJA 30.5 °C/W, and +44 K at 0.45 A.
    - **Finding:** Rev G (May 2026) gives RθJA 32.5 °C/W for RGW. That makes 0.96 W about +31 K and 1.44 W about +47 K (model).
    - **Verdict:** corrected
    - **Action:** Update the thermal figures. Keep the LDOs bonded to the plate.
    - **Impact:** About 3 K more. Still inside 125 °C.
    - **Sources:**
      - https://www.ti.com/lit/ds/symlink/tps7a47.pdf
  5.
    - **Claim in stack:** C9: TCBT-2R5G+ (200 mA max) only on channels ≤150 mA, with every channel behind a TPS2553 at 300 mA.
    - **Finding:** A TPS2553 at 88.7 kOhm lets 262-342 mA through before limiting. That is above the TCBT's 200 mA rating, so the TCBT is not protected. From the datasheet equations, RILIM 162 kOhm gives 144/166/192 mA (model).
    - **Verdict:** new_risk
    - **Action:** On a TCBT channel (ch2 Uputronics or ch4 LNA V2 only), fit RILIM 162 kOhm 1%. ch1 and ch3 keep 88.7 kOhm and the custom 0.5 A chokes. TCBT price: $9.05 each at qty 10+ from Mini-Circuits (71 in stock); singles from DigiKey.
    - **Impact:** Prevents cooking a budget injector in a partial-short fault.
    - **Sources:**
      - https://www.ti.com/lit/ds/symlink/tps2553.pdf
      - https://www.minicircuits.com/pdfs/TCBT-2R5G+.pdf
      - https://www.minicircuits.com/WebStore/dashboard.html?model=TCBT-2R5G%2B
  6.
    - **Claim in stack:** Stage 1: TPS2553-1 on ch2-ch4 only. Stage 2: per-channel current readback, part not chosen.
    - **Finding:** The TPS2553 has no current monitor, and a degraded LNA at 260-300 mA would sit under the trip point. INA3221AIRGVR (0-26 V bus, 40 µV shunt LSB, addresses 0x40-0x43, Rev C September 2026) is Active: DigiKey $3.47, 65,552 in stock. I2C2 already uses 0x20, 0x21, 0x22, 0x30 and 0x48.
    - **Verdict:** new_option
    - **Action:** Use TPS2553DBVR-1 (latch-off) on all four channels: one part number, and labd toggles EN to reset.
  Add 2x INA3221 on I2C2 at 0x41 and 0x43:
  - ch1-ch4 LNA with 0.2 Ohm shunts (36 mV at 180 mA, 0.2 mA resolution).
  - LNB with a 0.1 Ohm shunt.
  - Boni with a 0.2 Ohm shunt.
  labd alarms at more than 20% over each LNA's bring-up baseline. This also covers the TPS2596 current-limit blind spot.
    - **Impact:** About $7 plus shunts. Catches degraded or ESD-damaged LNAs and soft overloads on the LNB and Boni rails.
    - **Sources:**
      - https://www.ti.com/lit/ds/symlink/ina3221.pdf
      - https://www.digikey.com/en/products/result?keywords=INA3221AIRGVR
      - https://www.digikey.com/en/products/result?keywords=TPS2553DBVR-1
  7.
    - **Claim in stack:** 2.3: Uputronics 440 at $68.71 (GBP 51.59 incl. VAT). Stage 1: ex-VAT about $57.26. Stage 2: keep $68.71 for a European buyer.
    - **Finding:** The store localises prices (Shopify .js, 18 Oct 2026):
  - UK GBP 51.59 'Tax included'.
  - DE/FR EUR 52.95 with 'taxes calculated at checkout' = $59.52 at the stack's 1.1241 rate.
  - US $62.00.
  1090 unit: EUR 44.95 ($50.53) / US $53.00. 137.5 MHz unit: EUR 60.95 ($68.51) / US $72.00. The stack's convention is USD without import VAT. EU landed cost with 19-21% VAT is about $70.8-72.0 (model), not $68.71.
    - **Verdict:** corrected
    - **Action:** List the 440 at $59.52 (EUR 52.95, EU storefront, before checkout VAT), with US $62.00 as the world reference. List the 1090 alternative at $50.53. Note the EU landed cost of about $71-72 if VAT is added at checkout. Confirm at checkout.
    - **Impact:** -$9.19 on the 440 line against the stack. Refutes both earlier figures.
    - **Sources:**
      - https://store.uputronics.com/products/uputronics-filtered-preamps
      - https://store.uputronics.com/products/uputronics-filtered-preamps.js
  8.
    - **Claim in stack:** 2.3: budget for the 137 MHz LNA is 'SAWbird NOAA without +' (80 mA).
    - **Finding:** The non-plus part (100852) is $49.95, the same as the cased plus. SAWbird+ NOAA Barebones 100799 is $44.95 with the same electrical spec, but a 1-year warranty against 2 years for the cased 100800.
    - **Verdict:** corrected
    - **Action:** Budget line: Barebones 100799, $44.95, inside the shielded RF compartment, with the warranty difference noted. Keep the non-plus only as a low-current (80 mA, at least 20 dB) alternative.
    - **Impact:** -$5 on the budget line. Shorter warranty.
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-noaa.html
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-noaa.html
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-noaa-308.html
  9.
    - **Claim in stack:** 2.3 Uputronics row: bias input depends on revision ('5-26 V' vs '5V max'); 4.5 V not verified.
    - **Finding:** Datasheet Rev 3.0 gives 3.5-5.5 V, about 50 mA, and permanent damage above 5.5 V.
    - **Verdict:** corrected
    - **Action:** Mark it 'in spec at 4.5 V; measure current'. labd must never route more than 5.5 V to P2 or P3. Add a rain cover at the Yagi feed (not IP rated).
    - **Impact:** Closes an open bring-up item.
    - **Sources:**
      - https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf?v=1729257808
  10.
    - **Claim in stack:** C23 / 5.3: QO-100 LNB IF-penetration check for DVB-T 734-742 MHz and LTE B28 uplink.
    - **Finding:** For Europe, EU Decision 2016/687 puts FDD uplink at 703-733 MHz (below the 739.5-740 MHz IF), downlink at 758-788 MHz, and the 733-758 MHz gap at optional SDL 738-758 MHz (base-station downlink, member-state choice), PMSE, PPDR (733-736 / 753-758) and M2M. The NB IF therefore sits inside the optional SDL/PMSE gap.
    - **Verdict:** corrected
    - **Action:** Re-aim the ingress test at 733-758 MHz (SDL/PMSE): RTL-B on the LNB throw with the LNB powered off, then on. Keep double-shielded 75 Ohm coax and tight F connectors.
    - **Impact:** The test now targets the real local occupants of the IF.
    - **Sources:**
      - https://eur-lex.europa.eu/eli/dec_impl/2016/687/oj
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
  11.
    - **Claim in stack:** 5.3 Meteor LRPT: RTL-A gain 10-25 dB with the 41 dB SAWbird+ NOAA ahead.
    - **Finding:** Cascade model with 41 dB minus 1.5 dB of loss ahead: an RTL NF of 15/20/25/30 dB gives a system NF of 1.11/1.14/1.22/1.46 dB. Extra RTL gain adds headroom risk on the notchless V4L and almost no SNR. The community recommendation of 0-10 dB comes from stage 2 and was not re-fetched.
    - **Verdict:** corrected
    - **Action:** Default 5-10 dB (range 0-15 dB). At bring-up, pick the lowest gain at which switching the LNA on (antenna replaced by a load) raises the noise floor by 6 dB or more (model).
    - **Impact:** More strong-signal headroom at no measurable NF cost.
    - **Sources:**
      - https://www.nooelec.com/store/downloads/dl/file/id/112/product/301/sawbird_noaa_datasheet_revision_1.pdf
      - https://www.rtl-sdr.com/rtl-sdr-blog-v4l-lite-now-available-for-purchase/
  12.
    - **Claim in stack:** 3.2 sled: HMC7992 + PE4302 ...; RF4 50 Ohm default.
    - **Finding:** PE4302 was discontinued (pSemi, 2016 group). PE4312 is In Production and 'pin-compatible upgraded version of the PE4302', 1-4000 MHz. The sled's HMC7992 is specified only from 100 MHz.
    - **Verdict:** corrected
    - **Action:** Specify a PE4312 module and check the chip marking. Sweep it 1 MHz-2 GHz at 0/15.5/31.5 dB. Park the sled on RF1. Treat HF (<100 MHz) work through the sled or RTL-B BENCH throw as unspecified until swept on the LiteVNA.
    - **Impact:** Removes an EOL part and a power-up state that failed unsafe.
    - **Sources:**
      - https://psemi.com/?p=11471
      - https://www.psemi.com/products/digital-step-attenuators/pe4312
      - https://www.farnell.com/datasheets/2283884.pdf
  13.
    - **Claim in stack:** 2.3 HF+ switch: 2x Omron G6K-2F-RF 5 V, GBP 43-52 for two (RS UK), not verified.
    - **Finding:** DigiKey lists G6K-2F-RF DC5 under 'Aratas (Formerly Omron Components)' at $25.06, so $50.12 for two. Electropages confirms the rebrand. Ownership and dates from omron.com could not be verified (HTTP 403).
    - **Verdict:** corrected
    - **Action:** Order by part number and accept either marking. Relay cost $50.12 (DigiKey). Measure isolation on the LiteVNA.
    - **Impact:** About -$7 to -$19 against the RS figure.
    - **Sources:**
      - https://www.digikey.com/en/products/result?keywords=G6K-2F-RF%20DC5
      - https://www.electropages.com/blog/2026/07/omron-electronic-components-rebrands-aratas
  14.
    - **Claim in stack:** 2.3 / 3.2 H1: $45-50, not verified (URL gave 404).
    - **Finding:** SKU 100811 at $49.95, Add to Cart, 2-year warranty, 120 mA.
    - **Verdict:** corrected
    - **Action:** Set the price to $49.95 at https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-h1.html.
    - **Impact:** Extended total at the top of its range.
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-h1.html
  15.
    - **Claim in stack:** 5.3 P5: an SMA port that tolerates DC, with 12.5 V up the coax in the Boni profile. BONI12V5 12.5 V ±0.25 V.
    - **Finding:** An SMA LNA (Uputronics max 5.5 V; SAWbird 'up to 12 V' and not long-term) could mate with P5. The Boni-Whip and its bias tee use BNC. Bonito specifies 12-15 V. At ±2.5% the 12.5 V setpoint reaches a low end of 12.19 V, so the margin is only about 0.2 V.
    - **Verdict:** new_risk
    - **Action:** Fit a BNC bulkhead on P5 (keyed against SMA). Keep DC-sense and add a 'Boni attached' confirmation. eFuse 7.87 kOhm. Optional: set the BONI rail to 13.0 V by ANY-OUT (1.4+6.4+3.2+1.6+0.4) for margin. Schedule the Boni bring-up after WiMo's 20.11.2026 date.
    - **Impact:** Prevents destroying a $50-70 LNA with one wrong plug.
    - **Sources:**
      - https://www.wimo.com/en/18067
      - https://bonito.net/boni-whip/
      - https://cdn.shopify.com/s/files/1/0835/7707/8094/files/HAB-FPA_Series.pdf?v=1729257808
  16.
    - **Claim in stack:** Stage 1 protection: low-capacitance RF TVS on biased P2/P3, static bleed on P1/P6.
    - **Finding:** P1 already has the Flamingo+'s RF ESD diode (vendor claim on the page). On P2 the Uputronics has its own limiter. On P3, the exposed input is the SAWbird+ GOES input at the helix feed, outside the case; a TVS at the panel does not protect it. Candidate parts checked: Infineon ESD103-B1-02ELS (15 V, 0.13 pF) and ESD101-B1-02ELS (5.5 V, 0.2 pF) are 'Not For New Designs'; Nexperia PESD5V0C1BSF is discontinued at DigiKey.
    - **Verdict:** corrected
    - **Action:** P6: shunt bleed chip inductor of about 470 nH with SRF above 300 MHz (loss about 0.02-0.08 dB at 64-260 MHz, model; verify on the LiteVNA). P1: an optional bleed of the same kind. P3: static bleed (shunt inductor) at the SAWbird+ GOES input at the helix feed, or a DC-grounded feed. Panel TVS on P2/P3 stays optional, criteria VRWM ≥5.5 V and C ≤0.3 pF; no part selected.
    - **Impact:** Puts protection where the vulnerable stage actually is.
    - **Sources:**
      - https://www.nooelec.com/store/flamingo-plus-fm.html
      - https://www.digikey.com/en/products/result?keywords=ESD103-B1-02ELS
      - https://www.digikey.com/en/products/result?keywords=ESD101-B1-02ELS
      - https://www.digikey.com/en/products/result?keywords=PESD5V0C1BSF
  17.
    - **Claim in stack:** Stage 1: Bullseye 25 MHz reference port 'leave unterminated or capped'.
    - **Finding:** The reference is a live 25 MHz output on an F connector. 25 MHz falls inside the HF+ (to 31 MHz) and V4L HF ranges. DC on that port is not published.
    - **Verdict:** new_risk
    - **Action:** Measure DC on the reference port. If it is 0 V, fit a 75 Ohm F terminator; otherwise fit a dust cap. Check the HF+ and V4L for 25 MHz spurs during QO-100 sessions.
    - **Impact:** Avoids a self-made HF spur.
    - **Sources:**
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
  18.
    - **Claim in stack:** 5.3 HRPT: SAWbird+ GOES at the helix feed, passband 1648-1728 MHz (LTE B3 uplink 1710-1785 MHz inside).
    - **Finding:** Model: input P1dB is about -17 dBm (OP1dB 20 - 38 + 1). A +23 dBm handset at 1 m (0 dBi) delivers about -14 dBm. At 0.5 m in an 8 dBi lobe it delivers about 0 dBm, the absolute maximum. At 5 m it delivers -20 to -28 dBm.
    - **Verdict:** new_risk
    - **Action:** HRPT procedure: phones at least 5 m away or in flight mode. labd flags a noise-floor jump of more than 10 dB on the L-band throw.
    - **Impact:** Low; avoids desense or damage.
    - **Sources:**
      - https://www.nooelec.com/store/downloads/dl/file/id/108/product/296/sawbird_goes_datasheet_revision_1.pdf
- **New risks:**
  - Bias-tee token gate on all GPIOs breaks V4L VHF/UHF input switching. Osmocom drives GPIO5, the upconverter switch, through rtlsdr_set_bias_tee_gpio(). Gate gpio==0 only.
  - TPS2596 FLT is silent during overcurrent or short-circuit current limiting; it flags only overtemperature, OVLO or an ILM short. A soft overload on the LNB or Boni rail is invisible without INA3221 or ILM readback.
  - TCBT-2R5G+ (200 mA) behind a TPS2553 set for 300 mA (262-342 mA) is unprotected. Use RILIM 162 kOhm on TCBT channels.
  - The QO-100 IF at 739.5 MHz sits in the EU optional SDL (738-758 MHz) and PMSE gap. The planned DVB-T/B28 check looked at the wrong services.
  - TPS259630DDAR is out of stock at the TI store (DigiKey shows 487). Buy early; TPS259631DDAR (auto-retry) is the fallback.
  - Boni-Whip: Bonito specifies 12-15 V, and a 12.5 V rail at ±2.5% leaves about 0.2 V margin. Current draw is unpublished, which matters for the 0.125 A eFuse floor. WiMo has no stock until 20.11.2026.
  - HMC7992 is specified only from 0.1 GHz, so HF bench routing through the sled or the RTL-B BENCH throw is unspecified. Off-state return loss is only about 7 dB at the low end.
  - Bullseye 25 MHz reference output can put a spur on the HF receivers.
  - No current RF TVS part is selected. The obvious low-capacitance parts (Infineon ESD101/ESD103) are Not For New Designs, and Nexperia PESD5V0C1BSF is discontinued at DigiKey.
  - The SAWbird+ GOES input at the helix feed has no static path and no limiter (Nooelec publishes none). It is the most exposed MMIC in the system.
  - SAWbird+ Barebones saves $5 but halves the NOAA warranty (1 year against 2).
  - Generic HMC7992 boards: no primary listing has been verified, and missing DC blocks on RFC or RF1-RF4 are likely. Prefer chips on the custom injector PCB.
  - Osmocom 2.0.3 builds SOVERSION 0. Rebuilding from 2.0.3 for the device requires keeping .so.2, or every librtlsdr2 consumer breaks.
- **Refuted findings:**
  1.
    - **Finding:** Stage 1: Uputronics ex-VAT world price is GBP 42.99, about $57.26 (and $49.27 for the 1090).
    - **Why:** The store publishes its own regional prices: EU EUR 52.95 ($59.52, taxes at checkout) and US $62.00 for the 440; EUR 44.95 / US $53.00 for the 1090. The GBP/1.2 conversion is not what the store charges.
  2.
    - **Finding:** Stage 2: keep $68.71 (VAT-inclusive) for a European buyer.
    - **Why:** The stack's stated convention is USD without import VAT. The EU storefront shows EUR 52.95 before checkout VAT, and the landed cost with 19-21% VAT is about $71-72 (model), not $68.71.
  3.
    - **Finding:** Stage 1: pin the driver to rtl-sdr-blog V1.4.0 or later.
    - **Why:** V1.4.0 is titled 'RTL-SDR-BLOG Windows Release V1.4.0'. The fork's librtlsdr also has the offset-tuning and EEPROM force_bt bias paths. Use osmocom (2.0.3 contains V4L support).
  4.
    - **Finding:** Stage 2: put the LAB_BIAS_OK gate inside rtlsdr_set_bias_tee_gpio(), 'which all three paths call'.
    - **Why:** The tuner code also calls that function for GPIO5 (V4/V4L HF/UHF switch). An unconditional gate breaks VHF/UHF tuning. The gate must be limited to gpio==0.
  5.
    - **Finding:** Stage 1: TPS25962x 13.8 V clamp as an option for the LNB rail.
    - **Why:** VOVC minimum is 12.97 V, below the 13.2 V rail, and the datasheet limits input to the clamp option. Use TPS25963x OVLO instead (stage 2 is right).
  6.
    - **Finding:** Stage 1: 'Wire FLT to MCP #3 in place of the nonexistent PG' as sufficient fault reporting.
    - **Why:** TPS2596 Table 3: overcurrent and short-circuit show 'FLT Asserted: No'. Current readback is required.
  7.
    - **Finding:** Stage 1: fit pull-ups on A/B (10k to 3.3 V) as an equal alternative.
    - **Why:** The HMC7992 power-up sequence forbids control inputs ahead of VDD, and D13 is built on pull-downs. Parking on RF1 is the safe fix.
  8.
    - **Finding:** Stage 2: RILM about 7.5 kOhm for 0.125 A on the Boni rail.
    - **Why:** The datasheet equation RILM = 903/(ILIM - 0.0112) gives 7.94 kOhm, above the 7869 Ohm maximum. 7.5 kOhm gives about 0.132 A. Use 7.87 kOhm (characterised at 0.113-0.139 A).
  9.
    - **Finding:** Stage 1: TPS7A47 θJA 30.5 °C/W 'confirmed'.
    - **Why:** Datasheet SBVS204G (revised May 2026) lists RθJA 32.5 °C/W for RGW-20.
  10.
    - **Finding:** Stage 1: 434 MHz unit at '15.92 dB at 429.97 MHz and 16.08 dB at 437.97 MHz'.
    - **Why:** The plot markers read 16.92 dB at 429.67 MHz and 16.08 dB at 437.67 MHz. The conclusion (do not buy) stands.
  11.
    - **Finding:** Stage 1: a low-capacitance RF TVS on P2/P3 protects the first-stage LNAs.
    - **Why:** On P3 the exposed MMIC is the SAWbird+ at the helix feed, outside the case, and a panel TVS does not reach it. P2's Uputronics already has a limiter. The candidate TVS parts checked are NFND or discontinued.
  12.
    - **Finding:** Stack C23: IF-penetration risk is DVB-T 734-742 MHz and LTE B28 uplink.
    - **Why:** In the EU (user region), B28-equivalent uplink is 703-733 MHz, below the IF. The 700 MHz band no longer carries DVB-T; 738-758 MHz is optional SDL/PMSE (EU 2016/687).
  13.
    - **Finding:** Stage 1: Aratas is 'Carlyle-owned, independent from 1 Oct 2026'.
    - **Why:** Not supported by anything reachable: omron.com returned 403, and Electropages states no ownership. Only the rebrand and DigiKey's Aratas listing are verified.
- **Corrected spec:** RF FRONT END v1.1 (all prices USD ex-VAT at 1 EUR = 1.1241 USD, 1 GBP = 1.3318 USD; verified 18 Oct 2026 unless marked as a model)
  
  **P1 VHF-137 (SMA, no DC)**
  Chain: [optional shunt chip inductor ~470 nH, SRF >300 MHz, static bleed; verify on LiteVNA] → Nooelec Flamingo+ FM v2 → SAWbird+ NOAA (inside, in the shielded RF compartment) → injector ch1 (bias enters at the SAWbird output) → C0G DC block → HMC7992-A RF2 → RFC (C0G) → RTL-A.
  - Flamingo+ FM v2, SKU 100813, $24.95: >60 dB average stopband; passband IL 0.5 dB typ / 1.2 dB max; +18 dBm max input; RF ESD diode on its input.
  - SAWbird+ NOAA cased, 100800, $49.95: 41 dB, NF 1.1 dB, 2.6 MHz 3 dB bandwidth, 170-180 mA, Pin ≤0 dBm, bias 3-5 V through the SMA output. Budget: Barebones 100799, $44.95 (1-year warranty).
  - RTL-A gain: default 5-10 dB, range 0-15 dB.
  
  **LNA bias channels ch1-ch4**
  Chain: LNA4V5 4.5 V → TPS2553DBVR-1 (latch-off, $1.06) → INA3221 shunt → 0.5 A choke on the injector PCB.
  - RILIM 88.7 kOhm 1% gives IOS 262-342 mA (model).
  - On a channel that uses a TCBT-2R5G+ (ch2 or ch4 only; $9.05 at qty 10+), RILIM is 162 kOhm, giving 144-192 mA (model).
  - EN from MCP #1, FAULT to MCP #3. labd resets a latch by toggling EN.
  - Current readback: 2x INA3221AIRGVR ($3.47) on I2C2 at 0x41/0x43. Shunts 0.2 Ohm on ch1-4 and Boni, 0.1 Ohm on LNB. Alarm at more than 20% over the bring-up baseline.
  - labd LNA budget stays ≤1.0 A.
  
  **P2 UHF (SMA, 4.5 V out on ch2 after DC-sense)**
  - Uputronics FPA 440 MHz CubeSAT, V3 enclosure 69x40x12 mm: 3.5-5.5 V, ~50 mA, ≥19 dB, NF 0.75 dB average, Skyworks limiter, HPF <100 MHz. Dead when unpowered. Not IP rated, so fit a rain cover.
  - Price: EU EUR 52.95 = $59.52 (taxes at checkout); US $62.00.
  - Route → HMC7992-A RF3. Never more than 5.5 V on P2 or P3.
  
  **P3 L-band (SMA, 4.5 V on ch3 at the 300 mA limit; no TCBT)**
  - SAWbird+ GOES 100792, $49.95 (Barebones 100791, $44.95): 38 dB, NF 1.2 dB, 120-160 mA, Pin ≤0 dBm. Add a static bleed at its helix-side input.
  - Alternatives: SAWbird+ H1 100811, $49.95, 120 mA. SAWbird+ iO 100788, $49.95 (Barebones 100787, $44.95), only after the egc-gate. RTL-SDR Blog L-band patch, 20 mA.
  - Route → HMC7992-B RF2.
  - HRPT procedure: phones at least 5 m away.
  
  **P4 LNB (F)**
  Chain: SW → LC → TPS7A4701 (ANY-OUT 6P4V1+3P2V+1P6V+0P4V+0P2V to GND = 13.2 V ±2.5%, 12.87-13.53 V; RGW θJA 32.5 °C/W, bonded to the plate) → TPS259630DDAR ($1.07; fallback TPS259631DDAR) → INA3221 shunt 0.1 Ohm → choke ≥1 A → F.
  - eFuse current limit: RILM 2.05 kOhm 1% (0.405-0.499 A). Final value = 903/(1.5-2 × measured I_LNB - 0.0112).
  - OVLO: 110 kOhm / 10.0 kOhm 0.5%, trip 13.91-14.77 V (model).
  - FLT to MCP #3 with a pull-up.
  - EN of the LDO and eFuse together from MCP #1 GPB0, only while RTL-B is on RF3.
  - No PG and no PTC.
  - Signal side: LNB DC block (C0G, ≥50 V) → 15 dB pad (20 dB if gain is over 60 dB or unknown) → HMC7992-B RF3.
  - Bullseye BE01 $29.95. Reference port: terminator only if it measures 0 V DC, otherwise a dust cap.
  
  **BONI rail and P5**
  - Rail: TPS7A4701 at 12.5 V (optional 13.0 V) → TPS259630DDAR with RILM 7.87 kOhm (0.113-0.139 A) and the same OVLO divider → INA3221 → Boni bias tee → G6K K1.
  - P5 becomes a BNC bulkhead, keyed against SMA LNAs. DC-sense plus a 'Boni attached' confirmation.
  - Boni-Whip: WiMo EUR 133.61 net / 159.00 incl. VAT, available 20.11.2026; supply 12-15 V.
  
  **P6 VHF2/AIS (SMA, no DC)**
  - Shunt bleed ~470 nH (verify) → G6K K2 → HF+.
  - HF+ switch: 2x G6K-2F-RF DC5 (Aratas / formerly Omron), $25.06 each = $50.12.
  
  **P8 WIDE/2 m (optional)**
  - Flamingo+ #2 → RTL-SDR Blog Wideband LNA V2 ($19.95, 3-5 V, 90 mA) → ch4 → HMC7992-A RF4.
  
  **Switches**
  - HMC7992LP3DE: $13.10 (DigiKey, 4,655 in stock). Prefer chips on the custom injector PCB; otherwise qualify one generic board first.
  - RF1 = 50 Ohm park on every switch (A=B=low through D13's 100k pull-downs).
  - C0G DC blocks on all five RF pins. 100 pF on A/B.
  - VDD on the same 3.3 V rail as the MCP23017s, or 1 kOhm series resistors in A/B.
  - Qualify isolation ≥30 dB conducted. Specified 0.1-6 GHz only.
  
  **DC blocks, loads and injectors**
  - BLK-89-S+ $20.26 (50 V DC, 0.10 dB typ at 100-1000 MHz).
  - ANNE-50+ $14.84 (1 W at 50 °C; never on a biased line).
  - ZSWA4-63DR+ ($307.32, 0 in stock) rejected.
  
  **Sled**
  - HMC7992 parked on RF1, PE4312 (In Production, pin-compatible with the PE4302), MCP23017 #2 at 0x21, ADS1115 at 0x48.
  - Sources ≤ -40 dBm on the BENCH throw, with the antenna throws loaded.
  - HF (<100 MHz) through the sled is unspecified until swept.
  
  **Software**
  - Osmocom-based librtlsdr: noble 2.0.1 plus 0204c9c and 65f0658, or 2.0.3 with SOVERSION 2.
  - Bias token gate only on gpio==0 in rtlsdr_set_bias_tee_gpio(); GPIO5 is never gated.
  - Never install the rtl-sdr-blog fork.
  - modprobe 'install dvb_usb_rtl28xxu /bin/false' plus update-initramfs.
  - labd calls rtlsdr_set_bias_tee(dev,0) on every open.
  - At intake, check the EEPROM: byte 7 bit 1 must be 1.
  
  **Cascade rule unchanged:** on VHF the filter goes first; on UHF and L-band the LNA goes first at the antenna.
- **Bench tests:**
  - HMC7992 power-up (each switch): boot with labd stopped. A/B must read <0.3 V. Connect the tinySA at -40 dBm through a 30 dB pad to each throw in turn: only the RF1 load path may be connected, and no antenna throw may show the tone.
  - HMC7992 qualification on the LiteVNA, 100 MHz-2 GHz: IL ≤1.2 dB at 137/437/740/1700 MHz; isolation ≥30 dB on every throw pair. With the V4L tee forced on in a test build, confirm 0 V DC on RF1-RF4 (RFC block works).
  - V4L DC at boot: multimeter or scope on each V4L SMA from power-on through labd start, and after toggling 'offset tuning' in OpenWebRX+/SDRangel. Must read 0 V.
  - Token-patch regression: on the patched librtlsdr with no token, tune 137.9, 437.8, 1700 and 10 MHz. The level of a conducted noise source or beacon must match the unpatched build within 1 dB. Proves GPIO5 is not gated.
  - TPS2553 trip per channel (electronic load ramp at 4.5 V): 300 mA channels trip at 262-342 mA; TCBT channels (162 kOhm) at 144-192 mA. FAULT goes low on MCP #3, the latch holds, and an EN toggle resets it.
  - LNA current baselines via INA3221 at 4.5 V. Expected: SAWbird+ NOAA 170-180 mA, GOES 120-160 mA, H1 about 120 mA, Uputronics 440 about 50 mA, LNA V2 about 90 mA, L-band patch about 20 mA. Store them as labd alarm baselines.
  - LNB rail:
  - 13.2 V ±0.33 V at the F connector, battery 13.8-16.4 V.
  - Measure Bullseye current at 13.2 V, then set RILM.
  - Hard short on F: current limits near ILIM, then thermal shutdown and latch-off, FLT low.
  - Ramp eFuse IN on a bench supply: OVLO trips at 13.9-14.8 V and FLT asserts.
  - Soft overload just above ILIM: confirm FLT stays high and the INA3221 alarm fires.
  - Boni rail: setpoint under load, Boni-Whip current, and an eFuse limit of about 0.125 A. DC-sense must distinguish Boni (valid load), the 9:1 balun (short) and open. Confirm no SMA LNA can mate with the BNC P5.
  - Flamingo+ intake: S21 at 137.1/137.9 MHz ≤1.2 dB (expect ~0.5 dB); stopband 88-108 MHz ≥60 dB average.
  - RTL-A gain sweep on VHF-137, SAWbird+ on with a load at the input: choose the lowest gain at which the LNA raises the floor by ≥6 dB. Then repeat with the antenna at a strong-FM site.
  - QO-100 IF: noise rise 10-15 dB with LNB on and the 15/20 dB pad. A 3 dB pad step shows no intermod. Ingress scan 733-758 MHz with the LNB unpowered, then powered (EU SDL/PMSE).
  - Bullseye reference port: measure DC. Look for 25 MHz and harmonics on the HF+ and V4L with the port open, capped and terminated.
  - G6K-2F-RF pair on the LiteVNA: ≥35 dB isolation at 162-260 MHz and ≤0.3 dB IL from 10 kHz to 260 MHz; unpowered state = HF+ on 50 Ohm.
  - Static bleed inductors (P1, P6, helix feed): S21 loss ≤0.1 dB at 137 MHz / 64-260 MHz / 1.7 GHz, and no self-resonance in band.
  - PE4312 sled module: read the chip marking. Sweep 1 MHz-2 GHz at 0/15.5/31.5 dB. Also sweep the HMC7992 from 1 to 100 MHz if HF bench work will route through it.
  - Uputronics 440 on ch2: gain and current at 4.5 V. Confirm UHF reception is lost with ch2 off (no pass-through); labd must require ch2 on for UHF profiles.
- **Confidence:** medium

