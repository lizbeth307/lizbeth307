# Звіт посадки механічної моделі SR-RX-v2.1

Згенеровано `mechanical/build.py` (params 849d6e2620a0); не редагувати вручну. **MODEL FIT ONLY:** це перевірка конвертів і даних з даташитів, а не примірка деталей. Фізичні ворота посадки, ущільнення, тепла й падіння лишаються OPEN.

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
- правила: FAIL 0, OPEN 9 (OPEN = потрібна обрана або виміряна деталь)
- антенні деталі за правилом розміру: FAIL 0; площа плат (курт'ярди KiCad, деталі без роз'ємів джгутів): OPEN 1; з роз'ємами джгутів build/16: OPEN 2 (MODEL ESTIMATE, не в гейті; рішення — розбиття й розкладка плат)
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
| R-PLATE-SLOT-FILL | harness wires through each plate slot (build/16-dzhgut.csv rows of the slot segments) against the bare opening | {'SL1': {'opening_mm2': 79.2, 'wires': 29, 'wires_per_awg': {'28': 29}}, 'SL2': {'opening_mm2': 63.0, 'wires': 51, 'wires_per_awg': {'20': 12, '24': 18, '26': 21}}, 'SL3': {'opening_mm2': 67.5, 'wires': 17, 'wires_per_awg': {'20': 4, '24': 6, '26': 7}}} | bundle OD with edge trim inside the opening | OPEN: wire outer diameter (AI-WIRE-PTFE) and edge-trim profile (AI-EDGE-TRIM) not chosen, so the fill is not checked (SL1 carries the whole 40-way S01 ribbon as two stacked 20-way halves; build/16 rows count only its connected conductors); resize SL1/SL2 or add a slot once both are read (wave 2) |
| R-PWR-MODULES | modules on a board (height + mount standoff) inside the board envelope height there (worst module) | 10.17 | 10.5 | PASS (model) |
| R-COOLER-A | cooler A: Cu block inside the 32 x 31 keep-in and over SoC + LPDDR5 (cover margin >= 0.5); fan face >= the keep-in minimum and above the 40-pin and 2x2 headers | {'cover_margin': 0.97, 'fan_face_above_board': 10.5, 'tallest_header': 9.65} | {'cover_margin': 0.5, 'fan_face_above_board': 10.0} | PASS (model) |
| R-VENT-FOAM | battery vent: the thread ends in the 3 mm foam layer, so the foam has a hole >= thread d + 0.5 at the vent | {'V2': 13.0} | 12.5 | PASS (model) |
| R-HDMI-ROUTE | HDMI cable Q6A to HDMI board: keep-clear route in the envelope check (plug head, bends, plate notch, run) | {'cable_od': 5.2, 'bend_r': 8.0} |  | OPEN: the route needs a right-angle plug at the Q6A (MPN TBD) and has no 20 mm deep space for the two Fair-Rite 0431164281 snap ferrites (39.5 x 20 x 19.6) or for the S-fold of about 250 mm of excess cable: rule R-HDMI-ROUTE OPEN; proposed default (build/15 'Оболонка D15', 2026-11-07): STACK's FPC reserve Adafruit 3550 (right angle) + 3548 + 3560 with a grounded copper-tape wrap; MPN, length and a ferrite for the flat cable TBD until the Adafruit pages are read |
| R-PPS-LEN | PPS path Q6A J20.7 -> LC76G: harness length <= 200 mm (STACK 5.2 'UART7/PPS wiring <= 20 cm'; E3 J301 note) | {'via_segments_mm': 329, 'branch_mm': 196} | 200 | OPEN (end provisional): S01+S25 = 329 mm > 200: decision (build/15 W2 MECH-1) — PPS + UART6 + GND branch off the S01 ribbon at the Q6A end and run directly to the LC76G in the rear layer (harness only, E3 nets unchanged; build/15 W2 MECH-1); branch PPS = 196 mm <= 200 (model; ends on board edge zones / envelope faces until the header and pin positions are placed) |
| R-ROUTE-CLEAR | harness route centrelines (mechanical.json harness_routes) clear of every envelope, keep-clear reserve and structure part; plate and RF-bay wall only through openings | {'routed': 33, 'clear': 33, 'provisional_end': 33, 'no_route_unplaced_end': ['S06', 'S07', 'S36', 'S39', 'S40'], 'external': ['S33', 'S41'], 'crossing': []} |  | OPEN (end provisional): every routed centreline clears the envelopes and structure; 33 of 33 routes end on a board edge zone or at a module without an envelope (header positions, module envelopes and the bundle OD (AI-WIRE-PTFE) TBD); no route yet (end not placed): S06, S07, S36, S39, S40; routes through a plate slot that plate.slots does not list (R-PLATE-SLOT-FILL undercounts): SL1: S27 |
| R-HDR-HEIGHT | board-side harness headers (build/16 §4) inside the board height limit, or in a computed height zone (component side) / rear zone | {'above_limit': ['X01I1-CTRL IDC_top 9.1', 'X02P1-CTRL MF_top 9.9', 'X02P1-PWR MF_top 9.9', 'X04P1-PWR MF_top 9.9', 'X04P1-RF MF_top 9.9', 'X11P1-PWR MF_top 9.9', 'X12P1-PWR MF_top 9.9', 'X13P1-PWR MF_top 9.9', 'X14P1-PWR MF_top 9.9', 'X17P1-PWR MF_top 9.9', 'X18P1-PWR MF_top 9.9', 'X19P1-PWR MF_top 9.9', 'X25P1-CTRL MF_top 9.9', 'X28P1-CTRL MF_top 9.9', 'X32P1-PWR MF_top 9.9'], 'height_not_read': ['X05J1-PWR', 'X06J1-PWR', 'X07J1-PWR', 'X10J1-PWR', 'X27F1-CTRL']} | {'PWR': 9.0, 'RF': 5.5, 'CTRL': 5.5, 'ENC': 6.5} | OPEN: GR-3 decides (header orientation, board side or board): 15 headers above their board limit (X01I1-CTRL IDC_top 9.1, X02P1-CTRL MF_top 9.9, X02P1-PWR MF_top 9.9, X04P1-PWR MF_top 9.9, X04P1-RF MF_top 9.9, X11P1-PWR MF_top 9.9, X12P1-PWR MF_top 9.9, X13P1-PWR MF_top 9.9, X14P1-PWR MF_top 9.9, X17P1-PWR MF_top 9.9, X18P1-PWR MF_top 9.9, X19P1-PWR MF_top 9.9, X25P1-CTRL MF_top 9.9, X28P1-CTRL MF_top 9.9, X32P1-PWR MF_top 9.9); 5 heights not read; right-angle Micro-Fit 6.98 mm does not fit the CTRL component side (best zone 6.5 mm) |
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

## Площа плат: курт'ярди KiCad і роз'єми джгутів (MODEL ESTIMATE)

Джерело: KiCad 10.0.7 courtyards (build/kicad/footprints/manifest.json). Метод: sum of the vendored KiCad 10.0.7 F.CrtYd courtyards (bbox; polygon area for a single fp_poly) of the bare board parts of pcb/generated/components.csv (DNP excluded) per board domain; need = modules (mount pcb_module) x 1.0 + other parts x fill factor 1.5 or 1.8 (1.8 = planning value) — MODEL ESTIMATE, not a placement; роз'єми: header courtyard w x d (vendored KiCad 10.0.7 footprint where that pin count exists, else parts.json harness_headers) x fill factor 1.5 or 1.8, added to the parts need; frontage = sum of header widths against the edge zones of boards.json (every header at an edge, cable leaving sideways); Mini-Fit Jr., IDC and FAN3 courtyards are assumptions (parts.json).

MODEL ESTIMATE: reported, not gated (OPEN = need at the planning factor exceeds the outline; the real placement decides); MODEL ESTIMATE: reported, not gated (OPEN = the outline or the harness architecture needs a wave-2 decision)

| плата | контур, мм² | курт'ярди деталей, мм² | з них модулі (×1.0), мм² | потреба ×1.5 / ×1.8, мм² | результат | роз'ємів джгутів | курт'ярди роз'ємів, мм² | з роз'ємами ×1.5 / ×1.8, мм² | ширина роз'ємів / крайові зони, мм | результат |
|---|---|---|---|---|---|---|---|---|---|---|
| PWR | 7910 | 6411 | 1342 | 8945 / 10466 | OPEN: need 10466 mm2 at fill 1.8 > outline 7910 mm2 (model estimate; partition and placement decide, AREA / PCB) | 32 | 2702 | 12999 / 15330 | 396 / 233 | OPEN: area 15330 > 7910 mm2 at fill 1.8; frontage 396 > 233 mm of edge zones (model estimate; re-plan the board outline or fewer/denser headers — wave 2) |
| RF | 8188 | 2056 | 0 | 3083 / 3700 | PASS (model estimate) | 4 | 474 | 3794 / 4553 | 57 / 344 | PASS (model estimate) |
| CTRL | 5915 | 3248 | 1221 | 4261 / 4869 | PASS (model estimate) | 22 | 2701 | 8312 / 9731 | 322 / 145 | OPEN: area 9731 > 5915 mm2 at fill 1.8; frontage 322 > 145 mm of edge zones (model estimate; re-plan the board outline or fewer/denser headers — wave 2) |
| ENC | 576 | — | — | — | — | 2 | 94 | 141 / 169 | 11 / 12 | PASS (model estimate) |

Курт'ярди деталей за групами схем (design/E*.json «group»), мм²:

- PWR: E1 LAB5 1149; E1 SYS12 753; E1 Сервісний заряд 119; E1 AON і UV 94; E1 Головний вимикач 92; E1 Захист USB-PD 43; E1 Інгібування заряду 26; E1 Аварійний ADC 13; E2 Boni: малошумна захищена шина 500; E2 LNB: малошумна захищена шина 410; E2 J21: захищене живлення 12 V 399; E2 LNA4V5: паралельні LT3045 352; E2 LNA: канал 2 247; E2 LNA: канал 3 247; E2 AUX12: верхній ключ і PTC 185; E2 Дисплей: захищене живлення 12 V 171; E2 Lime M.2: комутована шина 3.3 V 166; E2 LNA: канал 1 146; E2 LNA: канал 4 146; E2 RTL-B: комутований VBUS 136; E2 S-band LaNA WB: захищена шина 5 V 136; E2 INA3221: струми LNA1–3 67; E2 INA3221: струми LNA4, LNB і Boni 67; E2 LNB: незалежне точне відсікання OVP 46; E2 LNB: контроль напруги 31; E2 Boni: контроль напруги 31; E2 AUX12: контроль напруги після PTC 31; E5 VBUS HF+ з демпфованим LC 306; E5 VBUS RTL-A і LAB PORT 228; E5 LAB BUS I2C buffer 57; E5 Сервіс і зовнішні шини 14
- RF: E4 RF and receiver interfaces 20; E4 RF passives and drivers 31; E4 SP4T switches 54; E4 DC detectors: UHF 95; E4 DC detectors: LBAND 95; E4 DC detectors: HF 95; E4 RF bias injector local decoupling 18; E4 DC detectors: common reference 171; E4 DC detectors: local power 35
- CTRL: E3 Pico HMI 1287; E3 MCP23017 control 783; E3 HMI buttons 487; E3 Indicators 219; E3 Cooling 147; E3 Q6A header 120; E3 HMI encoders 66; E3 Pico power control 48; E3 Ambient sensor 31; E3 MCP hardware watchdog reset 26; E3 GNSS 17; E3 Thermal sensors 17

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
| CTRL | тил | 0, 0, 34 x 57 | 3.9 | 3.4 | bms |
| CTRL | тил | 34, 0, 9.5 x 5.5 | 14.4 | 13.9 | plate.ext |
| CTRL | тил | 43.5, 0, 6.5 x 5.5 | 0.4 | 0 | plate.boss2 |
| CTRL | тил | 34, 5.5, 16 x 8.7 | 14.4 | 13.9 | plate.ext |
| CTRL | тил | 34, 14.2, 6.2 x 11.3 | 14.4 | 13.9 | plate.ext |
| CTRL | тил | 40.2, 14.2, 5.6 x 49.6 | 3.6 | 3.1 | hdmi_route_front_up |
| CTRL | тил | 45.8, 14.2, 4.2 x 11.3 | 14.4 | 13.9 | plate.ext |
| CTRL | тил | 34, 25.5, 6.2 x 27.5 | 14.4 | 13.9 | plate.main |
| CTRL | тил | 45.8, 25.5, 4.2 x 38.3 | 14.4 | 13.9 | plate.main |
| CTRL | тил | 34, 53, 0.8 x 4 | 14.4 | 13.9 | plate.main |
| CTRL | тил | 34.8, 53, 5.4 x 10.8 | 3.6 | 3.1 | hdmi_route_front_turn |
| CTRL | тил | 0, 57, 34.8 x 1.2 | 14.4 | 13.9 | plate.main |
| CTRL | тил | 0, 58.2, 34.8 x 5.6 | 3.6 | 3.1 | hdmi_route_front_run |
| CTRL | тил | 0, 63.8, 50 x 4.7 | 14.4 | 13.9 | plate.main |
| CTRL | тил | 0, 68.5, 12 x 14.5 | 14.4 | 13.9 | plate.main |
| CTRL | тил | 37, 68.5, 13 x 14.5 | 14.4 | 13.9 | plate.main |
| CTRL | тил | 0, 83, 12 x 10.5 | 1.4 | 0.9 | lime |
| CTRL | тил | 37, 83, 13 x 10.5 | 1.4 | 0.9 | lime |
| CTRL | тил | 0, 93.5, 50 x 15.5 | 1.4 | 0.9 | lime |
| CTRL | тил | 0, 109, 50 x 0.5 | 14.4 | 13.9 | plate.main |
| CTRL | тил | 0, 109.5, 12 x 25 | 3.9 | 3.4 | ip2368 |
| CTRL | тил | 37, 109.5, 7 x 25 | 3.9 | 3.4 | ip2368 |
| CTRL | тил | 44, 109.5, 6 x 27.5 | 14.4 | 13.9 | plate.main |
| CTRL | тил | 0, 134.5, 44 x 2.5 | 3.9 | 3.4 | ip2368 |
| CTRL | тил | 0, 137, 40 x 6.5 | 3.9 | 3.4 | ip2368 |
| CTRL | тил | 0, 143.5, 40 x 0.5 | 14.4 | 13.9 | plate.main |
| RF | лице | 0, 0, 95 x 27 | 16.8 | 16.3 | v4l_a |
| RF | лице | 95, 0, 1.5 x 27 | 29.8 | 29.3 | rfbay.lid |
| RF | лице | 96.5, 0, 87.5 x 27 | 16.8 | 16.3 | v4l_b |
| RF | лице | 0, 27, 184 x 0.5 | 29.8 | 29.3 | rfbay.lid |
| RF | лице | 0, 27.5, 73.7 x 17 | 11.1 | 10.6 | sawbird |
| RF | лице | 73.7, 27.5, 9.6 x 17 | 29.8 | 29.3 | rfbay.lid |
| RF | лице | 83.3, 27.5, 73.7 x 17 | 11.1 | 10.6 | flamingo |
| RF | лице | 157, 27.5, 27 x 17 | 29.8 | 29.3 | rfbay.lid |
| RF | тил | 0, 0, 184 x 44.5 | 3 | 2.5 | plate.main |

Роз'єми джгутів понад обмеження плати або без прочитаної висоти (20 з 60; правило R-HDR-HEIGHT):

| роз'єм | плата | родина | висота, мм | курт'ярд, мм | межа плати | найкраща зона лиця / тилу, мм | висновок |
|---|---|---|---|---|---|---|---|
| X01I1-CTRL | CTRL | IDC top | 9.1 | 61 x 9 | 5.5 | 5.5 / 0 | above the board limit 5.5; fits no computed zone that takes its courtyard |
| X02P1-CTRL | CTRL | MF top | 9.9 | 16.66 x 6.77 | 5.5 | 6.5 / 3.4 | above the board limit 5.5; fits no computed zone that takes its courtyard |
| X02P1-PWR | PWR | MF top | 9.9 | 16.66 x 6.77 | 9 | 10.5 / 0 | above the board limit 9; fits a component-side height zone |
| X04P1-PWR | PWR | MF top | 9.9 | 10.66 x 6.77 | 9 | 10.5 / 0 | above the board limit 9; fits a component-side height zone |
| X04P1-RF | RF | MF top | 9.9 | 10.66 x 6.77 | 5.5 | 29.3 / 2.5 | above the board limit 5.5; fits a component-side height zone |
| X05J1-PWR | PWR | MFJ top | TBD | 11.7 x 13 | 9 | 10.5 / 0 | height of MFJ_top not read (TBD) |
| X06J1-PWR | PWR | MFJ top | TBD | 11.7 x 13 | 9 | 10.5 / 0 | height of MFJ_top not read (TBD) |
| X07J1-PWR | PWR | MFJ top | TBD | 11.7 x 13 | 9 | 10.5 / 0 | height of MFJ_top not read (TBD) |
| X10J1-PWR | PWR | MFJ top | TBD | 15.9 x 13 | 9 | 10.5 / 0 | height of MFJ_top not read (TBD) |
| X11P1-PWR | PWR | MF top | 9.9 | 10.66 x 6.77 | 9 | 10.5 / 0 | above the board limit 9; fits a component-side height zone |
| X12P1-PWR | PWR | MF top | 9.9 | 10.66 x 6.77 | 9 | 10.5 / 0 | above the board limit 9; fits a component-side height zone |
| X13P1-PWR | PWR | MF top | 9.9 | 10.66 x 6.77 | 9 | 10.5 / 0 | above the board limit 9; fits a component-side height zone |
| X14P1-PWR | PWR | MF top | 9.9 | 10.66 x 6.77 | 9 | 10.5 / 0 | above the board limit 9; fits a component-side height zone |
| X17P1-PWR | PWR | MF top | 9.9 | 10.66 x 6.77 | 9 | 10.5 / 0 | above the board limit 9; fits a component-side height zone |
| X18P1-PWR | PWR | MF top | 9.9 | 10.66 x 6.77 | 9 | 10.5 / 0 | above the board limit 9; fits a component-side height zone |
| X19P1-PWR | PWR | MF top | 9.9 | 10.66 x 6.77 | 9 | 10.5 / 0 | above the board limit 9; fits a component-side height zone |
| X25P1-CTRL | CTRL | MF top | 9.9 | 10.66 x 6.77 | 5.5 | 6.5 / 13.9 | above the board limit 5.5; fits a rear zone (THT from the back) |
| X27F1-CTRL | CTRL | FAN3 top | TBD | 10.08 x 6 | 5.5 | 6.5 / 13.9 | height of FAN3_top not read (TBD) |
| X28P1-CTRL | CTRL | MF top | 9.9 | 10.66 x 6.77 | 5.5 | 6.5 / 13.9 | above the board limit 5.5; fits a rear zone (THT from the back) |
| X32P1-PWR | PWR | MF top | 9.9 | 10.66 x 6.77 | 9 | 10.5 / 0 | above the board limit 9; fits a component-side height zone |

## Траси джгутів (модель, generated/harness-routes.json)

Осьова лінія кожного сегмента build/16 крізь модель корпусу (mechanical.json harness_routes): довжина = ламана + запас на вигини (половина діаметра джгута × кут) + 2 × 15 мм сервісних петель, округлено вгору до 1 мм. Діаметр джгута — верхня межа за кількістю жил build/16 і найбільшою ізоляцією, яку беруть клеми (дріт не обрано, AI-WIRE-PTFE). Кінці на крайових зонах плат і біля модулів без конверту — попередні (OPEN), доки немає позицій роз'ємів. MODEL ESTIMATE, не виміряні довжини.

PPS (R-PPS-LEN): S01+S25 = 329 мм проти 200 мм; рішення — PPS + UART6 + GND branch off the S01 ribbon at the Q6A end and run directly to the LC76G in the rear layer (harness only, E3 nets unchanged; build/15 W2 MECH-1); гілка PPS = 196 мм.

| сегмент | тип | довжина, мм | ламана, мм | вигинів | ⌀ джгута, мм | прорізи | стан |
|---|---|---|---|---|---|---|---|
| S01 | harness | 102 | 66 | 3 | 2.54 | SL1 | OPEN (end provisional): CTRL header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S02 | harness | 189 | 80.5 | 6 | 16.55 | — | OPEN (end provisional): CTRL header position TBD (board layout; GR-3 header refs): end on the edge zone; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S03 | harness | 308 | 219.1 | 11 | 6.71 | SL2, N4 | OPEN (end provisional): CTRL header position TBD (board layout; GR-3 header refs): end on the edge zone; RF header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S04 | harness | 221 | 151.4 | 7 | 7.17 | SL2, N4 | OPEN (end provisional): PWR header position TBD (board layout; GR-3 header refs): end on the edge zone; RF header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S05 | harness | 35 | 4.8 | 0 | 6.93 | — | OPEN (end provisional): F101 carrier PACK_FUSE not modelled (mechanical/README): end on the pack top face; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S06 | harness | — | — | — | — | — | OPEN (end provisional): INA228 5832 has no envelope or place in the model yet (MECH-3) |
| S07 | harness | — | — | — | — | — | OPEN (end provisional): Pololu #2813 has no envelope or place in the model yet (MECH-3) |
| S10 | harness | 248 | 150.8 | 8 | 10.59 | — | OPEN (end provisional): PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S11 | harness | 229 | 175.6 | 6 | 4.78 | SL3 | OPEN (end provisional): behind-panel envelope of MUSBRM5C130 TBD (MECH-2): end at the port centre on the wall; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S12 | harness | 35 | 4.8 | 0 | 3.38 | — | OPEN (end provisional): XT30 pigtail place in the battery compartment TBD: end on the pack top face; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S13 | harness | 134 | 87.4 | 6 | 3.38 | SL2 | OPEN (end provisional): Adafruit 5997 has no envelope (mechanical/README): end below the Q6A USB stack (J2); PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S14 | harness | 68 | 34.8 | 1 | 3.38 | SL2 | OPEN (end provisional): hatch-board layout TBD (W2-05): end on the hatch-board envelope; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S15 | harness | 157 | 115.3 | 7 | 1.94 | SL2 | OPEN (end provisional): hatch-board layout TBD (W2-05): end on the hatch-board envelope; CTRL header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S16 | harness | 123 | 86.2 | 2 | 4.14 | — | OPEN (end provisional): hatch-board layout TBD (W2-05): J503 on the hatch-board envelope |
| S17 | harness | 66 | 27.6 | 3 | 3.38 | SL2 | OPEN (end provisional): VCC_3V3_MKEY tap on the Q6A not chosen (E5/E2; MECH-6 B-07): end at the Q6A board edge; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S18 | harness | 164 | 122.8 | 4 | 3.38 | SL2 | OPEN (end provisional): R44SF envelope TBD: end at the riser window (plate rear face); PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S19 | harness | 38 | 5 | 1 | 3.38 | — | OPEN (end provisional): barrel jack position on the Wisecoco HDMI board TBD (STACK D5): end on the board envelope; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S20 | harness | 156 | 115.2 | 5 | 2.74 | SL2, N2 | OPEN (end provisional): J543 pigtail (H2) place TBD: end at notch N2 of the RTL-A USB lead; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S21 | harness | 142 | 100.7 | 5 | 2.74 | SL2, N3 | OPEN (end provisional): J541 place TBD: end at notch N3 of the RTL-B USB lead; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S22 | harness | 55 | 19.2 | 2 | 3.35 | SL2 | OPEN (end provisional): J544 micro-USB pigtail exit on the HF+ can TBD: end on the can face; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S23 | harness | 242 | 193.3 | 7 | 3.35 | SL3 | OPEN (end provisional): behind-panel envelope of PX0845/A TBD (MECH-2): end at the port centre on the wall; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S24 | harness | 193 | 139 | 9 | 3.35 | SL2 | OPEN (end provisional): T7_INSERT envelope TBD (in the USB3 cable between Q6A J5 and the T7 gland): end beside the gland; CTRL header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S25 | harness | 227 | 159.5 | 8 | 5.85 | SL2 | OPEN (end provisional): P1 header position on the Waveshare 24370 board not read: end on the LC76G envelope face towards the route; CTRL header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S26 | harness | 97 | 63.6 | 1 | 3.87 | — | OPEN (end provisional): Adafruit 4162 envelope TBD: end at the bezel window on the top wall; CTRL header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S27 | stock_lead | 111 | 67.5 | 5 | 3.35 | SL1 | OPEN (end provisional): CTRL header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S28 | harness | 38 | 4.9 | 1 | 3.38 | — | OPEN (end provisional): CTRL header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S29 | harness | 72 | 32.9 | 4 | 2.74 | — | OPEN (end provisional): CTRL header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S30 | harness | 177 | 125.1 | 8 | 3.35 | SL2 | OPEN (end provisional): hatch-board layout TBD (W2-05): J502 on the hatch-board envelope; CTRL header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S31 | harness | 58 | 24.2 | 2 | 2.74 | — | OPEN (end provisional): J522 EDL contact pads on the Q6A not localised (E5 §9): end at the Q6A board edge |
| S32 | harness | 216 | 162.9 | 6 | 4.78 | SL3 | OPEN (end provisional): PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S33 | external | — | — | — | — | — | EXTERNAL: outside the enclosure; the length is set by the cable, not by the enclosure model |
| S34 | harness | 201 | 144.5 | 7 | 4.74 | SL3 | OPEN (end provisional): behind-panel envelope of KH-GX12-6P TBD (MECH-2): end at the port centre on the wall; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S35 | harness | 157 | 117.5 | 4 | 2.74 | SL2 | OPEN (end provisional): Boni-Whip bias-tee has no envelope (mechanical/README): end at the HF+ can top edge; PWR header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S36 | harness | — | — | — | — | — | OPEN (end provisional): pod power entry (J551 panel receptacle, GR-1) is not placed on a face yet (MECH-3) |
| S37 | harness | 31 | 0.8 | 0 | 3.87 | — | OPEN (end provisional): ENC header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S38 | harness | 31 | 0.8 | 0 | 3.87 | — | OPEN (end provisional): ENC header position TBD (board layout; GR-3 header refs): end on the edge zone |
| S39 | harness | — | — | — | — | — | OPEN (end provisional): TH301 place on the panel rear heat spreader TBD (MECH-6 B-10) |
| S40 | harness | — | — | — | — | — | OPEN (end provisional): TH302 place on the inner frame TBD (MECH-6 B-10) |
| S41 | external | — | — | — | — | — | EXTERNAL: outside the enclosure; the length is set by the cable, not by the enclosure model |
| PPS (гілка) | harness | 196 | 159.4 | 2 | 3.87 | — | OPEN (end provisional): P1 header position on the Waveshare 24370 not read: end at the centre of the LC76G top edge |

Прорізи пластини: SL1 — у plate.slots 1, трасами 2, поза списком: S27; SL2 — у plate.slots 14, трасами 14; SL3 — у plate.slots 4, трасами 4.

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
