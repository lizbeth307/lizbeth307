# Protection filter set 7 5 a pack 4 a j21: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** Protection/filter set (Power, core, qty 1 set): MINI blade fuses 7.5 A pack / 4 A J21 / 3 A LAB5 / 5 A service, plus holders and spares; SMBJ17A x2 (N and SW, re-audit D); SMBJ13A (J21); 220 uF/25 V; PTCs (0.75 A AUX, Boni 0.2 A at 60 C if v2 keeps it; the LNB PTC is replaced by a TPS259630DDAR per re-audit B); AUX12 P-FET with +/-20 V VGS + 2N7002; eFuse TPS259470A x3 (J21, DISP12, USB-C VBUS, re-audit D); LC pi-filter parts; Mix-31 ferrites; genuine Amass XT30
- **Current pick:** STACK v1 row 256 gives specs only, with no part numbers: 7.5/4/3 A mini blade fuses + holders, SMBJ17A, SMBJ13A, 220 uF/25 V, PTCs, P-FET +/-20 V VGS, eFuse 1.5 A, LC, Mix-31, Amass XT30. Re-audit D changes it to 3x TPS259470A and 2x SMBJ17A.
- **Current price usd:** 15-25 (STACK model, never verified). Real cost of the re-audited set, qty 1, before LC parts, shipping, VAT and EU fees: about 27.9 at the cheapest verified channel per line. DigiKey alone: about 28-30. LCSC alone: about 30.7, because of LCSC minimum order quantities and the Fair-Rite price there.
- **Decision:** keep
- **Chosen:** KEEP the set as specified. No cheaper analog survived as not-worse. Because STACK named no parts, the set is now filled with these verified branded parts (cheapest verified channel in brackets):
  - Fuses: Littelfuse MINI 297 .WXNV (silver-plated): 029707.5WXNV, 0297004.WXNV, 0297003.WXNV, 0297005.WXNV [LCSC C178942/C178940/C151092/C151093, minimum 5 each].
  - Holders: Keystone 3568 x4 for J21, LAB5, the 5 A service port, and the pack fuse on a small carrier or inline [DigiKey; LCSC stock is 0].
  - TVS: Littelfuse SMBJ17A x2 (marking LR) and SMBJ13A (marking LG) [LCSC C157523/C151252]. Vishay SMBJ17A-E3/52 and SMBJ13A-E3/52 are equal alternatives.
  - 220 uF/25 V: Nichicon UHE1E221MPD, radial 8x11.5 mm [DigiKey $0.63 qty 1, or LCSC C116228]. SMD fallback: Panasonic EEE-FK1E221GP (the G suffix is the 5000 h part).
  - PTCs: Bourns MF-MSMF075/24-2 (AUX) and MF-MSMF030-2 (Boni, only if v2 keeps a PTC there) [DigiKey qty 1].
  - AUX12 switch: AOS AO3407A + Nexperia 2N7002 [DigiKey].
  - eFuse: TI TPS259470ARPWR x3, the same part in all three places [DigiKey, a franchised distributor].
  - Ferrites: Fair-Rite 0431164281 x3 [DigiKey].
  - Connectors: Amass XT30U-M/-F [LCSC C99101/C99102, minimum 5].
  - LC parts: still unnamed (spec floor only).
- **Chosen price usd:** About 27.9 for the set, qty 1, at the cheapest verified channel per line:
  - Fuses 2.31 (20 pcs)
  - 4 holders 5.24
  - TVS 1.25 (10 pcs)
  - UHE capacitor 0.63
  - PTCs 0.89
  - AO3407A 0.52 + 2N7002 about 0.17
  - 3x TPS259470A 6.18
  - 3x Fair-Rite 8.55
  - XT30 5+5 pieces 2.19
  
  That is about 25.7 if the TI parts come from LCSC (not TI-franchised). Add about 2.14 if this set also carries the 2x TPS259630DDAR. Add 4-12 (model) for the LC parts, so roughly 31-40 all-in, before shipping, VAT and EU fees.
- **Saving usd:** 0 from analogs: none adopted. The STACK model of 15-25 was too low by about 3-13 even before the LC parts. The only real saving is from splitting the order by channel: about 1-3 against DigiKey alone and about 3 against LCSC alone. For a buyer in Europe, a separate small LCSC order would lose that saving to EU fees (EUR 3 per tariff line on IOSS orders up to EUR 150, plus the EUR 2 per line Union handling fee from about 1 Nov 2026). So add this set to an order that is already planned.
- **Equivalence proof:** The decision is keep, so every part implements the existing STACK and re-audit spec. These are the checks I verified myself, 18 Oct 2026:
  
  1. Fuses (Littelfuse MINI datasheet, LCSC PDF): 32 VDC, interrupting rating 1000 A at 32 VDC (this closes the gap both searches left open). UL 248 applies to the Ag-plated version only; the Sn-plated .WXT is not UL recognized and its system temperature limit is 85 C. 110% current must carry for 360,000 s minimum; 135% opens in 0.75-600 s. Cold resistance: 3 A 33.75 mohm, 4 A 23.48 mohm, 7.5 A 10.85 mohm. Load ratios: 4.6 A on 7.5 A is 62%; 2.3 A on 3 A is 77%. I could not read the re-rating curve, so the re-audit D 50 C bench test stays.
  
  2. Keystone 3568 (Keystone catalog p.48 and DigiKey): one-piece holder for MINI 297/ATM, UL rated 30 A, nylon 6/6 UL94 V-0 body, brass contacts, -50 to +145 C. DigiKey $1.31, 107,223 in stock.
  
  3. SMBJ (Littelfuse and Vishay 88392 rows):
  - SMBJ13A: VRWM 13.0 V, VBR 14.40-15.90 V, VC 21.5 V at 28.0 A, IR 1 uA, marking LG.
  - SMBJ17A: VRWM 17.0 V, VBR 18.90-20.90 V, VC 27.6 V at 21.8 A, marking LR.
  - LCSC C151252 lists SMBJ14A values in its attribute table (14 V, 17.2 V, 23.2 V at 25.9 A), so the marking must be checked at goods-in.
  - LCSC prices: $0.1075 and $0.1428, minimum 5; stock 2,865 and 4,510.
  
  4. Nichicon UHE1E221MPD (Nichicon catalog): 25 V, 8x11.5 mm, impedance at most 0.13 ohm at 100 kHz/20 C, ripple 640 mA at 100 kHz/105 C (448 mA at 120 Hz on DigiKey), 7000 h at 105 C, -40 to +105 C. That beats both searches' floors (5000 h, 0.6 A, damping ESR about 0.05-0.16 ohm, 8 mm diameter). It also beats EEE-FK1E221GP (0.16 ohm, 600 mA, 5000 h). DigiKey $0.63, 14,014 in stock.
  
  5. PTCs (Bourns MF-MSMF tables):
  - MF-MSMF075/24: 24 V, Imax 40 A, R1max 0.45 ohm, hold 0.55 A at 60 C. That matches STACK's 'about 0.55 A at 60 C' against the 0.42 A load.
  - MF-MSMF030: 30 V, R1max 3 ohm, hold 0.21 A at 60 C.
  
  6. AO3407A (AOS): -30 V, VGS +/-20 V, RDS(on) at most 48/78 mohm at -10/-4.5 V, VGS(th) -1.5 to -2.5 V, PD 1.4 W.
  
  7. TPS259470A (TI SLVSFC9C, May 2026): 2.7-23 V operating, 28 V absolute maximum, down to -15 V reverse, true reverse blocking, ILIM 0.5-6 A (+/-10% above 1 A), adjustable OVLO with 1.2 us response, auto-retry after 110 ms. LCSC $1.30 (4,449 in stock); DigiKey $2.06.
  
  8. Fair-Rite 0431164281 (DigiKey): material 31, about 310-315 ohm at 100 MHz, 6.60 mm inside diameter, 39.4 mm long, $2.85 qty 1 / $1.968 qty 10, 103,515 in stock.
  
  9. Amass XT30U (LCSC, brand Changzhou Amass): $0.2295 / $0.2072, minimum 5, stock about 49k and 42k.
  
  Hard rules: all of these are passive or DC protection parts. Nothing transmits, nothing is a loop, nothing is a signal source.
- **Rejected:**
  1.
    - **Name:** TPS259470LRPWR (latch-off version, DISP12 only)
    - **Why:** Same silicon, but per the TI datasheet a fault latches until EN is pulled below VSD(F) or VIN is cycled. DigiKey saves only $0.11 and has 12 in stock. At LCSC it costs more than the A version ($1.42 vs $1.30). It also breaks the single part number for all three places, so a spare A no longer fits everywhere.
  2.
    - **Name:** TPS259472ARPWR (overvoltage clamp version)
    - **Why:** The TI datasheet note says input voltage must be limited to the selected clamp threshold (3.8/5.7/13.8 V). It clamps and dissipates instead of disconnecting when SYS12 shorts, and it has no 22 V option for USB-C VBUS. Worse.
  3.
    - **Name:** TPS259630DDAR in place of TPS259470A on DISP12, J21 or VBUS
    - **Why:** RON 89 vs 28.3 mohm, ILIM at most 2 A, no reverse blocking, lower absolute maximum. Worse. It stays only on the LNB and Boni rails, per re-audit B.
  4.
    - **Name:** DIY discrete eFuse
    - **Why:** Cannot match the 1.2 us OVLO, the +/-10% ILIM, or reverse blocking, and it would reopen the J21 over-voltage path that re-audit D closed.
  5.
    - **Name:** Eaton SMBJ17A / SMBJ13A
    - **Why:** DigiKey and TME parametrics match (VC 27.6 V at 21.8 A, VBR 18.9-20.9 V, IR 1 uA), but I could not read the Eaton datasheet (HTTP/2 error, empty reply, TME bot wall). It is also not the cheapest: Littelfuse costs $0.1075/$0.1428 at LCSC against Eaton's $0.38/$0.45 at DigiKey, and TME is out of stock with a minimum order of 48,000. Usable only as a fallback in a DigiKey-only order, after the datasheet is read.
  6.
    - **Name:** Alpha & Omega SMBJ17A
    - **Why:** VC at IPP is not published and it is out of stock.
  7.
    - **Name:** MDD / FOSAN / YFW SMBJ13A and SMBJ17A
    - **Why:** Equal only on paper, with no independent clamp or surge data, and they protect a board with a 16 V limit. FOSAN IR is 5 uA against 1 uA. Saves about $0.25.
  8.
    - **Name:** ST SMBJ series (datasheet in p5prot_dl)
    - **Why:** ST makes no SMBJ17A, and its SMBJ13A has no VBR maximum (only 14.4 min / 15.2 typ), so it cannot be shown to stay below 15.9 V.
  9.
    - **Name:** Shenzhen JDT MINI fuse clones (029707.5J etc.)
    - **Why:** No time-current data, interrupting rating or re-rating; part numbers copy Littelfuse numbering; saves about $0.50.
  10.
    - **Name:** Keystone 3557 loose clips
    - **Why:** Two loose clips with no insulating body give weaker fuse retention under handheld shock. Saves about $0.77 per fuse.
  11.
    - **Name:** Littelfuse 01530008Z PCB holder
    - **Why:** Rated UL 20 A / UR 15 A (datasheet) against 30 A for the 3568, and costs $4.04 against $1.31.
  12.
    - **Name:** Littelfuse 1812L075/24DR (AUX PTC)
    - **Why:** Better Imax (100 A) and R1max (0.29 ohm), and active, but the Littelfuse derating table gives 0.50 A hold at 60 C against 0.55 A for the Bourns. The AUX margin over 0.42 A falls from 31% to 19%. Worse on the governing spec.
  13.
    - **Name:** LUTE 1812L075/24GR
    - **Why:** Its own datasheet gives 0.49 A hold at 60 C against 0.55 A. Worse.
  14.
    - **Name:** KUU K1812L075PR, Littelfuse 1812L075PR, Bourns MF-MSMF075-2 (13.2-16 V)
    - **Why:** Vmax is below the 16.4-16.8 V a SYS12 regulator short puts across the PTC.
  15.
    - **Name:** LUTE 1812L030/30GR (Boni)
    - **Why:** Equal or better on paper (0.21 A at 60 C, 3 ohm, Imax 40 A), but no qualification data. Saves about $0.05, and v2 may drop the Boni PTC altogether.
  16.
    - **Name:** UMW AO3407A
    - **Why:** VGS(th) up to -3.0 V against -2.5 V for AOS, and ID -4.2 vs -4.3 A. It is better on RDS(on) at -4.5 V (65 vs 78 mohm), but it does not dominate and has no independent data. Saves cents.
  17.
    - **Name:** Diodes DMP3099L-7
    - **Why:** RDS(on) 99 vs 78 mohm at -4.5 V and PD 1.08 vs 1.4 W. Worse.
  18.
    - **Name:** Panasonic EEE-FK1E221P (search 2 baseline)
    - **Why:** The Panasonic table gives 2000 h at 105 C, not the 5000 h search 2 claimed, so it fails the 5000 h floor. Only the GP suffix (EEE-FK1E221GP) is 5000 h, and that one is still worse than and dearer than the UHE.
  19.
    - **Name:** Panasonic EEU-FR1E221
    - **Why:** Out of stock with a 37-week lead time.
  20.
    - **Name:** HRK GVT1E227M0810CNVC / Nichicon UWT1E221MNL1GS
    - **Why:** 2000 h / 1000 h life and 175 mA ripple (HRK). Worse.
  21.
    - **Name:** Fair-Rite 0431164951 / 0431173951
    - **Why:** 280 / 180 ohm at 100 MHz against about 315 ohm. Worse.
  22.
    - **Name:** Wurth 74271140
    - **Why:** 4W620 NiZn rather than #31 material, lower impedance (92/178 ohm at 25/100 MHz) and dearer. Fits only the 2-3 mm touch-USB lead, as re-audit D already says.
  23.
    - **Name:** Unbranded clip-on ferrites
    - **Why:** No published impedance curve at 1-30 MHz.
  24.
    - **Name:** KLS XT30 and other XT30 clones
    - **Why:** No current, plating or housing data; genuine Amass costs $0.21-0.23 at LCSC.
  25.
    - **Name:** Sunlord SWRB1207S-101MT (100 uH)
    - **Why:** DCR 220 mohm against 110-180 for the Wurth and Bourns parts, and the datasheet could not be read. No LC part is named in STACK yet, so there was nothing to compare it to.
  26.
    - **Name:** Used or salvaged protection parts
    - **Why:** Condition cannot be checked: PTC R1max drift and TVS surge history are invisible.
- **Confidence:** medium
- **Conditions or tests:** - Goods-in: SMBJ13A must be marked LG (LK means SMBJ14A, reject it); SMBJ17A must be marked LR. Fuses must be .WXNV (Ag), not .WXT (Sn).
  - Bench, from re-audit D: 4.6 A on the 7.5 A fuse and 2.3 A on the 3 A fuse, 30 min each in a 50 C enclosure, logging holder temperature rise.
  - AUX PTC: 0.42 A for 60 min at 60 C with no trip.
  - Read the Eaton TVS datasheet before using Eaton in any DigiKey-only order.
  - Buy the TPS259470A from DigiKey (franchised; 78,910 in stock). LCSC is not TI-franchised and TME does not list the part.
  - Confirm the TME price and stock for the Fair-Rite cores; TME's structured data shows $1.23-2.62 with conflicting stock figures, so it is unverified.
  - Before choosing a channel, confirm how DigiKey DE handles EU duty and VAT and when the EUR 2 Union handling fee starts.
- **Stack changes:** 1. BOM row 256: name the parts listed under 'chosen'. Price the set at about $28 qty 1 plus LC parts, roughly $31-40 in total; the STACK figure of 15-25 is a low estimate. Count LCSC minimum order quantities (5 for TVS, fuses, capacitor and XT30; 10 for PTCs; 50 for 2N7002); for single PTCs and FETs DigiKey qty 1 is cheaper.
  
  2. J21 220 uF: Nichicon UHE1E221MPD is radial, so the power board needs an 8 mm can footprint with 3.5 mm pitch, and the can should be glued (RTV) against vibration. If an SMD part is required, use EEE-FK1E221GP, never EEE-FK1E221P (only 2000 h).
  
  3. AUX PTC must be MF-MSMF075/24-2, specified as 'at least 0.55 A hold at 60 C, at least 24 V'. Littelfuse 1812L075/24 is not a drop-in (0.50 A at 60 C). Bourns does not allow hand soldering or wave soldering of MF-MSMF parts, so the power board must be reflowed (hot plate, hot air or PCBA); the QFN-10 TPS25947 needs that anyway. The part is marked NFND, so keep the spares from the 10-piece minimum order.
  
  4. Re-audit B contradicts itself on the Boni rail. It says both 'drop the PTCs' (TPS259630DDAR with RILM 7.87 k) and 'BONI13V8 with a 0.15-0.2 A PTC', and gives the rail as both 12.5 V and 13.8 V. v2 must pick one. If the eFuse is fitted, delete MF-MSMF030-2. The LNB PTC is gone. Put the 2x TPS259630DDAR ($1.07 each) in exactly one BOM row.
  
  5. Re-audit D says 27.6 V is below the '30-36 V limits' of the TPS25947. That is wrong: the TPS25947 absolute maximum is 28 V. Temperature also matters: with alphaT of about 0.08%/K, at 60 C the SMBJ17A clamp rises to about 28.4 V and the SMBJ13A VBR maximum to about 16.3 V. So:
  - no TPS25947 may sit on node N or SW;
  - the J21 eFuse OVLO at 13.5 V is the primary over-voltage guard for the 16 V Q6A, and the SMBJ13A only handles fast transients.
  v2 should say this.
  
  6. One eFuse part number (TPS259470A) for all three places, as re-audit D intended. Per the TI datasheet note, consider a TVS from OUT to IN on the USB-C VBUS eFuse, where a powered cable can stress OUT relative to IN.
  
  7. LC parts: in v2, give each inductor an Isat at least equal to the downstream eFuse ILIM maximum (J21 about 4.4 A), not just 1.5x the load. The HF+ 100 uH is chosen after the HF+ current is measured.
  
  8. EU sourcing: put the set into one order that is already planned (DigiKey DE free shipping from EUR 75, or the planned LCSC order). Do not place a separate small LCSC order: from 1 Jul 2026 it pays EUR 3 per tariff line, and from about 1 Nov 2026 also EUR 2 per line (operator note 35).
  
  9. Not in this set, carried over from operator note 30 (verify): the Lime M.2 riser 3.3 V needs a load switch controlled by labd, to be added to the power tree.
  
  No change to drivers, the case or the receive-only, conducted-only and no-loop rules.
- **Sources:**
  - https://www.ti.com/product/TPS25947
  - https://www.ti.com/lit/ds/symlink/tps25947.pdf
  - https://datasheet.lcsc.com/datasheet/pdf/6640fa58723348e000da25e795536560.pdf?productCode=C178942
  - https://www.keyelco.com/userAssets/file/K75p48.pdf
  - https://www.digikey.com/en/products/detail/keystone-electronics/3568/2137306
  - https://www.nichicon.co.jp/english/series_items/catalog_pdf/e-uhe.pdf
  - https://www.digikey.com/en/products/detail/nichicon/UHE1E221MPD/589290
  - https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_PANASONIC-EEEFK1E221P_C128511.pdf
  - https://www.lcsc.com/product-detail/aluminum-electrolytic-capacitors-smd_panasonic-eeefk1e221gp_C401715.html
  - https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_BOURNS-MF-MSMF075-24-2_C208467.pdf
  - https://www.lcsc.com/product-detail/resettable-fuses_littelfuse-1812l075-24dr_C207065.html
  - https://www.lcsc.com/product-detail/resettable-fuses_lute-1812l075-24gr_C19078722.html
  - https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Littelfuse-SMBJ13A_C151252.pdf
  - https://www.vishay.com/docs/88392/smbj.pdf
  - https://www.lcsc.com/product-detail/esd-and-surge-protection-tvs-esd_littelfuse-smbj17a_C157523.html
  - https://www.digikey.com/en/products/detail/eaton-electronics-division/SMBJ17A/13621306
  - https://www.tme.eu/en/details/smbj17a-ea/unidirectional-tvs-smd-diodes/eaton-electronics/smbj17a/
  - https://www.lcsc.com/datasheet/lcsc_datasheet_1810231523_Alpha---Omega-Semicon-AO3407A_C15155.pdf
  - https://www.lcsc.com/datasheet/lcsc_datasheet_2311091734_UMW-Youtai-Semiconductor-Co---Ltd--AO3407A_C347478.pdf
  - https://www.lcsc.com/product-detail/surge-protection-devices-spds_texas-instruments-tps259470arpwr_C3662799.html
  - https://www.lcsc.com/product-detail/C3662793.html
  - https://www.digikey.com/en/products/detail/fair-rite-products-corp/0431164281/8594000
  - https://www.tme.eu/en/details/0431164281/ferrites-sleeves/fair-rite/
  - https://www.lcsc.com/product-detail/plug_changzhou-amass-elec-xt30u-m_C99101.html
  - https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=C116228 (LCSC catalogue API, prices and stock read 18 Oct 2026)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p5v_dl/ (TPS25947, MINI 297, Keystone, Nichicon UHE datasheets as downloaded)

