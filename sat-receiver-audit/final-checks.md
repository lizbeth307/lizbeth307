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

## integration:lens4 (run `wf_221684d9-b6c`)

- **Lens:** RESOURCES + LAB SYSTEM + MECHANICAL: Q6A RAM tier vs the IQ ring and apps; CPU core allocation and RT pinning; storage (UFS, T7 or microSD/NVMe, rolling caps, rollback); the LimeSDR keep-or-drop and what depends on it; case layout, display bonding and sun hood, connectors, the two antenna kits, the bench kit, packed volume and weight, field setup time
- **Issues:**
  1.
    - **Area:** RAM / IQ ring
    - **Components:**
      - Q6A 12 GB
      - labrx RAM ring
      - inferd-htp/cpu
      - T2 trainer
      - SatDump
      - SDRangel
      - OpenWebRX+
      - Lab Shell
    - **Problem:** Four incompatible ring sizes, two of which over-commit the 12 GB board. npu_training final fixes the ring at 6 GiB ('never shrunk live') and adds the 2 GiB trainer plus 1-1.35 GiB inferd. storage final wants an 8 GiB mlocked ring. The register says 4 GiB with training (Lime) and 1.5 GiB or less without the Lime. lab_ui_hf assumes about 4 GiB, compute 2-4 GiB. My model (app RSS figures are estimates; nothing has been measured on the Q6A) leaves -1.2 to +1.1 GiB free in Train mode with the 6 GiB ring. Every mlocked byte is unreclaimable, so the OOM killer would go after SatDump or the Shell.
    - **Severity:** major
    - **Fix:** One ring per hardware set, sized once at boot by labrx: 1.5 GiB without the Lime (98 s of 2xRTL+HF+ at 16.4 MB/s), 4 GiB with the Lime (19.2 s at 56 Msps ci16, 38 s ci8). Add an exclusive 'Burst' profile that stops the trainer, OpenWebRX+, SDRangel and Expert GUIs, then mlocks a second 3 GiB segment, failing gracefully. That gives 7 GiB, about 30 s of 160 Msps while draining to the T7. Delete the 6 GiB and 8 GiB figures. Measure MemTotal and the RSS of each app in the W1-2 gates.
    - **Evidence:** npu_training.json final.budgets ('IQ ring: 6 GiB with training enabled ... 8 GiB without'); storage.json verify.final_recommendation ('8 GiB mlocked RAM ring'); report_research.json decisions #46. Visible RAM measured: 6 GB board 5609 MB (sbc-bench KBw_, kernel 6.16.7), 8 GB board 7604 MiB (Geerling #85), so a 12 GB board shows about 11.3-11.4 GiB (my extrapolation). Model: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lens_rlm/calc/budgets.py
    - **Fix cost:** $0 (labrx config and text edits)
    - **Sources:**
      - https://raw.githubusercontent.com/ThomasKaiser/sbc-bench/master/results/KBw_.txt
      - https://github.com/geerlingguy/sbc-reviews/issues/85
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/storage.json
  2.
    - **Area:** RAM tier / purchase
    - **Components:**
      - Radxa Dragon Q6A 8 GB vs 12 GB
    - **Problem:** small_antenna_stack downgrades to the 8 GB board to save $50-74, but the saving is now EUR 22.31 ex VAT at one EU seller. My model (estimates, unmeasured) shows the 8 GB board (7.43 GiB visible) is already over-committed in the no-Lime 'train between passes' scenario: -0.2 to +2.2 GiB free with a 1 GiB ring. RAM cannot be added later.
    - **Severity:** major
    - **Fix:** Buy the 12 GB board now: TinyTronics NL at EUR 122.31 ex VAT / EUR 148 incl. VAT, 10+ in stock, fetched 18 Oct 2026; or Allnet at $189.99, in stock today. Strike the 8 GB downgrade from small_antenna_stack.
    - **Evidence:** TinyTronics 12 GB page fetched 18 Oct 2026: EUR 148.00 incl. / EUR 122.31 excl. VAT, '10+ pieces in stock'. compute.json verify: 8 GB EUR 121 incl. / EUR 100 ex VAT. Allnet products/radxa-dragon-q6a.js fetched today: 12 GB 18999 available, 8 GB 15999 unavailable, 6 GB 14999 available. This settles summaries #75 vs #86.
    - **Fix cost:** +EUR 22 ex VAT over the 8 GB board; about EUR 40 less than Allnet's $189.99
    - **Sources:**
      - https://www.tinytronics.nl/en/development-boards/single-board-computers/radxa-dragon-q6a-qcs6490-12gb
      - https://shop.allnetchina.cn/products/radxa-dragon-q6a.js
  3.
    - **Area:** CPU allocation / RT
    - **Components:**
      - CPU0-3 A55
      - CPU4-6 A78
      - CPU7 A78
      - lime:Rx0
      - labclassify
      - T2 trainer
      - SatDump
      - loggers
    - **Problem:** There are four core plans: npu_training (CPU7 RX; CPU4-6 FFT fallback, decoders and trainer), lab_ui_hf final (labclassify on CPU0-3, CPU7 always isolated), wideband verify (lime:Rx0 on cpu4-6 at FIFO 70) and storage/compute (taskset 7, chrt -f 50 or -f 10). Load model (estimates): an LRPT+HRPT pass with two SatDump instances, labrx and the P4 loggers (readsb, AIS-catcher, auto_rx) needs about 2.8-4.5 A78 cores. With the Lime, CPU7 is isolated and only 3 A78 cores remain. If VkFFT on the Adreno 643 fails (untested), the LIME-W CPU FFT fallback needs about 2 more A78 cores. A Lime wideband survey and a pass then cannot run together. Without the Lime, CPU7 is idle unless it is released. One more risk to check: if lime:Rx0 busy-polls, the default RT throttle (950 ms per 1 s) leaves 50 ms gaps, about the depth of the LA9310 FIFO.
    - **Severity:** major
    - **Fix:** Use one table. CPU0-3: UI, daemons, inferd-htp host, Stage-2 embedder, ORT CPU fallback (CPUQuota 100%). CPU4-6, or CPU4-7 without the Lime: labrx, engines and loggers. The T2 trainer gets AllowedCPUs 4-6/4-7, SCHED_IDLE and nice 19, and runs only between passes. CPU7 is isolated with FIFO 50 only in the Lime kernel-cmdline variant, with the Lime MSI moved off CPU7. labd pauses P4 loggers during Lime passes. Add 'VkFFT N=65536 on Turnip at 854 FFT/s or more' and 'zero limeTRX losses for 60 min with an LRPT+HRPT pass running' to the Lime gate. Check whether lime:Rx0 blocks or polls; if it polls, measure losses with RT throttling on.
    - **Evidence:** npu_training.json final.budgets 'Core plan'; lab_ui_hf.json final.ui_system.resource_arbitration 'CPU classes'; report_research.json decisions #19; storage.json verify fix ('taskset -c 7 chrt -f 50'); compute.json verify ('chrt -f 10'); npu_training 'CPU-fallback FFT: N=65536 ... about 2 A78 cores'
    - **Fix cost:** $0 (unit files and cmdline variant); about 1 day of bench time
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/wideband_sdr.json
  4.
    - **Area:** USB ports and bandwidth
    - **Components:**
      - blue USB 3.1
      - FE1.1s hub
      - Adafruit CH334F
      - RTL-A
      - RTL-B
      - HF+
      - HMI RP2040
      - IMU puck
      - LAB USB
      - T7
    - **Problem:** The 'Lime-agnostic' map runs out of ports. With the Lime, the T7 takes the blue port and RTL-A must move to the CH334F. If UART7 cannot be enabled, the USB devices are RTL-A, RTL-B, touch, HMI RP2040, HF+ and LAB, which is 6 devices for exactly 6 endpoints (3 FE1.1s ports minus 1 for the CH334F, plus 4 CH334F ports). That leaves no port for the FT232RL GNSS/PPS fallback, the RP2040 counter, an Airspy Mini, a Pluto or a puck on USB-CDC. radio_lab also limits the FE1.1s to '3 continuous streams', while the 4th-V4L monitor configuration runs 4 streams.
    - **Severity:** major
    - **Fix:** 1) The IMU is always relayed through the HMI RP2040's second UART (as lab_ui_hf specifies), so it never takes a USB port. 2) Add a second Adafruit CH334F behind CH334F #1 H3: LAB USB plus 3 spares. Hub depth to a bench instrument becomes 4, within USB 2.0's limit of 5. 3) Replace the '3 streams' rule with an aggregate cap of 25 MB/s on the FE1.1s tree (about 65% of the practical 35-40 MB/s). 4 streams are 18.2 MB/s. Test 30 min with zero dropped samples.
    - **Evidence:** report_research.json decisions #129 (map; H2 IMU 'if not on UART'); radio_lab.json final.usb_power_case_plan (H1-H4 full; '3 continuous streams'); lab_ui_hf.json final.stack_changes ('relays the BNO085 over its second UART'); minute-log 05:19 (interfaces lens: 'CH334F full ... with Lime+T7 RTL-A nowhere')
    - **Fix cost:** $4.95 plus about 0.1-0.25 W; 20 cm3
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  5.
    - **Area:** 5 V rails with the Lime
    - **Components:**
      - VCC_5V_PERI (SGM40666AS, about 17 W)
      - LAB 5 V (D36V28F5, 3.2 A)
      - T7
      - LimeSDR Micro
      - SAWbird+ injectors
    - **Problem:** With spec allowances, the Lime set on VCC_5V_PERI is Lime 8.25 + T7 about 4.5 + RTL-B 1.3 + tee 0.35 + fan 1 = 15.4 W (90% of about 17 W), or more if Wi-Fi is on. The power lens reports 20.6 W with both RTLs on the board. Moving RTL-A and all injectors to LAB 5 V puts that rail at about 1.9-2.2 A (CH334F x2 0.1, HMI 0.05, IMU 0.03, HF+ 0.1-0.2 unpublished, RTL-A 0.27-0.35, 2 SAWbird+ 0.36, LNA V2 about 0.1, LAB port up to 1.0), above the planned 2 A fuse.
    - **Severity:** major
    - **Fix:** Keep the T7 on the blue port's own VBUS. Put RTL-A (Lime case), the HF+ and all injectors on LAB 5 V. Fuse LAB 5 V at 3 A (the regulator is rated 3.2 A) and cap the LAB port at 0.8 A in field mode. Measure each USB device with the FNB58 and the Lime 3.3 V draw. Accept the Lime only if the measured VCC_5V_PERI sum is 14 W or less.
    - **Evidence:** report_research.json decisions #62 (17 W, Lime allowance 8.25 W); storage.json verify ('T7 (under 1 A)'); minute-log 05:16 and 05:19 (power lens 20.6 W; LAB 5 V 2.2-2.4 A sum of limits)
    - **Fix cost:** $0-1 (fuse value); measurement time
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
      - /home/user/lizbeth307/sat-receiver-audit/minute-log.md
  6.
    - **Area:** Storage / rollback
    - **Components:**
      - Radxa UFS 128 GB
      - Samsung T7 1 TB
      - lab-snap
      - offline update bundle
    - **Problem:** Rollback snapshots ('lab-snap' ext4 on the T7) and the offline update path ('insert the T7 with a GPG-signed bundle') both depend on a drive that is bought only if the Lime is kept. The no-Lime build would have no rollback, while self-test plus rollback is a stated design rule. A removable USB 3 drive is also a weak rollback medium: it is a known jammer near the GNSS and L-band chain.
    - **Severity:** major
    - **Fix:** Use an A/B root on UFS in every variant: ESP 1 GiB, root A 24 GiB, root B 24 GiB, with /etc/kernel/tries boot counting and a rescue entry. Updates go to the inactive root and are blessed after self-test. The T7 or SD card keeps only data plus a second snapshot copy. Update bundles come from any USB stick on LAB USB.
    - **Evidence:** lab_ui_hf.json final.ui_system.packaging_and_updates (steps 1 and 3 use the T7); stack_changes 'STORAGE: the T7 gets an ext4 lab-snap partition'; report_research.json decisions #35 and #72; gnss_imu decision #82 (USB 3 jams GNSS within about 2 m)
    - **Fix cost:** $0 (48 GiB of UFS)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  7.
    - **Area:** Storage capacity / retention
    - **Components:**
      - UFS 128 GB
      - microSD
      - 2230 NVMe
      - T7
    - **Problem:** No file has a combined partition or rolling-cap plan. After the A/B root, the 20 GB NPU quota, the local apt repo and map tiles, UFS keeps only about 35-42 GiB for recordings: 1.0-1.2 h of dual-RTL raw (36.9 GB/h) or 0.6-0.7 h with the HF+ cf32 added (59 GB/h). lab_ui_hf sends HF+ raw (22 GB/h) to UFS, and small_antenna_stack still claims 'about 5 h on UFS'.
    - **Severity:** minor
    - **Fix:** Adopt the storage table in budget_tables. Products are kept by default. Unpinned raw is deleted after the decoder oracle runs. Raw caps: UFS 30 GiB rolling; microSD about 200 GB / 14 days; T7 400 GB NPU raw / 14 days plus 300 GB captures. labrx refuses a raw start that its cap cannot hold.
    - **Evidence:** budgets.py model; report_research.json decisions #73; small_antenna_stack.json stack.display_power_mechanical_impact ('about 5 h of raw IQ at 18.4 GB/h')
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lens_rlm/calc/budgets.py
  8.
    - **Area:** Boot robustness with data media
    - **Components:**
      - SPI firmware 251013/260120 boot order
      - microSD
      - NVMe
      - LAB USB stick
    - **Problem:** The firmware boot order is USB > SD > NVMe > eMMC > UFS. A data microSD, NVMe or update stick carrying an ESP (for example, a reused rescue card) would boot instead of UFS in the field.
    - **Severity:** minor
    - **Fix:** Data media are ext4 or exFAT with no ESP. The rescue card is kept outside the case and labelled. Acceptance test: 20 cold boots with the data card and a LAB USB stick inserted all land on UFS.
    - **Evidence:** storage.json forums known_fix ('boot order USB > SD > NVMe > eMMC > UFS')
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/storage.json
  9.
    - **Area:** Case envelope and HMI
    - **Components:**
      - ASA shell
      - Al mid-plate
      - Wisecoco/4D panel
      - main encoder 30-35 mm knob
      - volume encoder
      - 6 sealed keys
      - HF+ can
      - selector relays
      - CH334F/LAB interface
    - **Problem:** mechanical_thermal's 205-215 x 130-140 x 50-55 mm, 1.2-1.4 kg predates the HF+ Discovery and its can, the HF+ input selector, the RTL input selectors and internal VHF LNA bay, the LAB interface, the second V4L, the speaker and the HMI (a 30-35 mm main knob, a second encoder and 6 keys of 12 mm or more at 13 mm pitch). A right-hand HMI column (38-42 mm) beside the 164.2 mm glass gives 214-218 x 131-141 mm. My parts-volume model (estimates) is 0.79-1.03 L, which is 58-75% of a 215x135x55 interior. That is above the roughly 50% that hand-wired RF builds manage. Also, the pack geometry differs between power.json (flat 86x71x22 mm) and mechanical (46x25x150 mm).
    - **Severity:** major
    - **Fix:** Plan for about 220-225 x 135-140 x 55-60 mm and 1.2-1.5 kg without the Lime (1.35-1.65 kg with it), using a right-hand HMI column. Do the CAD layout from Radxa STEP v1.21 and the measured panel before printing. Use the 46x25x150 mm pack. Make the shell parametric. Mirror the hardware column for left-handers by reprinting, not with soft keys.
    - **Evidence:** mechanical_thermal.json verify.issues (thickness stack 50-55 mm, plate 140 g); lab_ui_hf.json final.stack_changes ('Main tune/focus push-encoder with a 30-35 mm knob', 'Six sealed keys of at least 12 mm at 13 mm or more pitch', HF+ can); report_research.json decisions #70 ('footprint has not been re-derived for 2 encoders and 6 keys'); model /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lens_rlm/calc/mech.py
    - **Fix cost:** $0 design; about $10-27 for an extra ASA print
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/mechanical_thermal.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  10.
    - **Area:** Connectors / panel
    - **Components:**
      - RF bulkheads
      - F port
      - HF post
      - GNSS SMA
      - USB-C charge
      - LAB USB
      - LAB BUS
      - audio
      - IMU puck lead
    - **Problem:** No file has a single connector list. Bulkheads appear in four files under different names. The IMU puck (on the boom, UART to the HMI RP2040) has no case connector. The source of the HF+ 'VHF bus' (for AIS) is undefined. The completeness lens notes that each RTL has one SMA but 2-4 antenna sources, and that there is no IP target. The total is 11-14 case penetrations.
    - **Severity:** major
    - **Fix:** Freeze the panel. Top (antenna) edge: VHF/UHF SMA (RTL-A chain, no bias out), L-BAND SMA (RTL-B, 5 V via TPS2553), LNB F (13.2 V), HF SMA plus ground post, GNSS SMA (3.3 V active); with the Lime add LIME RX1/RX2 SMA and an optional REF IN. Bottom (noisy) edge: IP2368 USB-C (the only power input), capped LAB USB-A, 6-pin locking LAB BUS, 3.5 mm audio, and the T7 lead exit (Lime only). Back: captured 1/4-20 nut, strap lugs, 4-pin locking IMU puck socket. Internal relays: RTL-A selects VHF/UHF chain, HF+ VHF bus or 50 ohm; RTL-B selects L-BAND, LNB IF or 50 ohm. Pitch 20 mm or more for glove and wrench clearance: 5 RF ports = 100 mm, 8 = 160 mm on a 215 mm edge.
    - **Evidence:** radio_lab.json integ.internal_vs_external and final.usb_power_case_plan; lab_ui_hf.json final.stack_changes ('HF SMA bulkhead, plus a ground/counterpoise post'); small_antenna_stack.json final.revised_stack (mechanical row); minute-log 05:12 (completeness lens: no input routing, no IP target)
    - **Fix cost:** About $15-30 (two latching SP3T relays, a 4-pin locking connector, extra bulkheads; estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
      - /home/user/lizbeth307/sat-receiver-audit/minute-log.md
  11.
    - **Area:** Two antenna kits: VHF front-end topology
    - **Components:**
      - patch/chip tier whips
      - foldable V-dipole
      - crossed Yagi (hairpin DC short)
      - Flamingo+ FM
      - SAWbird+ NOAA
      - LNA V2 + 70 cm BPF
    - **Problem:** The two tiers need opposite topologies on the same RTL-A input. The patch tier puts the 'LNA directly behind its bulkhead, never on a remote lead'. The foldable tier puts the FM filter and SAWbird+ NOAA at the feed, with a 5 V injector at the SDR. The 'FM filter ahead of any gain' rule then needs two Flamingo+ and two SAWbird+ NOAA. Bias rules also multiply: the Yagi feeds are DC shorts.
    - **Severity:** major
    - **Fix:** Use one internal VHF/UHF front end for both kits: VHF/UHF bulkhead, then Flamingo+ FM, then a relay to either SAWbird+ NOAA (137 MHz) or 70 cm BPF + LNA V2 (145.8/435 MHz), with a third throw to the HF+ VHF bus. External VHF leads stay unpowered (bias permanently off on that port). Penalty of 1-2 m RG316 (0.3-0.6 dB) ahead of the LNA at 137 MHz: 0.06-0.36 dB SNR with Ta of 565-1830 K (my model, ITU-R P.372 galactic and rural values). L-band LNAs stay at the feed (1-1.5 dB/m coax loss, cold sky).
    - **Evidence:** report_research.json decisions #85, #96, #101, #113; small_antenna_stack.json final.revised_stack; foldable_antennas.json final.foldable_kit; mech.py SNR calculation
    - **Fix cost:** Saves $74.90 (a second Flamingo+ at $24.95 and a second SAWbird+ NOAA at $49.95); one more relay throw, about $3-5
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/small_antenna_stack.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
  12.
    - **Area:** Antenna kits: shared L-band parts
    - **Components:**
      - 4-turn RHCP helix
      - patch-tier 20 cm disc
      - helicone 18 cm base disc
      - SAWbird+ GOES/iO
    - **Problem:** The patch tier mounts the 4-turn helix on a 20 cm disc. The foldable helicone uses an 18 cm base disc whose petals are cut for 18 cm. That is two discs and two gain sets for the same helix (the register already flags 10.2-10.9 vs 11.6-12.0 dBic).
    - **Severity:** minor
    - **Fix:** Use one 18 cm, 1.5 mm Al disc as both the patch-tier helix ground plane and the helicone base, with the same 4-turn helix and the same SAWbird+ mount. The patch tier loses an estimated 0.3-0.5 dB of aperture limit against 20 cm (model; NEC re-run needed). This saves a part and makes patch-tier results transfer to the helicone.
    - **Evidence:** small_antenna_stack.json final.revised_stack (4-turn on 20 cm disc); foldable_antennas.json final.foldable_kit (18 cm disc, 'no-fold fallback: 4-5 turn helix on an 18 cm plate, 11.6-12.0 dBic'); report_research.json decisions #117
    - **Fix cost:** Saves about $5-10 and 100-150 g
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
  13.
    - **Area:** Packing, volume and weight
    - **Components:**
      - field sling/backpack
      - foldable kit
      - HF kit
      - Boni-Whip mast
      - mini tripod
      - Pelican 1450 lab case
    - **Problem:** radio_lab still uses the superseded antenna tier: antennas 2.5-3 L / 0.6-1.0 kg, sling 3.0-3.6 kg, and 'handheld and antennas fit along the Pelican'. The foldable kit is 6-6.5 L (a 35x25x10 cm pouch) and 1.3-1.8 kg with the LNB, LNAs and jumpers. The supports (mini pan-tilt tripod, a mast of 2 m or more for the Boni-Whip) are not counted anywhere. Model (estimates): field load about 15.8 L and 5.1-7.0 kg (4.2-5.8 kg without the HF kit and mast), so a sling is not enough. Pelican: core+extended+HF is 8.8 L (61% of 14.5 L); adding the handheld gives 72%, which will not close with dividers. Loaded case 8.2-9.1 kg, above the 7-8 kg cabin limits of many airlines.
    - **Severity:** major
    - **Fix:** Use a 15-20 L daypack for the field tier: handheld, foldable pouch, HF kit, field pouch, tripod, mast. The Pelican carries the bench kit only. Instruments with Li cells (tinySA, LiteVNA), the 88.8 Wh bank and the 72 Wh pack travel in the cabin bag; the Pelican can be checked. Rewrite the packing and weight tables.
    - **Evidence:** radio_lab.json final.usb_power_case_plan and totals; foldable_antennas.json final.total_packed_volume_and_weight; report_research.json decisions #71; mech.py model. Pelican dimensions and weight are from the radio_lab file, unverified (pelican.com returned 403).
    - **Fix cost:** About $30-60 daypack, $20-50 mini tripod, $15-30 sectioned mast (estimates, unverified)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
  14.
    - **Area:** Display bonding, panel choice and thermal path
    - **Components:**
      - Wisecoco 7in FHD
      - 4D Systems 4DHDMI-70-1280-800-CT-EAR-1000
      - sun hood
      - display blower
    - **Problem:** The case front cannot be designed: Wisecoco bonding, glass outline (164.2x98 mm is inferred), touch path and input supply are all unconfirmed. An air-gapped 2000-nit panel (1.5:1 at 100 klx) is worse than the bonded 1000-nit 4D (1.7:1). The 4D now has a world price ($128.95 DigiKey, 13 in stock per the P2 procurement note), about the Wisecoco's $132, but its 1280x800 has no clean pixel clock between 65 and 90 MHz. The files also disagree on the hood (15-25 mm in display.json, 25-35 mm in display_market and mechanical) and on airflow (display_market: panel air 'into the Q6A heatsink'; mechanical verifier: two separate paths).
    - **Severity:** major
    - **Fix:** Give Wisecoco one week for written answers on bonding, HID VID:PID, EDID, input V/A and the 51.7 Hz mode; otherwise order the 4D and budget labd's per-profile modeset table. Leave the bezel parametric until the panel is on the bench. Hood: 30 mm, hinged, folds flat as a lid (about 5 mm, 40-80 g estimate). Airflow: two separate paths per the verifier; display air must never pre-heat the Q6A fins.
    - **Evidence:** display_market.json final.verdict, sunlight_measures and acceptance_tests; display.json research ('15-25 mm 3D-printed sun hood'); mechanical_thermal.json verify.issues (two parallel paths); minute-log 05:12 (4D $128.95 DigiKey); report_research.json decisions #78
    - **Fix cost:** $0 (decision and sequencing); 4D about -$3 vs Wisecoco
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/display_market.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/mechanical_thermal.json
  15.
    - **Area:** Sun hood vs auto-dimming
    - **Components:**
      - VEML7700
      - RP2040 dimmer
      - sun hood
    - **Problem:** The lux sensor is placed 'facing the same way as the screen', which puts it inside the 25-35 mm hood. In full sun it would read the hood's shade and dim the panel exactly when full brightness is needed.
    - **Severity:** minor
    - **Fix:** Mount the VEML7700 on the outer top face of the bezel, outside the hood aperture. Alternatively add a reed or hall 'hood open' input that shifts the dimming curve.
    - **Evidence:** display_market.json final.sunlight_measures ('Auto-dim from a VEML7700 behind a diffuser facing the same way as the screen'; 'Hood: 25-35 mm deep ... hinged so it folds down as a lid')
    - **Fix cost:** $1-3
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/display_market.json
  16.
    - **Area:** Tripod/boom mount
    - **Components:**
      - 2 mm Al mid-plate
      - 1/4-20 mount
    - **Problem:** mechanical final allows 'a captured nut, or a thread tapped in the aluminium plate'. A 1/4-20 thread (1.27 mm pitch) in 2 mm aluminium engages only 1.57 threads, too few for a 1.2-1.6 kg device on a boom.
    - **Severity:** minor
    - **Fix:** Use only a captured 1/4-20 nut, or a press-in steel insert in a bonded boss of 6 mm or more. Never a tapped 2 mm plate.
    - **Evidence:** mechanical_thermal.json verify.known_problems ('captured 1/4"-20 nut, or a thread tapped in the aluminium plate'); mech.py (2/1.27 = 1.57)
    - **Fix cost:** $1-3
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/mechanical_thermal.json
  17.
    - **Area:** Lime-dependent mechanical work and its order
    - **Components:**
      - J21 header
      - ADT-Link R44SF
      - Al mid-plate
      - Lime pedestal
    - **Problem:** The Lime path requires desoldering J21 (8.5 mm, in the riser path). That cannot be undone and complicates an RMA, yet the board has known DDR and boot-loop failures and needs a burn-in inside the return window. The files do not order these steps. Building the case for the Lime before the gate wastes the aluminium plate if the Lime is dropped; building without provisions means a new plate later.
    - **Severity:** minor
    - **Fix:** Order: 12 h stressapptest and 50-100 cold boots, then decide on the Lime, then desolder J21 only if the Lime is kept. Cut the mid-plate once with the Lime pedestal and riser-clamp holes (no cost). Print the no-Lime shell first; if the Lime is kept, reprint only the top-edge strip.
    - **Evidence:** mechanical_thermal.json verify.known_problems (J21 desolder); compute.json verify (burn-in, return window); report_research.json decisions #22 and #69
    - **Fix cost:** $0; about $10 for a later strip reprint
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/mechanical_thermal.json
  18.
    - **Area:** Ergonomics (wish vs physics)
    - **Components:**
      - handheld 1.2-1.6 kg
      - hand strap
      - tripod
    - **Problem:** The 'one hand' wish is designed into the inputs (encoders and keys), but a 1.2-1.6 kg box held at reading distance for a 10-15 min pass while hand-tracking an antenna is not realistic one-handed.
    - **Severity:** minor
    - **Fix:** State plainly that one-hand means input, not holding. Supply a hand strap plus a neck strap, and a 1/4-20 mini tripod for the device or the antenna. Tracking passes put the device on the strap or tripod and the free hand on the antenna.
    - **Evidence:** mechanical_thermal.json verify ('needs a strap and a boom/tripod mount'); lab_ui_hf.json final.ui_system.design_rules
    - **Fix cost:** $10-25 (estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  19.
    - **Area:** T7 placement
    - **Components:**
      - Samsung T7
      - RF bay
      - GNSS patch
    - **Problem:** small_antenna_stack treats the T7 as internal (+70 g). Inside, it would sit in 25-35 W of internal heat and radiate USB 3 noise next to the L-band, S-band and GNSS paths. The storage file also relies on it being hot-swappable.
    - **Severity:** minor
    - **Fix:** Mount the T7 outside on the bottom (noisy) edge with a short shielded cable and a strap, away from the top-edge antennas. Run the floor A/B at 1.7/2.2 GHz and the GNSS C/N0 check with the T7 on and off.
    - **Evidence:** small_antenna_stack.json stack.size_weight_power_before_after ('internal T7'); report_research.json decisions #72 and #82; storage.json verify (T7 Shield rated 0-60 C)
    - **Fix cost:** $0-10
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/storage.json
  20.
    - **Area:** Field setup time
    - **Components:**
      - foldable kit
      - patch kit
      - HF wire
      - Boni-Whip
      - pass scheduler
    - **Problem:** No file states setup time per profile, and the pass scheduler warns only at T-10 and T-2 min. Foldable targets are 8-13 min in all (dipole 2, Yagi 4, helicone 3, horn 4; the ultra-compact Yagi adds 4-5 min). HF wire with a remote feed and a Boni-Whip on a mast take an estimated 8-12 and 5-8 min. Separately, register #84's 'LRPT and HRPT on the same pass needs two antennas pointed by one operator' is too strict: the V-dipole on its stand runs unattended on RTL-A while the helicone is hand-tracked on RTL-B.
    - **Severity:** minor
    - **Fix:** Add setup_min to each function profile. The pass card warns at T-(setup+5) min. Allow 'V-dipole fixed + helicone tracked' as a dual-SDR pass profile, with the RAM and CPU cost of two SatDump instances shown.
    - **Evidence:** foldable_antennas.json final.build_and_test_steps (step 10 drill targets) and ultra_compact_tier; lab_ui_hf.json final.ui_system.design_rules (banners at T-10 and T-2 min)
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
  21.
    - **Area:** Memory policy
    - **Components:**
      - systemd OOM handling
      - mlock limits
      - swap
    - **Problem:** No file sets LimitMEMLOCK for the mlocked ring, OOM ordering across the lab units, or the swap policy. storage says 'swapoff -a'; npu_training says 'OOM order: trainer, inferd, fusiond; capture last'. If systemd-oomd is active on the Radxa OS desktop image (unverified), it would kill whole cgroups by pressure, possibly the Shell session.
    - **Severity:** minor
    - **Fix:** labrx: LimitMEMLOCK=infinity, OOMScoreAdjust=-900. labd and labpowerd: -1000. Trainer 900, Expert GUIs 700, OpenWebRX+ 500, inferd 300. No disk swap; a zram of 1 GiB at low priority. Disable systemd-oomd or limit it to the trainer and Expert slices. Test: the trainer pushes past MemoryMax and the capture continues.
    - **Evidence:** npu_training.json final.budgets ('OOM order'); storage.json verify ('Run swapoff -a')
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  22.
    - **Area:** Price basis for storage
    - **Components:**
      - Samsung T7 1 TB
      - microSD
      - 2230 NVMe
    - **Problem:** Storage prices in the files are stale. The T7 is quoted as $207 (hotline.ua) or $190-275 (undated). The 2026 NAND shortage raised all flash prices: T7 1 TB $190 on sale at Amazon (8 Jun 2026, street $275), $229.99 at B&H per the P2 procurement note. Samsung PRO Endurance 256 GB was $81.99 at Amazon in an Apr 2026 snapshot (was about $20-27 in 2023-24). The Crucial P310 1 TB 2230 averaged $102.80 with a $159.99 peak in Feb 2026. These swings change the Lime premium and the choice of no-Lime secondary storage.
    - **Severity:** minor
    - **Fix:** Re-price at order time. Treat the figures as volatile. Decisions below use ranges: T7 $190-275, microSD 256 GB about $48-82, 2230 TLC 1 TB about $100-160 (unverified).
    - **Evidence:** PCWorld 8 Jun 2026; Slickdeals snapshot (5 Apr 2026); camelcamelcamel P310; minute-log 05:12
    - **Fix cost:** $0
    - **Sources:**
      - https://www.pcworld.com/article/3158933/samsung-fast-t7-portable-ssd-finally-drops-in-price-190-was-285.html
      - https://slickdeals.net/f/17754051-samsung-pro-endurance-256gb-microsdxc-memory-card-with-adapter-25-54-via-amazon
      - https://camelcamelcamel.com/product/B0D61Z8R1W
  23.
    - **Area:** Single ring vs engines that open SDRs
    - **Components:**
      - labrx
      - SatDump live
      - NPU AI tap
    - **Problem:** The single-ring model (labrx owns the stream) conflicts with SatDump live passes, which open the SDR themselves. During a pass the NPU tap and the MARK pre-trigger ring then see no IQ. The interfaces lens raised this as a blocker; from the resource side, the cost of fanning out to decoders is negligible (5 MB/s per RTL).
    - **Severity:** minor
    - **Fix:** labrx is always the SDR owner. Decoders take IQ from labrx through a FIFO, UDP or a shared-memory reader. Expert hand-offs, when no tap is needed, stay as labd leases. Budget 0.05-0.1 A78 core per fan-out (estimate).
    - **Evidence:** minute-log 05:15 (completeness lens: 'SatDump on a pass occupies the SDR, so the NPU has no IQ tap'); report_research.json decisions #50
    - **Fix cost:** $0 (software)
    - **Sources:**
      - /home/user/lizbeth307/sat-receiver-audit/minute-log.md
- **Proposed decisions:**
  1.
    - **Question:** C1. LimeSDR Micro: keep or drop, and what depends on it?
    - **Decision:** Keep it as a gated optional. Keep the cancellable pre-order only if it is refundable before shipping (small_antenna_stack says Crowd Supply refunds pre-orders in full before shipping; check the order type). Decide on delivery (about 15 Dec 2026) or by 31 Jan 2027. Keep it only if all of these hold: (1) the user wants S-band or 56 MHz wideband NPU survey; (2) riser acceptance: 8 GT/s x1, 50 warm and 20 cold boots, zero AER after 60 min; (3) VkFFT N=65536 on Turnip at 854 FFT/s or more, and zero limeTRX losses during an LRPT+HRPT pass; (4) VCC_5V_PERI measured at 14 W or less with the Lime, T7 and RTL-B; (5) the 1.7/2.2 GHz floor rises 1 dB or less with the T7 active. v1 is built without the Lime; the mid-plate is pre-drilled for it.
    - **Reason:** No core target needs the Lime. It adds S-band, 12-bit 435 MHz, AHRPT-rate capture and three of the five NPU profiles, but it costs about $475-700 more than the no-Lime storage option, plus 4-10 W, +0.15 kg, +5-10 mm of case, a desoldered J21 and an isolated A78 core.
    - **Consequences:** If kept: T7 on blue USB 3.1, RTL-A on the CH334F, 4 GiB ring, CPU7 cmdline variant, LAB 5 V fuse 3 A, top-edge strip reprint, REF IN and P4/P5/P7/P14/P18 enabled. If dropped: the M.2 slot is free for a 2230 NVMe, there is no CPU7 isolation, the ring is 1.5 GiB, RTL-A goes on the blue port, NPU profiles are RTL-F/RTL-C/HF-F only, and S-band needs the Pluto either/or.
    - **Alternatives rejected:** Buying it unconditionally now (unverified driver on ARM, 160 Msps unproven). Cancelling now (loses the only 56 MHz NPU survey path before any test). Pluto in parallel (duplicates the Lime and adds TX).
  2.
    - **Question:** C2. Q6A RAM tier and the single RAM budget
    - **Decision:** Buy the 12 GB board now from TinyTronics: EUR 122.31 ex VAT / EUR 148 incl. VAT, 10+ in stock on 18 Oct 2026. Allnet at $189.99 is the second source (in stock today). Ring sizes are set at boot: 1.5 GiB without the Lime, 4 GiB with it, plus a +3 GiB Burst segment that is allowed only when the trainer, OpenWebRX+, SDRangel and Expert GUIs are stopped. MemoryMax: inferd-htp 1 GiB, trainer 2 GiB.
    - **Reason:** The 8 GB board is now only EUR 22 cheaper at the same seller, and my model shows it over-committed in Train mode. 12 GB leaves 3.3-7.4 GiB free without the Lime and 0.8-4.9 GiB with it.
    - **Consequences:** Delete the 6 GiB and 8 GiB ring figures and the small stack's 8 GB downgrade. Measure MemTotal and app RSS in the W1-2 gates.
    - **Alternatives rejected:** 8 GB board (over-committed with the trainer). A fixed 6-8 GiB ring (OOM risk). Shrinking the ring live (fragile).
  3.
    - **Question:** C3. Pack 3S vs 4S
    - **Decision:** 4S1P P50B (72 Wh) with a regulated 12 V rail into J21, as the register recommends. Restate runtimes using the power lens's realistic 50-58 Wh usable.
    - **Reason:** Several loads need 12 V or more (LNB 13.2 V, Boni-Whip 12.5 V, AUX 12 V, 4D display 12 V, Pinecil). 3S cannot build those rails as designed.
    - **Consequences:** +75 g and about +$45. The cell row sits in the case as 46x25x150 mm.
    - **Alternatives rejected:** 3S direct to J21 (no clean rail for 12.5/13.2 V loads).
  4.
    - **Question:** C4. 12 V regulator: D36V50F12 or a forced-PWM buck-boost
    - **Decision:** Decide after the terminated-floor spur A/B and a sealed-case current test, as the register says. Buy two D36V50F12 now ('Rationed') as the default; switch only if light-load spurs appear on NAVTEX/LF.
    - **Reason:** This is outside my lens. The only resource point is its 13.3 V dropout against the 13.6 V Linux cutoff, which is acceptable.
    - **Consequences:** Hardware cut at 13.4 V or above.
    - **Alternatives rejected:** 9 V into J21 (based on a misplaced-TVS reading).
  5.
    - **Question:** C5. USB port map
    - **Decision:** Without the Lime: blue USB 3.1 = RTL-A. FE1.1s P1 = RTL-B, P2 = touch, P3 = CH334F #1 (H1 HMI RP2040 only if UART7 fails, H2 spare, H3 CH334F #2 for LAB USB plus 3 spares, H4 HF+). The IMU is always relayed by the HMI RP2040. With the Lime: blue = T7 on its own VBUS, RTL-A on CH334F #1 H2. Aggregate cap 25 MB/s on the FE1.1s tree.
    - **Reason:** This is the only map with a free port in every case (UART7 working or not, Lime or not).
    - **Consequences:** +$4.95 and about +0.2 W. Hub depth 4 to a bench instrument. The '3 streams' rule is retired.
    - **Alternatives rejected:** The single-CH334F map (full with Lime and no UART7). T7 on the FE1.1s (USB 2.0 cannot carry 224 MB/s).
  6.
    - **Question:** C6. 40-pin header, buses, IMU interface, fan pin
    - **Decision:** Accept the register map (PPS pin 7/GPIO96, UART6 16/18 LC76G, UART7 32/29 HMI, I2C0 INA228 only, I2C2 MCP23017 x2 + RP2040 target, no BNO085 on I2C). The IMU goes through the HMI RP2040's second UART in all cases. Fan: plain on/off at 60/50 C through an AO3400, on whichever of pin 33 or GPIO56 is free after the expander count.
    - **Reason:** On/off avoids 1 kHz PWM ticking and CPU cost. Relaying the IMU frees a USB port.
    - **Consequences:** The puck lead needs a 4-pin locking case socket.
    - **Alternatives rejected:** IMU on USB-CDC (uses a port). BNO085 on I2C2 (clock stretching).
  7.
    - **Question:** C7. Hardware ownership and the single ring
    - **Decision:** labd is the only lease and lock authority. labrx is the only SDR stream owner, ring and recorder. SatDump, SDRangel and OpenWebRX+ consume IQ from labrx fan-out when REC, MARK or the AI tap is active. A direct device open is allowed only under an Expert lease with no tap. labclassify runs inferd and fusiond.
    - **Reason:** One ring is the only way the RAM budget closes and MARK pre-trigger works during passes.
    - **Consequences:** The npu_training daemons are renamed into labrx and labclassify. SatDump runs with a file, pipe or UDP source (to be verified on the 2.0 alpha).
    - **Alternatives rejected:** Engines owning SDRs (two rings, no tap during passes).
  8.
    - **Question:** C8. LNB supply
    - **Decision:** Accept the register: 13.2 V ±0.2 V at the F connector, true disconnect, switch rated 20 V or more, no 18 V, one current limit at 1.5-2x the measured Bullseye draw.
    - **Reason:** Outside my lens. Physics: 18 V only selects horizontal WB/DATV, which is lost without a dish.
    - **Consequences:** The rf_frontend and lab_ui_hf 13.4/18.2 V entries are deleted.
    - **Alternatives rejected:** A switchable 13/18 V boost.
  9.
    - **Question:** C9. LNA bias rule
    - **Decision:** Accept: a TPS2553 at 250-300 mA for every SAWbird+. The V4L tee only for LNAs of 80 mA or less. Under C10b, VHF EXT leads get no bias at all.
    - **Reason:** 170-180 mA LNAs on a 180 mA tee leave no margin.
    - **Consequences:** The injectors move to LAB 5 V, which is why that rail needs a 3 A fuse.
    - **Alternatives rejected:** A 100-160 mA PTC (trips).
  10.
    - **Question:** C10. FM filter
    - **Decision:** One Nooelec Flamingo+ FM, fitted permanently inside the case at the head of the unified VHF/UHF chain (see C10b).
    - **Reason:** With one internal VHF front end, one filter covers both antenna kits.
    - **Consequences:** No second filter in the foldable kit.
    - **Alternatives rejected:** A filter at every feed (two parts, two LNAs).
  11.
    - **Question:** C10b. One VHF/UHF front end for both antenna kits
    - **Decision:** VHF/UHF bulkhead, then Flamingo+ FM, then a relay to SAWbird+ NOAA (137 MHz), 70 cm BPF + LNA V2 (145.8/435 MHz) or the HF+ VHF bus (AIS), then RTL-A. Whips screw onto the same bulkhead. The foldable V-dipole and Yagi run on 1-2 m of unpowered RG316. L-band LNAs stay at the feed.
    - **Reason:** 0.3-0.6 dB of coax ahead of the LNA costs only 0.06-0.36 dB SNR at 137 MHz, because the sky is hot (model). The design is simpler and removes the DC-short bias hazard on the Yagi hairpin.
    - **Consequences:** Saves $74.90. One relay throw.
    - **Alternatives rejected:** LNA at the feed for VHF (duplicate filter and LNA, bias interlocks).
  12.
    - **Question:** C11. librtlsdr recipe
    - **Decision:** Accept the register: rebuild noble 2.0.1 with commits 0204c9c and 65f0658, keep the .so.2 SONAME, hold it.
    - **Reason:** Outside my lens.
    - **Consequences:** First arm64 build on the Q6A.
    - **Alternatives rejected:** Purge-and-fork; 2.0.3 .so.0.
  13.
    - **Question:** C12. Display field-mode clock
    - **Decision:** Wisecoco: about 127.9 MHz (51.7 Hz, 2200x1125) by EDID override, or 164.4-168.4 MHz if accepted. 4D fallback: per-profile modeset table in labd, since no clock between 65 and 90 MHz is clean.
    - **Reason:** The register's harmonic scan; 128.70 MHz hits 1544.4 MHz.
    - **Consequences:** Lab UI tests use the field mode.
    - **Alternatives rejected:** 128.70 MHz; native 1080p60 in the field.
  14.
    - **Question:** C12b. Panel choice deadline and case sequencing
    - **Decision:** Wisecoco gets one week for written answers on bonding, HID VID:PID, EDID, input V/A and the 51.7 Hz mode. Otherwise buy the 4D ($128.95 DigiKey per the P2 procurement note). The bezel CAD starts only after the panel passes acceptance. Hood: 30 mm, hinged, lies flat as a lid. Lux sensor outside the hood.
    - **Reason:** Bonding sets sun contrast more than nits do, and the case front depends on the real outline.
    - **Consequences:** The case design waits about 2-4 weeks for the panel.
    - **Alternatives rejected:** Designing for the inferred 164.2x98 mm outline now.
  15.
    - **Question:** C13. Kernel hold vs PPS
    - **Decision:** Accept: an out-of-tree pps-gpio DKMS on 6.18.2-4. Drop Route B.
    - **Reason:** Outside my lens.
    - **Consequences:** Also build pps-ldisc if the FT232RL fallback is used; it now has a spare CH334F port.
    - **Alternatives rejected:** The 7.0.11 kernel.
  16.
    - **Question:** C14. INA228 access
    - **Decision:** Accept: I2C0, user-space i2c-dev, no DT binding, shunt in the pack lead.
    - **Reason:** Outside my lens.
    - **Consequences:** Fix the npu_training placement.
    - **Alternatives rejected:** The ina238 hwmon driver.
  17.
    - **Question:** C15. Antenna tiers
    - **Decision:** STACK.md has two tiers built on shared parts. The patch/chip tier (always carried: whips, 2-turn and 4-turn helix, bare LNB with an 11 cm cone, L-band patch) is a subset of the backpack foldable kit (V-dipole as the LRPT default, ultra-compact crossed Yagi as default, petal helicone, gore horn). Shared: one 18 cm helix disc and helix, one Bullseye, one set of SAWbird+ GOES/iO, one internal VHF chain. Every small_antenna_stack removal is re-decided: Lime gated, T7 tied to the Lime, 12 GB kept, foldables restored, loops struck.
    - **Reason:** Shared parts cut weight and cost and let results carry over between tiers.
    - **Consequences:** The patch-tier helix loses an estimated 0.3-0.5 dB on 18 cm instead of 20 cm (model).
    - **Alternatives rejected:** Two independent kits; the 20 cm helical whip as LRPT default.
  18.
    - **Question:** C16. Receive-only and policy leftovers
    - **Decision:** Accept the register's strike list in full before STACK.md.
    - **Reason:** Hard rules govern.
    - **Consequences:** No resource effect except removing the H-probe line (-$50 to -109).
    - **Alternatives rejected:** None.
  19.
    - **Question:** C17. HF antenna chain and HF+ selector
    - **Decision:** Boni-Whip at 12.5 V from the LDO. A latching DC-capable signal relay selects HF / VHF bus / 50 ohm (part TBD; budget $5-15 and 6-12 cm3). The HF+ in its can stays inside at the far end from the bucks. The wire is for HF only; LF time signals use the whip.
    - **Reason:** The case volume model already includes the can and the selector.
    - **Consequences:** Add both to the BOM and to the case CAD.
    - **Alternatives rejected:** HMC241 (its DC blocks hurt LF). An external HF+ (uses the LAB port).
  20.
    - **Question:** C18. Storage, secondary drive, rolling caps, rollback
    - **Decision:** Every variant gets an A/B root on UFS (ESP 1 + 2x24 GiB) with boot counting. Without the Lime: an internal 256 GB V30 endurance-class microSD (A2 is irrelevant for sequential IQ) for raw IQ and a second snapshot copy; a TLC 2230 NVMe in the free M.2 slot (Radxa measured 1467 MB/s write; about $100-160 per TB, unverified) only if pinned raw over about 6 h is needed. Updates come from a USB stick on LAB USB. With the Lime: T7 1 TB on blue USB 3.1, mounted outside on the bottom edge. Caps as in budget_tables.
    - **Reason:** Rollback must not depend on an optional drive. The worst no-Lime stream, 16.4 MB/s, is 1/3.7 of the measured microSD write (61.45 MB/s), and the card can be removed as a data mule.
    - **Consequences:** UFS keeps about 35-42 GiB for recordings (about 1 h dual-RTL raw). Products-only is the default.
    - **Alternatives rejected:** T7 without the Lime ($190-275 for unused bandwidth plus USB 3 RFI). Snapshots on removable media only.
  21.
    - **Question:** C19. CPU allocation and RT pinning
    - **Decision:** CPU0-3 (A55): UI, daemons, inferd host, Stage-2 embedder, ORT CPU fallback (CPUQuota 100%). CPU4-6 (A78), or CPU4-7 without the Lime: labrx, engines, loggers; the T2 trainer at SCHED_IDLE and nice 19 between passes only. CPU7: isolated with FIFO 50 for lime:Rx0 only in the Lime cmdline variant, irqaffinity=0-6; P4 loggers paused during Lime passes. Measure cpu7 vs cpu4-6 at FIFO 70 with the limeTRX loss counters.
    - **Reason:** The trainer on the A55 cores would take about 2.5x longer and compete with the UI. The A78 pool is the scarce resource once CPU7 is isolated.
    - **Consequences:** Fix lab_ui_hf (trainer and CPU7), npu_training and compute. Add VkFFT to the Lime gate.
    - **Alternatives rejected:** Isolating CPU7 always. Running the trainer on the A55 cores. lime:Rx0 on the shared pool without measurement.
  22.
    - **Question:** C20. Roadmaps
    - **Decision:** Accept: NPU Phase 0 inside the W1-2 gates; the minimal labeller and the 1.5 GiB ring in P0b; HF-F and second-RTL profiles before HF classes show in the UI.
    - **Reason:** The ring and labeller are prerequisites for collecting data.
    - **Consequences:** None for resources.
    - **Alternatives rejected:** The labeller in Feb-Apr 2027.
  23.
    - **Question:** C21. V4L count and continuous monitors
    - **Decision:** Buy 3: RTL-A and RTL-B plus 1 spare. AIS goes on the HF+ VHF bus. Continuous ADS-B or sonde monitoring uses a 4th V4L ($37.95) on a spare CH334F #2 port or LAB USB, inside the 25 MB/s cap (4 streams = 18.2 MB/s).
    - **Reason:** A spare that is always in service is not a spare.
    - **Consequences:** +$37.95 only if continuous monitoring is wanted. About +0.27 A on LAB 5 V.
    - **Alternatives rejected:** Using the spare as the monitor.
  24.
    - **Question:** C22. Software recipes
    - **Decision:** Accept: one venv per tool, pipx NanoVNA-Saver, PySide6 6.12, libgpiod v1, Skyfield 1.55 pip, SatDump 2.0-alpha from source, OpenWebRX+ pinned.
    - **Reason:** Outside my lens. A local apt repo of about 4 GiB is budgeted on UFS.
    - **Consequences:** Each tool tested on the Q6A.
    - **Alternatives rejected:** apt nanovna-saver 0.6.3; skyfield 1.48.
  25.
    - **Question:** C23. Region unknown
    - **Decision:** Accept: ask the user and hold off buying the LNB, horn and SAWbird+ iO.
    - **Reason:** Outside my lens.
    - **Consequences:** The QO-100 parts of the kit (horn gores, cone) may drop out, saving about 0.2 kg and 0.6-1 L.
    - **Alternatives rejected:** Buying everything now.
  26.
    - **Question:** C24. Costs and weights
    - **Decision:** Adopt my recomputed figures (models): handheld 1.2-1.5 kg without the Lime, 1.35-1.65 kg with it, about 220-225 x 135-140 x 55-60 mm. Field backpack 15-20 L, 4.2-5.8 kg (5.1-7.0 kg with the HF kit and mast). Pelican bench case 8.8 L of 14.5 L, 8.2-9.1 kg. Net Lime premium about $475-700, plus the S-band chain.
    - **Reason:** The old totals use the superseded antenna tier and omit the HF+, HMI and supports.
    - **Consequences:** Re-price everything at world prices in P5. Flash prices are volatile in 2026.
    - **Alternatives rejected:** radio_lab's 3.0-3.6 kg sling.
  27.
    - **Question:** C25. P1b completion
    - **Decision:** Resolved: final/report_research.json exists (576,735 B, 04:51). The errata blocks for summaries.md and minute-log.md are still to be added before STACK.md.
    - **Reason:** The file is present.
    - **Consequences:** None.
    - **Alternatives rejected:** None.
  28.
    - **Question:** Case layout and HMI placement
    - **Decision:** Right-hand HMI column (38-42 mm: 30-35 mm main knob, volume encoder, 2x3 sealed keys at 13 mm pitch) beside the glass. Antenna connectors on the top edge, power and data on the bottom edge, 1/4-20 captured nut on the back, internal pack 46x25x150 mm. Parametric shell; a mirrored left-hand print on request.
    - **Reason:** This is the only layout that keeps width near 215-225 mm and height at 131-141 mm with glove-size controls.
    - **Consequences:** Thickness 55-60 mm to keep the internal fill near 50-63%.
    - **Alternatives rejected:** HMI row below the display (162-166 mm tall). HMI split on both sides (about 260 mm wide).
- **Checks passed:**
  - Allnet China has the Q6A 12 GB in stock at $189.99 (8 GB unavailable, 6 GB $149.99), from products/radxa-dragon-q6a.js fetched 18 Oct 2026. This settles summaries #75 vs #86.
  - TinyTronics lists the Q6A 12 GB at EUR 148.00 incl. VAT / EUR 122.31 ex VAT with 10+ in stock (fetched 18 Oct 2026). That is EUR 22.31 ex VAT above the 8 GB board (EUR 100 ex VAT per compute.json).
  - Visible RAM after firmware carve-outs is measured on two boards: 6 GB shows 5609 MB (sbc-bench KBw_, kernel 6.16.7) and 8 GB shows 7604 MiB (Geerling #85). The register's 'about 11 GiB visible' for 12 GB is consistent; my extrapolation is 11.3-11.4 GiB.
  - Ring durations reproduced: 4 GiB = 19.2 s and 6 GiB = 28.8 s at 224 MB/s; 8 GiB at 160 Msps I16 draining at 395 MB/s = 35 s; 1.5 GiB = 98 s of 2xRTL+HF+.
  - Recording rates reproduced: 1 V4L 18.4 GB/h, 2 V4L 36.9 GB/h, 2 V4L + HF+ cf32 59 GB/h, Lime 56 Msps ci16 806 GB/h, ci8 403 GB/h. The register's correction of the small stack is right.
  - microSD on the Q6A: 61.45 MB/s sequential write and 0.80 MB/s 4K random write (Geerling #85). That is 3.7x headroom over the worst no-Lime stream, so it is adequate as raw-IQ secondary storage, not as an OS drive.
  - FE1.1s bandwidth with 4 streams (2 RTL + HF+ + monitor V4L) is 18.2 MB/s, under the practical 35-40 MB/s. USB 2.0 hub depth with two CH334F plus a bench hub is 4, within the limit of 5.
  - Placing the 137 MHz LNA inside the case behind 1-2 m of RG316 costs 0.06-0.36 dB SNR (my model with Ta of 565-1830 K), so one internal VHF chain can serve both antenna kits.
  - The 2230 NVMe option is real when the Lime is absent: the Q6A M.2 slot is M-key 2230 Gen3 x2, Radxa measured 1467 MB/s write, and it needs no riser (storage.json alternatives). There is one slot-failure forum report (30807).
  - The foldable kit meets the piece-size rule (longest pieces 35/34 cm Yagi; ultra-compact 20 cm or less). Packed volume 6-6.5 L and 1.0-1.4 kg of antennas are taken as given in foldable_antennas final.
  - Pelican 1450 holds core + extended + HF bench objects at 8.8 L of 14.5 L (61%), but not the handheld and antennas as well.
  - The mechanical verifier's thickness stack (50-55 mm), two-path airflow, ASA shell and riser and pedestal concept are consistent with the Q6A STEP-derived numbers in mechanical_thermal.json.
  - The UI ergonomics (15/20 mm targets, 3 mm gaps, encoders and keys for every capture-critical leaf, 1.5 s holds) are internally consistent and were verified in lab_ui_hf. My finding concerns the hardware envelope, not the UI rules.
  - The T7 1 TB world price is now documented: $190 on an Amazon sale on 8 Jun 2026 (PCWorld; street $275) and $229.99 at B&H (P2 procurement note). The register's $207 hotline.ua figure is superseded.
- **Budget tables:**
  - RAM, 12 GB Q6A (visible about 11.37 GiB, extrapolated from measured 6/8 GB boards). App RSS are MODEL estimates in GiB: OS base 0.45-0.7 | labwc+Xwayland+labbar 0.15-0.3 | Lab Shell 0.3-0.6 | lab daemons 0.12-0.25 | labrx 0.15-0.35 + shm 0.06 | inferd-htp+cpu+fusiond 0.6-1.35 | SatDump pass 0.4-1.2 | SDRangel 0.2-0.5 | OpenWebRX+ 0.2-0.5 | loggers 0.25-0.5 | Expert GUI 0.25-0.5 | trainer 2.0 (cap).
  Scenario / ring / free GiB:
  - No Lime, pass / 1.5 / 4.6-7.4
  - No Lime, lab or Expert / 1.5 / 4.3-7.1
  - No Lime, train / 1.5 / 3.3-5.6
  - Lime, pass / 4.0 / 2.1-4.9
  - Lime, train / 4.0 / 0.8-3.1
  - Lime, train / 6.0 (npu final) / -1.2 to +1.1 OVER
  - 8 GB board, no Lime, train / 1.0 / -0.2 to +2.2 OVER
  - CPU (MODEL, cores of demand):
  - CPU0-3 A55 1.9 GHz: Shell, labwc, Xwayland, bar 0.4-0.8; daemons, gpsd, chrony 0.1-0.2; inferd host, fusiond, Stage 2 0.3-0.5; ORT fallback up to 1.0 (CPUQuota). Typical 0.8-1.5 of 4; 1.8-2.5 in CPU-fallback mode.
  - CPU4-6 (+7 without the Lime) A78 2.4 GHz: labrx DSP and tiling 0.3-0.5; SatDump 1-2 per instance; SDRangel or OpenWebRX+ 0.3-1.0; loggers 0.5-1.0; LIME-W CPU FFT fallback about 2 (only if VkFFT fails); T2 trainer 3 (SCHED_IDLE, between passes). LRPT+HRPT pass plus loggers = 2.8-4.5, which fits 4 cores without the Lime and needs logger pausing on 3 cores with it.
  - CPU7 A78 2.7 GHz: lime:Rx0, FIFO 50, isolated (Lime only); otherwise in the pool.
  - Storage:
  - UFS 128 GB (about 119 GiB): ESP 1 | root A 24 | root B 24 (A/B rollback) | apt repo 4 | map tiles 4 | NPU dataset 18.6 (20 GB) | models and golden set 0.3 | logs 0.5. That leaves about 35-42 GiB of recordings: 1.0-1.2 h dual-RTL raw, 0.6-0.7 h with HF+. Raw cap 30 GiB rolling. Write 388 MB/s inside the about 4 GiB WriteBooster cache; post-cache unknown (estimate 120-200 MB/s).
  - No Lime: microSD 256 GB V30 endurance, 61 MB/s measured class (3.7x the 16.4 MB/s worst stream), 6.5 h dual-RTL, cap 200 GB / 14 days, about $48-82 (2026, volatile). Option: 2230 NVMe 1 TB, 1467 MB/s, 25 h dual-RTL, about $100-160 (unverified).
  - Lime: T7 1 TB on blue USB 3.1, 395 MB/s port limit (1.76x 224 MB/s), 1.15 h at 56 Msps ci16. NPU raw 400 GB / 14 days | captures and bursts 300 GB | exFAT exchange 64 GiB | snapshot copy 64 GiB. $190-275.
  - USB ports and bandwidth (MB/s):
  - Blue USB 3.1: RTL-A 5.12 (no Lime) or T7 up to 224 (Lime).
  - FE1.1s P1: RTL-B 5.12. P2: touch HID under 0.1. P3: CH334F #1. Internal: Wi-Fi/BT, rfkilled.
  - CH334F #1: H1 HMI RP2040 (only if UART7 fails) | H2 spare, or RTL-A 5.12 with the Lime | H3 CH334F #2 (LAB USB-A plus 3 spares: FT232RL GNSS fallback, RP2040 counter, 4th V4L 4.8) | H4 HF+ 3.1.
  - FE1.1s aggregate: 13.4 typical, 18.2 with a monitor V4L; cap 25 (practical ceiling 35-40). Hub depth to a bench instrument 4 of 5 allowed.
  - 5 V rails (A or W; spec allowances, HF+ unpublished):
  - VCC_5V_PERI, about 17 W (SGM40666AS). No Lime: 2 V4L 2.6 + tees 0.7 + fan 0.5-1 = 3.8-4.3 W. Lime: Lime 4-5 typical (8.25 allowance) + T7 2.5-4.5 + RTL-B 1.3 + tee 0.35 + fan 1 = 9.2-12.2 W typical, 15.4 W at allowances. Gate: measured 14 W or less.
  - LAB 5 V (D36V28F5, 3.2 A): CH334F x2 0.1 + HMI 0.05 + IMU 0.03 + HF+ 0.1-0.2 + SAWbird+ x2 0.36 + LNA V2 0.1 + LAB port 1.0 (0.8 in field mode) = 1.7-1.9 A. With the Lime add RTL-A 0.27-0.35 for 2.0-2.2 A. Fuse 3 A, not 2 A.
  - Connectors (case penetrations):
  - Top edge: VHF/UHF SMA, L-BAND SMA (5 V bias), LNB F (13.2 V), HF SMA + ground post, GNSS SMA (3.3 V). Lime adds RX1, RX2 and optional REF IN, for 5-8 RF ports at 20 mm pitch (100-160 mm of a 215 mm edge).
  - Bottom edge: IP2368 USB-C (the only power input), capped LAB USB-A, LAB BUS 6-pin locking, 3.5 mm audio, T7 lead (Lime only).
  - Back: 1/4-20 captured nut, 2-4 strap lugs, IMU puck 4-pin locking socket.
  - Total 11-14 penetrations; an IP target is still to be set.
  - Mechanical, weight and volume (MODEL):
  - Handheld: 214-218 x 131-141 mm footprint with a right-hand HMI column; plan 220-225 x 135-140 x 55-60 mm. Parts 0.79-1.03 L, which fills 58-75% of a 215x135x55 interior or 48-63% of 225x140x60. 1.2-1.5 kg without the Lime, 1.35-1.65 kg with it. Hood 30 mm, about 5 mm folded, 40-80 g.
  - Patch-tier extras (whips, 2-turn helix, cone, L-band patch): 0.15-0.3 kg, about 0.6 L.
  - Foldable kit: 6-6.5 L, 1.3-1.8 kg with LNB, LNAs and jumpers.
  - HF kit 0.4-0.5 kg, 0.8 L. Boni-Whip and mast 0.5-0.75 kg. Mini tripod 0.3-0.6 kg. Field pouch 0.8 kg, 2 L.
  - Field backpack (15-20 L): 4.2-5.8 kg, or 5.1-7.0 kg with the HF kit and mast.
  - Bench: Pelican 1450, 14.5 L interior; core 5.5 L / 4.3-4.8 kg, extended 2.5 L / 1.4 kg, HF 0.8 L. Fill 61%. Loaded 8.2-9.1 kg.
  - Field setup time (targets and estimates, unmeasured):
  - Boot to Shell: target 60 s or less (measure). GNSS 3D fix with 6+ satellites: target 60 s or less (LC76G TTFF unverified). IMU sun-sight north: about 1 min.
  - Patch tier: whip 0.5 min; helix on mini tripod 2 min; LNB with cone, pointed, 2-3 min.
  - Foldable (foldable step 10 targets): dipole 2, Yagi 4 (ultra-compact 8-9), helicone 3, horn 4; all 13 min (17-18 ultra).
  - HF wire with 9:1, counterpoise and 5-10 m coax: 8-12 min. Boni-Whip on a 2 m mast with ground stake: 5-8 min.
  - Bench (mat, bank, hub, VNA SOL per band): 10-15 min.
  - Arrival to first LEO pass with one antenna: 6-10 min. Full camp including HF: 25-35 min.
  - Lime keep vs drop, cost from my lens (USD, before VAT):
  - Keep: Lime $267 (incl. $18 shipping) + T7 $190-275 + R44SF $19 + 2x MHF4 $12 + I-PEX tool about $18 + pedestal, pad and fins $10-25 (estimate) + Lime pads and DC blocks $40-65 (estimate) + VLM-33-S+ $69.60 (optional) = about $556-751. S-band adds a EUR 65.45 cavity plus an unpriced LNA.
  - Drop: microSD 256 GB $48-82, or 2230 NVMe 1 TB $100-160.
  - Net premium about $475-700, plus 4-10 W, +0.15 kg, +5-10 mm length, J21 desoldered, CPU7 isolated.
- **Notes:** I read the requirements and the register in full: summary, 143 decisions, compliance, corrections, the 25 conflicts and the open questions. Then I cross-read the resource, mechanical and packing fields of compute, storage, mechanical_thermal, npu_training, lab_ui_hf, radio_lab, foldable_antennas, small_antenna_stack, display_market and display, plus the tail of minute-log.md (the P2 procurement, completeness and power lenses).
  
  What I settled myself:
  - 7 web calls: Allnet stock JSON, TinyTronics 12 GB, sbc-bench KBw_, Geerling #85, the PCWorld T7 article, a 2230 NVMe price search and a microSD price search. pelican.com returned 403, so the Pelican figures stay unverified.
  - Two local models, both estimates where noted: /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lens_rlm/calc/budgets.py (RAM, ring and storage) and /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/lens_rlm/calc/mech.py (envelope, fill, weight, packing, 1/4-20 engagement, VHF LNA-placement penalty). App RSS, CPU loads, part volumes and setup times are my estimates, not measurements, and are labelled MODEL.
  
  Main conclusions:
  1. Buy the 12 GB Q6A from TinyTronics now. It is EUR 22 ex VAT more than the 8 GB board, and the 8 GB board is over-committed with the trainer.
  2. Size one ring per hardware set: 1.5 GiB without the Lime, 4 GiB with it, plus a 3 GiB Burst segment. Delete the 6 GiB and 8 GiB figures.
  3. CPU7 is isolated only with the Lime. The trainer runs on the A78 cores at SCHED_IDLE between passes. The Lime gate must include a VkFFT benchmark and a loss test during a pass.
  4. Rollback lives on an A/B UFS root in every variant. The T7 exists only with the Lime. Without the Lime, an internal V30 endurance microSD (or a 2230 NVMe in the free M.2 slot) holds raw IQ.
  5. USB needs a second $4.95 CH334F, and the IMU always goes through the HMI RP2040. LAB 5 V needs a 3 A fuse.
  6. The case must be re-derived for the HMI column, the HF+ can and the selectors: about 220-225 x 135-140 x 55-60 mm, 1.2-1.65 kg.
  7. One internal VHF/UHF front end serves both antenna kits, and one 18 cm helix disc serves both tiers.
  8. The field tier is a 15-20 L daypack of 4.2-7.0 kg, not a sling. The Pelican carries the bench kit only.
  
  All 25 register conflicts have an explicit decision. Those outside my lens (C3, C4, C8, C9, C11, C13, C14, C16, C20, C22, C23) endorse the register, with only the resource side effects noted.
  
  Physics and evidence against wishes:
  - One-hand use applies to the inputs, not to holding a 1.2-1.6 kg device.
  - Flash prices are volatile in 2026: T7 street price $275, microSD about 3-4x its 2024 price.
  
  Unverified and needing bench work:
  - MemTotal and app RSS on the 12 GB board; UFS post-cache write; HF+ current; the Lime's real 3.3 V draw; VkFFT on the Adreno 643.
  - Whether lime:Rx0 busy-polls (RT throttling); whether systemd-oomd is present on Radxa OS.
  - Pelican weight and dimensions; Wisecoco outline and bonding; the 4D price, which comes from the procurement note and was not re-fetched by me.
  
  Sources: https://shop.allnetchina.cn/products/radxa-dragon-q6a.js ; https://www.tinytronics.nl/en/development-boards/single-board-computers/radxa-dragon-q6a-qcs6490-12gb ; https://raw.githubusercontent.com/ThomasKaiser/sbc-bench/master/results/KBw_.txt ; https://github.com/geerlingguy/sbc-reviews/issues/85 ; https://www.pcworld.com/article/3158933/samsung-fast-t7-portable-ssd-finally-drops-in-price-190-was-285.html ; https://camelcamelcamel.com/product/B0D61Z8R1W ; https://slickdeals.net/f/17754051-samsung-pro-endurance-256gb-microsdxc-memory-card-with-adapter-25-54-via-amazon

## integration:verify (run `wf_221684d9-b6c`)

- **Verdict:** The stack can be built as one handheld without the LimeSDR. On paper it works: every named target has an RTL-SDR V4L or Airspy HF+ receive chain, a rail with power and protection, one owning process, and a bench gate before it is trusted.
  
  Review outcome:
  - **Blocker (1, decided):** the files give three incompatible ways of opening the SDRs. This is resolved by one labd lease model: labrx mode by default, plus engine-exclusive leases enforced by cgroup DeviceAllow.
  - **Confirmed and merged:** 30 major and 27 minor issues across the four reviewers.
  - **Refuted or superseded:** 27 claims.
  - **Fixes the reviewers missed:**
    - The D36V50F12 EN divider set at 12.8 V would only wake again at about 14.4 V, which blocks a restart between 13.6 and 14.4 V. Its ratio changes to about 0.10.
    - The LT3045 (20 V absolute maximum) is replaced by the TPS7A4701 (36 V, verified on ti.com) on the pack-fed LNB and Boni-Whip rails.
    - The Pico replaces the RP2040-Zero as the HMI MCU because more GPIO is needed.
    - In my own harmonic scan, 151.50 MHz sits centred in a 148.11-153.27 MHz clean window. 127.90 MHz sits only 0.14 MHz below the top of its window.
  
  Frozen design:
  - **Pack:** 4S1P P50B, charged to 4.10 V/cell. Usable energy is 58 Wh warm and 50 Wh cold or aged (model).
  - **Main 12 V:** D36V50F12 into J21 (buy 2). It is kept only if the narrow-RBW LF/HF spur A/B and a sealed-case current test pass.
  - **LAB 5 V:** D36V28F5 with a 3 A fuse.
  - **Pack-fed LDOs:** two TPS7A4701, for the LNB (13.2 V) and the Boni-Whip (12.5 V).
  - **LNA rail:** 2x LT3045 in parallel at 4.5 V, with one TPS2553 at 300 mA per channel.
  - **Control:** every enable sits on an MCP23017 powered from the Q6A. One Pico (HMI and supervisor) runs on the switched rail, and a micropower UV supervisor trips at 12.8 V and releases at 13.6 V.
  - **Front end:** at VHF the filter comes before the LNA; at UHF and L-band the LNA sits at the antenna. Separate HMC7992 selectors serve RTL-A and RTL-B, and two Omron G6K relays select the HF+ input.
  - **Display and RF hygiene:** the field EDID uses 151.50 MHz first and 127.90 MHz second. pcie0 (Ethernet) is off in the field, and fans run DC with no PWM.
  - **Storage and RAM:** A/B root on UFS; 1.5 GiB IQ ring.
  
  Runtime (model):
  - LEO pass: 3.3 h.
  - Survey with two RTLs and the HF+: 2.5 h.
  - Idle or LF Quiet: 6.9-7.1 h.
  - With the Lime, typical: 1.9 h.
  
  Cost (USD, before shipping, VAT and duty; partly estimated):
  - Handheld core: $1,758-2,253.
  - Plus both antenna tiers: $2,285-3,086.
  - Plus the bench lab: $3,759-4,896.
  - Everything except the optional items: $4,257-5,603.
  
  Where physics and evidence override the wishes:
  - Sustained 2000 nits in 35 C noon sun is thermally impossible. Expect about 1000 nits sustained, with 2000 as a burst.
  - Patch and chip antennas cannot serve 137-146 MHz.
  - QO-100 DATV and typical SSB need a dish.
  - Without loops, HF is limited by local noise.
  - One-hand use applies to the controls, not to holding a 1.35-1.6 kg device.
  
  Confidence is medium: every runtime, thermal, RAM, CPU and harmonic figure is a model until the W1-2 bench gates are run.
- **Decisions:**
  1.
    - **Question:** C1 LimeSDR Micro: keep or drop, and what depends on it
    - **Decision:** Make it a gated optional and build v1 without it. If it is wanted, hold a refundable Crowd Supply store pre-order ($249 + $18 shipping). Make the keep/cancel decision by 1 Dec 2026, before it ships on 15 Dec.
  
  Keep it only if both hold:
  1. The user confirms that S-band, 3.3-3.8 GHz or the 56 MHz wideband NPU survey is wanted.
  2. No-Lime bench data by then show VkFFT N=65536 at 854 FFT/s or more on Turnip, and a measured VCC_5V_PERI of 5 W or less.
  
  If the user does not answer, cancel. If it is kept, run the acceptance tests inside the 30-day guarantee:
  - riser link at 8 GT/s x1;
  - 50 warm and 20 cold boots;
  - zero AER errors over 60 min;
  - zero limeTRX losses during an LRPT plus HRPT pass;
  - VCC_5V_PERI measured at 14 W or less.
  
  The mid-plate is cut with the pedestal and riser holes either way.
    - **Reason:** No core target depends on it, and S-band is not in the user's named target list. It costs about $596-681 with its parts and the T7. It cuts a typical session from 3.3 h to 1.9 h (30.8 W vs 17.6 W, model). Its arm64 driver is unvalidated. Crowd Supply refunds in full only before shipment (verified by the sourcing lens), so 31 Jan 2027 is not a free date.
    - **Consequences:** Without the Lime:
  - ring 1.5 GiB; CPU7 back in the pool;
  - RTL-A on the blue port;
  - NPU profiles RTL-F, RTL-C and HF-F only;
  - no DKMS, class fixup or J21 desolder.
  
  With the Lime:
  - T7 outside the case on its own VBUS (behind the 14 W gate);
  - RTL-A on CH334F H2;
  - CPU7 isolated; ring 4 GiB plus a 3 GiB Burst segment;
  - J21 desoldered only after burn-in;
  - top-edge strip reprinted; a third HMC7992 and 10 dB pads.
    - **Alternatives rejected:** Deciding on 31 Jan 2027 (costs at least $20 restocking, plus return shipping and import VAT). Making it core now. A Pluto in parallel (TX-capable, duplicates the Lime).
  2.
    - **Question:** C2 Q6A RAM tier
    - **Decision:** Buy the 12 GB board now. EU: TinyTronics, EUR 148 incl. VAT, 10+ in stock. Elsewhere: Allnet, $189.99, available. Both were verified on 18 Oct.
  
  Burn it in on arrival: 12 h stressapptest plus memtester, and 50-100 cold boots. Allnet takes returns only within 7 days and unused, so treat a failure as a warranty claim and keep the UART logs.
    - **Reason:** RAM cannot be added later. Allnet's 8 GB is sold out, and TinyTronics' 8 GB saves only about EUR 22-27. In the model, an 8 GB board is overcommitted by -0.2 to +2.2 GiB in no-Lime training mode.
    - **Consequences:** Delete the small_antenna_stack 8 GB downgrade. Measure MemTotal and the RSS of each app in the W1-2 gates.
    - **Alternatives rejected:** 8 GB board; Arace (sold out); Ameridroid (not a listed distributor).
  3.
    - **Question:** C3 Pack 3S vs 4S
    - **Decision:** 4S1P Molicel P50B, 72 Wh nominal. Buy 5 cells ($9.99 each at 18650 Battery Store, verified, or an established local retailer). Charge daily to 4.10 V/cell (16.4 V); balance monthly at 4.20 V with the ISDT 608PD and the master switch off. Plan on 58 Wh usable (25 C, new) and 50 Wh (0 C, or after about 300 cycles).
    - **Reason:** Physics: the LNB (13.2 V), Boni-Whip (12.5 V), AUX 12 V and the noise-source ENR all need more than 12.9 V. On 4S they become quiet LDOs off the pack; on 3S each would need a boost converter, adding new spur sources. 4S also keeps the pack current under 4.6 A even at the Lime peak.
    - **Consequences:** About +$45 and +75 g over 3S. All runtimes come from the per-mode table. The home-built pack is never flown.
    - **Alternatives rejected:** 3S direct into J21 (needs 3-4 boost converters, about 46 Wh). Charging to 4.20 V every day (about 8% more energy, faster ageing).
  4.
    - **Question:** C4 12 V regulator for J21
    - **Decision:** Pololu D36V50F12 ($39.95; buy 2 because stock is 'Rationed'), bonded to the plate. Accept its dropout region below about 13.3 V of pack. It stays only if two gates pass:
  1. The narrow-RBW HF+ A/B, run terminated and then on the antenna, with SYS12 and LAB5 loads stepped from 0.3 to 3 A and the charger on and off. No line may sit 3 dB or more above the floor within ±5 kHz of 40, 60, 77.5, 162, 490, 518 or 4209.5 kHz, or inside an in-scope decode passband.
  2. A sealed-case run at 3.5 A for 60 min, at 14.0 V and at 16.4 V input.
  
  If either gate fails, replace it with a forced-PWM synchronous buck at a fixed frequency set by RT/SYNC. Choose that frequency from a harmonic scan, preferring 1 MHz or more; pick the part in P5. No buck-boost.
    - **Reason:** It is the only verified, branded 12 V module of 4.5 A or more. Above the 13.2 V cutoff a buck is enough. Its dropout region is harmless: J21 accepts 4.5-16 V (forum) and the SY81012 runs from 2.7 to 16 V. Its roughly 500 kHz fundamental and power-save mode are exactly what the NAVTEX and LF-carrier gate tests.
    - **Consequences:** Below about 13.3 V of pack, SYS12 sags to about 11.5-12 V. labd blocks noise-source NF measurements below a pack voltage of 13.6 V. The display must stay stable at SYS12 = 11.0 V (acceptance test).
    - **Alternatives rejected:** A forced-PWM buck-boost as the default (none buyable from a reputable vendor; not needed). An EN hardware cut at 13.4 V or higher (wastes about 5 Wh). 9 V into J21. An LTC3780 module.
  5.
    - **Question:** C5 USB port map
    - **Decision:** One Lime-agnostic map:
  - Blue USB 3.1 (J5 bottom, USB0, also the EDL port): RTL-A on a 15 cm shielded extension with a ferrite. With the Lime it becomes the T7.
  - FE1.1s P1: RTL-B.
  - P2: touch USB-HID.
  - P3: Adafruit CH334F #1. D+, D- and GND come from the Q6A; the hub's 5V pin comes from LAB5 only; Q6A VBUS is left unconnected.
  - H1: spare; it takes the Pico's native USB only if UART7 fails.
  - H2: spare; RTL-A goes here with the Lime.
  - H3: LAB USB-A behind a TPS2553 at 0.75 A.
  - H4: HF+ behind an MCP-switched load switch with LC and Mix-31.
  - P4 (Wi-Fi/BT): rfkill plus USB de-authorisation in every field profile.
  
  The IMU puck never uses USB. CH334F #2 is bought ($4.95) but fitted only if the Lime is kept and UART7 also fails, or if a fifth internal device appears. The aggregate cap on the FE1.1s tree is 25 MB/s.
    - **Reason:** This map has a free port in all four cases (Lime yes or no, UART7 working or not). The FE1.1s tree carries 13.3 MB/s or less against 35-40 MB/s practical. Leaving the second hub unfitted removes a 12 MHz clock (harmonics at 144.000 and 432.000 MHz) and saves 0.1-0.25 W.
    - **Consequences:** udev names every device /dev/lab/<name> by serial. The '3 continuous streams' rule is replaced by the 25 MB/s cap. A 30-minute zero-drop test runs with RTL-B, the HF+ and one LAB device.
    - **Alternatives rejected:** IMU as a USB-CDC device (sourcing lens). HF+ on Q6A VBUS (lab_ui_hf). A hub powered from both sides. Both CH334Fs fitted. Time-sharing the blue port between the T7 and instruments.
  6.
    - **Question:** C6 40-pin header, buses, IMU interface and fan control
    - **Decision:** Header:
  - pin 7 (GPIO96): PPS;
  - pins 8/10: console;
  - I2C0 (13/15): INA228 only;
  - UART6 (16/18): LC76G;
  - I2C2 (27/28): MCP23017 #1 (0x20, outputs) and #3 (0x22, inputs), plus a TCA9517 to the LAB BUS;
  - UART7 (32/29): the Pico;
  - pin 3: INA228 ALERT; pin 5: expander INT;
  - pins 12/35/38: Pico SWD; pin 40: safe-boot.
  
  No safety enable sits on a header GPIO. The IMU is relayed by the Pico over its UART1. Both fans are 2-wire 5 V units switched on and off in DC by the Pico through FETs:
  - the Q6A fan comes on at 60 C and goes off at 50 C, on labd's command;
  - the blower follows the panel NTC;
  - both go to 100% if the heartbeat is lost.
  
  Pin 33 (GPIO56, which is the same pin as FP_SPI_MISO) stays spare. One combined lab-q6a.dtso is built from Radxa's uart6, uart7, i2c0 and i2c2 overlays.
    - **Reason:** Pin 7 and pins 11-40 sit behind TXB-type UM3304 buffers (4 kOhm, 50 pF or less, state undefined during boot), which cannot drive gates or coils. DC fan switching has no PWM comb at all; 1, 20 and 30 kHz PWM land exactly on the LF carriers.
    - **Consequences:** The register's 'GPIO56 vs pin 33' conflict is closed: it is the same pin. The power.json i2c6 placement is deleted. pinmux-pins must show one owner per pin.
    - **Alternatives rejected:** pwm-gpio at 1 kHz (PoE-HAT overlay). A 24/25 kHz fan PWM. Header GPIOs for bias, LNB or relays. The BNO085 on I2C2. An IMU on USB-CDC.
  7.
    - **Question:** C7 Hardware ownership and the SDR access model
    - **Decision:** One owner per resource:
  - **labd:** I2C2, every enable, the selectors, SDR leases and modes, the scheduler, profiles, policy, rfkill and USB de-authorisation, and instruments. radio_lab's rflab and lab-sched become labd modules, with labctl as their CLI.
  - **labrx:** the only SDR opener in labrx mode. It holds the single RAM ring, the SigMF recorder, the FFT tiles and the NPU tap, and fans out to decoders.
  - **labclassify:** inference.
  - **labtrain:** a transient unit started by labd.
  - **labpowerd:** I2C0/INA228, KEY_POWER and the cutoff table.
  - **labinput:** UART7.
  - **gpsd:** UART6.
  - **kernel pps-gpio:** GPIO96.
  
  There are two lease modes:
  1. labrx mode, the default for passes, survey, NPU teaching and MARK. Passes are recorded and then decoded by SatDump from the baseband file; live piping is used only if the 2.0-alpha supports it.
  2. Engine-exclusive mode, for readsb, AIS-catcher, auto_rx, OpenWebRX+, sdrangelsrv and the Expert GUIs. The engine opens the device itself with ai_tap=false, and the lease is enforced by a transient DevicePolicy=closed plus DeviceAllow on that USB node.
    - **Reason:** This removes the double-open blocker, the second ring and recorder, and the advisory flocks. auto_rx and some monitor engines need direct device access, so 'labrx always' is too strong.
    - **Consequences:** The npu_training daemons are renamed into labrx and labclassify, under one namespace: lab.target, /run/lab, /opt/lab and the SigMF extension 'lab'. NPU teaching runs only on labrx-mode devices.
    - **Alternatives rejected:** sdr-ingestd as the permanent opener. Engines always opening devices themselves. Per-SDR flocks. A separate rflab daemon as a second I2C2 owner.
  8.
    - **Question:** C8 LNB supply
    - **Decision:** TPS7A4701 LDO (36 V input, 1 A, 307 mV dropout at 1 A; ti.com, fetched 18 Oct) set to 13.2 V. It is fed from the switched pack node through an LC filter and bonded to the plate.
  - EN from MCP #1 GPB0, low at power-up, which gives a true 0 V at the port.
  - Enabled only while the RTL-B selector is on the LNB port.
  - One current limit: a PTC whose hold current at 60 C is 1.5-2x the measured Bullseye current (provisionally 0.45 A), backed by the LDO's internal limit and thermal shutdown. PG goes to MCP #3.
  - Injection through a choke rated 1 A or more on the antenna side of a DC block, then a 15 dB pad (20 dB if the measured LNB gain is above 60 dB).
  - No 18 V anywhere.
  
  Acceptance: 0 V when off; 13.2 V ±0.2 V at the F port under load with the pack at 13.8 V or more.
    - **Reason:** On 4S the pack stays between 13.2 and 16.4 V across the whole usable window. The LDO holds 13.2 V down to about 13.5 V of pack and still gives about 12.9 V at cutoff (Bullseye vertical range 11.5-14 V). It adds no switching spurs near the 739.5 MHz IF. Worst-case dissipation is 0.96 W, about +29 K at θJA 30.5 C/W. Its 36 V absolute maximum stays above the SMBJ17A clamp on node N; the LT3045's 20 V does not.
    - **Consequences:** Delete the TPS65233 line, the 13.4/18.2 V menu and arbiter entries, the boost and SEPIC lines, and power.json's '12 V rail suits LNB'. The rail is built in every unit even though the LNB purchase waits for the region.
    - **Alternatives rejected:** LT3045 (20 V absolute maximum). S18V20AHV SEPIC plus a second #2813. MT3608/XL6009 boost. TPS65233. The 12 V rail through a tee (10.6-11.4 V at the LNB).
  9.
    - **Question:** C9 LNA bias rule and injectors
    - **Decision:** LNA rail: LAB5 → LC → 2x LT3045 in parallel at 4.5 V (about 1 A).
  - Each channel gets a TPS2553 set to 300 mA nominal (240 mA or more at the low tolerance edge), with EN on MCP #1 and FAULT on MCP #3.
  - Injectors sit on one internal PCB with per-band chokes rated 0.5 A or more and C0G blocks, qualified conducted on the LiteVNA. The TCBT-2R5G+ (200 mA maximum) is used only on channels whose LNA draws 150 mA or less.
  - DC-sense runs before every bias enable, and bias is locked off on DC-short profiles.
  - The V4L internal tees stay off in core. The spare V4L's tee may feed an LNA of 90 mA or less, and only with the labd token.
  - labd enforces a budget of LAB port plus LNA current of 1.5 A or less.
    - **Reason:** SAWbird+ parts draw 170-180 mA. A TPS2553 at 250 mA leaves too little margin at its low edge. A 250 mA PTC derates to about 180-190 mA at 60 C. The TCBT is rated 200 mA (Mini-Circuits datasheet, sourcing lens). An LT3045 at 5 V fed from 12 V would dissipate 2.45 W.
    - **Consequences:** Delete:
  - the rf_frontend 100-160 mA polyfuse;
  - 'GOES+ on the tee after soak' and 'LNA V2 on the tee';
  - the radio_lab H1-on-tee line;
  - foldable step 3's micro-USB feed.
  
  The LAB5 fuse goes from 2 A to 3 A.
    - **Alternatives rejected:** PTCs in the feeds. GOES+ on the V4L tee. TCBT-2R5G+ on SAWbird+ channels at a 300 mA limit. ZFBT-4R2GW+ at $111.57 each (bench only). A single 0.5 A LT3045.
  10.
    - **Question:** C10 FM band-stop filter and its position
    - **Decision:** Nooelec Flamingo+ FM v2 ($24.95). It sits on the antenna side of the first VHF LNA: VHF-137 bulkhead, then Flamingo+, then SAWbird+ NOAA inside the case. The optional 2 m/WIDE port gets a second Flamingo+ ahead of its LNA V2. The AIS/FM port into the HF+ stays unfiltered, because FM broadcast is a target there.
    - **Reason:** Physics: the SAWbird+ NOAA (LNA, SAW, LNA) and the LNA V2 have an unfiltered first gain stage, and intermodulation created there cannot be removed downstream. At VHF sky temperatures the filter costs 0.06-0.45 dB (model). Bias enters at the LNA output, so no DC ever crosses the filter.
    - **Consequences:** Overrides the power lens's 'SDR side of the injector', rf_frontend chain (b), and the antennas file's 'after the LNA'.
    - **Alternatives rejected:** Filter on the SDR side. RTL-SDR Blog band-stop (no DC rating). A filter at every feed in both tiers.
  11.
    - **Question:** C11 librtlsdr
    - **Decision:** Rebuild noble's 2.0.1-2build1 with 0204c9c (R828S) and 65f0658 (USB hang), plus the zerocopy typo fix and a bias-tee token patch. rtlsdr_set_bias_tee() and rtlsdr_set_bias_tee_gpio() refuse 'on' unless LAB_BIAS_OK equals the device serial, and labd sets it only in DC-safe units.
  - Keep the .so.2 SONAME and hold it with apt-mark.
  - Divert rtl_biast.
  - Blacklist dvb_usb_rtl28xxu.
  - Keep the EEPROM bias default off.
    - **Reason:** Rule line 44 requires the token gate. The rebuild keeps every librtlsdr2 consumer working, and it closes the software bypass of the DC-short interlock.
    - **Consequences:** Build first on the Q6A in W1-2 and confirm 'RTL-SDR Blog V4 Lite Detected'. Delete the 2.0.3 .so.0 recipe and the purge-and-fork recipe, including in npu_training.
    - **Alternatives rejected:** 2.0.3 .so.0. Purge and build the fork. An unrestricted bias-tee API.
  12.
    - **Question:** C12 Display field-mode pixel clock
    - **Decision:** The field EDID carries two DTDs, tried in order:
  1. 151.50 MHz, 1920x1080, totals 2200x1148 (88/44/148 and 27/5/36), 59.99 Hz.
  2. 127.90 MHz, 2200x1125, 51.68 Hz.
  
  Other rules:
  - Strip the CEA VICs.
  - 148.5 MHz is for bring-up only; 128.70 MHz is banned.
  - Load it with drm.edid_firmware=HDMI-A-1:edid/field.bin from the initramfs, set video=...@60 or @52, and pin the mode in the labwc output config.
  - Confirm the delivered clock with modetest and debugfs, then near-field E-probe the predicted harmonic line.
  - Ask Wisecoco for the bridge's DSI mode and lane rate.
    - **Reason:** My scan covered 17 used windows with a 0.5 MHz guard and n up to 40:
  - 151.5 MHz sits centred in a clean window of 148.11-153.27 MHz, robust to ±1% drift or SSC. It runs at 60 Hz, and its line rate of 68.86 kHz is at least 8.6 kHz from every LF carrier.
  - 127.9 MHz is clean from 123.62 to 128.04 MHz, only 0.14 MHz below the top edge. Its line rate of 58.14 kHz is 1.86 kHz from 60 kHz.
  - 128.70 MHz x12 = 1544.4 MHz (Inmarsat-C).
  - With 0.5% SSC, 148.5 MHz x5 smears over the QO-100 IF.
  - 151.5 MHz x15 = 2272.5 MHz falls in the 2200-2300 MHz allocation, but 13.5 MHz from Black Kite (Lime only), which is acceptable.
    - **Consequences:** Update display_market, display, small_antenna_stack, the lab_ui_hf UI tests and the kernel cmdline together. If the panel rejects both modes, fall back to 148.5 MHz with full shielding and ask the user.
    - **Alternatives rejected:** 127.9 MHz first (the register). 164.4-168.4 MHz (fundamental at the edge of the AIS SAW; 166.0 MHz fails with SSC). 128.70 MHz. Native 1080p60 in the field.
  13.
    - **Question:** C13 PPS on the held kernel
    - **Decision:** Build pps-gpio out of tree as a +labN DKMS package for 6.18.2-4 (CONFIG_PPS=y), on GPIO96 with the lab overlay node. chrony uses 'refclock PPS /dev/pps0 lock NMEA'.
  
  The Route A fallback is written in C on the GPIO v2 ioctl with EVENT_CLOCK_REALTIME, never alongside pps-gpio. The FT232RL/pps-ldisc path is not bought.
    - **Reason:** This keeps the HDMI and NPU kernel hold. libgpiod 1.6.3 (v1 uAPI) gives monotonic timestamps.
    - **Consequences:** Confirm with chronyc sourcestats in W1-2.
    - **Alternatives rejected:** Route B on kernel 7.0.11. A fallback on libgpiod v1.
  14.
    - **Question:** C14 INA228
    - **Decision:** Adafruit #5832 with its 15 mOhm shunt in the pack lead (ADCRANGE 0, ±10.9 A), so it counts charge and discharge.
  - VS comes from the always-on 3.3 V LDO.
  - Breakout pull-ups are removed.
  - It is read on I2C0 through user-space i2c-dev with no DT binding; labpowerd is the only owner; ALERT goes to header pin 3.
  - The Pico reads the pack through its own 1:6 divider for failsafe logic.
  - No second INA: NPU power is the A/B delta at the pack.
    - **Reason:** A bound ina238 driver blocks CHARGE access. A second I2C master on I2C0 would conflict.
    - **Consequences:** Fix npu_training ('on the J21 rail') and power.json (i2c6, hwmon).
    - **Alternatives rejected:** ina238 hwmon. I2C6 (shares SE6 with UART6). A second INA.
  15.
    - **Question:** C15 Antenna tiers
    - **Decision:** Two tiers built on shared parts:
  - **Patch / always carried:**
    - dipole kit #1 as the V-dipole (the LRPT default; 23 cm collapsed);
    - dipole kit #2 for AIS/FM;
    - 17 cm whip, or A-V85/SRH-701;
    - Uputronics 440 preamp;
    - RTL-SDR Blog L-band patch (Inmarsat-C, GNSS-SDR);
    - 4-turn helix on one shared 18 cm disc with SAWbird+ GOES;
    - GNSS antenna.
  - **Foldable backpack:**
    - crossed Yagi, ultra-compact build by default;
    - petal helicone (reuses the same disc, helix and SAWbird+ GOES);
    - gore horn (region-dependent);
    - HF wire and 9:1 balun;
    - Boni-Whip with its mast.
  
  No loops. Every small_antenna_stack removal is re-decided: Lime gated, T7 only with the Lime, 12 GB kept, foldables restored.
    - **Reason:** User rule lines 10-11. Shared parts cut weight and cost and let results carry over between tiers. Physics: patch and chip antennas cannot serve 137-146 MHz.
    - **Consequences:** The patch-tier helix loses an estimated 0.3-0.5 dB on 18 cm instead of 20 cm (model; rerun NEC). The 20 cm helical whip stays an experiment. The 2-turn helix and the SAWbird+ IR are dropped. The small rigid whips and helices need the user's confirmation.
    - **Alternatives rejected:** Two independent kits. A helical whip as the LRPT default. The single-tier rule.
  16.
    - **Question:** C16 Receive-only and policy leftovers
    - **Decision:** Strike every item on the register's list before STACK.md, plus:
  - **Remove TX-capable software:** QSSTV, fldigi and direwolf, which can transmit. Replace them with slowrx built from source, OpenWebRX+ SSTV, and SDRangel's RX-only packet demodulator for APRS (verify on the device).
  - **Add an operational loop definition** with a grep check: QFH, eggbeater, quad, delta, biquad, halo, big wheel, loopstick, H-probes.
  - **Inmarsat-C:** remove SatDump inmarsat_support and SDRangel demodinmarsat. Add a labd egc-gate that discards at header level and must pass a mixed-recording test; until it does, the profile ships disabled.
  - **Other filters:**
    - Artemis matches show only 'out of scope';
    - Bluetooth: rfkill plus USB de-authorisation;
    - band mask: 3-30 kHz and 225-400 MHz stored as 'no data';
    - DSC: distress, urgency and safety only;
    - SITOR and skimmers: on allow-listed frequencies only;
    - WEFAX: civil met services only (Northwood excluded, the USCG-run NWS stations excluded by default);
    - ADS-B tracks with dbFlags&1 and AIS type 35 are not shown or logged;
    - no voice IQ is kept;
    - no bearing logs.
  - **No antenna S11 steps anywhere;** the SWR page opens only in Bench mode with a load or DUT on the port.
    - **Reason:** Hard rules 1-2 and delegated rule lines 31-46. Line 44 forbids TX-capable software, so direwolf cannot stay even with an audited config.
    - **Consequences:** The radio_lab P20 fldigi steps move to SDRangel channels. A CI and self-test audit covers the banned list. The SAWbird+ iO purchase waits for the egc-gate.
    - **Alternatives rejected:** Keeping direwolf or QSSTV 'unconfigured'. Filtering Inmarsat-C after decoding. Brief indoor antenna sweeps.
  17.
    - **Question:** C17 HF antenna chain and the HF+ input selector
    - **Decision:** - **Boni-Whip:** fed 12.5 V ±0.25 V from a TPS7A4701 (EN on MCP #1 GPB1, DC-sense first, PTC holding 0.2 A at 60 C, provisional) through its own bias tee, which is mounted inside next to the HF+ can, so DC goes up the HF coax.
  - **Common-mode choke:** two-stage, on the coax at the HF bulkhead (FT-240-77 for LF/MF, FT-240-31 for HF; targets 1 kOhm or more at 60 kHz and 2-5 kOhm at 1-30 MHz, measured conducted on the LiteVNA). The bulkhead is bonded to the plate, with a ground stake or counterpoise at the antenna.
  - **Antennas:** the 9:1 wire is for HF only; LF time signals use the Boni-Whip on a mast of 2 m or more.
  - **HF+ selector:** two Omron G6K-2F-RF relays in series-shunt. De-energised, the HF+ sits on 50 ohm and both antenna ports are terminated. Acceptance: 35 dB or more of conducted isolation at 162-260 MHz, and 0.3 dB or less of loss from 10 kHz to 260 MHz.
  - **Ask the user** to confirm the HF-loop removal.
    - **Reason:** 12.5 V sits inside both published supply ranges (9-15 V and 12-15 V). Clip-on ferrites give little common-mode impedance below a few MHz, and an E-field whip receives shield common-mode noise directly. The G6K pair costs about GBP 43-52 (RS UK); the ARJ22A03 costs $114-332 and coax relays $242 or more. Non-latching relays fail safe to 50 ohm, and only one coil (about 0.12-0.15 W) is ever energised.
    - **Consequences:** Adds about $77-110 to the HF chain. The external ANT PWR jack is dropped. The labd DC-sense locks the Boni rail if the 9:1 balun (a DC short) is on the port.
    - **Alternatives rejected:** A 10.0 V or 12.0 V Boni rail. Clip-on ferrites only. Latching relays with zero hold current. ARJ22A03. HMC241 (its DC blocks hurt LF).
  18.
    - **Question:** C18 Storage, rollback and retention
    - **Decision:** Every variant gets an A/B root on the UFS: ESP 1 GiB, root A 22 GiB, root B 22 GiB, with systemd-boot boot counting and a rescue entry. /data is about 74 GiB, of which about 46 GiB are for recordings, with a 30 GiB rolling raw cap.
  - Products are kept by default; raw only when pinned.
  - The HF+ is recorded as ci16.
  - Without the Lime: a V30 endurance microSD (128-256 GB) is added when NAND prices allow.
  - With the Lime: T7 1 TB on the blue port, mounted outside on the bottom edge. It never writes during L-band, S-band or GNSS sessions; those are decimated to 1 Msps or less and written to UFS.
  - Updates come as GPG-signed bundles from a USB stick on LAB USB.
  - Data media carry no ESP.
    - **Reason:** Self-test plus rollback is a design rule and must not depend on an optional drive. The worst no-Lime stream is 13.3 MB/s, well inside UFS and microSD write speeds. USB 3 near the GNSS and L-band chains is a known jammer.
    - **Consequences:** lab-snap and the update path move off the T7. Recording space is about 40 min of two RTLs plus the HF+ raw, or about 50 min of two RTLs. The 'about 5 h on UFS' claim is deleted.
    - **Alternatives rejected:** One root plus a 6 GB rescue rootfs (interface lens: rollback would depend on removable media). The T7 without the Lime. HF+ recorded as cf32.
  19.
    - **Question:** C19 CPU allocation and RT priorities
    - **Decision:** - **CPU0-3 (A55):** UI, daemons, labclassify, and the ORT CPU fallback (CPUQuota 100%).
  - **CPU4-6, plus CPU7 without the Lime (A78):** labrx and the engines. RTL and HF+ ingest run at SCHED_OTHER nice -5.
  - **Trainer:** AllowedCPUs on the A78 cores at SCHED_IDLE, nice 19, MemoryMax 2G. It runs only between passes, with the SoC below 75 C and the battery above 25% or on a charger.
  - **With the Lime:** CPU7 is isolated (isolcpus, nohz_full and rcu_nocbs on 7, irqaffinity=0-6, Lime MSI moved off CPU7).
    - lime:Rx0 runs at SCHED_OTHER nice -20 if it busy-polls, or SCHED_FIFO 10 if it blocks; choose with the limeTRX loss counters.
    - labd pauses the loggers during Lime passes.
    - **Reason:** On an isolated core, SCHED_OTHER avoids the 950 ms/s RT throttle, which would leave gaps about as deep as the LA9310's 50 ms FIFO. The A78 pool is the scarce resource once CPU7 is isolated, and the trainer on the A55 cores would take about 2.5x longer.
    - **Consequences:** Fix lab_ui_hf (trainer on the A55 cores, CPU7 always isolated), npu_training (FIFO 50) and compute (chrt -f 10/50).
    - **Alternatives rejected:** FIFO 50 or 70 for ingest. CPU7 always isolated. The trainer on the A55 cores.
  20.
    - **Question:** C20 UI and NPU roadmaps
    - **Decision:** Merge into one plan:
  - NPU Phase 0 runs inside the W1-2 gates (19 Oct-1 Nov 2026). A minimal labeller and the 1.5 GiB ring move into P0b (Nov-Dec).
  - The HF-F and second-RTL profiles ship before any HF class appears in the UI.
  - **CPU-mode schedule (about 5 tiles/s):** RTL-C on both RTLs plus RTL-F at K=4 on the SDR with the active pass. HF-F runs only when the RTLs are idle, and a 'reduced coverage' chip shows in the UI.
  - **HTP promotion gate**, scaled to the SDR set: p99 of 28 ms or less at 50% duty without the Lime (16.6-17.6 tiles/s); 11.7 ms or less, or 41 tiles/s or fewer, with it. Plus an 8 h soak with fault injection.
  - **Phase-0 power tasks in the W1-2 gates:** INA228 logs per mode, the LF/HF regulator A/B, and the sealed-case test.
    - **Reason:** CPU mode (4-6 tiles/s) cannot cover 14.6-17.6 tiles/s. Every runtime and thermal number is a model until measured.
    - **Consequences:** The model rows in STACK.md are replaced by measurements.
    - **Alternatives rejected:** One fixed 11.7 ms gate. A labeller in Feb-Apr 2027. Measuring after assembly.
  21.
    - **Question:** C21 V4L count and continuous monitors
    - **Decision:** Buy 3 now from official channels ($113.85): RTL-A and RTL-B in service, plus 1 spare.
  - AIS runs on the HF+ VHF port.
  - Continuous ADS-B uses the FlightAware Pro Stick Plus (extended) on LAB USB.
  - Occasional sonde or ADS-B runs use the spare V4L on LAB USB.
  - No 4th V4L.
    - **Reason:** The R828S is end of life, and a spare that is always in service is not a spare. A purpose-built ADS-B receiver beats a V4L on dipole arms.
    - **Consequences:** Each V4L gets a unique EEPROM serial, with udev naming by serial. In the EU, buy through the official eBay or AliExpress 4523039 store.
    - **Alternatives rejected:** One V4L plus a spare. A 4th V4L for a 24/7 monitor.
  22.
    - **Question:** C22 Software recipes and pinning
    - **Decision:** Use the register recipes:
  - one venv per tool (NanoVNA-Saver via pipx, QtTinySA with PySide6 6.12, Skyfield 1.55 and sgp4 2.27, lab venv with numpy<2);
  - libgpiod v1 in labd;
  - SatDump 2.0-alpha, SDR++ and SDRangel 7.27.2 (RX-only) built from source as +labN debs;
  - OpenWebRX+ 1.2.126 with --no-install-recommends and exact-name pins.
  
  Add to them:
  - hold Mesa 25.2.8-0ubuntu0.24.04.4 with libdrm 2.4.125;
  - mirror every third-party .deb (OpenWebRX+, linux-headers 6.18.2-4, radxa firmware, qcom-qnn-sdk-v68) into the signed aptly repo and pin those sources to 100;
  - purge brltty and mask ModemManager;
  - mask the apt and fwupd timers;
  - build slowrx from source.
    - **Reason:** This resolves every recipe conflict and the Mesa ambiguity, protects against repositories drifting, and stops serial-port hijacking of the instruments and the Pico.
    - **Consequences:** Each tool is tested on the Q6A inside the return window.
    - **Alternatives rejected:** apt nanovna-saver 0.6.3. Skyfield 1.48. Unmirrored PPA installs. Mesa 24.0.5.
  23.
    - **Question:** C23 Region unknown
    - **Decision:** Build the LNB rail, the F port and the selector throw in every unit. Hold these purchases:
  - **Until the user is confirmed inside the Es'hail-2 footprint:** the Bullseye, the horn materials and the LNB injector choke.
  - **Until the egc-gate passes on L-band patch recordings:** the SAWbird+ iO. This is a compliance gate, not a region gate.
  - **Until the region is known:** the choice between the LC76G and the MAX-M10S.
  
  labd computes 'visible from here' flags for GEO targets from the GNSS fix, and enables UAT, HD Radio and NOAA SAME only in the matching region profile. EGNOS becomes 'regional SBAS'.
    - **Reason:** The rail costs about $10-20. The LNB is useless outside the QO-100 footprint, and Inmarsat-C is legal only with header-level discard.
    - **Consequences:** Ask the user for the region at the phase end, and check LNB IF ingress (DVB-T 734-742 MHz, the LTE B28 uplink) once it is known.
    - **Alternatives rejected:** Buying everything now. Buying for Europe by default.
  24.
    - **Question:** C24 Costs and weights
    - **Decision:** Adopt the integrated BOM (USD, before shipping, import VAT and duty):
  - core handheld $1,758-2,253;
  - antenna-patch $176-208;
  - antenna-foldable $351-625;
  - bench $1,475-1,810;
  - extended $498-708;
  - optional/gated $933-1,157, excluded from the roll-ups.
  
  Weights (model):
  - handheld 1.35-1.6 kg without the Lime;
  - field daypack 4.4-6.0 kg, or 5.3-7.3 kg with the HF kit and mast;
  - Pelican bench case 8.2-9.1 kg.
    - **Reason:** The old totals used the superseded antenna tier, Ukrainian price bases, and left out the selectors, chokes, cable set, pack build, weather kit, supports and charger.
    - **Consequences:** P5 re-prices every unverified line, and flash prices are treated as volatile.
    - **Alternatives rejected:** radio_lab's 3.0-3.6 kg sling. UAH price bases.
  25.
    - **Question:** C25 P1b completion
    - **Decision:** Closed: final/report_research.json exists (576,735 bytes). Still to do before STACK.md: the errata blocks in summaries.md and minute-log.md, including the stale power, interface, display-clock, ISS-frequency and sourcing lines listed in confirmed_issues.
    - **Reason:** The file is present and was read in full.
    - **Consequences:** None.
    - **Alternatives rejected:** None.
  26.
    - **Question:** D1 Battery cutoff and threshold table (4S)
    - **Decision:** - **Economy:** at 20% SoC, or V_N below 14.0 V loaded for 30 s.
  - **NPU:** no training below 25%; NPU off below 15%.
  - **Linux poweroff:** at 3% SoC, or V_N at or below 13.2 V loaded for 10 s. Show a 30 s banner, finalise SigMF, turn off bias, LNB, Boni and AUX, then poweroff (never halt).
  - **Pico failsafe:** if the divider reads 12.9 V or less for 5 s with no heartbeat, pulse #2813 OFF.
  - **Hardware supervisor on the always-on rail:** trips at 12.8 V and holds #2813 OFF; releases at 13.6 V at rest.
  - **D36V50F12 EN backstop:** divider ratio about 0.10, so it sleeps at about 12.0 V and wakes at about 13.5 V (Pololu EN thresholds 1.2/1.35 V).
  - **BMS:** 2.5-2.8 V/cell.
  - **Restart:** button only, with the pack at 13.6 V or more at rest.
  - **Temperatures:**
    - charging only with the cell NTC between 0 and 45 C;
    - shutdown above 60 C at the cell;
    - SoC shedding at 80 and 85 C;
    - panel derating to 50% above 60 C and 20% above 68 C.
  - **Gauge resync:** at 16.35 V with under 0.1 A, or at 16.3 V or more at rest at boot.
    - **Reason:** This recovers about 5 Wh against a 13.6 V cut and avoids BMS lock-out. The power lens's EN divider at 12.8 V would wake only at about 14.4 V and block restarts between 13.6 and 14.4 V.
    - **Consequences:** The register's 13.4 V hardware cut and the 13.6 V Linux cut are rejected. Bench-test whether holding OFF blocks the A-pin button; if it does not, gate the button line with the supervisor.
    - **Alternatives rejected:** A 13.6 V Linux cut. A 13.4 V hardware cut. A cut by the EN divider alone. Relying on the BMS alone.
  27.
    - **Question:** D2 Pack fuse
    - **Decision:** One value in both builds: a 7.5 A automotive mini blade fuse at the pack. Plus a 4 A blade on the J21 branch and a 3 A fuse on LAB5. Spares kit: 7.5 A, 4 A, 3 A and a 5 A service-lead fuse.
    - **Reason:** Peaks at the 13.2 V cutoff are 3.4 A without the Lime and 4.6 A with it, and charging runs up to 3 A. A 5 A fuse is marginal at 60 C (about 3.3 A continuous after derating). The #2813 (6 A at 55 C) and the BMS (15 A) sit above it.
    - **Consequences:** Wiring is AWG 18-20 in the pack path.
    - **Alternatives rejected:** 5 A without the Lime and 7.5 A with it (completeness lens).
  28.
    - **Question:** D3 Always-on rail scope, HMI/supervisor MCU placement and the power key
    - **Decision:** - **Always on:** only the AON 3.3 V LDO (TPS709 class, 30 V input, µA quiescent; verify), the INA228 and the UV supervisor. That is about 13-14 mW, or about 170-185 days of standby.
  - **The Pico runs on the switched LAB5 rail:**
    - It boots when the #2813 turns on.
    - If the Q6A's 40-pin 3.3 V has not appeared after 1-2 s, it pulls J21 pin 3 low for 0.8-1.0 s, never more than 2 s.
    - It sends a 6 s hold as a hard cut.
    - It opens the #2813 3 s after the Q6A's 3.3 V drops.
    - It tri-states its TX while the 3.3 V is low.
  - **Case button (sealed momentary, to GND):** reaches the #2813 A input (on-only), J21 pin 3 (wired-OR with the Pico's open drain) and a Pico sense pin, each through its own BAT54.
  - **Shutdown requests** go over UART7 to labinput and then labpowerd, with HandlePowerKey=ignore.
    - **Reason:** The #2813 switches the Pico on at the button press, so the boot pulse and hard cut do not need an always-on MCU. The supervisor covers undervoltage with no firmware. The board's own boot pulse (SGM811, about 0.2-0.6 s) is shorter than the 400 ms the UEFI wants.
    - **Consequences:** Standby carries no MCU drain and no TX back-feed into the UM3304. The display rail and all MCP enables are off whenever the Q6A is off.
    - **Alternatives rejected:** An always-on RP2040 (interface lens). Gating LAB5 on the Q6A's on-state (it would kill the boot pulse). The button straight to J21 pin 3 only.
  29.
    - **Question:** D4 Display power budget, acceptance and rail
    - **Decision:** - **Budget (model):** 3, 6 and 13 W at 25, 50 and 100%.
  - **Acceptance:** at least 1800 nits at full white; 14 W or less at 100% and 7.5 W or less at 50%, measured at the board input; stable with SYS12 at 11.0 V; 20 cold boots; USB-HID touch.
  - **Rail:** SYS12 → LC → 1.5 A eFuse (EN from the Pico). If the board is 5 V only, use a dedicated D36V28F5 #2 from SW, never LAB5 or a Q6A port.
  - **Dimming:** analog/DC preferred; 24.0 kHz only if the board requires PWM.
  - **Wiring:** no VBUS link to the Q6A; HDMI pin 18 cut or diode-blocked.
    - **Reason:** Comparable panels draw 6.5 W (4D, 1000 nits) and 10-18 W (2000-nit monitors). The Midas datasheet (6.4 W of LEDs at 2000 nits) shows that 9 W or less is possible, but it is not guaranteed.
    - **Consequences:** At 100% the runtime is about 1.3 h at peak load. Sustained 2000 nits in hot sun is a burst mode only (see the thermal plan).
    - **Alternatives rejected:** 9 W or less at full white as a hard limit (could reject a normal 2000-nit panel). The LAB5 or a Q6A port for a 5 V panel.
  30.
    - **Question:** D5 Panel choice deadline and case sequencing
    - **Decision:** Before paying, send Wisecoco written questions:
  - USB-HID VID:PID;
  - bonding and AR treatment;
  - input voltage and current;
  - an EDID dump;
  - whether the 151.50 MHz and 127.90 MHz modes are accepted;
  - the bridge's DSI mode and lane rate;
  - glove mode;
  - operating temperature;
  - package contents.
  
  Pay by PayPal only after satisfactory answers. With no clear answer in about 7 days, order the 4D 4DHDMI-70-1280-800-CT-EAR-1000 at DigiKey ($128.95, 13 in stock), together with labd's per-profile modeset table.
  
  Bezel and front-case CAD start only after the panel passes acceptance. The hood is 30 mm deep, hinged, and folds flat as a lid, with the VEML7700 outside it.
    - **Reason:** In sun, bonding sets contrast more than nits do (1.5:1 with an air gap against 6.2:1 bonded with AR at 100 klx). The listing still says 'I2C touch'. The case front depends on the real glass outline.
    - **Consequences:** The case design waits about 2-4 weeks for the panel.
    - **Alternatives rejected:** Designing for the inferred 164.2x98 mm outline now. Buying the Wisecoco unconditionally.
  31.
    - **Question:** D6 Thermal layout and pack placement
    - **Decision:** - **Pack:** in an insulated compartment along the bottom-left intake side, behind 3 mm closed-cell foam, reflective film and a 1 mm FR-4 or mica barrier with a vent path to outside. The NTC goes on the middle cell.
  - **Charger:** IP2368 pad-mounted to the case wall at least 10 mm from the cells, with a 70 C KSD9700. No charging in HF/LF Quiet.
  - **Two separate airflow paths:** the Q6A copper block with its 40 mm fan to a rear exhaust; and the display channel with its blower over the plate fins. Display air never pre-heats the Q6A fins.
  - **Bonded to the plate:** the D36V50F12 and both TPS7A4701.
  - **T7 (Lime only):** outside the case.
  - **Acceptance:** a 45 min noon soak with the hood, in modes B, D and G: frame 60 C or less, glass 65 C or less, cells 45 C or less.
    - **Reason:** In the model, cells downstream of the board reach 45-55 C at 35 C ambient. That blocks charging (the IP2368's 45 C NTC limit) and ages the cells.
    - **Consequences:** The case layout changes before the drawing.
    - **Alternatives rejected:** A 2x2 cell block under the board. One shared airflow path.
  32.
    - **Question:** D7 Pinecil, balance charging and the service port
    - **Decision:** - Run the Pinecil from the PD bank at 20 V (about 64 W).
  - A fused 5 A node-N service port sits downstream of the INA228 shunt. It is used for the ISDT 608PD monthly balance charge (master off) and, only if no bank is available, for the Pinecil with the receiver off and IronOS set to 4S, 3.3 V/cell.
  - Never tap the raw pack upstream of the shunt.
    - **Reason:** This keeps the coulomb count correct and the pack energy for receiving.
    - **Consequences:** The XT30-to-DC5525 lead is fitted to the service port.
    - **Alternatives rejected:** An XT30 tap upstream of the shunt.
  33.
    - **Question:** D8 VHF/UHF/L-band front-end topology across both antenna tiers
    - **Decision:** - **VHF-137 port:** unpowered external lead → Flamingo+ → SAWbird+ NOAA inside the case, in both tiers.
  - **UHF port:** the Uputronics 440 MHz CubeSAT filtered preamp (LNA, then 30 MHz SAW; GBP 51.59, in stock) is always the first part after the antenna. In the patch tier it screws onto the bulkhead; in the foldable tier it sits at the Yagi feed. Bias goes up the coax after DC-sense.
  - **L-band:** the LNA at the feed (SAWbird+ GOES, H1 or iO), or the active L-band patch.
  - **Selectors:** HMC7992 SP4T boards behind the injectors.
    - RTL-A: T1 VHF-137, T2 UHF, T3 WIDE/2 m (optional), T4 50 ohm.
    - RTL-B: T1 L-band, T2 LNB IF, T4 50 ohm.
    - The power-up default is 50 ohm.
    - **Reason:** At 137 MHz, 1-1.5 m of RG316 ahead of the LNA costs only 0.06-0.36 dB. At 437 MHz the same lead costs about 0.7-1 dB on CubeSat links with -5 to +5 dB margin. The Uputronics part closes the 'no buyable 70 cm filter' gap and follows the LNA-first rule at UHF.
    - **Consequences:** One SAWbird+ NOAA and one Flamingo+ serve both tiers. The Ham Filter Bank and the in-service LNA V2 drop out; the LNA V2 becomes the bench spare and the optional WIDE-path LNA.
    - **Alternatives rejected:** A 430-440 MHz BPF ahead of the LNA (kills 2 m and costs 0.75-2.84 dB at UHF). The 70 cm LNA inside the case. A SAWbird+ at the dipole feed. Manual 'connect X' as the default.
  34.
    - **Question:** D9 Ethernet on pcie0 in the field
    - **Decision:** The field DT overlay disables pcie0. It stays enabled only on home and bench boots. Add 'pcie0 on/off' to the A/B at 1700.000, 1575.000, 1600.0 and 400.000 MHz. If the 25 MHz NIC crystal still shows a line 3 dB or more above the floor, copper-tape the PHY to the mid-plate.
    - **Reason:** The schematic shows an RTL8125BG/RTL8111K footprint with a 25 MHz crystal on PCIE0. 25 MHz x68 and 100 MHz x17 both give 1700.000 MHz, the Meteor HRPT centre. 25 MHz x63 gives 1575.000 MHz, 0.42 MHz from L1.
    - **Consequences:** No wired Ethernet in the field; Wi-Fi only at home.
    - **Alternatives rejected:** Leaving pcie0 on and masking the HRPT centre line.
  35.
    - **Question:** D10 Noise-floor A/B method and spur mask
    - **Decision:** One A/B matrix replaces P4, the display A/B, the HF A/B and the small-stack tests:
  - **Method:** per used window, 60 s of IQ at 2.4 Msps, a 2^20 FFT (2.3 Hz bins) with Welch averaging. HF+: 1 Hz RBW at the LF and NAVTEX carriers. GNSS: mean C/N0 of the top 8 satellites from GSV, plus GNSS-SDR.
  - **States:** each toggled alone (see the RF noise plan).
  - **Conditions:** lid closed after a 30-minute warm soak.
  - **Pass:** no line 3 dB or more above the floor inside a used window; broadband rise of 0.5 dB or less; GNSS change of 1 dB-Hz or less.
  - **Output:** a versioned spur-mask file read by labrx, the SatDump wrapper, auto_rx, the NPU labeller and the UI.
    - **Reason:** At NF 5 dB the floor is -119 dBm in a 100 kHz bin against -165 dBm in 2.3 Hz. Lines that cost about 1 dB on CW, 1200 sym/s or H1 targets are invisible in rtl_power bins.
    - **Consequences:** About 4-5 h per full run and 30 min for the regression subset. It decides the 12 V regulator, the display mode and the pcie0 overlay.
    - **Alternatives rejected:** rtl_power at 100 kHz bins. A pass mark of a 1-2 dB broadband rise. u-blox UBX-MON-RF (the LC76G has none).
  36.
    - **Question:** D11 LAB 5 V, LAB port and LNA rail values
    - **Decision:** - **LAB5:** D36V28F5 (3.2 A) with a 3 A fuse.
  - **LAB USB-A:** a TPS2553 at 0.75 A, one setting for field and bench. The bench hub is bank-powered.
  - **LNA rail:** 2x LT3045 in parallel at 4.5 V.
  - **labd budget:** LAB port plus LNA current 1.5 A or less.
  - **Lime build:** if RTL-A on H2 together with a heavy LAB load pushes LAB5 above 2.5 A, switch the LAB port off during Lime recording, or upgrade to a D36V50F5 (price unverified).
    - **Reason:** The worst-case sum is about 2.0 A without the Lime and 2.3 A with it, against the old 2 A fuse. The largest field instrument draws about 0.45 A.
    - **Consequences:** Check the D36V28F5 temperature in the sealed case.
    - **Alternatives rejected:** A 2 A fuse. A 1 A LAB port (power lens). 0.6 A (interface lens). A single 0.5 A LT3045.
  37.
    - **Question:** D12 IMU interface and the HMI MCU
    - **Decision:** - **IMU puck:** RP2040-Zero plus Adafruit BNO085 in a metal shell bonded to the cable shield. It sends framed UART (115200, CRC) over a 1.5-2 m shielded 4-core lead with a GX12 4-pin locking socket and TVS, to the Pico's UART1. RS-485 only if the 1e6-frame test shows errors. The puck mounts 30 cm or more behind the driven elements, with a 31/43-mix ferrite.
  - **HMI MCU:** a Raspberry Pi Pico (26 GPIO). The 6 keys and 2 encoder pushes go on a PCA9555 on the Pico's I2C with INT.
    - **Reason:** The relay goes through the Pico's own UART, so it works whether or not UART7 does. The merged HMI and supervisor role needs 26-33 GPIO; the RP2040-Zero exposes 20 on its edge.
    - **Consequences:** Buy 2 Picos (one spare). The puck takes no USB port and puts no USB edges on the boom.
    - **Alternatives rejected:** A USB-CDC puck on CH334F H2 (sourcing lens). An RP2040-Zero as the HMI MCU. An RP2350B board. A 2x3 key matrix (still short of GPIO).
  38.
    - **Question:** D13 Expanders
    - **Decision:** MCP23017 #1 at 0x20 for all outputs, and MCP23017 #3 at 0x22 for inputs, with two output pins. Both are Adafruit 5346 ($5.95, verified in stock), powered from the Q6A's 3.3 V with 100k pull-downs, and driven by labd through smbus2. Their INTA/INTB outputs are mirrored, open drain, to header pin 5. The sled keeps MCP23017 #2 at 0x21 and the ADS1115 at 0x48.
    - **Reason:** About 18 outputs and 12 inputs are needed. GPA7 and GPB7 are output-only on current silicon. Power-up high-Z plus pull-downs means everything is off at power-up, and everything is off when the Q6A is off.
    - **Consequences:** The TCA9535 is the budget alternative.
    - **Alternatives rejected:** A single MCP23017. Header GPIOs. pinctrl-mcp23s08 (driver not built).
  39.
    - **Question:** D14 Field kit, packing and travel
    - **Decision:** - **Field:** a 15-20 L daypack carrying the handheld, the patch pouch, the foldable kit, the HF kit, the mast, the tripod and the field pouch.
  - **Bench:** a Pelican 1450 or Apache 3800 for the bench kit only.
  - **Travel:** the 72 Wh home-built pack is never flown; it travels by ground or stays home. The Anker 737 and the instruments with Li cells go in the cabin bag. The Pelican may be checked.
    - **Reason:** The model puts the field load at 5.3-7.3 kg full. A Pelican with the handheld would be 72% full and over cabin weight limits.
    - **Consequences:** The packing and weight tables in radio_lab are rewritten.
    - **Alternatives rejected:** A 10-12 L sling. The handheld inside the Pelican.
  40.
    - **Question:** D15 Case envelope and connector panel
    - **Decision:** Plan 220-225 x 135-140 x 55-60 mm with a right-hand HMI column 38-42 mm wide. Draw the CAD from Radxa STEP v1.21, the measured panel and the 46x25x150 mm pack.
  - **Top edge:** RF ports P1-P7 at a 20 mm pitch (optional P8; Lime RX1, RX2 and REF IN).
  - **Bottom edge:** IP2368 USB-C (the only power input), capped LAB USB-A, a 6-pin locking LAB BUS, 3.5 mm audio, the T7 exit (Lime).
  - **Back:** a captured 1/4-20 nut or press-in steel insert in a boss of 6 mm or more, strap lugs, the GX12 IMU socket, and a service hatch (console, blue-port EDL).
  - **Weather:** IPX4/IP54 target.
    - **Reason:** The old 205-215 x 130-140 x 50-55 mm footprint predates the HF+ can, the selectors, the LAB interface, the second V4L and the HMI. In the model, parts fill 58-75% of the old interior.
    - **Consequences:** The left-hand variant is a mirrored reprint. The Q6A USB-C has no case opening. IP67 is not reachable with forced-air cooling (physics).
    - **Alternatives rejected:** An HMI row below the display (162-166 mm tall). HMI on both sides (about 260 mm wide).
  41.
    - **Question:** D16 Physics and evidence that override the wishes
    - **Decision:** State these plainly in STACK.md:
  - Sustained brightness in 35 C noon sun is about 1000 nits; 2000 nits is a burst mode.
  - One-hand use means input, not holding; use the strap and the 1/4-20 tripod.
  - Patch and chip antennas cannot serve 137-146 MHz or HRPT.
  - QO-100 DATV and typical SSB need dish-class gain (26 and 31-32 dBi).
  - Without loops, HF is limited by local noise; the remote feed and the common-mode choke are the closest compliant option.
  - The 9:1 balun is rated from 0.125 MHz, so LF time signals rely on the active whip.
  - Inmarsat-C bits must be demodulated before any header filter can act.
  - Any antenna S11 sweep radiates.
  - Capacitive touch fails through gloves, so the keys and encoders must cover every capture-critical action.
    - **Reason:** Model: the panel reaches about 71 C at 35 C ambient in full sun at 100%, above its 70 C rating. The other items come from measurements, published ratings or link budgets in the register.
    - **Consequences:** Acceptance tests and menu labels reflect these limits.
    - **Alternatives rejected:** Promising sustained 2000 nits. Treating the whips as patch antennas.
- **Confirmed issues:**
  1.
    - **Area:** Software / SDR access model
    - **Components:**
      - npu_training sdr-ingestd/recorderd
      - lab_ui_hf labd leases + engine units
      - radio_lab lab-sched/lab-rec/rflab
      - SatDump
    - **Problem:** Three designs each claim to open the SDRs:
  - npu_training: sdr-ingestd is the only opener;
  - lab_ui_hf: the engines open the devices under leases;
  - radio_lab: advisory flocks plus its own SoapySDR recorder.
  
  A USB SDR accepts one opener, so the second open fails. The result would be two RAM rings, two recorders and advisory locks. During a live SatDump pass the NPU tap and the MARK pre-trigger ring would get no IQ.
    - **Severity:** blocker
    - **Fix:** Decision C7: one labd lease model with two modes.
  - labrx mode is the default: labrx is the sole opener, holds the ring and recorder, and fans out. Passes are recorded and then decoded by SatDump.
  - Engine-exclusive lease: the engine opens the device itself, with ai_tap=false and cgroup DeviceAllow.
  
  Delete the flocks and the 'only opener' rule, and rename the daemons into labrx and labclassify.
    - **Evidence:** npu_training final.architecture P1; lab_ui_hf resource_arbitration sections 5 and 7; radio_lab final.software; register #51; final_completeness dismissed gap (auto_rx needs direct access).
    - **Fix cost:** $0 hardware; about 1-2 person-weeks of re-specification (estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  2.
    - **Area:** Power budget / runtime
    - **Components:**
      - 4S1P P50B
      - IP2368 4.10 V/cell
      - labpowerd
    - **Problem:** Every file assumes 61-65 Wh usable and leaves loads out (HF+, LNB, Boni-Whip, fans, LAB port, converter losses), and under-counts the display.
  
  Usable energy is 58 Wh warm and new, and 50 Wh at 0 C or aged, once these are counted:
  - charging stops at 4.10 V/cell, which is 93% SoC on the OCV model;
  - the 13.2 V loaded cutoff.
  
  Runtimes (model):
  - LEO pass: 3.3 h, not 3.7-5.3 h;
  - Lime typical: 1.9 h, not 2.2-2.6 h.
    - **Severity:** major
    - **Fix:** Publish the per-mode table (power section) and plan on 58/50 Wh. Replace the model rows with INA228 logs at first power-up.
    - **Evidence:** p2_power/model.py (generic NMC/Si OCV curve, not a Molicel curve); my modes2.py; register #68.
    - **Fix cost:** $0
    - **Sources:**
      - https://www.molicel.com/inr-21700-p50b/
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p2_final/modes2.py
  3.
    - **Area:** Battery cutoffs and the EN backstop
    - **Components:**
      - labpowerd
      - D36V50F12 EN
      - Pololu #2813
      - UV supervisor
      - BMS
    - **Problem:** Four cutoff sets conflict: 13.6 V, 13.2 V, a 12.8 V hardware cut, and 'a hardware cut at 13.4 V or above'. A 13.4-13.6 V cut wastes about 5 Wh, although J21 tolerates the regulator's dropout.
  
  The power lens's EN divider at 12.8 V has a fault. Pololu's EN sleeps below 1.2 V and wakes above 1.35 V, so that divider would wake only at about 14.4 V, and a restart between 13.6 and 14.4 V at rest would fail.
  
  A cut by EN alone leaves LAB5 and the MCU draining the pack.
    - **Severity:** major
    - **Fix:** Decision D1:
  - Linux poweroff at 3% SoC or 13.2 V loaded for 10 s.
  - A supervisor on the always-on rail trips at 12.8 V and holds #2813 OFF, releasing at 13.6 V.
  - EN divider ratio about 0.10: sleep at about 12.0 V, wake at about 13.5 V.
  - BMS at 2.5-2.8 V/cell.
  - Restart by button only.
    - **Evidence:** Register #61, #67; power.json; lab_ui_hf process_supervision; Pololu 4095 EN thresholds (power lens fetch).
    - **Fix cost:** About $2-4
    - **Sources:**
      - https://www.pololu.com/product/4095
  4.
    - **Area:** Display power and input
    - **Components:**
      - Wisecoco 7in FHD 2000 nit
      - DISP12
    - **Problem:** The display is budgeted at 3.6-4.8 W at 60% and 6-8 W at full, with an acceptance limit of 9 W or less at full white. Comparable panels draw 6.5 W (4D, 1000 nits) and 10-18 W (2000-nit monitors). The board's input voltage and current are unknown; if it is 5 V only, it would need about 2.6 A, which neither LAB5 nor a Q6A port can supply.
    - **Severity:** major
    - **Fix:** Decision D4:
  - Budget 3/6/13 W.
  - Acceptance: at least 1800 nits; 14 W or less at 100%; 7.5 W or less at 50%.
  - Feed: SYS12 → LC → 1.5 A eFuse, or a D36V28F5 #2 if the board is 5 V only.
  - Dimming: DC.
  - Get the input range in writing.
    - **Evidence:** small_antenna_stack display impact; display_market acceptance; 4D datasheet (12 V, 540 mA); Midas datasheet (2000 nits, 6.4 W of LEDs).
    - **Fix cost:** $0, or $23.95 if the board is 5 V only
    - **Sources:**
      - https://resources.4dsystems.com.au/datasheets/4dhdmi/4DHDMI_Datasheet_R_1_0.pdf
      - https://www.farnell.com/datasheets/3984938.pdf
  5.
    - **Area:** LNB supply
    - **Components:**
      - Othernet Bullseye
      - LNB regulator
      - labd arbiter
    - **Problem:** Five incompatible LNB feeds appear across the files:
  - a TPS65233 at 13.4/18.2 V (radio_lab);
  - a switchable 13.4/18.2 V boost (rf_frontend, lab_ui_hf);
  - an MT3608/XL6009 behind a TPS2553, which is rated only 2.5-6.5 V and has no output disconnect (small stack);
  - the 12 V rail, which gives 10.6-11.4 V at the LNB (power.json);
  - an S18V20AHV SEPIC plus a second #2813 (sourcing).
  
  On 4S the pack stays at 13.2 V or more throughout, so no switcher is needed.
    - **Severity:** major
    - **Fix:** Decision C8:
  - TPS7A4701 at 13.2 V from the switched node through LC.
  - EN from MCP #1, enabled only while the RTL-B selector is on the LNB port.
  - PTC at 1.5-2x the measured current at 60 C; PG to MCP #3.
  - Delete every 18 V entry.
  - Acceptance: 0 V when off; 13.2 ±0.2 V under load.
    - **Evidence:** Register #102-105; TI TPS7A47 page (fetched 18 Oct 2026: 3-36 V in, adjustable to 34 V, 1 A, 307 mV dropout, θJA 30.5 C/W, fixed internal limit).
    - **Fix cost:** About $10-20
    - **Sources:**
      - https://www.ti.com/product/TPS7A47
  6.
    - **Area:** LNA rail and LAB 5 V budget
    - **Components:**
      - LT3045 LNA LDO
      - TPS2553
      - LAB 5 V D36V28F5
      - CH334F
      - HF+
    - **Problem:** Three problems with the LNA feed and LAB 5 V:
  - No file says what feeds the 'LT3045-class 5 V LNA LDO'. Fed from 12 V it would dissipate 2.45 W.
  - The LAB5 rail carries the hub, HF+, puck, Pico, the LAB port at 1 A and the LNA feeds, behind a 2 A fuse, while the sum of the limits is 2.0-2.4 A.
  - A single LT3045 (0.5 A) is below the sum of the feed limits.
    - **Severity:** major
    - **Fix:** Decision D11:
  - LNA rail: LAB5 → LC → 2x LT3045 in parallel at 4.5 V, with a TPS2553 at 300 mA per channel.
  - LAB5 fuse at 3 A; LAB port at 0.75 A.
  - labd budget: LAB port plus LNA current 1.5 A or less.
    - **Evidence:** power.json integration notes; register #62/#63; TI TPS2553 range (interface lens fetch).
    - **Fix cost:** About $5-15
    - **Sources:**
      - https://www.ti.com/product/TPS2553
  7.
    - **Area:** Bias rules and injector ratings
    - **Components:**
      - V4L tee
      - SAWbird+ NOAA/GOES/H1
      - TCBT-2R5G+
      - PTC
    - **Problem:** Final texts still break the bias rule:
  - rf_frontend: GOES+ on the V4L tee 'after a soak', and the LNA V2 on the tee;
  - radio_lab: H1 on the tee at 120 mA;
  - foldable step 3: a micro-USB feed at the antenna;
  - a 100-160 mA polyfuse that trips under 170-180 mA.
  
  Ratings that do not fit:
  - The TCBT-2R5G+ is rated 200 mA DC maximum, below a 250-300 mA limit.
  - A PTC sold as 250 mA hold derates to about 180-190 mA at 60 C.
    - **Severity:** major
    - **Fix:** Decision C9:
  - A TPS2553 at 300 mA nominal per channel.
  - Injector chokes rated 0.5 A or more; the TCBT only on channels drawing 150 mA or less.
  - V4L tees off in core; the spare's tee only for LNAs of 90 mA or less, with the token.
  - No micro-USB feeds; delete the polyfuse rule.
    - **Evidence:** rf_frontend verify; radio_lab sweeps; foldable build step 3; Mini-Circuits TCBT-2R5G+ datasheet (sourcing lens).
    - **Fix cost:** $0 text; the injector PCB is in the BOM
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/final_world_sourcing.json
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/rf_frontend.json
  8.
    - **Area:** Back-feed paths and off-state draw
    - **Components:**
      - Adafruit CH334F
      - LAB 5 V
      - Q6A VBUS/WS4612
      - display board VBUS and HDMI pin 18
      - touch bridge
      - Q6A USB-C
    - **Problem:** Several paths can back-feed or drain the pack:
  - If LAB5 powers the CH334F while the Q6A port's VBUS is also wired to it, two 5 V sources run in parallel and back-feed VCC_5V_PERI.
  - The display board can back-feed through USB VBUS or HDMI pin 18.
  - With the Q6A off, the touch bridge's D+ pull-up back-drives FE1.1s P2.
  - A charger on the Q6A USB-C while J21 is live back-feeds through Q5.
  - LAB5 and the display keep draining after poweroff.
    - **Severity:** major
    - **Fix:** Wiring rules:
  - Hub: D+, D- and GND only from the Q6A; its 5V pin from LAB5.
  - No VBUS link to the display board; HDMI pin 18 cut or diode-blocked.
  - The display rail eFuse is off while the Q6A is off.
  - All enables sit on expanders powered from the Q6A.
  - The Pico opens the #2813 3 s after the Q6A's 3.3 V drops.
  - The Q6A USB-C has no case opening.
  
  Acceptance with the FNB58: 0 V on Q6A VBUS and HDMI +5 V with the Q6A off and LAB5 on.
    - **Evidence:** Adafruit CH334F guide (power lens); register #62/#69/#129; power.json verify (Q5).
    - **Fix cost:** $0-2
    - **Sources:**
      - https://learn.adafruit.com/adafruit-ch334f-mini-4-port-usb-hub-breakout?view=all
  9.
    - **Area:** Q6A 5 V rail with the Lime
    - **Components:**
      - SGM40666AS/SY7120 VCC_5V_PERI
      - LimeSDR Micro
      - T7
    - **Problem:** With the Lime and the T7 on VCC_5V_PERI, the load is 15.4-20.6 W at spec allowances, against a limit of about 17 W. The overload would come exactly during wideband recordings. Typical draw is 9-12 W, and without the Lime it is 4-5 W.
    - **Severity:** major
    - **Fix:** A Lime gate: the measured VCC_5V_PERI must be 14 W or less in a 60-minute soak at 56 Msps with the T7 writing and RTL-B running. If it fails, give the T7 its VBUS from LAB5 through a split lead, and switch the LAB port off during Lime recording or upgrade LAB5.
    - **Evidence:** Register #63 (about 17 W); storage.json T7 budget; modes.py.
    - **Fix cost:** $0, or $5-40 if the gate fails
    - **Sources:**
      - https://www.sg-micro.com/product/SGM40666A
  10.
    - **Area:** LF/MF/HF spur sources
    - **Components:**
      - D36V50F12
      - D36V28F5
      - IP2368
      - fan PWM
      - backlight PWM
      - USB SOF
      - display line rate
    - **Problem:** These spur sources are uncontrolled:
  - the D36V50F12 runs at about 500 kHz under heavy load and enters a power-save mode above 20 kHz at light load, near NAVTEX 490/518 kHz and across the 40-162 kHz carriers;
  - the IP2368's 250 kHz has its 2nd harmonic at 500 kHz;
  - 1, 20 and 30 kHz PWM put harmonics exactly on 40/60 kHz;
  - USB frames at 1 and 8 kHz give exact lines;
  - the display line rate at 127.9 MHz is 58.14 kHz, 1.86 kHz from 60 kHz.
  
  No plan tests below 500 kHz.
    - **Severity:** major
    - **Fix:** Run the regulator A/B gate (decision C4). Fans in DC with no PWM; backlight DC (24.0 kHz only if PWM is unavoidable); a 151.50 MHz field clock (line rate 68.86 kHz). In the LF Quiet profile: charger unplugged, only the HF+ streaming, pcie0 off, Wi-Fi de-authorised. The SID baseline is taken on a terminated input in the same profile.
    - **Evidence:** Pololu 4095 (power lens fetch); rfcx/lf.py; my pclk.py.
    - **Fix cost:** $0 for the test; about $10-30 per regulator swap if it fails
    - **Sources:**
      - https://www.pololu.com/product/4095
  11.
    - **Area:** Thermal inside the case
    - **Components:**
      - P50B pack
      - IP2368
      - panel
      - Q6A
      - T7
    - **Problem:** Model results:
  - internal heat is 8-36 W without the Lime and 30-53 W with it;
  - at 35 C ambient, cells downstream of the board reach 45-55 C, so the 45 C charge NTC blocks charging;
  - the panel at 100% in full sun reaches about 71 C, above its 70 C rating;
  - the SoC reaches 85-100 C at peak and throttles;
  - the T7 (Lime only) sits near its 60 C limit inside.
    - **Severity:** major
    - **Fix:** Decision D6:
  - insulated pack compartment on the intake side;
  - IP2368 at least 10 mm from the cells, with a KSD9700;
  - two separate airflow paths;
  - panel derating ladder;
  - training gated on SoC below 75 C;
  - T7 outside the case;
  - 45 min noon soak acceptance.
    - **Evidence:** p2_power/thermal.py; register #17/#18; panel rated -20 to 70 C (Youritech page, power lens).
    - **Fix cost:** About $5-10
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p2_power/thermal.py
  12.
    - **Area:** Header GPIO safe state
    - **Components:**
      - UM3304 TXB buffers
      - 40-pin header
      - bias/LNB/relay enables
    - **Problem:** lab_ui_hf drives the RF switches, relays, LNA, LNB, 12 V and VBUS-cut lines from header GPIOs. Pin 7 and pins 11-40 sit behind UM3304 TXB-type buffers (4 kOhm, 50 pF or less, pulls must be over 50 kOhm). Their state follows the SoC during UEFI and boot, so 'pull-downs keep every supply off' cannot work on them. The LNB or a bias feed could switch on into a DC short during boot, and these lines cannot drive coils or MOSFET gates.
    - **Severity:** major
    - **Fix:** Move every enable to the MCP23017s (decision D13). They power up high-Z with 100k pull-downs and are powered from the Q6A's 3.3 V. Header GPIOs carry only PPS, the UARTs, I2C, open-drain INT/ALERT, SWD and safe-boot.
    - **Evidence:** gnss_imu own fix (UM3304 TXB-type); q6a_sch.txt translator blocks (grep confirms UM3304/UM3204H/CJ3134K).
    - **Fix cost:** About $6-12
    - **Sources:**
      - https://www.union-ic.com/upload/Datasheet/Datasheet_UM3304_Rev16.pdf
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_sch/q6a_sch.txt
  13.
    - **Area:** HMI / power-supervisor MCU role
    - **Components:**
      - display RP2040
      - HMI RP2040
      - power MCU
      - NPU buttons
    - **Problem:** Each file gives the RP2040 a different role and link:
  - radio_lab: on CH334F H1, powered from LAB5;
  - lab_ui_hf: merged HMI on UART7;
  - power.json: an always-on MCU;
  - the register: on both H1 and UART7.
  
  It is also unclear how the cold-boot pulse works. The board's own SGM811 pulse (about 0.2-0.6 s) is shorter than the 400 ms the UEFI wants.
    - **Severity:** major
    - **Fix:** Decision D3: one Pico on the switched LAB5 rail.
  - Boot pulse on J21 pin 3 for 0.8-1.0 s when the Q6A's 3.3 V is absent.
  - 6 s hard cut.
  - Opens the #2813 after poweroff; tri-states its TX while the Q6A is off.
  - UART7 is the main link, with native USB on H1 as a fallback.
  
  The always-on rail powers only the INA228 and the UV supervisor.
    - **Evidence:** power.json SGM811 analysis; Pololu #2813 page (fetched 18 Oct: on-only wiring by putting the switch between A and ground; ON/OFF high pulse above 1 V).
    - **Fix cost:** $0-5
    - **Sources:**
      - https://www.pololu.com/product/2813
  14.
    - **Area:** Bias-tee interlock in software
    - **Components:**
      - librtlsdr rtlsdr_set_bias_tee
      - engines
      - rtl_biast
    - **Problem:** Any process that opens a V4L can switch its bias tee on, including SatDump, readsb, OpenWebRX+ and rtl_biast. That bypasses labd's interlock on DC-short antennas (the 9:1 balun and hairpin feeds). Rule line 44 requires a labd token.
    - **Severity:** major
    - **Fix:** Add a token patch to the .so.2 rebuild (bias refused unless LAB_BIAS_OK equals the device serial), divert rtl_biast, keep the EEPROM bias off, and audit engine configs for bias options.
    - **Evidence:** user_requirements.md line 44; register #102.
    - **Fix cost:** $0 (about 20 lines of C plus a test)
    - **Sources:**
      - https://github.com/osmocom/rtl-sdr
  15.
    - **Area:** USB port map overflow and the IMU interface
    - **Components:**
      - blue USB 3.1
      - FE1.1s
      - CH334F
      - IMU puck
      - T7
    - **Problem:** Four maps exist, and the register's map fills all four CH334F ports. With the Lime and T7 kept, RTL-A has nowhere to go. If the IMU is a USB-CDC device (gnss_imu, radio_lab, sourcing) or UART7 fails, a fifth port is needed. lab_ui_hf time-shares the only SuperSpeed port. The '3 continuous streams' rule blocks the monitor configuration.
    - **Severity:** major
    - **Fix:** Decision C5: the IMU always goes over UART to the Pico; RTL-A moves to H2 with the Lime; a second CH334F is bought but fitted only when needed; an aggregate cap of 25 MB/s replaces the stream rule.
    - **Evidence:** Register #130; gnss_imu final; sourcing decision 6.
    - **Fix cost:** $4.95
    - **Sources:**
      - https://www.adafruit.com/product/5997
  16.
    - **Area:** NPU CPU-mode coverage
    - **Components:**
      - inferd-cpu
      - fusiond
      - RTL-F/RTL-C/HF-F profiles
    - **Problem:** Until the HTP gate passes, inference runs on the CPU at 4-6 tiles/s, while demand is 14.6 tiles/s for two V4Ls (verified) and about 16.6-17.6 with HF-F (model). The broker would silently drop about two thirds of the tiles.
    - **Severity:** major
    - **Fix:** Decision C20: an explicit CPU-mode schedule of about 5 tiles/s, a 'reduced coverage' chip in the UI, and an HTP gate scaled to the SDR set (28 ms or less without the Lime, 11.7 ms or less with it).
    - **Evidence:** npu_training budgets; register #42.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  17.
    - **Area:** RAM ring over-commit
    - **Components:**
      - labrx ring
      - labclassify
      - trainer
      - engines
    - **Problem:** Four ring sizes appear: npu_training 6/8 GiB, storage 8 GiB mlocked, the register 4/1.5 GiB, and lab_ui_hf about 4 GiB. With a 6 GiB ring in training mode, the 12 GB board (about 11.3 GiB visible) has -1.2 to +1.1 GiB free (model), so the OOM killer would take SatDump or the Shell.
    - **Severity:** major
    - **Fix:** Size the ring once at boot: 1.5 GiB without the Lime; 4 GiB with it, plus a 3 GiB Burst segment only in an exclusive profile. Delete the 6 and 8 GiB values, and apply the OOM and memlock policy.
    - **Evidence:** lens_rlm/calc/budgets.py; sbc-bench KBw_ (6 GB board shows 5609 MB); Geerling #85 (8 GB board shows 7604 MiB).
    - **Fix cost:** $0
    - **Sources:**
      - https://github.com/geerlingguy/sbc-reviews/issues/85
      - https://raw.githubusercontent.com/ThomasKaiser/sbc-bench/master/results/KBw_.txt
  18.
    - **Area:** CPU allocation and RT priorities
    - **Components:**
      - lime:Rx0
      - labrx ingest
      - trainer
      - CPU7
    - **Problem:** The files give four core plans and four RT settings:
  - compute: chrt -f 10;
  - npu_training: FIFO 50 on CPU7;
  - wideband verify: FIFO 70 on CPU4-6;
  - lab_ui_hf: CPU7 always isolated and the trainer on the A55 cores.
  
  If lime:Rx0 busy-polls, RT throttling leaves gaps about as deep as the LA9310's 50 ms FIFO.
    - **Severity:** major
    - **Fix:** Decision C19.
    - **Evidence:** compute, npu_training, wideband_sdr, lab_ui_hf; register #20.
    - **Fix cost:** $0; about 1 day of bench time
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/compute.json
  19.
    - **Area:** Noise-floor A/B method
    - **Components:**
      - radio_lab P4
      - display A/B
      - HF A/B
      - LC76G
    - **Problem:** Every coexistence decision depends on an A/B test that cannot see narrowband spurs. rtl_power at 100 kHz bins has a floor of -119 dBm, while a line at -158 dBm already costs about 1 dB on a CW, 1200 sym/s or H1 target.
  
  Other gaps:
  - four separate band lists;
  - no LF carriers or NAVTEX in the plan;
  - a GNSS pass mark that needs UBX-MON-RF, which the LC76G does not have;
  - no states for the pcie0, HDMI or rails.
    - **Severity:** major
    - **Fix:** Decision D10: one narrow-RBW A/B matrix plus a spur-mask file.
    - **Evidence:** radio_lab procedures[4]; display_market acceptance; rfcx/stage.py.
    - **Fix cost:** $0; about 4-5 h per run
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/stage.py
  20.
    - **Area:** Board clocks: onboard Ethernet on pcie0
    - **Components:**
      - RTL8125BG/RTL8111K
      - 25 MHz crystal
      - pcie0 refclk
    - **Problem:** The 1700.000 MHz line was credited only to the Lime. The Q6A's own NIC sits on PCIE0 with a 25 MHz crystal (schematic: '25MHz_12PF_10ppm').
  - 25 MHz x68 and 100 MHz x17 both give 1700.000 MHz (the HRPT centre).
  - 25 MHz x63 gives 1575.000 MHz.
  - There are further lines at 1600.0 and 400.000 MHz.
  - The Bullseye's 25 MHz reference adds the same lines.
    - **Severity:** major
    - **Fix:** Decision D9 (pcie0 off in the field), an LNB EN interlock, and copper tape if the crystal still radiates.
    - **Evidence:** q6a_sch.txt PCIE0 and RTL8125BG/RTL8111K blocks (grep confirmed); rfcx/harm.py.
    - **Fix cost:** $0-2
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_sch/q6a_sch.txt
  21.
    - **Area:** FM band-stop placement
    - **Components:**
      - Flamingo+ FM
      - SAWbird+ NOAA
      - LNA V2
    - **Problem:** The power lens puts the Flamingo+ on the SDR side of the injector, which is after the LNA, and rf_frontend chain (b) does the same. The first MMIC of the SAWbird+ NOAA, and of the LNA V2, then sees the whole FM band unfiltered.
    - **Severity:** major
    - **Fix:** Decision C10: filter first at VHF. Bias enters at the LNA output, so no DC crosses the filter.
    - **Evidence:** rf_frontend verify issues[4]; Nooelec Flamingo+ page (RF lens fetch: -3 dB at 75/120 MHz, more than 60 dB rejection, 250 mA DC pass).
    - **Fix cost:** $0
    - **Sources:**
      - https://www.nooelec.com/store/flamingo-plus-fm.html
  22.
    - **Area:** HF/LF common-mode path
    - **Components:**
      - HF+ Discovery
      - Boni-Whip
      - 9:1 balun
      - feed coax
    - **Problem:** The remote feed point helps only if the coax shield does not carry the handheld's common-mode noise out to the antenna. Clip-on ferrites give little impedance below a few MHz. For an E-field whip, the shield's common-mode noise is received directly (PA3FWM tn07).
    - **Severity:** major
    - **Fix:** Decision C17: a two-stage common-mode choke with a measured impedance, the bulkhead bonded to the plate, and a ground stake.
    - **Evidence:** lab_ui_hf hf_antenna setup[3]; PA3FWM tn07.
    - **Fix cost:** About $15-30 (unverified)
    - **Sources:**
      - https://www.pa3fwm.nl/technotes/tn07.html
  23.
    - **Area:** HF+ input selector
    - **Components:**
      - Airspy HF+ (single SMA)
      - selector relays
    - **Problem:** No part is named, yet the AIS-on-HF+ default and the terminated-floor state both depend on it. Coax relays cost $242 or more, and the ARJ22A03 costs $114-332 and is NRND at one distributor.
    - **Severity:** major
    - **Fix:** Decision C17: two Omron G6K-2F-RF relays in series-shunt, defaulting to 50 ohm, with an isolation and loss acceptance test.
    - **Evidence:** Register #94; RF lens RS listings (about GBP 21-26 each, ex VAT).
    - **Fix cost:** About $62-80
    - **Sources:**
      - https://uk.rs-online.com/web/p/hf-rf-relays/0492917?gb=s
  24.
    - **Area:** VHF/UHF front-end topology and the 70 cm part
    - **Components:**
      - 70 cm whip/Yagi
      - LNA V2
      - 70 cm BPF
      - SAWbird+ NOAA
      - two antenna tiers
    - **Problem:** A single 2 m/70 cm input with a 430-440 MHz BPF ahead of the LNA kills 2 m. At UHF it costs 0.75-2.84 dB (model) on CubeSat links with only -5.3 to +5.3 dB of margin. No 70 cm filter part was named, and the two tiers ask for opposite topologies on RTL-A. Each RTL also has one SMA but 2-4 antenna sources.
    - **Severity:** major
    - **Fix:** Decision D8:
  - Uputronics 440 MHz CubeSAT filtered preamp at the antenna end.
  - The 137 MHz chain inside the case.
  - Separate ports, with an HMC7992 SP4T selector per RTL.
    - **Evidence:** rfcx/stage.py; final_world_sourcing (Uputronics GBP 51.59, available); final_completeness missing parts.
    - **Fix cost:** $68.71 plus about $30-40 for the selectors
    - **Sources:**
      - https://store.uputronics.com/products/uputronics-filtered-preamps
  25.
    - **Area:** Display field clock
    - **Components:**
      - Wisecoco HDMI-MIPI board
      - EDID override
      - RA620
    - **Problem:** 128.70 MHz is still in display_market, small_antenna_stack and the lab_ui_hf tests; its 12th harmonic (1544.4 MHz) falls in Inmarsat-C.
  - The register's 127.9 MHz sits only 0.14 MHz below the top of its clean window (my scan).
  - The CEA VIC list still lets the compositor fall back to 148.5 MHz.
  - The DSI clock is 3x the pixel clock only in non-burst mode.
    - **Severity:** major
    - **Fix:** Decision C12: 151.50 MHz first and 127.90 MHz second, CEA VICs stripped, and the delivered clock verified.
    - **Evidence:** p2_final/pclk.py (clean intervals 148.11-153.27 and 123.62-128.04 MHz without the Lime); register #78.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/p2_final/pclk.py
  26.
    - **Area:** Storage rollback
    - **Components:**
      - UFS
      - T7 lab-snap
      - offline update bundle
    - **Problem:** The rollback snapshots and the offline update path both live on the T7, which is bought only if the Lime is kept. A no-Lime build would have no rollback, although self-test plus rollback is a design rule.
    - **Severity:** major
    - **Fix:** Decision C18: an A/B root on UFS, and update bundles from a USB stick on LAB USB.
    - **Evidence:** lab_ui_hf packaging_and_updates; register #36.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  27.
    - **Area:** Case envelope
    - **Components:**
      - ASA shell
      - HMI
      - HF+ can
      - selectors
      - pack
    - **Problem:** The 205-215 x 130-140 x 50-55 mm, 1.2-1.4 kg envelope predates the HF+ and its can, the selectors, the LAB interface, the second V4L and the HMI column. In the model, parts fill 58-75% of that interior. Pack geometry also conflicts between files (86x71x22 vs 46x25x150 mm).
    - **Severity:** major
    - **Fix:** Decision D15: 220-225 x 135-140 x 55-60 mm, 1.35-1.6 kg, CAD drawn from the STEP file and the measured panel.
    - **Evidence:** mechanical_thermal verify; lens_rlm/calc/mech.py.
    - **Fix cost:** $0 design; about $10-27 for a reprint
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/mechanical_thermal.json
  28.
    - **Area:** Connector panel
    - **Components:**
      - RF bulkheads
      - F port
      - HF post
      - LAB BUS
      - IMU socket
    - **Problem:** No file has a single connector list. The IMU puck has no case socket, and the HF+ 'VHF bus' has no source. There are 11-14 case penetrations with no IP target.
    - **Severity:** major
    - **Fix:** Decision D15 panel (P1-P7 at a 20 mm pitch) plus the IPX4/IP54 weather kit.
    - **Evidence:** radio_lab internal_vs_external; final_completeness gaps.
    - **Fix cost:** About $15-30
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/final_completeness.json
  29.
    - **Area:** Packing, carried weight and supports
    - **Components:**
      - sling
      - foldable kit
      - mast
      - tripod
      - Pelican
    - **Problem:** radio_lab still uses the superseded antenna tier (sling 3.0-3.6 kg). The foldable kit alone is 6-6.5 L and 1.3-1.8 kg. The mast and tripod are not counted anywhere. A Pelican holding the handheld as well would be over cabin weight limits.
    - **Severity:** major
    - **Fix:** Decision D14: a 15-20 L daypack (5.3-7.3 kg full), the Pelican for the bench kit only, and the supports added to the BOM.
    - **Evidence:** foldable_antennas totals; mech.py.
    - **Fix cost:** About $135-305 (bags and supports, estimate)
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
  30.
    - **Area:** Display bonding, outline and touch unknown
    - **Components:**
      - Wisecoco
      - 4D fallback
    - **Problem:** Bonding, the glass outline (164.2x98 mm is inferred), the touch path and the input supply are all unconfirmed, and the listing still says I2C touch. An air-gapped 2000-nit panel (1.5:1 in sun) is worse than the bonded 1000-nit 4D (1.7:1).
    - **Severity:** major
    - **Fix:** Decision D5: written answers within about 7 days, or buy the 4D at DigiKey for $128.95. The bezel CAD starts only after acceptance.
    - **Evidence:** display_market; final_world_sourcing (listing text and 4D price verified).
    - **Fix cost:** $0
    - **Sources:**
      - https://www.wisecocodisplay.com/product/7-inch-1920x1080-high-brightness-2500nits-lcd-panel-with-hdmi-in-board-ips-mipi-interface-tft-lcd-screen/
  31.
    - **Area:** TX-capable software
    - **Components:**
      - QSSTV 9.5.8
      - direwolf
      - fldigi in radio_lab procedures
    - **Problem:** lab_ui_hf installs QSSTV, which can transmit with PTT. direwolf is a TNC that can beacon and digipeat. The radio_lab procedures depend on fldigi. Rule line 44 forbids TX-capable software on the device.
    - **Severity:** major
    - **Fix:** Remove all three. Use slowrx, OpenWebRX+ SSTV and the SDRangel RX-only packet demodulator, and move the fldigi procedures to SDRangel channels. Add the CI and self-test audit.
    - **Evidence:** lab_ui_hf tech_stack; radio_lab procedures; user_requirements.md line 44.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/user_requirements.md
  32.
    - **Area:** 12 V regulator capacity and stock
    - **Components:**
      - D36V50F12
    - **Problem:** At the Lime peak the output reaches about 3.6-4.1 A, against 4.5 A typical (limited by heat) in a sealed 45-50 C case. Stock is 'Rationed'.
    - **Severity:** minor
    - **Fix:** Bond it to the plate and run the 3.5 A, 60-minute sealed test. Buy 2. If the Lime is kept and the test fails, AUX must be off during Lime peaks.
    - **Evidence:** Pololu 4095 (power lens).
    - **Fix cost:** $39.95 for the spare
    - **Sources:**
      - https://www.pololu.com/product/4095
  33.
    - **Area:** TVS values
    - **Components:**
      - SMBJ14A at J21
      - node N
    - **Problem:** The SMBJ14A's breakdown voltage can reach 17.2 V, above the 16 V input capacitors. Node N has no TVS.
    - **Severity:** minor
    - **Fix:** SMBJ13A at J21 (VRWM 13 V, breakdown 14.4-15.9 V); SMBJ17A at node N. Balance-charge with the master switch off.
    - **Evidence:** Standard SMBJ catalogue values (not re-fetched).
    - **Fix cost:** About $0.5
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_sch/q6a_sch.txt
  34.
    - **Area:** Gauge integrity
    - **Components:**
      - Pinecil
      - ISDT 608PD
      - INA228
    - **Problem:** The Pinecil (about 43 W) and the 4.20 V balance charge connect through the pack's XT30, which may sit upstream of the shunt. The coulomb count then drifts without the gauge knowing.
    - **Severity:** minor
    - **Fix:** Decision D7: a fused node-N service port downstream of the shunt, and the Pinecil on the PD bank.
    - **Evidence:** radio_lab lab_bom; register #66.
    - **Fix cost:** $0
    - **Sources:**
      - https://ralim.github.io/IronOS/Settings/
  35.
    - **Area:** Charger source qualification
    - **Components:**
      - IP2368 BZ
      - PD sources
    - **Problem:** At 3 A the charger draws about 49-52 W. A 45 W source may be overloaded (behaviour unverified). Charging while running mode B takes about 2.5 h.
    - **Severity:** minor
    - **Fix:** Qualify each PD source with the FNB58. For 45 W sources use the input-power mode (bench-verify the RISET value). The UI shows 'charging paused (cell hot)'.
    - **Evidence:** IP2368 datasheet V1.41 (power verify).
    - **Fix cost:** $0
    - **Sources:**
      - https://datasheet.lcsc.com/datasheet/pdf/752f0c4a0b5b0a79a7f68752c4eac200.pdf?productCode=C5203723
  36.
    - **Area:** Unpublished currents
    - **Components:**
      - HF+
      - Boni-Whip
      - Bullseye
      - Uputronics 440
      - LNA V2
      - ZFL-500
    - **Problem:** There are no published currents for these parts, so every rail limit is provisional.
    - **Severity:** minor
    - **Fix:** Provisional budgets: HF+ 0.3 A at 5 V; Boni-Whip 0.1 A at 12.5 V; LNB 0.3 A at 13.2 V; Uputronics and LNA V2 0.1 A; noise source 0.15 A. Measure each on arrival, cold and hot, then set the PTC and TPS2553 values.
    - **Evidence:** Register open question 15; rtl-sdr.com power article (figures only in a video).
    - **Fix cost:** $0
    - **Sources:**
      - https://www.rtl-sdr.com/measuring-the-usb-power-consumption-of-various-software-defined-radios/
  37.
    - **Area:** Fan control
    - **Components:**
      - header pin 33 / GPIO56
      - AO3400
      - PoE-HAT overlay
    - **Problem:** Pin 33 sits behind a UM3304 (50 pF or less), which cannot drive an AO3400 gate. The PoE-HAT overlay's 1 kHz PWM puts harmonics on 40/60/162/490/518 kHz. The register's 'GPIO56 vs pin 33' conflict is about one physical pin.
    - **Severity:** minor
    - **Fix:** DC on/off from the Pico, failing safe to on (decision C6). Pin 33 stays spare.
    - **Evidence:** q6a_sch.txt (GPIO_56 = FP_SPI_MISO = pin 33, interface lens).
    - **Fix cost:** About $0.5
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/dl_sch/q6a_sch.txt
  38.
    - **Area:** Bus electrical details
    - **Components:**
      - UART7 (UM3304)
      - I2C2 (UM3204H)
      - TCA9517
      - MCP23017 GPA7/GPB7
      - display I2C-touch fallback
    - **Problem:** Several bus details are unresolved:
  - The UART7 overlay exists upstream, but the held image may not ship it, and the UM3304's 50 pF limit restricts wire length.
  - The UM3204H (TXS-type with 10k pull-ups) is sensitive to extra low-value pull-ups and to the orientation of the TCA9517.
  - GPA7 and GPB7 are output-only on current MCP23017 silicon.
  - The display I2C-touch fallback collides with UART6 (SE6), PPS (GPIO96) and the SWD pins.
    - **Severity:** minor
    - **Fix:** - Compile the uart7 overlay if needed; keep wires to 20 cm or less, or add a 74LVC2T45.
  - TCA9517: port A to the header, port B to the cable; 4.7k on the sled side; 100 kHz; PCA9615 for runs over 1 m.
  - Pass 1e6 reads with zero errors (i2cdetect -r).
  - Use GPA7 and GPB7 as outputs.
  - Accept only USB-HID touch panels.
    - **Evidence:** radxa-overlays uart7.dtso (interface lens fetch); gnss_imu; MCP23017 rev D/E.
    - **Fix cost:** $0-2
    - **Sources:**
      - https://raw.githubusercontent.com/radxa-pkg/radxa-overlays/main/arch/arm64/boot/dts/qcom/overlays/qcs6490-radxa-dragon-q6a-uart7.dtso
  39.
    - **Area:** HMI MCU GPIO budget
    - **Components:**
      - RP2040-Zero
      - HMI firmware
    - **Problem:** The merged HMI and supervisor role needs 30-33 lines (encoders, keys, two UARTs, I2C, backlight, display rail, fans, piezo, LED, button, J21 pin 3, OFF, Q6A sense, safe-boot, 3 ADC). The RP2040-Zero exposes 20 GPIO on its edge.
    - **Severity:** minor
    - **Fix:** Decision D12: a Pico with 26 GPIO, plus a PCA9555 for the 8 switches.
    - **Evidence:** lab_ui_hf HMI row; interface lens count.
    - **Fix cost:** About $5-10
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  40.
    - **Area:** Power key wiring
    - **Components:**
      - case button
      - J21 pin 3
      - #2813
      - Pico
    - **Problem:** power.json wires the button straight to pin 3, and lab_ui_hf has the MCU pulse pin 3. Neither says how they coexist with the #2813 button input, whose A-B wiring toggles power, so a press would cut power hard.
    - **Severity:** minor
    - **Fix:** Decision D3: the button goes to GND and reaches the #2813 A input (on-only), pin 3 and the Pico through BAT54s. The pulse never exceeds 2 s.
    - **Evidence:** Pololu #2813 page (fetched 18 Oct).
    - **Fix cost:** About $1
    - **Sources:**
      - https://www.pololu.com/product/2813
  41.
    - **Area:** Hard-cut sensing and the INA228 owner
    - **Components:**
      - INA228
      - Pico ADC
      - labpowerd
    - **Problem:** The MCU hard cut needs a pack voltage reading. The INA228 is owned by labpowerd, and a second I2C master would conflict.
    - **Severity:** minor
    - **Fix:** The Pico gets its own 1:6 divider for the failsafe; the UV supervisor provides the hardware cut. INA228 ALERT goes to pin 3.
    - **Evidence:** Register #66.
    - **Fix cost:** About $0.1
    - **Sources:**
      - https://www.adafruit.com/product/5832
  42.
    - **Area:** OS and USB hygiene
    - **Components:**
      - FCU760K Wi-Fi/BT
      - ModemManager
      - brltty
      - Mesa
      - PPA/Radxa repo
    - **Problem:** Several OS defaults put the lab devices or the build at risk:
  - rfkill leaves the Wi-Fi/BT module enumerated on the hub shared with RTL-B and the HF+.
  - ModemManager and brltty probe CDC and FTDI ports, which disturbs the instruments and the Pico.
  - The Mesa version is unresolved (24.0.5 vs 25.2.8).
  - The PPA and the Radxa index drift (only 7.0.11-7 is listed now).
    - **Severity:** minor
    - **Fix:** - Wi-Fi/BT: rfkill plus USB authorized=0 in field profiles.
  - Purge brltty and mask ModemManager.
  - Name devices in udev by serial.
  - Hold Mesa 25.2.8 and libdrm 2.4.125.
  - Mirror third-party debs into aptly.
    - **Evidence:** compute.json; register #25; lab_ui_hf tech_stack.
    - **Fix cost:** $0
    - **Sources:**
      - https://docs.radxa.com/en/dragon/q6a/system-config/vulkan
  43.
    - **Area:** Lease enforcement and naming
    - **Components:**
      - engine units (user labrx)
      - rflab namespace
      - duplicate waterfall
    - **Problem:** All engines run as the same user with udev access to every SDR, so leases are not enforced between engines. 'rflab' names different things in two files. npu_training adds a second waterfall renderer.
    - **Severity:** minor
    - **Fix:** Transient DevicePolicy=closed plus DeviceAllow drop-ins per lease; one 'lab' namespace; the waterfall drawn only in Lab Shell.
    - **Evidence:** lab_ui_hf resource_arbitration; npu_training architecture.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/lab_ui_hf.json
  44.
    - **Area:** PPS fallback timestamps
    - **Components:**
      - Route A daemon
      - libgpiod 1.6.3
    - **Problem:** libgpiod 1.6.3 uses the v1 uAPI, which gives monotonic edge timestamps, so a fallback written on it would carry the wrong timescale.
    - **Severity:** minor
    - **Fix:** Decision C13: write the fallback on the GPIO v2 ioctl with EVENT_CLOCK_REALTIME, and never run it alongside pps-gpio.
    - **Evidence:** Register #28; gnss_imu own fix.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/gnss_imu.json
  45.
    - **Area:** LimeSuiteNG packaging (Lime only)
    - **Components:**
      - LimeSuiteNG 37cb183
      - la9310_limesdr DKMS
      - Amarisoft plugin
    - **Problem:** At the pinned commit the packaging builds limepcie-dkms but no la9310_limesdr DKMS package. The CMake default for BUILD_PLUGINS_AMARISOFT is ON.
    - **Severity:** minor
    - **Fix:** Only if the Lime is kept: a la9310-limesdr-dkms +lab package for 6.18.2-4, always building with -DBUILD_PLUGINS_AMARISOFT=OFF, and CI failing on any amarisoft .so.
    - **Evidence:** git show 37cb183 (interface lens).
    - **Fix cost:** $0
    - **Sources:**
      - https://github.com/myriadrf/LimeSuiteNG/tree/limesdr-micro-staging
  46.
    - **Area:** Known lines and the LNB path
    - **Components:**
      - GPSDO 10 MHz
      - SoC 76.8/19.2 MHz
      - V4L 28.8 MHz
      - 12 MHz hub/RP2040
      - Bullseye
      - IF pad
    - **Problem:** The P4 line list misses these exact harmonics in used windows:
  - 1420.000 MHz (H1), 1090.000 (ADS-B), 1540.000 (Inmarsat-C) and 740.000 (QO-100 IF), from the GPSDO;
  - 1420.8, 1574.4 and 403.2 MHz;
  - 1597.44 MHz (Lime);
  - 1560.0 MHz (12 MHz x130).
  
  On the LNB path:
  - The LNB stays powered while RTL-B listens to L-band.
  - A 10 dB pad leaves about -32 dBm at the V4L.
  - The 739.5 MHz IF is exposed to DVB-T and LTE B28 ingress.
    - **Severity:** minor
    - **Fix:** Add the lines to the spur mask. Keep the GPSDO off for H1, ADS-B and Inmarsat-C sessions. auto_rx ignores 400.000 and 403.2 MHz. LNB EN only when it is selected; a 15/20 dB pad; a double-shielded IF lead.
    - **Evidence:** rfcx/harm.py; q6a_sch.txt (76.8 MHz XO); register #106.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/rfcx/harm.py
  47.
    - **Area:** IMU puck near the Yagi feeds
    - **Components:**
      - RP2040-Zero 12 MHz
      - puck lead
    - **Problem:** The puck's 12 MHz crystal has harmonics at 144.000 and 432.000 MHz near the feeds, and a USB lead would run past the driven elements.
    - **Severity:** minor
    - **Fix:** Metal puck bonded to the shield, a ferrite at the puck, mounted 30 cm or more behind the elements, UART instead of USB, and an on/off A/B at 145.9 and 437 MHz.
    - **Evidence:** Register #82.
    - **Fix cost:** $0-5
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/gnss_imu.json
  48.
    - **Area:** AIS and broadcast on the HF+ VHF input
    - **Components:**
      - HF+ VHF mode
      - dipole kit
    - **Problem:** The 'VHF bus' has no antenna. The only dipole kit is set for LRPT, so LRPT and continuous AIS cannot run together.
    - **Severity:** minor
    - **Fix:** A second dipole kit ($17.95) on a dedicated VHF2/AIS port into relay K2.
    - **Evidence:** lab_ui_hf hf_receiver; register #116.
    - **Fix cost:** $17.95
    - **Sources:**
      - https://www.rtl-sdr.com/DIPOLE
  49.
    - **Area:** Sled LNA bias
    - **Components:**
      - sled 5 V buck
      - TPS2553
    - **Problem:** The sled makes its LNA bias with a switching buck and no post-regulator, so ripple goes straight up the coax to the LNA outputs.
    - **Severity:** minor
    - **Fix:** Buck to about 6 V, then LC, then a low-noise LDO at 4.5-5 V, then the TPS2553s, with a shield wall inside the sled box.
    - **Evidence:** radio_lab sled build parts.
    - **Fix cost:** About $5-10
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/radio_lab.json
  50.
    - **Area:** Lime-only coexistence and the T7
    - **Components:**
      - T7 USB 3
      - Lime spurs
      - RF bay
    - **Problem:** T7 SuperSpeed traffic is broadband near 2.4 GHz and raises the L1 floor. An internal T7 would sit in 25-35 W of heat. The Lime adds spurs at 737.28, 1597.44, 1689.6 and 1720.32 MHz.
    - **Severity:** minor
    - **Fix:** The T7 mounts outside on the bottom edge and never writes during L-band, S-band or GNSS sessions. Add the Lime lines to the mask and give the Lime build its own A/B run.
    - **Evidence:** Register #70/#73; storage.json (T7 rated 0-60 C).
    - **Fix cost:** $0-10
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/storage.json
  51.
    - **Area:** Storage retention, format and boot media
    - **Components:**
      - UFS
      - HF+ recorder
      - microSD
      - boot order
    - **Problem:** Storage gaps:
  - No combined partition or rolling-cap plan.
  - HF+ recorded as cf32 (6.1 MB/s) doubles the writes of its int16 stream.
  - small_antenna_stack's 'about 5 h on UFS' is a factor-2 error.
  - The firmware boot order is USB > SD > NVMe > UFS, so a data card carrying an ESP would boot instead of UFS.
    - **Severity:** minor
    - **Fix:** Decision C18 table:
  - HF+ recorded as ci16;
  - 30 GiB raw cap;
  - products kept by default;
  - data media without an ESP;
  - 20 cold boots with the card inserted.
    - **Evidence:** Register #74; storage.json boot order.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/storage.json
  52.
    - **Area:** Sun hood and lux sensor
    - **Components:**
      - VEML7700
      - hood
    - **Problem:** The lux sensor faces the same way as the screen, so it sits inside the hood and would dim the panel in full sun. The files also disagree on hood depth (15-25 mm vs 25-35 mm).
    - **Severity:** minor
    - **Fix:** Mount the sensor on the outer top face of the bezel. Hood: 30 mm, hinged.
    - **Evidence:** display_market sunlight_measures; display.json.
    - **Fix cost:** $1-3
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/display_market.json
  53.
    - **Area:** Lime mechanical order and refund timing
    - **Components:**
      - J21
      - R44SF
      - mid-plate
      - Crowd Supply order
    - **Problem:** Desoldering J21 cannot be undone and complicates an RMA during burn-in. The files do not order these steps. Crowd Supply refunds only before shipment (15 Dec).
    - **Severity:** minor
    - **Fix:** Order of work:
  1. Burn-in.
  2. Lime decision by 1 Dec.
  3. Delivery tests.
  4. Desolder J21 only if the Lime is kept.
  
  The mid-plate is cut once with the Lime holes.
    - **Evidence:** mechanical_thermal; final_world_sourcing (refund policy).
    - **Fix cost:** $0
    - **Sources:**
      - https://www.crowdsupply.com/lime-micro/limesdr-micro
  54.
    - **Area:** Field ergonomics and setup time
    - **Components:**
      - handheld
      - pass scheduler
      - foldable kit
    - **Problem:** A 1.35-1.6 kg device cannot be held one-handed through a pass. Setup times are not in the profiles, and the pass scheduler warns only at T-10 and T-2 min. Register #85's 'one operator cannot run LRPT and HRPT together' is too strict.
    - **Severity:** minor
    - **Fix:** - Strap plus a 1/4-20 tripod.
  - setup_min per profile, with a warning at T-(setup+5).
  - Allow a dual pass with the V-dipole fixed and the helicone hand-tracked.
    - **Evidence:** foldable build steps; lab_ui_hf design rules.
    - **Fix cost:** $10-25
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
  55.
    - **Area:** Memory policy
    - **Components:**
      - systemd OOM
      - mlock
      - swap
    - **Problem:** No file sets LimitMEMLOCK, an OOM order or a swap policy. systemd-oomd could kill the Shell's cgroup.
    - **Severity:** minor
    - **Fix:** - labrx: LimitMEMLOCK=infinity, OOMScoreAdjust -900.
  - labd and labpowerd: -1000; trainer 900; Expert GUIs 700; OpenWebRX+ 500; inferd 300.
  - zram 1 GiB, no disk swap.
  - oomd off, or limited to the trainer and Expert slices.
    - **Evidence:** npu_training budgets; storage verify.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/npu_training.json
  56.
    - **Area:** Price basis
    - **Components:**
      - T7
      - microSD
      - NVMe
      - UAH lines
    - **Problem:** Flash prices swung sharply in 2026: T7 $190-275, microSD about 3-4x its 2024 price. Several lines still use UAH or an FX rate of 1.16.
    - **Severity:** minor
    - **Fix:** Re-price at order time and treat flash as volatile. Use the world-sourcing FX rates (EUR 1.1241, GBP 1.3318).
    - **Evidence:** final_world_sourcing; resource lens.
    - **Fix cost:** $0
    - **Sources:**
      - https://www.pcworld.com/article/3158933/samsung-fast-t7-portable-ssd-finally-drops-in-price-190-was-285.html
  57.
    - **Area:** Stale values across files (errata)
    - **Components:**
      - radio_lab
      - lab_ui_hf
      - power.json
      - npu_training
      - small_antenna_stack
      - display_market
    - **Problem:** Superseded values are still in the files:
  - AUX '0.5 A PTC' and the Boni-Whip '10.0 V LDO' (radio_lab item 49, P20);
  - lab_ui_hf: 'a 5 V boost good for about 7 A' and the HF+ on Q6A VBUS;
  - power.json: 'a 7-24 V display from the pack' and i2c6/hwmon;
  - npu_training: 'INA228 on the J21 rail', librtlsdr 2.0.3 and Set B;
  - radio_lab integ: pinctrl-mcp23s08, the LNB on the sled, 'USB 3.1: T7 only';
  - P17: a BNO085 on I2C2;
  - ISS SSTV at 145.800 MHz;
  - the 8 GB downgrade;
  - 128.70 MHz;
  - '18.4 GB/h for two dongles'.
    - **Severity:** minor
    - **Fix:** STACK.md uses only the frozen tables, plus an errata block in summaries.md and minute-log.md.
    - **Evidence:** Register corrections_to_my_report; all four lenses.
    - **Fix cost:** $0
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/report_research.json
  58.
    - **Area:** Shared L-band parts
    - **Components:**
      - 4-turn helix
      - 20 cm disc
      - 18 cm helicone disc
    - **Problem:** The patch tier uses a 20 cm disc and the helicone an 18 cm disc, which means two discs and two gain sets for the same helix.
    - **Severity:** minor
    - **Fix:** One 18 cm, 1.5 mm Al disc for both tiers. It costs an estimated 0.3-0.5 dB (model; rerun NEC).
    - **Evidence:** foldable_antennas; register #118.
    - **Fix cost:** Saves about $5-10 and 100-150 g
    - **Sources:**
      - /tmp/claude-0/-home-user-lizbeth307/f89a86b4-fa51-5ce8-96da-e73d5f771cf3/scratchpad/final/foldable_antennas.json
- **Refuted issues:**
  1.
    - **Problem:** Interface lens: the HMI/supervisor RP2040 must sit on an always-on rail, because a LAB-5 V device is unpowered exactly when the boot pulse and hard cut are needed.
    - **Why refuted:** The case button turns the #2813 on through its on-only A-to-GND input (Pololu page, fetched today). That powers LAB5 and the Pico before the Q6A boots, so the Pico can make the 0.8-1.0 s J21 pin 3 pulse. Undervoltage cuts are done by a micropower supervisor with no firmware. An always-on MCU would add standby drain and a TX back-feed path.
  2.
    - **Problem:** Interface lens C4: a forced-PWM buck-boost of 5 A or more is preferred, and the D36V50F12 is allowed only with an EN hardware cut at 13.4 V or above.
    - **Why refuted:** No buck-boost from a reputable module vendor was found (sourcing lens). Above the 13.2 V cutoff a buck is enough. J21 accepts 4.5-16 V and the SY81012 2.7-16 V, so the dropout region below about 13.3 V is harmless. A 13.4 V cut throws away about 5 Wh (model).
  3.
    - **Problem:** Interface lens: keep direwolf on the device with an audited config (no PTT, no beacon or digipeat lines).
    - **Why refuted:** User rule line 44 forbids TX-capable software on the device. direwolf is a TX-capable TNC. APRS decoding moves to SDRangel's RX-only packet demodulator or OpenWebRX+.
  4.
    - **Problem:** Interface lens: use one root plus a 6 GB rescue rootfs on UFS, reject an A/B root, and put snapshots on microSD.
    - **Why refuted:** Self-test plus rollback is a design rule and must not depend on removable media, which the no-Lime build does not even buy yet (NAND prices). The A/B root costs about 22 GiB, about 35 min of dual-RTL raw IQ. Products are kept by default, so that cost is acceptable.
  5.
    - **Problem:** Interface lens: enable LAB 5 V only while the Q6A is on.
    - **Why refuted:** The Pico, which makes the boot pulse, runs on LAB5, so this would block cold boots. Every load that must be off with the Q6A off is switched by an MCP23017 that is itself powered from the Q6A's 3.3 V.
  6.
    - **Problem:** RF lens and interface lens: fan control by 24/25 kHz PWM.
    - **Why refuted:** It is not needed. 2-wire fans switched on and off in DC have no comb at all, and on/off at 60/50 C is enough for the copper-block thermal mass. The Pico fails safe to 100% when the heartbeat is lost.
  7.
    - **Problem:** Register conflict 6/#18: fan pin 'GPIO56 (PoE-HAT overlay) vs header pin 33'.
    - **Why refuted:** The schematic shows GPIO56 is FP_SPI_MISO, which is header pin 33, so there is no conflict. The pin stays spare, because fan control moves to the Pico.
  8.
    - **Problem:** Power lens C10: put the Flamingo+ FM on the SDR side of the injector, to keep bias current out of its 250 mA DC path.
    - **Why refuted:** That leaves the first LNA stage unfiltered against the FM band; intermodulation created there cannot be removed downstream. With the filter on the antenna side, bias enters at the LNA output and no DC crosses the filter anyway (RF lens physics, register #86).
  9.
    - **Problem:** Power and RF lenses: an LT3045 as the LNB (13.2 V) and Boni-Whip (12.5 V) regulator.
    - **Why refuted:** The topology (an LDO from the pack) is kept, but the part is not. The LT3045's 20 V absolute maximum sits below the SMBJ17A clamp voltage on node N during transients, for example when the BMS opens. The TPS7A4701 (36 V in, 1 A, verified on ti.com) takes that role. The LT3045 stays only on the 4.5 V LNA rail, which is fed from 5 V.
  10.
    - **Problem:** Sourcing lens C8: feed the LNB from an S18V20AHV SEPIC plus a second #2813 for true off.
    - **Why refuted:** On 4S the pack stays at 13.2 V or more over the whole usable window, so a switcher is not needed. An LDO adds no switching spurs near the 739.5 MHz IF or onto the LNB's LO supply. The LDO's EN gives a true 0 V. It is also cheaper.
  11.
    - **Problem:** Sourcing lens C6: make the IMU a USB-CDC puck on CH334F H2, because UART7 is unverified.
    - **Why refuted:** The puck relays through the Pico's own UART1. The Pico reaches the Q6A over UART7, or over its native USB on H1 if UART7 fails. Either way the IMU never needs its own USB port, and no USB edges run past the antenna elements.
  12.
    - **Problem:** Completeness lens: a 5 A pack fuse without the Lime and 7.5 A with it.
    - **Why refuted:** The no-Lime peak at the 13.2 V cutoff is 3.4 A (model), and a 5 A blade derated at 60 C carries about 3.3 A continuous. One 7.5 A value covers both builds with a single spare. The BMS (15 A) and the #2813 (6 A at 55 C) remain the upstream and downstream limits.
  13.
    - **Problem:** Register #99 and the completeness BOM: a Nooelec Ham Filter Bank (or an unnamed 430-440 MHz BPF) as the core 70 cm filter, ahead of the LNA.
    - **Why refuted:** Superseded. The Uputronics 440 MHz CubeSAT filtered preamp (LNA, then SAW; GBP 51.59, available, 5 V bias) is in stock and follows the UHF LNA-first rule. A BPF first costs 0.75-2.84 dB (model), and the filter bank's bias button can put 4.5 V on a hairpin.
  14.
    - **Problem:** Register #61/#67: a hardware cut at 13.4 V or above with the D36V50F12, and Linux poweroff at 13.6 V.
    - **Why refuted:** It wastes about 5 Wh (7%) for no benefit, because the regulator's dropout does not harm J21. Replaced by Linux at 13.2 V loaded, a supervisor at 12.8 V, and an EN backstop at about 12.0 V.
  15.
    - **Problem:** Power lens: set the D36V50F12 EN divider to 12.8 V as the hardware backstop.
    - **Why refuted:** With Pololu's EN thresholds (sleep below 1.2 V, wake above 1.35 V), a 12.8 V sleep point means a wake point of about 14.4 V. Pressing the button with the pack at 13.6-14.4 V at rest would then give no 12 V output. Corrected to a ratio of about 0.10 (sleep about 12.0 V, wake about 13.5 V), with the supervisor as the real 12.8 V cut.
  16.
    - **Problem:** Register #78 and display_market: 127.9 MHz as the primary field pixel clock.
    - **Why refuted:** Refined, not rejected. 127.9 MHz is clean (my scan), but it sits 0.14 MHz below the top of its clean window (123.62-128.04 MHz), and its line rate is 1.86 kHz from 60 kHz. 151.50 MHz is centred in 148.11-153.27 MHz at 60 Hz, so it goes first and 127.90 MHz second.
  17.
    - **Problem:** RF lens: 127.9 MHz has only a ±0.1% SSC-proof window (127.79-128.04 MHz).
    - **Why refuted:** Partly refuted. Against the 17 core windows, the clean range extends down to 123.62 MHz, so 127.9 MHz survives a 0.5% down-spread. It is fragile only against upward drift, or when Lime S-band windows are included (then 127.81-128.04 MHz).
  18.
    - **Problem:** RF lens: 151.5 MHz is clean in all used windows, S-band included.
    - **Why refuted:** Partly refuted. Its 15th harmonic is 2272.5 MHz, inside the 2200-2300 MHz allocation, though 13.5 MHz from Black Kite (2286/2288 MHz) and clear of PHASMA. That is acceptable for the narrowband carriers and matters only with the Lime.
  19.
    - **Problem:** RF lens: the LF Quiet profile must always switch the HDMI link off.
    - **Why refuted:** With the 151.50 MHz field mode the line rate is 68.86 kHz, at least 8.6 kHz from every LF carrier. HDMI-off becomes conditional on the narrow-RBW A/B instead of mandatory, which keeps the LF waterfall usable.
  20.
    - **Problem:** Resource lens: always fit a second CH334F behind H3.
    - **Why refuted:** With the IMU on the UART relay and the Pico on UART7, one hub has a free port in all four configurations. A second hub adds a 12 MHz clock (harmonics at 144/432 MHz) and 0.1-0.25 W. It is bought as a spare and fitted only if needed.
  21.
    - **Problem:** Resource lens C10b: one internal VHF/UHF front end with the 70 cm LNA inside the case, and the external leads always unpowered.
    - **Why refuted:** Partly refuted. At 137 MHz the lead loss costs 0.06-0.36 dB, so the internal SAWbird+ NOAA is adopted. At 437 MHz, 1-2 m of RG316 ahead of the LNA costs about 0.7-1 dB on CubeSat links with -5 to +5 dB of margin, so the Uputronics 440 goes at the antenna end. The DC-sense interlock makes bias up the lead safe.
  22.
    - **Problem:** Resource and completeness lenses: 1/4-20 thread tapped into the 2 mm plate (1.57 threads) as an open defect.
    - **Why refuted:** Already resolved. Register #71 chose a captured nut, and the completeness lens dismissed the tapped-plate alternative. It stays only as a 'never' rule plus a pull test at 3x the device weight.
  23.
    - **Problem:** All lenses: the Lime keep/cancel decision on 31 Jan 2027, or on delivery, is free.
    - **Why refuted:** Crowd Supply refunds in full only before shipment, which is 15 Dec 2026 (verified by the sourcing lens). After delivery the 30-day guarantee carries a restocking fee of at least $20, plus return shipping and non-recoverable import VAT. The decision moves to 1 Dec 2026.
  24.
    - **Problem:** Power lens: the cells have no world price.
    - **Why refuted:** Resolved by final_world_sourcing: P50B at $9.99 each at 18650 Battery Store (verified live), and RaceDayQuads $18.49 per 2. The NKON EUR 6.75 figure stays unverified.
  25.
    - **Problem:** Power lens: the AO3401A AUX switch exceeds its ±12 V gate limit (a new defect).
    - **Why refuted:** Already handled: register #62 specifies the 10k/10k gate clamp, which gives about -6 V. A ±20 V V_GS P-FET is still preferred in the BOM for margin, but this was not an open design error.
  26.
    - **Problem:** Power lens: the HF+ selector should be a latching relay with zero hold current.
    - **Why refuted:** Non-latching G6K-2F-RF relays fail safe to 50 ohm at power loss, which is what the terminated-floor and boot states need. Only one coil (about 0.12-0.15 W) is ever energised, about 1% of a pass budget.
  27.
    - **Problem:** Completeness and sourcing: the V4L tee may power LNAs of 80 mA or less (or 90 mA) such as the LNA V2, as part of the core chains.
    - **Why refuted:** Moot in core. Every core LNA is fed from the internal TPS2553 injector board and the V4L tees stay off (token gate). The tee rule, set at 90 mA or 50% of its rating, applies only to the spare V4L on LAB USB.
- **Power architecture and budget:** All figures are MODEL unless marked verified or measured.
  
  **Topology**
  
  4S1P Molicel P50B → Daly 4S 15 A BMS → 7.5 A blade fuse → INA228 15 mOhm shunt → node N → Pololu #2813 HP master switch → switched node SW. SW then feeds:
  - D36V50F12 → SYS12, which supplies J21, DISP12 and AUX12;
  - D36V28F5 → LAB5;
  - TPS7A4701 → LNB 13.2 V;
  - TPS7A4701 → BONI 12.5 V.
  
  Node N also carries the IP2368 BZ charger, the always-on (AON) LDO, the fused node-N service port and an SMBJ17A.
  
  **RAIL TABLE**
  
  | Rail | Source → regulator | Setpoint | Limit / protection | Switch (default) | Loads | I typ / max |
  |---|---|---|---|---|---|---|
  | PACK / N | 4S1P P50B + Daly BMS + 7.5 A blade + INA228 shunt | 13.2-16.4 V; 16.8 V only during the monthly balance with the master OFF | SMBJ17A | always | IP2368, AON, #2813, service port | 0.6 / 3.4 A without Lime; 4.6 A at Lime peak |
  | AON 3V3 | N → TPS709-class LDO (30 V, µA Iq; verify) | 3.3 V | - | always | INA228, UV supervisor (12.8 V trip / 13.6 V release) | about 0.7 mA |
  | SW | N → #2813 HP (6 A at 55 C; off-state below 0.2 µA, verified) | pack voltage | - | button on-only (A to GND), Pico OFF pulse, supervisor OFF | everything below | - |
  | SYS12 | SW → D36V50F12 (12 V ±4%; about 500 kHz at heavy load; power-save at light load) | 12.0 V; tracks the pack minus dropout below about 13.3 V | internal OCP/OTP, PG; EN backstop (ratio about 0.10: sleep about 12.0 V, wake about 13.5 V) | with SW | J21, DISP12, AUX12 | 1.0 / 2.9 A without Lime; about 4 A at Lime peak |
  | J21 | SYS12 → 4 A blade → pi-filter → SMBJ13A + 220 µF/25 V → keyed, latched header (Lime: 20 AWG twisted pair from the bottom pads) | 11.5-12.5 V | Q6A accepts 4.5-16 V (forum); SY81012 2.7-16 V | - | Q6A, plus everything on VCC_5V_PERI | 0.35-1.3 A; 2.5 A at Lime peak |
  | DISP12 | SYS12 → LC → 1.5 A eFuse | 12 V | eFuse | Pico; OFF when the Q6A is off | Wisecoco board (if it is 5 V only: a D36V28F5 #2 from SW) | 0.25 / 1.1 A |
  | AUX12 | SYS12 → P-FET rated ±20 V V_GS + 10k/10k gate divider + 2N7002 | 12 V | 0.75 A-hold PTC (about 0.55 A at 60 C) | MCP #1 GPA1; OFF; BENCH only, antenna paths terminated | sled, noise source, 28 V boost | 0 / 0.42 A |
  | LAB5 | SW → D36V28F5 (3.2 A) → 3 A fuse | 5.0 V | fuse | with SW | Pico, CH334F, IMU puck, both fans, HF+ (load switch + LC + Mix-31), LAB USB-A (TPS2553 0.75 A), LNA rail | 0.6 / 2.0 A; 2.3 A with RTL-A on the hub (Lime) |
  | LNA4V5 | LAB5 → LC → 2x LT3045 in parallel | 4.5 V | TPS2553 per channel at 300 mA nominal (240 mA or more at minimum), FAULT to MCP #3 | MCP #1, OFF | ch1 SAWbird+ NOAA, ch2 UHF Uputronics 440, ch3 L-band (SAWbird+ GOES / H1 / iO, or the L-band patch), ch4 WIDE (optional) | 0.17 / 0.6 A; labd budget: LAB port + LNA ≤ 1.5 A |
  | LNB13V2 | SW → LC → TPS7A4701 (3-36 V in, 1 A, 307 mV dropout at 1 A; ti.com verified) | 13.2 V ±0.2 V at the F port | PTC hold = 1.5-2x the measured current at 60 C (provisionally 0.45 A); internal limit and OTP; PG to MCP #3 | MCP #1 GPB0, OFF; only while the RTL-B selector is on the LNB port | Bullseye | 0.2-0.3 A (unpublished); dissipation 0.96 W at 16.4 V |
  | BONI12V5 | SW → LC → TPS7A4701 | 12.5 V ±0.25 V | PTC 0.2 A hold at 60 C (provisional); PG; DC-sense first | MCP #1 GPB1, OFF | Boni-Whip, through its bias tee inside the case | 0.05-0.1 A (unpublished) |
  | VCC_5V_PERI | inside the Q6A: SGM40666AS (4.5 A) → SY7120 | 5 V | about 17 W; WS4612 about 2.1 A per port pair | - | RTL-A (blue port), RTL-B, touch, GNSS, Wi-Fi, M.2 | 4-5 W without Lime; about 11.8 W Lime typical; Lime gate ≤ 14 W measured |
  
  **PROTECTION AGAINST REAL CURRENTS**
  - **Pack:** the 7.5 A fuse sees 3.4 A (no Lime) or 4.6 A (Lime) at the 13.2 V cutoff, or 3 A of charging; current never adds across charge and discharge. One value for both builds. A 5 A fuse is rejected (about 3.3 A continuous at 60 C).
  - **Master switch:** #2813 rated 6 A at 55 C, against 4.6 A or less.
  - **J21 branch:** 4 A fuse against 1.3 A (2.5 A Lime).
  - **LAB5:** 3 A fuse against 2.0-2.3 A. The old 2 A was too small.
  - **LAB port:** 0.75 A.
  - **SAWbird+ channels:** TPS2553 at 300 mA nominal against 170-180 mA. A 250 mA setting is too tight, and PTCs are rejected.
  - **AUX:** PTC 0.75 A hold against 0.42 A.
  - **Display eFuse:** 1.5 A against 1.1 A.
  - **J21 TVS:** SMBJ13A (VRWM 13 V, above the 12.48 V maximum output; breakdown 14.4-15.9 V, below the Q6A's 16 V capacitors). The SMBJ14A is rejected because its breakdown can reach 17.2 V.
  - **Node N TVS:** SMBJ17A (VRWM 17 V, above 16.8 V).
  
  **CUTOFF TABLE (labpowerd + Pico + hardware)**
  - **Economy:** SoC 20%, or V_N below 14.0 V loaded for 30 s → dim to 30%, loggers off, Lime parked.
  - **NPU:** no training below 25% (the training gate also needs the SoC below 75 C); NPU off below 15%.
  - **Shutdown:** SoC 3%, or V_N ≤ 13.2 V loaded for 10 s → 30 s banner, finalise SigMF, turn off bias, LNB, Boni and AUX, then poweroff (never halt; halt still draws 1.9-2.5 W). The Pico opens the #2813 3 s after the Q6A's 3.3 V drops.
  - **Pico failsafe:** pack divider ≤ 12.9 V for 5 s with no heartbeat → #2813 OFF.
  - **Hardware supervisor (always-on rail):** trips at 12.8 V and holds OFF; releases at 13.6 V at rest.
  - **EN backstop:** about 12.0 V.
  - **BMS:** 2.5-2.8 V/cell.
  - **Restart:** button only, with the pack at 13.6 V or more at rest.
  - **Noise-source NF:** blocked below V_N 13.6 V.
  - **Temperatures:** charging only with the cell NTC between 0 and 45 C; shutdown above 60 C at the cell.
  - **Gauge resync:** 16.35 V with under 0.1 A, or 16.3 V or more at rest at boot.
  
  **CHARGING**
  - **Board settings:** IP2368 BZ charge-only; RVSET 5.1k (4.10 V/cell); RISET 15k (3 A, about 49-52 W drawn); 10k B3380 NTC.
  - **Source:** a PD source of 60 W or more, each one qualified with the FNB58. 45 W sources must use input-power mode (bench-verify RISET).
  - **Times (model):** about 1.4 h CC plus 0.3-0.5 h CV from idle; about 2.5 h while running mode B.
  - **Restrictions:** no charging in HF/LF Quiet (the charger switches at 250 kHz). The Pinecil runs from the PD bank.
  - **Balance:** the ISDT 608PD charges at 4.20 V monthly through the node-N service port, with the master switch OFF.
  
  **PER-MODE PACK POWER AND RUNTIME**
  
  Model inputs: usable 58 Wh warm and new, 50 Wh at 0 C or about 300 cycles; Q6A 2.9 / 9.3 / 10.1 W (measured, Geerling); V4L 1.3 W (datasheet); SAWbird+ 170-180 mA (vendor); display 3 / 6 / 13 W at 25 / 50 / 100%. Efficiencies: D36V50F12 92%, D36V28F5 88%, Q6A internal 85%, LDO = Vout/Vin.
  
  | Mode | W at pack | Warm | Cold |
  |---|---|---|---|
  | A idle / menu, display 25% | 8.4 | 6.9 h | 5.9 h |
  | B LEO pass (LRPT or ISS): 1 V4L + LNA, NPU, display 50% | 17.6 | 3.3 h | 2.8 h |
  | C QO-100 NB: RTL-B + LNB | 19.2 | 3.0 h | 2.6 h |
  | D survey: 2 V4L + HF+ + NPU | 22.9 | 2.5 h | 2.2 h |
  | E LF/HF Quiet: HF+ + Boni-Whip, display off | 8.2 | 7.1 h | 6.1 h |
  | E2 HF with display 25% | 12.0 | 4.8 h | 4.2 h |
  | F bench on pack: V4L + AUX sled + noise source + 1 LAB instrument | 18.9 | 3.1 h | 2.6 h |
  | G peak, no Lime: display 100%, all rails, LAB port 0.75 A, NPU + trainer | 45.0 | 1.3 h | 1.1 h |
  | H Lime typical: 56 Msps + T7 + RTL-B | 30.8 | 1.9 h | 1.6 h |
  | I Lime peak | 61.1 | 0.9 h | 0.8 h |
  | OFF: INA228 + IP2368 standby + BMS + supervisor | about 0.013-0.014 | about 170-185 days | - |
  
  The files' figures of 3.7-5.3 h (no Lime) and 2.2-2.6 h (Lime) are superseded. Measure every mode with the INA228 at first power-up and replace the model rows.
  
  Power subsystem cost: about $250-345, including the spare D36V50F12 and #2813 (BOM rows).
- **Port bus and pin allocation:** **USB MAP** (schematic v1.21; Lime-agnostic)
  
  | Port | VBUS source | No Lime | Lime kept |
  |---|---|---|---|
  | J5 bottom: blue USB 3.1 (USB0, HS+SS; also the EDL port) | U35 WS4612 (about 2.1 A, shared with J5 top) | RTL-A, on a 15 cm shielded extension with a ferrite. It runs at USB 2 HS only, so there is no SuperSpeed noise. | T7 on its own VBUS, mounted outside on the bottom edge. VBUS is split from LAB5 only if the 14 W gate fails. |
  | J5 top = FE1.1s P1 | U35 | RTL-B (extension + ferrite) | RTL-B |
  | J2a = FE1.1s P2 | U33 | Touch USB-HID from the display board; board VBUS not linked | same |
  | J2b = FE1.1s P3 | D+/D-/GND only; Q6A VBUS left unconnected | CH334F #1, its 5V pin fed from LAB5 | same |
  | CH334F H1 | LAB5 | spare (Pico native USB only if UART7 fails) | same |
  | CH334F H2 | LAB5 | spare | RTL-A |
  | CH334F H3 | TPS2553 0.75 A, MCP #1 GPA0 | LAB USB-A: one field device (Pro Stick Plus, spare V4L or an instrument); on the bench, a bank-powered MTT hub | same |
  | CH334F H4 | load switch (MCP #1 GPA4) + LC + Mix-31 | Airspy HF+ in its can | same |
  | FE1.1s P4 | WIFI_PWR_EN | FCU760K Wi-Fi/BT: rfkill plus USB authorized=0 in every field and QUIET profile | same |
  | CH334F #2 | bought as a spare | Fitted behind H1 only if the Lime is kept AND UART7 fails, or if a 5th internal device appears | - |
  
  - **Off USB:** GNSS on UART6; the Pico on UART7; the IMU puck on a UART to the Pico; the INA228 on I2C0; the expanders on I2C2.
  - **Bandwidth (MB/s):** the FE1.1s tree carries RTL-B 5.12 + HF+ 3.07 + one LAB-port device ≤5.12 + touch <0.1, i.e. ≤13.3. Aggregate cap 25 (practical 35-40). The blue port carries RTL-A 5.12, or the T7 at 224 against 395 measured.
  - **Hub depth to a bench instrument:** 3 hubs, against a limit of 5.
  
  **40-PIN HEADER** (level translator in brackets)
  
  | Pin | Signal | Use | Owner |
  |---|---|---|---|
  | 7 | GPIO96 (UM3304) | PPS in, wire ≤20 cm | kernel pps-gpio |
  | 8/10 | debug UART (UM3204H) | console, reserved | - |
  | 13/15 | I2C0 (CJ3134K) | INA228 at 0x40, breakout pull-ups removed | labpowerd |
  | 16/18 | UART6 (UM3204H) | LC76G (/dev/ttyHS1 → /dev/gnss0) | gpsd |
  | 27/28 | I2C2 (UM3204H), 100 kHz | MCP23017 #1 0x20 and #3 0x22; TCA9517 A side to the LAB BUS (sled MCP23017 #2 0x21, ADS1115 0x48, RP2040 counter 0x30 only with the Lime). No pull-ups below 10k on the header side; 4.7k on the sled side. | labd |
  | 32/29 | UART7 TX/RX (UM3304) | Pico UART0, 2-wire, ≤20 cm or via a 74LVC2T45 | labinput |
  | 3 | GPIO24 (UM3204H) | INA228 ALERT (open drain) | labpowerd |
  | 5 | GPIO25 (UM3204H) | MCP #3 INTA/B, mirrored, open drain | labd |
  | 12/35/38 | UM3304 | Pico SWCLK / SWDIO / RUN, service only | OpenOCD |
  | 40 | UM3304 | safe-boot flag from the Pico | early unit |
  | 33 | GPIO56 = FP_SPI_MISO (UM3304) | spare (fan fallback only via a 74LVC1G17 + 2N7002) | - |
  | 1/17, 2/4 | 3.3 V / 5 V | 3.3 V powers MCP #1/#3 and the Pico's Q6A-on sense | - |
  
  No safety enable sits on a header GPIO. Verify with debugfs pinmux-pins that every pin has a single owner: check UART6 against GPIO24/25, and that the UART7 overlay is on the held image.
  
  **EXPANDERS** (labd; powered from the Q6A's 3.3 V, so the Q6A off means every enable is off; 100k pull-downs)
  - **MCP23017 #1 (0x20), outputs:**
    - GPA0 LAB port EN; GPA1 AUX12 EN (BENCH only);
    - GPA2/GPA3 RTL-A / RTL-B VBUS cuts; GPA4 HF+ VBUS;
    - GPA5/6/7 LNA ch1 (VHF-137), ch2 (UHF), ch3 (L-band);
    - GPB0 LNB EN; GPB1 Boni EN;
    - GPB2 HF+ relay K1 (HF); GPB3 HF+ relay K2 (VHF2);
    - GPB4/5 RTL-A selector V1/V2; GPB6/7 RTL-B selector V1/V2 (00 = 50 ohm on both).
  - **MCP23017 #3 (0x22), inputs:** FAULT for the LAB port and ch1-ch4; LNB PG; Boni PG; DC-sense on UHF, L-band and HF; AUX PTC sense; sled present.
  - **MCP23017 #3, outputs:** GPA7 LNA ch4 EN (WIDE, optional) and GPB7 T7 VBUS (Lime only). GPA7 and GPB7 are output-only on current silicon.
  - **Sled MCP23017 #2 (0x21):** HMC7992 V1-V3; PE4302 D0-D5; NOISE EN (BENCH); LNA EN.
  
  **PICO** (RP2040, 26 GPIO; powered from LAB5 via VSYS)
  - **Links:** GP0/1 UART0 to and from Q6A UART7; GP8/9 UART1 to and from the IMU puck (115200, framed, CRC).
  - **HMI:** GP2/3 encoder 1 A/B; GP6/7 encoder 2 A/B; GP4/5 I2C0 to the VEML7700 (0x10) and a PCA9555 (0x20) carrying the 6 keys and 2 encoder pushes; GP10 key INT.
  - **Power and boot:** GP11 power-button sense (via BAT54); GP12 J21 pin 3, open drain via 2N7002; GP13 #2813 OFF pulse; GP14 Q6A-on sense (header 3.3 V via 10k); GP15 safe-boot to pin 40.
  - **Display and thermal:** GP16 DISP12 eFuse EN; GP17 backlight dimming (PWM through an RC to analog; direct 24.0 kHz only if the board needs PWM); GP18 Q6A fan FET; GP19 blower FET.
  - **Other:** GP20 piezo; GP21 status LED; GP22 spare; GP26-28 ADC (panel NTC, pack divider 1:6, case NTC); GP24 internal VBUS sense for the H1 fallback.
  - **TX pins** are tri-stated while the Q6A's 3.3 V is low.
  - **Power button** (sealed 12-16 mm momentary, to GND): BAT54 diodes to the #2813 A input (on-only), to J21 pin 3 (the PMIC key, wired-OR with GP12) and to GP11. The supervisor output and GP13 are diode-ORed onto the #2813 OFF input.
  
  **OTHER BUSES**
  - **LAB BUS** (6-pin locking): I2C-B, AUX 12 V, GND.
  - **IMU puck:** GX12 4-pin socket (3.3/5 V, TX, RX, GND, with TVS) and 1.5-2 m shielded 4-core lead.
  - **I2C address map:** no collisions. 0x40 on I2C0. 0x20, 0x21, 0x22, 0x48 and 0x30 on I2C2. 0x10 and 0x20 on the Pico's own bus.
- **Rf chain and switching:** **CASE RF PORTS** (top edge, 20 mm pitch; 7 ports without the Lime = 140 mm)
  - **P1 VHF-137 SMA** (no DC): Flamingo+ FM #1, then SAWbird+ NOAA (inside, in the RF bay), then injector ch1 (TPS2553 300 mA; bias enters on the SAWbird's output), then a DC block, then RTL-A selector throw T1.
  - **P2 UHF SMA** (4.5 V bias out on ch2, after DC-sense): injector ch2, then RTL-A T2. The Uputronics 440 MHz CubeSAT filtered preamp (LNA, then a 30 MHz SAW) is always the first part after the antenna. In the patch tier it screws onto P2; in the foldable tier it sits at the Yagi's 70 cm feed.
  - **P3 L-BAND SMA** (4.5 V bias out on ch3, after DC-sense): injector ch3, then RTL-B T1. Either an LNA at the feed (SAWbird+ GOES, H1 or iO) or the RTL-SDR Blog active L-band patch (20 mA).
  - **P4 LNB F** (13.2 V): LNB injector (choke rated 1 A or more, DC block), then a 15 dB pad (20 dB if the measured LNB gain is above 60 dB), then RTL-B T2. LNB EN only while the RTL-B selector is on T2.
  - **P5 HF SMA plus ground/counterpoise post** (DC-capable; 12.5 V goes up the coax only in the Boni profile): Boni-Whip bias tee (inside, by the HF+ can), then HF+ relay K1. The two-stage CM choke sits on the coax just outside P5.
  - **P6 VHF2/AIS SMA** (no DC): HF+ relay K2. The HF+ covers 64-260 MHz (AIS, FM-RDS, DAB).
  - **P7 GNSS SMA** (3.3 V from the LC76G): to the LC76G.
  - **Optional P8 WIDE/2 m SMA:** Flamingo+ #2, then the bench-spare LNA V2, then ch4, then RTL-A T3.
  - **Lime only:** LIME RX1, LIME RX2 and REF IN SMA. A third HMC7992 routes the ch3 L-band chain to RTL-B or to Lime RX1 through a 10 dB pad. S-band: a 7-turn helix in the cone, an S-band LNA (still unnamed) and a cf2235-kt30 cavity, on RX2.
  
  **SELECTORS**
  - RTL-A and RTL-B each use a generic HMC7992 SP4T board placed behind the injectors. The throws are DC-free; T4 is 50 ohm and is also the 00 power-up default. Isolation must measure 30 dB or more, conducted.
  - The HF+ uses two Omron G6K-2F-RF relays in series-shunt. De-energised, the HF+ sits on 50 ohm and both antenna ports are terminated. Acceptance: 35 dB or more of isolation at 162-260 MHz, and 0.3 dB or less of loss from 10 kHz to 260 MHz.
  
  **BIAS AND INTERLOCKS** (labd)
  - **V4L tees** stay off in core: librtlsdr token gate, EEPROM bias off. The spare V4L's tee may feed LNAs of 90 mA or less, and only with the token.
  - **SAWbird+ feeds:** every SAWbird+ runs through a TPS2553 at 300 mA nominal, on an injector rated 0.5 A or more. The TCBT-2R5G+ (200 mA) is used only on channels drawing 150 mA or less.
  - **DC protection:** DC-sense runs before every bias enable. Bias is locked off on DC-short profiles: the 9:1 balun, and the hairpin Yagi feeds when no LNA is fitted. No micro-USB power at any feed.
  - **LNB:** EN is interlocked with the RTL-B selector.
  - **Signal sources:** the GPSDO and the noise source run only in BENCH, with every selector on 50 ohm and conducted at -40 dBm or less.
  
  **FRONT-END ORDER RULE**
  - **VHF (137/145 MHz):** filter first, then LNA. The sky is 1000-3000 K, so the Flamingo+ costs only 0.06-0.45 dB.
  - **UHF and L-band:** LNA first, at the antenna, then the filter. At 437 MHz a 1-2 dB BPF first costs 0.75-2.84 dB, and 1-2 m of RG316 ahead of the LNA costs about 0.7-1 dB.
  - **137 MHz:** the LNA sits inside the case in both tiers; 1-1.5 m of RG316 ahead of it costs 0.06-0.36 dB (model).
  
  **PER-TARGET CHAINS** (no Lime; patch tier = always carried)
  
  | Target | Patch tier | Foldable tier | Port → SDR | Notes |
  |---|---|---|---|---|
  | Meteor LRPT 137.1/137.9 MHz | Dipole kit #1 as a V (53.4 cm arms, 120°, N-S, 1-1.1 m), on 1-1.5 m RG316 | Same; optional re-marked Yagi tapes (about 7.7 dBi) | P1 → RTL-A T1, about 1 Msps, gain 10-25 dB | Recorded, then decoded by SatDump |
  | ISS SSTV 437.550, APRS 437.825, FM 437.800; CubeSats 435-438 MHz | 17 cm whip, or A-V85/SRH-701, on the Uputronics 440 on P2, tilted broadside | Crossed Yagi 70 cm (ultra-compact) with the Uputronics 440 at the feed | P2 → RTL-A T2 | slowrx / OpenWebRX+ SSTV; APRS through the SDRangel RX-only packet demodulator (verify) |
  | 2 m 145.8-146 MHz (optional) | A-V85/SRH-701 | Yagi 2 m half (hairpin: no bias) | P8 → RTL-A T3 | Filter first |
  | Meteor HRPT 1700 MHz | 4-turn helix on the shared 18 cm disc, SAWbird+ GOES at the feed | Petal helicone with the same SAWbird+ GOES | P3 → RTL-B T1, 2.4-2.56 Msps | pcie0 off, LNB off. Helix marginal above 25-30° (model); helicone +8.9 to +9.4 dB (model) |
  | Inmarsat-C EGC SafetyNET | RTL-SDR Blog L-band patch | Helicone + SAWbird+ iO (held until the egc-gate passes) | P3 → RTL-B T1 | Header-level discard; LES channels never tuned |
  | H1 1420.4 MHz (extended) | Helix + SAWbird+ H1 | Helicone + H1 | P3 → RTL-B T1 | GPSDO off |
  | GNSS L1 / regional SBAS | Waveshare L1+L5 active antenna | Same | P7 → LC76G. Optional GNSS-SDR: L-band patch → RTL-B | PPS on pin 7 |
  | QO-100 NB (region-held) | Bare Bullseye + 11 cm cone | 6-gore horn on a tripod | P4 → RTL-B T2 | CW beacon with the bare LNB; PSK with the cone or horn; DATV and typical SSB not feasible without a dish |
  | ADS-B 1090 MHz | Pro Stick Plus (extended), or spare V4L with 6.5 cm arms, on LAB USB | Same | H3 | readsb lease; tracks with dbFlags&1 suppressed |
  | AIS 162 MHz | Dipole kit #2, vertical, 44 cm arms | Same | P6 → HF+ K2 | AIS-catcher; type 35 suppressed |
  | FM-RDS / DAB | Dipole kit #2 | Same | P6 → HF+ (or the spare V4L) | redsea, welle-cli |
  | Radiosondes 400-406 MHz | Spare V4L with 17.7 cm arms on LAB USB (or P8 WIDE) | Same | H3 | auto_rx 400.0-405.9 MHz; 400.000 and 403.2 MHz ignored |
  | HF 0.15-31 MHz | - | 7-15 m wire + 9:1 balun 5-10 m away, counterpoise | P5 → HF+ K1 | Bias locked off (DC short) |
  | LF time signals (DCF77, MSF/WWVB, JJY, TDF), NAVTEX 490/518 kHz | - | Boni-Whip on a mast of 2 m or more, ground stake | P5 → HF+ K1, 12.5 V | LF Quiet profile; SID amplitude-only on civil LF carriers |
  | Spectrum survey | any port | any port | HF+ 0.5 kHz-31 MHz and 64-260 MHz; V4L 24-1766 MHz | Occupancy only; 3-30 kHz and 225-400 MHz stored as 'no data' |
  | Calibration | 50 ohm throws on every selector | Same | - | tinySA ≤ -40 dBm, conducted; noise source BENCH only |
  
  **SIMULTANEOUS USE:** RTL-A (VHF/UHF), RTL-B (L-band/LNB), the HF+ (HF/LF or AIS) and one LAB-port receiver can run together. A single operator may run the V-dipole fixed on its stand on RTL-A while hand-tracking the helicone on RTL-B.
- **Thermal plan:** All figures are MODEL (case 210x135x52 mm, two fan paths about 5.4 m3/h, h about 10 W/m2K, 35 C ambient), to be replaced by the noon-soak measurements.
  
  **INTERNAL HEAT AND AIR TEMPERATURE RISE**
  
  | Mode | Internal heat | Mean air rise, shade / sun | Outlet rise | Note |
  |---|---|---|---|---|
  | B LEO pass | 17 W | +6 / +9 K | +10-14 K | - |
  | D survey | 22 W | +8 / +10.5 K | +13-17 K | - |
  | G peak, no Lime | 36 W | +13 / +16 K | +21-25 K | SoC throttles |
  | H Lime typical | 30 W | +11 / +13 K | +17-21 K | - |
  | I Lime peak | 53 W | +19 / +22 K | +31-35 K | not sustainable |
  
  About half of the 13.5-17 W solar load on the face is assumed to reach the internal air. Charging adds about 2.6 W of IP2368 loss inside the case.
  
  **AIRFLOW**
  - **Path 1:** rear intake, stepped copper block (32x31 mm keep-in) with a 40 mm 5 V fan, rear-top exhaust.
  - **Path 2:** bottom intake, the 4-6 mm channel behind the display with a 5 V blower, the mid-plate fins, side exhaust.
  - Display air never pre-heats the Q6A fins.
  - **Fan control:** both fans switch on and off in DC from the Pico. The Q6A fan is on at a SoC of 60 C and off at 50 C (commanded by labd). The blower follows the panel NTC (on at 45 C, off at 40 C). Both go to 100% if the heartbeat is lost.
  - Intakes have stainless mesh and hydrophobic foam, with ePTFE vents (IPX4/IP54).
  
  **PACK**
  - A separate insulated compartment along the bottom-left intake side, so the cells see near-ambient air.
  - Behind 3 mm closed-cell foam, reflective film and a 1 mm FR-4 or mica barrier, with a vent path to outside.
  - The NTC sits on the middle cell. The IP2368 window is 0-45 C; labpowerd shuts down above 60 C at the cell.
  - Without this, cells downstream of the board would reach 45-55 C at 35 C ambient, block charging and age faster.
  
  **CHARGER:** the IP2368 is pad-mounted to the case wall at the bottom edge, at least 10 mm from the cells, with a 70 C KSD9700 in its input. No charging in HF/LF Quiet.
  
  **REGULATORS:** the D36V50F12 and both TPS7A4701 are bonded to the mid-plate. The LNB LDO dissipates 0.96 W or less at θJA 30.5 C/W, about +29 K (about 79 C junction at 50 C internal). The D36V28F5 sits near the bottom intake. Sealed-case test: 3.5 A for 60 min at 14.0 V and 16.4 V input, output within 4%, no thermal cut.
  
  **DISPLAY**
  - Bonded panel, light bezel, 30 mm hinged hood, IR film.
  - NTC derating: above 60 C → 50%; above 68 C → 20%.
  - Panel temperature (model, backlight 11 / 5.5 / 2.8 W at 100 / 50 / 25%):
    - 25 C ambient, full sun, 100%: about 61 C.
    - 35 C ambient, full sun, 100%: about 71 C, above the 70 C rating.
    - 35 C ambient, full sun, 50%: about 62 C.
    - 35 C ambient, 50% with the hood: about 53 C.
  - Physics over the wish: sustained brightness in hot noon sun is about 1000 nits; 2000 nits is a burst.
  
  **SoC**
  - Tj maximum 95 C; throttling at about 90-91 C. Expected about 85 C typical and 90-100 C at G-mode peaks in 35 C sun.
  - Shedding ladder at 80 and 85 C.
  - Training only with the SoC below 75 C and the battery above 25%, or on a charger.
  
  **Other parts**
  - **UFS:** padded to a case boss (about 60 C).
  - **T7 (Lime only):** outside on the bottom edge (rated 0-60 C).
  - **Lime (if kept):** a 10 W conduction path through the pedestal and a pad of 6 W/mK or more to the plate.
  
  **COLD:** no charging below 0 C. UFS and T7 are rated from 0 C. Plan on 50 Wh usable.
  
  **ACCEPTANCE:** a 45-min noon soak with the hood fitted, in modes B, D and G, with internal air, cells, SoC, panel and charger temperatures all logged:
  - frame 60 C or less;
  - glass 65 C or less;
  - cells 45 C or less;
  - no thermal shutdown.
- **Rf noise plan:** **1. A/B METHOD** (one matrix replaces P4, the display A/B, the HF A/B and the small-stack tests)
  - **Per used window:** 60 s of IQ at 2.4 Msps, a 2^20-point FFT (2.3 Hz bins) with Welch averaging.
  - **HF+:** 1 Hz RBW at 40, 60, 77.5, 162, 490, 518 and 4209.5 kHz, and at 1, 7 and 14 MHz.
  - **GNSS:** mean C/N0 of the 8 strongest satellites from GSV, plus GNSS-SDR on a V4L.
  - **Why:** at NF 5 dB the floor is -119 dBm in a 100 kHz rtl_power bin against -165 dBm in a 2.3 Hz bin (model). A line that costs about 1 dB on CW, 1200 sym/s or H1 targets is invisible in the old bins.
  - **States (each toggled alone):**
    - HDMI link on/off; backlight 0/50/100% and the dimming method; field mode 151.50 vs 127.90 MHz;
    - pcie0 on/off; Wi-Fi/BT de-authorised; fans on/off;
    - LAB5 loads; the CH334F; the charger on/off and each PD source;
    - SYS12 and LAB5 electronic-load steps from 0.3 to 3 A;
    - LNB on/off with its IF terminated at the LNB; the LNA rails; the Boni rail;
    - the IMU puck; a V4L streaming on the shared hub; the T7 (Lime build).
  - **Conditions:** terminated at the SDR, then at the LNA input, then on the antenna; lid closed after a 30-min warm soak.
  - **Pass:** no line 3 dB or more above the local floor inside a used window; broadband rise of 0.5 dB or less inside the windows; GNSS change of 1 dB-Hz or less.
  - **Output:** a versioned spur-mask file (frequency, width, source) read by labrx, the SatDump wrapper, auto_rx, the NPU labeller and the UI.
  - **Effort:** about 4-5 h per full run, 30 min for the regression subset.
  
  **2. KNOWN LINES** (exact harmonics in used windows; amplitude unknown)
  
  | MHz | Source | Target |
  |---|---|---|
  | 1700.000 | 25 MHz x68 (NIC, LNB reference), 100 MHz x17 (pcie0/Lime), 10 MHz x170 (GPSDO) | Meteor HRPT |
  | 1699.2 | V4L 28.8 MHz x59 | Meteor HRPT |
  | 1575.000 | 25 MHz x63 | L1 |
  | 1574.4 | 19.2 MHz x82 | E1 lower lobe |
  | 1600.0 / 1597.44 | 100 MHz x16, 25 MHz x64 / Lime x52 | GLONASS G1 |
  | 1560.0 | 12 MHz x130 | BDS B1I |
  | 1544.4 | 128.70 MHz x12 (pixel-clock mode, banned) | Inmarsat-C |
  | 1540.0 | GPSDO x154 | Inmarsat-C |
  | 1420.000 / 1420.8 | GPSDO x142 / 19.2 MHz x74 | H1 |
  | 1090.000 | GPSDO x109 | ADS-B |
  | 1689.6 | 76.8 MHz x22, Lime x55 | FY-2H / Elektro window |
  | 740.000 / 737.28 | GPSDO x74 / Lime x24 | QO-100 IF |
  | 403.2 / 400.000 | 28.8 MHz x14, 19.2 MHz x21 / 25 MHz x16, 100 MHz x4, 10 MHz x40 | radiosondes |
  | 144.000 / 432.000 / 1704.0 | 12 MHz (hub, RP2040) | 2 m / 70 cm / Metop |
  
  **3. BOARD-LEVEL CONTROLS**
  - The field DT overlay disables pcie0; Ethernet runs only on home and bench boots. If the NIC crystal still radiates, copper-tape the PHY to the plate.
  - Wi-Fi/BT: rfkill plus USB authorized=0 in every field and QUIET profile. The self-test confirms the module is absent from lsusb and that 2.4 GHz is silent.
  - The GPSDO stays off and disconnected for H1, ADS-B and Inmarsat-C sessions.
  - In field mode only three continuous streams run on the FE1.1s.
  
  **4. DISPLAY**
  - Field EDID: DTD1 at 151.50 MHz (2200x1148, 59.99 Hz). My scan puts it in a clean window of 148.11-153.27 MHz; its line rate of 68.86 kHz is at least 8.6 kHz from every LF carrier. DTD2 at 127.90 MHz (51.68 Hz; clean 123.62-128.04 MHz).
  - Strip the CEA VICs. 148.5 MHz is for bring-up only. 128.70 MHz is banned.
  - Verify the delivered clock with modetest and debugfs, then near-field E-probe the predicted harmonic line.
  - Shielded 10-15 cm HDMI lead with Mix-31/61 ferrites; LC-filtered DISP12; backlight dimmed in analog/DC (24.0 kHz only if PWM is unavoidable).
  
  **5. LF/MF COMBS**
  - Fans run on DC, with no PWM.
  - The D36V50F12 (about 500 kHz, with a power-save mode at light load) is gated by the A/B. If it fails, replace it with a fixed-frequency forced-PWM synchronous buck whose frequency comes from a harmonic scan.
  - The IP2368's 250 kHz has its 2nd harmonic 10 kHz from NAVTEX 490 kHz, so there is no charging in HF/LF Quiet.
  - USB frame lines at 1 and 8 kHz: only the HF+ streams in LF Quiet.
  - SID logs subtract a terminated-input baseline taken in the same profile.
  
  **6. RAILS:** the LNB, Boni-Whip and LNA rails are all LDO-fed, so there is no switcher near the 739.5 MHz IF or the HF feed. Every rail leaving the power board has an LC pi-filter. The HF+ VBUS gets LC plus Mix-31.
  
  **7. HF**
  - A two-stage CM choke at the HF bulkhead: 77-mix for LF/MF and 31-mix for HF. Targets are 1 kOhm or more at 60 kHz and 2-5 kOhm at 1-30 MHz, measured conducted on the LiteVNA.
  - The bulkhead is bonded to the mid-plate, with a ground stake or counterpoise at the antenna and the feed point 5-10 m away.
  - The HF+ sits in a tinplate can at the far end from the bucks.
  
  **8. LAYOUT**
  - An RF bay of soldered copper-clad FR4 along the top edge, with seams of 7 mm or less.
  - The V4Ls sit inside the bay on 15 cm shielded extensions with ferrites, away from the HDMI/J5 edge.
  - The GNSS antenna is external on a 1-3 m lead. A lid patch is allowed only if it passes the C/N0 on/off test.
  
  **9. LNB PATH**
  - EN only while it is selected; injection on the antenna side of the DC-free selector.
  - 15/20 dB pad. Padding costs no SNR because LNB noise dominates, and it keeps the V4L below its -20 to -40 dBm desense range.
  - Double-shielded 75 ohm lead and tight F connectors. Check DVB-T and LTE B28 ingress once the region is known.
  
  **10. IMU PUCK:** metal shell bonded to the cable shield, a 31/43-mix ferrite at the puck, mounted 30 cm or more behind the driven elements, connected over UART rather than USB. A/B at 145.9 and 437 MHz.
  
  **11. LIME (if kept)**
  - The T7 never writes during L-band, S-band or GNSS sessions; labrx decimates those to 1 Msps or less and writes them to UFS.
  - Shielded riser; 10-12 dB pads after the SAWbirds; TX port terminated with 50 ohm.
  - The Lime build gets its own A/B run.
  
  **12. POLICY:** the 3-30 kHz and 225-400 MHz bins are masked to 'no data' before storage. Uploaders are off.
- **Software and process architecture:** **BASE SYSTEM**
  - Radxa OS r2 (noble) on SPI BIOS 6.0.260120, with linux-image-6.18.2-4-qcom held.
  - A/B root on UFS with systemd-boot boot counting and a rescue entry.
  - Kernel command line via /etc/kernel/cmdline and kernel-install: preempt=full, drm.edid_firmware=HDMI-A-1:edid/field.bin (EDID in the initramfs) and video=HDMI-A-1:1920x1080@60 (or @52). With the Lime only: pcie_aspm=off isolcpus=nohz,domain,managed_irq,7 nohz_full=7 rcu_nocbs=7 irqaffinity=0-6.
  - lab-q6a.dtso combines uart6, uart7, i2c0 and i2c2 with a pps-gpio node on GPIO96. The field variant disables pcie0.
  - FastRPC golden set (CDSP c4-00004, ADSP c9-00028, a shared-dma-pool overlay), with QAIRT 2.42.0.251225 from qcom-qnn-sdk-v68.
  
  **PROCESSES (one owner per resource)**
  - **labd** (Python): owns I2C2 through smbus2 (MCP #1 outputs, MCP #3 inputs, the sled through the TCA9517). It also owns every enable, the selectors, SDR leases and modes, the pass scheduler, profiles and instrument serial drivers, plus rfkill and USB de-authorisation.
    - Policy it enforces:
      - the egc-gate (header-level discard; the profile stays disabled until the mixed-recording test passes);
      - the band mask; the Artemis 'out of scope' stop;
      - DSC distress/urgency/safety only; SITOR, skimmer and WEFAX allow-lists;
      - ADS-B dbFlags&1 and AIS type 35 suppression;
      - no bearing logs.
    - For each lease it writes transient DevicePolicy=closed and DeviceAllow drop-ins.
    - rflab and lab-sched become labd modules; the CLI is labctl.
  - **labrx** (C++):
    - The only SDR opener in labrx mode, using librtlsdr .so.2+lab, libairspyhf and LimeSuiteNG if kept.
    - Holds the single mlocked RAM ring, sized at boot.
    - Writes SigMF: V4L as cu8, HF+ as ci16, Lime as ci16.
    - Makes FFT tiles with VkFFT on Turnip, falling back to FFTW.
    - Applies the spur mask and band mask before storage, and keeps no voice IQ.
    - Fans out over shm, UDP or FIFO to gr-satellites, SatDump (file or pipe), the SDR++ network source and slowrx.
    - Provides the NPU tap and the MARK pre-trigger.
  - **labclassify:** inferd-htp (sandboxed: WatchdogSec=5, MemoryMax=1G, CPUAffinity 0-3, one execute thread, 500 ms deadline broker, CDSP restart ladder), inferd-cpu (ONNX Runtime 1.31), fusiond, annotd and npu-health.
  - **labtrain:** a transient unit started by labd between passes: A78 cores, SCHED_IDLE, nice 19, MemoryMax 2G.
  - **labpowerd** (Python): owns the INA228 on I2C0 through i2c-dev, KEY_POWER through evdev, the cutoff table and the shed commands to labd. Restart=always, logind HandlePowerKey=ignore, poweroff and never halt.
  - **labinput:** the framed UART7 protocol with the Pico: keys, encoders, IMU frames, heartbeat, and fan, backlight and display-rail commands.
  - **gpsd 3.25** on UART6, with **chrony 4.5** (refclock PPS /dev/pps0 lock NMEA; maxchange 5 1 -1; rtcsync). pps-gpio is an out-of-tree DKMS module; the Route A fallback runs on the GPIO v2 ioctl with REALTIME timestamps.
  - **The location service** gates each fix:
    - 3D fix with 6 or more satellites;
    - time within 120 s of the RTC;
    - a jump over 100 km needs confirmation.
  
    It computes WMM2025 at the fix. Fallbacks are the last good fix with its age, or manual lat/lon or Maidenhead entry; there is no city table. A first-boot bootstrap accepts a fix that has been stable for N minutes with 8 or more satellites.
  
  **SDR ACCESS**
  - **Mode 1, labrx (default):** passes, survey, NPU teaching and MARK. Passes are recorded and then decoded by SatDump 2.0-alpha from the baseband file; a live pipe is used only if the alpha supports it.
  - **Mode 2, engine-exclusive lease:** readsb, AIS-catcher, radiosonde_auto_rx (uploaders off), OpenWebRX+ 1.2.126, sdrangelsrv (NAVTEX, RTTY, WEFAX, Radio Clock) and the SDR++/SDRangel Expert GUIs. The engine opens the device itself, with ai_tap=false and REC limited to products.
  - **Hand-off sequence:** stop → release → re-enumeration check → start.
  
  **UI:** Lab Shell (Qt 6.4.2 QML) on labwc 0.7.1 with XWayland, labbar (GTK3 + gtk-layer-shell), greetd with a crash counter, and cage as safe mode. One waterfall renderer: a QQuickItem in the Shell, fed from labrx shared memory. Every capture-critical leaf works from the keys and encoders alone, and a CI menu test checks every leaf with and without the Lime and T7.
  
  **ALLOWED DECODERS:**
  - satellites: SatDump (inmarsat_support not built), gr-satellites 5.5;
  - amateur and SSTV: jt9/wsprd only, slowrx (from source), SDRangel 7.27.2 RX-only (no TX/DSD plugins, demodinmarsat removed);
  - monitors: OpenWebRX+ (pinned), readsb/tar1090 with cached tiles, AIS-catcher, auto_rx;
  - broadcast: welle-cli, redsea;
  - science and navigation: Virgo, GNSS-SDR;
  - multimon-ng with EAS only, and only in the US profile.
  
  **BANNED** (CI and device self-test policy audit): the wsjtx GUI, fldigi, QSSTV, direwolf, SoapyRemote, URH, gr-iridium, gr-gsm, kalibrate, pager and trunking decoders, the LimeSuiteNG Amarisoft plugin, SDRangel TX and DSD .so files, and bias options in engine configs.
  
  **PACKAGING**
  - **Repository and pins:**
    - signed aptly repo of +labN debs built from tagged commits on an arm64 builder;
    - third-party debs mirrored into it: OpenWebRX+ 1.2.126, linux-headers 6.18.2-4, the radxa firmware, qcom-qnn-sdk-v68;
    - holds: the kernel and its meta-packages, the firmware and NPU set, Mesa 25.2.8-0ubuntu0.24.04.4 with libdrm 2.4.125, xwayland/wlroots/labwc/qt6, systemd-boot and pipewire;
    - a -1 pin list; unattended-upgrades removed; the apt and fwupd timers masked.
  - **Device hygiene:** brltty purged; ModemManager masked; udev names /dev/lab/<name> by serial.
  - **librtlsdr:** noble 2.0.1 rebuilt with 0204c9c, 65f0658, the zerocopy fix and the bias-tee token patch; rtl_biast diverted; dvb_usb_rtl28xxu blacklisted.
  - **Python tools:** one venv per tool (NanoVNA-Saver via pipx; QtTinySA with PySide6 6.12; Skyfield 1.55 and sgp4 2.27; the lab venv on numpy<2).
  - **Lime only:** la9310-limesdr-dkms+lab, built with -DBUILD_PLUGINS_AMARISOFT=OFF.
  
  **UPDATES:** a GPG-signed offline bundle from a USB stick on LAB USB. It needs 50% battery or more, installs into the inactive root, refuses to proceed if a held package would change, then runs the self-test and blesses the new root; otherwise boot counting rolls back.
  
  **MEMORY POLICY**
  - labrx: LimitMEMLOCK=infinity, OOMScoreAdjust -900.
  - labd and labpowerd: -1000. Trainer 900, Expert GUIs 700, OpenWebRX+ 500, inferd 300.
  - No disk swap; zram 1 GiB at low priority. systemd-oomd off, or limited to the trainer and Expert slices.
  
  **ROADMAP**
  - W1-2 gates (19 Oct-1 Nov 2026): board, kernel, buses, NPU Phase 0, power logs, A/B.
  - P0a/P0b (Nov-Dec): the 1.5 GiB ring and a minimal labeller.
  - The HF-F and second-RTL profiles ship before any HF class appears in the UI.
  - Lime work only if the Lime is kept on 1 Dec.
- **Ram cpu storage budget:** **RAM** (12 GB board; about 11.3 GiB visible, extrapolated from measured boards: 6 GB shows 5609 MB, 8 GB shows 7604 MiB; app RSS figures are MODEL)
  
  | Consumer | GiB |
  |---|---|
  | OS | 0.45-0.7 |
  | labwc + Xwayland + labbar | 0.15-0.3 |
  | Lab Shell | 0.3-0.9 |
  | labd, labpowerd, labinput | 0.12-0.25 |
  | labrx, without the ring | 0.15-0.35 (+ shm) |
  | labclassify (inferd-htp MemoryMax 1 GiB) | 0.6-1.35 |
  | SatDump, post-pass | 0.4-1.2 |
  | SDRangel | 0.2-0.5 |
  | OpenWebRX+ | 0.2-0.5 |
  | readsb, AIS-catcher, auto_rx | 0.25-0.5 |
  | Expert GUI | 0.25-0.5 |
  | trainer (MemoryMax, between passes only) | up to 2.0 |
  | headroom | 1.0 or more |
  
  IQ ring, mlocked and sized once at boot by labrx from the SDR set present:
  - **No Lime:** 1.5 GiB, about 98 s of 2 RTL + HF+ at 16.4 MB/s.
  - **Lime:** 4 GiB, 19.2 s at 56 Msps ci16.
  - **Burst profile:** +3 GiB, only when the trainer, OpenWebRX+, SDRangel and the Expert GUIs are stopped. The 7 GiB total gives about 30 s of 160 Msps while draining to the T7.
  - The 6 and 8 GiB figures are deleted.
  
  Free RAM (model): no Lime, pass 4.6-7.4 GiB; no Lime, training 3.3-5.6; Lime, pass 2.1-4.9; Lime, training 0.8-3.1. The 8 GB board would sit at -0.2 to +2.2 in no-Lime training, so it is rejected.
  
  **CPU** (MODEL)
  - **CPU0-3 (A55, 1.9 GHz):**
    - Shell, labwc and labbar: 0.4-0.8 core.
    - Daemons, gpsd and chrony: 0.1-0.2.
    - labclassify host, fusion and stage-2: 0.3-0.5.
    - ORT CPU detector: up to 1.0 (CPUQuota 100%).
    - Total: 0.8-1.5 typical, 1.8-2.5 in CPU-fallback mode.
  - **CPU4-6 (A78, 2.4 GHz), plus CPU7 (2.7 GHz) without the Lime:**
    - labrx ingest, FFT and tiles for 2 RTL + HF+: 0.3-0.5 core, at SCHED_OTHER nice -5.
    - SatDump: LRPT 0.3-0.5, HRPT 1-1.5 per instance.
    - SDRangel HF 0.3-0.6; readsb 0.3-0.5; OpenWebRX+ 0.5-1.
    - Trainer T2: 3 cores at SCHED_IDLE nice 19, between passes only (4.5-10.8 min per run, or 1-3 min with frozen layers).
    - An LRPT + HRPT pass with the loggers needs 2.8-4.5 cores. That fits 4 cores without the Lime; with the Lime, labd pauses the loggers during Lime passes.
    - If VkFFT fails on the Adreno 643, the LIME-W CPU fallback needs about 2 more A78 cores.
  - **CPU7, Lime only:** isolated, with the Lime MSI moved off it. lime:Rx0 runs at SCHED_OTHER nice -20 if it busy-polls, or SCHED_FIFO 10 if it blocks; decide with the limeTRX loss counters.
  - **GPU:** VkFFT needs about 7.8 GFLOPS of the 808 GFLOPS FP32 measured by Radxa on Mesa 25.2.8.
  - **NPU tile load:**
    - 2x V4L: 14.6 tiles/s (verified).
    - Adding HF-F: 16.6-17.6 tiles/s (model), so the HTP gate is p99 of 28 ms or less at 50% duty.
    - Lime + RTL: 42.5 tiles/s (verified), so the gate is p99 of 11.7 ms or less, or 41 tiles/s or fewer.
    - CPU mode reaches 4-6 tiles/s, so it runs the schedule of about 5 tiles/s.
  
  **STORAGE**
  
  UFS 128 GB (about 119 GiB) layout:
  
  | Partition | Size | Note |
  |---|---|---|
  | ESP | 1 GiB | - |
  | root A | 22 GiB | systemd-boot boot counting, rescue entry |
  | root B | 22 GiB | - |
  | /data | about 74 GiB | NPU dataset quota 20 GB (18.6 GiB), apt mirror 4, map tiles 4, models and golden set 0.3, logs 0.5 (journald 200M) |
  | of which recordings | about 46 GiB | including a 30 GiB rolling raw cap |
  
  Write speed is 388 MB/s inside the about 4 GiB WriteBooster cache; the sustained speed after the cache fills is unknown. Read the chip ID on arrival (0x01CE means Samsung).
  
  Recording rates:
  
  | Stream | Rate |
  |---|---|
  | 1 V4L, cu8 at 2.56 Msps | 5.12 MB/s = 18.4 GB/h |
  | 2 V4L | 36.9 GB/h |
  | HF+, ci16 at 768 ksps | 3.07 MB/s = 11 GB/h (cf32 only for derived products) |
  | 2 RTL + HF+ | 13.3 MB/s = 48 GB/h; the 30 GiB cap lasts about 40 min |
  | One 15-min HRPT pass | 4.6 GB |
  | Lime, 56 Msps ci16 | 224 MB/s, T7 only, about 74 min per TB |
  
  - **Retention:** products are kept by default; raw only when pinned. Unpinned raw is deleted after the decoder oracle runs. labrx refuses to start a raw recording that its cap cannot hold.
  - **Secondary storage, no Lime:** a V30 endurance microSD of 128-256 GB, bought when NAND prices allow (the 61 MB/s measured class is 3.7x the worst stream). It takes raw overflow and a second snapshot copy.
  - **Secondary storage, Lime:** a T7 1 TB on the blue port (port limit 395 MB/s, 1.76x 224 MB/s): NPU raw 400 GB for 14 days, captures and bursts 300 GB, a 64 GiB exFAT exchange area and a snapshot copy.
  - **Boot safety:** data media carry no ESP, because the boot order is USB > SD > NVMe > eMMC > UFS. Acceptance: 20 cold boots with the data card and a LAB stick inserted all land on UFS. The 64 GB rescue card is kept outside the case.
- **Mechanical layout and kit:** **HANDHELD**
  
  Landscape, planned at 220-225 x 135-140 x 55-60 mm. Parametric light-grey ASA shell (PETG rejected: it softens at 75-80 C). A 2 mm aluminium mid-plate serves as chassis, ground, shield and heat spreader.
  
  **Front:**
  - The bonded 7in panel on the left (glass about 164.2x98 mm, inferred; the bezel is drawn only after the panel passes acceptance).
  - A right-hand HMI column 38-42 mm wide:
    - a 30-35 mm main push-encoder;
    - a volume push-encoder;
    - 2x3 sealed keys (HOME, BACK, REC, MARK, FN, LOCK) at a 13 mm pitch;
    - the VEML7700 on the outer top face of the bezel, outside the 30 mm hinged hood, which folds flat as a lid.
  - A left-hand version is a mirrored reprint, not soft keys.
  
  **Inside, front to back:**
  - **Display:** glass, panel and HDMI board; a 4-6 mm display air channel with a 5 V blower; then the mid-plate fins.
  - **Q6A:** 85x56 mm, drawn from Radxa STEP v1.21. Stepped copper block in the 32x31 mm keep-in, with a 40 mm fan to a rear vent.
  - **RF bay** (soldered copper-clad FR4) along the top edge behind the antenna bulkheads: 2x V4L on 15 cm shielded extensions, the Flamingo+, the SAWbird+ NOAA, the injector board, 2x HMC7992 and the LNB injector with its pad.
  - **HF+ can** (tinplate) at the top right, as far as possible from the bucks, together with the Boni bias tee and the G6K selector board.
  - **Power board** (D36V50F12, D36V28F5, 2x TPS7A4701, 2x LT3045, INA228, #2813, AON LDO, supervisor) at the bottom right, with the regulators bonded to the plate.
  - **IP2368:** pad-mounted to the case wall at least 10 mm from the cells.
  - **Pack** (46x25x150 mm) in an insulated compartment along the bottom-left intake side, with a barrier and a vent path.
  - **UFS:** padded to a case boss.
  
  **Airflow:** two separate paths. Intakes at the bottom and rear behind mesh and foam; exhausts at the rear top. The weather target is IPX4/IP54; IP67 is impossible with forced air.
  
  **Panels and penetrations (11-14 in total):**
  - **Top edge:** P1 VHF-137, P2 UHF, P3 L-BAND, P4 LNB F, P5 HF with a ground post, P6 VHF2/AIS, P7 GNSS; optional P8 WIDE; with the Lime, LIME RX1, RX2 and REF IN.
  - **Bottom edge:** the IP2368 USB-C (the only power input), a capped LAB USB-A, a 6-pin locking LAB BUS, 3.5 mm audio, and the T7 lead exit (Lime).
  - **Back:**
    - a captured 1/4-20 nut, or a press-in steel insert in a boss of 6 mm or more (never a thread tapped in the 2 mm plate; pull-test at 3x the device weight);
    - 2-4 strap lugs for the hand and neck straps;
    - the GX12 4-pin IMU socket;
    - a service hatch with the console UART and access to the blue USB-A for EDL with an A-to-A cable.
  - The Q6A USB-C has no case opening.
  
  **Lime provisions:** cut the mid-plate once with the pedestal and riser-clamp holes. Desolder J21 only after burn-in, and only if the Lime is kept; then wire J21 from the bottom pads with a 20 AWG twisted pair. Print the no-Lime shell first; reprint only the top-edge strip if the Lime is kept.
  
  **KITS**
  - **Patch / always-carried pouch:**
    - dipole kit #1 (the V-dipole for LRPT) and dipole kit #2 (AIS/FM);
    - a 17 cm whip, or an A-V85/SRH-701;
    - the Uputronics 440, when it is not on P2;
    - the RTL-SDR Blog L-band patch;
    - the 4-turn helix on the 18 cm disc with the SAWbird+ GOES;
    - the GNSS antenna;
    - 1-2 m RG316 jumpers.
  
    Region-dependent: the bare Bullseye with its 11 cm cone.
  - **Foldable backpack kit** (every piece 35 cm or less; the ultra-compact Yagi has pieces of 17 cm or less), in a 15-20 L daypack:
    - the crossed Yagi;
    - the petal helicone (shares the disc, helix and SAWbird+ GOES);
    - the gore horn (region-dependent);
    - the HF wire reel, 9:1 balun, 5-10 m of coax and counterpoise;
    - the Boni-Whip with a shock-corded 7x35 cm mast, guys and a stake;
    - a travel tripod 35 cm or less folded, with pan-tilt;
    - an antenna roll and element tube;
    - a field pouch: tinySA, FNB58, DMM, pads, loads, Debug Probe.
  - **Bench kit** (Pelican 1450 / Apache 3800, bench only):
    - LiteVNA 64 and the noise source;
    - the pad kit, 30 dB pads, BLK-89-S+, ANNE-50+, 086-6SM+;
    - torque wrench, adapters and the spare LNA V2;
    - Hantek 6022BE with an LA, Pinecil and ESD mat;
    - Anker 737, MTT hub, ISDT 608PD and tools.
  
    The extended kit adds the LBE-1420, the sled, the Pro Stick Plus, the DPS-150 and the SAWbird+ H1.
  - **Travel:** the home-built 72 Wh pack is never flown. The Anker 737 (100 Wh or less) and instruments with Li cells go in the cabin bag; the Pelican may be checked.
- **Size weight estimate:** All figures are MODEL estimates, to be re-derived from the CAD once the panel and pack are in hand.
  
  **Handheld**
  - Size: 220-225 x 135-140 x 55-60 mm, plus about 5 mm for the folded hood. Interior fill 48-63%.
  - Weight: 1.35-1.6 kg without the Lime, +0.15 kg with it.
  
  | Part | kg |
  |---|---|
  | shell | 0.26-0.33 |
  | mid-plate | 0.14 |
  | display module | 0.12-0.18 |
  | pack, BMS and barrier | 0.32 |
  | Q6A and cooler | 0.09 |
  | RF bay contents | 0.2-0.25 |
  | HF+, can and selector | 0.1 |
  | power board | 0.05-0.07 |
  | bulkheads and cables | 0.14 |
  | HMI and hood | 0.1 |
  
  **Carried kit**
  
  | Item | Weight | Volume |
  |---|---|---|
  | Patch-tier extras | 0.25-0.4 kg | about 0.8 L |
  | Foldable kit (with LNB, LNAs, jumpers) | 1.3-1.8 kg | 6-6.5 L |
  | HF kit (wire, balun, coax) | 0.4-0.5 kg | 0.8 L |
  | Boni-Whip and mast | 0.5-0.75 kg | - |
  | Tripod | 0.3-0.6 kg | - |
  | Field pouch | 0.8 kg | 2 L |
  
  **Field daypack (15-20 L):** 4.4-6.0 kg without the HF kit and mast; 5.3-7.3 kg fully loaded. A sling is not enough.
  
  **Bench case:** a Pelican 1450 (14.5 L interior) holds about 8.8 L (61%) and weighs 8.2-9.1 kg loaded. The Pelican figures are unverified because pelican.com returned 403.
  
  **Setup times (targets, unmeasured)**
  - Boot to Shell: 60 s or less. GNSS 3D fix: 60 s or less (LC76G TTFF unverified). IMU sun-sight north: about 1 min.
  - Patch tier: whip 0.5 min; helix on the mini tripod 2 min; LNB with cone, pointed, 2-3 min.
  - Foldable: dipole 2 min, Yagi 4 min (8-9 min ultra-compact), helicone 3 min, horn 4 min; all of it 13 min (17-18 min with the ultra-compact Yagi).
  - HF wire 8-12 min; Boni-Whip on its mast 5-8 min; bench 10-15 min.
  - Arrival to the first LEO pass with one antenna: 6-10 min. Full camp including HF: 25-35 min.
  - Pass cards warn at T-(setup+5) min.
- **Integrated bom:**
  1.
    - **Group:** Compute
    - **Item:** Radxa Dragon Q6A 12 GB (QCS6490)
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 166.37 (TinyTronics EUR 148 incl. VAT, EU, verified) / 189.99 (Allnet, verified)
    - **Budget alternative:** None (8 GB rejected)
    - **Notes:** Burn-in on arrival. Allnet returns are 7 days, unused only.
  2.
    - **Group:** Compute
    - **Item:** Radxa UFS 3.1 128 GB RA022-B10J0U2
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 65.90 (Allnet, verified)
    - **Budget alternative:** TinyTronics EUR 58 (2-4 weeks)
    - **Notes:** A/B root; read ID 0x01CE
  3.
    - **Group:** Cooling
    - **Item:** Radxa Armor 7056A heatsink or stepped Cu block + Adafruit 6101 40 mm 5 V fan + 5 V display-channel blower
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 19.85-24.85 (blower estimated)
    - **Budget alternative:** Arace case $4.99
    - **Notes:** DC on/off from the Pico, no PWM
  4.
    - **Group:** Display
    - **Item:** Wisecoco 7in 1920x1080 2000+ nit HDMI kit (gated on written answers)
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 132.00 (verified)
    - **Budget alternative:** 4D 4DHDMI-70-1280-800-CT-EAR-1000 $128.95 DigiKey (verified)
    - **Notes:** Accept: ≥1800 nits; ≤14 W at 100%, ≤7.5 W at 50%; USB-HID; 151.50/127.90 MHz modes
  5.
    - **Group:** Display
    - **Item:** Shielded HDMI lead Adafruit 2420 + 2x Wurth 74271140 ferrites
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 17.77
    - **Budget alternative:** Adafruit FPC kit $14.50
    - **Notes:** -
  6.
    - **Group:** Display
    - **Item:** Printed 30 mm hinged hood + 7in AR film + VEML7700 breakout
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 15-25 (estimate)
    - **Budget alternative:** Hood only
    - **Notes:** Lux sensor outside the hood
  7.
    - **Group:** HMI
    - **Item:** Raspberry Pi Pico (RP2040), HMI + supervisor MCU
    - **Qty:** 2 (1 spare)
    - **Tier:** core
    - **Price usd:** 10.12 (2 x GBP 3.80)
    - **Budget alternative:** -
    - **Notes:** On switched LAB5; 26 GPIO
  8.
    - **Group:** HMI
    - **Item:** Bourns PEC11R-4215F-S0024 x3, C&K KSC641J IP67 keys x10, Adafruit 2055 knobs x2
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 17.75 (DigiKey lines not re-checked)
    - **Budget alternative:** EC11 + O-ring boot
    - **Notes:** -
  9.
    - **Group:** HMI
    - **Item:** PCA9555 key expander, piezo, status LED
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 5-10 (estimate)
    - **Budget alternative:** -
    - **Notes:** 8 switches with INT on the Pico I2C
  10.
    - **Group:** IMU
    - **Item:** Adafruit BNO085 4754 + RP2040-Zero + metal puck, GX12 4-pin pair, 1.5-2 m shielded 4-core lead, TVS
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 64.49-89.49 (29.50 + 4.99 + 30-55 estimate)
    - **Budget alternative:** SparkFun BNO086 $34.95
    - **Notes:** UART relay to the Pico; never USB
  11.
    - **Group:** GNSS
    - **Item:** Waveshare LC76G 24370 + RTC CR2032 cell
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 15.94 (verified)
    - **Budget alternative:** Uputronics MAX-M10S if spoof flags are needed
    - **Notes:** UART6; PPS on pin 7
  12.
    - **Group:** Interface
    - **Item:** Adafruit CH334F MTT hub 5997
    - **Qty:** 2 (1 fitted, 1 spare)
    - **Tier:** core
    - **Price usd:** 9.90 (verified)
    - **Budget alternative:** Pi Hut GBP 4.80
    - **Notes:** 5V pin from LAB5; Q6A VBUS unconnected
  13.
    - **Group:** Interface
    - **Item:** Adafruit MCP23017 5346 (0x20 outputs, 0x22 inputs)
    - **Qty:** 2
    - **Tier:** core
    - **Price usd:** 11.90 (verified)
    - **Budget alternative:** TCA9535
    - **Notes:** Powered from Q6A 3.3 V; 100k pull-downs
  14.
    - **Group:** Interface
    - **Item:** TCA9517 buffer, 74LVC1G17, 2N7002/AO3400 FETs, relay driver, BAT54 diodes
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 5-10 (estimate)
    - **Budget alternative:** -
    - **Notes:** -
  15.
    - **Group:** Recovery
    - **Item:** ALLNET 64 GB microSD + Adafruit 5212 reader + 6324 cable + USB3 A-A EDL cable
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 31.89
    - **Budget alternative:** -
    - **Notes:** Rescue card kept outside the case
  16.
    - **Group:** Power
    - **Item:** Molicel INR21700-P50B
    - **Qty:** 5 (4 + spare)
    - **Tier:** core
    - **Price usd:** 49.95 (9.99 each, 18650 Battery Store, verified)
    - **Budget alternative:** Local established retailer; NKON EUR 6.75 (unverified)
    - **Notes:** Test ≥4.85 Ah, IR, 68-70 g
  17.
    - **Group:** Power
    - **Item:** Daly 4S 15 A common-port balancing BMS
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 9.00 (TinyTronics)
    - **Budget alternative:** Other 4S 15-20 A
    - **Notes:** Charger wake test 3/3
  18.
    - **Group:** Power
    - **Item:** IP2368 4S 100 W PD board, charge-only BZ (RVSET 5.1k, RISET 15k)
    - **Qty:** 2
    - **Tier:** core
    - **Price usd:** 25-49 (unverified)
    - **Budget alternative:** -
    - **Notes:** Burn in; 10k B3380 NTC; KSD9700
  19.
    - **Group:** Power
    - **Item:** Pololu D36V50F12 (SYS12)
    - **Qty:** 2 (1 spare)
    - **Tier:** core
    - **Price usd:** 79.90 (verified, Rationed)
    - **Budget alternative:** Fixed-frequency forced-PWM sync buck (P5) if the A/B fails
    - **Notes:** Plate-bonded
  20.
    - **Group:** Power
    - **Item:** Pololu D36V28F5 (LAB5)
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 23.95
    - **Budget alternative:** -
    - **Notes:** 3 A fuse
  21.
    - **Group:** Power
    - **Item:** Pololu #2813 HP pushbutton power switch
    - **Qty:** 2 (1 spare)
    - **Tier:** core
    - **Price usd:** 17.90 (8.95 each, verified)
    - **Budget alternative:** -
    - **Notes:** Button wired on-only (A to GND)
  22.
    - **Group:** Power
    - **Item:** Adafruit INA228 5832
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 14.95 (verified)
    - **Budget alternative:** -
    - **Notes:** Shunt in the pack lead; AON 3.3 V; pull-ups removed
  23.
    - **Group:** Power
    - **Item:** TI TPS7A4701 LDO (LNB 13.2 V, Boni 12.5 V)
    - **Qty:** 2
    - **Tier:** core
    - **Price usd:** 10-20 (unverified)
    - **Budget alternative:** TPS7A4700 audio LDO module boards
    - **Notes:** 36 V in, 1 A (ti.com verified); PG to MCP #3
  24.
    - **Group:** Power
    - **Item:** ADI LT3045 (paralleled 4.5 V LNA rail)
    - **Qty:** 2
    - **Tier:** core
    - **Price usd:** 16.66 (LCSC 8.33 each)
    - **Budget alternative:** -
    - **Notes:** LCSC is not ADI-franchised
  25.
    - **Group:** Power
    - **Item:** TI TPS2553 (LAB port 0.75 A; LNA ch1-4 300 mA; HF+ and RTL VBUS)
    - **Qty:** 10
    - **Tier:** core
    - **Price usd:** 5.50
    - **Budget alternative:** -
    - **Notes:** -
  26.
    - **Group:** Power
    - **Item:** AON 3.3 V LDO (TPS709 class) + micropower UV supervisor 12.8/13.6 V
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 2-4 (estimate)
    - **Budget alternative:** -
    - **Notes:** Parts verified in P5
  27.
    - **Group:** Power
    - **Item:** Protection/filter set: 7.5 A pack, 4 A J21 and 3 A LAB5 blade fuses + holders; SMBJ17A; SMBJ13A; 220 µF/25 V; PTCs (0.75 A AUX, 0.2 A Boni, LNB sized after measurement); ±20 V V_GS P-FET; 1.5 A eFuse; LC parts; Mix-31 ferrites; XT30
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 15-25 (estimate)
    - **Budget alternative:** -
    - **Notes:** -
  28.
    - **Group:** Power
    - **Item:** Custom 2-layer PCBs: power board + 5-channel injector board (chokes ≥0.5 A, LNB choke ≥1 A, C0G blocks)
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 10-30 (estimate)
    - **Budget alternative:** Mini-Circuits TCBT-2R5G+ $11.31 on ≤150 mA channels
    - **Notes:** VNA-qualify, conducted
  29.
    - **Group:** Battery
    - **Item:** Pack sundries (nickel, fish paper, Kapton, JST-XH 5-pin, XT30 service lead), spot-weld service, FR-4/mica barrier, foam + reflective film, fire bag
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 50-110 (estimate)
    - **Budget alternative:** Weld at a battery shop
    - **Notes:** Never flown
  30.
    - **Group:** Charging
    - **Item:** 65-100 W USB-C PD charger + 5 A C-C cable
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 35-60 (estimate)
    - **Budget alternative:** Anker 737 (bench row)
    - **Notes:** PDO ≥60 W; FNB58-qualify
  31.
    - **Group:** Mechanical
    - **Item:** ASA 1 kg, CNC Kitchen M3 inserts and screws, Gelid pads, hand + neck strap
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 98-133
    - **Budget alternative:** Print service
    - **Notes:** Inserts verified EUR 9.40
  32.
    - **Group:** Mechanical
    - **Item:** 2 mm Al mid-plate, copper-clad FR4 RF bay, steel 1/4-20 insert, KSD9700
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 35-70 (estimate)
    - **Budget alternative:** -
    - **Notes:** Pull test at 3x weight
  33.
    - **Group:** Mechanical
    - **Item:** Weather kit IPX4/IP54 (mesh + foam, ePTFE vents, port caps, rain sleeve, silica gel)
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 45-110 (estimate)
    - **Budget alternative:** Caps + rain sleeve
    - **Notes:** -
  34.
    - **Group:** SDR
    - **Item:** RTL-SDR Blog V4L (R828S)
    - **Qty:** 3 (RTL-A, RTL-B, spare)
    - **Tier:** core
    - **Price usd:** 113.85 (37.95 each, verified)
    - **Budget alternative:** V3 fallback
    - **Notes:** Official channels only; EU via eBay/AliExpress 4523039
  35.
    - **Group:** RF
    - **Item:** Nooelec SAWbird+ NOAA cased (100800)
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 49.95 (verified)
    - **Budget alternative:** Non-plus SAWbird NOAA (80 mA)
    - **Notes:** Inside, behind P1
  36.
    - **Group:** RF
    - **Item:** Nooelec Flamingo+ FM v2 (100813)
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 24.95 (verified)
    - **Budget alternative:** RTL-SDR Blog band-stop $16.95 (no DC rating)
    - **Notes:** Filter first at VHF
  37.
    - **Group:** RF
    - **Item:** Uputronics 440 MHz CubeSAT filtered preamp
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 68.71 (GBP 51.59 incl. VAT, verified available)
    - **Budget alternative:** LNA V2 + Nooelec Ham Filter Bank $66.95
    - **Notes:** Always at the antenna end; measure current
  38.
    - **Group:** RF
    - **Item:** Generic HMC7992 SP4T boards (RTL-A and RTL-B selectors)
    - **Qty:** 2
    - **Tier:** core
    - **Price usd:** 30-40 (marketplace, unverified)
    - **Budget alternative:** Manual 'connect X' prompt
    - **Notes:** Default 50 ohm; qualify ≥30 dB isolation
  39.
    - **Group:** RF
    - **Item:** Cable/bulkhead set: 7 SMA + 1 F bulkheads, RG316 jumpers, 2x shielded 15 cm USB extensions + ferrites, pigtails, 75 ohm F lead
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 90-170 (estimate)
    - **Budget alternative:** VNA-screened generic RG316
    - **Notes:** Pads come from the bench kit
  40.
    - **Group:** HF
    - **Item:** Airspy HF+ Discovery
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 169.00 (ITEAD, verified)
    - **Budget alternative:** 2nd V4L in upconverter mode (no LF)
    - **Notes:** CH334F H4; in its own can
  41.
    - **Group:** HF
    - **Item:** HF+ selector: 2x Omron G6K-2F-RF 5 V (series-shunt) + driver PCB
    - **Qty:** 1 set
    - **Tier:** core
    - **Price usd:** 62-80 (RS UK, GBP 43-52 for two, ex VAT)
    - **Budget alternative:** Manual swap at P5/P6
    - **Notes:** De-energised = 50 ohm; ≥35 dB at 162-260 MHz
  42.
    - **Group:** HF
    - **Item:** Tinplate HF+ can + LC + Mix-31 on VBUS
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 8-15 (estimate)
    - **Budget alternative:** -
    - **Notes:** -
  43.
    - **Group:** HF
    - **Item:** Two-stage coax CM choke (FT-240-77 + FT-240-31, RG316, bonded bracket)
    - **Qty:** 1
    - **Tier:** core
    - **Price usd:** 15-30 (unverified)
    - **Budget alternative:** Clip-on ferrites (inadequate below a few MHz)
    - **Notes:** Measure CM impedance on the LiteVNA
  44.
    - **Group:** Antennas
    - **Item:** RTL-SDR Blog multipurpose dipole kit #1 (V-dipole, LRPT default)
    - **Qty:** 1
    - **Tier:** antenna-patch
    - **Price usd:** 17.95 (verified)
    - **Budget alternative:** 2-3 piece rods
    - **Notes:** 23 cm collapsed
  45.
    - **Group:** Antennas
    - **Item:** RTL-SDR Blog dipole kit #2 (AIS/FM/DAB on the HF+, spare elements)
    - **Qty:** 1
    - **Tier:** antenna-patch
    - **Price usd:** 17.95 (verified)
    - **Budget alternative:** Spare elements only
    - **Notes:** -
  46.
    - **Group:** Antennas
    - **Item:** 70 cm whip: DIY 17 cm, or Diamond SRH-701 / Baofeng A-V85
    - **Qty:** 1
    - **Tier:** antenna-patch
    - **Price usd:** 3-25 (estimate)
    - **Budget alternative:** DIY 17 cm
    - **Notes:** Tilt broadside
  47.
    - **Group:** Antennas
    - **Item:** RTL-SDR Blog active L-band patch (1525-1660 MHz, 20 mA)
    - **Qty:** 1
    - **Tier:** antenna-patch
    - **Price usd:** 59.95 (verified)
    - **Budget alternative:** 2-turn helix + SAWbird+ iO
    - **Notes:** Inmarsat-C and GNSS-SDR
  48.
    - **Group:** Antennas
    - **Item:** 4-turn RHCP helix on a shared 18 cm 1.5 mm Al disc (DIY)
    - **Qty:** 1
    - **Tier:** antenna-patch
    - **Price usd:** 10-20 (estimate)
    - **Budget alternative:** -
    - **Notes:** Same disc as the helicone
  49.
    - **Group:** Antennas
    - **Item:** Nooelec SAWbird+ GOES cased (100792)
    - **Qty:** 1
    - **Tier:** antenna-patch
    - **Price usd:** 49.95 (verified)
    - **Budget alternative:** Barebones $44.95 (only inside a shielded case)
    - **Notes:** Serves both tiers
  50.
    - **Group:** Antennas
    - **Item:** Waveshare GNSS L1+L5 active antenna (25346)
    - **Qty:** 1
    - **Tier:** antenna-patch
    - **Price usd:** 16.99 (verified)
    - **Budget alternative:** u-blox ANN-MB5 $42.50
    - **Notes:** -
  51.
    - **Group:** Antennas
    - **Item:** Crossed 2 m / 70 cm Yagi, ultra-compact (WB2HOL + N2SPI, DIY)
    - **Qty:** 1
    - **Tier:** antenna-foldable
    - **Price usd:** 25-40 (estimate)
    - **Budget alternative:** Standard build (35 cm pieces)
    - **Notes:** Tune receive-only
  52.
    - **Group:** Antennas
    - **Item:** Petal helicone (18 cm disc + 8 petals, DIY)
    - **Qty:** 1
    - **Tier:** antenna-foldable
    - **Price usd:** 20-35 (estimate)
    - **Budget alternative:** -
    - **Notes:** Shares the helix and SAWbird+ GOES
  53.
    - **Group:** Antennas
    - **Item:** HF wire kit: Nooelec Balun One Nine v2 + 7-15 m wire on a winder (or Tecsun AN-05) + 5-10 m thin coax + counterpoise
    - **Qty:** 1 set
    - **Tier:** antenna-foldable
    - **Price usd:** 46.95-66.44
    - **Budget alternative:** DIY wire only
    - **Notes:** HF only; bias locked off
  54.
    - **Group:** Antennas
    - **Item:** Bonito Boni-Whip (bias tee included)
    - **Qty:** 1
    - **Tier:** antenna-foldable
    - **Price usd:** 178.73 (WiMo EUR 159, from 20 Nov 2026) / 123.95 (Moonraker, unverified)
    - **Budget alternative:** PA0RDT miniwhip clone EUR 25.90
    - **Notes:** 12.5 V; at least 2 m up
  55.
    - **Group:** Supports
    - **Item:** Shock-corded mast (7 x 35 cm, about 2.4 m) + guys + stake
    - **Qty:** 1 set
    - **Tier:** antenna-foldable
    - **Price usd:** 15-50 (estimate)
    - **Budget alternative:** Tree or fence mount
    - **Notes:** -
  56.
    - **Group:** Supports
    - **Item:** Travel tripod ≤35 cm folded, 1.2 m or more, pan-tilt, 1/4-20
    - **Qty:** 1
    - **Tier:** antenna-foldable
    - **Price usd:** 40-100 (estimate)
    - **Budget alternative:** Dipole kit's mini tripod
    - **Notes:** Horn, helicone, V-dipole
  57.
    - **Group:** Bags
    - **Item:** Padded antenna roll + element tube + 15-20 L daypack
    - **Qty:** 1 set
    - **Tier:** antenna-foldable
    - **Price usd:** 80-155 (estimate)
    - **Budget alternative:** -
    - **Notes:** -
  58.
    - **Group:** Lab instruments
    - **Item:** LiteVNA 64
    - **Qty:** 1
    - **Tier:** bench
    - **Price usd:** 175.73 ex VAT export / 210.88 incl. FR VAT (Passion Radio)
    - **Budget alternative:** Lab401 EUR 192 (not chosen)
    - **Notes:** Conducted use only
  59.
    - **Group:** Lab instruments
    - **Item:** tinySA Ultra+ ZS407
    - **Qty:** 1
    - **Tier:** bench
    - **Price usd:** 204.28 ex VAT / 247.18 incl. VAT (Astroradio, verified)
    - **Budget alternative:** Mirfield GBP 189.95
    - **Notes:** Order early: it gates the regulator decision
  60.
    - **Group:** Lab instruments
    - **Item:** Noise source: Mini-Circuits ZFL-500LN+ (or ZFL-500+) in a DIY N8DMT-type source + box
    - **Qty:** 1
    - **Tier:** bench
    - **Price usd:** 104.55-126.81
    - **Budget alternative:** Used ZFL-500 $20-40
    - **Notes:** BENCH only via AUX; ENR at regulated 12 V
  61.
    - **Group:** RF accessories
    - **Item:** Nooelec pad kit, 2x 30 dB pads, 2x BLK-89-S+, 3x ANNE-50+, 3x 086-6SM+
    - **Qty:** 1 set
    - **Tier:** bench
    - **Price usd:** 212.68
    - **Budget alternative:** VAT-30W2+ $31.43 per 30 dB pad
    - **Notes:** One 086 cut into E-field probes
  62.
    - **Group:** RF accessories
    - **Item:** SMA torque wrench 0.9 N·m + adapter set
    - **Qty:** 1 set
    - **Tier:** bench
    - **Price usd:** 50.84-62.84
    - **Budget alternative:** AliExpress ratcheting $51.49
    - **Notes:** Confirm listing live
  63.
    - **Group:** RF accessories
    - **Item:** Spare RTL-SDR Blog Wideband LNA V2
    - **Qty:** 1
    - **Tier:** bench
    - **Price usd:** 19.95 (verified)
    - **Budget alternative:** -
    - **Notes:** Also the optional WIDE-path LNA
  64.
    - **Group:** Bench electronics
    - **Item:** FNIRSI FNB58 Std (no radio)
    - **Qty:** 1
    - **Tier:** bench
    - **Price usd:** 53.99 (verified)
    - **Budget alternative:** -
    - **Notes:** Measures every USB load
  65.
    - **Group:** Bench electronics
    - **Item:** ANENG AN8008/9 DMM
    - **Qty:** 1
    - **Tier:** bench
    - **Price usd:** 26-53
    - **Budget alternative:** -
    - **Notes:** Store unconfirmed
  66.
    - **Group:** Bench electronics
    - **Item:** Hantek 6022BE + fx2lafw LA
    - **Qty:** 1 set
    - **Tier:** bench
    - **Price usd:** 141-172
    - **Budget alternative:** 6022BL on AliExpress $84-102 (store unconfirmed)
    - **Notes:** -
  67.
    - **Group:** Bench electronics
    - **Item:** Raspberry Pi Debug Probe
    - **Qty:** 1
    - **Tier:** bench
    - **Price usd:** 12.00 (verified)
    - **Budget alternative:** -
    - **Notes:** Pico SWD
  68.
    - **Group:** Bench electronics
    - **Item:** Pinecil V2 (IronOS Bluetooth off)
    - **Qty:** 1
    - **Tier:** bench
    - **Price usd:** 25.99
    - **Budget alternative:** -
    - **Notes:** Powered from the PD bank
  69.
    - **Group:** Bench electronics
    - **Item:** iFixit portable anti-static mat
    - **Qty:** 1
    - **Tier:** bench
    - **Price usd:** 34.95
    - **Budget alternative:** iFixit EU EUR 29.95
    - **Notes:** -
  70.
    - **Group:** Bench electronics
    - **Item:** Anker 737 power bank (20 V/5 A PDO, ≤100 Wh)
    - **Qty:** 1
    - **Tier:** bench
    - **Price usd:** 109.99 (verified)
    - **Budget alternative:** Existing ≥60 W bank
    - **Notes:** Cabin baggage
  71.
    - **Group:** Bench electronics
    - **Item:** Waveshare MTT bench hub (bank-powered)
    - **Qty:** 1
    - **Tier:** bench
    - **Price usd:** 24.64 (verified)
    - **Budget alternative:** -
    - **Notes:** Behind the LAB port on the bench
  72.
    - **Group:** Bench electronics
    - **Item:** ISDT 608PD balance charger
    - **Qty:** 1
    - **Tier:** bench
    - **Price usd:** 32.99-42.99 (unverified)
    - **Budget alternative:** -
    - **Notes:** Monthly 4.20 V balance via the node-N port
  73.
    - **Group:** Tools
    - **Item:** Tools, spares, notebook, build tools (calipers, snips, M5 tap/die, heat gun)
    - **Qty:** 1 set
    - **Tier:** bench
    - **Price usd:** 245-400 (estimate)
    - **Budget alternative:** Borrow / makerspace
    - **Notes:** -
  74.
    - **Group:** Lab extended
    - **Item:** Leo Bodnar LBE-1420 GPSDO
    - **Qty:** 1
    - **Tier:** extended
    - **Price usd:** 175.80 (GBP 132, verified)
    - **Budget alternative:** PPS count + GNSS-SDR ppm (core, free)
    - **Notes:** Conducted, 80 dB pads + DC block
  75.
    - **Group:** Lab extended
    - **Item:** FlightAware Pro Stick Plus
    - **Qty:** 1
    - **Tier:** extended
    - **Price usd:** 69.92 (GBP 52.50, verified)
    - **Budget alternative:** Uputronics 1090 preamp on the spare V4L
    - **Notes:** Continuous ADS-B on LAB USB
  76.
    - **Group:** Lab extended
    - **Item:** RF sled: HMC7992 SP4T + PE4302 + MCP23017 #2 + ADS1115 + buck→LC→LDO bias + box
    - **Qty:** 1
    - **Tier:** extended
    - **Price usd:** 104-168 (unverified)
    - **Budget alternative:** Manual SMA swaps
    - **Notes:** Qualify isolation conducted
  77.
    - **Group:** Lab extended
    - **Item:** Nooelec SAWbird+ H1
    - **Qty:** 1
    - **Tier:** extended
    - **Price usd:** 45-50
    - **Budget alternative:** Reuse helix/helicone with GOES (no)
    - **Notes:** 120 mA via TPS2553
  78.
    - **Group:** Lab extended
    - **Item:** FNIRSI DPS-150 bench supply
    - **Qty:** 1
    - **Tier:** extended
    - **Price usd:** 73-75
    - **Budget alternative:** -
    - **Notes:** -
  79.
    - **Group:** Lab extended
    - **Item:** Pelican 1450 / Apache 3800 case with dividers
    - **Qty:** 1
    - **Tier:** extended
    - **Price usd:** 30-169
    - **Budget alternative:** Apache 3800
    - **Notes:** Bench kit only
  80.
    - **Group:** Optional / gated
    - **Item:** LimeSDR Micro M.2 Basic + $18 shipping + 2x MHF4L-SMA
    - **Qty:** 1
    - **Tier:** optional
    - **Price usd:** 279 (verified)
    - **Budget alternative:** Airspy Mini for AHRPT rates only
    - **Notes:** Keep/cancel by 1 Dec 2026
  81.
    - **Group:** Optional / gated
    - **Item:** Lime parts: ADT-Link R44SF, I-PEX 90435-001 tool, pedestal + pad + fins, DC blocks/pads, 3rd HMC7992
    - **Qty:** 1 set
    - **Tier:** optional
    - **Price usd:** 87-127
    - **Budget alternative:** -
    - **Notes:** Only if the Lime is kept
  82.
    - **Group:** Optional / gated
    - **Item:** Samsung T7 1 TB
    - **Qty:** 1
    - **Tier:** optional
    - **Price usd:** 229.99-274.99 (snippets)
    - **Budget alternative:** None needed without the Lime
    - **Notes:** Outside, bottom edge; Lime only
  83.
    - **Group:** Optional / gated
    - **Item:** QO-100 add-on: Othernet Bullseye TCXO LNB + F/75 ohm parts + cone/horn materials
    - **Qty:** 1 set
    - **Tier:** optional
    - **Price usd:** 47.95-75.00
    - **Budget alternative:** QRO.cz LNB as an upgrade
    - **Notes:** Held until region known; LNB rail already in core
  84.
    - **Group:** Optional / gated
    - **Item:** Nooelec SAWbird+ iO cased (100788)
    - **Qty:** 1
    - **Tier:** optional
    - **Price usd:** 49.95 (verified)
    - **Budget alternative:** L-band patch (core)
    - **Notes:** Only after the egc-gate passes
  85.
    - **Group:** Optional / gated
    - **Item:** V30 endurance microSD 128-256 GB
    - **Qty:** 1
    - **Tier:** optional
    - **Price usd:** 25-82 (volatile)
    - **Budget alternative:** UFS only
    - **Notes:** Raw overflow; buy when prices allow
  86.
    - **Group:** Optional / gated
    - **Item:** Airspy Mini
    - **Qty:** 1
    - **Tier:** optional
    - **Price usd:** about 140-160 (GBP ~110, unverified)
    - **Budget alternative:** Spare V4L at 2.88 Msps
    - **Notes:** Only after Metop hump + 2.88 Msps tests
  87.
    - **Group:** Optional / gated
    - **Item:** 2 m/WIDE path: second Flamingo+ FM (uses the bench LNA V2)
    - **Qty:** 1
    - **Tier:** optional
    - **Price usd:** 24.95
    - **Budget alternative:** -
    - **Notes:** Port P8
  88.
    - **Group:** Optional / gated
    - **Item:** Pololu D36V28F5 #2 for a 5 V-only display board
    - **Qty:** 1
    - **Tier:** optional
    - **Price usd:** 23.95
    - **Budget alternative:** -
    - **Notes:** Only if Wisecoco confirms 5 V input
  89.
    - **Group:** Optional / gated
    - **Item:** AD8318-class log detector power meter
    - **Qty:** 1
    - **Tier:** optional
    - **Price usd:** 25-60
    - **Budget alternative:** tinySA channel power (core)
    - **Notes:** Delegated: optional extended
- **Total cost:** USD before shipping, import VAT and duty. Low ends use EU-optimised or verified-cheapest prices; about 60-70% of the low total was re-seen live on 18 Oct 2026, and the rest are marked estimates. FX: 1 EUR = 1.1241 USD, 1 GBP = 1.3318 USD.
  
  Per tier:
  
  | Tier | Contents | USD |
  |---|---|---|
  | core | handheld incl. internal RF, HF+ and selector, power, mechanics, weather kit, cable set, pack build, charger | 1,758-2,253 |
  | antenna-patch | always-carried antennas | 176-208 |
  | antenna-foldable | Yagi, helicone, HF wire, Boni-Whip, mast, tripod, bags | 351-625 |
  | bench | lab core instruments and tools | 1,475-1,810 |
  | extended | GPSDO, Pro Stick Plus, sled, H1, DPS-150, case | 498-708 |
  | optional / gated | not in the roll-ups | 933-1,157 |
  
  The optional tier breaks down as:
  - Lime set (Lime + parts + T7): about $596-681.
  - QO-100 add-on: $48-75.
  - SAWbird+ iO: $49.95.
  - microSD: $25-82.
  - Airspy Mini: about $140-160.
  
  Roll-ups:
  - Handheld + patch antennas: $1,934-2,461.
  - Handheld + both antenna tiers: $2,285-3,086.
  - Plus the bench lab: $3,759-4,896.
  - Everything except optional: $4,257-5,603.
  
  Compared with the world-sourcing totals (core device $1,138-1,278 + HF chain $368-463), the core rises by about $250-510. The increase comes from parts that were missing: weather kit, cable set, pack build, PD charger, custom PCBs, selectors, CM choke, IMU puck kit and display hood.
- **Build order:**
  - 1. Today (18-20 Oct 2026), stock-risk items first: order the Q6A 12 GB and the UFS 128 GB (EU: one TinyTronics order; elsewhere: Allnet with the case, RTC cell and 64 GB SD). Re-check stock at checkout.
  - 2. Today: one Adafruit bring-up order (Debug Probe, 2x CH334F, 2x MCP23017, INA228, BNO085, fan, HDMI lead, reader, cable, knobs). Plus 3x V4L, 2 dipole kits, the L-band patch, the pigtail and adapter sets and the spare LNA V2 from the official RTL-SDR Blog channel.
  - 3. Today: send Wisecoco the written questions (HID VID:PID, bonding/AR, input V/I, EDID, 151.50/127.90 MHz modes, DSI mode, glove mode, contents). If there is no clear answer in about 7 days, order the 4D from DigiKey ($128.95).
  - 4. Week 1, instruments that gate decisions: tinySA ZS407 (official-list seller), FNB58 Std, a DMM and the Airspy HF+ (ITEAD). The HF+ is needed for the LF/HF regulator A/B and for its own current measurement.
  - 5. Week 1, power parts: one Pololu order (2x D36V50F12, D36V28F5, 2x #2813) because stock is Rationed. One LCSC order (2x TPS7A4701, 2x LT3045, 10x TPS2553, SMBJ13A/17A, fuses, PTCs, AON LDO, supervisor). 5x P50B from a local retailer, the Daly BMS, 2-3 IP2368 boards and 2 Picos.
  - 6. W1-2 board gates (19 Oct-1 Nov), with the board on a current-limited 12 V bench supply into J21:
  - 12 h stressapptest plus memtester; 50-100 cold boots with UART logs; SPI NOR backup; UFS chip ID.
  - Build librtlsdr .so.2 and confirm 'V4 Lite Detected'.
  - HDMI at 148.5 MHz, then the field EDIDs.
  - UART6 TX loopback, PPS on GPIO96, the UART7 overlay, I2C0/I2C2 with 1e6 reads each; pinmux-pins audit.
  - NPU Phase 0 (fastrpc_test 3/3, QAIRT 2.42, SpecDet p99, A16W8, VTCM).
  - VkFFT at N=4096 and 65536; MemTotal and app RSS.
  - FE1.1s 30-min zero-drop test.
  - 7. Early on-air checks as parts arrive: ISS SSTV Series 34 (22-25 Oct, 437.550 MHz) if a V4L and dipole arrive in time; Meteor LRPT on the V-dipole once the SAWbird+ NOAA and Flamingo+ arrive.
  - 8. Power board bring-up on the bench, with a current-limited supply and an electronic load:
  - every rail and the TVSs;
  - the supervisor at 12.8/13.6 V, the EN backstop at 12.0/13.5 V, and whether a held OFF blocks the A-pin button;
  - the eFuses;
  - back-feed with the FNB58 (0 V on Q6A VBUS and HDMI +5 V with the Q6A off);
  - standby drain.
  - 9. Narrow-RBW LF/HF/VHF A/B of the D36V50F12, D36V28F5 and IP2368: HF+ terminated, then on the wire or whip, with load steps from 0.3 to 3 A. Then the 60-min sealed-case test at 3.5 A at 14.0 V and 16.4 V. Decide whether to keep the D36V50F12 or pick the replacement buck in P5.
  - 10. RF parts (week 1-2): the Nooelec order (NOAA+, GOES+, Flamingo+, Balun, pad kit; free shipping), the Uputronics 440, the injector PCB, the HMC7992 boards and the G6K selector. Measure the HF+, Uputronics and LNA V2 currents; VNA-qualify the injectors, selectors and pads, conducted.
  - 11. Pack build (spot-weld service), BMS wake 3/3, IP2368 NTC inhibit, a 2 h burn-in at 3 A on 2-3 boards, and qualification of each PD source.
  - 12. Display acceptance on arrival: nits; power at 50% and 100%; USB-HID; both EDID modes; 20 cold boots; display states in the A/B; stability at SYS12 = 11.0 V.
  - 13. Case CAD from Radxa STEP v1.21, the measured panel and the pack. Print, integrate, run the 45-min noon soak in modes B, D and G, then the full A/B matrix with the lid closed. Publish spur mask v1.
  - 14. Lab core instruments (week 2-3): LiteVNA, Mini-Circuits parts, the noise-source amplifier, Pinecil, mat, Anker 737, MTT hub, Hantek with LA, torque wrench (after confirming the listing).
  - 15. From 20 Nov 2026: the Boni-Whip, CM-choke impedance measurement, LF Quiet tests and the isolation of the HF+ selector.
  - 16. 1 Dec 2026: Lime keep/cancel by rule C1. If kept: R44SF, the I-PEX tool, a re-priced T7, and the post-delivery acceptance inside the 30-day guarantee.
  - 17. Once the user's region is confirmed inside the Es'hail-2 footprint: buy the Bullseye and the horn materials, measure the LNB current at 13.2 V, then set the PTC and the pad.
  - 18. Once the egc-gate passes on L-band patch recordings: buy the SAWbird+ iO. Otherwise drop the Inmarsat-C profile.
  - 19. Last: the extended lab (LBE-1420, Pro Stick Plus, qualified sled, SAWbird+ H1, DPS-150, case). Deferred: the microSD (NAND prices), the T7 (only with the Lime), and the Airspy Mini (only after the Metop hump and the V4L 2.88 Msps tests).
- **Open items:**
  - Currents, cold and hot, at the operating voltage: HF+ Discovery (5 V), Boni-Whip (12.5 V), Bullseye (13.2 V), Uputronics 440, LNA V2 and the ZFL-500 noise source (12 V). Then set the PTC and TPS2553 limits at 1.5-2x the measured value.
  - Display board: input voltage range and current at 25/50/100%; luminance at full white; whether 2200x1148@59.99 (151.50 MHz) and 2200x1125@51.68 (127.90 MHz) are accepted; the delivered clock and its harmonic line on a near-field E-probe; the DSI mode and lane rate; stability at SYS12 = 11.0 V; the touch VID:PID.
  - D36V50F12: fundamental frequency against load and input voltage; the light-load (PSM) threshold; spurs within ±5 kHz of 40, 60, 77.5, 162, 490, 518 and 4209.5 kHz; dropout curve for 13.0-13.6 V in; 3.5 A for 60 min in the sealed case at 14.0 and 16.4 V. Repeat for the D36V28F5 and the IP2368.
  - Per-mode pack power and usable energy from the INA228 logs, replacing modes2.py. Also standby drain; BMS wake from the charger; IP2368 NTC inhibit and behaviour with a 45 W source.
  - #2813: does a held OFF input from the supervisor block the A-pin button? Does the BAT54-diode button network meet the A-pin threshold? Does the cold-boot pulse (0.8-1.0 s on J21 pin 3) boot the board reliably?
  - Back-feed: 0 V on Q6A VBUS and HDMI +5 V with the Q6A off and LAB5 on; zero reverse current on every Q6A USB port; touch-bridge back-drive.
  - LT3045 pair at 4.5 V from LAB5 near dropout: ripple and PSRR at the LNA ports. Also the TPS2553 trip point at the 300 mA setting, and the dissipation of the TPS7A4701 LNB LDO on the plate.
  - Thermal: the 45-min noon soak with the hood fitted (frame ≤60 C, glass ≤65 C, cells ≤45 C); SoC temperature in modes B/D/G; the panel NTC derating points; charger temperature against the pack.
  - pcie0 disabled: does the 25 MHz NIC crystal still radiate at 1700.000/1575.000 MHz?
  - RF parts: isolation, loss and logic levels of the HMC7992 boards; G6K pair isolation at 162-260 MHz and loss from 10 kHz to 260 MHz; CM-choke impedance at 60 kHz and 1-30 MHz; injector loss and return loss per band; DC pass of the Flamingo+ (only if any bias ever crosses it).
  - The full narrow-RBW A/B matrix for every state, with the GNSS C/N0 delta per state, published as spur mask v1.
  - FE1.1s tree: a 30-min zero-drop test with RTL-B, HF+ and one LAB device (and with 4 streams); the effect of de-authorising Wi-Fi.
  - Q6A bring-up: UART6 TX; GPIO96 free; the UART7 overlay on the held image; GPIO24/25 usable with UART6 enabled; the pps-gpio DKMS module; the watchdog DT node; which package provides systemd-bless-boot; whether UEFI variables persist.
  - NPU and compute: MemTotal and app RSS; VkFFT on the Adreno 643 (N=4096 and 65536); HTP p99 for SpecDet-S/M/G; A16W8 on 2.42; VTCM size; soc_model 35 vs 93; CPU load of SatDump, SDRangel and OpenWebRX+.
  - Storage: sustained UFS write after the WriteBooster cache, and the chip ID.
  - LNB: IF level with 15 and 20 dB pads (desense check), LNB gain, neck diameter and waveguide ID before building the horn. HF: HF+ ppm; Boni-Whip housing length; balun DCR and S21 at 40-500 kHz.
  - Compliance: the egc-gate mixed-recording test (header-level discard), and the DSC, SITOR and WEFAX allow-list tests on mixed recordings.
  - Lime, if kept: riser link at 8 GT/s x1 with zero AER errors over 60 min; zero limeTRX losses during an LRPT+HRPT pass; measured VCC_5V_PERI ≤14 W; T7 floor rise at 1.7/2.2 GHz ≤1 dB; FIFO 10 vs SCHED_OTHER nice -20 for lime:Rx0.
  - Questions for the user at the phase end: the region; confirmation of the HF-loop removal; acceptance of the small rigid whips and helices; whether the Lime (S-band, 56 MHz NPU survey) is wanted by 1 Dec; whether a home-base x86 PC with a GPU exists; whether the USCG-run NWS WEFAX stations are allowed.
- **Confidence:** medium

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

