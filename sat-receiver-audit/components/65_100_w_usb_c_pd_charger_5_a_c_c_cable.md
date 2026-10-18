# 65 100 w usb c pd charger 5 a c c cable: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_a268b76e-da0`_

- **Part:** 65-100 W USB-C PD charger + 5 A C-C cable (Charging group, core, qty 1). It is the only external source for the IP2368 4S charger port, which goes enclosure USB-C, then TPS259470A (OVLO about 22 V, ILIM about 3.5 A), then the COUT/Try.SRC board.
- **Current pick:** Generic branded single-port 65-100 W one-way USB-C PD wall adapter + 5 A C-C cable. No model is named. The STACK rule is a PDO of at least 60 W, qualified with the FNB58.
- **Current price usd:** 35-60 (STACK estimate, not verified)
- **Decision:** replace_conditionally
- **Chosen:** IKEA SJÖSS 65 W 1-port USB-C charger, type E2502-EU (art. 006.097.43), + IKEA RUNDHULT USB-C to USB-C 1.5 m, 100 W / 5 A (art. 606.209.26 or 206.177.04). Bought direct from IKEA, which has a 365-day return. Fallback if a gate fails or the user needs charging below 5 °C or above 35 °C: Xiaomi Mi 65W Fast Charger with GaN Tech, model AD65GEU, EUR 29.99 at mi.com/de with a 5 A 1 m C-C cable in the box ($33.71). It must pass the same gates. Cable fallback: UGREEN 100 W 5 A 1 m, SKU 70427, EUR 10.99 ($12.35).
- **Chosen price usd:** 25.83 incl. 19% DE VAT (21.71 ex VAT). Charger EUR 12.99 = $14.60 and cable EUR 9.99 = $11.23, both checked on ikea.com/de on 18 Oct 2026. The charger is also EUR 12.99 in ES. Stock is 'Verfügbarkeit prüfen' (varies by store). Delivery or Click & Collect fees are extra unless picked up in store. FX 1 EUR = 1.1241 USD.
- **Saving usd:** 9.17-34.17 (about 21.7 against the 47.5 midpoint). The Xiaomi AD65GEU fallback saves 1.29-26.29.
- **Equivalence proof:** Checked against the stack's needs, not marketing text:
  (1) Port role: a single USB-C wall adapter, so source-only. This avoids the DRP vs Try.SRC flapping that rules out the Anker 737.
  (2) PDOs from the E2502-EU manual (Technical data, read from the PDF): 5/9/12/15 V at 3.0 A and 20.0 V at 3.25 A = 65 W, plus PPS 5.0-16.0 V at 3.0 A. ChargerLAB measured the same set on the CN twin with a POWER-Z KM003C. 65 W is at least the 60 W PDO rule and equals the bottom of the pick's own 65-100 W range. The IP2368 at RISET 15k draws about 49-52 W, i.e. 2.5-2.6 A. That is 75-80 % of the rating, under 3.25 A and under the eFuse ILIM of about 3.5 A.
  (3) Over-voltage: the highest fixed PDO is 20 V and PPS tops out at 16 V. There is no EPR, so it stays below the TPS259470A OVLO of about 22 V.
  (4) Build, from the ChargerLAB teardown of 10 Oct 2026 (E2502-CN):
  - Infineon IGD70R140D2S CoolGaN 700 V.
  - Injoinic IP2006 QR flyback with OTP, OVP, UVP, OPP and brown-in/out.
  - DK5V100R10VL synchronous rectifier.
  - Injoinic IP2723T protocol IC (USB-IF PD3.0/PPS certified, TID 3135) and LT80N03 VBUS MOSFET.
  - Mains side: T3.15 A fuse, 1.5D-11 NTC, 10D681K MOV, bifilar CM choke plus a DM choke, X2 0.15 uF, two SMD Y caps.
  - Bulk 2x27 uF + 2x33 uF at 400 V; output 680 uF/25 V; PCBA fully potted.
  This is the same protection set as branded 65 W units.
  (5) Efficiency, declared in the manual: 83.5 % average active (test voltage not stated), 73.6 % at 10 % load, 0.08 W no-load. The no-load figure equals the Xiaomi 65 W that HKJ measured.
  (6) Legal and not counterfeit: IKEA of Sweden AB is named as manufacturer. Bought from IKEA directly.
  (7) Mechanical: Europlug, 100-240 V, 1.6 A max. 65.4x48.3x32.1 mm and 152.5 g (CN unit), within the 200 g kit limit. The Anker 715 EU page lists 149.69 g, so the IKEA is not heavier than the branded EU class.
  (8) Cable: 5 A rated ('Nennstrom: 5 A'), 100 W, so non-EPR as the Pinecil note wants. CE, overheat protection in the plug, 1.5 m, which is within the 1.5-2 m limit.
  
  What is NOT proven, and is why the replacement is conditional:
  - No one has published ripple, EMI, hipot or sustained-load thermal data for any SJÖSS 65 W.
  - The teardown shows one 680 uF output cap and no output LC stage is reported, so ripple may be higher than average.
  - The manual documents 'Output power will decrease to 45.0W if the charger becomes too hot'. If that is done by lowering OCP rather than re-sending Source_Capabilities, the IP2368 at about 50 W could hit a VBUS reset loop.
  - The teardown is of the CN unit. One IKEA DE reviewer says the EU unit has no PPS; PPS is not used here.
  
  Disclosed limits, not silent:
  - Operating range 5-35 °C, indoor use only. The Xiaomi AD65GEU publishes 0-40 °C. Angle B's floor ('at least 0/5-35 C') accepts 5-35 °C, but the stack's cell NTC window starts at 0 °C, so the 0-5 °C band is lost with the IKEA.
  - Larger volume (about 101 cm3 vs about 64 cm3 for the Anker 715).
  - No 20 V/5 A headroom. That is common to every 65 W unit and inside the pick's 65-100 W spec. The DPS-150 and Pinecil run from the Anker 737 bank per radio_lab, and the Pinecil is capped at 60 W anyway.
- **Rejected:**
  1.
    - **Name:** Xiaomi Mi 65W GaN AD65GEU (EU) as primary
    - **Why:** Not rejected outright; it is the fallback. Search A was wrong on two points. (1) HKJ's figures (33 mV rms / 414 mVpp, OCP about 3.1-3.3 A, 72 °C) are for the older CDQ07ZM, a 60x57x28 mm unit with folding legs. The EU AD65GEU is a different 30.8x30.8x56.3 mm design and is unmeasured. (2) A 5 A 1 m cable is in the box, so the set costs $33.71, not $46.07. It has the better 0-40 °C range, but costs $7.88 more than IKEA and is just as unmeasured, so it is used only if the IKEA fails. Price comes from a mi.com/de copy saved on 18 Oct 2026 (InStock, EUR 29.99). The live page returned 403 at verification.
  2.
    - **Name:** Xiaomi CDQ07ZM (CN market)
    - **Why:** Folding flat-pin non-EU plug, so it needs an adapter on a 65 W brick and is not an EU-market product. Price and availability are unverified. It is also measurably noisier and hotter than the Apple 61W on HKJ's bench.
  3.
    - **Name:** Anker 715 / Nano II 65W A2663
    - **Why:** The US unit ($29.99 on anker.com, in stock) has a US plug, so it fails the EU Type C/F plug requirement. The EU unit costs EUR 42.99 ($48.33), plus a cable ($12.35), for $60.68: no cheaper than the top of the range. The EU spec also lists input as 200-240 V only and 149.69 g. No ripple or thermal data.
  4.
    - **Name:** UGREEN Nexode Air 65W
    - **Why:** PDOs, the included cable's rating and certifications appear only in images (unverified), and there are no measurements. EUR 27.99 sale or 34.99 regular ($31.46-39.33), so more expensive than IKEA even before a 5 A cable.
  5.
    - **Name:** Anker 737 PowerCore 24K bank
    - **Why:** DRP: reaudit D expects flapping or failure against the COUT/Try.SRC IP2368. $109.99, not cheaper. It stays as the bench/instrument bank only.
  6.
    - **Name:** Apple 61W A1718 (used)
    - **Why:** 61 W is below the pick's 65 W lower bound. No 12/15 V PDOs. Used, discontinued, high counterfeit risk, aged bulk capacitors, price unverified (eBay 403). It is the quietest on HKJ's bench (15 mV rms), but that does not offset being worse in power and provenance.
  7.
    - **Name:** IKEA SITTBRUNN C-C 1 m 3 A (EUR 2.50)
    - **Why:** 3 A with no e-marker caps the charger at 60 W, below the 5 A cable spec. It would carry the 2.6 A load, but using it would be a silent spec trade.
  8.
    - **Name:** Generic AliExpress 5 A e-marked cables
    - **Why:** No traceable seller and no measurements. Fake or misprogrammed e-markers and thin VBUS conductors are common.
  9.
    - **Name:** No-name 100 W dual GaN P-TR-378J-2C100-EU
    - **Why:** No maker, seller or price. Input is 200-240 V only. Power splits 65+30 W when both ports are used. No measurements. Not traceable for EU legality.
  10.
    - **Name:** Choetech PD72-1C3U
    - **Why:** Failed HKJ hipot (arcing at 2.83/4.24 kV). No-load power 0.46 W.
  11.
    - **Name:** DIY Mean Well 24 V brick + SW35xx/IP27xx PD module
    - **Why:** Adds a second switching stage (a new spur source), mains DIY wiring and unproven PD compliance. Larger, heavier and not certified as a unit.
  12.
    - **Name:** Used OEM laptop USB-C 65 W (Lenovo/Dell/HP)
    - **Why:** No measurements, unknown age, worn captive cables, frequent counterfeits, price unverified.
- **Confidence:** medium
- **Conditions or tests:** Adopt the IKEA set only if every gate passes. On any failure, return it to IKEA (365 days) and run the same gates on the Xiaomi AD65GEU. If that also fails, keep the generic branded pick.
  G0 Goods-in: the label reads E2502-EU with CE and IKEA of Sweden AB.
  G1 FNB58 PDO dump: 5/9/12/15 V at 3 A, 20 V at 3.25 A, nothing above 20 V. PPS 16 V or absent is fine; PPS is unused. FNB58 e-marker readout of the RUNDHULT: 5 A, at least 20 V, 100 W (non-EPR). If there is no e-marker, swap to the UGREEN 70427.
  G2 Sustained load and foldback: a full IP2368 charge (RISET 15k, about 50 W) from about 20 % SoC with FNB58 1 s logging, run twice: at 23-25 °C, and at about 35 °C ambient or while running mode B. Pass:
  - no VBUS dropout, hard reset or repeated renegotiation;
  - any 45 W fold shows as a clean step down in IP2368 draw without a VBUS interruption;
  - charger case surface stays at about 75 °C or below.
  G3 Cable drop: 0.25 V or less between the charger VBUS and the enclosure port at 2.6 A. Otherwise use the UGREEN 1 m.
  G4 Ripple: Hantek 6022BE, AC-coupled with a spring ground at a USB-C breakout, 20 V at 2 A into a 10 ohm resistor of 50 W or more (HKJ method). Must be no more than 33 mV rms and 414 mVpp, the HKJ Xiaomi 65 W 'good' level.
  G5 Load-release step from 2.6 A to 0: VBUS peak below 21.5 V, so the 22 V OVLO does not nuisance-trip.
  G6 Receiver A/B, charger charging vs battery-only, in every non-HF mode (VHF/UHF/L-band on the RTL, Lime and tinySA), plus the HF+ watch-list gate (40/60/77.5/162/490/518/4209.5 kHz, ±5 kHz). Fail on any line 3 dB or more above the floor. Charging stays banned in HF/LF Quiet regardless.
  G7 tinySA conducted VBUS spur scan through a DC block and 20 dB or more of attenuation. Conducted only.
  Usage rule (disclosed trade): mains charging indoors at 5-35 °C ambient, with the charger not covered or bagged. If charging in rooms below 5 °C is required, the IKEA does not qualify and the AD65GEU (0-40 °C) is the part.
- **Stack changes:** STACK row 'PD-зарядний пристрій':
  - Replace the generic entry with: IKEA SJÖSS 65W E2502-EU (006.097.43) + RUNDHULT 1.5 m 100 W/5 A (606.209.26); IKEA DE; $25.83 incl. VAT; status 'price verified, conditional on G0-G7'.
  - Fallbacks: Xiaomi AD65GEU with included 5 A cable, $33.71; cable UGREEN 70427, $12.35.
  - Delete 'Бюджет: Anker 737 (стенд)' as an alternative for this row. It is DRP and not a substitute; it stays only in the bench kit.
  Charging group total:
  - Drops by $9.17-34.17.
  Add the usage rule to section 5 (Заряд):
  - Mains charging indoors at 5-35 °C ambient.
  - A 45 W thermal fold is expected; the IP2368 auto-derates, giving about 13 % slower charging.
  No electrical, connector, driver or case changes:
  - The 20 V maximum PDO and PPS of 16 V or less keep the TPS259470A OVLO (about 22 V) and ILIM (about 3.5 A) settings.
  - RISET 15k and RVSET 5.1k are unchanged.
  - The enclosure USB-C with CC1/CC2 direct is unchanged.
  - There is no software side.
  Field kit:
  - Weight is about 153 g + 60 g for the cable, within the 200 g charger allowance plus cable.
  - Volume is about 101 cm3, slightly bulkier than an Anker Nano-class unit.
  Hard rules:
  - Not affected: this is a passive mains-to-USB source with no TX, no loop and no signal source.
  Method note:
  - The WebSearch budget was exhausted (one query was refused). All checks used WebFetch on primary pages (ikea.com DE/ES, the IKEA manual PDF, ChargerLAB, lygte-info, anker.com US/EU, eu.ugreen.com) and same-day scratchpad copies of mi.com/de and the IKEA search JSON.
- **Sources:**
  - https://www.ikea.com/de/de/p/sjoess-ladegeraet-mit-1-usb-ausgang-65-w-00609743/
  - https://www.ikea.com/de/de/manuals/sjoess-ladegeraet-mit-1-usb-ausgang-65-w__AA-2584269-1-2.pdf
  - https://www.ikea.com/es/es/p/sjoss-cargador-usb-con-1-puerto-65-w-00609743/
  - https://www.chargerlab.com/teardown-of-the-ikea-sj%C3%B6ss-65w-1-port-usb-charger/
  - https://www.ikea.com/de/de/p/rundhult-usb-c-auf-usb-c-schwarz-weiss-60620926/
  - https://www.ikea.com/de/de/p/sittbrunn-usb-c-auf-usb-c-weiss-90618540/
  - https://www.mi.com/de/product/mi-65w-fast-charger-with-gan-tech/ (saved copy /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/chg_dl/mi65.html; live page 403 at verification)
  - https://lygte-info.dk/review/USBpower%20Xiaomi%20Mi%2065W%20USB-C%20charger%20CDQ07ZM%20UK.html
  - https://lygte-info.dk/review/USBpower%20Apple%2061W%20USB-C%20Power%20Adapter%20UK.html
  - https://lygte-info.dk/review/USBpower%20Choetech%20USB-C%20Desktop%20charger%2072W%20PD72-1C3U%20UK.html
  - https://www.anker.com/products/a2663
  - https://www.anker.com/eu-en/products/a2663
  - https://eu.ugreen.com/products/ugreen-usb-c-to-usb-c-100w-5a-charger-cable-nylon-braided
  - https://eu.ugreen.com/products/nexode-air-usb-c-charger-65w-gan
  - /home/user/lizbeth307/sat-receiver-audit/STACK.md
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/reaudit_D_power_mech_display_lab.json
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md

