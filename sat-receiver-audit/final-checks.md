# Фінальні перевірки: повні відповіді субагентів

## integration:lens1 (run `wf_221684d9-b6c`)

- **Lens:** POWER + THERMAL. One power architecture for the handheld and bench kit: pack, J21 feed, every rail and regulator, spur behaviour, fuses and limits against real currents, cutoffs, charger and gauge, back-feed paths, runtime per mode, and heat inside the case (2000-nit display, Q6A, optional Lime, cells).
- **Issues:**
  1.
    - **Area:** Power budget / runtime
    - **Components:**
      - 4S1P Molicel P50B
      - IP2368 (4.10 V/cell)
      - labpowerd
      - INA228
    - **Problem:** The runtime figures in every file are too optimistic. They assume 72 Wh x 85% = 61 Wh usable and leave loads out. Three things cut usable energy and add draw. (1) Charging stops at 4.10 V/cell, about 93% SoC in my model. (2) A 13.6 V loaded cutoff stops at about 17% SoC. Together that leaves about 55-56 Wh. (3) The HF+, LNB, Boni-Whip, fans, converter losses and the LAB port are missing from the budgets, and the display is under-counted. On my model a no-Lime LEO pass draws 18.5 W at the pack and runs about 3.1 h, not 3.7-5.3 h. A Lime pass draws 31 W and runs about 1.9 h, not 2.2-2.6 h.
    - **Severity:** major
    - **Evidence:** report_research register #67 and #58 ('61-65 Wh usable to 13.6 V'), small_antenna_stack cost_size_power_delta (3.7-5.3 h at 11-17 W), npu_training budgets (2.2-2.4 h), register #63 (RVSET 5.1k = 4.10 V/cell). My model in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p2_power/model.py uses a generic NMC/Si 21700 OCV curve (not a Molicel curve), cell IR 12.8 mOhm (Molicel page) / 18 mOhm DC, and 39 mOhm of path resistance. Usable energy is 55-57 Wh at a 13.6 V cut and 60-62 Wh at a 13.2 V cut, at 25 C with new cells. The per-mode figures are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p2_power/modes.py.
    - **Fix:** Plan with 58 Wh (warm, new cells, 13.2 V cut) and 50 Wh (0 C or after about 300 cycles). Publish the single per-mode table from budget_tables in STACK.md. Measure every mode with the INA228 at first power-up and replace the model rows.
    - **Fix cost:** $0
    - **Sources:**
      - https://www.molicel.com/inr-21700-p50b/
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  2.
    - **Area:** Battery cutoffs
    - **Components:**
      - labpowerd
      - D36V50F12 EN
      - Pololu #2813
      - BMS
    - **Problem:** Four cutoff sets conflict: 13.6 V Linux (power, radio_lab); 13.2 V (lab_ui_hf); a 12.8 V hardware cut; and the register's 'hardware cut at 13.4 V or above with the D36V50F12'. The register reasons that the buck drops out below 13.3 V. That dropout does not harm the Q6A, because J21 accepts 4.5-16 V. A 13.4-13.6 V cut throws away about 5 Wh (7%) for no benefit. Separately, the EN-divider-only hardware cut leaves the LAB 5 V buck and the RP2040 powered after the cut, so the pack keeps draining at about 0.5-25 mA.
    - **Severity:** major
    - **Evidence:** register #66 and #60; power.json verify known_problems ('Linux 13.6 V, EN 12.8 V'); lab_ui_hf ui_system.process_supervision ('8% or 13.2 V loaded for 10 s, above the ~12.8 V hardware cutoff'); Pololu 4095 page fetched today (EN sleep below 1.2 V, wake above 1.35 V; sleep current 10-20 uA per volt; PG low at 10% below nominal); compute register #15 (J21 4.5-16 V).
    - **Fix:** Use one table (see budget_tables): economy at 20% SoC; Linux poweroff at 3% SoC or V_N <= 13.2 V loaded for 10 s; hardware cut at V_N <= 12.8 V by a micropower supervisor on the always-on rail that drives the #2813 OFF input, with the D36V50F12 EN divider as a backstop; BMS at 2.5-2.8 V/cell as the last resort. Re-enable only by the button, and only above 13.6 V at rest. labd blocks noise-source NF measurements below V_N 13.6 V, because the 12 V rail only regulates above about 13.3 V.
    - **Fix cost:** About $2-4 (supervisor plus divider)
    - **Sources:**
      - https://www.pololu.com/product/4095
  3.
    - **Area:** Display power
    - **Components:**
      - Wisecoco 7in FHD 2000+ nit
      - SYS12 display branch
    - **Problem:** The display is under-budgeted. small_antenna_stack uses 3.6-4.8 W at 60% and 6-8 W at full, and the acceptance test asks for 9 W or less at full white. Comparable products draw more: the 4D 1000-nit panel is 6.5 W (12 V, 540 mA), the BenQ PVS7 2000-nit 7in is 10 W typical and 18 W maximum, and the LUT7 is 20 W. Scaling from these gives about 10-14 W at 100% for a 2000-nit FHD panel (my model). As written, the acceptance test would reject a normal panel, and the runtime and heat budgets are low. The board's input voltage is still unknown. If it is 5 V only, it needs about 2.6 A at full brightness, which the LAB 5 V and Q6A rails cannot supply.
    - **Severity:** major
    - **Evidence:** small_antenna_stack stack.display_power_mechanical_impact; display_market final.acceptance_tests; mechanical_thermal verify issue 2 (BenQ PVS7, IMA 16 W); power.json verify (LUT7 20 W); the Youritech ET070FH01-HT page (fetched today) gives no backlight power, -20 to 70 C operating.
    - **Fix:** Budget 3 W at 25%, 6 W at 50% and 13 W at 100% until measured. Change the acceptance to: 9 W or less at 50%, 14 W or less at 100%, and at least 1800 nits at 100%. Feed the panel from SYS12 through an LC filter and a 1.5 A eFuse or PTC. If the vendor confirms a 5 V-only board, add a dedicated D36V28F5 #2 (5 V/3.2 A); never use LAB 5 V or a Q6A USB port. Use DC/analog dimming. Get the input range in writing before buying.
    - **Fix cost:** $0, or $23.95 if the board is 5 V only
    - **Sources:**
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_0.pdf
      - https://www.benq.eu/en-eu/monitor/creative-pro/pvs7/spec.html
  4.
    - **Area:** LNB rail
    - **Components:**
      - Othernet Bullseye LNB
      - LNB regulator
      - labd
    - **Problem:** The files hold four incompatible LNB feeds. radio_lab BOM has a 'TPS65233-class 13.0-13.4 V regulator with a 250-300 mA limit'; that class is an LNB IC with 13.4/18.2 V outputs and 22 kHz functions the device does not need. rf_frontend and the lab_ui_hf menu and arbiter have a 13.4/18.2 V switchable boost ('LNB 13.4 V (V) / 18.2 V (H), hold-to-confirm'). small_antenna_stack has an MT3608/XL6009 boost behind a #2813. power.json feeds it from the 12 V rail. On 4S the switched pack node stays at 13.2-16.4 V over the whole usable window, so a switching boost is not needed at all.
    - **Severity:** major
    - **Evidence:** radio_lab final.lab_bom ('LNB feed fix'), lab_ui_hf final.ui_system.menu_tree[15] and resource_arbitration, small_antenna_stack final.revised_stack, register #102-104. LT3045 (datasheet via search): 1.8-20 V in, 0-15 V out, 500 mA, 260 mV typical dropout, programmable current limit, can be paralleled.
    - **Fix:** LNB rail = an LT3045 LDO set to 13.2 V, fed from the switched pack node through an LC filter. Use the LT3045-EP, or 2x LT3045 in parallel, bonded to the mid-plate; worst-case dissipation is (16.4-13.2) x 0.3 A = 0.96 W. EN comes from labd and is low at boot, which gives a true 0 V output with no boost leakage. ILIM is the single current limit, set to 1.5-2x the measured LNB current (provisionally 0.45 A for a draw of 0.3 A or less). The LDO holds 13.2 V down to about 13.55 V of pack, and still gives about 12.6-12.8 V at the LNB at the 13.2 V cutoff. That is above the 11.5 V minimum and below the roughly 14 V horizontal threshold, so the LNB can never switch to horizontal. Delete every 18.2 V entry, the TPS65233 line and the boost lines. Acceptance: 0 V when off; 13.2 V +/-0.2 V at the F connector under load with pack at 13.8 V or more.
    - **Fix cost:** About $5-15 (unverified module or board price)
    - **Sources:**
      - https://www.radiolocman.com/datasheet/pdf.html?di=169717
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  5.
    - **Area:** LNA bias rail
    - **Components:**
      - LT3045 LNA LDO
      - TPS2553 injectors
      - SAWbird+ NOAA/GOES/iO/H1
      - LAB 5 V
    - **Problem:** No file says what feeds the 'LT3045-class 5 V LNA LDO'. Fed from SYS12, it would dissipate (12-5) x 0.35 A = 2.45 W for two SAWbirds, above what an MSOP/DFN LDO can handle at a 45-50 C internal temperature. A 5 V output cannot come from the 5 V LAB rail. The TPS2553 (2.5-6.5 V) cannot sit on 12 V either. The LAB 5 V budget and its 2 A fuse also leave out the LNA current.
    - **Severity:** major
    - **Evidence:** power.json research.integration_notes ('LNAs: feed them from an LT3045-class LDO (5 V) behind an LC filter') with no source named; register #61 ('LNAs: LT3045-class LDO'); radio_lab final.lab_bom D36V28F5 (2 A fuse, budget without LNAs); my dissipation calculation.
    - **Fix:** LNA rail: LAB 5 V -> LC -> LT3045 set to 4.5 V (dissipation 0.25 W at 0.5 A) -> one TPS2553 per port at 300 mA nominal (about 240 mA minimum) -> injector. The SAWbird+ accepts 3.3-5.5 V. Raise the LAB 5 V fuse to 3 A and keep the LAB port at 1 A or less. labd enforces the LAB budget: LAB port + LNA current <= 1.5 A.
    - **Fix cost:** About $5-10
    - **Sources:**
      - https://www.nooelec.com/store/sawbird-plus-goes.html
  6.
    - **Area:** Back-feed (USB and display)
    - **Components:**
      - Adafruit CH334F hub
      - LAB 5 V
      - Q6A FE1.1s port P3 / WS4612
      - HF+
      - Wisecoco board
      - Q6A USB-C
    - **Problem:** On the Adafruit CH334F breakout, the upstream 5V pin is the board's power input, and each downstream port's 5V pin is an output. If LAB 5 V powers the hub while the Q6A port's VBUS is also wired to it, two 5 V sources run in parallel. LAB 5 V then back-feeds the Q6A's VCC_5V_PERI through the WS4612, and phantom-powers the Q6A when it is off. The same risk exists on the display board through its USB VBUS and HDMI pin 18 (+5 V). The register's acceptance test checks only USB VBUS. On the Q6A USB-C, a 'removable plug and label' still allows a charger to be connected while J21 is live, which back-feeds through Q5.
    - **Severity:** major
    - **Evidence:** Adafruit CH334F learn guide (search snippet: the upstream 5V pin is listed as a power input, the downstream 5V pins as outputs); register #62 and #129 (CH334F tree powered from LAB 5 V); display_market acceptance_tests (USB VBUS 0 V only); power.json verify issue 11 (VBUS from any source turns on Q5).
    - **Fix:** Wire the CH334F upstream through its pin header. Take D+, D- and GND from the Q6A port, and connect its 5V pin to LAB 5 V only. Leave the Q6A port's VBUS unconnected and never use the hub's USB-C. Apply the same rule to the display board: no VBUS link, and HDMI pin 18 cut or diode-blocked. The case has no opening for the Q6A USB-C, so bench power comes only through the IP2368 port. Acceptance with the FNB58: zero reverse current on every Q6A port, and 0 V on Q6A VBUS and HDMI +5 V with the Q6A off and LAB 5 V on.
    - **Fix cost:** $0 (wiring and trace cuts)
    - **Sources:**
      - https://learn.adafruit.com/adafruit-ch334f-mini-4-port-usb-hub-breakout?view=all
  7.
    - **Area:** Q6A 5 V rail (Lime-conditional)
    - **Components:**
      - SGM40666AS/SY7120 VCC_5V_PERI
      - LimeSDR Micro
      - Samsung T7
      - RTL-A/RTL-B
    - **Problem:** With the Lime and T7 kept, VCC_5V_PERI at the allowances is about 20.6 W: Lime 8.25 W, T7 7.5 W (storage budget), 2 V4L at 2.6 W, tee LNAs 0.8 W, fan, GNSS, touch and Wi-Fi. The rail's limit is about 17 W (SGM40666A 4.5 A). That overload would hit during exactly the 160 Msps burst recordings. Typical draw is about 11.8 W, which is fine.
    - **Severity:** major
    - **Evidence:** register #62 (about 17 W); storage.json ('a power budget of about 7.5 W' for the SSD); register #21 and #86 (Lime about 4 W typical, 8.25 W allowance); modes.py VCC_5V_PERI table.
    - **Fix:** Only if the Lime is kept: power the T7 from LAB 5 V through a VBUS-split USB 3 lead (data from the blue port, VBUS from a TPS2553 at 1.5 A). Then upgrade LAB 5 V to a Pololu D36V50F5 (price unverified), or switch the LAB port off during Lime recording. Accept only if the J21 input stays at 20 W or less in a 60-minute 56 Msps plus T7 write soak. Without the Lime, nothing changes (4.9 W of 17 W).
    - **Fix cost:** $5-10 lead and switch; about $35-40 if the D36V50F5 is needed (unverified)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/storage.json
  8.
    - **Area:** Regulator spurs (HF/LF)
    - **Components:**
      - Pololu D36V50F12
      - Pololu D36V28F5
      - IP2368
      - Airspy HF+
      - Boni-Whip
    - **Problem:** Per Pololu, the D36V50F12 switches at about 500 kHz under heavy load, and at light load drops into a power-save mode that only stays above 20 kHz. Its fundamental can therefore land near NAVTEX 490 and 518 kHz, its harmonic comb covers MW and HF, and in power-save mode it can wander through the 40-162 kHz time-signal band (DCF77, MSF/WWVB, JJY, TDF). All of these are in-scope HF+ targets. The D36V28F5 (LAB 5 V) behaves similarly and feeds the HF+ directly. The IP2368's 250 kHz has its 2nd harmonic at 500 kHz while charging. Forced PWM would not fix a fixed fundamental near NAVTEX; only the frequency choice does. No file plans an A/B test below 500 kHz.
    - **Severity:** major
    - **Evidence:** Pololu 4095 page fetched today ('about 500 kHz under heavy loads', 'ultrasonic ... above 20 kHz'); power.json verify known_problems (EMI list); radio_lab final.lab_bom (D36V28F5 power-save); lab_ui_hf hf_receiver.setup acceptance test (0.1-20 MHz only).
    - **Fix:** Add an LF/HF A/B gate: the HF+ terminated and then on the Boni-Whip at 2 m, at 40, 60, 77.5, 162, 490 and 518 kHz plus 0.5-30 MHz, with the SYS12 and LAB loads stepped from 0.3 to 3 A on an electronic load and the charger on and off. If any regulator line falls within +/-1 kHz of a target, or within the passband of an in-scope decode, replace that regulator with a forced-PWM buck whose RT/SYNC-set frequency comes from a harmonic scan (part chosen in P5). Put an LC filter plus Mix-31 ferrite on the HF+ VBUS. The HF Quiet profile forbids charging.
    - **Fix cost:** $0 for the test; about $10-30 per regulator swap if it fails (estimate)
    - **Sources:**
      - https://www.pololu.com/product/4095
  9.
    - **Area:** Thermal (cells, panel, SoC)
    - **Components:**
      - P50B pack
      - IP2368
      - Wisecoco panel
      - Q6A
      - T7
      - UFS
    - **Problem:** Model results:
  - Internal heat: 8-36 W without the Lime (about 17 W on a LEO pass) and 30-53 W with it, plus about 7 W of face solar reaching the internal air.
  - Air temperature with two fan paths (about 5.4 m3/h): mean rise 6-16 K, outlet rise up to 25 K (35 K at Lime peak). At 35 C ambient, cells downstream of the board sit at 45-55 C. The charger's 45 C NTC limit then blocks charging, and the cells age faster.
  - Charging adds about 2.6 W of IP2368 loss inside the case.
  - Panel: at 35 C ambient in full sun at 100% backlight it reaches about 71 C, above its 70 C rating. The derating ladder will hold it near 50% (about 1000 nits).
  - Q6A: about 85 C typical and 90-100 C at peak in 35 C sun, so it throttles.
  - T7 (Lime only): sits near its 60 C limit in the hot air.
    - **Severity:** major
    - **Evidence:** thermal.py (/tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p2_power/thermal.py; model, case 210x135x52 mm, h about 10 W/m2K); register #16 and #17 (throttling at 90-91 C, solar 13.5-17 W, UFS about 60 C); Youritech ET070FH01-HT page (fetched today: operating -20 to 70 C); power.json IP2368 NTC thresholds (0/45 C); storage.json (T7 Shield 0-60 C).
    - **Fix:** Put the pack in a separate grip compartment on the INTAKE side, behind 3 mm closed-cell foam and reflective film, with the NTC on the middle cell. Keep the IP2368 pad-mounted to the case at least 10 mm from the cells, with a 70 C KSD9700. Mount the T7 (Lime only) at the intake or outside the case. Allow NPU T2 training only when the SoC is below 75 C and the battery above 25%, or on a charger. State plainly that 2000 nits in hot noon sun is a burst mode, and that sustained brightness falls to about 1000 nits by physics. Keep the hood and IR film. Run the 45-minute noon soak with every mode in this table.
    - **Fix cost:** About $5 (foam, film, thermal fuse)
    - **Sources:**
      - https://www.youritech.com/products/7-inch-tft-lcd-display-1920x1080-mipi-2000nits-high-brightness-lcd-display-with-in-cell-touch-for-healthcare-medical-display-solution.html
  10.
    - **Area:** 12 V regulator capacity (Lime peak)
    - **Components:**
      - D36V50F12
      - J21 wiring
    - **Problem:** At the Lime peak, the D36V50F12 output reaches about 3.6-4.1 A at 12 V: J21 about 2.5 A, display about 1.1 A, AUX up to 0.42 A. Pololu rates it at 4.5 A typical at 36 V in, limited by heat dissipation, and its stock is 'Rationed'. In a sealed 45-50 C case this is marginal. Without the Lime the peak is about 2.9 A, which is fine.
    - **Severity:** minor
    - **Evidence:** Pololu 4095 page fetched today (4.5 A typical at 36 V in, 2.3-6.5 A depending on conditions, 'Rationed', $39.95 / $36.75 at 5+); modes.py peak modes.
    - **Fix:** Bond the D36V50F12 to the mid-plate and run the sealed-case test at 14.0 and 16.4 V input, 3.5 A, for 60 min (output stays within 4%, no thermal cut). Buy 2 now (one spare) because stock is rationed. If the Lime is kept and the test fails, AUX must be off during Lime peaks.
    - **Fix cost:** $36.75-39.95 for the spare
    - **Sources:**
      - https://www.pololu.com/product/4095
  11.
    - **Area:** TVS values
    - **Components:**
      - SMBJ14A at J21
      - pack-node TVS
    - **Problem:** SMBJ14A at J21: its breakdown voltage (VBR) can be as high as 17.2 V (datasheet maximum), above the 16 V rating of C611/C612 and the SY81012's 16 V operating limit. If the buck fails short (16.4 V), it may not clamp hard below 16 V. The pack node N, where the 20 V-max LT3045s sit, has no TVS specified.
    - **Severity:** minor
    - **Evidence:** register #15 (C611/C612 22 uF/16 V, SY81012 2.7-16 V, 18 V absolute maximum); standard SMBJ series ratings (SMBJ14A VBR 15.6-17.2 V; SMBJ13A 14.4-15.9 V; SMBJ17A 18.9-20.9 V), from catalogue values, not re-fetched.
    - **Fix:** Use an SMBJ13A at J21 (VRWM 13 V, above the 12.48 V maximum regulated output) and an SMBJ17A at node N (VRWM 17 V, above 16.8 V). Do the monthly 4.20 V balance charge with the master switch OFF, so the LDO inputs never see more than 16.4 V.
    - **Fix cost:** About $0.5
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_sch/q6a_sch.txt
  12.
    - **Area:** AUX 12 V switch
    - **Components:**
      - AO3401A
      - AUX 12 V
    - **Problem:** radio_lab says pulling the AO3401A gate to ground 'sits exactly at the ±12 V limit'. The D36V50F12 output can reach 12.48 V (+4%), which puts V_GS at -12.48 V, beyond the absolute maximum. The clamp is therefore mandatory.
    - **Severity:** minor
    - **Evidence:** radio_lab final.lab_bom AUX switch and refuted_claims; Pololu 4095 (12 V +/-4%).
    - **Fix:** Use a P-FET rated ±20 V V_GS (for example the AO3407A; verify the datasheet), still with the 10k/10k gate divider (about -6 V), a 2N7002 driver and the 0.75 A-hold PTC, default OFF.
    - **Fix cost:** About $0.2
    - **Sources:**
      - https://www.pololu.com/product/4095
  13.
    - **Area:** Bias current limits
    - **Components:**
      - TPS2553
      - PTC option
      - SAWbird+
      - Flamingo+ FM
    - **Problem:** 'A PTC with a hold current of 250 mA or more at the maximum internal temperature' is easy to misread. A PTC sold as 250 mA hold is rated at 25 C and derates to about 180-190 mA at 60 C, below the SAWbird+ 180 mA. A TPS2553 set to 250 mA nominal has only about 20-40 mA margin at its low tolerance edge. If the Flamingo+ FM (250 mA DC pass) sits between the injector and the LNA, a 300 mA fault limit exceeds its DC rating.
    - **Severity:** minor
    - **Evidence:** register #97 and #100 (SAWbird+ 170-180 mA, TPS2553 250-300 mA); register #85 and conflict 10 (Flamingo+ FM, 250 mA DC pass); typical PTC thermal derating (catalogue behaviour, not re-fetched).
    - **Fix:** Set the TPS2553 to 300 mA nominal on every SAWbird+ port. If a PTC is used instead, choose one with a hold current of 0.35-0.4 A at 25 C. Place the Flamingo+ FM on the SDR side of the injector, so no bias current flows through it.
    - **Fix cost:** $0
    - **Sources:**
      - https://www.nooelec.com/store/sawbird-plus-goes.html
  14.
    - **Area:** MCU and always-on rail
    - **Components:**
      - HMI RP2040
      - INA228
      - always-on LDO
    - **Problem:** register #66 puts the RP2040 hard cut and the J21 pin 3 pulse on an 'always-on rail', but the USB map powers the HMI RP2040 from CH334F H1, which is LAB 5 V and switched. An always-on RP2040 would drain about 0.1-0.4 W in 'off' unless it sleeps in dormant mode. When the RP2040 runs while the Q6A is off, its UART7 TX can also back-feed the Q6A's IO.
    - **Severity:** minor
    - **Evidence:** register #66 and #129; lab_ui_hf ui_system.architecture (UART7 behind UM3304).
    - **Fix:** Put the RP2040 on LAB 5 V. It powers up with the #2813, sends the J21 pin 3 pulse (0.5-1.5 s) only when the 40-pin 3.3 V is absent, opens the #2813 a few seconds after poweroff, and tri-states TX while the 40-pin 3.3 V is low. The always-on rail is a 30 V-rated LDO with Iq of a few uA (for example TI TPS709; verify) that powers only the INA228 and the 12.8 V supervisor. Off drain is about 14 mW, so a full pack lasts about 170 days.
    - **Fix cost:** About $1-2
    - **Sources:**
      - https://www.adafruit.com/product/5832
  15.
    - **Area:** Gauge integrity
    - **Components:**
      - Pinecil V2
      - ISDT 608PD
      - INA228
    - **Problem:** The Pinecil can run from 'the pack's XT30 service lead' at about 2.65 A (43 W at 16.4 V), and the monthly 4.20 V ISDT balance charge also goes through the XT30. If that lead sits upstream of the INA228 shunt, the coulomb count drifts without the gauge knowing.
    - **Severity:** minor
    - **Evidence:** radio_lab final.lab_bom (Pinecil lead, ISDT); register #63 and #65.
    - **Fix:** Run the Pinecil from the PD bank (about 64 W at 20 V). If the pack must be used, take it from a fused 5 A service port on node N, downstream of the shunt, with IronOS set to 4S and 3.3 V/cell. labpowerd re-syncs to 100% at boot when node N rests at 16.3 V or more, and recalibrates capacity at each full IP2368 charge.
    - **Fix cost:** $0
    - **Sources:**
      - https://ralim.github.io/IronOS/Settings/
  16.
    - **Area:** Charger source qualification
    - **Components:**
      - IP2368 BZ
      - PD sources
    - **Problem:** At 3 A in battery-current mode the IP2368 draws about 48-52 W from the source. A 45 W PD source may be overloaded if the IP2368 does not honour the source's PDO current; this is unverified. 'Use while charging' at an 18-24 W load still leaves only about 25 W for the cells, so a full charge takes about 2.5 h instead of 1.7-1.9 h.
    - **Severity:** minor
    - **Evidence:** power.json verify (ISET 15k = 3 A; input-power mode 4 W per kOhm; source of 45-65 W or more for use while charging); my calculation (4.19 Ah to refill, 1.4 h CC at 3 A plus CV).
    - **Fix:** Qualify each PD source with the FNB58: at a 3 A charge, the source current must stay within its PDO rating. If 45 W sources must be used, switch to input-power mode at about 45 W (RISET about 11.3k by the 4 W/kOhm rule; verify on the bench). The UI shows 'charging paused (cell hot)' when the NTC blocks charging.
    - **Fix cost:** $0
    - **Sources:**
      - https://datasheet.lcsc.com/datasheet/pdf/752f0c4a0b5b0a79a7f68752c4eac200.pdf?productCode=C5203723
  17.
    - **Area:** Stale power values in study files
    - **Components:**
      - radio_lab
      - lab_ui_hf
      - power.json
      - npu_training
    - **Problem:** Superseded values are still in the files:
  - radio_lab integ: AUX '0.5 A PTC'; 'LNB injector in the sled runs at 12 V'; 'AUX from the LNB 12 V branch'; Boni-Whip '10.0 V LDO' (item 49, P20).
  - lab_ui_hf: 'LDO dropout under 1.2 V at the 13.2 V shutdown threshold'; '5 V boost good for about 7 A'; HF+ on Q6A VBUS with a GPIO VBUS-cut.
  - power.json: 'a 7-24 V display straight from the pack'.
  - npu_training: 'INA228 on the 12 V J21 rail'.
    - **Severity:** minor
    - **Evidence:** radio_lab integ.power_budget and conflicts_and_fixes; lab_ui_hf final.stack_changes; power.json verify final_recommendation.why; npu_training final.hardware_needs.
    - **Fix:** STACK.md uses only the rail table in budget_tables. Add an errata block that lists these lines as superseded.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  18.
    - **Area:** Unpublished currents
    - **Components:**
      - Airspy HF+ Discovery
      - Boni-Whip
      - Bullseye LNB
      - ZFL-500 noise source
    - **Problem:** There is still no published current for the HF+ (I found none; the rtl-sdr.com comparison article keeps its numbers in a video), the Boni-Whip, the Bullseye or the noise source. The rail limits are therefore provisional.
    - **Severity:** minor
    - **Evidence:** WebSearch and WebFetch today (rtl-sdr.com USB power article without figures); register open_questions.
    - **Fix:** Provisional budgets: HF+ 0.3 A at 5 V, Boni-Whip 0.1 A at 12.5 V, LNB 0.3 A at 13.2 V, noise source 0.15 A at 12 V. Measure each with the FNB58 or DMM on arrival, then set the LT3045 ILIM and TPS2553 values to 1.5-2x the measured current.
    - **Fix cost:** $0
    - **Sources:**
      - https://www.rtl-sdr.com/measuring-the-usb-power-consumption-of-various-software-defined-radios/
  19.
    - **Area:** Cell sourcing (world price)
    - **Components:**
      - Molicel P50B
    - **Problem:** The files give only UAH prices for the cells.
    - **Severity:** minor
    - **Evidence:** register #59; search result today: nkon.nl EUR 6.75 incl. VAT (EUR 5.58 ex VAT), dated 31-07-2026. The page itself returned 403, so this is unverified. Simpower NZ lists NZ$18.45.
    - **Fix:** Budget 5 cells (4 plus 1 spare) at about EUR 6.75 each (about EUR 34) from NKON or an equivalent authorised EU/US seller. Test capacity and IR before welding.
    - **Fix cost:** About EUR 34
    - **Sources:**
      - https://www.nkon.nl/default/molicel-inr21700-p50b-5000mah-50a.html
      - https://www.molicel.com/inr-21700-p50b/
- **Proposed decisions:**
  1.
    - **Question:** C1 LimeSDR Micro keep or drop
    - **Decision:** Gated optional. Keep the cancellable pre-order and decide on 31 Jan 2027 or on delivery. Size the power architecture so the Lime plugs in without a redesign: same pack, same 7.5 A fuse and D36V50F12, plus three Lime-only changes. (1) The T7 takes VBUS from LAB 5 V. (2) J21 is wired from the bottom pads with a 20 AWG twisted pair. (3) The 10 W conduction path to the plate.
    - **Reason:** No core function depends on it. Its power cost is large: typical 31 W against 18.5 W, peak 64 W, and it would push VCC_5V_PERI over its limit if the T7 also ran from the Q6A.
    - **Consequences:** With the Lime: about 1.9 h typical, 0.9 h at peak, and 30-53 W of internal heat. Without it: 2.4-3.1 h typical.
    - **Alternatives rejected:** Lime as core: it would push VCC_5V_PERI past 17 W and runtime under 2 h. Dropping it now loses S-band and wideband NPU data before any test.
  2.
    - **Question:** C2 Q6A RAM tier
    - **Decision:** Buy the 12 GB board now, as the register says.
    - **Reason:** RAM cannot be upgraded, and the Lime and training option stays open. Power impact is negligible.
    - **Consequences:** Training bursts add 3-6 W for 1-11 min, gated by temperature and SoC.
    - **Alternatives rejected:** 8 GB, because 9.3 GiB of planned use does not fit.
  3.
    - **Question:** C3 Pack 3S vs 4S
    - **Decision:** 4S1P Molicel P50B (72 Wh nominal), charged daily to 4.10 V/cell (16.4 V). Plan with 58 Wh usable when warm and 50 Wh in the cold or when aged. Buy 5 cells, about EUR 6.75 each at NKON (unverified).
    - **Reason:** The LNB at 13.2 V, the Boni-Whip at 12.5 V, AUX 12 V and the noise source need 12 V or more. On 4S these become quiet LDOs from the pack; on 3S each would need its own boost. 4S also halves the current.
    - **Consequences:** Adds about $45 and 75 g over 3S. Every runtime is restated from the per-mode table.
    - **Alternatives rejected:** 3S direct into J21: it needs 3-4 boosts and gives about 46 Wh. 4.20 V daily charge: about +8% energy, but faster aging.
  4.
    - **Question:** C4 12 V regulator
    - **Decision:** Pololu D36V50F12 ($39.95, buy 2 because stock is 'Rationed') feeding SYS12. It is bonded to the plate, with an EN divider at 12.8 V as backstop, then a pi-filter and an SMBJ13A plus 220 uF/25 V at J21. Accept its dropout region, since the Q6A accepts 4.5-16 V. Gate: the sealed-case current test and the LF/HF/VHF A/B. If either fails, replace it with a forced-PWM buck whose frequency is set by RT/SYNC (P5).
    - **Reason:** It is the only verified, branded 12 V module of 4.5 A or more in hand. No forced-PWM 12 V buck-boost of 5 A or more was found from a reputable module vendor; Pololu's S18V20F12 is a 2 A SEPIC. Its load never falls below about 0.35 A while the Q6A runs, which favours PWM. Its 500 kHz needs the NAVTEX check.
    - **Consequences:** Below about 13.3 V of pack, SYS12 sags towards about 11.5 V. That is harmless for the Q6A and the display. labd blocks noise-source NF measurements below 13.6 V.
    - **Alternatives rejected:** 9 V buck: it would need a second 12 V converter for the display and AUX. LTC3780 module: reported very noisy. A buck-boost of unknown origin: spurs unverified.
  5.
    - **Question:** C5 USB port map
    - **Decision:** Use the register's Lime-agnostic map. Power rules on top of it:
  - RTL-A, RTL-B, touch, fan and GNSS take power from the Q6A (4.9 W of 17 W).
  - The CH334F tree, HMI RP2040, IMU puck, HF+, LAB port and LNA rail run from LAB 5 V. Q6A VBUS is never tied to LAB 5 V; the hub is wired through its upstream pin header with the 5V pin on LAB 5 V only.
  - With the Lime, the T7 takes VBUS from LAB 5 V.
    - **Reason:** It keeps the Q6A's 17 W rail at 30% or less without the Lime and at 70% or less with it, and removes the back-feed path.
    - **Consequences:** The LAB 5 V budget is 2.4 A at most with a 3 A fuse. With the Lime and T7, upgrade to the D36V50F5 or switch the LAB port off during recording.
    - **Alternatives rejected:** HF+ on Q6A VBUS (lab_ui_hf), and a hub powered both ways.
  6.
    - **Question:** C6 40-pin and bus map
    - **Decision:** Use the register's map. Power-related lines:
  - INA228 on I2C0 (0x40), read through user-space i2c-dev.
  - Q6A fan on/off at 60/50 C through an AO3400 on header pin 33 used as a plain GPIO, not 1 kHz pwm-gpio.
  - The display-channel blower is switched by the HMI RP2040 from the panel NTC.
  - The 12.8 V supervisor and the #2813 OFF line stay off the 40-pin entirely.
  - IMU over the RP2040 UART relay.
    - **Reason:** This avoids 1 kHz PWM ticking, frees a pin, and keeps the hardware cut independent of Linux.
    - **Consequences:** The RP2040 firmware owns the blower and backlight derating.
    - **Alternatives rejected:** GPIO56 with the PoE-HAT overlay (1 kHz PWM and the overlay typo); IMU over USB-CDC, which costs a hub port.
  7.
    - **Question:** C7 Hardware ownership
    - **Decision:** labd is the only owner of the rail enable lines: LNB, Boni-Whip, LNA ports, AUX, LAB port, T7 VBUS and the noise source. Their boot defaults are OFF. labpowerd stays separate and minimal: it owns the INA228, KEY_POWER, the cutoff table and shed commands, and labd must obey them.
    - **Reason:** There must be one lock authority. The power safety logic must survive a labd crash.
    - **Consequences:** labd restarts reconcile the rail state from /run.
    - **Alternatives rejected:** rflab or rflabd as a second GPIO owner.
  8.
    - **Question:** C8 LNB supply
    - **Decision:** LT3045 LDO at 13.2 V from the switched pack node (EP part or 2 in parallel, bonded to the plate). EN from labd, default low, giving a true 0 V output. The single current limit is the LT3045 ILIM at 1.5-2x the measured current (provisionally 0.45 A). No 18 V.
    - **Reason:** On 4S the pack stays at 13.2 V or more over the whole usable window, so no switcher is needed. Below 13.55 V of pack the LNB still gets 12.6-12.8 V and stays vertical. Worst-case dissipation is 0.96 W.
    - **Consequences:** The TPS65233, the 13.4/18.2 V menu and arbiter entries, the boost lines, and power.json's '12 V rail suits LNB' are deleted.
    - **Alternatives rejected:** TPS65233-class 13.4/18.2 V, MT3608/XL6009 boost, the 12 V rail through the tee (10.6-11.4 V).
  9.
    - **Question:** C9 LNA bias rule
    - **Decision:** LAB 5 V -> LT3045 at 4.5 V -> a TPS2553 at 300 mA nominal for every SAWbird+ (FAULT to the MCP23017). The V4L tee powers only LNAs of 80 mA or less. If a PTC is used, its hold current is 0.35-0.4 A at 25 C.
    - **Reason:** SAWbird+ draws 170-180 mA. 300 mA leaves margin at the TPS2553's low tolerance edge, and a 250 mA PTC derates below the load when hot.
    - **Consequences:** The LAB 5 V budget gains up to 0.5 A, so its fuse goes from 2 A to 3 A.
    - **Alternatives rejected:** A 100-160 mA PTC, GOES+ on the V4L tee, and an LT3045 at 5 V from 12 V (2.45 W).
  10.
    - **Question:** C10 FM filter
    - **Decision:** Nooelec Flamingo+ FM, permanently in the 137/145 MHz path, on the SDR side of the injector.
    - **Reason:** This keeps bias current out of its 250 mA DC path.
    - **Consequences:** None.
    - **Alternatives rejected:** A second filter type.
  11.
    - **Question:** C11 librtlsdr
    - **Decision:** Use the register's .so.2 rebuild of noble 2.0.1 (0204c9c + 65f0658).
    - **Reason:** Verified recipe. No power impact.
    - **Consequences:** Test on the Q6A.
    - **Alternatives rejected:** 2.0.3 (.so.0) and the purge-and-fork recipe.
  12.
    - **Question:** C12 Display field-mode pixel clock
    - **Decision:** About 127.9 MHz (51.7 Hz), or 164.4-168.4 MHz if the panel accepts it, as the register says. Add from the power side: DC/analog backlight dimming, the backlight boost frequency measured in the A/B, and the display fed from SYS12 through an LC filter and a 1.5 A eFuse.
    - **Reason:** 128.70 MHz hits Inmarsat-C. Backlight PWM and boost noise are separate sources.
    - **Consequences:** The A/B includes 40-518 kHz.
    - **Alternatives rejected:** 128.70 MHz, 148.5 MHz.
  13.
    - **Question:** C13 PPS on the held kernel
    - **Decision:** Out-of-tree pps-gpio on 6.18.2-4, as the register says.
    - **Reason:** CONFIG_PPS=y. No power impact.
    - **Consequences:** None for power.
    - **Alternatives rejected:** Route B on 7.0.11.
  14.
    - **Question:** C14 INA228
    - **Decision:** Adafruit #5832 with the 15 mOhm shunt in the pack lead (ADCRANGE 0, +/-10.9 A). VS comes from a 30 V-rated LDO with Iq of a few uA. Breakout pull-ups are removed, the device is read over user-space i2c-dev, and no driver is bound. There is no second INA: NPU power is measured as the delta at the pack with A/B toggling.
    - **Reason:** It counts both charge and load current. Off drain is about 10 mW. A second INA adds $15 for a number the A/B already gives.
    - **Consequences:** Fix npu_training's 'on the J21 rail'.
    - **Alternatives rejected:** ina238 hwmon binding (it blocks CHARGE access); i2c6.
  15.
    - **Question:** C15 Antenna tiers
    - **Decision:** Use the register's two-tier rule: the V-dipole is the LRPT default and the ultra-compact Yagi is the default build; strike the loops.
    - **Reason:** User rule. Power side: every active antenna is fed from a limited rail with the DC-sense interlock.
    - **Consequences:** None for power.
    - **Alternatives rejected:** The small-stack removals.
  16.
    - **Question:** C16 Policy leftovers
    - **Decision:** Strike everything on the register's list. On the power side, the noise source and every other signal source can be energised only through AUX in a BENCH profile with the antenna paths terminated.
    - **Reason:** Receive-only rule.
    - **Consequences:** AUX stays OFF in field profiles.
    - **Alternatives rejected:** None.
  17.
    - **Question:** C17 HF antenna chain
    - **Decision:** Boni-Whip on an LT3045 at 12.5 V (+/-0.25 V) from the switched pack node, with ILIM provisionally 0.2 A and EN from labd, default OFF. The LT3045 current limit makes a separate polyfuse unnecessary. The 9:1 wire is for HF only. The HF+ selector is a latching DC-capable relay (zero hold current, pulsed from LAB 5 V; part TBD). Ask the user to confirm the loop removal.
    - **Reason:** 12.5 V sits inside both published ranges (9-15 V and 12-15 V) and stays regulated down to about 12.85 V of pack, below the 13.2 V cutoff.
    - **Consequences:** Fix item 49, P20 and the setup text (10.0 V / 12.0 V).
    - **Alternatives rejected:** 10.0 V; 12.0 V at the lower edge; a boost on 3S.
  18.
    - **Question:** C18 Storage
    - **Decision:** T7 only if the Lime stays, powered from LAB 5 V and mounted at the intake or outside the case. Otherwise use UFS and a V30/A2 microSD with the retention policy.
    - **Reason:** This avoids the VCC_5V_PERI overload and keeps the T7 below its 60 C limit.
    - **Consequences:** A VBUS-split USB 3 lead is needed with the Lime.
    - **Alternatives rejected:** An internal T7 on Q6A VBUS in the hot air path.
  19.
    - **Question:** C19 CPU allocation
    - **Decision:** Use the register's plan, and add a power gate: T2 training runs only between passes, with the SoC below 75 C and the battery above 25%, or on a charger.
    - **Reason:** The thermal model shows the Q6A at 85-100 C in 35 C sun under load.
    - **Consequences:** Training may wait until shade or the bench.
    - **Alternatives rejected:** Training on the A55 cores.
  20.
    - **Question:** C20 Roadmaps
    - **Decision:** Use the register's plan, and add a Phase-0 power task in the W1-2 gates: INA228 logs per mode, the HF/LF regulator A/B, and the sealed-case D36V50F12 test.
    - **Reason:** Every runtime and thermal number is a model until then.
    - **Consequences:** Replace the model rows in STACK.md with measurements.
    - **Alternatives rejected:** Measuring after the build.
  21.
    - **Question:** C21 V4L count
    - **Decision:** Buy 3: 2 in service and 1 spare. Monitoring time-shares a receiver. A 4th V4L would add 1.3 W, which still fits (6.2 W of 17 W).
    - **Reason:** Register. Power allows either choice.
    - **Consequences:** None.
    - **Alternatives rejected:** 1 + spare.
  22.
    - **Question:** C22 Software recipes
    - **Decision:** Use the register's recipes, plus labpowerd (Python, i2c-dev, systemd Restart=always, HandlePowerKey=ignore, poweroff never halt).
    - **Reason:** Halt leaves 1.9-2.5 W draining.
    - **Consequences:** Test on the Q6A.
    - **Alternatives rejected:** HandlePowerKey=poweroff.
  23.
    - **Question:** C23 Region unknown
    - **Decision:** Build the LNB rail (LT3045, EN, F port) in every build; defer the LNB, horn and SAWbird+ iO purchases until the region is known. The power design itself does not depend on the region. The 72 Wh pack and an 88.8 Wh bank are both under the 100 Wh cabin limit.
    - **Reason:** The rail is cheap. The LNB is useless outside the QO-100 footprint.
    - **Consequences:** None for power.
    - **Alternatives rejected:** Buying everything now.
  24.
    - **Question:** C24 Costs and weights
    - **Decision:** Power subsystem at world prices: about $187-248 with one D36V50F12, plus about $37-40 for a spare. Cells 4 x about 68 g = 272 g, plus a spare. Power electronics about 50-70 g (estimate).
    - **Reason:** Itemised in budget_tables; several prices unverified.
    - **Consequences:** P5 re-prices the BMS, IP2368 BZ and LT3045 boards.
    - **Alternatives rejected:** UAH price bases.
  25.
    - **Question:** C25 P1b completion
    - **Decision:** Close it. final/report_research.json exists (576 KB, read today). Still to do: STACK.md and the summaries.md and minute-log.md errata blocks, which should include the stale power lines listed in issues.
    - **Reason:** The file exists.
    - **Consequences:** None.
    - **Alternatives rejected:** None.
  26.
    - **Question:** P1 Cutoff and threshold table
    - **Decision:** Economy at 20% SoC (or V_N below 14.0 V loaded for 30 s). No training below 25%; NPU off below 15%. Linux poweroff at 3% SoC or V_N <= 13.2 V loaded for 10 s. Hardware cut at V_N <= 12.8 V by the supervisor driving the #2813 OFF input, with the D36V50F12 EN divider as a backstop. BMS at 2.5-2.8 V/cell. Restart only by the button and only above 13.6 V at rest. Temperature: charge inhibited below 0 C and above 45 C (NTC); labpowerd shuts down above 60 C at the cell.
    - **Reason:** It recovers about 5 Wh against 13.6 V, keeps about 10% reserve, and avoids BMS lock-out and oscillation.
    - **Consequences:** The register's '13.4 V or above hardware cut' is rejected.
    - **Alternatives rejected:** Linux at 13.6 V; hardware cut at 13.4 V; BMS-only.
  27.
    - **Question:** P2 Pack fuse
    - **Decision:** One value: a 7.5 A automotive mini blade fuse at the pack, for both configurations.
    - **Reason:** Model peaks: 3.6 A without the Lime and 4.8 A with it, plus charging up to 3 A. A 5 A fuse is marginal at 60 C. Downstream, the #2813 (6 A at 55 C) never sees more than about 4.8 A.
    - **Consequences:** Spares kit: 7.5 A pack, 3 A LAB, 5 A service lead.
    - **Alternatives rejected:** 5 A.
  28.
    - **Question:** P3 Always-on rail scope
    - **Decision:** Only the INA228 and the 12.8 V supervisor are always on (about 1 mA, about 14 mW, about 170 days of standby). The HMI RP2040 runs on LAB 5 V.
    - **Reason:** Minimal standby drain. The hard-off and boot-pulse functions work from the switched side.
    - **Consequences:** The RP2040 tri-states its UART while the Q6A is off.
    - **Alternatives rejected:** RP2040 always on.
  29.
    - **Question:** P4 Display power
    - **Decision:** Budget 3, 6 and 13 W at 25, 50 and 100%. Acceptance: 9 W or less at 50%, 14 W or less at 100%, at least 1800 nits. Feed from SYS12 through an LC filter and a 1.5 A eFuse; a dedicated 5 V buck if the board is 5 V only.
    - **Reason:** 2000-nit 7in comparables draw 10-18 W.
    - **Consequences:** At 100%, runtime is about 1.2 h at peak. Sustained 2000 nits in hot sun is not achievable thermally; expect about 1000 nits by physics, which the user's wish has to accept.
    - **Alternatives rejected:** 9 W at full white as a hard limit.
  30.
    - **Question:** P5 Pack placement and thermal layout
    - **Decision:** Pack in an insulated grip compartment on the intake side. IP2368 pad-mounted at least 10 mm from the cells with a 70 C KSD9700. Two fan paths (Q6A fin stack; blower through the panel channel). T7 (Lime only) at the intake or outside.
    - **Reason:** Downstream cells would sit at 45-55 C at 35 C ambient, which blocks charging and ages the cells.
    - **Consequences:** The case layout changes before the drawing.
    - **Alternatives rejected:** A 2x2 block under the board.
  31.
    - **Question:** P6 Pinecil power source
    - **Decision:** Run the Pinecil from the PD bank at 20 V (about 64 W). From the pack only through a fused 5 A service port on node N, downstream of the shunt, with the receiver OFF and IronOS set to 4S and 3.3 V/cell.
    - **Reason:** The gauge stays correct and the pack keeps its energy for receiving.
    - **Consequences:** The XT30-to-DC5525 lead is fitted to the node-N service port.
    - **Alternatives rejected:** A raw pack XT30 tap upstream of the shunt.
- **Checks passed:**
  - J21 limits: the regulated SYS12 (11.5-12.5 V including dropout) stays inside the staff-stated 4.5-16 V, the SY81012's 2.7-16 V and the 16 V input capacitors. Raw 4S (16.4-16.8 V) is correctly excluded.
  - 12 V rather than 9 V into J21: 24 W is 2.0 A at 12 V against 2.7 A at 9 V. The TVS argument for 9 V is refuted by the schematic (D19 sits on TYPEC_IN).
  - J21 current: about 1.3 A or less without the Lime, about 2.5 A at the Lime peak (with J21 wired from the bottom pads).
  - #2813 HP (6 A at 55 C) carries the maximum switched load of about 4.8 A.
  - Pack current: 4.8 A at most against P50B 60 A continuous; IR loss about 1 W or less at peak.
  - 72 Wh pack and 88.8 Wh bank are both under the 100 Wh cabin limit.
  - IP2368: 2-5 cells, so 4S is supported; RVSET 5.1k gives 4.10 V/cell; the 10k B3380 NTC gives 0/45 C windows; charge-only BZ avoids Try.SRC pushing power into banks.
  - INA228 with the 15 mOhm shunt (ADCRANGE 0, +/-10.9 A) covers 3 A charge and 4.8 A discharge. With the shunt in the pack lead it counts both directions; the always-on draw is about 10 mW.
  - Standby drain: INA228 plus IP2368 standby (180 uA) plus BMS is about 14 mW, about 170 days from full.
  - Boni-Whip 12.5 V on an LT3045 (20 V in, 15 V maximum out, 260 mV dropout) stays regulated to about 12.85 V of pack. 12.5 V is inside both published ranges (9-15 V WiMo, 12-15 V SWLing).
  - LNB LDO keeps the Bullseye in vertical (11.5-14 V) down to the 13.2 V cutoff; the 18 V branch is not needed.
  - V4L bias tee (4.5 V, 180 mA) is limited to LNAs of 80 mA or less; the WS4612 (about 2.1 A per port) covers an RTL plus tee at about 0.35 A.
  - VCC_5V_PERI without the Lime is about 4.9 W of about 17 W (30%).
  - Lime 3.3 V comes from the on-board ETA3521 (4 A) against a 2.5 A allowance. The 3.20 V at-card acceptance leaves margin over the M.2 minimum of 3.135 V.
  - AUX 12 V load (sled about 0.2 A, noise source about 0.15 A, 28 V boost about 0.07 A, about 0.42 A total) is under a 0.75 A-hold PTC, which is still about 0.55 A at 60 C.
  - LDO thermal: Boni-Whip LDO 0.39 W, LNA LDO 0.25 W, LNB LDO 0.96 W worst case (needs plate bonding). All within LT3045 capability on a plate-bonded pad (model).
  - PSRR: LT3045 class (about 70 dB or more at 0.25-1 MHz) suppresses D36V50F12 and IP2368 input ripple on the LDO-fed rails (LNB, Boni-Whip, LNA).
  - The 3S budget option is correctly demoted: the LNB, Boni-Whip and AUX would each need a boost.
  - Q6A cooling (stepped copper block plus 30-40 mm fan, two airflow paths, Lime conduction to the plate) is the right topology. The noon soak and the 80/85 C shedding ladder remain the gate.
  - Power-key handling (labpowerd owns KEY_POWER and calls poweroff, never halt) and the RP2040 J21 pin 3 boot pulse (0.5-1.5 s, UEFI needs 400 ms or more) are consistent with each other.
- **Budget tables:**
  - RAIL MAP (one architecture; I = typical / max)
  | Rail | Source -> regulator | Setpoint | Limit / protection | Switch, default | Loads | I typ / max |
  |---|---|---|---|---|---|---|
  | PACK / node N | 4S1P P50B + 4S balancing BMS 15-20 A -> 7.5 A fuse -> INA228 15 mOhm shunt | 12.8-16.4 V (16.8 V only during a balance charge, master switch OFF) | SMBJ17A at node N | always | IP2368 BAT+, always-on LDO, #2813 | 0.6 / 4.8 A |
  | AON 3.3 V | node N -> 30 V uA-Iq LDO (TPS709 class, verify) | 3.3 V | - | always on | INA228, 12.8 V supervisor | about 1 mA |
  | SW | node N -> Pololu #2813 HP | pack voltage | 6 A at 55 C | button / RP2040 / supervisor OFF | all rails below | - |
  | SYS12 | SW -> D36V50F12 (EN divider 12.8 V) | 12.0 V +/-4%; tracks pack minus dropout below about 13.3 V | internal OCP/OTP, PG | with SW | J21, DISP12, AUX12 | 1.0 / 2.9 A without Lime; about 4 A at Lime peak |
  | J21 | SYS12 -> pi-filter + SMBJ13A + 220 uF/25 V | 11.5-12.5 V | - | - | Q6A plus everything on VCC_5V_PERI | 0.35-1.3 A without Lime; 2.5 A at Lime peak |
  | DISP12 | SYS12 -> LC filter -> eFuse | 12 V | 1.5 A | RP2040 backlight | Wisecoco board (12 V input preferred) | 0.25 / 1.1 A (model) |
  | AUX12 | SYS12 -> P-FET rated +/-20 V V_GS + 10k/10k gate divider | 12 V | 0.75 A-hold PTC | labd, OFF, BENCH only | sled, noise source, 28 V boost | 0 / 0.42 A |
  | LAB5 | SW -> D36V28F5 (D36V50F5 if Lime + T7) | 5.0 V | 3 A fuse | with SW | CH334F tree (wired through its 5V pin), HMI RP2040, IMU puck, HF+ (LC + ferrite), LAB port (TPS2553 1 A), LNA4V5, blower | 0.6 / 2.4 A |
  | LNA4V5 | LAB5 -> LT3045 | 4.5 V | TPS2553 at 300 mA per port | labd per port, OFF | SAWbird+ NOAA/GOES/iO/H1, LNA V2 | 0.17 / 0.5 A |
  | LNB13V2 | SW -> LT3045 (EP or 2 in parallel, bonded to plate) | 13.2 V | ILIM 1.5-2x measured (provisionally 0.45 A) | labd, OFF | Bullseye through the internal tee | 0.2-0.3 A (unpublished) |
  | BONI12V5 | SW -> LT3045 | 12.5 V | ILIM about 0.2 A (provisional) | labd, OFF | Boni-Whip injector | about 0.05-0.1 A (unpublished) |
  | VCC_5V_PERI | inside the Q6A: SGM40666AS -> SY7120 | 5 V | about 17 W; WS4612 about 2.1 A per port | - | RTL-A, RTL-B, fan, GNSS, touch, Wi-Fi, M.2 | 4.9 W without Lime; 11.8 W Lime typical; 20.6 W Lime worst case if the T7 stays on it |
  | M.2 3V3 | VCC_5V_PERI -> ETA3521 4 A | 3.3 V (3.20 V or more at the card) | - | - | LimeSDR (optional) | 1.2 / 2.5 A |
  - PER-MODE PACK POWER AND RUNTIME (model; usable 58 Wh warm / 50 Wh cold or aged; 4.10 V/cell charge, 13.2 V cutoff)
  | Mode | W at pack | Runtime warm | Runtime cold | Files claimed |
  |---|---|---|---|---|
  | A idle/menu, display 25% | 8.5 | 6.8 h | 5.9 h | - |
  | B LEO pass: 1 V4L + SAWbird, NPU, display 50% | 18.5 | 3.1 h | 2.7 h | 3.7-5.3 h at 11-17 W |
  | C QO-100 NB: V4L-B + LNB 13.2 V, display 50% | 20.0 | 2.9 h | 2.5 h | 13-21 W |
  | D survey: 2 V4L + HF+ + NPU, display 50% | 23.8 | 2.4 h | 2.1 h | - |
  | E HF Quiet: HF+ + Boni-Whip, display minimum | 9.0 | 6.4 h | 5.5 h | - |
  | F bench on pack: V4L, sled, noise source, 1 LAB instrument | 19.2 | 3.0 h | 2.6 h | 19-22 W, 2.8-3.4 h |
  | G peak without Lime: display 100%, all rails, LAB port 1 A | 47.6 (about 42 without the LAB port) | 1.2 h | 1.05 h | 24-32 W |
  | H Lime typical: 56 Msps + T7 + V4L, display 50% | 31.2 | 1.9 h | 1.6 h | 25-28 W, 2.2-2.6 h |
  | I Lime peak, display 100% | 63.9 | 0.9 h | 0.8 h | 45-52 W |
  | OFF (INA228 + IP2368 standby + BMS) | 0.014 | about 170 days | - | - |
  Charging from a 60 W or larger PD source: about 1.4 h CC plus 0.3-0.5 h CV (9.5% to 93%). While running mode B: about 2.5 h. The IP2368 draws 48-52 W at 3 A.
  - PROTECTION VALUES AGAINST REAL CURRENTS
  | Point | Device | Setting | Real current | Margin / verdict |
  |---|---|---|---|---|
  | Pack | blade fuse | 7.5 A | 3.6 A peak without Lime, 4.8 A with Lime, 3 A charge | OK; 5 A rejected |
  | Master | Pololu #2813 HP | 6 A at 55 C | 4.8 A or less | OK |
  | LAB5 | fuse | 3 A (was 2 A) | 2.4 A maximum including LNAs | OK; 2 A too small |
  | LAB port | TPS2553 | 1.0 A | 0.05-1.0 A | OK |
  | SAWbird+ ports | TPS2553 | 300 mA nominal (about 240 mA minimum) | 170-180 mA | OK; 250 mA nominal is too tight; a PTC needs 0.35-0.4 A hold |
  | V4L tee | internal | 180 mA | 80 mA or less allowed | OK |
  | LNB | LT3045 ILIM | 1.5-2x measured (provisionally 0.45 A) | 0.2-0.3 A (unpublished) | measure |
  | Boni-Whip | LT3045 ILIM | about 0.2 A (provisional) | unpublished | measure |
  | AUX12 | PTC | 0.75 A hold (about 0.55 A at 60 C) | 0.42 A | OK |
  | Display | eFuse | 1.5 A | 1.1 A at 100% (model) | OK |
  | Q6A USB-A | WS4612 | about 2.1 A | 0.35 A per RTL plus tee | OK |
  | VCC_5V_PERI | SGM40666AS | about 17 W | 4.9 / 11.8 / 20.6 W | OVER only for Lime + T7 at worst case: move the T7 to LAB5 |
  | J21 | SMBJ13A + 220 uF | VRWM 13 V | 12.48 V maximum | OK; SMBJ14A rejected (VBR up to 17.2 V) |
  | Node N | SMBJ17A | VRWM 17 V | 16.4 V (16.8 V with switch OFF) | OK |
  - CUTOFF TABLE (4S, labpowerd + hardware)
  | Level | Trigger | Action |
  |---|---|---|
  | Economy | SoC 20% or V_N below 14.0 V loaded for 30 s | dim to 30%, Lime parked, loggers off |
  | NPU shed | below 25% / below 15% | no training / NPU off |
  | Shutdown | SoC 3% or V_N <= 13.2 V loaded for 10 s | 30 s banner, finalise SigMF, bias/LNB/Boni/AUX off, sync, poweroff; RP2040 opens #2813 when 40-pin 3.3 V drops |
  | Hardware | V_N <= 12.8 V | supervisor -> #2813 OFF; D36V50F12 EN sleep as backstop |
  | BMS | 2.5-2.8 V/cell | last resort |
  | Restart | button only, V_N >= 13.6 V at rest | - |
  | Temperature | cell below 0 or above 45 C: no charge; cell above 60 C: shutdown; SoC above 75 C: no training; panel above 60 C: 50%, above 68 C: 20% | - |
  | Gauge resync | 16.35 V and below 0.1 A (IP2368 full), or V_N at rest >= 16.3 V at boot after an ISDT balance charge | - |
  - HEAT IN THE CASE (model: 210x135x52 mm, two fan paths about 5.4 m3/h, h about 10 W/m2K; ambient 35 C)
  | Mode | Internal W | Mean air rise shade/sun | Outlet rise | Notes |
  |---|---|---|---|---|
  | B LEO pass | 17.1 | 6.3 / 8.7 K | 10-14 K | cells downstream about 45-49 C, so no charging |
  | D survey | 22.1 | 8.1 / 10.5 K | 13-17 K | - |
  | G peak without Lime | 36.4 | 13.3 / 15.8 K | 21-25 K | SoC throttles (about 90-100 C) |
  | H Lime typical | 29.8 | 10.9 / 13.4 K | 17-21 K | T7 near its 60 C limit if inside |
  | I Lime peak | 52.7 | 19.3 / 21.7 K | 31-35 K | not sustainable |
  | Charging | +2.6 W (IP2368 loss) | - | - | keep at least 10 mm from the cells |
  Panel (backlight 11/5.5/2.8 W at 100/50/25%; 11.4 W of sun on the active area): at 25 C ambient, full sun, 100% about 61 C; at 35 C, full sun, 100% about 71 C (over the 70 C rating, so it derates to about 50%); at 35 C with the hood (50% shade) and 50% about 53 C.
  - POWER SUBSYSTEM COST (world prices)
  | Part | Qty | Price | Status |
  |---|---|---|---|
  | Molicel P50B | 5 | about EUR 6.75 each incl. VAT (NKON, 31 Jul 2026) | search snippet; the page returned 403 |
  | 4S common-port balancing BMS 15-20 A | 1 | $5-12 | unverified |
  | IP2368 BZ charge-only board | 2 | $8-17 each | unverified |
  | Pololu #2813 HP | 1 | $8.95 | verified (power.json) |
  | Pololu D36V50F12 | 1 (+1 spare) | $39.95 ($36.75 at 5+) | verified today, 'Rationed' |
  | Pololu D36V28F5 | 1 | $23.95 | radio_lab |
  | Adafruit INA228 #5832 | 1 | $14.95 | verified (power.json) |
  | LT3045 boards (LNA, LNB, Boni-Whip) | 3 | $5-10 each | unverified |
  | TPS2553 + carriers | 5 | $2-4 each | unverified |
  | uA LDO + 12.8 V supervisor | 1 | $2-4 | unverified |
  | SMBJ13A, SMBJ17A, P-FET rated +/-20 V V_GS, AO3400, fuses, NTC, XT30, 220 uF, ferrites, LC parts, foam/film, KSD9700 | - | $12-20 | estimate |
  | Total | | about $187-248 (+$37-40 for a spare D36V50F12) | |
  Optional: ISDT 608PD (reference price $47-54). D36V50F5 only for Lime + T7 (price unverified).
  - CURRENT PER LOAD USED IN THE MODEL
  | Load | Value | Basis |
  |---|---|---|
  | Q6A | 2.9 / 9.3 / 10.1 W | measured (Geerling) |
  | V4L | 1.3 W (250-270 mA) | datasheet |
  | SAWbird+ NOAA / GOES / H1 | 170 / 180 / 120 mA | Nooelec |
  | Lime | 4 W typical, 8.25 W allowance | Lime staff / M.2 spec |
  | Display | 3 / 6 / 13 W at 25/50/100% | model |
  | HF+ | 0.3 A at 5 V | provisional, unpublished |
  | LNB | 0.2-0.3 A at 13.2 V | unpublished |
  | Boni-Whip | 0.05-0.1 A at 12.5 V | unpublished |
  | Fans | 0.8-2 W | estimate |
  | T7 | 3 W typical, 7.5 W budget | storage.json |
  | Efficiencies | D36V50F12 92%, D36V28F5 88%, Q6A internal 85%, LDO Vout/Vin | Pololu 90-95%; estimates |
- **Notes:** I chose one power architecture:
  - **Pack:** 4S1P P50B, charged daily to 4.10 V/cell, behind a 7.5 A fuse and the INA228 shunt to node N.
  - **Charger:** IP2368 BZ, permanently on node N.
  - **Master switch:** #2813 HP, opened by the button, the RP2040 or a 12.8 V supervisor.
  - **Main 12 V:** D36V50F12 feeds SYS12: J21, a display branch with a 1.5 A eFuse, and AUX 12 V (default OFF).
  - **LAB 5 V:** D36V28F5 feeds the hub tree, HF+, LAB port and a 4.5 V LT3045 LNA rail with TPS2553 switches at 300 mA.
  - **Pack-fed LDOs:** two more LT3045s run straight from the switched pack node, LNB at 13.2 V and Boni-Whip at 12.5 V. No switching boost and no 18 V anywhere.
  
  There are no blockers in this lens. Ten findings are major. The biggest corrections:
  - Runtime and usable energy are overstated. Plan with 58 Wh warm and 50 Wh cold.
  - The display is under-budgeted. Model 10-14 W at 100%; the vendor input voltage is still unknown.
  - The LNB feed exists in four incompatible versions.
  - The LNA LDO has no defined input.
  - The CH334F/LAB 5 V wiring can back-feed into Q6A VBUS.
  - With the Lime, the Q6A's 17 W VCC_5V_PERI is exceeded if the T7 also runs from it.
  - The roughly 500 kHz switching of the 12 V buck sits near NAVTEX 490/518 kHz, and its light-load mode can wander through the LF time-signal band.
  - Cell and panel heat in sun: the charge NTC trips, and sustained 2000 nits is not reachable at 35 C ambient.
  
  Physics against the wishes: in hot noon sun, sustained 2000 nits is thermally impossible in a sealed handheld. Expect about 1000 nits sustained; 2000 is a burst mode. A 2000-nit panel at full brightness also roughly halves runtime.
  
  Model files:
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p2_power/model.py: usable energy, using a generic NMC/Si OCV curve, not Molicel data.
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p2_power/modes.py: per-mode power and VCC_5V_PERI.
  - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p2_power/thermal.py: case air rise and panel temperature.
  
  All runtime and thermal figures are models until the INA228 logs and the noon soak exist.
  
  Web use: 5 searches and 7 fetches. 3 fetches failed (TI 404, ADI 503, NKON 403).
  - Pololu 4095, fetched today: 13.3-50 V subject to dropout; 12 V ±4%; about 500 kHz under heavy load, light-load mode above 20 kHz; 4.5 A typical at 36 V in, 2.3-6.5 A depending on conditions; EN thresholds 1.2/1.35 V; sleep current 10-20 µA per volt; PG trips at -10%/+20%; $39.95 ($36.75 at 5+); 'Rationed'.
  - Molicel P50B page: 18 Wh, 60 A continuous, 12.8 mΩ.
  - LT3045, from a datasheet mirror found by search: 1.8-20 V in, 0-15 V out, 500 mA, 260 mV dropout, programmable current limit, can be paralleled.
  - Pololu S18V20F12: 2 A SEPIC, so no verified Pololu 12 V buck-boost of 5 A or more exists.
  - Adafruit CH334F guide: the upstream 5V pin is the board's power input; each downstream port's 5V pin is an output.
  - P50B price: EUR 6.75 at NKON, from a search snippet only.
  
  Still unverified: currents of the HF+, Boni-Whip, Bullseye LNB and noise source; Wisecoco input voltage and power; the D36V50F12 dropout curve and its real fundamental frequency versus load; IP2368 BZ world price and how it behaves with a 45 W source; BMS price; the AO3407A and TPS709 ratings, which are from memory.
  
  All 25 conflicts_for_final_checks items are resolved in proposed_decisions as C1-C25. P1-P6 are additional power decisions.

## integration:lens2 (run `wf_221684d9-b6c`)

- **Lens:** Interfaces + buses + software: one USB port map, 40-pin header and bus map, GPIO/expander ownership, IMU/HMI MCU interface, kernel and package pinning, single process architecture (labd/labrx/labclassify), NPU and recorder services, TX-capable package exclusion.
- **Issues:**
  1.
    - **Area:** Process architecture / SDR ownership
    - **Components:**
      - npu_training sdr-ingestd/spectrumd/recorderd
      - lab_ui_hf labd + labrx@ + engine units
      - radio_lab lab-sched/lab-rec/rflab
    - **Problem:** Three designs each claim to open the SDRs. npu_training says sdr-ingestd is the only process that opens them. lab_ui_hf lets the engines (sdrangelsrv, satdump-pass@, openwebrx, readsb, ais-catcher, auto-rx) open the device directly under a lease. radio_lab adds lab-sched with advisory flocks and its own lab-rec SoapySDR recorder. A USB SDR accepts one opener at a time (librtlsdr claims interface 0; libairspyhf is exclusive), so whichever process opens second fails. Built as written, the NPU capture and the pass engines cannot run together. There would also be two RAM rings and two recorders.
    - **Severity:** blocker
    - **Fix:** Adopt one model with two lease modes, both owned by labd. (1) labrx mode, the default: labrx (merging sdr-ingestd, spectrumd, recorderd, lab-rec and lab-sweep) is the only opener. It feeds the single RAM ring, the recorder, the NPU tap, gr-satellites, direwolf and SDR++ (network source). Satellite passes are recorded, then decoded by SatDump from the baseband file. (2) Engine-exclusive mode: readsb, AIS-catcher, auto_rx, OpenWebRX+, sdrangelsrv and Expert GUIs get the device itself, with ai_tap=false and REC limited to products. labd switches modes through its hand-off sequence. Delete the lab-sched flocks and the npu 'only opener' rule.
    - **Evidence:** npu_training.json final.architecture 'P1 sdr-ingestd ... the only process that opens the SDRs'; lab_ui_hf.json final.ui_system.resource_arbitration sections 5 and 7 (engine units BindsTo dev-lab-<sdr>.device) and capability flags; radio_lab.json final.software (lab-sched per-SDR flock, lab-rec); report_research register decision 50.
    - **Fix cost:** $0 hardware; about 1-2 person-weeks of re-specification inside the already planned labrx/labd work (estimate).
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  2.
    - **Area:** HMI / power-supervisor MCU
    - **Components:**
      - display RP2040 (radio_lab)
      - HMI RP2040 (lab_ui_hf)
      - power-controller MCU (power.json)
      - NPU buttons (npu_training)
    - **Problem:** The RP2040 has a different role and link in each file. radio_lab puts a 'display RP2040' on CH334F H1, powered by LAB 5 V after the master switch. lab_ui_hf merges HMI, dimming, IMU relay, heartbeat, hard-cut and safe-boot into one RP2040 on UART7. power.json wants an always-on MCU that pulses J21 pin 3. The register map lists the RP2040 on both H1 and UART7. Power-key boot pulses and hard-cut need an MCU that is powered while the Q6A is off. A USB-H1 device fed from LAB 5 V is unpowered exactly when those functions are needed.
    - **Severity:** major
    - **Fix:** Use one RP2040 (HMI and supervisor) on the always-on 3.3 V rail. It covers encoders, keys, VEML7700, NTCs, backlight PWM, piezo/LED, IMU relay on UART1, heartbeat watchdog, an open-drain J21 pin 3 pulse, the hard-cut output, the safe-boot line and optionally a 25 kHz fan PWM. Host link: UART7 (pins 32/29) primary. Wire its native USB to CH334F H1 as a fallback, and enable the D+ pull-up only when H1 VBUS is present.
    - **Evidence:** radio_lab.json final.usb_power_case_plan 'H1: display RP2040' and integ.connections; lab_ui_hf.json final.stack_changes 'HMI RP2040: merged with the dimming MCU and wired to UART7'; power.json 'small power-controller MCU that also handles shutdown'; npu_training.json final.hardware_needs item 4; register decisions 56 and 129.
    - **Fix cost:** Saves one RP2040 board; about $0-5 net.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/power.json
  3.
    - **Area:** GPIO / safe power-up state
    - **Components:**
      - 40-pin header
      - UM3304 TXB-type translators
      - bias, LNB, Boni-Whip, VBUS-cut, noise-source enables
    - **Problem:** lab_ui_hf drives these from header GPIOs held by labd: RF switches, the HF+ selector relay, LNA 5 V, LNB, the 12 V active-antenna rail, DC-sense, VBUS-cut pigtails and the noise-source switch. On schematic v1.21 almost every free header GPIO (pin 7, 11, 12, 19-26, 29-40) sits behind a UM3304. That is a TXB-type auto-direction buffer: 4 kOhm output drivers, at most 50 pF, and any pull resistor must be over 50 kOhm. Its state follows whatever the SoC presents during UEFI and boot, so the 'pull-downs keep every supply OFF' rule cannot work on these lines. A relay coil or MOSFET gate cannot be driven from them either. An LNB or bias rail could therefore turn on during boot, into a DC-short antenna.
    - **Severity:** major
    - **Fix:** Move every power, bias, RF-switch, relay and source enable to MCP23017 outputs. They power up high-Z, so 100 kOhm pull-downs hold everything OFF. Power the MCPs from Q6A VCC_3V3, so that Q6A off means everything off. Drive relay coils through a driver IC. Use header GPIOs only for PPS, the UARTs, I2C, open-drain INT/ALERT on UM3204H pins 3/5, SWD and safe-boot to the RP2040, and the buffered fan line.
    - **Evidence:** lab_ui_hf.json final.ui_system.architecture section 2; schematic text /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_sch/q6a_sch.txt lines 3720-3940 (U16/U51-U54 UM3304, U47/U48 UM3204H, Q12/Q13 CJ3134K); gnss_imu.json own fix ('UM3304 (TXB-type, 4 kOhm output buffers, max 50 pF load, needs pull resistors >50 kOhm)'); radio_lab.json integ.connections MCP #1 note.
    - **Fix cost:** About $3-6 for a second expander and a relay driver.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
      - https://www.union-ic.com/upload/Datasheet/Datasheet_UM3304_Rev16.pdf
  4.
    - **Area:** Bias-tee interlock
    - **Components:**
      - RTL-SDR Blog V4L internal tee
      - librtlsdr2 +lab
      - labd DC-sense interlock
    - **Problem:** labd is meant to own every bias source and lock bias off on DC-short antennas (the 9:1 balun, hairpin-matched Yagis). But librtlsdr's rtlsdr_set_bias_tee() is open to any process that opens the dongle. That includes SatDump, readsb, SDRangel, OpenWebRX+, rtl_biast and SDR++ configs. In engine-exclusive leases the interlock can therefore be bypassed in software. RTL-SDR Blog warns that prolonged shorting can kill the LDO or fuse.
    - **Severity:** major
    - **Fix:** Add a third patch to the planned librtlsdr 2.0.1 .so.2 rebuild. rtlsdr_set_bias_tee() and rtlsdr_set_bias_tee_gpio() refuse 'on' unless the environment variable LAB_BIAS_OK equals the device serial. labd sets that variable only in the units of DC-safe profiles. The policy audit also flags bias options in generated engine configs.
    - **Evidence:** lab_ui_hf.json final.ui_system.architecture ('V4L tee via its driver'); register decision 101 (bias onto DC-shorted antennas, never 'rtl_eeprom -b 1'); register decision 28 (librtlsdr rebuild).
    - **Fix cost:** $0; about 20 lines of C plus a test.
    - **Sources:**
      - https://github.com/osmocom/rtl-sdr
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/rf_frontend.json
  5.
    - **Area:** USB port map
    - **Components:**
      - blue USB 3.1
      - FE1.1s P1-P3
      - CH334F H1-H4
      - IMU puck
      - T7
    - **Problem:** The register's Lime-agnostic map fills all four CH334F ports: H1 HMI RP2040, H2 IMU puck 'if not on UART', H3 LAB, H4 HF+. When the Lime and T7 are kept, the T7 takes the blue port and RTL-A must move to the hub. If the IMU is on USB-CDC (as in gnss_imu final and radio_lab H2), or if UART7 fails, a fifth port is needed. lab_ui_hf also time-shares the blue port between the T7 and an instrument hub, which means re-plugging the only SuperSpeed port.
    - **Severity:** major
    - **Fix:** The IMU puck never uses USB. Its MCU sends framed UART (115200 baud, CRC) over a 4-core shielded lead of 1.5 m or less to HMI RP2040 UART1. Add RS-485 transceivers only if the 1e6-frame test shows errors. The resulting map fits all four configurations (budget table): RTL-A on blue without the Lime, or on H2 with it; H1 only for the HMI RP2040 if UART7 fails; instruments only on LAB USB (H3).
    - **Evidence:** report_research register decision 129 and conflict 5; gnss_imu.json final ('RP2040-Zero ... sends quaternion and accuracy over USB-CDC'); radio_lab.json final.usb_power_case_plan (H2 boom IMU puck); lab_ui_hf.json resource_arbitration ('Instrument port: the blue USB 3.1 port, time-shared with the T7').
    - **Fix cost:** $0-4 (connector; optional 2x RS-485 transceivers).
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/gnss_imu.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  6.
    - **Area:** VBUS / LAB 5 V budget
    - **Components:**
      - Pololu D36V28F5 LAB 5 V
      - TPS2553 LAB port and LNA injectors
      - CH334F
      - Airspy HF+
      - LNA LDO
    - **Problem:** The register moves the HF+, CH334F, puck, RP2040, bias injectors and LAB port onto LAB 5 V, which has a 2 A fuse. The sum of the current limits is about 2.2-2.4 A: CH334F 0.1 A, HF+ 0.3 A (unpublished), LAB-port TPS2553 at 1 A (up to 1.075 A per TI), and three LNA feeds at 0.25-0.3 A each. Typical draw is only about 1.0 A (model), but a worst case blows the fuse and takes down the hub, HF+ and RTL-A (Lime case) mid-pass. The 'LT3045-class' LNA LDO (0.5 A) is also below the 0.9 A sum of the three feed limits.
    - **Severity:** major
    - **Fix:** Set the LAB-port TPS2553 to about 0.6 A in field mode (the largest field instrument is about 0.45 A; the bench hub is bank-powered). Fit a 3 A LAB 5 V fuse; the files rate the D36V28F5 at 3.2 A, so check its temperature in the sealed case. Feed the LNAs from a 1 A low-noise rail (two paralleled LT3045, or a 1-2 A LDO; part to be verified). Enable LAB 5 V only while the Q6A is on.
    - **Evidence:** register decision 62; radio_lab.json integ.power_budget ('Budget 2 A'); TI TPS2553 page (75-1700 mA adjustable, 1 A setting 925-1075 mA); rf_frontend SAWbird+ currents (NOAA 170 mA, GOES 180 mA budget); model in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/iface/budget.py.
    - **Fix cost:** About $3-8 (fuse, RILIM change, second LDO or larger LDO).
    - **Sources:**
      - https://www.ti.com/product/TPS2553
      - https://rigpix.com/miscrx/airspy_hfplusdiscovery.htm
  7.
    - **Area:** NPU services / CPU-first MVP
    - **Components:**
      - labclassify inferd-cpu
      - fusiond
      - RTL-F/RTL-C/HF-F profiles
    - **Problem:** Until the Phase-0 HTP gate passes, the MVP runs on the CPU, and CPU mode handles 4-6 tiles/s. Without the Lime the demand is about 14.6 tiles/s for 2x V4L (verified), plus about 2 tiles/s for an HF-F profile at 768 ksps (my model), about 16.6 tiles/s in total. The broker would therefore drop about two thirds of the tiles. The UI and labeller would see silent coverage gaps.
    - **Severity:** major
    - **Fix:** Add an explicit CPU-mode schedule: RTL-C on both RTLs (1.6 tiles/s) plus RTL-F at K=4 only on the SDR with the active pass (about 3.5 tiles/s), about 5 tiles/s in total. Run HF-F only when the RTLs are idle. Show 'reduced coverage' in the status chip. Scale the HTP promotion gate to the SDR set actually present: p99 of 11.7 ms or less with the Lime, about 28 ms or less without it (50% duty at about 17.6 tiles/s).
    - **Evidence:** npu_training.json final.budgets ('CPU mode: 4-6 tiles/s'); register decision 41 ('2x V4L only: about 14.6 tiles/s'); register decision 43 (add HF-F); my calculation in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/iface/budget.py (model).
    - **Fix cost:** $0.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  8.
    - **Area:** RAM / ring buffer
    - **Components:**
      - labrx RAM ring
      - labclassify
      - trainer
      - engines
    - **Problem:** npu_training still sizes the IQ ring at 6 GiB with training and 8 GiB without. The register says 4/6 GiB with the Lime and 1.5 GiB or less without; lab_ui_hf says about 4 GiB. My estimate of non-ring use is 3.0-7.2 GiB, plus up to 2 GiB for the trainer. Against about 11 GiB visible (unverified), an 8 GiB ring cannot coexist with the shell, engines and labclassify.
    - **Severity:** major
    - **Fix:** Make ring size one boot-time parameter of labrx, derived from the SDR set: 1.5 GiB without the Lime (about 2 min of 2 RTLs + HF+); 4 GiB with the Lime and training allowed; 6 GiB with the Lime and training disabled. Delete the 8 GiB value. The scheduler starts the trainer only when no engine using more than 0.5 GiB is running.
    - **Evidence:** npu_training.json final.budgets RAM; register decision 46; lab_ui_hf integration_table labrx ('RAM ring of about 4 GiB').
    - **Fix cost:** $0.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  9.
    - **Area:** Fan control pin
    - **Components:**
      - header pin 33 / GPIO56
      - pwm-gpio
      - AO3400/2N7002
      - NF-A4x10 5V PWM
    - **Problem:** The register's 'GPIO56 (PoE-HAT overlay) vs header pin 33' conflict is false: the schematic shows GPIO56 is FP_SPI_MISO, which is header pin 33 (QUP1 SE6, spi14). The real problem is the drive. Pin 33 is behind UM3304 U54 (TXB-type, 50 pF or less), and the register drives an AO3400 gate directly; AO3400 gate capacitance is in the hundreds of pF (from memory), which is far beyond that limit. Also, the 1 kHz pwm-gpio comb lands exactly on 40 and 60 kHz (JJY, MSF/WWVB) and ticks audibly.
    - **Severity:** minor
    - **Fix:** Preferred: a 25 kHz hardware PWM from the HMI RP2040 into the fan's PWM input through a 2N7002, going to 100% when the heartbeat is lost. Its harmonics fall at 50, 75 and 100 kHz, off the LF carriers. Fallback: pin 33 through a 74LVC1G17 buffer and a 2N7002, using kernel pwm-fan from a fixed copy of the PoE-HAT overlay (spi14 disabled).
    - **Evidence:** q6a_sch.txt lines 274-286 (GPIO_56 = FP_SPI_MISO) and 3665 (FP_SPI_MISO_3V3 = pin 33); mechanical_thermal.json ('pwm-gpio on tlmm GPIO 56 (header pin 33)'); register decision 17.
    - **Fix cost:** About $0.5.
    - **Sources:**
      - https://dl.radxa.com/dragon/q6a/hw/radxa_dragon_q6a_schematic_v1.21.pdf
  10.
    - **Area:** UART7 availability and wiring
    - **Components:**
      - UART7 pins 32/29
      - UM3304 U16
      - HMI RP2040
    - **Problem:** Register decision 56 calls UART7 availability unverified. The overlay does exist in radxa-overlays main: qcs6490-radxa-dragon-q6a-uart7.dtso. It drives TX on pin 32 and RX on pin 29, disables spi7 and i2c7, and lists spi7, uart7, i2c7, gpio30 and gpio31 as exclusive. The remaining risks are whether the package on the held image ships it, and the UM3304 limit of 50 pF or less, which constrains how far the RP2040 can sit from the header.
    - **Severity:** minor
    - **Fix:** Install or compile the overlay from radxa-overlays main if the held image lacks it. Keep the UART7 wires 20 cm or shorter, or buffer them with a 74LVC2T45. Use 2-wire mode and leave pins 31/11 (CTS/RTS) free. Keep the H1 USB fallback wired.
    - **Evidence:** Web fetch of the radxa-overlays directory and of the uart7 .dtso (18 Oct 2026); gnss_imu.json ('UM3304 ... max 50 pF'; 'Keep header wires under about 20 cm').
    - **Fix cost:** $0-1.
    - **Sources:**
      - https://github.com/radxa-pkg/radxa-overlays/tree/main/arch/arm64/boot/dts/qcom/overlays
      - https://raw.githubusercontent.com/radxa-pkg/radxa-overlays/main/arch/arm64/boot/dts/qcom/overlays/qcs6490-radxa-dragon-q6a-uart7.dtso
  11.
    - **Area:** I2C2 LAB BUS electrical rules
    - **Components:**
      - I2C2 pins 27/28 (UM3204H U47)
      - TCA9517
      - sled MCP23017 #2
      - ADS1115
    - **Problem:** I2C2 passes through a UM3204H. That is a TXS-type part with internal 10 kOhm pull-ups and one-shot accelerators. It is I2C-capable but sensitive to extra low-value pull-ups and capacitance. The TCA9517's B port has a static offset, so it must not face the translator or another offset buffer. No file states the orientation or the pull-up values.
    - **Severity:** minor
    - **Fix:** Connect TCA9517 port A to the header side and port B to the LAB BUS cable. Add no pull-ups below 10 kOhm on the header segment. Fit 4.7 kOhm on the sled side, run at 100 kHz, never chain B to B, and use PCA9615 for cables over 1 m. Test with i2cdetect -y -r 2 (GENI has no SMBus Quick) and 1,000,000 reads with zero errors per address.
    - **Evidence:** q6a_sch.txt U47 block (QUPSE2_I2C to UM3204H); gnss_imu.json own fix (U47 UM3204H pins 8/10/27/28; i2cdetect -r); radio_lab.json conflicts note on the PCA9306.
    - **Fix cost:** $0.
    - **Sources:**
      - https://www.union-ic.com/upload/Datasheet/Datasheet_UM3204_Rev16.pdf
  12.
    - **Area:** I/O expanders
    - **Components:**
      - MCP23017 #1 0x20
      - second in-case expander
      - MCP23017 #2 sled
    - **Problem:** radio_lab's MCP #1 map uses about 9 lines. The merged design needs at least 14 outputs: LAB EN, AUX EN, 3 VBUS-cuts, 3 LNA feeds, LNB, Boni-Whip, 2 selector relays, sled power and spare. It also needs about 10 inputs: 6 FAULTs, DC-sense and selector readback. And on current MCP23017 silicon, GPA7 and GPB7 are output-only (datasheet rev D/E).
    - **Severity:** minor
    - **Fix:** Use MCP #1 (0x20, outputs only; GPA7/GPB7 used as outputs). Add a TCA9535 at 0x24 for all inputs, driven by the built-in pca953x driver as a gpiochip, with its open-drain INT on pin 5 (UM3204H). labd owns both. The sled keeps MCP #2 (0x21) and the ADS1115 (0x48).
    - **Evidence:** radio_lab.json integ.connections ('MCP23017 #1 pin map ... GPA7 and GPB7: outputs only (... from memory, verify)'); MCP23017 change confirmed by web search (Hackaday, Tasmota docs, DS20001952 rev E listing); kernel config GPIO_PCA953X=y (register decision 26).
    - **Fix cost:** About $2-3.
    - **Sources:**
      - https://hackaday.com/tag/debugging-hell/
      - https://tasmota.github.io/docs/MCP230xx/
      - https://www.farnell.com/datasheets/4797368.pdf
  13.
    - **Area:** Stale interface leftovers
    - **Components:**
      - radio_lab integ
      - radio_lab P17
      - npu_training software list
    - **Problem:** Superseded items remain in radio_lab integ.connections:
  - Binding both expanders with pinctrl-mcp23s08 (the driver is absent).
  - The RP2040 counter on USB-CDC H4 (the final puts it on I2C 0x30).
  - The LNB on sled GPA6 into a ZFBT and sled RF2 (the final says the LNB never goes on the sled).
  - A 0.5 A AUX PTC (the final uses 0.75 A).
  - 'USB 3.1: T7 only; RTL on FE1.1s P1'.
  P17 also captures a BNO085 on I2C2. npu_training still lists librtlsdr 2.0.3 and Set B.
    - **Severity:** minor
    - **Fix:** Strike these lines before STACK.md. Re-point P17 to capture the puck UART at the HMI RP2040. Keep only the .so.2 recipe.
    - **Evidence:** radio_lab.json integ.connections and final.procedures P17; npu_training.json final.software; register decisions 28, 38 and 56.
    - **Fix cost:** $0.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  14.
    - **Area:** Display touch fallback
    - **Components:**
      - display.json I2C touch fallback
      - UART6
      - PPS GPIO96
    - **Problem:** display.json's I2C-touch fallback has three collisions:
  - It uses I2C6 on pins 3/5, which share QUP0 SE6 with UART6 (GNSS), so I2C6 is unavailable once UART6 is enabled.
  - It puts INT on pin 7, which is GPIO96, the PPS line.
  - It puts RST on pin 12, which this map gives to the RP2040 SWD.
    - **Severity:** minor
    - **Fix:** If a panel turns out to be I2C-only, put it on I2C0 next to the INA228. Move INT to pin 36 through a 74LVC1G17 buffer and RST to pin 37. Otherwise accept only USB-HID touch panels (the Wisecoco purchase condition).
    - **Evidence:** display.json fallback text ('pins 1/6/3/5 (I2C6), INT to pin 7 (GPIO_96) and RST to pin 12'); gnss_imu.json ('UART6 (pins 16/18) and I2C6 (pins 3/5) share QUP SE6').
    - **Fix cost:** About $0.5.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/display.json
  15.
    - **Area:** TX-capable packages
    - **Components:**
      - QSSTV 9.5.8
      - direwolf 1.7
      - fldigi in radio_lab procedures
    - **Problem:** The register keeps wsjtx (GUI) and fldigi off the device, but lab_ui_hf installs QSSTV as an 'RX-only fallback'. QSSTV transmits SSTV with PTT. direwolf is a TX-capable TNC that can beacon and digipeat. radio_lab procedures still depend on fldigi for WEFAX, DWD RTTY/SYNOP, NAVTEX, ppm measurement and CW spot checks, so deleting fldigi breaks those procedures.
    - **Severity:** minor
    - **Fix:** Remove QSSTV; use the OpenWebRX+ SSTV decoder, or an RX-only decoder fed from labrx audio. Keep direwolf with an audited config: input-only audio device, no PTT, and no PBEACON, DIGIPEAT or IGTXVIA lines. Add both to the CI and self-test policy audit. Re-point the radio_lab P20 steps to the SDRangel WEFAX, RTTY and NAVTEX channels and to the labrx carrier-offset ppm measurement.
    - **Evidence:** lab_ui_hf.json tech_stack ('qsstv 9.5.8 ... RX-only fallbacks') and integration_table (direwolf 'No PTT device configured'); radio_lab.json final.procedures (fldigi WEFAX/RTTY/NAVTEX steps); register decision 10.
    - **Fix cost:** $0.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  16.
    - **Area:** Lease enforcement
    - **Components:**
      - labd Arbiter
      - engine units run as user labrx
      - udev group labrx
    - **Problem:** Every headless engine runs as the same user labrx, and udev gives that group access to every SDR and instrument node. Leases are therefore enforced only against the GUI user, not between engines. A mis-generated config, or opening a device by index, can grab a leased SDR.
    - **Severity:** minor
    - **Fix:** At lease time labd writes a transient drop-in for the engine unit: DevicePolicy=closed plus DeviceAllow on the leased /dev/bus/usb/BBB/DDD node (rw), or on /dev/limeX. Leases are then cgroup-enforced.
    - **Evidence:** lab_ui_hf.json resource_arbitration section 1 (ENFORCEMENT).
    - **Fix cost:** $0.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  17.
    - **Area:** Wi-Fi/BT on the shared hub
    - **Components:**
      - FCU760K (AIC8800D80) on FE1.1s P4
      - QUIET profile
    - **Problem:** QUIET relies on rfkill. The Wi-Fi/BT module stays enumerated on the same FE1.1s that carries RTL-B and the HF+. Whether the vendor AIC8800 driver honours rfkill without background USB traffic or 2.4 GHz emissions is unverified.
    - **Severity:** minor
    - **Fix:** QUIET runs rfkill block wlan and bluetooth, and also unbinds the Wi-Fi USB device (port 1-1.4), or switches WIFI_PWR_EN off if it is exposed. Accept it when usbmon shows no frames from that device and the tinySA shows no 2.4 GHz activity.
    - **Evidence:** q6a_sch.txt (USBDEV4 to the WIFI page, FCU760K); compute.json (FCU760K, AIC8800 a69c:8d80); register decision 8.
    - **Fix cost:** $0.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/compute.json
  18.
    - **Area:** Instrument USB identity
    - **Components:**
      - tinySA
      - LiteVNA
      - FT232RL fallback
      - HMI/IMU CDC
      - ModemManager/brltty
    - **Problem:** NanoVNA-family and tinySA instruments commonly enumerate as the same STM32 virtual COM port (0483:5740; check each unit on arrival). Ubuntu's ModemManager probes new ttyACM ports, and brltty claims some FTDI and CH34x serial IDs. Either can disturb labd's instrument drivers, the FT232RL GNSS fallback and the RP2040 CDC ports. No file mentions this.
    - **Severity:** minor
    - **Fix:** Purge brltty and mask ModemManager, or set ID_MM_DEVICE_IGNORE on all lab devices. Name devices through udev by iSerial or product string, with a labd identify query, as /dev/lab/<name>.
    - **Evidence:** lab_ui_hf.json integration_table (NanoVNA-Saver, QtTinySA, 'labd serial drivers'); gnss_imu FT232RL fallback; general Ubuntu behaviour (unverified on the Radxa OS r2 image).
    - **Fix cost:** $0.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  19.
    - **Area:** Package pinning
    - **Components:**
      - Mesa
      - luarvique PPA
      - Radxa repo
      - GitHub release debs
    - **Problem:** lab_ui_hf says to 'hold the validated Mesa set: noble 24.0.5 versus noble-updates 25.2.8' without choosing one. Radxa's Vulkan numbers and the npu_training VkFFT plan are on Mesa 25.2.8. Third-party sources can also drift or vanish: the PPA may drop 1.2.126, and the Radxa index now carries only 7.0.11-7.
    - **Severity:** minor
    - **Fix:** Hold mesa-* 25.2.8-0ubuntu0.24.04.4 with libdrm 2.4.125. Mirror every third-party .deb into the signed aptly repo: OpenWebRX+ 1.2.126, linux-headers 6.18.2-4 from GitHub, OpenHantek, the radxa-firmware set and qcom-qnn-sdk-v68. Then disable the PPA and Radxa sources, or pin them at 100.
    - **Evidence:** lab_ui_hf.json tech_stack; software.json ('Mesa 25.2.8 Turnip/freedreno from noble-updates works: Radxa measured 808 GFLOPS'); npu_training.json software; register decisions 24 and 35.
    - **Fix cost:** $0.
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/system-config/vulkan
  20.
    - **Area:** Real-time priorities
    - **Components:**
      - lime:Rx0
      - RTL/HF+ ingest
      - CPU7 isolation
    - **Problem:** Four RT settings conflict: compute uses chrt -f 10 (Lime warns that RT throttling drops packets); npu_training's sdr-ingestd uses FIFO 50 on CPU7; the wideband verify uses FIFO 70 on cpu4-6; lab_ui_hf uses FIFO 50 on isolated CPU7.
    - **Severity:** minor
    - **Fix:** lime:Rx0 at SCHED_FIFO 10 on isolated CPU7 (Lime only). RTL and HF+ ingest at SCHED_OTHER nice -5 on CPU4-6; USB bulk reads are light. Decide between cpu7 and cpu4-6 with the limeTRX loss counters.
    - **Evidence:** compute.json CPU budget; npu_training.json architecture P1; register decision 19.
    - **Fix cost:** $0.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/compute.json
  21.
    - **Area:** Recorder format
    - **Components:**
      - labrx SigMF writer
      - HF+
    - **Problem:** HF+ recordings are specified as cf32_le at 6.1 MB/s (22 GB/h). The device's native stream is int16 IQ at 3.07 MB/s, so the format doubles UFS writes and storage for no gain.
    - **Severity:** minor
    - **Fix:** Record the HF+ as ci16_le (lossless, 11 GB/h). Use cf32 only for derived products.
    - **Evidence:** lab_ui_hf.json resource_arbitration (HF+ cf32_le about 6.1 MB/s) and integration_table; register decision 73.
    - **Fix cost:** $0.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  22.
    - **Area:** UFS partitioning vs raw-IQ space
    - **Components:**
      - 128 GB UFS
      - A/B root
      - lab-snap
      - encrypted data
      - 20 GB NPU dataset quota
    - **Problem:** The register suggests an A/B root on UFS when there is no T7. npu_training adds encrypted data partitions and a 20 GB dataset quota. Together these cut the about 92-100 GB 'free after OS' to about 50-58 GB of raw-IQ space, about 1.1 h of 2 RTLs + HF+.
    - **Severity:** minor
    - **Fix:** Use one root plus a 6 GB rescue rootfs on UFS, leaving about 66-74 GB for IQ. Put snapshots and offline update bundles on a V30/A2 microSD (61 MB/s write measured), which also takes raw-IQ overflow, or on a USB stick via the LAB port. Use the T7 only with the Lime.
    - **Evidence:** register decisions 35, 72 and 73; npu_training.json architecture ('Data partitions are encrypted at rest'); storage.json (microSD 61 MB/s).
    - **Fix cost:** microSD about $15-25 (price unverified).
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/storage.json
  23.
    - **Area:** PPS fallback vs libgpiod
    - **Components:**
      - gnss Route A daemon
      - libgpiod 1.6.3
      - pps-gpio
    - **Problem:** Route A, the PPS fallback, needs REALTIME edge timestamps. Those exist only in the GPIO v2 uAPI (5.11+). libgpiod 1.6.3 on noble uses the v1 uAPI, whose timestamps are monotonic (as I recall). Written against noble's libgpiod, the fallback would carry the wrong timescale.
    - **Severity:** minor
    - **Fix:** Write the fallback in C directly on the v2 ioctl with the EVENT_CLOCK_REALTIME flag, or vendor libgpiod 2.x into that daemon only. Never run pps-gpio and Route A on GPIO96 at the same time.
    - **Evidence:** register decisions 27 and 32; gnss_imu.json own fix ('GPIO character device v2 API ... CLOCK_REALTIME').
    - **Fix cost:** $0.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/gnss_imu.json
  24.
    - **Area:** Power key / J21 pin 3
    - **Components:**
      - case power button
      - RP2040 open-drain
      - labpowerd KEY_POWER
    - **Problem:** power.json wires the case button straight to J21 pin 3. lab_ui_hf and the power verify have the RP2040 pulse pin 3 open-drain after a BMS cut or charge. Neither says how the two coexist, or how long the RP2040 may hold the pin before the PMIC's long-press reset acts (timer unverified).
    - **Severity:** minor
    - **Fix:** Wire the button and the RP2040 output as a wired-OR, both open-drain to GND. The RP2040 senses the button and pulses for 0.5-1.5 s, never more than 2 s. Shutdown requests go over the UART to labinput, then labpowerd, not as pin-3 pulses.
    - **Evidence:** power.json ('wire J21 pin 3 (PWR) to a case push-button'; SGM811 fake-press fix); lab_ui_hf.json process_supervision.
    - **Fix cost:** $0.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/power.json
  25.
    - **Area:** Hard-cut sensing and INA228 ownership
    - **Components:**
      - RP2040 critical-voltage input
      - INA228 on I2C0
      - labpowerd
    - **Problem:** The RP2040 hard cut needs a 'critical voltage' input, but the only gauge is the INA228, read by labpowerd over i2c-dev. A second I2C master on I2C0 would conflict.
    - **Severity:** minor
    - **Fix:** Give the RP2040 its own ADC divider on the pack (about 1:6, accurate to about 2%) for the hard-cut condition. The INA228 stays owned by labpowerd alone, with ALERT to header pin 3 (UM3204H, open-drain compatible). Remove the breakout pull-ups.
    - **Evidence:** register decisions 65 and 66; q6a_sch.txt Q12/Q13 CJ3134K shifter on I2C0.
    - **Fix cost:** About $0.1.
    - **Sources:**
      - https://www.adafruit.com/product/5832
  26.
    - **Area:** Back-drive and off-state draw
    - **Components:**
      - display board rail
      - touch USB bridge
      - LAB 5 V tree
      - HMI RP2040 USB
    - **Problem:** The display board, and its USB touch bridge, have their own rail from 12 V. LAB 5 V (CH334F, HF+) also stays up after poweroff while the master switch is on. With the Q6A off, the touch bridge's D+ pull-up back-drives FE1.1s P2, and the backlight and HF+ keep draining the pack.
    - **Severity:** minor
    - **Fix:** Gate the display rail and LAB 5 V EN on the Q6A on-state (VCC5V_HDMI_TX0 or VCC_3V3 sense, or RP2040 control). Firmware enables the RP2040 USB only when H1 VBUS is present.
    - **Evidence:** register decision 68 ('board's VBUS comes from its own regulator'); radio_lab LAB 5 V after #2813; q6a_sch.txt VCC5V_HDMI_TX0.
    - **Fix cost:** About $1-2 (load switch).
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/display_market.json
  27.
    - **Area:** HMI MCU GPIO budget
    - **Components:**
      - RP2040 (30 GPIO)
    - **Problem:** After the merge, the RP2040 needs about 30 GPIO without the fan and 31 with it, against 30 available. The lines are: 2 encoders (6), 6 keys, I2C (2), 2 UARTs (4), backlight, piezo, WS2812, power-button sense, J21 pin 3, hard cut, safe-boot, H1 VBUS sense and 3 ADC inputs.
    - **Severity:** minor
    - **Fix:** Use a 2x3 key matrix (saves 1-3 GPIO), or a 48-GPIO RP2350B board.
    - **Evidence:** lab_ui_hf.json HMI RP2040 firmware row; this audit's count.
    - **Fix cost:** $0-3.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  28.
    - **Area:** Naming collisions
    - **Components:**
      - radio_lab 'rflab daemon'
      - npu_training rflab.target, /run/rflab, /opt/rflab, SigMF 'rflab' extension, rflabd.py
    - **Problem:** 'rflab' names the MCP23017 owner in radio_lab, and also the NPU target, its IPC sockets and its SigMF namespace in npu_training. The npu 'ui (P7)' also has its own waterfall renderer, duplicating the Lab Shell QQuickItem waterfall.
    - **Severity:** minor
    - **Fix:** Use one namespace: lab.target, /run/lab, /opt/lab and the SigMF extension 'lab'. Make rflab a labd module, labctl the CLI for it, and draw the waterfall only in Lab Shell from labrx shared memory.
    - **Evidence:** npu_training.json final.architecture; radio_lab.json final.software; register decision 50.
    - **Fix cost:** $0.
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  29.
    - **Area:** LimeSuiteNG packaging (Lime only)
    - **Components:**
      - LimeSuiteNG limesdr-micro-staging 37cb183
      - la9310_limesdr DKMS
      - Amarisoft plugin
    - **Problem:** At the pinned commit 37cb183 (16 Oct 2026), debian/control builds limepcie-dkms but no la9310_limesdr DKMS package, although the Micro needs la9310_limesdr. plugins/CMakeLists.txt defaults BUILD_PLUGINS_AMARISOFT to ON on UNIX. Only debian/rules sets it to FALSE.
    - **Severity:** minor
    - **Fix:** If the Lime is kept, add a la9310-limesdr-dkms +lab package for the held 6.18.2-4 headers, always pass -DBUILD_PLUGINS_AMARISOFT=OFF, and have CI fail if any amarisoft plugin .so is present.
    - **Evidence:** git show 37cb183:debian/rules, :debian/control and :plugins/CMakeLists.txt in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/src/limeng.
    - **Fix cost:** $0.
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro-staging
- **Proposed decisions:**
  1.
    - **Question:** C1 (register conflict 1): LimeSDR Micro keep or drop, and its interface dependents?
    - **Decision:** Make the Lime a gated optional. Keep the cancellable pre-order and decide on 31 Jan 2027 or on delivery. No core function depends on it. Prepare two variants of the USB map, overlays, kernel cmdline (CPU7 isolation, pcie_aspm=off), RAM ring and DKMS set. Select the variant with one labd/labrx config switch.
    - **Reason:** The core targets run on 2x V4L plus the HF+. The USB map below works in both variants, and the driver is still unvalidated on arm64 or Qualcomm.
    - **Consequences:** With the Lime: T7 on the blue port, RTL-A on CH334F H2, CPU7 isolated, 4/6 GiB ring, la9310 DKMS, guard covers limeTRX. Without it, all of that is deleted.
    - **Alternatives rejected:** Making it core now: unvalidated driver, about $267, +20 W peak. Dropping it now: loses a cancellable, zero-cost option on S-band and wideband NPU.
  2.
    - **Question:** C2: Q6A RAM tier?
    - **Decision:** Buy the 12 GB board now.
    - **Reason:** RAM table (model): non-ring use is 3.0-7.2 GiB, plus 2 GiB for the trainer, plus the ring. An 8 GB board cannot run on-device T2 training alongside the shell, engines and labclassify, and RAM cannot be added later.
    - **Consequences:** Ring is 1.5 GiB without the Lime and 4 or 6 GiB with it. Measure visible RAM after carve-outs in the W1-2 gates.
    - **Alternatives rejected:** 8 GB (saves about $65-75, loses on-device training and the Lime path).
  3.
    - **Question:** C3: Pack 3S or 4S?
    - **Decision:** 4S1P P50B (72 Wh) with a regulated 12 V rail into J21.
    - **Reason:** Physics: the 13.2 V LNB, the 12.5 V Boni-Whip LDO and AUX 12 V need input above about 12.9 V. 3S would need boosts and their spurs. Outside this lens; I agree with the register.
    - **Consequences:** labpowerd, the RP2040 hard cut and the TPS2553/eFuse ratings use one 4S threshold table. The SMBJ14A goes after the regulator.
    - **Alternatives rejected:** 3S (budget only).
  4.
    - **Question:** C4: 12 V regulator for J21?
    - **Decision:** A forced-PWM buck-boost rated 5 A or more is preferred. The D36V50F12 is allowed only with its EN hardware cut at 13.4 V or above. Make the final choice after the terminated-floor A/B and the sealed-case current test.
    - **Reason:** The D36V50F12 drops out below 13.3 V and uses light-load PFM. Interface point: its EN must be driven by the always-on RP2040 or BMS logic, never by a Q6A GPIO.
    - **Consequences:** The part number is set in sourcing (P2/P5).
    - **Alternatives rejected:** 9 V into J21 (the TVS reading behind it was wrong).
  5.
    - **Question:** C5: Final USB port map, including the IMU and HMI interfaces?
    - **Decision:** J5 bottom (blue, USB0): RTL-A without the Lime, T7 with it. J5 top (FE1.1s P1): RTL-B. J2a (P2): touch HID. J2b (P3): Adafruit CH334F MTT, powered from LAB 5 V with upstream VBUS used only for sensing. Its ports: H1 for the HMI RP2040 only if UART7 fails (otherwise spare, or the FT232RL GNSS fallback); H2 for RTL-A with the Lime (otherwise spare, or a 4th V4L); H3 for LAB USB-A through a TPS2553 at 0.6 A in field mode; H4 for the HF+ behind an MCP-switched VBUS-cut. FE1.1s P4 stays the Wi-Fi/BT module, unbound in QUIET. Off USB: the IMU puck uses UART to the HMI RP2040, the HMI RP2040 uses UART7 (official overlay, pins 32/29), the GNSS uses UART6, the INA228 uses I2C0 and the expanders use I2C2.
    - **Reason:** It fits all four combinations (Lime yes/no x UART7 ok/fail) with zero overflow. Load is about 8-13 MB/s on the FE1.1s uplink against 35-40 MB/s practical. Each pair of ports shares a 2.1 A WS4612 with ample margin. No USB full-speed edges sit at the antenna boom.
    - **Consequences:** The IMU firmware relays through the HMI MCU. udev names devices by port path plus serial.
    - **Alternatives rejected:** IMU puck as USB-CDC (needs a 5th port in the worst case; USB edges at the antenna). T7/instrument time-sharing of the blue port (lab_ui_hf; means re-plugging the only SuperSpeed port). A 7-port hub (more clocks and power for no need). Display RP2040 on H1 as the only link (unpowered while the Q6A is off).
  6.
    - **Question:** C6: 40-pin header and bus map, including fan control?
    - **Decision:** Use the header table in budget_tables:
  - PPS: pin 7 (GPIO96, UM3304, bias-disable).
  - Console: pins 8/10.
  - I2C0 13/15: INA228.
  - UART6 16/18: LC76G.
  - I2C2 27/28: MCP #1 0x20, TCA9535 0x24, TCA9517 to the LAB BUS (sled MCP #2 0x21, ADS1115 0x48, optional RP2040 counter 0x30).
  - UART7 32/29: HMI RP2040.
  - Pin 3: INA228 ALERT. Pin 5: TCA9535 INT.
  - Pins 12/35/38: RP2040 SWCLK/SWDIO/RUN. Pin 40: safe-boot.
  - No safety enables on any header pin.
  Fan: 25 kHz PWM from the HMI RP2040, going to 100% when the heartbeat is lost. Fallback: pin 33 (GPIO56, the same pin as the PoE-HAT overlay) through a 74LVC1G17 and a 2N7002, with spi14 disabled. Build one combined lab-q6a.dtso on top of Radxa's uart6, uart7, i2c0 and i2c2 overlays, and check debugfs pinmux-pins shows one owner per pin.
    - **Reason:** Each function is matched to the translator type behind its pin. Open-drain lines go to UM3204H or CJ3134K pins; push-pull and short lines to UM3304 pins. A 1 kHz fan comb would hit 40 and 60 kHz exactly; 25 kHz does not.
    - **Consequences:** Register decision 17's 'fan pin conflict' is closed as a false conflict. power.json's i2c6 placement is deleted.
    - **Alternatives rejected:** Header GPIOs for bias, LNB or relays (undefined power-up state behind UM3304). The BNO085 directly on I2C2. pwm-gpio at 1 kHz.
  7.
    - **Question:** C7: Hardware ownership and process architecture (rflab, lab-sched and the npu daemons)?
    - **Decision:** One owner per resource:
  - labd: I2C2 (MCP #1, TCA9535, sled), all enables (bias, LNB, Boni-Whip, AUX, LAB VBUS, VBUS-cuts, HF+ selector, noise source in BENCH), SDR leases and modes, scheduler, profiles, policy, rfkill/unbind, instruments. radio_lab's rflab and lab-sched become labd modules, with labctl as their CLI.
  - labrx: the only SDR opener in labrx mode (sdr-ingestd, spectrumd, recorderd, lab-rec and lab-sweep merged in). It holds the single RAM ring, the recorder, FFT/tiles and the NPU tap.
  - labclassify: inferd-htp, inferd-cpu, fusiond, annotd and npu-health. modeld/trainer run as a transient unit started by labd between passes.
  - labpowerd: I2C0/INA228 and KEY_POWER.
  - labinput: UART7.
  - gpsd: UART6. Kernel: pps-gpio on GPIO96 and the fan fallback.
  Engine-exclusive leases run with per-unit DeviceAllow.
    - **Reason:** Removes the double-open blocker, the two rings, the two recorders and the advisory flocks. Gives cgroup-enforced leases.
    - **Consequences:** Passes are record-then-decode by default; live SatDump only as Expert. NPU teaching works on labrx-mode SDRs only.
    - **Alternatives rejected:** sdr-ingestd as permanent owner (readsb, auto_rx and OpenWebRX+ open devices themselves). Per-SDR flocks (advisory). A separate Python rflab daemon (second owner of I2C2).
  8.
    - **Question:** C8: LNB supply?
    - **Decision:** A dedicated 13.2 V ±0.2 V with true output disconnect, switched by a part rated 20 V or more. EN from MCP #1 GPB0, fault into the TCA9535. One current limit, set at 1.5-2x the measured Bullseye draw. No 18 V branch.
    - **Reason:** The QO-100 NB downlink is vertical. The TPS2553 is rated only 2.5-6.5 V, per TI.
    - **Consequences:** The lab_ui_hf arbiter resource 'LNB 13.4/18.2 V' becomes 'LNB 13.2 V'. The rf_frontend, foldable and power.json leftovers are deleted.
    - **Alternatives rejected:** A switchable 13.4/18.2 V boost. A 12 V rail through a tee (10.6-11.4 V at the LNB).
  9.
    - **Question:** C9: LNA bias rule?
    - **Decision:** Each SAWbird+ gets its own TPS2553 at 250-300 mA, fed from a 1 A low-noise LNA rail, with EN on MCP #1 and FAULT on the TCA9535. The V4L tee is used only for LNAs of 80 mA or less, and only through the librtlsdr LAB_BIAS_OK gate.
    - **Reason:** SAWbird+ parts draw 170-180 mA. A software path to the tee must not bypass the DC-safety interlock.
    - **Consequences:** The rf_frontend 100-160 mA PTC rule and the 'GOES+ on the tee' allowance are deleted.
    - **Alternatives rejected:** A polyfuse in each feed (nuisance trips). Unrestricted rtlsdr_set_bias_tee.
  10.
    - **Question:** C10: FM filter?
    - **Decision:** Nooelec Flamingo+ FM, fitted permanently in the 137/145 MHz path.
    - **Reason:** Its 250 mA DC pass is published, so the LNA injector topology still works. Outside this lens; I agree with the register.
    - **Consequences:** Measure DC pass on arrival.
    - **Alternatives rejected:** RTL-SDR Blog band-stop (no published DC rating).
  11.
    - **Question:** C11: librtlsdr build?
    - **Decision:** Rebuild noble 2.0.1-2build1 with 0204c9c (R828S) and 65f0658 (USB hang), plus the zerocopy typo fix and a new bias-tee gate patch. Keep the .so.2 SONAME, apt-mark hold it, and blacklist dvb_usb_rtl28xxu. Delete Recipe 2 (purge plus fork) and Recipe 3 (2.0.3 .so.0), including npu_training's 2.0.3.
    - **Reason:** Keeps every librtlsdr2 consumer working and closes the bias interlock gap.
    - **Consequences:** First arm64 build on the Q6A in the W1-2 gates.
    - **Alternatives rejected:** The 2.0.3 .so.0 recipe (breaks apt consumers). The destructive purge recipe.
  12.
    - **Question:** C12: Display field mode at the kernel and UI interface?
    - **Decision:** Field EDID: 1920x1080 at about 127.9 MHz (2200x1125 totals, 51.7 Hz), loaded with drm.edid_firmware=HDMI-A-1:edid/field.bin from the initramfs, with video=HDMI-A-1:1920x1080@52. Run all UI tests in that mode. Bring-up only at 148.5 MHz. A 1280x800 per-profile modeset, done by labsession on a labd request, only if the 4D panel is bought.
    - **Reason:** 128.70 MHz puts its 12th harmonic at 1544.4 MHz, inside Inmarsat-C.
    - **Consequences:** labbar restarts on DRM hotplug after every modeset.
    - **Alternatives rejected:** 128.70 MHz. Native 1080p60 in the field.
  13.
    - **Question:** C13: Kernel hold vs PPS?
    - **Decision:** Build pps-gpio out of tree as a +labN DKMS deb for 6.18.2-4 (CONFIG_PPS=y), using the lab overlay node on GPIO96. Drop Route B. The Route A fallback is written on the GPIO v2 ioctl with realtime timestamps. Build pps-ldisc only if the FT232RL fallback is used.
    - **Reason:** Keeps the HDMI/NPU kernel hold. libgpiod 1.6.3 cannot request realtime event timestamps.
    - **Consequences:** Confirm with chronyc sourcestats in W1-2.
    - **Alternatives rejected:** Kernel 7.0.11 for PPS.
  14.
    - **Question:** C14: INA228 bus and driver?
    - **Decision:** I2C0 (pins 13/15, MOSFET shifter), user-space i2c-dev with no DT binding. labpowerd is its only owner. Shunt in the pack lead. ALERT to pin 3. Breakout pull-ups removed. The RP2040 measures pack voltage on its own ADC.
    - **Reason:** A bound ina238 driver would block CHARGE access. This also avoids multi-master on I2C0.
    - **Consequences:** Fix power.json (i2c6) and npu_training ('on the J21 rail').
    - **Alternatives rejected:** I2C6 (shares SE6 with UART6). The hwmon driver.
  15.
    - **Question:** C15: Antenna tiers?
    - **Decision:** Two tiers: always-carried patch/chip/small antennas, plus a foldable backpack kit. The LRPT default is the V-dipole; the crossed Yagi defaults to the ultra-compact build; strike every loop. Outside this lens; I agree with the register.
    - **Reason:** user_requirements.md lines 10-11.
    - **Consequences:** labd profiles carry a DC-safety flag per antenna: 9:1 balun and hairpin = DC short, bias locked off.
    - **Alternatives rejected:** The small_antenna_stack single-tier rule (superseded).
  16.
    - **Question:** C16: Receive-only and policy leftovers?
    - **Decision:** Strike every item listed in register conflict 16. Also remove QSSTV, audit the direwolf config, implement the Artemis stop and the Bluetooth rfkill/unbind in labd and labclassify, and extend the policy audit to qsstv, direwolf TX directives, amarisoft plugin .so files and bias options in engine configs.
    - **Reason:** Hard rules 1-2 and delegated decisions in user_requirements.md lines 31-37.
    - **Consequences:** radio_lab P20 fldigi steps move to SDRangel channels.
    - **Alternatives rejected:** Keeping TX-capable apps 'unconfigured'.
  17.
    - **Question:** C17: HF antenna chain and HF+ input selector?
    - **Decision:** Boni-Whip at 12.5 V from an LDO on 4S, EN on MCP #1 GPB1. The 9:1 wire is for HF only; LF time signals use the active whip. The HF+ selector is two latching, DC-capable signal relays (HF bulkhead, VHF bus, 50 ohm) driven from MCP #1 through a driver, with state read back on the TCA9535. Part TBD; budget about $15-30 (unverified). Ask the user to confirm the HF-loop removal.
    - **Reason:** The AIS-on-HF+ default depends on the selector, and relay coils cannot hang off the header.
    - **Consequences:** Add the selector to the HF BOM and lab totals.
    - **Alternatives rejected:** HMC241 (its DC blocks hurt LF). 'Connect X' prompts as the default.
  18.
    - **Question:** C18: Storage without the T7?
    - **Decision:** T7 only with the Lime, on the blue port. Otherwise UFS with one root plus a 6 GB rescue rootfs (about 66-74 GB left for IQ), and a V30/A2 microSD for snapshots, offline bundles and raw overflow. Retention: products by default, raw only when pinned. HF+ recorded as ci16.
    - **Reason:** No-Lime streams top out at 13.3 MB/s, far below UFS and microSD write speeds. An A/B root would halve raw-IQ space.
    - **Consequences:** lab-snap and update bundles move off the T7.
    - **Alternatives rejected:** A/B root on 128 GB UFS. Buying the T7 regardless.
  19.
    - **Question:** C19: CPU allocation and RT priorities?
    - **Decision:** CPU0-3 (A55): UI, daemons, labclassify (HTP host and CPU fallback). CPU4-6 (A78), plus CPU7 when there is no Lime: labrx and engines; the trainer runs as a transient unit (AllowedCPUs=4-6, nice 19, CPUQuota=250%) between passes only. With the Lime: CPU7 isolated (isolcpus/nohz_full/rcu_nocbs=7, irqaffinity=0-6), lime:Rx0 at FIFO 10.
    - **Reason:** Matches the verified training estimate (4.5-10.8 min on the A78 cores) and Lime's warning about RT throttling.
    - **Consequences:** Fix the lab_ui_hf trainer-on-A55 text and npu_training's FIFO 50.
    - **Alternatives rejected:** FIFO 50/70 for ingest. The trainer on the A55 cores.
  20.
    - **Question:** C20: UI and NPU roadmaps?
    - **Decision:** NPU Phase 0 runs inside the W1-2 gates (19 Oct-1 Nov 2026). A minimal labeller moves into P0b. Add the HF-F and second-RTL profiles before exposing HF classes. Ship the CPU-mode tile schedule (about 5 tiles/s). The HTP gate scales with the SDR set: p99 of 11.7 ms or less with the Lime, about 28 ms or less without.
    - **Reason:** CPU mode (4-6 tiles/s) cannot cover 14.6-17.6 tiles/s without the Lime.
    - **Consequences:** The UI shows reduced coverage until the HTP is promoted.
    - **Alternatives rejected:** One fixed 11.7 ms gate regardless of load.
  21.
    - **Question:** C21: V4L count?
    - **Decision:** Buy 3: RTL-A and RTL-B in service plus 1 spare. Continuous ADS-B/AIS/sonde monitoring time-shares (AIS on the HF+). A 4th V4L only if the user wants 24/7 monitors; it fits on CH334F H2 (no Lime) or the LAB port.
    - **Reason:** USB slots exist without the Lime; the stock of R828S units is finite.
    - **Consequences:** Unique EEPROM serials; udev by serial.
    - **Alternatives rejected:** A single V4L (the lab_ui_hf count).
  22.
    - **Question:** C22: Software recipes and pinning?
    - **Decision:** One venv per tool:
  - NanoVNA-Saver via pipx; QtTinySA with PySide6 6.12; lab venv on numpy<2.
  - libgpiod v1 API in labd; Skyfield 1.55 and sgp4 2.27 from pip.
  - SatDump 2.0-alpha and SDR++/SDRangel from source as +labN debs.
  - OpenWebRX+ 1.2.126 with --no-install-recommends, exact-name -1 pins, mirrored into aptly.
  - Hold Mesa 25.2.8-0ubuntu0.24.04.4 and libdrm 2.4.125 plus the register hold list.
  - Purge brltty, mask ModemManager, mask apt and fwupd timers.
    - **Reason:** Resolves every recipe conflict and the Mesa ambiguity, and removes serial-port hijackers.
    - **Consequences:** Each tool is tested on the Q6A within the return window.
    - **Alternatives rejected:** apt nanovna-saver 0.6.3. Skyfield 1.48 from apt. Unmirrored PPA installs.
  23.
    - **Question:** C23: Region unknown?
    - **Decision:** Hold the region-dependent purchases (LNB, horn, SAWbird+ iO, LC76G vs MAX-M10S). labd computes GEO 'visible from here' flags from the GNSS fix and gates dump978, nrsc5 and EAS per region profile. Outside this lens; I agree with the register.
    - **Reason:** Visibility and legality depend on the region.
    - **Consequences:** Ask the user at the phase end.
    - **Alternatives rejected:** Buying for Europe by default.
  24.
    - **Question:** C24: Costs and weights?
    - **Decision:** Recompute with the corrected lines and add an internal-interface delta, an estimate of about $12-25:
  - TCA9535;
  - 2x 74LVC1G17;
  - a relay driver;
  - a 1 A LNA LDO;
  - 2 load switches for display and LAB EN;
  - optional RS-485 pair.
    - **Reason:** These parts come out of this lens; their prices are unverified.
    - **Consequences:** Fed into P5 (cheapest analogs).
    - **Alternatives rejected:** None.
  25.
    - **Question:** C25: P1b completion?
    - **Decision:** Closed. final/report_research.json exists (minute-log 04:52). STACK.md and build/ do not exist yet, which I checked; P2 is running.
    - **Reason:** File present and read in this step.
    - **Consequences:** Only the summaries.md and minute-log.md errata blocks remain.
    - **Alternatives rejected:** None.
- **Checks passed:**
  - Schematic v1.21 (local text): FE1.1s U23 sits on the SoC's USB1 (HS only). P1 goes to J5 top, P2/P3 to the J2 dual USB 2.0 stack, P4 to the FCU760K Wi-Fi/BT. The blue USB 3.1 is J5 bottom on USB0 (HS plus SS). This settles the J5 labelling: rf_frontend's 'J5 lower USB 2.0' is wrong, and narrowband's reading is right.
  - VBUS: U35 WS4612 feeds both J5 ports; U33 feeds both J2 ports. Each limits at about 2.1 A (Ilim = 6800/3.24 kOhm), and each limit is shared by two ports. No-Lime USB load is about 0.54 A on U35 and about 0.1 A on U33.
  - The FCU760K is the module and the AIC8800D80 (a69c:8d80) the chipset inside, so both names in the files are right.
  - USB bandwidth: the FE1.1s uplink carries 8.2 MB/s without the Lime (12.2 with the LA at 4 MS/s) and 13.3 MB/s with it (17.3), against 35-40 MB/s practical. The T7 at 224 MB/s uses about 57% of the 395 MB/s measured on the blue port.
  - Hub depth: root, FE1.1s, CH334F, bench hub is 3 hubs, within the USB 2.0 limit of 5. The CH334F is MTT, so full-speed instruments get their own TT; Adafruit 5997 costs $4.95 and is in stock.
  - VCC_5V_PERI (about 17 W): about 4.2 W without the Lime. With the Lime it is about 10 W typical, and about 16.5 W worst case at the 8.25 W M.2 spec limit, which is within the limit but tight.
  - Header translators: I2C0 (13/15) uses CJ3134K MOSFET shifters, correct for I2C. I2C2 (27/28) and the console share U47, a UM3204H (TXS-type, I2C-capable). UART6 and I2C6 use U48 (UM3204H). PPS pin 7, UART7, SPI12/14 and MI2S use UM3304 (TXB-type). This is consistent with gnss_imu.
  - UART6 and I2C6 share QUP0 SE6 (GPIO24-27), so I2C6 is unusable once UART6 is on; the register's correction of power.json holds.
  - The UART7 overlay exists upstream: qcs6490-radxa-dragon-q6a-uart7.dtso, TX on pin 32 and RX on pin 29, exclusive spi7/uart7/i2c7/gpio30/31. Upstream also has i2c0, i2c2, uart6, poe-hat and spi14 overlays.
  - GPIO56 is FP_SPI_MISO, which is header pin 33 (QUP1 SE6, spi14). The fan-pin conflict in the register is the same physical pin.
  - Kernel 6.18.2-4 (local config): CONFIG_PPS=y; PPS_CLIENT_GPIO and PPS_CLIENT_LDISC not set; PINCTRL_MCP23S08 not set; GPIO_PCA953X=y; I2C_CHARDEV=y; HIDRAW=y; PWM_GPIO=m; ina238.ko carries the ina228 alias. All register statements agree.
  - LimeSuiteNG 37cb183 (16 Oct 2026, limesdr-micro-staging) contains limeConfig --refclk and --refclk_source (cli/limeConfig.cpp lines 28-29, 98-99), which closes the radio_lab open question 'is 37cb183 new enough'. Its debian/rules sets BUILD_PLUGINS_AMARISOFT=FALSE, while the CMake default is ON, so source builds must pass the flag.
  - TPS2553 (TI): 2.5-6.5 V input, 75-1700 mA adjustable limit, 925-1075 mA at the 1 A setting. Suitable for the 250-300 mA LNA feeds and the LAB port; unsuitable for the LNB or 12 V rails, which confirms the register.
  - MCP23017 GPA7/GPB7 are output-only in current datasheet revisions (D/E), which confirms radio_lab's from-memory note.
  - I2C address plan has no collisions: INA228 0x40 on I2C0; MCP #1 0x20, MCP #2 0x21, TCA9535 0x24, ADS1115 0x48 and RP2040 counter 0x30 on I2C2. The VEML7700 (0x10) sits on the RP2040's own bus.
  - NPU duty without the Lime: about 17.6 tiles/s x 11.7 ms = 21%, under the 50% cap. With the Lime, 42.5 tiles/s holds at the 11.7 ms gate (verified).
  - Receive-only guard elements are consistent across lab_ui_hf, radio_lab and the register: Amarisoft plugin off, Lime TX terminated, sink-block and SOAPY_SDR_TX lint, SDRangel TX/DSD audit, jt9/wsprd only, the -1 pin list, URH rejected.
  - labclassify CPUAffinity=0-3 in lab_ui_hf final; the earlier 4-6 contradiction is already fixed there.
  - The Q6A USB-C stays blocked (Q5 back-feed), and the IP2368 USB-C is the only external power input; all files agree.
- **Budget tables:**
  - USB PORT MAP (schematic v1.21)
  | Port | VBUS | No Lime | Lime + T7 |
  |---|---|---|---|
  | J5 bottom, blue USB0 (HS+SS) | U35 2.1 A, shared with J5 top | RTL-A | T7 |
  | J5 top = FE1.1s P1 | U35 | RTL-B | RTL-B |
  | J2a = P2 | U33 2.1 A, shared with J2b | touch HID | touch HID |
  | J2b = P3 | U33 (CH334F senses VBUS only) | CH334F MTT | CH334F |
  | H1 | LAB 5 V | spare (HMI RP2040 if UART7 fails) | same |
  | H2 | LAB 5 V | spare / 4th V4L | RTL-A |
  | H3 | TPS2553 0.6 A | LAB USB-A | LAB USB-A |
  | H4 | VBUS-cut | Airspy HF+ | HF+ |
  | P4 internal | WIFI_PWR_EN | FCU760K, unbound in QUIET | same |
  | Off USB | - | GNSS UART6; HMI UART7; IMU UART to HMI; INA228 I2C0; expanders I2C2 | same |
  - USB BANDWIDTH (MB/s)
  | Link | No Lime | Lime + T7 | Capacity |
  |---|---|---|---|
  | USB0 blue | RTL-A 5.12 | T7 224 (56 Msps ci16) | 395 measured |
  | FE1.1s uplink | RTL-B 5.12 + HF+ 3.07 = 8.2 (12.2 with LA at 4 MS/s) | 2 RTL + HF+ = 13.3 (17.3) | 35-40 practical |
  | Rule | Wi-Fi unbound during jobs; at most 3 continuous streams | same | - |
  - 5 V / VBUS CURRENT (estimates; HF+ unpublished)
  | Rail | Loads | Typical | Worst at the limits | Limit |
  |---|---|---|---|---|
  | U35 (J5 pair) | 2x V4L 0.27 A (+ tee 0.18 A each, normally off) | 0.54 A | 0.9 A | 2.1 A |
  | U33 (J2 pair) | touch about 0.1 A | 0.1 A | 0.2 A | 2.1 A |
  | VCC_5V_PERI, no Lime | USB, fan, HDMI, misc | 4.2 W | 5.5 W | about 17 W |
  | VCC_5V_PERI, Lime | + T7 0.9 A, Lime 4 W (spec 8.25 W) | about 10 W | about 16.5 W | about 17 W |
  | LAB 5 V | CH334F 0.08, HF+ 0.15-0.3, 3 LNAs 0.41, LAB instrument 0.3 | about 1.0 A | 2.2-2.4 A (register settings) | fuse 2 A, change to 3 A |
  | LNA rail | NOAA 0.17 + GOES 0.18 + LNA V2 about 0.06 A | 0.41 A | 0.9 A | LT3045 0.5 A, change to a 1 A part |
  - 40-PIN HEADER MAP
  | Pin | Signal (translator) | Use | Owner |
  |---|---|---|---|
  | 7 | GPIO96 (UM3304) | PPS in, wire 20 cm or less | kernel pps-gpio |
  | 8/10 | debug UART (UM3204H) | console | reserved |
  | 13/15 | I2C0 (CJ3134K) | INA228 0x40 | labpowerd |
  | 16/18 | UART6 (UM3204H) | LC76G | gpsd |
  | 27/28 | I2C2 (UM3204H) | MCP #1, TCA9535, TCA9517 to LAB BUS | labd |
  | 32/29 | UART7 TX/RX (UM3304) | HMI RP2040, 20 cm or less | labinput |
  | 3 | GPIO24 (UM3204H) | INA228 ALERT | labpowerd |
  | 5 | GPIO25 (UM3204H) | TCA9535 INT | labd |
  | 12/35/38 | UM3304 | RP2040 SWCLK/SWDIO/RUN | OpenOCD (service only) |
  | 40 | UM3304 | safe-boot from RP2040 | early unit |
  | 33 | GPIO56 (UM3304) | fan fallback via 74LVC1G17 + 2N7002 | kernel pwm-fan |
  | 11, 31, 19-26, 22, 36, 37 | UM3304 | spare (spi12/spi14 disabled) | - |
  - EXPANDER LINES (labd)
  | Device | Lines |
  |---|---|
  | MCP23017 #1 0x20, outputs only (Q6A 3.3 V; power-up high-Z, 100k pull-downs) | GPA0 LAB EN, GPA1 AUX EN, GPA2 RTL-A cut, GPA3 RTL-B cut, GPA4 HF+ cut, GPA5-7 LNA VHF/UHF/L EN; GPB0 LNB EN, GPB1 Boni EN, GPB2-3 selector relays, GPB4 sled power, GPB5-7 spare |
  | TCA9535 0x24, inputs (pca953x) | 4x TPS2553 FAULT, LNB fault, Boni fault, 2x DC-sense, 2x selector readback, sled present (11 of 16) |
  | Sled MCP23017 #2 0x21 | switch V1-V3, PE4302 D0-D5, NOISE EN (BENCH), LNA EN |
  - HMI RP2040 GPIO (30 available)
  | Function | GPIO |
  |---|---|
  | 2 push-encoders | 6 |
  | 6 keys | 6 |
  | I2C (VEML7700) | 2 |
  | UART0 to Q6A, UART1 to puck | 4 |
  | backlight PWM, piezo, WS2812 | 3 |
  | power button, J21 pin 3, hard cut, safe-boot, H1 VBUS sense | 5 |
  | ADC: backlight NTC, pack divider, case NTC | 3 |
  | fan PWM | 1 |
  | Total | 30 (31 with fan); use a key matrix or RP2350B |
  - RAM, 12 GB board (about 11 GiB visible, unverified; model)
  | Consumer | GiB |
  |---|---|
  | OS, labwc, XWayland, labbar | 0.8 |
  | Lab Shell + QtWebEngine | 0.4-0.9 |
  | labd, labpowerd, labinput | 0.15-0.25 |
  | labrx without ring | 0.1-0.2 |
  | engines (SatDump post-pass, sdrangelsrv, OWRX+, readsb/AIS/auto_rx) | 1.0-2.6 |
  | labclassify (HTP 1.0 max, CPU 0.3, fusion 0.2) | 1.5 |
  | headroom | at least 1.0 |
  | Subtotal without trainer | 5.0-7.2 |
  | trainer (between passes only) | up to 2.0 |
  | Ring | 1.5 no Lime; 4 Lime with trainer; 6 Lime without trainer |
  - CPU (estimates; unmeasured)
  | Cores | Load |
  |---|---|
  | CPU0-3 A55 | UI 0.5-1 core; daemons 0.2; stage-2 0.3-0.5; CPU-mode detector about 1-2 cores at 5 tiles/s |
  | CPU4-6 A78 (+CPU7 without Lime) | labrx ingest/FFT for 2 RTL + HF+ under 0.3 core; SatDump LRPT 0.3-0.5, HRPT 1-1.5; SDRangel HF 0.3-0.6; readsb 0.3-0.5; OWRX+ 0.5-1; trainer T2 3 cores between passes |
  | CPU7 (Lime only) | isolated, lime:Rx0 at FIFO 10 |
  | GPU | VkFFT about 7.8 GFLOPS, about 1% of 808 |
  - STORAGE (MB/s and GB/h)
  | Stream | Rate |
  |---|---|
  | V4L cu8 2.56 Msps | 5.12 MB/s = 18.4 GB/h |
  | HF+ ci16 768 ksps | 3.07 MB/s = 11 GB/h (cf32 6.14 MB/s = 22 GB/h) |
  | 2 RTL + HF+ ci16 | 13.3 MB/s = 48 GB/h |
  | Lime 56 Msps ci16 | 224 MB/s, T7 only (about 74 min per TB) |
  | UFS left for IQ: one root + 6 GB rescue + 20 GB dataset | about 66-74 GB, about 1.4-1.5 h worst case |
  | With A/B root | about 50-58 GB (rejected) |
  - NPU TILE LOAD
  | SDR set | Tiles/s | HTP gate (50% duty) | CPU mode |
  |---|---|---|---|
  | Lime + RTL | 42.5 (verified) | p99 of 11.7 ms or less | far short |
  | 2x V4L | 14.6 (verified) | about 34 ms | about 5 tiles/s with schedule |
  | 2x V4L + HF-F | about 16.6-17.6 (model) | about 28 ms | about 5 tiles/s with schedule |
  - RESOURCE OWNERS
  | Resource | Single owner |
  |---|---|
  | SDR open (labrx mode) | labrx |
  | SDR open (engine-exclusive lease) | that engine unit, with DeviceAllow |
  | Leases, scheduler, all enables, I2C2, rfkill/unbind | labd |
  | I2C0 INA228, KEY_POWER | labpowerd |
  | UART7 (keys, encoders, IMU relay, heartbeat) | labinput |
  | UART6 GNSS | gpsd |
  | GPIO96 PPS | kernel pps-gpio |
  | HTP/CPU inference | labclassify |
  | RAM ring, recorder, FFT tiles | labrx |
- **Notes:** The stack can work as one device. Before STACK.md, these cross-file decisions have to be frozen: one SDR-opening model, one RP2040 for HMI and supervisor, all safety enables on I2C expanders (not header GPIO), a librtlsdr bias-tee gate, the IMU always on UART to the HMI MCU, the LAB 5 V budget, a CPU-mode NPU schedule, and one RAM ring table. One blocker: the SDR double-open conflict between npu_training's sdr-ingestd, the lab_ui_hf engine leases and the radio_lab flocks. All 25 register conflicts get a decision (C1-C25). Out-of-lens items (pack, FM filter, antenna tiers, region) follow the register, with their interface consequences added.
  
  Two local findings settle register items:
  - The 'fan pin GPIO56 vs pin 33' conflict is the same physical pin.
  - The audited LimeSuiteNG pin 37cb183 already has limeConfig --refclk.
  
  Web use: 3 WebSearch, 6 WebFetch (one returned 403).
  - Verified: the radxa-overlays listing (uart7, i2c0, i2c2, poe-hat overlays exist) and the uart7 .dtso pins; TI TPS2553 range and accuracy; the MCP23017 GPA7/GPB7 output-only change; Adafruit CH334F basics (no per-port power information).
  - Not found: HF+ Discovery current (RigPix lists it as unknown; the rtl-sdr.com table is only in a video).
  
  Model or unverified numbers: RAM and CPU budgets, LAB 5 V typical draw, HF-F tile rate, UFS free space and the interface parts cost; the UM3304/UM3204H types come from gnss_imu's datasheet reading and my schematic parse; ModemManager/brltty presence on Radxa OS r2, 0483:5740 on the LiteVNA, AO3400 gate capacitance, libgpiod v1 timestamp clock, PMIC long-press timer and the D36V28F5 3.2 A rating.
  
  Files: calculations in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/iface/budget.py; decision dumps in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/iface/decisions.txt and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/iface/verdict.txt; schematic text at /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_sch/q6a_sch.txt (USB sheet lines 4330-4610, header lines 3600-3940).

## integration:lens3 (run `wf_221684d9-b6c`)

- **Lens:** RF CHAIN + COEXISTENCE. I traced the RF path for every target in both antenna tiers (antenna, filter/LNA, injector, selector, SDR) and checked the bias-tee rules, the FM band-stop, the LNB feed, the HF wire and active whip, and the HF+ selector and shielding. I scanned harmonics and combs against every signal window in use: display pixel and DSI clocks, PCIe refclk and onboard Ethernet, SoC/hub/RP2040/V4L/GPSDO/Lime clocks, USB3, bucks, PWM, USB frame rates and the display line rate. I also reviewed the noise-floor A/B plan and the receive-only guards. Constraints: Q6A held, receive-only, no loops, world prices.
- **Issues:**
  1.
    - **Area:** Noise-floor A/B / acceptance method
    - **Components:**
      - radio_lab P4 terminated-floor audit
      - display RF A/B acceptance
      - lab_ui_hf HF noise A/B
      - small_antenna_stack first_tests
      - foldable build step 9
      - LC76G
    - **Problem:** Every coexistence decision (12 V regulator, display clock, Ethernet, hub, fan, charger) defers to the A/B test, but the A/B as written cannot see the spurs that hurt narrowband targets. P4 sweeps with rtl_power at 100 kHz bins, and the display test passes on a broadband '1-2 dB rise' in 5 windows. With NF 5 dB the floor is -119 dBm per 100 kHz bin, against -152 dBm in a 50 Hz CW/beacon filter (model). A CW line at -158 dBm costs about 1 dB on a QO-100 CW beacon, an Inmarsat-C 1200 sym/s carrier or an H1 channel, yet it sits about 39 dB below the 100 kHz bin floor. It is invisible. Further gaps: (a) four separate A/B plans with different band lists, none covering ADS-B, AIS, sondes, H1, Inmarsat-C 1537-1545 or GNSS together; (b) the HF A/B (0.1/0.5/1/5/10/20 MHz) skips the LF carriers 40/60/77.5/162 kHz and NAVTEX 490/518/4209.5 kHz; (c) the GNSS pass mark uses u-blox UBX-MON-RF, which the LC76G does not have; (d) no states for HDMI link off vs backlight off, pcie0/Ethernet, fan PWM vs DC, USB traffic, LNB/LNA/Boni rails, or a closed case at temperature.
    - **Severity:** major
    - **Evidence:** radio_lab.final.procedures[4] step 1 ('rtl_power -f 24M:1766M:100k -g 40 -i 10 -e 120'); display_market.final.acceptance_tests[8] ('Pass: 1-2 dB or less rise', windows 130-150/430-440/735-755/1685-1715/2200-2300, 'u-blox UBX-MON-RF'); lab_ui_hf.final.hf_receiver.setup[8]; small_antenna_stack.final.first_tests[0]; register #82 (LC76G has no MON-RF). Floors from my model: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/stage.py.
    - **Fix:** Replace all four with one matrix (budget table 'A/B matrix'). Per used signal window: 60 s of IQ at 2.4 Msps, FFT 2^20 (2.3 Hz bins), Welch-averaged; flag every line 6 dB or more above the local floor. HF+: terminated, then on each antenna, at 40/60/77.5/162/490/518/4209.5 kHz with 1 Hz RBW. GNSS: GSV mean C/N0 of the 8 strongest SVs, plus GNSS-SDR C/N0 on a V4L. Run lid closed after a 30 min warm soak. Pass: no line 3 dB or more above the floor inside any used signal window; broadband rise of 0.5 dB or less inside windows; GNSS change of 1 dB-Hz or less. Output: a versioned spur mask (freq, width, source) consumed by SatDump wrappers, auto_rx, the NPU labeller and the UI.
    - **Fix cost:** $0; about 4-5 h per full run, 30 min for the regression subset
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/display_market.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/stage.py
  2.
    - **Area:** Board clocks: onboard Ethernet on pcie0
    - **Components:**
      - Q6A RTL8111K/RTL8125BG footprint
      - pcie0 100 MHz refclk
      - 25 MHz Ethernet crystal
      - Meteor HRPT chain
      - GNSS L1
      - radiosondes
    - **Problem:** The 1700.000 MHz line is credited only to the Lime PCIe (register #127, P4). But the Q6A's own Ethernet controller sits on pcie0, with a 100 MHz refclk and a 25 MHz crystal. 100 MHz x17 and 25 MHz x68 both land exactly on 1700.000 MHz, the Meteor HRPT carrier centre (main lobe 1698.65-1701.35). Further lines: 25 MHz x63 = 1575.000 MHz (0.42 MHz from GPS L1, inside the C/A main lobe); 100 x4 and 25 x16 = 400.000 MHz (sonde band edge); 100 x16 and 25 x64 = 1600.0 MHz (GLONASS G1 channels -4/-3). The no-Lime build therefore still has these lines. The Bullseye's 25 MHz reference adds the same 1700.000/1575.000 lines whenever the LNB is powered.
    - **Severity:** major
    - **Evidence:** Schematic v1.21 text /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_sch/q6a_sch.txt: lines 883-937 (PCIE0_REFCLK_P/M, TX/RX), 4105-4133 (LANWAKEB, PERSTB, CKXTAL1/2, 'RTL8125BG' / '(RTL8111K)' dual footprint), 4314 ('25MHz_12PF_10ppm'); compute verify ('onboard NIC is 1 GbE RTL8111 on pcie0'); register #127 and radio_lab P4 list 1700.000 MHz only for the Lime. Harmonic scan: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/harm.py.
    - **Fix:** Add a field-image DT overlay that disables pcie0; Ethernet is not used in the field, and Wi-Fi is on USB. Keep pcie0 for home/bench boots. Add the state 'pcie0 enabled / disabled' to the A/B at 1700.000, 1575.000, 400.000 and 1600.0 MHz with narrow RBW. If the 25 MHz crystal keeps oscillating with the controller in reset and its line is 3 dB or more above the floor, copper-tape the PHY area to the mid-plate. Interlock LNB EN with the RTL-B selector so the LNB is powered only on its own path.
    - **Fix cost:** $0 (overlay and labd rule); copper tape about $2 if needed
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_sch/q6a_sch.txt
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/harm.py
  3.
    - **Area:** FM band-stop placement (conflict between final-check lenses)
    - **Components:**
      - Nooelec Flamingo+ FM
      - SAWbird+ NOAA
      - RTL-SDR Blog LNA V2
      - TPS2553 injector
    - **Problem:** The P2 power lens decided 'Flamingo+ FM ... on the SDR side of the injector'. That puts the filter after the LNA. rf_frontend's 2 m chain (b) does the same: LNA V2 at the feed, powered through the Flamingo+. The SAWbird+ NOAA is LNA-SAW-LNA, so its first MMIC, like the wideband LNA V2, sees the whole FM band unfiltered. Intermod it creates in-band cannot be removed downstream. The register rule (filter ahead of any gain; no broadband LNA ahead of the FM filter) and the completeness lens ('ahead of its LNA') are the RF-correct reading. The DC-pass concern behind the power lens's placement disappears with the correct placement: bias enters at the LNA's RF output, so no current flows through a filter on the antenna side.
    - **Severity:** major
    - **Evidence:** sat-receiver-audit/final-checks.md line 342 (power lens C10 decision) and line 190 (fix 13); rf_frontend.verify.final_recommendation.why (b) ('LNA V2 at the feed ... power it from the RTL's 4.5 V bias tee through the Flamingo+'); antennas.forums.recommendation_impact ('put the FM band-stop after the LNA'); register #96/#99; datasheet facts in rf_frontend.verify.issues[4] (first MMIC unfiltered). The Nooelec page (fetched) gives -3 dB points at 75/120 MHz, more than 60 dB rejection, 250 mA DC pass and +18 dBm maximum input. My model: 0.06-0.45 dB SNR cost at 137 MHz for 0.5-1.2 dB filter loss.
    - **Fix:** Use one rule in every file: antenna, then Flamingo+ FM, then VHF LNA at the feed, then coax, then injector (TPS2553), then selector, then RTL. Use two units, one on the 137 MHz entry and one on the 2 m entry. Delete 'SDR side of the injector', rf_frontend (b) and the antennas 'after the LNA' option. Only the Uputronics 162 AIS SAW preamp may run without it.
    - **Fix cost:** $0 (the second Flamingo+, $24.95, is already in the completeness lens)
    - **Sources:**
      - https://www.nooelec.com/store/flamingo-plus-fm.html
      - /home/user/lizbeth307/sat-receiver-audit/final-checks.md
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/rf_frontend.json
  4.
    - **Area:** HF/LF chain: common-mode path on the feed coax
    - **Components:**
      - Airspy HF+ Discovery
      - Balun One Nine v2 (9:1)
      - Boni-Whip
      - HF SMA bulkhead
      - 5-10 m RG-316/RG-174
    - **Problem:** The no-loop HF design depends on putting the feed point 5-10 m from the handheld. That only helps if the coax shield does not carry the handheld's common-mode noise out to the antenna. The files specify only 'clip-on ferrites at the receiver end'. One or two snap-on ferrites give little CM impedance below a few MHz (engineering judgement, not measured), so they do almost nothing at the LF time signals (40-162 kHz), NAVTEX 490/518 kHz or MW/160 m. For an E-field whip, the received signal is the voltage between element and shield (PA3FWM tn07), so CM noise on the shield is received directly. On this path the bucks, the display line rate, USB frame combs and fan PWM reach the Boni-Whip and the 9:1 counterpoise.
    - **Severity:** major
    - **Evidence:** lab_ui_hf.final.hf_antenna.setup[3] ('clip-on ferrites ... (a general common-mode choke)'); radio_lab lab_bom (HF antennas: '5-10 m thin coax with clip-on ferrites'); lab_ui_hf.design.hf_chain (PA3FWM quote: grounding only through the coax picks up 'much noise'); register #94/#95 (LF depends on the active whip).
    - **Fix:** Fit a two-stage coax CM choke at the HF bulkhead, on the antenna side of the Boni-Whip injector. DC still passes on the centre conductor. (a) LF/MF: about 25-40 turns of RG-316 on an FT-240-77 or a nanocrystalline core; design target 1 kOhm or more CM impedance at 60 kHz. (b) HF: 10-12 turns on FT-240-31 or a stack of 31-mix beads; target 2-5 kOhm at 1-30 MHz. Bond the bulkhead shield to the mid-plate at the entry point. Drive a ground stake or lay a counterpoise at the antenna end. Measure CM impedance conducted on the LiteVNA (shunt-through S21) before use. Turn counts are a design target, not verified.
    - **Fix cost:** About $15-30 for toroids, RG-316 and a bracket (unverified)
    - **Sources:**
      - https://www.pa3fwm.nl/technotes/tn07.html
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  5.
    - **Area:** HF+ input selector (HF / VHF / 50 ohm)
    - **Components:**
      - Airspy HF+ Discovery (single SMA)
      - selector relays
      - MCP23017 #1 GPB2-3
      - TCA9535 readback
    - **Problem:** No part is named, yet the AIS-on-HF+ default and the terminated-floor state depend on it. Latching coax relays cost $242 or more with 12/28 V coils (completeness lens). The obvious PCB RF relay, the Panasonic ARJ22A03 (2-coil latching), is listed at about $114-332 each with 10-22 week lead times and is marked NRND at one Mouser region, so it is not a hobby part. The HMC241 is rightly rejected (DC blocks hurt LF).
    - **Severity:** major
    - **Evidence:** register #93 (part TBD, missing from BOM and totals); lab_ui_hf.final.hf_receiver.setup[7]; final-checks.md line 1862; ARJ22A03 distributor search (flywing-tech $204.13 at qty 1, cytech about $114, IBS $331.75, Burklin EUR 217.60, Mouser.kr NRND).
    - **Fix:** Use two Omron G6K-2F-RF (50 ohm high-frequency DPDT PCB relays; insertion loss 0.2 dB or less, isolation 20 dB same pole and 30 dB different poles at 1 GHz, per RS listings) on a small 50 ohm CPWG board inside the HF+ can. Wire them series-shunt: the second pole of each relay drops the unselected path onto 50 ohm, which raises isolation. The de-energised default puts the HF+ on its 50 ohm load. Use the single-winding latching G6KU variant with an H-bridge only if the 100 mW hold power matters. Acceptance on the LiteVNA, conducted: 35 dB or more isolation at 162-260 MHz and 0.3 dB or less loss from 10 kHz to 260 MHz. Isolation at 162 MHz is my extrapolation from the 1 GHz figures and must be measured.
    - **Fix cost:** About GBP 43-52 for two relays (RS UK ex VAT, non-latching), plus $5-10 board and driver; about $60-80 in total
    - **Sources:**
      - https://uk.rs-online.com/web/p/hf-rf-relays/0492917?gb=s
      - https://uk.rs-online.com/web/p/hf-rf-relays/0492913P?gb=s
      - https://www.flywing-tech.com/product-detail/high-frequency-rf-relays-panasonic-electric-works-arj22a03-9cab24fc
      - https://www.cytechsystems.com/de/product/arj22a03z
      - https://www.tti.com/content/dam/tti-commons/supplier/panasonic/ecom/panasonic-rj-series-datasheet.pdf
  6.
    - **Area:** Bias-tee rule leftovers
    - **Components:**
      - RTL-SDR Blog V4L tee (4.5 V / 180 mA)
      - SAWbird+ GOES
      - SAWbird+ H1
      - SAWbird+ NOAA
      - LNA V2
      - TPS2553 injectors
    - **Problem:** Several final texts still break the rule (TPS2553 injector for every SAWbird+; V4L tee only for LNAs of 80 mA or less):
  - rf_frontend final (d) and known_problems[4]: the SAWbird+ GOES on the RTL tee 'after a 2-hour soak test'.
  - rf_frontend (b): the LNA V2 on the RTL tee through the Flamingo+.
  - radio_lab lab_bom and sweeps[2]: the SAWbird+ H1 'then the V4L (bias tee, 120 mA under the 180 mA limit)'. 120 mA breaks the 80 mA rule.
  - foldable build step 3: the SAWbird+ GOES 'powered by 5 V through its micro-USB, with a DC block'. That runs a USB power lead up to the feed and puts 5 V on the LNA's RF output.
  - rf_frontend known_problems[9]: a '100-160 mA polyfuse in each bias feed', which trips under 170-180 mA.
    - **Severity:** major
    - **Evidence:** rf_frontend.verify.final_recommendation.why (b)/(d) and known_problems_and_fixes_to_apply[4]/[9]; radio_lab.final.lab_bom (SAWbird+ H1 item) and radio_lab.sweeps[2].notes; foldable_antennas.final.build_and_test_steps[2]; register #97/#100.
    - **Fix:** Use one table in STACK.md (budget table 'Bias and RF rails'). Every SAWbird+ (NOAA 170 mA, GOES 140-180 mA, H1 120 mA, iO current unpublished) runs through an injector at the SDR end, fed by a TPS2553 at 300 mA nominal with FAULT readback. The V4L tee may power only the L-band active patch (20 mA), the LNA V2 (draw unpublished; measure it), the non-plus SAWbird GOES (30 mA) and NOAA (80 mA), and Uputronics preamps after a revision check, and only through the librtlsdr LAB_BIAS_OK gate. No micro-USB power at the feed. Delete the polyfuse rule and the soak allowance.
    - **Fix cost:** $0 (text); the injectors are already budgeted
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/rf_frontend.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
  7.
    - **Area:** 70 cm / 2 m front-end order and filter part
    - **Components:**
      - 17 cm whip / SRH-701 / A-V85
      - RTL-SDR Blog LNA V2 (QPL9547)
      - Nooelec Ham Filter Bank Barebones
      - 70 cm crossed-Yagi feed
    - **Problem:** The completeness lens found that one 2 m/70 cm entry with a 430-440 MHz BPF ahead of the LNA kills 2 m. The order is also wrong for UHF, where the external noise is low. With a BPF of 1-2 dB loss ahead of a 0.7 dB NF LNA, Te is 148-262 K, against 61-64 K with the LNA first. That costs 0.75-2.84 dB of SNR at Tant 150-400 K (my model) on links whose margins are -5.3 to +5.3 dB (1 W 9k6 CubeSats). The only purchasable 70 cm filter found is the Nooelec Ham Filter Bank Barebones ($66.95; 70 cm 420-450 MHz, 2 m 144-148 MHz). Its loss and rejection are unpublished, it is powered, and its input-bias pushbutton can put 4.5 V on a DC-shorted hairpin antenna. Its 420-450 MHz passband also passes PMR446 and 433.92 MHz ISM.
    - **Severity:** major
    - **Evidence:** final-checks.md lines 1455-1470 (completeness lens); small_antenna_stack.final.revised_stack[9]/[10] ('70 cm BPF ahead of the LNA V2'); reachable rows (CubeSat margins -5.3 to +5.3 dB); Nooelec page fetched 18 Oct 2026. Model: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/stage.py.
    - **Fix:** Use separate entries. 70 cm: whip or Yagi, then LNA V2 at the bulkhead or feed, then the 70 cm filter, then injector, selector and RTL. Change to BPF first only where the P12 site survey shows the LNA V2 compressing (near cell sites). 2 m: whip or Yagi, then Flamingo+ #2, then LNA V2, then optionally the 2 m filter-bank section. General rule: at VHF the filter goes first, because sky noise dominates (0.06-0.45 dB cost); at UHF and L-band the LNA goes first. Tape over or disable the filter bank's input-bias button. Run a P2 VNA check (loss at 437 MHz, rejection at 380-400, 446, 470-790 and 791-960 MHz) before relying on it.
    - **Fix cost:** $0 beyond the completeness lens ($66.95 filter bank, $19.95 second LNA V2, $24.95 second Flamingo+)
    - **Sources:**
      - https://www.nooelec.com/store/ham-filter-bank.html
      - /home/user/lizbeth307/sat-receiver-audit/final-checks.md
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/stage.py
  8.
    - **Area:** Display field-mode clock: leftovers, tolerance and verification
    - **Components:**
      - Wisecoco 7in FHD HDMI-to-MIPI board
      - RA620 DP-to-HDMI
      - EDID override
      - labwc output config
    - **Problem:** 128.70 MHz is still in display_market (q6a_settings[3]/[4], acceptance_tests[1]/[2]), in small_antenna_stack (Wisecoco row) and in the lab_ui_hf UI tests. My scan confirms that its 12th harmonic (1544.4 MHz) falls in the Inmarsat-C NCS band, and with a 0.5% down-spread it smears over 1536.7-1544.4 MHz, the whole band. The register's 127.9 MHz is clean in all used signal windows, but its SSC-proof clean window is only 127.79-128.04 MHz (±0.1%), so the delivered clock must be measured, not assumed. The register's alternative, 164.4-168.4 MHz, puts the strongest emission (the fundamental) 2-6 MHz above AIS and on the edge of the Uputronics 162 SAW passband (158.2-165.8 MHz); 166.0 MHz also fails once 0.5% SSC is applied. Other open points: DSI clock = 3x pclk only in non-burst video mode (a burst-mode bridge sets its own lane rate); the CEA extension still advertises 148.5 MHz (VIC 16), which the compositor may pick after a hotplug; and the DP link from the SoC to the RA620 is broadband whatever the pixel clock, so only 'link off' removes it.
    - **Severity:** major
    - **Evidence:** register #77/#53 and conflict 12; display_market.final.q6a_settings[3]/[4] and acceptance_tests; my scans /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/harm.py and win.py (25 signal windows including FM, VOR, NOAA WX, DAB, UAT, Iridium carrier and HamTV; 0.5 MHz guard; strong-emission LNA/SAW passbands for n of 3 or less); radio_lab lab_bom (Uputronics 162 7.6 MHz SAW).
    - **Fix:** Field EDID with two DTDs, tried in this order. (1) 151.50 MHz, 1920x1080, H total 2200 (88/44/148), V total 1148 (27/5/36), 59.99 Hz. It is clean with SSC across a 1.6 MHz window (150.755-152.35), and its line rate of 68.86 kHz is at least 7.95 kHz from every LF carrier. (2) 127.90 MHz at 2200x1125, 51.68 Hz. Strip the CEA VIC list. Keep 148.5 MHz for bring-up only, marked non-preferred. Pin the mode in the labwc output config. Acceptance: read the actual clock (modetest, debugfs), then confirm with the tinySA or an RTL on a near-field E-probe that the 10th/11th (151.5) or 12th (127.9) harmonic is a line at the predicted frequency, not a smear. Ask Wisecoco for the bridge's DSI mode and lane rate. Update all the files together.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/harm.py
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/win.py
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/display_market.json
  9.
    - **Area:** LF/MF comb sources (time signals, SID, NAVTEX)
    - **Components:**
      - fan PWM (pwm-gpio / PoE-HAT overlay)
      - backlight dimming PWM
      - USB SOF/microframes
      - display line rate
      - IP2368 (250 kHz)
      - D36V50F12 (~500 kHz)
    - **Problem:** None of these combs is frequency-planned against the in-scope LF carriers:
  - The PoE-HAT fan overlay runs PWM at 1 kHz. Its harmonics land exactly on 40, 60, 162, 490 and 518 kHz.
  - display_market recommends 20-25 kHz backlight PWM; 20 kHz puts harmonics exactly on 40 and 60 kHz.
  - USB 1 kHz frames and 8 kHz microframes give exact integer-kHz lines (40 kHz = 5x8 kHz).
  - The display line rate at 127.9 MHz is 58.14 kHz, 1.86 kHz from MSF/WWVB 60 kHz.
  - The IP2368's 250 kHz second harmonic is 500 kHz, 10 kHz from NAVTEX 490.
  - The D36V50F12 near 500 kHz is already flagged by the power lens.
  Amplitude-only SID logging is especially exposed, because a fixed line on the carrier biases the logged amplitude.
    - **Severity:** minor
    - **Evidence:** register #17 ('PoE-HAT overlay uses 1 kHz PWM'); display_market.final.sunlight_measures[6] ('20-25 kHz PWM'); lab_ui_hf hf_capabilities (LF time signals, SID amplitude, NAVTEX); final-checks.md line 115 (power lens, D36V50F12). My calculation: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/lf.py.
    - **Fix:** Set fan and backlight PWM to 24.0 kHz; up to the 40th harmonic every line stays at least 5.5 kHz from 40/60/77.5/162/490/518 kHz. Alternatively use DC (100% duty) or analog dimming. Add an 'LF Quiet' profile in labd:
  - HDMI link off (wlr-randr --off; keys, encoders and LED stay live) and backlight off;
  - fan on DC;
  - charger unplugged;
  - LAB 5 V, Ethernet/pcie0 and the LNB/LNA rails off;
  - the HF+ is the only USB device streaming.
  SID logging subtracts a terminated-input baseline recorded in the same profile.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/lf.py
  10.
    - **Area:** Known-line list for P4 and the spur mask
    - **Components:**
      - Leo Bodnar Mini (10 MHz)
      - QCS6490 76.8 MHz XO / 19.2 MHz
      - V4L 28.8 MHz TCXO
      - CH334F/FE1.1s/RP2040 12 MHz
      - Lime 30.72 MHz (conditional)
    - **Problem:** The P4 list (144.000, 432.000, 1704.000, 1700.000, 737.28, 1689.6, 740.000, 1415.7, 1544.4 MHz) misses lines that fall inside used signal windows:
  - GPSDO 10 MHz: x142 = 1420.000 (H1), x109 = 1090.000 (ADS-B), x154 = 1540.000 (Inmarsat-C), x40 = 400.000, x169 = 1690.0, x170 = 1700.0.
  - SoC 76.8 MHz: x22 = 1689.6 (FY-2H/Elektro window).
  - SoC 19.2 MHz: x74 = 1420.8 (H1 window), x82 = 1574.4 (on the lower Galileo E1 BOC lobe), x21 = 403.2.
  - V4L 28.8 MHz: x14 = 403.2 (sondes), next to the listed 1699.2.
  - Lime 30.72 MHz: x52 = 1597.44 (GLONASS G1).
  - 12 MHz: x130 = 1560.0 (BDS B1I).
  Line amplitudes are unknown; most are high-order harmonics.
    - **Severity:** minor
    - **Evidence:** radio_lab.final.procedures[4] step 3; XO value from q6a_sch.txt line 2377 ('76.8MHZ_7PF_12PPM'); scan /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/harm.py.
    - **Fix:** Add these lines to P4 and the spur mask (budget table 'Known lines'). Keep the GPSDO off and disconnected for H1, ADS-B and Inmarsat-C sessions. Configure auto_rx to ignore 400.000 and 403.2 MHz.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/harm.py
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_sch/q6a_sch.txt
  11.
    - **Area:** LNB path: interlocks, IF level, ingress
    - **Components:**
      - Othernet Bullseye TCXO LNB
      - 13.2 V LNB rail
      - RTL-B selector (SP4T)
      - IF pad
    - **Problem:** Three gaps on the LNB path:
  - The LNB stays powered while RTL-B listens to L-band. LNB IF noise (-22 to -38 dBm integrated over about 1.2 GHz at 50-66 dB gain, my model) then leaks through the 30-37 dB isolation of the selector into the L-band path, adding about 0.4 dB of noise (model), and the LNB's 25 MHz reference adds 1700.000/1575.000 MHz lines.
  - The pad is given as 10-20 dB. At 66 dB LNB gain, 10 dB leaves about -32 dBm at the V4L, inside its 3 dB desense range (-20 to -40 dBm).
  - The 739.5 MHz IF is region-exposed: DVB-T channel 54 (734-742 MHz) where UHF TV still runs to 790 MHz, and the LTE B28 uplink (703-748 MHz) in APAC. Both can couple in through F-connector or cable ingress.
    - **Severity:** minor
    - **Evidence:** register #105 (pad 10-20 dB, noise -33 to -22 dBm, V4L desense -20 to -40 dBm); completeness-lens SP4T selectors (isolation 30-37 dB); model /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/stage.py.
    - **Fix:** labd powers the LNB only while the RTL-B selector is on the LNB port. Inject 13.2 V on the antenna side of the DC-free selector. Use a 15 dB pad as the default and 20 dB when the measured LNB gain is above 60 dB; padding costs no SNR, because LNB noise dominates. Use a double-shielded IF lead and tight F connectors. Add 'LNB on, IF terminated at the LNB' and 'LNB off' to the A/B.
    - **Fix cost:** $0 (one extra pad from the kit)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/stage.py
  12.
    - **Area:** IMU puck next to the Yagi feeds
    - **Components:**
      - BNO085 puck with RP2040-Zero
      - USB-CDC lead on the boom
      - crossed 2 m/70 cm Yagi
    - **Problem:** The pointing puck sits on the boom. Its RP2040 12 MHz crystal has harmonics at 144.000 and 432.000 MHz, close to the 2 m and 70 cm feeds. Its USB-CDC cable (12 Mb/s full-speed) runs along the boom past the driven elements. The magnetic distance rule (15-20 cm from steel and power leads) does not cover RF.
    - **Severity:** minor
    - **Evidence:** gnss_imu final (RP2040-Zero over USB-CDC); register #81 (x12 = 144.000, x36 = 432.000; on/off A/B requested); radio_lab usb_power_case_plan (H2 boom IMU puck).
    - **Fix:** Use a metal puck bonded to the cable shield, with a 31/43-mix ferrite at the puck end. Mount it on the boom rear, 30 cm or more behind the driven elements. Prefer the UART relay to the HMI RP2040, which takes USB off the boom. Add 'puck on/off' at 145.9 and 437 MHz with narrow RBW to the A/B.
    - **Fix cost:** $0-5
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/gnss_imu.json
  13.
    - **Area:** AIS on the HF+: no antenna for the 'VHF bus'
    - **Components:**
      - Airspy HF+ VHF mode
      - RTL-SDR Blog dipole kit
      - AIS-catcher
    - **Problem:** The HF+ is the default AIS receiver, but the 'VHF bus' is never defined. The only VHF antenna, the dipole kit, is set to 53.4 cm arms for LRPT or re-set for AIS (44 cm), sondes or ADS-B, so LRPT and continuous AIS cannot run together.
    - **Severity:** minor
    - **Evidence:** lab_ui_hf.final.hf_receiver.why and setup[7] ('VHF bus'); register #115 (one dipole kit re-set per band) and #128.
    - **Fix:** Add a second RTL-SDR Blog dipole kit (44 cm arms, vertical) on a dedicated VHF bulkhead that feeds the selector's VHF port. Its spare elements also serve the spare V4L's sonde and ADS-B runs.
    - **Fix cost:** $17.95
    - **Sources:**
      - https://www.rtl-sdr.com/DIPOLE
  14.
    - **Area:** Sled LNA bias supply
    - **Components:**
      - external RF sled
      - sled 5 V buck
      - TPS2553
      - SAWbird+ on sled ports
    - **Problem:** The sled makes its LNA bias with a switching 5 V buck from AUX 12 V, inside the same box as the HMC7992 and the bias tees, with no post-regulator. Ripple and switching spurs go straight up the coax to LNAs whose bias is their RF output port.
    - **Severity:** minor
    - **Evidence:** radio_lab.final.lab_bom (sled build parts: '5 V buck, 2x TPS2553 bias switches'); usb_power_case_plan (AUX loads).
    - **Fix:** Use buck to about 6 V, then LC, then a low-noise LDO at 4.5-5 V, then the TPS2553s. Fit a shield wall between the buck and the switch/RF section of the sled box.
    - **Fix cost:** About $5-10
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  15.
    - **Area:** Receive-only guard: on-board Wi-Fi/BT
    - **Components:**
      - FCU760K (AIC8800D80) on FE1.1s port 4
      - labd QUIET/field profiles
    - **Problem:** rfkill soft-blocks the radio, but the module stays enumerated and polled on the same single-TT USB 2.0 hub as RTL-B, the HF+ and touch. A NetworkManager or firmware fault can bring it back. The guard also does not cover a Pluto (libiio) if one is bought.
    - **Severity:** minor
    - **Evidence:** register #8 and #11; final-checks.md (FCU760K on FE1.1s P4).
    - **Fix:** In field and QUIET profiles, rfkill wlan and bluetooth, then de-authorise the USB device (echo 0 > /sys/bus/usb/devices/<port>/authorized). Re-authorise only in HOME/BENCH. The self-test confirms it is absent from lsusb. Extend the guard to libiio TX if a Pluto is bought.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  16.
    - **Area:** Lime-only coexistence (conditional)
    - **Components:**
      - LimeSDR Micro
      - Samsung T7 on USB 3 (5 Gb/s class)
      - PCIe Gen3 riser
    - **Problem:** If the Lime is kept:
  - T7 SuperSpeed traffic is broadband, strongest near 2.4-2.5 GHz (well known; Intel white paper, not re-fetched). That is next to the S-band targets (PHASMA 2208/2210, Black Kite 2286/2288 MHz), and it also raises the L1 floor.
  - Files say 'T7 idle during L/S passes' but give no recording path. Black Kite needs only about 1 Msps.
  - Lime lines at 737.28 MHz (2.2 MHz below the QO-100 NB IF), 1597.44, 1689.6 and 1720.32 MHz.
    - **Severity:** minor
    - **Evidence:** register #72/#127; radio_lab usb_power_case_plan (T7 floor check at 1.7/2.2 GHz); P4 line list.
    - **Fix:** labrx decimates S-band and L-band passes to 1 Msps or less and writes to UFS, so the T7 never writes during L/S/GNSS sessions. Keep the riser shielded and the RF bay seams at 7 mm or less. Add the 1597.44 MHz line to the mask.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
- **Proposed decisions:**
  1.
    - **Question:** C1 LimeSDR Micro: keep or drop
    - **Decision:** Gated optional, as the register says: keep the cancellable pre-order and decide on 31 Jan 2027 or on delivery. No core RF chain depends on it. 137/145 MHz never go to the Lime.
    - **Reason:** Every core target has an RTL or HF+ chain (budget table 'RF path per target'). The Lime adds only S-band telemetry, AHRPT rates and wideband NPU IQ.
    - **Consequences:** In the Lime build: 10-12 dB pads after each SAWbird, a band filter on every port, T7 idle in L/S/GNSS sessions, the 737.28/1597.44/1689.6/1720.32 MHz lines in the mask, and its own A/B run.
    - **Alternatives rejected:** Drop now (loses S-band before testing); make it core (driver unmerged, ships 15 Dec 2026).
  2.
    - **Question:** C2 Q6A RAM tier
    - **Decision:** 12 GB now, as the register says.
    - **Reason:** RAM cannot be added later; there is no RF impact.
    - **Consequences:** None for RF.
    - **Alternatives rejected:** 8 GB (closes the Lime and NPU-training options).
  3.
    - **Question:** C3 Pack 3S vs 4S
    - **Decision:** 4S1P P50B, as the register and power lens say.
    - **Reason:** For RF, 4S lets the LNB (13.2 V) and Boni-Whip (12.5 V) rails be plain LDOs from the pack, with no switching converter near the IF or the HF feed.
    - **Consequences:** LDO dissipation up to about 1.1 W (LNB) and 0.9 W (Boni) at 16.8 V; pad both to the mid-plate.
    - **Alternatives rejected:** 3S (needs boost converters for LNB and Boni, which are new spur sources).
  4.
    - **Question:** C4 12 V regulator for J21
    - **Decision:** Start with the D36V50F12, which is buyable, and gate it on an RF test. With HF+ in LF Quiet, at loads of 0.3/1/3 A in the sealed case, there must be no line 3 dB or more above the floor within ±5 kHz of 40/60/77.5/162/490/518/4209.5 kHz, and no wandering line in HF target windows during load steps. If it fails, replace it with a forced-PWM synchronous buck switching at 1 MHz or more, spread spectrum off, synced (part to source in P5, unverified).
    - **Reason:** Its roughly 500 kHz fundamental straddles NAVTEX 490/518 kHz, and its power-save mode wanders. A switching frequency of 1 MHz or more keeps every fundamental out of LF/MF. A buck is enough above the 13.2-13.6 V cutoff.
    - **Consequences:** Possible later cost of about $20-40 for the replacement (unverified). The CM choke and remote feed remain the main HF defence.
    - **Alternatives rejected:** Buck-boost by default (no buyable forced-PWM 5 A part found, and not needed above the cutoff); trusting the regulator without a narrow-RBW test.
  5.
    - **Question:** C5 USB port map
    - **Decision:** Register map: blue USB0 = RTL-A (T7 with the Lime); FE1.1s P1 RTL-B, P2 touch, P3 CH334F (H1 HMI, H2 IMU if not on UART, H3 LAB, H4 HF+). RF rules: both V4Ls sit in the RF bay on 10-20 cm shielded extensions with ferrites; the HF+ is in its can on H4; Wi-Fi is de-authorised in the field; the spare V4L goes on LAB USB, outside the case.
    - **Reason:** FE1.1s RF streams total about 13.3 MB/s against 35-40 MB/s practical. The dongles stay away from the HDMI/J5 edge.
    - **Consequences:** Extension leads plus ferrites cost about $10.
    - **Alternatives rejected:** Dongles plugged straight into J5 next to the HDMI bridge.
  6.
    - **Question:** C6 40-pin header and bus map
    - **Decision:** Register map, with fan PWM at 24.0 kHz (or on/off through the AO3400, as the power lens prefers for pin-33 drive). No PWM in LF Quiet.
    - **Reason:** 1 kHz, 20 kHz and 30 kHz PWM put harmonics exactly on LF carriers. 24 kHz keeps them at least 5.5 kHz away.
    - **Consequences:** Change the overlay's PWM period.
    - **Alternatives rejected:** The PoE-HAT 1 kHz overlay.
  7.
    - **Question:** C7 Hardware ownership
    - **Decision:** labd is the sole owner. RF interlocks it enforces: LNB EN only while the RTL-B selector is on the LNB port; bias locked off on DC-short profiles (9:1, hairpin Yagis); selector power-on default = 50 ohm; GPSDO and noise source only in BENCH, with antenna paths terminated.
    - **Reason:** These interlocks are the hardware half of the receive-only and no-DC-into-shorts rules.
    - **Consequences:** The interlock tests go into the labd test suite.
    - **Alternatives rejected:** Advisory flocks per engine.
  8.
    - **Question:** C8 LNB supply
    - **Decision:** LT3045 at 13.2 V from the switched pack node; two in parallel if the measured draw is above 0.33 A. EN from labd gives a true 0 V. ILIM is the single limit at 1.5-2x the measured draw (maximum 0.5 A per device). Then LC plus ferrite, injection on the antenna side of the DC-free selector, and the F port. No 18 V branch.
    - **Reason:** An LDO puts no switching spurs on the 739.5 MHz IF path. EN gives the required disconnect and ILIM gives one current limit. 16.8-13.2 V at 0.3 A is about 1.1 W. LT3045: 20 V input, 500 mA, programmable current limit, typical 260 mV dropout (measured about 314 mV at 300 mA).
    - **Consequences:** The LNB voltage tracks pack minus about 0.3 V below 13.5 V (still at or above the Bullseye's 11.5 V minimum). The QRO.cz upgrade at about 400 mA needs two parallel parts.
    - **Alternatives rejected:** TPS65233 (13.4/18.2 V IC, QFN, 22 kHz features not needed); MT3608/XL6009 boost (no disconnect, switching noise); SEPIC S18V20AHV plus #2813 (a switching converter beside the IF, plus an extra switch).
  9.
    - **Question:** C9 LNA bias rule
    - **Decision:** Every SAWbird+ runs through an injector at the SDR end, fed by a TPS2553 at 300 mA nominal with FAULT readback. The V4L tee may power only LNAs of 80 mA or less (L-band patch 20 mA, LNA V2 after measurement, SAWbird GOES 30 mA, SAWbird NOAA 80 mA), through the LAB_BIAS_OK gate. No micro-USB power at the feed.
    - **Reason:** SAWbird+ NOAA 170 mA, GOES 140-180 mA and H1 120 mA leave no margin on the 180 mA tee in a warm case.
    - **Consequences:** Delete rf_frontend (b)/(d), the radio_lab H1-on-tee line, foldable step 3's micro-USB feed and the 100-160 mA polyfuse.
    - **Alternatives rejected:** GOES+ on the tee after a soak; PTCs rated at 25 C.
  10.
    - **Question:** C10 FM filter
    - **Decision:** Nooelec Flamingo+ FM, two units, each at the antenna side of its VHF LNA (137 MHz and 2 m).
    - **Reason:** Both the SAWbird+ NOAA and the LNA V2 have an unfiltered first gain stage. The filter costs 0.06-0.45 dB at VHF sky temperatures (model). Bias enters at the LNA output, so no DC crosses the filter.
    - **Consequences:** Overrides the power lens's 'SDR side of the injector'.
    - **Alternatives rejected:** SDR-side placement (the LNA meets FM unprotected); the RTL-SDR Blog band-stop (more than 50 dB, no DC rating).
  11.
    - **Question:** C11 librtlsdr
    - **Decision:** The .so.2 rebuild of noble 2.0.1 (0204c9c + 65f0658), plus the bias-tee gate patch and rtl_biast diverted.
    - **Reason:** Keeps the consumers working and lets labd enforce the bias rules.
    - **Consequences:** First build on the Q6A in the W1-2 gates.
    - **Alternatives rejected:** 2.0.3 (.so.0); purge-and-fork.
  12.
    - **Question:** C12 Display field-mode pixel clock
    - **Decision:** Field EDID with two DTDs, tried in this order. (1) 151.50 MHz at 2200x1148 (59.99 Hz). (2) 127.90 MHz at 2200x1125 (51.68 Hz). Strip the CEA VICs and keep 148.5 MHz only for bring-up. Drop 128.70 and 164.4-168.4 MHz. Confirm the delivered clock by modetest and by near-field harmonic measurement.
    - **Reason:** Both candidates are clean in all 25 used windows. 151.5 MHz holds a 1.6 MHz clean window even with 0.5% SSC (127.9 MHz only 0.25 MHz), runs at 60 Hz, and its line rate is 7.95 kHz clear of the LF carriers (127.9 MHz: 1.86 kHz from 60 kHz). 164.4-168.4 MHz sits at the AIS SAW edge and 166.0 MHz fails with SSC.
    - **Consequences:** Update display_market, display, small_antenna_stack, the lab_ui_hf UI tests and the kernel cmdline (video=...@60 or @52) together. Ask Wisecoco for the DSI mode and lane rate.
    - **Alternatives rejected:** 128.70 (Inmarsat-C x12); 148.5 (fundamental 0.5 MHz above the 2 m filter, x3 = 445.5 MHz inside the 70 cm filter); 138.5 (inside the SAWbird+ NOAA passband); 164.4-168.4.
  13.
    - **Question:** C13 PPS on the held kernel
    - **Decision:** Out-of-tree pps-gpio on 6.18.2-4.
    - **Reason:** Keeps the HDMI/NPU kernel hold; no RF impact.
    - **Consequences:** None for RF.
    - **Alternatives rejected:** Route B on 7.0.11.
  14.
    - **Question:** C14 INA228
    - **Decision:** I2C0, user-space i2c-dev, shunt in the pack lead.
    - **Reason:** Agrees with the register; no RF impact.
    - **Consequences:** None for RF.
    - **Alternatives rejected:** ina238 hwmon binding.
  15.
    - **Question:** C15 Antenna tiers
    - **Decision:** Two tiers. Tier 1 (always carried): case whips (17 cm, SRH-701/A-V85), 2- and 4-turn helices, the RTL-SDR Blog L-band patch, the bare LNB with the 11 cm cone, and the 23 cm dipole kit as the LRPT default. Tier 2: the crossed Yagi (ultra-compact build), petal helicone and gore horn. No loops.
    - **Reason:** Patch and chip antennas cannot serve 137-146 MHz. The dipole kit already meets the piece-size rule, so LRPT on the V-dipole is available in both tiers.
    - **Consequences:** The case helical whip for 137 MHz stays experimental.
    - **Alternatives rejected:** Helical whip as the LRPT default.
  16.
    - **Question:** C16 Receive-only and policy leftovers
    - **Decision:** Strike the register list. RF additions: replace the antenna S11 steps (foldable steps 2-4, small-stack first_tests[2], antennas verify) with the receive-only P9/P15 checks; de-authorise Wi-Fi/BT in the field; extend the guard to libiio if a Pluto is bought.
    - **Reason:** Any antenna S11 sweep radiates.
    - **Consequences:** Antenna tuning relies on beacon SNR, Sun noise and GNSS C/N0.
    - **Alternatives rejected:** Brief indoor µW sweeps (default: not allowed).
  17.
    - **Question:** C17 HF antenna chain
    - **Decision:** Boni-Whip on an LT3045 at 12.5 V (ILIM 0.2 A provisional, EN from labd, default off, DC-sense first). The 9:1 wire is for HF only. Add a two-stage coax CM choke at the HF bulkhead (77-mix for LF/MF, 31-mix for HF) and a ground stake at the antenna. HF+ selector: two Omron G6K-2F-RF in series-shunt (HF / VHF / 50 ohm), default 50 ohm.
    - **Reason:** The remote feed point helps only if the coax shield is isolated in common mode. The G6K is a stocked, roughly GBP 21-26 50 ohm relay, against $114-332 for the ARJ22A03.
    - **Consequences:** Add about $75-110 to the HF chain. Confirm the HF-loop removal with the user.
    - **Alternatives rejected:** Clip-on ferrites only; ARJ22A03; coax relays at $242 or more; HMC241.
  18.
    - **Question:** C18 Storage
    - **Decision:** T7 only with the Lime. labrx never writes to the T7 during L/S/GNSS sessions; those are decimated to UFS.
    - **Reason:** USB 3 noise near 2.4 GHz and at L1.
    - **Consequences:** None in the no-Lime build.
    - **Alternatives rejected:** T7 always on.
  19.
    - **Question:** C19 CPU allocation
    - **Decision:** Register plan.
    - **Reason:** No RF impact.
    - **Consequences:** None for RF.
    - **Alternatives rejected:** Trainer on the A55 cores.
  20.
    - **Question:** C20 Roadmaps
    - **Decision:** Run the narrow-RBW terminated-floor A/B in the W1-2 gates, with both candidate display modes and pcie0 on/off, before buying antennas and region-dependent parts.
    - **Reason:** It decides the display mode, the 12 V regulator and the Ethernet overlay.
    - **Consequences:** About 5 h of bench time.
    - **Alternatives rejected:** A/B after assembly.
  21.
    - **Question:** C21 V4L count
    - **Decision:** Buy 3: RTL-A and RTL-B plus a spare that doubles as the LAB-USB monitor (ADS-B or sondes) with its own antenna (second dipole kit).
    - **Reason:** Simultaneous chains need separate antennas.
    - **Consequences:** +$17.95 for the second dipole kit.
    - **Alternatives rejected:** Fourth V4L now.
  22.
    - **Question:** C22 Software recipes
    - **Decision:** Register recipes, plus spur-mask consumers (SatDump wrapper, auto_rx, NPU labeller).
    - **Reason:** Fixed lines are otherwise detected as signals.
    - **Consequences:** One spur-mask file under version control.
    - **Alternatives rejected:** Per-app ad-hoc masks.
  23.
    - **Question:** C23 Region unknown
    - **Decision:** Defer the LNB, horn, SAWbird+ iO and GNSS-module choice. labd computes GEO visibility from the fix. RF: check LNB IF ingress (DVB-T 694-790 MHz, LTE B28 uplink) once the region is known.
    - **Reason:** GEO targets and IF ingress depend on the region.
    - **Consequences:** The LNB rail is built anyway.
    - **Alternatives rejected:** Buying now.
  24.
    - **Question:** C24 Costs and weights
    - **Decision:** Add RF deltas: CM chokes $15-30, selector $60-80, second dipole kit $17.95, sled LDO $5-10. Total about $100-140 on top of the completeness lens's $112 of filters and LNA.
    - **Reason:** These items are missing from every BOM.
    - **Consequences:** HF chain total about $280-500.
    - **Alternatives rejected:** None.
  25.
    - **Question:** C25 P1b completion
    - **Decision:** Closed: report_research.json exists.
    - **Reason:** I read it in full.
    - **Consequences:** STACK.md must carry the RF tables from this lens.
    - **Alternatives rejected:** None.
  26.
    - **Question:** R1 Ethernet/pcie0 in the field
    - **Decision:** Field DT overlay with pcie0 disabled; pcie0 enabled only on home/bench boots.
    - **Reason:** 25 MHz x68 and 100 MHz x17 = 1700.000 MHz; 25 MHz x63 = 1575.000 MHz.
    - **Consequences:** No wired Ethernet in the field.
    - **Alternatives rejected:** Leaving it on and masking the HRPT centre line.
  27.
    - **Question:** R2 Front-end order rule
    - **Decision:** VHF: filter, then LNA. UHF and L-band: LNA, then filter (SAWbirds have the SAW integrated). Fall back to filter first only where the P12 survey shows LNA compression.
    - **Reason:** At 437 MHz, filter first costs 0.75-2.84 dB (model). At 137 MHz it costs 0.06-0.45 dB.
    - **Consequences:** Patch-tier 70 cm: whip, LNA V2, filter bank, RTL.
    - **Alternatives rejected:** BPF first everywhere.
- **Budget tables:**
  - RF PATH PER TARGET (core, no Lime; tier 1 = always carried, tier 2 = foldable)
  | Target | Tier-1 chain | Tier-2 chain | SDR / bias |
  | LRPT 137.1/137.9 | dipole kit V 53.4 cm > Flamingo+#1 > SAWbird+ NOAA (cased, feed) > 1-2 m RG-316 > injector | same | RTL-A, tee OFF, TPS2553 300 mA, gain 10-25 dB |
  | 2 m 145.8-146 | SRH-701/A-V85 > Flamingo+#2 > LNA V2 | Yagi 2 m (hairpin = DC short) > Flamingo+#2 > LNA V2 | RTL-A |
  | ISS 437.55/.80/.825, 435-438 | 17 cm whip > LNA V2 > filter bank 420-450 | Yagi 70 cm > LNA V2 > BPF | RTL-B or RTL-A; tee only if LNA V2 is 80 mA or less |
  | Inmarsat-C 1537-1545 | 2/4-turn helix > SAWbird+ iO, or L-band patch (20 mA) | helicone > iO | RTL-B; clock not 128.70 |
  | HRPT 1700 | 4-turn helix > SAWbird+ GOES | helicone > GOES | RTL-B 2.4-2.56 Msps; pcie0 off; LNB off |
  | H1 1420.4 | helix > SAWbird+ H1 (injector) | helicone > H1 > VBFZ-1400 | RTL-B; GPSDO off |
  | GNSS L1/EGNOS | LC76G active patch; GNSS-SDR: L1 patch on V4L tee | same | T7 idle; pcie0 off |
  | QO-100 | bare LNB / 11 cm cone > F > LT3045 13.2 V tee > 15-20 dB pad | 3/6-gore horn | RTL-B; LNB EN only when selected |
  | ADS-B 1090 | spare V4L + Uputronics 1090 or Pro Stick Plus, 6.5 cm | same | LAB USB |
  | AIS 162 | dipole kit #2 (44 cm) > VHF port > G6K selector | same | HF+ VHF |
  | Sondes 400-406 | spare V4L, 17.7 cm (+Uputronics 403) | same | mask 400.000/403.2 |
  | HF 0.5-31 MHz | 7-15 m wire + 9:1 at 5-10 m > RG-316 > CM choke > selector | same | all bias OFF |
  | LF 40-162 kHz, NAVTEX | Boni-Whip at 2 m or more (12.5 V via injector) > CM choke (77-mix) > selector | same | LF Quiet |
  - PIXEL-CLOCK CANDIDATES (my scan, 25 used windows, 0.5 MHz guard, n of 40 or less; strong-emission passbands for n of 3 or less)
  | pclk MHz | Totals / refresh | Hits | Clean window with 0.5% SSC |
  | 128.70 | 2200x1125 / 52.0 Hz | x12 = 1544.4 (Inmarsat-C) | none (smears 1536.7-1544.4) |
  | 127.90 | 2200x1125 / 51.68 Hz | none | 127.79-128.04 |
  | 151.50 | 2200x1148 / 59.99 Hz | none | 150.755-152.35; line rate 68.86 kHz |
  | 166.0 | 2200x1260 / about 60 Hz | none without SSC; fails with SSC | 166.635-168.65; fundamental at AIS SAW edge |
  | 148.5 | CEA 1080p60 | x3 = 445.5 inside 420-450 BPF; fundamental 0.5 MHz above 2 m filter | bring-up only |
  | 138.5 | CVT-RB | fundamental inside SAWbird+ NOAA passband | reject |
  | 83.77 / 71.0 | 4D 1280x800 | 1089.0 ADS-B / 1420.0 H1, 1562.0 B1I, 1704.0 | reject |
  - KNOWN LINES FOR P4 AND THE SPUR MASK (exact harmonic in a used window; amplitude unmeasured)
  | MHz | Source | Target hit | Control |
  | 1700.000 | 25 MHz x68 (Ethernet, LNB ref), 100 MHz x17 (pcie0 / Lime), 10 MHz x170 | Meteor HRPT centre | pcie0 off; LNB EN interlock; GPSDO off |
  | 1699.2 | V4L 28.8 x59 | HRPT | mask |
  | 1575.000 | 25 MHz x63 | GPS L1 (0.42 MHz offset) | pcie0 off; LNB off |
  | 1574.4 | 19.2 MHz x82 | Galileo E1 lobe | measure |
  | 1600.0 / 1597.44 | 100 x16, 25 x64 / Lime 30.72 x52 | GLONASS G1 | as above |
  | 1560.0 | 12 MHz x130 | BDS B1I | shield hub |
  | 1544.4 | 128.70 x12 | Inmarsat-C | change clock |
  | 1540.0 | GPSDO 10 x154 | Inmarsat-C | GPSDO off |
  | 1420.000 / 1420.8 | GPSDO 10 x142 / 19.2 x74 | H1 | GPSDO off; mask |
  | 1090.000 | GPSDO 10 x109 | ADS-B | GPSDO off |
  | 1689.6 | 76.8 x22, Lime 30.72 x55 | FY-2H/Elektro window | mask |
  | 740.000 / 737.28 | GPSDO x74 / Lime x24 | QO-100 NB IF | GPSDO off |
  | 403.2 / 400.000 | 28.8 x14, 19.2 x21 / 25 x16, 100 x4, 10 x40 | sondes | auto_rx ignore list |
  | 144.000 / 432.000 / 1704.0 | 12 MHz x12/x36/x142 | near 2 m/70 cm, Metop | puck and hub placement |
  - BIAS AND RF RAILS
  | Rail | Load | Current | Limit | Source |
  | LNA feed VHF | SAWbird+ NOAA | 170 mA | TPS2553 300 mA | LAB 5 V > LT3045 4.5 V |
  | LNA feed L | GOES+ / iO / H1 | 140-180 / unpublished / 120 mA | TPS2553 300 mA | same |
  | LNA feed UHF/2 m | LNA V2 (x2) | unpublished (measure) | V4L tee if 80 mA or less, else TPS2553 | tee or same |
  | Worst simultaneous LNA | NOAA + GOES + 2x LNA V2 | about 0.4-0.45 A | LT3045 0.5 A | - |
  | LNB 13.2 V | Bullseye | 200-300 mA budget (unpublished) | ILIM 1.5-2x measured | LT3045 (x2 above 0.33 A); 1.1 W at 16.8 V |
  | Boni 12.5 V | Boni-Whip | unpublished | ILIM 0.2 A provisional | LT3045; 0.86 W at 16.8 V |
  | HF+ | HF+ Discovery | unpublished (0.1-0.3 A) | LAB 5 V, VBUS-cut | CH334F H4 |
  | V4L x2-3 | dongles | 250-270 mA each | WS4612 about 2.1 A / LAB TPS2553 1 A | VCC_5V_PERI / LAB |
  - USB RF STREAMS (no Lime)
  | Device | Port | Rate |
  | RTL-A 2.56 Msps 8-bit IQ | blue USB0 (USB2 HS) | 5.12 MB/s |
  | RTL-B | FE1.1s P1 | 5.12 MB/s |
  | HF+ 768 ksps int16 | CH334F H4 | 3.07 MB/s |
  | Spare V4L (monitor) | LAB USB via CH334F H3 | 5.12 MB/s |
  | Touch, IMU, HMI | FE1.1s/CH334F | less than 0.1 MB/s |
  | FE1.1s total | single TT, 35-40 MB/s practical | about 13.3 MB/s |
  | Lime build: Lime PCIe 56 Msps cs16 > T7 on blue | - | 224 MB/s |
  - GAIN STAGING (model: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/stage.py)
  | Case | Result |
  | 70 cm, BPF 1/2/3 dB first vs LNA V2 (NF 0.7) first | Te 148/262/405 K vs 61/64/68 K; SNR loss 0.75-4.05 dB at Tant 150-400 K |
  | 137 MHz, Flamingo+ 0.5-1.2 dB before SAWbird+ NOAA | 0.06-0.45 dB at Tant 1000-3000 K |
  | LNB IF integrated noise (Tsys 100 K, 1.2 GHz) | 50/60/66 dB gain: -37.8/-27.8/-21.8 dBm; with 20 dB pad -57.8/-47.8/-41.8 dBm (V4L 3 dB desense -20 to -40 dBm) |
  | Spur visibility (NF 5 dB) | floor -119 dBm/100 kHz, -135/2.5 kHz, -152/50 Hz, -165/2.3 Hz |
  - LF COMB PLANNING (/tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/lf.py; carriers 40, 60, 77.5, 162, 490, 518 kHz)
  | Source | Closest harmonic to a carrier |
  | PWM 1 / 20 / 30 kHz | 0 kHz (exact hits) |
  | PWM 25 kHz | 2.5 kHz (75 vs 77.5) |
  | PWM 24.0 kHz | 5.5 kHz (best in 20-32 kHz) |
  | USB SOF 1 kHz / 8 kHz | exact on 40/60/162/490/518 kHz / exact on 40 kHz |
  | Line rate 127.9 MHz / 2200 | 58.14 kHz, 1.86 kHz from 60 |
  | Line rate 151.5 MHz / 2200 | 68.86 kHz, 7.95 kHz clear |
  | IP2368 250 kHz | 500 kHz, 10 kHz from NAVTEX 490 |
  - A/B MATRIX (one plan replacing P4, display A/B, HF A/B and the small-stack tests)
  | Item | Spec |
  | Windows | the 25 used windows (pixel-clock table) plus the known lines; HF+ at 40/60/77.5/162/490/518/4209.5 kHz, 1, 7, 14 MHz |
  | Method | 60 s IQ per window, 2^20 FFT, Welch average; HF+ 1 Hz RBW; GNSS GSV mean C/N0 (top 8) plus GNSS-SDR |
  | States | each one alone: HDMI link off / backlight 0-50-100% / mode A or B; pcie0 on/off; Wi-Fi deauth; fan DC / PWM; LAB 5 V; CH334F; charger; LNB on/off; LNA rails; Boni rail; puck; V4L streaming on the shared hub; T7 (Lime build) |
  | Conditions | terminated at the SDR, then at the LNA input, then on antenna; lid closed after a 30 min soak |
  | Pass | no line 3 dB or more above the floor inside a used window; broadband rise 0.5 dB or less; GNSS 1 dB-Hz or less; result saved as the spur mask |
- **Checks passed:**
  - 128.70 MHz x12 = 1544.4 MHz falls inside Inmarsat-C 1537.0-1544.2 (plus guard), as the register says; the field clock must change.
  - 127.9 MHz is clean in all 25 used signal windows: Meteor, 2 m, AIS, NOAA WX, sondes, 70 cm, QO-100 NB IF, ADS-B, UAT, H1, Inmarsat-C, B1I, L1/E1/SBAS, G1, Iridium carrier, FY-2H/Elektro, HRPT, Metop/AWS, S-band, FM, VOR, DAB. Its SSC-proof window is 127.79-128.04 MHz. The register's '127.84-127.99' agrees within my wider signal-window model.
  - 148.5 MHz has no harmonic in a used signal window. Its L5 hit (1188.0) is irrelevant because no receiver in the stack uses L5. It still fails on the fundamental next to the 2 m filter and on x3 inside the 70 cm filter, so 'bring-up only' stands.
  - The register's 9:1 limit is consistent: WB9-1 is rated 0.125-125 MHz, so the LF time signals correctly rely on the active E-field whip.
  - Flamingo+ FM (fetched): $24.95, more than 60 dB rejection, -3 dB at 75/120 MHz, 250 mA DC pass, +18 dBm maximum. It passes 137/145.8 MHz with about 0.5 dB loss.
  - A purchasable 70 cm filter exists: Nooelec Ham Filter Bank Barebones, $66.95, 2 m 144-148 MHz and 70 cm 420-450 MHz (fetched). This partly answers register open question 18; loss is unpublished.
  - LT3045 suits both the 13.2 V LNB and 12.5 V Boni rails: 20 V input, 500 mA, programmable current limit, typical 260 mV dropout (about 314 mV at 300 mA reported), output to 15 V.
  - Using the injector at the SDR end both powers the SAWbird+ through its output port and blocks DC from the SDR; no extra DC block is needed on the RTL ports.
  - LNB IF level: integrated noise of -22 to -38 dBm with a 15-20 dB pad stays below the V4L desense range without SNR loss, because LNB noise dominates.
  - USB bandwidth: about 13.3 MB/s of RF streams on the FE1.1s, against 35-40 MB/s practical.
  - Lime coexistence is already handled in the files: one RX LO (dual RX only within a band), 137/145 MHz kept on the RTL, 10-12 dB pads after the SAWbirds, the TX port terminated, and the software guard against TX sink blocks.
  - Receive-only: no core chain contains a transmitter. RTL and HF+ are RX-only, the LNB has no TX, and signal sources are conducted-only with pad rules (tinySA -40 dBm or less, 30 dB or more above 800 MHz, GPSDO 80 dB plus a DC block). QUIET mode rfkills WLAN and Bluetooth in radio_lab, the Pinecil runs with BT off and the FNB58 is the Std variant.
  - LTE B3 uplink (1710-1730 MHz) inside the SAWbird+ GOES passband is known and correctly handled: low gain, avoid crowds, optional 1695-1712 MHz post-filter.
  - The V4L and both SAWbird+ parts are metal-cased; the V4L case is aluminium, which suits RF-bay placement on short shielded extensions.
- **Notes:** Method. I read user_requirements.md and report_research.json in full: register decisions, compliance, corrections, conflicts, open questions and verdict. From the studies and audits I read the RF-relevant fields: radio_lab final (BOM, procedures P0-P21, USB/power plan), rf_frontend verify, lab_ui_hf HF receiver/antenna, small_antenna_stack revised stack and first tests, foldable kit and build steps, display_market settings and acceptance, and the mechanical RF notes. I also read the Q6A schematic text for clocks and PCIe0, and the existing final-checks.md. The power, interface and completeness lenses already cover the D36V50F12 near NAVTEX, the software bias-tee bypass, the missing 2 m filter and the RTL SP4T selectors. I reference them rather than repeat them, and I flag where the power lens's FM-filter placement contradicts RF practice.
  
  Models (all calculations, not measurements), in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/:
  - harm.py: harmonic hits against 18 core signal windows, extended to 25 (with broadcast and Lime bands) in a second run.
  - win.py: clean pixel-clock windows, with and without 0.5% down-spread SSC.
  - lf.py: LF comb planning.
  - stage.py: Friis gain staging, LNB IF level and spur visibility.
  Harmonic amplitudes are unknown. The scans only say where a line can fall; the narrow-RBW A/B decides whether it matters.
  
  Web: 4 WebSearch and 5 WebFetch calls (2 failed: an Analog Devices 503 and a Coilcraft 403). Verified this session: the Flamingo+ FM page; the Nooelec Ham Filter Bank page; LT3045 headline specs (Digi-Key highlight, ADI forum); Omron G6K-2F-RF RF specs and RS UK prices (about GBP 21-26 ex VAT, non-latching); Panasonic ARJ22A03 prices and lead times (about $114-332, NRND at one Mouser region).
  
  Unverified: CM-choke turn counts and impedances (design targets); G6K isolation at 162-260 MHz (extrapolated from 1 GHz); whether the RTL8111/RTL8125 25 MHz crystal keeps running with pcie0 disabled; DP/RA620 SSC behaviour; the Wisecoco DSI mode; whether the panel accepts 2200x1148 at 60 Hz or 51.7 Hz; the Ham Filter Bank's loss and selection method; currents of the LNA V2, SAWbird+ iO, Bullseye, Boni-Whip and HF+; the forced-PWM 12 V replacement part; and the USB 3 2.4 GHz noise level (well known, not re-fetched).
  
  Physics against wishes: no-loop HF stays limited by local noise, so the CM choke plus the remote feed is the closest compliant option. Patch and chip antennas cannot serve VHF. Typical QO-100 SSB and DATV still need dish-class gain. An antenna S11 sweep always radiates.

## completeness:lens2 (run `wf_6ce87eb1-883`)

- **Lens:** MISSING PARTS: cables and adapters, RF switching and its drive, bias tees, DC blocks, pads, loads, filters, fuses, PTCs and TVS, connectors and DC jacks, power key, charger input, fasteners, thermal parts, fan, sun hood, strap and tripod mount, weather protection, bags, spares, tools, flashing media, and the home-base PC for QAIRT 2.42.
- **Issues:**
  1.
    - **Area:** RF switching
    - **Components:**
      - RTL-A
      - RTL-B
      - Airspy HF+ input selector
      - HMC7992 SP4T
      - MCP23017
    - **Problem:** The core receivers have no input-routing hardware. In the patch tier, RTL-A has two VHF/UHF whip bulkheads (137 MHz and 2 m/70 cm). RTL-B has an L-band SMA and the LNB F port. Each RTL has one SMA input. The HF+ needs an HF / VHF-AIS / 50 ohm selector, but no part is named and it is missing from every BOM. The only switch in the files is the extended-tier sled (HMC7992), which was designed around the Lime COM port. The 'VHF bus' that feeds the HF+ for AIS is not defined anywhere. As specified, swapping chains means opening the case, and the menu cannot route inputs.
    - **Severity:** major
    - **Fix:** Fit two internal SP4T selectors. RTL-A: 137 / 2 m / 70 cm / terminated. RTL-B: L-band / LNB IF / BENCH or sled / terminated. Every port must be DC-free, with bias tees ahead of the switch. The HMC7992 board class from the files is enough here: expect about 30-37 dB isolation, and verify logic levels at 3.3 V. For the HF+, use a latching relay pair on a small PCB with SMA edge jacks (HF / VHF-AIS / 50 ohm). Accept it only if conducted isolation is 35 dB or more at 162-260 MHz on the LiteVNA. Do not buy commercial latching SMA relays: they are 12/28 V coil parts at about $242 or more. Drive everything from the new expander described in the GPIO issue. Fallback: the 'connect X' prompt, using external bulkheads only.
    - **Fix cost:** About $40-65: 2x HMC7992 board at CA$20.49 each (files, third-party listing, unverified), plus relays and PCB at $10-25 (estimate).
    - **Evidence:** small_antenna_stack.final.revised_stack[27] (two whip bulkheads, plus RTL-B SMA and the F port); report_research register decision #93 (selector part TBD, missing from the BOM); radio_lab.final.lab_bom[36] (sled HMC7992 is extended and Lime-oriented); lab_ui_hf.final.hf_receiver.setup ('VHF bus' undefined).
    - **Sources:**
      - https://www.datasheets.com/radiall/r570342100
      - https://www.pasternack.com/spdt-electromechanical-relay-latching-switch-accessory-pwb-3-ghz-12v-sma-pe71s8001-p.aspx
  2.
    - **Area:** Control I/O
    - **Components:**
      - MCP23017 #1 (0x20)
      - TPS2553 bias switches
      - LNB enable
      - Boni-Whip switch
      - selectors
    - **Problem:** One internal MCP23017 has 16 lines, but the core design needs about 24. Outputs (17): LAB EN, AUX EN, 3 VBUS cuts (RTL-A, RTL-B, HF+), 4 bias enables (137, L-band, 70 cm, H1), LNB EN, Boni EN, relay set/reset (2), and 2x2 SP4T control lines. Inputs (7): LAB FAULT, 4 bias FAULTs, LNB PG/FAULT, Boni FAULT. GPA4-GPA6 are already reserved for Lime bias.
    - **Severity:** major
    - **Fix:** Add MCP23017 #3 at 0x22 inside the handheld on I2C2. Alternatively use a TCA9535 with the built-in pca953x driver; avoid the PCA9555/TCA9555. Add the new lines to the single pin map before the schematic (P7). Use pull-downs so every switch and bias line is off and every selector sits on its terminated port at power-up.
    - **Fix cost:** $5.95 (Adafruit MCP23017 #5346, price from radio_lab), plus about $1 of resistors.
    - **Evidence:** radio_lab.integ.connections (MCP23017 #1 pin map: GPA0-3 used, GPA4-6 Lime bias, GPB0-1 FAULT); register decision #56; my count in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/missing_calc/b.py.
    - **Sources:** []
  3.
    - **Area:** LNB supply
    - **Components:**
      - LNB 13.2 V regulator
      - Pololu #2813
      - Othernet Bullseye LNB
    - **Problem:** The named LNB regulators are boost parts: 'TPS65233-class or a trimmed boost' in radio_lab, and an 'MT3608/XL6009-class boost' in the small stack. On the chosen 4S pack (12.0-16.8 V), the input is above 13.2 V for most of the discharge, and a boost cannot step down. A plain boost would pass roughly the pack voltage minus a diode drop, up to about 16 V, to the LNB. That is the horizontal-select range (16-19 V), outside the 11.5-14 V vertical window, so QO-100 NB would fail silently. TPS65233 behaviour with VIN above VOUT was not checked.
    - **Severity:** major
    - **Fix:** Use a SEPIC or buck-boost set to 13.2 V ±0.2 V: the Pololu S18V20AHV adjustable 9-30 V (same family as the S18V20F12). Pololu states the SEPIC output is 'not completely disconnected' when EN is low, so keep a second #2813 (or an eFuse rated 20 V or more) after it as the true disconnect. Then an LC filter, a PTC set from the measured LNB current, and an SMBJ15A at the F port. Strike the boost options from radio_lab lab_bom[34] and the small stack row 18.
    - **Fix cost:** About $40-50: S18V20F12 sibling $29.95 (pololu.com, rationed; S18V20AHV price not checked), #2813 $8.95, LC/PTC/TVS about $3.
    - **Evidence:** radio_lab.final.lab_bom[34]; small_antenna_stack.final.revised_stack[18]; register decisions #102/#103 (buck-boost or boost with true disconnect; 4S swings 12-16.8 V).
    - **Sources:**
      - https://www.pololu.com/product/2577
      - https://www.pololu.com/product/2813
  4.
    - **Area:** Bias tees / DC injection
    - **Components:**
      - SAWbird+ NOAA/GOES/iO/H1
      - RTL-SDR Blog LNA V2
      - LNB IF tee
      - TPS2553
    - **Problem:** No bias-tee part is named for the internal injectors. The files say 'specify an injector rated down to about 100 MHz', '2 generic 10 MHz-6 GHz bias tees (lose 3-7 dB at 100-200 MHz)', and 'the handheld's internal LNB bias tee', and the ZFBT was dropped. The current ratings are unchecked against the limits. The obvious SMD part, Mini-Circuits TCBT-14+, is rated 200 mA DC, which is below the TPS2553 250-300 mA limit for each SAWbird+ (180 mA budget). The LNB tee must carry 1.5-2x the measured LNB draw, which could be 0.4-0.8 A if a QRO.cz LNB (about 400 mA) is used.
    - **Severity:** major
    - **Fix:** Build one internal bias board with 5 channels (137, 2 m/70 cm, L-band, H1, LNB). Use inductors rated 0.5 A or more on the LNA channels and 1 A or more on the LNB channel, plus C0G DC blocks. Verify S21/S11 conducted on the LiteVNA over 100-1800 MHz (LNB channel 700-800 MHz) and record the results in parts.yaml. Use the TCBT-14+ only on lines of 80 mA or less. Where a bench-grade connectorised tee is wanted, use the ZFBT-4R2GW+ ($111.57 in the files).
    - **Fix cost:** $15-30 DIY (estimate). TCBT-14+ about $8.45 at qty 10 (old datasheet price).
    - **Evidence:** register decision #96 ('Specify an injector rated down to about 100 MHz'); register decision #100 (TPS2553 250-300 mA); radio_lab.integ ('2 generic 10 MHz-6 GHz bias tees'); radio_lab.final.lab_bom[34] (internal LNB tee unnamed).
    - **Sources:**
      - https://www.minicircuits.com/pdfs/TCBT-14+.pdf
      - https://www.mouser.at/new/mini-circuits/mini-circuits-tcbt14-plus-bias-tee/
  5.
    - **Area:** Cables and adapters
    - **Components:**
      - SMA bulkhead pigtails
      - RG316/RG174 jumpers
      - 75 ohm F lead
      - USB pigtails
      - HDMI lead
      - Adafruit CH334F #5997
    - **Problem:** No file has a cable schedule. Each study leaves cables out or guesses: foldable 'Not included: cables and pigtails ($40-60), DC blocks (about $25)'; antennas 'about $40-60 (estimate)'; small stack '2-3 thin leads $15-30'. Concrete gaps:
  - The Baofeng A-V85 is SMA-female, so it needs an M-M adapter.
  - The CH334F hub's 4 downstream ports are 4-pin pads only (Adafruit page), so LAB USB-A, the HF+, the HMI RP2040 and the puck all need pigtails.
  - The internal V4Ls need short USB extensions and SMA jumpers to their bulkheads.
  - The LNB needs a 75 ohm F lead.
  - The Boni-Whip needs a BNC lead.
  - The GNSS needs an IPX-to-SMA pigtail if the antenna is external.
  - The touch USB needs a VBUS-cut lead.
  - EDL recovery needs an A-to-A cable.
  - The HF+ USB connector type is not recorded (airspy.com does not list it).
    - **Severity:** major
    - **Fix:** Adopt the cable schedule in budget_tables, with every run's length, genders and qty. Buy branded RG316 jumpers or VNA-screen generic ones. Keep RP-SMA in a separate bag.
    - **Fix cost:** About $90-170: internal RF $25-45, external RF and adapters $40-80, USB $25-45 (estimates).
    - **Evidence:** foldable_antennas.final.total_cost; antennas.json (cables/pigtails/adapters estimate); small_antenna_stack.final.revised_stack[14] and [23]; radio_lab.final.lab_bom[30] (CH334F H1-H4); lab_ui_hf hf_antenna (BNC-to-SMA lead).
    - **Sources:**
      - https://www.adafruit.com/product/5997
      - https://www.waveshare.com/LC76G-GNSS-Module.htm
  6.
    - **Area:** Filters / LNA per band
    - **Components:**
      - Nooelec Flamingo+ FM
      - SAWbird+ NOAA
      - LNA V2
      - 70 cm BPF
    - **Problem:** The register picks 'one filter, permanently in the 137/145 MHz path', but the patch tier has two VHF/UHF entry points. The SAWbird+ NOAA has a 2.6 MHz passband at 137 MHz, so it blocks 145.8 MHz. The planned 70 cm BPF ahead of the LNA V2 blocks 2 m. As a result, no filtered 2 m path exists for the Yagi's 2 m half, 2 m CubeSats or APRS. The 70 cm BPF is still unnamed.
    - **Severity:** major
    - **Fix:** Write one band-to-filter/LNA matrix:
  - 137: Flamingo+ then SAWbird+ NOAA.
  - 2 m: Flamingo+ #2 then LNA V2.
  - 70 cm: BPF then LNA V2.
  - L-band: SAWbird+ GOES or iO.
  - 1420: SAWbird+ H1.
  - LNB IF: pad.
  Buy a second Flamingo+ and run two LNA V2s in service plus one spare. For the 70 cm BPF, either buy the Nooelec Ham Filter Bank Barebones ($66.95, files, includes 70 cm) now, or get a quote for the Anatech 9531 cavity (432-438 MHz, SMA, 1.0 dB or less, no price listed).
    - **Fix cost:** $24.95 Flamingo+ + $19.95 extra LNA V2 + $66.95 filter bank, about $112 in total.
    - **Evidence:** register decision #85 (one Flamingo+); register decision #96 (SAWbird+ NOAA 2.6 MHz 3 dB bandwidth); small_antenna_stack.final.revised_stack[9]/[10]/[14]; foldable_antennas.final.foldable_kit[1] (145.8 MHz feed to the RTL).
    - **Sources:**
      - https://anatechelectronics.com/435-mhz-band-pass-filter-9531.html
  7.
    - **Area:** Battery build
    - **Components:**
      - Molicel P50B x4 (+1 spare)
      - nickel strip
      - balance lead
      - BMS
      - welding
    - **Problem:** The pack is a welded 4S1P from bare cells ('test capacity and IR before spot-welding'), but no file budgets a welder or pack-build service, a nickel grade, fish paper, a balance-lead connector (the ISDT 608PD needs a JST-XH 5-pin balance lead) or a cell tester. The P50B also had only UAH prices.
    - **Severity:** major
    - **Fix:** Buy 5 P50B: NKON lists EUR 6.75 incl. VAT (EUR 5.58 ex VAT) per cell on a page dated 31 Jul 2026. Add 0.15x8 mm pure-nickel strip, fish-paper rings, Kapton, 4S wrap, a JST-XH 5-pin balance lead to an internal service connector, and an XT30 main lead. Have a battery shop or pack builder weld it. Buy a capacitor welder (third-party listings $270-305, unverified) only if more packs will be built. Reject spring holders (contact resistance and vibration in a handheld) and soldering to cells. Check cell IR and capacity before welding with a cell tester, or by individual charge and discharge.
    - **Fix cost:** $70-105: cells about $39 at EUR 33.75, sundries $10-25, welding service $20-40 (estimate).
    - **Evidence:** power.json verify.known_problems_and_fixes_to_apply (last item); power.json final_recommendation (P50B priced only on Prom.ua); register decision #59 ('No world price is given').
    - **Sources:**
      - https://www.nkon.nl/rechargeable/molicel-inr21700-p50b-5000mah-50a.html
  8.
    - **Area:** Mechanical mount
    - **Components:**
      - 1/4-20 tripod/boom mount
      - 2 mm aluminium mid-plate
    - **Problem:** mechanical_thermal offers 'a captured 1/4-20 nut, or a thread tapped in the aluminium plate'. A 1/4-20 thread has a 1.27 mm pitch, so a 2 mm plate gives only 1.57 engaged threads. About 9.5 mm (1.5 D) is a common aluminium rule of thumb. The tapped option would strip under a 1.05-1.4 kg device on a boom or tripod.
    - **Severity:** major
    - **Fix:** Strike the tapped-plate option. Use a 10-12 mm aluminium boss with a steel 1/4-20 insert or rivet nut, bolted to the mid-plate with 4x M3 and fitted with an anti-rotation pin, or a captured steel nut in a printed pocket backed by the plate. Pull-test it at 3x device weight.
    - **Fix cost:** $3-8 (estimate).
    - **Evidence:** mechanical_thermal.json verify.known_problems_and_fixes_to_apply ('Tripod/boom mount: a captured 1/4"-20 nut, or a thread tapped in the aluminium plate'); arithmetic in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/missing_calc/b.py (model).
    - **Sources:** []
  9.
    - **Area:** Antenna supports
    - **Components:**
      - travel tripod
      - pan-tilt head
      - collapsible mast
      - guy cords and stake
    - **Problem:** The procedures need supports that no BOM buys:
  - V-dipole at 1-1.1 m.
  - HRPT 'from a tripod at least 50 cm above ground'.
  - Tripod-mounted Yagi and 23 dBi horn.
  - Boni-Whip at least 2 m up on 'a pole that collapses to 35 cm or less'.
  The dipole kit includes only a flexible mini tripod, and foldable_antennas explicitly excludes 'a mini pan-tilt tripod'. The packed-size rule also applies to these supports.
    - **Severity:** major
    - **Fix:** Buy a travel tripod that folds to 35 cm or less, reaches 1.2 m or more, takes a 1/4-20 and has a small pan-tilt head. Add a shock-corded aluminium tent-pole mast (7x35 cm sections, about 2.4 m) with 2-3 guy cords and a ground stake. Add a throw cord and weight for the HF wire. Count 0.35-0.9 kg more in the sling.
    - **Fix cost:** $55-150 (estimate; no model priced).
    - **Evidence:** foldable_antennas.final.foldable_kit[0] (fold_method lists only the flexible tripod); foldable_antennas.final.total_cost ('Not included: ... A mini pan-tilt tripod'); foldable build step 7; lab_ui_hf.final.hf_antenna.setup (Boni-Whip pole).
    - **Sources:** []
  10.
    - **Area:** Weather protection
    - **Components:**
      - handheld case
      - fan and blower intakes
      - encoders and keys
      - feed-point LNAs
      - connectors
    - **Problem:** No study sets an ingress target or budgets weather parts:
  - The case has a fan and a blower intake; the encoders are not sealed.
  - The cased SAWbird+ units at the antenna feeds are not waterproof.
  - Only antennas.json mentions self-amalgamating tape, adhesive heat-shrink and drain holes; no file mentions desiccant.
  Physics versus wish: with 11-32 W internal (no Lime) plus 13.5-17 W solar on the display face, a sealed passive case cannot shed the heat, so IP67 is not reachable with this thermal design.
    - **Severity:** major
    - **Fix:** Target IPX4/IP54. Parts:
  - Baffled intakes with stainless mesh and hydrophobic foam.
  - Adhesive ePTFE vents on the sealed RF bay and the LNA boxes.
  - Silicone dust caps on every SMA, F and USB port.
  - A clear rain sleeve.
  - IP65 ABS boxes with cable glands for the feed LNAs.
  - Self-amalgamating tape and dielectric grease.
  - Silica gel in the Pelican and pouches.
  Add a rule: LOCK plus encoder-only operation in rain, and no fan intake facing up.
    - **Fix cost:** $45-110 (estimate).
    - **Evidence:** grep over final/*.json: 'desiccant' 0 hits; 'gasket' 2 hits (mechanical only); IP ratings only for displays; antennas.json sealing advice; mechanical_thermal decision #17 (25-35 W internal with the Lime, 11-17/24-32 W without; solar 13.5-17 W).
    - **Sources:** []
  11.
    - **Area:** Home-base PC
    - **Components:**
      - x86-64 PC
      - NVIDIA GPU 8-16 GB
      - Ubuntu 22.04 / Python 3.10 for QAIRT 2.42
    - **Problem:** The user's PC is unconfirmed (register #45, open question 9), and the Ubuntu 22.04 VM route is untested. Without a GPU there is no T3 detector retraining. Without any x86-64 machine there is no QAIRT 2.42 conversion: its Python converter and quantizer are x86-64 only.
    - **Severity:** major
    - **Fix:** Minimum: any x86-64 machine with 16 GB RAM or more, running an ubuntu:22.04 container (Python 3.10) with the archived QAIRT 2.42.0.251225 zip. No GPU needed; $0 if owned; container use is untested. Recommended for T3: an NVIDIA 12 GB card (RTX 3060 12 GB class), 32-64 GB RAM, 1-2 TB NVMe, and a 2-4 TB backup disk for golden images and datasets. Private captures stay off Colab/Kaggle.
    - **Fix cost:** $0 if a PC exists. GPU about EUR 298 (France low, GPUPrix, 6 Jul 2026) to about $500 (US listings after the relaunch, Guru3D, Jul 2026); backup disk $60-100 (estimate).
    - **Evidence:** npu_training.final.hardware_needs; register decision #45; register open_questions[9].
    - **Sources:**
      - https://www.guru3d.com/story/geforce-rtx-3060-12gb-prices-reportedly-jump-after-relaunch/
      - https://gpuprix.com/zh/france/gpus/geforce-rtx-3060-12gb
  12.
    - **Area:** Power accessories
    - **Components:**
      - Pololu #2813 pushbutton
      - power key
      - XT30 arming plug
      - IP2368 USB-C
      - wall PD charger
    - **Problem:** The #2813 needs a physical pushbutton, but the six sealed HMI keys have no POWER key. There is no transport disconnect, although the Pelican note says to 'pack so the master switch cannot be pressed'. The IP2368 needs a PD source of 60 W or more, but only a power bank is listed: no wall charger, no 3-5 A C-C cable, and no sealing for the charge port. The IP67 panel USB-C extensions found have inconsistent ratings (60 vs 100 W).
    - **Severity:** minor
    - **Fix:** Fit a recessed sealed 12-16 mm momentary button for the #2813, and an XT30 loop 'arming plug' that disconnects the pack for travel. Mount the IP2368 USB-C at the wall with an O-ring and silicone cap instead of an extension, which avoids CC-line problems. Add a 65-100 W PD wall charger and a 1 m 5 A C-C cable.
    - **Fix cost:** $40-70 (estimate). Panel extensions found: about $11 + $10 shipping (eBay) to $58.99 (Newegg).
    - **Evidence:** power.json final_recommendation (#2813 switch); radio_lab.final.lab_bom[48] note; radio_lab.final.lab_bom[26] (bank only).
    - **Sources:**
      - https://www.newegg.com/p/3C6-00V6-02DG1
      - https://www.ebay.de/itm/174361134723
  13.
    - **Area:** Protection ratings
    - **Components:**
      - pack fuse
      - J21 branch fuse
      - LAB 5 V fuse
      - PTCs
      - TVS
    - **Problem:** The protection table is incomplete and inconsistent:
  - Pack fuse 7.5 A vs 5 A.
  - The J21 branch is 'behind a fuse' with no value.
  - No Boni-Whip polyfuse value.
  - No TVS on the raw pack node.
  - No bias-PTC temperature derating (a 0.25 A-hold PTC at 25 C holds only about 0.17-0.19 A at 60-70 C; typical derating, unverified).
  - No fuse type or holder.
    - **Severity:** minor
    - **Fix:** Use the fuse/PTC/TVS table in budget_tables: ATM mini-blade 32 V fuses in holders, 18 AWG on the pack lead, SMBJ18A on the pack node, SMBJ14A after the 12 V regulator, SMBJ15A on the LNB port. A bias PTC (only where no TPS2553 is fitted) of 0.35-0.5 A hold at 25 C.
    - **Fix cost:** $13-25 (estimate).
    - **Evidence:** register decision #64 (fuse conflict); register decision #15 (J21 'behind a fuse'); register decision #95 (Boni polyfuse); register decision #100 (PTC hold 250 mA or more at maximum temperature).
    - **Sources:** []
  14.
    - **Area:** Flashing and recovery media
    - **Components:**
      - Radxa RA019-E1U1 UFS/eMMC reader
      - USB A-to-A cable
      - microSD rescue card
      - USB stick
      - card reader
    - **Problem:** The recovery and flashing kit is spread across files and never consolidated. storage.json gives the reader as an 'older listing ~$25'. Without the T7, offline update bundles and lab-snap need a USB stick or SD card, and neither is budgeted.
    - **Severity:** minor
    - **Fix:** One recovery kit:
  - RA019-E1U1 reader, EUR 13.00 at TinyTronics (A vs C connector differs between listings; check).
  - USB 3 A-to-A cable for edl-ng EDL on the blue port.
  - 32-64 GB A2 microSD with the rescue image.
  - USB 3 card reader.
  - 64 GB USB stick for signed offline bundles.
  Also archive the BIOS 260120 zip, edl-ng, the image and QAIRT 2.42 with SHA-256 on the home-base disk.
    - **Fix cost:** $40-55 (reader verified; rest estimate).
    - **Evidence:** storage.json (Radxa UFS/eMMC USB reader 'older listing ~$25'; microSD rescue image; edl-ng A-to-A); compute.json (EDL recovery kit); register decision #35 (lab-snap on the T7).
    - **Sources:**
      - https://www.tinytronics.nl/nl/data-opslag/modules/radxa-ufs-emmc-naar-usb-3.0-lezer-module
  15.
    - **Area:** Duplicate instrument / rule
    - **Components:**
      - NanoVNA 3 GHz (small stack)
      - LiteVNA 64 (core)
    - **Problem:** small_antenna_stack adds a NanoVNA covering 3 GHz or more ($60-130) as 'essential for tuning the helical whip ... sweep briefly indoors'. That use radiates, which breaks the receive-only rule, and the purchase duplicates the core LiteVNA 64.
    - **Severity:** minor
    - **Fix:** Drop it. Use the LiteVNA 64 conducted only, and tune antennas receive-only.
    - **Fix cost:** Saves $60-130.
    - **Evidence:** small_antenna_stack.final.revised_stack[29]; radio_lab.final.lab_bom[0]; user_requirements.md hard rule 1.
    - **Sources:** []
  16.
    - **Area:** HF chain connectors
    - **Components:**
      - Boni-Whip injector
      - 12.5 V active-antenna rail
    - **Problem:** The Boni-Whip injector is fed 'from the lab's active-antenna rail', but no output jack, cable or polyfuse value exists. The Boni-Whip current is unpublished.
    - **Severity:** minor
    - **Fix:** Fit a 2-pin locking 'ANT PWR' jack on the HF panel, with a 1-2 m DC lead to the injector. Use a 0.2 A-hold polyfuse and resize it after measuring the current. Put the labd switch and a FAULT input on MCP23017 #3.
    - **Fix cost:** $5-10 (estimate).
    - **Evidence:** lab_ui_hf.final.hf_antenna.setup ('BONI-WHIP: POWER'); register decision #95 (12.5 V; current not listed).
    - **Sources:** []
  17.
    - **Area:** HMI and audio
    - **Components:**
      - 2 push encoders
      - 6 sealed keys
      - knobs
      - VEML7700
      - RGB LED
      - piezo
      - 3.5 mm audio
      - headphones
    - **Problem:** The HMI parts are unpriced: lab_ui_hf open question 11 asks for 'part prices for the EC11 encoder, switches and knob', and mechanical gives '$10-20' for strap, buttons and encoder together. EC11-class encoders are not sealed. Audio uses the Q6A 3.5 mm jack, but there is no panel extension and no headphones. No speaker is planned, and a class-D amplifier would add switching noise near the RF bay.
    - **Severity:** minor
    - **Fix:** Budget 2 push encoders (sealed or O-ring-shafted), 6 IP67 tact keys, knobs, a VEML7700 breakout, an RGB LED and a piezo. Add a 3.5 mm panel extension and wired headphones. Fit a speaker only after a terminated-floor A/B with a linear amplifier.
    - **Fix cost:** $30-65 (estimate).
    - **Evidence:** lab_ui_hf.final open questions (item 11); lab_ui_hf (second push-encoder fix; PipeWire to the 3.5 mm jack); mechanical_thermal final_recommendation price line.
    - **Sources:** []
  18.
    - **Area:** Fasteners and consumables
    - **Components:**
      - heat-set inserts
      - screws
      - nylon screws near IMU
      - strap lugs
      - thermal pads/paste
      - KSD9700
      - AR film
    - **Problem:** There is no fastener schedule for the ASA shell: the file only says 'no heat-set inserts alone' for the tripod. Strap anchors are not defined, although 'Strap required'. The AR film needed for the 6.2:1 sun contrast is only 'e.g. TELESIN', with no price. The thermal pad grade and thickness are given only for the Lime pedestal, which is conditional.
    - **Severity:** minor
    - **Fix:** List:
  - M2.5 and M3 brass heat-set inserts for the shell joints.
  - A2 stainless screws, plus nylon or brass screws within 15-20 cm of the IMU.
  - 2 metal strap lugs bonded to the plate, a hand strap and a sling strap.
  - Pads of 1-2 mm and 3-6 W/mK for the UFS and IP2368, and paste for the SoC.
  - A KSD9700 70 C switch on the IP2368.
  - A 7in AR film of about 0.7% reflectance.
    - **Fix cost:** $55-105 (estimate).
    - **Evidence:** mechanical_thermal.json verify (tripod note; M2.5 standoffs; 'Strap required'); display_market.final.sunlight_measures; power.json (KSD9700).
    - **Sources:** []
  19.
    - **Area:** Bags and spares
    - **Components:**
      - antenna roll/pouch
      - Yagi element tube
      - 10-12 L sling
      - antenna spares
      - spare Q6A
    - **Problem:** Bags and spares are unpriced or uncounted:
  - foldable_antennas says the kit 'fits a 35 x 25 x 10 cm pouch', unpriced.
  - Foldable step 10 lists spares (telescopic pair, 2 x 70 cm elements, a petal, clips, a spare spool), unpriced.
  - The register's 'budget a spare board' for the Q6A is in no total.
  - The petals and gores have sharp 0.3-0.5 mm aluminium edges and need a padded roll.
    - **Severity:** minor
    - **Fix:** Buy a padded antenna roll, an element tube and a 10-12 L sling. Use a second RTL-SDR Blog dipole kit as the source of spare telescopic elements. A spare Q6A 12 GB is optional.
    - **Fix cost:** $68-113 (bags $50-95 estimate, dipole kit $17.95 in files); spare Q6A $189.99 (optional).
    - **Evidence:** foldable_antennas.final.total_packed_volume_and_weight; foldable build_and_test_steps[9]; register decision #22.
    - **Sources:** []
  20.
    - **Area:** Build tools
    - **Components:**
      - calipers
      - sheet-metal snips/deburr
      - M5 tap/die
      - heat gun
      - coax crimper
      - enclosed 3D printer for ASA
    - **Problem:** The antenna and case build needs tools that no list includes:
  - Calipers, for the LNB neck and waveguide ID (16.8-21.9 mm) that 'must be measured first', and for the helix geometry.
  - Snips and a deburring tool for the petals and gores.
  - An M5 tap and die for rod couplers.
  - A heat gun for adhesive heat-shrink.
  - A crimper, unless jumpers are bought ready-made.
  - An enclosed printer for ASA. Whether the user owns a 3D printer is unknown.
    - **Severity:** minor
    - **Fix:** Add a tool list. Use a print service for the ASA shell if there is no enclosed printer.
    - **Fix cost:** $80-140, plus a $30-80 print service if needed (estimates).
    - **Evidence:** register decision #106 (measure LNB neck and waveguide on arrival); foldable build steps 1-5; radio_lab.final.lab_bom[22] (only drivers, cutters, stripper, tweezers).
    - **Sources:** []
  21.
    - **Area:** Inconsistent LNA powering
    - **Components:**
      - SAWbird+ GOES on the helicone
    - **Problem:** foldable_antennas build step 3 powers the SAWbird+ GOES '5 V through its micro-USB, with a DC block before the Lime'. That needs a 5 V cable run to the feed, and it puts DC on the RF output. It contradicts the register rule that every SAWbird+ is fed through a coax injector from a TPS2553.
    - **Severity:** minor
    - **Fix:** Strike the micro-USB step. Power the LNA over the coax from the internal bias board.
    - **Fix cost:** $0
    - **Evidence:** foldable_antennas.final.build_and_test_steps[2]; register summary ('every SAWbird+ runs from a TPS2553 at 250-300 mA'); rf_frontend verify (micro-USB-powered SAWbird leaks DC to RF out).
    - **Sources:** []
  22.
    - **Area:** Puck, GNSS and service access
    - **Components:**
      - IMU puck enclosure/connector/cable
      - GNSS IPX-SMA pigtail + external antenna
      - RJ45/UART service access
      - Wi-Fi antennas
    - **Problem:** The puck's 'sealed boom connector', its 1-2 m cable and its enclosure or shield are unpriced. The external GNSS antenna 'on a 1-3 m lead' needs an IPX-to-SMA bulkhead and a cable antenna. The Waveshare kit ships with a ceramic active antenna, connector unconfirmed. The register's 'Keep UART access in the case' and storage's 'offload over GbE' have no hatch or panel part. Whether the FCU760K Wi-Fi needs U.FL antennas is not recorded.
    - **Severity:** minor
    - **Fix:** Puck: GX12 4-pin pair plus 2 m shielded 4-core cable and a shield can. GNSS: IPX-SMA bulkhead pigtail plus an active antenna with a 3 m SMA lead, if the antenna is not on the lid. Add a service hatch with UART and RJ45 access, or a panel RJ45 extension. Confirm the Wi-Fi antenna provision from the schematic.
    - **Fix cost:** $30-55 (estimate).
    - **Evidence:** radio_lab.integ.connections (H2 'sealed boom connector'); gnss_imu verify (external active antenna 1-3 m lead); register decision #22; storage.json (GbE offload).
    - **Sources:**
      - https://www.waveshare.com/LC76G-GNSS-Module.htm
  23.
    - **Area:** Carried weight
    - **Components:**
      - sling kit
    - **Problem:** The register's sling figure of 3.7-4.4 kg leaves out the supports, coax set, bag and weather kit. With them the sling is 4.4-6.05 kg, or 5.0-6.7 kg with the 630 g PD bank (model).
    - **Severity:** minor
    - **Fix:** Restate the weights in STACK.md. Offer a light patch-tier sling (whips, 4-turn helix, bare LNB, about 0.6-0.9 kg of antennas) as the everyday kit.
    - **Fix cost:** $0
    - **Evidence:** register decision #71; foldable_antennas.final.total_packed_volume_and_weight; /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/missing_calc/b.py.
    - **Sources:** []
- **Proposed decisions:**
  1.
    - **Question:** C1 LimeSDR Micro keep or drop
    - **Decision:** Gated optional. Keep the cancellable pre-order, confirm it is a refundable store order, and decide on 31 Jan 2027 or on delivery. Buy no Lime-only parts before the gate: R44SF $19, MHF4 tool $18.10, 2x MHF4L-SMA $12, REF IN, port DC blocks and pads, VLM-33-S+, cavity.
    - **Reason:** No core receive function needs it. The M.2 slot can take it later. The deposit is refundable before shipping.
    - **Consequences:** Its dependents are tagged conditional: RAM ring, T7, CPU7, LIME profiles, riser, 7.5 A fuse, sled COM. The core input selectors (RTL-A/B SP4T) are needed either way.
    - **Alternatives rejected:** Drop now: loses S-band and the 56 Msps NPU data with no saving that cannot be recovered. Firm keep: the driver is validated on x86 only.
  2.
    - **Question:** C2 Q6A RAM tier
    - **Decision:** Buy the 12 GB board now ($189.99, Allnet) and re-check stock on the order date. Budget RAM at 1.5 GiB or less for the ring without the Lime, and 4 GiB with it.
    - **Reason:** RAM cannot be added later, and the cost is only about $65-75 more than 8 GB.
    - **Consequences:** The 8 GB board is used only if the Lime is dropped before purchase.
    - **Alternatives rejected:** 8 GB board (would close the training and Lime options).
  3.
    - **Question:** C3 Pack 3S vs 4S
    - **Decision:** 4S1P P50B (72 Wh) with a regulated 12 V rail into J21. Cells come from NKON (EUR 6.75 incl. VAT each) or another established EU/US seller, plus 1 spare. The pack is welded by a shop or pack builder.
    - **Reason:** The 13.2 V LNB, 12.5 V Boni-Whip LDO, AUX 12 V and ENR stability all need headroom above 12 V.
    - **Consequences:** The LNB regulator must be buck-boost (see C8). Fuse is 5 A without the Lime and 7.5 A with it.
    - **Alternatives rejected:** 3S: needs a boost for every 12 V or higher load.
  4.
    - **Question:** C4 12 V regulator
    - **Decision:** Buy the D36V50F12 ($39.95) with the EN hardware cut at 13.4 V or above. Replace it with a forced-PWM buck-boost rated 5 A or more only if the terminated-floor A/B shows wandering spurs, or the sealed-case current test fails at 3.5 A.
    - **Reason:** It is the only verified, priced part. The model load is 3.5 A (42 W).
    - **Consequences:** Its 13.3 V dropout fixes the cut-off order: Linux at 13.6 V, then the hardware cut at 13.4 V.
    - **Alternatives rejected:** 9 V into J21 (based on a misplaced-TVS reading).
  5.
    - **Question:** C5 USB port map
    - **Decision:** Freeze the Lime-agnostic map:
  - Blue port: RTL-A, or the T7 if the Lime is kept.
  - FE1.1s P1: RTL-B. P2: touch. P3: CH334F.
  - CH334F: H1 HMI RP2040, H2 IMU puck, H3 LAB USB-A, H4 HF+, each through soldered pigtails (the board has pads only).
  With the Lime and T7, the IMU moves to the UART7 relay so that H2 can take RTL-A.
    - **Reason:** The CH334F has no USB-A ports (Adafruit page). The model FE1.1s load is 13.4 MB/s, 38% of 35 MB/s.
    - **Consequences:** Zero spare ports in the core; a 4th V4L can go only on LAB USB.
    - **Alternatives rejected:** A second CH334F (adds a 12 MHz harmonic source and hub depth).
  6.
    - **Question:** C6 40-pin header and bus map
    - **Decision:** Adopt the register map: PPS on pin 7, UART6 on 16/18, I2C0 for the INA228 only, I2C2 for the MCP23017s. Add MCP23017 #3 at 0x22 for the extra lines. The IMU uses USB-CDC on CH334F H2 until UART7 is proven. Fan PWM on pin 33 after the test, else GPIO56.
    - **Reason:** The core needs 24 control lines against 16 on one expander. UART7 is unverified.
    - **Consequences:** One extra $5.95 part and one I2C address.
    - **Alternatives rejected:** Header GPIOs for bias enables (the header is already crowded).
  7.
    - **Question:** C7 Hardware ownership
    - **Decision:** labd is the sole owner of the GPIO, expanders, selectors, bias and LNB. labrx owns the single ring and recorder. labclassify runs inferd and fusiond. rflab becomes a labd module.
    - **Reason:** Two owners of the same hardware lines cannot be made safe.
    - **Consequences:** The new selector and relay lines get labd leases and safe defaults.
    - **Alternatives rejected:** flock-based sharing.
  8.
    - **Question:** C8 LNB supply
    - **Decision:** A SEPIC or buck-boost (Pololu S18V20AHV class) set to 13.2 V ±0.2 V, then a second #2813 as true disconnect, then LC, a PTC, and an SMBJ15A at the F port. No 18 V branch. Set one current limit at 1.5-2x the measured draw. The internal LNB tee inductor is rated 1 A or more.
    - **Reason:** A boost cannot step a 12-16.8 V pack down to 13.2 V. Pololu says the SEPIC output is not fully disconnected when EN is low.
    - **Consequences:** About $40-50. Acceptance test: 0 V at the port when off.
    - **Alternatives rejected:** MT3608/XL6009 or TPS65233-class boost; switching with a TPS2553.
  9.
    - **Question:** C9 LNA bias rule
    - **Decision:** Each SAWbird+ gets a TPS2553 at 250-300 mA. Every bias tee is rated 0.5 A or more. The V4L tee is used only for LNAs of 80 mA or less. The TCBT-14+ (200 mA) is allowed only on lines of 80 mA or less.
    - **Reason:** A tee rated below the current limit is the weak link in a fault.
    - **Consequences:** The DIY bias board needs a conducted VNA check.
    - **Alternatives rejected:** The 100-160 mA PTC; the GOES+ on the V4L tee.
  10.
    - **Question:** C10 FM filter
    - **Decision:** Flamingo+ FM. Buy 2: one at the 137 MHz entry and one at the 2 m entry, each ahead of its LNA.
    - **Reason:** The patch tier has two VHF entry points, and the SAWbird+ NOAA blocks 145.8 MHz.
    - **Consequences:** +$24.95. The 70 cm path uses a BPF instead.
    - **Alternatives rejected:** One filter moved by hand; the RTL-SDR Blog band-stop (no DC rating published).
  11.
    - **Question:** C11 librtlsdr
    - **Decision:** Use only the .so.2 rebuild of noble 2.0.1 with commits 0204c9c and 65f0658, held. Delete the other recipes.
    - **Reason:** It keeps the consumers' ABI.
    - **Consequences:** First arm64 build on the Q6A.
    - **Alternatives rejected:** 2.0.3 .so.0; purge and fork.
  12.
    - **Question:** C12 Display field clock
    - **Decision:** 127.9 MHz (51.7 Hz, 2200x1125), or 164.4-168.4 MHz if the panel accepts it. Use a shielded 10-15 cm HDMI with Mix 31/61 ferrites.
    - **Reason:** 128.70 MHz has harmonics at 1544.4 and 1415.7 MHz.
    - **Consequences:** Change all files and the cmdline together.
    - **Alternatives rejected:** 128.70 MHz; 1080p60.
  13.
    - **Question:** C13 Kernel and PPS
    - **Decision:** Out-of-tree pps-gpio built as a DKMS deb on 6.18.2-4. Build pps-ldisc too, only if the FT232RL fallback is kept.
    - **Reason:** CONFIG_PPS=y is set on the held kernel.
    - **Consequences:** Route B (7.0.11) is dropped.
    - **Alternatives rejected:** Moving to the 7.0.11 kernel.
  14.
    - **Question:** C14 INA228
    - **Decision:** I2C0, user-space i2c-dev, no DT binding. Shunt in the pack lead ahead of the IP2368 tap.
    - **Reason:** A bound driver blocks access to the CHARGE register.
    - **Consequences:** Fix power.json and npu_training.
    - **Alternatives rejected:** The ina238 hwmon driver on i2c6.
  15.
    - **Question:** C15 Antenna tiers
    - **Decision:** Two tiers. The LRPT default is the V-dipole; the Yagi defaults to the ultra-compact build. Reverse the small-stack removals: Lime gated, T7 tied to the Lime, 12 GB kept. Strike the loops. Supports (tripod 35 cm or less folded, tent-pole mast) are in the foldable kit.
    - **Reason:** The governing size rule allows folded pieces of 35 cm or less.
    - **Consequences:** Sling weight 4.4-6.05 kg (model).
    - **Alternatives rejected:** Small-stack-only removals.
  16.
    - **Question:** C16 Policy leftovers
    - **Decision:** Strike everything listed before STACK.md:
  - VNA S11 into antennas, and the small-stack NanoVNA purchase.
  - Inmarsat-C decode-then-filter.
  - VLF SID.
  - BT rfkill and the Artemis stop (add both).
  - Voice IQ and Set B.
  - Iridium IRA/IBC and CARTOSAT-3.
  - H-probes.
  - City lists and Kyiv constants.
  - wsjtx GUI and fldigi.
  - The bearing log.
    - **Reason:** Each item breaks the rules in user_requirements.md.
    - **Consequences:** Saves $60-130 (NanoVNA) and $50-109 (H-probes).
    - **Alternatives rejected:** Keeping them with warnings.
  17.
    - **Question:** C17 HF antenna chain
    - **Decision:** Boni-Whip at 12.5 V via an LDO, behind an ANT PWR jack with a 0.2 A polyfuse (resize after measuring). HF+ selector: a latching relay pair accepted at 35 dB or more of conducted isolation at 162-260 MHz. Ask the user to confirm the HF-loop removal.
    - **Reason:** The selector was missing from the BOM, and commercial latching SMA relays are $242 or more with 12/28 V coils.
    - **Consequences:** $15-35 extra.
    - **Alternatives rejected:** HMC241 (DC blocks hurt LF); Radiall/Pasternack relays.
  18.
    - **Question:** C18 Storage
    - **Decision:** T7 only with the Lime. Otherwise a 64-128 GB A2 microSD plus a USB stick for bundles, with the rescue and A/B layout on UFS. Retention: products by default, raw only when pinned.
    - **Reason:** The no-Lime peak is 16.4 MB/s.
    - **Consequences:** The flashing kit must include an SD card and a stick.
    - **Alternatives rejected:** Buying the T7 unconditionally.
  19.
    - **Question:** C19 CPU allocation
    - **Decision:** A55: UI, daemons and CPU inference. CPU4-6: DSP and T2 between passes. CPU7 isolated only with the Lime.
    - **Reason:** T2 is 4.5-10.8 min on the A78 cores (model).
    - **Consequences:** Fix lab_ui_hf.
    - **Alternatives rejected:** Trainer on the A55 cores.
  20.
    - **Question:** C20 Roadmaps
    - **Decision:** NPU Phase 0 inside the W1-2 gates (19 Oct-1 Nov 2026). Minimal labeller in P0b. HF-F and second-RTL profiles before the HF classes are shown in the UI.
    - **Reason:** The labeller is needed about 3 months before the UI schedules it.
    - **Consequences:** The schedules in STACK.md are merged.
    - **Alternatives rejected:** Keeping two separate roadmaps.
  21.
    - **Question:** C21 V4L count
    - **Decision:** Buy 3: 2 in service plus 1 spare. Monitoring time-shares a receiver, or AIS runs on the HF+. A 4th ($37.95) only for continuous monitoring, on LAB USB.
    - **Reason:** R828S stock is finite, and there are no spare ports.
    - **Consequences:** $113.85.
    - **Alternatives rejected:** Using the spare as a full-time monitor.
  22.
    - **Question:** C22 Software recipes
    - **Decision:** One venv per tool, as in the register: NanoVNA-Saver via pipx, PySide6 6.12, libgpiod v1, Skyfield 1.55 from pip, SatDump 2.0-alpha from source.
    - **Reason:** These are the versions available in noble.
    - **Consequences:** Each is tested on the Q6A within the return window.
    - **Alternatives rejected:** apt nanovna-saver 0.6.3; libgpiod v2.
  23.
    - **Question:** C23 Region unknown
    - **Decision:** Hold the region-dependent purchases until the user names the region: LNB, horn materials, SAWbird+ iO, MAX-M10S. Everything else is bought at world prices.
    - **Reason:** GEO visibility depends on the region.
    - **Consequences:** QO-100 parts are about $35-90 deferred.
    - **Alternatives rejected:** Assuming Europe.
  24.
    - **Question:** C24 Costs and weights
    - **Decision:** Recompute with the missing-parts list: about $870-1,520 gross, about $830-1,450 net of lines already partly budgeted (mostly estimates). Sling 4.4-6.05 kg.
    - **Reason:** Cables, supports, weather parts, tools, the pack build and recovery media were never budgeted.
    - **Consequences:** The P5 analog search should include these lines.
    - **Alternatives rejected:** Keeping the old subtotals.
  25.
    - **Question:** C25 P1b completion
    - **Decision:** report_research.json now exists (minute-log 04:52). Still to do: add errata blocks to summaries.md and minute-log.md. grep finds no 'errata' in either file.
    - **Reason:** Uncorrected entries can propagate into P2 through digest.md.
    - **Consequences:** A small task before STACK.md.
    - **Alternatives rejected:** None.
  26.
    - **Question:** Lens: how chains are routed to the two RTLs and the HF+
    - **Decision:** Internal SP4T selectors on both RTLs, a latching relay pair for the HF+, and MCP23017 #3 for the extra control lines.
    - **Reason:** The one-touch menu wish needs software routing. Manual swaps would mean opening the sealed RF bay.
    - **Consequences:** $40-65. Isolation of 30-37 dB is enough for chain selection but not for an A/B leakage test.
    - **Alternatives rejected:** Manual swaps only; ZSWA4-63DR+ at $307.32 each.
  27.
    - **Question:** Lens: tripod mount implementation
    - **Decision:** An aluminium boss of 10-12 mm with a steel 1/4-20 insert, bolted to the plate.
    - **Reason:** A 2 mm plate gives only 1.57 engaged threads.
    - **Consequences:** About +15 g.
    - **Alternatives rejected:** A thread tapped in the plate; heat-set inserts in ASA.
  28.
    - **Question:** Lens: ingress target vs thermal physics
    - **Decision:** IPX4/IP54 with baffled, filtered intakes and ePTFE vents, not IP67.
    - **Reason:** The case must shed 11-32 W internal plus 13.5-17 W solar, so it needs forced air.
    - **Consequences:** Rain operation uses LOCK plus the encoder. The LNAs go in IP65 boxes.
    - **Alternatives rejected:** A sealed passive case (would overheat); no protection at all.
  29.
    - **Question:** Lens: home-base PC minimum
    - **Decision:** Any x86-64 machine with an ubuntu:22.04 / Python 3.10 container for QAIRT 2.42. A GPU (12 GB class) only for T3 training.
    - **Reason:** The QAIRT 2.42 converter is x86-64 only, and the CPU and on-device paths carry the system without a GPU.
    - **Consequences:** With no GPU, the detector is not retrained locally.
    - **Alternatives rejected:** ARM conversion; cloud training with private captures; an untested WSL2 setup as the only path.
- **Budget tables:**
  - CURRENT PER RAIL (model; 4S, cut-off 13.6 V, 90% efficiency)
  | Rail | Loads | Est. max | Protection |
  |---|---|---|---|
  | Pack 12.0-16.8 V | all | 2.61 A no-Lime peak 32 W; 4.25 A Lime peak 52 W; Pinecil 3.16 A (receiver off) | ATM 5 A (52-63%) / 7.5 A (57%); BMS 15-20 A |
  | 12 V D36V50F12 | Q6A 2.0 A, display ≤0.75 A, AUX ≤0.75 A | 3.5 A = 42 W (3.43 A input) | J21 branch 3.15 A fuse (proposal), display 1.5 A limit, AUX 0.75 A PTC |
  | LAB 5 V D36V28F5 (3.2 A) | hub 0.05, puck 0.10, HMI 0.05, HF+ ≤0.20 (unpublished), LAB port ≤1.0, 2x SAWbird+ 0.36, LNA V2 0.08, blower 0.10 | 1.94 A (61%); 0.79 A input | 2 A input fuse; TPS2553 1 A (LAB) / 250-300 mA (each LNA) |
  | LNB 13.2 V SEPIC | Bullseye 0.2-0.3 A (unpublished) | ≤4 W | 1.5-2x measured; #2813 disconnect; SMBJ15A |
  | Boni 12.5 V LDO | current unpublished | — | 0.2 A PTC (proposal) |
  - FUSE / PTC / TVS (proposal)
  | Point | Part | Rating |
  |---|---|---|
  | Pack lead | ATM mini-blade, 32 V | 5 A (no Lime) / 7.5 A (Lime), 18 AWG |
  | J21 branch | ATM | 3.15 A |
  | LAB 5 V input | ATM | 2 A |
  | Pinecil lead | inline | 5 A |
  | AUX 12 V | PTC | 0.75 A hold |
  | LNA bias (no TPS2553) | PTC | 0.35-0.5 A hold at 25 C (derates to about 0.25 A at 60-70 C) |
  | Pack node | SMBJ18A | standoff 18 V |
  | After 12 V regulator | SMBJ14A | — |
  | LNB F port | SMBJ15A | — |
  - USB PORTS AND BANDWIDTH
  | Port | Device | MB/s |
  |---|---|---|
  | Blue USB 3.1 | RTL-A (or the T7 with the Lime) | 5.12 (T7: up to 224) |
  | FE1.1s P1 | RTL-B | 5.12 |
  | FE1.1s P2 | touch | ~0 |
  | FE1.1s P3 | CH334F: HMI, puck, LAB, HF+ | 3.1 + LAB |
  | LAB USB | 2nd V4L or one instrument | 5.12 |
  FE1.1s total 13.4 MB/s, 38% of 35 MB/s. Spare ports: 0.
  - CONTROL LINES
  | Group | Out | In |
  |---|---|---|
  | LAB/AUX EN, 3 VBUS cuts | 5 | 1 |
  | 4 bias EN plus FAULT | 4 | 4 |
  | LNB EN/PG, Boni EN/FAULT | 2 | 2 |
  | HF+ relay set/reset, 2x SP4T V1/V2 | 6 | 0 |
  | Total | 17 | 7 = 24 lines, against 16 on MCP23017 #1, so add #3 (0x22) |
  - POWER AND RUNTIME (register figures, models)
  | Mode | W | h on 72 Wh at 85% |
  |---|---|---|
  | No Lime, single RTL | 11-17 | 3.6-5.6 |
  | QO-100 or dual RTL | 13-21 | 2.9-4.7 |
  | No-Lime peak | 24-32 | 1.9-2.6 |
  | Lime typical | 25-28 | 2.2-2.4 |
  | Lime peak | 45-52 | 1.2-1.4 |
  - RAM (12 GB board, about 11 GiB visible (unverified); app sizes are estimates)
  | Item | No Lime | Lime |
  |---|---|---|
  | OS + labwc + Lab Shell | 1.5-2 | 1.5-2 |
  | SatDump / SDRangel / OWRX+ | 1.3-2.5 | 1.3-2.5 |
  | Ring | ≤1.5 | 4 |
  | inferd-htp + cpu | 1.3 | 1.3 |
  | Trainer | ≤2 | ≤2 |
  | Total | 7.6-9.3 | 10.1-11.8 (tight) |
  - CPU
  | Cores | Use |
  |---|---|
  | CPU0-3 A55 | UI, daemons, NPU host, ORT fallback |
  | CPU4-6 A78 2.4 GHz | DSP, labrx, T2 between passes |
  | CPU7 A78 2.7 GHz | lime:Rx0 only with the Lime, otherwise free |
  - STORAGE (UFS 128 GB, estimates)
  | Item | GB |
  |---|---|
  | OS, apps, venvs, QAIRT runtime | 20-28 |
  | NPU dataset quota | 20 |
  | Offline map tiles (not budgeted in any file) | 2-10 |
  | Models, journald | 0.4 |
  | Left for recordings | 62-78, i.e. 1.7-2.1 h of dual-RTL raw at 36.9 GB/h |
  - CARRIED WEIGHT (sling, model)
  | Item | kg |
  |---|---|
  | Handheld (no Lime) | 1.05-1.25 |
  | Foldable kit + LNB + LNAs + jumpers | 1.3-1.8 |
  | HF wire kit | 0.4 |
  | 2 L pouch | 0.8 |
  | Tripod + mast | 0.35-0.9 |
  | Coax set | 0.15-0.3 |
  | Bag | 0.3-0.5 |
  | Weather kit | 0.05-0.1 |
  | Total | 4.4-6.05 (5.0-6.7 with the PD bank) |
  - CABLE SCHEDULE (proposal; prices are estimates)
  | Run | Type | Length | Qty |
  |---|---|---|---|
  | Bulkhead to internal (137, 2 m, 70 cm, L-band, HF, VHF-AIS) | SMA-F bulkhead to SMA-M RG316 | 10-15 cm | 6 |
  | LNB port | F-F bulkhead + 75 ohm lead to the tee | 10 cm | 1 |
  | GNSS external | IPX to SMA-F bulkhead | 10 cm | 1 |
  | V4L USB | A-M to A-F + ferrite | 15 cm | 2 |
  | FE1.1s P3 to CH334F | A-M to C-M, VBUS cut | 10 cm | 1 |
  | CH334F pads | panel USB-A / HF+ plug / RP2040 USB-C / puck GX12 | 5-15 cm | 4 |
  | Touch | USB with VBUS cut | 15 cm | 1 |
  | HDMI | shielded micro-coax + Mix 31/61 | 10-15 cm | 1 |
  | Feed LNA to handheld | RG316 SMA-M/M (about 0.5 dB/m at 137 MHz, 1.3 dB/m at 1.7 GHz, after the LNA) | 1-2 m | 4 |
  | LNB | 75 ohm thin F-F | 1 m | 1 |
  | HF | RG174 + Mix 31 clamps (in the HF kit) | 5-10 m | 1 |
  | Boni-Whip | BNC lead + BNC-SMA + DC lead | 1-2 m | 1 each |
  | Adapters | SMA M-M (A-V85), F-SMA, SMA barrels | — | set |
  | EDL | USB 3 A-A | 1 m | 1 |
  - MISSING-PARTS COST (USD, mostly estimates)
  | Group | $ |
  |---|---|
  | Selectors, expander, current monitors, bias board | 61-121 |
  | LNB SEPIC + disconnect | 40-50 |
  | Filters (2nd Flamingo+, filter bank) + pads | 102-117 |
  | Cables and adapters | 90-170 |
  | Panel connectors, power key | 23-45 |
  | Pack cells, sundries, welding, ISDT 608PD ($32.99-42.99) | 103-148 |
  | Protection parts | 13-25 |
  | Mechanical and thermal consumables | 55-105 |
  | Weather kit | 45-110 |
  | Supports | 55-150 |
  | Bags and antenna spares | 68-113 |
  | Tools | 80-140 |
  | Flashing media | 40-55 |
  | HMI, audio, puck | 35-80 |
  | Wall PD charger | 35-60 |
  | Total | about 870-1,520 gross (about 830-1,450 net) |
  Optional: GPU EUR 298 to about $500; spare Q6A $189.99; print service $30-80.
  - HOME-BASE PC
  | Need | Minimum | Recommended |
  |---|---|---|
  | CPU/OS | any x86-64; ubuntu:22.04 container, Python 3.10 (untested) | same |
  | GPU | none (conversion only) | 12 GB NVIDIA (RTX 3060 class) |
  | RAM | 16 GB | 32-64 GB |
  | Disk | 50 GB free | 1-2 TB NVMe + 2-4 TB backup |
  | Link | Wi-Fi | GbE to the device (needs RJ45 access on the case) |
- **Checks passed:**
  - The core lab RF accessories are specified with verified prices in radio_lab.final.lab_bom[5]-[12]: Nooelec pad kit $47.95, 2x BLK-89-S+ at $20.26, 3x ANNE-50+ at $14.84, 086-6SM+ at $16.67, OSL, torque wrench $35.89.
  - The LAB 5 V rail fits the D36V28F5: 1.94 A of 3.2 A (model), drawing 0.79 A at the input against its 2 A fuse.
  - The 12 V rail load of 3.5 A (42 W) sits within the D36V50F12's published 2.3-6.5 A range. A sealed-case test is still required.
  - Pack fuse loading is reasonable (model): 7.5 A runs at 57% at the 52 W Lime peak; 5 A runs at 52% at the 32 W no-Lime peak and 63% with the Pinecil.
  - USB 2.0 tree load is 13.4 MB/s, 38% of the practical 35 MB/s, even with a second V4L on LAB USB.
  - A spares kit exists (radio_lab lab_bom[23], $80-130): fuses, XT30, SMBJ14A, a spare IP2368, CR2032, RP2040-Zero, pigtails, barrels, a DC block, M2.5 hardware, thermal pads, Kapton.
  - Bench tools and ESD control are covered: Mako kit, cutters, stripper, ESD mat, Pinecil with a 5 A fused lead and IronOS Bluetooth off.
  - The transport case is specified: Pelican 1450, interior 37.1x25.8x15.2 cm, with the 35 cm Yagi pieces fitting. The PD bank and the back-power-protected bench hub are covered.
  - Cooling hardware is specified: Armor case or copper block, NF-A4x10 5V PWM, a 5 V blower, AO3400 drive. The printed sun hood, IR film and light bezel are in mechanical.
  - The QAIRT 2.42 host requirement (x86-64, Ubuntu 22.04, Python 3.10) is consistent across npu_training and the register.
  - New world prices this session: P50B EUR 6.75 incl. VAT at NKON (31 Jul 2026); ISDT 608PD $32.99-42.99; Radxa RA019-E1U1 reader EUR 13.00 at TinyTronics. These replace UAH-only or stale prices.
  - The Waveshare LC76G ships with an active ceramic antenna and has an MS621FE backup cell, so the lid-patch option needs no extra antenna.
- **Notes:** I read user_requirements.md and the full register in report_research.json: summary, 143 decisions, compliance, corrections, the 25 conflicts and the open questions. I also read the verdict notes and the cross-system conflicts. For my lens I read radio_lab.final (lab_bom, totals, usb_power_case_plan, connections, stack_changes), the foldable kit, totals and steps, small_antenna_stack.revised_stack, and the power, mechanical, GNSS, display and NPU hardware sections. I grepped all final/*.json files for about 60 part terms.
  
  Main finding: the studies cover instruments and the main modules well. What is missing is the layer between them:
  - Input routing and its control lines.
  - Correctly rated bias tees.
  - A buck-boost LNB supply. On 4S, every boost option named in the files is wrong.
  - A cable and adapter schedule.
  - A filter matrix with a real 2 m path.
  - The pack-building process, supports, weather protection, tools, bags, recovery media and the home-base PC.
  
  Web use was 10 searches and 4 fetches. Many accessory prices are still estimates and are marked as such.
  
  Unverified:
  - HF+ Discovery USB connector type.
  - S18V20AHV price.
  - HMC7992 board logic levels.
  - Bias-tee and relay parts beyond the TCBT-14+ 200 mA rating.
  - RTX 3060 October prices (latest data is July 2026: EUR 298 in France to about $500 at US retail).
  - Container use for QAIRT 2.42.
  
  Calculation scripts: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/missing_calc/b.py and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/missing_calc/cost.py. All their outputs are models.
  
  Sources:
  - https://www.adafruit.com/product/5997
  - https://www.pololu.com/product/2577
  - https://www.nkon.nl/rechargeable/molicel-inr21700-p50b-5000mah-50a.html
  - https://racedayquads.com/products/isdt-608pd-240w-10a-1-6s-dc-smart-charger-black
  - https://www.tinytronics.nl/nl/data-opslag/modules/radxa-ufs-emmc-naar-usb-3.0-lezer-module
  - https://www.minicircuits.com/pdfs/TCBT-14+.pdf
  - https://www.datasheets.com/radiall/r570342100
  - https://www.guru3d.com/story/geforce-rtx-3060-12gb-prices-reportedly-jump-after-relaunch/
  - https://gpuprix.com/zh/france/gpus/geforce-rtx-3060-12gb
  - https://www.waveshare.com/LC76G-GNSS-Module.htm
  - https://anatechelectronics.com/435-mhz-band-pass-filter-9531.html
  - https://www.newegg.com/p/3C6-00V6-02DG1</notes>
  </invoke>
  

## completeness:lens1 (run `wf_6ce87eb1-883`)

- **Lens:** GOALS + CAPABILITIES. I went through each goal in the patch/chip tier and the foldable tier, then through the radio lab, the NPU training system and the touch menu. For each I checked coverage, margin and evidence, and looked for claims that are unverified, model-only, stale or contradictory.
- **Issues:**
  1.
    - **Area:** Inmarsat-C EGC SafetyNET (both tiers)
    - **Components:**
      - sdrangelsrv Inmarsat C demodulator
      - labd EGC allow-list
      - stdcdec / Scytale-C
    - **Problem:** The planned backend filters only after decoding, which breaks the header-level rule (user_requirements.md line 37).
  - SDRangel's Inmarsat C plugin has only regex display filters on the decoded Type and Message columns.
  - Its Messages table, UDP forwarding and CSV logging apply to every received packet.
  - lab_ui_hf menu_tree[17] routes 'sdrangelsrv Inmarsat C -> UDP -> labd EGC SafetyNET allow-list'. So every packet is assembled and leaves the demodulator before the SafetyNET check.
  - The same leaf defaults to the undecided Lime RX1 and a SAWbird iO.
    - **Severity:** blocker
    - **Evidence:** SDRangel demodinmarsat readme (fetched 18 Oct 2026): filters match 'values displayed in the Type column' and the Message column; UDP and CSV apply to received packets in general. lab_ui_hf.json final.ui_system.menu_tree[17]. report_research register decision #2 and open_questions[17].
    - **Fix:** Fork one decoder (SDRangel demodinmarsat or stdcdec):
  - Parse only the packet type and service code.
  - Drop every non-SafetyNET packet, FleetNET included, before payload reassembly.
  - Compile out the Messages table, CSV and UDP output for all other types.
  - Unit-test on a mixed NCS recording.
  Make the V4L the default device. Ship the profile disabled until the test passes; if it never passes, drop Inmarsat-C.
    - **Fix cost:** About 3-5 developer days (estimate); $0 in hardware
    - **Sources:**
      - https://github.com/f4exb/sdrangel/blob/master/plugins/channelrx/demodinmarsat/readme.md
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  2.
    - **Area:** Receive-only rule: VNA in the menu and antenna checks
    - **Components:**
      - Lab Shell Instruments > VNA
      - foldable_antennas steps
    - **Problem:** The VNA leaf (menu_tree[56], 'Quick SWR/S11 page (huge readout)') is not gated by Bench mode; only the signal-generator leaf [58] is. An SWR page invites antenna sweeps, and those radiate.
  
  foldable_antennas also has radiating checks beyond the build steps 2-5 that the register lists:
  - foldable_kit[0]: 'VNA-tune it'.
  - loss_table[1]: 'one VNA check per re-mark'.
  - Build step 10: 'recheck S11 after every trip'.
    - **Severity:** blocker
    - **Evidence:** lab_ui_hf.json menu_tree[56] vs [58]; foldable_antennas.json final.foldable_kit[0], loss_table[1] and [11], build_and_test_steps[9]; user_requirements.md rule 1.
    - **Fix:** Allow the VNA leaf only inside Bench mode, with the same 1.5 s 'antenna disconnected' hold. Rename it 'Conducted S11/S21 (DUT only)'. Replace every antenna S11 check with receive-only checks: beacon C/N within 1 dB, terminated-vs-antenna noise rise, and GNSS C/N0.
    - **Fix cost:** $0 (edit)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
  3.
    - **Area:** Policy leftovers still in the FINAL menu and lab capabilities (confirmed in file)
    - **Components:**
      - lab_ui_hf menu
      - radio_lab capabilities
    - **Problem:** These leftovers are still in the final files:
  - menu[32] 'SID ... VLF/LF carrier-amplitude logging' and hf_capabilities[7]: VLF is dropped by rule.
  - menu[98] 'Radios off/on' and menu[34] 'HF Quiet' turn off Wi-Fi only; Bluetooth stays on.
  - menu[65] 'Tap a label for the offline Artemis entry' has no military/government stop.
  - menu[47] keeps an IMU bearing log in 'Interference hunt'.
  - menu[59] 'Power meter (model TBD)'.
  - radio_lab capabilities[16] installs WSJT-X and fldigi, both TX-capable.
  - radio_lab capabilities[1] claims 'visible to 12 GHz' with no source.
    - **Severity:** blocker
    - **Evidence:** lab_ui_hf.json final.ui_system.menu_tree[32,34,47,59,65,98] and final.hf_capabilities[7]; radio_lab.json final.capabilities[1,16]; register decisions #3, #8, #10, #12, #135.
    - **Fix:** Apply the register's fixes:
  - SID limited to DCF77/MSF/WWVB/JJY/TDF, amplitude only.
  - rfkill blocks wlan AND bluetooth.
  - Artemis stop.
  - Live heading readout only, no saved bearing log.
  - 'Power meter' becomes tinySA channel power.
  - jt9/wsprd only.
  - Delete the 12 GHz claim.
  Also extend the Artemis stop to ADS-B/AIS military flags (decision L8).
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  4.
    - **Area:** Metop-B AHRPT (foldable tier): SDR requirement and target status
    - **Components:**
      - RTL-SDR Blog V4L
      - Airspy Mini option
      - petal helicone
    - **Problem:** Register #91/#125, foldable loss_table[4] and NPU class 2 all say Metop needs an SDR faster than 2.56 Msps, i.e. a Lime or an Airspy Mini. Two pieces of evidence weaken that:
  - The project's own dish_replacement forum work cites SatDump issue #727, where an RTL-SDR Blog V4 decoded Metop AHRPT (an avhrr_3_composite image) at 2.88 Msps with DC block and AGC. The maintainer said the RTL is 'on the edge'.
  - NOAA OSPO notices of 6 May and 7 Jul 2026 list 'AHRPT Service - Metop-B' as an affected service, so the broadcast is live.
  So the receiver question is open, and only the link budget limits Metop-B: helicone about -1.5 to 0 dB average (model), plus the intermittent modulator loss.
    - **Severity:** major
    - **Evidence:** dish_replacement.json forums (SatDump #727 entry); register decisions #91, #123, #125; foldable_antennas loss_table[4]; NOAA OSPO messages of May and Jul 2026.
    - **Fix:** Before buying an Airspy Mini (about GBP 110, undated) or array LNAs (4 x $44.95), run two free gates:
  - (a) A 15 min rtl_test at 2.88 Msps on the blue USB 3.1 root port with zero dropped samples.
  - (b) A recording of one Metop-B pass above 45 deg on the helicone + SAWbird+ GOES + V4L at 2.88 Msps, checking for the spectral hump and lock.
  Buy the Airspy Mini only if (a) fails. Gate the array on (b).
    - **Fix cost:** $0; 1-2 evenings
    - **Sources:**
      - https://github.com/SatDump/SatDump/issues/727
      - https://www.ospo.noaa.gov/data/messages/2026/05/MSG_20260506_1452.html
      - https://ospo.noaa.gov/data/messages/2026/07/MSG_20260702_1650.html
  5.
    - **Area:** Patch/chip tier: L-band antenna for Inmarsat-C, GNSS-SDR and the Iridium carrier
    - **Components:**
      - 2-turn helix + SAWbird+ iO
      - RTL-SDR Blog Active L-band patch
    - **Problem:** The patch tier uses a DIY 2-turn helix, which is not a patch and still needs the user's OK (register #111), plus a SAWbird+ iO ($49.95). The Iridium carrier also needs a SAWbird+ IR that is not in the BOM.
  
  A true patch exists: the RTL-SDR Blog Active L-band patch.
  - 1525-1660 MHz, with its own LNA and filter.
  - 3.3-5 V bias tee, about 20-30 mA (blog for the older model; retailer says 20 mA).
  - It fits the patch rule and the '80 mA or less on the V4L tee' rule.
  - It covers Inmarsat-C, GPS/GLONASS L1 for GNSS-SDR, and Iridium carriers.
  - rtl-sdr.com reports SafetyNET decodes with a patch.
    - **Severity:** major
    - **Evidence:** small_antenna_stack final.reachable[9] and [13]; register decisions #2, #111, #112, #134. Price: $44.95 promo / $49.95 standard (rtl-sdr.com posts, dated); 679 SEK incl. VAT at Electrokit.
    - **Fix:** Make the patch the patch-tier default for Inmarsat-C, GNSS-SDR L1 and the Iridium carrier, and drop the SAWbird+ iO and IR from core. Keep the helix only for HRPT, because the patch's SAW blocks 1700 MHz. Re-check the current price and current on the product page in P5.
    - **Fix cost:** About $45-50, which replaces the $49.95 iO and the helix materials (net about $0)
    - **Sources:**
      - https://www.rtl-sdr.com/rtl-sdr-blog-active-l-band-patch-antenna-for-inmarsat-iridium-gps-back-in-stock/
      - https://www.rtl-sdr.com/preorder-sale-active-l-band-1525-1660-inmarsat-and-iridium-patch-back-in-stock-for-44-95/
      - https://www.electrokit.com/en/rtl-sdr-aktiv-antenn-l-band-1525-1660mhz
  6.
    - **Area:** Patch/chip tier: Meteor LRPT (and AIS, sondes, ADS-B, FM)
    - **Components:**
      - 20 cm helical whip
      - RTL-SDR Blog telescopic dipole kit
    - **Problem:** small_antenna_stack makes a 20 cm helical whip the LRPT default. It is model-only: decodes from about 17-24 deg in the model, and 'no published LRPT decode with an antenna under 20 cm' exists.
  
  Register #114 makes the V-dipole primary, but only in the foldable tier. Yet the dipole kit collapses to 23 cm (verified), weighs 150-250 g and packs to 0.9 L, so it already meets the 20-23 cm piece rule.
    - **Severity:** major
    - **Evidence:** small_antenna_stack final.reachable[2]; foldable_antennas final.foldable_kit[0]; register decisions #114 and #115.
    - **Fix:** Carry the dipole kit in BOTH tiers. LRPT then has a verified antenna (3.0 dBi NEC, widely used), and so do AIS (44 cm arms), radiosondes (17.7 cm), ADS-B (6.5-7 cm) and FM/DAB. Keep the helical whip as an experiment only.
    - **Fix cost:** $0 ($17.95 kit already in the BOM); +0.15-0.25 kg in the always-carried tier
    - **Sources:**
      - https://www.rtl-sdr.com/DIPOLE
  7.
    - **Area:** ISS 70 cm goal: stale frequencies and a wrong receiver route
    - **Components:**
      - foldable crossed Yagi
      - lab_ui_hf menu
      - npu class list
    - **Problem:** ARISS (status 7 Oct 2026) confirms APRS on 437.825 MHz and the FM repeater on 437.800 MHz down / 145.990 MHz up; SSTV events are on 437.55 MHz. These entries are still stale:
  - foldable_kit[1] '145.8 MHz (ISS SSTV)'. This is the only stated reason for the Yagi's 2 m half.
  - loss_table[1].
  - The ultra-compact note 'dipole kit as a straight dipole for ISS (-5.8 dB)'.
  - menu[12] 'ISS SSTV 145.800' and menu[13] 'APRS 145.825'. Both offer 'HF+ in VHF mode' as an alternate, but the HF+ stops at 260 MHz.
  - hf_capabilities[11] 'backup for ... 145.8 MHz ISS'.
  - NPU class 7.
  There is also no menu leaf for the ISS FM repeater downlink.
    - **Severity:** major
    - **Evidence:** ARISS current-status page (7 Oct 2026); foldable_antennas.json final.foldable_kit[1], loss_table[1], ultra_compact_tier; lab_ui_hf.json menu_tree[12] and [13], hf_capabilities[11]; npu_training.json final.class_list[8].
    - **Fix:** Retarget all entries to 437.550 / 437.825 / 437.800 MHz and delete the HF+ alternate for ISS. Add an 'ISS FM repeater 437.800 (listen)' pass profile. Re-justify the 2 m Yagi half on AO-73 145.935, JO-97 145.840, AO-7 145.9775, AO-91 145.960 and VHF APRS 145.825, and make it optional (decision L4).
    - **Fix cost:** $0
    - **Sources:**
      - https://www.ariss.org/current-status-of-iss-stations.html
  8.
    - **Area:** Touch menu: leaves that depend on the undecided Lime
    - **Components:**
      - lab_ui_hf menu
      - foldable 70 cm feed
    - **Problem:** These leaves have no working default while the Lime is optional:
  - [9] Meteor HRPT: 'SatDump at 7-10 Msps, Lime RX1 (V4L marginal)'.
  - [10] Metop/FY AHRPT: Lime RX1.
  - [11] Elektro LRIT: Lime RX1.
  - [14] CubeSats: Lime RX2.
  - [17] Inmarsat-C: Lime RX1.
  - [89] GNSS-SDR lab: Lime RX1.
  - [43] and [45] waterfall and survey: 'Lime wide'.
  - [1] Tune: 'Lime at 30 MHz'.
  In foldable_antennas, the 70 cm Yagi feeds the 'LimeSDR port', and polarisation diversity uses 'both Lime RX'.
    - **Severity:** major
    - **Evidence:** lab_ui_hf.json final.ui_system.menu_tree[1,9,10,11,14,17,43,45,89]; foldable_antennas.json foldable_kit[2] and loss_table[2]; register decision #86 (Lime is gated optional).
    - **Fix:** Give each leaf a V4L default:
  - HRPT at 2.4-2.56 Msps.
  - Metop at 2.88 Msps once the test passes.
  - LRIT on the RTL.
  - CubeSats on RTL-A.
  - GNSS-SDR on a V4L with the L-band patch.
  The Lime becomes an optional upgrade. A capability probe hides Lime-only leaves, and the acceptance test runs the whole menu with the Lime absent.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  9.
    - **Area:** Touch menu: leaves that depend on the T7
    - **Components:**
      - lab_ui_hf menu
      - labd Updater
    - **Problem:** These leaves need the T7, which C18 buys only if the Lime stays:
  - [18] TLE/OMM import.
  - [69] dataset export.
  - [77] recordings export.
  - [84] map import.
  - [100] Updates: the offline bundle and the rsync snapshot go to T7 ext4.
  - [73], [78] and [92]: storage views.
    - **Severity:** major
    - **Evidence:** lab_ui_hf.json menu_tree[18,69,73,77,78,84,92,100]; register decisions #35 and #72.
    - **Fix:** Add an 'external storage' abstraction: a V30/A2 microSD in the Q6A slot, or a USB stick on the LAB port. Put snapshots on an A/B root or a snapshot partition on UFS.
    - **Fix cost:** $0-30 (microSD price unverified)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  10.
    - **Area:** QO-100 menu leaf
    - **Components:**
      - lab_ui_hf menu_tree[15]
    - **Problem:** The leaf still offers 'LNB 13.4 V (V) / 18.2 V (H), hold-to-confirm' and an unlabelled 'SSB/CW listening'. The register decided on 13.2 V only, no 18 V, and the label 'beacon/CW/strong SSB only'.
    - **Severity:** major
    - **Evidence:** lab_ui_hf.json menu_tree[15]; register decisions #55, #102 and #103.
    - **Fix:** Give the leaf one 13.2 V state with true disconnect, and show the per-tier margin label on it.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  11.
    - **Area:** QO-100 capability per tier: contradictory ratings
    - **Components:**
      - bare Bullseye LNB
      - 11 cm cone / 10 cm cup
      - gore horn
    - **Problem:** small_antenna_stack reachable[14] and [15] rate:
  - bare-LNB FT8 'reliable with beacon lock'. The only evidence, RigExpert TBR-AN-1, used a GPSDO-locked LNB; the Bullseye is a TCXO LNB that drifts ±10-30 kHz.
  - the PSK beacon 'reliable with the cone (+7.4 ±2 dB)'.
  foldable loss_table[7] rates the comparable 18 dBi cup as 'PSK 5-8 dB (marginal)'.
  
  My conservative-model calculation (C/N0 = G + 13..16 dB-Hz) gives the cup or cone 31-34 dB-Hz, so the 400 bit/s Eb/N0 is 5.4-8.4 dB. Beacon lock also depends on the unfixed tracker bug (register #108).
    - **Severity:** major
    - **Evidence:** small_antenna_stack final.reachable[14] and [15]; foldable_antennas final.loss_table[7]; register decisions #107 and #108; /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/goals_calc/budget.py
    - **Fix:** Adopt one table (decision L2):
  - Bare LNB: CW beacon reliable (OK1DX), FT8 experimental.
  - Cone or cup: PSK marginal.
  - 21-23 dBi horn: PSK reliable (model), beacon-level SSB marginal (0 to +5 dB).
  - Typical SSB and DATV: lost.
  Fix qo100_beacon_track.py before making any FT8 claim.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/small_antenna_stack.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
  12.
    - **Area:** S-band goal
    - **Components:**
      - Lime/Pluto
      - S helix
      - cf2235-kt30 cavity
      - S-band LNA
    - **Problem:** Without a Lime or Pluto, the S-band goal is zero. Even with one:
  - small_antenna_stack reachable[18] calls Black Kite-1/2 'reliable'. SatNOGS DB lists Black Kite-1 as operational, but with no decoded data in the last 30 days and no decoders found, and its NORAD/TLE IDs have changed (98527, 66741).
  - HamTV is active in 2026 at 2395 MHz (ARISS status Jan 2026; test video Dec 2025), but the chosen cavity (2170-2300 MHz) blocks it.
  - The S-band LNA is still unnamed.
    - **Severity:** major
    - **Evidence:** SatNOGS DB Black Kite-1/2 entries; ARISS HamTV page and status; small_antenna_stack final.reachable[18]; register decision #90.
    - **Fix:** Make S-band conditional on the Lime gate. Rate Black Kite and PHASMA opportunistic: GMSK 38k4 demodulates, but the frames cannot be parsed. Rate HamTV carrier-only. Name and price an S-band LNA, or drop the chain.
    - **Fix cost:** S-band LNA unpriced; cavity EUR 65.45
    - **Sources:**
      - https://db.satnogs.org/satellite/98527/
      - https://db.satnogs.org/satellite/98371
      - https://www.ariss.org/hamtv-on-the-iss.html
  13.
    - **Area:** LNA bias power rail
    - **Components:**
      - LT3045-class LDO
      - LAB 5 V (D36V28F5, 2 A fuse)
      - TPS2553 injectors
    - **Problem:** The files disagree on where the LNA bias comes from, and neither option works as written:
  - Register #61 says 'LNAs: LT3045-class LDO'.
  - Conflict item 5 says 'HF+ and injectors powered from LAB 5 V'. But the LAB 5 V budget (1.3-1.4 A on a 2 A fuse) leaves the injectors out.
  
  Two SAWbird+ draw 0.35 A (170 + 180 mA):
  - On LAB 5 V, the total becomes about 1.75 A of the 2 A fuse.
  - Through an LT3045 from 12 V, the LDO dissipates 2.45 W, a junction rise of about 85-105 C (model). That cannot be built, and the LT3045 is rated for only 500 mA.
    - **Severity:** major
    - **Evidence:** register decisions #61 and #62, conflicts_for_final_checks[4]; radio_lab final.usb_power_case_plan; my calculation in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/goals_calc/budget.py
    - **Fix:** Build a dedicated 5 V low-noise LNA rail: a 12-to-6 V buck plus an LT3045 (0.35 W), or a 5 V buck plus a pi-filter, rated 0.6 A or more. Feed it to one TPS2553 per LNA, and recompute the LAB 5 V budget.
    - **Fix cost:** About $10-20 (estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  14.
    - **Area:** 137 MHz chain in the menu: wrong bias source
    - **Components:**
      - menu_tree[8]
      - SAWbird+ NOAA
      - V4L bias tee
    - **Problem:** The LRPT leaf specifies 'SAWbird+ NOAA on the V4L 4.5 V tee'. The SAWbird+ NOAA draws 170 mA, and register #96/#100 allow only LNAs of 80 mA or less on the 180 mA tee; every SAWbird+ goes on a TPS2553 injector. RTL-SDR Blog warns that long overloads can kill the dongle's LDO or fuse.
    - **Severity:** major
    - **Evidence:** lab_ui_hf.json menu_tree[8]; register decisions #96, #100 and #101.
    - **Fix:** Correct the leaf. The labd interlock checks that the injector is on and the V4L tee is off for this profile.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  15.
    - **Area:** 70 cm chain (ISS, CubeSats, sondes): unnamed band-pass filter
    - **Components:**
      - 70 cm BPF
      - Uputronics 435
      - LNA V2
    - **Problem:** The verifiers call 70 cm overload the main risk on the 8-bit V4L, but no purchasable band-pass filter is named; the generic one is budgeted at $15-40. The Uputronics 435 is down to its last items (EUR 47.64 at Kubii), and new stock is limited to 5 V bias.
    - **Severity:** major
    - **Evidence:** register decision #98 and open_questions[18]; verdict checked[12].
    - **Fix:** Name a 430-440 MHz SAW or cavity BPF, or a filtered LNA, in P5. Measure its insertion loss and DC pass on the LiteVNA (conducted).
    - **Fix cost:** $15-50 (estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  16.
    - **Area:** Spectrum survey: gap above 1.766 GHz
    - **Components:**
      - tinySA Ultra+ ZS407
      - labrx survey
    - **Problem:** radio_lab capabilities[2] surveys 0.5 MHz-1.766 GHz on the RTL and 0.3-3.8 GHz only on the Lime; menu[45] also says 'Lime (wide)'. Without the Lime, 1.766-7.3 GHz is never surveyed: LTE 1800/2100/2600, Wi-Fi 2.4/5 GHz and S-band. Yet the core tinySA Ultra+ already receives to 7.3 GHz in ULTRA mode.
    - **Severity:** major
    - **Evidence:** radio_lab.json final.capabilities[2]; register decision #131 (ULTRA mode to 7.3 GHz); lab_ui_hf menu_tree[45].
    - **Fix:** Add a 'Survey (tinySA, receive-only, coarse)' profile through the labd tinySA serial driver. Mark sensitivity above 800 MHz as unverified. Ku stays available through the LNB IF up to 11.516 GHz.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  17.
    - **Area:** NPU detect/classify: the CPU fallback cannot keep up
    - **Components:**
      - inferd-cpu (ORT 1.31)
      - RTL-F/RTL-C profiles
    - **Problem:** The CPU mode handles 4-6 tiles/s. One V4L needs 7.3 tiles/s (RTL-F 6.5 + RTL-C 0.8), and two V4Ls about 14.6. If Phase 0 fails, the MVP 'ships CPU-first', but the CPU then labels only 55-82% of one SDR's tiles and about 30-40% of two.
    - **Severity:** major
    - **Evidence:** npu_training.json final.budgets and roadmap[0]; register decision #41.
    - **Fix:** Define a CPU-mode profile of 4 tiles/s or less: RTL-F with doubled K, change-gated tiles, one SDR only. Otherwise make the HTP gate a prerequisite for live labels. Show 'AI: partial' on the status bar.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  18.
    - **Area:** NPU classes: observability and training data
    - **Components:**
      - npu class list
      - Phase 1 roadmap
    - **Problem:** Several classes cannot be trained or observed with the core hardware:
  - Class 12 dvbs2: the V4L's 2.56 MHz window is far narrower than a 27.5 MHz Ku transponder, and the QO-100 wideband beacon needs a dish.
  - Classes 16 wifi and 17 bt_ble work only with LIME-B.
  - Class 2 is 'Meteor/NOAA HRPT and MetOp', but NOAA ended in 2025.
  - Class 7 sstv is still on 145.800 MHz, and its only live data are ARISS events (Series 33: 2-6 Oct; Series 34: 22-25 Oct 2026). The plan of 300 boxes per class cannot come from live captures.
  - The UI's HF band survey (menu[23]) shows NPU classes, but there is no HF profile.
    - **Severity:** major
    - **Evidence:** npu_training.json final.class_list[3,8,13,17,18] and budgets (LABELLING EFFORT); lab_ui_hf menu_tree[23]; register decisions #43 and #47.
    - **Fix:** Tag the Lime-only classes conditional, and limit Phase 1 to classes the V4L and HF+ can observe. Build SSTV examples from file-only synthetic Robot 36 (no TX) plus recorded event passes. Add the HF-F profile before showing HF labels.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  19.
    - **Area:** NPU teaching on satellite passes: no IQ tap while SatDump owns the SDR
    - **Components:**
      - SatDump per-pass unit
      - labrx ring
      - Signals AI > Record and collect
    - **Problem:** The pass leaves run 'SatDump CLI per pass', which opens the SDR itself (menu[8], [9]). 'Record and collect' is 'greyed out ... when the mode has no IQ tap' (menu[66]). So during live passes, the most valuable data, the NPU and the MARK key see nothing. This is likely, but not proven.
    - **Severity:** major
    - **Evidence:** lab_ui_hf.json menu_tree[8], [9] and [66]; register decision #50 (labrx is the single ring owner).
    - **Fix:** Make labrx the only process that opens an SDR. Passes are recorded through labrx and decoded by SatDump from the file (record-then-decode, already the retention default) or from a FIFO. Whether SatDump 2.0-alpha supports a live pipe source is unverified, so test it.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  20.
    - **Area:** NPU teach goal depends on an unconfirmed home-base PC
    - **Components:**
      - SpecDet-S v0.1
      - E-S embedder
      - QAIRT 2.42 x86-64 converter
    - **Problem:** On-device few-shot learning (T0/T1) needs a frozen detector and embedder trained off-device. Phase 1 assumes an x86-64 PC with an 8-16 GB NVIDIA GPU, plus Ubuntu 22.04 for the 2.42 conversion. Neither is confirmed (open_questions[9]). Without one, the NPU goal stops at CFAR energy boxes.
    - **Severity:** major
    - **Evidence:** npu_training.json final.hardware_needs and roadmap[1]; register decision #45.
    - **Fix:** See decision L7. Use Colab/Kaggle for synthetic and satellite-only data, and run the 2.42 conversion in any x86-64 Ubuntu 22.04 VM or cloud runtime, once licence and runtime OS are checked.
    - **Fix cost:** $0 (cloud free tiers) to a GPU PC (user-owned?)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  21.
    - **Area:** AIS on the HF+ (public terrestrial goal)
    - **Components:**
      - HF+ input selector
      - menu RF path
    - **Problem:** The default 'AIS on the HF+' depends on an input selector whose part is still TBD and missing from the BOM. menu[64] RF path also names 'HMC241 SP4T boards', which were rejected for the HF+ selector; the sled uses an HMC7992.
    - **Severity:** major
    - **Evidence:** register decisions #93 and #128; lab_ui_hf menu_tree[38] and [64].
    - **Fix:** Choose a latching, DC-capable signal relay in P5 and add a BNC-SMA lead. Until then, show the 'connect X' prompt. Correct the menu[64] hardware list.
    - **Fix cost:** About $5-30 (estimate, part TBD)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  22.
    - **Area:** GEO, SBAS and LF goals depend on the unknown region
    - **Components:**
      - QO-100
      - Inmarsat NCS
      - Elektro/FY-2H
      - EGNOS
      - LF time station
    - **Problem:** These goals all depend on where the user is:
  - QO-100 at 25.9E.
  - Which Inmarsat NCS is overhead.
  - Elektro (76E, with L3 reportedly drifting to 14.5W) and FY-2H (79E).
  - EGNOS: PRN 121/136 are operational and 123 is in test, with a Europe/Africa service area. In the Americas or Asia-Pacific the goal must become WAAS, MSAS, GAGAN, etc.
  - The LF time station.
  Inmarsat-C itself has an NCS in every ocean region, so the L-band patch is safe to buy now.
    - **Severity:** major
    - **Evidence:** register decisions #109 and #124, open_questions[0]; EGNOS OS real-time page and Aug 2026 monthly report.
    - **Fix:** Ask the user for the region. Until then, compute 'visible from here' per target from the GNSS fix, generalise EGNOS to regional SBAS (decision L10), and hold only the Bullseye, horn materials and SAWbird+ iO.
    - **Fix cost:** $0
    - **Sources:**
      - https://pre-egnos.gsc-europa.eu/services/open-service/open-service-realtime-performance
      - https://egnos.gsc-europa.eu/node/12832
  23.
    - **Area:** Meteor HRPT on the V4L (L-band HRPT where the foldable kit allows)
    - **Components:**
      - V4L
      - 4-turn helix
      - petal helicone
      - CH334F/RP2040 clocks
    - **Problem:** Every margin here is a model:
  - Patch tier, 4-turn helix: +1.5 to +3 dB average above 25-30 deg; 'no small-helix HRPT decode documented'.
  - Foldable helicone: +8.9 to +9.4 dB (NEC); no dish-free hand-tracked decode is documented.
  - The V4L runs at 2.4-2.56 Msps against a 2.7 MHz main lobe.
  Own spurs also fall on or near the signal: the V4L's 28.8 MHz x59 = 1699.2 MHz is inside the 1700 MHz lobe, and 12 MHz x142 = 1704.0 MHz is close. OK9SGC's RTL decodes show it is feasible, but it is unproven in this enclosure.
    - **Severity:** major
    - **Evidence:** small_antenna_stack final.reachable[11]; foldable loss_table[3]; register decisions #117 and #127; antennas.json spur list.
    - **Fix:** Before the first pass, run a terminated-input scan of 1695-1705 MHz with the host streaming (P4/P13) and a SAWbird+ on/off check. Fly the first passes above 40 deg from a tripod.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/antennas.json
  24.
    - **Area:** FengYun, Elektro-L and AWS labels
    - **Components:**
      - menu_tree[10] and [11]
      - foldable loss_table[10], build step 7
    - **Problem:** Several labels are stale or too strong:
  - menu[10] says 'Metop/FY AHRPT', but FY-3 L-band ended in Nov 2024 and FY-3D to 3H are X-band.
  - foldable loss_table[10] says 'Elektro-L5 LRIT kept', and build step 7 uses Elektro as the A/B reference with a Kyiv elevation. The helicone sits about 3 dB below the 65 cm dish reports, so it is marginal.
  - FY-2H is given as both 1687.5 and 1690.5 MHz.
  - AWS needs 3.6 Msps or more, which is beyond the V4L even at 2.88 Msps.
    - **Severity:** minor
    - **Evidence:** lab_ui_hf menu_tree[10]; foldable_antennas loss_table[10] and build_and_test_steps[6]; register decisions #124 and #125.
    - **Fix:** Remove 'FY' from the AHRPT leaf. Add a 'GEO carrier check (Inmarsat NCS / FY-2H / Elektro)' leaf that searches the frequency on air. Rate Elektro opportunistic. Rate AWS as needing the Lime or an Airspy Mini.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
  25.
    - **Area:** Calibration: absolute level above 800 MHz
    - **Components:**
      - tinySA generator
      - DIY noise source
      - P10/P11 procedures
    - **Problem:** The tinySA sine output (-115 to -19 dBm, ±2 dB) is specified only up to 800 MHz; above that it gives unlevelled square-wave harmonics. The noise-source ENR is relative (±2-3 dB). So dBFS-to-dBm and MDS figures at 1.54, 1.70 and 1.42 GHz are relative only, and the files never say so.
    - **Severity:** minor
    - **Evidence:** register decisions #131 and #132; radio_lab final.capabilities[11].
    - **Fix:** Label every L-band absolute number '±3 dB, relative'. Calibrate by Y-factor with the ENR table taken at the regulated AUX voltage, and confirm with the GNSS C/N0 and Sun-noise checks.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  26.
    - **Area:** Pointing aid
    - **Components:**
      - BNO085 puck
      - Point antenna leaf
      - steel-tape 2 m Yagi
    - **Problem:** Three gaps in the pointing aid:
  - The IMU error of ±3-5 deg costs 0.7-1.9 dB on the 23 dBi horn (HPBW about 12.7 deg, model), but the Point leaf's audio pitch encodes only the IMU error, not signal strength.
  - The puck needs 15-20 cm from steel, yet the 2 m Yagi elements are steel tape at 0, 0.20 and 0.51 m on a 0.70 m boom.
  - The IMU interface is still undecided between four options.
    - **Severity:** minor
    - **Evidence:** gnss_imu digest (mounting, 1 uT is about 3 deg); register decision #81; lab_ui_hf menu_tree[81]; my HPBW calculation in budget.py.
    - **Fix:** Add a 'peak on signal' mode (beacon C/N0 or S-meter as pitch) for GEO and LEO. On the Yagi, take elevation from gravity and azimuth from a sun-sight. Freeze the IMU on the UART7 relay, with USB-CDC as fallback.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/goals_calc/budget.py
  27.
    - **Area:** Standalone pass prediction: orbital-element freshness
    - **Components:**
      - labd OMM cache
      - Skyfield 1.55
    - **Problem:** The cache warns at 3 days (ISS) and 7 days (others) and refreshes only 'when online' or from the T7. Wi-Fi is off in the field and there is no phone. No maximum age is tied to antenna beamwidth, and without the T7 there is no offline refresh path.
    - **Severity:** minor
    - **Evidence:** lab_ui_hf menu_tree[18]; user_requirements.md (standalone, no phone).
    - **Fix:** Block auto-pointing, but not reception, when the estimated along-track error exceeds a quarter of the beam. Refresh over home Wi-Fi or from a USB stick or microSD.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  28.
    - **Area:** LF time signals
    - **Components:**
      - Boni-Whip
      - SDRangel Radio Clock
    - **Problem:** LF time decoding depends entirely on the active whip, because the 9:1 wire loses an estimated 7-12 dB at 40-77.5 kHz. WiMo lists the Boni-Whip as available from 20 Nov 2026. lab_ui_hf promises 'JJY 40/60 kHz', but SDRangel Radio Clock lists only JJY on 40 kHz, alongside MSF, DCF77, TDF, WWVB, RBU and PCSK-225.
    - **Severity:** minor
    - **Evidence:** SDRangel radioclock readme (fetched); register decisions #94 and #95; lab_ui_hf hf_capabilities[1].
    - **Fix:** Buy whichever active whip is in stock (Moonraker $123.95, or the PA0RDT clone at EUR 25.90). Log JJY 60 kHz as amplitude only.
    - **Fix cost:** $30-160
    - **Sources:**
      - https://github.com/f4exb/sdrangel/blob/master/plugins/channelrx/radioclock/readme.md
  29.
    - **Area:** Sunlight use
    - **Components:**
      - Wisecoco 7in 2000-nit
      - 4D 1000-nit
      - Xenarc 702GSH
    - **Problem:** The sunlight plan rests on weak evidence:
  - Wisecoco: 0 reviews, '2500' in the title vs 2000 in the spec table, I2C in-cell touch, and bonding unconfirmed.
  - The 4D fallback has no world price.
  - Thermal derating to 50% above 60 C halves the brightness exactly in full sun: about 3.6:1 bonded with AR film at 1000 nits (model).
  - display_market's verified, world-priced bonded unit (Xenarc 702GSH, $429, in stock, 1000 nits, AR/AF coating, USB PCAP, 10-35 V, under 10 W, 0.70 kg, low resolution) was not carried into the register.
    - **Severity:** minor
    - **Evidence:** display_market.json sweeps[0] best_overall and sweeps[3] best_overall; register decisions #74 and #76.
    - **Fix:** Choose in this order (decision L11): Wisecoco only with written confirmation of bonding and USB-HID touch; else the 4D after a world quote; else the Xenarc. The hood is mandatory, and the 45 min noon soak is an acceptance test.
    - **Fix cost:** $0 to +$300 if the Xenarc is needed
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/display_market.json
  30.
    - **Area:** ADS-B placement in the lab tiers
    - **Components:**
      - radio_lab extended
      - V4L spare
    - **Problem:** radio_lab puts the '1090 MHz ADS-B front end on the spare V4L' in EXTENDED, although ADS-B is a core public-terrestrial goal.
    - **Severity:** minor
    - **Evidence:** radio_lab.json final.verdict (EXTENDED list); register decision #128.
    - **Fix:** Core: a time-shared V4L with dipole-kit arms of 6.5-7 cm. Optional: a preamp or the Pro Stick Plus (GBP 52.50).
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  31.
    - **Area:** Military-transmitter rule: unclear edge cases
    - **Components:**
      - HF WEFAX
      - NAVTEX/DSC
      - ADS-B/AIS displays
    - **Problem:** Some public broadcasts come from naval or coast-guard sites. The Northwood fax, for example, is believed to be Royal Navy-operated (to verify). ADS-B and AIS also show military aircraft and warships. The files apply the VLF-SID precedent to none of these.
    - **Severity:** minor
    - **Evidence:** user_requirements.md lines 33 and 36; lab_ui_hf hf_capabilities[2] and menu[27], [37], [38].
    - **Fix:** See decisions L8 and L9.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md
  32.
    - **Area:** No-loop rule: the exclusion list is incomplete
    - **Components:**
      - antennas.json alternatives
    - **Problem:** QFH (two bifilar loops) and eggbeater (two full-wave loops) are loop-type antennas, but they are not on the excluded list. antennas.json still carries 'QFH (quadrifilar helix) 137 MHz, DIY' as an alternative, so the P4/P5 re-research could bring it back.
    - **Severity:** minor
    - **Evidence:** antennas.json research.alternatives (QFH entry); register decision #4 exclusion list.
    - **Fix:** Add QFH, eggbeater, halo and big-wheel antennas to the 'excluded by user rule' list.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/antennas.json
  33.
    - **Area:** Menu coverage of lab functions
    - **Components:**
      - lab_ui_hf menu
    - **Problem:** Several functions have no menu leaf:
  - Scope/LA capture (Hantek 6022BL, PulseView).
  - FNB58 logging.
  - RF sled step attenuator.
  - Iridium/Orbcomm carrier-only views.
  - Ku carrier humps (Clarke-belt survey and horn calibration).
  - Inmarsat NCS scan of 1537-1545 MHz.
  'Reference / GPSDO (model TBD)' should name the Bodnar Mini, which is extended only.
    - **Severity:** minor
    - **Evidence:** lab_ui_hf.json menu_tree (105 leaves); radio_lab final.capabilities[19] and [12]; small_antenna_stack reachable[8], [13] and [17].
    - **Fix:** Add the leaves under Instruments and Satellites, all behind the same leases and the Bench interlock.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  34.
    - **Area:** Stale pipeline status
    - **Components:**
      - report_research register summary
      - conflicts_for_final_checks[24]
    - **Problem:** Both state that 'final/report_research.json is missing / does not exist yet'. The file exists: 576,735 B, written 18 Oct 04:51.
    - **Severity:** minor
    - **Evidence:** ls of the final/ directory; register.summary; conflicts_for_final_checks[24].
    - **Fix:** Close the item. Still add the errata blocks to summaries.md and minute-log.md.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
- **Proposed decisions:**
  1.
    - **Question:** C1. LimeSDR Micro: keep or drop?
    - **Decision:** Make it a gated optional. Keep the pre-order only if it is refundable, and decide on delivery or on 31 Jan 2027. Keep it only if (a) the riser acceptance passes (8 GT/s x1, zero AER errors after 60 min, 50 warm and 20 cold boots) and (b) the user wants S-band or the wideband NPU. Test Metop on the V4L at 2.88 Msps first (L1).
    - **Reason:** No core goal needs it:
  - LRPT, ISS, CubeSats, Inmarsat-C, the QO-100 IF, Meteor HRPT, ADS-B, AIS, sondes and HF all run on V4L + HF+.
  - Its unique additions are weak: Black Kite has no decoder in SatNOGS, the cavity blocks HamTV, the wideband NPU tiles are untested, and the driver is validated only on x86.
    - **Consequences:** Tag the RAM ring, T7, CPU7, LIME profiles, riser, REF IN and P4/P5/P7/P14/P18 as conditional. Survey above 1.766 GHz moves to the tinySA. Peak power stays at 24-32 W.
    - **Alternatives rejected:** Firm keep ($249-299 plus riser and cooling for opportunistic targets). Firm drop now (gives up a refundable option).
  2.
    - **Question:** C2. Q6A RAM tier
    - **Decision:** Buy the 12 GB board now ($189.99, Allnet; re-check stock on the order date). Fix the ring at 1.5 GiB without the Lime, and at 4 GiB with the Lime and training on.
    - **Reason:** RAM cannot be added later. The NPU trainer (up to 2 GiB) plus inferd (1.3 GiB) plus the apps would over-commit 8 GB.
    - **Consequences:** About $40 more than the 6 GB board. Burn-in within the return window.
    - **Alternatives rejected:** 8 GB (TinyTronics, EUR 100 ex VAT): too tight for training with the Lime.
  3.
    - **Question:** C3. Pack: 3S or 4S?
    - **Decision:** 4S1P Molicel P50B, 72 Wh, with a regulated 12 V rail into J21.
    - **Reason:** The 13.2 V LNB, the 12.5 V Boni-Whip LDO and AUX 12 V all need a source above 12.8 V. 4S gives 61-65 Wh usable to 13.6 V.
    - **Consequences:** +$45 and +75 g. Recompute all runtime tables (see budget table 1).
    - **Alternatives rejected:** 3S: it would need a boost converter for the LNB, Boni-Whip and AUX, with spurs on HF.
  4.
    - **Question:** C4. Which 12 V regulator?
    - **Decision:** Prefer a forced-PWM buck-boost rated 5 A or more, chosen in P5 after the terminated-floor spur A/B and a sealed-case current test. The fallback is the D36V50F12, with its hardware cut at 13.4 V or above.
    - **Reason:** A buck-boost works across all of 12.0-16.8 V and avoids light-load spur wander. The D36V50F12 drops out below 13.3 V and its stock is rationed.
    - **Consequences:** One more part to source. The 12 V load plan is 3.5 A.
    - **Alternatives rejected:** A 9 V J21 feed: it was based on a misplaced-TVS reading and is withdrawn.
  5.
    - **Question:** C5. USB port map
    - **Decision:** Freeze the Lime-agnostic map:
  - Blue USB 3.1: RTL-A, or the T7 only if the Lime stays.
  - FE1.1s P1: RTL-B.
  - FE1.1s P2: touch.
  - FE1.1s P3: CH334F hub. H1 HMI RP2040, H2 IMU (if not on UART7), H3 LAB USB-A, H4 HF+.
  The HF+ runs from LAB 5 V. SAWbird+ bias goes on its own 5 V LNA rail, not on LAB 5 V. Label the Wi-Fi module FCU760K.
    - **Reason:** FE1.1s load stays at 13 MB/s, 32-37% of its practical 35-40 MB/s. VCC_5V_PERI carries about 0.9 A of its 3.4 A. Putting the injectors on LAB 5 V would push it to about 1.75 A on a 2 A fuse.
    - **Consequences:** Run a 30 min zero-drop test with HF+ and V4L together on the FE1.1s.
    - **Alternatives rejected:** HF+ on Q6A VBUS (lab_ui_hf). LNA injectors on LAB 5 V.
  6.
    - **Question:** C6. 40-pin header and bus map
    - **Decision:** Freeze:
  - PPS on pin 7 (GPIO96, out-of-tree pps-gpio).
  - UART6 on 16/18 for the LC76G.
  - UART7 on 32/29 for the HMI RP2040, which also relays the IMU (fallback: USB-CDC on CH334F H2).
  - I2C0 on 13/15 for the INA228 only.
  - I2C2 on 27/28 for the MCP23017s at 0x20 and 0x21 (the counter at 0x30 only with the Lime). No BNO085 on I2C2.
  - Fan on pin 33 (pwm-gpio, spi14 off) after a test, else GPIO56.
    - **Reason:** The UART6 overlay disables i2c6, and the BNO08x clock-stretches on I2C.
    - **Consequences:** W1-2 bring-up tests: UART6 TX loopback, gpioinfo for GPIO96, and the UART7 overlay.
    - **Alternatives rejected:** INA228 on i2c6. BNO085 on I2C2.
  7.
    - **Question:** C7. Who owns the hardware?
    - **Decision:** labd is the only owner and lock authority. labrx owns the single RAM ring and recorder, and is the only process that opens SDRs; decoders such as SatDump read from labrx. labclassify runs inferd and fusiond.
    - **Reason:** One lease mechanism, and it gives the NPU an IQ tap during passes (issue on teaching during passes).
    - **Consequences:** Merge the npu_training daemon names. rflab becomes a labd module.
    - **Alternatives rejected:** Per-engine direct device access.
  8.
    - **Question:** C8. LNB supply
    - **Decision:** 13.2 V ±0.2 V measured at the F connector, with true disconnect, a switch rated 20 V or more, and no 18 V. Set one current limit at 1.5-2x the measured Bullseye draw.
    - **Reason:** 18 V selects only horizontal wideband/DATV, which is lost in every tier.
    - **Consequences:** Delete the 13.4/18.2 V rails from rf_frontend and from lab_ui_hf (arbiter and menu[15]).
    - **Alternatives rejected:** A switchable 13/18 V boost; the 12 V rail through a tee (gives only 10.6-11.4 V).
  9.
    - **Question:** C9. LNA bias rule and rail
    - **Decision:** Every SAWbird+ runs from a TPS2553 at 250-300 mA on a dedicated 5 V low-noise rail rated 0.6 A or more: a 12-to-6 V buck plus LT3045, or a 5 V buck plus pi-filter. The V4L tee powers only loads of 80 mA or less: LNA V2, the RTL-SDR Blog L-band patch (20-30 mA) and the non-plus SAWbird. Correct menu[8].
    - **Reason:** An LT3045 fed straight from 12 V would dissipate 2.45 W at 0.35 A (model). The 100-160 mA PTC would trip at 170-180 mA.
    - **Consequences:** About $10-20 of parts. Re-price cased and Barebones SAWbird+ separately.
    - **Alternatives rejected:** LT3045 directly from 12 V. GOES+ on the V4L tee.
  10.
    - **Question:** C10. FM band-stop filter
    - **Decision:** Nooelec Flamingo+ FM, fitted permanently in the 137/145 MHz path ahead of any gain.
    - **Reason:** Its 250 mA DC pass is published; the RTL-SDR Blog filter has no DC rating.
    - **Consequences:** $24.95. Measure its DC pass on arrival.
    - **Alternatives rejected:** Fitting it only at strong-FM sites.
  11.
    - **Question:** C11. librtlsdr build
    - **Decision:** Rebuild noble's 2.0.1 package with commits 0204c9c and 65f0658, keeping the .so.2 soname, and hold it.
    - **Reason:** It keeps the librtlsdr2 consumers (SoapyRTLSDR, gr-osmosdr, auto_rx) working.
    - **Consequences:** First bench task: an arm64 build that prints 'RTL-SDR Blog V4 Lite Detected'.
    - **Alternatives rejected:** The 2.0.3 .so.0 build. Purge-and-fork.
  12.
    - **Question:** C12. Display field-mode pixel clock
    - **Decision:** About 127.9 MHz (51.7 Hz at 2200x1125) in every file and in the cmdline. Use 164.4-168.4 MHz only if the panel accepts it. The 1280x800 per-profile mode switching applies only if the 4D is bought. The A/B test adds 1415.7 and 1544.4 MHz and 40-162 kHz.
    - **Reason:** 128.70 MHz puts its 12th harmonic at 1544.4 MHz, inside Inmarsat-C.
    - **Consequences:** Line rate 58.1 kHz, 1.9 kHz from 60 kHz. The LF A/B test decides whether that matters.
    - **Alternatives rejected:** 128.70 MHz. Native 1080p60 (148.5 MHz hits L5).
  13.
    - **Question:** C13. PPS on the held kernel
    - **Decision:** Build pps-gpio out of tree as a DKMS deb for 6.18.2-4 (CONFIG_PPS=y). Drop Route B. Build pps-ldisc only if the FT232RL fallback is used.
    - **Reason:** It keeps the HDMI/NPU kernel hold.
    - **Consequences:** Confirm with chronyc sourcestats.
    - **Alternatives rejected:** The 7.0.11 kernel.
  14.
    - **Question:** C14. INA228 bus and driver
    - **Decision:** I2C0, user-space i2c-dev with no DT binding, shunt in the pack lead.
    - **Reason:** A bound ina238 driver blocks access to the CHARGE register.
    - **Consequences:** Fix power.json and npu_training ('on the J21 rail').
    - **Alternatives rejected:** The ina238 hwmon driver on i2c6.
  15.
    - **Question:** C15. Antenna tiers: re-decide the small-stack removals
    - **Decision:** Patch/chip tier (always carried):
  - LC76G ceramic patch.
  - RTL-SDR Blog active L-band patch for Inmarsat-C, GNSS-SDR L1 and the Iridium carrier.
  - 70 cm whip on the case (A-V85, SRH-701 or a DIY 17 cm), tilted broadside.
  - Bare Bullseye LNB with a 10-11 cm cup.
  - The telescopic dipole kit (23 cm collapsed) for LRPT, AIS, sondes, ADS-B and FM.
  - A 4-turn helix on a 20 cm disc for HRPT (small rigid; needs the user's OK).
  Foldable tier adds:
  - The crossed Yagi in the ultra-compact build (2 m half optional, L4).
  - The petal helicone, 4-turn.
  - The 6-gore horn.
  - The S helix, only with the Lime.
  Loops are struck. The 20 cm helical whip becomes an experiment.
    - **Reason:** Patch and chip antennas cannot serve 137-146 MHz. The dipole kit already meets the 20-23 cm piece rule, and LRPT then has a verified antenna in both tiers. The true patch replaces a DIY helix and a $49.95 LNA.
    - **Consequences:** Patch-tier sling about 3.0-3.6 kg (estimate). The Lime, T7 and 12 GB are decided by C1, C18 and C2, not by antenna size.
    - **Alternatives rejected:** The small stack's strict deployed-size rule (superseded). Helical whip as the LRPT default (model-only).
  16.
    - **Question:** C16. Policy leftovers
    - **Decision:** Strike everything in register conflict 16 before STACK.md. Also gate the VNA leaf behind Bench mode, remove the foldable 'S11 after each trip' and 'VNA check per re-mark' steps, and remove the HF+ alternate for the 437 MHz ISS leaves.
    - **Reason:** Hard rules 1-3 and the delegated decisions.
    - **Consequences:** Add a CI policy audit over the menu tree and the class list.
    - **Alternatives rejected:** Brief indoor µW antenna sweeps (the user has not allowed them).
  17.
    - **Question:** C17. HF antenna chain
    - **Decision:** Boni-Whip at 12.5 V ±0.25 V from an LC filter and an LDO with 0.4 V or less dropout, behind a polyfuse and a labd load switch that defaults off. The 9:1 wire is for HF and NAVTEX only (0.15 MHz and up). LF time signals only on an active whip. Add a latching, DC-capable signal relay (part chosen in P5) and a BNC-SMA lead to the BOM. Confirm the HF-loop removal with the user at the phase end.
    - **Reason:** 12.5 V meets both published ranges (9-15 V and 12-15 V). The WB9-1 is rated only from 0.125 MHz. AIS-on-HF+ needs the selector. No user message records the loop removal.
    - **Consequences:** HF chain cost rises by about $10-40 (estimate).
    - **Alternatives rejected:** 10.0 V (below one source's 12 V floor). Using the HMC241 as the selector (its DC blocks hurt LF).
  18.
    - **Question:** C18. Storage without the T7
    - **Decision:** Buy the T7 only with the Lime. Otherwise use a V30/A2 microSD for raw IQ and exports, plus an A/B root or snapshot partition on UFS. Keep products by default and raw IQ only when pinned. All T7-bound menu leaves use an external-storage abstraction.
    - **Reason:** The worst no-Lime stream is 16.4 MB/s, within V30's 30 MB/s guaranteed sequential write. Dual-RTL raw is 36.9 GB/h.
    - **Consequences:** Test microSD sustained writes and reliability.
    - **Alternatives rejected:** Buying the T7 unconditionally.
  19.
    - **Question:** C19. CPU allocation
    - **Decision:** CPU0-3 (A55): UI, daemons, NPU host and CPU inference. CPU4-6 (A78): DSP, labrx, and T2 training only between passes. CPU7 is isolated only with the Lime.
    - **Reason:** T2 takes 4.5-10.8 min on the A78 cores; on the A55 cores it would take several times longer.
    - **Consequences:** Fix the lab_ui_hf trainer placement.
    - **Alternatives rejected:** Training on the A55 cores.
  20.
    - **Question:** C20. Roadmaps
    - **Decision:** Run NPU Phase 0 inside the W1-2 gates (19 Oct-1 Nov 2026). Move a minimal labeller into P0b. Limit Phase-1 classes to what the V4L and HF+ can observe. Add the HF-F and second-RTL profiles before any HF NPU label appears in the UI.
    - **Reason:** The labeller is needed about 3 months earlier than the UI schedules it, and the UI exposes HF classes long before the NPU has an HF profile.
    - **Consequences:** Use the ISS SSTV Series 34 pass (22-25 Oct) for the first live captures.
    - **Alternatives rejected:** Two separate roadmaps.
  21.
    - **Question:** C21. How many V4Ls?
    - **Decision:** Buy 3 now (2 in service plus 1 spare), and no 4th. Continuous ADS-B uses the spare on LAB USB at camp or on the bench. AIS runs on the HF+ through the selector. The spare also serves the 2.88 Msps Metop test.
    - **Reason:** R828S stock is finite (about 1 year). At most 3 continuous streams fit on the FE1.1s.
    - **Consequences:** $113.85.
    - **Alternatives rejected:** Buying a 4th unit now.
  22.
    - **Question:** C22. Software recipes
    - **Decision:** Use one venv per tool:
  - NanoVNA-Saver via pipx; PySide6 6.12; libgpiod v1; Skyfield 1.55 from pip; SatDump 2.0-alpha from source; OpenWebRX+ with pins.
  - qsstv 9.5.8 from noble universe (arm64 verified) as the SSTV fallback.
  - SDRangel Radio Clock for LF time signals.
    - **Reason:** These are the only recipes that work on noble arm64.
    - **Consequences:** Test each one on the Q6A within the return window.
    - **Alternatives rejected:** apt nanovna-saver 0.6.3. Skyfield 1.48. libgpiod v2.
  23.
    - **Question:** C23. Region unknown
    - **Decision:** Ask the user. In the meantime, buy the region-independent core, including the L-band patch (Inmarsat-C has an NCS in every ocean region). Hold the Bullseye, the horn materials and the SAWbird+ iO. Compute per-target visibility from the fix, and generalise EGNOS to regional SBAS.
    - **Reason:** QO-100, Elektro, FY-2H, EGNOS and the LF station are all region-bound.
    - **Consequences:** QO-100 may vanish from the goal list, saving about $60 and 0.3-0.5 kg.
    - **Alternatives rejected:** Assuming Europe.
  24.
    - **Question:** C24. Costs and weights
    - **Decision:** Recompute with the corrections:
  - Extended: about $555-780 without H-probes.
  - Internal interface: $56-73.
  - HF chain plus the selector and BNC-SMA lead.
  - Sling: 3.7-4.4 kg foldable, about 3.0-3.6 kg patch tier (estimate).
  Re-price every line at world prices in P5.
    - **Reason:** The subtotals do not match their line items.
    - **Consequences:** Feed the corrected BOM into P5.
    - **Alternatives rejected:** Carrying the old totals forward.
  25.
    - **Question:** C25. P1b completion
    - **Decision:** Close it: final/report_research.json exists (576,735 B, 04:51). Still add errata blocks to summaries.md and minute-log.md before the P2 synthesis.
    - **Reason:** The item is stale.
    - **Consequences:** None.
    - **Alternatives rejected:** Rewriting the file.
  26.
    - **Question:** L1. Metop AHRPT receiver path
    - **Decision:** Gate in this order:
  1. V4L at 2.88 Msps, 15 min zero-drop on the blue port.
  2. A Metop-B pass above 45 deg on helicone + V4L.
  3. Only if step 1 fails, buy an Airspy Mini (about GBP 110, undated).
  4. Build the array only after step 2 shows humps.
  AWS stays Lime/Airspy-only.
    - **Reason:** SatDump #727 shows a V4 decoding Metop at 2.88 Msps, and NOAA's 2026 notices show Metop-B AHRPT is live.
    - **Consequences:** Possibly no extra SDR at all. Metop stays experimental, at about -1.5 to 0 dB average (model).
    - **Alternatives rejected:** Buying the Airspy Mini or the Lime for Metop first.
  27.
    - **Question:** L2. QO-100 capability labels
    - **Decision:** Bare LNB: CW beacon reliable, FT8 experimental. 10-11 cm cup or cone: PSK marginal. 21 dBi horn: PSK reliable (model), beacon-level SSB marginal. 23 dBi horn: same, with SSB 2-5 dB. Typical SSB: lost. DATV: lost.
    - **Reason:** Conservative model, G + 13..16 dB-Hz (calculation). FT8 evidence exists only with a GPSDO-locked LNB. DATV needs 31-32 dBi (physics).
    - **Consequences:** Small-stack 'reliable' ratings are downgraded. The menu shows these margins.
    - **Alternatives rejected:** The optimistic G+28 anchor.
  28.
    - **Question:** L3. S-band scope
    - **Decision:** S-band only with the Lime (or a Pluto if the user accepts a TX-capable device). Black Kite and PHASMA are opportunistic. HamTV is carrier-only and needs its own 2.4 GHz filter.
    - **Reason:** SatNOGS has no decoder for Black Kite, and the cavity blocks 2395 MHz.
    - **Consequences:** No S-band hardware in core.
    - **Alternatives rejected:** A Pluto as a default.
  29.
    - **Question:** L4. The crossed Yagi's 2 m half
    - **Decision:** Make it optional. Carry the 70 cm half by default (ultra-compact build). Carry the 2 m tapes only for AO-73, JO-97, AO-7, AO-91 or VHF APRS sessions, or as the 137.5 MHz re-mark for weak LRPT passes.
    - **Reason:** The ISS moved all its modes to 70 cm.
    - **Consequences:** Saves an estimated 150-250 g and 2-3 min of setup. VHF linear and FM satellites drop to opportunistic when the tapes stay home.
    - **Alternatives rejected:** Always carrying both halves for ISS.
  30.
    - **Question:** L5. Spectrum survey above 1.766 GHz without the Lime
    - **Decision:** Add a coarse, receive-only tinySA Ultra+ survey profile (to 7.3 GHz) under Spectrum > Survey.
    - **Reason:** It is already core hardware.
    - **Consequences:** Sensitivity above 800 MHz is unverified.
    - **Alternatives rejected:** Buying an SDR just for the survey.
  31.
    - **Question:** L6. NPU Phase-1 scope
    - **Decision:** Phase-1 classes are limited to what the V4L and HF+ can observe. Add a CPU-mode profile of 4 tiles/s or less. dvbs2, wifi and bt_ble are Lime-conditional. HRPT means Meteor only. SSTV is trained partly on file-only synthetic data.
    - **Reason:** CPU mode runs 4-6 tiles/s against 7.3 for one V4L.
    - **Consequences:** Fewer live classes until the HTP gate passes.
    - **Alternatives rejected:** The full 24-class plan on CPU.
  32.
    - **Question:** L7. NPU training without a home PC
    - **Decision:** If the user has no GPU PC, use Colab/Kaggle with synthetic and satellite-only data. Run the QAIRT 2.42 conversion in an x86-64 Ubuntu 22.04 VM or cloud runtime. Check the AI Stack License for cloud use and the runtime OS version first.
    - **Reason:** Teach-on-device needs a pretrained backbone.
    - **Consequences:** Own terrestrial captures stay off cloud.
    - **Alternatives rejected:** Training the detector on the device (minutes per epoch at best).
  33.
    - **Question:** L8. Military entries in ADS-B and AIS displays
    - **Decision:** Do not display or log aircraft flagged military in the readsb/tar1090 database (flag bit to verify), or AIS ship type 35 ('military ops'). Log only 'out of scope'.
    - **Reason:** This mirrors the user's Artemis stop for incidentally received military emitters.
    - **Consequences:** A few tracks are hidden. Generic reception is unchanged.
    - **Alternatives rejected:** Showing everything; dropping ADS-B and AIS entirely.
  34.
    - **Question:** L9. WEFAX, NAVTEX and DSC from naval or coast-guard-operated stations
    - **Decision:** Allow public scheduled broadcasts (WEFAX, NAVTEX, MSI, DSC safety categories) only from an allow-list of stations in public schedules. By default exclude stations whose operator is a navy (e.g. Northwood, to verify), mirroring the VLF-SID precedent. Ask the user.
    - **Reason:** Rule 'no chains aimed at military transmitters'. The content itself is public weather and safety information.
    - **Consequences:** Some WEFAX charts may be lost.
    - **Alternatives rejected:** Allowing everything; banning coast-guard stations (that would remove most NAVTEX).
  35.
    - **Question:** L10. 'GNSS/EGNOS' outside Europe
    - **Decision:** The goal becomes 'regional SBAS' (EGNOS 121/136, WAAS, MSAS, GAGAN, etc.): SBAS fix flag plus tracked PRNs from the LC76G. Raw SBAS message decoding is out of scope unless a tool is verified.
    - **Reason:** EGNOS serves Europe/Africa only, and the region is unknown.
    - **Consequences:** Menu[86] is renamed.
    - **Alternatives rejected:** An EGNOS-only goal.
  36.
    - **Question:** L11. Display fallback order
    - **Decision:** Wisecoco, but only with written confirmation of bonding and USB-HID touch. Else the 4D after a world quote. Else the Xenarc 702GSH ($429, verified, 0.70 kg). The hood and AR film are mandatory.
    - **Reason:** Bonding, AR and shade matter more than nits. The Wisecoco has 0 reviews.
    - **Consequences:** Possibly lower resolution and +0.3-0.5 kg.
    - **Alternatives rejected:** A dim above-FHD panel.
  37.
    - **Question:** L12. Menu acceptance test
    - **Decision:** Every leaf must declare a no-Lime and a no-T7 backend. A CI test renders the menu with the Lime and T7 absent and checks the frequencies against the cached SatNOGS DB.
    - **Reason:** About 20 leaves are Lime- or T7-bound or stale today.
    - **Consequences:** Catches regressions like 145.800 early.
    - **Alternatives rejected:** Manual review.
- **Budget tables:**
  - Table 1. Power by scenario (no Lime, 4S 72 Wh, 61.2 Wh usable, 88% conversion efficiency; model, Q6A/V4L figures measured, the rest estimated)
  | Scenario | Load W | Pack W | Runtime h |
  |---|---|---|---|
  | Standby (Q6A idle, display 20%) | 5.6 | 6.4 | 9.6 |
  | LRPT pass (1 V4L + SAWbird+ NOAA) | 12.5 | 14.3 | 4.3 |
  | ISS / CubeSat pass (1 V4L + LNA V2) | 12.0 | 13.6 | 4.5 |
  | QO-100 session (LNB at mid 2.5 W) | 14.2 | 16.1 | 3.8 |
  | HRPT pass on helicone | 13.6 | 15.5 | 4.0 |
  | Full field (2 V4L, 2 SAWbird+, LNB, HF+) | 19.4 | 22.0 | 2.8 |
  | HF night logging (display off, Boni-Whip) | 6.2 | 7.0 | 8.8 |
  | Peak (Q6A 10.1, display 9, all RF, LAB 1 A) | 36.3 | 41.3 | 1.5 |
  | Add: Lime +4-5 W, T7 +2-3 W, training +3-6 W for 1-11 min | | | |
  - Table 2. Current per rail (model)
  | Rail | Planned load | Limit / part | Margin |
  |---|---|---|---|
  | Pack 4S 12.0-16.8 V | 1.2-1.6 A typical, 2.5-3.4 A peak | fuse 5 A (7.5 A with Lime) | OK |
  | 12 V to J21 | Q6A 2.0 + display 0.75 + AUX 0.75 = 3.5 A | regulator 5 A or more | 30% |
  | VCC_5V_PERI (Q6A) | 2 V4L 0.54 + LNA V2 0.08 + touch 0.1 + fan 0.12 + GNSS 0.04 = 0.88 A | about 3.4 A (17 W) | 74% |
  | LAB 5 V (D36V28F5) | 1.40 A (hub, puck, HMI, HF+ 0.2, LAB port 1.0) | 2 A fuse | 30%; only 12% if the injectors are added (1.75 A) |
  | LNA 5 V rail (new) | 2 SAWbird+ 0.35 A | 0.6 A or more; LT3045 0.5 A max | LT3045 from 12 V dissipates 2.45 W (not viable); 6 V pre-buck gives 0.35 W |
  | LNB 13.2 V | 110-270 mA (unpublished) | 1.5-2x measured | measure |
  | Boni-Whip 12.5 V | unknown | polyfuse plus load switch | measure |
  | V4L tee 4.5 V | 80 mA or less (LNA V2, L-band patch 20-30 mA) | 180 mA | OK |
  - Table 3. USB ports and bandwidth
  | Port | Device | MB/s |
  |---|---|---|
  | Blue USB 3.1 (own root) | RTL-A (or T7 at 224 MB/s with Lime; port 395 MB/s) | 5.12 (5.76 at 2.88 Msps) |
  | FE1.1s P1 | RTL-B | 5.12 |
  | FE1.1s P2 | touch HID | ~0 |
  | FE1.1s P3, CH334F H1/H2 | HMI RP2040 / IMU puck (if not on UART7) | ~0 |
  | CH334F H3 | LAB USB-A: 3rd V4L or Pro Stick 4.8; LA at 24 MS/s = 24 (forbidden while recording) | 0-4.8 |
  | CH334F H4 | HF+ at 768 ksps | 3.07 |
  | FE1.1s total (single-TT, 35-40 MB/s practical) | | 8.2 typical, 13.0 max allowed (32-37%) |
  | Non-USB | UART6 GNSS, UART7 HMI, I2C0 INA228, I2C2 MCP23017 x2, GPIO96 PPS, pin 33 fan, HDMI-A-1, microSD, M.2 (Lime only) | |
  - Table 4. RAM on the 12 GB board (about 11 GiB visible, unverified; app figures are estimates)
  | Item | No Lime GiB | Lime GiB |
  |---|---|---|
  | OS, labwc, Lab Shell | 1.2-1.8 | 1.2-1.8 |
  | SatDump during a pass | 0.4-1.0 | 0.4-1.0 |
  | SDRangel server, OpenWebRX+, readsb, AIS-catcher, auto_rx | 0.7-1.4 | 0.7-1.4 |
  | labrx ring (mlocked) | 1.5 | 4 (training on) / 6 (training off) |
  | inferd-htp + inferd-cpu + tiles | 1.4 | 1.4 |
  | Trainer (never during a pass) | up to 2.0 | up to 2.0 |
  | Worst concurrent case (pass, no trainer) | 5.2-7.1 | 7.7-9.6 (training on) |
  | Headroom of 11 GiB | 3.9-5.8 | 1.4-3.3 |
  - Table 5. CPU allocation (load figures unmeasured)
  | Cores | Use |
  |---|---|
  | CPU0-3 A55 1.9 GHz | UI, labd, labpowerd, NPU host, CPU inference at 4-6 tiles/s (needs 7.3 per V4L) |
  | CPU4-6 A78 2.4 GHz | labrx DSP, SatDump, SDRangel; T2 training (7.8 TFLOP, 4.5-10.8 min) only between passes |
  | CPU7 A78 2.7 GHz | isolated for lime:Rx0 only with the Lime; otherwise DSP |
  | GPU Adreno 643 | VkFFT for NPU tiles, about 7.8 GFLOPS of 808 measured |
  | HTP v68 | SpecDet INT8: 14.6 tiles/s with 2 V4L (17.5% duty at 12 ms); 42.5 tiles/s with the Lime, gate p99 11.7 ms or less |
  - Table 6. Storage
  | Store | Capacity | Use / rate |
  |---|---|---|
  | UFS 3.1 128 GB | about 92-100 GB free | OS, products, NPU dataset quota 20 GB |
  | Raw rates | | 1 V4L 18.4 GB/h; 2 V4L 36.9 GB/h; plus HF+ cf32 59.0 GB/h; one 15 min HRPT pass 4.6 GB (5.2 GB at 2.88 Msps) |
  | UFS raw time | | about 2.5 h dual-RTL, about 1.6 h for 2 RTL + HF+ |
  | microSD V30/A2 (no Lime) | 256-512 GB (price unverified) | 30 MB/s or more guaranteed sequential write vs 16.4 MB/s worst no-Lime stream |
  | T7 1 TB (Lime only) | about 74 min at 56 Msps cs16 (224 MB/s) | wideband bursts |
  - Table 7. Carried weight (estimates)
  | Item | kg |
  |---|---|
  | Handheld without / with Lime | 1.05-1.25 / 1.2-1.4 |
  | Patch tier antennas (whip, L-band patch, bare LNB + cup, 4-turn helix + disc) | 0.6-0.9 |
  | Dipole kit (both tiers) | 0.15-0.25 |
  | Foldable kit with LNB, SAWbird and jumpers | 1.3-1.8 |
  | HF wire kit (+ Boni-Whip 0.19 plus pole) | 0.4 (+0.3-0.5) |
  | Field pouch | 0.8 |
  | Sling, patch tier / foldable tier | about 3.0-3.6 / 3.7-4.4 |
  | Pelican 1450 full | 10-11 |
  - Table 8. Goal coverage by tier (margins are models unless stated)
  | Goal | Patch/chip tier | Foldable tier | Verdict |
  |---|---|---|---|
  | Meteor LRPT 137.9 | dipole kit (if carried): verified; helical whip: model only | V-dipole 3.0 dBi; N2-4 observed 17-18 Oct | covered (N2-3 opportunistic) |
  | ISS 437.550 / .825 / .800 | case whip, CNR 18.8-22 dB vs 10-12 needed; SatNOGS 12/12 images | 70 cm Yagi 11 dBi | covered; validate on Series 34 |
  | CubeSats 435-438 (1 W 9k6) | tilted whip -5.3 to +5.3 dB, passes above 30 deg | Yagi +5.7 dB at 10 deg, +11 at 30 (±5) | marginal / covered; BPF unnamed |
  | GNSS / EGNOS | LC76G; EGNOS PRN 121/136 operational | same | covered in Europe only |
  | Inmarsat-C SafetyNET | L-band patch, +7.5 dB with helix (model) | same | BLOCKED by header-filter rule |
  | QO-100 | bare LNB: CW beacon 6-9 dB/50 Hz | horn: PSK 8-13 dB, beacon SSB 0..+5 dB | DATV and typical SSB lost (physics); region-bound |
  | Meteor HRPT | 4-turn helix +1.5..+3 dB above 25-30 deg | helicone +8.9..+9.4 dB | model only; own spur at 1699.2 MHz |
  | Metop-B AHRPT | lost | helicone -1.5..0 dB; V4L at 2.88 Msps untested | experimental |
  | FengYun | FY-3 lost | FY-2H carrier only | lost / test only |
  | S-band | lost | Lime only; Black Kite opportunistic | conditional |
  | Elektro-L LRIT | lost | marginal, ~3 dB below dish reports | opportunistic |
  | ADS-B / AIS / sondes / FM / DAB | dipole kit + V4L / HF+ | same | covered (AIS-on-HF+ needs the selector) |
  | NAVTEX / LF time | wire + 9:1 for NAVTEX; LF only with the active whip | same | LF conditional on whip stock |
  | HF amateur decode-only | wire 5-10 m away, local-noise limited | same | covered with caveat |
  | Spectrum survey | 0.5 kHz-1.766 GHz; tinySA to 7.3 GHz (to add) | same | gap until the tinySA profile exists |
  | NPU detect / teach | design only; CPU 4-6 tiles/s | same | unmeasured |
  | Touch menu | 105 leaves, about 20 stale or Lime/T7-bound | | needs the L12 test |
- **Checks passed:**
  - ISS: APRS 437.825 MHz and the FM repeater 437.800 down / 145.990 up (PL 67) are confirmed on the ARISS status page (7 Oct 2026). SSTV Series 33/34 on 437.55 MHz was already confirmed by the verifier. The register's ISS frequencies are correct.
  - Meteor: N2-5 is still listed as planned for 2027 or later (WMO OSCAR, Jan 2026), so N2-3/N2-4 on 137.900 MHz is the complete current LRPT/HRPT target set, and all APT ended in 2025.
  - Metop-B AHRPT broadcast is live in 2026: NOAA OSPO notices on 6 May and 7 Jul 2026 list 'AHRPT Service - Metop-B'.
  - SatDump issue #727: Metop AHRPT was decoded (avhrr_3_composite) on an RTL-SDR Blog V4 at 2.88 Msps.
  - LF time decoding software: SDRangel Radio Clock supports MSF, DCF77, TDF, WWVB, JJY 40 kHz, RBU and PCSK-225 (readme). All civil allow-listed stations except JJY 60 kHz are covered.
  - SSTV decoder: qsstv 9.5.8-3build3 is in noble universe and arm64 is listed. This closes the small stack's 'arm64 package not verified'.
  - RTL-SDR Blog Active L-band patch: 1525-1660 MHz, LNA powered from a 3.3-5 V bias tee at about 20-30 mA (blog and retailer). It is compatible with the V4L tee rule.
  - EGNOS: PRN 121 and 136 are operational and PRN 123 is in test (EGNOS OS real-time page, Aug 2026 report); the files' PRN list is consistent.
  - HamTV is active in 2026 (ARISS, Jan 2026 status) and Black Kite-1/2 exist in SatNOGS DB with S-band GMSK 38k4 at 2288/2286 MHz. Both are real targets, though neither is reliable.
  - QO-100 conservative model reproduced: bare LNB 23-26 dB-Hz gives a CW beacon of 6-9 dB in 50 Hz, consistent with OK1DX. The 23 dBi horn gives beacon-level SSB of +2 to +5 dB in 2.5 kHz. DATV needs 31-32 dBi, so it is a physics limit in every tier.
  - Pointing: the helicone HPBW is about 29.5 deg, so ±3-5 deg of IMU error costs 0.12-0.34 dB (model). The aid is adequate for L-band.
  - USB: the FE1.1s carries 8.2-13.0 MB/s against 35-40 MB/s practical, and VCC_5V_PERI carries 0.88 A of about 3.4 A. Both pass for the Lime-agnostic map.
  - Frequency coverage: V4L (0.5-1766 MHz) plus HF+ (0.5 kHz-31 MHz and 64-260 MHz) reach every public terrestrial target: 40-162 kHz LF, 490/518 kHz NAVTEX, HF, FM, DAB, AIS 162 MHz, sondes 400-406 MHz, ADS-B 1090 MHz.
  - No dish appears in any final pick. The patch-physics limit (no useful 137-146 MHz patch) is consistent across the files.
  - The NPU class policy gate excludes radar, drone/RC, EW, military and fingerprinting classes. ADS-B and AIS oracles discard ICAO, MMSI and positions.
  - The runtime arithmetic reproduces: 72 Wh x 0.85 / 13-22 W gives 2.8-4.7 h without the Lime.
- **Notes:** I read user_requirements.md and the whole report_research register: 143 decisions, 25 conflicts, 24 open questions, plus the verdict's non-confirmed checks. I also read the finals of small_antenna_stack, foldable_antennas, radio_lab, npu_training and lab_ui_hf (menu, all 105 leaves), plus parts of display_market and the digest (dish_replacement, gnss_imu).
  
  Web use was 6 WebSearch and 5 WebFetch calls, on primary pages where possible: ARISS, SatDump GitHub, SDRangel readmes, packages.ubuntu.com, NOAA OSPO, SatNOGS DB, EGNOS and rtl-sdr.com. The calculations are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/goals_calc/budget.py and scen.py. Every power, RAM, CPU, pointing and QO-100 number they produce is a model.
  
  What is new compared with the register:
  - Metop is not necessarily Lime/Airspy-bound: an RTL decoded it at 2.88 Msps (SatDump #727), and Metop-B AHRPT is live in 2026.
  - A true L-band patch can replace the helix and SAWbird+ iO in the patch tier.
  - The dipole kit already meets the piece rule, so it can give LRPT a verified antenna in the patch tier.
  - The SDRangel Inmarsat filters are display-only, which confirms the blocker.
  - New menu errors: the SAWbird+ NOAA on the V4L tee; the HF+ offered for 437 MHz ISS; the VNA SWR leaf outside Bench mode; about 20 leaves bound to the Lime or the T7.
  - The LT3045 LNA rail cannot be built as written.
  - The CPU fallback (4-6 tiles/s) cannot keep up with even one V4L.
  - Several NPU classes cannot be observed without the Lime, and SSTV training data are scarce.
  - Black Kite has no decoder in SatNOGS; HamTV is active but blocked by the cavity.
  - The tinySA can fill the survey gap above 1.766 GHz.
  - Conflict #25 is stale.
  
  All 25 conflicts_for_final_checks are resolved in decisions C1-C25; L1-L12 are decisions from my lens.
  
  Physics limits restated objectively:
  - Patch and chip antennas cannot serve 137-146 MHz.
  - DATV and typical QO-100 SSB need dish-class gain.
  - Inmarsat-C bits must be demodulated before any header can be read.
  - Without loops, HF near the handheld is limited by local noise.
  - Antenna S11 sweeps always radiate.
  
  Still unverified (do not quote as fact):
  - Current draws of the HF+, Boni-Whip, LNB and L-band patch, and the patch's current price.
  - Whether the V4L holds 2.88 Msps without drops on the Q6A.
  - Airspy Mini price.
  - tinySA sensitivity above 800 MHz.
  - Which Northwood-type stations are naval-operated.
  - The readsb military flag bit.
  - QAIRT licence terms for cloud use.
  
  Sources: https://github.com/SatDump/SatDump/issues/727 ; https://www.ariss.org/current-status-of-iss-stations.html ; https://github.com/f4exb/sdrangel/blob/master/plugins/channelrx/radioclock/readme.md ; https://github.com/f4exb/sdrangel/blob/master/plugins/channelrx/demodinmarsat/readme.md ; https://packages.ubuntu.com/noble/qsstv ; https://www.rtl-sdr.com/rtl-sdr-blog-active-l-band-patch-antenna-for-inmarsat-iridium-gps-back-in-stock/ ; https://www.electrokit.com/en/rtl-sdr-aktiv-antenn-l-band-1525-1660mhz ; https://www.ariss.org/hamtv-on-the-iss.html ; https://db.satnogs.org/satellite/98527/ ; https://space.oscar.wmo.int/satellites/view/meteor_m_n2_5 ; https://pre-egnos.gsc-europa.eu/services/open-service/open-service-realtime-performance ; https://www.ospo.noaa.gov/data/messages/2026/05/MSG_20260506_1452.html

## completeness:lens3 (run `wf_6ce87eb1-883`)

- **Lens:** RULES + LEGAL + SAFETY. I checked every final/*.json (19 files), the register in report_research.json, digest.md and minute-log.md against user_requirements.md for: loop antennas and H-field probes; antenna S11 on air; decoding private content; military targets and NPU classes; voice IQ retention; TX-capable software and the Lime TX; Wi-Fi/Bluetooth in QUIET; the Artemis stop; city tables and Kyiv constants; Ukrainian prices and law used as the base. I also wrote generic legal and safety notes for a receive-only lab in an unknown country. I searched with a JSON-path walker (/tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rules_lens/jgrep.py), ran an emission and DC-hazard model (rules_lens/calc.py), made 2 WebSearch calls and 7 WebFetch calls (2 of the fetches failed).
- **Issues:**
  1.
    - **Area:** Inmarsat-C EGC SafetyNET decoder path
    - **Components:**
      - SDRangel demodinmarsat plugin (inmarsatc lib)
      - labd EGC filter
      - stdcdec / Scytale-C (small stack)
      - SatDump inmarsat_support
    - **Problem:** Every planned backend decodes all packets first and filters later. The SDRangel plugin fills a Messages table, and its two regular-expression filters act only on the decoded Type and Message columns. labd filters only after it receives UDP output from that decoder, and the Expert SDRangel GUI would show every message. The small stack decodes with stdcdec or Scytale-C and filters afterwards, and it also keeps 'bulletin-board packets' in scope. All of this breaks the rule in user_requirements.md line 37: discard at header level; never reassemble, convert to text, display, log or store any payload; FleetNET is discarded too.
    - **Severity:** blocker
    - **Evidence:** lab_ui_hf.json design.menu_tree[13].backend ('UDP output to labd EGC allow-list filter'), final.ui_system.integration_table[7] ('EGC SafetyNET allow-list and the DSC category filter'); small_antenna_stack.json final.reachable[9].receiver ('stdcdec or Scytale-C filtered to SafetyNET and bulletin-board packets'), final.excluded_by_law_or_ethics[1]; the SDRangel readme fetched today: 'The Messages table displays only packets that contain messages', and the filters match the 'Type column' and 'Message column'.
    - **Fix:** 1. Remove the SDRangel demodinmarsat plugin and the SatDump inmarsat_support plugin from the build; the packaging audit fails if either is present. 2. Write a labd 'egc-gate'. BPSK demodulation, deinterleaving and Viterbi decoding are unavoidable (physics caveat). Then, in RAM, read each packet descriptor, drop every non-EGC packet before any payload bytes are copied, read the EGC service code, drop FleetNET, and only then assemble SafetyNET text. 3. Use bulletin-board packets only for frame lock, never display or store them. 4. Never tune LES or ship channels. 5. Gate the release on mixed recordings: no non-SafetyNET byte may reach text, display or disk. 6. If the gate is not ready by P7, ship without the Inmarsat-C profile and do not buy the SAWbird+ iO. The packet descriptor values must be taken from the decoder source (unverified here).
    - **Fix cost:** $0 in parts, about 2-4 developer days (estimate); -$49.95 if the profile is dropped
    - **Sources:**
      - https://raw.githubusercontent.com/f4exb/sdrangel/master/plugins/channelrx/demodinmarsat/readme.md
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md
  2.
    - **Area:** Antenna S11/VSWR sweeps (radiate)
    - **Components:**
      - foldable_antennas final build steps
      - small_antenna_stack NanoVNA
      - radio_lab safety_and_legal[0] / P0
      - lab_ui_hf VNA leaf
      - antennas verify
      - narrowband_sdr fixes
    - **Problem:** Final build and test steps still sweep a VNA into antennas, and radio_lab adds a loophole ('unless local rules explicitly allow'). Hard rule 1 has no exception. A model of a -10 dBm sweep into a 2 dBi antenna gives 87 dBuV/m at 3 m. That is about 33 dB above the FCC 15.209 limit above 960 MHz (54 dBuV/m), and 44 dB above GPS C/A (-128.5 dBm) at 100 m on L1. The sweeps also cross the 1400-1427 MHz passive band (ITU RR 5.340, from memory).
    - **Severity:** blocker
    - **Evidence:** foldable_antennas.json final.build_and_test_steps[1],[2],[3],[9], loss_table[1],[11], ultra_compact_tier ('VNA-tune it'), foldable_kit[0]; small_antenna_stack.json final.first_tests[2] ('NanoVNA, briefly and indoors: tune the 20 cm helical whip'), revised_stack[29] ('Sweep briefly indoors'), legal_notes[7]; radio_lab.json final.safety_and_legal[0] and procedures[0].steps[4] ('unless local rules explicitly allow'), open_questions[14]; lab_ui_hf.json final.ui_system.menu_tree[56] ('Quick SWR/S11 page', not gated by Bench mode); antennas.json fixes.fixes[1].steps[2], verify.known_problems_and_fixes_to_apply[0],[7]; narrowband_sdr.json fixes.fixes[3].steps[4]. Model: rules_lens/calc.py.
    - **Fix:** 1. Delete every antenna S11 step and the 'local rules' clause, and close radio_lab OQ14 and register #0 with 'No'. 2. Replace them with receive-only acceptance: calculated lengths and printed marks, antenna-versus-terminated noise rise, Sun and cold sky, QO-100 beacon, NCS and GNSS C/N0 (P9/P15). 3. Check baluns and matching sections conducted only, into SMD-resistor dummy loads, and cables by TDR with the antenna removed. 4. Put the VNA leaf behind the Bench interlock, labelled 'DUT/load only'. 5. Drop the small-stack NanoVNA purchase, which duplicates the LiteVNA 64.
    - **Fix cost:** $0; saves $60-130 (unverified NanoVNA price)
    - **Sources:**
      - https://www.law.cornell.edu/uscode/text/18/2511
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rules_lens/calc.py
  3.
    - **Area:** Loop antennas and H-field probes in final BOM lines
    - **Components:**
      - small_antenna_stack DIY 20 cm/12 cm loop
      - radio_lab PS-500 / generic E/H set
      - display.json DIY H-field probe
      - QFH options
    - **Problem:** Loop items are still priced or prescribed. Small stack final: the optional DIY 20 cm loop (+$20-40), loop alternatives in reachable and lost, the IMU 'satellite in the loop plane' cue, and loop A/B tests. radio_lab final: lab_bom[3] allows 'small H-loop probes', its cheaper alternative is an E/H probe set, lab_bom[40] is the PS-500 (mostly H loops), and totals and the verdict keep the H-probe branch. The register misses that display.json still builds a DIY 15 mm H-field loop probe. QFH antennas (two bifilar loops) are still listed as options: antennas research.alternatives[1] and foldable bands[0].options[9]. Neither QFH nor eggbeater is on any exclusion list.
    - **Severity:** blocker
    - **Evidence:** small_antenna_stack.json final.revised_stack[12],[22],[23],[26], reachable[2],[4],[7],[8], lost[0],[9],[11], first_tests[2],[7],[8], borderline_options[2], size_rule_used, cost_size_power_delta; radio_lab.json final.lab_bom[3],[40], totals, verdict, open_questions[0],[1]; display.json fixes.fixes[5].steps[2] ('Make a DIY H-field probe: a 15 mm loop'); antennas.json research.alternatives[1]; foldable_antennas.json bands[0].options[9]. user_requirements.md lines 11 and 31.
    - **Fix:** Strike every loop row, cue, test and cost. Use E-field semi-rigid stub probes only, and replace the display.json H-probe step with an E-field stub. Add a 'loop-type antennas excluded' list: small and magnetic loops, QFH, eggbeater, quad, delta, biquad, halo, big wheel, ferrite loopsticks and coils (CANADUINO, AS3935), and H-field probes.
    - **Fix cost:** $0; saves $20-40 (loop) and $50-109 (H-probe line)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md
  4.
    - **Area:** VLF SID in the final menu and capabilities
    - **Components:**
      - lab_ui_hf menu SID
      - lab_ui_hf hf_capabilities[7]
      - radio_lab capabilities[16]
    - **Problem:** The final menu still offers 'VLF/LF carrier-amplitude logging', and radio_lab still lists 'SID carrier logging'. The 16-25 kHz carriers are naval transmitters, so this is a receive chain aimed at military transmitters, which the delegated decision forbids.
    - **Severity:** blocker
    - **Evidence:** lab_ui_hf.json final.ui_system.menu_tree[32] ('SID space weather: VLF/LF carrier-amplitude logging'), final.hf_capabilities[7]; radio_lab.json final.capabilities[16]; user_requirements.md line 36.
    - **Fix:** Rename the leaf 'SID (civil LF carriers)'. labd allow-lists DCF77 77.5 kHz, MSF and WWVB 60 kHz, JJY 40/60 kHz and TDF 162 kHz, records amplitude only, and refuses any SID tuning between 3 and 30 kHz.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md
  5.
    - **Area:** Voice IQ retention
    - **Components:**
      - npu_training class nfm_voice
      - npu_training retention.py
      - lab_ui_hf MARK / Record and collect
      - labrx ring snapshots
    - **Problem:** Voice is still kept as IQ. nfm_voice keeps IQ snippets of 0.25 s or less on the device. Raw IQ is kept 14 days, and voice bins are masked only after labelling. MARK saves 'the last N s from the RAM ring plus live IQ' even when the box is voice. All of these can be demodulated later, against the rule 'voice is spectrogram-only'.
    - **Severity:** blocker
    - **Evidence:** npu_training.json final.class_list[9] ('IQ snippets 0.25 s or less and kept on the device'), final.datasets[0].licence ('raw IQ is retained 14 days or masked'), final.scripts_to_write[25] ('masking ... after labelling'); lab_ui_hf.json final.ui_system.menu_tree[66]; user_requirements.md line 34.
    - **Fix:** 1. Persist no IQ for voice-tagged boxes; MARK on a voice box saves only the magnitude spectrogram crop. 2. labrx masks voice bins, taken from detector boxes plus the band plan, when a snapshot is written to UFS, not after labelling. 3. Refuse a raw-IQ pin that overlaps an unmasked voice box. 4. Exempt only broadcast programme audio (FM, AM, DRM, DAB).
    - **Fix cost:** $0, about 1 developer day (estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  6.
    - **Area:** Private networks and dual-use targets in the small-stack catalogue
    - **Components:**
      - Iridium NEXT target
      - Orbcomm OG2 target
      - SAWbird+ IR
      - CARTOSAT-3
      - gr-iridium IRA/IBC
    - **Problem:** The small-stack final still lists Iridium NEXT as 'reliable (carrier only)', with an optional SAWbird+ IR bought only for it, and Orbcomm OG2 as a target. Its bands and stack sections still rate Iridium IRA/IBC frames 'reliable', tell the decoders to keep 'Iridium IRA/IBC' frames, and justify S-band with CARTOSAT-3, a dual-use satellite. No user goal needs Iridium or Orbcomm. A burst-Doppler log of a private network is traffic metadata, and Iridium carries military users.
    - **Severity:** major
    - **Evidence:** small_antenna_stack.json final.reachable[8],[13], revised_stack[30], verdict ('Iridium is carrier and Doppler only'); bands[1].notes ('Filter the decoders to SafetyNET, bulletin-board and Iridium IRA/IBC'); stack.add[9], stack.remove[0], stack.sdr_decision, stack.revised_bom[23], stack.risks[7] (CARTOSAT-3); report_research register decision #1.
    - **Fix:** Remove Iridium and Orbcomm as targets. They show up only as unnamed occupancy in surveys: no Doppler product, no NPU class, no SAWbird+ IR. Delete every CARTOSAT-3 row. S-band (only with the Lime) is justified by Black Kite-1/2 housekeeping telemetry (a civil Rapidtek/TASA IoT CubeSat, verified; its LoRa IoT payload stays undecoded) and by amateur and science signals.
    - **Fix cost:** $0; saves $49.95
    - **Sources:**
      - https://db.satnogs.org/satellite/98527/
      - https://www.everythingrf.com/news/details/21257-rapidtek-successfully-launches-black-kite-1-with-taiwan-space-agency-to-advance-leo-iot-constellation
  7.
    - **Area:** HF/VHF text decoders without allow-lists (DSC, SITOR-B, RTTY/CW/PSK skimmer)
    - **Components:**
      - lab_ui_hf menu DSC
      - SITOR-B
      - CW/RTTY/PSK31 skimmer
      - SDRangel DSC demod
    - **Problem:** DSC 'hides' routine individual calls only after decoding them, and those calls carry the sender and addressee MMSIs. SITOR-B and the RTTY/CW/PSK skimmer decode on any tuned frequency, so outside the amateur and MSI channels they will print utility traffic: commercial telex, military or diplomatic RTTY, STANAG. UK WTA 2006 s48 makes it an offence to use apparatus 'with intent to obtain information as to the contents, sender or addressee' of messages not meant for the user, and to disclose them. Germany's §5 TDDDG allows listening only to messages meant for the operator, radio amateurs, the general public or an unspecified group of people.
    - **Severity:** major
    - **Evidence:** lab_ui_hf.json final.ui_system.menu_tree[25] (SITOR-B), [26] ('Routine individual calls are hidden and not stored'), [31] (CW/RTTY/PSK31); integration_table[7] ('DSC category filter'). The UK s48 and DE §5 texts were fetched today.
    - **Fix:** 1. labd gets a per-mode decode allow-list. RTTY/PSK/CW text only inside the amateur allocations of the region band plan, plus named public met broadcasts (the DWD RTTY list, to verify). SITOR-B only on the GMDSS HF MSI frequencies (4209.5, 4210, 6314, 8416.5, 12579, 16806.5, 19680.5, 22376 and 26100.5 kHz, from memory, to verify). 2. DSC: drop each frame at the format specifier. Keep distress and all-ships calls with distress, urgency or safety categories; drop individual and group calls before the address or self-ID fields are emitted. 3. Remove the SDRangel DSC plugin from the build if it cannot be configured to do this.
    - **Fix cost:** $0, about 1-2 developer days (estimate)
    - **Sources:**
      - https://www.legislation.gov.uk/ukpga/2006/36/section/48
      - https://dejure.org/gesetze/TDDDG/5.html
  8.
    - **Area:** QUIET/field mode leaves Bluetooth on
    - **Components:**
      - lab_ui_hf HF Quiet
      - System > Radios
      - FCU760K Wi-Fi/BT module
    - **Problem:** In the lab UI final, HF Quiet and 'Radios off/on' block Wi-Fi only, and the HF+ setup text says 'Wi-Fi rfkill'. The delegated rule is rfkill on wlan AND bluetooth. Nothing tests that the out-of-tree Wi-Fi driver actually honours rfkill.
    - **Severity:** major
    - **Evidence:** lab_ui_hf.json final.ui_system.menu_tree[34], [98] ('Wi-Fi (off by default in the field)'), final.hf_receiver.setup[8]; radio_lab.json final.procedures[0].steps[2] (compliant); user_requirements.md line 32.
    - **Fix:** 1. Every QUIET, field, pass and recording profile runs rfkill block wlan plus rfkill block bluetooth. 2. Bluetooth is disabled for good: mask bluetooth.service, blacklist the BT driver, persist the rfkill state. 3. Radios are blocked at every boot; Wi-Fi is unblocked only at home, by hold-to-confirm. 4. A self-test checks with the tinySA that 2.4 GHz emissions stop.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  9.
    - **Area:** Artemis identification-only stop
    - **Components:**
      - lab_ui_hf Signals AI > Live labels
      - labclassify
    - **Problem:** 'Tap a label for the offline Artemis entry' has no stop rule, and nothing defines what triggers the stop. A naive 'government' match would also stop on civil services such as weather satellites, time standards, NAVTEX and NOAA Weather Radio. The out-of-scope log could become a log of military emitters if it keeps frequency or position.
    - **Severity:** major
    - **Evidence:** lab_ui_hf.json final.ui_system.menu_tree[65]; radio_lab.json final.procedures[21].steps[1] and software[7] (stop rule present); user_requirements.md line 33. Artemis 4.2.0 category names are unverified.
    - **Fix:** labclassify treats a match as out of scope when the Artemis category is Military, Radar or Numbers, or the description names a military, navy, air force, intelligence, EW, jammer or OTH user. The box then shows only 'out of scope', and MARK, record, label, decode and export are disabled on it. The log row is UTC plus 'out of scope' only, with no frequency, location or bearing. Civil government services in the target catalogue are allow-listed so they never trigger the stop.
    - **Fix cost:** $0, about 0.5 developer day
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  10.
    - **Area:** Emitter geolocation through the UI
    - **Components:**
      - Interference hunt bearing log
      - GNSS-tagged survey heat map
      - SDRangel Heat Map plugin
    - **Problem:** A saved bearing log from the IMU heading, a 'GNSS-tagged heat map' survey and SDRangel's Heat Map plugin (named in the sweeps) together make an emitter-geolocation tool. That contradicts the NPU policy of no DF, AoA, geolocation or emitter tracks.
    - **Severity:** major
    - **Evidence:** lab_ui_hf.json final.ui_system.menu_tree[47] ('a bearing log from the IMU heading'), [45] ('GNSS-tagged heat map'), sweeps[2].options[6].key_specs (Heat Map); npu_training.json final.class_list[27]; register decision #12.
    - **Fix:** Interference hunting becomes a live readout that is never saved. A survey carries one rounded site tag per session and no spatial power map. The packaging audit fails if the SDRangel Heat Map plugin is present.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  11.
    - **Area:** No out-of-scope band mask for surveys and NPU logs
    - **Components:**
      - labrx survey
      - labclassify detection log
      - rtl_power heatmaps
    - **Problem:** Generic surveys from 0.5 to 1766 MHz and 'unknown_energy' detection boxes store GNSS-tagged activity in military bands: 225-400 MHz military aero UHF with SATCOM at 240-320 MHz and MUOS at 360-380 MHz, and VLF at 3-30 kHz. The result is an activity record of military emitters, which the VLF SID precedent and the Artemis stop rule out. Germany's §5(2) TDDDG also forbids passing on the fact that a non-public message was received.
    - **Severity:** major
    - **Evidence:** radio_lab.json final.capabilities[2] (0.5 MHz-1.766 GHz survey); lab_ui_hf.json final.ui_system.menu_tree[45], [72]; npu_training.json final.class_list[25] (unknown outcomes); small_antenna_stack.json final.excluded_by_law_or_ethics[5].
    - **Fix:** Add a labd band mask that the region profile can adjust. Defaults: 3-30 kHz and 225-400 MHz, with 328.6-335.4 MHz (ILS glide path) left visible. Inside the mask: live waterfall only; storage keeps only the band-mean noise floor; no boxes, snapshots or exports.
    - **Fix cost:** $0, about 1 developer day
    - **Sources:**
      - https://dejure.org/gesetze/TDDDG/5.html
  12.
    - **Area:** TX-capable software and hardware paths
    - **Components:**
      - wsjtx 2.7.0~rc3 GUI
      - fldigi 4.2.03
      - QSSTV 9.5.8
      - SoapyRemote 0.5.2
      - LimeSDR Micro TX
      - ADALM-PLUTO option
    - **Problem:** radio_lab final installs the full WSJT-X GUI and fldigi, and so do the small stack and P20. lab_ui_hf installs QSSTV, which can transmit, as an 'RX-only fallback'. radio_lab lists SoapyRemote, which serves the Lime TX streams to any LAN client and bypasses the ExecStartPre lint. The guard itself is a text lint: a script that passes direction 0 instead of SOAPY_SDR_TX gets past it. The Pluto option adds a second TX device, and whether it emits anything at power-up is unverified.
    - **Severity:** major
    - **Evidence:** radio_lab.json final.software[8], [11], procedures[20].steps[1], capabilities[16]; small_antenna_stack.json final.revised_stack[28], reachable[15], first_tests[5], revised_stack[31]; lab_ui_hf.json final.ui_system.tech_stack ('qsstv 9.5.8 and gqrx 2.17.4 (both RX-only fallbacks)'); register decisions #10, #11, #89.
    - **Fix:** 1. Install only jt9 and wsprd. 2. Drop fldigi, QSSTV (SatDump or an RX-only SSTV decoder covers SSTV) and SoapyRemote. 3. Patch the lab build of LimeSuiteNG and its Soapy module so any TX stream setup fails hard. Keep BUILD_GUI=OFF, the 50-ohm loads on the TX ports and the guard. 4. Do not adopt the Pluto. 5. The packaging audit checks for these binaries. 6. If the Lime is kept, check its TX ports with the tinySA after every boot.
    - **Fix cost:** $0, about 1 developer day
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  13.
    - **Area:** City tables and Kyiv constants; no bootstrap rule
    - **Components:**
      - gnss_imu WMM constants
      - dish_replacement pointing table
      - antennas/foldable/small stack angles
      - digest.md
    - **Problem:** Fixed angles and field values still stand in for computation. dish_replacement has a four-city pointing table (Kyiv 186/32, Lviv 178/33, Kharkiv 193/32, Odesa 187/36). gnss_imu has Kyiv and Odesa field values (F 51.05 uT, dip 67.6 deg, D +8.5 deg). Kyiv angles appear in antennas, foldable and small-stack finals, and in digest.md. Summary #128 offered a city list. There is still no first-boot rule for no saved fix with an unset RTC.
    - **Severity:** major
    - **Evidence:** dish_replacement.json fixes.fixes[0].steps[3], verify.known_problems_and_fixes_to_apply[4],[11]; gnss_imu.json fixes.fixes[5],[6], verify.known_problems_and_fixes_to_apply[7]; antennas.json fixes.fixes[0].steps[3], verify.issues[2], known_problems[10]; foldable_antennas.json final.loss_table[10], other_ways_out[4], build_and_test_steps[6]; small_antenna_stack.json final.first_tests[4],[5], reachable[9],[12],[14]; digest.md lines 116, 140, 914, 975.
    - **Fix:** 1. Compute every az/el and the WMM2025 declination, dip and field strength at the current fix. 2. Bootstrap: accept the first fix when it is 3D, has 8 or more satellites and stays within 50 m for 5 min; if the RTC is unset, accept GNSS time flagged 'unverified' until NTP over home Wi-Fi or a second session confirms it. 3. Fallbacks are the last good fix with its age, or manual lat/lon or Maidenhead entry. 4. No city list anywhere.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/gnss_imu.json
  14.
    - **Area:** Ukrainian law and prices used as the base
    - **Components:**
      - small_antenna_stack legal_notes
      - display_market purchase
      - compute/wideband/storage/power/gnss_imu prices
    - **Problem:** The small-stack legal notes are built on Ukrainian law: NKEK, martial law, Criminal Code 163/359/114-2, DSNS and SES-cleared land. Its cost delta counts Ukrainian duty, and display_market has a 'ukraine_purchase' field with UAH and EUR 150 duty-threshold pricing. Ukrainian price bases also remain in compute, wideband, storage, power, gnss_imu and foldable. The user is not in Ukraine.
    - **Severity:** major
    - **Evidence:** small_antenna_stack.json final.legal_notes[1]-[6], reachable[1].legal, reachable[11].legal, refuted_claims[6], excluded_by_law_or_ethics[3], revised_stack[0], cost_size_power_delta; display_market.json final.ukraine_purchase, main_pick.price, above_fhd_tier.price, ranked_candidates[1],[3],[5], open_questions[5],[7],[8]; foldable_antennas.json final.total_cost; register decision #6.
    - **Fix:** Re-price at world prices in P5. Replace the legal notes with the generic note in notes. Ukraine survives only as an optional 'restricted' region-profile example.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md
  15.
    - **Area:** Air travel with the DIY 4S pack
    - **Components:**
      - 4S1P Molicel P50B 72 Wh pack
      - 88.8 Wh PD bank
    - **Problem:** radio_lab tells the user to carry the 72 Wh receiver pack in cabin baggage because it is under 100 Wh. IATA also requires batteries to be 'of a type that meets the requirements of the UN Manual of Tests and Criteria, Part III, subsection 38.3'. A home-welded 4S1P has no UN 38.3 test summary.
    - **Severity:** major
    - **Evidence:** radio_lab.json final.safety_and_legal[6]; IATA passenger lithium battery guide (fetched today): up to 100 Wh in carry-on, spares in carry-on only with insulated terminals, UN 38.3 type requirement.
    - **Fix:** Rewrite SL6: never fly with the DIY pack. Fly with the commercial bank (100 Wh or less, terminals insulated) for bench work. For field use after a flight, buy or build a pack at the destination, or use a commercial 4S Li-ion pack that comes with a UN 38.3 summary (price unverified).
    - **Fix cost:** $0 (rule); a commercial pack is unpriced
    - **Sources:**
      - https://www.iata.org/contentassets/6fea26dd84d24b26a7a1fd5788561d6e/passenger-lithium-battery.pdf
  16.
    - **Area:** Battery fire and thermal-runaway design
    - **Components:**
      - 4S P50B pack
      - IP2368 board
      - ASA shell
      - mid-plate
    - **Problem:** No study designs pack containment. The 72 Wh pack sits in an ASA shell next to an IP2368 whose MOSFET went above 100 C at 5 A, with one report of a spontaneous burn-out. There is no barrier, no vent path, no charging-supervision rule and no storage state-of-charge rule. The grep found no mention of 'thermal runaway', a fire bag or UN 38.3.
    - **Severity:** major
    - **Evidence:** mechanical_thermal.json verify.final_recommendation (no pack bay); power.json fixes.fixes[5] ('spontaneous burn-out', 'over 100 C at 5 A'), verify.known_problems_and_fixes_to_apply[5],[6].
    - **Fix:** 1. Separate the pack bay from the electronics with the 2 mm aluminium mid-plate, or 1 mm FR-4 or mica. 2. Use fish paper, insulator rings and glass-fibre tape; spot-weld, never solder. 3. Give the bay a vent path to the outside, away from the grip and face. 4. Charge only when attended, on a non-flammable surface or in a fire-resistant bag. 5. Keep the existing 0-45 C NTC and the 70 C KSD9700. 6. Store at 3.6-3.8 V per cell, and retire swollen or dented cells.
    - **Fix cost:** About +$10-25 (estimate, unverified)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/power.json
  17.
    - **Area:** Bias onto DC-shorted antennas through the librtlsdr API
    - **Components:**
      - librtlsdr .so.2 rebuild
      - V4L 4.5 V tee
      - 9:1 balun, hairpin Yagis
    - **Problem:** Any process can call rtlsdr_set_bias_tee, and the EEPROM can make bias the default. labd's interlock binds only the daemons that go through it, and the DC-shorted antennas (hairpin matches, the 9:1 path) can burn the tee's LDO or fuse.
    - **Severity:** major
    - **Evidence:** report_research register decision 'Bias onto DC-shorted antennas'; minute-log.md 05:19 (librtlsdr lets any process enable bias).
    - **Fix:** In the .so.2 rebuild, make the bias-tee calls fail unless /run/labd/bias/<serial> exists. Set the EEPROM bias default to off. Require DC-sense before enabling.
    - **Fix cost:** $0
    - **Sources:**
      - /home/user/lizbeth307/sat-receiver-audit/minute-log.md
  18.
    - **Area:** LNB and DC hazard leftovers
    - **Components:**
      - lab_ui_hf QO-100 leaf
      - rf_frontend LNB supply
      - radio_lab SL3
      - foldable
    - **Problem:** The final menu still offers 'LNB 13.4 V (V) / 18.2 V (H)', SL3 still says '13-18 V', rf_frontend still has the switchable 13.4/18.2 V boost, and foldable says '18 V or rotate'. No rule covers hot-plugging the LNB. In the model, 13.2 V puts 3.5 W into a 1 W ANNE-50+ load and is 8.2 V above the tinySA's 5 V DC limit; 18.2 V would put 6.6 W into the load.
    - **Severity:** minor
    - **Evidence:** lab_ui_hf.json final.ui_system.menu_tree[15]; radio_lab.json final.safety_and_legal[3]; rf_frontend.json verify.final_recommendation; foldable_antennas.json final; rules_lens/calc.py.
    - **Fix:** 13.2 V only, current-limited. labd enforces 'feed off before connect or disconnect' with hold-to-confirm. A DC block goes toward every SDR and instrument, and the LNB is never on the sled, AUX or the raw pack.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rules_lens/calc.py
  19.
    - **Area:** Region and legal profile only in the NPU
    - **Components:**
      - labd
      - npu_training region profile
      - lab_ui_hf Region page
    - **Problem:** Only the NPU has a standard/restricted region profile, its default is 'standard', and the lab region is picked by hand. In an unknown country, ADS-B/AIS handling, VHF listening presets, UAT, NOAA SAME, HD Radio and upload defaults all need a lab-wide legal default.
    - **Severity:** minor
    - **Evidence:** npu_training.json final.ui_flows[12]; lab_ui_hf.json final.ui_system.menu_tree[99].
    - **Fix:** Make the region profile lab-wide in labd. It is derived from the GNSS fix through offline Natural Earth admin-0 polygons (public domain; jurisdiction only, not a location fallback) and is 'restricted' until a fix exists. The user can edit it.
    - **Fix cost:** $0, about 1 developer day
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  20.
    - **Area:** Generic legal and privacy notes
    - **Components:**
      - radio_lab safety_and_legal[9]
      - SigMF exports
      - tar1090
      - radiosonde chase
    - **Problem:** The generic note does not say that secrecy laws differ: the UK and Germany restrict listening to and disclosing non-public messages, while US 18 USC 2511(2)(g) allows radio communications that are readily accessible to the general public. SigMF exports outside the NPU keep the exact GNSS position, which reveals the user's home. tar1090 military and 'interesting' filters are not disabled. There are no radiosonde-chase safety rules.
    - **Severity:** minor
    - **Evidence:** radio_lab.json final.safety_and_legal[9], procedures[21].steps[0] (GNSS geolocation in every recording); lab_ui_hf.json final.ui_system.verdict ('SigMF: geolocation goes in each capture'); npu_training.json final.pipeline[24] (rounding only in NPU exports).
    - **Fix:** Add the legal note given in notes. Round the location in every export to 0.1 deg or a 4-character locator. Disable tar1090's military and 'interesting' filters. Sonde chase: obey traffic rules, respect private land and airfields, never climb trees or poles, keep away from power lines.
    - **Fix cost:** $0
    - **Sources:**
      - https://www.legislation.gov.uk/ukpga/2006/36/section/48
      - https://dejure.org/gesetze/TDDDG/5.html
      - https://www.law.cornell.edu/uscode/text/18/2511
  21.
    - **Area:** Public broadcasts from military-operated stations
    - **Components:**
      - HF WEFAX schedule
      - NAVTEX/MSI
    - **Problem:** No boundary is defined. GYA Northwood is a Royal Navy broadcast (hobbyist sources), and NMF/NMG/NMC are US Coast Guard (an armed service), yet NAVTEX is an explicit user target. Without a rule, the VLF precedent is applied inconsistently.
    - **Severity:** minor
    - **Evidence:** radio_lab.json sweeps[2].procedures[3].steps[0] (NMF/NMG/NMC), capabilities_added[3]; lab_ui_hf.json final.ui_system.menu_tree[27]; hfunderground and goughlui pages on GYA.
    - **Fix:** Apply proposed decision D-B: the default schedule holds civil met services plus public MSI. GYA stays out pending the user's answer.
    - **Fix cost:** $0
    - **Sources:**
      - https://hfunderground.com/wiki/index.php/Maritime_Fax_Transmissions
      - https://goughlui.com/2019/01/28/radiofax-gya-northwood-united-kingdom/
  22.
    - **Area:** Radiosonde scan overlaps the Cospas-Sarsat band
    - **Components:**
      - radiosonde_auto_rx scan settings
    - **Problem:** The 400-406 MHz scan includes 406.0-406.1 MHz, where the excluded EPIRB/PLB distress beacons transmit.
    - **Severity:** minor
    - **Evidence:** lab_ui_hf.json final.ui_system.menu_tree[42] ('400-406 MHz scan range'); small_antenna_stack.json final.excluded_by_law_or_ethics[10].
    - **Fix:** Set the auto_rx scan to 400.0-405.9 MHz.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  23.
    - **Area:** Outdoor antenna safety gaps
    - **Components:**
      - telescopic V-dipole
      - tape Yagi elements
      - throw line
      - masts and tripods
    - **Problem:** The lightning rule in the radio_lab sweeps depends on the excluded AS3935. Nothing covers eye injury from telescopic tips or tape-measure edges, a throw-weight hitting someone, or a mast in wind. The power-line rule appears only in the HF wire setup.
    - **Severity:** minor
    - **Evidence:** radio_lab.json sweeps[2].procedures[5].steps[4] (AS3935 storm rule); lab_ui_hf.json final.hf_antenna.setup[0]; radio_lab.json final.safety_and_legal[5].
    - **Fix:** Add rules: 30/30 thunder rule (no AS3935), take antennas down at first thunder, discharge before connecting; keep at least 2x the antenna or wire height from overhead lines; tip caps on telescopic and tape elements; eye protection when throwing a line; guy or lower masts above about 20 km/h wind (estimate).
    - **Fix cost:** About +$2-5 for tip caps (estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  24.
    - **Area:** QAIRT Set B in the NPU device plan
    - **Components:**
      - onnxruntime 1.27 + onnxruntime-qnn 2.3.0 (QAIRT 2.47)
    - **Problem:** Set B is still in the architecture, software, pipeline and roadmap, although the rule is INT8 on QAIRT 2.42.
    - **Severity:** minor
    - **Evidence:** npu_training.json final.architecture, software[5], pipeline[19], roadmap[3]; register decision #38.
    - **Fix:** Delete Set B from the device plan. If Phase 0 fails on 2.42, ask the user before using any newer QAIRT.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  25.
    - **Area:** Process: HF-loop removal has no recorded user message
    - **Components:**
      - user_requirements.md line 11
    - **Problem:** The governing file says the user removed the HF active loop, but the transcript records no such message; the last HF message (01:54) asked to add one. The rule stands, but it should be confirmed.
    - **Severity:** minor
    - **Evidence:** report_research register decision #5; summaries.md verifier check.
    - **Fix:** Keep the ban, which is the governing rule. Ask the user at the next phase end. If loops are allowed again, an LZ1AQ-class active loop returns as the HF/LF antenna and H-field probes as bench tools.
    - **Fix cost:** $0
    - **Sources:**
      - /home/user/lizbeth307/sat-receiver-audit/summaries.md
- **Proposed decisions:**
  1.
    - **Question:** C1. LimeSDR Micro M.2: keep or drop?
    - **Decision:** Gated optional. Keep the cancellable pre-order (ships 15 Dec 2026) and decide on delivery or 31 Jan 2027. No core function, menu default or NPU MVP profile depends on it. If kept: 50-ohm loads on the TX ports, LimeSuiteNG with BUILD_GUI=OFF and AMARISOFT=OFF plus a patch that makes TX stream setup fail, no SoapyRemote, and every dependent item tagged conditional (CPU7, riser/J21, 10 W cooling, T7, LIME-W/F/B, 7.5 A fuse, sled COM, P4/P5/P7/P14/P18, REF IN, S-band).
    - **Reason:** Every core target runs on 2-3 V4Ls plus the HF+. The Lime is the only TX-capable part, so dropping it makes the kit physically receive-only, the strongest legal position.
    - **Consequences:** Without it: no S-band, Metop AHRPT marginal, NPU loses 3 of 5 profiles; about $650-665 avoided, including the T7. With it: 45-52 W peak and a 7.5 A fuse.
    - **Alternatives rejected:** ADALM-PLUTO (also TX-capable, duplicates the Lime); buying unconditionally now.
  2.
    - **Question:** C2. Q6A RAM tier
    - **Decision:** Buy the 12 GB board now (P2 sourcing: TinyTronics about $137 ex VAT / $166 incl. VAT; ALLNET $189.99). RAM ring: 4 GiB with Lime and training, 1.5 GiB or less without the Lime.
    - **Reason:** RAM is soldered and cannot be upgraded. NPU training, SatDump, SDRangel and the Lab Shell together are unmeasured.
    - **Consequences:** About $25-54 more than 8 GB. No effect on the rules.
    - **Alternatives rejected:** 8 GB (cannot be fixed later).
  3.
    - **Question:** C3. Pack: 3S or 4S?
    - **Decision:** 4S1P Molicel P50B (72 Wh) with a regulated 12 V rail into J21. 13.2 V LNB rail, 12.5 V Boni-Whip LDO, 10k NTC charging window 0-45 C. Fuse 7.5 A with the Lime, 5 A without. The DIY pack is never flown.
    - **Reason:** Every downstream rail gets headroom and regulation, including the noise-source ENR stability. 72 Wh is under the 100 Wh class, but a DIY pack has no UN 38.3 summary.
    - **Consequences:** A 12 V regulator is needed, and the field pack does not travel by air.
    - **Alternatives rejected:** 3S feeding J21 directly (no headroom for 13.2 V; ENR drift).
  4.
    - **Question:** C4. 12 V regulator
    - **Decision:** Prototype on the D36V50F12 (buy 2, rationed stock): EN divider as a backstop, a supervisor driving the #2813 cut. Run the terminated-floor A/B at 40-162 kHz, 490/518 kHz, 2-30 MHz and 137/437/1544 MHz, and a sealed-case current test at 13.6-16.4 V. Switch to a forced-PWM buck-boost rated 5 A or more only if either test fails.
    - **Reason:** A verified part is available now, and the light-load spur risk can be measured.
    - **Consequences:** The rail drops out below about 13.3 V. That is harmless, because J21 accepts 4.5-16 V.
    - **Alternatives rejected:** Choosing before measuring.
  5.
    - **Question:** C5. USB port map
    - **Decision:** Freeze the Lime-agnostic map. Blue USB 3.1: RTL-A, or the T7 with the Lime. FE1.1s P1 RTL-B, P2 touch, P3 CH334F (HMI RP2040, IMU puck, LAB USB, HF+), P4 the internal FCU760K Wi-Fi/BT. HF+ and injectors are powered from LAB 5 V (VCC_5V_PERI is about 17 W).
    - **Reason:** One map has to work with or without the Lime. Wi-Fi shares the FE1.1s tree, so it is off during jobs anyway.
    - **Consequences:** The J5 labels and the FCU760K name are settled in STACK.md.
    - **Alternatives rejected:** The four divergent per-study maps.
  6.
    - **Question:** C6. 40-pin and bus map; IMU interface
    - **Decision:** PPS pin 7 (GPIO96); console 8/10; UART6 16/18 (LC76G); I2C0 13/15 for the INA228 only, from user space; I2C2 27/28 for MCP23017 x2 (+TCA9535) and the RP2040 target; fan via pwm-gpio on pin 33; spi14 off. The IMU is the USB-CDC RP2040 puck on the boom.
    - **Reason:** Keeps the magnetometer away from the cells, the fan and DC currents, and avoids the BNO08x I2C problems on Linux. UART7 is unverified.
    - **Consequences:** The puck uses one CH334F port.
    - **Alternatives rejected:** BNO085 on I2C2; a UART7 relay.
  7.
    - **Question:** C7. Hardware and policy ownership
    - **Decision:** labd is the single owner of lines, leases and interlocks, and the single enforcement point for policy: receive-only guard, rfkill, bias token, Bench interlock, region profile, Artemis stop, band mask, decode allow-lists. labrx owns the single RAM ring and recorder and applies voice masking. labclassify runs inferd and fusiond. rflab becomes a labd module, with one lease mechanism.
    - **Reason:** Rules can be enforced reliably only at one choke point.
    - **Consequences:** The npu_training daemon names are merged.
    - **Alternatives rejected:** Three daemons and three lock schemes.
  8.
    - **Question:** C8. LNB supply
    - **Decision:** 13.2 V ±0.2 V measured at the F connector under load, vertical only, true 0 V disconnect, switch rated 20 V or more, no 18 V branch. One current limit at 1.5-2x the measured Bullseye draw. Feed off before connect or disconnect. DC block toward the SDR.
    - **Reason:** 18 V only selects horizontal, which every tier loses anyway. 13.2 V into a 50-ohm load is 3.5 W.
    - **Consequences:** Rotate the LNB 90 deg for horizontal humps.
    - **Alternatives rejected:** Switchable 13.4/18.2 V; the 12 V rail through a tee (10.6-11.4 V).
  9.
    - **Question:** C9. LNA bias rule
    - **Decision:** Every SAWbird+ runs from a TPS2553 at 250-300 mA. The V4L tee feeds only LNAs of 80 mA or less. Delete the 100-160 mA PTC and the 'GOES+ on the V4L tee' allowance. Cased SAWbird+ ($49.95) in the field; Barebones ($44.95) only inside the shielded bay.
    - **Reason:** The SAWbird+ NOAA draws 170 mA and the GOES 180 mA, against the tee's 180 mA.
    - **Consequences:** One injector channel per SAWbird+.
    - **Alternatives rejected:** A polyfuse that trips at its own working current.
  10.
    - **Question:** C10. FM filter
    - **Decision:** Nooelec Flamingo+ FM (250 mA DC pass) permanently in the 137/145 MHz path. The second VHF/UHF entry needs its own filter (completeness lens).
    - **Reason:** One part with a published DC rating.
    - **Consequences:** Needs a second filter for the second VHF/UHF entry.
    - **Alternatives rejected:** Mixing the RTL-SDR Blog and Flamingo filters.
  11.
    - **Question:** C11. librtlsdr
    - **Decision:** Use only the .so.2 rebuild of noble 2.0.1 with 0204c9c and 65f0658, plus a patch: bias-tee calls fail unless the labd token /run/labd/bias/<serial> exists. EEPROM bias default off.
    - **Reason:** One ABI for all consumers, and DC-shorted antennas need bias protection.
    - **Consequences:** One small patch to keep across rebuilds.
    - **Alternatives rejected:** 2.0.3 (.so.0) with every consumer rebuilt; purge-and-fork.
  12.
    - **Question:** C12. Display field-mode pixel clock
    - **Decision:** About 127.9 MHz (51.7 Hz at 2200x1125), or 164.4-168.4 MHz if the panel accepts it. The 1280x800 fallback needs per-profile mode switching plus shielding. The display on/off A/B covers 1415.7, 1544.4 MHz and the LF bands.
    - **Reason:** The local harmonic scan.
    - **Consequences:** Cmdline and EDID edits.
    - **Alternatives rejected:** 128.70 MHz (its 12th harmonic falls inside Inmarsat-C).
  13.
    - **Question:** C13. Kernel hold and PPS
    - **Decision:** Build pps-gpio out of tree on 6.18.2-4 (CONFIG_PPS=y). Drop gnss_imu Route B (7.0.11). Build pps-ldisc only if the FT232RL fallback stays.
    - **Reason:** The kernel hold protects HDMI and the NPU.
    - **Consequences:** One DKMS-style module.
    - **Alternatives rejected:** A kernel jump.
  14.
    - **Question:** C14. INA228
    - **Decision:** On I2C0 through user-space i2c-dev, with no DT binding. Shunt in the pack lead after the fuse. Fix npu_training's 'on the J21 rail'.
    - **Reason:** The hwmon driver would block the CHARGE register.
    - **Consequences:** labpowerd reads the registers directly.
    - **Alternatives rejected:** The ina238 hwmon driver.
  15.
    - **Question:** C15. Antenna tiers
    - **Decision:** The two-tier rule from user_requirements.md governs: patch/chip antennas, and foldable antennas with pieces of 20-23 cm or less (about 35 cm maximum). Every small-stack removal made under the old 'deployed 20 cm or less' rule is void and re-decided: Lime gated (C1), T7 only with the Lime (C18), 12 GB bought (C2), foldables restored. LRPT default: the telescopic V-dipole. Crossed Yagi default: the ultra-compact build. Small rigid whips and helices await the user's confirmation. All loops are struck.
    - **Reason:** The governing file was revised after the small-stack run.
    - **Consequences:** The small-stack verdict and stack sections become archive only.
    - **Alternatives rejected:** Keeping the 20 cm helical whip as the LRPT default.
  16.
    - **Question:** C16. Receive-only and policy leftovers
    - **Decision:** Strike every item in stale_items_to_purge before STACK.md. Add a CI grep over STACK.md and build/ for banned items: loop antennas, antenna S11, Iridium frames, VLF SID, 18 V, the wsjtx GUI, fldigi, QSSTV, SoapyRemote, Set B, city names, UAH base prices.
    - **Reason:** Leftovers would otherwise re-enter at P4/P5 re-research.
    - **Consequences:** About 70 edits across 13 files.
    - **Alternatives rejected:** Purging by hand only.
  17.
    - **Question:** C17. HF antenna chain
    - **Decision:** Boni-Whip on a 12.5 V LDO from 4S, with DC-sense and default OFF. The 9:1 wire is for HF only; LF time signals are credited to the active whip. Add a latching DC-capable HF+ input relay (HF / VHF-AIS / 50-ohm) to the BOM (part TBD). The HF-loop ban stays; confirm it with the user.
    - **Reason:** 12.5 V is inside both published ranges (9-15 V WiMo, 12-15 V SWLing). The WB9-1 is rated only from 0.125 MHz.
    - **Consequences:** The radio_lab and lab_ui_hf 10.0/12.0 V text is fixed.
    - **Alternatives rejected:** 10.0 V; leaving the selector off the BOM.
  18.
    - **Question:** C18. Storage and retention
    - **Decision:** T7 only with the Lime. Otherwise a V30/A2 microSD or USB stick for exports and updates, and an A/B root on UFS. Retention: products by default; raw IQ only when pinned, deleted after 14 days; voice bins masked when a snapshot is written; masked bands never stored. Dual-RTL raw is 36.9 GB/h, about 2.5 h on 92-100 GB free.
    - **Reason:** Rule compliance and real data rates.
    - **Consequences:** labrx implements the masking.
    - **Alternatives rejected:** Buying the T7 unconditionally.
  19.
    - **Question:** C19. CPU allocation
    - **Decision:** A55 cores 0-3: UI, daemons and the labclassify fallback. A78 cores 4-6: DSP. T2 training on cores 4-6 only between passes. CPU7 isolated only with the Lime; measure cpu4-6 against cpu7 for lime:Rx0.
    - **Reason:** Keeps pass capture deterministic.
    - **Consequences:** Training pauses during passes.
    - **Alternatives rejected:** Training on the A55 cores.
  20.
    - **Question:** C20. Roadmaps
    - **Decision:** NPU Phase 0 runs inside the W1-2 gates (19 Oct-1 Nov 2026), and a minimal labeller moves into P0b. The policy gates (class policy, voice masking, Artemis stop, band mask) ship before the first labeller. HF classes appear in the UI only after the HF-F and second-RTL profiles exist.
    - **Reason:** The rules must exist before any data is collected.
    - **Consequences:** About 2-3 extra developer days in P0b.
    - **Alternatives rejected:** Adding policy after data collection starts.
  21.
    - **Question:** C21. V4L count
    - **Decision:** Buy 3 (2 in service, 1 spare). Continuous ADS-B/AIS/sonde monitoring time-shares a receiver, with AIS on the HF+. A 4th only if the user asks.
    - **Reason:** Cost against continuity.
    - **Consequences:** Monitors pause during passes.
    - **Alternatives rejected:** Using the spare as a full-time monitor at $0.
  22.
    - **Question:** C22. Software recipes and exclusions
    - **Decision:** One venv per tool: NanoVNA-Saver via pipx, PySide6 6.12, libgpiod v1 API, Skyfield 1.55 from pip, SatDump 2.0 from source, OpenWebRX+ 1.2.126 with pins. Excluded: the wsjtx GUI (jt9 and wsprd only), fldigi, QSSTV, js8call, SoapyRemote, the SDRangel Inmarsat C, DSC and Heat Map plugins (replaced by labd gates), and URH. The packaging audit fails the build on any of them.
    - **Reason:** Receive-only and policy enforcement by construction.
    - **Consequences:** The DSC gate and egc-gate are own code.
    - **Alternatives rejected:** Installing the full GUIs and relying on lint.
  23.
    - **Question:** C23. Region unknown
    - **Decision:** Ask the user. Meanwhile labd derives the jurisdiction from the GNSS fix (offline Natural Earth admin-0 polygons, not a city table) and stays 'restricted' until a fix exists. GEO 'visible from here' flags are computed at the fix. Hold the LNB, horn and SAWbird+ iO purchases until the region is known.
    - **Reason:** Legal flags and GEO visibility depend on the region.
    - **Consequences:** A few MB of polygon data, edited by the user.
    - **Alternatives rejected:** A 'standard' default everywhere.
  24.
    - **Question:** C24. Costs and weights
    - **Decision:** Recompute in P5 at world prices. radio_lab extended about $555-780 without H-probes; internal interface $56-73; sling about 3.7-4.4 kg (4.4-6.05 kg with supports, per the completeness lens); HF chain including the relay. Remove the loop, H-probe, NanoVNA and SAWbird+ IR lines (and the iO if Inmarsat is dropped). Add about $12-30 of safety items.
    - **Reason:** The subtotals do not match their line items, and the rules remove items.
    - **Consequences:** The fix-cost table below.
    - **Alternatives rejected:** Keeping the stale subtotals.
  25.
    - **Question:** C25. P1b completion
    - **Decision:** Close it. final/report_research.json exists (576,735 B, 18 Oct 04:51). Add errata blocks to summaries.md and minute-log.md, and delete the 'does not exist' statements.
    - **Reason:** File check.
    - **Consequences:** None.
    - **Alternatives rejected:** None.
  26.
    - **Question:** D-A. Is any antenna S11 sweep allowed, for example briefly indoors?
    - **Decision:** No. The ban is absolute, with no 'local rules' exception. radio_lab OQ14 and register #0 are closed as 'No' unless the user explicitly changes hard rule 1.
    - **Reason:** Rule 1 is explicit. The model puts a -10 dBm sweep about 33 dB above a typical unlicensed limit at 3 m and about 44 dB above GPS C/A at 100 m. Physics: any S11 sweep radiates.
    - **Consequences:** Antennas are accepted by receive-only checks and conducted checks of their matching parts.
    - **Alternatives rejected:** Brief indoor uW sweeps; sweeps in a shield box (the box detunes the antenna; impractical).
  27.
    - **Question:** D-B. Public broadcasts from military-operated stations
    - **Decision:** Allowed: public MSI and met broadcasts intended for general reception (NAVTEX, EGC SafetyNET, DSC distress/urgency/safety, NWS charts via the USCG NMF/NMG/NMC). Excluded: military communications (VLF submarine broadcasts, HFGCS, STANAG data, military SATCOM and aero), and stations broadcasting mainly for armed forces (GYA Northwood) from the default schedule until the user answers.
    - **Reason:** The rule targets chains aimed at military communications. NAVTEX is an explicit user target. GYA is described as 'for the Royal Navy' (hobbyist sources).
    - **Consequences:** The WEFAX default is civil met services (DWD, JMH) plus NWS charts.
    - **Alternatives rejected:** A strict operator-based ban (it would remove US NAVTEX and WEFAX and contradict the user's own NAVTEX target).
  28.
    - **Question:** D-C. Iridium and Orbcomm
    - **Decision:** No named target, no Doppler product, no NPU class, no SAWbird+ IR. They appear only as unnamed occupancy in surveys.
    - **Reason:** No user goal; burst and Doppler logs are traffic metadata; Iridium carries military users.
    - **Consequences:** -$49.95.
    - **Alternatives rejected:** Register #1 'carrier and Doppler only' target.
  29.
    - **Question:** D-D. Loop definition
    - **Decision:** Excluded: any antenna whose radiating element is a closed or nearly closed current loop (small and magnetic loops, QFH, eggbeater, quad, delta, biquad, halo, big wheel), ferrite loopsticks and coils (CANADUINO, AS3935), and H-field probes. Allowed: dipoles (V, folded, telescopic), Moxon, Yagi (including hairpin matches), axial and normal-mode helices, patch, chip, horn, cone, whips, E-field probes.
    - **Reason:** 'NO loop antennas of any kind' needs an operational test, or the P4/P5 re-research will bring QFH back.
    - **Consequences:** The QFH options are struck.
    - **Alternatives rejected:** Shape-only or name-only lists.
  30.
    - **Question:** D-E. Radios at boot
    - **Decision:** rfkill blocks all radios at boot. Bluetooth is disabled for good (service masked, driver blacklisted). Wi-Fi is unblocked only at home, by hold-to-confirm, and is re-blocked automatically at QUIET, pass, record or field start. A self-test confirms with the tinySA that 2.4 GHz emissions stop.
    - **Reason:** Meets the delegated rule even when the user forgets, and nothing needs Bluetooth.
    - **Consequences:** OMM refresh only at home, or by offline import.
    - **Alternatives rejected:** Blocking Wi-Fi only.
  31.
    - **Question:** D-F. Band mask for surveys and NPU logs
    - **Decision:** Default mask: 3-30 kHz and 225-400 MHz, with 328.6-335.4 MHz (ILS glide path) left visible; adjustable by region. Inside the mask: live display only; storage keeps the band-mean noise floor; no boxes, snapshots or exports.
    - **Reason:** Consistent with the VLF SID drop and the Artemis stop. DE §5(2) forbids disclosing the fact of reception.
    - **Consequences:** Small loss of generic survey detail.
    - **Alternatives rejected:** No mask; deleting the band from the display.
  32.
    - **Question:** D-G. Artemis stop
    - **Decision:** Out of scope when the category is Military, Radar or Numbers, or the description has military, intelligence, EW or OTH keywords. Civil government services in the target catalogue are allow-listed. Log row: UTC plus 'out of scope' only.
    - **Reason:** Makes 'identification only' operational without stopping on weather satellites or time standards.
    - **Consequences:** The Artemis 4.2.0 category names must be checked.
    - **Alternatives rejected:** Stopping on every 'government' entry.
  33.
    - **Question:** D-H. Air travel
    - **Decision:** The DIY 4S pack never flies. The commercial bank (100 Wh or less) travels in carry-on. A UN 38.3-documented commercial 4S pack is an option (unpriced).
    - **Reason:** IATA requires a UN 38.3 battery type.
    - **Consequences:** The pack is rebuilt or bought at the destination.
    - **Alternatives rejected:** A cell-holder pack (vibration, contact resistance).
  34.
    - **Question:** D-I. Voice data
    - **Decision:** No voice IQ is ever persisted. Masking happens at snapshot time. MARK on a voice box saves the spectrogram crop only. Broadcast programme audio is exempt; amateur voice is masked too.
    - **Reason:** Strict reading of 'voice is spectrogram-only'.
    - **Consequences:** Voice-class training uses spectrograms only.
    - **Alternatives rejected:** 0.25 s snippets; masking after labelling.
  35.
    - **Question:** D-J. Geolocation features
    - **Decision:** No persistent bearing logs or spatial power maps. Interference hunting is a live readout only.
    - **Reason:** The NPU no-DF/geolocation policy.
    - **Consequences:** Self-RFI hunting still works.
    - **Alternatives rejected:** A bearing log not linked to classes.
- **Budget tables:**
  - RULE-LEFTOVER PURGE BUDGET (grep hits in final/stack/design sections, 18 Oct 2026; approximate)
  | Category | small_antenna_stack | radio_lab | lab_ui_hf | npu_training | foldable | others |
  |---|---|---|---|---|---|---|
  | Loop / H-probe | stack 18, final 31 | final 18 (some are 'excluded' text) | 0 | 0 | QFH option (bands) | display fixes[5] H-probe; antennas QFH alternative |
  | Antenna S11 | final 3 | final 2 + OQ14 (loophole) | menu[56] not gated | 0 | final 7 | antennas verify 3, narrowband fixes 1 |
  | City / Kyiv angles | final 5 | 0 | 0 | 0 | final 4 | gnss_imu 6, antennas 4, dish 3 (4-city table), digest 6 |
  | UA law / UA price base | final about 17 | UAH as reference only (allowed) | 0 | example only | final 1 | display_market final about 24, compute, wideband, storage, power, gnss_imu |
  | Private / dual-use targets | stack 13, final 18 | 0 | Inmarsat and DSC decode-then-filter | 0 | 0 | 0 |
  | TX-capable software | stack 8, final 8 | final 7 | QSSTV | Set B (QAIRT 2.47) | 0 | 0 |
  | LNB 18 V | stack 2 | SL3 wording | final 4, design 4 | 0 | final 1 | rf_frontend verify 8 |
  - DC / BIAS HAZARD LIMITS
  | Line | Value | Hazard if misrouted | Rule |
  |---|---|---|---|
  | LNB feed | 13.2 V ±0.2 V; limit 1.5-2x measured (budget 200-300 mA, unmeasured) | 3.5 W into a 1 W ANNE-50+; 8.2 V above the tinySA's 5 V DC limit; Lime ESD8472 conducts above 7 V | DC block toward every SDR and instrument; never on the sled or AUX; feed off to connect |
  | 18 V branch | deleted | 6.6 W into a 1 W load | none |
  | SAWbird+ (NOAA/GOES/iO/H1) | 120-180 mA at 5 V | trips the 180 mA V4L tee | TPS2553 at 250-300 mA |
  | V4L tee | 4.5 V, 180 mA | DC into DC-shorted antennas (hairpin, 9:1) | LNAs of 80 mA or less only; bias calls need a labd token |
  | Boni-Whip | 12.5 V LDO on 4S | n/a | DC-sense, default OFF |
  | Pack | 4S 12.0-16.8 V; fuse 7.5 A (Lime) / 5 A (no Lime) | n/a | #2813 hard cut; supervisor at 12.8 V |
  - ANTENNA S11 SWEEP EMISSION (model: free space, 2 dBi antenna, rules_lens/calc.py)
  | Source into the antenna | E at 3 m | vs FCC 15.209 above 960 MHz (54 dBuV/m) | L1 at 100 m vs GPS C/A (-128.5 dBm) |
  |---|---|---|---|
  | -20 dBm | 77 dBuV/m | +23 dB | +34 dB |
  | -10 dBm | 87 dBuV/m | +33 dB | +44 dB |
  | 0 dBm | 97 dBuV/m | +43 dB | +54 dB |
  The FCC limit is only an example of an unlicensed-emission limit; the user's country is unknown.
  - PACK TRANSPORT AND CHARGE SAFETY
  | Item | Value | Source |
  |---|---|---|
  | Energy | 4 x 18 Wh = 72 Wh (about 67 Wh at 4.10 V/cell) | P50B 5.0 Ah x 3.6 V |
  | Airline class | 100 Wh or less: carry-on; spares carry-on only, terminals insulated | IATA passenger guide |
  | Test requirement | battery type must meet UN 38.3, so the DIY welded pack fails | IATA passenger guide |
  | Charge window | 0-45 C (10k B3380 NTC) | power.json verify |
  | IP2368 hot spot | above 100 C at 5 A, so 3 A RISET and a 70 C KSD9700 | power.json |
  | Fuse | 7.5 A (Lime) / 5 A (no Lime) | register |
  - QUIET / FIELD EMITTER STATE
  | Emitter | Field / QUIET | Home | Enforcement |
  |---|---|---|---|
  | Q6A Wi-Fi (FCU760K) | rfkill blocked | unblocked by hold-to-confirm; re-blocked at pass or record | labd + systemd-rfkill + tinySA self-test |
  | Q6A Bluetooth | blocked | blocked | service masked, driver blacklisted |
  | Pinecil V2 BLE | IronOS Bluetooth Off | Off | P0 check |
  | FNB58 | Std (no radio) | Std | BOM |
  | Lime TX | 50-ohm loads + TX-reject patch | same | build + guard |
  | VNA, tinySA generator, GPSDO, noise source | off | Bench mode only, into loads or DUTs | labd interlock + procedure |
  - STORAGE / RETENTION (rules view)
  | Stream | Rate | On about 92-100 GB free UFS | Policy |
  |---|---|---|---|
  | 1x V4L 2.56 Msps cu8 | 18.4 GB/h | about 5 h | products by default; raw only when pinned; deleted after 14 days |
  | 2x V4L | 36.9 GB/h | about 2.5 h | same |
  | HF+ cf32 768 ksps | about 22 GB/h | about 4 h | same |
  | NPU dataset quota | 20 GB | n/a | no voice IQ; masked bands never stored |
  | Voice IQ | 0 B | n/a | spectrogram crops only |
  - COST DELTA FROM THE RULE FIXES
  | Change | Delta |
  |---|---|
  | Drop H-field probe line (PS-500 or generic E/H set) | -$50 to -$109 |
  | Drop optional 20 cm loop | -$20 to -$40 |
  | Drop small-stack NanoVNA (duplicates the LiteVNA) | -$60 to -$130 (unverified price) |
  | Drop SAWbird+ IR (Iridium) | -$49.95 |
  | Drop SAWbird+ iO if the egc-gate is not ready | -$49.95 |
  | Do not adopt the Pluto module | -$350 to -$400 (small-stack estimate) |
  | Fire-resistant charging bag, pack barrier, fish paper | +$10 to +$25 (estimate) |
  | Tip caps for telescopic and tape elements | +$2 to +$5 (estimate) |
  | Software gates (egc-gate, DSC, band mask, Artemis stop, bias token, TX reject, region profile) | $0 in parts, about 6-10 developer days (estimate) |
- **Checks passed:**
  - The Q6A stays in every final; no alternative board is a pick.
  - No dish in any final pick (the 300 mm lens and the horns are not dishes).
  - radio_lab final: conducted-only source rules, pad levels, Bench interlock (sled on RF3/RF4 with antenna feeds loaded), rfkill on wlan and bluetooth in QUIET, Pinecil Bluetooth Off, FNB58 Std, Lime TX terminated.
  - lab_ui_hf final: pagers, DSD/AMBE, TETRA, ACARS/VDL2/HFDL, Meshtastic/LoRa, DroneID, 802.15.4 and the SDRangel TX plugins are excluded; apt pins at -1; network ports bound to 127.0.0.1 with nftables; uploads off by default.
  - URH is rejected everywhere; kalibrate-rtl and gr-gsm are rejected; GRAVES radar meteor counting is rejected; jammers are never bought (SL8).
  - LimeSuiteNG is built with BUILD_GUI=OFF and AMARISOFT=OFF; limeTRX TX flags are banned; limeConfig is limited to the refclk options.
  - NPU class policy excludes radar, drone/FPV/RC, EW/jammer, military, emitter fingerprinting and private-content classes; DMR/P25 become unnamed occupancy; LoRa is named only on a SatNOGS-predicted pass; ADS-B/AIS oracles discard ICAO, MMSI and positions; LTE, GSM, Wi-Fi and BT are occupancy-only.
  - The small-stack exclusion list covers Starlink, OneWeb, Kuiper, Thuraya, Globalstar, military UHF SATCOM and MUOS, Yunhai-1, DMSP, Coriolis, encrypted GNSS codes, ISS non-amateur channels, Cospas-Sarsat, ARGOS/DCP, pay-TV and terrestrial military or drone links.
  - Black Kite-1 is a civil Rapidtek/TASA/ITRI LEO IoT CubeSat (verified by web); housekeeping telemetry only is acceptable.
  - No Wi-Fi hotspot/AP mode, ESP32, Pico W or other radio accessory is in any BOM (grep).
  - The lab_ui_hf location design uses GNSS, a plausibility gate and WMM at the fix, with no city list; no hard-coded time zone was found.
  - Thunderstorm, discharge-before-connect and power-line rules exist in the lab_ui_hf HF wire setup; a GDT is fitted only with an earth that meets the electrical code.
  - Power safety already present: 0-45 C NTC charging window, never charging below 0 C, 70 C KSD9700 on the IP2368, pack fuse, #2813 hard cut, Q6A USB-C covered against back-feed, 72 Wh under the 100 Wh class.
  - The QAIRT AI Stack License terms are noted and the MIT ONNX Runtime CPU path stays first-class; dataset licences are recorded (RadioML NC kept out of redistributable weights).
  - SL3 DC-hazard notes and the 'DC block before every instrument' rule exist; the LNB never goes on the sled.
- **Notes:** Base path: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/. Tools: rules_lens/jgrep.py (JSON-path grep) and rules_lens/calc.py (emission and DC model). The register already caught most violations. This pass adds the following:
  - display.json fixes[5] still builds an H-field loop probe.
  - The QFH options are not marked as loops.
  - radio_lab SL0/P0 has a 'local rules' S11 loophole, and lab_ui_hf menu[56] (the SWR page) is not gated.
  - SoapyRemote and QSSTV are TX paths.
  - DSC, SITOR-B and the RTTY/CW skimmer have no allow-list.
  - The survey heat map and the SDRangel Heat Map plugin allow emitter geolocation.
  - There is no band mask for military bands.
  - The airline note ignores UN 38.3.
  - The pack has no fire containment.
  - The radiosonde scan overlaps the 406 MHz distress band.
  - The bias-tee API is ungated.
  
  GENERIC LEGAL NOTE for STACK.md (country unknown):
  - Owning and using a receiver is licence-free in most countries, but what may be listened to differs.
  - UK WTA 2006 s48: an offence to use apparatus to obtain the contents, sender or addressee of messages not meant for you, or to disclose them.
  - Germany §5 TDDDG: only messages meant for the operator, radio amateurs, the general public or an unspecified group of people may be heard; the content of others, and even the fact they were received, may not be passed on.
  - US 18 USC 2511(2)(g): radio communications readily accessible to the general public are allowed, including amateur, marine, aeronautical and distress.
  - So by default the lab decodes only broadcast, amateur, met-satellite, navigation and time, and public MSI. ADS-B and AIS follow the region profile. No air-band or marine voice presets exist. Recordings and exports never contain non-public content. Nothing is published without checking local rules.
  
  The 25 conflicts_for_final_checks are resolved as C1-C25, plus 10 extra decisions (D-A to D-J).
  
  Web use: 2 WebSearch calls (Black Kite-1, GYA Northwood) and 7 WebFetch calls (UK s48, DE §5 at dejure.org, US 18 USC 2511, IATA PDF, SDRangel readme; gesetze-im-internet.de returned 503 and FAA PackSafe returned 403).
  
  Unverified: the Artemis category names; the Inmarsat-C packet descriptor values; the GMDSS HF MSI and DWD RTTY frequency lists (from memory); ITU RR 5.340 (from memory); GYA's operator (hobbyist sources); the prices of the fire bag, tip caps and a commercial UN 38.3 pack.
  
  stale_items_to_purge (could not be passed as a separate field: the tool rejected one long JSON string; split for readability; each line is file: field - fix):
  - small_antenna_stack.json:
    - final.revised_stack[12]: DIY loop - delete
    - final.revised_stack[22],[23],[26]: loop leads/IMU loop-plane cue - delete
    - final.reachable[2],[4],[7],[8]: loop options - delete
    - final.lost[0],[9],[11]: loop alternatives - delete
    - final.borderline_options[2]: loop comparison - delete
    - final.size_rule_used: superseded rule and loop tiers - delete
    - final.first_tests[2]: NanoVNA/loop - rewrite receive-only
    - final.first_tests[7],[8]: loop A/B - delete
    - final.first_tests[4],[5]: Kyiv angles, WSJT-X - compute at fix; jt9 only
    - final.revised_stack[29]: NanoVNA - delete
    - final.legal_notes[7]: indoor sweep - delete
    - final.reachable[8]: Orbcomm target - delete
    - final.reachable[13], revised_stack[30]: Iridium / SAWbird+ IR - delete
    - final.reachable[9]: Kyiv angles; bulletin-board packets; stdcdec - fix
    - final.reachable[12],[14]: Kyiv angles - compute at fix
    - final.reachable[15], revised_stack[28]: WSJT-X, stdcdec/Scytale-C - replace
    - final.reachable[1].legal, [11].legal: Ukrainian Criminal Code, Ukrainian territory - generic
    - final.legal_notes[1]-[6]: NKEK, martial law, Art. 163/359/114-2, DSNS - generic note
    - final.refuted_claims[6]: Ukrainian law wording - generic
    - final.excluded_by_law_or_ethics[1]: bulletin-board in scope - SafetyNET only
    - final.excluded_by_law_or_ethics[3]: Starlink Ukraine framing - keep exclusion, drop the framing
    - final.revised_stack[0], cost_size_power_delta: duty, EUR 150 - world prices
    - final.revised_stack[31]: Pluto - not adopted
    - final.borderline_options[0]: 950 UAH - world price
    - final.open_questions[0],[7]: stale - close
    - final.verdict: optional loop; helical-whip LRPT default - V-dipole
    - bands[1]: Iridium IRA/IBC 'reliable', gr-iridium, CARTOSAT-3 - delete
    - stack.add[9], remove[0], sdr_decision, revised_bom[23], risks[7]: CARTOSAT-3 - delete
  - radio_lab.json:
    - final.safety_and_legal[0] and procedures[0].steps[4]: 'unless local rules allow' - delete
    - final.open_questions[14]: close as No
    - final.open_questions[0],[1]: H-probe and AS3935 questions - close (decided)
    - final.safety_and_legal[3]: '13-18 V' - 13.2 V
    - final.safety_and_legal[6]: airline - DIY pack never flies
    - final.lab_bom[3]: H-loop option, E/H set - E-field only
    - final.lab_bom[40], totals, verdict: PS-500 / generic set - delete
    - final.lab_bom[49], procedures[20].steps[0]: Boni-Whip 9-15 V/10 V - 12.5 V
    - final.capabilities[16]: SID, WSJT-X/fldigi - civil LF SID; jt9/wsprd
    - final.software[8]: wsjtx GUI, fldigi - jt9/wsprd only
    - final.software[11]: SoapyRemote - delete
    - final.procedures[20].steps[1]: WSJT-X/fldigi - replace
  - lab_ui_hf.json:
    - final.ui_system.menu_tree[12],[13]: 145.800/145.825 - 437.550/437.825
    - menu_tree[15]: 13.4/18.2 V - 13.2 V
    - menu_tree[17] and design.menu_tree[13], integration_table[7]: decode-then-filter - egc-gate
    - menu_tree[25],[26],[31]: no allow-lists - add them
    - menu_tree[32], hf_capabilities[7]: VLF SID - civil LF only
    - menu_tree[33], hf_antenna.setup, verdict: 12.0 V - 12.5 V
    - menu_tree[34],[98], hf_receiver.setup[8]: Wi-Fi only - add Bluetooth
    - menu_tree[42]: 400-406 MHz - 405.9 MHz
    - menu_tree[45],[47]: GNSS heat map, bearing log - live only
    - menu_tree[56]: SWR page - Bench-gated, DUT only
    - menu_tree[59]: 'power meter' - tinySA channel power
    - menu_tree[65]: Artemis - add the stop
    - menu_tree[66]: MARK raw IQ on voice - spectrogram only
    - tech_stack: qsstv - delete
  - npu_training.json:
    - final.class_list[9]: voice IQ snippets - delete
    - final.class_list[7]: SSTV 145.800 - 437.550
    - final.class_list[2]: NOAA HRPT - Meteor only
    - final.datasets[0], scripts_to_write[25]: masking after labelling - mask at snapshot
    - final.architecture, software[5], pipeline[19], roadmap[3]: Set B - delete
  - foldable_antennas.json:
    - final.build_and_test_steps[1],[2],[3],[9], loss_table[1],[11], ultra_compact_tier, foldable_kit[0]: S11/VNA tuning - receive-only checks
    - final.build_and_test_steps[6], loss_table[10], other_ways_out[4]: Kyiv - compute at fix
    - final.total_cost: Ukraine shipping - world prices
    - bands[0].options[9]: collapsible QFH - excluded
    - final: '18 V or rotate' - rotate only
    - final: ISS 145.8 - 437.x
    - build step 3: SAWbird+ via micro-USB - TPS2553 injector
  - gnss_imu.json:
    - fixes[5],[6], verify.known_problems_and_fixes_to_apply[7]: Kyiv/Odesa field values - WMM at fix
    - verify.final_recommendation: UAH price base; 'pps-gpio on 7.0.11'; Route B - world prices; out-of-tree module on 6.18.2-4
  - antennas.json:
    - fixes.fixes[0].steps[3], verify.issues[2], verify.known_problems_and_fixes_to_apply[10]: Kyiv - compute
    - fixes.fixes[1].steps[2], verify.known_problems_and_fixes_to_apply[0],[7], forums.common_problems[8].known_fix: VNA tuning - receive-only checks
    - research.alternatives[1]: QFH - excluded
  - dish_replacement.json:
    - fixes.fixes[0].steps[3], verify.known_problems_and_fixes_to_apply[4]: four-city pointing table - compute at fix
    - verify.known_problems_and_fixes_to_apply[11]: Kyiv - compute at fix
    - optimistic QO-100 model and '300 mm lens SSB readable' - superseded
  - display.json:
    - fixes.fixes[5].steps[2]: DIY H-field loop probe - E-field stub
    - final: 'native 1080p60' - 127.9 MHz field mode
  - display_market.json:
    - final.ukraine_purchase, main_pick.price, above_fhd_tier.price, ranked_candidates UAH, open_questions[5],[7],[8]: Ukraine basis - world prices
    - final: 128.70 MHz - 127.9 MHz
  - narrowband_sdr.json fixes.fixes[3].steps[4]: 'NanoVNA also tunes the Yagis and helix' - delete
  - rf_frontend.json: 13.4/18.2 V switchable LNB, 100-160 mA PTC, 'GOES+ on V4L tee' - delete
  - power.json: '12 V rail suits an LNB', UAH prices - delete, world prices
  - compute.json: 'before Ukrainian import VAT', 'pin QAIRT 2.46' - delete
  - wideband_sdr.json: Lime '$310-320 landed' including Ukrainian duty - world price
  - storage.json: T7 9,299 UAH - world price
  - mechanical_thermal.json: 9 V buck into J21 - 12 V
  - digest.md lines 116, 140, 914, 975 (city/Kyiv) and 944 (Ukrainian EW) - delete
  - summaries.md #128 (city-list fallback) - errata

## completeness:verify (run `wf_6ce87eb1-883`)

- **Confidence:** medium
- **Goal coverage:**
  1.
    - **Goal:** Meteor-M LRPT 137.9 MHz
    - **Tier:** patch/chip
    - **Status:** covered
    - **How:** RTL-SDR Blog multipurpose dipole kit ($17.95; 23 cm collapsed, so it meets the piece rule) set as a V-dipole and carried in both tiers. Chain: Flamingo+ FM, then SAWbird+ NOAA on a TPS2553 injector, then V4L. N2-4 was observed 17-18 Oct 2026; N2-3 is opportunistic. The 20 cm helical whip is demoted to an experiment (model only).
  2.
    - **Goal:** Meteor-M LRPT 137.9 MHz
    - **Tier:** foldable
    - **Status:** covered
    - **How:** Same V-dipole (NEC 3.0 dBi, -3 dB polarisation loss). An optional 137.5 MHz re-mark of the 2 m tapes gives about 7.7 dBi pointed (model) for weak passes.
  3.
    - **Goal:** ISS 70 cm (SSTV 437.550, APRS 437.825, FM 437.800)
    - **Tier:** patch/chip
    - **Status:** covered
    - **How:** A-V85 or SRH-701 whip on the case, tilted broadside; model CNR 18.8-22 dB against 10-12 dB needed. SSTV via OpenWebRX+ or slowrx (decode-only), APRS via direwolf. Validate on ARISS Series 34 (22-25 Oct 2026). The HF+ cannot serve 437 MHz (it tops out at 260 MHz).
  4.
    - **Goal:** ISS 70 cm (SSTV 437.550, APRS 437.825, FM 437.800)
    - **Tier:** foldable
    - **Status:** covered
    - **How:** 70 cm half of the crossed Yagi (11 dBi NEC, ultra-compact build). Needs a new pass profile for the FM repeater (listen only).
  5.
    - **Goal:** CubeSats 435-438 MHz (1 W, 9k6)
    - **Tier:** patch/chip
    - **Status:** partial
    - **How:** Tilted whip gives -5.3 to +5.3 dB, so passes above about 30 deg only (model). The 70 cm BPF is still unnamed; see the 70 cm BPF gap.
  6.
    - **Goal:** CubeSats 435-438 MHz (1 W, 9k6)
    - **Tier:** foldable
    - **Status:** covered
    - **How:** 70 cm Yagi on RTL-A: +5.7 dB at 10 deg, +11 dB at 30 deg (±5 dB, NEC model). Default device moves from the Lime to the RTL.
  7.
    - **Goal:** GNSS and SBAS (EGNOS)
    - **Tier:** both
    - **Status:** covered
    - **How:** LC76G with SBAS on UART6, PPS on pin 7. EGNOS PRN 121/136 serve only Europe and Africa, so the goal becomes 'regional SBAS' (WAAS, MSAS, GAGAN as visible). Optional GNSS-SDR L1 on a V4L with the RTL-SDR Blog L-band patch.
  8.
    - **Goal:** Inmarsat-C EGC SafetyNET only
    - **Tier:** both
    - **Status:** partial
    - **How:** RF side is covered: RTL-SDR Blog active L-band patch (1525-1660 MHz, 20 mA on the V4L tee, $59.95) on RTL-B. Decoding stays blocked until the labd egc-gate passes the mixed-recording test (header-level discard, rule line 37). Find the NCS by scanning 1537-1545 MHz.
  9.
    - **Goal:** QO-100 NB (beacons, CW, PSK, SSB)
    - **Tier:** patch/chip
    - **Status:** partial
    - **How:** Bare Bullseye LNB: CW beacon about 6-9 dB in 50 Hz (model, consistent with OK1DX); FT8 experimental. With a 10-11 cm cone, PSK is marginal (Eb/N0 5.4-8.8 dB, model). Only usable where 25.9E is visible.
  10.
    - **Goal:** QO-100 NB (beacons, CW, PSK, SSB)
    - **Tier:** foldable
    - **Status:** partial
    - **How:** 6-gore horn (21/23 dBi): PSK reliable (model), beacon-level SSB marginal (0 to +5 dB). Needs a tripod and a peak-on-beacon pointing mode. Region-bound.
  11.
    - **Goal:** QO-100 DATV and typical SSB
    - **Tier:** both
    - **Status:** not_feasible
    - **How:** Physics: needs about 26 dBi (SSB) and 31-32 dBi (DATV). Only a dish gives that, and dishes are banned by rule.
  12.
    - **Goal:** Meteor-M HRPT 1.7 GHz
    - **Tier:** patch/chip
    - **Status:** partial
    - **How:** 4-turn helix on a 20 cm disc with SAWbird+ GOES on V4L at 2.4-2.56 Msps: +1.5 to +3 dB above 25-30 deg (model). A small rigid antenna, so it needs the user's confirmation. Scan the own-spur lines first: 1699.2 MHz (28.8 MHz x59) and 1704.0 MHz (12 MHz x142).
  13.
    - **Goal:** Meteor-M HRPT 1.7 GHz
    - **Tier:** foldable
    - **Status:** covered
    - **How:** Petal helicone: +8.9 to +9.4 dB average (NEC model). No dish-free hand-tracked decode is documented, so the first passes go above 40 deg from a tripod.
  14.
    - **Goal:** Metop-B AHRPT (and AWS)
    - **Tier:** patch/chip
    - **Status:** not_feasible
    - **How:** Link budget: a 4-turn helix is well below the 16-19 dBic needed.
  15.
    - **Goal:** Metop-B AHRPT (and AWS)
    - **Tier:** foldable
    - **Status:** partial
    - **How:** Experimental. Helicone gives -1.5 to 0 dB (model). Two gates: V4L at 2.88 Msps (SatDump #727 shows a V4 decode at 2.88 Msps), then a pass test. Airspy Mini only if the rate test fails. AWS needs 3.6 Msps or more, so it needs the Lime or an Airspy.
  16.
    - **Goal:** FengYun-3 / FY-2H / Elektro-L LRIT
    - **Tier:** foldable
    - **Status:** partial
    - **How:** FY-3 is X-band or ended, so it is not feasible. FY-2H: carrier check only (1687.5 vs 1690.5 MHz to be settled on air). Elektro LRIT is opportunistic, about 3 dB below 65 cm dish reports (model). All region-bound.
  17.
    - **Goal:** S-band (Black Kite-1/2, PHASMA, HamTV)
    - **Tier:** patch/chip
    - **Status:** not_feasible
    - **How:** No S-band-capable SDR in core; the V4L stops at 1.766 GHz.
  18.
    - **Goal:** S-band (Black Kite-1/2, PHASMA, HamTV)
    - **Tier:** foldable
    - **Status:** partial
    - **How:** Conditional on keeping the Lime. 7-turn S helix in the cone, cavity, and an LNA not yet named. Telemetry is opportunistic. HamTV (2395 MHz) is carrier-only and needs its own filter, because the 2170-2300 MHz cavity blocks it. The Pluto is not adopted.
  19.
    - **Goal:** ADS-B 1090 MHz
    - **Tier:** both
    - **Status:** covered
    - **How:** Dipole-kit arms at 6.5-7 cm on a time-shared V4L, or the spare V4L on LAB USB at camp. readsb/tar1090 with pre-cached tiles and uploads off. Tracks flagged military (dbFlags&1) are not shown or logged.
  20.
    - **Goal:** AIS 162 MHz
    - **Tier:** both
    - **Status:** covered
    - **How:** HF+ in VHF mode through the new latching selector, or the spare V4L. 44 cm dipole arms, AIS-catcher. Ship type 35 is suppressed.
  21.
    - **Goal:** Radiosondes 400-406 MHz
    - **Tier:** both
    - **Status:** covered
    - **How:** 17.7 cm dipole arms on a V4L. radiosonde_auto_rx scans 400.0-405.9 MHz (clear of 406.0-406.1 Cospas-Sarsat), with uploads off and chasemapper offline.
  22.
    - **Goal:** Broadcast FM-RDS / DAB+
    - **Tier:** both
    - **Status:** covered
    - **How:** Dipole kit plus V4L (redsea, welle-cli). HD Radio and NOAA SAME only in the US region profile.
  23.
    - **Goal:** NAVTEX and HF MSI
    - **Tier:** both
    - **Status:** covered
    - **How:** HF+ with the remote wire and 9:1 balun (rated from 0.125 MHz). SITOR-B runs only on published MSI/NAVTEX channels; DSC goes through the format-specifier gate.
  24.
    - **Goal:** LF time signals (DCF77, MSF, WWVB, JJY, TDF)
    - **Tier:** both
    - **Status:** partial
    - **How:** Active E-field whip only, because the 9:1 balun loses about 7-12 dB at 40-77.5 kHz. Boni-Whip available 20 Nov 2026 (WiMo); fallback is the PA0RDT clone at EUR 25.90. SDRangel Radio Clock does not list JJY 60 kHz, so JJY 60 is amplitude only.
  25.
    - **Goal:** VLF time signals / VLF SID (3-30 kHz)
    - **Tier:** both
    - **Status:** excluded_by_rule
    - **How:** 16-25 kHz carriers are naval transmitters (rule line 36), and 3-30 kHz is a masked band (rule line 41). SID uses civil LF carriers only, amplitude only.
  26.
    - **Goal:** HF amateur decode-only and HF WEFAX
    - **Tier:** both
    - **Status:** partial
    - **How:** jt9/wsprd only. CW/RTTY/PSK skimmers run inside amateur allocations only. WEFAX is limited to civil met services (DWD, JMA and similar); Northwood is excluded, and the USCG-run NWS fax stations are excluded by default pending the user. Without loops, local noise often sets the floor (physics).
  27.
    - **Goal:** Spectrum survey
    - **Tier:** both
    - **Status:** partial
    - **How:** 0.5 kHz-1.766 GHz on the HF+ and V4L, storing occupancy only, with 3-30 kHz and 225-400 MHz masked to 'no data'. 1.766-7.3 GHz needs a new coarse tinySA Ultra+ survey profile (sensitivity above 800 MHz unverified). Ku via the LNB IF.
  28.
    - **Goal:** Calibration
    - **Tier:** both
    - **Status:** partial
    - **How:** tinySA channel power ±2 dB up to 800 MHz is absolute. L-band dBFS-to-dBm and MDS are relative (about ±3 dB). Noise-source NF is relative. PPS sample-count and GNSS-SDR give ppm. GPSDO is extended only.
  29.
    - **Goal:** Radio-astronomy basics (H1, Sun noise)
    - **Tier:** foldable
    - **Status:** partial
    - **How:** Helicone or helix with SAWbird+ H1 and Virgo; Sun rise about 0.7-1.2 dB (model). The no-Lime fallback for V4L PLL behaviour at 1420 MHz is the spare V4L. The flat-pack horn is optional.
  30.
    - **Goal:** NPU spectrum detector/classifier that the user can teach
    - **Tier:** both
    - **Status:** partial
    - **How:** SpecDet INT8 on QAIRT 2.42 plus a CPU embedder, design only; Phase 0 HTP gate is unmeasured. CPU mode handles 4-6 tiles/s, so it needs a 4.3 tiles/s single-SDR profile. 3 of 5 profiles are Lime-only. The home-base PC is unconfirmed. Policy gates (voice, band mask, Artemis) must ship before the labeller.
  31.
    - **Goal:** One touch menu for every lab function
    - **Tier:** both
    - **Status:** partial
    - **How:** Lab Shell design with 105 leaves; about 25 are stale, Lime-bound or T7-bound. Fixes: no-Lime/no-T7 backends and a CI menu test. Physics: capacitive touch fails through gloves, so every capture-critical action must work from keys and encoders.
  32.
    - **Goal:** Automatic self-location, standalone with no phone
    - **Tier:** both
    - **Status:** partial
    - **How:** GNSS, plausibility gate, WMM2025 at the fix, last-good-fix and manual fallbacks. The first-boot bootstrap rule (RTC unset) is still missing, and city and Kyiv constants must be purged.
  33.
    - **Goal:** Radio-lab instruments and bench
    - **Tier:** both
    - **Status:** partial
    - **How:** Core instruments are verified and costed ($1,306-1,688). Missing: the parts layer (selectors, bias board, LNB regulator, cable schedule, 70 cm BPF, supports, weather, pack build, recovery media); see missing_parts_bom.
  34.
    - **Goal:** Display bright and high quality
    - **Tier:** both
    - **Status:** partial
    - **How:** Wisecoco 7in FHD 2000-nit, only after written confirmation of bonding and USB-HID touch; fallback 4D 1000-nit, which still has no world price. Field pixel clock about 127.9 MHz. Above FHD only as the Midas project.
- **Requirement compliance:**
  1.
    - **Requirement:** Hard rule: receive-only on air; VNA/generators/noise sources conducted only (line 6)
    - **Status:** partly_met
    - **Where:** radio_lab safety_and_legal[0] ('unless local rules explicitly allow'); lab_ui_hf menu_tree[56] SWR page not Bench-gated; foldable build steps 2-5 and 10, foldable_kit[0], loss_table[1]/[11]; small_antenna_stack first_tests[2] and revised_stack[29]; antennas verify; narrowband fixes[3]
    - **Fix:** Purge every antenna S11 step and the loophole, gate the VNA leaf behind Bench mode, and use the receive-only acceptance checks (see the antenna-sweep gap).
  2.
    - **Requirement:** Hard rule: no private-communications content, no chains aimed at military communications; generic coverage fine (line 7)
    - **Status:** partly_met
    - **Where:** lab_ui_hf menu_tree[17] and small_antenna_stack reachable[9] (Inmarsat decoded, then filtered); small_antenna_stack reachable[8]/[13], bands[1] (Iridium IRA/IBC, Orbcomm), CARTOSAT-3 rows; VLF SID in menu_tree[32]
    - **Fix:** egc-gate; no named Iridium/Orbcomm target (generic occupancy only); delete CARTOSAT-3; civil LF SID only.
  3.
    - **Requirement:** Hard rule: compute stays Radxa Dragon Q6A (line 8)
    - **Status:** met
    - **Where:** All finals
    - **Fix:** Drop the moot board comparisons (compute, small_antenna_stack) from STACK.md. Buy the 12 GB tier (C2).
  4.
    - **Requirement:** Hard rule: no dishes of any size (line 9)
    - **Status:** met
    - **Where:** All final picks are dish-free. dish_replacement still has the refuted claim that a 300 mm lens makes typical SSB readable
    - **Fix:** Purge the optimistic QO-100 model. Physics limit stays: DATV, typical SSB and X-band FY-3/Metop are not reachable.
  5.
    - **Requirement:** Hard rule: antennas patch/chip or folding (pieces about 20-23 cm, max about 35 cm) (line 10)
    - **Status:** partly_met
    - **Where:** small_antenna_stack size_rule_used (superseded); the standard Yagi sits at the 35 cm limit; small rigid antennas (A-V85/SRH-701 whip, 4-turn helix on 20 cm disc, 10-11 cm cone, bare LNB) are neither patch nor folding
    - **Fix:** Two-tier rule (C15). Use the RTL-SDR Blog L-band patch instead of the 2-turn helix, the dipole kit in both tiers, and the ultra-compact Yagi as default. Ask the user to confirm the small rigid antennas.
  6.
    - **Requirement:** Hard rule: NO loop antennas of any kind; LRPT uses the folding V-dipole (line 11)
    - **Status:** violated
    - **Where:** small_antenna_stack final (162 'loop' hits: optional 20 cm loop, loop A/B tests, loop-plane IMU cue, helical whip as LRPT default); radio_lab lab_bom[3]/[40] H-loop probes; display.json fixes[5] 'DIY H-field probe: a 15 mm loop'; QFH in antennas research.alternatives[1] and foldable bands[0].options[9]
    - **Fix:** Strike all of them. Add an operational loop definition (QFH, eggbeater, quad, delta, biquad, halo, big wheel, loopsticks, H-probes) and a CI grep. V-dipole as the LRPT default in both tiers.
  7.
    - **Requirement:** Hard rule: world prices; Ukrainian prices only as reference (line 12)
    - **Status:** violated
    - **Where:** 'Ukrain'/UAH bases in display_market (84/23 hits), small_antenna_stack (101/15), gnss_imu (25/62), narrowband, rf_frontend, compute, storage, power, wideband, mechanical, dish, antennas, foldable, digest.md
    - **Fix:** Re-price every line in P5 (manufacturer, AliExpress, EU/US shops). Replace the UA legal notes with the generic note.
  8.
    - **Requirement:** Hard rule: automatic self-location, no city tables (line 13)
    - **Status:** partly_met
    - **Where:** Kyiv constants in gnss_imu (11 hits), small_antenna_stack (15), antennas (6), foldable (5), dish_replacement 4-city pointing table, digest.md (10); summaries #128 city list
    - **Fix:** Compute az/el and WMM at the fix. Add the bootstrap rule (3D fix, 8 or more satellites, stable within 50 m for 5 min; GNSS time flagged until NTP). Purge every city entry.
  9.
    - **Requirement:** Wish: bright, high-quality display, ideally above FHD (line 16)
    - **Status:** partly_met
    - **Where:** display_market (Wisecoco unconfirmed: 0 reviews, I2C in-cell touch); 4D priced only in UAH; 128.70 MHz in display_market (5) and display (1)
    - **Fix:** Send the written seller questions. Get a world quote for the 4D. Use 127.9 MHz everywhere. Above FHD only as the Midas project (physics: 7in FHD is already at the visual-acuity limit).
  10.
    - **Requirement:** Wish: full radio lab with instruments, RF switch, filter/LNA banks, extra receive capabilities, software, bench tools (line 17)
    - **Status:** partly_met
    - **Where:** radio_lab final; internal RF selectors, injector/bias board, cable schedule, 70 cm BPF, LNB regulator part and supports are missing; 'LF/VLF time signals' (VLF is excluded by lines 36/41)
    - **Fix:** Add the missing-parts BOM and recompute the totals (C24). VLF time signals stay out of scope by rule.
  11.
    - **Requirement:** Wish: HF receiver kept, small foldable NON-loop antenna (line 18)
    - **Status:** partly_met
    - **Where:** HF+ with wire and 9:1 plus the Boni-Whip; HF+ input selector missing from the BOM; Boni-Whip at 10.0/12.0 V in radio_lab item 49, P20 and lab_ui_hf
    - **Fix:** Latching DC-capable selector, Boni-Whip at 12.5 V via LDO, ANT PWR jack. Physics: the floor near the handheld is often set by local noise.
  12.
    - **Requirement:** Wish: NPU training on the spectrum, user teaching, on-device few-shot, home-base training, INT8 on QAIRT 2.42 (line 19)
    - **Status:** partly_met
    - **Where:** npu_training: Set B (QAIRT 2.47) in architecture/software[5]/pipeline[19]/roadmap[3]; class_list[3]/[8]/[9]/[13]; CPU fallback 4-6 tiles/s vs 7.3 tiles/s; home PC unconfirmed
    - **Fix:** Delete Set B. Add the CPU-mode profile and the Phase-1 observable class set. Ask about the home-base PC (the minimum needs no GPU).
  13.
    - **Requirement:** Wish: one ideal touch menu for every lab function (line 20)
    - **Status:** partly_met
    - **Where:** lab_ui_hf menu_tree: Lime-bound [1,9,10,11,14,17,43,45,89], T7-bound [18,69,77,84,100], stale [8,12,13,15,32,42,47,56,59,64,65,98]
    - **Fix:** No-Lime/no-T7 backend per leaf, a CI menu render test, the new leaves, and keys/encoders for every capture-critical action (glove physics).
  14.
    - **Requirement:** Process: pipeline P1-P7 (lines 23-26)
    - **Status:** partly_met
    - **Where:** P1b output final/report_research.json exists (576,735 B, 04:51); errata blocks are missing ('errata' has 0 hits in summaries.md and minute-log.md); STACK.md and build/ not yet written
    - **Fix:** Close conflict 25, write the errata blocks, then STACK.md.
  15.
    - **Requirement:** Process: per-minute summaries only in minute-log.md (line 27)
    - **Status:** met
    - **Where:** minute-log.md
    - **Fix:** Add the inline errata notes listed in register #141.
  16.
    - **Requirement:** Process: delegated objective decisions, report at phase ends (line 28)
    - **Status:** met
    - **Where:** user_requirements lines 30-46
    - **Fix:** At the phase end, ask the user about: the HF-loop removal, small rigid antennas, region, home PC, USCG WEFAX, and whether the Lime is a refundable pre-order.
  17.
    - **Requirement:** Delegated: no H-field probes or AS3935; E-field probes only (line 31)
    - **Status:** violated
    - **Where:** radio_lab lab_bom[3] and [40], totals and verdict (PS-500 or generic E/H set); display.json fixes[5] H-loop probe; radio_lab sweeps AS3935 storm rule
    - **Fix:** Delete them (saves $50-109). Use an E-field semi-rigid stub, and a 30/30 thunder rule instead of the AS3935.
  18.
    - **Requirement:** Delegated: QUIET/field mode rfkill wlan AND bluetooth; Pinecil BT off; FNB58 Std (line 32)
    - **Status:** violated
    - **Where:** lab_ui_hf menu_tree[34] and [98], hf_receiver.setup[8] (Wi-Fi only)
    - **Fix:** Block both radios at every boot; mask the BT service; Wi-Fi unblocked only at home; tinySA self-test at 2.4 GHz.
  19.
    - **Requirement:** Delegated: URH rejected; Artemis identification only with a military/government stop (line 33)
    - **Status:** partly_met
    - **Where:** URH rejected everywhere; lab_ui_hf menu_tree[65] has no stop
    - **Fix:** Operational stop rule with a civil allow-list; log UTC plus 'out of scope' only; extend it to ADS-B dbFlags&1 and AIS type 35.
  20.
    - **Requirement:** Delegated: NPU class policy gate; voice spectrogram-only; no decoder payloads stored (line 34)
    - **Status:** partly_met
    - **Where:** npu_training class_list[9] (voice IQ), class_list[3] (NOAA), class_list[8] (145.800)
    - **Fix:** See the line-43 fix. Correct the class metadata.
  21.
    - **Requirement:** Delegated: lab core follows the value verifier (Bodnar in extended, no duplicate OSL, no AD8318 in core) (line 35)
    - **Status:** met
    - **Where:** radio_lab final; lab_ui_hf menu_tree[59] still has 'Power meter (model TBD)'
    - **Fix:** Rename the leaf to tinySA channel power.
  22.
    - **Requirement:** Delegated: VLF SID dropped; civil LF carriers only, amplitude only (line 36)
    - **Status:** violated
    - **Where:** lab_ui_hf menu_tree[32] and hf_capabilities[7]; radio_lab capabilities[16]
    - **Fix:** 'SID (civil LF carriers)' with an allow-list of DCF77/MSF/WWVB/JJY/TDF, amplitude only; labd refuses SID tuning at 3-30 kHz.
  23.
    - **Requirement:** Delegated: Inmarsat-C EGC SafetyNET only, header-level discard, no LES channels, FleetNET discarded (line 37)
    - **Status:** violated
    - **Where:** lab_ui_hf menu_tree[17] (SDRangel decodes everything, UDP to labd); small_antenna_stack reachable[9] (stdcdec/Scytale-C plus bulletin-board packets); radio_lab says 'excluded'
    - **Fix:** labd egc-gate with a release test; SDRangel demodinmarsat and SatDump inmarsat_support out of the build. Physics: demodulation and FEC of all bits cannot be avoided.
  24.
    - **Requirement:** Delegated: power meter = tinySA; AD8318 optional extended (line 38)
    - **Status:** met
    - **Where:** radio_lab; lab_ui_hf menu_tree[59] stale
    - **Fix:** Rename the leaf.
  25.
    - **Requirement:** Delegated: location fallback without a city table (line 39)
    - **Status:** partly_met
    - **Where:** summaries #128; gnss_imu fixes[5]/[6]; dish_replacement pointing table
    - **Fix:** Last good fix with its age, manual lat/lon or Maidenhead entry, and the bootstrap rule. Purge the city tables.
  26.
    - **Requirement:** P2: no emitter geolocation; surveys store band occupancy only (line 40)
    - **Status:** violated
    - **Where:** lab_ui_hf menu_tree[47] (bearing log), [45] ('GNSS-tagged heat map'), sweeps SDRangel Heat Map; radio_lab capabilities[2] 'GNSS-tagged surveys'
    - **Fix:** Interference hunt becomes a live readout that is never saved; one rounded site tag per session; the packaging audit fails if the Heat Map plugin is present.
  27.
    - **Requirement:** P2: survey band mask 3-30 kHz and 225-400 MHz, masked to 'no data' before storage (line 41)
    - **Status:** violated
    - **Where:** Not implemented in labrx, labclassify or the survey design
    - **Fix:** Mask at write time in labrx for surveys, occupancy DB, NPU boxes, MARK/SNAP and exports; unit test; no carve-outs inside 225-400 MHz.
  28.
    - **Requirement:** P2: DSC dropped at format/category before MMSIs; SITOR-B/RTTY/CW/PSK only on amateur bands and MSI/NAVTEX channels; WEFAX civil met only, Northwood excluded (line 42)
    - **Status:** violated
    - **Where:** lab_ui_hf menu_tree[25], [26] (hidden after decode), [27], [31]; SDRangel DSC plugin
    - **Fix:** Own DSC format-specifier gate or a patched plugin, per-mode frequency allow-lists, and a civil WEFAX schedule. The USCG stations are put to the user.
  29.
    - **Requirement:** P2: no voice IQ at all; MARK/SNAP on voice saves spectrogram only (line 43)
    - **Status:** violated
    - **Where:** npu_training class_list[9], datasets[0] ('14 days or masked'), scripts_to_write[25] (mask after labelling); lab_ui_hf menu_tree[66]
    - **Fix:** labrx masks voice bins at snapshot write and refuses raw pins that overlap an unmasked voice box.
  30.
    - **Requirement:** P2: no TX-capable software (no WSJT-X GUI, fldigi, QSSTV, SoapyRemote); decode-only tools; librtlsdr bias token; EEPROM bias off (line 44)
    - **Status:** violated
    - **Where:** radio_lab software[8], [11], capabilities[16], procedures[20]; lab_ui_hf tech_stack and menu_tree[12] (QSSTV); small_antenna_stack revised_stack[28]
    - **Fix:** jt9/wsprd only. SSTV via OpenWebRX+ or slowrx built from source (not in noble: packages.ubuntu.com says 'No such package'). Patch librtlsdr to require /run/labd/bias/<serial>. Packaging audit.
  31.
    - **Requirement:** P2: no antenna sweeps on air; SWR page only in Bench mode with a load or DUT (line 45)
    - **Status:** violated
    - **Where:** lab_ui_hf menu_tree[56]; foldable and small-stack steps; radio_lab SL0
    - **Fix:** Bench-gate the leaf and purge the steps (see the antenna-sweep gap).
  32.
    - **Requirement:** P2: battery safety (home-built pack never flown; containment; NTC 0-45 C; supervised charging; storage at about 50 % SoC) (line 46)
    - **Status:** violated
    - **Where:** radio_lab safety_and_legal[6] (carry the 72 Wh pack in the cabin); no pack bay barrier or vent in mechanical_thermal; NTC window present in power.json
    - **Fix:** Rewrite SL6. Design the pack bay (barrier, vent path, fish paper, spot-welds), add charging rules and the storage-SoC rule.
- **Confirmed gaps:**
  1.
    - **Gap:** Inmarsat-C: no backend meets the header-level discard rule
    - **Kind:** rule_violation
    - **Why it matters:** Rule line 37. The SDRangel demodinmarsat filters act only on the decoded Type and Message columns, and its Messages table, UDP output and CSV logging handle every packet. lab_ui_hf menu_tree[17] sends the SDRangel output to labd and filters afterwards. small_antenna_stack decodes with stdcdec/Scytale-C, keeps bulletin-board packets and filters afterwards. The leaf also defaults to the undecided Lime and the SAWbird+ iO.
    - **Resolution:** 1. Build without SDRangel demodinmarsat and SatDump inmarsat_support; the packaging audit fails if either is present.
  2. Write a labd egc-gate:
  - BPSK demodulation, deinterleaving and Viterbi decoding are unavoidable (physics).
  - In RAM, read each packet descriptor and drop every non-EGC packet before any payload byte is copied.
  - Read the EGC service code, drop FleetNET and anything that is not SafetyNET, and only then assemble the SafetyNET text.
  3. Use bulletin-board packets only for frame lock; never display or store them. Never tune LES or ship channels.
  4. Take the descriptor and service-code values from the decoder source (unverified here).
  5. Release gate: on a mixed NCS recording, no byte of a non-SafetyNET packet reaches text, display or disk.
  6. Default chain: RTL-B plus the RTL-SDR Blog L-band patch.
  7. Ship the profile disabled; drop it at P7 if the gate has not passed.
    - **Cost:** $0 in parts; 2-5 developer days (estimate)
    - **Sources:**
      - https://github.com/f4exb/sdrangel/blob/master/plugins/channelrx/demodinmarsat/readme.md
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md
  2.
    - **Gap:** Antenna S11 sweeps and an ungated VNA leaf are still in the final files
    - **Kind:** rule_violation
    - **Why it matters:** Rules at lines 6 and 45. lab_ui_hf menu_tree[56] ('Quick SWR/S11 page') is outside Bench mode; only the generator leaf [58] is gated. radio_lab SL0 still carries the 'unless local rules explicitly allow' loophole. Radiating steps remain in foldable build steps 2-5 and 10 ('recheck S11'), foldable_kit[0] ('VNA-tune'), loss_table[1]/[11], small_antenna_stack first_tests[2] and revised_stack[29] (NanoVNA 'sweep briefly indoors'), antennas verify, and narrowband fixes[3]. Model: a -10 dBm sweep into a 2 dBi antenna gives about 87 dBuV/m at 3 m.
    - **Resolution:** 1. Rename the leaf 'Conducted S11/S21 (DUT/load only)' and make it reachable only in Bench mode, after the 1.5 s 'antenna disconnected' hold (same interlock as [58]).
  2. Delete the loophole and every antenna S11 step. Close radio_lab open question 14 and register #0 as 'No'.
  3. Receive-only acceptance instead:
  - beacon C/N within 1 dB of the baseline;
  - antenna vs terminated noise rise;
  - Sun and cold sky;
  - GNSS C/N0 and NCS SNR.
  4. Check baluns and matching sections conducted into SMD loads, and cables by TDR with the antenna removed.
  5. Drop the small-stack NanoVNA; the LiteVNA 64 covers it.
    - **Cost:** $0; saves $60-130
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rules_lens/calc.py
  3.
    - **Gap:** HF and maritime text decoders have no allow-lists (rule line 42)
    - **Kind:** rule_violation
    - **Why it matters:** menu_tree[25] (SITOR-B) and [31] (CW/RTTY/PSK skimmer) decode on any frequency, so they can print utility traffic. [26] DSC hides routine calls only after the MMSIs are decoded. [27] WEFAX has no operator filter. The SDRangel DSC plugin decodes every call.
    - **Resolution:** 1. Per-mode allow-lists in labd:
  - RTTY, PSK and CW text only inside the region's amateur allocations, plus named civil met RTTY (list to verify);
  - SITOR-B only on the published GMDSS MSI/NAVTEX channels (list to verify against ITU/IMO).
  2. DSC: own gate, or a patched SDRangel DSC plugin, that drops individual (120/123) and group (114) format specifiers before any address symbols are emitted. Keep distress (112), all-ships (116) and area (102) calls only with distress, urgency or safety categories.
  3. WEFAX: civil met schedule only (for example DWD, JMA). Northwood is excluded. USCG-run NMF/NMG/NMC are excluded by default under a strict reading (the USCG is an armed service) and put to the user.
  4. Unit tests on mixed recordings.
    - **Cost:** $0; 2-3 developer days (estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
      - https://www.legislation.gov.uk/ukpga/2006/36/section/48
  4.
    - **Gap:** Survey band mask (rule line 41) is not implemented
    - **Kind:** rule_violation
    - **Why it matters:** radio_lab capabilities[2] ('GNSS-tagged spectrum surveys'), lab_ui_hf menu_tree[45] and the NPU unknown_energy boxes would store activity at 225-400 MHz (MILSATCOM 240-320 MHz, MUOS 360-380 MHz) and at VLF.
    - **Resolution:** labrx masks bins in 3-30 kHz and 225-400 MHz to 'no data' before any write: surveys, occupancy DB, NPU boxes, MARK/SNAP, exports. The region profile may extend the mask but never shrink it. The live waterfall is unaffected. Unit test with synthetic carriers at 250, 300 and 380 MHz. No ILS carve-out, because the rule says 'at least 225-400 MHz'.
    - **Cost:** $0; about 1 developer day
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md
  5.
    - **Gap:** Voice IQ is still kept (rule line 43)
    - **Kind:** rule_violation
    - **Why it matters:** npu_training class_list[9] keeps 0.25 s IQ snippets; datasets[0] says 'raw IQ retained 14 days or masked'; scripts_to_write[25] masks after labelling; menu_tree[66] MARK saves raw IQ even on voice boxes. All of these can be demodulated later.
    - **Resolution:** labrx removes voice bins (detector boxes plus the band plan) when a snapshot is written to UFS. MARK/SNAP on a voice box saves only the magnitude spectrogram. Any raw-IQ pin that overlaps an unmasked voice box is refused. Only broadcast programme audio (FM, AM, DAB, DRM) is exempt; amateur voice is masked too.
    - **Cost:** $0; about 1 developer day
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  6.
    - **Gap:** No operational Artemis stop, and no handling of military flags in ADS-B/AIS
    - **Kind:** rule_violation
    - **Why it matters:** Rule line 33. menu_tree[65] has no stop at all. A naive 'government' match would also stop on weather satellites, time standards and NAVTEX. ADS-B and AIS displays decode military emitters incidentally. readsb defines military = dbFlags & 1 (verified in its README-json); AIS ship type 35 means military operations.
    - **Resolution:** labclassify treats a match as out of scope when:
  - the Artemis category is military, radar or numbers (Artemis 4.2.0 category names to verify); or
  - the description names military, navy, air force, intelligence, EW, jammer or OTH.
  Civil government services in the target catalogue are allow-listed. An out-of-scope box shows only 'out of scope', and MARK, record, label, decode and export are disabled on it. The log row is UTC plus 'out of scope', with no frequency, location or bearing.
  ADS-B: tracks with dbFlags&1 are neither displayed nor logged, and the tar1090 military/interesting filters are disabled.
  AIS: ship type 35 is neither displayed nor logged.
    - **Cost:** $0; 0.5-1 developer day
    - **Sources:**
      - https://github.com/wiedehopf/readsb/blob/dev/README-json.md
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  7.
    - **Gap:** QUIET and field modes leave Bluetooth on
    - **Kind:** rule_violation
    - **Why it matters:** Rule line 32. lab_ui_hf menu_tree[34], [98] and hf_receiver.setup[8] block Wi-Fi only. Nothing tests whether the out-of-tree FCU760K driver honours rfkill.
    - **Resolution:** 1. Every QUIET, field, pass and record profile runs rfkill block wlan and bluetooth.
  2. Disable Bluetooth for good: mask the service, blacklist the driver, persist the rfkill state.
  3. Block all radios at every boot. Wi-Fi is unblocked only at home, by hold-to-confirm, and is re-blocked automatically.
  4. Self-test: the tinySA confirms that 2.4 GHz emissions stop.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  8.
    - **Gap:** Battery transport and containment (rule line 46)
    - **Kind:** legal_or_safety
    - **Why it matters:** radio_lab SL6 tells the user to carry the 72 Wh DIY pack in cabin baggage. IATA requires every battery type to meet UN 38.3, and a home-welded 4S1P has no test summary. No pack bay barrier or vent is designed, and the IP2368 MOSFET exceeded 100 C at 5 A (power.json).
    - **Resolution:** 1. Rewrite SL6: the DIY pack never flies. A commercial bank of 100 Wh or less travels in carry-on with terminals insulated; the field pack is built or bought at the destination.
  2. Pack bay: separated by the 2 mm aluminium mid-plate or 1 mm FR-4/mica; fish paper and glass-fibre tape; spot-welds only; a vent path to the outside, away from the grip and face.
  3. Keep the 0-45 C NTC window and the 70 C KSD9700.
  4. Charge only when supervised, on a non-flammable surface or in a fire bag.
  5. Store at 3.6-3.8 V per cell (about 50 % SoC); retire swollen or dented cells.
    - **Cost:** +$20-45 (estimate)
    - **Sources:**
      - https://www.iata.org/contentassets/6fea26dd84d24b26a7a1fd5788561d6e/passenger-lithium-battery.pdf
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/power.json
  9.
    - **Gap:** Metop AHRPT receiver requirement is overstated; gate the V4L at 2.88 Msps before buying anything
    - **Kind:** unverified_claim
    - **Why it matters:** Register #91/#125, foldable loss_table[4] and NPU class 2 say Metop needs an SDR faster than 2.56 Msps. SatDump issue #727 (fetched): an RTL-SDR Blog V4 reached sync at 2.88 Msps with DC block and AGC, the attached image is avhrr_3_composite, and the maintainer called the RTL 'on the edge'. Caveats: that was June 2024, on a V4 (not the V4L), before Metop-B's intermittent modulator loss (03/2025), and with autotrack, so probably a dish.
    - **Resolution:** Gate (a): 15 min of rtl_test at 2.88 Msps (5.76 MB/s) on the blue USB 3.1 root port with zero drops.
  Gate (b): one Metop-B pass above 45 deg on helicone + SAWbird+ GOES + V4L at 2.88 Msps; look for the hump at 1701.3 MHz and for lock.
  Buy an Airspy Mini (about GBP 110, undated) only if (a) fails, and the array LNAs (4 x $44.95) only if (b) shows humps. Metop stays experimental (-1.5 to 0 dB, model). AWS stays Lime/Airspy-only.
    - **Cost:** $0; 1-2 evenings
    - **Sources:**
      - https://github.com/SatDump/SatDump/issues/727
  10.
    - **Gap:** About 9 menu leaves default to the undecided Lime
    - **Kind:** stale_or_contradictory
    - **Why it matters:** lab_ui_hf menu_tree:
  - [1] 'Lime at 30 MHz';
  - [9] HRPT on Lime RX1 ('V4L marginal');
  - [10] Metop/FY and [11] Elektro on the Lime;
  - [14] CubeSats on Lime RX2;
  - [17] Inmarsat on the Lime;
  - [89] GNSS-SDR on the Lime;
  - [43]/[45] 'Lime wide'.
  foldable_kit[2] feeds the 'LimeSDR port', and loss_table[2] uses 'both Lime RX'. Without the Lime these leaves have no working default.
    - **Resolution:** Every leaf declares a no-Lime and a no-T7 backend:
  - HRPT: V4L at 2.4-2.56 Msps.
  - Metop: V4L at 2.88 Msps after the gate.
  - LRIT: V4L.
  - CubeSats: RTL-A.
  - Inmarsat: RTL-B.
  - GNSS-SDR: V4L with the L-band patch.
  The Lime is used only from 300 MHz up, and only when present. A capability probe hides Lime-only leaves. CI renders the menu with the Lime and T7 absent and checks every frequency against the cached SatNOGS DB.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  11.
    - **Gap:** ISS entries: stale 2 m frequencies, an impossible HF+ route, no FM-repeater leaf
    - **Kind:** stale_or_contradictory
    - **Why it matters:** Stale or impossible entries:
  - menu_tree[12] (145.800) and [13] (145.825) both offer 'HF+ in VHF mode', but the HF+ stops at 260 MHz.
  - hf_capabilities[11] lists '145.8 MHz ISS'.
  - foldable_kit[1] uses 145.8 MHz as the only reason for the 2 m Yagi half.
  - NPU class 7 is still on 145.800 MHz.
  - There is no leaf for the FM repeater downlink (437.800 MHz).
    - **Resolution:** Use 437.550, 437.825 and 437.800 MHz everywhere (ARISS). Delete the HF+ alternates. Add an 'ISS FM repeater 437.800 (listen)' pass profile. Make the 2 m Yagi half optional, justified only by VHF amateur satellites (AO-7, AO-73, JO-97, AO-91 as active) and VHF APRS; the ultra-compact 70 cm half is the default.
    - **Cost:** $0; saves about 150-250 g (estimate) when the 2 m tapes stay home
    - **Sources:**
      - https://www.ariss.org/current-status-of-iss-stations.html
  12.
    - **Gap:** QO-100 ratings contradict each other between tiers
    - **Kind:** stale_or_contradictory
    - **Why it matters:** small_antenna_stack reachable[15] rates FT8 'reliable with beacon lock', but its evidence used a GPSDO-locked LNB, while the Bullseye is a TCXO LNB drifting ±10-30 kHz. reachable[14] rates the PSK beacon 'reliable' with the cone, while foldable loss_table[7] calls a comparable cup 'marginal'. My model: an 18.4-18.8 dBi cone gives C/N0 of 31.4-34.8 dB-Hz, so Eb/N0 of 5.4-8.8 dB at 400 bit/s.
    - **Resolution:** One table, used in STACK.md and on the menu leaf:
  - Bare LNB: CW beacon reliable (model); FT8 experimental.
  - 10-11 cm cone or cup: PSK marginal.
  - 21 dBi horn: PSK reliable (model); beacon-level SSB marginal.
  - 23 dBi horn: beacon SSB 2-5 dB.
  - Typical SSB and DATV: not feasible.
  Fix qo100_beacon_track.py (register #108) before any FT8 claim. Add peak-on-beacon pointing: the horn beam is about 12-15 deg, so 3-5 deg of IMU error costs 0.5-2.1 dB (model).
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/verifier_calc/v.py
  13.
    - **Gap:** S-band ratings are too strong
    - **Kind:** stale_or_contradictory
    - **Why it matters:** small_antenna_stack reachable[18] rates Black Kite 'reliable'. Per the goals critic (not re-checked here), SatNOGS DB shows no recent decoded data for it. The chosen cavity (2170-2300 MHz) blocks HamTV at 2395 MHz. The S-band LNA is still unnamed, and CARTOSAT-3 is used as a justification.
    - **Resolution:** S-band only if the Lime is kept. The Pluto is not adopted: it is TX-capable and duplicates the Lime. Rate Black Kite and PHASMA opportunistic (frame parsing unverified) and HamTV carrier-only with its own 2.4 GHz filter. Name and price an S-band LNA at the Lime gate, or drop the chain. Delete CARTOSAT-3.
    - **Cost:** $0 now; S-band LNA unpriced; cavity EUR 65.45 only with the Lime
    - **Sources:**
      - https://db.satnogs.org/satellite/98527/
  14.
    - **Gap:** No purchasable 70 cm band-pass filter is named
    - **Kind:** missing_part
    - **Why it matters:** 70 cm overload on the 8-bit V4L is the main technical risk (register #98, open question 18). My search found no 430-440 MHz SMA SAW part.
    - **Resolution:** Candidates for P5:
  - Nooelec Ham Filter Bank Barebones, $66.95 in radio_lab. It has a 2 m (144-148 MHz), a 70 cm (420-450 MHz) and three other filters plus a passthrough (third-party listing); selection method, insertion loss and DC pass are unverified. Preferred, because it also filters the optional 2 m path.
  - Uputronics 435 filtered preamp: EUR 47.64 at Kubii (last items); new stock is limited to 5 V bias.
  - antennas-amplifiers.com 430-450 MHz receive BPF: 119.00 (currency not shown), N connectors, about 0.15 dB.
  Measure insertion loss, rejection at 88-108 and 700-800 MHz, and DC pass on the LiteVNA (conducted). Without DC pass, place it after the LNA V2.
    - **Cost:** $50-120
    - **Sources:**
      - https://antennas-amplifiers.com/70cm-430-450mhz-ultimate-receiving-bandpass-filter/
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  15.
    - **Gap:** No RF input routing for the two internal RTLs
    - **Kind:** missing_part
    - **Why it matters:** Each RTL has one SMA input, but each needs several inputs:
  - RTL-A: the 137 MHz dipole, the 70 cm whip or Yagi, and the optional 2 m half.
  - RTL-B: the L-band patch or helix, and the LNB IF.
  The only switch in the files is the extended sled (built around the Lime). menu_tree[64] names HMC241 boards, which were rejected. The one-touch menu cannot route chains, and a terminated input is needed for the spur scans at 1699.2/1704.0 MHz and the display A/B.
    - **Resolution:** One HMC7992 SP4T board per RTL, placed behind the injectors, with every port DC-free (C0G blocks):
  - RTL-A: 137 MHz / 2 m / 70 cm / 50 ohm.
  - RTL-B: L-band / LNB IF / BENCH or sled / 50 ohm.
  Pull-downs select the 50 ohm port at power-up. Verify 3.3 V logic and conducted isolation of 30 dB or more. Correct the menu_tree[64] hardware text. Fallback: the 'connect X' prompt.
    - **Cost:** About $30 (2 x CA$20.49, third-party listing in radio_lab, unverified)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  16.
    - **Gap:** No injector or bias-tee part is named, and the obvious SMD tee is under-rated
    - **Kind:** missing_part
    - **Why it matters:** Register #96 asks for an injector rated down to about 100 MHz; radio_lab names only '2 generic 10 MHz-6 GHz tees' (they lose 3-7 dB at 100-200 MHz) and an unnamed internal LNB tee. TCBT-14+ is 200 mA DC (completeness critic citing the datasheet), below the 250-300 mA TPS2553 limit.
    - **Resolution:** Build one internal 5-channel bias board:
  - Per-band inductors with self-resonance above the band: 137 MHz about 0.47-1 uH; 2 m/70 cm about 150-220 nH; L-band about 33-56 nH; plus the LNB IF channel.
  - Rated 0.5 A or more on the LNA channels and 1 A or more on the LNB channel; C0G DC blocks.
  - One TPS2553 per LNA channel, set to 250-300 mA, with FAULT to the expander.
  Verify S21/S11 at 100-1800 MHz on the LiteVNA (conducted) and record the results in parts.yaml. Use TCBT-14+ only on lines of 80 mA or less. ZFBT-4R2GW+ ($111.57) is for the bench only.
    - **Cost:** $25-45 (estimate)
    - **Sources:**
      - https://www.minicircuits.com/pdfs/TCBT-14+.pdf
  17.
    - **Gap:** No cable and adapter schedule
    - **Kind:** missing_part
    - **Why it matters:** Cables are left out or guessed in every file (foldable: 'not included $40-60'). Concrete gaps:
  - The A-V85 is SMA-female.
  - The CH334F downstream ports are solder pads only.
  - Internal V4Ls need USB extensions.
  - The LNB needs a 75 ohm F lead.
  - The Boni-Whip needs BNC-SMA.
  - EDL recovery needs an A-A cable.
  - The HF+ USB connector type is not recorded.
    - **Resolution:** Adopt the completeness critic's schedule:
  - 6 internal RG316 jumpers;
  - F-F bulkhead plus a 75 ohm lead;
  - IPX-SMA pigtail;
  - 2 V4L USB extensions with ferrites;
  - 4 CH334F pigtails;
  - a touch lead with VBUS cut;
  - a shielded 10-15 cm HDMI with Mix 31/61 ferrites;
  - 4 RG316 feed jumpers of 1-2 m;
  - a 1 m thin 75 ohm F-F;
  - SMA M-M, F-SMA and barrel adapters;
  - a USB3 A-A cable.
  Use branded or VNA-screened RG316 and bag RP-SMA parts separately. Record the HF+ connector on arrival.
    - **Cost:** $90-170 (estimate)
    - **Sources:**
      - https://www.adafruit.com/product/5997
  18.
    - **Gap:** Survey is blind above 1.766 GHz without the Lime
    - **Kind:** goal_not_covered
    - **Why it matters:** radio_lab capabilities[2] and menu_tree[45] cover 1.766-3.8 GHz only with the Lime. Without it, LTE 1800-2600, Wi-Fi and S-band are never surveyed, although the core tinySA Ultra+ receives to 7.3 GHz in ULTRA mode. capabilities[1] also claims 'visible to 12 GHz' with no source.
    - **Resolution:** Add a 'Survey (tinySA, coarse, receive-only)' profile through the labd tinySA serial driver for 0.8-7.3 GHz, storing occupancy only with the band mask applied. Label sensitivity above 800 MHz unverified. Delete the 12 GHz claim.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  19.
    - **Gap:** The NPU CPU fallback cannot keep up with one V4L
    - **Kind:** goal_not_covered
    - **Why it matters:** CPU mode runs 4-6 tiles/s, while one V4L needs RTL-F 6.5 + RTL-C 0.8 = 7.3 tiles/s (my recompute: 7.75 at K=2). The MVP 'ships CPU-first' if Phase 0 fails.
    - **Resolution:** Add a CPU-mode profile: one SDR, RTL-F at K=4 (3.5 tiles/s) plus RTL-C 0.8, i.e. 4.3 tiles/s, with change-gated tiles. The status bar shows 'AI: partial'. Full live labels for 2 SDRs come only after the HTP gate.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/verifier_calc/v.py
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  20.
    - **Gap:** Several NPU classes cannot be observed or trained with core hardware
    - **Kind:** goal_not_covered
    - **Why it matters:** Problem classes:
  - class 2 is 'Meteor/NOAA HRPT', but NOAA ended in 2025;
  - class 7 SSTV is on 145.800 MHz, and live data come only from ARISS events, so 300 boxes cannot come from live captures;
  - class 12 dvbs2: a 2.56 MHz window cannot see a 27.5 MHz transponder;
  - classes 16 wifi and 17 bt_ble need the Lime.
  menu_tree[23] shows NPU classes on HF, but no HF profile exists.
    - **Resolution:** Tag the Lime-only classes conditional, and limit Phase 1 to classes the V4L and HF+ can observe. hrpt means Meteor only. Drop dvbs2 from Phase 1. Build SSTV examples from file-only synthetic Robot 36 (no TX) plus Series 34 recordings. Hide HF labels until the HF-F profile exists.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  21.
    - **Gap:** The home-base PC for T3 training and the QAIRT 2.42 conversion is unconfirmed
    - **Kind:** other
    - **Why it matters:** On-device few-shot learning needs a frozen detector and embedder trained off-device. The QAIRT 2.42 converter is x86-64 only (register #45, open question 9).
    - **Resolution:** Ask the user.
  - Minimum, which needs no GPU: any x86-64 machine with 16 GB RAM or more, running an ubuntu:22.04 / Python 3.10 container with the archived QAIRT 2.42.0.251225 zip (container use untested).
  - GPU (12 GB, RTX 3060 class) only for T3.
  - Colab/Kaggle only for synthetic or satellite-only data, after checking the AI Stack License.
  - Private captures never leave the home base.
    - **Cost:** $0 if a PC is owned; GPU about EUR 298 (France low) to about $500 (US), July 2026 listings, per the completeness critic
    - **Sources:**
      - https://www.guru3d.com/story/geforce-rtx-3060-12gb-prices-reportedly-jump-after-relaunch/
  22.
    - **Gap:** L-band absolute levels are presented without a 'relative' label
    - **Kind:** unverified_claim
    - **Why it matters:** The tinySA sine output is specified ±2 dB only up to 800 MHz, and the noise-source ENR is good to ±2-3 dB. So dBFS-to-dBm and MDS at 1.42, 1.54 and 1.70 GHz are relative, but the files never say so.
    - **Resolution:** Label every L-band absolute number '±3 dB, relative'. Calibrate by Y-factor with the ENR table taken at the regulated AUX voltage, and cross-check with GNSS C/N0 and Sun noise.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  23.
    - **Gap:** Pointing aid gaps
    - **Kind:** other
    - **Why it matters:** The Point leaf's audio pitch encodes only the IMU error, not signal strength, although 3-5 deg of error costs up to 2 dB on the 23 dBi horn. The puck needs 15-20 cm from steel, but the 2 m Yagi elements are steel tape.
    - **Resolution:** Add a 'peak on signal' mode: beacon C/N0 or S-meter as pitch, for GEO and LEO. On the tape Yagi, take elevation from gravity and azimuth from a sun-sight, with the magnetometer off. IMU on USB-CDC (C6).
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/verifier_calc/v.py
  24.
    - **Gap:** Orbital elements have no offline refresh path without the T7
    - **Kind:** other
    - **Why it matters:** menu_tree[18] imports elements only from the T7 or online. In the field Wi-Fi is off and there is no phone.
    - **Resolution:** Refresh over home Wi-Fi or from a USB stick or microSD through the external-storage abstraction. Keep the 3-day (ISS) and 7-day warnings. Disable the auto-pointing aid, but never reception, when the predicted along-track error exceeds a quarter of the beam.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  25.
    - **Gap:** The loop exclusion list is incomplete, and display.json still builds an H-loop probe
    - **Kind:** rule_violation
    - **Why it matters:** Leftovers:
  - display.json fixes[5]: 'Make a DIY H-field probe: a 15 mm loop' (not in the register).
  - QFH antennas (two bifilar loops) in antennas research.alternatives[1] and foldable bands[0].options[9].
  P4/P5 re-research could bring them back.
    - **Resolution:** Excluded: small and magnetic loops, QFH, eggbeater, quad, delta, biquad, halo, big wheel, ferrite loopsticks (CANADUINO), the AS3935 coil and H-field probes.
  Allowed: V and telescopic dipoles, Moxon, Yagi (including hairpin matches), axial and normal-mode helices, patch, chip, horn, cone, whips and E-field probes. Folded dipoles are not used anywhere, which avoids the edge case.
  Replace the display H-probe with an E-field semi-rigid stub, and add a CI grep.
    - **Cost:** $0; saves $50-149 (H-probe line and loop)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/display.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/antennas.json
  26.
    - **Gap:** Several lab functions have no menu leaf
    - **Kind:** missing_part
    - **Why it matters:** No leaf exists for:
  - scope/LA capture (Hantek 6022BL, PulseView);
  - FNB58 logging;
  - the sled step attenuator;
  - the Inmarsat NCS scan (1537-1545 MHz);
  - a GEO carrier check (NCS, FY-2H at 1687.5 vs 1690.5 MHz, Elektro);
  - Ku carrier humps;
  - the tinySA survey;
  - the ISS FM repeater.
  'Reference/GPSDO (model TBD)' should name the Bodnar Mini (extended).
    - **Resolution:** Add these leaves under Instruments and Satellites, behind leases and the Bench interlock. Every GEO leaf shows a 'visible from here' flag computed from the fix.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  27.
    - **Gap:** No antenna supports are budgeted
    - **Kind:** missing_part
    - **Why it matters:** The procedures need supports that no BOM buys:
  - the V-dipole at 1-1.1 m;
  - HRPT from a tripod at least 50 cm up;
  - the 23 dBi horn on a tripod;
  - the Boni-Whip at least 2 m up on a pole that collapses to 35 cm or less.
  The dipole kit includes only a flexible mini tripod, and foldable excludes a pan-tilt tripod.
    - **Resolution:** Travel tripod that folds to 35 cm or less, reaches 1.2 m or more, takes 1/4-20 and has a mini pan-tilt head. Shock-corded tent-pole mast (7 x 35 cm, about 2.4 m) with 3 guy cords and a stake. Throw cord and weight for the wire. Adds 0.35-0.9 kg (estimate).
    - **Cost:** $55-150 (estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
  28.
    - **Gap:** No ingress target or weather parts
    - **Kind:** missing_part
    - **Why it matters:** The case has a fan and a blower intake, and the encoders and feed LNAs are not sealed. 'desiccant' has 0 hits across final/*.json. Physics: 11-32 W internal plus 13.5-17 W of solar load need forced air, so IP67 is not reachable.
    - **Resolution:** Target IPX4/IP54:
  - baffled intakes with stainless mesh and hydrophobic foam;
  - ePTFE vents;
  - silicone caps on SMA, F and USB ports;
  - a clear rain sleeve;
  - IP65 boxes with glands for the feed LNAs;
  - self-amalgamating tape, dielectric grease and silica gel.
  In rain: LOCK plus encoder-only operation, and no intake facing up.
    - **Cost:** $45-110 (estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/mechanical_thermal.json
  29.
    - **Gap:** The pack build process is not budgeted, and the P50B has no world price
    - **Kind:** missing_part
    - **Why it matters:** The welded 4S1P has no welding, nickel, fish paper or balance lead in any BOM. The ISDT 608PD needs a JST-XH 5-pin balance lead. register #59 gives UAH prices only.
    - **Resolution:** 5 x P50B (NKON EUR 6.75 incl. VAT each per the completeness critic, page dated 31 Jul 2026; NKON blocked my fetch, so unverified). 0.15 x 8 mm pure nickel, fish paper, Kapton, 4S wrap, a JST-XH 5-pin balance lead to an internal service connector, and an XT30 lead. A battery shop welds the pack. Test cell IR and capacity before welding. No spring holders and no soldering to cells.
    - **Cost:** $70-105 (estimate)
    - **Sources:**
      - https://www.nkon.nl/rechargeable/molicel-inr21700-p50b-5000mah-50a.html
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/power.json
  30.
    - **Gap:** Power key, travel disconnect and wall charger are missing
    - **Kind:** missing_part
    - **Why it matters:** The #2813 needs a pushbutton, but the six HMI keys have no POWER key. There is no travel disconnect. The IP2368 needs a PD source of 60 W or more, but only a power bank is listed.
    - **Resolution:** A recessed sealed 12-16 mm momentary button for the #2813. An XT30 loop arming plug for travel. The IP2368 USB-C mounted at the wall with an O-ring and cap. A 65-100 W PD wall charger with a 1 m 5 A C-C cable.
    - **Cost:** $45-75 (estimate)
    - **Sources:**
      - https://www.pololu.com/product/2813
  31.
    - **Gap:** Protection values are inconsistent or missing
    - **Kind:** stale_or_contradictory
    - **Why it matters:** Pack fuse is given as 7.5 A vs 5 A. The J21 fuse has no value. There is no TVS on the pack node and no Boni-Whip polyfuse value. The LAB 5 V '2 A fuse' side is ambiguous, and it decides whether the LNA bias fits.
    - **Resolution:** ATM mini-blade fuses in holders:
  - pack lead: 5 A without the Lime / 7.5 A with it, 18 AWG;
  - J21 branch: 3.15 A;
  - LAB 5 V: 2 A on the INPUT side, so the D36V28F5's 3.2 A is the 5 V limit.
  PTCs: AUX 0.75 A hold; Boni-Whip 0.2 A (resize after measuring). TVS: SMBJ18A on the pack node, SMBJ14A after the 12 V regulator, SMBJ15A at the LNB F port. LNA channels use TPS2553 limits, not PTCs.
    - **Cost:** $13-25 (estimate)
    - **Sources:**
      - https://www.pololu.com/product/3782
  32.
    - **Gap:** Recovery and secondary-storage media are not budgeted
    - **Kind:** missing_part
    - **Why it matters:** Without the T7, nothing holds offline bundles, exports or the rescue image. The EDL A-A cable and the UFS reader are scattered across files.
    - **Resolution:** Recovery kit: Radxa RA019-E1U1 UFS/eMMC reader (EUR 13.00 at TinyTronics per the critic, unverified), a USB3 A-A cable, a 32-64 GB A2 rescue microSD and a USB3 card reader. Secondary storage: a V30/A2 128-256 GB microSD and a 64 GB stick. Archive BIOS 260120, edl-ng, the image and QAIRT 2.42 with SHA-256 at the home base.
    - **Cost:** $50-90 (estimate)
    - **Sources:**
      - https://www.tinytronics.nl/nl/data-opslag/modules/radxa-ufs-emmc-naar-usb-3.0-lezer-module
  33.
    - **Gap:** HMI, audio, fasteners, thermal consumables and AR film are unpriced
    - **Kind:** missing_part
    - **Why it matters:** lab_ui_hf open question 11 lists the encoder, keys and knob as unpriced. EC11 encoders are not sealed. There is no headphone path. No fastener schedule exists for the ASA shell, and the AR film needed for the 6.2:1 sun contrast is unpriced.
    - **Resolution:** HMI and audio: 2 O-ring-sealed push encoders, 6 IP67 tact keys, knobs, a VEML7700 breakout, an RGB LED, a piezo, a 3.5 mm panel extension and wired headphones; no speaker until a terminated-floor A/B passes.
  Mechanical: M2.5/M3 brass heat-set inserts, A2 screws, nylon or brass screws near the IMU, a steel 1/4-20 insert or captured nut (no tapped 2 mm plate), 2 strap lugs with hand and sling straps, 1-2 mm pads of 3-6 W/mK, SoC paste, and a 7in AR film.
    - **Cost:** $85-170 (estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  34.
    - **Gap:** Bags, spares and build tools are not listed
    - **Kind:** missing_part
    - **Why it matters:** The petals and gores have sharp 0.3-0.5 mm aluminium edges. The LNB neck and waveguide must be measured with calipers. Bench tools list only drivers, cutters, a stripper and tweezers.
    - **Resolution:** Padded antenna roll, element tube and a 10-12 L sling. A second dipole kit as the source of spare elements ($17.95, verified today). Calipers, snips with a deburr tool, an M5 tap and die, and a heat gun. A crimper only if jumpers are not bought ready-made. An ASA print service if no enclosed printer is available.
    - **Cost:** $130-235 (+$30-80 print service) (estimate)
    - **Sources:**
      - https://www.rtl-sdr.com/store/
  35.
    - **Gap:** IMU puck, external GNSS and service access are unpriced
    - **Kind:** missing_part
    - **Why it matters:** The puck's 'sealed boom connector', its cable and its shield are unpriced. An external GNSS antenna needs an IPX-SMA bulkhead. The UART and GbE access in the case have no hatch.
    - **Resolution:** GX12 4-pin pair, 2 m shielded 4-core cable and a shield can. IPX-SMA bulkhead and a 3 m active GNSS antenna, only if the lid patch fails the C/N0 on/off test. A service hatch with UART and RJ45 access. Confirm the FCU760K antenna provision from the schematic.
    - **Cost:** $30-55 (estimate)
    - **Sources:**
      - https://www.waveshare.com/LC76G-GNSS-Module.htm
  36.
    - **Gap:** The radiosonde scan covers the Cospas-Sarsat band
    - **Kind:** legal_or_safety
    - **Why it matters:** menu_tree[42] scans 400-406 MHz, which includes 406.0-406.1 MHz, an excluded distress-beacon band.
    - **Resolution:** Set the auto_rx scan to 400.0-405.9 MHz.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  37.
    - **Gap:** Outdoor safety rules are incomplete
    - **Kind:** legal_or_safety
    - **Why it matters:** The radio_lab storm rule depends on the excluded AS3935. Nothing covers telescopic tips, tape edges, throw-weights or a mast in wind; the power-line rule appears only in the HF wire setup.
    - **Resolution:** 30/30 thunder rule, and antennas down at the first thunder. Discharge before connecting. Keep at least 2x the antenna or wire height from overhead lines. Tip caps on telescopic and tape elements. Eye protection when throwing a line. Guy or lower masts above about 20 km/h of wind (estimate).
    - **Cost:** +$2-5
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  38.
    - **Gap:** Legal defaults: region profile, export privacy and the legal note
    - **Kind:** legal_or_safety
    - **Why it matters:** Only the NPU has a region profile (default 'standard'). SigMF exports carry the exact GNSS position, which reveals the home. The small-stack legal notes rest on Ukrainian law.
    - **Resolution:** Make the region profile lab-wide in labd. Derive it from the fix through offline admin-0 polygons (jurisdiction only, never a location fallback), and keep it 'restricted' until a fix exists; the user can edit it. Round the location in every export to 0.1 deg or a 4-character locator. Uploads stay off. Replace the UA legal notes with the generic note in legal_and_safety_notes.
    - **Cost:** $0; about 1 developer day
    - **Sources:**
      - https://dejure.org/gesetze/TDDDG/5.html
      - https://www.law.cornell.edu/uscode/text/18/2511
  39.
    - **Gap:** No first-boot location bootstrap rule
    - **Kind:** missing_part
    - **Why it matters:** Register #7 asks for it, but no design has it. The gate needs the time within 120 s of the RTC, which fails on a first boot with the RTC unset.
    - **Resolution:** Accept the first fix only when it is 3D, has 8 or more satellites and stays within 50 m for 5 min. With the RTC unset, accept GNSS time flagged 'unverified' until NTP at home or a second session confirms it. Fallbacks: last good fix with its age, or manual lat/lon or Maidenhead entry. WMM2025 at the fix. No city list.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  40.
    - **Gap:** C1 LimeSDR Micro: keep or drop
    - **Kind:** stale_or_contradictory
    - **Why it matters:** It drives the RAM ring, T7, USB map, CPU7, 3 of 5 NPU profiles, riser and cooling, fuse value, S-band and several lab procedures.
    - **Resolution:** DECISION: gated optional. Keep the pre-order (new orders ship 15 Dec 2026) only if it is refundable, and decide on delivery or on 31 Jan 2027. Keep it only if (a) it passes the riser acceptance (8 GT/s x1, zero AER errors after 60 min, 50 warm and 20 cold boots) and (b) the user wants S-band, AWS or the 56 Msps wideband NPU. Buy no Lime-only parts before the gate. If kept: TX ports loaded with 50 ohm, LimeSuiteNG patched to fail TX stream setup, no SoapyRemote. REASON: every core goal runs on 2-3 V4Ls plus the HF+. Its unique targets are opportunistic, its driver is validated only on x86, and it is the only TX-capable part.
    - **Cost:** $0 until the gate; $249 + $18 shipping if kept
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  41.
    - **Gap:** C2 Q6A RAM tier
    - **Kind:** stale_or_contradictory
    - **Why it matters:** RAM is soldered and cannot be upgraded.
    - **Resolution:** DECISION: buy the 12 GB board now. Allnet lists $189.99; the rules critic reports a TinyTronics 12 GB at about $166 incl. VAT (unverified); buy from the cheapest official listing on the order date. Ring 1.5 GiB without the Lime, 4 GiB with the Lime and training on. Burn-in within the return window. REASON: even without the Lime, the trainer phase is 6.8-8.1 GiB (OS 1.2-1.8, servers 0.7-1.4, ring 1.5, inferd 1.4, trainer 2.0; estimates), at or over an 8 GB board's visible RAM.
    - **Cost:** About $40 more than the 6 GB board (Allnet)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  42.
    - **Gap:** C3 Pack 3S vs 4S
    - **Kind:** stale_or_contradictory
    - **Why it matters:** The pack sets every rail topology and runtime.
    - **Resolution:** DECISION: 4S1P Molicel P50B, 72 Wh (about 61-65 Wh usable down to the 13.6 V cutoff), with a regulated 12 V rail into J21. The pack is never flown (rule line 46). REASON: the 13.2 V LNB, the 12.5 V Boni-Whip LDO, AUX 12 V and the noise-source ENR all need headroom above 12.6 V.
    - **Cost:** +$45 and +75 g vs 3S
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/power.json
  43.
    - **Gap:** C4 12 V regulator
    - **Kind:** stale_or_contradictory
    - **Why it matters:** The register prefers a buck-boost, while the verified part is the D36V50F12.
    - **Resolution:** DECISION: prototype on the Pololu D36V50F12 ($39.95; buy 2 because stock is rationed), with its EN hardware cut at 13.4 V or above. Switch to a forced-PWM buck-boost rated 5 A or more only if the terminated-floor spur A/B or the sealed-case 3.5 A test at 13.6-16.4 V fails. REASON: the pack runs only between 13.4 and 16.8 V, above the 13.3 V dropout, so a buck-boost adds nothing in that window. The 12 V load (Q6A 2 A, display 0.75 A, AUX 0.75 A) is inside the published 2.3-6.5 A.
    - **Cost:** $79.90 for 2
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  44.
    - **Gap:** C5 USB port map and LAB 5 V budget
    - **Kind:** stale_or_contradictory
    - **Why it matters:** Four maps exist, and the HF+ and LNA power paths differ between them.
    - **Resolution:** DECISION:
  - Blue USB 3.1: RTL-A, or the T7 only if the Lime and T7 are kept (RTL-A then moves to CH334F H2).
  - FE1.1s: P1 RTL-B; P2 touch; P3 CH334F; P4 FCU760K Wi-Fi/BT.
  - CH334F (soldered pigtails): H1 HMI RP2040; H2 IMU puck over USB-CDC; H3 LAB USB-A through a TPS2553 at 1 A, default off; H4 HF+.
  - HF+ and LNA bias come from LAB 5 V (D36V28F5, 3.2 A, fuse on the input side).
  LAB 5 V budget (model): 0.86 A during passes (27%, LAB port off) and 1.94 A on the bench (61%). Tests: 30 min with zero drops for HF+ and V4L together on the FE1.1s, and 15 min at 2.88 Msps on the blue port. REASON: the FE1.1s carries 8-13 MB/s of its 35-40 MB/s practical; VCC_5V_PERI carries 0.88 A of about 3.4 A.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/verifier_calc/v.py
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  45.
    - **Gap:** C6 40-pin header, buses, expanders and IMU
    - **Kind:** stale_or_contradictory
    - **Why it matters:** Assignments differ between files. One MCP23017 has 16 lines (GPA7/GPB7 output-only, per radio_lab, unverified), but the core needs about 24 (17 out, 7 in). radio_lab binds the expanders through pinctrl-mcp23s08, which is not built on 6.18.2-4.
    - **Resolution:** DECISION:
  - PPS: pin 7 (GPIO96, out-of-tree pps-gpio).
  - UART6: 16/18 for the LC76G.
  - I2C0: 13/15 for the INA228 only, from user space.
  - I2C2: 27/28 for MCP23017 #1 (0x20) and a NEW #3 (0x22) inside the handheld; sled #2 (0x21) behind the TCA9517; no BNO085 on I2C.
  - Expanders are driven by labd through smbus2; pull-downs make every switch and bias line off and every selector select its 50 ohm port at power-up.
  - IMU: USB-CDC puck on CH334F H2. UART7 is optional, only after its overlay is proven.
  - Fan: pin 33 pwm-gpio (spi14 off) after a test, else GPIO56.
  REASON: UART6 disables i2c6; the BNO08x clock-stretches; the mcp23s08 driver is absent from the held kernel.
    - **Cost:** $5.95 (Adafruit #5346)
    - **Sources:**
      - https://www.adafruit.com/product/5346
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  46.
    - **Gap:** C7 Hardware ownership and the IQ tap during passes
    - **Kind:** stale_or_contradictory
    - **Why it matters:** Three daemon designs exist. 'SatDump CLI per pass' opens the SDR itself, so the NPU and MARK see nothing during passes (menu_tree[8], [9], [66]).
    - **Resolution:** DECISION: labd is the sole owner of lines, leases, interlocks and policy enforcement; rflab becomes a labd module. labrx is the only process that opens an SDR for pass, survey, waterfall and NPU profiles, owns the single RAM ring and recorder, and applies the voice and band masks at write. SatDump decodes from the labrx recording (record-then-decode is already the retention default) or from a FIFO; SatDump 2.0-alpha live pipe input is untested. Monitor daemons that need direct device access (readsb, AIS-catcher, auto_rx) may open an SDR only under an exclusive labd lease, with no NPU tap for that SDR. udev ACLs give SDR nodes only to labrx or the current leaseholder. labclassify runs inferd and fusiond. REASON: one lock scheme, and an IQ tap during passes.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  47.
    - **Gap:** C8 LNB supply (the boost options named in the files fail on 4S)
    - **Kind:** stale_or_contradictory
    - **Why it matters:** radio_lab lab_bom[34] names a 'TPS65233-class or trimmed boost', and the small stack an MT3608/XL6009 boost. On 12.0-16.8 V a plain boost cannot step down, so it passes roughly the pack voltage minus a diode drop (up to about 16 V), which selects horizontal. The TPS65233 has an 18.2 V mode. lab_ui_hf menu_tree[15] still offers 13.4/18.2 V.
    - **Resolution:** DECISION: 13.2 V ±0.2 V measured at the F connector, vertical only, no 18 V.
  - Preferred: a low-noise LDO rated 36 V / 1 A (TPS7A4701 class) fed from the pack after the master switch, with EN driven by the expander as the true off (pass element off; acceptance 0 V into 1 kOhm). Dissipation is at most 1.0 W at 0.27 A and 1.44 W at 0.4 A at 16.8 V (model). Dropout of a few hundred mV keeps 13.2 V down to about 13.4-13.5 V of pack voltage, i.e. near the hardware cut.
  - Alternative: a Pololu S18V20AHV-class SEPIC plus a second #2813 for disconnect.
  - One current limit at 1.5-2x the measured Bullseye draw; LC filter, PTC and SMBJ15A; feed off before connect or disconnect; DC block toward the SDR.
  REASON: no switching spurs near the 739.5 MHz IF, cheaper, and the pack never drops below the dropout while the device runs.
    - **Cost:** $10-20 for the LDO route (estimate); $40-50 for the SEPIC route (S18V20AHV price not checked)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/verifier_calc/v.py
      - https://www.pololu.com/product/2813
  48.
    - **Gap:** C9 LNA bias rule and source (the LT3045-from-12 V line cannot be built)
    - **Kind:** stale_or_contradictory
    - **Why it matters:** Register #61 says 'LNAs: LT3045-class LDO'. From 12 V at 0.35 A it would dissipate 2.45 W, and the LT3045 is rated only 500 mA. Register #62 puts the injectors on LAB 5 V, but the LAB budget never counted them. menu_tree[8] puts the 170 mA SAWbird+ NOAA on the 180 mA V4L tee.
    - **Resolution:** DECISION: every SAWbird+ runs from a TPS2553 at 250-300 mA, on a filtered branch of LAB 5 V (ferrite plus LC pi-filter). An optional LT3045 post-regulator at 4.5 V (0.18 W at 0.36 A) is added only if the terminated-floor A/B shows ripple. The V4L tee powers only loads of 80 mA or less: LNA V2, the L-band patch (20 mA) and the non-plus SAWbird. Delete the 100-160 mA PTC, 'GOES+ on the tee' and 'LT3045 from 12 V'. Cased SAWbird+ ($49.95) at the feeds; Barebones ($44.95) only inside the shielded bay. labd checks 'injector on, tee off' per profile. REASON: there is enough LAB 5 V margin, and no separate buck is needed.
    - **Cost:** $5-12 (estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/verifier_calc/v.py
  49.
    - **Gap:** C10 FM filter and the 2 m path
    - **Kind:** stale_or_contradictory
    - **Why it matters:** The patch tier has more than one VHF entry, and the SAWbird+ NOAA (2.6 MHz wide) blocks 145.8 MHz.
    - **Resolution:** DECISION: one Nooelec Flamingo+ FM ($24.95, 250 mA DC pass published) permanently at the 137 MHz feed, ahead of the SAWbird+ NOAA. The optional 2 m path uses the Ham Filter Bank's 144-148 MHz filter after the LNA V2; a second Flamingo+ is bought only if the filter bank is not. The 70 cm path uses its own BPF. Measure DC pass on arrival. REASON: one published-DC-rated part, and the 2 m half is optional.
    - **Cost:** $0 extra (second Flamingo+ $24.95 only as a fallback)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  50.
    - **Gap:** C11 librtlsdr build and the bias token
    - **Kind:** stale_or_contradictory
    - **Why it matters:** Three recipes exist (one destructive), and any process can call rtlsdr_set_bias_tee.
    - **Resolution:** DECISION: rebuild noble's 2.0.1 with commits 0204c9c and 65f0658 plus the typo fix, keep the .so.2 soname, and hold it. Patch the bias-tee calls to fail unless /run/labd/bias/<serial> exists (rule line 44). Set the EEPROM bias default off and never use 'rtl_eeprom -b 1'. Blacklist dvb_usb_rtl28xxu. Delete the 2.0.3 .so.0 and purge-and-fork recipes. First bench task: the build must print 'RTL-SDR Blog V4 Lite Detected'.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  51.
    - **Gap:** C12 Display field-mode pixel clock
    - **Kind:** stale_or_contradictory
    - **Why it matters:** At 128.70 MHz the 12th harmonic is 1544.4 MHz (inside Inmarsat-C) and the 11th is 1415.7 MHz (in the H1 passband).
    - **Resolution:** DECISION: about 127.9 MHz (51.7 Hz at 2200x1125) in every file and in the cmdline; 164.4-168.4 MHz if the panel accepts it. 1280x800 per-profile mode switching only if the 4D is bought. The display on/off A/B adds 1415.7 and 1544.4 MHz and 40-162 kHz. REASON: register harmonic scan; the line rate of 58.1 kHz needs the LF A/B.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  52.
    - **Gap:** C13 PPS on the held kernel
    - **Kind:** stale_or_contradictory
    - **Why it matters:** gnss_imu Route B needs kernel 7.0.11, which breaks the HDMI/NPU hold.
    - **Resolution:** DECISION: build pps-gpio out of tree as a DKMS deb for 6.18.2-4 (CONFIG_PPS=y is set). Drop Route B. Build pps-ldisc only if the FT232RL fallback is kept. Confirm with chronyc sourcestats.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  53.
    - **Gap:** C14 INA228 bus and driver
    - **Kind:** stale_or_contradictory
    - **Why it matters:** A bound ina238 hwmon driver blocks access to the CHARGE register.
    - **Resolution:** DECISION: I2C0, user-space i2c-dev with no DT binding, shunt in the pack lead ahead of the IP2368 tap. Fix power.json (i2c6, ina238) and npu_training ('on the J21 rail').
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  54.
    - **Gap:** C15 Antenna tiers (the small-stack removals re-decided)
    - **Kind:** stale_or_contradictory
    - **Why it matters:** The small-stack removals were made under a superseded size rule. The LRPT default (helical whip) is model-only. The patch tier uses a DIY helix plus a $49.95 LNA where a true patch exists.
    - **Resolution:** DECISION.
  Patch/chip tier (always carried):
  - LC76G ceramic patch;
  - RTL-SDR Blog Active L-band patch ($59.95, 1525-1660 MHz, 3.3-5 V at 20 mA, in stock; verified 18 Oct 2026) for Inmarsat-C and GNSS-SDR L1 (Iridium only as generic occupancy);
  - A-V85/SRH-701 70 cm whip on the case, tilted;
  - bare Bullseye LNB with a 10-11 cm cone (region-gated);
  - the telescopic dipole kit (23 cm collapsed) for LRPT, AIS, sondes, ADS-B and FM;
  - a 4-turn helix on a 20 cm disc for HRPT (needs the user's OK).
  Foldable tier adds: the crossed Yagi (ultra-compact; 2 m half optional), the petal helicone, the 6-gore horn, and the S helix only with the Lime.
  Struck: all loops including QFH, the 2-turn helix with SAWbird+ iO, and the helical whip as default (experiment only).
  The Lime, T7 and 12 GB board are decided by C1/C18/C2, not by antenna size.
  REASON: patch antennas cannot serve 137-146 MHz; the dipole kit meets the piece rule and is a verified LRPT antenna.
    - **Cost:** +$10 net (patch $59.95 minus iO $49.95); +0.15-0.25 kg in the patch tier
    - **Sources:**
      - https://www.rtl-sdr.com/store/
  55.
    - **Gap:** C16 Policy leftovers before STACK.md
    - **Kind:** rule_violation
    - **Why it matters:** Leftovers would re-enter at the P4/P5 re-research.
    - **Resolution:** DECISION: strike everything in stale_items_to_purge. Add a CI policy audit that greps STACK.md, build/, the menu tree, the class list and the installed package set for:
  - loops and H-probes; antenna S11; VLF SID;
  - Iridium/Orbcomm frames and CARTOSAT-3;
  - 18 V; the 145.800 ISS row;
  - wsjtx GUI, fldigi, QSSTV, SoapyRemote; the SDRangel Inmarsat C/DSC/Heat Map plugins;
  - Set B; city names; UAH price bases; the 128.70 MHz clock.
  The build fails on any hit.
    - **Cost:** $0; about 70 edits in 13 files
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md
  56.
    - **Gap:** C17 HF antenna chain and the HF+ selector
    - **Kind:** stale_or_contradictory
    - **Why it matters:** The Boni-Whip is at 10.0/12.0 V in the files. The selector is missing from the BOM. LF depends on the whip's stock.
    - **Resolution:** DECISION:
  - Boni-Whip at 12.5 V ±0.25 V from an LC filter and an LDO with 0.4 V or less dropout, behind a 0.2 A polyfuse and a labd switch (default off, DC-sense), with a locking ANT PWR jack and a BNC-SMA lead.
  - 9:1 wire for HF and NAVTEX only (0.125 MHz and up); LF only on the active whip. Use the PA0RDT clone (EUR 25.90) if the Boni-Whip (WiMo, 20 Nov 2026) is late. JJY 60 kHz amplitude only.
  - HF+ selector: a latching DC-2.5 GHz PCB RF relay pair (HF / VHF-AIS / 50 ohm), accepted only with 35 dB or more of conducted isolation at 162-260 MHz (part chosen in P5).
  - Confirm the HF-loop removal with the user.
    - **Cost:** $25-55 (estimate)
    - **Sources:**
      - https://github.com/f4exb/sdrangel/blob/master/plugins/channelrx/radioclock/readme.md
  57.
    - **Gap:** C18 Storage without the T7
    - **Kind:** stale_or_contradictory
    - **Why it matters:** menu_tree[18], [69], [77], [84] and [100] (updates and rsync snapshots) all go to the T7.
    - **Resolution:** DECISION: buy the T7 only with the Lime. Otherwise: a V30/A2 microSD (128-256 GB) and a USB stick behind an external-storage abstraction, plus an A/B root or a snapshot partition on UFS. Retention: products by default; raw IQ only when pinned, deleted after 14 days; voice bins and masked bands never written. REASON: the worst no-Lime stream is 16.4 MB/s, inside V30's 30 MB/s; dual-RTL raw is 36.9 GB/h. Test microSD sustained writes.
    - **Cost:** $25-50 (estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  58.
    - **Gap:** C19 CPU allocation
    - **Kind:** stale_or_contradictory
    - **Why it matters:** lab_ui_hf puts the trainer on the A55 cores.
    - **Resolution:** DECISION: A55 cores 0-3 for UI, daemons, NPU host and CPU inference. A78 cores 4-6 for DSP, labrx and T2 training, only between passes. CPU7 is isolated only with the Lime, otherwise used for DSP. REASON: T2 takes 4.5-10.8 min on the A78 cores (model) and several times longer on the A55 cores.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  59.
    - **Gap:** C20 Roadmaps
    - **Kind:** stale_or_contradictory
    - **Why it matters:** The labeller is needed about 3 months before the UI schedules it, and the UI shows HF classes long before the NPU has an HF profile.
    - **Resolution:** DECISION: run NPU Phase 0 inside the W1-2 gates (19 Oct-1 Nov 2026) and move a minimal labeller into P0b. The policy gates (class gate, voice mask, band mask, Artemis stop) ship before the first labeller. HF classes appear only after the HF-F and second-RTL profiles exist. First live captures on ISS SSTV Series 34 (22-25 Oct 2026).
    - **Cost:** About 2-3 extra developer days in P0b
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  60.
    - **Gap:** C21 V4L count
    - **Kind:** stale_or_contradictory
    - **Why it matters:** The files buy 1, 2 or 3 units.
    - **Resolution:** DECISION: buy 3 now (2 in service, 1 spare; $113.85) and no 4th. Continuous ADS-B uses the spare on LAB USB at camp or on the bench; AIS runs on the HF+ via the selector; monitoring otherwise time-shares. The spare also runs the 2.88 Msps Metop gate. REASON: R828S stock is finite (about 1 year), and there are no spare internal ports.
    - **Cost:** $113.85
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  61.
    - **Gap:** C22 Software recipes and exclusions
    - **Kind:** stale_or_contradictory
    - **Why it matters:** The recipes conflict, and some packages violate rule line 44.
    - **Resolution:** DECISION: one venv per tool:
  - NanoVNA-Saver via pipx; PySide6 6.12; libgpiod v1 API;
  - Skyfield 1.55 and sgp4 2.27 from pip;
  - SatDump 2.0-alpha from source, without inmarsat_support;
  - OpenWebRX+ 1.2.126 with pins;
  - SDRangel 7.27.2 receive-only, without the Inmarsat C, Heat Map and ungated DSC plugins; Radio Clock kept for LF.
  SSTV: OpenWebRX+ SSTV first; slowrx built from source as the decode-only fallback (not in noble). Excluded: wsjtx GUI (jt9/wsprd only), fldigi, QSSTV, js8call, SoapyRemote, URH. Test each on the Q6A within the return window.
    - **Cost:** $0
    - **Sources:**
      - https://packages.ubuntu.com/noble/slowrx
  62.
    - **Gap:** C23 Region unknown
    - **Kind:** stale_or_contradictory
    - **Why it matters:** QO-100, the NCS, Elektro/FY-2H, EGNOS, the LF station, the legal profile and pricing all depend on it.
    - **Resolution:** DECISION: ask the user. Meanwhile buy the region-independent core, including the L-band patch (an Inmarsat NCS covers each ocean region; GNSS works everywhere). Hold the Bullseye LNB, horn and cone materials, and the MAX-M10S; the SAWbird+ iO is no longer needed. Compute 'visible from here' per GEO target from the fix. Generalise EGNOS to regional SBAS, and rename menu_tree[86].
    - **Cost:** Defers about $35-90
    - **Sources:**
      - https://pre-egnos.gsc-europa.eu/services/open-service/open-service-realtime-performance
  63.
    - **Gap:** C24 Costs and weights
    - **Kind:** stale_or_contradictory
    - **Why it matters:** The subtotals do not match their line items, and whole classes of parts were never budgeted.
    - **Resolution:** DECISION: recompute in P5 at world prices:
  - radio_lab extended about $555-780 without H-probes;
  - internal interface $56-73;
  - plus the missing-parts BOM (about $890-1,570 gross, mostly estimates);
  - minus removals ($230-380: iO, IR, NanoVNA, H-probes, loop).
  Weights (model): patch-tier sling about 3.0-3.6 kg; foldable sling 3.7-4.4 kg, or 4.4-6.05 kg with supports, coax, bag and weather kit.
    - **Cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  64.
    - **Gap:** C25 P1b completion
    - **Kind:** stale_or_contradictory
    - **Why it matters:** The register still says report_research.json is missing. The file exists (576,735 B, 04:51), but 'errata' has 0 hits in summaries.md and minute-log.md.
    - **Resolution:** DECISION: close conflict 25. Before STACK.md, write the errata blocks: summaries #26/#43/#45/#59/#74/#75/#81/#103/#126/#128/#129/#160/#168, and the minute-log entries 02:02, 02:08-02:11, 02:15, 03:25 and 03:33.
    - **Cost:** $0
    - **Sources:**
      - /home/user/lizbeth307/sat-receiver-audit/minute-log.md
- **Dismissed gaps:**
  1.
    - **Gap:** QO-100 leaf still offers 13.4/18.2 V (goals critic)
    - **Why:** Already decided in register #102/#103 and conflict 8 (13.2 V, no 18 V). Only the text needs purging; it is listed in stale_items_to_purge and folded into C8.
  2.
    - **Gap:** LRPT leaf puts the SAWbird+ NOAA on the V4L tee (goals critic)
    - **Why:** The rule already exists (register #96/#100/#101: TPS2553 for every SAWbird+, tee for 80 mA or less). This is stale menu text, purged and covered by the C9 interlock.
  3.
    - **Gap:** Meteor HRPT own-spur and model-only margin (goals critic)
    - **Why:** Register #127 already lists the 1699.2 MHz spur and the 'validate above 40 deg' action. The only new step is adding 1699.2 MHz to the P4 spur list, which the RTL-B selector's 50 ohm port enables (RF input routing gap).
  4.
    - **Gap:** FY/Elektro/AWS labels as a separate gap (goals critic)
    - **Why:** The status is settled in register #124/#125/#55. Only the menu_tree[10] 'FY' text and foldable loss_table[10]/step 7 need purging; the GEO carrier-check leaf is in the menu-coverage gap.
  5.
    - **Gap:** Sunlight plan: add the Xenarc 702GSH as a fallback (goals critic L11)
    - **Why:** User rule line 16 fixes Wisecoco with the 4D as fallback, and register #68 rejected field monitors. The hood and the 45 min noon soak are already acceptance tests (#17). The Xenarc (low resolution, 0.70 kg, $429) or the Lilliput 719/T is only a P5 candidate if the 4D cannot be quoted at world prices.
  6.
    - **Gap:** ADS-B placed in radio_lab EXTENDED (goals critic)
    - **Why:** ADS-B coverage is already decided in register #128 and conflict 21 (time-shared or spare V4L). Only a tier label needs fixing (purged).
  7.
    - **Gap:** Iridium carrier needs a SAWbird+ IR not in the BOM (goals critic)
    - **Why:** Refuted under rule line 7 and the rules critic's decision: no named Iridium target, Doppler product or NPU class. The L-band patch (1525-1660 MHz) already shows Iridium as unnamed occupancy, so the IR is removed (-$49.95).
  8.
    - **Gap:** The L-band patch costs about $45-50, net $0 (goals critic)
    - **Why:** Refuted on price: the rtl-sdr.com store lists $59.95 today (in stock, 20 mA). The swap is still adopted, at about +$10 net.
  9.
    - **Gap:** A dedicated LNA buck rail is required because neither option works (goals critic)
    - **Why:** Partly refuted. The D36V28F5 is rated 3.2 A, so with the 2 A fuse on its input side, LAB 5 V carries 0.86 A during passes and 1.94 A on the bench (model). Only the LT3045-from-12 V line is unbuildable, which C9 resolves with a filtered LAB 5 V branch.
  10.
    - **Gap:** The LNB needs a SEPIC or buck-boost (completeness critic)
    - **Why:** Partly refuted. The device runs only between 13.4 and 16.8 V of pack voltage, so a low-noise LDO (TPS7A4701 class) at 13.2 V stays in regulation, dissipates 1.44 W at most (model), is cheaper and adds no switching spurs near the 739.5 MHz IF. The SEPIC stays the alternative (C8).
  11.
    - **Gap:** A forced-PWM buck-boost is the preferred 12 V regulator (goals critic C4)
    - **Why:** Rejected. The operating window is above the D36V50F12's 13.3 V dropout, and the part is verified and priced. A buck-boost is the fallback only if the spur or current tests fail.
  12.
    - **Gap:** labrx must be the only process that ever opens an SDR (goals critic)
    - **Why:** Too strong. auto_rx and some monitor decoders need direct device access. C7 keeps labrx as the sole opener for pass, survey and NPU profiles, and lets monitor daemons open a device only under an exclusive labd lease.
  13.
    - **Gap:** Band mask should keep band-mean noise and carve out the ILS glide path (rules critic)
    - **Why:** Superseded by rule line 41, which masks at least 225-400 MHz to 'no data' before storage. A carve-out or a stored band-mean would contradict it.
  14.
    - **Gap:** QSSTV 9.5.8 as the SSTV fallback (goals critic C22)
    - **Why:** Excluded by rule line 44 (TX-capable). The replacement is slowrx built from source, because packages.ubuntu.com has no noble slowrx package, plus OpenWebRX+ SSTV.
  15.
    - **Gap:** Small-stack NanoVNA purchase (completeness critic)
    - **Why:** Settled by rule line 45 (no antenna sweeps), and the LiteVNA 64 already covers conducted work. Purged; saves $60-130.
  16.
    - **Gap:** Tripod mount tapped into the 2 mm plate (completeness critic)
    - **Why:** Register #70 already chose a captured 1/4-20 nut; the tapped plate (1.57 threads engaged) is only an alternative line in mechanical_thermal. The alternative is purged, the steel insert is in the fasteners BOM, and a pull test at 3x weight is kept.
  17.
    - **Gap:** SAWbird+ GOES powered by micro-USB in foldable step 3 (completeness critic)
    - **Why:** Already ruled out by register #97/#100 (coax injector from a TPS2553). Stale text, purged.
  18.
    - **Gap:** Carried weight as a separate gap (completeness critic)
    - **Why:** Folded into C24 together with the supports, weather and bag items.
  19.
    - **Gap:** Set B in the NPU plan (rules critic)
    - **Why:** Already removed by register #38 and the QAIRT 2.42 rule. Purge only.
  20.
    - **Gap:** HF-loop removal has no recorded user message (rules critic)
    - **Why:** Already covered by register #5 and conflict 17. The governing file keeps the ban, so it is a phase-end question for the user, not a design gap.
  21.
    - **Gap:** Region-dependent goals as a separate gap (goals critic)
    - **Why:** Same as conflict 23 and register #109; merged into C23, including the regional-SBAS rename.
- **Stale items to purge:**
  - lab_ui_hf.json final.ui_system.menu_tree[1]: 'Lime at 30 MHz and above' -> Lime only from 300 MHz, and only when present
  - lab_ui_hf.json menu_tree[8]: 'SAWbird+ NOAA on the V4L 4.5 V tee' and the 'HF+ alternate' -> TPS2553 injector, V4L tee off
  - lab_ui_hf.json menu_tree[9], [10], [11], [14], [17], [89]: Lime RX1/RX2 defaults -> V4L/RTL defaults; [10] drop 'FY'
  - lab_ui_hf.json menu_tree[12], [13] and hf_capabilities[11]: 145.800/145.825 MHz and 'HF+ in VHF mode' -> 437.550/437.825 MHz, V4L only; QSSTV fallback -> slowrx
  - lab_ui_hf.json menu_tree[15]: 'LNB 13.4 V (V) / 18.2 V (H)' and unlabelled SSB -> 13.2 V only, with the margin label
  - lab_ui_hf.json menu_tree[17] and design.menu_tree[13], integration_table[7]: SDRangel Inmarsat C -> UDP -> labd filter -> labd egc-gate
  - lab_ui_hf.json menu_tree[18], [69], [77], [84], [100]: T7-only paths -> external-storage abstraction (microSD/USB stick), A/B root on UFS
  - lab_ui_hf.json menu_tree[23]: NPU classes on the HF band survey -> hidden until the HF-F profile exists
  - lab_ui_hf.json menu_tree[25], [26], [27], [31]: no allow-lists, DSC hidden after decode -> per-mode allow-lists, DSC format-specifier gate, civil WEFAX
  - lab_ui_hf.json menu_tree[32] and hf_capabilities[7]: 'VLF/LF carrier-amplitude logging' -> civil LF carriers only
  - lab_ui_hf.json menu_tree[33], hf_antenna.setup, verdict: Boni-Whip 12.0 V (and the 10.0 V setup text) -> 12.5 V
  - lab_ui_hf.json menu_tree[34], [98], hf_receiver.setup[8]: Wi-Fi only -> rfkill wlan + bluetooth
  - lab_ui_hf.json menu_tree[42]: 400-406 MHz scan -> 400.0-405.9 MHz
  - lab_ui_hf.json menu_tree[43], [45]: 'Lime (wide)' and 'GNSS-tagged heat map' -> V4L/HF+/tinySA, occupancy only, band mask
  - lab_ui_hf.json menu_tree[47]: bearing log from the IMU heading -> live readout, never saved
  - lab_ui_hf.json menu_tree[56]: ungated SWR/S11 page and apt nanovna-saver 0.6.3 -> Bench-gated 'Conducted S11/S21 (DUT/load only)', NanoVNA-Saver via pipx
  - lab_ui_hf.json menu_tree[59]: 'Power meter (model TBD)' -> tinySA channel power
  - lab_ui_hf.json menu_tree[64]: 'HMC241 SP4T boards' -> HMC7992 selectors plus the HF+ latching relay
  - lab_ui_hf.json menu_tree[65]: Artemis tap with no stop -> operational stop rule
  - lab_ui_hf.json menu_tree[66]: MARK saves raw IQ on voice boxes -> spectrogram only
  - lab_ui_hf.json menu_tree[86]: 'SBAS/EGNOS' -> regional SBAS
  - lab_ui_hf.json ui_system.tech_stack: qsstv 9.5.8 and apt skyfield 1.48/sgp4 2.22 -> slowrx from source; pip Skyfield 1.55 / sgp4 2.27
  - lab_ui_hf.json: '5 V boost good for about 7 A', HF+ on Q6A VBUS, trainer on the A55 cores, kernel cmdline @52 (128.70 MHz) -> about 3.4 A VCC_5V_PERI, HF+ on LAB 5 V, T2 on CPU4-6, 127.9 MHz
  - radio_lab.json final.safety_and_legal[0] and procedures[0].steps[4]: 'unless local rules explicitly allow' -> delete; close open_questions[14] as No
  - radio_lab.json final.safety_and_legal[3]: '13-18 V' -> 13.2 V; safety_and_legal[6]: fly with the 72 Wh pack -> the DIY pack never flies
  - radio_lab.json final.lab_bom[3], [40], totals, verdict: H-loop probes / PS-500 / generic E/H set -> E-field stubs only; close open_questions[0], [1]
  - radio_lab.json final.lab_bom[34] and usb_power_case_plan: 'TPS65233-class or trimmed boost' LNB, '250-300 mA limit', 'LNB 12 V into the ZFBT' (sled GPA6) -> 13.2 V LDO/SEPIC, one measured limit, never via the sled
  - radio_lab.json final.lab_bom[49] and procedures[20].steps[0]: Boni-Whip 10.0 V -> 12.5 V
  - radio_lab.json final.capabilities[1]: 'visible to 12 GHz' -> delete; capabilities[2]: GNSS-tagged Lime surveys -> occupancy only, tinySA above 1.766 GHz, band mask
  - radio_lab.json final.capabilities[16], software[8], procedures[20].steps[1]: SID carrier logging, WSJT-X/fldigi -> civil LF SID; jt9/wsprd only
  - radio_lab.json final.software[11]: SoapyRemote -> delete; libgpiod v2 -> v1 API
  - radio_lab.json integ.connections: pinctrl-mcp23s08 DT overlay (driver not built on 6.18.2-4) and 'AIC8800' -> smbus2 user space in labd; FCU760K
  - radio_lab.json usb_power_case_plan: 'Tier 1 field sling about 3.0-3.6 kg' and Lime-baseline scenarios -> recompute for no-Lime and foldable
  - radio_lab.json sweeps: AS3935 storm rule, CANADUINO, MLA-30+, YouLoop, V4L as primary HF receiver -> 30/30 rule; loops excluded; HF+
  - npu_training.json final.class_list[3]: 'Meteor/NOAA HRPT and MetOp' -> Meteor HRPT (MetOp experimental)
  - npu_training.json final.class_list[8]: SSTV 145.800 MHz -> 437.550 MHz
  - npu_training.json final.class_list[9], datasets[0], scripts_to_write[25]: voice IQ snippets, 14-day raw, mask after labelling -> no voice IQ, mask at snapshot
  - npu_training.json final.class_list[13], [17], [18]: dvbs2, wifi, bt_ble as Phase-1 classes -> conditional (Lime) or dropped from Phase 1
  - npu_training.json final.architecture, software[5], pipeline[19], roadmap[3]: Set B (ORT 1.27 + onnxruntime-qnn 2.3.0 on QAIRT 2.47) -> delete
  - npu_training.json: 'INA228 on the 12 V J21 rail' and the sdr-ingestd librtlsdr 2.0.3 recipe -> pack-lead shunt; .so.2 rebuild
  - small_antenna_stack.json final.revised_stack[12], [22], [23], [26]; reachable[2], [4], [7], [8]; lost[0], [9], [11]; borderline_options[2]; first_tests[7], [8]: loop rows, loop A/B tests, loop-plane IMU cue -> delete
  - small_antenna_stack.json final.size_rule_used and verdict: superseded STRICT/SMALL deployed-size rule, helical whip as LRPT default, Lime/T7/12 GB removals -> two-tier rule (C15)
  - small_antenna_stack.json final.first_tests[2], revised_stack[29], legal_notes[7]: NanoVNA indoor sweeps -> delete
  - small_antenna_stack.json final.reachable[8], [13], revised_stack[30], bands[1], stack.add[9], remove[0], sdr_decision, revised_bom[23], risks[7]: Orbcomm, Iridium IRA/IBC, SAWbird+ IR, CARTOSAT-3 -> delete
  - small_antenna_stack.json final.reachable[9]: stdcdec/Scytale-C with bulletin-board packets in scope, Kyiv angles, 2-turn helix + SAWbird+ iO -> egc-gate, angles computed at the fix, L-band patch
  - small_antenna_stack.json final.reachable[14], [15]: 'FT8 reliable', 'PSK reliable with cone', Kyiv az/el -> L2 table, computed at the fix
  - small_antenna_stack.json final.reachable[18], revised_stack[31]: Black Kite 'reliable' with a Pluto -> opportunistic, Lime only; Pluto not adopted
  - small_antenna_stack.json final.revised_stack[18]: MT3608/XL6009 boost LNB supply from 3S -> C8
  - small_antenna_stack.json final.revised_stack[28], reachable[15], first_tests[5]: WSJT-X -> jt9/wsprd
  - small_antenna_stack.json final.legal_notes[1]-[6], reachable[1].legal, reachable[11].legal, refuted_claims[6], excluded_by_law_or_ethics[3]: Ukrainian law framing -> generic legal note
  - small_antenna_stack.json final.revised_stack[0], cost_size_power_delta, borderline_options[0]: duty, EUR 150 rule, UAH -> world prices
  - small_antenna_stack.json: 3S pack, 8 GB board, '18.4 GB/h for two dongles, 5 h on UFS', 128.70 MHz -> 4S, 12 GB, 36.9 GB/h / 2.5 h, 127.9 MHz
  - foldable_antennas.json final.build_and_test_steps[1], [2], [3], [9], loss_table[1], [11], ultra_compact_tier, foldable_kit[0]: S11/VNA tuning -> receive-only checks
  - foldable_antennas.json final.build_and_test_steps[2]: SAWbird+ GOES via micro-USB with a DC block before the Lime -> coax injector from the bias board, V4L default
  - foldable_antennas.json final.foldable_kit[1], loss_table[1], ultra_compact_tier: '145.8 MHz (ISS SSTV)' and straight dipole for ISS -> 70 cm ISS; 2 m half optional
  - foldable_antennas.json final.foldable_kit[2], loss_table[2]: 'LimeSDR port', 'both Lime RX' -> RTL-A default
  - foldable_antennas.json final.foldable_kit[5]: '18 V or rotate the LNB' -> rotate only
  - foldable_antennas.json final.build_and_test_steps[6], loss_table[10], other_ways_out[4]: Kyiv elevations, Elektro-L5 as the assured A/B reference -> computed at the fix; NCS first, Elektro opportunistic
  - foldable_antennas.json bands[0].options[9]: collapsible QFH -> excluded (loop)
  - foldable_antennas.json final.total_cost: Ukraine shipping -> world prices
  - antennas.json research.alternatives[1]: QFH 137 MHz -> excluded
  - antennas.json fixes.fixes[0].steps[3], verify.issues[2], verify.known_problems_and_fixes_to_apply[10]: Kyiv -> computed at the fix
  - antennas.json fixes.fixes[1].steps[2], verify.known_problems_and_fixes_to_apply[0], [7], forums.common_problems[8]: VNA antenna tuning, 'fit fixed 53 cm rods' -> receive-only checks; telescopic
  - antennas.json and rf_frontend.json: purge-and-fork librtlsdr recipe -> .so.2 rebuild
  - rf_frontend.json: 13.4/18.2 V switchable LNB boost, 100-160 mA PTC per bias feed, 'GOES+ on the V4L tee after a soak', Flamingo+ 'only at strong-FM sites', 'RTL unusable for HRPT' -> delete or correct
  - display.json fixes.fixes[5].steps[2]: DIY H-field probe (15 mm loop) -> E-field semi-rigid stub
  - display.json final: 'run native 1080p60' -> 127.9 MHz field mode (1080p60 for bring-up only)
  - display_market.json final.ukraine_purchase, main_pick.price, above_fhd_tier.price, ranked_candidates[1], [3], [5], open_questions[5], [7], [8]: Ukraine basis -> world prices; 128.70 MHz -> 127.9 MHz; add the 83.77 MHz ADS-B hit
  - dish_replacement.json: optimistic QO-100 model (G+28 dB-Hz, '300 mm lens makes typical SSB readable'), four-city pointing table (fixes[0].steps[3], verify.known_problems[4], [11]) -> conservative model; computed at the fix
  - gnss_imu.json fixes[5], [6], verify.known_problems_and_fixes_to_apply[7]: Kyiv/Lviv/Kharkiv/Odesa field values -> WMM2025 at the fix; Route B (7.0.11) and UAH bases -> out-of-tree pps-gpio; world prices
  - power.json: '12 V rail also suits an LNB', i2c6 + ina238 hwmon for the INA228, UAH prices -> delete; I2C0 i2c-dev; world prices
  - mechanical_thermal.json: 9 V J21 feed (Mini560/D36V50F9), SMBJ15CA on the J21 rail, 1/4-20 'thread tapped in the aluminium plate' -> 12 V; TVS on TYPEC_IN; steel insert or captured nut
  - compute.json: 'before Ukrainian import VAT', 'pin QAIRT 2.46', '2 MB / 8.5 ms' DMA ring, 'RTL8125BG 2.5GbE', hold list without meta-packages/Mesa -> world prices, 2.42, 256 KiB / 1.07 ms, RTL8111 1 GbE, merged hold list
  - wideband_sdr.json: Lime '$310-320 landed' with Ukrainian duty; 'helix on RX-A and LNB IF on RX-B at the same time'; '30 MHz-3.8 GHz' without the matched-path caveat -> world price; delete; reword
  - software.json final: librtlsdr 2.0.3 (.so.0) plus rebuild every consumer -> .so.2 rebuild
  - storage.json: T7 9,299 UAH; 245.76 MB/s at 56 Msps -> world price; 224 MB/s (about 74 min per TB)
  - narrowband_sdr.json fixes.fixes[3].steps[4]: 'NanoVNA also tunes the Yagis and helix' -> delete; UAH bases -> world prices
  - digest.md lines 116, 140, 914, 975 (city/Kyiv) and 944 (Ukrainian EW framing) -> delete
  - summaries.md #128 (city-list fallback), #43/#45 ('500 mA per port'), #74 (245.76 MB/s), #160 ('no ISS event after May') -> errata block
  - minute-log.md 02:02 (QAIRT 2.50 current), 02:08-02:11 (USD read as grams), 02:15 ('SatDump v1.15.0' is CyberEther; 'saving $670-715'), 03:25 (A16W8 on 2.42 as fact), 03:33 (ADS-B decision) -> inline errata
  - report_research.json register.summary and conflicts_for_final_checks[24]: 'report_research.json does not exist yet' -> closed
- **Missing parts bom:**
  1.
    - **Group:** RF routing and control
    - **Item:** HMC7992 SP4T board (RTL-A and RTL-B input selectors)
    - **Qty:** 2
    - **Tier:** core
    - **Price usd:** About 30 total (CA$20.49 each, third-party listing in radio_lab, unverified)
    - **Budget alternative:** Manual 'connect X' prompt at the bulkheads ($0)
    - **Notes:** Behind the injectors, ports DC-free; 50 ohm port at power-up; check 3.3 V logic and isolation of 30 dB or more
  2.
    - **Group:** RF routing and control
    - **Item:** HF+ input selector: latching DC-2.5 GHz PCB RF relay pair on a mini PCB with 3 SMA edge jacks (HF / VHF-AIS / 50 ohm)
    - **Qty:** 1 set
    - **Tier:** core (HF chain)
    - **Price usd:** 15-35 (estimate; part chosen in P5)
    - **Budget alternative:** Manual swap at the HF bulkhead
    - **Notes:** Accept only with 35 dB or more of conducted isolation at 162-260 MHz; commercial latching SMA relays ($242 or more, 12/28 V coils) rejected
  3.
    - **Group:** RF routing and control
    - **Item:** MCP23017 #3 (Adafruit #5346) at 0x22, plus pull-down resistors
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 5.95 + about 1
    - **Budget alternative:** TCA9535 with the built-in pca953x driver (price unverified)
    - **Notes:** About 24 control lines needed against 16 on #1; labd drives it through smbus2
  4.
    - **Group:** Antennas and filters
    - **Item:** RTL-SDR Blog Active L-band patch set (1525-1660 MHz, 3.3-5 V at 20 mA)
    - **Qty:** 1
    - **Tier:** core (both tiers)
    - **Price usd:** 59.95 (rtl-sdr.com store, in stock, 18 Oct 2026)
    - **Budget alternative:** 2-turn helix + SAWbird+ iO ($49.95 plus materials)
    - **Notes:** Replaces the 2-turn helix and the iO for Inmarsat-C and GNSS-SDR; powered from the V4L tee
  5.
    - **Group:** Antennas and filters
    - **Item:** 70 cm band-pass filter: Nooelec Ham Filter Bank Barebones (2 m 144-148, 70 cm 420-450 MHz and others)
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 66.95 (radio_lab; selection method, insertion loss and DC pass unverified)
    - **Budget alternative:** Uputronics 435 filtered preamp EUR 47.64 (Kubii, last items, 5 V bias) or antennas-amplifiers.com 430-450 MHz receive BPF 119.00 (currency not shown, N-type)
    - **Notes:** Also gives the optional 2 m path; measure conducted on the LiteVNA
  6.
    - **Group:** Power and protection
    - **Item:** Internal 5-channel bias/injector board (per-band inductors rated 0.5 A or more, 1 A or more on the LNB channel; C0G blocks; SMA) with TPS2553 x4
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 25-45 (estimate)
    - **Budget alternative:** Mini-Circuits ZFBT-4R2GW+ $111.57 each (bench only)
    - **Notes:** TCBT-14+ (200 mA) only on lines of 80 mA or less
  7.
    - **Group:** Power and protection
    - **Item:** LNA bias branch filter (ferrite + LC pi) and optional LT3045 4.5 V post-LDO
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 5-12 (estimate)
    - **Budget alternative:** Pi-filter only
    - **Notes:** Fed from LAB 5 V; no LT3045 from 12 V
  8.
    - **Group:** Power and protection
    - **Item:** LNB 13.2 V supply: TPS7A4701-class 36 V/1 A LDO board + LC + PTC + SMBJ15A
    - **Qty:** 1
    - **Tier:** core (region-gated with the LNB)
    - **Price usd:** 10-20 (estimate)
    - **Budget alternative:** Pololu S18V20AHV-class SEPIC + second #2813 ($8.95): about 40-50 (S18V20AHV price not checked)
    - **Notes:** EN-off gives 0 V at the port; up to 1.44 W at 0.4 A (model)
  9.
    - **Group:** Power and protection
    - **Item:** Protection set: ATM mini-blade holders + fuses (5/7.5 A pack, 3.15 A J21, 2 A LAB input), SMBJ18A, SMBJ14A, SMBJ15A, PTC 0.75 A (AUX), PTC 0.2 A (Boni)
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 13-25 (estimate)
    - **Budget alternative:** -
    - **Notes:** Fixes the 7.5 vs 5 A conflict per Lime state
  10.
    - **Group:** Power and protection
    - **Item:** Boni-Whip ANT PWR: 2-pin locking panel jack + 1-2 m DC lead + BNC-SMA lead
    - **Qty:** 1 set
    - **Tier:** core (HF chain)
    - **Price usd:** 10-20 (BNC-SMA $5-10 per register; rest estimate)
    - **Budget alternative:** -
    - **Notes:** Default off, DC-sense
  11.
    - **Group:** Power and protection
    - **Item:** Sealed 12-16 mm momentary power key for the #2813 + XT30 loop arming plug
    - **Qty:** 1 each
    - **Tier:** core
    - **Price usd:** 8-15 (estimate)
    - **Budget alternative:** -
    - **Notes:** Travel disconnect
  12.
    - **Group:** Power and protection
    - **Item:** 65-100 W USB-C PD wall charger + 1 m 5 A C-C cable
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 35-60 (estimate)
    - **Budget alternative:** Existing PD bank (60 W or more)
    - **Notes:** The IP2368 at 4S/3 A needs a PD source of 60 W or more
  13.
    - **Group:** Battery build and safety
    - **Item:** Molicel P50B 21700 cells (4 + 1 spare)
    - **Qty:** 5
    - **Tier:** core
    - **Price usd:** About 39 (NKON EUR 6.75 incl. VAT each per the completeness critic, page dated 31 Jul 2026; unverified, NKON blocked the fetch)
    - **Budget alternative:** Other established EU/US cell sellers
    - **Notes:** Test IR and capacity before welding
  14.
    - **Group:** Battery build and safety
    - **Item:** Pack sundries: 0.15x8 mm pure nickel, fish-paper rings, Kapton, glass-fibre tape, 4S wrap, JST-XH 5-pin balance lead + service connector, XT30 lead
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 10-25 (estimate)
    - **Budget alternative:** -
    - **Notes:** No spring holders, no soldering to cells
  15.
    - **Group:** Battery build and safety
    - **Item:** Spot-welding by a battery shop or pack builder
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 20-40 (estimate)
    - **Budget alternative:** Capacitor spot welder $270-305 (unverified), only for repeated builds
    - **Notes:** -
  16.
    - **Group:** Battery build and safety
    - **Item:** Pack containment (1 mm FR-4 or mica barrier, vent-path parts) + fire-resistant charging bag
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 20-45 (estimate)
    - **Budget alternative:** Use the 2 mm aluminium mid-plate as the barrier
    - **Notes:** Rule line 46
  17.
    - **Group:** Battery build and safety
    - **Item:** ISDT 608PD balance charger (if not already in a BOM)
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 32.99-42.99 (completeness critic, unverified here)
    - **Budget alternative:** -
    - **Notes:** Monthly 4.20 V balance charge
  18.
    - **Group:** Cables and adapters
    - **Item:** Cable schedule set: 6 internal RG316 SMA jumpers, F-F bulkhead + 75 ohm lead, IPX-SMA pigtail, 2 V4L USB extensions + ferrites, 4 CH334F pad pigtails, touch lead with VBUS cut, shielded 10-15 cm HDMI + Mix 31/61, 4 RG316 1-2 m feed jumpers, 1 m thin 75 ohm F-F, SMA M-M / F-SMA / barrels, USB3 A-A EDL cable
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 90-170 (estimate)
    - **Budget alternative:** VNA-screened generic RG316
    - **Notes:** Record the HF+ USB connector type on arrival
  19.
    - **Group:** Mechanical, weather and supports
    - **Item:** Travel tripod (35 cm or less folded, 1.2 m or more, 1/4-20, mini pan-tilt head)
    - **Qty:** 1
    - **Tier:** foldable
    - **Price usd:** 40-100 (estimate)
    - **Budget alternative:** Dipole kit's flexible mini tripod + hand holding
    - **Notes:** For the horn, the helicone and the V-dipole at 1-1.1 m
  20.
    - **Group:** Mechanical, weather and supports
    - **Item:** Shock-corded tent-pole mast (7 x 35 cm, about 2.4 m) + 3 guy cords + stake + throw cord
    - **Qty:** 1 set
    - **Tier:** foldable / HF
    - **Price usd:** 15-50 (estimate)
    - **Budget alternative:** Tree or fence mount
    - **Notes:** Boni-Whip at least 2 m up
  21.
    - **Group:** Mechanical, weather and supports
    - **Item:** Weather kit (IPX4/IP54): stainless mesh + hydrophobic foam, ePTFE vents, silicone port caps, rain sleeve, 2-3 IP65 boxes with glands, self-amalgamating tape, dielectric grease, silica gel
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 45-110 (estimate)
    - **Budget alternative:** Rain sleeve + caps only
    - **Notes:** IP67 is not reachable with forced-air cooling (physics)
  22.
    - **Group:** Mechanical, weather and supports
    - **Item:** Fasteners and thermal: M2.5/M3 heat-set inserts, A2 screws, nylon/brass screws near the IMU, steel 1/4-20 insert, 2 strap lugs + hand and sling straps, 1-2 mm 3-6 W/mK pads, paste, 7in AR film, element tip caps
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 57-110 (estimate)
    - **Budget alternative:** -
    - **Notes:** Pull-test the 1/4-20 at 3x device weight
  23.
    - **Group:** HMI and audio
    - **Item:** 2 O-ring push encoders, 6 IP67 tact keys, knobs, VEML7700 breakout, RGB LED, piezo, 3.5 mm panel extension, wired headphones
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 30-65 (estimate)
    - **Budget alternative:** Unsealed EC11 with an O-ring boot
    - **Notes:** No speaker until a terminated-floor A/B passes
  24.
    - **Group:** HMI and audio
    - **Item:** IMU puck kit (GX12 4-pin pair, 2 m shielded 4-core, shield can) + IPX-SMA bulkhead + optional 3 m active GNSS antenna + service hatch (UART/RJ45)
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 30-55 (estimate)
    - **Budget alternative:** Lid patch only, if it passes the C/N0 on/off test
    - **Notes:** -
  25.
    - **Group:** Storage and recovery
    - **Item:** V30/A2 microSD 128-256 GB + 64 GB USB stick (no-T7 secondary storage and offline bundles)
    - **Qty:** 1 each
    - **Tier:** core (no-Lime path)
    - **Price usd:** 25-50 (estimate, unverified)
    - **Budget alternative:** A/B root on UFS only
    - **Notes:** Test sustained writes (16.4 MB/s worst stream)
  26.
    - **Group:** Storage and recovery
    - **Item:** Recovery kit: Radxa RA019-E1U1 UFS/eMMC USB3 reader, 32-64 GB A2 rescue microSD, USB3 card reader
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 25-40 (reader EUR 13.00 at TinyTronics per the critic, unverified; rest estimate)
    - **Budget alternative:** -
    - **Notes:** Archive BIOS 260120, edl-ng, the image and QAIRT 2.42 with SHA-256
  27.
    - **Group:** Bags, spares and tools
    - **Item:** Padded antenna roll + element tube + 10-12 L sling
    - **Qty:** 1 set
    - **Tier:** foldable
    - **Price usd:** 50-95 (estimate)
    - **Budget alternative:** -
    - **Notes:** Sharp 0.3-0.5 mm petal and gore edges
  28.
    - **Group:** Bags, spares and tools
    - **Item:** Second RTL-SDR Blog multipurpose dipole kit (spare telescopic elements)
    - **Qty:** 1
    - **Tier:** optional
    - **Price usd:** 17.95 (rtl-sdr.com store, 18 Oct 2026)
    - **Budget alternative:** Spare elements only
    - **Notes:** -
  29.
    - **Group:** Bags, spares and tools
    - **Item:** Build tools: digital calipers, snips + deburr tool, M5 tap and die, heat gun (crimper only if jumpers are not bought ready-made)
    - **Qty:** 1 set
    - **Tier:** core (build)
    - **Price usd:** 80-140 (+30-80 ASA print service if no enclosed printer) (estimate)
    - **Budget alternative:** Borrow / makerspace
    - **Notes:** Measure the LNB neck and waveguide first
  30.
    - **Group:** Home base (conditional)
    - **Item:** x86-64 machine with 16 GB RAM or more running an ubuntu:22.04 / Python 3.10 container for QAIRT 2.42; optional RTX 3060 12 GB-class GPU; 2-4 TB backup disk
    - **Qty:** 1
    - **Tier:** home base
    - **Price usd:** 0 if owned; GPU about EUR 298 (France) to about $500 (US), July 2026 per the critic; disk 60-100 (estimate)
    - **Budget alternative:** Cloud VM for conversion only, with synthetic/satellite data and after a licence check
    - **Notes:** Ask the user
  31.
    - **Group:** Optional / gated
    - **Item:** Airspy Mini (Metop AHRPT)
    - **Qty:** 1
    - **Tier:** optional (gate L1)
    - **Price usd:** About GBP 110 (undated, unverified)
    - **Budget alternative:** Spare V4L at 2.88 Msps
    - **Notes:** Only if the 2.88 Msps zero-drop test fails
  32.
    - **Group:** Optional / gated
    - **Item:** Second Flamingo+ FM + second LNA V2 (2 m path)
    - **Qty:** 1 each
    - **Tier:** optional
    - **Price usd:** 24.95 + 19.95
    - **Budget alternative:** Filter Bank 2 m channel
    - **Notes:** Only if the 2 m Yagi half is carried and the filter bank is not bought
  33.
    - **Group:** Optional / gated
    - **Item:** PA0RDT miniwhip clone
    - **Qty:** 1
    - **Tier:** optional
    - **Price usd:** EUR 25.90 (register)
    - **Budget alternative:** -
    - **Notes:** Only if the Boni-Whip slips past 20 Nov 2026
  34.
    - **Group:** Optional / gated
    - **Item:** S-band LNA (unnamed) + cf2235-kt30 cavity
    - **Qty:** 1 each
    - **Tier:** only with the Lime
    - **Price usd:** LNA unpriced; cavity EUR 65.45
    - **Budget alternative:** -
    - **Notes:** HamTV needs its own 2.4 GHz filter
  35.
    - **Group:** Removals (credit)
    - **Item:** SAWbird+ iO, SAWbird+ IR, small-stack NanoVNA, H-field probe line, DIY loop; ADALM-PLUTO not adopted
    - **Qty:** -
    - **Tier:** -
    - **Price usd:** -230 to -380 (iO -49.95, IR -49.95, NanoVNA -60 to -130, H-probes -50 to -109, loop -20 to -40)
    - **Budget alternative:** -
    - **Notes:** Missing-parts total about $890-1,570 gross, so about $510-1,340 net of the removals (mostly estimates)
- **Legal and safety notes:**
  - Country unknown. Owning a receiver is licence-free in most countries, but what may be listened to differs. UK WTA 2006 s48 makes it an offence to use apparatus to obtain the contents, sender or addressee of messages not intended for you, or to disclose them. Germany's TDDDG §5 allows only messages meant for the operator, radio amateurs, the general public or an unspecified group, and forbids passing on the content, or even the fact, of other receptions. US 18 USC 2511(2)(g) permits readily accessible radio communications (amateur, marine, aeronautical, distress). These texts were checked by the rules critic on 18 Oct 2026; I did not re-fetch them.
  - Default decode scope: broadcast, amateur, meteorological satellites, navigation and time, ISS amateur, public MSI (NAVTEX, EGC SafetyNET via the egc-gate, DSC distress/urgency/safety only), and civil met WEFAX. No air-band or marine voice presets. Nothing is published or uploaded without checking local rules; all uploaders are off by default.
  - Inmarsat-C: user traffic, LES and ship channels and FleetNET are excluded. The profile ships disabled until the header-level egc-gate passes its mixed-recording test.
  - Military and dual-use: no chains, classes or logs aimed at military emitters. 3-30 kHz and 225-400 MHz are masked to 'no data'. Artemis matches show 'out of scope' only. ADS-B military-flagged tracks (readsb dbFlags&1) and AIS type 35 are neither shown nor logged. Northwood WEFAX is excluded. The USCG-run NWS fax stations are excluded by default; ask the user, because the USCG is an armed service while NAVTEX is an explicit target.
  - ADS-B and AIS identifiers can be personal data (for example leisure-craft MMSIs, LADD/PIA aircraft). Keep logs local, do not upload, and strip identifiers from NPU oracles. Round every export location to 0.1 deg or a 4-character locator so recordings do not reveal the home.
  - Receive-only: the Lime TX ports carry 50 ohm loads, with a TX-reject patch and the guard (if the Lime is kept). No TX-capable software is installed. The VNA, tinySA generator, GPSDO tone and noise source are used conducted only, into loads or DUTs, at -40 dBm or less into chains. Model: a -10 dBm antenna sweep would be about 33 dB above an FCC 15.209-class limit at 3 m and about 44 dB above GPS C/A at 100 m on L1, i.e. an unlicensed emission that can disturb nearby GNSS.
  - Bluetooth and Wi-Fi are rfkill-blocked at every boot and in every field, pass and record mode. Wi-Fi is unblocked only at home. A tinySA self-test checks that 2.4 GHz is silent.
  - Battery:
  - The home-built 4S 72 Wh pack is never flown (IATA requires a UN 38.3 battery type). A commercial bank of 100 Wh or less goes in carry-on with terminals insulated.
  - Charge 0-45 C only (NTC window), supervised, on a non-flammable surface or in a fire bag. Store at about 50 % SoC (3.6-3.8 V/cell).
  - Spot-weld only; barrier and vent path; KSD9700 70 C on the IP2368; retire swollen or dented cells.
  - Pack fuse 5 A without the Lime, 7.5 A with it.
  - DC hazards: the LNB feed (13.2 V) into a 1 W ANNE-50+ dissipates about 3.5 W, and it is 8.2 V above the tinySA's ±5 V DC input limit. Switch the feed off before connecting or disconnecting, put a DC block toward every SDR and instrument, and never route the LNB feed via AUX, the sled or the raw pack. Bias is never applied to DC-shorted antennas (hairpin matches, the 9:1 balun); librtlsdr bias calls need a labd token.
  - Outdoor: 30/30 thunder rule (no AS3935); take antennas down at the first thunder; discharge before connecting; use a GDT only with an earth that meets the electrical code. Keep at least 2x the antenna or wire height from overhead lines. Tip caps on telescopic and tape elements; eye protection when throwing a line; guy or lower masts in wind.
  - Radiosonde chase: obey traffic rules, respect private land and airfields, never climb trees or poles, and keep away from power lines. The auto_rx scan stops at 405.9 MHz, clear of the 406.0-406.1 MHz distress-beacon band.
  - Thermal and bench: accept the case only if the frame stays at 60 C or less and the glass at 65 C or less after the 45 min noon soak, with the hood fitted. Pinecil on a fused lead with Bluetooth off; ventilate solder fumes; use the ESD mat for the Q6A and LNAs.
  - Purchases: confirm that the LimeSDR pre-order is refundable before the gate. Buy V4Ls, the tinySA and the LiteVNA only from official sellers (clone risk). Region-specific services (NOAA SAME, HD Radio, UAT, dump978) are enabled only in the matching region profile.

## sourcing:group2 (run `wf_b9cc0186-94e`)

- **Group:** SDR + RF FRONT END + ANTENNAS (final verified picks; loops, H-field probes, YouLoop, VNA antenna sweeps and the 18 V LNB branch are excluded by the user's rules)
- **Offers:**
  1.
    - **Item:** RTL-SDR Blog V4L (Lite) R828S RTL2832U 1 ppm TCXO SMA, dongle only (buy 3: RTL-A, RTL-B, 1 spare)
    - **Seller:** RTL-SDR Blog official store (rtl-sdr.com)
    - **Url:** https://www.rtl-sdr.com/product/rtl-sdr-blog-v4l-lite-r828s-rtl2832u-1ppm-tcxo-sma-software-defined-radio-dongle-only/
    - **Price:** USD 37.95 each (3 = USD 113.85)
    - **Price usd:** 37.95
    - **In stock:** yes, 455 in stock (18 Oct 2026)
    - **Ships to:** Worldwide from the China warehouse, free economy shipping or paid express. Not to RU/BY or sanctioned countries. The webstore does not ship to the EU directly: EU buyers use the official eBay (rtl-sdr-blog) or AliExpress 'RTLSDRBlog Store' no. 4523039, or a listed reseller.
    - **Official channel:** так
    - **Notes:** HIGH clone risk. Blue/green cases, square silver 4-screw cases and 'Pro' labels are fakes, so buy only from the official store, eBay or AliExpress store, or a listed reseller. The R828S is end of life, so buy all 3 now. Amazon USA had not stocked it yet. Needs the patched librtlsdr .so.2.
  2.
    - **Item:** Airspy HF+ Discovery
    - **Seller:** ITEAD Studio (Airspy's official manufacturing partner)
    - **Url:** https://itead.cc/product/airspy-hf-discovery/
    - **Price:** USD 169.00
    - **Price usd:** 169.00
    - **In stock:** add-to-cart active; no stock count shown
    - **Ships to:** EU warehouse (3-6 days, card only); US warehouse (3-6 days); rest of world from China (15-35 days standard, 4-10 days expedited)
    - **Official channel:** так
    - **Notes:** MEDIUM clone risk. Buy only from the dealers listed at airspy.com/purchase: ITEAD, RTL-SDR.com (Amazon), WiMo, Moonraker, Ham Shop NL, FB Radio, AstroRadio, Neven, SDR UA (Ukraine only), AOR Japan. Its current draw is unpublished, so measure it.
  3.
    - **Item:** Airspy HF+ Discovery
    - **Seller:** AstroRadio, Barcelona (official Airspy dealer)
    - **Url:** https://www.astroradio.com/p/airspy_hf_discovery/
    - **Price:** EUR 214.17
    - **Price usd:** 248.44
    - **In stock:** not shown
    - **Ships to:** Spain/EU
    - **Official channel:** так
    - **Notes:** EU price including VAT. Converted at 1.16 USD/EUR.
  4.
    - **Item:** Airspy HF+ Discovery (SKU 10-201)
    - **Seller:** Moonraker (official Airspy dealer, UK/EU/US storefronts)
    - **Url:** https://moonrakeronline.com/eu/airspy-hf-plus-discovery-high-peformance-sdr-receiver
    - **Price:** EUR 231.99 (EU page) / USD 223.95 (US page, moonrakeronline.com/us/...)
    - **Price usd:** 223.95
    - **In stock:** 'in stock' per search snippet only; the page returned 403
    - **Ships to:** UK/EU (duty and tax paid at checkout) and US
    - **Official channel:** так
    - **Notes:** Search snippet only, so treat as unconfirmed.
  5.
    - **Item:** LimeSDR Micro M.2 2280 Basic (no GNSS); GATED OPTIONAL, cancellable pre-order
    - **Seller:** Crowd Supply (Lime Microsystems' official channel)
    - **Url:** https://www.crowdsupply.com/lime-micro/limesdr-micro
    - **Price:** USD 249 + shipping USD 8 (US) / USD 18 (worldwide) = USD 267 worldwide
    - **Price usd:** 267.00
    - **In stock:** pre-order; estimated ship date 15 Dec 2026
    - **Ships to:** Worldwide (USD 18). Buyer pays import VAT/duty.
    - **Official channel:** так
    - **Notes:** The GNSS variant is USD 299 and is not wanted. The listing has no 2230 variant, so the 80 mm card needs a support post or a riser in the Q6A 2230 M-key socket. The last campaign update was 17 Jun 2026. Store pre-orders are refundable before shipment.
  6.
    - **Item:** MHF4L to SMA(f) bulkhead coax cable, 100 mm (2x, only if the Lime is kept)
    - **Seller:** Crowd Supply (Lime accessory)
    - **Url:** https://www.crowdsupply.com/lime-micro/limesdr-micro
    - **Price:** USD 6 each (2 = USD 12), same shipping as the Lime order
    - **Price usd:** 6.00
    - **In stock:** yes (listed as in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Order with the Lime to share shipping. Label the pigtails X2/X4.
  7.
    - **Item:** ADT-Link R44SF M.2 NVMe M-key male-to-female extender, 5 cm (M.2 riser, only if the Lime is kept)
    - **Seller:** ADT-Link (manufacturer webshop)
    - **Url:** http://www.adt.link/product/R44SF.html
    - **Price:** USD 19.00 (5 cm); 3 cm USD 21, 10 cm USD 19
    - **Price usd:** 19.00
    - **In stock:** not shown (order via webshop R44-Shop.html or adt-sales@adt.link)
    - **Ships to:** From China; PayPal accepted. Destinations not listed.
    - **Official channel:** так
    - **Notes:** PCIe 3.0 x4 rated, which covers the Lime's Gen3 x1/x2. Third-party Newegg R44SF 4.0 listings are USD 39.99+ (20 cm) and are not official. Check whether it connects the M.2 SMBus pins (host-freeze risk).
  8.
    - **Item:** I-PEX 90435-001 MHF4 mating/unmating tool (only if the Lime is kept)
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=90435-001
    - **Price:** USD 18.10
    - **Price usd:** 18.10
    - **In stock:** yes, 474 (DigiKey part 5378-90435-001-ND)
    - **Ships to:** Worldwide (DigiKey international)
    - **Official channel:** так
    - **Notes:** Lime-only item.
  9.
    - **Item:** RTL-SDR Blog Wideband LNA V2 (QPL9547, bias-tee powered, 100 MHz-6 GHz)
    - **Seller:** RTL-SDR Blog official store
    - **Url:** https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
    - **Price:** USD 19.95
    - **Price usd:** 19.95
    - **In stock:** yes, 208 in stock
    - **Ships to:** Worldwide from China; Amazon USA in stock
    - **Official channel:** так
    - **Notes:** The vendor's buy page lists 3-5 V at 90 mA. That is above the register's 80 mA V4L-tee rule; see the notes for the decision. The radio_lab core spare adds a second unit.
  10.
    - **Item:** Nooelec SAWbird+ GOES, enclosed (SKU 100792; 1688 MHz, includes free aluminium enclosure)
    - **Seller:** Nooelec official store
    - **Url:** https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-goes-302.html
    - **Price:** USD 49.95
    - **Price usd:** 49.95
    - **In stock:** add-to-cart active; no stock text; ships in 1 business day
    - **Ships to:** From the USA; free worldwide shipping on orders over USD 100
    - **Official channel:** так
    - **Notes:** Use the cased version at the helix feed. 180 mA nominal, 3-5 V on the SMA. Feed it from a TPS2553 injector at 250-300 mA, never from the V4L tee. The Barebones SAWbird+ GOES is USD 44.95 (inside a shielded case only).
  11.
    - **Item:** Nooelec SAWbird+ iO, enclosed (SKU 100788; 1542 MHz, 60 MHz passband, 30 dB or more)
    - **Seller:** Nooelec official store
    - **Url:** https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-io-303.html
    - **Price:** USD 49.95
    - **Price usd:** 49.95
    - **In stock:** add-to-cart active; no stock text
    - **Ships to:** From the USA; free worldwide shipping over USD 100
    - **Official channel:** так
    - **Notes:** 180 mA nominal; TPS2553 injector. Used for Inmarsat-C EGC SafetyNET only, with header-level discard. The non-plus iO Barebones is USD 39.95.
  12.
    - **Item:** Nooelec Flamingo+ FM v2 broadcast FM band-stop (SKU 100813) - THE FM filter
    - **Seller:** Nooelec official store
    - **Url:** https://www.nooelec.com/store/flamingo-plus-fm.html
    - **Price:** USD 24.95
    - **Price usd:** 24.95
    - **In stock:** add-to-cart active; no stock text
    - **Ships to:** From the USA; free worldwide shipping over USD 100
    - **Official channel:** так
    - **Notes:** Over 60 dB average rejection; under 0.25 dB loss out of band; 250 mA minimum DC pass. Fitted permanently in the 137/145 MHz path. An SMA M-M barrel is included.
  13.
    - **Item:** RTL-SDR Blog Broadcast FM Band-Stop Filter (alternative only, not the pick)
    - **Seller:** RTL-SDR Blog official store
    - **Url:** https://www.rtl-sdr.com/product/rtl-sdr-blog-broadcast-fm-band-stop-filter/
    - **Price:** USD 16.95
    - **Price usd:** 16.95
    - **In stock:** yes, 131 in stock
    - **Ships to:** Worldwide from China; Amazon USA
    - **Official channel:** так
    - **Notes:** Over 50 dB rejection, under 0.5 dB loss to 1 GHz, no published DC rating. Not bought, because the standard is the Flamingo+.
  14.
    - **Item:** Nooelec SMA in-line DC block (2 W maximum)
    - **Seller:** Nooelec official store
    - **Url:** https://www.nooelec.com/store/dc-block.html
    - **Price:** USD 24.95
    - **Price usd:** 24.95
    - **In stock:** add-to-cart active
    - **Ships to:** From the USA; free worldwide over USD 100
    - **Official channel:** так
    - **Notes:** Its frequency and voltage ratings are not shown, so VNA-check it (conducted) on arrival. Mini-Circuits BLK-89-S+ is the better-specified choice.
  15.
    - **Item:** Mini-Circuits BLK-89-S+ DC block, SMA-F/SMA-M (2x in the core set)
    - **Seller:** Mini-Circuits webstore
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=BLK-89-S%2B
    - **Price:** USD 20.26 each (qty 1)
    - **Price usd:** 20.26
    - **In stock:** yes, more than 1,000 at Mini-Circuits (DigiKey 0)
    - **Ships to:** Mini-Circuits ships internationally, subject to export screening
    - **Official channel:** так
    - **Notes:** Matches the register's core accessory set (2x).
  16.
    - **Item:** Mini-Circuits BLK-18-S+ DC block, SMA-F/SMA-M (higher-frequency alternative)
    - **Seller:** Mini-Circuits webstore
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=BLK-18-S%2B
    - **Price:** USD 29.73
    - **Price usd:** 29.73
    - **In stock:** yes, more than 1,000
    - **Ships to:** International
    - **Official channel:** так
    - **Notes:** Use only if a block rated above 8 GHz is wanted. Not needed: the highest SDR-side frequency is the 739 MHz LNB IF or 2.2 GHz.
  17.
    - **Item:** Mini-Circuits TCBT-2R5G+ surface-mount bias tee (20 MHz-2.5 GHz), for the DIY 5 V LNA injectors in the shielded bay (3x)
    - **Seller:** DigiKey (3157-TCBT-2R5G+CT-ND)
    - **Url:** https://www.digikey.com/en/products/result?keywords=TCBT-2R5G%2B
    - **Price:** USD 11.31 each (qty 1, cut tape)
    - **Price usd:** 11.31
    - **In stock:** yes, 1,350 at DigiKey; Mini-Circuits 71 (its minimum order there is 10 at USD 9.05)
    - **Ships to:** Worldwide (DigiKey)
    - **Official channel:** так
    - **Notes:** Meets the register's 'injector rated down to about 100 MHz' requirement (20 MHz low edge), unlike generic 10 MHz-6 GHz boxes that lose 3-7 dB at 100-200 MHz. Check the datasheet DC current limit against 180 mA SAWbird+ loads and against the measured Bullseye current if used for the LNB.
  18.
    - **Item:** Mini-Circuits ZFBT-4R2GW+ connectorized bias tee, SMA (premium LNB / VHF injector option)
    - **Seller:** Mini-Circuits webstore
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=ZFBT-4R2GW%2B
    - **Price:** USD 111.57
    - **Price usd:** 111.57
    - **In stock:** yes, more than 100 at Mini-Circuits (DigiKey 0)
    - **Ships to:** International
    - **Official channel:** так
    - **Notes:** radio_lab dropped the ZFBT from its core set. Only worth it as a ready-made, characterised LNB injector; confirm the datasheet DC voltage/current rating against 13.2 V and the measured LNB draw. ZFBT-6GW+ is USD 125.54 (5 in stock) and not needed.
  19.
    - **Item:** Othernet QO-100 Bullseye TCXO LNB
    - **Seller:** RTL-SDR Blog official store
    - **Url:** https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
    - **Price:** USD 29.95
    - **Price usd:** 29.95
    - **In stock:** yes, 70 in stock
    - **Ships to:** Worldwide from China; also an Amazon UK/EU reseller
    - **Official channel:** так
    - **Notes:** HOLD until the region is known to be inside the QO-100 footprint. It needs 11.5-14 V for vertical: the plan supplies 13.2 V with true disconnect and no 18 V branch. Supply current, length and neck size are unpublished, so measure them on arrival before building the horn.
  20.
    - **Item:** Bullseye Ultra High Stability Single LNB for QO-100, 2 ppm TCXO (code LNBBullseye)
    - **Seller:** Technofix UK (official RTL-SDR Blog reseller)
    - **Url:** https://shop.technofix.uk/bullseye-ultra-high-stability-single-lnb-for-qo-100-2ppm-tcxo
    - **Price:** GBP 31.99 incl. UK VAT
    - **Price usd:** 42.87
    - **In stock:** OUT OF STOCK
    - **Ships to:** UK; non-UK buyers may owe import tax/duty
    - **Official channel:** так
    - **Notes:** Confirms a 'universal 40 mm LNB fixing', so the horn's 40.2 mm collar is consistent. Converted at 1.34 USD/GBP.
  21.
    - **Item:** RTL-SDR Blog Multipurpose Dipole Antenna Kit (foldable 137 MHz V-dipole; also AIS/sonde/ADS-B arms)
    - **Seller:** RTL-SDR Blog official store
    - **Url:** https://www.rtl-sdr.com/product/rtl-sdr-blog-multipurpose-dipole-antenna-kit/
    - **Price:** USD 17.95
    - **Price usd:** 17.95
    - **In stock:** yes, 357 in stock
    - **Ships to:** Worldwide from China (Amazon USA stock unclear)
    - **Official channel:** так
    - **Notes:** Contents: base with 60 cm RG174, 2x telescopics 23 cm-1 m, 2x 5-13 cm, 3 m RG174 extension, flexible tripod, suction mount. A second kit is the only official source of spare telescopic elements.
  22.
    - **Item:** RTL-SDR Blog Active L-band Patch Antenna (1525-1660 MHz RHCP, SAW filtered; Inmarsat-C / GNSS patch tier)
    - **Seller:** RTL-SDR Blog official store
    - **Url:** https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
    - **Price:** USD 59.95
    - **Price usd:** 59.95
    - **In stock:** in stock (Amazon USA and China warehouse, per the buy page)
    - **Ships to:** Worldwide from China; Amazon USA
    - **Official channel:** так
    - **Notes:** 3.3-5 V at 20 mA, so the V4L tee is fine. It does not cover HRPT (1.7 GHz) or L5. The product URL returned 404, so the price and stock come from the official buy page.
  23.
    - **Item:** Waveshare GNSS L1+L5 dual-frequency active antenna, SMA-J (SKU 25346, 'GPS External Antenna (D)')
    - **Seller:** Waveshare official store
    - **Url:** https://www.waveshare.com/gps-external-antenna-d.htm
    - **Price:** USD 16.99
    - **Price usd:** 16.99
    - **In stock:** add-to-cart active; no stock indicator
    - **Ships to:** Worldwide except IR/KP/CU/SD/SY
    - **Official channel:** так
    - **Notes:** The GNSS-SDR / EGNOS patch for the V4L: L1/E1/B1 plus L5/E5a/B2a, 2 dBi, 28 dB LNA, 3-18 V at 20 mA or less (V4L tee OK), 50x50x19 mm, 3 m RG174. Budget pick.
  24.
    - **Item:** u-blox ANN-MB5 multi-band active GNSS antenna L1/L5 (SparkFun GPS-25071)
    - **Seller:** SparkFun
    - **Url:** https://www.sparkfun.com/u-blox-multi-band-active-gnss-antenna-l1-l5-ann-mb5.html
    - **Price:** USD 42.50
    - **Price usd:** 42.50
    - **In stock:** yes, in stock
    - **Ships to:** US; SparkFun ships internationally
    - **Official channel:** так
    - **Notes:** Higher-grade L1/L5 alternative (L1 1559-1608 MHz, L5 1164-1186 MHz), 3 m RG174, SMA. Core Electronics AU sells it at AUD 73.55.
  25.
    - **Item:** Nooelec Balun One Nine v2, enclosed (9:1 HF balun/unun)
    - **Seller:** Nooelec official store
    - **Url:** https://www.nooelec.com/store/balun-one-nine-v2.html
    - **Price:** USD 26.95 (v2 Barebones USD 21.95; old v1 USD 15.95)
    - **Price usd:** 26.95
    - **In stock:** listed (search result); stock not shown
    - **Ships to:** From the USA; free worldwide over USD 100
    - **Official channel:** так
    - **Notes:** For the HF wire, HF only. It is a DC short, so labd locks bias off. LF time signals go to the Boni-Whip.
  26.
    - **Item:** Bonito Boni-Whip active E-field whip, 10 kHz-300 MHz, BNC (WiMo item 18067; includes its bias-tee power crossover)
    - **Seller:** WiMo (Germany, official Bonito dealer)
    - **Url:** https://www.wimo.com/es/18067
    - **Price:** EUR 159.00 incl. VAT (EUR 133.61 net) plus shipping
    - **Price usd:** 184.44
    - **In stock:** no; available from 20 Nov 2026
    - **Ships to:** EU and international (WiMo)
    - **Official channel:** так
    - **Notes:** 9-15 V supply, about 14 cm, 189 g. Feed 12.5 V from the LDO on the 4S pack. Current unpublished, so measure it. The net price (USD 155) applies to buyers outside the EU. Converted at 1.16 USD/EUR.
  27.
    - **Item:** Bonito Boni-Whip active antenna (SKU 34-010)
    - **Seller:** Moonraker (UK/EU/US storefronts)
    - **Url:** https://moonrakeronline.com/us/bonito-boni-whip-active-antenna
    - **Price:** USD 123.95 sale (US page) / EUR 127.27 (EU page) / GBP 109.95 (UK page)
    - **Price usd:** 123.95
    - **In stock:** unknown (search snippet only; page 403)
    - **Ships to:** UK, Eurozone (DPD, duties included), US
    - **Official channel:** так
    - **Notes:** Moonraker gives the length as 17 cm (WiMo says 14 cm). Unconfirmed snippet; cheaper than WiMo if live.
  28.
    - **Item:** Tecsun AN-05 FM/SW reel antenna with clip, 7.0 m (HF wire reel)
    - **Seller:** Moonraker
    - **Url:** https://moonrakeronline.com/us/an-05-fm-sw-reel-antenna-with-clip
    - **Price:** USD 14.49 sale (US page) / EUR 15.41 (EU) / GBP 12.95 (UK)
    - **Price usd:** 14.49
    - **In stock:** unclear: the page shows both 'In stock' and 'Out of stock' (search snippet; page 403)
    - **Ships to:** UK/EU/US
    - **Official channel:** ні
    - **Notes:** Retailer, not Tecsun-official. An eBay.de UK seller had GBP 14.94 (2 left, Aug 2025 listing). The alternative is 10-15 m of wire on a winder of 20 cm or less.
  29.
    - **Item:** Mini-Circuits 086-24SM+ hand-flex 0.086 in coax jumper, SMA-SMA, 24 in (61 cm)
    - **Seller:** Mini-Circuits webstore
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=086-24SM%2B
    - **Price:** USD 24.73 (qty 1-9)
    - **Price usd:** 24.73
    - **In stock:** yes, 356
    - **Ships to:** International
    - **Official channel:** так
    - **Notes:** Quality short lead for the helix/LNA feed and the bench. 086-6SM+ (USD 16.67, per the register) for internal jumpers.
  30.
    - **Item:** RTL-SDR Blog SMA pigtail adapter set (6 pcs); SMA straight adapter set (6 pcs); semi-rigid RG402 SMA adapter set (10 pcs)
    - **Seller:** RTL-SDR Blog official store
    - **Url:** https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
    - **Price:** USD 18.95 / USD 14.95 / USD 26.95
    - **Price usd:** 18.95
    - **In stock:** yes (Amazon USA and China warehouse)
    - **Ships to:** Worldwide from China; Amazon USA
    - **Official channel:** так
    - **Notes:** Covers the SMA/F/BNC adapters the chains need, such as BNC for the Boni-Whip and an F-SMA for the LNB IF (check the set contents). RTL-SDR Blog sells no coax: the kits ship with RG174.
  31.
    - **Item:** 3M 1170 aluminium foil tape with conductive adhesive, 1/4 in x 18 yd (horn gore seams)
    - **Seller:** DigiKey (3M 1170-1/4"X18YD)
    - **Url:** https://www.digikey.com/en/products/result?keywords=3M%201170%20aluminum%20foil%20tape
    - **Price:** USD 35.70 (1/2 in x 15 ft: USD 46.01)
    - **Price usd:** 35.70
    - **In stock:** yes, 196
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** A distributor-grade option. Hardware-store aluminium HVAC tape plus binder clips is the cheap route (seams cost 0.2-0.5 dB either way).
  32.
    - **Item:** Analog Devices EV1HMC7992LP3D evaluation board (HMC7992 SP4T 0.1-6 GHz), the official HMC7992 board
    - **Seller:** DigiKey (505-EV1HMC7992LP3D-ND)
    - **Url:** https://www.digikey.com/en/products/result?keywords=EV1HMC7992LP3D
    - **Price:** USD 319.28
    - **Price usd:** 319.28
    - **In stock:** yes, 2
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Too expensive for the extended sled. Farnell CH lists it at CHF 249.15 (search snippet). The bare HMC7992LP3DE chip is USD 13.10 at DigiKey, which suits a DIY board in the shielded sled.
  33.
    - **Item:** Generic 'HMC7992 non-reflective SP4T RF switch module 0.1-6 GHz' board
    - **Seller:** Walmart.ca marketplace seller 'Joystore'
    - **Url:** https://www.walmart.ca/en/ip/HMC7992-Non-Reflective-SP4T-RF-Switch-Module-PCB-Material-0-1-6GHz-Frequency-Range-3V-5V-Power-Supply-45dB-Isolation-0-6dB-Insertion-Loss-58dBm-IIP3/4LT6JIAL4ULJ
    - **Price:** CAD 20.49 (was CAD 25.27)
    - **Price usd:** 14.70
    - **In stock:** unknown (search snippet; page blocked by bot check)
    - **Ships to:** Canada (marketplace)
    - **Official channel:** ні
    - **Notes:** No official maker; quality and counterfeit-chip risk. The seller claims 45 dB isolation; expect 30-37 dB. Qualify it with the conducted P1/P13 procedure (40 dB or more below 1 GHz, 30 dB or more at 1.7-2.3 GHz) before use. Converted at about 0.72 USD/CAD.
  34.
    - **Item:** Mini-Circuits ZSWA4-63DR+ absorptive SP4T 1-6000 MHz
    - **Seller:** Mini-Circuits webstore
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=ZSWA4-63DR%2B
    - **Price:** USD 307.32 (qty 1-4)
    - **Price usd:** 307.32
    - **In stock:** NO, current stock 0 (DigiKey 0); contact sales
    - **Ships to:** International
    - **Official channel:** так
    - **Notes:** Premium switch (58 dB isolation per the register). Out of stock, so the extended sled stays on a qualified HMC7992 board or manual SMA swaps.
- **Not found:**
  1.
    - **Item:** RTL-SDR Blog official AliExpress store (no. 4523039) and official eBay (rtl-sdr-blog) prices for the V4L/LNA/filters
    - **Closest equivalent:** RTL-SDR Blog webstore at USD 37.95 / 19.95 / 16.95 / 17.95 / 29.95 / 59.95
    - **Note:** The AliExpress store page rendered empty. The official buy page confirms both channels exist and that Ukraine is reachable only via AliExpress. EU buyers must use eBay/AliExpress or a reseller (WiMo, Passion Radio, Technofix, AstroRadio, etc.).
  2.
    - **Item:** Generic SMA bias-tee injector 10 MHz-6 GHz (GPIO Labs on Tindie; Passion Radio BT4G)
    - **Closest equivalent:** DIY injector on Mini-Circuits TCBT-2R5G+ (USD 11.31, DigiKey) with a TPS2553 at 250-300 mA, or Mini-Circuits ZFBT-4R2GW+ (USD 111.57)
    - **Note:** Tindie returned 403 and Passion Radio a redirect loop. Generic boxes lose 3-7 dB at 100-200 MHz, so any bought unit must be VNA-checked (conducted) at 137/145/740/1700 MHz.
  3.
    - **Item:** Horn materials: 0.3 mm aluminium or 0.2 mm brass sheet (6 gores, largest about 19.7 x 13 cm), printed 40.2 mm collar, 127/180 mm rings
    - **Closest equivalent:** Local metal or hobby supplier: K&S 0.016 in (0.4 mm) aluminium sheets exist but the common 4x10 in size is too narrow; buy 200x300 mm or larger blanks
    - **Note:** Not sourced from an official international store. Budget USD 10-20 (estimate). Ace, True Value and Hemlock list K&S 4x10 in 0.016 in aluminium at about USD 2-2.6 (US only, search snippets).
  4.
    - **Item:** Helix/helicone materials: 2 mm (12 AWG) bare copper wire (about 1.5 m per 5-turn L helix plus about 1 m for the S helix), 18 cm x 1.5 mm Al disc, 8 petals of 0.3-0.5 mm Al (blanks at least 17 x 18 cm), PETG/ASA former, SMA panel jack
    - **Closest equivalent:** Local metal and electrical supplier, or electrician's 2.5 mm2 solid copper earth wire (stripped)
    - **Note:** DigiKey, Mouser and Farnell searches failed (no results or 503). Budget USD 20-35 (foldable study estimate). Build it rigid: the spring-helix idea is refuted.
  5.
    - **Item:** Tape-measure crossed Yagi parts: 25 mm steel tape (5 m or more), 20x20 mm square PVC/GRP tube (0.7 m, cut to 5 pieces of 16 cm or less), #8 (3.26 mm) or 1/8 in aluminium rod (about 2.5 m), Axotron v3 printed spools (free 3MF), hairpin match, two SMA/BNC feeds
    - **Closest equivalent:** Local hardware store; any 1 in-blade 25 ft tape measure
    - **Note:** No official world-shipping offer verified. Budget USD 25-40 (estimate). Tune receive-only; no VNA sweep into the antenna.
  6.
    - **Item:** Chip antennas
    - **Closest equivalent:** None needed
    - **Note:** Final picks use no chip antenna for satellite links (the Johanson 433 MHz chip at -4 dBi was rejected). The LC76G board brings its own active GNSS antenna.
  7.
    - **Item:** LMR-240-class jumpers and RG316/RG174 0.5-1 m SMA leads with ferrites
    - **Closest equivalent:** Mini-Circuits 086-24SM+ (USD 24.73), the RTL-SDR Blog dipole kit's 3 m RG174, RTL-SDR Blog pigtail set (USD 18.95)
    - **Note:** A DigiKey RG316 search returned only an out-of-stock Wi-Fi antenna. Ferrite clip-ons are not sourced here.
  8.
    - **Item:** Spare telescopic element pair for the dipole kit
    - **Closest equivalent:** A second RTL-SDR Blog dipole kit, USD 17.95
    - **Note:** No separate official listing seen.
  9.
    - **Item:** HF+ input selector relay (HF / VHF / 50 ohm, latching, DC-capable)
    - **Closest equivalent:** Part still TBD (a latching signal relay, measured on the LiteVNA conducted)
    - **Note:** Not in this group's list, but the AIS-on-HF+ default depends on it. Add it plus a BNC-SMA lead (USD 5-10) to the HF-chain BOM.
  10.
    - **Item:** Loop antennas (YouLoop, HF active loops, VHF loops) and H-field near-field probes
    - **Closest equivalent:** Excluded by the user's rule
    - **Note:** The RTL-SDR Blog store (USD 39.95) and AstroRadio (EUR 44.00) sell the YouLoop. It is deliberately NOT sourced.
- **Notes:** PICKS USED (latest study and verifier win): 3x RTL-SDR Blog V4L; Airspy HF+ Discovery; LimeSDR Micro M.2 2280 Basic, gated optional, plus the R44SF 5 cm riser, 2x MHF4L-SMA and the I-PEX tool only if kept; RTL-SDR Blog Wideband LNA V2; SAWbird+ GOES and SAWbird+ iO (cased); Flamingo+ FM as the single FM filter; TPS2553 injectors built on TCBT-2R5G+; 2x BLK-89-S+; Bullseye TCXO LNB bare or with gore horn; RTL-SDR Blog dipole kit as the V-dipole; tape Yagi, petal helicone and gore horn as DIY; RTL-SDR Blog active L-band patch plus a separate L1/L5 patch for GNSS-SDR; Tecsun AN-05 plus Balun One Nine v2 (HF only); Boni-Whip at 12.5 V; HMC7992 board or Mini-Circuits switch for the extended sled. Every price was seen on 18 Oct 2026. Rates: 1.16 USD/EUR, 1.34 USD/GBP, 0.72 USD/CAD.
  
  GROUP TOTAL (core, official channels, before shipping/VAT; Lime excluded): about USD 872. That is 3 V4L 113.85, HF+ 169, LNA V2 19.95, GOES+ 49.95, iO+ 49.95, Flamingo+ 24.95, Balun 26.95, Boni-Whip about 184 at WiMo, AN-05 14.49, dipole kit 17.95, L-band patch 59.95, Waveshare L1/L5 16.99, Bullseye 29.95, 2x BLK-89-S+ 40.52, 3x TCBT-2R5G+ 33.93, pigtail set 18.95. DIY Yagi, helicone and horn materials add about USD 55-95, for about USD 930-970. The SAWbird+ NOAA (USD 49.95, same Nooelec order) sits in the 137 chain but outside this list. Lime-if-kept adds USD 316 (249 + 18 shipping + 12 + 19 + 18.10).
  
  Shipping: one Nooelec order (GOES+, iO+, Flamingo+, Balun, plus NOAA+) exceeds USD 100, so worldwide shipping is free. RTL-SDR Blog ships free economy from China. ITEAD ships from EU/US/CN warehouses. Crowd Supply charges USD 18 worldwide.
  
  Clone risk: RTL-SDR HIGH (official store, eBay or AliExpress store 4523039 only; never 'V4'/'Pro'/blue cases). Airspy MEDIUM (airspy.com/purchase dealers only). Generic HMC7992 boards: quality and counterfeit risk, so qualify them conducted.
  
  Correction found: the vendor page says the LNA V2 draws 90 mA, not 80 mA or less.
  
  CONFLICT RESOLUTIONS (decision and reason):
  1. Lime: gated optional. Keep the refundable Crowd Supply store pre-order and decide on 31 Jan 2027 or on delivery. No core function depends on it, and its dependents (riser, MHF4, T7, CPU7, LIME NPU profiles, pads, REF IN, P5/P7/P14/P18) are tagged conditional. Reason: it ships 15 Dec 2026, has had no update since 17 Jun 2026, its driver is x86-validated only, and it adds only S-band and 56 Msps NPU IQ.
  2. Q6A: buy the 12 GB now (USD 189.99) and re-check Allnet stock. Reason: RAM cannot be added later, and the Lime and training options stay open.
  3. Pack: 4S1P P50B with a regulated 12 V into J21. Reason: it alone fits the 13.2 V LNB, the 12.5 V Boni-Whip LDO, AUX 12 V and the noise-source ENR.
  4. 12 V regulator: the D36V50F12 is provisional. A forced-PWM buck-boost rated 5 A or more replaces it if the terminated-floor spur A/B or the sealed-case current test fails. Reason: the choice depends on measurement.
  5. USB: freeze the Lime-agnostic map as written (blue = RTL-A, or the T7 with the Lime). The HF+ and injectors run from LAB 5 V. The Wi-Fi part is FCU760K (schematic label).
  6. Header: adopt the map as listed. The IMU uses USB-CDC through the RP2040 puck (gnss_imu final), with no BNO085 on I2C2. UART7 stays to be verified at bring-up.
  7. labd is the sole hardware owner and lock authority (rflab becomes a module). labrx owns the ring and recorder. labclassify runs inferd and fusiond. Reason: one owner prevents contention.
  8. LNB: 13.2 V ±0.2 V with true disconnect and a switch rated 20 V or more; no 18 V. One current limit at 1.5-2x the measured Bullseye draw. Reason: horizontal DATV is lost in every tier.
  9. LNA bias: every SAWbird+ runs from a TPS2553 at 250-300 mA. The V4L-tee threshold is amended to 90 mA or less, half the 180 mA tee rating, so the LNA V2 (90 mA per vendor) stays on the tee. Reason: the vendor figure, with the 2x margin kept.
  10. FM filter: Flamingo+ only (published 250 mA DC pass). Reason: the RTL-SDR Blog filter has no DC rating.
  11. librtlsdr: adopt only the noble 2.0.1 .so.2 rebuild (0204c9c + 65f0658).
  12. Display: 127.9 MHz field-mode clock, or 164.4-168.4 MHz if the panel accepts it. Reason: 128.7 MHz hits 1544.4 and 1415.7 MHz.
  13. PPS: out-of-tree pps-gpio on 6.18.2-4. Route B is dropped.
  14. INA228: on I2C0 with user-space i2c-dev, shunt in the pack lead.
  15. Antennas: the V-dipole is the LRPT default, the crossed Yagi defaults to the ultra-compact build, and all loops are struck. Small rigid pieces of 20-23 cm or less stay in the patch tier pending the user. Reason: the size rule is met.
  16. Strike every policy leftover (S11 antenna sweeps, decode-then-filter Inmarsat, VLF SID, Bluetooth and Artemis gaps, voice IQ, Set B, Iridium/CARTOSAT rows, H-probes, city list, wsjtx GUI/fldigi, bearing log). This sourcing list carries none of them.
  17. HF: Boni-Whip at 12.5 V. The 9:1 wire is HF only and LF goes to the whip. The selector relay is added to the BOM (part TBD). Confirmation of the loop removal remains a user question.
  18. Storage: the T7 only with the Lime; otherwise microSD V30/A2 or UFS A/B. Keep products by default and raw IQ only when pinned.
  19. CPU: adopt as written (A55 fallback, T2 on CPU4-6, CPU7 isolated only with the Lime).
  20. Roadmap: NPU Phase 0 in W1-2 (19 Oct-1 Nov 2026). The minimal labeller moves to P0b. HF-F and second-RTL profiles come before HF classes.
  21. Buy 3 V4L (USD 113.85, 455 in stock, R828S end of life). A 4th only for continuous ADS-B/AIS/sonde monitoring.
  22. Software: adopt the single venv-per-tool recipe and test it on the Q6A.
  23. Region: hold only the Bullseye and horn until the user is confirmed inside the QO-100 footprint. Buy the SAWbird+ iO now. Reason: Inmarsat-C EGC is broadcast in all four ocean regions (about ±75° latitude), and it lifts the Nooelec order over the free-shipping line. Stock risk: Technofix is already out of stock.
  24. Costs: the world prices above replace the estimates for this group. The extended, HF-chain and sled subtotals must be recomputed with these lines.
  25. P1b: report_research.json now exists. The summaries.md and minute-log errata blocks are still pending for the writer step.
  
  Sources (WebFetch/WebSearch, 18 Oct 2026): rtl-sdr.com buy page and product pages, itead.cc, airspy.com/purchase, astroradio.com, crowdsupply.com/lime-micro/limesdr-micro, adt.link/product/R44SF.html, nooelec.com, minicircuits.com, digikey.com, waveshare.com, sparkfun.com, wimo.com/es/18067, shop.technofix.uk. Moonraker and Walmart.ca figures come from search snippets only.

## sourcing:group1 (run `wf_b9cc0186-94e`)

- **Group:** COMPUTE + STORAGE + DISPLAY + HMI (Radxa Dragon Q6A 12 GB / 8 GB fallback, Radxa UFS 128 GB, heatsink and fan, Samsung T7 1 TB or microSD, Wisecoco 7in 2000-nit kit and 4D Systems fallback, HDMI/FPC cables, HMI RP2040, encoders, sealed keys, CH334F hub, flashing media)
- **Offers:**
  1.
    - **Item:** Radxa Dragon Q6A 12 GB (RS701-D12J0R44S32Y13W28, Wi-Fi 6/BT 5.4)
    - **Seller:** TinyTronics (Eindhoven, NL; Radxa reseller)
    - **Url:** https://www.tinytronics.nl/en/development-boards/single-board-computers/radxa-dragon-q6a-qcs6490-12gb
    - **Price:** EUR 148.00 incl. NL VAT / EUR 122.31 ex VAT
    - **Price usd:** 166.37 incl. VAT / 137.49 ex VAT
    - **In stock:** yes, 10+ pieces (18 Oct 2026)
    - **Ships to:** EU by DPD; outside the EU on request (contact form, DHL Express or own courier); UK private orders need EUR 170 ex VAT minimum
    - **Official channel:** так
    - **Notes:** New finding: cheapest in-stock 12 GB source, cheaper than Allnet. Ex-VAT price applies only if the seller exports without VAT. Run the burn-in inside the return window (decision #22).
  2.
    - **Item:** Radxa Dragon Q6A 12 GB (RS701-D12J0R44S32Y13W28, Wi-Fi 6/BT 5.4)
    - **Seller:** ALLNET China (official Radxa distributor)
    - **Url:** https://shop.allnetchina.cn/products/radxa-dragon-q6a
    - **Price:** USD 189.99
    - **Price usd:** 189.99
    - **In stock:** yes (Shopify available=true, 18 Oct 2026)
    - **Ships to:** Worldwide (the store country list covers most countries, all priced in USD)
    - **Official channel:** так
    - **Notes:** Answers the #75/#86 stock conflict: 12 GB is in stock. On the same page 8 GB is USD 159.99 (sold out) and 6 GB (Wi-Fi 5) is USD 149.99 (in stock). Shipping is added at checkout.
  3.
    - **Item:** Radxa Dragon Q6A 12 GB
    - **Seller:** Arace Tech (official Radxa store)
    - **Url:** https://arace.tech/products/radxa-dragon-q6a
    - **Price:** USD 169.00
    - **Price usd:** 169.00
    - **In stock:** no, sold out (all variants: 4 GB $95, 6 GB $115, 8 GB $139, 12 GB $169)
    - **Ships to:** Worldwide (multi-currency checkout)
    - **Official channel:** так
    - **Notes:** Cheapest list price, but not purchasable now.
  4.
    - **Item:** Radxa Dragon Q6A 12 GB (SKU E1037)
    - **Seller:** Ameridroid (US Radxa reseller; same listing is mirrored on sp-siliconpower.com)
    - **Url:** https://ameridroid.com/products/radxa-dragon-q6a
    - **Price:** USD 249.95
    - **Price usd:** 249.95
    - **In stock:** no, out of stock (6 GB $169.95, also out of stock)
    - **Ships to:** US (international shipping not verified)
    - **Official channel:** так
    - **Notes:** Most expensive of the official channels.
  5.
    - **Item:** Radxa Dragon Q6A 8 GB (fallback, only if the Lime is dropped before purchase)
    - **Seller:** TinyTronics (NL)
    - **Url:** https://www.tinytronics.nl/en/development-boards/single-board-computers/radxa-dragon-q6a-qcs6490-8gb
    - **Price:** EUR 121.00 incl. VAT / EUR 100.00 ex VAT
    - **Price usd:** 136.02 incl. VAT / 112.41 ex VAT
    - **In stock:** yes, 20+ pieces
    - **Ships to:** EU by DPD; outside the EU on request
    - **Official channel:** так
    - **Notes:** The 12 GB board at the same shop costs only EUR 27 more, which supports buying 12 GB (conflict #2).
  6.
    - **Item:** Radxa Dragon Q6A 8 GB
    - **Seller:** ALLNET China
    - **Url:** https://shop.allnetchina.cn/products/radxa-dragon-q6a
    - **Price:** USD 159.99
    - **Price usd:** 159.99
    - **In stock:** no, sold out
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** 
  7.
    - **Item:** Radxa UFS 3.1 Module 128 GB (RA022-B10J0U2)
    - **Seller:** ALLNET China
    - **Url:** https://shop.allnetchina.cn/products/high-performance-ufs-3-1-module
    - **Price:** USD 65.90
    - **Price usd:** 65.90
    - **In stock:** yes (the 64/256/512 GB modules are sold out)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** The only in-stock source at world price. Read the chip ID on arrival (0x01CE = Samsung, which is wanted).
  8.
    - **Item:** Radxa UFS 3.1 Module 128 GB (RA022-B10J0U2)
    - **Seller:** TinyTronics (NL)
    - **Url:** https://www.tinytronics.nl/en/data-storage/modules/radxa-ufs-module-128gb
    - **Price:** EUR 58.00 incl. VAT / EUR 47.93 ex VAT
    - **Price usd:** 65.20 incl. VAT / 53.88 ex VAT
    - **In stock:** no, not in stock (2-4 weeks)
    - **Ships to:** EU; outside the EU on request
    - **Official channel:** так
    - **Notes:** Could be combined with the TinyTronics 12 GB board order if the 2-4 week wait is acceptable.
  9.
    - **Item:** Radxa UFS 3.1 Module 128 GB (RA022-B10J0U2)
    - **Seller:** Arace Tech
    - **Url:** https://arace.tech/products/radxa-ufs-module
    - **Price:** USD 49.00
    - **Price usd:** 49.00
    - **In stock:** no, sold out
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** 
  10.
    - **Item:** Radxa UFS 3.1 Module 128 GB (SKU A0818)
    - **Seller:** Ameridroid (US)
    - **Url:** https://ameridroid.com/products/high-performance-ufs-3-1-module-128gb
    - **Price:** USD 89.95
    - **Price usd:** 89.95
    - **In stock:** yes
    - **Ships to:** US (international not verified)
    - **Official channel:** так
    - **Notes:** In stock, but $24 more than Allnet.
  11.
    - **Item:** Radxa Armor Case 7056A (AE036), heatsink case for the Q6A
    - **Seller:** Arace Tech
    - **Url:** https://arace.tech/products/radxa-armor-case-7056a
    - **Price:** USD 4.99
    - **Price usd:** 4.99
    - **In stock:** yes
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Allnet describes it as a passive (noiseless) case: top 70x56x15 mm. Active cooling is mandatory (#16), so add one 40 mm 5 V fan, switched at 60/50 C.
  12.
    - **Item:** Radxa Armor Case 7056A (AE036)
    - **Seller:** ALLNET China
    - **Url:** https://shop.allnetchina.cn/products/radxa-heatsink-7056a
    - **Price:** USD 9.90
    - **Price usd:** 9.90
    - **In stock:** yes
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Convenient to add to the Allnet board and UFS order.
  13.
    - **Item:** Noctua NF-A4x10 5V PWM 40x10 mm fan
    - **Seller:** The Pi Hut (UK)
    - **Url:** https://thepihut.com/products/noctua-nf-a4x10-5v-pwm-40x10mm-quiet-cooling-fan
    - **Price:** GBP 14.00 incl. UK VAT
    - **Price usd:** 18.65
    - **In stock:** yes
    - **Ships to:** UK and international
    - **Official channel:** ні
    - **Notes:** Authorized retailer, not Noctua's own store, which returned HTTP 429. It never stops on PWM (1000 rpm minimum), so on/off switch it through the AO3400 (#17).
  14.
    - **Item:** Sunon MF40100V2-1000U-A99 40x40x10 mm 5 V fan (0.094 A, 7 CFM, wire leads)
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=MF40100V2-1000U-A99
    - **Price:** USD 4.87
    - **Price usd:** 4.87
    - **In stock:** listed; the page did not clearly show stock for this exact part
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Cheapest named 40 mm 5 V fan.
  15.
    - **Item:** Adafruit 5V Square USB Fan - 4 cm (PID 6101)
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/6101
    - **Price:** USD 4.95
    - **Price usd:** 4.95
    - **In stock:** yes (in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** It has a USB plug; cut it and wire through the AO3400 switch.
  16.
    - **Item:** Samsung Portable SSD T7 1 TB (MU-PC1T0T/AM), only if the Lime is kept
    - **Seller:** Samsung US online store
    - **Url:** https://www.samsung.com/us/memory-storage/portable-ssd/portable-ssd-t7-usb-3-2-1tb-gray-sku-mu-pc1t0t-am/
    - **Price:** USD 274.99 (search-result snippet; page fetch blocked, HTTP 403)
    - **Price usd:** 274.99
    - **In stock:** unclear (the snippet shows an 'Out of stock' label that may refer to another capacity)
    - **Ships to:** US
    - **Official channel:** так
    - **Notes:** Not seen on a live page. Flash prices are high in Oct 2026: a Silicon Power 1 TB portable SSD lists at $245.97 on its own store.
  17.
    - **Item:** Samsung Portable SSD T7 1 TB Titan Gray (MU-PC1T0T/AM)
    - **Seller:** B&H Photo (US)
    - **Url:** https://www.bhphotovideo.com/c/product/1559836-REG/samsung_mu_pc1t0t_am_1tb_t7_portable_ssd.html
    - **Price:** USD 229.99 (search-result snippet; page fetch blocked)
    - **Price usd:** 229.99
    - **In stock:** in stock per the snippet
    - **Ships to:** US and international (B&H ships worldwide; not re-checked)
    - **Official channel:** ні
    - **Notes:** Large US retailer. Best Buy ($229.99, an old snapshot) and Newegg (third-party PlatinumMicro, $229.99) also appear in snippets. The /WW part number is the international SKU; buy the suffix for your region.
  18.
    - **Item:** microSD V30/A2 alternative to the T7: Silicon Power Superior 512 GB UHS-I U3 V30 A2 (SU512GBSTXDA2V20AC)
    - **Seller:** Ameridroid (US)
    - **Url:** https://ameridroid.com/products/silicon-power-512gb-superior-uhs-1u3-v30-a2-microsd-memory-card-with-adapter-not-compatible-with-switch-2
    - **Price:** USD 104.50
    - **Price usd:** 104.50
    - **In stock:** yes
    - **Ships to:** US (international not verified)
    - **Official channel:** ні
    - **Notes:** Of the official/reseller pages I checked, this is the only in-stock V30 A2 card. The 256 GB V30 A2 ($54.41) is out of stock. The 128 GB Superior is $32.63 in stock but is only A1. Q6A microSD was measured at 61 MB/s write; one forum card failed after 3-4 months, so use it only for products and snapshots, never for wideband.
  19.
    - **Item:** microSD alternative: Samsung PRO Plus 128 GB microSDXC A2 V30 (MB-MD128SA)
    - **Seller:** RS Components Austria
    - **Url:** https://at.rs-online.com/web/p/sd-karten/0566937
    - **Price:** EUR 33.58 ex VAT (search-result snippet; page blocked)
    - **Price usd:** 37.75
    - **In stock:** supply-shortage notice
    - **Ships to:** EU
    - **Official channel:** так
    - **Notes:** Coolblue DE lists EUR 59.90 incl. VAT ($67.33) and is sold out. NAND shortage: confirm the price live.
  20.
    - **Item:** Wisecoco 7in 1920x1080 LTPS IPS high-brightness panel with HDMI-in board and capacitive touch (store SKU id 4681)
    - **Seller:** Wisecoco (manufacturer's own store)
    - **Url:** https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
    - **Price:** USD 132.00 ex VAT (list price USD 135.00)
    - **Price usd:** 132.00
    - **In stock:** yes (schema.org InStock; Add to cart)
    - **Ships to:** North America, Europe, Australia and Asia by DHL/FedEx/UPS express (3-5 days), small parcel or air; shipping cost on request; payment by PayPal, T/T or Alibaba Trade Assurance
    - **Official channel:** так
    - **Notes:** The page still lists touch as I2C, gives no input voltage, says '2000+ cd/m2 typ' (2500 only in the title) and lists no package contents. Buy only after written answers on USB-HID VID:PID, bonding/AR, input V/I, the EDID and acceptance of a 127.9 MHz (51.7 Hz) mode (#74, #77). Pay by PayPal for buyer protection.
  21.
    - **Item:** 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000 (7in 1280x800, 1000 nits, bonded, GT928 capacitive touch over USB-C, 12 V)
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=4DHDMI-70-1280-800-CT-EAR-1000
    - **Price:** USD 128.95
    - **Price usd:** 128.95
    - **In stock:** yes, 13 in stock (manufacturer lead time 4 weeks)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** This fills the missing world price for the fallback (#76): about $100 less than the old UAH 9,520 (about $229) reference.
  22.
    - **Item:** 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000
    - **Seller:** 4D Systems (manufacturer's own store, Australia)
    - **Url:** https://4dsystems.com.au/products/4dhdmi-7-0
    - **Price:** USD 141.85
    - **Price usd:** 141.85
    - **In stock:** purchasable (Shopify available=true); 4D says only select models ship from stock and others may have MOQ and lead time
    - **Ships to:** Worldwide (country selector covers about 60 countries, all priced in USD)
    - **Official channel:** так
    - **Notes:** Ships with one USB cable and one HDMI cable. Choose the 'Display Tabs' variant to get the EAR mounting.
  23.
    - **Item:** Short HDMI cable: Adafruit Slim HDMI Cable 450 mm (PID 2420)
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/2420
    - **Price:** USD 9.95
    - **Price usd:** 9.95
    - **In stock:** yes (in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** The decision calls for a short shielded HDMI lead with ferrites; prefer this to an unshielded FPC. At The Pi Hut this length is discontinued (GBP 9.90); the 0.9 m is GBP 12.00 and out of stock.
  24.
    - **Item:** HDMI flat cable 30 cm (Adafruit PID 2197)
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/2197
    - **Price:** USD 3.95
    - **Price usd:** 3.95
    - **In stock:** yes (in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** The same item is GBP 3.40 ($4.53), in stock, at The Pi Hut (https://thepihut.com/products/hdmi-flat-cable-1-foot-30cm-long).
  25.
    - **Item:** DIY HDMI FPC kit: straight HDMI plug adapter (PID 3548) + 10 cm ribbon (PID 3560, $1.50) or 20 cm ribbon (PID 3561, $1.95); straight mini-HDMI plug adapter (PID 3552, $6.50) if the display board uses mini-HDMI
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/3548
    - **Price:** USD 6.50 per adapter + USD 1.50-1.95 per ribbon
    - **Price usd:** 14.50-14.95 per cable (2 adapters + 1 ribbon)
    - **In stock:** yes (all listed in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Only if case routing needs an FPC. The ribbon is unshielded, so wrap it in grounded copper tape and run the display on/off A/B test.
  26.
    - **Item:** Würth WE-STAR-TEC snap-on ferrite 74271140 (3.0 mm ID, 178 ohm at 100 MHz) for the touch, USB and display power leads
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=Wurth%20WE-STAR-TEC%20742711
    - **Price:** USD 3.91
    - **Price usd:** 3.91
    - **In stock:** yes, 541 in stock
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** A thicker HDMI lead needs a larger-ID clamp; size it to the cable you buy.
  27.
    - **Item:** HMI RP2040 board: Waveshare RP2040-Zero (no header, SKU 20187) / RP2040-Zero-M (pre-soldered header, SKU 20335)
    - **Seller:** Waveshare (manufacturer's own store)
    - **Url:** https://www.waveshare.com/rp2040-zero.htm
    - **Price:** USD 3.99 (no header) to USD 4.99 (with header)
    - **Price usd:** 3.99-4.99
    - **In stock:** both SKUs marked saleable; no stock count shown
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Buy 2 (HMI plus the spare that radio_lab lists for the IMU puck). The Pi Hut marks its RP2040-Zero listing 'Discontinued' (WAV-25506), so check Waveshare stock when ordering. Avoid unbranded AliExpress RP2040-Zero clones (flash and regulator vary).
  28.
    - **Item:** Raspberry Pi Pico RP2040 (SC0915 no headers / SC0917 with headers), fallback HMI MCU
    - **Seller:** The Pi Hut (Raspberry Pi Approved Reseller)
    - **Url:** https://thepihut.com/products/raspberry-pi-pico
    - **Price:** GBP 3.80 (no headers) / GBP 4.80 (with headers), incl. UK VAT
    - **Price usd:** 5.06 / 6.39
    - **In stock:** yes
    - **Ships to:** UK and international
    - **Official channel:** так
    - **Notes:** Larger (51x21 mm), same firmware. Adafruit PID 4864 ($4.00) is on backorder.
  29.
    - **Item:** Push-encoder (x2: tune, volume): Bourns PEC11R-4215F-S0024 (24 detents/24 PPR, push switch, 6 mm flatted shaft)
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=PEC11R-4215F-S0024
    - **Price:** USD 2.95 each (USD 2.376 at qty 10)
    - **Price usd:** 2.95
    - **In stock:** yes, 13,117 in stock
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** EC11-class part; chosen because the Alps EC11E15244G1 ($4.92) has 0 in stock (1,200 due 17 Dec 2026). Buy 3 (one spare).
  30.
    - **Item:** Main knob 35 mm for the tune encoder: Adafruit Scrubber Knob 35 mm (PID 2055)
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/2055
    - **Price:** USD 0.95
    - **Price usd:** 0.95
    - **In stock:** yes (in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Matches the 30-35 mm main knob spec. Check the fit on the 6 mm D shaft.
  31.
    - **Item:** Sealed keys (x6), premium: APEM IPR3SAD2 IP67 momentary panel pushbutton, black, SPST-NO 0.5 A/48 V, 13.6 mm cut-out
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/detail/apem-inc/IPR3SAD2/1280167
    - **Price:** USD 16.16 each
    - **Price usd:** 16.16 (six = 96.96)
    - **In stock:** yes, 5,079 in stock
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** A genuinely sealed panel key at about 12-14 mm with a defined click for gloves. Red IPR3SAD6 is $21.22 if a coloured REC key is wanted.
  32.
    - **Item:** Sealed keys (x6), budget: C&K KSC641J LFS IP67 sealed tact switch (6.2 mm SMT, 7.7 mm actuator, 340 gf) under printed caps of 12 mm or more and a case gasket
    - **Seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=KSC641J%20LFS
    - **Price:** USD 0.82 each (USD 0.70 at qty 10)
    - **Price usd:** 0.82 (ten = 7.00)
    - **In stock:** yes, 30,086 in stock
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** The switch is IP67; the 12 mm key and its seal come from the case design.
  33.
    - **Item:** Adafruit CH334F Mini 4-Port USB Hub Breakout (MTT), PID 5997
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/5997
    - **Price:** USD 4.95 (USD 4.46 at 10+)
    - **Price usd:** 4.95
    - **In stock:** yes (in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** The internal hub of the frozen USB map (#5/#129). Buy 2 (one spare).
  34.
    - **Item:** Adafruit CH334F Mini 4-Port USB Hub Breakout (ADA5997)
    - **Seller:** The Pi Hut (UK)
    - **Url:** https://thepihut.com/products/adafruit-ch334f-mini-4-port-usb-hub-breakout
    - **Price:** GBP 4.80 incl. UK VAT
    - **Price usd:** 6.39
    - **In stock:** yes
    - **Ships to:** UK and international
    - **Official channel:** так
    - **Notes:** Pimoroni lists it at GBP 4.15 but out of stock (its 2-port version is in stock).
  35.
    - **Item:** Flashing/rescue microSD: ALLNET 64 GB microSDXC UHS-I (ALN-TFUHS1-64)
    - **Seller:** ALLNET China
    - **Url:** https://shop.allnetchina.cn/products/allnet-micro-sd
    - **Price:** USD 16.99
    - **Price usd:** 16.99
    - **In stock:** yes
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** For the rescue image only (boot from SD with the UFS pulled). Speed class is not stated.
  36.
    - **Item:** Flashing/rescue microSD: Official Raspberry Pi A2-class microSD 64 GB (PID 6011)
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/6011
    - **Price:** USD 12.79
    - **Price usd:** 12.79
    - **In stock:** backorder
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Cheapest branded A2 card, but not shipping now.
  37.
    - **Item:** USB Type-C microSD card reader/writer (PID 5212)
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/5212
    - **Price:** USD 6.95
    - **Price usd:** 6.95
    - **In stock:** yes (in stock)
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** For writing the rescue and golden images on the home PC.
  38.
    - **Item:** USB-A to USB-C data cable 2 m (PID 6324) for EDL flashing (edl-ng / Armbian Imager) and SPI-NOR backup
    - **Seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/6324
    - **Price:** USD 2.95
    - **Price usd:** 2.95
    - **In stock:** yes, 93 in stock
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Use it only on the bench. Never connect USB-C while J21 is powered (Q5 back-feed).
  39.
    - **Item:** Radxa eMMC/UFS Module Reader (RA019, USB 3.0, UFS up to 1 TB)
    - **Seller:** ALLNET China
    - **Url:** https://shop.allnetchina.cn/products/emmc-ufs-module-reader-copy
    - **Price:** USD 12.99
    - **Price usd:** 12.99
    - **In stock:** no, sold out
    - **Ships to:** Worldwide
    - **Official channel:** так
    - **Notes:** Not required. Flash the UFS in place over EDL, or boot from microSD and dd to UFS (storage known fix). Arace's RA004 ($7.90, sold out) and Ameridroid's readers ($11.95/$12.95, in stock) are eMMC-only and do not fit UFS.
- **Not found:**
  1.
    - **Item:** OKdo listing for the Radxa Dragon Q6A
    - **Closest equivalent:** TinyTronics NL (EUR 148 for 12 GB, in stock) or ALLNET China ($189.99)
    - **Note:** okdo.com returned HTTP 503 on every fetch (product and search pages).
  2.
    - **Item:** Radxa official AliExpress store listing for the Q6A
    - **Closest equivalent:** ALLNET China / Arace own stores
    - **Note:** The AliExpress search showed only third-party listings at $197.79-344.99 with unclear RAM and copy-pasted RK3568/LPDDR4 text. Decision #22 says to avoid third-party AliExpress sellers (DDR-training dead boards), so none are recorded.
  3.
    - **Item:** Samsung T7 1 TB price seen on a live official page
    - **Closest equivalent:** Search-snippet prices: Samsung US $274.99, B&H $229.99, Best Buy $229.99, CDW $194.99 advertised
    - **Note:** Samsung, B&H, Best Buy, Newegg, CDW, Geizhals, PriceSpy and idealo returned 403/503; Amazon hides the price for bots ('add to cart to see price'). Purchase is deferred to the Lime gate anyway (#72, conflict 18).
  4.
    - **Item:** Wisecoco official AliExpress store listing for the 7in 1920x1080 2000-nit HDMI kit
    - **Closest equivalent:** wisecocodisplay.com own store at $132
    - **Note:** No AliExpress listing found. Search shows eBay listings from 'Wisecoco-official-store' with conflicting HDMI/MIPI and 2000-2400 nit specs; eBay returned 403.
  5.
    - **Item:** Radxa UFS reader in stock
    - **Closest equivalent:** EDL in-place flashing with the USB-A to C cable, or boot from microSD and write the UFS
    - **Note:** RA019 is sold out at Allnet. No other official seller lists a UFS-capable reader.
  6.
    - **Item:** Noctua NF-A4x10 5V price at Noctua's own store or Amazon
    - **Closest equivalent:** The Pi Hut GBP 14.00 (NF-A4x10 5V PWM, in stock)
    - **Note:** noctua.at returned HTTP 429; Amazon hides the price.
  7.
    - **Item:** Mouser, LCSC, TME and Farnell/Newark prices for the encoders, keys, ferrites and 4D display
    - **Closest equivalent:** DigiKey (product and search pages readable)
    - **Note:** Mouser, TME and Farnell/RS block bots (403/Cloudflare); LCSC search is rendered client-side and its API returned 403.
  8.
    - **Item:** In-stock Samsung PRO Plus / PRO Endurance microSD at an official channel
    - **Closest equivalent:** Silicon Power Superior 512 GB V30 A2 at Ameridroid ($104.50, in stock)
    - **Note:** Snippets show shortage or sold-out notices (RS AT EUR 33.58 ex VAT with a shortage notice; Coolblue EUR 59.90, sold out).
- **Notes:** FX: open.er-api.com, 18 Oct 2026 00:02 UTC: 1 EUR = 1.1241 USD, 1 GBP = 1.3318 USD. Every price is a live store read on 18 Oct 2026 (Shopify JSON, Adafruit API, schema.org data or WebFetch) unless the offer says 'search-result snippet'. 8 WebSearch calls were used. Catalog dumps and parsers are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/src_cmp/ and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/shop_grep.py.
  
  KEY FINDINGS
  1. Q6A 12 GB is in stock at two official channels:
  - TinyTronics: EUR 148 incl. VAT ($166.37), or EUR 122.31 ex VAT ($137.49) if exported VAT-free.
  - ALLNET China: $189.99, ships worldwide.
  Arace ($169) and Ameridroid ($249.95) are sold out. Decision #14's '$189.99 Allnet' is therefore no longer the cheapest source. The 8 GB board is only EUR 27 cheaper at TinyTronics, which strengthens the 12 GB choice.
  2. UFS 128 GB: ALLNET ($65.90) is the only in-stock world source. Arace ($49) is sold out; TinyTronics (EUR 58) has a 2-4 week wait.
  3. The 4D fallback now has a world price: DigiKey $128.95 (13 in stock), or $141.85 from the 4D store. This closes the 'UAH-only price' gap in #76 and requirement_compliance item 6.
  4. Wisecoco is $132 ex VAT and InStock on its own store. Shipping is quoted on request (DHL/FedEx/UPS to NA/EU/AU/Asia). The listing still says touch is I2C and gives no input voltage, so keep the written-confirmation gate.
  5. HMI parts are cheap and available:
  - Bourns PEC11R-4215F-S0024 at $2.95 (the Alps EC11E is out of stock until Dec 2026).
  - Sealed keys: C&K KSC641J IP67 at $0.82 each (budget), or APEM IPR3SAD2 IP67 panel keys at $16.16 each (premium).
  - CH334F: $4.95 at Adafruit.
  - RP2040-Zero: $3.99-4.99 at Waveshare.
  6. Flash prices are high in Oct 2026: T7 1 TB about $230-275 in snippets, Silicon Power 1 TB portable $245.97, Samsung PRO Plus 128 GB in shortage. This supports deferring the T7 to the Lime gate.
  
  SUGGESTED CORE BUY (cheapest in-stock official offers, before shipping and duties), about $440:
  - Q6A 12 GB, TinyTronics: $166.37 (Allnet $189.99 instead adds about $24).
  - UFS 128 GB, Allnet: $65.90.
  - Armor Case 7056A, Arace: $4.99.
  - Sunon 40 mm 5 V fan: $4.87.
  - Wisecoco kit: $132.00.
  - Slim HDMI 45 cm: $9.95, plus 2 ferrites at $3.91.
  - RP2040-Zero: $3.99.
  - 2x PEC11R: $5.90, plus a 35 mm knob at $0.95.
  - 6x KSC641J: $4.92.
  - CH334F: $4.95.
  - 64 GB rescue microSD: $16.99.
  - USB-C card reader: $6.95.
  - USB A-C cable: $2.95.
  Variants: APEM keys instead of KSC add about $92. The T7, if the Lime is kept, adds about $230-275. Buying from two shops (TinyTronics plus Allnet) doubles shipping; an all-Allnet order (board $189.99, UFS, case $9.90, microSD) is about $283 from one seller.
  
  AUTHENTICITY AND CLONE RISK: none of the clone-prone instruments (tinySA, LiteVNA, RTL-SDR, Airspy) are in this group. Risks here:
  - Third-party AliExpress Q6A listings: overpriced, wrong specs, RMA risk.
  - Unbranded RP2040-Zero clones.
  - Wisecoco listing inconsistencies: 2000 vs 2500 nits, I2C touch.
  - The T7 /AM vs /WW regional SKUs.
  
  CONFLICTS_FOR_FINAL_CHECKS (decision; reason):
  1. Lime: gated optional, decide on 31 Jan 2027 or on delivery; nothing in this group depends on it except the T7 (deferred).
  2. RAM: buy 12 GB now (TinyTronics EUR 148, or Allnet $189.99 for non-EU delivery); RAM cannot be added later. One budget: 4 GiB ring with the Lime, 1.5 GiB or less without it.
  3. Pack: 4S1P P50B with a regulated 12 V rail; fixes the LNB, Boni-Whip and J21 topologies.
  4. 12 V regulator: choose after the spur A/B and sealed-case current test; neither candidate is proven.
  5. USB map: freeze the Lime-agnostic map, using Adafruit CH334F #5997 (buy 2) for H1-H4.
  6. Header map: adopt the proposed map, with the HMI RP2040 on UART7 and a CH334F port as fallback; RP2040-Zero or Pico both fit.
  7. labd is the sole hardware owner; one lock authority prevents conflicts.
  8. LNB: 13.2 V ±0.2 V, true disconnect, no 18 V, one current limit at 1.5-2x the measured draw.
  9. LNA bias: TPS2553 at 250-300 mA for every SAWbird+; the V4L tee only for loads of 80 mA or less.
  10. FM filter: Flamingo+ FM (published 250 mA DC pass).
  11. librtlsdr: only the .so.2 rebuild of noble 2.0.1, which keeps the SONAME.
  12. Display: field mode at about 127.9 MHz; the Wisecoco purchase is gated on written acceptance of that mode plus the HID/bonding answers; 4D fallback at $128.95 DigiKey.
  13. PPS: out-of-tree pps-gpio on 6.18.2-4 (CONFIG_PPS=y); keeps the kernel hold.
  14. INA228: I2C0 with i2c-dev, shunt in the pack lead; no DT conflict.
  15. Antenna tiers: re-decide under the two-tier rule, strike loop leftovers (user rule).
  16. Policy leftovers: strike all before STACK.md (hard rules).
  17. HF chain: Boni-Whip at 12.5 V; meets both published supply ranges.
  18. Storage: T7 only with the Lime; otherwise UFS plus a V30/A2 microSD for products. Buy only the 64 GB rescue card now because of NAND prices.
  19. CPU: adopt the register allocation; it is the measured-plan default.
  20. Roadmaps: run NPU Phase 0 inside W1-2; aligns the gates.
  21. V4L: buy 3; 2 in service plus 1 spare.
  22. Software: one venv-per-tool recipe; avoids conflicting installs.
  23. Region unknown: prefer worldwide shippers (Allnet, Arace, DigiKey, Adafruit, 4D, Wisecoco); TinyTronics and Pi Hut are cheaper only for EU/UK buyers; duties are not included.
  24. Costs: this group is re-priced above at world prices.
  25. P1b completion: outside this group; write report_research.json errata before P2.

## sourcing:group3 (run `wf_b9cc0186-94e`)

- **Group:** POWER + GNSS/IMU + MECHANICAL (4S1P Molicel P50B pack, Daly 4S BMS, IP2368 charger, Pololu D36V50F12 / D36V28F5 / S18V20AHV / #2813, LT3045 LDOs, Adafruit INA228, TPS2553 switches, fuses/PTCs, XT30/DC jacks, Waveshare LC76G, Radxa RTC cell, BNO085 puck with RP2040-Zero, ASA shell, inserts, screws, gap pads, strap, 1/4-20 mount)
- **Offers:**
  1.
    - **Item:** Molicel INR21700-P50B 5000 mAh 21700 cell (buy 5: 4 for 4S1P + 1 spare)
    - **Seller:** 18650 Battery Store (US cell retailer)
    - **Url:** https://www.18650batterystore.com/products/molicel-21700-p50b-5000mah-50a-battery
    - **Price:** USD 9.99 (sale; regular 11.99)
    - **Price usd:** 9.99
    - **In stock:** yes (store product JSON available=true on 18 Oct 2026; an older search snippet said sold out)
    - **Ships to:** US (international shipping of loose cells not confirmed)
    - **Official channel:** ні
    - **Notes:** Established specialist cell retailer; Molicel has no retail store. Counterfeit/re-wrapped cell risk: test capacity (>=4.85 Ah), IR and weight (~68-70 g) before welding.
  2.
    - **Item:** Molicel INR21700-P50B 5000 mAh 21700 cell
    - **Seller:** Battery Junction (US)
    - **Url:** https://www.batteryjunction.com/molicel-inr21700-p50b
    - **Price:** USD 11.35
    - **Price usd:** 11.35
    - **In stock:** yes (store JSON available=true)
    - **Ships to:** US
    - **Official channel:** ні
    - **Notes:** Established US cell retailer; qty breaks from 10 pcs (not read).
  3.
    - **Item:** Molicel P50B 21700 5000 mAh, 2-pack
    - **Seller:** RaceDayQuads (US)
    - **Url:** https://www.racedayquads.com/products/molicel-p50b-21700-5000mah-60a-3-7v-li-ion-battery-2pcs
    - **Price:** USD 18.49 per 2 cells
    - **Price usd:** 9.25 per cell
    - **In stock:** yes (store JSON available=true)
    - **Ships to:** US
    - **Official channel:** ні
    - **Notes:** Cheapest in-stock per-cell price seen; buy 3 packs for 5 cells + 1 extra.
  4.
    - **Item:** Molicel 21700 P50B 5000 mAh
    - **Seller:** Kiwi Quads (New Zealand)
    - **Url:** https://kiwiquads.co.nz/product/molicel-21700-p50b-5000mah/
    - **Price:** NZD 22.99 (1-4 pcs; bulk tiers lower)
    - **Price usd:** 13.02
    - **In stock:** yes (page shows In stock, stock level 27)
    - **Ships to:** NZ
    - **Official channel:** ні
    - **Notes:** Oceania source.
  5.
    - **Item:** Molicel INR21700-P50B 5000 mAh
    - **Seller:** NKON (Netherlands, EU)
    - **Url:** https://www.nkon.nl/en/molicel-inr21700-p50b-5000mah-50a.html
    - **Price:** EUR 6.75 incl. VAT (EUR 5.58 ex VAT); EUR 5.79 at 10 pcs
    - **Price usd:** 7.60
    - **In stock:** unclear: store page returned 403 to me; seen only in search snippets, one of which carried a pre-order note
    - **Ships to:** EU
    - **Official channel:** ні
    - **Notes:** Cheapest EU source if in stock; verify on the live page. A cheaper 'reduced cycle' grade-B listing exists; do not use it.
  6.
    - **Item:** DALY 4S 15A Li-ion common-port balancing BMS (DL-J05G-L4S15ATJ)
    - **Seller:** TinyTronics (Eindhoven, NL)
    - **Url:** https://www.tinytronics.nl/en/power/bms-and-chargers/bms/daly-bms-li-ion-li-po-protection-circuit-4s-15a-with-balancing
    - **Price:** EUR 8.00 incl. VAT (EUR 6.61 ex)
    - **Price usd:** 9.00
    - **In stock:** yes (9 pcs)
    - **Ships to:** NL/EU (delivery page not read)
    - **Official channel:** ні
    - **Notes:** Li-ion thresholds: OV 4.25 V, UV 2.70 V, 15 A continuous, OCP 40 A, charge protection 10 A, passive balancing 30 mA from 4.18 V (so it balances only during the monthly 4.20 V charge; the daily 4.10 V charge never triggers it). 61x35x9 mm, 35 g. Test BMS wake by charger 3 out of 3 times.
  7.
    - **Item:** IP2368 100 W 4S bidirectional USB-C PD charge board (generic, unbranded)
    - **Seller:** Newegg marketplace, third-party seller shipping from China
    - **Url:** https://www.newegg.com/p/3C6-00RD-001C4
    - **Price:** USD 15.79 (search snippet; the page itself returned 403)
    - **Price usd:** 15.79
    - **In stock:** unknown
    - **Ships to:** US (ships from China)
    - **Official channel:** ні
    - **Notes:** Only marketplace listings exist (Newegg USD 15.79-23.98 CAD, Walmart 2-pack USD 19.94, OnBuy RON 83.27; snippet range USD 12.50-24.59). All of them are bidirectional COUT/NACT boards; I found no charge-only BZ board. Quality varies: buy 2-3, set RISET 15k (3 A) and RVSET 5.1k (4.10 V/cell), fit a real 10k B3380 NTC, burn in for 2 h.
  8.
    - **Item:** Injoinic IP2368_I2C_COUT chip (for a self-built charger board)
    - **Seller:** LCSC (C5372184)
    - **Url:** https://www.lcsc.com/product-detail/C5372184.html
    - **Price:** USD 2.17 (1 pc)
    - **Price usd:** 2.17
    - **In stock:** no (0)
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** Reference price for the chip only; the board route above is the practical one.
  9.
    - **Item:** Pololu 12V 4.5A Step-Down Voltage Regulator D36V50F12 (#4095), 12 V into Q6A J21
    - **Seller:** Pololu (manufacturer store)
    - **Url:** https://www.pololu.com/product/4095
    - **Price:** USD 39.95 (USD 36.75 each at 5+)
    - **Price usd:** 39.95
    - **In stock:** rationed (Active and Preferred), backorders allowed
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** 13.3-50 V in, 12 V +-4%, 4.5 A typical (2.3-6.5 A depending on conditions). Not forced-PWM. Set the EN hardware cut at 13.4 V or more, because it drops out below 13.3 V.
  10.
    - **Item:** Pololu 5V 3.2A Step-Down Voltage Regulator D36V28F5 (#3782), LAB 5 V rail
    - **Seller:** Pololu (manufacturer store)
    - **Url:** https://www.pololu.com/product/3782
    - **Price:** USD 23.95 (USD 22.03 at 5+)
    - **Price usd:** 23.95
    - **In stock:** rationed, backorders allowed
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** 5.3-50 V in, 3.2 A typical, about 500 kHz at heavy load, 17.8x20.3x8.8 mm. Has a light-load power-save mode, so include it in the spur A/B test.
  11.
    - **Item:** Pololu Adjustable 9-30V Step-Up/Step-Down Regulator S18V20AHV (#2573), LNB 13.2 V feed
    - **Seller:** Pololu (manufacturer store)
    - **Url:** https://www.pololu.com/product/2573
    - **Price:** USD 36.49 (USD 33.57 at 5+)
    - **Price usd:** 36.49
    - **In stock:** rationed, backorders allowed
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** 3-30 V in, 2 A typical. A buck-boost is needed because 4S swings 12-16.8 V across the 13.2 V target. Pololu states the SEPIC output is NOT fully disconnected when EN is low, so it needs a separate 40 V-rated switch (a second #2813) for a true 0 V off state.
  12.
    - **Item:** Pololu Big Pushbutton Power Switch with Reverse Voltage Protection, HP (#2813): master switch, plus a second one as the LNB switch
    - **Seller:** Pololu (manufacturer store)
    - **Url:** https://www.pololu.com/product/2813
    - **Price:** USD 8.95 (USD 8.23 at 5+)
    - **Price usd:** 8.95
    - **In stock:** rationed, backorders allowed
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** 4.5-40 V (32 V recommended), 6.0 A continuous at 55 C, <0.2 uA off, reverse protection. Buy 2 (master and LNB) plus 1 spare.
  13.
    - **Item:** Adafruit INA228 85V 20-bit power monitor (#5832), fuel gauge with its shunt in the pack lead
    - **Seller:** Adafruit (manufacturer store)
    - **Url:** https://www.adafruit.com/product/5832
    - **Price:** USD 14.95 (USD 13.46 at 10+)
    - **Price usd:** 14.95
    - **In stock:** yes
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** 15 mOhm 0.1% shunt, up to 10 A, 85 V. Remove the breakout pull-ups, power it from an always-on 3.3 V LDO, and read it on I2C0 through user-space i2c-dev.
  14.
    - **Item:** Analog Devices LT3045EMSE#PBF ultra-low-noise LDO (buy 2: 5 V LNA rail and 12.5 V Boni-Whip rail)
    - **Seller:** LCSC (C580012)
    - **Url:** https://www.lcsc.com/product-detail/voltage-regulators-linear-low-drop-out-ldo-regulators_analog-devices-lt3045emse-pbf_C580012.html
    - **Price:** USD 8.33 (1 pc), 7.27 (10 pcs)
    - **Price usd:** 8.33
    - **In stock:** yes (1,603)
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** 1.8-20 V in, 500 mA, 260 mV dropout, so 12.5 V out works down to the 13.6 V pack cutoff. LCSC is not an ADI-franchised distributor (moderate counterfeit risk); ADI, Mouser and DigiKey pages blocked my fetch. No ready LT3045 module found at an official store; it needs a small carrier PCB.
  15.
    - **Item:** TI TPS2553DBVR adjustable current-limited load switch (buy 4: 3 for SAWbird+ at 250-300 mA, 1 for the LAB port at about 1 A)
    - **Seller:** LCSC (C55266)
    - **Url:** https://www.lcsc.com/product-detail/C55266.html
    - **Price:** USD 0.5455 (1), 0.4515 (10)
    - **Price usd:** 0.55
    - **In stock:** yes (51,688)
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** 2.5-6.5 V, so it suits 5 V rails only (never the LNB or AUX 12 V). Choose the plain DBVR (constant-current, auto-recover), not the -1 latch-off variant. No ready carrier board found: use a SOT-23-6 breakout. LCSC also lists TPS2553DDBVR (C521201) at USD 0.19 with 11,035 in stock; I did not check its datasheet.
  16.
    - **Item:** TI TPS2553DBVR
    - **Seller:** Texas Instruments store
    - **Url:** https://www.ti.com/product/TPS2553/part-details/TPS2553DBVR
    - **Price:** USD 0.358 (TI listed price, volume tier)
    - **Price usd:** 0.36
    - **In stock:** no (schema.org OutOfStock on TI.com)
    - **Ships to:** worldwide (TI store)
    - **Official channel:** так
    - **Notes:** Manufacturer channel, out of stock on 18 Oct 2026.
  17.
    - **Item:** Littelfuse 029707.5WXNV MINI blade fuse 7.5 A 32 VDC (pack fuse if the Lime is kept)
    - **Seller:** LCSC (C178942)
    - **Url:** https://www.lcsc.com/product-detail/C178942.html
    - **Price:** USD 0.101 each (MOQ 5)
    - **Price usd:** 0.10
    - **In stock:** yes (7,500)
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** Buy alongside the 5 A part; it costs cents.
  18.
    - **Item:** Littelfuse 0297005.WXNV MINI blade fuse 5 A (pack fuse for the no-Lime 4S build)
    - **Seller:** LCSC (C151093)
    - **Url:** https://www.lcsc.com/product-detail/C151093.html
    - **Price:** USD 0.1326 each (MOQ 5)
    - **Price usd:** 0.13
    - **In stock:** yes (15,390)
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** Same family. The 2 A LAB 5 V fuse (0297002.WXNV) was not price-checked.
  19.
    - **Item:** Littelfuse 0FHM0001ZXJ inline MINI blade fuse holder, splash-proof
    - **Seller:** LCSC (C427665)
    - **Url:** https://www.lcsc.com/product-detail/C427665.html
    - **Price:** USD 3.51 (1), 3.04 (10)
    - **Price usd:** 3.51
    - **In stock:** yes (14 only)
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** Low stock: order early, or buy 2.
  20.
    - **Item:** Bourns MF-R075 PTC resettable fuse, 0.75 A hold, 60 V (AUX 12 V branch)
    - **Seller:** LCSC (C208478)
    - **Url:** https://www.lcsc.com/product-detail/C208478.html
    - **Price:** USD 0.178 each (MOQ 5)
    - **Price usd:** 0.18
    - **In stock:** yes (3,955)
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** Matches the 0.75 A-hold AUX PTC; the 0.5 A value was rejected for nuisance trips. The LNB polyfuse value waits for the measured Bullseye current (1.5-2x); other MF-R values are on the same page family.
  21.
    - **Item:** Amass XT30U-F female connector (pack and spare-pack lead; XT30U-M male not price-checked)
    - **Seller:** LCSC (C99102)
    - **Url:** https://www.lcsc.com/product-detail/C99102.html
    - **Price:** USD 0.207 each (MOQ 5)
    - **Price usd:** 0.21
    - **In stock:** yes (42,545)
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** Genuine Amass part (manufacturer listed). Clone XT30s are common on marketplaces.
  22.
    - **Item:** XKB DC-022B-2.0 panel-mount DC jack, 5.5x2.0 mm, 2 A, 30 V (AUX 12 V and Boni-Whip injector outlets)
    - **Seller:** LCSC (C319097)
    - **Url:** https://www.lcsc.com/product-detail/C319097.html
    - **Price:** USD 0.41 (1), 0.32 (10)
    - **Price usd:** 0.41
    - **In stock:** yes (2,421)
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** If 5.5x2.5 mm (DC5525) leads are kept, the DC-022B-2.5 (C319096) is out of stock. Key or colour-code each outlet so that 12 V AUX and 12.5 V whip cannot be swapped.
  23.
    - **Item:** Adafruit Panel Mount 2.1mm DC barrel jack (#610)
    - **Seller:** Adafruit (manufacturer store)
    - **Url:** https://www.adafruit.com/product/610
    - **Price:** USD 2.95
    - **Price usd:** 2.95
    - **In stock:** no (out of stock)
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** Alternative to the LCSC jack when back in stock.
  24.
    - **Item:** MYOUNG BH-21700-A5BJ001 single 21700 holder, THT (bench and test fixture only)
    - **Seller:** LCSC (C20606809)
    - **Url:** https://www.lcsc.com/product-detail/C20606809.html
    - **Price:** USD 1.65 (1), 1.38 (10)
    - **Price usd:** 1.65
    - **In stock:** yes (278)
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** Use it for capacity/IR testing before welding. The field pack is spot-welded with nickel strip (2 rows of 2 cells, end to end), because spring contacts cause brown-outs at about 4 A peaks. The SMD version BH-21700-B1BJ001 (C20606791) costs USD 0.91, 1,846 in stock.
  25.
    - **Item:** Waveshare LC76G Multi-GNSS Module (SKU 24370), on UART6 with PPS on pin 7
    - **Seller:** Waveshare (manufacturer store)
    - **Url:** https://www.waveshare.com/lc76g-gnss-module.htm
    - **Price:** USD 14.99 (13.63 at the 4+ tier)
    - **Price usd:** 14.99
    - **In stock:** unknown (page shows Add to Cart, no stock text)
    - **Ships to:** worldwide except Iran and Russia (Waveshare restriction)
    - **Official channel:** так
    - **Notes:** Includes an active ceramic antenna, an MX1.25 8-pin cable and an onboard MS621FE rechargeable backup cell, so no separate GNSS backup cell is needed. GPS/BDS/GLONASS/Galileo/QZSS, 1PPS, UART at 115200 baud by default. Use UART only.
  26.
    - **Item:** RTC Battery for RADXA SBC (CR2032-type cell on a lead for the Q6A RTC header)
    - **Seller:** Allnet China (official Radxa distributor)
    - **Url:** https://shop.allnetchina.cn/products/rtc-battery-for-radxa-sbc
    - **Price:** USD 0.95
    - **Price usd:** 0.95
    - **In stock:** yes
    - **Ships to:** worldwide (Allnet)
    - **Official channel:** так
    - **Notes:** The listing does not name the Q6A or the connector. Confirm the 2-pin 1.25 mm plug against Q6A schematic sheet 18 before relying on it. It is the time anchor for the location/spoofing gate (rtcsync).
  27.
    - **Item:** Adafruit 9-DOF Orientation IMU Fusion Breakout BNO085 (#4754), boom puck
    - **Seller:** Adafruit (manufacturer store)
    - **Url:** https://www.adafruit.com/product/4754
    - **Price:** USD 29.50 (26.55 at 10+)
    - **Price usd:** 29.50
    - **In stock:** yes
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** Genuine CEVA part. Avoid unbranded GY-BNO085 clones (marketplace clone risk).
  28.
    - **Item:** SparkFun VR IMU Breakout BNO086 Qwiic (SEN-22857), alternative puck IMU
    - **Seller:** SparkFun (manufacturer store)
    - **Url:** https://www.sparkfun.com/sparkfun-vr-imu-breakout-bno086-qwiic.html
    - **Price:** USD 34.95
    - **Price usd:** 34.95
    - **In stock:** yes
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** Rotation vector 2.0 deg static, 3.5 deg dynamic. 25.4x30.5 mm, 3 g.
  29.
    - **Item:** Waveshare RP2040-Zero (puck MCU, USB-CDC bridge for the BNO085)
    - **Seller:** Waveshare (manufacturer store)
    - **Url:** https://www.waveshare.com/rp2040-zero.htm
    - **Price:** USD 3.99-4.99 (without / with pre-soldered header)
    - **Price usd:** 3.99-4.99
    - **In stock:** unknown (not shown)
    - **Ships to:** worldwide except Iran and Russia
    - **Official channel:** так
    - **Notes:** Its 12 MHz clock has harmonics at 144.000 and 432.000 MHz: run the on/off noise-floor A/B at 137/145/435 MHz and keep the puck 15-20 cm or more from the LNAs.
  30.
    - **Item:** Polymaker ASA 1.75 mm, Grey, 1 kg (light-grey ASA shell, sun hood, clamps)
    - **Seller:** Polymaker US store (manufacturer)
    - **Url:** https://us.polymaker.com/products/asa
    - **Price:** USD 26.99 (Grey 1 kg); USD 25.99 White 1 kg
    - **Price usd:** 26.99
    - **In stock:** yes (product listed available)
    - **Ships to:** US store (Polymaker runs regional stores)
    - **Official channel:** так
    - **Notes:** One spool covers the about 0.4 kg shell plus the printed sun hood. Do not use PETG.
  31.
    - **Item:** Prusament ASA Signal White 800 g
    - **Seller:** Prusa Research (manufacturer store)
    - **Url:** https://www.prusa3d.com/category/prusament-asa/
    - **Price:** USD 25.92 (price shown for US shipping)
    - **Price usd:** 25.92
    - **In stock:** yes
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** No grey Prusament ASA is listed. White is equally good for sun load; a light colour is the requirement.
  32.
    - **Item:** CNC Kitchen Heat Set Insert M2.5 x 4 mm, 100 pcs
    - **Seller:** CNC Kitchen (manufacturer store, DE)
    - **Url:** https://cnckitchen.store/products/gewindeeinsatz-threaded-insert-m2-5-standard-100-stk-pcs
    - **Price:** EUR 9.90
    - **Price usd:** 11.14
    - **In stock:** yes
    - **Ships to:** EU and international (DE store; rates not read)
    - **Official channel:** так
    - **Notes:** M2.5 for board/standoff bosses. Brass is non-magnetic, so it is fine near the IMU.
  33.
    - **Item:** CNC Kitchen Heat Set Insert M3 x 5.7, 100 pcs
    - **Seller:** CNC Kitchen (manufacturer store, DE)
    - **Url:** https://cnckitchen.store/products/heat-set-insert-m3-x-5-7-100-pieces
    - **Price:** EUR 9.40
    - **Price usd:** 10.58
    - **In stock:** yes
    - **Ships to:** EU and international
    - **Official channel:** так
    - **Notes:** Shell closure screws.
  34.
    - **Item:** CNC Kitchen Heat Set Insert 1/4"-20 x 12.7 (camera thread), 20 pcs
    - **Seller:** CNC Kitchen (manufacturer store, DE)
    - **Url:** https://cnckitchen.store/products/heat-set-insert-1-4-20x12-7-camera-thread-20-pieces
    - **Price:** EUR 9.90
    - **Price usd:** 11.14
    - **In stock:** yes
    - **Ships to:** EU and international
    - **Official channel:** так
    - **Notes:** Use only on the IMU puck and accessories. For the 1.2-1.4 kg handheld, the tripod/boom mount must be a captured 1/4-20 nut or a thread tapped in the 2 mm aluminium mid-plate (an insert alone is not allowed).
  35.
    - **Item:** CNC Kitchen M2.5 Screw TX8 stainless steel low-profile, 25 pcs (M2.5x6; other lengths EUR 5.08-7.50)
    - **Seller:** CNC Kitchen (manufacturer store, DE)
    - **Url:** https://cnckitchen.store/products/m2-5-screw-stainless-steel-aisi-304-low-head
    - **Price:** EUR 6.00 (M2.5x6)
    - **Price usd:** 6.75
    - **In stock:** yes
    - **Ships to:** EU and international
    - **Official channel:** так
    - **Notes:** For the main chassis. An M2.5 assortment set costs EUR 31.90.
  36.
    - **Item:** CNC Kitchen Copper Hex Socket Cap Screw M2.5x12, 10 pcs (non-magnetic, IMU puck)
    - **Seller:** CNC Kitchen (manufacturer store, DE)
    - **Url:** https://cnckitchen.store/products/m2-5x12-copper-hex-socket-cap-screw-10pcs
    - **Price:** EUR 5.70
    - **Price usd:** 6.41
    - **In stock:** yes
    - **Ships to:** EU and international
    - **Official channel:** так
    - **Notes:** Meets the brass/nylon/non-ferrous screw rule within 15-20 cm of the BNO085.
  37.
    - **Item:** Gelid GP-Extreme 12 W/mK thermal pad 80x40x2.0 mm (TP-GP01-D)
    - **Seller:** QuietPC (NL)
    - **Url:** https://quietpc.co.nl/gelid-gp-pads
    - **Price:** EUR 4.98 (was 8.01)
    - **Price usd:** 5.60
    - **In stock:** yes (61)
    - **Ships to:** about 100 countries selectable (rates not read)
    - **Official channel:** ні
    - **Notes:** Above the 6 W/mK minimum. For the IP2368 board to the case, the UFS module to its boss, and the Lime pedestal if kept. The 3.0 mm (TP-GP01-E) costs EUR 6.64 (13 in stock). The GP-Ultimate 1.0 mm 90x50 costs EUR 4.14 (stock not shown) for the 0.5-1.5 mm gaps.
  38.
    - **Item:** Peak Design Leash camera strap with anchor links (handheld strap)
    - **Seller:** Peak Design (manufacturer store)
    - **Url:** https://www.peakdesign.com/products/leash
    - **Price:** USD 49.95
    - **Price usd:** 49.95
    - **In stock:** unknown (Add to cart shown)
    - **Ships to:** US store shown (international not stated)
    - **Official channel:** так
    - **Notes:** Quick-release anchors fit the 2 strap points on the shell. Any rated camera strap works; this is the only official-store strap price I saw.
- **Not found:**
  1.
    - **Item:** IP2368 charge-only (BZ) board from an official or branded store
    - **Closest equivalent:** Generic bidirectional IP2368 4S 100 W boards on Newegg/Walmart/OnBuy marketplaces, USD 12.50-24.59 (search snippets; pages returned 403/captcha)
    - **Note:** There is no manufacturer store. Charge from output-only PD ports or a USB-A-to-C lead, or test the power bank. Buy 2-3 boards and burn them in.
  2.
    - **Item:** Forced-PWM 12 V buck-boost rated 5 A or more (alternative to the D36V50F12)
    - **Closest equivalent:** Pololu D36V50F12 (#4095, USD 39.95)
    - **Note:** Pololu's step-up/step-down regulators top out at 2.5-3 A (S13V30F5, S13V25Fx), and none is a 12 V 5 A part. The D36V50F12 stays unless the terminated-floor spur A/B fails.
  3.
    - **Item:** Ready LT3045 low-noise LDO module from an official store
    - **Closest equivalent:** LT3045EMSE#PBF chip, LCSC C580012, USD 8.33
    - **Note:** analog.com (503), Mouser and DigiKey (403) blocked the fetch, so the ADI eval-board price was not seen. Generic AliExpress LT3045 modules were not checked.
  4.
    - **Item:** TPS2553 carrier/breakout board
    - **Closest equivalent:** TPS2553DBVR chip, LCSC C55266, USD 0.55, on a SOT-23-6 adapter
    - **Note:** No ready module found.
  5.
    - **Item:** Captured 1/4"-20 stainless hex nut (tripod/boom mount)
    - **Closest equivalent:** Any 18-8 stainless 1/4"-20 hex nut from a hardware store, or a thread tapped in the aluminium plate
    - **Note:** Bolt Depot returned 403. The CNC Kitchen 1/4"-20 insert is for the puck and accessories only.
  6.
    - **Item:** 2 mm aluminium mid-plate, copper-clad FR4 RF bay, IR-reflective film
    - **Closest equivalent:** Laser-cut sheet service (quote-based), generic FR4 sheet
    - **Note:** Not price-checked. The earlier estimate was USD 15-25 for plate and pads and USD 5 for FR4 (unverified).
  7.
    - **Item:** Sun hood
    - **Closest equivalent:** Printed from the same ASA spool (25-35 mm slide-on hood)
    - **Note:** No purchase needed.
  8.
    - **Item:** SMBJ14A TVS (after the 12 V regulator), 10k B3380 NTC, KSD9700 70 C bimetal switch, 2 A LAB fuse, XT30U-M, nickel strip
    - **Closest equivalent:** Standard LCSC/Mouser stock lines (the same LCSC order as above)
    - **Note:** Not price-checked within the search budget; each costs cents to about USD 1.
  9.
    - **Item:** Separate GNSS backup cell
    - **Closest equivalent:** Onboard MS621FE on the Waveshare LC76G
    - **Note:** Included, so no purchase.
  10.
    - **Item:** ISDT 608PD backup/monthly balance charger (optional)
    - **Closest equivalent:** Previous reference 1,979-2,250 UAH (about USD 47-54), Ukrainian price only
    - **Note:** World price not checked.
  11.
    - **Item:** 3S budget pack parts (3S BMS, INA226)
    - **Closest equivalent:** n/a
    - **Note:** Not sourced, because 4S is the decision (see conflict 3).
- **Notes:** FX: ECB reference rate of 16 Oct 2026. 1 EUR = 1.1253 USD; 1 GBP = 1.3335 USD; 1 NZD = 0.5664 USD. LCSC prices are in USD at the first ladder step (some have MOQ 5). Prices exclude shipping, VAT and duty.
  
  SUBTOTAL for this group (4S build, buying the cheapest in-stock official or established offer):
  - Power: about USD 254. This covers 5x P50B at 9.99, the Daly BMS at 9.00, 2 IP2368 boards at about 17, the D36V50F12, D36V28F5 and S18V20AHV, 2x #2813, the INA228, 2x LT3045, 4x TPS2553, both fuse values, the holder, the PTC, XT30s, the jack and the RTC cell.
  - GNSS/IMU: about USD 49.5 (LC76G, Adafruit BNO085, RP2040-Zero).
  - Mechanical: about USD 123 (ASA, M2.5 and 1/4-20 inserts, screws, copper screws, 2 Gelid pads, Peak Design strap).
  - Total about USD 426, or about USD 376 without the USD 49.95 strap.
  Shipping caveat: loose Li-ion cells mostly ship by ground and domestically only. A buyer outside the US/EU/NZ should buy the P50Bs from an established cell retailer in their own country and verify capacity, IR and weight.
  
  CLONE/QUALITY RISK:
  - P50B: re-wrapped fakes exist, so test every cell.
  - BNO085: buy Adafruit or SparkFun, not GY-BNO085 clones.
  - IP2368: board quality varies, so burn in 2-3 boards.
  - LCSC is not franchised for TI/ADI: moderate risk for the LT3045.
  - XT30: buy genuine Amass.
  - Pololu items show 'Rationed': quantity is limited per order, and backorders are allowed.
  
  Rule check: nothing in this group transmits or uses a loop. The H-field probe and AS3935 exclusions do not touch it.
  
  RESOLUTION OF ALL 25 conflicts_for_final_checks:
  1. LimeSDR Micro: gated optional. Keep the cancellable pre-order and decide on 31 Jan 2027 or on delivery; no core function depends on it. Reason: it does not ship before Dec 2026 and its power and heat are unmeasured, while the core targets are covered by the V4Ls and the HF+. Power parts here are sized so that nothing has to be re-bought if it stays: BMS 15 A, the 7.5 A fuse costs cents, and the #2813 is rated 6 A.
  2. RAM: buy the 12 GB Q6A now. RAM cannot be upgraded, and it keeps training and the Lime open. Re-check Allnet stock on the order date.
  3. Pack: 4S1P P50B (72 Wh), closed. Reason: the LNB at 13.2 V, the Boni-Whip at 12.5 V through an LDO, AUX 12 V and the 12 V display all need a source above 12 V, and 3S would need extra boost stages. Buy 5 cells and the Daly 4S 15 A BMS.
     - Fuse: 5 A now (no-Lime peak 24-32 W is about 2.4-2.7 A at 12-13.6 V; charging at 3 A), and 7.5 A only if the Lime is kept (about 4 A peak).
     - Thresholds: Linux poweroff at 13.6 V; D36V50F12 EN cut at 13.4 V or more; BMS 2.70 V/cell (Daly) as last resort.
  4. 12 V regulator: buy the D36V50F12 now. It is available, rated 4.5 A, and its EN pin gives the hardware cut. No forced-PWM 12 V buck-boost of 5 A or more exists in the official channels checked. Replace it only if the terminated-floor spur A/B or the sealed-case current test at 13.6 V input fails.
  5. USB map: freeze the Lime-agnostic map. Blue USB 3.1 port: RTL-A (or the T7 only with the Lime). FE1.1s P1 RTL-B, P2 touch, P3 CH334F (H1 HMI RP2040, H2 IMU puck, H3 LAB USB-A, H4 HF+). The HF+ and injectors run from LAB 5 V (D36V28F5). Reason: the same map works in both Lime cases and keeps load off VCC_5V_PERI (about 17 W).
  6. 40-pin map: freeze it.
     - Pins: PPS pin 7 (GPIO96); UART6 16/18 for the LC76G; I2C0 13/15 for the INA228 only; I2C2 27/28 for the MCP23017s and RP2040 counter, with no BNO085; UART7 32/29 only for the HMI RP2040 if it works.
     - IMU interface: the USB-CDC puck (RP2040-Zero + BNO085) on CH334F H2. Reason: it does not depend on the unverified UART7, it avoids BNO085 clock stretching on GENI I2C, and the boom puck needs its own MCU and cable anyway.
     - Fan: on/off at 60/50 C through an AO3400 on GPIO56 (PoE-HAT overlay with the 'cpu0-thermal' spelling fixed). Pin 33 pwm-gpio is the fallback. With on/off control the 1 kHz PWM ticking is irrelevant.
  7. Ownership: labd is the sole owner and lock authority for every rail switch here (LNB #2813, AUX P-FET, TPS2553 ENs, LAB VBUS). labrx owns the single ring and the recorder. labclassify runs inferd and fusiond. Reason: one lease mechanism prevents two daemons toggling the same supply.
  8. LNB supply: 13.2 V +-0.2 V from the Pololu S18V20AHV, switched by a second #2813 (40 V-rated, true off), then an LC filter, ferrite and polyfuse, on F connectors. No 18 V branch. Reason: the Bullseye needs 11.5-14 V for vertical; Pololu says the SEPIC's EN does not disconnect the output; the TPS2553 is only rated 2.5-6.5 V. Set one current limit at 1.5-2x the measured draw, choosing the PTC after the bench measurement.
  9. LNA bias: a TPS2553DBVR at 250-300 mA for every SAWbird+ (constant-current variant, FAULT to labd). The V4L tee powers only LNAs of 80 mA or less. Delete the 100-160 mA PTC rule.
  10. FM filter: Flamingo+ FM only.
  11. librtlsdr: the .so.2 rebuild of noble 2.0.1 (0204c9c + 65f0658) only.
  12. Display: about 127.9 MHz (51.7 Hz) field mode, or 164.4-168.4 MHz if the panel accepts it. Add 1415.7/1544.4 MHz and the LF time bands to the A/B test.
  13. PPS: out-of-tree pps-gpio on 6.18.2-4; drop Route B. Buy the FT232RL fallback (and build pps-ldisc) only if the UART6 TX loopback fails.
  14. INA228: Adafruit #5832 on I2C0 through user-space i2c-dev with no DT binding. Shunt in the pack lead ahead of both the IP2368 and the loads, so it counts charge and discharge. Always-on 3.3 V supply, pull-ups removed. Its 10 A shunt rating exceeds both fuse values.
  15. Antenna tiers: re-decide under the two-tier rule. LRPT uses the V-dipole; the crossed Yagi defaults to the ultra-compact build; strike every loop. Outside this group.
  16. Policy leftovers: strike all of them (VNA antenna S11, Inmarsat-C decode-then-filter replaced by the header-level rule, VLF SID, BT rfkill and the Artemis stop added, voice IQ and Set B removed, Iridium/CARTOSAT rows, H-probes, city lists and Kyiv constants, wsjtx GUI and fldigi, the bearing log). For this group, the location gate uses WMM2025 at the fix and the RTC anchor; there is no city table.
  17. HF chain: Boni-Whip at 12.5 V from an LT3045 on 4S. It has 1.1 V headroom at the 13.6 V cutoff against a 260 mV dropout, and 12.5 V meets both the 9-15 V and 12-15 V published ranges. LF time signals rely on the active whip. The selector relay is outside this group. The HF-loop removal follows REQUIREMENTS.md.
  18. Storage: the T7 only with the Lime; otherwise a V30/A2 microSD or an A/B UFS root, with products kept by default and raw IQ only when pinned.
  19. CPU: inference fallback on the A55 cores; T2 training on CPU4-6 between passes; CPU7 isolated only with the Lime.
  20. Roadmap: NPU Phase 0 inside W1-2 (19 Oct-1 Nov 2026); a minimal labeller in P0b; HF-F and second-RTL profiles before HF classes appear in the UI.
  21. V4L: buy 3 (2 in service plus 1 spare).
  22. Software: one venv-per-tool recipe (NanoVNA-Saver via pipx, PySide6 6.12), libgpiod v1, Skyfield 1.55 from pip, SatDump 2.0-alpha from source, OpenWebRX+ with pins.
  23. Region unknown: buy the LC76G now (USD 14.99, worldwide except Iran/Russia, jamming flags only). Add a u-blox M10 (Uputronics MAX-M10S) only if spoof flags matter in the user's region. Prices here are world prices. Hold the LNB, horn and SAWbird+ iO until the region is known.
  24. Costs and weights: this group is re-priced at world prices, about USD 426 (see the subtotal above). The sling (about 3.7-4.4 kg) and the case weight are to be recomputed after the panel outline is confirmed.
  25. P1b completion: final/report_research.json now exists (read for this task). The summaries.md and minute-log.md errata blocks remain for the orchestrator.
  
  Sources fetched on 18 Oct 2026: Pololu #4095/#3782/#2573/#2813 and categories 131/133; Adafruit 5832/4754/610; SparkFun SEN-22857; Waveshare LC76G and RP2040-Zero; LCSC C55266, C580012, C5372184, C178942, C151093, C427665, C208478, C99102, C319097, C319096, C20606809, C20606791, C521201; TI TPS2553DBVR; TinyTronics Daly; 18650batterystore, BatteryJunction and RaceDayQuads (Shopify JSON); Kiwiquads; Polymaker; Prusa; CNC Kitchen (Shopify JSON); QuietPC; Peak Design; Allnet. NKON, Newegg, Walmart, OnBuy, Mouser, DigiKey, TME, Farnell, Bolt Depot and analog.com blocked fetches; their figures are marked as snippets or not found. Scratch files are in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/pm_fetch.

## sourcing:group4 (run `wf_b9cc0186-94e`)

- **Group:** LAB INSTRUMENTS + BENCH TOOLS (final verified picks per radio_lab.json final lab_bom and report_research.json decisions 130-137 and 134; loops and H-field probes excluded)
- **Offers:**
  1.
    - **Item:** LiteVNA 64 (Zeenko), 50 kHz-6.3 GHz
    - **Seller:** Passion Radio (FR), Zeenko's official reseller in Europe
    - **Url:** https://www.passion-radio.com/analyzer-spectrum/lite-vna64-2730.html
    - **Price:** EUR 187.60, labelled 'tax excl.' (sale price, was EUR 219.00)
    - **Price usd:** 210.88
    - **In stock:** yes: 'In stock, 5 items, last items in stock'
    - **Ships to:** Europe and overseas, shipped from France
    - **Official channel:** так
    - **Notes:** Bundle: SMA cal kit (male OSL), USB cable, 2x 30 cm SMA M-M, SMA F-F. Clone risk: buy only from Zeenko-linked resellers. The research's EUR 177.03 is stale.
  2.
    - **Item:** LiteVNA 64 (Zeenko)
    - **Seller:** Lab401 (FR)
    - **Url:** https://lab401.com/products/litevna
    - **Price:** EUR 192.00
    - **Price usd:** 215.82
    - **In stock:** yes (store feed available=true)
    - **Ships to:** not stated (EU-based shop)
    - **Official channel:** ні
    - **Notes:** Listed as 'LiteVNA (NanoVNA Compatible)', SKU ZEENKO-LITEVNA. The description says '1x Zeenko LiteVNA 64' but the feed vendor field reads DeepElec. The shop claims official Zeenko origin, and Zeenko publishes no seller list to check that against.
  3.
    - **Item:** LiteVNA 64 (Zeenko)
    - **Seller:** GOTRONIK (PL), Zeenko distributor on the tinySA.org official list
    - **Url:** https://www.gotronik.pl/litevna-64-analizator-sieci-wektorowej-50khz-6-3ghz-p-10197.html
    - **Price:** PLN 860.00 gross / PLN 699.19 net (promo price)
    - **Price usd:** 221.33 gross (179.94 net)
    - **In stock:** no: 'Chwilowo niedostepny' (temporarily unavailable)
    - **Ships to:** Poland (only domestic couriers listed)
    - **Official channel:** так
    - **Notes:** Dispatch 24 h once stocked.
  4.
    - **Item:** LiteVNA 64 (Zeenko)
    - **Seller:** Limmared (SE)
    - **Url:** https://butik.limmared.nu/en/antenna-analysis/7430-litevna-64-vector-network-analyser-50khz-63ghz-.html
    - **Price:** SEK 2,195 incl. VAT
    - **Price usd:** 221.47
    - **In stock:** no: 'Out-of-Stock'
    - **Ships to:** not stated
    - **Official channel:** ні
    - **Notes:** Brand ZeenKo, ref 29-1053. Same bundle as Passion Radio.
  5.
    - **Item:** LiteVNA 64 (Zeenko)
    - **Seller:** AliExpress listing titled 'Zeenko LiteVNA 64 Version 0.3.3' (store name not visible)
    - **Url:** https://www.aliexpress.us/item/3256803365552690.html
    - **Price:** USD 212.63
    - **Price usd:** 212.63
    - **In stock:** unknown
    - **Ships to:** worldwide (AliExpress)
    - **Official channel:** ні
    - **Notes:** HIGH CLONE RISK. Buy only if the item is in the Zeenko factory store (store 5800447). The store page needs JavaScript, so I could not confirm the seller.
  6.
    - **Item:** tinySA Ultra+ ZS407
    - **Seller:** Astroradio (ES), on the tinySA.org official list
    - **Url:** https://www.astroradio.com/p/tinysa-ultra-analizador-de-espectro-plus/
    - **Price:** EUR 219.89 (listed as 'tinySA ULTRA++', Modelo ZS407)
    - **Price usd:** 247.17
    - **In stock:** yes: schema InStock, 'En stock entrega inmediata'
    - **Ships to:** Spain with free shipping ('Envio gratuito'); international not stated
    - **Official channel:** так
    - **Notes:** SKU 470011-1. The vendor text claims signals are visible to 12 GHz (marketing only; keep it out of the spec).
  7.
    - **Item:** tinySA Ultra+ ZS407
    - **Seller:** Mirfield Electronics (UK), on the tinySA.org official list
    - **Url:** https://www.mirfield-electronics.co.uk/
    - **Price:** GBP 189.95 + GBP 7.50 UK post (GBP 10 Europe post on sibling items)
    - **Price usd:** 252.98 + 9.99 post
    - **In stock:** limited: 'Limited stock forward orders accepted', 'Just arrived'
    - **Ships to:** UK and Europe
    - **Official channel:** так
    - **Notes:** Order code ME-TinySAUltra+. VAT basis not stated.
  8.
    - **Item:** tinySA Ultra+ ZS407
    - **Seller:** R&L Electronics (US), on the tinySA.org official list
    - **Url:** https://www.randl.com/index.php?main_page=product_info&cPath=16_16990&products_id=76237
    - **Price:** USD 219.95
    - **Price usd:** 219.95
    - **In stock:** no: 'Out of stock'
    - **Ships to:** US (international not stated)
    - **Official channel:** так
    - **Notes:** R&L's 'TINYSAULTRAPLUS' at $169.95 is the ZS406 (5.4 GHz): wrong model.
  9.
    - **Item:** tinySA Ultra+ ZS407
    - **Seller:** GOTRONIK (PL), on the tinySA.org official list
    - **Url:** https://www.gotronik.pl/tinysa-ultra-analizador-widma-100khz-7-3ghz-zs407-zeenko-p-13267.html
    - **Price:** PLN 899.00 gross / PLN 730.89 net
    - **Price usd:** 231.36 gross (188.10 net)
    - **In stock:** unclear: the page shows both 'Chwilowo niedostepny' and an add-to-cart button
    - **Ships to:** Poland
    - **Official channel:** так
    - **Notes:** Titled 'TinySA ULTRA ... ZS407 Zeenko'; the spec table says ZS-407.
  10.
    - **Item:** tinySA Ultra+ ZS407
    - **Seller:** Neven (CZ), on the tinySA.org official list
    - **Url:** https://www.neven.cz/search?phrase=tinysa
    - **Price:** CZK 5,790 incl. VAT (CZK 4,785.12 ex VAT)
    - **Price usd:** 267.47 (221.05 ex VAT)
    - **In stock:** no: 'Neni skladem (0 ks)'
    - **Ships to:** Central and Eastern Europe
    - **Official channel:** так
    - **Notes:** The ZS-406 is in stock there (12 pcs) but is the wrong model.
  11.
    - **Item:** tinySA Ultra+ ZS407
    - **Seller:** Switch Science (JP), on the tinySA.org official list
    - **Url:** https://www.switch-science.com/search?q=tinysa
    - **Price:** JPY 33,800 incl. tax
    - **Price usd:** 213.92
    - **In stock:** no: sold out
    - **Ships to:** Japan
    - **Official channel:** так
    - **Notes:** The old tinySA Ultra is marked discontinued there in favour of the ZS407.
  12.
    - **Item:** tinySA Ultra+ ZS407
    - **Seller:** AliExpress listing titled 'Zeenko TinySA Ultra ZS407 (7.3 GHz, HW V0.5.4)' (store name not visible)
    - **Url:** https://www.aliexpress.us/item/3256812823730328.html
    - **Price:** USD 221.32
    - **Price usd:** 221.32
    - **In stock:** unknown
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** HIGH CLONE RISK. tinySA.org says only the Zeenko factory store (zeenko.aliexpress.com/store/5800447) is safe on AliExpress, and I could not confirm this listing is in that store.
  13.
    - **Item:** Noise source part: Mini-Circuits ZFL-500LN+ (low-noise amp for the N8DMT DIY source)
    - **Seller:** Mini-Circuits
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=ZFL-500LN%2B
    - **Price:** USD 116.81 (qty 1-4)
    - **Price usd:** 116.81
    - **In stock:** yes: more than 100
    - **Ships to:** not stated on page (Mini-Circuits sells worldwide via its store and DigiKey/Mouser)
    - **Official channel:** так
    - **Notes:** 0.1-500 MHz, SMA. Add an ANNE-50+ on the input, pads from the Nooelec kit and a small box; run from regulated AUX 12 V. The study's $20-40 holds only for a used ZFL-500.
  14.
    - **Item:** Noise source part: Mini-Circuits ZFL-500+ (alternative amp)
    - **Seller:** Mini-Circuits
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=ZFL-500%2B
    - **Price:** USD 99.55 (qty 1-4)
    - **Price usd:** 99.55
    - **In stock:** yes: more than 100
    - **Ships to:** not stated
    - **Official channel:** так
    - **Notes:** 0.05-500 MHz gain block. Cheaper new option. Its ENR is uncalibrated: characterise it with the tinySA.
  15.
    - **Item:** E-field near-field probe parts: Mini-Circuits 086-6SM+ (cut in half to make two E-field stub probes)
    - **Seller:** Mini-Circuits
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=086-6SM%2B
    - **Price:** USD 16.67
    - **Price usd:** 16.67
    - **In stock:** yes: more than 1,000
    - **Ships to:** not stated
    - **Official channel:** так
    - **Notes:** 0.086 in. hand-flex, SMA male both ends, 15 cm. Expose about 5-10 mm of centre conductor and heat-shrink it. E-field only, as the rule requires.
  16.
    - **Item:** E-field probe parts (stiffer option): Mini-Circuits 141-6SM+
    - **Seller:** Mini-Circuits
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=141-6SM%2B
    - **Price:** USD 14.65
    - **Price usd:** 14.65
    - **In stock:** no: current stock 0 (contact sales)
    - **Ships to:** not stated
    - **Official channel:** так
    - **Notes:** 0.141 in. hand-flex, SMA.
  17.
    - **Item:** Nooelec SMA Attenuator Kit (1/2/3/6/10/20 dB, DC-6 GHz, 2 W)
    - **Seller:** Nooelec store
    - **Url:** https://www.nooelec.com/store/attenuator-bundle.html
    - **Price:** USD 47.95
    - **Price usd:** 47.95
    - **In stock:** not stated ('Orders usually shipped in 1 business day')
    - **Ships to:** worldwide ('Any order, anywhere'; free shipping over $100)
    - **Official channel:** так
    - **Notes:** SKU 100815. +/-0.1 dB to 3 GHz, +/-0.4 dB to 6 GHz.
  18.
    - **Item:** 30 dB SMA pad (generic, M-F, 0-6 GHz, 2 W), need x2
    - **Seller:** Passion Radio (FR), RF KONNECT brand
    - **Url:** https://www.passion-radio.com/sma/sma-attenuator-826.html
    - **Price:** EUR 13.20 each (EUR 11.00 ex VAT in the listing block); -30 dB version
    - **Price usd:** 14.84 each
    - **In stock:** yes: more than 10
    - **Ships to:** Europe and overseas
    - **Official channel:** так
    - **Notes:** Gold-plated brass, symmetrical. VNA-check on arrival as the BOM requires.
  19.
    - **Item:** 30 dB SMA pad (branded fallback): Mini-Circuits VAT-30W2+
    - **Seller:** Mini-Circuits
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=VAT-30W2%2B
    - **Price:** USD 31.43 (qty 1-4)
    - **Price usd:** 31.43
    - **In stock:** yes: more than 1,000 (DigiKey 48)
    - **Ships to:** not stated
    - **Official channel:** так
    - **Notes:** DC-6 GHz. Power rating is not on the page; check the datasheet. The VAT-30+ is non-catalog.
  20.
    - **Item:** 30 dB SMA pad (generic): Zeenko 30 dB DC-6 GHz 2 W
    - **Seller:** GOTRONIK (PL)
    - **Url:** https://www.gotronik.pl/tlumik-rf-sma-30db-dc-6ghz-2w-zeenko-p-15003.html
    - **Price:** PLN 48.00 gross / PLN 39.02 net
    - **Price usd:** 12.35
    - **In stock:** unclear ('Chwilowo niedostepny' shown)
    - **Ships to:** Poland
    - **Official channel:** так
    - **Notes:** SMA plug to jack.
  21.
    - **Item:** Mini-Circuits BLK-89-S+ DC block (need x2)
    - **Seller:** Mini-Circuits
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=BLK-89-S%2B
    - **Price:** USD 20.26 (qty 1-9)
    - **Price usd:** 20.26 each
    - **In stock:** yes: more than 1,000
    - **Ships to:** not stated
    - **Official channel:** так
    - **Notes:** SMA-F/SMA-M. DigiKey shows 0.
  22.
    - **Item:** Mini-Circuits ANNE-50+ 50 ohm termination (need x3)
    - **Seller:** Mini-Circuits
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=ANNE-50%2B
    - **Price:** USD 14.84 (qty 1-24)
    - **Price usd:** 14.84 each
    - **In stock:** yes: more than 1,000
    - **Ships to:** not stated
    - **Official channel:** так
    - **Notes:** SMA-M, 18 GHz. Never put LNB 13 V on it.
  23.
    - **Item:** Mini-Circuits 086-6SM+ 15 cm hand-flex jumper (need x2)
    - **Seller:** Mini-Circuits
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=086-6SM%2B
    - **Price:** USD 16.67 (qty 1-9)
    - **Price usd:** 16.67 each
    - **In stock:** yes: more than 1,000
    - **Ships to:** not stated
    - **Official channel:** так
    - **Notes:** Buy a 3rd if you make the E-field probes from one.
  24.
    - **Item:** Female SMA OSL kit (explicitly female)
    - **Seller:** AliExpress listing '3.5MM FEMALE CALIBRATION KIT 6GHZ YSG-85033 OPEN SHORT LOAD SET OF 3 SMA FEMALE'
    - **Url:** https://www.aliexpress.us/item/3256806434652651.html
    - **Price:** USD 68.75
    - **Price usd:** 68.75
    - **In stock:** unknown
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** Generic, store unknown; VNA-check it. Above the BOM's $10 estimate.
  25.
    - **Item:** Female SMA OSL kit (budget, gender of OSL not confirmed)
    - **Seller:** AliExpress listing '5pcs Network Analyzer Calibrator Kit DC-6GHz Short/Open/50 ohm Load SMA ... Female-to-Female'
    - **Url:** https://www.aliexpress.us/item/3256812356892241.html
    - **Price:** USD 10.55
    - **Price usd:** 10.55
    - **In stock:** unknown
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** The item page would not load. Confirm the OSL standards are female before buying. Free fallback: the bundled male OSL plus the bundled F-F adapter.
  26.
    - **Item:** SMA torque wrench 0.9 N·m, 8 mm, break-over (TOJOIN)
    - **Seller:** TOJOIN Official Store on eBay
    - **Url:** https://www.ebay.com/itm/354598266754
    - **Price:** USD 35.89, free standard shipping
    - **Price usd:** 35.89
    - **In stock:** seen in search results only (the eBay page returned 403 to fetch)
    - **Ships to:** multi-region eBay listing (de/fr/au/ca/at/es mirrors)
    - **Official channel:** так
    - **Notes:** The brand's own eBay store. Seen only in a search snippet, so confirm before ordering.
  27.
    - **Item:** SMA torque wrench (alternative): 8/4 mm ratcheting, preset 0.5-0.9 N·m
    - **Seller:** AliExpress listing (store unknown)
    - **Url:** https://www.aliexpress.us/item/3256812748700589.html
    - **Price:** USD 51.49
    - **Price usd:** 51.49
    - **In stock:** unknown
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** Fixed 0.9 N·m Zhongji listings cost $92.89-94.39.
  28.
    - **Item:** ANENG AN8008 pocket DMM
    - **Seller:** AliExpress listing 'ANENG AN8008 True RMS Digital Multimeter' (store name not visible)
    - **Url:** https://www.aliexpress.us/item/3256808914707497.html
    - **Price:** USD 28.22
    - **Price usd:** 28.22
    - **In stock:** unknown
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** Other AN8008 listings cost $21.56-42.59. ANENG sells mainly through AliExpress, but no listing showed a store name.
  29.
    - **Item:** ANENG AN8008 / AN8009 (thermocouple variant)
    - **Seller:** AliExpress listing 'ANENG AN8008/AN8009 Mini Digital Multimeter ... Double Fuse'
    - **Url:** https://www.aliexpress.us/item/3256809391514502.html
    - **Price:** USD 36.19
    - **Price usd:** 36.19
    - **In stock:** unknown
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** Choose AN8009 for the K-type thermocouple option. Store not confirmed.
  30.
    - **Item:** FNIRSI FNB58 Std (no Bluetooth)
    - **Seller:** FNIRSI official store
    - **Url:** https://www.fnirsi.com/products/fnb58
    - **Price:** USD 53.99 (FNB58 Std.); BT variant USD 58.99
    - **Price usd:** 53.99
    - **In stock:** yes (variant available=true)
    - **Ships to:** not stated
    - **Official channel:** так
    - **Notes:** CORRECTION: the $58.99 in radio_lab is the BT price. The required Std is $53.99.
  31.
    - **Item:** Hantek 6022BL USB scope + 16-ch LA
    - **Seller:** AliExpress listing '[Hantek Official Genuine] 6022BE ... 6022BL+Logic Analyzer'
    - **Url:** https://www.aliexpress.us/item/3256806554958024.html
    - **Price:** USD 102.34
    - **Price usd:** 102.34
    - **In stock:** unknown
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** The title mixes BE and BL, so choose the BL variant. Store not confirmed. Grey and clone risk.
  32.
    - **Item:** Hantek 6022BL
    - **Seller:** AliExpress listing 'Hantek 6022BL 2CH USB PC Oscilloscope 20MHz 48MSa/s 16CH Logic Analyzer'
    - **Url:** https://www.aliexpress.us/item/3256807879472370.html
    - **Price:** USD 84.33
    - **Price usd:** 84.33
    - **In stock:** unknown
    - **Ships to:** worldwide
    - **Official channel:** ні
    - **Notes:** Cheapest 6022BL seen; range $84.33-157.99. Store unknown.
  33.
    - **Item:** Hantek 6022BL (Western distributor)
    - **Seller:** The Debug Store (UK, Hantek distributor)
    - **Url:** https://thedebugstore.com/products/hantek-6022bl-oscilloscope-analyser-uk
    - **Price:** GBP 110 ex VAT / GBP 132 incl. VAT (search snippet only)
    - **Price usd:** 146.50 ex VAT
    - **In stock:** delisted: the product URL now returns 404, and the shop search lists only the 6022BE
    - **Ships to:** worldwide (multi-currency store)
    - **Official channel:** так
    - **Notes:** SainSmart also marks the 6022BL '[Discontinued]' at $88.20. Fallback in stock here: Hantek 6022BE at GBP 100 (about $133.18, https://thedebugstore.com/products/hantek-6022be-usb-oscilloscope-uk) plus the core fx2lafw LA.
  34.
    - **Item:** Raspberry Pi Debug Probe
    - **Seller:** Adafruit (US)
    - **Url:** https://www.adafruit.com/product/5699
    - **Price:** USD 12.00
    - **Price usd:** 12.00
    - **In stock:** yes: 'In stock'
    - **Ships to:** international (Adafruit ships worldwide; not stated on page)
    - **Official channel:** так
    - **Notes:** Raspberry Pi approved reseller.
  35.
    - **Item:** Raspberry Pi Debug Probe
    - **Seller:** PiShop.us (US)
    - **Url:** https://www.pishop.us/product/raspberry-pi-debug-probe/
    - **Price:** USD 12.00
    - **Price usd:** 12.00
    - **In stock:** yes: 'IN STOCK'
    - **Ships to:** not stated
    - **Official channel:** так
    - **Notes:** Approved reseller.
  36.
    - **Item:** Raspberry Pi Debug Probe
    - **Seller:** The Pi Hut (UK)
    - **Url:** https://thepihut.com/products/raspberry-pi-debug-probe
    - **Price:** GBP 11.50 incl. VAT
    - **Price usd:** 15.32
    - **In stock:** yes (available=true, SKU SC0889)
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** Approved reseller.
  37.
    - **Item:** PINE64 Pinecil V2
    - **Seller:** PINE64 store
    - **Url:** https://pine64.com/product/pinecil-smart-mini-portable-soldering-iron/
    - **Price:** USD 25.99 community price (retail USD 35.99)
    - **Price usd:** 25.99
    - **In stock:** yes: 'In stock'
    - **Ships to:** not stated (PINE64 ships internationally)
    - **Official channel:** так
    - **Notes:** Set IronOS Bluetooth Off and 4S at 3.4 V/cell.
  38.
    - **Item:** iFixit Portable Anti-Static Mat (with 1 Mohm wrist strap)
    - **Seller:** iFixit US
    - **Url:** https://www.ifixit.com/products/portable-anti-static-mat
    - **Price:** USD 34.95
    - **Price usd:** 34.95
    - **In stock:** yes: 'Ready to ship'
    - **Ships to:** US domestic free over $75; international not stated
    - **Official channel:** так
    - **Notes:** Part IF145-202-5. 10 mm snap, 1.8 m strap.
  39.
    - **Item:** iFixit Portable Anti-Static Mat
    - **Seller:** iFixit EU
    - **Url:** https://www.ifixit.com/en-eu/products/portable-anti-static-mat
    - **Price:** EUR 29.95
    - **Price usd:** 33.67
    - **In stock:** yes: 'Ready to ship from Germany'
    - **Ships to:** EU
    - **Official channel:** так
    - **Notes:** Cheaper for EU buyers.
  40.
    - **Item:** 65 W+ PD power bank: Anker 737 Power Bank (PowerCore 24K), A1289
    - **Seller:** Anker official store (US)
    - **Url:** https://www.anker.com/products/a1289
    - **Price:** USD 109.99
    - **Price usd:** 109.99
    - **In stock:** yes: 'In Stock, estimated delivery in 3-7 business days'
    - **Ships to:** US (regional Anker stores elsewhere)
    - **Official channel:** так
    - **Notes:** USB-C 5/9/15 V 3 A, 20 V 5 A, 28 V 5 A; 140 W max; 24,000 mAh (under the 100 Wh airline limit). Meets the 20 V/3 A PDO rule. It is bidirectional, so use the charge-only IP2368 BZ or check with the FNB58.
  41.
    - **Item:** Bench powered USB 2.0 hub, 4-port, separate 5 V input, reverse-current protection
    - **Seller:** The Pi Hut (UK), Waveshare Industrial Grade Dual-Host USB Hub (4x USB 2.0)
    - **Url:** https://thepihut.com/products/industrial-grade-dual-host-usb-hub-4x-usb-2-0
    - **Price:** GBP 18.50 incl. VAT
    - **Price usd:** 24.64
    - **In stock:** yes (available=true, WAV-21686)
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** MTT hub chip; protection against over-voltage, over-current, reverse current, UVLO and 8 kV ESD; 5 V DC barrel input (UK 5 V 2 A PSU included). Power it from the bank with a USB-to-DC5521 lead. Preferred because MTT avoids the single-TT bottleneck.
  42.
    - **Item:** Bench powered USB 2.0 hub (alternative): Waveshare USB-HUB-4U
    - **Seller:** Waveshare official store
    - **Url:** https://www.waveshare.com/usb-hub-4u.htm
    - **Price:** USD 14.99-16.99 (with or without PSU)
    - **Price usd:** 14.99-16.99
    - **In stock:** not stated
    - **Ships to:** not stated (Waveshare ships internationally)
    - **Official channel:** так
    - **Notes:** STT chip (single TT), DC 5 V jack, reverse-current protection, 1.2 A per port.
  43.
    - **Item:** GPSDO (extended): Leo Bodnar LBE-1420 GPS locked clock source
    - **Seller:** Leo Bodnar Electronics (UK)
    - **Url:** https://www.leobodnar.com/shop/index.php?main_page=product_info&cPath=107&products_id=393
    - **Price:** GBP 132.00 (VAT basis not stated)
    - **Price usd:** 175.80
    - **In stock:** yes: 'In stock'
    - **Ships to:** 'We ship to anywhere in the world'
    - **Official channel:** так
    - **Notes:** 1 Hz-1.1 GHz, 3.3 V into 50 ohm; USB-C 5 V 250 mA max; includes a magnetic active GPS antenna with 5 m cable. Same price as the Mini, and the vendor recommends it.
  44.
    - **Item:** GPSDO (extended alternative): Leo Bodnar Mini Precision GPS Reference Clock
    - **Seller:** Leo Bodnar Electronics (UK)
    - **Url:** https://www.leobodnar.com/shop/index.php?main_page=product_info&products_id=301
    - **Price:** GBP 132.00
    - **Price usd:** 175.80
    - **In stock:** yes: 'In stock'
    - **Ships to:** anywhere in the world
    - **Official channel:** так
    - **Notes:** 400 Hz-810 MHz. The product page shows 'We recommend a newer version of this product': LBE-1420.
  45.
    - **Item:** FlightAware Pro Stick Plus (ADS-B option)
    - **Seller:** The Pi Hut (UK), FlightAware's listed worldwide source
    - **Url:** https://thepihut.com/products/flightaware-pro-stick-plus-usb-sdr-ads-b-receiver
    - **Price:** GBP 52.50 incl. VAT
    - **Price usd:** 69.92
    - **In stock:** yes (available=true, SKU 103075)
    - **Ships to:** worldwide
    - **Official channel:** так
    - **Notes:** FlightAware's own page lists flightaware.store (USA) and The Pi Hut (worldwide). The US store blocked automated fetches (429 / bot check).
- **Not found:**
  1.
    - **Item:** ANENG AN8008 from a verifiable ANENG official store
    - **Closest equivalent:** AliExpress AN8008 listings at $21.56-42.59 (store name not shown on any of them)
    - **Note:** One search and two AliExpress fetches found no confirmed 'ANENG Official Store' page. ManoMano.de EUR 28.99 (third-party, search snippet) and eBay.de AU$44.60 (Shenzhen seller) are not official.
  2.
    - **Item:** Hantek 6022BL from an official Western reseller
    - **Closest equivalent:** Hantek 6022BE (GBP 100, in stock at The Debug Store) plus the core fx2lafw logic analyser; or AliExpress 6022BL listings ($84-158, store unconfirmed)
    - **Note:** The Debug Store's 6022BL page now returns 404 and SainSmart marks it discontinued. The 6022BE is scope-only, which matches the BOM's listed cheaper alternative.
  3.
    - **Item:** Female SMA OSL kit from a branded or official maker at the BOM's ~$10 estimate
    - **Closest equivalent:** Mini-Circuits KSOLT-63-S+ (female and male OSL, matched thrus and a torque wrench in one kit; price not retrievable), AliExpress generic kits ($10.55-68.75), or the free route: bundled male OSL plus bundled F-F adapter
    - **Note:** The Zeenko SOLT kit at Gotronik (PLN 120) has MALE open/short, so it does not fit. The Passion Radio RF KONNECT kit (EUR 19.90, in stock) does not state its gender.
  4.
    - **Item:** Ready-made E-field-only near-field probe set
    - **Closest equivalent:** DIY stub probes cut from a Mini-Circuits 086-6SM+ ($16.67)
    - **Note:** The Zeenko 3-probe EMI set (Gotronik PLN 39) contains two H-field loops (28 mm and 4.5 mm) plus one E-field probe, so the no-loop rule EXCLUDES it. The PS-500 and generic E/H sets are struck for the same reason.
  5.
    - **Item:** SMA torque wrench store page fetched directly
    - **Closest equivalent:** TOJOIN Official Store on eBay, $35.89 with free shipping (seen in search results only)
    - **Note:** eBay returned 403. A branded L-com LC-TWC08516 (DigiKey JP, about JPY 58,537, about $370) is far above budget.
  6.
    - **Item:** tinySA ZS407 and LiteVNA 64 confirmed inside the Zeenko AliExpress factory store (5800447)
    - **Closest equivalent:** AliExpress search listings titled 'Zeenko' ($221.32 tinySA, $212.63 LiteVNA); official EU/UK/US resellers above
    - **Note:** Store pages render only with JavaScript and item pages redirect to a login and captcha, so the seller could not be confirmed.
  7.
    - **Item:** FlightAware own US store price
    - **Closest equivalent:** The Pi Hut GBP 52.50 (in stock, worldwide)
    - **Note:** flightaware.store answered 429 and then a bot-verification page.
  8.
    - **Item:** Buyable compliant noise-source module
    - **Closest equivalent:** DIY N8DMT-type source built on a Mini-Circuits ZFL-500+ ($99.55) or ZFL-500LN+ ($116.81)
    - **Note:** The study bans the generic '0.001-3000 MHz noise generator' modules. The Nooelec 'Ham It Up noise source kits' ($5.95/$9.95) are upconverter add-ons and were not evaluated.
  9.
    - **Item:** LBE-1420 EUR price
    - **Closest equivalent:** GBP 132.00 on leobodnar.com
    - **Note:** The research's 'EUR 155 net' could not be re-seen. The UK shop page does not state its VAT basis.
- **Notes:** FX used (open.er-api.com, 18 Oct 2026 00:02 UTC): 1 USD = 0.8896 EUR / 0.7508 GBP / 3.8857 PLN / 9.911 SEK / 158.0 JPY / 21.65 CZK. All prices exclude shipping and import VAT unless stated.
  
  PICKS (cheapest in-stock official offers seen): LiteVNA 64 at Passion Radio EUR 187.60 (about $211); tinySA ZS407 at Astroradio EUR 219.89 (about $247, in stock), or Mirfield GBP 189.95 (limited); ZFL-500LN+ $116.81 or ZFL-500+ $99.55; E-field probes from one 086-6SM+ $16.67; Nooelec kit $47.95; 2x 30 dB pads from Passion Radio at EUR 13.20 each; 2x BLK-89-S+ $40.52; 3x ANNE-50+ $44.52; female OSL at about $10.55 (AliExpress, gender unconfirmed); 2x 086-6SM+ $33.34; TOJOIN wrench $35.89; AN8008 about $28; FNB58 Std $53.99; Hantek 6022BL about $84-102 (AliExpress only); Debug Probe $12; Pinecil $25.99; iFixit mat $34.95 (EUR 29.95 in the EU); Anker 737 $109.99; Waveshare MTT hub GBP 18.50. Core subtotal in this group is about $1,200 before shipping and VAT. Extended: LBE-1420 GBP 132 (about $176). ADS-B: Pro Stick Plus GBP 52.50 (about $70).
  
  CLONE RISK: tinySA: buy only from the tinySA.org list (Zeenko AliExpress store 5800447, Eleshop, R&L, Switch Science, Mirfield, Astroradio, Neven, Kami, Selteq, Gotronik, the Aursinc/SeeSii Amazon stores). TinyRFEquip and TinyRFLab are fake 'authorised' shops, and Banggood sells clones. WRONG MODEL: Lab401 'TinySA Ultra+' EUR 163, Passion Radio 'TinySA ULTRA' EUR 168.36, R&L 'TINYSAULTRAPLUS' $169.95 and Neven ZS-406 are all the 5.4 GHz ZS406, not the ZS407. LiteVNA: AliExpress listings carry high clone risk; prefer Passion Radio (Zeenko's official EU reseller) or Gotronik. Hantek on AliExpress is a grey/clone risk. RTL and Airspy are not in this group.
  
  CORRECTIONS from this step:
  (a) FNB58 Std is $53.99; $58.99 is the BT variant.
  (b) LBE-1420 is GBP 132 (same as the Mini), in stock, with antenna included. Choose the LBE-1420 for the extended GPSDO slot; the Linux flash-save and drive-level caveats remain.
  (c) The Hantek 6022BL looks discontinued in the West.
  (d) Passion Radio's LiteVNA 64 price is now EUR 187.60, not EUR 177.03.
  (e) R&L's ZS407 is out of stock at $219.95.
  (f) The Anker 737 has a 20 V/5 A PDO.
  (g) A new ZFL-500(LN)+ costs $100-117, so the core noise-source line becomes about $110-140 new (the $20-40 needs a used amp).
  (h) The Astroradio vendor text is the only source for 'visible to 12 GHz' and it is marketing; keep it out of the spec.
  
  RESOLUTIONS of conflicts_for_final_checks (decision, then reason):
  1. Lime: gated optional. Keep the cancellable pre-order and decide on 31 Jan 2027; no core lab function depends on it. Reason: S-band and 56 Msps are the only unique gains. Here, the GPSDO's 30.72 MHz J4 use is conditional.
  2. Buy the 12 GB Q6A now. Reason: RAM cannot be added later, and it keeps training and the Lime open. Re-check Allnet stock on the order date.
  3. 4S1P P50B with a regulated 12 V rail. Reason: the LNB, Boni-Whip, AUX and ENR stability need at least 12 V. The Pinecil is set to 4S at 3.4 V/cell.
  4. Defer the 12 V regulator choice until the terminated-floor spur A/B and the sealed-case current test. Reason: it needs data, so buy the tinySA, FNB58 and AN8008 first.
  5. Freeze the Lime-agnostic USB map. Bench mode puts the MTT Waveshare hub, powered from the bank, behind LAB USB. Reason: VCC_5V_PERI is only about 17 W.
  6. Adopt the header map. The IMU goes over a UART relay through the HMI RP2040. Reason: it saves a USB port; the Debug Probe verifies UART6/7.
  7. labd is the sole hardware owner. Reason: one lock authority.
  8. LNB at 13.2 V +/-0.2 V with true disconnect and no 18 V; current limit 1.5-2x the measured draw. Reason: the Bullseye window and safety. Never into an ANNE-50+.
  9. TPS2553 at 250-300 mA for every SAWbird+, and the V4L tee only for LNAs of 80 mA or less. Reason: the 180 mA draw.
  10. Flamingo+ FM only. Reason: its 250 mA DC pass is published.
  11. Use only the librtlsdr .so.2 rebuild. Reason: no consumer rebuilds are needed.
  12. Run the display at 127.9 MHz. Reason: the 128.70 MHz harmonics fall at 1544.4 and 1415.7 MHz. Verify with the tinySA and an E-field probe.
  13. Build pps-gpio out of tree on 6.18.2-4. Reason: CONFIG_PPS=y and the kernel hold.
  14. INA228 on I2C0 through user-space i2c-dev, shunt in the pack lead. Reason: this keeps CHARGE access.
  15. Two antenna tiers, V-dipole as the LRPT default, all loops struck. Reason: user rule.
  16. Strike every policy leftover. For this group: no H-field probes (PS-500, the E/H sets and the Zeenko 3-probe set are excluded); the LiteVNA never sweeps an antenna; the tinySA generator, noise source and GPSDO are conducted-only.
  17. Boni-Whip at 12.5 V, add the HF+ selector relay, LF only via the active whip. Reason: supply ranges and balun loss. The loop ban stands but is flagged for user confirmation.
  18. T7 only with the Lime; otherwise microSD or UFS. Reason: cost.
  19. CPU plan as recommended. Reason: isolation is needed only with the Lime.
  20. NPU Phase 0 inside W1-2. Reason: the early gate.
  21. Buy 3 V4Ls. For dedicated continuous ADS-B, the Pro Stick Plus (about $70) is cheaper than a V4L plus Uputronics 1090 (about $92). Reason: the prices above.
  22. venv recipe; test NanoVNA-Saver with the LiteVNA 64 and QtTinySA inside the return window. Reason: the apt versions are unverified.
  23. Region unknown: hold the LNB, horn and SAWbird+ iO. Lab instruments are region-neutral, so buy from the nearest official seller (EU: Passion Radio, Astroradio, iFixit EU; UK: Mirfield, Pi Hut, Bodnar; US: Mini-Circuits, Nooelec, Adafruit, PiShop, PINE64, Anker).
  24. Re-priced here at world prices, with the H-probe line removed. Reason: P5 needs real prices.
  25. report_research.json now exists and was read. The errata blocks belong to the orchestrator's summaries and minute-log step, not this sourcing step.
  
  SOURCES: tinysa.org/wiki/pmwiki.php?n=Main.Buying; passion-radio.com; lab401.com; gotronik.pl; butik.limmared.nu; astroradio.com; mirfield-electronics.co.uk; randl.com; neven.cz; switch-science.com; aliexpress.com search pages; minicircuits.com; nooelec.com; fnirsi.com; thedebugstore.com; sainsmart.com; adafruit.com; pishop.us; thepihut.com; pine64.com; ifixit.com; anker.com; waveshare.com; leobodnar.com; flightaware.com/adsb/prostick; ebay.com/itm/354598266754 (snippet). WebSearch calls used: 7.

## sourcing:verify (run `wf_b9cc0186-94e`)

- **Buying notes:** VERIFICATION, 18 Oct 2026. Methods: Shopify .js/JSON, the WooCommerce store API, page HTML, WebFetch and datasheet PDFs. I used 2 of about 12 WebSearch calls. FX (open.er-api, 18 Oct 00:02 UTC): 1 EUR = 1.1241 USD, 1 GBP = 1.3318 USD, 1 CAD = 0.7069 USD. The SDR group converted at 1.16 USD/EUR; those lines are recomputed here. About 69% of the low total uses prices I saw live today; the rest are agent-read prices or estimates, marked verified=false.
  
  CONFIRMED LIVE (price and stock)
  - Q6A 12 GB: TinyTronics EUR 148 incl. VAT, 10+ in stock. Allnet $189.99 available. Arace sold out on every variant. Allnet 8 GB sold out.
  - Radxa's own distributor page (radxa.com/distributors) lists Allnet, Arace and TinyTronics (plus RS, SB Components and Indian/Brazilian shops). Ameridroid and OKdo are not listed.
  - UFS 128 GB: Allnet $65.90 available. TinyTronics EUR 58, not in stock (2-4 weeks).
  - Displays: Wisecoco $132, schema InStock. The listing still says 'I2C Capacitive Touch', with no input voltage and no package contents. 4D 4DHDMI-70-1280-800-CT-EAR-1000: DigiKey $128.95 (13 in stock), 4D store $141.85.
  - LimeSDR Micro Basic: $249 + $18 worldwide shipping, pre-order, ships 15 Dec 2026; there is still no 2230 variant. MHF4L-SMA cable $6. Crowd Supply cancels stock and pre-orders with a full refund only before shipment. After delivery it gives a 30-day guarantee less a restocking fee of $20 or more.
  - RF: Airspy HF+ Discovery $169 at ITEAD, in stock at its EU, US and CN warehouses (store API). V4L $37.95 (455 in stock). Bullseye $29.95 (70). LNA V2 $19.95 (208). Dipole kit $17.95 (357). L-band patch set $59.95 (on the buy page; the product URL is 404).
  - Nooelec: SAWbird+ GOES/iO/NOAA cased $49.95 (SKUs 100792/100788/100800), Flamingo+ FM $24.95, Balun One Nine v2 $26.95, attenuator kit $47.95. Free worldwide shipping over $100.
  - Lab: tinySA ZS407 at Astroradio EUR 219.89 incl. 21% VAT, in stock; Astroradio is on the tinySA.org safe-seller list. LiteVNA 64 at Passion Radio: 5 left. Mini-Circuits: ZFL-500LN+ $116.81, ZFBT-4R2GW+ $111.57, BLK-89-S+ $20.26. Anker 737 $109.99. FNB58 Std $53.99 (BT $58.99). LBE-1420 GBP 132, in stock, antenna included.
  - Also confirmed: Pololu #4095/#3782/#2573/#2813 prices (all 'Rationed'). Adafruit CH334F, INA228, BNO085, HDMI 2420, fan 6101, reader, cable and Debug Probe in stock. Waveshare LC76G $14.99 and L1+L5 antenna $16.99 InStock. P50B $9.99 at 18650 Battery Store. Debug Store Hantek 6022BE GBP 100 in stock. Pi Hut Pro Stick Plus GBP 52.50 and MTT hub GBP 18.50.
  
  NEW FINDINGS THAT CHANGE THE DESIGN OR THE PLAN
  1. Uputronics' own store lists the '440MHz CubeSAT' filtered preamp at GBP 51.59 incl. UK VAT (about GBP 42.99 ex VAT), available; the '434MHz' variant is GBP 41.99. Bias input is 5 V, and the store calls it Airspy bias-tee compatible. This closes the 'no buyable 70 cm BPF/filtered preamp' gap. It replaces the unnamed BPF plus the in-service LNA V2; one LNA V2 stays as the lab spare. Measure its current before using the V4L tee.
  2. Mini-Circuits TCBT-2R5G+ datasheet: 20-2500 MHz, 0.4 dB, DC current 200 mA max, +25 V. TCBT-14+/14R+ are also 200 mA. ZFBT-4R2GW+/6GW+ are 500 mA and 30 V. So a TPS2553 set to 250-300 mA could hold an overload above the tee's rating. See conflict 9.
  3. Allnet refund policy: return within 7 days of receipt (14 days into the EU), unused and in original packaging only. A board that fails burn-in is therefore a warranty/RMA case, not a return; keep the UART logs.
  4. TinyTronics' delivery page lists only 26 EU destinations. The agent's 'outside EU on request / UK EUR 170 minimum' claim is unconfirmed. EU consumers pay VAT (OSS), so plan on EUR 148, not EUR 122.31.
  5. Passion Radio page variables show base EUR 219 incl. / 182.50 ex VAT and a reduction of 31.40 incl. / 26.17 ex. So EUR 187.60 is the VAT-inclusive (FR 20%) sale price, despite the 'tax excl.' label. A non-EU buyer may pay about EUR 156.33 ($175.73); confirm at checkout.
  6. The Nooelec core order (NOAA+, GOES+, Flamingo+, Balun, pad kit) is already $199.75, so the iO is not needed to reach free shipping.
  7. Arace shows a '16GB $119.50' Q6A variant (sold out), probably a listing error. Radxa's page says 'up to 16 GB'. Do not plan on it.
  
  CUSTOMS, VAT AND REGION (country unknown: check these)
  - EU: buy VAT-paid inside the EU where possible (TinyTronics, Passion Radio, Astroradio, WiMo, iFixit EU, CNC Kitchen, QuietPC). For non-EU parcels, check whether the seller collects VAT through IOSS (consignments of EUR 150 or less; AliExpress and eBay do). Above EUR 150, expect import VAT plus any duty plus courier handling fees. RTL-SDR Blog's webstore does not ship to the EU: use its official eBay or AliExpress store (no. 4523039).
  - UK: sellers collect VAT on consignments of GBP 135 or less. Above that, import VAT plus courier fees apply. UK sources: Pi Hut, Uputronics, Leo Bodnar (VAT basis of the GBP 132 is not stated), Mirfield, and Moonraker (duty-paid checkout).
  - US: check the current de minimis status and tariffs on China-origin goods before ordering from Allnet, the RTL-SDR Blog CN warehouse, LCSC, Waveshare, ADT-Link or AliExpress. My information, to verify: duty-free de minimis was suspended for all countries from 29 Aug 2025. Prefer US stock where it exists: ITEAD US, DigiKey, Adafruit, Nooelec, Pololu, Mini-Circuits, and RTL-SDR Blog on Amazon USA.
  - CA/AU/CH/NO/JP and elsewhere: check the low-value import GST/VAT rule and whether checkout collects it.
  - Li-ion cells (UN3480) mostly ship by ground and domestically only. Buy the five P50Bs from an established retailer in your own country and test capacity (4.85 Ah or more), IR and weight (68-70 g). The Anker 737 (24,000 mAh, about 86-88 Wh) is under the 100 Wh cabin limit.
  - Shipping restrictions: RTL-SDR Blog will not ship to RU/BY/IR/KP; Waveshare not to IR/RU; Mini-Circuits screens exports.
  - Small-part sellers (LCSC, DigiKey, Mini-Circuits) have shipping fees or minimums that can exceed the part value, so consolidate orders.
  - All totals exclude shipping, import VAT and duty.
  
  CLONE AND AUTHENTICITY
  - RTL-SDR (HIGH risk): official store, eBay rtl-sdr-blog, AliExpress store 4523039 or a listed reseller only. Never blue cases, 'Pro' or 'V4' copies.
  - tinySA and LiteVNA (HIGH): tinySA.org list sellers or Passion Radio only. Reject unconfirmed AliExpress 'Zeenko' listings, Banggood, TinyRFEquip and TinyRFLab.
  - Airspy (MEDIUM): dealers on airspy.com/purchase only.
  - Others: Adafruit or SparkFun BNO08x only. Branded Waveshare RP2040-Zero. Genuine Amass XT30. LCSC is not franchised for ADI/TI (moderate risk on the LT3045). Hantek, ANENG and generic HMC7992 boards from marketplaces have grey or clone risk.
  
  CONFLICTS_FOR_FINAL_CHECKS: DECISION; REASON
  1. LimeSDR Micro: gated optional. Place the store pre-order only if wanted. Move the free keep/cancel decision to 1 Dec 2026, before the 15 Dec ship date. A 31 Jan 2027 decision after delivery costs at least $20 restocking plus return shipping plus non-recoverable import VAT. Riser, MHF4 cables, I-PEX tool and T7 only if kept. Reason: verified Crowd Supply policy and ship date; no core function depends on it.
  2. RAM: buy the 12 GB now. EU: TinyTronics EUR 148 incl. VAT. Elsewhere: Allnet $189.99. RAM budget: 4 GiB ring with the Lime, 1.5 GiB or less without. Reason: both are verified in stock; Allnet 8 GB is sold out and TinyTronics 8 GB saves only EUR 27; RAM cannot be added later.
  3. Pack: 4S1P P50B, 5 cells. Reason: the 13.2 V LNB, the 12.5 V whip LDO and AUX 12 V need more than 12 V.
  4. 12 V regulator: buy the D36V50F12 now ($39.95; stock is 'Rationed', so add a spare if the ration allows). Replace it only if the tinySA terminated-floor spur A/B or the sealed-case current test fails. Reason: no official forced-PWM 12 V buck-boost of 5 A or more was found.
  5. USB map: freeze the Lime-agnostic map and buy 2 CH334F ($4.95, verified). Reason: works with or without the Lime. With Lime+T7, RTL-A needs another hub port; re-plan only if the Lime is kept.
  6. Header map: adopt it. IMU = USB-CDC puck (RP2040-Zero plus Adafruit BNO085) on CH334F H2; buy 2 RP2040-Zero. Reason: does not depend on the unverified UART7.
  7. labd is the sole hardware owner. Reason: one lock authority. No purchase impact.
  8. LNB: 13.2 V ±0.2 V from an S18V20AHV, true-off via a second #2813, no 18 V. Measure the Bullseye current, then set one limit at 1.5-2x that value. Choose the injector after the measurement: TCBT-2R5G+ if the draw is 150 mA or less, otherwise ZFBT-4R2GW+ (500 mA). Reason: TCBT is rated 200 mA and the S18V20AHV EN is not a true disconnect.
  9. LNA bias: keep 250-300 mA for every SAWbird+, but on any port that injects through a 200 mA TCBT, use the latch-off TPS2553-1 variant (check the TI datasheet), or a tee rated 300 mA or more. The V4L tee carries 90 mA or less (half its 180 mA rating). That covers the LNA V2 (90 mA), and the Uputronics 440 after its current is measured. Reason: the TCBT 200 mA rating found today; the vendor LNA V2 figure.
  10. FM filter: Flamingo+ FM v2, $24.95 verified. Reason: published 250 mA DC pass.
  11. librtlsdr: only the .so.2 rebuild of noble 2.0.1. No purchase impact.
  12. Display: buy the Wisecoco only after written answers on USB-HID VID:PID, bonding/AR, input V/I, EDID, acceptance of a 127.9 MHz/51.7 Hz mode, glove mode and package contents. Pay by PayPal. Otherwise buy the 4D from DigiKey at $128.95. Reason: the listing still says I2C touch.
  13. PPS: out-of-tree pps-gpio on 6.18.2-4. Do not buy the FT232RL fallback now. Reason: CONFIG_PPS=y on the held kernel.
  14. INA228: Adafruit 5832 on I2C0 through user-space i2c-dev, shunt in the pack lead. No purchase impact.
  15. Antenna tiers: two tiers. Patch/small: L-band patch, L1/L5 patch, small whips, 4-turn helix. Foldable: dipole kit as the V-dipole (LRPT default), crossed Yagi in the ultra-compact build, helicone, gore horn. No loops are sourced. Reason: user rule.
  16. Policy leftovers: struck. Not sourced: H-probes (PS-500, Zeenko 3-probe set, E/H sets), YouLoop, VNA antenna sweeps, wsjtx GUI/fldigi. Reason: hard rules.
  17. HF: Boni-Whip at 12.5 V from an LT3045. The 9:1 wire is HF only. The selector relay is still unsourced; choose it before relying on AIS-on-HF+. Reason: published supply ranges and the balun's LF loss.
  18. Storage: no T7 and no large microSD now; buy the UFS plus a 64 GB rescue card. Reason: NAND prices; the T7 is needed only with the Lime.
  19. CPU allocation: adopt as written. No purchase impact.
  20. Roadmap: NPU Phase 0 in W1-2, so the board, UFS and Debug Probe are ordered first.
  21. V4L: buy 3 now ($113.85). Continuous ADS-B goes on the Pro Stick Plus (extended), not a 4th V4L. Reason: the R828S is end of life, and the spare stays a spare.
  22. Software: one venv-per-tool recipe. No purchase impact.
  23. Region: hold the Bullseye, LNB supply and horn until the user is confirmed inside the Es'hail-2 footprint. Hold the SAWbird+ iO until header-level discard works on recordings from the L-band patch. Buy region-neutral lab tools from the nearest official seller. Reason: Inmarsat-C is a compliance gate, not a region gate, and the free-shipping argument for the iO is false.
  24. Costs: re-priced in totals_usd at world prices.
  25. P1b errata: outside sourcing. Add these sourcing errata: the 1.16 FX rate, the TCBT 200 mA rating, Uputronics availability, the Passion Radio VAT basis and the Lime cancellation timing.
- **Per item:**
  1.
    - **Item:** Radxa Dragon Q6A 12 GB (RS701-D12J0R44S32Y13W28, Wi-Fi 6/BT 5.4)
    - **Tier:** core device
    - **Best seller:** TinyTronics NL (Radxa-listed distributor) for EU buyers; ALLNET China for everyone else
    - **Url:** https://www.tinytronics.nl/en/development-boards/single-board-computers/radxa-dragon-q6a-qcs6490-12gb
    - **Price usd:** 166.37 (EUR 148 incl. VAT); Allnet 189.99 + shipping
    - **Verified:** так
    - **Alternative:** https://shop.allnetchina.cn/products/radxa-dragon-q6a ($189.99, available)
    - **Notes:** TinyTronics: 10+ in stock, ships only to the 26 EU countries on its delivery page. Arace ($169) is sold out. Allnet returns: 7 days, unused only, so a burn-in failure becomes a warranty claim.
  2.
    - **Item:** Radxa UFS 3.1 Module 128 GB (RA022-B10J0U2)
    - **Tier:** core device
    - **Best seller:** ALLNET China
    - **Url:** https://shop.allnetchina.cn/products/high-performance-ufs-3-1-module
    - **Price usd:** 65.90
    - **Verified:** так
    - **Alternative:** TinyTronics EUR 58 incl. VAT ($65.20), not in stock (2-4 weeks); suits EU buyers combining it with the board
    - **Notes:** Only in-stock world source. Read the manufacturer ID on arrival (0x01CE = Samsung).
  3.
    - **Item:** Radxa Armor Case 7056A (AE036) + 40 mm 5 V fan
    - **Tier:** core device
    - **Best seller:** ALLNET China (case, same order as the board) + Adafruit PID 6101 (fan)
    - **Url:** https://shop.allnetchina.cn/products/radxa-heatsink-7056a
    - **Price usd:** 9.90 + 4.95
    - **Verified:** так
    - **Alternative:** Arace case $4.99 (in stock, but nothing else in stock there, so separate shipping); Noctua NF-A4x10 5V at The Pi Hut GBP 14 ($18.65)
    - **Notes:** Switch the fan on/off at 60/50 C through an AO3400.
  4.
    - **Item:** Display: Wisecoco 7in 1920x1080 2000+ nit HDMI kit (gated)
    - **Tier:** core device
    - **Best seller:** Wisecoco own store
    - **Url:** https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
    - **Price usd:** 132.00 + quoted shipping
    - **Verified:** так
    - **Alternative:** 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000 at DigiKey $128.95 (13 in stock, 4-week lead after that); 4D store $141.85
    - **Notes:** Price and InStock confirmed. Specs are not: the listing says I2C capacitive touch, gives no input voltage and no package contents. Buy only after written answers; pay by PayPal.
  5.
    - **Item:** Short shielded HDMI lead + 2 snap-on ferrites
    - **Tier:** core device
    - **Best seller:** Adafruit PID 2420 + DigiKey Wurth 74271140
    - **Url:** https://www.adafruit.com/product/2420
    - **Price usd:** 9.95 + 7.82
    - **Verified:** так
    - **Alternative:** Adafruit FPC kit (3548 + 3560) at $14.50, only if routing needs it
    - **Notes:** The ferrite price ($3.91 each) was not re-checked.
  6.
    - **Item:** HMI and IMU MCUs: Waveshare RP2040-Zero x2
    - **Tier:** core device
    - **Best seller:** Waveshare
    - **Url:** https://www.waveshare.com/rp2040-zero.htm
    - **Price usd:** 7.98-9.98
    - **Verified:** ні
    - **Alternative:** Raspberry Pi Pico at The Pi Hut, GBP 3.80 ($5.06)
    - **Notes:** Counted once for both HMI and IMU puck (the compute and power groups both listed it). Stock is not shown on the page.
  7.
    - **Item:** Encoders, knobs, sealed keys
    - **Tier:** core device
    - **Best seller:** DigiKey (Bourns PEC11R-4215F-S0024 x3, C&K KSC641J LFS x10) + Adafruit 2055 knob x2
    - **Url:** https://www.digikey.com/en/products/result?keywords=PEC11R-4215F-S0024
    - **Price usd:** 8.85 + 7.00 + 1.90
    - **Verified:** ні
    - **Alternative:** APEM IPR3SAD2 IP67 panel keys at $16.16 each (+$90 for 6)
    - **Notes:** Adafruit knob in stock (verified). DigiKey lines not re-checked.
  8.
    - **Item:** Internal hub and I/O: Adafruit CH334F 5997 x2 + MCP23017 5346
    - **Tier:** core device
    - **Best seller:** Adafruit
    - **Url:** https://www.adafruit.com/product/5997
    - **Price usd:** 9.90 + 5.95
    - **Verified:** так
    - **Alternative:** The Pi Hut CH334F GBP 4.80
    - **Notes:** The completeness lens counts about 24 control lines; add a TCA9535 or a second MCP23017 if confirmed.
  9.
    - **Item:** Flashing/rescue kit: ALLNET 64 GB microSD + Adafruit 5212 reader + Adafruit 6324 USB-A-to-C cable
    - **Tier:** core device
    - **Best seller:** ALLNET China + Adafruit
    - **Url:** https://shop.allnetchina.cn/products/allnet-micro-sd
    - **Price usd:** 16.99 + 6.95 + 2.95
    - **Verified:** так
    - **Alternative:** Raspberry Pi A2 64 GB (Adafruit 6011) is on backorder
    - **Notes:** The Radxa UFS reader RA019 is sold out; flash over EDL or from microSD.
  10.
    - **Item:** Molicel INR21700-P50B x5
    - **Tier:** core device
    - **Best seller:** 18650 Battery Store (US)
    - **Url:** https://www.18650batterystore.com/products/molicel-21700-p50b-5000mah-50a-battery
    - **Price usd:** 49.95 (9.99 each)
    - **Verified:** так
    - **Alternative:** RaceDayQuads $18.49 per 2; NKON EUR 6.75 (unverified, page blocked)
    - **Notes:** Loose cells ship domestically; buy from an established retailer in your own country and test every cell.
  11.
    - **Item:** Daly 4S 15 A BMS + IP2368 100 W 4S PD boards x2
    - **Tier:** core device
    - **Best seller:** TinyTronics (BMS) + marketplace boards
    - **Url:** https://www.tinytronics.nl/en/power/bms-and-chargers/bms/daly-bms-li-ion-li-po-protection-circuit-4s-15a-with-balancing
    - **Price usd:** 9.00 + 25-49
    - **Verified:** ні
    - **Alternative:** None official for the IP2368 board
    - **Notes:** IP2368 prices are snippets only (Newegg $15.79). Burn in 2-3 boards; set RVSET 5.1k and RISET 15k.
  12.
    - **Item:** Pololu D36V50F12 (12 V), D36V28F5 (LAB 5 V), #2813 x2
    - **Tier:** core device
    - **Best seller:** Pololu
    - **Url:** https://www.pololu.com/product/4095
    - **Price usd:** 39.95 + 23.95 + 17.90
    - **Verified:** так
    - **Alternative:** None official for a forced-PWM 12 V 5 A buck-boost
    - **Notes:** All 'Rationed (Active and Preferred)'. Order in one go; buy a spare D36V50F12 if the ration allows.
  13.
    - **Item:** Adafruit INA228 (5832) + LCSC parts (LT3045 x1, TPS2553 x10, fuses, holder, PTC, XT30, DC jacks)
    - **Tier:** core device
    - **Best seller:** Adafruit + LCSC
    - **Url:** https://www.adafruit.com/product/5832
    - **Price usd:** 14.95 + about 25-29
    - **Verified:** ні
    - **Alternative:** TI store TPS2553 (out of stock)
    - **Notes:** INA228 verified in stock. LCSC lines not re-checked; LCSC is not ADI/TI-franchised. Also check the TPS2553-1 latch-off variant.
  14.
    - **Item:** GNSS + RTC + IMU: Waveshare LC76G 24370 + Allnet RTC cell + Adafruit BNO085 4754
    - **Tier:** core device
    - **Best seller:** Waveshare + ALLNET + Adafruit
    - **Url:** https://www.waveshare.com/lc76g-gnss-module.htm
    - **Price usd:** 14.99 + 0.95 + 29.50
    - **Verified:** так
    - **Alternative:** SparkFun BNO086 $34.95; Uputronics MAX-M10S only if spoof flags matter
    - **Notes:** Confirm the RTC plug against schematic sheet 18.
  15.
    - **Item:** Mechanical: ASA 1 kg, CNC Kitchen inserts and screws, Gelid pads x2, strap
    - **Tier:** core device
    - **Best seller:** Polymaker / Prusa, CNC Kitchen, QuietPC, any rated camera strap
    - **Url:** https://cnckitchen.store/products/heat-set-insert-m3-x-5-7-100-pieces
    - **Price usd:** 26 + 46 + 11 + 15-50
    - **Verified:** ні
    - **Alternative:** Peak Design Leash $49.95 (only official strap price seen)
    - **Notes:** CNC Kitchen M3 inserts verified (EUR 9.40). Others not re-checked.
  16.
    - **Item:** RTL-SDR Blog V4L (Lite) x3
    - **Tier:** core device
    - **Best seller:** RTL-SDR Blog official store (non-EU); official eBay/AliExpress store 4523039 (EU)
    - **Url:** https://www.rtl-sdr.com/product/rtl-sdr-blog-v4l-lite-r828s-rtl2832u-1ppm-tcxo-sma-software-defined-radio-dongle-only/
    - **Price usd:** 113.85 (37.95 each)
    - **Verified:** так
    - **Alternative:** None (V3 only as a fallback)
    - **Notes:** 455 in stock. The R828S is end of life, so buy now. HIGH clone risk.
  17.
    - **Item:** 137 MHz front end: Nooelec SAWbird+ NOAA (cased, 100800) + Flamingo+ FM v2 (100813)
    - **Tier:** core device
    - **Best seller:** Nooelec
    - **Url:** https://www.nooelec.com/store/flamingo-plus-fm.html
    - **Price usd:** 49.95 + 24.95
    - **Verified:** так
    - **Alternative:** RTL-SDR Blog FM band-stop $16.95 (no DC rating)
    - **Notes:** Same Nooelec order as GOES+, Balun and the pad kit ($199.75 total, free shipping).
  18.
    - **Item:** 70 cm front end: Uputronics Filtered Preamp, 440 MHz CubeSAT variant
    - **Tier:** core device
    - **Best seller:** Uputronics own store (UK)
    - **Url:** https://store.uputronics.com/products/uputronics-filtered-preamps
    - **Price usd:** 68.71 (GBP 51.59 incl. VAT; about 57.25 ex VAT)
    - **Verified:** так
    - **Alternative:** 434 MHz variant GBP 41.99 (narrower ISM SAW, avoid); LNA V2 + BPF (no BPF part found)
    - **Notes:** Available. Bias input 5 V. Replaces the unnamed 70 cm BPF and the in-service LNA V2. Measure its current before using the V4L tee.
  19.
    - **Item:** LNA injectors: Mini-Circuits TCBT-2R5G+ x3 (DIY SMA board)
    - **Tier:** core device
    - **Best seller:** DigiKey
    - **Url:** https://www.digikey.com/en/products/result?keywords=TCBT-2R5G%2B
    - **Price usd:** 33.93 (11.31 each)
    - **Verified:** так
    - **Alternative:** Mini-Circuits ZFBT-4R2GW+ $111.57 (500 mA, 30 V)
    - **Notes:** 1,350 in stock. Datasheet: 20-2500 MHz, 0.4 dB, 200 mA max, +25 V. Use the TPS2553-1 latch-off on SAWbird+ ports.
  20.
    - **Item:** Coax: RTL-SDR Blog SMA pigtail set + 0.5-1 m RG316 leads with ferrites
    - **Tier:** core device
    - **Best seller:** RTL-SDR Blog store + generic
    - **Url:** https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
    - **Price usd:** 18.95 + 15-30
    - **Verified:** ні
    - **Alternative:** Mini-Circuits 086-24SM+ $24.73
    - **Notes:** Leads are an estimate.
  21.
    - **Item:** RTL-SDR Blog Active L-band patch set (1525-1660 MHz)
    - **Tier:** antenna kits
    - **Best seller:** RTL-SDR Blog store
    - **Url:** https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
    - **Price usd:** 59.95
    - **Verified:** так
    - **Alternative:** DIY 2/4-turn helix + SAWbird+ iO
    - **Notes:** Listed on the buy page as in stock at the Amazon USA and China warehouses (the product URL is 404). 20 mA, so the V4L tee is fine. Patch-tier Inmarsat-C and GNSS antenna; records the header-filter test set.
  22.
    - **Item:** Waveshare GNSS L1+L5 active antenna (25346)
    - **Tier:** antenna kits
    - **Best seller:** Waveshare
    - **Url:** https://www.waveshare.com/gps-external-antenna-d.htm
    - **Price usd:** 16.99
    - **Verified:** так
    - **Alternative:** u-blox ANN-MB5 at SparkFun, $42.50
    - **Notes:** InStock. Also serves as the lab core's L1 reference (de-duplicated).
  23.
    - **Item:** L-band HRPT LNA: Nooelec SAWbird+ GOES (cased, 100792)
    - **Tier:** antenna kits
    - **Best seller:** Nooelec
    - **Url:** https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-goes-302.html
    - **Price usd:** 49.95
    - **Verified:** так
    - **Alternative:** Barebones $44.95 (only inside a shielded case)
    - **Notes:** Includes enclosure and SMA adapter. Feed from a TPS2553(-1), never the V4L tee.
  24.
    - **Item:** RTL-SDR Blog multipurpose dipole kit x2 (V-dipole + spare elements)
    - **Tier:** antenna kits
    - **Best seller:** RTL-SDR Blog store
    - **Url:** https://www.rtl-sdr.com/product/rtl-sdr-blog-multipurpose-dipole-antenna-kit/
    - **Price usd:** 35.90
    - **Verified:** так
    - **Alternative:** One kit + 2-3 piece rods
    - **Notes:** 357 in stock. LRPT default antenna.
  25.
    - **Item:** DIY antennas: 17 cm whip, A-V85/SRH-701 class whip, 4-turn helix, crossed Yagi (ultra-compact), petal helicone
    - **Tier:** antenna kits
    - **Best seller:** Local hardware and metal suppliers
    - **Url:** https://www.rtl-sdr.com/buy-rtl-sdr-dvb-t-dongles/
    - **Price usd:** 55-122 (estimate)
    - **Verified:** ні
    - **Alternative:** None
    - **Notes:** Materials only; tune receive-only.
  26.
    - **Item:** QO-100: Othernet Bullseye TCXO LNB (HOLD until region confirmed)
    - **Tier:** antenna kits (held add-on)
    - **Best seller:** RTL-SDR Blog store
    - **Url:** https://www.rtl-sdr.com/product/qo-100-bullseye-tcxo-lnb/
    - **Price usd:** 29.95
    - **Verified:** так
    - **Alternative:** Technofix UK GBP 31.99 (out of stock)
    - **Notes:** 70 in stock; Technofix is already out, so don't wait long once the region is known.
  27.
    - **Item:** LNB 13.2 V supply: Pololu S18V20AHV + #2813 + injector + F-SMA/LC/PTC
    - **Tier:** antenna kits (held add-on)
    - **Best seller:** Pololu + DigiKey/Mini-Circuits
    - **Url:** https://www.pololu.com/product/2573
    - **Price usd:** 36.49 + 8.95 + 11.31 or 111.57 + 5-10
    - **Verified:** так
    - **Alternative:** None verified
    - **Notes:** Pick the injector after measuring the LNB current: TCBT if 150 mA or less, else ZFBT-4R2GW+.
  28.
    - **Item:** QO-100 cone and gore horn materials
    - **Tier:** antenna kits (held add-on)
    - **Best seller:** Local metal supplier + 3M 1170 tape (DigiKey $35.70) or HVAC tape
    - **Url:** https://www.digikey.com/en/products/result?keywords=3M%201170%20aluminum%20foil%20tape
    - **Price usd:** 13-30 (estimate)
    - **Verified:** ні
    - **Alternative:** None
    - **Notes:** Measure the LNB neck and waveguide first.
  29.
    - **Item:** Inmarsat-C LNA: Nooelec SAWbird+ iO (cased, 100788) (HOLD)
    - **Tier:** antenna kits (held add-on)
    - **Best seller:** Nooelec
    - **Url:** https://www.nooelec.com/store/sdr/sdr-addons/sawbird/sawbird-plus-io-303.html
    - **Price usd:** 49.95
    - **Verified:** так
    - **Alternative:** The L-band patch already covers 1537-1545 MHz
    - **Notes:** Buy only after header-level discard works on recordings.
  30.
    - **Item:** LiteVNA 64 (Zeenko)
    - **Tier:** lab core
    - **Best seller:** Passion Radio (FR)
    - **Url:** https://www.passion-radio.com/analyzer-spectrum/lite-vna64-2730.html
    - **Price usd:** 210.88 (EUR 187.60 incl. FR VAT; about 175.73 ex VAT for export)
    - **Verified:** так
    - **Alternative:** Lab401 EUR 192 (vendor field DeepElec; not chosen)
    - **Notes:** 5 in stock. Bundle: male OSL, F-F, 2 cables. Conducted use only.
  31.
    - **Item:** tinySA Ultra+ ZS407
    - **Tier:** lab core
    - **Best seller:** Astroradio (ES), on the tinySA.org safe list
    - **Url:** https://www.astroradio.com/p/tinysa-ultra-analizador-de-espectro-plus/
    - **Price usd:** 247.18 (EUR 219.89 incl. 21% VAT; 204.28 ex VAT)
    - **Verified:** так
    - **Alternative:** Mirfield UK GBP 189.95 (limited stock); R&L $219.95 (out of stock)
    - **Notes:** In stock. Ignore the vendor's '12 GHz' claim. Order early: it gates the regulator decision.
  32.
    - **Item:** Noise source amplifier: Mini-Circuits ZFL-500+ (DIY N8DMT-type source)
    - **Tier:** lab core
    - **Best seller:** Mini-Circuits webstore
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=ZFL-500%2B
    - **Price usd:** 99.55 + box 5-10
    - **Verified:** ні
    - **Alternative:** ZFL-500LN+ $116.81 (verified, more than 100 in stock); used ZFL-500 about $20-40
    - **Notes:** ENR is characterised with the tinySA; NF results are relative.
  33.
    - **Item:** RF bench set: Nooelec pad kit, 2x 30 dB pads, 2x BLK-89-S+, 3x ANNE-50+, 3x 086-6SM+ (2 jumpers + 1 cut into E-field probes)
    - **Tier:** lab core
    - **Best seller:** Nooelec + Passion Radio + Mini-Circuits
    - **Url:** https://www.minicircuits.com/WebStore/dashboard.html?model=BLK-89-S%2B
    - **Price usd:** 47.95 + 29.68 + 40.52 + 44.52 + 50.01
    - **Verified:** так
    - **Alternative:** Mini-Circuits VAT-30W2+ $31.43 per 30 dB pad
    - **Notes:** BLK-89-S+ counted once (the SDR group also listed it). The female OSL is the bundled male OSL + F-F, so $0.
  34.
    - **Item:** SMA torque wrench 0.9 N·m + adapter set
    - **Tier:** lab core
    - **Best seller:** TOJOIN eBay store + RTL-SDR Blog SMA adapter set
    - **Url:** https://www.ebay.com/itm/354598266754
    - **Price usd:** 35.89 + 14.95-26.95
    - **Verified:** ні
    - **Alternative:** AliExpress ratcheting $51.49
    - **Notes:** Wrench seen only in a search snippet; confirm the listing before ordering.
  35.
    - **Item:** Spare RTL-SDR Blog Wideband LNA V2
    - **Tier:** lab core
    - **Best seller:** RTL-SDR Blog store
    - **Url:** https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/
    - **Price usd:** 19.95
    - **Verified:** так
    - **Alternative:** None
    - **Notes:** 208 in stock; 90 mA.
  36.
    - **Item:** Bench electronics: FNIRSI FNB58 Std, ANENG AN8008/9, Hantek 6022BE + fx2lafw LA, Raspberry Pi Debug Probe
    - **Tier:** lab core
    - **Best seller:** fnirsi.com, AliExpress (ANENG), The Debug Store, Adafruit
    - **Url:** https://www.fnirsi.com/products/fnb58
    - **Price usd:** 53.99 + 26-53 + 133-160 + 8-12 + 12.00
    - **Verified:** ні
    - **Alternative:** 6022BL on AliExpress $84-102 (store unconfirmed)
    - **Notes:** FNB58 Std, the 6022BE (GBP 100, VAT basis unclear) and the Debug Probe are verified. The ANENG store is unconfirmed.
  37.
    - **Item:** Pinecil V2, iFixit ESD mat, Anker 737, Waveshare MTT bench hub
    - **Tier:** lab core
    - **Best seller:** PINE64, iFixit (US/EU), Anker, The Pi Hut
    - **Url:** https://www.anker.com/products/a1289
    - **Price usd:** 25.99 + 34.95 + 109.99 + 24.64
    - **Verified:** так
    - **Alternative:** iFixit EU EUR 29.95
    - **Notes:** Anker (20 V/5 A PDO, in stock) and the hub (GBP 18.50) verified. The Pinecil and mat were not re-checked.
  38.
    - **Item:** Tools, spares kit, notebook and organiser
    - **Tier:** lab core
    - **Best seller:** Various
    - **Url:** https://www.ifixit.com/products/portable-anti-static-mat
    - **Price usd:** 165-260 (estimate)
    - **Verified:** ні
    - **Alternative:** Fuses, XT30s and pigtails only (about $25)
    - **Notes:** Not sourced.
  39.
    - **Item:** GPSDO: Leo Bodnar LBE-1420
    - **Tier:** lab extended
    - **Best seller:** Leo Bodnar Electronics (UK)
    - **Url:** https://www.leobodnar.com/shop/index.php?main_page=product_info&cPath=107&products_id=393
    - **Price usd:** 175.80 (GBP 132; VAT basis not stated)
    - **Verified:** так
    - **Alternative:** Bodnar Mini, same price, superseded
    - **Notes:** In stock; antenna included; ships worldwide.
  40.
    - **Item:** ADS-B: FlightAware Pro Stick Plus
    - **Tier:** lab extended
    - **Best seller:** The Pi Hut
    - **Url:** https://thepihut.com/products/flightaware-pro-stick-plus-usb-sdr-ads-b-receiver
    - **Price usd:** 69.92 (GBP 52.50)
    - **Verified:** так
    - **Alternative:** Uputronics 1090 MHz preamp GBP 44.39 ($59.12) on the spare V4L
    - **Notes:** Keeps the spare V4L a spare.
  41.
    - **Item:** RF sled: generic HMC7992 SP4T board + PE4302 + MCP23017 #2 + box/parts
    - **Tier:** lab extended
    - **Best seller:** Marketplace (unverified)
    - **Url:** https://www.walmart.ca/en/ip/HMC7992-Non-Reflective-SP4T-RF-Switch-Module-PCB-Material-0-1-6GHz-Frequency-Range-3V-5V-Power-Supply-45dB-Isolation-0-6dB-Insertion-Loss-58dBm-IIP3/4LT6JIAL4ULJ
    - **Price usd:** 99-158
    - **Verified:** ні
    - **Alternative:** Manual SMA swaps (free); EV1HMC7992LP3D $319.28 (rejected on value)
    - **Notes:** Qualify isolation (conducted) before use.
  42.
    - **Item:** SAWbird+ H1, FNIRSI DPS-150, Pelican 1450/Apache 3800
    - **Tier:** lab extended
    - **Best seller:** Nooelec, Elektor, various
    - **Url:** https://www.nooelec.com/store/
    - **Price usd:** 45-50 + 73-75 + 30-169
    - **Verified:** ні
    - **Alternative:** Reuse the helix/helicone
    - **Notes:** Not re-verified (the H1 URL tried returned 404).
  43.
    - **Item:** Airspy HF+ Discovery
    - **Tier:** HF chain
    - **Best seller:** ITEAD (official Airspy manufacturer partner), EU/US/CN warehouses
    - **Url:** https://itead.cc/product/airspy-hf-discovery/
    - **Price usd:** 169.00
    - **Verified:** так
    - **Alternative:** Moonraker $223.95 (snippet); AstroRadio EUR 214.17 = $240.75
    - **Notes:** Store API: in stock at all three warehouses.
  44.
    - **Item:** HF wire + Nooelec Balun One Nine v2 (100806) + thin coax/ferrites
    - **Tier:** HF chain
    - **Best seller:** Nooelec + local wire (or Tecsun AN-05)
    - **Url:** https://www.nooelec.com/store/balun-one-nine-v2.html
    - **Price usd:** 26.95 + 5-14.49 + 15-25
    - **Verified:** ні
    - **Alternative:** Moonraker AN-05 $14.49 (snippet; stock contradictory)
    - **Notes:** Balun price verified. HF only; bias locked off.
  45.
    - **Item:** Bonito Boni-Whip (BNC, bias tee included)
    - **Tier:** HF chain
    - **Best seller:** WiMo (DE)
    - **Url:** https://www.wimo.com/en/18067
    - **Price usd:** 178.73 (EUR 159 incl. VAT; 150.19 net)
    - **Verified:** так
    - **Alternative:** Moonraker $123.95 (search snippet only; page blocked)
    - **Notes:** Available from 20 Nov 2026. 9-15 V, about 14 cm, 189 g. Feed 12.5 V.
  46.
    - **Item:** Boni-Whip 12.5 V rail (LT3045 + LC + load switch + shield) and HF+ input selector relay + BNC-SMA lead
    - **Tier:** HF chain
    - **Best seller:** LCSC + part TBD
    - **Url:** https://www.lcsc.com/product-detail/voltage-regulators-linear-low-drop-out-ldo-regulators_analog-devices-lt3045emse-pbf_C580012.html
    - **Price usd:** 18-23 + 10-25 (estimate)
    - **Verified:** ні
    - **Alternative:** 'Connect X' prompt without a relay
    - **Notes:** Relay still unsourced.
  47.
    - **Item:** LimeSDR Micro M.2 2280 Basic + 2x MHF4L-SMA (Lime-conditional)
    - **Tier:** Lime-conditional
    - **Best seller:** Crowd Supply
    - **Url:** https://www.crowdsupply.com/lime-micro/limesdr-micro
    - **Price usd:** 267 + 12
    - **Verified:** так
    - **Alternative:** None
    - **Notes:** Pre-order, ships 15 Dec 2026. Full refund only before shipment.
  48.
    - **Item:** Lime-only parts: ADT-Link R44SF 5 cm, I-PEX 90435-001 tool, Samsung T7 1 TB
    - **Tier:** Lime-conditional
    - **Best seller:** ADT-Link webshop, DigiKey, B&H
    - **Url:** http://www.adt.link/product/R44SF.html
    - **Price usd:** 19 + 18.10 + 229.99-274.99
    - **Verified:** ні
    - **Alternative:** None
    - **Notes:** R44SF $19 verified (PCIe 3.0 x4, M-key to M-key). The T7 price is a snippet only; buy only if the Lime is kept.
- **Refuted offers:**
  1.
    - **Offer:** Arace Tech Q6A 12 GB $169 (and the other Arace variants)
    - **Why:** Sold out: Shopify .js shows every variant unavailable. It also lists an odd '16GB $119.50' variant. Not purchasable.
  2.
    - **Offer:** Ameridroid Q6A 12 GB $249.95 / 6 GB $169.95 (marked 'official_channel')
    - **Why:** Out of stock. Ameridroid is not on radxa.com/distributors (Allnet, Arace, TinyTronics, RS, SB Components and others are). Most expensive.
  3.
    - **Offer:** ALLNET Q6A 8 GB $159.99
    - **Why:** Sold out per Shopify .js.
  4.
    - **Offer:** TinyTronics Q6A at 'EUR 122.31 ex VAT ($137.49)' and 'ships outside the EU on request; UK minimum EUR 170'
    - **Why:** The delivery page lists only 26 EU destinations, so the non-EU claim is unconfirmed. EU consumers pay VAT; plan on EUR 148.
  5.
    - **Offer:** Arace UFS 128 GB $49
    - **Why:** Sold out (.js).
  6.
    - **Offer:** Passion Radio LiteVNA 64 'EUR 187.60 tax excl.'
    - **Why:** Page variables: base 219 incl. / 182.50 ex VAT, reduction 31.40 incl. So 187.60 is the VAT-inclusive price; the ex-VAT price is about EUR 156.33. Price corrected, offer kept.
  7.
    - **Offer:** WiMo Boni-Whip at $184.44, and AstroRadio HF+ at $248.44
    - **Why:** Converted at 1.16 USD/EUR. At 1.1241 they are $178.73 (net $150.19) and $240.75. Boni-Whip is not available until 20 Nov 2026.
  8.
    - **Offer:** Moonraker HF+ $223.95, Boni-Whip $123.95 'in stock', AN-05 $14.49
    - **Why:** Cloudflare 403 on my fetch too; undated search snippets only. Boni 'in stock' conflicts with WiMo's 20 Nov date. Unverified, not used as a planned price.
  9.
    - **Offer:** Mini-Circuits TCBT-2R5G+ as the SAWbird+ injector at a 250-300 mA TPS2553 limit, or as the LNB injector
    - **Why:** Datasheet: DC current 200 mA max, +25 V. TCBT-14+/14R+ are also 200 mA. Use only with a latch-off limit or loads of 150 mA or less; ZFBT-4R2GW+ (500 mA) otherwise.
  10.
    - **Offer:** SDR group's 'buy the SAWbird+ iO now because it lifts the Nooelec order over the $100 free-shipping line'
    - **Why:** NOAA+ + GOES+ + Flamingo+ = $124.85 already (core order $199.75). The iO is gated on header-level discard, not shipping.
  11.
    - **Offer:** 'No purchasable 70 cm band-pass / filtered preamp'
    - **Why:** Uputronics store lists the 440 MHz CubeSAT filtered preamp at GBP 51.59 (available).
  12.
    - **Offer:** AliExpress 'Zeenko' tinySA ZS407 $221.32 and LiteVNA 64 $212.63
    - **Why:** Store not confirmed as Zeenko 5800447; HIGH clone risk per tinySA.org.
  13.
    - **Offer:** R&L 'TINYSAULTRAPLUS' $169.95, Lab401 'TinySA Ultra+' EUR 163, Passion Radio 'TinySA ULTRA' EUR 168.36, Neven ZS-406
    - **Why:** Wrong model (ZS406, 5.4 GHz), not the ZS407.
  14.
    - **Offer:** R&L ZS407 $219.95, Neven ZS407, Switch Science ZS407, GOTRONIK LiteVNA/ZS407
    - **Why:** Out of stock or 'temporarily unavailable'.
  15.
    - **Offer:** Lab401 LiteVNA EUR 192
    - **Why:** Feed vendor 'DeepElec'. Not on any official list, and pricier than Passion Radio. Not chosen.
  16.
    - **Offer:** The Debug Store Hantek 6022BL GBP 110 ex VAT
    - **Why:** Product URL 404 (delisted); SainSmart marks it discontinued. AliExpress 6022BL listings ($84-158) have no confirmed store.
  17.
    - **Offer:** AliExpress female OSL kits ($68.75; $10.55)
    - **Why:** Generic, store and gender unconfirmed. The bundled male OSL + F-F adapter is free.
  18.
    - **Offer:** Zeenko 3-probe EMI set, Com-Power PS-500, generic E/H probe sets, YouLoop
    - **Why:** Contain H-field loops; excluded by the no-loop rule.
  19.
    - **Offer:** Generic HMC7992 SP4T board on Walmart.ca, CA$20.49
    - **Why:** Snippet only, marketplace, isolation claim of 45 dB unproven. CAD converted at 0.72 vs 0.7069 ($14.48). Extended-only experiment after a conducted check.
  20.
    - **Offer:** ADI EV1HMC7992LP3D $319.28 and Mini-Circuits ZSWA4-63DR+ $307.32
    - **Why:** EV1 is real (2 in stock) but rejected on value. ZSWA4 has 0 stock.
  21.
    - **Offer:** Samsung T7 1 TB at $274.99 (Samsung US) / $229.99 (B&H)
    - **Why:** Search snippets only (403). Deferred to the Lime gate; re-price then.
  22.
    - **Offer:** IP2368 board at Newegg $15.79, NKON P50B EUR 6.75, TOJOIN wrench $35.89
    - **Why:** Unverified (403/Cloudflare or snippet only). Use as estimates; confirm live before ordering.
  23.
    - **Offer:** Adafruit #610 DC jack, Adafruit 6011 A2 microSD, Allnet RA019 UFS reader, Technofix Bullseye, Mini-Circuits 141-6SM+, LCSC IP2368 chip, TI-store TPS2553
    - **Why:** Out of stock or backorder (Adafruit API: 0 and -3).
  24.
    - **Offer:** Lime decision 'on 31 Jan 2027' as a free option
    - **Why:** Crowd Supply refunds pre-orders in full only before shipment (ships 15 Dec 2026). After delivery it is a 30-day return less a restocking fee of $20 or more.
- **Totals usd:** USD before shipping, import VAT and duty. Range = low (EU-optimised or verified-cheapest) to high (worldwide shipper or upper estimate).
  
  - CORE DEVICE (handheld, 4S, no Lime): $1,138-1,278.
    - Compute, display and HMI: $457-491.
    - Power, GNSS/IMU and mechanics: $349-416.
    - Internal RF front end: $332-370 (3x V4L, NOAA+, Flamingo+, Uputronics 440, 3x TCBT, leads, LAB I/O).
  - ANTENNA KITS:
    - Region-neutral: $218-285 (L-band patch, L1/L5 patch, GOES+, 2 dipole kits, DIY whips, helix, Yagi and helicone).
    - Held QO-100/Inmarsat add-on: $155-277 (Bullseye, 13.2 V supply, injector, horn, iO). The injector choice sets the high end.
  - LAB CORE: $1,347-1,740. The new noise-source amp ($105-127) replaces the earlier $20-40; no H-probes; female OSL is $0.
  - LAB EXTENDED: $463-697. Covers the LBE-1420, Pro Stick Plus, sled, H1, DPS-150 and case; excludes the calibrated 346 head.
  - HF CHAIN: $368-463. Covers the HF+ $169, wire, balun, coax, Boni-Whip $124-179, 12.5 V rail and the selector-relay estimate.
  - LIME-CONDITIONAL (in no total): $316 for the Lime Basic + $18 shipping + 2 MHF4 + R44SF + I-PEX tool; plus a T7 at $230-275 (unverified); plus a $74 cavity if S-band.
  
  Roll-ups:
  - Handheld + antennas + HF: $1,724-2,025.
  - Adding the QO-100 add-on and lab core: $3,226-4,042.
  - Everything except the Lime: $3,689-4,739.
  
  Single-seller first orders:
  - ALLNET bundle (board, UFS, case, RTC cell, 64 GB SD): $283.73.
  - TinyTronics EU bundle (board, UFS, BMS): EUR 214 = $240.56.
  - Nooelec: $199.75, free shipping.
  - RTL-SDR Blog: $263.55.
  - Adafruit: $99.
  
  Model: computed in /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/sourcing_calc/bom.py. About 69% of the low total uses prices re-seen live on 18 Oct 2026.
- **Shopping plan:**
  - 1. Today (18-20 Oct), stock-risk items first:
  - Q6A 12 GB plus UFS 128 GB. EU: one VAT-paid TinyTronics order (board EUR 148 + UFS EUR 58 + Daly BMS EUR 8; the UFS comes in 2-4 weeks, so boot from microSD meanwhile). Elsewhere: one ALLNET order (board $189.99, UFS $65.90, Armor case $9.90, RTC cell $0.95, 64 GB SD $16.99).
  - Re-check stock at checkout: both were verified available on 18 Oct.
  - 2. Today: the bring-up kit for the W1-2 / NPU Phase 0 gates, as one Adafruit order of about $99: Debug Probe, USB-A-to-C cable, microSD reader, 2x CH334F, MCP23017, INA228, BNO085, fan, slim HDMI, knobs.
  - 3. Today: 3x V4L ($113.85; R828S end of life) from the official channel. Non-EU: the webstore. EU: the official eBay or AliExpress 4523039 store. In the same order: 2 dipole kits, the L-band patch set, the pigtail and SMA adapter sets, and the spare LNA V2.
  - 4. Today: send Wisecoco the written questions: USB-HID VID:PID, bonding/AR, input V/I, EDID, the 127.9 MHz/51.7 Hz mode, glove mode, package contents. Pay by PayPal only after satisfactory written answers. With no clear answer in about 7 days, order the 4D 4DHDMI-70-1280-800-CT-EAR-1000 from DigiKey ($128.95; 13 in stock, 4-week lead after that).
  - 5. Lime: if the user wants it, place the refundable Crowd Supply store pre-order ($267 worldwide) now to hold a slot. Put the keep/cancel decision in the calendar for 1 Dec 2026, before the 15 Dec shipment. Buy nothing Lime-only before that.
  - 6. Week 1, power: order all Pololu parts in one order because stock is 'Rationed': D36V50F12, D36V28F5, 2x #2813 (plus a spare D36V50F12 if allowed). LCSC order: LT3045 x2, TPS2553 x10 (also check the TPS2553-1 latch-off variant), fuses, holder, PTC, XT30, jacks. 5x P50B from an established local retailer. 2-3 IP2368 boards for burn-in.
  - 7. Week 1, instruments that gate decisions: tinySA ZS407 (Astroradio or another official-list seller near you), FNB58 Std, AN8008/9. These run the terminated-floor spur A/B (keep or replace the D36V50F12) and measure the HF+, LNB and Boni-Whip currents.
  - 8. Week 1-2, RF and mechanics:
  - Nooelec ($199.75, free shipping): NOAA+, GOES+, Flamingo+, Balun One Nine v2, pad kit.
  - Uputronics 440 MHz CubeSAT preamp (GBP 51.59).
  - Waveshare: LC76G, 2x RP2040-Zero, L1+L5 antenna.
  - DigiKey: PEC11R x3, KSC641J x10, ferrites, TCBT-2R5G+ x3.
  - ASA filament, CNC Kitchen inserts and screws, Gelid pads, strap.
  - 9. Week 2-3, lab core and HF:
  - Airspy HF+ from ITEAD (choose the nearest warehouse).
  - LiteVNA 64 (Passion Radio, 5 left) plus 2x 30 dB pads.
  - Mini-Circuits: 2x BLK-89-S+, 3x ANNE-50+, 3x 086-6SM+, ZFL-500+.
  - Anker 737, Pinecil V2, iFixit mat, Hantek 6022BE plus an fx2lafw LA, MTT bench hub.
  - Torque wrench, after confirming the TOJOIN listing live.
  - 10. On arrival:
  - Q6A: 12 h stressapptest plus memtester and 50-100 cold boots. Allnet takes back only unused items within 7 days, so treat failures as warranty claims and keep the UART logs.
  - UFS: read the chip ID (0x01CE).
  - Authenticity: check the V4L (case, labels, 'RTL-SDR Blog V4 Lite Detected'), the HF+ dealer invoice and the tinySA/LiteVNA seller.
  - Cells: test capacity, IR and weight.
  - Passive parts: VNA-check every generic pad and adapter (conducted).
  - 11. From 20 Nov 2026: Boni-Whip (WiMo EUR 159, or Moonraker if live stock is confirmed) with its LT3045 12.5 V rail. Choose and buy the HF+ input selector relay and a BNC-SMA lead before enabling AIS on the HF+.
  - 12. 1 Dec 2026: Lime keep/cancel. Only if kept: R44SF 5 cm ($19, ADT webshop), the I-PEX 90435-001 tool, the 2x MHF4L-SMA on the same Crowd Supply order, and a re-priced T7 1 TB. If cancelled, keep the CPU7 and RAM-ring plan in the no-Lime state.
  - 13. When the user's region is confirmed inside the Es'hail-2 footprint: Bullseye LNB ($29.95; Technofix is already out of stock, so do not wait long), S18V20AHV + #2813, LC/PTC/F-SMA parts and horn materials. Measure the LNB current at 13.2 V, then buy the injector: TCBT-2R5G+ if 150 mA or less, else ZFBT-4R2GW+ ($111.57).
  - 14. After header-level discard of non-SafetyNET packets is demonstrated on L-band patch recordings: SAWbird+ iO ($49.95). If the discard cannot be done, drop the Inmarsat-C profile and do not buy it.
  - 15. Lab extended last, after the core procedures pass: LBE-1420 (GBP 132), Pro Stick Plus (GBP 52.50), the qualified sled parts, SAWbird+ H1, DPS-150, and the case.
  - 16. Deferred, watch prices: V30/A2 microSD or the T7 while NAND prices stay high (buy only for the Lime, or once the UFS fills). Consider a 4th V4L only if the R828S stock warning returns and a second spare is wanted.
- **Confidence:** medium

