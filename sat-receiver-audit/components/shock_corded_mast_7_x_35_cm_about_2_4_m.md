# Shock corded mast 7 x 35 cm about 2 4 m: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_37583a7b-1a8`_

- **Part:** Shock-corded mast (7 x 35 cm, about 2.4 m) + guys + stake (Supports, antenna-foldable tier, qty 1 set). Role: holds the Boni-Whip (189 g, about 17 cm, BNC) at 2 m or more for DCF77/MSF/TDF and NAVTEX. The C17 ground stake sits at the antenna.
- **Current pick:** Generic shock-corded tent-pole mast, 7 x 35 cm, about 2.4 m, with 3 guys and a stake. No SKU or material is named in STACK.md (row 221) or final_completeness.json. The verifier treats the quality floor as 8.5 mm 7001-T6 aluminium with metal ferrules, sections of 35 cm or less including the ferrule, non-conductive guys and a steel stake.
- **Current price usd:** 15-50 is the stack's model estimate; it has no SKU and is unverified. The cheapest verified way to build this spec costs about 68.4, plus a stake (unpriced) and shipping. That is the Robens DIY 8.5 mm set at EUR 47.90 = 53.8 plus a Forclaz guy kit at EUR 12.99 = 14.6, at FX 1.124. No established seller offers an aluminium mast with sections of 35 cm or less for 50 or less. The Buddipole short mast is 79 and out of stock.
- **Decision:** keep
- **Chosen:** KEEP the current line, with a tighter spec.
  - Mast: shock-corded 8.5 mm 7001-T6 aluminium tent pole, metal ferrules, each section 35 cm or less including the ferrule, 2.4 m or more erected.
  - Guys: 3 non-conductive guys at about 2/3 height.
  - Stake: galvanised or stainless steel, 25-30 cm, doubling as the C17 ground stake.
  - Top: a printed tip adapter that holds the whip ABOVE the mast top.
  Verified purchase route:
  - Robens DIY Pole Set 8.5 mm, 7001-T6, 9 x 44.5 cm, 0.35 kg, 400.5 cm (Karkkainen FI). Cut 8 sections to about 30.5 cm of tube plus the ferrule, which gives about 2.44 m with one spare section. Re-tension the 400 cm shock cord.
  - One Forclaz Ultra-light Reflective Guy Ropes kit (10 m of 2 mm rope rated 20 kg, 4 runners, 32 g; Decathlon CY).
  - One 25-30 cm steel stake.
- **Chosen price usd:** About 68.4 plus the stake (unpriced, estimated 2-6) plus shipping.
  - Robens: 53.8 (EUR 47.90; the page does not say whether VAT is included; over 20 in stock).
  - Forclaz: 14.6 (EUR 12.99 incl. VAT).
  STACK's 15-50 should be raised to about 70-80 or marked unverified.
- **Saving usd:** 0 (keep). No candidate is both cheaper and not worse.
  The only cheaper real option is the Decathlon Quechua 8.5 mm fibreglass DIY build: about 11.2 for the pole kit plus 14.6 for guys, so about 25.8 plus a stake. It would save about 42.6 against the verified aluminium build, but it is worse in mass and durability. It is offered only as an explicit trade the user can accept, never as a silent swap.
- **Equivalence proof:** The specs that matter here and what the kept part must meet:
  - Height 2.4 m or more. PA3FWM tn07: 'The strength of the received signal is directly proportional to the height of the antenna above ground', so 2.0 m is about -1.6 dB and 1.8 m about -2.5 dB.
  - Packed section 35 cm or less, including the ferrule (foldable-kit rule).
  - Top-load stiffness for 189 g plus adapter plus coax. Model for an 8.5 x about 0.7 mm 7001-T6 tube (wall thickness assumed): EI is about 0.93e7 N mm^2, so the pinned Euler load over 2.4 m is about 16 N.
  - Mass inside the 0.5-0.75 kg Boni + mast budget.
  - Durability class.
  - Mast material and RF. PA3FWM: 'Whether the mast is conductive or not hardly matters for the reception'. A conductive mast must carry the whip 'not besides but above the mast' and should be grounded.
  - Non-conductive guys and a steel ground stake.
  
  The kept part as built (Robens, cut to 8 sections):
  - 2.44 m erected, packed 35 cm or less.
  - 7001-T6 per the seller page.
  - About 87 g/m including fittings (0.35 kg over 4.005 m), so about 0.22 kg for the pole.
  - Total with Boni, guys and stake is about 0.5 kg, inside the budget.
  
  The adversarial test of the closest cheaper candidate, the Quechua 8.5 mm GRP kit (EUR 9.99 on decathlon.com.gr; 10 x 50 cm, 654 g, 100% glass fibre, 2-year warranty, 4.4/5 from 241 reviews):
  - Height after cutting is 2.48-2.64 m: equal or better.
  - Packed length is 35 cm or less after cutting: equal.
  - Stiffness: EI is about 0.9-1.15e7 N mm^2 if the rods are solid (E 35-45 GPa, my calculation), which is equal. The page calls them 'tubes', so solidity is unverified. The mass of 131 g/m fits a solid rod.
  - Non-conductive: equal by PA3FWM, and the whip mount is easier.
  - Mass is 131 g/m against about 87 g/m, which is +0.1-0.13 kg at 2.4-2.6 m: WORSE.
  - Durability class: Wikipedia (Tent) says 'Cheap poles are made of tubes of fibreglass ... more expensive aluminium alloys are the material of choice for added strength and durability': WORSE.
  - Cut glass-fibre ends splinter and need sealing, and the build needs 8 sections against 7.
  
  It fails on two specs, so it cannot replace the current part under the user's rule. Every other candidate is either more expensive or fails height or packed length (see the rejected list).
- **Rejected:**
  1.
    - **Name:** Decathlon Quechua 8.5 mm fibreglass tent-pole kit, DIY cut to 8 x about 33 cm, plus Forclaz guys (search B pick)
    - **Why:** Cheaper (about 25.8 plus stake, verified EUR 9.99 GR plus EUR 12.99 CY) but WORSE in two specs. Mass: 654 g/5 m = 131 g/m against about 87 g/m for 7001-T6 (Robens 0.35 kg/4.005 m), so +0.1-0.13 kg. Durability class: fibreglass is the cheap tier, aluminium is chosen 'for added strength and durability' (Wikipedia Tent). It also has cut-end splinter risk. It is unproven: solid or hollow is not stated (the page says 'tubes'), and no load test exists. Kept only as an explicit user-accepted budget trade.
  2.
    - **Name:** Buddipole Shockcord Mast, short version (33 cm folded, 2.4 m, 0.45 kg)
    - **Why:** Spec-equal or better (better top threads), but price and availability fail: USD 79.00 on buddipole.com and OUT OF STOCK (verified 18 Oct 2026); WiMo EUR 125.90, no longer available, redesign pending. No guys or stake included.
  3.
    - **Name:** Used Buddipole short mast (eBay, swap sites)
    - **Why:** No price could be verified (eBay returned 403). Shock-cord and section condition unknown. Not shown to be cheaper than new.
  4.
    - **Name:** Robens DIY Pole Set 8.5 mm 7001-T6, used as-sold (9 x 44.5 cm)
    - **Why:** As sold, 44.5 cm sections break the 35 cm pack rule. Once cut, it is not an analog but the verified build route for the KEPT spec (EUR 47.90, over 20 in stock, 0.35 kg, 400.5 cm). It is not cheaper than the estimate's upper end.
  5.
    - **Name:** Decathlon Forclaz MT900 aluminium segments 32.5 cm, bought singly (7-8 needed)
    - **Why:** Prices exist only in search snippets (EUR 7.95-11.90 each; Decathlon CH returned 403). 8 segments plus cord is about EUR 64-95 = 72-107, more than the Robens route. Alloy and ferrule not stated.
  6.
    - **Name:** Intents Outdoors (Orson) 11 mm aluminium pole, 4 x 35 cm, two joined
    - **Why:** Shop JSON: NZ$36.99 each, 125 g, 4 x 35 cm, 11 mm. The title says 125 cm but the description says 130 cm. Alloy not stated. Two poles are NZ$73.98, about 43 at an unverified FX rate, before NZ-to-EU shipping and EU import VAT, which put the landed price at about 55-65 or more (estimate). A joiner sleeve adds a weak joint. Non-EU seller. Not cheaper landed.
  7.
    - **Name:** AliExpress unbranded 7.8 m 13-section 7001-T6 pole (USD 36.99)
    - **Why:** About 60 cm sections need cutting. Unbranded, with the 7001-T6 claim unverified and the store and diameter not shown, so it fails 'established seller, not mislabelled'. Not clearly cheaper once shipping is added.
  8.
    - **Name:** AliExpress unbranded 2 m 5-section awning pole (USD 16.69)
    - **Why:** 2.0 m max is -1.6 dB at LF against 2.4 m (PA3FWM: signal proportional to height). Sections are about 40 cm, which breaks the pack rule. Alloy, diameter and brand unknown.
  9.
    - **Name:** Ferrino 8.5 mm 7001-T6 replacement sections (2 x 50 cm, EUR 28.60, snippet only)
    - **Why:** 50 cm sections break the pack rule. About 4-5x the price per metre. Price not fetched.
  10.
    - **Name:** CAO fibreglass repair kits 11 mm / 9.5 mm (H2R Equipements, 4 kits)
    - **Why:** Verified: EUR 13.20 (11 mm) or EUR 11.40 (9.5 mm) per kit incl. VAT. Four kits are EUR 45.60-52.80 = 51-59, so not cheaper. Made to order (15-18 days). Fibreglass durability class and mass (about 0.5 kg for the 11 mm mast) are worse. Half the rods need loose sleeves glued in.
  11.
    - **Name:** SOTAbeams Mini Telescopic Mast 4.1 m (GBP 20.95 incl. UK VAT)
    - **Why:** Verified: 51 cm packed, which breaks the 35 cm pack rule. Friction-fit telescopic joints, no load rating. Non-UK buyers pay GBP 17.46 ex VAT plus import VAT.
  12.
    - **Name:** Tatonka Tarp Pole 180 cm / DD Hammocks 2.2 m / REI 8 ft tarp poles
    - **Why:** Height below 2.4 m (1.8 m is -2.5 dB, 2.2 m is -0.8 dB) and/or packed length well over 35 cm (45.5 cm, about 55-60 cm, 72 cm).
  13.
    - **Name:** Tree or fence mount (stack budget alternative)
    - **Why:** Site-dependent, with no defined height, and fails where there are no trees. A hung Boni swings, and the stack forbids climbing. PA3FWM recommends 'ideally in the open field'. Not not-worse; it stays only as the stack's budget fallback.
  14.
    - **Name:** Guy/stake sub-kits: MSR Groundhog 6-pack (EUR 22.90-27.00) and AliExpress nylon paracord with tensioners (USD 4.88)
    - **Why:** MSR costs more than the needed sub-kit and its aluminium Y-stakes are not a steel ground stake. Nylon paracord stretches more than polyester or Dyneema, and it is unbranded with unverified rope specs. The verified Forclaz kit (10 m x 2 mm, 20 kg, 4 runners, 32 g, EUR 12.99) is the reference.
- **Conditions or tests:** Acceptance on the bench and in the yard for the kept build:
  1. Every cut section is 35 cm or less including the ferrule. Ends are deburred and the shock cord is re-tensioned. Erected height is 2.4 m or more.
  2. Guy at about 2/3 height with light tension, 3 N or less per guy.
     - Model: the 8.5 mm tube has an Euler load of about 16 N pinned over 2.4 m, so firm top-only guying can buckle it. Guying at 2/3 height raises the lower span to about 36 N.
     - Load test: hang 0.6 kg at the top for 10 min. Pass means no buckling, no ferrule damage, and a lateral bow of 3 cm or less.
  3. The Boni body sits wholly above the mast tip in the printed adapter (PA3FWM: a conductive mast must be below the plate, not beside it), with BNC strain relief and a drip loop.
  4. Mast foot bonded to the C17 steel stake: check under 1 ohm with the DMM.
  5. Deploy time 8 min or less (stack target 5-8 min). Lower the mast above about 20 km/h of wind.
  6. Before buying, confirm with the seller:
     - that the Forclaz rope is non-conductive (polyester or Dyneema with no metallic reflective tracer); otherwise use plain polyester cord;
     - whether Karkkainen's EUR 47.90 includes VAT, and the shipping cost.
  
  If the user explicitly accepts the trade (+0.1-0.13 kg mass, fibreglass durability class) to save about 42.6, the Quechua 8.5 mm GRP build may replace the part. It must first pass the same tests and confirm the rods are solid. Not done by default.
- **Stack changes:** Changes to the stack:
  - BOM:
    - Add a printed PETG/ASA tip adapter that holds the Boni-Whip ABOVE the 8.5 mm pole tip, with BNC strain relief. The Bonito/WiMo pole mount 18067.MH (EUR 16.00, from 20.11.2026) fits only 28-40 mm tubes, so it cannot be used on this mast.
    - Add a ground-lead clamp from the mast foot to the C17 steel stake.
    - Specify the stake as galvanised or stainless steel, 25-30 cm.
  - Spec text for STACK row 221: '8.5 mm 7001-T6 aluminium, metal ferrules, sections 35 cm or less incl. ferrule, 2.4 m or more, 3 non-conductive low-stretch guys at about 2/3 height with light tension, steel stake'.
  - Price: raise row 221 from 15-50 to about 70-80 (verified route), or mark it unverified. The antenna-foldable tier total rises by about 20-30 at the top end.
  - Weight: about 0.22 kg pole, 0.03 kg guys and 0.05-0.1 kg stake, so Boni plus mast is about 0.5-0.55 kg, inside the 0.5-0.75 kg budget.
  - No change to power rails, connectors, drivers or the case. The pack bundle is about 35 cm x 8 sections of 8.5 mm.
  - Tools for the cut: tube cutter and deburrer, done at home.
  Search note: the shared WebSearch budget was exhausted before this step, so no new searches were made. Decathlon IE/CH/US/CY product pages returned 403/429. Figures marked as model or estimate are not measured.
- **Confidence:** medium
- **Sources:**
  - https://www.pa3fwm.nl/technotes/tn07.html
  - https://www.wimo.com/en/18067-mh
  - https://bonito.net/en/boni-whip-2/
  - https://www.buddipole.com/shockcordmast.html
  - https://www.wimo.com/de/buddipole-aluminum-schockcord-mast
  - https://www.karkkainen.com/en/robens-diy-8-5-mm-silver-tent-pole
  - https://decathlon.com.gr/en/p/3740-quechua-85-mm-fiberglass-tent-pole-kit.html
  - https://decathlon.com.cy/products/ultra-light-reflective-guy-ropes-orange
  - https://www.h2r-equipements.com/accessoire-de-tente-camping-randonnee/10065-cao-kit-reparation-arceau-fibre.html
  - https://www.sotabeams.co.uk/mini-telescopic-mast-4-1-m-13-5-ft/
  - https://en.wikipedia.org/wiki/Tent
  - https://intentsoutdoors.co.nz/products/130cm-ultralight-aluminium-tent-pole.json
  - https://decathlon.ch/en/p/jonc-aluminium-pour-arceau-ø-8-3-mm-x-32-5-cm-tente-mt900/_/R-p-326623
  - https://lynxgear.lv/en/online-store/camping/tatonka-tarp-pole-180-cm-5-piece-aluminium-support.htm
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/final_completeness.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_B_receivers_rf.json

