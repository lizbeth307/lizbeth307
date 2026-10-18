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

