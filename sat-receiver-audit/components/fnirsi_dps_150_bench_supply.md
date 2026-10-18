# Fnirsi dps 150 bench supply: повні відповіді субагентів

Тексти відповідей агенти писали англійською; тут вони наведені повністю, без скорочень.

## Адверсаріальна перевірка (`verify`)

_Run `wf_5b7fd800-40f`_

- **Part:** FNIRSI DPS-150 portable programmable bench supply (Lab extended tier, qty 1). Used for current-limited bring-up, LNA bias at 4.5 V with a 90 mA gate, LNB bias at 13.0-13.4 V plus the 18 V polarisation check, the Q6A at 9-12 V, BMS and buck boards, and the ESD-mat 10-20 V check. Runs from the Anker 737 (20 V PD) or the 4S pack.
- **Current pick:** FNIRSI DPS-150 through Elektor, which redirects the order to its partner store Eleshop (Elektor SKU 21002). Read live on 18 Oct 2026: "€ 59,00 (incl. VAT) … Order Now (at Eleshop)", and Shopify shows available=true. Box: DPS150, 2 alligator leads, Micro-USB cable, manual. Eleshop's own page returns HTTP 403, so its shipping cost and actual checkout price are unknown.
- **Current price usd:** 66.38 (EUR 59.00 incl. VAT at 1.125 USD/EUR), plus Eleshop shipping, which is not known. STACK v1's 73-75 is stale.
- **Decision:** replace_conditionally
- **Chosen:** Same unit, different seller: FNIRSI DPS-150 "Std. / Without Adapter" (SKU DPS-150-BU, variant 46011574550746), bought direct from the fnirsi.com EU storefront (https://www.fnirsi.com/products/dps-150). No other model survived the checks. This applies only if the checkout conditions below hold. Otherwise keep Elektor/Eleshop. If the user already has a Botland order, Botland is a second fallback.
- **Chosen price usd:** 62.64 = EUR 55.68 (fnirsi.com product JSON and Storefront cart for country DE/NL/FR/IT/ES/AT, read 18 Oct 2026; inventory_quantity 417). UNVERIFIED: whether EUR 55.68 includes VAT (the cart returns totalTaxAmount=null, and the price is the same in countries with 19-22% VAT), and whether shipping is free for the EU ("Free Shipping Over $30 USD*" banner). If VAT is added on top, it becomes EUR 66.26 in DE (about $74.54) and the swap is off.
- **Saving usd:** 3.74 (EUR 3.32) against Elektor's EUR 59.00 list price, plus whatever Eleshop charges for shipping. That is 10.36-12.36 against STACK v1's 73-75. The saving is zero if the checkout conditions fail.
- **Equivalence proof:** The hardware is the same, so every spec that matters is equal by identity, and the seller is the manufacturer.
  - fnirsi.com lists the same specs as Elektor: 0-30 V / 0-5 A / 150 W; 0.01 V / 0.001 A resolution; CC/CV; <20 mV ripple (spec); 0.49% load regulation; 96.3% full-load efficiency; 2.8 in 320x240 tilting IPS; 106x76x28 mm, 178 g; PD/QC/DC input, 5-30 V recommended (5-32 V on Elektor).
  - Protections are the same: OVP, OCP, OPP, OTP, LVP, reverse input, reverse output and short circuit.
  - The Std box matches Elektor's: host, 2 alligator leads, Micro-USB cable, manual.
  - The PC link is the same: Micro-USB, USB CDC-ACM serial at 115200 baud. The mtabini fnirsi-dps150 1.0.0 library opens it as /dev/cu.usbmodem* on macOS, which is CDC-ACM, not CH340. It uses the mainline cdc_acm driver on Ubuntu 24.04 arm64. No radio.
  - Measured behaviour (ripple about 0.9 mVrms to 28 mVpp, the reported periodic pulse, OCP trip of about 500 ms, overshoot not yet measured) belongs to the unit, not the seller, so it is unchanged and the goods-in gates stay.
  
  Quality and channel:
  - Buying from the manufacturer removes counterfeit risk.
  - It adds FNIRSI's 30-day return and 2-year warranty, which the warranty page says apply "only … purchased directly from fnirsi.com". Elektor/Eleshop does not get this.
  - What is weaker, stated openly: the seller is outside the EU, so EU legal-guarantee claims are harder to enforce than against Eleshop (NL). If the order is not dispatched from the EU warehouse, delivery is 15-25 business days.
  - The DPS-150 is in FNIRSI's "In stock at EU warehouse" collection, but the page says this is "except for some options", so the Std variant has to be confirmed at checkout.
  - No hard rule is touched: it is a DC bench supply, used conducted only, with no transmitter and no loop.
- **Rejected:**
  1.
    - **Name:** FNIRSI Official Store on AliExpress, item 1005007630120253 (company 香港菲尼瑞斯科技有限公司, 2,683 sold, 4.9 stars, ships from CN)
    - **Why:** Price is real but temporary: EUR 54.69 incl. 19% VAT with free shipping (DE search grid, taxRate 0.19, 18 Oct 2026), while the grid tag says the 30-day low is EUR 60.44 (promo, platform subsidy). Landed cost adds the EUR 3 per-item duty, which may not be in the price, plus the EUR 2 Union handling fee from about 1 Nov 2026: EUR 57.69-59.69 ($64.90-67.15). So the saving is at most EUR 1.31, and nothing or negative once the handling fee applies. It loses FNIRSI's 2-year warranty and the EU-seller legal guarantee. The item page is blocked by JavaScript, so it was not confirmed that the EUR 54.69 SKU is the bare Std unit.
  2.
    - **Name:** Other AliExpress DE listings, EUR 54.69-60.69 (1005007614877705, 1005008845271535, 1005007615398406, 1005008305772652 and others)
    - **Why:** Store identity is not shown for most of them, so authenticity and refurb risk are unproven. They have the same duty, fee and warranty problems as above and are not cheaper than fnirsi.com.
  3.
    - **Name:** Botland (PL), product 27837
    - **Why:** EUR 58.19 incl. VAT on a 19% basis (ex-VAT EUR 48.90), InStock, priceValidUntil 2026-11-02, plus GLS EU shipping from EUR 8.07, gives EUR 66.26 ($74.54) landed, which is dearer. The only exception is when it rides on an existing Botland order: then it saves EUR 0.81 against Elektor, which is the fallback-2 case.
  4.
    - **Name:** Eleshop.eu direct (the seller behind Elektor)
    - **Why:** A search snippet shows EUR 46.00 excl. VAT (EUR 54.74-55.66 incl. VAT), but the page returns 403 to curl and WebFetch, so price, VAT basis, shipping and stock are unverified. Do not use it as a booked price. Check it in a browser on the day: if its checkout total is at or below fnirsi.com's, buy at Eleshop, because an EU seller wins a tie.
  5.
    - **Name:** proshop.de 3476741
    - **Why:** Snippet only (page 403): EUR 59.51 incl. VAT plus EUR 4.99 shipping = EUR 64.50 ($72.56). Not cheaper.
  6.
    - **Name:** eBay.de China sellers (365521593088 and others)
    - **Why:** Snippets only: about EUR 58.5-58.6 including import charges. Not cheaper than fnirsi.com, higher grey-import and counterfeit risk, no FNIRSI warranty.
  7.
    - **Name:** Rotorama EUR 61.49, BerryBase EUR 68.90
    - **Why:** More expensive than the current pick.
  8.
    - **Name:** FNIRSI DPS-150 Plus with 100 W adapter (EUR 80.21 at fnirsi.com, EUR 74 ex VAT DPS150PD at Eleshop)
    - **Why:** More expensive. The adapter is not needed because the Anker 737 is the source.
  9.
    - **Name:** ALIENTEK DP100
    - **Why:** Not cheaper: ALIENTEK Official Store on AliExpress DE EUR 69.99 incl. VAT (grid, 18 Oct 2026), Openelab EUR 73.45. Its spec is also worse: 0.96 in 160x80 display against 2.8 in 320x240, 100 W against 150 W nameplate, no barrel input. The labd backend would need HID instead of CDC serial. Forum reports from the searches (about 1600 uF output capacitance, output-off spike, overshoot) were not re-measured by me, and are not needed to reject it.
  10.
    - **Name:** FNIRSI IPS3608 (36 V 8 A 285 W, PD 3.0)
    - **Why:** EUR 141-178 on AliExpress DE. Much more expensive.
  11.
    - **Name:** Riden RD6006 / RD6006P, Joy-IT DPS5005 (DIY with PD trigger and case)
    - **Why:** No native PD sink, so each needs a trigger board, a case and wiring, which is an extra failure point and worse build quality. RD6006 and DPS5005 have worse ripple (100 mVpp spec) and accuracy. RD6006P has no measured turn-on overshoot. None is cheaper as a working set. The RD6006W variant has Wi-Fi.
  12.
    - **Name:** Sinilink XY-SK120X and the XY family
    - **Why:** Ripple 150 mVpp typical, documented overshoot on its sibling (XYS3580), 120 W, no PD sink, no reverse-output protection. Worse and a risk to the LNA/LNB.
  13.
    - **Name:** VICTOR 3005M mains bench SMPS (EUR 36.19, AliExpress DE)
    - **Why:** Mains-only. It cannot run from the Anker 737 or the 4S pack, does not fit the Pelican bench kit, and its ripple, overshoot and PC interface are unverified. Fails stack compatibility.
  14.
    - **Name:** Used DPS-150
    - **Why:** No listings found on Kleinanzeigen or eBay.de (search B). No warranty, and the known failure modes (firmware brick, back-feed damage) cannot be seen before purchase.
- **Confidence:** medium
- **Conditions or tests:** BEFORE ORDERING (same day, in a normal browser, to the user's EU address):
  1. fnirsi.com checkout for the Std / Without Adapter variant must show all of these:
     - a total of no more than EUR 55.68, with VAT included and no separate tax, duty or handling-fee line;
     - shipping EUR 0;
     - preferably the "Ships from EU Warehouse" label under the button.
  2. Compare that total with the Eleshop checkout total for the plain DPS150 (not the DPS150PD), shipping included. Buy whichever is lower. On a tie or within EUR 1, buy at Eleshop (EU seller).
  3. If FNIRSI adds VAT on top (EUR 66.26 in DE) or charges shipping that makes it dearer than Eleshop, keep Elektor/Eleshop. If the user already has a Botland basket, Botland at EUR 58.19 is fallback 2. Ignore any coupon code until the checkout shows it applied: code DPS154 was not found on the page.
  
  GOODS-IN (any seller; return within 30 days if any check fails):
  1. Genuine unit: FNIRSI label and box, CE mark. Record the firmware version from the device menu.
  2. USB: on the Q6A, lsusb shows a CDC-ACM device and /dev/ttyACM* appears. Record the VID:PID for the udev rule. `fnirsi-dps150 --port /dev/ttyACM0 read-state` works.
  3. Overshoot (Hantek, 1 MS/s): output-enable at 13.2 V into 100 Ohm must peak at 13.6 V or less. Also capture output-off at light load while running from the Anker 737, and look for the reported 150 ms pulse every 530-600 ms.
  4. Headroom: maximum Vout from 20 V PD at 0.3 A must be at least 18.0 V, or the 18 V LNB polarisation test comes off the PD path.
  5. Accuracy against the AN8009 at 4.50 V and 13.20 V, and the CC limit at 90 mA into a short. Readings must be within the published ±(0.1%+5 mV) and ±(0.1%+3 mA).
- **Stack changes:** BOM (STACK.md line 367): price 73-75 becomes 62.64 (EUR 55.68, fnirsi.com EU storefront, Std / Without Adapter), marked conditional. Fallback: Elektor/Eleshop EUR 59.00 incl. VAT ($66.38) plus shipping. Status becomes "verified 18 Oct 2026 (VAT basis at fnirsi.com unverified)". Add a warranty note: FNIRSI's 2-year warranty applies only to fnirsi.com orders. Extended total: -$10.4 to -$12.4 against v1, or -$6.6 to -$8.6 on the fallback.
  
  Driver and interface correction: search B was wrong to say "USB-C, CH340".
  - The PC link is the Micro-USB port: USB CDC-ACM, cdc_acm module, /dev/ttyACM*, 115200 baud. It is not CH340/ch341 and not the USB-C port; the USB-C port is the PD power input only.
  - udev rule: match the VID:PID read at goods-in, symlink /dev/lab/dps150, mode 0600 for labd, and set ENV{ID_MM_DEVICE_IGNORE}="1" so ModemManager does not send AT probes to the supply.
  - labd backend: fnirsi-dps150 1.0.0 from PyPI (needs only pyserial; based on cho45's reverse-engineered protocol), pinned.
  - Cabling: the Micro-USB cable from the box goes to the LAB USB hub.
  
  Usage rules to add (FNIRSI precautions):
  - Battery and BMS work: put a reverse-blocking Schottky (5 A, 40 V or more) in series with the output. FNIRSI recommends it, and it covers the reported battery back-feed failure. Allow about 0.4-0.5 V of drop when setting 16.8 V.
  - Never feed the USB-C and DC inputs at the same time. Keep the input between 5 and 30 V.
  - Connect inductive or capacitive loads before enabling the output.
  
  No change to rails, connectors (other than the Micro-USB lead), case or Pelican layout. No hard rule is affected.
- **Sources:**
  - https://www.elektor.com/products/fnirsi-dps150-dc-power-supply-150-w (page text: '€ 59,00 (incl. VAT) … Order Now (at Eleshop)'; box list incl. Micro USB cable; reviews mention Micro USB PC link)
  - https://www.elektor.com/products/fnirsi-dps150-dc-power-supply-150-w.json and .js (SKU 21002, price 59.00, available=true, read 18 Oct 2026)
  - https://www.fnirsi.com/products/dps-150.json?country=DE (also NL, FR, IT, ES, AT: Std EUR 55.68, compare-at 90.60; USD storefront $57.99; PL PLN 249)
  - https://www.fnirsi.com/products/dps-150?country=DE (inventory_quantity 417; product in the 'In stock at EU warehouse' collection 'except for some options'; Std package list; precautions on input 5-30 V, both inputs, reverse diode for batteries)
  - https://www.fnirsi.com/pages/shipping-policy (duty payment service for EU orders under $150; 15-25 business days international)
  - https://www.fnirsi.com/pages/warranty-policy (2-year warranty only for fnirsi.com orders)
  - https://de.aliexpress.com/w/wholesale-fnirsi-dps-150.html (FNIRSI Official Store 1005007630120253 EUR 54.69, taxRate 0.19, 30-day low EUR 60.44; ALIENTEK Official DP100 EUR 69.99; IPS3608 EUR 141-178; VICTOR 3005M EUR 36.19)
  - https://botland.store/laboratory-power-supply/27837-fnirsi-dps150-laboratory-power-supply-unit-0-30v-5a-5907085527239.html (EUR 58.19, display_prices_tax_incl true, InStock, GLS EU from EUR 8.07)
  - https://eleshop.eu/fnirsi-dps150-mini-power-supply.html (HTTP 403; EUR 46.00 excl. VAT from search snippet only, unverified)
  - https://www.proshop.de/Instrumente/FNIRSI-DPS150-DC-Programmable-Mini-Laboratory-Power-Supply-Unit/3476741 (snippet EUR 59.51 incl. VAT + EUR 4.99 shipping; page 403)
  - https://pypi.org/pypi/fnirsi-dps150/json (v1.0.0, pyserial, /dev/cu.usbmodem* = CDC-ACM; repo github.com/mtabini/fnirsi-dps150, protocol.py DEFAULT_BAUDRATE 115200)
  - https://raw.githubusercontent.com/cho45/fnirsi-dps-150/main/README.md (serial protocol)
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/operator_notes.md items 34-35 (EUR 3 per-item duty from 1 Jul 2026; EUR 2 handling fee from about 1 Nov 2026)

