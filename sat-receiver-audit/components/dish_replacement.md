# Dish replacement: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Дослідження (`research`)

_Run `wf_5a66d65f-c3f`_

- **Component:** Antennas to replace the dishes: QO-100 at 10.489 GHz (LNB, IF around 740 MHz) and L-band HRPT at 1.70 GHz
- **Current pick assessment:** The plan that was dropped used a 35 cm camping dish with a Bullseye LNB, about 29.5 dBi at 10.49 GHz (calculated at 60% efficiency), plus an L-band dish or the 11-turn helix. The link budget below is anchored to field reports. It is an estimate, good to about ±3-4 dB, because no published report of QO-100 reception with a horn or lens was found.
  
  QO-100 narrowband transponder:
  - With a bare LNB (built-in feed, about 9-12 dBi estimated, about 40° beam), OK1DX copied the CW beacon. RigExpert TBR-AN-1 decoded FT8 at -12 to -14 dB SNR and says "Satellite dish – you do not need it!"
  - A 90 cm dish (about 37.5 dBi) gives a beacon C/N above 30 dB (BATC forum).
  - From these two points, beacon C/N0 is roughly 28 dB-Hz plus the antenna gain in dBi.
  
  Gain needed for each QO-100 target:
  - CW beacon, FT8 and CW: about 10 dBi.
  - SSB at beacon level, comfortable copy (10 dB in 2.7 kHz): about 17 dBi.
  - Typical SSB stations, 5-15 dB below the beacon: about 23-27 dBi.
  - Weak low-power (QRP) stations: 33 dBi or more.
  - Wideband DATV beacon (10491.5 MHz, 1.5 MS/s, DVB-S2 QPSK 4/5): a 71 cm dish gave MER 7.8 dB, which is 3.1 dB above threshold. Decoding therefore needs about 33 dBi or more.
  
  Estimated beacon C/N in 2.7 kHz for each antenna:
  - Camping dish: about 23 dB.
  - 20 dBi horn: about 14 dB.
  - 23 dBi horn: about 17 dB.
  - 30 cm W1GHZ metal-plate lens with horn (27.4 dBi, measured at 10 GHz): about 21 dB.
  
  L-band:
  - Metop AHRPT is QPSK at 2.333 Msym/s and needs at least 4 dB SNR in SatDump. Meteor HRPT runs at 665.4 ksym/s and needs only 0.5 dB.
  - EUMETSAT's reference receiving station is a 1.8 m dish with G/T 6 dB/K at 5° elevation.
  - An 11-turn helix with no dish gave about 7 dB average SNR on Meteor-M2-3. On Metop the same helix would give about 7 - 5.4 dB (symbol-rate penalty) = about 1.5-2 dB, assuming similar transmit power (EIRP, not verified). That is below threshold.
  - Metop therefore needs at least about 16 dBic, and about 18-19 dBic for reliable decodes. That is the aperture of a 60 cm dish (about 0.3 m²).
  
  Satellite status in October 2026:
  - FengYun-3 is no longer a 1.7 GHz target. FY-3C stopped HRPT outside China in May 2020 and ended all service on 28 Nov 2024. FY-3D/E/F/G/H "AHRPT" is X-band (7.79-7.86 GHz, 30-38.4 Msym/s, per the SatDump master pipelines).
  - NOAA OSPO (September 2026) lists Metop-C AHRPT as "No". Metop-B is the only live AHRPT source.
  
  Verdict: keep the 11-turn helix for Meteor-M HRPT and Elektro-L LRIT. Metop-B needs a dish-sized array of about 55-60 cm. Replace the 10 GHz dish with a horn, plus a lens if you want more gain.
- **Alternatives:**
  1.
    - **Name:** Bare TCXO/PLL LNB used alone, with no reflector (Bullseye BE01, Goobay 67269 PLL, or QRO.cz QO-100 LNB)
    - **Key specs:** Feed gain about 9-12 dBi (estimate) with a wide beam; RigExpert says aiming within ±20° is enough. Bullseye: input 10489-12750 MHz, LO 9750 MHz, TCXO ±10 kHz at 23°C and ±30 kHz from -20 to 60°C, NF 0.5 dB, gain 50-66 dB, 25 MHz reference output. Goobay PLL: ±300 kHz stability. QRO.cz: 25 MHz TCXO at 0.2 ppm or 10 MHz external reference, IF 739 MHz.
    - **Price:** Bullseye $29.95 (rtl-sdr.com store, 70 listed in stock); Goobay €5.90 excl. VAT (Passion Radio); QRO.cz from €65 incl. VAT (WiMo)
    - **Pros:** Proven without a dish: CW beacon copied (OK1DX) and FT8 decoded at -12 to -14 dB (RigExpert). Palm-sized. Its wide beam makes it a good first antenna for finding the satellite.
    - **Cons:** Beacon C/N is only about 3-6 dB in 2.7 kHz (estimate), so SSB is marginal and DATV is impossible. OK1DX found the signal does not pass through window glass. Plain LNBs drift (OK1DX saw about 50 kHz) and need beacon-lock correction.
    - **Sources:**
      - https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
      - http://ok1dx.cz/techinfo/qo100/qo100.html
      - https://www.passion-radio.com/satellite-qo-100/converter-432-936.html
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
      - https://passion-radio.com/lnb-pll/universal-goobay-1154.html
      - https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz
    - **Availability:** Bullseye: rtl-sdr.com store. Goobay: Passion Radio (EU). QRO.cz: WiMo (EU). Generic PLL LNBs are sold locally in Ukraine (no Ukrainian listing verified).
    - **Q6a compatibility:** IF at 739.5-749 MHz goes into a LimeSDR Micro RX (MHF4 to SMA pigtail). Fit a DC block and a 10-20 dB attenuator; OK1DX needed 20 dB. Supply 13 V for vertical polarisation (narrowband) and 18 V for horizontal (wideband).
  2.
    - **Name:** DIY optimum conical horn on the LNB throat (22 mm copper-pipe waveguide or QRO.cz POTY-adapter version)
    - **Key specs:** Calculated with λ = 28.6 mm, efficiency about 0.52 and slant length L = D²/(3λ): 20 dBi needs a 126 mm mouth, about 185 mm long, beam about 16°. 23 dBi needs 178 mm by 370 mm, beam about 11°. 25 dBi needs 224 mm by 590 mm. The throat is a 22 mm OD copper tube going into the LNB with its cap removed (TE11 cutoff about 8.8 GHz). The W1GHZ HDL_ANT program prints templates for optimum conical horns from 10 to 25 dB, and W1GHZ says built horns 'almost always' match predictions.
    - **Price:** About $5-20 for materials (copper, brass or aluminium sheet, or a PETG print covered in copper tape, plus 22 mm pipe), plus the LNB ($6-70)
    - **Pros:** Estimated beacon C/N 14-17 dB in 2.7 kHz. Beacon-level SSB is clean and FT8/CW are strong. The 20 dBi version is handheld; 23 dBi is light enough for a tripod. Either polarisation is selected by LNB supply voltage. Cheapest way to gain 10 dB.
    - **Cons:** No published QO-100 field report with a horn was found, so the numbers are scaled estimates. Stations more than 10 dB below the beacon are marginal, and DATV cannot be decoded. Needs metal cutting and soldering, and must point within ±5-8°.
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap2.pdf
      - http://www.w1ghz.org/software/HDL_ANT2_WinForms.zip
      - https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz
      - https://www.passion-radio.com/sat-accessory/ring-poty-999.html
    - **Availability:** All DIY. Copper/brass sheet and 22 mm copper pipe are plumbing and hardware-store items in Ukraine.
    - **Q6a compatibility:** Same as the bare LNB. Horn plus LNB weighs about 0.3-0.5 kg (estimate) and mounts on a light tripod or a hand grip. The QO-100 position is fixed, so no tracking is needed.
  3.
    - **Name:** Horn plus W1GHZ metal-plate lens (150-300 mm)
    - **Key specs:** W1GHZ measured at 10 GHz: 17.5 dBi horn alone; with a 150 mm lens, 20.9 dBi; with a 300 mm lens, 27.4 dBi (about 50% efficiency) at about 21 in (53 cm) focal distance. The lens is aluminium plates held in 3/4-inch styrofoam. The plates must be parallel to the E-field, so rotate the lens 90° for the horizontally polarised wideband transponder. Redesign it in HDL_ANT for 10.49 GHz.
    - **Price:** About $10-25 for aluminium sheet and styrofoam, plus horn and LNB
    - **Pros:** Comes within about 2 dB of the 35 cm camping dish (estimated beacon C/N about 21 dB; typical SSB readable). The lens is light and flat, packs flat, and is not a dish.
    - **Cons:** Assembly is about 60-70 cm long and needs a tripod. The beam is about 7°, so aiming must be careful (peak on the beacon). Works for one polarisation and a narrow band only. Plate spacing and curvature must be built accurately.
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap3.pdf
      - http://www.w1ghz.org/software/HDL_ANT2_WinForms.zip
    - **Availability:** DIY with local materials
    - **Q6a compatibility:** External antenna. Only IF coax runs to the handheld.
  4.
    - **Name:** Commercial WR90/WR75 standard-gain horn with SMA output
    - **Key specs:** WR90: 8.2-12.4 GHz, 20 dBi, beam about 17.5° (Pasternack PEWAN090-20ELSF). WR75: 9.84-15 GHz, 20 dBi (eBay). SMA-F end launch.
    - **Price:** $220.80 (WR75, eBay seller in Hangzhou); $228-356 (WR90, eBay); $1,520 (Pasternack)
    - **Pros:** Known, calibrated gain; robust; broadband.
    - **Cons:** The SMA output cannot feed a cheap TV LNB. It needs a separate 10 GHz LNA and mixer/LO with SMA input (cost not verified, far above $100). It costs 10-50 times a DIY horn for the same gain. AliExpress listings for 10 GHz horns could not be verified.
    - **Sources:**
      - https://www.pasternack.com/wr-90-waveguide-standard-gain-horn-antenna-20-dbi-sma-pewan090-20elsf-p.aspx
      - https://www.ebay.de/itm/317537757638
      - https://www.ebay.com/itm/397681373869
      - https://www.ebay.de/itm/314454124598
    - **Availability:** eBay (China), Pasternack (US). Shipping to Ukraine not verified.
    - **Q6a compatibility:** Only with an extra 10 GHz SMA downconverter. Not recommended.
  5.
    - **Name:** Selfsat H30D flat Ku-band panel with integrated LNB
    - **Key specs:** Specified 10.7-12.75 GHz, peak 33.7 dBi at 12.75 GHz, LO 9.75/10.6 GHz, H/V switching, 517 x 277 x 58 mm, 4.0-4.5 kg
    - **Price:** About €160 (PCComponentes PT listing)
    - **Pros:** The only non-dish shape with dish-class gain (about 31-33 dBi in band). In principle it could reach the DATV beacon threshold.
    - **Cons:** 10.489 GHz is below the specified band; gain and LNB-filter roll-off there are unknown. The LNB is not TCXO-stabilised, so it drifts. At 4+ kg it is not handheld. No QO-100 reports were found, so it is an unverified gamble.
    - **Sources:**
      - https://asset.conrad.com/media10/add/160267/c1/-/de/000943058DS01/tehnicni-podatki-943058-selfsat-h-30-d-sat-antena-brez-sprejemnika-stevilo-udelezencev-1.pdf
      - https://www.pccomponentes.pt/selfsat-h30d-antena-plana-exterior-lnb
    - **Availability:** EU retailers (Conrad, Kaufland, PCComponentes)
    - **Q6a compatibility:** F-connector IF output, so it is electrically the same as an LNB.
  6.
    - **Name:** Dielectric or 3D-printed lenses, Fresnel zone plates, Luneburg lenses
    - **Key specs:** A 3D-printed dielectric Fresnel zone plate at 10 GHz reached 18 dBi directivity (Loughborough, EuCAP 2016). PLA/PETG loss tangent at X-band varies widely with infill and orientation. W1GHZ notes most dielectrics are lossy at 10 GHz. Foil-ring zone plates have low efficiency and high sidelobes.
    - **Price:** About $5-30 for filament or foil
    - **Pros:** A zone plate is flat or foldable and very cheap.
    - **Cons:** Less efficient than a metal-plate lens. Dielectric loss is uncertain. No QO-100 reports found. A zone plate needs about 40-50 cm diameter to beat a 23 dBi horn (estimate).
    - **Sources:**
      - https://repository.lboro.ac.uk/articles/conference_contribution/3D_printed_dielectric_Fresnel_lens/9559433
      - https://setileague.org/articles/fresnel.htm
      - http://www.w1ghz.org/antbook/chap3.pdf
    - **Availability:** DIY
    - **Q6a compatibility:** In front of the LNB, same as the horn options.
  7.
    - **Name:** 10 GHz helix, PCB patch or slot arrays, phased arrays
    - **Key specs:** QO-100 downlinks are linearly polarised (narrowband vertical, wideband horizontal), so a helix loses 3 dB: a roughly 20-turn 10 GHz helix at about 14 dBic gives about 11 dBi effective (estimate). A Rogers PCB 8x8 patch array of about 22-24 dBi (estimate) needs an SMA-input LNA and downconverter. No hobby-priced Ku-band phased array is usable at 10.489 GHz.
    - **Price:** Helix about $5; PCB array not verified; phased array not available
    - **Pros:** None decisive for receive-only use.
    - **Cons:** No gain advantage over a horn, and more complexity. No commercial dish-free QO-100 receiver product was found.
    - **Sources:**
      - https://wiki.batc.org.uk/QO-100_WB_Bandplan
      - https://shop.amsat-uk.org/details/p3815740_17349465.aspx
    - **Availability:** n/a
    - **Q6a compatibility:** n/a
  8.
    - **Name:** Longer L-band helix (16-20 turns) or 3D-printed 1.7 GHz helicone (t0nito)
    - **Key specs:** Helix gain saturates: a helix about 7λ long (about 1.23 m at 1.7 GHz) gives only about 15 dBic, and Kraus's formula is too optimistic (SETI League, citing Emerson). 11 turns is about 12.5-13 dBic; 16-20 turns about 14-14.5 dBic at 70-88 cm long (estimate). The t0nito helicone is handheld and has received NOAA and Meteor HRPT hand-tracked.
    - **Price:** About $5-20 for copper wire, PVC or PETG, and aluminium plate
    - **Pros:** Natively RHCP, cheap, handheld. With the 11-turn helix, Meteor-M2-3 averaged about 7 dB SNR against 0.5 dB needed, and Elektro-L3 LRIT decoded at 13° elevation with no dish. A ground plane with bent-up edges added about 1.5 dB; height above ground and LTE shadowing matter.
    - **Cons:** Metop-B is marginal at best (estimated 3-4 dB SNR for 20 turns against 4 dB needed). Returns diminish past about 16 turns.
    - **Sources:**
      - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
      - https://www.qsl.net/seti/articles/helix2.htm
      - https://www.rtl-sdr.com/saveitforparts-testing-a-3d-printable-satellite-antenna-for-noaa-meteor-and-other-polar-orbiting-l-band-satellites/
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
      - https://www.rtl-sdr.com/receiving-elektro-l3-lrit-weather-satellite-images-with-an-11-turn-helix-antenna-and-no-dish/
    - **Availability:** DIY. STL files on Thingiverse (thing 6436342).
    - **Q6a compatibility:** SAW-filtered LNA at the feed, then into the LimeSDR. SatDump meteor_hrpt pipeline, 665.4 ksym/s.
  9.
    - **Name:** 2x2 array of 11-turn RHCP helices (four helices)
    - **Key specs:** Four helices at 12.5-13 dBic, +6 dB array gain, minus about 0.7-0.8 dB for a 4-way Wilkinson combiner (RF ONE PDM-00503-S4 spec: 0.7 dB loss, 0.5-3 GHz), gives about 18 dBic. Spacing about 25-30 cm (effective apertures just touching). Footprint about 55-60 cm square, depth about 50 cm, beam about 20°. Option B: two 2-helix sub-arrays into LimeSDR RX1/RX2, combined coherently in GNU Radio. A 2014 paper simulated a helical array reaching 22 dBi at 1700 MHz.
    - **Price:** About $30-60 materials for three more helices, ground plane, matching sections and coax; plus a combiner and SAW LNAs (prices not verified)
    - **Pros:** Estimated Metop-B SNR about 6-7 dB against 4 dB needed on medium and high passes; Meteor about 11-12 dB. Each helix still works alone. The helices unplug for transport. No dish.
    - **Cons:** Same aperture and bulk as a 60 cm dish, about 2-3 kg (estimate). Phase-matched feeding and impedance matching need a NanoVNA. Hand tracking needs a pan-tilt tripod. Low-elevation Metop passes are still lost.
    - **Sources:**
      - https://www.qsl.net/seti/articles/helix2.htm
      - https://www.amrita.edu/publication/design-of-axial-mode-helical-antenna-array-for-noaa-18-hrpt-reception-at-1700mhz/
      - https://www.everythingrf.com/products/power-dividers/rf-one-electronics/612-1911-pdm-00503-s4
      - https://blog.metislair.com/docs/Radio/L%20band%20weather%20satellite%20reception%20guide.html
    - **Availability:** DIY with local materials
    - **Q6a compatibility:** Uses the LimeSDR Micro's two coherent RX channels (RX1/RX2 from the LMS7002M). RX3/RX4 are analogue-baseband inputs on an FPC connector that need an accessory, not confirmed shipping.
  10.
    - **Name:** Dual-polarised 4G MIMO panel, 1700-2700 MHz (RNet 2x17 dB, 'Kvadrat' MIMO 17 dBi, Energy 2x15 dB), with 2-channel polarisation combining
    - **Key specs:** Two orthogonal linear ports go to LimeSDR RX1 and RX2. Combining them in software with a 90° shift recovers full RHCP (no 3 dB loss) or LHCP. The 17 dBi is a marketing figure; realistic gain at 1.70 GHz, below the 1710 MHz band edge, is about 13-15 dBi (estimate, check with a NanoVNA or a beacon).
    - **Price:** 1,199-1,499 UAH (about $29-37) on Prom.ua
    - **Pros:** Can be bought in Ukraine today. Flat. Also covers 2.2-2.3 GHz S-band. Polarisation is chosen in software.
    - **Cons:** Real gain is unverified, and match at the 1.70 GHz band edge may be poor. Needs a GNU Radio flowgraph because SatDump has no native 2-channel combining. Not enough alone for reliable Metop.
    - **Sources:**
      - https://prom.ua/Antenny-mimo-2x2.html
      - https://5g.in.ua/en/4g-3g-lte-antenna-panelnaya-energy-mimo-2-x-15-db-1700-2700-mgts/
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
    - **Availability:** In stock on Prom.ua and 5g.in.ua (Ukraine)
    - **Q6a compatibility:** Two MHF4 RX inputs on the LimeSDR Micro. A 2-channel stream at about 6 Msps is light work for the QCS6490.
  11.
    - **Name:** 1.7 GHz loop Yagi or crossed Yagis
    - **Key specs:** A 26-element loop Yagi about 181 cm long (about 10λ), estimated about 20 dBi linear by a reader comment, was used on a Meade tracking mount for HRPT. A single linear Yagi loses 3 dB on RHCP; a crossed pair with 2-channel combining avoids that.
    - **Price:** DIY about $20-40 (estimate)
    - **Pros:** Clean, narrow pattern. One commenter found it picked up less LTE interference than a helix.
    - **Cons:** 1.8 m boom is hard to hand-track and catches wind. The crossed version is complex.
    - **Sources:**
      - https://www.rtl-sdr.com/a-tutorial-on-receiving-hrpt-weather-satellite-images-with-an-sdrplay-rsp2/
    - **Availability:** DIY
    - **Q6a compatibility:** One or two RX channels.
  12.
    - **Name:** L-band 4x4 air-dielectric patch array, short-backfire antenna, or 1.7 GHz horn
    - **Key specs:** 4x4 patch array: about 18-19 dBic, about 56 cm square, flat (estimate). Short backfire: rim 2-2.5λ (35-44 cm), about 12-16 dBi, linear unless fed with crossed dipoles. 18 dBi pyramidal horn: about 62 x 49 cm aperture and about 1 m long (calculated).
    - **Price:** DIY about $20-60 (estimate)
    - **Pros:** The patch array is flat and can be built to fold.
    - **Cons:** Patch feed network plus CP phasing is the hardest DIY option. The short backfire is no better than a helix. The horn is huge.
    - **Sources:**
      - https://en.wikipedia.org/wiki/Short_backfire_antenna
      - https://ntrs.nasa.gov/api/citations/19670009367/downloads/19670009367.pdf
    - **Availability:** DIY
    - **Q6a compatibility:** Same as the other L-band options.
- **Recommended:**
  - **Name:** QO-100: TCXO LNB (QRO.cz 25 MHz TCXO with POTY adapter, or Othernet Bullseye) plus a DIY optimum conical horn of 20-23 dBi, with an optional 30 cm W1GHZ metal-plate lens (about 27 dBi) for tripod use. L-band: keep the 11-turn RHCP helix for Meteor-M HRPT and Elektro-L LRIT, and extend it to a 2x2 array of 11-turn helices (about 18 dBic) for Metop-B AHRPT.
  - **Why:** 10 GHz:
  - Three independent reports show a bare LNB already receives QO-100 (CW beacon, FT8), so every dB of horn gain goes straight into SSB quality.
  - A 20 dBi horn (126 x 185 mm) adds about 10 dB and keeps the setup handheld. A 23 dBi horn (178 x 370 mm) gives an estimated beacon C/N of about 17 dB in 2.7 kHz.
  - Adding a 300 mm metal-plate lens (27.4 dBi measured by W1GHZ) comes within about 2 dB of the dropped 35 cm dish, for about $10-25 in aluminium and styrofoam.
  - The QRO.cz LNB has a 0.2 ppm TCXO, about ±2 kHz at the 9.75 GHz LO (calculated), so SSB stays in tune. The Bullseye drifts up to ±30 kHz over temperature.
  - The POTY adapter takes a 22 mm copper tube, which is the natural throat for the horn.
  
  L-band:
  - The 11-turn helix already gives Meteor-M HRPT about 6.5 dB of margin.
  - Metop-B needs 4 dB SNR at 2.333 Msym/s, which takes about 16-19 dBic. Of the non-dish options, only a roughly 0.3 m² array gets there.
  - Four helices reuse the existing design, keep native RHCP, need no dish, come apart for transport, and can run as two sub-arrays on the LimeSDR's two coherent RX channels.
  
  Not reachable without a dish:
  - QO-100 wideband DATV beacon and DATV stations: about 33 dBi or more.
  - QRP SSB stations more than about 15-20 dB below the beacon.
  - FengYun-3 AHRPT: no L-band FengYun transmits to Europe in 2026. FY-3D to FY-3H are on X-band at 30-38 Msym/s, which needs a tracked dish of roughly 1 m or larger.
  - Metop-SG direct broadcast at 7.825 GHz (X-band).
  - Metop-B on low-elevation passes.
  
  Minimum non-dish sizes:
  - Typical QO-100 SSB (about 25-27 dBi): a 22 x 59 cm conical horn, or a 30 cm lens on a horn.
  - QO-100 DATV (33 dBi or more): an aperture of about 45-50 cm at high efficiency, which is effectively dish-sized.
  - Metop-B: about 55-60 cm square of RHCP array.
  - **Price:** QO-100: about $40-95 (LNB $30-70 plus $5-25 for horn and lens materials). L-band: about $60-200 including one SAW LNA per helix or per pair (LNA prices not verified here).
  - **Sources:**
    - https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
    - http://ok1dx.cz/techinfo/qo100/qo100.html
    - http://www.w1ghz.org/antbook/chap2.pdf
    - http://www.w1ghz.org/antbook/chap3.pdf
    - https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz
    - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
    - https://wiki.batc.org.uk/QO-100_WB_Bandplan
    - https://forum.batc.org.uk/viewtopic.php?p=37232
    - https://blog.metislair.com/docs/Radio/L%20band%20weather%20satellite%20reception%20guide.html
    - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
    - https://www.ospo.noaa.gov/operations/metop/status.html
    - https://space.oscar.wmo.int/satellites/view/fy_3c
    - https://github.com/SatDump/SatDump/blob/master/resources/pipelines/FengYun-3.json
- **Budget option:**
  - **Name:** Goobay 67269 PLL LNB (€5.90) or Bullseye ($29.95), with a conical horn of about 18-20 dBi made from tin or copper sheet using an HDL_ANT paper template. L-band: the existing 11-turn helix, or a 16-turn helix or t0nito helicone, for Meteor-M HRPT only. Optionally add a Prom.ua dual-polarised 4G MIMO panel for S-band and polarisation experiments.
  - **Why:** This keeps the proven QO-100 results (CW beacon, FT8, CW, and beacon-level SSB at about 12-14 dB estimated C/N) at near-zero cost. The Goobay's ±300 kHz drift is fixed in software by locking to the narrowband beacon. On L-band it covers Meteor-M2-3/M2-4 HRPT and Elektro-L LRIT, which are the realistic dish-free targets. Metop-B and DATV are given up.
  - **Price:** About $10-45 (plus 1,199-1,499 UAH, about $29-37, for the optional panel)
- **Risks:**
  - No published QO-100 report using a horn, lens or flat panel was found. Horn and lens C/N figures are estimates scaled from bare-LNB results (OK1DX, RigExpert) and dish results (BATC), good to about ±3-4 dB. Verify by measuring the beacon C/N against a bare LNB.
  - Metop C/N0 is estimated from Meteor-M2-3 helix field data plus symbol-rate scaling, assuming similar transmit power (EIRP not verified). Metop-B could be 2-3 dB better or worse than estimated.
  - L-band targets are shrinking. NOAA OSPO (September 2026) lists Metop-C AHRPT as 'No'. EUMETSAT shows Metop-B ground service as degraded. FengYun-3 L-band is gone (FY-3C ended 28 Nov 2024). WMO OSCAR lists Meteor-M N2-3 as 'working with limitations' and gives N2-4's HRPT as 1705 MHz rather than 1700 MHz. Check SatNOGS or SatDump reports before building the array.
  - Strong LTE-1800 and UMTS-2100 signals in Ukraine can desensitise L-band LNAs. The metislair guide advises against SPF5189Z-type wideband LNAs for HRPT; use SAW-filtered LNAs (it recommends SAWbird+ GOES) at each helix.
  - The metal-plate lens is polarisation-specific and narrowband (W1GHZ data is at 10.368 GHz). Redesign it for 10.49 GHz and rotate it 90° for the horizontally polarised wideband transponder.
  - Selfsat panels are not specified below 10.7 GHz, and their LNB is not TCXO-stabilised; they are untested on QO-100. Cheap 4G panels overstate gain, and 1.70 GHz is just below their 1710 MHz band edge.
  - Helix-array gain is lost to phase errors or mismatch between elements. It needs equal-length feeds, a matching section per helix, and a NanoVNA check.
  - The LimeSDR Micro's RX3/RX4 FPC inputs are analogue baseband and need an accessory; 4-channel beamforming is not confirmed available.
  - LNB output (50-66 dB gain) can overload the LimeSDR; a 10-20 dB attenuator and a DC block are mandatory.
- **Integration notes:**
  - QO-100 pointing from Ukraine (calculated for 25.9°E): Lviv about 178° azimuth and 33° elevation; Kyiv about 186° and 32°; Kharkiv about 193° and 32°; Odesa about 187° and 36°. Polarisation skew is only a few degrees. Beam widths: bare LNB about 40°, 20 dBi horn about 16°, 23 dBi horn about 11°, lens about 7°. Coarse-aim with the BNO085 and GNSS, then peak on the CW beacon at 10489.55 MHz (IF about 739.55 MHz with a 9750 MHz LO).
  - Power the LNB at 13 V for vertical (narrowband) and 18 V for horizontal (wideband DATV). Bullseye limits are 11.5-14 V and 16-19 V; Goobay draws up to 167 mA. Run a buck/boost from the 4S pack through a bias-tee injector, then DC block, then a 10-20 dB pad into a LimeSDR MHF4 RX.
  - For SSB, the narrowband beacon is the frequency reference. Use a QRO.cz 0.2 ppm TCXO, a Bullseye (±30 kHz over temperature), or software beacon-lock. SDR Console has beacon lock on Windows. On Ubuntu, a GNU Radio or SDRangel tracker is needed; I did not confirm that SDR++ has a beacon-lock feature.
  - L-band array: put one SAW LNA per helix, or per pair, before any combiner. Either use a 4-way Wilkinson combiner (about 0.7-0.8 dB loss) into RX1, or feed two 2-helix sub-arrays into RX1 and RX2 and sum them coherently in GNU Radio, with the phase estimated by cross-correlation. Record the combined baseband and run SatDump's metop_ahrpt pipeline (1701.3 MHz, 2.333 Msym/s; sample at about 6 Msps) offline. Meteor HRPT uses meteor_hrpt at 665.4 ksym/s.
  - Tracking: the 2x2 array's beam is about 20°. A LEO pass moves at most about 0.5°/s at zenith (calculated), so hand-tracking on a pan-tilt tripod with the on-screen BNO085 pointing aid works. Mount helices about 50 cm or more above ground (field reports show height matters) and use trees or buildings to shadow cell towers.
  - All of these antennas are external. The palm-sized unit only takes IF or L-band coax through MHF4-to-SMA pigtails, plus a DC feed. Keep 10 GHz conversion at the antenna (LNB) and the L-band LNAs at the feed.
- **Double duty opportunities:**
  - The bare LNB doubles as a wide-beam (about 40°) finder: find QO-100, then push the horn or lens onto the same 22 mm throat.
  - The LimeSDR Micro's two coherent RX channels can serve three roles: polarisation combining (dual-polarised panel, or crossed Yagis giving software RHCP/LHCP), spatial combining (two helix sub-arrays), and interference cancellation. All three come from the same GNU Radio flowgraph, with no hardware hybrids.
  - The dual-polarised 1700-2700 MHz 4G panel covers both 1.70 GHz HRPT (Meteor) and 2.2-2.3 GHz S-band downlinks. It costs about $29-37 locally.
  - Each helix in the 2x2 array is also a standalone Meteor-M HRPT and Elektro-L LRIT antenna. Two of them make a medium-gain array, and all four make the Metop array.
  - The QRO.cz POTY-adapter LNB accepts a horn, a lens-fed horn or a dish feed in the same 22 mm mount. A broadband WR90-class horn also covers other 10 GHz work, but not X-band LEO, which needs a dish.
- **Confidence:** medium

## Форуми та досвід спільноти (`forums`)

_Агент цього етапу ще працює (run `wf_5a66d65f-c3f`)._

