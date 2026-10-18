# Shielded hdmi lead adafruit 2420 2x wurt: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_071e1025-145`_

- **Part:** Shielded HDMI lead + 2 snap-on ferrites (Display group, core tier, qty 1 set): Q6A HDMI-A-1 to the Wisecoco HDMI-in board, HDMI-A to HDMI-A
- **Current pick:** Adafruit 2420 Slim HDMI 450 mm + 2x Wurth WE-STAR-TEC 74271140. As listed, this set cannot be built. The WE datasheet gives the 74271140 a cable range of 2.0-3.0 mm. The Adafruit/Kaweei drawing CHDMI-AM-AM-457 gives the 2420 an OD of 5.2 +/-0.15 mm. The smallest same-vendor core that fits is the 74271112 (4.5-6.0 mm), which makes the fitting set $18.71.
- **Current price usd:** 17.77 as listed ($9.95 Adafruit, in stock, rechecked 18 Oct 2026, + 2x $3.91 DigiKey). The fitting equivalent (2420 + 2x 74271112 at $4.38) is $18.71. Shipping and EU VAT are not included.
- **Decision:** replace_conditionally
- **Chosen:** Keep the Adafruit 2420 cable. Replace the 2x Wurth 74271140 with 2x Fair-Rite 0431164281 (Mix 31 Round Cable Snap-It, DigiKey 1934-1464-ND), with the cable built up to about 6.1-6.3 mm under each core and each closed core secured with a tie or heat-shrink band.
- **Chosen price usd:** 15.65 = $9.95 (Adafruit 2420, in stock) + 2x $2.85 (DigiKey 1934-1464-ND, qty-1 price, 103,515 in stock, Active, checked 18 Oct 2026). Ex VAT. Both items ride on the Adafruit and DigiKey orders the stack already places, so there is no extra shipping. EU VAT is added at the destination rate. Shim tape or heat-shrink comes from workshop stock and is not priced.
- **Saving usd:** 2.12 against the listed $17.77, or 3.06 against the set that actually fits ($18.71).
  Separate from this swap: the re-audit (D) already moved 1x 74271140 ($3.91) to the 2-3 mm touch-USB lead, and that ferrite needs its own BOM line under either option. If it is kept in this line, compare $19.56 with $22.62.
- **Equivalence proof:** CABLE: the same part, so every cable spec is unchanged. Per the drawing: 457 +/-15 mm, OD 5.2 mm, five pairs of 7/0.08 mm tinned copper (about 32 AWG), each pair with its own Al/Mylar foil and drain, an Al braid of 16x4x0.12 mm, gold-plated iron-shell plugs, all 19 pins wired, a drain wire to the shell at each end, and contact resistance of 3 ohm max.
  
  FERRITE, Fair-Rite datasheet (15 Sep 2026) against Wurth datasheets (rev 2025-09-10):
  1) Impedance per core, typical: 20/104/170/315/380 ohm at 1/10/25/100/250 MHz. Guaranteed minimum is the listed value less 20%, giving about 83/136/252 ohm at 10/25/100 MHz.
     - Listed 74271140: 92/178 ohm +/-25% (minimum 69/134). Fair-Rite is 1.8x higher.
     - Fitting 74271112: 175/316 ohm +/-25% (minimum 131/237). Fair-Rite typical is within 3%, and its guaranteed minimum is higher at both points.
     - Below 25 MHz Fair-Rite is higher (about 104 vs about 90 ohm at 10 MHz, 20 vs about 10 ohm at 1 MHz, the Wurth values read from its curve). That helps the HF+ chain.
     - At 250-300 MHz the two are about equal (380-400 ohm).
     - Above about 500 MHz neither datasheet gives usable data (the Fair-Rite curve shows a fixture rise, the WE curve falls to about 200 ohm at 1 GHz). At L-band the shield does the work for every option.
  2) Fit: the Fair-Rite chart puts 5.2 mm inside the 'will fit' band of 04XX164281 (about 4.9-6.1 mm) but below 'will grip' (about 6.1-6.3 mm). The bore is 6.30 mm minimum (DigiKey: 6.60 mm). Both vendors measure impedance with a thin wire in the bore (WE: AWG26, 100 mm), so the play affects how well the core is held, not its impedance, as long as the halves close fully.
  3) Flammability: UL94 V-0 on both.
  4) Envelope: 39.5 x 20 x about 19.6 mm, against 41 x 23.4 x 18 mm for the 74271112. Equal.
  5) Genuine source: Fair-Rite through DigiKey, an authorised distributor.
  
  NOT PUBLISHED for the Fair-Rite, so not proven equal; these are the reason for the conditions:
  - Operating temperature: WE states -50 to +105 C. The Fair-Rite polypropylene case states none.
  - AEC-Q200 qualification: WE has it.
  - WE-STAR-KEY safety lock: WE has it.
- **Rejected:**
  1.
    - **Name:** Listed set as is: 2420 + 2x Wurth 74271140
    - **Why:** The WE datasheet gives an applicable cable diameter of 2.0-3.0 mm, and the 2420 is 5.2 +/-0.15 mm. The core cannot close, so the line does not do its job. The fitting same-vendor set (2x 74271112) costs $18.71.
  2.
    - **Name:** 1x Wurth 74271111, or 2x 74271142 (3.5-5 mm)
    - **Why:** Per the 2420 drawing the OD is 5.2 +/-0.15 mm, which is above the 5.0 mm maximum of the range. The 4-5 mm figure from search 2 came from the contradictory Adafruit web text. A single core is also below the 2-core impedance sum on paper.
  3.
    - **Name:** Lindy 36960 0.3 m Anthra Line + 2x Fair-Rite 0431164281 (about $13.80 ex VAT, before shipping)
    - **Why:** The price is not real for an EU buyer, and the cable is a trade-off, not a not-worse analog.
  - Price and availability: Lindy 36960 is not stocked at DigiKey or TME. Lindy UK delivery terms cover the UK only (GBP 3.99 Royal Mail) and say nothing on EU delivery. The lindy.de and lindy.fr searches returned errors. The UK page shows both '22 In Stock' and 'out of stock'. Even GBP 3.99 of shipping makes it about $19.10, more than $18.71. The GBP/USD rate is unverified.
  - Specs worse on the Lindy page: jacket 6.0 mm against 5.2 mm, minimum bend radius stated as 48 mm, operating temperature -10 to +80 C.
  - Unproven: the page lists only 'Copper Braid, 65%' and gives no per-pair foil, while the 2420 drawing documents Al/Mylar per pair plus drain. ATC High Speed approval proves bandwidth, not EMI.
  - Better on paper: length, 30 AWG copper, a copper braid, and an 18 Gb/s rating. It is a possible deliberate upgrade only if the user accepts the OD and bend-radius penalty and an EU landed price of about $10 or less is confirmed.
  4.
    - **Name:** Lindy 36960 + 2x Laird 28A0593-0A2 (about $14.24)
    - **Why:** Note 3 on the Laird drawing (rev L) gives the case flammability as UL94 V-2, worse than V-0 on the Wurth and Fair-Rite. It also gives the case material as nylon. No operating temperature is stated. The core is 52.9 mm long. The Lindy price and spec problems above also apply.
  5.
    - **Name:** Delock 83352 0.25 m + 2x Wurth 74271131 (about $14.70-17.13)
    - **Why:** - Price: TME shows 'no-prices' for qty 1 (range $5.20-7.63) and conflicting stock (0 vs 16), and it would need a separate TME shipment.
  - Routing: the 7.3 mm OD is stiffer and bulkier than 5.2 mm.
  - Shielding: 'shielded twofold' only, with no braid material or coverage.
  - Ferrite: the 74271131 (125/235 ohm per re-audit D) is LOWER than the 74271112 (175/316) that fits the current cable.
  - Saving: about $0.64 at most against the listed set.
  6.
    - **Name:** Waveshare DIY HDMI adapters + 0.2 m EMI-shielded FFC (about $7.37)
    - **Why:** - Nothing documents a bond from the shield film to the plug shell, or which pins are wired.
  - The 0.5 mm-pitch FFC latch is weaker under handheld vibration.
  - Round snap cores do not fit a flat cable.
  - The price is a cached RobotShop snapshot.
  Worse, or at best unproven, in shielding and build.
  7.
    - **Name:** Adafruit FPC kit, 2x 3548 + 3560 ($14.50)
    - **Why:** Adafruit states these kits are 'not going to be as durable or shielded as ready-made cables'. Worse in the main job of this part. It stays in STACK only as the routing fallback, with a grounded copper-tape wrap.
  8.
    - **Name:** Adafruit 2197 flat HDMI 30 cm ($3.95)
    - **Why:** No datasheet: shielding, gauge, pin wiring and Type-A connectors are all unstated. Its flat profile does not take round snap cores. Cannot be shown not-worse.
  9.
    - **Name:** Generic AliExpress 15 cm 'HDMI 2.0' A-A ($1.09-4.83)
    - **Why:** Unbranded, store not identified, no shield or EMI data, and a risk of counterfeit HDMI logo use. Fails the genuine, traceable-source rule. At most a bench experiment after a teardown plus the A/B test.
  10.
    - **Name:** Generic unbranded clip-on ferrites
    - **Why:** No impedance or material data. Branded cheap examples are lower, for example RND at 60 ohm at 100 MHz against 178 ohm.
  11.
    - **Name:** Certified short cables (StarTech HDMM30CM 0.3 m, Roline Premium 1 m)
    - **Why:** More expensive ($12.09 and EUR 26.84 ex VAT). The StarTech certification is unconfirmed, and the Roline is 1 m long.
  12.
    - **Name:** Cable bundled with the display (4D 50 cm Mini-HDMI)
    - **Why:** Fits only the 4D fallback, 50 cm long, unknown shielding. Use for bench bring-up only.
  13.
    - **Name:** Fair-Rite 0461164281 (Mix 61) as the second core
    - **Why:** The 25 MHz impedance was not verified and is expected to be lower than Mix 31, so it does not meet the not-worse rule at 25 MHz.
- **Confidence:** medium
- **Conditions or tests:** If any of tests 1-3 fails, revert to 2420 + 2x Wurth 74271112 ($18.71); that combination is fully specified.
  1) Fit: build the 2420 jacket up to about 6.1-6.3 mm under each core, for example about 4 wraps of roughly 0.11 mm polyimide or PVC tape, or a thin-wall heat-shrink. The halves must close with no visible gap, and the core must not slide under a firm pull of about 5 N.
  2) Retention: put a cable tie or heat-shrink band around each closed core. This stands in for the WE safety key.
  3) Temperature: Fair-Rite publishes no operating range, so test one core on the cable.
     - Cold: 2 h at -20 C, then flex the cable and tap the cores. The latch must hold and the case must not crack.
     - Heat: 2 h at +70 C. The case must not deform.
  4) Acceptance, unchanged from STACK section 4: the display A/B test with HDMI on/off in the 151.50 and 127.90 MHz modes, E-field probe only (no H-field loops). Pass means no line at least 3 dB above the floor, a broadband rise of 0.5 dB or less, and a GNSS C/N0 change of 1 dB-Hz or less. Also run the HF+ A/B with the link on and off: Mix 31 should be equal or better below 25 MHz.
  5) Order check: the DigiKey line must read Fair-Rite 0431164281 / 1934-1464-ND.
- **Stack changes:** - BOM Display line becomes: 'Shielded HDMI lead Adafruit 2420 + 2x Fair-Rite 0431164281 (Mix 31, DigiKey 1934-1464-ND)', $15.65. This also brings the BOM in line with the STACK/integration text 'Mix-31/61 ferrites'. The 74271140 is 4W620 NiZn, not Mix 31/61, as re-audit D noted.
  - Keep 1x Wurth 74271140 ($3.91, DigiKey) as its own BOM line for the 2-3 mm touch-USB lead (D+/D-/GND only), per re-audit D. That cost exists under either option.
  - Case: reserve two core pockets of about 40 x 20 x 20 mm along the HDMI route. The listed 74271140 envelope was 32.4 x 19 x 13 mm, and the fitting 74271112 would need 41 x 23.4 x 18 mm anyway.
  - No change to rails, connectors (HDMI-A both ends), drivers, EDID, kanshi or the pin 18 series Schottky. The part is passive, so the receive-only, conducted-only, no-loop and other hard rules are unaffected.
  - Still open and not fixed by this swap: the 2420 is 457 mm long against the 10-15 cm spec. Lay the excess as a flat S-fold, never coiled, away from the RF bay and GNSS feed. No established-brand round 10-15 cm A-A cable was found.
  
  UNVERIFIED:
  - GBP/USD rate, the Lindy EU price, and Fair-Rite case and material operating temperature. My WebSearch budget for the turn was exhausted, so these were not searched further.
  - Ferrite impedance above about 500 MHz, for every option including the current one.
- **Sources:**
  - https://www.adafruit.com/product/2420
  - https://cdn-shop.adafruit.com/product-files/2420/C3242-002_CHDMI-AM-AM-457.pdf
  - https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/9036/431164281.pdf
  - https://www.digikey.com/en/products/result?keywords=0431164281
  - https://www.we-online.com/components/products/datasheet/74271112.pdf
  - https://www.we-online.com/components/products/datasheet/74271140.pdf
  - https://www.digikey.com/en/products/result?keywords=74271112
  - https://www.digikey.com/en/products/result?keywords=74271131
  - https://www.laird.com/document/datasheet/28a0593-0a2-datasheet
  - https://www.digikey.com/en/products/result?keywords=28A0593-0A2
  - https://www.lindy.co.uk/vat/ex/cables-adapters-c1/audio-video-cables-c107/0-3m-high-speed-hdmi-cable-anthra-line-p11154
  - https://www.lindy.co.uk/delivery-info-i5
  - https://www.digikey.com/en/products/result?keywords=lindy%2036960
  - https://www.tme.eu/en/katalog/?search=lindy+36960
  - https://www.tme.eu/en/details/delock-83352/hdmi-cables/delock/83352/
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md

