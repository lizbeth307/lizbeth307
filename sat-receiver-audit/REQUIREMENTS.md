# User requirements (consolidated 18 Oct 2026; governing input for every later phase)

Project: a handheld, standalone (no phone), RECEIVE-ONLY satellite receiver that is also a complete portable radio laboratory. The user wants maximum effort and full agent scale, objective decisions that weigh these wishes, and a finished, theoretically working stack with a final schematic and assembly instructions in files.

Hard rules
- Receive-only on air. Signal-generating instruments (VNA, generators, noise sources) are conducted bench tools only.
- No decoding of private-communications content (Iridium/Inmarsat/Orbcomm user traffic, Starlink user data) and no receive chains aimed at military communications; generic SDR frequency coverage is fine.
- Compute stays: Radxa Dragon Q6A (no alternative search for it).
- No dishes of any size.
- Antennas allowed: patch and chip antennas, plus antennas that fold/collapse into a small size (prefer every piece <= 20-23 cm, at most about 35 cm); deployed size may be larger.
- NO loop antennas of any kind: the HF active loop and everything for it, and the 20 cm / 12 cm VHF loops for Meteor, were removed by the user. Meteor LRPT uses the foldable telescopic V-dipole.
- The user is not in Ukraine and has not named a country: use world prices (manufacturer, AliExpress, EU/US shops); Ukrainian prices only as a reference.
- The device determines its own location automatically (GNSS + plausibility gate + fallbacks); no city tables.

Functional wishes
- Display: bright and high quality, ideally above Full HD. Objective audit result: a bonded 7in FHD 2000-nit panel (Wisecoco, conditional on bonding + USB-HID touch confirmation; fallback 4D Systems 1000-nit bonded) beats dim above-FHD kits; above-FHD only as a Midas 1200x1920 bring-up project.
- Full radio lab: instruments (VNA, spectrum analyzer, noise source, GPSDO/reference, power meter, near-field probes, attenuators, loads), RF switch and filter/LNA banks, extra receive capabilities (HF, LF/VLF time signals, ADS-B, AIS, radiosondes, broadcast, radio-astronomy basics), lab software, bench tools.
- HF receiver (keep), with a small foldable NON-loop antenna.
- NPU training system ON THE SPECTRUM: detect and classify signals on the waterfall; the user teaches it by marking signals; on-device few-shot learning plus home-base training; INT8 for QAIRT 2.42.
- One ideal touch MENU system through which every lab function is easy to use (gloves, sun, one hand, robust).

Process the user asked for (pipeline)
1. Finish all research. 1b. Agents research and verify the report I keep writing (minute-log.md, summaries.md, extra-studies.md, final/*.json).
2. Final checks (integration + completeness, then sourcing). 3. Consolidated STACK.md. 4. Full re-research of the whole stack at maximum agent scale.
5. Cheapest analogs that are NOT worse in quality or performance for every part EXCEPT the Q6A and the antennas, with adversarial verification.
6. Re-verify the stack with the analogs. 7. Complete schematic (block, power, RF, wiring/pinout), placement and mechanical drawing (SVG), software install plan, assembly and test instructions as files in sat-receiver-audit/build/.
- Per-minute summaries are not shown to the user; they are kept in sat-receiver-audit/minute-log.md.
- The user is asleep and delegated all remaining decisions: decide objectively, weighing these wishes; report at phase ends.

Decisions I made under the delegation after P1 (18 Oct 2026; revisit if the user objects)
- "No loops" also excludes H-field (small shielded loop) near-field probes and the AS3935 ferrite-coil lightning sensor by default; only E-field near-field probes are used. Trade-off accepted: the Airspy HF+ with a wire (feed point 5-10 m from the handheld) will often be limited by local noise.
- Field/QUIET mode: rfkill block wlan AND bluetooth; Pinecil IronOS Bluetooth = Off; FNB58 Std (no radio).
- Universal Radio Hacker (URH) is rejected (archived; record-and-send and attack features). The Artemis/sigidwiki database is used for identification only: a match to a military or government entry is logged as out of scope and not recorded, analysed, annotated or decoded further.
- NPU class policy gate: no radar, drone/FPV/RC link, EW/jammer, military, emitter-fingerprint or private-content classes; voice is spectrogram-only; decoder payloads are never stored.
- The radio-lab core kit follows the value verifier: Bodnar Mini GPSDO moves to extended (GNSS-SDR + PPS give ppm for free), no duplicate OSL kits, no AD8318 in core.
