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

**Умова закриття:** До батареї current-limited sweep 14→12→14 V при 25 і 50 °C: trip 12.8±0.1 V, release 13.6±0.1 V, drift≤50 mV. Калібрувати R105. AON без INA ≤11 µA. Утримуванням кнопки не можна обійти UV. 20 PD cycles без самозапуску. При провалі fallback TLV3012 із нижнім плечем 346.04 kΩ і повним повтором тесту. Після UV release і натискання кнопки E1_PG_SYS12 мусить з'явитися без подальшого заряду: EN-резерв SYS12 R108/R109 має wake 13.39…13.86 V на E1_SW лише з допусками резисторів (без допуску внутрішніх 100 kΩ і порога EN), тобто може бути вищим за release; якщо PG_SYS12 не з'являється, E1-04 не пройдено. Рекомендована зміна, не застосована: R107 4.22M→2.87M і нижнє плече≈332.0k (R104 324k + R105 8.06k trim) дає trip≈12.79 V, release≈14.01 V, критерій release 14.0±0.1 V; R109 не зменшувати, бо це знижує резервний sleep. Порядок порогів на кожному екземплярі, разом з E3-07: за максимального й мінімального навантаження виміряна програмна відсічка, приведена до E1_N (13.05±0.1 V), мінус виміряний тут trip ≥0.10 V, а під час контрольованого розряду graceful shutdown (5 s dwell + завершення Linux) завершується до апаратного UV trip. Інакше — повторний trim R105 або reject.

## E1-05 — OPEN / блокує випуск

Default LAB5: D36V50F5 +4 A fuse; конкретні parts фільтра обрані. Агрегатний струм, converter/filter stability, температура і напруги на кінцевих навантаженнях не підтверджені.

**Умова закриття:** U108 D36V50F5 #4091; F102 4 A; L101 XAL6060-103MEC; C111/C112 35SVPF22M; C113 16SVPC100M; R110 WSL2512R3300FEA. Звірити площу, висоту і land patterns. Виміряти всі режими: LAB5 ≤3.2 A continuous; blower reserve 0.25 A continuous /0.50 A startup; SB_LNA 65 mA враховувати один раз у I_ANT≤1 A. Додаткова policy: I_ANT+0.83 A×EN_LAB≤1.5 A. За 5 V та 0…50 °C підтвердити C111/C112 effective ≥10 µF; C113 початково ≥80 µF; step 10…90% без осциляцій; 5 V±5% на КОЖНОМУ пристрої після switch/кабелю. Термо 30 min при 3.2 A і середовищі 50 °C; до 4 A transient із логом запобіжника та пульсацій. Вихід модуля 5 V±4% та drop L101 не гарантують USB 4.75 V у всіх допусках: low unit відбракувати або переробити живлення. Для пари LT3045 (E2-04) потрібно LAB5 ≥4.90 V на виході модуля при 3.2 A, інакше LNA4V5 у dropout. Якщо actual сума перевищує бюджет — формальний concurrency cap/rail redesign із повтором тестів.

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

Остаточні ILIM і пускові струми RTL-B, Lime, LNB, Boni та LaNA WB потребують натурних вимірів; ємність riser і комерційних модулів не опублікована.

**Умова закриття:** FNB58/INA228/INA3221: 20 холодних і теплих пусків, струми стримінгу, КЗ і SOA. Установити ILIM 1.5–2× виміряного струму з допусками. Boni: baseline включає bleed E4 13.86 mA (сталий ≈78.9 mA); поточний RILM 7.87k (ILIM min 0.113 A) нижче 1.5×, тож до кваліфікації перерахувати (рекомендовано≈7.15k). Загальний LAB5 тестується за новими воротами E1 для D36V50F5 + запобіжник 4A; старі 2.5A не є лімітом default-збірки.

## E2-04 — OPEN / блокує випуск

Запас напруги пари LT3045 на 4.5V на папері від'ємний: LAB5 min 4.80V (5V−4%) − 3.2A×29.8mΩ L101 − 1A×9.4mΩ L205 = 4.695V на E2_LNA_IN (4.684V за моделлю міді 55°C) проти 4.5V + 0.26V типового dropout при 500mA = 4.76V, тобто −65mV ще до спаду на запобіжнику й PCB. Пара в dropout при LAB5 нижче ≈4.865V, PSRR втрачено. Розподіл струму й температура не підтверджені. Сума індивідуальних номінальних ILIM LNA більша за 1A пари.

**Умова закриття:** Перевірити LAB5 min, навантаження пари до 1A, температуру кожного LT3045 та спад до антени. Дотримуватися контракту R-E2-17: сума INA LNA1–4 + резерв 65mA S-band ≤1A; разом із резервом LAB-порту ≤1.5A. Приймання: при 3.2A LAB5 і 1A на пару виміряти E2_LNA_IN, OUTS і LNA4V5; LT3045 мусять бути в регулюванні, тобто V(E2_LNA_IN)−V(OUTS) більше виміряного dropout. Інакше модуль LAB5 відбракувати (вимога LAB5 ≥4.90V на виході модуля при 3.2A) або застосувати рекомендовану зміну (не застосовано): a) R227 22.5k→21.5k (4.30V) після підтвердження мінімального живлення кожного LNA після TPS2553, шунта й кабелю; b) межа пари 0.5A сумарно в R-E2-17 (dropout ≈130mV тип.).

## E2-05 — OPEN / блокує випуск

Відсутність фантомного живлення Q6A, вимкнення дисплея та фізична правильність кінцевих кабелів потребують перевірки з реальним обладнанням.

**Умова закриття:** За активної LAB5 і вимкненої Q6A: 3V3_Q6A та upstream VBUS близько 0V, PICO_DISP_EN низький. Продзвонити розрізаний VBUS, ключовані роз’єми E3/E5 та сигнал PWR_ON_KEY.

## E3-01 — OPEN / блокує випуск

IMU assembly and two metre single-ended UART need bench verification. Internal named-pad wiring is specified, but no physical harness has been measured.

**Умова закриття:** Check actual module revision, GX16 plug/socket viewing direction and continuity to E5 design pinout; validate input Schottky and TVS at both ends; 1e6 frames with zero CRC errors. Upgrade to differential interface if errors occur.

## E3-02 — OPEN / блокує випуск

Brightness control requires confirmed DDC/CI support or an exact Wisecoco KEY/Backlight interface. Pico GP17 is now reserved for MCP watchdog reset and unavailable for brightness.

**Умова закриття:** Demonstrate ddcutil brightness through the specified RA620 link, or obtain exact KEY/Backlight revision pinout and design a new interface using a free MCPGPIO if suitable. Verify thermal dimming; do not reuse PicoGP17.

## E3-03 — OPEN / блокує випуск

BOM candidate Delta BFB0305HA-C is selected; final mechanical fit, installed airflow, start/stall current, LAB5 concurrency and noise remain unqualified.

**Умова закриття:** Fit body envelope30.5x30.5x10.5mm plus duct/lead clearance into CAD before cutting enclosure. Measure0.25A design continuous reserve and provisional0.50A startup limit rather than claiming peak from datasheet. Confirm LAB5 within E1-05 (<=3.2A continuous, <=4A transient with default D36V50F5 + F102 4A) in allowed concurrency; over budget means a formal concurrency cap per R-E2-17. Run45min closed-cover solar thermal test and RF A/B noise checks; inlet drop<=5Pa at requiredflow.

## E3-04 — OPEN / блокує випуск

UM3304 UART7/PPS/SWD cable capacitance and power-off behavior cannot be proven by ERC.

**Умова закриття:** Check <=20cm wiring, UART7 loopback, boot glitches and absence of Q6A backfeed with Pico on/Q6A off. Verify TX high-impedance sequencing or add hardware isolation.

## E3-05 — OPEN / блокує випуск

Shared MCP interrupt requires open-drain configuration before interrupts are enabled, plus measured I2C rise time and VOL.

**Умова закриття:** Set ODR=1 and MIRROR=1 first. Validate 100kHz, rise <=1000ns, 1e6 reads under load, 20 cold/20 warm boots, and 10us FAULT capture.

## E3-06 — OPEN / блокує випуск

BOM candidate Semiware MF52A103F3950 is selected for both NTCs; purchased-lot curve, attachment, lag and installed calibration remain unqualified.

**Умова закриття:** Verify10k+/-1% at25C and manufacturerB25/50=3950+/-1%; use exactmakerRTtable. Fit insulated bead/strainrelief on panel spreader and frame, check25/60/68C against reference thermometer, qualify lag and open/short/stale fail-safe behavior. Remain inside-20..120C sensorrange.

## E3-07 — OPEN / блокує випуск

Battery ADC shutdown accuracy must be calibrated. Divider/reference initial tolerances can contribute about+/-0.28V near13.05V; nominal ADC code does not establish the13.05+/-0.1V cutoff. The software window 12.95-13.15V must stay above the E1-04 hardware AON UV trip window 12.8+/-0.1V on every unit.

**Умова закриття:** Calibrate gain/offset against a calibrated voltmeter at two pack-equivalent voltages such as12.6V and16.4V; cross-checkINA228. Independently verify physical13.05V software cutoff (labd and Pico fallback both 13050 mV) within+/-0.1V, including5s dwell, at12.95/13.05/13.15V across specifiedtemperature and load states. Per unit, at maximum and minimum load: the measured software cutoff referred to E1_N minus the measured E1-04 hardware trip must be >=0.10V, and during a controlled discharge the graceful shutdown (5s dwell plus Linux shutdown) must complete before the hardware UV trip asserts OFF; otherwise re-trim or reject. Store calibratedcoefficients with revision/CRC. No commissioningpassuntilmet; hardwareAON UVsupervisor remains independentbackup.

## E3-08 — OPEN / блокує випуск

Pico watchdog, MicroPython GPIO/UART adapter and host handshake implemented 20.10.2026 and tested on the host. Actual GPIO timing, reset levels, WDT/brownout behavior and Linux/serial fault recovery have not been qualified on the device.

**Умова закриття:** Run the implemented firmware with the actual accepted Pico/Q6A assembly: scope MCP RESET assertion/release, safe output image including CHG_INHIBIT=1 after initialization, 100ms guard, 750ms heartbeat deadline plus measured latency, explicit fresh-session recovery, Linux kill/hang, UART loss/corruption, WDT/brownout and GPIO current/backfeed. Complete Pico power loss with Q6A alive remains outside Q306 coverage; no software test closes this boundary.

## E4-01 — OPEN / блокує випуск

ch1–3 injector choke part selection is complete; final DC drop, thermal rise, RF impedance and footprint qualification remain open. Optional static bleeds stay DNP.

**Умова закриття:** Verify selected 0805LS-471XGRC / 0805HP-221XGRC / 0603HP-47NXGRW manufacturer land patterns and target-band impedance under bias. VNA qualify IL/RL/isolation and DC heating at actual/worst protected current. The current Coilcraft 0603HP PDF confirms the 2.3 GHz typical SRF; no documentary SRF question remains. L401/L407 stay optional DNP until separately qualified.

## E4-03 — OPEN / блокує випуск

Boni supplied bias-tee port labels, DC socket polarity and receiver DC block require actual hardware.

**Умова закриття:** Measure continuity/polarity, antenna DC and RADIO port <0.1 V before connecting HF+.

## E4-04 — OPEN / блокує випуск

S-band module and supply selection are complete; external inline pod assembly, cable loss, gain/NF and thermal/current measurements remain unqualified.

**Умова закриття:** Build specified LaNAWB100845 + cf2235 + DC blocks in Hammond1554U2GY pod; verify stacked fit/cable bends, weather seals and strain relief. Measure LaNA current/inrush at protected5V, 2.2–2.3GHz S21/NF/linearity, and receiver protection. Do not substitute generic nominal NF for the actual S-band measurement.

## E4-05 — OPEN / блокує випуск

Lime X2/X4 are verified RX ports for v1.2; supplied-board channel A/B and cable labels need confirmation.

**Умова закриття:** Check the exact revision schematic and conduct a one-port-at-a-time RX test. Generic setup X3 wording is not evidence.

## E4-06 — OPEN / блокує випуск

Three concrete protected bipolar DC-window detectors are designed; threshold, RF loading and power-off backfeed still need prototype qualification. The ±30 V foreign-DC envelope covers the detector tap only: the assembled P2/P3/HF_CM ports share their DC node with E2 TPS2553/INA3221/U214 and polarized capacitors, which own bias OFF does not isolate, so a hardware blocking element is required.

**Умова закриття:** Verify each DCS LOW at0V and HIGH by±0.100V in both sweep directions over admitted temperature/supply range; record thresholds/hysteresis. Apply ±30V limited foreign DC with Q6A ON/OFF, requiring3V3_Q6A<0.1V when OFF, only at the detector tap with the bias branch disconnected (L403/L404 not fitted; A406 DC port unplugged from BONI13V8). On an assembled port never exceed −0.3…+5.5V on P2/P3 or −0.3…+0.3V on HF_CM with own bias OFF (TPS2553 OUT −0.3…7V, INA3221 −0.3…26V, TPS259630 OUT ≤VIN+0.3V, polarized C239/C243/C273); the ±0.100V sweep lies inside these limits. Hardware redesign required before this gate can close: a ±30V-rated bidirectional blocking element in each sensed bias branch between the E2 output and the E4 injector (relay contact or back-to-back MOSFETs held open whenever EN_LNA2/EN_LNA3/EN_BONI is low, or a TPS2660-class ±60V eFuse with reverse-polarity and reverse-current blocking), keeping TPS2553/INA3221/U214 and the electrolytics on the protected side; the detector is not that protection. Then repeat ±30V at each assembled port. Measure RFtap IL/RL/NF impact. Require startup/reference-fault HIGH and ownbiasOFF≥500ms beforepreflight; readiness staysfalse untilqualified. Check floating/open antenna as well as0Ω/50ΩDC loads. Include the996Ω bleed load in current baselines and measure its RF loss/parasitics. Reject false-safe at±0.100V; false-unsafe units also fail usability qualification. Also qualify cold minimum-supply reference-feed headroom: the arithmetic model requires D450 Vf≤1.015 V at VDD3.135 V and REF2.072 V for at least80µA LM4040 cathode current. Reference collapse must force HIGH, and must not be misreported as a working detector.

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

**Умова закриття:** Obtain exact board photo/schematic, DMM mapping, vendor confirmation and enumerate with onlyD+/D−/GND. Never substitute guessed connector numbering.

## E5-02 — OPEN / блокує випуск

IMU cable and exact received board revisions are unverified physical assemblies; E3 now defines RP2040-Zero/BNO085 internal wiring.

**Умова закриття:** Verify E3 board-pad map on received revisions; confirm chosen GX16 harness orientation, 3.3V UART and diode-fed E5_IMU_VIN; run 1e6 CRC-clean frames and 100 cold starts.

## E5-03 — OPEN / блокує випуск

ADT-Link R44SF connector variant and removal of ALL host3.3V paths are not yet confirmed.

**Умова закриття:** Confirm part withADT-Link; continuity test every3.3V contact after modification. Validate8GT/sx1, cold/warm boots andzeroAER. Validate genuine power-cycle withLIME3V3 off including signal backfeed.

## E5-04 — OPEN / блокує випуск

Current-setting resistors are engineering starting values, no measured device steady/startup currents or hot-corner proof.

**Умова закриття:** Measure current/inrush, setRTL/HF limits1.5–2times measured asSTACK, confirmHFminimumstartup>=0.75A; retry/latch test at all battery states; scopeLCovershoot.

## E5-05 — OPEN / блокує випуск

T7 VBUS rail capacity and modified cable SuperSpeed signal integrity untested.

**Умова закриття:** WithrealT7 proveJ5load<1.5A expected operating budget, VCC_5V_PERI<=14W,5000M/UAS,noUSBresets,fio,hot-cornerTJ<=105C for1.5A. Reevaluate rail/switch/cable if failed.

## E5-06 — OPEN / блокує випуск

HDMI/display/hub and receiver backfeed paths through signal lines need physical power-state validation.

**Умова закриття:** VerifyQ6Aoff/LAB5on/displayon combinations usingDMM/FNB58. HDMI5VQ6A andQ6AUSBVBUS shouldremain0V withinmeasurementresolution. CheckDDC/HPD afterU506installation andno phantom receiverpower.

## E5-07 — OPEN / блокує випуск

EDL factory button pads and cable orientation not physically located on exact receivedQ6A.

**Умова закриття:** Use factory button first; continuity-identify its two switch nets before fittingparallelSW501. UnplugT7 forEDL and confirm05c6:9008.

## E5-08 — OPEN / блокує випуск

Project locking connector/GX16 numbers have been assigned but final keyed part footprints/orientation and wire lengths are not released.

**Умова закриття:** Record exact supplier part numbers, face-view and wire-color tables; no-power continuity plus first energization current limit.

## E5-09 — OPEN / блокує випуск

Radiated-noise behavior and USB2touch enumeration are physical integration gates, not determined by netlist.

**Умова закриття:** RunSTACK A/B noise matrix (HF+,GNSS,Lband,T7authorized=0/off), cable strain relief andenvironmental tests; do not markproductionready beforepasses.

## Додаткова калібровка аварійного ADC

Дільник E1 100 kΩ / 20 kΩ з допуском 1% та LM4040C30 0.5% не дають точного батарейного порога без калібровки. Початкова похибка біля 13.05 V може становити приблизно ±0.28 V. Перед штатним запуском потрібні дві опорні напруги, запис scale/offset із серійним номером пристрою та перевірка відсічки 13.05±0.1 V за кімнатної і підвищеної температури. Немає чинної калібровки — штатний режим заборонений.

## Правило звітності

Синтаксично валідний KiCad, збіг переліків з'єднань і навіть ERC без помилок не закривають ці ворота. Заборонено записувати PASS без виміряних даних, умов тесту, приладу й дати.
