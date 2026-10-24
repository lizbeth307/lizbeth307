# LC76G: UART-читач NMEA та обмежений імпульс RESET

Цей документ описує два програмні шари для приймача Quectel LC76G (Waveshare 24370, U304): `srrx.gnss_uart` — читач NMEA з UART6 лише на прийом (альтернатива gpsd, див. нижче), та операцію `gnss_reset` у `SafetyPolicy` служби labd — один обмежений імпульс RESET_N через MCP23017 #4. Код і тести реалізовано. **На зібраному Q6A, справжньому UART6 чи схемі скидання їх не запускали.** Модульні тести працюють на справжніх Linux PTY, тимчасовому фальшивому sysfs і `SimHardware`; це SIMULATION/EMULATION, а не апаратний PASS.

Обидва шари лише приймають або скидають приймач. Жоден з них не вмикає передавач, живлення антени чи DC на антенному вході, не надсилає приймачу команд налаштування й не розбирає приватний вміст. Позиція береться лише з власного GNSS-фіксу; таблиць міст немає, а тестові дані — одна безіменна синтетична точка lat/lon.

**Робочий ланцюг часу й місця за STACK — gpsd → chrony** (STACK.md:124, :879; build/07 §18): `gpsd -n -b -s 115200` читає `/dev/lab/gnss` і нічого не пише в приймач, chrony бере NMEA від gpsd через SHM і PPS з `/dev/pps-gnss`, а споживачі позиції (зараз — меню HMI) читають gpsd через `GpsdClient` ([LOCATION](LOCATION.md)). Сирий читач `srrx.gnss_uart` — лише альтернатива для конфігурації без gpsd; обидва режими взаємовиключні, UART читає лише одна сторона.

## Підключення (з графа схеми та build-документів)

| Що | Значення | Джерело |
|---|---|---|
| UART | UART6, хедер 16/18, `alias serial1 = …/serial@998000`, рівень 3.3 V | build/04-pidkliuchennia-pinout.md:37, :76, :201; build/07-pz-vstanovlennia.md:203 |
| Ланцюги | U304 P1.3 TXD → `UART6_RX`, P1.4 RXD ← `UART6_TX` | design/E3.json, U304 |
| Швидкість | 115200 8N1 (`GPSD_OPTIONS="-n -b -s 115200"`) | build/07-pz-vstanovlennia.md:461; 09-testy.md:55 (W-04) |
| Вузол | udev `KERNELS=="998000.serial"` → `/dev/lab/gnss`; ніколи жорстко `ttyHS1` (номер залежить від порядку probe) | build/04:37; build/07:475 |
| PPS | хедер 7, GPIO96, pps-gpio → `/dev/pps-gnss`; власник — chrony | build/04:33, :203; build/07:465-470 |
| RESET | MCP23017 #4 (0x23, U303) GPA1 → `E3_GNSS_RESET_GATE` → затвор 2N7002 Q301, стік на `E3_GNSS_RESET_N`; R326 100k тримає затвор низько; high = скидання, 0 = неактивний | design/E3.json U303/Q301/R326; build/04:144 |
| Вимога Quectel | RESET_N низько ≥100 ms, зовнішня підтяжка заборонена | design/E3.json, примітки U304 |
| Власник лінії RESET | labd | build/07:525 |

## Читач `srrx.gnss_uart`

Модуль використовує лише стандартну бібліотеку (`os`, `termios`, `fcntl`, `select`, `stat`, `re`, `errno`) і не має відносних імпортів, тож module lab завантажує саме цей файл.

```python
from srrx.gnss_uart import open_lc76g, NmeaUartReader
from srrx.location import LocationTracker

tracker = LocationTracker()
fd = open_lc76g()                      # лише /dev/lab/gnss, KERNELS=="998000.serial"
reader = NmeaUartReader(fd, tracker)   # читач володіє fd
accepted = reader.poll(now_ms)         # з наявного 20 ms select-циклу; перший виклик лише робить flush
reader.status()                        # state, bytes_received, flushes, last_byte_ms, error, reset_candidate
reader.close()                         # явне закриття; повторного відкриття немає
```

### Прив'язка `open_lc76g` / `bind_lc76g`

- Шлях за замовчуванням — рівно `/dev/lab/gnss`; інший шлях можливий лише явним аргументом (так роблять тести). Шлях має бути udev-псевдонімом (symlink). Ім'я ядра `/dev/tty*` відхиляється (`GNSS_PATH_NOT_ALIAS`); сканування `/dev` і запасного шляху немає.
- `realpath` мусить бути символьним пристроєм (`GNSS_NOT_CHAR_DEVICE`). `realpath(<sysfs>/class/tty/<ім'я>/device)` мусить містити сегмент шляху `998000.serial` (`GNSS_PARENT_MISMATCH`), як doctor перевіряє батьківський пристрій Pico. Номер у `<sysfs>/class/tty/<ім'я>/dev` мусить дорівнювати `st_rdev` вузла (`GNSS_SYSFS_DEV_MISMATCH`). Після відкриття `fstat` має повернути той самий `st_rdev` (`GNSS_DEVICE_CHANGED`).
- Відкриття: `O_RDONLY|O_NOCTTY|O_NONBLOCK|O_CLOEXEC`, далі `flock(LOCK_EX|LOCK_NB)` і `ioctl(TIOCEXCL)` до будь-якої зміни termios чи flush, як `srrx.link` для Pico. Root/CAP_SYS_ADMIN обходить `TIOCEXCL`.
- `configure_raw_115200(fd)`: `iflag=oflag=lflag=0`, `cflag=CS8|CREAD|CLOCAL` (без PARENB/CSTOPB/CRTSCTS/HUPCL), `ispeed=ospeed=B115200`, `VMIN=VTIME=0`, `tcsetattr(TCSANOW)`, тоді зворотне читання `tcgetattr`. Розбіжність дає `GNSS_TERMIOS_MISMATCH`; лише після збігу виконується `tcflush(TCIFLUSH)`. За будь-якої помилки дескриптор закривається; `termios.error` перетворюється на `OSError`.

### `NmeaUartReader.poll(now_ms)`

- Дескриптор має бути `O_RDONLY` і неблокувальним, інакше `GNSS_UART_FD_MODE`. Модуль не містить жодного шляху запису: не надсилає PAIR/PQTM-речень, оновлень прошивки чи команд скидання.
- Межа: щонайбільше 8 читань по 2048 байт (16 KiB) за виклик. Кожен шматок — окремий виклик `LocationTracker.ingest_nmea`, тож рядки від 16 байт укладаються в ліміт 128 рядків трекера; коротше сміття спрацьовує як `NMEA_BATCH_LIMIT` (fail closed). 115200 baud у 8N1 — це 11520 B/s (близько 11.25 KiB/s).
- Затримка хоста: якщо між викликами минуло понад 500 ms (або час пішов назад), читач робить `tcflush(TCIFLUSH)` і `tracker.invalidate("nmea", "NMEA_HOST_STALL")` (`NMEA_MONOTONIC_TIME_REVERSED`), як Engine відкидає UART-вхід Pico після розриву тіку. Після flush і на старті байти до першого `$` до трекера не потрапляють. Тому незавершений до затримки рядок трекер лише відкидає (`NMEA_RESYNC`), а нові байти ніколи його не «дописують». Інакше старе речення отримало б новий час прийому.
- Перший `poll()` теж вважається початком затримки: він завжди робить `tcflush(TCIFLUSH)`, хоч би коли його викликали після `open_lc76g()`. Байти, що накопичилися відтоді, не мають часу прийому, тож до трекера вони не потрапляють. Інвалідації цей flush не робить, бо читач ще нічого не передав. Тому перший виклик варто зробити одразу після створення читача; module lab так і робить.
- Тиша: без жодного байта 2 s — одноразово `invalidate("nmea", "NMEA_UART_SILENT")`, стан `QUIET`; від 10 s — `SILENT`, тобто лише кандидат на скидання. Автоматичного скидання чи ескалації немає. Затримка самого хоста не вважається тишею приймача: відлік тиші починається заново, але й прийомом це не вважається. До першого справжнього байта після flush стан лишається `STARTING`, а не `RECEIVING`. `last_byte_ms` у `status()` — час останнього справжнього байта, а не перезапуску відліку.
- Втрата: `POLLHUP/POLLERR/POLLNVAL` від `select.poll` або `EIO/ENXIO/ENODEV/EBADF` під час читання закривають дескриптор (окрім EBADF/POLLNVAL, коли номер уже може належати іншому файлу), викликають `invalidate("nmea", "NMEA_UART_LOST")` і ставлять `disconnected=True`. Інші помилки вводу-виводу дають `NMEA_UART_IO_ERROR`. Повторного відкриття немає: новий `open_lc76g()` і новий читач — явне рішення оператора чи служби. Порожнє читання за `VMIN=VTIME=0` означає лише «немає даних»; зависання tty видно тільки через poll.
- Стани: `STARTING` (жодного байта від початкового flush чи flush після затримки), `RECEIVING`, `QUIET`, `SILENT`, `DISCONNECTED`. Потоків і sleep немає; час — монотонні цілі мілісекунди того самого годинника, що й у трекера.
- Системні виклики `os.open`, `os.read`, `os.close` і `termios.tcgetattr` модуль бере через власні псевдоніми (`_os_open`, `_os_read`, `_os_close`, `_tcgetattr`). Тести підміняють ці імена, а не глобальні функції `os`, тож потоки інших тестів у тому самому процесі не перехоплюються.

### Режими та межі обсягу

- Режим gpsd (`gpsd -b`, без записів у приймач, STACK.md:879) — робочий; сирий режим цього читача — альтернатива без gpsd. Вони взаємовиключні **за конфігурацією**: UART читає лише одна сторона. `flock`/`TIOCEXCL` зупиняють інших непривілейованих відкривачів, але не root. У сирому режимі gpsd не повинен мати `/dev/lab/gnss` у `DEVICES`.
- Не реалізовано, свідомо поза цим обсягом: інтеграція читача в цикл служби labd, керування gpsd/chrony, PPS-ворота (`chronyc selectopts PPS ±noselect`, build/07:484), окремий інструмент надсилання налаштувань з allowlist build/07:485-498 з читанням назад (лише при зупиненому gpsd; ніколи `$PAIR007`, `$PAIR752`, `$PAIR753`, build/07:500).
- Ворота публікації позиції (3D і ≥6 супутників; перший фікс — 3D, ≥8 супутників, у межах 50 m протягом 5 хв; стрибок понад 100 km потребує підтвердження, STACK.md рядок «служба місця», build/07:503) належать шару-споживачу, а не читачу.

## udev-правило `/dev/lab/gnss`

`deploy.stage` разом із явними прив'язками пристроїв записує окремий файл `etc/udev/rules.d/71-srrx-gnss.rules`. Той самий кандидат друкує `python3 deployment/deploy.py udev-gnss`:

```text
SUBSYSTEM=="tty", KERNELS=="998000.serial", GROUP="srrx-gnss", MODE="0640", ENV{ID_MM_DEVICE_IGNORE}="1", SYMLINK+="lab/gnss", TAG+="systemd"
```

- `998000.serial` — фіксований UART6 плати, а не запис `devices.json`, тому точна схема `devices.json` (`schema_version` 1) не змінюється.
- `0640`: група лише читає, інші не мають доступу. `srrx-gnss` — системна група без login-членів, бо NMEA розкриває місцезнаходження. Її створюють до встановлення правила: `groupadd --system srrx-gnss`. Відсутня група **не** дає fail closed: невідому `GROUP` udev пропускає, і вузол може зберегти групу стандартних правил (`50-udev-default.rules` дає `dialout` для `ttyHS*`), тож NMEA змогли б читати члени `dialout`. Фактичного власника й режим перевіряють `stat -L /dev/lab/gnss` на Q6A (RUNTIME_ONLY). Якщо замість gpsd обрано сирий режим і читач інтегровано в службу, labd отримає `srrx-gnss` лише через `SupplementaryGroups`; цей крок ще не виконано, а udev-кандидат сам групу не створює ([DEPLOYMENT](DEPLOYMENT.md)).
- ModemManager не надсилає AT-проби (`ID_MM_DEVICE_IGNORE`).
- RUNTIME_ONLY на Q6A: `udevadm info`, справжній `ls -l /dev/lab/gnss`, права вузла після старту gpsd (gpsd під root перед скиданням привілеїв може змінювати права пристрою — перевірити `stat`) і те, що gpsd після скидання привілеїв повторно відкриває `/dev/lab/gnss` після втрати UART, 20 перезавантажень `ttyHS1 → 998000.serial` (09-testy.md:55, W-04).

## Імпульс RESET у labd

`SafetyPolicy` — єдиний власник I²C. Нова іменована операція:

```python
policy.command("gnss_reset", {"width_ms": 200}, now_ms)   # або None/{} -> 200 ms
engine.request({"op": "gnss_reset", "value": {"width_ms": 200}, "_owner": "uid:1000"})
```

```bash
# Поки `labctl hold --arm` того самого користувача тримає оренду:
PYTHONPATH=software:. python3 -m srrx.cli gnss_reset --width-ms 200
```

Сирий запис ланцюга `E3_GNSS_RESET_GATE` і далі відхиляється загальним whitelist (`raw GPIO is forbidden`), як у озброєному, так і в неозброєному стані.

### Передумови

| Перевірка | Де | Відмова |
|---|---|---|
| Власна чинна оренда того, хто запитує (немає оренди — немає власника) | Engine | `gnss_reset requires the caller's own valid lease` |
| Engine `configured`, ARM не очікує підтвердження | Engine | `… configured MCP outputs and no pending arm` |
| Свіжий статус Pico (≤500 ms), `mcp_reset == False` | Engine | `… fresh Pico status with MCP RESET released` |
| `policy.fault is None` | Policy | `fault latched: …` |
| Чинна оренда | Policy | `valid owner lease required` |
| `width_ms` — ціле (не bool) 100..500, за замовчуванням 200; інших ключів немає | Policy | `GNSS_RESET_WIDTH` |
| `hardware.initialized`, без засувки помилки адаптера | Policy | `GNSS_RESET_HARDWARE` |
| Імпульс не триває, лінія низька | Policy | `GNSS_RESET_IN_PROGRESS` |
| ≥30 s від **відпускання** попереднього імпульсу (холодний TTFF 28 s, 09-testy.md:179) | Policy | `GNSS_RESET_SPACING` |
| ≤3 імпульси за ковзні 15 хв | Policy | `GNSS_RESET_RATE_LIMIT` |

Імпульс нічого не живить, тому сам об'єкт `SafetyPolicy` дозволяє його і в неозброєному стані. **Через labd/labctl імпульс можливий лише в озброєному, налаштованому сеансі** (Pico ACTIVE). `Engine.configured` встановлює лише ARM-потік (CONFIGURING), кожен trip його скидає, а ARM, що очікує підтвердження, відхиляється. Тому `labctl hold --arm` — обов'язкова умова, а не лише приклад. Імпульс не перезапускається й не ескалюється автоматично.

### Часові межі

- Assert: запис `E3_GNSS_RESET_GATE=True`. `tick()` знімає імпульс на першому тіку ≥ start + width; Engine тікає кожні 20 ms. Якщо Pico-статус застарів, Engine все одно викликає `policy.tick`, поки імпульс триває.
- Жорсткий дедлайн 1000 ms: пізніший тік одразу знімає імпульс і записує `GNSS_RESET_OVERRUN`. Довше утримання RESET_N нічого не живить, тому це не trip.
- Невдалий запис зняття → `trip()` → `all_off()`. Якщо `all_off()` повернувся без помилки на ініціалізованому, відкритому адаптері, `LinuxHardware` записав і прочитав назад OLAT та IODIR кожного MCP. Тоді відпускання доведено: стан `IDLE`, `GNSS_RESET_DEASSERT_FAILED`, `release_ms` — момент цього запису.
- Програмний образ виходів не є доказом. `LinuxHardware.all_off()` спершу скидає образ до безпечного і лише потім кидає «Safe outputs not confirmed», тож після будь-якої спроби образ показує низький затвор. Тому стан визначає результат безпечного запису, а не образ. Якщо `all_off()` не підтверджено (`SAFE_UNCONFIRMED`) або адаптер не ініціалізовано чи вже закрито (тоді `all_off()` без помилки, але нічого не пише — наприклад, після невдалої повторної ініціалізації), стан стає `RELEASE_UNCONFIRMED`, `release_ms` і `last_width_ms` лишаються `None`, а `last_error` — `GNSS_RESET_RELEASE_UNCONFIRMED`. Так само для невдалого assert, для trip чи disarm посеред імпульсу і для засувки адаптера (`LinuxHardware._fail`), яку policy помічає лише на тіку. Повторних спроб запису немає. Нові імпульси заблоковано засувкою помилки й самим станом. Після Pico MCP RESET (outputs high-Z, R326) і нової ініціалізації `clear_fault` з успішним `all_off` переводить стан у `IDLE`. `release_ms` тоді — момент цього доказу, від нього відлічуються 30 s, а `last_width_ms` лишається невідомим (`None`).
- Trip, disarm, `clear_fault` або нова ініціалізація MCP посеред імпульсу відпускають лінію (`GNSS_RESET_ABORTED`), якщо безпечний запис підтверджено; інтервал 30 s відлічується від цього моменту.
- Невдалий запис assert зараховується до ліміту 3 за 15 хв: запис OLAT міг дійти до MCP раніше, ніж збій читання назад. Якщо `all_off()` потім підтверджено, стан `IDLE` з `GNSS_RESET_ASSERT_FAILED`.
- Якщо labd загине посеред імпульсу: тайм-аут HB Pico → MCP RESET через Q306 → виходи high-Z → R326 відпускає скидання. Це спроєктовано, але не кваліфіковано (OPEN_ITEMS.md, E3-08).

### Статус

`policy.status()["gnss_reset"]` (також у `engine.status()["policy"]`):

| Поле | Значення |
|---|---|
| `state` | `IDLE`, `ASSERTED`, `RELEASE_UNCONFIRMED` (`ASSERTING` існує лише всередині запису assert і назовні не видно) |
| `last_ms`, `width_ms`, `release_due_ms` | Початок останнього імпульсу, запитана ширина, плановий момент зняття (лише в `ASSERTED`) |
| `release_ms`, `last_width_ms` | Момент доведеного (прочитаного назад) відпускання і ширина за тіками; `None`, поки відпускання не доведено. Після відновлення з `RELEASE_UNCONFIRMED` `release_ms` — момент доказу, а ширина лишається `None` |
| `pulses_15min` | Початки, зокрема невдалі спроби assert, у ковзному 15-хвилинному вікні |
| `last_error` | Наслідок останнього імпульсу: `None`, `GNSS_RESET_OVERRUN`, `GNSS_RESET_ABORTED`, `GNSS_RESET_DEASSERT_FAILED`, `GNSS_RESET_ASSERT_FAILED`, `GNSS_RESET_RELEASE_UNCONFIRMED` (лишається й після відновлення як історія імпульсу); новий імпульс його скидає |

### Консервативні рішення там, де специфікація неоднозначна

- Інтервал 30 s відлічується від відпускання, а не від початку попереднього імпульсу (довший інтервал).
- «Пізно» до 1000 ms включно — лише зняття; `OVERRUN` — строго після 1000 ms.
- Engine вимагає власної чинної оренди того, хто запитує, а не лише «ніхто інший не володіє», і відмовляє, поки ARM очікує підтвердження.
- Стан `RELEASE_UNCONFIRMED` замість удаваного `IDLE`, коли програма не може довести низький рівень затвора. Доказом є лише запис із читанням назад (зняття, `all_off`, безпечна ініціалізація), а не програмний образ виходів.
- Невдалий assert зараховується до ліміту імпульсів.
- Перший `poll()` читача завжди робить flush; після затримки хоста стан `STARTING`, доки не надійде справжній байт.

### Служба місця навколо імпульсу (runtime, поза цим обсягом)

Перед імпульсом споживач, що тримає трекер, викликає `tracker.invalidate(<джерело>, "GNSS_RESET")`; chrony переводить PPS у `+noselect` (build/07:484); RTC і останній добрий фікс позначаються застарілими. Після імпульсу: дочекатися першого валідного речення, зупинити gpsd, повторно надіслати налаштування з allowlist і прочитати їх назад, знову запустити gpsd. PPS стає вибірним лише після читання назад і воріт 3D ≥6 (build/07:500, :503). Ця оркестрація gpsd/chrony — робота середовища виконання, тут її не реалізовано.

## Перевірки

```sh
PYTHONPATH=software python3 -m unittest discover -s software/tests -p 'test_gnss_*.py' -v
python3 deployment/module_lab/location_scenarios.py --project . --output /tmp/srrx-location.json
```

- `test_gnss_uart.py` (Linux PTY + тимчасовий sysfs): зворотне читання termios; fd `O_RDONLY` (запис → EBADF), `O_CLOEXEC`; виклик `TIOCEXCL` через інжектований ioctl; прив'язка (правильний батько проходить; хибний батько, шлях `ttyHS1`, сам вузол ядра, звичайний файл, розбіжність `dev` відхиляються без витоку дескриптора); фрагментація між викликами; 64 KiB за кілька обмежених викликів і рівно 8×2048 за виклик; затримка → flush + invalidate без «дописування» старого рядка; пізній перший `poll()` не передає накопичене від відкриття; затримка після тиші дає `STARTING`, а не `RECEIVING`; HUP → `disconnected` без повторного відкриття; тиша 2 s → одноразова інвалідація, 10 s → `SILENT`; статична перевірка, що модуль не має шляху запису; Pico на `998000.serial` відхиляє `validate_devices`/`udev_rules`/`stage`. Тест також запускає NMEA-сценарії module lab із цим виробничим читачем.
- `test_gnss_reset.py` (`SimHardware`, `LinuxHardware` над фальшивим регістровим файлом MCP23017, змодельований Engine із `SimLink`, labctl): assert у t0; ще утримано в t0+199; відпущено в t0+200; trip/disarm/ініціалізація посеред імпульсу; другий імпульс протягом 30 s і четвертий за 15 хв відхилено; ширини 99, 501, `True` відхилено; відмова без ініціалізації, із засувкою, без оренди; пізній тік у t0+5000 → `OVERRUN`; невдале зняття → trip із низьким затвором; сирий `E3_GNSS_RESET_GATE` і далі відхилено. З `LinuxHardware`: зламана шина при знятті, trip, disarm, збої `read_inputs` чи assert дає `RELEASE_UNCONFIRMED` з `release_ms=None`, хоча образ показує низький затвор, а регістр OLAT — ще високий; повторних записів немає; одноразовий збій з успішним `all_off` дає `IDLE`; відновлення лише після MCP RESET і `clear_fault`, а 30 s відлічуються від доказу.

Ці тести не доводять апаратну роботу. Відкритими лишаються: pinmux і справжня швидкість UART6 (09-testy.md:55, W-04), осцилограма імпульсу RESET і всіх виходів MCP #4 (09-testy.md:105, Ж-15), TTFF і `$PQTMVERNO` (09-testy.md:179, GNSS-01), відпускання через Pico/Q306/R326 (E3-08), живий udev/sysfs на Q6A. Усі вони мають статус RUNTIME_ONLY/BLOCKED, а не PASS.
