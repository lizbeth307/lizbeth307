"""Curated assembly inputs for tools/build_assembly_docs.py (data only, no I/O).

Everything electrical (refs, pins, nets) comes from design/E[1-5].json and the
board partition in pcb/generated/components.csv; this file only adds what the
graphs cannot carry: where each purchased module or panel part physically sits,
which harness segments exist between those places, design currents with their
source, connector families (build/15), fasteners, labels, power states and the
assembly order. Values marked "модель" or "рішення asm" are design inputs, not
measurements; every catalogue value names the document that was read.
"""

READ = "24.10.2026"
# Sources (re)read later than READ, or values added from them later.
READ_ON = {"JST-PH": "07.11.2026", "JST-PHD": "07.11.2026", "MOLEX-43030": "06.11.2026", "MOLEX-5556": "06.11.2026", "MOLEX-5566": "06.11.2026",
           "ESCC-3901-001": "06.11.2026", "HAMMOND-1550Z101": "06.11.2026", "PV6": "07.11.2026", "KINGHELM-GX12": "07.11.2026",
           "PEM-F": "07.11.2026", "PEM-SO": "07.11.2026", "POLOLU-D36V50": "07.11.2026", "DIGIKEY-MFJ": "07.11.2026",
           "HAMMOND-1554U2GY": "24.10.2026 (креслення), 07.11.2026 (DigiKey DE)"}

# --- Sources actually read for catalogue values (URL, what it gives) --------
SOURCES = {
    "JST-PH": ("https://www.jst-mfg.com/product/pdf/eng/ePH.pdf",
               "JST PH: 2 A AC/DC (AWG #24) — інших перерізів номінал не наводить; 100 V, −40…+105 °C; опір контакту 10 mΩ макс. "
               "початково / 20 mΩ після тесту; провід AWG #32…#24, ізоляція ⌀0.5…1.5 мм; "
               "SPH-002T-P0.5S — AWG #30…#24, ⌀0.8…1.5 мм; PHR-2…PHR-16; B2B…B16B-PH-K-S (верхній вхід), S2B…S16B-PH-K-S (боковий); "
               "THT-вилки: довжина B = 2(n−1) + 3.9; верхній вхід — висота 6, глибина 4.5, монтажна висота з розеткою (8); боковий — висота 4.8, "
               "глибина 7.6, з розеткою (9.6) (каталог ePH, с. 1 і 3, PDF від 27.01.2026)"),
    "MOLEX-43030": ("https://www.farnell.com/datasheets/1887331.pdf",
                    "Molex 43030-0007 (пакет; 43030-0001 — котушка, https://www.farnell.com/datasheets/1864962.pdf): гніздова клема Micro-Fit 3.0, "
                    "20/22/24 AWG, ізоляція ≤1.85 мм, 5 A на контакт (документи 2014–2016; лист 2018 https://www.farnell.com/datasheets/2696325.pdf — 8.5 A); "
                    "ручний інструмент 0638190000, екстрактор 0011030043; переріз для номіналу й опір контакту не наведено"),
    "MOLEX-43645": ("https://docs.rs-online.com/0eff/A700000015719686.pdf",
                    "Micro-Fit 3.0 43645 — однорядна розетка, крок 3.00 мм, фіксатор (Lock to Mating Part: Yes), −40…+105 °C, "
                    "клеми 43030; відповідні вилки 43640, плати 43650. Перевірені коди: 436450508 (5 конт.), "
                    "0436450300 (3 конт., https://www.farnell.com/datasheets/2696565.pdf), 0436451000 (10 конт., https://static.rapidonline.com/pdf/05-3707_v1.pdf), "
                    "436451200 (12 конт., https://docs.rs-online.com/d89e/A700000013692998.pdf)"),
    "MOLEX-43650": ("https://docs.rs-online.com/c936/A700000014857364.pdf",
                    "Micro-Fit 3.0 43650 — вертикальна плата, 1 ряд; 436500317 (3 конт., Au, TH, 8.5 A на контакт, 600 V, −40…+125 °C) — "
                    "покриття Au, тому для клем Sn обирається варіант Sn (parts DB)"),
    "ESCC-3901-001": ("https://escies.org/download/specdraftapppub?id=4604",
                      "ESCC 3901/001 Issue 3 (березень 2024), табл. 1(b): Imax 1.5/2.5/3.5/5/7.5/10 A для AWG 28/26/24/22/20/18 "
                      "(нагрів ≈50 °C над середовищем у вакуумі); у джгуті IBmax = Imax·(29−n)/28 при 1<n<15, Imax/2 при n>15; "
                      "табл. 1(a): макс. опір жили 148/105/50.9/32.2/20.6 Ω/km для AWG 26/24/22/20/18 (одножильні варіанти 24–28; "
                      "AWG 26/24 — високоміцний сплав, AWG 28 одножильного варіанта немає)"),
    "MOLEX-5556": ("https://static.chipdip.ru/lib/677/DOC040677478.pdf",
                   "Molex 0039000060 (сторінка Molex від 15.07.2020; котушка — 39000059): гніздова клема Mini-Fit Jr. 5556, Sn по фосфористій "
                   "бронзі, 18/20/22/24 AWG, ізоляція ⌀1.30–3.10 мм, 9.0 A на контакт (переріз для номіналу не вказано), 600 V, 30 циклів; "
                   "«Use With … Receptacle Housing 5557»; ручний інструмент 638190901 (18–24 AWG), екстрактор 11030044; опору контакту немає"),
    "MOLEX-5566": ("https://www.farnell.com/datasheets/2695871.pdf",
                   "Molex 0039000079 (клема 5556 на 16 AWG, сторінка Molex від 19.10.2018): «Mates With … Mini-Fit Jr. Header, Dual Row, "
                   "5566, 5569»; «Use With 5557 Mini-Fit Jr. Receptacle Housing» — вилки на платі дворядні"),
    "DIGIKEY-MFJ": ("https://www.digikey.de/en/products/detail/molex/0039012020/61315",
                    "DigiKey DE, сторінки Molex Mini-Fit Jr.: 0039012020 — серія 5557, розетка (Female Socket), 2 позиції, 2 ряди, 4.20 мм, "
                    "WM3700-ND, EUR 0.24 @1, на складі 283 219; 0039012040 (https://www.digikey.de/en/products/detail/molex/0039012040/61376) — "
                    "5557, 4 позиції, 2 ряди, 4.20 мм, WM3701-ND, EUR 0.28 @1, на складі 156 876; 0039288020 "
                    "(https://www.digikey.de/en/products/detail/molex/0039288020/930296) — серія 5566, вертикальна вилка THT, 2 позиції, 2 ряди, "
                    "олово, WM23800-ND, EUR 0.69 @1, на складі 17 016; 0039288040 (пошук https://www.digikey.de/en/products/result?keywords=0039288040) — "
                    "5566, вертикальна вилка THT, 4 позиції, 2 ряди, олово, WM23801-ND, EUR 1.03 @1, склад не показано (термін виробника 14 тижнів); "
                    "кілочків PCB, номінал струму й посадкового місця сторінки не дають"),
    "HAMMOND-1554U2GY": ("https://www.hammfg.com/files/parts/pdf/1554U2GY.pdf",
                         "Hammond 1554U2GY (REV 28.02.2020, прочитано пакетом механіки 24.10.2026, mechanical/params/parts.json hammond_1554u2gy): "
                         "зовні 200 × 120 × 90.5, усередині 192.13 × 108.13 × 84.5; крок гвинтів кришки 187 × 107; вставки M3 під панель з кроком 176 × 45; "
                         "момент гвинтів кришки 30–40 cN·m; DigiKey DE 07.11.2026: HM1816-ND, EUR 33.97 @1, на складі 155 "
                         "(https://www.digikey.de/en/products/detail/hammond-manufacturing/1554U2GY/2359917); панель 1554UPL — сталь, 190.45 × 106.60, "
                         "до серій 1554/1555, HM3493-ND, EUR 11.50 @1, на складі 40"),
    "HAMMOND-1550Z101": ("https://www.hammfg.com/files/parts/pdf/1550Z101BK.pdf",
                         "Hammond 1550Z101/1550Z101BK (REV 08.07.2024): «Purchased assembly includes box, lid, silicone gasket, and 2 cover "
                         "screws»; гвинти кришки нержавіючі M4-0.7×20 мм; «Recommended Cover screw torque 5-7.5 lbf.in (50-75 cN.m)»"),
    "NASA-19990009916": ("https://ntrs.nasa.gov/citations/19990009916",
                         "Cable Bundle Wire Derating (1998): 20 AWG — 3.7 A на провід у джгуті ≥15 проводів, 70 °C, вакуум (перехресна перевірка ESCC)"),
    "PEC11R": ("https://www.bourns.com/docs/Product-Datasheets/PEC11R.pdf",
               "Bourns PEC11R (REV. 04/26): момент кріплення 10.2 kgf·cm (8.83 lb·in) макс. ≈1.0 N·m; гайка M7×0.75 і шайба в комплекті; IP40; −30…+70 °C"),
    "PV6": ("https://configured-product-images.s3.amazonaws.com/Datasheets/PV6.pdf",
            "E-Switch PV6 (8.28.2025): антивандальна кнопка, виріз ⌀16.00 +0.20/−0.00 мм, панель 1–10 мм, IP65, 2 A 48 VDC, SPST Off-(On), "
            "рекомендований момент кріплення 0.6 N·m, −40…+85 °C; без підсвічування — безель ⌀18.00 × 1.50, різьба M16×1.0, 17.50 ±0.50 мм від "
            "безеля до кінців виводів (с. 1, 3, 5); розмір гайки не наведено"),
    "LTW-VENT": ("https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/7136/Amphenol%20LTW_Pressure%20Relief%20Vent%20Group.pdf",
                 "Amphenol LTW, каталог клапанів, M12 Plastic (VENT-PS1YBK-O8002 — з гайкою): M12×1.5, момент 6.0–8.0 kgf·cm (0.59–0.78 N·m), "
                 "наскрізний отвір 2.0–3.5 мм або різьбовий ≥4.0 мм, IP68/IP69K, O8002 >1000 ml/min при 7 kPa"),
    "WE-SMA": ("https://www.we-online.com/components/products/datasheet/60311082111559.pdf",
               "Würth WR-SMA 60311082111559 (2025-03-03): THT-гніздо SMA з прокладкою, IP67 на панелі; момент різьби на панелі 57 N·cm "
               "(«має виконуватися для IP67»), рекомендований момент стикування 57 N·cm, панель ≤2.8 мм, виріз ⌀6.5 з лискою 6"),
    "BINDER-M8": ("https://binder-usa.com/us-en/products/automation-technology/m8/86-6618-1120-00006-m8-female-panel-mount-connector-6-shieldable-tht-ip67-m10x075-front-fastened",
                  "binder 86 6618 1120 00006 (alt. 09 3422 81 06), M8 серія 718, 6 конт., A-код, THT, IP67, M10×0.75, 1.5 A, 30 V, −40…+85 °C; "
                  "кільце кабельного роз'єму — від руки ≈50 cN·m; сторінка суперечлива щодо переднього/заднього монтажу, виріз і момент гайки не наведені"),
    "KINGHELM-GX12": ("https://www.lcsc.com/product-detail/C18203264.html",
                      "Kinghelm KH-GX12-6P (LCSC C18203264): «CONN 1 SET MALE AND FEMALE M12 6POS», 6 конт.; виріз панелі, гайка, момент і IP на "
                      "сторінці не наведені, PDF-даташит LCSC тексту не віддав — TBD"),
    "PEM-F": ("https://catalog.pemnet.com/item/pemsert--self-clinching-flush-fasteners---type-f/msert-self-clinching-flush-fasteners-type-f-metric/f-m3-1",
              "PEM F-M3-1: M3×0.5, лист 1.53–2.32 мм, отвір 4.37 +0.08, ≥6.00 мм від осі отвору до кромки, лист ≤HRB 70 / HB 125, нержавійка 300; "
              "ставиться втискуванням (прес)"),
    "PEM-SO": ("https://catalog.pemnet.com/item/thru-hole-threaded-standoffs-types-so-soa-sos/ru-hole-threaded-standoffs-types-so-soa-sos-metric/so-m3-3zi",
               "PEM SO-M3-3ZI: M3×0.5, L 3 мм, лист ≥1.00 мм, отвір 4.22 +0.08, H 4.8, ≥6.00 мм від осі отвору до кромки; голівка врівень з одним боком листа; прес"),
    "POLOLU-D36V50": ("https://www.pololu.com/file/0J1732/d36v50fx-step-down-voltage-regulator-dimensions.pdf",
                      "Pololu D36V50Fx (reg24d, 24.12.2019): плата 25.4 × 25.4, 12 отворів ⌀1.02 у два ряди (VOUT, GND ×4, VIN, VRP, EN/PG), "
                      "3 отвори ⌀2.18 під M2; деталі на нижньому боці 1.8 мм — модуль стоїть на проставці гребінки"),
    "CNCK-M3": ("https://3djake.ch/en-CH/cnc-kitchen/threaded-inserts-m3-standard",
                "CNC Kitchen TC-M3x5.7: L 5.7, ⌀D1 4.6, отвір ⌀D3 4.0, стінка ≥1.6; ставити на 10–20 °C вище температури друку"),
    "CNCK-M25": ("https://3djake.ch/en-CH/cnc-kitchen/threaded-inserts-m25-standard",
                 "CNC Kitchen TC-M2,5x4: L 4.0, ⌀D1 4.6, отвір ⌀D3 4.0, стінка ≥1.6 (так у лістингу; звірити з кресленням CNC Kitchen перед CAD)"),
    "POLY-ASA": ("https://polymaker.com/wp-content/tech-docs/PolyLite_ASA_PIS_EN_V1.3.pdf",
                 "PolyLite ASA PIS V1.3: сопло 240–260 °C, стіл 75–95 °C, обдув вимкнено, 30–50 мм/с, корпус принтера рекомендовано; "
                 "Tg 97.8 °C, Vicat 105.3 °C; сушіння 80 °C 8 год"),
    "LAPP-MSM": ("https://media.lappcdn.com/8/876/87682/9bae7263e0a64d10b08facf80500d163.pdf",
                 "LAPP SKINTOP MS-M/MSR-M, інструкція: IP68 10 bar, −20…+100 °C динамічно; момент M для M12×1,5 — 8 N·m (категорія A); "
                 "інструкцію MS-SC-M не прочитано"),
    "OLIMEX-GX16": ("https://www.olimex.com/Products/Components/Connectors/CONNECTOR-GX16-4/",
                    "Olimex CONNECTOR-GX16-4 (у наявності 24.10.2026); 6-контактного GX у Olimex немає (лише GX12-4, GX16-4)"),
}

# --- Physical units ----------------------------------------------------------
# kind: board (copper can route a net through), module, panel (part in a wall),
# cable (assembly end), remote (outside the enclosure).
BOARD_OF_DOMAIN = {  # build/15 «Кількість плат»; PWR = the PWR-A/PWR-B stack, one harness unit (PHYSICAL_BOARD below)
    "PWR_MAIN": "PWR", "PWR_BRANCH": "PWR", "USB_POWER": "PWR", "PWR_BRANCH_SW": "PWR", "USB_POWER_SW": "PWR",
    "RF_HMC": "RF", "RF_HF": "RF", "RF_INJECTOR": "RF", "DC_CORE": "RF",
    "CTRL_HMI": "CTRL", "HATCH": "HATCH",
}
# Off-plate board domains of pcb/prepare.py whose parts belong to a module or cable unit here (no deviation; W2 GR-4: their boundary refs too):
# ENC (ENCM/ENCV), T7_INSERT (T7A: J514-J517), HDMI_INSERT (HDMIA), IMU_CARRIER (IMUPACK: J518, J320-J322), PACK_FUSE (PACK: J116/J117).
# Boards whose PH headers must be side entry: their envelope height is 5.5 mm (RF, CTRL) or 6.5 mm (ENC) and a
# top-entry PH stands 8 mm with its housing (JST ePH); the side-entry header stands 4.8 mm (mechanical/params/boards.json).
SIDE_ENTRY_UNITS = ("CTRL", "RF", "ENCM", "ENCV")
SIDE_ENTRY_PH_MAX = 8  # S16B-PH-K-S is not stocked (parts DB): 16-pin groups become 2 x 8 (build/15 «Сигнальні джгути»)

UNITS = [
    # id, kind, name, place
    ("PWR", "board", "Силова плата PWR (PWR_MAIN + PWR_BRANCH + USB_POWER) з модулями D36V50F12 U107 і D36V50F5 U108 на платі",
     "лицьовий бік середньої пластини ліворуч унизу: нижня смуга x 6–142 і ліва ніжка x 6–48 (05 §3 рядок 15, M-07, B-PWR); U107 і U108 "
     "впаяно в ліву ніжку обома парами силових пінів (E1 U108) на проставці гребінки (деталі низу модуля 1.8 мм, креслення Pololu), тепло — "
     "через мідь PWR і термопрокладки до пластини; рішення build/15 «Кількість плат»"),
    ("CTRL", "board", "Плата керування/HMI CTRL (CTRL_HMI)", "за правою колонкою HMI на бобишках передньої половини (B-CTRL); кнопки крізь лице, "
     "енкодери — на дочірніх платах ENC"),
    ("ENCM", "board", "Дочірня плата головного енкодера ENC (ENC301 + кнопка SW308)", "лице, колонка HMI, x 188.5 y 123 (M-01, B-ENC, place_at main); "
     "ENC1 = ENC301 = головний (настройка, вибір сторінки HMI, Pico GP2/GP3) — рішення R-E3-16; напрям обертання — стенд (firmware/pico/hmi.py:18)"),
    ("ENCV", "board", "Дочірня плата енкодера гучності ENC (ENC302 + кнопка SW309)", "лице, колонка HMI, x 188.5 y 82 (M-01, B-ENC, place_at volume)"),
    ("RF", "board", "RF/детекторна плата RF (RF_HMC + RF_HF + RF_INJECTOR + DC_CORE)", "за пластиною в РЧ-відсіку вздовж верхнього краю, компоненти до задньої стінки (B-RF)"),
    ("HATCH", "board", "Плата сервісного лючка HATCH (J502 консоль UART5, J503 сервісний J21, SW501 EDL)",
     "сервісний лючок задньої стінки x 116–138, y 40–90 (layout hatch_parts; виріз HATCH і гнізда HATCH_M3 — M-06, паз ущільнення кришки — M-13); "
     "рішення build/15 «Сигнальні джгути»"),
    ("Q6A.HDR", "module", "Q6A, 40-pin J20 (J301)", "середня пластина"),
    ("Q6A.CORE", "module", "Q6A, бортові шини (U500)", "середня пластина"),
    ("Q6A.J21", "module", "Q6A, майданчики J21 (J521)", "середня пластина"),
    ("Q6A.J5", "module", "Q6A, USB J5 (J511)", "середня пластина"),
    ("Q6A.J2", "module", "Q6A, USB J2 (J512)", "середня пластина"),
    ("Q6A.HDMI", "module", "Q6A, HDMI (J520)", "середня пластина"),
    ("Q6A.MKEY", "module", "Q6A, M.2 M-key (J530)", "середня пластина"),
    ("Q6A.EDL", "module", "Q6A, контакти кнопки EDL (J522)", "середня пластина"),
    ("Q6A.RTC", "module", "Q6A, J11 RTC (J303 + BT301)", "середня пластина"),
    ("PACK", "module", "Пак 4S1P + BMS Daly + запобіжник паку (BT101–BT104, U101, TH101, F101; майданчики J116/J117 носія F101)",
     "батарейний відсік (лоток x 3–161 уздовж нижньої стінки, layout battery_tray), BMS — лицьовий бік пластини x 175–210 (layout bms); "
     "F101 7.5 A — у тримачі Keystone 3568 на малій носійній платі PACK_FUSE біля плюса паку (STACK D2 «біля батареї»): конверт layout pack_fuse "
     "x 161.7–172.4, y 11.5–37.9, z 46.5–64.3 (з pack_fuse_board) — над розширенням пластини біля правого торця лотка, на 2 стійках PEM SO-M2.5-6ZI 6 мм (M-07 PF1–PF2; під носієм — NTC корпусу TH302), "
     "запобіжник догори — доступний, коли знято передню половину (W2 MECH-5); провід BT104.+ → майданчик J116 (мідь до F101.1) — найкоротший, "
     "18 AWG (його захищає лише BMS, DOCP 40±10 A, 02 §2); провід S05 — від майданчика J117 (мідь від F101.2), W2 GR-4"),
    ("INA", "module", "Adafruit INA228 5832 (U102, R101, C101, C102)", "задній шар під екраном HF+, на бобишках задньої стінки x 28.5–54.3, y 44.5–64.8, z 6–16.1 "
     "(layout ina228; W2 MECH-3 — задній шар, бо над PWR-A мезонін PWR-B; W2 MECH-5 — клемник VIN−/VBUS/VIN+ на грані +y, куди приходить S06, гребінка JP2 — на грані −y); кріплення — F09"),
    ("SWM", "module", "Pololu #2813 (U106)", "задній шар, на друкованому майданчику задньої стінки x 93.3–113.6, y 39–64.4, z 5.5–15.6 (layout swm_2813, W2 MECH-3); кріплення — F05"),
    ("CHG", "module", "IP2368 COUT (U110, R117–R120, C118, TH102)", "лицьовий бік пластини вгорі праворуч x 172–220, y 122.5–156.5 (layout ip2368; "
     "R-IP2368 ≥10 мм від батареї)"),
    ("HUB", "module", "Adafruit 5997 CH334F (U510)", "задній шар під екраном HF+, на 4 бобишках задньої стінки x 55.3–86.9, y 39–59.3, z 6–13.3 "
     "(layout hub_ch334f, W2 MECH-5): JP5 — на східному торці (x 84.4), до Q6A J2 (лицьова грань стека x 139.25) близько 55 мм; кріплення — F10"),
    ("T7A", "cable", "Вставка ключа VBUS T7 (U505, R514–R517, C514–C516, TP501; вилка S24 J514, майданчики VBUS J515/J516 і GND J517)",
     "у розриві USB3 під стеком USB Q6A J5: резерв layout t7_insert x 142–163.5, y 49.1–58.1, z 3–11.5 (W2 MECH-5; плата — PCB-SB2)"),
    ("T7", "remote", "Samsung T7 + цілісний кабель A–C (U540)", "ззовні ззаду внизу, тримач"),
    ("HDMIA", "cable", "HDMI-вставка pin 18 (U506, C517, C518, R552, TP502)", "між двома стрічками HDMI на лицьовому боці пластини праворуч від BMS: резерв layout hdmi_insert x 210.5–226.5, y 34–52 (W2 MECH-4)"),
    ("DISP", "module", "Дисплей Wisecoco (U520)", "лице"),
    ("RISER", "module", "ADT-Link R44SF (U530)", "крізь вікно пластини"),
    ("LIME", "module", "LimeSDR Micro M.2 (A415)", "на п'єдесталі"),
    ("RTLA", "cable", "RTL-A V4L + кабель USB (A411, J543)", "РЧ-відсік, ряд 1 розкладки (b): V4L x 99.2–194.2, y 99.1–126.1 на кришці, розетка USB-A Würth 614004190021 на носійній платі x 194.2–209.1 (layout usb_socket_a, W2 MECH-3); кабель — крізь виріз N2"),
    ("RTLB", "cable", "RTL-B V4L + кабель з розділеним VBUS (A412, J541)", "РЧ-відсік, ряд 2 розкладки (b): V4L x 99.2–194.2, y 126.6–153.6, розетка USB-A Würth 614004190021 на носійній платі (layout usb_socket_b, W2 MECH-3); кабель — над розеткою RTL-A крізь виріз N3"),
    ("HFP", "cable", "Airspy HF+ + пігтейл micro-USB (A414, J544)", "екран Schubert 6B за пластиною, середній ряд ліворуч x 2.6–114.6 (layout hfplus)"),
    ("USBC", "panel", "USB-C PD (J103, Amphenol ICC MUSBRM5C130)", "нижня грань x 189, z 24 (M-02, USB_C_IN); виріз — TBD (креслення не прочитано)"),
    ("XT30", "panel", "Сервісний XT30 (J101)", "пігтейл у батарейному відсіку (v2.1: заряд ISDT заблоковано)"),
    ("LABUSB", "panel", "LAB USB-A (J501, Bulgin PX0845/A)", "нижня грань x 172, z 24 (M-02, LAB_USB_A)"),
    ("LABBUS", "panel", "LAB BUS (J505, Kinghelm KH-GX12-6P)", "нижня грань x 206, z 30 (M-02, LAB_BUS); виріз — TBD"),
    ("GX16", "panel", "Гніздо IMU GX16-4 (J504)", "задня стінка x 175, y 25 (M-06, GX16_IMU)"),
    ("SBPWR", "panel", "Панельна розетка живлення S-band pod (J551, binder M8 A-код 3 конт.)",
     "стінка головного корпусу — грань і виріз TBD (MECH-07, моделює MECH-3); вилка — на кабелі W425 (S41); рішення build/15 «Ключування панельних роз'ємів»"),
    ("EDL", "panel", "Кнопка EDL (SW501, E-Switch PV6F240SS)", "на платі лючка за кришкою сервісного лючка (layout edl_key_body)"),
    ("PWRBTN", "panel", "Кнопка живлення (SW301, E-Switch PV6F240SS)", "верхня грань x 155.5, z 50 (layout pwr_key_body, nut.PWR_KEY, M-02, PWR_KEY; рішення build/15 «Кнопка живлення SW301 (W2 MECH-4)»)"),
    ("IMUPACK", "remote", "IMU-пак Hammond 1550Z101 (U309, U314, J550, D502, C519, C520, U552 і деталі E3 «External IMU»; майданчики "
     "носійної плати IMU_CARRIER: кабель J518, RP2040-Zero J320/J321, BNO085 J322)", "на штанзі антени, ≥30 см позаду"),
    ("GNSS", "module", "LC76G (U304)", "задня стінка ліворуч x 58–88.5, y 71–96.5 (layout lc76g; плата Waveshare 30.5 × 25.5 за кресленням, W2 MECH-6); P1 (MX1.25) — "
     "до валу біля лючка; IPEX → P7: пігтейл W407 Taoglas CAB.01029 250 мм, запас ≥30 мм над трасою (R-P7-PIGTAIL; build/15 «Пігтейл P7 і місце LC76G (W2 MECH-6)»)"),
    ("VEML", "module", "Adafruit 4162 VEML7700 (U308)", "під верхньою стінкою за вікном ⌀4 x 120, z 63 (top_face veml7700_window), поза козирком: плата x 107.3–132.7, "
     "z 49.3–67.1 у кишені 1.1 мм верхньої стінки (layout veml7700, W2 MECH-5); кріплення — F47: скотч на 4 упорах, 2 шипи в отворах плати"),
    ("NTCP", "module", "NTC панелі TH301 (бусинка Semiware MF52A103F3950 на виводах)",
     "тил панелі x 164.5–168.5, y 98.9–101.1 (layout ntc_panel): права смуга без плати HDMI біля колонки HMI, поліімідна стрічка (примітка E3 TH301; модель, OPEN T-02)"),
    ("NTCC", "module", "NTC корпусу TH302 (бусинка Semiware MF52A103F3950 на виводах)",
     "лицьова грань розширення пластини x 165–169, y 24–26.2 (layout ntc_case) між нижнім входом повітря шляху 2 і повітродувкою, ≥23 мм від PWR-A, поліімідна стрічка (примітка E3 TH302; модель)"),
    ("FAN1", "module", "Noctua NF-A4x10 5V (FAN301)", "на охолоджувачі A Q6A, витяжка шляху 1 у задній стінці (layout cooler_a, q6a_fan_duct)"),
    ("FAN2", "module", "Delta BFB0305HA-C (FAN302)", "лицьовий бік пластини x 144–174.5, y 38.5–69, шлях 2 (layout blower)"),
    ("BONI", "module", "Bias-tee Boni-Whip (A406)", "поруч з G6K, поза екраном HF+: резерв layout boni_a406 30 × 26 × 9.8 (x 106–136, поза трасою W407) у РЧ-відсіку над V4L-A під RF-платою "
     "(W2 MECH-5, припущення: розмір вузла Bonito не опубліковано; якщо не вміститься — саморобний bias-tee 2.2 mH примітки E4 A406)"),
    ("SPOD", "remote", "Кабель живлення S-band pod (W425)", "зовнішній вузол"),
]

# Refs whose physical place is not given by the partition column.
UNIT_OF_REF = {
    "J301": "Q6A.HDR", "U500": "Q6A.CORE", "J521": "Q6A.J21", "J511": "Q6A.J5", "J512": "Q6A.J2",
    "J520": "Q6A.HDMI", "J530": "Q6A.MKEY", "J522": "Q6A.EDL", "J303": "Q6A.RTC", "BT301": "Q6A.RTC",
    "BT101": "PACK", "BT102": "PACK", "BT103": "PACK", "BT104": "PACK", "U101": "PACK", "J102": "PACK", "TH101": "PACK",
    "U102": "INA", "R101": "INA", "C101": "INA", "C102": "INA",
    # U108 sits on PWR: its output reaches F102 through PWR copper, not a crimped harness, so the
    # E1-05 headroom budget (F102 ≤10 mΩ, E1→E2 ≤10 mΩ) is not spent on wire and contacts (ASM-R5).
    # U107 sits on PWR as well (build/15 «Кількість плат», 07.11.2026): the SYS12 link is PWR copper, no harness S08.
    "U106": "SWM", "U107": "PWR", "U108": "PWR",
    "U110": "CHG", "R117": "CHG", "R118": "CHG", "R119": "CHG", "R120": "CHG", "C118": "CHG", "TH102": "CHG",
    # F101 at the pack (STACK D2 «біля батареї»): every harness wire of the battery circuit is downstream of it (ASM-R1).
    "F101": "PACK", "F102": "PWR", "F103": "PWR", "F104": "PWR", "F201": "PWR", "F202": "PWR",
    "J101": "XT30", "J103": "USBC",
    "U510": "HUB", "U540": "T7", "U520": "DISP", "U530": "RISER", "A415": "LIME",
    "A411": "RTLA", "J543": "RTLA", "A412": "RTLB", "J541": "RTLB", "A414": "HFP", "J544": "HFP",
    "J501": "LABUSB", "J505": "LABBUS", "J504": "GX16", "J551": "SBPWR", "J502": "HATCH", "J503": "HATCH", "SW501": "EDL",
    "SW301": "PWRBTN", "U304": "GNSS", "U308": "VEML", "FAN301": "FAN1", "FAN302": "FAN2",
    "U305": "CTRL", "ENC301": "ENCM", "ENC302": "ENCV", "BZ301": "CTRL",
    # Leaded bead NTCs (parts DB mount "remote") sit away from CTRL (E3 notes: TH301 on the rear heat spreader of the
    # panel, TH302 on the inner frame away from converter heat), so each gets its own unit and a two-wire lead to a PH
    # header on CTRL (S39, S40) like every other off-board part; the CTRL headers are graph refs J318/J319 (W2 GR-3, HEADERS).
    "TH301": "NTCP", "TH302": "NTCC",
    "SW302": "CTRL", "SW303": "CTRL", "SW304": "CTRL", "SW305": "CTRL", "SW306": "CTRL", "SW307": "CTRL",
    "SW308": "ENCM", "SW309": "ENCV",  # push switches inside ENC301/ENC302 (parts DB virtual hosts)
    "U309": "IMUPACK", "U314": "IMUPACK", "J550": "IMUPACK", "D502": "IMUPACK", "C519": "IMUPACK",
    "C520": "IMUPACK", "U552": "IMUPACK",
    # W2 GR-4: boundary refs of the insert boards, in the unit that assembles the board (pcb/prepare.py DOMAIN_OVERRIDE).
    "J518": "IMUPACK", "J320": "IMUPACK", "J321": "IMUPACK", "J322": "IMUPACK", "J116": "PACK", "J117": "PACK",
    "J514": "T7A", "J515": "T7A", "J516": "T7A", "J517": "T7A",
    "U506": "HDMIA", "C517": "HDMIA", "C518": "HDMIA", "R552": "HDMIA", "TP502": "HDMIA",
    "U505": "T7A", "R514": "T7A", "R515": "T7A", "R516": "T7A", "R517": "T7A", "C514": "T7A", "C515": "T7A",
    "C516": "T7A", "TP501": "T7A",
    "A406": "BONI", "W425": "SPOD", "NT401": "RF",
    "J409": "RF", "J410": "RF", "J411": "RF", "J412": "RF",
}
# Test points of E1/E2 sit on the power board.
for _n in list(range(101, 109)) + list(range(201, 217)) + [2901, 2902, 2903]:
    UNIT_OF_REF[f"TP{_n}"] = "PWR"
# FAULT_N test points of the thin-branch switches (W2 GR-1) sit beside their switch: U315 on CTRL, U553 on PWR.
UNIT_OF_REF.update({"TP301": "CTRL", "TP503": "PWR"})
# Bare parts drawn on E3 but built into the IMU pack (E3 group "External IMU").
UNIT_OF_GROUP = {("E3", "External IMU"): "IMUPACK"}
# Physical board of a pcb/prepare.py domain (the 'board' column of build/16-dzhgut-rozyemy.csv). The harness unit PWR is the
# PWR-A/PWR-B stack: one bundle end that breaks out after the slot onto headers of both boards (pcb/partition-spec.json; the
# JLC BOM board names of tools/build_parts.py BOARD3 are the same).
PHYSICAL_BOARD = {"PWR_MAIN": "PWR_A", "PWR_BRANCH": "PWR_A", "USB_POWER": "PWR_A", "PWR_BRANCH_SW": "PWR_B", "USB_POWER_SW": "PWR_B",
                  "CTRL_HMI": "CTRL", "RF_HMC": "RF", "RF_HF": "RF", "RF_INJECTOR": "RF", "DC_CORE": "RF", "HATCH": "HATCH", "ENC": "ENC",
                  # the insert boards (W2 GR-4): a header there (J514) is listed on its own board
                  "T7_INSERT": "T7_INSERT", "HDMI_INSERT": "HDMI_INSERT", "IMU_CARRIER": "IMU_CARRIER", "PACK_FUSE": "PACK_FUSE"}
# PWR-B is a mezzanine on the PWR-A L, joined by the Samtec B2B pair (pcb/partition-spec.json, W2 AREA), so BOARD_OF_DOMAIN keeps
# one harness unit PWR for both. Source of the dual-row PHD headers (W2 GR-3), set here after the units so that the line citations
# into this file (side-entry rule and ENC units: build/15, pcb/README.md, pcb/boards/ENC.json) keep their numbers.
SOURCES["JST-PHD"] = ("https://datasheet.lcsc.com/datasheet/pdf/5f2def6b1b145b42d10ba2e392671cbf.pdf?productCode=C111516",
                      "JST PHD (каталог JST, копія LCSC до C111516; jst-mfg.com/product/pdf/eng/ePHD.pdf відповів 403 07.11.2026): 2.0 мм, 2 ряди; "
                      "3 A AC/DC (AWG #22) — інших перерізів номінал не наводить; 250 V, −25…+85 °C; опір контакту 10 mΩ макс. початково / 20 mΩ після "
                      "тесту; провід AWG #28…#22; SPHD-001T-P0.5 — AWG 26…22, ⌀ ізоляції 1.0…1.5 мм; SPHD-002T-P0.5 — AWG 28…24, ⌀ 0.9…1.5 мм; "
                      "розетки PHDR-08VS…PHDR-34VS; вилки B8B…B34B-PHDSS (верхній вхід), S8B…S34B-PHDSS (боковий); аплікатор AP-K2N з матрицею "
                      "MK/SPHD-001-05 (с. 1–2)")

# --- Board-side harness headers (graph refs, W2 GR-3 / W2-01) ------------------------------------------------
# ref -> (harness label, {segment: "contact numbers"}). Every board end of a harness wire lands on a listed contact of one
# of these refs (tools/build_assembly_docs.py explicit mode); a contact that is not listed is a reserve (nc in the graph).
# Labels keep the X ids of the wave-1 tables or the consolidation names of pcb/partition-spec.json (build/16 §4 column).
HEADERS = {
    "J304": ("X01I1-CTRL", {"S01": "1 3 5 8-10 12-15 17 20 25 27-30 32 34 35 38-40"}),
    "J305": ("X02P1-CTRL", {"S02": "1-4"}),
    "J306": ("S02-CTRL-SIG-1", {"S02": "1-20"}),
    "J307": ("S02-CTRL-SIG-2", {"S02B": "1-20"}),  # branch S02B of S02 to the top-entry J203 (W2 PWR-L6-PLACE third pass)
    "J308": ("X03S1-CTRL", {"S03": "1-8"}),
    "J309": ("X03S2-CTRL", {"S03": "1-4"}),
    "J310": ("S15-30-CTRL", {"S15": "1", "S30": "2-4"}),
    "J311": ("S24-25-CTRL", {"S24": "1-3", "S25": "4-6"}),
    "J312": ("X26S1-CTRL", {"S26": "1-4"}),
    "J313": ("X27F1-CTRL", {"S27": "1-3"}),
    "J314": ("X28P1-CTRL", {"S28": "1 2"}),
    "J315": ("X29S1-CTRL", {"S29": "1 2"}),
    "J316": ("X37S1-CTRL", {"S37": "1-4"}),
    "J317": ("X38S1-CTRL", {"S38": "1-4"}),
    "J318": ("X39S1-CTRL", {"S39": "1 2"}),
    "J319": ("X40S1-CTRL", {"S40": "1 2"}),
    "J418": ("X03S1-RF", {"S03": "1-8"}),
    "J419": ("X03S2-RF", {"S03": "1-4"}),
    "J420": ("X04S1-RF", {"S04": "1-8"}),
    "J104": ("X02P1-PWR", {"S02": "1-4"}),
    "J105": ("X05J1-PWR", {"S05": "1 2"}),
    "J106": ("X06J1-PWR", {"S06": "1 2"}),
    "J107": ("X07J1-PWR", {"S07": "1 2"}),
    "J108": ("X10J1-PWR", {"S10": "1-3"}),
    "J109": ("X05S1-PWR", {"S05": "1"}),
    "J110": ("X06S1-PWR", {"S06": "1-5"}),
    "J111": ("X07S1-PWR", {"S07": "1-3"}),
    "J112": ("X10S1-PWR", {"S10": "1-4"}),
    "J113": ("X11S1-PWR", {"S11": "1 2"}),
    "J114": ("X11P1-PWR", {"S11": "1 2"}),
    "J115": ("X12P1-PWR", {"S12": "1 2"}),
    "J201": ("X02S0-PWR", {"S02": "1-4"}),
    "J202": ("S02-PWR-SIG-1", {"S02": "1-20"}),
    "J203": ("S02-PWR-SIG-2", {"S02B": "1-20"}),  # W2 PWR-L6-PLACE third pass: top entry B20B-PHDSS in PWR-B zone 2
    "J204": ("X04S1-PWR", {"S04": "1-8"}),
    "J205": ("X19P1-PWR", {"S19": "1 2"}),
    "J206": ("SL2-PWR-MF", {"S13": "1 2", "S14": "3 4", "S17": "5 6", "S18": "7 8"}),
    "J207": ("SL2-PWR-PH", {"S20": "1 2", "S21": "3 4", "S22": "5-7", "S35": "8 9", "S36": "10 11"}),
    "J506": ("SL3-PWR-PH", {"S23": "1-3", "S34": "4-9"}),  # W2 GR-5B: J506 (S23) + J508 (S34) in one JST PH 9; top entry B9B in PWR-B zone 2 since W2 PWR-L6-PLACE
    "J507": ("X32S1-PWR", {"S32": "1-4"}),
    # J508 (X34S1-PWR, S34) is merged into J506 above (W2 GR-5B, SHRINK-2)
    "J509": ("X14P1-HATCH", {"S14": "1 2"}),
    "J510": ("X15S1-HATCH", {"S15": "1"}),
    "J513": ("X30S1-HATCH", {"S30": "1-3"}),
    # W2 GR-4: the T7A end of S24 lands on the side-entry PH 3 header of the T7_INSERT board (was soldered to U505/R516 pins)
    "J514": ("X24S1-T7A", {"S24": "1-3"}),
}
# Graph connectors whose contacts serve more than one segment: the S01 ribbon conductors 6, 7, 16 and 18 leave as the PPS branch
# right after the J20 socket (build/15 W2 MECH-1, mechanical/params/mechanical.json harness_routes branches.PPS).
PIN_SEGMENTS = {"J301": {"S01": "1 3 5 8-10 12-15 17 20 25 27-30 32 34 35 38-40", "PPS": "6 7 16 18"}}
# Branch segments listed under their parent bundle in build/16 (wire ids <parent>-<branch>-nn, segment column = parent): the PPS
# conductors are S01 ribbon conductors that leave it after the J20 socket; their route is branches.PPS of the mechanical model.
SEGMENT_BRANCHES = {"PPS": "S01", "S02B": "S02"}  # S02B: the J307 <-> J203 conductors of S02 (W2 PWR-L6-PLACE third pass)
# Board units whose harness ends have no graph header ref yet, with the reason; only there the generator still writes an X id.
PENDING_BOARD_ENDS = {
    "ENCM": "роз'єм дочірньої плати ENC: жоден корпус JST PH не вміщується біля PEC11R на контурі 24 × 24 (W2 PCB-PIPE, pcb/boards/ENC.json "
            "J1 pilot_placeholder); ref графа з доменом ENC зламав би доменний аудит плати ENC, доки її специфікацію не оновить PCB-SB1",
    "ENCV": "як ENCM (той самий шаблон плати ENC, pcb/boards/ENC.json)",
}
# Harness purchases outside the wire table that the roll-up owns (BOM ownership, W2 GR-3): (family, pins, role, qty, note).
ROLLUP_EXTRA = [
    ("PH", 3, "розетка кабелю", 1, "провід адаптера консолі UART5 до J502 на платі лючка (зовнішній, поза таблицею проводів)"),
    ("PH", "", "клема", 3, "провід адаптера консолі UART5 до J502 (зовнішній, поза таблицею проводів)"),
]
# Acknowledged places that differ from the board_candidate of pcb/generated/components.csv:
# unit or ref -> why. The generator lists every such ref in build/16 §2 and fails on an unacknowledged one.
# Empty since the integration of 07.11.2026: pcb/prepare.py gives the inserts, the IMU-pack carrier, the hatch board,
# the encoder boards and the F101 carrier their own domains, and J302 stays on CTRL as graph E3 has it.
PARTITION_DEVIATIONS = {}


def partition_deviation(ref, unit):
    """Reason for a place that differs from the board partition, or None."""
    return PARTITION_DEVIATIONS.get(ref) or PARTITION_DEVIATIONS.get(unit)
# Remaining E4 modules, panel RF connectors and coax assemblies form the RF domain
# (each is its own unit; links are coax, see section "РЧ" of build/16).
RF_DOMAIN_PREFIXES = ("A4", "J4", "W4")

# Q6A sub-units are one board: their shared nets join on the Q6A itself.
INTERNAL_LINKS = [
    ("Q6A.CORE", "Q6A.HDR"), ("Q6A.CORE", "Q6A.J21"), ("Q6A.CORE", "Q6A.J5"), ("Q6A.CORE", "Q6A.J2"),
    ("Q6A.CORE", "Q6A.HDMI"), ("Q6A.CORE", "Q6A.MKEY"), ("Q6A.CORE", "Q6A.EDL"), ("Q6A.CORE", "Q6A.RTC"),
    ("RISER", "LIME"),  # card in the riser slot
]

# --- Harness segments --------------------------------------------------------
# id, end a, end b, title, family override (None = by current), length (mm or text), note
SEGMENTS = [
    ("S01", "Q6A.HDR", "CTRL", "Шлейф 40-pin Q6A J20 → CTRL", "IDC", "≤200 (UART7 і PPS ≤20 см, STACK §5.2)",
     "IDC 2×20 2.54 мм 1:1, стрічка 3M 3365/40 (дві половини по 20, укладені одна на одну: 2 × 0.89 мм) крізь проріз SL1 27.5 × 4.4 над верхнім краєм Q6A "
     "(M-07; R-PLATE-SLOT-FILL: вміщується, модель); на CTRL — бокс-роз'єм 2×20 з ключем J304; його висота проти обмеження CTRL 5.5 мм — TBD (R-HDR-HEIGHT); провідники 6, 7, 16 і 18 "
     "(GND, PPS, UART6) відходять гілкою PPS одразу за розеткою J20, тож контакти 6/7/16/18 бокса на CTRL — без кола (рішення build/15 W2 MECH-1, W2 GR-3)"),
    ("PPS", "Q6A.HDR", "GNSS", "Гілка PPS і UART6 шлейфу S01 → LC76G", "IDC", "≤200 (STACK §5.2)",
     "провідники 6 (GND), 7 (PPS), 16 і 18 (UART6) стрічки S01 відокремлено одразу за розеткою на J20 і проведено задньою площиною до P1 LC76G "
     "(mechanical/params/mechanical.json harness_routes branches.PPS; R-PPS-LEN: ≤200 мм за моделлю і в найгіршому випадку; build/15 W2 MECH-1, W2 MECH-6); на LC76G — пайка; мережі E3 не змінюються"),
    ("S02", "CTRL", "PWR", "Керування і LAB5: CTRL ↔ PWR", None, "TBD (CAD)",
     "I2C2/3V3_Q6A: на CTRL — J302 (E3, S5B-PH-K-S, боковий вхід; контакт 5 MCP_INT лишається на CTRL), на PWR-B — J201 (S5B-PH-K-S, боковий вхід, "
     "контакт 5 без кола); LAB5 — кутова J305 (43650-0400) на CTRL ↔ J104 (43650-0415) на PWR-A; сигнали — 2 × S20B-PHDSS: J306/J307 ↔ J202/J203 (W2 GR-3); S02 як FFC не прийнято: READS-P не встановив пару FH12 + кабель (W2 GR-5B, OPEN)"),
    ("S03", "CTRL", "RF", "Керування RF: CTRL ↔ RF", None, "TBD (CAD)",
     "лінії HMC7992/G6K/DCS; крізь проріз SL2 (M-07) і виріз N4 стінки РЧ-відсіку; подалі від буферних дроселів"),
    ("S04", "PWR", "RF", "Зміщення і реле: PWR ↔ RF", None, "TBD (CAD)",
     "шини bias ch1–ch4, LNB і LAB5_RLY котушок G6K (після PTC F104 на PWR-A, R-E1-09); крізь проріз SL2 і виріз N4 (M-07, M-09); J204 (PH 8, PWR-B) ↔ J420 (PH 8, RF): злиття J204 з J207 у PHD 2×10 (SHRINK-2) — OPEN, бо клема PHD бере 22 AWG, а PH — 30–24 AWG, тож потрібна й J420 PHD (лінія RF); LAB5_RLY 1.5 A проти 1.2 A контакту PH — OPEN (W2 GR-5B)"),
    ("S05", "PACK", "PWR", "Пак (після F101) → PWR", None, "мінімальна (TBD, CAD)",
     "F101 стоїть біля паку, тож увесь сегмент захищає F101 7.5 A; коло батареї 18 AWG (E1 F101); найкоротша траса, без петель; "
     "кінець у паку — майданчик J117 носійної плати PACK_FUSE (мідь від F101.2, W2 GR-4); "
     "роз'єм S05 на PWR — також вхід стенда при запуску (19 §4)"),
    ("S06", "PWR", "INA", "PWR ↔ INA228 (шунт)", None, "TBD (CAD)", "VIN+/VIN− — клеми шунта Adafruit 5832; I2C0/ALERT/VS — гребінка модуля"),
    ("S07", "PWR", "SWM", "PWR ↔ Pololu #2813", None, "TBD (CAD)", "пайка до контактів модуля; коло батареї 18 AWG"),
    ("S10", "PWR", "CHG", "PWR ↔ IP2368", None, "TBD (CAD)", "пайка до контактів роздрібної плати; KSD9700 — на MOSFET плати"),
    ("S11", "USBC", "PWR", "USB-C панелі → PWR", None, "TBD (CAD)", "CC1/CC2 проходять PWR транзитом до IP2368; крізь проріз SL3 (M-07)"),
    ("S12", "PWR", "XT30", "PWR → сервісний XT30", None, "TBD (CAD)",
     "пігтейл XT30U-F (бік паку/PWR, під напругою — гніздо); XT30U-M — на сервісному дроті; v2.1: ISDT/raw-balance заблоковано до E1-02"),
    ("S13", "PWR", "HUB", "LAB5 → CH334F JP5.1", None, "TBD (CAD)", "лише живлення хаба; дані — кабель C-HUB; крізь проріз SL2"),
    ("S14", "PWR", "HATCH", "J21 12 V → плата лючка (J503)", None, "TBD (CAD)", "кручена пара 12 V/GND (STACK §5.8); крізь проріз SL2"),
    ("S15", "CTRL", "HATCH", "PWR_ON_KEY → плата лючка (J503.3)", None, "TBD (CAD)",
     "окрема жила KEY до вузла АБО (STACK §5.8); на платі лючка — мідь до J503.3; крізь проріз SL2"),
    ("S16", "HATCH", "Q6A.J21", "J503 (плата лючка) → майданчики J21 Q6A", "SOLDER", "TBD (CAD)",
     "після прогону Q6A (08 крок 7.7): розетка 43645-0300 на J503 плати лючка; 12 V/GND — кручена пара 20 AWG, KEY — 24 AWG (примітка E5 J503, "
     "build/15: найтонший переріз клеми Micro-Fit 43030); термоусадка на кожному з'єднанні, поліімід на корпусі USB-C"),
    ("S17", "PWR", "Q6A.CORE", "VCC_3V3_MKEY Q6A → ключ LIME3V3", None, "TBD (CAD)",
     "відвід — дві площадки C17 (22 мкФ, вихід U20, нижній бік Q6A; parts.json q6a.mkey_tap): паяти після приймальних тестів Q6A, до монтажу; котра площадка VCC — прозвонка (OPEN); пару 20 AWG закріпити на платі ≤10 мм від площадок (вибір конструкції: малий конденсатор, ризик відриву площадки від тягнення дроту); крізь SL2"),
    ("S18", "PWR", "RISER", "LIME3V3 → R44SF (бік картки)", None, "TBD (CAD)", "лише до контактів 3.3 V картки, відділених від VCC_3V3_MKEY (E5 §10); крізь проріз SL2"),
    ("S19", "PWR", "DISP", "DISP12 → барель Wisecoco", None, "TBD (CAD)", "розмір і полярність бареля — E5-01 відкрито"),
    ("S20", "PWR", "RTLA", "VBUS_RTLA → кабель RTL-A (J543.1)", None, "TBD (CAD)", "VBUS вставляється в пігтейл H2; JP1.1 хаба не з'єднувати; крізь SL2 і виріз N2"),
    ("S21", "PWR", "RTLB", "VBUS_RTLB → кабель RTL-B (J541.1)", None, "TBD (CAD)", "розділений VBUS; J5.10 не з'єднувати; крізь SL2 і виріз N3"),
    ("S22", "PWR", "HFP", "VBUS_HFP → пігтейл HF+ (J544.1)", None, "TBD (CAD)", "після L501 і демпфера; 2× Fair-Rite 2631480002 на повному кабелі; крізь SL2"),
    ("S23", "PWR", "LABUSB", "VBUS_LABPORT → J501.1", None, "TBD (CAD)", "C506, C521, C522 (3 × 16SVPG47M, 141 мкФ; W2 GR-5B) біля вихідного порту на PWR-B; на PWR-B — контакти 1–3 вилки PH 9 J506 (SL3-PWR-PH, спільна з S34); крізь проріз SL3"),
    ("S24", "CTRL", "T7A", "EN_T7/3V3 → вставка T7", None, "TBD (CAD)",
     "U505 на вставці USB3; на вставці — вилка J514 (X24S1-T7A, PH 3 бічного входу, W2 GR-4); крізь проріз SL2"),
    ("S25", "CTRL", "GNSS", "CTRL → LC76G (живлення і RESET)", None, "TBD (CAD)",
     "E3_GNSS5V від U315 і E3_GNSS_RESET_N від Q301 з CTRL, крізь SL2, до P1 (MX1.25) LC76G; PPS і UART6 сюди не входять — вони йдуть гілкою PPS шлейфу S01 "
     "(S01 + S25 за моделлю понад 200 мм, R-PPS-LEN; рішення build/15 W2 MECH-1)"),
    ("S26", "CTRL", "VEML", "CTRL → VEML7700", None, "TBD (CAD)", "100 Ω + TVS біля безеля (на CTRL)"),
    ("S27", "CTRL", "FAN1", "CTRL → Noctua", "FAN3", "кабель вентилятора", "штатний 3-контактний роз'єм Noctua; на CTRL — сумісна 3-контактна вилка 2.54 мм"),
    ("S28", "CTRL", "FAN2", "CTRL → повітродувка Delta", None, "TBD (CAD)", "2 дроти; низький ключ на CTRL"),
    ("S29", "CTRL", "PWRBTN", "CTRL → кнопка живлення", None, "TBD (CAD)", "пайка до виводів PV6F240SS"),
    ("S30", "CTRL", "HATCH", "CTRL → плата лючка (консоль UART5 J502)", None, "TBD (CAD)", "лише 3.3 V TTL, без живлення адаптера; крізь проріз SL2"),
    ("S31", "Q6A.EDL", "EDL", "Контакти EDL Q6A → SW501", "SOLDER", "TBD (CAD)", "точки пайки на Q6A не локалізовано (E5 §9); пайка до виводів PV6F240SS"),
    ("S32", "PWR", "GX16", "PWR → гніздо GX16-4 (J504)", None, "TBD (CAD)", "U551 біля входу на PWR; корпус GX16 → CHASSIS; крізь проріз SL3"),
    ("S33", "GX16", "IMUPACK", "Зовнішній кабель IMU", "CABLE", "2000 (HELU 49655, STACK §2.10)",
     "HELU SUPERTRONIC-C-PURO 4×0.14 мм²; оплітка 360° у GX16 і в SKINTOP паку"),
    ("S34", "PWR", "LABBUS", "PWR → LAB BUS (J505)", None, "TBD (CAD)",
     "пайка в чашки KH-GX12-6P; кабель за межами корпусу ≤1 м (понад — PCA9615, E5 §9); на PWR-B — контакти 4–9 вилки PH 9 J506 (SL3-PWR-PH, спільна з S23; W2 GR-5B); крізь проріз SL3"),
    ("S35", "PWR", "BONI", "BONI13V8_PORT → bias-tee Boni", None, "TBD (CAD)", "штекер 5.5/2.1 мм (STACK, «Склад набору кабелів»); крізь проріз SL2"),
    ("S36", "PWR", "SBPWR", "BIAS_SB_LNA → панельна розетка J551", None, "TBD (CAD)",
     "виводи розетки J551 (binder 76 6618 1111 00003-0200: 0.2 м, AWG 24) — до роз'єму PWR; місце J551 на стінці — MECH-07 (MECH-3); довжина виводів проти траси — TBD"),
    ("S37", "CTRL", "ENCM", "CTRL ↔ дочірня плата головного енкодера", None, "TBD (CAD)",
     "A/B/C і кнопка ENC1_PRESS; JST PH боковий вхід на обох кінцях (зона з'єднання ENC — лівий край, boards.json)"),
    ("S38", "CTRL", "ENCV", "CTRL ↔ дочірня плата енкодера гучності", None, "TBD (CAD)", "A/B/C і кнопка ENC2_PRESS; JST PH боковий вхід"),
    ("S39", "CTRL", "NTCP", "CTRL → NTC панелі TH301", None, "TBD (CAD)",
     "2 дроти до виводів бусинки на тилі панелі (layout ntc_panel): паяти ≥6 мм від бусинки, виводи ізолювати й розвантажити (примітка E3 TH301); "
     "на CTRL — J318, PH боковий вхід; обрив або КЗ датчика → повне охолодження (E3)"),
    ("S40", "CTRL", "NTCC", "CTRL → NTC корпусу TH302", None, "TBD (CAD)",
     "2 дроти до виводів бусинки на пластині (layout ntc_case): паяти ≥6 мм від бусинки, виводи ізолювати й розвантажити (примітка E3 TH302); "
     "на CTRL — J319, PH боковий вхід; обрив або КЗ датчика → повне охолодження (E3)"),
    ("S41", "SBPWR", "SPOD", "Кабель живлення S-band pod W425", "CABLE", "1500 (W425, база деталей W-USBC-POWER)",
     "вилка M8 binder 99 3379 100 03 (супутня деталь J-POD-PWR-PANEL, гвинтові клеми, кабель ⌀3.5–5.0 мм) у J551 ↔ USB-C у LaNA WB крізь "
     "гермоввід pod (F43); пара живлення 26 AWG; кабель — W-USBC-POWER (SRC-2)"),
]

# Families: (name, contact rating A, design share, AWG allowed, source). power_awg is the gauge the catalogue
# rating is taken for: JST gives 2 A at AWG #24 only, Molex gives one rating per terminal without a gauge, so a
# power wire (any net with a current budget) in a rated family uses that gauge or a thicker one it accepts.
FAMILIES = {
    "PH": {"title": "JST PH 2.0 мм", "rating": 2.0, "share": 0.6, "awg": (26, 24), "signal_awg": 26, "power_awg": 24,
           "max_pins": 16, "source": "JST-PH",
           "db": "PH", "tool": "JST WC-240 (секції 30-28, 26, 24 AWG; зачистка 2.2 мм; assembly_items AI-JST-PH-TOOL)"},
    "MF": {"title": "Molex Micro-Fit 3.0 (1 ряд, 3.00 мм)", "rating": 5.0, "share": 0.6, "awg": (24, 22, 20), "signal_awg": 24, "power_awg": 20,
           "max_pins": 12, "source": "MOLEX-43030",
           "db": "MF", "tool": "Molex 0638190000; екстрактор 0011030043"},
    # Dual-row variants of the board headers (W2 GR-3, consolidation of pcb/partition-spec.json): the same selection rule as
    # their single-row family (tools/build_assembly_docs.py HINT_OF), their own housings in harness_families.
    "MF2": {"title": "Molex Micro-Fit 3.0 (2 ряди, 3.00 мм)", "rating": 5.0, "share": 0.6, "awg": (24, 22, 20), "signal_awg": 24, "power_awg": 20,
            "max_pins": 24, "source": "MOLEX-43030",
            "db": "MF2", "tool": "Molex 0638190000; екстрактор 0011030043"},
    "PHD": {"title": "JST PHD 2.0 мм (2 ряди)", "rating": 3.0, "share": 0.6, "awg": (22,), "signal_awg": 22, "power_awg": 22,
            "max_pins": 34, "source": "JST-PHD",
            "db": "PHD", "tool": "TBD: каталог PHD називає лише аплікатор AP-K2N з матрицею MK/SPHD-001-05 (ручного інструмента не наведено)"},
    "IDC": {"title": "IDC 2×20, 2.54 мм, стрічка 1.27 мм", "rating": None, "share": None, "awg": (28,), "signal_awg": 28, "power_awg": 28,
            "max_pins": 40, "source": None, "db": "IDC", "tool": "прес IDC"},
    "MFJ": {"title": "Molex Mini-Fit Jr. (дворядна)", "rating": 9.0, "share": 0.6, "awg": (24, 22, 20, 18), "signal_awg": 24, "power_awg": 18,
            "max_pins": 12, "source": "MOLEX-5556",
            # Housings 5557 (0039012020/0039012040), vertical headers 5566 (0039288020/0039288040) and the 0039000060
            # terminal are the harness_families MFJ entry of design/parts/parts.json (LCSC listings plus DigiKey DE SKUs,
            # W2 SRC-1), so the generator takes them from the database like PH, MF and IDC. Header footprints: KiCad 10.0.7
            # Connector_Molex 5566-02A/-04A (no PCB pegs, by the library mapping; the Molex drawings were not readable).
            # The codes first read on DigiKey DE stay in SOURCES DIGIKEY-MFJ.
            "db": "MFJ", "terminal": "0039000060 (пакет) / 0039000059 (котушка)",
            "tool": "Molex 638190901 (18–24 AWG); екстрактор 11030044"},
    "SOLDER": {"title": "пайка до майданчиків", "rating": None, "share": None, "awg": (28, 26, 24, 22, 20, 18), "signal_awg": 26, "power_awg": 20,
               "max_pins": 99, "source": None, "housing": "—", "header": "—", "terminal": "—", "tool": "паяльник; термоусадка"},
    "CABLE": {"title": "готовий кабель", "rating": None, "share": None, "awg": (26,), "signal_awg": 26, "power_awg": 26,
              "max_pins": 99, "source": None, "housing": "—", "header": "—", "terminal": "—", "tool": "—"},
    "FAN3": {"title": "3-контактний роз'єм вентилятора 2.54 мм (штатний Noctua)", "rating": None, "share": None, "awg": (26,),
             "signal_awg": 26, "power_awg": 26, "max_pins": 3, "source": None, "db": "FAN3",
             "housing": "штатний на кабелі Noctua", "terminal": "—", "tool": "—"},
}
# Battery circuit downstream of F101: E1 F101 «18 AWG. Тримач та інтерконекти мають витримувати ≥7.5 A». Its wires are
# never thinner than this, and a connector carrying them (and their return) uses a family that accepts 18 AWG.
MIN_AWG = {"E1_SHUNT_P": 18, "E1_N": 18, "E1_SW": 18}
MIN_AWG_SOURCE = "E1.json F101: «18 AWG. Тримач та інтерконекти мають витримувати ≥7.5 A»"
# Contact resistance per mating interface, mΩ (None = not given in the documents read).
CONTACT_MOHM = {"PH": (20, "JST-PH: 10 mΩ макс. початково / 20 mΩ після тесту — взято 20"), "MF": (None, "MOLEX-43030: не наведено"),
                "PHD": (20, "JST-PHD: 10 mΩ макс. початково / 20 mΩ після тесту — взято 20"), "MF2": (None, "MOLEX-43030: не наведено"),
                "MFJ": (None, "MOLEX-5556: не наведено")}
# Conductor resistance, Ω/km at 20 °C (ESCC 3901/001 table 1(a), single-core variants; no 28 AWG variant).
WIRE_OHM_PER_KM = {26: 148, 24: 105, 22: 50.9, 20: 32.2, 18: 20.6}
# Fixed gauges where STACK names them (segment, net) -> AWG
FIXED_AWG = {("S14", "J21"): 20, ("S14", "GND"): 20, ("S16", "J21"): 20, ("S16", "GND"): 20, ("S16", "PWR_ON_KEY"): 24}
# Segments that may carry only the listed nets (GND is added by the generator where both ends have it).
SEGMENT_NETS = {
    "S13": {"LAB5"}, "S14": {"J21"}, "S15": {"PWR_ON_KEY"}, "S16": {"J21", "PWR_ON_KEY"}, "S17": {"VCC_3V3_MKEY"},
    "S18": {"LIME3V3"}, "S19": {"DISP12"}, "S20": {"VBUS_RTLA"}, "S21": {"VBUS_RTLB"}, "S22": {"VBUS_HFP"},
    "S23": {"VBUS_LABPORT"}, "S35": {"BONI13V8_PORT"}, "S36": {"BIAS_SB_LNA"}, "S41": {"BIAS_SB_LNA"},
    "PPS": {"E3_GNSS_PPS", "UART6_RX", "UART6_TX"}, "S25": {"E3_GNSS5V", "E3_GNSS_RESET_N"},
}
NO_GND = {"S15", "S02B"}  # KEY joins J503, whose GND contact already carries the S14 return; S02B: J307/J203 have no free contact, the return is in S02 (W2 PWR-L6-PLACE)
GND_GROUP_SKIP = {("S06", "MFJ"), ("S07", "MFJ")}  # shunt path and #2813 switch: no return current in that connector
GND_CURRENT = {"S06": (0.01, None), "S07": (0.05, None)}  # chip/control ground only (INA228, #2813 logic)
# Module end of a wire: which contact it lands on, (segment, unit, net) -> "REF.PIN (note)".
END_PIN = {
    ("S05", "PACK", "E1_SHUNT_P"): "F101.2 (вихід тримача F101 біля плюса паку; провід паяється в майданчик J117 носійної плати PACK_FUSE, W2 GR-4)", ("S05", "PACK", "GND"): "U101.P- (P− BMS)",
    ("S06", "INA", "E1_N"): "R101.2 (клема VIN− модуля 5832)", ("S06", "INA", "E1_SHUNT_P"): "R101.1 (клема VIN+ модуля 5832)",
    ("S06", "INA", "GND"): "U102.7", ("S07", "SWM", "GND"): "U106.GND",
    ("S10", "CHG", "GND"): "U110.BAT-", ("S13", "HUB", "GND"): "U510.JP5_4",
    ("S17", "Q6A.CORE", "GND"): "U500.GND", ("S18", "RISER", "GND"): "U530.GND", ("S19", "DISP", "GND"): "U520.DC_GND",
    ("S25", "GNSS", "GND"): "U304.P1.2", ("PPS", "GNSS", "GND"): "U304.P1.2 (повернення PPS/UART6, разом із GND S25)",
    ("S26", "VEML", "GND"): "U308.GND",
    ("S27", "FAN1", "GND"): "FAN301.GND", ("S35", "BONI", "GND"): "A406.SHIELDS", ("S41", "SPOD", "GND"): "W425.RETURN",
    ("S10", "CHG", "E1_CHG_NTC"): "U110.NTC",
}
ESCC_IMAX = {28: 1.5, 26: 2.5, 24: 3.5, 22: 5.0, 20: 7.5, 18: 10.0}

# --- Design currents: net -> (continuous A, protective/limiting A, protection, source)
# Signals not listed: 0.05 A, no protection value (logic level).
NET_CURRENT = {
    "E1_CELL4": (4.6, 7.5, "BMS Daly (DOCP 40±10 A) — провід паку до F101, усередині паку", "02 §2–3 (модель 4.6 A з Lime)"),
    "E1_SHUNT_P": (4.6, 7.5, "F101 7.5 A (у паку)", "02 §3"),
    "E1_N": (4.6, 7.5, "F101 7.5 A", "02 §3"),
    "E1_SW": (4.6, 7.5, "F101 7.5 A (вище за течією)", "02 §3"),
    "SYS12": (4.0, 7.5, "F101 7.5 A вище; власна межа D36V50F12 — TBD", "02 §2 (≈4 A пік з Lime)"),
    "E1_LAB5_RAW": (3.2, 7.5, "F101 7.5 A вище; F102 4 A — після U108 на міді PWR", "E1.json lab5_budget (3.2 A тривало, 4 A перехідно)"),
    "LAB5": (1.0, 4.0, "F102 4 A", "бюджет гілки 1.0 A — рішення asm; загальний бюджет LAB5 3.2 A (E1-05)"),
    "LAB5_RLY": (0.10, 1.50, "PTC F104 MF-MSMF075/24-2 (Itrip 1.50 A при 23 °C; Ihold 0.75 A, 0.49 A при 70 °C)",
                 "2 котушки G6K ≈21.1 mA (08 крок 10); R-E1-09; Bourns MF-MSMF REV. AO (прочитано 07.11.2026)"),
    "J21": (2.5, 4.0, "F201 4 A + eFuse U201 ≈4 A", "02 §2 (2.5 A з Lime)"),
    "DISP12": (1.27, 1.70, "eFuse U202 RILM 1.96k ≈1.70 A", "E2.json U202; 02 §2 (1.27 A на межі 14 W)"),
    "AUX12": (0.42, 0.75, "PTC MF-MSMF075/24-2, утримання 0.75 A", "02 §2"),
    "LIME3V3": (1.2, 2.2, "eFuse U203 RILM 1.65k: 1.80–2.20 A", "E2.json U203; 02 §2 (≈1.2 A модель)"),
    "VCC_3V3_MKEY": (1.2, 2.2, "U203 після; бортовий захист Q6A — TBD", "живить LIME3V3"),
    "E1_USB_PD_RAW": (3.0, 3.5, "eFuse U109 RILM 953 Ω ≈3.50 A", "E1.json U109"),
    "E1_USB_PD_SAFE": (3.0, 3.5, "eFuse U109 ≈3.50 A", "E1.json U109"),
    "E1_SERVICE_P": (3.0, 5.0, "F103 5 A", "E1.json F103; v2.1 сервіс заблоковано"),
    "VBUS_RTLA": (0.673, 0.673, "U501 TPS2553 (старт R501 43.2k: 0.544–0.673 A)", "E5 §3"),
    "VBUS_RTLB": (0.673, 0.673, "U210 TPS2553 (старт R248 56.2k — менша межа, ніж 43.2k)", "E2.json R248; E5 §3"),
    "VBUS_HFP": (0.989, 0.989, "U503 TPS2553 (старт R509 28.7k: 0.825–0.989 A)", "E5 §6"),
    "VBUS_LABPORT": (0.825, 0.825, "U502 TPS2553 (R505 34.8k: 0.678–0.825 A)", "E5 §5"),
    "BIAS_CH1": (0.339, 0.339, "U206 TPS2553 (RILIM 88.7k: 265–339 mA)", "02 §2"),
    "BIAS_CH2_PORT": (0.339, 0.339, "U207 TPS2553 (88.7k)", "02 §2"),
    "BIAS_CH3_PORT": (0.339, 0.339, "U208 TPS2553 (88.7k)", "02 §2"),
    "BIAS_CH4": (0.192, 0.192, "U209 TPS2553 (162k: 144–192 mA)", "02 §2"),
    "BIAS_SB_LNA": (0.065, 0.192, "U221 TPS2553 (162k: 144–192 mA)", "E2.json U221 (LaNA WB ≤65 mA)"),
    "LNB13V2": (0.30, 0.499, "eFuse U212 (RILM 2.05k: 0.405–0.499 A)", "02 §2"),
    "BONI13V8_PORT": (0.065, 0.153, "eFuse U214 (RILM 7.15k: 0.122–0.153 A)", "02 §2"),
    "E1_CHG_INHIBIT_LOW": (0.01, 0.01, "R121 2.2k", "E1.json"),
    "E3_FAN5": (0.25, 4.0, "F102 4 A (ключ Q304 без межі струму; лише мідь CTRL до F301)", "бюджет вентилятора — рішення asm, виміряти"),
    "E3_FAN5_P": (0.25, 1.50, "PTC F301 MF-MSMF075/24-2 (Itrip 1.50 A при 23 °C; Ihold 0.75 A, 0.49 A при 70 °C)",
                  "бюджет вентилятора — рішення asm, виміряти; Bourns MF-MSMF REV. AO (прочитано 07.11.2026)"),
    "E3_GNSS5V": (0.10, 0.192, "U315 TPS2553DBVR-1 (RILIM 162k: 144–192 mA)",
                  "LC76G IPEAK ≤58 mA (Quectel LC76G HD V1.3, табл. 14) + плата Waveshare; бюджет 0.10 A — рішення asm (E3-08)"),
    "E5_IMU5V": (0.20, 0.339, "U553 TPS2553DBVR, сталий струм (RILIM 88.7k: 265–339 mA)", "бюджет паку IMU — рішення asm, виміряти (E5-04)"),
    "E3_BLOWER_GND": (0.50, 4.0, "F102 4 A (ключ Q305 без межі струму)", "E3-03: 0.25 A тривало / 0.50 A старт"),
    "VCC_5V_PERI": (0.10, 4.5, "бортовий SGM40666 Q6A (≈4.5 A, 02 §2)", "лише Q6A: у шлейф S01 не йде (R-E3-15); бюджет 0.10 A — рішення asm"),
    "3V3_Q6A": (0.10, 0.10, "PMIC Q6A (межа не опублікована)", "бюджет шини логіки — рішення asm"),
    "AON3V3": (0.01, 0.01, "TPS70933", "02 §4 (INA228 ≤750 мкА)"),
    "E3_PICO3V3": (0.02, 0.02, "LDO Pico", "VEML7700 — малий струм"),
}
# Per-segment overrides (segment, net) -> (cont, prot, protection, source)
SEG_CURRENT = {
    ("S10", "E1_N"): (3.0, 7.5, "F101 7.5 A (вузол N)", "IP2368 RISET 15k = 3 A (02 §5)"),
    ("S28", "LAB5"): (0.50, 4.0, "F102 4 A", "E3-03: старт 0.50 A"),
    ("S13", "LAB5"): (0.30, 4.0, "F102 4 A", "бюджет хаба — рішення asm, виміряти"),
}
# W2 PWR-L6-PLACE third pass: the J307 <-> J203 conductors of S02 leave the bundle as branch S02B (SEGMENT_BRANCHES), because
# J203 is the top-entry header of PWR-B zone 2 (mechanical/params/mechanical.json harness_routes branches.S02B). Inserted here,
# after the NET_CURRENT / SEG_CURRENT rows, so that the line citations into this file (pcb/generated/netclasses.json) keep their
# numbers. The row stands just before S02 in SEGMENTS, so that the harness router (tools/build_assembly_docs.py route) tries
# the branch first for its 20 nets (SEGMENT_NETS) and S02 for every other CTRL <-> PWR net.
SEGMENT_NETS["S02B"] = {"FAULT_LNA4", "FAULT_RTLA", "FAULT_RTLB", "FLT_BONI", "FLT_LIME3V3", "FLT_LNB", "FLT_SB_LNA", "I2C0_SCL",
                        "I2C0_SDA", "IMU_RX", "IMU_TX", "INA228_ALERT", "OVP_LNB_N", "PG_BONI", "PG_LNB", "PICO_DISP_EN",
                        "PICO_OFF", "PTC_AUX", "PWR_BUTTON", "SLED_DET"}  # J307.1-20 = J203.1-20 (design/E3.json, design/E2.json)
SEGMENTS.insert(next(i for i, s in enumerate(SEGMENTS) if s[0] == "S02"), (
    "S02B", "CTRL", "PWR", "Сигнали S02-SIG-2: CTRL J307 ↔ PWR-B J203 (гілка S02)", None, "TBD (CAD)",
    "20 проводів PHD 22 AWG (SPHD-001T-P0.5) від J307 (S20B-PHDSS, боковий вхід, зона 0 CTRL) до J203 (B20B-PHDSS(LF)(SN), верхній "
    "вхід, зона 2 нижнього краю PWR-B); джгут прямий, J307.k ↔ J203.k, розпіновка без змін; відходить від S02 у зоні 0 CTRL; траса — "
    "harness_routes branches.S02B механічної моделі (повз бобишку кріплення дисплея); радіус згину над J203 і примірка — OPEN "
    "(W2 PWR-L6-PLACE, третій прохід, build/15)"))

# Wire colours by net (regex, colour) — project convention, first match wins.
COLOURS = [
    (r"^GND$", "чорний"), (r"^CHASSIS$", "жовто-зелений"),
    (r"^(E1_CELL4|E1_SHUNT_P|E1_N|E1_SW|E1_SERVICE_P|E1_USB_PD_RAW|E1_USB_PD_SAFE)$", "коричневий"),
    (r"^(SYS12|J21|DISP12|AUX12)$", "жовтий"),
    (r"^(LAB5|E1_LAB5_RAW|VBUS_|E3_FAN5|VCC_5V_PERI|BIAS_SB_LNA|E3_GNSS5V|E5_IMU5V)", "червоний"),
    (r"^(LNB13V2|BONI13V8_PORT)$", "фіолетовий"),
    (r"^BIAS_CH", "рожевий"),
    (r"^(3V3_Q6A|AON3V3|LIME3V3|VCC_3V3_MKEY|E3_PICO3V3)$", "помаранчевий"),
    (r"(SDA|SDA_)", "синій"), (r"(SCL)", "білий"),
    (r"^(UART|IMU_)", "зелений"),
    (r"^(EN_|PICO_|CHG_INHIBIT|SW_|K[12]_ON)", "сірий"),
    (r"^(FAULT_|FLT_|PG_|DCS_|OVP_|PTC_|MCP_INT|INA228_ALERT|SLED_DET)", "блакитний"),
    (r".*", "білий"),
]
INSULATION = ("PTFE, посріблена мідь багатодротова, −60…+200 °C (Alpha Wire, assembly_items AI-WIRE-PTFE): 26 AWG 5853, 20 AWG 5856 і 18 AWG 5857 — "
              "MIL-W-16878/4 type E, 24 AWG 2844/7 і 22 AWG 2845/7 — MIL-W-16878/6 type ET; ⌀ ізоляції в межах клеми; артикул за кольором — "
              "підсумок закупівлі")
# Hook-up wire per gauge (W2 SRC-1, build/15 «Провід, стрічка й інструмент (W2 SRC-1)»): Alpha Wire PTFE, silver-plated copper.
# AWG -> (Alpha Wire item, MIL-W-16878 type, insulation OD mm, OD tolerance mm), from the Alpha Wire customer specifications read
# 07.11.2026 (design/parts/snapshots/2026-11-07-w2-src1-manual.json web:alphawire-*; inch values x 25.4). Per gauge the thinnest
# series whose OD range fits every crimp terminal the gauge ends in (WIRE_INSULATION_RANGE): 2843/7 (ET, 0.79 +/- 0.05) is under the
# PH minimum, so 26 AWG is type E 5853; type ET is made only up to 22 AWG (Alpha catalogue), so 20/18 AWG are type E.
WIRE = {
    28: ("2842/7", "MIL-W-16878/6 type ET, 250 V", 0.69, 0.05),
    26: ("5853", "MIL-W-16878/4 type E, 600 V", 0.99, 0.10),
    24: ("2844/7", "MIL-W-16878/6 type ET, 250 V", 0.91, 0.05),
    22: ("2845/7", "MIL-W-16878/6 type ET, 250 V", 1.07, 0.05),
    20: ("5856", "MIL-W-16878/4 type E, 600 V", 1.47, 0.10),
    18: ("5857", "MIL-W-16878/4 type E, 600 V", 1.75, 0.13),
}
# Alpha Wire colour codes of the ten colours every series above is made in (specifications; DigiKey forum code list, DigiKey DE pages);
# a harness colour outside them is bought white and told apart by the printed marker (build/18).
WIRE_COLOUR_CODE = {"білий": "WH", "чорний": "BK", "червоний": "RD", "зелений": "GR", "жовтий": "YL", "синій": "BL", "коричневий": "BR",
                    "помаранчевий": "OR", "сірий": "SL", "фіолетовий": "VI"}
WIRE_PUTUP = "005"  # 100 ft (30.48 m) spool: the shortest put-up every WIRE series lists (5857 also lists 50 ft, code not read)
WIRE_SPOOL_M = 30.48  # length of one WIRE_PUTUP spool, m (100 ft)
# Insulation OD each crimp terminal accepts, mm (None: no limit given): JST-PH SPH-002T-P0.5S, MOLEX-43030, MOLEX-5556 (SOURCES).
WIRE_INSULATION_RANGE = {"PH": (0.8, 1.5), "MF": (None, 1.85), "MFJ": (1.30, 3.10), "MF2": (None, 1.85), "PHD": (1.0, 1.5)}

# High-speed / factory cable assemblies: id -> (title, net regex, ends, parts)
ASSEMBLIES = [
    ("C-HDMI", "HDMI Q6A → Wisecoco", r"^E5_HDMI_", "Q6A.HDMI → HDMIA → DISP",
     "FPC-набір (W2 MECH-4, build/15 «Кабель HDMI (W2 MECH-4)»; траса R-HDMI-ROUTE у fit-report — модель): Adafruit 3550 або 3549 у HDMI Q6A, "
     "стрічка 3560 10 см з феритом Würth 74278011, вставка HDMI_INSERT біля BMS, стрічка 3560 10 см, Adafruit 3548 у вхід Wisecoco (assembly_items "
     "AI-HDMI-FPC, AI-HDMI-FPC-R, AI-HDMI-FPC-FLEX, AI-HDMI-FPC-3548, AI-HDMI-FERRITE); обмотка заземленою мідною стрічкою (AI-HDMI-CU-TAPE, TBD); "
     "pin 18 через U506 на вставці (E5 §8, домен HDMI_INSERT); TMDS не розплітати; лінк і EMI — стенд"),
    ("C-T7", "USB3 Q6A J5 нижній → T7", r"^E5_(T7_|VBUS_J5|VBUS_T7)", "Q6A.J5 → T7A → T7",
     "цілісний екранований кабель A–C ≤0.5 м + вставка U505 (E5 §7): VBUS-жилу розрізано лише на вставці (J515 від J5, J516 до T7), GND-жилу не розривають (відвід J517), S24 — вилка J514 (W2 GR-4); перевірка 5000M/uas"),
    ("C-HUB", "USB2 Q6A J2 P3 → CH334F JP5", r"^E5_HUB_", "Q6A.J2 → HUB", "VBUS Q6A не підключати (E5 §2)"),
    ("C-TOUCH", "USB2 Q6A J2 P2 → touch Wisecoco", r"^E5_TOUCH_", "Q6A.J2 → DISP", "лише D+/D−/GND, ферит Würth 74271140"),
    ("C-RTLA", "USB2 H2 → RTL-A", r"^RTLA_D", "HUB → RTLA", "пігтейл H2 → USB-A J543; VBUS лише з S20"),
    ("C-RTLB", "USB2 Q6A J5 верхній → RTL-B", r"^RTLB_D", "Q6A.J5 → RTLB", "Lindy 36700 0.2 м + Würth 74271112; VBUS лише з S21"),
    ("C-HFP", "USB2 H4 → HF+ micro-USB", r"^HFP_D", "HUB → HFP", "екранований пігтейл OD ≤4.9 мм, ≥55 мм прямого дроту"),
    ("C-LAB", "USB2 H3 → LAB USB-A J501", r"^E5_LABPORT_D", "HUB → LABUSB", "VBUS лише з S23"),
    ("C-PCIE", "PCIe x1 Q6A → R44SF → Lime", r"^E5_PCIE_", "Q6A.MKEY → RISER → LIME", "ADT-Link R44SF 5 см; 3.3 V хоста відділено (E5 §10)"),
]

# --- Labels (build/18) ---------------------------------------------------------
# Panel RF ports: ref -> (label text, DC on the port). Must cover every panel RF connector.
PORT_LABELS = {
    "J401": ("P1 VHF-137", "без DC"),
    "J402": ("P2 UHF", "DC 4.3 V після DC-sense; ніколи >5.5 V"),
    "J403": ("P3 L-BAND", "DC 4.3 V після DC-sense; ніколи >5.5 V"),
    "J404": ("P4 LNB (F)", "DC 13.2 V (12.5 V з QRO.cz); заглушка непровідна"),
    "J405": ("P5 HF (BNC)", "DC 13.8 V лише в профілі Boni"),
    "J406": ("P6 VHF2/AIS", "без DC"),
    "J407": ("P7 GNSS", "DC ≈3.1 V від LC76G"),
    "J408": ("P8 WIDE", "DC 4.3 V лише з LNA ch4"),
    "J413": ("RX1 (Lime)", "без DC"),
    "J414": ("RX2 (Lime)", "без DC"),
    "J415": ("REF IN (Lime)", "без DC"),
}
LABELS = [
    # id, place, text, material, size mm, source
    ("L-RX", "лице, біля дисплея", "ЛИШЕ ПРИЙОМ · без передавача", "полієстер, УФ-стабільний ламінат", "40×8", "правило «лише прийом»"),
    ("L-USBC", "нижній край, USB-C", "USB-C · єдиний вхід живлення (PD)", "полієстер, УФ-стабільний ламінат", "30×8", "STACK §5.8"),
    ("L-LABUSB", "нижній край, LAB USB-A", "LAB USB-A · 5 V ≤0.75 A", "полієстер, УФ-стабільний ламінат", "30×8", "E5 §5"),
    ("L-LABBUS", "нижній край, LAB BUS", "LAB BUS · AUX 12 V · I2C", "полієстер, УФ-стабільний ламінат", "30×8", "E5 §9"),
    ("L-AUDIO", "нижній край, 3.5 мм", "АУДІО 3.5 мм", "полієстер, УФ-стабільний ламінат", "20×6", "STACK §5.8"),
    ("L-T7", "задня стінка, гермоввід T7 (x 150, y 66, M-06, T7_GLAND)", "T7 USB3", "полієстер, УФ-стабільний ламінат", "20×6", "STACK §5.8; mechanical.json t7_gland"),
    ("L-IMU", "задня стінка, GX16-4", "IMU · GX16-4 · 5 V · ключ ▲", "полієстер, УФ-стабільний ламінат", "30×8", "E5 §9"),
    ("L-HATCH", "кришка сервісного лючка", "СЕРВІС: UART5 · EDL · J21 · USB-A", "полієстер, УФ-стабільний ламінат", "45×8", "STACK §5.8"),
    ("L-J21", "сервісний лючок, біля J503", "J21 unplugged before USB-C", "поліімід", "40×6", "05 §5.5; STACK §11.5 #16"),
    ("L-SUN", "внутрішній бік козирка", "не лишати лицем до сонця", "полієстер, УФ-стабільний ламінат", "40×6", "05 §2 (козирок); STACK §5.8"),
    ("L-BAT", "пак 4S1P", "Li-ion 4S1P · 14.4 V ном. · 72 Wh · F1 7.5 A · не перевозити літаком", "поліімід", "60×20", "08 крок 0 п. 2; 02 §2"),
    ("L-F101", "на носійній платі PACK_FUSE біля тримача F101 (біля лотка паку; доступ — після відкриття шва, R-F101-ACCESS)",
     "F1 7.5 A — вийняти для зберігання >2–4 тиж.", "поліімід", "30×6", "02 §9 п. 9; E1 F101"),
    ("L-DISP12", "кабель DISP12 біля бареля", "DISP12 · 12 V · полярність TBD (E5-01)", "поліімід, обгортковий", "25×6", "E5-01"),
    ("L-LABRXA", "кабель RTL-A", "LABRXA", "поліімід, обгортковий", "20×6", "04 §6"),
    ("L-LABRXB", "кабель RTL-B", "LABRXB", "поліімід, обгортковий", "20×6", "04 §6"),
    ("L-LIME-X2", "кабель CAB.01075 X2", "Lime X2 → RX1", "поліімід, обгортковий", "20×6", "04 §8 рядок 25"),
    ("L-LIME-X4", "кабель CAB.01075 X4", "Lime X4 → RX2", "поліімід, обгортковий", "20×6", "04 §8 рядок 25"),
    ("L-LIME-J4", "кабель CAB.01075 J4", "Lime J4 → REF IN", "поліімід, обгортковий", "20×6", "04 §8 рядок 25"),
    ("L-LIME-X1", "кабель CAB.01075 X1 (усередині)", "Lime X1 → ANNE-50+ (лише навантаження, не на панель)", "поліімід, обгортковий", "30×6", "05 §5.2"),
]

# --- Fasteners and torques (build/17) ------------------------------------------
# id, place, part, qty, spares, receiving, torque, torque source, washer/locking, step
FASTENERS = [
    ("F01", "Q6A → стійки на середній пластині", "гвинт M2.5×6 TX8 A2 (STACK, рядок «Корпус»)", "4", "2",
     "стійка M2.5 F-F 6 мм (mechanical.json q6a_mount; AI-STANDOFF-M25-6)", "TBD — виробник не публікує; задати за купоном (див. §2)", "—", "—", "E3"),
    ("F02", "стійки Q6A → пластина 2 мм Al", "гвинт M2.5 A2 з лицьового боку пластини (довжина TBD, AI-M25-Q6A-PLATE)", "4", "2",
     "наскрізний отвір ⌀2.9 у пластині (M-07 Q6A1-4; різьбу не нарізати)", "TBD — купон", "—", "пружинна шайба M2.5", "E3"),
    ("F03", "кришка Armor 7056A (варіант B охолоджувача)", "гвинт M2.5 зі стійками комплекту Radxa", "за комплектом", "2",
     "стійки M2.5 крізь отвори ⌀3.5", "TBD — за інструкцією Radxa", "—", "—", "E3"),
    ("F04", "п'єдестал Lime → пластина", "гвинт M3 (тип і довжина TBD, AI-M3-LIME)", "2", "2",
     "отвори ⌀3.4 LP1–LP2 у пластині (M-07); різьба — у п'єдесталі Al, не в пластині", "TBD — купон", "—", "—", "E3"),
    ("F05", "модуль Pololu #2813 U106 → задня стінка", "двосторонній акриловий скотч 3M VHB 4910 1.0 мм (mechanical/params/parts.json vhb_4910; "
     "позиція закупівлі AI-VHB-4910-MODULES) на друкованому майданчику 12 × 14 задньої стінки: монтажних отворів у #2813 немає — усі 20 отворів є "
     "виводами (креслення Pololu psw03b, 12.01.2016, https://www.pololu.com/file/0J1102/big-pushbutton-power-switch-with-reverse-voltage-protection-dimension-diagram.pdf, "
     "прочитано 07.11.2026)", "1 смужка 12 × 14", "1",
     "майданчик x 97.46–109.46, y 44–58, верх z 4.5 (M-06 «Бобишки модулів»; mechanical.json module_mounts) — під серединою плати, поза рядами виводів",
     "—", "—", "дроти S07 закріпити стяжкою біля плати (скотч не несе натягу проводів)", "E8"),
    ("F06", "PWR-A → пластина", "зовнішня різьба M3 стійок F45 з боку компонентів (замість гвинта M3×4, W2 MECH-3) + шайба-прокладка 0.4 мм "
     "(AI-SHIM-M3-0.4): шпилька 3.594–4.064 мм при PWR-A 1.664 мм (MODEL, W2 MECH-8; для всього допуску товщини 1.44–1.76 мм — 3.69–3.84 мм) — уся різьба гайки PEM (1.53), кінець не далі тильної грані пластини (generated/fastener-stacks.json PWR_A-PLATE)", "7", "2",
     "гайка PEM F-M3-1 урівень з лицьовою гранню пластини (M-07 PWR1–PWR7; AI-PEM-F-M3-1): плата 1.664 (6 шарів, MODEL) + шайба 0.4 + пластина 2.0", "TBD — PEM моменту не дає; купон на зразку пластини (§2)",
     "PEM-F", "—", "E2"),
    ("F07", "RF → пластина", "гвинт M3×5 ISO 14580 A2 TX10 з боку компонентів (AI-M3X5-ISO14580)", "6", "2",
     "стійка PEM SO-M3-3ZI 3 мм, голівка врівень з лицьовою гранню пластини (M-07 RF1–RF6; AI-PEM-SO-M3-3ZI)", "TBD — купон (§2)", "PEM-SO",
     "—; бондинг RF GND — окрема точка BOND-RF (F26)", "E4"),
    ("F08", "CTRL → бобишки передньої половини", "гвинт M2.5 A2 TX8 (довжина TBD, AI-M25-CTRL-ENC)", "6", "2",
     "вставка TC-M2,5x4 (boards.json CTRL: 6 отворів ⌀2.7)", "TBD — купон (§2)", "CNCK-M25", "—", "E5"),
    ("F09", "INA228 5832 → задня стінка", "гвинт M2.5×6 ISO 14580 A2 TX8 (AI-M25X6-MODULES; плата 1.6 + 4.4, з них 4.0 у вставці; вікно 5.35–6.1 мм, generated/fastener-stacks.json INA228; Adafruit 3299: M2.5 підходить до отворів ⌀2.5 її плат)",
     "2", "2",
     "вставка TC-M2,5x4 у друкованих бобишках ⌀7.2 задньої стінки (верх z 6.0, отвір 5.0 = вставка + 1.0; M-06 «Бобишки модулів») під отворами ⌀2.5 (2.54, 17.78) і (22.86, 17.78) "
     "файла плати Adafruit (github.com/adafruit/Adafruit-INA228-PCB, 61b0d99, прочитано 07.11.2026); край гребінки лежить на 2 друкованих упорах ⌀6",
     "TBD — купон (§2)", "CNCK-M25", "—", "E8"),
    ("F10", "CH334F 5997 → задня стінка", "гвинт M2.5×6 ISO 14580 A2 TX8 (AI-M25X6-MODULES; плата 1.6 + 4.4, з них 4.0 у вставці; вікно 5.35–6.1 мм, generated/fastener-stacks.json HUB-5997)", "4", "2",
     "вставка TC-M2,5x4 у друкованих бобишках ⌀7.2 задньої стінки (верх z 6.0, отвір 5.0 = вставка + 1.0; M-06 «Бобишки модулів») під 4 отворами ⌀2.5 (2.54 від країв) файла плати "
     "Adafruit (github.com/adafruit/Adafruit-CH334F-Breakout-PCB, a29ea77, прочитано 07.11.2026)", "TBD — купон (§2)", "CNCK-M25", "—", "E8"),
    ("F11", "IP2368 → пластина", "кріплення TBD: у роздрібної плати IP2368 немає описаних отворів (components/ip2368_4s_100_w_pd_board_charge_only_bz.md — лише 48 × 34 мм; "
     "креслення не знайдено, 07.11.2026); варіанти — ізолювальні стійки за отворами отриманої плати або термостійкий двосторонній скотч; виміряти при вхідному контролі",
     "TBD", "—", "лицьовий бік пластини вгорі праворуч (layout ip2368)", "—", "—", "—", "E2"),
    ("F12", "половини корпусу", "гвинт M3 ISO 14580 A2 TX10 (довжина TBD, AI-M3-CLOSURE) + ущільнювальна шайба (AI-SEAL-WASHER-M3)", "14", "2",
     "вставка TC-M3x5.7 (mechanical.json closure, 14 бобишок)", "TBD — купон (§2)", "CNCK-M3", "EPDM-шнур у пазу (build/15)", "E10"),
    ("F13", "кришка сервісного лючка", "невипадний гвинт M3 (AI-M3-HATCH)", "2", "2", "вставка TC-M3x5.7", "TBD — купон (§2)", "CNCK-M3", "власна прокладка лючка", "E10"),
    ("F14", "прохідники SMA P1–P3, P6–P8, RX1, RX2, REF IN", "гайка й шайба з лицьового боку (зовні), корпус 8 HEX — на Al-кутнику зсередини: P2, P3, P6, P8 — "
     "пігтейли Taoglas CAB.718 (гайка HEX8 × 1.8, шайба ⌀6.35/10.2, корпус 8 HEX × 3.4; база деталей J-SMA-PANEL-RFBOARD), P1 — Adam Tech CA-DKCA1-305L5-APAJ "
     "(гайка 8 HEX × 1.7, шайба ⌀10.2/6.5; J-SMA-PANEL), P7 — SMA-кінець Taoglas CAB.011, RX1/RX2/REF IN — Taoglas CAB.01075", "9", "2",
     "стінка 4.5 мм (ASA 2.5 + Al-кутник 2.0): P2, P3, P6, P8 — виріз ⌀6.5 з лискою 6 +0.08/0 у стінці ASA за кресленням CAB.718 (SPE-12-8-100, прочитано "
     "07.11.2026), отвір кутника ⌀6.5; P1, RX1, RX2, REF IN — отвір ⌀6.5; різьба 1/4-36 довжиною 11.4: товщину шайби CAB.718 і Adam Tech не розмірено "
     "(після гайки й 3 витків лишається 2.48 і 2.32 мм), гайку й шайбу CAB.01075 і різьбу CAB.011 — теж (R-SMA-THREAD OPEN)",
     "за даташитом обраного прохідника; довідково 0.57 N·m (Würth WR-SMA, вимога IP67)", "WE-SMA",
     "стопорна шайба; кілець у кресленнях CAB.718, Adam Tech і CAB.01075 немає — ущільнення вирізу T-07", "E7"),
    ("F15", "стикування SMA (нержавіючі)", "—", "—", "—", "—", "0.9 N·m ключем TOJOIN/TekBox; латунні гнізда приладів — пальцями (09 правило 7)",
     "STACK §5.3", "—", "E4"),
    ("F16", "прохідник F (P4)", "гайка 11.0 HEX × 2.4 і шайба ⌀12.0/9.7 × 0.4 адаптера F/F Cinch VFA340 (база деталей J404; креслення ISS 3, "
     "https://www.cinch.com/media/drawings/products/rf-microwave/adapters/dr-ccs-vit-vfa340.pdf, прочитано 07.11.2026)", "1", "1",
     "отвір ⌀9.7 у стінці 4.5 мм; фланець 11 HEX × 1.5 зовні (коротка сторона 7.6 — під F-вилку W401), шайба й гайка зсередини на Al-кутнику; "
     "усередині лишається 3.6 мм різьби 3/8-32 під F-вилку W402 (R-SMA-THREAD виконано в моделі)",
     "TBD — момент на кресленні Cinch не наведено (R-BULKHEAD-NUTS: гайка ⌀12.7 у моделі)", "—", "—", "E7"),
    ("F17", "BNC-прохідник (P5)", "гайка адаптера BNC/SMA Amphenol RF 242181 (база деталей J405; DigiKey: у комплекті прокладка, стопорна шайба й гайка)", "1", "1",
     "стінка 4.5 мм; виріз — TBD: креслення не читається (https://www.amphenolrf.com/en-us/assets/file/4065787441/, 403, 07.11.2026)",
     "TBD — креслення Amphenol не прочитано (R-BULKHEAD-NUTS OPEN)", "—", "—", "E7"),
    ("F18", "гніздо GX16-4 (J504)", "шестигранна гайка 18.8 мм (Olimex)", "1", "1", "отвір ⌀16 у задній стінці, пласке гніздо 3 мм (M-06, GX16_IMU)",
     "TBD — Olimex не публікує момент", "OLIMEX-GX16", "—", "E8"),
    ("F19", "LAB BUS GX12 (J505)", "гайка Kinghelm KH-GX12-6P (комплект; 14.6 під ключ, ⌀16.9 по кутах, за кресленням LCSC C18203264)", "1", "1",
     "виріз ⌀12.0 з лискою 11.2 у нижній стінці 2.5 мм (M-02 LAB_BUS); фланець ⌀15 × 1.7 зовні, різьба M12×0.75 довжиною 8.8, гайка зсередини",
     "TBD — момент не наведено", "KINGHELM-GX12", "заглушка LAB BUS (10-bom рядок 90); IP на кресленні не наведено (T-07)", "E7"),
    ("F20", "енкодери PEC11R-4220F (ENC301/302)", "гайка M7×0.75 + шайба (комплект)", "2", "1 запасний енкодер", "бобишка: O-ring + стінка 2.4–3 + шайба 0.5 + гайка 2.0 ≤6.5",
     "≤1.0 N·m (10.2 kgf·cm макс.)", "PEC11R", "шайба з комплекту", "E5"),
    ("F21", "кнопка живлення SW301 (E-Switch PV6F240SS)", "гайка M16×1.0 (комплект кнопки; окрема гайка E-Switch PV2PV3PV6HEX16, DigiKey DE "
     "141-PV2PV3PV6HEX16-ND «HEX NUT FOR PV2 SERIES», 07.11.2026 — розмір не наведено ні там, ні в PV2/PV6; виміряти при вхідному контролі)", "1", "—",
     "виріз ⌀16.00 +0.20 у верхній стінці 2.5 мм (панель 1–10 мм) на x 155.5, z 50; гайка зсередини — у резерві ⌀22 × 3.5 (nut.PWR_KEY, припущення) "
     "у вирізі пластини: 0.5 мм до верхнього Al-кутника, 0.8 мм до плати HDMI (R-PWR-KEY-NUT OPEN); затягувати в E5 до встановлення пластини (E6), "
     "ключ підводити з тильного боку — після E6 гайку закривають пластина й кутник", "0.6 N·m (рекомендований момент кріплення)", "PV6", "—", "E5"),
    ("F22a", "клапани LTW VENT-PS1NBK-O8002 V1/V2 (×2)", "без гайки: різьба M12×1.5 у гнізді", "2", "—",
     "різьбове гніздо 4.0 мм (V1 — права стінка, V2 — лице; mechanical.json vents)", "0.59–0.78 N·m (6.0–8.0 kgf·cm)", "LTW-VENT",
     "MOLYKOTE 4 — ніколи на силіконові кільця клапанів (STACK)", "E7"),
    ("F22b", "клапани LTW VENT-PS1YBK-O8002 коробок Gainta (×3)", "гайка M12×1.5 (комплект)", "3", "—", "наскрізний отвір 2.0–3.5 мм у стінці коробки",
     "0.59–0.78 N·m (6.0–8.0 kgf·cm)", "LTW-VENT", "MOLYKOTE 4 — ніколи на силіконові кільця клапанів (STACK)", "E9"),
    ("F23", "гермоввід паку IMU LAPP SKINTOP MS-SC-M12", "гайка-ковпак і контргайка", "1", "1", "отвір 12 мм у стінці Hammond 1550Z101",
     "TBD — інструкція MS-SC-M не прочитана (M12×1.5: 8 N·m для MS-M, категорія A — лише орієнтир)", "LAPP-MSM", "—", "E9"),
    ("F24", "кришка паку IMU Hammond 1550Z101", "латунний гвинт M4×20 замість штатних нержавіючих M4-0.7×20 (STACK §2.8, рядок «Пак IMU»; AI-M4X20-BRASS)", "2", "2",
     "корпус Hammond (штатно 2 гвинти кришки)", "0.50–0.75 N·m — значення Hammond для штатних нержавіючих гвинтів; для латунних — "
     "перевірити купоном (§2), не перевищувати 0.75 N·m", "HAMMOND-1550Z101", "шов перекрито провідною стрічкою", "E9"),
    ("F25", "штативна гайка 1/4-20 UNC", "захоплена оцинкована гайка 7/16 in AF", "1", "1", "шестигранне гніздо 11.3 AF бобишки ASA 100 % на цоколі 5 мм",
     "приймання: момент ≥3 N·m, 20 циклів (тест, не момент затягування)", "STACK §5.8", "—", "E8"),
    ("F26", "бондинг CHASSIS: BOND-RF, екран USB-C, корпус GX16, пластина", "кабельний наконечник + гвинт M3 (AI-M3-BOND)", "4", "2",
     "гола точка пластини (BOND-RF на M-07; 08 крок 5 п. 2)", "TBD — купон (§2)", "—", "зубчаста шайба", "E10"),
    ("F27", "вентилятор Noctua NF-A4x10", "кріплення з комплекту Noctua", "4", "—", "задній отвір", "TBD", "—", "—", "E3"),
    ("F28", "повітродувка Delta BFB0305HA-C", "TBD за кресленням Delta", "TBD", "—", "лицьовий бік пластини (layout blower)", "TBD", "—", "—", "E3"),
    ("F29", "дочірні плати ENC ×2 → бобишки передньої половини", "гвинт M2.5 A2 TX8 (довжина TBD, AI-M25-CTRL-ENC)", "4", "2",
     "вставка TC-M2,5x4 (boards.json ENC: 2 отвори ⌀2.7 на плату)", "TBD — купон (§2)", "CNCK-M25", "—", "E5"),
    ("F30", "пластина → бобишки передньої половини", "гвинт M3 ISO 14580 A2 TX10 (довжина TBD, AI-M3-PLATE)", "4", "2",
     "вставка TC-M3x5.7 у бобишках PM1–PM4 (M-07, отвір пластини ⌀3.4)", "TBD — купон (§2)", "CNCK-M3", "—", "E6"),
    ("F31", "Al-кутники → пластина", "гвинт M3×4 ISO 14580 A2 TX10 з тильного боку (AI-M3X4-ISO14580): кутник 2 + пластина 2", "8", "2",
     "гайка врівень PEM F-M3-1 (M-07 AT1–AT5, AR1–AR3)", "TBD — купон (§2)", "PEM-F", "—", "E4"),
    ("F32", "бобишка UFS → пластина", "гвинт M2.5 з потайною голівкою ISO 10642 з лицьового боку (AI-M25-UFS)", "2", "2",
     "бобишка UFS Al з різьбою M2.5 (M-07 UB1–UB2)", "TBD — купон (§2)", "—", "—", "E3"),
    ("F33", "тримач T7 → задня стінка", "гвинт M3×14 ISO 14580 A2 TX10 ззовні (AI-M3X14-ISO14580)", "3", "2",
     "вставка TC-M3x5.7 у майданчиках задньої стінки (mechanical.json t7_holder)", "TBD — купон (§2)", "CNCK-M3", "—", "E8"),
    ("F34", "кнопка EDL SW501 (E-Switch PV6F240SS) на платі лючка", "гайка M16×1.0 (комплект)", "1", "—",
     "виріз ⌀16.00 +0.20 у платі лючка 1.6 мм як панелі (панель 1–10 мм)", "0.6 N·m (рекомендований момент кріплення)", "PV6", "—", "E8"),
    ("F35", "носій паку IMU (imu_carrier) → дно Hammond 1550Z101", "гвинт M3 (довжина TBD, AI-M3-IMU-CARRIER)", "2", "2",
     "вставка TC-M3x5.7 (mechanical/params/imu_pack.json carrier.screws; на тих самих гвинтах — носійна плата IMU_CARRIER)", "TBD — купон (§2)",
     "CNCK-M3", "—", "E9"),
    ("F36", "пара BNO085 + RP2040-Zero → носій паку IMU", "стійки 13 мм (тип, кількість і MPN TBD, AI-STANDOFF-IMU-13)", "TBD (за отворами плат)", "2",
     "носій паку IMU (imu_pack.json boards.standoff_h 13.0: під платами — вставка 1/4-20 × 12.7)", "TBD", "—", "—", "E9"),
    ("F37", "штативна вставка носія паку IMU", "латунна вставка 1/4-20 × 12.7 (AI-INSERT-1420; 10-bom рядок 86)", "1", "1",
     "носій паку IMU, друк ≥4 периметри навколо вставки (build/21 §1); вставка CNC Kitchen (10-bom рядок 86), процедура — 17 §3",
     "TBD — купон (§2)", "—", "—", "E9"),
    ("F38", "плата лючка HATCH → дві бобишки задньої стінки обабіч лючка (вушка плати, x 112 і 142, y 85; W2 PCB-SB1)",
     "гвинт M2.5 A2 TX8 з боку роз'ємів плати (зсередини корпусу), до закриття половин (AI-HATCH-BOARD-FIX); довжина TBD: бобишок плати лючка "
     "в моделі механіки ще немає, стосу HATCH-BOARD у generated/fastener-stacks.json немає (плата 1.6 і вставка ті самі, що в ENC: там вікно "
     "5.35–5.6 мм без довжини ISO 14580, R-FASTENER-STACKS OPEN)", "2", "2",
     "вставка CNC Kitchen TC-M2,5x4 у кожній бобишці (L 4.0, ⌀D1 4.6, стінка ≥1.6 — бобишка ⌀7.8; лістинг 3djake, прочитано 07.11.2026); "
     "отвори плати ⌀2.7 (pcb/boards/HATCH.json, build/kicad/boards/HATCH/contract-proposal.json — пропозиція, бобишки додає механіка)",
     "TBD — купон (§2)", "CNCK-M25", "—", "E8"),
    ("F39", "носійна плата F101 PACK_FUSE (10.7 × 26.4) → дві стійки на розширенні пластини біля правого кінця лотка паку (M-07 PF1–PF2: (169.0, 14.1) і (169.0, 35.3); W2 MECH-5, W2 PCB-SB2)",
     "гвинт M2.5×6 ISO 14580 A2-70 TX8 з боку тримача (AI-PACK-FUSE-FIX; dk 4.5, k 1.85 — сторінка 3djake CNC Kitchen, прочитано 11.11.2026): плата 1.6 + 4.4 у різьбі стійки, "
     "вікно 4.1–9.6 мм (generated/fastener-stacks.json PACK-FUSE), вістря 1.6 над лицьовою гранню пластини; ізоляція: на обох шарах плати немає міді ближче 2.5 мм до осі гвинта "
     "(голівка ⌀4.5 і бочка стійки ⌀4.20 — під потенціалом пластини, заливки — плюс паку), виводи тримача й J116/J117 знизу заклеєно поліімідною стрічкою (AI-POLYIMIDE-TAPE)",
     "2", "2",
     "стійка PEM SO-M2.5-6ZI 6 мм, голівка врівень з тильною гранню пластини (AI-PEM-SO-M25-6ZI); отвори плати ⌀2.7 за 2.6 від торців "
     "(pcb/boards/PACK_FUSE.json, build/kicad/boards/PACK_FUSE/contract-proposal.json — пропозиція, у контракті механіки плати ще немає)",
     "TBD — купон (§2)", "—", "—", "E8"),
    ("F40", "кришка зовнішнього S-band вузла Hammond 1554U2GY", "гвинти кришки Hammond (комплектність не перевірено; DigiKey DE: «Cover Included»)",
     "4 (крок 187 × 107)", "2", "корпус Hammond 1554U2GY", "0.30–0.40 N·m (30–40 cN·m, креслення Hammond)", "HAMMOND-1554U2GY",
     "ущільнення кришки — штатне Hammond", "E9b"),
    ("F41", "сталева панель Hammond 1554UPL → корпус pod", "гвинт M3 (тип і довжина TBD, AI-M3-POD-PANEL)", "4 (крок 176 × 45 — звірити з кресленням)", "2",
     "вставки M3 корпусу Hammond (mechanical/params/parts.json hammond_1554u2gy panel_inserts_m3)", "TBD — купон (§2)", "—", "—", "E9b"),
    ("F42", "cf2235-kt30 на панелі, LaNA WB другим шаром 5 мм над фільтром", "стійки й гвинти TBD (AI-POD-STANDOFFS): отвори кріплення модулів — за "
     "їхніми кресленнями (P-01: TBD)", "TBD", "2", "панель 1554UPL (P-01)", "TBD", "—", "—", "E9b"),
    ("F43", "SMA-прохідники RF_IN/RF_OUT і гермоввід W425 pod", "гайка прохідника + кільце (тип TBD, AI-SMA-BULK-POD ×2, MECH-07); гермоввід кабелю "
     "живлення USB-C (тип TBD, AI-GLAND-POD)", "3", "1", "торці pod: RF_IN ⌀6.4, RF_OUT ⌀6.4, PWR ⌀12.2 (P-02); кільця — з боку корпусу",
     "TBD — за даташитом обраних деталей", "—", "стопорна шайба прохідника", "E9b"),
    ("F44", "клапан LTW VENT-PS1YBK-O8002 pod", "гайка M12×1.5 (комплект)", "1", "—",
     "наскрізний отвір ⌀12.2 у бічній стінці pod (P-02 VENT; стінка — звірити з 2.0–3.5 мм), ніколи догори", "0.59–0.78 N·m (6.0–8.0 kgf·cm)",
     "LTW-VENT", "MOLYKOTE 4 — ніколи на силіконові кільця клапанів (STACK)", "E9b"),
    ("F45", "PWR-A → PWR-B: стійки мезоніна", "стійка M3 «тато-мама», тіло 5.0 мм = висота стику B2B Samtec LSHM-150-02.5 × 2 (pcb/partition-spec.json b2b), "
     "шпилька 3.594–4.064 мм (F06; PWR-A 1.664 мм, W2 MECH-8); MPN не обрано — SRC-2 (C-14)", "7", "2",
     "співвісні отвори ⌀3.2 PWR-A і PWR-B (boards.json PWR / PWR_B holes); шпилька — у гайку PEM F-M3-1 пластини", "TBD — купон (§2)", "—", "—", "E2"),
    ("F46", "PWR-B → стійки F45", "гвинт M3 ISO 14580 A2 TX10 з боку компонентів PWR-B, довжина під голівкою 4.66–6.16 мм (PWR-B 1.664 мм, W2 MECH-8) "
     "(generated/fastener-stacks.json PWR_B-STANDOFF); артикул — SRC-2 (C-13)", "7", "2",
     "внутрішня різьба стійки F45 (глибина різьби деталі не прочитана — вікно до довжини тіла 5.0)", "TBD — купон (§2)", "—", "—", "E2"),
    ("F47", "VEML7700 4162 U308 → верхня стінка", "двосторонній акриловий скотч 3M VHB 4910 1.0 мм (AI-VHB-4910-MODULES): 4 диски ⌀6 з отвором ⌀2.5 на друкованих "
     "упорах ⌀6 у кишені верхньої стінки; гвинта немає — у стінці 2.5 мм з кишенею 1.1 немає глибини для вставки з загвинчуванням ≥1.5 d "
     "(generated/fastener-stacks.json VEML7700, W2 MECH-5)", "4 диски", "2",
     "упори VR1–VR4 (грань y 160.1; M-02 «Упори VEML7700»; mechanical.json module_mounts) під 4 отворами ⌀2.5 файла плати Adafruit "
     "(github.com/adafruit/Adafruit-VEML7700-PCB, ab489f0, прочитано 07.11.2026); 2 шипи ⌀2.2 упорів у діагональних отворах ставлять датчик під вікно ⌀4",
     "—", "—", "провід S26 (STEMMA QT) закріпити біля плати (скотч не несе натягу проводу)", "E5"),
]
INSERTS = [
    ("TC-M3x5.7", "M3", "4.0", "≥1.6", "CNCK-M3"),
    ("TC-M2,5x4", "M2.5", "4.0 (так у лістингу)", "≥1.6", "CNCK-M25"),
]

# --- Power states and test points (build/19) -----------------------------------
STATES = [
    ("B0", "Гола плата без живлення (до і після оплавлення)", "опір до GND, DMM"),
    ("S0", "OFF: стенд 14.8 V через стендовий провід у вхідний роз'єм S05 (J105) на PWR-A (пак від'єднано), S1 вимкнено", "за 08 крок 16 п. 1–2; 19 §4"),
    ("S1", "SW увімкнено, Q6A не під'єднана (J21 без навантаження)", "SYS12/LAB5 без зовнішніх навантажень"),
    ("S2", "Q6A увімкнена: є 3V3_Q6A, усі EN низькі", "до старту labd"),
    ("S3", "DISP12 увімкнено (GP16 = 1)", "дисплей під'єднано"),
    ("S4", "Один EN = 1 (вказаний у рядку), решта 0", "по одному каналу, на навантаженні"),
]
# net -> {state: text}, plus (en net that enables it in S4, source)
TP_EXPECT = {
    "E1_N": ({"S0": "= стенд 14.8 V мінус падіння шунта R101 15 mΩ і S05/S06", "S1": "≈ стенд (−69 mV на шунті при 4.6 A)", "S2": "≈ стенд",
              "S3": "≈ стенд", "S4": "≈ стенд"}, None, "02 §2, 08 крок 16; E1 R101 (69 mV при 4.6 A)"),
    "E1_SW": ({"S0": "≈0 V (S1 вимкнено; витік ≤0.2 мкА)", "S1": "V_N − ≤40 mV при 4.6 A", "S2": "як S1", "S3": "як S1", "S4": "як S1"}, None, "02 §2 (#2813)"),
    "AON3V3": ({"S0": "3.3 V ±1 % (3.267–3.333 V)", "S1": "3.3 V ±1 %", "S2": "3.3 V ±1 %", "S3": "3.3 V ±1 %", "S4": "3.3 V ±1 %"}, None, "STACK D3 (TPS70933 ±1 %)"),
    "GND": ({"S0": "0 V (опорна)", "S1": "0 V", "S2": "0 V", "S3": "0 V", "S4": "0 V"}, None, "—"),
    "E1_UV_OFF": ({"S0": "низький при V_N 14.8 V (високий = низька батарея)", "S1": "низький", "S2": "низький", "S3": "низький", "S4": "низький"}, None,
                  "E1.json U104; поріг 12.8 ±0.1 / 13.6 ±0.1 V (08 крок 4)"),
    "E1_PG_SYS12": ({"S0": "—", "S1": "open-drain без підтяжки: лише сервісно з 10k до 3.3 V", "S2": "сервісно", "S3": "сервісно", "S4": "сервісно"}, None, "E1.json TP101"),
    "E1_PG_LAB5": ({"S0": "—", "S1": "open-drain без підтяжки: лише сервісно", "S2": "сервісно", "S3": "сервісно", "S4": "сервісно"}, None, "E1.json TP102"),
    "E1_PD_FLT": ({"S0": "open-drain без підтяжки; сервісно", "S1": "сервісно", "S2": "сервісно", "S3": "сервісно", "S4": "сервісно"}, None, "E1.json TP103"),
    "J21": ({"S0": "0 V", "S1": "11.5–12.5 V (без навантаження)", "S2": "11.5–12.5 V", "S3": "11.5–12.5 V", "S4": "11.5–12.5 V"}, None, "02 §2; 08 крок 16"),
    "DISP12": ({"S0": "0 V", "S1": "0 V (GP16 = 0, 100k)", "S2": "0 V", "S3": "≈ SYS12 (12.0 V ±4 %)", "S4": "як у S2/S3"}, None, "E2.json U202; 02 §2"),
    "LIME3V3": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (EN_LIME3V3 = 0, 100k)", "S3": "0 V", "S4": "≈ VCC_3V3_MKEY при EN_LIME3V3 = 1"}, "EN_LIME3V3", "E2.json U203; 02 §2"),
    "AUX12": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (EN_AUX12 = 0)", "S3": "0 V", "S4": "≈ SYS12 при EN_AUX12 = 1 (лише BENCH)"}, "EN_AUX12", "02 §2"),
    "LNA4V5": ({"S0": "0 V", "S1": "4.30 V (4.208–4.392 V)", "S2": "4.30 V", "S3": "4.30 V", "S4": "4.30 V; запас V(E2_LNA_IN)−V(OUTS) ≥0.40 V"}, None, "08 крок 4 (v2.1, R227 21.5k)"),
    "BIAS_CH1": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (EN_LNA1 = 0)", "S3": "0 V", "S4": "≈ LNA4V5 мінус падіння ключа при EN_LNA1 = 1"}, "EN_LNA1", "02 §2; Ж-06/Ж-07"),
    "BIAS_CH2": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (EN_LNA2 = 0)", "S3": "0 V", "S4": "≈ LNA4V5 при EN_LNA2 = 1"}, "EN_LNA2", "02 §2"),
    "BIAS_CH2_PORT": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (блокувальний елемент закритий)", "S3": "0 V", "S4": "≈ BIAS_CH2 при EN_LNA2 = 1"}, "EN_LNA2", "E2 R-E2-21; DC-30"),
    "BIAS_CH3": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (EN_LNA3 = 0)", "S3": "0 V", "S4": "≈ LNA4V5 при EN_LNA3 = 1"}, "EN_LNA3", "02 §2"),
    "BIAS_CH3_PORT": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (блокувальний елемент закритий)", "S3": "0 V", "S4": "≈ BIAS_CH3 при EN_LNA3 = 1"}, "EN_LNA3", "E2 R-E2-21; DC-30"),
    "BIAS_CH4": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (EN_LNA4 = 0)", "S3": "0 V", "S4": "≈ LNA4V5 при EN_LNA4 = 1"}, "EN_LNA4", "02 §2"),
    "VBUS_RTLB": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (EN_RTLB = 0)", "S3": "0 V", "S4": "≈ LAB5 (5.0 V ±4 %) при EN_RTLB = 1"}, "EN_RTLB", "02 §2"),
    "LNB13V2": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (EN_LNB = 0)", "S3": "0 V", "S4": "13.2 V (смуга ІС 12.87–13.53 V; на F 11.5–14 V) при EN_LNB = 1"}, "EN_LNB", "02 §2; Ж-09"),
    "BONI13V8": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (EN_BONI = 0)", "S3": "0 V", "S4": "13.8 V (смуга ІС 13.455–14.145 V при IN ≥14.8 V) при EN_BONI = 1"}, "EN_BONI", "08 крок 4; Ж-10"),
    "BONI13V8_PORT": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (блокувальний елемент закритий)", "S3": "0 V", "S4": "≈ BONI13V8 при EN_BONI = 1"}, "EN_BONI", "E2 R-E2-21; DC-30"),
    "E2_FAULT_J21": ({"S0": "—", "S1": "open-drain FLT U201: без несправності — високий лише за наявної підтяжки", "S2": "без несправності — не активний", "S3": "як S2", "S4": "як S2"}, None, "E2.json U201"),
    "E2_FAULT_DISP": ({"S0": "—", "S1": "open-drain FLT U202", "S2": "без несправності — не активний", "S3": "як S2", "S4": "як S2"}, None, "E2.json U202"),
    "OVP_LNB_N": ({"S0": "низький (100k на GND)", "S1": "низький (EN_LNB = 0)", "S2": "низький", "S3": "низький", "S4": "високий при EN_LNB = 1 і без OVP (поріг 13.760 V ном.)"}, "EN_LNB", "E2.json U212/U220"),
    "BIAS_SB_LNA": ({"S0": "0 V", "S1": "0 V", "S2": "0 V (EN_SB_LNA = 0)", "S3": "0 V", "S4": "≈ LAB5 при EN_SB_LNA = 1 (≤5.5 V для LaNA)"}, "EN_SB_LNA", "E2.json U221"),
    "E5_FAULT_T7": ({"S0": "—", "S1": "0 V (підтяжка до 3V3_Q6A)", "S2": "≈3.3 V без несправності", "S3": "як S2", "S4": "як S2; EN_T7 = 1 — T7 живиться"}, "EN_T7", "E5 §7"),
    "E5_HDMI_ST_N": ({"S0": "—", "S1": "—", "S2": "до 5 V: не підключати до GPIO 3.3 V", "S3": "як S2", "S4": "як S2"}, None, "E5 §8"),
    "E3_GNSS_FAULT": ({"S0": "—", "S1": "open-drain FAULT_N U315 без підтяжки: лише сервісно з 10k до 3.3 V; U315 вимкнено (EN = 3V3_Q6A = 0)",
                       "S2": "без несправності — не активний (U315 увімкнено разом з 3V3_Q6A)", "S3": "як S2", "S4": "як S2"}, None,
                      "E3.json U315 (R-E3-15); TI SLVS841G §8.3.3"),
    "E5_IMU_FAULT": ({"S0": "—", "S1": "open-drain FAULT_N U553 без підтяжки: лише сервісно; без несправності не активний (EN = LAB5)",
                      "S2": "як S1", "S3": "як S1", "S4": "як S1"}, None, "E5.json U553 (R-E5-08); TI SLVS841G §8.3.3"),
}

# Staged bench-supply limits for the first power-up of the assembled power chain.
STAGES = [
    ("L0", "S0: лише домен N (AON, INA228, UV); стенд через роз'єм S05 (J105) на PWR-A; спершу PWR-A сама, потім PWR-A + PWR-B (19 §4 п. 1)",
     "0.02", "≤1.0 mA з INA228 у роботі / ≤0.25 mA у shutdown при 14.8 V; PWR-B домену N не навантажує (AON3V3 і E1_N стик B2B не перетинають, "
     "pcb/generated/b2b-nets.json)", "02 §4; 08 крок 16"),
    ("L1", "S1: SW увімкнено, Q6A і модулі LAB5 не під'єднані; PWR-A сама, потім PWR-A + PWR-B", "0.30",
     "записати окремо для PWR-A і для PWR-A + PWR-B (струм холостого ходу перетворювачів)", "уставка asm, обмежує енергію КЗ"),
    ("L2", "S2: Q6A (без Lime, без SDR)", "1.50", "J21 0.35–1.3 A при 12 V (модель)", "02 §2"),
    ("L3", "S3: + дисплей", "3.00", "DISP12 0.25 / 1.1 A (модель)", "02 §2"),
    ("L4", "Повна збірка з Lime (режими H/I)", "5.00", "до 4.6 A на піку (модель)", "02 §2–3; нижче F101 7.5 A"),
]
SHORT_LIMIT_OHM = 10  # bare-board criterion (рішення asm): below this a rail is treated as shorted

# --- Superseded v2 tokens that must not appear in build/02, 04, 08 outside a historic clause
STALE = [
    (r"D36V28F5", "LAB5 — D36V50F5 #4091 (v2.1)"),
    (r"F3 3 A|запобіжник 3 A LAB5|3 A \(0297003", "запобіжник LAB5 — 4 A (v2.1)"),
    (r"запобіжнику 3 A|на 3 A \(77", "запобіжник LAB5 — F102 4 A, тривало ≤3.2 A (v2.1, E1-05)"),
    (r"повітродувка 5 V 5015|5015 \(", "повітродувка — Delta BFB0305HA-C (E3-03)"),
    (r"GP17 \| димінг|STACK\.md 5\.2 GP17", "GP17 — reset MCP (E3-review)"),
    (r"ворота 2\.5 A", "LAB5 — тривало ≤3.2 A (E1-05); 2.5 A — лише legacy D36V28F5"),
]
# v2.1 readings of build/09 rows for the bench form (09 keeps its numbering; §21 points here):
# id -> ("replace", procedure, threshold) | ("sub", old, new) | ("note", text appended to the procedure).
FORM_V21 = {
    "Ж-05": ("replace",
             "v2.1 (E1 U108, E1-05): D36V50F5 #4091 (LAB5): шовкографія; вихід без навантаження і при 3.2 A від 16.4 V; кроки 0.3–3.2 A "
             "(A/B C4, А-02); 3.2 A через F102 4 A 30 хв при 50 °C; перехідно до 4 A з логом запобіжника і пульсацій",
             "5.0 V ±4 %; без нових ліній за A/B C4 (частоти D36V28F5 з рядка 09 не переносяться); тривало ≤3.2 A, перехідно 4 A (E1-05); "
             "60-хв ворота 4.2 A для LAB5 не діють; перевищення бюджету → E1-05 (обмеження одночасності або переробка шини, повтор тестів)"),
    "А-02 (C4 (1))": ("sub", "D36V28F5", "D36V50F5 #4091 (LAB5, v2.1: E1 U108)"),
    "А-03 (HF-6)": ("sub", "D36V28F5", "D36V50F5 #4091 (LAB5, v2.1: E1 U108)"),
    "Д-02": ("note", "v2.1: D36V28F5 тут — окремий перетворювач 5 V лише для варіанта плати дисплея тільки на 5 V, не LAB5 "
                     "(LAB5 — D36V50F5 #4091, E1 U108)"),
}
FORM_V21_MARK = "v2.1"
HISTORIC_MARK = "історичн"

# --- Assembly order (build/21) --------------------------------------------------
# Each step: id, title, actions (list), refs (segments, fasteners, labels)
STEPS = [
    # id, title, parts, actions, checks, refs (segments S.., fasteners F.., labels L.., assemblies C-..)
    ("E0", "Підготовка і друк",
     "друковані деталі ASA (§1), термовставки TC-M3x5.7 / TC-M2,5x4, купон з тієї самої котушки",
     ["Робоче місце, ESD і безпека — за 08 крок 0; літієвий пак не під'єднано, F101 вийнято з тримача на носійній платі PACK_FUSE і лежить окремо.",
      "Надрукувати деталі за таблицею §1; дати охолонути до кімнатної температури.",
      "Купон: одна бобишка з кожним типом вставки; задати робочий момент за 17 §2 і записати в бланк 20.",
      "Вставки в корпус — за 17 §3, по одній, торець урівень із бобишкою."],
     ["вставки не провертаються робочим моментом купона", "торець вставки урівень, без напливів пластику в різьбі"],
     []),
    ("E1", "Плати на столі",
     "плати PWR-A, PWR-B, RF, CTRL, ENC ×2 (+1 запасна), плата лючка HATCH після оплавлення (PWR-A, PWR-B і RF — деталі лише зверху, "
     "CTRL — з обох боків; build/15 «Монтаж»)",
     ["Замовлення (до цього кроку): кожну плату — за її набором `build/kicad/boards/<B>/fab/` (NOT RELEASED: вихід CI/моделі, build/13 §6). "
      "Перед оплатою кожну деталь CPL (`assembly/<B>-cpl-jlc.csv`) перевірити в переглядачі JLC — поворот, центр і бік: таблиця поправок "
      "`assembly/<B>-cpl-rotation-offsets.csv` порожня (TBD), бо CI їх не перевіряє; прийняти DFM JLC, перечитати склад LCSC на дату замовлення "
      "і замовляти з контролем імпедансу лише там, де цього вимагає `<B>-fab-notes.pdf`.",
      "Перевірка B0: опір кожної шини до GND за 19 §2 до і після оплавлення.",
      "Плати окремо не живити: PWR-A вмикається лише на пластині — спершу сама, потім разом з PWR-B (E2, 19 §4 п. 1); RF — лише через S04 "
      "від PWR-B і S03 від CTRL (E4); CTRL — від 3V3_Q6A через S01 (E6); порядок — 19 §4.",
      "Обжати джгути S02, S03, S04 за 16 §1 (інструмент Molex 0638190000 для Micro-Fit); маркер з ID проводу на обох кінцях (L-WIRE)."],
     ["кожна деталь CPL перевірена в переглядачі JLC до оплати", "жодна шина < 10 Ω до GND",
      "прозвонка кожного проводу джгута від маркера до маркера"],
     ["S02", "S02B", "S03", "S04", "L-WIRE", "L-CONN"]),
    ("E2", "Збірка середньої пластини (на столі, поза корпусом)",
     "пластина 2 мм EN AW-5754 за шаблоном M-07 (08 крок 5), гайки PEM F-M3-1 ×15, стійки PEM SO-M3-3ZI ×6 і SO-M2.5-6ZI ×2, D36V50F12, D36V50F5, #2813, INA228 5832, "
     "IP2368, PWR-A, PWR-B (стик B2B — дві однакові Samtec LSHM-150: J208 на PWR-A, J209 на PWR-B), стендовий провід (розетка Mini-Fit Jr. 5557 під вхідний "
     "роз'єм S05, 18 AWG, запобіжник 7.5 A у розриві)",
     ["Самоклінчувальні деталі — пресом, до будь-якого монтажу: F-M3-1 у PWR1–7, AT1–5, AR1–3; SO-M3-3ZI у RF1–6 голівкою врівень з лицьовою гранню; SO-M2.5-6ZI у PF1–PF2 (носій PACK_FUSE) голівкою врівень з тильною гранню "
      "(PEM: «install with a squeeze in properly sized round holes»; прес — AI-PEM-PRESS); кромки прорізів SL1–SL3 — кант (AI-EDGE-TRIM).",
      "D36V50F12 U107 і D36V50F5 U108 — впаяти в ліву ніжку PWR-A обома парами силових пінів (E1 U108) на проставці гребінки (деталі низу модуля "
      "1.8 мм) до встановлення PWR-A.",
      "PWR-A — на пластину з термопрокладками 0.5 мм і шайбами 0.4 мм шпильками стійок F45 (F06): перед тим поліімідний ізолятор — над зазором "
      "0.4 мм і на дні кишень PB* під деталями нижнього боку PWR-A (M-07, W2 MECH-7), а під кожною площадкою THT PWR-A поза PB* (радіальні конденсатори, тримач Keystone 3568 F102, роз'єми крайових смуг; "
      "перелік — pwr_a_tht_pocket_items у pcb/partition-budget.json) у пластині має бути кишеня ≥1.0 мм (M-07; build/15 «Кишені пластини під PWR-A (W2 MECH-7)»); виводи THT "
      "не повинні проткнути ізолятор.",
      "Перевірка кишень і ізоляції — до будь-якого живлення і до PWR-B (кишені вже закриває сама PWR-A, а після PWR-B поля виводів THT і TP "
      "PWR-A поза вікнами щупа PWR-B стають недосяжні): прозвонка від голої точки пластини до кожної TP PWR-A (19 §3, стовпець «плата») — "
      "розрив; зв'язок GND/CHASSIS — лише BOND-RF (E10, build/15 «План шарів»).",
      "INA228 5832 і Pololu #2813 U106 на пластину не ставити: для стендового запуску під'єднати їх джгутами S06 і S07 до роз'ємів PWR-A і "
      "покласти ізольовано на стіл (поліімід, подалі від пластини), вбудована кнопка #2813 — доступна (19 §4 п. 1). Їхнє місце в корпусі — "
      "задній шар під екраном HF+ біля батарейного лотка (INA228 x 28.5–54.3, y 44.5–64.8, z 6–16.1; #2813 x 93.3–113.6, y 39–64.4, z 5.5–15.6; між ними хаб "
      "CH334F — build/15 «INA228 5832 і Pololu #2813 (W2 MECH-3)» і «Модулі заднього шару (W2 MECH-5)»); вони стають на бобишки й майданчик задньої "
      "стінки в кроці E8 (F09, F05; хаб — F10). IP2368 — на лицьовий бік пластини вгорі праворуч "
      "(F11), джгут S10; термовимикач TH102 — кронштейном до найгарячішого MOSFET IP2368 через поліімід (08 крок 3; деталь і кріплення — "
      "build/15 «IP2368»); джгути S12, S13 — до роз'ємів PWR-A; кінець S12 (XT30) ізолювати; S05 паку ще не під'єднувати.",
      "Стендовий провід — у вхідний роз'єм S05 (J105) на PWR-A; TP104 — лише щуп, не живлення: PWR-A сама — ступінь L0, потім S1 (L1) "
      "вбудованою кнопкою модуля #2813 U106 (19 §4 п. 1 (а), 19 §5); кнопка SW301 стоїть на CTRL, і її коло PWR_BUTTON доходить до PWR-A лише "
      "через S02 і стик B2B — до E6 вона не під'єднана.",
      "PWR-B: знеструмити (кнопкою #2813 — S0, стендовий провід від'єднати); J209 PWR-B — на J208 PWR-A: контакт 1 J209 сідає на контакт 2 "
      "J208 (Samtec LSHM Rev Z, прим. 4; pcb/generated/b2b-nets.json), рівно, без перекосу; PWR-B — на стійки F45 гвинтами F46 (build/17); під полями виводів THT PWR-B і під стиком на PWR-A "
      "деталей немає (build/15 «Розмір»).",
      "Стендовий провід — знову в J105: PWR-A + PWR-B — ступінь L0, потім S1 (L1) тією самою кнопкою #2813 (19 §4 п. 1 (б))."],
     ["прозвонка гола точка пластини → кожна TP PWR-A — розрив (до першого ввімкнення)",
      "TP104/TP105/TP106/TP108 за станами S0–S1 (19 §3): спершу PWR-A сама, потім з PWR-B; TP PWR-B у S1 — за 19 §3",
      "струм L0 ≤1.0 mA при 14.8 V в обох ступенях; струм L1 записано окремо для PWR-A і для PWR-A + PWR-B",
      "гайки PEM F-M3-1 урівень з боку голівки (у пластині 2.0 мм хвостовик ≤1.53 мм не доходить до другої грані — так і має бути, PEM-F), стійки SO-M3-3ZI урівень з лицьовою гранню, SO-M2.5-6ZI — з тильною"],
     ["F06", "F11", "F45", "F46", "S06", "S07", "S10", "S12", "S13"]),
    ("E3", "Q6A, Lime, охолодження і кабель хаба на пластині",
     "Q6A (прогнаний за 08 крок 1), охолоджувач A або B, Noctua NF-A4x10, повітродувка Delta, кабель C-HUB, бобишка UFS, R44SF + Lime на п'єдесталі",
     ["Бобишка UFS — на тильний бік пластини потайними M2.5 (F32); Q6A — на стійки M2.5 6 мм (F01/F02); охолоджувач — за 08 крок 6 (F03 для Armor).",
      "П'єдестал Lime (F04) з прокладкою; riser крізь вікно; кабель C-PCIE; LIME3V3 S18 — лише після прозвонки ізоляції 3.3 V картки (E5 §10).",
      "Відвід VCC_3V3_MKEY S17 — лише після локалізації точки на Q6A (16 §11); до того LIME3V3 не живити.",
      "Кабель C-HUB — вилкою в J2 Q6A (хаб CH334F стоїть на задній стінці, F10, крок E8); Noctua (F27) з кабелем S27; повітродувка Delta на лицьовий бік пластини (F28).",
      "J21: до прогону — заводський кабель; після прогону — S16 пайкою до майданчиків J21 (08 крок 7.7)."],
     ["S2 за 19 §3 з Q6A на J21 (ступінь L2, 19 §4 п. 2)", "lsusb бачить хаб; Noctua обертається; тахо на GP22"],
     ["F01", "F02", "F03", "F04", "F27", "F28", "F32", "S17", "S18", "S27", "S16", "C-PCIE", "C-HUB"]),
    ("E4", "РЧ-відсік і кутники на пластині",
     "RF-плата, Al-кутники, модулі РЧ-тракту (Flamingo+, SAWbird+, атенюатор LNB), RTL-A/B на подовжувачах, HF+ в екрані Schubert 6B, bias-tee Boni, G6K",
     ["Al-кутники (верхній і правий) — на тильний бік пластини гвинтами M3×4 у гайки PEM (F31).",
      "RF-плата на стійки SO-M3-3 (F07); бондинг RF GND — окрема точка BOND-RF (F26, E10).",
      "Модулі РЧ-тракту і коаксіальні з'єднання — за 16 §8; ключ 0.9 N·m лише для нержавіючих SMA (F15).",
      "RTL-A/B: кабелі C-RTLA/C-RTLB і VBUS S20/S21; HF+: C-HFP і S22 з двома феритами на повному кабелі; Boni: S35.",
      "Джгути S03/S04 з E1 — під'єднати крізь проріз SL2 і виріз N4; укласти вздовж пластини, подалі від буферних дроселів."],
     ["HMC7992 у RF1 при ввімкненні (08 крок 9)", "котушки G6K знеструмлені", "розрив центр–корпус на кожному SMA з вимкненим зміщенням"],
     ["F07", "F15", "F31", "S03", "S04", "S20", "S21", "S22", "S35", "C-RTLA", "C-RTLB", "C-HFP", "L-LABRXA", "L-LABRXB",
      "L-LIME-X2", "L-LIME-X4", "L-LIME-J4", "L-LIME-X1"]),
    ("E5", "Передня половина: дисплей і HMI",
     "передня половина корпусу, Wisecoco + рамка, CTRL, дві плати ENC з енкодерами PEC11R-4220F, кнопка PV6F240SS, VEML7700",
     ["Дисплей у рамку (параметрична модель; клей/фіксація — TBD за пакетом механіки), козирок і L-SUN.",
      "CTRL на бобишки (F08); плати ENC на бобишки (F29), джгути S37/S38 до CTRL; вали енкодерів вкоротити до встановлення (08 крок 12); "
      "гайки енкодерів ≤1.0 N·m (F20); SW301 PV6F240SS у верхню стінку — 0.6 N·m (F21).",
      "VEML7700 — скотчем на упори кишені верхньої стінки за вікном (F47, S26); провід повітродувки S28 — заготовити до CTRL.",
      "NTC панелі TH301 — на задній тепловідвід панелі біля гарячої точки, ізольовано; виводи розвантажити, паяти ≥6 мм від бусинки (S39, примітка E3).",
      "Шлейф S01 без 5 V (N-E3-01, R-E3-15) — до заготовлення кабелів CTRL (наступний пункт): у місці кожної з двох розеток IDC до обтиснення вирізати "
      "провідники 2 і 4 стрічки (ділянку ≈5 мм під лезами контактів 2 і 4), щоб жоден кінець цих провідників не торкався контакту; на CTRL контакти 2/4 "
      "бокса — без кола. Без цього кроку 5 V Q6A J20 знову опиняється в стрічці 28 AWG без межі струму; LC76G живиться від U315 на CTRL (S25).",
      "Кабелі CTRL: S01 (≤200 мм), S24, S25 (живлення і RESET LC76G), S29, S30, S15 — заготовити з запасом петлі; гілка PPS: провідники 6, 7, "
      "16 і 18 стрічки S01 відокремити одразу за розеткою J20 (до обтиснення розетки CTRL вирізати їх там, як 2 і 4) і довести до P1 LC76G (≤200 мм, "
      "модель 196 мм; N-E3-03)."],
     ["вали енкодерів вкорочені, ручки не торкаються гайок", "кнопки й енкодери перевіряються в E6 (19 §4 п. 3) — CTRL живиться від Q6A",
      "S01: прозвонка контактів 2 і 4 розетки Q6A → контакти 2 і 4 розетки CTRL — розрив, сусідні 1, 3, 5 — є з'єднання (до підключення до Q6A)",
      "гілка PPS: J20.7 → P1.5, J20.16 → P1.4, J20.18 → P1.3, J20.6 → P1.2 LC76G — є з'єднання; ті самі провідники до розетки CTRL (контакти 6, 7, 16, 18) — розрив"],
     ["F08", "F20", "F21", "F29", "F47", "S01", "PPS", "S15", "S24", "S25", "S26", "S28", "S29", "S30", "S37", "S38", "S39", "L-SUN", "L-RX"]),
    ("E6", "Пластина в передню половину",
     "збірка середньої пластини (E2–E4), передня половина (E5)",
     ["Встановити пластину на бобишки передньої половини гвинтами M3 у вставки PM1–PM4 (F30); дисплей — до пластини з каналом повітря 4–6 мм.",
      "HDMI C-HDMI (FPC-набір, mechanical.json hdmi_route, W2 MECH-4): стрічку 1 (3560) протягнути крізь ферит 74278011 і затиснути в адаптер 3550 "
      "або 3549 (той, що спрямовує затискач до задньої стінки); адаптер — у HDMI Q6A, стрічка вниз, згин 45° під LAB BUS, ферит, згин 45° угору біля "
      "правої стінки, крізь відкритий виріз пластини (стрічку заводять збоку), на лицьовий бік до затискача A вставки HDMI_INSERT справа від BMS; "
      "стрічку 2 (3560) — від затискача B угору смугою, згин 45° під CTRL, по пластині до 3548 у вході Wisecoco; кожен згин один раз, без повторного "
      "заламування; обидві стрічки, крім фериту, обмотати мідною стрічкою (AI-HDMI-CU-TAPE) і заземлити на голу кромку пластини біля вирізу; "
      "подалі від РЧ-відсіку і фідера GNSS; touch C-TOUCH.",
      "DISP12 S19 з наклейкою L-DISP12; S02 CTRL ↔ PWR; S01 Q6A ↔ CTRL крізь проріз SL1; S24 до вставки T7 у C-T7.",
      "NTC корпусу TH302 — на внутрішню раму подалі від прямого тепла перетворювачів, ізольовано (примітка E3; місце в моделі — TBD); S40 до CTRL, "
      "паяти ≥6 мм від бусинки.",
      "Стяжки до пластини ≤30 мм від кожного роз'єму і далі кожні 50–80 мм (16 §1)."],
     ["S2 і S3 за 19 §3 (ступінь L3)", "EN-тести S4 і кнопки/енкодери за 19 §4 п. 3", "touch енумерується без VBUS (E5 §8)",
      "TH301/TH302: обрив і КЗ датчика вмикають повне охолодження (E3)"],
     ["F30", "S19", "S02", "S02B", "S01", "S40", "C-HDMI", "C-TOUCH", "C-T7", "L-DISP12"]),
    ("E7", "Передня половина: панельні деталі стінок",
     "прохідники SMA/F/BNC верхньої грані (крізь стінку і верхній Al-кутник), RX2/REF IN правої стінки, USB-C, LAB USB-A, LAB BUS GX12 і аудіо нижньої "
     "грані, клапани V1/V2 — усі в стінках передньої половини (роз'єм половин z 14, mechanical.json split_z)",
     ["Прохідники SMA (F14), F (F16), BNC (F17) — крізь верхню стінку і верхній кутник; RX2/REF IN — крізь праву стінку і правий кутник; ≥3 витки для стикування.",
      "USB-C (S11), LAB USB-A (S23 + C-LAB), LAB BUS GX12 (F19, S34) — у нижню грань; дроти крізь проріз SL3 пластини.",
      "Клапани V1/V2 VENT-PS1NBK-O8002 у різьбові гнізда 4 мм (F22a); наклейки панелей."],
     ["розрив центр–корпус на кожному SMA з вимкненим зміщенням", "наклейки за 18"],
     ["F14", "F16", "F17", "F19", "F22a", "S11", "S23", "S34", "C-LAB", "L-USBC", "L-LABUSB", "L-LABBUS", "L-AUDIO"]
     + ["L-" + _ref for _ref in PORT_LABELS]),
    ("E8", "Задня половина: GX16, гермоввід T7, лючок, батарейний відсік",
     "задня половина, GX16-4, гермоввід T7, тримач T7, плата лючка (J502, J503, SW501), гайка 1/4-20, ремінь",
     ["GX16-4 (F18, S32 крізь проріз SL3), тримач T7 ззовні (F33), захоплена гайка 1/4-20 на цоколі (F25); гермоввід T7 — розрізний icotek KVT 20 "
      "(M20×1.5, фланець ⌀40, кабель ≤11 мм, IP54): місце на задній стінці — TBD (у проміжку між лючком і решіткою вентилятора не вміщується; "
      "mechanical.json t7_gland), до того кабель T7 не вводити.",
      "Модулі заднього шару (W2 MECH-5): хаб CH334F 5997 на 4 бобишки (F10), INA228 5832 на 2 бобишки й 2 упори (F09), Pololu #2813 на майданчик зі скотчем "
      "(F05) — M-06 «Бобишки модулів»; джгути S06/S07 і кабелі хаба (C-HUB, H2–H4) — до закриття шва.",
      "Сервісний лючок: плата лючка на бобишки задньої стінки (F38; кріплення TBD до контуру плати, W2-05) з J503 (S14 + S15, далі S16 до J21) і J502 (S30), "
      "SW501 PV6F240SS у платі лючка (F34, S31), синій USB-A Q6A; наклейки L-HATCH, L-J21.",
      "Батарейний відсік: піна 3 мм, відбивна плівка, бар'єр; пак з L-BAT і L-F101; носійна плата F101 (PACK_FUSE) ізольовано й закріплено біля лотка (F39, кріплення TBD); S05 паку поки не "
      "під'єднувати (у вхідному роз'ємі S05 (J105) на PWR-A — стендовий провід), F101 вийнятий."],
     ["оплітка GX16 — корпус ≤0.1 Ω", "розрив між J503 і J502 (різні родини, не стикуються)", "наклейки за 18"],
     ["F05", "F09", "F10", "F18", "F25", "F33", "F34", "F38", "F39", "S32", "S36", "S14", "S30", "S31", "L-HATCH", "L-J21", "L-BAT", "L-T7", "L-IMU", "L-F101"]),
    ("E9", "Пак IMU, зовнішній кабель і коробки Gainta",
     "Hammond 1550Z101, носій паку (imu_carrier, друк) з латунною вставкою 1/4-20 × 12.7, носійна плата IMU_CARRIER (U552, D502, C519, C520, деталі E3 "
     "«External IMU»), RP2040-Zero, BNO085, стійки 13 мм, SKINTOP MS-SC-M12, кабель HELU 49655 2 м; коробки Gainta з клапанами LTW",
     ["Носій паку: латунна вставка 1/4-20 × 12.7 (F37) навпроти отвору ⌀6.6 дна (I-01); пара BNO085 + RP2040-Zero на стійках 13 мм над носієм (F36), "
      "осі BNO085 — за I-01; носій разом із носійною платою IMU_CARRIER — гвинтами M3 у вставки (F35).",
      "Гермоввід (F23) на стінці, найдальшій від BNO085.",
      "Кабель S33: оплітка 360° у SKINTOP і обтиснута в GX16; кришка латунними M4 (F24), шов — провідна стрічка.",
      "Коробки Gainta: клапани VENT-PS1YBK-O8002 з гайкою в наскрізних отворах 2.0–3.5 мм (F22b)."],
     ["оплітка — корпус паку і GX16 ≤0.1 Ω", "1e6 кадрів IMU без CRC-помилок (E5 §10 п. 8)"],
     ["F22b", "F23", "F24", "F35", "F36", "F37", "S33"]),
    ("E9b", "Зовнішній S-band вузол (pod)",
     "Hammond 1554U2GY і сталева панель 1554UPL, sysmocom cf2235-kt30 (A423), Nooelec LaNA WB 100845 (A422), DC-блок Mini-Circuits BLK-89-S+ (A425), "
     "RG316 W422/W423 (куплено 152.4 мм), W424 1 м до RX2, SMA-прохідники RF_IN/RF_OUT, гермоввід і кабель живлення W425 (USB-C ↔ вилка M8 binder "
     "99 3379 100 03), клапан VENT-PS1YBK-O8002",
     ["Свердління за P-02: RF_IN і RF_OUT ⌀6.4 на торцях, PWR ⌀12.2 (гермоввід W425), VENT ⌀12.2 на бічній стінці; розміщення — за P-01 (build/12: шари "
      "з 5 мм між ними).",
      "Панель 1554UPL — у корпус (F41); cf2235-kt30 — на панель, LaNA WB — другим шаром 5 мм над фільтром (F42; отвори кріплення модулів — TBD за їхніми "
      "кресленнями).",
      "РЧ (16 §8): J422 спіралі → W422 → LaNA SMA_IN; LaNA SMA_OUT → W423 → BLK-89-S+ A425 → cf2235-kt30 → W424 → RX2; W422 (від спіралі) і W424 (до RX2) "
      "з'єднуються зі стінкою pod через прохідники RF_IN/RF_OUT (F43; тип і стать TBD, MECH-07); нержавіючі SMA — ключем 0.9 N·m (правило F15).",
      "Живлення LaNA — лише кабель W425 (S41): вилка M8 binder 99 3379 100 03 — у панельну розетку J551 головного корпусу (BIAS_SB_LNA через S36), "
      "кінець USB-C — крізь гермоввід pod (F43) у LaNA; інших способів живлення LaNA не застосовувати (E4 A422). J551 — M8 A-код, корпус іншого розміру, "
      "ніж GX16 J504 і GX12 J505, тож кабель IMU чи LAB BUS у неї не входить (build/15 «Ключування панельних роз'ємів»); грань і виріз J551 — MECH-07.",
      "Клапан (F44) — на бічну стінку, ніколи догори; кришка — гвинтами Hammond 30–40 cN·m (F40)."],
     ["розрив центр–корпус на кожному SMA pod з вимкненим зміщенням", "клапан не дивиться догори",
      "посадка, герметизація, S21 і NF на 2.2–2.3 ГГц — ворота E4-04 (OPEN)",
      "вилка W425 входить лише в J551, а в J504 (GX16) і J505 (GX12) — ні; на J551 при EN_SB_LNA = 0 — 0 V"],
     ["F40", "F41", "F42", "F43", "F44", "S41"]),
    ("E9c", "Зовнішній аксесуар P8 (у лінії антени, поза корпусом)",
     "Nooelec Flamingo+ FM #2 (A403), RTL-SDR Blog Wideband LNA V2 (A404) з перехідником SMA male–male з комплекту LNA (якщо обидва гнізда — SMA female; "
     "роди роз'ємів A403/A404 не прочитано), коаксіальний кабель A404 → P8; "
     "коробка аксесуара, адаптери, кабель і кріплення — SRC-2 (CC-27; mechanical/params/parts.json p8_accessory, правило R-P8-ACCESSORY)",
     ["Ланцюг (build/03, рядок P8): антена → вхід SMA A403 (J428) → A403 OUT → перехідник SMA male–male з комплекту LNA V2 → A404 IN — припущення: "
      "обидва гнізда SMA female (роди роз'ємів A403 і A404 не прочитано: сторінка LNA V2 їх не наводить, 07.11.2026; перевірити при вхідному контролі й за "
      "потреби взяти інший перехідник — SRC-2); A404 OUT → кабель → панельний P8 "
      "(Taoglas CAB.718, J408). Зміщення ch4 4.3 V приходить на A404 лише цим кабелем через P8 (LNA V2: «Requires 3 - 5v bias tee power»); інших "
      "джерел живлення аксесуара немає, P8 віддає назовні лише зміщення LNA — правило «лише прийом».",
      "Обидва модулі — у коробку аксесуара (SRC-2) поруч, за порядком ланцюга; розміри A404 на сторінці виробника не наведено (07.11.2026), тож конверт коробки — "
      "TBD до вимірювання отриманого LNA V2; A403 — резерв 73.7 × 30.6 × 18.7 (припущення, як корпус SAWbird+).",
      "Коробку кріпити біля антени (щогла або штатив; кріплення — SRC-2), кабель до P8 — без перегину біля роз'ємів; ключ 0.9 N·m лише для "
      "нержавіючих SMA (правило F15).",
      "Ущільнення коробки й роз'ємів — TBD (ворота T-07 OPEN)."],
     ["з вимкненим ch4 на P8 — 0 V (записати в бланк 20)",
      "ch4 не має DC-sense (E4-06 OPEN): кабель аксесуара на P8 під'єднувати й від'єднувати лише з вимкненим ch4",
      "посадка, ущільнення і S21/NF аксесуара — стенд (OPEN)"],
     []),
    ("E10", "Бондинг, перевірка і закриття",
     "EPDM-шнур, гвинти половин F12 з ущільнювальними шайбами, кришка лючка F13",
     ["Бондинг CHASSIS за 16 §9 (F26), зокрема BOND-RF.",
      "Перевірка перед закриттям — 19 §6 (ще від стенду); бланк 20.",
      "Лише після ступенів L0–L4 від стенду (19 §5; 09 ЗБ-02): від'єднати стендовий провід, S05 паку — у вхідний роз'єм S05 (J105) на PWR-A, F101 — у тримач носійної плати.",
      "EPDM-шнур у паз без розтягу, стик — на прямій ділянці; половини — гвинти хрест-навхрест у два проходи (F12); кришка лючка (F13).",
      "Перше ввімкнення від паку — 08 крок 16 п. 6 і таблиця перевірки кроку 16."],
     ["шнур не виступає з пазу", "перевірки 08 крок 16 від паку (INA228, labd) на закритому корпусі", "тест штативної гайки ≥3 N·m (F25)"],
     ["F26", "S05", "F12", "F13"]),
]

# Printed parts (table in build/21 §1); geometry belongs to the mechanical package.
PRINTS = [
    # from the printed parts of the mechanical model (mechanical/generated/stl, fit-report «Друковані деталі»)
    ("корпус: передня половина (front_shell)", "лицем на стіл", "≥4 периметри у бобишках вставок; 30 % заповнення (mechanical.json print)", "лише під навислими вирізами портів"),
    ("корпус: задня половина (rear_shell)", "внутрішньою стороною вгору", "≥4 периметри; бобишка гайки 1/4-20 — 100 % (STACK §5.8)", "під прорізами ременя"),
    ("кришка сервісного лючка (hatch_cover)", "пласко", "≥4 периметри навколо вставок", "ні"),
    ("козирок 30 мм (hood, шарнірний)", "пласко", "3 периметри (PIS)", "ні"),
    ("лоток батареї (battery_tray)", "дном на стіл", "3 периметри (PIS)", "ні"),
    ("тримач T7 (t7_holder)", "пласко", "3 периметри (PIS)", "ні"),
    ("притискачі дисплея ×4 (display_clamp_x4)", "пласко", "3 периметри (PIS)", "ні"),
    ("ковпачки кнопок ×4 і з ребром ×2 (button_cap_x4, button_cap_ribbed_x2)", "торцем на стіл", "суцільні", "ні"),
    ("ручка головного енкодера (main_knob)", "спідницею на стіл", "≥4 периметри", "ні"),
    ("носій паку IMU (imu_carrier)", "пласко", "≥4 периметри навколо вставки 1/4-20", "ні"),
]
