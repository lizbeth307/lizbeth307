# Ворота приймання SR-RX-v2.1

Жоден стендовий тест не виконано. `OPEN` не означає, що виявлено несправність конкретного екземпляра: це умова, без підтвердження якої його не можна приймати чи підключати. Стан апаратного випуску — **BLOCKED**.

Основні інструкції українською наведено в аудитах [E1](design/E1-review.md), [E2](design/E2-review.md), [E3](design/E3-review.md), [E4](design/E4-review.md), [E5](design/E5-review.md) та [таблицях монтажу](design/E5-connection-guide.md). Нижче — повний реєстр ідентифікаторів із машинного контракту.

## E1-01 — OPEN / блокує випуск

Ревізія COUT і місця NTC/VSET/ISET/ISET_MODE/CELLSET не підтверджені офіційною схемою. Вікно 0…45 °C та inhibit не перевірені.

**Умова закриття:** До модифікацій отримати ревізійну схему або фото обох боків з continuity до IC. Стенд: NTC 0/45 °C, обрив/КЗ, зупинка charge і reverse boost, 2 h при 3 A, 20 PD cycles, зовнішній VBUS=0 V, startup 5→20 V, CV кожної комірки. При провалі цей модуль не використовувати; ISDT лише після E1-02.

## E1-02 — OPEN / блокує випуск

Balance B0 = raw B− може шунтувати Daly через спільну землю ISDT 608PD і пропускати силовий струм по тонкому sense-дроту.

**Умова закриття:** J102 позначено DNP/service-only; місячний баланс ISDT вимкнути до затвердженого інтерфейсу. До підключення перевірити DMM ізоляцію output−/balance B0 ISDT без живлення та отримати принципову схему виробника. При спільній землі потрібне перепроєктування з явним аналізом усіх струмових шляхів і незалежним захистом; ані main OFF, ані 5 A fuse не доводять безпеку. Не виправляти перенесенням B0→P− чи XT30−→raw B−. Внутрішній sense harness Daly лишається. Див. design/charger-bms-review.md. Низька continuity є reject; високий опір без живлення не є pass, бо стан може змінитися при роботі чи через USB. Для закриття потрібне підтвердження топології виробником або redesign із fault validation відсічки BMS в усіх струмових шляхах.

## E1-03 — OPEN / блокує випуск

Фізичний PHB2.0 pin order Daly та ревізія J05G/J04G3 нез’ясовані.

**Умова закриття:** На прийманні звірити маркування з Daly DS саме цієї ревізії. Продзвонити B0…B4 зі знятим sense-штекером; послідовні напруги 3…4.2 V, сумарно 4S. Пробудження зарядником 3/3. До цього підключення sense заборонене.

## E1-04 — OPEN / блокує випуск

UV ±0.1 V потребує індивідуальної калібровки; held OFF проти кнопки, старт SYS12 після release і порядок із програмною відсічкою E3-07 ще не перевірені.

**Умова закриття:** До батареї current-limited sweep 14→12→14 V при 25 і 50 °C: trip 12.8±0.1 V, release 13.6±0.1 V, drift≤50 mV. Калібрувати R105. AON без INA ≤11 µA. Утримуванням кнопки не можна обійти UV. 20 PD cycles без самозапуску. При провалі fallback TLV3012 із нижнім плечем 346.04 kΩ і повним повтором тесту. Після UV release (13.5…13.7 V у спокої) одне натискання кнопки мусить одразу дати E1_PG_SYS12 без подальшого заряду — з реальним пусковим навантаженням (LAB5 з примусово ввімкненими вентиляторами, старт Q6A) при 25 і 50 °C, без повторного UV trip і без циклу програмної відсічки 13.05 V; інакше E1-04 не пройдено. v2.1, рішення власника: EN-резерв SYS12 R108 4.99k / R109 562R 0.1% 25 ppm/K, UV-мережа R103–R107 без змін; wake ≤13.27 V на E1_SW навіть за внутрішніх 100 kΩ ±20% і припущених ±3% порога EN. Порядок release > wake + спад E1_N→E1_SW (≈0.06 V) чинний, доки фактичний поріг EN наростання не більш як на 4.3% вище 1.35 V; його вимірює Ж-03 (wake >13.30 V → R109 576R і повторна розгортка; після перепаювання wake ≤13.30 V і sleep ≥10.9 V, інакше reject). Резервний sleep 10.9…11.8 V нижче точки стабільності Q6A 11.5 V: при відмові UV і Pico резерв уже не знімає SYS12 до просідання Q6A, тож основним відсіченням лишається UV trip U104. Якщо кнопка на піні A обходить утримуваний OFF, SYS12 тепер стартує вже від ≈12.2…13.3 V — тоді кнопку вести через супервізор. Симуляція відмови UV (вихід компаратора примусово low): резерв знімає SYS12 при 10.9…11.8 V без циклів sleep/wake. Порядок порогів на кожному екземплярі, разом з E3-07: за максимального й мінімального навантаження виміряна програмна відсічка, приведена до E1_N (13.05±0.1 V), мінус виміряний тут trip ≥0.10 V, а під час контрольованого розряду graceful shutdown (5 s dwell + завершення Linux) завершується до апаратного UV trip. Інакше — повторний trim R105 або reject.

## E1-05 — OPEN / блокує випуск

Default LAB5: D36V50F5 +4 A fuse; конкретні parts фільтра обрані. Агрегатний струм, converter/filter stability, температура і напруги на кінцевих навантаженнях не підтверджені.

**Умова закриття:** U108 D36V50F5 #4091; F102 4 A; L101 XAL6060-103MEC; C111/C112 35SVPF22M; C113 16SVPC100M; R110 WSL2512R3300FEA. Звірити площу, висоту і land patterns. Виміряти всі режими: LAB5 ≤3.2 A continuous; blower reserve 0.25 A continuous /0.50 A startup; SB_LNA 65 mA враховувати один раз у I_ANT≤1 A. Додаткова policy: I_ANT+0.83 A×EN_LAB≤1.5 A. За 5 V та 0…50 °C підтвердити C111/C112 effective ≥10 µF; C113 початково ≥80 µF; step 10…90% без осциляцій; 5 V±5% на КОЖНОМУ пристрої після switch/кабелю. Термо 30 min при 3.2 A і середовищі 50 °C; до 4 A transient із логом запобіжника та пульсацій. Вихід модуля 5 V±4% та drop L101 не гарантують USB 4.75 V у всіх допусках: low unit відбракувати або переробити живлення. Пара LT3045 (E2-04, v2.1 VSET 4.30 V) окремої вимоги до LAB5 не має: її приймання — виміряний V(E2_LNA_IN)−V(OUTS) ≥0.40 V при 3.2 A LAB5 / 1 A пари / 50 °C. Відкрито: MPN F102 з холодним опором ≤10 mΩ і опір з'єднання LAB5 E1→E2 ≤10 mΩ (кожні 10 mΩ — 32 mV при 3.2 A). Якщо actual сума перевищує бюджет — формальний concurrency cap/rail redesign із повтором тестів.

## E1-06 — OPEN / блокує випуск

Термо, transient, ESD та узгодження захистів не доведені на реальному PCB.

**Умова закриття:** Силова плата reflow. Перевірити USB-PD OVLO≈22 V, ILIM≈3.5 A, hot-plug 0→20 V і reverse blocking. TVS E1_SW не вважати гарантією захисту 28 V eFuse. SYS12: C4 RF A/B і 60 min при 4.2 A, входи 14/16.4 V; батарейний шлях 4.6 A при case 50 °C. Перед виготовленням PCB потрібні layout, ERC і DRC.

## E1-07 — OPEN / блокує випуск

USB-C feedthrough, XT30 та BMS мають функціональні контакти; механічні parts і land patterns не задано.

**Умова закриття:** Перед PCB вибрати конкретні частини, відобразити їхні фізичні контакти на functional nets і незалежно перевірити pin mapping. Ця JSON описує схему, а не Gerber.

## E2-01 — OPEN / блокує випуск

MPN L/C і діодів обрані. Ефективна ємність, ESR/ESL, демпфування LC та від’ємний викид OUT залежать від розведення і реальних деталей.

**Умова закриття:** Перевірити COUT ≥10uF при робочому bias/температурі, ESR LT3045 <20mR і ESL <2nH; виконати тести ступінчастого навантаження, RF-шуму та від’ємного OUT ≥−0.4V.

## E2-02 — OPEN / блокує випуск

Статичне вікно OVP LNB закрито TPS3701: 13.56–13.96V. Швидкий викид при відмові LDO не обмежено гарантованим максимальним часом у даташитах: 9.9µs компаратора і близько 12µs EN-off eFuse задані лише типово.

**Умова закриття:** Без LNB і зі струмовим обмеженням подати на вузол LDO контрольований стрибок 13.2→16.4V; осцилографувати F-вихід при мін./макс. навантаженні, на холоді й при 50°C. Отримати граничні імпульсні параметри Bullseye; якщо потрібно, додати швидке відсікання/обмеження з гарантованим часом.

## E2-03 — OPEN / блокує випуск

Остаточні ILIM і пускові струми RTL-B, Lime, LNB, Boni та LaNA WB потребують натурних вимірів; ємність riser і комерційних модулів не опублікована. Поріг OVLO Boni (R263/R264, стартовий розрахунок 112k/10.0k) STACK §5.1 вимагає перерахувати для 13.8 V; на стенді його не перевірено.

**Умова закриття:** FNB58/INA228/INA3221: 20 холодних і теплих пусків, струми стримінгу, КЗ і SOA. Установити ILIM 1.5–2× виміряного струму з допусками. Boni (v2.1, R-E2-19): RILM 7.15k 1% ≤100 ppm/K → ILIM 0.122…0.153 A (0.1215…0.154 A з TCR) проти найгіршого сталого ≈79.7 mA (Boni 65 mA тип. + bleed E4 до 14.35 mA + R283/R284 і DCS tap), тобто 1.53…1.92×; з блокувальним елементом E4-06 (+≈1.6 mA) ≈81.3 mA і 1.5× = 0.122 A — на межі ILIM min. Після HF-9 (струм Boni-Whip холодним і гарячим при 13.8 і 14.1 V) перерахувати RILM = 903/(ILIM−0.0112): ILIM min ≥1.5×, ILIM max ≤ min(2×, DC-рейтинг bias-tee ≥0.16 A). Електронне навантаження на BONI13V8 при 13.8 V: спрацювання в межах 0.122…0.153 A, поведінка понад TA 80 °C. Тверде КЗ на P5 при ввімкненому bias (v2.1, Q2903 послідовно): пара Q2903 самозміщується біля VGS(th) і тримає BONI13V8 на ≈1.2…4.4 V; струм U214 — між foldback ≈0.09…0.115 A (Figure 22, VOUT = 0) і ILIM, U214 ≈0.9…1.9 W, Q2903 ≈0.1…0.7 W у лінійному режимі; FLT мовчить — записати BONI13V8, струм, температуру корпусу Q2903 і поведінку U214 (обмеження чи TSD) до зняття EN_BONI та підтвердити, що labd знімає EN_BONI за min_voltage_v і PG_BONI ≤2 s. Межа labd 0.113 A не змінюється. Загальний LAB5 тестується за новими воротами E1 для D36V50F5 + запобіжник 4A; старі 2.5A не є лімітом default-збірки. OVLO Boni (STACK §8.1 HF-8/RF-5): без Boni-Whip і зі струмовим обмеженням — повільна розгортка вузла E2_BONI_LDO (вхід eFuse U214) 13.8→15.5→13.8 V, записати пороги спрацювання й відпускання; OVLO не спрацьовує в смузі 13.8 V, поріг вище 14.145 V (макс. LDO) і нижче 15 V (межа Boni). Поза вікном — перерахувати R263/R264 і повторити.

## E2-04 — OPEN / блокує випуск

v2.1, рішення власника (R-E2-18): R227 21.5k задає LNA4V5 4.30V (4.208…4.392V). Запас на папері: LAB5 min 4.80V (5V−4%) − 3.2A×29.8mΩ L101 − 1A×9.4mΩ L205 = 4.695V на E2_LNA_IN, тобто 0.395V над VSET: +135mV проти типового dropout 260mV (500mA на ІС), +45mV проти 350mV max при 25°C, −55mV проти 450mV max у повному діапазоні температур — ще до F102 і з'єднання E1→E2 (кожні 10mΩ — −32mV при 3.2A). Близько 0.4V — коліно PSRR. Розподіл струму й температура не підтверджені. Сума індивідуальних номінальних ILIM LNA більша за 1A пари.

**Умова закриття:** Перевірити LAB5 min, навантаження пари до 1A, температуру кожного LT3045 та спад до антени. Дотримуватися контракту R-E2-17: сума INA LNA1–4 + резерв 65mA S-band ≤1A; разом із резервом LAB-порту ≤1.5A. Приймання: при 3.2A LAB5, 1A на пару і 50°C виміряти E2_LNA_IN, OUTS і LNA4V5; вимога — виміряний V(E2_LNA_IN)−V(OUTS) ≥0.40V, LNA4V5 на TP205 4.19…4.39V при 1A пари (VSET 4.208…4.392V мінус до 12mV на баласті 20mΩ при 600mA); пульсації та спури 500kHz…2MHz на портах LNA при 0.17A і 0.6A. Окремої вимоги LAB5 ≥4.90V для E2-04 немає; E1-05 лишає відбір low LAB5 для USB. Відкрито: MPN F102 з холодним опором ≤10mΩ і з'єднання E1→E2 ≤10mΩ. Кожен LNA має працювати при зниженому зміщенні: найгірше ≈3.95V на LNA (≥0.45V над 3.5V Uputronics 440); базові струми INA3221 (RF-3) переміряти при 4.3V. Невиконання — reject модуля LAB5 або перепроєктування рейки.

## E2-05 — OPEN / блокує випуск

Відсутність фантомного живлення Q6A, вимкнення дисплея та фізична правильність кінцевих кабелів потребують перевірки з реальним обладнанням.

**Умова закриття:** За активної LAB5 і вимкненої Q6A: 3V3_Q6A та upstream VBUS близько 0V, PICO_DISP_EN низький. Продзвонити розрізаний VBUS, ключовані роз’єми E3/E5 та сигнал PWR_ON_KEY. UVLO J21 (v2.1, R202 13.0k): джерело з обмеженням струму на E2_J21_FUSED, Q6A або e-load на J21, повільна розгортка 0→12.5→0 V при 25 і 50 °C — увімкнення 10.09…10.83 V, вимкнення 9.18…9.88 V (з TCR 9.99…10.95 / 9.08…9.99 V), без брязкоту OUT/FLT під час пуску; кроки навантаження SYS12 0.3→3 A при SYS12 = 11.0 V і біля UV trip — мінімум E2_J21_FUSED вище виміряного порога вимкнення, без FLT і скидання Q6A. Спрацювання UVLO вимикає Q6A, і Pico через 3 s відкриває #2813 (засувка OFF, перезапуск лише кнопкою при ≥13.6 V) — очікувана поведінка. Імпульс Pico на PWR_ON_KEY не реалізований (firmware/pico/supervisor.py тримає q6a_key=False): B11 (автостарт, імпульс 20/20) спершу потребує доробки прошивки — відкритий пункт.

## E3-01 — OPEN / блокує випуск

IMU assembly and two metre single-ended UART need bench verification. Internal named-pad wiring is specified, but no physical harness has been measured.

**Умова закриття:** Check actual module revision, GX16 plug/socket viewing direction and continuity to E5 design pinout; validate input Schottky and TVS at both ends; 1e6 frames with zero CRC errors. Upgrade to differential interface if errors occur.

## E3-02 — OPEN / блокує випуск

Brightness control requires confirmed DDC/CI support or an exact Wisecoco KEY/Backlight interface. Pico GP17 is now reserved for MCP watchdog reset and unavailable for brightness.

**Умова закриття:** Demonstrate ddcutil brightness through the specified RA620 link, or obtain the exact KEY/Backlight revision pinout and design a new interface using a free MCP GPIO if suitable. Verify thermal dimming; do not reuse Pico GP17.

## E3-03 — OPEN / блокує випуск

BOM candidate Delta BFB0305HA-C is selected; final mechanical fit, installed airflow, start/stall current, LAB5 concurrency and noise remain unqualified.

**Умова закриття:** Fit the body envelope 30.5x30.5x10.5 mm plus duct/lead clearance into CAD before cutting the enclosure. Measure the 0.25 A design continuous reserve and the provisional 0.50 A startup limit rather than claiming peak from the datasheet. Confirm LAB5 within E1-05 (<=3.2 A continuous, <=4 A transient with default D36V50F5 + F102 4 A) in allowed concurrency; over budget means a formal concurrency cap per R-E2-17. Run the 45 min closed-cover solar thermal test and RF A/B noise checks; inlet drop <=5 Pa at the required flow.

## E3-04 — OPEN / блокує випуск

UM3304 UART7/PPS/SWD cable capacitance and power-off behavior cannot be proven by ERC.

**Умова закриття:** Check <=20cm wiring, UART7 loopback, boot glitches and absence of Q6A backfeed with Pico on/Q6A off. Verify TX high-impedance sequencing or add hardware isolation.

## E3-05 — OPEN / блокує випуск

Shared MCP interrupt requires open-drain configuration before interrupts are enabled, plus measured I2C rise time and VOL.

**Умова закриття:** Set ODR=1 and MIRROR=1 first. Validate 100kHz, rise <=1000ns, 1e6 reads under load, 20 cold/20 warm boots, and 10us FAULT capture.

## E3-06 — OPEN / блокує випуск

BOM candidate Semiware MF52A103F3950 is selected for both NTCs; purchased-lot curve, attachment, lag and installed calibration remain unqualified.

**Умова закриття:** Verify 10k +/-1% at 25 C and manufacturer B25/50 = 3950 +/-1%; use the exact maker R/T table. Fit an insulated bead/strain relief on the panel spreader and frame, check 25/60/68 C against a reference thermometer, qualify lag and open/short/stale fail-safe behavior. Remain inside the -20..120 C sensor range.

## E3-07 — OPEN / блокує випуск

Battery ADC shutdown accuracy must be calibrated. Divider/reference initial tolerances can contribute about +/-0.28 V near 13.05 V; a nominal ADC code does not establish the 13.05 +/-0.1 V cutoff. The software window 12.95-13.15 V must stay above the E1-04 hardware AON UV trip window 12.8 +/-0.1 V on every unit.

**Умова закриття:** Calibrate gain/offset against a calibrated voltmeter at two pack-equivalent voltages such as 12.6 V and 16.4 V; cross-check INA228. Independently verify the physical 13.05 V software cutoff (labd and Pico fallback both 13050 mV) within +/-0.1 V, including 5 s dwell, at 12.95/13.05/13.15 V across the specified temperature and load states. Per unit, at maximum and minimum load: the measured software cutoff referred to E1_N minus the measured E1-04 hardware trip must be >=0.10 V, and during a controlled discharge the graceful shutdown (5 s dwell plus Linux shutdown) must complete before the hardware UV trip asserts OFF; otherwise re-trim or reject. Store calibrated coefficients with revision/CRC. No commissioning pass until met; the hardware AON UV supervisor remains an independent backup.

## E3-08 — OPEN / блокує випуск

Pico watchdog, MicroPython GPIO/UART adapter and host handshake implemented 20.10.2026 and tested on the host. Actual GPIO timing, reset levels, WDT/brownout behavior and Linux/serial fault recovery have not been qualified on the device.

**Умова закриття:** Run the implemented firmware with the actual accepted Pico/Q6A assembly: scope MCP RESET assertion/release, safe output image including CHG_INHIBIT=1 after initialization, 100ms guard, 750ms heartbeat deadline plus measured latency, explicit fresh-session recovery, Linux kill/hang, UART loss/corruption, WDT/brownout and GPIO current/backfeed. Complete Pico power loss with Q6A alive remains outside Q306 coverage; no software test closes this boundary.

## E4-01 — OPEN / блокує випуск

ch1–3 injector choke part selection is complete; final DC drop, thermal rise, RF impedance and footprint qualification remain open. Optional static bleeds stay DNP.

**Умова закриття:** Verify selected 0805LS-471XGRC / 0805HP-221XGRC / 0603HP-47NXGRW manufacturer land patterns and target-band impedance under bias. VNA qualify IL/RL/isolation and DC heating at actual/worst protected current. The current Coilcraft 0603HP PDF confirms the 2.3 GHz typical SRF; no documentary SRF question remains. L401/L407 stay optional DNP until separately qualified.

## E4-03 — OPEN / блокує випуск

Boni supplied bias-tee port labels, DC socket polarity and receiver DC block require actual hardware.

**Умова закриття:** Measure continuity/polarity, antenna DC and RADIO port <0.1 V before connecting HF+. v2.1: A406 DC is BONI13V8_PORT behind the E2 blocking element Q2903 — confirm on the supplied Einspeiseweiche a DC current rating ≥0.16 A (ILIM max 0.153 A, 0.154 A with TCR, RILM 7.15k) and DC-block/choke voltage ratings ≥30 V; otherwise use the homemade 2.2 mH bias-tee with a choke Irms and Isat ≥0.20 A and count its DCR in the 12.0 V barrel gate.

## E4-04 — OPEN / блокує випуск

S-band module and supply selection are complete; external inline pod assembly, cable loss, gain/NF and thermal/current measurements remain unqualified.

**Умова закриття:** Build the specified LaNA WB 100845 + cf2235 + DC blocks in the Hammond 1554U2GY pod; verify stacked fit/cable bends, weather seals and strain relief. Measure LaNA current/inrush at protected 5 V, 2.2–2.3 GHz S21/NF/linearity, and receiver protection. Do not substitute generic nominal NF for the actual S-band measurement.

## E4-05 — OPEN / блокує випуск

Lime X2/X4 are the v1.2 RX ports, but which of them is RX-A and which RX-B is TBD (STACK §2.11.1, §8.1 L-12: check against the board marking). Pins are named X2_RX/X4_RX and nets E4_LIME_X2_RX/E4_LIME_X4_RX, so the drawing fixes no channel; supplied-board cable labels need confirmation.

**Умова закриття:** Check the exact revision schematic and conduct a one-port-at-a-time RX test. Generic setup X3 wording is not evidence.

## E4-06 — OPEN / блокує випуск

Three concrete protected bipolar DC-window detectors are designed; threshold, RF loading and power-off backfeed still need prototype qualification. v2.1 (owner decision): each sensed bias branch has an E2 back-to-back P-MOSFET blocking element (Q2901/Q2902/Q2903 DMP6050SSD-13 with a 100 nF gate-source capacitor, held open by low EN_LNA2/EN_LNA3/EN_BONI) between the protected E2 node (TPS2553/INA3221/U214, polarized capacitors) and the E4 port node; ±30 V at the assembled port is a design target until bench-proven.

**Умова закриття:** Verify each DCS LOW at 0 V and HIGH by ±0.100 V in both sweep directions over the admitted temperature/supply range; record thresholds/hysteresis. With own bias OFF and Q6A ON/OFF (3V3_Q6A <0.1 V when OFF), apply foreign DC at each assembled port P2/P3/HF_CM: (1) slow ±30 V limited DC; (2) fast-edge hot plug — a pre-energised current-limited ±12/±24/±30 V source switched onto the port through a coax plug or relay. Pass: BIAS_CH2/BIAS_CH3/BONI13V8 (TPS2553 OUT, INA3221 inputs, U214 OUT) stay within −0.3…+0.3 V, no INA/MCP fault; repeat at 0 °C and 50 °C. The DPS-150 cannot reach 30 V from the project's 20 V PD or 4S sources; use a source that really delivers 30 V. Hot plug while own bias is ON is not covered and must not be tested destructively. Also measure off-state leakage (protected-node rise <0.1 V at 50 °C), the on-state drop at 184.5/54.5/80 mA including the cold VGS(th) corner (VGS ≈−4.2 V on the 4.30 V rail; total ≤0.25 V to the antenna), turn-on with and without trapped charge (the ≈48 µF protected reservoir dumps into the port outside the TPS2553/U214 limit) and unchanged soft-start/ILIM. A shorted FET is not detectable; an open element on LNA2/LNA3 is silent. Measure RF tap and element IL/RL/NF impact. Require startup/reference-fault HIGH and own bias OFF ≥500 ms before preflight; readiness stays false until qualified. Check floating/open antenna as well as 0 Ω/50 Ω DC loads. Include the 996 Ω bleed load in current baselines and measure its RF loss/parasitics. Reject false-safe at ±0.100 V; false-unsafe units also fail usability qualification. Also qualify cold minimum-supply reference-feed headroom: the arithmetic model requires D450 Vf ≤1.015 V at VDD 3.135 V and REF 2.072 V for at least 80 µA LM4040 cathode current. Reference collapse must force HIGH, and must not be misreported as a working detector.

## E4-07 — OPEN / блокує випуск

RF PCB, relay insertion loss, isolation, return loss and startup PARK are unmeasured.

**Умова закриття:** VNA: HF selector 10 kHz–260 MHz IL ≤0.3 dB, RL ≥21 dB, isolation ≥35 dB at 162–260 MHz plus STACK LF/HF gates. HMC ≥40 dB isolation at 0.1–1.7 GHz (37–40 dB conditional and recorded); verify all DC blocks and startup. Check all SMT footprint pad numbers, dimensions, orientation and ground/exposed-pad implementation against the now-verified manufacturer maps.

## E4-08 — OPEN / блокує випуск

RX1 captive edge/pad/panel assembly and H1 attenuation have not been measured.

**Умова закриття:** Confirm edge → pad → panel → X2 without bypass. YAT 10±0.5 dB and RL ≥20 dB; H1 total ≥12.0 dB at 1420 MHz, using 3 dB pad if the 2 dB pad fails.

## E4-09 — умова окремої опції

BENCH RF sled is not delivered as a separate HMC7992 + PE4312 PCB here.

**Умова закриття:** Deliver its PCB/netlist, controls and 31.5 dB startup test if installed. Until then use the internal BENCH SMA with a qualified external conducted source.

## E5-01 — OPEN / блокує випуск

Received Wisecoco board DC barrel size/polarity and USBTP/USB-C touch wiring still undocumented; no-VBUS enumeration must work.

**Умова закриття:** Obtain the exact board photo/schematic, DMM mapping, vendor confirmation and enumerate with only D+/D−/GND. Never substitute guessed connector numbering.

## E5-02 — OPEN / блокує випуск

IMU cable and exact received board revisions are unverified physical assemblies; E3 now defines RP2040-Zero/BNO085 internal wiring.

**Умова закриття:** Verify E3 board-pad map on received revisions; confirm chosen GX16 harness orientation, 3.3V UART and diode-fed E5_IMU_VIN; run 1e6 CRC-clean frames and 100 cold starts.

## E5-03 — OPEN / блокує випуск

ADT-Link R44SF connector variant and removal of ALL host 3.3 V paths are not yet confirmed.

**Умова закриття:** Confirm the part with ADT-Link; continuity-test every 3.3 V contact after modification. Validate 8 GT/s x1, cold/warm boots and zero AER. Validate a genuine power-cycle with LIME3V3 off, including signal backfeed.

## E5-04 — OPEN / блокує випуск

Current-setting resistors R501 (RTL-A), R509 (HF+) and R514 (T7) are engineering starting values (RILIM TBD); STACK §5.1 fixes only the rule 1.5–2× measured current. No measured device steady/startup currents or hot-corner proof.

**Умова закриття:** Measure current/inrush; set the RTL-A/HF+/T7 limits to 1.5–2× the measured current as STACK §5.1 requires; confirm HF+ minimum startup ≥0.75 A. Run the STACK §8 TPS2553DBVR-1 item 3 inrush test on latching U503 (HF+ LC 100 µH/100 µF + 220 µF damper) at final RILIM; only if it latches, fit TPS2553DBVR (constant-current) on this channel alone. Retry/latch test at all battery states; scope LC overshoot.

## E5-05 — OPEN / блокує випуск

T7 VBUS rail capacity and modified cable SuperSpeed signal integrity untested.

**Умова закриття:** With a real T7 prove J5 load <1.5 A expected operating budget, VCC_5V_PERI <=14 W, 5000M/UAS, no USB resets, fio, hot-corner TJ <=105 C for 1.5 A. Re-evaluate rail/switch/cable if failed.

## E5-06 — OPEN / блокує випуск

HDMI/display/hub and receiver backfeed paths through signal lines need physical power-state validation.

**Умова закриття:** Verify Q6A off / LAB5 on / display on combinations using DMM/FNB58. Q6A HDMI 5 V and Q6A USB VBUS should remain 0 V within measurement resolution. Check DDC/HPD after U506 installation and no phantom receiver power.

## E5-07 — OPEN / блокує випуск

EDL factory button pads and cable orientation not physically located on the exact received Q6A.

**Умова закриття:** Use the factory button first; continuity-identify its two switch nets before fitting parallel SW501. Unplug T7 for EDL and confirm 05c6:9008.

## E5-08 — OPEN / блокує випуск

Project locking connector/GX16 numbers have been assigned but final keyed part footprints/orientation and wire lengths are not released.

**Умова закриття:** Record exact supplier part numbers, face-view and wire-color tables; no-power continuity plus first energization current limit.

## E5-09 — OPEN / блокує випуск

Radiated-noise behavior and USB2 touch enumeration are physical integration gates, not determined by netlist.

**Умова закриття:** Run the STACK A/B noise matrix (HF+, GNSS, L-band, T7 authorized=0/off), cable strain relief and environmental tests; do not mark production-ready before passes.

## E5-10 — OPEN / блокує випуск

Wi-Fi/BT Q6A (FCU760K, AIC8800 на порту 4 FE1.1s) у польовому/QUIET root вимкнено лише програмно: blacklist з install /bin/false, udev authorized=0 за шляхом порту 4 і rfkill як другий шар. Апаратне утримання WIFI_PWR_EN (GPIO TLMM через CJ3134K до WIFI_PWR_EN_3V3, схема Radxa v1.21, с. 4) на отриманій платі не знайдено; gpio-hog у польовому DTBO не створено й не виміряно.

**Умова закриття:** W1-2 (STACK §8): домашній root з увімкненим Wi-Fi, тепле, а потім холодне перезавантаження в польовий root — на порту 4 FE1.1s немає пристрою (lsusb -t), немає мережевого пристрою wlan і hci0. Знайти лінію TLMM WIFI_PWR_EN, застосувати gpio-hog output-low у польовому DTBO, виміряти 0 V на живленні модуля й підтвердити, що домашнє розблокування працює; dpkg -l aicrf-test — пакет відсутній. До закриття authorized=0 без прив’язаного драйвера не вважати апаратним вимкненням.

## Додаткова калібровка аварійного ADC

Дільник E1 100 kΩ / 20 kΩ з допуском 1% та LM4040C30 0.5% не дають точного батарейного порога без калібровки. Початкова похибка біля 13.05 V може становити приблизно ±0.28 V. Перед штатним запуском потрібні дві опорні напруги, запис scale/offset із серійним номером пристрою та перевірка відсічки 13.05±0.1 V за кімнатної і підвищеної температури. Немає чинної калібровки — штатний режим заборонений.

## Правило звітності

Синтаксично валідний KiCad, збіг переліків з'єднань і навіть ERC без помилок не закривають ці ворота. Заборонено записувати PASS без виміряних даних, умов тесту, приладу й дати.
