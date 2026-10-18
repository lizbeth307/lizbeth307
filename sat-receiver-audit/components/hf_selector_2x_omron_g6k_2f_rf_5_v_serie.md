# Hf selector 2x omron g6k 2f rf 5 v serie: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e32114dd-52d`_

- **Part:** HF+ input selector: 2x DPDT RF relays in series-shunt plus driver PCB (K1 = P5 HF/LF, K2 = P6 VHF2/AIS; de-energised, the HF+ sits on 50 ohm and both antenna ports are terminated)
- **Current pick:** 2x Aratas (formerly Omron) G6K-2F-RF DC5 (standard footprint), 5 V single-side-stable coil, plus driver PCB (FET drivers on MCP23017 #1 GPB2/GPB3, LAB5 rail)
- **Current price usd:** STACK: 62-80 per set (relays from RS UK at GBP 43-52 for two ex VAT, which is $57.27-69.25, plus the driver PCB). Re-audit corrected relay price, which I verified on 18 Oct 2026: $50.12 for two at DigiKey US (Z2037-ND, $25.06 each, Active, 6,930 in stock). DigiKey DE: EUR 22.00 each ex VAT (EUR 26.18 incl. VAT).
- **Decision:** replace_conditionally
- **Chosen:** 2x Aratas (formerly Omron) G6K-2F-RF-S DC5, the 'board space-saving' variant of the same relay. Bought from DigiKey, an authorised distributor (US part Z2828-ND). Fallback if the bench condition fails: the current G6K-2F-RF DC5 from DigiKey (Z2037-ND).
- **Chosen price usd:** 39.38 for two relays at DigiKey US ($19.69 each, Active, 2,027 in stock, 26-week factory lead time; verified 18 Oct 2026). EU: DigiKey DE EUR 17.29 each without VAT, EUR 20.58 with VAT (both shown on the page), so EUR 34.58 ex VAT (about $38.87) or EUR 41.15 incl. 19% DE VAT for two. DE shipping is free from EUR 75, otherwise EUR 25, so bundle it with the other DigiKey lines. The set costs about $44-50 including the unchanged driver PCB.
- **Saving usd:** $10.74 per set (21%) against the same seller's price for the current part ($50.12 to $39.38). In the EU at DigiKey DE: EUR 9.42 ex VAT (about $10.59). Against STACK's RS UK relay figure ($57.27-69.25): $17.89-29.87.
- **Equivalence proof:** Source: Omron datasheet K242-E1-07, 'G6K(U)-2F(P)-RF(-S,-T)'. One datasheet and one guarantee table cover both parts. I read the local copy and digitised the page-3 curves myself at 600 dpi (±1 dB).
  
  (1) Guaranteed RF figures are identical. At 1 GHz: isolation 20 dB min (same polarity) and 30 dB min (different polarity), insertion loss 0.2 dB max, VSWR 1.2 max. Carry 3 W, switching 1 W.
  
  (2) Average curves in the band the stack specifies, standard vs -S:
  - Isolation, one open contact: 162 MHz 42.8 vs 43.2 dB; 200 MHz 40.9 vs 41.6 dB; 260 MHz 38.8 vs 39.4 dB. From 30 to 100 MHz the two are within about 1 dB, with -S equal or slightly higher.
  - Insertion loss: 162 MHz 0.048 vs 0.045 dB; 260 MHz 0.061 vs 0.058 dB.
  - Return loss: 162 MHz 43.6 vs 43.6 dB; 260 MHz 41.1 vs 40.5 dB.
  So the -S is equal or better on every curve that the stack acceptance uses (≥35 dB at 162-260 MHz, ≤0.3 dB from 10 kHz to 260 MHz, VSWR ≤1.2).
  
  (3) Same coil: 5 V, 237 ohm, 21.1 mA, about 100 mW (about 105 mW from 5 V); must-operate 80% max, must-release 10% min, maximum 150%.
  
  (4) Same contacts and mechanics:
  - DPDT (2 Form C), single-side stable (fail-safe: de-energised gives 50 ohm on the HF+ and terminated ports), DC-coupled with no DC block.
  - 100 mOhm max; 125 VAC/60 VDC, 1 A; 750 VAC across open contacts.
  - 5x10^7 mechanical and 1x10^5 electrical operations.
  - Vibration 300 m/s2 and shock 1,000 m/s2 (destruction).
  - -40 to +70 C, fully sealed, 0.95 g, same body 10.3 x 6.9 x 5.4 mm.
  - Same internal connections and pin numbering. The -S has 6 ground terminals instead of 2 end tabs.
  
  (5) The one weaker published figure, stated openly rather than traded silently: below about 25 MHz the -S average isolation curve bottoms out at about 62 dB, while the standard curve reaches about 77 dB at the left edge. Both read about 61-62 dB near 15 MHz and about 55-58 dB at 30 MHz. The plot is a linear 0-3 GHz sweep, and a capacitive model fitted to the 260 MHz point (about 0.07 pF) gives more than 87 dB below 1 MHz for both. So I judge the gap to be the analyser floor at the first sweep point, not the relay. That is inference, not proof. No stack function depends on it either: leaked strong HF carriers sit far above the -140 dBm MDS with either part (for example -20 dBm becomes -82 or -97 dBm), and broadband leakage is far below the floor with both.
  
  (6) Provenance: an authorised distributor with the Aratas/Omron marking; Electropages confirms the rebrand (re-audit B). Passive, receive-only part; no hard rule is touched.
- **Rejected:**
  1.
    - **Name:** G6K-2F-RF DC5 (current part) from DigiKey, $50.12 for two (EUR 44.00 ex VAT at DigiKey DE)
    - **Why:** Not rejected on quality, because it is the identical part. It is $10.74 dearer than the -S, which matches it on every guaranteed figure and on every average curve at 30-300 MHz. It stays as the named fallback if the -S fails the LF/HF bench gate. Buy it from DigiKey, not RS UK (RS is about $7-19 dearer).
  2.
    - **Name:** G6K-2F-RF-S DC5 from LCSC (C2750987, brand listed as OMRON), $12.00 each, $24.00 for two, 357 in stock
    - **Why:** Same part on paper, but provenance does not survive: I could not verify that LCSC is a franchised Omron/Aratas distributor. Its '670+ authorised brands' page did not show Omron or Aratas, and Omron's distributor page returned 403. The listing says '300/Full Reel' for a part number that Omron packs in trays (the -TR03 suffix is the reel form). Whether single pieces ship moisture-proof (Omron requires use within about one week at ≤30 C/60% RH after opening) is not verified. Optional only with the user's explicit OK: bundle it into the stack's existing LCSC order (TPS7A4701/LT3045/TPS2553) to save another $15.38, then check the marking and date code and run the same bench gate.
  3.
    - **Name:** G6K-2F-RF-S DC4.5 + 22 ohm series resistor, $27.44 for two (DigiKey Z2827-ND, $13.72 each, 1,091 in stock, verified)
    - **Why:** Same RF data as the -S DC5, and the operate margin is the same (4.5/3.6 = 1.25, same as 5.0/4.0). But the rail draw is 5 V x 23.15 mA = 115.7 mW against 105.5 mW, about 10% worse per energised coil, and it needs one extra part per coil. Without the resistor the coil runs at 111% of rated, continuously above its rated point. Worse in coil power, so it fails the rule. Optional trade with the user's OK: it saves a further $11.94.
  4.
    - **Name:** TE/Axicom HF3 1462051-2, 5 V SPDT, $17.72 each
    - **Why:** SPDT (confirmed in TE 108-98000: 1 form C). Two of them cannot give both the 50 ohm HF+ state and terminated antenna ports when de-energised; three cost $53.16, which is more than $50.12. Also worse: coil 140 mW, mechanical life 10^7, and 14.6 x 7.2 x 10 mm (10 mm tall in the HF+ can).
  5.
    - **Name:** Aratas/Omron G6K-2F(-Y) DC5, non-RF, about $5 each
    - **Why:** No RF guarantee. Omron's typical data for the G6K-2G sample ends at 100 MHz and already shows about 0.18-0.2 dB IL and about 29 dB RL there, against 0.033 dB and about 47 dB for the -RF. There is no data at 162-260 MHz.
  6.
    - **Name:** Reed relays: Coto 9814-05-00, Standex-Meder CRF05-1A, Coto 9002-05-00
    - **Why:** SPST-NO (Form A). They are open when de-energised, so the fail-safe 50 ohm HF+ state and terminated ports are impossible.
  7.
    - **Name:** TE IM03GR signal relay
    - **Why:** Datasheet isolation is 37.0 dB at 100 MHz, against about 48 dB for the G6K-RF. VSWR is 1.06 at 100 MHz and 1.49 at 900 MHz. The standard coil is 140 mW. Price not checked.
  8.
    - **Name:** Hongfa HFD48/5-SR
    - **Why:** Confirmed in its datasheet: 125 ohm, 200 mW coil (double), plastic sealed (not fully sealed), and only 3 GHz specs (isolation ≥18 dB, IL ≤0.6 dB). No VHF data, and the price is unverified.
  9.
    - **Name:** Solid-state switches (HMC7992/HMC241 class)
    - **Why:** The RF pins need DC blocks, so LF time signals and NAVTEX are lost. There is no unpowered 50 ohm state, and CMOS junctions are exposed to ESD on a 5-10 m wire. Fails hard requirements.
  10.
    - **Name:** Used/surplus SMA coaxial relays (e.g. Radiall R570 series, 12 V)
    - **Why:** No verified price or condition, unknown contact wear, 12 V coil power unverified and likely much higher, and they do not fit the HF+ can or RF bay.
  11.
    - **Name:** Panasonic ARA200A05
    - **Why:** $38.54 each (dearer). IL 0.3 dB max against 0.2 dB, coil 140 mW, 14.7 x 9.7 x 5.9 mm.
  12.
    - **Name:** G6KU-2F-RF (latching) and G6K-2F-RF-T DC5
    - **Why:** The latching part loses the fail-safe de-energised 50 ohm state. The -T costs $26.03 each, which is not cheaper.
  13.
    - **Name:** Budget alternative: manual coax swap at P5/P6
    - **Why:** Loses the automatic fail-safe 50 ohm/terminated boot state, one-touch switching and automatic AIS on the HF+.
- **Confidence:** medium
- **Conditions or tests:** Gate on the first assembled -S pair, conducted only. Sources are LiteVNA port 1 or the tinySA generator at ≤ -40 dBm (STACK rule), with every antenna port loaded.
  
  (a) Unchanged stack acceptance:
  - ≥35 dB isolation at 162-260 MHz, P6→HF+ with K1 selected and P5→HF+ with K2 selected.
  - ≤0.3 dB insertion loss from 10 kHz (or the source's lowest frequency) to 260 MHz.
  - Return loss ≥21 dB (VSWR ≤1.2) to 260 MHz.
  - Unpowered: HF+ on 50 ohm and both ports terminated.
  
  (b) New LF/HF gate, because the -S published curve is lower below 25 MHz:
  - Measure P5→HF+ isolation with K2 energised and with all coils off, and P6→HF+ with K1 energised.
  - Use the HF+ as the detector (MDS about -140 dBm), referenced to the through level with the port selected.
  - Accept if isolation is ≥75 dB from the lowest source frequency (≤100 kHz; LiteVNA/tinySA lower limits not re-verified) to 2 MHz, ≥60 dB to 20 MHz, and ≥55 dB at 20-30 MHz. These levels equal or exceed the current part's published average where it is physically meaningful.
  - If only (b) fails, either fit the standard G6K-2F-RF DC5 (fallback; needs its own land pattern) or the user explicitly accepts the measured figure.
  
  (c) On arrival: check the Aratas/Omron marking and date code. Pull-in at ≤4.0 V and drop-out at ≥0.5 V on each coil.
  
  (d) Handling: Omron ships SMT parts moisture-proof. Solder within about one week of opening (≤30 C/60% RH) and reseal the spares.
- **Stack changes:** - **BOM row 'HF+ input selector'** (C17, section 2.3, line 380): change to 2x Aratas (formerly Omron) G6K-2F-RF-S DC5, DigiKey Z2828-ND, $39.38 (DigiKey DE EUR 17.29 each ex VAT, EUR 20.58 incl. VAT). Seller becomes DigiKey, not RS UK. Status: verified 18 Oct 2026. Fallback: G6K-2F-RF DC5 Z2037-ND at $25.06 each. Remove the RS UK link at line 1206, or keep it as a third source.
  - **Shopping order step 7:** move the G6K line from 'RS UK' into the existing DigiKey order (reaches DigiKey DE free shipping at EUR 75 or more).
  - **Driver PCB:**
    - Use the -S land pattern from Omron K242 p.4: 8.8 x 7.5 mm, with 6 ground terminals (four corners plus two beside pins 1 and 8). Tie all of them to the RF ground plane with vias.
    - Signal pads 1-8 sit at the same positions as on the standard part (0.8 mm pads, 3.2/5.4/7.6 mm pitch, 7 mm rows). A union footprint that also takes the standard part's two end tabs (11.5 mm span) may therefore be possible, which would avoid a re-spin for the fallback; check clearance in CAD (unverified).
    - Observe the coil polarity marking (+ on pin 1, - on pin 8 per Omron's diagram). Keep the flyback diode and low-side FET.
  - **Rails:** unchanged (LAB5, one coil at a time). Correct STACK's coil figure from 0.12-0.15 W to about 0.105 W (5 V x 21.1 mA).
  - **Drivers and software:** unchanged (MCP23017 #1 GPB2/GPB3, labd mapping, boot state).
  - **Case and placement:** unchanged. Same body; the footprint is 2.7 mm shorter, so the board can shrink slightly inside the HF+ can.
  - **Correction to the isolation basis:** my digitisation of Omron's average curves gives about 43 dB at 162 MHz, about 41 dB at 200 MHz and about 39 dB at 260 MHz per open contact, for both variants. The search results' 46/41 dB and 44/39 dB were high. Only about 4 dB of single-contact margin remains over the 35 dB target at 260 MHz before the shunt pole is counted, which is one more reason to keep the measured acceptance.
  - **Test plan:** add the LF/HF isolation gate (b) to the bring-up RF test row (line 1082) and to step 10.
  - **Unverified:** the Mouser and Farnell pages returned 503, Omron returned 403, and TME shows 0 in stock with no price. I had no WebSearch budget left this turn (shared limit reached), so all checks were made with WebFetch on primary pages. The digitised curves are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/adv_g6k/r/.
- **Sources:**
  - https://www.digikey.com/en/products/detail/aratas-formerly-omron-components/G6K-2F-RF-S-DC5/1936449
  - https://www.digikey.de/en/products/detail/aratas-formerly-omron-components/G6K-2F-RF-S-DC5/1936449
  - https://www.digikey.com/en/products/detail/aratas-formerly-omron-components/G6K-2F-RF-DC5/503107
  - https://www.digikey.de/en/products/detail/aratas-formerly-omron-components/G6K-2F-RF-DC5/503107
  - https://www.digikey.com/en/products/detail/aratas-formerly-omron-components/G6K-2F-RF-S-DC4-5/1936448
  - https://omronfs.omron.com/en_US/ecb/products/pdf/en-g6k_2f_rf.pdf (K242-E1-07; local copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/adv_g6k/ds/omron_rf.pdf, pages 2-4 read and digitised)
  - https://www.lcsc.com/product-detail/C2750987.html
  - https://www.lcsc.com/franchised-brand
  - https://www.tme.eu/en/details/g6k-2f-rf-s-5dc/rf-relays/omron-electronic-components/g6k-2f-rf-s-5vdc/
  - https://www.electropages.com/blog/2026/07/omron-electronic-components-rebrands-aratas (via re-audit B)
  - https://www.te.com/en/product-1462051-2.html (HF3 datasheet 108-98000, local copy hf3_dl/hf3.pdf)
  - https://macrogroup.ru/upload/iblock/d12/gs6kxustts46kilcbe8du2d8xcnv2fil/HFD48.pdf
  - https://static.rapidonline.com/pdf/60-1278.pdf (TE IM datasheet)

