# Weather kit ipx4 ip54 mesh foam eptfe ve: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_37583a7b-1a8`_

- **Part:** Weather kit IPX4/IP54 (core, Mechanical, 1 set): stainless mesh + hydrophobic foam on the intakes, ePTFE vents, port caps (SMA x11, F, USB-C, USB-A, 3.5 mm, LAB BUS, GX12/M8), clear rain sleeve, 3 IP65+ feed-LNA boxes with glands, self-amalgamating tape, dielectric grease, cobalt-free silica gel
- **Current pick:** Unspecified kit with no SKUs (STACK.md line 276, status 'model'). Budget alternative noted there: caps + rain sleeve only.
- **Current price usd:** 45-110. This is a STACK estimate. It names no SKUs, so the figure cannot be checked.
- **Decision:** keep
- **Chosen:** KEEP the kit's content. No candidate is cheaper than the 45-110 estimate and also not worse. The estimate cannot be met by any genuine branded build. The kit is now pinned to these verified SKUs:
  (1) Vents: Amphenol LTW VENT-PS1YBK-O8002 x5. This is the version WITH a nut, with an OLEOPHOBIC membrane and the >1000 ml/min grade. It replaces both search picks: O8001 has only >550 ml/min, and N8001 is hydrophobic only.
  (2) SMA caps: GCT RFCT-SMA-CAP-GS-1 x11 (brass, gold, IP67, chained per TME).
  (3) LNA boxes: Gainta G201-IP67 polycarbonate x3, but only if the fit and UV conditions pass. Otherwise use the next larger Gainta IP67 PC box (unpriced). Use the die-cast G104MF-IP67 only where UV is unconfirmed and the added mass is acceptable.
  (4) Glands: LAPP SKINTOP ST-M 12x1.5 (53111400) for RG58/LMR-195 only. RG316 entries need an M12 gland with a 2-5 mm range or a reducing insert, or IP67 SMA bulkhead jacks (unpriced).
  (5) Intake foam: Qualtek 09150-M-30 media (UL 900 Class II, 36.4 mm). 30 PPI is preferred over 45 because the drop must stay at or below 5 Pa. It sits behind a COARSE 316 woven mesh (about 0.4-0.5 mm aperture, 45% or more open area) from an EU seller. The 150-mesh cloth is not used.
  (6) Sleeve: OP/TECH Rainsleeve 18 in 2-pack (9001132). Not the Small 8 in model.
  (7) Tape: 3M Scotch 23, 19 mm x 9.15 m.
  (8) Grease: MOLYKOTE 4, 100 g.
  (9) Desiccant: orange cobalt-free indicating silica gel, 5-10 g sachets, plus a humidity indicator card (SKU still open).
  (10) Other caps: non-conductive caps for F, USB-C, USB-A, 3.5 mm, LAB BUS and GX12/M8. The F cap must NOT be a 75-ohm terminator.
- **Chosen price usd:** About 116-168 ex VAT, before shipping. Verified-SKU lines come to about 102-138; unpriced estimates add 14-30.
  Line by line:
  - Vents: 19.25 (DigiKey 5 x 3.85) to 23.20 (TME, 5 x 4.64 at the top of its structured-data range).
  - SMA caps: 30.14-45.43 for 11 (TME structured data); DigiKey tiers give 42.97 (10 x 3.845 + 1 x 4.52).
  - Boxes: 10.29-12.48 for 3 (TME).
  - Glands: 2.10-5.88 for 6.
  - Foam: about 4.14 (3 x 1.38; this is the -45 price from the Angle-B DigiKey figure, and the -30 price is unverified).
  - Sleeve: 9.49-12.99 (US) or GBP 8 (UK).
  - Scotch 23: EUR 12.50-19.14 ex VAT, about 14.4-22.0.
  - MOLYKOTE 4: EUR 10.71 ex VAT, about 12.3.
  - Estimates: other caps 3-8, mesh 5-10, silica gel and card 6-12.
  - FX assumed at 1.15 USD/EUR (not verified).
  - An EU consumer pays 19-27% VAT on top.
  - Non-EU lines (the US/UK sleeve, a UK mesh) also carry EUR 3 duty per tariff line plus EUR 2 handling fee per line from about 1 Nov 2026, plus shipping (per operator note 35; not re-verified).
- **Saving usd:** None against the STACK figure. The real cost is about 58-71 USD ABOVE the 45-110 estimate (116-168 against 45-110), so the estimate must be raised.
  Within the pinned list:
  - Gainta boxes instead of Hammond 1554B2GY: about 16-21 less for 3 (10.29-12.48 against 26.37-33.72).
  - Oleophobic O8002 instead of Angle B's hydrophobic N8001: about 2.20 more for 5 (3.85 against 3.41 at DigiKey qty 1). This is a deliberate spec upgrade, not a silent trade.
- **Equivalence proof:** The current kit is only a spec, so 'not worse' means meeting every spec in the kit and passing the stack's own tests.
  
  1. Vents. The Amphenol LTW Breathable Vent Series catalogue (DigiKey PDF, which I extracted myself) decodes the part number this way:
  - PS1N = without nut, PS1Y = with nut.
  - -N = hydrophobic ePTFE, -O = oleophobic ePTFE.
  - 001 / 002 = airflow grade: N8001 >1000 ml/min, N8002 >3000, O8001 >550, O8002 >1000 ml/min at 7 kPa (= 70 mbar).
  - All versions: IP68 (2 m, 1 h) and IP69K, water entry pressure 60 kPa or more for 60 s, -40 to +125 C, thermoplastic housing UL 94V-0 f1 (UV/outdoor), silicone O-ring, 1000 h salt spray, M12x1.5.
  - Panel: through-hole 2.0-3.5 mm (nut version) or threaded hole at least 4.0 mm.
  So VENT-PS1YBK-O8002 meets every vent spec: oleophobic, 1000 ml/min or more at 70 mbar, IP68/IP69K, WEP at least 40-60 kPa, -40 C, UV-rated. DigiKey: 3.85 at 1, 3.078 at 10, 1,450 in stock. TME: 2.78-4.64 USD, structured stock 194. Both search picks were worse: O8001 has half the airflow, and N8001/N8002 are not oleophobic.
  
  2. SMA caps. GCT RFCT-SMA-CAP-GS-1 on DigiKey: brass body, gold finish, IP67, 'dust cap for SMA jacks', 5,468 in stock, 10-week lead time. This beats unrated silicone caps on sealing, wear on the 1/4-36 thread, and UV. The chain is stated by TME only. Whether it shorts the centre pin is NOT published: the GCT drawing returned 403 again, so a bench check is required.
  
  3. Boxes. Gainta G201-IP67 (TME): polycarbonate, IP67 (better than the IP65 required), -40 to 125 C, gasket and brass bushings included, 65.7 g. Hammond 1554B2GY (TME) is 65x65x40 mm, UL94V-0, at 8.79-11.24, with TME stock 0 / OutOfStock. So the reference is dearer and unavailable at TME, and it shares the same unverified fit. Neither page gives UV stabilisation or interior dimensions.
  
  4. Foam. The Qualtek 09150-M drawing (extracted) gives 36.4 mm square, 30/45/60/100 PPI, UL 900 Class II. The Orion GRM40 datasheet (rev 3/25/2024, extracted) gives only the ABS guard as UL94 V-0. For the media it says only 'porous mesh 30/45 PPI', with no flammability, material or pressure-drop data. So Qualtek has the stronger evidence.
  
  5. Sleeve. 7 in diameter x 18 in gives about 559 mm circumference against the 400 mm section perimeter, and 457 mm length against 225 mm.
  
  6. Scotch 23. ASTM D4388 Type III, 90 C continuous and 130 C overload, 5-year shelf life (3M TDS, per Angle B).
  
  7. MOLYKOTE 4. Silmid shows EUR 10.71 ex VAT / 12.85 inc VAT, 100 g tube with 500 in stock, -40 to +200 C, SAE-AS-8660. Compatibility with silicone rubber is NOT stated.
  
  Every item is passive and mechanical: no rails, no drivers, no RF emission and no loops, so receive-only and conducted-only sources are unaffected.
  
  A note on my own budget: the shared WebSearch budget was already used up when I started, so every check above is a direct fetch of a datasheet or distributor page. Nothing came from new searches.
- **Rejected:**
  1.
    - **Name:** Amphenol LTW VENT-PS1NBK-O8001 (Angle A pick)
    - **Why:** WORSE on airflow. The LTW catalogue gives O8001 >550 ml/min at 7 kPa, against the kit's requirement of about 1000 ml/min at 70 mbar. It is also the no-nut version, which needs a threaded hole at least 4.0 mm deep; that is weak in printed ASA and in a thin box wall. Use VENT-PS1YBK-O8002 instead.
  2.
    - **Name:** Amphenol LTW VENT-PS1NBK-N8001 / VENT-PS1YBK-N8001 (Angle B pin)
    - **Why:** WORSE: the membrane is hydrophobic only, not oleophobic (catalogue code -N), so skin oil and sunscreen on a handheld can wet it. It is only about 0.44 USD cheaper each than O8002 (DigiKey 3.41 against 3.85).
  3.
    - **Name:** Gore VE adhesive vents (RS)
    - **Why:** Sold only in 50-packs at GBP 189-293 ex VAT, from a UK seller (EU duty and handling fee apply). Not cheaper for 5 vents.
  4.
    - **Name:** Hammond 1554B2GY (reference box)
    - **Why:** Not cheaper: 8.79-11.24 each against 3.43-4.16 for the Gainta. TME shows inventory 0 / OutOfStock. It has the same unverified fit (65x65x40 mm outside) and the same unverified UV data.
  5.
    - **Name:** Gainta G104MF-IP67 die-cast Al as the default feed box
    - **Why:** 150.4 g against 65.7 g for the PC version (TME gross weights), so it adds about 85 g at the feed of a handheld foldable antenna. The TME page lists no gasket, temperature or finish data. The shielding benefit does not matter here, because the cased SAWbird already has a metal case. Keep it only as the fallback if Gainta cannot confirm UV-stabilised PC.
  6.
    - **Name:** Amphenol RF 202112-10 / TE 3-1478985-0 SMA caps
    - **Why:** Dearer: 3.89 (Amphenol, 0 stock, 12-week lead) and 4.76 (TE), against 2.74-4.13 (TME) or 3.845 at 10 (DigiKey) for the GCT.
  7.
    - **Name:** Essentra EFA02-43-001 PVC SMA cap
    - **Why:** WORSE: no tether, no IP rating, unverified thread engagement, and PVC ages under UV and cold. Its price comes from an aggregator listing.
  8.
    - **Name:** Generic rubber SMA dust caps (eBay.de lot of 100)
    - **Why:** Rejected for now: no IP rating or sealing data, no tether, unknown compound, and the price is from a search snippet only (the page returned 403). They could replace the GCT caps (saving about 30-40) only after they pass the full-kit IPX4 spray test and a heat and UV soak, and only with a tether added.
  9.
    - **Name:** Orion GRM40-45 filter kit
    - **Why:** The datasheet gives no media flammability, material or pressure-drop data, and it costs 2.38 against 1.38 for the UL 900 Class II Qualtek media. Also, 45 PPI is the higher-drop grade for a low-pressure 5 V fan. If a snap-in guard is wanted, use GRM40-30 behind the steel mesh, only after the 5 Pa bench test.
  10.
    - **Name:** F.H. Brundle 316 150-mesh (Angle B pin)
    - **Why:** Likely WORSE on intake drop (my model, not measured): 34% open area and 0.098 mm aperture. A Wieghardt-type screen-loss estimate gives roughly 10-20 Pa at a fan-face velocity of about 1.2 m/s, against the 5 Pa budget, unless the intake is about 3x the fan face. The foam already does the dust job. It is also a UK seller (EU duty and handling fee). Use a coarser 316 mesh from an EU seller.
  11.
    - **Name:** LAPP SKINTOP ST-M 12x1.5 (53111400) for all entries
    - **Why:** Its 3.5-7 mm clamping range does not seal RG316 (about 2.5 mm), and -20 C is its minimum. A pre-terminated SMA plug (8 mm hex) will not pass an M12 gland bore. Keep it for RG58/LMR-195 only.
  12.
    - **Name:** Spelsberg Abox 025-L
    - **Why:** WORSE: +40 C maximum operating temperature, no UV rating, membrane entries instead of glands (Angle B, RS data).
  13.
    - **Name:** Generic ABS IP65 boxes, generic M12 vents, DIY printed ASA boxes
    - **Why:** No measured ingress, airflow or UV data. The IP claims are the seller's own (Angle B). Not proven equal.
  14.
    - **Name:** 3M Temflex 2155
    - **Why:** WORSE: 80 C rating, ASTM D4388 Type I, 3-year shelf life, against 90/130 C, Type III and 5 years for Scotch 23 (3M TDS).
  15.
    - **Name:** Generic self-fusing silicone tape
    - **Why:** No ASTM D4388 class and no independent test; it does not adhere to the connector body.
  16.
    - **Name:** Permatex 81150 / 22058 dielectric grease
    - **Why:** 81150 is a 0.33 oz (about 9.4 g) tube at 8.80 USD, about 9x MOLYKOTE 4's cost per gram (100 g for EUR 10.71 ex VAT). No TDS or temperature data was verified, and only US retail prices exist (EU duty and handling fee). The 22058 price has an ASIN mismatch.
  17.
    - **Name:** MG Chemicals 8462
    - **Why:** Not cheaper: 17.53 USD per 85 mL against about 12.3 USD per 100 g for MOLYKOTE 4.
  18.
    - **Name:** Non-indicating silica gel (eBay.de, audiosense.be)
    - **Why:** WORSE: saturation cannot be seen, and no DMF-free or DIN 55473 statement. The prices are unverified (one page returns 404).
  19.
    - **Name:** OP/TECH Rainsleeve Small 8 in
    - **Why:** Too small: 4.5 in diameter.
  20.
    - **Name:** Budget alternative in STACK: caps + rain sleeve only
    - **Why:** WORSE: it drops the intake protection, vents, LNA boxes, glands, tape, grease and desiccant, so it fails IP5X at the intakes and leaves the feed LNAs exposed. It is a reduced kit, not an analog. Relabel it in STACK as 'reduced protection, no rain or dust use'.
- **Confidence:** medium
- **Conditions or tests:** 1. LNA box fit (before ordering 3). Measure the cased SAWbird+ GOES (and any other feed LNA) with mated plugs; Nooelec publishes no dimensions. The G201 (58x64x35 mm outside, interior not published) must hold the LNA plus straight mated SMA plugs with an RG316 bend, or right-angle plugs. If it cannot, use the next larger Gainta IP67 PC size, not the Hammond by default.
  2. Box UV. Get a written statement or datasheet that the Gainta PC is UV-stabilised. If there is none, use the G104MF-IP67 and accept about 85 g more per box.
  3. SMA cap safety. With each GCT cap fitted on a panel jack, centre-to-shell resistance must read open (above 10 MOhm). Confirm the chain is present. Fit caps only with the bias tees off (labd default).
  4. F port. Use only a non-conductive weather cap, never a 75-ohm terminator cap, because the LNB rail carries 13/18 V DC.
  5. Intake pressure drop. Measure the mesh plus foam at the operating point of the NF-A4x10 5V fan and of the blower: 5 Pa or less (manometer, or tach/flow comparison against an open intake). If it is over, enlarge the intake area, or use 30 PPI foam and a coarser mesh.
  6. Whole device. IPX4 spray test (IEC 60529 oscillating tube or hand-held spray, 10 min) with every cap fitted and the fans running: no water at the GX12/M8, the LAB BUS or the battery bay. Then a dust check at the intakes.
  7. Each LNA box, closed with its vent and glands or bulkheads fitted. IPX5 jet test (12.5 L/min, 3 min): no water inside, and the humidity card unchanged.
  8. Vent mounting. Each vent on a flat land 2.0-3.5 mm thick with the nut (Y version). Never facing up. One vent per LNA box, display cavity and battery bay. These vents do not replace the P2 battery thermal-runaway vent path.
  9. Grease. Confirm in the Dow TDS that MOLYKOTE 4 is compatible with silicone O-rings before putting it on the vents' silicone O-rings. Until then, use it on the chloroprene gland seals and threads only, and never on RF mating faces.
  10. Price. Re-check the TME tier prices (the visible price was hidden; stock fields conflict) and the EU price of the OP/TECH sleeve and of the 316 mesh before ordering. Re-check the start date of the EU handling fee.
- **Stack changes:** STACK.md line 276 (2.9):
  - Price: 45-110 becomes about 116-168 USD ex VAT before shipping.
  - Status: 'model' becomes 'partly verified (SKUs pinned)'.
  - Group 2.9 subtotal: 178-313 becomes about 249-371.
  - Relabel the budget alternative 'caps + sleeve' as reduced protection, not an analog.
  - Add the SKU list from 'chosen' to the BOM and to parts.yaml.
  
  Case CAD (D15):
  - M12 vent lands at 2.0-3.5 mm wall thickness on the display cavity and the battery bay.
  - Intake openings sized for 5 Pa or less with a coarse mesh; enlarge them if the bench test fails. Retainer pockets for the 36.4 mm foam.
  - No intake faces upward.
  - Tether anchor points beside each SMA port and beside the F, USB and LAB BUS ports.
  
  Feed LNA boxes:
  - One VENT-PS1YBK-O8002 each, mounted on a side wall, never on top.
  - Coax entries: LAPP ST-M12 for 5 mm coax, plus a 2-5 mm-range M12 gland or a reducing insert for RG316. Alternatively, use IP67 O-ring SMA bulkhead jacks with short internal RG316 jumpers, because pre-terminated SMA plugs do not pass an M12 gland. Unpriced: add as an open BOM item.
  - One silica sachet per box.
  
  Sourcing (Europe):
  - TME (PL): LTW vents, GCT caps, Gainta boxes, LAPP glands.
  - DigiKey: LTW and GCT as a backup, Qualtek foam.
  - Silmid EU sites: MOLYKOTE 4 and Scotch 23 (Scotch 23 was out of stock at Silmid ES with a 26-day lead).
  - Avoid UK and US sellers for small lines (EUR 3 duty per tariff line and EUR 2 handling fee from about 1 Nov 2026, plus import VAT; operator note 35, not re-verified).
  - Use only orange cobalt-free silica gel in the EU.
  
  No changes to power rails, connectors' electrical pinout, drivers or Ubuntu 24.04 packages. The Q6A and the antennas are untouched. All hard rules hold.
- **Sources:**
  - https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/7136/Amphenol%20LTW_Pressure%20Relief%20Vent%20Group.pdf
  - https://www.digikey.com/en/products/result?keywords=VENT-PS1YBK-O8002
  - https://www.tme.eu/en/details/vent-ps1ybk-o8002/enclosures-other-accessories/amphenol-ltw/ltw-vent-ps1ybk-o8002/
  - https://www.digikey.com/en/products/detail/gct-gradconn/RFCT-SMA-CAP-GS-1/12822389
  - https://www.tme.eu/en/details/rfct-sma-cap-gs-1/sma-smb-smc-connectors/gct/
  - https://www.tme.eu/en/details/g201-ip67/multipurpose-enclosures/gainta/
  - https://www.tme.eu/en/details/g104mf-ip67/multipurpose-enclosures/gainta/
  - https://www.tme.eu/en/details/hm-1554b2gy/multipurpose-enclosures/hammond/1554b2gy/
  - https://orionfans.com/productFiles/datasheet/GRM40.pdf
  - https://www.qualtekusa.com/images/Fan%20Accessories/PDFDrawings/09150m.pdf
  - https://www.digikey.com/en/products/detail/qualtek/09150-M-45/273619
  - https://www.nooelec.com/store/sawbird-goes.html
  - https://www.nooelec.com/store/sawbird-plus-goes.html
  - https://www.nooelec.com/store/sawbird-plus-noaa.html
  - https://silmid.com/es/silicones/silicone-compounds/MOLYKOTE-Dow-Corning-4-Electrical-Insulating-Compound-SAE-AS-8660-in-various-sizes
  - https://www.silmid.com/es/tapes/insulating-tapes/3m-23-rubber-splicing-tape-19mmx9-15mt-roll/
  - https://multimedia.3m.com/mws/media/41153O/scotch-all-voltage-splicing-tape-23.pdf
  - https://multimedia.3m.com/mws/media/37550O/3m-temflex-rubber-splicing-tape-2155.pdf
  - https://www.tme.eu/en/details/skintop-st-m12x1.5/glands/lapp/53111400/
  - https://www.bhphotovideo.com/c/product/469774-REG/OP_TECH_USA_9001132_18_Rainsleeve_Set_of.html
  - https://www.pictureline.com/products/op-tech-rainsleeve
  - https://www.fhbrundle.co.uk/products/270615046__Stainless_316_150_Mesh_45_46g_071_Sq_Ft_Woven_1_22M_wide_roll
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md (lines 76, 276, 839, 896)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md (items 34-35)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/wk_ltw_pdf/ltw.txt (extracted LTW catalogue text)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/wk_orion_pdf/grm40.txt
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/wk_qualtek_pdf/q.txt

