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

_Run `wf_5a66d65f-c3f`_

- **Component:** Antennas replacing the dishes: QO-100 at 10.489 GHz (LNB, IF about 739-740 MHz) and L-band HRPT around 1.70 GHz
- **Fixes:**
  1.
    - **Problem:** No published report of QO-100 reception with a horn, metal-plate lens, zone plate, 10 GHz patch array or flat panel. The 20-23 dBi horn figures are estimates scaled from bare-LNB and dish reports (about ±3-4 dB).
    - **Proposed fix:** Generate the missing data yourself. Build an optimum conical horn from W1GHZ's design rules: efficiency about 0.522, slant length L = d²/(3λ), λ = 28.58 mm at 10.4895 GHz. W1GHZ says built horns 'almost always' match prediction without tuning. Then measure it against the bare LNB on the same day, with a pass/fail threshold.
  
  Computed dimensions, all on a 20 mm inside-diameter throat:
  - 18 dBi: mouth 100 mm. Template arcs R_in 23.3 / R_out 117 mm, sector 154.3°.
  - 20 dBi: mouth 126 mm. Arcs 29.4 / 185 mm, sector 122.6°. Cone 146 mm long. Beam width about 16°.
  - 23 dBi: mouth 178 mm. Arcs 41.5 / 369 mm, sector 86.8°. Cone 318 mm long. Beam width about 11°.
  
  Correction to the earlier research: the lower beacon is at 10489.500 MHz, not 10489.550. It is constant-carrier FSK with 400 Hz shift. The PSK beacon is at 10489.750 MHz (AMSAT-DL bandplan).
    - **Steps:**
      - Throat: use 22 x 1.0 mm EN 1057 copper plumbing pipe (inside diameter 20.0 mm). Its TE11 cutoff is 8.79 GHz and TM01 is 11.48 GHz, so only one mode propagates at 10.49 GHz. Any throat must have an inside diameter between 16.8 and 21.9 mm.
      - Fitting the throat to the LNB: on the QRO.cz LNB, put the pipe in the POTY adapter, which replaces the white cap and is held by an M4 screw. On a Bullseye or Goobay, remove the cap and measure the waveguide inside diameter with calipers. Then make a sleeve, with a step under 1 mm or a 15-20 mm taper. Remove any dielectric plug.
      - Cutting the cone: use 0.3-0.5 mm copper, brass or tinplate, with a 6-8 mm overlap tab. Solder the seam closed and solder the small end to the pipe. ±1 mm tolerance is fine. A PETG print with copper foil also works if the foil seams overlap by at least 5 mm and are soldered. Alternatively, print the template from HDL_ANT.
      - Baseline measurement (same day, before fitting the horn): put the bare LNB on a tripod at 13 V and point it. Azimuth/elevation: Kyiv 186°/32°, Lviv 178°/33°, Kharkiv 193°/32°, Odesa 187°/36°. Record 60 s of IQ at 7.68 Msps with the LO at 738.9 MHz. Compute the C/N in 2.7 kHz of the 10489.500 and 10489.750 MHz beacons against noise at 10489.485-10489.495 MHz. That is the same noise window DJ0ABR's code uses.
      - Fit the horn and repeat within 30 minutes. Scan ±10° in 2° steps, and rotate the assembly in 15° steps, to find the peak.
      - Log C/N, ambient temperature and LNB current for both runs. This log becomes the missing field report.
    - **How to verify:** Pass if the horn's C/N minus the bare LNB's C/N is +8 to +12 dB for the 20 dBi horn, or +11 to +15 dB for the 23 dBi. The extra 1-3 dB beyond the directivity gain is expected, because the narrow beam sees less warm ground. If the gain is under +6 dB, check in this order: throat step or gap, seam continuity, polarisation rotation, a dielectric left in the throat, pointing.
  
  Independent check that needs no satellite: switch the SDR AGC off and compare noise power pointing at the Sun against 15-20° away. At about 300 sfu, expect about +0.4-0.5 dB for 20 dBi (ΔT about 7 K) and +0.7-0.9 dB for 23 dBi (ΔT about 14 K). A bare LNB rises less than 0.05 dB (ΔT about 0.7 K).
    - **Confidence:** medium
    - **Sources:**
      - http://www.w1ghz.org/antbook/chap2.pdf
      - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
      - https://amsat-dl.org/en/new-qo-100-band-plan/
      - https://github.com/dj0abr/QO100_Transceiver
      - http://ok1dx.cz/techinfo/qo100/qo100.html
      - https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
      - https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz
  2.
    - **Problem:** No dish-free Metop-B AHRPT decode exists anywhere. The 2x2 helix array would be a first-of-its-kind build aimed at one ageing satellite.
    - **Proposed fix:** Change the target instead of forcing Metop-B. New primary evidence:
  - The SatDump satellite list (satdump.org repo, July 2026) shows MetOp-C AHRPT at 1701.3 MHz as active and healthy.
  - The same list says MetOp-B 'suffers from intermittent modulator issues causing a distorted constellation and lower SNR than MetOp-C'. metislair puts the loss at about 7 dB since March 2025. That makes MetOp-B unreachable with about 18 dBic.
  - AWS PFM is active: 1707 MHz, QPSK at 1.785 Msym/s, about 1.2 dB less bandwidth than Metop, SatDump pipeline aws_pfm, end of life 2029 or later per WMO OSCAR.
  - The NOAA OSPO 'AHRPT: No' for Metop-C conflicts with SatDump. It most likely refers to NOAA's own service, not the satellite's transmitter, so verify it on air.
  
  Build the array in stages, with go/no-go gates measured on the existing single helix.
    - **Steps:**
      - Stage 0, measurement: use the existing 11-turn helix and a SAW-filtered LNA at the feed. Record one or more high Metop-C and AWS passes at 7.68 Msps on LimeSDR RX1. The LimeSuiteNG code sets a minimum of 7 Msps. Run SatDump offline with the metop_ahrpt and aws_pfm pipelines and log the peak SNR.
      - Decision gate: thresholds are SatDump's 4 dB plus 1 dB margin. If one helix reaches 2 dB or more, build 1x2: two helices into RX1/RX2 plus MRC (Fix 3) gives +3 dB, with no combiner and no phase matching. From 0 to +2 dB, build 2x2: two 2-way Wilkinsons into RX1/RX2 plus MRC, about +5 dB after roughly 0.4 dB combiner loss and 0.5 dB phasing loss. Below 0 dB, you need 0.4 m² or more of aperture (dish-class); stop. Expect MetOp-B about 7 dB below MetOp-C, so skip it.
      - Mechanics: space the helices 26-30 cm apart (1.5-1.7λ at 1.70 GHz) with boresights parallel within 2°. Use a common aluminium ground plane with about 3 cm bent-up edges. Mount at least 50 cm above ground and use buildings to shadow LTE towers.
      - RF: one SAW LNA per helix (SAWbird+ GOES class; metislair advises against SPF5189Z-type boards). Inside each Wilkinson pair, use equal-length coax within ±5 mm (about 15°, under 0.1 dB loss). Between RX1 and RX2, cable length does not matter, because MRC absorbs it.
      - Tracking: point and wait, re-aiming every 20-30 s using Gpredict and the BNO085 aid. The 2x2 beam is about 20°.
      - Storage: two channels of CS16 at 7.68 Msps is 61 MB/s, about 55 GB per 15-minute pass. Record to UFS and delete after decoding.
    - **How to verify:** On the same pass, compare SatDump SNR for RX1 alone, RX2 alone and the combined output. Combined should be +2.5-3 dB over the best single helix for 1x2, or +4.5-5.5 dB for 2x2. Success means a decode with RS-corrected frames and AVHRR imagery on medium and high passes.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
      - https://github.com/SatDump/SatDump/blob/master/resources/pipelines/AWS.json
      - https://github.com/SatDump/SatDump/blob/master/resources/pipelines/MetOp.json
      - https://blog.metislair.com/docs/Radio/L%20band%20weather%20satellite%20reception%20guide.html
      - https://space.oscar.wmo.int/satellites/view/aws_pfm
      - https://www.ospo.noaa.gov/operations/metop/status.html
      - https://user.eumetsat.int/s3/eup-strapi-media/TD_18_Metop_Direct_Readout_AHRPT_Technical_Description_v3_A_1cb789b653.pdf
  3.
    - **Problem:** No amateur precedent or ready software for coherent two-channel HRPT combining (spatial or polarisation) on LimeSDR hardware. LimeSuiteNG has no channel alignment, and the LMS7002M phase can flip by 0 or 180° on retune.
    - **Proposed fix:** A blind adaptive max-SNR (MRC) combiner. It has been designed, written and tested in simulation.
  
  What the LimeSuiteNG limesdr-micro branch (1 Oct 2026) shows:
  - LMS7002M_SDRDevice::SetFrequency ignores the channel argument. Both RX channels therefore share one SXR local oscillator, so their phase difference is constant within a tune, apart from the 0/180° divider ambiguity.
  - RX1 and RX2 go as analogue I/Q to LA9310 RX0/RX1 (per the docs).
  - Each channel has its own DMA pipeline, so a constant integer-sample offset between channels is possible.
  - Channel alignment (issue #356) is work in progress, and only for the LimeSDR-USB.
  
  The algorithm, in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dishfix_ag/mrc_combine.py:
  1. Find the integer lag by FFT cross-correlation, restricted to the signal band.
  2. For each 20 ms block, compute the band-limited 2x2 covariance and whiten it with out-of-band noise estimates. The principal eigenvector gives the weights, referenced to channel 0's phase.
  3. Output y = wᴴx as cf32 for SatDump.
  
  The same weights also form RHCP from a dual-polarised panel.
  
  Simulation results (sim_test.py):
  - Lags of 37 and -12 were recovered exactly, with a 180° phase offset and 0.3-0.8 rad/s phase drift.
  - Output SNR: +3.01 dB for equal branches; 3.76 dB from branches at 2 and -1 dB (the ideal MRC value); 0.00 dB from two branches at -3 dB.
  - Speed: about 1x real time on one x86 core.
    - **Steps:**
      - Install python3-soapysdr and the LimeSuiteNG Soapy plugin (driver key 'limesuiteng').
      - Capture: for both channels 0 and 1, set rate 7.68e6, the same frequency, antenna 'LNAW' and gain. Call setupStream(SOAPY_SDR_CS16, [0, 1]) and write the samples interleaved. Alternative: limeTRX --channelsmask 3 -o pass writes interleaved CS16 to .sigmf-data. However, limeConfig only configures channel 0, so set channel 1 through Soapy or an .ini file.
      - Combine: python3 -I mrc_combine.py pass.sigmf-data comb.cf32 --fs 7.68e6 --bw 4.5e6. Use --bw 3.4e6 for AWS and 1.5e6 for Meteor.
      - Decode: satdump pipeline metop_ahrpt baseband comb.cf32 out --samplerate 7.68e6 --baseband_format cf32 --dc_block
      - Check the printed lag peak/median ratio. If it is under 5, there was no common signal yet; re-run the estimate on a later part of the pass.
      - Bench test without a second antenna: split one helix+LNA output with a 2-way splitter and put a 30 dB pad on each branch, so the LimeSDR's own uncorrelated noise dominates. Feed RX1 and RX2 through different cable lengths. The combined SNR should rise about 3 dB, which proves the lag and phase handling works.
      - Guard against interference: band-limit to the satellite's bandwidth. Log the eigenvalue ratio per block; a sudden jump means a strong correlated interferer has captured the weights.
    - **How to verify:** On the bench test and on a real pass, the combined SatDump SNR should equal 10·log10(10^(SNR1/10) + 10^(SNR2/10)) within 0.5 dB. Also check for no phase jumps: the PLL stays locked across blocks, and the constellation stays clean.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro/src/boards/LimeSDR_Micro
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro/src/boards/LMS7002M_SDRDevice.cpp
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro/cli/limeTRX.cpp
      - https://github.com/myriadrf/LimeSuiteNG/issues/356
      - https://discourse.myriadrf.org/t/limesdr-xtrx-rx-data-out-of-sync/13290
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/digital.html
      - https://github.com/myriadrf/LMS7002M-docs/blob/master/LimeSDR-USB_channel_alignment_v01r00.pdf
      - https://github.com/SatDump/SatDump/blob/master/README.md
  4.
    - **Problem:** No QO-100 beacon-lock tool for the Ubuntu + LimeSDR stack.
    - **Proposed fix:** Confirmed gaps:
  - SDR++ has no beacon lock. Its source tree (July 2026) has only frequency_manager, scanner, rigctl_server, iq_exporter and recorder, and ppm correction exists only in the RTL sources.
  - SDRangel's Frequency Tracker corrects only its own channel, by at most fs/1000 per step, and needs an external reverse-API script.
  - AMSAT-DL's tool supports only the Pluto.
  
  So build a small GNU Radio 3.10 front end that feeds SDR++:
  - LimeSDR at 7.68 Msps goes into freq_xlating_fir_filter, decimating by 8 to 960 ksps. Its 'freq' message port, which takes a dict {freq: Hz} or a pair, is confirmed in the gr-filter source.
  - An embedded Python block runs the tracker in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dishfix_ag/qo100_beacon_track.py.
  - Acquisition searches ±400 kHz for the pair pattern: the lower beacon at 10489.500 MHz with the PSK beacon 250 kHz above it. Requiring both rejects strong SSB stations.
  - Tracking squares a 2 kHz slice around the BPSK beacon to remove the modulation. It sends the correction back to the 'freq' port each second.
  - The output goes to a TCP server sink, then to the SDR++ Network source.
  
  Simulated with a -163 kHz error drifting 3 kHz/min, plus 25 SSB-like carriers: acquisition landed within 30 Hz, and the tracking error stayed at 3 Hz or less at 13 dB C/N and 6 Hz or less at 4 dB C/N (bare-LNB level).
    - **Steps:**
      - sudo apt install gnuradio python3-soapysdr (GNU Radio 3.10 on Ubuntu 24.04). Then build LimeSuiteNG from the limesdr-micro branch with its SoapySDR plugin.
      - Soapy source: driver=limesuiteng, 7.68 Msps, LO 738.900 MHz, antenna LNAW. This keeps the NB transponder 0.6-1.1 MHz away from the DC spur; F1ATB also avoids using the beacon at the DC centre.
      - freq_xlating_fir_filter_ccc: decimation 8, taps firdes.low_pass(1, 7.68e6, 300e3, 100e3), initial centre +850 kHz.
      - Embedded Python block, a pass-through: buffer 1 s. On the first buffer, call acquire(). After that, each second compute resid = track(buf, 960e3, 0), set centre += resid, and publish a dict {freq: centre}. If the beacon score stays under 6 dB for 5 s, re-acquire.
      - blocks.tcp_server_sink(gr.sizeof_gr_complex, '127.0.0.1', 5555). In SDR++: Network source, TCP (Client), 127.0.0.1:5555, Float32, sample rate 960000. Set the source manual offset to 10489.750e6 so the display shows RF frequencies. Use SDR++ for SSB demodulation and recording.
      - Log centre against time. This also measures your LNB's drift, which F1ATB reports as -140 to -180 kHz across temperature for a plain PLL LNB.
    - **How to verify:** Over 30 minutes including warm-up and sun, the lower beacon should stay at 10489.500 MHz ±10 Hz on the SDR++ display. An SSB QSO should stay inside a 2.7 kHz filter without retuning. The correction log should look smooth, with no 250 kHz jumps from false locks.
    - **Confidence:** medium
    - **Sources:**
      - https://github.com/AlexandreRouma/SDRPlusPlus
      - https://github.com/f4exb/sdrangel/blob/master/plugins/channelrx/freqtracker/readme.md
      - https://github.com/gnuradio/gnuradio/blob/maint-3.10/gr-filter/lib/freq_xlating_fir_filter_impl.cc
      - https://amsat-dl.org/en/qo-100-linux-transceiver/
      - https://f1atb.fr/qo-100-live/
      - https://amsat-dl.org/en/new-qo-100-band-plan/
  5.
    - **Problem:** The supply voltage that selects each polarisation on the QRO.cz/RemoteQTH LNB is documented inconsistently.
    - **Proposed fix:** The sources disagree:
  - QRO.cz's own manual (hamparts.shop) gives 11-15 VDC and says power 'is switched between 12V and 18V to select V or H polarisation', without saying which is which.
  - WiMo says '12 V: hor, 15 V: vert'.
  - mikrocontroller.net and the BATC forum give the TV convention: about 13-14 V vertical, 18 V horizontal.
  
  Make the question irrelevant. With a rotationally symmetric conical horn or a bare LNB, rotating the LNB selects the polarisation. So fix the supply at 13.0 V and find the narrowband orientation empirically, once. The wideband DATV polarisation is not decodable without a dish anyway.
    - **Steps:**
      - Set a buck-boost module to 13.0 V, rated at least 0.5 A. A plain buck is not enough, because the 4S pack spans 12.0-16.8 V. The QRO.cz bias box draws about 400 mA typical; the Goobay up to 167 mA. Feed the bias-tee DC port through a 0.5 A polyfuse.
      - Point at QO-100 and tune the PSK beacon at IF 739.750 MHz.
      - Rotate the LNB/horn in 15° steps over 180° and log beacon C/N. Expect a maximum, and about 90° away a cross-polar minimum at least 15-20 dB lower. Mark the maximum position as 'NB @ 13 V'.
      - At that position, briefly feed 18 V from a bench supply. The beacon should fall by at least 15 dB. If it rises instead, this unit's convention is inverted; label it.
      - Clamp and mark the rotation. Polarisation skew from Ukraine is only a few degrees.
    - **How to verify:** Cross-polar ratio of at least 15 dB, and a beacon drop of at least 15 dB when switching 13 V to 18 V at the marked orientation.
    - **Confidence:** high
    - **Sources:**
      - https://hamparts.shop/blog/lnb-dual-lo-ref-manual.html
      - https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz
      - https://www.mikrocontroller.net/articles/QO-100_der_erste_geostationäre_Amateurfunkumsetzer
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
  6.
    - **Problem:** The real gain and match at 1.70 GHz of the Ukrainian dual-polarised 4G MIMO panels are unknown; 1.70 GHz is below their 1710 MHz band edge.
    - **Proposed fix:** The aperture limit already rules out the small panels. At 1.70 GHz:
  - 20-23 cm panels: at most 12.3-13.3 dBi even at 100% efficiency, and about 10-11 dBi at a realistic 60%.
  - 43 cm (Energy MIMO 2x24, about 2800-2950 UAH, price not re-verified): about 16.5 dBi at 60%.
  
  So only the 43 cm panel is worth testing. Its two ports into RX1/RX2, combined with the Fix 3 MRC script, give full RHCP gain with no 3 dB polarisation loss.
  
  Measure it three ways.
    - **Steps:**
      - S11 of each port on a NanoVNA that reaches at least 1.8 GHz (V2 or LiteVNA class; a NanoVNA-H is only usable to about 1.5 GHz). Accept -10 dB or better across 1.69-1.71 GHz, which means 0.46 dB or less mismatch loss.
      - Three-antenna Friis method, using helix #1, helix #2 and one panel port. Separation 5 m (the far field begins at about 2.1 m for the panel and 2.6 m for a 48 cm helix). Free-space loss is 51.0 dB at 1.70 GHz and 5 m. Mount everything 1.5-2 m high, outdoors. Use 0 dB polarisation loss for helix-to-helix (both RHCP, facing each other) and 3 dB for helix-to-linear. Solve: G_A = (L_AB + L_AC - L_BC)/2, where each L is the measured S21 plus FSPL plus the polarisation correction.
      - Sun-noise ratio: use the same SAW LNA and fixed LimeSDR gain, with AGC off, measuring 2 MHz around 1700 MHz away from LTE. ΔP = P_sun - P_cold-sky in linear units, and gain ratio = ΔP_A / ΔP_B. At about 80 sfu, expect ΔT about 14 K for a 13 dBic helix and about 29 K for a 16 dBi panel port.
      - On-air comparison: helix on RX1 and panel on RX2, on the same Meteor-M2-4 pass, with the same LO. Then move both panel ports to RX1/RX2 and apply MRC. Compare the SatDump SNRs.
      - For a geostationary reference: the SatDump list says Elektro-L3 transmissions are paused pending Elektro-L5 commissioning. FengYun-2H at 79°E sends a strong 1690.5 MHz carrier around each LRIT slot (every 3 h from 00:48 UTC), at a calculated elevation of 13-20° from Ukraine.
    - **How to verify:** The Friis and sun-noise gains should agree within 1.5 dB. Buy or keep the panel only if the MRC-combined panel beats a single helix by at least 2 dB on the same pass.
    - **Confidence:** medium
    - **Sources:**
      - https://prom.ua/Antenny-mimo-2x2.html
      - https://5g.in.ua/en/4g-3g-lte-antenna-panelnaya-energy-mimo-2-x-15-db-1700-2700-mgts/
      - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/rfcontrol.html
  7.
    - **Problem:** Selfsat-type flat Ku panels are unproven at 10.489 GHz.
    - **Proposed fix:** Do not buy one for this build. For close-to-dish gain without a dish, use the W1GHZ 300 mm metal-plate lens on the 20 dBi horn instead: 27.4 dBi measured at 10 GHz, about $10-25 in materials.
  
  If you test a panel anyway, buy from an EU shop with a 14-day return right and run a front-end test that needs no satellite before the beacon test.
    - **Steps:**
      - Power at 13 V with the 9.75 GHz LO (no 22 kHz tone), point at clear sky, and measure the IF noise density at 739 MHz (10.489 GHz RF) against 1000 MHz (10.75 GHz RF).
      - If 739 MHz is more than 3 dB below 1000 MHz, the panel's input filter is rolling off at 10.49 GHz. Expect at least that much loss in G/T. Return it.
      - If it is flat, run the Fix 1 beacon C/N comparison against the horn. Run beacon lock (Fix 4) because the LNB is not TCXO-stabilised. Mount on a tripod, since it weighs 4-4.5 kg.
    - **How to verify:** Noise-floor slope under 3 dB between 739 and 1000 MHz IF, and a beacon C/N at least 6 dB above the 23 dBi horn. Otherwise return it.
    - **Confidence:** medium
    - **Sources:**
      - https://asset.conrad.com/media10/add/160267/c1/-/de/000943058DS01/tehnicni-podatki-943058-selfsat-h-30-d-sat-antena-brez-sprejemnika-stevilo-udelezencev-1.pdf
      - http://www.w1ghz.org/antbook/chap3.pdf
  8.
    - **Problem:** Key BATC and SARTS figures could only be read as search snippets, because those sites block automated readers: Bullseye drift, the DATV MER ceiling and the SARTS bare-LNB slide.
    - **Proposed fix:** Replace the snippet-only numbers with your own measurements, and anchor on primary sources that can be read in full: OK1DX and RigExpert TBR-AN-1 for bare-LNB results, the AMSAT-DL bandplan, and F1ATB's drift data. The DATV MER ceiling no longer matters for the decision, because no non-dish option reaches the roughly 33 dBi needed.
    - **Steps:**
      - Bullseye drift: run the Fix 4 tracker log over a sunny afternoon and a cold night. The spec is ±10 kHz at 23°C and ±30 kHz from -20 to 60°C.
      - Bare-LNB C/N: take the Fix 1 baseline at your own site. It replaces the SARTS slide.
      - Archive the IQ files and logs, and post them to the BATC or AMSAT-DL forums. That turns this build into the missing first report.
    - **How to verify:** Your own logged C/N and drift numbers fall within the ranges quoted by the accessible sources (OK1DX, RigExpert, F1ATB), or explain any difference.
    - **Confidence:** high
    - **Sources:**
      - http://ok1dx.cz/techinfo/qo100/qo100.html
      - https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
      - https://f1atb.fr/qo-100-live/
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
  9.
    - **Problem:** A reader's Goobay external-reference modification failed (no test tone, raised noise floor), and this was never explained.
    - **Proposed fix:** Diagnosis, from the baltic-lab article (chip marked '3566E' with a 25 MHz crystal, LO = 390 x ref; about 3 Vpp injection through 2.2 µH plus 18 pF; current rose from 60 to 90 mA at lock) and the reader Ali's comment:
  (a) A rising noise floor when the reference is applied is the normal sign of a running LO: the LNB's amplified noise is being converted to IF. The LNB was probably working.
  (b) The test tone was the 3rd harmonic of a Pluto. That is very weak, and TV LNB input filters are specified only from 10.7 GHz.
  (c) The reference frequency sets the IF. 25.00 versus 25.78 MHz moves the LO by 304 MHz, so the IF may simply have been outside the window being watched.
  (d) The article is ambiguous about XTAL1 versus XTAL2. Injecting into the oscillator output pin, or overdriving it, can give an injection-pulled, noisy LO. Reciprocal mixing then raises the noise floor.
  
  Fix: use the real satellite as the test signal, and inject a clean sine of 0.5-1 Vpp into the oscillator input pin. Better still, buy a TCXO LNB: QRO.cz from €65 or Bullseye $29.95.
    - **Steps:**
      - Before modifying, check the stock Goobay on the QO-100 beacons: IF 739.500 and 739.750 MHz, with a ±300 kHz search (use the Fix 4 tracker).
      - Remove the crystal. Drive a 25.000 MHz 0.5 ppm TCXO (clipped sine, about 0.8 Vpp) through a 100 pF capacitor into one crystal pad, and leave the other pad open. Try both pads. The right one gives lock (the current step) AND a clean beacon line.
      - Judge the LO quality from the beacon: the PSK beacon spectrum should be narrow (a few hundred Hz), and the noise floor at 10489.49 MHz should equal its level with the stock crystal. A smeared beacon or a higher floor means a noisy LO; reduce the drive or move pins.
      - If it still fails after 2 hours of work, stop and buy a TCXO LNB.
    - **How to verify:** Beacons appear at the expected IF to within the TCXO error (±2.5 kHz at 9.75 GHz for 0.25 ppm), with beacon C/N within 1 dB of the stock-crystal LNB.
    - **Confidence:** low
    - **Sources:**
      - https://baltic-lab.com/2023/07/lnb-modification-for-10-ghz-qo-100-satellite-reception/
      - https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz
      - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
  10.
    - **Problem:** No field reports yet of the LimeSDR Micro M.2 used with an LNB or an L-band LNA chain. Its overload level and bias-tee handling are undocumented.
    - **Proposed fix:** What the official docs and code establish:
  - RX ports are RX*_W (0.7-2.6 GHz, LNAW) and RX*_L (0.3-2.2 GHz, LNAL), switched together for both channels by SKY13414 switches. Both 739 MHz and 1.70 GHz are covered.
  - No bias tee is documented. Lime forum users confirm none on the Mini or USB boards; the XTRX has only an optional one.
  - Both RX channels share one LO. You cannot receive the QO-100 IF on RX1 and L-band on RX2 at the same time.
  - Minimum sample rate is 7 Msps (LimeSuiteNG descriptor).
  
  Use an external chain and set levels by the noise-rise method.
  
  Level budget with a 60 dB gain LNB: output noise density is about -118.6 dBm/Hz (about -27 dBm over 1.5 GHz), plus the Ku TV carriers from 26°E. After a 30 dB pad, the density is -148.6 dBm/Hz, still about 20 dB above the Lime's estimated floor of about -169 dBm/Hz. The pad therefore costs less than 0.1 dB SNR and keeps total input around -57 dBm. Lime forum users advise staying below 0 dBm, citing an IIP3 of about +4 dBm.
    - **Steps:**
      - QO-100 chain: LNB, then F cable, then bias tee (13 V on the DC port), then DC block, then a 20-30 dB SMA pad, then an SMA-to-MHF4 pigtail into RX1. Try LNAW and LNAL and keep whichever gives the higher beacon C/N.
      - L-band chain: helix, then SAW LNA (3.3-5 V bias, about 50-110 mA), then coax, then bias tee (5 V), then DC block, then RX1 or RX2 on LNAW. SAWbird boards back-feed DC, so always keep a DC block on the SDR side.
      - Noise rise: compare the IF noise floor with the LNB/LNA unpowered and powered. Aim for 10-15 dB. Above 20 dB, add pad or reduce Lime gain. Below 8 dB, remove pad.
      - Compression check: insert an extra 3 dB pad. Signal and noise must both drop by exactly 3 dB. If their ratio changes, the chain is compressing.
      - Ordering: Crowd Supply now lists Basic $249 and GNSS $299, with pre-orders shipping 15 December 2026. Plan the first tests with the RTL-SDR V4/V4L, which can show the QO-100 IF and Meteor HRPT, but not the 4.5 MHz Metop signal at its 2.56 Msps.
    - **How to verify:** The noise rise lands in the 10-15 dB window, and the 3 dB-pad test shows unchanged C/N. Beacon C/N on the Lime equals or exceeds the same LNB on an RTL-SDR.
    - **Confidence:** medium
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.2/rfcontrol.html
      - https://myriadrf.org/projects/limesdr-micro/reference/M.2/v1.0/overview.html
      - https://github.com/myriadrf/LimeSuiteNG/blob/limesdr-micro/src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp
      - https://discourse.myriadrf.org/t/mini-2-0-rf-input-power-limits/8648
      - https://discourse.myriadrf.org/t/bias-tee-support-on-limesdr-mini/5893
      - https://discourse.myriadrf.org/t/bias-tee-option-on-limesdr-xtrx/13105
      - https://discourse.myriadrf.org/t/limesdr-micro-m-2-pcie-frequency-range/13348
- **Residual risks:**
  - The LimeSDR Micro schedule and price have changed. Crowd Supply (October 2026) lists Basic $249 / GNSS $299 with pre-orders shipping 15 December 2026, against $199 and about 30 September in the current stack. Dual-RX streaming on it has no field reports yet.
  - Both LimeSDR RX channels share one LO, so QO-100 IF and L-band cannot be received at the same time. The 7 Msps software minimum makes dual-channel recordings 56-61 MB/s, about 50-55 GB per 15-minute pass. The MRC script ran at about 1x real time on one x86 core; its speed on the Q6A was not measured.
  - The horn and lens figures for QO-100 are still predictions until the user's own A/B measurement. The absolute C/N estimate is ±3-4 dB, though W1GHZ reports that built horn gain matches theory.
  - L-band targets are uncertain. Metop-C AHRPT is 'active' per SatDump but 'No' per NOAA OSPO. Metop-B has a degraded modulator (about 7 dB loss reported). AWS EIRP is unknown and the signal fades at low elevation. Elektro-L3 transmissions are paused, and Elektro-L5 is sporadic.
  - The adaptive MRC can be captured by a strong in-band correlated interferer. Mitigate with band-limiting and the eigenvalue-ratio log.
  - The beacon tracker and MRC were validated only on synthetic signals, not on real hardware. Forum reports say the QO-100 beacon is occasionally jammed, so keep the re-acquire logic.
  - Prices and stock for the SAW LNAs (SAWbird+), Wilkinson combiners, the NanoVNA V2/LiteVNA and the 43 cm Energy panel were not re-verified here.
  - The Goobay reference-injection diagnosis is hypothesis-level; buying a TCXO LNB remains the low-risk path.
  - The helper scripts are in a shared, temporary scratchpad folder: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dishfix_ag/ (mrc_combine.py, qo100_beacon_track.py, sim_test.py). Copy them before the session ends.

## Адверсаріальна перевірка (`verify`)

_Run `wf_5a66d65f-c3f`_

- **Component:** Antennas to replace the dishes: QO-100 at 10.489 GHz (LNB, IF about 739-740 MHz) and L-band HRPT at 1.70 GHz
- **Recommendation holds:** так
- **Issues:**
  1.
    - **Claim:** Peak the antenna on the 'CW beacon at 10489.55 MHz (IF 739.55 MHz)' (research integration notes).
    - **Problem:** This is the wrong frequency. The AMSAT-DL narrowband bandplan gives the lower beacon at 10489.500 (CW/F1A, 400 Hz shift), the middle beacon at 10489.750 (400 bit/s BPSK), a multimedia beacon at 10489.9935 and the upper beacon at 10490.000 MHz.
    - **Correction:** Peak and measure C/N on 10489.500 and 10489.750 MHz, which is IF 739.500 and 739.750 MHz with the 9750 MHz LO. The own-fixes agent already corrected this.
    - **Source:** https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
  2.
    - **Claim:** Decoding the QO-100 wideband DATV beacon needs about 33 dBi or more.
    - **Problem:** This overstates the requirement by about 2 dB. BATC's measured beacon MER (10491.5 MHz, 1.5 MS, DVB-S2 4/5): 60 cm dish 6 dB, 70 cm 7 dB, 80 cm 8 dB, 1.2 m 10 dB, saturating near 12 dB. Fitting a saturation model to these puts the QPSK 4/5 threshold (about 3 dB MER) near a 40-45 cm dish, about 31 dBi.
    - **Correction:** The DATV beacon needs about 31-32 dBi, roughly a 45 cm dish. For DATV user signals, BATC recommends a dish of 90 cm or more. The conclusion is unchanged: the best non-dish options reach 27-28 dBi, so DATV stays out of reach.
    - **Source:** https://wiki.batc.org.uk/Receiving_Oscar_100_DATV_signals
  3.
    - **Claim:** The QRO.cz TCXO LNB costs 'from €65', and 13 V selects vertical, 18 V horizontal. Own fix: 'briefly feed 18 V' to check the polarisation.
    - **Problem:** €65 is only WiMo's cheapest variant, and WiMo shows €54.62 shipping on top. QRO.cz's own shop (hamparts.shop) prices the 10 MHz external-reference dual-LO LNB at €199 ex VAT (€240.79 incl.) and the bias-tee box at €63 ex VAT. WiMo states 12 V = horizontal and 15 V = vertical. The QRO.cz manual gives an 11-15 VDC supply range and about 400 mA typical draw. Applying 18 V would exceed the stated rating.
    - **Correction:** Budget about €120 delivered for the cheapest QRO.cz variant. On QRO.cz units, test polarisation with 12 V and 15 V only, never 18 V. The 13/18 V convention applies to the Bullseye and standard TV LNBs. Allow about 5 W for the QRO.cz box.
    - **Source:** https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz ; https://hamparts.shop/blog/lnb-dual-lo-ref-manual.html ; https://hamparts.shop/
  4.
    - **Claim:** 'Metop-B is the only live AHRPT source' (research) versus 'Metop-C is active, skip Metop-B' (own fixes).
    - **Problem:** Primary sources disagree:
  - NOAA OSPO (updated 3 Sep 2026): Metop-C AHRPT 'No', Metop-B 'Yes'.
  - WMO OSCAR (27 Aug 2026): Metop-C 1701.3 MHz 'not in use', 1707 MHz 'used part time'.
  - SatDump sat_list: both active at 1701.3 MHz, with Metop-B's 'intermittent modulator issues'.
  - metislair: about 7 dB loss on Metop-B since 03/2025.
    - **Correction:** Treat Metop AHRPT availability as unknown until checked on air. Before building any array, record high passes of both Metops with the single helix and look at both 1701.3 and 1707 MHz. Add AWS (1707 MHz, 1.785 Msym/s, 600 km orbit, active with end of life 2029 or later) as a parallel target.
    - **Source:** https://www.ospo.noaa.gov/operations/metop/status.html ; https://space.oscar.wmo.int/satellites/view/metop_c ; https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json ; https://blog.metislair.com/docs/Radio/L%20band%20weather%20satellite%20reception%20guide.html
  5.
    - **Claim:** Keep the 11-turn helix for Meteor-M HRPT and Elektro-L LRIT.
    - **Problem:** SatDump lists Elektro-L3 as 'transmissions paused pending Elektro-L5 commissioning', and L5 is 'still commissioning, with sporadic transmissions'. Even when L3 was on, metislair's 11-turn helix gave only about 1.5 dB equivalent on LRIT.
    - **Correction:** Meteor-M N2-3 and N2-4 HRPT (1700 MHz, both active) are the only verified dish-free L-band targets today. Count Elektro-L as opportunistic.
    - **Source:** https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json ; https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
  6.
    - **Claim:** The 30 cm W1GHZ lens gives 27.4 dBi when put in front of the 20-23 dBi horn.
    - **Problem:** The 27.4 dBi was measured at 10.368 GHz with a 17.5 dBi Gunnplexer horn at about 21 in (53 cm) focal distance. The 150 mm lens gave 20.9 dBi at about 8 in. A 20-23 dBi horn has a narrower beam and would under-illuminate the lens at that distance, losing gain. The plates must also be perpendicular to the waveguide's wide wall.
    - **Correction:** Feed the lens with a horn of about 17.5-18 dBi (mouth about 100 mm), or recompute the focal length in HDL_ANT for the horn you use. Recompute the plate curvature for 10.489 GHz. With 19.05 mm foam, the effective index changes from about 0.651 to about 0.661. Set the horn-to-lens spacing on the beacon.
    - **Source:** http://www.w1ghz.org/antbook/chap3.pdf (Table 3-1)
  7.
    - **Claim:** mrc_combine.py (own fix 3) combines a pass recorded from LimeSDR RX1 and RX2.
    - **Problem:** The algorithm is sound: I re-ran sim_test.py and it gives +3.01 dB for equal branches, 3.76 dB for 2/-1 dB branches, and recovers lags exactly. The file handling, however, fails on real passes:
  - It loads the whole interleaved CS16 file with np.fromfile and converts it to complex64. A 15-minute two-channel pass at 7.68 Msps is about 55 GB on disk and about 110 GB in RAM, so it runs out of memory on the 16 GB Q6A.
  - It estimates the lag from the first second only, which is noise if recording starts before the satellite rises, and applies the lag even when peak/median is below 5.
  - The docstring says the weights are interpolated, but the code holds them piecewise constant.
    - **Correction:** Read the file through np.memmap and process it in 2 s chunks. Scan 1 s windows across the pass and use the lag with the highest peak/median. Refuse to apply a lag whose ratio is below 5. Better still, run the combiner in a streaming GNU Radio graph and write only the combined, decimated output. That also cuts storage from about 55 GB to under 15 GB per pass.
    - **Source:** /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dishfix_ag/mrc_combine.py (reviewed and simulation re-run)
  8.
    - **Claim:** The QO-100 beacon tracker (own fix 4) acquires over ±400 kHz behind a decimate-by-8 freq_xlating filter (taps low_pass 300 kHz cutoff, 100 kHz transition, centred on the PSK beacon).
    - **Problem:** acquire() needs the lower beacon 250 kHz below the PSK beacon. Behind a 300 kHz low-pass, the lower beacon falls outside the passband whenever the LNB error is below about -50 kHz. Plain PLL LNBs are -140 to -180 kHz off (F1ATB), and the Goobay is specified at ±300 kHz. Even unfiltered at 960 ksps, errors below -230 kHz cannot be acquired. The simulation passed only because it fed unfiltered baseband directly.
    - **Correction:** Run acquisition on the 7.68 Msps stream, or on a decimate-by-4 branch with about ±800 kHz passband centred on 10489.625 MHz (IF 739.625). Then hand the coarse offset to the narrow tracker. With a Bullseye (±30 kHz) or a QRO.cz TCXO LNB, the bug is masked.
    - **Source:** /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dishfix_ag/qo100_beacon_track.py ; https://f1atb.fr/qo-100-live/
  9.
    - **Claim:** The LimeSDR Micro ($199, deliveries from about 30 Sept 2026) is the IF and L-band receiver.
    - **Problem:** Crowd Supply now lists Basic $249 and GNSS $299 (shipping $18 worldwide). Orders placed now ship 15 Dec 2026. The page does not mention a bias tee.
    - **Correction:** Start with the RTL-SDR V4/V4L, which works now and leaves the Lime free for L-band later:
  - The QO-100 narrowband transponder is only 500 kHz wide, which the RTL-SDR covers easily at the 739 MHz IF.
  - It also handles Meteor HRPT at 1.7 GHz on a helix.
  - The V4L listing gives no frequency range and warns that not all applications support it yet.
  - External bias tees and DC blocks are mandatory for both SDRs.
    - **Source:** https://www.crowdsupply.com/lime-micro/limesdr-micro ; https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
  10.
    - **Claim:** 'The 22 mm copper pipe in the POTY adapter is the natural horn throat.'
    - **Problem:** Unverified. Neither WiMo nor the QRO.cz manual gives the tube diameter, and BATC wiki pages mention POTY without dimensions. The Bullseye page gives no flange or feed dimensions.
    - **Correction:** Remove the LNB cap and measure the waveguide inside diameter before cutting anything. Single-mode TE11 at 10.49 GHz needs an inside diameter of 16.8-21.9 mm (both limits checked). A no-surgery alternative: a cone that clamps over the LNB's 40 mm feed, with gain confirmed by the bare-LNB A/B test.
    - **Source:** https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz ; https://hamparts.shop/blog/lnb-dual-lo-ref-manual.html
  11.
    - **Claim:** Community findings: 'RigExpert TBR-AN-1 gives no S/N figures.' Research: 'FT8 decoded at -12 to -14 dB.'
    - **Problem:** The note's WSJT-X screenshot shows decodes at -11 to -15 dB, so the research is right. The LNB used was not stock: it was modified for a GPSDO-locked 25 MHz reference, and the note says aiming within ±20° is enough.
    - **Correction:** Keep the bare-LNB evidence, but note it came from a reference-locked LNB. A stock TCXO LNB needs the beacon tracker for FT8 and SSB.
    - **Source:** https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
  12.
    - **Claim:** FengYun-3D/E/F/G/H AHRPT is X-band at 30-38.4 Msym/s.
    - **Problem:** Minor error: FY-3G sends AHRPT at 7790 MHz and only 6 Msym/s (drifting orbit), and FY-3F is LHCP. FY-3C, the last L-band FengYun, ended in 11-2024.
    - **Correction:** The conclusion is unchanged: there is no L-band FengYun-3, and X-band needs a tracked dish.
    - **Source:** https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
  13.
    - **Claim:** LimeSuiteNG issue #356 'Channel Alignment' was opened by Andrew Back.
    - **Problem:** It was opened by ztamosevicius on 29 Jul 2026. A port exists on a work branch (65 unit tests pass, not verified on hardware) and covers LimeSDR-USB first, then X3, XTRX and MMX8. The LimeSDR Micro is not mentioned.
    - **Correction:** The conclusion holds: there is no driver alignment for the Micro, so use the software MRC combiner or a passive combiner.
    - **Source:** https://github.com/myriadrf/LimeSuiteNG/issues/356
  14.
    - **Claim:** The 2x2 helix array gives Metop about 6-7 dB SNR on medium and high passes.
    - **Problem:** My own check against EUMETSAT's AHRPT spec: power flux density -133 dBW/m² per 1.5 MHz, up to about -128 dBW/m² converted from -154 dBW/m² per 4 kHz; QPSK 3/4 at 2.33 Mbit/s coded; reference station G/T 6 dB/K with a 1.8 m dish; assumed Tsys about 150 K.
  - Single 11-turn helix: about -1 to +3 dB Es/N0.
  - 2x2 array (about 17-18 dBic after losses): about 3-8 dB depending on elevation.
  The research figure is plausible only for passes above about 30°. Low passes stay under the 4 dB threshold, and Metop-B's modulator fault makes it unreliable.
    - **Correction:** Keep the array as experimental and gate it with the staged plan. Measure the single-helix signal as a spectral hump (in-band power against noise floor), because SatDump will not lock below threshold, so its SNR readout is meaningless there.
    - **Source:** https://user.eumetsat.int/s3/eup-strapi-media/TD_18_Metop_Direct_Readout_AHRPT_Technical_Description_v3_A_1cb789b653.pdf (Tables 3-4)
- **Forum and fix assessment:** The forum work is mostly sound and does change the recommendation in the right direction.
  
  QO-100, what holds up:
  - Dish-free narrowband reception is real and documented:
    - RigExpert decoded FT8 at -11 to -15 dB with an LNB alone (verified in the PDF screenshot; the LNB was GPSDO-referenced).
    - OK1DX copied the CW beacon (page was 503 today, so not re-read).
    - A Passion Radio buyer reports the same; SARTS only as a search snippet.
  - Nobody has published QO-100 results with a horn or lens. The horn and lens figures are physics-based estimates, and the horn geometry checks out:
    - 20 dBi: 126 mm mouth, 185 mm slant, half-angle 19.9°, cone 147 mm from a 20 mm throat.
    - 23 dBi: 178 mm mouth, 370 mm slant, cone about 319 mm.
    - Waveguide limits: TE11 cutoff at 16.8 mm and TM01 at 21.9 mm inside diameter.
  - W1GHZ's lens table is verified (17.5 / 20.9 / 27.4 dBi), but it was fed by a 17.5 dBi horn at 10.368 GHz.
  - The BATC MER table confirms DATV is out of reach for any non-dish option.
  - I could not find an independent anchor for the absolute narrowband beacon C/N; the 90 cm '>30 dB' figure has an unknown bandwidth. Keep the ±4 dB caveat and rely on the A/B measurement.
  
  QO-100 fixes:
  - The A/B horn test and the 'fix the supply voltage, rotate the LNB' method are good.
  - The 18 V step is unsafe for the QRO.cz unit (rated 11-15 V; WiMo gives 12 V horizontal / 15 V vertical).
  - The beacon-frequency correction to 10489.500/10489.750 is right.
  - The beacon tracker's algorithm works in simulation, but the proposed flowgraph has an acquisition bug: the 300 kHz low-pass removes the lower beacon for LNB errors below about -50 kHz. Acquire on the wide stream first.
  
  L-band, what holds up:
  - Meteor-M N2-3/N2-4 HRPT with an 11-turn helix (metislair, about 7 dB average) is the only proven dish-free target.
  - Elektro-L3 is paused. FengYun-3 L-band is gone. Metop status is contradictory across NOAA, WMO and SatDump. AWS at 1707 MHz is a valid new target.
  
  L-band fixes:
  - The staged go/no-go plan and the software MRC combiner are technically sound. I re-ran the simulation: +3.01 dB for equal branches.
  - mrc_combine.py will run out of memory on real 55 GB pass files and picks its lag from the first second only. It needs memmap/streaming and a lag search across the pass.
  - The Friis three-antenna and sun-noise methods are numerically correct (51.0 dB path loss at 5 m; about 14 K sun-noise rise for a 13 dBic helix at 80 sfu).
  - Metislair's recommended Sysmocom cavity filter (1525-1705 MHz) would block AWS at 1707 MHz. The SAWbird+ GOES (80 MHz passband centred on 1688 MHz) passes everything from 1700 to 1707 MHz.
  
  Search limits: the shared WebSearch budget was exhausted before this review started (all three searches refused). No new forum searches were possible (for horn or Selfsat QO-100 reports, or dish-free Metop decodes), so this review relies on WebFetch of primary sources.
- **Final recommendation:**
  - **Name:** QO-100: Othernet Bullseye TCXO LNB, first used bare, then with a DIY optimum conical horn (20 dBi handheld, then 23 dBi on a tripod), optionally adding a 300 mm W1GHZ metal-plate lens fed by a ~17.5-18 dBi horn for about 27 dBi. Upgrade path: the QRO.cz 0.2 ppm TCXO LNB with POTY adapter. L-band: keep the 11-turn RHCP helix with a SAWbird+ GOES at the feed for Meteor-M N2-3/N2-4 HRPT. A 1x2 or 2x2 helix array for Metop-C/AWS stays experimental, built only after on-air gating.
  - **Price:** QO-100:
  - Bullseye: $29.95 (rtl-sdr.com, 70 in stock; shipping to Ukraine not verified).
  - Horn materials: about $5-20.
  - Lens: about $10-25 in aluminium foil and 19 mm XPS foam.
  - Power inserter, DC block and pad: about $15-30 (not verified).
  - QRO.cz alternative: €65 plus €54.62 shipping at WiMo.
  L-band:
  - SAWbird+ GOES: $44.95 (Nooelec).
  - Helix materials: about $5-20.
  - Array option: about 4 x $44.95 = $180 in LNAs, plus combiner and materials.
  - **Sources:**
    - https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
    - https://www.wimo.com/en/qo-100-10ghz-lnb-qro-cz
    - https://amsat-dl.org/en/p4-a-nb-transponder-bandplan-and-operating-guidelines
    - https://rigexpert.com/files/product_documentation/gpsdo/TBR-AN-1.pdf
    - http://www.w1ghz.org/antbook/chap2.pdf
    - http://www.w1ghz.org/antbook/chap3.pdf
    - https://wiki.batc.org.uk/Receiving_Oscar_100_DATV_signals
    - https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-goes.html
    - https://blog.metislair.com/docs/Radio/Creating%20a%20helix%20for%20direct%20satrx.html
    - https://blog.metislair.com/docs/Radio/L%20band%20weather%20satellite%20reception%20guide.html
    - https://github.com/SatDump/satdump.org/blob/master/sat-list/sat_list.json
    - https://user.eumetsat.int/s3/eup-strapi-media/TD_18_Metop_Direct_Readout_AHRPT_Technical_Description_v3_A_1cb789b653.pdf
    - https://www.ospo.noaa.gov/operations/metop/status.html
    - https://space.oscar.wmo.int/satellites/view/aws_pfm
  - **Why:** QO-100:
  - Bullseye over QRO.cz: in stock at $29.95 against about €120 delivered. Its ±10-30 kHz drift is handled by the (corrected) beacon tracker, which you need for SSB anyway. Its 25 MHz reference output is a bonus.
  - Bare-LNB reception of the beacon and FT8 is documented, so the horn's estimated +10-13 dB goes directly into SSB quality: about 14-17 dB beacon C/N in 2.7 kHz (±4 dB).
  - The 300 mm lens is the only non-dish path to about 27 dBi. That makes typical SSB stations readable.
  - DATV needs about 31-32 dBi (BATC MER data), which no non-dish option reaches.
  
  L-band:
  - Meteor-M N2-3/N2-4 HRPT is the only target with real dish-free decodes. Elektro-L3 is paused, FengYun-3 L-band has ended, and Metop availability is contradictory across sources.
  - The EUMETSAT flux-density spec puts a single helix below the Metop threshold, and a 2x2 array (about 0.16 m², the same aperture as metislair's 60 cm minimum dish) at roughly 3-8 dB, so only high passes would decode.
  
  First receiver: use the RTL-SDR V4/V4L for both bands now. The LimeSDR Micro ships 15 Dec 2026 at $249.
- **Final budget option:**
  - **Name:** Bare Bullseye TCXO LNB, then a tinplate or copper ~18-20 dBi conical horn from an HDL_ANT template, into the RTL-SDR V4/V4L through a 13 V power inserter, DC block and 10-20 dB pad, with the fixed beacon tracker. For L-band, a single 11-turn helix with a SAWbird GOES barebones on the same RTL-SDR, for Meteor-M HRPT only.
  - **Price:** About $95-130:
  - Bullseye: $29.95.
  - SAWbird GOES barebones: $39.95 (30 mA, so the RTL-SDR's 4.5 V bias tee can power it).
  - Horn and helix materials: about $10-30.
  - Power inserter, DC block, pad and 13 V buck-boost: about $15-30 (not verified).
  Shipping is extra.
  - **Why:** This keeps every verified dish-free result: QO-100 beacon, FT8, CW and beacon-level SSB, plus Meteor HRPT. It uses the SDR the user already owns, so it works before the LimeSDR Micro ships. It drops Metop, AWS, DATV and weak SSB. The Goobay €5.90 PLL LNB is cheaper, but its ±300 kHz stability could not be verified and needs a wide-acquisition tracker.
- **Known problems and fixes to apply:**
  - The LNB's 50-66 dB gain overloads the SDR. Fit a DC block and a 10-20 dB pad for the RTL-SDR, or 20-30 dB for the LimeSDR. Aim for a 10-15 dB noise rise when the LNB is powered, and confirm with the 3 dB-pad compression test.
  - Polarisation and supply voltage:
  - Bullseye and standard LNBs: 13 V vertical (narrowband), 18 V horizontal.
  - QRO.cz: rated 11-15 V (WiMo: 12 V horizontal, 15 V vertical). Never apply 18 V.
  - Fix the voltage, then rotate the LNB or horn in 15° steps to find the beacon maximum. Expect at least 15 dB cross-polar rejection.
  - Use a buck-boost, not a plain buck, because the 4S pack swings 12-16.8 V. Add a 0.5 A polyfuse.
  - Beacon frequencies are 10489.500 MHz (CW/FSK) and 10489.750 MHz (BPSK), i.e. IF 739.500 and 739.750 MHz. Do not use 10489.55.
  - Beacon tracker: acquire on the wide stream (7.68 Msps, or ±800 kHz centred on IF 739.625) before narrowing to 960 ksps with a 300 kHz low-pass. Otherwise the lower beacon is filtered out for LNB errors below about -50 kHz. Keep the re-acquire logic for times when the beacon is off or jammed.
  - Operate outdoors with a clear path to 25.9°E. OK1DX found that 10 GHz did not pass through window glass. Pointing: Kyiv 186°/32°, Lviv 178°/33°, Kharkiv 193°/32°, Odesa 187°/36°.
  - Horn build:
  - Measure the LNB waveguide inside diameter first; it must be 16.8-21.9 mm for single-mode operation.
  - Remove any dielectric plug, keep any step under 1 mm or taper it, and solder the seams.
  - 20 dBi: 126 mm mouth, cone 147 mm. 23 dBi: 178 mm mouth, cone about 319 mm (from a 20 mm throat).
  - Validate against the bare LNB on the same day; expect +8 to +12 dB (20 dBi) or +11 to +15 dB (23 dBi).
  - Lens:
  - Feed it with a horn of about 17.5-18 dBi, or recompute the focal length in HDL_ANT.
  - Recompute the curvature for 10.489 GHz.
  - Make the plates 1-2 inches oversize, keep them parallel to the E-field, and set the horn-to-lens spacing on the beacon.
  - L-band LNA:
  - Put one SAWbird+ GOES ($44.95, 180 mA) or SAWbird GOES ($39.95, 30 mA) at each feed. Avoid SPF5189Z-type wideband boards.
  - Keep a DC block on the SDR side, because the SAWbird back-feeds DC when powered over USB.
  - If you add a cavity filter, do not use the Sysmocom 1525-1705 MHz part when targeting AWS at 1707 MHz.
  - Helix site practice:
  - Mount it 50 cm or more above ground and vary the height during the pass.
  - Bend up the ground-plane edges (about +1.5 dB) and rotate the helix (about +1 dB).
  - Shadow cell towers with buildings or trees, and put phones in airplane mode.
  - Wind it RHCP, since it sits over a ground plane.
  - Match its 140-150 Ω feed impedance and check with a NanoVNA that reaches 1.8 GHz or more.
  - Before building any array:
  - Record Metop-B and Metop-C (check both 1701.3 and 1707 MHz) and AWS (1707 MHz) with the single helix.
  - Measure the signal as a spectral hump; SatDump's SNR readout is meaningless below lock.
  - Build 1x2 or 2x2 only if the gates pass. Expect decodes only on passes above about 30°. Skip Metop-B, whose modulator loses about 7 dB intermittently.
  - mrc_combine.py:
  - Switch to np.memmap and chunked processing; a 15-minute two-channel pass is about 55 GB.
  - Search the whole pass for the lag with the highest peak/median, and reject any below 5.
  - Or combine in a streaming GNU Radio graph and store only the combined, decimated output.
  - Do not plan on Elektro-L3 (paused) or FengYun-3 L-band (ended 11-2024). FengYun-2H S-VISSR at 1687.5 MHz (79°E, about 16-17° elevation from Kyiv, linearly polarised) can serve as a fixed reference to compare L-band antennas without tracking.
- **Missed better options:**
  - Use the RTL-SDR V4/V4L, which the user already owns, as the QO-100 IF receiver. The narrowband transponder is only 500 kHz wide at a 739 MHz IF. The same RTL-SDR also handles Meteor HRPT. This frees the LimeSDR Micro, which ships only on 15 Dec 2026 at $249, for wideband and L-band work. The V4L has software-compatibility caveats.
  - AWS (Arctic Weather Satellite): 1707 MHz, 1.785 Msym/s, 600 km orbit (Metop is at 830 km), active with end of life 2029 or later, SatDump pipeline aws_pfm. It is a possibly easier second L-band target than Metop. Its transmit power is not published, and it fades at low elevation.
  - FengYun-2H at 79°E (S-VISSR at 1687.5 MHz, plus a test-pattern carrier at 1690.5 MHz every 3 hours). It is a geostationary signal for measuring and comparing the helix, array and panel at 1.69 GHz without tracking. Polarisation is linear, so subtract 3 dB in absolute terms.
  - The Bullseye's 25 MHz reference output (red F connector) is unused in every plan. It is a stable reference that could be logged or compared against the SDR clock.
  - A cone that clamps over the LNB's 40 mm feed, as a no-surgery alternative to removing the cap and inserting a throat tube. Its gain is not predicted in advance, so verify it with the A/B beacon test.
- **Remaining uncertainties:**
  - No published QO-100 reception with a horn, lens, zone plate or flat panel. The absolute beacon C/N estimates (about 28 + G dB-Hz) rest on an anchor of unknown bandwidth (the BATC 90 cm '>30 dB' snippet), so treat them as ±4 dB until your own A/B measurement.
  - Metop AHRPT status conflicts across NOAA OSPO (Metop-C 'No'), WMO OSCAR (Metop-C 1701.3 'not in use', 1707 'part time') and SatDump (both active at 1701.3). Only an on-air check resolves it.
  - AWS transmit power and decode threshold are unknown, as is Meteor-M HRPT transmit power. My Metop link budget assumes Tsys of about 150 K and that the EUMETSAT flux-density range is -133 to about -128 dBW/m² per 1.5 MHz.
  - The internal waveguide diameter of the Bullseye and Goobay LNBs, and the POTY tube diameter, could not be verified.
  - Shipping of the Bullseye (rtl-sdr.com store) and of QRO.cz/WiMo to Ukraine, and the delivered prices, were not verified.
  - The Goobay 67269 specs (±300 kHz, €5.90) could not be re-checked; the Passion Radio pages return a redirect loop.
  - The RTL-SDR V4L frequency range (whether it reaches 1.7 GHz) and its software support are not stated on the store page.
  - The LimeSDR Micro's 7 Msps minimum sample rate, dual-RX streaming and RX overload level with an LNB have no field reports yet.
  - The OK1DX page returned HTTP 503 today. Its bare-LNB findings were taken from the earlier agents' reading.
  - The shared WebSearch budget was exhausted, so no new forum searches were possible (Selfsat on QO-100, horn on QO-100, dish-free Metop or AWS). Only WebFetch of primary sources and the SatNOGS Discourse search, which found nothing, were used.
- **Confidence:** medium

