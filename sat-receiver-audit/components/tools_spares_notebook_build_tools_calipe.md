# Tools spares notebook build tools calipe: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** Tools, spares, notebook, build tools (bench tier, group Tools, qty 1 set; STACK.md line 356)
- **Current pick:** STACK line 356 is a cost model with no SKUs: spares kit, notebook and labels, organiser, the build tools (calipers, snips + deburrer, M5 tap and die, heat gun), and the hand-tool roll that radio_lab.json reconstructs (iFixit Mako, flush cutter, stripper, tweezers, spudger).
- **Current price usd:** 245-400 (model, unverified, no breakdown in STACK)
- **Decision:** replace_conditionally
- **Chosen:** Replace the cost model with these named SKUs. All are EU stock.
  
  BUILD TOOLS
  - Calipers: Goobay 77001, 0-150 mm (reichelt). CONDITIONAL on the acceptance test. Fallback: SCALA 230.207-X (TME).
  - Snips: Stanley 2-14-556 MaxSteel, straight pattern, 250 mm (TME).
  - Deburrer: swivel deburrer from reichelt (C.K T2281, Gedore 8730 or RUTHEX HSS set). Blade type unverified.
  - Tap: Völkel 90530 M5x0.8, HSS-E, ISO2/6H, through-hole (TME).
  - Die: Völkel 27434 M5x0.8, HSS, DIN 223, 6g, 20x7 mm (TME).
  - Die stock: Völkel 15003, 20x7 mm (TME).
  - Tap wrench: Völkel 14010, DIN 1814, steel, M1-M10 (TME).
  - Heat gun: Steinel HL 1821 S (TME).
  
  HAND-TOOL ROLL
  - iFixit Mako 64-bit, from the iFixit EU store (ships from DE). Same SKU as now.
  - Flush cutter: Knipex 78 61 125 (TME).
  - Stripper: Jokari 40026 PWS-Plus (TME). Add Jokari 20050 only if the battery path is wired in 18 AWG.
  - ESD tweezers: Bernstein 5-089-13 or Knipex 92 78 77 ESD (reichelt).
  - Spudger and an 8 mm open spanner (unverified).
  
  OTHER
  - Notebook: Rite in the Rain No. 373 via an EU reseller (EU price unverified), plus labels.
  - Organiser: unverified.
  - Spares kit: Search B's de-duplicated kit (only spares no other STACK line already carries), corrected in two ways:
    - It keeps 2 spare MHF4L-SMA pigtails. The 2 pigtails in the Lime line are the installed ones, and the Lime stays per the 18 Oct decision.
    - It uses SMBJ13A and SMBJ17A, not SMBJ14A.
  
  KNOCK-ON ADDITION
  - SCALA 533.501 0-25 mm micrometer (TME). The G3 nickel goods-in check (0.15 +/- 0.01 mm) needs it, and it also serves as the reference for the caliper acceptance test.
- **Chosen price usd:** About 335-391 incl. 19% DE VAT, at TME single-unit prices (the structured-data highPrice), excl. shipping for two parcels (TME + reichelt).
  
  Breakdown:
  - Build tools 128.0-134.7:
    - Goobay caliper 21.35 (EUR 18.99)
    - Stanley 17.96
    - Deburrer 15.73-22.47
    - Völkel tap 5.02, die 7.53, die stock 5.74, wrench 15.10
    - Steinel 39.56
  - Roll 124.5-133.3:
    - Mako 44.91 (EUR 39.95)
    - Knipex 26.37
    - Jokari 29.17
    - Tweezers 19.10-22.82
    - Spudger and spanner 5-10
  - Notebook and labels 15-25; organiser 10-20; spares 57-78.
  
  Plus the micrometer: 41.66. Possible add-ons:
  - SCALA caliper fallback: +22.49
  - HL 1920 E upgrade: +40.14
  - Jokari 20050 if 18 AWG: +28.63
  
  FX 1.1241 USD/EUR (stack). TME prices are treated as net.
- **Saving usd:** No net saving against the model as a whole. The verified named set lands at 335-391 incl. VAT, the upper half of 245-400, plus 41.66 for the micrometer gap. The 245 low end cannot be reached with documented-spec tools once EU VAT is added.
  
  Proven savings inside the line:
  - Spares de-duplication: same part numbers, 80-130 down to 57-78, so 23-52 saved. That is less than Search B claimed, because the 2 MHF4 spares are added back.
  - Goobay 77001 instead of SCALA 230.207-X: 22.49 saved, conditional on the test.
  - Buying every item EU-side avoids the EUR 3 per-line duty and the EUR 2 handling fee (operator notes 34/35).
- **Equivalence proof:** The current line names no part, so the reference is the requirement floor taken from the stack. These items are verified against it.
  
  CALIPERS
  - Goobay 77001 (manual REV2019 and reichelt page): 0-150 mm, 0.01 mm reading, error limit 30 um per DIN 862, repeatability 0.01 mm. Hardened stainless; outside, inside, depth and step measurement; LR44 cell; no radio.
  - SCALA 230.207-X (SCALA catalogue, Type 230): 0-150 mm, 40 mm jaws, 0.01 mm, 'DIN 862' with no figure printed. Hardened stainless, cross points, square depth bar, RS232.
  - They are equal on paper for every check the stack uses: Q6A outline 85.0/56.0 +/-0.2, PCB 1.44-1.76 mm, 4.90 lead OD vs 4.95 bore, cable build-up 6.1-6.3 mm. The SCALA RS232 port is unused.
  - Neither has an independent measurement, so the Goobay pick is conditional on a test.
  
  SNIPS: Stanley 2-14-556
  - The Stanley UK page confirms 'Straight Pattern Tin Snips', forged Cr-Mo, 0.78 mm cold-rolled steel and 0.46 mm stainless capacity.
  - 0.3-0.5 mm aluminium is well inside that capacity.
  - STATED TRADE: straight pattern, not compound left/right, so it is worse for tight curves.
  
  TAP: Völkel 90530 (TME)
  - M5x0.8, HSS-E (cobalt), ISO2/6H, for through holes.
  - It is a machine-form tap (60 mm, JIS B4430, 4.5 mm square). In a DIN 1814 wrench it cuts through holes by hand, but it is not suitable for blind holes.
  
  DIE: Völkel 27434 (TME)
  - M5x0.8, HSS, DIN 223, 6g, 20x7 mm.
  - Correction to Search B: the EXACT SE M5 die is also HSS ('HSS Eventus', DIN 223B/EN 22568, 6g, 20x7 mm, reichelt). It is an equal alternative.
  
  DIE STOCK AND WRENCH
  - Die stock Völkel 15003 (20x7 mm) is verified on TME at $3.70-4.82 net, not only at the dealer list price.
  - Wrench Völkel 14010 is steel, DIN 1814, M1-M10.
  
  HEAT GUN: Steinel HL 1821 S (datasheet)
  - 1800 W; 300/550 C; 350-450 l/min; micanite heater.
  - Thermal fuse against overheating; 3-year warranty; 2.2 m cord; CE.
  - STATED TRADE: no adjustable stage below 300 C. Technique and bench test are below; HL 1920 E is the upgrade.
  
  HAND-TOOL ROLL
  - Mako, EU store: identical SKU. Hex 0.7-5.0 mm including 2.0 mm (for the M2.5 socket heads), PH000-PH2, T2-T5, TR6-TR25. EUR 39.95, ready to ship from Germany.
  - Knipex 78 61 125: reference-grade electronics flush cutter.
  - Jokari 40026: round wire 0.3-1.0 mm. That covers 28-20 AWG, and the finest wire the stack documents is 26-28 AWG (PWR_ON_KEY, 28 AWG cables). No 30 AWG need is documented.
  
  SPARES
  - Identical part numbers, from authorised distributors.
  - STACK already carries these spares in other lines: V4L 3 (1 spare), Pico 2, CH334F 2, D36V50F12 2, #2813 2, P50B 5, fuses 7.5/4/3/5 A (line 256 / D2), KSD9700 x5 (G4), dipole kit #2.
  
  MICROMETER: SCALA 533.501
  - 0-25 mm, 0.01 mm reading, carbide faces, friction ratchet, clamp.
  - It is the only listed tool that can resolve the G3 nickel check of 0.15 +/- 0.01 mm.
  
  HARD RULES
  - Nothing in the set transmits. The SCALA fallback's data link is wired RS232.
  - No loops or probes; no signal sources.
  - The heat gun is mains, bench only, and not on any device rail.
- **Rejected:**
  1.
    - **Name:** Keep the 245-400 model as-is
    - **Why:** It names no SKUs, so it cannot be bought or checked. Its low end cannot be reached with documented-spec tools once EU VAT is added.
  2.
    - **Name:** SCALA 230.207-X as the primary caliper (TME $36.84 net, $43.84 gross)
    - **Why:** Not worse on paper (DIN 862, hardened stainless, cross points, depth bar), but $22.49 dearer than the Goobay 77001, which is equal on paper. Kept as the fallback if the Goobay fails its acceptance test. TME stock fields conflict (0 shown vs 16 in the data).
  3.
    - **Name:** Bernstein 7-511 caliper (TME $48.49-51.96 net)
    - **Why:** Dearer. Resolution, jaws, depth rod and battery are not on the page, and it is unclear whether '0.02 mm' means accuracy or resolution, so it cannot be shown to be not worse.
  4.
    - **Name:** Bahco 1150D caliper (TME $85-95)
    - **Why:** Not cheaper. Its +/-0.03 mm is the same as the cheaper options.
  5.
    - **Name:** Goobay 77822 heat gun (reichelt EUR 26.99 = $30.34)
    - **Why:** I read the manual (REV2025-08-07) and the datasheet. Neither states a thermal fuse or overheat cut-out, and the reichelt page states no warranty. The cord is 1.3 m vs 2.2 m. Its stepless 50-350 C low range is better, but that does not make up for a missing safety spec.
  6.
    - **Name:** Goobay 77823 / 77821 heat guns
    - **Why:** Same family, also with no stated overheat protection. The 77823's lowest setting is 100 C; the 77821 has fixed 200/500 C stages.
  7.
    - **Name:** Steinel HL 1920 E (TME $66.97 net, $79.69 gross)
    - **Why:** It costs $40.14 more. Upgrade only if the heat-shrink bench test fails or adjustable low temperature is required.
  8.
    - **Name:** GSR 00706010 13-piece tap and die set
    - **Why:** Steel grade, tolerance class and die size are not stated, so its build quality cannot be shown to be not worse.
  9.
    - **Name:** EXACT 20003 tap + EXACT SE M5 die (reichelt EUR 4.20 + 5.40)
    - **Why:** Equal price. The die is HSS, DIN 223B, 6g, so it is equal (Search B was wrong that its material is unknown). The tap's tolerance class is not stated, while Völkel states ISO2/6H. A valid same-parcel alternative, but not a cheaper not-worse pick.
  10.
    - **Name:** EXACT Windeisen 1 tap wrench (reichelt EUR 5.30)
    - **Why:** $9.14 cheaper than the Völkel 14010, but its body is zinc die-cast, against steel. Lower build material, so rejected under the build-quality rule.
  11.
    - **Name:** HAZET HZ 849AG-10 die holder (reichelt EUR 53.99)
    - **Why:** About 10x the price of the Völkel 15003 die stock, for the same job.
  12.
    - **Name:** WISS M5R snips (reichelt EUR 29.99)
    - **Why:** About $17 dearer than the Stanley. Its serrated jaws mark soft aluminium edges, and its 1.65 mm capacity is not needed. The listing does not state the cut direction.
  13.
    - **Name:** iFixit Moray 32-bit kit ($19.95)
    - **Why:** No 2.0 mm hex, which the M2.5 socket heads on the Q6A, standoffs and case need. Also no PH00 or JIS. Worse in coverage.
  14.
    - **Name:** Jokari 20050 or Knipex 12 62 180 as the only stripper
    - **Why:** Their minimum is 24 AWG, so they cannot strip the 26-28 AWG PWR_ON_KEY wire. The Jokari 20050 is kept only as an add-on for 18 AWG.
  15.
    - **Name:** Knipex 12 42 195 MultiStrip 10 ($88-95 net)
    - **Why:** It covers everything, but costs about 3.5x the Jokari 40026 for a 30 AWG capability the stack does not document.
  16.
    - **Name:** Search A spares example: Littelfuse SMBJ14A
    - **Why:** Wrong part. STACK replaced SMBJ14A with SMBJ13A (J21) and SMBJ17A (nodes N and SW); see lines 98, 256 and 990. TME stock was also 0.
  17.
    - **Name:** Search B spares de-dup as written (45-66)
    - **Why:** It removes the 2 spare MHF4L-SMA pigtails by counting the Lime line's '2x MHF4L-SMA', but those are the installed pigtails, and the Lime stays per the 18 Oct decision. Corrected to 57-78.
  18.
    - **Name:** Borrow / makerspace ($0)
    - **Why:** Tool condition and calibration are unknown and measurements are not traceable, so it cannot be shown to be not worse. It also does not cover calipers for repeated goods-in checks, spares or the notebook. Acceptable only as the user's own choice for one-off M5 threading.
  19.
    - **Name:** Rite in the Rain No. 373 from riteintherain.com ($9.95)
    - **Why:** The product meets the spec, but the maker ships only within the contiguous US. A US order would add express shipping, import VAT and the EUR 3 duty plus EUR 2 handling fee. Buy it from an EU reseller instead (price unverified).
- **Conditions or tests:** 1. CALIPER ACCEPTANCE (within the 14-day EU withdrawal window)
     - Use the SCALA 533.501 micrometer as the reference.
     - Measure 3 hardened round parts (about 3, 5 and 10 mm drill shanks or ISO 8734 m6 dowel pins) and one 20-25 mm part.
     - Pass:
       - The caliper reading is within +/-0.02 mm of the micrometer.
       - It returns to 0.00 after 10 closes.
       - Drift is at most 0.01 mm over 30 minutes at the bench.
     - Fail: return it to reichelt and buy the SCALA 230.207-X (+$22.49).
  
  2. HEAT-GUN BENCH TEST (HL 1821 S at the 300 C stage, reducer nozzle)
     - Shrink 3:1 adhesive-lined tube on an RG174 offcut and on a PTFE-coax offcut, next to a PETG and an ASA test coupon at working distance.
     - Pass: no jacket damage and no deformation of the prints.
     - Shield prints with aluminium tape and never leave the gun unattended.
     - Fail: buy the HL 1920 E (+$40.14).
     - The gun has a brush motor: keep it off during conducted RF measurements.
  
  3. THREAD TEST
     - First confirm that the RTL-SDR Blog dipole thread is M5x0.8.
     - Cut a thread on a 5 mm brass or aluminium offcut.
     - Pass: a stock M5 nut runs on by hand without play, and the rod seats in the dipole base.
     - The tap is spiral-point, through holes only. M5 couplers must be through-tapped sleeves. Blind holes need a bottoming tap, which is not priced.
  
  4. WIRE GAUGE
     - Fix the battery-path gauge, which STACK gives as 18-20 AWG.
     - If 20 AWG: the Jokari 40026 alone. Test it on 20 AWG silicone and on 28 AWG; no nicked strands.
     - If 18 AWG: add the Jokari 20050 (+$28.63).
     - The TME page does not say whether 0.3-1.0 mm is the conductor or the outer diameter. Check on arrival.
  
  5. SNIPS
     - Straight pattern only.
     - If the dish gore templates need tight curves, add a compound left/right aviation snip (unpriced) or use relief cuts.
  
  6. TME ORDER CHECKS
     - Confirm the single-unit price and stock in the cart. Every TME page shows 0 in stock while its structured data shows stock.
     - Stock is low: Stanley 2, Völkel die 4, die stock 6, wrench 6, micrometer 4.
     - Shipping for two parcels (TME + reichelt) is not included and not verified.
  
  7. SPARES
     - Each spare follows its parent part's own analog decision (G1-G4).
     - If any parent line drops to qty 1, its spare moves into this kit.
     - Keep one spares inventory sheet in the notebook.
- **Stack changes:** - Line 356: replace the 'model' with the named BOM above.
    - Re-price to about $335-391 incl. 19% DE VAT, plus shipping.
    - Mark the deburrer, spudger, spanner, notebook EU price and organiser as unverified.
  - Spares list:
    - SMBJ14A becomes SMBJ13A and SMBJ17A.
    - Keep 2 spare MHF4L-SMA, because the Lime stays (18 Oct decision) and its 2 pigtails are installed parts.
    - Remove items already carried as spares in other lines.
  - New gap item: SCALA 533.501 0-25 mm micrometer, $41.66 incl. VAT. It is needed for the G3 nickel check (0.15 +/- 0.01 mm). The other option is that G3 drops the micrometer step and relies on its mV/100 mm resistance test.
  - Wire gauge: state 20 AWG or 18 AWG for the battery path, since 18 AWG needs a second stripper.
  - No change to rails, connectors, Ubuntu 24.04 arm64 drivers or the case.
    - All items are unpowered bench tools, except the mains heat gun, which stays bench-only.
    - Nothing transmits.
    - Calipers measure only unpowered boards.
- **Sources:**
  - https://www.reichelt.de/de/de/shop/produkt/messschieber_analog_digital_150_mm-16976
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/toolsB_dl/goobay_77001.pdf (Goobay 77001 manual: error limit 30 um, DIN 862, hardened stainless)
  - https://www.tme.eu/en/details/sc230207/measuring-tools/scala/230-207-x/
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_scala/scala.txt (SCALA catalogue, Type 230 p.46-47; Type 533 micrometer p.75)
  - https://www.tme.eu/en/details/sc533501/
  - https://www.tme.eu/en/details/stl-2-14-556/shears-scissors-knives/stanley/2-14-556/
  - https://www.stanleytools.co.uk/product/2-14-556/maxsteel-tin-snips-250mm
  - https://www.tme.eu/en/details/volkel-90530/threading-dies-and-taps/volkel/90530/
  - https://www.tme.eu/en/details/volkel-27434/threading-dies-and-taps/volkel/27434/
  - https://www.tme.eu/en/details/volkel-15003/
  - https://www.tme.eu/en/details/volkel-14010/
  - https://www.reichelt.de/de/de/shop/produkt/gewindebohrer_m5-214069
  - https://www.reichelt.de/de/de/shop/produkt/schneideisen_m5-44247
  - https://www.reichelt.de/de/de/shop/produkt/windeisen_m3_-_m10-44252
  - https://www.reichelt.de/de/de/shop/suche/schneideisen
  - https://www.tme.eu/en/details/hl1821s/hot-air-guns-and-accessories/steinel/hl-1821-s/
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_steinel/hl1821s.pdf (Steinel HL 1821 S datasheet: thermal fuse, 3-year warranty)
  - https://www.reichelt.de/de/de/shop/produkt/heissluftpistole_1500_w_230_v_stufenlos_50_bis_500_grad-417265
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/toolsB_dl/goobay_77822_anl.pdf and goobay_77822_db.pdf (no overheat protection stated)
  - https://www.tme.eu/en/details/hl1920e/hot-air-guns-and-accessories/steinel/hl-1920-e/
  - https://www.ifixit.com/en-eu/products/mako-driver-kit-64-precision-bits
  - https://www.tme.eu/en/details/knp.7861125/cutting-pliers/knipex/78-61-125/
  - https://www.tme.eu/en/details/jokari-40026/strippers-for-wire-cable/jokari/40026/
  - https://www.reichelt.de/de/de/shop/suche/entgrater
  - https://www.reichelt.de/de/de/shop/suche/pinzette%20esd
  - https://www.reichelt.de/de/de/shop/produkt/blechschere_bulldogschere_233_mm-161071
  - https://www.riteintherain.com/no-373-side-spiral-notebook
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md lines 57, 63, 98, 133, 183, 205, 233, 236, 245-256, 292-293, 356, 990
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/analogs_G3_power_gnss_imu.json (nickel micrometer check 0.15 +/- 0.01 mm)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json (18-20 AWG battery path, 26-28 AWG PWR_ON_KEY)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/mechanical_thermal.json (2 Lime MHF4L-SMA are the installed cables)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md items 34-35
- **Confidence:** medium

