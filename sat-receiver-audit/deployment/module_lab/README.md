# Емуляція модулів та реєстр покриття

Цей набір підключає поточні драйвери, переносну прошивку та програмну політику до незалежних моделей регістрів, пакетів і зовнішніх API. Він перевіряє взаємодію коду до підключення плати. **Результат емуляції не є апаратним прийманням:** живлення, RF, реальні датчики, Q6A та покупні модулі залишаються фізично неперевіреними.

`inventory.json` розподіляє всі **750 схемних позначень** між **64 вузлами**, містить **166 деталізованих інтерфейсів** і **30 окремих каталожних/заводських сутностей**. Це розмір реєстру, а не кількість виконаних чи успішних емуляторів. Резистор або механічна деталь є параметром свого вузла; їм не приписується вигаданий регістровий інтерфейс. Історичні альтернативи, запасні прилади та заводські внутрішні частини не стають автоматично встановленими модулями.

## Запуск усіх наборів

Потрібні Linux, Python 3.11+, NumPy, PySide6 для Qt-сценаріїв та компілятори C `cc` і C++17 `c++` для native receiver fixtures і Lime guard snippets. Використовуйте підготовлене середовище [Linux lab](../linux_lab/README.md) або окреме власне середовище із цими залежностями. Набір не встановлює пакети, не відкриває фізичні USB/I²C/GPIO/UART і не створює чинного acceptance-файла.

Із кореня повного проєкту:

```sh
PYTHONDONTWRITEBYTECODE=1 QT_QPA_PLATFORM=offscreen \
  python3 deployment/module_lab/run.py --project . --output /tmp/srrx-module-run-001
```

`--output` тут — **новий порожній каталог**, а не JSON-файл. Повторне використання непорожнього каталогу відхиляється. Runner запускає шість окремих процесів; кожний має обмеження 600 s. Він звіряє розмір і SHA256 усіх семи вихідних snapshots із `inventory.json`: п'яти `design/E1.json`–`E5.json`, `STACK.md` та `build/12-revision-v2.1.md`. Додатково перевіряються точний розподіл схемних refs без пропусків/дублювання і збіг повних `source_pins` та `value` кожного деталізованого інтерфейсу з поточним графом. Застарілий реєстр відхиляється. Після зміни джерел перегляньте реєстр і відповідні моделі; відповідність файлів не підтверджує фізичну розпіновку або правильність електричного проєкту.

Вихідні файли:

| Файл | Вміст |
|---|---|
| `report.json` | Зведений фактичний результат, оточення, hashes, вкладені domain reports і coverage |
| `module-results.html` | Автономна таблиця інтерфейсів із пошуком, фільтром та деталями моделей/обмежень |
| `MODULE-RESULTS.md` | Коротка таблиця результатів для читання без браузера |
| `power.json`, `mcu.json`, `radio.json`, `location.json`, `io.json`, `connectivity.json` | Повні сценарії шести окремих наборів і їхні межі |
| Відповідні `*.log` | stdout/stderr запуску кожного domain process |

Runner зберігає hashes графів, inventory та Python-моделей. Перевіряйте їх разом із domain reports перед посиланням на старий результат. Наявність README або порожнього каталогу результатів не є доказом виконання. Архітектура й версія Linux беруться із фактичного запуску: результат x86_64 не слід називати ARM64-випробуванням.

Перебудувати лише Markdown/HTML з уже наявного звіту, без повторного виконання моделей:

```sh
python3 deployment/module_lab/run.py \
  --render-report /tmp/srrx-module-run-001/report.json \
  --output /tmp/srrx-module-view
```

## Що означають стани

| Стан | Значення |
|---|---|
| `EMULATION_PASS` або domain `PASS` | Пройдено записані сценарії конкретного драйвера/моделі на зазначеному рівні покриття |
| `FAIL`, `EMULATION_FAIL` | Виявлена помилка виконання або перевірки; дивіться конкретний сценарій і журнал |
| `CONNECTION_MODEL_PASS`, `CONNECTION_MODEL_FAIL` | Результат окремої перевірки динамічної моделі з'єднань проти KiCad XML; не результат функціональної емуляції драйвера |
| `UNSUPPORTED`, `UNAVAILABLE` | Потрібний інтерфейс/драйвер/залежність не реалізований, не підтверджений або недоступний у середовищі; це не PASS |
| `CONNECTION_MODEL_ONLY` | Для цього схемного інтерфейсу немає успішної функціональної моделі; перевірка його з'єднань може окремо мати `CONNECTION_MODEL_PASS` |
| Загальний `EMULATION_PASS_WITH_GAPS` | Усі шість domain processes завершилися успішно і немає виявленої помилки покритого інтерфейсу; непокриті функції та модулі все одно залишаються відкритими |
| Фізичний `NOT_TESTED`, `hardware_qualified=false` | Пристрій або його фізичні властивості не прийняті незалежно від програмного результату |

У зведеній таблиці `EMULATION_PASS` означає, що **принаймні одна** модель для цього ref виконана успішно. Це не означає перевірки всіх функцій модуля. Розкрийте `models`, `coverage_level`, `limitations`, `unmodeled_records`, `constraints` і `pinout_status`: для того самого ref можуть залишатися інші `UNSUPPORTED` функції. Окремі каталожні прилади наведені у JSON `coverage.catalogue_only_entities`; вони не перетворюються на перевірені драйвери через відсутність окремого схемного символу.

У JSON поле `coverage.interfaces[].connection_status` обліковується окремо від функціонального `status`. Успішний Connectivity набір не збільшує кількість функціональних `EMULATION_PASS` і не закриває `UNSUPPORTED`: звірка з'єднань та виконання драйвера перевіряють різні властивості.

Код завершення загального runner: **0** — виконані набори успішні із зазначеними прогалинами; **1** — хоча б один набір завершився невдало/недоступний або перевірка покриття виявила помилку. Індивідуальні CLI можуть додатково повертати **2** для недоступного середовища. Деякі domain reports містять навмисні `UNSUPPORTED` записи й успішно завершуються: читайте деталізацію, а не лише exit code.

## Межі шести наборів

| Набір | Що реально виконується | Що цим не доведено |
|---|---|---|
| Power | Поточні LinuxHardware/I²C read-write та telemetry methods проти незалежних MCP23017/INA228/INA3221 register models; reset, помилки шини, conversion/freshness, sign/scale та керування виходами | Kernel I²C ioctl, електричні рівні, силові перехідні процеси, точність ADC, калібрування, BMS, нагрів та властивості кремнію поза реалізованим subset |
| MCU/HMI/IMU | Переносні production Pico/IMU драйвери з моделями machine/SPI/I²C/UART, BNO085 SHTP, ключами PI4IO9555, енкодерами, VEML7700, ADC/NTC/tach і supervisor | Виконання інструкцій RP2040, MicroPython/UF2/USB boot, фізичний watchdog, IRQ/GC latency, sensor fusion/магнітна калібровка та оптична/термічна точність |
| Radio | Реальні ctypes ABI та окремі RX worker processes проти скомпільованих synthetic C libraries; RTL-A/B, HF+, контрольна політика RF/bias, точні підтримувані guard-фрагменти Lime | Реальна USB-прошивка/FPGA/MMIO, фізичне термінування TX, analog gain/NF/isolation/matching, PCIe та повний аудит Lime або отримання ефірних сигналів |
| Location | Linux PTY з LC76G NMEA-байтами → production LocationTracker; production GpsdClient → незалежний сервер GPSD JSON API на 127.0.0.1; checksum, fragmentation, replay, stale/drop/reconnect і UTC gates | Справжній gpsd, супутниковий прийом, PPS/chrony, Q6A UART6 pinmux/електрика, reset circuit, GNSS UTC або дисциплінування системного годинника |
| I/O/storage/display | Приватне дерево synthetic USB descriptors, реальні файлові операції/відмови та production storage paths; Qt input events і поточні меню/контролер | Kernel USB enumeration/uevents, реальні VID/PID/контролери/інструменти, UFS/T7 firmware/ресурс/швидкість, фізичні HDMI/HID/touch/backlight та заводська прошивка панелі |
| Connectivity | Динамічна модель ідеальних nets для всіх 750 refs і 166 деталізованих інтерфейсів, звірена окремим parser із поточним `verification/netlist.xml`; від'єднання кожного підключеного pin, всього компонента/вузла, shorts між nets, розрізнення навмисного NC та помилкового приєднання | Функції драйверів/модулів, поширення сигналів через компоненти, аналогові властивості, правильність самого задуму схеми або фізична здатність пристрою виявити кожну несправність |

У моделях можуть бути явно задані synthetic permissions, reset state, струми, напруги чи ознаки локальної калібровки, щоб досягти перевірюваної гілки коду. Вони не зберігаються як апаратні докази й не змінюють production release guards. Cached all-off після помилки I²C не є підтвердженням фізичного LOW: відповідні сценарії окремо перевіряють модель latch/reset і залишають апаратну межу відкритою.

Connectivity навмисно зберігає DNP, NC, невідомі/TBD контакти та розрізнення функціональних назв і підтверджених фізичних номерів. KiCad XML має спільне зі схемними графами джерело проєктування: окремий parser виявляє розбіжності серіалізації та штучно внесені несправності, але не є незалежним підтвердженням електричного рішення. Ідеальна модель не проводить сигнал крізь резистори, конденсатори, діоди, switches чи внутрішні схеми IC/модулів. J102 залишається DNP/service-only з відкритим E1-02; модель його nets не дозволяє підключення зарядного пристрою.

LC76G та GPSD API мають вигадані лабораторні координати/епохи, не позицію користувача й не таблицю міст. Три різні 3D-повідомлення перевіряють програмний UTC gate щодо **інжектованого синтетичного reference**, а не справжність часу GNSS. Raw UART glue у цьому тесті доставляє байти до `LocationTracker.ingest_nmea`; окремий production raw-LC76G UART reader цим не створюється.

GPSD API-сценарії використовують лише числовий loopback 127.0.0.1 і не потребують NIC або зовнішнього інтернету. Тому весь module lab запускається **окремо від** `tools/run_tests_offline.py`, який забороняє створення AF_INET/AF_INET6 sockets у своєму процесі. Відсутність мережевої карти не вимикає loopback усередині Linux VM.

## Окремі CLI та API

Кожна наведена команда використовує JSON-**файл** як `--output`; це відрізняється від загального runner вище:

```sh
python3 deployment/module_lab/power_scenarios.py --project . --output /tmp/srrx-power.json
python3 deployment/module_lab/mcu_scenarios.py --project . --output /tmp/srrx-mcu.json
python3 deployment/module_lab/radio_modules.py --project . --output /tmp/srrx-radio.json
python3 deployment/module_lab/location_scenarios.py --project . --output /tmp/srrx-location.json
QT_QPA_PLATFORM=offscreen python3 deployment/module_lab/io_scenarios.py --project . --output /tmp/srrx-io.json
python3 deployment/module_lab/connectivity.py --project . --output /tmp/srrx-connectivity.json
```

Програмні входи: `power_scenarios.run(project)`, `mcu_scenarios.run(project=None)`, `radio_modules.run(project, compiler='cc', include_worker=True, include_control=True)`, `location_scenarios.run(project)`/`run_all(project)`, `io_scenarios.run(project=None, output_dir=None, qt=True)`, `connectivity.run(project)`. Загальний `run.py` викликає CLI в окремих процесах і нормалізує їхні власні схеми звітів; їхні сирі JSON не треба вважати однаковою API-схемою.

`radio_modules --no-worker/--no-control` та `io_scenarios --no-qt` звужують перевірку. Результат такого запуску не рівнозначний повному набору. Підтвердження конкретного ARM64 запуску, кількості виконаних сценаріїв і фактичних прогалин беріть тільки зі збережених результатів відповідного середовища.
