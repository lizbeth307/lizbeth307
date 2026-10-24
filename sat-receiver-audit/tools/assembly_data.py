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

# --- Sources actually read for catalogue values (URL, what it gives) --------
SOURCES = {
    "JST-PH": ("https://www.jst-mfg.com/product/pdf/eng/ePH.pdf",
               "JST PH: 2 A AC/DC (AWG #24), 100 V, −40…+105 °C; провід AWG #32…#24, ізоляція ⌀0.5…1.5 мм; "
               "SPH-002T-P0.5S — AWG #30…#24, ⌀0.8…1.5 мм; PHR-2…PHR-16; B2B…B16B-PH-K-S (верхній вхід), S2B…S16B-PH-K-S (боковий)"),
    "MOLEX-43030": ("https://www.farnell.com/datasheets/1887331.pdf",
                    "Molex 43030-0007 (пакет; 43030-0001 — котушка, https://www.farnell.com/datasheets/1864962.pdf): гніздова клема Micro-Fit 3.0, "
                    "20/22/24 AWG, ізоляція ≤1.85 мм, 5 A на контакт (документи 2014–2016; лист 2018 https://www.farnell.com/datasheets/2696325.pdf — 8.5 A); "
                    "ручний інструмент 0638190000, екстрактор 0011030043"),
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
                      "(нагрів ≈50 °C над середовищем у вакуумі); у джгуті IBmax = Imax·(29−n)/28 при 1<n<15, Imax/2 при n>15"),
    "NASA-19990009916": ("https://ntrs.nasa.gov/citations/19990009916",
                         "Cable Bundle Wire Derating (1998): 20 AWG — 3.7 A на провід у джгуті ≥15 проводів, 70 °C, вакуум (перехресна перевірка ESCC)"),
    "PEC11R": ("https://www.bourns.com/docs/Product-Datasheets/PEC11R.pdf",
               "Bourns PEC11R (REV. 04/26): момент кріплення 10.2 kgf·cm (8.83 lb·in) макс. ≈1.0 N·m; гайка M7×0.75 і шайба в комплекті; IP40; −30…+70 °C"),
    "PV0": ("https://configured-product-images.s3.amazonaws.com/Datasheets/PV0.pdf",
            "E-Switch PV0 (3.16.2026): антивандальна кнопка, виріз ⌀12.00 (+0.20) мм, панель 1–6 мм, IP67, 2 A 36 VDC, SPST Off-(On), "
            "момент гайки 0.6 N·m, −40…+85 °C"),
    "LTW-VENT": ("https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/7136/Amphenol%20LTW_Pressure%20Relief%20Vent%20Group.pdf",
                 "Amphenol LTW, каталог клапанів, M12 Plastic (VENT-PS1YBK-O8002 — з гайкою): M12×1.5, момент 6.0–8.0 kgf·cm (0.59–0.78 N·m), "
                 "наскрізний отвір 2.0–3.5 мм або різьбовий ≥4.0 мм, IP68/IP69K, O8002 >1000 ml/min при 7 kPa"),
    "WE-SMA": ("https://www.we-online.com/components/products/datasheet/60311082111559.pdf",
               "Würth WR-SMA 60311082111559 (2025-03-03): THT-гніздо SMA з прокладкою, IP67 на панелі; момент різьби на панелі 57 N·cm "
               "(«має виконуватися для IP67»), рекомендований момент стикування 57 N·cm, панель ≤2.8 мм, виріз ⌀6.5 з лискою 6"),
    "BINDER-M8": ("https://binder-usa.com/us-en/products/automation-technology/m8/86-6618-1120-00006-m8-female-panel-mount-connector-6-shieldable-tht-ip67-m10x075-front-fastened",
                  "binder 86 6618 1120 00006 (alt. 09 3422 81 06), M8 серія 718, 6 конт., A-код, THT, IP67, M10×0.75, 1.5 A, 30 V, −40…+85 °C; "
                  "кільце кабельного роз'єму — від руки ≈50 cN·m; сторінка суперечлива щодо переднього/заднього монтажу, виріз і момент гайки не наведені"),
    "CNCK-M3": ("https://3djake.ch/en-CH/cnc-kitchen/threaded-inserts-m3-standard",
                "CNC Kitchen TC-M3x5.7: L 5.7, ⌀D1 4.6, отвір ⌀D3 4.0, стінка ≥1.6; ставити на 10–20 °C вище температури друку"),
    "CNCK-M25": ("https://3djake.ch/en-CH/cnc-kitchen/threaded-inserts-m25-standard",
                 "CNC Kitchen TC-M2,5x4: L 4.0, ⌀D1 4.6, отвір ⌀D3 4.0, стінка ≥1.6 (так у лістингу; звірити з кресленням CNC Kitchen перед CAD)"),
    "POLY-ASA": ("https://polymaker.com/wp-content/tech-docs/PolyLite_ASA_PIS_EN_V1.3.pdf",
                 "PolyLite ASA PIS V1.3: сопло 240–260 °C, стіл 75–95 °C, обдув вимкнено, 30–50 мм/с, корпус принтера рекомендовано; "
                 "Tg 97.8 °C, Vicat 105.3 °C; сушіння 80 °C 8 год"),
    "LAPP-MSM": ("https://media.lappcdn.com/8/876/87682/9bae7263e0a64d10b08facf80500d163.pdf",
                 "LAPP SKINTOP MS-M/MSR-M, інструкція: IP68 10 bar, −20…+100 °C динамічно; таблиця моментів (розмітка таблиці в PDF злита, для MS-SC-M окремо не прочитано)"),
    "OLIMEX-GX16": ("https://www.olimex.com/Products/Components/Connectors/CONNECTOR-GX16-4/",
                    "Olimex CONNECTOR-GX16-4 (у наявності 24.10.2026); 6-контактного GX у Olimex немає (лише GX12-4, GX16-4)"),
}

# --- Physical units ----------------------------------------------------------
# kind: board (copper can route a net through), module, panel (part in a wall),
# cable (assembly end), remote (outside the enclosure).
BOARD_OF_DOMAIN = {  # build/15 «Кількість плат»
    "PWR_MAIN": "PWR", "PWR_BRANCH": "PWR", "USB_POWER": "PWR",
    "RF_HMC": "RF", "RF_HF": "RF", "RF_INJECTOR": "RF", "DC_CORE": "RF",
    "CTRL_HMI": "CTRL",
}

UNITS = [
    # id, kind, name, place
    ("PWR", "board", "Силова плата PWR (PWR_MAIN + PWR_BRANCH + USB_POWER)", "унизу праворуч на середній пластині (STACK §5.8)"),
    ("CTRL", "board", "Плата керування/HMI CTRL (CTRL_HMI)", "за правою колонкою HMI; кнопки й енкодери крізь лице"),
    ("RF", "board", "RF/детекторна плата RF (RF_HMC + RF_HF + RF_INJECTOR + DC_CORE)", "РЧ-відсік уздовж верхнього краю"),
    ("Q6A.HDR", "module", "Q6A, 40-pin J20 (J301)", "середня пластина"),
    ("Q6A.CORE", "module", "Q6A, бортові шини (U500)", "середня пластина"),
    ("Q6A.J21", "module", "Q6A, майданчики J21 (J521)", "середня пластина"),
    ("Q6A.J5", "module", "Q6A, USB J5 (J511)", "середня пластина"),
    ("Q6A.J2", "module", "Q6A, USB J2 (J512)", "середня пластина"),
    ("Q6A.HDMI", "module", "Q6A, HDMI (J520)", "середня пластина"),
    ("Q6A.MKEY", "module", "Q6A, M.2 M-key (J530)", "середня пластина"),
    ("Q6A.EDL", "module", "Q6A, контакти кнопки EDL (J522)", "середня пластина"),
    ("Q6A.RTC", "module", "Q6A, J11 RTC (J303 + BT301)", "середня пластина"),
    ("PACK", "module", "Пак 4S1P + BMS Daly (BT101–BT104, U101, TH101)", "батарейний відсік зліва внизу"),
    ("INA", "module", "Adafruit INA228 5832 (U102, R101, C101, C102)", "на стійках над PWR"),
    ("SWM", "module", "Pololu #2813 (U106)", "на середній пластині біля PWR"),
    ("REG12", "module", "Pololu D36V50F12 (U107)", "прикріплено до середньої пластини"),
    ("REG5", "module", "Pololu D36V50F5 #4091 (U108)", "прикріплено до середньої пластини"),
    ("CHG", "module", "IP2368 COUT (U110, R117–R120, C118, TH102)", "на стінці корпусу, ≥10 мм від елементів"),
    ("HUB", "module", "Adafruit 5997 CH334F (U510)", "біля Q6A J2"),
    ("T7A", "cable", "Вставка ключа VBUS T7 (U505, R514–R517, C514–C516, TP501)", "у розриві USB3 біля Q6A J5"),
    ("T7", "remote", "Samsung T7 + цілісний кабель A–C (U540)", "ззовні ззаду внизу, тримач"),
    ("HDMIA", "cable", "HDMI-вставка pin 18 (U506, C517, C518, R552, TP502)", "біля HDMI Q6A"),
    ("DISP", "module", "Дисплей Wisecoco (U520)", "лице"),
    ("RISER", "module", "ADT-Link R44SF (U530)", "крізь вікно пластини"),
    ("LIME", "module", "LimeSDR Micro M.2 (A415)", "на п'єдесталі"),
    ("RTLA", "cable", "RTL-A V4L + кабель USB (A411, J543)", "РЧ-відсік"),
    ("RTLB", "cable", "RTL-B V4L + кабель з розділеним VBUS (A412, J541)", "РЧ-відсік"),
    ("HFP", "cable", "Airspy HF+ + пігтейл micro-USB (A414, J544)", "екран Schubert 6B угорі праворуч"),
    ("USBC", "panel", "USB-C PD (J103)", "нижній край"),
    ("XT30", "panel", "Сервісний XT30 (J101)", "пігтейл у батарейному відсіку (v2.1: заряд ISDT заблоковано)"),
    ("LABUSB", "panel", "LAB USB-A (J501)", "нижній край"),
    ("LABBUS", "panel", "LAB BUS (J505)", "нижній край"),
    ("GX16", "panel", "Гніздо IMU GX16-4 (J504)", "задня стінка"),
    ("UART5", "panel", "Консоль UART5 (J502)", "сервісний лючок"),
    ("J21H", "panel", "Сервісний роз'єм J21 (J503)", "сервісний лючок"),
    ("EDL", "panel", "Кнопка EDL (SW501)", "сервісний лючок"),
    ("PWRBTN", "panel", "Кнопка живлення (SW301)", "TBD (STACK §5.8 не задає місце)"),
    ("IMUPACK", "remote", "IMU-пак Hammond 1550Z101 (U309, U314, J550, D502, C519, C520, U552 і деталі E3 «External IMU»)", "на штанзі антени, ≥30 см позаду"),
    ("GNSS", "module", "LC76G (U304)", "біля P7"),
    ("VEML", "module", "Adafruit 4162 VEML7700 (U308)", "верхня грань безеля, поза козирком"),
    ("FAN1", "module", "Noctua NF-A4x10 5V (FAN301)", "задній отвір, шлях 1"),
    ("FAN2", "module", "Delta BFB0305HA-C (FAN302)", "канал дисплея, шлях 2"),
    ("BONI", "module", "Bias-tee Boni-Whip (A406)", "поруч з G6K, поза екраном HF+"),
    ("SPOD", "remote", "Кабель живлення S-band pod (W425)", "зовнішній вузол"),
]

# Refs whose physical place is not given by the partition column.
UNIT_OF_REF = {
    "J301": "Q6A.HDR", "U500": "Q6A.CORE", "J521": "Q6A.J21", "J511": "Q6A.J5", "J512": "Q6A.J2",
    "J520": "Q6A.HDMI", "J530": "Q6A.MKEY", "J522": "Q6A.EDL", "J303": "Q6A.RTC", "BT301": "Q6A.RTC",
    "BT101": "PACK", "BT102": "PACK", "BT103": "PACK", "BT104": "PACK", "U101": "PACK", "J102": "PACK", "TH101": "PACK",
    "U102": "INA", "R101": "INA", "C101": "INA", "C102": "INA",
    "U106": "SWM", "U107": "REG12", "U108": "REG5",
    "U110": "CHG", "R117": "CHG", "R118": "CHG", "R119": "CHG", "R120": "CHG", "C118": "CHG", "TH102": "CHG",
    "F101": "PWR", "F102": "PWR", "F103": "PWR", "F201": "PWR", "F202": "PWR", "J302": "PWR",
    "J101": "XT30", "J103": "USBC",
    "U510": "HUB", "U540": "T7", "U520": "DISP", "U530": "RISER", "A415": "LIME",
    "A411": "RTLA", "J543": "RTLA", "A412": "RTLB", "J541": "RTLB", "A414": "HFP", "J544": "HFP",
    "J501": "LABUSB", "J505": "LABBUS", "J504": "GX16", "J502": "UART5", "J503": "J21H", "SW501": "EDL",
    "SW301": "PWRBTN", "U304": "GNSS", "U308": "VEML", "FAN301": "FAN1", "FAN302": "FAN2",
    "U305": "CTRL", "ENC301": "CTRL", "ENC302": "CTRL", "BZ301": "CTRL",
    "SW302": "CTRL", "SW303": "CTRL", "SW304": "CTRL", "SW305": "CTRL", "SW306": "CTRL", "SW307": "CTRL",
    "SW308": "CTRL", "SW309": "CTRL",
    "U309": "IMUPACK", "U314": "IMUPACK", "J550": "IMUPACK", "D502": "IMUPACK", "C519": "IMUPACK",
    "C520": "IMUPACK", "U552": "IMUPACK",
    "U506": "HDMIA", "C517": "HDMIA", "C518": "HDMIA", "R552": "HDMIA", "TP502": "HDMIA",
    "U505": "T7A", "R514": "T7A", "R515": "T7A", "R516": "T7A", "R517": "T7A", "C514": "T7A", "C515": "T7A",
    "C516": "T7A", "TP501": "T7A",
    "A406": "BONI", "W425": "SPOD", "NT401": "RF",
    "J409": "RF", "J410": "RF", "J411": "RF", "J412": "RF",
}
# Test points of E1/E2 sit on the power board.
for _n in list(range(101, 109)) + list(range(201, 217)) + [2901, 2902, 2903]:
    UNIT_OF_REF[f"TP{_n}"] = "PWR"
# Bare parts drawn on E3 but built into the IMU pack (E3 group "External IMU").
UNIT_OF_GROUP = {("E3", "External IMU"): "IMUPACK"}
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
     "IDC 2×20 2.54 мм 1:1; на CTRL — екранований бокс-роз'єм 2×20 з ключем"),
    ("S02", "CTRL", "PWR", "Керування і LAB5: CTRL ↔ PWR", None, "TBD (CAD)",
     "на PWR 5 мереж I2C2/INT/3V3_Q6A приходять у J302 (E3), решта — у роз'єми X02"),
    ("S03", "CTRL", "RF", "Керування RF: CTRL ↔ RF", None, "TBD (CAD)", "лінії HMC7992/G6K/DCS; вести вздовж пластини, подалі від буферних дроселів"),
    ("S04", "PWR", "RF", "Зміщення і реле: PWR ↔ RF", None, "TBD (CAD)", "шини bias ch1–ch4, LNB і LAB5 котушок G6K"),
    ("S05", "PACK", "PWR", "Пак → PWR", None, "мінімальна (TBD, CAD)", "до F101 дріт захищає лише BMS (DOCP 40±10 A, 02 §2) — найкоротша траса, без петель"),
    ("S06", "PWR", "INA", "PWR ↔ INA228 (шунт)", None, "TBD (CAD)", "VIN+/VIN− — клеми шунта Adafruit 5832; I2C0/ALERT/VS — гребінка модуля"),
    ("S07", "PWR", "SWM", "PWR ↔ Pololu #2813", None, "TBD (CAD)", "пайка до контактів модуля"),
    ("S08", "PWR", "REG12", "PWR ↔ D36V50F12 (SYS12)", None, "TBD (CAD)", "пайка до контактів модуля"),
    ("S09", "PWR", "REG5", "PWR ↔ D36V50F5 (LAB5)", None, "TBD (CAD)", "пайка до контактів модуля"),
    ("S10", "PWR", "CHG", "PWR ↔ IP2368", None, "TBD (CAD)", "пайка до контактів роздрібної плати; KSD9700 — на MOSFET плати"),
    ("S11", "USBC", "PWR", "USB-C панелі → PWR", None, "TBD (CAD)", "CC1/CC2 проходять PWR транзитом до IP2368"),
    ("S12", "PWR", "XT30", "PWR → сервісний XT30", None, "TBD (CAD)", "пігтейл XT30U-M; v2.1: ISDT/raw-balance заблоковано до E1-02"),
    ("S13", "PWR", "HUB", "LAB5 → CH334F JP5.1", None, "TBD (CAD)", "лише живлення хаба; дані — кабель C-HUB"),
    ("S14", "PWR", "J21H", "J21 12 V → J503", None, "TBD (CAD)", "кручена пара 12 V/GND (STACK §5.8)"),
    ("S15", "CTRL", "J21H", "PWR_ON_KEY → J503.3", None, "TBD (CAD)", "окрема жила KEY 26–28 AWG до вузла АБО (STACK §5.8)"),
    ("S16", "J21H", "Q6A.J21", "J503 → майданчики J21 Q6A", "SOLDER", "TBD (CAD)",
     "після прогону Q6A (08 крок 7.7): 12 V/GND — кручена пара 20 AWG, KEY — 26–28 AWG; термоусадка на кожному з'єднанні, поліімід на корпусі USB-C"),
    ("S17", "PWR", "Q6A.CORE", "VCC_3V3_MKEY Q6A → ключ LIME3V3", None, "TBD (CAD)",
     "точка відводу 3.3 V M.2 на Q6A не визначена (E5/E2) — TBD до прозвонки Q6A"),
    ("S18", "PWR", "RISER", "LIME3V3 → R44SF (бік картки)", None, "TBD (CAD)", "лише до контактів 3.3 V картки, відділених від VCC_3V3_MKEY (E5 §10)"),
    ("S19", "PWR", "DISP", "DISP12 → барель Wisecoco", None, "TBD (CAD)", "розмір і полярність бареля — E5-01 відкрито"),
    ("S20", "PWR", "RTLA", "VBUS_RTLA → кабель RTL-A (J543.1)", None, "TBD (CAD)", "VBUS вставляється в пігтейл H2; JP1.1 хаба не з'єднувати"),
    ("S21", "PWR", "RTLB", "VBUS_RTLB → кабель RTL-B (J541.1)", None, "TBD (CAD)", "розділений VBUS; J5.10 не з'єднувати"),
    ("S22", "PWR", "HFP", "VBUS_HFP → пігтейл HF+ (J544.1)", None, "TBD (CAD)", "після L501 і демпфера; 2× Fair-Rite 2631480002 на повному кабелі"),
    ("S23", "PWR", "LABUSB", "VBUS_LABPORT → J501.1", None, "TBD (CAD)", "C506 біля вихідного порту"),
    ("S24", "CTRL", "T7A", "EN_T7/3V3 → вставка T7", None, "TBD (CAD)", "U505 на вставці USB3"),
    ("S25", "CTRL", "GNSS", "CTRL → LC76G", None, "≤200 разом з S01 для PPS", "UART6 і PPS з J20 транзитом через CTRL"),
    ("S26", "CTRL", "VEML", "CTRL → VEML7700", None, "TBD (CAD)", "100 Ω + TVS біля безеля (на CTRL)"),
    ("S27", "CTRL", "FAN1", "CTRL → Noctua", "FAN3", "кабель вентилятора", "штатний 3-контактний роз'єм Noctua; на CTRL — сумісна 3-контактна вилка 2.54 мм"),
    ("S28", "CTRL", "FAN2", "CTRL → повітродувка Delta", None, "TBD (CAD)", "2 дроти; низький ключ на CTRL"),
    ("S29", "CTRL", "PWRBTN", "CTRL → кнопка живлення", None, "TBD (CAD)", "пайка до контактів кнопки"),
    ("S30", "CTRL", "UART5", "CTRL → консоль UART5 (J502)", None, "TBD (CAD)", "лише 3.3 V TTL, без живлення адаптера"),
    ("S31", "Q6A.EDL", "EDL", "Контакти EDL Q6A → SW501", "SOLDER", "TBD (CAD)", "точки пайки на Q6A не локалізовано (E5 §9)"),
    ("S32", "PWR", "GX16", "PWR → гніздо GX16-4 (J504)", None, "TBD (CAD)", "U551 біля входу на PWR; корпус GX16 → CHASSIS"),
    ("S33", "GX16", "IMUPACK", "Зовнішній кабель IMU", "CABLE", "2000 (HELU 49655, STACK §2.10)",
     "HELU SUPERTRONIC-C-PURO 4×0.14 мм²; оплітка 360° у GX16 і в SKINTOP паку"),
    ("S34", "PWR", "LABBUS", "PWR → LAB BUS (J505)", None, "TBD (CAD)", "кабель за межами корпусу ≤1 м (понад — PCA9615, E5 §9)"),
    ("S35", "PWR", "BONI", "BONI13V8_PORT → bias-tee Boni", None, "TBD (CAD)", "штекер 5.5/2.1 мм (STACK, «Склад набору кабелів»)"),
    ("S36", "PWR", "SPOD", "BIAS_SB_LNA → кабель W425", None, "TBD (CAD); W425 = 1500",
     "ввід кабелю живлення pod у корпус у графах не визначено — TBD (E2/E4)"),
]

# Families: (name, contact rating A, design share, AWG allowed, source)
FAMILIES = {
    "PH": {"title": "JST PH 2.0 мм", "rating": 2.0, "share": 0.6, "awg": (26, 24), "signal_awg": 26, "power_awg": 24,
           "max_pins": 16, "source": "JST-PH",
           "housing": "PHR-{n}", "header": "S{n}B-PH-K-S (боковий вхід) або B{n}B-PH-K-S (верхній)", "terminal": "SPH-002T-P0.5S",
           "tool": "ручний інструмент JST для SPH-002T-P0.5S — TBD (каталог ePH називає лише аплікатор APLMK SPH002-05S / машину AP-K2N)"},
    "MF": {"title": "Molex Micro-Fit 3.0 (1 ряд, 3.00 мм)", "rating": 5.0, "share": 0.6, "awg": (24, 22, 20), "signal_awg": 24, "power_awg": 20,
           "max_pins": 12, "source": "MOLEX-43030",
           "housing": "43645-0{n:d}00 (серія 43645; перевірені коди — 0436450300, 436450508, 0436451000, 436451200)",
           "header": "43650 вертикальна, Sn, TH (точний код — parts DB)", "terminal": "0430300007 (пакет) / 0430300001 (котушка)",
           "tool": "Molex 0638190000; екстрактор 0011030043"},
    "IDC": {"title": "IDC 2×20, 2.54 мм, стрічка 1.27 мм", "rating": None, "share": None, "awg": (28,), "signal_awg": 28, "power_awg": 28,
            "max_pins": 40, "source": None, "housing": "IDC-гніздо 2×20 з ключем — parts DB", "header": "бокс 2×20 з ключем на CTRL — parts DB",
            "terminal": "—", "tool": "прес IDC"},
    "SOLDER": {"title": "пайка до майданчиків", "rating": None, "share": None, "awg": (28, 26, 24, 22, 20), "signal_awg": 26, "power_awg": 20,
               "max_pins": 99, "source": None, "housing": "—", "header": "—", "terminal": "—", "tool": "паяльник; термоусадка"},
    "CABLE": {"title": "готовий кабель", "rating": None, "share": None, "awg": (26,), "signal_awg": 26, "power_awg": 26,
              "max_pins": 99, "source": None, "housing": "—", "header": "—", "terminal": "—", "tool": "—"},
    "FAN3": {"title": "3-контактний роз'єм вентилятора 2.54 мм (штатний Noctua)", "rating": None, "share": None, "awg": (26,),
             "signal_awg": 26, "power_awg": 26, "max_pins": 3, "source": None,
             "housing": "штатний на кабелі Noctua", "header": "3-контактна вилка 2.54 мм із замком — parts DB", "terminal": "—", "tool": "—"},
}
# Fixed gauges where STACK names them (segment, net) -> AWG
FIXED_AWG = {("S14", "J21"): 20, ("S14", "GND"): 20, ("S16", "J21"): 20, ("S16", "GND"): 20, ("S16", "PWR_ON_KEY"): 24}
# Segments that may carry only the listed nets (GND is added by the generator where both ends have it).
SEGMENT_NETS = {
    "S13": {"LAB5"}, "S14": {"J21"}, "S15": {"PWR_ON_KEY"}, "S16": {"J21", "PWR_ON_KEY"}, "S17": {"VCC_3V3_MKEY"},
    "S18": {"LIME3V3"}, "S19": {"DISP12"}, "S20": {"VBUS_RTLA"}, "S21": {"VBUS_RTLB"}, "S22": {"VBUS_HFP"},
    "S23": {"VBUS_LABPORT"}, "S35": {"BONI13V8_PORT"}, "S36": {"BIAS_SB_LNA"},
}
NO_GND = {"S15"}  # KEY joins J503, whose GND contact already carries the S14 return
GND_GROUP_SKIP = {("S06", "MF"), ("S07", "MF")}  # shunt path and #2813 switch: no return current in that connector
GND_CURRENT = {"S06": (0.01, None), "S07": (0.05, None)}  # chip/control ground only (INA228, #2813 logic)
# Module end of a wire: which contact it lands on, (segment, unit, net) -> "REF.PIN (note)".
END_PIN = {
    ("S05", "PACK", "E1_CELL4"): "BT104.+ (плюс паку, не сенсорний B4 BMS)", ("S05", "PACK", "GND"): "U101.P- (P− BMS)",
    ("S06", "INA", "E1_N"): "R101.2 (клема VIN− модуля 5832)", ("S06", "INA", "E1_SHUNT_P"): "R101.1 (клема VIN+ модуля 5832)",
    ("S06", "INA", "GND"): "U102.7", ("S07", "SWM", "GND"): "U106.GND", ("S08", "REG12", "GND"): "U107.GND",
    ("S09", "REG5", "GND"): "U108.GND", ("S10", "CHG", "GND"): "U110.BAT-", ("S13", "HUB", "GND"): "U510.JP5_4",
    ("S17", "Q6A.CORE", "GND"): "U500.GND", ("S18", "RISER", "GND"): "U530.GND", ("S19", "DISP", "GND"): "U520.DC_GND",
    ("S24", "T7A", "GND"): "U505.5", ("S25", "GNSS", "GND"): "U304.P1.2", ("S26", "VEML", "GND"): "U308.GND",
    ("S27", "FAN1", "GND"): "FAN301.GND", ("S35", "BONI", "GND"): "A406.SHIELDS", ("S36", "SPOD", "GND"): "W425.RETURN",
    ("S10", "CHG", "E1_CHG_NTC"): "U110.NTC",
}
ESCC_IMAX = {28: 1.5, 26: 2.5, 24: 3.5, 22: 5.0, 20: 7.5, 18: 10.0}

# --- Design currents: net -> (continuous A, protective/limiting A, protection, source)
# Signals not listed: 0.05 A, no protection value (logic level).
NET_CURRENT = {
    "E1_CELL4": (4.6, 7.5, "BMS Daly (DOCP 40±10 A) до F101; F101 7.5 A після", "02 §2–3 (модель 4.6 A з Lime)"),
    "E1_SHUNT_P": (4.6, 7.5, "F101 7.5 A", "02 §3"),
    "E1_N": (4.6, 7.5, "F101 7.5 A", "02 §3"),
    "E1_SW": (4.6, 7.5, "F101 7.5 A (вище за течією)", "02 §3"),
    "SYS12": (4.0, 7.5, "F101 7.5 A вище; власна межа D36V50F12 — TBD", "02 §2 (≈4 A пік з Lime)"),
    "E1_LAB5_RAW": (3.2, 7.5, "F101 7.5 A вище; F102 4 A — після цього дроту", "E1.json lab5_budget (3.2 A тривало, 4 A перехідно)"),
    "LAB5": (1.0, 4.0, "F102 4 A", "бюджет гілки 1.0 A — рішення asm; загальний бюджет LAB5 3.2 A (E1-05)"),
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
    "E3_FAN5": (0.25, 4.0, "F102 4 A (ключ Q304 без межі струму)", "бюджет вентилятора — рішення asm, виміряти"),
    "E3_BLOWER_GND": (0.50, 4.0, "F102 4 A (ключ Q305 без межі струму)", "E3-03: 0.25 A тривало / 0.50 A старт"),
    "VCC_5V_PERI": (0.10, 4.5, "бортовий SGM40666 Q6A (≈4.5 A, 02 §2)", "LC76G — малий струм; бюджет 0.10 A — рішення asm"),
    "3V3_Q6A": (0.10, 0.10, "PMIC Q6A (межа не опублікована)", "бюджет шини логіки — рішення asm"),
    "AON3V3": (0.01, 0.01, "TPS70933", "02 §4 (INA228 ≤750 мкА)"),
    "E3_PICO3V3": (0.02, 0.02, "LDO Pico", "VEML7700 — малий струм"),
}
# Per-segment overrides (segment, net) -> (cont, prot, protection, source)
SEG_CURRENT = {
    ("S10", "E1_N"): (3.0, 7.5, "F101 7.5 A (вузол N)", "IP2368 RISET 15k = 3 A (02 §5)"),
    ("S28", "LAB5"): (0.50, 4.0, "F102 4 A", "E3-03: старт 0.50 A"),
    ("S32", "LAB5"): (0.20, 4.0, "F102 4 A (окремої межі гілки IMU немає)", "бюджет паку IMU — рішення asm, виміряти"),
    ("S13", "LAB5"): (0.30, 4.0, "F102 4 A", "бюджет хаба — рішення asm, виміряти"),
    ("S04", "LAB5"): (0.10, 4.0, "F102 4 A", "2 котушки G6K ≈21.1 mA (08 крок 10)"),
}

# Wire colours by net (regex, colour) — project convention, first match wins.
COLOURS = [
    (r"^GND$", "чорний"), (r"^CHASSIS$", "жовто-зелений"),
    (r"^(E1_CELL4|E1_SHUNT_P|E1_N|E1_SW|E1_SERVICE_P|E1_USB_PD_RAW|E1_USB_PD_SAFE)$", "коричневий"),
    (r"^(SYS12|J21|DISP12|AUX12)$", "жовтий"),
    (r"^(LAB5|E1_LAB5_RAW|VBUS_|E3_FAN5|VCC_5V_PERI|BIAS_SB_LNA)", "червоний"),
    (r"^(LNB13V2|BONI13V8_PORT)$", "фіолетовий"),
    (r"^BIAS_CH", "рожевий"),
    (r"^(3V3_Q6A|AON3V3|LIME3V3|VCC_3V3_MKEY|E3_PICO3V3)$", "помаранчевий"),
    (r"(SDA|SDA_)", "синій"), (r"(SCL)", "білий"),
    (r"^(UART|IMU_)", "зелений"),
    (r"^(EN_|PICO_|CHG_INHIBIT|SW_|K[12]_ON)", "сірий"),
    (r"^(FAULT_|FLT_|PG_|DCS_|OVP_|PTC_|MCP_INT|INA228_ALERT|SLED_DET)", "блакитний"),
    (r".*", "білий"),
]
INSULATION = "PTFE, луджена мідь багатодротова, ≥200 °C (тип і MPN — parts DB); ⌀ ізоляції в межах клеми"

# High-speed / factory cable assemblies: id -> (title, net regex, ends, parts)
ASSEMBLIES = [
    ("C-HDMI", "HDMI Q6A → Wisecoco", r"^E5_HDMI_", "Q6A.HDMI → HDMIA → DISP",
     "Adafruit 2420 457 мм + 2× Fair-Rite 0431164281; pin 18 через U506 на вставці (E5 §8); TMDS не розплітати"),
    ("C-T7", "USB3 Q6A J5 нижній → T7", r"^E5_(T7_|VBUS_J5|VBUS_T7)", "Q6A.J5 → T7A → T7",
     "цілісний екранований кабель A–C ≤0.5 м + вставка U505 (E5 §7); перевірка 5000M/uas"),
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
    ("L-T7", "нижній край, гермоввід T7", "T7 USB3", "полієстер, УФ-стабільний ламінат", "20×6", "STACK §5.8"),
    ("L-IMU", "задня стінка, GX16-4", "IMU · GX16-4 · 5 V · ключ ▲", "полієстер, УФ-стабільний ламінат", "30×8", "E5 §9"),
    ("L-HATCH", "кришка сервісного лючка", "СЕРВІС: UART5 · EDL · J21 · USB-A", "полієстер, УФ-стабільний ламінат", "45×8", "STACK §5.8"),
    ("L-J21", "сервісний лючок, біля J503", "J21 unplugged before USB-C", "поліімід", "40×6", "05 §5.5; STACK §11.5 #16"),
    ("L-SUN", "внутрішній бік козирка", "не лишати лицем до сонця", "полієстер, УФ-стабільний ламінат", "40×6", "05:56"),
    ("L-BAT", "пак 4S1P", "Li-ion 4S1P · 14.4 V ном. · 72 Wh · F1 7.5 A · не перевозити літаком", "поліімід", "60×20", "08 крок 0 п. 2; 02 §2"),
    ("L-F101", "біля F101", "F1 7.5 A — вийняти для зберігання >2–4 тиж.", "поліімід", "30×6", "02 §9 п. 9"),
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
     "стійка M2.5 F-F (висота з CAD)", "TBD — виробник не публікує; задати за купоном (див. §2)", "—", "—", "E3"),
    ("F02", "стійки Q6A → пластина 2 мм Al", "гвинт M2.5 (довжина з CAD) знизу пластини", "4", "2",
     "наскрізний отвір ⌀3.5 у пластині (різьбу не нарізати, 08 крок 5)", "TBD — купон", "—", "пружинна шайба M2.5", "E3"),
    ("F03", "кришка Armor 7056A (варіант B охолоджувача)", "гвинт M2.5 зі стійками комплекту Radxa", "за комплектом", "2",
     "стійки M2.5 крізь отвори ⌀3.5", "TBD — за інструкцією Radxa", "—", "—", "E3"),
    ("F04", "п'єдестал Lime → пластина", "гвинт M2.5 (тип і довжина з CAD)", "TBD (CAD)", "2", "пластина/п'єдестал", "TBD — купон", "—", "—", "E4"),
    ("F05", "модулі Pololu U106/U107/U108 → пластина", "за отворами модулів Pololu", "TBD (креслення Pololu)", "2",
     "стійки/прокладка до пластини", "TBD — креслення Pololu не прочитані", "—", "ізолювальна шайба під отвір з міддю", "E2"),
    ("F06", "PWR → бобишки корпусу/пластина", "гвинт M3 ISO 14580 A2 TX10 (CNC Kitchen, STACK)", "TBD (CAD)", "2",
     "вставка CNC Kitchen TC-M3x5.7", "TBD — купон (§2)", "CNCK-M3", "—", "E2"),
    ("F07", "RF → пластина (з бондингом NT401)", "гвинт M3 ISO 14580 A2 TX10", "TBD (CAD)", "2",
     "вставка TC-M3x5.7 або стійка до пластини", "TBD — купон (§2)", "CNCK-M3", "зубчаста шайба на голому металі в точці NT401", "E4"),
    ("F08", "CTRL → бобишки корпусу", "гвинт M3 ISO 14580 A2 TX10", "TBD (CAD)", "2", "вставка TC-M3x5.7", "TBD — купон (§2)", "CNCK-M3", "—", "E5"),
    ("F09", "INA228 5832 → стійки над PWR", "гвинт M2.5 + стійка", "TBD (креслення Adafruit)", "2", "стійка M2.5", "TBD", "—", "—", "E2"),
    ("F10", "CH334F 5997 → корпус", "гвинт M2.5 + стійка", "TBD (креслення Adafruit)", "2", "стійка M2.5", "TBD", "—", "—", "E3"),
    ("F11", "IP2368 → стінка корпусу", "кріплення TBD (у плати немає описаних отворів)", "TBD", "—", "стінка ASA", "—", "—", "—", "E2"),
    ("F12", "половини корпусу", "гвинт M3 ISO 14580 A2 TX10", "TBD (CAD)", "4", "вставка TC-M3x5.7", "TBD — купон (§2)", "CNCK-M3",
     "EPDM-шнур у пазу (build/15)", "E9"),
    ("F13", "кришка сервісного лючка", "невипадний гвинт M3", "TBD (CAD)", "2", "вставка TC-M3x5.7", "TBD — купон (§2)", "CNCK-M3", "власна прокладка лючка", "E9"),
    ("F14", "прохідники SMA P1–P3, P6–P8, RX1, RX2, REF IN", "гайка прохідника + кільце + стопорна шайба (STACK §5.8)", "9", "2",
     "стінка 4–5 мм (ASA + 2 мм Al), ≥3 витки для стикування", "за даташитом обраного прохідника; довідково 0.57 N·m (Würth WR-SMA, вимога IP67)",
     "WE-SMA", "стопорна шайба; лиска від провертання", "E6"),
    ("F15", "стикування SMA (нержавіючі)", "—", "—", "—", "—", "0.9 N·m ключем TOJOIN/TekBox; латунні гнізда приладів — пальцями (09 правило 7)",
     "STACK §5.3", "—", "E6"),
    ("F16", "прохідник F (P4)", "гайка прохідника F-F (SAT)", "1", "1", "стінка 4–5 мм", "TBD — SKU не названо (05 §5.1)", "—", "—", "E6"),
    ("F17", "BNC-прохідник (P5)", "гайка BNC", "1", "1", "стінка 4–5 мм", "TBD — SKU не названо (05 §5.1)", "—", "—", "E6"),
    ("F18", "гніздо GX16-4 (J504)", "шестигранна гайка 18.8 мм (Olimex)", "1", "1", "отвір ⌀16 у задній стінці", "TBD — Olimex не публікує момент",
     "OLIMEX-GX16", "—", "E6"),
    ("F19", "LAB BUS M8 (J505)", "гайка M10×0.75 binder 718", "1", "1", "виріз — TBD (сторінка binder без розміру)",
     "гайка — TBD; кільце кабелю від руки ≈50 cN·m", "BINDER-M8", "—", "E6"),
    ("F20", "енкодери PEC11R-4220F (ENC301/302)", "гайка M7×0.75 + шайба (комплект)", "2", "1 запасний енкодер", "бобишка: O-ring + стінка 2.4–3 + шайба 0.5 + гайка 2.0 ≤6.5",
     "≤1.0 N·m (10.2 kgf·cm макс.)", "PEC11R", "шайба з комплекту", "E5"),
    ("F21", "кнопка живлення SW301 (E-Switch PV0)", "гайка M12×0.75 (комплект)", "1", "—", "виріз ⌀12.00 +0.20, панель 1–6 мм", "0.6 N·m", "PV0", "кільце з комплекту", "E5"),
    ("F22", "клапани LTW VENT-PS1YBK-O8002 (×5)", "гайка M12×1.5 (комплект)", "5", "1", "наскрізний отвір у майданчику 2.0–3.5 мм (STACK) ", "0.59–0.78 N·m (6.0–8.0 kgf·cm)",
     "LTW-VENT", "MOLYKOTE 4 — ніколи на силіконові кільця клапанів (STACK)", "E6"),
    ("F23", "гермоввід паку IMU LAPP SKINTOP MS-SC-M12", "гайка-ковпак і контргайка", "1", "1", "отвір 12 мм у стінці Hammond 1550Z101",
     "TBD — інструкція MS-SC-M не прочитана (для MS-M M12 LAPP дає 7–8 N·m — лише орієнтир)", "LAPP-MSM", "—", "E7"),
    ("F24", "кришка паку IMU Hammond 1550Z101", "латунний гвинт M4×20 (STACK §5.8 п. 9)", "4", "2", "корпус Hammond", "TBD — Hammond не прочитано", "—",
     "шов перекрито провідною стрічкою", "E7"),
    ("F25", "штативна гайка 1/4-20 UNC", "захоплена оцинкована гайка 7/16 in AF", "1", "1", "шестигранне гніздо 11.3 AF бобишки ASA 100 %",
     "приймання: момент ≥3 N·m, 20 циклів (тест, не момент затягування)", "STACK §5.8", "—", "E9"),
    ("F26", "бондинг CHASSIS: екран USB-C, корпус GX16, пластина", "кабельний наконечник + гвинт M3", "3", "2", "гола точка пластини (08 крок 5 п. 2)",
     "TBD — купон (§2)", "—", "зубчаста шайба", "E8"),
    ("F27", "вентилятор Noctua NF-A4x10", "кріплення з комплекту Noctua", "4", "—", "задній отвір", "TBD", "—", "—", "E3"),
    ("F28", "повітродувка Delta BFB0305HA-C", "TBD за кресленням Delta", "TBD", "—", "канал дисплея", "TBD", "—", "—", "E5"),
]
INSERTS = [
    ("TC-M3x5.7", "M3", "4.0", "≥1.6", "CNCK-M3"),
    ("TC-M2,5x4", "M2.5", "4.0 (так у лістингу)", "≥1.6", "CNCK-M25"),
]

# --- Power states and test points (build/19) -----------------------------------
STATES = [
    ("B0", "Гола плата без живлення (до і після оплавлення)", "опір до GND, DMM"),
    ("S0", "OFF: джерело на вузлі N 14.8 V, F101 вийнято, S1 вимкнено", "за 08 крок 16 п. 1–2"),
    ("S1", "SW увімкнено, Q6A не під'єднана (J21 без навантаження)", "SYS12/LAB5 без зовнішніх навантажень"),
    ("S2", "Q6A увімкнена: є 3V3_Q6A, усі EN низькі", "до старту labd"),
    ("S3", "DISP12 увімкнено (GP16 = 1)", "дисплей під'єднано"),
    ("S4", "Один EN = 1 (вказаний у рядку), решта 0", "по одному каналу, на навантаженні"),
]
# net -> {state: text}, plus (en net that enables it in S4, source)
TP_EXPECT = {
    "E1_N": ({"S0": "= джерело 14.8 V", "S1": "= джерело", "S2": "= джерело", "S3": "= джерело", "S4": "= джерело"}, None, "02 §2, 08 крок 16"),
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
}

# Staged bench-supply limits for the first power-up of the assembled power chain.
STAGES = [
    ("L0", "S0: лише домен N (AON, INA228, UV)", "0.02", "≤1.0 mA з INA228 у роботі / ≤0.25 mA у shutdown при 14.8 V", "02 §4; 08 крок 16"),
    ("L1", "S1: SW увімкнено, Q6A і модулі LAB5 не під'єднані", "0.30", "записати (струм холостого ходу перетворювачів)", "уставка asm, обмежує енергію КЗ"),
    ("L2", "S2: Q6A (без Lime, без SDR)", "1.50", "J21 0.35–1.3 A при 12 V (модель)", "02 §2"),
    ("L3", "S3: + дисплей", "3.00", "DISP12 0.25 / 1.1 A (модель)", "02 §2"),
    ("L4", "Повна збірка з Lime (режими H/I)", "5.00", "до 4.6 A на піку (модель)", "02 §2–3; нижче F101 7.5 A"),
]
SHORT_LIMIT_OHM = 10  # bare-board criterion (рішення asm): below this a rail is treated as shorted

# --- Superseded v2 tokens that must not appear in build/02, 04, 08 outside a historic clause
STALE = [
    (r"D36V28F5", "LAB5 — D36V50F5 #4091 (v2.1)"),
    (r"F3 3 A|запобіжник 3 A LAB5|3 A \(0297003", "запобіжник LAB5 — 4 A (v2.1)"),
    (r"повітродувка 5 V 5015|5015 \(", "повітродувка — Delta BFB0305HA-C (E3-03)"),
    (r"GP17 \| димінг|STACK\.md 5\.2 GP17", "GP17 — reset MCP (E3-review)"),
]
HISTORIC_MARK = "історичн"

# --- Assembly order (build/21) --------------------------------------------------
# Each step: id, title, actions (list), refs (segments, fasteners, labels)
STEPS = [
    # id, title, parts, actions, checks, refs (segments S.., fasteners F.., labels L.., assemblies C-..)
    ("E0", "Підготовка і друк",
     "друковані деталі ASA (§1), термовставки TC-M3x5.7 / TC-M2,5x4, купон з тієї самої котушки",
     ["Робоче місце, ESD і безпека — за 08 крок 0; літієвий пак не під'єднано, F101 вийнято і лежить окремо.",
      "Надрукувати деталі за таблицею §1; дати охолонути до кімнатної температури.",
      "Купон: одна бобишка з кожним типом вставки; задати робочий момент за 17 §2 і записати в бланк 20.",
      "Вставки в корпус — за 17 §3, по одній, торець урівень із бобишкою."],
     ["вставки не провертаються робочим моментом купона", "торець вставки урівень, без напливів пластику в різьбі"],
     ["F06", "F08", "F12", "F13"]),
    ("E1", "Плати на столі",
     "плати PWR, RF, CTRL після оплавлення (лише верхній бік, build/15)",
     ["Перевірка B0: опір кожної шини до GND за 19 §2 до і після оплавлення.",
      "Запуск кожної плати окремо за 19 §4 зі ступенями L0–L1 (19 §5).",
      "Обжати джгути S02, S03, S04 за 16 §1 (інструмент Molex 0638190000 для Micro-Fit); маркер з ID проводу на обох кінцях (L-WIRE)."],
     ["жодна шина < 10 Ω до GND", "стани S0–S1 за 19 §3", "прозвонка кожного проводу джгута від маркера до маркера"],
     ["S02", "S03", "S04", "L-WIRE", "L-CONN"]),
    ("E2", "Збірка середньої пластини (на столі, поза корпусом)",
     "пластина 2 мм EN AW-5754 (08 крок 5), D36V50F12, D36V50F5, #2813, INA228 5832, PWR, F101 (вийнятий)",
     ["Модулі Pololu U106/U107/U108 — на пластину через ізолювальні прокладки (F05); PWR — на стійки (F06).",
      "INA228 — на стійки над PWR (F09); джгути S05–S09, S12, S13 — до роз'ємів PWR; кінці S05 і S12 ізолювати, поки пак не встановлено.",
      "Стенд на TP104 при вийнятому F101: ступінь L0, потім кнопка — L1 (19 §5)."],
     ["TP104/TP105/TP106/TP108 за станами S0–S1 (19 §3)", "струм L0 ≤1.0 mA при 14.8 V"],
     ["F05", "F06", "F09", "S05", "S06", "S07", "S08", "S09", "S12", "S13"]),
    ("E3", "Q6A, Lime, охолодження і хаб на пластині",
     "Q6A (прогнаний за 08 крок 1), охолоджувач A або B, Noctua NF-A4x10, CH334F 5997, R44SF + Lime на п'єдесталі",
     ["Q6A — на стійки M2.5 (F01/F02); охолоджувач — за 08 крок 6 (F03 для Armor).",
      "П'єдестал Lime (F04) з прокладкою; riser крізь вікно; кабель C-PCIE; LIME3V3 S18 — лише після прозвонки ізоляції 3.3 V картки (E5 §10).",
      "Відвід VCC_3V3_MKEY S17 — лише після локалізації точки на Q6A (16 §11); до того LIME3V3 не живити.",
      "Хаб (F10), кабель C-HUB; Noctua (F27) з кабелем S27.",
      "J21: до прогону — заводський кабель; після прогону — S16 пайкою до майданчиків J21 (08 крок 7.7)."],
     ["S2 за 19 §3 з Q6A на J21 (ступінь L2)", "lsusb бачить хаб; Noctua обертається; тахо на GP22"],
     ["F01", "F02", "F03", "F04", "F10", "F27", "S17", "S18", "S27", "S16", "C-PCIE", "C-HUB"]),
    ("E4", "РЧ-відсік на пластині",
     "RF-плата, модулі РЧ-тракту (Flamingo+, SAWbird+, атенюатор LNB), RTL-A/B на подовжувачах, HF+ в екрані Schubert 6B, bias-tee Boni, G6K",
     ["RF-плата на пластину з бондингом NT401 (F07, зубчаста шайба на голій точці).",
      "Модулі РЧ-тракту і коаксіальні з'єднання — за 16 §8; ключ 0.9 N·m лише для нержавіючих SMA (F15).",
      "RTL-A/B: кабелі C-RTLA/C-RTLB і VBUS S20/S21; HF+: C-HFP і S22 з двома феритами на повному кабелі; Boni: S35.",
      "Джгути S03/S04 з E1 — під'єднати; укласти вздовж пластини, подалі від буферних дроселів."],
     ["HMC7992 у RF1 при ввімкненні (08 крок 9)", "котушки G6K знеструмлені", "розрив центр–корпус на кожному SMA з вимкненим зміщенням"],
     ["F07", "F15", "S03", "S04", "S20", "S21", "S22", "S35", "C-RTLA", "C-RTLB", "C-HFP", "L-LABRXA", "L-LABRXB",
      "L-LIME-X2", "L-LIME-X4", "L-LIME-J4", "L-LIME-X1"]),
    ("E5", "Передня половина: дисплей і HMI",
     "передня половина корпусу, Wisecoco + рамка, CTRL, енкодери PEC11R-4220F, кнопка PV0, VEML7700, повітродувка Delta",
     ["Дисплей у рамку (параметрична модель; клей/фіксація — TBD за пакетом механіки), козирок і L-SUN.",
      "CTRL на бобишки (F08); вали енкодерів вкоротити до встановлення (08 крок 12); гайки енкодерів ≤1.0 N·m (F20); PV0 — 0.6 N·m (F21).",
      "VEML7700 на верхній грані безеля (S26); повітродувка в канал дисплея (F28, S28).",
      "Кабелі CTRL: S01 (≤200 мм), S24, S25 (PPS разом з S01 ≤200 мм), S29, S30 — заготовити з запасом петлі."],
     ["кнопки й енкодери працюють на стенді через S01 (19 §4 п. 2)", "ручки не торкаються гайок"],
     ["F08", "F20", "F21", "F28", "S01", "S24", "S25", "S26", "S28", "S29", "L-SUN", "L-RX"]),
    ("E6", "Пластина в передню половину",
     "збірка середньої пластини (E2–E4), передня половина (E5)",
     ["Встановити пластину на бобишки передньої половини; дисплей — до пластини з каналом повітря 4–6 мм.",
      "HDMI C-HDMI: пласка S-складка, ферити в кишенях 40×20×20, подалі від РЧ-відсіку і фідера GNSS; touch C-TOUCH.",
      "DISP12 S19 з наклейкою L-DISP12; S02 CTRL ↔ PWR; S01 Q6A ↔ CTRL; S24 до вставки T7 у C-T7.",
      "Стяжки до пластини ≤30 мм від кожного роз'єму і далі кожні 50–80 мм (16 §1)."],
     ["S2 і S3 за 19 §3 (ступінь L3)", "touch енумерується без VBUS (E5 §8)"],
     ["S19", "S02", "S01", "S24", "C-HDMI", "C-TOUCH", "C-T7", "L-DISP12"]),
    ("E7", "Задня половина: панелі, лючок, батарейний відсік",
     "задня половина, прохідники SMA/F/BNC, GX16-4, LAB BUS M8, USB-C, LAB USB-A, гермоввід T7, клапани LTW, гайка 1/4-20",
     ["Прохідники SMA (F14), F (F16), BNC (F17) — у верхню стінку/смугу; ≥3 витки для стикування.",
      "GX16-4 (F18), LAB BUS M8 (F19), USB-C, LAB USB-A, клапани LTW (F22), захоплена гайка 1/4-20 (F25).",
      "Джгути S11 (USB-C), S23 + C-LAB (LAB USB-A), S32 (GX16), S34 (LAB BUS), S36 (ввід pod — TBD).",
      "Сервісний лючок: J503 (S14 + S15), J502 (S30), SW501 (S31), синій USB-A; наклейки L-HATCH, L-J21.",
      "IP2368 на стінку ≥10 мм від елементів (F11), джгут S10; KSD9700 на MOSFET через поліімід (08 крок 3).",
      "Батарейний відсік: піна 3 мм, відбивна плівка, бар'єр; пак з L-BAT; S05 — під'єднати останнім, F101 ще вийнятий."],
     ["оплітка GX16 — корпус ≤0.1 Ω", "розрив між J503 і J502 (різні родини, не стикуються)", "наклейки за 18"],
     ["F14", "F16", "F17", "F18", "F19", "F22", "F25", "S11", "S23", "S32", "S34", "S36", "S14", "S15", "S30", "S31",
      "S10", "F11", "C-LAB", "L-HATCH", "L-J21", "L-BAT", "L-USBC", "L-LABUSB", "L-LABBUS", "L-AUDIO", "L-T7", "L-IMU", "L-F101"]
     + ["L-" + _ref for _ref in PORT_LABELS]),
    ("E8", "Пак IMU і зовнішній кабель",
     "Hammond 1550Z101, носійна частина паку (U552, D502, C519, C520, деталі E3 «External IMU»), RP2040-Zero, BNO085, SKINTOP MS-SC-M12, кабель HELU 49655 2 м",
     ["Плати в корпус паку; гермоввід (F23) на стінці, найдальшій від BNO085.",
      "Кабель S33: оплітка 360° у SKINTOP і обтиснута в GX16; кришка латунними M4 (F24), шов — провідна стрічка."],
     ["оплітка — корпус паку і GX16 ≤0.1 Ω", "1e6 кадрів IMU без CRC-помилок (E5 §10 п. 8)"],
     ["F23", "F24", "S33"]),
    ("E9", "Бондинг, перевірка і закриття",
     "EPDM-шнур, гвинти половин F12, кришка лючка F13",
     ["Бондинг CHASSIS за 16 §9 (F26).",
      "Перевірка перед закриттям — 19 §6; бланк 20.",
      "EPDM-шнур у паз без розтягу, стик — на прямій ділянці; половини — гвинти хрест-навхрест у два проходи (F12); кришка лючка (F13).",
      "Вставити F101 лише після 19 §5 ступенів L0–L3 від стенду; далі перше ввімкнення від паку за 08 крок 16."],
     ["шнур не виступає з пазу", "S0–S4 за 19 §3 на закритому корпусі", "тест штативної гайки ≥3 N·m (F25)"],
     ["F26", "F12", "F13"]),
]

# Printed parts (table in build/21 §1); geometry belongs to the mechanical package.
PRINTS = [
    ("корпус: передня половина", "лицем на стіл", "≥4 периметри у бобишках вставок і гайки 1/4-20; бобишка гайки — 100 % (STACK §5.8)", "лише під навислими вирізами портів"),
    ("корпус: задня половина", "внутрішньою стороною вгору", "як вище", "під прорізами ременя"),
    ("верхня смуга під Lime", "довгим боком на стіл", "≥4 периметри навколо прохідників", "ні"),
    ("козирок 30 мм (шарнірний)", "пласко", "3 периметри (PIS)", "ні"),
    ("рамка дисплея (параметрична)", "лицем на стіл", "3 периметри (PIS)", "ні"),
    ("тримач T7", "пласко", "3 периметри (PIS)", "ні"),
]
