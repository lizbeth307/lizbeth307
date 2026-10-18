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

_Run `wf_5a66d65f-c3f`_

- **Component:** Antennas to replace the dishes: QO-100 at 10.489 GHz (TCXO LNB with no reflector, conical horn, metal-plate lens) and L-band HRPT at 1.70 GHz (long helix or helicone, a 2x2 helix array, 4G MIMO panels, loop Yagi), all feeding a LimeSDR Micro on the Radxa Dragon Q6A
- **Experiences:**
  1.
    - **Product:** Plain TV LNB with no dish, into an RTL-SDR
    - **Source url:** http://ok1dx.cz/techinfo/qo100/qo100.html
    - **Community:** OK1DX personal ham station page (Czech Republic, updated August 2025)
    - **What they built:** A standard LNB pointed at QO-100 with no reflector, feeding an RTL-SDR through an attenuator. The same LNB was later used in an 80 cm offset dish.
    - **Problems:**
      - The LNB output was too strong for the RTL-SDR, which needed about 20 dB of attenuation.
      - The 10 GHz signal did not pass through the glass of the balcony door.
      - The LO drifted about 50 kHz after switch-on.
    - **Fixes:**
      - Fitted an attenuator of about 20 dB between the LNB and the RTL-SDR.
      - Moved the LNB outside so there was no glass in the path.
      - For drift, the author points to beacon locking but did not use it himself.
    - **Outcome:** He copied the CW beacon with the LNB alone, just pointed at QO-100. In the dish the signal was strong enough to show the transponder noise floor. He later removed the receive dish and went back to a web SDR.
  2.
    - **Product:** LNB modified for an external 25 MHz reference (RigExpert Tokenblauser GPSDO), ADALM-Pluto on a 40 MHz external reference, SDR Console and WSJT-X
    - **Source url:** https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
    - **Community:** RigExpert application note TBR-AN-1 (12 July 2022)
    - **What they built:** A dish-free FT8 receiver for the QO-100 narrowband transponder. The note's parts list literally reads 'Satellite dish – you do not need it!'
    - **Problems:**
      - The stock 25 MHz crystal is not stable enough for narrowband FT8.
      - The LNB has to be pointed and its polarisation set.
    - **Fixes:**
      - Opened the LNB and used an oscilloscope to find the crystal pad with the larger swing (the chip's output). Cut that trace and wired it to an RF connector with a 75 Ω resistor to ground (or reused the LNB's second output). Fed 25 MHz from the GPSDO. Resealed the case with silicone.
      - Aimed to within about ±20° using eshail.batc.org.uk/point, because the bare LNB has a wide beam. Mounted the LNB for vertical polarisation.
    - **Outcome:** FT8 signals at 10.489540-10.489543 GHz showed on the waterfall and decoded in WSJT-X. The note gives no S/N figures.
  3.
    - **Product:** RemoteQTH (QRO.cz) LNB PLL with TCXO plus bias-tee pack (€69 excl. VAT)
    - **Source url:** https://www.passion-radio.com/satellite-qo-100/converter-432-936.html
    - **Community:** Passion Radio customer review dated 17/12/2022
    - **What they built:** The QRO.cz TCXO LNB and its bias-tee, tested with and without an ex-Sky dish
    - **Problems:**
      - The review gives no figures.
    - **Fixes:** []
    - **Outcome:** Quote: 'I can actually receive the QO-100 directly without using the dish antenna, which was a surprise.' With the dish the signal was 'very strong'. This is an independent confirmation that a TCXO LNB alone hears QO-100.
  4.
    - **Product:** Bare LNB used for receive, with a WiFi panel or Yagi for transmit
    - **Source url:** https://www.sarts.org.sg/wp/wp-content/uploads/2025/09/QO-100-Presentation-1.pdf
    - **Community:** SARTS (Singapore Amateur Radio Transmitting Society) QO-100 presentation, September 2025
    - **What they built:** A minimal QO-100 station for members who cannot get permission for a dish
    - **Problems:**
      - Elevation from Singapore is only about 3.2°.
      - Tall buildings block the path.
      - Dishes need permission and draw attention.
    - **Fixes:**
      - Use a bare LNB for receive, which is enough for some FT8 and JT65.
    - **Outcome:** The slide text reads: 'Can work some FT8/JT65 with bare LNB for RX + wifi panel/yagi for TX'. This was seen only in a search-engine snippet; downloading the PDF failed (HTTP 503 or connection reset).
  5.
    - **Product:** Othernet Bullseye TCXO LNB with ADALM-Pluto and SDR Console beacon lock
    - **Source url:** https://forum.sdr-radio.com/viewtopic.php?p=10393
    - **Community:** SDR-Radio.com forum, Pluto board (October 2023, G8VLR, M0TGC, G4ELI, jdow)
    - **What they built:** A QO-100 narrowband receiver using the Bullseye LNB
    - **Problems:**
      - The frequency drifted by up to 2 kHz over time even with beacon lock on.
      - It later jumped by a 'massive 20 kHz'.
    - **Fixes:**
      - Reinstalled SDR Console, which did not help.
      - Started testing the Pluto and its new 40 MHz reference separately.
      - jdow's advice: 1 ppm at 10 GHz is 10 kHz, so a GPS-locked downconverter is needed for tight tolerance.
    - **Outcome:** Unresolved in the thread; a hardware fault was suspected. M0TGC reports years of drift-free beacon lock with a similar setup.
  6.
    - **Product:** Othernet Bullseye LNB with Langstone and Minitiouner receivers
    - **Source url:** https://forum.batc.org.uk/viewtopic.php?p=26716
    - **Community:** BATC forum (2021). Seen only through search-engine snippets, because the forum serves a JavaScript browser-verification page (HTTP 503) to automated clients.
    - **What they built:** QO-100 narrowband and wideband receive setups
    - **Problems:**
      - One user's Bullseye had about 10 kHz offset with 'some drift'.
      - Another (topic p=27854) found the LO 'normally within 20 kHz' and his was 16 kHz low.
    - **Fixes:**
      - Reply in the Langstone thread: there is 'no means of locking a drifting LNB'; the software assumes a modified, stable LNB.
      - Asked the manufacturer whether users could trim the LO; the answer was not seen.
    - **Outcome:** Bullseye offsets of 10-20 kHz are normal. Software beacon lock needs a capture window of at least ±30 kHz to cover its temperature specification.
  7.
    - **Product:** Goobay 67269 PLL LNB modified for an external reference
    - **Source url:** https://baltic-lab.com/2023/07/lnb-modification-for-10-ghz-qo-100-satellite-reception/
    - **Community:** baltic-lab blog and its comments (July 2023, comments up to February 2024)
    - **What they built:** A Goobay LNB with its crystal removed, fed with 25.78 MHz to pull the LO near 10.49 GHz
    - **Problems:**
      - The LNB's high gain easily overdrove the receiver.
      - The 75 Ω LNB input was not matched to 50 Ω test equipment.
      - There is very little room inside the case.
      - Reader 'Ali' (February 2024) saw the supply current rise when the reference was connected, but only a raised noise floor and no signal, on two LNBs.
    - **Fixes:**
      - Removed the 25 MHz crystal and fitted a 2.2 µH inductor under Kapton tape. Cut the XTAL1 trace and added 18 pF from the F-connector pin to XTAL1. Injected about 3 Vpp (about 12 dBm) of reference.
      - Fed 14 V bias; the current rose from about 60 mA unlocked to about 90 mA locked.
      - Pointed the LNB away from the source and fitted a 10 dB attenuator before the RTL2832.
    - **Outcome:** Works on the bench with the author's test signals; it had not been tested on the satellite. Ali's failure case is unresolved.
  8.
    - **Product:** AMSAT-DL QO-100 Linux Transceiver (ADALM-Pluto on ARM single-board computers)
    - **Source url:** https://amsat-dl.org/en/qo-100-linux-transceiver/
    - **Community:** AMSAT-DL project page
    - **What they built:** A QO-100 transceiver running on Raspberry Pi 4, Odroid C4/N2 and Rocket-PI-4 boards (armhf image)
    - **Problems:**
      - LNB clock drift.
    - **Fixes:**
      - Optional beacon synchronisation corrects LNB drift within a range of about 2 kHz.
      - Built-in calibration programs for the Pluto TCXO and the LNB, for systems without GPS sync.
    - **Outcome:** A working precedent for beacon lock on ARM Linux. It supports the Pluto only, not the LimeSDR, and its ±2 kHz range implies a TCXO or GPSDO LNB.
  9.
    - **Product:** F1ATB Remote-SDR, a QO-100 live web SDR (Raspberry Pi 4, GNU Radio, HackRF or Nooelec)
    - **Source url:** https://f1atb.fr/qo-100-live/
    - **Community:** F1ATB project page and its comments
    - **What they built:** A browser-based QO-100 receiver that corrects LNB drift automatically
    - **Problems:**
      - The required LNB correction is about -140 to -180 kHz depending on temperature.
      - The middle beacon sits at the SDR centre frequency, where I/Q DC bias corrupts it.
      - Beacons are sometimes switched off, which breaks the lock.
      - Users report waterfall lag.
    - **Fixes:**
      - Locks on the lower and upper beacons instead of the middle one.
      - Enable autocorrect; for large drift, move the signal manually with the mouse wheel; set the span to 500 kHz.
    - **Outcome:** Proves a wide-capture, two-beacon tracker can make an unstabilised LNB usable on Linux and ARM. A ±2 kHz window could never cover drift of this size.
  10.
    - **Product:** W1GHZ/KB1VC aluminium-foil metal-plate lenses (150 mm and 300 mm) on a small horn
    - **Source url:** http://www.w1ghz.org/antbook/chap3.pdf
    - **Community:** W1GHZ (Paul Wade) Microwave Antenna Book, Eastern VHF/UHF Conference 1992, contest use 1992-1997
    - **What they built:** Foam-and-foil lenses in front of a Gunnplexer horn at 10 GHz, used for portable terrestrial contesting
    - **Problems:**
      - Best gain came with the horn slightly closer to the lens than calculated (edge effects).
      - The lens only works in the E-plane.
      - With a Gunnplexer, energy reflected from the lens modulated the LO.
    - **Fixes:**
      - Make the plates 1-2 inches larger than calculated.
      - Mount the plates perpendicular to the wide waveguide wall, i.e. parallel to the E-field.
      - Adjust the horn-to-lens spacing for the best received signal.
      - Cut to 1 mm accuracy; the foam thickness sets the plate spacing.
    - **Outcome:** Measured on an antenna range: horn 17.5 dBi; with the 150 mm lens 20.9 dBi; with the 300 mm lens 27.4 dBi (about 50% efficiency). Contest range grew about 50%, to over 200 km. This is terrestrial use; no QO-100 use was found.
  11.
    - **Product:** W1GHZ HDL_ANT homebrew horns at 10 GHz
    - **Source url:** http://www.w1ghz.org/antbook/chap2.pdf
    - **Community:** W1GHZ Microwave Antenna Book
    - **What they built:** Sheet-metal horns from printed templates, including a 17.5 dB horn used for long 10 GHz contacts
    - **Problems:**
      - The horn's length grows much faster than its gain.
    - **Fixes:**
      - Use optimum-horn templates from HDL_ANT.
    - **Outcome:** 'Performance of the finished horn almost always matches predictions, with no tuning adjustments required.' This supports the estimated gain of a DIY horn, but no QO-100 horn report exists.
  12.
    - **Product:** QO-100 wideband DATV beacon, received with large dishes
    - **Source url:** https://forum.batc.org.uk/viewtopic.php?p=18655
    - **Community:** BATC forum, 'QO-100 Wideband Spectrum Monitor' thread. Seen only through a search-engine snippet; the forum is behind a browser-verification wall.
    - **What they built:** Measurements of beacon MER on consumer-grade setups
    - **Problems:**
      - Beacon MER is about 8-9 dB on a 1.2 m dish and roughly 10 dB on 1.8 m.
      - Nobody has reported more than about 11 dB.
    - **Fixes:** []
    - **Outcome:** The wideband beacon is limited by noise on the satellite itself, and a 71 cm dish already sits only about 3 dB above threshold. A 20-27 dBi horn or lens cannot decode DATV, which confirms dropping DATV.
  13.
    - **Product:** 11-turn RHCP copper helix on a 17x17 cm ground plane with bent-up edges, with a SAWbird+ GOES LNA and Airspy R2
    - **Source url:** https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
    - **Community:** Meti's blog (metislair), also covered by RTL-SDR.com
    - **What they built:** Successive dish-free L-band helices of 5.5, 8 and 11 turns
    - **Problems:**
      - Signal depends strongly on height above ground and can vanish at the wrong height.
      - Small build imperfections cost signal.
      - A nearby cell tower raised the noise floor.
      - The 5.5-turn and 8-turn versions underperformed.
    - **Fixes:**
      - Hold the helix about 50 cm up and vary the height during the pass.
      - Rotating the helix gained about 1 dB.
      - Moving a few metres so trees shadowed the cell tower steadied the noise floor.
      - Bending up the ground-plane edges gained about 1.5 dB.
      - Went to 11 turns.
    - **Outcome:** Meteor-M2-3 HRPT image at about 7 dB average SNR. Elektro-L3: 10.5 dB average on GGAK and LRIT decoded at 13° elevation. No Metop attempt reported.
  14.
    - **Product:** t0nito 3D-printed 1.7 GHz helicone (Thingiverse 6436342), PLA, Nooelec GOES preamp, RTL-SDR
    - **Source url:** https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
    - **Community:** SatNOGS community forum (pe2bz, t0nito, herman; January-February 2024)
    - **What they built:** The helicone (cone 134 mm base, 440 mm top, 88 mm high, 29.7°), used hand-tracked and as a fixed zenith-pointing SatNOGS station, also tried with 1545 and 2250 MHz helices
    - **Problems:**
      - PrusaSlicer did not fix print orientation or add supports, which cost PLA and hours of reprinting.
      - The holder did not suit swappable helices and connectors.
      - Question raised: a wok or frying-pan reflector flips the handedness, so does this one?
    - **Fixes:**
      - Check part orientation and supports before slicing.
      - For S-band, all dimensions were scaled to 75%.
      - herman's explanation: a helix over a ground plane keeps its handedness (RHCP helix for an RHCP signal); only a reflector fed from the focus inverts it.
    - **Outcome:** Good Meteor images, hand-tracked. After 72 h of observations at 1700 and 2250 MHz it beat a helix with a flat reflector. Three weak S-band satellites were found that had not shown up before.
  15.
    - **Product:** t0nito helicone printed by Saveitforparts (Gabe), with a phone, RTL-SDR and SatDump
    - **Source url:** https://www.rtl-sdr.com/saveitforparts-testing-a-3d-printable-satellite-antenna-for-noaa-meteor-and-other-polar-orbiting-l-band-satellites/
    - **Community:** RTL-SDR.com write-up of a YouTube build
    - **What they built:** A handheld helicone for polar-orbiting L-band satellites
    - **Problems:**
      - The scaffold legs warped in several prints.
    - **Fixes:**
      - Modified the model to add centre supports.
    - **Outcome:** NOAA HRPT images received hand-tracked. NOAA HRPT has since ended with NOAA-15/18/19 decommissioning, so Meteor-M is the remaining target.
  16.
    - **Product:** 5-turn helix (derekcz OpenSCAD scaffold) with an AliExpress TQM3M9037 LNA powered by the HackRF bias-tee
    - **Source url:** https://community.libre.space/t/station-2830-stockholm-l-and-s-band-new-helix-antenna/12046
    - **Community:** SatNOGS community forum (SM0TGU, SA2KNG, m0roj, vu3tyg; July-August 2024)
    - **What they built:** A fixed, zenith-pointing L/S-band SatNOGS station
    - **Problems:**
      - The LNA board includes a TP4056 Li-ion charger. If the switch is ON when power is applied, it drops into trickle mode and delivers only about 2.5 V.
      - A B5819 diode sits oddly in the bias path.
      - m0roj found the LNA unsuitable for mast-head use because of this power behaviour.
      - Users asked about running L-band and S-band through one LNA with a diplexer.
    - **Fixes:**
      - Power up with the switch OFF ('USB mode').
      - SA2KNG removed the charger circuit and fitted a linear regulator.
      - Sprayed the helix with UV protection and sealed solder joints with glue and vulcanising tape.
      - SA2KNG's advice: one LNA at each antenna feedpoint, cavity filters against strong adjacent signals, and quarter-wave care if joining feeds with a T.
    - **Outcome:** Performance comparable to other helix S-band stations.
  17.
    - **Product:** 26-element loop Yagi on a Meade telescope mount compared with helices (RSP2 HRPT tutorial and its comments)
    - **Source url:** https://www.rtl-sdr.com/a-tutorial-on-receiving-hrpt-weather-satellite-images-with-an-sdrplay-rsp2/
    - **Community:** RTL-SDR.com reader comments (RFGeek, Adam, G1EKW and others)
    - **What they built:** HRPT reception with a loop Yagi about 181 cm long. Readers also built or discussed 25-turn and 1.5 m helices.
    - **Problems:**
      - RFGeek tested a helix against a loop Yagi of similar length; the helix 'performed much worse', mainly from terrestrial interference outside the beam.
      - A helix's feed impedance is about 150 Ω.
      - Kraus's gain formula is about 3 dB optimistic.
      - The helix ground plane collided with a DS2090AT mount, limiting tilt to about 45°.
      - The loop Yagi is narrowband and needs tuning.
    - **Fixes:**
      - G1EKW: helix impedance is about 140 × C/λ ohms; a parallel-fed stacked pair gives about 70 Ω; enlarge the circumference about 7% (about 12 mm at HRPT).
      - Adam: capacitive matching near the first turn, an aluminium square boom, copper strip, and a rimmed reflector.
      - Trim the reflector where it hits the mount.
    - **Outcome:** The loop Yagi decoded HRPT; no SNR figures. Adam estimated a 25-turn helix at about 16.5 dBi and a 7λ practical limit.
  18.
    - **Product:** 2.4 GHz WiFi grid antenna, LNA4ALL and ADALM-Pluto, used for NOAA-18 HRPT
    - **Source url:** https://www.rtl-sdr.com/receiving-almost-hrpt-with-the-adalm-pluto-and-a-wifi-grid-antenna/
    - **Community:** RTL-SDR.com, Tysonpower (German YouTube)
    - **What they built:** An off-band, mid-gain antenna with no tracking
    - **Problems:**
      - The signal was detected but too weak to decode.
      - The antenna is designed for 2.4 GHz, not 1.7 GHz.
      - There was no tracking.
    - **Fixes:** []
    - **Outcome:** Failed to decode. A cautionary data point: mid-gain antennas that are off-band or untracked fall short even of the easiest HRPT.
  19.
    - **Product:** SatDump Metop AHRPT on an RTL-SDR Blog V4 with autotrack
    - **Source url:** https://github.com/SatDump/SatDump/issues/727
    - **Community:** SatDump GitHub issues (closed 13 June 2024)
    - **What they built:** Metop AHRPT reception (antenna not stated)
    - **Problems:**
      - NOSYNC despite 'plenty of SNR'; restarting mid-pass made it sync immediately.
    - **Fixes:**
      - Raised the sample rate to 2.88 Msps and enabled both DC block and AGC. Maintainer Aang23 suspected the RTL-SDR was at the edge of its capability.
    - **Outcome:** Decoded AVHRR. On the LimeSDR, run Metop at about 6 Msps with DC block on, so no symbol-rate edge case occurs.
  20.
    - **Product:** L-band LNAs and minimum SNR (metislair L-band reception guide)
    - **Source url:** https://blog.metislair.com/docs/Radio/L%20band%20weather%20satellite%20reception%20guide.html
    - **Community:** metislair guide (SatDump user community)
    - **What they built:** Guidance compiled from many HRPT stations
    - **Problems:**
      - The SAWbird+ GOES backfeeds DC when powered over USB.
      - Cheap 'SPF/SBF' wideband LNAs do not work well enough for L-band HRPT.
      - Noise-floor jumps come from phones, cell towers, bad USB cables and storms.
      - NOSYNC with a 'donut' constellation near the SDR's sample-rate limit.
      - Viterbi spikes from dropped samples.
    - **Fixes:**
      - Power the SAWbird+ through a bias-tee or add a DC block.
      - Use a SAWbird+ GOES or a Digitelektro L-band LNA (about €60).
      - Airplane mode for phones; move away from towers; lower the gain; add a cavity filter such as the Sysmocom L-band filter.
      - Sample at about 1.2x the symbol rate plus Doppler margin; use a high-performance power plan and raise SatDump's priority.
    - **Outcome:** Minimum SNRs: Meteor HRPT 0.5 dB, Metop AHRPT 4 dB. The minimum dish for both is 60 cm. Metop AHRPT is called 'just barely receivable with an RTLSDR'.
  21.
    - **Product:** LMS7002M dual-RX phase coherence (LimeSDR family, including LimeSuiteNG on XTRX)
    - **Source url:** https://discourse.myriadrf.org/t/limesdr-xtrx-rx-data-out-of-sync/13290
    - **Community:** MyriadRF/Lime discourse: topics 13290 (July 2026), 8708 (2025-2026), 2501 (2018); LimeSuiteNG issue #356
    - **What they built:** Two-channel coherent receivers for direction finding, beamforming and MIMO
    - **Problems:**
      - Driving both RX channels from a splitter showed misaligned sample data between RX A and RX B in LimeSuiteNG basicRX and LimeGUI.
      - The channel-alignment code from classic LimeSuite was never ported to LimeSuiteNG; the StreamConfig alignPhase flag is unused.
      - On the LMS7002M, the phase between RX A and RX B is randomly 0° or 180° after power-up or an LO retune.
    - **Fixes:**
      - Andrew Back (Lime) opened LimeSuiteNG issue #356 'Channel Alignment' on 29 July 2026; it is still open.
      - CarlThurston wrote an unfinished patch porting AlignRxRF.
      - 2018 workarounds: RstRxIQGen() resets the RX PLL forward divider and quadrature generator. Others measured the phase on a loopback or external tone after every retune and added π when needed.
    - **Outcome:** No fix in LimeSuiteNG yet. This directly affects the plan to combine two helix sub-arrays or two panel polarisations on the LimeSDR Micro's RX1/RX2.
  22.
    - **Product:** Ukrainian 4G MIMO panels for 1700-2700 MHz (R-Net 'Kvadrat' 2x17, Energy MIMO 2x15, Energy MIMO 2x24)
    - **Source url:** https://prom.ua/Antenny-mimo-2x2.html
    - **Community:** Prom.ua listings (Ukraine). These are spec checks, not user reports; no hobbyist HRPT report with these panels was found.
    - **What they built:** No builds; I worked out each panel's maximum possible gain from the dimensions in its listing.
    - **Problems:**
      - R-Net 2x17: 205x205x50 mm, 0.6 kg, 1900 UAH. Its 20.5 cm aperture cannot exceed 12.3 dBi at 1.70 GHz even at 100% efficiency, or 16.3 dBi at 2.7 GHz.
      - Energy 2x15: 230x230 mm, 935 UAH. At most 13.3 dBi at 1.70 GHz.
      - Energy 2x24: 430x430x40 mm, 2805-2950 UAH. At most 18.7 dBi at 1.70 GHz and 22.8 dBi at 2.7 GHz.
      - 1.70 GHz is below the 1710 MHz design edge of all three panels.
    - **Fixes:**
      - Self-researched: gain from aperture, D = 4πA/λ² with λ = 0.176 m.
      - Real-world estimates: about 10-11 dBi for the small panels and about 15-17 dBi for the 43 cm panel.
      - Check the 1.70 GHz match with a NanoVNA, and compare against the 11-turn helix on a Meteor pass, before relying on any panel.
    - **Outcome:** The small panels are not Metop candidates. The 43 cm panel, with software polarisation combining, could reach roughly 15-17 dBic, which is borderline for Metop-B. Unverified.
- **Common problems:**
  1.
    - **Problem:** LNB output (50-66 dB gain) overloads the SDR when the LNB is used without a dish
    - **Affected products:** Bare TV LNBs, Goobay PLL LNB, Bullseye or QRO.cz LNB into RTL-SDR, Pluto or LimeSDR
    - **Frequency:** common
    - **Known fix:** Fit a 10-20 dB pad between the LNB and the SDR (OK1DX used about 20 dB; baltic-lab used 10 dB). Also fit a DC block on the SDR side of the bias-tee. Even without a dish, the LNB's own gain is the problem.
    - **Fix sources:**
      - http://ok1dx.cz/techinfo/qo100/qo100.html
      - https://baltic-lab.com/2023/07/lnb-modification-for-10-ghz-qo-100-satellite-reception/
  2.
    - **Problem:** LNB LO drift or offset is too large for narrowband SSB, CW and FT8 and for narrow beacon-lock windows
    - **Affected products:** Plain LNBs: about 50 kHz after switch-on (OK1DX) and -140 to -180 kHz versus temperature (F1ATB). Bullseye: offset 10-20 kHz and drift up to ±30 kHz. Goobay: ±300 kHz.
    - **Frequency:** common
    - **Known fix:** Use a 0.2 ppm TCXO LNB (QRO.cz, about ±1 kHz after 5 minutes of warm-up) or a GPSDO-referenced LNB (RigExpert method). Then add software beacon lock. AMSAT-DL's Linux tracker covers only ±2 kHz. F1ATB's Remote-SDR tracks the lower and upper beacons (avoiding the centre-frequency DC spike) over a wide range, which suits unstabilised LNBs.
    - **Fix sources:**
      - https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz
      - https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
      - https://amsat-dl.org/en/qo-100-linux-transceiver/
      - https://f1atb.fr/qo-100-live/
      - https://forum.sdr-radio.com/viewtopic.php?p=10393
  3.
    - **Problem:** 10 GHz does not pass through window or door glass (likely coated glazing)
    - **Affected products:** Any indoor dish-free QO-100 attempt
    - **Frequency:** occasional
    - **Known fix:** Operate outdoors or through an open window with a clear path to 25.9°E.
    - **Fix sources:**
      - http://ok1dx.cz/techinfo/qo100/qo100.html
  4.
    - **Problem:** Dish-free L-band helix: signal swings with height and ground reflection, and nearby cell towers raise the noise floor
    - **Affected products:** 11-turn helix, helicone, longer helices
    - **Frequency:** common
    - **Known fix:** Mount at least 50 cm above ground and vary the height during the pass. Rotate the helix (about +1 dB). Bend up the ground-plane edges (about +1.5 dB). Pick a spot where trees or buildings shadow cell towers. Put a SAW-filtered LNA (SAWbird+ GOES, Digitelektro) at the feed, and add a cavity filter if needed.
    - **Fix sources:**
      - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
      - https://blog.metislair.com/docs/Radio/L%20band%20weather%20satellite%20reception%20guide.html
      - https://community.libre.space/t/station-2830-stockholm-l-and-s-band-new-helix-antenna/12046
  5.
    - **Problem:** A helix picks up terrestrial interference outside its main beam, worse than a loop Yagi of similar length
    - **Affected products:** Long L-band helices
    - **Frequency:** occasional
    - **Known fix:** Filter at the feed and shield by site choice. Consider a loop Yagi (narrower, cleaner pattern, but narrowband and needs tuning). An array narrows the beam and reduces the problem.
    - **Fix sources:**
      - https://www.rtl-sdr.com/a-tutorial-on-receiving-hrpt-weather-satellite-images-with-an-sdrplay-rsp2/
  6.
    - **Problem:** Helix feed impedance is about 140-150 Ω, and Kraus's gain formula is about 3 dB optimistic
    - **Affected products:** All axial-mode helices and helix arrays
    - **Frequency:** common
    - **Known fix:** Fit a matching strip or capacitive matching near the first turn (2 mm above the reflector at its start, adjusted for peak signal). Use Z ≈ 140·C/λ. A parallel-fed pair gives about 70 Ω. Use Emerson's or King-Wong's gain figures, not Kraus's. Check every element with a NanoVNA.
    - **Fix sources:**
      - https://www.rtl-sdr.com/a-tutorial-on-receiving-hrpt-weather-satellite-images-with-an-sdrplay-rsp2/
      - https://wettersat.bplaced.net/equipment.html
      - https://www.qsl.net/seti/articles/helix2.htm
  7.
    - **Problem:** Getting circular-polarisation handedness wrong
    - **Affected products:** Helix over a ground plane versus a helix feeding a reflector (wok, dish)
    - **Frequency:** occasional
    - **Known fix:** A helix on a ground plane or cone keeps its handedness, so wind it RHCP for RHCP downlinks. Only reflector-fed helices need the opposite hand.
    - **Fix sources:**
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
  8.
    - **Problem:** 3D-printed helix and helicone scaffolds warp or print badly
    - **Affected products:** t0nito helicone, derekcz helix scaffold
    - **Frequency:** occasional
    - **Known fix:** Add centre supports to the legs (Saveitforparts). Check orientation and supports in the slicer (pe2bz). Spray UV protection and seal joints with glue and vulcanising tape for outdoor use.
    - **Fix sources:**
      - https://www.rtl-sdr.com/saveitforparts-testing-a-3d-printable-satellite-antenna-for-noaa-meteor-and-other-polar-orbiting-l-band-satellites/
      - https://community.libre.space/t/3d-printed-helical-cone-reflector-antenna/11309
  9.
    - **Problem:** Cheap AliExpress L-band LNA boards misbehave on bias power
    - **Affected products:** TQM3M9037 LNA with an onboard TP4056 charger
    - **Frequency:** occasional
    - **Known fix:** Power up with the switch OFF ('USB mode'), or remove the charger and fit a linear regulator.
    - **Fix sources:**
      - https://community.libre.space/t/station-2830-stockholm-l-and-s-band-new-helix-antenna/12046
  10.
    - **Problem:** Metop AHRPT NOSYNC even with good SNR
    - **Affected products:** SatDump metop_ahrpt pipeline on marginal sample-rate settings
    - **Frequency:** occasional
    - **Known fix:** Raise the sample rate (2.88 Msps worked on an RTL-SDR V4; use about 6 Msps on the LimeSDR) and enable DC block and AGC.
    - **Fix sources:**
      - https://github.com/SatDump/SatDump/issues/727
  11.
    - **Problem:** LMS7002M RX A/B relative phase is random (including 0/180° flips after retune) and samples are misaligned; LimeSuiteNG has no channel alignment
    - **Affected products:** LimeSDR family, including LimeSDR Micro two-channel combining
    - **Frequency:** occasional
    - **Known fix:** There is no driver fix (LimeSuiteNG issue #356 is open). Workaround: estimate the delay and phase in software on each stream.
    - **Fix sources:**
      - https://discourse.myriadrf.org/t/limesdr-xtrx-rx-data-out-of-sync/13290
      - https://discourse.myriadrf.org/t/lms7002m-mimo-mode/2501
      - https://github.com/myriadrf/LimeSuiteNG/issues?q=channel+alignment
  12.
    - **Problem:** Advertised 4G panel gains are physically impossible at 1.7 GHz
    - **Affected products:** Prom.ua 1700-2700 MHz MIMO panels advertised at 17 dBi or 24 dBi
    - **Frequency:** common
    - **Known fix:** Self-researched. Check gain against aperture: a 20 cm square tops out at about 12 dBi at 1.70 GHz, and a 43 cm square at about 18.7 dBi. Measure against a known helix on a Meteor pass.
    - **Fix sources:**
      - https://prom.ua/p1469825430-moschnaya-panelnaya-antenna.html
      - https://prom.ua/p2499424468-antenna-energy-mimo.html
  13.
    - **Problem:** The metal-plate lens focus shifts and the lens only works in one polarisation
    - **Affected products:** W1GHZ-type lens
    - **Frequency:** rare
    - **Known fix:** Make the plates 1-2 inches oversize, set the horn-to-lens spacing on the beacon, and keep the plates parallel to the E-field. That means rotating the lens 90° between the vertical narrowband transponder and the horizontal wideband one.
    - **Fix sources:**
      - http://www.w1ghz.org/antbook/chap3.pdf
- **Unresolved problems:**
  1.
    - **Problem:** No published report of QO-100 reception with a horn, a metal-plate lens, a zone plate or Fresnel lens, a 10 GHz patch array, or a Selfsat flat panel
    - **Why it matters for us:** The recommended 20-23 dBi conical horn and the optional 300 mm lens rest on estimates scaled from bare-LNB and dish reports, accurate to about ±3-4 dB. The horn should beat the bare LNB by about 10 dB, but whether typical SSB stations become comfortable copy is unproven. Self-test: log beacon C/N in 2.7 kHz with the bare LNB, then with the horn, on the same day. The horn should add 8-11 dB; if not, check throat fit and polarisation.
    - **Evidence:** Searches in English, German, Russian and Ukrainian, and checks of SatNOGS, SDR-Radio, EEVblog, Hackaday and WiMo/Passion Radio, found only bare-LNB reports (OK1DX, RigExpert, a Passion Radio review, SARTS) and dish or dish-feed reports. The BATC forum, mikrocontroller.net, groups.io and Reddit could not be read.
  2.
    - **Problem:** No dish-free Metop-B AHRPT decode found anywhere (helix, helix array, panel or Yagi)
    - **Why it matters for us:** The 2x2 helix array (about 0.3 m², 2-3 kg, $60-200) would be a first-of-its-kind build aimed at a single ageing satellite. NOAA OSPO (3 September 2026) lists Metop-C AHRPT as 'No'. NOAA POES is decommissioned, and FengYun-3 L-band is gone. The closest data point, Tysonpower's mid-gain antenna, failed to decode even NOAA HRPT.
    - **Evidence:** metislair lists a 60 cm dish as the minimum for Metop. All found dish-free L-band successes are Meteor-M HRPT, Elektro-L LRIT or NOAA HRPT (helix, helicone). https://www.ospo.noaa.gov/operations/metop/status.html
  3.
    - **Problem:** No amateur precedent and no ready software for coherent two-channel combining of HRPT (spatial or polarisation) on LimeSDR hardware
    - **Why it matters for us:** Both the 'two helix sub-arrays into RX1/RX2' idea and the 'dual-polarised panel with software RHCP' idea depend on it. LimeSuiteNG lacks channel alignment, and the LMS7002M flips phase by 0 or 180° on retune. A self-designed fix, not field-tested: lock the LO, then estimate the inter-channel delay once per stream by cross-correlation on the satellite signal and correct it with a delay block. Then track the complex weight w = E[x1·x2*]/E[|x2|²] over blocks of about 10-50 ms and add x1 + w·x2. That is an adaptive maximal-ratio combiner, which absorbs any fixed or flipped phase. Write the summed IQ to a file and feed it to SatDump. Simpler fallback: a passive 4-way Wilkinson combiner into a single RX, which needs no software alignment.
    - **Evidence:** https://discourse.myriadrf.org/t/limesdr-xtrx-rx-data-out-of-sync/13290 ; https://discourse.myriadrf.org/t/lms7002m-mimo-mode/2501 ; https://discourse.myriadrf.org/t/limesuiteng-and-mimo-phase-alignment-on-xtrx/8708 . A web search for amateur diversity combining for HRPT or LRPT returned only patents and theses.
  4.
    - **Problem:** No QO-100 beacon-lock tool found for the planned Ubuntu stack with a LimeSDR (SDR++ beacon lock not confirmed)
    - **Why it matters for us:** With a Goobay or other plain LNB (±300 kHz, or the -140 to -180 kHz F1ATB measured), SSB is unusable without lock. The AMSAT-DL tool (±2 kHz) is Pluto-only, and F1ATB's Remote-SDR targets the Raspberry Pi with HackRF or RTL. A self-designed fix: a GNU Radio Python block that FFT-peak-tracks the CW beacon at 10489.550 MHz, or the lower and upper PSK beacons (avoiding the DC centre), across a ±400 kHz window, then drives a frequency-xlating rotator. Or buy the 0.2 ppm QRO.cz TCXO LNB so a narrow tracker is enough.
    - **Evidence:** https://amsat-dl.org/en/qo-100-linux-transceiver/ ; https://f1atb.fr/qo-100-live/
  5.
    - **Problem:** Supply voltage versus polarisation for the QRO.cz/RemoteQTH LNB is documented inconsistently
    - **Why it matters for us:** WiMo's listing says '12 V horizontal, 15 V vertical'. Passion Radio's RemoteQTH pack says 12 V for the narrowband (vertical) transponder and 18 V for DATV (horizontal), which matches standard TV practice of 13 V vertical and 18 V horizontal. The wrong voltage on the 4S-pack bias-tee would select the wrong polarisation and lose the beacon. Verify on the beacon by switching voltage, or ask QRO.cz.
    - **Evidence:** https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz ; https://www.passion-radio.com/satellite-qo-100/converter-432-936.html
  6.
    - **Problem:** Real gain and match of the Ukrainian 4G MIMO panels at 1.70 GHz, below their 1710 MHz band edge
    - **Why it matters for us:** Only the 43 cm 'Energy MIMO 2x24' (about 2800-2950 UAH) is physically capable of about 15-17 dBi at 1.70 GHz (my aperture calculation). The 20-23 cm models cannot exceed 12-13 dBi. With no user reports, this needs a NanoVNA and an on-air comparison before it can replace the helix array.
    - **Evidence:** Prom.ua listings: R-Net 205x205 mm '17 dBi', Energy 230 mm '15 dBi', Energy 430x430 mm '24 dBi'. No HRPT reports with these panels were found.
  7.
    - **Problem:** Selfsat-type flat Ku panels at 10.489 GHz
    - **Why it matters for us:** It is the only flat shape with dish-class gain (about 31-33 dBi in band). But it is specified only from 10.7 GHz, with no QO-100 reports, and it uses a non-TCXO LNB and weighs 4+ kg. It stays a gamble and should not be bought for this build.
    - **Evidence:** Vendor specs only (satking.de, Conrad datasheet). Web searches found no amateur test.
  8.
    - **Problem:** Several key claims could only be seen in search-engine snippets because the source sites block automated readers
    - **Why it matters for us:** The BATC Bullseye drift threads (p=26716, p=27854), the wideband beacon MER ceiling (p=18655, p=37232) and the SARTS bare-LNB slide could not be read in full. Their figures should be treated as indicative.
    - **Evidence:** forum.batc.org.uk returns a JavaScript proof-of-work page (HTTP 503). The SARTS PDF returned 503 or connection reset.
  9.
    - **Problem:** Goobay external-reference modification failure (no signal, raised noise floor) never explained
    - **Why it matters for us:** It matters only if the €6 Goobay is modified instead of buying a TCXO LNB. Likely causes, untested: reference too weak or too strong, or the chip has a different crystal-oscillator topology. Prefer a ready TCXO LNB.
    - **Evidence:** Comment by 'Ali' (February 2024) on https://baltic-lab.com/2023/07/lnb-modification-for-10-ghz-qo-100-satellite-reception/
  10.
    - **Problem:** No field reports yet of the LimeSDR Micro M.2 used with an LNB or an L-band LNA chain
    - **Why it matters for us:** The board ships from about 30 September 2026. Its RX input overload level with an LNB (even after a 20 dB pad) and bias-tee handling (none on board, as far as found) are undocumented. Lime confirmed that the RX bands in the docs only show where matching is optimised, not coverage gaps, so the 740 MHz IF and 1.70 GHz are covered.
    - **Evidence:** https://discourse.myriadrf.org/t/limesdr-micro-m-2-pcie-frequency-range/13348
- **Communities checked:**
  - ok1dx.cz (OK1DX station page): readable
  - RigExpert application note TBR-AN-1: readable
  - Passion Radio product reviews (France): readable
  - WiMo product page (QRO.cz LNB): readable, no reviews
  - SatNOGS community forum (community.libre.space): readable through the Discourse JSON search and topic API; topics 11309, 12046, 11343, 2496
  - MyriadRF/Lime discourse (discourse.myriadrf.org): readable through JSON; topics 13348, 13290, 8708, 2501 and search results
  - SDR-Radio.com forum (phpBB): readable; beacon-lock and Pluto threads
  - BATC forum: blocked by JavaScript browser verification (HTTP 503); only search-engine snippets used
  - BATC wiki: readable (wideband bandplan, search)
  - Reddit (r/RTLSDR, r/amateursatellites and others): not reachable; WebFetch is blocked and the WebSearch domain filter was rejected
  - groups.io (QO-100 group): blocked by a JavaScript fingerprint wall
  - mikrocontroller.net: HTTP 403
  - Hackaday.io: search needs login; hackaday.com articles seen through search only
  - EEVblog forum: searched through WebSearch, no relevant threads
  - RTL-SDR.com articles and comments: Bullseye LNB, HRPT RSP2 tutorial, Elektro-L3 helix, Saveitforparts helicone, Tysonpower grid, TechMinds Inmarsat helix
  - blog.metislair.com: helix build and L-band reception guide
  - GitHub: SatDump issues through WebFetch (issue #727); LimeSuiteNG issues (issue #356). The gh search API is blocked in this session
  - Thingiverse (t0nito helicone): HTTP 403
  - AMSAT-DL (QO-100 Linux transceiver page)
  - F1ATB Remote-SDR page and comments
  - baltic-lab blog and comments (Goobay modification)
  - W1GHZ Microwave Antenna Book, chapters 2 and 3
  - SETI League helix article (qsl.net/seti)
  - DARC regional talks (DK3NB PDF) and OE3DSB station page (German)
  - SARTS Singapore QO-100 presentation: snippet only, download failed
  - Google Groups pnw-microwave: nothing relevant
  - NOAA OSPO Metop status page (updated 3 September 2026)
  - Prom.ua listings (Ukraine): readable; 5g.in.ua: Cloudflare challenge
  - Russian- and Ukrainian-language web searches: no dish-free QO-100 or HRPT community reports found
- **Recommendation impact:** QO-100:
  - Keep the plan, but reorder it. The TCXO LNB with no reflector is the only dish-free option with real field reports: OK1DX (CW beacon), RigExpert (FT8), a Passion Radio buyer, and SARTS (FT8, snippet only). Make it phase 1.
  - Prefer the 0.2 ppm QRO.cz/RemoteQTH TCXO LNB over the Goobay. Users report plain-LNB drift of 50-180 kHz, and the only ARM/Linux beacon-lock precedent (AMSAT-DL) covers just ±2 kHz. The Bullseye is acceptable if the software tracker captures at least ±30 kHz.
  - Always fit a 10-20 dB pad and a DC block. Operate outdoors, since glass blocks 10 GHz.
  - Verify which supply voltage selects which polarisation on the beacon; the QRO.cz documentation conflicts.
  - Phase 2: the 20-23 dBi conical horn. W1GHZ reports that his horns 'almost always' match their predicted gain. It is unvalidated on QO-100, so measure it against the bare LNB.
  - The W1GHZ metal-plate lens has a long real-world record (27.4 dBi measured, years of contest use) and remains the best non-dish path to near-dish gain.
  - DATV is definitively out. The wideband beacon's MER tops out around 8-11 dB even with large dishes.
  - Drop the Selfsat panel.
  
  L-band:
  - Keep the 11-turn helix or the helicone for Meteor-M HRPT and Elektro-L; there are several successful dish-free reports.
  - Apply the community fixes: at least 50 cm height, a bent-edge ground plane, a SAW LNA at the feed, shadowing cell towers, an RHCP winding over the ground plane, and a matching strip.
  - Downgrade the Metop-B 2x2 helix array from 'recommended' to 'experimental'. Nobody has decoded Metop without a dish, and Metop-B is the last L-band AHRPT source.
  - If the array is built, combine passively first (4-way Wilkinson into one RX). Do not rely on RX1/RX2 software combining until a custom delay-and-phase estimator is written. LimeSuiteNG lacks channel alignment (issue #356 open) and the LMS7002M flips phase after retune.
  - Treat a loop Yagi as an alternative to the array: one user found it far cleaner than a helix against terrestrial interference.
  - Remove the 20-23 cm Ukrainian 4G panels as Metop candidates; their aperture caps them at about 12-13 dBi at 1.70 GHz. Only the 43 cm 'Energy MIMO 2x24' class (about 2800-2950 UAH) is worth a NanoVNA and Meteor-pass test, for S-band experiments and possibly polarisation-combined L-band.
  
  Confidence: medium-high for the bare-LNB and helix findings; low for horn, lens, array and panel performance on these specific targets.

## Власні виправлення (`fixes`)

_Агент цього етапу ще працює (run `wf_5a66d65f-c3f`)._

