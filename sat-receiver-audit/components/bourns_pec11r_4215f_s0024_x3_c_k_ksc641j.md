# Bourns pec11r 4215f s0024 x3 c k ksc641j: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_071e1025-145`_

- **Part:** HMI set: Bourns PEC11R-4215F-S0024 encoders x3 (2 fitted + 1 spare), C&K KSC641J LFS IP67 keys x10, Adafruit 2055 35 mm knobs x2
- **Current pick:** Bourns PEC11R-4215F-S0024 x3 ($2.95, DigiKey) + C&K KSC641J LFS x10 ($0.70 at qty 10, DigiKey 108-KSC641JLFSCT-ND, 30,086 in stock, Active) + Adafruit 2055 x2 ($0.95, adafruit.com)
- **Current price usd:** 17.75 (8.85 + 7.00 + 1.90, ex VAT and shipping; all three lines re-checked 18 Oct 2026)
- **Decision:** replace_conditionally
- **Chosen:** Bourns PEC11R-4220F-S0024 x3 (UNCONDITIONAL: the same datasheet with a longer bushing thread, which the current part needs and lacks) + E-Switch TL3145BF350QJ x10 (CONDITIONAL on a bench test before the P7 keypad layout is frozen; if it fails, keep the KSC641J LFS) + Adafruit 2055 x2 (KEPT; no cheaper knob passes). All in the existing DigiKey order except the knobs.
- **Chosen price usd:** 13.64 (encoders 3 x 2.69 = 8.07 + keys 10 x 0.367 = 3.67 + knobs 2 x 0.95 = 1.90), ex VAT. 14.37 if 2 spare TL3145 are bought for the tests (12 x 0.367 = 4.40).
- **Saving usd:** 4.11 (23%) ex VAT: encoders 0.78, keys 3.33, knobs 0. 3.38 with 2 spare TL3145. With DigiKey EU VAT at 19-27% the gross saving is about 4.89-5.22. If the TL3145 fails its gate, the saving is 0.78 (encoders only).
- **Equivalence proof:** ENCODER: PEC11R-4220F-S0024 vs -4215F-S0024. I read the Bourns PEC11R datasheet REV.D04/26 (PDF text extracted locally). Both parts share one ordering code apart from the shaft length. Code 4 = PC pin horizontal / rear facing (DigiKey lists this as Vertical, Panel/PCB through-hole). Code 2 = 24 detents, 0024 = 24 PPR, F = metal flatted shaft, S = push momentary switch. Every published spec is identical:
  - Electrical: 10 mA @ 5 VDC; 100 Mohm @ 250 VDC; 300 VAC dielectric; bounce 2.0 ms max at 15 RPM; 60 RPM max.
  - Environment: -30 to +70 C operating, -40 to +85 C storage; IP40; shock 100 G; vibration 10-55 Hz at 1.5 mm.
  - Torque and load: detent 30-90 gf-cm, running 10-70 gf-cm, mounting 10.2 kgf-cm; side load 2.04 kgf min; 5 g max.
  - Life: 30,000 rotations min.
  - Switch: 20,000 cycles min, 610 +/- 306 gf, 0.5 +/- 0.3 mm travel, 100 mohm.
  - Mechanics: 6.0 mm metal shaft with the same 4.5 mm flat; metal M7x0.75 bushing; nut 2.0 +/- 0.2 mm and washer 0.5 mm supplied.
  The firmware is unchanged (4 counts per detent) and so are the footprint and filter.
  Only the shaft table differs (flatted shaft: L / LB / F):
  - 4215F: 15 / 5 / 7 mm.
  - 4220F: 20 / 7 / 10 mm.
  This makes the 4220F mechanically BETTER on a listed critical spec. Through the wall the nut stack is wall 2.4-3 mm + washer 0.5 + nut 2.0 = 4.9-5.5 mm, before adding any O-ring of about 1 mm. The 4215F's 5 mm thread cannot take that with a 3 mm wall even without an O-ring, and has only 0.1 mm to spare with a 2.4 mm wall. The 4220F's 7 mm thread takes the full 5.9-6.5 mm stack.
  DigiKey PEC11R-4220F-S0024-ND: $2.69 at qty 1, 9,155 in stock, Active, tray. The 4215F is $2.95.
  
  KEYS: TL3145BF350QJ vs KSC641J LFS. Sources: the E-Switch TL3145 datasheet dated 4.2.2024 (text extracted) and the C&K KSC series sheet via TME (text extracted).
  - Force: 350 +/- 80 gf, i.e. 2.65-4.22 N, which lies inside the KSC641's 3.4 +/- 0.85 N (2.55-4.25 N). The minimum force is slightly higher, which is better against accidental presses.
  - Life: 500,000 cycles at 350 gf vs 300,000. Better.
  - Travel: 0.5 mm (no tolerance given) vs 0.4 +/- 0.2 mm. Equal.
  - IP67 vs IP67. Equal.
  - Operating temperature: -40 to +85 C vs -40 to +85 C. Equal.
  - Contact resistance: 100 mohm max vs 100 mohm max. Equal.
  - Insulation: 100 Mohm min @ 500 VDC vs 10 Mohm @ 100 V. Better.
  - Dielectric: 250 VAC for 1 min vs 250 Vrms or more. Equal.
  - Maximum rating: 50 mA / 12 VDC vs 50 mA / 32 VDC. Irrelevant at 3.3 V.
  - Contacts: silver (Q) vs silver (LFS). Same metal class.
  - Body and termination: SMT J-lead, 6.45 x 6.45 mm vs 6.2 mm.
  - DigiKey: $0.367 at qty 10 cut tape, 5,989 in stock, Active.
  - TME independently gives 3.43 N, 500,000 cycles and a 0.5 mm stroke. DigiKey's '0.15 mm travel' and '3,000,000 cycles' conflict with the datasheet, which governs; 3,000,000 is the 180 gf figure.
  NOT PUBLISHED for the TL3145, so not proven equal (this is why the swap is conditional): bounce (C&K gives 1 ms or less), minimum switching current (C&K silver: 1 mA min, 20 mV), storage temperature (C&K: -55 to +85 C), reflow profile (C&K: IEC 61760-1), and actuator material and tactile feel (KSC6 is 'hard actuator, positive tactile feeling').
  Actuator height is 5.2 mm vs 7.7 mm. That is a mechanical change to the cap/boot stack, not a performance loss. The keypad PCB is not laid out yet.
  
  KNOBS: no candidate is both cheaper and not worse, so Adafruit 2055 stays ($0.95, 34.7 x 10.5 mm, snap-on; bore and D-flat not published).
- **Rejected:**
  1.
    - **Name:** C&K KSC441J ST1 LFS (same family, soft actuator, 5.2 mm)
    - **Why:** WORSE in force: 3.4 +/- 1 N on the C&K KSC sheet gives a 2.4 N floor, vs 2.55 N for the KSC641, so it gives less protection against accidental presses. It also has a soft actuator instead of a hard one (feel is worse or unproven) and 0.7 +/- 0.25 mm travel. It saves only $0.71.
  2.
    - **Name:** Alps Alpine SKRAAQE010 (SKRA IP67 3.43 N)
    - **Why:** WORSE in life: the Alps product page gives 'Operating life 100,000 cycles' vs 300,000. Bounce is not specified. Alps' own minimum order unit is 1,400 pcs (one reel). The qty-10 DigiKey price is UNVERIFIED.
  3.
    - **Name:** Alps Alpine EC11E15244G1 (the STACK 'EC11 + O-ring' budget line)
    - **Why:** WORSE. The Alps page gives 15,000 rotations vs 30,000, and 15 pulses / 30 detents vs 24/24, which means a firmware and tuning-step change. Alps' minimum order unit is 1,200/2,400 pcs, and the footprint differs. The STACK budget alternative fails the not-worse rule and should be deleted.
  4.
    - **Name:** Bourns PEC12R-xx20F-S0024
    - **Why:** WORSE build. The PEC12R datasheet REV 07/21 gives 'F = Insulated Flatted Shaft' (plastic, not metal), insulation of 10 Mohm vs 100 Mohm, and a 3 g body. The price was not checked.
  5.
    - **Name:** Same parts from TME (EU)
    - **Why:** Price and stock are UNVERIFIED and cannot be counted. TME's page shows 'Total: no-prices'. Its JSON-LD gives only ranges (PEC11R-4215F USD 1.27-1.72) and its stock conflicts ('0 in TME stock' vs inventoryLevel 779). TME has the TL3145BF350QJ OutOfStock. Buying there splits the order, so TME shipping comes on top. A cart check is possible later; it is not a verified saving.
  6.
    - **Name:** Generic unbranded EC11 encoders (AliExpress, about $1.04-1.09 each; plastic-shaft 5-packs)
    - **Why:** No life, bounce, torque, temperature or IP data. 30 detents vs 24/24. Shaft material is unknown or plastic. The EC11 footprint means a PCB change. No independent measurement exists.
  7.
    - **Name:** 'EC11E15244G1' sold on AliExpress (non-authorized seller)
    - **Why:** A brand part number from an unauthorized marketplace seller is a counterfeit risk, which breaks the legally-sold rule. Even if genuine, it fails on 15k life and 15/30 detents, as above.
  8.
    - **Name:** Generic IP67 6.2 mm tact 50-packs (AliExpress, $7.82 / $11.53)
    - **Why:** Not cheaper than 10 genuine KSC641J ($7.00). Force, life, travel, temperature and height are all unstated, and the IP67 claim is unverified.
  9.
    - **Name:** Generic silicone-gel 6.2 mm tact 30-pack ($1.09)
    - **Why:** No IP rating (sealing requirement fails), 3.1-5.0 mm heights, no force or life data.
  10.
    - **Name:** Generic knobs (35 mm aluminium $1.09 each; 29 mm plastic D-shaft 2-pack $1.09)
    - **Why:** The aluminium knob costs more ($2.18 vs $1.90), with an unconfirmed D bore and no dimple. The plastic knob is a 29 mm grip with no scrubber dimple, which is worse for gloved one-finger tuning.
  11.
    - **Name:** DIY AS5600 magnetic encoder + printed detent + separate key
    - **Why:** No proven detent or integrated push switch. It needs new firmware and pins (only GP22 is free) and has no measured life.
  12.
    - **Name:** Adafruit 2055 bought in the DigiKey order (searcher's idea)
    - **Why:** Not available. DigiKey searches for 'adafruit 2055' and 'scrubber knob' return nothing, and 1528-2055-ND is a different, discontinued Adafruit product (2325). The EU source is Kiwi Electronics at EUR 0.95 ex VAT, in stock.
  13.
    - **Name:** Batch rejects from search A: TT EN11-HSM1AF15, PEC11R-42xxK knurled, PEC11R-40xxF (no detents), Alps EC12E (no switch), Wurth WS-TASV 320 gf, Same Sky TS08 160 gf, C&K KSC643J LFG
    - **Why:** Each is more expensive, lower in force or detents, missing a switch, or not stocked. I accepted these as reported and did not re-verify each one individually, since none is a replacement.
- **Confidence:** medium
- **Conditions or tests:** ENCODER (no gate, CAD and build steps only):
  1. In CAD, keep the through-wall stack (O-ring + wall + 0.5 mm washer + 2.0 mm nut) at 6.5 mm or less, so at least 0.5 mm of the 7.0 mm thread is left.
  2. Measure the Adafruit 2055 bore depth and D-key length d on a first article.
  3. Trim the 4220F shaft by T so the knob skirt clears the nut by 0.5 mm or more, with T <= 10 - d, so the remaining flat (10 - T) is still at least d. The searcher's 'after trimming 3-4 mm the flat is still >= 7 mm' is wrong for 4 mm, which leaves 6 mm.
  4. Cut in a shaft vise before fitting the encoder, keep swarf out of the body, and deburr.
  5. Check the snap-on retention with a gloved pinch and spin (the same open item as before).
  
  KEYS (gate, run before the P7 keypad layout is frozen; buy 12 TL3145BF350QJ so 2 are spares):
  (a) Bounce: sample a Pico GPIO at 100 kHz or faster with the 2.2 k pull-up, 50 presses at room temperature and 50 after 1 h at -20 C. The last edge must come within 1 ms (C&K figure), and in every case within the firmware debounce window.
  (b) Reflow: put one coupon through the same reflow process as the keypad PCB. Then check that it actuates and that contact resistance is 100 mohm or less (voltage drop at 10 mA). Immerse it 30 min at 15 cm, dry the outside, and check that insulation is still 10 Mohm or more.
  (c) Gloved feel through the silicone keypad: 50 presses per key with winter gloves, zero misses, and zero accidental actuations in a 10 min handling drill.
  If any of these fail, keep the KSC641J LFS ($7.00) and its 6.2 mm footprint. Saving drops to $0.78.
- **Stack changes:** 1. BOM line 'Encoders, keys, knobs': PEC11R-4220F-S0024 x3 ($8.07, DigiKey PEC11R-4220F-S0024-ND) + TL3145BF350QJ x10 (or x12) ($3.67 / $4.40, DigiKey 141-TL3145BF350QJCT-ND) + Adafruit 2055 x2 ($1.90) = $13.64. Delete the 'Budget: EC11 with O-ring' note (it fails the not-worse rule: 15k life, 15/30 detents). Mark the knob source as Adafruit US or Kiwi Electronics NL (EUR 0.95 ex VAT); DigiKey does not list it.
  2. Case/CAD: the encoder bosses are designed for the 7 mm thread (O-ring + 2.4-3 mm wall + washer + nut <= 6.5 mm). The current 4215F would have needed a local counterbore of the wall; the 4220F does not. Add a shaft-trim step to the assembly instructions. The knob height and keypad stack are re-dimensioned in P7.
  3. Keypad PCB (P7): use the TL3145 land pattern from the E-Switch datasheet (6.45 mm body, J-lead) instead of the KSC 6.2 mm J-bend. Actuator height drops 7.7 -> 5.2 mm, so the silicone keypad plungers get 2.5 mm longer or the keypad PCB moves 2.5 mm closer to the panel. Keep the cap shapes and 19-21 mm pitch.
  4. Electrical (applies with either key): add external 2.2 kohm pull-ups to 3.3 V on the 6 key lines and the 2 encoder-push lines at the TCA9555, about $0.10 for 8 x 0603. The C&K sheet gives a 1 mA minimum for silver contacts; the expander's weak internal pull-up gives only tens of uA. With 2.2 kohm, 1.5 mA flows while pressed and nothing at idle. The TL3145 states no minimum, so the same fix applies. The encoder A/B 10k/10k/10 nF filter is unchanged.
  5. Firmware, rails, drivers, Ubuntu 24.04 arm64: none. The parts sit on the Pico/TCA9555; PIO stays at 4 counts per detent and the key debounce stays in firmware.
  6. Hard rules: passive HMI parts only, so there is no RF, TX, loop or signal-source implication.
  
  Verification limits: the shared WebSearch budget was exhausted (0 searches available to me). Mouser and Farnell returned 503. The TME page shows no price table. No independent bounce or feel measurements exist for either key.
- **Sources:**
  - https://www.bourns.com/docs/Product-Datasheets/PEC11R.pdf
  - https://www.digikey.com/en/products/result?keywords=PEC11R-4220F-S0024
  - https://configured-product-images.s3.amazonaws.com/Datasheets/TL3145.pdf
  - https://www.digikey.com/en/products/result?keywords=TL3145BF350QJ
  - https://www.tme.eu/en/details/tl3145bf350qj/microswitches-tact/e-switch/
  - https://www.tme.eu/Document/f93a4f13570c490b639b5e693f5d3fda/tactile%281%29.pdf
  - https://www.digikey.com/en/products/result?keywords=KSC641J%20LFS
  - https://www.tme.eu/en/details/pec11r-4215f-s0024/encoders/bourns/
  - https://www.adafruit.com/product/2055
  - https://www.digikey.com/en/products/result?keywords=adafruit%202055
  - https://www.digikey.com/en/products/result?keywords=scrubber%20knob
  - https://www.digikey.com/en/products/result?keywords=1528-2055-ND
  - https://www.kiwi-electronics.com/en/scrubber-knob-for-rotary-encoder-35mm-1812
  - https://tech.alpsalpine.com/e/products/detail/EC11E15244G1/
  - https://tech.alpsalpine.com/e/products/detail/SKRAAQE010/
  - https://www.bourns.com/docs/Product-Datasheets/PEC12R.pdf

