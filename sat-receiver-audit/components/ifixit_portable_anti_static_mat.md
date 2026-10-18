# Ifixit portable anti static mat: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_e5582d4c-0a2`_

- **Part:** Portable anti-static mat (bench tier, Bench electronics, qty 1)
- **Current pick:** iFixit Portable Anti-Static Mat, iFixit part no. IF145-202-5 (iFixit US)
- **Current price usd:** 34.95 (iFixit US, 'Ready to ship', re-verified 18 Oct 2026; US price excludes any tax; shipping to the EU plus import VAT would be extra)
- **Decision:** keep
- **Chosen:** Keep the same part, iFixit IF145-202-5, and buy it from the iFixit EU store (ships from Germany). This is a change of seller only, not a different part; STACK already lists iFixit EU for this line.
- **Chosen price usd:** 33.70 = EUR 29.95 at the ECB reference rate of 16 Oct 2026 (1 EUR = 1.1253 USD). The product page does not say whether VAT is included; an EU B2C price normally includes it, and the page's own strings contain 'Includes VAT, VAT can be removed at checkout'. Confirm at checkout. Shipping is extra unless the iFixit cart reaches EUR 65: EUR 4.90 to Germany (DHL, 1-2 days) or EUR 8.90 to PL/FR/IT/ES/NL/AT (UPS, 1-4 days). Landed cost is about $39.22 in Germany or $43.72 elsewhere in the EU.
- **Saving usd:** $1.25 on the label price ($34.95 to $33.70), with no spec change. The real gain for a European buyer is avoiding US-to-EU shipping, import VAT and handling on a US order. That landed-cost saving is not quantified, because the US international shipping fee was not verified. No cheaper part from another vendor survived checking, so there is no part saving.
- **Equivalence proof:** Both pages show the same SKU: MPN/SKU IF145-202-5 in the EU page's structured data, and the same number on the US and UK pages. The specs are identical on the pages I fetched on 18 Oct 2026: 60 x 60 cm; surface resistance 10^7-10^9 Ohm, inside the S20.20 limit of 1e6 to under 1e9; ESD S4.1 / S20.20 (the US page says 'designed to meet', the EU page 'meets'; neither has a test report); 10 mm grounding snap; 1.8 m ground cord to a socket earth or a metal object, with a clip; adjustable wrist strap with an alligator clip (US page: 6 ft, 1 MOhm, adjustable to XL); foldable ('can be folded, packed, and deployed with ease'); raised border; ESD Safe true, not magnetic.
  
  Two differences, stated openly. (1) Guarantee: the EU page says '25-year producer guarantee', the US and UK pages say 'Lifetime'. This is a difference in wording only for this item, and EU statutory warranty applies on top. (2) Material: the same iFixit page lists 'Polyester' in the product JSON and 'Rubber & Nylon' in its comparison table. This conflict is on iFixit's side, not a difference between stores, and no heat rating is given either way.
  
  Weight and folded size are not published for any store. Fit in the Pelican 1450 is therefore a check on arrival (see conditions), not a proven fact.
- **Rejected:**
  1.
    - **Name:** iFixit IF145-202-5 from the iFixit UK store
    - **Why:** GBP 27.99 is about $37.33 (ECB GBP 0.84385), which costs more than the EU store. iFixit's EU policy says UK orders must go through the UK store, so this is the wrong channel for an EU buyer and adds post-Brexit import handling. The product is identical, but it is not cheaper.
  2.
    - **Name:** Adafruit PID 4405 A4 ESD rework mat + iFixit wrist strap (Adafruit PID 5911), $15.45
    - **Why:** Verified on the page: 30 x 20 cm x 2 mm, about 1/6 of the 60 x 60 cm area. Resistance is only 'like 10's of Megaohms' and is not quantified. No ESD standard is stated. Folding is not mentioned and it is a 2 mm slab. No raised border. It is a US seller, so shipping and import VAT to the EU are extra. It is worse in area, documentation and portability.
  3.
    - **Name:** OEM (TME, Lodz) 2-layer rubber ESD table mat 600 x 400 x 2 mm, Botland, EUR 24.79 (about $27.90)
    - **Why:** Its 5-500 MOhm resistance is dissipative, so that spec is equal. It is worse elsewhere: area 0.24 m2 against 0.36 m2 (33% smaller); a 2 mm, 0.6 kg rubber slab that does not fold for the Pelican 1450; no wrist strap or ground cord included; no ESD standard (only a RoHS certificate); the '440 C' figure is an obvious typo. Adding a strap and a cord from another shop costs about EUR 29.95 or more, with two shipments.
  4.
    - **Name:** kaputt.de KPT-151-ESD ESD mat with ground cable (BerryBase), EUR 14.90 (about $16.77; about $19.58 with a Zhongdi ZD-152C strap at EUR 2.50)
    - **Why:** Page checked: 50 x 70 cm (0.35 m2, slightly below 0.36). No surface or ground resistance figure and no IEC 61340 or ANSI ESD claim, so it cannot be shown to be dissipative. The AN8008 cannot check 10^7-10^9 Ohm properly at home. No wrist strap included, foldability not stated, 0.76 kg gross, and 'Currently not available'. It fails the resistance and documentation specs, and its availability is not real.
  5.
    - **Name:** AliExpress generic mat + strap kits ($1.09-25.39 listings)
    - **Why:** No resistance value on any listing. All are smaller than 60 x 60 cm. No test reports, and the item pages need a login, so contents and prices are unverified. There is a known category risk that 'anti-static' mats are insulative (10^9-10^11) or conductive. Not provably not-worse.
  6.
    - **Name:** Used Desco/SCS portable field service kits (eBay)
    - **Why:** eBay returned 403, so no listing or price was seen. A used mat's present resistance is unknown, because contamination and wear shift it. It cannot be checked with the AN8008. No warranty, and a risk of counterfeit or mismatched cords.
  7.
    - **Name:** DIY Velostat / pink antistatic poly sheet with a home-made 1 MOhm cord
    - **Why:** From general knowledge (not fetched): carbon-loaded film is conductive (about 10^3-10^5 Ohm/sq), with CDM risk to the LNAs, Lime and Q6A; pink poly is about 10^9-10^11, near insulative. Neither is a dissipative work surface, and there is no standards basis.
  8.
    - **Name:** STAT-X Mobile ESD workstation (reichelt ESD SERVICEKIT, MPN 920000 000002), EUR 42.99 incl. VAT (about $48.38)
    - **Why:** Not cheaper. Verified 59 x 59 cm, 10-100 MOhm, coiled strap and cord, case, 0.735 kg. No standard is stated on the page.
  9.
    - **Name:** Desco 04599 portable field service kit (DigiKey DE), EUR 50.03 (about $56.30); SCS 8507 EUR 218.16
    - **Why:** More expensive than the current part. Out of scope under the 'cheaper' rule.
  10.
    - **Name:** Antistat 069-0010 table mat set (TME), about $45-51
    - **Why:** More expensive. A 120 x 60 x 2 mm rubber mat at 2.38 kg gross; not portable or foldable.
  11.
    - **Name:** ELME 157KIT 6090 table mat set (TME), about $57-62
    - **Why:** More expensive. A 90 x 60 x 2 mm rubber mat at 1.67 kg; not foldable. It does have 5-500 MOhm and 1 MOhm cords.
  12.
    - **Name:** Reichelt STAT-X / Bernstein / Weller mats and sets, EUR 38.99-159.99
    - **Why:** All more expensive than EUR 29.95. Most come without a wrist strap, or are large rigid mats.
  13.
    - **Name:** Velleman AS14 silicone ESD bench mat (from the search agent; not re-fetched by me)
    - **Why:** No price shown and out of stock, per the search agent. 60 x 50 cm, 990 g, not foldable, no strap. Worse in size, mass and portability, although better in heat rating.
- **Confidence:** high
- **Conditions or tests:** Acceptance on arrival, inside the EU 14-day withdrawal window. All tests are conducted bench measurements with no RF:
  (1) Wrist strap: measure snap-to-clip resistance with the AN8008. Expect about 1 MOhm (accept about 0.8-1.2 MOhm). An open circuit or under 0.5 MOhm is a fail.
  (2) Mat ground cord: check continuity, and note whether it has a series resistor (iFixit does not say).
  (3) Optional, indicative only (not the S4.1 method): put a 10-20 V DC current-limited source (DPS-150 from the PD bank) in series with the AN8008 on a uA/nA range across two flat metal weights about 25 cm apart on the mat. R = V/I should be 1e6 to 1e9 Ohm, i.e. about 20 nA to 20 uA at 20 V. The AN8008's nA resolution is taken from STACK and is not re-verified.
  (4) Fold test: the mat, the coiled strap and the cord must fit the Pelican 1450 interior (about 37 x 26 x 15 cm, from STACK) without a hard crease. If not, return it under the 14-day right.
  (5) Check which earth termination ships with the EU unit (clip or socket plug). The field bond point is the device's aluminium mid-plate or the bench common point, so a clip or a 4/10 mm stud is needed.
  Usage rule (no rating published): the Pinecil always goes in its stand, and hot work goes on a separate silicone pad.
  Coverage limits: the shared WebSearch budget was already used up (0 searches ran for me). Conrad, Mouser, Amazon.de, eBay and Farnell were blocked (403/503), and TME item pages gave prices only in structured data. So 'no cheaper not-worse analog exists' is proven only across iFixit US/EU/UK, reichelt, BerryBase, Botland, TME, DigiKey DE and Adafruit. A follow-up with search budget could check Conrad Toolcraft and Amazon.de field kits.
- **Stack changes:** BOM line 352 (STACK.md 'Антистатичний килимок'): seller iFixit EU (Germany); price $33.70 (EUR 29.95 at ECB 1.1253, 16.10.2026); add shipping EUR 4.90 DE / EUR 8.90 other EU unless the iFixit cart is EUR 65 or more; change status from 'не перевірено' to 'перевірено' (US $34.95, EU EUR 29.95 and UK GBP 27.99 all seen 18.10.2026). Add these notes: no heat rating (iFixit lists the material as both polyester and rubber & nylon); weight and folded size not published, so do the fold check; check the EU earth termination. Nothing changes for rails, connectors, drivers, firmware or the case. The bonding plan (mat snap, wrist strap and mid-plate to one common point) is unchanged. No hard rule is affected: it is a passive item with no RF, no TX, no loop or H-field probe, and the cords are not antennas.
- **Sources:**
  - https://www.ifixit.com/en-eu/products/portable-anti-static-mat
  - https://www.ifixit.com/products/portable-anti-static-mat
  - https://www.ifixit.com/en-gb/products/portable-anti-static-mat
  - https://www.ifixit.com/Info/EU_Shipping_Policy
  - https://www.ifixit.com/Info/EU_Shipping_Destinations_and_Options
  - https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
  - https://www.adafruit.com/product/4405
  - https://botland.store/soldering-mats/7913-esd-table-mat-600x400mm-beige-5903351249645.html
  - https://botland.store/soldering-mats
  - https://www.berrybase.de/en/esd-matte-mit-erdungskabel-und-anschluss-fuer-armband
  - https://www.berrybase.de/en/search?search=esd
  - https://www.reichelt.com/de/en/shop/product/mobile_esd_workstation-60392
  - https://www.reichelt.com/de/en/shop/search/esd%20mat
  - https://www.digikey.de/de/products/result?keywords=portable%20field%20service%20kit
  - https://www.tme.eu/en/details/ats-069-0010/esd-workstations/antistat/069-0010/
  - https://www.tme.eu/en/details/as-b60x90bl/esd-workstations/elme/157kit-6090-blue/
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md

