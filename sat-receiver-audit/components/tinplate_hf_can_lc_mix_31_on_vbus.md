# Tinplate hf can lc mix 31 on vbus: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e32114dd-52d`_

- **Part:** HF+ shield assembly: tinplate can around the Airspy HF+ Discovery, plus the damped VBUS LC (100 uH / 100 uF) and a Mix-31 ferrite on the short shielded micro-USB pigtail from CH334F H4. Tier core, group HF, qty 1.
- **Current pick:** Tinplate HF+ can + LC + Mix-31 on VBUS. STACK.md names no part numbers. My verified reference build is Schubert Art. 9 (111x74x30, 0.5 mm tinplate) + Bourns SRR1260-101M + Panasonic EEU-FR1C101 + R-C damper + Fair-Rite 0431164281 31-mix snap-it.
- **Current price usd:** STACK.md gives 8-15 (estimate, model). I verified a reference build at 10.94-11.24: the can at EUR 5.58 German gross (= 6.27), inductor 1.11, cap 0.41, damper 0.3-0.6 (not verified), ferrite 2.85. Net of VAT it is 9.94-10.24. Shipping excluded. Rate: 1 EUR = 1.1241 USD.
- **Decision:** replace_conditionally
- **Chosen:** A concrete build of the same design:
  - Otto Schubert tinplate housing Art. 6B (111x55x20 mm outside, inside 109x53x18, 0.5 mm tinplate, two L-walls and two slip-on lids).
  - Bourns SRR1260-101M (no change).
  - Panasonic EEU-FR1C101 100 uF/16 V plus an R-C damper of about 1 ohm and 220 uF (no change).
  - TWO Fair-Rite 2631480002 solid #31 sleeves in series on the micro-USB pigtail, held with heat-shrink. Fair-Rite lists this sleeve as the solid equivalent of the 0431164951 snap-it.
  Fallbacks: Art. 6 (111x55x30) at the same price if 18 mm inside height is too tight. Art. 9 only if the Boni tee or G6K board has to go inside the can. Keep 0431164281 if the lead is thicker than 4.9 mm.
- **Chosen price usd:** 8.56-8.86 with the can at German gross price (Art. 6B EUR 4.25 = 4.78 + 1.11 + 0.41 + damper 0.3-0.6 + 2 x 0.98). Net of VAT: 7.79-8.09. Real cash outlay is higher because Schubert has a EUR 20 (22.48 USD) minimum order, gross, excluding shipping. Shipping is quoted per order, payment is prepayment or SEPA only, and orders go by e-mail.
- **Saving usd:** About 2.38 per unit against the verified reference build (2.15 net): 1.49 on the can (Art. 6B instead of Art. 9) and 0.89 on the ferrite (2 x 2631480002 instead of 0431164281). The new build sits at the bottom of the STACK's 8-15 estimate. It is also about 38 g lighter (model). Because of the Schubert EUR 20 minimum, the can saving is only real if the order is filled with items the stack will actually use.
- **Equivalence proof:** Can: Art. 6B against Art. 9.
  - Same maker and the same product family. The Schubert page says "aus 0,5mm Weißblech gefertigt", "gut lötbar", "HF – DICHT und ROHS-Konform", "Innen minus 2mm".
  - Same construction. The page's parts image shows two L-shaped walls and two slip-on lids; the separate FD flange lids are optional.
  - So material, thickness, seams and lid contact are identical. Only the footprint is smaller.
  - Cavity TE101 is about 3.1 GHz against 2.5 GHz (model), far above 260 MHz.
  - Inside 53x109x18 mm holds the HF+ (45x60x10 per airspy.com) and a straight micro-USB plug. The LC (12.5 mm inductor, radial caps lying flat) fits beside the plug in the 53 mm width.
  - The heat path (HF+, thermal pad, lid, mid plate) is set by the HF+ footprint, not by the can size. The 60-minute sealed test still confirms it.
  - Mass is lower: about 87 g against 123 g (model: 0.5 mm steel at 3.93 kg/m2).
  
  Ferrite: two 2631480002 sleeves against one 0431164281 snap-it, from Fair-Rite's typical single-turn impedance.
  - 2631480002 per sleeve: 37/104/129/192/318/356 ohm at 1/5/10/25/100/250 MHz (table 1); 34/88/115/175/295/267 ohm (table 2).
  - 0431164281: 20/75/104/170/315/380 ohm (table 1); 28/83/105/180/310/240 ohm (table 2).
  - K9YC: the impedances of chokes in series add.
  - Two sleeves therefore give +87% to +270% (table 1) and +90% to +143% (table 2) at every listed frequency. That is better everywhere, including above the guaranteed minimums at 10, 25 and 100 MHz.
  - Bore is 4.95 mm (+0.25/-0). Two sleeves weigh 24 g against 26 g and are 50.8 mm long.
  - A solid sleeve cannot spring open. K9YC says snap-ons need a cable tie for this reason.
  - DigiKey 1934-1377-ND: $0.98 at qty 1, 60,395 in stock, Active. 0431164281 is $2.85, 103,515 in stock.
  - Ferrite DC bias does not matter: the VBUS current and its return flow in the same cable, so the core sees no net current.
  
  LC: unchanged and re-verified. SRR1260-101M: 100 uH +/-20%, shielded, Irms 1.7 A, Isat 1.7 A, DCR 180 mOhm max, SRF 6.07 MHz, -40 to 125 C, $1.11, 81,074 in stock. That is more than 2x the 0.817 A worst-case limit with the LAB-port resistor (34.8k). EEU-FR1C101 is $0.41.
  
  Not affected: all parts are passive, so no rails, interfaces or drivers change, and nothing changes against receive-only, no-loop or conducted-only.
- **Rejected:**
  1.
    - **Name:** Fair-Rite 0431164951 31-mix snap-it (4.9 mm bore), the searcher's main ferrite swap
    - **Why:** Not proven to be no worse. Only Fair-Rite's table 1 shows it +2-3% against 0431164281. The same page's second typical table gives 25/75/100/169/280 ohm against 28/83/105/180/310 ohm, which is -5% to -11% at 1-100 MHz. It also costs more at DigiKey (2.46, the searcher's figure, which I did not re-check) than two 2631480002 sleeves (1.96). The bore limit is the same, and it needs a cable tie.
  2.
    - **Name:** A single Fair-Rite 2631480002 sleeve (the second searcher's swap, 0.98)
    - **Why:** Much better at 1-10 MHz (+6% to +85%), but table 2 shows -3% at 25 MHz and -5% at 100 MHz, and table 1 shows -6% at 250 MHz, against 0431164281. That would trade away part of the VHF suppression on the HF+ VHF2 role without saying so. A second sleeve (+0.98) removes the deficit. A single sleeve is only acceptable if the user accepts that VHF trade.
  3.
    - **Name:** Schubert Art. 5B 74x55x20 or Art. 5 74x55x30 (3.54 USD gross), the second searcher's can
    - **Why:** Inside length is 72 mm: the 60 mm HF+ plus SMA plus micro-USB plug leaves no room for the 12.5 mm inductor. It only works with the SMA through the wall, a right-angle plug and the LC outside the can, and none of that is proven. The price was verified. Fit not shown, so rejected unless the HF+ is measured on arrival.
  4.
    - **Name:** Schubert Art. 9 111x74x30 (reference)
    - **Why:** Not worse, but EUR 1.33 dearer and about 36 g heavier (model). Only needed if the Boni tee or G6K board must go inside the can. STACK 5.8 and C17 place them beside the can.
  5.
    - **Name:** Fair-Rite 0431173951
    - **Why:** About 40% lower impedance at every HF point (12/45/65/103 ohm).
  6.
    - **Name:** Fair-Rite 2631102002 large sleeve, 2 turns
    - **Why:** An upgrade, not a saving: about 2.71 (searcher's figure, not verified), 56 g, and it is not known whether the plug passes through it.
  7.
    - **Name:** Wurth 7447714101 WE-PD 100 uH
    - **Why:** Dearer (2.26), DCR 198 against 180 mOhm, 1.5 against 1.7 A, out of stock (searcher's data).
  8.
    - **Name:** Wurth 7447709101 100 uH
    - **Why:** Dearer (2.57); lower SRF of 4.3 MHz; 10 mm tall.
  9.
    - **Name:** Sunlord, LCSC or generic 100 uH, and AliExpress LC or USB filter modules
    - **Why:** Specs and price not verified, and no measured S21, ripple or Isat data. A saving under 1 USD is not worth the risk.
  10.
    - **Name:** Generic unbranded clip-on ferrites
    - **Why:** Unknown mix and no 1-30 MHz data. Risk of counterfeits.
  11.
    - **Name:** Schubert WB1 sheet folded into a DIY can (2.06)
    - **Why:** No factory-formed overlapping lids, so seam and lid fit depend on the builder. Worse build quality unless an A/B test proves otherwise.
  12.
    - **Name:** industriegehaeuse.de GH02AG003/320
    - **Why:** No published price, so it cannot be shown to be cheaper.
  13.
    - **Name:** Perancea FFL screening boxes
    - **Why:** About 4-5x the price, and FFL1T is too small.
  14.
    - **Name:** Teko 273.16
    - **Why:** Discontinued.
  15.
    - **Name:** Copper-clad FR4 sub-compartment
    - **Why:** 35 um of non-ferrous copper gives much weaker LF/MF H-field absorption (about 1.5 dB against about 68 dB at 100 kHz, model). Adamczyk & Spence measured the same trend.
  16.
    - **Name:** Aluminium, diecast or Nobu machined case
    - **Why:** Non-ferrous, so weaker LF H-field absorption. No measurements. Nobu is sold only on Amazon Japan.
  17.
    - **Name:** Mint tin
    - **Why:** Unknown thickness, lacquered, with a hinge seam all round. No measurement.
  18.
    - **Name:** No external can (rely on the HF+ internal can)
    - **Why:** Not proven inside this handheld near the bucks. The stack's own A/B test needs the can to run it.
- **Conditions or tests:** 1. Lead OD: measure the shielded micro-USB pigtail. It must be 4.9 mm or less (sleeve bore 4.95 +0.25/-0). Thread both sleeves on before soldering the CH334F H4 pad end, and leave at least 55 mm of straight lead. If the lead is thicker, keep 0431164281 ($2.85) with a cable tie.
  2. Fit: when the HF+ arrives, measure its length including the SMA. Confirm that the HF+, a straight plug and the LC fit inside 53x109x18 mm, with the SMA passing through the end wall and its nut bonding the shell to the can. Otherwise use Art. 6 (same price). Use Art. 9 only if the Boni tee or G6K board moves inside.
  3. Lids: confirm in the order e-mail that the price includes both slip-on lids. The page text is silent; the parts image shows them.
  4. Stack bench tests, all conducted only:
     - HF+ A/B with and without the can (RBW 1 Hz at 40/60/77.5/162/490/518/4209.5 kHz and 1/7/14 MHz).
     - VBUS ripple from 1 kHz to 30 MHz at the HF+ pin, plus turn-on ringing.
     - 60 minutes sealed: HF+ temperature and current.
     - Impedance (Z) of the sleeve pair on a test wire with the LiteVNA, against the 0431164281 figures at 1-250 MHz.
  5. Inrush (knock-on, applies to every candidate): the total capacitance behind the HF+ load switch must charge within the switch's overcurrent deglitch at the final limit (C x 5 V / I_lim). 100 + 220 uF at 0.3 A is about 5.3 ms against the TPS2553's 7.5 ms typical; a 470 uF damper (about 9.5 ms) could latch a -1 part. Keep the damper at 220 uF and check that FAULT stays clear at turn-on.
  6. Schubert ordering: EUR 20 gross minimum, shipping extra, prepayment or SEPA by e-mail. Fill it with items the stack will use: a spare 6B, D1000 1 nF feedthroughs (EUR 0.68 each) and WB1 sheet.
  Not checked: the WebSearch budget was used up (a limit shared by every agent in this run), so EU resellers that might sell Schubert cans without the minimum (reichelt, box73) were not checked. The user can ask in a follow-up.
- **Stack changes:** - BOM line "Екран HF+" (8-15, DIY, model) becomes: Schubert 6B + SRR1260-101M + EEU-FR1C101 + 1 ohm / 220 uF damper + 2x Fair-Rite 2631480002. About $8.6-8.9 (can at German gross price), $7.8-8.1 net. Vendors: Schubert (new, e-mail order, EUR 20 minimum) and DigiKey, which rides in the existing week 1-2 DigiKey order.
  - Mass: the line "HF+, екран і перемикач 0.1 kg" is under-modelled. A 0.5 mm tinplate can alone weighs about 87 g (6B), 100 g (Art. 6) or 123 g (Art. 9) (model). Set the line to about 0.15-0.17 kg with 6B: HF+ 32 g (searcher's figure; airspy.com gives no weight), can 87, ferrites 24, LC about 5, G6K board about 15. Device total rises by 0.05-0.07 kg. This build is still about 38 g lighter than the Art. 9 + snap-it reference.
  - Case and CAD: the top-right can footprint is about 112x56x21 mm with lid rims, so it no longer needs 74 mm width. The G6K board and Boni tee stay beside it, outside the can, as STACK 5.8 and C17 say.
  - Assembly: thread the sleeves onto the pigtail before soldering to the CH334F pads, then heat-shrink. Clamp the HF+ SMA to the can wall with its nut. Bond the lid to the mid plate.
  - Keep the damper at 220 uF (inrush, item 5).
  - No changes to rails, connectors, drivers or software. Hard rules are unaffected: all parts are passive, with no emitter, no loop and no H-field probe.
- **Confidence:** medium
- **Sources:**
  - https://www.schubert-gehaeuse.de/weissblechgehaeuse.html
  - https://www.schubert-gehaeuse.de/media/images/weissblech_einzelteile_neu-large.jpg
  - https://www.schubert-gehaeuse.de/versand.html
  - https://www.schubert-gehaeuse.de/weissblechgehaeuse_zubehoer.html
  - https://fair-rite.com/product/round-cable-emi-suppression-cores-2631480002/
  - https://fair-rite.com/product/round-cable-snap-its-431164281/
  - https://fair-rite.com/product/round-cable-snap-its-431164951/
  - https://www.digikey.com/en/products/result?keywords=2631480002
  - https://www.digikey.com/en/products/result?keywords=0431164281
  - https://www.digikey.com/en/products/result?keywords=SRR1260-101M
  - https://www.digikey.com/en/products/result?keywords=EEU-FR1C101
  - https://airspy.com/airspy-hf-discovery/
  - http://k9yc.com/RFI-Ham.pdf
  - https://incompliancemag.com/near-field-shield-effectiveness-evaluation-using-h-field-probe/
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_B_receivers_rf.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json

