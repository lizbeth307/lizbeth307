# Antennas: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_6b9836f8-796`_

- **Component:** Antennas and cabling (137 MHz, 145 MHz, 435 MHz, 1.7 GHz HRPT, 2.2 GHz S-band, QO-100 10.489 GHz) for the Q6A + LimeSDR Micro + RTL-SDR handheld
- **Current pick assessment:** The v3 antenna list is a good fit for a portable, receive-only station. Six points need fixing or updating. (1) The RTL-SDR Blog V4 is end-of-life. The RTL-SDR Blog buy page (Oct 2026) says "with the V4 EOL" and now sells the V4L (Lite) as dongle-only for $37.95; a kit is promised "in 2-3 months". Buy the multipurpose dipole kit on its own for $17.95 (in stock) to keep the 137 MHz V-dipole. (2) The WB2HOL 2 m Yagi and the 70 cm Yagi can be merged into one dual-band handheld. Because the station never transmits, no duplexer is needed: run two coax leads, the 2 m half to the RTL-SDR and the 70 cm half to the LimeSDR. (3) I found no good commercial 1.7 GHz RHCP helix. The commercial options are either the wrong band, low gain (4 dBic conical) or Iridium-only, and the RTL-SDR Blog L-band patch is explicitly not for HRPT. So the DIY 11-turn helix is the right choice. Put a SAW-filtered LNA (Nooelec SAWbird GOES or SAWbird+ GOES) directly at the feed. (4) The Bullseye TCXO LNB is still sold in Oct 2026: $29.95 at the RTL-SDR store with 70-100 in stock, free economy shipping from China to non-EU countries such as Ukraine. A 35 cm camping dish is the practical minimum. HB9RYZ ran a complete portable QO-100 station on a 35 cm Megasat dish, but vendors recommend 40 cm minimum and 60 cm. The stack's '13 V only' LNB supply covers just the vertical-polarisation narrowband transponder. The wideband/DATV downlink is horizontal and needs 18 V or rotating the LNB 90 degrees. (5) The Discovery Dish is in stock and is a real upgrade, not a necessity. Crowd Supply lists the dish at $149 plus feeds at $125 each, shipped free worldwide; Mouser lists the dish at $129 and the L-band feed at $115.50. Its feed has the LNA and SAW filters built in, so it replaces the separate L-band LNA/SAW. It also adds S-band with a $125 feed. (6) On cabling: keep MHF4 pigtails at 15 cm or less. Use LMR-200/240-class coax for anything above 1 GHz that runs before an LNA, and plain 75-ohm RG6 for the LNB IF. Also note that NOAA-15/18/19 were decommissioned in 2025, so the HRPT targets are now Meteor-M N2-3/N2-4, Metop-B/C and FengYun-3.
- **Alternatives:**
  1.
    - **Name:** RTL-SDR Blog multipurpose dipole kit used as a 137 MHz V-dipole (current pick)
    - **Key specs:** Dipole base with 60 cm RG174, 2x 23 cm-1 m and 2x 5-13 cm telescopic elements, 3 m RG174 extension, flexible tripod and suction-cup mounts. For 137 MHz set each arm to about 53.4 cm, open them to about 120 degrees, mount horizontally and point it north-south. Linear polarisation: about 3 dB loss on a circularly polarised satellite, but about 20 dB rejection of vertically polarised terrestrial QRM.
    - **Price:** $17.95 alone (RTL-SDR Blog store, China warehouse, in stock, Oct 2026)
    - **Availability:** In stock; free economy shipping worldwide outside the US/EU (2-4 weeks). The V4 dongle+kit bundle is gone (V4 is EOL); the V4L kit is promised later.
    - **Pros:** Packs flat. Doubles as a general-purpose dipole for 145/435 MHz testing. Proven on Meteor LRPT.
    - **Cons:** About 3 dB polarisation loss. Low gain near the horizon. The thin RG174 adds about 1 dB at 137 MHz over 3 m (acceptable).
    - **Q6a compatibility:** Connects to the RTL-SDR V4/V4L SMA input. Not the LimeSDR Micro, whose RX ports are specified only from 0.3 GHz.
    - **Sources:**
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://www.rtl-sdr.com/DIPOLE
      - https://www.rtl-sdr.com/simple-noaameteor-weather-satellite-antenna-137-mhz-v-dipole/
  2.
    - **Name:** QFH (quadrifilar helix) 137 MHz, DIY
    - **Key specs:** Circularly polarised and omnidirectional, no pointing needed. Roughly 1 m tall in PVC/copper for 137 MHz (my estimate, not from a cited source). According to the V-dipole's designer, a home-built QFH typically loses about 1 dB to construction errors and rejects vertical terrestrial QRM by only about 3 dB.
    - **Price:** Unverified (DIY materials only; I could not check commercial QFH prices because the search budget ran out)
    - **Availability:** DIY
    - **Pros:** Steadier signal through the pass, which is often reported as better on Meteor M2-4.
    - **Cons:** Bulky, fragile and fussy to build. Weaker rejection of strong 137 MHz area QRM. Not palm-portable.
    - **Q6a compatibility:** RTL-SDR input; the same as the V-dipole.
    - **Sources:**
      - https://www.rtl-sdr.com/simple-noaameteor-weather-satellite-antenna-137-mhz-v-dipole/
  3.
    - **Name:** DIY 4-element handheld 137 MHz Yagi
    - **Key specs:** Reflector, driven dipole and 2 directors on a wooden boom with brass welding-rod elements and 3D-printed handles; the LNA and SDR can be mounted on the boom.
    - **Price:** Unverified (DIY, low cost)
    - **Availability:** DIY
    - **Pros:** Clearly stronger than a V-dipole or QFH. Especially useful for Meteor M2-3, whose signal is weak because of a partially deployed antenna.
    - **Cons:** Must be hand-pointed for the whole 10-15 minute pass. A third VHF antenna to carry.
    - **Q6a compatibility:** RTL-SDR input; the IMU pointing aid helps here.
    - **Sources:**
      - https://www.rtl-sdr.com/building-a-diy-portable-137-mhz-yagi-antenna-for-lrpt/
  4.
    - **Name:** WB2HOL 3-element tape-measure Yagi, 2 m (current pick)
    - **Key specs:** Reflector 41-3/8 in (105 cm), driven element 2x 17-3/4 in (45 cm) with a 1 in gap, director 35-1/8 in (89 cm), 1/2 in PVC boom. One builder with 19 mm tape got better SWR by extending the driven element from 451 mm to 468 mm.
    - **Price:** About $10-15 in materials (estimate)
    - **Availability:** DIY. The tape and PVC are available in any Ukrainian hardware store.
    - **Pros:** Elements fold flat, are almost unbreakable, and it is proven on ISS SSTV at 145.8 MHz.
    - **Cons:** 2 m only. Linear polarisation, so rotate it by hand to fight fading.
    - **Q6a compatibility:** RTL-SDR (145 MHz is below the LimeSDR Micro's specified 0.3 GHz RX range).
    - **Sources:**
      - https://www.w9rh.org/wp-content/uploads/2024/01/2m-tape-measure-yagi-instructions.pdf
      - https://hamradioprep.com/how-to-build-a-tape-measure-yagi-antenna/
      - https://nt1k.com/vhf-3el-tape-measure-yagi/
  5.
    - **Name:** N2SPI cheap 7-element 70 cm Yagi (WA5VJB electrical design) (current pick)
    - **Key specs:** 76 cm (30 in) foam-board or wood boom, #8 AWG aluminium elements. Reflector 13-3/8 in (34 cm), folded dipole 13 in (33 cm), D1 12-3/8 in, D2 and D3 12 in, D4 11 in. No-solder coax connection; RG58 BNC jumper.
    - **Price:** About $10 in materials (estimate)
    - **Availability:** DIY
    - **Pros:** Extremely light, so easy to hold through a whole CubeSat pass. Proven on FM LEO downlinks.
    - **Cons:** Single band. The foam board is not weatherproof.
    - **Q6a compatibility:** LimeSDR Micro RX (435 MHz is inside the 0.3-2.2 GHz RX-low range) or the RTL-SDR.
    - **Sources:**
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
      - https://wa5vjb.com/yagi-pdf/cheapyagi.pdf
  6.
    - **Name:** Elk Antennas 2M/440L5 dual-band log-periodic
    - **Key specs:** 5 elements; 8.7 dBi (2 m) and 9 dBi (70 cm); 61 cm (24 in) boom; 0.64 kg (1.4 lb); single feedline with no duplexer; UHF (SO-239) connector.
    - **Price:** $137.95 (Gigaparts, in stock); $137.95-170.95 on elkantennas.com depending on variant
    - **Availability:** US sellers only. Shipping and customs to Ukraine not verified.
    - **Pros:** One antenna and one cable for both bands. Breaks down easily. An NT1K comparison rates it about equal to the Arrow in use.
    - **Cons:** Expensive once US shipping is added. The SO-239 connector needs an adapter. One feed means only one band can be received at a time without a diplexer.
    - **Q6a compatibility:** A single coax to the LimeSDR (435 MHz) or the RTL-SDR (both bands); add a 2 m/70 cm diplexer to feed both SDRs at once.
    - **Sources:**
      - https://www.gigaparts.com/2m-440l5-dual-band-directional-yagi-antenna.html
      - https://elkantennas.com/
      - https://nt1k.com/antenna-reviews-arrow-satellite-ii-vs-elk-log-periodic/
  7.
    - **Name:** Arrow II 146/437-10BP (no duplexer) / -10WBP (with duplexer)
    - **Key specs:** Handheld crossed dual-band Yagi with arrow-shaft elements; boom splits in two. Element split is 3 (2 m) + 7 (70 cm) according to the model naming; I did not re-verify this in this run.
    - **Price:** 10BP: $156.95 / GBP 139.95. 10WBP: $224.95 / GBP 199.95 / EUR 229.61 incl. VAT (Moonraker; listing date not shown)
    - **Availability:** Moonraker UK/EU/US; I could not confirm stock (the EU page returned 403).
    - **Pros:** The classic proven satellite handheld. The 10BP's two separate feeds suit two SDRs well (145 MHz to the RTL, 435 MHz to the Lime) at the same time.
    - **Cons:** Most expensive option. Bulky assembled. The arrow shafts can break.
    - **Q6a compatibility:** Two coax leads to two SDRs. Receive-only, so the duplexer is not needed.
    - **Sources:**
      - https://moonrakeronline.com/us/arrow-ii-146-437-10bp-without-duplexer-handheld-portable-satellite-antenna
      - https://moonrakeronline.com/us/arrow-ii-146-437-10wbp-handheld-portable-satellite-antenna
      - https://moonrakeronline.com/eu/arrow-ii-146-437-10wbp-handheld-portable-satellite-antenna
  8.
    - **Name:** DIY carbon 'Arrow-style' dual-band Yagi (DO5TY)
    - **Key specs:** 2x 50 cm carbon rods (12 mm OD) as the boom, 3D-printed joints, 6 mm and 10 mm aluminium elements, 2 m and 70 cm Yagis crossed at 90 degrees, diplexer. Element dimensions are only given in images on the author's page.
    - **Price:** About EUR 20 (author's figure)
    - **Availability:** DIY. STL files on Thingiverse, tutorial at tysonpower.de.
    - **Pros:** Much lighter and cheaper than the Arrow. Two feeds possible.
    - **Cons:** Needs a 3D printer and careful build. No measured SWR or gain published.
    - **Q6a compatibility:** Same as the Arrow: two coax leads to the RTL-SDR and the LimeSDR.
    - **Sources:**
      - https://www.rtl-sdr.com/building-a-carbon-fibre-dual-band-yagi-antenna-for-amateur-radio-satellites-with-3d-printed-parts-for-20e/
      - https://tysonpower.de/blog/carbon-arrow-yagi-antenna
  9.
    - **Name:** DIY 11-turn RHCP helix for 1.7 GHz + Nooelec SAWbird(+) GOES at the feed (current pick, improved)
    - **Key specs:** Calculated, not taken from a source: wavelength 17.6 cm at 1700 MHz; circumference about 1 wavelength (coil diameter about 56 mm); pitch 0.25 wavelength (about 44 mm); 11 turns, about 48 cm axial length; ground plane at least 15-20 cm; 2-2.5 mm copper wire on a PVC former. Realistic gain about 12-14 dBic (the Kraus formula's ~16 dBic is optimistic); half-power beamwidth about 30 degrees, so hand-tracking is easy. SAWbird GOES: 1688 MHz centre, 80 MHz passband (covers 1698-1707 MHz), at least 20 dB gain, 3-5 V bias tee or micro-USB, about 30 mA. SAWbird+ GOES: higher gain and lower noise, about 180 mA.
    - **Price:** Helix about $10-15 in materials (estimate). SAWbird GOES $39.95; SAWbird+ GOES $44.95 (Nooelec).
    - **Availability:** DIY; Nooelec ships internationally (shipping to Ukraine not verified).
    - **Pros:** Best gain per kg for handheld HRPT. Wide beam is forgiving to point. A printable 'helicone' variant (t0nito, Thingiverse) has received HRPT by hand-tracking.
    - **Cons:** Polarisation sense must be right: a helix used directly needs RHCP, but a helix used as a dish feed must be LHCP. Bulky at 48 cm. Marginal for 2.2 GHz unless the circumference is designed for both bands.
    - **Q6a compatibility:** Use the LimeSDR RX (1.7 GHz is inside RX-low/wide) for Metop/FY AHRPT, which needs more than 3 MHz of bandwidth. Meteor HRPT also works on the RTL-SDR at 2.4 Msps. The Lime has no documented bias tee, so power the SAWbird from a 5 V rail (micro-USB) or an external bias tee.
    - **Sources:**
      - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-goes.html
      - https://www.rtl-sdr.com/saveitforparts-testing-a-3d-printable-satellite-antenna-for-noaa-meteor-and-other-polar-orbiting-l-band-satellites/
      - https://space.oscar.wmo.int/satellites/view/meteor_m_n2_4
  10.
    - **Name:** Commercial L-band helix/patch options (checked, rejected)
    - **Key specs:** RTL-SDR Blog active L-band patch: 1525-1660 MHz RHCP, $59.95. The vendor says it cannot be used for weak signals such as HRPT, and 1700 MHz is outside its band. Southwest Antennas 1005-007: RHCP conical helix, 1.7-2.7 GHz, only 4 dBic. Alaris HELI-A0109: 1160-1610 MHz. Maxtena M1621HCT: Iridium only, $234.95.
    - **Price:** $59.95 to more than $230
    - **Availability:** Various
    - **Pros:** Ready-made.
    - **Cons:** None has the gain and band for 1700 MHz HRPT, so DIY or a dish wins.
    - **Q6a compatibility:** n/a
    - **Sources:**
      - https://www.rtl-sdr.com/preorder-sale-active-l-band-1525-1660-inmarsat-and-iridium-patch-back-in-stock-for-44-95/
      - https://everythingrf.com/products/all-antennas/southwest-antennas/741-685-1005-007
      - https://antennas.alaris.tech/product/1461
  11.
    - **Name:** KrakenRF Discovery Dish 70 cm + L-band feed (+ optional S-band feed)
    - **Key specs:** 70 cm dish in 3 aluminium petals, under 1 kg design target, pole mount. L-band feed: linear dipole, 2x Qorvo QPL9547 LNAs + 2x SAW filters at 1680 MHz with 69 MHz bandwidth, 5 V bias tee, waterproof, comes with 6 m LMR200/240-equivalent coax. S-band feed 2.2-2.3 GHz. Calculated gain about 19 dBi at 1.7 GHz (about 16 dBic-equivalent after 3 dB linear-vs-circular loss); about 17.6 degree beamwidth.
    - **Price:** Crowd Supply: dish $149 + L-band feed $125 + S-band feed $125, free worldwide shipping, all in stock. Mouser: dish $129 (363 in stock) + L-band feed $115.50 (was on backorder to Aug/Sep 2026); S-band feed about $113 / EUR 103.58.
    - **Availability:** In stock (Crowd Supply, Oct 2026). Shipping to Ukraine not verified.
    - **Pros:** Roughly 3+ dB more than the helix. The LNA+SAW is built in, which removes the separate L-band LNA/filter. One reflector covers L-band and S-band by swapping feeds. Light for its size.
    - **Cons:** $244-274 for L-band only, and about $370-400 with S-band. Narrow beam is hard to hand-track, so it practically needs a tripod or the (coming) Discovery Drive rotator. Linear feed means 3 dB loss and polarisation fading. Wind loading. Not designed for 10 GHz (surface accuracy unpublished).
    - **Q6a compatibility:** 6 m coax to the LimeSDR RX. Needs a 5 V bias tee, which the Lime does not have, so use an external bias tee from the device's 5 V buck.
    - **Sources:**
      - https://www.crowdsupply.com/krakenrf/discovery-dish
      - https://www.mouser.com/en/ProductDetail/KrakenRF/DISCOVERY-L-BAND-FEED-01?qs=mELouGlnn3dq1NMxJJwRIA%3D%3D
      - https://www.mouser.com/en/new/krakenrf/krakenrf-discovery-dish-accessories/
      - https://k6thebaldgeek.blogspot.com/2026/01/discovery-dish-mini-review.html
  12.
    - **Name:** Othernet Bullseye TCXO LNB (current pick)
    - **Key specs:** LO 9750/10600 MHz; input 10489-12750 MHz; IF 739-1950 MHz (low band), so the narrowband beacon lands at about 739.5 MHz. PLL with a 2 ppm TCXO; ±10 kHz at 23°C, ±30 kHz over −20 to 60°C. Noise figure 0.5 dB; gain 50-66 dB; separate F port with a 25 MHz reference output. Needs a 12-19 V bias tee; the RTL-SDR's 4.5 V is not enough.
    - **Price:** $29.95 (RTL-SDR store); EUR 32.64 (Passion Radio); GBP 31.99 (TechnoFix); EUR 30 (Astroradio)
    - **Availability:** RTL-SDR store showed 70-100 in stock. Amazon and SDRstore.eu were out of stock.
    - **Pros:** Cheapest stable LNB. The standard 40 mm collar fits any TV/camping dish.
    - **Cons:** ±10-30 kHz drift, so narrowband SSB/CW needs beacon-locked drift correction in software.
    - **Q6a compatibility:** IF at about 740 MHz goes to the LimeSDR RX or the RTL-SDR through a 13/18 V bias tee with DC blocking on the SDR side.
    - **Sources:**
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
      - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
      - https://shop.technofix.uk/bullseye-ultra-high-stability-single-lnb-for-qo-100-2ppm-tcxo
      - https://www.astroradio.com/en/p/qo-100-bullseye-tcxo-lnb/
  13.
    - **Name:** qro.cz QO-100 LNB (sold by WiMo): TCXO 0.2 ppm or 10 MHz external-reference version
    - **Key specs:** Built-in 25 MHz TCXO at 0.2 ppm: about ±1 kHz drift after a 5-minute warm-up, 3 kHz maximum. IF 739 MHz (QO-100), 432 or 618 MHz options. A version with an external 10 MHz reference input (fed over the coax) is available for a GPSDO. Polarisation switched by bias voltage: WiMo's page says 12 V horizontal, 15 V vertical, which is not the usual 13 V vertical / 18 V horizontal; I did not verify this.
    - **Price:** From EUR 65 incl. VAT (WiMo), plus EUR 54.62 shipping as listed
    - **Availability:** In stock, ships in 1-2 days (WiMo). Ordering direct from qro.cz (Czech Republic) may ship more cheaply to Ukraine (unverified).
    - **Pros:** About 10x more stable than the Bullseye, which makes narrowband SSB/CW listening practical without much software correction.
    - **Cons:** About twice the price, plus expensive shipping.
    - **Q6a compatibility:** Same IF and bias-tee arrangement as the Bullseye.
    - **Sources:**
      - https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz
  14.
    - **Name:** 35 cm camping dish (Opticum / Megasat / Schwaiger)
    - **Key specs:** Opticum 35 cm set: 35x38 cm, 1.4 kg, 40 mm LNB collar, carry case. Megasat Campingkoffer HD 35 cm (1800035): case, single LNB, 10 m coax. Calculated gain at 10.49 GHz about 29.5 dBi, versus about 34 dBi for 60 cm.
    - **Price:** Opticum EUR 49.90 (Kontrolsat, sold out); Megasat EUR 74.99 (Expert-Technomarkt) / EUR 79.66 (Kaufland); Schwaiger 35 cm EUR 69.90 (Kaufland)
    - **Availability:** EU retailers. I found no 35 cm camping dish listing on Prom.ua.
    - **Pros:** The most portable option. HB9RYZ ran a complete portable QO-100 station on a 35 cm Megasat dish.
    - **Cons:** Thin margin: Passion Radio recommends at least 40 cm and 60 cm. Too small for comfortable DATV.
    - **Q6a compatibility:** Holds the Bullseye; the IMU/compass aid helps aim it. From Kyiv QO-100 is at about 186° azimuth and 32° elevation (my calculation).
    - **Sources:**
      - https://www.kontrolsat.com/en/satellite-dishes/portable-satellite-dish-camping-set-035m-opticum-12114.html
      - https://www.expert-technomarkt.de/Sat-Antennen/Megasat-1800035-Campingkoffer-HD-35-cm-Sat-Spiegel.11830002778.html
      - https://www.kaufland.de/product/301843516/
      - https://www.hb9ryz.ch/downloads/qo-100-sat-portable-setup-hb9ryz.pdf
      - https://www.passion-radio.com/satellite-qo-100/camping-dish-749.html
  15.
    - **Name:** Ukrainian-market 55-60 cm offset TV dish
    - **Key specs:** CA-600 60 cm (Kharkiv 'Variant'), Inverto IDLB-ALCF62 60 cm, Schwaiger 714494 55x62 cm. All take a standard 40 mm LNB collar.
    - **Price:** CA-600 876 UAH; Inverto 1442 UAH (both out of stock when checked); Schwaiger 2550 UAH, in stock (Prom.ua). Roughly $21-62 at about 41 UAH/USD (rate assumed).
    - **Availability:** Prom.ua and Rozetka; used dishes on OLX for 400-600 UAH.
    - **Pros:** About 4.7 dB more than 35 cm. Very cheap. Bought locally, so no customs.
    - **Cons:** Steel, 3+ kg, not palm-portable. Better as a home or car-trunk dish.
    - **Q6a compatibility:** Same as the camping dish.
    - **Sources:**
      - https://prom.ua/ua/search?search_term=%D1%81%D1%83%D0%BF%D1%83%D1%82%D0%BD%D0%B8%D0%BA%D0%BE%D0%B2%D0%B0%20%D0%B0%D0%BD%D1%82%D0%B5%D0%BD%D0%B0%2060%20%D1%81%D0%BC
      - https://www.olx.ua/elektronika/tv-videotehnika/sputnikovoe-tv/kharkov/
  16.
    - **Name:** Coax: RG174 / RG316 / RG58 / LMR-200 / LMR-240
    - **Key specs:** Approximate loss per metre: LMR-240 0.10 at 150 MHz, 0.17 at 450 MHz, 0.33 at 1.5 GHz, 0.42 at 2.5 GHz. LMR-200 0.21 at 400 MHz, 0.54 at 2.4 GHz. RG58 0.38 at 400 MHz, 0.79 at 1 GHz, 1.28 at 2.4 GHz. RG316 about 0.55 at 400 MHz, 0.86-0.98 at 1 GHz, 1.29-1.46 at 2 GHz. RG174 0.48 at 400 MHz, 1.41 at 2.4 GHz. The 0.81 mm MHF4 pigtail cable is lossier still; I did not verify a figure.
    - **Price:** I could not verify AliExpress or Ukrainian prices (search budget exhausted). Estimate: SMA-SMA LMR-200/240-class 3 m jumpers about $8-20, RG316 jumpers $2-5, MHF4-to-SMA bulkhead pigtails $2-4 each.
    - **Availability:** AliExpress, Ukrainian radio shops
    - **Pros:** LMR-240 cuts loss by about 3x versus RG58 at L/S-band. RG316 is thin, flexible and fine for runs under 30 cm.
    - **Cons:** LMR-240 is stiff (6.1 mm). RG316 and RG174 are lossy above 1 GHz.
    - **Q6a compatibility:** Internal: MHF4 to SMA-female bulkheads on the case.
    - **Sources:**
      - https://www.raveon.com/data_radio_info/?p=1036
      - https://www.rfcafe.com/references/electrical/coax-chart.htm
      - https://www.fairviewmicrowave.com/content/dam/infinite-electronics/product-assets/fairview-microwave/product-datasheets/LMR-240-FT.pdf
      - https://uk.rs-online.com/web/p/coaxial-cable/2605590?gb=s
      - https://blog.koax24.de/en/tag/rg316-en/
- **Recommended:**
  - **Name:** Portable value kit: RTL-SDR Blog dipole kit as V-dipole + DIY crossed dual-band handheld (WB2HOL 3-el 2 m tape Yagi + N2SPI/WA5VJB 7-el 70 cm, or the DO5TY carbon design) with two separate feeds + DIY 11-turn RHCP helix with SAWbird+ GOES at the feed + Bullseye TCXO LNB on a 35-40 cm camping dish + LMR-240-class/RG6 cabling and SMA bulkheads. Optional premium upgrade: Discovery Dish with L-band and S-band feeds.
  - **Why:** This covers every target with gear that packs into a backpack, at roughly a third of the cost of commercial Arrow/Elk plus Discovery Dish, and almost everything can be bought locally in Ukraine or from China with free shipping. It cuts four antennas down to three to carry (V-dipole, dual-band Yagi, helix) plus the dish. Because the station is receive-only, the dual-band Yagi needs no duplexer: its two coax leads can feed the RTL-SDR (145 MHz) and the LimeSDR (435 MHz) at the same time. The helix's roughly 30 degree beam is easy to hand-track using the BNO085 pointing aid. Putting the SAWbird at the feed sets the noise figure there, so 3 m of LMR-240 afterwards (about 1 dB at 1.7 GHz) does not matter. The Bullseye is $29.95, in stock, and ships free from China, and HB9RYZ has shown a 35 cm dish works. Approximate cost: dipole kit $18; dual-band DIY $20-30; helix materials $15 plus SAWbird+ $45; Bullseye $30; 35 cm dish EUR 50-80; cables, adapters and two bias tees about $50-70 (estimate). Total about $240-300. Premium path: add the Discovery Dish ($149 dish + $125 L-band + $125 S-band from Crowd Supply). It adds roughly 3 dB on HRPT and makes S-band possible, and its built-in LNA/SAW makes the SAWbird optional, but it needs a tripod or rotator.
  - **Price:** About $240-300 total (core kit); Discovery Dish upgrade +$274-399
  - **Sources:**
    - https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
    - https://www.w9rh.org/wp-content/uploads/2024/01/2m-tape-measure-yagi-instructions.pdf
    - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
    - https://tysonpower.de/blog/carbon-arrow-yagi-antenna
    - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-goes.html
    - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
    - https://www.hb9ryz.ch/downloads/qo-100-sat-portable-setup-hb9ryz.pdf
    - https://www.crowdsupply.com/krakenrf/discovery-dish
- **Budget option:**
  - **Name:** Minimum-cost kit: V-dipole from the dipole kit (or DIY from rods) + WB2HOL tape Yagi and N2SPI foam-board 70 cm Yagi on one handle + DIY helix with SAWbird GOES + Bullseye on a cheap Ukrainian 55-60 cm (or used OLX) offset dish + RG58 and RG6 TV coax
  - **Why:** Every antenna except the LNB and LNA is DIY from hardware-store parts. The SAWbird GOES (lower-gain version, about 30 mA) can run from the RTL-SDR's 4.5 V bias tee or a 5 V rail. A local 60 cm steel dish costs about 876-2550 UAH (roughly $21-62), or less used on OLX, and gives about 4.7 dB more QO-100 margin than 35 cm, at the price of portability. RG58 is acceptable at 137-435 MHz in 3-5 m runs (about 1-2 dB) and after an LNA at L-band. RG6 is fine for the LNB IF because of the LNB's 50-66 dB gain. Approximate total: $18 + $20 + $15 + $40 + $30 + $25-60 + $25 in cables (estimate), about $175-210; using the dipole kit you already have and a used dish brings it to about $130-160.
  - **Price:** About $130-210
- **Risks:**
  - The RTL-SDR Blog V4 is EOL (admin comment on the RTL-SDR Blog buy page). The V4L dongle is $37.95 dongle-only, and its kit is promised 'in 2-3 months'. The dipole kit is sold separately at $17.95.
  - NOAA-15/18/19 were decommissioned in 2025, so the L-band HRPT investment depends on Meteor-M N2-3/N2-4 (N2-4 operational per WMO OSCAR, last updated 2026-01-23; modes and frequencies change with little notice), Metop-B/C and FengYun-3.
  - Polarisation sense: a helix used directly must be RHCP, while a helix or feed used in a dish must be LHCP, because the reflection reverses the sense. The Discovery Dish feed is linear, so expect about 3 dB loss and some fading.
  - Bullseye drift is ±10 kHz at 23°C and ±30 kHz over −20 to 60°C, so outdoor narrowband QO-100 needs beacon-lock correction in software. The qro.cz 0.2 ppm LNB (about ±1 kHz, EUR 65 + shipping) is the fix if that proves painful.
  - A 35 cm dish is the minimum workable size; vendors recommend at least 40 cm and 60 cm. Expect a weak beacon in rain or with poor pointing. QO-100's wideband/DATV downlink is horizontal: it needs 18 V (on standard LNBs) or the LNB rotated 90 degrees, not 13 V.
  - Never connect 13-18 V LNB power to the SAWbird or Discovery feeds (5 V maximum; SAWbird tolerates up to 12 V only briefly). Use separate, labelled bias-tee ports and DC blocks. The LimeSDR Micro RX ports are damaged above +10 dBm.
  - MHF4 connectors are fragile with few mating cycles. Terminate them once on SMA bulkheads and never hang antenna cables directly on the M.2 card.
  - Shipping and customs to Ukraine for Crowd Supply/Mouser (Discovery Dish), Arrow and Elk are not verified, and Ukraine's parcel duty threshold may have changed in 2025-26 (unverified). Imported US antennas can cost 1.3-1.6x list price once delivered.
  - Martial law in Ukraine: aiming Yagis and dishes at the sky in public, or near infrastructure, may attract attention from police or the military. Receive-only equipment is generally lawful, but check local restrictions and carry an explanation of the hobby (not legally verified).
  - I could not verify AliExpress or Ukrainian prices for coax, bias tees, QFH and grid dishes: the shared web-search budget ran out mid-research, so those figures are estimates.
- **Integration notes:**
  - Band-to-SDR mapping: the LimeSDR Micro M.2's RX ports X2 and X3 are specified at 0.3-2.2 GHz (RX-low), 0.7-2.6 GHz (RX-wide) and 3.3-3.8 GHz. So route 137 MHz and 145 MHz to the RTL-SDR, and 435 MHz, the about 740 MHz QO-100 IF, 1.7 GHz and 2.2 GHz to the Lime. The Lime's two RX channels share one RX synthesiser (LMS7002M architecture; my understanding, not checked in this run), so X2 and X3 act as a two-antenna selector inside one tuned bandwidth, not as two independent receivers.
  - Case bulkheads: 2x SMA-female wired to Lime X2 and X3 using MHF4 pigtails of 15 cm or less (Lime TX X1 left unused or capped), 1x SMA for the RTL-SDR (or use the dongle's own SMA), and optionally 1x for GNSS. Label them 'VHF', 'UHF/IF', 'L/S'.
  - Bias power: the LimeSDR Micro page documents no bias tee. Fit two external bias-tee boards fed from the 4S buck rails: (a) 5 V for the SAWbird or Discovery feed, (b) a 13/18 V switchable supply for the LNB, using a GPIO-controlled relay or two buck outputs. The SAWbird+ draws about 180 mA at 5 V and the SAWbird about 30 mA; I did not verify the Bullseye's current draw (typical LNBs draw 100-200 mA).
  - Cable choice: 137-145 MHz: RG58 or the kit's 3 m RG174 (under 1 dB). 435 MHz with no LNA: 3 m LMR-200/240 (about 0.5 dB) instead of RG58 (about 1.1 dB) or RG316 (about 1.7 dB). 1.7 and 2.2 GHz: LNA at the antenna, then 3-6 m of LMR-240-class (1-2.5 dB). The Discovery feed already comes with 6 m. QO-100: 5-10 m of 75-ohm RG6 with F connectors plus an F-female to SMA-male adapter; the 50/75 ohm mismatch can be ignored after 50-66 dB of LNB gain.
  - Connector standard: SMA at the device; BNC on VHF/UHF antennas for quick field swaps; F on the LNB. Carry an adapter set: SMA-M to BNC-F, SMA-M to F-F, and SMA-M to SO-239 only if you buy the Elk.
  - The 11-turn helix (about 48 cm × 6 cm) and the 70 cm Yagi share a 'handle' form factor. Mount the BNO085 on whichever antenna is in use, or on the dish's LNB arm, so the on-screen pointing aid reads true boresight; calibrate magnetic declination for Ukraine (about +7 to +9° E, unverified).
  - QO-100 pointing from Ukraine, calculated: Kyiv about 186° azimuth / 32° elevation; Lviv about 178° / 33°; Kharkiv about 194° / 32°. Rotate the LNB for polarisation skew (a few degrees) and peak on the 10489.5 MHz beacon (IF about 739.5 MHz).
  - Gain staging: with the LNA at the feed, leave out the SPF5189Z on L-band paths so the Lime is not overloaded. Use the SPF5189Z plus FM bandstop only on the VHF/UHF path if needed.
- **Double duty opportunities:**
  - One DIY crossed 2 m/70 cm handheld with two separate feeds replaces the WB2HOL and the 70 cm Yagi as two separate antennas, and lets the RTL-SDR (145.8 MHz ISS) and the LimeSDR (435-438 MHz CubeSats) run at the same time. No duplexer is needed because the station never transmits.
  - The Discovery Dish's L-band feed has two LNAs and two SAW filters built in, which removes the separate L-band LNA and 1.7 GHz SAW filter from the stack. The same reflector covers S-band with the $125 feed.
  - Design the helix with circumference about 0.9 wavelength at 1.7 GHz (about 50 mm coil diameter, about 38 mm pitch). It then stays in axial mode (0.75-1.33 circumference/wavelength) from 1.7 to about 2.25 GHz, giving one antenna for HRPT plus a fallback for S-band. Lower gain at 1.7 GHz; this is a design calculation, not a tested build.
  - The RTL-SDR dipole kit doubles as the 137 MHz V-dipole and as a general 145/435 MHz test and scan antenna, and its tripod and suction mounts can hold the GNSS or L-band patch.
  - Add an 18 V option to the 13 V LNB rail and the same supply serves both QO-100 narrowband (vertical) and wideband/DATV (horizontal); alternatively rotate the LNB 90 degrees.
  - The Bullseye's 25 MHz TCXO reference port could, in theory, act as a shared clock reference (for example, into the Lime's MHF4 clock input), but this is unverified and may not be supported.
  - The BNO085 pointing aid serves the Yagis, the helix and the dish; mount it in a removable 3D-printed clip that fits each antenna.
- **Confidence:** medium

## Форуми та досвід спільноти (`forums`)

_Run `wf_6b9836f8-796`_

- **Component:** Antennas and cabling: 137 MHz V-dipole/QFH, 145.8 MHz tape Yagi, 435 MHz cheap Yagi, dual-band handhelds (Arrow II / Elk / DIY crossed), 1.7 GHz RHCP helix + SAWbird, Discovery Dish, QO-100 Bullseye LNB and apertures, coax/MHF4/bias tees, for the Radxa Dragon Q6A + LimeSDR Micro M.2 + RTL-SDR handheld
- **Experiences:**
  1.
    - **Product:** 137 MHz V-dipole (Adam 9A4QV design, as used with the RTL-SDR Blog dipole kit)
    - **Source url:** https://www.rtl-sdr.com/simple-noaameteor-weather-satellite-antenna-137-mhz-v-dipole/
    - **Community:** RTL-SDR.com article comments
    - **What they built:** Home-built and kit V-dipoles for NOAA/Meteor APT/LRPT
    - **Problems:**
      - Prabakaran D: the terminal block is a weak point; the element weight shifts the angle, so it only suits field tests
      - Steve Cook expected a poor 50-ohm match
      - David: a bent dipole worked down to about 15 deg elevation with weak spots, while his QFH only worked above about 35 deg
    - **Fixes:**
      - Rusty: replace the terminal block with a Penn-Union ASRB-11-2-2 aluminium splice reducer block
      - Steve Cook: checked it with a VNA ('spot on 137MHz') and weatherproofed it with hot-melt glue; it survived a couple of years outdoors
    - **Outcome:** Works well for LRPT. Weak spots are mechanical, not electrical. One anecdote says the V-dipole beat a QFH at low elevation.
  2.
    - **Product:** V-dipole height/geometry for Meteor M2-4 (preprint + SatNOGS station 4330)
    - **Source url:** https://community.libre.space/t/mathematical-modeling-and-physical-optimization-of-v-dipole-antennas-for-vhf-imaging-satellite-reception/14844
    - **Community:** SatNOGS / Libre Space Community (May 30 2026)
    - **What they built:** uzzam modelled a V-dipole on an RTL-SDR V4; bali runs a similar V-dipole on SatNOGS station 4330
    - **Problems:**
      - bali's dipole mounted at about 55 cm worked well only on high passes
      - At h = 0.5 m the pattern is broad with low peak gain
    - **Fixes:**
      - Mount the V-dipole at about 1.1 m (more than a quarter wavelength) to get a single lobe peaking near 29.5 deg and coverage from about 8 deg
      - Arms about 52.6-53.7 cm (mean 53.2 cm; the community uses 53.4 cm)
      - Point it north-south
    - **Outcome:** Agreed guidance: height above ground matters as much as the angle. For handheld use, hold or mount it about 1 m above the ground, not at chest level near the device.
  3.
    - **Product:** RTL-SDR Blog multipurpose dipole kit (mechanics)
    - **Source url:** https://www.ebay.de/urw/RTL-SDR-Blog-Multipurpose-Dipole-Antenna-Kit-DE-SPJS-1110-1874-/product-reviews/9013164391?pgn=1
    - **Community:** eBay.de and desertcart buyer reviews (also https://www.desertcart.uy/products/56715887)
    - **What they built:** Used the kit for general VHF/UHF and satellite reception
    - **Problems:**
      - Telescopic tubes work loose
      - The last telescopic section came completely off on first extension
      - Tripod legs break, the suction cup loses grip, and the arm holders on the base get floppy
      - Not weatherproof: Akos and the vendor say it is for temporary outdoor use only
    - **Fixes:**
      - One reviewer simply bought spares
      - Others recommend the kit's FM broadcast filter in strong-FM areas
    - **Outcome:** Good value, but treat it as a consumable. Carry spare telescopic elements or replace them with fixed 53 cm rods for 137 MHz.
  4.
    - **Product:** SPF5189Z wideband LNA ahead of a V-dipole + RTL-SDR (SatNOGS)
    - **Source url:** https://community.libre.space/t/seem-to-have-similar-worse-performance-with-lna/5867
    - **Community:** SatNOGS / Libre Space Community (Mar-Apr 2020)
    - **What they built:** Indoor and loft VHF dipoles with SPF5189Z-type LNAs on RTL-SDR/Raspberry Pi stations
    - **Problems:**
      - The LNA made reception worse: no 5 V reached it, so it acted as an attenuator
      - BBC FM breakthrough and FM harmonics
      - LNA overload from broadcast stations
    - **Fixes:**
      - 0xCoto: the SPF5189Z board cannot take 5 V through RF_OUT; removing C4 lets it run on the RTL-SDR's 4.5 V bias tee
      - mat: put the RTL-SDR FM band-stop filter AFTER the LNA (before it, it hurt satellite reception; after it, it removed the FM harmonics)
      - Use RTL gain of about 10-20
      - Check for 5 V at the LNA and confirm the bias tee current passes through any filter
    - **Outcome:** The FM bleed was fixed, but no clear net benefit from the LNA was shown. Wideband LNAs at VHF are frequently counter-productive in high-RF areas.
  5.
    - **Product:** LNA placement at 137 MHz (Raspberry Pi SoapyServer station)
    - **Source url:** https://community.libre.space/t/observation-10391348-noaa-19-33591/12377?page=2
    - **Community:** SatNOGS / Libre Space Community (Oct 2024)
    - **What they built:** thanasispolitis: Pi-based 137 MHz station with an LNA
    - **Problems:**
      - Heavy interference: on the same RG58 the signal was clean with the LNA at the SDR but badly corrupted with the LNA at the antenna
      - PE0SAT listed likely sources: SMPS, solar inverters, Ethernet switches, FM broadcast and VHF pagers
    - **Fixes:**
      - Diagnose remotely with rtl_tcp or satdump_sdr_server and scan the band; no confirmed fix
    - **Outcome:** Unresolved root cause, but it shows a wideband LNA at the feed can pick up or amplify local noise.
  6.
    - **Product:** Antenna diversity for ISS SSTV (3-el Arrow Yagi + 137 MHz QFH)
    - **Source url:** https://community.libre.space/t/iss-sstv-ariss-sstv-experiment-october-8-14/12325
    - **Community:** SatNOGS / Libre Space Community (ARISS SSTV event, Oct)
    - **What they built:** XW0LP: a 3-element Arrow Yagi pointed straight up plus a homebrew 137 MHz QFH, joined by a Wilkinson combiner into an LNA and RTL v3
    - **Problems:**
      - Low-elevation passes
      - jomjom79: a nearby APRS transmitter (144.800 MHz in Region 1) overloaded the band
      - Valley terrain blocking
    - **Fixes:**
      - Combining the Yagi and the QFH helped at low elevation
      - Move to higher ground
    - **Outcome:** Excellent image on a pass peaking at 21 deg. Several others got images even with mobile whips.
  7.
    - **Product:** WB2HOL 2 m tape-measure Yagi
    - **Source url:** https://forums.radioreference.com/threads/my-take-on-the-wb2hol-tape-measure-yagi.308728
    - **Community:** RadioReference forums (page returned HTTP 503; content seen only in a search snippet) + hamradioprep build guide
    - **What they built:** Builds of the WB2HOL 3-element tape Yagi with a hairpin match
    - **Problems:**
      - Soldering the hairpin, coax and tape without melting the PVC was the hardest part; the hairpin insulation 'took a beating'
      - With 19 mm tape the SWR was off at the published 451 mm driven-element length
    - **Fixes:**
      - Extend the driven elements from 451 mm to 468 mm when using 19 mm tape (nanoVNA-tuned build, https://hamradioprep.com/how-to-build-a-tape-measure-yagi-antenna/)
      - Adjust the driven-element gap for SWR
    - **Outcome:** Builds work. Ukrainian 19 mm tapes will need the longer driven element.
  8.
    - **Product:** Dual-band (2 m + 70 cm) tape-measure Yagi
    - **Source url:** https://mailman.amsat.org/hyperkitty/list/amsat-bb@amsat.org/thread/HWXYUKXTHNXEZPB5DC5W3ZRP2XP5QU74
    - **Community:** AMSAT-BB mailing list (archive returned 403; content seen only in a search snippet)
    - **What they built:** Added a 70 cm section to a 2 m tape Yagi
    - **Problems:**
      - Poor 70 cm match
    - **Fixes:**
      - Reply: the 1-inch tape used for 2 m is too wide for 70 cm; use 1/2-inch tape for the 70 cm elements
    - **Outcome:** Merging bands on one tape-measure boom needs band-appropriate element widths.
  9.
    - **Product:** N2SPI foam-board 70 cm Yagi (WA5VJB electrical design)
    - **Source url:** https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
    - **Community:** AMSAT Journal Jul/Aug 2006 (author's own build article)
    - **What they built:** Handheld 440 MHz Yagi on a 30-inch foam-board boom with #8 AWG aluminium elements and a no-solder Euro terminal-strip coax joint
    - **Problems:**
      - Foam board is not weatherproof
      - Element lengths must be cut within +/-1/32 inch
    - **Fixes:**
      - Table 3 of the article: REF 13-3/8 in, folded DE 13 in, D1 12-3/8, D2 12, D3 12, D4 11 in. That is 6 elements (7 boom holes because the folded dipole uses two), not 7 as the findings state
    - **Outcome:** The author routinely worked FM LEOs (AO-27, SO-50, AO-51) with it, hand-held from horizon to horizon.
  10.
    - **Product:** WA5VJB 'Cheap Yagi' 70 cm (web copy of the 11-element version)
    - **Source url:** https://brainwagon.org/blog/wa5vjb-cheap-yagis-wood-boom/
    - **Community:** brainwagon blog (Mark VandeWettering)
    - **What they built:** Wood-boom WA5VJB Cheap Yagi for 70 cm with copper-bronze welding-rod elements
    - **Problems:**
      - The web version of the 11-element 70 cm table had director 4 at 11 in, between 12 in directors
    - **Fixes:**
      - Checked the scan of the original article: D4 should be 12 in
    - **Outcome:** Cross-check element tables against the original scan before cutting. A 2008 AMSAT-BB thread also traced a 70 cm cheap-Yagi SWR problem to the folded feedpoint (https://mail.amsat.org/archives/pipermail/amsat-bb/2008-June/011853.html).
  11.
    - **Product:** Arrow Satellite II vs Elk 2M/440L5 log-periodic
    - **Source url:** https://nt1k.com/antenna-reviews-arrow-satellite-ii-vs-elk-log-periodic/
    - **Community:** NT1K blog + reader comments
    - **What they built:** Owned and used both antennas for satellite work
    - **Problems:**
      - Arrow: unlabelled elements make assembly slow; arrows can break; tiring to hold; duplexer loss
      - Arrow: John Heger found the 90-degree band offset awkward for monitoring both bands at once on a tripod
      - Elk: the coax must leave at least 8 in at 90 deg to the boom or SWR suffers
      - Elk: screws tore the stock nylon bag
      - VK6MIK: overseas shipping is a large share of the price
    - **Fixes:**
      - Colour-code the Arrow elements with tape or paint
      - KJ4KKI and another reader run the Arrow without the duplexer (direct BNC per band)
      - Build a fixture for the Elk coax routing
      - Use a canvas bag
      - 3D-printed Elk handle
      - TI3IES built his own Arrow-style antenna from plans
    - **Outcome:** The reviewer called it a draw. For a receive-only station the Arrow's separate feeds suit two SDRs, while the Elk's single feed needs a diplexer.
  12.
    - **Product:** Arrow II durability / parts
    - **Source url:** https://mail.amsat.org/archives/pipermail/amsat-bb/2011-July/035645.html
    - **Community:** AMSAT-BB mailing list
    - **What they built:** Long-term Arrow II and 7x7 UHF Arrow owners
    - **Problems:**
      - A threaded insert went missing from an element after the antenna was loaned out
    - **Fixes:**
      - The manufacturer shipped a replacement element, inserts and threaded rod free; the insert was hammered back in
    - **Outcome:** Mechanically robust: one 7x7 UHF Arrow survived 5,000 truck miles. Small parts are the failure point, so carry spares.
  13.
    - **Product:** Elk 2M/440L5 in field use
    - **Source url:** https://forums.radioreference.com/threads/log-periodic-from-elk-rocks.36128/
    - **Community:** RadioReference forums (search snippet) + AMSAT-BB (https://mailman.amsat.org/hyperkitty/list/amsat-bb@amsat.org/thread/WDT7RXZU6VUTQDHKYIB2Y3T3SRJNTOJB)
    - **What they built:** Owners using the Elk for satellite passes
    - **Problems:**
      - Colour-coding tape came loose after heat in a vehicle
      - On AO-51 it worked lower passes but had a much tighter pointing tolerance, needing constant adjustment
      - Less 70 cm gain than an Arrow (AMSAT-BB)
    - **Fixes:**
      - None reported beyond re-marking the elements
    - **Outcome:** Rugged ('made like a tank') but less forgiving to hand-point.
  14.
    - **Product:** M1GEO dual-band satellite Yagi (2 m Moxon + 5-el 70 cm Yagi, LY3LP-derived)
    - **Source url:** https://george-smart.co.uk/?p=5294
    - **Community:** George Smart (M1GEO) blog
    - **What they built:** A 2 m Moxon rectangle passively coupled to a 70 cm 5-element Yagi, 3.2 mm aluminium welding wire, coax choke on the boom
    - **Problems:**
      - The original LY3LP-based build had SWR above 2:1
    - **Fixes:**
      - Modified the geometry with G8OCV; simulated SWR 1.07:1 at 145.825 MHz and 1.09:1 at 436.5 MHz (simulation, not bench measurement)
    - **Outcome:** A single-feed dual-band design, so receive-only use with two SDRs would need a diplexer. No field results were published.
  15.
    - **Product:** DO5TY (Tysonpower) carbon 'Arrow-style' crossed dual-band Yagi
    - **Source url:** https://tysonpower.de/blog/carbon-arrow-yagi-antenna
    - **Community:** tysonpower.de blog (comments closed) + RTL-SDR.com coverage (https://www.rtl-sdr.com/building-a-carbon-fibre-dual-band-yagi-antenna-for-amateur-radio-satellites-with-3d-printed-parts-for-20e/)
    - **What they built:** 2x 50 cm 12 mm carbon boom with 3D-printed joints, 6/10 mm aluminium elements, DK7ZB-style match using 50- and 75-ohm cable sections, diplexer
    - **Problems:**
      - No SWR or pattern data published
      - Element lengths given only in images
    - **Fixes:**
      - Use the STL files on Thingiverse and a nanoVNA to tune
    - **Outcome:** The author made several satellite contacts with a 5 W Baofeng. Cost about EUR 20.
  16.
    - **Product:** Arrow II + RTL-SDR v3 (transmit desense)
    - **Source url:** https://groups.google.com/g/skyroof/c/HBxIE54rZf4
    - **Community:** SkyRoof Google Group (Jul 2026)
    - **What they built:** Full-duplex satellite station with an RTL-SDR panadapter on an Arrow II
    - **Problems:**
      - The RTL-SDR goes deaf during the station's own transmissions
    - **Fixes:**
      - VE3NEA: sweep 100-500 MHz at low gain to find the overload source
      - The Nooelec ham filter bank gives about 50 dB (2 m) / 70 dB (70 cm) rejection but cannot fix 3rd-harmonic (435 MHz) pickup
    - **Outcome:** Unresolved. Not applicable to our receive-only station, but the same sweep method helps diagnose strong terrestrial signals.
  17.
    - **Product:** 3D-printed 1.7 GHz 'helicone' (t0nito design) with Nooelec GOES preamp
    - **Source url:** https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
    - **Community:** SatNOGS / Libre Space Community (Jan-Feb 2024)
    - **What they built:** pe2bz: PLA mesh cone reflector (134 mm base, 440 mm top, 88 mm high) around 1545/1700/2250 MHz RHCP helices; the original Facebook-group builders hand-tracked Meteor HRPT with the Nooelec GOES preamp and an RTL-SDR directly at the antenna
    - **Problems:**
      - PrusaSlicer did not auto-orient or add supports, which wasted prints
      - Wrong assembly order of the mesh holders
      - Sharp mesh edges
      - The holder blocked the antenna connector
      - Debate over whether a reflector flips RHCP to LHCP (herman: a ground-plane reflector keeps RHCP)
    - **Fixes:**
      - Heed slicer warnings and enable supports
      - Tape the mesh edges
      - Scale all dimensions to 75% for 2250 MHz
    - **Outcome:** Stronger and longer signals than a flat reflector. The 2250 MHz version received S-band on SatNOGS. Meteor HRPT hand-tracking success is reported second-hand.
  18.
    - **Product:** saveitforparts 3D-printable L-band helix (helicone)
    - **Source url:** https://www.rtl-sdr.com/saveitforparts-testing-a-3d-printable-satellite-antenna-for-noaa-meteor-and-other-polar-orbiting-l-band-satellites/
    - **Community:** RTL-SDR.com (video write-up; 0 comments)
    - **What they built:** Thingiverse helicone with a sheet-metal reflector and mesh, hand-held
    - **Problems:**
      - Several prints failed because the scaffold legs warped
    - **Fixes:**
      - Modified the model to add centre supports
    - **Outcome:** Received NOAA HRPT images by hand tracking, with a phone running RTL-SDR + SatDump.
  19.
    - **Product:** Helicone + SAWbird GOES + RTL-SDR V4 (Reddit r/amateursatellites)
    - **Source url:** https://r.datuan.dev/r/amateursatellites
    - **Community:** Reddit r/amateursatellites via a mirror (reddit.com blocked for fetch; the mirror later returned 502; content seen in search snippets)
    - **What they built:** 3D-printed helicone at 1.7 GHz, SAWbird GOES, RTL-SDR Blog V4, 5 m cable between the antenna and the SAWbird
    - **Problems:**
      - A tall spike at 1.7 GHz with smaller spikes around it when pointed at Meteor M2-3, and no images
      - The poster suspected the 5 m cable before the LNA, the soldering, or the mesh thickness
    - **Fixes:**
      - Community help (details not visible); follow-up post 'First HRPT Images, thank you to everyone that helped'
    - **Outcome:** HRPT images were eventually decoded but very noisy. The poster blamed indoor RFI while hand-tracking from a bedroom window. The exact fix is undocumented.
  20.
    - **Product:** 11-turn RHCP copper helix, no dish (Meti)
    - **Source url:** https://www.rtl-sdr.com/receiving-elektro-l3-lrit-weather-satellite-images-with-an-11-turn-helix-antenna-and-no-dish/
    - **Community:** RTL-SDR.com (0 comments)
    - **What they built:** 11-turn RHCP helix on a 17x17 cm ground plane
    - **Problems:**
      - Height above ground is critical
      - Cell-tower interference
      - Low SNR: 1.5 dB on Elektro-L3 at 13 deg elevation vs 5-6 dB for a 70 cm Discovery Dish
    - **Fixes:**
      - Rotate the helix
      - Bend the ground-plane corners
      - Choose the mounting height carefully
    - **Outcome:** Perfect LRIT images at 1.5 dB SNR. The same helix also receives polar L-band satellites such as Meteor M2-3. It is the closest documented match to our planned 11-turn helix.
  21.
    - **Product:** 5-turn L/S-band helix + AliExpress TQM3M9037 LNA (SatNOGS station 2830)
    - **Source url:** https://community.libre.space/t/station-2830-stockholm-l-and-s-band-new-helix-antenna/12046
    - **Community:** SatNOGS / Libre Space Community (Jul-Aug 2024)
    - **What they built:** SM0TGU: zenith-pointing 5-turn helix on a 3D-printed derekcz scaffold, LNA bias-tee'd from a HackRF
    - **Problems:**
      - SA2KNG found the AliExpress LNA's TP4056 Li-ion charger enters trickle mode if the switch is on at power-up, delivering only about 2.5 V
      - Strong adjacent signals on S-band
    - **Fixes:**
      - Replace the TP4056 with a linear regulator, or run the switch in the 'Off' (USB) position
      - Seal the joints and connectors with glue and vulcanising tape plus UV protection
      - SA2KNG: one LNA at each feedpoint and a cavity filter for S-band
    - **Outcome:** Much better signals than the previous antenna, comparable to other S-band helix stations.
  22.
    - **Product:** L/S-band helix stations, power and filtering (general)
    - **Source url:** https://community.libre.space/t/equipment-for-l-band-and-s-band-rx/11031
    - **Community:** SatNOGS / Libre Space Community (Nov 2023)
    - **What they built:** SA2KNG L- and S-band helices with a PGA-103+ preamp behind the reflector
    - **Problems:**
      - PE0SAT: 2.4 GHz Wi-Fi interference makes S-band difficult without a filter
      - SA2KNG: the RTL-SDR Blog L-band patch is 'not super strong'
    - **Fixes:**
      - Power the LNA from filtered SMPS 12 V and a 7805; a linear transformer made little difference
      - Use small eBay aluminium bias tees for RX
      - Use a 2170-2300 MHz cavity filter for S-band
    - **Outcome:** Advice only, no measurements. Relevant because the Q6A has on-board Wi-Fi 6.
  23.
    - **Product:** KrakenRF Discovery Dish (L-band/Inmarsat feed) vs patch vs helix
    - **Source url:** https://community.airframes.io/t/discovery-dish-rtlsdr-blog-l-band-acars/181
    - **Community:** Airframes community forum + thebaldgeek blog (https://k6thebaldgeek.blogspot.com/2026/01/discovery-dish-mini-review.html)
    - **What they built:** thebaldgeek compared a GPS puck, the RTL-SDR Blog patch, a 7-turn 3D-printed helix and the Discovery Dish on Inmarsat 4F3 ACARS
    - **Problems:**
      - The feed is linear, not LHCP
      - Significant wind loading
      - Questions over the SAW filter quality (Lothar: likely TaiSaw TA2247, about 3.1 dB insertion loss)
      - Shipping months late
      - A UK user: weakening 4F A4 signals; a 10-turn helix no better than the patch; 2 m RG316 no improvement
    - **Fixes:**
      - Linear feed accepted because of the high gain
      - Sturdy mount
      - For the UK user: check the helix LNA works and that the patch's coax isn't reused wrongly with the helix
    - **Outcome:** Ranking: puck < patch < helix < dish. The helix was judged the best value for size.
  24.
    - **Product:** Discovery Dish L-band feed (GOES)
    - **Source url:** https://forum.krakenrf.com/t/discovery-dish-l-band-lna-not-working/2068
    - **Community:** KrakenRF forum (Mar 2025, 2 pages)
    - **What they built:** WxSat/Bill: Discovery Dish + RTL-SDR V3 + 6 m feed coax + 20 ft KMR400 + 20 m USB repeater
    - **Problems:**
      - No lock, SNR 0.3-0.4 dB
      - Bias-tee draw 0.389 A (vs 0.150 A without the feed)
      - 1.536 Msps too narrow
      - Heavy in-band RFI from a local source
      - SatDump freezes
    - **Fixes:**
      - Feed replaced by KrakenRF
      - Use 2.4-2.56 Msps
      - Set skew
      - Remove the extension
      - Relocate the dish about 30 ft away from the house electronics; Carl notes Wyze IP cameras as known wideband sources
    - **Outcome:** 'Finally Working!!' after relocation. The local-RFI lesson applies equally to a handheld helix used near houses.
  25.
    - **Product:** SAWbird + RTL-SDR V4 on ARM Linux (Raspberry Pi 5 DragonOS / Ubuntu)
    - **Source url:** https://github.com/SatDump/SatDump/issues/696
    - **Community:** GitHub SatDump issues (Apr-Aug 2024)
    - **What they built:** Nooelec GOES dish + SAWbird + RTL-SDR Blog V4 on a Pi 5 and an Ubuntu server
    - **Problems:**
      - Perfect lock on Windows but no lock on Linux; gain changes had no effect; the bias tee was confirmed on
    - **Fixes:**
      - Compile the RTL-SDR Blog driver from source instead of the distro librtlsdr package
      - Also suggested: limit bandwidth to 2.56 Msps and use an active USB extension to move the dongle away from the Pi
    - **Outcome:** Fixed by the driver rebuild. This applies directly to Ubuntu 24.04 on the Q6A with a V4/V4L.
  26.
    - **Product:** SatDump bias-tee control over rtl_tcp
    - **Source url:** https://github.com/SatDump/SatDump/issues/261
    - **Community:** GitHub SatDump issues (Mar 2023)
    - **What they built:** Remote RTL-SDR via rtl_tcp feeding an LNA
    - **Problems:**
      - SatDump disabled the bias tee on connect, so the LNA was unpowered
    - **Fixes:**
      - Fixed by Aang23 on Mar 8 2023 (use a current SatDump); related issue #525: bias tee left on after closing satdump-ui
    - **Outcome:** Resolved in software. Verify LNA power (LED or 5 V) before each pass.
  27.
    - **Product:** LimeSDR Mini wideband front end (no filtering)
    - **Source url:** https://discourse.myriadrf.org/t/fm-images-all-over-hf-and-vhf-bands/7245
    - **Community:** MyriadRF Discourse (Jul 2021)
    - **What they built:** LimeSDR Mini + SDRangel on general antennas
    - **Problems:**
      - FM broadcast images at about 25, 58, 125 and 155 MHz
      - Harmonics from overload; absent on an RTL-SDR
    - **Fixes:**
      - Band-pass filter per band
      - FM band-stop (plus LTE band-stop)
      - Set the RX LPF just above the sample rate
      - Reduce gain to the strongest in-band signal
    - **Outcome:** No final confirmation. Consensus: the LMS7002M needs external band-pass filtering, which applies to the LimeSDR Micro as well.
  28.
    - **Product:** LimeSDR Mini v2.2 on 137 MHz NOAA vs SDRplay RSPdx
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-mini-v2-2-rx-interference-issues/8073
    - **Community:** MyriadRF Discourse (Oct 2023)
    - **What they built:** Peter M0LNB: the same roof discone fed both SDRs; the Lime was in a plastic case on hub power
    - **Problems:**
      - Wavy-line interference on Lime APT images; the RSPdx images were clean
    - **Fixes:**
      - Planned: extra screening cans and a 10 nF decoupling change; Lime staff were unaware of the issue
    - **Outcome:** Unresolved. It suggests the Lime M.2 inside a plastic 3D-printed case near a busy SoC needs shielding.
  29.
    - **Product:** LimeSDR U.FL pigtails
    - **Source url:** https://discourse.myriadrf.org/t/plug-in-u-fl-pigtails/2620
    - **Community:** MyriadRF Discourse (Apr 2018)
    - **What they built:** DL8WOW fitting SMA/U.FL pigtails to a LimeSDR
    - **Problems:**
      - 4 of 10 cheap pigtails out of tolerance
      - Forcing one ruptured the TX transformer T2 (Mini-Circuits TCM1-63AX+)
      - Cable-side contacts can get pinched shut
    - **Fixes:**
      - Seat with tweezers and press down with a pencil eraser until it clicks
      - Reopen pinched contacts gently with a pin
      - Mini-Circuits sent free T2 samples; replaced T2; Digikey pigtails fitted fine
    - **Outcome:** Repaired. Lesson: buy name-brand pigtails (Hirose, I-PEX) and mate them once.
  30.
    - **Product:** LimeSDR RX input failure
    - **Source url:** https://discourse.myriadrf.org/t/input-deaf-broken-repair-rx2-usage/1006
    - **Community:** MyriadRF Discourse (Mar-Apr 2017)
    - **What they built:** Ismas: LimeSDR with an outdoor antenna (EasyFix mod with T3 removed)
    - **Problems:**
      - RX1_L went about 35 dB deaf while he adjusted the antenna, suspected ESD or a hot-unplug short
    - **Fixes:**
      - Used the other RX ports; no repair confirmed
    - **Outcome:** Unresolved. It argues for ESD protection and DC blocks on outdoor antenna leads to the Lime.
  31.
    - **Product:** LimeSDR Mini as a QO-100 IF receiver (clock drift and shielding)
    - **Source url:** https://discourse.myriadrf.org/t/external-40mhz-tcxo-by-phil-crump/6934
    - **Community:** MyriadRF Discourse (Feb 2021)
    - **What they built:** HansKarel and Phil Crump: LimeSDR Mini for QO-100 narrowband
    - **Problems:**
      - The internal TCXO drifted as the unit warmed up
    - **Fixes:**
      - Phil Crump: external 40 MHz TCXO (R59 0R removed, fed at R62) inside a die-cast box, with no adverse effects as an NB IF receiver
      - Cheap 10 MHz OCXO plus multiplier tried (phase-noise caveat)
    - **Outcome:** Worked for Phil. Drift of the SDR's own clock adds to the LNB drift for narrowband QO-100.
  32.
    - **Product:** LimeNET Micro supplying a 25 MHz LNB reference
    - **Source url:** https://discourse.myriadrf.org/t/limenet-micro-clock-setting/13082
    - **Community:** MyriadRF Discourse (Mar-May 2026)
    - **What they built:** PE0AJF: QO-100 receiver with an LNB needing 25 MHz injected on the coax
    - **Problems:**
      - The Lime's 30.72 MHz GPS-disciplined clock cannot simply be set to 25 MHz
    - **Fixes:**
      - Zack: replace the oscillator, or generate 25 MHz with an FPGA PLL on a GPIO (gateware change, performance unknown)
    - **Outcome:** Unresolved. Sharing a clock between an LNB and a Lime is not plug-and-play.
  33.
    - **Product:** Non-dish QO-100 downlink: Kathrein flat SAT-TV panel + NORAD PLL LNB
    - **Source url:** https://www.dd1us.de
    - **Community:** DD1US portable QO-100 write-up (Oct 27 2019, PDF from dd1us.de)
    - **What they built:** An old Kathrein flat panel (probably BAS-65), cleaned and resealed, original converters removed, WR75 waveguide adapter, NORAD PLL LNB, on a small telescope tripod
    - **Problems:**
      - The panel was corroded
      - Margin uncertain
    - **Fixes:**
      - Disassembled, cleaned and resealed it; tripod adapter for elevation and skew
    - **Outcome:** On an Airspy Mini the CW beacon read S4-5 and the PSK beacon S3-4 above an S0 floor. This is the only documented non-dish QO-100 receive setup found.
  34.
    - **Product:** 35 cm Megasat camping dish QO-100 station
    - **Source url:** https://www.hb9ryz.ch/downloads/qo-100-sat-portable-setup-hb9ryz.pdf
    - **Community:** HB9RYZ station PDF (Mar 2020)
    - **What they built:** Megasat 35 cm dish, TCXO-modified LNB, patch uplink, Pluto, 10-15 W PA
    - **Problems:**
      - Station weighs 9-11 kg with the tripod
    - **Fixes:**
      - SDR Console beacon synchronisation, so no GPSDO is needed
    - **Outcome:** A working portable NB station on 35 cm. Moot now that the user has dropped dishes.
  35.
    - **Product:** QO-100 beacon lock vs LNB drift
    - **Source url:** https://forum.sdr-radio.com/viewtopic.php?p=7986
    - **Community:** SDR-Radio.com forum (Nov-Dec 2021)
    - **What they built:** LA6GH: SDR Console with QO-100 beacon lock
    - **Problems:**
      - In cold weather the LNB error put the beacon outside the lock window
    - **Fixes:**
      - Set the LNB offset from the drift measured at the temperature extremes so the beacon stays inside the span
      - Edit the downconverter definition
    - **Outcome:** The beacon was reached and lock became possible. Outdoor temperature swings matter for any TCXO LNB.
  36.
    - **Product:** Othernet Bullseye LNB calibration
    - **Source url:** https://github.com/g4eml/Bullseye-Calibrator
    - **Community:** GitHub (g4eml) + BATC forum (forum unreachable, HTTP 503; snippet: units typically within about 20 kHz)
    - **What they built:** Arduino calibrator that trims the Bullseye TCXO in about 200 Hz steps over the red F-port serial link (9600 baud, 0/+15 V); the LNB is powered via the green port
    - **Problems:**
      - Offset from the nominal 9750 MHz LO (spec: within 10 kHz)
      - Adjusting voids the warranty
    - **Fixes:**
      - Let it warm up 10 min, compare against the beacon, trim and SAVE (stored in the LNB)
    - **Outcome:** The author reports staying within 1 kHz at room temperature. The red port is also a control/serial port, not only a '25 MHz monitor' output.
  37.
    - **Product:** Bullseye LNB + 80 cm dish + PlutoSDR
    - **Source url:** https://forum.sdr-radio.com/viewtopic.php?p=4628
    - **Community:** SDR-Radio.com forum (Jan 2021)
    - **What they built:** DF6DBF: 80 cm offset dish, Bullseye, Pluto, SDR Console
    - **Problems:**
      - G4ELI's signal was weaker than expected (suspected wrong polarisation or alignment)
    - **Fixes:**
      - Check polarisation and alignment; calibrate SDR gain with a known test signal
    - **Outcome:** PSK beacon at -73 dBm on 80 cm. This gives a reference for how much a smaller, non-dish aperture will lose.
  38.
    - **Product:** HDMI monitor/display RFI near VHF/UHF receivers
    - **Source url:** https://groups.google.com/g/hamcoham/c/gmO-qqWNK2k
    - **Community:** hamcoham Google Group (search snippet) + HFUnderground
    - **What they built:** Ham stations suffering monitor noise
    - **Problems:**
      - The 1080p60 pixel clock of 148.5 MHz and its 3rd harmonic at 445.5 MHz leak from HDMI cables; even short HDMI cables radiate
    - **Fixes:**
      - Change refresh rate or resolution to move the harmonics
      - Loop the HDMI cable 4 times through a 60 mm ferrite near the port
      - Ferrite the display power lead
      - Separate the antenna and the display
    - **Outcome:** Reported effective. 148.5 MHz sits about 2.7 MHz from ISS 145.8 MHz, which matters for our HDMI-display decision.
  39.
    - **Product:** Receiving in Ukraine under martial law
    - **Source url:** https://www.rtl-sdr.com/russian-bomber-hf-activity-amateur-radio-banned-in-ukraine-sdr-hobbyist-warning-again/
    - **Community:** RTL-SDR.com (Feb 2022) + https://www.rtl-sdr.com/a-warning-to-ukraine-based-rtl-sdr-hobbyists/
    - **What they built:** n/a (advisory)
    - **Problems:**
      - All amateur transmitting ordered to cease
      - Public-facing receive feeds (ADS-B, WebSDR) may be seen as a threat
    - **Fixes:**
      - Stop public-facing receive feeds; consider taking antennas down (2022 advice)
    - **Outcome:** No documented rule on receive-only portable antennas. Receive-only but visible Yagis and helices remain a social and legal grey area.
- **Common problems:**
  1.
    - **Problem:** A wideband LNA (SPF5189Z-class) ahead of the SDR makes VHF reception worse: FM/pager overload, harmonics, or an unpowered LNA acting as an attenuator
    - **Affected products:** SPF5189Z boards, generic AliExpress LNAs, V-dipole/QFH stations on RTL-SDR; the LimeSDR is worse (no front-end filtering)
    - **Frequency:** common
    - **Known fix:** Verify about 4.5-5 V at the LNA (SPF5189Z: remove C4 so it can be bias-tee'd from the RTL's 4.5 V). Put the FM band-stop AFTER the LNA. Run RTL gain at about 10-20. Prefer band-filtered LNAs (SAW-filtered) over wideband ones. Skip the LNA at 137/145 MHz if the dipole is close to the SDR.
    - **Fix sources:**
      - https://community.libre.space/t/seem-to-have-similar-worse-performance-with-lna/5867
      - https://community.libre.space/t/observation-10391348-noaa-19-33591/12377?page=2
  2.
    - **Problem:** LMS7002M-based Lime boards show images, aliases and overload products because their RX path has almost no band filtering
    - **Affected products:** LimeSDR Mini/USB (documented); LimeSDR Micro uses the same RFIC (expected)
    - **Frequency:** common
    - **Known fix:** Fit a band-pass filter per band in front of the Lime: 435 MHz BPF, 1.7 GHz SAW (SAWbird), a cavity/SAW for 2.2 GHz. Add an FM band-stop. Set the RX LPF just above the sample rate. Reduce gain to the strongest in-band signal.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/fm-images-all-over-hf-and-vhf-bands/7245
  3.
    - **Problem:** Local RFI dominates L-band and VHF: SMPS, IP cameras, solar inverters, SBCs, USB 3 links, HDMI pixel-clock harmonics, Wi-Fi at S-band
    - **Affected products:** Every antenna in the kit, especially hand-tracked HRPT near buildings and a handheld with an HDMI screen
    - **Frequency:** common
    - **Known fix:** Move away from houses (the Discovery Dish user fixed it by moving 30 ft). Put ferrites on HDMI and power leads. Choose display timings whose harmonics avoid the bands. Shield the SDR in a metal can. Keep the LNA at the feed and the electronics behind the antenna. Filter S-band against 2.4 GHz Wi-Fi.
    - **Fix sources:**
      - https://forum.krakenrf.com/t/discovery-dish-l-band-lna-not-working/2068?page=2
      - https://groups.google.com/g/hamcoham/c/gmO-qqWNK2k
      - https://community.libre.space/t/equipment-for-l-band-and-s-band-rx/11031
  4.
    - **Problem:** RTL-SDR V4 (and likely V4L) silently fails to lock or decode on ARM Linux when using the distro librtlsdr
    - **Affected products:** RTL-SDR Blog V4 + SatDump on Raspberry Pi 5 / Ubuntu; directly relevant to Ubuntu 24.04 on the Q6A
    - **Frequency:** common
    - **Known fix:** Uninstall the distro rtl-sdr packages, build the rtl-sdr-blog driver from source, then rebuild or point SatDump/SoapyRTLSDR at it.
    - **Fix sources:**
      - https://github.com/SatDump/SatDump/issues/696
      - https://community.libre.space/t/satnogs-3649-rtl-sdr-blog-v4-issues/11942
  5.
    - **Problem:** Long coax between a 1.7 GHz antenna and its LNA, or a missing or unpowered LNA, means no HRPT lock
    - **Affected products:** Helicone/helix + SAWbird + RTL-SDR builds
    - **Frequency:** common
    - **Known fix:** Mount the SAWbird directly on the helix feed. Run only coax after the LNA. Confirm bias-tee power (LED or 5 V); SatDump once disabled the bias tee over rtl_tcp (fixed 2023). Use 2.4-2.56 Msps on an RTL for Meteor HRPT.
    - **Fix sources:**
      - https://r.datuan.dev/r/amateursatellites
      - https://github.com/SatDump/SatDump/issues/261
      - https://forum.krakenrf.com/t/discovery-dish-l-band-lna-not-working/2068
  6.
    - **Problem:** 3D-printed helix and helicone scaffolds fail to print or warp, and assembly is fiddly
    - **Affected products:** t0nito helicone, saveitforparts helix, derekcz scaffolds
    - **Frequency:** occasional
    - **Known fix:** Add centre supports to the model. Heed slicer warnings and enable supports. Assemble the mesh holders after the base ring. Tape the mesh edges. Leave access to the connector.
    - **Fix sources:**
      - https://www.rtl-sdr.com/saveitforparts-testing-a-3d-printable-satellite-antenna-for-noaa-meteor-and-other-polar-orbiting-l-band-satellites/
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
  7.
    - **Problem:** Helix performance depends on height, rotation and ground-plane shape, and builders get confused about polarisation sense
    - **Affected products:** 11-turn RHCP helices, helicones
    - **Frequency:** occasional
    - **Known fix:** Use RHCP for a direct helix (the flat or cone reflector of a helix keeps the sense; only a dish reflection flips it). Experiment with height. Rotate the helix. Bend the ground-plane corners.
    - **Fix sources:**
      - https://www.rtl-sdr.com/receiving-elektro-l3-lrit-weather-satellite-images-with-an-11-turn-helix-antenna-and-no-dish/
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
  8.
    - **Problem:** U.FL/MHF4 pigtail damage: out-of-tolerance cheap pigtails, ripped parts, few mating cycles
    - **Affected products:** LimeSDR family (documented on LimeSDR USB); the LimeSDR Micro uses MHF4
    - **Frequency:** occasional
    - **Known fix:** Buy name-brand pigtails. Seat them with tweezers and an eraser, pinch-and-twist to remove (or use the Hirose tool). Mate once onto case bulkheads. Never hang cables off the card.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/plug-in-u-fl-pigtails/2620
      - https://community.element14.com/technologies/test-and-measurement/f/forum/50334/rf-connectors-assortment/194481
  9.
    - **Problem:** Dual-band Yagi matching and mechanical issues: element width, single-feed designs with SWR above 2:1, unlabelled elements, feedline routing
    - **Affected products:** DIY dual-band tape Yagis, LY3LP/M1GEO designs, Arrow II, Elk 2M/440L5
    - **Frequency:** occasional
    - **Known fix:** Use 1/2-inch tape for 70 cm elements. Tune each band with a nanoVNA. Colour-code the elements. Route the Elk coax at least 8 in at 90 deg. Run the Arrow without the duplexer and with two coaxes for two SDRs.
    - **Fix sources:**
      - https://mailman.amsat.org/hyperkitty/list/amsat-bb@amsat.org/thread/HWXYUKXTHNXEZPB5DC5W3ZRP2XP5QU74
      - https://nt1k.com/antenna-reviews-arrow-satellite-ii-vs-elk-log-periodic/
      - https://george-smart.co.uk/?p=5294
  10.
    - **Problem:** Errors in published element tables
    - **Affected products:** WA5VJB 11-element 70 cm web copy (D4); the N2SPI design is 6 elements, not 7
    - **Frequency:** occasional
    - **Known fix:** Cross-check against the original scans: WA5VJB 11-el D4 = 12 in; N2SPI Table 3: REF 13-3/8, DE 13, D1 12-3/8, D2 12, D3 12, D4 11 in.
    - **Fix sources:**
      - https://brainwagon.org/blog/wa5vjb-cheap-yagis-wood-boom/
      - https://www.amsat.org/articles/n2spi/JulAug06AmsatJournal.pdf
  11.
    - **Problem:** LNB drift and offset push the QO-100 beacon out of the software lock window, especially in cold weather
    - **Affected products:** Bullseye and PLL LNBs; Lime TCXO drift adds to it
    - **Frequency:** occasional
    - **Known fix:** Set the LNB offset from the measured drift extremes. Use beacon lock (SDR Console style). Re-trim the Bullseye with the g4eml calibrator (about 200 Hz steps; voids the warranty). Put the SDR in a shielded box, or give the Lime an external TCXO.
    - **Fix sources:**
      - https://forum.sdr-radio.com/viewtopic.php?p=7986
      - https://github.com/g4eml/Bullseye-Calibrator
      - https://discourse.myriadrf.org/t/external-40mhz-tcxo-by-phil-crump/6934
  12.
    - **Problem:** Dipole-kit mechanical wear: telescopic sections come loose, tripod legs and suction cup fail, not weatherproof
    - **Affected products:** RTL-SDR Blog multipurpose dipole kit
    - **Frequency:** occasional
    - **Known fix:** Treat the telescopics as consumables, or replace them with fixed 53 cm rods for 137 MHz. Swap the terminal block for an aluminium splice block. Hot-melt-glue the joints.
    - **Fix sources:**
      - https://www.ebay.de/urw/RTL-SDR-Blog-Multipurpose-Dipole-Antenna-Kit-DE-SPJS-1110-1874-/product-reviews/9013164391?pgn=1
      - https://www.rtl-sdr.com/simple-noaameteor-weather-satellite-antenna-137-mhz-v-dipole/
  13.
    - **Problem:** V-dipole height and elevation trade-off: low mounting gives poor low-elevation passes
    - **Affected products:** 137 MHz V-dipole
    - **Frequency:** occasional
    - **Known fix:** Mount about 1-1.1 m above ground, arms about 53.2 cm, 120 deg, north-south axis.
    - **Fix sources:**
      - https://community.libre.space/t/mathematical-modeling-and-physical-optimization-of-v-dipole-antennas-for-vhf-imaging-satellite-reception/14844
  14.
    - **Problem:** Cheap AliExpress LNAs with built-in Li-ion chargers or odd bias paths deliver about 2.5 V
    - **Affected products:** TQM3M9037 'battery' LNA boards
    - **Frequency:** rare
    - **Known fix:** Buy the non-battery version, or replace the TP4056 with a linear regulator, or power it with the switch in the USB position.
    - **Fix sources:**
      - https://community.libre.space/t/station-2830-stockholm-l-and-s-band-new-helix-antenna/12046
  15.
    - **Problem:** Lost or broken small parts on the Arrow antenna
    - **Affected products:** Arrow II
    - **Frequency:** rare
    - **Known fix:** Carry spare inserts and threaded rod (Arrow shipped spares free in 2011).
    - **Fix sources:**
      - https://mail.amsat.org/archives/pipermail/amsat-bb/2011-July/035645.html
- **Unresolved problems:**
  1.
    - **Problem:** QO-100 reception WITHOUT a dish is barely documented
    - **Evidence:** Only DD1US's resealed Kathrein flat panel + PLL LNB (CW beacon S4-5 on an Airspy Mini, 2019) and an unmeasured vendor testimonial on passion-radio.com. No measured horn or patch-array SNR was found. The BATC forum, the main QO-100 community, returned HTTP 503 every time.
    - **Why it matters for us:** The user abandoned dishes. The Bullseye LNB alone (about 0 dBi probe) will not see the NB beacon, so the QO-100 goal hinges on a flat panel or horn that no community has characterised. Kathrein BAS panels are discontinued (used only). This must be resolved by the separate antenna component before buying.
  2.
    - **Problem:** Both the researcher's 'recommended' and 'budget' kits still include dishes (35 cm camping dish, Discovery Dish, a 60 cm Ukrainian dish)
    - **Evidence:** This conflicts with update (1). The only community-proven non-dish handheld HRPT antennas are the helicone (saveitforparts, t0nito) and the 11-turn helix (Meti, 1.5 dB SNR on Elektro-L3).
    - **Why it matters for us:** The L-band plan must stand on the helix alone (about 3-5 dB less than the 70 cm dish per Meti's comparison). Hand-tracked HRPT success rates on Meteor M2-4, Metop or FY-3 with an 11-turn helix are not documented; the Reddit helicone case decoded only noisy images.
  3.
    - **Problem:** No community reports exist of the Radxa Dragon Q6A (or any QCS6490 board) as an SDR host, or of its RF self-noise
    - **Evidence:** A Radxa forum search for SDR returned only Rock 4 / NIO 12L topics. Analogous Pi 4 reports show about 10 dB of noise-floor rise from the board and PSU, USB 3 emitting at 1.2-1.5 GHz, and HDMI 148.5 MHz pixel-clock leakage.
    - **Why it matters for us:** The antennas are hand-held about 1 m from a box containing a PCIe Gen3 SDR, a USB-C PD buck, Wi-Fi 6 and an HDMI display. Unmeasured self-noise at 137/145.8/435/1700 MHz could erase the helix's thin margin. Plan a noise-floor test with the Q6A on and off, Wi-Fi off, and the display on and off.
  4.
    - **Problem:** Whether the LimeSDR Micro tolerates DC on its RX ports, and what ESD protection it has, is undocumented
    - **Evidence:** The Lime has no bias tee. Nooelec warns that powering the SAWbird externally can trip SDR ESD diodes and suggests a DC block. A LimeSDR RX1_L went 35 dB deaf after antenna handling. No LimeSDR Micro field reports were found (the product is new and its MyriadRF search returned nothing for MHF4).
    - **Why it matters for us:** A micro-USB- or bias-tee-powered SAWbird, or a 13-18 V LNB injector, feeding the Lime could put DC on its MHF4 RX inputs. Always fit inline DC blocks and ESD protection on the Lime's antenna ports.
  5.
    - **Problem:** Using the Bullseye's red F port as a shared reference clock is unsupported
    - **Evidence:** RTL-SDR.com calls the red port a 25 MHz monitoring output, but g4eml uses it as a 9600-baud 0/+15 V serial calibration port. The LimeNET Micro thread found no easy way to make or consume 25 MHz. Lime Mini users fed 40 MHz (or 10 MHz with software changes).
    - **Why it matters for us:** The findings' 'shared 25 MHz clock into the Lime' idea has no supporting build and could inject serial or DC into the SDR. Drop it, or test it with a scope first.
  6.
    - **Problem:** The SAWbird+ GOES draws 180 mA nominal, exactly the RTL-SDR V4/V4L bias tee's 180 mA continuous limit
    - **Evidence:** Nooelec page (180 mA nominal); V4L datasheet ('up to 180 mA'). No community report was found of running at this limit.
    - **Why it matters for us:** If the helix SAWbird+ is fed from the RTL (the budget path), it may brown out or overheat the bias-tee switch. Use the 30 mA SAWbird GOES on the RTL, or feed the SAWbird+ from the 5 V buck through an external bias tee.
  7.
    - **Problem:** Crossed 2 m/70 cm Yagi interaction is unmeasured for the DIY designs
    - **Evidence:** DO5TY and other DIY Arrow clones publish no SWR or pattern data. The 2 m elements resonate near 3x145 = 435 MHz (harmonic coupling noted on worldwidedx for the Jetstream). Only WiMo claims 'nearly zero interaction' for its WY-3000 with separate feeds.
    - **Why it matters for us:** Merging the WB2HOL and N2SPI antennas onto one boom could detune the 70 cm half or distort its pattern. Model it in 4NEC2/MMANA or tune each band with a nanoVNA while fully assembled.
  8.
    - **Problem:** Quality of AliExpress coax (LMR-240 clones, RG316 jumpers), cheap bias tees and MHF4 pigtails is unmeasured
    - **Evidence:** Only vendor-sponsored counterfeit-LMR articles were found. One Amazon review of a generic 10 MHz-6 GHz bias tee measured -3 dB at 200 MHz, -7 dB at 100 MHz and -15 dB at 30 MHz. Cheap U.FL pigtails were out of tolerance and damaged a LimeSDR.
    - **Why it matters for us:** A generic bias tee in the 137/145 MHz path could cost several dB. Bad MHF4 pigtails can destroy the Lime's ports. Measure every cable and bias tee with a nanoVNA before use.
  9.
    - **Problem:** LimeSDR internal clock stability for narrowband QO-100 and LRPT on the Micro is unknown
    - **Evidence:** The LimeSDR Mini TCXO drifted on warm-up (MyriadRF 2021). No Micro data was found.
    - **Why it matters for us:** In a hot, fan-cooled handheld enclosure, SDR drift adds to the Bullseye's ±10-30 kHz. Software beacon lock may need more range.
  10.
    - **Problem:** Legal and practical status of pointing receive-only antennas in public under Ukrainian martial law is undocumented
    - **Evidence:** Only 2022 RTL-SDR.com advisories exist (transmitting banned; stop public receive feeds). The Ukrainian-language search found no current rule.
    - **Why it matters for us:** Hand-tracking Yagis and a 48 cm helix outdoors may draw police or SBU attention. Keep it receive-only with no streaming, and carry documentation.
  11.
    - **Problem:** Long-term field durability of DIY handheld antennas (foam-board N2SPI, tape Yagi hairpin, printed helix scaffolds) outdoors
    - **Evidence:** Builders report hairpin insulation damage, PVC melting during soldering, foam board not weatherproof, and PLA scaffolds warping. No multi-season reports were found.
    - **Why it matters for us:** Ukrainian winters, summer sun and humidity favour PETG/ASA prints, wood or PVC booms and sealed joints over PLA and foam.
- **Communities checked:**
  - RTL-SDR.com article comments (V-dipole, Meteor M2-4, Bullseye LNB, saveitforparts helicone, Elektro-L3 11-turn helix, dipole-kit review, Ukraine warnings)
  - SatNOGS / Libre Space Community (search.json + threads 11309, 12046, 11031, 14844, 5867, 12377, 12325, 7549, 1487, 14688, 14602)
  - MyriadRF / Lime Discourse (search.json + threads 7245, 8073, 2620, 1006, 6934, 13082)
  - KrakenRF forum (Discovery Dish L-band LNA thread, 2 pages)
  - Airframes community forum (Discovery Dish vs patch vs helix)
  - Crowd Supply Discovery Dish community-projects update
  - thebaldgeek blog (Discovery Dish mini review)
  - GitHub SatDump issues (web search pages: limesdr, bias tee; issues #696, #261)
  - GitHub g4eml/Bullseye-Calibrator
  - SDR-Radio.com forum (QO-100 beacon lock, beacon level)
  - SkyRoof Google Group (Arrow II + RTL-SDR)
  - NT1K blog (Arrow vs Elk, reader comments)
  - AMSAT Journal (N2SPI article PDF, full text read)
  - AMSAT-BB archives (pipermail via search; hyperkitty returned 403, snippets only)
  - brainwagon blog, George Smart M1GEO blog, tysonpower.de blog
  - HB9RYZ and DD1US QO-100 portable write-ups (PDF)
  - Nooelec product pages (SAWbird GOES / SAWbird+ GOES)
  - RTL-SDR Blog store (Bullseye page, V4L datasheet)
  - eBay.de / desertcart buyer reviews (dipole kit)
  - Radxa forum (search.json for SDR: nothing Q6A-related)
  - BATC forum and wiki (forum returned HTTP 503 every time; wiki page read; forum content only from search snippets)
  - RadioReference forums (HTTP 503; snippets only)
  - Reddit r/amateursatellites, r/RTLSDR (reddit.com blocked for fetch; mirror r.datuan.dev returned 502; only search snippets used)
  - hamcoham Google Group / HFUnderground (HDMI RFI, via search snippets)
  - Ukrainian-language web search on martial-law rules (no current official source found)
- **Recommendation impact:** Recommended changes to the antenna/cabling pick. (1) Drop every dish from both kits, per the user's update: the 35 cm camping dish, the 60 cm Ukrainian dish and the Discovery Dish (Discovery data is kept only as a benchmark). L-band HRPT then relies on the DIY 11-turn RHCP helix with the SAWbird mounted directly at the feed, which has community proof (saveitforparts, t0nito/pe2bz helicone, Meti's 11-turn helix). Expect a thin margin of about 1.5-3 dB SNR; Meti measured 1.5 dB on the helix vs 5-6 dB on the dish. Hand-track well away from houses. The Bullseye stays only if the separate QO-100 component finds a non-dish aperture: a resealed flat SAT panel like DD1US's, or a horn. There is no measured community data for this, so do not buy the LNB yet. (2) 137 MHz: keep the dipole kit as a V-dipole at about 1 m height, arms 53.2-53.4 cm, north-south. Expect to replace the telescopic sections, or use fixed rods. (3) 145.8 MHz ISS SSTV: AMSAT-UK and RTL-SDR.com say a simple dipole or ground plane is enough, so the dipole kit (arms reset for 145.8 MHz) can cover ISS. The WB2HOL becomes optional; if you build it with 19 mm tape, lengthen the driven element to about 468 mm. Note the 144.800 MHz APRS QRM in Region 1. (4) 435 MHz: N2SPI is a 6-element design, not 7; use its Table 3 lengths. If you merge bands, keep two separate feeds (Arrow 10BP style or a DIY crossed Yagi) and use 1/2-inch elements for 70 cm. Tune with both halves assembled, because interaction is unmeasured. The Elk is single-feed and needs a diplexer for two SDRs, and has a tighter pointing tolerance, so it is a poorer fit. (5) Filtering is mandatory in front of the LimeSDR because the LMS7002M has none: a 435 MHz BPF, the 1.7 GHz SAW (SAWbird) and a 2.2 GHz cavity/SAW filter (Wi-Fi 6 on the Q6A is a nearby S-band interferer). Do not put the wideband SPF5189Z/QPL9547 LNA in the Lime path. On the RTL VHF path, put the FM band-stop after the LNA, or skip the LNA. (6) Power: the SAWbird GOES (30 mA) can run from the RTL bias tee. The SAWbird+ (180 mA) sits at the RTL V4/V4L's 180 mA limit, so feed it from the 5 V buck through a quality bias tee. Put inline DC blocks and ESD protection on every Lime MHF4 RX lead. Drop the idea of sharing the Bullseye's 25 MHz clock with the Lime. (7) Cabling: use short, name-brand MHF4-to-SMA bulkhead pigtails, mated once. Keep the LNA at the feed and avoid cable before it (the Reddit 5 m failure). Measure the AliExpress LMR-240, RG316 and bias tees with a nanoVNA. (8) Software: on Ubuntu 24.04 ARM, build the rtl-sdr-blog driver from source (SatDump #696). (9) Cross-component flags: choose HDMI display timings whose pixel clock and harmonics avoid 137-138, 145.8, 435-438, about 740 and 1698-1707 MHz (1080p60's 148.5 MHz lands near ISS), and ferrite the HDMI lead. Run a noise-floor test with the Q6A, display and Wi-Fi each on and off. Shield the Lime in metal inside the printed case. Revised core cost without dishes: about $18 (dipole kit) + $20-30 (DIY dual-band) + $15 + $40-45 (helix + SAWbird) + $40-60 (filters, DC blocks, quality pigtails, bias tee) = about $135-170, plus the QO-100 aperture, which is still to be determined.

## Власні виправлення (`fixes`)

_Агент цього етапу ще працює (run `wf_6b9836f8-796`)._

