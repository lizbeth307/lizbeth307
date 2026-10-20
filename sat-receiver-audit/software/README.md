# SR-RX 0.3 — керування, приймальна обробка й меню, 20.10.2026

У цій редакції реалізовано Python-службу `labd`, CLI `labctl`, переносний протокол UART, Pico Supervisor і прошивку зовнішнього RP2040-Zero/BNO085. Linux-служба має реальний I²C/UART backend та окремий режим SIMULATION. За замовчуванням запускається симуляція. Апаратного приймання, встановлення на Q6A або прошивання MCU не виконано.

Додано [labrx](RX.md) з RTL/HF+ bindings і FFT, [маскований спектр](SPECTRUM.md), [GNSS](LOCATION.md), [навчання](LEARNING.md), [Qt-меню](HMI.md), [декодерні адаптери](DECODERS.md) та [встановлення](DEPLOYMENT.md). Для цих функцій потрібні додаткові залежності; labd лишається на стандартній бібліотеці. Шість сторінок меню перевірено справжнім Qt offscreen. Знімки та hashes — `verification/hmi-views/`; це SIMULATION, не робота приймача на столі.

## Швидкий запуск меню

У власному Python-середовищі встановити `software` з extras `hmi` (NumPy/PySide6):

```sh
python3 -m venv /tmp/srrx-demo-venv
/tmp/srrx-demo-venv/bin/pip install './software[hmi]'
PYTHONPATH=software:. /tmp/srrx-demo-venv/bin/python -m srrx.hmi --demo
```

Демонстрація запускає справжній дочірній labd через pipes. Команду виконують із кореня повного проєкту: design/firmware є частиною комплекту, а не Python-wheel. `PYTHONPATH` вибирає саме це дерево джерел і його графи. У меню можна явно ARM/HOLD, вибирати routes, створити SIM-спектр, позначити дозволені ділянки й навчити CPU-модель. Немає автоматичного дозволу фізичного приймача. Для офлайн-встановлення використовують перевірений wheel cache з deployment, а не завантажують пакети наосліп на пристрій.

Повна хостова перевірка: `python3 tools/run_tests_offline.py`. Тестовий процес блокує IPv4/IPv6 sockets; ONNX telemetry opt-out встановлюється до import. Якщо необов'язкові Qt/ONNX залежності відсутні, їхні перевірки мають явний SKIP; це видно у звіті. Пакет джерел MCU: `python3 tools/build_firmware.py`.

Дані схеми залишаються в `design/E1.json`–`E5.json`. Карта MCP завантажується з E3; інтерлоки, бюджети та апаратні обмеження беруться з актуальних E1–E5, а не зі старої таблиці STACK. Протокол — [PROTOCOL.md](PROTOCOL.md), незалежний огляд — [INTEGRATION-REVIEW.md](INTEGRATION-REVIEW.md). Точні поточні лічильники тестів і SHA256 — `verification/software-tests.json`.

## Запуск без пристрою

Python 3.11+ на Linux. Із кореня `sat-receiver-audit`:

```bash
python3 tools/run_tests_offline.py
PYTHONPATH=software:. python3 -m srrx.demo --output verification/software-simulation.json
```

Демонстрація виконує повний handshake, вмикає модель LNA2, розриває зв'язок, перевіряє OFF/RESET, повертає зв'язок без автоматичного arm, робить явне recovery й перевіряє засувку FAULT. Використовуються справжні host/Pico state machines та обидва wire codecs. У звіті `physical_tests_performed=false`; синтетичні струми не зберігаються як виміри приймання.

Локальний сервіс через Unix-сокет:

```bash
PYTHONPATH=software:. python3 -m srrx.daemon --simulate
```

В іншому терміналі:

```bash
PYTHONPATH=software:. python3 -m srrx.cli status
PYTHONPATH=software:. python3 -m srrx.cli hold --arm
```

Поки `hold` працює, можна керувати з іншого термінала того самого користувача:

```bash
PYTHONPATH=software:. python3 -m srrx.cli route RTLA '"RF3"'
PYTHONPATH=software:. python3 -m srrx.cli set EN_LNA2 on
PYTHONPATH=software:. python3 -m srrx.cli sim FAULT_LNA2 false
PYTHONPATH=software:. python3 -m srrx.cli status
```

Для LNA2 спершу зачекати щонайменше 1 s після safe initialization: 500 ms OFF settling і 500 ms безперервного LOW DCS. Після FAULT один лише HIGH або повернення UART не відновлює виходи. Прибрати причину, завершити старий `hold`, явно виконати `recover`, далі підтримувати нову оренду; всі попередні навантаження залишаються OFF.

Оренда належить локальному UID, отриманому ядром через SO_PEERCRED, та має строк не більше 5 s. `hold` поновлює її раз на секунду; Ctrl-C робить disarm. Статус не поновлює оренду. Інший owner не може ввімкнути навантаження, але вимкнення залишається доступним. Сервер слухає лише Unix-сокет; мережевого HTTP/TCP endpoint немає.

У середовищі цієї перевірки створення AF_UNIX заборонене. Тому тест справжнього Unix-сокета має явний SKIP. Реальний дочірній процес через pipes перевірений:

```bash
PYTHONPATH=software:. python3 -m srrx.daemon --simulate --stdio
```

Уводьте JSON-рядки, наприклад `{"op":"status"}`, `{"op":"arm"}`, `{"op":"lease","value":{"ttl_ms":5000}}`. Відповідь — один JSON-рядок. EOF вимикає керування. Це той самий Engine; обмеження середовища не підміняється твердженням про успішний Unix IPC.

## Що робить фізичний backend

1. Перевіряє unit ID, 36 апаратних gates із локальними доказами, точні SHA256 графів/ПЗ, ADC, прошивки, струмові вікна й бюджет LAB5.
2. Відкриває лише явно задані I²C0/I²C2/UART7. Номери `/dev/i2c-*` не вгадуються.
3. Отримує свіжий Pico HELLO та звіряє живі serial/calibration CRC із прийнятим записом. CRC виявляє пошкодження; це не криптографічна автентифікація.
4. Після явного ARM Pico утримує RESET ≥100 ms і чекає два нові HB. У CONFIGURING Linux перевіряє справжній reset image MCP, записує safe OLAT (**CHG_INHIBIT=1**, інші керовані виходи LOW), IODIR, ODR/MIRROR та GPINTEN, перевіряє readback. CONFIGURED має завершитись за 1 s.
5. Лише після ACTIVE, свіжих справних входів і нової оренди політика дозволяє конкретні EN/route/relay. HB іде кожні 200 ms; Pico timeout 750 ms, host timeout STATUS >500 ms. I²C write не вважається успішним після помилки; незалежний MCP RESET виконує Pico.

INA228 рахує `V_N = VBUS − signed VSHUNT`. INA3221 фізично вимірює лише LNA1–4/LNB/BONI. Для решти гілок статус показує невідомий поточний струм і прийнятий фіксований резерв. Дані ADC для USB/S-band не вигадуються. Номінальне перетворення шунта саме по собі не має `calibration_valid=true`: runtime bridge застосовує прийняті unit-specific коефіцієнти до свіжих вимірів.

Інтерлоки охоплюють DCS preflight лише при власному bias OFF, відкладений PG, latched FAULT, HMC PARK, заборону K1=K2=1, break-before-make реле, LNB тільки через RTL-B RF3, Boni тільки після явних підтверджень і HF-реле, BENCH/AUX12 лише в lab/PARK, I_ANT≤1 A та I_ANT+0.83 A×EN_LABPORT≤1.5 A. До LAB5 додаються прийнятий always-on резерв, 52 mA overhead і резерви ввімкнених гілок; межа ≤3.2 A. Повний нуль I²C/ADC або відсутній baseline не стає дозволом.

IMU EVENT передається Pico з віком джерела. Host додатково враховує власний вік і 100 ms RX budget; при 500 ms орієнтація стає нечинною, quaternion=null. Після host loop gap >100 ms очищається кеш і UART RX. Старі записи в `events` є журналом, а не живими показами. Quaternion не задає true-north heading і не замінює GNSS.

## Приймання та встановлення

```bash
PYTHONPATH=software:. python3 -m srrx.provision template --output software/config/acceptance.template.json
```

Шаблон містить OPEN/null, актуальні hashes і жодного вигаданого PASS. Після реального приймання файл заповнюється доказами, точними коефіцієнтами, виміряними резервами та серійним номером Pico. `load_acceptance` перевіряє структуру/цілісність і прив'язку; достовірність фізичних вимірів забезпечує сам процес приймання. Зміна коду чи графа відкликає відповідність hashes.

Підготовка локальних записів Pico можлива лише із повністю прийнятого файла:

```bash
PYTHONPATH=software:. python3 -m srrx.provision prepare --acceptance /шлях/acceptance.json --output /шлях/pico-provisioned
python3 tools/build_firmware.py
```

Перший крок створює калібрування та device-bound commissioning CRC із hash приймального запису. Другий пакує MicroPython source і shared wire.py для обох MCU; **UF2 runtime не входить**, жоден MCU не прошивається автоматично. Інструкції: [Pico](../firmware/pico/README.md), [IMU](../firmware/imu/README.md). У репозиторії немає hardware-enabled commissioning файла.

Для Q6A зберегти проєкт у `/opt/srrx`, створити системного користувача `labd` і підтвердити доступ до потрібних I²C/UART. `systemd/srrx.service` використовує `/etc/srrx/acceptance.json` та перевірені шляхи з `/etc/srrx/devices.env`; example навмисно UNVERIFIED. Оператору потрібен доступ до групи локального control socket. Units перевірено `systemd-analyze verify`; запуск, доступи, pinmux і kernel/PMIC на Q6A ще не випробувані. Автоматичне встановлення/enable units тут не виконувалось.

`srrx-poweroff.service` — окремий root bridge. Лише в HARDWARE із прийнятим і живо прив'язаним unit та станом SHUTTING_DOWN він просить OFF_NOW і виконує `systemctl poweroff`. Pico дає фіксовані 20 s; повторні запити не продовжують строк. За замовчуванням модуль `srrx.poweroff` працює dry run; реальна дія вимагає `--execute`. У SIMULATION вимкнення ОС не виконується.

## Межа цієї реалізації

`labd` є контролером живлення/комутації; SDR відкриває окремий приймальний процес. Реалізовані FFT/RAM pipeline, bindings RTL/HF+, GNSS, спектральне навчання та меню не замінюють весь початковий C++ data plane 56 MS/s, повний каталог декодерів, підтверджений HTP/QAIRT runtime чи встановлений A/B образ. Lime runtime заблокований; експериментальні vendor patches є вихідним кодом для аудиту. Приймання Q6A, реальних SDR/дисплея й фізичних входів не виконано. HMI не має права самостійно дозволяти EN.

Прошивки не змінюють відому апаратну межу: повна втрата Pico3V3 при живій Q6A відпускає Q306 і не покривається цим reset actuator. Під час MCP RESET CHG_INHIBIT також high impedance — зарядка залишається під автономним апаратним контролем. Власне приймання батарейного/зарядного вузла, ISR/OS latency, GPIO рівнів, RF/термо й backfeed не виконано. Деталі: [OPEN_ITEMS](../OPEN_ITEMS.md).
