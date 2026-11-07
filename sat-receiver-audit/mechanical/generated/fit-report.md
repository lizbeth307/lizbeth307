# Звіт посадки механічної моделі SR-RX-v2.1

Згенеровано `mechanical/build.py` (params 8c4e291cf3a1); не редагувати вручну. **MODEL FIT ONLY:** це перевірка конвертів і даних з даташитів, а не примірка деталей. Фізичні ворота посадки, ущільнення, тепла й падіння лишаються OPEN.

## Габарит

| | модель | D15 |
|---|---|---|
| Ш x В x Г, мм | 230 x 160 x 66 | 222.5 x 137.5 x 57.5 |
| об'єм, L | 2.43 | 1.76 |
| поверхня, m² | 0.1251 | 0.1026 |
| лице, m² | 0.0368 | 0.0306 |
| над поясом шва, мм | 233.8 x 163.8 x 66 | — |
| мішок 23 x 30 см (W+D ≤ 300, H+D ≤ 230; D — глибина закритого пристрою з усіма виступами, 98 мм) | 331.8 / 261.8: FAIL (model): charge on a non-flammable surface instead (STACK 5.8 fallback) | — |

Глибина закритого пристрою (козирок складено, штекери вийнято), z від задньої зовнішньої грані:

- strap lugs and tunnels: z -6
- tripod plinth: z -5
- T7 holder: z -14
- T7 gland outside (assumption): z -15
- front face: z 66
- hood hinge knuckles (hood folded on them): z 72
- main knob: z 83
- volume knob (Adafruit 2055): z 79.5

Разом z -15…83; без тримача T7 — 98 мм. Не враховано: GX16 cap, SMA/F/BNC caps and screw heads on the T7 holder are not counted (parts not chosen).

## Підсумок

- зіткнень конвертів: 0; поза внутрішнім об'ємом: 0
- правила: FAIL 0, OPEN 5 (OPEN = потрібна обрана або виміряна деталь)
- антенні деталі за правилом розміру: FAIL 0; площа плат (деталі без роз'ємів джгутів): FAIL 0; з роз'ємами джгутів build/16: OPEN 2 (оцінка, не в гейті до перерозкладки хвилі 2)
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
| R-SMA-THREAD | bulkhead thread through ASA wall + Al angle with O-ring, lock washer and nut, >= 3 full threads left (1/4-36: 3 x 0.706 mm) | 4.5 | thread length of the chosen bulkhead >= wall + O-ring + washer + nut + 2.1 | OPEN: bulkhead/pigtail MPN and its thread length not chosen (MECH-07); the representative Samtec SMA-J-C-X-ST-BH4 takes a 3.8 mm panel at most, less than this 4.5 mm wall: choose a long-thread bulkhead |
| R-BULKHEAD-NUTS | nut and lock washer of every panel bulkhead inside the wall clear of the RF-bay walls and parts (envelope check) | SMA: washer d 10.15, 2.5 thick (layout nut.*) |  | OPEN: hardware of P4, P5 not chosen (MPN TBD), no nut envelope |
| R-PWR-PADS | PWR thermal-pad zones clear of the screw keep-outs (margin, worst pair) | 0.5 | 0 | PASS (model) |
| R-HOLE-EDGE | plate holes: centre-to-edge distance minus the hole diameter (worst hole) | 0.1 | 0 | PASS (model) |
| R-CLINCH-EDGE | self-clinching nut/standoff: hole centre to the nearest plate edge or window (worst hole) | 6 | 6 | PASS (model) |
| R-SEAM-HOLES | closure insert holes inboard of the seam groove (wall left between hole and groove, worst boss) | 0.9 | 0.9 | PASS (model) |
| R-VENT-SEAT | vent seats: threaded hole >= 4.0 mm, or 2.0-3.5 mm through hole with the nut | {'V1': 4.0, 'V2': 4.0} | {'threaded': 4.0, 'through': [2.0, 3.5]} | PASS (model) |
| R-VENT-REACH | space behind each vent seat minus the thread reach (worst vent) | 1.8 | 0.5 | PASS (model) |
| R-PANEL-FLAT | side-face cut-outs on the flat face and clear of the seam belt (split plane +- 5.5 mm) | none |  | PASS (model) |
| R-PWR-KEY | E-Switch PV6F240SS panel thickness at the power key (top wall) and at SW501 (hatch board 1.6 mm) | 2.5 / 1.6 | 1 / 10 | PASS (model) |
| R-PWR-KEY-NUT | PV6 panel nut inside the top wall clear of the HDMI board, the display clamp bosses and the top Al angle | {'key_x': 155.5, 'key_z': 48.5, 'nut_d_assumed': 20.0} |  | OPEN: the PV6 datasheet gives no nut size; a D20 nut (assumption) at x 155.5 / z 48.5 would reach the HDMI board edge (x 146.2) and the top-right display clamp boss (z >= 56.5): measure the received nut; if it does not clear, re-place the key (wave 2 layout) |
| R-PLATE-SLOTS | plate harness slots inside the outline with a web >= 1.5 mm to the outline and to every other opening (worst slot) | 1.5 | 1.5 | PASS (model) |
| R-PWR-MODULES | modules on a board (height + mount standoff) inside the board envelope height there (worst module) | 10.17 | 10.5 | PASS (model) |
| R-COOLER-A | cooler A: Cu block inside the 32 x 31 keep-in and over SoC + LPDDR5 (cover margin >= 0.5); fan face >= the keep-in minimum and above the 40-pin and 2x2 headers | {'cover_margin': 0.97, 'fan_face_above_board': 10.5, 'tallest_header': 9.65} | {'cover_margin': 0.5, 'fan_face_above_board': 10.0} | PASS (model) |
| R-VENT-FOAM | battery vent: the thread ends in the 3 mm foam layer, so the foam has a hole >= thread d + 0.5 at the vent | {'V2': 13.0} | 12.5 | PASS (model) |
| R-HDMI-ROUTE | HDMI cable Q6A to HDMI board: keep-clear route in the envelope check (plug head, bends, plate notch, run) | {'cable_od': 5.2, 'bend_r': 8.0} |  | OPEN: the route needs a right-angle plug at the Q6A (MPN TBD) and has no 20 mm deep space for the two Fair-Rite 0431164281 snap ferrites (39.5 x 20 x 19.6) or for the S-fold of about 250 mm of excess cable: rule R-HDMI-ROUTE OPEN; proposed default (build/15 'Оболонка D15', 2026-11-07): STACK's FPC reserve Adafruit 3550 (right angle) + 3548 + 3560 with a grounded copper-tape wrap; MPN, length and a ferrite for the flat cable TBD until the Adafruit pages are read |
| R-TOOL-ACCESS | every closure, hatch and T7-holder screw: clear tool path (counterbore, then d 8.0 for 60 mm) from outside | CLOSURE_1: remove t7_holder first / CLOSURE_2: remove t7_holder first | no fixed solid in a tool path; removable parts only over closure screws | PASS (model) |
| R-TRIPOD-DISC | tripod plate disc d 50.0 about the 1/4-20: no solid prouder than the plinth face (5.0 mm) | none | plinth d 23.0, 5.0 proud | PASS (model) |

## РЧ-відсік: донгли V4L, розетки USB-подовжувачів і модулі LNA

Внутрішній розмір кришки 192.5 x 58.9 мм; резерви: V4L 95 / 27 / 13, розетка 40 / 16 / 9 (припущення), корпус LNA 73.7 / 30.6.

- layout (two dongles in one row): ряд 270 мм
- alternative (dongle + socket + LNA case per row): ряд 208.7 мм
- висота двох рядів у варіанті «донгл + розетка + LNA»: 61.2 мм

Результат: OPEN: the female USB ends of the two V4L leads are not inside the modelled bay; with the current reserves neither arrangement fits (measure the V4L and the socket, then re-pack or move the cased LNA modules out of the bay)

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
| T-PWR3 | PWR board bottom copper to the plate, zone 3 | Gelid GP-Ultimate pad | 0.4 ± 0.05 | 0.5 (TP-GP04-A) | 10-30 % | 30 x 30 | PASS (model) |
| T-PWR4 | PWR board bottom copper to the plate, zone 4 | Gelid GP-Ultimate pad | 0.4 ± 0.05 | 0.5 (TP-GP04-A) | 10-30 % | 30 x 30 | PASS (model) |
| T-KSD9700 | KSD9700 70 C NO on the hottest IP2368 MOSFET | polyimide tape + thermally conductive adhesive | — | — | — | — | OPEN: adhesive product and its datasheet not chosen in this package (STACK 5.6 gives only the polyimide layer) |
| T-NTC | pack NTC on the middle cell (E3-06) | polyimide tape | — | — | — | — | OPEN: attachment product not chosen in this package |

Розкрій листів 90 x 50:

- 0.5 мм: 2 лист(и): T-PWR1 60x23 (лист 1), T-PWR2 56x23 (лист 1), T-PWR3 30x30 (лист 2), T-PWR4 30x30 (лист 2)
- 1.0 мм: 1 лист(и): T-LIME 60x22 (лист 1), T-UFS 16.5x11.5 (лист 1), T-LPDDR5 15x12.4 (лист 1)

## Ущільнення шва і гвинти

EPDM-шнур ⌀2 у пазу 2.6 x 1.55 у зовнішньому поясі 1.9 мм: стиск 22 %, заповнення 78 % — PASS (model); довжина по осі паза 754 мм, замовити 800 мм.

Гвинтів шва 14, середній проліт 55.7 мм, найдовший 121 мм (лівий нижній кут: батарея й екран HF+ доходять до стінок, бобишка не вміщується; рішення — стенд T-07). Доступ інструмента до кожного гвинта — рядок R-TOOL-ACCESS (гвинти 1 і 2 — після зняття тримача T7, який кріпиться ззовні).

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

## Тісні місця (зазор < 0.5 мм, модель)

- display ↔ pwr_key_body: 0 мм
- CTRL.r0 ↔ plate.boss2: 0.4 мм
- q6a.board ↔ closure.boss6: 0.4 мм
- hatch_parts ↔ edl_key_body: 0 мм
- v4l_a ↔ rfbay.wall.bottom: 0.4 мм
- v4l_b ↔ rfbay.wall.bottom: 0.4 мм
- RF.r0 ↔ rfbay.wall.bottom: 0.4 мм
- pwr_key_body ↔ plate.main: 0 мм

## Плати: механічний інтерфейс (contract/boards.json)

| плата | домени pcb/prepare.py | контур, мм² | отвори | висота деталей | розміщення | кріплення |
|---|---|---|---|---|---|---|
| PWR | PWR_MAIN, PWR_BRANCH, USB_POWER | 7910 | 7 x ⌀3.2 | ≤9 | default: (6, 38.5) z 40.9 +z | plate front face; Gelid 0.5 mm pads under the thermal_bond zones, gap 0.4 mm set by shim washers (mechanical.json pwr_bond) |
| RF | RF_HMC, RF_HF, RF_INJECTOR, DC_CORE | 8188 | 6 x ⌀3.2 | ≤5.5 | default: (17.6, 99) z 35.5 -z | PEM SO-M3-3 thru-hole standoffs (3 mm) clinched into the plate, heads flush with the plate front face; single RF GND/CHASSIS bond at BOND-RF |
| CTRL | CTRL_HMI | 5915 | 6 x ⌀2.7 | ≤5.5 | default: (176, 13) z 54.9 +z | M2.5 screws into CNC Kitchen TC-M2,5x4 inserts in the front-shell bosses |
| ENC | ENC | 576 | 2 x ⌀2.7 | ≤6.5 | main: (188.5, 123) z 54.3 +z; volume: (188.5, 82) z 54.3 +z | 2x M2.5 into CNC Kitchen TC-M2,5x4 inserts in the front-shell bosses |

## Площа плат: деталі і роз'єми джгутів (оцінка, модель)

courtyard estimate per footprint class x 1.8 placement density (model, not a placement); courtyard w x d per header (parts.json harness_headers) x 1.8 placement density, added to the parts estimate; frontage = sum of header widths against the edge zones of boards.json (every header at an edge, cable leaving sideways).

MODEL ESTIMATE: reported, not gated (OPEN = the outline or the harness architecture needs a wave-2 decision)

| плата | контур, мм² | деталі (без джгутів), мм² | результат | роз'ємів джгутів | з роз'ємами, мм² | ширина роз'ємів / крайові зони, мм | результат |
|---|---|---|---|---|---|---|---|
| PWR | 7910 | 7597 | PASS (model) | 32 | 12461 | 396 / 233 | OPEN: area 12461 > 7910 mm2; frontage 396 > 233 mm of edge zones (model estimate; re-plan the board outline or fewer/denser headers — wave 2) |
| RF | 8188 | 2787 | PASS (model) | 4 | 3640 | 57 / 344 | PASS (model) |
| CTRL | 5915 | 3049 | PASS (model) | 20 | 7697 | 309 / 145 | OPEN: area 7697 > 5915 mm2; frontage 309 > 145 mm of edge zones (model estimate; re-plan the board outline or fewer/denser headers — wave 2) |
| ENC | 576 | — | — | 2 | 169 | 11 / 12 | PASS (model) |

## Розташування конвертів (мм; x вправо, y вгору з лиця, z від задньої зовнішньої грані)

| ID | деталь / плата | x | y | z | кріплення |
|---|---|---|---|---|---|
| battery_tray | — | 3.1-161.2 | 4.55-37.95 | 4-58.4 | free |
| battery_pack | battery_pack | 7.3-157.3 | 8.75-33.75 | 8.2-54.2 | free |
| display | display_module | 6.3-170.52 | 50.3-148.28 | 56.5-62.5 | front_wall |
| hdmi_board | hdmi_board | 50-146.2 | 75-157 | 45-56 | plate_front |
| PWR.r0 | PWR | 6-142 | 38.5-73.5 | 40.9-51.5 | plate_front |
| PWR.r1 | PWR | 6-48 | 73.5-148.5 | 40.9-53 | plate_front |
| blower | blower | 144-174.5 | 38.5-69 | 45-55.5 | plate_front |
| CTRL.r0 | CTRL | 176-226 | 13-81.5 | 54.9-62 | front_wall |
| CTRL.r1 | CTRL | 176-188 | 81.5-147.5 | 54.9-62 | front_wall |
| CTRL.r2 | CTRL | 213-226 | 81.5-147.5 | 54.9-62 | front_wall |
| CTRL.r3 | CTRL | 176-226 | 106.5-122.5 | 54.9-62 | front_wall |
| CTRL.r4 | CTRL | 176-216 | 147.5-157 | 54.9-62 | front_wall |
| CTRL.r5 | CTRL | 216-226 | 147.5-150 | 54.9-62 | front_wall |
| ENC.r0 | ENC | 188.5-212.5 | 123-147 | 54.3-62.4 | front_wall |
| ENC.r0 | ENC | 188.5-212.5 | 82-106 | 54.3-62.4 | front_wall |
| bms | daly_bms | 175-210 | 9-70 | 41-51 | plate_front |
| ip2368 | ip2368_board | 172-220 | 122.5-156.5 | 41-51 | plate_front |
| lime | lime | 147-227 | 96-122 | 40.5-53.5 | plate_front |
| hfplus | hfplus_can | 2.6-114.6 | 38.5-94.5 | 17.5-38.5 | plate_rear |
| lc76g | lc76g | 8-71.6 | 38.5-92.5 | 3-16.1 | rear_wall |
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
| hdmi_plug_ra | резерв (порожньо) | 186.5-211 | 24-36.2 | 22.2-33.2 | free |
| hdmi_route_rear | резерв (порожньо) | 211-221.8 | 27.2-32.8 | 25-38.5 | free |
| hdmi_route_front_up | резерв (порожньо) | 216.2-221.8 | 27.2-76.8 | 40.5-51.3 | free |
| hdmi_route_front_turn | резерв (порожньо) | 210.8-221.8 | 66-76.8 | 45.7-51.3 | free |
| hdmi_route_front_run | резерв (порожньо) | 146.2-221.8 | 71.2-76.8 | 45.7-51.3 | free |
| hatch_parts | — | 116-138 | 40-90 | 2.5-13.5 | rear_wall |
| edl_key_body | pv6_button | 119-135 | 72-88 | 13.5-28.1 | rear_wall |
| t7_gland_body | — | 143-157 | 59-73 | 2.5-15.5 | rear_wall |
| t7_gland_outside | — | 143-157 | 59-73 | -15-0 | outside |
| v4l_a | v4l | 17.6-112.6 | 99-126 | 4.1-17.1 | rf_lid |
| v4l_b | v4l | 114.1-209.1 | 99-126 | 4.1-17.1 | rf_lid |
| sawbird | sawbird_noaa | 17.6-91.3 | 126.5-157.1 | 4.1-22.8 | rf_lid |
| flamingo | flamingo_fm | 100.9-174.6 | 126.5-157.1 | 4.1-22.8 | rf_lid |
| RF.r0 | RF | 17.6-201.6 | 99-143.5 | 28.4-35.5 | plate_rear |
| gx16 | gx16_socket | 165-185 | 15-35 | 2.5-24.5 | rear_wall |
| pwr_key_body | pv6_button | 147.5-163.5 | 137-157.5 | 40.5-56.5 | front_wall |
| nut.P1 | — | 38.42-48.58 | 153-155.5 | 24.93-35.08 | angle |
| nut.P2 | — | 58.42-68.58 | 153-155.5 | 24.93-35.08 | angle |
| nut.P3 | — | 78.42-88.58 | 153-155.5 | 24.93-35.08 | angle |
| nut.P6 | — | 138.43-148.57 | 153-155.5 | 24.93-35.08 | angle |
| nut.P7 | — | 158.43-168.57 | 153-155.5 | 24.93-35.08 | angle |
| nut.P8 | — | 178.43-188.57 | 153-155.5 | 24.93-35.08 | angle |
| nut.RX1 | — | 198.43-208.57 | 153-155.5 | 24.93-35.08 | angle |
| nut.RX2 | — | 223-225.5 | 136.93-147.07 | 24.93-35.08 | angle |
| nut.REF_IN | — | 223-225.5 | 116.92-127.08 | 24.93-35.08 | angle |

## Друковані деталі: верхня межа маси

solid CAD volume x 1.13 g/cm3 (PolyLite ASA, ISO 1183); real prints with 30 % infill weigh less

| деталь | об'єм, cm³ | g (суцільна) |
|---|---|---|
| front_shell | 157.89 | 178 |
| rear_shell | 126.02 | 142 |
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
