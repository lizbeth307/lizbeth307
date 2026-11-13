# Звіт посадки механічної моделі SR-RX-v2.1

Згенеровано `mechanical/build.py` (params a96d409b1d6c); не редагувати вручну. **MODEL FIT ONLY:** це перевірка конвертів і даних з даташитів, а не примірка деталей. Фізичні ворота посадки, ущільнення, тепла й падіння лишаються OPEN.

## Габарит

| | модель | D15 |
|---|---|---|
| Ш x В x Г, мм | 230 x 163.8 x 70.08 | 222.5 x 137.5 x 57.5 |
| об'єм, L | 2.64 | 1.76 |
| поверхня, m² | 0.1305 | 0.1026 |
| лице, m² | 0.0377 | 0.0306 |
| над поясом шва, мм | 233.8 x 167.6 x 70.08 | — |
| мішок 23 x 30 см (W+D ≤ 300, H+D ≤ 230; D — глибина закритого пристрою з усіма виступами, 102.1 мм) | 335.9 / 269.7: FAIL (model): charge on a non-flammable surface instead (STACK 5.8 fallback) | — |

Глибина закритого пристрою (козирок складено, штекери вийнято), z від задньої зовнішньої грані:

- strap lugs and tunnels: z -6
- tripod plinth: z -5
- T7 holder: z -14
- T7 gland outside (assumption): z -15
- front face: z 70.08
- hood hinge knuckles (hood folded on them): z 76.08
- main knob: z 87.08
- volume knob (Adafruit 2055): z 83.58

Разом z -15…87.08; без тримача T7 — 102.1 мм. Не враховано: GX16 cap, SMA/F/BNC caps and screw heads on the T7 holder are not counted (parts not chosen); side-face parts (RX2/REF IN bulkheads, the J551 M8 receptacle 7.5 mm proud of the right face) are not in W/H.

## Підсумок

- зіткнень конвертів: 0; поза внутрішнім об'ємом: 0
- правила: FAIL 0, OPEN 13 (OPEN = потрібна обрана або виміряна деталь)
- антенні деталі за правилом розміру: FAIL 0; площа плат (курт'ярди KiCad, деталі без роз'ємів джгутів): OPEN 2; з роз'ємами джгутів build/16: OPEN 0 (MODEL ESTIMATE, не в гейті; рішення — розбиття й розкладка плат)
- термоінтерфейси: FAIL 0, OPEN 3; ущільнення: PASS (model)
- звірка з STEP постачальника: PASS (model vs vendor STEP)
- перетини тіл B-rep (оболонки, пластина, кутники, РЧ-відсік, лоток) з конвертами: 0; деталі з кількох тіл («висячі» елементи): 0

## Правила (build/05 §6, STACK 5.8)

| ID | правило | значення, мм | межа | результат |
|---|---|---|---|---|
| R-UFS-LIME | UFS boss to the Lime pedestal (in the plate plane) | 30.7 | 30 | PASS (model) |
| R-UFS-REG | UFS boss to the regulator bond zones of the PWR board | 43.3 | 30 | PASS (model) |
| R-IP2368 | IP2368 board to the battery compartment | 85.2 | 10 | PASS (model) |
| R-ENC | PEC11R bushing stack (O-ring + boss wall + washer + nut) | 6.1 | 6.5 | PASS (model) |
| R-KEYS | button caps, edge-to-edge gap (pitch 22: STACK allows 22-25 when the face height permits) | 10 | 7 / 13 | PASS (model) |
| R-TRIPOD | captive 1/4-20 nut pocket: outer wall <= 1.0, 11.3 AF, >= 3 mm behind the nut | 1 / 11.3 / 3 |  | PASS (model) |
| R-SMA-THREAD | per panel port: thread left for mating after the 4.5 mm wall (ASA 2.5 + Al angle 2.0), washer and nut >= 3 full threads (1/4-36: 3 x 0.706; 3/8-32: 3 x 0.794) | {'P1': 'OPEN: washer thickness not drawn: 2.32 mm left for it after the nut and 3 threads', 'P2': 'OPEN: washer thickness not drawn: 2.48 mm left for it after the nut and 3 threads', 'P3': 'OPEN: washer thickness not drawn: 2.48 mm left for it after the nut and 3 threads', 'P4': 'PASS (model): 3.6 mm left >= 2.38 (3 x 0.794); inside, for the W402 F plug: long side (min) - wall - washer - nut (max); the 7.6 short side outside is free for W401', 'P5': 'OPEN: drawing not readable: https://www.amphenolrf.com/en-us/assets/file/4065787441/ 2026-11-07 403 (distributor copies 403 or timeout, parts.json amphenol_242181); hole 9.7 is the typical 3/8-32 bulkhead value, the panel end, thread length and nut stay TBD (R-BULKHEAD-NUTS, R-SMA-THREAD)', 'P6': 'OPEN: washer thickness not drawn: 2.48 mm left for it after the nut and 3 threads', 'P7': 'PASS (model): 3.25 mm left >= 2.12 (3 x 0.706); outside: thread (min) - wall - items 5 + 6 (max); the seal sits at the flange inside', 'P8': 'OPEN: washer thickness not drawn: 2.48 mm left for it after the nut and 3 threads', 'RX1': 'OPEN: nut and washer not drawn: 4.58 mm left for both after 3 threads (1/4-36 sets read: Taoglas p.11 items 5 + 6 up to 3.35, Samtec 2.5)', 'RX2': 'OPEN: nut and washer not drawn: 4.58 mm left for both after 3 threads (1/4-36 sets read: Taoglas p.11 items 5 + 6 up to 3.35, Samtec 2.5)', 'REF_IN': 'OPEN: nut and washer not drawn: 4.58 mm left for both after 3 threads (1/4-36 sets read: Taoglas p.11 items 5 + 6 up to 3.35, Samtec 2.5)'} | 3 x pitch; wall 4.5 | OPEN: P1, P2, P3, P5, P6, P8, RX1, RX2, REF_IN (thread or hardware not drawn, or part not read); PASS (model): P4, P7 |
| R-BULKHEAD-NUTS | nut, washer or connector body of every panel bulkhead inside the wall: an envelope from the part's drawing in the envelope check (nut.*: clear of the RF-bay walls, modules and structure) | {'P1': 'd 9.24 x 3.40 deep: connector body hex inside, nut outside (adamtech_ca_dkca1_305l5)', 'P2': 'd 9.24 x 3.60 deep: connector body hex inside, nut outside (taoglas_cab718)', 'P3': 'd 9.24 x 3.60 deep: connector body hex inside, nut outside (taoglas_cab718)', 'P4': 'd 12.70 x 7.30 deep: washer, nut and the long side inside (cinch_vfa340)', 'P5': 'no envelope: drawing not readable: https://www.amphenolrf.com/en-us/assets/file/4065787441/ 2026-11-07 403 (distributor copies 403 or timeout, parts.json amphenol_242181); hole 9.7 is the typical 3/8-32 bulkhead value, the panel end, thread length and nut stay TBD (R-BULKHEAD-NUTS, R-SMA-THREAD)', 'P6': 'd 9.24 x 3.60 deep: connector body hex inside, nut outside (taoglas_cab718)', 'P7': 'd 10.20 x 3.40 deep: connector body inside, nut outside (taoglas_mhf1_sma_wp)', 'P8': 'd 9.24 x 3.60 deep: connector body hex inside, nut outside (taoglas_cab718)', 'RX1': 'd 10.20 x 3.40 deep: connector body inside, nut outside (taoglas_cab01075)', 'RX2': 'd 10.20 x 3.40 deep: connector body inside, nut outside (taoglas_cab01075)', 'REF_IN': 'd 10.20 x 3.40 deep: connector body inside, nut outside (taoglas_cab01075)', 'J551': 'd 12.60 x 9.50 deep: collar, rear body and lead bend inside, nut outside (binder_76_6618_1111)', 'LAB_BUS': 'd 16.86 x 10.80 deep: nut (corners) and rear thread with solder cups (kinghelm_gx12_6p)'} |  | OPEN: no inner envelope for P5 (drawing not read); body OD or length not dimensioned, envelope reserve for P1, P7, RX1, RX2, REF_IN |
| R-PWR-PADS | PWR thermal-pad zones clear of the screw keep-outs (margin, worst pair) | 0.5 | 0 | PASS (model) |
| R-HOLE-EDGE | plate holes: centre-to-edge distance minus the hole diameter (worst hole) | 0.1 | 0 | PASS (model) |
| R-CLINCH-EDGE | self-clinching nut/standoff: hole centre to the nearest plate edge or window (worst hole) | 6 | 6 | PASS (model) |
| R-SEAM-HOLES | closure insert holes inboard of the seam groove (wall left between hole and groove, worst boss) | 0.9 | 0.9 | PASS (model) |
| R-VENT-SEAT | vent seats: threaded hole >= 4.0 mm, or 2.0-3.5 mm through hole with the nut | {'V1': 4.0, 'V2': 4.0} | {'threaded': 4.0, 'through': [2.0, 3.5]} | PASS (model) |
| R-VENT-REACH | space behind each vent seat minus the thread reach (worst vent) | 5.88 | 0.5 | PASS (model) |
| R-PANEL-FLAT | side-face cut-outs on the flat face and clear of the seam belt (split plane +- 5.5 mm) | none |  | PASS (model) |
| R-PWR-KEY | E-Switch PV6F240SS panel thickness at the power key (top wall) and at SW501 (hatch board 1.6 mm) | 2.5 / 1.6 | 1 / 10 | PASS (model) |
| R-PWR-KEY-NUT | PV6 panel nut inside the top wall (reserve nut.PWR_KEY) and the key body clear of the HDMI board, the display and its clamp plates, the top Al angle and the plate (the nut inside the plate notch), >= 0.5 | {'key_x': 155.5, 'key_z': 50.0, 'nut_reserve': [22.0, 3.5], 'clear_mm': {'body-display': 2.58, 'body-display_clamp.3': 0.58, 'body-hdmi_board': 1.3, 'body-plate.main': 1.5, 'nut-angle.top.plate': 0.5, 'nut-angle.top.wall': 0.5, 'nut-display_clamp.3': 1.05, 'nut-front_wall': 6.58, 'nut-hdmi_board': 0.8}, 'worst': ['nut-angle.top.plate', 0.5], 'in_plate_notch': True} | 0.5 | OPEN: the nut is not dimensioned (PV6 and PV2 datasheets; DigiKey PV2PV3PV6HEX16 'HEX NUT FOR PV2 SERIES'; parts.json pv6_button nut_src): the reserve D22 x 3.5 (assumption) at x 155.5 / z 50 clears everything by >= 0.5 (worst nut-angle.top.plate 0.50) inside the plate notch, and the key body no longer touches the plate; measure the received nut at incoming inspection: a nut wider than the reserve needs the top Al angle notched or the key moved |
| R-PLATE-SLOTS | plate harness slots inside the outline with a web >= 1.5 mm to the outline and to every other opening (worst slot) | 1.5 | 1.5 | PASS (model) |
| R-PLATE-SLOT-FILL | harness bundle through each plate slot (wire areas / 0.6 + ribbon stack) inside the opening left by the edge trim (edging essentra_mgs_2_01 base 1.397 per edge, tape 0.1); ribbon, stack and largest wire fit the inner size; loose wires pack as round wires beside / on the ribbon; edging legs (2.54 onto each face) clear | {'SL1': {'opening_mm': [27.5, 4.4], 'trim': {'bottom': 'grommet', 'top': 'tape', 'left': 'tape', 'right': 'tape'}, 'inner_mm': [27.3, 2.9], 'inner_mm2': 79.3, 'wires': 30, 'loose_wires': 3, 'wires_per_awg': {'26': 3, '28': 27}, 'wire_area_mm2': 2.8, 'ribbon': {'segment': 'S01', 'w_mm': 25.4, 'stack_mm': 1.78, 'conductors_in_build16': 27}, 'bundle_need_mm2': 49.9, 'fill_of_inner': 0.63, 'largest_wire_mm': 1.09, 'packing': {'regions_mm': [[1.9, 2.9], [25.4, 1.12]], 'method': 'round wires, next-fit decreasing shelves, no nesting (beside the ribbon, then on it)', 'unplaced': 0}, 'legs_clear': 'yes', 'result': 'PASS (model)'}, 'SL2': {'opening_mm': [18.0, 8.2], 'trim': {'bottom': 'tape', 'top': 'grommet', 'left': 'tape', 'right': 'tape'}, 'inner_mm': [17.8, 6.7], 'inner_mm2': 119.3, 'wires': 61, 'loose_wires': 61, 'wires_per_awg': {'18': 4, '20': 8, '24': 24, '26': 25}, 'wire_area_mm2': 67.3, 'ribbon': None, 'bundle_need_mm2': 112.2, 'fill_of_inner': 0.94, 'largest_wire_mm': 1.88, 'packing': {'regions_mm': [[17.8, 6.7]], 'method': 'round wires, next-fit decreasing shelves, no nesting', 'unplaced': 0}, 'legs_clear': 'yes', 'result': 'PASS (model)'}, 'SL3': {'opening_mm': [5.5, 11.5], 'trim': {'bottom': 'tape', 'top': 'tape', 'left': 'tape', 'right': 'grommet'}, 'inner_mm': [4.0, 11.3], 'inner_mm2': 45.2, 'wires': 17, 'loose_wires': 17, 'wires_per_awg': {'20': 2, '24': 8, '26': 7}, 'wire_area_mm2': 16.2, 'ribbon': None, 'bundle_need_mm2': 27.0, 'fill_of_inner': 0.6, 'largest_wire_mm': 1.57, 'packing': {'regions_mm': [[4.0, 11.3]], 'method': 'round wires, next-fit decreasing shelves, no nesting', 'unplaced': 0}, 'legs_clear': 'yes', 'result': 'PASS (model)'}} | bundle inside the trimmed opening | PASS (model): SL1 49.9 <= 79.3 mm2 (0.63 of the inner opening 27.3 x 2.9); SL2 112.2 <= 119.3 mm2 (0.94 of the inner opening 17.8 x 6.7); SL3 27 <= 45.2 mm2 (0.6 of the inner opening 4 x 11.3); loose wires pack beside / on the ribbon; edging legs clear of the envelopes, the structure and the plate-hole footprints |
| R-PWR-MODULES | no purchased module on a custom board (W2 MECH-7: SHRINK-2 replaced the Pololu U107/U108) | None | 4.5 | PASS (model): no module on a board; the converters are board parts (partition height rule); the reserved blocks CONV_LAB5, CONV_SYS12, FUSE_F103, FUSE_F201, RPP are in the graph as real parts (GR-5A), so their heights are the partition height rule's (pcb/partition-spec.json heights.by_mpn) |
| R-COOLER-A | cooler A: Cu block inside the 32 x 31 keep-in and over SoC + LPDDR5 (cover margin >= 0.5); fan face >= the keep-in minimum and above the 40-pin and 2x2 headers | {'cover_margin': 0.97, 'fan_face_above_board': 10.5, 'tallest_header': 9.65} | {'cover_margin': 0.5, 'fan_face_above_board': 10.0} | PASS (model) |
| R-VENT-FOAM | battery vent: the thread ends in the 3 mm foam layer, so the foam has a hole >= thread d + 0.5 at the vent | {'V2': 13.0} | 12.5 | PASS (model) |
| R-HDMI-ROUTE | HDMI FPC route Q6A to the Wisecoco input: adapter, fold, ferrite, insert and run envelopes in the envelope check without a conflict; each flex covers its centreline with slack 0-40 mm; flex width through the ferrite slot and the plate notch (bare flex thickness <= the slot height once measured) | {'segments': {'FLEX1': {'part': '3560', 'flex_mm': 100.0, 'centreline_mm': 73.8, 'slack_mm': 26.2, 'folds': 2}, 'FLEX2': {'part': '3560', 'flex_mm': 100.0, 'centreline_mm': 83.5, 'slack_mm': 16.5, 'folds': 1}}, 'flex_w': 10.0, 'ferrite_slot': [11.5, 0.5], 'flex_bare_t': 'not published (measure)', 'notch': [211.0, 26.5, 15.5, 7.0], 'envelopes': 11, 'folds': 3, 'harness_near': {'nearest_centreline': ['S02', 'hdmi_route_front_rise', 0.5], 'bundle_overlaps': 35, 'segments': ['S02', 'S03', 'S10', 'S15', 'S24', 'S25', 'S30'], 'envelopes': ['hdmi_fpc_disp', 'hdmi_route_front_flat', 'hdmi_route_front_rise'], 'worst': ['S02', 'hdmi_route_front_rise', 6.52]}} |  | PASS (model): Adafruit 3550 on the Q6A receptacle, flex 1 3560 (26.2 mm slack) with the WE-FLAT 74278011 ferrite under the LAB BUS nut, through the plate notch to the HDMI_INSERT reserve right of the BMS, flex 2 3560 (16.5 mm slack) up the strip and along y 78.65-88.65 to the Adafruit 3548 in the Wisecoco input; 3 45-degree folds; labelled assumptions: 3550 axis from the product photos (3550 or 3549 by the receptacle side), flex thickness 0.5 and bend radius 2 not published, insert reserve size, Wisecoco HDMI input at the lower end of the board's right edge (STACK D5: measure the received board); only the flex width is checked against the ferrite slot: the bare flex must be <= 0.5 thick for the 11.5 x 0.5 (+0.5/-0) slot (thickness not published: measure, OPEN); harness bundles are centrelines in the envelope check (R-ROUTE-CLEAR): the nearest, S02, runs 0.5 mm from hdmi_route_front_rise; with bundle_od_mm / 2 about the centreline 35 route pieces of S02, S03, S10, S15, S24, S25, S30 reach into hdmi_fpc_disp, hdmi_route_front_flat, hdmi_route_front_rise (worst S02 6.52 mm into hdmi_route_front_rise): the drops must move clear of flex 2, OPEN for the harness routes; link, EMI of the wrapped flex and the folds stay bench OPEN |
| R-PPS-LEN | PPS path Q6A J20.7 -> LC76G: harness length <= 200 mm (STACK 5.2 'UART7/PPS wiring <= 20 cm'; E3 J301 note) | {'via_segments_mm': 301, 'branch_mm': 158, 'branch_max_mm': 182} | 200 | PASS (model): S01+S25 = 301 mm > 200: decision (build/15 W2 MECH-1) — PPS + UART6 + GND branch off the S01 ribbon at the Q6A end and run directly to the LC76G in the rear layer (harness only, E3 nets unchanged; build/15 W2 MECH-1); branch PPS = 158 mm; worst case 182 mm with the bounded provisional ends (+23.1 mm: J20 pin-1 orientation not read (no pin-1 mark on J20 in the Radxa placement map V1.21, read 2026-11-07): take-off at the centre of the S01 socket, while J20.7 (column 4 of 20, 2.54 pitch) sits 16.5 mm to one side of it: +/-16.5 mm on the branch; P1 (MX1.25) position read on the Waveshare outline drawing (parts.json lc76g), its height inside the 13.1 mm reserve is not (module height not read): end at mid-height, +/-6.6 mm) <= 200 |
| R-ROUTE-CLEAR | harness route centrelines (mechanical.json harness_routes) clear of every envelope, keep-clear reserve and structure part; plate and RF-bay wall only through openings | {'routed': 40, 'clear': 39, 'provisional_end': 39, 'no_route_unplaced_end': [], 'external': ['S33', 'S41'], 'crossing': ['S26']} |  | OPEN (end provisional): every routed centreline clears the envelopes and structure; 39 of 40 routes end on a board edge zone (header refs named, positions TBD until the board placement) or at a module without an envelope; no route yet (end not placed): none; provisional routes crossing a solid: S26 |
| R-P7-PIGTAIL | W407 P7 bulkhead -> LC76G IPEX: pigtail lower length (nominal - tolerance) - coax route >= 30 mm slack | {'route_mm': 204, 'pigtails': [{'mpn': 'CAB.01028', 'length_mm': 200.0, 'tol_mm': 6.0, 'slack_mm': -10.0, 'fits': False}, {'mpn': 'CAB.01029', 'length_mm': 250.0, 'tol_mm': 7.5, 'slack_mm': 38.5, 'fits': True}]} | 30 | PASS (model): route 204 mm (bulkhead body to the IPEX plug, no service loops); CAB.01029 250 - 7.5 mm leaves 38.5 mm >= 30; CAB.01028 200 mm leaves -10 mm |
| R-HDR-HEIGHT | board-side harness headers (build/16 §4) inside the board height limit, or in a computed height zone (component side) / rear zone; heights mated (header + plug) where read, else the header body (labelled); the wire exit beyond the plug is not included (wire TBD, AI-WIRE-PTFE) | {'above_limit': ['J104 MF_top 17.27 mated', 'J109 PH_top 8 mated', 'J110 PH_top 8 mated', 'J111 PH_top 8 mated', 'J112 PH_top 8 mated', 'J113 PH_top 8 mated', 'J114 MF_top 17.27 mated', 'J115 MF_top 17.27 mated', 'J203 PHD_top 8.8 mated', 'J205 MF_top 17.27 mated', 'J206 MF2_top 17.64 mated', 'J506 PH_top 8 mated', 'J507 PH_top 8 mated', 'J304 IDC_top 9.1 body', 'J305 MF_top 17.27 mated', 'J306 PHD_top 8.8 mated', 'J307 PHD_top 8.8 mated', 'J314 MF_top 17.27 mated'], 'height_not_read': ['J105', 'J106', 'J107', 'J108', 'J313'], 'alternative_fits': ['J305', 'J314'], 'alternative_fits_no_zone': ['J104', 'J114', 'J115', 'J205'], 'body_height_only': {'PHD_side': ['J202'], 'IDC_top': ['J304']}} | {'PWR': 4.5, 'PWR_B': 5.5, 'RF': 5.5, 'CTRL': 5.5, 'ENC': 6.5} | OPEN: GR-3 decides (header orientation, board side or board): 18 headers above their board limit (J104 MF_top 17.27 mated, J109 PH_top 8 mated, J110 PH_top 8 mated, J111 PH_top 8 mated, J112 PH_top 8 mated, J113 PH_top 8 mated, J114 MF_top 17.27 mated, J115 MF_top 17.27 mated, J203 PHD_top 8.8 mated, J205 MF_top 17.27 mated, J206 MF2_top 17.64 mated, J506 PH_top 8 mated, J507 PH_top 8 mated, J304 IDC_top 9.1 body, J305 MF_top 17.27 mated, J306 PHD_top 8.8 mated, J307 PHD_top 8.8 mated, J314 MF_top 17.27 mated); as right-angle Micro-Fit (MF_ra 6.98 mm mated) 2 fit (J305, J314), 4 fit no zone (J104, J114, J115, J205); judged on the header body because the mated height is not read: PHD_side (J202); IDC_top (J304); 5 heights not read |
| R-BOTTOM-PITCH | bottom-face port row: outer flange or inner nut radius of each port + 1 mm <= centre distance (re-space inside x 163-213 if it fails) | {'USB_C_IN-LAB_USB_A': '17.0 mm apart; OPEN: USB_C_IN, LAB_USB_A not modelled', 'USB_C_IN-LAB_BUS': '17.6 mm apart; OPEN: USB_C_IN not modelled', 'USB_C_IN-AUDIO_3V5': '33.3 mm apart; OPEN: USB_C_IN, AUDIO_3V5 not modelled', 'LAB_USB_A-LAB_BUS': '34.3 mm apart; OPEN: LAB_USB_A not modelled', 'LAB_USB_A-AUDIO_3V5': '28.0 mm apart; OPEN: LAB_USB_A, AUDIO_3V5 not modelled', 'LAB_BUS-AUDIO_3V5': '42.2 mm apart; OPEN: AUDIO_3V5 not modelled'} | 1 | OPEN: USB_C_IN, LAB_USB_A, AUDIO_3V5 not modelled (mechanical.json bottom_face '_tbd_reason'); read but not placed: PX0845/A (hex 42) needs 22 mm + the neighbour radius to each neighbour, more than the 17 mm row pitch |
| R-POD-WALL | S-band pod: bulkhead panel range, gland thread through wall + locknut, vent through-hole range against the pod wall (worst case) | {'RF_IN': 'PASS (model): wall 3.94 <= panel max 6.35; end wall not dimensioned: upper bound (outside - inside length) / 2', 'RF_OUT': 'PASS (model): wall 3.94 <= panel max 6.35; end wall not dimensioned: upper bound (outside - inside length) / 2', 'PWR': 'PASS (model): thread 8 - wall 3.94 - locknut 3 = 1.06 >= 0 (locknut fully on the thread); end wall not dimensioned: upper bound (outside - inside length) / 2', 'VENT': 'PASS (model): wall 3.00 in the through-hole range 2-3.5; side wall, Hammond 1554U section B-B'} |  | PASS (model); the end walls are not dimensioned (upper bound used) |
| R-PWR-POCKETS | plate relief pockets under PWR-A (M-07): bottom-part pockets PB* (W2 MECH-7) and a pocket >= 1 mm under every PWR-A THT pad group (pin field + 1 mm) outside them; polyimide film in every pocket | {'PB1': 'PWR-A bottom side: 7.00 x 17.00 x 1 deep at x 6.00..13.00, y 50.50..67.50; 3.8 mm to the nearest plate hole, 2.0 mm to the nearest bond zone', 'PB2': 'PWR-A bottom side: 6.00 x 13.00 x 1 deep at x 136.00..142.00, y 50.50..63.50; 3.8 mm to the nearest plate hole, 2.0 mm to the nearest bond zone', 'PB3': 'PWR-A bottom side: 40.00 x 8.00 x 1 deep at x 6.00..46.00, y 67.50..75.50; 3.8 mm to the nearest plate hole, 2.0 mm to the nearest bond zone', 'PB4': 'PWR-A bottom side: 74.00 x 5.10 x 1 deep at x 58.00..132.00, y 67.50..72.60; 3.8 mm to the nearest plate hole, 2.0 mm to the nearest bond zone', 'PB5': 'PWR-A bottom side: 5.00 x 28.00 x 1 deep at x 6.00..11.00, y 75.50..103.50; 8.5 mm to the nearest plate hole, 2.0 mm to the nearest bond zone', 'PB6': 'PWR-A bottom side: 9.60 x 5.50 x 1 deep at x 6.00..15.60, y 103.50..109.00; 3.9 mm to the nearest plate hole, 2.0 mm to the nearest bond zone', 'PB7': 'PWR-A bottom side: 20.40 x 5.50 x 1 deep at x 27.60..48.00, y 103.50..109.00; 3.9 mm to the nearest plate hole, 2.0 mm to the nearest bond zone', 'PB8': 'PWR-A bottom side: 5.00 x 18.00 x 1 deep at x 6.00..11.00, y 109.50..127.50; 9.6 mm to the nearest plate hole, 2.0 mm to the nearest bond zone', 'PB9': 'PWR-A bottom side: 42.00 x 6.00 x 1 deep at x 6.00..48.00, y 127.50..133.50; 3.9 mm to the nearest plate hole, 2.0 mm to the nearest bond zone', 'PB10': 'PWR-A bottom side: 9.60 x 5.00 x 1 deep at x 6.00..15.60, y 133.50..138.50; 3.8 mm to the nearest plate hole, 8.0 mm to the nearest bond zone', 'PB11': 'PWR-A bottom side: 20.40 x 5.00 x 1 deep at x 27.60..48.00, y 133.50..138.50; 3.8 mm to the nearest plate hole, 8.0 mm to the nearest bond zone', 'PB12': 'PWR-A bottom side: 10.40 x 7.00 x 1 deep at x 27.60..38.00, y 138.50..145.50; 3.8 mm to the nearest plate hole, 13.0 mm to the nearest bond zone', 'PB13': 'PWR-A bottom side: 22.00 x 3.00 x 1 deep at x 16.00..38.00, y 145.50..148.50; 3.8 mm to the nearest plate hole, 20.0 mm to the nearest bond zone'} | {'depth_min': 1.0, 'plate_t': 2.0, 'web_min': 1.0, 'bond_land': 2.0} | OPEN: 13 bottom-part pockets PB1-PB13 (1830 mm2, 1 deep, web 1, >= 2 from every bond zone, outside the converter heat corridors and the plate-hole lands) are drawn (M-07); the PWR-A THT groups (radials, the Keystone 3568 holder of F102, the PWR-A harness headers: pcb/partition-budget.json candidates.<chosen> pwr_a_tht_pocket_items; W2 MECH-7: no Pololu rows any more, PK1/PK2 are deleted) whose pin fields lie outside the PB pockets, in a thermal_bond zone (the Gelid pad is cut there too), a land or a heat corridor get their own pocket at the PCB-PWRA-3 placement: OPEN until it exists (rule R-PWR-POCKETS prints the current count) (pcb/partition-budget.json candidates.shrink2 pwr_a_tht_pocket_items now: 23 items with 66 THT pads) |
| R-J551 | pod power receptacle J551 (binder M8): wall inside the data-sheet range, cut-out from the data sheet, inner envelope nut.J551 in the envelope check | {'face': 'right', 'y': 106.0, 'z': 30.0, 'wall': 2.5, 'range': [2.0, 6.5], 'hole_d': 10.1, 'proud_outside': 7.5, 'inner': [12.6, 9.5], 'leads_mm': 200.0} | {'wall': [2.0, 6.5]} | PASS (model): 2.5 mm ASA wall inside 2-6.5; inserted from inside (collar on the inner face), SW 11 nut outside, 7.5 mm proud of the right face; plain bore 10.1 (binder proposal 2: takes the M10x0.75 body with or without flats); anti-rotation with the flats proposal (9.1 across) OPEN until flats on this part's body are confirmed (the READS-E reading of the scale drawing names none) |
| R-FASTENER-STACKS | screw joints: under-head length window between the minimum engagement and the tip limit (generated/fastener-stacks.json) | {'CLOSURE': [15.5, 17.0], 'HATCH': [8.25, 9.75], 'T7_HOLDER': [14.0, 15.5], 'PLATE_PM1': [6.5, 8.0], 'PLATE_PM2': [6.5, 8.0], 'PLATE_PM3': [6.5, 8.0], 'PLATE_PM4': [6.5, 8.0], 'ANGLES': [3.53, 4.0], 'PWR_A-PLATE': [3.59, 4.06], 'PWR_B-STANDOFF': [4.66, 6.16], 'RF-STANDOFF': [4.6, 6.6], 'CTRL': [5.35, 5.6], 'ENC': [5.35, 5.6], 'UFS-BOSS': [4.5, 4.7], 'LIME-PEDESTAL': [5.0, 7.0], 'DISPLAY-CLAMP': [5.75, 6.0], 'INA228': [5.35, 6.1], 'HUB-5997': [5.35, 6.1], 'PACK-FUSE': [4.1, 9.6]} |  | OPEN: HATCH, PWR_A-PLATE, CTRL, ENC, Q6A-STANDOFF, Q6A-PLATE, UFS-BOSS, LIME-PEDESTAL, DISPLAY-CLAMP, IMU-CARRIER, IMU-LID, IMU-BOARD-STANDOFFS, IMU-TRIPOD, POD-LID, POD-PANEL, SWM-2813, VEML7700, PACK-FUSE, PWR-BOND, IP2368, FAN-NF-A4X10, BLOWER, HATCH-BOARD, POD-MODULES (thread depth not read, fixing or screw not chosen, or no ISO length in the window); PASS (model): CLOSURE, T7_HOLDER, PLATE_PM1, PLATE_PM2, PLATE_PM3, PLATE_PM4, ANGLES, PWR_B-STANDOFF, RF-STANDOFF, INA228, HUB-5997 |
| R-F101-ACCESS | F101 for storage (STACK: F1 out for more than 2-4 weeks): the PACK_FUSE carrier with the fuse facing the hatch opening needs carrier + Keystone 3568 + MINI body of free depth in the hatch bottom strip, and its place must leave the hatch access path to the keep-clear reserves behind it (USB-A plug bay) open; otherwise the seam is opened | {'place': [116.0, 40.0, 22.0, 16.5], 'free_depth': 11.65, 'stack': 17.77, 'stack_parts': {'carrier': 1.6, 'keystone_3568': 7.37, 'mini_fuse_body': 8.8}, 'access_path_to': ['usb_plug_bay']} | 17.77 | PASS (model, decision: seam): storage keeps the seam procedure, F101 is not reached through the hatch: facing the opening, the stack needs 17.77 mm (carrier 1.6 + Keystone 3568 7.37 + MINI body 8.8) against 11.65 mm in front of the USB-A plug bay; the place is the hatch access path to usb_plug_bay (the USB-A plug of the Q6A goes in through this strip, hatch.content); the rest of the hatch footprint is the hatch board (J502, J503) and the EDL key; F101 stays on the PACK_FUSE carrier beside the battery tray (envelope MECH-5) and comes out after the seam is opened (build/21 section 4 item 7, build/15 'Ущільнення') |
| R-P8-ACCESSORY | P8 external inline accessory (A403 -> A404 in the antenna line, ch4 bias through P8): module envelopes, chain and the parts still open | {'outside_enclosure': True, 'chain': ['J428 antenna feed (SMA input of A403)', 'A403 Flamingo+ FM #2', 'SMA male-male adapter from the LNA V2 package (A403 OUT -> A404 IN; assumption: both jacks SMA female, connector genders of A403/A404 not read, check at incoming inspection)', 'A404 RTL-SDR Blog Wideband LNA V2', 'coax A404 OUT -> P8 (W2 GR-2 net E4_RF_CH4; ch4 bias 4.3 V reaches A404 over it)'], 'modules': {'A403': [73.7, 30.6, 18.7], 'A404': None}, 'envelope': {'length': None, 'w': 30.6, 'h': 18.7}} |  | OPEN: A404: RTL-SDR Blog Wideband LNA V2: the maker's page https://www.rtl-sdr.com/product/rtl-sdr-blog-wideband-lna-bias-tee-powered/ (read 2026-11-07 with WebFetch) gives no dimensions and no connector genders; it lists '1x SMA male to SMA male adapter' in the package and 'Requires 3 - 5v bias tee power' (ch4 gives 4.3 V through P8, build/03 P8 row); length = A403 73.7 (reserve) + adapter + A404 (not read); box, adapters, cable and mounting items are SRC-2's (CC-27); sealing of the accessory box is OPEN (T-07); assembly order build/21 E9c |
| R-MODULE-MOUNTS | module fixing (mechanical.json module_mounts): insert hole + skin <= wall + boss, board face = envelope face, screw holes = the makers' board-file holes, rear-wall insert holes >= tripod_clear from the 1/4-20 nut pocket, the INA228 terminal wire side free of envelopes and harness bundles, 18 AWG inside the terminal range, this package's envelopes >= bundle OD / 2 + bundle_clear from other routes, plate standoff barrels clear of the envelopes; plate standoff holes in R-HOLE-EDGE / R-CLINCH-EDGE | {'hub_ch334f': {'screws': [{'c': [84.38, 41.54], 'skin_mm': 1.0, 'to_tripod_pocket_mm': 23.94}, {'c': [84.38, 56.78], 'skin_mm': 1.0, 'to_tripod_pocket_mm': 11.94}, {'c': [58.98, 41.54], 'skin_mm': 1.0, 'to_tripod_pocket_mm': 41.4}, {'c': [58.98, 56.78], 'skin_mm': 1.0, 'to_tripod_pocket_mm': 34.57}]}, 'ina228': {'screws': [{'c': [31.24, 62.26], 'skin_mm': 1.0, 'to_tripod_pocket_mm': 60.67}, {'c': [51.56, 62.26], 'skin_mm': 1.0, 'to_tripod_pocket_mm': 40.53}], 'rests': [{'c': [33.3, 53.48], 'skin_mm': None}, {'c': [49.3, 53.48], 'skin_mm': None}], 'terminal': {'wire_side': '+y', 'free_mm': 30.64, 'free_envelopes_only_mm': 34.3, 'limited_by': 'W407', 'need_mm': 8.0, 'awg_range': [16, 30], 'vin_awg': 18}}, 'swm_2813': {'pad': {'rect': [97.46, 44.0, 12.0, 14.0], 'seat_z': 4.5, 'tape': 1.0}}, 'veml7700': {'rests': [{'c': [109.84, 51.824], 'skin_mm': None, 'face_y': 160.1, 'tape': 1.0}, {'c': [130.16, 51.824], 'skin_mm': None, 'face_y': 160.1, 'tape': 1.0}, {'c': [109.84, 64.524], 'skin_mm': None, 'face_y': 160.1, 'tape': 1.0}, {'c': [130.16, 64.524], 'skin_mm': None, 'face_y': 160.1, 'tape': 1.0}], 'spigots': [{'c': [109.84, 64.524], 'd': 2.2, 'len': 2.0}, {'c': [130.16, 51.824], 'd': 2.2, 'len': 2.0}], 'pocket_skin_mm': 1.4, 'front_edge_to_wall_mm': 0.52}, 'bundle_clearance': {'hub_ch334f': {'route': 'S06', 'centreline_mm': 8.68, 'need_mm': 3.71}, 'ina228': {'route': 'W407', 'centreline_mm': 29.08, 'need_mm': 1.06}, 'veml7700': {'route': 'S29', 'centreline_mm': 24.41, 'need_mm': 1.5}, 't7_insert': {'route': 'S13', 'centreline_mm': 2.0, 'need_mm': 1.94}, 'pack_fuse': {'route': 'S02B', 'centreline_mm': 4.3, 'need_mm': 3.73}, 'pack_fuse_board': {'route': 'S40', 'centreline_mm': 1.6, 'need_mm': 1.5}, 'boni_a406': {'route': 'W407', 'centreline_mm': 1.28, 'need_mm': 1.06}}, 'plate_standoffs': {'pack_fuse': [{'c': [169.0, 14.1], 'nearest': 'plate.boss3', 'gap_mm': 0.99}, {'c': [169.0, 35.3], 'nearest': 'blower', 'gap_mm': 1.09}]}} |  | PASS (model): CH334F 4 x M2.5 and INA228 2 x M2.5 (+2 rests) into TC-M2,5x4 inserts in rear-wall bosses (hole 5 deep, skin 1, 11.94 from the tripod nut pocket >= 3), #2813 on a printed pad with acrylic foam tape (no mounting hole on the Pololu drawing), VEML7700 taped to 4 rests (+2 locating spigots) in a 1.1 mm pocket of the top wall (skin 1.4; no insert joint fits that wall), PACK_FUSE on 2 PEM SO-M2.5-6ZI (M-07 PF; barrels 0.99 from the nearest envelope); INA228 terminal wire side +y with 30.64 mm free of envelopes and harness bundles (limit: W407), 18 AWG inside 30-16 AWG (4UCON 19963; block identity inferred, confirm at incoming inspection); this package's envelopes keep bundle OD / 2 + 0.5 from the other route centrelines; torques coupon-defined (build/17 section 2); OPEN: boni_a406: fixing TBD (assumption, no drawing) |
| R-PWR-ZONES | PWR-A converters inside their thermal_bond zones (graph courtyards of the zone refs once GR-5A has placed them in the graph, else the budget block; each part turned 0 or 90 deg) | {'zone 3': {'zone_mm': [7, 39, 17, 24], 'basis': 'graph courtyards (GR-5A)', 'refs': {'U107': [4.9, 4.4], 'L102': [13.0, 10.5]}, 'footprints': {'U107': 'SR_RX_Custom:TI_RJR0014A_VQFN-HR-14_4x3.5mm', 'L102': 'Inductor_SMD:L_Bourns_SRP1038C_10.0x10.0mm'}, 'block_retired': 'CONV_SYS12', 'budget_still_lists_block': False, 'margin_mm': 6.5, 'arrangement': 'column along y'}, 'zone 4': {'zone_mm': [7, 73, 14, 14], 'basis': 'graph courtyards (GR-5A)', 'refs': {'U108': [5.9, 6.0]}, 'footprints': {'U108': 'SR_RX_Custom:TI_RDL0020A_B3QFN-20_5x5.5mm'}, 'block_retired': 'CONV_LAB5', 'budget_still_lists_block': False, 'margin_mm': 8.0, 'arrangement': 'row along x'}} | converter inside its zone | PASS (model): zone 3 17 x 24 holds U107 4.9 x 4.4 + L102 13 x 10.5 (graph courtyards, column along y, margin 6.50); zone 4 14 x 14 holds U108 5.9 x 6 (graph courtyards, row along x, margin 8.00); the power passives sit next to them (TI layout), positions at the PCB-PWRA-3 placement |
| R-PWR-BOTTOM | bottom-side parts of PWR-A: inside the plate pockets PB*, no taller than shim gap + pocket depth - polyimide film - clearance | {'pockets': 13, 'pocket_area_mm2': 1830.2, 'h_room_mm': 1.4, 'film_mm': 0.07, 'clearance_mm': 0.3, 'h_max_mm': 1.03, 'bottom_refs': 94, 'budget_raw_mm2': 496.2, 'budget_demand_1_8_mm2': 893.1, 'raw_fill': 0.271, 'ratio_1_8': 0.488, 'budget_bottom_usable_mm2': 3227.5} | {'h_max': 1.03, 'pocket_area_mm2': 1830.2} | OPEN: 94 bottom refs, courtyards 496.2 mm2 = 0.27 of the 13 PB pockets (1830 mm2; 893.1 at 1.8 fits, ratio 0.49); room 1.4 - film 0.07 - clearance 0.3 = h_max 1.03 mm; TBD per MPN: the heights of the bottom chip refs are not read (pcb/partition-spec.json candidates.shrink2.pwr_a_bottom.h_room_formula); PCB-PWRA-3 checks each against h_max; positions at the PCB-PWRA-3 placement |
| R-H-TRIM | rule H-TRIM: PWR-A parts <= zone_h_max under the PWR-B THT pin fields, pins trimmed to <= protrusion_max; clearance >= 0.5 (model gap) | {'pwr_a_face_z': 42.564, 'pwr_b_bottom_z': 47.564, 'protrusion_max': 1.0, 'zone_h_max': 2.7, 'clearance_mm': 1.3, 'spec_clearance_mm': 1.3} | 0.5 | OPEN: stack 47.564 - 1 - (42.564 + 2.7) = 1.3 mm clearance (model arithmetic, equal to pcb/partition-spec.json keepouts.h_trim); OPEN: the trimmed protrusion and the 1.3 mm clearance (stack 5.0 - protrusion 1.0 - zone part 2.7) are measured at proof-fit; PCB-PWRB-2 marks every PWR-B THT pin field for flush trim in its fab and assembly notes; if H-TRIM fails, F2-C fires (rule R-H-TRIM) |
| R-HDR-MATED | PWR-A headers under the display: mated top (PWR-A face 42.564 + header and plug) <= the path-2 channel floor 56.58 (display module back 60.58 - channel 4) | {'channel_floor_z': 56.58, 'pwr_a_face_z': 42.564, 'under_display_pass': ['J113', 'J507'], 'fails_as_specified': ['J104 MF_top 59.83', 'J114 MF_top 59.83', 'J115 MF_top 59.83', 'J205 MF_top 59.83', 'J206 MF2_top 60.2'], 'alternative_passes': ['J104', 'J114', 'J115', 'J205'], 'tbd': [], 'outside_display': ['J105', 'J106', 'J107', 'J108', 'J109', 'J110', 'J111', 'J112'], 'alternative_area_delta_mm2': {'J104': 69.0, 'J114': 44.1, 'J115': 44.1, 'J205': 44.1}, 'alternative_area_total_mm2': 201.3, 'fill_trigger': 0.6, 'pwr_a_margin_mm2': 35.0, 'budget': 'candidates.shrink2 PWR_A usable 7640.6, demand 4549.4', 'all_within_margin': False, 'largest_sets_within_margin': [], 'text': 'MF_ra adds PWR-A top courtyard area (J104 69, J114 44.1, J115 44.1, J205 44.1; total 201.3 mm2) against the 35 mm2 left below the fill trigger 0.60 (pcb/partition-budget.json candidates.shrink2 PWR_A: 0.60 x 7640.6 - 4549.4): MF_ra on all of them would fire F2-C (pcb/partition-spec.json fallbacks F2-C); the largest sets within the margin: none; the others need a place outside the display or F2-C'} | 56.58 | OPEN: 2 pass (J113, J507); 5 fail as specified (J104 MF_top 59.83, J114 MF_top 59.83, J115 MF_top 59.83, J205 MF_top 59.83, J206 MF2_top 60.2), as the right-angle Micro-Fit 43650 (MF_ra) J104, J114, J115, J205 pass; MF_ra adds PWR-A top courtyard area (J104 69, J114 44.1, J115 44.1, J205 44.1; total 201.3 mm2) against the 35 mm2 left below the fill trigger 0.60 (pcb/partition-budget.json candidates.shrink2 PWR_A: 0.60 x 7640.6 - 4549.4): MF_ra on all of them would fire F2-C (pcb/partition-spec.json fallbacks F2-C); the largest sets within the margin: none; the others need a place outside the display or F2-C; no passing part read for J206 (TBD: a lower-mated part or a place outside the display); places outside the display, the longest run of each failing header's exit edge zone clear of the display footprint: J104 right 11.8 mm (enclosure y 38.5-50.3), J114 right 11.8 mm (enclosure y 38.5-50.3), J115 right 11.8 mm (enclosure y 38.5-50.3), J205 top 0.3 mm (enclosure x 6-6.3), J206 top 0 mm (shared with the other headers of that zone; positions at the PCB-PWRA-3 placement); outside the display footprint: J105, J106, J107, J108, J109, J110, J111, J112; the header family and orientation are GR's (build/16), the exit edge and position PCB-PWRA-3's |
| R-PWRB-EXIT | PWR-B edge zones: free room in front of the edge in the plug height band against the mated side-entry housing proud of the header face plus the bundle OD of the zone's segments; bundle clearance of each segment's leg to its first opening (header set-back and wire bend: PCB-PWRB-2 placement, proof-fit) | {'zones': [{'zone': 0, 'edge': 'right', 'span': [0, 35], 'headers': ['J201', 'J202'], 'families': ['PH', 'PHD'], 'band_z': [49.23, 54.23], 'room_mm': 2.0, 'nearest': 'blower', 'plug_proud_mm': 2.3, 'plug_proud_tbd': [], 'segments': ['S02'], 'bundle_od_max_mm': 14.04, 'bundle_clearance_mm': 0.5, 'legs': {'S02': {'bundle_od_mm': 14.04, 'pieces': 7, 'clear_mm': -7.02, 'nearest': 'PWR.r0'}}, 'set_back_min_mm': 14.84, 'verdict': 'room 2 mm to blower < housing proud 2.3 + bundle OD 14.04 (S02) + clearance 0.5 = 16.84 (bundle OD 14.04 > room 2: the bundle cannot turn in front of the edge): the header face sits >= 14.84 mm inboard of the board edge and the wires turn over the board (bend radius TBD); leg to the first opening, bundle (centreline + OD/2) against the envelopes: S02 reaches 7.02 into PWR.r0'}, {'zone': 1, 'edge': 'top', 'span': [58, 107], 'headers': ['J204', 'J207'], 'families': ['PH'], 'band_z': [49.23, 54.03], 'room_mm': 1.5, 'nearest': 'hdmi_board', 'plug_proud_mm': 2.0, 'plug_proud_tbd': [], 'segments': ['S04', 'S20', 'S21', 'S22', 'S35', 'S36'], 'bundle_od_max_mm': 3.51, 'bundle_clearance_mm': 0.5, 'legs': {'S04': {'bundle_od_mm': 3.51, 'pieces': 3, 'clear_mm': -1.0, 'nearest': 'hdmi_board'}, 'S20': {'bundle_od_mm': 1.75, 'pieces': 3, 'clear_mm': -0.12, 'nearest': 'hdmi_board'}, 'S21': {'bundle_od_mm': 1.75, 'pieces': 3, 'clear_mm': -0.12, 'nearest': 'hdmi_board'}, 'S22': {'bundle_od_mm': 2.15, 'pieces': 3, 'clear_mm': -0.32, 'nearest': 'hdmi_board'}, 'S35': {'bundle_od_mm': 1.75, 'pieces': 3, 'clear_mm': -0.12, 'nearest': 'hdmi_board'}, 'S36': {'bundle_od_mm': 1.75, 'pieces': 3, 'clear_mm': -0.12, 'nearest': 'hdmi_board'}}, 'set_back_min_mm': 4.51, 'verdict': 'room 1.5 mm to hdmi_board < housing proud 2 + bundle OD 3.51 (S04) + clearance 0.5 = 6.01 (bundle OD 3.51 > room 1.5: the bundle cannot turn in front of the edge): the header face sits >= 4.51 mm inboard of the board edge and the wires turn over the board (bend radius TBD); leg to the first opening, bundle (centreline + OD/2) against the envelopes: S04 reaches 1 into hdmi_board, S20 reaches 0.12 into hdmi_board, S21 reaches 0.12 into hdmi_board, S22 reaches 0.32 into hdmi_board, S35 reaches 0.12 into hdmi_board, S36 reaches 0.12 into hdmi_board'}, {'zone': 2, 'edge': 'bottom', 'exit': 'top', 'span': [90.0, 115.0], 'headers': ['J203', 'J506'], 'families': ['PH', 'PHD'], 'footprint_xy': [96.0, 38.5, 121.0, 50.3], 'face_z': 49.228, 'ceiling_z': 67.58, 'ceiling': 'front wall', 'mated_h_mm': {'PH': 8.0, 'PHD': 8.8}, 'plug_top_z': 58.028, 'segments': ['S02B', 'S23', 'S34'], 'bundle_od_max_mm': 6.47, 'bundle_clearance_mm': 0.5, 'legs': {'S02B': {'bundle_od_mm': 6.47, 'pieces': 6, 'clear_mm': 0.56, 'nearest': 'display', 'boss_clear_mm': 2.015, 'boss': [163.8, 46.0]}, 'S23': {'bundle_od_mm': 2.15, 'pieces': 6, 'clear_mm': 0.93, 'nearest': 'bms', 'boss_clear_mm': 1.283, 'boss': [163.8, 46.0]}, 'S34': {'bundle_od_mm': 3.45, 'pieces': 6, 'clear_mm': 0.27, 'nearest': 'bms', 'boss_clear_mm': 0.633, 'boss': [163.8, 46.0]}}, 'vertical_room_mm': 9.552, 'room_mm': 9.552, 'room_kind': 'vertical over the mated plugs (top entry)', 'plug_proud_mm': None, 'need_mm': 6.97, 'room_ok': True, 'verdict': 'vertical room 9.552 mm over the mated plugs (front wall z 67.58 - face 49.228 - mated 8.8) >= bundle OD 6.47 (S02B) + clearance 0.5 = 6.97; the wires rise from the plug tops (bend radius over the plugs TBD); legs, bundle (centreline + OD/2) against the envelopes: clear: S02B 0.56, S23 0.93, S34 0.27 mm; bundle surface to the display clamp bosses (whole route): S02B 2.015, S23 1.283, S34 0.633 mm'}]} | {'PH': 2.0, 'PHD': 2.3} | OPEN: zone 0 (right 0-35, J201, J202): room 2 mm to blower < housing proud 2.3 + bundle OD 14.04 (S02) + clearance 0.5 = 16.84 (bundle OD 14.04 > room 2: the bundle cannot turn in front of the edge): the header face sits >= 14.84 mm inboard of the board edge and the wires turn over the board (bend radius TBD); leg to the first opening, bundle (centreline + OD/2) against the envelopes: S02 reaches 7.02 into PWR.r0; zone 1 (top 58-107, J204, J207): room 1.5 mm to hdmi_board < housing proud 2 + bundle OD 3.51 (S04) + clearance 0.5 = 6.01 (bundle OD 3.51 > room 1.5: the bundle cannot turn in front of the edge): the header face sits >= 4.51 mm inboard of the board edge and the wires turn over the board (bend radius TBD); leg to the first opening, bundle (centreline + OD/2) against the envelopes: S04 reaches 1 into hdmi_board, S20 reaches 0.12 into hdmi_board, S21 reaches 0.12 into hdmi_board, S22 reaches 0.32 into hdmi_board, S35 reaches 0.12 into hdmi_board, S36 reaches 0.12 into hdmi_board; zone 2 (bottom 90-115, top entry J203, J506): vertical room 9.552 mm over the mated plugs (front wall z 67.58 - face 49.228 - mated 8.8) >= bundle OD 6.47 (S02B) + clearance 0.5 = 6.97; the wires rise from the plug tops (bend radius over the plugs TBD); legs, bundle (centreline + OD/2) against the envelopes: clear: S02B 0.56, S23 0.93, S34 0.27 mm; bundle surface to the display clamp bosses (whole route): S02B 2.015, S23 1.283, S34 0.633 mm; OPEN: PCB-PWRB-2 sets the header set-back from the board edge at its placement (at least the R-PWRB-EXIT set_back_min_mm of the zone, plus the bend radius, TBD) and the wire turn is checked at proof-fit (rule R-PWRB-EXIT) |
| R-PWR-STACK | mated PWR-A/PWR-B stack (W2 MECH-8, 6-layer boards): PWR-B bottom = PWR-A bottom + t(PWR) + B2B stack, and PWR-B top + hB <= the path-2 channel floor (module back - air_channel), at the contract thickness and over the order band of each board | {'plate_front_z': 40.5, 'bond_gap_mm': 0.4, 'pwr_a': {'t_mm': 1.664, 'layers': 6, 'bottom_z': 40.9, 'top_z': 42.564}, 'b2b_stack_mm': 5.0, 'partition_spec_stack_mm': 5.0, 'pwr_b': {'t_mm': 1.664, 'layers': 6, 'bottom_z': 47.564, 'bottom_z_from_stack': 47.564, 'top_z': 49.228, 'parts_top_z': 54.728}, 'stack_height_from_plate_mm': 14.228, 'channel_floor_z': 56.58, 'air_channel_mm': 4.0, 'channel_to_module_back_mm': 5.852, 'margin_mm': 1.852, 'margin_with_shared_t_mm': 1.98, 'shared_t_mm': 1.6, 'order_band_mm': {'PWR': [1.44, 1.76], 'PWR_B': [1.44, 1.76], 'margin_min_mm': 1.66, 'margin_max_mm': 2.3}, 'dz_mezz_mm': {'at_contract_t': 2.228, 'partition_spec_recorded': 2.1, 'partition_spec_dz': 4.08, 'dz_unchanged': True}, 'pwr_a_stud_window_mm': {'at_contract_t': [3.594, 4.064], 'at_band_ends': [[3.37, 3.84], [3.69, 4.16]], 'common_over_band': [3.69, 3.84]}} | 0 | PASS (model): PWR-A 40.9 + 1.664 + B2B 5 = PWR-B 47.564; PWR-B parts top 54.728 under the channel floor 56.58: margin 1.852 mm (1.98 with 1.6 mm boards); over the order band 1.44-1.76 mm of both boards the margin is 1.66-2.3 mm; finished thickness TBD at order, mated stack a proof-fit gate (OPEN) |
| R-TOOL-ACCESS | every closure, hatch and T7-holder screw: clear tool path (counterbore, then d 8.0 for 60 mm) from outside | CLOSURE_1: remove t7_holder first / CLOSURE_2: remove t7_holder first | no fixed solid in a tool path; removable parts only over closure screws | PASS (model) |
| R-TRIPOD-DISC | tripod plate disc d 50.0 about the 1/4-20: no solid prouder than the plinth face (5.0 mm) | none | plinth d 23.0, 5.0 proud | PASS (model) |

## РЧ-відсік: донгли V4L, розетки USB-подовжувачів і модулі LNA

Внутрішній розмір кришки 192.5 x 62.7 мм, зазор 0.5 мм; резерви: V4L 95 / 27 / 13 (listing), розетка на носійній платі 14.9 / 22 / 13 (wurth_614004190021), корпус LNA 73.7 / 30.6.

| варіант | розкладка | ряд, мм | висота, мм | запас ряду / висоти, мм | вміщується |
|---|---|---|---|---|---|
| (a) | two dongles with their sockets in one row, the LNA cases in a second row | 221.3 | 59.1 | -28.8 / 3.6 | ні |
| (b) (обрано) | LNA case + V4L + socket per row, two rows (LNA cases stacked at one end) | 185.1 | 62.7 | 7.4 / 0 | так |
| (c) | V4L + socket per row, two rows, LNA cases moved out of the bay | 110.9 | 55.5 | 81.6 / 7.2 | так; fits without growth, but the two cased LNA modules then need a shielded place outside the RF bay with new wall ports and seals: none in the model, so not chosen |

Не враховано: coax mating plugs at the module SMA ends (cable assemblies TBD, SRC-2): (b) leaves the row spare between the LNA case and the V4L SMA end for a right-angle plug; the lead paths beyond notches N2/N3 to the hub (Adafruit 5997, envelope MECH-5).

Результат: PASS (model): arrangement (b) 185.1 x 62.7 mm in 192.5 x 62.7; socket Wurth 614004190021 from its drawing; V4L reserve is the seller-listing maximum (measure at receipt)

## Термоінтерфейси (Gelid GP-Ultimate)

Gelid GP-Ultimate, compression 10%-30% over the design gap +- tolerance (upper limit: Gelid product page, parts.json)

| ID | де | середовище | зазор ± допуск, мм | прокладка | стиск | виріз, мм | результат |
|---|---|---|---|---|---|---|---|
| T-SOC | Q6A SoC (BGA1287) to the cooler-A Cu block, flat face | thermal paste or PTM7950 (never a pad) | — | — | — | 12 x 14 | OPEN: material TDS not read in this package |
| T-LPDDR5 | LPDDR5 (BGA315) to the recessed step of the Cu block | Gelid GP-Ultimate pad | 0.8 ± 0.1 | 1 (TP-GP04-B) | 10-30 % | 15 x 12.4 | PASS (model) |
| T-LIME | Lime bottom-side parts to the Al pedestal | Gelid GP-Ultimate pad | 0.8 ± 0.1 | 1 (TP-GP04-B) | 10-30 % | 60 x 22 | PASS (model) |
| T-UFS | UFS module (Q6A bottom side) to the Al boss on the plate | Gelid GP-Ultimate pad | 0.8 ± 0.1 | 1 (TP-GP04-B) | 10-30 % | 16.5 x 11.5 | PASS (model) |
| T-PWR1 | PWR board bottom copper to the plate, zone 1 | Gelid GP-Ultimate pad | 0.4 ± 0.05 | 0.5 (TP-GP04-A) | 10-30 % | 60 x 23 | PASS (model) |
| T-PWR2 | PWR board bottom copper to the plate, zone 2 | Gelid GP-Ultimate pad | 0.4 ± 0.05 | 0.5 (TP-GP04-A) | 10-30 % | 56 x 23 | PASS (model) |
| T-PWR3 | PWR board bottom copper to the plate, zone 3 | Gelid GP-Ultimate pad | 0.4 ± 0.05 | 0.5 (TP-GP04-A) | 10-30 % | 17 x 24 | PASS (model) |
| T-PWR4 | PWR board bottom copper to the plate, zone 4 | Gelid GP-Ultimate pad | 0.4 ± 0.05 | 0.5 (TP-GP04-A) | 10-30 % | 14 x 14 | PASS (model) |
| T-KSD9700 | KSD9700 70 C NO on the hottest IP2368 MOSFET | polyimide tape + thermally conductive adhesive | — | — | — | — | OPEN: adhesive product and its datasheet not chosen in this package (STACK 5.6 gives only the polyimide layer) |
| T-NTC | pack NTC on the middle cell (E3-06) | polyimide tape | — | — | — | — | OPEN: attachment product not chosen in this package |

Розкрій листів 90 x 50:

- 0.5 мм: 1 лист(и): T-PWR1 60x23 (лист 1), T-PWR2 56x23 (лист 1), T-PWR3 24x17 (лист 1), T-PWR4 14x14 (лист 1)
- 1.0 мм: 1 лист(и): T-LIME 60x22 (лист 1), T-UFS 16.5x11.5 (лист 1), T-LPDDR5 15x12.4 (лист 1)

## Ущільнення шва і гвинти

EPDM-шнур ⌀2 у пазу 2.6 x 1.55 у зовнішньому поясі 1.9 мм: стиск 22 %, заповнення 78 % — PASS (model); довжина по осі паза 762 мм, замовити 800 мм.

Гвинтів шва 14, середній проліт 56.3 мм, найдовший 121 мм (лівий нижній кут: батарея й екран HF+ доходять до стінок, бобишка не вміщується; рішення — стенд T-07). Доступ інструмента до кожного гвинта — рядок R-TOOL-ACCESS (гвинти 1 і 2 — після зняття тримача T7, який кріпиться ззовні).

## Перетини тіл (B-rep)

B-rep intersection of every envelope with the shells, plate, angles, RF bay, pedestal, UFS boss, tray, hatch, hood and T7 holder; all 78 pairs of these solids against each other; overlaps above 0.5 mm3 outside by-design features fail.

Результат: PASS (model fit only).


Перетини за задумом (плата на стійках, Lime на п'єдесталі тощо):

- CTRL.r0 ↔ front_shell: 219.4 мм³
- CTRL.r1 ↔ front_shell: 109.7 мм³
- CTRL.r2 ↔ front_shell: 115.9 мм³
- CTRL.r3 ↔ front_shell: 219.4 мм³
- CTRL.r4 ↔ front_shell: 109.7 мм³
- CTRL.r5 ↔ front_shell: 48.7 мм³
- ENC.r0 ↔ front_shell: 276 мм³
- ENC.r0 ↔ front_shell: 276 мм³
- lime ↔ lime_pedestal: 7160.1 мм³
- q6a.board ↔ ufs_boss: 73.3 мм³
- hatch_parts ↔ rear_shell: 11.8 мм³
- hatch_parts ↔ hatch_cover: 45 мм³
- gx16 ↔ rear_shell: 77.2 мм³
- veml7700 ↔ front_shell: 143.8 мм³

## Тісні місця (зазор < 0.5 мм, модель)

- q6a.board ↔ closure.boss6: 0.4 мм
- hatch_parts ↔ edl_key_body: 0 мм
- RF.r0 ↔ rfbay.wall.bottom: 0.4 мм

## Плати: механічний інтерфейс (contract/boards.json)

| плата | домени pcb/prepare.py | контур, мм² | отвори | висота деталей | розміщення | кріплення |
|---|---|---|---|---|---|---|
| PWR | PWR_MAIN, PWR_BRANCH, USB_POWER | 7910 | 7 x ⌀3.2 | ≤4.5 | default: (6, 38.5) z 40.9 +z | plate front face; Gelid 0.5 mm pads under the thermal_bond zones, gap 0.4 mm set by shim washers (mechanical.json pwr_bond) |
| PWR_B | PWR_BRANCH_SW, USB_POWER_SW | 7910 | 7 x ⌀3.2 | ≤5.5 | default: (6, 38.5) z 47.56 +z | on seven M3 male-female standoffs 5.0 mm (F45) over the PWR-A holes, M3 screws from the component side (F46); the Samtec LSHM-150-02.5-L-DV-A-N-K-TR J209 on the PWR-B bottom mates the same part J208 on the PWR-A top at 5.00 mm (two -02.5 halves, catalogue F-224; pcb/partition-spec.json b2b, W2 B2B) |
| RF | RF_HMC, RF_HF, RF_INJECTOR, DC_CORE | 8188 | 6 x ⌀3.2 | ≤5.5 | default: (17.6, 99) z 35.5 -z | PEM SO-M3-3 thru-hole standoffs (3 mm) clinched into the plate, heads flush with the plate front face; single RF GND/CHASSIS bond at BOND-RF |
| CTRL | CTRL_HMI | 5915 | 6 x ⌀2.7 | ≤5.5 | default: (176, 13) z 58.98 +z | M2.5 screws into CNC Kitchen TC-M2,5x4 inserts in the front-shell bosses |
| ENC | ENC | 576 | 2 x ⌀2.7 | ≤6.5 | main: (188.5, 123) z 58.38 +z; volume: (188.5, 82) z 58.38 +z | 2x M2.5 into CNC Kitchen TC-M2,5x4 inserts in the front-shell bosses |

## Площа плат: курт'ярди KiCad і роз'єми джгутів (MODEL ESTIMATE)

Джерело: KiCad 10.0.7 courtyards (build/kicad/footprints/manifest.json). Метод: sum of the vendored KiCad 10.0.7 F.CrtYd courtyards (bbox; polygon area for a single fp_poly) of the bare board parts of pcb/generated/components.csv (DNP excluded) per board domain; need = modules (mount pcb_module) x 1.0 + other parts x fill factor 1.5 or 1.8 (1.8 = planning value) — MODEL ESTIMATE, not a placement; роз'єми: header courtyard w x d (vendored KiCad 10.0.7 footprint where that pin count exists, else parts.json harness_headers) x fill factor 1.5 or 1.8, added to the parts need; frontage = sum of header widths against the edge zones of boards.json (every header at an edge, cable leaving sideways); Mini-Fit Jr., IDC and FAN3 courtyards are assumptions (parts.json).

MODEL ESTIMATE: reported, not gated (OPEN = need at the planning factor exceeds the outline; the real placement decides); MODEL ESTIMATE: reported, not gated (OPEN = the outline or the harness architecture needs a wave-2 decision)

| плата | контур, мм² | курт'ярди деталей, мм² | з них модулі (×1.0), мм² | потреба ×1.5 / ×1.8, мм² | результат | роз'ємів джгутів | курт'ярди роз'ємів, мм² | з роз'ємами ×1.5 / ×1.8, мм² | ширина роз'ємів / крайові зони, мм | результат |
|---|---|---|---|---|---|---|---|---|---|---|
| PWR | 7910 | 5046 | 0 | 7568 / 9082 | OPEN: 1 planned content changes of pcb/partition-budget.json candidates.shrink2 are pending (GR-5B), so the graph's courtyards (5046 mm2 raw) are not the decided content: the budget's planned PWR_A demand 8189 mm2 at fill 1.8 against its usable 7641 mm2 (budget ratio_1.8 = usable / demand 0.933, raw fill 0.595); model estimate, the placement decides (PCB) | — | — | — | — | — |
| PWR_B | 7910 | 2777 | 0 | 4166 / 4999 | PASS (model estimate): 1 planned content changes of pcb/partition-budget.json candidates.shrink2 are pending (GR-5B), so the graph's courtyards (2777 mm2 raw) are not the decided content: the budget's planned PWR_B demand 4727 mm2 at fill 1.8 against its usable 5056 mm2 (budget ratio_1.8 = usable / demand 1.07, raw fill 0.519); model estimate, the placement decides (PCB) | — | — | — | — | — |
| RF | 8188 | 2757 | 0 | 4136 / 4963 | PASS (model estimate) | — | — | — | — | — |
| CTRL | 5915 | 5675 | 1221 | 7901 / 9238 | OPEN: need 9238 mm2 at fill 1.8 > outline 5915 mm2 (model estimate; partition and placement decide, AREA / PCB) | — | — | — | — | — |
| ENC | 576 | — | — | — | — | 2 | 94 | 141 / 169 | 11 / 12 | PASS (model estimate) |

Курт'ярди деталей за групами схем (design/E*.json «group»), мм²: курт'ярди (потреба ×1.5 / ×1.8):

- PWR: E1 Роз'єми джгутів PWR 870 (1306 / 1567); E1 LAB5 469 (703 / 844); E2 Boni: малошумна захищена шина 455 (683 / 820); E2 Роз'єми джгутів PWR 430 (645 / 775); E1 SYS12 412 (618 / 742); E2 LNB: малошумна захищена шина 363 (544 / 653); E2 LNA4V5: паралельні LT3045 358 (537 / 644); E2 J21: захищене живлення 12 V 320 (479 / 575); E5 VBUS HF+ з демпфованим LC 315 (472 / 566); E2 Lime M.2: комутована шина 3.3 V 172 (258 / 310); E2 AUX12: верхній ключ і PTC 165 (247 / 297); E2 Дисплей: захищене живлення 12 V 157 (235 / 282); E1 AON і UV 94 (142 / 170); E1 Головний вимикач 92 (138 / 166); E2 INA3221: струми LNA4, LNB і Boni 67 (101 / 121); E5 Роз'єми джгутів PWR і HATCH 60 (90 / 108); E2 LNB: незалежне точне відсікання OVP 52 (78 / 94); E1 Захист USB-PD 50 (74 / 89); E5 Сервіс і зовнішні шини 47 (71 / 85); E1 Контрольні точки 31 (47 / 56); E1 Сервісний заряд 27 (41 / 49); E1 Інгібування заряду 26 (39 / 47); E1 Аварійний ADC 13 (19 / 23)
- PWR_B: E2 Роз'єми джгутів PWR 1075 (1613 / 1936); E5 VBUS RTL-A і LAB PORT 263 (395 / 474); E2 LNA: канал 2 259 (388 / 466); E2 LNA: канал 3 259 (388 / 466); E2 LNA: канал 1 152 (228 / 274); E2 LNA: канал 4 152 (228 / 274); E2 RTL-B: комутований VBUS 142 (213 / 255); E2 S-band LaNA WB: захищена шина 5 V 142 (213 / 255); E5 Роз'єми джгутів PWR і HATCH 115 (172 / 207); E2 INA3221: струми LNA1–3 67 (101 / 121); E5 LAB BUS I2C buffer 57 (86 / 103); E2 LNB: контроль напруги 31 (47 / 56); E2 Boni: контроль напруги 31 (47 / 56); E2 AUX12: контроль напруги після PTC 31 (47 / 56)
- RF: E4 RF and receiver interfaces 1139 (1708 / 2050); E4 RF passives and drivers 454 (680 / 817); E4 Роз'єми джгутів RF 419 (628 / 754); E4 DC detectors: common reference 171 (257 / 308); E4 DC detectors: UHF 156 (234 / 281); E4 DC detectors: LBAND 156 (234 / 281); E4 DC detectors: HF 156 (234 / 281); E4 SP4T switches 54 (82 / 98); E4 DC detectors: local power 35 (52 / 62); E4 RF bias injector local decoupling 18 (27 / 32)
- CTRL: E3 Роз'єми джгутів CTRL 2368 (3552 / 4263); E3 Pico HMI 1287 (1320 / 1340); E3 MCP23017 control 783 (1174 / 1409); E3 HMI buttons 487 (730 / 876); E3 Indicators 219 (328 / 394); E3 Cooling 170 (255 / 306); E3 Q6A header 120 (179 / 215); E3 HMI encoders 66 (99 / 118); E3 GNSS 53 (79 / 95); E3 Pico power control 48 (72 / 86); E3 Ambient sensor 31 (47 / 56); E3 MCP hardware watchdog reset 26 (39 / 47); E3 Thermal sensors 17 (26 / 31)
- роз'єми, що вже є деталями плати (пораховано раз): J104, J105, J106, J107, J108, J109, J110, J111, J112, J113, J114, J115, J201, J202, J203, J204, J205, J206, J207, J302, J304, J305, J306, J307, J308, J309, J310, J311, J312, J313, J314, J315, J316, J317, J318, J319, J418, J419, J420, J506, J507

## Зони висоти CTRL і RF (карта вільної висоти, модель)

Вільна висота від площини компонентів (лице) і від тильної площини плати до найближчого конверту, деталі конструкції, фланця кнопки або стінки; «вміщує» = вільна − 0.5 мм. Координати — від лівого нижнього кута контуру плати (boards.json). Ті самі списки записано в boards.json (height_zones / rear_zones) і в contract/boards.json.

| плата | бік | x, y, ш x в, мм | вільна, мм | вміщує, мм | обмежує |
|---|---|---|---|---|---|
| CTRL | лице | 0, 0, 6 x 14.5 | 7 | 6.5 | front wall |
| CTRL | лице | 6, 0, 15 x 14.5 | 5.5 | 5 | button_flange.02 |
| CTRL | лице | 21, 0, 7 x 14.5 | 7 | 6.5 | front wall |
| CTRL | лице | 28, 0, 15 x 14.5 | 5.5 | 5 | button_flange.12 |
| CTRL | лице | 43, 0, 7 x 14.5 | 7 | 6.5 | front wall |
| CTRL | лице | 0, 14.5, 50 x 7 | 7 | 6.5 | front wall |
| CTRL | лице | 0, 21.5, 6 x 15 | 7 | 6.5 | front wall |
| CTRL | лице | 6, 21.5, 15 x 15 | 5.5 | 5 | button_flange.01 |
| CTRL | лице | 21, 21.5, 7 x 15 | 7 | 6.5 | front wall |
| CTRL | лице | 28, 21.5, 15 x 15 | 5.5 | 5 | button_flange.11 |
| CTRL | лице | 43, 21.5, 7 x 15 | 7 | 6.5 | front wall |
| CTRL | лице | 0, 36.5, 50 x 7 | 7 | 6.5 | front wall |
| CTRL | лице | 0, 43.5, 6 x 15 | 7 | 6.5 | front wall |
| CTRL | лице | 6, 43.5, 15 x 15 | 5.5 | 5 | button_flange.00 |
| CTRL | лице | 21, 43.5, 7 x 15 | 7 | 6.5 | front wall |
| CTRL | лице | 28, 43.5, 15 x 15 | 5.5 | 5 | button_flange.10 |
| CTRL | лице | 43, 43.5, 7 x 15 | 7 | 6.5 | front wall |
| CTRL | лице | 0, 58.5, 50 x 10 | 7 | 6.5 | front wall |
| CTRL | лице | 0, 68.5, 12 x 25 | 7 | 6.5 | front wall |
| CTRL | лице | 37, 68.5, 13 x 25 | 7 | 6.5 | front wall |
| CTRL | лице | 0, 93.5, 50 x 16 | 7 | 6.5 | front wall |
| CTRL | лице | 0, 109.5, 12 x 25 | 7 | 6.5 | front wall |
| CTRL | лице | 37, 109.5, 13 x 25 | 7 | 6.5 | front wall |
| CTRL | лице | 0, 134.5, 50 x 2.5 | 7 | 6.5 | front wall |
| CTRL | лице | 0, 137, 40 x 7 | 7 | 6.5 | front wall |
| CTRL | тил | 0, 0, 34 x 57 | 7.98 | 7.48 | bms |
| CTRL | тил | 34, 0, 9.5 x 5.5 | 18.48 | 17.98 | plate.ext |
| CTRL | тил | 43.5, 0, 6.5 x 5.5 | 4.48 | 3.98 | plate.boss2 |
| CTRL | тил | 34, 5.5, 16 x 8 | 18.48 | 17.98 | plate.ext |
| CTRL | тил | 34, 13.5, 1 x 7.5 | 18.48 | 17.98 | plate.ext |
| CTRL | тил | 35, 13.5, 11 x 7.5 | 14.98 | 14.48 | hdmi_route_front_up |
| CTRL | тил | 46, 13.5, 4 x 7.5 | 18.48 | 17.98 | plate.ext |
| CTRL | тил | 34, 21, 0.5 x 4.5 | 18.48 | 17.98 | plate.ext |
| CTRL | тил | 34.5, 21, 15.5 x 18 | 13.48 | 12.98 | hdmi_insert |
| CTRL | тил | 34, 25.5, 0.5 x 13.5 | 18.48 | 17.98 | plate.main |
| CTRL | тил | 34, 39, 1 x 18 | 18.48 | 17.98 | plate.main |
| CTRL | тил | 35, 39, 11 x 24.8 | 17.38 | 16.88 | hdmi_route_front_run |
| CTRL | тил | 46, 39, 4 x 37.5 | 18.48 | 17.98 | plate.main |
| CTRL | тил | 0, 57, 35 x 8.5 | 18.48 | 17.98 | plate.main |
| CTRL | тил | 35, 63.8, 11 x 4.7 | 16.48 | 15.98 | hdmi_route_front_turn |
| CTRL | тил | 0, 65.5, 10 x 11 | 7.98 | 7.48 | hdmi_route_front_rise |
| CTRL | тил | 10, 65.5, 25 x 3 | 16.98 | 16.48 | hdmi_route_front_flat |
| CTRL | тил | 10, 68.5, 2 x 8 | 16.98 | 16.48 | hdmi_route_front_flat |
| CTRL | тил | 37, 68.5, 9 x 8 | 16.48 | 15.98 | hdmi_route_front_turn |
| CTRL | тил | 0, 76.5, 12 x 6.5 | 18.48 | 17.98 | plate.main |
| CTRL | тил | 37, 76.5, 13 x 6.5 | 18.48 | 17.98 | plate.main |
| CTRL | тил | 0, 83, 12 x 10.5 | 5.48 | 4.98 | lime |
| CTRL | тил | 37, 83, 13 x 10.5 | 5.48 | 4.98 | lime |
| CTRL | тил | 0, 93.5, 50 x 15.5 | 5.48 | 4.98 | lime |
| CTRL | тил | 0, 109, 50 x 0.5 | 18.48 | 17.98 | plate.main |
| CTRL | тил | 0, 109.5, 12 x 25 | 7.98 | 7.48 | ip2368 |
| CTRL | тил | 37, 109.5, 7 x 25 | 7.98 | 7.48 | ip2368 |
| CTRL | тил | 44, 109.5, 6 x 27.5 | 18.48 | 17.98 | plate.main |
| CTRL | тил | 0, 134.5, 44 x 2.5 | 7.98 | 7.48 | ip2368 |
| CTRL | тил | 0, 137, 40 x 6.5 | 7.98 | 7.48 | ip2368 |
| CTRL | тил | 0, 143.5, 40 x 0.5 | 18.48 | 17.98 | plate.main |
| RF | лице | 0, 0, 184 x 0.1 | 29.8 | 29.3 | rfbay.lid |
| RF | лице | 0, 0.1, 73.7 x 30.6 | 11.1 | 10.6 | sawbird |
| RF | лице | 73.7, 0.1, 7.9 x 27 | 29.8 | 29.3 | rfbay.lid |
| RF | лице | 81.6, 0.1, 95 x 0.5 | 16.8 | 16.3 | v4l_a |
| RF | лице | 176.6, 0.1, 7.4 x 22 | 16.8 | 16.3 | usb_socket_a |
| RF | лице | 81.6, 0.6, 6.8 x 26 | 16.8 | 16.3 | v4l_a |
| RF | лице | 88.4, 0.6, 30 x 26 | 6.5 | 6 | boni_a406 |
| RF | лице | 118.4, 0.6, 58.2 x 26 | 16.8 | 16.3 | v4l_a |
| RF | лице | 176.6, 22.1, 7.4 x 5 | 29.8 | 29.3 | rfbay.lid |
| RF | лице | 81.6, 26.6, 95 x 0.5 | 16.8 | 16.3 | v4l_a |
| RF | лице | 73.7, 27.1, 110.3 x 0.5 | 29.8 | 29.3 | rfbay.lid |
| RF | лице | 73.7, 27.6, 7.9 x 3.1 | 29.8 | 29.3 | rfbay.lid |
| RF | лице | 81.6, 27.6, 95 x 16.9 | 16.8 | 16.3 | v4l_b |
| RF | лице | 176.6, 27.6, 7.4 x 16.9 | 16.8 | 16.3 | usb_socket_b |
| RF | лице | 0, 30.7, 81.6 x 0.5 | 29.8 | 29.3 | rfbay.lid |
| RF | лице | 0, 31.2, 73.7 x 13.3 | 11.1 | 10.6 | flamingo |
| RF | лице | 73.7, 31.2, 7.9 x 13.3 | 29.8 | 29.3 | rfbay.lid |
| RF | тил | 0, 0, 184 x 44.5 | 3 | 2.5 | plate.main |

Роз'єми джгутів понад обмеження плати або без прочитаної висоти (24 з 43; правило R-HDR-HEIGHT). Висота — з'єднаної пари (вилка + кабельна частина), де її прочитано, інакше корпусу вилки (позначено); вихід дроту за кабельною частиною не враховано (дріт TBD, AI-WIRE-PTFE). Для Micro-Fit понад межу наведено й кутову 43650 (MF_ra):

| роз'єм | плата | родина | висота, мм | курт'ярд, мм | межа плати | найкраща зона лиця / тилу, мм | кутова 43650: висота, курт'ярд, зони лиця / тилу, мм | висновок |
|---|---|---|---|---|---|---|---|---|
| J104 | PWR | MF top | 17.27 (пара) | 16.66 x 6.77 | 4.5 | 4.5 / 0 | 6.98 (пара); 16.66 x 10.91; 4.5 / 0 | above the board limit 4.5; fits no computed zone that takes its courtyard; W2 MECH-7: it stands in a PWR-B edge strip (no PWR-B over it), its mated top under the display is rule R-HDR-MATED; as MF_ra (6.98 mm mated): above the board limit 4.5; fits no computed zone that takes its courtyard |
| J105 | PWR | MFJ top | TBD | 11.7 x 13 | 4.5 | 4.5 / 0 | — | height of MFJ_top not read (TBD) |
| J106 | PWR | MFJ top | TBD | 11.7 x 13 | 4.5 | 4.5 / 0 | — | height of MFJ_top not read (TBD) |
| J107 | PWR | MFJ top | TBD | 11.7 x 13 | 4.5 | 4.5 / 0 | — | height of MFJ_top not read (TBD) |
| J108 | PWR | MFJ top | TBD | 15.9 x 13 | 4.5 | 4.5 / 0 | — | height of MFJ_top not read (TBD) |
| J109 | PWR | PH top | 8 (пара) | 6.9 x 5.5 | 4.5 | 4.5 / 0 | — | above the board limit 4.5; fits no computed zone that takes its courtyard; W2 MECH-7: it stands in a PWR-B edge strip (no PWR-B over it), its mated top under the display is rule R-HDR-MATED |
| J110 | PWR | PH top | 8 (пара) | 12.9 x 5.5 | 4.5 | 4.5 / 0 | — | above the board limit 4.5; fits no computed zone that takes its courtyard; W2 MECH-7: it stands in a PWR-B edge strip (no PWR-B over it), its mated top under the display is rule R-HDR-MATED |
| J111 | PWR | PH top | 8 (пара) | 8.9 x 5.5 | 4.5 | 4.5 / 0 | — | above the board limit 4.5; fits no computed zone that takes its courtyard; W2 MECH-7: it stands in a PWR-B edge strip (no PWR-B over it), its mated top under the display is rule R-HDR-MATED |
| J112 | PWR | PH top | 8 (пара) | 10.9 x 5.5 | 4.5 | 4.5 / 0 | — | above the board limit 4.5; fits no computed zone that takes its courtyard; W2 MECH-7: it stands in a PWR-B edge strip (no PWR-B over it), its mated top under the display is rule R-HDR-MATED |
| J113 | PWR | PH top | 8 (пара) | 6.9 x 5.5 | 4.5 | 4.5 / 0 | — | above the board limit 4.5; fits no computed zone that takes its courtyard; W2 MECH-7: it stands in a PWR-B edge strip (no PWR-B over it), its mated top under the display is rule R-HDR-MATED |
| J114 | PWR | MF top | 17.27 (пара) | 10.66 x 6.77 | 4.5 | 4.5 / 0 | 6.98 (пара); 10.66 x 10.91; 4.5 / 0 | above the board limit 4.5; fits no computed zone that takes its courtyard; W2 MECH-7: it stands in a PWR-B edge strip (no PWR-B over it), its mated top under the display is rule R-HDR-MATED; as MF_ra (6.98 mm mated): above the board limit 4.5; fits no computed zone that takes its courtyard |
| J115 | PWR | MF top | 17.27 (пара) | 10.66 x 6.77 | 4.5 | 4.5 / 0 | 6.98 (пара); 10.66 x 10.91; 4.5 / 0 | above the board limit 4.5; fits no computed zone that takes its courtyard; W2 MECH-7: it stands in a PWR-B edge strip (no PWR-B over it), its mated top under the display is rule R-HDR-MATED; as MF_ra (6.98 mm mated): above the board limit 4.5; fits no computed zone that takes its courtyard |
| J202 | PWR_B | PHD side | 5 (корпус) | — | 5.5 | 5.5 / 0 | — | inside the board limit (header body 5 mm; mated height not read: TBD) |
| J203 | PWR_B | PHD top | 8.8 (пара) | 21.9 x 5 | 5.5 | 17.85 / 0 | — | above the board limit 5.5; fits a component-side height zone |
| J205 | PWR | MF top | 17.27 (пара) | 10.66 x 6.77 | 4.5 | 4.5 / 0 | 6.98 (пара); 10.66 x 10.91; 4.5 / 0 | above the board limit 4.5; fits no computed zone that takes its courtyard; W2 MECH-7: it stands in a PWR-B edge strip (no PWR-B over it), its mated top under the display is rule R-HDR-MATED; as MF_ra (6.98 mm mated): above the board limit 4.5; fits no computed zone that takes its courtyard |
| J206 | PWR | MF2 top | 17.64 (пара) | — | 4.5 | 4.5 / 0 | — | above the board limit 4.5; fits no computed zone that takes its courtyard; W2 MECH-7: it stands in a PWR-B edge strip (no PWR-B over it), its mated top under the display is rule R-HDR-MATED |
| J506 | PWR_B | PH top | 8 (пара) | 20.9 x 5.5 | 5.5 | 17.85 / 0 | — | above the board limit 5.5; fits a component-side height zone |
| J507 | PWR | PH top | 8 (пара) | 10.9 x 5.5 | 4.5 | 4.5 / 0 | — | above the board limit 4.5; fits no computed zone that takes its courtyard; W2 MECH-7: it stands in a PWR-B edge strip (no PWR-B over it), its mated top under the display is rule R-HDR-MATED |
| J304 | CTRL | IDC top | 9.1 (корпус) | 61 x 9 | 5.5 | 5.5 / 0 | — | above the board limit 5.5; fits no computed zone that takes its courtyard (header body 9.1 mm, reference part; mated height not read: TBD) |
| J305 | CTRL | MF top | 17.27 (пара) | 16.66 x 6.77 | 5.5 | 6.5 / 17.98 | 6.98 (пара); 16.66 x 10.91; 6.5 / 16.88 | above the board limit 5.5; fits a rear zone (THT from the back); as MF_ra (6.98 mm mated): above the board limit 5.5; fits a rear zone (THT from the back) |
| J306 | CTRL | PHD top | 8.8 (пара) | 21.9 x 5 | 5.5 | 6.5 / 17.98 | — | above the board limit 5.5; fits a rear zone (THT from the back) |
| J307 | CTRL | PHD top | 8.8 (пара) | 21.9 x 5 | 5.5 | 6.5 / 17.98 | — | above the board limit 5.5; fits a rear zone (THT from the back) |
| J313 | CTRL | FAN3 top | TBD | 10.08 x 6 | 5.5 | 6.5 / 17.98 | — | height of FAN3_top not read (TBD) |
| J314 | CTRL | MF top | 17.27 (пара) | 10.66 x 6.77 | 5.5 | 6.5 / 17.98 | 6.98 (пара); 10.66 x 10.91; 6.5 / 16.88 | above the board limit 5.5; fits a rear zone (THT from the back); as MF_ra (6.98 mm mated): above the board limit 5.5; fits a rear zone (THT from the back) |

## Траси джгутів (модель, generated/harness-routes.json)

Осьова лінія кожного сегмента build/16 крізь модель корпусу (mechanical.json harness_routes): довжина = ламана + запас на вигини (половина діаметра джгута × кут) + 2 × 15 мм сервісних петель, округлено вгору до 1 мм. Діаметр джгута — верхня межа за кількістю жил build/16 і найбільшим ⌀ обраного дроту PTFE (номінал + допуск, parts.json hookup_wire_ptfe; переріз без прочитаного ⌀ — найбільша ізоляція, яку беруть клеми). Коаксіал W407 — без сервісних петель, із запасом ≥30 мм до довжини пігтейла (R-P7-PIGTAIL). Кінці на крайових зонах плат (з назвами роз'ємів графа) і біля модулів без конверту — попередні (OPEN), доки немає позицій роз'ємів. MODEL ESTIMATE, не виміряні довжини.

PPS (R-PPS-LEN): S01+S25 = 301 мм проти 200 мм; рішення — PPS + UART6 + GND branch off the S01 ribbon at the Q6A end and run directly to the LC76G in the rear layer (harness only, E3 nets unchanged; build/15 W2 MECH-1); гілка PPS = 158 мм.

| сегмент | тип | довжина, мм | ламана, мм | вигинів | ⌀ джгута, мм | прорізи | стан |
|---|---|---|---|---|---|---|---|
| S01 | harness | 106 | 69.5 | 3 | 2.54 | SL1 | OPEN (end provisional): J304 (X01I1-CTRL, CTRL) position TBD (board placement): end on the CTRL edge zone 0 |
| S02 | harness | 188 | 91.3 | 6 | 14.04 | — | OPEN (end provisional): J302 (CTRL), J305 (X02P1-CTRL, CTRL), J306 (S02-CTRL-SIG-1, CTRL), J307 (S02-CTRL-SIG-2, CTRL) position TBD (board placement): end on the CTRL edge zone 0; J104 (X02P1-PWR, PWR_A), J201 (X02S0-PWR, PWR_B), J202 (S02-PWR-SIG-1, PWR_B), J203 (S02-PWR-SIG-2, PWR_B) position TBD (board placement): end on the PWR_B edge zone 0 |
| S03 | harness | 295 | 222.7 | 11 | 4.87 | SL2, N4 | OPEN (end provisional): J308 (X03S1-CTRL, CTRL), J309 (X03S2-CTRL, CTRL) position TBD (board placement): end on the CTRL edge zone 0; J418 (X03S1-RF, RF), J419 (X03S2-RF, RF) position TBD (board placement): end on the RF edge zone 2 |
| S04 | harness | 260 | 205.1 | 9 | 3.51 | SL2, N4 | OPEN (end provisional): J204 (X04S1-PWR, PWR_B) position TBD (board placement): end on the PWR_B edge zone 1; J420 (X04S1-RF, RF) position TBD (board placement): end on the RF edge zone 2 |
| S05 | harness | 35 | 4.8 | 0 | 4.2 | — | OPEN (end provisional): F101 carrier PACK_FUSE not modelled (mechanical/README): end on the pack top face; J105 (X05J1-PWR, PWR_A), J109 (X05S1-PWR, PWR_A) position TBD (board placement): end on the PWR edge zone 0 |
| S06 | harness | 188 | 127.3 | 6 | 6.42 | SL2 | OPEN (end provisional): INA228 5832 terminal block position on the board not read (Adafruit page gives the outline only): end at the top (+y) face of its envelope; J106 (X06J1-PWR, PWR_A), J110 (X06S1-PWR, PWR_A) position TBD (board placement): end on the PWR edge zone 3 |
| S07 | harness | 122 | 70.2 | 5 | 5.43 | SL2 | OPEN (end provisional): #2813 terminal positions not read (no Pololu dimension drawing on the product page): end at the top (+y) face of its envelope; J107 (X07J1-PWR, PWR_A), J111 (X07S1-PWR, PWR_A) position TBD (board placement): end on the PWR edge zone 3 |
| S10 | harness | 222 | 150.9 | 8 | 6.42 | — | OPEN (end provisional): J108 (X10J1-PWR, PWR_A), J112 (X10S1-PWR, PWR_A) position TBD (board placement): end on the PWR edge zone 0 |
| S11 | harness | 227 | 177.6 | 6 | 4.05 | SL3 | OPEN (end provisional): behind-panel envelope of MUSBRM5C130 TBD (MECH-2): end at the port centre on the wall; J113 (X11S1-PWR, PWR_A), J114 (X11P1-PWR, PWR_A) position TBD (board placement): end on the PWR edge zone 1 |
| S12 | harness | 55 | 22.5 | 1 | 2.87 | — | OPEN (end provisional): XT30 pigtail place in the battery compartment TBD: end on the pack top face; J115 (X12P1-PWR, PWR_A) position TBD (board placement): end on the PWR edge zone 1 |
| S13 | harness | 131 | 87.5 | 6 | 2.87 | SL2 | OPEN (end provisional): Adafruit 5997 has no envelope (mechanical/README): end below the Q6A USB stack (J2); J206 (SL2-PWR-MF, PWR_A) position TBD (board placement): end on the PWR edge zone 3 |
| S14 | harness | 68 | 34.8 | 1 | 2.87 | SL2 | OPEN (end provisional): hatch-board layout TBD (W2-05): end on the hatch-board envelope; J206 (SL2-PWR-MF, PWR_A) position TBD (board placement): end on the PWR edge zone 3 |
| S15 | harness | 158 | 119.4 | 7 | 1.41 | SL2 | OPEN (end provisional): hatch-board layout TBD (W2-05): end on the hatch-board envelope; J310 (S15-30-CTRL, CTRL) position TBD (board placement): end on the CTRL edge zone 0 |
| S16 | harness | 122 | 86.2 | 2 | 3.51 | — | OPEN (end provisional): hatch-board layout TBD (W2-05): J503 on the hatch-board envelope |
| S17 | harness | 160 | 115.6 | 6 | 2.87 | SL2 | OPEN (end provisional): J206 (SL2-PWR-MF, PWR_A) position TBD (board placement): end on the PWR edge zone 3 |
| S18 | harness | 161 | 122 | 4 | 2.87 | SL2 | OPEN (end provisional): R44SF envelope TBD: end at the riser window (plate rear face); J206 (SL2-PWR-MF, PWR_A) position TBD (board placement): end on the PWR edge zone 3 |
| S19 | harness | 38 | 5 | 1 | 2.87 | — | OPEN (end provisional): barrel jack position on the Wisecoco HDMI board TBD (STACK D5): end on the board envelope; J205 (X19P1-PWR, PWR_A) position TBD (board placement): end on the PWR edge zone 2 |
| S20 | harness | 210 | 170.2 | 7 | 1.75 | SL2, N2 | OPEN (end provisional): J543 pigtail (H2) place TBD: end at notch N2 of the RTL-A USB lead; J207 (SL2-PWR-PH, PWR_B) position TBD (board placement): end on the PWR_B edge zone 1 |
| S21 | harness | 211 | 171.2 | 7 | 1.75 | SL2, N3 | OPEN (end provisional): J541 place TBD: end at notch N3 of the RTL-B USB lead; J207 (SL2-PWR-PH, PWR_B) position TBD (board placement): end on the PWR_B edge zone 1 |
| S22 | harness | 82 | 44.9 | 4 | 2.15 | SL2 | OPEN (end provisional): J544 micro-USB pigtail exit on the HF+ can TBD: end on the can face; J207 (SL2-PWR-PH, PWR_B) position TBD (board placement): end on the PWR_B edge zone 1 |
| S23 | harness | 280 | 230.6 | 11 | 2.15 | SL3 | OPEN (end provisional): behind-panel envelope of PX0845/A TBD (MECH-2): end at the port centre on the wall; J506 (SL3-PWR-PH, PWR_B) position TBD (board placement): end on the PWR_B edge zone 2 |
| S24 | harness | 190 | 142.1 | 9 | 2.44 | SL2 | OPEN (end provisional): T7_INSERT envelope TBD (in the USB3 cable between Q6A J5 and the T7 gland): end beside the gland; J311 (S24-25-CTRL, CTRL) position TBD (board placement): end on the CTRL edge zone 0 |
| S25 | harness | 195 | 148.3 | 9 | 2.44 | SL2 | OPEN (end provisional): J311 (S24-25-CTRL, CTRL) position TBD (board placement): end on the CTRL edge zone 0 |
| S26 | harness | 100 | 67.3 | 1 | 2.81 | — | OPEN (end provisional): route crosses a solid — re-route when the ends are placed: piece 3 through veml7700 |
| S27 | stock_lead | 114 | 71.6 | 6 | 2.44 | SL1 | OPEN (end provisional): J313 (X27F1-CTRL, CTRL) position TBD (board placement): end on the CTRL edge zone 0 |
| S28 | harness | 42 | 9 | 1 | 2.87 | — | OPEN (end provisional): J314 (X28P1-CTRL, CTRL) position TBD (board placement): end on the CTRL edge zone 0 |
| S29 | harness | 76 | 39.3 | 4 | 1.99 | — | OPEN (end provisional): J315 (X29S1-CTRL, CTRL) position TBD (board placement): end on the CTRL edge zone 0 |
| S30 | harness | 175 | 129.2 | 8 | 2.44 | SL2 | OPEN (end provisional): hatch-board layout TBD (W2-05): J502 on the hatch-board envelope; J310 (S15-30-CTRL, CTRL) position TBD (board placement): end on the CTRL edge zone 0 |
| S31 | harness | 57 | 24.2 | 2 | 1.99 | — | OPEN (end provisional): J522 EDL contact pads on the Q6A not localised (E5 §9): end at the Q6A board edge |
| S32 | harness | 209 | 164.8 | 6 | 2.81 | SL3 | OPEN (end provisional): J507 (X32S1-PWR, PWR_A) position TBD (board placement): end on the PWR edge zone 1 |
| S33 | external | — | — | — | — | — | EXTERNAL: outside the enclosure; the length is set by the cable, not by the enclosure model |
| S34 | harness | 231 | 176 | 9 | 3.45 | SL3 | OPEN (end provisional): KH-GX12-6P solder cups inside the receptacle not modelled: end at the rear (+y) face of its inner nut envelope (nut.LAB_BUS, READS-E drawing row), W2 MECH-7 part 2; J506 (SL3-PWR-PH, PWR_B) position TBD (board placement): end on the PWR_B edge zone 2 |
| S35 | harness | 177 | 138.3 | 6 | 1.75 | SL2 | OPEN (end provisional): Boni-Whip bias-tee has no envelope (mechanical/README): end at the HF+ can top edge; J207 (SL2-PWR-PH, PWR_B) position TBD (board placement): end on the PWR_B edge zone 1 |
| S36 | harness | 213 | 173.2 | 7 | 1.75 | SL2 | OPEN (end provisional): J551 lead exit at the receptacle rear (0.2 m AWG 24 leads, soldered to the S36 wires, build/16): end at the rear face of the receptacle's inner envelope (nut.J551); J207 (SL2-PWR-PH, PWR_B) position TBD (board placement): end on the PWR_B edge zone 1 |
| S37 | harness | 31 | 0.8 | 0 | 2.81 | — | OPEN (end provisional): X37S0-ENCM (ENCM) position TBD (board placement): end on the ENC edge zone 0 |
| S38 | harness | 31 | 0.8 | 0 | 2.81 | — | OPEN (end provisional): X38S0-ENCV (ENCV) position TBD (board placement): end on the ENC edge zone 0 |
| S39 | harness | 45 | 11 | 2 | 1.99 | — | OPEN (end provisional): J318 (X39S1-CTRL, CTRL) position TBD (board placement): end on the CTRL edge zone 0 |
| S40 | harness | 64 | 28.4 | 3 | 1.99 | — | OPEN (end provisional): J319 (X40S1-CTRL, CTRL) position TBD (board placement): end on the CTRL edge zone 0 |
| S41 | external | — | — | — | — | — | EXTERNAL: outside the enclosure; the length is set by the cable, not by the enclosure model |
| PPS (гілка) | harness | 158 | 118.7 | 3 | 3.87 | — | OPEN (end provisional): J20 pin-1 orientation not read (no pin-1 mark on J20 in the Radxa placement map V1.21, read 2026-11-07): take-off at the centre of the S01 socket, while J20.7 (column 4 of 20, 2.54 pitch) sits 16.5 mm to one side of it: +/-16.5 mm on the branch; P1 (MX1.25) position read on the Waveshare outline drawing (parts.json lc76g), its height inside the 13.1 mm reserve is not (module height not read): end at mid-height, +/-6.6 mm |
| S02B (гілка) | harness | 162 | 105.9 | 5 | 6.47 | — | OPEN (end provisional): CTRL header position TBD (board layout; GR-3 header refs): end on the edge zone; PWR_B header position TBD (board layout; GR-3 header refs): end on the edge zone |
| W407 (коаксіал) | coax | 204 | 198.6 | 6 | 1.13 | N1 | PASS (model) |

Прорізи пластини: SL1 — у plate.slots 2, трасами 2; SL2 — у plate.slots 17, трасами 17; SL3 — у plate.slots 4, трасами 4.

## Розташування конвертів (мм; x вправо, y вгору з лиця, z від задньої зовнішньої грані)

| ID | деталь / плата | x | y | z | кріплення |
|---|---|---|---|---|---|
| battery_tray | — | 3.1-161.2 | 4.55-37.95 | 4-58.4 | free |
| battery_pack | battery_pack | 7.3-157.3 | 8.75-33.75 | 8.2-54.2 | free |
| display | display_module | 6.3-170.52 | 50.3-148.28 | 60.58-66.58 | front_wall |
| hdmi_board | hdmi_board | 50-146.2 | 75-157 | 45-56 | plate_front |
| PWR.r0 | PWR | 6-142 | 38.5-73.5 | 40.9-47.06 | plate_front |
| PWR.r1 | PWR | 6-48 | 73.5-148.5 | 40.9-47.06 | plate_front |
| PWR.b0 | PWR | 6-13 | 50.5-67.5 | 39.87-40.9 | plate_front |
| PWR.b1 | PWR | 136-142 | 50.5-63.5 | 39.87-40.9 | plate_front |
| PWR.b2 | PWR | 6-46 | 67.5-75.5 | 39.87-40.9 | plate_front |
| PWR.b3 | PWR | 58-132 | 67.5-72.6 | 39.87-40.9 | plate_front |
| PWR.b4 | PWR | 6-11 | 75.5-103.5 | 39.87-40.9 | plate_front |
| PWR.b5 | PWR | 6-15.6 | 103.5-109 | 39.87-40.9 | plate_front |
| PWR.b6 | PWR | 27.6-48 | 103.5-109 | 39.87-40.9 | plate_front |
| PWR.b7 | PWR | 6-11 | 109.5-127.5 | 39.87-40.9 | plate_front |
| PWR.b8 | PWR | 6-48 | 127.5-133.5 | 39.87-40.9 | plate_front |
| PWR.b9 | PWR | 6-15.6 | 133.5-138.5 | 39.87-40.9 | plate_front |
| PWR.b10 | PWR | 27.6-48 | 133.5-138.5 | 39.87-40.9 | plate_front |
| PWR.b11 | PWR | 27.6-38 | 138.5-145.5 | 39.87-40.9 | plate_front |
| PWR.b12 | PWR | 16-38 | 145.5-148.5 | 39.87-40.9 | plate_front |
| PWR_B.r0 | PWR_B | 6-142 | 38.5-73.5 | 47.56-54.73 | plate_front |
| PWR_B.r1 | PWR_B | 6-48 | 73.5-148.5 | 47.56-54.73 | plate_front |
| blower | blower | 144-174.5 | 38.5-69 | 45-55.5 | plate_front |
| CTRL.r0 | CTRL | 176-226 | 13-81.5 | 58.98-66.08 | front_wall |
| CTRL.r1 | CTRL | 176-188 | 81.5-147.5 | 58.98-66.08 | front_wall |
| CTRL.r2 | CTRL | 213-226 | 81.5-147.5 | 58.98-66.08 | front_wall |
| CTRL.r3 | CTRL | 176-226 | 106.5-122.5 | 58.98-66.08 | front_wall |
| CTRL.r4 | CTRL | 176-216 | 147.5-157 | 58.98-66.08 | front_wall |
| CTRL.r5 | CTRL | 216-226 | 147.5-150 | 58.98-66.08 | front_wall |
| ENC.r0 | ENC | 188.5-212.5 | 123-147 | 58.38-66.48 | front_wall |
| ENC.r0 | ENC | 188.5-212.5 | 82-106 | 58.38-66.48 | front_wall |
| bms | daly_bms | 175-210 | 9-70 | 41-51 | plate_front |
| ip2368 | ip2368_board | 172-220 | 122.5-156.5 | 41-51 | plate_front |
| lime | lime | 147-227 | 96-122 | 40.5-53.5 | plate_front |
| hfplus | hfplus_can | 2.6-114.6 | 38.5-94.5 | 17.5-38.5 | plate_rear |
| lc76g | lc76g | 58-88.5 | 71-96.5 | 3-16.1 | rear_wall |
| tripod_boss | — | 89-111 | 59-81 | 2.5-4.8 | rear_wall |
| q6a.board | q6a | 142-227 | 38.5-94.5 | 23.4-36.2 | plate_rear |
| q6a.usb_stack | q6a | 139.25-156.71 | 39.25-54.92 | 14.65-30.9 | plate_rear |
| q6a.rj45 | q6a | 138.71-159.96 | 76.24-92.47 | 17.3-30.9 | plate_rear |
| q6a.hdmi | q6a | 187.45-202.45 | 36.23-48.23 | 24.54-30.9 | plate_rear |
| q6a.audio | q6a | 169.13-176.83 | 35.88-49.88 | 25.65-30.9 | plate_rear |
| q6a.usb_c | q6a | 211.37-220.31 | 37.27-44.62 | 27.8-30.9 | plate_rear |
| q6a.header40 | q6a | 169.03-219.83 | 87.14-94.35 | 21.25-30.9 | plate_rear |
| q6a.j21_3p | q6a | 202.95-210.57 | 39.39-41.93 | 22.4-30.9 | plate_rear |
| q6a.hdr2x2 | q6a | 162.91-167.99 | 82.36-87.44 | 23.4-30.9 | plate_rear |
| q6a.s01_idc_socket | q6a | 169.03-219.83 | 87.14-94.35 | 14.4-30.9 | plate_rear |
| cooler_a.block | q6a_cooler_zone | 172.63-189.63 | 51.84-81.5 | 24.9-29.9 | q6a |
| cooler_a.fins | q6a_cooler_zone | 169-201 | 50.5-81.5 | 20.4-24.9 | q6a |
| cooler_a.fan | q6a_cooler_zone | 164-204 | 46-86 | 10.4-20.4 | q6a |
| q6a_fan_duct | — | 164-204 | 46-86 | 2.5-10.4 | rear_wall |
| usb_plug_bay | резерв (порожньо) | 116.6-139 | 38.5-56.5 | 14.65-30.65 | free |
| hdmi_fpc_q6a | adafruit_3550 | 186.45-203.45 | 21.23-36.23 | 16.22-35.22 | free |
| hdmi_route_rear | резерв (порожньо) | 189.45-222 | 11.6-22 | 10.5-16 | free |
| hdmi_ferrite | wurth_74278011 | 201.5-209.5 | 8.8-24.8 | 10.5-15.5 | free |
| hdmi_route_rise | резерв (порожньо) | 211-222 | 21.6-33.5 | 10.5-38.5 | free |
| hdmi_route_front_up | резерв (порожньо) | 211-222 | 26.5-34 | 40.5-44 | free |
| hdmi_insert | hdmi_insert_board | 210.5-226.5 | 34-52 | 40.5-45.5 | plate_front |
| hdmi_route_front_run | резерв (порожньо) | 211-222 | 52-76.8 | 40.5-41.6 | free |
| hdmi_route_front_turn | резерв (порожньо) | 211-222 | 76.8-89.5 | 40.5-42.5 | free |
| hdmi_route_front_flat | резерв (порожньо) | 176-211 | 78.5-89.5 | 40.5-42 | free |
| hdmi_route_front_rise | резерв (порожньо) | 171.7-186 | 78.5-89.5 | 40.5-51 | free |
| hdmi_fpc_disp | adafruit_3548 | 146.2-171.7 | 75-92.3 | 45.5-50.5 | free |
| hatch_parts | — | 116-138 | 40-90 | 2.5-13.5 | rear_wall |
| edl_key_body | pv6_button | 119-135 | 72-88 | 13.5-28.1 | rear_wall |
| t7_gland_body | — | 143-157 | 59-73 | 2.5-15.5 | rear_wall |
| t7_gland_outside | — | 143-157 | 59-73 | -15-0 | outside |
| v4l_a | v4l | 99.2-194.2 | 99.1-126.1 | 4.1-17.1 | rf_lid |
| v4l_b | v4l | 99.2-194.2 | 126.6-153.6 | 4.1-17.1 | rf_lid |
| sawbird | sawbird_noaa | 17.6-91.3 | 99.1-129.7 | 4.1-22.8 | rf_lid |
| flamingo | flamingo_fm | 17.6-91.3 | 130.2-160.8 | 4.1-22.8 | rf_lid |
| usb_socket_a | wurth_614004190021 | 194.2-209.1 | 99.1-121.1 | 4.1-17.1 | rf_lid |
| usb_socket_b | wurth_614004190021 | 194.2-209.1 | 126.6-148.6 | 4.1-17.1 | rf_lid |
| usb_lead_b | резерв (порожньо) | 202.1-208.6 | 99.1-126.6 | 17.6-22.1 | free |
| RF.r0 | RF | 17.6-201.6 | 99-143.5 | 28.4-35.5 | plate_rear |
| ina228 | adafruit_ina228_5832 | 28.5-54.3 | 44.48-64.8 | 6-16.1 | rear_wall |
| swm_2813 | pololu_2813 | 93.3-113.62 | 39-64.4 | 5.5-15.6 | rear_wall |
| gx16 | gx16_socket | 165-185 | 15-35 | 2.5-24.5 | rear_wall |
| pwr_key_body | pv6_button | 147.5-163.5 | 140.8-161.3 | 42-58 | front_wall |
| nut.PWR_KEY | — | 144.5-166.5 | 157.8-161.3 | 39-61 | front_wall |
| hub_ch334f | adafruit_5997 | 55.3-86.92 | 39-59.32 | 6-13.3 | rear_wall |
| veml7700 | adafruit_4162 | 107.3-137.7 | 157.5-161.3 | 49.28-67.06 | front_wall |
| t7_insert | t7_insert_board | 142-163.5 | 49.1-58.1 | 3-11.5 | free |
| pack_fuse | pack_fuse_carrier | 163.7-170.4 | 16.7-32.7 | 48.1-64.27 | plate_front |
| pack_fuse_board | pack_fuse_carrier | 161.7-172.4 | 11.5-37.9 | 46.5-50 | plate_front |
| boni_a406 | boni_a406 | 106-136 | 99.6-125.6 | 17.6-27.4 | free |
| ntc_panel | ntc_mf52a | 164.5-168.5 | 98.9-101.1 | 58.38-60.58 | display |
| ntc_case | ntc_mf52a | 165-169 | 24-26.2 | 40.5-42.7 | plate_front |
| nut.P1 | — | 38.88-48.12 | 155.9-159.3 | 25.38-34.62 | angle |
| nut.P2 | — | 58.88-68.12 | 155.7-159.3 | 25.38-34.62 | angle |
| nut.P3 | — | 78.88-88.12 | 155.7-159.3 | 25.38-34.62 | angle |
| nut.P4 | — | 97.15-109.85 | 152-159.3 | 23.65-36.35 | angle |
| nut.P6 | — | 138.88-148.12 | 155.7-159.3 | 25.38-34.62 | angle |
| nut.P7 | — | 158.4-168.6 | 155.9-159.3 | 24.9-35.1 | angle |
| nut.P8 | — | 178.88-188.12 | 155.7-159.3 | 25.38-34.62 | angle |
| nut.RX1 | — | 198.4-208.6 | 155.9-159.3 | 24.9-35.1 | angle |
| nut.RX2 | — | 222.1-225.5 | 136.9-147.1 | 24.9-35.1 | angle |
| nut.REF_IN | — | 222.1-225.5 | 116.9-127.1 | 24.9-35.1 | angle |
| nut.J551 | — | 218-227.5 | 99.7-112.3 | 23.7-36.3 | angle |
| nut.LAB_BUS | — | 197.57-214.43 | 2.5-13.3 | 20.07-36.93 | angle |

## Друковані деталі: верхня межа маси

solid CAD volume x 1.13 g/cm3 (PolyLite ASA, ISO 1183); real prints with 30 % infill weigh less

| деталь | об'єм, cm³ | g (суцільна) |
|---|---|---|
| front_shell | 168.02 | 190 |
| rear_shell | 129.51 | 146 |
| hatch_cover | 5.68 | 6 |
| hood | 15.87 | 18 |
| battery_tray | 23.26 | 26 |
| t7_holder | 29.23 | 33 |
| display_clamp_x4 | 0.29 | 0 |
| button_cap_x4 | 0.79 | 1 |
| button_cap_ribbed_x2 | 0.8 | 1 |
| main_knob | 9.22 | 10 |
| mandrel_hrpt_4t | 134.86 | 152 |
| mandrel_sband_7t | 129.09 | 146 |
| lnb_neck_adapter | 22.25 | 25 |
| lnb_throat_ring | 10.76 | 12 |
| horn_ring_127 | 7 | 8 |
| horn_ring_180 | 9.94 | 11 |
| yagi_tape_clamp | 4.92 | 6 |
| yagi_de_clamp | 15.87 | 18 |
| yagi_boom_spigot | 11.72 | 13 |
| imu_carrier | 6.28 | 7 |
